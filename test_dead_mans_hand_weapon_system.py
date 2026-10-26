from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dead_mans_hand_sfx_live_in_dedicated_folder():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "assets/sounds/dead_mans_hand/pistol_shot.wav" in source
    assert "assets/sounds/dead_mans_hand/pistol_reload.wav" in source
    assert "assets/sounds/dead_mans_hand/enemy_hit.wav" in source
    assert "assets/sounds/dead_mans_hand/enemy_down.wav" in source
    assert "assets/sounds/dead_mans_hand/player_hit.wav" in source
    assert "assets/sounds/dead_mans_hand/player_down.wav" in source


def test_dead_mans_hand_has_ads_reload_and_per_weapon_viewmodel_config():
    source = (ROOT / "dead_mans_hand_game.py").read_text(encoding="utf-8")
    assert "PISTOL_VIEWMODEL" in source
    assert "ADS_FOV" in source
    assert "def set_aiming(self, active):" in source
    assert "def start_reload(self):" in source
    assert "pistol_ads.png" in source
    assert "pistol_ads_fire.png" in source
    assert "pistol_reload_" in source
    assert 'Path("dead_mans_hand") / "weapons" / "muzzle_flash.png"' in source


def test_dead_mans_hand_main_wires_rmb_ads_and_r_reload():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "dead_mans_hand_game.set_aiming(True)" in source
    assert "dead_mans_hand_game.set_aiming(False)" in source
    assert "dead_mans_hand_game.start_reload()" in source
    assert '"pistol_shot": "dead_mans_hand_pistol_shot"' in source
    assert '"pistol_reload": "dead_mans_hand_pistol_reload"' in source


def test_dead_mans_hand_viewmodel_prefers_new_weapon_folder_but_keeps_old_fallback():
    source = (ROOT / "dead_mans_hand_game.py").read_text(encoding="utf-8")
    assert 'Path("dead_mans_hand") / "weapons" / "pistol" / frame' in source
    assert 'Path("dead_mans_hand") / "weapon.png"' in source


def test_dead_mans_hand_hud_supports_custom_ui_assets_and_level_pngs():
    source = (ROOT / "dead_mans_hand_game.py").read_text(encoding="utf-8")
    assert 'Path("dead_mans_hand") / "ui" / "health_bar_bg.png"' in source
    assert 'Path("dead_mans_hand") / "ui" / "health_bar_fill.png"' in source
    assert 'Path("dead_mans_hand") / "ui" / "ammo_bar_bg.png"' in source
    assert 'Path("dead_mans_hand") / "ui" / "ammo_bar_fill.png"' in source
    assert 'Path("dead_mans_hand") / "ui" / "kill_count.png"' in source
    assert 'Path("dead_mans_hand") / "ui" / "levels" / f"level_{int(level_number):02d}.png"' in source
    assert 'dead_mans_hand_numbers.ttf' in source
    assert 'Scary Halloween Font.ttf' in source
    assert 'dead_mans_hand_ui.ttf' in source


def test_dead_mans_hand_hides_live_score_and_uses_kills_in_gameplay_hud():
    source = (ROOT / "dead_mans_hand_game.py").read_text(encoding="utf-8")
    assert 'f"SCORE {self.score:,}' not in source
    assert 'kill_count_value = getattr(self, "total_kills", 0)' in source
    assert 'Final score {self.score:,}' in source


def test_dead_mans_hand_weapon_tuning_has_separate_ads_and_hip_muzzle_anchors():
    source = (ROOT / "dead_mans_hand_game.py").read_text(encoding="utf-8")
    assert '"anchor": (0.690, 1.040)' in source
    assert '"anchor": (0.515, 1.060)' in source
    assert '"muzzle_uv": (0.09, 0.13)' in source
    assert '"muzzle_uv": (0.505, 0.255)' in source


def test_dead_mans_hand_tracks_total_kills_instead_of_remaining_enemies():
    source = (ROOT / "dead_mans_hand_game.py").read_text(encoding="utf-8")
    assert 'self.total_kills = 0' in source
    assert 'self.total_kills += 1' in source
