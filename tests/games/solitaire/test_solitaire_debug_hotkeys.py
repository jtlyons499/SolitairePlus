"""D1 (Solitaire): the F8 instant-win and F7 auto-solve debug hotkeys are gone from PLAYING.

The designer keeps the instant win for the F10 debug menu (Phase 10 adds a 'Win this Solitaire
round' button), so the old F8 body lives on as games.solitaire.screen.instant_win_round(); it is
not bound to any key. Game.debug_auto_solve_state and Game.start_debug_victory_animation stay.
"""
import ast
import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

from solitaireplus.app import state, state_names
from solitaireplus.games.solitaire import screen
from solitaireplus.games.solitaire.rules import Game

SCREEN_FILE = Path(screen.__file__)
OLD_F8_SUMMARY = {
    'moves': 112,
    'elapsed_seconds': 387,
    'base_score': 5000,
    'move_bonus': 1700,
    'time_bonus': 952,
    'score': 7652,
    'xp_earned': 150,
    'remark': 'Efficient work.',
}


class SolitaireDebugHotkeyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.surface = pygame.display.set_mode((1, 1))

    def setUp(self):
        names = ('current_state', 'current_game_mode', 'game_pause_menu_open',
                 'confirm_return_to_menu', 'game_mouse_pos')
        missing = object()
        saved = {name: getattr(state, name, missing) for name in names}

        def restore():
            for name, value in saved.items():
                if value is missing:
                    if hasattr(state, name):
                        delattr(state, name)
                else:
                    setattr(state, name, value)

        self.addCleanup(restore)
        state.current_state = state_names.STATE_PLAYING
        state.current_game_mode = 'free_play'
        state.game_pause_menu_open = False
        state.confirm_return_to_menu = False
        state.game_mouse_pos = (0, 0)

        prompt_open = screen.solitaire_restart_prompt.open
        self.addCleanup(setattr, screen.solitaire_restart_prompt, 'open', prompt_open)
        screen.solitaire_restart_prompt.open = False

        with patch.object(Game, 'load_card_images', return_value=None):
            self.game = Game(self.surface, Mock())
        self.sounds = MagicMock()
        table_patch = patch.object(screen, 'table', SimpleNamespace(game=self.game))
        sounds_patch = patch.object(screen, 'sounds', self.sounds)
        table_patch.start()
        sounds_patch.start()
        self.addCleanup(table_patch.stop)
        self.addCleanup(sounds_patch.stop)

    def press(self, key):
        screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode=''))

    def test_f8_in_playing_does_not_win_the_round(self):
        self.press(pygame.K_F8)

        self.assertFalse(self.game.round_won)
        self.assertIsNone(self.game.round_summary)
        self.assertIsNone(self.game.victory_animation)
        self.game.audio.play_sound.assert_not_called()

    def test_f7_in_playing_does_not_auto_solve(self):
        tableau_before = [[(c.rank, c.suit, c.face_up) for c in pile] for pile in self.game.tableau]
        with patch.object(self.game, 'debug_auto_solve_state') as auto_solve:
            self.press(pygame.K_F7)
            auto_solve.assert_not_called()
        self.press(pygame.K_F7)

        self.assertFalse(self.game.round_won)
        self.assertEqual(
            [[(c.rank, c.suit, c.face_up) for c in pile] for pile in self.game.tableau],
            tableau_before)

    def test_handle_event_binds_neither_f7_nor_f8(self):
        tree = ast.parse(SCREEN_FILE.read_text(encoding='utf-8'))
        keys = {node.attr for node in ast.walk(tree)
                if isinstance(node, ast.Attribute) and node.attr in ('K_F7', 'K_F8')}
        self.assertEqual(keys, set(), 'Solitaire screen still references a debug hotkey')

    def test_instant_win_round_does_what_f8_did(self):
        self.assertTrue(callable(getattr(screen, 'instant_win_round', None)))

        screen.instant_win_round()

        self.assertTrue(self.game.round_won)
        self.assertEqual(self.game.round_summary, OLD_F8_SUMMARY)
        self.game.audio.play_sound.assert_called_once_with('celebration_1')
        self.assertIsNotNone(self.game.victory_animation)
        self.assertEqual(len(self.game.victory_animation['cards']), 52)

    def test_debug_helpers_stay_on_the_game(self):
        self.assertTrue(callable(getattr(Game, 'debug_auto_solve_state', None)))
        self.assertTrue(callable(getattr(Game, 'start_debug_victory_animation', None)))


if __name__ == '__main__':
    unittest.main()
