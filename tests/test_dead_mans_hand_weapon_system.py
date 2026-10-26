from pathlib import Path

from dead_mans_hand import LEVELS, wall_at
from dead_mans_hand_weapons import DEFAULT_WEAPON_PICKUPS, WEAPON_DEFINITIONS, weapon_for_slot

ROOT = Path(__file__).resolve().parents[1]


def test_dead_mans_hand_sfx_live_in_dedicated_folder():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    for filename in (
        "pistol_shot.wav", "pistol_reload.wav",
        "kar98k_shot.wav", "kar98k_bolt.wav", "kar98k_reload.wav",
        "thompson_shot.wav", "thompson_reload.wav",
        "scar20_shot.wav", "scar20_reload.wav", "weapon_pickup.wav",
        "enemy_hit.wav", "enemy_down.wav", "player_hit.wav", "player_down.wav",
    ):
        assert f"assets/sounds/dead_mans_hand/{filename}" in source


def test_weapon_roster_and_core_behavior():
    assert weapon_for_slot(1) == "pistol"
    assert weapon_for_slot(2) == "kar98k"
    assert weapon_for_slot(3) == "thompson"
    assert weapon_for_slot(4) == "scar20"
    assert WEAPON_DEFINITIONS["kar98k"]["mag_size"] == 5
    assert WEAPON_DEFINITIONS["kar98k"]["bolt_seconds"] > 0
    assert WEAPON_DEFINITIONS["thompson"]["mag_size"] == 30
    assert WEAPON_DEFINITIONS["thompson"]["automatic"] is True
    assert WEAPON_DEFINITIONS["scar20"]["mag_size"] == 10
    assert WEAPON_DEFINITIONS["scar20"]["ads_fov"] < WEAPON_DEFINITIONS["pistol"]["ads_fov"]


def test_starter_pickups_are_in_open_level_cells():
    for level_index, entries in DEFAULT_WEAPON_PICKUPS.items():
        level = LEVELS[level_index]
        for weapon_id, x, y in entries:
            assert weapon_id in WEAPON_DEFINITIONS
            assert wall_at(level, x, y) is None


def test_renderer_has_ads_reload_bolt_pickups_and_viewmodel_frames():
    source = (ROOT / "dead_mans_hand_game.py").read_text(encoding="utf-8")
    assert "def set_aiming(self, active):" in source
    assert "def start_reload(self):" in source
    assert "def switch_weapon_by_slot(self, slot):" in source
    assert "def cycle_weapon(self, direction=1):" in source
    assert "def _render_pickup(self, pickup):" in source
    assert "PICKUP_SPIN_SPEED" in source
    assert "bolt_" in source
    assert 'Path("dead_mans_hand") / "weapons" / "muzzle_flash.png"' in source


def test_main_wires_weapon_switching_trigger_hold_and_reload():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "dead_mans_hand_game.switch_weapon_by_slot" in source
    assert "dead_mans_hand_game.cycle_weapon" in source
    assert "dead_mans_hand_game.set_trigger_held(True)" in source
    assert "dead_mans_hand_game.set_trigger_held(False)" in source
    assert "dead_mans_hand_game.start_reload()" in source


def test_hud_supports_custom_assets_without_health_or_ammo_numbers():
    source = (ROOT / "dead_mans_hand_game.py").read_text(encoding="utf-8")
    assert 'Path("dead_mans_hand") / "ui" / "health_bar_bg.png"' in source
    assert 'Path("dead_mans_hand") / "ui" / "ammo_bar_bg.png"' in source
    assert 'Path("dead_mans_hand") / "ui" / "kill_count.png"' in source
    assert 'Path("dead_mans_hand") / "ui" / "weapons" / f"{weapon_id}.png"' in source
    assert 'Scary Halloween Font.ttf' in source
    assert 'f"{self.health:03d}"' not in source
    assert 'f"{self.pistol_ammo:02d}' not in source


def test_dead_mans_hand_hides_live_score_and_tracks_total_kills():
    source = (ROOT / "dead_mans_hand_game.py").read_text(encoding="utf-8")
    assert 'f"SCORE {self.score:,}' not in source
    assert "self.total_kills = 0" in source
    assert "self.total_kills += 1" in source
    assert 'Final score {self.score:,}' in source


def test_pistol_tuning_keeps_separate_ads_and_hip_muzzle_anchors():
    pistol = WEAPON_DEFINITIONS["pistol"]
    assert pistol["hip"]["anchor"] == (0.690, 1.040)
    assert pistol["ads"]["anchor"] == (0.515, 1.060)
    assert pistol["hip"]["muzzle_uv"] != pistol["ads"]["muzzle_uv"]
