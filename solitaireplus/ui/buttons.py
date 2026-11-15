"""Wooden menu buttons and plain buttons (moved out of main.py)."""
import pygame
from solitaireplus.app.lazy import lazy
assets = lazy("solitaireplus.app.assets")
fonts = lazy("solitaireplus.app.fonts")
window = lazy("solitaireplus.app.window")

# ==================================================
# GENERIC UI DRAWING
# ==================================================

def draw_button(
    rect,
    text,
    selected=False,
    font=None
):
    if font is None:
        font = fonts.option_value_font

    if selected:
        fill_color = (
            80,
            145,
            100
        )

    else:
        fill_color = (
            50,
            110,
            75
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

    label = font.render(
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

def draw_menu_button(
        rect,
        text,
        mouse_pos,
        selected=False,
        font=None
):
    if font is None:
        font = fonts.menu_font

    hovered = False

    if mouse_pos is not None:
        hovered = rect.collidepoint(
            mouse_pos
        )

    if selected:
        image = assets.button_selected

    elif hovered:
        image = assets.button_hover

    else:
        image = assets.button_normal

    scaled_image = pygame.transform.smoothscale(
        image,
        (
            rect.width,
            rect.height
        )
    )

    window.game_surface.blit(
        scaled_image,
        rect.topleft
    )

    label = font.render(
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
