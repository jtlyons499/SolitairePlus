import random
from collections import Counter

RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
SUITS = ["Clubs", "Diamonds", "Hearts", "Spades"]
RANK_VALUES = {
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
    "K": 13,
    "A": 14,
}


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


def evaluate_five_card_hand(cards):
    """Return a sortable traditional five-card poker score tuple."""
    if cards is None or len(cards) != 5 or any(card is None for card in cards):
        return None

    values = sorted(
        [RANK_VALUES[card["rank"]] for card in cards],
        reverse=True,
    )
    suits = [card["suit"] for card in cards]
    counts = Counter(values)

    is_flush = len(set(suits)) == 1
    unique_values = sorted(set(values), reverse=True)
    if 14 in unique_values:
        unique_values.append(1)

    straight_high = None
    for index in range(len(unique_values) - 4):
        window = unique_values[index:index + 5]
        if window[0] - window[4] == 4:
            straight_high = window[0]
            break

    if is_flush and straight_high is not None:
        return 8, straight_high

    quads = sorted(
        (value for value, count in counts.items() if count == 4),
        reverse=True,
    )
    if quads:
        quad = quads[0]
        kicker = max(value for value in values if value != quad)
        return 7, quad, kicker

    triples = sorted(
        (value for value, count in counts.items() if count == 3),
        reverse=True,
    )
    pairs_or_better = sorted(
        (value for value, count in counts.items() if count >= 2),
        reverse=True,
    )
    if triples:
        trip = triples[0]
        pair_candidates = [value for value in pairs_or_better if value != trip]
        if len(triples) >= 2:
            pair_candidates.append(triples[1])
        if pair_candidates:
            return 6, trip, max(pair_candidates)

    if is_flush:
        return 5, *values

    if straight_high is not None:
        return 4, straight_high

    if triples:
        trip = triples[0]
        kickers = sorted(
            (value for value in values if value != trip),
            reverse=True,
        )[:2]
        return 3, trip, *kickers

    exact_pairs = sorted(
        (value for value, count in counts.items() if count == 2),
        reverse=True,
    )
    if len(exact_pairs) >= 2:
        high_pair, low_pair = exact_pairs[:2]
        kicker = max(
            value for value in values
            if value not in (high_pair, low_pair)
        )
        return 2, high_pair, low_pair, kicker

    if len(exact_pairs) == 1:
        pair = exact_pairs[0]
        kickers = sorted(
            (value for value in values if value != pair),
            reverse=True,
        )[:3]
        return 1, pair, *kickers

    return 0, *values


def compare_scores(left, right):
    if left is None and right is None:
        return 0
    if left is None:
        return -1
    if right is None:
        return 1
    if left > right:
        return 1
    if left < right:
        return -1
    return 0
