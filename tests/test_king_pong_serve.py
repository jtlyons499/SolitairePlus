"""B53: after a point, King Pong serves toward the side that conceded it.

The player's paddle is on the left (a negative x velocity heads to the
player), the NPC's paddle is on the right (a positive x velocity heads to
the NPC).  When the player scores, the NPC conceded, so the next serve must
head to the NPC; when the NPC scores, it must head to the player.
"""
import os
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from solitaireplus.games.arcade.king_pong import KingPongGame  # noqa: E402


class _NoKeys:
    """Pressed-keys stand-in: nothing is held down."""

    def __getitem__(self, key):
        return False


class KingPongServeDirectionTest(unittest.TestCase):

    def _serve_after_point(self, player_scored):
        game = KingPongGame()
        with mock.patch("pygame.time.get_ticks", return_value=1000):
            game.start_match({"name": "Rival"}, target_score=5)
            game._score_point(player_scored=player_scored)
        self.assertFalse(game.finished)
        self.assertEqual(game._ball_velocity.x, 0)
        # Let the point pause run out; the next update serves the ball.
        resume_at = game._serve_resume_at
        self.assertGreater(resume_at, 1000)
        with mock.patch("pygame.time.get_ticks", return_value=resume_at + 1):
            game.update(1 / 60, _NoKeys())
        return game

    def test_player_point_serves_toward_npc(self):
        for _ in range(20):
            game = self._serve_after_point(player_scored=True)
            self.assertGreater(
                game._ball_velocity.x, 0,
                "after the player scores the serve must head to the NPC",
            )

    def test_npc_point_serves_toward_player(self):
        for _ in range(20):
            game = self._serve_after_point(player_scored=False)
            self.assertLess(
                game._ball_velocity.x, 0,
                "after the NPC scores the serve must head to the player",
            )

    def test_pending_serve_flag_names_the_side_that_conceded(self):
        game = KingPongGame()
        with mock.patch("pygame.time.get_ticks", return_value=1000):
            game.start_match({"name": "Rival"}, target_score=5)
            game._score_point(player_scored=True)
            self.assertIs(game._pending_serve_to_player, False)
            game._score_point(player_scored=False)
            self.assertIs(game._pending_serve_to_player, True)


if __name__ == "__main__":
    unittest.main()
