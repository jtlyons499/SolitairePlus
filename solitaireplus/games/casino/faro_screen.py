"""Faro table screen (moved out of legacy.py)."""
from solitaireplus.games.casino.faro_ui import ACTION_BET_RANK_PREFIX as FARO_ACTION_BET_RANK_PREFIX
from solitaireplus.games.casino.faro_ui import ACTION_CHIP_10 as FARO_ACTION_CHIP_10
from solitaireplus.games.casino.faro_ui import ACTION_CHIP_100 as FARO_ACTION_CHIP_100
from solitaireplus.games.casino.faro_ui import ACTION_CHIP_50 as FARO_ACTION_CHIP_50
from solitaireplus.games.casino.faro_ui import ACTION_CHIP_500 as FARO_ACTION_CHIP_500
from solitaireplus.games.casino.faro_ui import ACTION_CLEAR_BETS as FARO_ACTION_CLEAR_BETS
from solitaireplus.games.casino.faro_ui import ACTION_DEAL as FARO_ACTION_DEAL
from solitaireplus.games.casino.faro_ui import ACTION_RETURN as FARO_ACTION_RETURN
from solitaireplus.games.casino.faro import FaroGame
from solitaireplus.career import career_rewards
from solitaireplus.games.casino.faro_ui import draw_faro
from solitaireplus.games.casino.faro_ui import get_faro_action
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.career.session_summary import track_night_cash
from solitaireplus.app.lazy import lazy
training = lazy("solitaireplus.career.training")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
panels = lazy("solitaireplus.ui.panels")
night = lazy("solitaireplus.career.events.night")
leveling = lazy("solitaireplus.profile.leveling")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")


faro_game = FaroGame()


def start_faro_session():

    state.faro_session_net = 0
    faro_game.start_session(state.career_cash)
    state.current_state = state_names.STATE_FARO
    return True


def claim_faro_session_result():

    if faro_game.reward_claimed:
        state.career_cash = faro_game.cash_out()
        return state.faro_session_net

    state.career_cash = faro_game.cash_out()
    state.faro_session_net = faro_game.get_session_net()

    # Only stakes a dealt turn settled count as really playing (B33): chips placed
    # and taken back before the deal never risked anything.
    if faro_game.turns_dealt <= 0 or faro_game.settled_total <= 0:
        faro_game.reward_claimed = True
        return state.faro_session_net

    state.career_event_has_activity = True

    strong_threshold = max(500, int(faro_game.starting_cash * 0.25))
    bad_threshold = max(100, int(faro_game.starting_cash * 0.10))

    if state.faro_session_net >= strong_threshold:
        reward_key = "strong_profit"
    elif state.faro_session_net > 0:
        reward_key = "profit"
    elif state.faro_session_net <= -bad_threshold:
        reward_key = "bad_session"
    else:
        reward_key = "break_even"

    rating_gain = training.TRAINING_RATING_REWARDS["faro"][reward_key]

    if state.faro_session_net > 0:
        career_rewards.award_fans_for_cash_win(
            state.faro_session_net,
            "Faro profit"
        )

    leveling.award_game_xp(
        "faro",
        won=(state.faro_session_net > 0),
    )

    night.record_career_event_result(
        "faro",
        won=(state.faro_session_net > 0),
        net=state.faro_session_net,
        turns=faro_game.turns_dealt,
    )

    track_night_cash(legacy.game_namespace(), "faro", state.faro_session_net)
    faro_game.reward_claimed = True
    return state.faro_session_net


def handle_event(event):
    """Old main-loop event branch for STATE_FARO."""

    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button in (1, 3)
            and state.game_mouse_pos is not None
    ):
        faro_action = get_faro_action(state.game_mouse_pos, event.button, faro_game)
        is_right_click = (event.button == 3)

        if faro_action == FARO_ACTION_CHIP_10:
            state.faro_chip_value = 10
            sounds.audio.play_sound("button_click")

        elif faro_action == FARO_ACTION_CHIP_50:
            state.faro_chip_value = 50
            sounds.audio.play_sound("button_click")

        elif faro_action == FARO_ACTION_CHIP_100:
            state.faro_chip_value = 100
            sounds.audio.play_sound("button_click")

        elif faro_action == FARO_ACTION_CHIP_500:
            state.faro_chip_value = 500
            sounds.audio.play_sound("button_click")

        elif faro_action == FARO_ACTION_CLEAR_BETS:
            if faro_game.clear_bets():
                sounds.audio.play_sound("poker_chips_1")

        elif (
                faro_action is not None
                and faro_action.startswith(FARO_ACTION_BET_RANK_PREFIX)
        ):
            rank = faro_action[len(FARO_ACTION_BET_RANK_PREFIX):]
            if is_right_click:
                if faro_game.remove_bet(rank, state.faro_chip_value):
                    sounds.audio.play_sound("poker_chips_1")
            else:
                if faro_game.place_bet(rank, state.faro_chip_value):
                    sounds.audio.play_sound("poker_chips_1")

        elif (
                faro_action == FARO_ACTION_DEAL
                and event.button == 1
                and not faro_game.session_complete
        ):
            if faro_game.deal_turn():
                net = faro_game.last_profit - faro_game.last_loss - faro_game.last_doublet_loss
                if net: career_rewards.rate_house_game("faro", net)
                sounds.audio.play_sound("card_draw")
                if faro_game.turns_dealt > 0 and faro_game.settled_total > 0:
                    state.career_event_has_activity = True

        elif (
                faro_action == FARO_ACTION_RETURN
                and event.button == 1
        ):
            sounds.audio.play_sound("button_click")
            claim_faro_session_result()
            if state.current_game_mode == "free":
                legacy.finish_free_play_sandbox()
                state.current_state = state_names.STATE_FREE_PLAY_SELECT
            else:
                state.current_state = state_names.STATE_CAREER_EVENT_SELECT


def draw():
    """Old draw-chain branch for STATE_FARO."""

    draw_faro(
        window.game_surface,
        state.game_mouse_pos,
        faro_game,
        state.faro_chip_value,
        panels.draw_submenu_background,
        panels.draw_submenu_title,
        buttons.draw_menu_button,
        fonts.options_title_font,
        fonts.option_label_font,
        fonts.difficulty_detail_font,
        card_fronts=legacy.game.card_fronts,
        card_back_surface=legacy.game.get_card_back_surface(),
    )
