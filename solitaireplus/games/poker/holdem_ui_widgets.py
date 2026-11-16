"""Texas Hold'em table UI: translucent panels, buttons and fitted text.

One part of the Hold'em table UI (see holdem_ui.py, which re-exports every name here).
draw_holdem_glossy_button is also used by the multiplayer menus and the Five-O table.
"""
import math

import pygame

from solitaireplus.games.poker.holdem_ui_state import WHITE


def draw_translucent_panel(
        surface,
        rect,
        fill_color,
        border_color=(185, 185, 190),
        border_width=2,
        radius=12
):

    panel = pygame.Surface(
        (
            rect.width,
            rect.height
        ),
        pygame.SRCALPHA
    )

    pygame.draw.rect(
        panel,
        fill_color,
        panel.get_rect(),
        border_radius=radius
    )

    surface.blit(
        panel,
        rect.topleft
    )

    if border_width > 0:

        pygame.draw.rect(
            surface,
            border_color,
            rect,
            border_width,
            border_radius=radius
        )

def draw_modern_button(
        surface,
        rect,
        text,
        mouse_pos,
        font,
        enabled=True,
        accent_color=None
):

    hovered = (
        mouse_pos is not None
        and rect.collidepoint(mouse_pos)
    )

    if not enabled:

        fill_color = (
            65,
            65,
            70
        )

        border_color = (
            100,
            100,
            105
        )

        text_color = (
            155,
            155,
            160
        )

    else:

        if accent_color is not None:

            fill_color = (
                accent_color
                if not hovered
                else (
                    min(255, accent_color[0] + 18),
                    min(255, accent_color[1] + 18),
                    min(255, accent_color[2] + 18),
                )
            )

            border_color = (
                235,
                165,
                165
            )

        elif hovered:

            fill_color = (
                70,
                76,
                84
            )

            border_color = (
                180,
                190,
                200
            )

        else:

            fill_color = (
                45,
                50,
                57
            )

            border_color = (
                120,
                125,
                135
            )

        text_color = WHITE

    draw_translucent_panel(
        surface,
        rect,
        (
            *fill_color,
            235
        ),
        border_color=border_color,
        border_width=2,
        radius=10
    )

    blit_text_fit(
        surface,
        text,
        font,
        text_color,
        rect,
        padding=8
    )

def blit_text_fit(
        surface,
        text,
        font,
        color,
        rect,
        padding=10
):
    text_surface = font.render(
        text,
        True,
        color
    )

    max_width = rect.width - padding * 2

    if text_surface.get_width() > max_width:
        scale = (
            max_width
            / text_surface.get_width()
        )

        new_width = max(
            1,
            int(
                text_surface.get_width()
                * scale
            )
        )

        new_height = max(
            1,
            int(
                text_surface.get_height()
                * scale
            )
        )

        text_surface = pygame.transform.smoothscale(
            text_surface,
            (
                new_width,
                new_height
            )
        )

    text_rect = text_surface.get_rect(
        center=rect.center
    )

    surface.blit(
        text_surface,
        text_rect
    )


def draw_holdem_glossy_button(
        game_surface,
        rect,
        text,
        mouse_pos,
        font,
        enabled=True,
        selected=False,
        danger=False,
        attention=False
):

    hovered = (
        mouse_pos is not None
        and rect.collidepoint(mouse_pos)
    )

    if not enabled:
        base_color = (62, 62, 66)
        border_color = (110, 110, 116)
        text_color = (150, 150, 155)

    elif danger:
        base_color = (205, 48, 48) if hovered else (185, 42, 42)
        border_color = (255, 175, 175)
        text_color = WHITE


    elif selected:

        base_color = (72, 102, 132)

        border_color = (180, 220, 255)

        text_color = WHITE


    elif attention:

        # Soft pulsing notification glow.

        pulse = (
                        pygame.time.get_ticks()
                        % 1200
                ) / 1200.0

        pulse = (
                0.5
                + 0.5
                * math.sin(
            pulse
            * math.pi
            * 2
        )
        )

        base_color = (

            int(105 + 35 * pulse),

            int(82 + 28 * pulse),

            int(32 + 12 * pulse),

        )

        border_color = (

            255,

            int(195 + 45 * pulse),

            80,

        )

        text_color = WHITE

    elif hovered:
        base_color = (80, 88, 96)
        border_color = (185, 190, 195)
        text_color = WHITE

    else:
        base_color = (58, 62, 68)
        border_color = (145, 150, 155)
        text_color = (238, 238, 238)

    button_surface = pygame.Surface(
        (rect.width, rect.height),
        pygame.SRCALPHA
    )

    button_surface.fill((0, 0, 0, 0))

    pygame.draw.rect(
        button_surface,
        (*base_color, 215),
        button_surface.get_rect(),
        border_radius=12
    )

    gloss_rect = pygame.Rect(
        3,
        3,
        rect.width - 6,
        max(
            8,
            rect.height // 2 - 3
        )
    )

    pygame.draw.rect(
        button_surface,
        (255, 255, 255, 28),
        gloss_rect,
        border_radius=10
    )

    pygame.draw.rect(
        button_surface,
        border_color,
        button_surface.get_rect(),
        2,
        border_radius=12
    )

    game_surface.blit(
        button_surface,
        rect.topleft
    )

    text_surface = font.render(
        text,
        True,
        text_color
    )

    text_rect = text_surface.get_rect(
        center=rect.center
    )

    game_surface.blit(
        text_surface,
        text_rect
    )
