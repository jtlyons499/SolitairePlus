"""The game's side of updating. All real work happens in SolitaireUpdater.exe.

    checker = UpdateChecker()
    checker.start()            # quiet background check (no window)
    checker.poll()             # call every frame; fills checker.result when done
    checker.update_available   # True when a newer release exists
    launch_update()            # start the updater window; the game should then quit

The game never downloads or replaces files itself, and never touches the
network directly (see docs/NETWORKING.md). Updates only work in the installed
or packaged game; running from source, everything here is switched off.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

UPDATER_EXE = "SolitaireUpdater.exe"
JOURNAL = Path(".update") / "journal.json"
PENDING_DELETE = "pending-delete.txt"   # same names as updater/config.py
OLD_SUFFIX = ".updating-old"


def install_dir() -> Path | None:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return None


def updater_path() -> Path | None:
    folder = install_dir()
    if folder is None:
        return None
    path = folder / UPDATER_EXE
    return path if path.is_file() else None


def available() -> bool:
    return updater_path() is not None


def _env() -> dict:
    # A packaged game starting another packaged program must not pass on its own runtime state.
    return dict(os.environ, PYINSTALLER_RESET_ENVIRONMENT="1")


def _start(arguments, hidden=False):
    path = updater_path()
    if path is None:
        return None
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if hidden else 0
    try:
        return subprocess.Popen([str(path), *arguments], cwd=str(path.parent), env=_env(),
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, creationflags=flags, close_fds=True)
    except OSError:
        return None


def cleanup_leftovers() -> None:
    """Delete files an update had to rename aside because they were in use (see updater/transaction.py)."""
    folder = install_dir()
    listing = folder / PENDING_DELETE if folder else None
    if listing is None or not listing.is_file():
        return
    remaining = []
    try:
        for line in listing.read_text(encoding="utf-8").splitlines():
            relpath = line.strip()
            if not relpath.endswith(OLD_SUFFIX) or ".." in relpath.split("/"):
                continue
            try:
                (folder / relpath).unlink(missing_ok=True)
            except OSError:
                remaining.append(relpath)
        if remaining:
            listing.write_text("\n".join(remaining) + "\n", encoding="utf-8")
        else:
            listing.unlink()
    except OSError:
        pass  # never stop the game from starting over this


def recover_if_needed() -> bool:
    """At game start: if a previous update was interrupted, let the updater undo it.

    Returns True when the game should exit immediately (the updater will restart it).
    """
    folder = install_dir()
    if folder is None or not (folder / JOURNAL).is_file():
        return False
    return _start(["--recover", "--relaunch"]) is not None


def launch_update() -> bool:
    """Open the updater window. It waits for this game process to close, updates, and restarts the game."""
    return _start(["--apply", "--wait-pid", str(os.getpid()), "--relaunch"]) is not None


class UpdateChecker:
    def __init__(self):
        self.process = None
        self.result_file = None
        self.result: dict | None = None

    @property
    def checking(self) -> bool:
        return self.process is not None

    @property
    def update_available(self) -> bool:
        return bool(self.result and self.result.get("status") == "update_available")

    @property
    def latest(self) -> str:
        return str((self.result or {}).get("latest", ""))

    def start(self) -> bool:
        if self.process is not None or not available():
            return False
        handle, name = tempfile.mkstemp(prefix="solitaire-update-", suffix=".json")
        os.close(handle)
        self.result_file = Path(name)
        self.result = None
        self.process = _start(["--check", "--result-file", str(self.result_file)], hidden=True)
        if self.process is None:
            self._cleanup()
            self.result = {"status": "error", "message": "The updater could not be started."}
            return False
        return True

    def poll(self) -> dict | None:
        if self.process is None or self.process.poll() is None:
            return self.result
        try:
            self.result = json.loads(self.result_file.read_text(encoding="utf-8"))
        except (OSError, ValueError, AttributeError):
            self.result = {"status": "error", "message": "Could not check for updates."}
        self.process = None
        self._cleanup()
        return self.result

    def status_text(self) -> str:
        if not available():
            return "Updates are only available in the installed game."
        if self.checking:
            return "Checking for updates…"
        if not self.result:
            return ""
        status = self.result.get("status")
        if status == "update_available":
            return f"Version {self.latest} is available."
        if status == "up_to_date":
            return f"You have the latest version ({self.result.get('installed', '')})."
        return str(self.result.get("message") or "Could not check for updates.")

    def _cleanup(self):
        if self.result_file is not None:
            try:
                self.result_file.unlink()
            except OSError:
                pass
            self.result_file = None
