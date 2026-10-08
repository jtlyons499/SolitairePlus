"""Compatibility import; implementation lives in shared/poker_ui_assets.py."""
import sys
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
