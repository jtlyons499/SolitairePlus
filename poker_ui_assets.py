"""Compatibility import; implementation lives in shared/poker_ui_assets.py."""
import sys
from shared import poker_ui_assets as _implementation
sys.modules[__name__] = _implementation
