"""Ace Invaders Arcade Night tuning and difficulty helpers."""
from __future__ import annotations


ACE_INVADERS_DIFFICULTIES = {
    "casual": {
        "label": "CASUAL",
        "ticket_multiplier": 0.75,
        "description": "Slower formations, relaxed enemy fire.",
        "formation_speed": 54.0,
        "enemy_fire_ms": 1450,
        "enemy_bullet_speed": 185.0,
        "player_fire_ms": 260,
        "rows": 3,
        "columns": 7,
        "drop_distance": 20,
    },
    "standard": {
        "label": "STANDARD",
        "ticket_multiplier": 1.00,
        "description": "Classic arcade pacing and pressure.",
        "formation_speed": 68.0,
        "enemy_fire_ms": 1125,
        "enemy_bullet_speed": 220.0,
        "player_fire_ms": 245,
        "rows": 3,
        "columns": 8,
        "drop_distance": 22,
    },
    "difficult": {
        "label": "DIFFICULT",
        "ticket_multiplier": 1.35,
        "description": "Faster Aces with heavier return fire.",
        "formation_speed": 84.0,
        "enemy_fire_ms": 850,
        "enemy_bullet_speed": 260.0,
        "player_fire_ms": 235,
        "rows": 4,
        "columns": 8,
        "drop_distance": 24,
    },
    "expert": {
        "label": "EXPERT",
        "ticket_multiplier": 1.75,
        "description": "Dense waves, fast shots, little breathing room.",
        "formation_speed": 102.0,
        "enemy_fire_ms": 650,
        "enemy_bullet_speed": 305.0,
        "player_fire_ms": 225,
        "rows": 4,
        "columns": 9,
        "drop_distance": 26,
    },
}


def get_ace_invaders_difficulty(difficulty_id):
    return ACE_INVADERS_DIFFICULTIES.get(
        difficulty_id,
        ACE_INVADERS_DIFFICULTIES["standard"],
    )
