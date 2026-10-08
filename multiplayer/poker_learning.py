"""Compatibility import for the consolidated Solitaire project."""
import sys
from pathlib import Path
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.append(_project_root)
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
