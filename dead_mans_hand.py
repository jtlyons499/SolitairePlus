"""Core data and pure helpers for the Dead Man's Hand raycast prototype.

This module deliberately has no pygame dependency so map validation and Career
integration can be tested without initializing the renderer.
"""

from __future__ import annotations

import math

GAME_ID = "dead_mans_hand"
GAME_TITLE = "Dead Man's Hand"
CAREER_ACTIVITY_ID = "dead_mans_hand"

RENDER_WIDTH = 480
RENDER_HEIGHT = 270
FOV = math.radians(62.0)
MAX_RAY_DEPTH = 24.0

# Walls are intentionally grid-aligned. Different digits are rendered with
# different procedural materials by dead_mans_hand_game.py.
LEVELS = (
    {
        "name": "The Ante",
        "map": (
            "1111111111111111",
            "1..............1",
            "1..22..........1",
            "1..22....333...1",
            "1........333...1",
            "1....11........1",
            "1....11........1",
            "1..............1",
            "1..333.........1",
            "1..333....22...1",
            "1..............1",
            "1111111111111111",
        ),
        "player": (2.5, 9.5, -0.55),
        "enemies": (
            ("9H", 11.5, 2.5),
            ("9S", 13.0, 4.5),
            ("JS", 8.5, 7.5),
            ("9D", 12.5, 9.5),
            ("KH", 5.5, 2.5),
        ),
    },
    {
        "name": "Skull Saloon",
        "map": (
            "111111111111111111",
            "1................1",
            "1..222......333..1",
            "1..222......333..1",
            "1................1",
            "1.....11..11.....1",
            "1.....11..11.....1",
            "1................1",
            "1..333......222..1",
            "1..333......222..1",
            "1................1",
            "1.......11.......1",
            "1................1",
            "111111111111111111",
        ),
        "player": (2.5, 11.5, -0.72),
        "enemies": (
            ("9C", 16.0, 2.5),
            ("9D", 9.5, 2.0),
            ("JH", 15.0, 6.5),
            ("JS", 10.5, 8.0),
            ("QH", 4.5, 4.5),
            ("QS", 7.5, 10.0),
            ("KC", 14.5, 10.5),
            ("KS", 7.5, 2.5),
        ),
    },
    {
        "name": "All In",
        "map": (
            "111111111111111111",
            "1................1",
            "1.222..333..222..1",
            "1.222..333..222..1",
            "1................1",
            "1....11....11....1",
            "1....11....11....1",
            "1................1",
            "1.333..222..333..1",
            "1.333..222..333..1",
            "1................1",
            "1....22....22....1",
            "1................1",
            "111111111111111111",
        ),
        "player": (2.5, 11.5, -0.55),
        "enemies": (
            ("8S", 16.0, 2.0),
            ("8C", 11.5, 4.5),
            ("9H", 10.5, 2.0),
            ("9D", 15.0, 7.0),
            ("JH", 10.5, 10.5),
            ("JS", 5.5, 7.0),
            ("QH", 5.5, 3.0),
            ("QS", 13.5, 11.0),
            ("KH", 8.5, 7.0),
            ("KS", 15.0, 11.0),
        ),
    },
)


def normalize_angle(angle: float) -> float:
    """Return an angle in the [-pi, pi) range."""
    return (float(angle) + math.pi) % (math.tau) - math.pi


def map_size(level: dict) -> tuple[int, int]:
    rows = level.get("map") or ()
    if not rows:
        return 0, 0
    return len(rows[0]), len(rows)


def wall_at(level: dict, x: float, y: float) -> str | None:
    """Return wall material at a world coordinate or None for open space."""
    rows = level.get("map") or ()
    if not rows:
        return "1"
    tx = int(math.floor(x))
    ty = int(math.floor(y))
    if ty < 0 or ty >= len(rows) or tx < 0 or tx >= len(rows[0]):
        return "1"
    cell = rows[ty][tx]
    return None if cell == "." else cell


def validate_levels(levels=LEVELS) -> list[str]:
    """Return human-readable validation errors for level data."""
    errors: list[str] = []
    for index, level in enumerate(levels):
        label = level.get("name") or f"Level {index + 1}"
        rows = level.get("map") or ()
        if not rows:
            errors.append(f"{label}: map is empty")
            continue
        width = len(rows[0])
        if width < 3 or len(rows) < 3:
            errors.append(f"{label}: map is too small")
            continue
        if any(len(row) != width for row in rows):
            errors.append(f"{label}: map rows have different widths")
            continue
        if any(cell not in ".123" for row in rows for cell in row):
            errors.append(f"{label}: map contains an unsupported tile")
        if any(row[0] == "." or row[-1] == "." for row in rows):
            errors.append(f"{label}: side border is open")
        if any(cell == "." for cell in rows[0] + rows[-1]):
            errors.append(f"{label}: top/bottom border is open")
        player = level.get("player") or ()
        if len(player) != 3 or (len(player) == 3 and wall_at(level, player[0], player[1])):
            errors.append(f"{label}: invalid player spawn")
        for enemy in level.get("enemies") or ():
            if len(enemy) != 3:
                errors.append(f"{label}: malformed enemy spawn")
                continue
            if wall_at(level, enemy[1], enemy[2]):
                errors.append(f"{label}: enemy {enemy[0]} starts inside a wall")
    return errors


LEVEL_VALIDATION_ERRORS = validate_levels()
