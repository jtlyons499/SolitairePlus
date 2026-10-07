import pygame
from pathlib import Path
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

CARD_SIZE = (148, 207)
DRAW_CARD_SIZE = (148, 207)
STACK_OFFSET = 18

FIVE_O_RETURN_RECT = pygame.Rect(915, 20, 135, 44)
FIVE_O_PLAYER_COLUMN_RECTS = [
    pygame.Rect(360 + index * 190, 400, 156, 293)
    for index in range(5)
]
# Leave room for the hand-value captions beneath the last card.
CARD_BOTTOM = max(rect.y + 8 + 4*STACK_OFFSET + CARD_SIZE[1]
                  for rect in FIVE_O_PLAYER_COLUMN_RECTS)
VALUE_LABEL_Y = CARD_BOTTOM + 8
ACTION_Y = max(728, VALUE_LABEL_Y + 28)
RIGHT_EDGE = FIVE_O_PLAYER_COLUMN_RECTS[-1].right
FIVE_O_NEXT_RECT = pygame.Rect(RIGHT_EDGE-180, ACTION_Y, 180, 34)
FIVE_O_ACTION_RECTS = {
    ACTION_FOLD: pygame.Rect(715, ACTION_Y, 145, 34),
    ACTION_CHECK: pygame.Rect(875, ACTION_Y, 155, 34),
    ACTION_CALL: pygame.Rect(875, ACTION_Y, 155, 34),
    ACTION_BET: pygame.Rect(1045, ACTION_Y, RIGHT_EDGE-1045, 34),
}

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


def _draw_card(surface, card, rect, detail_font, card_fronts, card_back_surface=None, face_up=True, stacked=False):
    if face_up:
        image = _load_card(card, card_fronts, rect.size)
    else:
        image = card_back_surface
        if image is not None and image.get_size() != rect.size:
            image = pygame.transform.smoothscale(image, rect.size)

    if image is not None:
        surface.blit(image, rect)
        if not face_up or not stacked:
            return

    if image is None:
        pygame.draw.rect(surface, WHITE if face_up else (45, 70, 145), rect, border_radius=4)
        pygame.draw.rect(surface, DARK, rect, 2, border_radius=4)
    if face_up and card:
        font = pygame.font.Font(None, 22)
        color = (172, 32, 42) if card.get("suit") in ("Diamonds", "Hearts") else DARK
        label = font.render(str(card.get('rank', '?')), True, color)
        badge = pygame.Rect(rect.x + 2, rect.y + 2, rect.width - 4, STACK_OFFSET - 2)
        pygame.draw.rect(surface, WHITE, badge, border_radius=3)
        surface.blit(label, (badge.x + 4, badge.y))
        x, y = badge.x + label.get_width() + 17, badge.y + 8
        suit = card.get("suit")
        # Draw suit symbols directly: pygame's bundled font lacks these glyphs
        # on some machines. All four suits remain recognisable on stacked cards.
        if suit == "Diamonds":
            pygame.draw.polygon(surface, color, [(x,y-6),(x+5,y),(x,y+6),(x-5,y)])
        elif suit == "Hearts":
            pygame.draw.circle(surface, color, (x-3,y-2), 3)
            pygame.draw.circle(surface, color, (x+3,y-2), 3)
            pygame.draw.polygon(surface, color, [(x-6,y-1),(x+6,y-1),(x,y+6)])
        elif suit == "Spades":
            pygame.draw.polygon(surface, color, [(x,y-6),(x-6,y+2),(x+6,y+2)])
            pygame.draw.circle(surface, color, (x-3,y+1), 3)
            pygame.draw.circle(surface, color, (x+3,y+1), 3)
            pygame.draw.rect(surface, color, (x-1,y+1,3,6))
        else:
            for center in ((x,y-3),(x-3,y+1),(x+3,y+1)):
                pygame.draw.circle(surface, color, center, 3)
            pygame.draw.rect(surface, color, (x-1,y+1,3,6))



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
        card_rect = pygame.Rect(rect.centerx - CARD_SIZE[0] // 2, rect.y + 8 + index * STACK_OFFSET, *CARD_SIZE)
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
            stacked=index < len(cards) - 1,
        )


def _draw_button(surface, rect, text, mouse_pos, font, enabled=True, accent=False):
    from texas_holdem_ui import draw_holdem_glossy_button
    draw_holdem_glossy_button(surface, rect, text, mouse_pos, font, enabled=enabled)


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

    if OPTIONS_RECT.collidepoint(mouse_pos):
        game.options_open = not game.options_open
        return "ui_click"
    if game.options_open == "quit":
        if CLOSE_RECT.collidepoint(mouse_pos): game.options_open = False
        elif FAST_RECT.collidepoint(mouse_pos):
            game.options_open = False
            if not game.hand_complete:
                game.pending_npc_at = 0.0
                if game.showdown_pending_finish:
                    game.result_text = game.pending_showdown_result_text
                    game.showdown_revealed_columns = 5
                    game.showdown_pending_finish = False
                    game._finish_hand()
                else:
                    game.player_folded = True
                    game._award_fold_win(False)
            return ACTION_RETURN
        return "ui_click"
    if game.options_open:
        if FAST_RECT.collidepoint(mouse_pos): game.fast_reveal = not game.fast_reveal
        elif SOUND_RECT.collidepoint(mouse_pos): game.sounds_enabled = not game.sounds_enabled
        elif CLOSE_RECT.collidepoint(mouse_pos): game.options_open = False
        return "ui_click"
    if QUIT_RECT.collidepoint(mouse_pos):
        game.options_open = "quit"
        return "ui_click"
    for index, rect in enumerate(BET_PRESET_RECTS):
        if game.phase == "betting" and rect.collidepoint(mouse_pos):
            game.bet_fraction = (.25, .5, 1, 100)[index]
            return "ui_click"
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


OPTIONS_RECT = pygame.Rect(1205, 20, 135, 44)
QUIT_RECT = pygame.Rect(1060, 20, 135, 44)
FAST_RECT = pygame.Rect(453, 285, 460, 58)
SOUND_RECT = pygame.Rect(453, 365, 460, 58)
CLOSE_RECT = pygame.Rect(583, 475, 200, 48)
BET_PRESET_RECTS = [pygame.Rect(32+(i%2)*154, 488+(i//2)*46, 142, 36) for i in range(4)]
_logo = None
_logo_signature = None
_sound_cache = {}

def _play_column_sound(game, index):
    if not game.sounds_enabled: return
    result = game.column_results[index]
    if result == "tie": return
    path = "assets/sounds/five_o_column_" + ("win" if result == "player" else "loss") + ".wav"
    if path not in _sound_cache:
        try: _sound_cache[path] = pygame.mixer.Sound(path)
        except (pygame.error, FileNotFoundError): _sound_cache[path] = None
    if _sound_cache[path]: _sound_cache[path].play()

def draw_five_o_poker(surface, mouse_pos, game, player_name, draw_submenu_background,
                      title_font, label_font, detail_font, card_fronts=None, card_back_surface=None):
    from score_four_ui import panel, text
    global _logo, _logo_signature
    draw_submenu_background(overlay_alpha=115)
    logo_path = Path("assets/poker/logos/five_o_poker.png")
    try:
        stat = logo_path.stat()
        signature = (stat.st_mtime_ns, stat.st_size)
    except OSError:
        signature = None
    if _logo is None or signature != _logo_signature:
        _logo_signature = signature
        try:
            source = pygame.image.load(str(logo_path)).convert_alpha()
            scale = min(430 / source.get_width(), 64 / source.get_height())
            _logo = pygame.transform.smoothscale(source, (max(1, round(source.get_width()*scale)), max(1, round(source.get_height()*scale))))
        except (OSError, pygame.error):
            _logo = False
    if _logo: surface.blit(_logo, _logo.get_rect(center=(640, 38)))
    else: text(surface, "FIVE-O  •  FIVE FRONTS", (640, 36), 42, CREAM, True)
    panel(surface, (20, 75, 320, 585), (10, 23, 34, 225), (167, 191, 211))
    panel(surface, (20, 660, 320, 90), (10, 23, 34, 225), (167, 191, 211))
    font = pygame.font.Font(None, 24)
    def line(value, y, color=WHITE):
        surface.blit(_fit_line(font, value, 296, color), (32, y))
    def wrap(value, y, color=WHITE):
        rows = [""]
        for word in str(value).split():
            trial = (rows[-1] + " " + word).strip()
            if font.size(trial)[0] > 296 and rows[-1]: rows.append(word)
            else: rows[-1] = trial
        for row in rows:
            line(row, y, color); y += 23
        return y
    line(game.get_npc_name(), 87, GOLD)
    line(f"Opponent: ${game.npc_stack:,}", 115, CREAM)
    line(f"{player_name or 'Player'}: ${game.player_stack:,}", 145)
    line(f"Pot: ${game.pot:,}  •  Ante: ${game.ante:,}", 179, GOLD)
    revealed = game.get_showdown_revealed_count()
    key = (game.hand_number, revealed)
    previous = getattr(game, "ui_revealed", (game.hand_number, 0))
    if previous[0] != game.hand_number: previous = (game.hand_number, 0)
    for index in range(previous[1], revealed): _play_column_sound(game, index)
    game.ui_revealed = key
    available = set(game.get_available_player_columns())
    for index, player_rect in enumerate(FIVE_O_PLAYER_COLUMN_RECTS):
        npc_rect = pygame.Rect(player_rect.x, 78, player_rect.w, player_rect.h)
        result = game.column_results[index] if index < revealed else None
        color = {"player": (255, 223, 82), "npc": (255, 100, 100), "tie": CREAM}.get(result, (126, 161, 178))
        for rect in (npc_rect, player_rect): panel(surface, rect, (12, 28, 41, 170), color)
        if index in available: pygame.draw.rect(surface, GOLD, player_rect, 3, border_radius=18)
        _draw_column(surface, game.npc_columns[index], npc_rect, font, card_fronts, card_back_surface, hidden_to_viewer=True, showdown=index < revealed)
        # Players always know their own hidden fourth card.
        _draw_column(surface, game.player_columns[index], player_rect, font, card_fronts, card_back_surface, showdown=True)
        tag = {"player": "WIN", "npc": "LOSS", "tie": "TIE"}.get(result, f"COLUMN {index+1}")
        center = (player_rect.centerx, 385)
        for dx, dy in ((-2,0),(2,0),(0,-2),(0,2)):
            shadow = font.render(tag, True, (0, 0, 0)); surface.blit(shadow, shadow.get_rect(center=(center[0]+dx, center[1]+dy)))
        if result in ("player", "npc"):
            glow = font.render(tag, True, color).convert_alpha()
            glow.set_alpha(70)
            for dx, dy in ((-3,0),(3,0),(0,-3),(0,3),(-2,-2),(2,2)):
                surface.blit(glow, glow.get_rect(center=(center[0]+dx, center[1]+dy)))
        label = font.render(tag, True, color); surface.blit(label, label.get_rect(center=center))
        if game.player_columns[index]:
            description = game.get_column_description("player", index)
            if description == "Incomplete":
                cards = game.player_columns[index]
                ranks = [card.get("rank") for card in cards]
                counts = sorted([ranks.count(rank) for rank in set(ranks)], reverse=True)
                groups = sorted(set(ranks), key=lambda rank: ranks.count(rank), reverse=True)
                description = ("Four of " if counts[0] == 4 else "Three of " if counts[0] == 3 else "Pair of ") + str(groups[0]) + "s" if counts[0] >= 2 else "High card"
                if counts[:2] == [2,2]: description = "Two pair"
            description = description.split(",")[0]
            small = pygame.font.Font(None, 22)
            label = _fit_line(small, description, player_rect.width, WHITE)
            surface.blit(label, label.get_rect(midtop=(player_rect.centerx, VALUE_LABEL_Y)))
    if game.phase == "placement" and game.player_drawn_card:
        line("NEXT CARD", 225, GOLD)
        _draw_card(surface, game.player_drawn_card, pygame.Rect(104, 258, *DRAW_CARD_SIZE), font, card_fronts, card_back_surface)
        wrap(f"Layer {game.placement_round}/5 • Choose a column to strengthen.", 490)
        wrap("Your fourth cards stay hidden from the opponent.", 550, CREAM)
    elif game.phase == "betting":
        line("ONE BETTING ROUND", 225, GOLD)
        wrap(game.result_text, 260)
        wrap(game.last_player_action, 370, CREAM)
        wrap(game.last_npc_action, 420, CREAM)
        for index, rect in enumerate(BET_PRESET_RECTS): _draw_button(surface, rect, ("1/4 POT", "1/2 POT", "POT", "MAX")[index], mouse_pos, pygame.font.Font(None, 22))
    else:
        line(f"Columns: You {game.player_column_wins} / Rival {game.npc_column_wins}", 216, GOLD)
        for index in range(revealed):
            y = 253 + index*65
            result = game.column_results[index]
            color = {"player": GOLD, "npc": (255, 100, 100), "tie": CREAM}.get(result, WHITE)
            line(f"{index+1}. " + {"player": "Win", "npc": "Loss", "tie": "Tie"}.get(result, ""), y, color)
            line("You: " + game.get_column_description("player", index), y+20)
            line("Rival: " + game.get_column_description("npc", index), y+40)
        if game.hand_complete: wrap(game.result_text, 594, GOLD)
    actions = set(game.get_player_actions())
    for action in (ACTION_FOLD, ACTION_CHECK, ACTION_CALL, ACTION_BET):
        if action not in actions: continue
        label = action.upper()
        if action == ACTION_CALL: label += f" ${max(0, game.current_bet-game.player_betting_paid):,}"
        if action == ACTION_BET: label = ("RAISE TO" if game.current_bet else "BET") + f" ${game.get_effective_bet_unit():,}"
        _draw_button(surface, FIVE_O_ACTION_RECTS[action], label, mouse_pos, font)
    if game.hand_complete: _draw_button(surface, FIVE_O_NEXT_RECT, "NEXT HAND", mouse_pos, font, enabled=game.can_start_next_hand())
    _draw_button(surface, FIVE_O_RETURN_RECT, "CASH OUT", mouse_pos, font, enabled=game.hand_complete)
    _draw_button(surface, QUIT_RECT, "QUIT", mouse_pos, font)
    _draw_button(surface, OPTIONS_RECT, "OPTIONS", mouse_pos, font)
    line(f"Session: ${game.get_session_net():+,}", 675, CREAM)
    hand_net = game.player_stack - getattr(game, "hand_start_player_stack", game.player_stack)
    line(f"Hand: ${hand_net:+,}  •  Played: {game.hands_played}", 712)
    if game.options_open:
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA); shade.fill((0,0,0,170)); surface.blit(shade,(0,0))
        panel(surface, (413, 210, 540, 360), (10, 23, 34, 250), GOLD)
        if game.options_open == "quit":
            text(surface, "Leave the table?", (683, 246), 38, WHITE, True)
            text(surface, "An unfinished hand forfeits its pot.", (683, 393), 26, CREAM, True)
            _draw_button(surface, FAST_RECT, "QUIT AND CASH OUT", mouse_pos, font)
            _draw_button(surface, CLOSE_RECT, "CANCEL", mouse_pos, font)
        else:
            text(surface, "FIVE-O OPTIONS", (683, 246), 38, WHITE, True)
            _draw_button(surface, FAST_RECT, "Column reveal: " + ("Fast" if game.fast_reveal else "Readable"), mouse_pos, font)
            _draw_button(surface, SOUND_RECT, "Column sounds: " + ("On" if game.sounds_enabled else "Off"), mouse_pos, font)
            _draw_button(surface, CLOSE_RECT, "DONE", mouse_pos, font)
