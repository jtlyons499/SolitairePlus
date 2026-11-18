"""W1, multiplayer part: the multiplayer window is solitaireplus/app/window.py.

mp_options.Options decides the start size and fullscreen choice (handed over by single-player,
else saved, else the default size) and window.py opens, resizes and fullscreens the window with
the single-player size rules. The window opens once per process, so each test that opens it
starts a fresh display.
Areas are client areas in real screen pixels, as window.usable_area() returns them.
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
import mp_options
from mp_options import Options, SIZES, inherited_window

ROOT = Path(__file__).resolve().parents[2]
DANS_PC = window.usable_area_from((1920, 1152), (20, 49))    # 1920x1200 at 125%: (1900, 1103)
LAPTOP = window.usable_area_from((1366, 728), (16, 39))      # 1366x768 at 100%: (1350, 689)
MISSING = object()
WINDOW_STATE = ("screen", "WINDOW_WIDTH", "WINDOW_HEIGHT", "WINDOWED_WIDTH", "WINDOWED_HEIGHT",
                "window_pending_size", "fullscreen_enabled", "window_custom_cursor", "holdem_table_speed")
HANDOFF = ("SOLITAIRE_MP_WINDOW", "SOLITAIRE_MP_FULLSCREEN")


class WindowTestCase(unittest.TestCase):
    def setUp(self):
        self.saved = {name: getattr(state, name, MISSING) for name in WINDOW_STATE}
        self.folder = tempfile.TemporaryDirectory(prefix="mp-window-")
        self.addCleanup(self.folder.cleanup)
        environ = {name: value for name, value in os.environ.items() if name not in HANDOFF}
        environ.update(LOCALAPPDATA=self.folder.name, SDL_VIDEODRIVER="dummy")
        patcher = mock.patch.dict(os.environ, environ, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.options_file = Path(self.folder.name) / "SolitaireMultiplayer" / "options.json"
        state.fullscreen_enabled = False
        state.window_custom_cursor = True

    def tearDown(self):
        pygame.display.quit()
        pygame.display.init()                         # as the test runner left it (no window)
        for name, value in self.saved.items():
            if value is MISSING:
                if hasattr(state, name):
                    delattr(state, name)
            else:
                setattr(state, name, value)

    def write_saved(self, values):
        self.options_file.parent.mkdir(parents=True, exist_ok=True)
        self.options_file.write_text(json.dumps(values), encoding="utf-8")

    def saved_file(self):
        return json.loads(self.options_file.read_text(encoding="utf-8")) if self.options_file.exists() else None

    def make_options(self, saved=None, **handoff):
        if saved is not None:
            self.write_saved(saved)
        with mock.patch.dict(os.environ, handoff):
            return Options()

    def open(self, options, area=DANS_PC):
        """options.open_window() on a fresh dummy display; returns the number of fullscreen toggles."""
        pygame.display.quit()
        pygame.display.init()
        self.assertEqual(pygame.display.get_driver(), "dummy")
        with mock.patch.object(window, "usable_area", return_value=area), \
                mock.patch.object(window, "_set_sdl_fullscreen") as toggle, \
                warnings.catch_warnings():
            warnings.simplefilter("ignore")               # "no fast renderer available" (dummy driver)
            options.open_window()
        return toggle.call_count

    def assert_windowed_size(self, size):
        self.assertEqual((state.WINDOWED_WIDTH, state.WINDOWED_HEIGHT), tuple(size))
        # The SDL window really has that size, also below 1366x768.
        self.assertEqual(tuple(window._sdl_window().size), tuple(size))


class StartSizeTests(WindowTestCase):
    def test_inherited_default_size_with_fullscreen_is_honoured(self):
        # Single-player's own default window (not an Options size) in fullscreen.
        options = self.make_options(SOLITAIRE_MP_WINDOW="1696x954", SOLITAIRE_MP_FULLSCREEN="1")
        self.assertEqual((options.start_size, options.start_fullscreen), ((1696, 954), True))
        self.assertEqual(self.open(options), 1)
        self.assert_windowed_size((1696, 954))
        self.assertTrue(state.fullscreen_enabled)
        self.assertIs(state.window_custom_cursor, False)
        self.assertEqual(pygame.display.get_caption()[0], "Solitaire+ Multiplayer")
        self.assertEqual(state.screen.get_size(), (1696, 954))        # the picture is scaled to fill it
        # Handed-over values are for this start only: nothing is saved.
        self.assertEqual((options.values["size"], options.values["fullscreen"]), (None, False))
        self.assertIsNone(self.saved_file())

    def test_inherited_values_win_but_are_never_saved(self):
        saved = {"size": [1366, 768], "fullscreen": True, "sound": False, "volume": 50}
        options = self.make_options(saved, SOLITAIRE_MP_WINDOW="1600x900", SOLITAIRE_MP_FULLSCREEN="0")
        self.assertEqual(self.open(options), 0)
        self.assert_windowed_size((1600, 900))
        self.assertFalse(state.fullscreen_enabled)
        options.values["volume"] = 25
        options.save()                                   # e.g. a later SFX change
        written = self.saved_file()
        self.assertEqual({name: written[name] for name in saved}, dict(saved, volume=25))

    def test_inherited_or_saved_2560x1440_is_clamped_to_the_default_size(self):
        for label, saved, handoff in (("inherited", None, {"SOLITAIRE_MP_WINDOW": "2560x1440"}),
                                      ("saved", {"size": [2560, 1440]}, {})):
            for area in (DANS_PC, LAPTOP):
                with self.subTest(label, area=area):
                    if self.options_file.exists():
                        self.options_file.unlink()
                    options = self.make_options(saved, **handoff)
                    self.assertEqual(options.start_size, (2560, 1440) if saved is None else [2560, 1440])
                    self.assertEqual(self.open(options, area), 0)
                    self.assert_windowed_size(window.default_window_size(area))
                    self.assertFalse(state.fullscreen_enabled)
        self.assertEqual(window.default_window_size(DANS_PC), (1696, 954))
        self.assertEqual(window.default_window_size(LAPTOP), (1088, 612))

    def test_inherited_size_smaller_than_the_game_picture_is_honoured(self):
        # 1088x612 is single-player's default on a 1366x768 laptop; on a bigger screen it fits too.
        for area in (DANS_PC, LAPTOP):
            with self.subTest(area=area):
                options = self.make_options(SOLITAIRE_MP_WINDOW="1088x612")
                self.assertEqual(self.open(options, area), 0)
                self.assert_windowed_size((1088, 612))

    def test_default_start_and_saved_fullscreen(self):
        options = self.make_options()
        self.assertEqual((options.start_size, options.start_fullscreen), (None, False))
        self.assertEqual(self.open(options), 0)
        self.assert_windowed_size((1696, 954))
        options = self.make_options({"fullscreen": True})
        self.assertEqual(self.open(options), 1)
        self.assertTrue(state.fullscreen_enabled)
        self.assert_windowed_size((1696, 954))           # the size F11 comes back to

    def test_saved_values_are_checked(self):
        # Only Options sizes are taken from the file; a bad size does not lose the other values.
        for size in ([1700, 950], None, "1600x900", 5, [1600]):
            with self.subTest(size=size):
                options = self.make_options({"size": size, "sound": False, "volume": 40})
                self.assertIsNone(options.start_size)
                self.assertEqual((options.values["sound"], options.values["volume"]), (False, 40))
        self.assertEqual(self.make_options({"size": [1920, 1080]}).start_size, [1920, 1080])

    def test_inherited_window_parsing(self):
        cases = {("1696x954", "1"): ((1696, 954), True), ("1600x900", "0"): ((1600, 900), False),
                 ("1088X612", ""): ((1088, 612), None), ("", "1"): (None, True),
                 ("0x0", "yes"): (None, None), ("-1600x900", "2"): (None, None),
                 ("abc", None): (None, None), ("1600x900x2", "0"): (None, False),
                 ("1600 x 900", "1"): ((1600, 900), True)}
        for (size, fullscreen), expected in cases.items():
            with self.subTest(size=size, fullscreen=fullscreen):
                environ = {"SOLITAIRE_MP_WINDOW": size}
                if fullscreen is not None:
                    environ["SOLITAIRE_MP_FULLSCREEN"] = fullscreen
                self.assertEqual(inherited_window(environ), expected)
        self.assertEqual(inherited_window({}), (None, None))
        self.assertEqual(inherited_window(), (None, None))            # os.environ without a hand-off


class RecordingFont:
    """A pygame font that also records the texts it renders."""
    def __init__(self, font, texts):
        self.font, self.texts = font, texts

    def render(self, text, *args):
        self.texts.append(text)
        return self.font.render(text, *args)

    def __getattr__(self, name):
        return getattr(self.font, name)


class OptionsScreenTests(WindowTestCase):
    def setUp(self):
        super().setUp()
        self.options = self.make_options()
        self.open(self.options)
        self.area = mock.patch.object(window, "usable_area", return_value=DANS_PC)
        self.area.start()
        self.addCleanup(self.area.stop)
        self.toggle = mock.patch.object(window, "_set_sdl_fullscreen")
        self.toggle.start()
        self.addCleanup(self.toggle.stop)

    def draw(self):
        labels = []
        real = mp_options.wooden_button

        def record(surface, appearance, rect, label, font, enabled=True, hover=False):
            labels.append((label, enabled))
            return real(surface, appearance, rect, label, font, enabled, hover)

        texts = []
        with mock.patch.object(mp_options, "wooden_button", record), \
                mock.patch.object(self.options, "small", RecordingFont(self.options.small, texts)):
            self.options.draw(window.game_surface, None)
        return labels, texts

    def click(self, action):
        rect = next(rect for rect, item in self.options.buttons if item == action)
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)
        self.options.event(event, rect.center, None)

    def test_set_size_ignores_a_size_that_does_not_fit(self):
        with mock.patch.object(window, "set_window_size", wraps=window.set_window_size) as resize:
            self.assertFalse(self.options.set_size((1920, 1080)))      # 1080 + title bar > 1103
            self.assertFalse(self.options.set_size((2560, 1440)))
            resize.assert_not_called()
            self.assert_windowed_size((1696, 954))
            self.assertIsNone(self.saved_file())
            self.assertTrue(self.options.set_size((1600, 900)))
            resize.assert_called_once_with(1600, 900)
        self.assert_windowed_size((1600, 900))
        self.assertEqual(state.window_pending_size, (1600, 900))       # present() centres it
        self.assertEqual(self.saved_file()["size"], [1600, 900])
        self.assertIs(self.saved_file()["fullscreen"], False)

    def test_size_buttons_follow_the_screen(self):
        labels, texts = self.draw()
        sizes = [(label, enabled) for label, enabled in labels if "×" in label]
        self.assertEqual(sizes, [("1366×768", True), ("1600×900", True), ("1920×1080", False), ("2560×1440", False)])
        self.assertIn("Greyed out: too large for this screen", texts)
        clickable = [item[1] for _, item in self.options.buttons if isinstance(item, tuple) and item[0] == "size"]
        self.assertEqual(clickable, [(1366, 768), (1600, 900)])        # greyed-out sizes cannot be clicked
        self.click(("size", (1600, 900)))
        self.assert_windowed_size((1600, 900))
        labels, _ = self.draw()
        self.assertIn(("1600×900 *", True), labels)                     # the current window size
        # A big screen offers every size and shows no hint.
        with mock.patch.object(window, "usable_area", return_value=(3840, 2082)):
            labels, texts = self.draw()
        self.assertEqual([enabled for label, enabled in labels if "×" in label], [True] * len(SIZES))
        self.assertNotIn("Greyed out: too large for this screen", texts)

    def test_fullscreen_toggle_and_size_click_leave_fullscreen(self):
        self.draw()
        self.click(("toggle", "fullscreen"))
        self.assertTrue(state.fullscreen_enabled)
        self.assertIs(self.saved_file()["fullscreen"], True)
        labels, _ = self.draw()
        self.assertIn(("Fullscreen: On", True), labels)
        self.click(("size", (1366, 768)))                               # back to a window
        self.assertFalse(state.fullscreen_enabled)
        self.assert_windowed_size((1366, 768))
        self.assertEqual(self.saved_file(), dict(self.saved_file(), size=[1366, 768], fullscreen=False))
        self.options.set_fullscreen(True)
        self.options.set_fullscreen(False)
        self.assertFalse(state.fullscreen_enabled)
        self.assert_windowed_size((1366, 768))
        self.assertIs(self.saved_file()["fullscreen"], False)

    def test_default_size_is_not_written(self):
        self.options.values["sound"] = False
        self.options.save()
        self.assertNotIn("size", self.saved_file())
        self.assertIs(self.saved_file()["sound"], False)


# Runs the real launcher (root main.py --multiplayer) in a fresh process with dummy SDL drivers
# and scripted input. Printed as one JSON line.
MAIN_CHILD = r"""
import ctypes, json, os, runpy, sys, warnings
from pathlib import Path
from unittest import mock
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
warnings.simplefilter("ignore")
import pygame
from solitaireplus.app import state, window

AREA = (1900, 1103)                       # 1920x1200 at 125%: default window 1696x954
def click(pos): return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)
def key(code): return pygame.event.Event(pygame.KEYDOWN, key=code, mod=0, unicode="", scancode=0)
SIZE_1600, SIZE_1920, FULLSCREEN = (600, 285), (760, 285), (515, 346)   # Options buttons
passes = [((0, 0), []),                                       # 0 hub
          ((0, 0), [key(pygame.K_ESCAPE)]),                   # 1 Options opens
          ((0, 0), []),                                       # 2
          (SIZE_1600, [click(SIZE_1600)]),                    # 3 1600x900
          (SIZE_1920, [click(SIZE_1920)]),                    # 4 greyed out: nothing
          ((0, 0), [pygame.event.Event(pygame.VIDEORESIZE, size=(1800, 1000), w=1800, h=1000),
                    pygame.event.Event(pygame.WINDOWSIZECHANGED, x=1800, y=1000)]),   # 5 edge drag
          ((0, 0), [key(pygame.K_F11)]),                      # 6 fullscreen
          (FULLSCREEN, [click(FULLSCREEN)]),                  # 7 Options toggle: windowed
          ((0, 0), [key(pygame.K_ESCAPE)]),                   # 8 Options closes
          ((0, 0), [key(pygame.K_F11)]),                      # 9 fullscreen
          ((0, 0), [pygame.event.Event(pygame.QUIT)])]        # 10
current = [-1]
extra = [0]
def events(*args, **kwargs):
    current[0] += 1
    if current[0] >= len(passes):
        extra[0] += 1
        return [pygame.event.Event(pygame.QUIT)]
    return passes[current[0]][1]
def mouse():
    return passes[min(current[0] + 1, len(passes) - 1)][0]
frames = []
def flip():
    frames.append({"pass": current[0], "windowed": [state.WINDOWED_WIDTH, state.WINDOWED_HEIGHT],
                   "fullscreen": state.fullscreen_enabled, "caption": pygame.display.get_caption()[0],
                   "surface": list(pygame.display.get_surface().get_size())})
errors = []
with mock.patch.object(window, "usable_area", return_value=AREA), \
        mock.patch.object(window, "_set_sdl_fullscreen") as toggle, \
        mock.patch("pygame.event.get", side_effect=events), \
        mock.patch("pygame.mouse.get_pos", side_effect=mouse), \
        mock.patch("pygame.display.flip", side_effect=flip), \
        mock.patch.object(window, "_current_picture_rect", return_value=pygame.Rect(0, 0, 1366, 768)):
    sys.argv = [str(ROOT / "main.py"), "--multiplayer"]
    try:
        runpy.run_path(str(ROOT / "main.py"), run_name="__main__")
    except SystemExit as stop:
        if stop.code not in (0, None):
            errors.append("exit %r" % (stop.code,))
    except BaseException as error:
        errors.append(repr(error))
awareness = None
if sys.platform.startswith("win"):
    value = ctypes.c_int(-1)
    if ctypes.windll.shcore.GetProcessDpiAwareness(None, ctypes.byref(value)) == 0:
        awareness = value.value
options_file = Path(os.environ["LOCALAPPDATA"]) / "SolitaireMultiplayer" / "options.json"
loaded = [name for name in ("solitaireplus.app.startup", "solitaireplus.ui.cursors") if name in sys.modules]
print("@@CHILD " + json.dumps({
    "loaded": loaded, "errors": errors, "passes": current[0], "extra": extra[0], "frames": frames,
    "toggles": toggle.call_count,
    "custom_cursor": state.window_custom_cursor, "dpi_awareness": awareness,
    "dpi_hint": os.environ.get("SDL_WINDOWS_DPI_AWARENESS"),
    "saved": json.loads(options_file.read_text(encoding="utf-8")) if options_file.exists() else None,
    "window_module": "solitaireplus.app.window" in sys.modules}))
"""


class MultiplayerMainTests(unittest.TestCase):
    def test_main_uses_the_shared_window_and_never_starts_single_player(self):
        with tempfile.TemporaryDirectory(prefix="mp-window-main-") as temporary:
            env = {name: value for name, value in os.environ.items()
                   if name not in HANDOFF + ("PYTHONPATH", "SDL_WINDOWS_DPI_AWARENESS")}
            env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", PYGAME_HIDE_SUPPORT_PROMPT="1",
                       LOCALAPPDATA=temporary, APPDATA=temporary, PYTHONIOENCODING="utf-8")
            done = subprocess.run([sys.executable, "-c", MAIN_CHILD], cwd=ROOT, env=env, capture_output=True,
                                  text=True, encoding="utf-8", errors="replace", timeout=240)
        lines = [line for line in done.stdout.splitlines() if line.startswith("@@CHILD ")]
        self.assertEqual(len(lines), 1, f"exit {done.returncode}\n{done.stdout[-3000:]}\n{done.stderr[-3000:]}")
        result = json.loads(lines[0][len("@@CHILD "):])
        self.assertEqual(result["errors"], [], done.stderr[-3000:])
        self.assertEqual(result["loaded"], [])                  # no single-player game, no cursors module
        self.assertTrue(result["window_module"])
        self.assertEqual((result["passes"], result["extra"]), (10, 0))  # every pass used, QUIT ended it
        self.assertIs(result["custom_cursor"], False)
        self.assertEqual(result["dpi_hint"], "permonitorv2")
        if sys.platform.startswith("win"):
            self.assertEqual(result["dpi_awareness"], 2)         # per-monitor DPI aware on its own
        by_pass = {frame["pass"]: frame for frame in result["frames"]}
        self.assertEqual(sorted(by_pass), list(range(11)))       # one frame per pass, QUIT's included
        expected = {0: ([1696, 954], False), 2: ([1696, 954], False), 3: ([1600, 900], False),
                    4: ([1600, 900], False), 5: ([1600, 900], False), 6: ([1600, 900], True),
                    7: ([1600, 900], False), 9: ([1600, 900], True)}
        for number, (windowed, fullscreen) in expected.items():
            with self.subTest(number=number):
                self.assertEqual((by_pass[number]["windowed"], by_pass[number]["fullscreen"]), (windowed, fullscreen))
        # The window surface has the window's size (the 1366x768 picture is scaled into it).
        self.assertTrue(all(frame["surface"] == frame["windowed"] for frame in result["frames"]
                            if not frame["fullscreen"] and frame["pass"] > 0), result["frames"])
        self.assertTrue(all(frame["caption"] == "Solitaire+ Multiplayer" for frame in result["frames"]))
        self.assertEqual(result["toggles"], 3)
        self.assertEqual((result["saved"]["size"], result["saved"]["fullscreen"]), ([1600, 900], True))
        self.assertEqual(done.returncode, 0)


if __name__ == "__main__":
    unittest.main()
