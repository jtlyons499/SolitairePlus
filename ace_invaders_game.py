"""Playable Ace Invaders cabinet for Arcade Night.

The module owns the real-time shooter state and rendering. Career/token/ticket
settlement stays in main.py so Arcade Night remains the single economy owner.
"""
from __future__ import annotations

import os
import random

import pygame

from ace_invaders import ACE_INVADERS_DIFFICULTIES, get_ace_invaders_difficulty


ASSET_ROOT = os.path.join("assets", "arcade", "ace_invaders")
ARCADE_BACKGROUND = os.path.join("assets", "arcade", "bg.png")

PLAYFIELD_RECT = pygame.Rect(145, 168, 1076, 486)
PLAYER_SIZE = (64, 52)
ENEMY_SIZE = (48, 64)
PLAYER_BULLET_SIZE = (12, 24)
ENEMY_BULLET_SIZE = (8, 18)

STARTING_LIVES = 3
PLAYER_SPEED = 410.0
PLAYER_BULLET_SPEED = 610.0
WAVE_PAUSE_MS = 850
PLAYER_INVULNERABLE_MS = 900
ENEMY_EDGE_MARGIN = 18

# Four destructible bunkers sit between the player and the formation. Each
# bunker is built from individual blocks so damage is visibly carved out rather
# than represented by a generic health bar. A fresh set returns each wave.
SHIELD_BLOCK_SIZE = (12, 10)
SHIELD_COLUMNS = 8
SHIELD_ROWS = 4
SHIELD_Y = PLAYFIELD_RECT.bottom - 134
SHIELD_CENTERS_X = (
    PLAYFIELD_RECT.left + 170,
    PLAYFIELD_RECT.left + 415,
    PLAYFIELD_RECT.right - 415,
    PLAYFIELD_RECT.right - 170,
)

SUITS = ("spades", "hearts", "clubs", "diamonds")
SUIT_LABELS = {
    "spades": "S",
    "hearts": "H",
    "clubs": "C",
    "diamonds": "D",
}


class AceInvadersGame:
    def __init__(self):
        self._asset_cache = {}
        self._sound_events = []
        self._rng = random.Random()

        self.difficulty_id = "standard"
        self.difficulty_config = dict(ACE_INVADERS_DIFFICULTIES["standard"])
        self.ticket_multiplier = 1.0

        self.player_rect = pygame.Rect(0, 0, *PLAYER_SIZE)
        self.player_bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.shields = []

        self.score = 0
        self.starting_high_score = 0
        self.high_score = 0
        self.new_high_score = False
        self.lives = STARTING_LIVES
        self.wave = 1
        self.waves_cleared = 0
        self.enemies_destroyed = 0
        self.shots_fired = 0
        self.finished = False
        self.player_won = False
        self.forfeited = False
        self.reward_claimed = False

        self._formation_direction = 1
        self._last_player_shot_at = -99999
        self._last_enemy_shot_at = 0
        self._wave_resume_at = 0
        self._invulnerable_until = 0
        self._flash_message = ""
        self._flash_until = 0

        self._reset_player()

    def start_session(self, difficulty_id="standard", *, rng_seed=None, high_score=0):
        self.difficulty_id = (
            difficulty_id
            if difficulty_id in ACE_INVADERS_DIFFICULTIES
            else "standard"
        )
        self.difficulty_config = dict(get_ace_invaders_difficulty(self.difficulty_id))
        self.ticket_multiplier = float(
            self.difficulty_config.get("ticket_multiplier", 1.0)
        )

        if rng_seed is not None:
            self._rng.seed(rng_seed)

        self.score = 0
        try:
            self.starting_high_score = max(0, int(high_score or 0))
        except (TypeError, ValueError):
            self.starting_high_score = 0
        self.high_score = self.starting_high_score
        self.new_high_score = False
        self.lives = STARTING_LIVES
        self.wave = 1
        self.waves_cleared = 0
        self.enemies_destroyed = 0
        self.shots_fired = 0
        self.finished = False
        self.player_won = False
        self.forfeited = False
        self.reward_claimed = False

        self.player_bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.shields = []
        self._sound_events = []
        self._formation_direction = 1
        self._last_player_shot_at = -99999
        self._last_enemy_shot_at = 0
        self._wave_resume_at = 0
        self._invulnerable_until = 0
        self._flash_message = "WAVE 1"
        self._flash_until = pygame.time.get_ticks() + 900

        self._reset_player()
        self._spawn_wave()

    def _reset_player(self):
        self.player_rect.size = PLAYER_SIZE
        self.player_rect.midbottom = (
            PLAYFIELD_RECT.centerx,
            PLAYFIELD_RECT.bottom - 12,
        )

    def _reset_shields(self):
        """Build four fresh block bunkers in evenly spaced positions."""
        self.shields = []
        block_w, block_h = SHIELD_BLOCK_SIZE
        bunker_width = SHIELD_COLUMNS * block_w

        # A simple arch/notch silhouette inspired by classic arcade bunkers.
        # True means the block exists at the beginning of the wave.
        shape = (
            (False, True, True, True, True, True, True, False),
            (True, True, True, True, True, True, True, True),
            (True, True, True, True, True, True, True, True),
            (True, True, True, False, False, True, True, True),
        )

        for center_x in SHIELD_CENTERS_X:
            bunker = []
            left = int(center_x - bunker_width / 2)
            for row, row_data in enumerate(shape):
                for column, present in enumerate(row_data):
                    if not present:
                        continue
                    bunker.append(
                        pygame.Rect(
                            left + column * block_w,
                            SHIELD_Y + row * block_h,
                            block_w,
                            block_h,
                        )
                    )
            self.shields.append(bunker)

    def _damage_shield_at(self, rect, projectile_vy=0):
        """Remove the first bunker block reached by a projectile."""
        for bunker in self.shields:
            # Upward player fire reaches the lower face first; downward enemy
            # fire reaches the upper face first.
            ordered = sorted(
                bunker,
                key=lambda block: block.centery,
                reverse=(projectile_vy < 0),
            )
            for block in ordered:
                if rect.colliderect(block):
                    bunker.remove(block)
                    self._queue_sound("ace_invaders_shield_hit")
                    return True
        return False

    def _erode_shields_from_enemies(self):
        if not self.enemies or not self.shields:
            return
        for bunker in self.shields:
            if not bunker:
                continue
            bunker[:] = [
                block
                for block in bunker
                if not any(enemy["rect"].colliderect(block) for enemy in self.enemies)
            ]

    def _spawn_wave(self):
        self.player_bullets.clear()
        self.enemy_bullets.clear()
        self.enemies.clear()

        base_rows = max(2, int(self.difficulty_config.get("rows", 3)))
        base_columns = max(5, int(self.difficulty_config.get("columns", 8)))

        # Endless mode gradually fills the formation out before relying on
        # movement/fire speed for later difficulty. Caps keep the layout inside
        # the authored playfield on very long high-score runs.
        rows = min(5, base_rows + min(1, (self.wave - 1) // 5))
        columns = min(10, base_columns + min(2, (self.wave - 1) // 3))

        # Keep every difficulty comfortably inside the authored playfield while
        # making later waves spread slightly farther across the cabinet.
        horizontal_gap = min(
            82,
            max(58, int((PLAYFIELD_RECT.width - 170) / max(1, columns - 1))),
        )
        vertical_gap = 72
        total_width = (columns - 1) * horizontal_gap + ENEMY_SIZE[0]
        start_x = PLAYFIELD_RECT.centerx - total_width // 2
        start_y = PLAYFIELD_RECT.y + 44

        for row in range(rows):
            for column in range(columns):
                suit = SUITS[(row + column + self.wave - 1) % len(SUITS)]
                rect = pygame.Rect(
                    start_x + column * horizontal_gap,
                    start_y + row * vertical_gap,
                    *ENEMY_SIZE,
                )
                self.enemies.append({
                    "rect": rect,
                    "suit": suit,
                    "row": row,
                    "column": column,
                })

        self._formation_direction = 1
        self._last_enemy_shot_at = pygame.time.get_ticks()
        self._reset_shields()

    def forfeit(self):
        if self.finished:
            return
        self.forfeited = True
        self.finished = True
        self.player_won = False
        self._sound_events.clear()

    def pop_sound_events(self):
        events = list(self._sound_events)
        self._sound_events.clear()
        return events

    def _queue_sound(self, name):
        self._sound_events.append(str(name))

    def _fire_player(self, now):
        cooldown = max(120, int(self.difficulty_config.get("player_fire_ms", 245)))
        if now - self._last_player_shot_at < cooldown:
            return

        rect = pygame.Rect(0, 0, *PLAYER_BULLET_SIZE)
        rect.midbottom = (
            self.player_rect.centerx,
            self.player_rect.top + 5,
        )
        self.player_bullets.append({"rect": rect, "vy": -PLAYER_BULLET_SPEED})
        self._last_player_shot_at = now
        self.shots_fired += 1
        self._queue_sound("ace_invaders_shoot")

    def _bottom_shooters(self):
        """Return the lowest surviving Ace in each formation column."""
        by_column = {}
        for enemy in self.enemies:
            column = enemy["column"]
            previous = by_column.get(column)
            if previous is None or enemy["rect"].y > previous["rect"].y:
                by_column[column] = enemy
        return list(by_column.values())

    def _fire_enemy(self, now):
        interval = int(self.difficulty_config.get("enemy_fire_ms", 1125))
        # Endless waves increase pressure, but the floor prevents late runs
        # from degenerating into an unreadable wall of bullets.
        interval = max(320, interval - min(720, (self.wave - 1) * 65))
        if now - self._last_enemy_shot_at < interval:
            return

        shooters = self._bottom_shooters()
        if not shooters:
            return

        # Prefer an Ace reasonably near the player so shots feel intentional,
        # while keeping enough randomness for classic arcade movement.
        near_player = sorted(
            shooters,
            key=lambda enemy: abs(enemy["rect"].centerx - self.player_rect.centerx),
        )[:max(1, min(3, len(shooters)))]
        shooter = self._rng.choice(near_player)
        rect = pygame.Rect(0, 0, *ENEMY_BULLET_SIZE)
        rect.midtop = shooter["rect"].midbottom

        speed = float(self.difficulty_config.get("enemy_bullet_speed", 220.0))
        speed *= min(1.85, 1.0 + (self.wave - 1) * 0.045)
        self.enemy_bullets.append({"rect": rect, "vy": speed})
        self._last_enemy_shot_at = now
        self._queue_sound("ace_invaders_enemy_shoot")

    def _damage_player(self, now, *, formation_breach=False):
        if now < self._invulnerable_until or self.finished:
            return

        self.lives -= 1
        self._queue_sound("ace_invaders_player_hit")
        self._invulnerable_until = now + PLAYER_INVULNERABLE_MS
        self.player_bullets.clear()
        self.enemy_bullets.clear()
        self._reset_player()

        if self.lives <= 0:
            self.finished = True
            self.player_won = False
            self._flash_message = "GAME OVER"
            self._flash_until = now + 1500
            self._queue_sound("ace_invaders_loss")
            return

        self._flash_message = f"LIFE LOST - {self.lives} LEFT"
        self._flash_until = now + 850

        if formation_breach:
            # Pull the surviving formation back toward the top instead of
            # allowing one unlucky breach to chain through every remaining life.
            if self.enemies:
                top = min(enemy["rect"].top for enemy in self.enemies)
                correction = max(0, top - (PLAYFIELD_RECT.y + 44))
                for enemy in self.enemies:
                    enemy["rect"].y -= correction
                formation_bottom = max(enemy["rect"].bottom for enemy in self.enemies)
                if formation_bottom > PLAYFIELD_RECT.centery + 90:
                    shift = formation_bottom - (PLAYFIELD_RECT.centery + 90)
                    for enemy in self.enemies:
                        enemy["rect"].y -= shift

    def _complete_wave(self, now):
        # Ace Invaders is a true score-attack cabinet: there is no final wave.
        # Clearing a formation simply advances the difficulty curve and repairs
        # the four bunkers for the next wave.
        self.waves_cleared += 1
        self.wave += 1
        self._wave_resume_at = now + WAVE_PAUSE_MS
        self.player_bullets.clear()
        self.enemy_bullets.clear()
        self._flash_message = f"WAVE {self.wave}"
        self._flash_until = self._wave_resume_at + 500
        self._queue_sound("ace_invaders_wave_clear")

    def _move_formation(self, dt):
        if not self.enemies:
            return

        speed = float(self.difficulty_config.get("formation_speed", 68.0))
        speed *= min(2.15, 1.0 + (self.wave - 1) * 0.08)

        dx = speed * self._formation_direction * dt
        left_edge = min(enemy["rect"].left for enemy in self.enemies)
        right_edge = max(enemy["rect"].right for enemy in self.enemies)

        if (
            (self._formation_direction < 0 and left_edge + dx <= PLAYFIELD_RECT.left + ENEMY_EDGE_MARGIN)
            or
            (self._formation_direction > 0 and right_edge + dx >= PLAYFIELD_RECT.right - ENEMY_EDGE_MARGIN)
        ):
            self._formation_direction *= -1
            drop = int(self.difficulty_config.get("drop_distance", 22))
            drop += min(8, ((self.wave - 1) // 3) * 2)
            for enemy in self.enemies:
                enemy["rect"].y += drop
        else:
            for enemy in self.enemies:
                enemy["rect"].x += int(round(dx))

    def _update_bullets(self, dt, now):
        for bullet in self.player_bullets:
            bullet["rect"].y += int(round(bullet["vy"] * dt))
        for bullet in self.enemy_bullets:
            bullet["rect"].y += int(round(bullet["vy"] * dt))

        self.player_bullets = [
            bullet for bullet in self.player_bullets
            if bullet["rect"].bottom >= PLAYFIELD_RECT.top
        ]
        self.enemy_bullets = [
            bullet for bullet in self.enemy_bullets
            if bullet["rect"].top <= PLAYFIELD_RECT.bottom
        ]

        # Both sides can chew through the bunkers, matching the risk/reward of
        # the classic arcade shields: hiding behind them helps, but careless
        # rapid fire also opens holes for the Aces.
        surviving_player_bullets = []
        for bullet in self.player_bullets:
            if not self._damage_shield_at(bullet["rect"], bullet.get("vy", 0)):
                surviving_player_bullets.append(bullet)
        self.player_bullets = surviving_player_bullets

        surviving_enemy_bullets = []
        for bullet in self.enemy_bullets:
            if not self._damage_shield_at(bullet["rect"], bullet.get("vy", 0)):
                surviving_enemy_bullets.append(bullet)
        self.enemy_bullets = surviving_enemy_bullets

        hit_bullets = set()
        hit_enemies = set()
        for bullet_index, bullet in enumerate(self.player_bullets):
            for enemy_index, enemy in enumerate(self.enemies):
                if enemy_index in hit_enemies:
                    continue
                if bullet["rect"].colliderect(enemy["rect"]):
                    hit_bullets.add(bullet_index)
                    hit_enemies.add(enemy_index)
                    self.score += 10 + min(30, (self.wave - 1) * 2)
                    self.high_score = max(self.high_score, self.score)
                    if (
                            not self.new_high_score
                            and self.score > self.starting_high_score
                            and self.starting_high_score > 0
                    ):
                        self.new_high_score = True
                        self._flash_message = "NEW HIGH SCORE!"
                        self._flash_until = now + 1100
                    self.enemies_destroyed += 1
                    self._queue_sound("ace_invaders_enemy_hit")
                    break

        if hit_bullets:
            self.player_bullets = [
                bullet for index, bullet in enumerate(self.player_bullets)
                if index not in hit_bullets
            ]
        if hit_enemies:
            self.enemies = [
                enemy for index, enemy in enumerate(self.enemies)
                if index not in hit_enemies
            ]

        if now >= self._invulnerable_until:
            for bullet in list(self.enemy_bullets):
                if bullet["rect"].colliderect(self.player_rect):
                    self.enemy_bullets.remove(bullet)
                    self._damage_player(now)
                    break

    def update(self, dt, pressed_keys, now=None):
        if self.finished:
            return

        now = pygame.time.get_ticks() if now is None else int(now)
        try:
            dt = float(dt)
        except (TypeError, ValueError):
            dt = 1 / 60
        dt = max(1 / 240, min(dt, 1 / 20))

        move = 0
        if pressed_keys[pygame.K_a] or pressed_keys[pygame.K_LEFT]:
            move -= 1
        if pressed_keys[pygame.K_d] or pressed_keys[pygame.K_RIGHT]:
            move += 1

        self.player_rect.x += int(round(move * PLAYER_SPEED * dt))
        self.player_rect.left = max(PLAYFIELD_RECT.left + 14, self.player_rect.left)
        self.player_rect.right = min(PLAYFIELD_RECT.right - 14, self.player_rect.right)

        if pressed_keys[pygame.K_SPACE]:
            self._fire_player(now)

        if self._wave_resume_at:
            if now >= self._wave_resume_at:
                self._wave_resume_at = 0
                self._spawn_wave()
            return

        self._move_formation(dt)
        self._erode_shields_from_enemies()
        self._fire_enemy(now)
        self._update_bullets(dt, now)

        if not self.enemies and not self.finished:
            self._complete_wave(now)
            return

        if self.enemies:
            formation_bottom = max(enemy["rect"].bottom for enemy in self.enemies)
            if formation_bottom >= self.player_rect.top - 10:
                self._damage_player(now, formation_breach=True)

    @property
    def accuracy_percent(self):
        if self.shots_fired <= 0:
            return 0
        return int(round(100.0 * self.enemies_destroyed / self.shots_fired))

    def _load_image(self, path):
        if path in self._asset_cache:
            return self._asset_cache[path]
        try:
            image = pygame.image.load(path).convert_alpha()
        except (pygame.error, FileNotFoundError):
            image = None
        self._asset_cache[path] = image
        return image

    def _fit_image(self, path, size):
        cache_key = (path, tuple(size))
        if cache_key in self._asset_cache:
            return self._asset_cache[cache_key]

        source = self._load_image(path)
        if source is None:
            self._asset_cache[cache_key] = None
            return None

        width, height = source.get_size()
        if width <= 0 or height <= 0:
            self._asset_cache[cache_key] = None
            return None

        scale = min(size[0] / width, size[1] / height)
        fitted = pygame.transform.smoothscale(
            source,
            (
                max(1, int(round(width * scale))),
                max(1, int(round(height * scale))),
            ),
        )
        self._asset_cache[cache_key] = fitted
        return fitted

    def _draw_background(self, surface):
        background = self._load_image(os.path.join(ASSET_ROOT, "background.png"))
        if background is None:
            background = self._load_image(ARCADE_BACKGROUND)

        if background is not None:
            background = pygame.transform.smoothscale(background, surface.get_size())
            surface.blit(background, (0, 0))
            veil = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            veil.fill((3, 7, 18, 92))
            surface.blit(veil, (0, 0))
        else:
            surface.fill((4, 7, 20))

    def _draw_enemy(self, surface, enemy):
        suit = enemy["suit"]
        custom_path = os.path.join(ASSET_ROOT, f"ace_{suit}.png")
        image = self._fit_image(custom_path, enemy["rect"].size)

        if image is None:
            legacy_map = {
                "spades": os.path.join("assets", "cards", "fronts", "AS.png"),
                "hearts": os.path.join("assets", "cards", "fronts", "AH.png"),
                "clubs": os.path.join("assets", "cards", "fronts", "AC.png"),
                "diamonds": os.path.join("assets", "cards", "fronts", "AD.png"),
            }
            image = self._fit_image(legacy_map[suit], enemy["rect"].size)

        if image is not None:
            surface.blit(image, image.get_rect(center=enemy["rect"].center))
            return

        color = (215, 58, 64) if suit in ("hearts", "diamonds") else (232, 236, 244)
        pygame.draw.rect(surface, (18, 22, 32), enemy["rect"], border_radius=7)
        pygame.draw.rect(surface, color, enemy["rect"], 2, border_radius=7)
        font = pygame.font.Font(None, 34)
        glyph = font.render("A" + SUIT_LABELS[suit], True, color)
        surface.blit(glyph, glyph.get_rect(center=enemy["rect"].center))

    def _draw_player(self, surface, now):
        if now < self._invulnerable_until and (now // 90) % 2 == 0:
            return

        image = self._fit_image(
            os.path.join(ASSET_ROOT, "player_ship.png"),
            self.player_rect.size,
        )
        if image is not None:
            surface.blit(image, image.get_rect(center=self.player_rect.center))
            return

        points = (
            (self.player_rect.centerx, self.player_rect.top),
            (self.player_rect.left, self.player_rect.bottom),
            (self.player_rect.centerx, self.player_rect.bottom - 13),
            (self.player_rect.right, self.player_rect.bottom),
        )
        pygame.draw.polygon(surface, (114, 222, 238), points)
        pygame.draw.polygon(surface, (245, 245, 238), points, 2)

    def _draw_shields(self, surface):
        for bunker_index, bunker in enumerate(self.shields):
            # Subtle suit-family variation keeps the four bunkers readable
            # without requiring another art asset.
            colors = (
                (101, 224, 126),
                (112, 218, 155),
                (103, 210, 178),
                (119, 222, 135),
            )
            color = colors[bunker_index % len(colors)]
            for block in bunker:
                draw_rect = block.inflate(-2, -2)
                pygame.draw.rect(surface, color, draw_rect, border_radius=2)
                pygame.draw.line(
                    surface,
                    (205, 247, 210),
                    draw_rect.topleft,
                    (draw_rect.right - 1, draw_rect.top),
                    1,
                )

    def _draw_bullet(self, surface, bullet, player=True):
        if player:
            image = self._fit_image(
                os.path.join(ASSET_ROOT, "bullet.png"),
                bullet["rect"].size,
            )
            if image is not None:
                surface.blit(image, image.get_rect(center=bullet["rect"].center))
                return
            pygame.draw.rect(surface, (255, 231, 105), bullet["rect"], border_radius=4)
        else:
            pygame.draw.rect(surface, (237, 91, 98), bullet["rect"], border_radius=4)

    def draw(self, surface, fonts):
        now = pygame.time.get_ticks()
        self._draw_background(surface)

        title_font = fonts.get("title")
        label_font = fonts.get("label")
        detail_font = fonts.get("detail")
        small_font = fonts.get("small") or detail_font

        header = pygame.Rect(70, 32, 1226, 112)
        pygame.draw.rect(surface, (8, 14, 27), header, border_radius=15)
        pygame.draw.rect(surface, (219, 191, 102), header, 3, border_radius=15)

        logo = self._fit_image(os.path.join(ASSET_ROOT, "logo.png"), (360, 92))
        if logo is not None:
            surface.blit(logo, logo.get_rect(center=(252, header.centery)))
        elif title_font is not None:
            title = title_font.render("ACE INVADERS", True, (248, 247, 239))
            surface.blit(title, title.get_rect(center=(260, header.centery - 8)))

        difficulty = self.difficulty_config.get("label", self.difficulty_id.upper())
        if label_font is not None:
            hud_items = (
                (f"SCORE {self.score:,}", (255, 235, 136), 550),
                (f"HIGH {self.high_score:,}", (255, 214, 105), 760),
                (f"WAVE {self.wave}", (232, 238, 245), 985),
                (f"LIVES {self.lives}", (232, 238, 245), 1170),
            )
            for hud_text, hud_color, hud_x in hud_items:
                hud_surface = label_font.render(hud_text, True, hud_color)
                surface.blit(hud_surface, hud_surface.get_rect(center=(hud_x, 76)))

        if detail_font is not None:
            info = detail_font.render(
                f"{difficulty}  -  x{self.ticket_multiplier:.2f} tickets  -  ENDLESS SCORE ATTACK",
                True,
                (135, 220, 170),
            )
            surface.blit(info, info.get_rect(center=(896, 111)))

        pygame.draw.rect(surface, (3, 8, 19), PLAYFIELD_RECT, border_radius=13)
        pygame.draw.rect(surface, (190, 204, 222), PLAYFIELD_RECT, 3, border_radius=13)

        for enemy in self.enemies:
            self._draw_enemy(surface, enemy)
        self._draw_shields(surface)
        for bullet in self.player_bullets:
            self._draw_bullet(surface, bullet, player=True)
        for bullet in self.enemy_bullets:
            self._draw_bullet(surface, bullet, player=False)
        self._draw_player(surface, now)

        if self._wave_resume_at and detail_font is not None:
            wave_text = detail_font.render(
                f"Prepare for Wave {self.wave}",
                True,
                (255, 235, 140),
            )
            surface.blit(wave_text, wave_text.get_rect(center=PLAYFIELD_RECT.center))

        game_over_flash = self.finished and self._flash_message == "GAME OVER"
        flash_visible = (
            game_over_flash and (now // 450) % 2 == 0
        ) or (
            not game_over_flash and self._flash_message and now <= self._flash_until
        )
        if flash_visible and label_font is not None:
            flash = label_font.render(self._flash_message, True, (255, 238, 150))
            flash_center_y = PLAYFIELD_RECT.centery if game_over_flash else PLAYFIELD_RECT.y + 32
            box = flash.get_rect(center=(PLAYFIELD_RECT.centerx, flash_center_y)).inflate(36, 20)
            panel = pygame.Surface(box.size, pygame.SRCALPHA)
            panel.fill((6, 12, 25, 225))
            surface.blit(panel, box.topleft)
            pygame.draw.rect(surface, (220, 190, 100), box, 3 if game_over_flash else 2, border_radius=8)
            surface.blit(flash, flash.get_rect(center=box.center))

        footer = pygame.Rect(205, 674, 890, 58)
        pygame.draw.rect(surface, (8, 14, 27), footer, border_radius=12)
        pygame.draw.rect(surface, (92, 182, 215), footer, 2, border_radius=12)

        if detail_font is not None:
            if self.finished:
                record_note = "  NEW HIGH SCORE!" if self.score >= self.high_score and self.score > self.starting_high_score else ""
                result = (
                    f"GAME OVER  -  Score {self.score:,}  -  Wave {self.wave}  -  High {self.high_score:,}{record_note}"
                )
                text = detail_font.render(result, True, (235, 239, 244))
            else:
                text = detail_font.render(
                    "Use A/D or Left/Right to move. Space fires. Survive as long as you can.",
                    True,
                    (218, 225, 232),
                )
            surface.blit(text, text.get_rect(center=footer.center))
