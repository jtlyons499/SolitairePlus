"""game_namespace(): the old main.py's global namespace as one mapping (moved out of legacy.py).

Some code still looks names up in one mapping: career/event_progress.py (store and restore a
calendar night), career/session_summary.py (night cash totals), debug/unlocks.py (Max Level /
Unlock All) and games/cards/score_four_ui.py (the Score Four table) take the namespace as an
argument, and other modules read single values from it with .get(). Reads look in the shared state
first, then in the modules game_namespace() lists, then in the few names kept elsewhere; writes go
to solitaireplus.app.state.
"""
import collections as _collections


def _names_kept_elsewhere():
    """The few old main.py names that the callers above still look up through the namespace and
    that live outside the modules game_namespace() chains (they used to be found in legacy.py)."""
    from solitaireplus.app import settings
    from solitaireplus.career import case_opening
    from solitaireplus.games.arcade import support as arcade_support
    from solitaireplus.games.cryptid import collection as cryptid_collection
    from solitaireplus.games.solitaire import table
    from solitaireplus.npc import game_portraits
    from solitaireplus.profile import achievements
    from solitaireplus.profile import cosmetics
    return {
        "ACHIEVEMENT_DEFINITIONS": achievements.ACHIEVEMENT_DEFINITIONS,
        "ARCADE_PRIZE_CATALOG": arcade_support.ARCADE_PRIZE_CATALOG,
        "CASE_ITEMS": case_opening.ITEMS,
        "LEVEL_XP_THRESHOLDS": settings.LEVEL_XP_THRESHOLDS,
        "REWARD_CURSOR_IDS": cosmetics.REWARD_CURSOR_IDS,
        "award_level_packs": cryptid_collection.award_level_packs,
        "draw_npc_portrait": game_portraits.draw_npc_portrait,
        "game": table.game,
    }


def game_namespace():
    """The old main.py's global namespace: shared state first, then the modules below, then
    _names_kept_elsewhere(). Writes go to solitaireplus.app.state."""
    from solitaireplus.app import state
    from solitaireplus.app import state_names
    from solitaireplus.app import sounds
    from solitaireplus.app import window
    from solitaireplus.app import assets
    from solitaireplus.app import fonts
    from solitaireplus.ui import cursors
    from solitaireplus.ui import buttons
    from solitaireplus.ui import text as ui_text
    from solitaireplus.ui import panels
    from solitaireplus.ui import backgrounds
    modules = [state, state_names, sounds, window, assets, fonts, cursors, buttons, ui_text, panels, backgrounds]
    return _collections.ChainMap(*(vars(module) for module in modules), _names_kept_elsewhere())
