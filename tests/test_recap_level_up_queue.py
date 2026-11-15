"""B7: the Recap screen must not drop level-ups that were already queued.

The real Recap handler (solitaireplus/profile/recap.py) and the real Level-up
screen (solitaireplus/profile/level_up.py) run here. Only the click sound and
the new deal ("No" button) are replaced by stand-ins, so the game never starts.

Before the fix both Recap buttons replaced state.level_up_queue with the
round's level-ups, so a level-up queued earlier (for example XP from another
game or a Cryptid battle) was never shown.
"""
import os
import types
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.profile import level_up
from solitaireplus.profile import recap

SAVED_STATE = (
    "level_up_queue",
    "last_progression_result",
    "current_level_up_data",
    "current_state",
    "post_round_return_state",
    "game_mouse_pos",
)


class FakeSounds:
    """sounds module stand-in: audio.play_sound does nothing."""

    def __init__(self):
        self.audio = types.SimpleNamespace(play_sound=lambda *args, **kwargs: None)


class RecapKeepsQueuedLevelUps(unittest.TestCase):

    def setUp(self):
        missing = object()
        self.saved = {name: getattr(state, name, missing) for name in SAVED_STATE}
        self.missing = missing
        self.new_games = []
        fake_legacy = types.SimpleNamespace(
            game=types.SimpleNamespace(new_game=lambda: self.new_games.append(True))
        )
        for patcher in (
            mock.patch.object(recap, "sounds", FakeSounds()),
            mock.patch.object(level_up, "sounds", FakeSounds()),
            mock.patch.object(recap, "legacy", fake_legacy),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

        # One level-up is already waiting when the round's recap appears,
        # and the finished round itself earned another one.
        state.level_up_queue = [{"level": 4, "unlocks": []}]
        state.last_progression_result = {
            "level_up_screens": [{"level": 5, "unlocks": [("title", "gold")]}],
        }
        state.current_level_up_data = None
        state.current_state = state_names.STATE_RECAP
        state.post_round_return_state = state_names.STATE_MENU

    def tearDown(self):
        for name, value in self.saved.items():
            if value is self.missing:
                if hasattr(state, name):
                    delattr(state, name)
            else:
                setattr(state, name, value)

    def click(self, rect):
        state.game_mouse_pos = rect.center
        recap.handle_event(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)
        )

    def press_continue(self):
        level_up.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))

    def shown_levels(self):
        """Every level-up screen shown, in order, until the player is sent on."""
        levels = []
        for _ in range(10):
            if state.current_state != state_names.STATE_LEVEL_UP:
                break
            levels.append(state.current_level_up_data["level"])
            self.press_continue()
        return levels

    def test_yes_shows_queued_and_round_level_ups(self):
        self.click(recap.recap_yes_rect)

        self.assertEqual(self.shown_levels(), [4, 5])
        self.assertEqual(state.current_state, state_names.STATE_MENU)
        self.assertEqual(state.level_up_queue, [])

    def test_no_shows_queued_and_round_level_ups_then_deals(self):
        self.click(recap.recap_no_rect)

        self.assertEqual(self.new_games, [True])
        self.assertEqual(self.shown_levels(), [4, 5])
        self.assertEqual(state.current_state, state_names.STATE_PLAYING)
        self.assertEqual(state.level_up_queue, [])

    def test_round_without_level_ups_leaves_queue_alone(self):
        state.last_progression_result = {"level_up_screens": []}

        self.click(recap.recap_yes_rect)

        self.assertEqual(state.current_state, state_names.STATE_MENU)
        self.assertEqual(state.level_up_queue, [{"level": 4, "unlocks": []}])

    def test_round_screens_are_not_shared_with_the_progression_result(self):
        self.click(recap.recap_yes_rect)
        self.shown_levels()

        self.assertEqual(
            state.last_progression_result["level_up_screens"],
            [{"level": 5, "unlocks": [("title", "gold")]}],
        )


if __name__ == "__main__":
    unittest.main()
