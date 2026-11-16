"""B50: Suit Snake must not race ahead after a pause or frame hitch.

update() catches up at most two grid steps per frame. Before the fix the step
clock (_last_step_at) was only advanced by those two steps, so after a long gap
it stayed far behind "now" and every following frame did two more steps until
the whole debt was paid: the snake shot across the board.
"""
import unittest

import pygame

from solitaireplus.games.arcade.suit_snake_game import SuitSnakeGame


class _NoKeys:
    """Stand-in for pygame.key.get_pressed(): nothing is held."""

    def __getitem__(self, key):
        return False


FRAME_MS = 16


class SuitSnakePauseCatchUpTests(unittest.TestCase):
    def _started_game(self, start_at=1000):
        game = SuitSnakeGame()
        # Wraparound mode, so a long run to the right never hits a border.
        game.start_session("lahey_wraparound", rng_seed=7)
        self.assertTrue(game.wraparound)
        # Keep the target out of the snake's row so no card is collected
        # (collecting would not change the step count, but keeps it simple).
        game.target_cell = (0, 0)
        self.assertTrue(game._start_movement("right", now=start_at))
        return game

    def _head_x_steps(self, game, before):
        """Cells moved to the right since `before`, allowing for wraparound."""
        return (game.snake[0][0] - before) % game.grid_columns

    def test_three_second_gap_then_normal_frames_keeps_normal_rate(self):
        start = 1000
        game = self._started_game(start)
        step_ms = max(55, int(game.mode_config.get("step_ms", 165)))
        head_x = game.snake[0][0]

        # A 3-second pause (no update calls), then one frame.
        now = start + 3000
        game.update(1.0 / 60.0, _NoKeys(), now=now)
        moved = self._head_x_steps(game, head_x)
        self.assertEqual(moved, 2, "catch-up is capped at two cells")
        self.assertFalse(game.finished)

        # Then normal 16 ms frames for one second: the snake must move at its
        # normal rate (about 1000 / step_ms cells), not in a burst.
        head_x = game.snake[0][0]
        steps_per_frame = []
        frames = 1000 // FRAME_MS
        for _ in range(frames):
            before = game.snake[0][0]
            now += FRAME_MS
            game.update(1.0 / 60.0, _NoKeys(), now=now)
            steps_per_frame.append(self._head_x_steps(game, before))
        self.assertFalse(game.finished)
        self.assertLessEqual(max(steps_per_frame), 1, "no frame steps twice")
        moved = self._head_x_steps(game, head_x)
        expected = (frames * FRAME_MS) // step_ms
        self.assertEqual(moved, expected)

    def test_step_clock_is_clamped_to_now_after_a_long_gap(self):
        start = 1000
        game = self._started_game(start)
        now = start + 3000
        game.update(1.0 / 60.0, _NoKeys(), now=now)
        self.assertEqual(game._last_step_at, now)

    def test_normal_frames_keep_exact_cadence(self):
        # Without a gap the step clock keeps its sub-step remainder: it
        # advances in whole step_ms units and is not snapped to "now".
        start = 1000
        game = self._started_game(start)
        step_ms = max(55, int(game.mode_config.get("step_ms", 165)))
        head_x = game.snake[0][0]
        now = start
        for _ in range(100):
            now += FRAME_MS
            game.update(1.0 / 60.0, _NoKeys(), now=now)
        self.assertEqual(self._head_x_steps(game, head_x), (now - start) // step_ms)
        self.assertEqual(game._last_step_at, start + ((now - start) // step_ms) * step_ms)

    def test_two_step_hitch_keeps_remainder(self):
        # A hitch worth exactly two steps (plus a remainder) is fully caught
        # up and the remainder is kept, as before.
        start = 1000
        game = self._started_game(start)
        step_ms = max(55, int(game.mode_config.get("step_ms", 165)))
        now = start + 2 * step_ms + 10
        game.update(1.0 / 60.0, _NoKeys(), now=now)
        self.assertEqual(game._last_step_at, start + 2 * step_ms)


if __name__ == "__main__":
    pygame.init()
    unittest.main()
