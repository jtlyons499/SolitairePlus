"""Compatibility import for the consolidated Solitaire project."""
import sys
from pathlib import Path
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.append(_project_root)
from solitaireplus.games.poker import speech as _implementation

# Explicit exports allow IDEs to resolve the shared API.
from solitaireplus.games.poker.speech import (
    POKER_CHAT_POPUPS_ENABLED,
    PokerSpeechOverlay,
    is_poker_chat_popups_enabled,
    set_poker_chat_popups_enabled,
)

sys.modules[__name__] = _implementation
