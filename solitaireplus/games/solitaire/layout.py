"""Game tableau geometry: dynamic column spacing, card and drop-target rects, and finding the
tableau card, column or foundation under the mouse (a mixin of rules.Game).
"""
import pygame

from solitaireplus.games.solitaire.card import CARD_WIDTH, CARD_HEIGHT
from solitaireplus.games.solitaire.constants import (
    BASE_HEIGHT,
    START_X,
    START_Y,
    SPACING_X,
    FACE_DOWN_SPACING,
    FACE_UP_SPACING,
)


class LayoutMixin:
    # --------------------------------------------------
    # Dynamic tableau spacing
    # --------------------------------------------------

    def get_tableau_spacings(self, column):
        bottom_margin = 20

        available_height = (
            BASE_HEIGHT
            - START_Y
            - bottom_margin
        )

        normal_stack_height = CARD_HEIGHT

        for card in column[:-1]:
            if card.face_up:
                normal_stack_height += (
                    FACE_UP_SPACING
                )

            else:
                normal_stack_height += (
                    FACE_DOWN_SPACING
                )

        face_down_spacing = FACE_DOWN_SPACING
        face_up_spacing = FACE_UP_SPACING

        if normal_stack_height > available_height:
            extra_cards = len(column) - 1

            if extra_cards > 0:
                compressed_spacing = (
                    available_height
                    - CARD_HEIGHT
                ) / extra_cards

                face_down_spacing = min(
                    FACE_DOWN_SPACING,
                    compressed_spacing
                )

                face_up_spacing = min(
                    FACE_UP_SPACING,
                    compressed_spacing
                )

        return (
            face_down_spacing,
            face_up_spacing
        )

    def get_tableau_card_rect(
            self,
            column_index,
            target_card
    ):
        column = self.tableau[
            column_index
        ]

        x = (
                START_X
                + column_index * SPACING_X
        )

        y = START_Y

        face_down_spacing, face_up_spacing = (
            self.get_tableau_spacings(
                column
            )
        )

        for card in column:
            rect = pygame.Rect(
                x,
                y,
                CARD_WIDTH,
                CARD_HEIGHT
            )

            if card is target_card:
                return rect

            if card.face_up:
                y += face_up_spacing
            else:
                y += face_down_spacing

        return None

    def get_tableau_target_rect(
            self,
            column_index
    ):
        column = self.tableau[
            column_index
        ]

        x = (
                START_X
                + column_index * SPACING_X
        )

        if not column:
            return pygame.Rect(
                x,
                START_Y,
                CARD_WIDTH,
                CARD_HEIGHT
            )

        return self.get_tableau_card_rect(
            column_index,
            column[-1]
        )

    # --------------------------------------------------
    # Finding clicked cards
    # --------------------------------------------------

    def get_tableau_card_at_position(
        self,
        mouse_pos
    ):
        for column_index, column in enumerate(
            self.tableau
        ):
            x = (
                START_X
                + column_index * SPACING_X
            )

            y = START_Y

            face_down_spacing, face_up_spacing = (
                self.get_tableau_spacings(
                    column
                )
            )

            card_positions = []

            for card in column:
                rect = pygame.Rect(
                    x,
                    y,
                    CARD_WIDTH,
                    CARD_HEIGHT
                )

                card_positions.append(
                    (card, rect)
                )

                if card.face_up:
                    y += face_up_spacing

                else:
                    y += face_down_spacing

            for card, rect in reversed(
                card_positions
            ):
                if (
                    rect.collidepoint(mouse_pos)
                    and card.face_up
                ):
                    return card, column_index

        return None, None

    def get_tableau_column_at_position(
        self,
        mouse_pos
    ):
        for column_index in range(7):
            x = (
                START_X
                + column_index * SPACING_X
            )

            column_rect = pygame.Rect(
                x,
                START_Y,
                CARD_WIDTH,
                BASE_HEIGHT - START_Y
            )

            if column_rect.collidepoint(
                mouse_pos
            ):
                return column_index

        return None

    def get_foundation_at_position(
        self,
        mouse_pos
    ):
        for index, rect in enumerate(
            self.foundation_rects
        ):
            if rect.collidepoint(mouse_pos):
                return index

        return None
