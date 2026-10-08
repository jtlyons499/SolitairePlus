"""Compatibility import; implementation lives in shared/texas_holdem_chat.py."""
import sys
from shared import texas_holdem_chat as _implementation
sys.modules[__name__] = _implementation
