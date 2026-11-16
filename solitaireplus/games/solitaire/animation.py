"""Game animations: the card flip and the victory card cascade (a mixin of rules.Game)."""
import pygame

from solitaireplus.games.solitaire.card import CARD_WIDTH, CARD_HEIGHT
from solitaireplus.games.solitaire.constants import (
    BASE_WIDTH,
    BASE_HEIGHT,
    FLIP_DURATION_MS,
    VICTORY_DURATION_MS,
    VICTORY_CARD_DELAY_MS,
    VICTORY_GRAVITY,
    VICTORY_BOUNCE,
)


class AnimationMixin:
    # --------------------------------------------------
    # Card flip animation
    # --------------------------------------------------

    def start_flip_animation(
            self,
            card
    ):
        card.face_up = True

        self.flip_animation = {
            "card": card,
            "start_ticks": pygame.time.get_ticks(),
        }

    def is_flip_animating(self):
        # Normally the renderer clears a finished flip when it draws the
        # card. Clear it here too, so code that runs between frames (auto-
        # solve) does not wait on a flip that has already ended.
        if self.flip_animation is None:
            return False

        elapsed = (
                pygame.time.get_ticks()
                - self.flip_animation["start_ticks"]
        )

        if elapsed >= FLIP_DURATION_MS:
            self.flip_animation = None
            return False

        return True

    # --------------------------------------------------
    # Victory animation
    # --------------------------------------------------

    def start_victory_animation(self):
        animated_cards = []

        # Work from the four completed foundations.
        for foundation_index, foundation in enumerate(
                self.foundations
        ):
            foundation_rect = self.foundation_rects[
                foundation_index
            ]

            for card_index, card in enumerate(
                    reversed(foundation)
            ):
                # Alternate horizontal directions and
                # vary the strength slightly by foundation.
                direction = (
                    -1
                    if foundation_index % 2 == 0
                    else 1
                )

                speed_x = (
                        direction
                        * (
                                3.2
                                + foundation_index * 0.55
                                + card_index * 0.025
                        )
                )

                speed_y = (
                        -5.5
                        - (card_index % 5) * 0.45
                )

                animated_cards.append(
                    {
                        "card": card,
                        "x": float(
                            foundation_rect.x
                        ),
                        "y": float(
                            foundation_rect.y
                        ),
                        "vx": speed_x,
                        "vy": speed_y,
                        "delay": (
                                len(animated_cards)
                                * VICTORY_CARD_DELAY_MS
                        ),
                        "active": False,
                    }
                )

        self.victory_animation = {
            "start_ticks": pygame.time.get_ticks(),
            "last_ticks": pygame.time.get_ticks(),
            "cards": animated_cards,
        }

    def start_debug_victory_animation(self):
        all_cards = []

        # Tableau cards
        for column in self.tableau:
            all_cards.extend(
                column
            )

        # Stock cards
        all_cards.extend(
            self.stock
        )

        # Waste cards
        all_cards.extend(
            self.waste
        )

        # Foundation cards
        for foundation in self.foundations:
            all_cards.extend(
                foundation
            )

        animated_cards = []

        for index, card in enumerate(
                all_cards
        ):
            foundation_index = (
                    index % 4
            )

            foundation_rect = (
                self.foundation_rects[
                    foundation_index
                ]
            )

            direction = (
                -1
                if foundation_index % 2 == 0
                else 1
            )

            speed_x = (
                    direction
                    * (
                            3.2
                            + foundation_index * 0.55
                            + index * 0.025
                    )
            )

            speed_y = (
                    -5.5
                    - (index % 5) * 0.45
            )

            animated_cards.append(
                {
                    "card": card,

                    "x": float(
                        foundation_rect.x
                    ),

                    "y": float(
                        foundation_rect.y
                    ),

                    "vx": speed_x,
                    "vy": speed_y,

                    "delay": (
                            index
                            * VICTORY_CARD_DELAY_MS
                    ),

                    "active": False,
                }
            )

        now = pygame.time.get_ticks()

        self.victory_animation = {
            "start_ticks": now,
            "last_ticks": now,
            "cards": animated_cards,
        }

    def update_victory_animation(self):
        if self.victory_animation is None:
            return

        now = pygame.time.get_ticks()

        elapsed = (
                now
                - self.victory_animation[
                    "start_ticks"
                ]
        )

        delta_ms = (
                now
                - self.victory_animation[
                    "last_ticks"
                ]
        )

        self.victory_animation[
            "last_ticks"
        ] = now

        # Normalize around 60 FPS.
        delta = min(
            2.0,
            delta_ms / 16.67
        )

        for data in self.victory_animation[
            "cards"
        ]:
            if elapsed < data["delay"]:
                continue

            data["active"] = True

            data["x"] += (
                    data["vx"] * delta
            )

            data["y"] += (
                    data["vy"] * delta
            )

            data["vy"] += (
                    VICTORY_GRAVITY * delta
            )

            # Bounce off bottom edge.
            if (
                    data["y"] + CARD_HEIGHT
                    >= BASE_HEIGHT
            ):
                data["y"] = (
                        BASE_HEIGHT
                        - CARD_HEIGHT
                )

                data["vy"] *= (
                    VICTORY_BOUNCE
                )

                # Lose a little horizontal energy.
                data["vx"] *= 0.98

            # Wrap horizontally.
            if (
                    data["x"]
                    > BASE_WIDTH
            ):
                data["x"] = (
                    -CARD_WIDTH
                )

            elif (
                    data["x"] + CARD_WIDTH
                    < 0
            ):
                data["x"] = (
                    BASE_WIDTH
                )

        if elapsed >= VICTORY_DURATION_MS:
            self.victory_animation = None

    def draw_victory_animation(self):
        if self.victory_animation is None:
            return

        for data in self.victory_animation[
            "cards"
        ]:
            if not data["active"]:
                continue

            card = data["card"]

            key = self.get_card_image_key(
                card
            )

            image = self.card_fronts[
                key
            ]

            self.screen.blit(
                image,
                (
                    int(data["x"]),
                    int(data["y"])
                )
            )
