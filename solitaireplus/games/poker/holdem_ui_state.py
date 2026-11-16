"""Texas Hold'em table UI: the shared state, constants, HUD rects, fonts and chip images.

One part of the Hold'em table UI (see holdem_ui.py, which re-exports every name here).
_ui is the one holder of the table UI's module-private caches and animation keys: every
holdem_ui_* module imports this same object, so there are still no 'global' statements.
The log and chat histories and the Quick Chat queue are module lists changed in place,
never rebound, so every module that imports them sees the same list.
"""
from solitaireplus.app import paths
from types import SimpleNamespace

import pygame

from solitaireplus.games.poker.speech import PokerSpeechOverlay


# Module-private caches, animation keys and table UI state. Their starting values are
# set next to the code that uses them (below, and in holdem_ui_pot.py and holdem_ui_cards.py);
# one holder means no 'global' statements.
_ui = SimpleNamespace()


# ==================================================
# ACTIONS
# ==================================================

ACTION_DEAL = "deal"
ACTION_FLOP = "flop"
ACTION_TURN = "turn"
ACTION_RIVER = "river"
ACTION_SHOWDOWN = "showdown"
ACTION_RETURN = "return"
ACTION_FOLD = "fold"
ACTION_CHECK_CALL = "check_call"
ACTION_BET_RAISE = "bet_raise"
ACTION_NEXT_HAND = "next_hand"

# ==================================================
# HOLDEM LOG
# ==================================================

HOLDEM_LOG_RECT = pygame.Rect(
    18,
    610,
    410,
    140
)

# The GAME LOG's text area inside the panel's inner box (12 px in, 48 px down): rows
# start 9 px into the box, 10 px in, are at most 24 px narrower than the box, and end
# 2 px above its bottom edge.
HOLDEM_LOG_TEXT_WIDTH = HOLDEM_LOG_RECT.width - 48
HOLDEM_LOG_TEXT_HEIGHT = HOLDEM_LOG_RECT.height - 69
HOLDEM_LOG_LINE_STEP = 23
# A log line wider than the text area is squashed to fit on one row, exactly as the
# panel always drew it, while that keeps at least 65 % of its size: up to 556 px wide
# at the 17 px log font, which leaves text about 11 px, the smallest size the Draw log
# ever drew. The panel shows three rows, so every line that wraps pushes an older
# line out of the end-of-hand view; this floor keeps showdown and winner lines on one
# row (a long one, 'Mohammed wins $12,345 with Two Pair, Queens and Sevens, 10
# kicker.', squashes to 66 %). Split, side-pot and payout lines, which the panel
# squashed to about 30-50 % and could not be read, wrap onto several rows at full
# size (log_rows).
HOLDEM_LOG_MIN_SQUASH = 0.65

# Kept in solitaireplus/app/state.py: state.holdem_log_scroll.

# ==================================================
# LOAD ASSETS/IMAGES
# ==================================================
_ui.poker_chip_images = None


def get_poker_chip_images():

    if _ui.poker_chip_images is None:

        _ui.poker_chip_images = {
            "black": pygame.image.load(
                str(paths.asset("poker/chip_black.png"))
            ).convert_alpha(),

            "blue": pygame.image.load(
                str(paths.asset("poker/chip_blue.png"))
            ).convert_alpha(),

            "green": pygame.image.load(
                str(paths.asset("poker/chip_green.png"))
            ).convert_alpha(),

            "red": pygame.image.load(
                str(paths.asset("poker/chip_red.png"))
            ).convert_alpha(),

            "yellow": pygame.image.load(
                str(paths.asset("poker/chip_yellow.png"))
            ).convert_alpha(),
        }

    return _ui.poker_chip_images

# ==================================================
# HOLDEM FONTS
# ==================================================

_ui.holdem_fonts = None
_ui.holdem_fonts_quit_hooked = False


def clear_holdem_fonts():
    """Forget the cached fonts; the next get_holdem_fonts() builds them again."""
    _ui.holdem_fonts = None


def _holdem_fonts_quit_hook():
    # Registered with pygame.register_quit: fonts don't survive pygame.quit(), and pygame
    # forgets this hook once it has run, so the next get_holdem_fonts() registers it again.
    # Only this hook clears the flag; a direct clear_holdem_fonts() call leaves the hook in place.
    _ui.holdem_fonts_quit_hooked = False
    clear_holdem_fonts()


def get_holdem_fonts():

    if _ui.holdem_fonts is None:

        if not pygame.font.get_init():
            pygame.font.init()

        # pygame forgets its quit hooks once they have run, so hook again after each quit.
        if not _ui.holdem_fonts_quit_hooked:
            pygame.register_quit(_holdem_fonts_quit_hook)
            _ui.holdem_fonts_quit_hooked = True

        _ui.holdem_fonts = {
            "title": pygame.font.SysFont(
                "cambria",
                31,
                bold=True
            ),

            "name": pygame.font.SysFont(
                "cambria",
                20,
                bold=True
            ),

            "small": pygame.font.SysFont(
                "cambria",
                17,
                bold=True
            ),

            "tiny": pygame.font.SysFont(
                "cambria",
                15,
                bold=True
            ),
        }

    return _ui.holdem_fonts

# ==================================================
# COLORS
# ==================================================

WHITE = (
    255,
    255,
    255
)

BLACK = (
    20,
    20,
    20
)

TABLE_GREEN = (
    30,
    105,
    55
)

TABLE_EDGE = (
    95,
    65,
    35
)

PANEL_DARK = (
    20,
    35,
    25
)


# ==================================================
# HOLDEM HUD RECTS
# ==================================================

holdem_next_hand_rect = pygame.Rect(
    1010,
    626,
    250,
    42
)

holdem_action_panel_rect = pygame.Rect(
    925,
    610,
    420,
    140
)

# Main poker actions
holdem_fold_rect = pygame.Rect(
    942,
    622,
    112,
    40
)

holdem_call_rect = pygame.Rect(
    1064,
    622,
    132,
    40
)

holdem_raise_rect = pygame.Rect(
    1206,
    622,
    122,
    40
)

# ==================================================
# BET SLIDER STATE
# ==================================================

# Kept in solitaireplus/app/state.py: state.holdem_bet_fraction, state.holdem_bet_slider_dragging,
# state.holdem_manual_bet_text, state.holdem_manual_bet_active.

# Raise slider
holdem_slider_rect = pygame.Rect(
    942,
    683,
    250,
    14
)

# Direct numeric bet / raise-to entry.
holdem_manual_bet_rect = pygame.Rect(
    1202,
    674,
    126,
    30
)

# Raise shortcuts
holdem_min_rect = pygame.Rect(
    942,
    708,
    68,
    28
)

holdem_half_rect = pygame.Rect(
    1018,
    708,
    68,
    28
)

holdem_pot_rect = pygame.Rect(
    1094,
    708,
    68,
    28
)

holdem_max_rect = pygame.Rect(
    1170,
    708,
    68,
    28
)

# Top-right utility buttons
holdem_options_rect = pygame.Rect(
    1180,
    20,
    90,
    38
)

holdem_exit_rect = pygame.Rect(
    1280,
    20,
    68,
    38
)

# ==================================================
# HOLDEM LOG STATE
# ==================================================

holdem_log_history = []

# Kept in solitaireplus/app/state.py: state.holdem_log_scroll.

holdem_chat_history = []
_holdem_speech_overlay = PokerSpeechOverlay()

# Kept in solitaireplus/app/state.py: state.holdem_active_tab, state.holdem_chat_scroll,
# state.holdem_chat_unread, state.holdem_quick_chat_open, state.holdem_quick_chat_target_mode.

# Player quick-chat panel. The active game reference is refreshed every draw,
# keeping the existing main.py click path unchanged.
holdem_quick_chat_pending = []
_ui.holdem_active_game = None

_ui.holdem_last_stage = None
_ui.holdem_last_result = None
