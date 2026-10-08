"""Compatibility import; implementation lives in shared/npc_personality_chat.py."""
import sys
from shared import npc_personality_chat as _implementation

# Explicit exports allow IDEs to resolve the shared API.
from shared.npc_personality_chat import (
    NEUTRAL_CHAT,
    TRAIT_CHAT,
    game_trait_chat,
    trait_chat,
)

sys.modules[__name__] = _implementation
