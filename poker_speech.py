"""Compatibility import; implementation lives in shared/poker_speech.py."""
import sys
from shared import poker_speech as _implementation
sys.modules[__name__] = _implementation
