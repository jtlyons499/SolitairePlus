"""The main loop and the screen registry (the old `while running:` loop of main.py).

Each frame: poll the update check and settings, sync audio, handle events (global keys,
mouse mapping, then the current screen), run per-frame updates, draw the current screen,
then overlays, then present. The order is exactly the old loop's order.

Importing this module runs the start-up sequence first (solitaireplus/app/startup.py).

SCREENS maps a screen name to the code that runs it: "package.module" for a screen module
(functions handle_event(event), draw(), and optionally update(), late_update(), enter() and
leave()), or "package.module:<screen>" for a module that holds several screens (functions
loop_event_<screen>, loop_draw_<screen>, ...).

When state.current_state changes, the old screen's leave() and the new screen's enter() run
(checked after each event and at the start of each frame).

Mouse positions: while an event is handled, state.game_mouse_pos is that event's position
(None for events without one, like key presses). Drawing uses the mouse position of the frame
(state.mouse_pos), so a key press does not drop the hover highlight.
"""
import importlib
import pygame
from solitaireplus.menus.achievements_screen import draw_achievement_popup
from solitaireplus.app import state, state_names
from solitaireplus.app import startup  # noqa: F401,I001 (runs the start-up sequence; must come before the modules below)
from solitaireplus.debug import actions  # loaded at start-up, as in main.py: tools find the F10 actions by name
from solitaireplus.app import fonts
from solitaireplus.app import sounds
from solitaireplus.app import window
from solitaireplus.menus import main_menu
from solitaireplus.menus import options_screen
from solitaireplus.games.arcade import machine_music
from solitaireplus.games.dead_mans_hand import game_screen
from solitaireplus.games.casino import horse_races_screen
from solitaireplus.games.solitaire import screen as solitaire_screen
from solitaireplus.profile import level_up
from solitaireplus.profile import leveling
from solitaireplus.app.lazy import lazy
five_card_draw_ui = lazy("solitaireplus.games.poker.five_card_draw_ui")

SCREENS = {
    state_names.STATE_DEBUG_POKER_NPC_SELECT: "solitaireplus.debug.poker_select_screen",
    state_names.STATE_DEBUG_MENU: "solitaireplus.debug.menu_screen",
    state_names.STATE_SPLASH: "solitaireplus.menus.splash",
    state_names.STATE_PROFILE_SELECT: "solitaireplus.profile.profile_select",
    state_names.STATE_MENU: "solitaireplus.menus.main_menu",
    state_names.STATE_MODE_SELECT: "solitaireplus.menus.mode_select",
    state_names.STATE_CASE_OPENING: "solitaireplus.career.case_opening_screen",
    state_names.STATE_CRYPTID_CREATURES: "solitaireplus.games.cryptid.collection_screen",
    state_names.STATE_FREE_PLAY_SELECT: "solitaireplus.menus.free_play_select",
    state_names.STATE_CAREER_ACTIVITY: "solitaireplus.career.activity_screen",
    state_names.STATE_CAREER_HUB: "solitaireplus.career.hub_screen",
    state_names.STATE_SCORE_FOUR_MODE_SELECT: "solitaireplus.games.cards.score_four_screen:score_four_mode_select",
    state_names.STATE_SCORE_FOUR_OPPONENT_SELECT: "solitaireplus.games.cards.score_four_screen:score_four_opponent_select",
    state_names.STATE_SEVEN_CARD_STUD_BUY_IN: "solitaireplus.games.poker.seven_card_stud_screen:seven_card_stud_buy_in",
    state_names.STATE_SEVEN_CARD_STUD: "solitaireplus.games.poker.seven_card_stud_screen:seven_card_stud",
    state_names.STATE_FIVE_CARD_DRAW_BUY_IN: "solitaireplus.games.poker.five_card_draw_screen:five_card_draw_buy_in",
    state_names.STATE_FIVE_CARD_DRAW: "solitaireplus.games.poker.five_card_draw_screen:five_card_draw",
    state_names.STATE_TEXAS_HOLDEM_BUY_IN: "solitaireplus.games.poker.holdem_screen:texas_holdem_buy_in",
    state_names.STATE_TEXAS_HOLDEM: "solitaireplus.games.poker.holdem_screen:texas_holdem",
    state_names.STATE_BLACKJACK_BET: "solitaireplus.games.casino.blackjack_screen:blackjack_bet",
    state_names.STATE_BLACKJACK: "solitaireplus.games.casino.blackjack_screen:blackjack",
    state_names.STATE_ROULETTE: "solitaireplus.games.casino.roulette_screen",
    state_names.STATE_HORSE_RACES: "solitaireplus.games.casino.horse_races_screen",
    state_names.STATE_FARO: "solitaireplus.games.casino.faro_screen",
    state_names.STATE_FIVE_O_POKER: "solitaireplus.games.poker.five_o_screen",
    state_names.STATE_BLIND_MANS_BLUFF: "solitaireplus.games.poker.blind_mans_bluff_screen",
    state_names.STATE_CRAZY_EIGHTS: "solitaireplus.games.cards.crazy_eights_screen",
    state_names.STATE_BANGO: "solitaireplus.games.cards.bango_screen",
    state_names.STATE_SCORE_FOUR: "solitaireplus.games.cards.score_four_screen:score_four",
    state_names.STATE_ACHIEVEMENTS: "solitaireplus.menus.achievements_screen",
    state_names.STATE_HOW_TO_PLAY: "solitaireplus.menus.help_screen",
    state_names.STATE_CAREER_JOBS: "solitaireplus.career.jobs_screen",
    state_names.STATE_CAREER_LEADERBOARD_BIO: "solitaireplus.career.leaderboard_bio_screen",
    state_names.STATE_CAREER_LEADERBOARDS: "solitaireplus.career.leaderboards_screen",
    state_names.STATE_CAREER_NEWS: "solitaireplus.career.news_screen",
    state_names.STATE_CAREER_EVENT: "solitaireplus.career.events.event_screen",
    state_names.STATE_CAREER_EVENT_SUMMARY: "solitaireplus.career.events.summary_screen",
    state_names.STATE_CAREER_EVENT_SELECT: "solitaireplus.career.events.event_select_screen",
    state_names.STATE_KING_PONG_OPPONENT_SELECT: "solitaireplus.games.arcade.machine_select:king_pong_opponent_select",
    state_names.STATE_BATTLE_BOSSES_OPPONENT_SELECT: "solitaireplus.games.arcade.machine_select:battle_bosses_opponent_select",
    state_names.STATE_ACE_INVADERS_DIFFICULTY_SELECT: "solitaireplus.games.arcade.machine_select:ace_invaders_difficulty_select",
    state_names.STATE_SUIT_SNAKE_DIFFICULTY_SELECT: "solitaireplus.games.arcade.machine_select:suit_snake_difficulty_select",
    state_names.STATE_ARCADE_TOKEN_EXCHANGE: "solitaireplus.games.arcade.hub_screens:arcade_token_exchange",
    state_names.STATE_ARCADE_PRIZE_COUNTER: "solitaireplus.games.arcade.hub_screens:arcade_prize_counter",
    state_names.STATE_ARCADE_TROPHY_ROOM: "solitaireplus.games.arcade.hub_screens:arcade_trophy_room",
    state_names.STATE_KING_PONG: "solitaireplus.games.arcade.machine_screens:king_pong",
    state_names.STATE_BATTLE_BOSSES: "solitaireplus.games.arcade.machine_screens:battle_bosses",
    state_names.STATE_ACE_INVADERS: "solitaireplus.games.arcade.machine_screens:ace_invaders",
    state_names.STATE_SUIT_SNAKE: "solitaireplus.games.arcade.machine_screens:suit_snake",
    state_names.STATE_DEAD_MANS_HAND: "solitaireplus.games.dead_mans_hand.game_screen",
    state_names.STATE_CAREER_REAL_ESTATE: "solitaireplus.career.real_estate_screen",
    state_names.STATE_DIFFICULTY: "solitaireplus.menus.difficulty_screen",
    state_names.STATE_OPTIONS: "solitaireplus.menus.options_screen",
    state_names.STATE_CUSTOMIZE: "solitaireplus.menus.customize",
    state_names.STATE_RECAP: "solitaireplus.profile.recap",
    state_names.STATE_LEVEL_UP: "solitaireplus.profile.level_up",
    state_names.STATE_PROFILE: "solitaireplus.profile.profile_editor",
    state_names.STATE_PLAYING: "solitaireplus.games.solitaire.screen",
}

# Screens the old loop drew in its second draw chain, after the timed poker turns. That chain
# looked at current_state again, which the first chain may have changed.
DRAWN_LATE = {state_names.STATE_DEBUG_POKER_NPC_SELECT, state_names.STATE_DEBUG_MENU, state_names.STATE_LEVEL_UP, state_names.STATE_PLAYING}


class _LegacyScreen:
    """A screen in a module that holds several screens: its code is that module's loop_event_<screen>,
    loop_draw_<screen>, ... functions (the naming the screens had in the old legacy.py)."""

    def __init__(self, module, slug, draws_late):
        self.handle_event = getattr(module, f"loop_event_{slug}", None)
        self.draw = getattr(module, f"loop_draw_{slug}", None)
        self.late_update = getattr(module, f"loop_late_{slug}", None)
        self.enter = getattr(module, f"loop_enter_{slug}", None)
        self.leave = getattr(module, f"loop_leave_{slug}", None)
        self.update = None
        self.DRAWS_LATE = draws_late


_loaded = {}


def screen_for(name):
    """The screen object for a screen name (None for a name without code)."""
    if name not in _loaded:
        target = SCREENS.get(name)
        if target is None:
            _loaded[name] = None
        elif ":" in target:
            module_name, slug = target.split(":", 1)
            _loaded[name] = _LegacyScreen(importlib.import_module(module_name), slug, name in DRAWN_LATE)
        else:
            _loaded[name] = importlib.import_module(target)
    return _loaded[name]


def run_screen_hooks(entered_state):
    """If state.current_state is no longer `entered_state`, run the old screen's leave() and the
    new screen's enter(). Returns the screen name now entered (pass it in next time)."""
    new_state = state.current_state
    if new_state == entered_state:
        return entered_state
    old_screen = screen_for(entered_state)
    if old_screen is not None and getattr(old_screen, "leave", None) is not None:
        old_screen.leave()
    new_screen = screen_for(new_state)
    if new_screen is not None and getattr(new_screen, "enter", None) is not None:
        new_screen.enter()
    return new_state


def typing_in_a_text_field():
    """True while a text field of the current screen has the keyboard focus: the F10 debug menu
    hotkey then does nothing (D1), and the key goes to the screen like any other key.

    The text fields: the Profile screen's name, country, age, hometown and bio, and the manual
    bet boxes at the Hold'em and Five-Card Draw tables. (The Cryptid collection's search box has
    no focus, every key types into it, so it does not hold F10 back.)
    """
    if state.current_state == state_names.STATE_PROFILE:
        return bool(state.profile_name_active or state.profile_country_active or state.profile_age_active
                    or state.profile_hometown_active or state.profile_bio_active)
    if state.current_state == state_names.STATE_TEXAS_HOLDEM:
        return bool(state.holdem_manual_bet_active)
    if state.current_state == state_names.STATE_FIVE_CARD_DRAW:
        return bool(five_card_draw_ui.five_card_draw_manual_bet_active())
    return False


def loop_post_event_updates():
    """Old per-frame updates between the event loop and drawing."""
    solitaire_screen.update_solitaire_round()

    if (
            state.current_state != state_names.STATE_HORSE_RACES
            and state.horse_race_music_channel is not None
    ):
        horse_races_screen.stop_horse_race_music(300)

    # Non-Solitaire games award XP too. If that XP crossed a level threshold,
    # wait until the player has safely returned to a hub/selection screen before
    # presenting the queued level-up cards.
    if (
            state.level_up_queue
            and state.current_level_up_data is None
            and state.current_state in (
                state_names.STATE_MENU,
                state_names.STATE_CAREER_HUB,
                state_names.STATE_CAREER_EVENT_SELECT,
                state_names.STATE_FREE_PLAY_SELECT,
            )
    ):
        state.post_round_return_state = state.current_state
        level_up.advance_level_up_screen()


def run():

    # ==================================================
    # MAIN LOOP // EVENT STATE CHAIN
    # ==================================================

    options_screen.apply_saved_app_settings()
    if options_screen.app_settings.get("auto_update_check"):
        main_menu.update_checker.start()

    state.running = True
    entered_state = None   # the screen whose enter() ran last (the first frame enters the first screen)
    last_pointer_event = None   # position of the last mouse event, not clamped to the picture
    pointer_in_window = True

    while state.running:

        # A screen change made outside the event loop (per-frame updates, draw chains).
        entered_state = run_screen_hooks(entered_state)

        # Saved Options are written shortly after they change (only while the Options
        # screen is open, so temporary changes like horse-race music ducking are not saved).
        main_menu.update_checker.poll()
        if state.current_state == state_names.STATE_OPTIONS:
            options_screen.app_settings.update(options_screen.current_app_settings_values())
        else:
            options_screen.app_settings.tick()

        # Keep the soundtrack aligned with the active arcade cabinet. Selection,
        # token exchange, prize counter, and the rest of Career use the player's
        # normal Instrumental/Ambient choice; only live machine gameplay overrides
        # it when that cabinet has a custom track installed.
        active_machine_track = (
            machine_music.ARCADE_MACHINE_MUSIC_BY_STATE.get(state.current_state)
            if state.arcade_placeholder_music_enabled
            else None
        )
        sounds.audio.sync_machine_music(
            state.current_state if active_machine_track else None,
            active_machine_track,
        )
        sounds.audio.update()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                state.running = False

            sounds.audio.handle_event(
                event
            )

            # ==================================================
            # GLOBAL FULLSCREEN HOTKEY
            # ==================================================

            if (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_F11
            ):
                window.set_fullscreen_enabled(
                    not state.fullscreen_enabled
                )
                options_screen.app_settings.update({"fullscreen": state.fullscreen_enabled})
                continue

            # ==================================================
            # GLOBAL DEBUG MENU HOTKEY
            # ==================================================

            if (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_F10
                    and not typing_in_a_text_field()
            ):

                print(
                    "F10 DEBUG MENU"
                )

                if state.current_state == state_names.STATE_DEBUG_MENU:

                    actions.close_debug_menu()   # the same way back as the menu's Close button (B59)

                else:

                    state.debug_previous_state = state.current_state
                    if state.current_state == state_names.STATE_DEAD_MANS_HAND:
                        game_screen.dead_mans_hand_game.release_mouse()

                    state.current_state = state_names.STATE_DEBUG_MENU

                entered_state = run_screen_hooks(entered_state)
                continue

            state.game_mouse_pos = None

            if hasattr(
                event,
                "pos"
            ):
                state.game_mouse_pos = (
                    window.window_to_game_coords(
                        event.pos
                    )
                )

            if state.game_mouse_pos is not None:
                state.menu_mouse_pos = state.game_mouse_pos
                last_pointer_event = state.game_mouse_pos
                pointer_in_window = True
            elif event.type == pygame.WINDOWLEAVE:
                pointer_in_window = False      # nothing hovers while the mouse is outside the window
            elif event.type == pygame.WINDOWENTER:
                pointer_in_window = True

            screen = screen_for(state.current_state)
            if screen is not None and screen.handle_event is not None:
                screen.handle_event(window.translate_event(event))   # mouse positions in game coordinates

            entered_state = run_screen_hooks(entered_state)

        loop_post_event_updates()

        # Drawing uses where the mouse is this frame, not the last event's position (which is
        # None after a key press, so nothing would be hovered until the mouse moved).
        state.mouse_pos = window.window_to_game_coords(pygame.mouse.get_pos())
        if last_pointer_event is not None and not (
                0 <= last_pointer_event[0] < window.game_surface.get_width()
                and 0 <= last_pointer_event[1] < window.game_surface.get_height()):
            # The pointer is in a letterbox bar: keep the real (outside) position the last
            # event reported, so nothing along the picture's edge is hovered.
            state.mouse_pos = last_pointer_event
        if not pointer_in_window:
            state.mouse_pos = None
        state.game_mouse_pos = state.mouse_pos
        if state.mouse_pos is not None:
            state.menu_mouse_pos = state.mouse_pos

        # First draw chain: per-frame update, then draw.
        screen = screen_for(state.current_state)
        if screen is not None:
            if getattr(screen, "update", None) is not None:
                screen.update(pygame.time.get_ticks())
            if getattr(screen, "draw", None) is not None and not getattr(screen, "DRAWS_LATE", False):
                screen.draw()

        # Second draw chain (looks at current_state again): timed poker turns, and the screens
        # that are drawn late (debug menus, level-up, Solitaire).
        screen = screen_for(state.current_state)
        if screen is not None:
            if getattr(screen, "late_update", None) is not None:
                screen.late_update()
            elif getattr(screen, "draw", None) is not None and getattr(screen, "DRAWS_LATE", False):
                screen.draw()


        leveling.update_achievement_popup()
        if state.achievement_popup_current is not None:
            draw_achievement_popup(
                window.game_surface,
                state.achievement_popup_current,
                pygame.time.get_ticks() - state.achievement_popup_started,
                state.achievement_popup_fans,
                state.achievement_popup_cosmetic,
                fonts.option_label_font,
                fonts.difficulty_detail_font,
            )

        window.present()



        # The arcade machines move by the real length of the frame (B49).
        state.frame_dt = window.clock.tick(
            window.FPS
        ) / 1000.0



    options_screen.app_settings.flush()
    pygame.quit()
