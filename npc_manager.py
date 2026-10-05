import copy
import json
import random
from npc_personality import get_npc_traits
from pathlib import Path

from career_npc_development import development_stage, rating_tier
from career_npc_world import career_roster


NPC_FILE = (
    Path(__file__).parent
    / "data"
    / "npcs.json"
)


def load_npcs(path=NPC_FILE):

    with open(
            path,
            "r",
            encoding="utf-8"
    ) as file:

        roster = json.load(file)
        for npc in roster:
            npc["personality_traits"] = get_npc_traits(npc)
        return roster


# Immutable metadata belongs to data files; the active list is rebuilt per save.
# Keep NPCS itself alive so all imported references and debug views stay current.
BASE_NPCS = tuple(copy.deepcopy(load_npcs()))
PROSPECT_POOL = tuple(copy.deepcopy(load_npcs(NPC_FILE.with_name("npc_prospects.json"))))
NPCS = copy.deepcopy(list(BASE_NPCS))


def sync_npc_runtime_state(career_state, month=1):
    """Restore this save's exact roster, resetting ages when switching profiles."""
    career_state = career_state if isinstance(career_state, dict) else {}
    live = {npc["id"]: npc for npc in NPCS}
    active = []
    for template in career_roster(BASE_NPCS, career_state):
        npc_id = template["id"]
        npc = live.get(npc_id, {})
        npc.clear()
        npc.update(copy.deepcopy(template))
        state = career_state.get(npc_id)
        if isinstance(state, dict):
            for key in ("age", "birthday_month", "public_appeal"):
                if key in state:
                    npc[key] = state[key]
            if isinstance(state.get("ratings"), dict):
                npc["career_ratings"] = dict(state["ratings"])
                npc["skill_tier"] = rating_tier(state["ratings"]["overall"])
            if "fans" in state:
                npc["career_fans"] = state["fans"]
            if state.get("development"):
                npc["career_stage"] = development_stage(state, month)
                npc["is_prodigy"] = bool(state["development"].get("prodigy"))
            if "joined_month" in state:
                npc["joined_month"] = state["joined_month"]
        active.append(npc)
    NPCS[:] = active


def get_random_npc(
        minimum_age=None,
        exclude_ids=None
):

    if exclude_ids is None:
        exclude_ids = []

    candidates = []

    for npc in NPCS:

        if npc.get("id") in exclude_ids:
            continue

        if (
                minimum_age is not None
                and npc.get("age", 0)
                < minimum_age
        ):
            continue

        candidates.append(
            npc
        )

    if not candidates:
        return None

    return random.choice(
        candidates
    )


def get_random_npc_group(
        count,
        minimum_age=None,
        exclude_ids=None
):

    if exclude_ids is None:
        exclude_ids = []

    used_ids = set(exclude_ids)
    group = []

    try:
        count = max(0, int(count))
    except (TypeError, ValueError):
        count = 0

    for _ in range(count):
        npc = get_random_npc(
            minimum_age=minimum_age,
            exclude_ids=used_ids
        )

        if npc is None:
            break

        group.append(npc)
        used_ids.add(npc.get("id"))

    return group


def get_random_blackjack_dealer():

    return get_random_npc(
        minimum_age=18
    )


def get_random_score_four_opponent():

    return get_random_npc()


def get_random_npc_by_tier(
        skill_tier,
        exclude_ids=None,
        game_key=None
):

    if exclude_ids is None:
        exclude_ids = []

    candidates = [
        npc for npc in NPCS
        if (
            (rating_tier(npc["career_ratings"][game_key])
             if game_key and game_key in npc.get("career_ratings", {})
             else npc.get("skill_tier")) == skill_tier
            and npc.get("id") not in exclude_ids
        )
    ]

    if not candidates:
        return None

    return random.choice(
        candidates
    )


def get_npcs_missing_portraits():

    return [
        npc
        for npc in NPCS
        if not npc.get("portrait")
    ]


def get_score_four_opponent_choices():

    tiers = [
        "low",
        "mid",
        "strong",
        "elite",
    ]

    choices = []

    used_ids = []

    for tier in tiers:

        npc = get_random_npc_by_tier(
            tier,
            exclude_ids=used_ids,
            game_key="score_four",
        )

        if npc is not None:

            choices.append(
                npc
            )

            used_ids.append(
                npc["id"]
            )

    return choices

