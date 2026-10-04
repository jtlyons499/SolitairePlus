import random

from niche_poker_common import (
    RANK_VALUES,
    build_standard_deck,
    card_key,
    round_chip_amount,
)
from poker_ai import (
    decide_poker_action,
    get_poker_personality,
    get_poker_skill_factor,
)
from poker_core import format_poker_display_name


class BlindMansBluffGame:
    """Standard one-card Blind Man's Bluff / forehead poker.

    Every player can see every opponent's card but not their own. Highest rank
    wins after one betting round. Suits do not break ties.

    The game uses one betting round with variable opening sizes and no raises.
    Players can check, open for different amounts, call, or fold while still
    never seeing their own card.
    """

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.npcs = []
        self.starting_stack = 0
        self.player_stack = 0
        self.npc_stacks = []
        self.ante = 0
        self.bet_unit = 0
        self.pot = 0
        self.hand_number = 0
        self.deck = []
        self.cards = []
        self.folded = []
        self.live_at_start = []
        self.phase = "idle"
        self.bet_state = ""
        self.current_bet = 0
        self.bettor_index = None
        self.hand_complete = False
        self.session_complete = False
        self.result_text = ""
        self.last_winner_indexes = []
        self.last_actions = []
        self.hands_played = 0
        self.hands_won = 0
        self.hands_lost = 0
        self.hands_tied = 0
        self.reward_claimed = False
        self.opening_index = 0

    # --------------------------------------------------
    # Session / stacks
    # --------------------------------------------------

    def start_session(self, npcs, starting_stack):
        self.npcs = list(npcs or [])[:3]
        self.starting_stack = max(0, int(starting_stack))
        self.player_stack = self.starting_stack
        self.npc_stacks = [self.starting_stack for _ in self.npcs]
        self.ante = round_chip_amount(self.starting_stack * 0.008, minimum=5)
        self.bet_unit = round_chip_amount(self.starting_stack * 0.02, minimum=10)
        self.hand_number = 0
        self.hands_played = 0
        self.hands_won = 0
        self.hands_lost = 0
        self.hands_tied = 0
        self.reward_claimed = False
        self.session_complete = False
        return self.start_hand()

    def _stack_for(self, table_index):
        if table_index == 0:
            return self.player_stack
        npc_index = table_index - 1
        if 0 <= npc_index < len(self.npc_stacks):
            return self.npc_stacks[npc_index]
        return 0

    def _commit(self, table_index, amount):
        amount = max(0, int(amount))
        if table_index == 0:
            paid = min(amount, self.player_stack)
            self.player_stack -= paid
        else:
            npc_index = table_index - 1
            if not (0 <= npc_index < len(self.npc_stacks)):
                return 0
            paid = min(amount, self.npc_stacks[npc_index])
            self.npc_stacks[npc_index] -= paid
        self.pot += paid
        return paid

    def get_name(self, table_index):
        if table_index == 0:
            return "You"
        npc_index = table_index - 1
        if 0 <= npc_index < len(self.npcs):
            return format_poker_display_name(self.npcs[npc_index].get("name", "Opponent"))
        return "Opponent"

    def get_npc(self, table_index):
        npc_index = table_index - 1
        if 0 <= npc_index < len(self.npcs):
            return self.npcs[npc_index]
        return {}

    def get_active_indexes(self, include_folded=False):
        indexes = []
        for table_index in self.live_at_start:
            if include_folded or not self.folded[table_index]:
                indexes.append(table_index)
        return indexes

    def start_hand(self):
        eligible = []
        if self.player_stack >= self.ante:
            eligible.append(0)
        for npc_index, stack in enumerate(self.npc_stacks):
            if stack >= self.ante:
                eligible.append(npc_index + 1)

        if 0 not in eligible or len(eligible) < 2:
            self.session_complete = True
            self.phase = "session_over"
            self.hand_complete = True
            if 0 not in eligible:
                self.result_text = "You do not have enough chips for another Blind Man's Bluff hand."
            else:
                self.result_text = "No opponents have enough chips for another hand."
            return False

        self.hand_number += 1
        self.deck = build_standard_deck(self.rng)
        seat_count = len(self.npcs) + 1
        self.cards = [None] * seat_count
        self.folded = [True] * seat_count
        self.last_actions = [""] * seat_count
        self.live_at_start = list(eligible)
        self.pot = 0
        self.phase = "betting"
        self.current_bet = 0
        self.bettor_index = None
        self.hand_complete = False
        self.result_text = "You can see everyone else's card, but not your own."
        self.last_winner_indexes = []

        for table_index in eligible:
            self.folded[table_index] = False
            self._commit(table_index, self.ante)
            self.cards[table_index] = self.deck.pop()

        # Rotate the opening action through every live seat instead of making
        # the human open every hand. When an NPC opens, their table decisions
        # resolve first and the player acts last or responds to the wager.
        self.opening_index = eligible[(self.hand_number - 1) % len(eligible)]
        if self.opening_index == 0:
            self.bet_state = "player_open"
        else:
            self._process_npc_opening_before_player()

        return True

    # --------------------------------------------------
    # Information / AI strength
    # --------------------------------------------------

    def get_visible_cards_for(self, viewer_index):
        return [
            self.cards[index]
            for index in self.get_active_indexes()
            if index != viewer_index and self.cards[index] is not None
        ]

    def _npc_hidden_card_strength(self, table_index):
        """Exact expected showdown share from the NPC's legal information.

        The NPC knows all active opponent cards and treats its own forehead card
        as any card remaining in the deck. Suits do not break Blind Man's Bluff
        ties, matching the supplied highest-card rule.
        """
        visible_active = self.get_visible_cards_for(table_index)
        if not visible_active:
            return 0.5

        # Folded forehead cards are still visible and therefore known to be
        # unavailable as the NPC's own card, even though they no longer matter
        # when deciding which live rank must be beaten.
        known_other_cards = [
            self.cards[index]
            for index in self.live_at_start
            if index != table_index and self.cards[index] is not None
        ]
        visible_keys = {card_key(card) for card in known_other_cards}
        unseen = [
            card for card in build_standard_deck(random.Random(0))
            if card_key(card) not in visible_keys
        ]
        if not unseen:
            return 0.5

        max_visible = max(RANK_VALUES[card["rank"]] for card in visible_active)
        visible_max_count = sum(
            1 for card in visible_active
            if RANK_VALUES[card["rank"]] == max_visible
        )

        total_value = 0.0
        for candidate in unseen:
            value = RANK_VALUES[candidate["rank"]]
            if value > max_visible:
                total_value += 1.0
            elif value == max_visible:
                total_value += 1.0 / (visible_max_count + 1.0)
        return total_value / len(unseen)

    def _npc_decision(self, table_index, facing_bet=False):
        npc = self.get_npc(table_index)
        strength = self._npc_hidden_card_strength(table_index)
        amount_to_call = self.current_bet if facing_bet else 0
        max_open = self.get_max_open_bet()
        min_open = self.get_min_open_bet()
        context = {
            "stage": "forehead_bet",
            "position": "unknown",
            "hand_strength": strength,
            "skill_factor": get_poker_skill_factor(npc),
            "amount_to_call": amount_to_call,
            "stack": self._stack_for(table_index),
            "pot": self.pot,
            "current_bet": self.current_bet,
            "can_raise": False,
            "opponents_remaining": max(1, len(self.get_active_indexes()) - 1),
            "minimum_open_bet": min_open,
            "maximum_open_bet": max_open,
        }
        return decide_poker_action(
            get_poker_personality(npc),
            context,
            rng=self.rng,
        )

    def get_max_open_bet(self):
        active = self.get_active_indexes()
        if len(active) < 2:
            return 0
        stacks = [self._stack_for(index) for index in active]
        return max(0, min(stacks))

    def get_min_open_bet(self):
        maximum = self.get_max_open_bet()
        if maximum <= 0:
            return 0
        minimum = max(self.ante, round_chip_amount(self.starting_stack * 0.01, minimum=5))
        return min(maximum, minimum)

    def get_player_bet_presets(self):
        minimum = self.get_min_open_bet()
        maximum = self.get_max_open_bet()
        if maximum <= 0:
            return []

        pot = max(1, int(self.pot))
        raw = [
            ("MIN", minimum),
            ("1/2 POT", max(minimum, round_chip_amount(pot * 0.5, minimum=minimum))),
            ("POT", max(minimum, round_chip_amount(pot, minimum=minimum))),
            ("MAX", maximum),
        ]

        presets = []
        seen = set()
        for label, amount in raw:
            amount = max(minimum, min(int(amount), maximum))
            if amount in seen:
                continue
            seen.add(amount)
            presets.append((label, amount))
        return presets

    def _choose_npc_open_bet(self, table_index, strength, decision):
        minimum = self.get_min_open_bet()
        maximum = self.get_max_open_bet()
        if maximum <= 0:
            return 0

        pot = max(1, int(self.pot))
        personality = str(
            decision.get("effective_personality")
            or get_poker_personality(self.get_npc(table_index))
            or "balanced"
        ).lower()

        # Variable sizing keeps the one-round format quick while letting
        # personality, confidence and bluffs change the pressure of a hand.
        multiplier = 0.50
        if strength >= 0.72:
            multiplier = self.rng.choice((0.85, 1.0, 1.35))
        elif strength >= 0.50:
            multiplier = self.rng.choice((0.55, 0.75, 1.0))
        elif decision.get("bluff"):
            multiplier = self.rng.choice((0.65, 0.90, 1.15))
        else:
            multiplier = self.rng.choice((0.40, 0.50, 0.65))

        if personality in ("aggressive", "escalator"):
            multiplier *= 1.25
        elif personality == "timid":
            multiplier *= 0.75
        elif personality == "unpredictable":
            multiplier *= self.rng.uniform(0.65, 1.45)

        amount = round_chip_amount(pot * multiplier, minimum=minimum)
        return max(minimum, min(int(amount), maximum))

    def get_effective_bet_unit(self):
        # Backward-compatible helper used by older UI paths.
        return self.get_min_open_bet()

    def get_player_actions(self):
        if self.phase != "betting" or self.hand_complete or self.folded[0]:
            return []
        if self.bet_state in ("player_open", "player_last_open"):
            actions = ["check"]
            if self.get_effective_bet_unit() > 0:
                actions.append("bet")
            return actions
        if self.bet_state == "player_response":
            return ["fold", "call"]
        return []

    # --------------------------------------------------
    # Betting round
    # --------------------------------------------------

    def _npc_opening_order(self):
        active_npcs = [index for index in self.get_active_indexes() if index != 0]
        if not active_npcs:
            return []
        if self.opening_index not in active_npcs:
            return active_npcs
        start = active_npcs.index(self.opening_index)
        return active_npcs[start:] + active_npcs[:start]

    def _process_npc_opening_before_player(self):
        bettor = None
        for table_index in self._npc_opening_order():
            if self.folded[table_index]:
                continue

            if bettor is None:
                decision = self._npc_decision(table_index, facing_bet=False)
                if decision.get("action") == "bet" and self.get_max_open_bet() > 0:
                    amount = self._choose_npc_open_bet(
                        table_index,
                        self._npc_hidden_card_strength(table_index),
                        decision,
                    )
                    self.current_bet = self._commit(table_index, amount)
                    self.bettor_index = table_index
                    self.last_actions[table_index] = f"Bet ${self.current_bet:,}"
                    bettor = table_index
                else:
                    self.last_actions[table_index] = "Checked"
            else:
                decision = self._npc_decision(table_index, facing_bet=True)
                if decision.get("action") == "fold":
                    self.folded[table_index] = True
                    self.last_actions[table_index] = "Folded"
                else:
                    paid = self._commit(table_index, self.current_bet)
                    self.last_actions[table_index] = f"Called ${paid:,}"

        if bettor is None:
            self.bet_state = "player_last_open"
            self.result_text = "The table checks around to you. Check behind or make the only bet."
        else:
            self.bet_state = "player_response"
            self.result_text = (
                f"{self.get_name(bettor)} opens for ${self.current_bet:,}. "
                "Call or fold without seeing your card."
            )

    def player_check(self):
        if "check" not in self.get_player_actions():
            return False
        self.last_actions[0] = "Checked"
        if self.bet_state == "player_last_open":
            self._showdown()
        else:
            self._process_npcs_after_player_check()
        return True

    def player_bet(self, amount=None):
        if "bet" not in self.get_player_actions():
            return False
        minimum = self.get_min_open_bet()
        maximum = self.get_max_open_bet()
        if maximum <= 0:
            return False
        if amount is None:
            amount = max(minimum, min(maximum, self.pot))
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            amount = minimum
        amount = max(minimum, min(amount, maximum))
        self.current_bet = self._commit(0, amount)
        self.bettor_index = 0
        self.last_actions[0] = f"Bet ${self.current_bet:,}"

        callers = 0
        for table_index in list(self.get_active_indexes()):
            if table_index == 0:
                continue
            decision = self._npc_decision(table_index, facing_bet=True)
            if decision.get("action") == "fold":
                self.folded[table_index] = True
                self.last_actions[table_index] = "Folded"
            else:
                paid = self._commit(table_index, self.current_bet)
                self.last_actions[table_index] = f"Called ${paid:,}"
                callers += 1

        if callers == 0:
            self._award_single_survivor(0)
        else:
            self._showdown()
        return True

    def _process_npcs_after_player_check(self):
        active_npcs = [index for index in self.get_active_indexes() if index != 0]
        bettor = None

        for table_index in active_npcs:
            decision = self._npc_decision(table_index, facing_bet=False)
            if decision.get("action") == "bet" and self.get_max_open_bet() > 0:
                amount = self._choose_npc_open_bet(
                    table_index,
                    self._npc_hidden_card_strength(table_index),
                    decision,
                )
                self.current_bet = self._commit(table_index, amount)
                self.bettor_index = table_index
                self.last_actions[table_index] = f"Bet ${self.current_bet:,}"
                bettor = table_index
                break
            self.last_actions[table_index] = "Checked"

        if bettor is None:
            self._showdown()
            return

        # Everyone except the bettor and human gets one call/fold decision.
        for table_index in active_npcs:
            if table_index == bettor:
                continue
            decision = self._npc_decision(table_index, facing_bet=True)
            if decision.get("action") == "fold":
                self.folded[table_index] = True
                self.last_actions[table_index] = "Folded"
            else:
                paid = self._commit(table_index, self.current_bet)
                self.last_actions[table_index] = f"Called ${paid:,}"

        self.bet_state = "player_response"
        self.result_text = (
            f"{self.get_name(bettor)} bets ${self.current_bet:,}. You still cannot see your card."
        )

    def player_call(self):
        if "call" not in self.get_player_actions():
            return False
        paid = self._commit(0, self.current_bet)
        self.last_actions[0] = f"Called ${paid:,}"
        self._showdown()
        return True

    def player_fold(self):
        if "fold" not in self.get_player_actions():
            return False
        self.folded[0] = True
        self.last_actions[0] = "Folded"
        remaining = self.get_active_indexes()
        if len(remaining) == 1:
            self._award_single_survivor(remaining[0])
        else:
            self._showdown()
        return True

    # --------------------------------------------------
    # Resolution
    # --------------------------------------------------

    def _award_single_survivor(self, table_index):
        self._pay_pot([table_index])
        self.last_winner_indexes = [table_index]
        if table_index == 0:
            self.hands_won += 1
            self.result_text = f"Everyone folds. You win the ${self.pot_awarded:,} pot without seeing your card."
        else:
            self.hands_lost += 1
            self.result_text = f"{self.get_name(table_index)} wins the pot after the folds."
        self._finish_hand()

    def _pay_pot(self, winner_indexes):
        if not winner_indexes:
            return
        pot_before = self.pot
        share = pot_before // len(winner_indexes)
        remainder = pot_before - share * len(winner_indexes)
        for offset, table_index in enumerate(winner_indexes):
            amount = share + (1 if offset < remainder else 0)
            if table_index == 0:
                self.player_stack += amount
            else:
                self.npc_stacks[table_index - 1] += amount
        self.pot_awarded = pot_before
        self.pot = 0

    def _showdown(self):
        self.phase = "showdown"
        active = self.get_active_indexes()
        if not active:
            self.last_winner_indexes = []
            self.result_text = "No live cards remained."
            self._finish_hand()
            return

        high_rank = max(
            RANK_VALUES[self.cards[index]["rank"]]
            for index in active
        )
        winners = [
            index for index in active
            if RANK_VALUES[self.cards[index]["rank"]] == high_rank
        ]
        self.last_winner_indexes = winners
        self._pay_pot(winners)

        if 0 in winners:
            if len(winners) == 1:
                self.hands_won += 1
                self.result_text = (
                    f"Your {self.cards[0]['rank']} is highest. You win ${self.pot_awarded:,}."
                )
            else:
                self.hands_tied += 1
                self.result_text = (
                    f"Your {self.cards[0]['rank']} ties for high card. The pot is split {len(winners)} ways."
                )
        else:
            self.hands_lost += 1
            if len(winners) == 1:
                winner = winners[0]
                self.result_text = (
                    f"{self.get_name(winner)} wins with {self.cards[winner]['rank']} high."
                )
            else:
                names = ", ".join(self.get_name(index) for index in winners)
                self.result_text = f"{names} tie for the highest card and split the pot."

        self._finish_hand()

    def _finish_hand(self):
        self.hand_complete = True
        self.phase = "showdown"
        self.hands_played += 1
        if self.player_stack < self.ante:
            self.session_complete = True
        else:
            live_opponents = sum(1 for stack in self.npc_stacks if stack >= self.ante)
            if live_opponents < 1:
                self.session_complete = True

    def can_start_next_hand(self):
        return self.hand_complete and not self.session_complete

    def get_session_net(self):
        return int(self.player_stack - self.starting_stack)
