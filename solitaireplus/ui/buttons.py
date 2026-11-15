"""Wooden menu buttons and plain buttons (moved out of main.py)."""
import pygame
from solitaireplus.app.lazy import lazy
assets = lazy("solitaireplus.app.assets")
fonts = lazy("solitaireplus.app.fonts")
window = lazy("solitaireplus.app.window")

# ==================================================
# SCALED IMAGE CACHE
# ==================================================
# Menu buttons and submenu plaques used to smoothscale their art on every draw (B17).
# scaled_image() scales each image once per size. An entry is keyed by (id(image), size) and
# keeps the image itself: while the entry exists that id can't be reused by another image, and
# a hit is only accepted for that same image object. The result is SHARED: blit it, never draw
# on it. (Drawing on a source image after scaling it would need clear_scaled_images().)

SCALED_IMAGE_LIMIT = 128   # buttons use a handful of sizes; only a guard against unbounded sizes

_scaled_images = {}


def clear_scaled_images():
    _scaled_images.clear()


def scaled_image(image, size):
    """pygame.transform.smoothscale(image, size), computed once per image and size."""
    key = (id(image), tuple(size))
    entry = _scaled_images.get(key)
    if entry is not None and entry[0] is image:
        return entry[1]
    scaled = pygame.transform.smoothscale(image, size)
    if len(_scaled_images) >= SCALED_IMAGE_LIMIT:
        _scaled_images.pop(next(iter(_scaled_images)))   # drop the oldest
    _scaled_images[key] = (image, scaled)
    return scaled

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

    button_image = scaled_image(
        image,
        (
            rect.width,
            rect.height
        )
    )

    window.game_surface.blit(
        button_image,
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
