"""Compatibility import; implementation lives in shared/poker_learning.py."""
import sys
from shared import poker_learning as _implementation
sys.modules[__name__] = _implementation
