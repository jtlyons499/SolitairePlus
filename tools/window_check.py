"""W1 check on a real screen: does the game window stay fully on-screen with its title bar visible?

    python tools/window_check.py source              # run main.py from source and check
    python tools/window_check.py packaged [--exe dist/SolitairePlus/SolitairePlus.exe]
    python tools/window_check.py source --multiplayer      # the same for the multiplayer window
    python tools/window_check.py packaged --multiplayer

Windows only. It opens the real game window (and switches it to fullscreen and back), so don't
use the PC while it runs (about a minute; with --multiplayer about three). It never changes
system settings. For each step it prints the window's visible rectangle (DWM extended frame
bounds), its client size and the monitor's work area:

* source: starts with no saved size, then with a saved 2560x1440 window size (must be clamped),
  then with saved fullscreen; at each start: the start-up window, 5 x F11 (fullscreen and back),
  and every window size the Options screen offers.
* packaged: starts the exe (with a temporary LOCALAPPDATA, so your saves and settings are not
  touched), checks the start-up window, then sends F11 five times and checks after each.
* --multiplayer: runs `main.py --multiplayer` (source) or `SolitairePlus.exe --multiplayer`
  (packaged) with a temporary LOCALAPPDATA holding SolitaireMultiplayer\\options.json and a
  profile. Starts: no saved size, saved 2560x1440, saved fullscreen, and the window handed over
  by single-player (SOLITAIRE_MP_WINDOW) 1600x900, 1088x612, 2560x1440 and 1600x900 with
  SOLITAIRE_MP_FULLSCREEN=1. Extra checks: the process is per-monitor DPI aware (2), the caption
  is 'Solitaire+ Multiplayer' and (source only) the single-player game and its cursors module
  were never imported. It also prints the window's DPI.

Source runs also check that a windowed start-up has the size it should have (the saved or
handed-over size if it fits the screen, else the default size; also below 1366x768) and that
its client area is centred on the monitor.

Picture checks (after every step) read what is really on the screen inside the window's client
area and check that the game picture fills it: no black bars in a 16:9 window, and in fullscreen
on a screen of another shape only the bars that keep the picture 16:9 (for example 60 pixels top
and bottom on 1920x1200). Source runs paint the whole game picture magenta for one frame and
measure it; packaged runs measure the black bars around whatever the game shows.

Exit code 0 = every windowed check is inside the work area, every fullscreen check covers
the monitor, and every extra check passed.
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "support" / "fixtures" / "profile_1.json"

user32 = ctypes.windll.user32 if sys.platform.startswith("win") else None
dwmapi = ctypes.windll.dwmapi if sys.platform.startswith("win") else None

MP_CAPTION = "Solitaire+ Multiplayer"
# Variables a parent process may have set that would change how the multiplayer window starts.
# They are removed from the child environment unless a start case sets them.
MP_ENV_CLEARED = ("SOLITAIRE_MP_WINDOW", "SOLITAIRE_MP_FULLSCREEN", "SDL_WINDOWS_DPI_AWARENESS",
                  "SOLITAIRE_NET_INPROCESS")
# (label, saved SolitaireMultiplayer\options.json or None for no file, environment)
MP_STARTS = [
    ("no saved size", None, {}),
    ("saved 2560x1440", {"size": [2560, 1440]}, {}),
    ("saved fullscreen", {"fullscreen": True}, {}),
    ("inherited 1600x900", None, {"SOLITAIRE_MP_WINDOW": "1600x900", "SOLITAIRE_MP_FULLSCREEN": "0"}),
    ("inherited 1088x612", None, {"SOLITAIRE_MP_WINDOW": "1088x612", "SOLITAIRE_MP_FULLSCREEN": "0"}),
    ("inherited 2560x1440", None, {"SOLITAIRE_MP_WINDOW": "2560x1440", "SOLITAIRE_MP_FULLSCREEN": "0"}),
    ("inherited 1600x900 fullscreen", None, {"SOLITAIRE_MP_WINDOW": "1600x900", "SOLITAIRE_MP_FULLSCREEN": "1"}),
]


class MonitorInfo(ctypes.Structure):
    _fields_ = [("cbSize", wt.DWORD), ("rcMonitor", wt.RECT), ("rcWork", wt.RECT), ("dwFlags", wt.DWORD)]


def as_tuple(rect):
    return (rect.left, rect.top, rect.right, rect.bottom)


def visible_rect(hwnd):
    """The window as the user sees it (without the invisible resize borders of Windows 10/11)."""
    rect = wt.RECT()
    if dwmapi is not None and dwmapi.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(rect), ctypes.sizeof(rect)) == 0:
        return as_tuple(rect)
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return as_tuple(rect)


def client_size(hwnd):
    rect = wt.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    return (rect.right - rect.left, rect.bottom - rect.top)


def monitor_rects(hwnd):
    monitor = user32.MonitorFromWindow(hwnd, 2)
    info = MonitorInfo()
    info.cbSize = ctypes.sizeof(MonitorInfo)
    user32.GetMonitorInfoW(monitor, ctypes.byref(info))
    return as_tuple(info.rcMonitor), as_tuple(info.rcWork)


def inside(inner, outer):
    return inner[0] >= outer[0] and inner[1] >= outer[1] and inner[2] <= outer[2] and inner[3] <= outer[3]


def check(hwnd, label, fullscreen):
    window = visible_rect(hwnd)
    monitor, work = monitor_rects(hwnd)
    ok = (window == monitor) if fullscreen else inside(window, work)
    size = (window[2] - window[0], window[3] - window[1])
    client = client_size(hwnd)
    print(f"  {'ok ' if ok else 'BAD'} {label:<34} window {window} size {size}  "
          f"{'monitor' if fullscreen else 'work area'} {monitor if fullscreen else work}  "
          f"client {client[0]}x{client[1]}", flush=True)
    return {"label": label, "window": window, "monitor": monitor, "work": work, "fullscreen": fullscreen,
            "client": client, "ok": ok}


class _BitmapInfoHeader(ctypes.Structure):
    _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG), ("biPlanes", wt.WORD),
                ("biBitCount", wt.WORD), ("biCompression", wt.DWORD), ("biSizeImage", wt.DWORD),
                ("biXPelsPerMeter", wt.LONG), ("biYPelsPerMeter", wt.LONG), ("biClrUsed", wt.DWORD),
                ("biClrImportant", wt.DWORD)]


def capture_client(hwnd):
    """(width, height, BGRA bytes) of what the screen shows inside the window's client area."""
    gdi32 = ctypes.windll.gdi32
    width, height = client_size(hwnd)
    origin = wt.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(origin))
    screen_dc = user32.GetDC(0)
    memory_dc = gdi32.CreateCompatibleDC(screen_dc)
    bitmap = gdi32.CreateCompatibleBitmap(screen_dc, width, height)
    old = gdi32.SelectObject(memory_dc, bitmap)
    try:
        gdi32.BitBlt(memory_dc, 0, 0, width, height, screen_dc, origin.x, origin.y, 0x00CC0020)   # SRCCOPY
        info = _BitmapInfoHeader()
        info.biSize = ctypes.sizeof(info)
        info.biWidth, info.biHeight, info.biPlanes, info.biBitCount = width, -height, 1, 32
        pixels = (ctypes.c_ubyte * (width * height * 4))()
        gdi32.GetDIBits(memory_dc, bitmap, 0, height, pixels, ctypes.byref(info), 0)
    finally:
        gdi32.SelectObject(memory_dc, old)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(memory_dc)
        user32.ReleaseDC(0, screen_dc)
    return width, height, bytes(pixels)


def expected_picture(client):
    sys.path.insert(0, str(ROOT))
    from solitaireplus.app.window import picture_rect
    rect = picture_rect(client)
    return (rect.x, rect.y, rect.width, rect.height)


def measure_picture(capture, is_picture):
    """(x, y, width, height) of the picture: the extent of pixels for which is_picture(b, g, r)
    holds, along the middle row and the middle column (sampled every pixel)."""
    width, height, pixels = capture
    def hit(x, y):
        i = (y * width + x) * 4
        return is_picture(pixels[i], pixels[i + 1], pixels[i + 2])
    xs = [x for x in range(width) if hit(x, height // 2)]
    ys = [y for y in range(height) if hit(width // 2, y)]
    if not xs or not ys:
        return (0, 0, 0, 0)
    return (xs[0], ys[0], xs[-1] - xs[0] + 1, ys[-1] - ys[0] + 1)


def picture_check(hwnd, label, capture, is_picture, tolerance=2):
    client = (capture[0], capture[1])
    want = expected_picture(client)
    got = measure_picture(capture, is_picture)
    ok = all(abs(a - b) <= tolerance for a, b in zip(got, want))
    fill = 100 * got[2] * got[3] / max(1, client[0] * client[1])
    print(f"  {'ok ' if ok else 'BAD'} {label:<34} picture {got[2]}x{got[3]} at ({got[0]},{got[1]}) "
          f"in client {client[0]}x{client[1]} = {fill:.0f}%  (want {want[2]}x{want[3]} at ({want[0]},{want[1]}))",
          flush=True)
    return {"label": label, "client": list(client), "picture": list(got), "expected": list(want), "ok": ok}


def not_black(b, g, r):
    return max(b, g, r) > 8


def magenta(b, g, r):
    return r > 200 and b > 200 and g < 60


def start_size_check(hwnd, label, expected):
    """The start-up window has the size it should have (the requested size if it fits the
    screen, else the default size for it) and is centred: SDL centres the client area on the
    monitor."""
    client = client_size(hwnd)
    origin = wt.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(origin))
    monitor, _work = monitor_rects(hwnd)
    offset = (origin.x + client[0] / 2 - (monitor[0] + monitor[2]) / 2,
              origin.y + client[1] / 2 - (monitor[1] + monitor[3]) / 2)
    centred = abs(offset[0]) <= 2 and abs(offset[1]) <= 2
    ok = tuple(client) == tuple(expected) and centred
    print(f"  {'ok ' if ok else 'BAD'} {label:<34} client {client[0]}x{client[1]} "
          f"(want {expected[0]}x{expected[1]}), centre offset {offset[0]:+.1f},{offset[1]:+.1f}",
          flush=True)
    return {"label": label, "client": client, "expected": list(expected), "centred": centred, "ok": ok}


def window_dpi(hwnd):
    return user32.GetDpiForWindow(hwnd) if hasattr(user32, "GetDpiForWindow") else 0


def process_dpi_awareness(handle=None):
    """0 unaware, 1 system aware, 2 per-monitor aware; None if Windows cannot tell.
    handle None = this process."""
    value = ctypes.c_int(-1)
    try:
        if ctypes.windll.shcore.GetProcessDpiAwareness(handle, ctypes.byref(value)) == 0:
            return value.value
    except (AttributeError, OSError):
        pass
    return None


def other_process_dpi_awareness(pid):
    kernel32 = ctypes.windll.kernel32
    kernel32.OpenProcess.restype = wt.HANDLE
    handle = kernel32.OpenProcess(0x1000, False, pid)          # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return None
    try:
        return process_dpi_awareness(handle)
    finally:
        kernel32.CloseHandle(handle)


def window_caption(hwnd):
    buffer = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, buffer, len(buffer))
    return buffer.value


def extra_check(label, awareness, caption, loaded, dpi):
    """The multiplayer extras: DPI awareness, caption and (if known) the modules never loaded."""
    problems = []
    if awareness != 2:
        problems.append(f"DPI awareness {awareness} (want 2)")
    if caption != MP_CAPTION:
        problems.append(f"caption {caption!r}")
    if loaded:
        problems.append(f"loaded {', '.join(loaded)}")
    ok = not problems
    modules = "not checked (packaged)" if loaded is None else ("none loaded" if not loaded else ", ".join(loaded))
    print(f"  {'ok ' if ok else 'BAD'} {label:<34} DPI awareness {awareness}, window DPI {dpi} "
          f"({dpi * 100 // 96 if dpi else '?'}%), caption {caption!r}, start-up/cursors: {modules}"
          + (f"  -- {'; '.join(problems)}" if problems else ""), flush=True)
    return {"label": label, "awareness": awareness, "caption": caption, "loaded": loaded, "dpi": dpi, "ok": ok}


def prepare_appdata(folder: Path, settings: dict) -> Path:
    data = folder / "SimpleSolitaire"
    (data / "saves").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FIXTURE, data / "saves" / "profile_1.json")
    (data / "app_settings.json").write_text(json.dumps({"auto_update_check": False, **settings}), encoding="utf-8")
    return folder


def prepare_mp_appdata(folder: Path, options) -> Path:
    """SolitaireMultiplayer\\options.json (only if options is a dict) and a profile, UTF-8 without BOM."""
    data = folder / "SolitaireMultiplayer"
    (data / "profiles").mkdir(parents=True, exist_ok=True)
    (data / "profiles" / "profile_1.json").write_text(json.dumps({"version": 1, "name": "Window Check"}),
                                                       encoding="utf-8")
    if options is not None:
        (data / "options.json").write_text(json.dumps(options), encoding="utf-8")
    return folder


def mp_child_env(appdata: Path, extra: dict) -> dict:
    env = dict(os.environ, LOCALAPPDATA=str(appdata), PYGAME_HIDE_SUPPORT_PROMPT="1")
    for name in MP_ENV_CLEARED + ("SDL_VIDEODRIVER",):
        env.pop(name, None)
    env.update(extra)
    return env


def mp_requested_size(options, extra):
    """The start size a multiplayer case asks for: the handed-over size, else the saved one
    (None = the default size). open_window() keeps it only if it fits the screen."""
    handed = extra.get("SOLITAIRE_MP_WINDOW")
    if handed:
        return [int(part) for part in handed.lower().split("x")]
    return (options or {}).get("size")


def mp_start_fullscreen(options, extra) -> bool:
    """What the multiplayer window should start with: the handed-over choice, else the saved one."""
    handed = extra.get("SOLITAIRE_MP_FULLSCREEN")
    if handed in ("0", "1"):
        return handed == "1"
    return bool((options or {}).get("fullscreen"))


# ------------------------------------------------------------------ source: scripted run of main.py

def source_child(out_path: str, multiplayer: bool = False) -> None:
    """Runs inside a child process: start main.py and drive it from pygame.display.flip()."""
    import runpy
    sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)
    import pygame

    results = []
    real_flip = pygame.display.flip
    frames = {"n": 0}

    def single_player_loaded():
        return [name for name in ("solitaireplus.app.startup", "solitaireplus.ui.cursors") if name in sys.modules]

    probing = {"on": False}

    def picture(hwnd, label):
        """Show one all-magenta game picture and measure how much of the client area it fills."""
        from solitaireplus.app import window
        saved = window.game_surface.copy()
        probing["on"] = True
        try:
            window.game_surface.fill((255, 0, 255))
            window.present()
            time.sleep(0.25)                      # let the compositor show it
            capture = capture_client(hwnd)
        finally:
            window.game_surface.blit(saved, (0, 0))
            probing["on"] = False
        return picture_check(hwnd, label, capture, magenta)

    def steps():
        from solitaireplus.app import state, window
        from solitaireplus.app.settings import RESOLUTION_OPTIONS
        yield 90
        hwnd = pygame.display.get_wm_info()["window"]
        results.append(check(hwnd, "start-up", state.fullscreen_enabled))
        results.append(picture(hwnd, "start-up picture"))
        if not state.fullscreen_enabled:
            request = json.loads(os.environ.get("WINDOW_CHECK_REQUEST") or "null")
            results.append(start_size_check(hwnd, "start-up size and centre",
                                            window.clamp_window_size(request, window.usable_area())))
        if multiplayer:
            results.append(extra_check("start-up extras", process_dpi_awareness(), pygame.display.get_caption()[0],
                                       single_player_loaded(), window_dpi(hwnd)))
        for round_number in range(1, 6):
            for _ in range(2):
                pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F11, mod=0, unicode="", scancode=0))
                yield 60
                results.append(check(hwnd, f"F11 #{round_number} -> "
                                     f"{'fullscreen' if state.fullscreen_enabled else 'window'}",
                                     state.fullscreen_enabled))
                results.append(picture(hwnd, f"F11 #{round_number} picture"))
        if state.fullscreen_enabled:
            window.set_fullscreen_enabled(False)
            yield 60
        for size, fits in window.window_size_choices(window.usable_area(), RESOLUTION_OPTIONS):
            if not fits:
                print(f"      (Options greys out {size[0]}x{size[1]}: too large for this screen)")
                continue
            window.set_window_size(*size)          # what clicking the Options button does
            yield 60
            results.append(check(hwnd, f"Options size {size[0]}x{size[1]}", False))
            results.append(picture(hwnd, f"Options size {size[0]}x{size[1]} picture"))
        if multiplayer:
            results.append(extra_check("extras at the end", process_dpi_awareness(), pygame.display.get_caption()[0],
                                       single_player_loaded(), window_dpi(hwnd)))

    script = steps()
    wait = {"n": 0}

    def hook():
        real_flip()
        if probing["on"]:
            return
        frames["n"] += 1
        if wait["n"] > 0:
            wait["n"] -= 1
            return
        try:
            wait["n"] = next(script)
        except StopIteration:
            Path(out_path).write_text(json.dumps(results), encoding="utf-8")
            raise SystemExit(0)

    pygame.display.flip = hook
    sys.argv = [str(ROOT / "main.py")] + (["--multiplayer"] if multiplayer else [])
    runpy.run_path(str(ROOT / "main.py"), run_name="__main__")


def run_source_child(label, appdata: Path, env: dict, multiplayer: bool) -> list:
    out = appdata / "result.json"
    command = [sys.executable, str(Path(__file__).resolve()), "_source_child", str(out)]
    if multiplayer:
        command.append("--multiplayer")
    done = subprocess.run(command, cwd=ROOT, env=env, timeout=300)
    if not out.is_file():
        print(f"  BAD the game did not finish the checks (exit code {done.returncode})")
        return [{"label": f"{label}: run", "ok": False}]
    items = json.loads(out.read_text(encoding="utf-8"))
    for item in items:
        item["label"] = f"{label}: {item['label']}"
    return items


def run_source() -> list:
    starts = [("no saved size", {}), ("saved 2560x1440", {"window_size": [2560, 1440]}),
              ("saved fullscreen", {"fullscreen": True})]
    everything = []
    for label, settings in starts:
        print(f"\n== source, {label}", flush=True)
        with tempfile.TemporaryDirectory(prefix="window-check-") as temporary:
            appdata = prepare_appdata(Path(temporary), settings)
            env = dict(os.environ, LOCALAPPDATA=str(appdata), PYGAME_HIDE_SUPPORT_PROMPT="1",
                       WINDOW_CHECK_REQUEST=json.dumps(settings.get("window_size")))
            env.pop("SDL_VIDEODRIVER", None)
            everything += run_source_child(label, appdata, env, False)
    return everything


def run_source_multiplayer() -> list:
    everything = []
    for label, options, extra in MP_STARTS:
        print(f"\n== source --multiplayer, {label}", flush=True)
        with tempfile.TemporaryDirectory(prefix="window-check-mp-") as temporary:
            appdata = prepare_mp_appdata(Path(temporary), options)
            env = mp_child_env(appdata, extra)
            env["WINDOW_CHECK_REQUEST"] = json.dumps(mp_requested_size(options, extra))
            everything += run_source_child(f"multiplayer {label}", appdata, env, True)
    return everything


# ------------------------------------------------------------------ packaged: the real exe

def find_window(pid, timeout=30.0):
    found = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def callback(hwnd, _):
        owner = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and user32.IsWindowVisible(hwnd):
            left, top, right, bottom = visible_rect(hwnd)
            if right - left >= 640 and bottom - top >= 360:     # the game window, not a helper window
                found.append(((right - left) * (bottom - top), hwnd))
        return True

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        found.clear()
        user32.EnumWindows(callback, 0)
        if found:
            return max(found)[1]
        time.sleep(0.25)
    return None


def bring_to_front(hwnd):
    """Windows only lets the foreground process hand over the foreground; an Alt tap unlocks it."""
    for _ in range(3):
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.2)
        if user32.GetForegroundWindow() == hwnd:
            return True
        user32.keybd_event(0x12, 0, 0, 0)    # VK_MENU (Alt) down
        user32.keybd_event(0x12, 0, 2, 0)    # up
    return user32.GetForegroundWindow() == hwnd


def press_f11(hwnd):
    """Press F11 in the game window. Injected input (keybd_event/SendInput) does not reliably reach
    another process's window, so the key messages are posted to the window itself; SDL turns them
    into a normal KEYDOWN/KEYUP, exactly like a real key press."""
    bring_to_front(hwnd)
    scan = user32.MapVirtualKeyW(0x7A, 0)
    user32.PostMessageW(hwnd, 0x0100, 0x7A, 1 | (scan << 16))                     # WM_KEYDOWN VK_F11
    time.sleep(0.05)
    user32.PostMessageW(hwnd, 0x0101, 0x7A, 1 | (scan << 16) | (3 << 30))         # WM_KEYUP


def run_packaged_once(command, env, label, start_fullscreen=False, multiplayer=False) -> list:
    results = []
    process = subprocess.Popen(command, env=env)
    try:
        hwnd = find_window(process.pid)
        if hwnd is None:
            print("  BAD no game window appeared")
            return [{"label": f"{label}: window", "ok": False}]
        time.sleep(3)
        results.append(check(hwnd, "start-up", start_fullscreen))
        # The packaged game loads for a few seconds before its first frame: wait for it (max 15 s).
        started = time.monotonic()
        while time.monotonic() - started < 15:
            capture = capture_client(hwnd)
            if measure_picture(capture, not_black)[2] > capture[0] // 2:
                break
            time.sleep(0.5)
        print(f"      first frame after {3 + time.monotonic() - started:.1f} s", flush=True)
        results.append(picture_check(hwnd, "start-up picture", capture_client(hwnd), not_black))
        if multiplayer:
            results.append(extra_check("start-up extras", other_process_dpi_awareness(process.pid),
                                       window_caption(hwnd), None, window_dpi(hwnd)))
        fullscreen = start_fullscreen
        for round_number in range(1, 6):
            for _ in range(2):
                press_f11(hwnd)
                fullscreen = not fullscreen
                time.sleep(1.5)
                results.append(check(hwnd, f"F11 #{round_number} -> {'fullscreen' if fullscreen else 'window'}",
                                     fullscreen))
                results.append(picture_check(hwnd, f"F11 #{round_number} picture", capture_client(hwnd), not_black))
    finally:
        process.kill()
        try:
            process.wait(timeout=15)      # let it release its log file before the folder is removed
        except subprocess.TimeoutExpired:
            pass
        time.sleep(0.5)
    for item in results:
        item["label"] = f"{label}: {item['label']}"
    return results


def run_packaged(exe: Path) -> list:
    print(f"\n== packaged: {exe}", flush=True)
    with tempfile.TemporaryDirectory(prefix="window-check-") as temporary:
        appdata = prepare_appdata(Path(temporary), {})
        env = dict(os.environ, LOCALAPPDATA=str(appdata))
        return run_packaged_once([str(exe)], env, "packaged")


def run_packaged_multiplayer(exe: Path) -> list:
    everything = []
    for label, options, extra in MP_STARTS:
        print(f"\n== packaged --multiplayer, {label}: {exe}", flush=True)
        with tempfile.TemporaryDirectory(prefix="window-check-mp-") as temporary:
            appdata = prepare_mp_appdata(Path(temporary), options)
            everything += run_packaged_once([str(exe), "--multiplayer"], mp_child_env(appdata, extra),
                                            f"packaged multiplayer {label}", mp_start_fullscreen(options, extra),
                                            multiplayer=True)
    return everything


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", choices=["source", "packaged", "_source_child"])
    parser.add_argument("out", nargs="?")
    parser.add_argument("--exe", default=str(ROOT / "dist" / "SolitairePlus" / "SolitairePlus.exe"))
    parser.add_argument("--multiplayer", action="store_true", help="check the multiplayer window instead")
    args = parser.parse_args(argv)
    if user32 is None:
        raise SystemExit("window_check.py needs Windows")
    if args.mode == "packaged":
        # measure in real pixels, like the DPI-aware game does
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass
    if args.mode == "_source_child":
        source_child(args.out, args.multiplayer)
        return 0
    if args.mode == "source":
        results = run_source_multiplayer() if args.multiplayer else run_source()
    else:
        results = run_packaged_multiplayer(Path(args.exe)) if args.multiplayer else run_packaged(Path(args.exe))
    bad = [r for r in results if not r.get("ok")]
    print(f"\n{len(results) - len(bad)}/{len(results)} checks ok")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
