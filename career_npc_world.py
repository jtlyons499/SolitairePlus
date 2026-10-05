"""Career-only roster evolution, saved arrivals and monthly world simulation."""
import copy
import random
import secrets

from career_npc_development import (advance_npc_development, ensure_npc_development,
                                   month_index, rating_tier, stable_seed)
from career_ratings import GAME_RATING_KEYS, ensure_npc_career_state
from npc_avatars import ensure_prospect_avatar

WORLD_VERSION = 1
ARRIVAL_INTERVAL = (3, 5)


def career_roster(base_roster, states):
    """Return immutable base identities plus the prospects actually in this save."""
    roster = list(base_roster)
    used = {npc["id"] for npc in roster}
    for npc_id, state in states.items():
        record = state.get("prospect_record") if isinstance(state, dict) else None
        if isinstance(record, dict) and npc_id not in used:
            npc = copy.deepcopy(record)
            npc["id"] = npc_id
            roster.append(npc)
            used.add(npc_id)
    return roster


def ensure_career_world(world, states, base_roster, year, month, seed=None):
    """Migrate at the current month; never replay pre-batch career history."""
    if not isinstance(world, dict):
        world = {}
    serial = month_index(year, month)
    if world.get("version") != WORLD_VERSION:
        world.update(version=WORLD_VERSION,
                     seed=int(seed if seed is not None else secrets.randbits(63)),
                     started_month=serial, last_simulated_month=serial)
        rng = random.Random(stable_seed(world["seed"], serial, "arrivals"))
        world["next_arrival_month"] = serial + rng.randint(*ARRIVAL_INTERVAL)
    used = [npc_id for npc_id, state in states.items()
            if isinstance(state, dict) and isinstance(state.get("prospect_record"), dict)]
    world.setdefault("used_prospect_ids", [])
    world["used_prospect_ids"] = sorted(set(world["used_prospect_ids"]) | set(used))
    world.setdefault("arrival_count", len(used))
    world.setdefault("next_arrival_month", serial + ARRIVAL_INTERVAL[0])
    for npc in career_roster(base_roster, states):
        npc_id = npc["id"]
        if npc_id not in states:
            # Restoring an incomplete older roster preserves the normal tier ranges.
            rng = random.Random(stable_seed(world["seed"], npc_id, "initial_rating"))
            limits = {"elite": (2150, 2800), "strong": (1650, 2200),
                      "mid": (1150, 1750), "low": (750, 1300)}
            low, high = limits.get(npc.get("skill_tier"), limits["mid"])
            states[npc_id] = {"rating": rng.randint(low, high)}
        state = ensure_npc_career_state(states[npc_id], npc,
                                       random.Random(stable_seed(world["seed"], npc_id, "ratings")))
        states[npc_id] = state
        if isinstance(state.get("prospect_record"), dict):
            ensure_prospect_avatar(state["prospect_record"])
        ensure_npc_development(state, npc, year, month, world["seed"],
                               prospect=bool(state.get("prospect_record")))
    return world


def add_prospect(world, states, pool, year, month, force_prodigy=False):
    """Activate one named prospect, with persistent identity, traits and potential."""
    used = set(world["used_prospect_ids"]) | set(states)
    available = [npc for npc in pool if npc["id"] not in used]
    if not available:
        return None
    serial = month_index(year, month)
    rng = random.Random(stable_seed(world["seed"], world["arrival_count"], serial, "prospect"))
    record = copy.deepcopy(rng.choice(available))
    ensure_prospect_avatar(record)
    age = rng.randint(5, 10)
    record["age"] = age
    record["birthday_month"] = rng.randint(1, 12)
    entry_rating = rng.randint(350, 650)
    ratings = {key: max(100, entry_rating + rng.randint(-60, 60)) for key in GAME_RATING_KEYS}
    state = ensure_npc_career_state({"age": age, "rating": entry_rating,
                                     "ratings": ratings, "prospect_record": record,
                                     "joined_month": serial}, record, rng)
    ensure_npc_development(state, record, year, month, world["seed"],
                           prospect=True, force_prodigy=force_prodigy)
    state["prospect_record"]["skill_tier"] = rating_tier(state["rating"])
    states[record["id"]] = state
    world["used_prospect_ids"] = sorted(set(world["used_prospect_ids"]) | {record["id"]})
    world["arrival_count"] += 1
    kind = "PRODIGY" if state["development"]["prodigy"] else "PROSPECT"
    return {
        "npc_id": record["id"],
        "headline": f"NEW {kind}: {record['name'].upper()} JOINS THE CIRCUIT",
        "body": (f"{record['name']}, {age}, from {record['hometown']}, has entered the rankings "
                 f"at {state['rating']:,} Overall. "
                 + ("Scouts see exceptional promise, though a long development road lies ahead."
                    if kind == "PRODIGY" else "The junior will develop alongside the established competitors.")),
        "category": "career",
        "year": int(year), "month": int(month),
    }


def _milestone_stories(states, roster, year, month):
    names = {npc["id"]: npc["name"] for npc in roster}
    # Include all circuit NPCs. Player rank is handled by the existing leaderboard.
    top_ids = {npc_id for npc_id, state in sorted(states.items(),
                key=lambda item: item[1].get("rating", 1000), reverse=True)[:5]}
    stories = []
    for npc_id, state in states.items():
        development = state.get("development", {})
        if not state.get("prospect_record") or not development:
            continue
        flags = development["news_flags"]
        name = names.get(npc_id, state["prospect_record"]["name"])
        story = None
        if development["prodigy"] and state["rating"] >= 2400 and "elite" not in flags:
            flags.append("elite")
            story = (f"{name.upper()} REACHES ELITE TERRITORY",
                     f"The young prodigy has reached {state['rating']:,} Overall at age {state['age']}. "
                     "The established contenders have another name to watch.")
        elif development["prodigy"] and npc_id in top_ids and "top_five" not in flags:
            flags.append("top_five")
            story = (f"{name.upper()} BREAKS INTO THE CIRCUIT TOP FIVE",
                     f"{name} has climbed into the leading five NPCs at {state['rating']:,} Overall. "
                     "Years of development have brought the prospect into title contention.")
        elif state["rating"] >= 1100 and "1100" not in flags:
            flags.append("1100")
            story = (f"{name.upper()} PASSES FIRST CAREER BENCHMARK",
                     f"{name}, now {state['age']}, has reached {state['rating']:,} Overall "
                     "after progressing through the junior circuit.")
        if story:
            stories.append({"npc_id": npc_id, "headline": story[0], "body": story[1],
                            "category": "career", "year": year, "month": month})
    return stories


def advance_career_world(world, states, base_roster, pool, year, month):
    """Advance consecutive months once; profile reloads and redraws do nothing."""
    world = ensure_career_world(world, states, base_roster, year, month)
    target = month_index(year, month)
    stories = []
    for serial in range(world["last_simulated_month"] + 1, target + 1):
        current_year, zero_month = divmod(serial, 12)
        current_month = zero_month + 1
        roster = career_roster(base_roster, states)
        for npc in roster:
            advance_npc_development(states[npc["id"]], npc, current_year, current_month, world["seed"])
        if serial >= world["next_arrival_month"]:
            story = add_prospect(world, states, pool, current_year, current_month)
            if story:
                stories.append(story)
            rng = random.Random(stable_seed(world["seed"], serial, "arrivals"))
            world["next_arrival_month"] = serial + rng.randint(*ARRIVAL_INTERVAL)
        stories.extend(_milestone_stories(states, career_roster(base_roster, states), current_year, current_month))
        world["last_simulated_month"] = serial
    return world, stories
