"""The slowly drifting main-menu background (moved out of main.py)."""
import math
import pygame
from solitaireplus.games.solitaire.rules import BASE_WIDTH, BASE_HEIGHT
from solitaireplus.app import state
from solitaireplus.app.lazy import lazy
assets = lazy("solitaireplus.app.assets")
window = lazy("solitaireplus.app.window")

# ==================================================
# MENU BACKGROUND DRIFT
# ==================================================

MENU_DRIFT_SCALE = 3
MENU_DRIFT_MARGIN = 35

MENU_DRIFT_X = 20
MENU_DRIFT_Y = 12

# Seconds for one full back-and-forth cycle.
MENU_DRIFT_PERIOD_X = 50.0
MENU_DRIFT_PERIOD_Y = 80.0

def draw_drifting_menu_background():

    background = assets.menu_background_drift_cache.get(
        state.selected_menu_background, assets.menu_background_surfaces[state.selected_menu_background],
        (assets.drift_width * MENU_DRIFT_SCALE, assets.drift_height * MENU_DRIFT_SCALE)
    )

    time_sec = (
        pygame.time.get_ticks()
        / 1000.0
    )

    # ----------------------------
    # Extremely slow drift
    # ----------------------------

    x_phase = (
        time_sec
        / MENU_DRIFT_PERIOD_X
        * math.tau
    )

    y_phase = (
        time_sec
        / MENU_DRIFT_PERIOD_Y
        * math.tau
    )

    drift_x = (
        math.sin(x_phase)
        * MENU_DRIFT_X
    )

    drift_y = (
        math.sin(
            y_phase + 1.3
        )
        * MENU_DRIFT_Y
    )

    # Convert movement into the supersampled drift space.
    # At 3x, one source-pixel step becomes one third of a
    # logical game pixel after the downsample.
    draw_x = round(
        (
            -MENU_DRIFT_MARGIN
            + drift_x
        )
        * MENU_DRIFT_SCALE
    )

    draw_y = round(
        (
            -MENU_DRIFT_MARGIN
            + drift_y
        )
        * MENU_DRIFT_SCALE
    )

    assets.menu_drift_render_surface.blit(
        background,
        (
            draw_x,
            draw_y
        )
    )

    # Downsample only the drifting background. UI/text is
    # drawn afterward at the normal 1366x768 design size.
    pygame.transform.smoothscale(
        assets.menu_drift_render_surface,
        (
            BASE_WIDTH,
            BASE_HEIGHT
        ),
        window.game_surface
    )
