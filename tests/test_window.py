"""W1: window size rules (solitaireplus/app/window.py).

Areas are real screen pixels (the game is DPI-aware): the work area (screen minus taskbar) and the
frame + title bar size at that monitor's scaling.
"""
import unittest

from solitaireplus.app import window
from solitaireplus.app.settings import RESOLUTION_OPTIONS

# name: (work area, frame + title bar)
SCREENS = {
    "1366x768 laptop, 100%": ((1366, 728), (16, 39)),
    "1920x1080 at 125%": ((1920, 1032), (20, 49)),
    "2560x1600 at 150%": ((2560, 1528), (24, 59)),
    "1536x960 logical (Dan's PC without DPI awareness)": ((1536, 922), (16, 39)),
    "1920x1200 at 125% (Dan's PC, DPI-aware)": ((1920, 1152), (20, 49)),
    "3840x2160 at 200%": ((3840, 2064), (32, 78)),
    "ultrawide 3440x1440, 100%": ((3440, 1400), (16, 39)),
}

EXPECTED_DEFAULT = {
    "1366x768 laptop, 100%": (1088, 612),
    "1920x1080 at 125%": (1568, 882),
    "2560x1600 at 150%": (2272, 1278),
    "1536x960 logical (Dan's PC without DPI awareness)": (1360, 765),
    "1920x1200 at 125% (Dan's PC, DPI-aware)": (1696, 954),
    "3840x2160 at 200%": (2560, 1440),
    "ultrawide 3440x1440, 100%": (2176, 1224),
}


def usable(name):
    work, decoration = SCREENS[name]
    return window.usable_area_from(work, decoration)


class DefaultSizeTests(unittest.TestCase):
    def test_default_is_the_largest_16_9_within_90_percent_and_clamped(self):
        for name, expected in EXPECTED_DEFAULT.items():
            with self.subTest(name):
                area = usable(name)
                size = window.default_window_size(area)
                self.assertEqual(size, expected)
                self.assertEqual(size[0] * 9, size[1] * 16)                      # exactly 16:9
                self.assertTrue(window.fits(size, area))                         # never off-screen
                self.assertLessEqual(size, window.MAX_WINDOW_SIZE)
                self.assertGreaterEqual(size, window.MIN_WINDOW_SIZE)

    def test_default_window_always_leaves_room_for_the_title_bar(self):
        for name in SCREENS:
            with self.subTest(name):
                work, decoration = SCREENS[name]
                size = window.default_window_size(usable(name))
                self.assertLessEqual(size[0] + decoration[0], work[0])
                self.assertLessEqual(size[1] + decoration[1], work[1])

    def test_largest_16_9(self):
        self.assertEqual(window.largest_16_9(1920, 1080), (1920, 1080))
        self.assertEqual(window.largest_16_9(1366, 768), (1360, 765))
        self.assertEqual(window.largest_16_9(3000, 1000), (1776, 999))


class OptionsAndSavedSizeTests(unittest.TestCase):
    def test_options_offer_only_sizes_that_fit(self):
        choices = dict(window.window_size_choices(usable("1920x1200 at 125% (Dan's PC, DPI-aware)"), RESOLUTION_OPTIONS))
        self.assertTrue(choices[(1366, 768)])
        self.assertTrue(choices[(1600, 900)])
        self.assertFalse(choices[(1920, 1080)])      # 1080 + title bar does not fit in 1152 - taskbar
        self.assertFalse(choices[(2560, 1440)])
        big = dict(window.window_size_choices(usable("3840x2160 at 200%"), RESOLUTION_OPTIONS))
        self.assertTrue(all(big.values()))
        laptop = dict(window.window_size_choices(usable("1366x768 laptop, 100%"), RESOLUTION_OPTIONS))
        self.assertFalse(any(laptop.values()))       # only the default size fits a 1366x768 laptop

    def test_saved_size_is_kept_when_it_fits_and_clamped_when_it_does_not(self):
        area = usable("1920x1200 at 125% (Dan's PC, DPI-aware)")
        self.assertEqual(window.clamp_window_size([1600, 900], area), (1600, 900))
        self.assertEqual(window.clamp_window_size([2560, 1440], area), (1696, 954))   # saved on a big monitor
        self.assertEqual(window.clamp_window_size(None, area), (1696, 954))
        self.assertEqual(window.clamp_window_size([1920, 1080], usable("3840x2160 at 200%")), (1920, 1080))

    def test_usable_area_never_goes_below_one_pixel(self):
        self.assertEqual(window.usable_area_from((10, 10), (16, 39)), (1, 1))


class MouseMappingTests(unittest.TestCase):
    def test_scaled_mode_positions_are_already_game_coordinates(self):
        # SDL maps window positions to 1366x768 (letterbox bars land outside it).
        self.assertEqual(window.window_to_game_coords((683.0, 384.4)), (683, 384))
        self.assertEqual(window.window_to_game_coords((-5, 800)), (-5, 800))


if __name__ == "__main__":
    unittest.main()


class MultiplayerHandoffTests(unittest.TestCase):
    def test_multiplayer_window_inherits_the_players_window_size_and_fullscreen_choice(self):
        # Since W1 the display surface is always the 1366x768 game picture, so the launcher must
        # pass the real window size (state.WINDOWED_*) and the fullscreen choice instead.
        import subprocess
        from unittest.mock import patch
        from solitaireplus.app import multiplayer_launcher, state
        saved = {name: getattr(state, name, None) for name in ("WINDOWED_WIDTH", "WINDOWED_HEIGHT", "fullscreen_enabled")}
        try:
            state.WINDOWED_WIDTH, state.WINDOWED_HEIGHT, state.fullscreen_enabled = 1600, 900, True
            with patch.object(subprocess, "Popen") as popen:
                self.assertTrue(multiplayer_launcher.MultiplayerLauncher().launch())
            env = popen.call_args.kwargs["env"]
            self.assertEqual(env["SOLITAIRE_MP_WINDOW"], "1600x900")
            self.assertEqual(env["SOLITAIRE_MP_FULLSCREEN"], "1")
        finally:
            for name, value in saved.items():
                setattr(state, name, value)
