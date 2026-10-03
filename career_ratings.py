import random

from career_fans import ensure_npc_fan_state


RATING_KEYS = (
    "overall",
    "solitaire",
    "texas_holdem",
    "five_card_draw",
    "seven_card_stud",
    "blackjack",
    "roulette",
    "score_four",
)

RATING_DISPLAY_NAMES = {
    "overall": "Overall",
    "solitaire": "Solitaire",
    "texas_holdem": "Texas Hold'em",
    "five_card_draw": "Five-Card Draw",
    "seven_card_stud": "Seven-Card Stud",
    "blackjack": "Blackjack",
    "roulette": "Roulette",
    "score_four": "Score-Four",
}


def make_player_rating_bundle(legacy_rating=1000):
    """Create a backward-compatible multi-game rating bundle.

    The old career rating represented competitive Solitaire while also
    functioning as the game's overall rating. Existing saves therefore start
    with that same value in Overall and Solitaire, while newly introduced game
    ratings begin at 1000 until those systems start awarding their own points.
    """
    legacy_rating = max(100, int(legacy_rating or 1000))

    ratings = {
        key: 1000
        for key in RATING_KEYS
    }

    ratings["overall"] = legacy_rating
    ratings["solitaire"] = legacy_rating

    return ratings


def normalize_rating_bundle(bundle, legacy_rating=1000):
    ratings = make_player_rating_bundle(legacy_rating)

    if isinstance(bundle, dict):
        for key in RATING_KEYS:
            if key not in bundle:
                continue

            try:
                value = int(bundle[key])
            except (TypeError, ValueError):
                continue

            ratings[key] = max(100, value)

    return ratings


def get_stable_birthday_month(npc):
    """Return a stable 1-12 birthday month for an NPC.

    NPC JSON may eventually provide an explicit ``birthday_month``. Until then,
    existing characters receive a deterministic month based on their ID so old
    saves do not make everybody age together in January and different sessions
    do not reroll birthdays.
    """
    if isinstance(npc, dict):
        explicit = npc.get("birthday_month")
        try:
            explicit = int(explicit)
        except (TypeError, ValueError):
            explicit = None

        if explicit is not None and 1 <= explicit <= 12:
            return explicit

        identity = str(
            npc.get("id")
            or npc.get("name")
            or "npc"
        )
    else:
        identity = str(npc or "npc")

    weighted_sum = sum(
        (index + 1) * ord(character)
        for index, character in enumerate(identity)
    )

    return weighted_sum % 12 + 1


def _npc_rating_spread_for_tier(skill_tier):
    return {
        "low": 145,
        "mid": 175,
        "strong": 205,
        "elite": 235,
    }.get(str(skill_tier or "mid").lower(), 175)


def make_npc_rating_bundle(base_rating, skill_tier="mid", rng=None):
    """Seed per-game ratings around an NPC's existing career rating.

    This is intentionally only scaffolding for now. Overall and Solitaire keep
    the exact legacy rating. Other games receive modest stable-in-save variance
    so the later sortable leaderboards already have believable underlying data.
    """
    if rng is None:
        rng = random

    base_rating = max(100, int(base_rating or 1000))
    spread = _npc_rating_spread_for_tier(skill_tier)

    ratings = {
        "overall": base_rating,
        "solitaire": base_rating,
    }

    for key in RATING_KEYS:
        if key in ratings:
            continue

        ratings[key] = max(
            100,
            base_rating + rng.randint(-spread, spread)
        )

    return ratings


def ensure_npc_career_state(state, npc, rng=None):
    """Migrate/complete one NPC's save-state record in place."""
    if rng is None:
        rng = random

    if not isinstance(state, dict):
        state = {}

    legacy_rating = state.get("rating", 1000)
    try:
        legacy_rating = int(legacy_rating)
    except (TypeError, ValueError):
        legacy_rating = 1000

    legacy_rating = max(100, legacy_rating)

    if "age" not in state:
        try:
            state["age"] = int(npc.get("age", 0))
        except (AttributeError, TypeError, ValueError):
            state["age"] = 0

    if "birthday_month" not in state:
        state["birthday_month"] = get_stable_birthday_month(npc)

    ratings = state.get("ratings")
    if not isinstance(ratings, dict):
        ratings = make_npc_rating_bundle(
            legacy_rating,
            npc.get("skill_tier", "mid") if isinstance(npc, dict) else "mid",
            rng=rng,
        )
    else:
        fallback = make_npc_rating_bundle(
            legacy_rating,
            npc.get("skill_tier", "mid") if isinstance(npc, dict) else "mid",
            rng=rng,
        )
        for key in RATING_KEYS:
            try:
                value = int(ratings.get(key, fallback[key]))
            except (TypeError, ValueError):
                value = fallback[key]
            ratings[key] = max(100, value)

    # The legacy field remains the authoritative visible overall rating until
    # the leaderboard UI is converted to selectable rating categories.
    ratings["overall"] = legacy_rating

    state["rating"] = legacy_rating
    state["ratings"] = ratings
    state.setdefault("last_change", 0)

    ensure_npc_fan_state(state, npc)

    return state


def advance_npc_age_for_month(state, npc, month):
    """Increase age only when the career crosses this NPC's birthday month."""
    state = ensure_npc_career_state(state, npc)

    try:
        month = int(month)
    except (TypeError, ValueError):
        return False

    if month != state.get("birthday_month"):
        return False

    state["age"] = max(0, int(state.get("age", 0))) + 1
    return True
