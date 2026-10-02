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