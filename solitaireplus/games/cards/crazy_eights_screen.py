"""Crazy Eights table screen (moved out of legacy.py)."""
from solitaireplus.games.cards.crazy_eights_ui import ACTION_CARD as CRAZY_EIGHTS_ACTION_CARD
from solitaireplus.games.cards.crazy_eights_ui import ACTION_CONTINUE as CRAZY_EIGHTS_ACTION_CONTINUE
from solitaireplus.games.cards.crazy_eights_ui import ACTION_DRAW as CRAZY_EIGHTS_ACTION_DRAW
from solitaireplus.games.cards.crazy_eights_ui import ACTION_RETURN as CRAZY_EIGHTS_ACTION_RETURN
from solitaireplus.games.cards.crazy_eights_ui import ACTION_SUIT as CRAZY_EIGHTS_ACTION_SUIT
from solitaireplus.games.cards.crazy_eights import CrazyEightsGame
from solitaireplus.career import career_rewards
from solitaireplus.games.cards.crazy_eights_ui import draw_crazy_eights
from solitaireplus.games.cards.crazy_eights_ui import get_crazy_eights_action
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


crazy_eights_game = CrazyEightsGame()


def start_crazy_eights_session():

    opponents = get_random_npc_group(3)
    crazy_eights_game.start_game(opponents)

    state.current_state = state_names.STATE_CRAZY_EIGHTS



def claim_crazy_eights_result():

    if crazy_eights_game.reward_claimed:
        return

    state.career_event_has_activity = True

    player_won = (crazy_eights_game.winner_index == 0)
    night.record_career_event_result(
        "crazy_eights",
        won=player_won,
    )

    if player_won:
        rating_gain = 60
        career_rewards.award_fans_for_rating_win(
            rating_gain,
            "Crazy Eights win"
        )

    leveling.award_game_xp("crazy_eights", won=player_won)
    crazy_eights_game.reward_claimed = True


def handle_event(event):
    """Old main-loop event branch for STATE_CRAZY_EIGHTS."""

    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
    ):
        crazy_action = get_crazy_eights_action(
            state.menu_mouse_pos,
            crazy_eights_game
        )

        if crazy_action is not None:
            action_name, action_value = crazy_action

            if action_name == CRAZY_EIGHTS_ACTION_RETURN:
                sounds.audio.play_sound("button_click")
                if state.current_game_mode == "free":
                    legacy.finish_free_play_sandbox()
                    state.current_state = state_names.STATE_FREE_PLAY_SELECT
                else:
                    state.current_state = state_names.STATE_CAREER_EVENT_SELECT

            elif action_name == CRAZY_EIGHTS_ACTION_CONTINUE:
                sounds.audio.play_sound("button_click")
                claim_crazy_eights_result()
                if state.current_game_mode == "free":
                    legacy.finish_free_play_sandbox()
                    state.current_state = state_names.STATE_FREE_PLAY_SELECT
                else:
                    state.current_state = state_names.STATE_CAREER_EVENT_SELECT

            elif action_name == CRAZY_EIGHTS_ACTION_DRAW:
                if crazy_eights_game.draw_player_card():
                    sounds.audio.play_sound("card_draw")

            elif action_name == CRAZY_EIGHTS_ACTION_CARD:
                result = crazy_eights_game.play_player_card(
                    action_value
                )
                if result in ("played", "choose_suit"):
                    sounds.audio.play_sound("card_move")

            elif action_name == CRAZY_EIGHTS_ACTION_SUIT:
                if crazy_eights_game.choose_player_suit(
                        action_value
                ):
                    sounds.audio.play_sound("card_move")


def draw():
    """Old draw-chain branch for STATE_CRAZY_EIGHTS."""

    crazy_eights_game.update()

    draw_crazy_eights(
        window.game_surface,
        state.game_mouse_pos,
        crazy_eights_game,
        legacy.game.card_fronts,
        legacy.game.get_card_back_surface(),
        portrait_loader=legacy.get_npc_portrait_surface,
    )
