"""Game move rules and moves: placement checks, the stock, tableau / waste / foundation moves,
the all-or-nothing foundation rule, auto-moves and undo (a mixin of rules.Game).
"""
import copy
import random

from solitaireplus.games.solitaire.assist import get_complete_suit_run, is_same_suit_descending_step


class MovesMixin:
    # --------------------------------------------------
    # Solitaire rules
    # --------------------------------------------------

    def can_place_on_tableau(self, moving_card, target_card):
        different_color = (
            moving_card.is_red
            != target_card.is_red
        )

        correct_rank = (
            moving_card.value
            == target_card.value - 1
        )

        standard_move = different_color and correct_rank

        if self.challenge_id == "all_or_nothing":
            return (
                standard_move
                or is_same_suit_descending_step(
                    moving_card,
                    target_card
                )
            )

        return standard_move

    def can_place_on_foundation(self, moving_card, foundation):
        if self.challenge_id == "all_or_nothing":
            return False

        if not foundation:
            return moving_card.rank == "A"

        top_card = foundation[-1]

        same_suit = (
            moving_card.suit
            == top_card.suit
        )

        next_rank = (
            moving_card.value
            == top_card.value + 1
        )

        return same_suit and next_rank

    def get_all_or_nothing_stack(
            self,
            source_column_index,
            selected_card=None
    ):
        if self.challenge_id != "all_or_nothing":
            return None

        if not (
                0 <= source_column_index < len(self.tableau)
        ):
            return None

        return get_complete_suit_run(
            self.tableau[source_column_index],
            selected_card=selected_card
        )

    def move_all_or_nothing_stack_to_foundation(
            self,
            source_column_index,
            selected_card,
            foundation_index
    ):
        if self.challenge_id != "all_or_nothing":
            return False

        if not (0 <= foundation_index < len(self.foundations)):
            return False

        foundation = self.foundations[foundation_index]
        if foundation:
            return False

        run = self.get_all_or_nothing_stack(
            source_column_index,
            selected_card=selected_card
        )

        if run is None:
            return False

        source_column = self.tableau[source_column_index]

        self.save_undo_state()

        del source_column[-13:]

        # Tableau run is K..A from top to playable end. Foundations store
        # A..K so the completed suit behaves like a normal finished pile.
        foundation.extend(reversed(run))

        self.record_move()
        self.audio.play_sound("card_move")

        if (
                source_column
                and not source_column[-1].face_up
        ):
            self.start_flip_animation(
                source_column[-1]
            )
            self.audio.play_sound("card_flip")

        self.clear_selection()
        self.check_for_win()
        return True

    # --------------------------------------------------
    # Stock
    # --------------------------------------------------

    def click_stock(self):

        if self.flip_animation is not None:
            return

        self.clear_selection()

        if self.stock:
            self.save_undo_state()

            cards_to_draw = min(
                self.stock_draw_count,
                len(self.stock)
            )

            last_card = None

            for _ in range(
                    cards_to_draw
            ):
                card = self.stock.pop()

                card.face_up = True

                self.waste.append(
                    card
                )

                last_card = card

            # Animate only the final/top card.
            if last_card is not None:
                self.start_flip_animation(
                    last_card
                )

            self.record_move()

            self.audio.play_sound(
                "card_draw"
            )

        elif self.waste:

            # ----------------------------
            # Check stock-pass limit
            # ----------------------------

            if (
                    self.stock_pass_limit
                    is not None
                    and self.stock_passes_used
                    >= self.stock_pass_limit
            ):
                return

            self.save_undo_state()

            while self.waste:
                card = self.waste.pop()

                card.face_up = False

                self.stock.append(
                    card
                )

            self.stock_passes_used += 1

            self.record_move()

    def shuffle_stock(self):

        if not self.shuffle_enabled:
            return False

        cards = (
                self.stock[:]
                + self.waste[:]
        )

        if not cards:
            return False

        self.save_undo_state()

        for card in cards:
            card.face_up = False

        random.shuffle(cards)

        self.stock = cards
        self.waste = []
        self.deal_status = "modified"

        self.clear_selection()
        self.flip_animation = None

        self.record_move()

        self.audio.play_sound(
            "card_shuffle"
        )

        return True

    # --------------------------------------------------
    # Tableau movement
    # --------------------------------------------------

    def move_tableau_stack(
        self,
        source_column_index,
        selected_card,
        target_column_index
    ):
        source_column = self.tableau[
            source_column_index
        ]

        target_column = self.tableau[
            target_column_index
        ]

        if selected_card not in source_column:
            self.clear_selection()
            return False

        selected_index = source_column.index(
            selected_card
        )

        moving_stack = source_column[
            selected_index:
        ]

        if not target_column:
            if selected_card.rank != "K":
                return False

        else:
            target_card = target_column[-1]

            if not self.can_place_on_tableau(
                selected_card,
                target_card
            ):
                return False

        self.save_undo_state()

        del source_column[selected_index:]

        target_column.extend(moving_stack)

        self.record_move()

        self.audio.play_sound(
            "card_move"
        )

        if (
                source_column
                and not source_column[-1].face_up
        ):
            self.start_flip_animation(
                source_column[-1]
            )

            self.audio.play_sound(
                "card_flip"
            )

        return True

    # --------------------------------------------------
    # Waste -> tableau
    # --------------------------------------------------

    def move_waste_to_tableau(
        self,
        target_column_index
    ):
        if not self.waste:
            return False

        moving_card = self.waste[-1]

        target_column = self.tableau[
            target_column_index
        ]

        if not target_column:
            if moving_card.rank != "K":
                return False

        else:
            target_card = target_column[-1]

            if not self.can_place_on_tableau(
                moving_card,
                target_card
            ):
                return False

        self.save_undo_state()

        self.waste.pop()

        target_column.append(
            moving_card
        )

        self.record_move()

        self.audio.play_sound(
            "card_move"
        )

        return True

    # --------------------------------------------------
    # Waste -> foundation
    # --------------------------------------------------

    def move_waste_to_foundation(
        self,
        foundation_index
    ):
        if not self.waste:
            return False

        moving_card = self.waste[-1]

        foundation = self.foundations[
            foundation_index
        ]

        if not self.can_place_on_foundation(
            moving_card,
            foundation
        ):
            return False

        self.save_undo_state()

        self.waste.pop()
        foundation.append(moving_card)
        self.record_move()

        self.audio.play_sound("card_move")

        self.check_for_win()

        return True

    # --------------------------------------------------
    # Tableau -> foundation
    # --------------------------------------------------

    def move_tableau_to_foundation(
        self,
        source_column_index,
        selected_card,
        foundation_index
    ):
        if self.challenge_id == "all_or_nothing":
            return self.move_all_or_nothing_stack_to_foundation(
                source_column_index,
                selected_card,
                foundation_index
            )

        source_column = self.tableau[
            source_column_index
        ]

        if not source_column:
            return False

        if source_column[-1] is not selected_card:
            return False

        foundation = self.foundations[
            foundation_index
        ]

        if not self.can_place_on_foundation(
            selected_card,
            foundation
        ):
            return False

        self.save_undo_state()

        source_column.pop()
        foundation.append(selected_card)
        self.record_move()

        self.audio.play_sound(
            "card_move"
        )

        if (
                source_column
                and not source_column[-1].face_up
        ):
            self.start_flip_animation(
                source_column[-1]
            )

            self.audio.play_sound(
                "card_flip"
            )

        self.check_for_win()

        return True

    # --------------------------------------------------
    # Foundation -> tableau
    # --------------------------------------------------

    def move_foundation_to_tableau(
        self,
        foundation_index,
        target_column_index
    ):
        if self.challenge_id == "all_or_nothing":
            return False

        foundation = self.foundations[
            foundation_index
        ]

        if not foundation:
            return False

        moving_card = foundation[-1]

        target_column = self.tableau[
            target_column_index
        ]

        if not target_column:
            if moving_card.rank != "K":
                return False

        else:
            target_card = target_column[-1]

            if not self.can_place_on_tableau(
                moving_card,
                target_card
            ):
                return False

        self.save_undo_state()

        foundation.pop()
        target_column.append(moving_card)

        self.record_move()

        self.audio.play_sound(
            "card_move"
        )

        return True

    # --------------------------------------------------
    # Auto-move helpers
    # --------------------------------------------------

    def try_auto_move_to_foundation(
            self,
            card,
            source
    ):
        if self.challenge_id == "all_or_nothing":
            if (
                    source is None
                    or source[0] != "tableau"
            ):
                return False

            for foundation_index, foundation in enumerate(
                    self.foundations
            ):
                if foundation:
                    continue

                if self.move_all_or_nothing_stack_to_foundation(
                        source[1],
                        card,
                        foundation_index
                ):
                    return True

            return False

        for foundation_index, foundation in enumerate(
                self.foundations
        ):
            if not self.can_place_on_foundation(
                    card,
                    foundation
            ):
                continue

            # Waste -> foundation
            if source == ("waste", None):
                if not self.waste:
                    return False

                if self.waste[-1] is not card:
                    return False

                self.save_undo_state()

                self.waste.pop()

                foundation.append(
                    card
                )

                self.record_move()

                self.audio.play_sound(
                    "card_move"
                )

                self.check_for_win()

                self.clear_selection()

                return True

            # Tableau -> foundation
            if (
                    source is not None
                    and source[0] == "tableau"
            ):
                source_column = self.tableau[
                    source[1]
                ]

                if not source_column:
                    return False

                if source_column[-1] is not card:
                    return False

                self.save_undo_state()

                source_column.pop()

                foundation.append(
                    card
                )

                self.record_move()

                self.audio.play_sound(
                    "card_move"
                )

                self.check_for_win()

                # Flip newly exposed card
                if (
                        source_column
                        and not source_column[-1].face_up
                ):
                    self.start_flip_animation(
                        source_column[-1]
                    )

                    self.audio.play_sound(
                        "card_flip"
                    )

                self.clear_selection()

                return True

        return False

    # --------------------------------------------------
    # Undo
    # --------------------------------------------------

    def save_undo_state(self):
        state = {
            "tableau": self.tableau,
            "stock": self.stock,
            "waste": self.waste,
            "foundations": self.foundations,
            "move_count": self.move_count,
            "stock_passes_used":
                self.stock_passes_used,
            "hints_remaining":
                self.hints_remaining,
            "deal_status":
                self.deal_status,
        }

        self.undo_stack.append(
            copy.deepcopy(state)
        )

        if (
                self.undo_history_limit
                is not None
        ):
            while (
                    len(self.undo_stack)
                    > self.undo_history_limit
            ):
                self.undo_stack.pop(0)

    def undo(self):

        if self.challenge_id == "no_undo":
            return False

        if not self.undo_stack:
            return False

        state = self.undo_stack.pop()

        self.tableau = state["tableau"]
        self.stock = state["stock"]
        self.waste = state["waste"]
        self.foundations = state["foundations"]
        self.move_count = state["move_count"]

        self.stock_passes_used = (
            state[
                "stock_passes_used"
            ]
        )

        self.hints_remaining = (
            state[
                "hints_remaining"
            ]
        )

        self.deal_status = state.get(
            "deal_status",
            self.deal_status
        )

        self.selected_card = None
        self.selected_source = None

        self.flip_animation = None

        return True

    # --------------------------------------------------
    # Auto-move to tableau
    # --------------------------------------------------

    def try_auto_move_to_tableau(
            self,
            card,
            source
    ):
        for target_column_index, target_column in enumerate(
                self.tableau
        ):
            # Avoid moving a tableau card
            # onto its own column
            if (
                    source is not None
                    and source[0] == "tableau"
                    and source[1] == target_column_index
            ):
                continue

            # Check target validity
            if not target_column:
                if card.rank != "K":
                    continue

            else:
                target_card = target_column[-1]

                if not self.can_place_on_tableau(
                        card,
                        target_card
                ):
                    continue

            # ----------------------------
            # Waste -> tableau
            # ----------------------------

            if source == ("waste", None):
                if not self.waste:
                    return False

                if self.waste[-1] is not card:
                    return False

                self.save_undo_state()

                self.waste.pop()
                target_column.append(card)

                self.record_move()

                self.audio.play_sound("card_move")

                self.clear_selection()

                return True

            # ----------------------------
            # Foundation -> tableau
            # ----------------------------

            if (
                    source is not None
                    and source[0] == "foundation"
            ):
                foundation = self.foundations[
                    source[1]
                ]

                if not foundation:
                    return False

                if foundation[-1] is not card:
                    return False

                self.save_undo_state()

                foundation.pop()
                target_column.append(card)

                self.record_move()

                self.audio.play_sound("card_move")

                self.clear_selection()

                return True

            # ----------------------------
            # Tableau -> tableau
            # ----------------------------

            if (
                    source is not None
                    and source[0] == "tableau"
            ):
                source_column = self.tableau[
                    source[1]
                ]

                if card not in source_column:
                    return False

                card_index = source_column.index(card)

                moving_stack = source_column[
                    card_index:
                ]

                self.save_undo_state()

                del source_column[
                    card_index:
                ]

                target_column.extend(
                    moving_stack
                )

                self.record_move()

                self.audio.play_sound("card_move")

                # Flip newly exposed card
                if (
                        source_column
                        and not source_column[-1].face_up
                ):
                    self.start_flip_animation(
                        source_column[-1]
                    )

                    self.audio.play_sound(
                        "card_flip"
                    )

                return True

        return False
