"""The game window: the fixed 1366x768 game surface, window size, fullscreen, mouse mapping and
presenting each frame.

The game always draws on ``game_surface`` (1366x768). The window uses pygame's SCALED mode:
SDL scales that picture to whatever size the window has, keeps the 16:9 shape with black bars
when needed (letterboxing), and gives the game mouse positions in 1366x768 coordinates.

Window size rules (W1 in docs/dev/RESTRUCTURE_BRIEF.md):
* the process is DPI-aware, so sizes are real screen pixels (no blurry stretching by Windows);
* the default window is the largest 16:9 size that fits in 90% of the usable screen area (the
  work area without the taskbar, minus the title bar and frame), never above 2560x1440 and never
  below 1024x576;
* Options only offers sizes that fit; a saved size that no longer fits is replaced on start-up;
* the window is centred whenever it is created, resized or brought back from fullscreen;
* fullscreen is desktop fullscreen on the window's monitor (the picture is letterboxed).

Importing this module has no side effects; ``open_window()`` creates the window at start-up.
The multiplayer window uses the same code: it opens with its own caption and starting size and
sets ``state.window_custom_cursor = False`` (it has no single-player cursor choices).
"""
from __future__ import annotations

import ctypes
import os
import sys
import warnings

import pygame

from solitaireplus.app import state
from solitaireplus.app.lazy import lazy
from solitaireplus.games.solitaire.rules import BASE_HEIGHT, BASE_WIDTH

cursors = lazy("solitaireplus.ui.cursors")

FPS = 60

MIN_WINDOW_SIZE = (1024, 576)
MAX_WINDOW_SIZE = (2560, 1440)
SCREEN_FILL = 0.9            # the default window uses at most 90% of the usable area
FALLBACK_DECORATION = (16, 39)   # frame + title bar when Windows cannot be asked

# Everything in the game is designed at 1366 x 768 regardless of the window size.
game_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))

clock = pygame.time.Clock()


# ==================================================
# SIZE RULES (pure, unit-tested)
# ==================================================

def largest_16_9(width, height):
    """The largest 16:9 size (width a multiple of 16) that fits in width x height."""
    best_width = int(min(width, height * 16 / 9)) // 16 * 16
    return (best_width, best_width * 9 // 16)


def fits(size, area):
    return size[0] <= area[0] and size[1] <= area[1]


def default_window_size(area):
    """Default window client size for a usable area (both in screen pixels)."""
    size = largest_16_9(area[0] * SCREEN_FILL, area[1] * SCREEN_FILL)
    if size[0] > MAX_WINDOW_SIZE[0]:
        return MAX_WINDOW_SIZE
    if size[0] < MIN_WINDOW_SIZE[0]:
        return MIN_WINDOW_SIZE
    return size


def window_size_choices(area, options):
    """[(size, fits_on_this_screen)] for the Options buttons, in the given order."""
    return [(tuple(size), fits(size, area)) for size in options]


def clamp_window_size(saved, area):
    """The saved window size if it still fits this screen, otherwise the default size."""
    if saved and len(saved) == 2 and fits(saved, area):
        return (int(saved[0]), int(saved[1]))
    return default_window_size(area)


def usable_area_from(work_area, decoration):
    """Client area left for the window: the work area minus the frame and title bar."""
    return (max(1, work_area[0] - decoration[0]), max(1, work_area[1] - decoration[1]))


# ==================================================
# PLATFORM (Windows: DPI awareness, work area, frame size)
# ==================================================

def enable_dpi_awareness():
    """Call before pygame.display.init(): sizes become real pixels, nothing is stretched by Windows."""
    os.environ.setdefault("SDL_WINDOWS_DPI_AWARENESS", "permonitorv2")
    if not sys.platform.startswith("win"):
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)          # per-monitor aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


class _Rect(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


class _MonitorInfo(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_ulong), ("rcMonitor", _Rect), ("rcWork", _Rect), ("dwFlags", ctypes.c_ulong)]


def _window_handle():
    try:
        return pygame.display.get_wm_info().get("window")
    except pygame.error:
        return None


def work_area():
    """(width, height) of the work area (screen minus taskbar) of the window's monitor."""
    if sys.platform.startswith("win"):
        try:
            user32 = ctypes.windll.user32
            handle = _window_handle()
            if handle:
                monitor = user32.MonitorFromWindow(handle, 2)            # MONITOR_DEFAULTTONEAREST
                info = _MonitorInfo()
                info.cbSize = ctypes.sizeof(_MonitorInfo)
                if monitor and user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
                    work = info.rcWork
                    return (work.right - work.left, work.bottom - work.top)
            work = _Rect()
            if user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(work), 0):   # SPI_GETWORKAREA
                return (work.right - work.left, work.bottom - work.top)
        except Exception:
            pass
    try:
        width, height = pygame.display.get_desktop_sizes()[0]
        return (width, height - 48)
    except (pygame.error, IndexError):
        return MAX_WINDOW_SIZE


def window_decoration():
    """(extra width, extra height) the frame and title bar add around the client area."""
    if sys.platform.startswith("win"):
        try:
            user32 = ctypes.windll.user32
            handle = _window_handle()
            dpi = user32.GetDpiForWindow(handle) if handle and hasattr(user32, "GetDpiForWindow") else 0
            if dpi and hasattr(user32, "GetSystemMetricsForDpi"):
                metric = lambda index: user32.GetSystemMetricsForDpi(index, dpi)  # noqa: E731
            else:
                metric = user32.GetSystemMetrics
            frame = metric(32) + metric(92)          # SM_CXSIZEFRAME + SM_CXPADDEDBORDER
            caption = metric(4)                      # SM_CYCAPTION
            if caption > 0:
                return (2 * frame, caption + 2 * frame)
        except Exception:
            pass
    return FALLBACK_DECORATION


def usable_area():
    return usable_area_from(work_area(), window_decoration())


# ==================================================
# WINDOW
# ==================================================

def _sdl_window():
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            return pygame.Window.from_display_module()
    except (pygame.error, AttributeError):
        return None


def _allow_small_window(window):
    """Let the window be smaller than the 1366x768 game picture (SDL scales it down).

    pygame's SCALED mode makes the game size the window's minimum size, and sets it again
    after fullscreen; SDL then quietly keeps any smaller size at 1366x768 (for example the
    1088x612 default of a 1366x768 laptop), so the window no longer fits the screen."""
    try:
        if tuple(window.minimum_size) != MIN_WINDOW_SIZE:
            window.minimum_size = MIN_WINDOW_SIZE
    except (pygame.error, AttributeError, TypeError, ValueError):
        pass


def _request_window_size(size):
    """Resize and centre the window. SDL applies a new size a frame or two later, so present()
    keeps checking until it has, then centres the window again."""
    state.window_pending_size = tuple(size)
    window = _sdl_window()
    if window is not None:
        _allow_small_window(window)
        try:
            window.size = tuple(size)
            window.position = pygame.WINDOWPOS_CENTERED
        except (pygame.error, TypeError, ValueError):
            pass


def _finish_pending_resize():
    size = state.window_pending_size
    if size is None or state.fullscreen_enabled:
        return
    window = _sdl_window()
    if window is None:
        state.window_pending_size = None
        return
    try:
        if tuple(window.size) != size:
            _allow_small_window(window)
            window.size = size
            return
        window.position = pygame.WINDOWPOS_CENTERED
    except (pygame.error, TypeError, ValueError):
        pass
    state.window_pending_size = None


def open_window(caption="Solitaire", size=None):
    """Create the game window (once per process, at start-up): scaled, resizable, centred.

    ``size`` is a starting window size (for example the one handed over from single-player); it is
    used only if it fits this screen, otherwise (and when it is None) the default size is used.
    Call it only once: pygame-ce 2.5.8 crashes on a second SCALED set_mode after a resize."""
    state.screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.SCALED | pygame.RESIZABLE)
    pygame.display.set_caption(caption)
    size = clamp_window_size(size, usable_area())
    state.WINDOW_WIDTH, state.WINDOW_HEIGHT = size
    state.WINDOWED_WIDTH, state.WINDOWED_HEIGHT = size
    _request_window_size(size)


def set_window_size(width, height):
    """Windowed mode at this size (leaves fullscreen first), centred on its monitor."""
    if state.fullscreen_enabled:
        pygame.display.toggle_fullscreen()
        state.fullscreen_enabled = False
    state.WINDOWED_WIDTH = int(width)
    state.WINDOWED_HEIGHT = int(height)
    state.WINDOW_WIDTH = state.WINDOWED_WIDTH
    state.WINDOW_HEIGHT = state.WINDOWED_HEIGHT
    _request_window_size((state.WINDOW_WIDTH, state.WINDOW_HEIGHT))
    if state.window_custom_cursor:
        cursors.apply_selected_cursor()


def set_fullscreen_enabled(enabled):
    """Desktop fullscreen on the window's monitor, or back to the centred window."""
    enabled = bool(enabled)
    if enabled == state.fullscreen_enabled:
        return
    pygame.display.toggle_fullscreen()
    state.fullscreen_enabled = enabled
    if enabled:
        try:
            state.WINDOW_WIDTH, state.WINDOW_HEIGHT = pygame.display.get_desktop_sizes()[0]
        except (pygame.error, IndexError):
            pass
    else:
        state.WINDOW_WIDTH = state.WINDOWED_WIDTH
        state.WINDOW_HEIGHT = state.WINDOWED_HEIGHT
        _request_window_size((state.WINDOW_WIDTH, state.WINDOW_HEIGHT))
    if state.window_custom_cursor:
        cursors.apply_selected_cursor()


def window_to_game_coords(pos):
    """Mouse position -> game coordinates. In SCALED mode SDL already reports game coordinates
    (including the letterbox bars, which fall outside 0..1366 x 0..768)."""
    return (int(pos[0]), int(pos[1]))


def present():
    """Show the frame: SDL scales the 1366x768 picture into the window."""
    _finish_pending_resize()
    # Always the current display surface: resizing or fullscreen may replace it.
    state.screen = pygame.display.get_surface()
    state.screen.blit(game_surface, (0, 0))

    # Software cursor fallback (accessible-size or unsupported colour cursors)
    if state.software_cursor_fallback and state.cursor_image is not None:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        state.screen.blit(state.cursor_image, (mouse_x, mouse_y))

    pygame.display.flip()
