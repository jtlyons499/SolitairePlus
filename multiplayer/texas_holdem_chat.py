"""Compatibility import for the consolidated Solitaire project."""
import sys
from pathlib import Path
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.append(_project_root)
from shared import texas_holdem_chat as _implementation

# Explicit exports allow IDEs to resolve the shared API.
from shared.texas_holdem_chat import (
    ACTION_CHAT_CHANCE,
    PLAYER_REACTION_CHANCE,
    generate_npc_action_chat,
    generate_player_action_reaction,
    generate_showdown_chat,
    get_action_type,
    get_npc_name,
    get_showdown_phrase,
)

sys.modules[__name__] = _implementation
