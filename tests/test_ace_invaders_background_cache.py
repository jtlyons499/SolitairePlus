"""Ace Invaders scales its background once per screen size, not every frame (B52).

AceInvadersGame._draw_background smoothscaled the whole background picture to the screen size on
every frame. The scaled picture is now kept per target size, like _fit_image keeps its sprites.
The pixels must stay the same.
"""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

SCREEN_SIZE = (1366, 768)


class AceInvadersBackgroundCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def _count_background_scales(self, draw_frame, size):
        real = pygame.transform.smoothscale
        calls = []

        def counting(image, target, *args, **kwargs):
            calls.append(tuple(target))
            return real(image, target, *args, **kwargs)

        frames = []
        with patch.object(pygame.transform, "smoothscale", counting):
            for _ in range(2):
                surface = pygame.Surface(size)
                draw_frame(surface)
                frames.append(pygame.image.tobytes(surface, "RGB"))
        return calls.count(tuple(size)), frames

    def test_two_draws_scale_the_background_once(self):
        from solitaireplus.games.arcade.ace_invaders_game import AceInvadersGame
        game = AceInvadersGame()
        game.start_session("standard", rng_seed=7)
        scales, frames = self._count_background_scales(lambda s: game.draw(s, {}), SCREEN_SIZE)
        self.assertEqual(scales, 1, "background smoothscaled again on the second frame")
        self.assertEqual(frames[0], frames[1])

    def test_background_looks_like_scaling_every_frame(self):
        from solitaireplus.games.arcade import ace_invaders_game as aig
        game = aig.AceInvadersGame()
        scales, frames = self._count_background_scales(game._draw_background, SCREEN_SIZE)
        self.assertEqual(scales, 1)
        # The old code: scale the source to the screen, blit it, then the blue veil on top.
        source = pygame.image.load(os.path.join(aig.ASSET_ROOT, "background.png")).convert_alpha()
        reference = pygame.Surface(SCREEN_SIZE)
        reference.blit(pygame.transform.smoothscale(source, SCREEN_SIZE), (0, 0))
        veil = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
        veil.fill((3, 7, 18, 92))
        reference.blit(veil, (0, 0))
        expected = pygame.image.tobytes(reference, "RGB")
        self.assertEqual(frames[0], expected)
        self.assertEqual(frames[1], expected)

    def test_a_new_size_gets_its_own_scaled_background(self):
        from solitaireplus.games.arcade.ace_invaders_game import AceInvadersGame
        game = AceInvadersGame()
        game._draw_background(pygame.Surface(SCREEN_SIZE))
        scales, frames = self._count_background_scales(game._draw_background, (800, 450))
        self.assertEqual(scales, 1)
        self.assertEqual(frames[0], frames[1])
        # Going back to the first size reuses its cached picture.
        scales, _ = self._count_background_scales(game._draw_background, SCREEN_SIZE)
        self.assertEqual(scales, 0)

    def test_missing_background_still_fills_the_screen(self):
        from solitaireplus.games.arcade.ace_invaders_game import AceInvadersGame
        game = AceInvadersGame()
        with patch.object(pygame.image, "load", side_effect=FileNotFoundError):
            for _ in range(2):
                surface = pygame.Surface((40, 30))
                surface.fill((255, 255, 255))
                game._draw_background(surface)
                self.assertEqual(surface.get_at((5, 5))[:3], (4, 7, 20))


if __name__ == "__main__":
    unittest.main()
