"""The F10 debug menu screen (moved out of legacy.py)."""
from solitaireplus.debug.menu import ACTION_ACE_INVADERS
from solitaireplus.debug.menu import ACTION_ACHIEVEMENT_TEST
from solitaireplus.debug.menu import ACTION_ADD_CASH
from solitaireplus.debug.menu import ACTION_ADD_PRODIGY
from solitaireplus.debug.menu import ACTION_ADD_PROSPECT
from solitaireplus.debug.menu import ACTION_ADD_RATING
from solitaireplus.debug.menu import ACTION_ADD_XP
from solitaireplus.debug.menu import ACTION_ADVANCE_CAREER_DAY
from solitaireplus.debug.menu import ACTION_ARCADE_NIGHT
from solitaireplus.debug.menu import ACTION_BANGO
from solitaireplus.debug.menu import ACTION_BATTLE_BOSSES
from solitaireplus.debug.menu import ACTION_BLACKJACK
from solitaireplus.debug.menu import ACTION_BLIND_MANS_BLUFF
from solitaireplus.debug.menu import ACTION_CAREER_HUB
from solitaireplus.debug.menu import ACTION_CAREER_YEAR
from solitaireplus.debug.menu import ACTION_CASINO_NIGHT
from solitaireplus.debug.menu import ACTION_CASUAL_CARDS
from solitaireplus.debug.menu import ACTION_CHALLENGE_ALL_OR_NOTHING
from solitaireplus.debug.menu import ACTION_CHALLENGE_DRAW_3
from solitaireplus.debug.menu import ACTION_CHALLENGE_NO_HINTS
from solitaireplus.debug.menu import ACTION_CHALLENGE_NO_UNDO
from solitaireplus.debug.menu import ACTION_CLOSE
from solitaireplus.debug.menu import ACTION_CRAZY_EIGHTS
from solitaireplus.debug.menu import ACTION_DEAD_MANS_HAND
from solitaireplus.debug.menu import ACTION_FARO
from solitaireplus.debug.menu import ACTION_FIVE_CARD_DRAW
from solitaireplus.debug.menu import ACTION_FIVE_O_POKER
from solitaireplus.debug.menu import ACTION_HEAD_TO_HEAD
from solitaireplus.debug.menu import ACTION_HORSE_RACES
from solitaireplus.debug.menu import ACTION_KING_PONG
from solitaireplus.debug.menu import ACTION_LEVEL_10
from solitaireplus.debug.menu import ACTION_LEVEL_3
from solitaireplus.debug.menu import ACTION_LEVEL_6
from solitaireplus.debug.menu import ACTION_LEVEL_MAX
from solitaireplus.debug.menu import ACTION_NEW_CAREER_MONTH
from solitaireplus.debug.menu import ACTION_POKER_NIGHT
from solitaireplus.debug.menu import ACTION_ROULETTE
from solitaireplus.debug.menu import ACTION_SCORE_FOUR_COMPETITIVE
from solitaireplus.debug.menu import ACTION_SCORE_FOUR_SOLO
from solitaireplus.debug.menu import ACTION_SEVEN_CARD_STUD
from solitaireplus.debug.menu import ACTION_SUB_RATING
from solitaireplus.debug.menu import ACTION_SUIT_SNAKE
from solitaireplus.debug.menu import ACTION_TEXAS_HOLDEM
from solitaireplus.debug.menu import ACTION_WIN_SOLITAIRE_ROUND
from solitaireplus.debug.menu import ACTION_ZERO_CASH
from solitaireplus.debug.menu import CAREER_HUB_JUMP_ACTIONS as DEBUG_CAREER_HUB_JUMP_ACTIONS
from solitaireplus.debug.menu import LAUNCH_ACTIONS as DEBUG_LAUNCH_ACTIONS
from solitaireplus.app.settings import LEVEL_XP_THRESHOLDS
from solitaireplus.debug.menu import draw_debug_menu
from solitaireplus.debug.game_mode import end_debug_game_mode
from solitaireplus.debug.menu import get_debug_action
from solitaireplus.debug.menu import is_minigame_category_action
import pygame
from solitaireplus.debug.menu import show_debug_message
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.debug.menu import toggle_minigame_category
from solitaireplus.app.lazy import lazy
game_screen = lazy("solitaireplus.games.dead_mans_hand.game_screen")
actions = lazy("solitaireplus.debug.actions")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
panels = lazy("solitaireplus.ui.panels")
leveling = lazy("solitaireplus.profile.leveling")
horse_races_screen = lazy("solitaireplus.games.casino.horse_races_screen")
fonts = lazy("solitaireplus.app.fonts")
five_o_screen = lazy("solitaireplus.games.poker.five_o_screen")
faro_screen = lazy("solitaireplus.games.casino.faro_screen")
calendar = lazy("solitaireplus.career.calendar")
buttons = lazy("solitaireplus.ui.buttons")
blind_mans_bluff_screen = lazy("solitaireplus.games.poker.blind_mans_bluff_screen")
solitaire_screen = lazy("solitaireplus.games.solitaire.screen")


def solitaire_win_available():
    """The 'Win this Solitaire round' button works only when the menu was opened from the
    Solitaire table (D1), and not while its 'Restart this hand?' prompt is open (that prompt
    swallowed the old F8 key too)."""
    return (state.debug_previous_state == state_names.STATE_PLAYING
            and not solitaire_screen.solitaire_restart_prompt.open)


def handle_event(event):
    """Old main-loop event branch for STATE_DEBUG_MENU."""

    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):

        debug_action = (
            get_debug_action(
                state.game_mouse_pos
            )
        )

        # Every button that launches a game, night or career screen ends a running Free Play
        # sandbox first, so no later Career save (hub actions, the event select's Return...)
        # writes the sandbox cash (B21). The menu's own controls and Close keep the sandbox.
        if debug_action in DEBUG_LAUNCH_ACTIONS:
            actions.debug_end_free_play_sandbox()

        # A jump to the Career Hub also leaves the "debug" mode of a debug night the player
        # did not end, so the real hub never runs in "debug" mode (B22).
        if debug_action in DEBUG_CAREER_HUB_JUMP_ACTIONS:
            end_debug_game_mode()
            # The hub only runs Career nights: a mode left over from the main menu (None) would
            # record no results, like "debug".
            if state.current_game_mode != "career":
                state.current_game_mode = "career"

        # ==========================================
        # Expandable Minigames navigation
        # ==========================================

        if is_minigame_category_action(debug_action):
            sounds.audio.play_sound("button_click")
            toggle_minigame_category(debug_action)

        # ==========================================
        # Career / event navigation
        # ==========================================

        elif debug_action == ACTION_CAREER_HUB:
            sounds.audio.play_sound("button_click")
            state.current_state = state_names.STATE_CAREER_HUB

        elif debug_action == ACTION_CASUAL_CARDS:
            sounds.audio.play_sound("button_click")
            actions.debug_open_casual_cards()

        elif debug_action == ACTION_POKER_NIGHT:
            sounds.audio.play_sound("button_click")
            actions.debug_open_poker_night()

        elif debug_action == ACTION_CASINO_NIGHT:
            sounds.audio.play_sound("button_click")
            actions.debug_open_casino_night()

        elif debug_action == ACTION_HEAD_TO_HEAD:
            sounds.audio.play_sound("button_click")
            actions.debug_open_head_to_head()

        elif debug_action == ACTION_ADVANCE_CAREER_DAY:
            sounds.audio.play_sound("button_click")
            calendar.advance_career_day(
                completed=False
            )
            state.current_state = state_names.STATE_CAREER_HUB

        elif debug_action == ACTION_NEW_CAREER_MONTH:
            sounds.audio.play_sound("button_click")
            actions.debug_start_next_career_month()
            state.current_state = state_names.STATE_CAREER_HUB

        elif debug_action in (ACTION_ADD_PROSPECT, ACTION_ADD_PRODIGY):
            sounds.audio.play_sound("button_click")
            actions.debug_add_career_prospect(prodigy=debug_action == ACTION_ADD_PRODIGY)

        elif debug_action == ACTION_CAREER_YEAR:
            sounds.audio.play_sound("button_click")
            actions.debug_advance_career_year()
            state.current_state = state_names.STATE_CAREER_HUB

        # ==========================================
        # Solitaire challenges
        # ==========================================

        elif debug_action == ACTION_CHALLENGE_DRAW_3:
            sounds.audio.play_sound("button_click")
            actions.debug_open_solitaire_challenge(
                "draw_3"
            )

        elif debug_action == ACTION_CHALLENGE_NO_UNDO:
            sounds.audio.play_sound("button_click")
            actions.debug_open_solitaire_challenge(
                "no_undo"
            )

        elif debug_action == ACTION_CHALLENGE_NO_HINTS:
            sounds.audio.play_sound("button_click")
            actions.debug_open_solitaire_challenge(
                "no_hints"
            )

        elif debug_action == ACTION_CHALLENGE_ALL_OR_NOTHING:
            sounds.audio.play_sound("button_click")
            actions.debug_open_solitaire_challenge(
                "all_or_nothing"
            )

        elif debug_action == ACTION_WIN_SOLITAIRE_ROUND:
            # The designer's instant win (was the Solitaire F8 key, D1): back to the table, then
            # win the round. Opened from anywhere else, the button is disabled.
            if solitaire_win_available():
                sounds.audio.play_sound("button_click")
                actions.close_debug_menu()
                solitaire_screen.instant_win_round()

        # ==========================================
        # Minigames
        # ==========================================

        elif debug_action == ACTION_ARCADE_NIGHT:
            sounds.audio.play_sound("button_click")
            actions.debug_open_arcade_night()

        elif debug_action == ACTION_KING_PONG:
            sounds.audio.play_sound("button_click")
            actions.debug_open_king_pong()

        elif debug_action == ACTION_BATTLE_BOSSES:
            sounds.audio.play_sound("button_click")
            actions.debug_open_battle_bosses()

        elif debug_action == ACTION_ACE_INVADERS:
            sounds.audio.play_sound("button_click")
            actions.debug_open_ace_invaders()

        elif debug_action == ACTION_SUIT_SNAKE:
            sounds.audio.play_sound("button_click")
            actions.debug_open_suit_snake()

        elif debug_action == ACTION_DEAD_MANS_HAND:
            sounds.audio.play_sound("button_click")
            game_screen.start_dead_mans_hand(return_state=state_names.STATE_DEBUG_MENU)

        elif debug_action == ACTION_SCORE_FOUR_SOLO:
            sounds.audio.play_sound("button_click")
            actions.debug_open_score_four_solo()

        elif debug_action == ACTION_SCORE_FOUR_COMPETITIVE:
            sounds.audio.play_sound("button_click")
            actions.debug_open_score_four_competitive()

        elif debug_action == ACTION_CRAZY_EIGHTS:
            sounds.audio.play_sound("button_click")
            actions.debug_open_crazy_eights()

        elif debug_action == ACTION_BANGO:
            sounds.audio.play_sound("button_click")
            actions.debug_open_bango()

        elif debug_action == ACTION_FARO:
            sounds.audio.play_sound("button_click")
            if state.career_cash < 10:
                show_debug_message("Add cash to play")
            else:
                actions.debug_open_faro()

        elif debug_action == ACTION_FIVE_O_POKER:
            sounds.audio.play_sound("button_click")
            if not actions.debug_open_five_o_poker():
                show_debug_message("Add cash to play")

        elif debug_action == ACTION_BLIND_MANS_BLUFF:
            sounds.audio.play_sound("button_click")
            if not actions.debug_open_blind_mans_bluff():
                show_debug_message("Add cash to play")

        elif debug_action == ACTION_BLACKJACK:
            sounds.audio.play_sound("button_click")
            actions.debug_open_blackjack()

        elif debug_action == ACTION_ROULETTE:
            sounds.audio.play_sound("button_click")
            actions.debug_open_roulette()

        elif debug_action == ACTION_HORSE_RACES:
            sounds.audio.play_sound("button_click")
            if state.career_cash < 10:
                show_debug_message("Add cash to play")
            else:
                actions.debug_open_horse_races()

        elif debug_action == ACTION_TEXAS_HOLDEM:
            sounds.audio.play_sound("button_click")
            actions.open_debug_poker_npc_select("texas_holdem")

        elif debug_action == ACTION_FIVE_CARD_DRAW:
            sounds.audio.play_sound("button_click")
            actions.open_debug_poker_npc_select("five_card_draw")

        elif debug_action == ACTION_SEVEN_CARD_STUD:
            sounds.audio.play_sound("button_click")
            actions.open_debug_poker_npc_select("seven_card_stud")

        # ==========================================
        # Progression controls
        # ==========================================

        elif debug_action == ACTION_ADD_CASH:
            sounds.audio.play_sound("button_click")
            state.career_cash += 5000
            if state.debug_previous_state == state_names.STATE_FARO and not faro_screen.faro_game.cashed_out:
                faro_screen.faro_game.cash += 5000
                faro_screen.faro_game.starting_cash += 5000
            elif state.debug_previous_state == state_names.STATE_HORSE_RACES:
                horse_races_screen.horse_races_game.bankroll += 5000
                horse_races_screen.horse_races_game.starting_cash += 5000
            elif state.debug_previous_state == state_names.STATE_FIVE_O_POKER:
                five_o_screen.five_o_poker_game.player_stack += 5000
                five_o_screen.five_o_poker_game.starting_stack += 5000
                state.five_o_poker_starting_stack += 5000
            elif state.debug_previous_state == state_names.STATE_BLIND_MANS_BLUFF:
                blind_mans_bluff_screen.blind_mans_bluff_game.player_stack += 5000
                blind_mans_bluff_screen.blind_mans_bluff_game.starting_stack += 5000
                state.blind_mans_bluff_starting_stack += 5000
            print("Cash:", state.career_cash)

        elif debug_action == ACTION_ZERO_CASH:
            sounds.audio.play_sound("button_click")
            state.career_cash = 0
            print("Cash:", state.career_cash)

        elif debug_action == ACTION_ADD_RATING:
            sounds.audio.play_sound("button_click")
            actions.adjust_debug_ratings(100)
            print("Rating:", state.career_rating)

        elif debug_action == ACTION_SUB_RATING:
            sounds.audio.play_sound("button_click")
            actions.adjust_debug_ratings(-100)
            print("Rating:", state.career_rating)

        elif debug_action == ACTION_ADD_XP:
            sounds.audio.play_sound("button_click")
            leveling.add_player_xp(1000)
            print("XP:", state.player_xp, "Level:", state.player_level)

        elif debug_action == ACTION_LEVEL_3:
            sounds.audio.play_sound("button_click")
            actions.debug_set_player_level(3)
            print("Level:", state.player_level)

        elif debug_action == ACTION_LEVEL_6:
            sounds.audio.play_sound("button_click")
            actions.debug_set_player_level(6)
            print("Level:", state.player_level)

        elif debug_action == ACTION_LEVEL_10:
            sounds.audio.play_sound("button_click")
            actions.debug_set_player_level(10)
            print("Level:", state.player_level)

        elif debug_action == ACTION_LEVEL_MAX:
            sounds.audio.play_sound("button_click")
            actions.debug_set_player_level(
                max(LEVEL_XP_THRESHOLDS)
            )
            from solitaireplus.debug.unlocks import debug_unlock_everything
            unlock_summary = debug_unlock_everything(legacy.game_namespace())
            show_debug_message(
                "Max level + all current unlocks enabled"
            )
            print("Level:", state.player_level, "Unlocks:", unlock_summary)

        elif debug_action == ACTION_ACHIEVEMENT_TEST:
            sounds.audio.play_sound("button_click")
            unlocked_title = actions.debug_unlock_next_achievement()
            if unlocked_title:
                show_debug_message(
                    f"Unlocked: {unlocked_title}",
                    duration=2200,
                )
            else:
                show_debug_message("All achievements unlocked")

        # ==========================================
        # Close
        # ==========================================

        elif debug_action == ACTION_CLOSE:
            sounds.audio.play_sound("button_click")
            actions.close_debug_menu()   # like F10: back, recapturing the mouse in Dead Man's Hand (B59)

    return


def draw():
    """Old draw-chain branch for STATE_DEBUG_MENU."""

    draw_debug_menu(

        window.game_surface,

        state.game_mouse_pos,

        panels.draw_submenu_background,

        panels.draw_submenu_title,

        buttons.draw_menu_button,

        fonts.option_label_font,

        fonts.difficulty_detail_font,

        solitaire_win_available=solitaire_win_available(),

    )


# The old loop drew this screen in its second draw chain (see app/loop.py).
DRAWS_LATE = True
