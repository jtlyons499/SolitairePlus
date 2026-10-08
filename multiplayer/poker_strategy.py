"""Compatibility import for the consolidated Solitaire project."""
import sys
from pathlib import Path
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.append(_project_root)
from shared import poker_strategy as _implementation

# Explicit exports allow IDEs to resolve the shared API.
from shared.poker_strategy import (
    ACTION_TYPES,
    LATE_STREETS,
    PokerTableReads,
    SIGNATURES,
    STRATEGY_CHAT,
    clamp,
    effective_wager_cap,
    estimate_range,
    signature_for,
    strategic_context,
    strategic_fraction,
    strategy_chat_line,
)

sys.modules[__name__] = _implementation
