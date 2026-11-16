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

class TexasHoldemGame:

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

    # ==================================================
    # CHIP COMMITMENT HELPERS
    # ==================================================

    def commit_player_chips(
            self,
            amount,
            count_round_bet=True,
            show_chunk=True
    ):

        amount = max(
            0,
            int(amount)
        )

        amount_paid = min(
            amount,
            self.player_stack
        )

        if amount_paid <= 0:
            return 0

        self.player_stack -= (
            amount_paid
        )

        self.player_hand_contribution += (
            amount_paid
        )

        self.pot += (
            amount_paid
        )

        if count_round_bet:
            self.player_round_bet += (
                amount_paid
            )

        if show_chunk:
            self.player_bet_chunks.append(
                amount_paid
            )

        if self.player_stack == 0:
            self.player_all_in = True

        return amount_paid

    def commit_npc_chips(
            self,
            npc_index,
            amount,
            count_round_bet=True,
            show_chunk=True
    ):

        if not (
                0
                <= npc_index
                < len(self.npcs)
        ):
            return 0

        amount = max(
            0,
            int(amount)
        )

        amount_paid = min(
            amount,
            self.npc_stacks[
                npc_index
            ]
        )

        if amount_paid <= 0:
            return 0

        self.npc_stacks[
            npc_index
        ] -= amount_paid

        self.npc_hand_contributions[
            npc_index
        ] += amount_paid

        self.pot += (
            amount_paid
        )

        if count_round_bet:
            self.npc_round_bets[
                npc_index
            ] += amount_paid

        if show_chunk:
            self.npc_bet_chunks[
                npc_index
            ].append(
                amount_paid
            )

        if (
                self.npc_stacks[
                    npc_index
                ]
                == 0
        ):
            self.npc_all_in[
                npc_index
            ] = True

        return amount_paid

    # ==================================================
    # TABLE POSITION / BLIND HELPERS
    # ==================================================

    def get_live_player_indexes(self):

        live_indexes = []

        if (
                not self.player_busted
                and self.player_stack > 0
        ):
            live_indexes.append(0)

        for npc_index, stack in enumerate(
                self.npc_stacks
        ):

            busted = (
                    npc_index < len(self.npc_busted)
                    and self.npc_busted[npc_index]
            )

            if not busted and stack > 0:
                live_indexes.append(
                    npc_index + 1
                )

        return live_indexes

    def get_next_live_player_index(
            self,
            current_index
    ):

        actor_count = len(self.npcs) + 1
        live_indexes = set(
            self.get_live_player_indexes()
        )

        if not live_indexes:
            return None

        for offset in range(
                1,
                actor_count + 1
        ):

            candidate = (
                    current_index + offset
            ) % actor_count

            if candidate in live_indexes:
                return candidate

        return None

    def rotate_dealer(self):

        live_indexes = (
            self.get_live_player_indexes()
        )

        if not live_indexes:
            self.dealer_index = None
            return None

        next_dealer = (
            self.get_next_live_player_index(
                self.dealer_index
                if self.dealer_index is not None
                else -1
            )
        )

        self.dealer_index = next_dealer

        return next_dealer

    def assign_blind_positions(self):

        live_indexes = (
            self.get_live_player_indexes()
        )

        self.small_blind_index = None
        self.big_blind_index = None

        if len(live_indexes) < 2:
            return False

        # Heads-up exception: dealer posts the small blind.
        if len(live_indexes) == 2:
            self.small_blind_index = (
                self.dealer_index
            )

            self.big_blind_index = (
                self.get_next_live_player_index(
                    self.dealer_index
                )
            )

            return True

        self.small_blind_index = (
            self.get_next_live_player_index(
                self.dealer_index
            )
        )

        self.big_blind_index = (
            self.get_next_live_player_index(
                self.small_blind_index
            )
        )

        return True

    def get_preflop_first_actor_index(self):

        live_indexes = (
            self.get_active_player_indexes()
        )

        if len(live_indexes) < 2:
            return None

        # Heads-up: dealer / small blind acts first preflop.
        if len(live_indexes) == 2:
            return self.dealer_index

        # Three or more: action begins left of the big blind.
        return self.get_next_live_player_index(
            self.big_blind_index
        )

    def get_postflop_first_actor_index(self):

        # Postflop action always starts with the first live seat
        # clockwise from the dealer. Folded/all-in seats are then
        # skipped by set_first_actor_from().
        if self.dealer_index is None:
            return None

        return self.get_next_live_player_index(
            self.dealer_index
        )

    def set_first_actor_from(
            self,
            starting_index
    ):

        if starting_index is None:
            self.current_actor = -1
            self.betting_round_complete = True
            return None

        actor_count = len(self.npcs) + 1

        for offset in range(actor_count):

            candidate = (
                    starting_index + offset
            ) % actor_count

            if self.actor_needs_action(
                    candidate
            ):
                self.current_actor = candidate
                self.betting_round_complete = False
                return candidate

        self.current_actor = -1
        self.betting_round_complete = True

        return None

    def post_blind(
            self,
            player_index,
            blind_amount,
            blind_label
    ):

        blind_amount = max(
            0,
            int(blind_amount)
        )

        if blind_amount <= 0:
            return 0

        if player_index == 0:

            amount_paid = (
                self.commit_player_chips(
                    blind_amount,
                    count_round_bet=True,
                    show_chunk=True
                )
            )

            if amount_paid > 0:
                self.player_action_text = (
                    f"{blind_label} ${amount_paid:,}"
                )

                blind_name = (
                    "small blind"
                    if blind_label == "SB"
                    else "big blind"
                )

                suffix = (
                    " and are all-in."
                    if self.player_all_in
                    else "."
                )

                self.log_hand_event(
                    "blind",
                    (
                        f"You post the {blind_name} "
                        f"${amount_paid:,}{suffix}"
                    ),
                    actor_index=0,
                    amount=amount_paid,
                    blind=blind_name,
                    all_in=self.player_all_in
                )

            return amount_paid

        npc_index = player_index - 1

        if not (
                0 <= npc_index < len(self.npcs)
        ):
            return 0

        amount_paid = (
            self.commit_npc_chips(
                npc_index,
                blind_amount,
                count_round_bet=True,
                show_chunk=True
            )
        )

        if amount_paid > 0:
            self.npc_action_texts[npc_index] = (
                f"{blind_label} ${amount_paid:,}"
            )

            blind_name = (
                "small blind"
                if blind_label == "SB"
                else "big blind"
            )

            name = self.get_table_player_name(
                player_index
            )

            suffix = (
                " and is all-in."
                if self.npc_all_in[npc_index]
                else "."
            )

            self.log_hand_event(
                "blind",
                (
                    f"{name} posts the {blind_name} "
                    f"${amount_paid:,}{suffix}"
                ),
                actor_index=player_index,
                amount=amount_paid,
                blind=blind_name,
                all_in=self.npc_all_in[npc_index]
            )

        return amount_paid

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
    # BETTING HELPERS
    # ==================================================
    def npc_raise(
            self,
            npc_index,
            raise_to
    ):

        self.ensure_npc_bet_chunk_state()
        self.ensure_npc_action_state()
        self.last_wager_full = False

        if not (
                0
                <= npc_index
                < len(self.npcs)
        ):
            return False

        if (
                self.npc_busted[npc_index]
                or self.npc_folded[npc_index]
                or self.npc_all_in[npc_index]
        ):
            return False

        if self.current_bet <= 0:
            return False

        stack = (
            self.npc_stacks[
                npc_index
            ]
        )

        if stack <= 0:
            return False

        maximum_raise_to = (
                self.npc_round_bets[
                    npc_index
                ]
                + stack
        )

        minimum_raise_to = (
            self.get_minimum_raise_to()
        )

        raise_to = int(
            raise_to
        )

        if raise_to <= self.current_bet:
            return False

        if (
                raise_to < minimum_raise_to
                and raise_to < maximum_raise_to
        ):
            return False

        target = min(
            raise_to,
            maximum_raise_to
        )

        # B36: a raise needs somebody left to respond (and an open
        # betting round). A short stack's all-in call is still allowed.
        if (
                target > self.current_bet
                and not self.can_npc_raise(npc_index)
        ):
            return False

        old_current_bet = (
            self.current_bet
        )

        amount_needed = (
                target
                - self.npc_round_bets[
                    npc_index
                ]
        )

        if amount_needed <= 0:
            return False

        amount_paid = (
            self.commit_npc_chips(
                npc_index,
                amount_needed
            )
        )

        if amount_paid <= 0:
            return False

        self.apply_wager(
            npc_index + 1,
            old_current_bet,
            self.npc_round_bets[npc_index],
            self.get_minimum_raise_size()
        )

        self.npc_has_acted[
            npc_index
        ] = True

        self.npc_action_texts[
            npc_index
        ] = (
            f"Raised to "
            f"${self.npc_round_bets[npc_index]:,}"
        )

        name = self.get_table_player_name(
            npc_index + 1
        )

        suffix = (
            " and is all-in."
            if self.npc_all_in[npc_index]
            else "."
        )

        self.log_hand_event(
            "raise",
            (
                f"{name} raises to "
                f"${self.npc_round_bets[npc_index]:,}"
                f"{suffix}"
            ),
            actor_index=npc_index + 1,
            amount=amount_paid,
            raise_to=self.npc_round_bets[npc_index],
            all_in=self.npc_all_in[npc_index]
        )

        return True

    def npc_bet(
            self,
            npc_index,
            amount
    ):

        self.ensure_npc_bet_chunk_state()
        self.ensure_npc_action_state()
        self.last_wager_full = False

        if not (
                0
                <= npc_index
                < len(self.npcs)
        ):
            return False

        if self.current_bet > 0:
            return False

        if (
                self.npc_busted[npc_index]
                or self.npc_folded[npc_index]
                or self.npc_all_in[npc_index]
        ):
            return False

        stack = (
            self.npc_stacks[
                npc_index
            ]
        )

        if stack <= 0:
            return False

        # B36: a bet needs somebody left to respond.
        if not self.can_npc_raise(npc_index):
            return False

        amount = int(
            amount
        )

        minimum_bet = (
            self.get_minimum_open_bet()
        )

        if (
                amount < minimum_bet
                and amount < stack
        ):
            return False

        target_amount = min(
            max(
                1,
                amount
            ),
            stack
        )

        old_current_bet = (
            self.current_bet
        )

        amount_paid = (
            self.commit_npc_chips(
                npc_index,
                target_amount
            )
        )

        if amount_paid <= 0:
            return False

        self.apply_wager(
            npc_index + 1,
            old_current_bet,
            self.npc_round_bets[npc_index],
            minimum_bet
        )

        self.npc_has_acted[
            npc_index
        ] = True

        self.npc_action_texts[
            npc_index
        ] = (
            f"Bet ${amount_paid:,}"
        )

        name = self.get_table_player_name(
            npc_index + 1
        )

        suffix = (
            " and is all-in."
            if self.npc_all_in[npc_index]
            else "."
        )

        self.log_hand_event(
            "bet",
            f"{name} bets ${amount_paid:,}{suffix}",
            actor_index=npc_index + 1,
            amount=amount_paid,
            all_in=self.npc_all_in[npc_index]
        )

        return True

    def apply_wager(
            self,
            seat,
            old_current_bet,
            new_total,
            minimum_size
    ):
        """Record a bet or raise that took seat's round bet to new_total.

        The bet to call rises to new_total if it is higher. Only a full
        wager (at least minimum_size more, core.classify_wager) sets the
        next minimum raise, becomes the last raise and reopens betting
        for the seats that already acted. Returns whether it was full.
        """
        increase, full = classify_wager(
            old_current_bet,
            new_total,
            minimum_size
        )

        if increase > 0:
            self.current_bet = new_total

        if full:
            self.last_raise_size = increase
            self.last_raiser = seat
            self.reset_actions_after_aggression(
                seat
            )

        self.last_wager_full = full

        return full

    # ==================================================
    # RESET ACTIONS AFTER BET / RAISE
    # ==================================================

    def reset_actions_after_aggression(
            self,
            aggressor_index
    ):

        # ==================================================
        # Human
        # ==================================================

        if (
                not self.player_busted
                and not self.player_folded
                and not self.player_all_in
        ):
            self.player_has_acted = False

        # ==================================================
        # NPCs
        # ==================================================

        for npc_index in range(
                len(self.npcs)
        ):

            if (
                    not self.npc_busted[npc_index]
                    and not self.npc_folded[npc_index]
                    and not self.npc_all_in[npc_index]
            ):
                self.npc_has_acted[
                    npc_index
                ] = False

        # ==================================================
        # Aggressor already acted
        # ==================================================

        if aggressor_index == 0:

            self.player_has_acted = True

        else:

            npc_index = (
                    aggressor_index - 1
            )

            if (
                    0
                    <= npc_index
                    < len(self.npc_has_acted)
            ):
                self.npc_has_acted[
                    npc_index
                ] = True

    # ==================================================
    # ACTOR / TURN HELPERS
    # ==================================================

    def refresh_busted_state(self):

        # ==================================================
        # Remember previous state
        # ==================================================

        previous_player_busted = (
            self.player_busted
        )

        previous_npc_busted = list(
            self.npc_busted
        )

        # Make defensive length correction.
        if len(previous_npc_busted) != len(
                self.npcs
        ):
            previous_npc_busted = [
                False
                for _ in self.npcs
            ]

        # ==================================================
        # Refresh current state
        # ==================================================

        self.player_busted = (
                self.player_stack <= 0
        )

        self.npc_busted = [
            stack <= 0
            for stack in self.npc_stacks
        ]

        # ==================================================
        # Who JUST busted?
        #
        # Table indexes:
        # 0 = player
        # 1+ = NPCs
        # ==================================================

        newly_busted = []

        if (
                self.player_busted
                and not previous_player_busted
        ):
            newly_busted.append(
                0
            )

        for npc_index in range(
                len(self.npcs)
        ):

            if (
                    self.npc_busted[npc_index]
                    and not previous_npc_busted[
                npc_index
            ]
            ):
                newly_busted.append(
                    npc_index + 1
                )

        self.last_hand_busted_indexes = (
            newly_busted
        )

        return newly_busted

    def all_npcs_busted(self):

        return (
                bool(self.npcs)
                and all(
            self.npc_busted
        )
        )

    def table_is_over(self):
        """True when the session cannot go on (core.session_over).

        Meant for between hands: during a hand an all-in seat has 0 chips
        but is still playing. Once refresh_busted_state() has run at the
        end of a hand this equals player_busted or all_npcs_busted().
        """

        return session_over(
            self.seat_stacks()
        )

    def ensure_npc_bet_chunk_state(self):

        npc_count = len(
            self.npcs
        )

        if len(
                self.npc_bet_chunks
        ) != npc_count:
            self.npc_bet_chunks = [
                []
                for _ in range(
                    npc_count
                )
            ]

    def ensure_npc_action_state(self):

        npc_count = len(
            self.npcs
        )

        if len(
                self.npc_action_texts
        ) != npc_count:
            self.npc_action_texts = [
                ""
                for _ in range(
                    npc_count
                )
            ]

    def actor_needs_action(
            self,
            actor_index
    ):

        # ==================================================
        # Human player
        # ==================================================

        if actor_index == 0:

            if (
                    self.player_busted
                    or self.player_folded
            ):
                return False

            # Only truly all-in if the stack is actually 0.
            if (
                    self.player_all_in
                    and self.player_stack <= 0
            ):
                return False

            # Repair stale all-in state.
            if (
                    self.player_all_in
                    and self.player_stack > 0
            ):
                self.player_all_in = False

            return (
                    not self.player_has_acted
                    or self.player_round_bet
                    < self.current_bet
            )

        # ==================================================
        # NPC
        # ==================================================

        npc_index = (
                actor_index - 1
        )

        if not (
                0
                <= npc_index
                < len(self.npcs)
        ):
            return False

        if (
                self.npc_busted[npc_index]
                or self.npc_folded[npc_index]
        ):
            return False

        # Only skip an all-in NPC when that NPC
        # actually has no chips remaining.
        if (
                self.npc_all_in[npc_index]
                and self.npc_stacks[npc_index] <= 0
        ):
            return False

        # Repair impossible/stale state:
        # positive stack + all-in flag.
        if (
                self.npc_all_in[npc_index]
                and self.npc_stacks[npc_index] > 0
        ):
            self.npc_all_in[npc_index] = False

        return (
                not self.npc_has_acted[npc_index]
                or self.npc_round_bets[npc_index]
                < self.current_bet
        )

    def advance_to_next_actor(self):

        # A fold or an all-in may have left one seat with chips. If it
        # has already matched what the others put in, nobody can bet
        # any more: no turn is offered and the hand runs out
        # (core.bet_to_match, core.betting_closed).
        self.settle_bet_to_match()

        if (
                len(self.get_active_player_indexes()) > 1
                and betting_closed(
                    self.seat_in_hand(),
                    self.seat_stacks(),
                    self.seat_round_bets(),
                    self.current_bet
                )
        ):
            self.current_actor = -1
            self.betting_round_complete = True
            return None

        actor_count = (
                len(self.npcs) + 1
        )

        for offset in range(
                1,
                actor_count + 1
        ):

            candidate = (
                                self.current_actor + offset
                        ) % actor_count

            if self.actor_needs_action(
                    candidate
            ):
                self.current_actor = (
                    candidate
                )

                self.betting_round_complete = False

                return candidate

        self.betting_round_complete = True

        return None

    # ==================================================
    # ACTIVE PLAYERS
    # ==================================================

    def get_active_player_indexes(self):

        active_indexes = []

        # Human = index 0
        if (
                not self.player_busted
                and not self.player_folded
        ):
            active_indexes.append(
                0
            )

        # NPCs = indexes 1+
        for npc_index in range(
                len(self.npcs)
        ):

            if (
                    not self.npc_busted[npc_index]
                    and not self.npc_folded[npc_index]
            ):
                active_indexes.append(
                    npc_index + 1
                )

        return active_indexes

    # ==================================================
    # SEAT VIEWS
    #
    # Read-only per-seat lists for the shared table rules
    # in core.py. Seat 0 is the human, seat i is npcs[i-1].
    # ==================================================

    def seat_count(self):

        return len(self.npcs) + 1

    def seat_stacks(self):

        return [self.player_stack, *self.npc_stacks]

    def seat_round_bets(self):

        return [self.player_round_bet, *self.npc_round_bets]

    def seat_in_hand(self):
        """Per seat: not busted and not folded (get_active_player_indexes)."""

        return [
            not self.player_busted and not self.player_folded,
            *(
                not self.npc_busted[npc_index]
                and not self.npc_folded[npc_index]
                for npc_index in range(len(self.npcs))
            ),
        ]

    def seat_at_table(self):
        """Per seat: not knocked out of the session (npc_inputs' observers).

        Busted is only set between hands, so a seat that is all-in with 0
        chips is still at the table during the hand it is playing.
        """

        busted = self.npc_busted

        return [
            not self.player_busted,
            *(
                not (npc_index < len(busted) and busted[npc_index])
                for npc_index in range(len(self.npcs))
            ),
        ]

    def seat_can_act(self):
        """Per seat: in the hand with chips left (get_actionable_player_indexes)."""

        return [
            in_hand and stack > 0
            for in_hand, stack in zip(
                self.seat_in_hand(),
                self.seat_stacks()
            )
        ]

    def seat_has_acted(self):

        return [self.player_has_acted, *self.npc_has_acted]

    # ==================================================
    # SIDE POT HELPERS
    # ==================================================

    def get_hand_contributions(self):

        return [
            self.player_hand_contribution,
            *self.npc_hand_contributions
        ]

    def is_showdown_eligible(
            self,
            player_index
    ):

        # Human
        if player_index == 0:
            return (
                    not self.player_folded
                    and len(self.player_hand) >= 2
            )

        # NPC
        npc_index = (
                player_index - 1
        )

        if not (
                0
                <= npc_index
                < len(self.npcs)
        ):
            return False

        return (
                not self.npc_folded[npc_index]
                and len(
            self.npc_hands[
                npc_index
            ]
        ) >= 2
        )

    def build_side_pots(self):
        """The main pot and side pots by core.build_pots (compatibility).

        Uncalled chips and layers no showdown-eligible seat paid into are
        refunds there, not pots, so they are not in this list.
        """
        return build_pots(
            self.get_hand_contributions(),
            [
                self.is_showdown_eligible(seat)
                for seat in range(self.seat_count())
            ]
        )[0]

    def get_display_pot_amount(self):
        """Pot amount the table should display right now."""
        if (
                self.current_stage == "showdown"
                or self.hand_complete
        ):
            return max(
                0,
                int(self.last_resolved_pot)
            )

        return max(
            0,
            int(self.pot)
        )

    def has_true_side_pots(self, showdown_indexes):
        """Return True only when live showdown players had unequal stakes.

        core.build_pots already folds dead money from folded seats into
        the pot it was paid towards, so with equal live stakes there is a
        single pot. Only real side pots are labelled in the hand history.
        """
        contributions = self.get_hand_contributions()

        showdown_levels = {
            contributions[player_index]
            for player_index in showdown_indexes
            if (
                    0 <= player_index < len(contributions)
                    and contributions[player_index] > 0
            )
        }

        return (
                len(showdown_levels) > 1
                and len(self.last_pot_awards) > 1
        )

    def log_detailed_pot_awards(self, showdown_indexes):
        if not self.has_true_side_pots(showdown_indexes):
            return False

        for pot_index, pot_award in enumerate(
                self.last_pot_awards
        ):
            pot_label = (
                "Main pot"
                if pot_index == 0
                else f"Side pot {pot_index}"
            )

            pot_amount = int(
                pot_award.get(
                    "amount",
                    0
                )
            )

            winners = list(
                pot_award.get(
                    "winners",
                    []
                )
            )

            winner_names = [
                self.get_table_player_name(player_index)
                for player_index in winners
            ]

            # A pot only one seat could win beat nobody (core.
            # collected_uncontested): it is collected, with no winning hand.
            if winners and collected_uncontested(
                    pot_award,
                    self.last_pot_awards
            ):
                collector = winners[0]
                collected = int(
                    pot_award.get("payouts", {}).get(collector, pot_amount)
                )
                who = (
                    "you collect"
                    if collector == 0
                    else f"{winner_names[0]} collects"
                )
                self.log_hand_event(
                    "pot_award",
                    f"{pot_label} ${pot_amount:,}: nobody else could win "
                    f"it; {who} ${collected:,}.",
                    amount=pot_amount,
                    winners=winners,
                    pot_index=pot_index
                )
                continue

            # "You win" / "<Name> wins"; one winner "receives", tied
            # winners "each receive".
            if len(winner_names) == 1:
                human = winners[0] == 0
                award_text = (
                    f"{pot_label} ${pot_amount:,}: "
                    f"{winner_names[0]} {'win' if human else 'wins'}."
                )
                receives = (
                    f"{winner_names[0]} "
                    f"{'receive' if human else 'receives'}"
                )
            else:
                # "split between you and Ada" / "between Ada, Bo and you".
                names = [
                    "you" if player_index == 0 else name
                    for player_index, name in zip(winners, winner_names)
                ]
                award_text = (
                    f"{pot_label} ${pot_amount:,}: "
                    f"split between {join_poker_names(names)}."
                )
                receives = "Each winner receives"

            detail = pot_award.get("hand", "")
            if detail:
                share = int(pot_award.get("share", pot_amount))
                award_text += f" Winning hand: {detail}. {receives} ${share:,}"
                # Name the winners who got an odd chip (the first ones in
                # odd-chip order): "(odd chip to Ada)", "(odd chips to Ada
                # and you)".
                remainder = int(pot_award.get("remainder", 0) or 0)
                if remainder:
                    payouts = pot_award.get("payouts")
                    odd_seats = [
                        player_index
                        for player_index in winners
                        if int(payouts.get(player_index, 0)) > share
                    ] if payouts else winners[:remainder]
                    odd_names = [
                        "you" if player_index == 0 else name
                        for player_index, name in zip(winners, winner_names)
                        if player_index in odd_seats
                    ]
                    award_text += (
                        f" (odd chip{'s' if len(odd_names) > 1 else ''} "
                        f"to {join_poker_names(odd_names)})"
                    )
                award_text += "."
            self.log_hand_event(
                "pot_award",
                award_text,
                amount=pot_amount,
                winners=winners,
                pot_index=pot_index
            )

        return True

    def finalize_showdown_display_state(self):
        """Clear stale action labels while preserving final statuses."""
        if self.player_busted:
            self.player_action_text = "Busted"
        elif self.player_folded:
            self.player_action_text = "Folded"
        else:
            self.player_action_text = ""

        cleaned_actions = []

        for npc_index in range(len(self.npcs)):
            if (
                    npc_index < len(self.npc_busted)
                    and self.npc_busted[npc_index]
            ):
                cleaned_actions.append("Busted")

            elif (
                    npc_index < len(self.npc_folded)
                    and self.npc_folded[npc_index]
            ):
                cleaned_actions.append("Folded")

            else:
                cleaned_actions.append("")

        self.npc_action_texts = cleaned_actions

    def get_showdown_result(
            self,
            player_index
    ):

        if player_index == 0:
            return self.evaluate_best_hand(
                self.player_hand
                + self.community_cards
            )

        npc_index = (
                player_index - 1
        )

        return self.evaluate_best_hand(
            self.npc_hands[
                npc_index
            ]
            + self.community_cards
        )

    def get_table_player_name(
            self,
            player_index
    ):

        if player_index == 0:
            return "You"

        npc_index = (
                player_index - 1
        )

        return format_poker_display_name(
            self.npcs[
                npc_index
            ].get(
                "name",
                "Opponent"
            )
        )

    def award_chips_to_player(
            self,
            player_index,
            amount
    ):

        if amount <= 0:
            return

        if player_index == 0:

            self.player_stack += (
                amount
            )

        else:

            npc_index = (
                    player_index - 1
            )

            self.npc_stacks[
                npc_index
            ] += amount

    def log_refund_events(self, refunds):
        """Log one hand-history line per seat that got uncalled chips back."""
        for player_index, amount in sorted(refunds.items()):
            owner = (
                "you"
                if player_index == 0
                else self.get_table_player_name(player_index)
            )

            self.log_hand_event(
                "refund",
                f"Uncalled ${amount:,} returned to {owner}.",
                actor_index=player_index,
                amount=amount
            )

    # ==================================================
    # AWARD POT TO ONE REMAINING PLAYER
    # ==================================================

    def award_pot_to_single_player(
            self,
            winner_index
    ):

        # ==================================================
        # Defensive protection against duplicate resolution
        # ==================================================

        if self.hand_complete:
            return False

        # core.settle_fold_win: settled like a showdown with one live
        # seat. The winner wins the pot of matched chips; uncalled chips
        # go back to whoever put them in, the winner's own included (a
        # shove nobody called, or a short all-in big blind left alone by
        # the folds, which can win only what it matched).
        winnings, refunds = settle_fold_win(
            self.get_hand_contributions(),
            winner_index
        )
        self.last_resolved_pot = max(
            0,
            int(winnings)
        )

        self.award_chips_to_player(
            winner_index,
            winnings
        )

        for player_index, amount in refunds.items():
            self.award_chips_to_player(
                player_index,
                amount
            )

        winner_name = (
            self.get_table_player_name(
                winner_index
            )
        )

        if winner_index == 0:

            self.result_text = (
                f"You win ${winnings:,}."
            )

        else:

            self.result_text = (
                f"{winner_name} wins "
                f"${winnings:,}."
            )

        # The same record shape as a showdown pot (core.award_pots).
        self.last_pot_awards = [
            {
                "amount":
                    winnings,

                # Everyone else folded, so the winner is the only
                # player who could take this pot.
                "eligible":
                    [winner_index],

                "winners":
                    [winner_index],

                "payouts":
                    {winner_index: winnings},

                "share":
                    winnings,

                "remainder":
                    0,

                "hand":
                    "",
            }
        ]

        # Uncalled chips, the winner's own included, are refunds, not
        # winnings (the recap lists them under 'Returned (uncalled):').
        self.last_refunds = dict(refunds)

        self.winner_indexes = [
            winner_index
        ]

        self.log_refund_events(refunds)

        self.log_hand_event(
            "result",
            self.result_text,
            actor_index=winner_index,
            amount=winnings,
            winners=[winner_index]
        )

        self.pot = 0

        self.hand_complete = True

        self.current_actor = -1

        self.current_stage = "showdown"

        newly_busted = self.refresh_busted_state()

        self.log_newly_busted_players(
            newly_busted
        )

        self.finalize_showdown_display_state()

        return True

    # ==================================================
    # RESOLVE HAND AFTER FOLD
    #
    # Shared by Hold'em, Draw and Stud.
    # ==================================================

    def resolve_after_fold(self):

        # ==================================================
        # A completed hand has already been resolved.
        # Never pay or rewrite its result a second time.
        # ==================================================

        if self.hand_complete:
            return False

        active_indexes = (
            self.get_active_player_indexes()
        )

        # ------------------------------------------
        # Network room table: settle the hand only
        # when one seat is left. The room moves the
        # turn on after every fold itself.
        # ------------------------------------------

        if not self.finish_hand_after_player_fold:
            return (
                self.award_pot_to_single_player(
                    active_indexes[0]
                )
                if len(active_indexes) == 1
                else False
            )

        # ------------------------------------------
        # Nobody active
        # Should never happen, but guard against it.
        # ------------------------------------------

        if not active_indexes:
            return False

        # ------------------------------------------
        # Only one player remains
        # ------------------------------------------

        if len(active_indexes) == 1:
            return (
                self.award_pot_to_single_player(
                    active_indexes[0]
                )
            )

        # ------------------------------------------
        # Human folded, NPCs remain
        #
        # The hand goes on: the NPCs still in it keep
        # betting street by street, on the same timers
        # as when the human is all-in (NEW-3).
        # ------------------------------------------

        if (
                self.player_folded
                and self.current_actor == 0
        ):
            self.advance_to_next_actor()

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

    def get_npc_amount_to_call(
            self,
            npc_index
    ):

        if not (
                0
                <= npc_index
                < len(self.npc_stacks)
        ):
            return 0

        return max(
            0,
            self.current_bet
            - self.npc_round_bets[
                npc_index
            ]
        )

    def npc_check(
            self,
            npc_index
    ):

        if self.npc_folded[npc_index]:
            return False

        if (
                self.npc_all_in[npc_index]
                and self.npc_stacks[npc_index] <= 0
        ):
            return False

        if (
                self.get_npc_amount_to_call(
                    npc_index
                )
                != 0
        ):
            return False

        self.npc_has_acted[
            npc_index
        ] = True

        self.npc_action_texts[
            npc_index
        ] = "Checked"

        name = self.get_table_player_name(
            npc_index + 1
        )

        self.log_hand_event(
            "check",
            f"{name} checks.",
            actor_index=npc_index + 1
        )

        return True

    def npc_fold(
            self,
            npc_index
    ):

        self.ensure_npc_action_state()

        if self.npc_folded[npc_index]:
            return False

        if (
                self.npc_all_in[npc_index]
                and self.npc_stacks[npc_index] <= 0
        ):
            return False

        self.npc_folded[
            npc_index
        ] = True

        self.npc_has_acted[
            npc_index
        ] = True

        self.npc_action_texts[
            npc_index
        ] = "Folded"

        name = self.get_table_player_name(
            npc_index + 1
        )

        self.log_hand_event(
            "fold",
            f"{name} folds.",
            actor_index=npc_index + 1
        )

        # ==================================================
        # If this fold leaves only one player,
        # award the pot immediately.
        # ==================================================

        active_indexes = (
            self.get_active_player_indexes()
        )

        if len(active_indexes) == 1:
            self.award_pot_to_single_player(
                active_indexes[0]
            )
        else:
            self.settle_bet_to_match()

        return True

    def npc_call(
            self,
            npc_index
    ):

        self.ensure_npc_action_state()
        self.ensure_npc_bet_chunk_state()

        if not (
                0
                <= npc_index
                < len(self.npcs)
        ):
            return False

        if (
                self.npc_busted[npc_index]
                or self.npc_folded[npc_index]
                or self.npc_all_in[npc_index]
        ):
            return False

        amount_to_call = (
            self.get_npc_amount_to_call(
                npc_index
            )
        )

        if amount_to_call <= 0:
            return False

        amount_paid = (
            self.commit_npc_chips(
                npc_index,
                amount_to_call
            )
        )

        if amount_paid <= 0:
            return False

        self.npc_has_acted[
            npc_index
        ] = True

        self.npc_action_texts[
            npc_index
        ] = (
            f"Called ${amount_paid:,}"
        )

        name = self.get_table_player_name(
            npc_index + 1
        )

        suffix = (
            " and is all-in."
            if self.npc_all_in[npc_index]
            else "."
        )

        self.log_hand_event(
            "call",
            f"{name} calls ${amount_paid:,}{suffix}",
            actor_index=npc_index + 1,
            amount=amount_paid,
            all_in=self.npc_all_in[npc_index]
        )

        return True

    # ==================================================
    # NPC BETTING LOOP
    # ==================================================

    # ==================================================
    # NPC PERSONALITY HELPERS
    # ==================================================

    def get_npc_personality(
            self,
            npc_index
    ):

        if not (
                0
                <= npc_index
                < len(self.npcs)
        ):
            return "balanced"

        return get_poker_personality(
            self.npcs[npc_index]
        )

    def get_npc_effective_personality(
            self,
            npc_index
    ):

        return get_effective_poker_personality(
            self.get_npc_personality(
                npc_index
            )
        )

    def get_npc_personality_profile(
            self,
            npc_index
    ):

        if not 0 <= npc_index < len(self.npcs):
            return "balanced", get_poker_personality_profile("balanced")

        effective_personality = (
            self.get_npc_effective_personality(
                npc_index
            )
        )

        return (
            effective_personality,
            get_poker_personality_profile(self.npcs[npc_index])
        )

    rating_game_key = "texas_holdem"

    def get_npc_skill_factor(
            self,
            npc_index
    ):

        if not (
                0
                <= npc_index
                < len(self.npcs)
        ):
            return 0.55

        return get_poker_skill_factor(
            self.npcs[npc_index], self.rating_game_key
        )

    def get_poker_position_label(
            self,
            player_index
    ):

        if player_index == self.dealer_index:
            return "button"

        if player_index == self.small_blind_index:
            return "small_blind"

        if player_index == self.big_blind_index:
            return "big_blind"

        hand_indexes = list(
            self.hand_seat_indexes
        )

        if not hand_indexes:
            hand_indexes = (
                self.get_live_player_indexes()
            )

        if player_index not in hand_indexes:
            return "unknown"

        if self.big_blind_index is None:
            return "unknown"

        actor_count = len(self.npcs) + 1

        non_blind_indexes = [
            index
            for index in hand_indexes
            if index not in (
                self.dealer_index,
                self.small_blind_index,
                self.big_blind_index,
            )
        ]

        non_blind_indexes.sort(
            key=lambda index: (
                index
                - self.big_blind_index
            ) % actor_count
        )

        if player_index not in non_blind_indexes:
            return "unknown"

        if len(non_blind_indexes) == 1:
            return "early"

        if player_index == non_blind_indexes[-1]:
            return "cutoff"

        if player_index == non_blind_indexes[0]:
            return "early"

        return "middle"

    def build_npc_ai_context(
            self,
            npc_index,
            strength=None
    ):

        if strength is None:
            strength = (
                self.get_npc_hand_strength(
                    npc_index
                )
            )

        stack = self.npc_stacks[npc_index]
        current_round_bet = (
            self.npc_round_bets[npc_index]
        )

        maximum_raise_to = (
            current_round_bet
            + stack
        )

        minimum_raise_to = (
            self.get_minimum_raise_to()
        )

        stage_cap = (
            self.get_npc_stage_bet_cap(
                npc_index
            )
        )

        soft_maximum_raise_to = min(
            maximum_raise_to,
            stage_cap
        )

        active_indexes = (
            self.get_active_player_indexes()
        )

        context = {
            "game": "texas_holdem",
            "stage": self.current_stage,
            "position": self.get_poker_position_label(
                npc_index + 1
            ),
            "hand_strength": strength,
            "pot": self.pot,
            "amount_to_call": self.get_npc_amount_to_call(
                npc_index
            ),
            "stack": stack,
            "current_bet": self.current_bet,
            "current_round_bet": current_round_bet,
            "minimum_open_bet": self.get_minimum_open_bet(),
            "maximum_open_bet": min(
                stack,
                stage_cap
            ),
            "minimum_raise_size": self.get_minimum_raise_size(),
            "minimum_raise_to": minimum_raise_to,
            "maximum_raise_to": maximum_raise_to,
            "soft_maximum_raise_to": soft_maximum_raise_to,
            "can_raise": self.can_npc_raise(
                npc_index
            ),
            "players_remaining": len(
                active_indexes
            ),
            "opponents_remaining": max(
                0,
                len(active_indexes) - 1
            ),
            "last_raiser": self.last_raiser,
            "last_raiser_is_player": (
                self.last_raiser == 0
            ),
        }

        # The inputs every poker variant shares: traits, skill, cash on
        # hand, table reads, player tendencies and grudges.
        context.update(npc_decision_inputs(
            npc=self.npcs[npc_index],
            seat=npc_index + 1,
            rating_game_key=self.rating_game_key,
            stack=stack,
            starting_stack=self.starting_stack,
            hand_number=self.hand_number,
            opponents=self.get_npc_opponent_rows(npc_index),
            last_raiser=self.last_raiser,
            grudge_memory=self.personality_memory,
            table_reads=self.table_reads,
            player_model=self.player_model,
            player_active=(
                not self.player_busted
                and not self.player_folded
            ),
            wealth_scale=self.get_npc_wealth_scale(),
        ))
        context["skill_factor"] = self.get_npc_skill_factor(
            npc_index
        )

        if self.quick_chat_enabled:
            context.update(get_npc_quick_chat_context(self, npc_index))

        return context

    def get_npc_wealth_scale(self):
        """How much of the shared wealth pressure this variant uses (1.0 in Hold'em)."""

        return 1.0


    # ==================================================
    # NPC HAND STRENGTH
    #
    # Returns roughly:
    #
    # 0.00 = garbage
    # 0.25 = weak
    # 0.50 = decent
    # 0.75 = strong
    # 1.00 = monster
    # ==================================================

    def get_npc_opponent_rows(self, npc_index):
        """Public rows (npc_inputs.opponent_rows) for every other seat in the hand."""
        seat = npc_index + 1
        active = self.get_active_player_indexes()
        names = {
            other: self.get_table_player_name(other)
            for other in active if other != seat
        }
        return opponent_rows(seat, active, names, table_identities(self.npcs),
                             self.seat_stacks(), self.seat_round_bets())

    def get_npc_grudge_context(self, npc_index):
        return self.personality_memory.context(self.npcs[npc_index], npc_index + 1,
                                              self.get_npc_opponent_rows(npc_index),
                                              self.last_raiser, self.hand_number)

    def record_personality_showdown(self, results):
        """Only resent an opponent who actually beat this NPC in a contested pot.

        A side-pot winner may still lose another pot, and folded players do not
        get invented showdown grudges. The memory deduplicates repeated hooks.
        """
        awards = [
            {"eligible": sorted(set(pot.get("eligible", results)) & set(results)),
             "winners": list(pot.get("winners", []))}
            for pot in self.last_pot_awards
        ]
        self.personality_memory.record_showdown(
            awards, grudge_seats(self.npcs, self.get_hand_contributions()),
            self.hand_number, self.starting_stack)

    def get_npc_hand_strength(
            self,
            npc_index
    ):

        if not (
                0
                <= npc_index
                < len(self.npc_hands)
        ):
            return 0.0

        hand = (
            self.npc_hands[
                npc_index
            ]
        )

        if len(hand) < 2:
            return 0.0

        # ==================================================
        # PREFLOP
        # ==================================================

        if len(
                self.community_cards
        ) < 3:

            rank_1 = (
                RANK_VALUES[
                    hand[0]["rank"]
                ]
            )

            rank_2 = (
                RANK_VALUES[
                    hand[1]["rank"]
                ]
            )

            high_rank = max(
                rank_1,
                rank_2
            )

            low_rank = min(
                rank_1,
                rank_2
            )

            suited = (
                    hand[0]["suit"]
                    == hand[1]["suit"]
            )

            gap = abs(
                rank_1 - rank_2
            )

            # ------------------------------------------
            # Pocket pair
            # ------------------------------------------

            if rank_1 == rank_2:
                strength = (
                        0.43
                        + (
                                high_rank - 2
                        )
                        / 12.0
                        * 0.52
                )

                return max(
                    0.0,
                    min(
                        strength,
                        1.0
                    )
                )

            # ------------------------------------------
            # Non-pair
            # ------------------------------------------

            strength = (
                    0.08
                    + (
                            high_rank - 2
                    )
                    / 12.0
                    * 0.42
                    + (
                            low_rank - 2
                    )
                    / 12.0
                    * 0.12
            )

            # Suited cards
            if suited:
                strength += 0.07

            # Connected / nearly connected
            if gap == 1:
                strength += 0.07

            elif gap == 2:
                strength += 0.035

            # Two broadway cards
            if (
                    high_rank >= 10
                    and low_rank >= 10
            ):
                strength += 0.08

            # Ace bonus
            if high_rank == 14:
                strength += 0.035

            return max(
                0.0,
                min(
                    strength,
                    0.92
                )
            )

        # ==================================================
        # FLOP / TURN / RIVER
        # ==================================================

        cards = (
                hand
                + self.community_cards
        )

        result = (
            self.evaluate_best_hand(
                cards
            )
        )

        if result is None:
            return 0.0

        score = (
            result[0]
        )

        category = (
            score[0]
        )

        category_strengths = {
            0: 0.18,  # High card
            1: 0.40,  # Pair
            2: 0.58,  # Two pair
            3: 0.69,  # Trips
            4: 0.78,  # Straight
            5: 0.83,  # Flush
            6: 0.91,  # Full house
            7: 0.97,  # Quads
            8: 1.00,  # Straight flush
        }

        strength = (
            category_strengths.get(
                category,
                0.20
            )
        )

        # Give a small boost based on the most
        # important rank in the evaluated hand.
        if (
                len(score) >= 2
                and isinstance(
            score[1],
            int
        )
        ):
            strength += (
                    score[1]
                    / 14.0
                    * 0.06
            )

        return max(
            0.0,
            min(
                strength,
                1.0
            )
        )

    def can_npc_raise(
            self,
            npc_index
    ):

        if not (
                0
                <= npc_index
                < len(self.npcs)
        ):
            return False

        if (
                self.npc_busted[npc_index]
                or self.npc_folded[npc_index]
                or self.npc_all_in[npc_index]
        ):
            return False

        # The shared rule (core.can_raise): chips beyond the call,
        # somebody left to respond (B36), and betting reopened
        # (seat_betting_reopened). An NPC that already acted and only
        # returned because of a short all-in raise may call or fold, but
        # not raise.
        return can_raise(
            npc_index + 1,
            self.seat_in_hand(),
            self.seat_stacks(),
            self.seat_round_bets(),
            self.current_bet,
            reopened=self.seat_betting_reopened(npc_index + 1)
        )

    def seat_betting_reopened(self, seat):
        """May seat bet or raise again this round (core.betting_reopened)?

        No-limit (Hold'em, Draw): a seat that already acted may raise
        again once the short all-ins it faces add up to a full raise
        (TDA Rule 47). Seven-Card Stud overrides this with its
        fixed-limit rule.
        """
        return betting_reopened(
            self.seat_has_acted()[seat],
            self.seat_round_bets()[seat],
            self.current_bet,
            self.get_minimum_raise_size()
        )

    # ==================================================
    # NPC BET SIZING
    # ==================================================

    # ==================================================
    # NPC STREET BETTING CAP
    #
    # This is a SOFT AI cap, not a poker-rule cap.
    # It keeps NPCs from voluntarily detonating their
    # entire stack too early in the hand.
    # ==================================================

    def get_npc_wealth_pressure(
            self,
            npc_index
    ):
        """Return 0..1 pressure from a stack that has grown beyond the buy-in.

        A small run-good bump should not rewrite a personality, so the effect
        begins only after the NPC is at least 15% above the starting stack and
        reaches full strength around 2.5x the original buy-in.
        """
        if not (0 <= npc_index < len(self.npc_stacks)):
            return 0.0

        return wealth_pressure(
            self.npc_stacks[npc_index],
            self.starting_stack
        )

    def get_npc_stage_bet_cap(
            self,
            npc_index
    ):

        stack = self.npc_stacks[npc_index]

        if stack <= 0:
            return self.npc_round_bets[npc_index]

        stage_fractions = {
            "preflop": 0.12,
            "flop": 0.22,
            "turn": 0.40,
            "river": 1.00,
        }

        # Wealthy stacks are allowed to exert more pressure on early/middle
        # streets. The personality AI still decides whether to use this extra
        # room; this merely prevents the old fixed buy-in cap from making a
        # huge chip leader bet exactly like a fresh stack.
        stage_wealth_boost = {
            "preflop": 0.70,
            "flop": 0.85,
            "turn": 0.65,
            "river": 0.50,
        }

        return soft_bet_cap(
            self.starting_stack,
            stage_fractions.get(self.current_stage, 0.25),
            self.get_npc_wealth_pressure(npc_index),
            stage_wealth_boost.get(self.current_stage, 0.45),
            self.get_minimum_open_bet(),
            self.npc_round_bets[npc_index] + stack,
        )

    def get_npc_open_bet_amount(
            self,
            npc_index,
            strength,
            profile,
            bluff=False
    ):

        context = self.build_npc_ai_context(
            npc_index,
            strength=strength
        )

        return choose_poker_open_bet_amount(
            context,
            profile,
            strength,
            bluff=bluff
        )

    def get_npc_raise_to_amount(
            self,
            npc_index,
            strength,
            profile,
            bluff=False
    ):

        context = self.build_npc_ai_context(
            npc_index,
            strength=strength
        )

        return choose_poker_raise_to_amount(
            context,
            profile,
            strength,
            bluff=bluff
        )

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
    # BETTING RULE HELPERS
    # ==================================================

    def get_minimum_open_bet(self):

        # A legal opening bet is one big blind.
        return max(
            1,
            self.big_blind
        )

    def get_minimum_raise_size(self):

        if self.last_raise_size > 0:
            return self.last_raise_size

        return max(
            1,
            self.big_blind
        )

    def get_minimum_raise_to(self):

        return minimum_raise_to(
            self.current_bet,
            self.last_raise_size,
            self.get_minimum_open_bet()
        )

    def set_opening_wager(
            self,
            nominal_bet,
            minimum_raise
    ):
        """Set the bet to call once a hand's forced bets are posted.

        nominal_bet is the forced wager (big blind or bring-in);
        minimum_raise is the first full raise. With at most one seat able
        to act, only what was really posted can be called
        (core.opening_current_bet).
        """
        self.current_bet = opening_current_bet(
            nominal_bet,
            self.seat_round_bets(),
            self.seat_can_act()
        )
        self.settle_bet_to_match()

        self.last_raise_size = minimum_raise
        self.last_raiser = None

    def settle_bet_to_match(self):
        """Lower the bet to call when nobody can contest it (core.bet_to_match).

        With at most one seat in the hand holding chips, that seat only has
        to match the largest round bet of the other seats in the hand. Run
        at the deal, after every fold and before every turn, so a fold that
        leaves the human alone against all-in seats never asks it for a call
        that would only be returned.
        """
        self.current_bet = bet_to_match(
            self.seat_in_hand(),
            self.seat_stacks(),
            self.seat_round_bets(),
            self.current_bet
        )

    def get_player_maximum_raise_to(self):

        return (
                self.player_round_bet
                + self.player_stack
        )

    def get_player_amount_to_call(self):

        return max(
            0,
            self.current_bet
            - self.player_round_bet
        )

    def can_player_act_now(self):

        if (
                self.current_actor != 0
                or self.player_stack <= 0
                or self.player_busted
                or self.player_folded
                or self.player_all_in
                or self.hand_complete
        ):
            return False

        # The player may already have acted earlier
        # in the betting round but still owe money
        # because of a later raise.
        return (
                not self.player_has_acted
                or self.player_round_bet
                < self.current_bet
        )

    def can_player_check(self):

        return (
                self.can_player_act_now()
                and self.get_player_amount_to_call() == 0
        )

    def can_player_call(self):

        return (
                self.can_player_act_now()
                and self.get_player_amount_to_call() > 0
        )

    def can_player_raise(self):

        # The shared rule (core.can_raise): chips beyond the call,
        # somebody left to respond, and betting reopened
        # (seat_betting_reopened). If the player already acted and has
        # only been brought back by a short all-in raise, Call/Fold are
        # allowed, but raising is not reopened.
        return (
                self.can_player_act_now()
                and can_raise(
                    0,
                    self.seat_in_hand(),
                    self.seat_stacks(),
                    self.seat_round_bets(),
                    self.current_bet,
                    reopened=self.seat_betting_reopened(0)
                )
        )

    def player_fold(self):

        if (
                self.player_stack <= 0
                or self.player_folded
                or self.player_all_in
                or self.hand_complete
        ):
            return False

        self.record_player_tendency_action(
            "fold"
        )

        self.player_folded = True
        self.player_has_acted = True

        self.player_action_text = (
            "Folded"
        )

        self.log_hand_event(
            "fold",
            "You fold.",
            actor_index=0
        )

        self.resolve_after_fold()

        return True

    def player_check(self):

        if not self.can_player_check():
            return False

        self.record_player_tendency_action(
            "check"
        )

        self.player_has_acted = True
        self.player_action_text = "Checked"

        self.log_hand_event(
            "check",
            "You check.",
            actor_index=0
        )

        self.advance_to_next_actor()

        return True

    def player_call(self):

        if not self.can_player_call():
            return False

        amount_to_call = (
            self.get_player_amount_to_call()
        )

        pot_before = self.pot

        amount_paid = (
            self.commit_player_chips(
                amount_to_call
            )
        )

        if amount_paid <= 0:
            return False

        self.record_player_tendency_action(
            "call",
            amount=amount_paid,
            amount_to_call=amount_to_call,
            pot_before=pot_before
        )

        self.player_has_acted = True

        self.player_action_text = (
            f"Called ${amount_paid:,}"
        )

        suffix = (
            " and are all-in."
            if self.player_all_in
            else "."
        )

        self.log_hand_event(
            "call",
            f"You call ${amount_paid:,}{suffix}",
            actor_index=0,
            amount=amount_paid,
            all_in=self.player_all_in
        )

        self.advance_to_next_actor()

        return True

    def player_bet(
            self,
            amount
    ):

        self.last_wager_full = False

        if not self.can_player_act_now():
            return False

        if self.current_bet > 0:
            return False

        if self.player_stack <= 0:
            return False

        # B36: a bet needs somebody left to respond.
        if not self.can_player_raise():
            return False

        amount = int(
            amount
        )

        if amount <= 0:
            return False

        minimum_bet = (
            self.get_minimum_open_bet()
        )

        maximum_bet = (
            self.player_stack
        )

        if (
                amount < minimum_bet
                and amount < maximum_bet
        ):
            return False

        old_current_bet = self.current_bet
        pot_before = self.pot

        amount_paid = (
            self.commit_player_chips(
                min(
                    amount,
                    maximum_bet
                )
            )
        )

        if amount_paid <= 0:
            return False

        self.record_player_tendency_action(
            "bet",
            amount=amount_paid,
            amount_to_call=0,
            pot_before=pot_before
        )

        self.apply_wager(
            0,
            old_current_bet,
            self.player_round_bet,
            minimum_bet
        )

        self.player_has_acted = True

        self.player_action_text = (
            f"Bet ${amount_paid:,}"
        )

        suffix = (
            " and are all-in."
            if self.player_all_in
            else "."
        )

        self.log_hand_event(
            "bet",
            f"You bet ${amount_paid:,}{suffix}",
            actor_index=0,
            amount=amount_paid,
            all_in=self.player_all_in
        )

        self.advance_to_next_actor()

        return True

    def player_raise(
            self,
            raise_to
    ):

        self.last_wager_full = False

        # An all-in call uses the same chips as Call; it must remain available
        # even when the stack cannot reach the opponent's bet.
        if self.can_player_call() and self.get_player_amount_to_call() >= self.player_stack:
            return self.player_call()
        # B36: anything else lifts the bet to call, so it needs a legal raise
        # (somebody left to respond, betting still open to the player).
        if not self.can_player_raise():
            return False

        if self.current_bet <= 0:
            return False

        raise_to = int(
            raise_to
        )

        maximum_raise_to = (
            self.get_player_maximum_raise_to()
        )

        minimum_raise_to = (
            self.get_minimum_raise_to()
        )

        if raise_to <= self.current_bet:
            return False

        if (
                raise_to < minimum_raise_to
                and raise_to < maximum_raise_to
        ):
            return False

        target = min(
            raise_to,
            maximum_raise_to
        )

        old_current_bet = self.current_bet
        amount_to_call = self.get_player_amount_to_call()
        pot_before = self.pot

        amount_needed = (
            target
            - self.player_round_bet
        )

        if amount_needed <= 0:
            return False

        amount_paid = (
            self.commit_player_chips(
                amount_needed
            )
        )

        if amount_paid <= 0:
            return False

        self.record_player_tendency_action(
            "raise",
            amount=amount_paid,
            amount_to_call=amount_to_call,
            pot_before=pot_before
        )

        self.apply_wager(
            0,
            old_current_bet,
            self.player_round_bet,
            self.get_minimum_raise_size()
        )

        self.player_has_acted = True

        self.player_action_text = (
            f"Raised to "
            f"${self.player_round_bet:,}"
        )

        suffix = (
            " and are all-in."
            if self.player_all_in
            else "."
        )

        self.log_hand_event(
            "raise",
            (
                f"You raise to "
                f"${self.player_round_bet:,}"
                f"{suffix}"
            ),
            actor_index=0,
            amount=amount_paid,
            raise_to=self.player_round_bet,
            all_in=self.player_all_in
        )

        self.advance_to_next_actor()

        return True

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

    # ==================================================
    # HAND EVALUATION (shared scorer in core.py)
    # ==================================================

    def evaluate_five_cards(
            self,
            cards
    ):

        return evaluate_five_poker_cards(cards)

    def evaluate_best_hand(
            self,
            cards
    ):

        return evaluate_best_poker_hand(cards)

    # ==================================================
    # SHOWDOWN
    # ==================================================

    def showdown_ready(self):
        """True once every card needed to settle the hand is out.

        Hold'em needs the full board. Five-Card Draw and Seven-Card Stud
        override this: their showdown comes after the last betting round.
        """
        return len(self.community_cards) == 5

    def showdown(self):

        if not self.showdown_ready():
            return False

        return self.resolve_showdown()

    def resolve_showdown(self):
        """Settle the hand with the shared pot rules in core.py.

        Shared by Hold'em, Five-Card Draw and Seven-Card Stud. Every live
        hand is shown; core.build_pots builds the main pot and side pots
        and returns uncalled chips; core.award_pots pays each pot to its
        best eligible hand, splitting ties with odd chips from the
        dealer's left. A seat that only got chips back is not a winner.
        """

        # A completed hand has already been resolved: never pay its
        # pots a second time.
        if self.hand_complete:
            return False

        active_indexes = (
            self.get_active_player_indexes()
        )

        if not active_indexes:
            return False

        # ==================================================
        # One player remains
        # ==================================================

        if len(active_indexes) == 1:
            return (
                self.award_pot_to_single_player(
                    active_indexes[0]
                )
            )

        # ==================================================
        # Evaluate every active hand ONCE
        # ==================================================

        results = {}

        for player_index in active_indexes:

            result = (
                self.get_showdown_result(
                    player_index
                )
            )

            if result is not None:
                results[
                    player_index
                ] = result

        if not results:
            return False

        self.log_hand_event(
            "showdown",
            "Showdown."
        )

        for player_index, result in results.items():

            if player_index == 0:
                cards = self.player_hand
                prefix = "You show"
            else:
                npc_index = player_index - 1
                cards = self.npc_hands[npc_index]
                prefix = (
                    f"{self.get_table_player_name(player_index)} "
                    f"shows"
                )

            category = HAND_NAMES[
                result[0][0]
            ]

            hand_detail = describe_poker_score(
                result[0],
                compact=True
            )

            self.log_hand_event(
                "showdown_hand",
                (
                    f"{prefix} "
                    f"{format_poker_cards(cards)} "
                    f"({hand_detail})."
                ),
                actor_index=player_index,
                cards=[
                    dict(card)
                    for card in cards
                    if card
                ],
                hand_name=category,
                hand_detail=hand_detail
            )

        # ==================================================
        # Build main pot + side pots
        # ==================================================

        # Only a seat with a shown hand can win; everyone else's chips
        # are dead money in the pots they were paid towards.
        seat_count = self.seat_count()

        pots, refunds = build_pots(
            self.get_hand_contributions(),
            [
                seat in results
                for seat in range(seat_count)
            ]
        )

        # ==================================================
        # Resolve each pot separately
        # ==================================================

        awards, payout_totals = award_pots(
            pots,
            {
                seat: result[0]
                for seat, result in results.items()
            },
            self.dealer_index,
            seat_count,
            describe=lambda score: describe_poker_score(
                score,
                compact=True
            )
        )

        for player_index, amount in payout_totals.items():
            self.award_chips_to_player(
                player_index,
                amount
            )

        # Uncalled chips go back to whoever bet them: not a win.
        for player_index, amount in refunds.items():
            self.award_chips_to_player(
                player_index,
                amount
            )

        self.last_pot_awards = awards
        self.last_refunds = dict(refunds)
        self.last_resolved_pot = sum(
            int(award["amount"])
            for award in awards
        )
        self.recap_open = False
        self.recap_page = 0

        # ==================================================
        # Record everybody who won or tied a pot
        #
        # core.hand_winners: a pot whose only eligible seat is the
        # seat that takes it (its own excess plus folded seats' dead
        # money) is won only when that seat made money on the hand;
        # otherwise it is just collected. winner_indexes drives the
        # win sound, highlight, achievements and chat.
        # ==================================================

        self.winner_indexes = hand_winners(
            awards,
            hand_nets(
                self.get_hand_contributions(),
                awards,
                refunds
            )
        )

        # ==================================================
        # Result text: every seat that collected a pot
        # ==================================================

        payout_winners = sorted(
            player_index
            for player_index, winnings
            in payout_totals.items()
            if winnings > 0
        )

        # ------------------------------------------
        # One player collected everything
        # ------------------------------------------

        if len(payout_winners) == 1:

            winner_index = (
                payout_winners[0]
            )

            winnings = (
                payout_totals[
                    winner_index
                ]
            )

            winner_result = (
                results[
                    winner_index
                ]
            )

            category = (
                HAND_NAMES[
                    winner_result[0][0]
                ]
            )

            hand_detail = describe_poker_score(
                winner_result[0],
                compact=True
            )

            if winner_index == 0:

                self.result_text = (
                    f"You win ${winnings:,} "
                    f"with {hand_detail}!"
                )

            else:

                winner_name = (
                    self.get_table_player_name(
                        winner_index
                    )
                )

                self.result_text = (
                    f"{winner_name} wins "
                    f"${winnings:,} with "
                    f"{hand_detail}."
                )

        # ------------------------------------------
        # Different players won different pots
        # ------------------------------------------

        else:

            payout_parts = []

            for player_index in payout_winners:
                name = (
                    self.get_table_player_name(
                        player_index
                    )
                )

                winnings = (
                    payout_totals[
                        player_index
                    ]
                )

                part = f"{name} ${winnings:,}"

                # A seat that only collected pots nobody else could win
                # beat nobody, so no hand is named for it.
                if self.payout_text_names_hands and any(
                        player_index in award["payouts"]
                        and not collected_uncontested(award, awards)
                        for award in awards
                ):
                    part += (
                        f" with "
                        f"{describe_poker_score(results[player_index][0], compact=True)}"
                    )

                payout_parts.append(part)

            self.result_text = (
                    "Payouts: "
                    + "; ".join(
                payout_parts
            )
                    + "."
            )

        # ==================================================
        # Uncalled chips and detailed side-pot history
        # ==================================================

        self.log_refund_events(refunds)

        # Keep the result in the normal payout banner. Detailed review is opt-in.
        self.recap_open = False
        self.log_detailed_pot_awards(
            results.keys()
        )

        self.log_hand_event(
            "result",
            self.result_text,
            winners=self.winner_indexes.copy(),
            payouts={
                player_index: payout_totals[player_index]
                for player_index in payout_winners
            }
        )

        # ==================================================
        # Finish hand
        # ==================================================

        self.record_personality_showdown(results)

        self.pot = 0

        self.hand_complete = True

        self.current_actor = -1

        self.current_stage = "showdown"

        # Only NOW is a $0 stack actually busted.
        #
        # Somebody who was temporarily at $0 because
        # they were all-in may have just won chips.
        newly_busted = self.refresh_busted_state()

        self.log_newly_busted_players(
            newly_busted
        )

        self.finalize_showdown_display_state()

        return True

    # ==================================================
    # DISPLAY HELPERS
    # ==================================================

    def get_player_hand_name(self):

        cards = (
            self.player_hand
            + self.community_cards
        )

        if len(cards) < 5:
            return ""

        result = (
            self.evaluate_best_hand(
                cards
            )
        )

        if result is None:
            return ""

        return HAND_NAMES[
            result[0][0]
        ]

    def get_npc_hand_name(
            self,
            npc_index
    ):

        if not (
                0
                <= npc_index
                < len(
                    self.npc_hands
                )
        ):

            return ""

        cards = (
            self.npc_hands[
                npc_index
            ]
            + self.community_cards
        )

        if len(cards) < 5:
            return ""

        result = (
            self.evaluate_best_hand(
                cards
            )
        )

        if result is None:
            return ""

        return HAND_NAMES[
            result[0][0]
        ]

