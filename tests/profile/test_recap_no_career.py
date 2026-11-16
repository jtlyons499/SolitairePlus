"""B5: "Leave table? -> No" after a career round must not deal a new paid game.

When a career round is won, the Solitaire screen uses the calendar day and
clears the pending career activity before the Recap screen appears. Before the
fix, "No" on the Recap screen then dealt a fresh game while the mode was still
"career", so the next win paid full career rewards without using a day.

Designer decision (2026-11-15): after a career round, "No" returns to the
Career hub without dealing. Free play and other modes still deal a new game.

The real Recap handler (solitaireplus/profile/recap.py) and the real Level-up
screen (solitaireplus/profile/level_up.py) run here. Only the click sound and
the deal (table.game.new_game) are replaced by stand-ins.
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
    "current_game_mode",
    "pending_career_activity_index",
    "pending_career_activity_type",
    "pending_career_challenge_id",
)
MISSING = object()


class FakeSounds:
    """sounds module stand-in: audio.play_sound does nothing."""

    def __init__(self):
        self.audio = types.SimpleNamespace(play_sound=lambda *args, **kwargs: None)


class RecapNoAfterRound(unittest.TestCase):

    def setUp(self):
        saved = {name: getattr(state, name, MISSING) for name in SAVED_STATE}

        def restore():
            for name, value in saved.items():
                if value is MISSING:
                    if hasattr(state, name):
                        delattr(state, name)
                else:
                    setattr(state, name, value)

        self.addCleanup(restore)

        self.new_games = []
        fake_table = types.SimpleNamespace(
            game=types.SimpleNamespace(new_game=lambda *a, **k: self.new_games.append(True))
        )
        for patcher in (
            mock.patch.object(recap, "sounds", FakeSounds()),
            mock.patch.object(level_up, "sounds", FakeSounds()),
            mock.patch.object(recap, "table", fake_table),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

        state.level_up_queue = []
        state.last_progression_result = {"level_up_screens": []}
        state.current_level_up_data = None
        state.current_state = state_names.STATE_RECAP

    def finish_career_round(self):
        """State exactly as update_solitaire_round leaves it after a career win."""
        state.current_game_mode = "career"
        state.post_round_return_state = state_names.STATE_CAREER_HUB
        # The day was used and the pending activity cleared at round completion.
        state.pending_career_activity_index = None
        state.pending_career_activity_type = None
        state.pending_career_challenge_id = None

    def finish_free_play_round(self):
        state.current_game_mode = "free"
        state.post_round_return_state = state_names.STATE_FREE_PLAY_SELECT
        state.pending_career_activity_index = None
        state.pending_career_activity_type = None
        state.pending_career_challenge_id = None

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

    def assert_nothing_reward_eligible(self):
        self.assertEqual(self.new_games, [], "No must not deal a paid career game")
        self.assertIsNone(state.pending_career_activity_index)
        self.assertIsNone(state.pending_career_activity_type)
        self.assertIsNone(state.pending_career_challenge_id)
        self.assertNotEqual(state.post_round_return_state, state_names.STATE_PLAYING)

    def test_career_no_returns_to_hub_without_dealing(self):
        self.finish_career_round()

        self.click(recap.recap_no_rect)

        self.assertEqual(state.current_state, state_names.STATE_CAREER_HUB)
        self.assertEqual(state.post_round_return_state, state_names.STATE_CAREER_HUB)
        self.assert_nothing_reward_eligible()

    def test_career_no_shows_level_ups_then_returns_to_hub(self):
        self.finish_career_round()
        state.level_up_queue = [{"level": 4, "unlocks": []}]
        state.last_progression_result = {
            "level_up_screens": [{"level": 5, "unlocks": [("title", "gold")]}],
        }

        self.click(recap.recap_no_rect)

        self.assertEqual(self.shown_levels(), [4, 5])
        self.assertEqual(state.current_state, state_names.STATE_CAREER_HUB)
        self.assertEqual(state.level_up_queue, [])
        self.assert_nothing_reward_eligible()

    def test_free_play_no_still_deals_a_new_game(self):
        self.finish_free_play_round()

        self.click(recap.recap_no_rect)

        self.assertEqual(self.new_games, [True])
        self.assertEqual(state.current_state, state_names.STATE_PLAYING)
        self.assertEqual(state.post_round_return_state, state_names.STATE_PLAYING)

    def test_free_play_no_shows_level_ups_then_deals(self):
        self.finish_free_play_round()
        state.last_progression_result = {
            "level_up_screens": [{"level": 5, "unlocks": []}],
        }

        self.click(recap.recap_no_rect)

        self.assertEqual(self.new_games, [True])
        self.assertEqual(self.shown_levels(), [5])
        self.assertEqual(state.current_state, state_names.STATE_PLAYING)

    def test_career_yes_unchanged(self):
        self.finish_career_round()

        self.click(recap.recap_yes_rect)

        self.assertEqual(state.current_state, state_names.STATE_CAREER_HUB)
        self.assertEqual(self.new_games, [])


if __name__ == "__main__":
    unittest.main()
