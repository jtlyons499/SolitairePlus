"""Pygame raycaster prototype for Dead Man's Hand.

The renderer intentionally runs at a low internal resolution and is then scaled
onto Simple Solitaire's existing 1366x768 game surface. No OpenGL dependency is
needed: this is a classic CPU raycaster with billboard card enemies.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import random

import pygame

from dead_mans_hand import (
    FOV,
    GAME_TITLE,
    LEVELS,
    MAX_RAY_DEPTH,
    RENDER_HEIGHT,
    RENDER_WIDTH,
    normalize_angle,
    wall_at,
)


@dataclass
class CardEnemy:
    card_id: str
    x: float
    y: float
    hp: float
    max_hp: float
    speed: float
    damage: int
    attack_range: float
    score_value: int
    radius: float = 0.22
    alive: bool = True
    attack_cooldown: float = 0.0
    hit_flash: float = 0.0


@dataclass
class WeaponPickup:
    weapon_id: str
    x: float
    y: float
    phase: float = 0.0
    acquired: bool = False


ENEMY_ARCHETYPES = {
    "pip": {"hp": 70.0, "speed": 0.82, "damage": 8, "attack_range": 0.68, "score": 100},
    "jack": {"hp": 85.0, "speed": 1.18, "damage": 10, "attack_range": 0.70, "score": 175},
    "queen": {"hp": 120.0, "speed": 0.76, "damage": 13, "attack_range": 0.72, "score": 250},
    "king": {"hp": 180.0, "speed": 0.58, "damage": 18, "attack_range": 0.78, "score": 400},
}

WALL_COLORS = {
    "1": (122, 37, 45),
    "2": (56, 88, 112),
    "3": (119, 91, 52),
}

from dead_mans_hand_weapons import DEFAULT_WEAPON_PICKUPS, WEAPON_DEFINITIONS, weapon_for_slot

ADS_TRANSITION_SPEED = 9.5
PICKUP_RADIUS = 0.58
PICKUP_SPIN_SPEED = 1.25
PICKUP_BOB_SPEED = 2.25
PICKUP_BOB_HEIGHT = 7



class DeadMansHandGame:
    PLAYER_RADIUS = 0.20
    MOVE_SPEED = 2.55
    STRAFE_SPEED = 2.30
    TURN_SPEED = 1.75
    MOUSE_SENSITIVITY = 0.00265
    SHOT_COOLDOWN = 0.245
    SHOT_DAMAGE = 48.0
    ENEMY_WAKE_DISTANCE = 10.5

    def __init__(self, asset_root="assets"):
        self.asset_root = Path(asset_root)
        self.render_surface = pygame.Surface((RENDER_WIDTH, RENDER_HEIGHT)).convert()
        self._font_cache = {}
        self._dmh_font_cache = {}
        self._card_surfaces = {}
        self._placeholder_cards = {}
        self._weapon_surfaces = {}
        self._ui_surfaces = {}
        self._z_buffer = [MAX_RAY_DEPTH] * RENDER_WIDTH
        self.rng = random.Random()

        self.level_index = 0
        self.level = LEVELS[0]
        self.player_x = 0.0
        self.player_y = 0.0
        self.player_angle = 0.0
        self.health = 100
        self.score = 0
        self.enemies = []
        self.shot_timer = 0.0
        self.muzzle_flash_timer = 0.0
        self.damage_flash_timer = 0.0
        self.level_clear_timer = 0.0
        self.level_banner_timer = 0.0
        self.game_over = False
        self.prototype_complete = False
        self.elapsed = 0.0
        self._pending_sound_events = []
        self._mouse_captured = False

        # Multi-weapon state. ADS is hold-to-aim (RMB); every weapon owns its
        # own magazine, animation timing, fire behavior, and viewmodel config.
        self.aiming_down_sights = False
        self.ads_blend = 0.0
        self.walk_phase = 0.0
        self.is_moving = False
        self.current_weapon_id = "pistol"
        self.owned_weapons = {"pistol"}
        self.weapon_ammo = {weapon_id: int(cfg["mag_size"]) for weapon_id, cfg in WEAPON_DEFINITIONS.items()}
        self.reload_timer = 0.0
        self.reloading = False
        self.bolt_timer = 0.0
        self.trigger_held = False
        self.pickups = []
        self.start_run()

    # ------------------------------------------------------------------
    # Run / level lifecycle
    # ------------------------------------------------------------------
    def start_run(self):
        self.score = 0
        self.total_kills = 0
        self.health = 100
        self.game_over = False
        self.prototype_complete = False
        self.level_index = 0
        self.aiming_down_sights = False
        self.ads_blend = 0.0
        self.walk_phase = 0.0
        self.is_moving = False
        self.current_weapon_id = "pistol"
        self.owned_weapons = {"pistol"}
        self.weapon_ammo = {weapon_id: int(cfg["mag_size"]) for weapon_id, cfg in WEAPON_DEFINITIONS.items()}
        self.reload_timer = 0.0
        self.reloading = False
        self.bolt_timer = 0.0
        self.trigger_held = False
        self._load_level(0, preserve_health=False)

    def current_weapon_config(self):
        return WEAPON_DEFINITIONS[self.current_weapon_id]

    def current_ammo(self):
        return int(self.weapon_ammo.get(self.current_weapon_id, 0))

    def switch_weapon(self, weapon_id):
        weapon_id = str(weapon_id)
        if self.bolt_timer > 0.0 and weapon_id != self.current_weapon_id:
            return False
        if weapon_id not in self.owned_weapons or weapon_id not in WEAPON_DEFINITIONS:
            return False
        if weapon_id == self.current_weapon_id:
            return True
        self.current_weapon_id = weapon_id
        self.reloading = False
        self.reload_timer = 0.0
        self.bolt_timer = 0.0
        self.aiming_down_sights = False
        self.trigger_held = False
        self.muzzle_flash_timer = 0.0
        return True

    def switch_weapon_by_slot(self, slot):
        weapon_id = weapon_for_slot(slot)
        return self.switch_weapon(weapon_id) if weapon_id else False

    def cycle_weapon(self, direction=1):
        owned = sorted(
            (wid for wid in self.owned_weapons if wid in WEAPON_DEFINITIONS),
            key=lambda wid: int(WEAPON_DEFINITIONS[wid]["slot"]),
        )
        if len(owned) <= 1:
            return False
        try:
            index = owned.index(self.current_weapon_id)
        except ValueError:
            index = 0
        return self.switch_weapon(owned[(index + (1 if direction >= 0 else -1)) % len(owned)])

    def set_trigger_held(self, active):
        self.trigger_held = bool(active)

    def _enemy_archetype(self, card_id):
        rank = str(card_id or "9")[:-1].upper()
        if rank == "K":
            return ENEMY_ARCHETYPES["king"]
        if rank == "Q":
            return ENEMY_ARCHETYPES["queen"]
        if rank == "J":
            return ENEMY_ARCHETYPES["jack"]
        return ENEMY_ARCHETYPES["pip"]

    def _load_level(self, index, preserve_health=True):
        self.level_index = int(index)
        self.level = LEVELS[self.level_index]
        px, py, angle = self.level["player"]
        self.player_x = float(px)
        self.player_y = float(py)
        self.player_angle = float(angle)
        if not preserve_health:
            self.health = 100
        else:
            # Clearing a room gives a small recovery without trivializing damage.
            self.health = min(100, self.health + 22)
        self.enemies = []
        self.pickups = []
        for weapon_id, wx, wy in DEFAULT_WEAPON_PICKUPS.get(self.level_index, ()):
            if weapon_id not in self.owned_weapons:
                self.pickups.append(WeaponPickup(str(weapon_id), float(wx), float(wy), phase=self.rng.random() * math.tau))
        for card_id, ex, ey in self.level.get("enemies", ()):
            cfg = self._enemy_archetype(card_id)
            hp = cfg["hp"]
            self.enemies.append(
                CardEnemy(
                    card_id=str(card_id),
                    x=float(ex),
                    y=float(ey),
                    hp=hp,
                    max_hp=hp,
                    speed=cfg["speed"] * (1.0 + self.level_index * 0.075),
                    damage=cfg["damage"] + self.level_index * 2,
                    attack_range=cfg["attack_range"],
                    score_value=cfg["score"] + self.level_index * 25,
                )
            )
        self.shot_timer = 0.0
        self.muzzle_flash_timer = 0.0
        self.damage_flash_timer = 0.0
        self.level_clear_timer = 0.0
        self.level_banner_timer = 2.0

    def capture_mouse(self):
        if self._mouse_captured:
            return
        try:
            pygame.event.set_grab(True)
            pygame.mouse.set_visible(False)
            pygame.mouse.get_rel()
        except pygame.error:
            pass
        self._mouse_captured = True

    def release_mouse(self):
        try:
            pygame.event.set_grab(False)
            pygame.mouse.set_visible(True)
        except pygame.error:
            pass
        self._mouse_captured = False
        self.aiming_down_sights = False
        self.trigger_held = False

    # ------------------------------------------------------------------
    # Input / simulation
    # ------------------------------------------------------------------
    def handle_mouse_motion(self, dx):
        if self.game_over or self.prototype_complete:
            return
        sensitivity = self.MOUSE_SENSITIVITY * (0.72 if self.ads_blend > 0.5 else 1.0)
        self.player_angle = normalize_angle(
            self.player_angle + float(dx) * sensitivity
        )

    def set_aiming(self, active):
        """Hold RMB to aim down sights; each weapon supplies its own zoom."""
        if self.game_over or self.prototype_complete or self.reloading:
            self.aiming_down_sights = False
            return
        self.aiming_down_sights = bool(active)

    def start_reload(self):
        """Reload the equipped weapon's current magazine."""
        if self.game_over or self.prototype_complete or self.bolt_timer > 0.0:
            return False
        cfg = self.current_weapon_config()
        if self.reloading or self.current_ammo() >= int(cfg["mag_size"]):
            return False
        self.reloading = True
        self.reload_timer = float(cfg["reload_seconds"])
        self.aiming_down_sights = False
        self.trigger_held = False
        self._pending_sound_events.append(f"{self.current_weapon_id}_reload")
        return True

    def _collides_world(self, x, y, radius):
        probes = (
            (x - radius, y - radius),
            (x + radius, y - radius),
            (x - radius, y + radius),
            (x + radius, y + radius),
        )
        return any(wall_at(self.level, px, py) for px, py in probes)

    def _try_move(self, dx, dy):
        target_x = self.player_x + dx
        target_y = self.player_y + dy
        if not self._collides_world(target_x, self.player_y, self.PLAYER_RADIUS):
            self.player_x = target_x
        if not self._collides_world(self.player_x, target_y, self.PLAYER_RADIUS):
            self.player_y = target_y

    def _line_of_sight(self, x0, y0, x1, y1):
        dx = x1 - x0
        dy = y1 - y0
        distance = math.hypot(dx, dy)
        if distance <= 0.01:
            return True
        steps = max(1, int(distance / 0.075))
        for step in range(1, steps):
            t = step / steps
            if wall_at(self.level, x0 + dx * t, y0 + dy * t):
                return False
        return True

    def fire(self):
        cfg = self.current_weapon_config()
        if (
            self.game_over
            or self.prototype_complete
            or self.shot_timer > 0.0
            or self.reloading
            or self.bolt_timer > 0.0
        ):
            return False
        if self.current_ammo() <= 0:
            self.start_reload()
            return False

        self.weapon_ammo[self.current_weapon_id] = self.current_ammo() - 1
        self.shot_timer = float(cfg["fire_interval"])
        self.muzzle_flash_timer = 0.070 if cfg.get("automatic") else 0.095
        self._pending_sound_events.append(f"{self.current_weapon_id}_shot")
        bolt_seconds = float(cfg.get("bolt_seconds", 0.0))
        if bolt_seconds > 0.0:
            self.bolt_timer = bolt_seconds
            self._pending_sound_events.append(f"{self.current_weapon_id}_bolt")

        best = None
        best_distance = 1e9
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            dx = enemy.x - self.player_x
            dy = enemy.y - self.player_y
            distance = math.hypot(dx, dy)
            if distance <= 0.01:
                continue
            delta = normalize_angle(math.atan2(dy, dx) - self.player_angle)
            angular_radius = min(0.20, 0.28 / max(0.6, distance))
            if abs(delta) <= angular_radius and distance < best_distance:
                if self._line_of_sight(self.player_x, self.player_y, enemy.x, enemy.y):
                    best = enemy
                    best_distance = distance

        if best is not None:
            best.hp -= float(cfg["damage"])
            best.hit_flash = 0.12
            if best.hp <= 0:
                best.alive = False
                self.score += best.score_value
                self.total_kills += 1
                self._pending_sound_events.append("enemy_down")
            else:
                self._pending_sound_events.append("enemy_hit")
        return True

    def pop_sound_events(self):
        events = self._pending_sound_events[:]
        self._pending_sound_events.clear()
        return events

    def _move_enemy(self, enemy, dt):
        dx = self.player_x - enemy.x
        dy = self.player_y - enemy.y
        distance = math.hypot(dx, dy)
        if distance > self.ENEMY_WAKE_DISTANCE:
            return

        enemy.attack_cooldown = max(0.0, enemy.attack_cooldown - dt)
        if distance <= enemy.attack_range:
            if enemy.attack_cooldown <= 0.0:
                self.health = max(0, self.health - enemy.damage)
                self.damage_flash_timer = 0.22
                enemy.attack_cooldown = 0.72
                self._pending_sound_events.append("player_hit")
                if self.health <= 0:
                    self.game_over = True
                    self._pending_sound_events.append("player_down")
            return

        if distance <= 0.001:
            return
        ux = dx / distance
        uy = dy / distance
        step = enemy.speed * dt
        # Axis-separated collision lets cards slide around simple corners.
        nx = enemy.x + ux * step
        ny = enemy.y + uy * step
        if not self._collides_world(nx, enemy.y, enemy.radius):
            enemy.x = nx
        if not self._collides_world(enemy.x, ny, enemy.radius):
            enemy.y = ny

    def update(self, dt, keys):
        dt = max(0.0, min(0.05, float(dt)))
        self.elapsed += dt
        self.shot_timer = max(0.0, self.shot_timer - dt)
        self.muzzle_flash_timer = max(0.0, self.muzzle_flash_timer - dt)
        self.damage_flash_timer = max(0.0, self.damage_flash_timer - dt)
        self.level_banner_timer = max(0.0, self.level_banner_timer - dt)
        self.bolt_timer = max(0.0, self.bolt_timer - dt)
        for pickup in self.pickups:
            pickup.phase = (pickup.phase + PICKUP_SPIN_SPEED * dt) % math.tau

        # Smooth ADS transition and reload lifecycle.
        ads_target = 1.0 if (self.aiming_down_sights and not self.reloading) else 0.0
        ads_step = ADS_TRANSITION_SPEED * dt
        if self.ads_blend < ads_target:
            self.ads_blend = min(ads_target, self.ads_blend + ads_step)
        elif self.ads_blend > ads_target:
            self.ads_blend = max(ads_target, self.ads_blend - ads_step)

        if self.reloading:
            self.reload_timer = max(0.0, self.reload_timer - dt)
            if self.reload_timer <= 0.0:
                self.reloading = False
                cfg = self.current_weapon_config()
                self.weapon_ammo[self.current_weapon_id] = int(cfg["mag_size"])

        for enemy in self.enemies:
            enemy.hit_flash = max(0.0, enemy.hit_flash - dt)

        if self.game_over or self.prototype_complete:
            self.is_moving = False
            return

        turn = (1 if keys[pygame.K_RIGHT] else 0) - (1 if keys[pygame.K_LEFT] else 0)
        self.player_angle = normalize_angle(self.player_angle + turn * self.TURN_SPEED * dt)

        forward = (1 if keys[pygame.K_w] else 0) - (1 if keys[pygame.K_s] else 0)
        strafe = (1 if keys[pygame.K_d] else 0) - (1 if keys[pygame.K_a] else 0)
        # Arrow up/down are allowed as secondary movement controls; left/right turn.
        forward += (1 if keys[pygame.K_UP] else 0) - (1 if keys[pygame.K_DOWN] else 0)
        self.is_moving = bool(forward or strafe)
        if self.is_moving:
            length = max(1.0, math.hypot(forward, strafe))
            forward /= length
            strafe /= length
            ca = math.cos(self.player_angle)
            sa = math.sin(self.player_angle)
            # ADS trims movement slightly and damps viewmodel bob.
            move_scale = 0.82 if self.ads_blend > 0.5 else 1.0
            dx = (ca * forward * self.MOVE_SPEED * dt + (-sa) * strafe * self.STRAFE_SPEED * dt) * move_scale
            dy = (sa * forward * self.MOVE_SPEED * dt + ca * strafe * self.STRAFE_SPEED * dt) * move_scale
            self._try_move(dx, dy)
            self.walk_phase = (self.walk_phase + dt * 10.5) % math.tau

        # Pickups unlock a weapon for the rest of the run and equip it immediately.
        for pickup in self.pickups:
            if pickup.acquired:
                continue
            if math.hypot(pickup.x - self.player_x, pickup.y - self.player_y) <= PICKUP_RADIUS:
                pickup.acquired = True
                self.owned_weapons.add(pickup.weapon_id)
                cfg = WEAPON_DEFINITIONS[pickup.weapon_id]
                self.weapon_ammo[pickup.weapon_id] = int(cfg["mag_size"])
                self.switch_weapon(pickup.weapon_id)
                self._pending_sound_events.append("weapon_pickup")

        # Full-auto weapons keep firing while LMB is held. Semi-auto weapons only
        # fire from the initial mouse-down event in main.py.
        if self.trigger_held and self.current_weapon_config().get("automatic"):
            self.fire()

        for enemy in self.enemies:
            if enemy.alive:
                self._move_enemy(enemy, dt)
                if self.game_over:
                    break

        if not self.game_over and all(not enemy.alive for enemy in self.enemies):
            if self.level_clear_timer <= 0.0:
                self.level_clear_timer = 1.65
                self.score += 500 + self.level_index * 250
            else:
                self.level_clear_timer -= dt
                if self.level_clear_timer <= 0.0:
                    next_index = self.level_index + 1
                    if next_index < len(LEVELS):
                        self._load_level(next_index, preserve_health=True)
                    else:
                        self.prototype_complete = True
                        self.score += 2500

    # ------------------------------------------------------------------
    # Raycaster
    # ------------------------------------------------------------------
    def _cast_ray(self, ray_angle):
        # Grid DDA: visit only the map cells crossed by this ray instead of
        # advancing in tiny world-space increments. That keeps the CPU cost
        # low enough for the raycaster to coexist comfortably with Solitaire.
        ray_x = math.cos(ray_angle)
        ray_y = math.sin(ray_angle)
        map_x = int(self.player_x)
        map_y = int(self.player_y)
        rows = self.level["map"]
        map_w = len(rows[0])
        map_h = len(rows)

        delta_x = abs(1.0 / ray_x) if abs(ray_x) > 1e-9 else 1e30
        delta_y = abs(1.0 / ray_y) if abs(ray_y) > 1e-9 else 1e30

        if ray_x < 0:
            step_x = -1
            side_x = (self.player_x - map_x) * delta_x
        else:
            step_x = 1
            side_x = (map_x + 1.0 - self.player_x) * delta_x
        if ray_y < 0:
            step_y = -1
            side_y = (self.player_y - map_y) * delta_y
        else:
            step_y = 1
            side_y = (map_y + 1.0 - self.player_y) * delta_y

        material = "1"
        side = 0
        distance = MAX_RAY_DEPTH
        for _ in range(96):
            if side_x < side_y:
                map_x += step_x
                distance = side_x
                side_x += delta_x
                side = 0
            else:
                map_y += step_y
                distance = side_y
                side_y += delta_y
                side = 1

            if distance >= MAX_RAY_DEPTH:
                break
            if map_x < 0 or map_y < 0 or map_x >= map_w or map_y >= map_h:
                material = "1"
                break
            cell = rows[map_y][map_x]
            if cell != ".":
                material = cell
                break

        hit_x = self.player_x + ray_x * distance
        hit_y = self.player_y + ray_y * distance
        wall_coord = hit_y if side == 0 else hit_x
        frac = wall_coord - math.floor(wall_coord)
        edge = min(frac, 1.0 - frac)
        texture_phase = int(frac * 8.0) & 1
        # Slight orientation variation makes perpendicular walls easier to read.
        if side == 1:
            texture_phase ^= 1
        return min(distance, MAX_RAY_DEPTH), material, edge, texture_phase

    def _render_world(self):
        surface = self.render_surface
        # Sky/floor bands. The simple gradient keeps the prototype readable and
        # can later be replaced by authored textures without changing physics.
        horizon = RENDER_HEIGHT // 2
        for y in range(horizon):
            t = y / max(1, horizon)
            color = (int(28 + 28 * t), int(35 + 35 * t), int(50 + 42 * t))
            pygame.draw.line(surface, color, (0, y), (RENDER_WIDTH, y))
        for y in range(horizon, RENDER_HEIGHT):
            t = (y - horizon) / max(1, RENDER_HEIGHT - horizon)
            color = (int(42 - 22 * t), int(40 - 19 * t), int(37 - 18 * t))
            pygame.draw.line(surface, color, (0, y), (RENDER_WIDTH, y))

        for column in range(RENDER_WIDTH):
            camera = (column / max(1, RENDER_WIDTH - 1)) - 0.5
            current_fov = FOV + (float(self.current_weapon_config()["ads_fov"]) - FOV) * self.ads_blend
            ray_angle = self.player_angle + camera * current_fov
            raw_distance, material, edge, phase = self._cast_ray(ray_angle)
            corrected = max(0.055, raw_distance * math.cos(ray_angle - self.player_angle))
            self._z_buffer[column] = corrected
            zoom_scale = FOV / max(0.001, current_fov)
            wall_height = min(
                RENDER_HEIGHT * 3,
                int(((RENDER_HEIGHT * 0.92) / corrected) * zoom_scale),
            )
            y0 = horizon - wall_height // 2
            y1 = horizon + wall_height // 2
            base = WALL_COLORS.get(material, WALL_COLORS["1"])
            shade = max(0.22, min(1.0, 1.06 - corrected / 14.0))
            if phase:
                shade *= 0.86
            if edge < 0.035:
                shade *= 0.72
            color = tuple(max(0, min(255, int(channel * shade))) for channel in base)
            pygame.draw.line(surface, color, (column, y0), (column, y1))

    def _font(self, size, bold=False):
        key = (int(size), bool(bold))
        if key not in self._font_cache:
            self._font_cache[key] = pygame.font.Font(None, int(size))
            self._font_cache[key].set_bold(bool(bold))
        return self._font_cache[key]

    def _dmh_font(self, family, size, bold=False):
        family = str(family or "ui")
        filenames = ["Scary Halloween Font.ttf"]
        if family == "numbers":
            filenames.append("dead_mans_hand_numbers.ttf")
        else:
            filenames.append("dead_mans_hand_ui.ttf")
        key = (tuple(filenames), int(size), bool(bold))
        if key not in self._dmh_font_cache:
            font = None
            for filename in filenames:
                path = self.asset_root / "fonts" / filename
                try:
                    font = pygame.font.Font(str(path), int(size))
                    break
                except (pygame.error, OSError, FileNotFoundError):
                    continue
            if font is None:
                font = pygame.font.Font(None, int(size))
            font.set_bold(bool(bold))
            self._dmh_font_cache[key] = font
        return self._dmh_font_cache[key]

    def _load_ui_surface(self, relative_path):
        key = str(relative_path)
        if key in self._ui_surfaces:
            return self._ui_surfaces[key]
        path = self.asset_root / relative_path
        try:
            surface = pygame.image.load(str(path)).convert_alpha()
        except (pygame.error, OSError, FileNotFoundError):
            surface = None
        self._ui_surfaces[key] = surface
        return surface

    def _load_level_header_surface(self, level_number):
        return self._load_ui_surface(
            Path("dead_mans_hand") / "ui" / "levels" / f"level_{int(level_number):02d}.png"
        )

    def _fit_surface(self, surface, max_width, max_height, upscale=False):
        if surface is None:
            return None
        max_width = max(1, int(max_width))
        max_height = max(1, int(max_height))
        sw, sh = surface.get_size()
        if sw <= 0 or sh <= 0:
            return surface
        scale = min(max_width / sw, max_height / sh)
        if not upscale:
            scale = min(1.0, scale)
        if scale <= 0:
            return surface
        if abs(scale - 1.0) < 0.01:
            return surface
        new_size = (max(1, int(sw * scale)), max(1, int(sh * scale)))
        return pygame.transform.smoothscale(surface, new_size)

    def _blit_fill_bar(self, target, fill_surface, dest_rect, ratio):
        ratio = max(0.0, min(1.0, float(ratio)))
        if ratio <= 0.0:
            return
        fill_width = max(1, int(fill_surface.get_width() * ratio))
        source = fill_surface.subsurface((0, 0, fill_width, fill_surface.get_height()))
        target.blit(source, dest_rect.topleft)

    def _draw_meter_widget(
        self,
        target,
        x,
        y,
        bg_path,
        fill_path,
        label_path,
        ratio,
        fallback_label,
        fill_color,
        widget_size=(360, 72),
        fill_insets=(28, 30, 28, 12),
    ):
        rect = pygame.Rect(int(x), int(y), int(widget_size[0]), int(widget_size[1]))
        bg = self._fit_surface(self._load_ui_surface(bg_path), rect.width, rect.height, upscale=True)
        fill = self._load_ui_surface(fill_path)
        label = self._load_ui_surface(label_path)

        if bg is not None:
            target.blit(bg, bg.get_rect(center=rect.center))
        else:
            pygame.draw.rect(target, (10, 12, 18), rect, border_radius=10)
            pygame.draw.rect(target, (224, 194, 104), rect, 2, border_radius=10)

        left, top, right, bottom = (int(v) for v in fill_insets)
        inner = pygame.Rect(
            rect.left + left,
            rect.top + top,
            max(1, rect.width - left - right),
            max(1, rect.height - top - bottom),
        )
        old_clip = target.get_clip()
        target.set_clip(inner)
        if fill is not None:
            fill = pygame.transform.smoothscale(fill, (inner.width, inner.height))
            self._blit_fill_bar(target, fill, fill.get_rect(topleft=inner.topleft), ratio)
        else:
            pygame.draw.rect(target, (28, 32, 39), inner, border_radius=5)
            if ratio > 0.0:
                fill_w = max(1, int(inner.width * max(0.0, min(1.0, ratio))))
                pygame.draw.rect(target, fill_color, (inner.left, inner.top, fill_w, inner.height), border_radius=5)
        target.set_clip(old_clip)

        label_area = pygame.Rect(rect.left + 10, rect.top + 3, int(rect.width * 0.56), max(14, top - 4))
        if label is not None:
            label = self._fit_surface(label, label_area.width, label_area.height, upscale=False)
            target.blit(label, label.get_rect(midleft=(label_area.left, label_area.centery)))
        elif fallback_label:
            label_font = self._dmh_font("ui", max(18, int(rect.height * 0.30)), True)
            label_surface = label_font.render(fallback_label, True, (235, 224, 202))
            target.blit(label_surface, label_surface.get_rect(midleft=(label_area.left + 3, label_area.centery)))
        return rect

    def _draw_number_with_shadow(self, target, text, font, pos, color, shadow=(0, 0, 0), shadow_offset=(3, 3)):
        shadow_surface = font.render(str(text), True, shadow)
        target.blit(shadow_surface, (int(pos[0] + shadow_offset[0]), int(pos[1] + shadow_offset[1])))
        surface = font.render(str(text), True, color)
        target.blit(surface, pos)
        return surface.get_rect(topleft=pos)

    def _load_card_surface(self, card_id):
        if card_id in self._card_surfaces:
            return self._card_surfaces[card_id]
        path = self.asset_root / "cards" / "fronts" / f"{card_id}.png"
        try:
            surface = pygame.image.load(str(path)).convert_alpha()
        except (pygame.error, OSError):
            surface = pygame.Surface((70, 98), pygame.SRCALPHA)
            pygame.draw.rect(surface, (238, 235, 220), surface.get_rect(), border_radius=5)
            pygame.draw.rect(surface, (30, 30, 30), surface.get_rect(), 3, border_radius=5)
            text = self._font(30, True).render(str(card_id), True, (130, 20, 25))
            surface.blit(text, text.get_rect(center=surface.get_rect().center))
        self._card_surfaces[card_id] = surface
        return surface

    def _render_enemy(self, enemy):
        dx = enemy.x - self.player_x
        dy = enemy.y - self.player_y
        distance = math.hypot(dx, dy)
        if distance <= 0.04:
            return
        delta = normalize_angle(math.atan2(dy, dx) - self.player_angle)
        current_fov = FOV + (float(self.current_weapon_config()["ads_fov"]) - FOV) * self.ads_blend
        if abs(delta) > current_fov * 0.64:
            return
        corrected = max(0.05, distance * math.cos(delta))
        center_x = int((0.5 + delta / current_fov) * RENDER_WIDTH)
        zoom_scale = FOV / max(0.001, current_fov)
        height = max(
            8,
            min(
                RENDER_HEIGHT * 2,
                int(((RENDER_HEIGHT * 0.78) / corrected) * zoom_scale),
            ),
        )
        width = max(6, int(height * 0.70))
        bottom_y = int(RENDER_HEIGHT * 0.73 + height * 0.11)
        top_y = bottom_y - height
        left_x = center_x - width // 2

        card = self._load_card_surface(enemy.card_id)
        sprite = pygame.transform.scale(card, (width, height))
        if enemy.hit_flash > 0.0:
            flash = pygame.Surface(sprite.get_size(), pygame.SRCALPHA)
            flash.fill((255, 70, 70, 105))
            sprite.blit(flash, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # Draw one vertical sprite slice at a time so walls occlude the card.
        for sx in range(width):
            screen_x = left_x + sx
            if screen_x < 0 or screen_x >= RENDER_WIDTH:
                continue
            if corrected >= self._z_buffer[screen_x] + 0.06:
                continue
            source_x = min(sprite.get_width() - 1, sx)
            self.render_surface.blit(
                sprite,
                (screen_x, top_y),
                area=pygame.Rect(source_x, 0, 1, sprite.get_height()),
            )

        # Tiny health bar is only visible once a card has taken damage.
        if enemy.hp < enemy.max_hp and 0 <= center_x < RENDER_WIDTH and corrected < 7.5:
            bar_w = max(10, min(42, width))
            ratio = max(0.0, enemy.hp / enemy.max_hp)
            bx = center_x - bar_w // 2
            by = max(3, top_y - 5)
            pygame.draw.rect(self.render_surface, (32, 15, 15), (bx, by, bar_w, 3))
            pygame.draw.rect(self.render_surface, (210, 52, 52), (bx, by, int(bar_w * ratio), 3))

    def _load_pickup_surface(self, weapon_id):
        key = f"pickup::{weapon_id}"
        if key in self._ui_surfaces:
            return self._ui_surfaces[key]
        path = self.asset_root / "dead_mans_hand" / "pickups" / f"{weapon_id}.png"
        try:
            surface = pygame.image.load(str(path)).convert_alpha()
        except (pygame.error, OSError, FileNotFoundError):
            surface = pygame.Surface((128, 128), pygame.SRCALPHA)
            pygame.draw.rect(surface, (16, 17, 21, 220), (8, 8, 112, 112), border_radius=12)
            pygame.draw.rect(surface, (174, 39, 45), (8, 8, 112, 112), 4, border_radius=12)
            label = self._font(22, True).render(WEAPON_DEFINITIONS[weapon_id]["name"], True, (238, 226, 204))
            if label.get_width() > 108:
                label = pygame.transform.smoothscale(label, (108, max(1, int(label.get_height() * 108 / label.get_width()))))
            surface.blit(label, label.get_rect(center=(64, 64)))
        self._ui_surfaces[key] = surface
        return surface

    def _render_pickup(self, pickup):
        if pickup.acquired:
            return
        dx = pickup.x - self.player_x
        dy = pickup.y - self.player_y
        distance = math.hypot(dx, dy)
        if distance <= 0.04:
            return
        delta = normalize_angle(math.atan2(dy, dx) - self.player_angle)
        current_fov = FOV + (float(self.current_weapon_config()["ads_fov"]) - FOV) * self.ads_blend
        if abs(delta) > current_fov * 0.64:
            return
        corrected = max(0.05, distance * math.cos(delta))
        center_x = int((0.5 + delta / current_fov) * RENDER_WIDTH)
        zoom_scale = FOV / max(0.001, current_fov)
        base_height = max(12, min(100, int(((RENDER_HEIGHT * 0.35) / corrected) * zoom_scale)))
        spin_cos = math.cos(pickup.phase)
        width_factor = max(0.13, abs(spin_cos))
        bob = int(math.sin(pickup.phase * (PICKUP_BOB_SPEED / PICKUP_SPIN_SPEED)) * PICKUP_BOB_HEIGHT)

        source = self._load_pickup_surface(pickup.weapon_id)
        aspect = source.get_width() / max(1, source.get_height())
        full_width = max(8, int(base_height * aspect))
        draw_width = max(2, int(full_width * width_factor))
        sprite = pygame.transform.smoothscale(source, (draw_width, base_height))
        if spin_cos < 0:
            sprite = pygame.transform.flip(sprite, True, False)

        bottom_y = int(RENDER_HEIGHT * 0.72) + bob
        top_y = bottom_y - base_height
        left_x = center_x - draw_width // 2
        for sx in range(draw_width):
            screen_x = left_x + sx
            if screen_x < 0 or screen_x >= RENDER_WIDTH:
                continue
            if corrected >= self._z_buffer[screen_x] + 0.06:
                continue
            self.render_surface.blit(
                sprite,
                (screen_x, top_y),
                area=pygame.Rect(sx, 0, 1, sprite.get_height()),
            )

    def _load_weapon_icon(self, weapon_id):
        return self._load_ui_surface(Path("dead_mans_hand") / "ui" / "weapons" / f"{weapon_id}.png")

    def _draw_weapon_sidebar(self, target):
        owned = sorted(
            (wid for wid in self.owned_weapons if wid in WEAPON_DEFINITIONS),
            key=lambda wid: int(WEAPON_DEFINITIONS[wid]["slot"]),
        )
        if not owned:
            return
        box_size = 72
        gap = 8
        x = 10
        y = 138
        number_font = self._dmh_font("numbers", 23, True)
        for weapon_id in owned:
            cfg = WEAPON_DEFINITIONS[weapon_id]
            rect = pygame.Rect(x, y, box_size, box_size)
            selected = weapon_id == self.current_weapon_id
            pygame.draw.rect(target, (6, 7, 10, 220), rect, border_radius=4)
            pygame.draw.rect(target, (223, 44, 44) if selected else (55, 61, 70), rect, 4 if selected else 2, border_radius=4)
            icon = self._load_weapon_icon(weapon_id)
            if icon is not None:
                icon = self._fit_surface(icon, box_size - 14, box_size - 14, upscale=False)
                target.blit(icon, icon.get_rect(center=rect.center))
            else:
                short = cfg["name"]
                font = self._font(16, True)
                label = font.render(short, True, (220, 220, 220))
                if label.get_width() > box_size - 10:
                    label = pygame.transform.smoothscale(label, (box_size - 10, max(1, int(label.get_height() * (box_size - 10) / label.get_width()))))
                target.blit(label, label.get_rect(center=rect.center))
            key_text = number_font.render(str(cfg["slot"]), True, (235, 224, 202))
            key_bg = pygame.Surface((24, 24), pygame.SRCALPHA)
            key_bg.fill((6, 7, 10, 210))
            target.blit(key_bg, (rect.right - 24, rect.top))
            target.blit(key_text, key_text.get_rect(center=(rect.right - 12, rect.top + 12)))
            y += box_size + gap

    def _load_weapon_surface(self, relative_path, fallback_path=None):
        """Load/cache an authored viewmodel frame; return None when unavailable."""
        key = (str(relative_path), str(fallback_path or ""))
        if key in self._weapon_surfaces:
            return self._weapon_surfaces[key]

        candidates = [self.asset_root / relative_path]
        if fallback_path:
            candidates.append(self.asset_root / fallback_path)
        surface = None
        for path in candidates:
            if not path.exists():
                continue
            try:
                surface = pygame.image.load(str(path)).convert_alpha()
                break
            except (pygame.error, OSError):
                continue
        self._weapon_surfaces[key] = surface
        return surface

    @staticmethod
    def _lerp(a, b, t):
        return a + (b - a) * t

    def _weapon_frame_candidates(self, weapon_id, stem):
        folder = Path("dead_mans_hand") / "weapons" / weapon_id
        return (
            folder / f"{stem}.png",
            folder / f"{weapon_id}_{stem}.png",
        )

    def _load_first_weapon_frame(self, weapon_id, stems):
        for stem in stems:
            for path in self._weapon_frame_candidates(weapon_id, stem):
                surface = self._load_weapon_surface(path)
                if surface is not None:
                    return surface
        if weapon_id == "pistol":
            return self._load_weapon_surface(Path("dead_mans_hand") / "weapon.png")
        return None

    def _render_weapon(self):
        weapon_id = self.current_weapon_id
        cfg = self.current_weapon_config()
        hip = cfg["hip"]
        ads = cfg["ads"]
        blend = max(0.0, min(1.0, self.ads_blend))
        firing = self.muzzle_flash_timer > 0.0

        stems = []
        if self.reloading:
            progress = 1.0 - (self.reload_timer / max(0.001, float(cfg["reload_seconds"])))
            frame_count = max(1, int(cfg.get("reload_frames", 3)))
            reload_index = min(frame_count, max(1, int(progress * frame_count) + 1))
            stems.extend((f"reload_{reload_index:02d}", "idle"))
        elif firing:
            if blend >= 0.55:
                if cfg.get("automatic"):
                    fire_index = 1 + (int(self.elapsed * 24.0) % 2)
                    stems.extend((f"ads_fire_{fire_index:02d}", "ads_fire", "ads"))
                else:
                    stems.extend(("ads_fire", "ads"))
            else:
                if cfg.get("automatic"):
                    fire_index = 1 + (int(self.elapsed * 24.0) % 2)
                    stems.extend((f"fire_{fire_index:02d}", "fire", "idle"))
                else:
                    stems.extend(("fire", "idle"))
        elif self.bolt_timer > 0.0 and float(cfg.get("bolt_seconds", 0.0)) > 0.0:
            progress = 1.0 - (self.bolt_timer / max(0.001, float(cfg["bolt_seconds"])))
            frame_count = max(1, int(cfg.get("bolt_frames", 3)))
            bolt_index = min(frame_count, max(1, int(progress * frame_count) + 1))
            stems.extend((f"bolt_{bolt_index:02d}", "ads" if blend >= 0.55 else "idle"))
        elif blend >= 0.55:
            stems.append("ads")
        else:
            stems.append("idle")

        weapon = self._load_first_weapon_frame(weapon_id, stems)
        anchor_x = self._lerp(hip["anchor"][0], ads["anchor"][0], blend) * RENDER_WIDTH
        anchor_y = self._lerp(hip["anchor"][1], ads["anchor"][1], blend) * RENDER_HEIGHT
        target_h = int(round(self._lerp(hip["height"], ads["height"], blend)))

        bob_strength = (1.0 - blend * 0.82) if self.is_moving else 0.0
        bob_x = math.sin(self.walk_phase) * float(cfg["bob_x"]) * bob_strength
        bob_y = abs(math.cos(self.walk_phase * 2.0)) * float(cfg["bob_y"]) * bob_strength
        recoil_ratio = min(1.0, self.muzzle_flash_timer / 0.095) if firing else 0.0
        recoil_y = -float(cfg["recoil_y"]) * recoil_ratio

        if self.reloading:
            progress = 1.0 - (self.reload_timer / max(0.001, float(cfg["reload_seconds"])))
            reload_arc = math.sin(max(0.0, min(1.0, progress)) * math.pi)
            bob_y += 28.0 * reload_arc
            bob_x += 9.0 * reload_arc
        elif self.bolt_timer > 0.0 and float(cfg.get("bolt_seconds", 0.0)) > 0.0:
            progress = 1.0 - (self.bolt_timer / float(cfg["bolt_seconds"]))
            bolt_arc = math.sin(max(0.0, min(1.0, progress)) * math.pi)
            bob_x += 8.0 * bolt_arc
            bob_y += 3.0 * bolt_arc

        weapon_rect = None
        if weapon is not None:
            target_w = max(1, int(weapon.get_width() * target_h / max(1, weapon.get_height())))
            scaled = pygame.transform.smoothscale(weapon, (target_w, target_h))
            weapon_rect = scaled.get_rect(midbottom=(int(anchor_x + bob_x), int(anchor_y + bob_y + recoil_y)))
            self.render_surface.blit(scaled, weapon_rect)
        else:
            # Generic placeholder keeps newly unlocked weapons usable before art arrives.
            cx = int(anchor_x + bob_x)
            base_y = int(anchor_y + bob_y + recoil_y)
            long_gun = weapon_id != "pistol"
            body_w = 86 if long_gun else 54
            body_h = 24 if long_gun else 40
            pygame.draw.rect(self.render_surface, (42, 44, 49), (cx - body_w // 2, base_y - 70, body_w, body_h), border_radius=6)
            pygame.draw.rect(self.render_surface, (100, 72, 43), (cx - 10, base_y - 48, 20, 48), border_radius=4)
            if long_gun:
                pygame.draw.rect(self.render_surface, (78, 79, 82), (cx - 58, base_y - 66, 116, 9), border_radius=3)
            weapon_rect = pygame.Rect(cx - 70, base_y - 110, 140, 110)

        if firing and weapon_rect is not None:
            muzzle_u = self._lerp(hip["muzzle_uv"][0], ads["muzzle_uv"][0], blend)
            muzzle_v = self._lerp(hip["muzzle_uv"][1], ads["muzzle_uv"][1], blend)
            muzzle_x = int(weapon_rect.left + weapon_rect.width * muzzle_u)
            muzzle_y = int(weapon_rect.top + weapon_rect.height * muzzle_v)
            flash = self._load_weapon_surface(Path("dead_mans_hand") / "weapons" / "muzzle_flash.png")
            if flash is not None:
                flash_size = int(self._lerp(22, 18, blend))
                flash_scaled = pygame.transform.smoothscale(flash, (flash_size, flash_size))
                self.render_surface.blit(flash_scaled, flash_scaled.get_rect(center=(muzzle_x, muzzle_y)))
            else:
                pygame.draw.circle(self.render_surface, (255, 219, 91), (muzzle_x, muzzle_y), 8)
                pygame.draw.circle(self.render_surface, (255, 113, 42), (muzzle_x, muzzle_y), 4)

    def _render_crosshair(self):
        # Authored sights take over once the pistol reaches ADS.
        if self.ads_blend >= 0.72:
            return
        cx = RENDER_WIDTH // 2
        cy = RENDER_HEIGHT // 2
        color = (238, 231, 211)
        pygame.draw.line(self.render_surface, color, (cx - 7, cy), (cx - 2, cy), 1)
        pygame.draw.line(self.render_surface, color, (cx + 2, cy), (cx + 7, cy), 1)
        pygame.draw.line(self.render_surface, color, (cx, cy - 7), (cx, cy - 2), 1)
        pygame.draw.line(self.render_surface, color, (cx, cy + 2), (cx, cy + 7), 1)

    def draw(self, target_surface):
        self._render_world()
        visible = [enemy for enemy in self.enemies if enemy.alive]
        visible.sort(
            key=lambda enemy: math.hypot(enemy.x - self.player_x, enemy.y - self.player_y),
            reverse=True,
        )
        for enemy in visible:
            self._render_enemy(enemy)
        for pickup in self.pickups:
            self._render_pickup(pickup)
        self._render_weapon()
        self._render_crosshair()

        scaled = pygame.transform.scale(self.render_surface, target_surface.get_size())
        target_surface.blit(scaled, (0, 0))
        self._draw_hud(target_surface)

    def _draw_hud(self, target):
        width, height = target.get_size()
        small_font = self._font(22, False)
        title_font = self._font(46, True)
        dmh_title_font = self._dmh_font("ui", 46, True)
        alive = sum(1 for enemy in self.enemies if enemy.alive)
        kill_count_value = getattr(self, "total_kills", 0)

        panel_h = 102
        panel = pygame.Surface((width, panel_h), pygame.SRCALPHA)
        panel.fill((8, 9, 12, 176))
        target.blit(panel, (0, 0))

        health_rect = self._draw_meter_widget(
            target,
            16,
            18,
            Path("dead_mans_hand") / "ui" / "health_bar_bg.png",
            Path("dead_mans_hand") / "ui" / "health_bar_fill.png",
            Path("dead_mans_hand") / "ui" / "health_label.png",
            self.health / 100.0,
            "HEALTH",
            (188, 44, 44),
            widget_size=(332, 56),
            fill_insets=(30, 30, 28, 12),
        )

        # Center: per-level PNG header with explicit bounds so oversized art never collides.
        level_box = pygame.Rect(width // 2 - 300, 4, 600, 76)
        level_surface = self._load_level_header_surface(self.level_index + 1)
        if level_surface is not None:
            level_surface = self._fit_surface(level_surface, level_box.width, level_box.height, upscale=False)
            target.blit(level_surface, level_surface.get_rect(center=level_box.center))
        else:
            center = dmh_title_font.render(
                f"LEVEL {self.level_index + 1}: {self.level['name']}", True, (224, 194, 104)
            )
            target.blit(center, center.get_rect(center=level_box.center))

        # Right side gets two non-overlapping slots: kill counter above, ammo bar below.
        kills_box = pygame.Rect(width - 224, 8, 208, 36)
        kills_surface = self._load_ui_surface(Path("dead_mans_hand") / "ui" / "kill_count.png")
        if kills_surface is not None:
            kills_surface = self._fit_surface(kills_surface, kills_box.width, kills_box.height, upscale=False)
            kills_rect = kills_surface.get_rect(center=kills_box.center)
            target.blit(kills_surface, kills_rect)
            number_font = self._dmh_font("numbers", 24, True)
            number_text = f"{kill_count_value}"
            num_surface = number_font.render(number_text, True, (0, 0, 0))
            max_num_w = int(kills_rect.width * 0.18)
            if num_surface.get_width() > max_num_w:
                number_font = self._dmh_font("numbers", 20, True)
                num_surface = number_font.render(number_text, True, (0, 0, 0))
            number_rect = num_surface.get_rect(center=(kills_rect.left + int(kills_rect.width * 0.76), kills_rect.centery + 1))
            accent = number_font.render(number_text, True, (225, 38, 38))
            target.blit(accent, accent.get_rect(midright=(number_rect.midright[0] + 3, number_rect.midright[1] + 2)))
            target.blit(num_surface, number_rect)
        else:
            fallback = self._dmh_font("ui", 26, True).render(f"KILLS {kill_count_value}", True, (235, 224, 202))
            target.blit(fallback, fallback.get_rect(topright=(width - 18, 14)))

        ammo_ratio = self.current_ammo() / max(1, int(self.current_weapon_config()["mag_size"]))
        self._draw_meter_widget(
            target,
            width - 392,
            48,
            Path("dead_mans_hand") / "ui" / "ammo_bar_bg.png",
            Path("dead_mans_hand") / "ui" / "ammo_bar_fill.png",
            Path("dead_mans_hand") / "ui" / "ammo_label.png",
            ammo_ratio,
            "AMMO",
            (215, 177, 55),
            widget_size=(376, 46),
            fill_insets=(28, 24, 28, 9),
        )

        self._draw_weapon_sidebar(target)

        controls = small_font.render(
            "WASD move   Mouse aim   LMB fire   RMB aim   1-4 weapons   R reload   ESC exit",
            True,
            (225, 225, 225),
        )
        controls_bg = pygame.Surface((controls.get_width() + 26, 34), pygame.SRCALPHA)
        controls_bg.fill((8, 9, 12, 165))
        controls_rect = controls_bg.get_rect(midbottom=(width // 2, height - 12))
        target.blit(controls_bg, controls_rect)
        target.blit(controls, controls.get_rect(center=controls_rect.center))

        if self.damage_flash_timer > 0:
            alpha = int(115 * min(1.0, self.damage_flash_timer / 0.22))
            flash = pygame.Surface(target.get_size(), pygame.SRCALPHA)
            flash.fill((190, 20, 20, alpha))
            target.blit(flash, (0, 0))

        # If a custom level PNG exists, the top-center HUD already covers the identity.
        if self.level_banner_timer > 0 and level_surface is None:
            subtitle = self._dmh_font("ui", 30, True).render(
                f"LEVEL {self.level_index + 1}  -  {self.level['name']}", True, (255, 236, 171)
            )
            banner = pygame.Surface((subtitle.get_width() + 70, 62), pygame.SRCALPHA)
            banner.fill((5, 6, 9, 205))
            rect = banner.get_rect(center=(width // 2, 132))
            target.blit(banner, rect)
            target.blit(subtitle, subtitle.get_rect(center=rect.center))

        if self.level_clear_timer > 0 and not self.prototype_complete:
            text = title_font.render("ROOM CLEARED", True, (255, 226, 104))
            target.blit(text, text.get_rect(center=(width // 2, height // 2 - 80)))

        if self.game_over or self.prototype_complete:
            overlay = pygame.Surface(target.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 145))
            target.blit(overlay, (0, 0))
            if self.prototype_complete:
                headline = "PROTOTYPE COMPLETE"
                detail = f"Three levels cleared  -  Final score {self.score:,}"
            else:
                headline = "DEAD MAN'S HAND"
                detail = f"You were dealt out  -  Score {self.score:,}"
            title = title_font.render(headline, True, (225, 61, 61))
            info = self._font(28, True).render(detail, True, (245, 235, 214))
            hint = small_font.render("Press R to restart or ESC to return", True, (220, 220, 220))
            target.blit(title, title.get_rect(center=(width // 2, height // 2 - 54)))
            target.blit(info, info.get_rect(center=(width // 2, height // 2 + 8)))
            target.blit(hint, hint.get_rect(center=(width // 2, height // 2 + 56)))
