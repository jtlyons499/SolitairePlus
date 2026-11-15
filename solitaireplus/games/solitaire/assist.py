import random

DEAL_MODE_RANDOM = "random"
DEAL_MODE_VERIFIED = "verified"
VALID_DEAL_MODES = {
    DEAL_MODE_RANDOM,
    DEAL_MODE_VERIFIED,
}

RANKS = [
    "A", "2", "3", "4", "5", "6", "7",
    "8", "9", "10", "J", "Q", "K",
]

PREFERRED_SUITS = [
    "Clubs",
    "Diamonds",
    "Hearts",
    "Spades",
]


def normalize_deal_mode(mode):
    mode = str(mode or DEAL_MODE_RANDOM).strip().lower()
    if mode not in VALID_DEAL_MODES:
        return DEAL_MODE_RANDOM
    return mode


def _ordered_cards_by_foundation_progress(deck, rng):
    cards_by_key = {
        (card.suit, card.rank): card
        for card in deck
    }

    suits = [
        suit
        for suit in PREFERRED_SUITS
        if any(card.suit == suit for card in deck)
    ]

    extras = sorted({
        card.suit
        for card in deck
        if card.suit not in suits
    })
    suits.extend(extras)

    if len(suits) != 4:
        raise ValueError(
            "Verified Solitaire deals require exactly four suits."
        )

    # Build a randomized interleaving of the four suit progressions while
    # preserving A->K order within each individual suit.  The old generator
    # walked rank-major (all aces, all twos, ...), which made the stock look
    # obviously patterned and caused race deals to feel nearly identical.
    next_rank_index = {suit: 0 for suit in suits}
    ordered = []

    while len(ordered) < 52:
        available_suits = [
            suit
            for suit in suits
            if next_rank_index[suit] < len(RANKS)
        ]
        suit = rng.choice(available_suits)
        rank = RANKS[next_rank_index[suit]]
        next_rank_index[suit] += 1

        card = cards_by_key.get((suit, rank))
        if card is None:
            raise ValueError(
                f"Verified deal is missing {rank} of {suit}."
            )
        ordered.append(card)

    if len(ordered) != 52:
        raise ValueError(
            "Verified Solitaire deals require a complete 52-card deck."
        )

    return ordered


def _build_verified_tableau(tableau_cards, rng):
    capacities = [1, 2, 3, 4, 5, 6, 7]
    reveal_orders = [[] for _ in capacities]
    remaining = list(capacities)

    # Cards are assigned in foundation-safe order. Each column preserves
    # that order, so when one card is removed, the next card revealed in
    # that same column is always later in the safe sequence.
    for card in tableau_cards:
        choices = [
            index
            for index, capacity in enumerate(remaining)
            if capacity > 0
        ]
        column_index = rng.choice(choices)
        reveal_orders[column_index].append(card)
        remaining[column_index] -= 1

    tableau = []
    for reveal_order in reveal_orders:
        column = list(reversed(reveal_order))
        for card in column:
            card.face_up = False
        if column:
            column[-1].face_up = True
        tableau.append(column)

    return tableau


def _build_verified_stock(stock_sequence, draw_count):
    draw_count = max(1, int(draw_count or 1))

    chunks = [
        stock_sequence[index:index + draw_count]
        for index in range(0, len(stock_sequence), draw_count)
    ]

    # Stock draws use pop(). Reversing the chunk order while preserving
    # the cards inside each chunk means a draw-3 group lands in waste with
    # the earliest foundation-safe card on top, then the next one beneath.
    stock = []
    for chunk in reversed(chunks):
        stock.extend(chunk)

    for card in stock:
        card.face_up = False

    return stock


def build_verified_deal(deck, draw_count=1, rng=None):
    """Return a standard Klondike deal with a known winning line.

    A randomized foundation-safe progression is distributed across the seven
    tableau reveal queues and the stock queue.  Each queue preserves its own
    safe order, while the global assignment varies the exposed cards and stock
    substantially from race to race.  The deal remains ordinary Klondike: only
    the exposed tableau card is face-up and stock starts down.
    """
    if rng is None:
        rng = random

    ordered = _ordered_cards_by_foundation_progress(deck, rng)

    # Randomly distribute the single foundation-safe progression across all
    # seven tableau reveal queues *and* the stock queue.  Earlier versions put
    # the first 28 safe cards in the tableau and the final 24 in stock, which
    # made every verified game visibly low-cards-first and tutorial-easy.
    capacities = [1, 2, 3, 4, 5, 6, 7, 24]
    queues = [[] for _ in capacities]
    remaining = list(capacities)

    for card in ordered:
        weighted_choices = []
        for index, capacity in enumerate(remaining):
            weighted_choices.extend([index] * max(0, capacity))
        if not weighted_choices:
            raise ValueError("Verified deal queue allocation exhausted early.")
        queue_index = rng.choice(weighted_choices)
        queues[queue_index].append(card)
        remaining[queue_index] -= 1

    tableau = []
    for reveal_order in queues[:7]:
        column = list(reversed(reveal_order))
        for card in column:
            card.face_up = False
        if column:
            column[-1].face_up = True
        tableau.append(column)

    stock = _build_verified_stock(queues[7], draw_count)
    return tableau, stock


def is_same_suit_descending_step(moving_card, target_card):
    return (
        moving_card.suit == target_card.suit
        and moving_card.value == target_card.value - 1
    )


def get_complete_suit_run(column, selected_card=None):
    """Return the complete K..A face-up run at the playable end, if any."""
    if len(column) < 13:
        return None

    run = column[-13:]

    if selected_card is not None and run[0] is not selected_card:
        return None

    if any(not card.face_up for card in run):
        return None

    suit = run[0].suit
    expected_values = list(range(13, 0, -1))

    if any(card.suit != suit for card in run):
        return None

    if [card.value for card in run] != expected_values:
        return None

    return run
