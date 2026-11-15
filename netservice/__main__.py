"""Entry point: `python -m netservice` (source) or SolitaireNet.exe (packaged)."""
import sys

from netservice.service import main

if __name__ == "__main__":
    sys.exit(main())
