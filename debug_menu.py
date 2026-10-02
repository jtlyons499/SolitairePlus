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


def _column_rect(column_index, row_index):
    return pygame.Rect(
        _COLUMN_X[column_index],
        _BUTTON_START_Y
        + row_index * (_BUTTON_HEIGHT + _BUTTON_GAP),
        _COLUMN_WIDTH,
        _BUTTON_HEIGHT,
    )


DEBUG_GROUPS = (
    (
        "CAREER",
        (
            (ACTION_CAREER_HUB, "Career Hub"),
            (ACTION_CASUAL_CARDS, "Casual Cards"),
            (ACTION_POKER_NIGHT, "Poker Night"),
            (ACTION_CASINO_NIGHT, "Casino Night"),
            (ACTION_HEAD_TO_HEAD, "Head-to-Head"),
            (ACTION_ADVANCE_CAREER_DAY, "Skip Current Day"),
            (ACTION_NEW_CAREER_MONTH, "Start Next Month"),
        ),
    ),
    (
        "CHALLENGES / NICHE",
        (
            (ACTION_CHALLENGE_DRAW_3, "3 Draw"),
            (ACTION_CHALLENGE_NO_UNDO, "No Undo"),
            (ACTION_CHALLENGE_NO_HINTS, "No Hints"),
            (ACTION_CHALLENGE_ALL_OR_NOTHING, "All or Nothing"),
            (ACTION_FARO, "Faro"),
            (ACTION_FIVE_O_POKER, "Five-O Poker"),
            (ACTION_BLIND_MANS_BLUFF, "Blind Man's Bluff"),
        ),
    ),
    (
        "MINIGAMES",
        (
            (ACTION_SCORE_FOUR_SOLO, "Score-Four Solo"),
            (ACTION_SCORE_FOUR_COMPETITIVE, "Score-Four Competitive"),
            (ACTION_CRAZY_EIGHTS, "Crazy Eights"),
            (ACTION_BANGO, "Bango"),
            (ACTION_BLACKJACK, "Blackjack"),
            (ACTION_ROULETTE, "Roulette"),
            (ACTION_HORSE_RACES, "Horse Races"),
            (ACTION_TEXAS_HOLDEM, "Texas Hold'em"),
            (ACTION_FIVE_CARD_DRAW, "Five-Card Draw"),
            (ACTION_SEVEN_CARD_STUD, "Seven-Card Stud"),
        ),
    ),
    (
        "PROGRESSION",
        (
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
        ),
    ),
)

_ACTION_RECTS = {}
for column_index, (_title, entries) in enumerate(DEBUG_GROUPS):
    for row_index, (action, _label) in enumerate(entries):
        _ACTION_RECTS[action] = _column_rect(column_index, row_index)

_CLOSE_RECT = pygame.Rect(533, 704, 300, 48)
_ACTION_RECTS[ACTION_CLOSE] = _CLOSE_RECT




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

    text_surface = font.render(
        _debug_message,
        True,
        (255, 240, 185),
    )
    box = text_surface.get_rect(center=(683, 662)).inflate(42, 22)
    panel = pygame.Surface(box.size, pygame.SRCALPHA)
    pygame.draw.rect(
        panel,
        (20, 22, 26, min(225, alpha)),
        panel.get_rect(),
        border_radius=10,
    )
    pygame.draw.rect(
        panel,
        (255, 210, 95, alpha),
        panel.get_rect(),
        2,
        border_radius=10,
    )
    game_surface.blit(panel, box.topleft)
    text_surface.set_alpha(alpha)
    game_surface.blit(text_surface, text_surface.get_rect(center=box.center))


# ==================================================
# INPUT
# ==================================================


def get_debug_action(mouse_pos):
    if mouse_pos is None:
        return None

    for action, rect in _ACTION_RECTS.items():
        if rect.collidepoint(mouse_pos):
            return action

    return None


# ==================================================
# DRAW
# ==================================================


def draw_debug_menu(
        game_surface,
        mouse_pos,
        draw_submenu_background,
        draw_submenu_title,
        draw_menu_button,
        option_label_font,
        difficulty_detail_font
):
    draw_submenu_background(overlay_alpha=145)
    draw_submenu_title("DEBUG MENU")

    hint_surface = difficulty_detail_font.render(
        "F10 toggles this menu. Debug actions are intended for testing only.",
        True,
        (225, 225, 225),
    )
    game_surface.blit(
        hint_surface,
        hint_surface.get_rect(center=(683, 92)),
    )

    for column_index, (group_title, entries) in enumerate(DEBUG_GROUPS):
        header = option_label_font.render(
            group_title,
            True,
            (255, 225, 105),
        )
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
            rect = _column_rect(column_index, row_index)
            draw_menu_button(
                rect,
                label,
                mouse_pos,
                font=difficulty_detail_font,
            )

    draw_menu_button(
        _CLOSE_RECT,
        "Close Debug Menu",
        mouse_pos,
        font=difficulty_detail_font,
    )

    _draw_debug_message(
        game_surface,
        option_label_font,
    )
