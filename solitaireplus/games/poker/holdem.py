"""Texas Hold'em engine: the TexasHoldemGame class. Five-Card Draw and Seven-Card Stud build on it.

TexasHoldemGame is assembled from topic mixins in this package (one class split across
modules; every method moved verbatim, keeps its name and works on the same game instance):
    holdem_seats.py     SeatsMixin: chips committed, seat order, dealer and blinds, whose turn
                        it is, the active players, seat views for core.py
    holdem_npc.py       NpcMixin: NPC bets, raises, checks, folds and calls, personality,
                        hand strength and bet sizing
    holdem_betting.py   BettingMixin: recording a wager, the betting rules, the player's actions
    holdem_pots.py      PotsMixin: side pots, pot awards and refunds, the fold win
    holdem_showdown.py  ShowdownMixin: hand evaluation, the showdown, hand names
This module keeps the table settings, the constructor, hand history, the deck, sessions, new
hands, running the next NPC action, ending a betting round and dealing the streets.

Every module-level name holdem.py had is still importable from here (Five-Card Draw and
Seven-Card Stud import HAND_NAMES and RANK_VALUES from here). run_next_npc_action stays here,
so tests that patch holdem.decide_poker_action still reach it. The import block below is the
original one, in its original order.
"""
import random
from solitaireplus.npc.personality import PokerGrudgeMemory
from solitaireplus.games.poker.strategy import PokerTableReads
from solitaireplus.games.poker.quick_chat import get_npc_quick_chat_context
from solitaireplus.games.poker.npc_inputs import (
    grudge_seats,
    npc_decision_inputs,
    observe_public_action,
    opponent_rows,
    reset_session_memory,
    soft_bet_cap,
    table_identities,
    wealth_pressure,
)

# RANK_VALUES and HAND_NAMES live in core.py with the shared evaluator.
# They are imported here too so Five-Card Draw and Seven-Card Stud can
# keep importing them from this module.
from solitaireplus.games.poker.core import (
    HAND_NAMES,
    RANK_VALUES,
    PokerHandHistory,
    award_pots,
    bet_to_match,
    betting_closed,
    betting_reopened,
    build_pots,
    can_raise,
    classify_wager,
    collected_uncontested,
    describe_poker_score,
    evaluate_best_hand as evaluate_best_poker_hand,
    evaluate_five_cards as evaluate_five_poker_cards,
    format_poker_cards,
    format_poker_display_name,
    hand_nets,
    join_poker_names,
    hand_winners,
    minimum_raise_to,
    opening_current_bet,
    session_over,
    settle_fold_win,
)

from solitaireplus.games.poker.ai import (
    PokerOpponentModel,
    calculate_pot_odds,
    choose_poker_open_bet_amount,
    choose_poker_raise_to_amount,
    decide_poker_action,
    get_effective_poker_personality,
    get_poker_personality,
    get_poker_personality_profile,
    get_poker_skill_factor,
)

# The topic mixins TexasHoldemGame is built from (see the docstring).
from solitaireplus.games.poker.holdem_seats import SeatsMixin
from solitaireplus.games.poker.holdem_npc import NpcMixin
from solitaireplus.games.poker.holdem_betting import BettingMixin
from solitaireplus.games.poker.holdem_pots import PotsMixin
from solitaireplus.games.poker.holdem_showdown import ShowdownMixin


# ==================================================
# CARD CONSTANTS
# ==================================================

RANKS = [
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "J",
    "Q",
    "K",
    "A",
]

SUITS = [
    "Clubs",
    "Diamonds",
    "Hearts",
    "Spades",
]


class TexasHoldemGame(
    SeatsMixin,
    NpcMixin,
    BettingMixin,
    PotsMixin,
    ShowdownMixin,
):

    # A showdown with several winners lists each winner's hand in the payout
    # banner. Hold'em's banner wraps; Draw's and Stud's is one fixed-width
    # line, so they list names and amounts only (the hands are in the hand
    # history), as they did before the shared showdown.
    payout_text_names_hands = True

    # Network table options: the defaults are single-player behaviour.
    # Multiplayer room subclasses turn this on (a busted seat 0 watches, dealt no cards).
    allow_network_spectator = False
    # Multiplayer room subclasses turn this off (a fold settles only the last seat left).
    finish_hand_after_player_fold = True
    # Multiplayer room subclasses turn this off (no quick-chat state or NPC nudges).
    quick_chat_enabled = True
    # Multiplayer rooms turn this on: showdown pot records list 'contributors' (room XP, B79).
    record_pot_contributors = False

    # Ratings and rival learning use this key; each variant sets its own.
    rating_game_key = "texas_holdem"

    def __init__(self):

        # ==================================================
        # CARDS / TABLE
        # ==================================================

        self.deck = []

        self.player_hand = []
        self.npc_hands = []

        self.community_cards = []

        self.npcs = []

        self.hand_number = 0

        self.last_hand_busted_indexes = []

        # ==================================================
        # SHARED POKER HAND HISTORY
        # ==================================================

        self.hand_history = PokerHandHistory()

        # Shared session-level model of how the human player
        # has actually been behaving at this poker table.
        self.player_model = PokerOpponentModel()
        self.table_reads = PokerTableReads()
        self.learning_store = None
        self.personality_memory = PokerGrudgeMemory()

        # Snapshot of seats that began the current hand. This
        # remains stable even if somebody moves all-in mid-hand.
        self.hand_seat_indexes = []

        # Last structured AI decision for each NPC. This is kept
        # primarily for debugging and future AI-facing UI tools.
        self.npc_ai_last_decisions = []

        # ==================================================
        # SESSION MONEY
        # ==================================================

        self.starting_stack = 0

        # ``ante`` is retained as the session's base blind unit
        # for compatibility with the rest of the project.
        self.ante = 0
        self.small_blind = 1
        self.big_blind = 2

        # Table indexes: 0 = human, 1+ = NPCs.
        self.dealer_index = -1
        self.small_blind_index = None
        self.big_blind_index = None

        self.player_stack = 0
        self.npc_stacks = []

        self.pot = 0

        # ==================================================
        # ENTIRE-HAND CONTRIBUTIONS
        #
        # Used for main pots and side pots.
        # These include blinds + every later wager.
        # ==================================================

        self.player_hand_contribution = 0

        self.npc_hand_contributions = []

        # How the last hand was settled (see resolve_showdown):
        # one record per pot, and the uncalled chips returned.
        self.last_pot_awards = []
        self.last_refunds = {}
        self.recap_open = False
        self.recap_page = 0

        # Final pot amount retained after payout so the UI can
        # continue showing the completed hand's pot at showdown.
        # Uncalled chips returned to their owner are not included.
        self.last_resolved_pot = 0

        # ==================================================
        # TABLE STATUS
        # ==================================================

        self.player_busted = False

        self.npc_busted = []

        # ==================================================
        # BETTING DISPLAY STATE
        # ==================================================

        self.player_bet_chunks = []

        self.npc_bet_chunks = []

        self.player_action_text = ""

        self.npc_action_texts = []

        # ==================================================
        # CURRENT BETTING ROUND
        # ==================================================

        self.current_bet = 0

        self.player_round_bet = 0

        self.npc_round_bets = []

        self.player_folded = False

        self.npc_folded = []

        self.player_all_in = False

        self.npc_all_in = []

        self.player_has_acted = False

        self.npc_has_acted = []

        self.current_actor = 0

        self.last_raiser = None

        self.last_raise_size = 0

        # Whether the last bet or raise was a full one (core.classify_wager).
        # False after a short all-in or a raise that became a call.
        self.last_wager_full = False

        self.betting_round_complete = False

        # ==================================================
        # HAND STATE
        # ==================================================

        self.current_stage = "idle"

        self.hand_complete = False

        self.winner_indexes = []

        self.result_text = ""

    # ==================================================
    # HAND HISTORY HELPERS
    # ==================================================

    def log_hand_event(
            self,
            event_type,
            text,
            actor_index=None,
            amount=None,
            **data
    ):

        round_total = 0
        if actor_index == 0:
            round_total = self.player_round_bet
        elif actor_index is not None and 0 < actor_index <= len(self.npc_round_bets):
            round_total = self.npc_round_bets[actor_index - 1]
        facing_amount = None
        if event_type in ("call", "fold", "check"):
            previous_total = round_total - int(amount or 0) if event_type == "call" else round_total
            facing_amount = max(0, self.current_bet - previous_total)
        observe_public_action(
            self, event_type, actor_index, stage=self.current_stage,
            amount=amount, round_total=round_total,
            facing_amount=facing_amount,
            hand_name=data.get("hand_name"),
            draw_count=data.get("draw_count"),
        )
        self.hand_history.add(
            event_type,
            text,
            hand_number=self.hand_number,
            stage=self.current_stage,
            actor_index=actor_index,
            amount=amount,
            **data
        )

    def get_hand_history_lines(self):

        return self.hand_history.get_lines()

    def get_hand_history_events(self):

        return self.hand_history.get_events()

    def get_player_tendencies(self):

        return self.player_model.snapshot()

    def record_player_tendency_action(
            self,
            action,
            amount=0,
            amount_to_call=None,
            pot_before=None
    ):

        if amount_to_call is None:
            amount_to_call = (
                self.get_player_amount_to_call()
            )

        if pot_before is None:
            pot_before = self.pot

        self.player_model.record_action(
            action,
            stage=self.current_stage,
            amount_to_call=amount_to_call,
            pot_before=pot_before,
            amount=amount
        )

    def log_newly_busted_players(
            self,
            player_indexes
    ):

        for player_index in player_indexes:

            name = self.get_table_player_name(
                player_index
            )

            if player_index == 0:
                text = "You are eliminated from the table."
            else:
                text = f"{name} is eliminated from the table."

            self.log_hand_event(
                "elimination",
                text,
                actor_index=player_index
            )

    # ==================================================
    # DECK
    # ==================================================

    def build_deck(self):

        self.deck = []

        for suit in SUITS:

            for rank in RANKS:

                self.deck.append(
                    {
                        "rank": rank,
                        "suit": suit,
                    }
                )

        random.shuffle(
            self.deck
        )

    def draw_card(self):

        if not self.deck:
            return None

        return self.deck.pop()

    # ==================================================
    # SESSION
    # ==================================================

    def start_session(
            self,
            npcs,
            starting_stack,
            ante
    ):

        self.hand_number = 0
        self.rating_seen_hands = set()
        self.rating_final_stacks = None
        self.session_rating_rewarded = False

        self.last_hand_busted_indexes = []

        self.hand_history.clear()
        self.hand_seat_indexes = []

        # ==================================================
        # Participants
        # ==================================================

        self.npcs = list(
            npcs
        )

        # Grudges, quick chat, player tendencies and table reads start
        # fresh; the reads bind to the career rival-learning store.
        reset_session_memory(self, self.rating_game_key)

        if not self.quick_chat_enabled:
            # A table without quick chat keeps no quick-chat state: drop
            # what reset_session_memory just set up (everything else it
            # reset stays reset).
            for name in (
                    "quick_chat_state",
                    "_quick_chat_event_counter",
                    "_quick_chat_event_signature",
            ):
                self.__dict__.pop(name, None)

        self.starting_stack = int(
            starting_stack
        )

        self.ante = max(
            1,
            int(ante)
        )

        # The old ante value now acts as the small-blind unit.
        # Keeping the parameter name avoids touching main.py.
        self.small_blind = max(
            1,
            self.ante
        )

        self.big_blind = max(
            2,
            self.small_blind * 2
        )

        # The first hand rotates from -1 to seat 0, making the
        # human the opening dealer when still active.
        self.dealer_index = -1
        self.small_blind_index = None
        self.big_blind_index = None

        # ==================================================
        # Stacks
        # ==================================================

        self.player_stack = (
            self.starting_stack
        )

        self.npc_stacks = [
            self.starting_stack
            for _ in self.npcs
        ]

        self.npc_ai_last_decisions = [
            None
            for _ in self.npcs
        ]

        # ==================================================
        # Bust state
        # ==================================================

        self.player_busted = False

        self.npc_busted = [
            False
            for _ in self.npcs
        ]

        # ==================================================
        # Hand contributions
        # ==================================================

        self.player_hand_contribution = 0

        self.npc_hand_contributions = [
            0
            for _ in self.npcs
        ]

        self.last_pot_awards = []
        self.last_refunds = {}
        self.recap_open = False
        self.recap_page = 0
        self.last_resolved_pot = 0

        # ==================================================
        # Betting state
        # ==================================================

        self.player_bet_chunks = []

        self.npc_bet_chunks = [
            []
            for _ in self.npcs
        ]

        self.player_action_text = ""

        self.npc_action_texts = [
            ""
            for _ in self.npcs
        ]

        self.player_round_bet = 0

        self.npc_round_bets = [
            0
            for _ in self.npcs
        ]

        self.player_folded = False

        self.npc_folded = [
            False
            for _ in self.npcs
        ]

        self.player_all_in = False

        self.npc_all_in = [
            False
            for _ in self.npcs
        ]

        self.player_has_acted = False

        self.npc_has_acted = [
            False
            for _ in self.npcs
        ]

        self.current_bet = 0

        self.last_raise_size = 0

        self.last_raiser = None

        self.current_actor = 0

        self.betting_round_complete = False

        # ==================================================
        # Session state
        # ==================================================

        self.pot = 0

        self.current_stage = "ready"

        self.hand_complete = False

        self.winner_indexes = []

        self.result_text = ""

    def reset_seat_ai_state(self, seat):
        """Forget what the table learned about whoever sat in ``seat`` (1+).

        For multiplayer rooms, where a seat changes hands between hands
        (a late joiner, a leaver's NPC coming back, a replacement NPC);
        single-player never calls it. Call it after npcs[seat - 1] holds
        the new occupant: the seat's public-action reads and showdown
        reveals are dropped, its last AI decision is cleared, and the
        rival-learning seat-to-identity map is rebuilt from the npcs.
        """
        reads = self.table_reads

        for per_seat in (
                reads.histories,
                reads.reveals,
                reads.hand_actions,
                reads.street_bets,
                reads.draw_counts,
        ):
            per_seat.pop(seat, None)

        if 0 <= seat - 1 < len(self.npc_ai_last_decisions):
            self.npc_ai_last_decisions[seat - 1] = None

        if reads.learning is not None:
            reads.bind_learning(
                self.learning_store,
                self.rating_game_key,
                table_identities(self.npcs)
            )

    # ==================================================
    # NEW HAND
    # ==================================================

    def begin_hand_records(self):
        """Forget how the previous hand was settled.

        Every variant's start_hand calls this, so a new hand never shows
        the last hand's pots, refunds, resolved pot, winners or recap.
        """
        self.last_pot_awards = []
        self.last_refunds = {}
        self.last_resolved_pot = 0
        self.winner_indexes = []
        self.recap_open = False
        self.recap_page = 0

    def start_hand(self):

        # ==================================================
        # Determine who is still at the table
        # ==================================================

        self.refresh_busted_state()

        # A network spectator table plays on without a busted seat 0
        # (it is dealt no hole cards below).
        if (
                self.player_busted
                and not self.allow_network_spectator
        ):
            self.hand_complete = True
            self.current_actor = -1
            self.current_stage = "busted"
            self.result_text = (
                "You are out of chips."
            )
            return False

        live_indexes = (
            self.get_live_player_indexes()
        )

        if len(live_indexes) < 2:
            self.hand_complete = True
            self.current_actor = -1
            self.current_stage = "showdown"
            self.result_text = (
                "The table has been cleared."
            )
            return False

        self.hand_seat_indexes = list(
            live_indexes
        )

        self.player_model.start_hand()

        self.hand_number += 1
        self.last_hand_busted_indexes = []

        self.hand_history.start_hand(
            self.hand_number,
            "Texas Hold'em",
            stage="preflop"
        )

        # ==================================================
        # New hand
        # ==================================================

        self.build_deck()

        self.player_hand = []

        self.npc_hands = [
            []
            for _ in self.npcs
        ]

        self.community_cards = []
        self.pot = 0
        self.hand_complete = False
        self.result_text = ""
        self.begin_hand_records()

        # ==================================================
        # Reset ENTIRE-HAND contributions
        # ==================================================

        self.player_hand_contribution = 0

        self.npc_hand_contributions = [
            0
            for _ in self.npcs
        ]

        # ==================================================
        # Whole-hand status
        # ==================================================

        self.player_folded = False

        self.npc_folded = [
            busted
            for busted in self.npc_busted
        ]

        self.player_all_in = False

        self.npc_all_in = [
            False
            for _ in self.npcs
        ]

        # ==================================================
        # Rotate dealer and assign blinds
        # ==================================================

        self.rotate_dealer()
        self.assign_blind_positions()

        self.current_stage = "preflop"

        dealer_name = self.get_table_player_name(
            self.dealer_index
        )

        self.log_hand_event(
            "dealer",
            f"Dealer: {dealer_name}.",
            actor_index=self.dealer_index
        )

        # Reset the street before blinds are posted so the blind
        # chips count toward the preflop round wagers.
        self.reset_betting_round(
            assign_actor=False
        )

        # ==================================================
        # Post small blind / big blind
        # ==================================================

        self.post_blind(
            self.small_blind_index,
            self.small_blind,
            "SB"
        )

        self.post_blind(
            self.big_blind_index,
            self.big_blind,
            "BB"
        )

        # A short all-in big blind keeps the nominal wager while two or
        # more seats can still act; otherwise only what was posted can
        # be called (core.opening_current_bet).
        self.set_opening_wager(
            self.big_blind,
            self.big_blind
        )

        # ==================================================
        # Busted seat labels
        # ==================================================

        for npc_index in range(
                len(self.npcs)
        ):

            if self.npc_busted[npc_index]:
                self.npc_action_texts[
                    npc_index
                ] = "Busted"

        # ==================================================
        # Hole cards
        # ==================================================

        # A busted seat 0 is dealt nothing. Only a network spectator
        # table gets here with one (single-player stopped above), so the
        # single-player deal order is unchanged.
        for _ in range(2):

            if not self.player_busted:
                self.player_hand.append(
                    self.draw_card()
                )

            for npc_index in range(
                    len(self.npcs)
            ):

                if self.npc_busted[
                    npc_index
                ]:
                    continue

                self.npc_hands[
                    npc_index
                ].append(
                    self.draw_card()
                )

        if self.player_hand:

            player_cards_text = format_poker_cards(
                self.player_hand
            )

            self.log_hand_event(
                "hole_cards",
                f"You are dealt {player_cards_text}.",
                actor_index=0,
                cards=[
                    dict(card)
                    for card in self.player_hand
                    if card
                ]
            )

        # ==================================================
        # Correct preflop action order
        # ==================================================

        self.set_first_actor_from(
            self.get_preflop_first_actor_index()
        )

        return True

    # ==================================================
    # ADVANCE AFTER BETTING ROUND
    # ==================================================

    def advance_after_betting_round(self):

        if not self.is_betting_round_complete():
            return False

        if self.current_stage == "preflop":

            return self.deal_flop()

        elif self.current_stage == "flop":

            return self.deal_turn()

        elif self.current_stage == "turn":

            return self.deal_river()

        elif self.current_stage == "river":

            return self.showdown()

        return False

    # ==================================================
    # RUN ONE NPC ACTION
    # ==================================================

    def run_next_npc_action(self):

        self.ensure_npc_action_state()
        self.ensure_npc_bet_chunk_state()

        if (
                self.hand_complete
                or self.betting_round_complete
        ):
            return False

        if self.current_actor == 0:
            return False

        npc_index = self.current_actor - 1

        if not (
                0
                <= npc_index
                < len(self.npcs)
        ):
            self.advance_to_next_actor()
            return False

        # Repair impossible stale all-in state.
        if (
                self.npc_all_in[npc_index]
                and self.npc_stacks[npc_index] > 0
        ):
            self.npc_all_in[npc_index] = False

        if not self.actor_needs_action(
                self.current_actor
        ):
            self.advance_to_next_actor()
            return False

        if (
                self.npc_busted[npc_index]
                or self.npc_folded[npc_index]
                or self.npc_all_in[npc_index]
        ):
            self.advance_to_next_actor()
            return False

        if self.npc_stacks[npc_index] <= 0:
            self.npc_all_in[npc_index] = True
            self.npc_has_acted[npc_index] = True
            self.advance_to_next_actor()
            return False

        personality = self.get_npc_personality(
            npc_index
        )

        strength = self.get_npc_hand_strength(
            npc_index
        )

        context = self.build_npc_ai_context(
            npc_index,
            strength=strength
        )

        decision = decide_poker_action(
            personality,
            context
        )

        if len(self.npc_ai_last_decisions) != len(
                self.npcs
        ):
            self.npc_ai_last_decisions = [
                None
                for _ in self.npcs
            ]

        self.npc_ai_last_decisions[npc_index] = dict(
            decision
        )

        action = decision.get(
            "action",
            "check"
        )

        profile = decision.get(
            "profile",
            get_poker_personality_profile(
                "balanced"
            )
        )

        bluff = bool(
            decision.get(
                "bluff",
                False
            )
        )

        success = False

        if action == "fold":
            success = self.npc_fold(
                npc_index
            )

        elif action == "call":
            success = self.npc_call(
                npc_index
            )

        elif action == "check":
            success = self.npc_check(
                npc_index
            )

        elif action == "bet":
            bet_amount = self.get_npc_open_bet_amount(
                npc_index,
                strength,
                profile,
                bluff=bluff
            )

            if bet_amount is not None:
                success = self.npc_bet(
                    npc_index,
                    bet_amount
                )

        elif action == "raise":
            raise_to = self.get_npc_raise_to_amount(
                npc_index,
                strength,
                profile,
                bluff=bluff
            )

            if raise_to is not None:
                success = self.npc_raise(
                    npc_index,
                    raise_to
                )

        # ==================================================
        # Defensive legal fallback
        # ==================================================

        if not success and not self.hand_complete:
            amount_to_call = self.get_npc_amount_to_call(
                npc_index
            )

            if amount_to_call > 0:
                # If the desired action failed, a legal call is
                # preferable to leaving the turn unresolved.
                success = self.npc_call(
                    npc_index
                )

                if not success:
                    success = self.npc_fold(
                        npc_index
                    )

            else:
                success = self.npc_check(
                    npc_index
                )

        # npc_fold() may have awarded the pot immediately.
        if self.hand_complete:
            return success

        self.advance_to_next_actor()

        return success

    def get_actionable_player_indexes(self):

        actionable = []

        if (
                not self.player_busted
                and not self.player_folded
                and self.player_stack > 0
        ):
            actionable.append(0)

        for npc_index in range(
                len(self.npcs)
        ):

            if (
                    self.npc_busted[npc_index]
                    or self.npc_folded[npc_index]
                    or self.npc_stacks[npc_index] <= 0
            ):
                continue

            actionable.append(
                npc_index + 1
            )

        return actionable

    def should_reveal_runout_hands(self):
        """Expose live hands only once no further betting or outstanding call exists."""
        if self.current_stage not in ('preflop','flop','turn','river') or self.hand_complete:
            return False
        # Two or more seats still in the hand, and betting is closed for it
        # (core.betting_closed: every call settled, at most one seat with chips).
        return (
                len(self.get_active_player_indexes()) >= 2
                and betting_closed(
                    self.seat_in_hand(),
                    self.seat_stacks(),
                    self.seat_round_bets(),
                    self.current_bet
                )
        )

    def is_betting_round_complete(self):

        active_indexes = (
            self.get_active_player_indexes()
        )

        actionable_indexes = (
            self.get_actionable_player_indexes()
        )

        # ==================================================
        # First make sure every player who still CAN respond
        # has matched the current wager. This must happen before
        # the all-in auto-runout shortcut.
        # ==================================================

        if (
                not self.player_busted
                and not self.player_folded
                and self.player_stack > 0
        ):

            if self.player_all_in:
                self.player_all_in = False

            if (
                    self.player_round_bet
                    < self.current_bet
            ):
                return False

        for npc_index in range(
                len(self.npcs)
        ):

            if (
                    self.npc_busted[npc_index]
                    or self.npc_folded[npc_index]
                    or self.npc_stacks[npc_index] <= 0
            ):
                continue

            if self.npc_all_in[npc_index]:
                self.npc_all_in[npc_index] = False

            if (
                    self.npc_round_bets[npc_index]
                    < self.current_bet
            ):
                return False

        # ==================================================
        # Once all outstanding calls are settled, there is no
        # reason to make the lone player with chips check through
        # empty streets against only all-in opponents
        # (core.betting_closed: the all-in run-out).
        # ==================================================

        if (
                len(active_indexes) > 1
                and betting_closed(
                    self.seat_in_hand(),
                    self.seat_stacks(),
                    self.seat_round_bets(),
                    self.current_bet
                )
        ):
            return True

        # ==================================================
        # Normal acted-state checks
        # ==================================================

        if 0 in actionable_indexes:
            if not self.player_has_acted:
                return False

        for player_index in actionable_indexes:

            if player_index == 0:
                continue

            npc_index = player_index - 1

            if not self.npc_has_acted[npc_index]:
                return False

        return True

    # ==================================================
    # RESET BETTING ROUND
    # ==================================================

    def reset_betting_round(
            self,
            first_actor=None,
            assign_actor=True
    ):

        self.current_bet = 0
        self.last_raise_size = 0
        self.last_raiser = None
        self.last_wager_full = False

        # ==================================================
        # Round wagers
        # ==================================================

        self.player_round_bet = 0

        self.npc_round_bets = [
            0
            for _ in self.npcs
        ]

        self.player_bet_chunks = []

        self.npc_bet_chunks = [
            []
            for _ in self.npcs
        ]

        # ==================================================
        # Action labels
        # ==================================================

        self.player_action_text = ""

        self.npc_action_texts = [
            ""
            for _ in self.npcs
        ]

        # ==================================================
        # Acted flags
        # ==================================================

        self.player_has_acted = (
                self.player_busted
                or self.player_folded
                or (
                    self.player_all_in
                    and self.player_stack <= 0
                )
        )

        self.npc_has_acted = []

        for npc_index in range(
                len(self.npcs)
        ):

            inactive = (
                    self.npc_busted[npc_index]
                    or self.npc_folded[npc_index]
                    or (
                        self.npc_all_in[npc_index]
                        and self.npc_stacks[npc_index] <= 0
                    )
            )

            self.npc_has_acted.append(
                inactive
            )

        self.current_actor = -1
        self.betting_round_complete = False

        if not assign_actor:
            return

        if first_actor is None:
            first_actor = (
                self.get_postflop_first_actor_index()
            )

        self.set_first_actor_from(
            first_actor
        )

    # ==================================================
    # COMMUNITY CARDS
    # ==================================================

    def deal_flop(self):

        if self.current_stage != "preflop":
            return False

        # Burn
        self.draw_card()

        for _ in range(3):
            self.community_cards.append(
                self.draw_card()
            )

        self.current_stage = "flop"

        flop_cards = self.community_cards[:3]

        self.log_hand_event(
            "flop",
            f"Flop: {format_poker_cards(flop_cards)}.",
            cards=[
                dict(card)
                for card in flop_cards
                if card
            ]
        )

        self.reset_betting_round(
            first_actor=(
                self.get_postflop_first_actor_index()
            )
        )

        return True

    def deal_turn(self):

        if self.current_stage != "flop":
            return False

        # Burn
        self.draw_card()

        self.community_cards.append(
            self.draw_card()
        )

        self.current_stage = "turn"

        turn_card = self.community_cards[-1]

        self.log_hand_event(
            "turn",
            f"Turn: {format_poker_cards([turn_card])}.",
            cards=[dict(turn_card)] if turn_card else []
        )

        self.reset_betting_round(
            first_actor=(
                self.get_postflop_first_actor_index()
            )
        )

        return True

    def deal_river(self):

        if self.current_stage != "turn":
            return False

        # Burn
        self.draw_card()

        self.community_cards.append(
            self.draw_card()
        )

        self.current_stage = "river"

        river_card = self.community_cards[-1]

        self.log_hand_event(
            "river",
            f"River: {format_poker_cards([river_card])}.",
            cards=[dict(river_card)] if river_card else []
        )

        self.reset_betting_round(
            first_actor=(
                self.get_postflop_first_actor_index()
            )
        )

        return True
