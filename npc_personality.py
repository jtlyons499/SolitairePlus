"""Compatibility import; implementation lives in shared/npc_personality.py."""
import sys
from shared import npc_personality as _implementation
sys.modules[__name__] = _implementation
