"""Hold'em seats: chips committed to the pot, seat order, the dealer and blinds, whose turn
it is, the active players and the read-only seat views for core.py
(a mixin of holdem.TexasHoldemGame; Draw and Stud inherit it).
"""
from solitaireplus.games.poker.core import betting_closed, session_over


class SeatsMixin:
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
