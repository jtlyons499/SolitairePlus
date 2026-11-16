"""Texas Hold'em table UI: the buy-in screen and the Options overlay.

One part of the Hold'em table UI (see holdem_ui.py, which re-exports every name here).
Also the table settings (Table Speed, auto deal, table chat, chat pop-ups) and the delays
from the Table Speed that every poker table uses. The settings live in
solitaireplus/app/state.py.
"""
from solitaireplus.app import state

import pygame

from solitaireplus.games.poker.speech import (
    is_poker_chat_popups_enabled,
    set_poker_chat_popups_enabled,
)
from solitaireplus.games.poker.holdem_ui_state import WHITE, get_holdem_fonts
from solitaireplus.games.poker.holdem_ui_widgets import draw_modern_button, draw_translucent_panel


# ==================================================
# HOLDEM OPTIONS STATE
# ==================================================

# Kept in solitaireplus/app/state.py: state.holdem_options_open, state.holdem_table_speed,
# state.holdem_auto_deal_enabled, state.holdem_table_chat_enabled.


# ==================================================
# HOLDEM OPTIONS RECTS
# ==================================================

holdem_options_panel_rect = pygame.Rect(
    438,
    185,
    490,
    430
)

holdem_options_close_rect = pygame.Rect(
    842,
    220,
    66,
    34
)

# Table speed
holdem_speed_slow_rect = pygame.Rect(
    515,
    325,
    110,
    38
)

holdem_speed_normal_rect = pygame.Rect(
    628,
    325,
    110,
    38
)

holdem_speed_fast_rect = pygame.Rect(
    741,
    325,
    110,
    38
)

# Auto deal
holdem_auto_deal_toggle_rect = pygame.Rect(
    707,
    406,
    144,
    38
)

# Table chat
holdem_chat_toggle_rect = pygame.Rect(
    707,
    468,
    144,
    38
)

# Table chat pop-ups
holdem_chat_popups_toggle_rect = pygame.Rect(
    707,
    530,
    144,
    38
)

# More UI
# ==================================================
# HOLDEM BUY-IN RECTS
# ==================================================

holdem_buy_in_panel_rect = pygame.Rect(
    283,
    180,
    800,
    410
)

holdem_buy_in_25_rect = pygame.Rect(
    318,
    330,
    165,
    100
)

holdem_buy_in_50_rect = pygame.Rect(
    506,
    330,
    165,
    100
)

holdem_buy_in_75_rect = pygame.Rect(
    694,
    330,
    165,
    100
)

holdem_buy_in_max_rect = pygame.Rect(
    882,
    330,
    165,
    100
)

holdem_buy_in_back_rect = pygame.Rect(
    558,
    505,
    250,
    44
)

# ==================================================
# HOLDEM BUY-IN HELPERS
# ==================================================

def get_holdem_buy_in_amounts(
        career_cash
):

    career_cash = max(
        0,
        int(career_cash)
    )

    return {
        "25": int(
            career_cash * 0.25
        ),

        "50": int(
            career_cash * 0.50
        ),

        "75": int(
            career_cash * 0.75
        ),

        "max": career_cash,
    }


def get_texas_holdem_buy_in_action(
        mouse_pos,
        career_cash,
        minimum_buy_in=100
):

    if mouse_pos is None:
        return None

    if holdem_buy_in_back_rect.collidepoint(
            mouse_pos
    ):

        return (
            "back",
            None
        )

    amounts = (
        get_holdem_buy_in_amounts(
            career_cash
        )
    )

    choices = (
        (
            holdem_buy_in_25_rect,
            amounts["25"]
        ),
        (
            holdem_buy_in_50_rect,
            amounts["50"]
        ),
        (
            holdem_buy_in_75_rect,
            amounts["75"]
        ),
        (
            holdem_buy_in_max_rect,
            amounts["max"]
        ),
    )

    for rect, amount in choices:

        if (
                rect.collidepoint(
                    mouse_pos
                )
                and amount
                >= minimum_buy_in
        ):

            return (
                "buy_in",
                amount
            )

    return None

# ==================================================
# HOLDEM OPTIONS HELPERS
# ==================================================

def is_holdem_options_open():

    return state.holdem_options_open


def toggle_holdem_options():

    state.holdem_options_open = (
        not state.holdem_options_open
    )


def close_holdem_options():

    state.holdem_options_open = False


def is_holdem_auto_deal_enabled():

    return state.holdem_auto_deal_enabled


def is_holdem_table_chat_enabled():

    return state.holdem_table_chat_enabled


def is_holdem_table_chat_popups_enabled():

    return is_poker_chat_popups_enabled()


def get_holdem_npc_delay(speed=None):

    # speed: "slow", "normal" or "fast"; None means the table speed in state.
    delays = {
        "slow": 1800,
        "normal": 1200,
        "fast": 600,
    }

    return delays.get(
        state.holdem_table_speed if speed is None else speed,
        1200
    )


def get_holdem_street_delay(speed=None):

    # Keep enough time for the chip sweep animation
    # to finish before the next street appears.
    # speed: as get_holdem_npc_delay.
    delays = {
        "slow": 1700,
        "normal": 1200,
        "fast": 950,
    }

    return delays.get(
        state.holdem_table_speed if speed is None else speed,
        1200
    )


def get_holdem_next_hand_delay(speed=None):

    # Auto-deal countdown itself stays reasonably
    # relaxed, but fast mode trims it somewhat.
    # speed: as get_holdem_npc_delay.
    delays = {
        "slow": 18000,
        "normal": 15000,
        "fast": 9000,
    }

    return delays.get(
        state.holdem_table_speed if speed is None else speed,
        15000
    )


def handle_holdem_options_click(
        mouse_pos
):

    if not state.holdem_options_open:
        return False

    if mouse_pos is None:
        return False

    # ==================================================
    # Close
    # ==================================================

    if holdem_options_close_rect.collidepoint(
            mouse_pos
    ):

        state.holdem_options_open = False

        return True

    # ==================================================
    # Speed
    # ==================================================

    if holdem_speed_slow_rect.collidepoint(
            mouse_pos
    ):

        state.holdem_table_speed = "slow"

        return True

    if holdem_speed_normal_rect.collidepoint(
            mouse_pos
    ):

        state.holdem_table_speed = "normal"

        return True

    if holdem_speed_fast_rect.collidepoint(
            mouse_pos
    ):

        state.holdem_table_speed = "fast"

        return True

    # ==================================================
    # Auto deal
    # ==================================================

    if holdem_auto_deal_toggle_rect.collidepoint(
            mouse_pos
    ):

        state.holdem_auto_deal_enabled = (
            not state.holdem_auto_deal_enabled
        )

        return True

    # ==================================================
    # Table chat
    # ==================================================

    if holdem_chat_toggle_rect.collidepoint(
            mouse_pos
    ):

        state.holdem_table_chat_enabled = (
            not state.holdem_table_chat_enabled
        )

        return True

    if (
            state.holdem_table_chat_enabled
            and holdem_chat_popups_toggle_rect.collidepoint(mouse_pos)
    ):
        set_poker_chat_popups_enabled(
            not is_poker_chat_popups_enabled()
        )
        return True

    return False


# ==================================================
# DRAW HOLDEM BUY-IN
# ==================================================
def draw_texas_holdem_buy_in(
        game_surface,
        mouse_pos,
        career_cash,
        draw_submenu_background,
        minimum_buy_in=100
):

    draw_submenu_background(
        overlay_alpha=125
    )

    holdem_fonts = (
        get_holdem_fonts()
    )

    title_font = (
        holdem_fonts["title"]
    )

    name_font = (
        holdem_fonts["name"]
    )

    small_font = (
        holdem_fonts["small"]
    )

    # ==================================================
    # Panel
    # ==================================================

    draw_translucent_panel(
        game_surface,
        holdem_buy_in_panel_rect,
        (
            10,
            18,
            18,
            245
        ),
        border_color=(
            185,
            190,
            195
        ),
        border_width=2,
        radius=16
    )

    # ==================================================
    # Title
    # ==================================================

    title_surface = (
        title_font.render(
            "TEXAS HOLD'EM BUY-IN",
            True,
            WHITE
        )
    )

    title_rect = (
        title_surface.get_rect(
            center=(
                holdem_buy_in_panel_rect.centerx,
                225
            )
        )
    )

    game_surface.blit(
        title_surface,
        title_rect
    )

    eligible = small_font.render('Rated session: complete at least 1 hand, then cash out', True, (217, 231, 228))
    game_surface.blit(eligible, eligible.get_rect(center=(683, 251)))

    # ==================================================
    # Career cash
    # ==================================================

    cash_surface = (
        name_font.render(
            (
                f"Career Cash: "
                f"${career_cash:,}"
            ),
            True,
            (
                235,
                240,
                235
            )
        )
    )

    cash_rect = (
        cash_surface.get_rect(
            center=(
                holdem_buy_in_panel_rect.centerx,
                275
            )
        )
    )

    game_surface.blit(
        cash_surface,
        cash_rect
    )

    # ==================================================
    # Buy-in choices
    # ==================================================

    amounts = (
        get_holdem_buy_in_amounts(
            career_cash
        )
    )

    choices = (
        (
            holdem_buy_in_25_rect,
            "25%",
            amounts["25"]
        ),
        (
            holdem_buy_in_50_rect,
            "50%",
            amounts["50"]
        ),
        (
            holdem_buy_in_75_rect,
            "75%",
            amounts["75"]
        ),
        (
            holdem_buy_in_max_rect,
            "MAX",
            amounts["max"]
        ),
    )

    for (
            rect,
            label,
            amount
    ) in choices:

        enabled = (
            amount
            >= minimum_buy_in
        )

        hovered = (
            enabled
            and mouse_pos is not None
            and rect.collidepoint(
                mouse_pos
            )
        )

        if enabled:

            fill_color = (
                (
                    55,
                    105,
                    72,
                    245
                )
                if hovered
                else (
                    32,
                    72,
                    48,
                    245
                )
            )

            border_color = (
                (
                    230,
                    210,
                    110
                )
                if hovered
                else (
                    145,
                    165,
                    150
                )
            )

            text_color = WHITE

        else:

            fill_color = (
                45,
                45,
                48,
                225
            )

            border_color = (
                85,
                85,
                90
            )

            text_color = (
                140,
                140,
                145
            )

        draw_translucent_panel(
            game_surface,
            rect,
            fill_color,
            border_color=border_color,
            border_width=2,
            radius=12
        )

        label_surface = (
            name_font.render(
                label,
                True,
                text_color
            )
        )

        label_rect = (
            label_surface.get_rect(
                center=(
                    rect.centerx,
                    rect.y + 31
                )
            )
        )

        game_surface.blit(
            label_surface,
            label_rect
        )

        amount_surface = (
            small_font.render(
                f"${amount:,}",
                True,
                text_color
            )
        )

        amount_rect = (
            amount_surface.get_rect(
                center=(
                    rect.centerx,
                    rect.y + 69
                )
            )
        )

        game_surface.blit(
            amount_surface,
            amount_rect
        )

    # ==================================================
    # Explanation
    # ==================================================

    info_surface = (
        small_font.render(
            (
                "Unused cash stays in your "
                "Career wallet. Opponents "
                "begin with the same stack."
            ),
            True,
            (
                190,
                195,
                195
            )
        )
    )

    info_rect = (
        info_surface.get_rect(
            center=(
                holdem_buy_in_panel_rect.centerx,
                466
            )
        )
    )

    game_surface.blit(
        info_surface,
        info_rect
    )

    # ==================================================
    # Insufficient cash warning
    # ==================================================

    if career_cash < minimum_buy_in:

        warning_surface = (
            small_font.render(
                (
                    f"At least "
                    f"${minimum_buy_in:,} "
                    f"is required to play."
                ),
                True,
                (
                    235,
                    135,
                    135
                )
            )
        )

        warning_rect = (
            warning_surface.get_rect(
                center=(
                    holdem_buy_in_panel_rect.centerx,
                    495
                )
            )
        )

        game_surface.blit(
            warning_surface,
            warning_rect
        )

    # ==================================================
    # Back
    # ==================================================

    draw_modern_button(
        game_surface,
        holdem_buy_in_back_rect,
        "BACK",
        mouse_pos,
        small_font,
        enabled=True
    )


# ==================================================
# DRAW HOLDEM OPTIONS OVERLAY
# ==================================================

def draw_holdem_options_overlay(
        surface,
        mouse_pos
):

    if not state.holdem_options_open:
        return

    holdem_fonts = (
        get_holdem_fonts()
    )

    title_font = (
        holdem_fonts["title"]
    )

    name_font = (
        holdem_fonts["name"]
    )

    small_font = (
        holdem_fonts["small"]
    )

    # ==================================================
    # Dim table behind overlay
    # ==================================================

    dim_surface = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA
    )

    dim_surface.fill(
        (
            0,
            0,
            0,
            125
        )
    )

    surface.blit(
        dim_surface,
        (0, 0)
    )

    # ==================================================
    # Main panel
    # ==================================================

    draw_translucent_panel(
        surface,
        holdem_options_panel_rect,
        (
            12,
            18,
            20,
            248
        ),
        border_color=(
            175,
            180,
            190
        ),
        border_width=2,
        radius=16
    )

    # ==================================================
    # Title
    # ==================================================

    title_surface = (
        title_font.render(
            "POKER OPTIONS",
            True,
            WHITE
        )
    )

    title_rect = (
        title_surface.get_rect(
            center=(
                holdem_options_panel_rect.centerx,
                247
            )
        )
    )

    surface.blit(
        title_surface,
        title_rect
    )

    # ==================================================
    # Close
    # ==================================================

    draw_modern_button(
        surface,
        holdem_options_close_rect,
        "X",
        mouse_pos,
        small_font,
        enabled=True
    )

    # ==================================================
    # TABLE SPEED
    # ==================================================

    speed_label = (
        name_font.render(
            "Table Speed",
            True,
            WHITE
        )
    )

    surface.blit(
        speed_label,
        (
            515,
            287
        )
    )

    draw_modern_button(
        surface,
        holdem_speed_slow_rect,
        "SLOW",
        mouse_pos,
        small_font,
        enabled=True,
        accent_color=(
            (70, 95, 125)
            if state.holdem_table_speed
            == "slow"
            else None
        )
    )

    draw_modern_button(
        surface,
        holdem_speed_normal_rect,
        "NORMAL",
        mouse_pos,
        small_font,
        enabled=True,
        accent_color=(
            (70, 95, 125)
            if state.holdem_table_speed
            == "normal"
            else None
        )
    )

    draw_modern_button(
        surface,
        holdem_speed_fast_rect,
        "FAST",
        mouse_pos,
        small_font,
        enabled=True,
        accent_color=(
            (70, 95, 125)
            if state.holdem_table_speed
            == "fast"
            else None
        )
    )

    # ==================================================
    # AUTO DEAL
    # ==================================================

    auto_label = (
        name_font.render(
            "Auto Deal Next Hand",
            True,
            WHITE
        )
    )

    surface.blit(
        auto_label,
        (
            515,
            413
        )
    )

    auto_text = (
        "ON"
        if state.holdem_auto_deal_enabled
        else "OFF"
    )

    auto_color = (
        (45, 115, 75)
        if state.holdem_auto_deal_enabled
        else (130, 55, 55)
    )

    draw_modern_button(
        surface,
        holdem_auto_deal_toggle_rect,
        auto_text,
        mouse_pos,
        small_font,
        enabled=True,
        accent_color=auto_color
    )

    # ==================================================
    # TABLE CHAT
    # ==================================================

    chat_label = (
        name_font.render(
            "NPC Table Chat",
            True,
            WHITE
        )
    )

    surface.blit(
        chat_label,
        (
            515,
            475
        )
    )

    chat_text = (
        "ON"
        if state.holdem_table_chat_enabled
        else "OFF"
    )

    chat_color = (
        (45, 115, 75)
        if state.holdem_table_chat_enabled
        else (130, 55, 55)
    )

    draw_modern_button(
        surface,
        holdem_chat_toggle_rect,
        chat_text,
        mouse_pos,
        small_font,
        enabled=True,
        accent_color=chat_color
    )

    # ==================================================
    # TABLE CHAT POP-UPS
    # ==================================================

    popup_label = name_font.render(
        "Table Chat Pop-ups",
        True,
        WHITE if state.holdem_table_chat_enabled else (125, 130, 135)
    )
    surface.blit(popup_label, (515, 537))

    popup_enabled = is_poker_chat_popups_enabled()
    popup_text = "ON" if popup_enabled else "OFF"
    popup_color = (45, 115, 75) if popup_enabled else (130, 55, 55)

    draw_modern_button(
        surface,
        holdem_chat_popups_toggle_rect,
        popup_text,
        mouse_pos,
        small_font,
        enabled=state.holdem_table_chat_enabled,
        accent_color=popup_color
    )

    # ==================================================
    # Small explanatory text
    # ==================================================

    note_surface = (
        small_font.render(
            "Settings apply immediately.",
            True,
            (
                180,
                185,
                190
            )
        )
    )

    note_rect = (
        note_surface.get_rect(
            center=(
                holdem_options_panel_rect.centerx,
                592
            )
        )
    )

    surface.blit(
        note_surface,
        note_rect
    )
