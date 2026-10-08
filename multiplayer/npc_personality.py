"""Compatibility import for the consolidated Solitaire project."""
import sys
from pathlib import Path
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.append(_project_root)
from shared import npc_personality as _implementation

# Explicit exports allow IDEs to resolve the shared API.
from shared.npc_personality import (
    LEGACY_TRAITS,
    PokerGrudgeMemory,
    TRAIT_LABELS,
    TRAIT_NAMES,
    build_trait_profile,
    get_npc_traits,
    npc_identity,
    personality_summary,
    trait_units,
)

sys.modules[__name__] = _implementation
