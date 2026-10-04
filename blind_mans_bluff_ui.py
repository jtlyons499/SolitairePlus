import pygame

from niche_poker_common import RANK_VALUES
from poker_core import format_poker_display_name


ACTION_RETURN = "return"
ACTION_NEXT_HAND = "next_hand"
ACTION_CHECK = "check"
ACTION_BET = "bet"
ACTION_CALL = "call"
ACTION_FOLD = "fold"

BET_PRESET_RECTS = {
    "MIN": pygame.Rect(785, 640, 100, 34),
    "1/2 POT": pygame.Rect(895, 640, 100, 34),
    "POT": pygame.Rect(1005, 640, 100, 34),
    "MAX": pygame.Rect(1115, 640, 100, 34),
}
_selected_bet_label = "POT"

WHITE = (245, 245, 240)
CREAM = (236, 221, 181)
GOLD = (226, 187, 78)
RED = (190, 70, 70)
DARK = (18, 23, 24)

CARD_SIZE = (84, 118)
BLUFF_RETURN_RECT = pygame.Rect(1120, 25, 205, 44)
BLUFF_NEXT_RECT = pygame.Rect(895, 690, 205, 44)
BLUFF_ACTION_RECTS = {
    ACTION_FOLD: pygame.Rect(800, 690, 135, 44),
    ACTION_CHECK: pygame.Rect(945, 690, 150, 44),
    ACTION_CALL: pygame.Rect(945, 690, 150, 44),
    ACTION_BET: pygame.Rect(1105, 690, 150, 44),
}

NPC_CENTERS = (
    (310, 220),
    (683, 160),
    (1056, 220),
)

_scaled_card_cache = {}
_portrait_cache = {}


def _card_key(card):
    if not card:
        return None
    suit_letter = {
        "Clubs": "C",
        "Diamonds": "D",
        "Hearts": "H",
        "Spades": "S",
    }.get(card.get("suit"))
    if not suit_letter:
        return None
    return f"{card.get('rank')}{suit_letter}"


def _load_card(card, card_fronts, size=CARD_SIZE):
    key = _card_key(card)
    if key is None or not isinstance(card_fronts, dict):
        return None
    source = card_fronts.get(key)
    if source is None:
        return None
    cache_key = (key, tuple(size), id(source))
    if cache_key not in _scaled_card_cache:
        _scaled_card_cache[cache_key] = pygame.transform.smoothscale(source, size)
    return _scaled_card_cache[cache_key]


def _load_portrait(npc, size=(82, 82)):
    path = npc.get("portrait") if isinstance(npc, dict) else None
    key = (path, size)
    if key in _portrait_cache:
        return _portrait_cache[key]
    image = None
    if path:
        try:
            image = pygame.image.load(path).convert_alpha()
            image = pygame.transform.smoothscale(image, size)
        except (pygame.error, FileNotFoundError):
            image = None
    _portrait_cache[key] = image
    return image


def _draw_card(surface, card, rect, font, card_fronts, card_back_surface, face_up=True):
    image = _load_card(card, card_fronts, rect.size) if face_up else card_back_surface
    if image is not None and image.get_size() != rect.size:
        image = pygame.transform.smoothscale(image, rect.size)
    if image is not None:
        surface.blit(image, rect)
        return
    pygame.draw.rect(surface, WHITE if face_up else (48, 73, 145), rect, border_radius=5)
    pygame.draw.rect(surface, DARK, rect, 2, border_radius=5)
    if face_up and card:
        text = font.render(f"{card['rank']} {card['suit'][0]}", True, DARK)
        surface.blit(text, text.get_rect(center=rect.center))


def _draw_button(surface, rect, text, mouse_pos, font, enabled=True, accent=False):
    hovered = enabled and mouse_pos is not None and rect.collidepoint(mouse_pos)
    if enabled:
        fill = (45, 105, 73) if hovered else (29, 72, 54)
        border = GOLD if hovered or accent else (220, 225, 222)
        color = WHITE
    else:
        fill = (58, 62, 61)
        border = (118, 124, 121)
        color = (148, 152, 150)
    pygame.draw.rect(surface, fill, rect, border_radius=8)
    pygame.draw.rect(surface, border, rect, 3 if hovered else 2, border_radius=8)
    label = font.render(text, True, color)
    surface.blit(label, label.get_rect(center=rect.center))


def get_blind_mans_bluff_bet_amount(game):
    presets = game.get_player_bet_presets()
    if not presets:
        return 0

    by_label = {label: amount for label, amount in presets}
    if _selected_bet_label in by_label:
        return by_label[_selected_bet_label]

    # POT can collapse into another amount when stacks are short. Prefer the
    # largest non-all-in option, then fall back to the maximum legal bet.
    if len(presets) >= 2:
        return presets[-2][1]
    return presets[-1][1]


def get_blind_mans_bluff_action(mouse_pos, game):
    global _selected_bet_label
    if mouse_pos is None:
        return None
    if game.hand_complete:
        if BLUFF_RETURN_RECT.collidepoint(mouse_pos):
            return ACTION_RETURN
        if game.can_start_next_hand() and BLUFF_NEXT_RECT.collidepoint(mouse_pos):
            return ACTION_NEXT_HAND

    actions = set(game.get_player_actions())

    if ACTION_BET in actions:
        available_labels = {label for label, _ in game.get_player_bet_presets()}
        for label, rect in BET_PRESET_RECTS.items():
            if label in available_labels and rect.collidepoint(mouse_pos):
                _selected_bet_label = label
                return None

    for action in (ACTION_FOLD, ACTION_CHECK, ACTION_CALL, ACTION_BET):
        if action in actions and BLUFF_ACTION_RECTS[action].collidepoint(mouse_pos):
            return action
    return None


def draw_blind_mans_bluff(
        surface,
        mouse_pos,
        game,
        player_name,
        draw_submenu_background,
        title_font,
        label_font,
        detail_font,
        card_fronts=None,
        card_back_surface=None,
):
    draw_submenu_background(overlay_alpha=112)

    title = title_font.render("BLIND MAN'S BLUFF", True, WHITE)
    surface.blit(title, title.get_rect(center=(683, 42)))

    # A table only, with no rectangular panel behind it. This keeps the screen
    # in the same darker-modern family as the poker tables without the old box.
    table = pygame.Rect(150, 95, 1066, 530)
    pygame.draw.ellipse(surface, (82, 54, 35), table, 14)
    inner = table.inflate(-26, -26)
    pygame.draw.ellipse(surface, (28, 103, 67), inner)
    pygame.draw.ellipse(surface, (225, 214, 178), inner, 2)

    opener_name = game.get_name(getattr(game, "opening_index", 0))
    opener_badge = pygame.Rect(555, 86, 256, 34)
    badge = pygame.Surface(opener_badge.size, pygame.SRCALPHA)
    badge.fill((12, 27, 23, 205))
    surface.blit(badge, opener_badge.topleft)
    pygame.draw.rect(surface, GOLD, opener_badge, 2, border_radius=10)
    opener_text = detail_font.render(f"Opening action: {opener_name}", True, CREAM)
    surface.blit(opener_text, opener_text.get_rect(center=opener_badge.center))

    for npc_index, npc in enumerate(game.npcs):
        if npc_index >= len(NPC_CENTERS):
            break
        table_index = npc_index + 1
        cx, cy = NPC_CENTERS[npc_index]
        portrait_rect = pygame.Rect(cx - 41, cy - 15, 82, 82)
        portrait = _load_portrait(npc, portrait_rect.size)
        if portrait is not None:
            surface.blit(portrait, portrait_rect)
        else:
            pygame.draw.rect(surface, (60, 69, 68), portrait_rect, border_radius=12)
        pygame.draw.rect(surface, GOLD, portrait_rect, 2, border_radius=12)

        card_rect = pygame.Rect(cx - 42, cy - 130, *CARD_SIZE)
        card = game.cards[table_index] if table_index < len(game.cards) else None
        _draw_card(surface, card, card_rect, detail_font, card_fronts, card_back_surface, face_up=True)

        name = format_poker_display_name(npc.get("name", "Opponent"))
        name_surface = label_font.render(name, True, WHITE)
        surface.blit(name_surface, name_surface.get_rect(center=(cx, cy + 82)))
        stack = game.npc_stacks[npc_index] if npc_index < len(game.npc_stacks) else 0
        stack_surface = detail_font.render(f"${stack:,}", True, CREAM)
        surface.blit(stack_surface, stack_surface.get_rect(center=(cx, cy + 108)))

        if table_index < len(game.folded) and game.folded[table_index]:
            shade = pygame.Surface(card_rect.size, pygame.SRCALPHA)
            shade.fill((0, 0, 0, 135))
            surface.blit(shade, card_rect.topleft)
            fold = label_font.render("FOLDED", True, RED)
            surface.blit(fold, fold.get_rect(center=card_rect.center))

        if game.hand_complete and table_index in game.last_winner_indexes:
            pygame.draw.rect(surface, GOLD, card_rect.inflate(8, 8), 4, border_radius=7)

        if table_index < len(game.last_actions) and game.last_actions[table_index]:
            action = detail_font.render(game.last_actions[table_index], True, (225, 230, 227))
            surface.blit(action, action.get_rect(center=(cx, cy + 132)))

    player_card_rect = pygame.Rect(641, 465, *CARD_SIZE)
    player_card = game.cards[0] if game.cards else None
    reveal_player = game.hand_complete
    _draw_card(
        surface,
        player_card,
        player_card_rect,
        detail_font,
        card_fronts,
        card_back_surface,
        face_up=reveal_player,
    )
    if not reveal_player:
        hidden = detail_font.render("YOUR CARD IS FACING THE TABLE", True, GOLD)
        surface.blit(hidden, hidden.get_rect(center=(683, 599)))
    elif 0 in game.last_winner_indexes:
        pygame.draw.rect(surface, GOLD, player_card_rect.inflate(8, 8), 4, border_radius=7)

    player_label = label_font.render(str(player_name or "Player"), True, WHITE)
    surface.blit(player_label, player_label.get_rect(center=(683, 627)))

    status_rect = pygame.Rect(438, 305, 490, 142)
    status_panel = pygame.Surface(status_rect.size, pygame.SRCALPHA)
    status_panel.fill((13, 26, 23, 218))
    surface.blit(status_panel, status_rect.topleft)
    pygame.draw.rect(surface, (137, 158, 148), status_rect, 2, border_radius=12)

    pot = label_font.render(f"Pot: ${game.pot:,}", True, GOLD)
    surface.blit(pot, pot.get_rect(center=(683, 330)))
    stakes = detail_font.render(
        f"Ante ${game.ante:,}  •  Open ${game.get_min_open_bet():,}-${game.get_max_open_bet():,}",
        True,
        CREAM,
    )
    surface.blit(stakes, stakes.get_rect(center=(683, 361)))

    visible_cards = [
        game.cards[index]
        for index in game.get_active_indexes()
        if index != 0 and game.cards[index] is not None
    ] if game.cards else []
    if visible_cards and not game.hand_complete:
        visible_high = max(visible_cards, key=lambda card: RANK_VALUES[card["rank"]])
        info_text = f"Highest card you can see: {visible_high['rank']}"
    else:
        info_text = game.result_text
    info = detail_font.render(info_text, True, WHITE)
    surface.blit(info, info.get_rect(center=(683, 395)))

    if game.bet_state == "player_response" and not game.hand_complete:
        response_text = f"Facing ${game.current_bet:,}: call blind or fold."
    elif game.bet_state == "player_last_open" and not game.hand_complete:
        response_text = "Everyone checked before you. Check behind or choose an opening size."
    elif not game.hand_complete:
        response_text = "Everyone else can see your card. Read their betting, not your own hand."
    else:
        response_text = ""

    if response_text:
        response = detail_font.render(response_text, True, (235, 215, 155))
        surface.blit(response, response.get_rect(center=(683, 425)))

    actions = set(game.get_player_actions())
    if not game.hand_complete:
        if ACTION_FOLD in actions:
            _draw_button(surface, BLUFF_ACTION_RECTS[ACTION_FOLD], "FOLD", mouse_pos, label_font)
        if ACTION_CHECK in actions:
            _draw_button(surface, BLUFF_ACTION_RECTS[ACTION_CHECK], "CHECK", mouse_pos, label_font)
        if ACTION_CALL in actions:
            _draw_button(surface, BLUFF_ACTION_RECTS[ACTION_CALL], f"CALL ${game.current_bet:,}", mouse_pos, label_font)
        if ACTION_BET in actions:
            presets = game.get_player_bet_presets()
            available = {label: amount for label, amount in presets}
            for label, rect in BET_PRESET_RECTS.items():
                if label not in available:
                    continue
                selected = (label == _selected_bet_label)
                _draw_button(
                    surface,
                    rect,
                    f"{label} ${available[label]:,}",
                    mouse_pos,
                    detail_font,
                    accent=selected,
                )
            bet_amount = get_blind_mans_bluff_bet_amount(game)
            _draw_button(
                surface,
                BLUFF_ACTION_RECTS[ACTION_BET],
                f"BET ${bet_amount:,}",
                mouse_pos,
                label_font,
                accent=True,
            )

    if game.hand_complete:
        result = detail_font.render(game.result_text, True, WHITE)
        surface.blit(result, result.get_rect(center=(683, 666)))
        _draw_button(surface, BLUFF_NEXT_RECT, "NEXT HAND", mouse_pos, label_font, enabled=game.can_start_next_hand())
        _draw_button(surface, BLUFF_RETURN_RECT, "CASH OUT", mouse_pos, label_font, accent=True)
    else:
        _draw_button(surface, BLUFF_RETURN_RECT, "CASH OUT", mouse_pos, label_font, enabled=False)

    session = detail_font.render(
        f"Session: {game.get_session_net():+d}   Hands: {game.hands_played}",
        True,
        (216, 222, 219),
    )
    surface.blit(session, (156, 702))
