"""B17: legacy screens must not build pygame fonts every frame.

Starts the game's modules headless (as the game does, saves in a temporary folder), then draws
each screen that used to call pygame.font.Font / SysFont per frame twice: only the first draw
may build a font. Fonts built by other modules (Score Four's own helpers, B44) are not counted.
"""
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

COUNTED_FILES = {'legacy.py', 'text.py'}   # solitaireplus/legacy.py and solitaireplus/ui/text.py


class FontCounter:
    def __init__(self, real):
        self.real, self.calls = real, []

    def __call__(self, *args, **kwargs):
        caller = sys._getframe(1).f_code
        if os.path.basename(caller.co_filename) in COUNTED_FILES:
            self.calls.append((caller.co_name, args))
        return self.real(*args, **kwargs)


class LegacyFontSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = tempfile.TemporaryDirectory()
        cls.old_local_app_data = os.environ.get('LOCALAPPDATA')
        os.environ['LOCALAPPDATA'] = cls.data.name
        from solitaireplus.app import runtime_support
        saves = os.path.join(cls.data.name, 'saves')
        os.makedirs(saves, exist_ok=True)
        runtime_support.save_directory = lambda: saves
        from solitaireplus import legacy
        from solitaireplus.app import state
        from solitaireplus.ui import text as ui_text
        cls.legacy, cls.state, cls.ui_text = legacy, state, ui_text
        state.game_mouse_pos = None
        state.menu_mouse_pos = None

    @classmethod
    def tearDownClass(cls):
        if cls.old_local_app_data is None:
            os.environ.pop('LOCALAPPDATA', None)
        else:
            os.environ['LOCALAPPDATA'] = cls.old_local_app_data
        cls.data.cleanup()

    def setUp(self):
        clear = getattr(self.ui_text, 'clear_font_cache', None)
        if clear is not None:
            clear()

    def assert_fonts_built_once(self, draw):
        font, sysfont = FontCounter(pygame.font.Font), FontCounter(pygame.font.SysFont)
        with patch('pygame.font.Font', font), patch('pygame.font.SysFont', sysfont):
            draw()
            first = font.calls + sysfont.calls
            del font.calls[:], sysfont.calls[:]
            draw()
            second = font.calls + sysfont.calls
        self.assertTrue(first, 'the screen did not reach its font code')
        self.assertEqual(second, [], 'fonts were built again on the second frame')

    def screens(self):
        legacy, state = self.legacy, self.state

        def score_four_opponent_select():
            if not state.score_four_opponent_choices:
                state.score_four_opponent_choices = legacy.get_score_four_opponent_choices()
            legacy.draw_score_four_opponent_select()

        def career_event_summary():
            state.career_event_summary_title = 'Casino Night'
            state.career_event_summary_lines = [f'Result line {n}' for n in range(9)]   # > 7 lines
            legacy.draw_career_event_summary()

        real_leaderboard = legacy.get_career_leaderboard

        def leaderboard_with_changes(*args, **kwargs):
            board = real_leaderboard(*args, **kwargs)
            for entry in board:
                entry['last_change'] = 3
            return board

        def career_leaderboards():
            with patch.object(legacy, 'get_career_leaderboard', leaderboard_with_changes):
                legacy.draw_career_leaderboards()

        def career_event_select():
            legacy.debug_open_casino_night()
            legacy.draw_career_event_select()

        def battle_bosses_opponent_select():
            if not state.battle_bosses_opponent_choices:
                state.battle_bosses_opponent_choices = legacy.build_battle_bosses_opponent_choices()
            legacy.draw_battle_bosses_opponent_select()

        return {
            'draw_score_four_opponent_select': score_four_opponent_select,
            'draw_career_event_summary': career_event_summary,
            'draw_career_hub': legacy.draw_career_hub,
            'draw_career_real_estate': legacy.draw_career_real_estate,
            'draw_career_leaderboards': career_leaderboards,
            'draw_career_event_select': career_event_select,
            'draw_battle_bosses_opponent_select': battle_bosses_opponent_select,
            'draw_customize_menu': legacy.draw_customize_menu,
            'draw_profile_screen': legacy.draw_profile_screen,
        }

    def test_screens_build_their_fonts_only_once(self):
        for name, draw in self.screens().items():
            with self.subTest(screen=name):
                self.setUp()
                self.assert_fonts_built_once(draw)

    def test_shared_fonts_draw_the_same_pixels_as_fresh_ones(self):
        """A frame drawn with cached fonts (after another frame used them) matches the old way,
        which built every font fresh; a shared font changed by a draw would show up here."""
        from solitaireplus.app import window
        real_font, real_sysfont = pygame.font.Font, pygame.font.SysFont

        def fresh_font(name, size, bold=False, italic=False, sysfont=False):
            if sysfont:
                return real_sysfont(name, size, bold=bold, italic=italic)
            return real_font(name, size)

        def frame(draw):
            window.game_surface.fill((90, 20, 140))
            draw()
            return pygame.image.tobytes(window.game_surface, 'RGB')

        with patch('pygame.time.get_ticks', return_value=123_456):
            for name, draw in self.screens().items():
                with self.subTest(screen=name):
                    self.setUp()
                    with patch.object(self.ui_text, 'get_font', fresh_font):
                        old = frame(draw)
                        self.assertEqual(frame(draw), old, 'the screen is not deterministic')
                    frame(draw)
                    self.assertEqual(frame(draw), old)


if __name__ == '__main__':
    unittest.main()
