"""Draw-one race deals sampled from independently shuffled, proven games.

The pool contains legal winning lines, not constructed rank queues. Runtime
selection and colour-preserving suit permutations keep repeat races varied.
This module also checks the proof without importing Pygame.
"""
from collections import deque
import json
from pathlib import Path
import random

SUITS = ("Clubs", "Diamonds", "Hearts", "Spades")
RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
_recent = deque(maxlen=128)
_pool = None


def rank(card):
    return card % 13 + 1


def red(card):
    return card // 13 in (1, 2)


def fits(card, column):
    return rank(card) == 13 if not column else (
        rank(card) + 1 == rank(column[-1]) and red(card) != red(column[-1])
    )


def initial_state(deck):
    """Deck is encoded in deal/draw order, rather than Python pop order."""
    if sorted(deck) != list(range(52)):
        raise ValueError("Race deal must contain each card exactly once")
    columns, start = [], 0
    for size in range(1, 8):
        columns.append((size - 1, tuple(deck[start:start + size])))
        start += size
    return tuple(columns), tuple(deck[28:]), (0, 0, 0, 0)


def apply_move(state, move):
    """Validate a solver step using ordinary Klondike rules.

    Any remaining reserve card is reachable with unlimited draw-one passes.
    Removing it represents drawing/recycling up to that card, then playing the
    top waste card. Reserve order never changes across passes.
    """
    columns, reserve, foundations = state
    columns = list(columns)
    foundations = list(foundations)
    kind, source, destination, count = move
    if kind.startswith("r"):
        if source not in reserve:
            raise ValueError("Card is no longer in the reserve")
        cards = (source,)
        reserve = tuple(card for card in reserve if card != source)
    elif kind.startswith("t"):
        hidden, column = columns[source]
        if count < 1 or len(column) - count < hidden:
            raise ValueError("Cannot move hidden cards")
        cards = column[-count:]
        if any(not fits(cards[index], cards[:index]) for index in range(1, len(cards))):
            raise ValueError("Invalid descending alternating run")
        remaining = column[:-count]
        columns[source] = (min(hidden, max(0, len(remaining) - 1)), remaining)
    else:
        raise ValueError("Unknown race solution step")
    if kind.endswith("f"):
        card = cards[0]
        suit = card // 13
        if len(cards) != 1 or rank(card) != foundations[suit] + 1:
            raise ValueError("Illegal foundation move")
        foundations[suit] += 1
    else:
        hidden, target = columns[destination]
        if not fits(cards[0], target):
            raise ValueError("Illegal tableau move")
        columns[destination] = (hidden, target + cards)
    return tuple(columns), reserve, tuple(foundations)


def verify_deal(deck, solution):
    state = initial_state(deck)
    for move in solution:
        state = apply_move(state, move)
    if state[2] != (13, 13, 13, 13):
        raise ValueError("Race proof does not finish all foundations")
    return True


def opening_is_varied(deck):
    exposed = [deck[index] for index in (0, 2, 5, 9, 14, 20, 27)]
    values = [rank(card) for card in exposed]
    return (sum(value >= 7 for value in values) >= 3
            and sum(value <= 3 for value in values) <= 2
            and len(set(values)) >= 5)


def _load_pool():
    global _pool
    if _pool is None:
        # PyInstaller ships this file through the existing --add-data data flag.
        path = Path(__file__).resolve().parent / "data" / "solitaire_race_deals.json"
        entries = json.loads(path.read_text(encoding="utf-8"))["deals"]
        if not entries:
            raise ValueError("Race deal pool is empty")
        for entry in entries:
            verify_deal(entry["deck"], entry["solution"])
            if not opening_is_varied(entry["deck"]):
                raise ValueError("Race opening failed variety check")
        _pool = entries
    return _pool


def build_race_deal(rng=None):
    """Return Card objects for a standard 1..7 tableau and 24-card stock."""
    from card import Card

    rng = rng or random.SystemRandom()
    pool = _load_pool()
    candidates = [index for index in range(len(pool)) if index not in _recent]
    if not candidates:
        # With a smaller custom pool, exhaust every entry before starting again.
        _recent.clear()
        candidates = list(range(len(pool)))
    index = rng.choice(candidates)
    _recent.append(index)
    entry = pool[index]
    black = rng.sample([0, 3], 2)
    red_suits = rng.sample([1, 2], 2)
    if rng.randrange(2):
        black, red_suits = red_suits, black
    suit_map = {0: black[0], 3: black[1], 1: red_suits[0], 2: red_suits[1]}
    deck = [suit_map[card // 13] * 13 + card % 13 for card in entry["deck"]]
    state = initial_state(deck)
    tableau = []
    for hidden, encoded in state[0]:
        column = [Card(SUITS[card // 13], RANKS[card % 13]) for card in encoded]
        column[-1].face_up = True
        tableau.append(column)
    stock = [Card(SUITS[card // 13], RANKS[card % 13]) for card in reversed(state[1])]
    return tableau, stock, {"pool_id": index, "solution_steps": len(entry["solution"])}
