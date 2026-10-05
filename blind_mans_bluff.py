import random
from niche_poker_common import RANK_VALUES, build_standard_deck, card_key, round_chip_amount
from poker_ai import (decide_poker_action, get_poker_personality, get_poker_skill_factor,
                      choose_poker_open_bet_amount, choose_poker_raise_to_amount)
from poker_core import format_poker_display_name
from npc_personality import get_npc_traits, PokerGrudgeMemory, npc_identity
from npc_personality_chat import trait_chat


class BlindMansBluffGame:
    """Forehead poker: one full betting round; only opponents' cards are visible.

    Check, bet, call, raise and fold use real round contributions. All-ins create
    side pots and short all-in raises do not reopen an already-acted player's
    raise rights. Highest rank wins each eligible pot; equal ranks split it.
    """
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.npcs = []
        self.starting_stack = self.player_stack = self.ante = self.bet_unit = 0
        self.npc_stacks = []
        self.pot = self.hand_number = self.current_bet = self.pot_awarded = 0
        self.deck, self.cards, self.folded, self.live_at_start = [], [], [], []
        self.phase, self.bet_state, self.result_text = "idle", "", ""
        self.bettor_index = None
        self.hand_complete = self.session_complete = False
        self.last_winner_indexes, self.last_actions, self.last_chat = [], [], []
        self.hands_played = self.hands_won = self.hands_lost = self.hands_tied = 0
        self.reward_claimed = False
        self.opening_index = self.current_actor = 0
        self.round_bets, self.hand_contributions = [], []
        self.pending, self.raise_rights = set(), set()
        self.last_raise_size = 1
        self.personality_memory = PokerGrudgeMemory()
        self.npc_ai_last_decisions = []

    def start_session(self, npcs, starting_stack):
        self.npcs = list(npcs or [])[:3]
        self.starting_stack = max(0, int(starting_stack))
        self.player_stack = self.starting_stack
        self.npc_stacks = [self.starting_stack for _ in self.npcs]
        self.ante = round_chip_amount(self.starting_stack * 0.008, minimum=5)
        self.bet_unit = round_chip_amount(self.starting_stack * 0.02, minimum=10)
        self.hand_number = self.hands_played = self.hands_won = self.hands_lost = self.hands_tied = 0
        self.reward_claimed = self.session_complete = False
        self.personality_memory.clear()
        return self.start_hand()

    def _stack_for(self, seat):
        return self.player_stack if seat == 0 else self.npc_stacks[seat - 1]

    def _commit(self, seat, amount, round_bet=True):
        paid = min(max(0, int(amount)), self._stack_for(seat))
        if seat == 0:
            self.player_stack -= paid
        else:
            self.npc_stacks[seat - 1] -= paid
        self.pot += paid
        self.hand_contributions[seat] += paid
        if round_bet:
            self.round_bets[seat] += paid
        return paid

    def get_npc(self, seat):
        return self.npcs[seat - 1] if 1 <= seat <= len(self.npcs) else {}

    def get_name(self, seat):
        return "You" if seat == 0 else format_poker_display_name(self.get_npc(seat).get("name", "Opponent"))

    def get_active_indexes(self, include_folded=False):
        return [seat for seat in self.live_at_start if include_folded or not self.folded[seat]]

    def start_hand(self):
        eligible = [seat for seat in range(len(self.npcs) + 1) if self._stack_for(seat) >= self.ante]
        if 0 not in eligible or len(eligible) < 2:
            self.session_complete = self.hand_complete = True
            self.phase = "session_over"
            self.result_text = "Not enough chips or opponents for another hand."
            return False
        self.hand_number += 1
        self.deck = build_standard_deck(self.rng)
        count = len(self.npcs) + 1
        self.cards, self.folded = [None]*count, [True]*count
        self.last_actions, self.last_chat = [""]*count, [""]*count
        self.round_bets, self.hand_contributions = [0]*count, [0]*count
        self.npc_ai_last_decisions = [None]*len(self.npcs)
        self.live_at_start = eligible
        self.pot = self.current_bet = self.pot_awarded = 0
        self.bettor_index = None
        self.phase = "betting"
        self.hand_complete = False
        self.result_text = "You can see everyone else's card, but not your own."
        self.last_winner_indexes = []
        for seat in eligible:
            self.folded[seat] = False
            self._commit(seat, self.ante, round_bet=False)
            self.cards[seat] = self.deck.pop()
        self.last_raise_size = self._base_minimum()
        self.opening_index = eligible[(self.hand_number - 1) % len(eligible)]
        self.current_actor = self.opening_index
        self.pending = {seat for seat in eligible if self._stack_for(seat) > 0}
        self.raise_rights = set(self.pending)
        self._advance(self.current_actor, inclusive=True)
        return True

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

    def _base_minimum(self):
        return max(self.ante, round_chip_amount(self.starting_stack * 0.01, minimum=5))

    def get_player_amount_to_call(self):
        return min(self.player_stack, max(0, self.current_bet - self.round_bets[0])) if self.round_bets else 0

    def _can_raise(self, seat):
        active = self.get_active_indexes()
        return (seat in self.raise_rights and self._stack_for(seat) + self.round_bets[seat] > self.current_bet
                and any(other != seat and self._stack_for(other) > 0 for other in active))

    def get_max_open_bet(self):
        return self.player_stack if self._can_raise(0) else 0

    def get_min_open_bet(self):
        return min(self.get_max_open_bet(), self._base_minimum())

    def get_minimum_raise_to(self):
        return self.current_bet + self.last_raise_size

    def get_player_bet_presets(self):
        raising = self.current_bet > 0
        maximum = self.player_stack + (self.round_bets[0] if raising else 0)
        if not self._can_raise(0):
            return []
        minimum = min(maximum, self.get_minimum_raise_to() if raising else self._base_minimum())
        raw = [("MIN", minimum),
               ("1/2 POT", max(minimum, self.current_bet + int(self.pot*0.5))),
               ("POT", max(minimum, self.current_bet + self.pot)), ("MAX", maximum)]
        seen, presets = set(), []
        for label, amount in raw:
            amount = max(minimum, min(maximum, int(amount)))
            if amount not in seen:
                presets.append((label, amount))
                seen.add(amount)
        return presets

    def get_effective_bet_unit(self):
        return self.get_min_open_bet()

    def get_player_actions(self):
        if self.hand_complete or self.phase != "betting" or self.current_actor != 0 or 0 not in self.pending:
            return []
        due = max(0, self.current_bet - self.round_bets[0])
        actions = ["fold", "call"] if due else ["check"]
        if self._can_raise(0):
            actions.append("raise" if self.current_bet else "bet")
        return actions

    def _grudge_context(self, seat):
        opponents = [{"seat": other, "id": npc_identity(self.get_npc(other), other),
                      "name": self.get_name(other), "stack": self._stack_for(other),
                      "round_bet": self.round_bets[other]}
                     for other in self.get_active_indexes() if other != seat]
        return self.personality_memory.context(self.get_npc(seat), seat, opponents,
                                               self.bettor_index, self.hand_number)

    def _npc_context(self, seat):
        stack = self._stack_for(seat)
        context = {
            "game": "blind_mans_bluff", "stage": "forehead_bet", "position": "unknown",
            "personality_traits": get_npc_traits(self.get_npc(seat)),
            "hand_strength": self._npc_hidden_card_strength(seat),
            "skill_factor": get_poker_skill_factor(self.get_npc(seat)),
            "amount_to_call": max(0, self.current_bet - self.round_bets[seat]),
            "stack": stack, "pot": self.pot, "current_bet": self.current_bet,
            "current_round_bet": self.round_bets[seat],
            "can_raise": self._can_raise(seat), "last_raiser": self.bettor_index,
            "opponents_remaining": len(self.get_active_indexes()) - 1,
            "minimum_open_bet": self._base_minimum(), "maximum_open_bet": stack,
            "minimum_raise_to": self.get_minimum_raise_to(),
            "minimum_raise_size": self.last_raise_size,
            "maximum_raise_to": stack + self.round_bets[seat],
        }
        context.update(self._grudge_context(seat))
        return context

    def _npc_take_turn(self, seat):
        context = self._npc_context(seat)
        decision = decide_poker_action(get_poker_personality(self.get_npc(seat)), context, self.rng)
        self.npc_ai_last_decisions[seat - 1] = decision
        action = decision["action"]
        amount = None
        if action == "bet":
            amount = choose_poker_open_bet_amount(context, decision["profile"], context["hand_strength"], decision["bluff"])
        elif action == "raise":
            amount = choose_poker_raise_to_amount(context, decision["profile"], context["hand_strength"], decision["bluff"])
        if amount is None and action in ("bet", "raise"):
            action = "call" if context["amount_to_call"] else "check"
        if not self._act(seat, action, amount):
            self._act(seat, "call" if context["amount_to_call"] else "check")
        if self.rng.random() < 0.22:
            self.last_chat[seat] = trait_chat(self.get_npc(seat), action, self.rng,
                                             context.get("grudge_target"), context.get("grudge_intensity", 0))

    def _act(self, seat, action, amount=None):
        if seat not in self.pending or self.hand_complete:
            return False
        due = max(0, self.current_bet - self.round_bets[seat])
        if action == "fold":
            self.folded[seat] = True
            self.last_actions[seat] = "Folded"
        elif action == "check":
            if due:
                return False
            self.last_actions[seat] = "Checked"
        elif action == "call":
            if not due:
                return False
            paid = self._commit(seat, due)
            self.last_actions[seat] = f"Called ${paid:,}"
        elif action in ("bet", "raise"):
            if not self._can_raise(seat) or (action == "bet") != (self.current_bet == 0):
                return False
            maximum = self.round_bets[seat] + self._stack_for(seat)
            minimum = self.get_minimum_raise_to() if self.current_bet else self._base_minimum()
            try:
                target = int(amount if amount is not None else max(minimum, self.current_bet + self.pot))
            except (TypeError, ValueError):
                return False
            target = min(maximum, max(minimum, target))
            if target <= self.current_bet:
                return False
            increase = target - self.current_bet
            full_raise = increase >= self.last_raise_size
            self._commit(seat, target - self.round_bets[seat])
            self.current_bet, self.bettor_index = target, seat
            if full_raise:
                self.last_raise_size = increase
                self.raise_rights = {other for other in self.get_active_indexes() if self._stack_for(other) > 0}
                self.pending = set(self.raise_rights)
            else:
                self.pending.update(other for other in self.get_active_indexes()
                                    if self._stack_for(other) > 0 and self.round_bets[other] < target)
            self.last_actions[seat] = f"{'Bet' if action == 'bet' else 'Raised to'} ${target:,}"
        else:
            return False
        self.pending.discard(seat)
        self.raise_rights.discard(seat)
        return True

    def _advance(self, after, inclusive=False):
        count = len(self.npcs) + 1
        search_from = after if inclusive else (after + 1) % count
        while not self.hand_complete:
            active = self.get_active_indexes()
            if len(active) == 1:
                self._award_single_survivor(active[0])
                return
            self.pending.intersection_update(seat for seat in active if self._stack_for(seat) > 0)
            # With nobody left to respond, a free option cannot create a pot.
            if len([seat for seat in active if self._stack_for(seat) > 0]) <= 1:
                self.pending = {seat for seat in self.pending if self.round_bets[seat] < self.current_bet}
            if not self.pending:
                self._showdown()
                return
            seat = next((search_from + offset) % count for offset in range(count)
                        if (search_from + offset) % count in self.pending)
            self.current_actor = seat
            if seat == 0:
                self.bet_state = "player_response" if self.current_bet > self.round_bets[0] else "player_open"
                due = self.get_player_amount_to_call()
                self.result_text = f"Call ${due:,}, raise, or fold." if due else "Check or choose a wager."
                return
            self._npc_take_turn(seat)
            search_from = (seat + 1) % count

    def _player_action(self, action, amount=None):
        if action not in self.get_player_actions() or not self._act(0, action, amount):
            return False
        self._advance(0)
        return True

    def player_check(self):
        return self._player_action("check")

    def player_bet(self, amount=None):
        return self._player_action("bet", amount)

    def player_raise(self, amount=None):
        return self._player_action("raise", amount)

    def player_call(self):
        return self._player_action("call")

    def player_fold(self):
        return self._player_action("fold")

    def _credit(self, seat, amount):
        if seat == 0:
            self.player_stack += amount
        else:
            self.npc_stacks[seat - 1] += amount

    def _award_single_survivor(self, seat):
        self.pot_awarded = self.pot
        self._credit(seat, self.pot)
        self.pot = 0
        self.last_winner_indexes = [seat]
        if seat == 0:
            self.hands_won += 1
        else:
            self.hands_lost += 1
        self.result_text = f"{self.get_name(seat)} wins ${self.pot_awarded:,} after the folds."
        self._finish_hand()

    def _showdown(self):
        active = self.get_active_indexes()
        payouts = [0]*len(self.cards)
        won_pots = set()
        previous = 0
        self.pot_awarded = self.pot
        for level in sorted(set(value for value in self.hand_contributions if value > 0)):
            contributors = [seat for seat in self.live_at_start if self.hand_contributions[seat] >= level]
            amount = (level - previous)*len(contributors)
            previous = level
            eligible = [seat for seat in contributors if seat in active]
            # An unmatched top layer is a refund, not a won showdown pot.
            if len(contributors) == 1:
                payouts[contributors[0]] += amount
                continue
            if not eligible:
                # Defensive refund for an unreachable no-eligible contribution layer.
                for seat in contributors:
                    payouts[seat] += amount // len(contributors)
                continue
            high = max(RANK_VALUES[self.cards[seat]["rank"]] for seat in eligible)
            winners = [seat for seat in eligible if RANK_VALUES[self.cards[seat]["rank"]] == high]
            won_pots.update(winners)
            for offset, seat in enumerate(winners):
                payouts[seat] += amount//len(winners) + (offset < amount % len(winners))
            for loser in set(eligible) - set(winners):
                if loser == 0:
                    continue
                npc = self.get_npc(loser)
                for winner in winners:
                    self.personality_memory.record_loss(
                        npc_identity(npc, loser), npc_identity(self.get_npc(winner), winner),
                        self.hand_number, get_npc_traits(npc)["bitterness"],
                        self.hand_contributions[loser]/max(1, self.starting_stack))
        for seat, amount in enumerate(payouts):
            self._credit(seat, amount)
        self.pot = 0
        self.last_winner_indexes = sorted(won_pots)
        if 0 in won_pots:
            if len(won_pots) == 1:
                self.hands_won += 1
            else:
                self.hands_tied += 1
        else:
            self.hands_lost += 1
        parts = [f"{self.get_name(seat)} ${payouts[seat]:,}" for seat in sorted(won_pots)]
        self.result_text = "Payouts: " + "; ".join(parts) + "."
        self._finish_hand()

    def _finish_hand(self):
        self.hand_complete = True
        self.phase, self.bet_state = "showdown", ""
        self.current_actor = -1
        self.hands_played += 1
        self.session_complete = (self.player_stack < self.ante
                                 or not any(stack >= self.ante for stack in self.npc_stacks))

    def can_start_next_hand(self):
        return self.hand_complete and not self.session_complete

    def get_session_net(self):
        return self.player_stack - self.starting_stack
