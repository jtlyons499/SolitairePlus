"""Game rendering: card art (faces, backs, felt), drawing one card sprite, and drawing the
table: challenge notice, stock, waste, foundations, tableau and dragged cards (a mixin of
rules.Game).
"""
import pygame

from solitaireplus.app import paths
from solitaireplus.games.solitaire.card import CARD_WIDTH, CARD_HEIGHT
from solitaireplus.games.solitaire.constants import (
    TABLE_GREEN,
    PLACEHOLDER,
    OUTLINE,
    START_X,
    START_Y,
    SPACING_X,
    FLIP_DURATION_MS,
)


class DrawingMixin:
    # --------------------------------------------------
    # Card sprite (draws the card flip animation too)
    # --------------------------------------------------

    def draw_card_sprite(
            self,
            card,
            x,
            y,
            selected=False
    ):
        rect = pygame.Rect(
            x,
            y,
            CARD_WIDTH,
            CARD_HEIGHT
        )

        # --------------------------------------------------
        # Flip animation
        # --------------------------------------------------

        if (
                self.flip_animation is not None
                and self.flip_animation["card"] is card
        ):
            elapsed = (
                    pygame.time.get_ticks()
                    - self.flip_animation[
                        "start_ticks"
                    ]
            )

            if elapsed >= FLIP_DURATION_MS:
                self.flip_animation = None

            else:
                progress = (
                        elapsed
                        / FLIP_DURATION_MS
                )

                # First half shows the back shrinking.
                if progress < 0.5:
                    image = (
                        self.get_card_back_surface()
                    )

                    width_percent = (
                            1.0
                            - progress * 2
                    )

                # Second half shows the front expanding.
                else:
                    key = (
                        self.get_card_image_key(
                            card
                        )
                    )

                    image = self.card_fronts[key]

                    width_percent = (
                            (progress - 0.5)
                            * 2
                    )

                animated_width = max(
                    1,
                    int(
                        CARD_WIDTH
                        * width_percent
                    )
                )

                animated_image = (
                    pygame.transform.scale(
                        image,
                        (
                            animated_width,
                            CARD_HEIGHT
                        )
                    )
                )

                animated_x = (
                        x
                        + (
                                CARD_WIDTH
                                - animated_width
                        ) // 2
                )

                self.screen.blit(
                    animated_image,
                    (
                        animated_x,
                        y
                    )
                )

                return

        # --------------------------------------------------
        # Normal card drawing
        # --------------------------------------------------

        if card.face_up:
            key = self.get_card_image_key(
                card
            )

            image = self.card_fronts[key]

        else:
            image = (
                self.get_card_back_surface()
            )

        self.screen.blit(
            image,
            (
                x,
                y
            )
        )

        if selected:
            pygame.draw.rect(
                self.screen,
                (
                    255,
                    215,
                    0
                ),
                rect,
                3
            )

        rect = pygame.Rect(
            x,
            y,
            CARD_WIDTH,
            CARD_HEIGHT
        )

        if card.face_up:
            key = self.get_card_image_key(
                card
            )

            image = self.card_fronts[
                key
            ]

        else:
            image = (
                self.get_card_back_surface()
            )

        self.screen.blit(
            image,
            (x, y)
        )

        # Optional outline if selected
        if selected:
            pygame.draw.rect(
                self.screen,
                (255, 215, 0),
                rect,
                3
            )

    # --------------------------------------------------
    # Card art
    # --------------------------------------------------

    def get_card_image_key(self, card):
        suit_map = {
            "Clubs": "C",
            "Diamonds": "D",
            "Hearts": "H",
            "Spades": "S",
            "C": "C",
            "D": "D",
            "H": "H",
            "S": "S",
        }

        suit_letter = suit_map[
            card.suit
        ]

        return f"{card.rank}{suit_letter}"

    def set_felt_surface(self, felt_surface):
        self.felt_surface = felt_surface

    def load_card_images(self):
        ranks = [
            "A", "2", "3", "4", "5", "6", "7",
            "8", "9", "10", "J", "Q", "K"
        ]

        suits = ["C", "D", "H", "S"]

        for rank in ranks:
            for suit in suits:
                key = f"{rank}{suit}"
                path = str(paths.asset((
                    f"cards/fronts/{key}.png"
                )))

                image = pygame.image.load(
                    path
                ).convert_alpha()

                # Optional safety resize in case
                # your files are not exactly 100x140
                image = pygame.transform.scale(
                    image,
                    (
                        CARD_WIDTH,
                        CARD_HEIGHT
                    )
                )

                self.card_fronts[key] = image



        # ----------------------------
        # Card backs
        # ----------------------------

        card_back_paths = {
            "back_default":
                str(paths.asset("cards/backs/back_default.png")),

            "back_red":
                str(paths.asset("cards/backs/back_red.png")),

            "back_cyan":
                str(paths.asset("cards/backs/back_cyan.png")),

            "back_july_four":
                str(paths.asset("cards/backs/back_july_four.png")),
        }

        for back_id, path in card_back_paths.items():
            image = pygame.image.load(
                path
            ).convert_alpha()

            image = pygame.transform.scale(
                image,
                (
                    CARD_WIDTH,
                    CARD_HEIGHT
                )
            )

            self.card_backs[
                back_id
            ] = image

    def set_card_back(
            self,
            card_back_id
    ):
        if card_back_id in self.card_backs:
            self.selected_card_back = (
                card_back_id
            )

    def get_card_back_surface(self):
        return self.card_backs[
            self.selected_card_back
        ]

    # --------------------------------------------------
    # Drawing
    # --------------------------------------------------

    def draw(self):
        if self.felt_surface is not None:
            self.screen.blit(
                self.felt_surface,
                (0, 0)
            )
        else:
            self.screen.fill(
                TABLE_GREEN
            )

        self.draw_stock()
        self.draw_waste()
        self.draw_foundations()
        self.draw_tableau()

        self.draw_challenge_notice()
        self.draw_hint()

        # Draw moving cards above all normal piles.
        self.draw_dragged_cards()

        self.update_victory_animation()
        self.draw_victory_animation()

    def draw_challenge_notice(self):
        if self.challenge_id != "all_or_nothing":
            return

        if self.challenge_notice_start_ticks <= 0:
            return

        elapsed = (
            pygame.time.get_ticks()
            - self.challenge_notice_start_ticks
        )

        if elapsed >= 7500:
            return

        panel_rect = pygame.Rect(375, 58, 350, 112)
        panel = pygame.Surface(
            panel_rect.size,
            pygame.SRCALPHA
        )

        alpha = 225
        if elapsed >= 6200:
            alpha = max(0, int(225 * (7500 - elapsed) / 1300))

        pygame.draw.rect(
            panel,
            (15, 24, 18, alpha),
            panel.get_rect(),
            border_radius=12
        )
        pygame.draw.rect(
            panel,
            (255, 220, 90, alpha),
            panel.get_rect(),
            2,
            border_radius=12
        )

        title = self.challenge_title_font.render(
            "ALL OR NOTHING",
            True,
            (255, 225, 105)
        )
        line_1 = self.challenge_body_font.render(
            "Build complete same-suit K to A runs in the tableau.",
            True,
            (245, 245, 245)
        )
        line_2 = self.challenge_body_font.render(
            "Foundations accept the full 13-card suit at once.",
            True,
            (245, 245, 245)
        )

        for surface in (title, line_1, line_2):
            surface.set_alpha(alpha)

        panel.blit(
            title,
            title.get_rect(center=(panel_rect.width // 2, 27))
        )
        panel.blit(
            line_1,
            line_1.get_rect(center=(panel_rect.width // 2, 64))
        )
        panel.blit(
            line_2,
            line_2.get_rect(center=(panel_rect.width // 2, 87))
        )

        self.screen.blit(
            panel,
            panel_rect.topleft
        )

    def draw_stock(self):
        if self.stock:
            self.screen.blit(
                self.get_card_back_surface(),
                (
                    self.stock_rect.x,
                    self.stock_rect.y
                )
            )

        else:
            pygame.draw.rect(
                self.screen,
                PLACEHOLDER,
                self.stock_rect,
                2
            )

    def draw_waste(self):
        if not self.waste:
            pygame.draw.rect(
                self.screen,
                PLACEHOLDER,
                self.waste_rect,
                2
            )
            return

        # Show up to the last 3 waste cards.
        # Only the newest/top card is actually playable.
        visible_cards = self.waste[-3:]

        history_offset = 22

        start_x = (
                self.waste_rect.x
                - history_offset
                * (len(visible_cards) - 1)
        )

        for index, card in enumerate(
                visible_cards
        ):

            if (
                    self.dragging
                    and self.drag_source
                    == ("waste", None)
                    and card is self.waste[-1]
            ):
                continue

            x = (
                    start_x
                    + index * history_offset
            )

            is_top_card = (
                    card is self.waste[-1]
            )

            self.draw_card_sprite(
                card,
                x,
                self.waste_rect.y,
                selected=(
                        is_top_card
                        and self.selected_card
                        is card
                )
            )

    def draw_foundations(self):
        for index, rect in enumerate(
                self.foundation_rects
        ):
            foundation = self.foundations[
                index
            ]

            dragging_this_card = (
                    self.dragging
                    and self.drag_source
                    == (
                        "foundation",
                        index
                    )
            )

            # While the top foundation card is being dragged,
            # keep the source pile visible underneath it.
            #
            # If another card remains in the pile, show that
            # newly exposed card. If the dragged card was the
            # only card, show the normal empty foundation slot.
            if dragging_this_card:

                if len(foundation) >= 2:
                    exposed_card = foundation[-2]

                    self.draw_card_sprite(
                        exposed_card,
                        rect.x,
                        rect.y,
                        selected=False
                    )

                else:
                    pygame.draw.rect(
                        self.screen,
                        PLACEHOLDER,
                        rect,
                        2
                    )

                continue

            if foundation:
                card = foundation[-1]

                self.draw_card_sprite(
                    card,
                    rect.x,
                    rect.y,
                    selected=(
                            self.selected_card
                            is card
                    )
                )

            else:
                pygame.draw.rect(
                    self.screen,
                    PLACEHOLDER,
                    rect,
                    2
                )

    def draw_tableau(self):
        for column_index, column in enumerate(
                self.tableau
        ):
            x = (
                    START_X
                    + column_index * SPACING_X
            )

            y = START_Y

            # ----------------------------
            # Empty column
            # ----------------------------

            if not column:
                pygame.draw.rect(
                    self.screen,
                    OUTLINE,
                    pygame.Rect(
                        x,
                        START_Y,
                        CARD_WIDTH,
                        CARD_HEIGHT
                    ),
                    2
                )

                continue

            # ----------------------------
            # Dynamic spacing
            # ----------------------------

            face_down_spacing, face_up_spacing = (
                self.get_tableau_spacings(
                    column
                )
            )

            # ----------------------------
            # Cards
            # ----------------------------

            for card_index, card in enumerate(
                    column
            ):

                dragging_this_card = (
                        self.dragging
                        and self.drag_source
                        == (
                            "tableau",
                            column_index
                        )
                        and self.drag_source_index
                        is not None
                        and card_index
                        >= self.drag_source_index
                )

                if not dragging_this_card:
                    self.draw_card_sprite(
                        card,
                        x,
                        y,
                        selected=(
                                self.selected_card
                                is card
                        )
                    )

                if card.face_up:
                    y += face_up_spacing

                else:
                    y += face_down_spacing



    def draw_dragged_cards(self):
        if not self.dragging:
            return

        if not self.drag_cards:
            return

        x = (
                self.drag_mouse_x
                - self.drag_offset_x
        )

        y = (
                self.drag_mouse_y
                - self.drag_offset_y
        )

        for index, card in enumerate(
                self.drag_cards
        ):
            self.draw_card_sprite(
                card,
                x,
                y + index * self.drag_spacing
            )
