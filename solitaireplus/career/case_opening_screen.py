"""Case opening screen (moved out of legacy.py)."""
from solitaireplus.career.case_opening_ui import CaseOpeningScreen
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
career_saving = lazy("solitaireplus.career.career_saving")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")


case_screen = CaseOpeningScreen()


def handle_event(event):
    """Old main-loop event branch for STATE_CASE_OPENING."""
    if case_screen.handle_event(event, state.game_mouse_pos) == "return":
        if state.current_game_mode == "free":
            legacy.leave_free_play_game()
        else:
            try:
                career_saving.auto_save_career()
                state.current_state = state_names.STATE_CAREER_HUB
            except OSError as error:
                case_screen.notice = "Save failed. Check the saves folder and retry Return."


def draw():
    """Old draw-chain branch for STATE_CASE_OPENING."""
    case_screen.update(pygame.time.get_ticks(), sounds.audio.play_sound)
    case_screen.draw(window.game_surface, state.game_mouse_pos)
