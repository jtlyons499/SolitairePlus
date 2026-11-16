"""B54: King Pong and Ace Invaders keep sub-pixel positions.

Both machines used to add ``int(round(speed * dt))`` to a pygame Rect every
frame, so any speed that is not a whole number of pixels per frame was
rounded each frame (a 68 px/s formation moved 60 px a second, a 145 px/s
rival paddle 120 px). They now keep float positions and copy them into the
Rects, so an object covers ``speed * time`` within a pixel.
"""
import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from solitaireplus.games.arcade.ace_invaders_game import (  # noqa: E402
    PLAYER_SPEED,
    PLAYFIELD_RECT,
    AceInvadersGame,
)
from solitaireplus.games.arcade.king_pong import KingPongGame  # noqa: E402

FRAME = 1 / 60
FRAMES = 60


class _Keys:
    """Pressed-keys stand-in holding down the given keys."""

    def __init__(self, *held):
        self._held = set(held)

    def __getitem__(self, key):
        return key in self._held


class KingPongSubPixelTest(unittest.TestCase):

    def _game(self):
        game = KingPongGame()
        game.start_match({"name": "Rival"}, target_score=5)
        return game

    def test_ball_covers_its_full_distance(self):
        game = self._game()
        # 385 px/s and 135 px/s are 6.42 and 2.25 px per frame: neither is a
        # whole number, so rounding each frame lost 25 px and 15 px a second.
        game._ball_velocity = pygame.Vector2(-385, -135)
        start = pygame.Vector2(game.ball_rect.center)
        for _ in range(FRAMES):
            game.update(FRAME, _Keys())
        moved = pygame.Vector2(game.ball_rect.center) - start
        self.assertAlmostEqual(moved.x, -385, delta=1)
        self.assertAlmostEqual(moved.y, -135, delta=1)

    def test_player_paddle_covers_its_full_distance(self):
        game = self._game()
        game._ball_velocity = pygame.Vector2(0, 0)
        start_x = game.player_paddle.x
        # 375 px/s is 6.25 px per frame; 40 frames stay inside the zone.
        for _ in range(40):
            game.update(FRAME, _Keys(pygame.K_d))
        expected = game.PLAYER_HORIZONTAL_SPEED * 40 * FRAME
        self.assertAlmostEqual(game.player_paddle.x - start_x, expected, delta=1)

        start_y = game.player_paddle.y
        # 500 px/s is 8.33 px per frame; 15 frames stay inside the zone.
        for _ in range(15):
            game.update(FRAME, _Keys(pygame.K_s))
        expected = game.PLAYER_VERTICAL_SPEED * 15 * FRAME
        self.assertAlmostEqual(game.player_paddle.y - start_y, expected, delta=1)

    def test_rival_paddle_covers_its_full_distance(self):
        game = self._game()
        game.difficulty_id = "low"  # 225 px/s: 3.75 px per frame
        game._ball_velocity = pygame.Vector2(0, 0)
        game._npc_error = 0.0
        # Park the chip far below the rival so it chases straight down.
        game.ball_rect.center = (game.playfield.centerx + 100, game.playfield.bottom - 20)
        start_y = game.opponent_paddle.y
        for _ in range(20):
            game.update(FRAME, _Keys())
        expected = game.difficulty["npc_speed"] * 20 * FRAME
        self.assertAlmostEqual(game.opponent_paddle.y - start_y, expected, delta=1)

    def test_direct_rect_moves_still_win(self):
        """A reset, clamp or bounce that sets the Rect is not undone."""
        game = self._game()
        game._ball_velocity = pygame.Vector2(0, 0)
        for _ in range(7):
            game.update(FRAME, _Keys(pygame.K_d))
        game.reset_positions()
        reset_rect = game.player_paddle.copy()
        game.update(FRAME, _Keys())
        self.assertEqual(game.player_paddle, reset_rect)
        game.update(FRAME, _Keys(pygame.K_d))
        self.assertIn(game.player_paddle.x - reset_rect.x, (6, 7))
        self.assertEqual(game.player_paddle.y, reset_rect.y)

        # Pushing into the zone wall keeps the paddle on the wall.
        for _ in range(30):
            game.update(FRAME, _Keys(pygame.K_w))
        zone = game._player_zone()
        self.assertEqual(game.player_paddle.top, zone.top)
        game.update(FRAME, _Keys(pygame.K_s))
        self.assertIn(game.player_paddle.top - zone.top, (8, 9))


class AceInvadersSubPixelTest(unittest.TestCase):

    def _game(self):
        game = AceInvadersGame()
        game.start_session("standard", rng_seed=7)
        return game

    def test_player_ship_covers_its_full_distance(self):
        game = self._game()
        game._last_enemy_shot_at = 10 ** 9  # hold the Aces' fire
        start_x = game.player_rect.x
        # 410 px/s is 6.83 px per frame (rounded up to 7 before the fix).
        for frame in range(FRAMES):
            game.update(FRAME, _Keys(pygame.K_d), now=1000 + frame * 16)
        self.assertAlmostEqual(game.player_rect.x - start_x, PLAYER_SPEED, delta=1)

    def test_formation_covers_its_full_distance(self):
        game = self._game()
        speed = game.difficulty_config["formation_speed"]  # 68 px/s: 1.13 px per frame
        start = [enemy["rect"].x for enemy in game.enemies]
        for _ in range(FRAMES):
            game._move_formation(FRAME)
        for start_x, enemy in zip(start, game.enemies):
            self.assertAlmostEqual(enemy["rect"].x - start_x, speed, delta=1)

    def test_bullets_cover_their_full_distance(self):
        game = self._game()
        game.enemies = []
        game.shields = []
        player_shot = pygame.Rect(PLAYFIELD_RECT.centerx, 600, 12, 24)
        enemy_shot = pygame.Rect(PLAYFIELD_RECT.centerx + 200, 200, 8, 18)
        game.player_bullets = [{"rect": player_shot, "vy": -250.0}]
        game.enemy_bullets = [{"rect": enemy_shot, "vy": 220.0}]
        for frame in range(FRAMES):
            game._update_bullets(FRAME, 1000 + frame * 16)
        self.assertEqual(len(game.player_bullets), 1)
        self.assertEqual(len(game.enemy_bullets), 1)
        self.assertAlmostEqual(game.player_bullets[0]["rect"].y - 600, -250, delta=1)
        self.assertAlmostEqual(game.enemy_bullets[0]["rect"].y - 200, 220, delta=1)


if __name__ == "__main__":
    unittest.main()
