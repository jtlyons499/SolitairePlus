"""Compatibility import for the consolidated Solitaire project."""
import sys
from pathlib import Path
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.append(_project_root)
from solitaireplus.games.poker import core as _implementation

# Explicit exports allow IDEs to resolve the shared API.
from solitaireplus.games.poker.core import (
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
