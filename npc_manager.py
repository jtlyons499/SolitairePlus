import json
import random
from pathlib import Path


NPC_FILE = (
    Path(__file__).parent
    / "data"
    / "npcs.json"
)


def load_npcs():

    with open(
            NPC_FILE,
            "r",
            encoding="utf-8"
    ) as file:

        return json.load(file)


NPCS = load_npcs()


def sync_npc_runtime_state(career_state):
    """Apply save-specific NPC age/rating metadata to the live NPC roster.

    The JSON file remains the immutable starting roster. Career Mode owns the
    changing age/rating state, and this helper lets Poker, Blackjack, Score-Four
    and other game selectors see the same current age without rewriting JSON.
    """
    if not isinstance(career_state, dict):
        return

    for npc in NPCS:
        npc_id = npc.get("id")
        state = career_state.get(npc_id)

        if not isinstance(state, dict):
            continue

        if "age" in state:
            npc["age"] = state["age"]

        if "birthday_month" in state:
            npc["birthday_month"] = state["birthday_month"]

        if isinstance(state.get("ratings"), dict):
            npc["career_ratings"] = dict(state["ratings"])

        if "fans" in state:
            npc["career_fans"] = state["fans"]

        if "public_appeal" in state:
            npc["public_appeal"] = state["public_appeal"]


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
        exclude_ids=None
):

    if exclude_ids is None:
        exclude_ids = []

    candidates = [
        npc for npc in NPCS
        if (
            npc.get("skill_tier") == skill_tier
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
            exclude_ids=used_ids
        )

        if npc is not None:

            choices.append(
                npc
            )

            used_ids.append(
                npc["id"]
            )

    return choices
