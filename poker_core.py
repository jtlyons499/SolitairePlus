"""Compatibility import; implementation lives in shared/poker_core.py."""
import sys
from shared import poker_core as _implementation

# Explicit exports allow IDEs to resolve the shared API.
from shared.poker_core import (
    POKER_RANK_NAMES,
    POKER_RANK_PLURALS,
    POKER_RANK_SHORT,
    PokerHandHistory,
    SUIT_SYMBOLS,
    describe_poker_score,
    format_poker_card,
    format_poker_cards,
    format_poker_display_name,
)

sys.modules[__name__] = _implementation
