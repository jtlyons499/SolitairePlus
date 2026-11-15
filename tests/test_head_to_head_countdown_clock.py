"""B3: the Head-to-Head 3-2-1 countdown must not count against the player's time.

The race is started the way the Career hub starts it (begin_selected_head_to_head_race, with the
real Game and HeadToHeadRace) under a controlled clock. When the countdown ends, the player's
elapsed race time must be 0, and from then on it must match the race clock.
"""
import os
import random
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from solitaireplus.app import state_names
from solitaireplus.app.settings import DEFAULT_DIFFICULTY
from solitaireplus.games.solitaire.head_to_head import HEAD_TO_HEAD_COUNTDOWN_MS, HeadToHeadRace
from solitaireplus.games.solitaire.rules import Game
from tests.support import locate


DEAL_TIME_MS = 50_000


class HeadToHeadCountdownClockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.Surface((1366, 768))

    def setUp(self):
        self.clock = [DEAL_TIME_MS]
        ticks = patch.object(pygame.time, "get_ticks", lambda: self.clock[0])
        ticks.start()
        self.addCleanup(ticks.stop)

        with patch.object(Game, "load_card_images", return_value=None):
            self.game = Game(self.screen, Mock())
        self.race = HeadToHeadRace(rng=random.Random(7))
        self.env = locate.exec_functions(["begin_selected_head_to_head_race"], {
            "pygame": pygame,
            "game": self.game,
            "head_to_head_race": self.race,
            "DEFAULT_DIFFICULTY": DEFAULT_DIFFICULTY,
            "state_names": state_names,
            "head_to_head_opponents": [
                {"id": "npc_1", "name": "Rival", "rating": 1000, "ratings": {"solitaire": 1000}},
            ],
            "head_to_head_selected_index": 0,
            "career_ratings": {"solitaire": 1000},
            "head_to_head_previous_deal_mode": None,
            "head_to_head_previous_difficulty": None,
            "head_to_head_previous_stock_draw_count": None,
            "career_event_has_activity": False,
            "current_game_mode": "career",
            "current_state": None,
        })

    def start_race(self):
        self.assertTrue(self.env["begin_selected_head_to_head_race"]())
        self.assertEqual(self.env["current_game_mode"], "head_to_head")
        self.assertEqual(self.race.race_started_ms, DEAL_TIME_MS + HEAD_TO_HEAD_COUNTDOWN_MS)

    def test_player_time_is_zero_when_the_countdown_ends(self):
        self.start_race()
        self.clock[0] = DEAL_TIME_MS + HEAD_TO_HEAD_COUNTDOWN_MS
        self.assertFalse(self.race.is_countdown_active(self.clock[0]))
        self.assertEqual(self.game.get_elapsed_seconds(), 0)

    def test_player_time_is_zero_during_the_countdown(self):
        self.start_race()
        self.clock[0] = DEAL_TIME_MS + HEAD_TO_HEAD_COUNTDOWN_MS - 1
        self.assertTrue(self.race.is_countdown_active(self.clock[0]))
        self.assertEqual(self.game.get_elapsed_seconds(), 0)

    def test_player_time_matches_the_race_clock_after_go(self):
        self.start_race()
        self.clock[0] = DEAL_TIME_MS + HEAD_TO_HEAD_COUNTDOWN_MS + 45_500
        self.assertEqual(self.game.get_elapsed_seconds(), 45)
        self.assertEqual(self.race.elapsed_ms(self.clock[0]) // 1000, 45)

    def test_winning_round_summary_excludes_the_countdown(self):
        self.start_race()
        self.clock[0] = DEAL_TIME_MS + HEAD_TO_HEAD_COUNTDOWN_MS + 120_000
        self.game.foundations = [[object()] * 13 for _ in range(4)]
        with patch.object(self.game, "start_victory_animation"), patch("builtins.print"):
            self.game.check_for_win()
        self.assertEqual(self.game.round_summary["elapsed_seconds"], 120)


if __name__ == "__main__":
    unittest.main()
