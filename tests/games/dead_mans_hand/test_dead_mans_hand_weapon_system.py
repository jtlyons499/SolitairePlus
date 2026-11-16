"""Dead Man's Hand weapons, viewmodel art and HUD.

Some checks read the source; the HUD and viewmodel checks build a real
DeadMansHandGame whose art comes from a temporary folder.
"""
import os
import tempfile
from pathlib import Path
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from tests.support import locate
from solitaireplus.games.dead_mans_hand.game import DeadMansHandGame
from solitaireplus.games.dead_mans_hand.levels import LEVELS, RENDER_HEIGHT, RENDER_WIDTH, wall_at
from solitaireplus.games.dead_mans_hand.weapons import DEFAULT_WEAPON_PICKUPS, WEAPON_DEFINITIONS, weapon_for_slot

ROOT = Path(__file__).resolve().parents[3]
DMH = Path("dead_mans_hand")


def _game(asset_root):
    """A real DeadMansHandGame that loads its art from asset_root."""
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))  # convert()/convert_alpha() need a display mode
    return DeadMansHandGame(asset_root=str(asset_root))


def _write_png(path, size):
    path.parent.mkdir(parents=True, exist_ok=True)
    surface = pygame.Surface(size, pygame.SRCALPHA)
    surface.fill((200, 40, 40, 255))
    pygame.image.save(surface, str(path))


class _RecordingFont:
    """Wraps a pygame font and remembers every text drawn with it."""

    def __init__(self, font, texts):
        self._font = font
        self._texts = texts

    def render(self, text, *args, **kwargs):
        self._texts.append(str(text))
        return self._font.render(text, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._font, name)


class _BlitRecorder(pygame.Surface):
    """A surface that remembers the destination of every blit onto it."""

    def __init__(self, size):
        super().__init__(size)
        self.destinations = []

    def blit(self, source, dest, *args, **kwargs):
        self.destinations.append(dest)
        return super().blit(source, dest, *args, **kwargs)


def test_dead_mans_hand_sfx_live_in_dedicated_folder():
    source = locate.source()
    for filename in (
        "pistol_shot.wav", "pistol_reload.wav",
        "kar98k_shot.wav", "kar98k_bolt.wav", "kar98k_reload.wav",
        "thompson_shot.wav", "thompson_reload.wav",
        "scar20_shot.wav", "scar20_reload.wav", "weapon_pickup.wav",
        "enemy_hit.wav", "enemy_down.wav", "player_hit.wav", "player_down.wav",
    ):
        assert f'paths.asset("sounds/dead_mans_hand/{filename}")' in source


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
    source = (ROOT / "solitaireplus/games/dead_mans_hand/game.py").read_text(encoding="utf-8")
    assert "def set_aiming(self, active):" in source
    assert "def start_reload(self):" in source
    assert "def switch_weapon_by_slot(self, slot):" in source
    assert "def cycle_weapon(self, direction=1):" in source
    assert "def _render_pickup(self, pickup):" in source
    assert "PICKUP_SPIN_SPEED" in source
    assert "bolt_" in source
    assert 'Path("dead_mans_hand") / "weapons" / "muzzle_flash.png"' in source


def test_main_wires_weapon_switching_trigger_hold_and_reload():
    source = locate.source()
    assert "dead_mans_hand_game.switch_weapon_by_slot" in source
    assert "dead_mans_hand_game.cycle_weapon" in source
    assert "dead_mans_hand_game.set_trigger_held(True)" in source
    assert "dead_mans_hand_game.set_trigger_held(False)" in source
    assert "dead_mans_hand_game.start_reload()" in source


def test_main_wires_rmb_ads_and_weapon_sound_names():
    source = locate.source()
    assert "dead_mans_hand_game.set_aiming(True)" in source
    assert "dead_mans_hand_game.set_aiming(False)" in source
    for weapon_id in WEAPON_DEFINITIONS:
        for sound in ("shot", "reload"):
            assert f'"{weapon_id}_{sound}": "dead_mans_hand_{weapon_id}_{sound}"' in source


def test_viewmodel_prefers_weapon_folders_but_keeps_old_pistol_fallback():
    weapons = DMH / "weapons"
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        _write_png(root / weapons / "sniper" / "idle.png", (10, 20))        # new art, named by asset_slug
        _write_png(root / weapons / "scar20" / "idle.png", (11, 20))        # older art, named by weapon id
        _write_png(root / weapons / "pistol" / "pistol_ads.png", (12, 20))  # <folder>/<folder>_<frame>.png
        _write_png(root / DMH / "weapon.png", (13, 20))                     # the prototype's single pistol image
        game = _game(root)

        def width(weapon_id, stems):
            surface = game._load_first_weapon_frame(weapon_id, stems)
            return None if surface is None else surface.get_width()

        assert width("scar20", ["idle"]) == 10
        assert width("pistol", ["ads_fire", "ads"]) == 12
        assert width("pistol", ["idle"]) == 13
        assert width("kar98k", ["idle"]) is None  # no art: a placeholder shape is drawn


def test_hud_supports_custom_assets_without_health_or_ammo_numbers():
    # Custom PNGs replace the drawn bars, kill counter, level title and weapon names.
    # Health and ammo are shown only as bars, never as numbers.
    hud_art = {
        "ui/health_bar_bg.png": (360, 72), "ui/health_bar_fill.png": (320, 28),
        "ui/ammo_bar_bg.png": (360, 72), "ui/ammo_bar_fill.png": (320, 28),
        "ui/kill_count.png": (208, 36), "ui/levels/level_01.png": (600, 76),
        "ui/weapons/pistol.png": (64, 64),
        "ui/weapons/sniper.png": (64, 64),  # scar20 icon, found by its asset_slug
    }
    loaded, texts = [], []
    with tempfile.TemporaryDirectory() as folder:
        for name, size in hud_art.items():
            _write_png(Path(folder) / DMH / name, size)
        game = _game(folder)
        game.owned_weapons = {"pistol", "scar20"}
        game.health = 73
        game.weapon_ammo["pistol"] = 9
        for enemy in game.enemies[:2]:
            enemy.alive = False
        game.total_kills = 7  # kills so far: not the number of enemies still standing
        alive = sum(1 for enemy in game.enemies if enemy.alive)
        assert alive not in (0, game.total_kills), alive

        load_ui_surface, font, dmh_font = game._load_ui_surface, game._font, game._dmh_font

        def recording_load(relative_path):
            surface = load_ui_surface(relative_path)
            if surface is not None:
                loaded.append(Path(relative_path).relative_to(DMH).as_posix())
            return surface

        def recording(make_font):
            return lambda *args, **kwargs: _RecordingFont(make_font(*args, **kwargs), texts)

        game._load_ui_surface = recording_load
        game._font = recording(font)          # the game's cached fonts
        game._dmh_font = recording(dmh_font)
        # Fonts made directly while drawing the HUD are recorded too.
        with mock.patch.object(pygame.font, "Font", recording(pygame.font.Font)), \
                mock.patch.object(pygame.font, "SysFont", recording(pygame.font.SysFont)):
            game._draw_hud(pygame.Surface((1366, 768)))

        assert set(hud_art) <= set(loaded), sorted(set(hud_art) - set(loaded))
        assert "7" in texts, texts  # the kill count is written on the custom kill_count.png
        assert str(alive) not in texts, texts  # ...and it is not the enemies left
        for number in ("73", "9", "12"):  # health, pistol ammo, magazine size
            assert not any(number in text for text in texts), (number, texts)

    with tempfile.TemporaryDirectory() as folder:
        _write_png(Path(folder) / DMH / "ui" / "weapons" / "scar20.png", (30, 30))
        game = _game(folder)
        icon = game._load_weapon_icon("scar20")
        assert icon is not None and icon.get_size() == (30, 30)  # the weapon-id file name still works
        assert game._load_weapon_icon("kar98k") is None  # no icon: the sidebar writes the weapon name


def test_hud_fonts_prefer_the_custom_font_files():
    tried = []
    real_font = pygame.font.Font

    def recording_font(path, size):
        tried.append(Path(path).name if path else None)
        return real_font(path, size)

    with tempfile.TemporaryDirectory() as folder:
        game = _game(folder)  # no font files here, so every custom font is missing
        with mock.patch.object(pygame.font, "Font", recording_font):
            game._dmh_font("numbers", 24)
            game._dmh_font("ui", 24)
    assert tried == [
        "Scary Halloween Font.ttf", "dead_mans_hand_numbers.ttf", None,
        "Scary Halloween Font.ttf", "dead_mans_hand_ui.ttf", None,
    ]


def test_dead_mans_hand_hides_live_score_and_tracks_total_kills():
    source = (ROOT / "solitaireplus/games/dead_mans_hand/game.py").read_text(encoding="utf-8")
    assert 'f"SCORE {self.score:,}' not in source
    assert "self.total_kills = 0" in source
    assert "self.total_kills += 1" in source
    assert 'Final score {self.score:,}' in source


def test_pistol_tuning_keeps_separate_ads_and_hip_muzzle_anchors():
    # Hip fire holds each gun low and to the right; aiming brings it bigger and to the centre,
    # and the muzzle-flash point has its own position in each pose.
    for weapon_id, cfg in WEAPON_DEFINITIONS.items():
        hip, ads = cfg["hip"], cfg["ads"]
        assert hip["anchor"] != ads["anchor"], weapon_id
        assert hip["muzzle_uv"] != ads["muzzle_uv"], weapon_id
        assert hip["anchor"][0] > 0.5, weapon_id
        assert abs(ads["anchor"][0] - 0.5) < abs(hip["anchor"][0] - 0.5), weapon_id
        assert ads["height"] > hip["height"], weapon_id

    # The renderer really uses the two anchors: not aiming -> hip anchor, fully aimed -> ADS anchor.
    pistol = WEAPON_DEFINITIONS["pistol"]
    art = pygame.Surface((20, 40), pygame.SRCALPHA)
    with tempfile.TemporaryDirectory() as folder:
        game = _game(folder)
        game._load_first_weapon_frame = lambda weapon_id, stems: art
        for blend, pose in ((0.0, "hip"), (1.0, "ads")):
            game.ads_blend = blend
            game.render_surface = _BlitRecorder((RENDER_WIDTH, RENDER_HEIGHT))
            game._render_weapon()
            rect = pygame.Rect(game.render_surface.destinations[-1])
            anchor_x, anchor_y = pistol[pose]["anchor"]
            assert abs(rect.centerx - anchor_x * RENDER_WIDTH) <= 1, (pose, rect)
            assert abs(rect.bottom - anchor_y * RENDER_HEIGHT) <= 1, (pose, rect)
            assert rect.height == pistol[pose]["height"], (pose, rect)
