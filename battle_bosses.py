"""Battle Bosses Arcade Night setup helpers.

Gameplay will use the selected three-rival squad. This module stays free of
pygame so opponent generation and tuning can be regression-tested cheaply.
"""
from __future__ import annotations

import random


BATTLE_BOSSES_DIFFICULTIES = {
    "casual": {
        "label": "CASUAL",
        "ticket_multiplier": 0.80,
        "tier_mix": ("low", "low", "mid"),
        "description": "Forgiving shields and a mixed rookie squad.",
        "npc_shield_speed": 54.0,
        "aim_error": 21.0,
        "reaction_distance": 390.0,
        "ball_speed": 325.0,
    },
    "standard": {
        "label": "STANDARD",
        "ticket_multiplier": 1.00,
        "tier_mix": ("low", "mid", "strong"),
        "description": "A varied three-rival lineup with normal pacing.",
        "npc_shield_speed": 68.0,
        "aim_error": 15.0,
        "reaction_distance": 455.0,
        "ball_speed": 340.0,
    },
    "difficult": {
        "label": "DIFFICULT",
        "ticket_multiplier": 1.40,
        "tier_mix": ("mid", "strong", "strong"),
        "description": "Aggressive shields and stronger corner rivals.",
        "npc_shield_speed": 82.0,
        "aim_error": 9.0,
        "reaction_distance": 520.0,
        "ball_speed": 360.0,
    },
    "expert": {
        "label": "EXPERT",
        "ticket_multiplier": 1.85,
        "tier_mix": ("strong", "elite", "elite"),
        "description": "Fast reactions and a tournament-level trio.",
        "npc_shield_speed": 98.0,
        "aim_error": 5.0,
        "reaction_distance": 590.0,
        "ball_speed": 380.0,
    },
}


def _available_npcs(npcs):
    return [
        npc for npc in (npcs or [])
        if isinstance(npc, dict) and npc.get("name")
    ]


def _npc_identity(npc):
    return npc.get("id") or npc.get("name")


def build_battle_bosses_squad(npcs, difficulty_id, rng=None):
    """Choose three distinct NPCs matching the requested difficulty mix."""
    rng = rng or random
    config = BATTLE_BOSSES_DIFFICULTIES.get(
        difficulty_id,
        BATTLE_BOSSES_DIFFICULTIES["standard"],
    )
    pool = _available_npcs(npcs)
    chosen = []
    used = set()

    for seat_index, desired_tier in enumerate(config["tier_mix"]):
        tier_pool = [
            npc for npc in pool
            if npc.get("skill_tier", "mid") == desired_tier
            and _npc_identity(npc) not in used
        ]
        fallback = [
            npc for npc in pool
            if _npc_identity(npc) not in used
        ]
        candidates = tier_pool or fallback

        if candidates:
            npc = rng.choice(candidates)
        else:
            npc = {
                "id": f"battle_bosses_{difficulty_id}_{seat_index}",
                "name": f"Arcade Boss {seat_index + 1}",
                "skill_tier": desired_tier,
            }

        identity = _npc_identity(npc)
        if identity is not None:
            used.add(identity)
        chosen.append(npc)

    return chosen


def build_battle_bosses_choices(npcs, rng=None):
    """Build one three-NPC squad for each selectable difficulty."""
    return [
        {
            "difficulty_id": difficulty_id,
            "config": config,
            "npcs": build_battle_bosses_squad(npcs, difficulty_id, rng=rng),
        }
        for difficulty_id, config in BATTLE_BOSSES_DIFFICULTIES.items()
    ]
