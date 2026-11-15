"""W1 check on a real screen: does the game window stay fully on-screen with its title bar visible?

    python tools/window_check.py source              # run main.py from source and check
    python tools/window_check.py packaged [--exe dist/SolitairePlus/SolitairePlus.exe]

Windows only. It opens the real game window (and switches it to fullscreen and back), so don't
use the PC while it runs (about a minute). It never changes system settings. For each step it
prints the window's visible rectangle (DWM extended frame bounds) and the monitor's work area:

* source: starts with no saved size, then with a saved 2560x1440 window size (must be clamped),
  then with saved fullscreen; at each start: the start-up window, 5 x F11 (fullscreen and back),
  and every window size the Options screen offers.
* packaged: starts the exe (with a temporary LOCALAPPDATA, so your saves and settings are not
  touched), checks the start-up window, then sends F11 five times and checks after each.

Exit code 0 = every windowed check is inside the work area and every fullscreen check covers
the monitor.
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
    print(f"  {'ok ' if ok else 'BAD'} {label:<34} window {window} size {size}  "
          f"{'monitor' if fullscreen else 'work area'} {monitor if fullscreen else work}", flush=True)
    return {"label": label, "window": window, "monitor": monitor, "work": work, "fullscreen": fullscreen, "ok": ok}


def prepare_appdata(folder: Path, settings: dict) -> Path:
    data = folder / "SimpleSolitaire"
    (data / "saves").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FIXTURE, data / "saves" / "profile_1.json")
    (data / "app_settings.json").write_text(json.dumps({"auto_update_check": False, **settings}), encoding="utf-8")
    return folder


# ------------------------------------------------------------------ source: scripted run of main.py

def source_child(out_path: str) -> None:
    """Runs inside a child process: start main.py and drive it from pygame.display.flip()."""
    import runpy
    sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)
    import pygame

    results = []
    real_flip = pygame.display.flip
    frames = {"n": 0}

    def steps():
        from solitaireplus.app import state, window
        from solitaireplus.app.settings import RESOLUTION_OPTIONS
        yield 90
        hwnd = pygame.display.get_wm_info()["window"]
        results.append(check(hwnd, "start-up", state.fullscreen_enabled))
        for round_number in range(1, 6):
            for _ in range(2):
                pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F11, mod=0, unicode="", scancode=0))
                yield 60
                results.append(check(hwnd, f"F11 #{round_number} -> "
                                     f"{'fullscreen' if state.fullscreen_enabled else 'window'}",
                                     state.fullscreen_enabled))
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

    script = steps()
    wait = {"n": 0}

    def hook():
        real_flip()
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
    sys.argv = [str(ROOT / "main.py")]
    runpy.run_path(str(ROOT / "main.py"), run_name="__main__")


def run_source() -> list:
    starts = [("no saved size", {}), ("saved 2560x1440", {"window_size": [2560, 1440]}),
              ("saved fullscreen", {"fullscreen": True})]
    everything = []
    for label, settings in starts:
        print(f"\n== source, {label}", flush=True)
        with tempfile.TemporaryDirectory(prefix="window-check-") as temporary:
            appdata = prepare_appdata(Path(temporary), settings)
            out = Path(temporary) / "result.json"
            env = dict(os.environ, LOCALAPPDATA=str(appdata), PYGAME_HIDE_SUPPORT_PROMPT="1")
            env.pop("SDL_VIDEODRIVER", None)
            done = subprocess.run([sys.executable, str(Path(__file__).resolve()), "_source_child", str(out)],
                                  cwd=ROOT, env=env, timeout=300)
            if not out.is_file():
                print(f"  BAD the game did not finish the checks (exit code {done.returncode})")
                everything.append({"label": f"{label}: run", "ok": False})
                continue
            for item in json.loads(out.read_text(encoding="utf-8")):
                item["label"] = f"{label}: {item['label']}"
                everything.append(item)
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


def run_packaged(exe: Path) -> list:
    print(f"\n== packaged: {exe}", flush=True)
    results = []
    with tempfile.TemporaryDirectory(prefix="window-check-") as temporary:
        appdata = prepare_appdata(Path(temporary), {})
        env = dict(os.environ, LOCALAPPDATA=str(appdata))
        process = subprocess.Popen([str(exe)], env=env)
        try:
            hwnd = find_window(process.pid)
            if hwnd is None:
                print("  BAD no game window appeared")
                return [{"label": "packaged: window", "ok": False}]
            time.sleep(3)
            results.append(check(hwnd, "start-up", False))
            fullscreen = False
            for round_number in range(1, 6):
                for _ in range(2):
                    press_f11(hwnd)
                    fullscreen = not fullscreen
                    time.sleep(1.5)
                    results.append(check(hwnd, f"F11 #{round_number} -> {'fullscreen' if fullscreen else 'window'}",
                                         fullscreen))
        finally:
            process.kill()
            try:
                process.wait(timeout=15)      # let it release its log file before the folder is removed
            except subprocess.TimeoutExpired:
                pass
            time.sleep(0.5)
    for item in results:
        item["label"] = f"packaged: {item['label']}"
    return results


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", choices=["source", "packaged", "_source_child"])
    parser.add_argument("out", nargs="?")
    parser.add_argument("--exe", default=str(ROOT / "dist" / "SolitairePlus" / "SolitairePlus.exe"))
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
        source_child(args.out)
        return 0
    results = run_source() if args.mode == "source" else run_packaged(Path(args.exe))
    bad = [r for r in results if not r.get("ok")]
    print(f"\n{len(results) - len(bad)}/{len(results)} checks ok")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
