from __future__ import annotations

import os
import pygame

from achievements import (
    ACHIEVEMENT_DEFINITIONS,
    get_progress_text,
    get_unlock_count,
)


BACK_RECT = pygame.Rect(1060, 680, 240, 50)
GRID_RECT = pygame.Rect(64, 176, 1238, 470)
CARD_W = 290
CARD_H = 140
CARD_GAP_X = 18
CARD_GAP_Y = 16
COLUMNS = 4
SCROLL_STEP = CARD_H + CARD_GAP_Y

_asset_cache = {}


def _load_optional(path):
    if path in _asset_cache:
        return _asset_cache[path]
    if not path or not os.path.exists(path):
        _asset_cache[path] = None
        return None
    try:
        surface = pygame.image.load(path).convert_alpha()
    except (pygame.error, OSError):
        surface = None
    _asset_cache[path] = surface
    return surface


def _fit(surface, max_size):
    if surface is None:
        return None
    width, height = surface.get_size()
    if width <= 0 or height <= 0:
        return surface
    scale = min(max_size[0] / width, max_size[1] / height)
    size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return pygame.transform.smoothscale(surface, size)


def get_max_scroll():
    rows = (len(ACHIEVEMENT_DEFINITIONS) + COLUMNS - 1) // COLUMNS
    content_height = rows * CARD_H + max(0, rows - 1) * CARD_GAP_Y
    return max(0, content_height - GRID_RECT.height)


def clamp_scroll(value):
    return max(0, min(int(value), get_max_scroll()))


def draw_achievements_screen(
        game_surface,
        mouse_pos,
        state,
        scroll_y,
        draw_submenu_background,
        draw_submenu_title,
        draw_menu_button,
        options_title_font,
        option_label_font,
        difficulty_detail_font,
):
    background = _load_optional("assets/achievements/background.png")
    if background is not None:
        game_surface.blit(
            pygame.transform.smoothscale(background, game_surface.get_size()),
            (0, 0),
        )
        veil = pygame.Surface(game_surface.get_size(), pygame.SRCALPHA)
        veil.fill((8, 10, 14, 74))
        game_surface.blit(veil, (0, 0))
    else:
        draw_submenu_background(overlay_alpha=150)

    title = _load_optional("assets/achievements/title.png")
    if title is not None:
        title = _fit(title, (520, 125))
        game_surface.blit(title, title.get_rect(center=(683, 75)))
    else:
        draw_submenu_title("ACHIEVEMENTS", y=45, width=500)

    unlocked = set((state or {}).get("unlocked", []))
    count = get_unlock_count(state)
    counter = option_label_font.render(
        f"{count} / {len(ACHIEVEMENT_DEFINITIONS)} unlocked",
        True,
        (230, 225, 205),
    )
    game_surface.blit(counter, counter.get_rect(center=(683, 142)))

    clip_before = game_surface.get_clip()
    game_surface.set_clip(GRID_RECT)

    for index, definition in enumerate(ACHIEVEMENT_DEFINITIONS):
        row = index // COLUMNS
        col = index % COLUMNS
        x = GRID_RECT.x + col * (CARD_W + CARD_GAP_X)
        y = GRID_RECT.y + row * (CARD_H + CARD_GAP_Y) - scroll_y
        rect = pygame.Rect(x, y, CARD_W, CARD_H)
        if rect.bottom < GRID_RECT.top or rect.top > GRID_RECT.bottom:
            continue

        is_unlocked = definition["id"] in unlocked
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((24, 29, 34, 235) if is_unlocked else (21, 23, 26, 220))
        border = (215, 177, 80) if is_unlocked else (102, 106, 111)
        pygame.draw.rect(panel, border, panel.get_rect(), 2, border_radius=9)
        game_surface.blit(panel, rect.topleft)

        icon_rect = pygame.Rect(rect.x + 12, rect.y + 15, 78, 78)
        icon = _load_optional(definition.get("icon"))
        if is_unlocked and icon is not None:
            icon = _fit(icon, icon_rect.size)
            game_surface.blit(icon, icon.get_rect(center=icon_rect.center))
        elif definition.get("secret") and not is_unlocked:
            pygame.draw.rect(game_surface, (48, 50, 54), icon_rect, border_radius=7)
            question = options_title_font.render("?", True, (205, 205, 205))
            game_surface.blit(question, question.get_rect(center=icon_rect.center))
        elif icon is not None:
            icon = _fit(icon, icon_rect.size)
            gray = icon.copy()
            gray.fill((115, 115, 115, 255), special_flags=pygame.BLEND_RGBA_MULT)
            game_surface.blit(gray, gray.get_rect(center=icon_rect.center))
        else:
            pygame.draw.rect(game_surface, (50, 53, 58), icon_rect, border_radius=7)

        title_text = definition["title"] if is_unlocked or not definition.get("secret") else "Secret Achievement"
        title_surface = option_label_font.render(title_text, True, (245, 232, 190) if is_unlocked else (190, 193, 198))
        if title_surface.get_width() > 180:
            scale = 180 / title_surface.get_width()
            title_surface = pygame.transform.smoothscale(
                title_surface,
                (180, max(1, int(title_surface.get_height() * scale))),
            )
        game_surface.blit(title_surface, (rect.x + 102, rect.y + 15))

        description = definition.get("description", "")
        if definition.get("secret") and not is_unlocked:
            description = definition.get("locked_description", "Secret achievement.")

        words = description.split()
        lines = []
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if difficulty_detail_font.size(candidate)[0] <= 172:
                line = candidate
            else:
                if line:
                    lines.append(line)
                line = word
            if len(lines) >= 3:
                break
        if line and len(lines) < 3:
            lines.append(line)

        for line_index, line_text in enumerate(lines[:3]):
            text = difficulty_detail_font.render(line_text, True, (204, 207, 212))
            game_surface.blit(text, (rect.x + 102, rect.y + 48 + line_index * 19))

        progress = get_progress_text(definition, state)
        if is_unlocked:
            progress = "UNLOCKED"
        if progress:
            progress_surface = difficulty_detail_font.render(
                progress,
                True,
                (232, 193, 86) if is_unlocked else (158, 164, 172),
            )
            game_surface.blit(progress_surface, (rect.x + 102, rect.bottom - 25))

        category_surface = difficulty_detail_font.render(
            definition.get("category", ""),
            True,
            (120, 175, 215),
        )
        game_surface.blit(category_surface, (rect.x + 13, rect.bottom - 27))

    game_surface.set_clip(clip_before)

    if get_max_scroll() > 0:
        scroll_hint = difficulty_detail_font.render(
            "Mouse wheel to scroll",
            True,
            (175, 178, 184),
        )
        game_surface.blit(scroll_hint, (72, 695))

    back_image = _load_optional("assets/achievements/back.png")
    if back_image is not None:
        button = pygame.transform.smoothscale(back_image, BACK_RECT.size)
        if mouse_pos is not None and BACK_RECT.collidepoint(mouse_pos):
            bright = button.copy()
            bright.fill((118, 118, 118, 255), special_flags=pygame.BLEND_RGBA_MULT)
            game_surface.blit(bright, BACK_RECT)
        else:
            game_surface.blit(button, BACK_RECT)
    else:
        draw_menu_button(BACK_RECT, "Back", mouse_pos, font=difficulty_detail_font)


def draw_achievement_popup(
        game_surface,
        definition,
        elapsed_ms,
        fan_reward=0,
        cosmetic_label="",
        option_label_font=None,
        difficulty_detail_font=None,
):
    if not definition:
        return

    duration = 4400
    if elapsed_ms >= duration:
        return

    fade_start = 3500
    alpha = 255
    if elapsed_ms > fade_start:
        alpha = int(255 * max(0.0, (duration - elapsed_ms) / (duration - fade_start)))

    frame_rect = pygame.Rect(790, 28, 540, 154)
    frame = _load_optional("assets/achievements/unlock_frame.png")
    if frame is not None:
        frame = pygame.transform.smoothscale(frame, frame_rect.size)
        frame.set_alpha(alpha)
        game_surface.blit(frame, frame_rect)
    else:
        panel = pygame.Surface(frame_rect.size, pygame.SRCALPHA)
        panel.fill((17, 20, 24, min(alpha, 238)))
        pygame.draw.rect(panel, (225, 181, 66, alpha), panel.get_rect(), 3, border_radius=12)
        game_surface.blit(panel, frame_rect)

    icon = _load_optional(definition.get("icon"))
    icon_rect = pygame.Rect(frame_rect.x + 18, frame_rect.y + 27, 96, 96)
    if icon is not None:
        icon = _fit(icon, icon_rect.size)
        icon.set_alpha(alpha)
        game_surface.blit(icon, icon.get_rect(center=icon_rect.center))

    if option_label_font is None or difficulty_detail_font is None:
        return

    lines = [
        ("ACHIEVEMENT UNLOCKED", option_label_font, (245, 202, 78)),
        (definition.get("title", "Achievement"), option_label_font, (248, 248, 245)),
    ]
    if fan_reward:
        lines.append((f"+{fan_reward:,} Fans", difficulty_detail_font, (150, 220, 166)))
    if cosmetic_label:
        lines.append((f"Reward: {cosmetic_label}", difficulty_detail_font, (207, 207, 220)))

    y = frame_rect.y + 24
    for text, font, color in lines:
        surface = font.render(text, True, color)
        surface.set_alpha(alpha)
        game_surface.blit(surface, (frame_rect.x + 132, y))
        y += surface.get_height() + 6
