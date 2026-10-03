import os
import pygame


ACTION_RETURN = "return"
ACTION_DRAW = "draw"
ACTION_CONTINUE = "continue"
ACTION_CARD = "card"
ACTION_SUIT = "suit"


_RETURN_RECT = pygame.Rect(1218, 22, 118, 40)
_DRAW_RECT = pygame.Rect(1120, 545, 170, 48)
_CONTINUE_RECT = pygame.Rect(533, 585, 300, 52)

_SUIT_RECTS = {
    "C": pygame.Rect(472, 390, 100, 54),
    "D": pygame.Rect(580, 390, 100, 54),
    "H": pygame.Rect(688, 390, 100, 54),
    "S": pygame.Rect(796, 390, 100, 54),
}

_player_card_rects = []
_fonts = None


SUIT_NAMES = {
    "C": "Clubs",
    "D": "Diamonds",
    "H": "Hearts",
    "S": "Spades",
}

SUIT_ICON_PATHS = {
    "C": "assets/ui/suits/clubs.png",
    "D": "assets/ui/suits/diamonds.png",
    "H": "assets/ui/suits/hearts.png",
    "S": "assets/ui/suits/spades.png",
}

_suit_icon_cache = {}

def _get_suit_icon(suit, size):
    cache_key = (suit, tuple(size))
    if cache_key in _suit_icon_cache:
        return _suit_icon_cache[cache_key]

    path = SUIT_ICON_PATHS.get(suit)
    image = None
    if path and os.path.exists(path):
        try:
            image = pygame.image.load(path).convert_alpha()
            image = pygame.transform.smoothscale(image, size)
        except pygame.error:
            image = None

    _suit_icon_cache[cache_key] = image
    return image

def _draw_suit_label(surface, suit, suit_name, center, font, text_color=(245, 245, 235), icon_size=26):
    prefix = font.render("Active suit:", True, text_color)
    name = font.render(suit_name, True, text_color)
    icon = _get_suit_icon(suit, (icon_size, icon_size))
    gap = 8
    icon_width = icon_size if icon is not None else font.size(suit)[0]
    total_width = prefix.get_width() + gap + icon_width + gap + name.get_width()
    x = center[0] - total_width // 2
    y = center[1]

    surface.blit(prefix, prefix.get_rect(midleft=(x, y)))
    x += prefix.get_width() + gap

    if icon is not None:
        surface.blit(icon, icon.get_rect(center=(x + icon_width // 2, y)))
    else:
        fallback = font.render(suit, True, text_color)
        surface.blit(fallback, fallback.get_rect(center=(x + icon_width // 2, y)))
    x += icon_width + gap
    surface.blit(name, name.get_rect(midleft=(x, y)))

def _draw_suit_button(surface, rect, suit, mouse_pos, font):
    hovered = mouse_pos is not None and rect.collidepoint(mouse_pos)
    fill = (60, 105, 72) if hovered else (45, 75, 54)
    border = (255, 225, 120) if hovered else (210, 215, 210)
    pygame.draw.rect(surface, fill, rect, border_radius=9)
    pygame.draw.rect(surface, border, rect, 2, border_radius=9)

    icon = _get_suit_icon(suit, (22, 22))
    label = font.render(SUIT_NAMES[suit], True, (255, 255, 255))
    gap = 7
    icon_width = 22 if icon is not None else font.size(suit)[0]
    total = icon_width + gap + label.get_width()
    x = rect.centerx - total // 2

    if icon is not None:
        surface.blit(icon, icon.get_rect(center=(x + icon_width // 2, rect.centery)))
    else:
        fallback = font.render(suit, True, (255, 255, 255))
        surface.blit(fallback, fallback.get_rect(center=(x + icon_width // 2, rect.centery)))
    surface.blit(label, label.get_rect(midleft=(x + icon_width + gap, rect.centery)))


def _get_fonts():
    global _fonts
    if _fonts is None:
        _fonts = {
            "title": pygame.font.SysFont("cambria", 38, bold=True),
            "large": pygame.font.SysFont("cambria", 25, bold=True),
            "medium": pygame.font.SysFont("cambria", 19, bold=True),
            "small": pygame.font.SysFont("cambria", 15, bold=True),
            "tiny": pygame.font.SysFont("cambria", 13),
        }
    return _fonts


def _draw_panel(surface, rect, fill=(18, 28, 22, 225), border=(205, 210, 205), width=2):
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, fill, panel.get_rect(), border_radius=12)
    pygame.draw.rect(panel, (*border, 245), panel.get_rect(), width, border_radius=12)
    surface.blit(panel, rect.topleft)


def _draw_button(surface, rect, label, mouse_pos, font, enabled=True, selected=False):
    hovered = enabled and mouse_pos is not None and rect.collidepoint(mouse_pos)

    if not enabled:
        fill = (63, 67, 66)
        border = (105, 108, 107)
        text_color = (150, 153, 152)
    elif selected:
        fill = (90, 76, 30)
        border = (255, 220, 105)
        text_color = (255, 255, 255)
    elif hovered:
        fill = (60, 105, 72)
        border = (255, 225, 120)
        text_color = (255, 255, 255)
    else:
        fill = (45, 75, 54)
        border = (210, 215, 210)
        text_color = (245, 245, 245)

    pygame.draw.rect(surface, fill, rect, border_radius=9)
    pygame.draw.rect(surface, border, rect, 2, border_radius=9)
    text = font.render(label, True, text_color)
    surface.blit(text, text.get_rect(center=rect.center))


def _draw_card(surface, card, rect, card_fronts, card_back=None, face_up=True):
    image = None

    if face_up and card:
        key = f"{card['rank']}{card['suit']}"
        image = card_fronts.get(key)
    elif card_back is not None:
        image = card_back

    if image is None:
        pygame.draw.rect(surface, (235, 235, 230), rect, border_radius=5)
        pygame.draw.rect(surface, (40, 40, 40), rect, 2, border_radius=5)
        return

    scaled = pygame.transform.smoothscale(image, rect.size)
    surface.blit(scaled, rect.topleft)


def _draw_portrait(surface, npc, rect, portrait_loader):
    pygame.draw.rect(surface, (42, 52, 44), rect, border_radius=7)

    portrait = None
    if portrait_loader is not None:
        try:
            portrait = portrait_loader(npc, max(rect.width, rect.height))
        except Exception:
            portrait = None

    if portrait is not None:
        portrait = pygame.transform.smoothscale(portrait, rect.size)
        surface.blit(portrait, rect.topleft)
    else:
        fonts = _get_fonts()
        name = str(npc.get("name", "NPC"))
        initials = "".join(part[:1] for part in name.split()[:2]).upper() or "?"
        label = fonts["medium"].render(initials, True, (245, 245, 245))
        surface.blit(label, label.get_rect(center=rect.center))

    pygame.draw.rect(surface, (220, 220, 215), rect, 2, border_radius=7)


def _draw_npc_panel(surface, rect, npc, card_count, active, portrait_loader):
    fonts = _get_fonts()
    border = (255, 215, 85) if active else (180, 185, 180)
    _draw_panel(surface, rect, border=border, width=3 if active else 2)

    portrait_rect = pygame.Rect(rect.x + 10, rect.y + 10, 58, 58)
    _draw_portrait(surface, npc, portrait_rect, portrait_loader)

    name = str(npc.get("name", "NPC"))
    if len(name) > 20:
        name = name[:18] + "..."

    name_surf = fonts["small"].render(name, True, (245, 245, 245))
    surface.blit(name_surf, (rect.x + 78, rect.y + 13))

    count_surf = fonts["tiny"].render(
        f"Cards: {card_count}",
        True,
        (200, 205, 200),
    )
    surface.blit(count_surf, (rect.x + 78, rect.y + 40))

    if active:
        turn = fonts["tiny"].render("TURN", True, (255, 220, 100))
        surface.blit(turn, (rect.x + 78, rect.y + 57))


def _player_hand_layout(card_count):
    if card_count <= 0:
        return []

    width = 78
    height = 109
    max_span = 1020

    if card_count == 1:
        spacing = 0
    else:
        spacing = min(84, max(20, (max_span - width) // (card_count - 1)))

    total_width = width + spacing * (card_count - 1)
    start_x = 683 - total_width // 2
    y = 610

    return [
        pygame.Rect(start_x + index * spacing, y, width, height)
        for index in range(card_count)
    ]


def draw_crazy_eights(
        surface,
        mouse_pos,
        game,
        card_fronts,
        card_back,
        portrait_loader=None,
):
    global _player_card_rects

    fonts = _get_fonts()
    surface.fill((28, 104, 58))

    # Soft center table.
    table_rect = pygame.Rect(215, 92, 936, 445)
    pygame.draw.ellipse(surface, (22, 83, 48), table_rect)
    pygame.draw.ellipse(surface, (120, 84, 46), table_rect, 8)

    title = fonts["title"].render("CRAZY EIGHTS", True, (250, 244, 220))
    surface.blit(title, title.get_rect(center=(683, 49)))

    _draw_button(surface, _RETURN_RECT, "Return", mouse_pos, fonts["small"], enabled=True)

    # NPC panels across the upper table.
    npc_xs = (265, 545, 825)
    for npc_index, npc in enumerate(game.npcs[:3]):
        player_index = npc_index + 1
        rect = pygame.Rect(npc_xs[npc_index], 110, 240, 82)
        card_count = len(game.hands[player_index]) if player_index < len(game.hands) else 0
        _draw_npc_panel(
            surface,
            rect,
            npc,
            card_count,
            active=(game.current_player == player_index and not game.game_over),
            portrait_loader=portrait_loader,
        )

    # Draw pile + discard.
    stock_rect = pygame.Rect(570, 255, 88, 123)
    discard_rect = pygame.Rect(708, 255, 88, 123)

    _draw_card(surface, None, stock_rect, card_fronts, card_back=card_back, face_up=False)
    top = game.get_top_discard()
    _draw_card(surface, top, discard_rect, card_fronts, card_back=card_back, face_up=True)

    stock_count = fonts["tiny"].render(
        f"Draw pile: {len(game.stock)}",
        True,
        (235, 235, 225),
    )
    surface.blit(stock_count, stock_count.get_rect(center=(stock_rect.centerx, stock_rect.bottom + 18)))

    discard_label = fonts["tiny"].render(
        "Discard",
        True,
        (235, 235, 225),
    )
    surface.blit(discard_label, discard_label.get_rect(center=(discard_rect.centerx, discard_rect.bottom + 18)))

    _draw_suit_label(
        surface,
        game.current_suit,
        game.get_active_suit_name(),
        (683, 425),
        fonts["large"],
        text_color=(245, 245, 235),
        icon_size=26,
    )

    if game.game_over:
        turn_text = game.result_text
    elif game.current_player == 0:
        turn_text = "Your turn"
    else:
        turn_text = f"{game.get_player_name(game.current_player)} is thinking..."

    turn_surface = fonts["medium"].render(turn_text, True, (250, 240, 200))
    surface.blit(turn_surface, turn_surface.get_rect(center=(683, 468)))

    if game.last_action_text:
        action = game.last_action_text
        if len(action) > 86:
            action = action[:83] + "..."
        action_surface = fonts["small"].render(action, True, (215, 220, 210))
        surface.blit(action_surface, action_surface.get_rect(center=(683, 505)))

    # Player hand.
    player_hand = game.hands[0] if game.hands else []
    _player_card_rects = _player_hand_layout(len(player_hand))

    player_label = fonts["medium"].render("YOUR HAND", True, (250, 245, 225))
    surface.blit(player_label, (70, 565))

    for index, (card, rect) in enumerate(zip(player_hand, _player_card_rects)):
        hovered = mouse_pos is not None and rect.collidepoint(mouse_pos)
        playable = (
            not game.game_over
            and game.current_player == 0
            and not game.waiting_for_suit_choice
            and game.is_card_playable(card)
        )

        draw_rect = rect.copy()
        if hovered and playable:
            draw_rect.y -= 9

        _draw_card(surface, card, draw_rect, card_fronts, card_back=card_back, face_up=True)

        if playable:
            pygame.draw.rect(
                surface,
                (255, 218, 82) if not hovered else (255, 245, 180),
                draw_rect,
                3 if not hovered else 5,
                border_radius=5,
            )

    draw_enabled = game.can_player_draw()
    _draw_button(
        surface,
        _DRAW_RECT,
        "Draw Card",
        mouse_pos,
        fonts["medium"],
        enabled=draw_enabled,
    )

    if not game.game_over and game.current_player == 0 and not game.waiting_for_suit_choice:
        if game.has_playable_card(0):
            hint = "Play a card matching the active suit or rank. Eights are wild."
        else:
            hint = "No legal play. Draw one card."
        hint_surface = fonts["tiny"].render(hint, True, (220, 225, 215))
        surface.blit(hint_surface, (70, 735))

    # Suit choice overlay for a human-played eight.
    if game.waiting_for_suit_choice and not game.game_over:
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 145))
        surface.blit(shade, (0, 0))

        panel = pygame.Rect(420, 285, 526, 210)
        _draw_panel(surface, panel, fill=(18, 24, 20, 245), border=(255, 220, 105), width=3)

        header = fonts["large"].render("Eight played! Choose the new suit", True, (255, 245, 215))
        surface.blit(header, header.get_rect(center=(683, 337)))

        for suit, rect in _SUIT_RECTS.items():
            _draw_suit_button(surface, rect, suit, mouse_pos, fonts["small"])

    # Game over result overlay.
    if game.game_over:
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 125))
        surface.blit(shade, (0, 0))

        panel = pygame.Rect(383, 330, 600, 320)
        _draw_panel(surface, panel, fill=(18, 24, 20, 245), border=(255, 220, 105), width=3)

        header = fonts["title"].render(
            "YOU WIN!" if game.winner_index == 0 else "ROUND COMPLETE",
            True,
            (255, 224, 100),
        )
        surface.blit(header, header.get_rect(center=(683, 385)))

        result = fonts["medium"].render(game.result_text, True, (245, 245, 240))
        surface.blit(result, result.get_rect(center=(683, 448)))

        if game.winner_index == 0:
            reward = fonts["small"].render(
                "Career reward: +60 Overall Rating and fan gain",
                True,
                (205, 230, 205),
            )
            surface.blit(reward, reward.get_rect(center=(683, 500)))

        _draw_button(surface, _CONTINUE_RECT, "Continue", mouse_pos, fonts["medium"], enabled=True)


def get_crazy_eights_action(mouse_pos, game):
    if mouse_pos is None:
        return None

    if game.game_over:
        if _CONTINUE_RECT.collidepoint(mouse_pos):
            return (ACTION_CONTINUE, None)
        return None

    if _RETURN_RECT.collidepoint(mouse_pos):
        return (ACTION_RETURN, None)

    if game.waiting_for_suit_choice:
        for suit, rect in _SUIT_RECTS.items():
            if rect.collidepoint(mouse_pos):
                return (ACTION_SUIT, suit)
        return None

    if game.current_player != 0:
        return None

    for index in range(len(_player_card_rects) - 1, -1, -1):
        if _player_card_rects[index].collidepoint(mouse_pos):
            return (ACTION_CARD, index)

    if _DRAW_RECT.collidepoint(mouse_pos) and game.can_player_draw():
        return (ACTION_DRAW, None)

    return None
