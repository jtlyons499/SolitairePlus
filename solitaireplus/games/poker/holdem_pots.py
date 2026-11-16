"""Hold'em pots: side pots, the pot shown on the table, pot awards and refunds, and winning
by a fold (a mixin of holdem.TexasHoldemGame; Draw and Stud inherit it).
"""
from solitaireplus.games.poker.core import (
    build_pots,
    collected_uncontested,
    format_poker_display_name,
    join_poker_names,
    settle_fold_win,
)


class PotsMixin:
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
