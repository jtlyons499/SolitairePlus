"""Playable Battle Bosses arena for Arcade Night.

The arena is inspired by classic four-corner projectile games, but uses an
original card-themed presentation: four corner forts, orbiting shields, and a
Joker projectile. The player defends the lower-left fort against three Career
NPC rivals.
"""
from __future__ import annotations

import math
import os
import random

import pygame


ASSET_ROOT = os.path.join("assets", "arcade", "battle_bosses")
ARCADE_BACKGROUND_PATH = os.path.join("assets", "arcade", "bg.png")


class BattleBossesGame:
    # Keep the four stations visually gathered around one shared arena.
    # The first playable draft used almost the full 1366-wide screen, which
    # made opposite rivals feel miles apart while each shield hugged its own
    # fort.  A more compact, taller arena plus a larger shield orbit produces
    # the classic four-corner spacing without copying any legacy game's art.
    ARENA_RECT = pygame.Rect(320, 170, 726, 450)
    FORT_RADIUS = 50
    SHIELD_RADIUS = 126
    SHIELD_LENGTH = 82
    MIN_SHIELD_LENGTH = 46
    SHIELD_WEAR_PER_BLOCK = 3.0
    SHIELD_THICKNESS = 15
    BALL_SIZE = (30, 38)
    PLAYER_SHIELD_SPEED = 105.0  # degrees / second
    BALL_START_SPEED = 345.0
    BALL_MAX_SPEED = 610.0
    MAX_HP = 5
    HIT_COOLDOWN_MS = 95
    COLLISION_STEP_PX = 5.0
    LOOP_CONTACT_WINDOW_MS = 1600
    LOOP_ESCAPE_COOLDOWN_MS = 850
    LOOP_CONTACT_LIMIT = 6
    LOOP_CLUSTER_RADIUS = 125.0

    CORNERS = (
        "bottom_left",
        "top_left",
        "top_right",
        "bottom_right",
    )

    # Each shield travels on the inward-facing sixty-degree section of its
    # fort's orbit.  This keeps every defender between its fort and the center
    # rather than letting shields bunch against the outer arena walls.
    CORNER_ANGLE_RANGES = {
        "bottom_left": (-65.0, -5.0),
        "top_left": (5.0, 65.0),
        "top_right": (115.0, 175.0),
        "bottom_right": (185.0, 245.0),
    }

    def __init__(self):
        self.player_name = "You"
        self.opponents = []
        self.difficulty_id = "standard"
        self.difficulty = {}
        self.forts = []
        self.ball_rect = pygame.Rect(0, 0, *self.BALL_SIZE)
        self.ball_velocity = pygame.Vector2(0, 0)
        self.finished = False
        self.forfeited = False
        self.reward_claimed = False
        self.winner_text = ""
        self.rivals_eliminated = 0
        self._last_collision_at = 0
        self._last_hit_text = ""
        self._hit_text_until = 0
        self._sound_events = []
        self._contact_history = []
        self._last_loop_escape_at = -10000
        self._asset_cache = {}
        self._scaled_cache = {}
        # Rotate the human through all four corners from match to match.
        # This prevents any small geometric advantage from becoming a permanent
        # player advantage while keeping the four-corner identity intact.
        self._player_corner_rotation = -1

    @property
    def player_fort(self):
        return self.forts[0] if self.forts else None

    @property
    def player_won(self):
        return bool(
            self.finished
            and not self.forfeited
            and self.player_fort
            and self.player_fort["hp"] > 0
            and all(fort["hp"] <= 0 for fort in self.forts[1:])
        )

    @property
    def ticket_multiplier(self):
        return float(self.difficulty.get("ticket_multiplier", 1.0))

    @property
    def player_hp(self):
        if not self.player_fort:
            return 0
        return max(0, int(self.player_fort.get("hp", 0)))

    def start_match(self, opponents, difficulty_id, difficulty_config, player_name="You"):
        self.player_name = str(player_name or "You")
        self.opponents = list(opponents or [])[:3]
        while len(self.opponents) < 3:
            index = len(self.opponents)
            self.opponents.append({
                "id": f"battle_bosses_fallback_{index}",
                "name": f"Arcade Boss {index + 1}",
                "skill_tier": "mid",
            })

        self.difficulty_id = str(difficulty_id or "standard")
        self.difficulty = dict(difficulty_config or {})
        self.finished = False
        self.forfeited = False
        self.reward_claimed = False
        self.winner_text = ""
        self.rivals_eliminated = 0
        self._last_collision_at = 0
        self._last_hit_text = ""
        self._hit_text_until = 0
        self._sound_events = []
        self._contact_history = []
        self._last_loop_escape_at = -10000

        centers = self._fort_centers()
        self._player_corner_rotation = (self._player_corner_rotation + 1) % len(self.CORNERS)
        player_corner = self.CORNERS[self._player_corner_rotation]
        rival_corners = [corner for corner in self.CORNERS if corner != player_corner]
        entries = [
            (self.player_name, None, player_corner),
            (str(self.opponents[0].get("name") or "Rival 1"), self.opponents[0], rival_corners[0]),
            (str(self.opponents[1].get("name") or "Rival 2"), self.opponents[1], rival_corners[1]),
            (str(self.opponents[2].get("name") or "Rival 3"), self.opponents[2], rival_corners[2]),
        ]
        self.forts = []
        for index, (name, npc, corner) in enumerate(entries):
            angle_min, angle_max = self.CORNER_ANGLE_RANGES[corner]
            self.forts.append({
                "index": index,
                "name": name,
                "npc": npc,
                "corner": corner,
                "center": pygame.Vector2(centers[corner]),
                "hp": self.MAX_HP,
                "max_hp": self.MAX_HP,
                "angle": (angle_min + angle_max) / 2.0,
                "angle_min": angle_min,
                "angle_max": angle_max,
                "angular_velocity": 0.0,
                "shield_blocks": 0,
            })

        self._serve_ball()

    def _queue_sound(self, sound_name):
        sound_name = str(sound_name or "").strip()
        if sound_name:
            self._sound_events.append(sound_name)

    def pop_sound_events(self):
        events = list(self._sound_events)
        self._sound_events.clear()
        return events

    def forfeit(self):
        if self.finished:
            return
        self.forfeited = True
        self.finished = True
        self.ball_velocity.update(0, 0)
        self.winner_text = "You left the Battle Bosses arena."

    def _fort_centers(self):
        # Forts sit near the true corners, while their shields orbit farther
        # inward.  The equal insets keep all four stations symmetric.
        inset_x = 70
        inset_y = 70
        arena = self.ARENA_RECT
        return {
            "top_left": (arena.left + inset_x, arena.top + inset_y),
            "top_right": (arena.right - inset_x, arena.top + inset_y),
            "bottom_left": (arena.left + inset_x, arena.bottom - inset_y),
            "bottom_right": (arena.right - inset_x, arena.bottom - inset_y),
        }

    @staticmethod
    def _vector_from_angle(angle_degrees):
        radians = math.radians(angle_degrees)
        return pygame.Vector2(math.cos(radians), math.sin(radians))

    @staticmethod
    def _clamp(value, low, high):
        return max(low, min(high, value))

    @staticmethod
    def _angle_for_vector(vector):
        angle = math.degrees(math.atan2(vector.y, vector.x))
        if angle < 0:
            angle += 360.0
        return angle

    @staticmethod
    def _unwrap_angle_for_range(angle, low, high):
        candidates = (angle - 360.0, angle, angle + 360.0)
        return min(
            candidates,
            key=lambda candidate: 0.0 if low <= candidate <= high else min(abs(candidate - low), abs(candidate - high)),
        )

    def _active_fort_count(self):
        return sum(1 for fort in self.forts if fort.get("hp", 0) > 0)

    def _late_game_speed_floor(self):
        active = self._active_fort_count()
        base = float(self.difficulty.get("ball_speed", self.BALL_START_SPEED))
        if active <= 2:
            return max(base, 485.0)
        if active == 3:
            return max(base, 410.0)
        return max(base, self.BALL_START_SPEED)

    def _apply_late_game_pace(self):
        if self.finished or self.ball_velocity.length_squared() <= 0.0001:
            return
        floor = self._late_game_speed_floor()
        speed = self.ball_velocity.length()
        if speed < floor:
            self.ball_velocity.scale_to_length(floor)

    def _serve_ball(self):
        self.ball_rect.center = self.ARENA_RECT.center
        angle = random.choice((28, 38, 52, 128, 142, 218, 232, 308, 322))
        direction = self._vector_from_angle(angle)
        speed = float(self.difficulty.get("ball_speed", self.BALL_START_SPEED))
        self.ball_velocity = direction * speed
        self._apply_late_game_pace()

    def _shield_length(self, fort):
        blocks = max(0, int(fort.get("shield_blocks", 0)))
        return max(
            self.MIN_SHIELD_LENGTH,
            self.SHIELD_LENGTH - blocks * self.SHIELD_WEAR_PER_BLOCK,
        )

    def _shield_geometry(self, fort):
        radial = self._vector_from_angle(fort["angle"])
        center = fort["center"] + radial * self.SHIELD_RADIUS
        tangent = pygame.Vector2(-radial.y, radial.x)
        half = tangent * (self._shield_length(fort) / 2.0)
        return center, center - half, center + half, radial

    @staticmethod
    def _closest_point_on_segment(point, start, end):
        segment = end - start
        length_sq = segment.length_squared()
        if length_sq <= 0.0001:
            return start.copy(), 0.5
        t = (point - start).dot(segment) / length_sq
        t = max(0.0, min(1.0, t))
        return start + segment * t, t

    @classmethod
    def _distance_to_segment(cls, point, start, end):
        closest, _t = cls._closest_point_on_segment(point, start, end)
        return (point - closest).length()

    def _move_player_shield(self, dt, pressed_keys):
        fort = self.player_fort
        if not fort or fort["hp"] <= 0:
            return
        direction = 0
        if pressed_keys[pygame.K_a] or pressed_keys[pygame.K_LEFT]:
            direction -= 1
        if pressed_keys[pygame.K_d] or pressed_keys[pygame.K_RIGHT]:
            direction += 1
        previous_angle = fort["angle"]
        fort["angle"] = self._clamp(
            fort["angle"] + direction * self.PLAYER_SHIELD_SPEED * dt,
            fort["angle_min"],
            fort["angle_max"],
        )
        fort["angular_velocity"] = (fort["angle"] - previous_angle) / max(dt, 0.0001)

    def _move_npc_shields(self, dt):
        ball_center = pygame.Vector2(self.ball_rect.center)
        base_speed = float(self.difficulty.get("npc_shield_speed", 72.0))
        aim_error = float(self.difficulty.get("aim_error", 12.0))
        reaction_distance = float(self.difficulty.get("reaction_distance", 520.0))

        for fort in self.forts[1:]:
            if fort["hp"] <= 0:
                continue
            to_ball = ball_center - fort["center"]
            distance = to_ball.length()
            if distance <= 0.001:
                continue

            if distance > reaction_distance:
                target = (fort["angle_min"] + fort["angle_max"]) / 2.0
            else:
                target = self._angle_for_vector(to_ball)
                target = self._unwrap_angle_for_range(target, fort["angle_min"], fort["angle_max"])
                target += random.uniform(-aim_error, aim_error) * min(1.0, dt * 3.0)
                target = self._clamp(target, fort["angle_min"], fort["angle_max"])

            previous_angle = fort["angle"]
            delta = target - fort["angle"]
            max_step = base_speed * dt
            if abs(delta) <= max_step:
                fort["angle"] = target
            else:
                fort["angle"] += max_step if delta > 0 else -max_step
            fort["angular_velocity"] = (fort["angle"] - previous_angle) / max(dt, 0.0001)

    def _record_contact(self, now, kind, key=None):
        """Remember recent collision positions so stable pinball loops can escape.

        Normal rallies are untouched.  The watchdog only acts after several
        contacts repeat inside a small part of the arena in a short window.
        """
        center = pygame.Vector2(self.ball_rect.center)
        self._contact_history.append((int(now), str(kind), key, center.x, center.y))
        cutoff = int(now) - self.LOOP_CONTACT_WINDOW_MS
        self._contact_history = [entry for entry in self._contact_history if entry[0] >= cutoff]

    def _break_ricochet_loop_if_needed(self, now):
        if int(now) < self._last_loop_escape_at + self.LOOP_ESCAPE_COOLDOWN_MS:
            return False

        history = self._contact_history
        if len(history) < self.LOOP_CONTACT_LIMIT:
            return False

        recent = history[-self.LOOP_CONTACT_LIMIT:]
        xs = [entry[3] for entry in recent]
        ys = [entry[4] for entry in recent]
        clustered = (
            max(xs) - min(xs) <= self.LOOP_CLUSTER_RADIUS
            and max(ys) - min(ys) <= self.LOOP_CLUSTER_RADIUS
        )

        # A same-shield pocket can cover slightly more space than the generic
        # cluster threshold, so also recognize repeated contacts with one
        # defender during the watchdog window.
        shield_keys = [entry[2] for entry in recent if entry[1] == "shield"]
        repeated_shield = bool(shield_keys) and max(shield_keys.count(key) for key in set(shield_keys)) >= 4

        if not clustered and not repeated_shield:
            return False

        ball_center = pygame.Vector2(self.ball_rect.center)
        toward_center = pygame.Vector2(self.ARENA_RECT.center) - ball_center
        if toward_center.length_squared() <= 64.0:
            # In the unlikely event a loop forms around center court, rotate
            # the current path instead of inventing a preferred corner.
            if self.ball_velocity.length_squared() > 0.0001:
                toward_center = self.ball_velocity.rotate(random.choice((-31.0, 31.0)))
            else:
                toward_center = self._vector_from_angle(random.choice((31, 149, 211, 329)))

        direction = toward_center.normalize()
        perpendicular = pygame.Vector2(-direction.y, direction.x)
        direction = direction + perpendicular * random.uniform(-0.20, 0.20)
        if direction.length_squared() <= 0.0001:
            direction = toward_center.normalize()
        direction = direction.normalize()

        speed = max(
            self._late_game_speed_floor(),
            self.ball_velocity.length() if self.ball_velocity.length_squared() > 0.0001 else 0.0,
            430.0,
        )
        self.ball_velocity = direction * min(self.BALL_MAX_SPEED, speed)

        # Move a few pixels down the escape path so the next substep cannot
        # immediately rediscover the exact same contact point.
        escaped = ball_center + direction * 14.0
        half_w = self.ball_rect.width / 2.0
        half_h = self.ball_rect.height / 2.0
        escaped.x = self._clamp(escaped.x, self.ARENA_RECT.left + half_w + 2, self.ARENA_RECT.right - half_w - 2)
        escaped.y = self._clamp(escaped.y, self.ARENA_RECT.top + half_h + 2, self.ARENA_RECT.bottom - half_h - 2)
        self.ball_rect.center = (int(round(escaped.x)), int(round(escaped.y)))

        self._last_loop_escape_at = int(now)
        self._last_collision_at = int(now)
        self._contact_history.clear()
        return True

    def _bounce_from_boundaries(self, now):
        arena = self.ARENA_RECT
        bounced = None
        if self.ball_rect.left <= arena.left:
            self.ball_rect.left = arena.left
            self.ball_velocity.x = abs(self.ball_velocity.x)
            bounced = "left"
        elif self.ball_rect.right >= arena.right:
            self.ball_rect.right = arena.right
            self.ball_velocity.x = -abs(self.ball_velocity.x)
            bounced = "right"

        if self.ball_rect.top <= arena.top:
            self.ball_rect.top = arena.top
            self.ball_velocity.y = abs(self.ball_velocity.y)
            bounced = "top" if bounced is None else bounced + "+top"
        elif self.ball_rect.bottom >= arena.bottom:
            self.ball_rect.bottom = arena.bottom
            self.ball_velocity.y = -abs(self.ball_velocity.y)
            bounced = "bottom" if bounced is None else bounced + "+bottom"

        if bounced is not None:
            self._record_contact(now, "wall", bounced)
            self._break_ricochet_loop_if_needed(now)

    def _reflect_velocity(self, normal, speed_boost=1.025, tangent_impulse=None):
        if normal.length_squared() <= 0.0001:
            normal = pygame.Vector2(1, 0)
        normal = normal.normalize()
        velocity = self.ball_velocity
        reflected = velocity - 2.0 * velocity.dot(normal) * normal
        if tangent_impulse is not None:
            reflected += tangent_impulse
        if reflected.length_squared() <= 0.0001:
            reflected = -velocity
        speed = min(
            self.BALL_MAX_SPEED,
            max(self._late_game_speed_floor(), reflected.length() * speed_boost),
        )
        self.ball_velocity = reflected.normalize() * speed

    def _check_shield_collisions(self, now):
        if now < self._last_collision_at + self.HIT_COOLDOWN_MS:
            return False

        ball_center = pygame.Vector2(self.ball_rect.center)
        ball_radius = max(self.ball_rect.width, self.ball_rect.height) * 0.42
        contact_radius = ball_radius + self.SHIELD_THICKNESS / 2.0

        for fort in self.forts:
            if fort["hp"] <= 0:
                continue

            shield_center, start, end, radial = self._shield_geometry(fort)
            closest, segment_t = self._closest_point_on_segment(ball_center, start, end)
            separation = ball_center - closest
            distance = separation.length()
            if distance > contact_radius:
                continue

            # Shields are one-way defensive faces. Once the Joker has passed
            # behind a shield toward its fort, let it continue to the fort
            # instead of trapping it between the shield's back face and the
            # corner. Small substeps ensure a genuine front-face impact is
            # detected before this threshold is crossed.
            front_side = (ball_center - shield_center).dot(radial)
            if front_side < -2.0:
                continue

            # Use the actual ball-to-shield contact normal instead of snapping
            # the Joker toward the center of the shield. With movement broken
            # into small substeps this gives a clean air-hockey-like ricochet.
            if distance > 0.001:
                normal = separation / distance
            else:
                normal = radial.copy()
                if self.ball_velocity.dot(normal) > 0:
                    normal *= -1

            # Only collide while moving into this face of the shield.
            approach_speed = self.ball_velocity.dot(normal)
            if approach_speed >= -2.0:
                continue

            tangent = end - start
            if tangent.length_squared() > 0.001:
                tangent = tangent.normalize()
            else:
                tangent = pygame.Vector2(-normal.y, normal.x)

            # Edge hits and a moving shield add a small tangential impulse.
            # This prevents every save from returning along the same radial
            # line while keeping the result predictable enough to defend.
            edge_factor = (segment_t - 0.5) * 2.0
            angular_velocity = float(fort.get("angular_velocity", 0.0))
            surface_speed = math.radians(angular_velocity) * self.SHIELD_RADIUS
            tangent_impulse = tangent * (edge_factor * 42.0 + surface_speed * 0.24)

            self._reflect_velocity(
                normal,
                speed_boost=1.025,
                tangent_impulse=tangent_impulse,
            )

            # Resolve penetration from the exact closest point. This is the
            # key anti-sticking step: the Joker leaves the shield surface
            # rather than being teleported toward its rotating center.
            safe_center = closest + normal * (contact_radius + 2.5)
            self.ball_rect.center = (
                int(round(safe_center.x)),
                int(round(safe_center.y)),
            )
            self._last_collision_at = now
            fort["shield_blocks"] = int(fort.get("shield_blocks", 0)) + 1
            self._queue_sound("battle_bosses_ricochet")
            self._record_contact(now, "shield", fort["index"])
            self._break_ricochet_loop_if_needed(now)
            return True

        return False

    def _check_fort_collisions(self, now):
        if now < self._last_collision_at + self.HIT_COOLDOWN_MS:
            return False
        ball_center = pygame.Vector2(self.ball_rect.center)

        for fort in self.forts:
            if fort["hp"] <= 0:
                continue
            delta = ball_center - fort["center"]
            distance = delta.length()
            if distance > self.FORT_RADIUS:
                continue
            if distance <= 0.001:
                delta = pygame.Vector2(1, 0)
            radial = delta.normalize()

            # Damage only on an inward hit. If a previous reflection leaves the
            # projectile barely inside the radius, do not double-charge HP.
            if self.ball_velocity.dot(radial) >= 0:
                continue

            fort["hp"] = max(0, fort["hp"] - 1)
            self._last_collision_at = now
            self._record_contact(now, "fort", fort["index"])
            self._reflect_velocity(radial, speed_boost=1.035)
            self._queue_sound("battle_bosses_fort_hit")
            safe_center = fort["center"] + radial * (self.FORT_RADIUS + 18)
            self.ball_rect.center = (int(round(safe_center.x)), int(round(safe_center.y)))

            if fort["hp"] <= 0:
                if fort["index"] == 0:
                    self.finished = True
                    self.ball_velocity.update(0, 0)
                    self.winner_text = "Your fort fell. The bosses win."
                    self._queue_sound("battle_bosses_loss")
                else:
                    self.rivals_eliminated += 1
                    self._apply_late_game_pace()
                    self._last_hit_text = f"{fort['name']} eliminated!"
                    self._queue_sound("battle_bosses_eliminate")
                    if all(rival["hp"] <= 0 for rival in self.forts[1:]):
                        self.finished = True
                        self.ball_velocity.update(0, 0)
                        self.winner_text = "All three bosses are down!"
                        self._queue_sound("battle_bosses_win")
            else:
                self._last_hit_text = f"{fort['name']} fort hit - {fort['hp']} shields left"

            self._hit_text_until = now + 1200
            return True
        return False

    def update(self, dt, pressed_keys):
        if self.finished:
            return
        try:
            dt = float(dt)
        except (TypeError, ValueError):
            dt = 1 / 60
        dt = max(1 / 240, min(dt, 1 / 20))

        self._move_player_shield(dt, pressed_keys)
        self._move_npc_shields(dt)
        self._apply_late_game_pace()

        travel = self.ball_velocity.length() * dt
        steps = max(1, min(10, int(math.ceil(travel / self.COLLISION_STEP_PX))))
        step_dt = dt / steps

        for _step in range(steps):
            if self.finished:
                break
            self.ball_rect.x += int(round(self.ball_velocity.x * step_dt))
            self.ball_rect.y += int(round(self.ball_velocity.y * step_dt))
            now = pygame.time.get_ticks()
            self._bounce_from_boundaries(now)

            if not self._check_shield_collisions(now):
                self._check_fort_collisions(now)

    def _load_image(self, path):
        if path in self._asset_cache:
            return self._asset_cache[path]
        try:
            image = pygame.image.load(path).convert_alpha()
        except (pygame.error, FileNotFoundError):
            image = None
        self._asset_cache[path] = image
        return image

    def _scaled_image(self, path, size):
        key = (path, tuple(size))
        if key in self._scaled_cache:
            return self._scaled_cache[key]
        image = self._load_image(path)
        if image is None:
            self._scaled_cache[key] = None
            return None
        scaled = pygame.transform.smoothscale(image, size)
        self._scaled_cache[key] = scaled
        return scaled

    def _draw_ball(self, surface):
        image = self._scaled_image(
            os.path.join(ASSET_ROOT, "joker_ball.png"),
            self.ball_rect.size,
        )
        if image is not None:
            surface.blit(image, self.ball_rect.topleft)
            return

        center = self.ball_rect.center
        pygame.draw.ellipse(surface, (246, 243, 226), self.ball_rect)
        pygame.draw.ellipse(surface, (224, 65, 83), self.ball_rect, 2)
        font = pygame.font.Font(None, 22)
        joker = font.render("J", True, (34, 34, 40))
        surface.blit(joker, joker.get_rect(center=center))

    @staticmethod
    def _corner_label_anchor(fort):
        x, y = fort["center"]
        corner = fort["corner"]
        if "left" in corner:
            label_x = x + 5
        else:
            label_x = x - 5
        if "top" in corner:
            label_y = y - 72
        else:
            label_y = y + 72
        return int(label_x), int(label_y)

    def _draw_portrait(self, surface, fort, portrait_loader, player_portrait):
        center = fort["center"]
        rect = pygame.Rect(0, 0, 54, 54)
        rect.center = (int(center.x), int(center.y))
        pygame.draw.ellipse(surface, (14, 21, 30), rect)

        portrait = None
        if fort["index"] == 0:
            portrait = player_portrait
        elif callable(portrait_loader) and isinstance(fort.get("npc"), dict):
            try:
                portrait = portrait_loader(fort["npc"], 54)
            except Exception:
                portrait = None

        if portrait is not None:
            try:
                portrait = pygame.transform.smoothscale(portrait, rect.size)
                mask = pygame.Surface(rect.size, pygame.SRCALPHA)
                pygame.draw.ellipse(mask, (255, 255, 255, 255), mask.get_rect())
                clipped = portrait.copy()
                clipped.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                surface.blit(clipped, rect.topleft)
            except pygame.error:
                portrait = None

        if portrait is None:
            suit = "H" if fort["index"] == 0 else ("S", "D", "C")[(fort["index"] - 1) % 3]
            font = pygame.font.Font(None, 36)
            color = (224, 72, 88) if suit in ("H", "D") else (230, 232, 235)
            rendered = font.render(suit, True, color)
            surface.blit(rendered, rendered.get_rect(center=rect.center))

        border = (230, 196, 101) if fort["hp"] > 0 else (105, 108, 115)
        pygame.draw.ellipse(surface, border, rect, 2)

    def draw(self, surface, fonts, portrait_loader=None, player_portrait=None):
        title_font = fonts.get("title")
        label_font = fonts.get("label")
        detail_font = fonts.get("detail")
        small_font = fonts.get("small") or detail_font

        background = self._scaled_image(
            os.path.join(ASSET_ROOT, "background.png"),
            surface.get_size(),
        )
        if background is None:
            background = self._scaled_image(ARCADE_BACKGROUND_PATH, surface.get_size())
        if background is not None:
            surface.blit(background, (0, 0))
        else:
            surface.fill((10, 15, 24))

        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 82))
        surface.blit(shade, (0, 0))

        header = pygame.Rect(92, 18, surface.get_width() - 184, 112)
        header_panel = pygame.Surface(header.size, pygame.SRCALPHA)
        header_panel.fill((7, 13, 22, 230))
        surface.blit(header_panel, header.topleft)
        pygame.draw.rect(surface, (226, 194, 104), header, 3, border_radius=16)

        logo = self._scaled_image(
            os.path.join(ASSET_ROOT, "logo.png"),
            (356, 84),
        )
        if logo is not None:
            surface.blit(logo, logo.get_rect(midleft=(header.x + 24, header.centery)))
        else:
            title = title_font.render("BATTLE BOSSES", True, (250, 248, 239))
            surface.blit(title, title.get_rect(midleft=(header.x + 26, header.centery)))

        instruction = detail_font.render(
            "A/D or Left/Right moves your shield. Deflect the Joker and break all three rival forts.",
            True,
            (213, 220, 228),
        )
        surface.blit(
            instruction,
            instruction.get_rect(center=(header.x + 810, header.y + 42)),
        )
        difficulty_text = detail_font.render(
            f"{self.difficulty.get('label', self.difficulty_id.upper())}  -  x{self.ticket_multiplier:.2f} tickets",
            True,
            (255, 235, 147),
        )
        surface.blit(
            difficulty_text,
            difficulty_text.get_rect(center=(header.x + 810, header.y + 75)),
        )

        arena = self.ARENA_RECT
        arena_surface = pygame.Surface(arena.size, pygame.SRCALPHA)
        arena_surface.fill((5, 11, 19, 236))
        surface.blit(arena_surface, arena.topleft)
        pygame.draw.rect(surface, (204, 212, 224), arena, 3, border_radius=15)
        pygame.draw.line(surface, (63, 77, 94), arena.midtop, arena.midbottom, 1)
        pygame.draw.line(surface, (63, 77, 94), arena.midleft, arena.midright, 1)

        for fort in self.forts:
            center = fort["center"]
            center_xy = (int(center.x), int(center.y))
            hp = max(0, int(fort["hp"]))

            # Card-fort rings visualize remaining durability.
            for ring in range(self.MAX_HP):
                radius = 61 - ring * 7
                color = (224, 189, 97) if ring < hp else (58, 64, 73)
                pygame.draw.circle(surface, color, center_xy, radius, 4)

            self._draw_portrait(surface, fort, portrait_loader, player_portrait)

            shield_center, start, end, _radial = self._shield_geometry(fort)
            if hp > 0:
                shield_color = (105, 211, 236) if fort["index"] == 0 else (231, 111, 123)
                pygame.draw.line(
                    surface,
                    shield_color,
                    (int(start.x), int(start.y)),
                    (int(end.x), int(end.y)),
                    self.SHIELD_THICKNESS,
                )
                pygame.draw.line(
                    surface,
                    (247, 247, 241),
                    (int(start.x), int(start.y)),
                    (int(end.x), int(end.y)),
                    2,
                )

            # Keep names/HP outside the orbiting shield graphics. Top forts
            # use the slim row above the arena; bottom forts use the row below.
            is_left = "left" in fort["corner"]
            is_top = "top" in fort["corner"]
            status_width = 226
            status_height = 42
            status_x = arena.left if is_left else arena.right - status_width
            status_y = arena.top - 46 if is_top else arena.bottom + 7
            status_rect = pygame.Rect(status_x, status_y, status_width, status_height)
            plate = pygame.Surface(status_rect.size, pygame.SRCALPHA)
            plate.fill((7, 13, 21, 218))
            surface.blit(plate, status_rect.topleft)
            pygame.draw.rect(
                surface,
                (226, 194, 104) if hp > 0 else (96, 103, 114),
                status_rect,
                2,
                border_radius=8,
            )

            name = small_font.render(fort["name"], True, (236, 240, 243))
            max_name_width = status_width - 74
            if name.get_width() > max_name_width:
                ratio = max_name_width / max(1, name.get_width())
                name = pygame.transform.smoothscale(
                    name,
                    (max_name_width, max(1, int(round(name.get_height() * ratio)))),
                )
            hp_text = small_font.render(
                "KO" if hp <= 0 else f"{hp}/{self.MAX_HP}",
                True,
                (155, 160, 168) if hp <= 0 else (255, 234, 143),
            )
            surface.blit(name, name.get_rect(midleft=(status_rect.x + 12, status_rect.centery)))
            surface.blit(hp_text, hp_text.get_rect(midright=(status_rect.right - 12, status_rect.centery)))

        self._draw_ball(surface)

        if self._last_hit_text and pygame.time.get_ticks() <= self._hit_text_until:
            hit = detail_font.render(self._last_hit_text, True, (255, 236, 145))
            plate = hit.get_rect(center=(arena.centerx, arena.centery)).inflate(28, 14)
            overlay = pygame.Surface(plate.size, pygame.SRCALPHA)
            overlay.fill((7, 12, 20, 225))
            surface.blit(overlay, plate.topleft)
            pygame.draw.rect(surface, (226, 194, 104), plate, 2, border_radius=8)
            surface.blit(hit, hit.get_rect(center=plate.center))

        status_text = (
            self.winner_text
            if self.finished
            else f"Rivals eliminated: {self.rivals_eliminated}/3"
        )
        status = detail_font.render(status_text, True, (231, 235, 239))
        surface.blit(status, status.get_rect(center=(surface.get_width() // 2, 698)))

        if self.finished:
            hint = small_font.render(
                "Enter or Quit returns to Arcade Night. Space starts a rematch.",
                True,
                (192, 201, 211),
            )
            surface.blit(hint, hint.get_rect(center=(surface.get_width() // 2, 727)))
