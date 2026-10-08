"""Compatibility import; implementation lives in shared/poker_learning.py."""
import sys
from shared import poker_learning as _implementation

# Explicit exports allow IDEs to resolve the shared API.
from shared.poker_learning import (
    ACTIONS,
    GAMES,
    RivalLearning,
    new_learning,
    normalize_learning,
)

sys.modules[__name__] = _implementation
