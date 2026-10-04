import os
import math
import pygame


ACTION_RETURN = "return"
ACTION_PLACE_BET = "place_bet"
ACTION_CLEAR_BETS = "clear_bets"
ACTION_START_RACE = "start_race"
ACTION_NEXT_RACE = "next_race"
ACTION_WIN = "bet_type_win"
ACTION_PLACE = "bet_type_place"
ACTION_SHOW = "bet_type_show"
ACTION_CHIP_10 = "chip_10"
ACTION_CHIP_50 = "chip_50"
ACTION_CHIP_100 = "chip_100"
ACTION_CHIP_500 = "chip_500"
ACTION_HORSE_PREFIX = "horse:"

TRACK_RECT = pygame.Rect(36, 148, 948, 352)
FIELD_PANEL_RECT = pygame.Rect(1000, 136, 330, 364)
BOTTOM_PANEL_RECT = pygame.Rect(36, 518, 1294, 208)
RETURN_RECT = pygame.Rect(1117, 32, 203, 54)
PLACE_BET_RECT = pygame.Rect(910, 575, 180, 48)
CLEAR_BETS_RECT = pygame.Rect(1102, 575, 180, 48)
RACE_ACTION_RECT = pygame.Rect(1087, 653, 195, 52)

BET_TYPE_RECTS = {
    "win": pygame.Rect(54, 565, 108, 44),
    "place": pygame.Rect(172, 565, 108, 44),
    "show": pygame.Rect(290, 565, 108, 44),
}

CHIP_RECTS = {
    10: pygame.Rect(472, 559, 70, 58),
    50: pygame.Rect(552, 559, 70, 58),
    100: pygame.Rect(632, 559, 70, 58),
    500: pygame.Rect(712, 559, 70, 58),
}

HORSE_ROW_RECTS = [
    pygame.Rect(1012, 166 + index * 52, 306, 46)
    for index in range(6)
]

_asset_cache = {}
_font_cache = {}
_chip_cache = {}
_horse_cache = {}

WHITE = (242, 242, 238)
CREAM = (238, 222, 178)
GOLD = (214, 176, 86)
DARK = (18, 22, 24)
PANEL = (20, 25, 28, 220)
PANEL_ALT = (33, 40, 42, 225)
MUTED = (175, 184, 180)
GREEN = (66, 130, 88)
RED = (158, 69, 62)


def _font(size, bold=False):
    key = (int(size), bool(bold))
    if key not in _font_cache:
        _font_cache[key] = pygame.font.SysFont(
            "georgia",
            int(size),
            bold=bold,
        )
    return _font_cache[key]


def _load_image(path, size=None):
    key = (path, tuple(size) if size else None)
    if key in _asset_cache:
        return _asset_cache[key]
    try:
        image = pygame.image.load(path).convert_alpha()
        if size is not None:
            image = pygame.transform.smoothscale(image, size)
    except (pygame.error, FileNotFoundError):
        image = None
    _asset_cache[key] = image
    return image


def _draw_translucent_panel(surface, rect, fill=PANEL, border=GOLD, radius=12):
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(layer, fill, layer.get_rect(), border_radius=radius)
    pygame.draw.rect(layer, (*border, 220), layer.get_rect(), 2, border_radius=radius)
    surface.blit(layer, rect.topleft)


def _draw_selected_glow(surface, rect):
    """Draw a pulsing gold halo around a selected betting control."""
    pulse = (math.sin(pygame.time.get_ticks() / 180.0) + 1.0) * 0.5
    glow_alpha = int(70 + 90 * pulse)

    pad = 10
    glow = pygame.Surface(
        (rect.width + pad * 2, rect.height + pad * 2),
        pygame.SRCALPHA,
    )
    glow_rect = glow.get_rect()

    for inset, alpha_scale in ((0, 0.28), (3, 0.42), (6, 0.62)):
        outline = glow_rect.inflate(-inset * 2, -inset * 2)
        pygame.draw.rect(
            glow,
            (*GOLD, int(glow_alpha * alpha_scale)),
            outline,
            3,
            border_radius=11,
        )

    surface.blit(glow, (rect.x - pad, rect.y - pad))


def _draw_winner_fireworks(surface, game):
    """Brief procedural fireworks above the winning horse after a race."""
    if game.stage != "results" or not game.result_order or not game.current_field:
        return

    finish_durations = [
        float(horse.get("finish_duration", 0.0) or 0.0)
        for horse in game.current_field
    ]
    if not finish_durations or not game.race_started_ms:
        return

    results_started_ms = (
        int(game.race_started_ms)
        + int(max(finish_durations) * 1000.0)
    )
    elapsed_ms = pygame.time.get_ticks() - results_started_ms
    if elapsed_ms < 0 or elapsed_ms > 3000:
        return

    winner_index = int(game.result_order[0])
    if not 0 <= winner_index < len(game.current_field):
        return

    lane_height = TRACK_RECT.height / 6.0
    horse_y = int(
        TRACK_RECT.top
        + winner_index * lane_height
        + lane_height / 2
    )

    # The winner is at the finish after the race resolves. Keep the bursts just
    # above and slightly behind the horse so the sprite remains readable.
    finish_x = TRACK_RECT.right - 120
    base_x = finish_x + 36
    base_y = horse_y - 42

    palette = (
        (255, 218, 86),
        (255, 245, 190),
        (238, 100, 86),
        (112, 195, 255),
    )

    layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    t = elapsed_ms / 1000.0

    for burst_index, delay in enumerate((0.0, 0.48, 0.96, 1.42, 1.90)):
        age = t - delay
        if age < 0.0 or age > 1.05:
            continue

        progress = age / 1.05
        radius = 10.0 + progress * 45.0
        alpha = int(255 * (1.0 - progress))
        cx = base_x + ((burst_index % 3) - 1) * 42
        cy = base_y - (burst_index % 2) * 28

        for ray in range(12):
            angle = ray * (math.tau / 12.0) + burst_index * 0.24
            inner = max(4.0, radius - 13.0)
            x1 = int(cx + math.cos(angle) * inner)
            y1 = int(cy + math.sin(angle) * inner)
            x2 = int(cx + math.cos(angle) * radius)
            y2 = int(cy + math.sin(angle) * radius)
            color = palette[(ray + burst_index) % len(palette)]
            pygame.draw.line(
                layer,
                (*color, alpha),
                (x1, y1),
                (x2, y2),
                3,
            )
            pygame.draw.circle(
                layer,
                (*color, alpha),
                (x2, y2),
                3,
            )

    surface.blit(layer, (0, 0))


def _load_chip(value):
    if value in _chip_cache:
        return _chip_cache[value]
    filename = {
        10: "chip_red.png",
        50: "chip_blue.png",
        100: "chip_green.png",
        500: "chip_black.png",
    }.get(value)
    image = None
    if filename:
        image = _load_image(os.path.join("assets", "poker", filename), (54, 54))
    _chip_cache[value] = image
    return image


def _load_horse(lane):
    lane = max(1, min(6, int(lane)))
    if lane in _horse_cache:
        return _horse_cache[lane]
    path = f"assets/horse_races/horse_{lane}.png"
    image = _load_image(path, (88, 60))
    _horse_cache[lane] = image
    return image


def _draw_image_button(surface, rect, path, fallback, mouse_pos, enabled=True):
    image = _load_image(path, rect.size)
    hovered = enabled and mouse_pos is not None and rect.collidepoint(mouse_pos)
    if image is not None:
        button = image.copy()
        if hovered:
            button.fill((24, 24, 24, 0), special_flags=pygame.BLEND_RGBA_ADD)
        if not enabled:
            button.fill((105, 105, 105, 255), special_flags=pygame.BLEND_RGBA_MULT)
            button.set_alpha(150)
        surface.blit(button, rect.topleft)
        return

    fill = (66, 74, 72) if enabled else (48, 52, 53)
    if hovered:
        fill = (82, 93, 88)
    pygame.draw.rect(surface, fill, rect, border_radius=9)
    pygame.draw.rect(surface, GOLD if enabled else (100, 100, 100), rect, 2, border_radius=9)
    text = _font(17, True).render(fallback, True, WHITE if enabled else MUTED)
    surface.blit(text, text.get_rect(center=rect.center))


def _draw_track_fallback(surface):
    pygame.draw.rect(surface, (91, 60, 38), TRACK_RECT, border_radius=8)
    lane_height = TRACK_RECT.height / 6.0
    for index in range(7):
        y = int(TRACK_RECT.top + index * lane_height)
        pygame.draw.line(
            surface,
            (224, 214, 187),
            (TRACK_RECT.left, y),
            (TRACK_RECT.right, y),
            2,
        )
    finish_x = TRACK_RECT.right - 44
    for row in range(12):
        y = TRACK_RECT.top + int(row * TRACK_RECT.height / 12)
        pygame.draw.rect(
            surface,
            (235, 235, 230) if row % 2 == 0 else (40, 40, 40),
            (finish_x, y, 18, int(TRACK_RECT.height / 12) + 1),
        )
        pygame.draw.rect(
            surface,
            (40, 40, 40) if row % 2 == 0 else (235, 235, 230),
            (finish_x + 18, y, 18, int(TRACK_RECT.height / 12) + 1),
        )


def _draw_horses(surface, game):
    if not game.current_field:
        return
    lane_height = TRACK_RECT.height / 6.0
    start_x = TRACK_RECT.left + 24
    finish_x = TRACK_RECT.right - 120
    for index, horse in enumerate(game.current_field):
        progress = 0.0
        if index < len(game.positions):
            progress = max(0.0, min(1.0, float(game.positions[index])))
        x = int(start_x + (finish_x - start_x) * progress)
        y = int(TRACK_RECT.top + index * lane_height + lane_height / 2)
        sprite = _load_horse(horse.get("lane", index + 1))
        if sprite is not None:
            rect = sprite.get_rect(midleft=(x, y))
            surface.blit(sprite, rect)
        else:
            fallback = pygame.Rect(x, y - 18, 70, 36)
            pygame.draw.rect(surface, (62 + index * 18, 88, 104), fallback, border_radius=14)
            label = _font(15, True).render(f"#{index + 1}", True, WHITE)
            surface.blit(label, label.get_rect(center=fallback.center))


def _draw_field_panel(surface, mouse_pos, game):
    _draw_translucent_panel(surface, FIELD_PANEL_RECT)
    title = _font(18, True).render("RACE CARD", True, CREAM)
    surface.blit(title, (FIELD_PANEL_RECT.x + 14, FIELD_PANEL_RECT.y + 10))

    for index, horse in enumerate(game.current_field[:6]):
        rect = HORSE_ROW_RECTS[index]
        selected = index == game.selected_horse_index
        hovered = mouse_pos is not None and rect.collidepoint(mouse_pos)
        fill = (64, 63, 44) if selected else (40, 46, 47)
        if hovered and game.stage == "betting":
            fill = (58, 64, 60)
        pygame.draw.rect(surface, fill, rect, border_radius=7)
        pygame.draw.rect(surface, GOLD if selected else (91, 99, 96), rect, 2, border_radius=7)

        lane = _font(16, True).render(str(index + 1), True, CREAM)
        surface.blit(lane, (rect.x + 9, rect.y + 7))

        name = _font(14, True).render(horse["name"], True, WHITE)
        surface.blit(name, (rect.x + 31, rect.y + 5))

        odds = _font(14, True).render(
            f"W {horse['win_odds']:.1f}:1   P {horse['place_odds']:.1f}:1   S {horse['show_odds']:.1f}:1",
            True,
            MUTED,
        )
        surface.blit(odds, (rect.x + 31, rect.y + 24))

        if game.stage == "results" and index in game.result_order:
            place = game.result_order.index(index) + 1
            badge = _font(12, True).render(f"#{place}", True, GOLD if place <= 3 else MUTED)
            surface.blit(badge, badge.get_rect(midright=(rect.right - 8, rect.centery)))


def _draw_betting_controls(surface, mouse_pos, game):
    betting_enabled = game.stage == "betting"

    label = _font(14, True).render("BET TYPE", True, CREAM)
    surface.blit(label, (54, 542))

    for bet_type, rect in BET_TYPE_RECTS.items():
        selected = game.selected_bet_type == bet_type

        # Selection is intentionally much stronger than hover: a pulsing gold
        # halo plus a thicker inner border makes WIN / PLACE / SHOW obvious at
        # a glance, even with custom button artwork.
        if selected and betting_enabled:
            _draw_selected_glow(surface, rect)

        icon = _load_image(f"assets/horse_races/{bet_type}.png", rect.size)
        if icon is not None:
            button = icon.copy()
            if not betting_enabled:
                button.set_alpha(115)
            elif selected:
                button.fill((32, 28, 12, 0), special_flags=pygame.BLEND_RGBA_ADD)
            surface.blit(button, rect.topleft)
            pygame.draw.rect(
                surface,
                GOLD if selected else (104, 110, 105),
                rect,
                5 if selected and betting_enabled else 2,
                border_radius=8,
            )
        else:
            fill = (92, 75, 35) if selected else (48, 55, 55)
            if not betting_enabled:
                fill = (42, 44, 44)
            pygame.draw.rect(surface, fill, rect, border_radius=8)
            pygame.draw.rect(
                surface,
                GOLD if selected else (104, 110, 105),
                rect,
                5 if selected and betting_enabled else 2,
                border_radius=8,
            )
            text = _font(16, True).render(
                bet_type.upper(),
                True,
                WHITE if betting_enabled else MUTED,
            )
            surface.blit(text, text.get_rect(center=rect.center))

    chip_label = _font(14, True).render("CHIP", True, CREAM)
    surface.blit(chip_label, (472, 542))
    for value, rect in CHIP_RECTS.items():
        selected = value == game.selected_chip_value
        image = _load_chip(value)
        if image is not None:
            chip = image.copy()
            if not betting_enabled:
                chip.set_alpha(110)
            surface.blit(chip, chip.get_rect(center=rect.center))
        else:
            pygame.draw.circle(surface, (80, 85, 85), rect.center, 25)
        pygame.draw.rect(surface, GOLD if selected else (92, 98, 96), rect, 2, border_radius=9)
        value_text = _font(10, True).render(f"${value}", True, WHITE)
        surface.blit(value_text, value_text.get_rect(center=(rect.centerx, rect.bottom - 4)))

    _draw_image_button(
        surface,
        PLACE_BET_RECT,
        "assets/horse_races/place_bet.png",
        "Place Bet",
        mouse_pos,
        enabled=betting_enabled and game.bankroll >= game.selected_chip_value,
    )
    _draw_image_button(
        surface,
        CLEAR_BETS_RECT,
        "",
        "Clear Bets",
        mouse_pos,
        enabled=betting_enabled and bool(game.tickets),
    )

    if game.stage == "betting":
        race_path = "assets/horse_races/start_race.png"
        race_label = "Start Race"
        race_enabled = game.can_start_race()
    elif game.stage == "results":
        race_path = "assets/horse_races/next_race.png"
        race_label = "Next Race"
        race_enabled = True
    else:
        race_path = "assets/horse_races/start_race.png"
        race_label = "Racing..."
        race_enabled = False

    _draw_image_button(
        surface,
        RACE_ACTION_RECT,
        race_path,
        race_label,
        mouse_pos,
        enabled=race_enabled,
    )


def _draw_ticket_area(surface, game):
    title = _font(14, True).render("TICKETS", True, CREAM)
    surface.blit(title, (54, 625))

    if not game.tickets:
        text = _font(13).render("No wagers placed yet.", True, MUTED)
        surface.blit(text, (54, 650))
    else:
        x = 54
        y = 648
        for ticket in game.tickets[:4]:
            status = ""
            if game.stage == "results":
                status = f"  RETURN ${ticket.get('return', 0):,}" if ticket.get("won") else "  LOST"
            line = (
                f"#{ticket['lane']} {ticket['horse_name']}  "
                f"{ticket['bet_type'].upper()}  ${ticket['stake']:,} @ {ticket['odds']:.1f}:1{status}"
            )
            text = _font(12).render(line, True, WHITE if ticket.get("won") else MUTED)
            surface.blit(text, (x, y))
            y += 20

        if len(game.tickets) > 4:
            more = _font(11).render(f"+{len(game.tickets) - 4} more ticket(s)", True, MUTED)
            surface.blit(more, (54, y))

    bankroll = _font(16, True).render(f"Bankroll: ${game.bankroll:,}", True, WHITE)
    session_net = game.get_session_net()
    net_text = f"Session: {'+' if session_net > 0 else ''}${session_net:,}"
    session = _font(14, True).render(net_text, True, GREEN if session_net >= 0 else RED)
    surface.blit(bankroll, (800, 646))
    surface.blit(session, (800, 674))


def _draw_result_strip(surface, game):
    message = game.race_message or ""
    color = GOLD if game.photo_finish else WHITE
    rendered = _font(17, True).render(message, True, color)
    max_width = 900
    if rendered.get_width() > max_width:
        rendered = pygame.transform.smoothscale(
            rendered,
            (max_width, rendered.get_height()),
        )
    surface.blit(rendered, rendered.get_rect(center=(683, 112)))


def draw_horse_races(surface, mouse_pos, game):
    background = _load_image("assets/horse_races/background.png", surface.get_size())
    if background is not None:
        surface.blit(background, (0, 0))
    else:
        surface.fill((17, 28, 27))
        for y in range(0, surface.get_height(), 80):
            pygame.draw.line(surface, (23, 38, 35), (0, y), (surface.get_width(), y), 1)

    logo = _load_image("assets/horse_races/logo.png", (300, 80))
    if logo is not None:
        surface.blit(logo, (38, 25))
    else:
        title = _font(34, True).render("HORSE RACES", True, CREAM)
        surface.blit(title, (40, 42))

    _draw_image_button(
        surface,
        RETURN_RECT,
        "assets/horse_races/return.png",
        "Return",
        mouse_pos,
        enabled=game.stage != "racing",
    )

    track = _load_image("assets/horse_races/track.png", TRACK_RECT.size)
    if track is not None:
        surface.blit(track, TRACK_RECT.topleft)
    else:
        _draw_track_fallback(surface)

    # Lane markers stay readable even if the supplied track has no numbers.
    lane_height = TRACK_RECT.height / 6.0
    for index in range(6):
        marker = pygame.Rect(TRACK_RECT.x + 4, int(TRACK_RECT.y + index * lane_height + 9), 34, 34)
        pygame.draw.rect(surface, (18, 22, 22, 210), marker, border_radius=8)
        num = _font(15, True).render(str(index + 1), True, CREAM)
        surface.blit(num, num.get_rect(center=marker.center))

    _draw_horses(surface, game)
    _draw_winner_fireworks(surface, game)
    _draw_field_panel(surface, mouse_pos, game)
    _draw_translucent_panel(surface, BOTTOM_PANEL_RECT)
    _draw_betting_controls(surface, mouse_pos, game)
    _draw_ticket_area(surface, game)
    _draw_result_strip(surface, game)

    if game.stage == "betting" and not game.tickets:
        hint = _font(11).render("Place at least one wager before starting the race.", True, MUTED)
        surface.blit(hint, hint.get_rect(midright=(RACE_ACTION_RECT.right, 638)))


def get_horse_races_action(mouse_pos):
    if mouse_pos is None:
        return None
    if RETURN_RECT.collidepoint(mouse_pos):
        return ACTION_RETURN
    if PLACE_BET_RECT.collidepoint(mouse_pos):
        return ACTION_PLACE_BET
    if CLEAR_BETS_RECT.collidepoint(mouse_pos):
        return ACTION_CLEAR_BETS
    if RACE_ACTION_RECT.collidepoint(mouse_pos):
        return ACTION_START_RACE

    for bet_type, rect in BET_TYPE_RECTS.items():
        if rect.collidepoint(mouse_pos):
            return {
                "win": ACTION_WIN,
                "place": ACTION_PLACE,
                "show": ACTION_SHOW,
            }[bet_type]

    for value, rect in CHIP_RECTS.items():
        if rect.collidepoint(mouse_pos):
            return {
                10: ACTION_CHIP_10,
                50: ACTION_CHIP_50,
                100: ACTION_CHIP_100,
                500: ACTION_CHIP_500,
            }[value]

    for index, rect in enumerate(HORSE_ROW_RECTS):
        if rect.collidepoint(mouse_pos):
            return f"{ACTION_HORSE_PREFIX}{index}"

    return None
