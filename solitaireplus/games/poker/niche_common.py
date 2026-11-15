import random

# The hand evaluator is shared by every poker variant and lives in core.py.
# These names stay importable from here for Five-O, Blind Man's Bluff and tests.
from solitaireplus.games.poker.core import (
    RANK_VALUES,
    compare_scores,
    evaluate_five_cards as evaluate_five_card_hand,
)

RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
SUITS = ["Clubs", "Diamonds", "Hearts", "Spades"]


def build_standard_deck(rng=None):
    rng = rng or random
    deck = [
        {"rank": rank, "suit": suit}
        for suit in SUITS
        for rank in RANKS
    ]
    rng.shuffle(deck)
    return deck


def card_key(card):
    if not card:
        return None
    return card.get("rank"), card.get("suit")


def round_chip_amount(value, minimum=1):
    value = max(float(minimum), float(value))
    if value >= 100:
        step = 10
    elif value >= 25:
        step = 5
    else:
        step = 1
    return max(minimum, int(round(value / step) * step))
