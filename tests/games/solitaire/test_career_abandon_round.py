"""B6: abandoning a career round from the pause menu must not leave stale career state.

The real Solitaire screen event code (solitaireplus/games/solitaire/screen.py) runs here with a
real rules Game; only the Solitaire table (which would start the whole game) and the sounds are stood in for.
The player opens the pause menu, clicks "Return to Menu", then "Yes".
"""
import os
import types
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.games.solitaire import screen
from solitaireplus.games.solitaire.rules import Game

STATE_NAMES = (
    "confirm_return_to_menu",
    "game_pause_menu_open",
    "game_mouse_pos",
    "current_game_mode",
    "current_state",
    "pending_career_activity_index",
    "pending_career_activity_type",
    "pending_career_challenge_id",
)
MISSING = object()


def click(pos):
    state.game_mouse_pos = pos
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))


class AbandonCareerRoundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.surface = pygame.display.set_mode((1, 1))

    def setUp(self):
        saved = {name: getattr(state, name, MISSING) for name in STATE_NAMES}

        def restore():
            for name, value in saved.items():
                if value is MISSING:
                    if hasattr(state, name):
                        delattr(state, name)
                else:
                    setattr(state, name, value)

        self.addCleanup(restore)
        with patch.object(Game, "load_card_images", return_value=None):
            self.game = Game(self.surface, Mock())
        for name, value in (("table", types.SimpleNamespace(game=self.game)),
                            ("sounds", types.SimpleNamespace(audio=Mock()))):
            patcher = patch.object(screen, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.assertFalse(screen.solitaire_restart_prompt.open)

    def play_career_activity(self, activity_type, challenge_id):
        state.current_game_mode = "career"
        state.current_state = state_names.STATE_PLAYING
        state.pending_career_activity_index = 2
        state.pending_career_activity_type = activity_type
        state.pending_career_challenge_id = challenge_id
        if challenge_id is not None:
            self.assertTrue(self.game.set_challenge(challenge_id))
        state.confirm_return_to_menu = False
        state.game_pause_menu_open = True

    def abandon(self):
        click(screen.pause_menu_rect.center)
        self.assertTrue(state.confirm_return_to_menu)
        click(screen.confirm_yes_rect.center)

    def assert_career_state_cleared(self):
        self.assertEqual(state.current_state, state_names.STATE_CAREER_HUB)
        self.assertFalse(state.confirm_return_to_menu)
        self.assertIsNone(state.pending_career_activity_index)
        self.assertIsNone(state.pending_career_activity_type)
        self.assertIsNone(state.pending_career_challenge_id)
        self.assertIsNone(self.game.challenge_id)

    def test_abandoning_a_career_challenge_clears_activity_and_challenge(self):
        self.play_career_activity("challenge", "draw_3")
        self.assertEqual(self.game.stock_draw_count, 3)

        self.abandon()

        self.assert_career_state_cleared()
        self.assertEqual(self.game.stock_draw_count, 1)

    def test_abandoning_a_career_round_clears_pending_activity(self):
        self.play_career_activity("round", None)

        self.abandon()

        self.assert_career_state_cleared()

    def test_no_keeps_the_career_activity(self):
        self.play_career_activity("challenge", "no_undo")
        click(screen.pause_menu_rect.center)

        click(screen.confirm_no_rect.center)

        self.assertTrue(state.game_pause_menu_open)
        self.assertEqual(state.pending_career_activity_type, "challenge")
        self.assertEqual(state.pending_career_challenge_id, "no_undo")
        self.assertEqual(self.game.challenge_id, "no_undo")


if __name__ == "__main__":
    unittest.main()
