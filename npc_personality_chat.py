"""Compatibility import; implementation lives in shared/npc_personality_chat.py."""
import sys
from shared import npc_personality_chat as _implementation
sys.modules[__name__] = _implementation
