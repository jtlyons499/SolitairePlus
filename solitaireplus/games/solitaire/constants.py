"""Solitaire table constants: base window size, colours, tableau layout and animation timings.

Kept where rules.py defined them; rules.py re-exports them, so screens keep importing
BASE_WIDTH / BASE_HEIGHT from solitaireplus.games.solitaire.rules.
"""

# ----------------------------
# Window settings
# ----------------------------

BASE_WIDTH = 1366
BASE_HEIGHT = 768


# ----------------------------
# Colors
# ----------------------------

TABLE_GREEN = (30, 110, 60)
PLACEHOLDER = (255, 255, 255)
OUTLINE = (200, 200, 200)

CARD_BACK = (40, 60, 150)


# ----------------------------
# Tableau layout
# ----------------------------

START_X = 65
START_Y = 235

SPACING_X = 185

FACE_DOWN_SPACING = 30
FACE_UP_SPACING = 48

FLIP_DURATION_MS = 220
HINT_DURATION_MS = 2200

VICTORY_DURATION_MS = 6500
VICTORY_CARD_DELAY_MS = 85

VICTORY_GRAVITY = 0.32
VICTORY_BOUNCE = -0.72
