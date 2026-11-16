"""Arcade night token exchange, prize counter and trophy room (moved out of legacy.py)."""
from solitaireplus.games.arcade.support import ARCADE_PRIZE_CATALOG
from solitaireplus.games.arcade.support import ARCADE_TOKEN_PACKAGES
from solitaireplus.games.solitaire.rules import BASE_HEIGHT
from solitaireplus.games.solitaire.rules import BASE_WIDTH
from solitaireplus.games.arcade.support import buy_token_package
from solitaireplus.career import career_saving
from solitaireplus.games.arcade.support import clone_arcade_state
from solitaireplus.games.arcade.support import get_machine_cost
import math
from solitaireplus.app import paths
import pygame
from solitaireplus.games.arcade.support import redeem_prize
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
machine_screens = lazy("solitaireplus.games.arcade.machine_screens")
images = lazy("solitaireplus.ui.images")
window = lazy("solitaireplus.app.window")
ui_text = lazy("solitaireplus.ui.text")
sounds = lazy("solitaireplus.app.sounds")
fonts = lazy("solitaireplus.app.fonts")
cursors = lazy("solitaireplus.ui.cursors")
buttons = lazy("solitaireplus.ui.buttons")


arcade_token_package_rects = {}
for package_index in range(len(ARCADE_TOKEN_PACKAGES)):
    row = package_index // 2
    column = package_index % 2
    arcade_token_package_rects[package_index] = pygame.Rect(
        248 + column * 475,
        270 + row * 172,
        395,
        132,
    )

arcade_token_exchange_back_rect = pygame.Rect(128, 658, 240, 54)
arcade_token_exchange_continue_rect = pygame.Rect(998, 658, 240, 54)

ARCADE_PRIZES_PER_PAGE = 4
arcade_prize_card_rects = {
    slot: pygame.Rect(102 + slot * 292, 207, 270, 300)
    for slot in range(ARCADE_PRIZES_PER_PAGE)
}
arcade_prize_prev_rect = pygame.Rect(474, 525, 118, 38)
arcade_prize_next_rect = pygame.Rect(774, 525, 118, 38)
arcade_prize_back_rect = pygame.Rect(106, 658, 220, 54)
arcade_prize_trophy_room_rect = pygame.Rect(573, 658, 220, 54)
arcade_prize_buy_rect = pygame.Rect(1040, 658, 220, 54)
arcade_trophy_room_back_rect = pygame.Rect(503, 658, 360, 54)


def set_arcade_status_message(message, duration_ms=2600):

    state.arcade_status_message = str(message or "")
    state.arcade_status_message_expires = pygame.time.get_ticks() + max(600, int(duration_ms or 0))


def open_arcade_token_exchange(pending_game_id=None):

    state.arcade_pending_launch_game_id = pending_game_id
    state.current_state = state_names.STATE_ARCADE_TOKEN_EXCHANGE


# Arcade Night uses authored image buttons instead of the generic wood/menu
# controls. Missing art falls back to the normal button renderer so a code
# update never makes the event unusable while artwork is being prepared.
ARCADE_ACTION_BUTTON_ASSET_PATHS = {
    "buy_tokens": str(paths.asset("arcade/ui/buy_tokens.png")),
    "prize_counter": str(paths.asset("arcade/ui/prize_counter.png")),
    "return": str(paths.asset("arcade/ui/return.png")),
    "end": str(paths.asset("arcade/ui/end_night.png")),
    # Shared small controls used by the individual Arcade game setup screens.
    # play_tokens.png should include the PLAY artwork/label; the changing token
    # price is drawn by code just above the button so one asset works for every game.
    "back": str(paths.asset("arcade/ui/back.png")),
    "play_tokens": str(paths.asset("arcade/ui/play_tokens.png")),
    "reroll_rivals": str(paths.asset("arcade/ui/reroll_rivals.png")),
    "quit": str(paths.asset("arcade/ui/quit.png")),
    "continue": str(paths.asset("arcade/ui/continue.png")),
    "redeem_tickets": str(paths.asset("arcade/ui/redeem_tickets.png")),
    "trophy_room": str(paths.asset("arcade/ui/trophy_room.png")),
    "back_to_prize_counter": str(paths.asset("arcade/ui/back_to_prize_counter.png")),
}


def draw_arcade_action_image_button(
        rect,
        button_kind,
        fallback_text,
        enabled=True,
        badge_text=None,
):
    """Draw an Arcade control with authored PNG art and a safe generic fallback.

    ``badge_text`` is intended for values that change in code (currently the
    machine entry price). The authored play_tokens.png can therefore say PLAY
    while the live ``2 TOKENS`` / ``3 TOKENS`` value remains accurate without
    covering any part of the button artwork.
    """
    path = ARCADE_ACTION_BUTTON_ASSET_PATHS.get(button_kind)
    image = images.get_cover_scaled_ui_asset(path, rect.size)
    hovered = (
        enabled
        and state.game_mouse_pos is not None
        and rect.collidepoint(state.game_mouse_pos)
    )

    if image is None:
        buttons.draw_menu_button(
            rect,
            fallback_text,
            state.game_mouse_pos if enabled else None,
            font=fonts.difficulty_detail_font,
        )
        if not enabled:
            overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 125))
            window.game_surface.blit(overlay, rect.topleft)
        return

    button = image.copy()
    if hovered:
        button.fill((24, 24, 24, 0), special_flags=pygame.BLEND_RGBA_ADD)
    if not enabled:
        button.fill((105, 105, 105, 255), special_flags=pygame.BLEND_RGBA_MULT)
        button.set_alpha(145)

    window.game_surface.blit(button, rect.topleft)

    border_color = (247, 213, 115) if hovered else (177, 190, 205)
    pygame.draw.rect(
        window.game_surface,
        border_color,
        rect,
        3 if hovered else 2,
        border_radius=9,
    )

    if badge_text:
        # Keep the changing entry price completely outside the authored PLAY
        # art. This preserves custom transparent button designs instead of
        # covering the right side with a live-value badge.
        badge = fonts.arcade_button_badge_font.render(
            badge_text,
            True,
            (246, 239, 214),
        )
        shadow = fonts.arcade_button_badge_font.render(
            badge_text,
            True,
            (6, 9, 13),
        )
        badge_center = (rect.centerx, rect.top - 11)
        window.game_surface.blit(
            shadow,
            shadow.get_rect(center=(badge_center[0] + 1, badge_center[1] + 1)),
        )
        window.game_surface.blit(
            badge,
            badge.get_rect(center=badge_center),
        )


def draw_arcade_page_background(shade_alpha=72):
    background = images.get_event_ui_asset(str(paths.asset("arcade/bg.png")), (BASE_WIDTH, BASE_HEIGHT))
    if background is not None:
        window.game_surface.blit(background, (0, 0))
    else:
        window.game_surface.fill((12, 18, 28))
    shade = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
    shade.fill((0, 0, 0, max(0, min(255, int(shade_alpha)))))
    window.game_surface.blit(shade, (0, 0))


def draw_arcade_token_exchange():
    draw_arcade_page_background(62)

    panel = pygame.Rect(90, 58, 1186, 662)
    panel_surface = pygame.Surface(panel.size, pygame.SRCALPHA)
    panel_surface.fill((10, 17, 28, 235))
    window.game_surface.blit(panel_surface, panel.topleft)
    pygame.draw.rect(window.game_surface, (229, 197, 102), panel, 3, border_radius=16)

    title = fonts.options_title_font.render("ARCADE TOKEN EXCHANGE", True, (255, 255, 255))
    subtitle = fonts.difficulty_detail_font.render(
        "Trade Career cash for tokens. Tickets are earned by playing the machines.",
        True,
        (214, 220, 226),
    )
    window.game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 102)))
    window.game_surface.blit(subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 140)))

    status = (
        ("CASH", f"${state.career_cash:,}"),
        ("TOKENS", f"{int(state.arcade_state.get('tokens', 0)):,}"),
        ("TICKETS", f"{int(state.arcade_state.get('tickets', 0)):,}"),
    )
    for index, (label, value) in enumerate(status):
        rect = pygame.Rect(226 + index * 310, 166, 270, 58)
        pygame.draw.rect(window.game_surface, (7, 14, 24), rect, border_radius=10)
        pygame.draw.rect(window.game_surface, (95, 176, 205), rect, 2, border_radius=10)
        label_surface = fonts.difficulty_detail_font.render(label, True, (179, 191, 203))
        value_surface = fonts.option_label_font.render(value, True, (255, 237, 156))
        window.game_surface.blit(label_surface, label_surface.get_rect(midleft=(rect.x + 16, rect.centery)))
        window.game_surface.blit(value_surface, value_surface.get_rect(midright=(rect.right - 16, rect.centery)))

    for index, package in enumerate(ARCADE_TOKEN_PACKAGES):
        rect = arcade_token_package_rects[index]
        hovered = state.game_mouse_pos is not None and rect.collidepoint(state.game_mouse_pos)
        fill = (28, 38, 52) if not hovered else (37, 52, 68)
        pygame.draw.rect(window.game_surface, fill, rect, border_radius=14)
        pygame.draw.rect(
            window.game_surface,
            (230, 199, 108) if hovered else (119, 132, 148),
            rect,
            3 if hovered else 2,
            border_radius=14,
        )

        name = fonts.option_label_font.render(package["name"], True, (247, 248, 249))
        token_count = fonts.options_title_font.render(str(package["tokens"]), True, (255, 236, 142))
        token_label = fonts.difficulty_detail_font.render("TOKENS", True, (255, 240, 180))
        cash_label = fonts.difficulty_detail_font.render(
            f"${package['cash_cost']} CASH",
            True,
            (202, 210, 220),
        )

        window.game_surface.blit(name, name.get_rect(center=(rect.centerx, rect.y + 25)))
        window.game_surface.blit(token_count, token_count.get_rect(center=(rect.centerx, rect.y + 65)))
        window.game_surface.blit(token_label, token_label.get_rect(center=(rect.centerx, rect.y + 94)))
        window.game_surface.blit(cash_label, cash_label.get_rect(center=(rect.centerx, rect.bottom - 18)))

    if state.arcade_status_message and pygame.time.get_ticks() <= state.arcade_status_message_expires:
        info = fonts.difficulty_detail_font.render(state.arcade_status_message, True, (248, 242, 216))
        info_rect = info.get_rect(center=(BASE_WIDTH // 2, 619)).inflate(26, 12)
        info_panel = pygame.Surface(info_rect.size, pygame.SRCALPHA)
        info_panel.fill((5, 11, 20, 225))
        window.game_surface.blit(info_panel, info_rect.topleft)
        pygame.draw.rect(window.game_surface, (226, 194, 104), info_rect, 2, border_radius=8)
        window.game_surface.blit(info, info.get_rect(center=info_rect.center))

    draw_arcade_action_image_button(
        arcade_token_exchange_back_rect,
        "back",
        "Back",
    )
    if (
            state.arcade_pending_launch_game_id == "king_pong"
            and int(state.arcade_state.get("tokens", 0)) >= get_machine_cost("king_pong")
    ):
        continue_label = "Play King Pong"
    elif (
            state.arcade_pending_launch_game_id == "battle_bosses"
            and int(state.arcade_state.get("tokens", 0)) >= get_machine_cost("battle_bosses")
    ):
        continue_label = "Play Battle Bosses"
    else:
        continue_label = "Continue"
    draw_arcade_action_image_button(
        arcade_token_exchange_continue_rect,
        "continue",
        continue_label,
        enabled=True,
    )


def redeem_arcade_prize_for_career(prize_id):
    """Redeem one ticket prize and atomically unlock any attached cosmetic."""
    previous_state = clone_arcade_state(state.arcade_state)
    previous_backgrounds = set(state.unlocked_menu_backgrounds)
    previous_felts = set(state.unlocked_felts)
    previous_titles = set(state.unlocked_titles)
    previous_cursors = set(cursors.unlocked_cursors)

    success, new_state, message, prize = redeem_prize(state.arcade_state, prize_id)
    if not success:
        return False, message, prize

    state.arcade_state = new_state
    if prize and prize.get("kind") == "cosmetic":
        from solitaireplus.profile.cosmetics import unlock_reward
        unlock_reward(
            prize.get("cosmetic_type"),
            prize.get("asset_id"),
            state.unlocked_menu_backgrounds,
            state.unlocked_felts,
            state.unlocked_titles,
            cursors.unlocked_cursors,
        )

    try:
        career_saving.auto_save_career()
    except Exception:
        state.arcade_state = previous_state
        state.unlocked_menu_backgrounds.clear(); state.unlocked_menu_backgrounds.update(previous_backgrounds)
        state.unlocked_felts.clear(); state.unlocked_felts.update(previous_felts)
        state.unlocked_titles.clear(); state.unlocked_titles.update(previous_titles)
        cursors.unlocked_cursors.clear(); cursors.unlocked_cursors.update(previous_cursors)
        raise
    return True, message, prize


def _draw_arcade_prize_page_button(rect, label, enabled):
    hovered = enabled and state.game_mouse_pos is not None and rect.collidepoint(state.game_mouse_pos)
    fill = (34, 48, 65) if hovered else (20, 29, 41)
    border = (247, 213, 115) if hovered else (126, 141, 158)
    pygame.draw.rect(window.game_surface, fill, rect, border_radius=8)
    pygame.draw.rect(window.game_surface, border, rect, 2, border_radius=8)
    color = (247, 241, 217) if enabled else (100, 111, 124)
    text = fonts.difficulty_detail_font.render(label, True, color)
    window.game_surface.blit(text, text.get_rect(center=rect.center))


def _draw_arcade_prize_art(prize, art_rect):
    art = images.get_event_ui_asset(prize.get("image"))
    if art is not None:
        scale = min(art_rect.width / art.get_width(), art_rect.height / art.get_height())
        size = (
            max(1, int(round(art.get_width() * scale))),
            max(1, int(round(art.get_height() * scale))),
        )
        art = pygame.transform.smoothscale(art, size)
        window.game_surface.blit(art, art.get_rect(center=art_rect.center))
        return

    # Safe placeholder while the authored prize PNG is being created.
    kind = prize.get("cosmetic_type") or prize.get("kind", "prize")
    pygame.draw.rect(window.game_surface, (12, 18, 27), art_rect, border_radius=10)
    pygame.draw.rect(window.game_surface, (91, 109, 132), art_rect, 2, border_radius=10)
    label = fonts.difficulty_detail_font.render(str(kind).replace("_", " ").upper(), True, (184, 196, 210))
    window.game_surface.blit(label, label.get_rect(center=art_rect.center))


def draw_arcade_prize_counter():
    draw_arcade_page_background(70)
    panel = pygame.Rect(70, 70, 1226, 620)
    pygame.draw.rect(window.game_surface, (16, 23, 34), panel, border_radius=18)
    pygame.draw.rect(window.game_surface, (226, 194, 104), panel, 3, border_radius=18)
    title = fonts.options_title_font.render("PRIZE COUNTER", True, (255, 255, 255))
    subtitle = fonts.difficulty_detail_font.render(
        "Redeem tickets for trophies and exclusive arcade cosmetics.",
        True,
        (210, 217, 224),
    )
    window.game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 112)))
    window.game_surface.blit(subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 145)))

    ticket_surface = fonts.option_label_font.render(
        f"Tickets: {int(state.arcade_state.get('tickets', 0)):,}",
        True,
        (255, 238, 154),
    )
    window.game_surface.blit(ticket_surface, ticket_surface.get_rect(center=(BASE_WIDTH // 2, 176)))

    page_count = max(1, math.ceil(len(ARCADE_PRIZE_CATALOG) / ARCADE_PRIZES_PER_PAGE))
    page = max(0, min(page_count - 1, int(state.arcade_prize_page)))
    page_start = page * ARCADE_PRIZES_PER_PAGE

    for slot, rect in arcade_prize_card_rects.items():
        index = page_start + slot
        if index >= len(ARCADE_PRIZE_CATALOG):
            continue
        prize = ARCADE_PRIZE_CATALOG[index]
        hovered = state.game_mouse_pos is not None and rect.collidepoint(state.game_mouse_pos)
        selected = index == state.arcade_selected_prize_index
        owned = prize['id'] in state.arcade_state.get('trophies', [])
        pygame.draw.rect(
            window.game_surface,
            (25, 34, 48) if not hovered and not selected else (34, 46, 64),
            rect,
            border_radius=14,
        )
        pygame.draw.rect(
            window.game_surface,
            (220, 191, 103) if hovered or selected else (109, 121, 138),
            rect,
            2,
            border_radius=14,
        )

        name_rect = pygame.Rect(rect.x + 12, rect.y + 12, rect.width - 24, 50)
        ui_text.draw_wrapped_text_limited(
            prize['name'], fonts.option_label_font, (248, 249, 250), name_rect, 2, line_spacing=2
        )
        _draw_arcade_prize_art(prize, pygame.Rect(rect.x + 72, rect.y + 66, 126, 86))

        cost = fonts.options_title_font.render(f"{prize['cost']}", True, (255, 236, 142))
        window.game_surface.blit(cost, cost.get_rect(center=(rect.centerx, rect.y + 178)))
        tickets_word = fonts.difficulty_detail_font.render("TICKETS", True, (255, 240, 180))
        window.game_surface.blit(tickets_word, tickets_word.get_rect(center=(rect.centerx, rect.y + 207)))
        ui_text.draw_wrapped_text_limited(
            prize['description'],
            fonts.difficulty_detail_font,
            (208, 216, 224),
            pygame.Rect(rect.x + 14, rect.y + 226, rect.width - 28, 46),
            2,
            line_spacing=3,
        )
        footer = "OWNED" if owned else prize.get("cosmetic_type", "Select").replace("_", " ").upper()
        footer_color = (135, 222, 173) if owned else (173, 182, 194)
        footer_surface = fonts.difficulty_detail_font.render(footer, True, footer_color)
        window.game_surface.blit(footer_surface, footer_surface.get_rect(center=(rect.centerx, rect.bottom - 16)))

    _draw_arcade_prize_page_button(arcade_prize_prev_rect, "PREV", page > 0)
    _draw_arcade_prize_page_button(arcade_prize_next_rect, "NEXT", page + 1 < page_count)
    page_text = fonts.difficulty_detail_font.render(f"PAGE {page + 1} / {page_count}", True, (178, 190, 204))
    window.game_surface.blit(page_text, page_text.get_rect(center=(BASE_WIDTH // 2, 544)))

    draw_arcade_action_image_button(arcade_prize_back_rect, "back", "Back")
    draw_arcade_action_image_button(arcade_prize_trophy_room_rect, "trophy_room", "Trophy Room")

    selected_index = max(0, min(len(ARCADE_PRIZE_CATALOG) - 1, state.arcade_selected_prize_index))
    selected_prize = ARCADE_PRIZE_CATALOG[selected_index]
    owned = selected_prize['id'] in state.arcade_state.get('trophies', [])
    draw_arcade_action_image_button(
        arcade_prize_buy_rect,
        "redeem_tickets",
        "Redeem Tickets",
        enabled=not owned,
        badge_text=f"{selected_prize['cost']} TICKETS" if not owned else "OWNED",
    )

    if state.arcade_status_message and pygame.time.get_ticks() <= state.arcade_status_message_expires:
        info = fonts.difficulty_detail_font.render(state.arcade_status_message, True, (246, 241, 217))
        bg = info.get_rect(center=(BASE_WIDTH // 2, 610)).inflate(28, 16)
        overlay = pygame.Surface(bg.size, pygame.SRCALPHA)
        overlay.fill((8, 14, 24, 225))
        window.game_surface.blit(overlay, bg.topleft)
        pygame.draw.rect(window.game_surface, (228, 197, 107), bg, 2, border_radius=9)
        window.game_surface.blit(info, info.get_rect(center=bg.center))

def draw_arcade_trophy_room():
    draw_arcade_page_background(66)
    panel = pygame.Rect(104, 92, 1158, 576)
    pygame.draw.rect(window.game_surface, (15, 21, 31), panel, border_radius=18)
    pygame.draw.rect(window.game_surface, (225, 193, 103), panel, 3, border_radius=18)
    title = fonts.options_title_font.render("ARCADE TROPHY ROOM", True, (255, 255, 255))
    subtitle = fonts.difficulty_detail_font.render(
        "Ticket trophies live here. Redeemed cosmetics are available under Customize.",
        True,
        (210, 217, 224),
    )
    window.game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 132)))
    window.game_surface.blit(subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 166)))

    trophies = [
        prize for prize in ARCADE_PRIZE_CATALOG
        if prize.get('kind') == 'trophy' and prize['id'] in state.arcade_state.get('trophies', [])
    ]
    if not trophies:
        empty = fonts.option_label_font.render("No trophies redeemed yet.", True, (232, 236, 240))
        hint = fonts.difficulty_detail_font.render("Visit the Prize Counter after stacking up some tickets.", True, (165, 175, 188))
        window.game_surface.blit(empty, empty.get_rect(center=(BASE_WIDTH // 2, 350)))
        window.game_surface.blit(hint, hint.get_rect(center=(BASE_WIDTH // 2, 388)))
    else:
        for index, prize in enumerate(trophies):
            rect = pygame.Rect(164 + (index % 3) * 330, 232 + (index // 3) * 180, 270, 132)
            pygame.draw.rect(window.game_surface, (29, 38, 52), rect, border_radius=14)
            pygame.draw.rect(window.game_surface, (222, 191, 102), rect, 2, border_radius=14)
            _draw_arcade_prize_art(prize, pygame.Rect(rect.x + 18, rect.y + 20, 66, 66))
            name = fonts.option_label_font.render(prize['name'], True, (248, 249, 250))
            cost = fonts.difficulty_detail_font.render(f"Redeemed for {prize['cost']} tickets", True, (189, 198, 208))
            window.game_surface.blit(name, name.get_rect(midleft=(rect.x + 96, rect.y + 42)))
            ui_text.draw_wrapped_text_limited(
                prize['description'], fonts.difficulty_detail_font, (210, 217, 224),
                pygame.Rect(rect.x + 96, rect.y + 56, rect.width - 114, 46), 2, line_spacing=4
            )
            window.game_surface.blit(cost, cost.get_rect(midleft=(rect.x + 96, rect.bottom - 22)))

    draw_arcade_action_image_button(
        arcade_trophy_room_back_rect,
        "back_to_prize_counter",
        "Back to Prize Counter",
    )


def loop_event_arcade_token_exchange(event):
    """Old main-loop event branch for STATE_ARCADE_TOKEN_EXCHANGE."""

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        if arcade_token_exchange_back_rect.collidepoint(state.menu_mouse_pos):
            sounds.audio.play_sound("button_click")
            if state.arcade_pending_launch_game_id == "king_pong":
                state.arcade_pending_launch_game_id = None
                state.current_state = state_names.STATE_KING_PONG_OPPONENT_SELECT
            elif state.arcade_pending_launch_game_id == "battle_bosses":
                state.arcade_pending_launch_game_id = None
                state.current_state = state_names.STATE_BATTLE_BOSSES_OPPONENT_SELECT
            elif state.arcade_pending_launch_game_id == "ace_invaders":
                state.arcade_pending_launch_game_id = None
                state.current_state = state_names.STATE_ACE_INVADERS_DIFFICULTY_SELECT
            elif state.arcade_pending_launch_game_id == "suit_snake":
                state.arcade_pending_launch_game_id = None
                state.current_state = state_names.STATE_SUIT_SNAKE_DIFFICULTY_SELECT
            else:
                state.current_state = state_names.STATE_CAREER_EVENT_SELECT
        elif arcade_token_exchange_continue_rect.collidepoint(state.menu_mouse_pos):
            sounds.audio.play_sound("button_click")
            if state.arcade_pending_launch_game_id == "king_pong":
                if int(state.arcade_state.get("tokens", 0)) >= get_machine_cost("king_pong"):
                    machine_screens.start_king_pong_session()
                else:
                    set_arcade_status_message("Buy enough tokens to play King Pong.")
            elif state.arcade_pending_launch_game_id == "battle_bosses":
                if int(state.arcade_state.get("tokens", 0)) >= get_machine_cost("battle_bosses"):
                    machine_screens.start_battle_bosses_session()
                else:
                    set_arcade_status_message("Buy enough tokens to play Battle Bosses.")
            elif state.arcade_pending_launch_game_id == "ace_invaders":
                if int(state.arcade_state.get("tokens", 0)) >= get_machine_cost("ace_invaders"):
                    machine_screens.start_ace_invaders_session()
                else:
                    set_arcade_status_message("Buy enough tokens to play Ace Invaders.")
            elif state.arcade_pending_launch_game_id == "suit_snake":
                if int(state.arcade_state.get("tokens", 0)) >= get_machine_cost("suit_snake"):
                    machine_screens.start_suit_snake_session()
                else:
                    set_arcade_status_message("Buy enough tokens to play Suit Snake.")
            else:
                state.current_state = state_names.STATE_CAREER_EVENT_SELECT
        else:
            for package_index, package_rect in arcade_token_package_rects.items():
                if package_rect.collidepoint(state.menu_mouse_pos):
                    package = ARCADE_TOKEN_PACKAGES[package_index]
                    state.success, new_state, new_cash, message = buy_token_package(state.arcade_state, state.career_cash, package['id'])
                    state.arcade_state = new_state
                    if state.success:
                        state.career_cash = new_cash
                        career_saving.auto_save_career()
                    set_arcade_status_message(message)
                    sounds.audio.play_sound("button_click")
                    break


def loop_event_arcade_prize_counter(event):
    """Old main-loop event branch for STATE_ARCADE_PRIZE_COUNTER."""

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        page_count = max(1, math.ceil(len(ARCADE_PRIZE_CATALOG) / ARCADE_PRIZES_PER_PAGE))
        if arcade_prize_back_rect.collidepoint(state.menu_mouse_pos):
            sounds.audio.play_sound("button_click")
            state.current_state = state_names.STATE_CAREER_EVENT_SELECT
        elif arcade_prize_trophy_room_rect.collidepoint(state.menu_mouse_pos):
            sounds.audio.play_sound("button_click")
            state.current_state = state_names.STATE_ARCADE_TROPHY_ROOM
        elif arcade_prize_buy_rect.collidepoint(state.menu_mouse_pos):
            prize = ARCADE_PRIZE_CATALOG[state.arcade_selected_prize_index]
            _success, message, _prize = redeem_arcade_prize_for_career(prize['id'])
            set_arcade_status_message(message)
            sounds.audio.play_sound("button_click")
        elif arcade_prize_prev_rect.collidepoint(state.menu_mouse_pos) and state.arcade_prize_page > 0:
            state.arcade_prize_page -= 1
            state.arcade_selected_prize_index = state.arcade_prize_page * ARCADE_PRIZES_PER_PAGE
            sounds.audio.play_sound("button_click")
        elif arcade_prize_next_rect.collidepoint(state.menu_mouse_pos) and state.arcade_prize_page + 1 < page_count:
            state.arcade_prize_page += 1
            state.arcade_selected_prize_index = state.arcade_prize_page * ARCADE_PRIZES_PER_PAGE
            sounds.audio.play_sound("button_click")
        else:
            page_start = state.arcade_prize_page * ARCADE_PRIZES_PER_PAGE
            for prize_slot, prize_rect in arcade_prize_card_rects.items():
                prize_index = page_start + prize_slot
                if prize_index < len(ARCADE_PRIZE_CATALOG) and prize_rect.collidepoint(state.menu_mouse_pos):
                    state.arcade_selected_prize_index = prize_index
                    sounds.audio.play_sound("button_click")
                    break


def loop_event_arcade_trophy_room(event):
    """Old main-loop event branch for STATE_ARCADE_TROPHY_ROOM."""

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        if arcade_trophy_room_back_rect.collidepoint(state.menu_mouse_pos):
            sounds.audio.play_sound("button_click")
            state.current_state = state_names.STATE_ARCADE_PRIZE_COUNTER


def loop_draw_arcade_token_exchange():
    """Old draw-chain branch for STATE_ARCADE_TOKEN_EXCHANGE."""

    draw_arcade_token_exchange()


def loop_draw_arcade_prize_counter():
    """Old draw-chain branch for STATE_ARCADE_PRIZE_COUNTER."""

    draw_arcade_prize_counter()


def loop_draw_arcade_trophy_room():
    """Old draw-chain branch for STATE_ARCADE_TROPHY_ROOM."""

    draw_arcade_trophy_room()
