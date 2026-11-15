"""Suit Snake Arcade Night mode helpers.

Suit Snake uses four playfield modes rather than speed-based difficulty.
Movement presentation (classic step vs. smooth interpolation) is selected
separately and does not change the underlying collision grid.
"""
from __future__ import annotations


SUIT_SNAKE_MODES = {
    "classic_standard": {
        "label": "CLASSIC STANDARD",
        "label_lines": ("CLASSIC", "STANDARD"),
        "ticket_multiplier": 1.00,
        "step_ms": 165,
        "grid_columns": 24,
        "grid_rows": 13,
        "cell_size": 32,
        "wraparound": False,
        "description": "Classic cabinet grid. Touching any border ends the run.",
    },
    "classic_big_grid": {
        "label": "CLASSIC BIG GRID",
        "label_lines": ("CLASSIC", "BIG GRID"),
        "ticket_multiplier": 1.00,
        "step_ms": 165,
        "grid_columns": 30,
        "grid_rows": 16,
        "cell_size": 28,
        "wraparound": False,
        "description": "More room for long chains, but the borders are still deadly.",
    },
    "lahey_wraparound": {
        "label": "LAHEY WRAPAROUND",
        "label_lines": ("LAHEY", "WRAPAROUND"),
        "ticket_multiplier": 1.00,
        "step_ms": 165,
        "grid_columns": 24,
        "grid_rows": 13,
        "cell_size": 32,
        "wraparound": True,
        "description": "Exit one edge and reappear on the opposite side of the grid.",
    },
    "lahey_wraparound_big_grid": {
        "label": "LAHEY WRAPAROUND BIG GRID",
        "label_lines": ("LAHEY WRAPAROUND", "BIG GRID"),
        "ticket_multiplier": 1.00,
        "step_ms": 165,
        "grid_columns": 30,
        "grid_rows": 16,
        "cell_size": 28,
        "wraparound": True,
        "description": "The larger grid plus edge wrapping for maximum roaming room.",
    },
}

# Backward-compatible alias for any older integration code that still imports
# the original name. New UI/code should refer to modes.
SUIT_SNAKE_DIFFICULTIES = SUIT_SNAKE_MODES

SUIT_SNAKE_MOVEMENT_STYLES = {
    "step": {
        "label": "STEP MOVEMENT",
        "description": "Classic Snake: the chain advances one grid cell at a time.",
    },
    "smooth": {
        "label": "SMOOTH MOVEMENT",
        "description": "Same grid rules, with continuous visual movement between cells.",
    },
}

SUIT_ORDER = ("spades", "diamonds", "clubs", "hearts")
RANK_ORDER = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A")

CARD_SEQUENCE = tuple(
    (rank, suit)
    for rank in RANK_ORDER
    for suit in SUIT_ORDER
)


def get_suit_snake_mode(mode_id):
    return SUIT_SNAKE_MODES.get(
        mode_id,
        SUIT_SNAKE_MODES["classic_standard"],
    )


def get_suit_snake_difficulty(difficulty_id):
    """Backward-compatible wrapper around the new mode system."""
    return get_suit_snake_mode(difficulty_id)


def get_suit_snake_movement_style(style_id):
    return SUIT_SNAKE_MOVEMENT_STYLES.get(
        style_id,
        SUIT_SNAKE_MOVEMENT_STYLES["step"],
    )


def sequence_card(index):
    """Return (rank, suit, deck_number) for a zero-based collection index."""
    try:
        index = max(0, int(index))
    except (TypeError, ValueError):
        index = 0
    deck_number, card_index = divmod(index, len(CARD_SEQUENCE))
    rank, suit = CARD_SEQUENCE[card_index]
    return rank, suit, deck_number + 1
