import pygame


# ==================================================
# DEBUG ACTIONS
# ==================================================

ACTION_CAREER_HUB = "career_hub"
ACTION_CASUAL_CARDS = "casual_cards"
ACTION_POKER_NIGHT = "poker_night"
ACTION_CASINO_NIGHT = "casino_night"
ACTION_HEAD_TO_HEAD = "head_to_head"
ACTION_ADVANCE_CAREER_DAY = "advance_career_day"
ACTION_NEW_CAREER_MONTH = "new_career_month"
ACTION_ADD_PROSPECT = "add_prospect"
ACTION_ADD_PRODIGY = "add_prodigy"
ACTION_CAREER_YEAR = "career_year"

ACTION_CHALLENGE_DRAW_3 = "challenge_draw_3"
ACTION_CHALLENGE_NO_UNDO = "challenge_no_undo"
ACTION_CHALLENGE_NO_HINTS = "challenge_no_hints"
ACTION_CHALLENGE_ALL_OR_NOTHING = "challenge_all_or_nothing"

ACTION_SCORE_FOUR_SOLO = "score_four_solo"
ACTION_SCORE_FOUR_COMPETITIVE = "score_four_competitive"
ACTION_CRAZY_EIGHTS = "crazy_eights"
ACTION_BANGO = "bango"
ACTION_FARO = "faro"
ACTION_FIVE_O_POKER = "five_o_poker"
ACTION_BLIND_MANS_BLUFF = "blind_mans_bluff"
ACTION_BLACKJACK = "blackjack"
ACTION_ROULETTE = "roulette"
ACTION_HORSE_RACES = "horse_races"
ACTION_TEXAS_HOLDEM = "texas_holdem"
ACTION_FIVE_CARD_DRAW = "five_card_draw"
ACTION_SEVEN_CARD_STUD = "seven_card_stud"

# Arcade debug entry points. Arcade Night opens the whole event selector while
# the individual entries jump directly to their difficulty/rival selectors.
ACTION_ARCADE_NIGHT = "arcade_night"
ACTION_KING_PONG = "king_pong"
ACTION_BATTLE_BOSSES = "battle_bosses"
ACTION_ACE_INVADERS = "ace_invaders"
ACTION_SUIT_SNAKE = "suit_snake"
ACTION_DEAD_MANS_HAND = "dead_mans_hand"

ACTION_MINIGAME_CATEGORY_ARCADE = "minigame_category_arcade"
ACTION_MINIGAME_CATEGORY_CASUAL = "minigame_category_casual"
ACTION_MINIGAME_CATEGORY_CASINO = "minigame_category_casino"
ACTION_MINIGAME_CATEGORY_POKER = "minigame_category_poker"
ACTION_MINIGAME_CATEGORY_STANDALONE = "minigame_category_standalone"

ACTION_ADD_CASH = "add_cash"
ACTION_ZERO_CASH = "zero_cash"
ACTION_ADD_RATING = "add_rating"
ACTION_SUB_RATING = "sub_rating"
ACTION_ADD_XP = "add_xp"
ACTION_LEVEL_3 = "level_3"
ACTION_LEVEL_6 = "level_6"
ACTION_LEVEL_10 = "level_10"
ACTION_LEVEL_MAX = "level_max"
ACTION_ACHIEVEMENT_TEST = "achievement_test"

ACTION_CLOSE = "close"


# ==================================================
# LAYOUT
# ==================================================

_COLUMN_X = (48, 375, 702, 1029)
_COLUMN_WIDTH = 285
_HEADER_Y = 118
_BUTTON_START_Y = 156
_BUTTON_HEIGHT = 44
_BUTTON_GAP = 9
_CHILD_INDENT = 18
_CHILD_HEIGHT = 38
_CHILD_GAP = 6


def _column_rect(column_index, row_index):
    return pygame.Rect(
        _COLUMN_X[column_index],
        _BUTTON_START_Y + row_index * (_BUTTON_HEIGHT + _BUTTON_GAP),
        _COLUMN_WIDTH,
        _BUTTON_HEIGHT,
    )


CAREER_ENTRIES = (
    (ACTION_CAREER_HUB, "Career Hub"),
    (ACTION_CASUAL_CARDS, "Casual Cards"),
    (ACTION_POKER_NIGHT, "Poker Night"),
    (ACTION_CASINO_NIGHT, "Casino Night"),
    (ACTION_HEAD_TO_HEAD, "Head-to-Head"),
    (ACTION_ADVANCE_CAREER_DAY, "Skip Current Day"),
    (ACTION_NEW_CAREER_MONTH, "Start Next Month"),
    (ACTION_ADD_PROSPECT, "Add Prospect"),
    (ACTION_ADD_PRODIGY, "Add Prodigy"),
    (ACTION_CAREER_YEAR, "Advance 1 Career Year"),
)

CHALLENGE_ENTRIES = (
    (ACTION_CHALLENGE_DRAW_3, "3 Draw"),
    (ACTION_CHALLENGE_NO_UNDO, "No Undo"),
    (ACTION_CHALLENGE_NO_HINTS, "No Hints"),
    (ACTION_CHALLENGE_ALL_OR_NOTHING, "All or Nothing"),
)

PROGRESSION_ENTRIES = (
    (ACTION_ADD_CASH, "+$5,000 Cash"),
    (ACTION_ZERO_CASH, "Set Cash to $0"),
    (ACTION_ADD_RATING, "+100 Rating"),
    (ACTION_SUB_RATING, "-100 Rating"),
    (ACTION_ADD_XP, "+1,000 XP"),
    (ACTION_LEVEL_3, "Set Level 3"),
    (ACTION_LEVEL_6, "Set Level 6"),
    (ACTION_LEVEL_10, "Set Level 10"),
    (ACTION_LEVEL_MAX, "Max Level / Unlock All"),
    (ACTION_ACHIEVEMENT_TEST, "Unlock Next Achievement"),
)

# This is intentionally an accordion instead of a growing flat list. Only one
# section expands at a time, mirroring the Help navigation behavior.
MINIGAME_CATEGORIES = (
    (
        "arcade",
        ACTION_MINIGAME_CATEGORY_ARCADE,
        "Arcade Games",
        (
            (ACTION_ARCADE_NIGHT, "Arcade Night"),
            (ACTION_KING_PONG, "King Pong"),
            (ACTION_BATTLE_BOSSES, "Battle Bosses"),
            (ACTION_ACE_INVADERS, "Ace Invaders"),
            (ACTION_SUIT_SNAKE, "Suit Snake"),
        ),
    ),
    (
        "casual",
        ACTION_MINIGAME_CATEGORY_CASUAL,
        "Casual / Puzzle",
        (
            (ACTION_SCORE_FOUR_SOLO, "Score-Four Solo"),
            (ACTION_SCORE_FOUR_COMPETITIVE, "Score-Four Competitive"),
            (ACTION_CRAZY_EIGHTS, "Crazy Eights"),
            (ACTION_BANGO, "Bango"),
        ),
    ),
    (
        "casino",
        ACTION_MINIGAME_CATEGORY_CASINO,
        "Casino",
        (
            (ACTION_BLACKJACK, "Blackjack"),
            (ACTION_ROULETTE, "Roulette"),
            (ACTION_HORSE_RACES, "Horse Races"),
            (ACTION_FARO, "Faro"),
        ),
    ),
    (
        "poker",
        ACTION_MINIGAME_CATEGORY_POKER,
        "Poker",
        (
            (ACTION_TEXAS_HOLDEM, "Texas Hold'em"),
            (ACTION_FIVE_CARD_DRAW, "Five-Card Draw"),
            (ACTION_SEVEN_CARD_STUD, "Seven-Card Stud"),
            (ACTION_FIVE_O_POKER, "Five-O Poker"),
            (ACTION_BLIND_MANS_BLUFF, "Blind Man's Bluff"),
        ),
    ),
    (
        "standalone",
        ACTION_MINIGAME_CATEGORY_STANDALONE,
        "Standalone / Prototype",
        (
            (ACTION_DEAD_MANS_HAND, "Dead Man's Hand"),
        ),
    ),
)

_CATEGORY_ACTION_TO_ID = {
    action: category_id
    for category_id, action, _label, _entries in MINIGAME_CATEGORIES
}

_expanded_minigame_category = None
_ACTION_RECTS = {}
_CATEGORY_RECTS = {}
_CHILD_ACTIONS = set()

_CLOSE_RECT = pygame.Rect(533, 704, 300, 48)


def _rebuild_action_rects():
    """Build hit boxes for the current accordion state."""
    _ACTION_RECTS.clear()
    _CATEGORY_RECTS.clear()
    _CHILD_ACTIONS.clear()

    for row_index, (action, _label) in enumerate(CAREER_ENTRIES):
        _ACTION_RECTS[action] = _column_rect(0, row_index)

    for row_index, (action, _label) in enumerate(CHALLENGE_ENTRIES):
        _ACTION_RECTS[action] = _column_rect(1, row_index)

    y = _BUTTON_START_Y
    for category_id, category_action, _label, entries in MINIGAME_CATEGORIES:
        category_rect = pygame.Rect(
            _COLUMN_X[2],
            y,
            _COLUMN_WIDTH,
            _BUTTON_HEIGHT,
        )
        _CATEGORY_RECTS[category_action] = category_rect
        _ACTION_RECTS[category_action] = category_rect
        y += _BUTTON_HEIGHT + _BUTTON_GAP

        if _expanded_minigame_category == category_id:
            for action, _entry_label in entries:
                rect = pygame.Rect(
                    _COLUMN_X[2] + _CHILD_INDENT,
                    y,
                    _COLUMN_WIDTH - _CHILD_INDENT,
                    _CHILD_HEIGHT,
                )
                _ACTION_RECTS[action] = rect
                _CHILD_ACTIONS.add(action)
                y += _CHILD_HEIGHT + _CHILD_GAP
            y += 3

    for row_index, (action, _label) in enumerate(PROGRESSION_ENTRIES):
        _ACTION_RECTS[action] = _column_rect(3, row_index)

    _ACTION_RECTS[ACTION_CLOSE] = _CLOSE_RECT


_rebuild_action_rects()


# ==================================================
# ACCORDION HELPERS
# ==================================================


def is_minigame_category_action(action):
    return action in _CATEGORY_ACTION_TO_ID


def toggle_minigame_category(action):
    """Expand one Minigames section, collapsing the previously open one."""
    global _expanded_minigame_category

    category_id = _CATEGORY_ACTION_TO_ID.get(action)
    if category_id is None:
        return False

    if _expanded_minigame_category == category_id:
        _expanded_minigame_category = None
    else:
        _expanded_minigame_category = category_id

    _rebuild_action_rects()
    return True


def get_expanded_minigame_category():
    return _expanded_minigame_category


# ==================================================
# TRANSIENT FEEDBACK
# ==================================================

_debug_message = ""
_debug_message_started = 0
_debug_message_duration = 1800


def show_debug_message(message, duration=1800):
    global _debug_message
    global _debug_message_started
    global _debug_message_duration

    _debug_message = str(message or "")
    _debug_message_started = pygame.time.get_ticks()
    _debug_message_duration = max(250, int(duration))


def _draw_debug_message(game_surface, font):
    if not _debug_message:
        return

    elapsed = pygame.time.get_ticks() - _debug_message_started
    if elapsed >= _debug_message_duration:
        return

    fade_start = int(_debug_message_duration * 0.58)
    if elapsed <= fade_start:
        alpha = 245
    else:
        remaining = max(0, _debug_message_duration - elapsed)
        fade_span = max(1, _debug_message_duration - fade_start)
        alpha = int(245 * (remaining / fade_span))

    text_surface = font.render(_debug_message, True, (255, 240, 185))
    box = text_surface.get_rect(center=(683, 662)).inflate(42, 22)
    panel = pygame.Surface(box.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (20, 22, 26, min(225, alpha)), panel.get_rect(), border_radius=10)
    pygame.draw.rect(panel, (255, 210, 95, alpha), panel.get_rect(), 2, border_radius=10)
    game_surface.blit(panel, box.topleft)
    text_surface.set_alpha(alpha)
    game_surface.blit(text_surface, text_surface.get_rect(center=box.center))


# ==================================================
# INPUT
# ==================================================


def get_debug_action(mouse_pos):
    if mouse_pos is None:
        return None

    _rebuild_action_rects()
    for action, rect in _ACTION_RECTS.items():
        if rect.collidepoint(mouse_pos):
            return action
    return None


# ==================================================
# DRAW
# ==================================================


def _draw_fixed_column(
        game_surface,
        column_index,
        group_title,
        entries,
        mouse_pos,
        draw_menu_button,
        option_label_font,
        difficulty_detail_font,
):
    header = option_label_font.render(group_title, True, (255, 225, 105))
    game_surface.blit(
        header,
        header.get_rect(
            center=(
                _COLUMN_X[column_index] + _COLUMN_WIDTH // 2,
                _HEADER_Y,
            )
        ),
    )

    for row_index, (action, label) in enumerate(entries):
        draw_menu_button(
            _column_rect(column_index, row_index),
            label,
            mouse_pos,
            font=difficulty_detail_font,
        )


def _draw_minigame_accordion(
        game_surface,
        mouse_pos,
        draw_menu_button,
        option_label_font,
        difficulty_detail_font,
):
    header = option_label_font.render("MINIGAMES", True, (255, 225, 105))
    game_surface.blit(
        header,
        header.get_rect(center=(_COLUMN_X[2] + _COLUMN_WIDTH // 2, _HEADER_Y)),
    )

    for category_id, category_action, label, entries in MINIGAME_CATEGORIES:
        category_rect = _CATEGORY_RECTS.get(category_action)
        if category_rect is None:
            continue

        expanded = _expanded_minigame_category == category_id
        marker = "-" if expanded else "+"
        draw_menu_button(
            category_rect,
            f"{marker}  {label}",
            mouse_pos,
            selected=expanded,
            font=difficulty_detail_font,
        )

        if expanded:
            for action, child_label in entries:
                child_rect = _ACTION_RECTS.get(action)
                if child_rect is None:
                    continue
                draw_menu_button(
                    child_rect,
                    child_label,
                    mouse_pos,
                    font=difficulty_detail_font,
                )


def draw_debug_menu(
        game_surface,
        mouse_pos,
        draw_submenu_background,
        draw_submenu_title,
        draw_menu_button,
        option_label_font,
        difficulty_detail_font
):
    _rebuild_action_rects()

    draw_submenu_background(overlay_alpha=145)
    draw_submenu_title("DEBUG MENU")

    hint_surface = difficulty_detail_font.render(
        "F10 toggles this menu. Expand a Minigames category to jump directly into a test.",
        True,
        (225, 225, 225),
    )
    game_surface.blit(hint_surface, hint_surface.get_rect(center=(683, 92)))

    _draw_fixed_column(
        game_surface,
        0,
        "CAREER",
        CAREER_ENTRIES,
        mouse_pos,
        draw_menu_button,
        option_label_font,
        difficulty_detail_font,
    )
    _draw_fixed_column(
        game_surface,
        1,
        "SOLITAIRE CHALLENGES",
        CHALLENGE_ENTRIES,
        mouse_pos,
        draw_menu_button,
        option_label_font,
        difficulty_detail_font,
    )
    _draw_minigame_accordion(
        game_surface,
        mouse_pos,
        draw_menu_button,
        option_label_font,
        difficulty_detail_font,
    )
    _draw_fixed_column(
        game_surface,
        3,
        "PROGRESSION",
        PROGRESSION_ENTRIES,
        mouse_pos,
        draw_menu_button,
        option_label_font,
        difficulty_detail_font,
    )

    draw_menu_button(
        _CLOSE_RECT,
        "Close Debug Menu",
        mouse_pos,
        font=difficulty_detail_font,
    )

    _draw_debug_message(game_surface, option_label_font)
