"""Compatibility import; implementation lives in shared/poker_speech.py."""
import sys
from shared import poker_speech as _implementation

# Explicit exports allow IDEs to resolve the shared API.
from shared.poker_speech import (
    POKER_CHAT_POPUPS_ENABLED,
    PokerSpeechOverlay,
    is_poker_chat_popups_enabled,
    set_poker_chat_popups_enabled,
)

sys.modules[__name__] = _implementation
