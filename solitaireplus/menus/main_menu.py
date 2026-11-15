"""Main menu, the update banner and the multiplayer launcher button (moved out of legacy.py)."""
from solitaireplus.games.solitaire.rules import BASE_HEIGHT
from solitaireplus.games.solitaire.rules import BASE_WIDTH
from version import __version__ as BUILD_VERSION
from solitaireplus.app.multiplayer_launcher import MultiplayerLauncher
import math
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app import update_check
from solitaireplus.app.lazy import lazy
options_screen = lazy("solitaireplus.menus.options_screen")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")
backgrounds = lazy("solitaireplus.ui.backgrounds")
assets = lazy("solitaireplus.app.assets")


multiplayer_launcher = MultiplayerLauncher()


# ==================================================
# MAIN MENU UI
# ==================================================

new_game_rect = pygame.Rect(533, 214, 300, 54)
profile_rect = pygame.Rect(533, 278, 300, 54)
customize_rect = pygame.Rect(533, 342, 300, 54)
achievements_rect = pygame.Rect(533, 406, 300, 54)
how_to_play_rect = pygame.Rect(533, 470, 300, 54)
options_rect = pygame.Rect(533, 534, 300, 54)
quit_rect = pygame.Rect(533, 598, 300, 54)
multiplayer_rect = pygame.Rect(533, 662, 300, 54)
update_checker = update_check.UpdateChecker()
update_banner_rect = pygame.Rect(946, 688, 400, 54)


def start_game_update():
    """Save, open the updater window, and close the game (the updater restarts it)."""
    if multiplayer_launcher.process is not None and multiplayer_launcher.process.poll() is None:
        state.update_message = "Close the Multiplayer window first, then try again."
        return
    legacy.auto_save_career()
    options_screen.app_settings.flush()
    if update_check.launch_update():
        state.running = False
    else:
        state.update_message = "The updater could not be started. Reinstall Solitaire+ to fix this."


def draw_update_banner():
    if update_checker.update_available:
        buttons.draw_menu_button(update_banner_rect, f"Update to {update_checker.latest}", state.menu_mouse_pos,
                         font=fonts.option_value_font)
    if state.update_message:
        text = fonts.ui_small_font.render(state.update_message, True, (255, 200, 150))
        window.game_surface.blit(text, text.get_rect(midright=(BASE_WIDTH - 20, update_banner_rect.y - 16)))

# ==================================================
# MAIN MENU
# ==================================================

def draw_main_menu():

    # ----------------------------
    # Drifting background
    # ----------------------------

    backgrounds.draw_drifting_menu_background()

    # ----------------------------
    # Floating logo
    # ----------------------------

    time_sec = pygame.time.get_ticks() / 1000.0

    bob_y = int(
        math.sin(time_sec * 1.7) * 10
    )

    window.game_surface.blit(
        assets.floating_logo,
        (70, 690 + bob_y)
    )

    # ----------------------------
    # Title image
    # ----------------------------

    title_image = assets.title_surfaces[
        state.selected_title
    ]

    window.game_surface.blit(
        title_image,
        (0, 0)
    )

    # ----------------------------
    # Buttons
    # ----------------------------

    buttons.draw_menu_button(
        new_game_rect,
        "Play",
        state.menu_mouse_pos
    )

    buttons.draw_menu_button(
        profile_rect,
        "Profile",
        state.menu_mouse_pos
    )

    buttons.draw_menu_button(
        customize_rect,
        "Customize",
        state.menu_mouse_pos
    )

    buttons.draw_menu_button(
        achievements_rect,
        "Achievements",
        state.menu_mouse_pos
    )

    buttons.draw_menu_button(
        how_to_play_rect,
        "Help",
        state.menu_mouse_pos
    )

    buttons.draw_menu_button(
        options_rect,
        "Options",
        state.menu_mouse_pos
    )

    buttons.draw_menu_button(
        quit_rect,
        "Quit",
        state.menu_mouse_pos
    )

    buttons.draw_menu_button(multiplayer_rect, "Launch Multiplayer", state.menu_mouse_pos)
    if multiplayer_launcher.error:
        message = fonts.ui_small_font.render(multiplayer_launcher.error, True, (255, 180, 140))
        window.game_surface.blit(message, message.get_rect(center=(BASE_WIDTH // 2, 735)))

    build_surface = fonts.ui_small_font.render(
        BUILD_VERSION,
        True,
        (
            120,
            120,
            120
        )
    )

    window.game_surface.blit(
        build_surface,
        (
            10,
            BASE_HEIGHT - 28
        )
    )

    draw_update_banner()


def handle_event(event):
    """Old main-loop event branch for STATE_MENU."""

    if (
        event.type
        == pygame.MOUSEBUTTONDOWN
        and event.button == 1
    ):
        if new_game_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.current_state = state_names.STATE_MODE_SELECT

        elif multiplayer_rect.collidepoint(state.game_mouse_pos):
            sounds.audio.play_sound("button_click")
            multiplayer_launcher.launch()

        elif update_checker.update_available and update_banner_rect.collidepoint(state.game_mouse_pos):
            sounds.audio.play_sound("button_click")
            start_game_update()

        elif customize_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.customize_return_state = state_names.STATE_MENU
            state.customize_category = legacy.CUSTOMIZE_BACKGROUNDS

            state.customize_page = 0

            state.current_state = state_names.STATE_CUSTOMIZE

        elif achievements_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound("button_click")
            state.achievements_scroll_y = 0
            state.current_state = state_names.STATE_ACHIEVEMENTS

        elif how_to_play_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.current_state = state_names.STATE_HOW_TO_PLAY

        elif options_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.options_return_state = state_names.STATE_MENU

            state.current_state = state_names.STATE_OPTIONS

        elif profile_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.profile_return_state = state_names.STATE_MENU
            state.profile_select_return_state = state_names.STATE_MENU
            state.profile_name_text = state.player_name
            state.profile_name_active = False
            state.profile_country_active = False
            state.profile_age_active = False
            state.profile_hometown_active = False
            state.profile_bio_active = False
            state.gender_dropdown_open = False
            state.favorite_suit_dropdown_open = False
            state.profile_message = ""

            state.current_state = state_names.STATE_PROFILE

        elif quit_rect.collidepoint(
            state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.running = False


def draw():
    """Old draw-chain branch for STATE_MENU."""

    draw_main_menu()
