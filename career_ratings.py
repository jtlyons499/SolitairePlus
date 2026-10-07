import random

from career_fans import ensure_npc_fan_state


CATEGORY_KEYS = ("strategy", "poker", "casino")
RATING_KEYS = ("overall", *CATEGORY_KEYS)
GAME_CATEGORIES = {
    "solitaire": "strategy", "score_four": "strategy",
    "texas_holdem": "poker", "five_card_draw": "poker",
    "seven_card_stud": "poker", "five_o_poker": "poker",
    "blackjack": "casino", "roulette": "casino", "faro": "casino",
}
GAME_RATING_KEYS = tuple(GAME_CATEGORIES)
RATING_DISPLAY_NAMES = {
    "overall": "Global Rating", "strategy": "Strategy Games Rating",
    "poker": "Poker Rating", "casino": "Casino Rating",
    **{game: category.title() + " Rating" for game, category in GAME_CATEGORIES.items()},
}
RATING_SCHEMA_VERSION = 3
MIN_RATING = 100


class RatingPoints(float):
    """Fractional save precision with whole-point UI formatting."""
    def __format__(self, spec):
        return format(int(round(self)), spec.replace("f", "d") if "f" not in spec else spec)

    def __str__(self):
        return str(int(round(self)))


def _rating(value, fallback=1000):
    try:
        import math
        value = float(value)
        return RatingPoints(max(MIN_RATING, value if math.isfinite(value) else float(fallback)))
    except (TypeError, ValueError, OverflowError):
        return RatingPoints(max(MIN_RATING, float(fallback)))


def derive_overall(ratings):
    return _rating(sum(float(ratings.get(key, 1000)) * weight
                       for key, weight in zip(CATEGORY_KEYS, (.55, .35, .10))))


def _finish_bundle(ratings):
    for game, category in GAME_CATEGORIES.items():
        ratings[game] = ratings[category]
    ratings["overall"] = derive_overall(ratings)
    return ratings


def make_player_rating_bundle(legacy_rating=1000):
    return _finish_bundle({"strategy": _rating(legacy_rating), "poker": _rating(1000), "casino": _rating(1000)})


def normalize_rating_bundle(bundle, legacy_rating=1000):
    ratings = make_player_rating_bundle(legacy_rating)
    if isinstance(bundle, dict):
        for category in CATEGORY_KEYS:
            if category in bundle:
                ratings[category] = _rating(bundle[category])
            else:
                previous = [float(_rating(bundle[game])) for game, group in GAME_CATEGORIES.items()
                            if group == category and game in bundle]
                if previous:
                    ratings[category] = _rating(sum(previous) / len(previous))
    return _finish_bundle(ratings)


def reward_scale(rating):
    steps = max(0, int((float(rating) - 1000) // 100))
    return max(.10, 1.0 - .005 * steps)


def apply_rating_change(ratings, game_key, amount, *, scale_rewards=True):
    category = GAME_CATEGORIES.get(game_key, game_key if game_key in CATEGORY_KEYS else None)
    if category is None:
        raise ValueError(f"{game_key!r} is not rated")
    normalized = normalize_rating_bundle(ratings)
    before = normalized[category]
    amount = float(amount)
    if amount > 0 and scale_rewards:
        amount *= reward_scale(before)
    normalized[category] = _rating(float(before) + amount)
    _finish_bundle(normalized)
    ratings.clear()
    ratings.update(normalized)
    # UI notifications stay integral; fractional progress persists in the save.
    return int(round(normalized[category])) - int(round(before))


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
    actual = apply_rating_change(state["ratings"], game_key, amount, scale_rewards=False)
    state["rating"] = state["ratings"]["overall"]
    state["last_changes"][game_key] = actual
    state["last_change"] = state["rating"] - before
    state["last_changes"]["overall"] = state["last_change"]
    return actual


def boost_npc_overall(state, target):
    """Seed a superstar by shifting three categories, never writing Global."""
    ratings = normalize_rating_bundle(state["ratings"])
    difference = _rating(target) - ratings["overall"]
    for key in CATEGORY_KEYS:
        apply_rating_change(ratings, key, difference, scale_rewards=False)
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
    for key in rng.sample(list(CATEGORY_KEYS), rng.randint(1, 3)):
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
    ratings = {key: _rating(base_rating + rng.randint(-spread, spread)) for key in CATEGORY_KEYS}
    ratings["strategy"] = base_rating
    return _finish_bundle(ratings)


def normalize_npc_rating_bundle(bundle, legacy_rating=1000):
    if not isinstance(bundle, dict) or not bundle:
        return _finish_bundle({key: _rating(legacy_rating) for key in CATEGORY_KEYS})
    return normalize_rating_bundle(bundle, legacy_rating)


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


