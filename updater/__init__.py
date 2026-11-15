"""Solitaire+ updater (built as SolitaireUpdater.exe).

Checks GitHub Releases for a newer version, downloads only the files that
changed, verifies them, and replaces them all-or-nothing (with automatic
rollback). Saves are never touched; they live in %LOCALAPPDATA%.

    SolitaireUpdater.exe --check --result-file out.json   # quiet check, used by the game
    SolitaireUpdater.exe --apply [--wait-pid N] [--relaunch]
    SolitaireUpdater.exe                                  # same as --apply (Start Menu shortcut)
    SolitaireUpdater.exe --recover                        # undo an interrupted update

See docs/RELEASING.md and AGENTS.md for how releases feed this.
"""

# Version of the updater component only (not the game version). Bump it when
# you change anything in updater/, so SolitaireUpdater.exe is rebuilt.
__version__ = "1.0.0"
