import pygame


ACTION_RETURN = "return"
ACTION_CALL = "call"
ACTION_CONTINUE = "continue"


_RETURN_RECT = pygame.Rect(1218, 22, 118, 40)
_CALL_RECT = pygame.Rect(598, 397, 250, 48)
_CONTINUE_RECT = pygame.Rect(533, 600, 300, 52)

_fonts = None


SUIT_NAMES = {
    "C": "Clubs",
    "D": "Diamonds",
    "H": "Hearts",
    "S": "Spades",
}


def _get_fonts():
    global _fonts
    if _fonts is None:
        _fonts = {
            "title": pygame.font.SysFont("cambria", 40, bold=True),
            "large": pygame.font.SysFont("cambria", 25, bold=True),
            "medium": pygame.font.SysFont("cambria", 18, bold=True),
            "small": pygame.font.SysFont("cambria", 14, bold=True),
            "tiny": pygame.font.SysFont("cambria", 12),
        }
    return _fonts


def _draw_panel(surface, rect, fill=(22, 31, 45, 230), border=(190, 200, 215), width=2):
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, fill, panel.get_rect(), border_radius=11)
    pygame.draw.rect(panel, (*border, 245), panel.get_rect(), width, border_radius=11)
    surface.blit(panel, rect.topleft)


def _draw_button(surface, rect, label, mouse_pos, font, enabled=True):
    hovered = enabled and mouse_pos is not None and rect.collidepoint(mouse_pos)

    if not enabled:
        fill = (65, 68, 75)
        border = (105, 110, 120)
        text_color = (150, 155, 165)
    elif hovered:
        fill = (56, 92, 126)
        border = (255, 225, 120)
        text_color = (255, 255, 255)
    else:
        fill = (42, 70, 100)
        border = (200, 210, 225)
        text_color = (245, 245, 250)

    pygame.draw.rect(surface, fill, rect, border_radius=9)
    pygame.draw.rect(surface, border, rect, 2, border_radius=9)
    text = font.render(label, True, text_color)
    surface.blit(text, text.get_rect(center=rect.center))


def _draw_card(surface, card, rect, card_fronts, card_back, face_up=True):
    image = None
    if face_up and card:
        image = card_fronts.get(f"{card['rank']}{card['suit']}")
    elif card_back is not None:
        image = card_back

    if image is None:
        pygame.draw.rect(surface, (238, 238, 235), rect, border_radius=4)
        pygame.draw.rect(surface, (30, 30, 35), rect, 2, border_radius=4)
        return

    scaled = pygame.transform.smoothscale(image, rect.size)
    surface.blit(scaled, rect.topleft)


def _draw_portrait(surface, npc, rect, portrait_loader):
    portrait = None
    if portrait_loader is not None:
        try:
            portrait = portrait_loader(npc, max(rect.width, rect.height))
        except Exception:
            portrait = None

    pygame.draw.rect(surface, (38, 42, 50), rect, border_radius=7)

    if portrait is not None:
        portrait = pygame.transform.smoothscale(portrait, rect.size)
        surface.blit(portrait, rect.topleft)
    else:
        fonts = _get_fonts()
        initials = "".join(part[:1] for part in str(npc.get("name", "NPC")).split()[:2]).upper() or "?"
        text = fonts["medium"].render(initials, True, (245, 245, 245))
        surface.blit(text, text.get_rect(center=rect.center))

    pygame.draw.rect(surface, (205, 210, 220), rect, 2, border_radius=7)


def _draw_hand(surface, hand, start_x, y, card_fronts, card_back, width, height, gap, last_called_key=None):
    for index, item in enumerate(hand):
        rect = pygame.Rect(start_x + index * gap, y, width, height)
        card = item["card"]
        marked = bool(item["marked"])
        _draw_card(
            surface,
            card,
            rect,
            card_fronts,
            card_back,
            face_up=not marked,
        )

        if last_called_key and f"{card['rank']}{card['suit']}" == last_called_key:
            pygame.draw.rect(surface, (255, 215, 80), rect, 4, border_radius=5)


def draw_bango(
        surface,
        mouse_pos,
        game,
        card_fronts,
        card_back,
        portrait_loader=None,
):
    fonts = _get_fonts()
    surface.fill((32, 72, 104))

    title = fonts["title"].render("BANGO!", True, (255, 245, 205))
    surface.blit(title, title.get_rect(center=(683, 48)))

    subtitle = fonts["small"].render(
        "The caller uses a second deck. Cover all five of your cards first.",
        True,
        (225, 235, 245),
    )
    surface.blit(subtitle, subtitle.get_rect(center=(683, 84)))

    _draw_button(surface, _RETURN_RECT, "Return", mouse_pos, fonts["small"], enabled=True)

    last_called_key = None
    if game.last_called_card:
        last_called_key = f"{game.last_called_card['rank']}{game.last_called_card['suit']}"

    # NPC panels across the upper half.
    panel_xs = (55, 438, 821)
    for npc_index, npc in enumerate(game.npcs[:3]):
        player_index = npc_index + 1
        panel = pygame.Rect(panel_xs[npc_index], 115, 490 if npc_index == 1 else 490, 170)

        # Keep three 340px panels from overlapping by using a compact custom width.
        panel.width = 330
        if npc_index == 1:
            panel.x = 518
        elif npc_index == 2:
            panel.x = 901
            panel.width = 410

        # Re-normalize into three even compact panels.
        compact_xs = (45, 466, 887)
        panel = pygame.Rect(compact_xs[npc_index], 115, 390, 170)
        _draw_panel(surface, panel)

        portrait_rect = pygame.Rect(panel.x + 12, panel.y + 12, 52, 52)
        _draw_portrait(surface, npc, portrait_rect, portrait_loader)

        name = str(npc.get("name", "NPC"))
        if len(name) > 22:
            name = name[:20] + "..."
        name_surf = fonts["small"].render(name, True, (245, 245, 250))
        surface.blit(name_surf, (panel.x + 74, panel.y + 15))

        marked_count = game.get_marked_count(player_index)
        progress = fonts["tiny"].render(
            f"Covered: {marked_count}/5",
            True,
            (205, 215, 230),
        )
        surface.blit(progress, (panel.x + 74, panel.y + 40))

        if player_index < len(game.hands):
            _draw_hand(
                surface,
                game.hands[player_index],
                panel.x + 12,
                panel.y + 80,
                card_fronts,
                card_back,
                width=48,
                height=67,
                gap=60,
                last_called_key=last_called_key,
            )

    # Caller area.
    caller_panel = pygame.Rect(470, 310, 426, 160)
    _draw_panel(surface, caller_panel, fill=(18, 32, 50, 235), border=(255, 220, 105), width=2)

    if game.last_called_card is not None:
        call_card_rect = pygame.Rect(492, 325, 76, 106)
        _draw_card(
            surface,
            game.last_called_card,
            call_card_rect,
            card_fronts,
            card_back,
            face_up=True,
        )

        call_text = fonts["medium"].render(
            f"Called: {game.card_label(game.last_called_card)}",
            True,
            (250, 245, 230),
        )
        surface.blit(call_text, (585, 333))
    else:
        waiting = fonts["medium"].render("Caller is ready.", True, (250, 245, 230))
        surface.blit(waiting, waiting.get_rect(center=(683, 347)))

    remaining = fonts["tiny"].render(
        f"Calls: {game.call_count}    Caller deck remaining: {len(game.caller_deck)}",
        True,
        (205, 215, 230),
    )
    surface.blit(remaining, remaining.get_rect(center=(683, 374)))

    _draw_button(
        surface,
        _CALL_RECT,
        "Call Next Card",
        mouse_pos,
        fonts["medium"],
        enabled=not game.game_over,
    )

    # Human hand.
    player_panel = pygame.Rect(255, 493, 856, 230)
    _draw_panel(surface, player_panel, fill=(22, 31, 45, 232), border=(220, 225, 235), width=2)

    header = fonts["large"].render("YOUR CARDS", True, (255, 245, 215))
    surface.blit(header, header.get_rect(center=(683, 527)))

    marked = game.get_marked_count(0)
    status = fonts["small"].render(
        f"Covered: {marked}/5",
        True,
        (210, 220, 235),
    )
    surface.blit(status, status.get_rect(center=(683, 558)))

    if game.hands:
        hand = game.hands[0]
        width = 82
        height = 115
        gap = 108
        total_width = width + gap * (len(hand) - 1)
        start_x = 683 - total_width // 2
        _draw_hand(
            surface,
            hand,
            start_x,
            582,
            card_fronts,
            card_back,
            width=width,
            height=height,
            gap=gap,
            last_called_key=last_called_key,
        )

    if game.game_over:
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 145))
        surface.blit(shade, (0, 0))

        panel = pygame.Rect(383, 315, 600, 350)
        _draw_panel(surface, panel, fill=(18, 27, 42, 248), border=(255, 220, 105), width=3)

        bango = fonts["title"].render("BANGO!", True, (255, 220, 90))
        surface.blit(bango, bango.get_rect(center=(683, 375)))

        result = game.result_text
        if len(result) > 64:
            result = result[:61] + "..."
        result_surf = fonts["medium"].render(result, True, (245, 245, 248))
        surface.blit(result_surf, result_surf.get_rect(center=(683, 435)))

        if game.winner_index == 0:
            reward = fonts["small"].render(
                "Career reward: XP and fans",
                True,
                (205, 230, 210),
            )
            surface.blit(reward, reward.get_rect(center=(683, 488)))

        _draw_button(surface, _CONTINUE_RECT, "Continue", mouse_pos, fonts["medium"], enabled=True)


def get_bango_action(mouse_pos, game):
    if mouse_pos is None:
        return None

    if game.game_over:
        if _CONTINUE_RECT.collidepoint(mouse_pos):
            return ACTION_CONTINUE
        return None

    if _RETURN_RECT.collidepoint(mouse_pos):
        return ACTION_RETURN

    if _CALL_RECT.collidepoint(mouse_pos):
        return ACTION_CALL

    return None

