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


GAME_RATING_KEYS = RATING_KEYS[1:]
RATING_SCHEMA_VERSION = 2
MIN_RATING = 100


def _rating(value, fallback=1000):
    try:
        return max(MIN_RATING, int(value))
    except (TypeError, ValueError, OverflowError):
        return max(MIN_RATING, int(fallback))


def derive_overall(ratings):
    """Equal-weight average of seven game ratings, rounded to nearest integer."""
    return (sum(_rating(ratings.get(key, 1000)) for key in GAME_RATING_KEYS) + 3) // 7


def make_player_rating_bundle(legacy_rating=1000):
    ratings = dict.fromkeys(GAME_RATING_KEYS, 1000)
    ratings["solitaire"] = _rating(legacy_rating)
    ratings["overall"] = derive_overall(ratings)
    return ratings


def normalize_rating_bundle(bundle, legacy_rating=1000):
    ratings = make_player_rating_bundle(legacy_rating)
    if isinstance(bundle, dict):
        for key in GAME_RATING_KEYS:
            ratings[key] = _rating(bundle.get(key, ratings[key]), ratings[key])
    ratings["overall"] = derive_overall(ratings)
    return ratings


def apply_rating_change(ratings, game_key, amount):
    """Change only the named game; Overall is always recalculated."""
    if game_key not in GAME_RATING_KEYS:
        raise ValueError(f"{game_key!r} is not an independently rated game")
    normalized = normalize_rating_bundle(ratings)
    before = normalized[game_key]
    normalized[game_key] = _rating(before + int(amount))
    normalized["overall"] = derive_overall(normalized)
    ratings.clear()
    ratings.update(normalized)
    return normalized[game_key] - before


def elo_delta(player_rating, opponent_rating, score, k=48):
    score = max(0.0, min(1.0, float(score)))
    gap = max(-3200, min(3200, _rating(opponent_rating) - _rating(player_rating)))
    expected = 1.0 / (1.0 + 10.0 ** (gap / 400.0))
    raw = float(k) * (score - expected)
    # Decisive results always have the correct sign, even against extreme gaps.
    change = int(round(raw))
    if score == 1:
        change = max(1, change)
    elif score == 0:
        change = min(-1, change)
    return change


def update_npc_rating(state, npc, game_key, amount):
    state = ensure_npc_career_state(state, npc)
    before = state["rating"]
    actual = apply_rating_change(state["ratings"], game_key, amount)
    state["rating"] = state["ratings"]["overall"]
    state["last_changes"][game_key] = actual
    state["last_change"] = state["rating"] - before
    state["last_changes"]["overall"] = state["last_change"]
    return actual


def boost_npc_overall(state, target):
    """Seed a superstar by shifting all seven skills, never writing Overall."""
    ratings = normalize_rating_bundle(state["ratings"])
    difference = _rating(target) - ratings["overall"]
    for key in GAME_RATING_KEYS:
        apply_rating_change(ratings, key, difference)
    state["ratings"] = ratings
    state["rating"] = ratings["overall"]


def simulate_npc_rating_month(state, npc, star=False, rng=None):
    """Monthly form affects independently selected games on the NPC circuit."""
    rng = rng or random
    state = ensure_npc_career_state(state, npc, rng)
    before = state["rating"]
    limits = {"elite": (-45, 50), "strong": (-50, 45), "mid": (-55, 55), "low": (-60, 60)}
    low, high = (-25, 55) if star else limits.get(npc.get("skill_tier"), (-55, 55))
    state["last_changes"] = dict.fromkeys(RATING_KEYS, 0)
    for key in rng.sample(list(GAME_RATING_KEYS), rng.randint(2, 4)):
        state["last_changes"][key] = apply_rating_change(state["ratings"], key, rng.randint(low, high))
    state["rating"] = state["ratings"]["overall"]
    state["last_change"] = state["rating"] - before
    state["last_changes"]["overall"] = state["last_change"]
    return state


def migrate_profile_ratings(profile):
    """Preserve game values, career possessions and unrelated/unknown save data."""
    if not isinstance(profile, dict):
        return profile
    career = profile.setdefault("career", {})
    if not isinstance(career, dict):
        return profile
    career["ratings"] = normalize_rating_bundle(career.get("ratings"), career.get("rating", 1000))
    career["rating"] = career["ratings"]["overall"]
    career["rating_schema_version"] = RATING_SCHEMA_VERSION
    career.setdefault("rating_results", {})
    states = career.get("leaderboard_state", {})
    if isinstance(states, dict):
        for state in states.values():
            if isinstance(state, dict):
                state["ratings"] = normalize_npc_rating_bundle(state.get("ratings"), state.get("rating", 1000))
                state["rating"] = state["ratings"]["overall"]
                state["rating_schema_version"] = RATING_SCHEMA_VERSION
    return profile


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
    rng = rng or random
    base_rating = _rating(base_rating)
    spread = _npc_rating_spread_for_tier(skill_tier)
    ratings = {key: _rating(base_rating + rng.randint(-spread, spread)) for key in GAME_RATING_KEYS}
    ratings["solitaire"] = base_rating
    ratings["overall"] = derive_overall(ratings)
    return ratings


def normalize_npc_rating_bundle(bundle, legacy_rating=1000):
    base = _rating(legacy_rating)
    bundle = bundle if isinstance(bundle, dict) else {}
    ratings = {key: _rating(bundle.get(key, base), base) for key in GAME_RATING_KEYS}
    ratings["overall"] = derive_overall(ratings)
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
    except (TypeError, ValueError, OverflowError):
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
        ratings = normalize_npc_rating_bundle(ratings, legacy_rating)

    ratings["overall"] = derive_overall(ratings)
    state["rating"] = ratings["overall"]
    state["ratings"] = ratings
    state["rating_schema_version"] = RATING_SCHEMA_VERSION
    state.setdefault("last_change", 0)
    state.setdefault("last_changes", dict.fromkeys(RATING_KEYS, 0))
    state.setdefault("rating_results", {})

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

