"""D1 (Score Four): the F6 debug hotkey is gone from the Score Four table.

F6 on the table set puzzles_completed = 3, round_complete and session_complete, which finished a
training session (and its rewards) without solving anything. The F10 debug menu stays the only debug
tool. The real table controls (Escape closing the rating panel, the mouse) must keep working.
"""
import ast
import copy
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

from solitaireplus.app import state, state_names
from solitaireplus.games.cards import score_four_screen
from solitaireplus.games.cards.score_four import ScoreFourGame

SCREEN_FILE = Path(score_four_screen.__file__)
STATE_NAMES = ('current_state', 'game_mouse_pos', 'menu_mouse_pos', 'current_game_mode')


class ScoreFourDebugHotkeyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def setUp(self):
        missing = object()
        saved = {name: getattr(state, name, missing) for name in STATE_NAMES}

        def restore():
            for name, value in saved.items():
                if value is missing:
                    if hasattr(state, name):
                        delattr(state, name)
                else:
                    setattr(state, name, value)

        self.addCleanup(restore)
        state.current_state = state_names.STATE_SCORE_FOUR
        state.game_mouse_pos = (0, 0)
        state.menu_mouse_pos = (0, 0)
        state.current_game_mode = 'career'

        self.game = ScoreFourGame()
        self.sounds = MagicMock()
        for name, value in (('score_four_game', self.game), ('sounds', self.sounds)):
            patcher = patch.object(score_four_screen, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    # ------------------------------------------------------------------ helpers

    def press(self, key, unicode=''):
        event = pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode=unicode)
        score_four_screen.loop_event_score_four(event)

    def snapshot(self):
        return copy.deepcopy(vars(self.game)), state.current_state

    def assert_f6_changes_nothing(self):
        before = self.snapshot()
        self.press(pygame.K_F6)
        self.assertEqual(self.snapshot(), before)
        self.sounds.audio.play_sound.assert_not_called()

    # ------------------------------------------------------------------ the debug key is gone

    def test_f6_does_not_complete_a_solo_training_session(self):
        self.game.start_solo_session()
        self.assertEqual(self.game.puzzles_completed, 0)
        self.assert_f6_changes_nothing()
        self.assertFalse(self.game.session_complete)
        self.assertFalse(self.game.round_complete)

    def test_f6_does_not_end_a_competitive_round(self):
        self.game.start_competitive_session('mid')
        self.assert_f6_changes_nothing()
        self.assertFalse(self.game.round_complete)
        self.assertFalse(self.game.session_complete)

    def test_table_handler_binds_no_f6(self):
        tree = ast.parse(SCREEN_FILE.read_text(encoding='utf-8'))
        handler = next(node for node in ast.walk(tree)
                       if isinstance(node, ast.FunctionDef) and node.name == 'loop_event_score_four')
        keys = {node.attr for node in ast.walk(handler)
                if isinstance(node, ast.Attribute) and node.attr == 'K_F6'}
        self.assertEqual(keys, set(), 'Score Four table still binds the F6 debug hotkey')

    # ------------------------------------------------------------------ the real controls still work

    def test_escape_still_closes_the_rating_panel(self):
        self.game.start_solo_session()
        self.game.rating_info_open = True
        self.press(pygame.K_ESCAPE)
        self.assertFalse(self.game.rating_info_open)

    def test_training_complete_button_still_returns_to_the_event_list(self):
        self.game.start_solo_session()
        self.game.puzzles_completed = self.game.puzzles_required
        self.game.round_complete = True
        self.game.session_complete = True
        state.menu_mouse_pos = score_four_screen.score_four_complete_rect.center
        state.game_mouse_pos = None
        with patch.object(score_four_screen, 'settle_score_four_session_result') as settle:
            score_four_screen.loop_event_score_four(
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=state.menu_mouse_pos, button=1))
        settle.assert_called_once_with()
        self.sounds.audio.play_sound.assert_called_with('button_click')
        self.assertEqual(state.current_state, state_names.STATE_CAREER_EVENT_SELECT)


if __name__ == '__main__':
    unittest.main()
