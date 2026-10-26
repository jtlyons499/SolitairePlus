"""Shared helpers for unlockable cosmetics awarded outside normal progression."""

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
