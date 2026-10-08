"""Compatibility import; implementation lives in shared/poker_strategy.py."""
import sys
from shared import poker_strategy as _implementation
sys.modules[__name__] = _implementation
