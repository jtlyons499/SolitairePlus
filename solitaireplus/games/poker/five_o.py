import random
from solitaireplus.npc.personality import get_npc_traits, trait_units, PokerGrudgeMemory
from solitaireplus.npc.personality_chat import game_trait_chat
from solitaireplus.games.poker.holdem_chat import npc_action_chat_chance, npc_action_chat_event
import time

from solitaireplus.games.poker.niche_common import (
    build_standard_deck,
    card_key,
    compare_scores,
    evaluate_five_card_hand,
    round_chip_amount,
)
from solitaireplus.games.poker.ai import (
    PokerOpponentModel,
    decide_poker_action,
    get_poker_personality,
    get_poker_skill_factor,
)
from solitaireplus.games.poker.core import (can_raise, describe_poker_score, format_poker_display_name,
                                            settle_fold_win, split_pot)
from solitaireplus.games.poker.npc_inputs import (
    grudge_seats,
    npc_decision_inputs,
    observe_public_action,
    opponent_rows,
    reset_session_memory,
    table_identities,
    wealth_pressure,
)
from solitaireplus.games.poker.strategy import PokerTableReads


class FiveOPokerGame:
    """Heads-up Five-O Poker.

    Card construction follows the supplied rules exactly: five starting face-up
    cards per player, four more placement layers, the fourth card in every
    column hidden from the opponent, then one betting round and five paired
    poker-hand comparisons.

    One pot-based betting round supports checks, bets, calls, raises and folds.
    Opponent responses pause briefly, followed by sequential column reveals.
    """

    HIDDEN_CARD_INDEX = 3

    # The career rating (and rival-learning game) the NPC's skill and memory use.
    rating_game_key = "five_o_poker"

    # The stage name of the single betting round in NPC contexts and table reads.
    BETTING_STAGE = "showdown_bet"

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.npc = None
        self.personality_memory = PokerGrudgeMemory()
        # Public reads of every seat, the human's tendencies and (career only)
        # the profile's rival-learning store, as at the other poker tables.
        self.table_reads = PokerTableReads()
        self.player_model = PokerOpponentModel()
        self.learning_store = None
        # The seat of the last bet or raise this round (None if nobody bet).
        self.last_raiser = None
        self.last_npc_chat = ""
        # Table talk lines the table has not shown yet (take_npc_chat).
        self.npc_chat_queue = []
        # The NPC's last AI decision this hand (one entry: the NPC), for its table talk.
        self.npc_ai_last_decisions = [None]
        self.starting_stack = 0
        self.player_stack = 0
        self.npc_stack = 0
        self.ante = 0
        self.bet_unit = 0
        self.pot = 0
        self.hand_number = 0
        self.deck = []
        self.player_columns = [[] for _ in range(5)]
        self.npc_columns = [[] for _ in range(5)]
        self.player_drawn_card = None
        self.placement_round = 2
        self.phase = "idle"
        self.bet_state = ""
        self.current_bet = 0
        self.player_folded = False
        self.npc_folded = False
        self.hand_complete = False
        self.session_complete = False
        self.result_text = ""
        self.column_results = [None] * 5
        self.player_column_wins = 0
        self.npc_column_wins = 0
        self.player_five_o = False
        self.npc_five_o = False
        self.hands_played = 0
        self.hands_won = 0
        self.hands_lost = 0
        self.hands_tied = 0
        self.five_o_wins = 0
        self.reward_claimed = False
        self.rating_seen_hands = set()
        self.rating_final_stacks = None
        self.session_rating_rewarded = False
        self.session_rating_change = 0
        self.session_rating_net = 0
        self.session_rating_roi = 0.0
        self.last_winner = None
        self.last_npc_action = ""
        self.last_player_action = ""
        self.opening_index = 0
        self.placement_opener = 0

        # Reveal the five showdown columns one at a time so the player can
        # actually read each comparison before the final result appears.
        self.showdown_revealed_columns = 0
        self.showdown_reveal_started_at = 0.0
        self.showdown_reveal_interval = 1.1
        self.fast_reveal = False
        self.sounds_enabled = True
        self.options_open = False
        self.bet_fraction = .5
        self.pending_npc_at = 0.0
        # How long the NPC thinks before each betting decision (seconds). The
        # screen sets it from the table speed every frame; the default keeps
        # the old fixed pause for engine-only use.
        self.npc_delay_seconds = 0.65
        self.player_betting_paid = 0
        self.npc_betting_paid = 0
        # Chips each seat (0 = human, 1 = NPC) put in this hand, antes included.
        self.hand_contributions = [0, 0]
        # How the last hand was settled, in the shared record shape
        # (core.award_pots). Five-O has one pot and no uncalled chips.
        self.last_pot_awards = []
        self.last_refunds = {}
        self.last_resolved_pot = 0
        self.raise_count = 0
        self.pending_showdown_result_text = ""
        self.showdown_pending_finish = False

    # --------------------------------------------------
    # Seat views: read-only per-seat lists for the shared
    # table rules in core.py. Seat 0 is the human, seat 1
    # the NPC, as in the multi-seat variants.
    # --------------------------------------------------

    @property
    def npcs(self):
        return [self.npc] if isinstance(self.npc, dict) else []

    def seat_stacks(self):
        return [self.player_stack, self.npc_stack]

    def seat_round_bets(self):
        return [self.player_betting_paid, self.npc_betting_paid]

    def seat_in_hand(self):
        return [not self.player_folded, not self.npc_folded]

    def seat_at_table(self):
        """Per seat: not knocked out of the session. A hand is dealt only while both
        seats can ante, so both are at the table, all-in or not."""
        return [True, True]

    # --------------------------------------------------
    # Session / deck
    # --------------------------------------------------

    def start_session(self, npc, starting_stack):
        self.last_npc_chat = ""
        self.npc_chat_queue = []
        self.npc = npc or {"name": "Opponent", "skill_tier": "mid"}
        # Grudges, quick chat, player tendencies and table reads start fresh;
        # the reads bind to the career rival-learning store.
        reset_session_memory(self, self.rating_game_key)
        self.starting_stack = max(0, int(starting_stack))
        self.player_stack = self.starting_stack
        self.npc_stack = self.starting_stack
        self.ante = round_chip_amount(self.starting_stack * 0.01, minimum=5)
        self.bet_unit = round_chip_amount(self.starting_stack * 0.02, minimum=10)
        self.hand_number = 0
        self.hands_played = 0
        self.hands_won = 0
        self.hands_lost = 0
        self.hands_tied = 0
        self.five_o_wins = 0
        self.reward_claimed = False
        self.rating_seen_hands = set()
        self.rating_final_stacks = None
        self.session_rating_rewarded = False
        self.session_rating_change = 0
        self.session_rating_net = 0
        self.session_rating_roi = 0.0
        self.session_complete = False
        return self.start_hand()

    def draw_card(self):
        return self.deck.pop() if self.deck else None

    def _commit_player(self, amount):
        paid = min(max(0, int(amount)), self.player_stack)
        self.player_stack -= paid
        self.pot += paid
        self.hand_contributions[0] += paid
        return paid

    def _commit_npc(self, amount):
        paid = min(max(0, int(amount)), self.npc_stack)
        self.npc_stack -= paid
        self.pot += paid
        self.hand_contributions[1] += paid
        return paid

    def start_hand(self):
        self.hand_start_player_stack = self.player_stack
        self.pending_npc_at = 0.0
        self.player_betting_paid = self.npc_betting_paid = 0
        self.last_raiser = None
        if self.player_stack < self.ante or self.npc_stack < self.ante:
            self.session_complete = True
            self.phase = "session_over"
            self.hand_complete = True
            if self.player_stack < self.ante:
                self.result_text = "You do not have enough chips for another Five-O hand."
            else:
                self.result_text = f"{self.get_npc_name()} is out of chips."
            return False

        self.player_model.start_hand()
        self.hand_number += 1
        self.last_npc_chat = ""
        self.npc_chat_queue = []
        self.npc_ai_last_decisions = [None]
        self.deck = build_standard_deck(self.rng)
        self.player_columns = [[] for _ in range(5)]
        self.npc_columns = [[] for _ in range(5)]
        self.player_drawn_card = None
        self.placement_round = 2
        self.phase = "placement"
        self.bet_state = ""
        self.current_bet = 0
        self.pot = 0
        self.player_folded = False
        self.npc_folded = False
        self.hand_complete = False
        self.result_text = "Build five poker hands. Place the drawn card in one open column."
        self.column_results = [None] * 5
        self.player_column_wins = 0
        self.npc_column_wins = 0
        self.player_five_o = False
        self.npc_five_o = False
        self.last_winner = None
        self.last_npc_action = ""
        self.last_player_action = ""
        self.opening_index = 0
        self.placement_opener = 0
        self.showdown_revealed_columns = 0
        self.showdown_reveal_started_at = 0.0
        self.pending_showdown_result_text = ""
        self.showdown_pending_finish = False
        self.hand_contributions = [0, 0]
        self.last_pot_awards = []
        self.last_refunds = {}
        self.last_resolved_pot = 0

        self._commit_player(self.ante)
        self._commit_npc(self.ante)

        # "Five alternate face-up cards each". Deal one to the human, then one
        # to the opponent, for each of the five starting columns.
        for column_index in range(5):
            self.player_columns[column_index].append(self.draw_card())
            self.npc_columns[column_index].append(self.draw_card())

        # Alternate who gets the first placement each hand. The NPC acts
        # instantly in the UI, but this keeps the actual turn order rotating
        # instead of making the human open every hand.
        self.opening_index = 0 if self.hand_number % 2 == 1 else 1
        self.placement_opener = self.opening_index

        if self.placement_opener == 1:
            self._npc_take_placement_turn()
        else:
            self.player_drawn_card = self.draw_card()

        return True

    # --------------------------------------------------
    # Placement phase
    # --------------------------------------------------

    def get_available_player_columns(self):
        if self.phase != "placement" or self.player_drawn_card is None:
            return []
        expected_length = self.placement_round - 1
        return [
            index for index, column in enumerate(self.player_columns)
            if len(column) == expected_length
        ]

    def get_available_npc_columns(self):
        if self.phase != "placement":
            return []
        expected_length = self.placement_round - 1
        return [
            index for index, column in enumerate(self.npc_columns)
            if len(column) == expected_length
        ]

    @staticmethod
    def _partial_hand_value(cards):
        if not cards:
            return 0.0
        rank_values = {
            "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
            "8": 8, "9": 9, "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14,
        }
        ranks = [rank_values[c["rank"]] for c in cards]
        suits = [c["suit"] for c in cards]
        counts = {}
        for rank in ranks:
            counts[rank] = counts.get(rank, 0) + 1
        pair_bonus = sum((count - 1) * 7.0 for count in counts.values() if count > 1)
        flush_bonus = 4.5 if len(set(suits)) == 1 and len(cards) >= 2 else 0.0
        spread = max(ranks) - min(ranks) if len(ranks) >= 2 else 0
        straight_bonus = 2.5 if len(set(ranks)) == len(ranks) and spread <= 4 else 0.0
        high = sum(ranks) / len(ranks)
        return high + pair_bonus + flush_bonus + straight_bonus

    def _choose_npc_column(self, card):
        available = self.get_available_npc_columns()
        if not available:
            return None

        skill = get_poker_skill_factor(self.npc, self.rating_game_key)
        if self.rng.random() > (0.32 + skill * 0.68):
            return self.rng.choice(available)

        scored = []
        for index in available:
            own_cards = self.npc_columns[index] + [card]
            own_value = self._partial_hand_value(own_cards)

            # The opponent column is mostly visible. Favor columns where this
            # card improves a hand that can plausibly overtake the human hand.
            visible_player = [
                candidate for pos, candidate in enumerate(self.player_columns[index])
                if pos != self.HIDDEN_CARD_INDEX
            ]
            opponent_value = self._partial_hand_value(visible_player)
            catchup_bonus = max(-4.0, min(4.0, opponent_value - own_value)) * 0.20
            t = trait_units(get_npc_traits(self.npc))
            noise = self.rng.uniform(-1.5, 1.5) * ((1.0 - skill) + 0.45*t["unpredictability"])
            catchup_bonus *= 0.65 + 0.70*t["selectivity"]
            scored.append((own_value + catchup_bonus + noise, index))

        scored.sort(reverse=True)
        return scored[0][1]

    def _placement_layer_complete(self):
        return (
            all(len(column) >= self.placement_round for column in self.player_columns)
            and all(len(column) >= self.placement_round for column in self.npc_columns)
        )

    def _advance_placement_layer_if_ready(self):
        if not self._placement_layer_complete():
            return False

        self.placement_round += 1
        if self.placement_round > 5:
            self._begin_betting()
            return True

        return True

    def _npc_take_placement_turn(self):
        if self.phase != "placement":
            return False

        npc_card = self.draw_card()
        npc_column = self._choose_npc_column(npc_card)
        if npc_card is None or npc_column is None:
            return False

        self.npc_columns[npc_column].append(npc_card)
        self.last_npc_action = f"{self.get_npc_name()} used column {npc_column + 1}."

        self._advance_placement_layer_if_ready()
        if self.phase == "placement":
            self.player_drawn_card = self.draw_card()

        return True

    def place_player_card(self, column_index):
        if self.phase != "placement" or self.player_drawn_card is None:
            return False
        if column_index not in self.get_available_player_columns():
            return False

        self.player_columns[column_index].append(self.player_drawn_card)
        self.player_drawn_card = None
        self.last_player_action = f"Placed in column {column_index + 1}"

        # If the human completed the layer, advance first. When the NPC is
        # the opener it then immediately opens the next layer; otherwise this
        # is simply the NPC's matching turn in the current layer.
        self._advance_placement_layer_if_ready()

        if self.phase == "placement":
            self._npc_take_placement_turn()

        return True

    # --------------------------------------------------
    # Betting
    # --------------------------------------------------

    def _begin_betting(self):
        self.phase = "betting"
        self.current_bet = 0
        self.player_betting_paid = self.npc_betting_paid = 0
        self.raise_count = 0
        self.last_raiser = None
        self.pending_npc_at = 0.0
        self.player_drawn_card = None
        self.result_text = (
            f"All five hands are built. One betting round for ${self.get_effective_bet_unit():,}."
        )

        if self.opening_index == 0:
            self.bet_state = "player_open"
            return

        # On alternating hands the opponent gets first betting action, after
        # the same thinking pause as its other betting decisions.
        if self.npc_delay_seconds > 0:
            self.bet_state = "npc_open"
            self._queue_opponent()
            return
        self._npc_open()

    def _npc_open(self):
        """The NPC opens the betting round: bet the unit or check to the human."""
        decision = self._npc_decision(facing_bet=False)
        if decision.get("action") == "bet" and self._npc_bet():
            self.last_npc_action = f"{self.get_npc_name()} bets ${self.current_bet:,}."
            self.bet_state = "player_response"
            self.result_text = (f"{self.get_npc_name()} opens for ${self.current_bet:,}. "
                                + self._response_prompt())
            self._npc_talk("bet")
        else:
            self._observe_action("check", 1)
            self.last_npc_action = f"{self.get_npc_name()} checks."
            self.bet_state = "player_last_open"
            self.result_text = f"{self.get_npc_name()} checks. Action is on you."
            self._npc_talk("check")

    def _response_prompt(self):
        """The prompt when the human faces a bet: it names raising only when the
        raise button is offered (get_player_actions, _seat_can_raise)."""
        return "Call, raise or fold." if self._seat_can_raise(0) else "Call or fold."

    def can_select_bet_fraction(self):
        """May the human change the bet-size preset now?

        Five-O has one bet unit per round, and the preset (bet_fraction) sizes
        the NPC's bets and raises too. So it is locked while the NPC is
        thinking (pending_npc_at): the human cannot resize the bet the NPC is
        about to make.
        """
        return self.phase == "betting" and not self.hand_complete and not self.pending_npc_at

    def select_bet_fraction(self, fraction):
        """Set the bet-size preset; False (nothing changes) while it is locked."""
        if not self.can_select_bet_fraction():
            return False
        self.bet_fraction = fraction
        return True

    def get_effective_bet_unit(self):
        ceiling = min(self.player_stack + self.player_betting_paid, self.npc_stack + self.npc_betting_paid)
        minimum = max(self.ante * 2, self.current_bet * 2)
        target = round_chip_amount(max(self.pot, self.ante * 4) * self.bet_fraction, minimum=minimum)
        return max(0, min(ceiling, target))

    def _seat_can_raise(self, seat):
        """May seat (0 = human, 1 = NPC) bet or raise now?

        The shared rule (core.can_raise: chips beyond the call and somebody
        able to respond) plus Five-O's own limits: at most three raises
        after the opening bet, and the fixed bet unit must top the bet.
        """
        return (
            can_raise(seat, self.seat_in_hand(), self.seat_stacks(), self.seat_round_bets(),
                      self.current_bet)
            and (self.current_bet == 0 or self.raise_count < 3)
            and self.get_effective_bet_unit() > self.current_bet
        )

    def get_player_actions(self):
        if self.phase != "betting" or self.hand_complete or self.pending_npc_at:
            return []
        if self.bet_state in ("player_open", "player_last_open"):
            return ["check", "bet"] if self._seat_can_raise(0) else ["check"]
        if self.bet_state == "player_response":
            actions = ["fold", "call"]
            if self._seat_can_raise(0):
                actions.append("bet")
            return actions
        return []

    def _observe_action(self, event, seat, paid=0, facing=0):
        """Let the NPC read a public action (npc_inputs.observe_public_action)."""
        observe_public_action(
            self, event, seat, stage=self.BETTING_STAGE, amount=paid,
            round_total=self.seat_round_bets()[seat], facing_amount=facing,
        )

    def _record_player_action(self, action, facing, pot_before, paid=0):
        """Remember the human's action in the player-tendency model."""
        self.player_model.record_action(
            action, stage=self.BETTING_STAGE, amount_to_call=facing,
            pot_before=pot_before, amount=paid,
        )

    def _npc_bet(self):
        """The NPC opens the betting for the bet unit; False if it may not bet."""
        if self.current_bet or not self._seat_can_raise(1):
            return False
        self.current_bet = self._commit_npc(self.get_effective_bet_unit())
        self.npc_betting_paid = self.current_bet
        self.last_raiser = 1
        self._observe_action("bet", 1, self.current_bet)
        return True

    def _npc_raise(self):
        """The NPC raises to the bet unit; False if it may not raise (NEW-4)."""
        if not self.current_bet or not self._seat_can_raise(1):
            return False
        target = self.get_effective_bet_unit()
        facing = self.current_bet - self.npc_betting_paid
        paid = self._commit_npc(target - self.npc_betting_paid)
        self.npc_betting_paid += paid
        self.current_bet = self.npc_betting_paid
        self.raise_count += 1
        self.last_raiser = 1
        self._observe_action("raise", 1, paid, facing)
        return True

    def _queue_opponent(self):
        self.pending_npc_at = time.monotonic() + self.npc_delay_seconds
        self.result_text = f"{self.get_npc_name()} is considering the action…"

    def _finish_opponent_response(self):
        self.pending_npc_at = 0.0
        if self.bet_state == "npc_open":
            self._npc_open()
            return
        if not self.current_bet:
            decision = self._npc_decision(facing_bet=False)
            if decision.get("action") == "bet" and self._npc_bet():
                self.bet_state = "player_response"
                self.last_npc_action = f"{self.get_npc_name()} bets ${self.current_bet:,}."
                self.result_text = self.last_npc_action + " " + self._response_prompt()
                self._npc_talk("bet")
            else:
                self._observe_action("check", 1)
                self.last_npc_action = f"{self.get_npc_name()} checks."
                self._npc_talk("check")
                self._showdown()
            return
        decision = self._npc_decision(facing_bet=True)
        facing = self.current_bet - self.npc_betting_paid
        if decision.get("action") == "fold":
            self.npc_folded = True
            self._observe_action("fold", 1, 0, facing)
            self.last_npc_action = f"{self.get_npc_name()} folds."
            self._npc_talk("fold")
            self._award_fold_win(player_won=True)
        elif decision.get("action") == "raise" and self._npc_raise():
            self.bet_state = "player_response"
            self.last_npc_action = f"{self.get_npc_name()} raises to ${self.current_bet:,}."
            self.result_text = self.last_npc_action + " " + self._response_prompt()
            self._npc_talk("raise")
        else:
            paid = self._commit_npc(facing)
            self.npc_betting_paid += paid
            self._observe_action("call", 1, paid, facing)
            self.last_npc_action = f"{self.get_npc_name()} calls ${paid:,}."
            self._npc_talk("call")
            self._showdown()

    def _npc_talk(self, action):
        """The NPC may talk after the action it took, as at every poker table.

        How often (npc_action_chat_chance) and what it says (game_trait_chat: a
        strong grudge first, then the decision's tactic line, then the trait mix)
        are shared with the other tables. A line is kept in last_npc_chat and
        queued for the table to show (take_npc_chat).
        """
        event = npc_action_chat_event(action, self.npc_stack)
        if self.rng.random() < npc_action_chat_chance(self.npc, event):
            self.last_npc_chat = game_trait_chat(self, 0, event, self.rng)
            self.npc_chat_queue.append(self.last_npc_chat)

    def take_npc_chat(self):
        """Return the NPC's table talk not yet shown, oldest first, and forget it."""
        lines, self.npc_chat_queue = self.npc_chat_queue, []
        return lines

    def get_npc_wealth_pressure(self):
        """Return 0..1 pressure from an NPC stack that has grown past buy-in."""
        return wealth_pressure(self.npc_stack, self.starting_stack)

    def _known_npc_strength(self, samples=120):
        """Estimate how often the NPC wins 3+ columns without peeking at the
        human's five face-down fourth cards."""
        known_keys = set()
        for column in self.npc_columns:
            for card in column:
                known_keys.add(card_key(card))
        for column in self.player_columns:
            for position, card in enumerate(column):
                if position != self.HIDDEN_CARD_INDEX:
                    known_keys.add(card_key(card))

        unseen = [
            card for card in build_standard_deck(random.Random(0))
            if card_key(card) not in known_keys
        ]
        if len(unseen) < 5:
            return 0.5

        wins = 0.0
        sample_count = max(20, int(samples))
        for _ in range(sample_count):
            hidden_cards = self.rng.sample(unseen, 5)
            npc_columns_won = 0
            player_columns_won = 0
            for index in range(5):
                player_cards = list(self.player_columns[index])
                player_cards[self.HIDDEN_CARD_INDEX] = hidden_cards[index]
                player_score = evaluate_five_card_hand(player_cards)
                npc_score = evaluate_five_card_hand(self.npc_columns[index])
                comparison = compare_scores(npc_score, player_score)
                if comparison > 0:
                    npc_columns_won += 1
                elif comparison < 0:
                    player_columns_won += 1
            if npc_columns_won >= 3:
                wins += 1.0
            elif player_columns_won < 3:
                wins += 0.5
        return wins / sample_count

    def _npc_decision(self, facing_bet=False):
        strength = self._known_npc_strength()
        personality = get_poker_personality(self.npc)
        amount_to_call = max(0, self.current_bet - self.npc_betting_paid) if facing_bet else 0
        context = {
            "game": "five_o_poker",
            "stage": self.BETTING_STAGE,
            "position": "unknown",
            "hand_strength": strength,
            "amount_to_call": amount_to_call,
            "stack": self.npc_stack,
            "pot": self.pot,
            "current_bet": self.current_bet,
            # NEW-4: facing a bet the NPC may raise, to the fixed bet unit.
            "can_raise": facing_bet and self._seat_can_raise(1),
            "opponents_remaining": 1,
            "last_raiser": self.last_raiser,
            "minimum_open_bet": self.get_effective_bet_unit(),
            "maximum_open_bet": self.get_effective_bet_unit(),
            "minimum_raise_to": self.get_effective_bet_unit(),
            "maximum_raise_to": self.get_effective_bet_unit(),
        }
        # The inputs every poker variant shares: traits, rating skill, cash on
        # hand, table reads, player tendencies and the grudge against the bettor.
        context.update(npc_decision_inputs(
            npc=self.npc, seat=1, rating_game_key=self.rating_game_key,
            stack=self.npc_stack, starting_stack=self.starting_stack,
            hand_number=self.hand_number, opponents=self._opponent_rows(),
            last_raiser=self.last_raiser, grudge_memory=self.personality_memory,
            table_reads=self.table_reads, player_model=self.player_model,
            player_active=not self.player_folded,
        ))
        # Share the same short-lived conversational effects used by Hold'em,
        # Draw and Stud without duplicating any dialogue in this module.
        from solitaireplus.games.poker.quick_chat import get_npc_quick_chat_context
        from solitaireplus.games.poker.quick_chat_adapter import adapt_quick_chat_game
        context.update(get_npc_quick_chat_context(adapt_quick_chat_game(self, "five_o_poker"), 0))

        decision = decide_poker_action(personality, context, rng=self.rng)
        self.npc_ai_last_decisions = [dict(decision)]
        return decision

    def get_npc_grudge_context(self, npc_index=0):
        """The NPC's grudge context now (PokerGrudgeMemory.context), as at every table."""
        return self.personality_memory.context(self.npc, 1, self._opponent_rows(),
                                               self.last_raiser, self.hand_number)

    def _opponent_rows(self):
        """The NPC's public row for the human (npc_inputs.opponent_rows), if still in the hand."""
        return opponent_rows(1, [] if self.player_folded else [0], {0: "You"},
                             table_identities(self.npcs), self.seat_stacks(), self.seat_round_bets())

    def player_check(self):
        if "check" not in self.get_player_actions(): return False
        self._record_player_action("check", 0, self.pot)
        self._observe_action("check", 0)
        self.last_player_action = "Checked"
        if self.bet_state == "player_last_open": self._showdown()
        else: self._queue_opponent()
        return True

    def player_bet(self):
        if "bet" not in self.get_player_actions(): return False
        target = self.get_effective_bet_unit()
        if target <= self.current_bet: return False
        raised = self.current_bet > 0
        facing, pot_before = self.current_bet - self.player_betting_paid, self.pot
        paid = self._commit_player(target - self.player_betting_paid)
        self.player_betting_paid += paid
        self.current_bet = self.player_betting_paid
        if raised: self.raise_count += 1
        self.last_raiser = 0
        action = "raise" if raised else "bet"
        self._record_player_action(action, facing, pot_before, paid)
        self._observe_action(action, 0, paid, facing)
        self.last_player_action = f"{'Raised to' if raised else 'Bet'} ${self.current_bet:,}"
        self._queue_opponent()
        return True

    def player_call(self):
        if "call" not in self.get_player_actions(): return False
        facing, pot_before = self.current_bet - self.player_betting_paid, self.pot
        paid = self._commit_player(facing)
        self.player_betting_paid += paid
        self._record_player_action("call", facing, pot_before, paid)
        self._observe_action("call", 0, paid, facing)
        self.last_player_action = f"Called ${paid:,}"
        self._showdown()
        return True

    def player_fold(self):
        if "fold" not in self.get_player_actions():
            return False
        facing = self.current_bet - self.player_betting_paid
        self._record_player_action("fold", facing, self.pot)
        self.player_folded = True
        self._observe_action("fold", 0, 0, facing)
        self.last_player_action = "Folded"
        self._award_fold_win(player_won=False)
        return True

    # --------------------------------------------------
    # Resolution
    # --------------------------------------------------

    def _record_pot(self, payouts, eligible):
        """Record this hand's single pot in the shared award shape (core.award_pots)."""
        amount = sum(payouts.values())
        winners = list(payouts)
        self.last_pot_awards = [{
            "amount": amount,
            "eligible": list(eligible),
            "winners": winners,
            "payouts": dict(payouts),
            "share": amount // len(winners),
            "remainder": amount % len(winners),
            "hand": "",
        }]
        self.last_refunds = {}
        self.last_resolved_pot = amount

    def _award_fold_win(self, player_won):
        winner = 0 if player_won else 1
        # core.settle_fold_win, as at every table: settled like a showdown with
        # one live seat. Five-O's bets are always callable, so the folder never
        # has chips above the winner's; the winner's own bet that the fold left
        # uncalled goes back to it, and it wins the pot of matched chips.
        winnings, refunds = settle_fold_win(self.hand_contributions, winner)
        self._record_pot({winner: winnings}, [winner])
        self.last_refunds = dict(refunds)
        self.player_stack += refunds.get(0, 0)
        self.npc_stack += refunds.get(1, 0)
        if player_won:
            self.player_stack += winnings
            self.last_winner = "player"
            self.result_text = f"{self.get_npc_name()} folds. You win ${winnings:,}"
            self.hands_won += 1
        else:
            self.npc_stack += winnings
            self.last_winner = "npc"
            self.result_text = f"You fold. {self.get_npc_name()} wins ${winnings:,}"
            self.hands_lost += 1
        # Every Five-O fold leaves the winner's last bet uncalled. Said in a few words,
        # the result keeps to two rows of the table's result panel.
        own = refunds.get(winner, 0)
        self.result_text += f" (uncalled ${own:,} returned)." if own else "."
        for seat, amount in sorted(refunds.items()):
            if seat != winner:
                owner = "you" if seat == 0 else self.get_npc_name()
                self.result_text += f" Uncalled ${amount:,} returned to {owner}."
        self.pot = 0
        self._finish_hand()

    def _showdown(self):
        # Resolution can be reached through either betting path. Re-entry must
        # never award the same pot or advance session statistics twice.
        if self.showdown_pending_finish or self.hand_complete:
            return
        self.phase = "showdown"
        # The hand settles here: nothing the NPC had queued may still run.
        self.pending_npc_at = 0.0
        self.column_results = []
        self.player_column_wins = 0
        self.npc_column_wins = 0

        for index in range(5):
            player_score = evaluate_five_card_hand(self.player_columns[index])
            npc_score = evaluate_five_card_hand(self.npc_columns[index])
            comparison = compare_scores(player_score, npc_score)
            if comparison > 0:
                self.column_results.append("player")
                self.player_column_wins += 1
            elif comparison < 0:
                self.column_results.append("npc")
                self.npc_column_wins += 1
            else:
                self.column_results.append("tie")

        self.player_five_o = self.player_column_wins == 5
        self.npc_five_o = self.npc_column_wins == 5

        if self.player_column_wins >= 3:
            self._record_pot({0: self.pot}, [0, 1])
            self.player_stack += self.pot
            self.last_winner = "player"
            self.hands_won += 1
            if self.player_five_o:
                self.five_o_wins += 1
                final_text = f"FIVE-O! You sweep all five columns and win ${self.pot:,}."
            else:
                final_text = (
                    f"You win {self.player_column_wins}-{self.npc_column_wins} "
                    f"and take ${self.pot:,}."
                )
        elif self.npc_column_wins >= 3:
            self._record_pot({1: self.pot}, [0, 1])
            self.npc_stack += self.pot
            self.last_winner = "npc"
            self.hands_lost += 1
            if self.npc_five_o:
                final_text = (
                    f"FIVE-O for {self.get_npc_name()}. "
                    "You lose all five columns."
                )
            else:
                final_text = (
                    f"{self.get_npc_name()} wins "
                    f"{self.npc_column_wins}-{self.player_column_wins} "
                    f"and takes ${self.pot:,}."
                )
        else:
            # Column-majority tie: split the pot. Five-O pots are even (equal antes,
            # called bets); a stray odd chip would go to the opener, as in every variant
            # the first seat left of the dealer takes it (core.split_pot).
            payouts = split_pot(self.pot, [0, 1], 1 - self.opening_index, 2)
            self._record_pot(payouts, [0, 1])
            self.player_stack += payouts[0]
            self.npc_stack += payouts[1]
            self.last_winner = "tie"
            self.hands_tied += 1
            final_text = (
                f"The five columns split {self.player_column_wins}-"
                f"{self.npc_column_wins} with ties. Pot split."
            )

        # Both seats' columns are shown: a seat that bet or raised and won
        # nothing showed a weak holding. A seat beaten in the pot resents the
        # winner by how much it put in (a split records nothing).
        payouts = self.last_pot_awards[0]["payouts"]
        for seat in (0, 1):
            observe_public_action(self, "showdown_hand", seat, stage=self.BETTING_STAGE,
                                  weak=payouts.get(seat, 0) <= 0)
        self.personality_memory.record_showdown(
            self.last_pot_awards, grudge_seats(self.npcs, self.hand_contributions),
            self.hand_number, self.starting_stack)
        self.pot = 0
        self.pending_showdown_result_text = final_text
        self.result_text = "Showdown: revealing column 1 of 5..."
        self.showdown_revealed_columns = 0
        self.showdown_reveal_started_at = time.monotonic()
        self.showdown_pending_finish = True

    def update(self):
        if self.pending_npc_at:
            if self.hand_complete or self.phase != "betting":
                # The hand has settled (or reached its showdown): a queued NPC
                # turn, its opening included, never runs on it.
                self.pending_npc_at = 0.0
            elif time.monotonic() >= self.pending_npc_at:
                self._finish_opponent_response()
        if not self.showdown_pending_finish or self.hand_complete:
            return

        elapsed = time.monotonic() - self.showdown_reveal_started_at
        target_count = min(
            5,
            int(elapsed / (.25 if self.fast_reveal else self.showdown_reveal_interval)) + 1,
        )

        if target_count > self.showdown_revealed_columns:
            self.showdown_revealed_columns = target_count

        if self.showdown_revealed_columns >= 5:
            # Let the fifth comparison sit on screen for one reveal interval
            # before showing the final hand result / Next Hand controls.
            final_hold = (.25 if self.fast_reveal else self.showdown_reveal_interval) * 5
            if elapsed >= final_hold:
                self.result_text = self.pending_showdown_result_text
                self.showdown_pending_finish = False
                self._finish_hand()
            else:
                self.result_text = (
                    "Showdown: column 5 resolved. Final result incoming..."
                )
        else:
            next_column = self.showdown_revealed_columns + 1
            self.result_text = (
                f"Showdown: column {self.showdown_revealed_columns} resolved. "
                f"Revealing column {next_column} of 5..."
            )

    def get_showdown_revealed_count(self):
        if self.hand_complete:
            return 5
        if self.phase == "showdown":
            return max(0, min(5, int(self.showdown_revealed_columns)))
        return 0

    def _finish_hand(self):
        self.hand_complete = True
        self.phase = "showdown"
        self.pending_npc_at = 0.0
        self.hands_played += 1

        # Five-O uses its own game class rather than the shared Hold'em table,
        # so keep the same completed-hand rating snapshot here.  This prevents
        # chips committed to a new unfinished hand from affecting cash-out.
        if self.hand_number not in self.rating_seen_hands:
            self.rating_seen_hands.add(self.hand_number)
            self.rating_final_stacks = [
                int(self.player_stack),
                int(self.npc_stack),
            ]

        if self.player_stack < self.ante or self.npc_stack < self.ante:
            self.session_complete = True

    def get_column_score(self, player, column_index):
        columns = self.player_columns if player == "player" else self.npc_columns
        if not (0 <= column_index < len(columns)):
            return None
        return evaluate_five_card_hand(columns[column_index])

    def get_column_description(self, player, column_index):
        score = self.get_column_score(player, column_index)
        return describe_poker_score(score) if score else "Incomplete"

    def get_npc_name(self):
        return format_poker_display_name(
            self.npc.get("name", "Opponent") if isinstance(self.npc, dict) else "Opponent"
        )

    def get_session_net(self):
        return int(self.player_stack - self.starting_stack)

    def can_start_next_hand(self):
        return (
            self.hand_complete
            and not self.session_complete
            and self.player_stack >= self.ante
            and self.npc_stack >= self.ante
        )


