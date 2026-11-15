"""B17: no heavy work every frame (font cache, scaled button art, pre-scaled menu drift).

Each changed draw helper is called twice: the font constructor or smoothscale may only run for
the first call. The pixels are compared with the old, uncached drawing code (copied here).
Legacy screens that built fonts every frame are covered by test_frame_font_sites.py.
"""
import math
import os
import random
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

from solitaireplus.app import state
from solitaireplus.app.cosmetic_assets import SingleDriftCache
from solitaireplus.games.solitaire.rules import BASE_WIDTH, BASE_HEIGHT
from solitaireplus.ui import backgrounds, buttons, panels
from solitaireplus.ui import text as ui_text

REAL_FONT = pygame.font.Font
REAL_SYSFONT = pygame.font.SysFont
REAL_SMOOTHSCALE = pygame.transform.smoothscale


class Counter:
    """Wraps a pygame function and records each call (name of the calling function, args)."""

    def __init__(self, real):
        self.real, self.calls = real, []

    def __call__(self, *args, **kwargs):
        self.calls.append((sys._getframe(1).f_code.co_name, args))
        return self.real(*args, **kwargs)


def pixels(surface):
    return pygame.image.tobytes(surface, 'RGB')


def noise(size, seed, alpha=True):
    """A random image (random alpha too), so any change in scaling or blending shows."""
    rng = random.Random(seed)
    if alpha:
        return pygame.image.frombytes(rng.randbytes(size[0] * size[1] * 4), size, 'RGBA').convert_alpha()
    return pygame.image.frombytes(rng.randbytes(size[0] * size[1] * 3), size, 'RGB').convert_alpha()


def clear_caches():
    for module, name in ((ui_text, 'clear_font_cache'), (buttons, 'clear_scaled_images')):
        clear = getattr(module, name, None)
        if clear is not None:
            clear()


class DisplayTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT))

    def setUp(self):
        clear_caches()
        self.addCleanup(clear_caches)


class FontCacheTests(DisplayTestCase):
    def test_font_style_is_built_once_and_shared(self):
        with patch('pygame.font.Font', Counter(REAL_FONT)) as built:
            first = ui_text.get_font(None, 24)
            self.assertIs(first, ui_text.get_font(None, 24))
            self.assertEqual(len(built.calls), 1)
            self.assertEqual(built.calls[0][1], (None, 24))
            others = [ui_text.get_font(None, 25), ui_text.get_font(None, 24, bold=True),
                      ui_text.get_font(None, 24, italic=True)]
        self.assertEqual(len({id(font) for font in [first] + others}), 4)
        self.assertFalse(first.bold or first.italic)          # styled copies don't leak into it
        self.assertTrue(others[1].bold and not others[1].italic)
        self.assertTrue(others[2].italic and not others[2].bold)
        self.assertEqual(pixels(first.render('Win +12 / Loss -8', True, (225, 239, 244))),
                         pixels(REAL_FONT(None, 24).render('Win +12 / Loss -8', True, (225, 239, 244))))

    def test_sysfont_style_is_built_once_and_matches_pygame(self):
        with patch('pygame.font.SysFont', Counter(REAL_SYSFONT)) as built:
            title = ui_text.get_font('cambria', 44, bold=True, sysfont=True)
            self.assertIs(title, ui_text.get_font('cambria', 44, bold=True, sysfont=True))
            plain = ui_text.get_font(None, 58, sysfont=True)
            self.assertIs(plain, ui_text.get_font(None, 58, sysfont=True))
            self.assertEqual(len(built.calls), 2)
        self.assertIsNot(title, plain)
        self.assertEqual(pixels(title.render('PROFILE', True, (255, 255, 255))),
                         pixels(REAL_SYSFONT('cambria', 44, bold=True).render('PROFILE', True, (255, 255, 255))))
        self.assertEqual(pixels(plain.render('March 2027', True, (0, 0, 0))),
                         pixels(REAL_SYSFONT(None, 58).render('March 2027', True, (0, 0, 0))))

    def test_cache_does_not_outlive_pygame_quit(self):
        before = ui_text.get_font(None, 21)
        pygame.quit()
        pygame.init()
        pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT))
        after = ui_text.get_font(None, 21)
        self.assertIsNot(before, after)
        self.assertGreater(after.render('ok', True, (255, 255, 255)).get_width(), 0)

    def test_render_text_fit_builds_its_smaller_fonts_once(self):
        font = REAL_FONT(None, 40)
        text = 'A label that is much too wide for its box'

        def old_render_text_fit(max_width, minimum_size=14):
            surface = font.render(text, True, (0, 0, 0))
            size = font.get_height()
            while surface.get_width() > max_width and size > minimum_size:
                size -= 1
                surface = REAL_FONT(None, size).render(text, True, (0, 0, 0))
            return surface

        for max_width in (180, 330, 2000):
            with self.subTest(max_width=max_width):
                with patch('pygame.font.Font', Counter(REAL_FONT)) as built:
                    first = ui_text.render_text_fit(text, font, max_width)
                    first_calls = len(built.calls)
                    second = ui_text.render_text_fit(text, font, max_width)
                self.assertEqual(len(built.calls), first_calls, 'the second call built fonts again')
                expected = pixels(old_render_text_fit(max_width))
                self.assertEqual(pixels(first), expected)
                self.assertEqual(pixels(second), expected)


class MenuButtonTests(DisplayTestCase):
    def setUp(self):
        super().setUp()
        self.art = SimpleNamespace(button_normal=noise((300, 90), 1), button_hover=noise((300, 90), 2),
                                   button_selected=noise((300, 90), 3))
        self.font = REAL_FONT(None, 30)
        self.surface = noise((BASE_WIDTH, BASE_HEIGHT), 4, alpha=False).convert()
        for target, name, value in ((buttons, 'assets', self.art),
                                    (buttons, 'window', SimpleNamespace(game_surface=self.surface))):
            patcher = patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def old_draw_menu_button(self, surface, rect, text, mouse_pos, selected=False):
        hovered = mouse_pos is not None and rect.collidepoint(mouse_pos)
        image = (self.art.button_selected if selected else
                 self.art.button_hover if hovered else self.art.button_normal)
        surface.blit(REAL_SMOOTHSCALE(image, (rect.width, rect.height)), rect.topleft)
        label = self.font.render(text, True, (255, 255, 255))
        surface.blit(label, label.get_rect(center=rect.center))

    def draw_all(self, draw, surface=None):
        for rect in (pygame.Rect(100, 100, 260, 64), pygame.Rect(500, 300, 181, 47)):
            for mouse_pos, selected in ((None, False), (rect.center, False), ((0, 0), True)):
                if surface is None:
                    draw(rect, 'Return', mouse_pos, selected=selected, font=self.font)
                else:
                    draw(surface, rect, 'Return', mouse_pos, selected=selected)

    def test_each_image_and_size_is_scaled_once_and_pixels_match(self):
        expected = self.surface.copy()
        for _ in range(2):
            self.draw_all(self.old_draw_menu_button, expected)
        with patch('pygame.transform.smoothscale', Counter(REAL_SMOOTHSCALE)) as scaled:
            self.draw_all(buttons.draw_menu_button)
            self.assertEqual(len(scaled.calls), 6)        # 3 images x 2 sizes
            self.draw_all(buttons.draw_menu_button)
            self.assertEqual(len(scaled.calls), 6, 'the second frame smoothscaled again')
        self.assertEqual(pixels(self.surface), pixels(expected))

    def test_a_different_image_never_gets_a_stale_copy(self):
        rect = pygame.Rect(40, 40, 200, 60)
        buttons.draw_menu_button(rect, '', None, font=self.font)
        for seed in (11, 12, 13):
            # A new image of the same size each time; the old one is dropped (its id may be reused).
            self.art.button_normal = noise((300, 90), seed)
            expected = self.surface.copy()
            expected.blit(REAL_SMOOTHSCALE(self.art.button_normal, rect.size), rect.topleft)
            buttons.draw_menu_button(rect, '', None, font=self.font)
            self.assertEqual(pixels(self.surface), pixels(expected))

    def test_submenu_title_scales_its_plaque_once_and_pixels_match(self):
        title_font = REAL_FONT(None, 48)
        expected = self.surface.copy()

        def old_draw_submenu_title(text, y=55, width=360, height=72):
            rect = pygame.Rect(BASE_WIDTH // 2 - width // 2, y - height // 2, width, height)
            expected.blit(REAL_SMOOTHSCALE(self.art.button_normal, (rect.width, rect.height)), rect.topleft)
            shadow = title_font.render(text, True, (35, 20, 10))
            expected.blit(shadow, shadow.get_rect(center=(rect.centerx + 3, rect.centery + 3)))
            label = title_font.render(text, True, (255, 255, 255))
            expected.blit(label, label.get_rect(center=rect.center))

        with patch.object(panels, 'assets', self.art), \
                patch.object(panels, 'fonts', SimpleNamespace(options_title_font=title_font)), \
                patch.object(panels, 'window', SimpleNamespace(game_surface=self.surface)), \
                patch('pygame.transform.smoothscale', Counter(REAL_SMOOTHSCALE)) as scaled:
            for _ in range(2):
                panels.draw_submenu_title('OPTIONS')
                panels.draw_submenu_title('CUSTOMIZE', y=90, width=420, height=80)
        for _ in range(2):
            old_draw_submenu_title('OPTIONS')
            old_draw_submenu_title('CUSTOMIZE', y=90, width=420, height=80)
        self.assertEqual(len(scaled.calls), 2, 'each plaque size should be scaled once')
        self.assertEqual(pixels(self.surface), pixels(expected))


def old_drift_offset(ticks):
    """draw_x, draw_y exactly as draw_drifting_menu_background computes them."""
    time_sec = ticks / 1000.0
    drift_x = math.sin(time_sec / backgrounds.MENU_DRIFT_PERIOD_X * math.tau) * backgrounds.MENU_DRIFT_X
    drift_y = math.sin(time_sec / backgrounds.MENU_DRIFT_PERIOD_Y * math.tau + 1.3) * backgrounds.MENU_DRIFT_Y
    scale = backgrounds.MENU_DRIFT_SCALE
    return (round((-backgrounds.MENU_DRIFT_MARGIN + drift_x) * scale),
            round((-backgrounds.MENU_DRIFT_MARGIN + drift_y) * scale))


class DriftingBackgroundTests(DisplayTestCase):
    SCALE = backgrounds.MENU_DRIFT_SCALE

    def setUp(self):
        super().setUp()
        self.surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
        self.reference_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
        self.backgrounds = {'opaque': noise((BASE_WIDTH, BASE_HEIGHT), 21, alpha=False),
                            'see_through': noise((BASE_WIDTH, BASE_HEIGHT), 22, alpha=True)}
        drift_size = (BASE_WIDTH + backgrounds.MENU_DRIFT_MARGIN * 2, BASE_HEIGHT + backgrounds.MENU_DRIFT_MARGIN * 2)
        self.assets = SimpleNamespace(
            menu_background_drift_cache=SingleDriftCache(),
            menu_background_surfaces=self.backgrounds,
            drift_width=drift_size[0], drift_height=drift_size[1],
            menu_drift_render_surface=pygame.Surface((BASE_WIDTH * self.SCALE, BASE_HEIGHT * self.SCALE)).convert())
        # The old code's own 3x buffer, kept across frames like the real one.
        self.reference_render = pygame.Surface((BASE_WIDTH * self.SCALE, BASE_HEIGHT * self.SCALE)).convert()
        self.reference_cache = SingleDriftCache()
        for target, name, value in ((backgrounds, 'assets', self.assets),
                                    (backgrounds, 'window', SimpleNamespace(game_surface=self.surface))):
            patcher = patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(state, 'selected_menu_background', 'opaque', create=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def old_draw(self, ticks):
        """The old draw_drifting_menu_background: blit into the 3x buffer, then smoothscale it down."""
        key = state.selected_menu_background
        background = self.reference_cache.get(
            key, self.backgrounds[key],
            (self.assets.drift_width * self.SCALE, self.assets.drift_height * self.SCALE))
        self.reference_render.blit(background, old_drift_offset(ticks))
        REAL_SMOOTHSCALE(self.reference_render, (BASE_WIDTH, BASE_HEIGHT), self.reference_surface)
        return pixels(self.reference_surface)

    def draw(self, ticks):
        with patch('pygame.time.get_ticks', return_value=ticks):
            backgrounds.draw_drifting_menu_background()
        return pixels(self.surface)

    @staticmethod
    def frame_ticks():
        """One frame time for every sub-pixel phase of the drift, plus the extreme positions."""
        chosen, extremes = {}, {}
        for ticks in range(0, 400_000, 37):
            x, y = old_drift_offset(ticks)
            chosen.setdefault((x % 3, y % 3), ticks)
            for name, value in (('min_x', x), ('max_x', -x), ('min_y', y), ('max_y', -y)):
                if name not in extremes or value < extremes[name][0]:
                    extremes[name] = (value, ticks)
        assert len(chosen) == 9, chosen
        return sorted(set(chosen.values()) | {ticks for _value, ticks in extremes.values()})

    def warm_drift_cache(self):
        key = state.selected_menu_background
        self.assets.menu_background_drift_cache.get(
            key, self.backgrounds[key],
            (self.assets.drift_width * self.SCALE, self.assets.drift_height * self.SCALE))

    def test_menu_drift_is_not_smoothscaled_every_frame(self):
        self.warm_drift_cache()
        with patch('pygame.transform.smoothscale', Counter(REAL_SMOOTHSCALE)) as scaled:
            first = self.draw(0)
            second = self.draw(0)
            third = self.draw(16)         # next frame, same sub-pixel phase
        self.assertEqual(old_drift_offset(0), old_drift_offset(16))
        self.assertEqual(len(scaled.calls), 1, 'only the first frame of a phase may smoothscale')
        self.assertEqual(first, second)
        self.assertEqual(first, third)
        self.assertEqual(first, self.old_draw(0))

    def test_every_drift_phase_matches_the_old_pixels(self):
        for ticks in self.frame_ticks():
            with self.subTest(ticks=ticks, offset=old_drift_offset(ticks)):
                self.assertEqual(self.draw(ticks), self.old_draw(ticks))

    def test_nearly_opaque_background_uses_the_prescaled_frames(self):
        # Scaling opaque art to 3x leaves alpha 251-254 here and there; such backgrounds must use
        # the cache too, and look like the old drawing up to a few colour levels.
        rng = random.Random(23)
        size = (BASE_WIDTH, BASE_HEIGHT)
        raw = bytearray(rng.randbytes(size[0] * size[1] * 4))
        raw[3::4] = bytes([252]) * (size[0] * size[1])
        self.backgrounds['nearly'] = pygame.image.frombytes(bytes(raw), size, 'RGBA').convert_alpha()
        state.selected_menu_background = 'nearly'
        for ticks in (0, 16, 32):                 # warm the old buffer so its history settles
            self.old_draw(ticks)
        self.draw(0)                              # build the first phase
        with patch('pygame.transform.smoothscale', Counter(REAL_SMOOTHSCALE)) as scaled:
            new = self.draw(16)
        self.assertEqual(len(scaled.calls), 0, 'a nearly opaque background must not be smoothscaled every frame')
        old = self.old_draw(16)
        self.assertLessEqual(max(abs(a - b) for a, b in zip(new, old)), 4)

    def test_switching_to_a_see_through_background_keeps_the_old_pixels(self):
        # Transparent pixels blend over what the 3x buffer held from earlier frames, so the
        # history matters: opaque frames, then see-through ones, then opaque again.
        sequence = [('opaque', 0), ('opaque', 30_000), ('see_through', 30_016), ('see_through', 61_000),
                    ('opaque', 61_016), ('see_through', 90_000), ('see_through', 90_016)]
        for key, ticks in sequence:
            state.selected_menu_background = key
            with self.subTest(background=key, ticks=ticks):
                self.assertEqual(self.draw(ticks), self.old_draw(ticks))


if __name__ == '__main__':
    unittest.main()
