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
