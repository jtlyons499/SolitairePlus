"""Persistent, game-specific ability curves for Career NPCs.

Ceilings describe long-term form, not a hard cap on ratings earned in matches.
All variation is seeded per NPC/month so loading a profile cannot reroll it.
"""
import hashlib
import random

from career_ratings import CATEGORY_KEYS as GAME_RATING_KEYS, GAME_CATEGORIES, RATING_KEYS, apply_rating_change, ensure_npc_career_state
from career_fans import ensure_npc_fan_state

DEVELOPMENT_VERSION = 1
PRODIGY_CHANCE = 0.01


def stable_seed(*parts):
    digest = hashlib.sha256("|".join(map(str, parts)).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def month_index(year, month):
    month = int(month)
    if not 1 <= month <= 12:
        raise ValueError("Career month must be between 1 and 12")
    return int(year) * 12 + month - 1


def effective_age(state, month):
    return max(0, int(state.get("age", 0))) + ((int(month) - int(state["birthday_month"])) % 12) / 12.0


def rating_tier(rating):
    value = int(rating)
    return "elite" if value >= 2150 else "strong" if value >= 1650 else "mid" if value >= 1150 else "low"


def choose_prospect_band(rng, force_prodigy=False):
    roll = rng.random()
    if force_prodigy or roll < PRODIGY_CHANCE:
        return "prodigy", rng.randint(2450, 2650), 18
    if roll < 0.10:
        return "strong", rng.randint(2000, 2400), rng.randint(18, 22)
    if roll < 0.33:
        return "competitive", rng.randint(1400, 1950), rng.randint(16, 20)
    return "club", rng.randint(980, 1250), rng.choice((15, 15, 15, 16, 17))


def ensure_npc_development(state, npc, year, month, world_seed=0, prospect=False, force_prodigy=False):
    """Initialize once at today's ratings; migration never ages or rerates NPCs."""
    state = ensure_npc_career_state(state, npc)
    existing = state.get("development")
    if isinstance(existing, dict) and existing.get("version") == DEVELOPMENT_VERSION:
        for field in ("anchor_ratings", "peak_ratings", "last_targets", "carry"):
            values = existing[field]
            for category in GAME_RATING_KEYS:
                if category not in values:
                    old = [float(value) for key, value in values.items() if GAME_CATEGORIES.get(key) == category]
                    values[category] = sum(old)/len(old) if old else (0 if field == "carry" else state["ratings"][category])
        return existing
    seed = stable_seed(world_seed, npc.get("id"), "development")
    rng = random.Random(seed)
    age = effective_age(state, month)
    ratings = state["ratings"]
    decline_start = rng.randint(38, 45)
    if prospect:
        band, ceiling, peak_age = choose_prospect_band(rng, force_prodigy)
        specialty = rng.choice(GAME_RATING_KEYS)
        peaks = {key: max(ratings[key] + 40, ceiling + rng.randint(-95, 65)) for key in GAME_RATING_KEYS}
        peaks[specialty] += rng.randint(80, 180)
        adult_bonus = rng.randint(200, 400) if band == "prodigy" else 0
    else:
        band = "established"
        peak_age = rng.randint(35, min(42, decline_start)) if age >= 18 else rng.randint(18, 25)
        # Older NPCs begin at their saved strength; no retrospective age shock.
        peaks = {key: ratings[key] + (rng.randint(60, 230) if age < peak_age else 0)
                 for key in GAME_RATING_KEYS}
        adult_bonus = 0
    development = {
        "version": DEVELOPMENT_VERSION,
        "seed": seed,
        "band": band,
        "prodigy": band == "prodigy",
        "anchor_age": age,
        "anchor_ratings": {key: ratings[key] for key in GAME_RATING_KEYS},
        "peak_age": peak_age,
        "peak_ratings": peaks,
        "decline_start": decline_start,
        "decline_per_year": round(rng.uniform(3.0, 7.0), 3),
        "decline_fraction_cap": round(rng.uniform(0.12, 0.20), 3),
        "adult_bonus": adult_bonus,
        "timeless": bool(npc.get("timeless", int(state["age"]) > 120)),
        "last_targets": {key: float(ratings[key]) for key in GAME_RATING_KEYS},
        "carry": dict.fromkeys(GAME_RATING_KEYS, 0.0),
        "last_simulated_month": month_index(year, month),
        "last_birthday_year": int(year) if int(month) >= int(state["birthday_month"]) else int(year) - 1,
        "news_flags": [],
    }
    state["development"] = development
    return development


def ability_target(development, game_key, age):
    anchor = float(development["anchor_age"])
    initial = float(development["anchor_ratings"][game_key])
    if development.get("timeless"):
        return initial
    peak_age = float(development["peak_age"])
    peak = float(development["peak_ratings"][game_key])
    if age < peak_age and anchor < peak_age:
        progress = max(0.0, min(1.0, (age - anchor) / (peak_age - anchor)))
        return initial + (peak - initial) * progress
    target = peak
    if development.get("prodigy"):
        # Exceptional juniors continue developing into elite adult careers.
        span = max(1.0, development["decline_start"] - peak_age)
        progress = max(0.0, min(1.0, (age - peak_age) / span))
        target += development["adult_bonus"] * progress
    decline_years = max(0.0, age - max(anchor, development["decline_start"]))
    loss = min(development["decline_per_year"] * decline_years,
               target * development["decline_fraction_cap"])
    return max(100.0, target - loss)


def development_stage(state, month):
    development = state.get("development", {})
    if not development:
        return "Established"
    age = effective_age(state, month)
    if development.get("timeless"):
        return "Timeless"
    if age < development["peak_age"]:
        return "Prodigy · developing" if development.get("prodigy") else "Developing"
    if age < development["decline_start"]:
        return "Prodigy · rising" if development.get("prodigy") else "Plateau"
    return "Veteran · gradual decline"


def advance_npc_development(state, npc, year, month, world_seed=0):
    """One idempotent monthly transaction: birthday, curve drift and form."""
    development = ensure_npc_development(state, npc, year, month, world_seed)
    serial = month_index(year, month)
    if serial <= development["last_simulated_month"]:
        return False
    if int(month) == int(state["birthday_month"]) and int(year) > development["last_birthday_year"]:
        state["age"] = max(0, int(state["age"])) + 1
        development["last_birthday_year"] = int(year)
    rng = random.Random(stable_seed(development["seed"], serial, "form"))
    active_games = set(rng.sample(list(GAME_RATING_KEYS), rng.randint(1, 3)))
    before = state["ratings"]["overall"]
    changes = dict.fromkeys(RATING_KEYS, 0)
    age = effective_age(state, month)
    for key in GAME_RATING_KEYS:
        previous_target = development["last_targets"][key]
        target = ability_target(development, key, age)
        # Form is bounded and returns toward the underlying ability curve.
        # Competitive results remain meaningful but cannot create a random walk.
        reversion = max(-18.0, min(18.0, (previous_target - state["ratings"][key]) * 0.12))
        form = rng.randint(-12, 12) if key in active_games else 0
        raw = target - previous_target + reversion + form + development["carry"][key]
        delta = int(round(raw))
        development["carry"][key] = round(raw - delta, 6)
        changes[key] = apply_rating_change(state["ratings"], key, delta, scale_rewards=False)
        development["last_targets"][key] = round(target, 6)
    state["rating"] = state["ratings"]["overall"]
    changes["overall"] = state["rating"] - before
    state["last_changes"] = changes
    state["last_change"] = changes["overall"]
    development["last_simulated_month"] = serial
    ensure_npc_fan_state(state, npc)
    return True

