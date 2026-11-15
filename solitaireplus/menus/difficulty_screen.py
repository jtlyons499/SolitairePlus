"""Solitaire difficulty screen (moved out of legacy.py)."""
from solitaireplus.games.solitaire.rules import BASE_WIDTH
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")


difficulty_easy_rect = pygame.Rect(
    283,
    155,
    800,
    80
)

difficulty_normal_rect = pygame.Rect(
    283,
    250,
    800,
    80
)

difficulty_hard_rect = pygame.Rect(
    283,
    345,
    800,
    80
)

difficulty_very_hard_rect = pygame.Rect(
    283,
    440,
    800,
    80
)

difficulty_extreme_rect = pygame.Rect(
    283,
    535,
    800,
    80
)

difficulty_back_rect = pygame.Rect(
    533,
    665,
    300,
    50
)

# ==================================================
# DIFFICULTY SELECT
# ==================================================

def draw_difficulty_screen():

    window.game_surface.fill(
        (
            20,
            70,
            45
        )
    )

    title = fonts.options_title_font.render(
        "SELECT DIFFICULTY",
        True,
        (
            255,
            255,
            255
        )
    )

    title_rect = title.get_rect(
        center=(
            BASE_WIDTH // 2,
            90
        )
    )

    window.game_surface.blit(
        title,
        title_rect
    )

    difficulty_buttons = [
        (
            difficulty_easy_rect,
            "Easy",
            "0.70x rewards",
            "Unlimited stock  |  Unlimited hints  |  Unlimited undo  |  Shuffling"
        ),

        (
            difficulty_normal_rect,
            "Normal",
            "1.00x rewards",
            "Unlimited stock  |  Unlimited hints  |  Unlimited undo"
        ),

        (
            difficulty_hard_rect,
            "Hard",
            "1.25x rewards",
            "10 stock passes  |  15 hints  |  Unlimited undo"
        ),

        (
            difficulty_very_hard_rect,
            "Very Hard",
            "1.50x rewards",
            "8 stock passes  |  No hints  |  20-move undo history"
        ),

        (
            difficulty_extreme_rect,
            "Impossible",
            "1.85x rewards",
            "3 stock passes  |  No hints  |  5-move undo history"
        ),
    ]

    for (
            rect,
            name,
            reward_text,
            description
    ) in difficulty_buttons:
        hovered = rect.collidepoint(
            state.menu_mouse_pos
        )

        fill_color = (
            (80, 145, 100)
            if hovered
            else (50, 110, 75)
        )

        pygame.draw.rect(
            window.game_surface,
            fill_color,
            rect
        )

        pygame.draw.rect(
            window.game_surface,
            (
                255,
                255,
                255
            ),
            rect,
            2
        )

        # ------------------------
        # Difficulty name
        # ------------------------

        name_surface = fonts.option_label_font.render(
            name,
            True,
            (
                255,
                255,
                255
            )
        )

        window.game_surface.blit(
            name_surface,
            (
                rect.x + 20,
                rect.y + 10
            )
        )

        # ------------------------
        # Reward multiplier
        # ------------------------

        reward_surface = (
            fonts.option_value_font.render(
                reward_text,
                True,
                (
                    255,
                    215,
                    0
                )
            )
        )

        reward_rect = (
            reward_surface.get_rect(
                right=rect.right - 20,
                centery=rect.y + 25
            )
        )

        window.game_surface.blit(
            reward_surface,
            reward_rect
        )

        # ------------------------
        # Rules
        # ------------------------

        description_surface = (
            fonts.difficulty_detail_font.render(
                description,
                True,
                (
                    210,
                    210,
                    210
                )
            )
        )

        window.game_surface.blit(
            description_surface,
            (
                rect.x + 20,
                rect.y + 49
            )
        )

    buttons.draw_button(
        difficulty_back_rect,
        "Back"
    )


def handle_event(event):
    """Old main-loop event branch for STATE_DIFFICULTY."""

    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
    ):

        selected_difficulty = None

        if difficulty_easy_rect.collidepoint(
                state.game_mouse_pos
        ):
            selected_difficulty = "easy"

        elif difficulty_normal_rect.collidepoint(
                state.game_mouse_pos
        ):
            selected_difficulty = "normal"

        elif difficulty_hard_rect.collidepoint(
                state.game_mouse_pos
        ):
            selected_difficulty = "hard"

        elif difficulty_very_hard_rect.collidepoint(
                state.game_mouse_pos
        ):
            selected_difficulty = (
                "very_hard"
            )

        elif difficulty_extreme_rect.collidepoint(
                state.game_mouse_pos
        ):
            selected_difficulty = (
                "extreme"
            )


        elif difficulty_back_rect.collidepoint(

                state.game_mouse_pos

        ):

            sounds.audio.play_sound(

                "button_click"

            )

            if state.current_game_mode == "career":

                state.current_state = state_names.STATE_CAREER_HUB


            else:

                if state.current_game_mode == "free":
                    legacy.finish_free_play_sandbox()
                    state.current_state = state_names.STATE_FREE_PLAY_SELECT
                else:
                    state.current_state = state_names.STATE_MODE_SELECT

        if selected_difficulty is not None:
            sounds.audio.play_sound(
                "button_click"
            )

            legacy.game.set_difficulty(
                selected_difficulty
            )


            legacy.game.new_game()

            state.current_state = state_names.STATE_PLAYING


def draw():
    """Old draw-chain branch for STATE_DIFFICULTY."""

    draw_difficulty_screen()
