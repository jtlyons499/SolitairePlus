"""Settings for the whole game (not per save slot), kept between launches.

Stored in %LOCALAPPDATA%\\SimpleSolitaire\\app_settings.json (next to the
saves folder, never inside the install folder, so updates cannot touch it).
Per-profile settings (like New Deals) stay in the profile save instead.

Unknown or invalid values are ignored and the defaults used, so a damaged
file can never stop the game from starting.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

DEFAULTS = {
    "auto_update_check": True,
    "music_mode": None,          # None = keep the game's built-in default
    "music_volume": None,
    "sfx_volume": None,
    "double_click_mode": None,
    "window_size": None,         # [width, height]
    "fullscreen": None,
}
MUSIC_MODES = {"instrumental", "ambient", "off"}
DOUBLE_CLICK_MODES = {"foundation", "foundation_and_tableau"}
SAVE_DELAY = 0.6  # seconds: dragging a volume slider writes once, not every frame


def settings_path() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".local/share")
    return base / "SimpleSolitaire" / "app_settings.json"


def _clean(raw: dict) -> dict:
    values = dict(DEFAULTS)
    if isinstance(raw.get("auto_update_check"), bool):
        values["auto_update_check"] = raw["auto_update_check"]
    if raw.get("music_mode") in MUSIC_MODES:
        values["music_mode"] = raw["music_mode"]
    for key in ("music_volume", "sfx_volume"):
        if isinstance(raw.get(key), (int, float)) and not isinstance(raw.get(key), bool):
            values[key] = max(0.0, min(1.0, float(raw[key])))
    if raw.get("double_click_mode") in DOUBLE_CLICK_MODES:
        values["double_click_mode"] = raw["double_click_mode"]
    size = raw.get("window_size")
    if isinstance(size, list) and len(size) == 2 and all(isinstance(v, int) and 320 <= v <= 10000 for v in size):
        values["window_size"] = size
    if isinstance(raw.get("fullscreen"), bool):
        values["fullscreen"] = raw["fullscreen"]
    return values


class AppSettings:
    def __init__(self, path: Path | None = None):
        self.path = path or settings_path()
        self.values = dict(DEFAULTS)
        self._pending_since = None
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                self.values = _clean(raw)
        except (OSError, ValueError):
            pass

    def get(self, key):
        return self.values.get(key, DEFAULTS.get(key))

    def update(self, changes: dict, now: float | None = None) -> None:
        """Record new values; they are written shortly after they stop changing."""
        merged = _clean({**self.values, **changes})
        if merged != self.values:
            self.values = merged
            self._pending_since = time.monotonic() if now is None else now
        self.tick(now)

    def tick(self, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now
        if self._pending_since is not None and now - self._pending_since >= SAVE_DELAY:
            self.flush()

    def flush(self) -> None:
        if self._pending_since is None:
            return
        self._pending_since = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_name(self.path.name + ".tmp")
            temporary.write_text(json.dumps(self.values, indent=1), encoding="utf-8")
            os.replace(temporary, self.path)
        except OSError:
            pass  # settings are a convenience; never crash the game over them
