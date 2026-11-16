"""Texas Hold'em table UI: the bet slider, the manual bet entry and the action panel.

One part of the Hold'em table UI (see holdem_ui.py, which re-exports every name here).
The slider and manual bet values live in solitaireplus/app/state.py.
"""
from solitaireplus.app import state

import pygame

from solitaireplus.games.poker.holdem_ui_state import (
    WHITE,
    get_holdem_fonts,
    holdem_action_panel_rect,
    holdem_call_rect,
    holdem_fold_rect,
    holdem_half_rect,
    holdem_manual_bet_rect,
    holdem_max_rect,
    holdem_min_rect,
    holdem_next_hand_rect,
    holdem_pot_rect,
    holdem_raise_rect,
    holdem_slider_rect,
)
from solitaireplus.games.poker.holdem_ui_widgets import draw_modern_button, draw_translucent_panel


def set_holdem_bet_slider_from_mouse(
        mouse_pos
):

    if mouse_pos is None:
        return False

    mouse_x = max(
        holdem_slider_rect.left,
        min(
            mouse_pos[0],
            holdem_slider_rect.right
        )
    )

    relative_x = (
        mouse_x
        - holdem_slider_rect.left
    )

    state.holdem_bet_fraction = (
        relative_x
        / max(
            1,
            holdem_slider_rect.width
        )
    )

    state.holdem_bet_fraction = max(
        0.0,
        min(
            state.holdem_bet_fraction,
            1.0
        )
    )

    state.holdem_manual_bet_text = ""
    state.holdem_manual_bet_active = False

    return True


def drag_holdem_bet_slider(
        mouse_pos
):

    if not state.holdem_bet_slider_dragging:
        return False

    return (
        set_holdem_bet_slider_from_mouse(
            mouse_pos
        )
    )


def stop_holdem_bet_slider_drag():

    was_dragging = (
        state.holdem_bet_slider_dragging
    )

    state.holdem_bet_slider_dragging = False

    return was_dragging

def update_holdem_bet_slider(
        mouse_pos,
        holdem_game
):

    if mouse_pos is None:
        return False

    # ==================================================
    # Is wager adjustment currently meaningful?
    # ==================================================

    if (
            holdem_game.hand_complete
            or holdem_game.player_folded
            or holdem_game.player_all_in
            or holdem_game.player_stack <= 0
    ):
        return False

    # If facing an existing bet, only allow the
    # slider when raising is actually legal.
    if (
            holdem_game.current_bet > 0
            and not holdem_game.can_player_raise()
    ):
        return False

    # ==================================================
    # Slider
    #
    # Use a taller hitbox than the visual track so
    # grabbing the knob feels forgiving.
    # ==================================================

    slider_hit_rect = (
        holdem_slider_rect.inflate(
            0,
            24
        )
    )

    if slider_hit_rect.collidepoint(
            mouse_pos
    ):

        state.holdem_bet_slider_dragging = True

        set_holdem_bet_slider_from_mouse(
            mouse_pos
        )

        return True

    # ==================================================
    # Shortcut buttons
    # ==================================================

    if holdem_min_rect.collidepoint(
            mouse_pos
    ):

        state.holdem_bet_fraction = 0.0
        state.holdem_manual_bet_text = ""
        state.holdem_manual_bet_active = False

        return True

    if holdem_half_rect.collidepoint(
            mouse_pos
    ):

        state.holdem_bet_fraction = 0.5
        state.holdem_manual_bet_text = ""
        state.holdem_manual_bet_active = False

        return True

    if holdem_pot_rect.collidepoint(
            mouse_pos
    ):

        if holdem_game.player_stack <= 0:
            return False

        pot_target = min(
            holdem_game.pot,
            holdem_game.player_stack
        )

        state.holdem_bet_fraction = (
            pot_target
            / holdem_game.player_stack
        )

        state.holdem_bet_fraction = max(
            0.0,
            min(
                state.holdem_bet_fraction,
                1.0
            )
        )

        state.holdem_manual_bet_text = ""
        state.holdem_manual_bet_active = False

        return True

    if holdem_max_rect.collidepoint(
            mouse_pos
    ):

        state.holdem_bet_fraction = 1.0
        state.holdem_manual_bet_text = ""
        state.holdem_manual_bet_active = False

        return True

    return False

def clear_holdem_manual_bet():

    state.holdem_manual_bet_text = ""
    state.holdem_manual_bet_active = False


def handle_holdem_manual_bet_click(
        mouse_pos,
        holdem_game
):

    if mouse_pos is None:
        return False

    can_edit = (
        not holdem_game.hand_complete
        and holdem_game.can_player_act_now()
        and (
            holdem_game.current_bet == 0
            or holdem_game.can_player_raise()
        )
    )

    if can_edit and holdem_manual_bet_rect.collidepoint(mouse_pos):
        state.holdem_manual_bet_active = True
        return True

    if state.holdem_manual_bet_active:
        state.holdem_manual_bet_active = False

    return False


def handle_holdem_manual_bet_key(
        event,
        holdem_game
):

    if not state.holdem_manual_bet_active:
        return False

    if event.type != pygame.KEYDOWN:
        return False

    if event.key == pygame.K_ESCAPE:
        state.holdem_manual_bet_active = False
        return True

    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        state.holdem_manual_bet_active = False
        return True

    if event.key == pygame.K_BACKSPACE:
        state.holdem_manual_bet_text = state.holdem_manual_bet_text[:-1]
        return True

    character = getattr(event, "unicode", "")

    if character.isdigit() and len(state.holdem_manual_bet_text) < 9:
        state.holdem_manual_bet_text += character

    return True


def get_holdem_manual_bet_amount(holdem_game):

    if not state.holdem_manual_bet_text:
        return None

    try:
        requested = int(state.holdem_manual_bet_text)
    except ValueError:
        return None

    if requested <= 0 or holdem_game.player_stack <= 0:
        return None

    if holdem_game.current_bet == 0:
        minimum = holdem_game.get_minimum_open_bet()
        maximum = holdem_game.player_stack

        if maximum <= minimum:
            return maximum

        return max(minimum, min(requested, maximum))

    minimum = holdem_game.get_minimum_raise_to()
    maximum = holdem_game.get_player_maximum_raise_to()

    if maximum <= minimum:
        return maximum

    return max(minimum, min(requested, maximum))


def get_holdem_bet_amount(
        holdem_game
):

    available_stack = (
        holdem_game.player_stack
    )

    if available_stack <= 0:
        return 0

    manual_amount = get_holdem_manual_bet_amount(
        holdem_game
    )

    if manual_amount is not None:
        return manual_amount

    # ==================================================
    # Opening bet
    # ==================================================

    if holdem_game.current_bet == 0:

        minimum = (
            holdem_game.get_minimum_open_bet()
        )

        maximum = (
            available_stack
        )

        if maximum <= minimum:
            return maximum

        amount = int(
            minimum
            + (
                maximum
                - minimum
            )
            * state.holdem_bet_fraction
        )

        return max(
            minimum,
            min(
                amount,
                maximum
            )
        )

    # ==================================================
    # Raise TO amount
    # ==================================================

    minimum_raise_to = (
        holdem_game.get_minimum_raise_to()
    )

    maximum_raise_to = (
        holdem_game
        .get_player_maximum_raise_to()
    )

    if (
            maximum_raise_to
            <= minimum_raise_to
    ):

        return maximum_raise_to

    amount = int(
        minimum_raise_to
        + (
            maximum_raise_to
            - minimum_raise_to
        )
        * state.holdem_bet_fraction
    )

    return max(
        minimum_raise_to,
        min(
            amount,
            maximum_raise_to
        )
    )


def draw_holdem_side_panel(
        surface,
        holdem_game,
        title_font,
        detail_font,
        mouse_pos,
        next_hand_seconds=None
):
    player_is_current_actor = (
            not holdem_game.hand_complete
            and holdem_game.current_actor == 0
            and not holdem_game.player_has_acted
    )

    holdem_fonts = get_holdem_fonts()

    holdem_small_font = (
        holdem_fonts["small"]
    )

    panel_rect = (
        holdem_action_panel_rect
    )

    draw_translucent_panel(
        surface,
        panel_rect,
        (
            8,
            18,
            18,
            220
        ),
        border_color=(
            200,
            200,
            205
        ),
        border_width=2,
        radius=14
    )

    # ==================================================
    # Hand complete / next-hand controls
    # ==================================================

    if holdem_game.hand_complete:

        # ==================================================
        # Player busted
        # ==================================================

        if holdem_game.player_busted:
            draw_modern_button(
                surface,
                holdem_next_hand_rect,
                "BUSTED",
                mouse_pos,
                holdem_small_font,
                enabled=False
            )

            return

        # ==================================================
        # Player cleared table
        # ==================================================

        if holdem_game.all_npcs_busted():
            draw_modern_button(
                surface,
                holdem_next_hand_rect,
                "TABLE CLEARED +100",
                mouse_pos,
                holdem_small_font,
                enabled=True,
                accent_color=(
                    105,
                    82,
                    32
                )
            )

            return

        # ==================================================
        # Normal completed hand
        # ==================================================

        draw_modern_button(
            surface,
            holdem_next_hand_rect,
            "NEXT HAND",
            mouse_pos,
            holdem_small_font,
            enabled=True
        )

        if next_hand_seconds is not None:
            countdown_text = (
                f"Auto-deal in "
                f"{next_hand_seconds}s"
            )

            countdown_surface = (
                holdem_small_font.render(
                    countdown_text,
                    True,
                    WHITE
                )
            )

            countdown_rect = (
                countdown_surface.get_rect(
                    center=(
                        holdem_action_panel_rect.centerx,
                        704
                    )
                )
            )

            surface.blit(
                countdown_surface,
                countdown_rect
            )

        return

    # ==================================================
    # Context-sensitive button labels
    # ==================================================

    amount_to_call = (
        holdem_game.get_player_amount_to_call()
    )

    bet_amount = (
        get_holdem_bet_amount(
            holdem_game
        )
    )

    if amount_to_call > 0:

        call_amount = min(
            amount_to_call,
            holdem_game.player_stack
        )

        call_text = (
            f"CALL ${call_amount:,}"
        )

    else:

        call_text = "CHECK"

    # ==================================================
    # Bet / Raise button label
    # ==================================================

    if holdem_game.current_bet > 0:

        maximum_action_amount = (
            holdem_game
            .get_player_maximum_raise_to()
        )

    else:

        maximum_action_amount = (
            holdem_game.player_stack
        )

    is_all_in_amount = (
            maximum_action_amount > 0
            and bet_amount
            >= maximum_action_amount
    )

    if is_all_in_amount:

        raise_text = "ALL IN"

    elif holdem_game.current_bet > 0:

        raise_text = (
            f"RAISE TO ${bet_amount:,}"
        )

    else:

        raise_text = (
            f"BET ${bet_amount:,}"
        )

    # ==================================================
    # Button enabled states
    # ==================================================

    player_can_act = (
        holdem_game.can_player_act_now()
    )

    fold_enabled = (
        player_can_act
    )

    call_enabled = (
        player_can_act
    )

    all_in_call = amount_to_call > 0 and amount_to_call >= holdem_game.player_stack
    if all_in_call:
        call_text = f"ALL-IN CALL ${holdem_game.player_stack:,}"
        raise_text = "ALL IN"
    raise_enabled = player_can_act and (holdem_game.can_player_raise() or all_in_call)

    call_accent = None

    if (
            player_is_current_actor
            and call_enabled
    ):
        pulse = (
                        pygame.time.get_ticks()
                        % 1600
                ) / 1600.0

        pulse_strength = (
                0.5
                + 0.5
                * abs(
            2.0 * pulse - 1.0
        )
        )

        call_accent = (
            int(150 + 70 * pulse_strength),
            int(115 + 65 * pulse_strength),
            int(25 + 35 * pulse_strength)
        )

    # ==================================================
    # Main action row
    # ==================================================

    draw_modern_button(
        surface,
        holdem_fold_rect,
        "FOLD",
        mouse_pos,
        holdem_small_font,
        enabled=fold_enabled,
        accent_color=(
            185,
            45,
            45
        )
    )

    draw_modern_button(
        surface,
        holdem_call_rect,
        call_text,
        mouse_pos,
        holdem_small_font,
        enabled=call_enabled,
        accent_color=call_accent
    )

    draw_modern_button(
        surface,
        holdem_raise_rect,
        raise_text,
        mouse_pos,
        holdem_small_font,
        enabled=raise_enabled,
        accent_color=(
            45,
            125,
            80
        )
    )

    # ==================================================
    # Raise slider
    # ==================================================

    pygame.draw.rect(
        surface,
        (
            70,
            75,
            85
        ),
        holdem_slider_rect,
        border_radius=7
    )

    knob_width = 18

    knob_x = int(
        holdem_slider_rect.x
        + (
                holdem_slider_rect.width
                - knob_width
        )
        * state.holdem_bet_fraction
    )

    knob_rect = pygame.Rect(
        knob_x,
        holdem_slider_rect.y - 3,
        knob_width,
        holdem_slider_rect.height + 6
    )

    if state.holdem_bet_slider_dragging:

        knob_color = (
            175,
            205,
            240
        )

        knob_border = (
            235,
            245,
            255
        )

    else:

        knob_color = (
            130,
            170,
            220
        )

        knob_border = (
            170,
            195,
            225
        )

    pygame.draw.rect(
        surface,
        knob_color,
        knob_rect,
        border_radius=6
    )

    pygame.draw.rect(
        surface,
        knob_border,
        knob_rect,
        2,
        border_radius=6
    )

    # ==================================================
    # Manual bet / raise-to entry
    # ==================================================

    manual_enabled = (
        player_can_act
        and (
            holdem_game.current_bet == 0
            or holdem_game.can_player_raise()
        )
    )

    manual_fill = (18, 24, 27, 235) if manual_enabled else (48, 48, 52, 220)
    manual_border = (235, 190, 70) if state.holdem_manual_bet_active else ((150, 175, 205) if state.holdem_manual_bet_text else (105, 110, 118))

    draw_translucent_panel(
        surface,
        holdem_manual_bet_rect,
        manual_fill,
        border_color=manual_border,
        border_width=2 if state.holdem_manual_bet_active else 1,
        radius=7
    )

    if state.holdem_manual_bet_text:
        manual_label = f"${state.holdem_manual_bet_text}"
        manual_color = WHITE if manual_enabled else (150, 150, 155)
    else:
        manual_label = (
            "BET $"
            if holdem_game.current_bet == 0
            else "RAISE $"
        )
        manual_color = (165, 170, 178) if manual_enabled else (120, 120, 125)

    manual_surface = holdem_small_font.render(
        manual_label,
        True,
        manual_color
    )

    surface.blit(
        manual_surface,
        manual_surface.get_rect(center=holdem_manual_bet_rect.center)
    )

    # ==================================================
    # Slider shortcuts
    # ==================================================

    draw_modern_button(
        surface,
        holdem_min_rect,
        "MIN",
        mouse_pos,
        holdem_small_font,
        enabled=True
    )

    draw_modern_button(
        surface,
        holdem_half_rect,
        "1/2",
        mouse_pos,
        holdem_small_font,
        enabled=True
    )

    draw_modern_button(
        surface,
        holdem_pot_rect,
        "POT",
        mouse_pos,
        holdem_small_font,
        enabled=True
    )

    draw_modern_button(
        surface,
        holdem_max_rect,
        "MAX",
        mouse_pos,
        holdem_small_font,
        enabled=True
    )
