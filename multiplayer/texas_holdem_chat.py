"""Compatibility import for the consolidated Solitaire project."""
import sys
from pathlib import Path
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.append(_project_root)
from shared import texas_holdem_chat as _implementation
sys.modules[__name__] = _implementation
