import os

import pygame

from faro import FARO_RANKS


ACTION_RETURN = "return"
ACTION_DEAL = "deal"
ACTION_CLEAR_BETS = "clear_bets"
ACTION_CHIP_10 = "chip_10"
ACTION_CHIP_50 = "chip_50"
ACTION_CHIP_100 = "chip_100"
ACTION_CHIP_500 = "chip_500"
ACTION_BET_RANK_PREFIX = "bet_rank_"

WHITE = (245, 245, 240)
CREAM = (239, 224, 184)
GOLD = (226, 188, 78)
DARK = (20, 25, 24)
DARK_GREEN = (22, 69, 46)
LIGHT_GREEN = (48, 116, 76)
RED = (198, 92, 85)
WIN_GREEN = (144, 218, 157)

FARO_RETURN_RECT = pygame.Rect(1120, 696, 190, 44)
FARO_DEAL_RECT = pygame.Rect(900, 696, 200, 44)
FARO_CLEAR_RECT = pygame.Rect(676, 696, 200, 44)
FARO_CHIP_RECTS = {
    10: pygame.Rect(92, 697, 105, 42),
    50: pygame.Rect(207, 697, 105, 42),
    100: pygame.Rect(322, 697, 115, 42),
    500: pygame.Rect(447, 697, 115, 42),
}

FARO_RANK_RECTS = {}
_asset_cache = {}
_chip_cache = {}
_scaled_card_cache = {}


def _build_rank_rects():
    FARO_RANK_RECTS.clear()
    width = 102
    height = 88
    gap = 10
    top = FARO_RANKS[:7]
    bottom = FARO_RANKS[7:]
    center_x = 635

    top_total = len(top) * width + (len(top) - 1) * gap
    bottom_total = len(bottom) * width + (len(bottom) - 1) * gap
    top_x = center_x - top_total // 2
    bottom_x = center_x - bottom_total // 2

    for index, rank in enumerate(top):
        FARO_RANK_RECTS[rank] = pygame.Rect(
            top_x + index * (width + gap), 178, width, height
        )
    for index, rank in enumerate(bottom):
        FARO_RANK_RECTS[rank] = pygame.Rect(
            bottom_x + index * (width + gap), 280, width, height
        )


_build_rank_rects()


def _load_asset(path, size=None):
    key = (path, tuple(size) if size else None)
    if key in _asset_cache:
        return _asset_cache[key]
    image = None
    try:
        image = pygame.image.load(path).convert_alpha()
        if size is not None:
            image = pygame.transform.smoothscale(image, size)
    except (pygame.error, FileNotFoundError):
        image = None
    _asset_cache[key] = image
    return image


def _load_card_surface(card, card_fronts, size=(84, 118)):
    if not card or not isinstance(card_fronts, dict):
        return None
    suit = card.get("suit")
    if suit in ("C", "D", "H", "S"):
        key = f"{card.get('rank')}{suit}"
    else:
        letter = {
            "Clubs": "C", "Diamonds": "D", "Hearts": "H", "Spades": "S"
        }.get(suit)
        key = f"{card.get('rank')}{letter}" if letter else None
    if not key:
        return None
    source = card_fronts.get(key)
    if source is None:
        return None
    cache_key = (key, tuple(size), id(source))
    if cache_key not in _scaled_card_cache:
        _scaled_card_cache[cache_key] = pygame.transform.smoothscale(source, size)
    return _scaled_card_cache[cache_key]


def _load_chip_surface(value):
    if value in _chip_cache:
        return _chip_cache[value]
    filename = {
        10: "chip_red.png",
        50: "chip_blue.png",
        100: "chip_green.png",
        500: "chip_black.png",
    }.get(value, "chip_yellow.png")
    path = os.path.join("assets", "poker", filename)
    image = _load_asset(path, (40, 40))
    _chip_cache[value] = image
    return image


def _draw_chip(surface, center, amount, font):
    if amount <= 0:
        return
    chip_value = 500 if amount >= 500 else 100 if amount >= 100 else 50 if amount >= 50 else 10
    image = _load_chip_surface(chip_value)
    if image is not None:
        surface.blit(image, image.get_rect(center=center))
    else:
        pygame.draw.circle(surface, CREAM, center, 18)
        pygame.draw.circle(surface, DARK, center, 18, 2)
    label = font.render(f"${amount:,}", True, WHITE)
    shadow = font.render(f"${amount:,}", True, (12, 12, 12))
    rect = label.get_rect(center=(center[0], center[1] + 28))
    surface.blit(shadow, rect.move(1, 1))
    surface.blit(label, rect)


def _draw_card(surface, card, center, font, card_fronts, card_back_surface=None, face_up=True, size=(84, 118)):
    rect = pygame.Rect(0, 0, *size)
    rect.center = center
    image = _load_card_surface(card, card_fronts, size) if face_up else card_back_surface
    if image is not None and image.get_size() != size:
        image = pygame.transform.smoothscale(image, size)
    if image is not None:
        surface.blit(image, rect)
    else:
        pygame.draw.rect(surface, WHITE if face_up else (45, 70, 145), rect, border_radius=5)
        pygame.draw.rect(surface, DARK, rect, 2, border_radius=5)
        if face_up and card:
            text = font.render(f"{card.get('rank','?')}{card.get('suit','?')}", True, DARK)
            surface.blit(text, text.get_rect(center=rect.center))
    return rect


def _draw_small_heading(surface, font, title, subtitle, center, subtitle_color):
    title_s = font.render(title, True, WHITE)
    sub_s = font.render(subtitle, True, subtitle_color)
    surface.blit(title_s, title_s.get_rect(center=(center[0], center[1] - 10)))
    surface.blit(sub_s, sub_s.get_rect(center=(center[0], center[1] + 12)))


def draw_faro(
        game_surface,
        mouse_pos,
        faro_game,
        selected_chip_value,
        draw_submenu_background,
        draw_submenu_title,
        draw_menu_button,
        title_font,
        label_font,
        detail_font,
        card_fronts=None,
        card_back_surface=None,
):
    background = _load_asset("assets/faro/table.png", (1366, 768))
    if background is not None:
        game_surface.blit(background, (0, 0))
        wash = pygame.Surface((1366, 768), pygame.SRCALPHA)
        wash.fill((0, 0, 0, 58))
        game_surface.blit(wash, (0, 0))
    else:
        draw_submenu_background(overlay_alpha=132)

    logo = _load_asset("assets/faro/logo.png", (300, 80))
    if logo is not None:
        game_surface.blit(logo, (28, 24))
    else:
        fallback = title_font.render("FARO", True, WHITE)
        game_surface.blit(fallback, (45, 42))

    rules = detail_font.render(
        "Banker rank loses  •  Player rank wins  •  Doublet takes half",
        True,
        CREAM,
    )
    game_surface.blit(rules, rules.get_rect(center=(682, 102)))

    board = pygame.Rect(118, 137, 1000, 508)
    panel = pygame.Surface(board.size, pygame.SRCALPHA)
    panel.fill((9, 28, 20, 188))
    game_surface.blit(panel, board.topleft)
    pygame.draw.rect(game_surface, (202, 180, 121), board, 2, border_radius=18)

    stats_rect = pygame.Rect(1134, 136, 198, 510)
    stats = pygame.Surface(stats_rect.size, pygame.SRCALPHA)
    stats.fill((8, 22, 18, 220))
    game_surface.blit(stats, stats_rect.topleft)
    pygame.draw.rect(game_surface, GOLD, stats_rect, 2, border_radius=14)

    net = faro_game.get_session_net()
    net_label = f"+${net:,}" if net > 0 else f"-${abs(net):,}" if net < 0 else "$0"
    stat_lines = (
        ("BANKROLL", f"${faro_game.cash:,}", WHITE),
        ("ON TABLE", f"${faro_game.get_total_bet():,}", CREAM),
        ("SESSION", net_label, WIN_GREEN if net >= 0 else RED),
        ("CARDS LEFT", str(len(faro_game.deck)), WHITE),
        ("TURN", str(faro_game.turn_number), WHITE),
    )
    y = 165
    for heading, value, color in stat_lines:
        h = detail_font.render(heading, True, (178, 185, 181))
        v = label_font.render(value, True, color)
        game_surface.blit(h, h.get_rect(center=(stats_rect.centerx, y)))
        game_surface.blit(v, v.get_rect(center=(stats_rect.centerx, y + 28)))
        y += 75

    for rank, rect in FARO_RANK_RECTS.items():
        hovered = mouse_pos is not None and rect.collidepoint(mouse_pos)
        wager = faro_game.get_bet_amount(rank)
        fill = LIGHT_GREEN if hovered else DARK_GREEN
        pygame.draw.rect(game_surface, fill, rect, border_radius=9)
        pygame.draw.rect(
            game_surface,
            GOLD if wager > 0 else CREAM,
            rect,
            4 if wager > 0 else 2,
            border_radius=9,
        )
        rank_surface = label_font.render(rank, True, WHITE)
        game_surface.blit(rank_surface, rank_surface.get_rect(center=(rect.centerx, rect.y + 27)))
        _draw_chip(game_surface, (rect.centerx, rect.y + 57), wager, detail_font)

    # Card resolution zone: the labels sit above each card, so none of the
    # Banker/Player wording collides with the card bottoms anymore.
    box_center = (332, 516)
    banker_center = (540, 516)
    player_center = (748, 516)
    case_center = (956, 516)

    _draw_small_heading(game_surface, detail_font, "DEALING BOX", "NEXT CARDS", (box_center[0], 420), CREAM)
    _draw_small_heading(game_surface, detail_font, "BANKER", "LOSES", (banker_center[0], 420), RED)
    _draw_small_heading(game_surface, detail_font, "PLAYER", "WINS", (player_center[0], 420), WIN_GREEN)
    _draw_small_heading(game_surface, detail_font, "CASE CARD", "FINAL CARD", (case_center[0], 420), GOLD)

    dealing_box = _load_asset("assets/faro/dealing_box.png", (126, 176))
    if dealing_box is not None:
        game_surface.blit(dealing_box, dealing_box.get_rect(center=box_center))
    else:
        _draw_card(
            game_surface, None, box_center, detail_font, card_fronts,
            card_back_surface=card_back_surface, face_up=False, size=(92, 130)
        )

    if faro_game.banker_card is not None:
        _draw_card(game_surface, faro_game.banker_card, banker_center, detail_font, card_fronts, face_up=True, size=(92, 130))
    else:
        empty = pygame.Rect(0, 0, 92, 130); empty.center = banker_center
        pygame.draw.rect(game_surface, (28, 42, 35), empty, 2, border_radius=6)

    if faro_game.player_card is not None:
        _draw_card(game_surface, faro_game.player_card, player_center, detail_font, card_fronts, face_up=True, size=(92, 130))
    else:
        empty = pygame.Rect(0, 0, 92, 130); empty.center = player_center
        pygame.draw.rect(game_surface, (28, 42, 35), empty, 2, border_radius=6)

    if faro_game.case_card is not None:
        _draw_card(game_surface, faro_game.case_card, case_center, detail_font, card_fronts, face_up=True, size=(92, 130))
    else:
        empty = pygame.Rect(0, 0, 92, 130); empty.center = case_center
        pygame.draw.rect(game_surface, (28, 42, 35), empty, 2, border_radius=6)

    result_panel = pygame.Rect(220, 620, 812, 40)
    result_bg = pygame.Surface(result_panel.size, pygame.SRCALPHA)
    result_bg.fill((7, 20, 16, 215))
    game_surface.blit(result_bg, result_panel.topleft)
    result = detail_font.render(faro_game.last_result_text, True, WHITE)
    if result.get_width() > result_panel.width - 20:
        text = faro_game.last_result_text
        while text and detail_font.size(text + "...")[0] > result_panel.width - 20:
            text = text[:-1]
        result = detail_font.render(text.rstrip() + "...", True, WHITE)
    game_surface.blit(result, result.get_rect(center=result_panel.center))

    chip_label = detail_font.render("CHIP", True, WHITE)
    game_surface.blit(chip_label, (36, 709))
    for value, rect in FARO_CHIP_RECTS.items():
        draw_menu_button(rect, f"${value}", mouse_pos, selected=(selected_chip_value == value), font=detail_font)

    draw_menu_button(FARO_CLEAR_RECT, "CLEAR BETS", mouse_pos, font=detail_font)

    if faro_game.session_complete:
        pygame.draw.rect(game_surface, (70, 74, 76), FARO_DEAL_RECT, border_radius=7)
        pygame.draw.rect(game_surface, (135, 140, 142), FARO_DEAL_RECT, 2, border_radius=7)
        label = detail_font.render(faro_game.get_deal_button_label(), True, (160, 164, 165))
        game_surface.blit(label, label.get_rect(center=FARO_DEAL_RECT.center))
    else:
        draw_menu_button(FARO_DEAL_RECT, faro_game.get_deal_button_label(), mouse_pos, font=detail_font)

    draw_menu_button(FARO_RETURN_RECT, "CASH OUT", mouse_pos, font=detail_font)


def get_faro_action(mouse_pos, button, faro_game):
    if mouse_pos is None:
        return None

    if FARO_RETURN_RECT.collidepoint(mouse_pos):
        return ACTION_RETURN

    if FARO_DEAL_RECT.collidepoint(mouse_pos):
        return ACTION_DEAL

    if FARO_CLEAR_RECT.collidepoint(mouse_pos):
        return ACTION_CLEAR_BETS

    for value, rect in FARO_CHIP_RECTS.items():
        if rect.collidepoint(mouse_pos):
            return {
                10: ACTION_CHIP_10,
                50: ACTION_CHIP_50,
                100: ACTION_CHIP_100,
                500: ACTION_CHIP_500,
            }[value]

    for rank, rect in FARO_RANK_RECTS.items():
        if rect.collidepoint(mouse_pos):
            return f"{ACTION_BET_RANK_PREFIX}{rank}"

    return None
