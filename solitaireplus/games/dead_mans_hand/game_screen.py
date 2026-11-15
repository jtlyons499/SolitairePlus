"""Dead Man's Hand screen (moved out of legacy.py)."""
from solitaireplus.games.dead_mans_hand.game import DeadMansHandGame
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")


dead_mans_hand_game = DeadMansHandGame()


def start_dead_mans_hand(return_state=None):
    """Launch the isolated raycaster prototype without attaching it to a Night."""

    state.dead_mans_hand_return_state = return_state or state_names.STATE_DEBUG_MENU
    dead_mans_hand_game.start_run()
    dead_mans_hand_game.capture_mouse()
    state.current_state = state_names.STATE_DEAD_MANS_HAND


def exit_dead_mans_hand():
    dead_mans_hand_game.release_mouse()
    state.current_state = state.dead_mans_hand_return_state or state_names.STATE_DEBUG_MENU


def handle_event(event):
    """Old main-loop event branch for STATE_DEAD_MANS_HAND."""

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            exit_dead_mans_hand()
        elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
            dead_mans_hand_game.switch_weapon_by_slot(event.key - pygame.K_0)
        elif event.key == pygame.K_r:
            if dead_mans_hand_game.game_over or dead_mans_hand_game.prototype_complete:
                dead_mans_hand_game.start_run()
                dead_mans_hand_game.capture_mouse()
            else:
                dead_mans_hand_game.start_reload()
    elif event.type == pygame.MOUSEMOTION:
        dead_mans_hand_game.handle_mouse_motion(event.rel[0])
    elif event.type == pygame.MOUSEWHEEL:
        dead_mans_hand_game.cycle_weapon(1 if event.y < 0 else -1)
    elif event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1:
            dead_mans_hand_game.set_trigger_held(True)
            dead_mans_hand_game.fire()
        elif event.button == 3:
            dead_mans_hand_game.set_aiming(True)
        elif event.button == 4:
            dead_mans_hand_game.cycle_weapon(-1)
        elif event.button == 5:
            dead_mans_hand_game.cycle_weapon(1)
    elif event.type == pygame.MOUSEBUTTONUP:
        if event.button == 1:
            dead_mans_hand_game.set_trigger_held(False)
        elif event.button == 3:
            dead_mans_hand_game.set_aiming(False)


def draw():
    """Old draw-chain branch for STATE_DEAD_MANS_HAND."""

    dead_mans_hand_dt = min(0.05, max(0.0, window.clock.get_time() / 1000.0))
    dead_mans_hand_game.update(dead_mans_hand_dt, pygame.key.get_pressed())
    for dmh_sound_event in dead_mans_hand_game.pop_sound_events():
        sound_name = {
            "pistol_shot": "dead_mans_hand_pistol_shot",
            "pistol_reload": "dead_mans_hand_pistol_reload",
            "kar98k_shot": "dead_mans_hand_kar98k_shot",
            "kar98k_bolt": "dead_mans_hand_kar98k_bolt",
            "kar98k_reload": "dead_mans_hand_kar98k_reload",
            "thompson_shot": "dead_mans_hand_thompson_shot",
            "thompson_reload": "dead_mans_hand_thompson_reload",
            "scar20_shot": "dead_mans_hand_scar20_shot",
            "scar20_reload": "dead_mans_hand_scar20_reload",
            "weapon_pickup": "dead_mans_hand_weapon_pickup",
            "enemy_hit": "dead_mans_hand_enemy_hit",
            "enemy_down": "dead_mans_hand_enemy_down",
            "player_hit": "dead_mans_hand_player_hit",
            "player_down": "dead_mans_hand_player_down",
        }.get(dmh_sound_event)
        if sound_name:
            sounds.audio.play_sound(sound_name)
    dead_mans_hand_game.draw(window.game_surface)
