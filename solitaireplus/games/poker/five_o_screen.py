"""Five-O Poker screen and sessions (moved out of legacy.py)."""
from solitaireplus.games.poker.five_o_ui import ACTION_BET as FIVE_O_ACTION_BET
from solitaireplus.games.poker.five_o_ui import ACTION_CALL as FIVE_O_ACTION_CALL
from solitaireplus.games.poker.five_o_ui import ACTION_CHECK as FIVE_O_ACTION_CHECK
from solitaireplus.games.poker.five_o_ui import ACTION_COLUMN_PREFIX as FIVE_O_ACTION_COLUMN_PREFIX
from solitaireplus.games.poker.five_o_ui import ACTION_FOLD as FIVE_O_ACTION_FOLD
from solitaireplus.games.poker.five_o_ui import ACTION_NEXT_HAND as FIVE_O_ACTION_NEXT_HAND
from solitaireplus.games.poker.five_o_ui import ACTION_RETURN as FIVE_O_ACTION_RETURN
from solitaireplus.games.poker.five_o import FiveOPokerGame
from solitaireplus.career import career_rewards
from solitaireplus.games.poker.five_o_ui import draw_five_o_poker
from solitaireplus.games.poker.five_o_ui import get_five_o_action
from solitaireplus.games.poker.variant_quick_chat import reset_variant_quick_chat
from solitaireplus.npc.manager import get_random_npc
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.career.session_summary import track_night_cash
from solitaireplus.app.lazy import lazy
table_stakes = lazy("solitaireplus.games.poker.table_stakes")
holdem_screen = lazy("solitaireplus.games.poker.holdem_screen")
holdem_ui = lazy("solitaireplus.games.poker.holdem_ui")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
panels = lazy("solitaireplus.ui.panels")
night = lazy("solitaireplus.career.events.night")
leveling = lazy("solitaireplus.profile.leveling")
fonts = lazy("solitaireplus.app.fonts")


five_o_poker_game = FiveOPokerGame()

def start_five_o_poker_session(starting_stack=None):

    if starting_stack is None:
        starting_stack = table_stakes.get_niche_poker_starting_stack(
            table_stakes.FIVE_O_POKER_MIN_BUY_IN
        )

    starting_stack = min(max(0, int(starting_stack)), state.career_cash)
    if starting_stack < table_stakes.FIVE_O_POKER_MIN_BUY_IN:
        return False

    opponent = get_random_npc()
    if opponent is None:
        return False

    state.career_cash -= starting_stack
    state.five_o_poker_starting_stack = starting_stack
    state.five_o_poker_session_net = 0
    state.five_o_poker_buy_in_active = True
    five_o_poker_game.session_xp_rewarded = False

    five_o_poker_game.learning_store = legacy.game_namespace().get("career_poker_learning") if state.current_game_mode == "career" else None
    # The last session's Quick Chat menu, queued replies and history do not carry over.
    reset_variant_quick_chat("five_o_poker")
    if not five_o_poker_game.start_session(opponent, starting_stack):
        state.career_cash += starting_stack
        state.five_o_poker_buy_in_active = False
        return False

    state.career_event_has_activity = True
    state.current_state = state_names.STATE_FIVE_O_POKER
    sounds.audio.play_sound("card_shuffle")
    return True


def finish_five_o_poker_session():

    if state.five_o_poker_buy_in_active:
        state.career_cash += five_o_poker_game.player_stack
        state.five_o_poker_session_net = (
            five_o_poker_game.player_stack - state.five_o_poker_starting_stack
        )
        state.five_o_poker_buy_in_active = False

    if five_o_poker_game.hands_played > 0:
        state.career_event_has_activity = True

    won_five_o_session = (
        state.five_o_poker_session_net > 0
        or five_o_poker_game.hands_won > five_o_poker_game.hands_lost
    )

    if (
            five_o_poker_game.hands_played > 0
            and not getattr(five_o_poker_game, "session_xp_rewarded", False)
    ):
        leveling.award_game_xp("five_o_poker", won=won_five_o_session)
        five_o_poker_game.session_xp_rewarded = True

    if (
            state.current_game_mode == "career"
            and five_o_poker_game.hands_played > 0
            and not five_o_poker_game.reward_claimed
    ):
        rating_gain = career_rewards.rate_poker_cash_out(
            "five_o_poker",
            five_o_poker_game,
        )

        won_session = won_five_o_session
        if won_session:
            career_rewards.award_fans_for_rating_win(
                rating_gain,
                "Five-O Poker session"
            )

        night.record_career_event_result(
            "five_o_poker",
            won=won_session,
            net=state.five_o_poker_session_net,
            hands=five_o_poker_game.hands_played,
            hands_won=five_o_poker_game.hands_won,
            five_o_wins=five_o_poker_game.five_o_wins,
            rating_reward=rating_gain,
        )
        track_night_cash(legacy.game_namespace(), "five_o_poker", state.five_o_poker_session_net)
        five_o_poker_game.reward_claimed = True

    if state.current_game_mode == "free":
        legacy.finish_free_play_sandbox()
        state.current_state = state_names.STATE_FREE_PLAY_SELECT
    else:
        state.current_state = state_names.STATE_CAREER_EVENT_SELECT


def handle_event(event):
    """Old main-loop event branch for STATE_FIVE_O_POKER."""

    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):
        five_o_action = get_five_o_action(
            state.game_mouse_pos,
            five_o_poker_game
        )

        if five_o_action == "ui_click":
            sounds.audio.play_sound("button_click")

        elif five_o_action == FIVE_O_ACTION_RETURN:
            sounds.audio.play_sound("button_click")
            finish_five_o_poker_session()

        elif five_o_action == FIVE_O_ACTION_NEXT_HAND:
            if five_o_poker_game.start_hand():
                sounds.audio.play_sound("card_shuffle")

        elif (
                five_o_action is not None
                and five_o_action.startswith(FIVE_O_ACTION_COLUMN_PREFIX)
        ):
            try:
                state.column_index = int(
                    five_o_action[len(FIVE_O_ACTION_COLUMN_PREFIX):]
                )
            except ValueError:
                state.column_index = -1
            if five_o_poker_game.place_player_card(state.column_index):
                sounds.audio.play_sound("card_move")

        elif five_o_action == FIVE_O_ACTION_CHECK:
            if five_o_poker_game.player_check():
                sounds.audio.play_sound("poker_check")

        elif five_o_action == FIVE_O_ACTION_BET:
            if five_o_poker_game.player_bet():
                holdem_screen.play_texas_holdem_chip_sound()

        elif five_o_action == FIVE_O_ACTION_CALL:
            if five_o_poker_game.player_call():
                holdem_screen.play_texas_holdem_chip_sound()

        elif five_o_action == FIVE_O_ACTION_FOLD:
            if five_o_poker_game.player_fold():
                sounds.audio.play_sound("button_click")


def sync_npc_delay(game):
    """Pace the NPC's betting decisions by the table speed (as at the Hold'em tables)."""
    game.npc_delay_seconds = holdem_ui.get_holdem_npc_delay() / 1000


def draw():
    """Old draw-chain branch for STATE_FIVE_O_POKER."""

    sync_npc_delay(five_o_poker_game)
    five_o_poker_game.update()

    draw_five_o_poker(
        window.game_surface,
        state.game_mouse_pos,
        five_o_poker_game,
        state.player_name,
        panels.draw_submenu_background,
        fonts.options_title_font,
        fonts.option_label_font,
        fonts.difficulty_detail_font,
        card_fronts=legacy.game.card_fronts,
        card_back_surface=legacy.game.get_card_back_surface(),
    )
