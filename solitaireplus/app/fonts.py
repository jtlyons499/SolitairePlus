"""Fonts created at start-up and shared by many screens (moved out of main.py)."""
import pygame
from solitaireplus.app import state

# ==================================================
# FONTS
# ==================================================

menu_title_font = pygame.font.SysFont(
    None,
    72
)

old_english_names = [
    "Old English Text MT",
    "OldEnglishTextMT",
    "Old English Text",
    "oldenglishtextmt",
]

for font_name in old_english_names:

    state.courrier_font_path = (
        pygame.font.match_font(
            font_name
        )
    )

    if state.courrier_font_path:
        break


if state.courrier_font_path:

    print(
        "Loaded Courrier font:",
        state.courrier_font_path
    )

    state.courrier_title_font = (
        pygame.font.Font(
            state.courrier_font_path,
            58
        )
    )

else:

    print(
        "Old English Text MT not found. "
        "Using fallback."
    )

    state.courrier_title_font = (
        menu_title_font
    )

menu_font = pygame.font.SysFont(
    None,
    42
)

options_title_font = pygame.font.SysFont(
    None,
    60
)

option_label_font = pygame.font.SysFont(
    None,
    34
)

option_value_font = pygame.font.SysFont(
    None,
    27
)

difficulty_detail_font = pygame.font.SysFont(
    None,
    24
)

arcade_button_badge_font = pygame.font.SysFont(
    None,
    20,
    bold=True,
)

tooltip_font = pygame.font.SysFont(
    None,
    22
)

# Blackjack deliberately uses its own typography rather than the default UI
# font so the table has a more distinct casino identity.
blackjack_title_font = pygame.font.SysFont(
    "georgia",
    46,
    bold=True
)
blackjack_heading_font = pygame.font.SysFont(
    "cambria",
    27,
    bold=True
)
blackjack_body_font = pygame.font.SysFont(
    "cambria",
    21
)
blackjack_small_font = pygame.font.SysFont(
    "cambria",
    17
)


ui_small_font = pygame.font.SysFont(
    None,
    24
)

leaderboard_tiny_font = pygame.font.SysFont(
    None,
    16
)

score_four_score_font = pygame.font.Font(
    None,
    36
)

score_four_round_font = pygame.font.Font(
    None,
    26
)

score_four_npc_font = pygame.font.Font(
    None,
    30
)
