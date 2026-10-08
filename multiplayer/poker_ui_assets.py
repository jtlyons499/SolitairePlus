"""Compatibility import for the consolidated Solitaire project."""
import sys
from pathlib import Path
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.append(_project_root)
from shared import poker_ui_assets as _implementation

# Explicit exports allow IDEs to resolve the shared API.
from shared.poker_ui_assets import (
    POKER_LOGO_DRAW_SIZE,
    POKER_LOGO_PATHS,
    POKER_LOGO_SOURCE_SIZE,
    draw_poker_logo,
    get_poker_logo,
)

sys.modules[__name__] = _implementation
