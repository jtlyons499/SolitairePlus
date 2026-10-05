import os
import pygame


BASE_WIDTH = 1366
BASE_HEIGHT = 768

HEAD_TO_HEAD_RETURN_RECT = pygame.Rect(148, 646, 250, 62)
HEAD_TO_HEAD_START_RECT = pygame.Rect(968, 646, 250, 62)

OPPONENT_CARD_RECTS = [
    pygame.Rect(120 + index * 286, 210, 258, 360)
    for index in range(4)
]

_asset_cache = {}


def _load_asset(path, size=None):
    if not path:
        return None
    key = (path, tuple(size) if size else None)
    if key in _asset_cache:
        return _asset_cache[key]
    try:
        image = pygame.image.load(path).convert_alpha()
        if size:
            image = pygame.transform.smoothscale(image, size)
    except (pygame.error, FileNotFoundError):
        image = None
    _asset_cache[key] = image
    return image


def _draw_button(surface, rect, path, fallback_text, font, mouse_pos, enabled=True):
    image = _load_asset(path, rect.size)
    hovered = enabled and mouse_pos is not None and rect.collidepoint(mouse_pos)

    if image is not None:
        button = image.copy()
        if hovered:
            button.fill((24, 24, 24, 0), special_flags=pygame.BLEND_RGBA_ADD)
        if not enabled:
            button.fill((105, 105, 105, 255), special_flags=pygame.BLEND_RGBA_MULT)
            button.set_alpha(155)
        surface.blit(button, rect.topleft)
        return

    fill = (62, 92, 78) if enabled else (48, 52, 50)
    if hovered:
        fill = (77, 112, 92)
    pygame.draw.rect(surface, fill, rect, border_radius=10)
    pygame.draw.rect(surface, (228, 211, 142), rect, 2, border_radius=10)
    label = font.render(fallback_text, True, (245, 245, 240) if enabled else (145, 145, 145))
    surface.blit(label, label.get_rect(center=rect.center))


def get_selection_action(mouse_pos, opponent_count):
    if mouse_pos is None:
        return None
    for index, rect in enumerate(OPPONENT_CARD_RECTS[:opponent_count]):
        if rect.collidepoint(mouse_pos):
            return ("opponent", index)
    if HEAD_TO_HEAD_RETURN_RECT.collidepoint(mouse_pos):
        return ("return", None)
    if HEAD_TO_HEAD_START_RECT.collidepoint(mouse_pos):
        return ("start", None)
    return None


def draw_head_to_head_selection(
        surface,
        mouse_pos,
        opponents,
        selected_index,
        player_name,
        player_rating,
        portrait_loader,
        title_font,
        heading_font,
        body_font,
        small_font,
        player_avatar=None,
):
    background = _load_asset(
        "assets/events/head_to_head/background.png",
        (BASE_WIDTH, BASE_HEIGHT),
    )
    if background is not None:
        surface.blit(background, (0, 0))
        shade = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 48))
        surface.blit(shade, (0, 0))
    else:
        surface.fill((15, 33, 32))
        pygame.draw.rect(surface, (23, 55, 49), (0, 0, BASE_WIDTH, 768))

    title_asset = _load_asset(
        "assets/events/head_to_head/title.png",
        (360, 96),
    )
    if title_asset is not None:
        surface.blit(title_asset, title_asset.get_rect(center=(BASE_WIDTH // 2, 74)))
    else:
        title = title_font.render("HEAD-TO-HEAD", True, (248, 238, 205))
        surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 70)))

    subtitle = body_font.render(
        "Choose a rival for a timed Klondike race. First to 52 foundation cards wins.",
        True,
        (220, 226, 223),
    )
    surface.blit(subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 134)))

    player_panel = pygame.Rect(468, 145, 430, 52)
    panel = pygame.Surface(player_panel.size, pygame.SRCALPHA)
    panel.fill((10, 18, 18, 190))
    surface.blit(panel, player_panel.topleft)
    pygame.draw.rect(surface, (180, 159, 91), player_panel, 2, border_radius=8)
    if player_avatar is not None:
        avatar = pygame.transform.smoothscale(player_avatar, (36, 43))
        surface.blit(avatar, (player_panel.x + 14, player_panel.y + 4))

    player_label = small_font.render(
        f"{player_name}  •  Solitaire {int(player_rating):,}",
        True,
        (246, 237, 203),
    )
    label_center_x = player_panel.centerx + (18 if player_avatar is not None else 0)
    surface.blit(
        player_label,
        player_label.get_rect(center=(label_center_x, player_panel.centery))
    )

    for index, opponent in enumerate(opponents[:4]):
        rect = OPPONENT_CARD_RECTS[index]
        selected = index == selected_index
        hovered = mouse_pos is not None and rect.collidepoint(mouse_pos)
        fill = (24, 42, 39, 228)
        if hovered:
            fill = (29, 53, 48, 236)
        card_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        card_surface.fill(fill)
        surface.blit(card_surface, rect.topleft)

        border = (243, 204, 88) if selected else (185, 195, 190)
        pygame.draw.rect(surface, border, rect, 4 if selected else 2, border_radius=12)

        npc = opponent.get("npc") or {}
        portrait = portrait_loader(npc, 118) if callable(portrait_loader) else None
        portrait_rect = pygame.Rect(rect.centerx - 59, rect.y + 22, 118, 118)
        pygame.draw.ellipse(surface, (12, 18, 18), portrait_rect)
        if portrait is not None:
            clipped = portrait.copy()
            mask = pygame.Surface((118, 118), pygame.SRCALPHA)
            pygame.draw.ellipse(mask, (255, 255, 255, 255), mask.get_rect())
            clipped.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(clipped, portrait_rect.topleft)
        pygame.draw.ellipse(surface, border, portrait_rect, 3)

        name = str(opponent.get("name", "Opponent"))
        rating = int(opponent.get("rating", 1000))
        delta = rating - int(player_rating)
        relationship = "HIGHER RATED" if delta > 0 else "LOWER RATED" if delta < 0 else "EVEN MATCH"

        name_surface = heading_font.render(name, True, (245, 245, 240))
        surface.blit(name_surface, name_surface.get_rect(center=(rect.centerx, rect.y + 168)))

        rating_surface = body_font.render(
            f"Solitaire {rating:,}",
            True,
            (232, 211, 144),
        )
        surface.blit(rating_surface, rating_surface.get_rect(center=(rect.centerx, rect.y + 207)))

        delta_text = f"{delta:+,}" if delta else "±0"
        delta_surface = small_font.render(
            f"{relationship}  {delta_text}",
            True,
            (196, 204, 200),
        )
        surface.blit(delta_surface, delta_surface.get_rect(center=(rect.centerx, rect.y + 240)))

        hometown = str(opponent.get("hometown", "Unknown"))
        if len(hometown) > 30:
            hometown = hometown[:27] + "..."
        hometown_surface = small_font.render(hometown, True, (174, 184, 180))
        surface.blit(hometown_surface, hometown_surface.get_rect(center=(rect.centerx, rect.y + 282)))

        if selected:
            selected_surface = small_font.render("SELECTED", True, (255, 225, 105))
            surface.blit(selected_surface, selected_surface.get_rect(center=(rect.centerx, rect.bottom - 28)))

    _draw_button(
        surface,
        HEAD_TO_HEAD_RETURN_RECT,
        "assets/events/head_to_head/return.png",
        "Return",
        body_font,
        mouse_pos,
        enabled=True,
    )
    _draw_button(
        surface,
        HEAD_TO_HEAD_START_RECT,
        "assets/events/head_to_head/start_race.png",
        "Start Race",
        body_font,
        mouse_pos,
        enabled=selected_index is not None,
    )

    if selected_index is None and mouse_pos is not None and HEAD_TO_HEAD_START_RECT.collidepoint(mouse_pos):
        tooltip = small_font.render("Choose an opponent first.", True, (245, 245, 245))
        tooltip_rect = tooltip.get_rect(midbottom=(HEAD_TO_HEAD_START_RECT.centerx, HEAD_TO_HEAD_START_RECT.y - 8)).inflate(18, 10)
        box = pygame.Surface(tooltip_rect.size, pygame.SRCALPHA)
        box.fill((10, 16, 15, 235))
        surface.blit(box, tooltip_rect.topleft)
        pygame.draw.rect(surface, (229, 198, 101), tooltip_rect, 2, border_radius=7)
        surface.blit(tooltip, tooltip.get_rect(center=tooltip_rect.center))


def draw_head_to_head_hud(
        surface,
        race,
        player_progress,
        now_ms,
        portrait_loader,
        heading_font,
        body_font,
        small_font,
):
    if race is None or race.opponent is None:
        return

    panel_rect = pygame.Rect(382, 8, 350, 126)
    panel = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
    panel.fill((8, 16, 16, 212))
    surface.blit(panel, panel_rect.topleft)
    pygame.draw.rect(surface, (219, 194, 115), panel_rect, 2, border_radius=10)

    opponent = race.opponent
    npc = opponent.get("npc") or {}
    portrait = portrait_loader(npc, 62) if callable(portrait_loader) else None
    portrait_rect = pygame.Rect(panel_rect.x + 14, panel_rect.y + 24, 62, 62)
    if portrait is not None:
        clipped = portrait.copy()
        mask = pygame.Surface((62, 62), pygame.SRCALPHA)
        pygame.draw.ellipse(mask, (255, 255, 255, 255), mask.get_rect())
        clipped.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(clipped, portrait_rect.topleft)
    pygame.draw.ellipse(surface, (219, 194, 115), portrait_rect, 2)

    opponent_name = str(opponent.get("name", "Opponent"))
    compact_name = opponent_name if len(opponent_name) <= 15 else opponent_name.split()[0]
    name = heading_font.render(compact_name, True, (245, 245, 240))
    surface.blit(name, (panel_rect.x + 88, panel_rect.y + 12))

    timer = body_font.render(race.format_elapsed(now_ms), True, (242, 219, 128))
    surface.blit(timer, timer.get_rect(topright=(panel_rect.right - 18, panel_rect.y + 16)))

    bar_x = panel_rect.x + 88
    bar_w = 168
    player_y = panel_rect.y + 51
    npc_y = panel_rect.y + 86

    for label, progress, y, fill_color in (
            ("YOU", player_progress, player_y, (122, 202, 150)),
            ("NPC", race.npc_progress_cards, npc_y, (211, 161, 106)),
    ):
        label_surface = small_font.render(label, True, (220, 226, 223))
        surface.blit(label_surface, (bar_x, y - 2))
        bar_rect = pygame.Rect(bar_x + 45, y, bar_w, 17)
        pygame.draw.rect(surface, (48, 58, 57), bar_rect, border_radius=8)
        filled = pygame.Rect(
            bar_rect.x,
            bar_rect.y,
            int(bar_rect.width * max(0, min(52, progress)) / 52.0),
            bar_rect.height,
        )
        if filled.width > 0:
            pygame.draw.rect(surface, fill_color, filled, border_radius=8)
        pygame.draw.rect(surface, (126, 139, 135), bar_rect, 1, border_radius=8)
        count = small_font.render(f"{progress}/52", True, (237, 237, 233))
        surface.blit(count, count.get_rect(midleft=(bar_rect.right + 6, bar_rect.centery)))

    if race.is_countdown_active(now_ms):
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 92))
        surface.blit(overlay, (0, 0))
        label = race.countdown_label(now_ms)
        giant_font = pygame.font.SysFont("georgia", 96, bold=True)
        count_surface = giant_font.render(label, True, (255, 229, 112))
        surface.blit(count_surface, count_surface.get_rect(center=(BASE_WIDTH // 2, BASE_HEIGHT // 2)))
        sub = body_font.render("First to clear all 52 foundation cards wins.", True, (250, 250, 245))
        surface.blit(sub, sub.get_rect(center=(BASE_WIDTH // 2, BASE_HEIGHT // 2 + 82)))

