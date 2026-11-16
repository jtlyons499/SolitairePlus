"""Hold'em showdown: hand evaluation (the shared scorer in core.py), the showdown and the hand
names shown on the table (a mixin of holdem.TexasHoldemGame; Draw and Stud inherit it).
"""
from solitaireplus.games.poker.core import (
    HAND_NAMES,
    award_pots,
    build_pots,
    collected_uncontested,
    describe_poker_score,
    evaluate_best_hand as evaluate_best_poker_hand,
    evaluate_five_cards as evaluate_five_poker_cards,
    format_poker_cards,
    hand_nets,
    hand_winners,
)


class ShowdownMixin:
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

        if self.record_pot_contributors:
            # Every seat that paid into each pot, folded seats included
            # (award_pots keeps build_pots' order, one record per pot).
            for award, pot in zip(awards, pots):
                award["contributors"] = list(pot["contributors"])

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
