"""B58: Battle Bosses must not build pygame fonts every frame.

BattleBossesGame.draw built a Font(None, 22) for the Joker ball's "J" whenever the ball image is
missing, and a Font(None, 36) for each fort's suit letter whenever that fort has no portrait, on
every frame. They now come from the shared font cache (ui_text.get_font) with the same arguments,
so each font is built once and the arena looks exactly as before.

The arena is drawn with its art missing and no portraits (so both fallbacks run) twice: the second
frame must build no font, and the picture must equal one drawn with freshly built fonts.
"""
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ENGINE_PY = os.path.normcase(os.path.join(ROOT, 'solitaireplus', 'games', 'arcade', 'battle_bosses_game.py'))
TEXT_PY = os.path.normcase(os.path.join(ROOT, 'solitaireplus', 'ui', 'text.py'))
OPPONENTS = [{'id': f'npc{index}', 'name': name, 'skill_tier': 'mid'}
             for index, name in enumerate(('Alex', 'Blake', 'Casey'))]


def fresh_font(name, size, bold=False, italic=False, sysfont=False):
    """What the draw code did before: build a new font on every call."""
    if sysfont:
        return pygame.font.SysFont(name, size, bold, italic)
    font = pygame.font.Font(name, size)
    if bold:
        font.set_bold(True)
    if italic:
        font.set_italic(True)
    return font


def engine_site(frame):
    """The Battle Bosses engine function that built a font, or None for other code.

    A font built by the shared cache (ui_text.get_font) or by fresh_font counts for the engine
    code that asked for it."""
    code = frame.f_code
    if code is fresh_font.__code__ or os.path.normcase(os.path.abspath(code.co_filename)) == TEXT_PY:
        frame = frame.f_back
        code = frame.f_code
    if os.path.normcase(os.path.abspath(code.co_filename)) != ENGINE_PY:
        return None
    return code.co_name


class FontBuilds:
    """Records every pygame.font.Font / SysFont built for the Battle Bosses engine while active."""

    def __init__(self):
        self.calls = []
        self._patches = []

    def _wrap(self, real):
        def build(*args, **kwargs):
            site = engine_site(sys._getframe(1))
            if site is not None:
                self.calls.append((site, args[:2]))
            return real(*args, **kwargs)
        return build

    def __enter__(self):
        self._patches = [patch('pygame.font.Font', self._wrap(pygame.font.Font)),
                         patch('pygame.font.SysFont', self._wrap(pygame.font.SysFont))]
        for item in self._patches:
            item.start()
        return self

    def __exit__(self, *exc):
        for item in reversed(self._patches):
            item.stop()


class BattleBossesFontCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1366, 768))
        from solitaireplus.games.arcade import battle_bosses_game
        from solitaireplus.ui import text as ui_text
        cls.engine, cls.ui_text = battle_bosses_game, ui_text
        cls.missing = tempfile.TemporaryDirectory()   # an empty folder: every arcade image is missing
        cls.fonts = {
            'title': pygame.font.Font(None, 48),
            'label': pygame.font.Font(None, 30),
            'detail': pygame.font.Font(None, 24),
            'small': pygame.font.Font(None, 20),
        }

    @classmethod
    def tearDownClass(cls):
        cls.missing.cleanup()

    def setUp(self):
        self.ui_text.clear_font_cache()
        art = patch.multiple(self.engine, ASSET_ROOT=self.missing.name,
                             ARCADE_BACKGROUND_PATH=os.path.join(self.missing.name, 'bg.png'))
        art.start()
        self.addCleanup(art.stop)
        self.game = self.engine.BattleBossesGame()
        self.game.start_match(OPPONENTS, 'standard', {'label': 'STANDARD', 'ticket_multiplier': 1.0})

    def draw(self):
        surface = pygame.Surface((1366, 768))
        self.game.draw(surface, self.fonts, portrait_loader=lambda npc, size: None, player_portrait=None)
        return pygame.image.tobytes(surface, 'RGB')

    def test_second_frame_builds_no_font(self):
        with FontBuilds() as builds:
            self.draw()
            first = list(builds.calls)
            del builds.calls[:]
            self.draw()
            second = list(builds.calls)
        self.assertTrue(first, 'the draw did not reach its fallback font code')
        self.assertIn('_draw_ball', [site for site, _args in first])
        self.assertIn('_draw_portrait', [site for site, _args in first])
        self.assertEqual(second, [], 'fonts were built again on the second frame')

    def test_ball_and_suit_fonts_are_built_once_per_size(self):
        with FontBuilds() as builds:
            for _frame in range(3):
                self.draw()
        self.assertEqual(sorted(builds.calls),
                         [('_draw_ball', (None, 22)), ('_draw_portrait', (None, 36))])

    def test_picture_unchanged(self):
        with patch.object(self.ui_text, 'get_font', fresh_font):
            expected = self.draw()
        self.assertEqual(self.draw(), expected)   # first frame: the cache builds the fonts
        self.assertEqual(self.draw(), expected)   # later frames: the cached fonts


if __name__ == '__main__':
    unittest.main()
