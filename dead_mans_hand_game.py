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
    # weapon_id is retained as the generic pickup id for compatibility with the
    # original weapon-only implementation. pickup_type distinguishes power-ups.
    weapon_id: str
    x: float
    y: float
    phase: float = 0.0
    acquired: bool = False
    pickup_type: str = "weapon"


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

from dead_mans_hand_weapons import (
    DEFAULT_POWERUP_PICKUPS,
    DEFAULT_WEAPON_PICKUPS,
    WEAPON_DEFINITIONS,
    weapon_for_slot,
)

ADS_TRANSITION_SPEED = 9.5
PICKUP_RADIUS = 0.58
# Phase is now used only for a subtle visibility pulse. Pickups no longer spin
# edge-on or bob at a fixed screen height.
PICKUP_SPIN_SPEED = 1.25
PICKUP_BOB_SPEED = 2.25
PICKUP_BOB_HEIGHT = 2
INVISIBILITY_SECONDS = 15.0
JUMP_IMPULSE = 3.35
JUMP_GRAVITY = 8.6
MAX_SHIELD = 100
POWERUP_COLORS = {
    "healthkit": (214, 55, 55),
    "overshield": (64, 157, 238),
    "invisibility": (174, 92, 230),
}



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
        self._level_surfaces = {}
        self._z_buffer = [MAX_RAY_DEPTH] * RENDER_WIDTH
        self.rng = random.Random()

        self.level_index = 0
        self.level = LEVELS[0]
        self.player_x = 0.0
        self.player_y = 0.0
        self.player_angle = 0.0
        self.health = 100
        self.shield = 0
        self.invisibility_timer = 0.0
        self.player_z = 0.0
        self.jump_velocity = 0.0
        self._jump_key_was_down = False
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
        self.shield = 0
        self.invisibility_timer = 0.0
        self.player_z = 0.0
        self.jump_velocity = 0.0
        self._jump_key_was_down = False
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
        self.player_z = 0.0
        self.jump_velocity = 0.0
        if not preserve_health:
            self.health = 100
        else:
            # Clearing a room still gives a modest recovery. Later rooms also
            # contain full health kits, so damage remains meaningful.
            self.health = min(100, self.health + 22)
        self.enemies = []
        self.pickups = []
        self._spawn_level_pickups()

        # Difficulty ramps across the full ten-level run. By Level 10 even pip
        # cards hit hard, while face cards become serious threats.
        progress = self.level_index / max(1, len(LEVELS) - 1)
        hp_mult = 1.0 + 0.60 * progress
        speed_mult = 1.0 + 0.28 * progress
        damage_mult = 1.0 + 1.25 * progress
        for card_id, ex, ey in self.level.get("enemies", ()):
            cfg = self._enemy_archetype(card_id)
            hp = float(cfg["hp"]) * hp_mult
            self.enemies.append(
                CardEnemy(
                    card_id=str(card_id),
                    x=float(ex),
                    y=float(ey),
                    hp=hp,
                    max_hp=hp,
                    speed=float(cfg["speed"]) * speed_mult,
                    damage=max(1, int(round(float(cfg["damage"]) * damage_mult))),
                    attack_range=cfg["attack_range"],
                    score_value=cfg["score"] + self.level_index * 35,
                )
            )
        self.shot_timer = 0.0
        self.muzzle_flash_timer = 0.0
        self.damage_flash_timer = 0.0
        self.level_clear_timer = 0.0
        self.level_banner_timer = 2.0

    def _reachable_open_cells(self):
        """Return grid cells reachable from the current player spawn."""
        rows = self.level.get("map") or ()
        if not rows:
            return set()
        width = len(rows[0])
        height = len(rows)
        start = (int(self.player_x), int(self.player_y))
        if not (0 <= start[0] < width and 0 <= start[1] < height):
            return set()
        if rows[start[1]][start[0]] != ".":
            return set()

        reachable = {start}
        frontier = [start]
        while frontier:
            x, y = frontier.pop()
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if (nx, ny) in reachable:
                    continue
                if not (0 <= nx < width and 0 <= ny < height):
                    continue
                if rows[ny][nx] != ".":
                    continue
                reachable.add((nx, ny))
                frontier.append((nx, ny))
        return reachable

    def _reachable_pickup_position(self, desired_x, desired_y, reachable=None):
        """Keep a pickup on a reachable open tile, falling back near its target."""
        reachable = self._reachable_open_cells() if reachable is None else reachable
        if not reachable:
            return float(self.player_x), float(self.player_y)

        desired_cell = (int(math.floor(desired_x)), int(math.floor(desired_y)))
        if desired_cell in reachable:
            return float(desired_x), float(desired_y)

        # Prefer the reachable cell closest to the authored placement; ties favor
        # cells near the player so a malformed future map cannot hide progression.
        px, py = self.player_x, self.player_y
        best = min(
            reachable,
            key=lambda cell: (
                (cell[0] + 0.5 - desired_x) ** 2 + (cell[1] + 0.5 - desired_y) ** 2,
                (cell[0] + 0.5 - px) ** 2 + (cell[1] + 0.5 - py) ** 2,
            ),
        )
        return best[0] + 0.5, best[1] + 0.5

    def _spawn_level_pickups(self):
        """Spawn reachable weapon and power-up pickups for the current level."""
        reachable = self._reachable_open_cells()

        seen = set()
        for weapon_id, wx, wy in DEFAULT_WEAPON_PICKUPS.get(self.level_index, ()):
            weapon_id = str(weapon_id)
            if weapon_id in seen or weapon_id in self.owned_weapons or weapon_id not in WEAPON_DEFINITIONS:
                continue
            seen.add(weapon_id)
            spawn_x, spawn_y = self._reachable_pickup_position(float(wx), float(wy), reachable)
            self.pickups.append(
                WeaponPickup(weapon_id, spawn_x, spawn_y, phase=self.rng.random() * math.tau, pickup_type="weapon")
            )

        for pickup_type, wx, wy in DEFAULT_POWERUP_PICKUPS.get(self.level_index, ()):
            pickup_type = str(pickup_type)
            spawn_x, spawn_y = self._reachable_pickup_position(float(wx), float(wy), reachable)
            self.pickups.append(
                WeaponPickup(pickup_type, spawn_x, spawn_y, phase=self.rng.random() * math.tau, pickup_type=pickup_type)
            )

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

    def _apply_player_damage(self, amount):
        """Apply incoming damage to overshield first, then normal health."""
        remaining = max(0, int(round(amount)))
        if remaining <= 0:
            return
        if self.shield > 0:
            absorbed = min(self.shield, remaining)
            self.shield -= absorbed
            remaining -= absorbed
        if remaining > 0:
            self.health = max(0, self.health - remaining)
        self.damage_flash_timer = 0.22
        self._pending_sound_events.append("player_hit")
        if self.health <= 0:
            self.game_over = True
            self._pending_sound_events.append("player_down")

    def _collect_pickup(self, pickup):
        """Apply one pickup effect. Return True only when it should be consumed."""
        pickup_type = str(getattr(pickup, "pickup_type", "weapon"))
        pickup_id = str(pickup.weapon_id)
        if pickup_type == "weapon":
            if pickup_id not in WEAPON_DEFINITIONS:
                return False
            self.owned_weapons.add(pickup_id)
            cfg = WEAPON_DEFINITIONS[pickup_id]
            self.weapon_ammo[pickup_id] = int(cfg["mag_size"])
            self.switch_weapon(pickup_id)
        elif pickup_type == "healthkit":
            if self.health >= 100:
                return False
            self.health = 100
        elif pickup_type == "overshield":
            if self.shield >= MAX_SHIELD:
                return False
            self.shield = MAX_SHIELD
        elif pickup_type == "invisibility":
            self.invisibility_timer = INVISIBILITY_SECONDS
        else:
            return False
        self._pending_sound_events.append("weapon_pickup")
        return True

    def jump(self):
        """Start a jump when grounded."""
        if self.game_over or self.prototype_complete or self.player_z > 0.001:
            return False
        self.jump_velocity = JUMP_IMPULSE
        return True

    def _move_enemy(self, enemy, dt):
        # Invisibility breaks enemy targeting for the full effect duration. Cards
        # remain visible but stop chasing/attacking until the player reappears.
        if self.invisibility_timer > 0.0:
            enemy.attack_cooldown = max(0.0, enemy.attack_cooldown - dt)
            return

        dx = self.player_x - enemy.x
        dy = self.player_y - enemy.y
        distance = math.hypot(dx, dy)
        if distance > self.ENEMY_WAKE_DISTANCE:
            return

        enemy.attack_cooldown = max(0.0, enemy.attack_cooldown - dt)
        if distance <= enemy.attack_range:
            if enemy.attack_cooldown <= 0.0:
                # A high jump can dodge a close-range card swipe.
                if self.player_z < 0.52:
                    self._apply_player_damage(enemy.damage)
                enemy.attack_cooldown = 0.72
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
        self.invisibility_timer = max(0.0, self.invisibility_timer - dt)
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

        # Space is edge-triggered here so main.py does not need a special jump
        # event path. Vertical motion is real gameplay state and also shifts the
        # camera; jumping high enough can dodge melee damage.
        jump_down = bool(keys[pygame.K_SPACE])
        if jump_down and not self._jump_key_was_down:
            self.jump()
        self._jump_key_was_down = jump_down
        if self.player_z > 0.0 or self.jump_velocity > 0.0:
            self.jump_velocity -= JUMP_GRAVITY * dt
            self.player_z += self.jump_velocity * dt
            if self.player_z <= 0.0:
                self.player_z = 0.0
                self.jump_velocity = 0.0

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

        # Pickups are proximity based. Full health/shield pickups remain in the
        # room until they can actually benefit the player.
        for pickup in self.pickups:
            if pickup.acquired:
                continue
            if math.hypot(pickup.x - self.player_x, pickup.y - self.player_y) <= PICKUP_RADIUS:
                if self._collect_pickup(pickup):
                    pickup.acquired = True

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
            # Weapon pickups never gate room completion. If the player leaves one
            # behind, the room still advances normally after the clear banner.
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
                        self.score += 5000

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
        return min(distance, MAX_RAY_DEPTH), material, edge, texture_phase, frac

    @staticmethod
    def _mix_color(a, b, t):
        t = max(0.0, min(1.0, float(t)))
        return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

    def _level_asset(self, filename):
        key = ("level_asset", self.level_index, str(filename))
        if key in self._level_surfaces:
            return self._level_surfaces[key]
        path = self.asset_root / "dead_mans_hand" / "levels" / f"level_{self.level_index + 1:02d}" / str(filename)
        try:
            surface = pygame.image.load(str(path)).convert_alpha()
        except (pygame.error, OSError, FileNotFoundError):
            surface = None
        self._level_surfaces[key] = surface
        return surface

    def _draw_environment_background(self, surface, horizon):
        theme = self.level.get("theme") or {}
        sky_top = tuple(theme.get("sky_top", (28, 35, 50)))
        sky_bottom = tuple(theme.get("sky_bottom", (56, 70, 92)))
        floor_near = tuple(theme.get("floor_near", (22, 21, 20)))
        floor_far = tuple(theme.get("floor_far", (63, 55, 45)))
        horizon = max(36, min(RENDER_HEIGHT - 36, int(horizon)))

        skybox = self._level_asset("skybox.png")
        if skybox is not None:
            sh = max(1, horizon)
            sw = max(RENDER_WIDTH * 2, int(skybox.get_width() * sh / max(1, skybox.get_height())))
            cache_key = ("sky_scaled", self.level_index, sw, sh)
            scaled = self._level_surfaces.get(cache_key)
            if scaled is None:
                scaled = pygame.transform.smoothscale(skybox, (sw, sh))
                self._level_surfaces[cache_key] = scaled
            offset = int(((self.player_angle % math.tau) / math.tau) * sw) % sw
            x = -offset
            while x < RENDER_WIDTH:
                surface.blit(scaled, (x, 0))
                x += sw
            if -offset + sw > 0 and -offset > 0:
                surface.blit(scaled, (-offset - sw, 0))
        else:
            for y in range(horizon):
                surface.fill(self._mix_color(sky_top, sky_bottom, y / max(1, horizon - 1)), (0, y, RENDER_WIDTH, 1))
            style = str(theme.get("sky_style", "dusk"))
            if style in ("night", "moon", "storm", "dusk"):
                for i in range(18):
                    x = (i * 83 + self.level_index * 29) % RENDER_WIDTH
                    y = (i * 37 + self.level_index * 11) % max(1, horizon - 8)
                    pygame.draw.circle(surface, (205, 211, 210), (x, y), 1)
            if style == "moon":
                pygame.draw.circle(surface, (208, 198, 174), (RENDER_WIDTH - 78, max(24, horizon // 3)), 18)
            elif style == "sunset":
                pygame.draw.circle(surface, (226, 143, 73), (RENDER_WIDTH - 72, max(24, int(horizon * 0.62))), 20)
            elif style == "city":
                for i in range(16):
                    w = 14 + (i * 7) % 22
                    h = 18 + (i * 17) % 48
                    x = i * 34 - 10
                    pygame.draw.rect(surface, (22, 16, 31), (x, horizon - h, w, h))
            elif style == "storm":
                pygame.draw.line(surface, (221, 214, 192), (350, 20), (328, 55), 2)
                pygame.draw.line(surface, (221, 214, 192), (328, 55), (345, 55), 2)
                pygame.draw.line(surface, (221, 214, 192), (345, 55), (322, 92), 2)
            elif style == "fog":
                for y in range(max(0, horizon - 45), horizon, 9):
                    pygame.draw.line(surface, (78, 103, 101), (0, y), (RENDER_WIDTH, y), 2)

        floor_tex = self._level_asset("floor.png")
        floor_h = max(1, RENDER_HEIGHT - horizon)
        if floor_tex is not None:
            cache_key = ("floor_scaled", self.level_index, RENDER_WIDTH, floor_h)
            scaled = self._level_surfaces.get(cache_key)
            if scaled is None:
                scaled = pygame.transform.smoothscale(floor_tex, (RENDER_WIDTH, floor_h))
                self._level_surfaces[cache_key] = scaled
            surface.blit(scaled, (0, horizon))
        else:
            for y in range(horizon, RENDER_HEIGHT):
                t = (y - horizon) / max(1, RENDER_HEIGHT - horizon - 1)
                color = self._mix_color(floor_far, floor_near, t)
                surface.fill(color, (0, y, RENDER_WIDTH, 1))
            # Perspective-ish floor seams make each palette read as a real floor.
            seam = tuple(max(0, int(c * 0.58)) for c in floor_near)
            for y in range(horizon + 18, RENDER_HEIGHT, 28):
                pygame.draw.line(surface, seam, (0, y), (RENDER_WIDTH, y), 1)
            for x in range(-RENDER_WIDTH, RENDER_WIDTH * 2, 54):
                pygame.draw.line(surface, seam, (RENDER_WIDTH // 2, horizon), (x, RENDER_HEIGHT), 1)

    def _render_world(self):
        surface = self.render_surface
        horizon = RENDER_HEIGHT // 2 + int(self.player_z * 18.0)
        self._draw_environment_background(surface, horizon)

        current_fov = FOV + (float(self.current_weapon_config()["ads_fov"]) - FOV) * self.ads_blend
        zoom_scale = FOV / max(0.001, current_fov)
        for column in range(RENDER_WIDTH):
            camera = (column / max(1, RENDER_WIDTH - 1)) - 0.5
            ray_angle = self.player_angle + camera * current_fov
            raw_distance, material, edge, phase, frac = self._cast_ray(ray_angle)
            corrected = max(0.055, raw_distance * math.cos(ray_angle - self.player_angle))
            self._z_buffer[column] = corrected
            wall_height = min(RENDER_HEIGHT * 3, int(((RENDER_HEIGHT * 0.92) / corrected) * zoom_scale))
            y0 = horizon - wall_height // 2

            authored_texture = self._level_asset(f"wall_{material}.png")
            shade = max(0.24, min(1.0, 1.08 - corrected / 16.0))
            if edge < 0.035:
                shade *= 0.72

            if authored_texture is not None:
                # Optional authored wall art gets true vertical texture sampling.
                tex_x = min(authored_texture.get_width() - 1, max(0, int(frac * authored_texture.get_width())))
                if phase:
                    tex_x = authored_texture.get_width() - 1 - tex_x
                source = authored_texture.subsurface((tex_x, 0, 1, authored_texture.get_height()))
                stripe = pygame.transform.scale(source, (1, max(1, wall_height)))
                shade_byte = max(0, min(255, int(255 * shade)))
                stripe.fill((shade_byte, shade_byte, shade_byte), special_flags=pygame.BLEND_RGB_MULT)
                surface.blit(stripe, (column, y0))
            else:
                # Fast procedural wall styling keeps the stock build lightweight.
                theme = self.level.get("theme") or {}
                base = (theme.get("walls") or {}).get(str(material), WALL_COLORS.get(material, WALL_COLORS["1"]))
                style = str(theme.get("wall_style", "boards"))
                stripe_index = int(frac * 16.0)
                pattern = 1.0
                if style in ("boards", "saloon"):
                    pattern = 0.80 if stripe_index % 3 == 0 else (1.08 if stripe_index % 3 == 1 else 0.94)
                elif style == "brick":
                    pattern = 0.82 if stripe_index % 4 == 0 else 1.0
                elif style == "steel":
                    pattern = 1.12 if stripe_index % 4 == 1 else (0.76 if stripe_index % 4 == 2 else 0.94)
                elif style == "stone":
                    pattern = 0.84 if stripe_index % 5 in (0, 1) else 1.02
                elif style == "mine":
                    pattern = 1.12 if stripe_index % 7 in (1, 2) else 0.72
                elif style == "wallpaper":
                    pattern = 1.12 if stripe_index % 4 == 0 else 0.90
                elif style == "rail":
                    pattern = 1.15 if stripe_index % 3 == 0 else 0.72
                elif style == "inferno":
                    pattern = 1.18 if stripe_index % 5 == 2 else 0.78
                final_shade = shade * pattern * (0.90 if phase else 1.0)
                color = tuple(max(0, min(255, int(channel * final_shade))) for channel in base)
                pygame.draw.line(surface, color, (column, y0), (column, y0 + wall_height))

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
        bg_source = self._load_ui_surface(bg_path)
        bg = self._fit_surface(bg_source, rect.width, rect.height, upscale=True)
        fill = self._load_ui_surface(fill_path)
        label = self._load_ui_surface(label_path)

        if bg is not None:
            bg_rect = bg.get_rect(center=rect.center)
            target.blit(bg, bg_rect)
        else:
            bg_rect = rect.copy()
            pygame.draw.rect(target, (10, 12, 18), rect, border_radius=10)
            pygame.draw.rect(target, (224, 194, 104), rect, 2, border_radius=10)

        # fill_insets are authored in the native background image's pixel space.
        # Convert them against the *actual fitted frame rect*, not the larger
        # widget slot. This guarantees the fill cannot spill outside an
        # aspect-fitted frame (the ammo HUD is intentionally much shorter).
        left, top, right, bottom = (int(v) for v in fill_insets)
        if bg_source is not None and bg is not None:
            source_w, source_h = bg_source.get_size()
            scale_x = bg_rect.width / max(1, source_w)
            scale_y = bg_rect.height / max(1, source_h)
            left = int(round(left * scale_x))
            right = int(round(right * scale_x))
            top = int(round(top * scale_y))
            bottom = int(round(bottom * scale_y))

        inner = pygame.Rect(
            bg_rect.left + left,
            bg_rect.top + top,
            max(1, bg_rect.width - left - right),
            max(1, bg_rect.height - top - bottom),
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

        # Preserve normal FPS perspective: cards get smaller with distance and
        # larger as they approach.  The previous overhaul accidentally made
        # every enemy a fixed ~94 px tall, which made distant cards enormous.
        # A modest minimum keeps far-away enemies readable without reintroducing
        # the old "tiny card" look, while the cap prevents point-blank cards
        # from swallowing most of the screen.
        zoom_scale = min(1.35, max(1.0, FOV / max(0.001, current_fov)))
        projected_height = ((RENDER_HEIGHT * 0.56) / corrected) * zoom_scale
        height = max(18, min(112, int(round(projected_height))))
        card = self._load_card_surface(enemy.card_id)
        width = max(8, int(height * card.get_width() / max(1, card.get_height())))
        horizon = RENDER_HEIGHT // 2 + int(self.player_z * 18.0)
        floor_drop = max(8, min(78, int((92.0 / corrected) * zoom_scale)))
        bottom_y = horizon + floor_drop
        top_y = bottom_y - height
        left_x = center_x - width // 2

        sprite = pygame.transform.smoothscale(card, (width, height))
        if enemy.hit_flash > 0.0:
            flash = pygame.Surface(sprite.get_size(), pygame.SRCALPHA)
            flash.fill((255, 70, 70, 105))
            sprite.blit(flash, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # Draw one vertical sprite slice at a time so walls still occlude cards.
        for sx in range(width):
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

        if enemy.hp < enemy.max_hp and 0 <= center_x < RENDER_WIDTH:
            bar_w = max(18, min(48, width))
            ratio = max(0.0, enemy.hp / enemy.max_hp)
            bx = center_x - bar_w // 2
            by = max(3, top_y - 5)
            pygame.draw.rect(self.render_surface, (32, 15, 15), (bx, by, bar_w, 3))
            pygame.draw.rect(self.render_surface, (210, 52, 52), (bx, by, int(bar_w * ratio), 3))

    def _load_pickup_surface(self, pickup_id, pickup_type="weapon"):
        pickup_id = str(pickup_id)
        pickup_type = str(pickup_type)
        key = f"pickup::{pickup_type}::{pickup_id}"
        if key in self._ui_surfaces:
            return self._ui_surfaces[key]

        names = [pickup_id]
        if pickup_type == "weapon" and pickup_id in WEAPON_DEFINITIONS:
            slug = str(WEAPON_DEFINITIONS[pickup_id].get("asset_slug", pickup_id))
            if slug not in names:
                names.insert(0, slug)
        surface = None
        for name in names:
            path = self.asset_root / "dead_mans_hand" / "pickups" / f"{name}.png"
            try:
                surface = pygame.image.load(str(path)).convert_alpha()
                break
            except (pygame.error, OSError, FileNotFoundError):
                continue

        if surface is None:
            surface = pygame.Surface((128, 128), pygame.SRCALPHA)
            accent = POWERUP_COLORS.get(pickup_type, (174, 39, 45))
            pygame.draw.rect(surface, (16, 17, 21, 235), (8, 8, 112, 112), border_radius=12)
            pygame.draw.rect(surface, accent, (8, 8, 112, 112), 5, border_radius=12)
            if pickup_type == "healthkit":
                pygame.draw.rect(surface, accent, (52, 25, 24, 78), border_radius=4)
                pygame.draw.rect(surface, accent, (25, 52, 78, 24), border_radius=4)
                label_text = "HEALTH"
            elif pickup_type == "overshield":
                pygame.draw.polygon(surface, accent, ((64, 20), (100, 34), (94, 80), (64, 106), (34, 80), (28, 34)))
                pygame.draw.polygon(surface, (25, 34, 45), ((64, 31), (89, 41), (84, 73), (64, 91), (44, 73), (39, 41)))
                label_text = "SHIELD"
            elif pickup_type == "invisibility":
                pygame.draw.ellipse(surface, accent, (24, 42, 80, 44), 6)
                pygame.draw.circle(surface, accent, (64, 64), 13, 4)
                label_text = "INVIS"
            else:
                label_text = WEAPON_DEFINITIONS.get(pickup_id, {}).get("name", pickup_id)
            if pickup_type == "weapon":
                label = self._font(21, True).render(str(label_text), True, (238, 226, 204))
                if label.get_width() > 106:
                    label = pygame.transform.smoothscale(label, (106, max(1, int(label.get_height() * 106 / label.get_width()))))
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
        if center_x < -96 or center_x > RENDER_WIDTH + 96:
            return
        zoom_scale = min(1.35, max(1.0, FOV / max(0.001, current_fov)))

        # Stable billboard: no edge-on spin. A tiny pulse catches the eye while
        # the projected floor position keeps the icon from appearing to float.
        pulse = 1.0 + math.sin(pickup.phase * (PICKUP_BOB_SPEED / PICKUP_SPIN_SPEED)) * 0.045
        base_height = max(36, min(74, int((70.0 / corrected) * zoom_scale)))
        base_height = max(32, int(base_height * pulse))
        source = self._load_pickup_surface(pickup.weapon_id, pickup.pickup_type)
        aspect = source.get_width() / max(1, source.get_height())
        draw_width = max(22, int(base_height * aspect))
        sprite = pygame.transform.smoothscale(source, (draw_width, base_height))

        horizon = RENDER_HEIGHT // 2 + int(self.player_z * 18.0)
        floor_drop = max(8, min(80, int((88.0 / corrected) * zoom_scale)))
        bottom_y = horizon + floor_drop
        top_y = bottom_y - base_height
        left_x = center_x - draw_width // 2

        center_visible = 0 <= center_x < RENDER_WIDTH and corrected < self._z_buffer[center_x] + 0.04
        if center_visible:
            accent = POWERUP_COLORS.get(pickup.pickup_type, (223, 178, 66))
            glow_w = max(18, int(draw_width * 0.78))
            pygame.draw.ellipse(
                self.render_surface,
                tuple(max(0, int(c * 0.72)) for c in accent),
                (center_x - glow_w // 2, bottom_y - 4, glow_w, 7),
                1,
            )

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
        cfg = WEAPON_DEFINITIONS.get(weapon_id, {})
        slug = str(cfg.get("asset_slug", weapon_id))
        for candidate in (slug, weapon_id):
            icon = self._load_ui_surface(Path("dead_mans_hand") / "ui" / "weapons" / f"{candidate}.png")
            if icon is not None:
                return icon
        return None

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
        cfg = WEAPON_DEFINITIONS.get(weapon_id, {})
        slug = str(cfg.get("asset_slug", weapon_id))
        candidates = []
        for folder_name in dict.fromkeys((slug, weapon_id)):
            folder = Path("dead_mans_hand") / "weapons" / folder_name
            candidates.extend((folder / f"{stem}.png", folder / f"{folder_name}_{stem}.png"))
        return tuple(candidates)

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

        panel_h = 120
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
            # Native 360x72 frame contains a 320x28 fill at x=20, y=22.
            fill_insets=(20, 22, 20, 22),
        )

        if self.shield > 0:
            shield_label = self._font(16, True).render("SHIELD", True, (126, 205, 255))
            target.blit(shield_label, (18, 78))
            shield_rect = pygame.Rect(76, 80, 272, 12)
            pygame.draw.rect(target, (10, 21, 31), shield_rect, border_radius=4)
            shield_fill = shield_rect.copy()
            shield_fill.width = max(1, int(shield_rect.width * (self.shield / MAX_SHIELD)))
            pygame.draw.rect(target, (57, 151, 225), shield_fill, border_radius=4)
            pygame.draw.rect(target, (128, 211, 255), shield_rect, 2, border_radius=4)

        if self.invisibility_timer > 0.0:
            invis = self._font(16, True).render(
                f"INVISIBLE {self.invisibility_timer:0.1f}s", True, (210, 143, 255)
            )
            target.blit(invis, (18, 98))

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
            # Native 360x72 frame contains a 320x28 fill at x=20, y=22.
            fill_insets=(20, 22, 20, 22),
        )

        self._draw_weapon_sidebar(target)

        controls = small_font.render(
            "WASD move   SPACE jump   Mouse aim   LMB fire   RMB aim   1-4 weapons   R reload   ESC exit",
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
                headline = "RUN COMPLETE"
                detail = f"Ten levels cleared  -  Final score {self.score:,}"
            else:
                headline = "DEAD MAN'S HAND"
                detail = f"You were dealt out  -  Score {self.score:,}"
            title = title_font.render(headline, True, (225, 61, 61))
            info = self._font(28, True).render(detail, True, (245, 235, 214))
            hint = small_font.render("Press R to restart or ESC to return", True, (220, 220, 220))
            target.blit(title, title.get_rect(center=(width // 2, height // 2 - 54)))
            target.blit(info, info.get_rect(center=(width // 2, height // 2 + 8)))
            target.blit(hint, hint.get_rect(center=(width // 2, height // 2 + 56)))
