"""King Pong: Arcade Night's card-themed paddle game."""
from __future__ import annotations

import os
import random

import pygame


ASSET_ROOT = os.path.join("assets", "arcade", "king_pong")
ARCADE_BACKGROUND_PATH = os.path.join("assets", "arcade", "bg.png")

KING_PONG_DIFFICULTIES = {
    "low": {
        "label": "LOW",
        "npc_tier": "low",
        "ticket_multiplier": 0.75,
        "npc_speed": 225,
        "npc_horizontal_speed": 145,
        "forward_aggression": 0.18,
        "tracking_error": 140.0,
        "deadzone": 28,
        "recenter_distance": 265,
    },
    "medium": {
        "label": "MEDIUM",
        "npc_tier": "mid",
        "ticket_multiplier": 1.00,
        "npc_speed": 285,
        "npc_horizontal_speed": 185,
        "forward_aggression": 0.28,
        "tracking_error": 102.0,
        "deadzone": 20,
        "recenter_distance": 215,
    },
    "high": {
        "label": "HIGH",
        "npc_tier": "strong",
        "ticket_multiplier": 1.35,
        "npc_speed": 350,
        "npc_horizontal_speed": 235,
        "forward_aggression": 0.42,
        "tracking_error": 68.0,
        "deadzone": 14,
        "recenter_distance": 160,
    },
    "expert": {
        "label": "EXPERT",
        "npc_tier": "elite",
        "ticket_multiplier": 1.75,
        "npc_speed": 420,
        "npc_horizontal_speed": 295,
        "forward_aggression": 0.56,
        "tracking_error": 40.0,
        "deadzone": 9,
        "recenter_distance": 112,
    },
}


class KingPongGame:
    """First-to-five paddle game with card-art paddles and a poker-chip ball."""

    PADDLE_SIZE = (54, 132)
    BALL_SIZE = (32, 32)
    PLAYER_VERTICAL_SPEED = 500.0
    PLAYER_HORIZONTAL_SPEED = 375.0
    PLAYER_ZONE_FRACTION = 0.30
    OPPONENT_ZONE_FRACTION = 0.30
    BALL_MAX_SPEED_X = 700.0
    POINT_PAUSE_MS = 700

    def __init__(self):
        self.playfield = pygame.Rect(92, 174, 1182, 451)
        self.player_paddle = pygame.Rect(0, 0, *self.PADDLE_SIZE)
        self.opponent_paddle = pygame.Rect(0, 0, *self.PADDLE_SIZE)
        self.ball_rect = pygame.Rect(0, 0, *self.BALL_SIZE)
        self.player_name = "You"
        self.opponent = None
        self.difficulty_id = "medium"
        self.target_score = 5
        self.player_score = 0
        self.opponent_score = 0
        self.finished = False
        self.reward_claimed = False
        self.forfeited = False
        self._npc_error = 0.0
        self._flash_until = 0
        self._last_scorer = None
        self._ball_velocity = pygame.Vector2(0, 0)
        self._player_motion_x = 0.0
        self._opponent_motion_x = 0.0
        self._winner_text = ""
        self._point_events = []
        self._serve_resume_at = 0
        self._pending_serve_to_player = None
        self._asset_cache = {}
        self._scaled_cache = {}
        self.reset_positions()

    @property
    def difficulty(self):
        return KING_PONG_DIFFICULTIES.get(
            self.difficulty_id,
            KING_PONG_DIFFICULTIES["medium"],
        )

    @property
    def ticket_multiplier(self):
        return float(self.difficulty.get("ticket_multiplier", 1.0))

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

    def _fit_image(self, path, bounds):
        """Scale an authored asset into bounds without distorting its aspect ratio."""
        image = self._load_image(path)
        if image is None:
            return None
        src_w, src_h = image.get_size()
        if src_w <= 0 or src_h <= 0:
            return None
        scale = min(bounds[0] / src_w, bounds[1] / src_h)
        size = (
            max(1, int(round(src_w * scale))),
            max(1, int(round(src_h * scale))),
        )
        return self._scaled_image(path, size)

    def _player_zone(self):
        width = int(round(self.playfield.width * self.PLAYER_ZONE_FRACTION))
        return pygame.Rect(
            self.playfield.left + 14,
            self.playfield.top + 8,
            width - 14,
            self.playfield.height - 16,
        )

    def _opponent_zone(self):
        width = int(round(self.playfield.width * self.OPPONENT_ZONE_FRACTION))
        return pygame.Rect(
            self.playfield.right - width,
            self.playfield.top + 8,
            width - 14,
            self.playfield.height - 16,
        )

    def reset_positions(self):
        player_zone = self._player_zone()
        opponent_zone = self._opponent_zone()
        self.player_paddle.midleft = (
            player_zone.left + 12,
            self.playfield.centery,
        )
        self.opponent_paddle.midright = (
            opponent_zone.right - 12,
            self.playfield.centery,
        )
        self.ball_rect.center = self.playfield.center
        self._player_motion_x = 0.0
        self._opponent_motion_x = 0.0
        self._flash_until = 0

    def _reroll_npc_error(self):
        spread = float(self.difficulty.get("tracking_error", 64.0))
        self._npc_error = random.uniform(-spread, spread)

    def reset_ball(self, serve_to_player=None):
        self.ball_rect.center = self.playfield.center
        direction = random.choice((-1, 1))
        if serve_to_player is True:
            direction = -1
        elif serve_to_player is False:
            direction = 1
        self._ball_velocity = pygame.Vector2(
            random.choice((385, 405, 425)) * direction,
            random.choice((-220, -180, -135, 135, 180, 220)),
        )
        self._reroll_npc_error()

    def start_match(
            self,
            opponent=None,
            *,
            difficulty_id="medium",
            target_score=5,
            player_name="You",
    ):
        self.player_name = str(player_name or "You")
        self.opponent = opponent or {"name": "Arcade Rival"}
        self.difficulty_id = (
            difficulty_id
            if difficulty_id in KING_PONG_DIFFICULTIES
            else "medium"
        )
        self.target_score = max(3, int(target_score or 5))
        self.player_score = 0
        self.opponent_score = 0
        self.finished = False
        self.reward_claimed = False
        self.forfeited = False
        self._winner_text = ""
        self._last_scorer = None
        self._point_events = []
        self._serve_resume_at = 0
        self._pending_serve_to_player = None
        self.reset_positions()
        self.reset_ball()

    def forfeit(self):
        if self.finished:
            return
        self.forfeited = True
        self.opponent_score = max(self.target_score, self.opponent_score)
        self.finished = True
        self._winner_text = f"{self.opponent_name} wins by forfeit"

    def pop_point_event(self):
        """Return the next completed point event exactly once."""
        if not self._point_events:
            return None
        return self._point_events.pop(0)

    @property
    def opponent_name(self):
        if isinstance(self.opponent, dict):
            return str(self.opponent.get("name") or "Arcade Rival")
        return "Arcade Rival"

    @property
    def player_won(self):
        return self.finished and self.player_score > self.opponent_score

    @staticmethod
    def _clamp_paddle_to_zone(paddle, zone):
        if paddle.left < zone.left:
            paddle.left = zone.left
        if paddle.right > zone.right:
            paddle.right = zone.right
        if paddle.top < zone.top:
            paddle.top = zone.top
        if paddle.bottom > zone.bottom:
            paddle.bottom = zone.bottom

    def update(self, dt, pressed_keys):
        if self.finished:
            return

        try:
            dt = float(dt)
        except (TypeError, ValueError):
            dt = 1 / 60
        dt = max(1 / 240, min(dt, 1 / 20))

        if self._serve_resume_at:
            if pygame.time.get_ticks() < self._serve_resume_at:
                return
            serve_to_player = self._pending_serve_to_player
            self._serve_resume_at = 0
            self._pending_serve_to_player = None
            self.reset_ball(serve_to_player=serve_to_player)

        vertical_direction = 0
        horizontal_direction = 0
        if pressed_keys[pygame.K_w] or pressed_keys[pygame.K_UP]:
            vertical_direction -= 1
        if pressed_keys[pygame.K_s] or pressed_keys[pygame.K_DOWN]:
            vertical_direction += 1
        if pressed_keys[pygame.K_a] or pressed_keys[pygame.K_LEFT]:
            horizontal_direction -= 1
        if pressed_keys[pygame.K_d] or pressed_keys[pygame.K_RIGHT]:
            horizontal_direction += 1

        # Normalize diagonals so WASD does not move faster at 45 degrees.
        if vertical_direction and horizontal_direction:
            diagonal_scale = 0.70710678
        else:
            diagonal_scale = 1.0

        player_dx = (
            horizontal_direction
            * self.PLAYER_HORIZONTAL_SPEED
            * diagonal_scale
            * dt
        )
        player_dy = (
            vertical_direction
            * self.PLAYER_VERTICAL_SPEED
            * diagonal_scale
            * dt
        )
        self.player_paddle.x += int(round(player_dx))
        self.player_paddle.y += int(round(player_dy))
        self._player_motion_x = (player_dx / dt) if dt > 0 else 0.0
        self._clamp_paddle_to_zone(self.player_paddle, self._player_zone())

        recenter_distance = int(self.difficulty.get("recenter_distance", 165))
        target_y = self.ball_rect.centery + self._npc_error
        if self.ball_rect.centerx < self.playfield.centerx - recenter_distance:
            target_y = self.playfield.centery

        npc_speed = float(self.difficulty.get("npc_speed", 355))
        deadzone = int(self.difficulty.get("deadzone", 12))
        npc_dy = 0.0
        if target_y > self.opponent_paddle.centery + deadzone:
            npc_dy = npc_speed * dt
        elif target_y < self.opponent_paddle.centery - deadzone:
            npc_dy = -npc_speed * dt
        self.opponent_paddle.y += int(round(npc_dy))

        # The rival can also move forward/back within its own side. Better
        # difficulties challenge the chip farther from their goal line.
        opponent_zone = self._opponent_zone()
        home_x = opponent_zone.right - self.opponent_paddle.width - 12
        aggression = float(self.difficulty.get("forward_aggression", 0.44))
        forward_x = int(round(
            opponent_zone.left
            + (opponent_zone.width - self.opponent_paddle.width)
            * (1.0 - aggression)
        ))
        ball_approaching = self._ball_velocity.x > 0
        ball_in_attack_range = self.ball_rect.centerx > self.playfield.centerx - recenter_distance
        target_x = forward_x if ball_approaching and ball_in_attack_range else home_x
        npc_horizontal_speed = float(self.difficulty.get("npc_horizontal_speed", 255))
        npc_dx = 0.0
        if target_x > self.opponent_paddle.x + deadzone:
            npc_dx = min(npc_horizontal_speed * dt, target_x - self.opponent_paddle.x)
        elif target_x < self.opponent_paddle.x - deadzone:
            npc_dx = -min(npc_horizontal_speed * dt, self.opponent_paddle.x - target_x)
        self.opponent_paddle.x += int(round(npc_dx))
        self._opponent_motion_x = (npc_dx / dt) if dt > 0 else 0.0
        self._clamp_paddle_to_zone(self.opponent_paddle, opponent_zone)

        self.ball_rect.x += int(round(self._ball_velocity.x * dt))
        self.ball_rect.y += int(round(self._ball_velocity.y * dt))

        if self.ball_rect.top <= self.playfield.top + 5:
            self.ball_rect.top = self.playfield.top + 5
            self._ball_velocity.y = abs(self._ball_velocity.y)
        elif self.ball_rect.bottom >= self.playfield.bottom - 5:
            self.ball_rect.bottom = self.playfield.bottom - 5
            self._ball_velocity.y = -abs(self._ball_velocity.y)

        if self.ball_rect.colliderect(self.player_paddle) and self._ball_velocity.x < 0:
            self.ball_rect.left = self.player_paddle.right
            offset = (
                self.ball_rect.centery - self.player_paddle.centery
            ) / max(1, self.player_paddle.height / 2)
            forward_boost = max(0.0, self._player_motion_x) * 0.28
            self._ball_velocity.x = min(
                self.BALL_MAX_SPEED_X,
                abs(self._ball_velocity.x) * 1.055 + forward_boost,
            )
            self._ball_velocity.y = max(
                -390,
                min(390, self._ball_velocity.y + offset * 145),
            )

        elif self.ball_rect.colliderect(self.opponent_paddle) and self._ball_velocity.x > 0:
            self.ball_rect.right = self.opponent_paddle.left
            offset = (
                self.ball_rect.centery - self.opponent_paddle.centery
            ) / max(1, self.opponent_paddle.height / 2)
            forward_boost = max(0.0, -self._opponent_motion_x) * 0.28
            self._ball_velocity.x = -min(
                self.BALL_MAX_SPEED_X,
                abs(self._ball_velocity.x) * 1.055 + forward_boost,
            )
            self._ball_velocity.y = max(
                -390,
                min(390, self._ball_velocity.y + offset * 145),
            )
            self._reroll_npc_error()

        if self.ball_rect.right < self.playfield.left:
            self._score_point(player_scored=False)
        elif self.ball_rect.left > self.playfield.right:
            self._score_point(player_scored=True)

    def _score_point(self, player_scored):
        if player_scored:
            self.player_score += 1
            self._last_scorer = self.player_name
            finished = self.player_score >= self.target_score
        else:
            self.opponent_score += 1
            self._last_scorer = self.opponent_name
            finished = self.opponent_score >= self.target_score

        self._point_events.append({
            "player_scored": bool(player_scored),
            "player_score": int(self.player_score),
            "opponent_score": int(self.opponent_score),
        })
        self._flash_until = pygame.time.get_ticks() + self.POINT_PAUSE_MS

        if finished:
            self.finished = True
            self._serve_resume_at = 0
            self._pending_serve_to_player = None
            self._ball_velocity.update(0, 0)
            if self.player_score > self.opponent_score:
                self._winner_text = (
                    f"{self.player_name} wins "
                    f"{self.player_score}-{self.opponent_score}!"
                )
            else:
                self._winner_text = (
                    f"{self.opponent_name} wins "
                    f"{self.opponent_score}-{self.player_score}."
                )
            return

        # Give the score a readable beat, reset both Kings to neutral positions,
        # then serve toward the player who conceded the point.
        scorer = self._last_scorer
        self.reset_positions()
        self._last_scorer = scorer
        self._flash_until = pygame.time.get_ticks() + self.POINT_PAUSE_MS
        self._ball_velocity.update(0, 0)
        self._pending_serve_to_player = bool(player_scored)
        self._serve_resume_at = pygame.time.get_ticks() + self.POINT_PAUSE_MS

    def _draw_score(self, surface, score, box, fallback_font):
        """Draw custom numeral art inside a fixed box so tall art cannot overlap."""
        score = max(0, min(self.target_score, int(score)))
        score_path = os.path.join(ASSET_ROOT, f"score_{score}.png")
        image = self._fit_image(score_path, box.size)
        if image is not None:
            surface.blit(image, image.get_rect(center=box.center))
            return

        rendered = fallback_font.render(str(score), True, (255, 239, 154))
        surface.blit(rendered, rendered.get_rect(center=box.center))

    def _draw_paddle(self, surface, rect, filename, fallback_color):
        image = self._scaled_image(
            os.path.join(ASSET_ROOT, filename),
            rect.size,
        )
        if image is not None:
            surface.blit(image, rect.topleft)
            return
        pygame.draw.rect(surface, fallback_color, rect, border_radius=8)
        pygame.draw.rect(surface, (245, 245, 245), rect, 2, border_radius=8)

    def _draw_ball(self, surface):
        image = self._scaled_image(
            os.path.join(ASSET_ROOT, "chip_ball.png"),
            self.ball_rect.size,
        )
        if image is not None:
            surface.blit(image, self.ball_rect.topleft)
            return
        pygame.draw.ellipse(surface, (250, 235, 140), self.ball_rect)
        pygame.draw.ellipse(surface, (255, 255, 255), self.ball_rect, 2)

    def _draw_logo(self, surface, rect, fallback_font):
        logo = self._fit_image(
            os.path.join(ASSET_ROOT, "logo.png"),
            (rect.width, rect.height),
        )
        if logo is None:
            logo = self._fit_image(
                os.path.join(ASSET_ROOT, "logo_old.png"),
                (rect.width, rect.height),
            )
        if logo is not None:
            surface.blit(logo, logo.get_rect(center=rect.center))
            return
        rendered = fallback_font.render("KING PONG", True, (248, 248, 244))
        surface.blit(rendered, rendered.get_rect(center=rect.center))

    def draw(self, surface, fonts, portrait_loader=None):
        title_font = fonts.get("title")
        label_font = fonts.get("label")
        detail_font = fonts.get("detail")
        small_font = fonts.get("small") or detail_font

        background = self._scaled_image(ARCADE_BACKGROUND_PATH, surface.get_size())
        if background is not None:
            surface.blit(background, (0, 0))
        else:
            surface.fill((11, 17, 28))

        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 62))
        surface.blit(shade, (0, 0))

        # Header is deliberately split into logo / scoreboard / rival zones.
        header = pygame.Rect(82, 22, 1202, 132)
        header_surface = pygame.Surface(header.size, pygame.SRCALPHA)
        header_surface.fill((7, 13, 23, 226))
        surface.blit(header_surface, header.topleft)
        pygame.draw.rect(surface, (229, 195, 101), header, 3, border_radius=16)

        logo_rect = pygame.Rect(112, 42, 330, 92)
        self._draw_logo(surface, logo_rect, title_font)

        # Center scoreboard: names above compact fixed score boxes.
        scoreboard = pygame.Rect(472, 38, 520, 104)
        pygame.draw.line(
            surface,
            (87, 105, 125),
            (scoreboard.left, scoreboard.bottom),
            (scoreboard.right, scoreboard.bottom),
            1,
        )

        player_name = label_font.render(self.player_name, True, (239, 243, 247))
        opponent_name = label_font.render(self.opponent_name, True, (239, 243, 247))
        surface.blit(
            player_name,
            player_name.get_rect(center=(scoreboard.x + 120, scoreboard.y + 24)),
        )
        surface.blit(
            opponent_name,
            opponent_name.get_rect(center=(scoreboard.right - 120, scoreboard.y + 24)),
        )

        player_box = pygame.Rect(scoreboard.x + 142, scoreboard.y + 43, 44, 50)
        opponent_box = pygame.Rect(scoreboard.right - 186, scoreboard.y + 43, 44, 50)
        self._draw_score(surface, self.player_score, player_box, title_font)
        self._draw_score(surface, self.opponent_score, opponent_box, title_font)

        versus = detail_font.render("VS", True, (168, 180, 193))
        surface.blit(
            versus,
            versus.get_rect(center=(scoreboard.centerx, scoreboard.y + 68)),
        )

        # NPC portrait and difficulty live in the right zone.
        portrait_rect = pygame.Rect(1138, 36, 78, 78)
        pygame.draw.ellipse(surface, (26, 38, 52), portrait_rect)
        if callable(portrait_loader):
            try:
                portrait = portrait_loader(self.opponent, 78)
            except Exception:
                portrait = None
            if portrait is not None:
                portrait = pygame.transform.smoothscale(portrait, portrait_rect.size)
                mask = pygame.Surface(portrait_rect.size, pygame.SRCALPHA)
                pygame.draw.ellipse(mask, (255, 255, 255, 255), mask.get_rect())
                clipped = portrait.copy()
                clipped.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                surface.blit(clipped, portrait_rect.topleft)
        pygame.draw.ellipse(surface, (229, 195, 101), portrait_rect, 2)

        difficulty_label = self.difficulty.get("label", "MEDIUM")
        multiplier = self.ticket_multiplier
        badge = small_font.render(
            f"{difficulty_label}  x{multiplier:.2f} tickets",
            True,
            (255, 232, 142),
        )
        surface.blit(
            badge,
            badge.get_rect(center=(portrait_rect.centerx, 130)),
        )

        # Main arcade screen.
        field = self.playfield
        field_surface = pygame.Surface(field.size, pygame.SRCALPHA)
        field_surface.fill((4, 8, 15, 238))
        surface.blit(field_surface, field.topleft)
        pygame.draw.rect(surface, (205, 213, 224), field, 3, border_radius=16)

        for dash_y in range(field.y + 16, field.bottom - 12, 36):
            pygame.draw.rect(
                surface,
                (155, 167, 183),
                pygame.Rect(field.centerx - 3, dash_y, 6, 20),
                border_radius=3,
            )

        self._draw_paddle(
            surface,
            self.player_paddle,
            "paddle_king_hearts.png",
            (81, 218, 237),
        )
        self._draw_paddle(
            surface,
            self.opponent_paddle,
            "paddle_king_spades.png",
            (235, 102, 110),
        )
        self._draw_ball(surface)

        if (
            self._flash_until > pygame.time.get_ticks()
            and self._last_scorer
            and detail_font is not None
        ):
            flash = detail_font.render(
                f"POINT - {self._last_scorer}",
                True,
                (255, 236, 142),
            )
            plate = flash.get_rect(center=(field.centerx, field.y + 30)).inflate(24, 12)
            overlay = pygame.Surface(plate.size, pygame.SRCALPHA)
            overlay.fill((10, 16, 26, 215))
            surface.blit(overlay, plate.topleft)
            surface.blit(flash, flash.get_rect(center=plate.center))

        footer = pygame.Rect(250, 648, 866, 72)
        footer_surface = pygame.Surface(footer.size, pygame.SRCALPHA)
        footer_surface.fill((7, 13, 23, 220))
        surface.blit(footer_surface, footer.topleft)
        pygame.draw.rect(surface, (91, 176, 208), footer, 2, border_radius=14)

        if self.finished:
            result = label_font.render(
                self._winner_text or "MATCH COMPLETE",
                True,
                (249, 242, 210),
            )
            surface.blit(result, result.get_rect(center=(footer.centerx, footer.y + 22)))
            prompt = small_font.render(
                "Enter: quit to Arcade Night   |   Space: rematch at the same difficulty",
                True,
                (202, 211, 221),
            )
            surface.blit(prompt, prompt.get_rect(center=(footer.centerx, footer.y + 50)))
        else:
            controls = small_font.render(
                "Use WASD or Arrow Keys to move. Keep the Joker chip in play. First to 5 wins.",
                True,
                (202, 211, 221),
            )
            surface.blit(controls, controls.get_rect(center=footer.center))
