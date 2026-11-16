"""Shared helpers for unlockable cosmetics awarded outside normal progression."""
from solitaireplus.app import state
from solitaireplus.app.settings import FELTS, MENU_BACKGROUNDS, TITLES
from solitaireplus.career.case_opening import ITEMS as CASE_ITEMS
from solitaireplus.games.arcade.support import ARCADE_PRIZE_CATALOG

COSMETIC_TYPES = ("background", "felt", "title", "cursor")


def normalize_cosmetic_type(value):
    value = str(value or "").strip().lower()
    aliases = {
        "backgrounds": "background",
        "felts": "felt",
        "titles": "title",
        "cursors": "cursor",
    }
    value = aliases.get(value, value)
    return value if value in COSMETIC_TYPES else ""


def unlock_reward(cosmetic_type, asset_id, backgrounds, felts, titles, cursors):
    """Add one cosmetic ID to the appropriate ownership set.

    Returns True only when the reward was newly unlocked. Artwork does not need
    to exist yet; ownership persists so dropping the PNG in later immediately
    makes the reward usable.
    """
    cosmetic_type = normalize_cosmetic_type(cosmetic_type)
    asset_id = str(asset_id or "").strip()
    if not cosmetic_type or not asset_id:
        return False

    target = {
        "background": backgrounds,
        "felt": felts,
        "title": titles,
        "cursor": cursors,
    }[cosmetic_type]
    before = len(target)
    target.add(asset_id)
    return len(target) > before


def reward_owned(cosmetic_type, asset_id, backgrounds, felts, titles, cursors):
    cosmetic_type = normalize_cosmetic_type(cosmetic_type)
    asset_id = str(asset_id or "").strip()
    if not cosmetic_type or not asset_id:
        return False
    target = {
        "background": backgrounds,
        "felt": felts,
        "title": titles,
        "cursor": cursors,
    }[cosmetic_type]
    return asset_id in target


# Cursor cosmetics that are rewards (cases, Prize Counter); filled by register_reward_cosmetics().
REWARD_CURSOR_IDS = set()


def register_reward_cosmetics():
    """Case-opening and Arcade Prize Counter cosmetics are real Customize rewards: add them to the
    Customize catalogs (and the cursors to REWARD_CURSOR_IDS).

    Start-up (app/startup.py) calls this once, before the image catalogs are built. Missing PNGs
    are intentionally allowed: ownership can be earned now and the art can be dropped in later
    without changing code or losing the unlock.
    """
    for reward in [*CASE_ITEMS.values(), *ARCADE_PRIZE_CATALOG]:
        if reward.get("kind") != "cosmetic":
            continue
        ctype = str(reward.get("cosmetic_type", "")).lower()
        asset_id = str(reward.get("asset_id", "")).strip()
        asset_path = str(reward.get("asset_path", "")).strip()
        if not asset_id or not asset_path:
            continue
        state._entry = {
            "name": reward.get("name", asset_id),
            "path": asset_path,
            "order": state._reward_cosmetic_order,
        }
        state._reward_cosmetic_order += 10
        if ctype == "background":
            MENU_BACKGROUNDS.setdefault(asset_id, state._entry)
        elif ctype == "felt":
            FELTS.setdefault(asset_id, state._entry)
        elif ctype == "title":
            TITLES.setdefault(asset_id, state._entry)
        elif ctype == "cursor":
            REWARD_CURSOR_IDS.add(asset_id)
