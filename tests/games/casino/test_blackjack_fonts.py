"""B34: the blackjack screens must not build pygame fonts every frame.

_render_blackjack_fit shrinks a label one point at a time until it fits, and used to build a
fresh pygame.font.SysFont for every size it tried, on every frame. It now takes its fonts from
the shared font cache (ui_text.get_font), so each font is built once. The labels it draws must
look exactly as before.

Starts the game's modules headless (as the game does, saves in a temporary folder).
"""
import os
import random
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

PACKAGE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'solitaireplus')

LONG_NAME = 'Maximilian Bartholomew Featherstonehaugh-Worthington'   # needs shrinking, then hits the floor
LONG_HOMETOWN = 'Llanfairpwllgwyngyll, Isle of Anglesey'
CLOCK = 10_000.0


def counted(filename):
    """Fonts built anywhere in the game package count (the font cache lives there too)."""
    filename = os.path.abspath(filename)
    return os.path.commonpath([filename, PACKAGE]) == PACKAGE


class FontCounter:
    def __init__(self, real):
        self.real, self.calls = real, []

    def __call__(self, *args, **kwargs):
        caller = sys._getframe(1).f_code
        if counted(caller.co_filename):
            self.calls.append((caller.co_name, args, tuple(sorted(kwargs.items()))))
        return self.real(*args, **kwargs)


def old_render_blackjack_fit(screen, text, max_width, size=21, bold=False, color=(255, 255, 255), minimum_size=13):
    """_render_blackjack_fit as it was before B34: a fresh SysFont for every size tried."""
    current_size = int(size)
    while current_size >= minimum_size:
        font = pygame.font.SysFont("cambria", current_size, bold=bold)
        surface = font.render(str(text), True, color)
        if surface.get_width() <= max_width or current_size == minimum_size:
            return surface
        current_size -= 1
    return screen.fonts.blackjack_small_font.render(str(text), True, color)


def pixels(surface):
    return surface.get_size(), pygame.image.tobytes(surface, 'RGBA')


class BlackjackFontTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = tempfile.TemporaryDirectory()
        cls.old_local_app_data = os.environ.get('LOCALAPPDATA')
        os.environ['LOCALAPPDATA'] = cls.data.name
        from solitaireplus.app import runtime_support
        saves = os.path.join(cls.data.name, 'saves')
        os.makedirs(saves, exist_ok=True)
        runtime_support.save_directory = lambda: saves
        from solitaireplus.app import startup  # noqa: F401 (the game's start-up)
        from solitaireplus.app import state, window
        from solitaireplus.ui import text as ui_text
        from solitaireplus.games.casino import blackjack_screen
        from solitaireplus.npc.manager import NPCS
        cls.state, cls.window = state, window
        cls.ui_text, cls.screen = ui_text, blackjack_screen
        state.game_mouse_pos = None
        state.menu_mouse_pos = None
        from solitaireplus.debug import actions as debug_actions   # the F10 actions (Phase 10)
        debug_actions.debug_open_blackjack()
        dealer = dict(NPCS[0])
        dealer.update(name=LONG_NAME, hometown=LONG_HOMETOWN, favorite_suit='Spades')
        state.blackjack_dealer_npc = dealer
        random.seed(34)
        with patch.object(time, 'monotonic', return_value=CLOCK):
            blackjack_screen.blackjack_game.start_round(5)

    @classmethod
    def tearDownClass(cls):
        if cls.old_local_app_data is None:
            os.environ.pop('LOCALAPPDATA', None)
        else:
            os.environ['LOCALAPPDATA'] = cls.old_local_app_data
        cls.data.cleanup()

    def setUp(self):
        self.ui_text.clear_font_cache()
        later = patch.object(time, 'monotonic', return_value=CLOCK + 60)   # the deal animation is over
        later.start()
        self.addCleanup(later.stop)

    def screens(self):
        return {
            'draw_blackjack_bet': self.screen.draw_blackjack_bet,
            'draw_blackjack': self.screen.draw_blackjack,
        }

    def frame(self, draw):
        self.window.game_surface.fill((90, 20, 140))
        draw()
        return pygame.image.tobytes(self.window.game_surface, 'RGB')

    def test_screens_build_each_font_once(self):
        for name, draw in self.screens().items():
            with self.subTest(screen=name):
                self.ui_text.clear_font_cache()
                font, sysfont = FontCounter(pygame.font.Font), FontCounter(pygame.font.SysFont)
                with patch('pygame.font.Font', font), patch('pygame.font.SysFont', sysfont):
                    draw()
                    first = font.calls + sysfont.calls
                    del font.calls[:], sysfont.calls[:]
                    draw()
                    second = font.calls + sysfont.calls
                self.assertTrue(first, 'the screen did not reach its font code')
                built = [(args, kwargs) for _, args, kwargs in first]
                self.assertEqual(len(built), len(set(built)), 'a font was built twice in one frame')
                self.assertEqual(second, [], 'fonts were built again on the second frame')

    def test_fitted_labels_match_the_old_rendering(self):
        """Every label _render_blackjack_fit draws on both screens is byte-identical to the old,
        uncached rendering, on the first frame and on a later one that reuses the cached fonts."""
        real_fit = self.screen._render_blackjack_fit
        drawn = []

        def recording_fit(*args, **kwargs):
            surface = real_fit(*args, **kwargs)
            drawn.append((args, kwargs, surface))
            return surface

        with patch.object(self.screen, '_render_blackjack_fit', recording_fit):
            for draw in self.screens().values():
                draw()
                draw()
        self.assertGreaterEqual(len(drawn), 12, 'the dealer labels were not drawn')
        self.assertIn(LONG_NAME, [args[0] for args, _, _ in drawn])
        for args, kwargs, surface in drawn:
            with self.subTest(label=args[0], max_width=args[1], **kwargs):
                old = old_render_blackjack_fit(self.screen, *args, **kwargs)
                self.assertEqual(pixels(surface), pixels(old))

    def test_fit_edge_cases_match_the_old_rendering(self):
        cases = [
            (('Short', 400), {}),
            ((LONG_NAME, 180), dict(size=27, bold=True, minimum_size=17)),        # shrinks to the floor
            (('Favorite suit: Diamonds', 172), dict(size=17, minimum_size=12)),    # shrinks a little
            ((12345, 300), dict(size=19.0, color=(10, 200, 30))),                  # not a str, float size
            (('Too small', 300), dict(size=11, minimum_size=13)),                  # old fallback font
        ]
        for args, kwargs in cases:
            with self.subTest(args=args, **kwargs):
                old = old_render_blackjack_fit(self.screen, *args, **kwargs)
                self.assertEqual(pixels(self.screen._render_blackjack_fit(*args, **kwargs)), pixels(old))
                self.assertEqual(pixels(self.screen._render_blackjack_fit(*args, **kwargs)), pixels(old))

    def test_frames_match_the_old_rendering(self):
        for name, draw in self.screens().items():
            with self.subTest(screen=name):
                self.ui_text.clear_font_cache()
                with patch.object(self.screen, '_render_blackjack_fit',
                                  lambda *a, **k: old_render_blackjack_fit(self.screen, *a, **k)):
                    old = self.frame(draw)
                    self.assertEqual(self.frame(draw), old, 'the screen is not deterministic')
                self.assertEqual(self.frame(draw), old)
                self.assertEqual(self.frame(draw), old)   # with the cached fonts


if __name__ == '__main__':
    unittest.main()
