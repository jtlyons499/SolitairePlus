"""Pure weapon data for Dead Man's Hand.

No pygame dependency: weapon balance, slot assignments, and starter pickup
placements can be tested or extended without importing the renderer.
"""

from __future__ import annotations

import math

WEAPON_DEFINITIONS = {
    "pistol": {
        "name": "Pistol", "slot": 1, "mag_size": 12, "damage": 48.0,
        "fire_interval": 0.245, "automatic": False, "reload_seconds": 1.05,
        "reload_frames": 4, "ads_fov": math.radians(49.0), "bolt_seconds": 0.0,
        "hip": {"anchor": (0.690, 1.040), "height": 112, "muzzle_uv": (0.09, 0.13)},
        "ads": {"anchor": (0.515, 1.060), "height": 120, "muzzle_uv": (0.505, 0.255)},
        "bob_x": 3.2, "bob_y": 2.0, "recoil_y": 8.0,
    },
    "kar98k": {
        "name": "Kar98k", "slot": 2, "mag_size": 5, "damage": 135.0,
        "fire_interval": 0.34, "automatic": False, "reload_seconds": 2.25,
        "reload_frames": 3, "ads_fov": math.radians(39.0), "bolt_seconds": 0.82,
        "bolt_frames": 3,
        "hip": {"anchor": (0.705, 1.055), "height": 126, "muzzle_uv": (0.12, 0.15)},
        "ads": {"anchor": (0.505, 1.070), "height": 132, "muzzle_uv": (0.50, 0.22)},
        "bob_x": 2.7, "bob_y": 1.8, "recoil_y": 14.0,
    },
    "thompson": {
        "name": "Thompson", "slot": 3, "mag_size": 30, "damage": 24.0,
        "fire_interval": 0.085, "automatic": True, "reload_seconds": 1.85,
        "reload_frames": 3, "ads_fov": math.radians(52.0), "bolt_seconds": 0.0,
        "hip": {"anchor": (0.685, 1.055), "height": 130, "muzzle_uv": (0.11, 0.16)},
        "ads": {"anchor": (0.510, 1.070), "height": 136, "muzzle_uv": (0.50, 0.23)},
        "bob_x": 3.6, "bob_y": 2.3, "recoil_y": 5.5,
    },
    "scar20": {
        "name": "SCAR-20", "slot": 4, "mag_size": 10, "damage": 92.0,
        "fire_interval": 0.31, "automatic": False, "reload_seconds": 1.95,
        "reload_frames": 3, "ads_fov": math.radians(28.0), "bolt_seconds": 0.0,
        "hip": {"anchor": (0.710, 1.060), "height": 132, "muzzle_uv": (0.11, 0.15)},
        "ads": {"anchor": (0.505, 1.075), "height": 140, "muzzle_uv": (0.50, 0.22)},
        "bob_x": 2.8, "bob_y": 1.8, "recoil_y": 10.0,
    },
}

# Starter prototype placements. These deliberately live outside dead_mans_hand.py
# so a weapon patch never overwrites locally customized level names.
DEFAULT_WEAPON_PICKUPS = {
    0: (("kar98k", 4.5, 10.5),),
    1: (("thompson", 4.5, 11.5),),
    2: (("scar20", 10.5, 12.5),),
}


def weapon_for_slot(slot: int) -> str | None:
    slot = int(slot)
    for weapon_id, config in WEAPON_DEFINITIONS.items():
        if int(config["slot"]) == slot:
            return weapon_id
    return None
