"""Text helpers: fitting text into a width and word-wrapping (moved out of main.py)."""
import pygame
from solitaireplus.app.lazy import lazy
window = lazy("solitaireplus.app.window")

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

        smaller_font = pygame.font.Font(
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
