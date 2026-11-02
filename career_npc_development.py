"""Persistent, game-specific ability curves for Career NPCs.

Ceilings describe long-term form, not a hard cap on ratings earned in matches.
All variation is seeded per NPC/month so loading a profile cannot reroll it.
"""
import hashlib
import random

from career_ratings import CATEGORY_KEYS as GAME_RATING_KEYS, GAME_CATEGORIES, RATING_KEYS, apply_rating_change, ensure_npc_career_state
from career_fans import ensure_npc_fan_state

DEVELOPMENT_VERSION = 1
# A true 3000-capable prospect should feel like an event, not a routine spawn.
PRODIGY_CHANCE = 0.004


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
        # The upper end plus adult development can create a genuine 3000+
        # outlier. Most forced/debug prodigies still land below that ceiling.
        return "prodigy", rng.randint(2650, 3050), rng.randint(18, 21)
    if roll < 0.085:
        return "strong", rng.randint(2050, 2450), rng.randint(18, 23)
    if roll < 0.31:
        return "competitive", rng.randint(1450, 2000), rng.randint(16, 21)
    return "club", rng.randint(980, 1280), rng.choice((15, 15, 15, 16, 17))


def ensure_npc_development(state, npc, year, month, world_seed=0, prospect=False, force_prodigy=False):
    """Initialize once at today's ratings; migration never retroactively rerates NPCs."""
    state = ensure_npc_career_state(state, npc)
    existing = state.get("development")
    if isinstance(existing, dict) and existing.get("version") == DEVELOPMENT_VERSION:
        for field in ("anchor_ratings", "peak_ratings", "last_targets", "carry"):
            values = existing.setdefault(field, {})
            for category in GAME_RATING_KEYS:
                if category not in values:
                    old = [float(value) for key, value in values.items() if GAME_CATEGORIES.get(key) == category]
                    values[category] = sum(old)/len(old) if old else (0 if field == "carry" else state["ratings"][category])
        # Upgrade older version-1 curves in place without rerolling the NPC.
        # The presence of age_acceleration is our marker that the stronger
        # veteran model has already been applied to this saved career.
        if "age_acceleration" not in existing:
            upgrade_rng = random.Random(stable_seed(existing.get("seed", 0), "aging_v2"))
            if existing.get("prodigy"):
                existing["decline_per_year"] = round(max(float(existing.get("decline_per_year", 0)), upgrade_rng.uniform(7.0, 15.0)), 3)
                existing["decline_fraction_cap"] = round(max(float(existing.get("decline_fraction_cap", 0)), upgrade_rng.uniform(0.24, 0.40)), 3)
                existing["age_acceleration"] = round(upgrade_rng.uniform(0.018, 0.032), 4)
            else:
                existing["decline_per_year"] = round(max(float(existing.get("decline_per_year", 0)), upgrade_rng.uniform(11.0, 24.0)), 3)
                existing["decline_fraction_cap"] = round(max(float(existing.get("decline_fraction_cap", 0)), upgrade_rng.uniform(0.30, 0.52)), 3)
                existing["age_acceleration"] = round(upgrade_rng.uniform(0.026, 0.048), 4)
        existing.setdefault("adult_bonus", 0)
        existing.setdefault("news_flags", [])
        return existing

    seed = stable_seed(world_seed, npc.get("id"), "development")
    rng = random.Random(seed)
    age = effective_age(state, month)
    ratings = state["ratings"]
    decline_start = rng.randint(35, 43)

    if prospect:
        band, ceiling, peak_age = choose_prospect_band(rng, force_prodigy)
        specialty = rng.choice(GAME_RATING_KEYS)
        spread = 115 if band == "prodigy" else 95
        peaks = {key: max(ratings[key] + 40, ceiling + rng.randint(-spread, 80)) for key in GAME_RATING_KEYS}
        peaks[specialty] += rng.randint(120, 260) if band == "prodigy" else rng.randint(70, 170)
        adult_bonus = rng.randint(180, 420) if band == "prodigy" else 0
    else:
        band = "established"
        peak_age = rng.randint(34, min(42, decline_start)) if age >= 18 else rng.randint(18, 25)
        peaks = {
            key: ratings[key] + (rng.randint(70, 250) if age < peak_age else 0)
            for key in GAME_RATING_KEYS
        }
        adult_bonus = 0

    if band == "prodigy":
        decline_rate = rng.uniform(7.0, 15.0)
        decline_cap = rng.uniform(0.24, 0.40)
        age_acceleration = rng.uniform(0.018, 0.032)
    else:
        # Veteran decline is now meaningful. A great 40-year-old can remain
        # elite for years, but holding the same peak into the 70s is rare.
        decline_rate = rng.uniform(11.0, 24.0)
        decline_cap = rng.uniform(0.30, 0.52)
        age_acceleration = rng.uniform(0.026, 0.048)

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
        "decline_per_year": round(decline_rate, 3),
        "decline_fraction_cap": round(decline_cap, 3),
        "age_acceleration": round(age_acceleration, 4),
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
        span = max(1.0, development["decline_start"] - peak_age)
        progress = max(0.0, min(1.0, (age - peak_age) / span))
        target += development.get("adult_bonus", 0) * progress

    decline_origin = max(anchor, float(development["decline_start"]))
    decline_years = max(0.0, age - decline_origin)
    accel = 1.0 + max(0.0, age - 50.0) * float(development.get("age_acceleration", 0.035))
    raw_loss = float(development["decline_per_year"]) * decline_years * accel
    loss = min(raw_loss, target * float(development["decline_fraction_cap"]))
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
    if age >= 62:
        return "Veteran · late-career decline"
    if age >= 50:
        return "Veteran · declining"
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
        reversion = max(-20.0, min(20.0, (previous_target - state["ratings"][key]) * 0.13))
        # Form volatility fades a little in old age so a 70-year-old cannot
        # repeatedly roll +12 months and cancel the underlying decline curve.
        form_span = 12 if age < 50 else 9 if age < 62 else 6
        form = rng.randint(-form_span, form_span) if key in active_games else 0
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
