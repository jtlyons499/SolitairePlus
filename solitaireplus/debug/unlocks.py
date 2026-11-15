"""Debug-only helper for keeping Max Level / Unlock All current.

This intentionally accepts main.py's globals mapping so new catalog entries are
picked up dynamically instead of copying a second hard-coded unlock list here.
"""
from __future__ import annotations


def _update_set(namespace, set_name, values):
    target = namespace.get(set_name)
    if isinstance(target, set):
        before = len(target)
        target.update(values)
        return len(target) - before
    return 0


def debug_unlock_everything(namespace):
    """Unlock every currently registered progression/reward collectible.

    Returns a small summary for debug feedback. Missing future systems are simply
    ignored, making this safe for older profiles and partial developer builds.
    """
    summary = {
        "backgrounds": 0,
        "felts": 0,
        "titles": 0,
        "cursors": 0,
        "achievements": 0,
        "case_rewards": 0,
        "arcade_prizes": 0,
        "cryptid_packs": 0,
    }

    catalogs = (
        ("unlocked_menu_backgrounds", "MENU_BACKGROUNDS", "backgrounds"),
        ("unlocked_felts", "FELTS", "felts"),
        ("unlocked_titles", "TITLES", "titles"),
    )
    for set_name, catalog_name, summary_key in catalogs:
        catalog = namespace.get(catalog_name, {})
        if isinstance(catalog, dict):
            summary[summary_key] = _update_set(namespace, set_name, catalog.keys())

    cursor_ids = set()
    cursor_catalog = namespace.get("cursor_cosmetics", {})
    if isinstance(cursor_catalog, dict):
        cursor_ids.update(cursor_catalog)
    reward_cursor_ids = namespace.get("REWARD_CURSOR_IDS", set())
    if isinstance(reward_cursor_ids, (set, list, tuple)):
        cursor_ids.update(reward_cursor_ids)
    summary["cursors"] = _update_set(namespace, "unlocked_cursors", cursor_ids)

    achievements = namespace.get("achievement_state")
    definitions = namespace.get("ACHIEVEMENT_DEFINITIONS", {})
    if isinstance(achievements, dict) and isinstance(definitions, dict):
        unlocked = achievements.setdefault("unlocked", [])
        if isinstance(unlocked, list):
            before = set(unlocked)
            for achievement_id in definitions:
                if achievement_id not in before:
                    unlocked.append(achievement_id)
            summary["achievements"] = len(set(unlocked) - before)

    # Case trophies/cosmetics are possession-backed. Granting one copy makes
    # them show as owned and keeps reward reconciliation/save behavior correct.
    case_state = namespace.get("case_collection_state")
    case_items = namespace.get("CASE_ITEMS", {})
    if isinstance(case_state, dict) and isinstance(case_items, dict):
        inventory = case_state.setdefault("inventory", {})
        if isinstance(inventory, dict):
            for item_id, item in case_items.items():
                if not isinstance(item, dict) or item.get("kind") not in ("trophy", "cosmetic"):
                    continue
                if int(inventory.get(item_id, 0) or 0) < 1:
                    inventory[item_id] = 1
                    summary["case_rewards"] += 1

    # Prize Counter ownership is represented by prize IDs in arcade.trophies,
    # including cosmetics as well as literal trophies.
    arcade_state = namespace.get("arcade_state")
    prize_catalog = namespace.get("ARCADE_PRIZE_CATALOG", ())
    if isinstance(arcade_state, dict) and isinstance(prize_catalog, (list, tuple)):
        owned = arcade_state.setdefault("trophies", [])
        if isinstance(owned, list):
            seen = set(owned)
            for prize in prize_catalog:
                prize_id = str(prize.get("id", "")) if isinstance(prize, dict) else ""
                if prize_id and prize_id not in seen:
                    owned.append(prize_id)
                    seen.add(prize_id)
                    summary["arcade_prizes"] += 1

    # Max-level debug should mirror normal leveling's Cryptid pack awards.
    award_packs = namespace.get("award_level_packs")
    cryptids = namespace.get("cryptid_collection_state")
    thresholds = namespace.get("LEVEL_XP_THRESHOLDS", {})
    if callable(award_packs) and isinstance(cryptids, dict) and isinstance(thresholds, dict) and thresholds:
        try:
            summary["cryptid_packs"] = int(award_packs(cryptids, max(thresholds)))
        except (KeyError, TypeError, ValueError):
            pass

    return summary
