"""Casino screens build nothing per frame that could be built once (review of B34/B66).

blackjack_presentation.draw_background smoothscaled the whole background (and the logo) every frame
and used a 'global' statement for the logo; roulette_ui.draw_bet_chip built a pygame font for every
chip on every frame. Pixels must stay the same.
"""
import ast
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from tests.support import locate

FILES = ("solitaireplus/games/casino/blackjack_presentation.py", "solitaireplus/games/casino/roulette_ui.py")


class CasinoFrameCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def test_no_global_statements(self):
        for relative in FILES:
            tree = ast.parse((locate.ROOT / relative).read_text(encoding="utf-8"))
            self.assertFalse([n for n in ast.walk(tree) if isinstance(n, ast.Global)], relative)

    def test_blackjack_background_is_scaled_once_and_looks_the_same(self):
        from solitaireplus.games.casino import blackjack_presentation as bp
        background = pygame.Surface((800, 450))
        background.fill((90, 40, 20))
        pygame.draw.circle(background, (200, 180, 60), (400, 225), 120)
        felt = pygame.Surface((64, 64))
        felt.fill((20, 90, 60))
        real = pygame.transform.smoothscale
        calls = []

        def counting(image, size, *args):
            calls.append(image.get_size())
            return real(image, size, *args)

        frames = []
        with patch.object(bp.pygame.transform, "smoothscale", counting):
            for _ in range(2):
                surface = pygame.Surface((1366, 768))
                bp.draw_background(surface, background, felt)
                frames.append(pygame.image.tobytes(surface, "RGB"))
        self.assertEqual(calls.count((800, 450)), 1, "background scaled again on the second frame")
        self.assertEqual(frames[0], frames[1])
        # The same picture as scaling every frame (the old code).
        reference = pygame.Surface((1366, 768))
        bp._scaled_cache.clear()
        bp._felt_cache.clear()
        bp.draw_background(reference, background, felt)
        self.assertEqual(pygame.image.tobytes(reference, "RGB"), frames[0])

    def test_roulette_chip_font_is_built_once(self):
        from solitaireplus.games.casino import roulette_ui
        from solitaireplus.ui import text as ui_text
        ui_text.clear_font_cache()
        real = pygame.font.Font
        built = []

        def counting(*args, **kwargs):
            built.append(args)
            return real(*args, **kwargs)

        with patch("pygame.font.Font", counting):
            for _ in range(3):
                surface = pygame.Surface((200, 100))
                roulette_ui.draw_bet_chip(surface, pygame.Rect(10, 10, 80, 40), 1500, None)
        self.assertEqual(len(built), 1)


if __name__ == "__main__":
    unittest.main()
