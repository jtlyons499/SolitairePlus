"""Game hint system: finding, requesting and drawing a hint (a mixin of rules.Game)."""
import pygame
import math

from solitaireplus.games.solitaire.assist import get_complete_suit_run
from solitaireplus.games.solitaire.constants import HINT_DURATION_MS


class HintMixin:
    # --------------------------------------------------
    # Hint system
    # --------------------------------------------------

    def is_recent_tableau_hint(
            self,
            source_index,
            target_index,
            card
    ):

        for recent_move in self.recent_hint_moves:

            (
                recent_source,
                recent_target,
                recent_rank,
                recent_suit
            ) = recent_move

            same_stack = (
                    recent_rank == card.rank
                    and recent_suit == card.suit
            )

            if not same_stack:
                continue

            # Exact same hint again.
            if (
                    recent_source == source_index
                    and recent_target == target_index
            ):
                return True

            # Reverse of a recent hint.
            if (
                    recent_source == target_index
                    and recent_target == source_index
            ):
                return True

        return False

    def find_hint(self):

        # ==================================================
        # ALL OR NOTHING: completed suit -> foundation
        # ==================================================

        if self.challenge_id == "all_or_nothing":
            empty_foundation_index = next(
                (
                    index
                    for index, foundation in enumerate(self.foundations)
                    if not foundation
                ),
                None
            )

            if empty_foundation_index is not None:
                for column_index, column in enumerate(self.tableau):
                    run = get_complete_suit_run(column)
                    if run is None:
                        continue

                    return {
                        "source_rect": self.get_tableau_card_rect(
                            column_index,
                            run[0]
                        ),
                        "target_rect": self.foundation_rects[
                            empty_foundation_index
                        ],
                        "text": "Move complete suit to foundation",
                    }

        # ==================================================
        # 1. Tableau -> foundation
        # ==================================================

        for column_index, column in enumerate(
                self.tableau
        ):
            if not column:
                continue

            card = column[-1]

            if not card.face_up:
                continue

            for foundation_index, foundation in enumerate(
                    self.foundations
            ):
                if self.can_place_on_foundation(
                        card,
                        foundation
                ):
                    return {
                        "source_rect":
                            self.get_tableau_card_rect(
                                column_index,
                                card
                            ),

                        "target_rect":
                            self.foundation_rects[
                                foundation_index
                            ],

                        "text":
                            "Move card to foundation",
                    }

        # ==================================================
        # 2. Waste -> foundation
        # ==================================================

        if self.waste:
            card = self.waste[-1]

            for foundation_index, foundation in enumerate(
                    self.foundations
            ):
                if self.can_place_on_foundation(
                        card,
                        foundation
                ):
                    return {
                        "source_rect":
                            self.waste_rect.copy(),

                        "target_rect":
                            self.foundation_rects[
                                foundation_index
                            ],

                        "text":
                            "Move waste card to foundation",
                    }

        # ==================================================
        # 3. Tableau -> tableau
        #
        # First prefer moves that reveal a face-down card.
        # ==================================================

        for source_index, source_column in enumerate(
                self.tableau
        ):
            if not source_column:
                continue

            for card_index, card in enumerate(
                    source_column
            ):
                if not card.face_up:
                    continue

                # Prefer a move that exposes a hidden card.
                reveals_hidden = (
                        card_index > 0
                        and not source_column[
                    card_index - 1
                    ].face_up
                )

                if not reveals_hidden:
                    continue

                for target_index, target_column in enumerate(
                        self.tableau
                ):
                    if target_index == source_index:
                        continue

                    if not target_column:
                        legal = (
                                card.rank == "K"
                        )

                    else:
                        legal = (
                            self.can_place_on_tableau(
                                card,
                                target_column[-1]
                            )
                        )

                    if legal:
                        return {
                            "source_rect":
                                self.get_tableau_card_rect(
                                    source_index,
                                    card
                                ),

                            "target_rect":
                                self.get_tableau_target_rect(
                                    target_index
                                ),

                            "text":
                                "Move stack to reveal a card",

                            "move_type":
                                "tableau_to_tableau",

                            "source_index":
                                source_index,

                            "target_index":
                                target_index,

                            "card_rank":
                                card.rank,

                            "card_suit":
                                card.suit,
                        }

        # ==================================================
        # 4. Waste -> tableau
        # ==================================================

        if self.waste:
            card = self.waste[-1]

            for target_index, target_column in enumerate(
                    self.tableau
            ):
                if not target_column:
                    legal = (
                            card.rank == "K"
                    )

                else:
                    legal = (
                        self.can_place_on_tableau(
                            card,
                            target_column[-1]
                        )
                    )

                if legal:
                    return {
                        "source_rect":
                            self.waste_rect.copy(),

                        "target_rect":
                            self.get_tableau_target_rect(
                                target_index
                            ),

                        "text":
                            "Move waste card to tableau",
                    }

        # ==================================================
        # 5. Useful tableau -> tableau move
        #
        # Avoid moves that simply shift an entire
        # face-up pile into an empty column.
        # ==================================================

        for source_index, source_column in enumerate(
                self.tableau
        ):
            if not source_column:
                continue

            for card_index, card in enumerate(
                    source_column
            ):

                if not card.face_up:
                    continue

                for target_index, target_column in enumerate(
                        self.tableau
                ):
                    if target_index == source_index:
                        continue

                    # ----------------------------
                    # Empty tableau
                    # ----------------------------

                    if not target_column:

                        if card.rank != "K":
                            continue

                        # If this King is the first card
                        # in the source column, moving it
                        # just transfers the entire pile
                        # from one empty slot to another.
                        if card_index == 0:
                            continue

                        legal = True

                    # ----------------------------
                    # Occupied tableau
                    # ----------------------------

                    else:
                        legal = (
                            self.can_place_on_tableau(
                                card,
                                target_column[-1]
                            )
                        )

                    if not legal:
                        continue

                    # ==================================================
                    # Avoid meaningless equivalent-parent moves
                    #
                    # Example:
                    #
                    # J - 10 - 9 - 8 - 7
                    #
                    # moving the 9-8-7 onto another 10 without
                    # revealing anything underneath.
                    # ==================================================

                    if (
                            target_column
                            and card_index > 0
                    ):

                        source_parent = (
                            source_column[
                                card_index - 1
                                ]
                        )

                        target_parent = (
                            target_column[-1]
                        )

                        if (
                                source_parent.face_up
                                and source_parent.rank
                                == target_parent.rank
                        ):
                            continue

                    # ==================================================
                    # Avoid recently suggested loops / reversals
                    # ==================================================

                    if self.is_recent_tableau_hint(
                            source_index,
                            target_index,
                            card
                    ):
                        continue

                    return {
                        "source_rect":
                            self.get_tableau_card_rect(
                                source_index,
                                card
                            ),

                        "target_rect":
                            self.get_tableau_target_rect(
                                target_index
                            ),

                        "text":
                            "Move card or stack",

                        "move_type":
                            "tableau_to_tableau",

                        "source_index":
                            source_index,

                        "target_index":
                            target_index,

                        "card_rank":
                            card.rank,

                        "card_suit":
                            card.suit,
                    }

        # ==================================================
        # 6. Nothing obvious -> draw from stock
        # ==================================================

        if self.stock or self.waste:
            return {
                "source_rect":
                    self.stock_rect.copy(),

                "target_rect":
                    None,

                "text":
                    "Draw from stock",
            }

        return None

    def request_hint(self):

        if not self.hints_enabled:
            return False

        if (
                self.hints_remaining
                is not None
                and self.hints_remaining <= 0
        ):
            return False

        if self.victory_animation is not None:
            return False

        self.clear_selection()

        hint = self.find_hint()

        if hint is None:
            return False

        self.hint_data = hint

        if (
                hint.get(
                    "move_type"
                )
                == "tableau_to_tableau"
        ):

            recent_move = (
                hint["source_index"],
                hint["target_index"],
                hint["card_rank"],
                hint["card_suit"],
            )

            self.recent_hint_moves.append(
                recent_move
            )

            if (
                    len(
                        self.recent_hint_moves
                    )
                    > self.max_recent_hint_moves
            ):
                self.recent_hint_moves.pop(0)

        self.hint_start_ticks = (
            pygame.time.get_ticks()
        )

        if self.hints_remaining is not None:
            self.hints_remaining -= 1

        return True

    def draw_hint(self):

        if self.hint_data is None:
            return

        elapsed = (
                pygame.time.get_ticks()
                - self.hint_start_ticks
        )

        if elapsed >= HINT_DURATION_MS:
            self.hint_data = None
            return

        source_rect = self.hint_data[
            "source_rect"
        ]

        target_rect = self.hint_data[
            "target_rect"
        ]

        # A bright pulse is much easier to follow than the old static
        # outline, especially when source and destination are far apart.
        phase = (elapsed % 520) / 520.0
        pulse = (
            math.sin(phase * math.tau)
            + 1.0
        ) / 2.0

        border_width = 3 + int(round(pulse * 4))
        highlight_color = (
            255,
            int(185 + 70 * pulse),
            int(25 + 120 * pulse)
        )

        def draw_pulsing_outline(rect):
            if rect is None:
                return

            outer = rect.inflate(
                int(4 + pulse * 6),
                int(4 + pulse * 6)
            )

            pygame.draw.rect(
                self.screen,
                highlight_color,
                outer,
                border_width,
                border_radius=5
            )

            if pulse >= 0.55:
                pygame.draw.rect(
                    self.screen,
                    (255, 255, 255),
                    rect.inflate(2, 2),
                    2,
                    border_radius=4
                )

        draw_pulsing_outline(source_rect)
        draw_pulsing_outline(target_rect)
