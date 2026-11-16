"""Game auto-solve: when it is allowed, starting it and stepping it each frame, plus the debug
auto-solve state (a mixin of rules.Game).
"""
import pygame

from solitaireplus.games.solitaire.deck import create_deck


class AutoSolveMixin:
    # --------------------------------------------------
    # Debug auto-solve state
    # --------------------------------------------------

    def debug_auto_solve_state(self):

        deck = create_deck()

        rank_order = {
            "A": 1,
            "2": 2,
            "3": 3,
            "4": 4,
            "5": 5,
            "6": 6,
            "7": 7,
            "8": 8,
            "9": 9,
            "10": 10,
            "J": 11,
            "Q": 12,
            "K": 13,
        }

        # --------------------------------------------------
        # Group cards by suit
        # --------------------------------------------------

        suits = {}

        for card in deck:
            suits.setdefault(
                card.suit,
                []
            ).append(card)

        for suit_cards in suits.values():
            suit_cards.sort(
                key=lambda card:
                rank_order[card.rank]
            )

        # --------------------------------------------------
        # Foundations contain A through Q
        # --------------------------------------------------

        self.foundations = []

        kings = []

        for suit_cards in suits.values():

            foundation_cards = []

            for card in suit_cards:

                card.face_up = True

                if card.rank == "K":
                    kings.append(card)

                else:
                    foundation_cards.append(
                        card
                    )

            self.foundations.append(
                foundation_cards
            )

        # --------------------------------------------------
        # Four exposed Kings in tableau
        # --------------------------------------------------

        self.tableau = [
            [],
            [],
            [],
            [],
            [],
            [],
            []
        ]

        for index, king in enumerate(kings):
            self.tableau[index].append(
                king
            )

        # --------------------------------------------------
        # Nothing left in stock or waste
        # --------------------------------------------------

        self.stock = []
        self.waste = []

        # --------------------------------------------------
        # Reset temporary state
        # --------------------------------------------------

        self.clear_selection()
        self.clear_drag()

        self.undo_stack = []

        self.flip_animation = None
        self.victory_animation = None

        self.hint_data = None

        self.round_won = False

        self.move_count = 0

        self.round_start_ticks = (
            pygame.time.get_ticks()
        )

    # --------------------------------------------------
    # Utility / Check Methods
    # --------------------------------------------------

    def can_auto_solve(self):

        if self.challenge_id == "all_or_nothing":
            return False

        if self.victory_animation is not None:
            return False

        if self.round_won:
            return False

        # Every tableau card must be face-up.
        for column in self.tableau:
            for card in column:
                if not card.face_up:
                    return False

        return True

    def auto_solve(self):

        if not self.can_auto_solve():
            return False

        self.clear_selection()
        self.clear_drag()

        self.auto_solving = True

        self.auto_solve_last_ticks = (
            pygame.time.get_ticks()
        )

        self.auto_solve_steps = 0
        self.auto_solve_recycle_signature = None

        return True

    def update_auto_solve(self):

        if not self.auto_solving:
            return

        if self.round_won:
            self.auto_solving = False
            return

        current_ticks = (
            pygame.time.get_ticks()
        )

        if (
                current_ticks
                - self.auto_solve_last_ticks
                < self.auto_solve_delay_ms
        ):
            return

        self.auto_solve_last_ticks = (
            current_ticks
        )

        self.auto_solve_steps += 1

        if (
                self.auto_solve_steps
                >= self.auto_solve_max_steps
        ):
            self.auto_solving = False
            return

        # ==================================================
        # TABLEAU -> FOUNDATION
        # ==================================================

        for source_index, column in enumerate(
                self.tableau
        ):

            if not column:
                continue

            card = column[-1]

            for foundation_index in range(4):

                if self.move_tableau_to_foundation(
                        source_index,
                        card,
                        foundation_index
                ):
                    return

        # ==================================================
        # WASTE -> FOUNDATION
        # ==================================================

        if self.waste:

            for foundation_index in range(4):

                if self.move_waste_to_foundation(
                        foundation_index
                ):
                    return

        # ==================================================
        # USEFUL TABLEAU -> TABLEAU
        #
        # Auto-solve used to stop as soon as every face-up top card was
        # temporarily blocked from the foundations.  Before giving up, move a
        # legal face-up stack when doing so exposes a card that can immediately
        # advance a foundation.  This keeps the convenience feature conservative
        # while handling the common "last few cards" stall.
        # ==================================================

        for source_index, source_column in enumerate(self.tableau):
            if len(source_column) < 2:
                continue

            for card_index in range(1, len(source_column)):
                selected_card = source_column[card_index]
                if not selected_card.face_up:
                    continue

                exposed_after_move = source_column[card_index - 1]
                if not exposed_after_move.face_up:
                    continue

                exposes_foundation_move = any(
                    self.can_place_on_foundation(
                        exposed_after_move,
                        foundation,
                    )
                    for foundation in self.foundations
                )
                if not exposes_foundation_move:
                    continue

                for target_index, target_column in enumerate(self.tableau):
                    if target_index == source_index:
                        continue

                    if target_column:
                        legal = self.can_place_on_tableau(
                            selected_card,
                            target_column[-1],
                        )
                    else:
                        legal = selected_card.rank == "K"

                    if legal and self.move_tableau_stack(
                        source_index,
                        selected_card,
                        target_index,
                    ):
                        return

        # ==================================================
        # WASTE -> TABLEAU
        #
        # Moving a blocked waste card onto the tableau can uncover the next
        # stock card and is required for some otherwise auto-solvable endings.
        # ==================================================

        if self.waste:
            moving_card = self.waste[-1]
            for target_index, target_column in enumerate(self.tableau):
                if target_column:
                    legal = self.can_place_on_tableau(
                        moving_card,
                        target_column[-1],
                    )
                else:
                    legal = moving_card.rank == "K"

                if legal and self.move_waste_to_tableau(target_index):
                    return

        # ==================================================
        # WAIT FOR THE FLIP (B1)
        #
        # click_stock() ignores clicks while a card flip animates, and the
        # flip lasts longer than one auto-solve step. Wait and try again on
        # a later step instead of mistaking the ignored recycle for
        # "nothing else to do".
        # ==================================================

        if (
                (self.stock or self.waste)
                and self.is_flip_animating()
        ):
            return

        # ==================================================
        # STOCK
        # ==================================================

        if self.stock:
            self.click_stock()
            return

        # ==================================================
        # RECYCLE WASTE -> STOCK
        # ==================================================

        if self.waste:

            # A whole pass through the stock that played no card (nothing left
            # the stock/waste, no foundation grew) will repeat forever with
            # unlimited passes (draw 3): stop instead of cycling until the
            # step cap. Waiting for the flip (B1) made such passes possible.
            signature = (
                len(self.stock) + len(self.waste),
                sum(len(foundation) for foundation in self.foundations)
            )
            if signature == self.auto_solve_recycle_signature:
                self.auto_solving = False
                return
            self.auto_solve_recycle_signature = signature

            old_stock_count = len(
                self.stock
            )

            self.click_stock()

            if len(self.stock) > old_stock_count:
                return

        # ==================================================
        # NOTHING ELSE TO DO
        # ==================================================

        self.auto_solving = False
