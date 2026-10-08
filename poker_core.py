"""Compatibility import; implementation lives in shared/poker_core.py."""
import sys
from shared import poker_core as _implementation
sys.modules[__name__] = _implementation
