"""Free Play / Career choice screen (moved out of legacy.py)."""
from solitaireplus.games.solitaire.rules import BASE_HEIGHT
from solitaireplus.games.solitaire.rules import BASE_WIDTH
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
news_screen = lazy("solitaireplus.career.news_screen")
leaderboard_engine = lazy("solitaireplus.career.leaderboard_engine")
calendar = lazy("solitaireplus.career.calendar")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")


# ==================================================
# PLAY MODE SELECT
# ==================================================

play_free_rect = pygame.Rect(
    0,
    0,
    BASE_WIDTH // 2,
    BASE_HEIGHT
)

play_career_rect = pygame.Rect(
    BASE_WIDTH // 2,
    0,
    BASE_WIDTH // 2,
    BASE_HEIGHT
)

play_return_rect = pygame.Rect(
    BASE_WIDTH // 2 - 90,
    BASE_HEIGHT - 70,
    180,
    46
)

mode_select_back_rect = pygame.Rect(
    533,
    650,
    300,
    55
)


def draw_mode_select():
    # ==================================================
    # Background
    # ==================================================

    window.game_surface.blit(
        state.play_background_image,
        (
            0,
            0
        )
    )

    mouse_pos = state.game_mouse_pos

    if mouse_pos is None:
        mouse_pos = pygame.mouse.get_pos()

    # ==================================================
    # Hover feedback
    # ==================================================

    hover_surface = pygame.Surface(
        (
            BASE_WIDTH // 2,
            BASE_HEIGHT
        ),
        pygame.SRCALPHA
    )

    hover_surface.fill(
        (
            255,
            255,
            255,
            25
        )
    )

    if play_free_rect.collidepoint(
            mouse_pos
    ):
        window.game_surface.blit(
            hover_surface,
            (
                0,
                0
            )
        )

    elif play_career_rect.collidepoint(
            mouse_pos
    ):
        window.game_surface.blit(
            hover_surface,
            (
                BASE_WIDTH // 2,
                0
            )
        )

    # ==================================================
    # Return
    # ==================================================

    buttons.draw_menu_button(
        play_return_rect,
        "Return to Menu",
        state.game_mouse_pos,
        font=fonts.difficulty_detail_font
    )


def handle_event(event):
    """Old main-loop event branch for STATE_MODE_SELECT."""

    if (

            event.type

            == pygame.MOUSEBUTTONDOWN

            and event.button == 1

    ):

        # ==========================================

        # Return

        # ==========================================

        if play_return_rect.collidepoint(

                state.game_mouse_pos

        ):

            sounds.audio.play_sound(

                "button_click"

            )

            state.current_state = state_names.STATE_MENU


        # ==========================================

        # Free Play

        # ==========================================

        elif play_free_rect.collidepoint(
                state.game_mouse_pos
        ):

            sounds.audio.play_sound(
                "button_click"
            )

            state.current_game_mode = "free"
            state.current_state = state_names.STATE_FREE_PLAY_SELECT


        # ==========================================
        # Career
        # ==========================================

        elif play_career_rect.collidepoint(
                state.game_mouse_pos
        ):

            sounds.audio.play_sound(
                "button_click"
            )

            state.current_game_mode = (
                "career"
            )

            calendar.ensure_career_schedule()
            leaderboard_engine.ensure_career_leaderboard()
            news_screen.ensure_career_news()

            state.current_state = state_names.STATE_CAREER_HUB

        elif mode_select_back_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.current_state = state_names.STATE_MENU


def draw():
    """Old draw-chain branch for STATE_MODE_SELECT."""

    draw_mode_select()
