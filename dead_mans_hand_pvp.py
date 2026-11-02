"""Dead Man's Hand 1v1 PvP prototype using the existing Solitaire+ relay.

The host is authoritative for health, scoring, hit confirmation and respawns.
Movement remains client-side for responsiveness and poses are synchronized at
20 Hz.  The protocol deliberately rides the legacy two-player relay so the
currently deployed relay server needs no update.
"""
from __future__ import annotations

import math
import queue
import time
from pathlib import Path

import pygame

from dead_mans_hand import FOV, LEVELS, RENDER_HEIGHT, RENDER_WIDTH, normalize_angle, wall_at
from dead_mans_hand_game import (
    ADS_TRANSITION_SPEED,
    JUMP_GRAVITY,
    JUMP_IMPULSE,
    MAX_SHIELD,
    DeadMansHandGame,
)
from dead_mans_hand_weapons import WEAPON_DEFINITIONS
from relay_transport import RelayPeer

ARENA_LEVEL_INDEX = 5  # O.K. Corral
SYNC_INTERVAL = 0.05   # 20 Hz
FIRST_TO_KILLS = 5
RESPAWN_SECONDS = 2.0
SPAWN_PROTECTION_SECONDS = 1.0
REMOTE_SMOOTH_RATE = 13.0
PLAYER_RADIUS = 0.24
PVP_DAMAGE = {"pistol": 34, "kar98k": 82, "thompson": 17, "scar20": 68}


def _open_cells(level):
    rows = level["map"]
    return [(x + .5, y + .5) for y, row in enumerate(rows) for x, c in enumerate(row) if c == "."]


def _spawn_pair(level):
    """Choose two distant, reachable floor positions from the authored arena."""
    cells = _open_cells(level)
    if not cells:
        return ((2.5, 2.5, 0.0), (3.5, 3.5, math.pi))
    a = min(cells, key=lambda p: p[0] + p[1])
    b = max(cells, key=lambda p: (p[0] - a[0]) ** 2 + (p[1] - a[1]) ** 2)
    angle_a = math.atan2(b[1] - a[1], b[0] - a[0])
    angle_b = normalize_angle(angle_a + math.pi)
    return ((a[0], a[1], angle_a), (b[0], b[1], angle_b))


SPAWNS = _spawn_pair(LEVELS[ARENA_LEVEL_INDEX])


def _los(level, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    distance = math.hypot(dx, dy)
    steps = max(1, int(distance / .075))
    for step in range(1, steps):
        t = step / steps
        if wall_at(level, x0 + dx * t, y0 + dy * t):
            return False
    return True


def _shot_hits(level, shooter, target):
    if not shooter or not target or target.get("dead"):
        return False
    sx, sy = float(shooter.get("x", 0)), float(shooter.get("y", 0))
    tx, ty = float(target.get("x", 0)), float(target.get("y", 0))
    distance = math.hypot(tx - sx, ty - sy)
    if distance <= .05 or distance > 24:
        return False
    aim = float(shooter.get("angle", 0))
    delta = normalize_angle(math.atan2(ty - sy, tx - sx) - aim)
    # Slightly forgiving hit cone, roughly matching campaign card targeting.
    angular_radius = min(.16, .30 / max(.7, distance))
    if abs(delta) > angular_radius:
        return False
    if not _los(level, sx, sy, tx, ty):
        return False
    # A high jump can move the target above a chest-level hitscan.
    if float(target.get("z", 0)) > .72 and distance < 3.0:
        return False
    return True


class PvPGame(DeadMansHandGame):
    """DMH renderer/input stripped of campaign enemies and room progression."""
    def __init__(self, side: int):
        self.side = int(side)
        super().__init__()
        self.level_index = ARENA_LEVEL_INDEX
        self.level = LEVELS[self.level_index]
        self.enemies = []
        self.pickups = []
        self.score = 0
        self.total_kills = 0
        self.game_over = False
        self.prototype_complete = False
        self.owned_weapons = set(WEAPON_DEFINITIONS)
        self.weapon_ammo = {wid: int(cfg["mag_size"]) for wid, cfg in WEAPON_DEFINITIONS.items()}
        self.current_weapon_id = "pistol"
        self.remote = None
        self.remote_target = None
        self.remote_name = "Opponent"
        self.local_name = "YOU"
        self.remote_health = 100
        self.remote_score = 0
        self.local_score = 0
        self.match_over = False
        self.winner_text = ""
        self.respawn_text = ""
        self.spawn_protection_timer = 0.0
        self.remote_muzzle_timer = 0.0
        self.remote_weapon = "pistol"
        self.hit_marker_timer = 0.0
        self.kill_marker_timer = 0.0
        self.kill_feed = []
        self._shot_events = []
        self.respawn(side)

    def respawn(self, side=None):
        if side is not None:
            self.side = int(side)
        x, y, angle = SPAWNS[self.side]
        self.player_x, self.player_y, self.player_angle = float(x), float(y), float(angle)
        self.player_z = 0.0
        self.jump_velocity = 0.0
        self.health = 100
        self.shield = 0
        self.game_over = False
        self.damage_flash_timer = 0.0
        self.reloading = False
        self.reload_timer = 0.0
        self.bolt_timer = 0.0
        self.shot_timer = 0.0
        self.aiming_down_sights = False
        self.ads_blend = 0.0
        self.trigger_held = False
        self.weapon_ammo = {wid: int(cfg["mag_size"]) for wid, cfg in WEAPON_DEFINITIONS.items()}
        self.spawn_protection_timer = SPAWN_PROTECTION_SECONDS

    def local_pose(self):
        return {
            "x": round(self.player_x, 4), "y": round(self.player_y, 4),
            "angle": round(self.player_angle, 5), "z": round(self.player_z, 4),
            "weapon": self.current_weapon_id, "ads": round(self.ads_blend, 3),
            "dead": bool(self.game_over),
        }

    def set_remote(self, state, name=None):
        if isinstance(state, dict):
            self.remote_target = dict(state)
            self.remote_health = int(state.get("health", self.remote_health))
            self.remote_weapon = str(state.get("weapon", self.remote_weapon))
            if self.remote is None or state.get("respawn"):
                self.remote = dict(state)
        if name:
            self.remote_name = str(name)[:24]

    def notify_remote_shot(self, weapon):
        self.remote_weapon = str(weapon or self.remote_weapon)
        self.remote_muzzle_timer = 0.095

    def show_hit_marker(self, killed=False):
        self.hit_marker_timer = 0.14
        if killed:
            self.kill_marker_timer = 0.30

    def add_kill_feed(self, text):
        text = str(text).strip()
        if not text:
            return
        self.kill_feed.insert(0, [text[:72], 4.0])
        del self.kill_feed[4:]

    def _smooth_remote(self, dt):
        target = self.remote_target
        if not target:
            return
        if self.remote is None:
            self.remote = dict(target)
            return
        blend = min(1.0, REMOTE_SMOOTH_RATE * max(0.0, float(dt)))
        for key in ("x", "y", "z"):
            current = float(self.remote.get(key, target.get(key, 0.0)))
            wanted = float(target.get(key, current))
            self.remote[key] = current + (wanted - current) * blend
        current_angle = float(self.remote.get("angle", target.get("angle", 0.0)))
        wanted_angle = float(target.get("angle", current_angle))
        self.remote["angle"] = normalize_angle(current_angle + normalize_angle(wanted_angle - current_angle) * blend)
        for key in ("weapon", "ads", "dead", "health", "protected", "respawn"):
            if key in target:
                self.remote[key] = target[key]

    def fire(self):
        cfg = self.current_weapon_config()
        if self.game_over or self.match_over or self.shot_timer > 0 or self.reloading or self.bolt_timer > 0:
            return False
        if self.current_ammo() <= 0:
            self.start_reload(); return False
        self.weapon_ammo[self.current_weapon_id] = self.current_ammo() - 1
        self.shot_timer = float(cfg["fire_interval"])
        self.muzzle_flash_timer = .070 if cfg.get("automatic") else .095
        self._pending_sound_events.append(f"{self.current_weapon_id}_shot")
        bolt = float(cfg.get("bolt_seconds", 0))
        if bolt > 0:
            self.bolt_timer = bolt
            self._pending_sound_events.append(f"{self.current_weapon_id}_bolt")
        self._shot_events.append({
            "weapon": self.current_weapon_id,
            "x": self.player_x, "y": self.player_y, "z": self.player_z,
            "angle": self.player_angle,
        })
        return True

    def pop_shots(self):
        out = self._shot_events[:]
        self._shot_events.clear()
        return out

    def update(self, dt, keys):
        dt = max(0.0, min(.05, float(dt)))
        self.elapsed += dt
        self.shot_timer = max(0.0, self.shot_timer - dt)
        self.muzzle_flash_timer = max(0.0, self.muzzle_flash_timer - dt)
        self.damage_flash_timer = max(0.0, self.damage_flash_timer - dt)
        self.bolt_timer = max(0.0, self.bolt_timer - dt)
        self.spawn_protection_timer = max(0.0, self.spawn_protection_timer - dt)
        self.remote_muzzle_timer = max(0.0, self.remote_muzzle_timer - dt)
        self.hit_marker_timer = max(0.0, self.hit_marker_timer - dt)
        self.kill_marker_timer = max(0.0, self.kill_marker_timer - dt)
        for item in self.kill_feed:
            item[1] = max(0.0, item[1] - dt)
        self.kill_feed[:] = [item for item in self.kill_feed if item[1] > 0.0]
        self._smooth_remote(dt)

        ads_target = 1.0 if (self.aiming_down_sights and not self.reloading) else 0.0
        step = ADS_TRANSITION_SPEED * dt
        self.ads_blend += max(-step, min(step, ads_target - self.ads_blend))

        if self.reloading:
            self.reload_timer = max(0.0, self.reload_timer - dt)
            if self.reload_timer <= 0:
                self.reloading = False
                self.weapon_ammo[self.current_weapon_id] = int(self.current_weapon_config()["mag_size"])

        if self.game_over or self.match_over:
            self.is_moving = False
            return

        jump_down = bool(keys[pygame.K_SPACE])
        if jump_down and not self._jump_key_was_down and self.player_z <= .001:
            self.jump_velocity = JUMP_IMPULSE
        self._jump_key_was_down = jump_down
        if self.player_z > 0 or self.jump_velocity > 0:
            self.jump_velocity -= JUMP_GRAVITY * dt
            self.player_z += self.jump_velocity * dt
            if self.player_z <= 0:
                self.player_z = 0; self.jump_velocity = 0

        turn = (1 if keys[pygame.K_RIGHT] else 0) - (1 if keys[pygame.K_LEFT] else 0)
        self.player_angle = normalize_angle(self.player_angle + turn * self.TURN_SPEED * dt)
        forward = (1 if keys[pygame.K_w] else 0) - (1 if keys[pygame.K_s] else 0)
        strafe = (1 if keys[pygame.K_d] else 0) - (1 if keys[pygame.K_a] else 0)
        forward += (1 if keys[pygame.K_UP] else 0) - (1 if keys[pygame.K_DOWN] else 0)
        self.is_moving = bool(forward or strafe)
        if self.is_moving:
            length = max(1.0, math.hypot(forward, strafe)); forward /= length; strafe /= length
            ca, sa = math.cos(self.player_angle), math.sin(self.player_angle)
            move_scale = .82 if self.ads_blend > .5 else 1.0
            dx = (ca * forward * self.MOVE_SPEED * dt - sa * strafe * self.STRAFE_SPEED * dt) * move_scale
            dy = (sa * forward * self.MOVE_SPEED * dt + ca * strafe * self.STRAFE_SPEED * dt) * move_scale
            self._try_move(dx, dy)
            self.walk_phase = (self.walk_phase + dt * 10.5) % math.tau
        if self.trigger_held and self.current_weapon_config().get("automatic"):
            self.fire()

    def _remote_sprite(self, weapon_id=None, protected=False):
        """Procedural western opponent billboard; custom art can replace this later."""
        surf = pygame.Surface((84, 140), pygame.SRCALPHA)
        outline = (245, 211, 105, 255) if protected else (196, 47, 47, 255)
        coat = (61, 36, 30, 250)
        shirt = (28, 30, 31, 250)
        skin = (198, 154, 112, 255)
        hat = (42, 29, 22, 255)

        # Hat + head.
        pygame.draw.ellipse(surf, outline, (17, 7, 50, 12))
        pygame.draw.ellipse(surf, hat, (20, 9, 44, 8))
        pygame.draw.rect(surf, outline, (29, 0, 27, 14), border_radius=5)
        pygame.draw.rect(surf, hat, (32, 2, 21, 11), border_radius=4)
        pygame.draw.circle(surf, outline, (42, 28), 16)
        pygame.draw.circle(surf, skin, (42, 28), 12)
        pygame.draw.rect(surf, (45, 24, 20), (31, 31, 22, 4), border_radius=2)

        # Shoulders, coat and legs.
        pygame.draw.polygon(surf, outline, ((17, 49), (67, 49), (75, 108), (9, 108)))
        pygame.draw.polygon(surf, coat, ((21, 53), (63, 53), (69, 104), (15, 104)))
        pygame.draw.polygon(surf, shirt, ((36, 54), (48, 54), (53, 89), (31, 89)))
        pygame.draw.rect(surf, outline, (12, 105, 26, 31), border_radius=6)
        pygame.draw.rect(surf, outline, (46, 105, 26, 31), border_radius=6)
        pygame.draw.rect(surf, (25, 26, 27), (16, 108, 18, 27), border_radius=5)
        pygame.draw.rect(surf, (25, 26, 27), (50, 108, 18, 27), border_radius=5)

        # Readable remote weapon silhouette across the torso.
        weapon_id = str(weapon_id or self.remote_weapon)
        lengths = {"pistol": 23, "kar98k": 49, "thompson": 39, "scar20": 51}
        gun_len = lengths.get(weapon_id, 34)
        gun_y = 70
        gun_x = 42 - gun_len // 2
        pygame.draw.rect(surf, outline, (gun_x - 2, gun_y - 3, gun_len + 4, 10), border_radius=3)
        pygame.draw.rect(surf, (14, 16, 17), (gun_x, gun_y - 1, gun_len, 6), border_radius=2)
        if weapon_id == "thompson":
            pygame.draw.rect(surf, (14, 16, 17), (41, gun_y + 4, 7, 16), border_radius=2)
        return surf

    def _render_remote(self):
        r = self.remote
        if not r or r.get("dead"):
            return
        dx, dy = float(r.get("x", 0)) - self.player_x, float(r.get("y", 0)) - self.player_y
        distance = math.hypot(dx, dy)
        if distance <= .04:
            return
        delta = normalize_angle(math.atan2(dy, dx) - self.player_angle)
        current_fov = FOV + (float(self.current_weapon_config()["ads_fov"]) - FOV) * self.ads_blend
        if abs(delta) > current_fov * .64:
            return
        corrected = max(.05, distance * math.cos(delta))
        cx = int((.5 + delta / current_fov) * RENDER_WIDTH)
        if not (0 <= cx < RENDER_WIDTH):
            return
        if corrected >= self._z_buffer[cx] + .06:
            return

        zoom = min(1.35, max(1.0, FOV / max(.001, current_fov)))
        h = max(20, min(132, int((RENDER_HEIGHT * .62 / corrected) * zoom)))
        protected = bool(r.get("protected"))
        sprite = pygame.transform.smoothscale(
            self._remote_sprite(r.get("weapon"), protected),
            (max(12, int(h * .60)), h),
        )
        horizon = RENDER_HEIGHT // 2 + int(self.player_z * 18)
        bottom = horizon + max(8, min(78, int(92 / corrected * zoom))) - int(float(r.get("z", 0)) * 18)
        rect = sprite.get_rect(midbottom=(cx, bottom))
        for sx in range(rect.width):
            screen_x = rect.left + sx
            if 0 <= screen_x < RENDER_WIDTH and corrected < self._z_buffer[screen_x] + .06:
                self.render_surface.blit(sprite, (screen_x, rect.top), area=pygame.Rect(sx, 0, 1, rect.height))

        # Remote muzzle flash makes enemy fire readable without needing new art.
        if self.remote_muzzle_timer > 0.0:
            flash_x = min(RENDER_WIDTH - 3, rect.right - max(2, rect.width // 8))
            flash_y = rect.top + int(rect.height * .52)
            pygame.draw.circle(self.render_surface, (255, 226, 93), (flash_x, flash_y), max(2, rect.width // 9))
            pygame.draw.circle(self.render_surface, (255, 108, 39), (flash_x, flash_y), max(1, rect.width // 15))

        # World-space name/health/weapon plate.
        ratio = max(0, min(1, self.remote_health / 100))
        bw = max(24, min(58, rect.width + 8))
        bx = cx - bw // 2
        by = max(3, rect.top - 10)
        pygame.draw.rect(self.render_surface, (30, 8, 8), (bx, by, bw, 4))
        pygame.draw.rect(self.render_surface, (220, 48, 48), (bx, by, int(bw * ratio), 4))
        if protected:
            pygame.draw.rect(self.render_surface, (246, 210, 96), (bx - 1, by - 1, bw + 2, 6), 1)
        label_font = pygame.font.Font(None, 10)
        name = label_font.render(self.remote_name[:16], True, (246, 236, 210))
        self.render_surface.blit(name, name.get_rect(midbottom=(cx, by - 1)))
        weapon_name = WEAPON_DEFINITIONS.get(str(r.get("weapon", "pistol")), {}).get("name", "")
        if weapon_name:
            weapon = pygame.font.Font(None, 8).render(str(weapon_name), True, (224, 200, 139))
            self.render_surface.blit(weapon, weapon.get_rect(midtop=(cx, by + 5)))

    def draw(self, target):
        self._render_world()
        self._render_remote()
        self._render_weapon()
        self._render_crosshair()
        target.blit(pygame.transform.scale(self.render_surface, target.get_size()), (0, 0))
        self._draw_pvp_hud(target)

    def _draw_pvp_hud(self, target):
        w, h = target.get_size()
        panel_h = 108
        panel = pygame.Surface((w, panel_h), pygame.SRCALPHA)
        panel.fill((8, 9, 12, 176))
        target.blit(panel, (0, 0))

        small = self._font(18, False)
        tiny = self._font(15, False)
        score_font = self._dmh_font("numbers", 38, True)
        title_font = self._dmh_font("ui", 20, True)

        # Same authored health/ammo assets as campaign DMH.
        self._draw_meter_widget(
            target, 16, 18,
            Path("dead_mans_hand") / "ui" / "health_bar_bg.png",
            Path("dead_mans_hand") / "ui" / "health_bar_fill.png",
            Path("dead_mans_hand") / "ui" / "health_label.png",
            self.health / 100.0, "HEALTH", (188, 44, 44),
            widget_size=(332, 56), fill_insets=(20, 22, 20, 22),
        )
        if self.spawn_protection_timer > 0.0 and not self.game_over:
            protection = tiny.render(
                f"SPAWN PROTECTED {self.spawn_protection_timer:0.1f}s", True, (246, 210, 96)
            )
            target.blit(protection, (20, 78))

        ammo_ratio = self.current_ammo() / max(1, int(self.current_weapon_config()["mag_size"]))
        self._draw_meter_widget(
            target, w - 392, 48,
            Path("dead_mans_hand") / "ui" / "ammo_bar_bg.png",
            Path("dead_mans_hand") / "ui" / "ammo_bar_fill.png",
            Path("dead_mans_hand") / "ui" / "ammo_label.png",
            ammo_ratio, "AMMO", (215, 177, 55),
            widget_size=(376, 46), fill_insets=(20, 22, 20, 22),
        )

        # Scoreboard and player names.
        score = score_font.render(f"{self.local_score}  -  {self.remote_score}", True, (246, 236, 210))
        target.blit(score, score.get_rect(center=(w // 2, 32)))
        left_name = title_font.render(self.local_name[:18], True, (238, 211, 132))
        right_name = title_font.render(self.remote_name[:18], True, (220, 93, 84))
        target.blit(left_name, left_name.get_rect(topright=(w // 2 - 76, 56)))
        target.blit(right_name, right_name.get_rect(topleft=(w // 2 + 76, 56)))
        mode = tiny.render(f"FIRST TO {FIRST_TO_KILLS}  •  O.K. CORRAL", True, (201, 191, 171))
        target.blit(mode, mode.get_rect(center=(w // 2, 88)))

        self._draw_weapon_sidebar(target)

        # Kill feed uses authoritative kill events, not local guesses.
        feed_y = 116
        for text, life in self.kill_feed:
            alpha = 255 if life > .5 else int(255 * max(0.0, life / .5))
            image = tiny.render(text, True, (244, 229, 197))
            bg = pygame.Surface((image.get_width() + 16, image.get_height() + 8), pygame.SRCALPHA)
            bg.fill((5, 6, 9, min(185, alpha)))
            rect = bg.get_rect(topright=(w - 16, feed_y))
            target.blit(bg, rect)
            target.blit(image, image.get_rect(center=rect.center))
            feed_y += rect.height + 4

        controls = small.render(
            "WASD move   SPACE jump   Mouse aim   LMB fire   RMB aim   1-4 weapons   R reload   ESC leave",
            True, (225, 225, 225),
        )
        controls_bg = pygame.Surface((controls.get_width() + 26, 34), pygame.SRCALPHA)
        controls_bg.fill((8, 9, 12, 165))
        controls_rect = controls_bg.get_rect(midbottom=(w // 2, h - 12))
        target.blit(controls_bg, controls_rect)
        target.blit(controls, controls.get_rect(center=controls_rect.center))

        # Hit confirmation: white X for a hit, red/larger X for a kill.
        if self.hit_marker_timer > 0.0 or self.kill_marker_timer > 0.0:
            cx, cy = w // 2, h // 2
            killed = self.kill_marker_timer > 0.0
            color = (235, 64, 55) if killed else (245, 239, 220)
            radius = 14 if killed else 10
            thickness = 3 if killed else 2
            pygame.draw.line(target, color, (cx - radius, cy - radius), (cx - 4, cy - 4), thickness)
            pygame.draw.line(target, color, (cx + 4, cy + 4), (cx + radius, cy + radius), thickness)
            pygame.draw.line(target, color, (cx + radius, cy - radius), (cx + 4, cy - 4), thickness)
            pygame.draw.line(target, color, (cx - 4, cy + 4), (cx - radius, cy + radius), thickness)

        if self.damage_flash_timer > 0:
            alpha = int(115 * min(1.0, self.damage_flash_timer / 0.22))
            flash = pygame.Surface(target.get_size(), pygame.SRCALPHA)
            flash.fill((190, 20, 20, alpha))
            target.blit(flash, (0, 0))

        if self.respawn_text:
            msg = self._dmh_font("ui", 42, True).render(self.respawn_text, True, (245, 210, 110))
            target.blit(msg, msg.get_rect(center=(w // 2, h // 2)))
        if self.match_over:
            veil = pygame.Surface((w, h), pygame.SRCALPHA)
            veil.fill((0, 0, 0, 155))
            target.blit(veil, (0, 0))
            msg = self._dmh_font("ui", 50, True).render(self.winner_text, True, (245, 220, 130))
            target.blit(msg, msg.get_rect(center=(w // 2, h // 2)))
            sub = self._font(24, False).render("ESC to return to Multiplayer", True, (245, 235, 215))
            target.blit(sub, sub.get_rect(center=(w // 2, h // 2 + 56)))


class DeadMansHandPvPMode:
    """Lobby + 1v1 network coordinator embedded in multiplayer/main.py."""
    def __init__(self, name, relay_address, sound=None):
        self.name = (name or "Player")[:24]
        self.relay_address = relay_address or "tcp://yamanote.proxy.rlwy.net:40274"
        self.code = ""
        self.focus = "code"
        self.peer = None
        self.hosting = False
        self.connected = False
        self.status = "Host a duel or enter your friend's room code."
        self.game = None
        self.remote_name = "Opponent"
        self.remote_pose = None
        self.authority = {
            0: {"health": 100, "score": 0, "dead_until": 0.0, "protected_until": 0.0},
            1: {"health": 100, "score": 0, "dead_until": 0.0, "protected_until": 0.0},
        }
        self.event_seq = 0
        self.event_log = []
        self.last_guest_event_seq = 0
        self.last_sync = 0.0
        self.closed = False
        self.sound = sound or (lambda _key: None)
        self.font = pygame.font.Font(None, 34)
        self.small = pygame.font.Font(None, 25)
        self.title = pygame.font.Font(None, 60)
        self.relay_rect = pygame.Rect(325, 330, 716, 52)
        self.code_rect = pygame.Rect(483, 420, 400, 52)
        self.host_rect = pygame.Rect(350, 510, 300, 58)
        self.join_rect = pygame.Rect(716, 510, 300, 58)
        self.back_rect = pygame.Rect(24, 22, 180, 46)

    def close(self):
        if self.peer: self.peer.close()
        self.peer = None
        if self.game: self.game.release_mouse()
        self.closed = True

    def _start(self, hosting):
        if self.peer:
            self.peer.close()
        self.hosting = bool(hosting)
        self.connected = False
        self.remote_pose = None
        self.remote_name = "Opponent"
        self.authority = {
            0: {"health": 100, "score": 0, "dead_until": 0.0, "protected_until": 0.0},
            1: {"health": 100, "score": 0, "dead_until": 0.0, "protected_until": 0.0},
        }
        self.event_seq = 0
        self.event_log = []
        self.last_guest_event_seq = 0
        self.game = PvPGame(0 if self.hosting else 1)
        self.game.local_name = self.name
        self.peer = RelayPeer(self.hosting, self.relay_address, self.name, self.code, version=1)
        self.status = "Creating duel room…" if self.hosting else "Joining duel room…"
        self.last_sync = 0.0
        pygame.key.stop_text_input()

    def _play_sound_events(self):
        if not self.game:
            return
        for event in self.game.pop_sound_events():
            self.sound(event)

    def _record_event(self, kind, **payload):
        self.event_seq += 1
        event = {"seq": self.event_seq, "kind": str(kind)}
        event.update(payload)
        self.event_log.append(event)
        del self.event_log[:-12]
        return event

    @staticmethod
    def _weapon_name(weapon):
        return str(WEAPON_DEFINITIONS.get(str(weapon), {}).get("name", str(weapon).title()))

    def _side_name(self, side):
        side = int(side)
        if self.hosting:
            return self.name if side == 0 else self.remote_name
        return self.remote_name if side == 0 else self.name

    def _kill_feed_text(self, shooter_side, target_side, weapon):
        return f"{self._side_name(shooter_side)}  [{self._weapon_name(weapon)}]  {self._side_name(target_side)}"

    def _host_feedback_for_hit(self, shooter_side, target_side, weapon, killed):
        if shooter_side == 0:
            self.sound("enemy_down" if killed else "enemy_hit")
            self.game.show_hit_marker(killed)
        if target_side == 0:
            self.sound("player_down" if killed else "player_hit")
            self.game.damage_flash_timer = .22
        if killed:
            self.game.add_kill_feed(self._kill_feed_text(shooter_side, target_side, weapon))

    def _guest_process_events(self, events):
        if not isinstance(events, list):
            return
        for event in events:
            try:
                seq = int(event.get("seq", 0))
            except (TypeError, ValueError):
                continue
            if seq <= self.last_guest_event_seq:
                continue
            self.last_guest_event_seq = seq
            kind = event.get("kind")
            if kind == "shot":
                side = int(event.get("side", -1))
                weapon = str(event.get("weapon", "pistol"))
                if side == 0:
                    self.sound(f"{weapon}_shot")
                    self.game.notify_remote_shot(weapon)
            elif kind == "hit":
                shooter = int(event.get("shooter", -1))
                target = int(event.get("target", -1))
                weapon = str(event.get("weapon", "pistol"))
                killed = bool(event.get("killed"))
                if shooter == 1:
                    self.sound("enemy_down" if killed else "enemy_hit")
                    self.game.show_hit_marker(killed)
                if target == 1:
                    self.sound("player_down" if killed else "player_hit")
                    self.game.damage_flash_timer = .22
                if killed:
                    self.game.add_kill_feed(self._kill_feed_text(shooter, target, weapon))

    def _host_state(self):
        now = time.monotonic()
        local = self.game.local_pose()
        remote = dict(self.remote_pose or SPAWN_STATE[1])
        respawned = {0: False, 1: False}

        for side, pose in ((0, local), (1, remote)):
            a = self.authority[side]
            if (
                a["health"] <= 0
                and a["dead_until"]
                and now >= a["dead_until"]
                and max(self.authority[0]["score"], self.authority[1]["score"]) < FIRST_TO_KILLS
            ):
                a["health"] = 100
                a["dead_until"] = 0.0
                a["protected_until"] = now + SPAWN_PROTECTION_SECONDS
                x, y, angle = SPAWNS[side]
                pose.update({"x": x, "y": y, "angle": angle, "z": 0.0, "dead": False})
                respawned[side] = True
                if side == 0:
                    self.game.respawn(0)
                    local = self.game.local_pose()
                    pose = local
                else:
                    self.remote_pose = dict(pose)
                    remote = pose

            pose["health"] = a["health"]
            pose["score"] = a["score"]
            pose["dead"] = a["health"] <= 0
            pose["respawn"] = bool(respawned[side])
            pose["respawn_in"] = max(0.0, a["dead_until"] - now) if pose["dead"] and a["dead_until"] else 0.0
            pose["protection_in"] = max(0.0, a["protected_until"] - now)
            pose["protected"] = pose["protection_in"] > 0.0

        return {
            "type": "state",
            "host": local,
            "guest": remote,
            "host_name": self.name,
            "guest_name": self.remote_name,
            "first_to": FIRST_TO_KILLS,
            "events": self.event_log[-12:],
            "match_over": max(self.authority[0]["score"], self.authority[1]["score"]) >= FIRST_TO_KILLS,
        }

    def _apply_hit(self, shooter_side, shot):
        target_side = 1 - shooter_side
        now = time.monotonic()
        shooter_auth = self.authority[shooter_side]
        target_auth = self.authority[target_side]
        if shooter_auth["health"] <= 0 or target_auth["health"] <= 0:
            return False
        if now < float(target_auth.get("protected_until", 0.0)):
            return False

        shooter = self.game.local_pose() if shooter_side == 0 else dict(self.remote_pose or {})
        # Use the firing event's origin/angle so host validation is not shifted by the next pose packet.
        shooter.update({k: shot[k] for k in ("x", "y", "z", "angle", "weapon") if k in shot})
        target = dict(self.remote_pose or {}) if target_side == 1 else self.game.local_pose()
        target["dead"] = target_auth["health"] <= 0
        if not _shot_hits(self.game.level, shooter, target):
            return False

        weapon = str(shot.get("weapon", "pistol"))
        damage = int(PVP_DAMAGE.get(weapon, 30))
        target_auth["health"] = max(0, target_auth["health"] - damage)
        killed = target_auth["health"] <= 0
        if killed:
            shooter_auth["score"] += 1
            target_auth["dead_until"] = now + RESPAWN_SECONDS
            target_auth["protected_until"] = 0.0

        if target_side == 0:
            self.game.health = target_auth["health"]
            if killed:
                self.game.game_over = True

        self._record_event(
            "hit",
            shooter=shooter_side,
            target=target_side,
            weapon=weapon,
            damage=damage,
            health=target_auth["health"],
            killed=killed,
        )
        self._host_feedback_for_hit(shooter_side, target_side, weapon, killed)
        return True

    def _process_network(self):
        if not self.peer:
            return
        while True:
            try:
                m = self.peer.inbox.get_nowait()
            except queue.Empty:
                break
            kind = m.get("type")
            if kind == "status":
                self.status = m.get("text", self.status)
                if self.hosting and self.peer.code:
                    self.code = self.peer.code
            elif kind == "hello":
                self.connected = True
                self.remote_name = str(m.get("name", "Opponent"))[:24]
                self.status = f"Duel connected: {self.name} vs {self.remote_name}"
                self.game.local_name = self.name
                self.game.remote_name = self.remote_name
                self.game.spawn_protection_timer = SPAWN_PROTECTION_SECONDS
                if self.hosting:
                    now = time.monotonic()
                    self.authority[0]["protected_until"] = now + SPAWN_PROTECTION_SECONDS
                    self.authority[1]["protected_until"] = now + SPAWN_PROTECTION_SECONDS
                self.game.capture_mouse()
            elif kind == "disconnected":
                self.status = m.get("text", "Disconnected")
                self.connected = False
                if self.game:
                    self.game.release_mouse()
            elif kind == "action" and self.hosting:
                action = m.get("action")
                if action == "pose":
                    pose = dict(m.get("pose") or {})
                    pose.pop("health", None)
                    pose.pop("score", None)
                    pose.pop("protected", None)
                    pose.pop("protection_in", None)
                    self.remote_pose = pose
                elif action == "shot":
                    shot = dict(m.get("shot") or {})
                    weapon = str(shot.get("weapon", "pistol"))
                    self._record_event("shot", side=1, weapon=weapon)
                    self.sound(f"{weapon}_shot")
                    self.game.notify_remote_shot(weapon)
                    self._apply_hit(1, shot)
            elif kind == "state" and not self.hosting:
                host = dict(m.get("host") or {})
                guest = dict(m.get("guest") or {})
                self.remote_name = str(m.get("host_name", self.remote_name))[:24]
                self.game.local_name = self.name
                self.game.remote_name = self.remote_name
                self.remote_pose = host
                self.game.health = int(guest.get("health", self.game.health))
                self.game.local_score = int(guest.get("score", 0))
                self.game.remote_score = int(host.get("score", 0))
                self.game.spawn_protection_timer = max(0.0, float(guest.get("protection_in", 0.0)))
                self.game.set_remote(host, self.remote_name)
                self._guest_process_events(m.get("events", []))

                if guest.get("respawn"):
                    self.game.respawn(1)
                    self.game.spawn_protection_timer = max(
                        self.game.spawn_protection_timer,
                        float(guest.get("protection_in", SPAWN_PROTECTION_SECONDS)),
                    )
                    self.game.respawn_text = ""
                elif guest.get("dead"):
                    self.game.game_over = True
                    remaining = float(guest.get("respawn_in", 0.0))
                    self.game.respawn_text = (
                        f"Respawning in {max(1, math.ceil(remaining))}"
                        if remaining > 0
                        else "Respawning…"
                    )
                else:
                    self.game.game_over = False
                    self.game.respawn_text = ""

                self.game.match_over = bool(m.get("match_over"))
                if self.game.match_over:
                    self.game.winner_text = (
                        "YOU WIN"
                        if self.game.local_score > self.game.remote_score
                        else f"{self.remote_name.upper()} WINS"
                    )

    def update(self, dt):
        self._process_network()
        if not self.game or not self.connected:
            return
        self.game.update(dt, pygame.key.get_pressed())
        self._play_sound_events()
        now = time.monotonic()

        if self.hosting:
            for shot in self.game.pop_shots():
                weapon = str(shot.get("weapon", "pistol"))
                self._record_event("shot", side=0, weapon=weapon)
                self._apply_hit(0, shot)

            self.authority[0]["health"] = self.game.health
            self.game.local_score = self.authority[0]["score"]
            self.game.remote_score = self.authority[1]["score"]
            self.game.spawn_protection_timer = max(
                0.0, self.authority[0]["protected_until"] - now
            )

            if self.authority[0]["health"] <= 0 and self.authority[0]["dead_until"]:
                remaining = max(0.0, self.authority[0]["dead_until"] - now)
                self.game.respawn_text = (
                    f"Respawning in {max(1, math.ceil(remaining))}"
                    if remaining > 0
                    else "Respawning…"
                )
            else:
                self.game.respawn_text = ""

            if self.remote_pose:
                rp = dict(self.remote_pose)
                rp["health"] = self.authority[1]["health"]
                rp["dead"] = self.authority[1]["health"] <= 0
                rp["protection_in"] = max(
                    0.0, self.authority[1]["protected_until"] - now
                )
                rp["protected"] = rp["protection_in"] > 0.0
                self.game.set_remote(rp, self.remote_name)

            if now - self.last_sync >= SYNC_INTERVAL:
                self.peer.send(self._host_state())
                self.last_sync = now

            over = max(
                self.authority[0]["score"], self.authority[1]["score"]
            ) >= FIRST_TO_KILLS
            self.game.match_over = over
            if over:
                self.game.winner_text = (
                    "YOU WIN"
                    if self.authority[0]["score"] > self.authority[1]["score"]
                    else f"{self.remote_name.upper()} WINS"
                )
        else:
            for shot in self.game.pop_shots():
                self.peer.send({"type": "action", "action": "shot", "shot": shot})
            if now - self.last_sync >= SYNC_INTERVAL:
                self.peer.send({
                    "type": "action",
                    "action": "pose",
                    "pose": self.game.local_pose(),
                })
                self.last_sync = now

    def handle_event(self, event, mouse):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close(); return
        if self.game and self.connected:
            if event.type == pygame.MOUSEMOTION: self.game.handle_mouse_motion(event.rel[0])
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: self.game.set_trigger_held(True); self.game.fire()
                elif event.button == 3: self.game.set_aiming(True)
                elif event.button == 4: self.game.cycle_weapon(-1)
                elif event.button == 5: self.game.cycle_weapon(1)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1: self.game.set_trigger_held(False)
                elif event.button == 3: self.game.set_aiming(False)
            elif event.type == pygame.MOUSEWHEEL: self.game.cycle_weapon(1 if event.y < 0 else -1)
            elif event.type == pygame.KEYDOWN:
                if pygame.K_1 <= event.key <= pygame.K_4: self.game.switch_weapon_by_slot(event.key - pygame.K_0)
                elif event.key == pygame.K_r: self.game.start_reload()
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_rect.collidepoint(mouse): self.close(); return
            if self.relay_rect.collidepoint(mouse): self.focus = "relay"; pygame.key.start_text_input()
            elif self.code_rect.collidepoint(mouse): self.focus = "code"; pygame.key.start_text_input()
            elif self.host_rect.collidepoint(mouse): self._start(True)
            elif self.join_rect.collidepoint(mouse) and self.code.strip(): self._start(False)
        if event.type == pygame.TEXTINPUT:
            if self.focus == "relay": self.relay_address = (self.relay_address + event.text)[:128]
            else: self.code = (self.code + event.text.upper())[:8]
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
            if self.focus == "relay": self.relay_address = self.relay_address[:-1]
            else: self.code = self.code[:-1]

    def draw(self, canvas, mouse):
        if self.game and self.connected:
            self.game.draw(canvas); return
        canvas.fill((17, 23, 27))
        title = self.title.render("DEAD MAN'S HAND • PvP", True, (224, 56, 48)); canvas.blit(title, title.get_rect(center=(683, 135)))
        sub = self.small.render("1v1 prototype • First to 5 kills • Host-authoritative hit confirmation", True, (225, 215, 190)); canvas.blit(sub, sub.get_rect(center=(683, 190)))
        canvas.blit(self.small.render("Relay address", True, (235, 225, 200)), (325, 297))
        canvas.blit(self.small.render("Room code", True, (235, 225, 200)), (483, 388))
        for rect, text, active in ((self.relay_rect, self.relay_address, self.focus == "relay"), (self.code_rect, self.code, self.focus == "code")):
            pygame.draw.rect(canvas, (31, 65, 57), rect); pygame.draw.rect(canvas, (221, 183, 91) if active else (103, 142, 126), rect, 2)
            clip = canvas.get_clip(); canvas.set_clip(rect.inflate(-10, -4)); canvas.blit(self.font.render(text, True, (248, 240, 216)), (rect.x + 12, rect.y + 12)); canvas.set_clip(clip)
        for rect, label in ((self.host_rect, "Host Duel"), (self.join_rect, "Join Duel"), (self.back_rect, "Back")):
            pygame.draw.rect(canvas, (104, 65, 39) if rect.collidepoint(mouse) else (82, 50, 32), rect, border_radius=7); pygame.draw.rect(canvas, (184, 139, 82), rect, 2, border_radius=7)
            img = self.font.render(label, True, (248, 235, 205)); canvas.blit(img, img.get_rect(center=rect.center))
        status = self.small.render(self.status, True, (235, 205, 130)); canvas.blit(status, status.get_rect(center=(683, 625)))
        if self.hosting and self.peer and self.peer.code:
            code = self.title.render(self.peer.code, True, (245, 230, 130)); canvas.blit(code, code.get_rect(center=(683, 690)))


SPAWN_STATE = {
    0: {"x": SPAWNS[0][0], "y": SPAWNS[0][1], "angle": SPAWNS[0][2], "z": 0.0, "weapon": "pistol", "dead": False},
    1: {"x": SPAWNS[1][0], "y": SPAWNS[1][1], "angle": SPAWNS[1][2], "z": 0.0, "weapon": "pistol", "dead": False},
}
