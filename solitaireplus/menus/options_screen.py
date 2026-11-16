"""Options screen and the app settings it saves (moved out of legacy.py)."""
from solitaireplus.app.settings import RESOLUTION_OPTIONS
from solitaireplus.app import app_settings as app_settings_module
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
career_saving = lazy("solitaireplus.career.career_saving")
main_menu = lazy("solitaireplus.menus.main_menu")
table = lazy("solitaireplus.games.solitaire.table")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
panels = lazy("solitaireplus.ui.panels")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")


# ----------------------------
# Music mode
# ----------------------------

music_instrumental_rect = pygame.Rect(
    420,
    180,
    170,
    50
)

music_ambient_rect = pygame.Rect(
    600,
    180,
    170,
    50
)

music_off_rect = pygame.Rect(
    780,
    180,
    170,
    50
)


# ----------------------------
# Music volume
# ----------------------------

music_slider_rect = pygame.Rect(
    500,
    290,
    400,
    20
)


# ----------------------------
# SFX volume
# ----------------------------

sfx_slider_rect = pygame.Rect(
    500,
    390,
    400,
    20
)


# ----------------------------
# Double-click mode
# ----------------------------

double_foundation_rect = pygame.Rect(
    430,
    480,
    220,
    50
)

double_both_rect = pygame.Rect(
    670,
    480,
    260,
    50
)


# ----------------------------
# Solitaire deal mode
# ----------------------------

deal_random_rect = pygame.Rect(
    430,
    540,
    180,
    42
)

deal_verified_rect = pygame.Rect(
    630,
    540,
    300,
    42
)


# ----------------------------
# Resolution
# ----------------------------

resolution_rects = [
    pygame.Rect(
        440,
        598,
        125,
        38
    ),
    pygame.Rect(
        575,
        598,
        125,
        38
    ),
    pygame.Rect(
        710,
        598,
        125,
        38
    ),
    pygame.Rect(
        845,
        598,
        125,
        38
    ),
]


# ----------------------------
# Fullscreen
# ----------------------------

fullscreen_toggle_rect = pygame.Rect(
    760,
    646,
    210,
    38
)

# ----------------------------
# Back
# ----------------------------

options_back_rect = pygame.Rect(
    533,
    705,
    300,
    42
)

app_settings = app_settings_module.AppSettings()
update_now_rect = pygame.Rect(1000, 530, 260, 42)
update_auto_rect = pygame.Rect(1000, 590, 260, 42)


def handle_update_button():
    state.update_message = ""
    if main_menu.update_checker.update_available:
        main_menu.start_game_update()
    else:
        main_menu.update_checker.start()


def current_app_settings_values():
    return {
        "music_mode": sounds.audio.music_mode,
        "music_volume": sounds.audio.music_volume,
        "sfx_volume": sounds.audio.sfx_volume,
        "double_click_mode": table.game.double_click_mode,
        "window_size": [state.WINDOWED_WIDTH, state.WINDOWED_HEIGHT],
        "fullscreen": state.fullscreen_enabled,
    }


def apply_saved_app_settings():
    """Restore the Options choices from the last session (called once, before the main loop)."""
    mode = app_settings.get("music_mode")
    if mode and mode != sounds.audio.music_mode:
        sounds.audio.set_music_mode(mode)
    if app_settings.get("music_volume") is not None:
        sounds.audio.set_music_volume(app_settings.get("music_volume"))
    if app_settings.get("sfx_volume") is not None:
        sounds.audio.set_sfx_volume(app_settings.get("sfx_volume"))
    if app_settings.get("double_click_mode"):
        table.game.double_click_mode = app_settings.get("double_click_mode")
    size = app_settings.get("window_size")
    if size and tuple(size) in RESOLUTION_OPTIONS:
        # A size saved on a bigger monitor may not fit this one: then keep the default size.
        size = window.clamp_window_size(size, window.usable_area())
        if size != (state.WINDOWED_WIDTH, state.WINDOWED_HEIGHT):
            window.set_window_size(*size)
    if app_settings.get("fullscreen"):
        window.set_fullscreen_enabled(True)


def draw_update_options_panel():
    label = fonts.option_label_font.render("Updates", True, (255, 255, 255))
    window.game_surface.blit(label, (1000, 480))
    buttons.draw_menu_button(update_now_rect, "Update now" if main_menu.update_checker.update_available else "Check now",
                     state.game_mouse_pos, font=fonts.option_value_font)
    auto = app_settings.get("auto_update_check")
    buttons.draw_menu_button(update_auto_rect, f"Auto check: {'On' if auto else 'Off'}", state.game_mouse_pos,
                     selected=auto, font=fonts.option_value_font)
    status = state.update_message or main_menu.update_checker.status_text()
    line, y = "", 642
    for word in status.split():  # wrap to the space right of the other options
        candidate = f"{line} {word}".strip()
        if line and fonts.ui_small_font.size(candidate)[0] > 340:
            window.game_surface.blit(fonts.ui_small_font.render(line, True, (220, 220, 220)), (1000, y))
            line, y = word, y + fonts.ui_small_font.get_linesize()
        else:
            line = candidate
    if line:
        window.game_surface.blit(fonts.ui_small_font.render(line, True, (220, 220, 220)), (1000, y))


# ==================================================
# OPTIONS MENU
# ==================================================

def draw_options_menu():

    panels.draw_submenu_background(
        overlay_alpha=135
    )

    panels.draw_submenu_title(
        "OPTIONS",
        y=60,
        width=390
    )

    # ----------------------------
    # Music
    # ----------------------------

    label = fonts.option_label_font.render(
        "Music",
        True,
        (
            255,
            255,
            255
        )
    )

    window.game_surface.blit(
        label,
        (
            250,
            190
        )
    )

    buttons.draw_menu_button(
        music_instrumental_rect,
        "Instrumental",
        state.game_mouse_pos,
        selected=(
                sounds.audio.music_mode
                == "instrumental"
        ),
        font=fonts.option_value_font
    )

    buttons.draw_menu_button(
        music_ambient_rect,
        "Ambient",
        state.game_mouse_pos,
        selected=(
                sounds.audio.music_mode
                == "ambient"
        ),
        font=fonts.option_value_font
    )

    buttons.draw_menu_button(
        music_off_rect,
        "Off",
        state.game_mouse_pos,
        selected=(
                sounds.audio.music_mode
                == "off"
        ),
        font=fonts.option_value_font
    )

    # ----------------------------
    # Music volume
    # ----------------------------

    label = fonts.option_label_font.render(
        "Music Volume",
        True,
        (
            255,
            255,
            255
        )
    )

    window.game_surface.blit(
        label,
        (
            250,
            280
        )
    )

    pygame.draw.rect(
        window.game_surface,
        (
            100,
            100,
            100
        ),
        music_slider_rect
    )

    music_fill_width = int(
        music_slider_rect.width
        * sounds.audio.music_volume
    )

    pygame.draw.rect(
        window.game_surface,
        (
            255,
            255,
            255
        ),
        (
            music_slider_rect.x,
            music_slider_rect.y,
            music_fill_width,
            music_slider_rect.height
        )
    )

    music_knob_x = (
            music_slider_rect.x
            + music_fill_width
    )

    pygame.draw.circle(
        window.game_surface,
        (
            255,
            255,
            255
        ),
        (
            music_knob_x,
            music_slider_rect.centery
        ),
        12
    )

    pygame.draw.circle(
        window.game_surface,
        (
            40,
            40,
            40
        ),
        (
            music_knob_x,
            music_slider_rect.centery
        ),
        12,
        2
    )

    percent = fonts.option_value_font.render(
        f"{int(sounds.audio.music_volume * 100)}%",
        True,
        (
            255,
            255,
            255
        )
    )

    window.game_surface.blit(
        percent,
        (
            930,
            music_slider_rect.y - 5
        )
    )

    # ----------------------------
    # SFX volume
    # ----------------------------

    label = fonts.option_label_font.render(
        "Sound Effects",
        True,
        (
            255,
            255,
            255
        )
    )

    window.game_surface.blit(
        label,
        (
            250,
            380
        )
    )

    pygame.draw.rect(
        window.game_surface,
        (
            100,
            100,
            100
        ),
        sfx_slider_rect
    )

    sfx_fill_width = int(
        sfx_slider_rect.width
        * sounds.audio.sfx_volume
    )

    pygame.draw.rect(
        window.game_surface,
        (
            255,
            255,
            255
        ),
        (
            sfx_slider_rect.x,
            sfx_slider_rect.y,
            sfx_fill_width,
            sfx_slider_rect.height
        )
    )

    sfx_knob_x = (
            sfx_slider_rect.x
            + sfx_fill_width
    )

    pygame.draw.circle(
        window.game_surface,
        (
            255,
            255,
            255
        ),
        (
            sfx_knob_x,
            sfx_slider_rect.centery
        ),
        12
    )

    pygame.draw.circle(
        window.game_surface,
        (
            40,
            40,
            40
        ),
        (
            sfx_knob_x,
            sfx_slider_rect.centery
        ),
        12,
        2
    )

    percent = fonts.option_value_font.render(
        f"{int(sounds.audio.sfx_volume * 100)}%",
        True,
        (
            255,
            255,
            255
        )
    )

    window.game_surface.blit(
        percent,
        (
            930,
            sfx_slider_rect.y - 5
        )
    )

    # ----------------------------
    # Double-click mode
    # ----------------------------

    label = fonts.option_label_font.render(
        "Double Click",
        True,
        (
            255,
            255,
            255
        )
    )

    window.game_surface.blit(
        label,
        (
            250,
            490
        )
    )

    buttons.draw_menu_button(
        double_foundation_rect,
        "Foundation Only",
        state.game_mouse_pos,
        selected=(
                table.game.double_click_mode
                == "foundation"
        ),
        font=fonts.option_value_font
    )

    buttons.draw_menu_button(
        double_both_rect,
        "Foundation + Tableau",
        state.game_mouse_pos,
        selected=(
                table.game.double_click_mode
                == "foundation_and_tableau"
        ),
        font=fonts.option_value_font
    )

    # ----------------------------
    # Solitaire deal mode
    # ----------------------------

    label = fonts.option_label_font.render(
        "New Deals",
        True,
        (
            255,
            255,
            255
        )
    )

    window.game_surface.blit(
        label,
        (
            250,
            550
        )
    )

    buttons.draw_menu_button(
        deal_random_rect,
        "Random",
        state.game_mouse_pos,
        selected=(
                table.game.deal_mode
                == "random"
        ),
        font=fonts.option_value_font
    )

    if table.VERIFIED_DEALS_ENABLED:
        buttons.draw_menu_button(
            deal_verified_rect,
            "Verified Solvable",
            state.game_mouse_pos,
            selected=(table.game.deal_mode == "verified"),
            font=fonts.option_value_font
        )
    else:
        pygame.draw.rect(
            window.game_surface,
            (72, 76, 74),
            deal_verified_rect,
            border_radius=8,
        )
        pygame.draw.rect(
            window.game_surface,
            (115, 120, 118),
            deal_verified_rect,
            2,
            border_radius=8,
        )
        disabled_label = fonts.option_value_font.render(
            "Verified Solvable",
            True,
            (155, 158, 156),
        )
        window.game_surface.blit(
            disabled_label,
            disabled_label.get_rect(center=deal_verified_rect.center),
        )

        if (
                state.game_mouse_pos is not None
                and deal_verified_rect.collidepoint(state.game_mouse_pos)
        ):
            tooltip_rect = pygame.Rect(600, 492, 455, 38)
            pygame.draw.rect(
                window.game_surface,
                (22, 26, 24),
                tooltip_rect,
                border_radius=7,
            )
            pygame.draw.rect(
                window.game_surface,
                (205, 178, 90),
                tooltip_rect,
                2,
                border_radius=7,
            )
            tooltip = fonts.difficulty_detail_font.render(
                "Temporarily disabled while the deal generator is rebuilt.",
                True,
                (240, 235, 218),
            )
            window.game_surface.blit(
                tooltip,
                tooltip.get_rect(center=tooltip_rect.center),
            )

    # ----------------------------
    # Window size
    # ----------------------------

    label = fonts.option_label_font.render(
        "Window Size",
        True,
        (
            255,
            255,
            255
        )
    )

    window.game_surface.blit(
        label,
        (
            250,
            608
        )
    )

    # Sizes that don't fit this screen (with the title bar and taskbar) are greyed out (W1).
    size_choices = window.window_size_choices(window.usable_area(), RESOLUTION_OPTIONS)
    too_large_hovered = False

    for index, (resolution, fits_screen) in enumerate(size_choices):
        width, height = resolution

        selected = (
            state.WINDOWED_WIDTH == width
            and state.WINDOWED_HEIGHT == height
        )

        text = (
            f"{width}x{height}"
        )

        if fits_screen:
            buttons.draw_menu_button(
                resolution_rects[index],
                text,
                state.game_mouse_pos,
                selected=selected,
                font=fonts.option_value_font
            )
            continue

        pygame.draw.rect(window.game_surface, (72, 76, 74), resolution_rects[index], border_radius=8)
        pygame.draw.rect(window.game_surface, (115, 120, 118), resolution_rects[index], 2, border_radius=8)
        disabled_label = fonts.option_value_font.render(text, True, (155, 158, 156))
        window.game_surface.blit(disabled_label, disabled_label.get_rect(center=resolution_rects[index].center))
        if state.game_mouse_pos is not None and resolution_rects[index].collidepoint(state.game_mouse_pos):
            too_large_hovered = True

    if too_large_hovered:
        tooltip_rect = pygame.Rect(440, 556, 530, 36)
        pygame.draw.rect(window.game_surface, (22, 26, 24), tooltip_rect, border_radius=7)
        pygame.draw.rect(window.game_surface, (205, 178, 90), tooltip_rect, 2, border_radius=7)
        tooltip = fonts.difficulty_detail_font.render("Too large for this screen.", True, (240, 235, 218))
        window.game_surface.blit(tooltip, tooltip.get_rect(center=tooltip_rect.center))

    # ----------------------------
    # Fullscreen
    # ----------------------------

    label = fonts.option_label_font.render(
        "Fullscreen",
        True,
        (
            255,
            255,
            255
        )
    )

    window.game_surface.blit(
        label,
        (
            250,
            654
        )
    )

    buttons.draw_menu_button(
        fullscreen_toggle_rect,
        "On" if state.fullscreen_enabled else "Off",
        state.game_mouse_pos,
        selected=state.fullscreen_enabled,
        font=fonts.option_value_font
    )

    draw_update_options_panel()

    # ----------------------------
    # Back
    # ----------------------------

    buttons.draw_menu_button(
        options_back_rect,
        "Return",
        state.game_mouse_pos,
        font=fonts.difficulty_detail_font
    )


def handle_event(event):
    """Old main-loop event branch for STATE_OPTIONS."""

    # ==================================================
    # Mouse down
    # ==================================================

    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):

        # ----------------------------
        # Music mode
        # ----------------------------

        if music_instrumental_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            sounds.audio.set_music_mode(
                "instrumental"
            )

        elif music_ambient_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            sounds.audio.set_music_mode(
                "ambient"
            )

        elif music_off_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            sounds.audio.set_music_mode(
                "off"
            )

        # ----------------------------
        # Music volume
        # ----------------------------

        elif music_slider_rect.collidepoint(
                state.game_mouse_pos
        ):
            state.music_slider_dragging = True

            state.relative_x = (
                    state.game_mouse_pos[0]
                    - music_slider_rect.x
            )

            state.volume = (
                    state.relative_x
                    / music_slider_rect.width
            )

            state.volume = max(
                0.0,
                min(
                    1.0,
                    state.volume
                )
            )

            sounds.audio.set_music_volume(
                state.volume
            )

        # ----------------------------
        # SFX volume
        # ----------------------------

        elif sfx_slider_rect.collidepoint(
                state.game_mouse_pos
        ):
            state.sfx_slider_dragging = True

            state.relative_x = (
                    state.game_mouse_pos[0]
                    - sfx_slider_rect.x
            )

            state.volume = (
                    state.relative_x
                    / sfx_slider_rect.width
            )

            state.volume = max(
                0.0,
                min(
                    1.0,
                    state.volume
                )
            )

            sounds.audio.set_sfx_volume(
                state.volume
            )

            sounds.audio.play_sound(
                "button_click"
            )

        # ----------------------------
        # Double click
        # ----------------------------

        elif double_foundation_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            table.game.double_click_mode = (
                "foundation"
            )

        elif double_both_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            table.game.double_click_mode = (
                "foundation_and_tableau"
            )

        # ----------------------------
        # Solitaire deal mode
        # ----------------------------

        elif deal_random_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )
            table.game.set_deal_mode(
                "random"
            )

        elif deal_verified_rect.collidepoint(
                state.game_mouse_pos
        ):
            if table.VERIFIED_DEALS_ENABLED:
                sounds.audio.play_sound("button_click")
                table.game.set_deal_mode("verified")

        # ----------------------------
        # Fullscreen
        # ----------------------------

        elif fullscreen_toggle_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            window.set_fullscreen_enabled(
                not state.fullscreen_enabled
            )

        # ----------------------------
        # Updates
        # ----------------------------

        elif update_now_rect.collidepoint(state.game_mouse_pos):
            sounds.audio.play_sound("button_click")
            handle_update_button()

        elif update_auto_rect.collidepoint(state.game_mouse_pos):
            sounds.audio.play_sound("button_click")
            app_settings.update({"auto_update_check": not app_settings.get("auto_update_check")})
            app_settings.flush()

        # ----------------------------
        # Resolution
        # ----------------------------

        else:
            resolution_clicked = False

            for resolution_index, resolution_rect in enumerate(
                    resolution_rects
            ):
                if resolution_rect.collidepoint(
                        state.game_mouse_pos
                ):
                    width, height = (
                        RESOLUTION_OPTIONS[
                            resolution_index
                        ]
                    )

                    resolution_clicked = True

                    # Greyed-out sizes (too large for this screen) do nothing (W1).
                    if not window.fits((width, height), window.usable_area()):
                        break

                    sounds.audio.play_sound(
                        "button_click"
                    )

                    window.set_window_size(
                        width,
                        height
                    )

                    break

            # ----------------------------
            # Back
            # ----------------------------

            if (
                    not resolution_clicked
                    and options_back_rect
                    .collidepoint(
                state.game_mouse_pos
            )
            ):
                sounds.audio.play_sound(
                    "button_click"
                )

                state.music_slider_dragging = False
                state.sfx_slider_dragging = False

                if state.options_return_state == state_names.STATE_CAREER_HUB:
                    career_saving.save_career_from_hub()
                state.current_state = state.options_return_state

    # ==================================================
    # Slider dragging
    # ==================================================

    elif (
            event.type == pygame.MOUSEMOTION
            and state.game_mouse_pos is not None
    ):

        # ----------------------------
        # Music volume
        # ----------------------------

        if state.music_slider_dragging:

            state.relative_x = (
                    state.game_mouse_pos[0]
                    - music_slider_rect.x
            )

            state.volume = (
                    state.relative_x
                    / music_slider_rect.width
            )

            state.volume = max(
                0.0,
                min(
                    1.0,
                    state.volume
                )
            )

            sounds.audio.set_music_volume(
                state.volume
            )

        # ----------------------------
        # SFX volume
        # ----------------------------

        elif state.sfx_slider_dragging:

            state.relative_x = (
                    state.game_mouse_pos[0]
                    - sfx_slider_rect.x
            )

            state.volume = (
                    state.relative_x
                    / sfx_slider_rect.width
            )

            state.volume = max(
                0.0,
                min(
                    1.0,
                    state.volume
                )
            )

            sounds.audio.set_sfx_volume(
                state.volume
            )

    # ==================================================
    # End slider dragging
    # ==================================================

    elif (
            event.type
            == pygame.MOUSEBUTTONUP
            and event.button == 1
    ):

        state.music_slider_dragging = False
        state.sfx_slider_dragging = False


def enter():
    """Options opens with no slider drag (the button release of an old drag may have gone elsewhere)."""
    state.music_slider_dragging = False
    state.sfx_slider_dragging = False


def leave():
    """Leaving Options mid-drag (F10 for example) ends the drag."""
    state.music_slider_dragging = False
    state.sfx_slider_dragging = False


def draw():
    """Old draw-chain branch for STATE_OPTIONS."""

    draw_options_menu()
