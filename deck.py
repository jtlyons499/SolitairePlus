import random

from card import Card


SUITS = [
    "Hearts",
    "Diamonds",
    "Clubs",
    "Spades"
]

RANKS = [
    "A",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "J",
    "Q",
    "K"
]


def create_deck():
    deck = []

    for suit in SUITS:
        for rank in RANKS:
            deck.append(
                Card(suit, rank)
            )

    random.shuffle(deck)

    return deck


def deal_tableau(deck):
    tableau = [
        [],
        [],
        [],
        [],
        [],
        [],
        []
    ]

    for column_index in range(7):

        for _ in range(column_index + 1):
            card = deck.pop()
            tableau[column_index].append(card)

        # Bottom card begins face-up
        tableau[column_index][-1].face_up = True

    return tableau