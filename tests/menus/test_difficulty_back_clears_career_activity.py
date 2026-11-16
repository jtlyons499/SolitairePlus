"""Backing out of the Solitaire difficulty screen abandons a career calendar round (review of B6).

Choosing a calendar Round or Challenge sets state.pending_career_activity_* and opens the
difficulty screen; Back returned to the hub with them still set (stale, like B6)."""
import types
import unittest
from unittest.mock import Mock, patch

import pygame

from solitaireplus.app import state, state_names
from solitaireplus.menus import difficulty_screen

NAMES = ("current_game_mode", "current_state", "game_mouse_pos", "pending_career_activity_index",
         "pending_career_activity_type", "pending_career_challenge_id")


class DifficultyBackTests(unittest.TestCase):
    def setUp(self):
        missing = object()
        saved = {name: getattr(state, name, missing) for name in NAMES}

        def restore():
            for name, value in saved.items():
                if value is missing:
                    if hasattr(state, name):
                        delattr(state, name)
                else:
                    setattr(state, name, value)

        self.addCleanup(restore)
        self.game = Mock()
        self.free_play_select = types.SimpleNamespace(finish_free_play_sandbox=Mock())
        for name, value in (("table", types.SimpleNamespace(game=self.game)),
                            ("free_play_select", self.free_play_select),
                            ("sounds", types.SimpleNamespace(audio=types.SimpleNamespace(play_sound=Mock())))):
            patcher = patch.object(difficulty_screen, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def press_back(self):
        state.current_state = state_names.STATE_DIFFICULTY
        state.game_mouse_pos = difficulty_screen.difficulty_back_rect.center
        difficulty_screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                                          pos=state.game_mouse_pos))

    def test_back_from_a_career_round_clears_the_pending_activity(self):
        state.current_game_mode = "career"
        state.pending_career_activity_index = 2
        state.pending_career_activity_type = "challenge"
        state.pending_career_challenge_id = "draw_3"

        self.press_back()

        self.assertEqual(state.current_state, state_names.STATE_CAREER_HUB)
        self.assertIsNone(state.pending_career_activity_index)
        self.assertIsNone(state.pending_career_activity_type)
        self.assertIsNone(state.pending_career_challenge_id)
        self.game.clear_challenge.assert_called_once()
        self.game.new_game.assert_not_called()

    def test_back_in_free_play_is_unchanged(self):
        state.current_game_mode = "free"
        self.press_back()
        self.assertEqual(state.current_state, state_names.STATE_FREE_PLAY_SELECT)
        self.free_play_select.finish_free_play_sandbox.assert_called_once()
        self.game.clear_challenge.assert_not_called()


if __name__ == "__main__":
    unittest.main()
