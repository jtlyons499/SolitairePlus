"""Career-world reactions to exceptional player ratings.

Pure helpers: no pygame, no save I/O.  The caller persists ``seen_flags``.
"""
from __future__ import annotations

CATEGORY_LABELS = {
    "strategy": "Strategy",
    "poker": "Poker",
    "casino": "Casino",
    "overall": "Global",
}

RATING_MILESTONES = (2000, 2250, 2500, 2750, 3000, 3250)


def rating_status(rating):
    try:
        rating = int(rating)
    except (TypeError, ValueError):
        rating = 1000
    if rating >= 3250:
        return "Rating Anomaly"
    if rating >= 3000:
        return "GOAT Territory"
    if rating >= 2750:
        return "Era-Defining"
    if rating >= 2500:
        return "Legendary"
    if rating >= 2250:
        return "World-Class"
    if rating >= 2000:
        return "Elite"
    if rating >= 1750:
        return "Contender"
    return "Established"


def strongest_rating_status(ratings):
    ratings = ratings if isinstance(ratings, dict) else {}
    pairs = [(key, int(ratings.get(key, 0) or 0)) for key in CATEGORY_LABELS]
    key, value = max(pairs, key=lambda item: item[1], default=("overall", 1000))
    return rating_status(value), CATEGORY_LABELS.get(key, key.title()), value


def _story(player_name, key, threshold, value):
    name = str(player_name or "Player")
    label = CATEGORY_LABELS[key]
    if threshold >= 3250:
        return (
            f"RATING SYSTEM SELF IMPLODING {name.upper()}",
            f"{name}'s {label} rating has reached {value:,}. Analysts are starting to fear that their statistical models will never account for this creature.",
            "ratings",
        )
    if threshold >= 3000:
        return (
            f"{name.upper()} BREAKS 3K!",
            f"A {label} rating of {value:,} has pushed {name} into the history books and rattled neuroscientists globally.",
            "ratings",
        )
    if threshold >= 2750:
        return (
            f"{name.upper()} PUSHES {label.upper()} RATING TO {value:,}",
            f"The world is fixated on {name}. At {value:,} in {label}, the current run could become something of science-fiction, like A Space Odyssey or however you spell that word.",
            "ratings",
        )
    if threshold >= 2500:
        return (
            f"{name.upper()} BREAKS 2500 IN {label.upper()}",
            f"{name} has reached {value:,} in {label}, the heights of GMs in chess. Us journalists will watch closely.",
            "ratings",
        )
    if threshold >= 2250:
        return (
            f"{name.upper()} REACHES WORLD-CLASS {label.upper()} FORM",
            f"A {label} rating of {value:,} has separated {name} from the casual players on Twitch.tv. They are now legit.",
            "ratings",
        )
    return (
        f"{name.upper()} JOINS {label.upper()} ELITE",
        f"{name} crossed 2,000 in {label}, a strong sign they are capable of one day challenging the GOATs.",
        "ratings",
    )


def rating_milestone_stories(player_name, ratings, seen_flags=None):
    """Return new milestone stories and an updated flag set.

    A large debug/rating jump emits at most one story per rating category while
    marking lower crossed thresholds as seen, preventing a five-headline dump.
    """
    ratings = ratings if isinstance(ratings, dict) else {}
    seen = set(str(flag) for flag in (seen_flags or ()))
    stories = []
    for key in ("strategy", "poker", "casino", "overall"):
        try:
            value = int(ratings.get(key, 0) or 0)
        except (TypeError, ValueError):
            value = 0
        crossed = [threshold for threshold in RATING_MILESTONES if value >= threshold]
        if not crossed:
            continue
        unseen = [threshold for threshold in crossed if f"{key}:{threshold}" not in seen]
        if not unseen:
            continue
        highest = max(unseen)
        for threshold in crossed:
            seen.add(f"{key}:{threshold}")
        stories.append(_story(player_name, key, highest, value))
    # Global gets first priority, then only the strongest category story. This
    # keeps one rating update from flooding the Career news column.
    if len(stories) > 2:
        global_story = next((story for story in stories if "GLOBAL" in story[0] or "3000 CLUB" in story[0]), None)
        stories = ([global_story] if global_story else []) + [story for story in stories if story is not global_story][:1]
    return stories[:2], seen
