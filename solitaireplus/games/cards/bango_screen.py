"""Bango table screen (moved out of legacy.py)."""
from solitaireplus.games.cards.bango_ui import ACTION_CALL as BANGO_ACTION_CALL
from solitaireplus.games.cards.bango_ui import ACTION_CONTINUE as BANGO_ACTION_CONTINUE
from solitaireplus.games.cards.bango_ui import ACTION_RETURN as BANGO_ACTION_RETURN
from solitaireplus.games.cards.bango import BangoGame
from solitaireplus.career import career_rewards
from solitaireplus.games.cards.bango_ui import draw_bango
from solitaireplus.games.cards.bango_ui import get_bango_action
from solitaireplus.npc.manager import get_random_npc_group
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
night = lazy("solitaireplus.career.events.night")
leveling = lazy("solitaireplus.profile.leveling")


bango_game = BangoGame()



def start_bango_session():

    opponents = get_random_npc_group(3)
    bango_game.start_game(
        opponents,
        hand_size=5
    )

    state.current_state = state_names.STATE_BANGO



def claim_bango_result():

    if bango_game.reward_claimed:
        return

    state.career_event_has_activity = True

    player_won = (bango_game.winner_index == 0)
    night.record_career_event_result(
        "bango",
        won=player_won,
    )

    if player_won:
        rating_gain = 35
        career_rewards.award_fans_for_rating_win(
            rating_gain,
            "Bango win"
        )

    leveling.award_game_xp("bango", won=player_won)
    bango_game.reward_claimed = True


def handle_event(event):
    """Old main-loop event branch for STATE_BANGO."""

    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
    ):
        bango_action = get_bango_action(
            state.menu_mouse_pos,
            bango_game
        )

        if bango_action == BANGO_ACTION_RETURN:
            sounds.audio.play_sound("button_click")
            if state.current_game_mode == "free":
                legacy.finish_free_play_sandbox()
                state.current_state = state_names.STATE_FREE_PLAY_SELECT
            else:
                state.current_state = state_names.STATE_CAREER_EVENT_SELECT

        elif bango_action == BANGO_ACTION_CONTINUE:
            sounds.audio.play_sound("button_click")
            claim_bango_result()
            if state.current_game_mode == "free":
                legacy.finish_free_play_sandbox()
                state.current_state = state_names.STATE_FREE_PLAY_SELECT
            else:
                state.current_state = state_names.STATE_CAREER_EVENT_SELECT

        elif bango_action == BANGO_ACTION_CALL:
            if bango_game.call_next():
                sounds.audio.play_sound("card_draw")


def draw():
    """Old draw-chain branch for STATE_BANGO."""

    draw_bango(
        window.game_surface,
        state.game_mouse_pos,
        bango_game,
        legacy.game.card_fronts,
        legacy.game.get_card_back_surface(),
        portrait_loader=legacy.get_npc_portrait_surface,
    )
