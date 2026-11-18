"""W1: window size rules (solitaireplus/app/window.py).

Areas are real screen pixels (the game is DPI-aware): the work area (screen minus taskbar) and the
frame + title bar size at that monitor's scaling.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest import mock

import pygame

from solitaireplus.app import state, window
from solitaireplus.app.settings import RESOLUTION_OPTIONS

ROOT = Path(__file__).resolve().parents[2]

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


class PictureRectTests(unittest.TestCase):
    """The 1366x768 picture fills the window (W1: no black borders in a 16:9 window)."""

    def test_16_9_windows_are_filled_completely(self):
        for size in [(1366, 768), (1696, 954), (1024, 576), (1088, 612), (1920, 1080), (2560, 1440), (1600, 900)]:
            self.assertEqual(window.picture_rect(size), pygame.Rect(0, 0, *size), size)

    def test_other_shapes_get_bars_only_on_the_extra_side(self):
        # 16:10 fullscreen (Dan's 1920x1200 monitor): 60-pixel bars top and bottom, none at the sides.
        self.assertEqual(window.picture_rect((1920, 1200)), pygame.Rect(0, 60, 1920, 1079))   # 1366 is a hair over 16:9
        # A window dragged wider than 16:9: bars at the sides only.
        self.assertEqual(window.picture_rect((2000, 900)), pygame.Rect(199, 0, 1601, 900))
        # A window size that is not an exact 16:9 multiple fills to within a pixel.
        rect = window.picture_rect((1700, 956))
        self.assertLessEqual(1700 - rect.width, 1)
        self.assertLessEqual(956 - rect.height, 1)


class MouseMappingTests(unittest.TestCase):
    def test_unscaled_picture_maps_one_to_one(self):
        rect = pygame.Rect(0, 0, 1366, 768)
        self.assertEqual(window.window_to_game_coords((683.0, 384.4), rect), (683, 384))
        self.assertEqual(window.window_to_game_coords((-5, 800), rect), (-5, 800))

    def test_scaled_window_maps_back_to_game_coordinates(self):
        rect = window.picture_rect((1696, 954))
        self.assertEqual(window.window_to_game_coords((0, 0), rect), (0, 0))
        self.assertEqual(window.window_to_game_coords((848, 477), rect), (683, 384))
        self.assertEqual(window.window_to_game_coords((1695, 953), rect), (1365, 767))

    def test_black_bars_map_outside_the_picture(self):
        rect = window.picture_rect((1920, 1200))          # bars of 60 pixels top and bottom
        self.assertLess(window.window_to_game_coords((960, 30), rect)[1], 0)
        self.assertGreaterEqual(window.window_to_game_coords((960, 1170), rect)[1], 768)
        self.assertEqual(window.window_to_game_coords((960, 600), rect), (683, 384))

    def test_events_get_game_positions_and_movement(self):
        rect = window.picture_rect((2732, 1536))          # exactly twice the game size
        event = pygame.event.Event(pygame.MOUSEMOTION, pos=(1000, 500), rel=(10, -4), buttons=(0, 0, 0))
        moved = window.translate_event(event, rect)
        self.assertEqual(moved.pos, (500, 250))
        self.assertEqual(moved.rel, (5, -2))
        self.assertEqual(moved.buttons, (0, 0, 0))
        click = window.translate_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(2, 2), button=1), rect)
        self.assertEqual((click.pos, click.button), ((1, 1), 1))
        key = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a)
        self.assertIs(window.translate_event(key, rect), key)
        # At 1366x768 nothing changes (the screenshot harness relies on this).
        self.assertIs(window.translate_event(event, pygame.Rect(0, 0, 1366, 768)), event)


MISSING = object()
WINDOW_STATE = ("screen", "WINDOW_WIDTH", "WINDOW_HEIGHT", "WINDOWED_WIDTH", "WINDOWED_HEIGHT",
                "window_pending_size", "fullscreen_enabled", "window_custom_cursor")
DANS_PC = usable("1920x1200 at 125% (Dan's PC, DPI-aware)")      # (1900, 1103): default 1696x954


class OpenWindowTests(unittest.TestCase):
    """open_window(caption, size) is shared with the multiplayer window (W1, Phase 11)."""

    def setUp(self):
        self.saved = {name: getattr(state, name, MISSING) for name in WINDOW_STATE}
        self.driver = os.environ.get("SDL_VIDEODRIVER")
        os.environ["SDL_VIDEODRIVER"] = "dummy"        # never a real window, even outside run_tests.py
        pygame.display.quit()
        pygame.display.init()

    def tearDown(self):
        pygame.display.quit()
        if self.driver is None:
            os.environ.pop("SDL_VIDEODRIVER", None)
        else:
            os.environ["SDL_VIDEODRIVER"] = self.driver
        pygame.display.init()                          # as the test runner left it (no window)
        for name, value in self.saved.items():
            if value is MISSING:
                if hasattr(state, name):
                    delattr(state, name)
            else:
                setattr(state, name, value)

    def open(self, *args, area=DANS_PC):
        # A fresh display each time: the game opens its window once per process.
        pygame.display.quit()
        pygame.display.init()
        self.assertEqual(pygame.display.get_driver(), "dummy")
        with mock.patch.object(window, "usable_area", return_value=area), warnings.catch_warnings():
            warnings.simplefilter("ignore")                # "no fast renderer available" (dummy driver)
            window.open_window(*args)
        return window._sdl_window()

    def assert_window(self, sdl_window, caption, size):
        self.assertEqual(pygame.display.get_caption()[0], caption)
        self.assertEqual(state.screen.get_size(), size)                    # the picture is scaled to fill it
        self.assertEqual((state.WINDOWED_WIDTH, state.WINDOWED_HEIGHT), size)
        self.assertEqual((state.WINDOW_WIDTH, state.WINDOW_HEIGHT), size)
        self.assertEqual(state.window_pending_size, size)                  # present() centres it again
        # SDL really has the size, also below 1366x768.
        self.assertEqual(tuple(sdl_window.size), size)
        self.assertEqual(tuple(sdl_window.minimum_size), window.MIN_WINDOW_SIZE)

    def present(self, frames=3):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for _ in range(frames):
                pygame.event.pump()
                window.present()

    def test_open_window_sets_caption_and_clamps_size(self):
        # A size handed over from a bigger monitor (or saved there) falls back to the default size.
        self.assert_window(self.open("Solitaire+ Multiplayer", (2560, 1440)), "Solitaire+ Multiplayer", (1696, 954))
        # A size that fits is kept, also as a JSON list and when it is not one of the Options sizes.
        self.assert_window(self.open("Solitaire+ Multiplayer", [1600, 900]), "Solitaire+ Multiplayer", (1600, 900))
        self.assert_window(self.open("Solitaire+ Multiplayer", (1088, 612)), "Solitaire+ Multiplayer", (1088, 612))
        # On a 1366x768 laptop only the default size fits.
        laptop = usable("1366x768 laptop, 100%")
        self.assert_window(self.open("Solitaire+ Multiplayer", (1366, 768), area=laptop),
                           "Solitaire+ Multiplayer", (1088, 612))

    def test_small_window_sizes_really_apply(self):
        # A 1366x768 laptop: the default 1088x612 is smaller than the game picture. SDL must take
        # it, or the window (1366x768 plus its frame) would not fit the screen, the pending size
        # would never clear and present() would resize the window on every frame.
        state.window_custom_cursor = False         # no single-player cursor module (see below)
        sdl_window = self.open(area=usable("1366x768 laptop, 100%"))
        self.present()
        self.assertEqual(tuple(sdl_window.size), (1088, 612))
        self.assertIsNone(state.window_pending_size)
        # A size the player drags the window to stays (it is not snapped back to 1366x768).
        sdl_window.size = (1200, 675)
        self.present()
        self.assertEqual(tuple(sdl_window.size), (1200, 675))
        # If SDL puts a bigger minimum back after fullscreen, the next size request lowers it.
        sdl_window.minimum_size = (1366, 768)
        with mock.patch.object(window, "_set_sdl_fullscreen"):
            window.set_fullscreen_enabled(True)
            window.set_fullscreen_enabled(False)
        self.present()
        self.assertEqual(tuple(sdl_window.size), (1088, 612))
        self.assertIsNone(state.window_pending_size)
        sdl_window.minimum_size = (1366, 768)
        window.set_window_size(1024, 576)
        self.present()
        self.assertEqual(tuple(sdl_window.size), (1024, 576))
        self.assertIsNone(state.window_pending_size)

    def test_open_window_default_unchanged(self):
        # Single-player calls open_window() with no arguments: caption and default size as before.
        self.assertEqual(window.default_window_size(DANS_PC), (1696, 954))
        self.assert_window(self.open(), "Solitaire", (1696, 954))
        self.assert_window(self.open("Solitaire", None), "Solitaire", (1696, 954))
        laptop = usable("1366x768 laptop, 100%")
        self.assert_window(self.open(area=laptop), "Solitaire", (1088, 612))

    def test_custom_cursor_is_applied_only_when_enabled(self):
        self.assertIs(state.window_custom_cursor, True)                      # single-player default
        self.open()
        # new= is given so that patch never touches the lazy module (that would import it).
        cursors = mock.Mock()
        with mock.patch.object(window, "cursors", new=cursors), \
                mock.patch.object(window, "_set_sdl_fullscreen") as toggle:
            window.set_window_size(1366, 768)
            window.set_fullscreen_enabled(True)
            window.set_fullscreen_enabled(False)
            self.assertEqual(cursors.apply_selected_cursor.call_count, 3)
            state.window_custom_cursor = False
            window.set_window_size(1600, 900)
            window.set_fullscreen_enabled(True)
            window.set_window_size(1366, 768)                              # leaves fullscreen first
            self.assertEqual(cursors.apply_selected_cursor.call_count, 3)
        self.assertEqual(toggle.call_count, 4)
        self.assertFalse(state.fullscreen_enabled)
        self.assertEqual((state.WINDOWED_WIDTH, state.WINDOWED_HEIGHT), (1366, 768))


# Runs in a fresh process: the multiplayer window must never import the single-player cursors
# module or the single-player start-up (solitaireplus.app.startup, which starts the whole game);
# the cursor code reads profile.cosmetics.REWARD_CURSOR_IDS when it applies a cursor.
NO_CURSOR_CHILD = r"""
import json, sys, warnings
from unittest import mock
import pygame
from solitaireplus.app import state, window

warnings.simplefilter("ignore")
state.window_custom_cursor = False
pygame.display.init()
errors = []
window.open_window("Solitaire+ Multiplayer", (1600, 900))
with mock.patch.object(window, "_set_sdl_fullscreen") as toggle:
    steps = [lambda: window.set_window_size(1366, 768),
             lambda: window.set_fullscreen_enabled(True),
             lambda: window.set_window_size(1600, 900),
             lambda: window.set_fullscreen_enabled(True),
             lambda: window.set_fullscreen_enabled(False)]
    for step in steps:
        try:
            step()
        except BaseException as error:
            errors.append(repr(error))
    toggles = toggle.call_count
loaded = [name for name in ("solitaireplus.ui.cursors", "solitaireplus.app.startup") if name in sys.modules]
print("@@CHILD " + json.dumps({"loaded": loaded, "errors": errors, "toggles": toggles,
                               "windowed": [state.WINDOWED_WIDTH, state.WINDOWED_HEIGHT],
                               "fullscreen": state.fullscreen_enabled}))
"""


class NoCursorImportTests(unittest.TestCase):
    def test_no_cursor_import_when_custom_cursor_off(self):
        with tempfile.TemporaryDirectory(prefix="window-test-") as temporary:
            env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy",
                       PYGAME_HIDE_SUPPORT_PROMPT="1", LOCALAPPDATA=temporary, APPDATA=temporary,
                       PYTHONIOENCODING="utf-8")
            env.pop("PYTHONPATH", None)
            done = subprocess.run([sys.executable, "-c", NO_CURSOR_CHILD], cwd=ROOT, env=env,
                                  capture_output=True, text=True, encoding="utf-8", errors="replace",
                                  timeout=180)
        lines = [line for line in done.stdout.splitlines() if line.startswith("@@CHILD ")]
        self.assertEqual(len(lines), 1, f"exit {done.returncode}\n{done.stdout[-2000:]}\n{done.stderr[-2000:]}")
        result = json.loads(lines[0][len("@@CHILD "):])
        self.assertEqual(result["loaded"], [])
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["toggles"], 4)
        self.assertEqual(result["windowed"], [1600, 900])
        self.assertFalse(result["fullscreen"])
        self.assertEqual(done.returncode, 0)


class MultiplayerHandoffTests(unittest.TestCase):
    # (window size, fullscreen) in single-player -> what the multiplayer window starts with.
    # The default window (1696x954 on Dan's PC, 1088x612 on a 1366x768 laptop) is not an Options
    # size, and multiplayer must honour it too (W1, Phase 11).
    CASES = (((1600, 900), True), ((1696, 954), False), ((1696, 954), True), ((1088, 612), False))

    def launch_env(self, size, fullscreen):
        # The launcher must pass the real windowed size (state.WINDOWED_*) and the fullscreen choice instead.
        from solitaireplus.app import multiplayer_launcher
        saved = {name: getattr(state, name, MISSING) for name in ("WINDOWED_WIDTH", "WINDOWED_HEIGHT", "fullscreen_enabled")}
        try:
            (state.WINDOWED_WIDTH, state.WINDOWED_HEIGHT), state.fullscreen_enabled = size, fullscreen
            with mock.patch.object(subprocess, "Popen") as popen:
                self.assertTrue(multiplayer_launcher.MultiplayerLauncher().launch())
            return popen.call_args.kwargs["env"]
        finally:
            for name, value in saved.items():
                if value is MISSING:
                    delattr(state, name)
                else:
                    setattr(state, name, value)

    def test_multiplayer_window_inherits_the_players_window_size_and_fullscreen_choice(self):
        for size, fullscreen in self.CASES:
            with self.subTest(size=size, fullscreen=fullscreen):
                env = self.launch_env(size, fullscreen)
                self.assertEqual(env["SOLITAIRE_MP_WINDOW"], f"{size[0]}x{size[1]}")
                self.assertEqual(env["SOLITAIRE_MP_FULLSCREEN"], "1" if fullscreen else "0")

    def test_multiplayer_options_read_the_handoff(self):
        # The other end: multiplayer/mp_options.py turns the launcher's variables into the start
        # size and fullscreen choice (open_window then clamps the size to the screen).
        sys.path.insert(0, str(ROOT / "multiplayer"))
        try:
            import mp_options
        finally:
            sys.path.remove(str(ROOT / "multiplayer"))
        for size, fullscreen in self.CASES:
            with self.subTest(size=size, fullscreen=fullscreen):
                self.assertEqual(mp_options.inherited_window(self.launch_env(size, fullscreen)), (size, fullscreen))


if __name__ == "__main__":
    unittest.main()
