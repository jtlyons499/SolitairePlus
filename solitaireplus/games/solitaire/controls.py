"""Game mouse input: click, double-click, press / drag / release, selection and drag state,
and the pygame event entry point (a mixin of rules.Game).
"""
import pygame

from solitaireplus.games.solitaire.constants import FACE_UP_SPACING


class ControlsMixin:
    # --------------------------------------------------
    # Mouse click entry point
    # --------------------------------------------------

    def handle_mouse_click(
            self,
            mouse_pos,
            clicks=1
    ):
        if self.victory_animation is not None:
            return


        if clicks >= 2:
            self.handle_double_click(
                mouse_pos
            )

        else:
            self.handle_click(
                mouse_pos
            )

    # --------------------------------------------------
    # Selection
    # --------------------------------------------------

    def clear_selection(self):
        self.selected_card = None
        self.selected_source = None

    # --------------------------------------------------
    # Drag helpers
    # --------------------------------------------------

    def clear_drag(self):
        self.dragging = False

        self.drag_cards = []
        self.drag_source = None
        self.drag_source_index = None

        self.drag_candidate = False
        self.drag_start_pos = None
        self.drag_start_rect = None

        self.drag_spacing = FACE_UP_SPACING

    def handle_mouse_down(
            self,
            mouse_pos,
            clicks=1
    ):
        if self.victory_animation is not None:
            return

        self.pending_clicks = clicks

        # ----------------------------
        # Double click
        # ----------------------------

        if clicks >= 2:
            self.clear_drag()

            self.handle_double_click(
                mouse_pos
            )

            return

        self.clear_drag()

        self.drag_start_pos = mouse_pos

        # ==================================================
        # Waste
        # ==================================================

        if (
                self.waste
                and self.waste_rect.collidepoint(
            mouse_pos
        )
        ):
            card = self.waste[-1]

            self.drag_candidate = True

            self.drag_cards = [
                card
            ]

            self.drag_source = (
                "waste",
                None
            )

            self.drag_start_rect = (
                self.waste_rect.copy()
            )

            self.drag_offset_x = (
                    mouse_pos[0]
                    - self.drag_start_rect.x
            )

            self.drag_offset_y = (
                    mouse_pos[1]
                    - self.drag_start_rect.y
            )

            return

        # ==================================================
        # Foundation
        # ==================================================

        foundation_index = (
            self.get_foundation_at_position(
                mouse_pos
            )
        )

        if (
                foundation_index is not None
                and self.foundations[
            foundation_index
        ]
        ):
            card = self.foundations[
                foundation_index
            ][-1]

            self.drag_candidate = True

            self.drag_cards = [
                card
            ]

            self.drag_source = (
                "foundation",
                foundation_index
            )

            self.drag_start_rect = (
                self.foundation_rects[
                    foundation_index
                ].copy()
            )

            self.drag_offset_x = (
                    mouse_pos[0]
                    - self.drag_start_rect.x
            )

            self.drag_offset_y = (
                    mouse_pos[1]
                    - self.drag_start_rect.y
            )

            return

        # ==================================================
        # Tableau
        # ==================================================

        card, column_index = (
            self.get_tableau_card_at_position(
                mouse_pos
            )
        )

        if card is None:
            return

        source_column = self.tableau[
            column_index
        ]

        card_index = source_column.index(
            card
        )

        # Everything from the selected card downward
        # travels together.
        self.drag_cards = source_column[
            card_index:
        ]

        self.drag_candidate = True

        self.drag_source = (
            "tableau",
            column_index
        )

        self.drag_source_index = (
            card_index
        )

        self.drag_start_rect = (
            self.get_tableau_card_rect(
                column_index,
                card
            )
        )

        (
            _,
            face_up_spacing
        ) = self.get_tableau_spacings(
            source_column
        )

        self.drag_spacing = (
            face_up_spacing
        )

        self.drag_offset_x = (
                mouse_pos[0]
                - self.drag_start_rect.x
        )

        self.drag_offset_y = (
                mouse_pos[1]
                - self.drag_start_rect.y
        )

    def handle_mouse_motion(
            self,
            mouse_pos
    ):
        if not self.drag_candidate:
            return

        if self.drag_start_pos is None:
            return

        delta_x = (
                mouse_pos[0]
                - self.drag_start_pos[0]
        )

        delta_y = (
                mouse_pos[1]
                - self.drag_start_pos[1]
        )

        distance_squared = (
                delta_x * delta_x
                + delta_y * delta_y
        )

        # Don't turn tiny mouse movements
        # into accidental drags.
        if (
                not self.dragging
                and distance_squared
                >= self.drag_threshold ** 2
        ):
            self.dragging = True

            self.clear_selection()

        if self.dragging:
            self.drag_mouse_x = (
                mouse_pos[0]
            )

            self.drag_mouse_y = (
                mouse_pos[1]
            )

    def handle_mouse_up(
            self,
            mouse_pos
    ):
        # ==================================================
        # Normal click
        # ==================================================

        if not self.dragging:

            clicks = self.pending_clicks

            self.clear_drag()

            # Double clicks were already handled
            # during mouse-down.
            if clicks < 2:
                self.handle_mouse_click(
                    mouse_pos,
                    clicks
                )

            return

        # ==================================================
        # Drag drop
        # ==================================================

        source = self.drag_source

        if (
                source is None
                or not self.drag_cards
        ):
            self.clear_drag()
            return

        moving_card = self.drag_cards[0]

        moved = False

        # ----------------------------
        # Find destination
        # ----------------------------

        foundation_index = (
            self.get_foundation_at_position(
                mouse_pos
            )
        )

        target_column = (
            self.get_tableau_column_at_position(
                mouse_pos
            )
        )

        # ==================================================
        # Waste source
        # ==================================================

        if source[0] == "waste":

            if foundation_index is not None:
                moved = (
                    self.move_waste_to_foundation(
                        foundation_index
                    )
                )

            elif target_column is not None:
                moved = (
                    self.move_waste_to_tableau(
                        target_column
                    )
                )

        # ==================================================
        # Foundation source
        # ==================================================

        elif source[0] == "foundation":

            source_foundation = (
                source[1]
            )

            if target_column is not None:
                moved = (
                    self.move_foundation_to_tableau(
                        source_foundation,
                        target_column
                    )
                )

        # ==================================================
        # Tableau source
        # ==================================================

        elif source[0] == "tableau":

            source_column = (
                source[1]
            )

            # ----------------------------
            # Tableau -> foundation
            # ----------------------------

            if foundation_index is not None:

                # Existing method only succeeds if
                # this is the bottom/top playable card.
                moved = (
                    self.move_tableau_to_foundation(
                        source_column,
                        moving_card,
                        foundation_index
                    )
                )

            # ----------------------------
            # Tableau -> tableau
            # ----------------------------

            elif (
                    target_column is not None
                    and target_column
                    != source_column
            ):
                moved = (
                    self.move_tableau_stack(
                        source_column,
                        moving_card,
                        target_column
                    )
                )

        # Whether valid or invalid, stop dragging.
        # An invalid drop simply causes the original
        # cards to appear back in their source pile.
        self.clear_drag()

        self.clear_selection()

    # --------------------------------------------------
    # Mouse input
    # --------------------------------------------------

    def handle_click(self, mouse_pos):

        # Stock
        if self.stock_rect.collidepoint(
            mouse_pos
        ):
            self.click_stock()
            return

        # Waste
        if (
            self.waste_rect.collidepoint(
                mouse_pos
            )
            and self.waste
        ):
            self.selected_card = self.waste[-1]

            self.selected_source = (
                "waste",
                None
            )

            return

        # Foundation
        foundation_index = (
            self.get_foundation_at_position(
                mouse_pos
            )
        )

        # Waste -> foundation
        if (
            self.selected_card is not None
            and self.selected_source
            == ("waste", None)
            and foundation_index is not None
        ):
            moved = (
                self.move_waste_to_foundation(
                    foundation_index
                )
            )

            if moved:
                self.clear_selection()

            return

        # Tableau -> foundation
        if (
            self.selected_card is not None
            and self.selected_source is not None
            and self.selected_source[0]
            == "tableau"
            and foundation_index is not None
        ):
            moved = (
                self.move_tableau_to_foundation(
                    self.selected_source[1],
                    self.selected_card,
                    foundation_index
                )
            )

            if moved:
                self.clear_selection()

            return

        # Select foundation card
        if (
            foundation_index is not None
            and self.foundations[
                foundation_index
            ]
            and self.selected_card is None
        ):
            self.selected_card = (
                self.foundations[
                    foundation_index
                ][-1]
            )

            self.selected_source = (
                "foundation",
                foundation_index
            )

            return

        # Tableau click detection
        card, clicked_column = (
            self.get_tableau_card_at_position(
                mouse_pos
            )
        )

        target_column = (
            self.get_tableau_column_at_position(
                mouse_pos
            )
        )

        # Waste -> tableau
        if (
            self.selected_card is not None
            and self.selected_source
            == ("waste", None)
            and target_column is not None
        ):
            moved = (
                self.move_waste_to_tableau(
                    target_column
                )
            )

            if moved:
                self.clear_selection()

            return

        # Foundation -> tableau
        if (
            self.selected_card is not None
            and self.selected_source is not None
            and self.selected_source[0]
            == "foundation"
            and target_column is not None
        ):
            moved = (
                self.move_foundation_to_tableau(
                    self.selected_source[1],
                    target_column
                )
            )

            if moved:
                self.clear_selection()

            return

        # Tableau -> tableau
        if (
            self.selected_card is not None
            and self.selected_source is not None
            and self.selected_source[0]
            == "tableau"
            and target_column is not None
        ):
            source_column = (
                self.selected_source[1]
            )

            if target_column != source_column:
                moved = (
                    self.move_tableau_stack(
                        source_column,
                        self.selected_card,
                        target_column
                    )
                )

                if moved:
                    self.clear_selection()

                return

        # Select tableau card
        if card is not None:
            self.selected_card = card

            self.selected_source = (
                "tableau",
                clicked_column
            )

        else:
            self.clear_selection()

    # --------------------------------------------------
    # Double-click
    # --------------------------------------------------

    def handle_double_click(
            self,
            mouse_pos
    ):
        self.clear_selection()

        # ----------------------------
        # Stock
        # ----------------------------

        if self.stock_rect.collidepoint(
                mouse_pos
        ):
            self.click_stock()
            return

        # ----------------------------
        # Waste
        # -----------------------------------------------------

        if (
            self.waste_rect.collidepoint(
                mouse_pos
            )
            and self.waste
        ):
            card = self.waste[-1]

            source = (
                "waste",
                None
            )

            moved = (
                self.try_auto_move_to_foundation(
                    card,
                    source
                )
            )

            if (
                not moved
                and self.double_click_mode
                == "foundation_and_tableau"
            ):
                self.try_auto_move_to_tableau(
                    card,
                    source
                )

            return

        # ----------------------------
        # Foundation
        # ----------------------------

        foundation_index = (
            self.get_foundation_at_position(
                mouse_pos
            )
        )

        if (
            foundation_index is not None
            and self.foundations[
                foundation_index
            ]
        ):
            card = self.foundations[
                foundation_index
            ][-1]

            source = (
                "foundation",
                foundation_index
            )

            if (
                self.double_click_mode
                == "foundation_and_tableau"
            ):
                self.try_auto_move_to_tableau(
                    card,
                    source
                )

            return

        # ----------------------------
        # Tableau
        # ----------------------------

        card, column_index = (
            self.get_tableau_card_at_position(
                mouse_pos
            )
        )

        if card is None:
            return

        source = (
            "tableau",
            column_index
        )

        moved = (
            self.try_auto_move_to_foundation(
                card,
                source
            )
        )

        if (
            not moved
            and self.double_click_mode
            == "foundation_and_tableau"
        ):
            self.try_auto_move_to_tableau(
                card,
                source
            )

    # --------------------------------------------------
    # Events
    # --------------------------------------------------

    def handle_event(self, event):
        if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            if event.clicks >= 2:
                self.handle_double_click(
                    event.pos
                )

            else:
                self.handle_click(
                    event.pos
                )
