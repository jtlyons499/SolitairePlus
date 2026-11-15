"""Career event-night game selection screen (moved out of legacy.py)."""
from solitaireplus.games.arcade.support import ARCADE_COMING_SOON_GAME_IDS
from solitaireplus.games.arcade.support import ARCADE_MACHINE_NAMES
from solitaireplus.games.solitaire.rules import BASE_HEIGHT
from solitaireplus.games.solitaire.rules import BASE_WIDTH
from solitaireplus.app.settings import GAME_UNLOCK_LEVELS
from solitaireplus.career.news import build_arcade_story
from solitaireplus.career.news import build_casino_story
from solitaireplus.career.news import build_casual_cards_story
from solitaireplus.career.news import build_niche_story
from solitaireplus.career.news import build_poker_story
from solitaireplus.games.arcade.support import get_machine_cost
from solitaireplus.npc.manager import get_random_blackjack_dealer
from solitaireplus.app import paths
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.career.event_progress import store_event_progress
from solitaireplus.app.lazy import lazy
news_screen = lazy("solitaireplus.career.news_screen")
night = lazy("solitaireplus.career.events.night")
career_saving = lazy("solitaireplus.career.career_saving")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
ui_text = lazy("solitaireplus.ui.text")
sounds = lazy("solitaireplus.app.sounds")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")


def publish_career_event_news():

    if state.career_event_news_posted:
        return False

    if not isinstance(state.career_event_entry, dict):
        return False

    activity_type = state.career_event_entry.get("activity_type")
    story = None

    if activity_type == night.CAREER_ACTIVITY_CASUAL_CARDS:
        story = build_casual_cards_story(
            state.player_name,
            state.career_event_result_log,
        )

    elif activity_type == night.CAREER_ACTIVITY_POKER_NIGHT:
        story = build_poker_story(
            state.player_name,
            {
                "texas_holdem": state.texas_holdem_session_net,
                "five_card_draw": state.five_card_draw_session_net,
                "seven_card_stud": state.seven_card_stud_session_net,
            },
        )

    elif activity_type == night.CAREER_ACTIVITY_CASINO_NIGHT:
        story = build_casino_story(
            state.player_name,
            blackjack_net=state.blackjack_session_net,
            roulette_net=state.roulette_session_net,
            horse_races_net=state.horse_races_session_net,
        )

    elif activity_type == night.CAREER_ACTIVITY_NICHE_NIGHT:
        story = build_niche_story(
            state.player_name,
            state.career_event_result_log,
        )

    elif activity_type == night.CAREER_ACTIVITY_ARCADE_NIGHT:
        story = build_arcade_story(
            state.player_name,
            state.career_event_result_log,
        )

    if story is None:
        return False

    headline, body, category = story
    news_screen.add_career_news(headline, body, category)
    state.career_event_news_posted = True
    return True

career_event_card_rects = []

career_event_return_rect = pygame.Rect(
    BASE_WIDTH // 2 - 245,
    646,
    220,
    59
)

career_event_end_rect = pygame.Rect(
    BASE_WIDTH // 2 + 25,
    646,
    220,
    59
)

arcade_machine_buy_tokens_rect = pygame.Rect(328, 535, 330, 92)
arcade_machine_prize_counter_rect = pygame.Rect(708, 535, 330, 92)
arcade_placeholder_music_toggle_rect = pygame.Rect(BASE_WIDTH - 276, 18, 246, 34)

def get_game_unlock_level(
        game_id
):
    return GAME_UNLOCK_LEVELS.get(
        game_id,
        1
    )

POKER_NIGHT_SELECTION_IMAGE_SIZE = (
    288,
    162
)

POKER_NIGHT_SELECTION_IMAGE_PATHS = {
    "texas_holdem":
        str(paths.asset("poker/poker_night/texas_holdem.png")),
    "seven_card_stud":
        str(paths.asset("poker/poker_night/seven_card_stud.png")),
    "five_card_draw":
        str(paths.asset("poker/poker_night/five_card_draw.png")),
}

_poker_night_selection_image_cache = {}


EVENT_SELECTION_IMAGE_SIZE = (288, 162)

EVENT_SELECTION_IMAGE_PATHS = {
    "score_four": str(paths.asset("events/casual_cards/score_four.png")),
    "crazy_eights": str(paths.asset("events/casual_cards/crazy_eights.png")),
    "bango": str(paths.asset("events/casual_cards/bango.png")),
    "blackjack": str(paths.asset("events/casino_night/blackjack.png")),
    "roulette": str(paths.asset("events/casino_night/roulette.png")),
    "horse_races": str(paths.asset("events/casino_night/horse_races.png")),
    "faro": str(paths.asset("events/niche_night/faro.png")),
    "five_o_poker": str(paths.asset("events/niche_night/five_o_poker.png")),
    "blind_mans_bluff": str(paths.asset("events/niche_night/blind_mans_bluff.png")),
    "king_pong": str(paths.asset("arcade/king_pong/select.png")),
    "battle_bosses": str(paths.asset("arcade/battle_bosses/select.png")),
    "ace_invaders": str(paths.asset("arcade/ace_invaders/select.png")),
    "suit_snake": str(paths.asset("arcade/suit_snake/select.png")),
    "prize_counter": str(paths.asset("arcade/ui/prize_counter.png")),
}

_event_selection_image_cache = {}

EVENT_TITLE_ASSET_PATHS = {
    night.CAREER_ACTIVITY_CASUAL_CARDS: str(paths.asset("events/casual_cards/title.png")),
    night.CAREER_ACTIVITY_POKER_NIGHT: str(paths.asset("events/poker_night/title.png")),
    night.CAREER_ACTIVITY_CASINO_NIGHT: str(paths.asset("events/casino_night/title.png")),
    night.CAREER_ACTIVITY_NICHE_NIGHT: str(paths.asset("events/niche_night/title.png")),
}

EVENT_BACKGROUND_ASSET_PATHS = {
    night.CAREER_ACTIVITY_CASUAL_CARDS: str(paths.asset("events/casual_cards/background.png")),
    night.CAREER_ACTIVITY_POKER_NIGHT: str(paths.asset("events/poker_night/background.png")),
    night.CAREER_ACTIVITY_CASINO_NIGHT: str(paths.asset("events/casino_night/background.png")),
    night.CAREER_ACTIVITY_NICHE_NIGHT: str(paths.asset("events/niche_night/background.png")),
    night.CAREER_ACTIVITY_ARCADE_NIGHT: str(paths.asset("arcade/ui/background.png")),
}

EVENT_BUTTON_ASSET_PATHS = {
    night.CAREER_ACTIVITY_CASUAL_CARDS: {
        "return": str(paths.asset("events/casual_cards/return.png")),
        "end": str(paths.asset("events/casual_cards/end_night.png")),
    },
    night.CAREER_ACTIVITY_POKER_NIGHT: {
        "return": str(paths.asset("events/poker_night/return.png")),
        "end": str(paths.asset("events/poker_night/end_night.png")),
    },
    night.CAREER_ACTIVITY_CASINO_NIGHT: {
        "return": str(paths.asset("events/casino_night/return.png")),
        "end": str(paths.asset("events/casino_night/end_night.png")),
    },
    night.CAREER_ACTIVITY_NICHE_NIGHT: {
        "return": str(paths.asset("events/niche_night/return.png")),
        "end": str(paths.asset("events/niche_night/end_night.png")),
    },
}


def draw_event_image_button(rect, activity_type, button_kind, fallback_text, enabled=True):
    path = EVENT_BUTTON_ASSET_PATHS.get(activity_type, {}).get(button_kind)
    image = legacy.get_event_ui_asset(path, rect.size)
    hovered = (
        enabled
        and state.game_mouse_pos is not None
        and rect.collidepoint(state.game_mouse_pos)
    )

    if image is None:
        buttons.draw_menu_button(
            rect,
            fallback_text,
            state.game_mouse_pos,
            font=fonts.difficulty_detail_font
        )
        if not enabled:
            overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 125))
            window.game_surface.blit(overlay, rect.topleft)
        return

    button = image.copy()
    if hovered:
        button.fill((22, 22, 22, 0), special_flags=pygame.BLEND_RGBA_ADD)
    if not enabled:
        button.fill((110, 110, 110, 255), special_flags=pygame.BLEND_RGBA_MULT)
        button.set_alpha(150)
    window.game_surface.blit(button, rect.topleft)


def get_event_selection_image(game_id, size=None):
    path = EVENT_SELECTION_IMAGE_PATHS.get(game_id)
    if not path:
        return None

    requested_size = tuple(size or EVENT_SELECTION_IMAGE_SIZE)
    cache_key = (game_id, requested_size)
    if cache_key in _event_selection_image_cache:
        return _event_selection_image_cache[cache_key]

    try:
        image = pygame.image.load(path).convert_alpha()
        image = pygame.transform.smoothscale(image, requested_size)
        _event_selection_image_cache[cache_key] = image
        return image
    except (pygame.error, FileNotFoundError):
        return None


def get_poker_night_selection_image(game_id, size=None):
    path = POKER_NIGHT_SELECTION_IMAGE_PATHS.get(game_id)

    if not path:
        return None

    requested_size = tuple(size or POKER_NIGHT_SELECTION_IMAGE_SIZE)
    cache_key = (game_id, requested_size)

    if cache_key in _poker_night_selection_image_cache:
        return _poker_night_selection_image_cache[cache_key]

    try:
        image = pygame.image.load(path).convert_alpha()
        image = pygame.transform.smoothscale(image, requested_size)
        _poker_night_selection_image_cache[cache_key] = image
        return image

    except (pygame.error, FileNotFoundError):
        return None


def get_career_event_card_layout(activity_type, game_count):
    if activity_type == night.CAREER_ACTIVITY_ARCADE_NIGHT or game_count >= 5:
        return 232, 312, 14, 184
    if game_count == 4:
        return 246, 320, 18, 180
    return 300, 330, 30, 178


def draw_poker_night_high_stakes_label(
        surface,
        center
):
    label = "HIGH STAKES"

    # Several soft offset passes make the gold lettering glow
    # without requiring a separate asset.
    for offset_x, offset_y, alpha in (
            (-3, 0, 60),
            (3, 0, 60),
            (0, -3, 60),
            (0, 3, 60),
            (-2, -2, 50),
            (2, -2, 50),
            (-2, 2, 50),
            (2, 2, 50),
    ):
        glow = fonts.difficulty_detail_font.render(
            label,
            True,
            (
                255,
                185,
                45
            )
        )
        glow.set_alpha(
            alpha
        )
        glow_rect = glow.get_rect(
            center=(
                center[0] + offset_x,
                center[1] + offset_y
            )
        )
        surface.blit(
            glow,
            glow_rect
        )

    text_surface = fonts.difficulty_detail_font.render(
        label,
        True,
        (
            255,
            230,
            95
        )
    )

    text_rect = text_surface.get_rect(
        center=center
    )

    surface.blit(
        text_surface,
        text_rect
    )


def draw_arcade_night_select():
    background = legacy.get_event_ui_asset(str(paths.asset("arcade/ui/background.png")), (BASE_WIDTH, BASE_HEIGHT))
    if background is not None:
        window.game_surface.blit(background, (0, 0))
    else:
        window.game_surface.fill((13, 18, 28))

    shade = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
    shade.fill((0, 0, 0, 42))
    window.game_surface.blit(shade, (0, 0))

    title_asset = legacy.get_event_ui_asset(str(paths.asset("arcade/ui/title.png")), (350, 84))
    if title_asset is not None:
        window.game_surface.blit(
            title_asset,
            title_asset.get_rect(center=(BASE_WIDTH // 2, 47)),
        )
    else:
        title = fonts.options_title_font.render("ARCADE NIGHT", True, (255, 255, 255))
        window.game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 48)))

    subtitle = fonts.difficulty_detail_font.render(
        "Choose a machine, buy tokens, and turn your wins into tickets.",
        True,
        (221, 226, 232),
    )
    window.game_surface.blit(subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 92)))

    # Optional cabinet soundtrack toggle.  Machine music is intentionally OFF
    # on every fresh launch because the temporary tracks can compete with the
    # machine SFX.  The normal Instrumental/Ambient soundtrack is unaffected.
    music_toggle_hovered = (
        state.game_mouse_pos is not None
        and arcade_placeholder_music_toggle_rect.collidepoint(state.game_mouse_pos)
    )
    toggle_panel = pygame.Surface(
        arcade_placeholder_music_toggle_rect.size,
        pygame.SRCALPHA,
    )
    toggle_panel.fill((8, 14, 24, 232 if music_toggle_hovered else 214))
    window.game_surface.blit(toggle_panel, arcade_placeholder_music_toggle_rect.topleft)
    toggle_border = (
        (247, 213, 115)
        if state.arcade_placeholder_music_enabled
        else ((130, 194, 218) if music_toggle_hovered else (111, 126, 145))
    )
    pygame.draw.rect(
        window.game_surface,
        toggle_border,
        arcade_placeholder_music_toggle_rect,
        2,
        border_radius=8,
    )
    toggle_text = ui_text.render_text_fit(
        f"Placeholder Music: {'On' if state.arcade_placeholder_music_enabled else 'Off'}",
        fonts.difficulty_detail_font,
        arcade_placeholder_music_toggle_rect.width - 18,
        color=(255, 235, 145) if state.arcade_placeholder_music_enabled else (218, 225, 232),
        minimum_size=14,
    )
    window.game_surface.blit(
        toggle_text,
        toggle_text.get_rect(center=arcade_placeholder_music_toggle_rect.center),
    )

    counter_data = (
        ("CASH", f"${state.career_cash:,}"),
        ("TOKENS", f"{int(state.arcade_state.get('tokens', 0)):,}"),
        ("TICKETS", f"{int(state.arcade_state.get('tickets', 0)):,}"),
    )
    counter_width = 220
    counter_gap = 22
    total_counter_width = counter_width * 3 + counter_gap * 2
    counter_x = (BASE_WIDTH - total_counter_width) // 2
    for index, (label, value) in enumerate(counter_data):
        rect = pygame.Rect(counter_x + index * (counter_width + counter_gap), 112, counter_width, 54)
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((7, 14, 24, 222))
        window.game_surface.blit(panel, rect.topleft)
        pygame.draw.rect(window.game_surface, (92, 184, 218), rect, 2, border_radius=9)
        label_surface = fonts.difficulty_detail_font.render(label, True, (179, 191, 203))
        value_surface = fonts.option_label_font.render(value, True, (255, 237, 151))
        window.game_surface.blit(label_surface, label_surface.get_rect(midleft=(rect.x + 14, rect.centery)))
        window.game_surface.blit(value_surface, value_surface.get_rect(midright=(rect.right - 14, rect.centery)))

    machine_ids = [
        game_id
        for game_id in state.career_event_entry.get("game_ids", [])
        if game_id != "prize_counter"
    ]
    machine_names = {
        "king_pong": "King Pong",
        "battle_bosses": "Battle Bosses",
        "ace_invaders": "Ace Invaders",
        "suit_snake": "Suit Snake",
    }
    descriptions = {
        "king_pong": ("Classic Pong.", "First to five wins."),
        "battle_bosses": ("Deflect a projectile", "and break the rival strongholds."),
        "ace_invaders": ("Defeat waves of incoming", "Ace suits before they reach you."),
        "suit_snake": ("Build a card-chain snake", "through the deck in sequence."),
    }

    card_width = 276
    card_height = 326
    card_gap = 18
    card_y = 188
    total_width = card_width * len(machine_ids) + card_gap * max(0, len(machine_ids) - 1)
    start_x = (BASE_WIDTH - total_width) // 2

    for index, game_id in enumerate(machine_ids):
        rect = pygame.Rect(start_x + index * (card_width + card_gap), card_y, card_width, card_height)
        unlocked = legacy.is_game_unlocked(game_id)
        coming_soon = game_id in ARCADE_COMING_SOON_GAME_IDS
        hovered = (
            unlocked
            and not coming_soon
            and state.game_mouse_pos is not None
            and rect.collidepoint(state.game_mouse_pos)
        )

        fill = (22, 31, 44, 238) if not hovered else (31, 57, 68, 242)
        card_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        card_surface.fill(fill)
        window.game_surface.blit(card_surface, rect.topleft)
        border = (247, 213, 115) if hovered else (198, 207, 219)
        pygame.draw.rect(window.game_surface, border, rect, 3 if hovered else 2, border_radius=12)

        image_rect = pygame.Rect(rect.x + 8, rect.y + 8, rect.width - 16, 146)
        image = get_event_selection_image(game_id, image_rect.size)
        if image is not None:
            window.game_surface.blit(image, image_rect)
        else:
            pygame.draw.rect(window.game_surface, (7, 10, 16), image_rect, border_radius=7)
            placeholder = fonts.difficulty_detail_font.render("SELECT ART", True, (114, 123, 136))
            window.game_surface.blit(placeholder, placeholder.get_rect(center=image_rect.center))

        if coming_soon or not unlocked:
            overlay = pygame.Surface(image_rect.size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 145))
            window.game_surface.blit(overlay, image_rect.topleft)
            if coming_soon:
                state_text = "COMING SOON"
            else:
                state_text = f"LOCKED — LEVEL {get_game_unlock_level(game_id)}"
            state_surface = fonts.option_label_font.render(state_text, True, (245, 245, 245))
            window.game_surface.blit(state_surface, state_surface.get_rect(center=image_rect.center))

        name = fonts.option_label_font.render(machine_names.get(game_id, game_id.replace("_", " ").title()), True, (248, 249, 250))
        window.game_surface.blit(name, name.get_rect(center=(rect.centerx, rect.y + 181)))

        for line_index, line in enumerate(descriptions.get(game_id, ("Arcade machine.", ""))):
            line_surface = fonts.difficulty_detail_font.render(line, True, (204, 212, 221))
            window.game_surface.blit(line_surface, line_surface.get_rect(center=(rect.centerx, rect.y + 220 + line_index * 25)))

        token_cost = get_machine_cost(game_id)
        cost_text = "COMING SOON" if coming_soon else f"{token_cost} TOKEN{'S' if token_cost != 1 else ''} PER PLAY"
        cost_color = (155, 163, 176) if coming_soon else (255, 235, 145)
        cost_surface = fonts.difficulty_detail_font.render(cost_text, True, cost_color)
        window.game_surface.blit(cost_surface, cost_surface.get_rect(center=(rect.centerx, rect.bottom - 28)))

        career_event_card_rects.append((rect, game_id))

    # Arcade Night action controls are all authored PNG buttons. The loader
    # preserves aspect ratio with a center crop and falls back to the generic
    # renderer until the corresponding artwork exists.
    legacy.draw_arcade_action_image_button(
        arcade_machine_buy_tokens_rect,
        "buy_tokens",
        "Buy Tokens",
        enabled=True,
    )
    legacy.draw_arcade_action_image_button(
        arcade_machine_prize_counter_rect,
        "prize_counter",
        "Prize Counter",
        enabled=True,
    )

    career_event_card_rects.append((arcade_machine_buy_tokens_rect, "token_exchange"))
    career_event_card_rects.append((arcade_machine_prize_counter_rect, "prize_counter"))

    legacy.draw_arcade_action_image_button(
        career_event_return_rect,
        "return",
        "Return",
        enabled=True,
    )
    legacy.draw_arcade_action_image_button(
        career_event_end_rect,
        "end",
        "End Arcade Night",
        enabled=state.career_event_has_activity,
    )

    if not state.career_event_has_activity and state.game_mouse_pos is not None and career_event_end_rect.collidepoint(state.game_mouse_pos):
        tooltip_surface = fonts.difficulty_detail_font.render(
            "Play at least one arcade game before ending the night.",
            True,
            (245, 245, 245),
        )
        tooltip_rect = tooltip_surface.get_rect(
            midbottom=(career_event_end_rect.centerx, career_event_end_rect.y - 8)
        ).inflate(20, 12)
        panel = pygame.Surface(tooltip_rect.size, pygame.SRCALPHA)
        panel.fill((8, 14, 23, 235))
        window.game_surface.blit(panel, tooltip_rect.topleft)
        pygame.draw.rect(window.game_surface, (228, 198, 108), tooltip_rect, 2, border_radius=8)
        window.game_surface.blit(tooltip_surface, tooltip_surface.get_rect(center=tooltip_rect.center))

    if state.arcade_status_message and pygame.time.get_ticks() <= state.arcade_status_message_expires:
        message_surface = fonts.difficulty_detail_font.render(state.arcade_status_message, True, (251, 244, 217))
        backdrop = message_surface.get_rect(center=(BASE_WIDTH // 2, 540)).inflate(24, 12)
        pane = pygame.Surface(backdrop.size, pygame.SRCALPHA)
        pane.fill((8, 14, 24, 230))
        window.game_surface.blit(pane, backdrop.topleft)
        pygame.draw.rect(window.game_surface, (226, 194, 104), backdrop, 2, border_radius=8)
        window.game_surface.blit(message_surface, message_surface.get_rect(center=backdrop.center))


def _draw_career_event_select():
    window.game_surface.fill((20, 28, 35))
    career_event_card_rects.clear()

    if state.career_event_entry is None:
        return

    activity_type = state.career_event_entry.get("activity_type")
    if activity_type == night.CAREER_ACTIVITY_ARCADE_NIGHT:
        draw_arcade_night_select()
        return

    is_poker_night = activity_type == night.CAREER_ACTIVITY_POKER_NIGHT
    is_arcade_night = activity_type == night.CAREER_ACTIVITY_ARCADE_NIGHT
    event_title = night.CAREER_EVENT_NAMES.get(activity_type, "Card Event")

    background_path = EVENT_BACKGROUND_ASSET_PATHS.get(activity_type)
    background = legacy.get_event_ui_asset(background_path, (BASE_WIDTH, BASE_HEIGHT))
    if background is not None:
        window.game_surface.blit(background, (0, 0))
        shade = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 45))
        window.game_surface.blit(shade, (0, 0))

    title_asset = legacy.get_event_ui_asset(EVENT_TITLE_ASSET_PATHS.get(activity_type), (360, 96))
    if title_asset is not None:
        window.game_surface.blit(title_asset, title_asset.get_rect(center=(BASE_WIDTH // 2, 66)))
    else:
        title_surface = fonts.options_title_font.render(event_title, True, (255, 255, 255))
        window.game_surface.blit(title_surface, title_surface.get_rect(center=(BASE_WIDTH // 2, 78)))

    subtitle_text = "Choose your machine" if is_arcade_night else ("Choose your table" if is_poker_night else "Choose a game")
    subtitle_surface = fonts.difficulty_detail_font.render(subtitle_text, True, (230, 230, 230))
    subtitle_y = 126
    window.game_surface.blit(subtitle_surface, subtitle_surface.get_rect(center=(BASE_WIDTH // 2, subtitle_y)))

    if is_arcade_night:
        counters = (
            ("Cash", f"${state.career_cash:,}"),
            ("Tokens", f"{int(state.arcade_state.get('tokens', 0)):,}"),
            ("Tickets", f"{int(state.arcade_state.get('tickets', 0)):,}"),
        )
        for index, (label, value) in enumerate(counters):
            rect = pygame.Rect(392 + index * 198, 144, 182, 44)
            pygame.draw.rect(window.game_surface, (12, 20, 30), rect, border_radius=10)
            pygame.draw.rect(window.game_surface, (226, 195, 104), rect, 2, border_radius=10)
            label_surface = fonts.difficulty_detail_font.render(label, True, (212, 219, 225))
            value_surface = fonts.difficulty_detail_font.render(value, True, (255, 237, 156))
            window.game_surface.blit(label_surface, label_surface.get_rect(midleft=(rect.x + 14, rect.centery)))
            window.game_surface.blit(value_surface, value_surface.get_rect(midright=(rect.right - 14, rect.centery)))

    game_ids = state.career_event_entry.get("game_ids", [])
    uses_image_cards = activity_type in (
        night.CAREER_ACTIVITY_CASUAL_CARDS,
        night.CAREER_ACTIVITY_POKER_NIGHT,
        night.CAREER_ACTIVITY_CASINO_NIGHT,
        night.CAREER_ACTIVITY_NICHE_NIGHT,
        night.CAREER_ACTIVITY_ARCADE_NIGHT,
    )

    if uses_image_cards:
        card_width, card_height, card_gap, card_y = get_career_event_card_layout(activity_type, len(game_ids))
    else:
        card_width, card_height, card_gap, card_y = 270, 250, 35, 220

    total_width = card_width * len(game_ids) + card_gap * max(0, len(game_ids) - 1)
    start_x = BASE_WIDTH // 2 - total_width // 2

    game_names = {
        "score_four": "Score-Four",
        "bango": "Bango",
        "crazy_eights": "Crazy Eights",
        "texas_holdem": "Texas Hold'em",
        "seven_card_stud": "Seven-Card Stud",
        "five_card_draw": "Five-Card Draw",
        "blackjack": "Blackjack",
        "roulette": "Roulette",
        "horse_races": "Horse Races",
        "faro": "Faro",
        "five_o_poker": "Five-O Poker",
        "blind_mans_bluff": "Blind Man's Bluff",
        **ARCADE_MACHINE_NAMES,
    }

    poker_descriptions = {
        "texas_holdem": ("Community cards, blinds,", "and no-limit betting."),
        "seven_card_stud": ("Seven cards, exposed streets,", "and fixed-limit betting."),
        "five_card_draw": ("Classic draw poker with", "one discard-and-draw round."),
    }

    event_descriptions = {
        "score_four": ("Use all four numbers", "to make exactly 24."),
        "crazy_eights": ("Match suit or rank;", "eights are wild."),
        "bango": ("Cover all five cards", "before anyone else."),
        "blackjack": ("Beat the dealer", "without going over 21."),
        "roulette": ("Place your chips", "and spin the wheel."),
        "horse_races": ("Back a horse to Win,", "Place, or Show."),
        "faro": ("Back ranks against", "the banker deck."),
        "five_o_poker": ("Build five poker hands", "at the same time."),
        "blind_mans_bluff": ("See every card", "except your own."),
        "king_pong": ("Arcade paddle duel", "for tickets and bragging rights."),
        "battle_bosses": ("Card battlers and", "boss fights are on deck."),
        "ace_invaders": ("A retro shooter with", "card-flavored waves."),
        "suit_snake": ("Chase a longer chain", "of hearts, clubs, and spades."),
        "prize_counter": ("Redeem tickets and", "check your trophy shelf."),
    }

    for index, game_id in enumerate(game_ids):
        rect = pygame.Rect(start_x + index * (card_width + card_gap), card_y, card_width, card_height)
        unlocked = legacy.is_game_unlocked(game_id)
        coming_soon = is_arcade_night and game_id in ARCADE_COMING_SOON_GAME_IDS
        clickable = unlocked and not coming_soon
        hovered = clickable and state.game_mouse_pos is not None and rect.collidepoint(state.game_mouse_pos)

        if not unlocked:
            fill_color, border_color, border_width = (55, 55, 58), (125, 125, 130), 3
        elif coming_soon:
            fill_color, border_color, border_width = (48, 53, 70), (158, 166, 188), 3
        elif hovered:
            fill_color, border_color, border_width = (48, 112, 66), (255, 225, 120), 5
        else:
            fill_color, border_color, border_width = (38, 92, 53), (235, 235, 235), 3

        pygame.draw.rect(window.game_surface, fill_color, rect, border_radius=10)
        pygame.draw.rect(window.game_surface, border_color, rect, border_width, border_radius=10)

        game_name = game_names.get(game_id, game_id.replace("_", " ").title())
        is_high_stakes = is_poker_night and game_id == state.career_event_entry.get("high_stakes_game_id")

        image_width = max(120, card_width - 12)
        image_height = max(90, int(round(image_width * 9 / 16)))
        image_rect = pygame.Rect(rect.x + (card_width - image_width) // 2, rect.y + 17, image_width, image_height)
        image = get_poker_night_selection_image(game_id, image_rect.size) if is_poker_night else get_event_selection_image(game_id, image_rect.size)

        if image is not None:
            window.game_surface.blit(image, image_rect)
        else:
            pygame.draw.rect(window.game_surface, (24, 28, 31), image_rect, border_radius=6)
            pygame.draw.rect(window.game_surface, (115, 125, 130), image_rect, 2, border_radius=6)
            missing_name = fonts.option_label_font.render(game_name, True, (220, 222, 224))
            missing_note = fonts.difficulty_detail_font.render("EVENT ART", True, (150, 155, 160))
            window.game_surface.blit(missing_name, missing_name.get_rect(center=(image_rect.centerx, image_rect.centery - 12)))
            window.game_surface.blit(missing_note, missing_note.get_rect(center=(image_rect.centerx, image_rect.centery + 18)))

        if not unlocked or coming_soon:
            overlay = pygame.Surface(image_rect.size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 145 if not unlocked else 120))
            window.game_surface.blit(overlay, image_rect.topleft)
            if not unlocked:
                required_level = get_game_unlock_level(game_id)
                text_line = f"LOCKED - LEVEL {required_level}"
            else:
                text_line = "COMING SOON"
            lock_surface = fonts.difficulty_detail_font.render(text_line, True, (240, 240, 240))
            window.game_surface.blit(lock_surface, lock_surface.get_rect(center=image_rect.center))

        description_lines = poker_descriptions.get(game_id, ("Poker Night game.", "")) if is_poker_night else event_descriptions.get(game_id, ("Card game.", ""))
        description_y = image_rect.bottom + 18
        if is_high_stakes:
            draw_poker_night_high_stakes_label(window.game_surface, (rect.centerx, image_rect.bottom + 8))
            description_y += 18

        for line_index, line in enumerate(description_lines):
            if not line:
                continue
            line_surface = fonts.difficulty_detail_font.render(line, True, (220, 223, 225))
            window.game_surface.blit(line_surface, line_surface.get_rect(center=(rect.centerx, description_y + line_index * 25)))

        career_event_card_rects.append((rect, game_id))

    draw_event_image_button(career_event_return_rect, activity_type, "return", "Return", enabled=True)

    if state.career_event_entry is not None:
        event_name = night.CAREER_EVENT_NAMES.get(activity_type, "Event")
        draw_event_image_button(career_event_end_rect, activity_type, "end", f"End {event_name}", enabled=state.career_event_has_activity)

    if (not state.career_event_has_activity and state.game_mouse_pos is not None and career_event_end_rect.collidepoint(state.game_mouse_pos)):
        tooltip_text = "Play at least one game before ending the event."
        tooltip_surface = fonts.difficulty_detail_font.render(tooltip_text, True, (245, 245, 245))
        tooltip_rect = tooltip_surface.get_rect(midbottom=(career_event_end_rect.centerx, career_event_end_rect.y - 10)).inflate(22, 14)
        panel = pygame.Surface(tooltip_rect.size, pygame.SRCALPHA)
        panel.fill((12, 18, 16, 235))
        window.game_surface.blit(panel, tooltip_rect.topleft)
        pygame.draw.rect(window.game_surface, (228, 200, 115), tooltip_rect, 2, border_radius=7)
        window.game_surface.blit(tooltip_surface, tooltip_surface.get_rect(center=tooltip_rect.center))

    if is_arcade_night and state.arcade_status_message and pygame.time.get_ticks() <= state.arcade_status_message_expires:
        message_surface = fonts.difficulty_detail_font.render(state.arcade_status_message, True, (251, 244, 217))
        backdrop = message_surface.get_rect(center=(BASE_WIDTH // 2, 714)).inflate(28, 16)
        pane = pygame.Surface(backdrop.size, pygame.SRCALPHA)
        pane.fill((14, 19, 32, 228))
        window.game_surface.blit(pane, backdrop.topleft)
        pygame.draw.rect(window.game_surface, (226, 194, 104), backdrop, 2, border_radius=9)
        window.game_surface.blit(message_surface, message_surface.get_rect(center=backdrop.center))


def draw_career_event_select():
    _draw_career_event_select()
    if not state.career_event_entry:
        return
    if state.career_event_entry.get("activity_type") == night.CAREER_ACTIVITY_ARCADE_NIGHT:
        return
    from solitaireplus.career.ratings import GAME_CATEGORIES
    games = state.career_event_entry.get("game_ids", [])
    count = len(games)
    if not count:
        return
    width, _height, gap, card_y = get_career_event_card_layout(state.career_event_entry.get("activity_type"), count)
    start = (BASE_WIDTH - (width * count + gap * (count - 1))) // 2
    label_y = max(150, card_y - 14)
    tag_font = ui_text.get_font(None, 24)
    for index, key in enumerate(games):
        category = GAME_CATEGORIES.get(key)
        if state.career_event_entry.get("activity_type") == night.CAREER_ACTIVITY_ARCADE_NIGHT and key == "prize_counter":
            label = "ARCADE SERVICE"
            color = (225, 225, 225)
        else:
            label = ("RATED • " + category.upper()) if category else "UNRATED"
            color = (255, 239, 165) if category else (225, 225, 225)
        text = tag_font.render(label, True, color)
        rect = text.get_rect(center=(start + index * (width + gap) + width // 2, label_y))
        pygame.draw.rect(window.game_surface, (10, 18, 25), rect.inflate(20, 6), border_radius=7)
        window.game_surface.blit(text, rect)


def handle_event(event):
    """Old main-loop event branch for STATE_CAREER_EVENT_SELECT."""

    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.menu_mouse_pos is not None
    ):

        game_clicked = False

        is_arcade_night_select = (
            state.career_event_entry is not None
            and state.career_event_entry.get("activity_type") == night.CAREER_ACTIVITY_ARCADE_NIGHT
        )
        if (
                is_arcade_night_select
                and arcade_placeholder_music_toggle_rect.collidepoint(state.menu_mouse_pos)
        ):
            state.arcade_placeholder_music_enabled = not state.arcade_placeholder_music_enabled
            sounds.audio.play_sound("button_click")
            game_clicked = True
            legacy.set_arcade_status_message(
                "Placeholder arcade music enabled."
                if state.arcade_placeholder_music_enabled
                else "Placeholder arcade music disabled."
            )

        for (state.rect, game_id) in career_event_card_rects:

            if not game_clicked and state.rect.collidepoint(state.menu_mouse_pos):
                game_clicked = True

                if not legacy.is_game_unlocked(game_id):
                    break

                if (
                        state.career_event_entry is not None
                        and state.career_event_entry.get("activity_type") == night.CAREER_ACTIVITY_ARCADE_NIGHT
                        and game_id in ARCADE_COMING_SOON_GAME_IDS
                ):
                    sounds.audio.play_sound("button_click")
                    legacy.set_arcade_status_message(f"{ARCADE_MACHINE_NAMES.get(game_id, game_id)} is coming soon.")
                    break

                sounds.audio.play_sound("button_click")

                if game_id == "score_four":
                    state.current_state = state_names.STATE_SCORE_FOUR_MODE_SELECT

                elif game_id == "crazy_eights":
                    legacy.start_crazy_eights_session()

                elif game_id == "bango":
                    legacy.start_bango_session()

                elif game_id == "blackjack":
                    state.blackjack_selected_bet_percentage = None
                    state.blackjack_bet_dropdown_open = False
                    state.blackjack_session_net = 0
                    state.blackjack_session_rating_change = 0
                    state.blackjack_dealer_npc = get_random_blackjack_dealer()
                    state.current_state = state_names.STATE_BLACKJACK_BET

                elif game_id == "roulette":
                    state.roulette_session_net = 0
                    legacy.roulette_game.reset_round()
                    state.current_state = state_names.STATE_ROULETTE

                elif game_id == "horse_races":
                    legacy.start_horse_races_session()

                elif game_id == "faro":
                    legacy.start_faro_session()

                elif game_id == "five_o_poker":
                    if not legacy.start_five_o_poker_session():
                        print("Not enough cash to enter Five-O Poker.")

                elif game_id == "blind_mans_bluff":
                    if not legacy.start_blind_mans_bluff_session():
                        print("Not enough cash to enter Blind Man's Bluff.")

                elif game_id == "texas_holdem":
                    state.current_state = state_names.STATE_TEXAS_HOLDEM_BUY_IN

                elif game_id == "seven_card_stud":
                    state.current_state = state_names.STATE_SEVEN_CARD_STUD_BUY_IN

                elif game_id == "five_card_draw":
                    state.current_state = state_names.STATE_FIVE_CARD_DRAW_BUY_IN

                elif game_id == "king_pong":
                    legacy.open_king_pong_opponent_select(refresh=True)

                elif game_id == "battle_bosses":
                    legacy.open_battle_bosses_opponent_select(refresh=True)

                elif game_id == "ace_invaders":
                    legacy.open_ace_invaders_difficulty_select(reset_selection=True)

                elif game_id == "suit_snake":
                    legacy.open_suit_snake_difficulty_select(reset_selection=True)

                elif game_id == "token_exchange":
                    legacy.open_arcade_token_exchange()

                elif game_id == "prize_counter":
                    state.arcade_selected_prize_index = 0
                    state.arcade_prize_page = 0
                    state.current_state = state_names.STATE_ARCADE_PRIZE_COUNTER

                else:
                    print("Career game not implemented yet:", game_id)

                break

        if not game_clicked:

            if career_event_return_rect.collidepoint(state.menu_mouse_pos):
                sounds.audio.play_sound("button_click")
                store_event_progress(state.career_event_entry, legacy.game_namespace())
                career_saving.auto_save_career()
                state.current_state = state_names.STATE_CAREER_HUB

            elif (
                    career_event_end_rect.collidepoint(state.menu_mouse_pos)
                    and state.career_event_has_activity
            ):
                sounds.audio.play_sound("button_click")
                publish_career_event_news()
                night.build_career_event_summary()
                state.current_state = state_names.STATE_CAREER_EVENT_SUMMARY


def draw():
    """Old draw-chain branch for STATE_CAREER_EVENT_SELECT."""

    draw_career_event_select()
