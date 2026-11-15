import pygame

CARD_WIDTH = 120
CARD_HEIGHT = 168

RANK_VALUES = {
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
    "K": 13
}


class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.face_up = False

    def __repr__(self):
        return f"{self.rank} of {self.suit}"

    @property
    def is_red(self):
        return self.suit in ["Hearts", "Diamonds"]

    @property
    def value(self):
        return RANK_VALUES[self.rank]

    def draw(self, screen, x, y, selected=False):
        rect = pygame.Rect(
            x,
            y,
            CARD_WIDTH,
            CARD_HEIGHT
        )

        if self.face_up:
            pygame.draw.rect(
                screen,
                (245, 245, 245),
                rect
            )

            pygame.draw.rect(
                screen,
                (30, 30, 30),
                rect,
                2
            )

            if self.is_red:
                color = (180, 30, 30)
            else:
                color = (20, 20, 20)

            font = pygame.font.SysFont(None, 28)

            text = font.render(
                f"{self.rank} {self.suit[0]}",
                True,
                color
            )

            screen.blit(
                text,
                (x + 8, y + 8)
            )

        else:
            pygame.draw.rect(
                screen,
                (40, 60, 150),
                rect
            )

            pygame.draw.rect(
                screen,
                (240, 240, 240),
                rect,
                2
            )

        # Gold outline when selected
        if selected:
            pygame.draw.rect(
                screen,
                (255, 215, 0),
                rect,
                4
            )