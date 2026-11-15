"""B51: Suit Snake must not build two pygame fonts for every card token on every frame.

SuitSnakeGame._draw_card_token built a SysFont(None, size, bold=True) for the rank and another
for the suit letter each time it drew a token: every snake segment plus the target card, every
frame. The fonts now come from the shared font cache (ui_text.get_font) with the same arguments,
so each one is built once and the cabinet looks exactly as before.
"""
import os
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAKE_PY = os.path.normcase(os.path.join(ROOT, 'solitaireplus', 'games', 'arcade', 'suit_snake_game.py'))
TEXT_PY = os.path.normcase(os.path.join(ROOT, 'solitaireplus', 'ui', 'text.py'))
TICKS = 123_456


def fresh_font(name, size, bold=False, italic=False, sysfont=False):
    """What _draw_card_token did before: build a new font on every call."""
    if sysfont:
        return pygame.font.SysFont(name, size, bold=bold, italic=italic)
    font = pygame.font.Font(name, size)
    if bold:
        font.set_bold(True)
    if italic:
        font.set_italic(True)
    return font


def _filename(code):
    return os.path.normcase(os.path.abspath(code.co_filename))


class FontBuilds:
    """Records every pygame.font.Font / SysFont built for suit_snake_game.py while active.

    A font built by the shared cache (ui_text.get_font) or by fresh_font counts for the Suit
    Snake code that asked for it."""

    def __init__(self):
        self.calls = []
        self._patches = []

    def _wrap(self, real):
        def build(*args, **kwargs):
            frame = sys._getframe(1)
            if frame.f_code is fresh_font.__code__ or _filename(frame.f_code) == TEXT_PY:
                frame = frame.f_back
            if _filename(frame.f_code) == SNAKE_PY:
                size = args[1] if len(args) > 1 else kwargs.get('size')
                self.calls.append((frame.f_code.co_name, size))
            return real(*args, **kwargs)
        return build

    def __enter__(self):
        self._patches = [patch('pygame.font.Font', self._wrap(pygame.font.Font)),
                         patch('pygame.font.SysFont', self._wrap(pygame.font.SysFont))]
        for active in self._patches:
            active.start()
        return self

    def __exit__(self, *exc):
        for active in reversed(self._patches):
            active.stop()
        return False


def built_fonts(draw):
    with FontBuilds() as builds:
        draw()
    return builds.calls


def pixels(surface):
    return surface.get_size(), pygame.image.tobytes(surface, 'RGBA')


class SuitSnakeFontCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1366, 768))
        from solitaireplus.ui import text as ui_text
        from solitaireplus.games.arcade import suit_snake_game
        cls.ui_text = ui_text
        cls.snake_module = suit_snake_game
        cls.hud_fonts = {
            'title': pygame.font.Font(None, 48),
            'label': pygame.font.Font(None, 30),
            'detail': pygame.font.Font(None, 24),
            'small': pygame.font.Font(None, 20),
        }

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.ui_text.clear_font_cache()
        ticks = patch('pygame.time.get_ticks', return_value=TICKS)
        ticks.start()
        self.addCleanup(ticks.stop)

    # ------------------------------------------------------------------ the drawings

    def token_draw(self, width, rank, **flags):
        surface = pygame.Surface((80, 80))
        rect = pygame.Rect(10, 10, width, width)

        def draw():
            surface.fill((4, 12, 13))
            self.snake_module.SuitSnakeGame._draw_card_token(surface, rect, rank, 'hearts', **flags)
            return surface
        return draw

    def game_draw(self, mode_id, cards_collected=0):
        game = self.snake_module.SuitSnakeGame()
        game.start_session(mode_id, rng_seed=7)
        # A grown snake inside the grid: one segment per collected card (40 cards reach the 10s).
        cards = [self.snake_module.sequence_card(index) for index in range(cards_collected)]
        game.collected_cards = cards
        game.cards_collected = len(cards)
        columns = game.grid_columns
        game.snake = [(index % columns, index // columns) for index in range(len(cards))] or game.snake
        game._render_from_cells = list(game.snake)
        game.started = bool(cards)
        surface = pygame.Surface((1366, 768))

        def draw():
            game.draw(surface, self.hud_fonts)
            return surface
        return draw

    def drawings(self):
        """name -> (draw, the token font sizes its first frame needs)."""
        return {
            'token_32_rank_2': (self.token_draw(32, '2'), {17, 16}),
            'token_32_rank_10_head': (self.token_draw(32, '10', head=True), {14, 16}),
            'token_28_target': (self.token_draw(28, 'A', target=True), {14}),
            'classic_standard_start': (self.game_draw('classic_standard'), {17, 16}),
            'classic_standard_long_snake': (self.game_draw('classic_standard', 40), {17, 16, 14}),
            'classic_big_grid_long_snake': (self.game_draw('classic_big_grid', 40), {14}),
        }

    # ------------------------------------------------------------------ fonts built once

    def test_second_frame_builds_no_font(self):
        for name, (draw, sizes) in self.drawings().items():
            with self.subTest(drawing=name):
                self.ui_text.clear_font_cache()
                first = built_fonts(draw)
                second = built_fonts(draw)
                self.assertEqual({size for _site, size in first}, sizes)
                self.assertEqual(len(first), len(sizes), f'a font was built more than once: {first}')
                self.assertEqual(second, [], 'fonts were built again on the second frame')

    def test_tokens_build_the_old_fonts(self):
        """The fonts built are still SysFont(None, size, bold=True), at the old sizes."""
        real = pygame.font.SysFont
        requests = []

        def recording_sysfont(name, size, bold=False, italic=False):
            requests.append((name, size, bool(bold), bool(italic)))
            return real(name, size, bold, italic)

        with patch('pygame.font.SysFont', recording_sysfont):
            for width, rank in ((32, '2'), (32, '10'), (28, 'A')):
                self.ui_text.clear_font_cache()
                self.token_draw(width, rank)()
        self.assertEqual(sorted(set(requests)), [
            (None, 14, True, False), (None, 16, True, False), (None, 17, True, False)])
        self.assertEqual(len(requests), 5)   # 17+16, 14+16, then one 14 for both on the small token

    # ------------------------------------------------------------------ same pixels

    def test_frames_match_fresh_fonts(self):
        """A frame drawn with the cached fonts (after another frame used them) is byte-identical to
        one drawn the old way, with every font built fresh."""
        for name, (draw, _sizes) in self.drawings().items():
            with self.subTest(drawing=name):
                self.ui_text.clear_font_cache()
                with patch.object(self.ui_text, 'get_font', fresh_font):
                    old = pixels(draw())
                    self.assertEqual(pixels(draw()), old, 'the drawing is not deterministic')
                self.assertEqual(pixels(draw()), old)
                self.assertEqual(pixels(draw()), old)   # with the cached fonts


if __name__ == '__main__':
    unittest.main()
