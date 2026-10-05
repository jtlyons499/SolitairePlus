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

CARD_SIZE = (88, 123)
DRAW_CARD_SIZE = (90, 126)
STACK_OFFSET = 16

FIVE_O_RETURN_RECT = pygame.Rect(1130, 25, 195, 44)
FIVE_O_NEXT_RECT = pygame.Rect(905, 690, 205, 44)
FIVE_O_ACTION_RECTS = {
    ACTION_FOLD: pygame.Rect(800, 690, 135, 44),
    ACTION_CHECK: pygame.Rect(945, 690, 150, 44),
    ACTION_CALL: pygame.Rect(945, 690, 150, 44),
    ACTION_BET: pygame.Rect(1105, 690, 150, 44),
}

FIVE_O_PLAYER_COLUMN_RECTS = [
    pygame.Rect(360 + index * 125, 452, 110, 190)
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
        return

    pygame.draw.rect(surface, WHITE if face_up else (45, 70, 145), rect, border_radius=4)
    pygame.draw.rect(surface, DARK, rect, 2, border_radius=4)
    if face_up and card:
        fallback = detail_font.render(
            f"{card.get('rank', '?')} {str(card.get('suit', '?'))[:1]}",
            True,
            DARK,
        )
        surface.blit(fallback, fallback.get_rect(center=rect.center))


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
    surface.blit(title, title.get_rect(center=(683, 42)))

    table = pygame.Rect(105, 76, 1156, 590)
    table_panel = pygame.Surface(table.size, pygame.SRCALPHA)
    table_panel.fill((15, 75, 49, 228))
    surface.blit(table_panel, table.topleft)
    pygame.draw.rect(surface, CREAM, table, 3, border_radius=28)

    npc = game.npc if isinstance(game.npc, dict) else {}
    portrait_rect = pygame.Rect(132, 112, 86, 86)
    portrait = _load_portrait(npc, portrait_rect.size)
    if portrait is not None:
        surface.blit(portrait, portrait_rect)
    else:
        pygame.draw.rect(surface, (58, 70, 68), portrait_rect, border_radius=10)
    pygame.draw.rect(surface, GOLD, portrait_rect, 2, border_radius=10)

    npc_name = format_poker_display_name(npc.get("name", "Opponent"))
    npc_label = label_font.render(npc_name, True, WHITE)
    surface.blit(npc_label, (230, 119))
    npc_stack = detail_font.render(f"Stack: ${game.npc_stack:,}", True, CREAM)
    surface.blit(npc_stack, (230, 151))

    if getattr(game, "last_npc_chat", "") and is_poker_chat_popups_enabled():
        lines = [""]
        for word in game.last_npc_chat.split():
            candidate = (lines[-1] + " " + word).strip()
            if detail_font.size(candidate)[0] > 210 and lines[-1]:
                lines.append(word)
            else:
                lines[-1] = candidate
        for row, line in enumerate(lines[:3]):
            surface.blit(_fit_line(detail_font, line, 210, GOLD), (132, 220 + row*20))

    player_label = label_font.render(str(player_name or "Player"), True, WHITE)
    surface.blit(player_label, (132, 522))
    player_stack = detail_font.render(f"Stack: ${game.player_stack:,}", True, CREAM)
    surface.blit(player_stack, (132, 554))

    opener_name = "You" if getattr(game, "opening_index", 0) == 0 else npc_name
    opener = detail_font.render(f"Opened this hand: {opener_name}", True, (204, 214, 208))
    surface.blit(opener, (132, 586))

    revealed_count = (
        game.get_showdown_revealed_count()
        if hasattr(game, "get_showdown_revealed_count")
        else (5 if game.hand_complete else 0)
    )
    showdown = bool(game.hand_complete)
    available = set(game.get_available_player_columns()) if game.phase == "placement" else set()
    for index in range(5):
        x = 360 + index * 125
        npc_rect = pygame.Rect(x, 95, 110, 190)
        player_rect = FIVE_O_PLAYER_COLUMN_RECTS[index]

        pygame.draw.rect(surface, (25, 58, 46), npc_rect, border_radius=8)
        pygame.draw.rect(surface, (25, 58, 46), player_rect, border_radius=8)

        column_revealed = index < revealed_count
        result = (
            game.column_results[index]
            if column_revealed and index < len(game.column_results)
            else None
        )
        result_color = {
            "player": GREEN,
            "npc": RED,
            "tie": GOLD,
        }.get(result, (135, 145, 140))

        pygame.draw.rect(surface, result_color if column_revealed else (135, 145, 140), npc_rect, 2, border_radius=8)
        border = GOLD if index in available else (135, 145, 140)
        width = 4 if index in available else 2
        pygame.draw.rect(surface, border, player_rect, width, border_radius=8)

        _draw_column(
            surface,
            game.npc_columns[index],
            npc_rect,
            detail_font,
            card_fronts,
            card_back_surface,
            hidden_to_viewer=True,
            showdown=column_revealed,
        )
        _draw_column(
            surface,
            game.player_columns[index],
            player_rect,
            detail_font,
            card_fronts,
            card_back_surface,
            hidden_to_viewer=True,
            showdown=column_revealed,
        )

        number = detail_font.render(str(index + 1), True, CREAM)
        surface.blit(number, number.get_rect(center=(player_rect.centerx, 652)))

        if column_revealed:
            result_text = {"player": "WIN", "npc": "LOSS", "tie": "TIE"}.get(result, "")
            tag = detail_font.render(result_text, True, result_color)
            surface.blit(tag, tag.get_rect(center=(player_rect.centerx, 432)))

    info = pygame.Rect(250, 294, 985, 144)
    overlay = pygame.Surface(info.size, pygame.SRCALPHA)
    overlay.fill((13, 29, 25, 210))
    surface.blit(overlay, info.topleft)
    pygame.draw.rect(surface, (123, 154, 138), info, 2, border_radius=12)

    pot = detail_font.render(
        f"Pot: ${game.pot:,}   Ante: ${game.ante:,}   Bet: ${game.bet_unit:,}",
        True,
        CREAM,
    )
    surface.blit(pot, pot.get_rect(center=(742, 313)))

    if game.phase == "placement" and game.player_drawn_card is not None:
        drawn_rect = pygame.Rect(267, 321, *DRAW_CARD_SIZE)
        _draw_card(
            surface,
            game.player_drawn_card,
            drawn_rect,
            detail_font,
            card_fronts,
            card_back_surface,
            True,
        )
        drawn_label = detail_font.render("DRAWN CARD", True, GOLD)
        surface.blit(drawn_label, drawn_label.get_rect(center=(drawn_rect.centerx, 429)))
        instruction = label_font.render(
            f"Layer {game.placement_round} of 5: choose a highlighted column",
            True,
            WHITE,
        )
        surface.blit(instruction, instruction.get_rect(center=(800, 350)))
        hidden_note = detail_font.render(
            "Every earlier card stays visible. Card #4 is the one face-down card.",
            True,
            (210, 218, 214),
        )
        surface.blit(hidden_note, hidden_note.get_rect(center=(800, 386)))

    elif game.phase == "betting":
        status = label_font.render("SINGLE BETTING ROUND", True, GOLD)
        surface.blit(status, status.get_rect(center=(742, 346)))
        note = _fit_line(detail_font, game.result_text, 850, WHITE)
        surface.blit(note, note.get_rect(center=(742, 386)))

    else:
        if game.hand_complete:
            header_text = (
                f"Columns: You {game.player_column_wins}  •  "
                f"{game.get_npc_name()} {game.npc_column_wins}"
            )
        else:
            header_text = game.result_text

        score = _fit_line(label_font, header_text, 900, GOLD)
        surface.blit(score, score.get_rect(center=(742, 318)))

        y = 336
        for index in range(min(revealed_count, 5)):
            result = game.column_results[index] if index < len(game.column_results) else None
            player_desc = game.get_column_description("player", index)
            npc_desc = game.get_column_description("npc", index)
            if result == "player":
                comparison = f"{index + 1}. You: {player_desc}  beats  {game.get_npc_name()}: {npc_desc}"
                color = (188, 236, 194)
            elif result == "npc":
                comparison = f"{index + 1}. {game.get_npc_name()}: {npc_desc}  beats  You: {player_desc}"
                color = (245, 184, 184)
            else:
                comparison = f"{index + 1}. Tie: {player_desc}"
                color = (239, 218, 155)
            line = _fit_line(detail_font, comparison, 900, color)
            surface.blit(line, (280, y))
            y += 18

        if game.hand_complete:
            final_line = _fit_line(detail_font, game.result_text, 900, WHITE)
            surface.blit(final_line, final_line.get_rect(center=(742, 425)))

    actions = set(game.get_player_actions())
    if game.phase == "betting" and not game.hand_complete:
        if ACTION_FOLD in actions:
            _draw_button(surface, FIVE_O_ACTION_RECTS[ACTION_FOLD], "FOLD", mouse_pos, label_font)
        if ACTION_CHECK in actions:
            _draw_button(surface, FIVE_O_ACTION_RECTS[ACTION_CHECK], "CHECK", mouse_pos, label_font)
        if ACTION_CALL in actions:
            _draw_button(surface, FIVE_O_ACTION_RECTS[ACTION_CALL], f"CALL ${game.current_bet:,}", mouse_pos, label_font)
        if ACTION_BET in actions:
            _draw_button(surface, FIVE_O_ACTION_RECTS[ACTION_BET], f"BET ${game.get_effective_bet_unit():,}", mouse_pos, label_font, accent=True)

    if game.hand_complete:
        _draw_button(surface, FIVE_O_NEXT_RECT, "NEXT HAND", mouse_pos, label_font, enabled=game.can_start_next_hand())
        _draw_button(surface, FIVE_O_RETURN_RECT, "CASH OUT", mouse_pos, label_font, accent=True)
    else:
        _draw_button(surface, FIVE_O_RETURN_RECT, "CASH OUT", mouse_pos, label_font, enabled=False)

    session = detail_font.render(
        f"Session: {game.get_session_net():+d}   Hands: {game.hands_played}   Five-O sweeps: {game.five_o_wins}",
        True,
        (215, 222, 218),
    )
    surface.blit(session, session.get_rect(midleft=(126, 714)))

