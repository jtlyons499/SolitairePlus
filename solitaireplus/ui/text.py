"""Text helpers: the shared font cache, fitting text into a width and word-wrapping (moved out of main.py)."""
import os
import pygame
from solitaireplus.app.lazy import lazy
window = lazy("solitaireplus.app.window")

# ==================================================
# FONT CACHE
# ==================================================
# Building a pygame font opens and parses the font file, so drawing code must not do it every
# frame (B17). get_font() builds each font once and returns the same object afterwards.
# The fonts are SHARED: never change one (set_bold, set_italic, set_underline, .bold = ...,
# .point_size = ..., ...), or every other user gets the change. Ask get_font for the style.

FONT_CACHE_LIMIT = 256   # far more than the game uses; only a guard against unbounded sizes

_font_cache = {}
_font_cache_flags = {"quit_hooked": False}   # a dict, so no `global` is needed
_UNCACHED = object()


def clear_font_cache():
    """Forget every cached font. Runs on pygame.quit() too: fonts don't survive it."""
    _font_cache.clear()
    _font_cache_flags["quit_hooked"] = False


def _font_name_key(name):
    if name is None or isinstance(name, (str, bytes)):
        return name
    if isinstance(name, os.PathLike):
        return os.fspath(name)
    if isinstance(name, (list, tuple)):   # SysFont also takes a list of names
        return tuple(name)
    return _UNCACHED                      # e.g. a file object: build it every time, as before


def get_font(name, size, bold=False, italic=False, sysfont=False):
    """A shared pygame font for these arguments, built on first use.

    sysfont=False: pygame.font.Font(name, size); name is a font file path, or None for pygame's
    default font. bold/italic switch on pygame's synthetic styles for that cached copy.
    sysfont=True: pygame.font.SysFont(name, size, bold, italic); name is an installed font
    name, a list of names, or None.
    """
    name_key = _font_name_key(name)
    key = (bool(sysfont), name_key, size, type(size), bool(bold), bool(italic))
    if name_key is not _UNCACHED:
        try:
            font = _font_cache.get(key)
        except TypeError:                 # a list holding something unhashable
            name_key = _UNCACHED
        else:
            if font is not None:
                return font

    if sysfont:
        font = pygame.font.SysFont(name, size, bold, italic)
    else:
        font = pygame.font.Font(name, size)
        if bold:
            font.set_bold(True)
        if italic:
            font.set_italic(True)

    if name_key is _UNCACHED:
        return font
    if not _font_cache_flags["quit_hooked"]:
        pygame.register_quit(clear_font_cache)
        _font_cache_flags["quit_hooked"] = True
    if len(_font_cache) >= FONT_CACHE_LIMIT:
        _font_cache.pop(next(iter(_font_cache)))   # drop the oldest
    _font_cache[key] = font
    return font

def draw_wrapped_text_limited(
        text,
        font,
        color,
        rect,
        max_lines,
        line_spacing=2
):

    words = text.split()

    lines = []
    current_line = ""

    for word in words:

        test_line = (
            current_line + " " + word
            if current_line
            else word
        )

        test_width = font.size(
            test_line
        )[0]

        if test_width <= rect.width:

            current_line = test_line

        else:

            if current_line:
                lines.append(
                    current_line
                )

            current_line = word

    if current_line:
        lines.append(
            current_line
        )

    # ----------------------------------------------
    # Limit visible lines
    # ----------------------------------------------

    lines = lines[
        :max_lines
    ]

    # Add ... if text was cut off
    if len(lines) == max_lines:

        displayed_text = " ".join(
            lines
        )

        if len(displayed_text) < len(
            text
        ):

            last_line = lines[
                -1
            ]

            while (
                font.size(
                    last_line + "..."
                )[0]
                > rect.width
                and last_line
            ):

                last_line = (
                    last_line[:-1]
                )

            lines[
                -1
            ] = (
                last_line.rstrip()
                + "..."
            )

    y = rect.y

    for line in lines:

        surface = font.render(
            line,
            True,
            color
        )

        window.game_surface.blit(
            surface,
            (
                rect.x,
                y
            )
        )

        y += (
            font.get_linesize()
            + line_spacing
        )

def draw_wrapped_text(
        text,
        font,
        color,
        rect,
        line_spacing=4
):
    words = text.split()

    lines = []

    current_line = ""

    for word in words:

        test_line = (
            word
            if not current_line
            else current_line
            + " "
            + word
        )

        test_surface = font.render(
            test_line,
            True,
            color
        )

        if (
            test_surface.get_width()
            <= rect.width
        ):
            current_line = (
                test_line
            )

        else:
            if current_line:
                lines.append(
                    current_line
                )

            current_line = (
                word
            )

    if current_line:
        lines.append(
            current_line
        )

    y = rect.y

    for line in lines:

        surface = font.render(
            line,
            True,
            color
        )

        window.game_surface.blit(
            surface,
            (
                rect.x,
                y
            )
        )

        y += (
            surface.get_height()
            + line_spacing
        )

def render_text_fit(
        text,
        font,
        max_width,
        color=(0, 0, 0),
        minimum_size=14
):
    surface = font.render(
        text,
        True,
        color
    )

    if (
        surface.get_width()
        <= max_width
    ):
        return surface

    current_size = (
        font.get_height()
    )

    while current_size > minimum_size:

        current_size -= 1

        smaller_font = get_font(
            None,
            current_size
        )

        surface = smaller_font.render(
            text,
            True,
            color
        )

        if (
            surface.get_width()
            <= max_width
        ):
            return surface

    return surface
