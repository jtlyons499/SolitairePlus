"""The game window: the fixed 1366x768 game surface, window size, fullscreen, mouse mapping and
presenting each frame.

The game always draws on ``game_surface`` (1366x768). The window is a plain resizable window of
any size; ``present()`` scales the picture to fill it, keeping the 16:9 shape (black bars only
when the window or screen is not 16:9, for example a 16:10 monitor in fullscreen).
``window_to_game_coords()`` and ``translate_event()`` turn window mouse positions back into
1366x768 game coordinates.

Do not use pygame's SCALED mode: it does not rescale after the window is resized (measured with
pygame-ce 2.5.8 at 125% Windows scaling, the picture stayed 1366x768 in the middle of a
1696x954 window, with wide black borders).

Window size rules (W1 in docs/dev/RESTRUCTURE_BRIEF.md):
* the process is DPI-aware, so sizes are real screen pixels (no blurry stretching by Windows);
* the default window is the largest 16:9 size that fits in 90% of the usable screen area (the
  work area without the taskbar, minus the title bar and frame), never above 2560x1440 and never
  below 1024x576;
* Options only offers sizes that fit; a saved size that no longer fits is replaced on start-up;
* the window is centred whenever it is created, resized or brought back from fullscreen;
* fullscreen is desktop fullscreen on the window's monitor (no display mode change).

Importing this module has no side effects; ``open_window()`` creates the window at start-up.
The multiplayer window uses the same code: it opens with its own caption and starting size and
sets ``state.window_custom_cursor = False`` (it has no single-player cursor choices).
"""
from __future__ import annotations

import ctypes
import math
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
ASPECT_TOLERANCE = 0.01      # a window this close to the game's shape is filled exactly (no bars)

# Everything in the game is designed at 1366 x 768 regardless of the window size.
game_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
_scaled_frame = {"surface": None}   # reused target for the scaled picture (same size as the picture)

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


def picture_rect(window_size):
    """Where the 16:9 game picture goes in a window of this size: as large as fits, centred."""
    width, height = max(1, int(window_size[0])), max(1, int(window_size[1]))
    # 1366x768 is a hair wider than true 16:9 (1920x1080, 1696x954 ...): fill those windows
    # completely; the 0.05% stretch is invisible, a 1-pixel black line would not be.
    if abs((width / height) / (BASE_WIDTH / BASE_HEIGHT) - 1) <= ASPECT_TOLERANCE:
        return pygame.Rect(0, 0, width, height)
    scale = min(width / BASE_WIDTH, height / BASE_HEIGHT)
    picture_width = max(1, min(width, round(BASE_WIDTH * scale)))
    picture_height = max(1, min(height, round(BASE_HEIGHT * scale)))
    return pygame.Rect((width - picture_width) // 2, (height - picture_height) // 2,
                       picture_width, picture_height)


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
    """The smallest size a player can drag the window to (the picture is scaled down to fit)."""
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
    """Create the game window (once per process, at start-up): resizable and centred.

    ``size`` is a starting window size (for example the one handed over from single-player); it is
    used only if it fits this screen, otherwise (and when it is None) the default size is used.
    The window opens first, so the work area is measured on the monitor it opens on."""
    state.screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption(caption)
    size = clamp_window_size(size, usable_area())
    state.WINDOW_WIDTH, state.WINDOW_HEIGHT = size
    state.WINDOWED_WIDTH, state.WINDOWED_HEIGHT = size
    _request_window_size(size)


def set_window_size(width, height):
    """Windowed mode at this size (leaves fullscreen first), centred on its monitor."""
    if state.fullscreen_enabled:
        _set_sdl_fullscreen(False)
        state.fullscreen_enabled = False
    state.WINDOWED_WIDTH = int(width)
    state.WINDOWED_HEIGHT = int(height)
    state.WINDOW_WIDTH = state.WINDOWED_WIDTH
    state.WINDOW_HEIGHT = state.WINDOWED_HEIGHT
    _request_window_size((state.WINDOW_WIDTH, state.WINDOW_HEIGHT))
    if state.window_custom_cursor:
        cursors.apply_selected_cursor()


def _set_sdl_fullscreen(enabled):
    """Desktop fullscreen (borderless, the monitor keeps its resolution) or back to a window."""
    window = _sdl_window()
    if window is None:
        pygame.display.toggle_fullscreen()
        return
    try:
        if enabled:
            window.set_fullscreen(desktop=True)
        else:
            window.set_windowed()
    except pygame.error:
        pygame.display.toggle_fullscreen()


def set_fullscreen_enabled(enabled):
    """Desktop fullscreen on the window's monitor, or back to the centred window."""
    enabled = bool(enabled)
    if enabled == state.fullscreen_enabled:
        return
    _set_sdl_fullscreen(enabled)
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


def _current_picture_rect():
    surface = pygame.display.get_surface()
    if surface is None:
        return pygame.Rect(0, 0, BASE_WIDTH, BASE_HEIGHT)
    return picture_rect(surface.get_size())


def window_to_game_coords(pos, rect=None):
    """Window mouse position -> 1366x768 game coordinates. Positions in a black bar fall outside
    0..1366 x 0..768, so nothing there is hovered or clicked."""
    rect = rect or _current_picture_rect()
    if rect.size == (BASE_WIDTH, BASE_HEIGHT):
        return (math.floor(pos[0] - rect.x), math.floor(pos[1] - rect.y))
    return (math.floor((pos[0] - rect.x) * BASE_WIDTH / rect.width),
            math.floor((pos[1] - rect.y) * BASE_HEIGHT / rect.height))


def translate_event(event, rect=None):
    """The same event with its mouse position (and movement) in game coordinates."""
    if not hasattr(event, "pos"):
        return event
    rect = rect or _current_picture_rect()
    if rect == pygame.Rect(0, 0, BASE_WIDTH, BASE_HEIGHT):
        return event
    data = dict(event.dict)
    data["pos"] = window_to_game_coords(event.pos, rect)
    if "rel" in data:
        data["rel"] = (round(event.rel[0] * BASE_WIDTH / rect.width),
                       round(event.rel[1] * BASE_HEIGHT / rect.height))
    return pygame.event.Event(event.type, data)


def get_events():
    """pygame.event.get() with mouse positions in game coordinates."""
    rect = _current_picture_rect()
    return [translate_event(event, rect) for event in pygame.event.get()]


def present():
    """Show the frame: scale the 1366x768 picture to fill the window (16:9, centred)."""
    _finish_pending_resize()
    # Always the current display surface: resizing or fullscreen may replace it.
    state.screen = pygame.display.get_surface()
    rect = picture_rect(state.screen.get_size())
    if rect.size == (BASE_WIDTH, BASE_HEIGHT):
        state.screen.blit(game_surface, rect)
    else:
        frame = _scaled_frame["surface"]
        if frame is None or frame.get_size() != rect.size:
            frame = _scaled_frame["surface"] = pygame.Surface(rect.size)
        pygame.transform.smoothscale(game_surface, rect.size, frame)
        state.screen.blit(frame, rect)
    width, height = state.screen.get_size()
    for bar in (pygame.Rect(0, 0, width, rect.top),                       # black bars, if any
                pygame.Rect(0, rect.bottom, width, height - rect.bottom),
                pygame.Rect(0, rect.top, rect.left, rect.height),
                pygame.Rect(rect.right, rect.top, width - rect.right, rect.height)):
        if bar.width > 0 and bar.height > 0:
            state.screen.fill((0, 0, 0), bar)

    # Software cursor fallback (accessible-size or unsupported colour cursors)
    if state.software_cursor_fallback and state.cursor_image is not None:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        state.screen.blit(state.cursor_image, (mouse_x, mouse_y))

    pygame.display.flip()
