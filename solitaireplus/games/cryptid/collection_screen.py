"""Cryptid Creatures screen (moved out of legacy.py)."""
from solitaireplus.games.cryptid.ui import CryptidScreen
from solitaireplus.career import career_saving
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
free_play_select = lazy("solitaireplus.menus.free_play_select")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")


def leave_career_cryptid():
    if not cryptid_screen.claim_result():return False
    try:career_saving.auto_save_career()
    except OSError:
        cryptid_screen.notice='Could not save. Check the saves folder and retry Return.'
        cryptid_screen.collection_view.message=cryptid_screen.notice
        return False
    state.current_state=state_names.STATE_CAREER_HUB
    return True
cryptid_screen = CryptidScreen()


def handle_event(event):
    """Old main-loop event branch for STATE_CRYPTID_CREATURES."""
    if cryptid_screen.handle_event(event, state.game_mouse_pos) == "return":
        if cryptid_screen.career_mode:
            leave_career_cryptid()
        else:free_play_select.leave_free_play_game()


def draw():
    """Old draw-chain branch for STATE_CRYPTID_CREATURES."""
    cryptid_screen.sfx_volume = sounds.audio.sfx_volume
    cryptid_screen.update(pygame.time.get_ticks())
    cryptid_screen.draw(window.game_surface, state.menu_mouse_pos)
