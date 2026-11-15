"""Blind Man's Bluff screen and sessions (moved out of legacy.py)."""
from solitaireplus.games.poker.blind_mans_bluff_ui import ACTION_BET as BLUFF_ACTION_BET
from solitaireplus.games.poker.blind_mans_bluff_ui import ACTION_CALL as BLUFF_ACTION_CALL
from solitaireplus.games.poker.blind_mans_bluff_ui import ACTION_CHECK as BLUFF_ACTION_CHECK
from solitaireplus.games.poker.blind_mans_bluff_ui import ACTION_FOLD as BLUFF_ACTION_FOLD
from solitaireplus.games.poker.blind_mans_bluff_ui import ACTION_NEXT_HAND as BLUFF_ACTION_NEXT_HAND
from solitaireplus.games.poker.blind_mans_bluff_ui import ACTION_RAISE as BLUFF_ACTION_RAISE
from solitaireplus.games.poker.blind_mans_bluff_ui import ACTION_RETURN as BLUFF_ACTION_RETURN
from solitaireplus.games.poker.blind_mans_bluff import BlindMansBluffGame
from solitaireplus.career import career_rewards
from solitaireplus.games.poker.blind_mans_bluff_ui import draw_blind_mans_bluff
from solitaireplus.games.poker.blind_mans_bluff_ui import get_blind_mans_bluff_action
from solitaireplus.games.poker.blind_mans_bluff_ui import get_blind_mans_bluff_bet_amount
from solitaireplus.games.poker.variant_quick_chat import reset_variant_quick_chat
from solitaireplus.npc.manager import get_random_npc_group
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.career.session_summary import track_night_cash
from solitaireplus.games.poker.bluff_presentation import update_bluff_presentation
from solitaireplus.app.lazy import lazy
table_stakes = lazy("solitaireplus.games.poker.table_stakes")
holdem_screen = lazy("solitaireplus.games.poker.holdem_screen")
holdem_ui = lazy("solitaireplus.games.poker.holdem_ui")
training = lazy("solitaireplus.career.training")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
panels = lazy("solitaireplus.ui.panels")
night = lazy("solitaireplus.career.events.night")
leveling = lazy("solitaireplus.profile.leveling")
fonts = lazy("solitaireplus.app.fonts")


blind_mans_bluff_game = BlindMansBluffGame()


def start_blind_mans_bluff_session(starting_stack=None):

    if starting_stack is None:
        starting_stack = table_stakes.get_niche_poker_starting_stack(
            table_stakes.BLIND_MANS_BLUFF_MIN_BUY_IN
        )

    starting_stack = min(max(0, int(starting_stack)), state.career_cash)
    if starting_stack < table_stakes.BLIND_MANS_BLUFF_MIN_BUY_IN:
        return False

    opponents = get_random_npc_group(3)
    if len(opponents) < 3:
        return False

    state.career_cash -= starting_stack
    state.blind_mans_bluff_starting_stack = starting_stack
    state.blind_mans_bluff_session_net = 0
    state.blind_mans_bluff_buy_in_active = True
    blind_mans_bluff_game.session_xp_rewarded = False

    blind_mans_bluff_game.learning_store = legacy.game_namespace().get("career_poker_learning") if state.current_game_mode == "career" else None
    # The last session's Quick Chat menu, queued replies and history do not carry over.
    reset_variant_quick_chat("blind_mans_bluff")
    if not blind_mans_bluff_game.start_session(opponents, starting_stack):
        state.career_cash += starting_stack
        state.blind_mans_bluff_buy_in_active = False
        return False

    state.career_event_has_activity = True
    state.current_state = state_names.STATE_BLIND_MANS_BLUFF
    sounds.audio.play_sound("card_shuffle")
    return True


def finish_blind_mans_bluff_session():

    if state.blind_mans_bluff_buy_in_active:
        state.career_cash += blind_mans_bluff_game.player_stack
        state.blind_mans_bluff_session_net = (
            blind_mans_bluff_game.player_stack
            - state.blind_mans_bluff_starting_stack
        )
        state.blind_mans_bluff_buy_in_active = False

    if blind_mans_bluff_game.hands_played > 0:
        state.career_event_has_activity = True

    won_bluff_session = (
        state.blind_mans_bluff_session_net > 0
        or blind_mans_bluff_game.hands_won > blind_mans_bluff_game.hands_lost
    )

    if (
            blind_mans_bluff_game.hands_played > 0
            and not getattr(blind_mans_bluff_game, "session_xp_rewarded", False)
    ):
        leveling.award_game_xp("blind_mans_bluff", won=won_bluff_session)
        blind_mans_bluff_game.session_xp_rewarded = True

    if (
            state.current_game_mode == "career"
            and blind_mans_bluff_game.hands_played > 0
            and not blind_mans_bluff_game.reward_claimed
    ):
        if state.blind_mans_bluff_session_net > 0:
            reward_key = "profit"
        elif state.blind_mans_bluff_session_net == 0:
            reward_key = "break_even"
        else:
            reward_key = "loss"

        rating_gain = training.TRAINING_RATING_REWARDS["blind_mans_bluff"][reward_key]
    
        won_session = won_bluff_session
        if won_session:
            career_rewards.award_fans_for_rating_win(
                rating_gain,
                "Blind Man's Bluff session"
            )

        night.record_career_event_result(
            "blind_mans_bluff",
            won=won_session,
            net=state.blind_mans_bluff_session_net,
            hands=blind_mans_bluff_game.hands_played,
            hands_won=blind_mans_bluff_game.hands_won,
        )
        track_night_cash(legacy.game_namespace(), "blind_mans_bluff", state.blind_mans_bluff_session_net)
        blind_mans_bluff_game.reward_claimed = True

    if state.current_game_mode == "free":
        legacy.finish_free_play_sandbox()
        state.current_state = state_names.STATE_FREE_PLAY_SELECT
    else:
        state.current_state = state_names.STATE_CAREER_EVENT_SELECT


def handle_event(event):
    """Old main-loop event branch for STATE_BLIND_MANS_BLUFF."""

    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):
        bluff_action = get_blind_mans_bluff_action(
            state.game_mouse_pos,
            blind_mans_bluff_game
        )

        if bluff_action == BLUFF_ACTION_RETURN:
            sounds.audio.play_sound("button_click")
            finish_blind_mans_bluff_session()

        elif bluff_action == BLUFF_ACTION_NEXT_HAND:
            if blind_mans_bluff_game.start_hand():
                sounds.audio.play_sound("card_shuffle")

        elif bluff_action == BLUFF_ACTION_CHECK:
            if blind_mans_bluff_game.player_check():
                sounds.audio.play_sound("poker_check")

        elif bluff_action == BLUFF_ACTION_BET:
            bluff_bet_amount = get_blind_mans_bluff_bet_amount(
                blind_mans_bluff_game
            )
            if blind_mans_bluff_game.player_bet(bluff_bet_amount):
                holdem_screen.play_texas_holdem_chip_sound()

        elif bluff_action == BLUFF_ACTION_RAISE:
            amount = get_blind_mans_bluff_bet_amount(blind_mans_bluff_game)
            if blind_mans_bluff_game.player_raise(amount):
                holdem_screen.play_texas_holdem_chip_sound()

        elif bluff_action == BLUFF_ACTION_CALL:
            if blind_mans_bluff_game.player_call():
                holdem_screen.play_texas_holdem_chip_sound()

        elif bluff_action == BLUFF_ACTION_FOLD:
            if blind_mans_bluff_game.player_fold():
                sounds.audio.play_sound("button_click")


def sync_npc_delay(game):
    """Pace the NPC turns by the table speed (as at the Hold'em tables)."""
    game.npc_delay_seconds = holdem_ui.get_holdem_npc_delay() / 1000


def draw():
    """Old draw-chain branch for STATE_BLIND_MANS_BLUFF."""

    # A due NPC turn runs before the presentation, so its chips and sounds show this frame.
    sync_npc_delay(blind_mans_bluff_game)
    blind_mans_bluff_game.update()
    update_bluff_presentation(blind_mans_bluff_game, sounds.audio.play_sound)
    draw_blind_mans_bluff(
        window.game_surface,
        state.game_mouse_pos,
        blind_mans_bluff_game,
        state.player_name,
        panels.draw_submenu_background,
        fonts.options_title_font,
        fonts.option_label_font,
        fonts.difficulty_detail_font,
        card_fronts=legacy.game.card_fronts,
        card_back_surface=legacy.game.get_card_back_surface(),
    )
