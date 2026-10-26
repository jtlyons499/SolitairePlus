"""Core data and pure helpers for Dead Man's Hand.

This module deliberately has no pygame dependency so map validation, level
progression, and Career integration can be tested without initializing the
renderer.
"""

from __future__ import annotations

import math

GAME_ID = "dead_mans_hand"
GAME_TITLE = "Dead Man's Hand"
CAREER_ACTIVITY_ID = "dead_mans_hand"

RENDER_WIDTH = 480
RENDER_HEIGHT = 270
FOV = math.radians(62.0)
MAX_RAY_DEPTH = 28.0


def _build_map(width: int, height: int, blocks=()) -> tuple[str, ...]:
    """Build an enclosed grid map from authored rectangular wall blocks."""
    width = max(8, int(width))
    height = max(8, int(height))
    grid = [["." for _ in range(width)] for _ in range(height)]
    for x in range(width):
        grid[0][x] = "1"
        grid[-1][x] = "1"
    for y in range(height):
        grid[y][0] = "1"
        grid[y][-1] = "1"

    for material, bx, by, bw, bh in blocks:
        material = str(material)
        for y in range(int(by), int(by + bh)):
            for x in range(int(bx), int(bx + bw)):
                if 0 < x < width - 1 and 0 < y < height - 1:
                    grid[y][x] = material
    return tuple("".join(row) for row in grid)


def _enemy_spawns(rows, player, cards, salt=0):
    """Spread an authored card roster across open floor cells deterministically."""
    px, py, _angle = player
    candidates = []
    for y, row in enumerate(rows):
        for x, cell in enumerate(row):
            if cell != ".":
                continue
            cx, cy = x + 0.5, y + 0.5
            distance = math.hypot(cx - px, cy - py)
            if distance < 3.0:
                continue
            # Distance keeps most enemies away from the spawn; the small hashed
            # term stops every level from placing them in the exact same pattern.
            spread = ((x * 37 + y * 53 + int(salt) * 97) % 101) / 101.0
            candidates.append((distance + spread * 1.6, cx, cy))
    candidates.sort(reverse=True)
    if not candidates:
        return ()

    chosen = []
    for index, card in enumerate(cards):
        # Walk through the sorted pool at different strides, rejecting points
        # that would stack cards on top of one another.
        start = (index * 7 + int(salt) * 3) % len(candidates)
        selected = None
        for offset in range(len(candidates)):
            _score, cx, cy = candidates[(start + offset) % len(candidates)]
            if all(math.hypot(cx - ox, cy - oy) >= 1.35 for _c, ox, oy in chosen):
                selected = (str(card), cx, cy)
                break
        if selected is None:
            _score, cx, cy = candidates[start]
            selected = (str(card), cx, cy)
        chosen.append(selected)
    return tuple(chosen)


def _level(name, width, height, player, blocks, cards, theme, salt):
    rows = _build_map(width, height, blocks)
    return {
        "name": str(name),
        "map": rows,
        "player": tuple(player),
        "enemies": _enemy_spawns(rows, player, cards, salt=salt),
        "theme": dict(theme),
    }


# Each level has a distinct layout plus a renderer theme.  Authored art can be
# dropped into assets/dead_mans_hand/levels/level_XX/ as skybox.png, floor.png,
# and wall_1.png / wall_2.png / wall_3.png.  The renderer uses these procedural
# themes when those optional files do not exist.
LEVELS = (
    _level(
        "The Ante", 16, 12, (2.5, 9.5, -0.55),
        (("2", 3, 2, 2, 2), ("3", 9, 3, 3, 2), ("1", 6, 5, 2, 2), ("3", 3, 8, 3, 2), ("2", 11, 8, 2, 2)),
        ("9H", "9S", "JS", "9D", "KH"),
        {"sky_top": (20, 27, 43), "sky_bottom": (65, 75, 94), "floor_near": (22, 21, 20), "floor_far": (63, 55, 45),
         "walls": {"1": (126, 38, 43), "2": (54, 91, 117), "3": (128, 94, 48)}, "wall_style": "boards", "sky_style": "dusk"}, 1,
    ),
    _level(
        "Skull Saloon", 18, 14, (2.5, 11.5, -0.72),
        (("2", 3, 2, 3, 2), ("3", 12, 2, 3, 2), ("1", 6, 5, 2, 3), ("1", 10, 5, 2, 3), ("3", 3, 9, 3, 2), ("2", 12, 9, 3, 2), ("1", 8, 11, 2, 1)),
        ("9C", "9D", "JH", "JS", "QH", "QS", "KC"),
        {"sky_top": (31, 18, 24), "sky_bottom": (113, 61, 48), "floor_near": (25, 16, 14), "floor_far": (83, 51, 33),
         "walls": {"1": (104, 45, 35), "2": (143, 105, 60), "3": (70, 50, 31)}, "wall_style": "saloon", "sky_style": "sunset"}, 2,
    ),
    _level(
        "All In", 18, 14, (2.5, 11.5, -0.55),
        (("2", 2, 2, 3, 2), ("3", 7, 2, 3, 2), ("2", 12, 2, 3, 2), ("1", 5, 5, 2, 2), ("1", 11, 5, 2, 2),
         ("3", 2, 8, 3, 2), ("2", 7, 8, 3, 2), ("3", 12, 8, 3, 2), ("2", 5, 11, 2, 1), ("2", 11, 11, 2, 1)),
        ("8S", "8C", "9H", "9D", "JH", "JS", "QH", "QS", "KH"),
        {"sky_top": (11, 15, 28), "sky_bottom": (38, 47, 69), "floor_near": (15, 17, 19), "floor_far": (48, 50, 52),
         "walls": {"1": (67, 72, 79), "2": (116, 25, 34), "3": (33, 78, 72)}, "wall_style": "steel", "sky_style": "night"}, 3,
    ),
    _level(
        "The Gem", 20, 14, (2.5, 11.5, -0.35),
        (("3", 4, 2, 2, 5), ("2", 8, 2, 5, 2), ("1", 15, 2, 2, 5), ("1", 8, 6, 2, 5), ("3", 12, 8, 5, 2), ("2", 3, 9, 3, 2)),
        ("8H", "9S", "9C", "JH", "JS", "QC", "QH", "KS", "KD", "9D"),
        {"sky_top": (54, 36, 31), "sky_bottom": (155, 105, 66), "floor_near": (44, 31, 22), "floor_far": (112, 83, 52),
         "walls": {"1": (111, 67, 42), "2": (73, 91, 82), "3": (150, 116, 73)}, "wall_style": "brick", "sky_style": "dust"}, 4,
    ),
    _level(
        "Westworld", 20, 15, (2.5, 12.5, -0.62),
        (("1", 4, 2, 4, 2), ("2", 11, 2, 2, 5), ("3", 15, 3, 2, 4), ("3", 4, 6, 3, 2), ("1", 9, 8, 5, 2), ("2", 4, 11, 3, 2), ("1", 16, 10, 2, 3)),
        ("8C", "9H", "9S", "9D", "JC", "JH", "JS", "QD", "QH", "KC", "KS"),
        {"sky_top": (15, 7, 16), "sky_bottom": (100, 30, 42), "floor_near": (20, 16, 18), "floor_far": (70, 42, 43),
         "walls": {"1": (85, 50, 58), "2": (108, 82, 75), "3": (91, 27, 34)}, "wall_style": "brick", "sky_style": "moon"}, 5,
    ),
    _level(
        "O.K. Corral", 20, 16, (2.5, 13.5, -0.50),
        (("3", 3, 2, 2, 4), ("3", 7, 3, 2, 5), ("1", 12, 2, 2, 4), ("2", 16, 3, 2, 5), ("2", 4, 9, 3, 2), ("1", 10, 9, 2, 5), ("3", 14, 11, 3, 2)),
        ("8D", "8S", "9C", "9H", "9S", "JC", "JH", "JS", "QC", "QH", "QS", "KH"),
        {"sky_top": (22, 31, 28), "sky_bottom": (83, 101, 74), "floor_near": (27, 26, 19), "floor_far": (86, 80, 55),
         "walls": {"1": (97, 94, 73), "2": (65, 83, 67), "3": (132, 125, 95)}, "wall_style": "stone", "sky_style": "cloud"}, 6,
    ),
    _level(
        "Blackwater", 22, 16, (2.5, 13.5, -0.40),
        (("3", 4, 2, 2, 6), ("1", 8, 2, 2, 3), ("2", 12, 2, 6, 2), ("1", 16, 5, 2, 5), ("3", 8, 7, 5, 2), ("2", 4, 10, 2, 4), ("1", 10, 11, 6, 2)),
        ("8H", "8S", "9C", "9D", "9H", "JC", "JD", "JH", "JS", "QC", "QD", "QH", "KS"),
        {"sky_top": (8, 11, 14), "sky_bottom": (34, 36, 34), "floor_near": (13, 13, 12), "floor_far": (46, 42, 36),
         "walls": {"1": (67, 58, 47), "2": (49, 54, 58), "3": (105, 78, 48)}, "wall_style": "mine", "sky_style": "night"}, 7,
    ),
    _level(
        "Armadillo", 22, 17, (2.5, 14.5, -0.55),
        (("2", 4, 2, 5, 2), ("3", 12, 2, 5, 2), ("1", 5, 5, 2, 7), ("1", 10, 5, 2, 3), ("1", 15, 5, 2, 7), ("3", 8, 10, 6, 2), ("2", 8, 13, 6, 2)),
        ("8C", "8D", "9C", "9D", "9H", "9S", "JC", "JH", "JS", "QC", "QH", "QS", "KC", "KH"),
        {"sky_top": (20, 10, 29), "sky_bottom": (77, 38, 86), "floor_near": (27, 14, 25), "floor_far": (84, 49, 70),
         "walls": {"1": (91, 42, 87), "2": (155, 123, 58), "3": (50, 92, 100)}, "wall_style": "wallpaper", "sky_style": "city"}, 8,
    ),
    _level(
        "Beecher's Hope", 22, 17, (2.5, 14.5, -0.35),
        (("1", 4, 2, 2, 10), ("2", 8, 2, 2, 5), ("3", 12, 2, 2, 10), ("2", 16, 2, 2, 5), ("1", 8, 9, 2, 5), ("3", 16, 9, 2, 5), ("2", 6, 13, 10, 2)),
        ("8S", "9C", "9D", "9H", "9S", "JC", "JD", "JH", "JS", "QC", "QD", "QH", "QS", "KC", "KS"),
        {"sky_top": (5, 16, 19), "sky_bottom": (32, 68, 70), "floor_near": (12, 19, 19), "floor_far": (42, 66, 61),
         "walls": {"1": (48, 66, 68), "2": (94, 82, 58), "3": (43, 91, 84)}, "wall_style": "rail", "sky_style": "fog"}, 9,
    ),
    _level(
        "Sad Hill Cemetery", 24, 18, (2.5, 15.5, -0.48),
        (("1", 4, 2, 3, 4), ("2", 9, 2, 2, 7), ("3", 13, 2, 2, 7), ("1", 17, 2, 3, 4), ("3", 4, 8, 3, 5), ("2", 17, 8, 3, 5),
         ("1", 9, 11, 2, 4), ("3", 13, 11, 2, 4), ("2", 7, 7, 10, 2), ("1", 7, 15, 10, 1)),
        ("8C", "8D", "8H", "9C", "9D", "9H", "9S", "JC", "JD", "JH", "JS", "QC", "QD", "QH", "QS", "KC", "KH", "KS"),
        {"sky_top": (20, 3, 5), "sky_bottom": (112, 20, 18), "floor_near": (19, 8, 8), "floor_far": (77, 29, 21),
         "walls": {"1": (98, 24, 24), "2": (55, 47, 51), "3": (139, 88, 39)}, "wall_style": "inferno", "sky_style": "storm"}, 10,
    ),
)


def normalize_angle(angle: float) -> float:
    """Return an angle in the [-pi, pi) range."""
    return (float(angle) + math.pi) % math.tau - math.pi


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
