"""Submenu title plaques and darkened submenu backgrounds (moved out of main.py)."""
import pygame
from solitaireplus.games.solitaire.rules import BASE_WIDTH, BASE_HEIGHT
from solitaireplus.app import state
from solitaireplus.app.lazy import lazy
assets = lazy("solitaireplus.app.assets")
fonts = lazy("solitaireplus.app.fonts")
window = lazy("solitaireplus.app.window")
buttons = lazy("solitaireplus.ui.buttons")

def draw_submenu_title(
        text,
        y=55,
        width=360,
        height=72
):
    rect = pygame.Rect(
        BASE_WIDTH // 2 - width // 2,
        y - height // 2,
        width,
        height
    )

    # Wood plaque (scaled once per size, shared: only blit it)
    plaque = buttons.scaled_image(
        assets.button_normal,
        (
            rect.width,
            rect.height
        )
    )

    window.game_surface.blit(
        plaque,
        rect.topleft
    )

    # Dark text shadow
    shadow = fonts.options_title_font.render(
        text,
        True,
        (
            35,
            20,
            10
        )
    )

    shadow_rect = shadow.get_rect(
        center=(
            rect.centerx + 3,
            rect.centery + 3
        )
    )

    window.game_surface.blit(
        shadow,
        shadow_rect
    )

    # Main title
    label = fonts.options_title_font.render(
        text,
        True,
        (
            255,
            255,
            255
        )
    )

    label_rect = label.get_rect(
        center=rect.center
    )

    window.game_surface.blit(
        label,
        label_rect
    )

def draw_submenu_background(
        overlay_alpha=120
):
    window.game_surface.blit(
        assets.menu_background_surfaces[
            state.selected_menu_background
        ],
        (
            0,
            0
        )
    )

    overlay = pygame.Surface(
        (
            BASE_WIDTH,
            BASE_HEIGHT
        ),
        pygame.SRCALPHA
    )

    overlay.fill(
        (
            0,
            0,
            0,
            overlay_alpha
        )
    )

    window.game_surface.blit(
        overlay,
        (
            0,
            0
        )
    )
