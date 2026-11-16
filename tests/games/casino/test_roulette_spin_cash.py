"""Roulette takes the stake only when the wheel really starts spinning (B25).

The Spin button handler took the total bet out of the player's cash first and only then asked
RouletteGame.start_spin() to start the wheel. When start_spin() refused (already spinning, no
bets, ...), the stake was gone but no round ran, so it was never paid back. The same cash value
(state.career_cash) holds the Free Play sandbox stake while a sandbox is running, so the bug hit
both modes.
"""
import unittest
from unittest.mock import patch

import pygame

from solitaireplus.app import state
from solitaireplus.games.casino import roulette_screen
from solitaireplus.games.casino.roulette import RouletteGame
from solitaireplus.games.casino.roulette_ui import ACTION_SPIN


class _QuietAudio:
    def play_sound(self, *args, **kwargs):
        pass


class _QuietSounds:
    audio = _QuietAudio()


class RouletteSpinCashTests(unittest.TestCase):
    def setUp(self):
        self.game = RouletteGame()
        for target, name, value in (
                (roulette_screen, "roulette_game", self.game),
                (roulette_screen, "get_roulette_action", lambda pos: ACTION_SPIN),
                (roulette_screen, "sounds", _QuietSounds()),
                (state, "game_mouse_pos", (10, 10)),
                (state, "career_cash", 1000),
                (state, "career_event_has_activity", False),
                (state, "current_game_mode", "career"),
                (state, "free_play_snapshot", None),
        ):
            # create=True: some state values (game_mouse_pos...) only exist once the loop ran.
            patcher = patch.object(target, name, value, create=True)
            patcher.start()
            self.addCleanup(patcher.stop)

    def click_spin(self):
        roulette_screen.handle_event(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(10, 10)))

    def test_refused_spin_keeps_career_cash(self):
        self.game.place_bet("color", "red", 100)
        with patch.object(self.game, "start_spin", return_value=False) as start_spin:
            self.click_spin()
        start_spin.assert_called_once()
        self.assertEqual(state.career_cash, 1000)
        self.assertFalse(state.career_event_has_activity)

    def test_refused_spin_keeps_sandbox_cash(self):
        state.current_game_mode = "free"
        state.free_play_snapshot = {"career_cash": 777}   # the real Career cash, set aside
        state.career_cash = 5000                           # the sandbox stake
        self.game.place_bet("color", "black", 250)
        with patch.object(self.game, "start_spin", return_value=False):
            self.click_spin()
        self.assertEqual(state.career_cash, 5000)

    def test_spin_while_already_spinning_keeps_cash(self):
        self.game.place_bet("color", "red", 100)
        self.assertTrue(self.game.start_spin())
        self.click_spin()
        self.assertEqual(state.career_cash, 1000)

    def test_spin_without_bets_keeps_cash(self):
        self.click_spin()
        self.assertFalse(self.game.spinning)
        self.assertEqual(state.career_cash, 1000)

    def test_started_spin_takes_the_stake_once(self):
        self.game.place_bet("color", "red", 100)
        self.game.place_bet("number", "7", 50)
        self.click_spin()
        self.assertTrue(self.game.spinning)
        self.assertEqual(state.career_cash, 850)
        self.assertTrue(state.career_event_has_activity)


if __name__ == "__main__":
    unittest.main()
