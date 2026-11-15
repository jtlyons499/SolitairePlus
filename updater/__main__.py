"""Entry point: `python -m updater` (source) or SolitaireUpdater.exe (packaged)."""
import sys

from updater.cli import main

if __name__ == "__main__":
    sys.exit(main())
