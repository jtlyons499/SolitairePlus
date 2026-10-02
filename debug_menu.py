import pygame


# ==================================================
# DEBUG ACTIONS
# ==================================================

ACTION_CAREER_HUB = "career_hub"
ACTION_CASUAL_CARDS = "casual_cards"
ACTION_CASINO_NIGHT = "casino_night"

ACTION_SCORE_FOUR_SOLO = "score_four_solo"
ACTION_SCORE_FOUR_COMPETITIVE = "score_four_competitive"
ACTION_BLACKJACK = "blackjack"
ACTION_ROULETTE = "roulette"
ACTION_TEXAS_HOLDEM = "texas_holdem"

ACTION_ADD_CASH = "add_cash"
ACTION_ZERO_CASH = "zero_cash"
ACTION_ADD_XP = "add_xp"

ACTION_LEVEL_3 = "level_3"
ACTION_LEVEL_6 = "level_6"
ACTION_LEVEL_10 = "level_10"

ACTION_CLOSE = "close"


# ==================================================
# DEBUG MENU RECTS
# ==================================================

debug_career_hub_rect = pygame.Rect(
    170, 180, 220, 50
)

debug_casual_cards_rect = pygame.Rect(
    170, 245, 220, 50
)

debug_casino_night_rect = pygame.Rect(
    170, 310, 220, 50
)


debug_score_four_solo_rect = pygame.Rect(
    470, 180, 260, 50
)

debug_score_four_comp_rect = pygame.Rect(
    470, 245, 260, 50
)

debug_blackjack_rect = pygame.Rect(
    470, 310, 260, 50
)

debug_roulette_rect = pygame.Rect(
    470, 375, 260, 50
)

debug_texas_holdem_rect = pygame.Rect(
    470, 440, 260, 50
)

debug_add_cash_rect = pygame.Rect(
    810, 180, 220, 50
)

debug_zero_cash_rect = pygame.Rect(
    810, 245, 220, 50
)

debug_add_xp_rect = pygame.Rect(
    810, 310, 220, 50
)

debug_level_3_rect = pygame.Rect(
    810, 375, 220, 50
)

debug_level_6_rect = pygame.Rect(
    810, 440, 220, 50
)

debug_level_10_rect = pygame.Rect(
    810, 505, 220, 50
)


debug_close_rect = pygame.Rect(
    583,
    610,
    200,
    50
)


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

    draw_submenu_background(
        overlay_alpha=155
    )

    draw_submenu_title(
        "DEBUG MENU",
        y=60,
        width=360
    )

    # ==================================================
    # Section labels
    # ==================================================

    career_label = option_label_font.render(
        "CAREER",
        True,
        (
            255,
            255,
            255
        )
    )

    game_surface.blit(
        career_label,
        (
            170,
            130
        )
    )

    games_label = option_label_font.render(
        "GAMES",
        True,
        (
            255,
            255,
            255
        )
    )

    game_surface.blit(
        games_label,
        (
            470,
            130
        )
    )

    utilities_label = option_label_font.render(
        "UTILITIES",
        True,
        (
            255,
            255,
            255
        )
    )

    game_surface.blit(
        utilities_label,
        (
            810,
            130
        )
    )

    # ==================================================
    # Career
    # ==================================================

    draw_menu_button(
        debug_career_hub_rect,
        "Career Hub",
        mouse_pos,
        font=difficulty_detail_font
    )

    draw_menu_button(
        debug_casual_cards_rect,
        "Casual Cards",
        mouse_pos,
        font=difficulty_detail_font
    )

    draw_menu_button(
        debug_casino_night_rect,
        "Casino Night",
        mouse_pos,
        font=difficulty_detail_font
    )

    # ==================================================
    # Games
    # ==================================================

    draw_menu_button(
        debug_score_four_solo_rect,
        "Score-Four Solo",
        mouse_pos,
        font=difficulty_detail_font
    )

    draw_menu_button(
        debug_score_four_comp_rect,
        "Score-Four Competitive",
        mouse_pos,
        font=difficulty_detail_font
    )

    draw_menu_button(
        debug_blackjack_rect,
        "Blackjack",
        mouse_pos,
        font=difficulty_detail_font
    )

    draw_menu_button(
        debug_roulette_rect,
        "Roulette",
        mouse_pos,
        font=difficulty_detail_font
    )

    draw_menu_button(
        debug_texas_holdem_rect,
        "Texas Hold'em",
        mouse_pos,
        font=difficulty_detail_font
    )

    # ==================================================
    # Utilities
    # ==================================================

    draw_menu_button(
        debug_add_cash_rect,
        "Add $5,000",
        mouse_pos,
        font=difficulty_detail_font
    )

    draw_menu_button(
        debug_zero_cash_rect,
        "Set Cash $0",
        mouse_pos,
        font=difficulty_detail_font
    )

    draw_menu_button(
        debug_add_xp_rect,
        "Add 1,000 XP",
        mouse_pos,
        font=difficulty_detail_font
    )

    draw_menu_button(
        debug_level_3_rect,
        "Set Level 3",
        mouse_pos,
        font=difficulty_detail_font
    )

    draw_menu_button(
        debug_level_6_rect,
        "Set Level 6",
        mouse_pos,
        font=difficulty_detail_font
    )

    draw_menu_button(
        debug_level_10_rect,
        "Set Level 10",
        mouse_pos,
        font=difficulty_detail_font
    )

    # ==================================================
    # Close
    # ==================================================

    draw_menu_button(
        debug_close_rect,
        "Close",
        mouse_pos,
        font=difficulty_detail_font
    )


# ==================================================
# CLICK DETECTION
# ==================================================

def get_debug_action(
        mouse_pos
):

    if mouse_pos is None:
        return None

    if debug_career_hub_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_CAREER_HUB

    if debug_casual_cards_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_CASUAL_CARDS

    if debug_casino_night_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_CASINO_NIGHT

    if debug_score_four_solo_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_SCORE_FOUR_SOLO

    if debug_score_four_comp_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_SCORE_FOUR_COMPETITIVE

    if debug_blackjack_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_BLACKJACK

    if debug_roulette_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_ROULETTE

    if debug_texas_holdem_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_TEXAS_HOLDEM

    if debug_add_cash_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_ADD_CASH

    if debug_zero_cash_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_ZERO_CASH

    if debug_add_xp_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_ADD_XP

    if debug_level_3_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_LEVEL_3

    if debug_level_6_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_LEVEL_6

    if debug_level_10_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_LEVEL_10

    if debug_close_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_CLOSE

    return None