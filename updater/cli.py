"""Command line for SolitaireUpdater.exe (also `python -m updater` from source)."""
from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from . import __version__, config, core, transaction


def default_install_dir() -> Path | None:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return None


def setup_logging() -> None:
    try:
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".local/share")
        folder = base / "SimpleSolitaire" / "logs"
        folder.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(folder / "updater.log", maxBytes=256_000, backupCount=1, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logging.getLogger("updater").addHandler(handler)
        logging.getLogger("updater").setLevel(logging.INFO)
    except OSError:
        pass


def relaunch_game(install_dir: Path) -> None:
    game = install_dir / config.GAME_EXE
    if not game.is_file():
        return
    env = dict(os.environ, PYINSTALLER_RESET_ENVIRONMENT="1")
    subprocess.Popen([str(game)], cwd=str(install_dir), env=env, close_fds=True,
                     creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(prog="SolitaireUpdater", description="Solitaire+ updater")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="only check; write the answer to --result-file")
    mode.add_argument("--apply", action="store_true", help="download and install (default)")
    mode.add_argument("--recover", action="store_true", help="undo an interrupted update")
    mode.add_argument("--selftest", action="store_true", help="prove the packaged updater starts")
    mode.add_argument("--version", action="store_true")
    parser.add_argument("--result-file", type=Path)
    parser.add_argument("--install-dir", type=Path, default=None)
    parser.add_argument("--manifest-url", default=config.DEFAULT_MANIFEST_URL)
    parser.add_argument("--wait-pid", type=int)
    parser.add_argument("--relaunch", action="store_true", help="start the game afterwards")
    parser.add_argument("--repair", action="store_true", help="re-check every file even if up to date")
    args = parser.parse_args(argv)

    if args.version or args.selftest:
        if sys.stdout:  # None in the packaged (windowed) exe; the exit code is what counts
            print(f"SolitaireUpdater {__version__}")
        if args.selftest:
            import tkinter  # noqa: F401  (proves the window toolkit is packaged)
            from . import signing  # noqa: F401
        return 0

    setup_logging()
    install_dir = (args.install_dir or default_install_dir())
    if install_dir is None:
        parser.error("--install-dir is required when running from source")
    install_dir = install_dir.resolve()
    transaction.cleanup_pending(install_dir)  # leftovers renamed aside by an earlier update

    if args.check:
        result = core.check(install_dir, args.manifest_url)
        text = json.dumps(result)
        if args.result_file:
            args.result_file.write_text(text, encoding="utf-8")
        elif sys.stdout:
            print(text)
        return 0 if result["status"] != "error" else 1

    if args.recover:
        undone = core.recover(install_dir)
        logging.getLogger("updater").warning("Recovery run: %s", "rolled back" if undone else "nothing to do")
        if args.relaunch:
            relaunch_game(install_dir)
        return 0

    # --apply (also the default when started from the Start Menu).
    # The updater runs from the install folder itself; files it is using are
    # renamed aside instead of overwritten (see transaction.py).
    from .ui import TkUI
    ui = TkUI()

    def worker(window):
        if args.wait_pid:
            window.status("Waiting for Solitaire+ to close…")
            core.wait_for_exit(args.wait_pid)
        return core.run_update(install_dir, args.manifest_url, window, repair=args.repair)

    code = ui.run(worker)
    if args.relaunch:  # bring the game back even if the update was cancelled or failed
        relaunch_game(install_dir)
    return code
