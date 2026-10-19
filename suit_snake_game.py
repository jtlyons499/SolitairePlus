"""Playable Suit Snake cabinet for Arcade Night.

Suit Snake follows a fixed deck sequence:
2S, 2D, 2C, 2H, 3S ... through AH. Completing the deck starts the
sequence again while the snake keeps growing.

Four cabinet modes control grid size and border behavior. Movement presentation
is selected separately: Step Movement keeps the classic tile-by-tile look,
while Smooth Movement interpolates the same grid simulation between steps.
Career/token/ticket settlement stays in main.py.
"""
from __future__ import annotations

import os
import random

import pygame

from suit_snake import (
    CARD_SEQUENCE,
    SUIT_SNAKE_MODES,
    SUIT_SNAKE_MOVEMENT_STYLES,
    get_suit_snake_mode,
    get_suit_snake_movement_style,
    sequence_card,
)


ASSET_ROOT = os.path.join("assets", "arcade", "suit_snake")
ARCADE_BACKGROUND = os.path.join("assets", "arcade", "bg.png")

BASE_WIDTH = 1366
STANDARD_PLAYFIELD_TOP = 204
BIG_PLAYFIELD_TOP = 184

SUIT_SYMBOLS = {
    "spades": "S",
    "diamonds": "D",
    "clubs": "C",
    "hearts": "H",
}

SUIT_COLORS = {
    "spades": (30, 35, 43),
    "clubs": (30, 35, 43),
    "diamonds": (205, 54, 62),
    "hearts": (205, 54, 62),
}

DIRECTION_VECTORS = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}

OPPOSITE_DIRECTION = {
    "up": "down",
    "down": "up",
    "left": "right",
    "right": "left",
}


class SuitSnakeGame:
    def __init__(self):
        self._asset_cache = {}
        self._sound_events = []
        self._rng = random.Random()

        self.mode_id = "classic_standard"
        self.mode_config = dict(SUIT_SNAKE_MODES["classic_standard"])
        # Kept as an alias so generic Arcade result code from older builds
        # continues to work.
        self.difficulty_id = self.mode_id
        self.difficulty_config = self.mode_config
        self.ticket_multiplier = 1.0

        self.movement_style = "step"
        self.movement_config = dict(SUIT_SNAKE_MOVEMENT_STYLES["step"])

        self.grid_columns = 24
        self.grid_rows = 13
        self.cell_size = 32
        self.wraparound = False
        self.playfield_rect = pygame.Rect(299, STANDARD_PLAYFIELD_TOP, 768, 416)

        self.snake = [self._start_cell()]
        self.collected_cards = []
        self.direction = None
        self.pending_direction = None
        self.started = False
        self.target_cell = (self.snake[0][0] + 5, self.snake[0][1])
        self.target_index = 0

        self.score = 0
        self.starting_high_score = 0
        self.high_score = 0
        self.new_high_score = False
        self.cards_collected = 0
        self.decks_completed = 0
        self.finished = False
        self.forfeited = False
        self.reward_claimed = False

        self._last_step_at = 0
        self._render_step_started_at = 0
        self._render_from_cells = list(self.snake)
        self._flash_message = ""
        self._flash_until = 0

    def _start_cell(self):
        return (self.grid_columns // 2, self.grid_rows // 2)

    def _configure_board(self):
        self.grid_columns = max(8, int(self.mode_config.get("grid_columns", 24)))
        self.grid_rows = max(6, int(self.mode_config.get("grid_rows", 13)))
        self.cell_size = max(18, int(self.mode_config.get("cell_size", 32)))
        self.wraparound = bool(self.mode_config.get("wraparound", False))

        width = self.grid_columns * self.cell_size
        height = self.grid_rows * self.cell_size
        top = BIG_PLAYFIELD_TOP if self.grid_rows > 13 else STANDARD_PLAYFIELD_TOP
        self.playfield_rect = pygame.Rect(
            (BASE_WIDTH - width) // 2,
            top,
            width,
            height,
        )

    @property
    def chain_length(self):
        return len(self.snake)

    @property
    def next_card(self):
        return sequence_card(self.target_index)

    def start_session(
        self,
        mode_id="classic_standard",
        *,
        movement_style="step",
        rng_seed=None,
        high_score=0,
        difficulty_id=None,
    ):
        # difficulty_id is accepted for compatibility with an older caller.
        if difficulty_id is not None and mode_id == "classic_standard":
            mode_id = difficulty_id

        self.mode_id = mode_id if mode_id in SUIT_SNAKE_MODES else "classic_standard"
        self.mode_config = dict(get_suit_snake_mode(self.mode_id))
        self.difficulty_id = self.mode_id
        self.difficulty_config = self.mode_config
        self.ticket_multiplier = float(self.mode_config.get("ticket_multiplier", 1.0))

        self.movement_style = (
            movement_style
            if movement_style in SUIT_SNAKE_MOVEMENT_STYLES
            else "step"
        )
        self.movement_config = dict(
            get_suit_snake_movement_style(self.movement_style)
        )
        self._configure_board()

        if rng_seed is not None:
            self._rng.seed(rng_seed)

        try:
            self.starting_high_score = max(0, int(high_score or 0))
        except (TypeError, ValueError):
            self.starting_high_score = 0

        self.high_score = self.starting_high_score
        self.new_high_score = False
        self.snake = [self._start_cell()]
        self.collected_cards = []
        self.direction = None
        self.pending_direction = None
        self.started = False
        self.target_index = 0
        self.score = 0
        self.cards_collected = 0
        self.decks_completed = 0
        self.finished = False
        self.forfeited = False
        self.reward_claimed = False
        self._sound_events = []

        now = pygame.time.get_ticks()
        self._last_step_at = now
        self._render_step_started_at = now
        self._render_from_cells = list(self.snake)
        self._flash_message = "PRESS A GAMEPLAY KEY TO START"
        self._flash_until = now + 999999
        self._place_target()

    def forfeit(self):
        if self.finished:
            return
        self.forfeited = True
        self.finished = True
        self._sound_events.clear()

    def pop_sound_events(self):
        events = list(self._sound_events)
        self._sound_events.clear()
        return events

    def _queue_sound(self, name):
        self._sound_events.append(str(name))

    def _start_movement(self, direction, now=None):
        if direction not in DIRECTION_VECTORS or self.finished:
            return False
        if now is None:
            now = pygame.time.get_ticks()

        self.started = True
        self.direction = direction
        self.pending_direction = direction
        self._last_step_at = now
        self._render_step_started_at = now
        self._render_from_cells = list(self.snake)
        self._flash_message = ""
        self._flash_until = 0
        return True

    def _read_direction(self, pressed_keys):
        requested = None
        if pressed_keys[pygame.K_w] or pressed_keys[pygame.K_UP]:
            requested = "up"
        elif pressed_keys[pygame.K_s] or pressed_keys[pygame.K_DOWN]:
            requested = "down"
        elif pressed_keys[pygame.K_a] or pressed_keys[pygame.K_LEFT]:
            requested = "left"
        elif pressed_keys[pygame.K_d] or pressed_keys[pygame.K_RIGHT]:
            requested = "right"

        if requested is None:
            return
        if not self.started:
            self._start_movement(requested)
            return
        if requested == OPPOSITE_DIRECTION.get(self.direction):
            return
        self.pending_direction = requested

    def queue_direction(self, direction):
        """Keyboard-event friendly direction setter used by integration/tests."""
        if direction not in DIRECTION_VECTORS or self.finished:
            return False
        if not self.started:
            return self._start_movement(direction)
        if direction == OPPOSITE_DIRECTION.get(self.direction):
            return False
        self.pending_direction = direction
        return True

    def _place_target(self):
        occupied = set(self.snake)
        free_cells = [
            (x, y)
            for y in range(self.grid_rows)
            for x in range(self.grid_columns)
            if (x, y) not in occupied
        ]
        if not free_cells:
            self.finished = True
            self._flash_message = "DECK MASTER!"
            self._flash_until = pygame.time.get_ticks() + 999999
            return
        self.target_cell = self._rng.choice(free_cells)

    def _collect_target(self):
        rank, suit, deck_number = self.next_card
        self.collected_cards.append((rank, suit, deck_number))
        self.cards_collected += 1
        self.target_index += 1

        self.score += 100
        if self.cards_collected % 4 == 0:
            self.score += 50
            self._flash_message = f"{rank} SET COMPLETE"
            self._flash_until = pygame.time.get_ticks() + 650

        if self.cards_collected % len(CARD_SEQUENCE) == 0:
            self.decks_completed += 1
            self.score += 1000
            self._flash_message = f"DECK {self.decks_completed} COMPLETE!"
            self._flash_until = pygame.time.get_ticks() + 1100
            self._queue_sound("suit_snake_deck")
        else:
            self._queue_sound("suit_snake_collect")

        if self.score > self.high_score:
            if (
                self.high_score == self.starting_high_score
                and self.score > self.starting_high_score
            ):
                self.new_high_score = True
            self.high_score = self.score

        self._place_target()

    def _finish_collision(self):
        self.finished = True
        self._flash_message = "GAME OVER"
        self._flash_until = pygame.time.get_ticks() + 999999
        self._queue_sound("suit_snake_loss")

    def _step(self, step_time=None):
        if self.finished or not self.started or self.direction is None:
            return

        if step_time is None:
            step_time = pygame.time.get_ticks()

        if self.pending_direction != OPPOSITE_DIRECTION.get(self.direction):
            self.direction = self.pending_direction

        dx, dy = DIRECTION_VECTORS[self.direction]
        head_x, head_y = self.snake[0]
        new_x = head_x + dx
        new_y = head_y + dy

        if self.wraparound:
            new_x %= self.grid_columns
            new_y %= self.grid_rows
        elif (
            new_x < 0
            or new_x >= self.grid_columns
            or new_y < 0
            or new_y >= self.grid_rows
        ):
            self._finish_collision()
            return

        new_head = (new_x, new_y)
        growing = new_head == self.target_cell
        body_to_check = self.snake if growing else self.snake[:-1]
        if new_head in body_to_check:
            self._finish_collision()
            return

        old_snake = list(self.snake)
        self.snake.insert(0, new_head)
        if growing:
            self._collect_target()
        else:
            self.snake.pop()

        # Each current segment begins its visual trip from the previous
        # segment's old cell. This preserves the familiar "follow the leader"
        # Snake motion while allowing interpolation in Smooth Movement.
        render_from = []
        for index in range(len(self.snake)):
            if not old_snake:
                render_from.append(self.snake[index])
            elif index == 0:
                render_from.append(old_snake[0])
            else:
                render_from.append(old_snake[min(index - 1, len(old_snake) - 1)])
        self._render_from_cells = render_from
        self._render_step_started_at = int(step_time)

    def update(self, dt, pressed_keys, now=None):
        del dt  # Grid simulation cadence is independent of frame rate.
        if self.finished:
            return

        if now is None:
            now = pygame.time.get_ticks()

        self._read_direction(pressed_keys)
        if not self.started:
            return

        step_ms = max(55, int(self.mode_config.get("step_ms", 165)))
        # Catch up at most two cells after a frame hitch.
        steps_due = min(2, max(0, (now - self._last_step_at) // step_ms))
        for _ in range(int(steps_due)):
            self._last_step_at += step_ms
            self._step(step_time=self._last_step_at)
            if self.finished:
                break

    @property
    def accuracy_percent(self):
        return round(
            (self.target_index % len(CARD_SEQUENCE))
            / len(CARD_SEQUENCE)
            * 100.0,
            1,
        )

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
        key = (path, tuple(size))
        if key in self._asset_cache:
            return self._asset_cache[key]
        source = self._load_image(path)
        if source is None:
            self._asset_cache[key] = None
            return None
        sw, sh = source.get_size()
        tw, th = size
        scale = min(tw / max(1, sw), th / max(1, sh))
        scaled = pygame.transform.smoothscale(
            source,
            (max(1, int(sw * scale)), max(1, int(sh * scale))),
        )
        self._asset_cache[key] = scaled
        return scaled

    def _draw_background(self, surface):
        image = self._fit_image(
            os.path.join(ASSET_ROOT, "background.png"),
            surface.get_size(),
        )
        if image is None:
            image = self._fit_image(ARCADE_BACKGROUND, surface.get_size())
        if image is not None:
            surface.blit(image, image.get_rect(center=surface.get_rect().center))
        else:
            surface.fill((5, 12, 19))

    def _cell_rect(self, cell):
        x, y = cell
        return pygame.Rect(
            round(self.playfield_rect.left + x * self.cell_size),
            round(self.playfield_rect.top + y * self.cell_size),
            self.cell_size,
            self.cell_size,
        )

    def _interpolated_cell(self, index, now):
        current = self.snake[index]
        if (
            self.movement_style != "smooth"
            or not self.started
            or index >= len(self._render_from_cells)
        ):
            return current

        step_ms = max(55, int(self.mode_config.get("step_ms", 165)))
        progress = max(
            0.0,
            min(1.0, (now - self._render_step_started_at) / float(step_ms)),
        )
        start_x, start_y = self._render_from_cells[index]
        target_x, target_y = current

        if self.wraparound:
            dx = target_x - start_x
            dy = target_y - start_y
            if dx > self.grid_columns / 2:
                target_x -= self.grid_columns
            elif dx < -self.grid_columns / 2:
                target_x += self.grid_columns
            if dy > self.grid_rows / 2:
                target_y -= self.grid_rows
            elif dy < -self.grid_rows / 2:
                target_y += self.grid_rows

        draw_x = start_x + (target_x - start_x) * progress
        draw_y = start_y + (target_y - start_y) * progress

        if self.wraparound:
            draw_x %= self.grid_columns
            draw_y %= self.grid_rows
        return draw_x, draw_y

    @staticmethod
    def _draw_card_token(surface, rect, rank, suit, *, head=False, target=False):
        center = rect.center
        radius = max(8, min(rect.width, rect.height) // 2 - 3)

        if target:
            pygame.draw.circle(surface, (245, 214, 100), center, radius + 4, 3)

        fill = (251, 247, 229) if not head else (255, 236, 142)
        pygame.draw.circle(surface, fill, center, radius)
        pygame.draw.circle(surface, (17, 22, 28), center, radius, 2)

        suit_color = SUIT_COLORS.get(suit, (28, 32, 38))
        symbol = SUIT_SYMBOLS.get(suit, "?")
        rank_font = pygame.font.SysFont(
            None,
            14 if rect.width < 30 or len(str(rank)) > 1 else 17,
            bold=True,
        )
        suit_font = pygame.font.SysFont(
            None,
            14 if rect.width < 30 else 16,
            bold=True,
        )

        rank_surface = rank_font.render(str(rank), True, suit_color)
        suit_surface = suit_font.render(symbol, True, suit_color)
        vertical_scale = rect.height / 32.0
        surface.blit(
            rank_surface,
            rank_surface.get_rect(
                center=(center[0], center[1] - round(6 * vertical_scale))
            ),
        )
        surface.blit(
            suit_surface,
            suit_surface.get_rect(
                center=(center[0], center[1] + round(7 * vertical_scale))
            ),
        )

    def _draw_snake(self, surface, now):
        for index in range(len(self.snake) - 1, -1, -1):
            cell = self._interpolated_cell(index, now)
            rect = self._cell_rect(cell)

            if self.collected_cards:
                card_index = max(0, len(self.collected_cards) - 1 - index)
                rank, suit, _deck_number = self.collected_cards[card_index]
            else:
                rank, suit = "2", "spades"

            self._draw_card_token(
                surface,
                rect,
                rank,
                suit,
                head=(index == 0),
            )

    def draw(self, surface, fonts):
        now = pygame.time.get_ticks()
        self._draw_background(surface)

        title_font = fonts.get("title")
        label_font = fonts.get("label")
        detail_font = fonts.get("detail")
        small_font = fonts.get("small") or detail_font

        header = pygame.Rect(70, 28, 1226, 132)
        pygame.draw.rect(surface, (8, 14, 24), header, border_radius=15)
        pygame.draw.rect(surface, (219, 191, 102), header, 3, border_radius=15)

        logo = self._fit_image(os.path.join(ASSET_ROOT, "logo.png"), (360, 105))
        if logo is not None:
            surface.blit(logo, logo.get_rect(center=(252, header.centery)))
        elif title_font is not None:
            title = title_font.render("SUIT SNAKE", True, (248, 247, 239))
            surface.blit(title, title.get_rect(center=(250, header.centery - 5)))

        mode_label = self.mode_config.get("label", self.mode_id.upper())
        movement_label = self.movement_config.get("label", self.movement_style.upper())
        rank, suit, deck_number = self.next_card
        next_text = f"{rank}{SUIT_SYMBOLS.get(suit, '?')}"

        if label_font is not None:
            hud_items = (
                (f"SCORE {self.score:,}", (255, 235, 136), 535),
                (f"HIGH {self.high_score:,}", (255, 214, 105), 735),
                (f"NEXT {next_text}", (232, 238, 245), 930),
                (f"LENGTH {self.cards_collected + 1}", (232, 238, 245), 1145),
            )
            for hud_text, hud_color, hud_x in hud_items:
                rendered = label_font.render(hud_text, True, hud_color)
                surface.blit(rendered, rendered.get_rect(center=(hud_x, 72)))

        if detail_font is not None:
            info = detail_font.render(
                f"{mode_label}  -  {movement_label}  -  DECK {deck_number}",
                True,
                (135, 220, 170),
            )
            surface.blit(info, info.get_rect(center=(850, 118)))

        pygame.draw.rect(surface, (4, 12, 13), self.playfield_rect, border_radius=12)
        pygame.draw.rect(
            surface,
            (188, 205, 210),
            self.playfield_rect,
            3,
            border_radius=12,
        )

        for x in range(1, self.grid_columns):
            px = self.playfield_rect.left + x * self.cell_size
            pygame.draw.line(
                surface,
                (17, 34, 35),
                (px, self.playfield_rect.top),
                (px, self.playfield_rect.bottom),
            )
        for y in range(1, self.grid_rows):
            py = self.playfield_rect.top + y * self.cell_size
            pygame.draw.line(
                surface,
                (17, 34, 35),
                (self.playfield_rect.left, py),
                (self.playfield_rect.right, py),
            )

        self._draw_snake(surface, now)

        target_rect = self._cell_rect(self.target_cell)
        target_rank, target_suit, _target_deck = self.next_card
        self._draw_card_token(
            surface,
            target_rect,
            target_rank,
            target_suit,
            target=True,
        )

        game_over_flash = self.finished and self._flash_message == "GAME OVER"
        start_prompt = not self.started and not self.finished
        flash_visible = (
            game_over_flash and (now // 450) % 2 == 0
        ) or start_prompt or (
            not game_over_flash
            and self._flash_message
            and now <= self._flash_until
        )
        if flash_visible and label_font is not None:
            message = (
                "PRESS WASD OR ARROW KEY TO START"
                if start_prompt
                else self._flash_message
            )
            flash = label_font.render(message, True, (255, 238, 150))
            box = flash.get_rect(center=self.playfield_rect.center).inflate(38, 22)
            panel = pygame.Surface(box.size, pygame.SRCALPHA)
            panel.fill((6, 12, 18, 225))
            surface.blit(panel, box.topleft)
            pygame.draw.rect(
                surface,
                (220, 190, 100),
                box,
                3 if game_over_flash or start_prompt else 2,
                border_radius=8,
            )
            surface.blit(flash, flash.get_rect(center=box.center))

        footer_top = min(650, self.playfield_rect.bottom + 18)
        footer = pygame.Rect(220, footer_top, 925, 66)
        pygame.draw.rect(surface, (8, 14, 24), footer, border_radius=12)
        pygame.draw.rect(surface, (92, 182, 215), footer, 2, border_radius=12)

        if detail_font is not None:
            if self.finished:
                record_note = "  NEW HIGH SCORE!" if self.new_high_score else ""
                footer_text = (
                    f"GAME OVER  -  Score {self.score:,}  -  Cards {self.cards_collected}"
                    f"  -  High {self.high_score:,}{record_note}"
                )
            elif not self.started:
                footer_text = (
                    "Choose your opening direction with WASD or Arrow Keys. "
                    "The run will not begin until you press one."
                )
            else:
                border_text = (
                    "Edges wrap to the opposite side."
                    if self.wraparound
                    else "Borders end the run."
                )
                footer_text = (
                    "Collect cards in order: 2S, 2D, 2C, 2H, then 3S...  "
                    + border_text
                )
            rendered = detail_font.render(footer_text, True, (218, 225, 232))
            surface.blit(rendered, rendered.get_rect(center=footer.center))
