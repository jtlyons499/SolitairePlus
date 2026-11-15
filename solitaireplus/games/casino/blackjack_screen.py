"""Blackjack table and bet screens (moved out of legacy.py)."""
from solitaireplus.games.solitaire.rules import BASE_WIDTH
from solitaireplus.games.casino.blackjack import BlackjackGame
from solitaireplus.career import career_rewards
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.career.session_summary import track_night_cash
from solitaireplus.app.lazy import lazy
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
leveling = lazy("solitaireplus.profile.leveling")
fonts = lazy("solitaireplus.app.fonts")
assets = lazy("solitaireplus.app.assets")
ui_text = lazy("solitaireplus.ui.text")


# MINIGAME RUNTIME OBJECTS
blackjack_game = BlackjackGame()

# ==================================================
# DIFFICULTY SELECT -- AREA FOR UI RECTANGLE DEFINITIONS
# ==================================================

# ==================================================
# BLACKJACK UI // MINIGAME RECTS
# ==================================================

# During a hand these five buttons directly choose the NEXT hand's bet.
blackjack_bet_dropdown_rects = [
    pygame.Rect(1052, 365, 116, 44),
    pygame.Rect(1180, 365, 116, 44),
    pygame.Rect(1052, 419, 116, 44),
    pygame.Rect(1180, 419, 116, 44),
    pygame.Rect(1052, 473, 244, 44),
]

# Kept for compatibility with older state, but no longer drawn as a two-step
# Change Bet control.
blackjack_change_bet_rect = pygame.Rect(0, 0, 0, 0)

blackjack_hit_rect = pygame.Rect(430, 660, 150, 50)
blackjack_stand_rect = pygame.Rect(595, 660, 150, 50)
blackjack_double_rect = pygame.Rect(760, 660, 165, 50)
blackjack_split_rect = pygame.Rect(940, 660, 150, 50)
blackjack_return_rect = pygame.Rect(1105, 660, 185, 50)
blackjack_deal_again_rect = pygame.Rect(570, 660, 225, 50)

# ==================================================
# BLACKJACK BET SELECT
# ==================================================

blackjack_bet_1_rect = pygame.Rect(370, 390, 145, 58)
blackjack_bet_2_rect = pygame.Rect(525, 390, 145, 58)
blackjack_bet_5_rect = pygame.Rect(680, 390, 145, 58)
blackjack_bet_10_rect = pygame.Rect(835, 390, 145, 58)
blackjack_bet_all_rect = pygame.Rect(525, 475, 300, 58)
blackjack_bet_return_rect = pygame.Rect(BASE_WIDTH // 2 - 105, 640, 210, 48)

def _render_blackjack_fit(text, max_width, size=21, bold=False, color=(255, 255, 255), minimum_size=13):
    current_size = int(size)
    while current_size >= minimum_size:
        # Shared font cache: building a SysFont for every size tried, every frame, was B34.
        font = ui_text.get_font("cambria", current_size, bold=bold, sysfont=True)
        surface = font.render(str(text), True, color)
        if surface.get_width() <= max_width or current_size == minimum_size:
            return surface
        current_size -= 1
    return fonts.blackjack_small_font.render(str(text), True, color)


def _draw_blackjack_panel(rect, fill=(10, 28, 21, 205), border=(220, 190, 100), radius=12):
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, fill, panel.get_rect(), border_radius=radius)
    window.game_surface.blit(panel, rect.topleft)
    pygame.draw.rect(
        window.game_surface,
        border,
        rect,
        2,
        border_radius=radius
    )


def _draw_blackjack_dealer_identity(rect):
    _draw_blackjack_panel(
        rect,
        fill=(8, 24, 18, 218),
        border=(210, 220, 205),
        radius=12
    )

    heading = fonts.blackjack_small_font.render(
        "TONIGHT'S DEALER",
        True,
        (222, 190, 98)
    )
    window.game_surface.blit(
        heading,
        (rect.x + 14, rect.y + 12)
    )

    portrait_rect = pygame.Rect(
        rect.x + 14,
        rect.y + 44,
        88,
        88
    )

    if state.blackjack_dealer_npc is not None:
        legacy.draw_npc_portrait(
            state.blackjack_dealer_npc,
            portrait_rect,
            "blackjack"
        )
        dealer_name = state.blackjack_dealer_npc.get("name", "Dealer")
        hometown = state.blackjack_dealer_npc.get("hometown", "Unknown")
        favorite_suit = state.blackjack_dealer_npc.get("favorite_suit", "Unknown")
    else:
        pygame.draw.rect(window.game_surface, (42, 58, 49), portrait_rect)
        pygame.draw.rect(window.game_surface, (215, 215, 215), portrait_rect, 2)
        dealer_name = "Dealer"
        hometown = "Unknown"
        favorite_suit = "Unknown"

    portrait = window.game_surface.subsurface(portrait_rect).copy()
    mask = pygame.Surface(portrait_rect.size, pygame.SRCALPHA)
    pygame.draw.ellipse(mask, (255, 255, 255, 255), mask.get_rect())
    portrait = portrait.convert_alpha()
    portrait.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    pygame.draw.rect(window.game_surface, (13, 25, 32), portrait_rect)
    window.game_surface.blit(portrait, portrait_rect)
    pygame.draw.ellipse(window.game_surface, (207, 225, 233), portrait_rect, 2)

    name_surface = _render_blackjack_fit(
        dealer_name,
        rect.width - 126,
        size=27,
        bold=True,
        color=(255, 255, 255),
        minimum_size=17
    )
    window.game_surface.blit(
        name_surface,
        (rect.x + 116, rect.y + 48)
    )

    hometown_surface = _render_blackjack_fit(
        hometown,
        rect.width - 130,
        size=17,
        color=(205, 214, 208),
        minimum_size=12
    )
    window.game_surface.blit(
        hometown_surface,
        (rect.x + 116, rect.y + 84)
    )

    suit_surface = _render_blackjack_fit(
        f"Favorite suit: {favorite_suit}",
        rect.width - 130,
        size=17,
        color=(232, 210, 145),
        minimum_size=12
    )
    window.game_surface.blit(
        suit_surface,
        (rect.x + 116, rect.y + 112)
    )


def _draw_blackjack_background():
    from solitaireplus.games.casino.blackjack_presentation import draw_background
    draw_background(window.game_surface, assets.menu_background_surfaces.get(state.selected_menu_background), assets.felt_surfaces.get(state.selected_felt))


def _draw_blackjack_button(rect, label, mouse, font=None, selected=False):
    from solitaireplus.games.casino.blackjack_presentation import draw_button
    draw_button(window.game_surface, rect, label, mouse, font or fonts.blackjack_body_font, selected=selected)


def draw_blackjack_bet():
    _draw_blackjack_background()

    dealer_identity_rect = pygame.Rect(34, 122, 302, 164)
    _draw_blackjack_dealer_identity(dealer_identity_rect)

    bet_panel = pygame.Rect(360, 138, 650, 450)
    _draw_blackjack_panel(
        bet_panel,
        fill=(7, 31, 22, 210),
        border=(230, 205, 120),
        radius=14
    )

    cash_surface = fonts.blackjack_heading_font.render(
        f"Bankroll  ${state.career_cash:,}",
        True,
        (255, 228, 135)
    )
    window.game_surface.blit(
        cash_surface,
        cash_surface.get_rect(center=(bet_panel.centerx, 190))
    )

    prompt = fonts.blackjack_heading_font.render(
        "Choose your opening wager",
        True,
        (245, 245, 240)
    )
    window.game_surface.blit(
        prompt,
        prompt.get_rect(center=(bet_panel.centerx, 245))
    )

    detail = fonts.blackjack_body_font.render(
        "The percentage is calculated from your current bankroll.",
        True,
        (194, 207, 199)
    )
    window.game_surface.blit(
        detail,
        detail.get_rect(center=(bet_panel.centerx, 280))
    )

    if state.career_cash > 0:
        bet_options = [
            (blackjack_bet_1_rect, "1%", 0.01),
            (blackjack_bet_2_rect, "2%", 0.02),
            (blackjack_bet_5_rect, "5%", 0.05),
            (blackjack_bet_10_rect, "10%", 0.10),
            (blackjack_bet_all_rect, "ALL IN", 1.0),
        ]

        for rect, label_text, percentage in bet_options:
            amount = get_blackjack_bet(percentage)
            label = f"{label_text}   ${amount:,}"
            _draw_blackjack_button(
                rect,
                label,
                state.game_mouse_pos,
                selected=(state.blackjack_selected_bet_percentage == percentage),
                font=fonts.blackjack_small_font
            )
    else:
        broke_surface = fonts.blackjack_heading_font.render(
            "OUT OF CASH",
            True,
            (255, 220, 120)
        )
        window.game_surface.blit(
            broke_surface,
            broke_surface.get_rect(center=(bet_panel.centerx, 365))
        )

        broke_detail = fonts.blackjack_body_font.render(
            "Return to the previous screen to finish the session.",
            True,
            (210, 215, 210)
        )
        window.game_surface.blit(
            broke_detail,
            broke_detail.get_rect(center=(bet_panel.centerx, 410))
        )

    _draw_blackjack_button(
        blackjack_bet_return_rect,
        "Return",
        state.game_mouse_pos,
        font=fonts.blackjack_body_font
    )


def draw_blackjack():
    _draw_blackjack_background()

    dealer_identity_rect = pygame.Rect(28, 112, 305, 170)
    _draw_blackjack_dealer_identity(dealer_identity_rect)

    right_panel = pygame.Rect(1033, 106, 304, 530)
    _draw_blackjack_panel(
        right_panel,
        fill=(7, 26, 19, 220),
        border=(210, 220, 205),
        radius=12
    )

    # ==================================================
    # Table labels / cards
    # ==================================================

    dealer_heading = fonts.blackjack_heading_font.render(
        "DEALER",
        True,
        (245, 235, 205)
    )
    window.game_surface.blit(
        dealer_heading,
        dealer_heading.get_rect(center=(686, 116))
    )

    dealer_count = max(1, len(blackjack_game.dealer_hand))
    dealer_spacing = min(92, 430 // max(1, dealer_count - 1))
    dealer_total_width = 100 + max(0, dealer_count - 1) * dealer_spacing
    dealer_x = 686 - dealer_total_width // 2
    dealer_y = 145

    for index, card in enumerate(blackjack_game.dealer_hand):
        target_x = dealer_x + index * dealer_spacing
        position = get_blackjack_animated_position(
            "dealer",
            index,
            target_x,
            dealer_y
        )
        if position is None:
            continue

        x, y = position

        if index == 1:
            flip_progress = blackjack_game.get_dealer_flip_progress()

            if flip_progress is None or flip_progress <= 0.0:
                window.game_surface.blit(
                    legacy.game.get_card_back_surface(),
                    (x, y)
                )
                continue

            if flip_progress < 1.0:
                if flip_progress < 0.5:
                    image = legacy.game.get_card_back_surface()
                    scale_progress = 1.0 - flip_progress * 2.0
                else:
                    card_key = get_card_key(card)
                    image = legacy.game.card_fronts[card_key]
                    scale_progress = (flip_progress - 0.5) * 2.0

                original_width = image.get_width()
                original_height = image.get_height()
                scaled_width = max(1, int(original_width * scale_progress))
                scaled_image = pygame.transform.smoothscale(
                    image,
                    (scaled_width, original_height)
                )
                scaled_rect = scaled_image.get_rect(
                    center=(
                        x + original_width // 2,
                        y + original_height // 2
                    )
                )
                window.game_surface.blit(scaled_image, scaled_rect)
                continue

        card_key = get_card_key(card)
        window.game_surface.blit(
            legacy.game.card_fronts[card_key],
            (x, y)
        )

    dealer_value_text = (
        f"Dealer total: {blackjack_game.dealer_value()}"
        if blackjack_game.dealer_hole_is_revealed()
        else "Dealer total: ?"
    )
    dealer_value_surface = fonts.blackjack_body_font.render(
        dealer_value_text,
        True,
        (245, 245, 240)
    )
    dealer_value_rect = dealer_value_surface.get_rect(center=(686, 318))
    value_bg = dealer_value_rect.inflate(28, 14)
    _draw_blackjack_panel(
        value_bg,
        fill=(8, 24, 18, 205),
        border=(173, 190, 179),
        radius=8
    )
    window.game_surface.blit(dealer_value_surface, dealer_value_rect)

    if blackjack_game.is_split_round():
        player_heading = fonts.blackjack_heading_font.render(
            "YOUR SPLIT HANDS",
            True,
            (245, 235, 205)
        )
        window.game_surface.blit(
            player_heading,
            player_heading.get_rect(center=(686, 382))
        )

        split_centers = (535, 835)
        hands = blackjack_game.get_player_hands()

        for hand_index, hand in enumerate(hands):
            center_x = split_centers[hand_index]
            active = (
                not blackjack_game.round_complete
                and not blackjack_game.player_stood
                and blackjack_game.active_hand_index == hand_index
                and not blackjack_game.player_hand_done[hand_index]
            )

            hand_label = fonts.blackjack_small_font.render(
                f"HAND {hand_index + 1}",
                True,
                (255, 224, 120) if active else (215, 220, 216)
            )
            window.game_surface.blit(
                hand_label,
                hand_label.get_rect(center=(center_x, 408))
            )

            card_count = max(1, len(hand))
            card_spacing = min(70, 205 // max(1, card_count - 1))
            total_width = 100 + max(0, card_count - 1) * card_spacing
            start_x = center_x - total_width // 2
            card_y = 428

            for index, card in enumerate(hand):
                target_x = start_x + index * card_spacing
                position = get_blackjack_animated_position(
                    f"player_{hand_index}",
                    index,
                    target_x,
                    card_y
                )
                if position is None:
                    continue
                x, y = position
                card_key = get_card_key(card)
                window.game_surface.blit(legacy.game.card_fronts[card_key], (x, y))

            value = blackjack_game.get_hand_value_at(hand_index)
            wager = blackjack_game.player_hand_bets[hand_index]
            detail = fonts.blackjack_small_font.render(
                f"Total {value}   |   Bet ${wager:,}",
                True,
                (255, 232, 148) if active else (240, 240, 236)
            )
            detail_rect = detail.get_rect(center=(center_x, 594))
            detail_bg = detail_rect.inflate(20, 10)
            _draw_blackjack_panel(
                detail_bg,
                fill=(8, 24, 18, 205),
                border=(232, 198, 95) if active else (173, 190, 179),
                radius=8
            )
            window.game_surface.blit(detail, detail_rect)

            if blackjack_game.round_complete:
                hand_result = blackjack_game.get_hand_result(hand_index)
                result_names = {
                    "player": "WIN",
                    "push": "PUSH",
                    "dealer": "LOSS",
                }
                result_label = fonts.blackjack_small_font.render(
                    result_names.get(hand_result, ""),
                    True,
                    (255, 224, 120)
                )
                window.game_surface.blit(
                    result_label,
                    result_label.get_rect(center=(center_x, 625))
                )
    else:
        player_heading = fonts.blackjack_heading_font.render(
            "YOUR HAND",
            True,
            (245, 235, 205)
        )
        window.game_surface.blit(
            player_heading,
            player_heading.get_rect(center=(686, 390))
        )

        player_count = max(1, len(blackjack_game.player_hand))
        player_spacing = min(92, 430 // max(1, player_count - 1))
        player_total_width = 100 + max(0, player_count - 1) * player_spacing
        player_x = 686 - player_total_width // 2
        player_y = 420

        for index, card in enumerate(blackjack_game.player_hand):
            target_x = player_x + index * player_spacing
            position = get_blackjack_animated_position(
                "player",
                index,
                target_x,
                player_y
            )
            if position is None:
                continue

            x, y = position
            card_key = get_card_key(card)
            window.game_surface.blit(
                legacy.game.card_fronts[card_key],
                (x, y)
            )

        player_value_surface = fonts.blackjack_body_font.render(
            f"Hand total: {blackjack_game.player_value()}",
            True,
            (245, 245, 240)
        )
        player_value_rect = player_value_surface.get_rect(center=(686, 602))
        player_bg = player_value_rect.inflate(28, 14)
        _draw_blackjack_panel(
            player_bg,
            fill=(8, 24, 18, 205),
            border=(173, 190, 179),
            radius=8
        )
        window.game_surface.blit(player_value_surface, player_value_rect)

    # ==================================================
    # Bankroll / next wager panel
    # ==================================================

    panel_title = fonts.blackjack_heading_font.render(
        "TABLE BANK",
        True,
        (255, 225, 130)
    )
    window.game_surface.blit(
        panel_title,
        panel_title.get_rect(center=(right_panel.centerx, 138))
    )

    info_lines = [
        f"Current wager: ${blackjack_game.bet:,}",
        f"Cash: ${state.career_cash:,}",
    ]
    if state.blackjack_session_net > 0:
        session_text = f"Session: +${state.blackjack_session_net:,}"
    elif state.blackjack_session_net < 0:
        session_text = f"Session: -${abs(state.blackjack_session_net):,}"
    else:
        session_text = "Session: $0"
    info_lines.append(session_text)
    if state.current_game_mode == "career":
        info_lines.append(f"Casino: {state.career_ratings['casino']:,} ({state.blackjack_session_rating_change:+d})")

    for index, text in enumerate(info_lines):
        surface = fonts.blackjack_body_font.render(
            text,
            True,
            (235, 238, 235)
        )
        window.game_surface.blit(
            surface,
            (right_panel.x + 20, 182 + index * 34)
        )

    next_bet_heading = fonts.blackjack_heading_font.render(
        "NEXT HAND BET",
        True,
        (255, 225, 130)
    )
    window.game_surface.blit(
        next_bet_heading,
        next_bet_heading.get_rect(center=(right_panel.centerx, 326))
    )

    next_bet_note = fonts.blackjack_small_font.render(
        "Choose your next wager anytime.",
        True,
        (180, 196, 187)
    )
    window.game_surface.blit(
        next_bet_note,
        next_bet_note.get_rect(center=(right_panel.centerx, 350))
    )

    bet_choices = [
        ("1%", 0.01),
        ("2%", 0.02),
        ("5%", 0.05),
        ("10%", 0.10),
        ("ALL IN", 1.0),
    ]

    for index, (label_text, percentage) in enumerate(bet_choices):
        amount = get_blackjack_bet(percentage) if state.career_cash > 0 else 0
        if percentage >= 1.0:
            button_text = f"{label_text}  ${amount:,}"
        else:
            button_text = f"{label_text}  ${amount:,}"
        _draw_blackjack_button(
            blackjack_bet_dropdown_rects[index],
            button_text,
            state.game_mouse_pos,
            selected=(state.blackjack_selected_bet_percentage == percentage),
            font=fonts.blackjack_small_font
        )

    # ==================================================
    # Result / temporary dealer reveal status
    # ==================================================

    if blackjack_game.round_complete:
        net_result = blackjack_game.get_net_result()

        if blackjack_game.is_split_round():
            if net_result > 0:
                result_text = f"SPLIT HANDS  +${net_result:,}"
            elif net_result < 0:
                result_text = f"SPLIT HANDS  -${abs(net_result):,}"
            else:
                result_text = "SPLIT HANDS  EVEN"
        else:
            dealer_natural = (
                len(blackjack_game.dealer_hand) == 2
                and blackjack_game.dealer_value() == 21
            )
            player_natural = (
                len(blackjack_game.player_hand) == 2
                and blackjack_game.player_value() == 21
            )

            if blackjack_game.result == "blackjack":
                result_text = f"BLACKJACK!  +${net_result:,}"
            elif blackjack_game.result == "player":
                result_text = f"YOU WIN  +${net_result:,}"
            elif blackjack_game.result == "push" and dealer_natural and player_natural:
                result_text = "BOTH BLACKJACK - PUSH"
            elif blackjack_game.result == "push":
                result_text = "PUSH - BET RETURNED"
            elif dealer_natural:
                result_text = "DEALER BLACKJACK"
            else:
                result_text = f"DEALER WINS  ${blackjack_game.bet:,}"

        result_surface = fonts.blackjack_heading_font.render(
            result_text,
            True,
            (255, 226, 125)
        )
        result_rect = result_surface.get_rect(center=(686, 358))
        result_bg = result_rect.inflate(34, 18)
        _draw_blackjack_panel(
            result_bg,
            fill=(30, 24, 12, 225),
            border=(232, 198, 95),
            radius=9
        )
        window.game_surface.blit(result_surface, result_rect)

    elif blackjack_game.pending_natural_result is not None:
        reveal_surface = fonts.blackjack_body_font.render(
            "Dealer checks the hole card...",
            True,
            (244, 226, 165)
        )
        window.game_surface.blit(
            reveal_surface,
            reveal_surface.get_rect(center=(686, 358))
        )

    # ==================================================
    # Controls
    # ==================================================

    if (
            not blackjack_game.round_complete
            and not blackjack_game.player_stood
    ):
        _draw_blackjack_button(
            blackjack_hit_rect,
            "Hit",
            state.game_mouse_pos,
            font=fonts.blackjack_body_font
        )
        _draw_blackjack_button(
            blackjack_stand_rect,
            "Stand",
            state.game_mouse_pos,
            font=fonts.blackjack_body_font
        )
        if (
                blackjack_game.can_double_down()
                and state.career_cash >= blackjack_game.current_hand_bet()
        ):
            _draw_blackjack_button(
                blackjack_double_rect,
                "Double",
                state.game_mouse_pos,
                font=fonts.blackjack_body_font
            )

        if (
                blackjack_game.can_split()
                and state.career_cash >= blackjack_game.current_hand_bet()
        ):
            _draw_blackjack_button(
                blackjack_split_rect,
                "Split",
                state.game_mouse_pos,
                font=fonts.blackjack_body_font
            )

    elif blackjack_game.round_complete:
        if state.career_cash > 0:
            _draw_blackjack_button(
                blackjack_deal_again_rect,
                "Deal Next Hand",
                state.game_mouse_pos,
                font=fonts.blackjack_body_font
            )
        else:
            out_surface = fonts.blackjack_heading_font.render(
                "OUT OF CASH",
                True,
                (255, 220, 120)
            )
            window.game_surface.blit(
                out_surface,
                out_surface.get_rect(center=blackjack_deal_again_rect.center)
            )

    # Return is intentionally visible throughout the hand, but only clickable
    # after the result. The tooltip explains the disabled state.
    if blackjack_game.round_complete:
        _draw_blackjack_button(
            blackjack_return_rect,
            "Return",
            state.game_mouse_pos,
            font=fonts.blackjack_body_font
        )
    else:
        pygame.draw.rect(
            window.game_surface,
            (68, 76, 72),
            blackjack_return_rect,
            border_radius=7
        )
        pygame.draw.rect(
            window.game_surface,
            (145, 154, 149),
            blackjack_return_rect,
            2,
            border_radius=7
        )
        disabled = fonts.blackjack_body_font.render(
            "Return",
            True,
            (155, 160, 157)
        )
        window.game_surface.blit(
            disabled,
            disabled.get_rect(center=blackjack_return_rect.center)
        )

        if (
                state.game_mouse_pos is not None
                and blackjack_return_rect.collidepoint(state.game_mouse_pos)
        ):
            tooltip = fonts.blackjack_small_font.render(
                "Finish the current hand before leaving.",
                True,
                (255, 255, 255)
            )
            tooltip_rect = tooltip.get_rect(
                midbottom=(blackjack_return_rect.centerx, blackjack_return_rect.y - 8)
            )
            tooltip_bg = tooltip_rect.inflate(18, 10)
            pygame.draw.rect(
                window.game_surface,
                (18, 24, 21),
                tooltip_bg,
                border_radius=6
            )
            window.game_surface.blit(tooltip, tooltip_rect)


def get_blackjack_bet(
        percentage
):

    if state.career_cash <= 0:
        return 0

    if percentage >= 1.0:
        return state.career_cash

    return max(
        1,
        round(
            state.career_cash
            * percentage
        )
    )

def settle_blackjack_round():

    if not blackjack_game.round_complete:
        return

    if blackjack_game.payout_claimed:
        return

    payout = blackjack_game.get_payout()

    state.career_cash += payout

    net_result = (
        payout
        - blackjack_game.bet
    )

    state.blackjack_session_net += (
        net_result
    )
    if state.current_game_mode == "career":
        if blackjack_game.is_split_round():
            blackjack_game.rating_change = sum(career_rewards.rate_house_game("blackjack", 1 if result == "player" else -1 if result == "dealer" else 0)
                                               for result in blackjack_game.player_hand_results)
        else:
            blackjack_game.rating_change = career_rewards.rate_house_game("blackjack", net_result)
    else:
        blackjack_game.rating_change = None
    state.blackjack_session_rating_change = legacy.game_namespace().get("blackjack_session_rating_change", 0) + int(blackjack_game.rating_change or 0)

    if net_result > 0:
        career_rewards.award_fans_for_cash_win(
            net_result,
            "Blackjack win"
        )
    elif state.current_game_mode == "career" and net_result <= -500:
        legacy.lose_fans_for_bad_result(
            "Rough Blackjack hand",
            net_loss=abs(net_result),
            severity=0.65,
        )

    leveling.award_game_xp(
        "blackjack",
        won=(net_result > 0),
        bonus=12 if blackjack_game.result == "blackjack" else 0,
    )

    blackjack_hand_values = [
        blackjack_game.get_hand_value(hand)
        for hand in blackjack_game.get_player_hands()
    ]

    leveling.process_achievement_event(
        "blackjack_round",
        result=blackjack_game.result,
        net=net_result,
        natural=(
            not blackjack_game.is_split_round()
            and len(blackjack_game.player_hand) == 2
            and blackjack_game.player_value() == 21
        ),
        doubled=state.blackjack_round_doubled,
        all_in=state.blackjack_round_all_in,
        # The player pressed Stand (not just "turn over", which doubles,
        # naturals and 21s also reach) (B30).
        stood=bool(getattr(blackjack_game, "player_chose_stand", False)),
        player_total=max(blackjack_hand_values, default=0),
        hit_count=max(
            0,
            blackjack_game.get_total_player_cards()
            - (4 if blackjack_game.is_split_round() else 2)
        ),
        starting_bet=state.blackjack_round_start_bet,
    )

    track_night_cash(legacy.game_namespace(), "blackjack", net_result)
    blackjack_game.payout_claimed = True


def get_card_key(
        card
):
    rank, suit = card

    return f"{rank}{suit}"

def get_blackjack_animated_position(
        hand_name,
        card_index,
        target_x,
        target_y
):

    progress = (
        blackjack_game.get_card_animation_progress(
            hand_name,
            card_index
        )
    )

    # Card's animation has not begun.
    if progress < 0:
        return None

    deck_x = 1120
    deck_y = 265

    # Smooth-out cubic ease.
    eased = (
        1
        - (1 - progress) ** 3
    )

    x = (
        deck_x
        + (
            target_x
            - deck_x
        )
        * eased
    )

    y = (
        deck_y
        + (
            target_y
            - deck_y
        )
        * eased
    )

    return (
        int(x),
        int(y)
    )


def loop_event_blackjack_bet(event):
    """Old main-loop event branch for STATE_BLACKJACK_BET."""

    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):

        selected_bet = None

        # ==========================================
        # Bet selection
        # ==========================================

        if state.career_cash > 0:

            if blackjack_bet_1_rect.collidepoint(
                    state.game_mouse_pos
            ):

                state.blackjack_selected_bet_percentage = (
                    0.01
                )

                selected_bet = (
                    get_blackjack_bet(
                        state.blackjack_selected_bet_percentage
                    )
                )

            elif blackjack_bet_2_rect.collidepoint(
                    state.game_mouse_pos
            ):

                state.blackjack_selected_bet_percentage = (
                    0.02
                )

                selected_bet = (
                    get_blackjack_bet(
                        state.blackjack_selected_bet_percentage
                    )
                )

            elif blackjack_bet_5_rect.collidepoint(
                    state.game_mouse_pos
            ):

                state.blackjack_selected_bet_percentage = (
                    0.05
                )

                selected_bet = (
                    get_blackjack_bet(
                        state.blackjack_selected_bet_percentage
                    )
                )

            elif blackjack_bet_10_rect.collidepoint(
                    state.game_mouse_pos
            ):

                state.blackjack_selected_bet_percentage = (
                    0.10
                )

                selected_bet = (
                    get_blackjack_bet(
                        state.blackjack_selected_bet_percentage
                    )
                )

            elif blackjack_bet_all_rect.collidepoint(
                    state.game_mouse_pos
            ):

                state.blackjack_selected_bet_percentage = (
                    1.0
                )

                selected_bet = (
                    get_blackjack_bet(
                        state.blackjack_selected_bet_percentage
                    )
                )

        # ==========================================
        # Start hand
        # ==========================================

        if (
                selected_bet is not None
                and selected_bet > 0
                and state.career_cash >= selected_bet
        ):

            sounds.audio.play_sound(
                "button_click"
            )

            state.blackjack_round_doubled = False
            state.blackjack_round_all_in = (
                selected_bet >= state.career_cash
            )
            state.blackjack_round_start_bet = selected_bet

            state.career_cash -= (
                selected_bet
            )

            blackjack_game.start_round(
                selected_bet
            )

            state.career_event_has_activity = True

            state.current_state = state_names.STATE_BLACKJACK

        # ==========================================
        # Return
        # ==========================================

        elif blackjack_bet_return_rect.collidepoint(
                state.game_mouse_pos
        ):

            sounds.audio.play_sound(
                "button_click"
            )

            if state.current_game_mode == "free":
                legacy.finish_free_play_sandbox()
            state.current_state = (
                state_names.STATE_FREE_PLAY_SELECT if state.current_game_mode == "free" else state_names.STATE_CAREER_EVENT_SELECT
            )


def loop_event_blackjack(event):
    """Old main-loop event branch for STATE_BLACKJACK."""

    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):

        # ==========================================
        # Next-hand bet selection
        # ==========================================

        next_bet_choices = [
            0.01,
            0.02,
            0.05,
            0.10,
            1.0,
        ]
        next_bet_clicked = False

        for state.index, state.rect in enumerate(blackjack_bet_dropdown_rects):
            if state.rect.collidepoint(state.game_mouse_pos):
                state.blackjack_selected_bet_percentage = next_bet_choices[state.index]
                state.blackjack_bet_dropdown_open = False
                sounds.audio.play_sound("button_click")
                next_bet_clicked = True
                break

        # ==========================================
        # Hit
        # ==========================================

        if next_bet_clicked:
            return

        # ==========================================

        elif (
                not blackjack_game.round_complete
                and blackjack_hit_rect.collidepoint(
            state.game_mouse_pos
        )
        ):

            sounds.audio.play_sound(
                "card_draw"
            )

            blackjack_game.hit()

        # ==========================================
        # Stand
        # ==========================================

        elif (
                not blackjack_game.round_complete
                and blackjack_stand_rect.collidepoint(
            state.game_mouse_pos
        )
        ):

            sounds.audio.play_sound(
                "button_click"
            )

            blackjack_game.stand()

        # ==========================================
        # Split
        # ==========================================

        elif (
                blackjack_game.can_split()
                and state.career_cash >= blackjack_game.current_hand_bet()
                and blackjack_split_rect.collidepoint(
            state.game_mouse_pos
        )
        ):
            state.additional_bet = blackjack_game.current_hand_bet()

            if state.career_cash >= state.additional_bet:
                state.career_cash -= state.additional_bet
                sounds.audio.play_sound("button_click")
                sounds.audio.play_sound("card_draw")
                blackjack_game.split_hand()

        # ==========================================
        # Double
        # ==========================================

        elif (
                blackjack_game.can_double_down()
                and state.career_cash >= blackjack_game.current_hand_bet()
                and blackjack_double_rect.collidepoint(
            state.game_mouse_pos
        )
        ):

            state.additional_bet = blackjack_game.current_hand_bet()

            if state.career_cash >= state.additional_bet:
                state.career_cash -= state.additional_bet

                sounds.audio.play_sound(
                    "button_click"
                )

                sounds.audio.play_sound(
                    "card_draw"
                )

                state.blackjack_round_doubled = True
                blackjack_game.double_down()

        # ==========================================
        # Deal Again
        # ==========================================

        elif (
                blackjack_game.round_complete
                and state.career_cash > 0
                and blackjack_deal_again_rect.collidepoint(
            state.game_mouse_pos
        )
        ):

            if (
                    state.blackjack_selected_bet_percentage
                    is not None
            ):

                next_bet = (
                    get_blackjack_bet(
                        state.blackjack_selected_bet_percentage
                    )
                )

                if (
                        next_bet > 0
                        and state.career_cash >= next_bet
                ):
                    sounds.audio.play_sound(
                        "button_click"
                    )

                    state.blackjack_round_doubled = False
                    state.blackjack_round_all_in = (
                        next_bet >= state.career_cash
                    )
                    state.blackjack_round_start_bet = next_bet

                    state.career_cash -= (
                        next_bet
                    )

                    blackjack_game.start_round(
                        next_bet
                    )

                    state.blackjack_bet_dropdown_open = False

        # ==========================================
        # Return
        # ==========================================

        elif (
                blackjack_game.round_complete
                and blackjack_return_rect.collidepoint(
            state.game_mouse_pos
        )
        ):

            sounds.audio.play_sound(
                "button_click"
            )

            state.blackjack_bet_dropdown_open = False

            if state.current_game_mode == "free":
                legacy.finish_free_play_sandbox()
            state.current_state = (
                state_names.STATE_FREE_PLAY_SELECT if state.current_game_mode == "free" else state_names.STATE_CAREER_EVENT_SELECT
            )


def loop_draw_blackjack():
    """Old draw-chain branch for STATE_BLACKJACK."""

    blackjack_game.update()

    settle_blackjack_round()

    draw_blackjack()


def loop_draw_blackjack_bet():
    """Old draw-chain branch for STATE_BLACKJACK_BET."""

    draw_blackjack_bet()
