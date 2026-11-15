"""The game window: the fixed 1366x768 game surface, window size, fullscreen, mouse mapping and
presenting each frame (moved out of main.py)."""
import pygame
from solitaireplus.games.solitaire.rules import BASE_WIDTH, BASE_HEIGHT
from solitaireplus.app.settings import DEFAULT_WINDOW_SIZE
from solitaireplus.app import state
from solitaireplus.app.lazy import lazy
cursors = lazy("solitaireplus.ui.cursors")

# ==================================================
# DISPLAY
# ==================================================

FPS = 60

state.WINDOW_WIDTH, state.WINDOW_HEIGHT = DEFAULT_WINDOW_SIZE

# Remember the user's normal window size so fullscreen can
# return to it cleanly. Fullscreen uses the desktop size.
state.WINDOWED_WIDTH, state.WINDOWED_HEIGHT = DEFAULT_WINDOW_SIZE

state.screen = pygame.display.set_mode(
    (
        state.WINDOW_WIDTH,
        state.WINDOW_HEIGHT
    )
)

pygame.display.set_caption(
    "Solitaire"
)

# Everything in the game is designed at
# 1366 x 768 regardless of actual window size.
game_surface = pygame.Surface(
    (
        BASE_WIDTH,
        BASE_HEIGHT
    )
)

clock = pygame.time.Clock()

# ==================================================
# WINDOW HELPERS
# ==================================================

def invalidate_scaled_surface_cache():
    state.scaled_surface_cache = None


def set_window_size(width, height):

    state.WINDOWED_WIDTH = int(width)
    state.WINDOWED_HEIGHT = int(height)

    # Choosing a window size while fullscreen is active
    # returns the game to a normal window at that size.
    state.fullscreen_enabled = False

    state.WINDOW_WIDTH = state.WINDOWED_WIDTH
    state.WINDOW_HEIGHT = state.WINDOWED_HEIGHT

    state.screen = pygame.display.set_mode(
        (
            state.WINDOW_WIDTH,
            state.WINDOW_HEIGHT
        )
    )

    invalidate_scaled_surface_cache()
    cursors.apply_selected_cursor()


def set_fullscreen_enabled(enabled):

    enabled = bool(enabled)

    if enabled == state.fullscreen_enabled:
        return

    if enabled:
        state.WINDOWED_WIDTH = state.WINDOW_WIDTH
        state.WINDOWED_HEIGHT = state.WINDOW_HEIGHT

        state.screen = pygame.display.set_mode(
            (0, 0),
            pygame.FULLSCREEN
        )

        state.WINDOW_WIDTH, state.WINDOW_HEIGHT = (
            state.screen.get_size()
        )

        state.fullscreen_enabled = True

    else:
        state.WINDOW_WIDTH = state.WINDOWED_WIDTH
        state.WINDOW_HEIGHT = state.WINDOWED_HEIGHT

        state.screen = pygame.display.set_mode(
            (
                state.WINDOW_WIDTH,
                state.WINDOW_HEIGHT
            )
        )

        state.fullscreen_enabled = False

    invalidate_scaled_surface_cache()
    cursors.apply_selected_cursor()


def window_to_game_coords(pos):
    x, y = pos

    game_x = int(
        x
        * BASE_WIDTH
        / state.WINDOW_WIDTH
    )

    game_y = int(
        y
        * BASE_HEIGHT
        / state.WINDOW_HEIGHT
    )

    return (
        game_x,
        game_y
    )
def present():
    """Scale the 1366x768 game surface into the window and show the frame."""

    # ----------------------------------------------
    # Scale internal 1366x768 image
    # to the selected actual window size.
    # ----------------------------------------------

    if (
            state.WINDOW_WIDTH == BASE_WIDTH
            and state.WINDOW_HEIGHT == BASE_HEIGHT
    ):
        state.screen.blit(
            game_surface,
            (0, 0)
        )

    else:
        if (
                state.scaled_surface_cache is None
                or state.scaled_surface_cache.get_size()
                != (state.WINDOW_WIDTH, state.WINDOW_HEIGHT)
        ):
            state.scaled_surface_cache = pygame.Surface(
                (
                    state.WINDOW_WIDTH,
                    state.WINDOW_HEIGHT
                )
            ).convert()

        # Keep the cached destination surface from the
        # performance pass, but use filtered scaling again.
        # Plain transform.scale() made the entire 1366x768
        # frame, especially text, visibly blurry/blocky when
        # enlarged to 1920x1080 or 2560x1440.
        pygame.transform.smoothscale(
            game_surface,
            (
                state.WINDOW_WIDTH,
                state.WINDOW_HEIGHT
            ),
            state.scaled_surface_cache
        )

        state.screen.blit(
            state.scaled_surface_cache,
            (0, 0)
        )

    # ----------------------------
    # Software cursor fallback
    # ----------------------------

    if (
            state.software_cursor_fallback
            and state.cursor_image is not None
    ):
        mouse_x, mouse_y = (
            pygame.mouse.get_pos()
        )

        state.screen.blit(
            state.cursor_image,
            (
                mouse_x,
                mouse_y
            )
        )

    pygame.display.flip()
