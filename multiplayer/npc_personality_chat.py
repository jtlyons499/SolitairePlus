"""Compatibility import for the consolidated Solitaire project."""
import sys
from pathlib import Path
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.append(_project_root)
from shared import npc_personality_chat as _implementation

# Explicit exports allow IDEs to resolve the shared API.
from shared.npc_personality_chat import (
    NEUTRAL_CHAT,
    TRAIT_CHAT,
    game_trait_chat,
    trait_chat,
)

sys.modules[__name__] = _implementation
