import pygame
from poker_speech import is_poker_chat_popups_enabled

from poker_core import format_poker_display_name


ACTION_RETURN = "return"
ACTION_NEXT_HAND = "next_hand"
ACTION_CHECK = "check"
ACTION_BET = "bet"
ACTION_CALL = "call"
ACTION_FOLD = "fold"
ACTION_COLUMN_PREFIX = "column_"

WHITE = (245, 245, 240)
CREAM = (238, 224, 184)
GOLD = (228, 188, 76)
GREEN = (61, 173, 97)
RED = (194, 74, 74)
DARK = (19, 25, 25)

CARD_SIZE = (132, 185)
DRAW_CARD_SIZE = (132, 185)
STACK_OFFSET = 26

FIVE_O_RETURN_RECT = pygame.Rect(1130, 25, 195, 44)
FIVE_O_NEXT_RECT = pygame.Rect(905, 722, 205, 40)
FIVE_O_ACTION_RECTS = {
    ACTION_FOLD: pygame.Rect(800, 722, 135, 40),
    ACTION_CHECK: pygame.Rect(945, 722, 150, 40),
    ACTION_CALL: pygame.Rect(945, 722, 150, 40),
    ACTION_BET: pygame.Rect(1105, 722, 150, 40),
}

FIVE_O_PLAYER_COLUMN_RECTS = [
    pygame.Rect(360 + index * 190, 400, 156, 293)
    for index in range(5)
]

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


def _load_portrait(npc, size=(86, 86)):
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


def _draw_card(surface, card, rect, detail_font, card_fronts, card_back_surface=None, face_up=True):
    if face_up:
        image = _load_card(card, card_fronts, rect.size)
    else:
        image = card_back_surface
        if image is not None and image.get_size() != rect.size:
            image = pygame.transform.smoothscale(image, rect.size)

    if image is not None:
        surface.blit(image, rect)
        if not face_up:
            return

    if image is None:
        pygame.draw.rect(surface, WHITE if face_up else (45, 70, 145), rect, border_radius=4)
        pygame.draw.rect(surface, DARK, rect, 2, border_radius=4)
    if face_up and card:
        font = pygame.font.Font(None, 27)
        color = (172, 32, 42) if card.get("suit") in ("Diamonds", "Hearts") else DARK
        label = font.render(str(card.get('rank', '?')), True, color)
        badge = pygame.Rect(rect.x + 4, rect.y + 2, label.get_width() + 26, 24)
        pygame.draw.rect(surface, WHITE, badge, border_radius=3)
        surface.blit(label, (badge.x + 4, badge.y))
        x, y = badge.right - 13, badge.y + 12
        suit = card.get("suit")
        # Draw suit symbols directly: pygame's bundled font lacks these glyphs
        # on some machines. All four suits remain recognisable on stacked cards.
        if suit == "Diamonds":
            pygame.draw.polygon(surface, color, [(x,y-9),(x+7,y),(x,y+9),(x-7,y)])
        elif suit == "Hearts":
            pygame.draw.circle(surface, color, (x-4,y-3), 5)
            pygame.draw.circle(surface, color, (x+4,y-3), 5)
            pygame.draw.polygon(surface, color, [(x-9,y-2),(x+9,y-2),(x,y+9)])
        elif suit == "Spades":
            pygame.draw.polygon(surface, color, [(x,y-9),(x-8,y+2),(x+8,y+2)])
            pygame.draw.circle(surface, color, (x-4,y+2), 4)
            pygame.draw.circle(surface, color, (x+4,y+2), 4)
            pygame.draw.rect(surface, color, (x-2,y+2,4,8))
        else:
            for center in ((x,y-5),(x-5,y+1),(x+5,y+1)):
                pygame.draw.circle(surface, color, center, 5)
            pygame.draw.rect(surface, color, (x-2,y+2,4,8))






def _draw_column(
        surface,
        column,
        rect,
        detail_font,
        card_fronts,
        card_back_surface,
        hidden_to_viewer=False,
        showdown=False,
):
    cards = list(column or [])
    for index, card in enumerate(cards):
        card_rect = pygame.Rect(rect.centerx - CARD_SIZE[0] // 2, rect.y + index * STACK_OFFSET, *CARD_SIZE)
        face_up = not (
            hidden_to_viewer
            and index == 3
            and not showdown
        )
        _draw_card(
            surface,
            card,
            card_rect,
            detail_font,
            card_fronts,
            card_back_surface=card_back_surface,
            face_up=face_up,
        )


def _draw_button(surface, rect, text, mouse_pos, font, enabled=True, accent=False):
    hovered = enabled and mouse_pos is not None and rect.collidepoint(mouse_pos)
    if not enabled:
        fill = (59, 63, 62)
        border = (120, 125, 123)
        text_color = (145, 148, 147)
    else:
        fill = (50, 108, 75) if hovered else (31, 76, 58)
        border = GOLD if (hovered or accent) else (220, 224, 221)
        text_color = WHITE
    pygame.draw.rect(surface, fill, rect, border_radius=8)
    pygame.draw.rect(surface, border, rect, 3 if hovered else 2, border_radius=8)
    label = font.render(text, True, text_color)
    surface.blit(label, label.get_rect(center=rect.center))


def _fit_line(font, text, max_width, color=WHITE):
    if font.size(text)[0] <= max_width:
        return font.render(text, True, color)
    shortened = str(text)
    while shortened and font.size(shortened + "...")[0] > max_width:
        shortened = shortened[:-1]
    return font.render(shortened.rstrip() + "...", True, color)


def get_five_o_action(mouse_pos, game):
    if mouse_pos is None:
        return None

    if game.hand_complete:
        if FIVE_O_RETURN_RECT.collidepoint(mouse_pos):
            return ACTION_RETURN
        if game.can_start_next_hand() and FIVE_O_NEXT_RECT.collidepoint(mouse_pos):
            return ACTION_NEXT_HAND

    if game.phase == "placement":
        for index in game.get_available_player_columns():
            if FIVE_O_PLAYER_COLUMN_RECTS[index].collidepoint(mouse_pos):
                return f"{ACTION_COLUMN_PREFIX}{index}"

    actions = set(game.get_player_actions())
    for action in (ACTION_FOLD, ACTION_CHECK, ACTION_CALL, ACTION_BET):
        if action in actions and FIVE_O_ACTION_RECTS[action].collidepoint(mouse_pos):
            return action

    return None


def draw_five_o_poker(
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
    draw_submenu_background(overlay_alpha=105)
    title = title_font.render("FIVE-O POKER", True, WHITE)
    surface.blit(title, title.get_rect(center=(683, 36)))
    panel = pygame.Surface((320, 620), pygame.SRCALPHA)
    panel.fill((13, 29, 25, 225))
    surface.blit(panel, (20, 75))
    font = pygame.font.Font(None, 25)
    def line(value, y, color=WHITE):
        surface.blit(_fit_line(font, value, 296, color), (32, y))
    def wrap(value, y, color=WHITE):
        words = str(value).split()
        rows = [""]
        for word in words:
            trial = (rows[-1] + " " + word).strip()
            if font.size(trial)[0] > 296 and rows[-1]:
                rows.append(word)
            else:
                rows[-1] = trial
        for row in rows:
            line(row, y, color)
            y += 25
        return y
    line(game.get_npc_name(), 86, GOLD)
    line(f"Opponent stack: ${game.npc_stack:,}", 116, CREAM)
    line(f"{player_name or 'Player'}: ${game.player_stack:,}", 150)
    line(f"Pot: ${game.pot:,}", 184, GOLD)
    line(f"Ante ${game.ante:,}  /  Bet ${game.bet_unit:,}", 214, CREAM)
    revealed = game.get_showdown_revealed_count()
    available = set(game.get_available_player_columns())
    for index, player_rect in enumerate(FIVE_O_PLAYER_COLUMN_RECTS):
        npc_rect = pygame.Rect(player_rect.x, 78, player_rect.w, player_rect.h)
        result = game.column_results[index] if index < revealed else None
        color = {"player": GREEN, "npc": RED, "tie": GOLD}.get(result, (130, 150, 140))
        for rect in (npc_rect, player_rect):
            pygame.draw.rect(surface, (25, 58, 46), rect, border_radius=8)
            pygame.draw.rect(surface, color, rect, 2, border_radius=8)
        if index in available:
            pygame.draw.rect(surface, GOLD, player_rect, 4, border_radius=8)
        _draw_column(surface, game.npc_columns[index], npc_rect, font, card_fronts,
                     card_back_surface, hidden_to_viewer=True, showdown=index < revealed)
        _draw_column(surface, game.player_columns[index], player_rect, font, card_fronts,
                     card_back_surface, hidden_to_viewer=True, showdown=index < revealed)
        tag = {"player": "YOU WIN", "npc": "NPC WINS", "tie": "TIE"}.get(result, f"COLUMN {index + 1}")
        label = font.render(tag, True, color if result else CREAM)
        surface.blit(label, label.get_rect(center=(player_rect.centerx, 385)))
    if game.phase == "placement" and game.player_drawn_card:
        _draw_card(surface, game.player_drawn_card, pygame.Rect(112, 280, *DRAW_CARD_SIZE),
                   font, card_fronts, card_back_surface)
        line("DRAWN CARD", 250, GOLD)
        y = wrap(f"Layer {game.placement_round} of 5: choose a highlighted column.", 490)
        wrap("The fourth card stays face down until its column is revealed.", y + 14, CREAM)
    elif game.phase == "betting":
        line("BETTING ROUND", 258, GOLD)
        wrap(game.result_text, 295)
    else:
        line(f"Columns: You {game.player_column_wins} / NPC {game.npc_column_wins}", 250, GOLD)
        y = 284
        for index in range(revealed):
            result = game.column_results[index]
            color = {"player": GREEN, "npc": RED, "tie": GOLD}.get(result, WHITE)
            line(f"{index + 1}. " + {"player": "You win", "npc": "Opponent wins", "tie": "Tie"}.get(result, ""), y, color)
            line("You: " + game.get_column_description("player", index), y + 23)
            line("NPC: " + game.get_column_description("npc", index), y + 46)
            y += 76
        if game.hand_complete:
            # Result gets its own full-width footer, away from the five comparisons.
            label = _fit_line(font, game.result_text, 740, GOLD)
            surface.blit(label, (32, 697))
    actions = set(game.get_player_actions())
    for action in (ACTION_FOLD, ACTION_CHECK, ACTION_CALL, ACTION_BET):
        if action in actions:
            label = action.upper()
            if action == ACTION_CALL: label += f" ${game.current_bet:,}"
            if action == ACTION_BET: label += f" ${game.get_effective_bet_unit():,}"
            rect = FIVE_O_ACTION_RECTS[action]
            _draw_button(surface, rect, label, mouse_pos, font, accent=action == ACTION_BET)
    if game.hand_complete:
        _draw_button(surface, FIVE_O_NEXT_RECT, "NEXT HAND", mouse_pos, font,
                     enabled=game.can_start_next_hand())
    _draw_button(surface, FIVE_O_RETURN_RECT, "CASH OUT", mouse_pos, font,
                 enabled=game.hand_complete, accent=game.hand_complete)
    line(f"Session {game.get_session_net():+d}  /  Hands {game.hands_played}", 737, CREAM)
