from career_session_summary import poker_session_status
import math

import pygame

from poker_speech import PokerSpeechOverlay, is_poker_chat_popups_enabled
from poker_ui_assets import draw_poker_logo


# ==================================================
# ACTIONS
# ==================================================

ACTION_RETURN = "return"
ACTION_FOLD = "fold"
ACTION_CHECK_CALL = "check_call"
ACTION_BET_RAISE = "bet_raise"
ACTION_DRAW = "draw"
ACTION_NEXT_HAND = "next_hand"
ACTION_OPTIONS = "options"


# ==================================================
# COLORS
# ==================================================

WHITE = (245, 245, 245)
MUTED = (185, 190, 190)
GOLD = (235, 190, 70)
TABLE_GREEN = (30, 105, 55)
TABLE_EDGE = (95, 65, 35)
PANEL_DARK = (18, 20, 24)
PANEL_INNER = (10, 12, 14)


# ==================================================
# LAYOUT
# ==================================================

DRAW_LOG_RECT = pygame.Rect(18, 610, 410, 140)
DRAW_ACTION_PANEL_RECT = pygame.Rect(925, 610, 420, 140)

DRAW_FOLD_RECT = pygame.Rect(942, 622, 112, 40)
DRAW_CALL_RECT = pygame.Rect(1064, 622, 132, 40)
DRAW_RAISE_RECT = pygame.Rect(1206, 622, 122, 40)

DRAW_MIN_RECT = pygame.Rect(942, 708, 68, 28)
DRAW_HALF_RECT = pygame.Rect(1018, 708, 68, 28)
DRAW_POT_RECT = pygame.Rect(1094, 708, 68, 28)
DRAW_MAX_RECT = pygame.Rect(1170, 708, 68, 28)

DRAW_CONFIRM_RECT = pygame.Rect(1006, 668, 220, 48)
DRAW_CLEAR_RECT = pygame.Rect(1238, 668, 92, 48)
DRAW_NEXT_HAND_RECT = pygame.Rect(1018, 650, 250, 48)
DRAW_OPTIONS_RECT = pygame.Rect(1180, 20, 90, 38)
DRAW_EXIT_RECT = pygame.Rect(1280, 20, 68, 38)

DRAW_SLIDER_RECT = pygame.Rect(942, 683, 245, 14)
DRAW_MANUAL_BET_RECT = pygame.Rect(1202, 674, 126, 30)

DRAW_BUY_IN_PANEL_RECT = pygame.Rect(283, 180, 800, 410)
DRAW_BUY_IN_25_RECT = pygame.Rect(318, 330, 165, 100)
DRAW_BUY_IN_50_RECT = pygame.Rect(506, 330, 165, 100)
DRAW_BUY_IN_75_RECT = pygame.Rect(694, 330, 165, 100)
DRAW_BUY_IN_MAX_RECT = pygame.Rect(882, 330, 165, 100)
DRAW_BUY_IN_BACK_RECT = pygame.Rect(558, 505, 250, 44)

TABLE_RECT = pygame.Rect(233, 105, 900, 460)
INNER_TABLE_RECT = TABLE_RECT.inflate(-30, -30)

PLAYER_CARD_WIDTH = 82
PLAYER_CARD_HEIGHT = 114
PLAYER_CARD_GAP = 4
PLAYER_CARD_Y = 535
PLAYER_CARD_SELECTED_LIFT = 20


# ==================================================
# UI STATE
# ==================================================

_draw_fonts = None
_draw_chip_images = None
_draw_selected_card_indexes = set()
_draw_bet_fraction = 0.50
_draw_bet_slider_dragging = False
_draw_manual_bet_text = ""
_draw_manual_bet_active = False
_draw_chat_history = []
_draw_speech_overlay = PokerSpeechOverlay()
_draw_active_tab = "log"
_draw_log_scroll = 0
_draw_chat_scroll = 0
_draw_chat_unread = False
_draw_last_hand_number = -1


# ==================================================
# FONTS / BASIC DRAWING
# ==================================================

def get_draw_fonts():
    global _draw_fonts

    if _draw_fonts is None:
        if not pygame.font.get_init():
            pygame.font.init()

        _draw_fonts = {
            "title": pygame.font.SysFont("cambria", 31, bold=True),
            "name": pygame.font.SysFont("cambria", 20, bold=True),
            "small": pygame.font.SysFont("cambria", 17, bold=True),
            "tiny": pygame.font.SysFont("cambria", 15, bold=True),
            "micro": pygame.font.SysFont("cambria", 12, bold=True),
        }

    return _draw_fonts


def draw_panel(
        surface,
        rect,
        fill=(18, 20, 24, 235),
        border=(145, 150, 155),
        radius=10,
        border_width=2
):
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)

    pygame.draw.rect(
        panel,
        fill,
        panel.get_rect(),
        border_radius=radius
    )

    # Draw the soft upper highlight on a separate alpha layer.
    # Drawing a low-alpha rectangle directly onto an SRCALPHA surface
    # replaces those pixels instead of blending them, which made large
    # panels look transparent on top and nearly black on the bottom.
    gloss_layer = pygame.Surface(
        rect.size,
        pygame.SRCALPHA
    )

    gloss_rect = pygame.Rect(
        3,
        3,
        max(1, rect.width - 6),
        max(8, rect.height // 2 - 3)
    )

    pygame.draw.rect(
        gloss_layer,
        (255, 255, 255, 18),
        gloss_rect,
        border_radius=max(4, radius - 2)
    )

    panel.blit(
        gloss_layer,
        (0, 0)
    )

    pygame.draw.rect(
        panel,
        (*border, 245),
        panel.get_rect(),
        border_width,
        border_radius=radius
    )

    surface.blit(panel, rect.topleft)


def render_text_fit(text, font, color, max_width, minimum_size=10):
    text = str(text)
    rendered = font.render(text, True, color)

    if rendered.get_width() <= max_width:
        return rendered

    font_name = "cambria"
    current_size = max(minimum_size, font.get_height() - 2)

    while current_size >= minimum_size:
        smaller = pygame.font.SysFont(font_name, current_size, bold=True)
        rendered = smaller.render(text, True, color)

        if rendered.get_width() <= max_width:
            return rendered

        current_size -= 1

    return rendered


def draw_button(
        surface,
        rect,
        text,
        mouse_pos,
        font,
        enabled=True,
        selected=False,
        attention=False
):
    hovered = enabled and mouse_pos is not None and rect.collidepoint(mouse_pos)

    if not enabled:
        base = (62, 62, 66)
        border = (110, 110, 116)
        color = (150, 150, 155)
    elif selected:
        base = (72, 102, 132)
        border = (180, 220, 255)
        color = WHITE
    elif attention:
        phase = (pygame.time.get_ticks() % 1200) / 1200.0
        pulse = 0.5 + 0.5 * math.sin(phase * math.pi * 2)
        base = (int(105 + 35 * pulse), int(82 + 28 * pulse), int(32 + 12 * pulse))
        border = (255, int(195 + 45 * pulse), 80)
        color = WHITE
    elif hovered:
        base = (80, 88, 96)
        border = (185, 190, 195)
        color = WHITE
    else:
        base = (58, 62, 68)
        border = (145, 150, 155)
        color = (238, 238, 238)

    button = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(button, (*base, 215), button.get_rect(), border_radius=12)
    gloss = pygame.Rect(3, 3, rect.width - 6, max(8, rect.height // 2 - 3))
    pygame.draw.rect(button, (255, 255, 255, 28), gloss, border_radius=10)
    pygame.draw.rect(button, border, button.get_rect(), 2, border_radius=12)
    surface.blit(button, rect.topleft)

    label = render_text_fit(text, font, color, rect.width - 12, minimum_size=10)
    surface.blit(label, label.get_rect(center=rect.center))

# ==================================================


# ==================================================

def get_card_key(card):
    if not card:
        return None

    suit_letter = {
        "Clubs": "C",
        "Diamonds": "D",
        "Hearts": "H",
        "Spades": "S",
    }.get(card.get("suit"))

    if suit_letter is None:
        return None

    return f"{card.get('rank')}{suit_letter}"


def draw_card_face(
        surface,
        card,
        x,
        y,
        card_fronts,
        width=72,
        height=101
):
    key = get_card_key(card)

    if key is None or key not in card_fronts:
        return

    image = pygame.transform.smoothscale(
        card_fronts[key],
        (width, height)
    )

    surface.blit(image, (x, y))


def draw_card_back(
        surface,
        card_back,
        x,
        y,
        width=72,
        height=101
):
    if card_back is None:
        return

    image = pygame.transform.smoothscale(
        card_back,
        (width, height)
    )

    surface.blit(image, (x, y))


# ==================================================
# CHIP HELPERS
# ==================================================

def get_draw_chip_images():
    global _draw_chip_images

    if _draw_chip_images is None:
        _draw_chip_images = {
            "black": pygame.image.load(
                "assets/poker/chip_black.png"
            ).convert_alpha(),
            "blue": pygame.image.load(
                "assets/poker/chip_blue.png"
            ).convert_alpha(),
            "green": pygame.image.load(
                "assets/poker/chip_green.png"
            ).convert_alpha(),
            "red": pygame.image.load(
                "assets/poker/chip_red.png"
            ).convert_alpha(),
            "yellow": pygame.image.load(
                "assets/poker/chip_yellow.png"
            ).convert_alpha(),
        }

    return _draw_chip_images


def get_chip_key(amount, base_unit):
    base_unit = max(1, int(base_unit))

    if amount >= base_unit * 20:
        return "black"
    if amount >= base_unit * 10:
        return "yellow"
    if amount >= base_unit * 5:
        return "green"
    if amount >= base_unit * 2:
        return "blue"
    return "red"


def draw_wager_marker(surface, amount, center, base_unit):
    if amount <= 0:
        return

    fonts = get_draw_fonts()
    chips = get_draw_chip_images()
    chip_key = get_chip_key(amount, base_unit)
    chip = chips.get(chip_key)

    if chip is not None:
        chip = pygame.transform.smoothscale(chip, (26, 26))
        surface.blit(
            chip,
            chip.get_rect(center=center)
        )

    amount_surface = fonts["tiny"].render(
        f"${amount:,}",
        True,
        WHITE
    )

    surface.blit(
        amount_surface,
        amount_surface.get_rect(
            center=(center[0], center[1] + 25)
        )
    )



# ==================================================
# POT DISPLAY / PAYOUT ANIMATION
# ==================================================

_draw_payout_fx_key = None
_draw_payout_fx_started_at = 0

DRAW_PAYOUT_FX_DURATION = 1050


def _draw_pot_chip_count(
        amount,
        base_unit
):
    if amount <= 0:
        return 0

    ratio = (
        float(amount)
        / max(
            1.0,
            float(base_unit)
        )
    )

    if ratio < 2:
        return 1
    if ratio < 5:
        return 2
    if ratio < 10:
        return 3
    if ratio < 20:
        return 4
    if ratio < 40:
        return 5
    if ratio < 80:
        return 6

    return 7


def draw_draw_pot_stack(
        surface,
        amount,
        center,
        base_unit
):
    amount = max(
        0,
        int(amount)
    )

    count = _draw_pot_chip_count(
        amount,
        base_unit
    )

    if count <= 0:
        return

    chips = get_draw_chip_images()
    chip = chips.get(
        get_chip_key(
            amount,
            base_unit
        )
    )

    if chip is None:
        return

    chip_size = 21
    spacing = 11
    row_capacity = 4

    for index in range(count):
        row = index // row_capacity
        column = index % row_capacity

        items_in_row = min(
            row_capacity,
            count - row * row_capacity
        )

        row_width = (
            (items_in_row - 1)
            * spacing
        )

        draw_x = (
            center[0]
            - row_width // 2
            + column * spacing
        )

        draw_y = (
            center[1]
            - row * 7
        )

        scaled = pygame.transform.smoothscale(
            chip,
            (
                chip_size,
                chip_size
            )
        )

        surface.blit(
            scaled,
            scaled.get_rect(
                center=(
                    draw_x,
                    draw_y
                )
            )
        )


def get_draw_payout_fx_progress(
        game
):
    global _draw_payout_fx_key
    global _draw_payout_fx_started_at

    if (
            game.current_stage != "showdown"
            or not game.hand_complete
            or not game.winner_indexes
            or game.get_display_pot_amount() <= 0
    ):
        return None

    key = (
        getattr(
            game,
            "hand_number",
            0
        ),
        tuple(
            game.winner_indexes
        ),
        int(
            game.get_display_pot_amount()
        )
    )

    now = pygame.time.get_ticks()

    if key != _draw_payout_fx_key:
        _draw_payout_fx_key = key
        _draw_payout_fx_started_at = now

    progress = (
        now
        - _draw_payout_fx_started_at
    ) / DRAW_PAYOUT_FX_DURATION

    progress = max(
        0.0,
        min(
            1.0,
            progress
        )
    )

    return _ease_out_cubic(
        progress
    )


def draw_draw_payout_animation(
        surface,
        game,
        npc_anchors
):
    progress = get_draw_payout_fx_progress(
        game
    )

    if (
            progress is None
            or progress >= 1.0
    ):
        return

    winners = list(
        game.winner_indexes
    )

    if not winners:
        return

    amount = max(
        1,
        int(
            game.get_display_pot_amount()
        )
    )

    base_unit = max(
        1,
        int(
            getattr(
                game,
                "big_blind",
                1
            )
        )
    )

    chips = get_draw_chip_images()
    chip = chips.get(
        get_chip_key(
            amount,
            base_unit
        )
    )

    if chip is None:
        return

    start = (
        683,
        242
    )

    target_by_player = {
        0: (
            683,
            708
        )
    }

    for index, anchor in enumerate(
            npc_anchors
    ):
        target_by_player[
            index + 1
        ] = (
            anchor[0] + 82,
            anchor[1] + 28
        )

    chip_count = max(
        3,
        min(
            8,
            _draw_pot_chip_count(
                amount,
                base_unit
            ) + 1
        )
    )

    for chip_index in range(
            chip_count
    ):
        winner_index = winners[
            chip_index
            % len(winners)
        ]

        target = target_by_player.get(
            winner_index,
            start
        )

        local_progress = max(
            0.0,
            min(
                1.0,
                progress
                * 1.18
                - chip_index * 0.035
            )
        )

        draw_x = int(
            start[0]
            + (
                target[0]
                - start[0]
            )
            * local_progress
        )

        draw_y = int(
            start[1]
            + (
                target[1]
                - start[1]
            )
            * local_progress
        )

        draw_y -= int(
            math.sin(
                local_progress
                * math.pi
            )
            * 34
        )

        draw_x += (
            chip_index % 3
            - 1
        ) * 7

        scaled = pygame.transform.smoothscale(
            chip,
            (
                24,
                24
            )
        )

        surface.blit(
            scaled,
            scaled.get_rect(
                center=(
                    draw_x,
                    draw_y
                )
            )
        )


def draw_draw_showdown_banner(
        surface,
        game
):
    if (
            game.current_stage != "showdown"
            or not game.result_text
    ):
        return

    fonts = get_draw_fonts()

    player_won = (
        0 in game.winner_indexes
    )

    phase = (
        pygame.time.get_ticks()
        % 1200
    ) / 1200.0

    pulse = (
        0.5
        + 0.5
        * math.sin(
            phase
            * math.tau
        )
    )

    border = (
        (
            255,
            int(
                190
                + 55 * pulse
            ),
            65
        )
        if player_won
        else (
            185,
            190,
            195
        )
    )

    rect = pygame.Rect(
        358,
        448,
        650,
        48
    )

    draw_panel(
        surface,
        rect,
        (
            10,
            12,
            14,
            225
        ),
        border=border,
        radius=12,
        border_width=(
            4
            if player_won
            else 2
        )
    )

    result_surface = render_text_fit(
        game.result_text,
        fonts["small"],
        WHITE,
        rect.width - 30,
        minimum_size=12
    )

    surface.blit(
        result_surface,
        result_surface.get_rect(
            center=rect.center
        )
    )


# ==================================================
# POLISHED CARD / CHIP ANIMATION HELPERS
# ==================================================

DRAW_CHIP_FX_DURATION = 280
DRAW_WAGER_SWEEP_DELAY = 180
DRAW_WAGER_SWEEP_DURATION = 680

_draw_card_fx_hand_number = -1
_draw_card_fx_stage = None
_draw_card_fx_kind = None
_draw_card_fx_started_at = 0

_draw_chip_fx_hand_number = -1
_draw_chip_fx_stage = None
_draw_chip_fx_signatures = {}
_draw_chip_fx_started_at = {}
_draw_chip_fx_indexes = {}
_draw_wager_sweep_key = None
_draw_wager_sweep_started_at = 0


def _ease_out_cubic(progress):
    progress = max(0.0, min(1.0, float(progress)))
    return 1.0 - pow(1.0 - progress, 3)


def _fx_progress(elapsed, delay=0, duration=180):
    if elapsed <= delay:
        return 0.0
    return max(0.0, min(1.0, (elapsed - delay) / max(1, duration)))


def sync_draw_card_fx(game):
    global _draw_card_fx_hand_number
    global _draw_card_fx_stage
    global _draw_card_fx_kind
    global _draw_card_fx_started_at

    now = pygame.time.get_ticks()
    hand_number = getattr(game, "hand_number", 0)
    stage = getattr(game, "current_stage", None)

    if hand_number != _draw_card_fx_hand_number:
        _draw_card_fx_hand_number = hand_number
        _draw_card_fx_stage = stage
        _draw_card_fx_kind = "deal"
        _draw_card_fx_started_at = now
    elif stage != _draw_card_fx_stage:
        _draw_card_fx_stage = stage
        if stage == "draw":
            _draw_card_fx_kind = "draw_phase"
        elif stage == "post_draw":
            _draw_card_fx_kind = "redraw"
        elif stage == "showdown":
            _draw_card_fx_kind = "showdown"
        else:
            _draw_card_fx_kind = None
        _draw_card_fx_started_at = now

    elapsed = now - _draw_card_fx_started_at
    if elapsed > 1500:
        return None, elapsed
    return _draw_card_fx_kind, elapsed


def _draw_scaled_card(surface, image, x, y, width, height, progress):
    progress = max(0.0, min(1.0, progress))
    eased = _ease_out_cubic(progress)
    scale = 0.72 + 0.28 * eased
    draw_w = max(8, int(width * scale))
    draw_h = max(10, int(height * scale))
    scaled = pygame.transform.smoothscale(image, (draw_w, draw_h))
    if progress < 1.0:
        scaled.set_alpha(max(80, int(255 * eased)))
    target_center = (x + width // 2, y + height // 2)
    surface.blit(scaled, scaled.get_rect(center=target_center))


def draw_popping_card_face(surface, card, x, y, card_fronts, width, height, progress):
    key = get_card_key(card)
    if key is None or key not in card_fronts:
        return
    image = card_fronts[key]
    _draw_scaled_card(surface, image, x, y, width, height, progress)


def draw_popping_card_back(surface, card_back, x, y, width, height, progress):
    if card_back is None:
        return
    _draw_scaled_card(surface, card_back, x, y, width, height, progress)


def sync_draw_chip_fx_context(game):
    global _draw_chip_fx_hand_number
    global _draw_chip_fx_stage
    global _draw_chip_fx_signatures
    global _draw_chip_fx_started_at
    global _draw_chip_fx_indexes
    global _draw_wager_sweep_key
    global _draw_wager_sweep_started_at

    hand_number = getattr(game, "hand_number", 0)
    stage = getattr(game, "current_stage", None)

    if hand_number != _draw_chip_fx_hand_number or stage != _draw_chip_fx_stage:
        _draw_chip_fx_hand_number = hand_number
        _draw_chip_fx_stage = stage
        _draw_chip_fx_signatures = {}
        _draw_chip_fx_started_at = {}
        _draw_chip_fx_indexes = {}
        _draw_wager_sweep_key = None
        _draw_wager_sweep_started_at = 0


def _get_draw_chip_fx(key, chunks):
    global _draw_chip_fx_signatures
    global _draw_chip_fx_started_at
    global _draw_chip_fx_indexes

    signature = tuple(int(v) for v in chunks)
    previous = _draw_chip_fx_signatures.get(key)
    now = pygame.time.get_ticks()

    if previous is None:
        _draw_chip_fx_signatures[key] = signature
        if signature:
            _draw_chip_fx_indexes[key] = len(signature) - 1
            _draw_chip_fx_started_at[key] = now
    elif previous != signature:
        old_len = len(previous)
        _draw_chip_fx_signatures[key] = signature
        if len(signature) > old_len:
            _draw_chip_fx_indexes[key] = len(signature) - 1
            _draw_chip_fx_started_at[key] = now
        else:
            _draw_chip_fx_indexes.pop(key, None)
            _draw_chip_fx_started_at.pop(key, None)

    idx = _draw_chip_fx_indexes.get(key)
    started = _draw_chip_fx_started_at.get(key)
    if idx is None or started is None:
        return None, 1.0

    progress = max(0.0, min(1.0, (now - started) / DRAW_CHIP_FX_DURATION))
    return idx, progress


def get_draw_wager_sweep_progress(game):
    global _draw_wager_sweep_key
    global _draw_wager_sweep_started_at

    if game.current_stage not in ("preflop", "post_draw"):
        return 0.0

    has_chips = bool(game.player_bet_chunks) or any(bool(c) for c in game.npc_bet_chunks)
    if not has_chips or game.current_actor != -1:
        return 0.0

    key = (getattr(game, "hand_number", 0), game.current_stage)
    now = pygame.time.get_ticks()

    if _draw_wager_sweep_key != key:
        _draw_wager_sweep_key = key
        _draw_wager_sweep_started_at = now

    elapsed = now - _draw_wager_sweep_started_at
    if elapsed < DRAW_WAGER_SWEEP_DELAY:
        return 0.0

    progress = (elapsed - DRAW_WAGER_SWEEP_DELAY) / DRAW_WAGER_SWEEP_DURATION
    return _ease_out_cubic(max(0.0, min(1.0, progress)))


def draw_animated_wager_chunks(
        surface,
        chunks,
        center_x,
        y,
        base_unit,
        origin,
        animation_key,
        sweep_target=None,
        sweep_progress=0.0
):
    if not chunks or sweep_progress >= 1.0:
        return

    fonts = get_draw_fonts()
    chips = get_draw_chip_images()
    animated_index, progress = _get_draw_chip_fx(animation_key, chunks)
    eased = _ease_out_cubic(progress)

    chip_size = 24
    spacing = 13
    total_width = max(0, (len(chunks) - 1) * spacing)
    start_x = center_x - total_width // 2

    for chunk_index, amount in enumerate(chunks):
        if amount <= 0:
            continue

        chip = chips.get(get_chip_key(amount, base_unit))
        if chip is None:
            continue

        target_x = start_x + chunk_index * spacing
        target_y = y
        draw_x, draw_y = target_x, target_y
        draw_size = chip_size

        if chunk_index == animated_index and progress < 1.0 and sweep_progress <= 0.0:
            ox, oy = origin
            draw_x = int(ox + (target_x - ox) * eased)
            draw_y = int(oy + (target_y - oy) * eased)
            draw_y -= int(math.sin(progress * math.pi) * 16)
            draw_size = max(12, int(chip_size * (0.78 + 0.22 * eased)))

        if sweep_target is not None and sweep_progress > 0.0:
            px, py = sweep_target
            draw_x = int(target_x + (px - target_x) * sweep_progress)
            draw_y = int(target_y + (py - target_y) * sweep_progress)
            draw_y -= int(math.sin(sweep_progress * math.pi) * 10)
            draw_size = max(13, int(chip_size * (1.0 - 0.30 * sweep_progress)))

        scaled = pygame.transform.smoothscale(chip, (draw_size, draw_size))
        surface.blit(scaled, scaled.get_rect(center=(draw_x, draw_y)))

    total = sum(chunks)
    if total > 0:
        text = fonts["tiny"].render(f"${total:,}", True, WHITE)
        if sweep_progress > 0.0:
            text.set_alpha(max(0, int(255 * (1.0 - sweep_progress))))
        surface.blit(text, text.get_rect(center=(center_x, y + 27)))


# ==================================================
# BUY-IN
# ==================================================

def get_five_card_draw_buy_in_amounts(career_cash):
    career_cash = max(0, int(career_cash))

    return {
        "25": int(career_cash * 0.25),
        "50": int(career_cash * 0.50),
        "75": int(career_cash * 0.75),
        "max": career_cash,
    }


def get_five_card_draw_buy_in_action(
        mouse_pos,
        career_cash,
        minimum_buy_in=100
):
    if mouse_pos is None:
        return None

    if DRAW_BUY_IN_BACK_RECT.collidepoint(mouse_pos):
        return "back", None

    amounts = get_five_card_draw_buy_in_amounts(career_cash)

    choices = (
        (DRAW_BUY_IN_25_RECT, amounts["25"]),
        (DRAW_BUY_IN_50_RECT, amounts["50"]),
        (DRAW_BUY_IN_75_RECT, amounts["75"]),
        (DRAW_BUY_IN_MAX_RECT, amounts["max"]),
    )

    for rect, amount in choices:
        if (
                rect.collidepoint(mouse_pos)
                and amount >= minimum_buy_in
        ):
            return "buy_in", amount

    return None


def draw_five_card_draw_buy_in(
        surface,
        mouse_pos,
        career_cash,
        draw_submenu_background,
        minimum_buy_in=100
):
    draw_submenu_background(overlay_alpha=125)

    fonts = get_draw_fonts()

    draw_panel(
        surface,
        DRAW_BUY_IN_PANEL_RECT,
        (10, 18, 18, 245),
        (185, 190, 195),
        radius=16
    )

    title = fonts["title"].render(
        "FIVE-CARD DRAW BUY-IN",
        True,
        WHITE
    )

    surface.blit(
        title,
        title.get_rect(
            center=(DRAW_BUY_IN_PANEL_RECT.centerx, 225)
        )
    )

    cash = fonts["name"].render(
        f"Career Cash: ${career_cash:,}",
        True,
        WHITE
    )

    surface.blit(
        cash,
        cash.get_rect(
            center=(DRAW_BUY_IN_PANEL_RECT.centerx, 275)
        )
    )

    amounts = get_five_card_draw_buy_in_amounts(career_cash)

    choices = (
        (DRAW_BUY_IN_25_RECT, "25%", amounts["25"]),
        (DRAW_BUY_IN_50_RECT, "50%", amounts["50"]),
        (DRAW_BUY_IN_75_RECT, "75%", amounts["75"]),
        (DRAW_BUY_IN_MAX_RECT, "MAX", amounts["max"]),
    )

    for rect, label, amount in choices:
        enabled = amount >= minimum_buy_in

        draw_button(
            surface,
            rect,
            label,
            mouse_pos,
            fonts["name"],
            enabled=enabled
        )

        amount_surface = fonts["small"].render(
            f"${amount:,}",
            True,
            WHITE if enabled else (130, 130, 130)
        )

        surface.blit(
            amount_surface,
            amount_surface.get_rect(
                center=(rect.centerx, rect.centery + 26)
            )
        )

    info = fonts["small"].render(
        "Unused cash stays in your Career wallet. Opponents begin with the same stack.",
        True,
        MUTED
    )

    surface.blit(
        info,
        info.get_rect(
            center=(DRAW_BUY_IN_PANEL_RECT.centerx, 466)
        )
    )

    if career_cash < minimum_buy_in:
        warning = fonts["small"].render(
            f"At least ${minimum_buy_in:,} is required to play.",
            True,
            (235, 135, 135)
        )

        surface.blit(
            warning,
            warning.get_rect(
                center=(DRAW_BUY_IN_PANEL_RECT.centerx, 495)
            )
        )

    draw_button(
        surface,
        DRAW_BUY_IN_BACK_RECT,
        "BACK",
        mouse_pos,
        fonts["small"],
        enabled=True
    )


# ==================================================
# SESSION / CHAT / LOG STATE
# ==================================================

def reset_five_card_draw_ui_session():
    global _draw_selected_card_indexes
    global _draw_chat_history
    global _draw_active_tab
    global _draw_log_scroll
    global _draw_chat_scroll
    global _draw_chat_unread
    global _draw_last_hand_number
    global _draw_bet_fraction
    global _draw_bet_slider_dragging
    global _draw_manual_bet_text
    global _draw_manual_bet_active

    _draw_selected_card_indexes = set()
    _draw_chat_history = []
    _draw_speech_overlay.clear()
    _draw_active_tab = "log"
    _draw_log_scroll = 0
    _draw_chat_scroll = 0
    _draw_chat_unread = False
    _draw_last_hand_number = -1
    _draw_bet_fraction = 0.50
    _draw_bet_slider_dragging = False
    _draw_manual_bet_text = ""
    _draw_manual_bet_active = False


def add_five_card_draw_chat_message(speaker, message):
    global _draw_chat_unread
    global _draw_chat_scroll

    if not message:
        return

    if speaker and is_poker_chat_popups_enabled():
        _draw_speech_overlay.post(
            speaker,
            message
        )

    text = (
        f"{speaker}: {message}"
        if speaker
        else str(message)
    )

    _draw_chat_history.append(text)

    if len(_draw_chat_history) > 100:
        del _draw_chat_history[:-100]

    _draw_chat_scroll = 0

    if _draw_active_tab != "chat":
        _draw_chat_unread = True


def handle_five_card_draw_panel_click(mouse_pos):
    global _draw_active_tab
    global _draw_chat_unread

    if mouse_pos is None:
        return False

    log_rect = pygame.Rect(
        DRAW_LOG_RECT.x + 12,
        DRAW_LOG_RECT.y + 10,
        100,
        28
    )

    chat_rect = pygame.Rect(
        DRAW_LOG_RECT.x + 118,
        DRAW_LOG_RECT.y + 10,
        76,
        28
    )

    if log_rect.collidepoint(mouse_pos):
        _draw_active_tab = "log"
        return True

    if chat_rect.collidepoint(mouse_pos):
        _draw_active_tab = "chat"
        _draw_chat_unread = False
        return True

    return False


def scroll_five_card_draw_panel(wheel_y, game):
    global _draw_log_scroll
    global _draw_chat_scroll

    visible = 3

    if _draw_active_tab == "chat":
        max_scroll = max(
            0,
            len(_draw_chat_history) - visible
        )

        _draw_chat_scroll = max(
            0,
            min(
                _draw_chat_scroll + wheel_y,
                max_scroll
            )
        )

    else:
        lines = game.get_hand_history_lines()

        max_scroll = max(
            0,
            len(lines) - visible
        )

        _draw_log_scroll = max(
            0,
            min(
                _draw_log_scroll + wheel_y,
                max_scroll
            )
        )


# ==================================================
# PLAYER DRAW SELECTION
# ==================================================

def get_player_card_rects():
    total_width = (
        PLAYER_CARD_WIDTH * 5
        + PLAYER_CARD_GAP * 4
    )

    start_x = 683 - total_width // 2
    rects = []

    for index in range(5):
        lift = (
            PLAYER_CARD_SELECTED_LIFT
            if index in _draw_selected_card_indexes
            else 0
        )

        rects.append(
            pygame.Rect(
                start_x + index * (
                    PLAYER_CARD_WIDTH + PLAYER_CARD_GAP
                ),
                PLAYER_CARD_Y - lift,
                PLAYER_CARD_WIDTH,
                PLAYER_CARD_HEIGHT
            )
        )

    return rects


def handle_five_card_draw_card_click(mouse_pos, game):
    global _draw_selected_card_indexes

    if (
            mouse_pos is None
            or game.current_stage != "draw"
            or game.player_draw_complete
            or game.player_folded
            or game.hand_complete
    ):
        return False

    for index, rect in enumerate(
            get_player_card_rects()
    ):
        if rect.collidepoint(mouse_pos):
            if index in _draw_selected_card_indexes:
                _draw_selected_card_indexes.remove(index)
            else:
                _draw_selected_card_indexes.add(index)

            return True

    return False


def get_selected_draw_indexes():
    return sorted(_draw_selected_card_indexes)


def clear_five_card_draw_selection():
    global _draw_selected_card_indexes
    _draw_selected_card_indexes = set()


# ==================================================
# BETTING CONTROLS
# ==================================================

def clear_five_card_draw_manual_bet():
    global _draw_manual_bet_text
    global _draw_manual_bet_active

    _draw_manual_bet_text = ""
    _draw_manual_bet_active = False


def handle_five_card_draw_manual_bet_click(mouse_pos, game):
    global _draw_manual_bet_active

    if mouse_pos is None:
        return False

    can_edit = (
        not game.hand_complete
        and game.current_stage in ("preflop", "post_draw")
        and game.current_actor == 0
        and game.can_player_act_now()
        and (game.current_bet == 0 or game.can_player_raise())
    )

    if can_edit and DRAW_MANUAL_BET_RECT.collidepoint(mouse_pos):
        _draw_manual_bet_active = True
        return True

    if _draw_manual_bet_active:
        _draw_manual_bet_active = False

    return False


def handle_five_card_draw_manual_bet_key(event, game):
    global _draw_manual_bet_text
    global _draw_manual_bet_active

    if not _draw_manual_bet_active or event.type != pygame.KEYDOWN:
        return False

    if event.key == pygame.K_ESCAPE:
        _draw_manual_bet_active = False
        return True

    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        _draw_manual_bet_active = False
        return True

    if event.key == pygame.K_BACKSPACE:
        _draw_manual_bet_text = _draw_manual_bet_text[:-1]
        return True

    character = getattr(event, "unicode", "")
    if character.isdigit() and len(_draw_manual_bet_text) < 9:
        _draw_manual_bet_text += character

    return True


def get_five_card_draw_manual_bet_amount(game):
    if not _draw_manual_bet_text:
        return None

    try:
        requested = int(_draw_manual_bet_text)
    except ValueError:
        return None

    if requested <= 0 or game.player_stack <= 0:
        return None

    if game.current_bet == 0:
        minimum = game.get_minimum_open_bet()
        maximum = game.player_stack
        if maximum <= minimum:
            return maximum
        return max(minimum, min(requested, maximum))

    minimum = game.get_minimum_raise_to()
    maximum = game.get_player_maximum_raise_to()
    if maximum <= minimum:
        return maximum
    return max(minimum, min(requested, maximum))


def set_five_card_draw_bet_slider_from_mouse(mouse_pos):
    global _draw_bet_fraction
    global _draw_manual_bet_text
    global _draw_manual_bet_active

    if mouse_pos is None:
        return False

    mouse_x = max(
        DRAW_SLIDER_RECT.left,
        min(mouse_pos[0], DRAW_SLIDER_RECT.right)
    )

    _draw_bet_fraction = (
        mouse_x - DRAW_SLIDER_RECT.left
    ) / max(1, DRAW_SLIDER_RECT.width)

    _draw_bet_fraction = max(0.0, min(_draw_bet_fraction, 1.0))
    _draw_manual_bet_text = ""
    _draw_manual_bet_active = False
    return True


def update_five_card_draw_bet_slider(mouse_pos, game):
    global _draw_bet_slider_dragging

    can_edit = (
        not game.hand_complete
        and game.current_stage in ("preflop", "post_draw")
        and game.current_actor == 0
        and game.can_player_act_now()
        and (game.current_bet == 0 or game.can_player_raise())
    )

    if not can_edit or mouse_pos is None:
        return False

    hit_rect = DRAW_SLIDER_RECT.inflate(0, 24)
    if hit_rect.collidepoint(mouse_pos):
        _draw_bet_slider_dragging = True
        return set_five_card_draw_bet_slider_from_mouse(mouse_pos)

    return False


def drag_five_card_draw_bet_slider(mouse_pos):
    if not _draw_bet_slider_dragging:
        return False
    return set_five_card_draw_bet_slider_from_mouse(mouse_pos)


def stop_five_card_draw_bet_slider():
    global _draw_bet_slider_dragging
    was_dragging = _draw_bet_slider_dragging
    _draw_bet_slider_dragging = False
    return was_dragging


def handle_five_card_draw_bet_preset(mouse_pos):
    global _draw_bet_fraction
    global _draw_manual_bet_text
    global _draw_manual_bet_active

    if mouse_pos is None:
        return False

    if DRAW_MIN_RECT.collidepoint(mouse_pos):
        _draw_bet_fraction = 0.0
        _draw_manual_bet_text = ""
        _draw_manual_bet_active = False
        return True

    if DRAW_HALF_RECT.collidepoint(mouse_pos):
        _draw_bet_fraction = 0.5
        _draw_manual_bet_text = ""
        _draw_manual_bet_active = False
        return True

    if DRAW_POT_RECT.collidepoint(mouse_pos):
        _draw_bet_fraction = 0.75
        _draw_manual_bet_text = ""
        _draw_manual_bet_active = False
        return True

    if DRAW_MAX_RECT.collidepoint(mouse_pos):
        _draw_bet_fraction = 1.0
        _draw_manual_bet_text = ""
        _draw_manual_bet_active = False
        return True

    return False


def get_five_card_draw_bet_amount(game):
    stack = game.player_stack

    if stack <= 0:
        return 0

    manual_amount = get_five_card_draw_manual_bet_amount(game)
    if manual_amount is not None:
        return manual_amount

    if game.current_bet == 0:
        minimum = game.get_minimum_open_bet()
        maximum = stack

        if maximum <= minimum:
            return maximum

        if _draw_bet_fraction >= 0.99:
            return maximum

        pot_target = max(
            minimum,
            int(
                max(game.pot, minimum)
                * max(0.35, _draw_bet_fraction)
            )
        )

        return max(
            minimum,
            min(pot_target, maximum)
        )

    minimum = game.get_minimum_raise_to()
    maximum = game.get_player_maximum_raise_to()

    if maximum <= minimum:
        return maximum

    if _draw_bet_fraction >= 0.99:
        return maximum

    additional = max(
        game.get_minimum_raise_size(),
        int(
            max(game.pot, game.big_blind)
            * max(0.35, _draw_bet_fraction)
        )
    )

    target = game.current_bet + additional

    return max(
        minimum,
        min(target, maximum)
    )


def get_five_card_draw_action(mouse_pos, game):
    if mouse_pos is None:
        return None

    if DRAW_OPTIONS_RECT.collidepoint(mouse_pos):
        return ACTION_OPTIONS

    if game.hand_complete and DRAW_EXIT_RECT.collidepoint(mouse_pos):
        return ACTION_RETURN

    if game.hand_complete:
        if DRAW_NEXT_HAND_RECT.collidepoint(mouse_pos):
            return ACTION_NEXT_HAND
        return None

    if (
            game.current_stage == "draw"
            and not game.player_draw_complete
            and not game.player_folded
    ):
        if DRAW_CONFIRM_RECT.collidepoint(mouse_pos):
            return ACTION_DRAW

        if DRAW_CLEAR_RECT.collidepoint(mouse_pos):
            clear_five_card_draw_selection()
            return "clear"

        return None

    if (
            game.current_actor != 0
            or not game.can_player_act_now()
    ):
        return None

    if DRAW_FOLD_RECT.collidepoint(mouse_pos):
        return ACTION_FOLD

    if DRAW_CALL_RECT.collidepoint(mouse_pos):
        return ACTION_CHECK_CALL

    if DRAW_RAISE_RECT.collidepoint(mouse_pos):
        if (
                game.current_bet == 0
                or game.can_player_raise()
        ):
            return ACTION_BET_RAISE

    return None


# ==================================================
# POSITION BADGES
# ==================================================

def get_position_labels(game, player_index):
    labels = []

    if player_index == game.dealer_index:
        labels.append("D")

    if player_index == game.small_blind_index:
        labels.append("SB")

    if player_index == game.big_blind_index:
        labels.append("BB")

    return labels


def draw_position_badges(
        surface,
        game,
        player_index,
        x,
        y
):
    font = get_draw_fonts()["micro"]

    colors = {
        "D": (205, 165, 55),
        "SB": (70, 125, 190),
        "BB": (170, 75, 70),
    }

    for label in get_position_labels(
            game,
            player_index
    ):
        width = 28 if label == "D" else 34
        rect = pygame.Rect(x, y, width, 20)

        pygame.draw.rect(
            surface,
            colors[label],
            rect,
            border_radius=6
        )

        pygame.draw.rect(
            surface,
            (245, 235, 205),
            rect,
            1,
            border_radius=6
        )

        text = font.render(label, True, WHITE)

        surface.blit(
            text,
            text.get_rect(center=rect.center)
        )

        x += rect.width + 4


# ==================================================
# LOG PANEL
# ==================================================

def draw_log_panel(surface, game):
    fonts = get_draw_fonts()

    draw_panel(
        surface,
        DRAW_LOG_RECT,
        (10, 15, 15, 235),
        (115, 125, 120),
        radius=12
    )

    log_rect = pygame.Rect(
        DRAW_LOG_RECT.x + 12,
        DRAW_LOG_RECT.y + 10,
        100,
        28
    )

    chat_rect = pygame.Rect(
        DRAW_LOG_RECT.x + 118,
        DRAW_LOG_RECT.y + 10,
        76,
        28
    )

    draw_button(
        surface,
        log_rect,
        "GAME LOG",
        None,
        fonts["tiny"],
        selected=_draw_active_tab == "log"
    )

    chat_label = "CHAT"

    draw_button(
        surface,
        chat_rect,
        chat_label,
        None,
        fonts["tiny"],
        selected=_draw_active_tab == "chat",
        attention=(
            _draw_chat_unread
            and _draw_active_tab != "chat"
        )
    )

    if _draw_active_tab == "chat":
        lines = _draw_chat_history
        scroll = _draw_chat_scroll
    else:
        lines = game.get_hand_history_lines()
        scroll = _draw_log_scroll

    visible = (
        4
        if _draw_active_tab == "chat"
        else 3
    )
    line_step = (
        19
        if _draw_active_tab == "chat"
        else 28
    )
    end = max(0, len(lines) - scroll)
    start = max(0, end - visible)
    shown = lines[start:end]

    y = DRAW_LOG_RECT.y + 50

    for line in shown:
        rendered = render_text_fit(
            str(line),
            fonts["tiny"],
            (220, 225, 220),
            DRAW_LOG_RECT.width - 28,
            minimum_size=11
        )

        surface.blit(
            rendered,
            (DRAW_LOG_RECT.x + 14, y)
        )

        y += line_step


# ==================================================
# ACTION PANEL
# ==================================================

def draw_action_panel(
        surface,
        mouse_pos,
        game,
        next_hand_seconds=None
):
    fonts = get_draw_fonts()

    draw_panel(
        surface,
        DRAW_ACTION_PANEL_RECT,
        (10, 15, 15, 235),
        (115, 125, 120),
        radius=12
    )

    if game.hand_complete:
        table_cleared = (
            game.all_npcs_busted()
            and not game.player_busted
        )

        if table_cleared:
            label = "TABLE CLEARED +100"
            enabled = True

        else:
            label = "NEXT HAND"

            if (
                    next_hand_seconds is not None
                    and next_hand_seconds > 0
            ):
                label = f"NEXT HAND ({next_hand_seconds})"

            enabled = (
                game.player_stack > 0
                and not game.player_busted
            )

        draw_button(
            surface,
            DRAW_NEXT_HAND_RECT,
            label,
            mouse_pos,
            fonts["small"],
            enabled=enabled,
            attention=enabled
        )

        return

    if (
            game.current_stage == "draw"
            and not game.player_draw_complete
            and not game.player_folded
    ):
        count = len(_draw_selected_card_indexes)

        instruction = (
            "Select up to five cards to discard."
            if count == 0
            else f"{count} card{'s' if count != 1 else ''} marked for discard."
        )

        tip = fonts["tiny"].render(
            instruction,
            True,
            MUTED
        )

        surface.blit(
            tip,
            tip.get_rect(
                center=(
                    DRAW_ACTION_PANEL_RECT.centerx,
                    DRAW_ACTION_PANEL_RECT.y + 26
                )
            )
        )

        label = (
            "STAND PAT"
            if count == 0
            else f"DRAW {count}"
        )

        draw_button(
            surface,
            DRAW_CONFIRM_RECT,
            label,
            mouse_pos,
            fonts["small"],
            enabled=True,
            attention=True
        )

        draw_button(
            surface,
            DRAW_CLEAR_RECT,
            "CLEAR",
            mouse_pos,
            fonts["tiny"],
            enabled=count > 0
        )

        return

    can_act = (
        game.current_actor == 0
        and game.can_player_act_now()
    )

    amount_to_call = (
        game.get_player_amount_to_call()
        if can_act
        else 0
    )

    call_label = (
        "CHECK"
        if amount_to_call == 0
        else f"CALL ${min(amount_to_call, game.player_stack):,}"
    )

    wager_amount = (
        get_five_card_draw_bet_amount(game)
        if can_act
        else 0
    )

    raise_label = (
        f"BET ${wager_amount:,}"
        if game.current_bet == 0
        else f"RAISE ${wager_amount:,}"
    )

    draw_button(
        surface,
        DRAW_FOLD_RECT,
        "FOLD",
        mouse_pos,
        fonts["small"],
        enabled=can_act
    )

    draw_button(
        surface,
        DRAW_CALL_RECT,
        call_label,
        mouse_pos,
        fonts["small"],
        enabled=can_act
    )

    draw_button(
        surface,
        DRAW_RAISE_RECT,
        raise_label,
        mouse_pos,
        fonts["tiny"],
        enabled=(
            can_act
            and (
                game.current_bet == 0
                or game.can_player_raise()
            )
        ),
        attention=(
            can_act
            and game.current_bet == 0
        )
    )

    # Clear visual separation between primary actions and bet sizing.
    pygame.draw.line(
        surface,
        (85, 90, 92),
        (
            DRAW_ACTION_PANEL_RECT.x + 18,
            DRAW_ACTION_PANEL_RECT.y + 62
        ),
        (
            DRAW_ACTION_PANEL_RECT.right - 18,
            DRAW_ACTION_PANEL_RECT.y + 62
        ),
        1
    )

    # Bet sizing slider. Stud remains fixed-limit, but Draw is no-limit.
    pygame.draw.rect(
        surface,
        (70, 75, 85),
        DRAW_SLIDER_RECT,
        border_radius=7
    )

    knob_width = 18
    knob_x = int(
        DRAW_SLIDER_RECT.x
        + (DRAW_SLIDER_RECT.width - knob_width)
        * _draw_bet_fraction
    )
    knob_rect = pygame.Rect(
        knob_x,
        DRAW_SLIDER_RECT.y - 3,
        knob_width,
        DRAW_SLIDER_RECT.height + 6
    )
    pygame.draw.rect(
        surface,
        (175, 205, 240) if _draw_bet_slider_dragging else (130, 170, 220),
        knob_rect,
        border_radius=6
    )
    pygame.draw.rect(surface, (210, 225, 240), knob_rect, 2, border_radius=6)

    manual_enabled = can_act and (game.current_bet == 0 or game.can_player_raise())
    draw_panel(
        surface,
        DRAW_MANUAL_BET_RECT,
        (18, 24, 27, 235) if manual_enabled else (48, 48, 52, 220),
        GOLD if _draw_manual_bet_active else ((150, 175, 205) if _draw_manual_bet_text else (105, 110, 118)),
        radius=7,
        border_width=2 if _draw_manual_bet_active else 1
    )
    manual_label = f"${_draw_manual_bet_text}" if _draw_manual_bet_text else "TYPE $"
    manual_surface = fonts["tiny"].render(
        manual_label,
        True,
        WHITE if manual_enabled else (145, 145, 150)
    )
    surface.blit(manual_surface, manual_surface.get_rect(center=DRAW_MANUAL_BET_RECT.center))

    presets = (
        (DRAW_MIN_RECT, "MIN", 0.0),
        (DRAW_HALF_RECT, "1/2", 0.5),
        (DRAW_POT_RECT, "POT", 0.75),
        (DRAW_MAX_RECT, "MAX", 1.0),
    )

    for rect, label, fraction in presets:
        draw_button(
            surface,
            rect,
            label,
            mouse_pos,
            fonts["tiny"],
            enabled=can_act,
            selected=(
                abs(_draw_bet_fraction - fraction)
                < 0.01
            )
        )

    if not can_act:
        waiting = fonts["tiny"].render(
            "Waiting for opponent...",
            True,
            MUTED
        )

        surface.blit(
            waiting,
            waiting.get_rect(
                center=(
                    DRAW_ACTION_PANEL_RECT.centerx,
                    DRAW_ACTION_PANEL_RECT.y + 92
                )
            )
        )


# ==================================================
# TABLE DRAWING HELPERS
# ==================================================

def draw_table(surface, felt_surface):
    pygame.draw.ellipse(
        surface,
        TABLE_EDGE,
        TABLE_RECT
    )

    if felt_surface is not None:
        scaled_felt = pygame.transform.smoothscale(
            felt_surface,
            INNER_TABLE_RECT.size
        )

        felt_layer = pygame.Surface(
            INNER_TABLE_RECT.size,
            pygame.SRCALPHA
        )

        felt_layer.blit(scaled_felt, (0, 0))

        mask = pygame.Surface(
            INNER_TABLE_RECT.size,
            pygame.SRCALPHA
        )

        pygame.draw.ellipse(
            mask,
            (255, 255, 255, 255),
            mask.get_rect()
        )

        felt_layer.blit(
            mask,
            (0, 0),
            special_flags=pygame.BLEND_RGBA_MULT
        )

        surface.blit(
            felt_layer,
            INNER_TABLE_RECT.topleft
        )

    else:
        pygame.draw.ellipse(
            surface,
            TABLE_GREEN,
            INNER_TABLE_RECT
        )

    pygame.draw.ellipse(
        surface,
        WHITE,
        INNER_TABLE_RECT,
        2
    )


def draw_npc_seat(
        surface,
        game,
        index,
        npc,
        anchor,
        card_fronts,
        card_back,
        draw_npc_portrait,
        card_fx_kind=None,
        card_fx_elapsed=0
):
    fonts = get_draw_fonts()
    anchor_x, anchor_y = anchor

    busted = index < len(game.npc_busted) and game.npc_busted[index]
    folded = index < len(game.npc_folded) and game.npc_folded[index]
    all_in = (
        index < len(game.npc_all_in)
        and game.npc_all_in[index]
        and not busted
        and not folded
    )
    current = (
        game.current_actor == index + 1
        and not game.hand_complete
        and not busted
        and not folded
    )
    winner = game.current_stage == "showdown" and index + 1 in game.winner_indexes

    portrait_rect = pygame.Rect(anchor_x - 52, anchor_y, 72, 72)
    draw_npc_portrait(npc, portrait_rect, "holdem")

    if busted or folded:
        overlay = pygame.Surface(portrait_rect.size, pygame.SRCALPHA)
        pygame.draw.circle(
            overlay,
            (5, 5, 5, 205 if busted else 165),
            (portrait_rect.width // 2, portrait_rect.height // 2),
            min(portrait_rect.width, portrait_rect.height) // 2
        )
        surface.blit(overlay, portrait_rect.topleft)

        if busted:
            pygame.draw.line(surface, (150, 150, 150),
                             (portrait_rect.left + 18, portrait_rect.top + 18),
                             (portrait_rect.right - 18, portrait_rect.bottom - 18), 3)
            pygame.draw.line(surface, (150, 150, 150),
                             (portrait_rect.right - 18, portrait_rect.top + 18),
                             (portrait_rect.left + 18, portrait_rect.bottom - 18), 3)

    if current or winner:
        pygame.draw.rect(
            surface, GOLD, portrait_rect.inflate(6, 6),
            4 if winner else 3, border_radius=9
        )

    # Compact five-card spread. The cards live mostly over the name side of
    # the seat so position badges and portraits stay readable.
    hand = game.npc_hands[index] if index < len(game.npc_hands) else []
    show_faces = game.current_stage == "showdown" and not folded and not busted

    if not busted:
        card_w, card_h, step_x = 52, 73, 16
        card_count = min(5, len(hand))
        total_width = card_w + max(0, card_count - 1) * step_x
        cards_center_x = anchor_x + 48
        cards_x = cards_center_x - total_width // 2
        cards_y = anchor_y - 58

        for card_index in range(card_count):
            x = cards_x + card_index * step_x
            y = cards_y + abs(card_index - 2) * 2

            shadow = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(shadow, (0, 0, 0, 75), shadow.get_rect(), border_radius=5)
            surface.blit(shadow, (x + 3, y + 4))

            delay = (index * 5 + card_index) * 32
            progress = _fx_progress(card_fx_elapsed, delay=delay, duration=190)
            animate = card_fx_kind in ("deal", "draw_phase", "showdown") and progress < 1.0

            if show_faces:
                if animate:
                    draw_popping_card_face(surface, hand[card_index], x, y, card_fronts, card_w, card_h, progress)
                else:
                    draw_card_face(surface, hand[card_index], x, y, card_fronts, card_w, card_h)
            else:
                if animate:
                    draw_popping_card_back(surface, card_back, x, y, card_w, card_h, progress)
                else:
                    draw_card_back(surface, card_back, x, y, card_w, card_h)

            if folded:
                fold_tint = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                fold_tint.fill((105, 105, 105, 185))
                surface.blit(fold_tint, (x, y))

    draw_position_badges(
        surface, game, index + 1,
        portrait_rect.left - 2, portrait_rect.top - 26
    )

    name_rect = pygame.Rect(anchor_x, anchor_y + 6, 165, 40)
    if busted:
        name_fill, name_border, name_color = (24, 24, 26, 230), (75, 75, 80), (145, 145, 150)
    elif folded:
        name_fill, name_border, name_color = (10, 10, 10, 215), (85, 85, 90), (185, 185, 190)
    else:
        name_fill = (18, 20, 24, 238)
        name_border = GOLD if (current or winner) else (120, 125, 130)
        name_color = WHITE

    draw_panel(surface, name_rect, name_fill, name_border, radius=10,
               border_width=4 if winner else (3 if current else 2))
    name_surface = render_text_fit(
        game.get_table_player_name(index + 1),
        fonts["name"],
        name_color,
        name_rect.width - 14,
        minimum_size=12
    )
    surface.blit(name_surface, name_surface.get_rect(center=name_rect.center))

    money_rect = pygame.Rect(name_rect.centerx - 59, name_rect.bottom - 2, 118, 28)
    stack = game.npc_stacks[index] if index < len(game.npc_stacks) else 0
    draw_panel(surface, money_rect, (12, 14, 16, 242), (90, 95, 100), radius=8, border_width=1)
    money_surface = fonts["small"].render("OUT" if busted else f"${stack:,}", True,
                                           MUTED if busted else (240, 255, 235))
    surface.blit(money_surface, money_surface.get_rect(center=money_rect.center))

    action_rect = pygame.Rect(money_rect.x, money_rect.bottom + 4, money_rect.width, 27)
    action = game.npc_action_texts[index] if index < len(game.npc_action_texts) else ""
    if game.current_stage == "draw" and not folded and not busted and index < len(game.npc_draw_counts):
        count = game.npc_draw_counts[index]
        action = "Stood pat" if count == 0 else f"Drew {count}"
    if busted:
        action = "ELIMINATED"
    elif all_in:
        action = "ALL IN"
    elif folded:
        action = "FOLDED"

    if action:
        draw_panel(surface, action_rect,
                   (58, 50, 16, 235) if all_in else (12, 14, 16, 225),
                   GOLD if all_in else (85, 90, 95), radius=7, border_width=1)
        action_surface = render_text_fit(action, fonts["tiny"],
                                         GOLD if all_in else (225, 225, 215),
                                         action_rect.width - 8, minimum_size=10)
        surface.blit(action_surface, action_surface.get_rect(center=action_rect.center))
def draw_player_hud(surface, game, player_name):
    fonts = get_draw_fonts()
    panel_rect = pygame.Rect(548, 680, 270, 72)

    is_current = game.current_actor == 0 and not game.hand_complete
    is_winner = game.current_stage == "showdown" and 0 in game.winner_indexes

    draw_panel(
        surface, panel_rect, (18, 20, 24, 250),
        GOLD if (is_current or is_winner) else (185, 185, 190),
        radius=12,
        border_width=4 if is_winner else (3 if is_current else 2)
    )

    name_surface = render_text_fit(player_name, fonts["title"], WHITE,
                                   panel_rect.width - 30, minimum_size=18)
    surface.blit(name_surface, name_surface.get_rect(center=(panel_rect.centerx, panel_rect.y + 24)))

    money_rect = pygame.Rect(panel_rect.centerx - 62, panel_rect.y + 43, 124, 23)
    draw_panel(surface, money_rect, (10, 12, 14, 255), (115, 115, 120), radius=9, border_width=1)
    money_surface = fonts["small"].render(f"${game.player_stack:,}", True, (240, 255, 235))
    surface.blit(money_surface, money_surface.get_rect(center=money_rect.center))

    draw_position_badges(surface, game, 0, panel_rect.right + 10, panel_rect.y + 9)

# ==================================================


# ==================================================

def draw_five_card_draw(
        surface,
        mouse_pos,
        game,
        card_fronts,
        card_back,
        draw_submenu_background,
        draw_npc_portrait,
        player_name,
        felt_surface,
        next_hand_seconds=None
):
    global _draw_last_hand_number
    global _draw_selected_card_indexes

    if game.hand_number != _draw_last_hand_number:
        _draw_last_hand_number = game.hand_number
        _draw_selected_card_indexes = set()

    draw_submenu_background(overlay_alpha=110)
    fonts = get_draw_fonts()

    card_fx_kind, card_fx_elapsed = sync_draw_card_fx(game)
    sync_draw_chip_fx_context(game)
    sweep_progress = get_draw_wager_sweep_progress(game)
    sweep_target = (TABLE_RECT.centerx, 250)

    draw_table(surface, felt_surface)

    draw_poker_logo(
        surface,
        "five_card_draw",
        pygame.Rect(32, 66, 280, 75)
    )

    draw_button(surface, DRAW_OPTIONS_RECT, "OPTIONS", mouse_pos, fonts["tiny"], enabled=True)
    draw_button(surface, DRAW_EXIT_RECT, "EXIT", mouse_pos, fonts["tiny"], enabled=bool(game.hand_complete))

    # Subtle center panel keeps table information readable on custom felts.
    draw_panel(
        surface,
        pygame.Rect(513, 184, 340, 98),
        (0, 0, 0, 88),
        (105, 115, 110),
        radius=10,
        border_width=1
    )

    stage_names = {
        "preflop": "FIRST BETTING ROUND",
        "draw": "DRAW",
        "post_draw": "FINAL BETTING ROUND",
        "showdown": "SHOWDOWN",
        "busted": "SESSION OVER",
    }
    stage_text = stage_names.get(game.current_stage, game.current_stage.upper())
    stage_surface = fonts["small"].render(stage_text, True, GOLD)
    surface.blit(stage_surface, stage_surface.get_rect(center=(683, 202)))

    blind_surface = fonts["tiny"].render(
        f"Blinds: ${game.small_blind:,} / ${game.big_blind:,}", True, (225, 225, 230)
    )
    surface.blit(blind_surface, blind_surface.get_rect(center=(683, 228)))

    display_pot = game.get_display_pot_amount() if hasattr(game, "get_display_pot_amount") else game.pot
    pot_base_unit = max(
        1,
        int(
            getattr(
                game,
                "big_blind",
                1
            )
        )
    )

    draw_draw_pot_stack(
        surface,
        display_pot,
        (
            683,
            244
        ),
        pot_base_unit
    )

    pot_surface = fonts["small"].render(f"Pot: ${display_pot:,}", True, WHITE)
    surface.blit(pot_surface, pot_surface.get_rect(center=(683, 266)))

    npc_anchors = [(180, 325), (450, 120), (900, 120), (1090, 325)]
    for index, npc in enumerate(game.npcs[:4]):
        draw_npc_seat(
            surface, game, index, npc, npc_anchors[index],
            card_fronts, card_back, draw_npc_portrait,
            card_fx_kind=card_fx_kind,
            card_fx_elapsed=card_fx_elapsed
        )

    wager_positions = [(365, 360), (525, 285), (842, 285), (1000, 360)]
    if game.current_stage != "showdown":
        for index in range(min(4, len(game.npcs))):
            chunks = game.npc_bet_chunks[index] if index < len(game.npc_bet_chunks) else []
            anchor_x, anchor_y = npc_anchors[index]
            draw_animated_wager_chunks(
                surface, chunks, wager_positions[index][0], wager_positions[index][1],
                game.small_blind, origin=(anchor_x + 82, anchor_y + 58),
                animation_key=f"npc_{index}", sweep_target=sweep_target,
                sweep_progress=sweep_progress
            )

        # Five cards span much farther right than Hold'em's two-card hand.
        # Keep the player's wager just beyond the spread so the chip amount
        # never disappears underneath the fifth card.
        draw_animated_wager_chunks(
            surface, game.player_bet_chunks, 1045, 500, game.small_blind,
            origin=(683, 714), animation_key="player",
            sweep_target=sweep_target, sweep_progress=sweep_progress
        )

    card_rects = get_player_card_rects()
    for index, card in enumerate(game.player_hand[:5]):
        rect = card_rects[index]
        selected = index in _draw_selected_card_indexes and game.current_stage == "draw"

        shadow = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 85), shadow.get_rect(), border_radius=7)
        surface.blit(shadow, (rect.x + 4, rect.y + 5))

        if selected:
            draw_panel(surface, rect.inflate(8, 8), (105, 30, 30, 105), (240, 105, 95), radius=10, border_width=2)

        animate = card_fx_kind in ("deal", "redraw")
        delay = (20 + index) * 32 if card_fx_kind == "deal" else index * 55
        progress = _fx_progress(card_fx_elapsed, delay=delay, duration=200)

        if animate and progress < 1.0:
            draw_popping_card_face(surface, card, rect.x, rect.y, card_fronts, rect.width, rect.height, progress)
        else:
            draw_card_face(surface, card, rect.x, rect.y, card_fronts, rect.width, rect.height)

        if (
                game.current_stage in ("post_draw", "showdown")
                and index in getattr(game, "player_last_draw_indexes", [])
        ):
            pygame.draw.line(
                surface,
                GOLD,
                (rect.left + 10, rect.bottom + 3),
                (rect.right - 10, rect.bottom + 3),
                3
            )

        if selected:
            tag_rect = pygame.Rect(rect.centerx - 32, rect.bottom + 4, 64, 20)
            pygame.draw.rect(surface, (145, 40, 40), tag_rect, border_radius=6)
            pygame.draw.rect(surface, (245, 170, 160), tag_rect, 1, border_radius=6)
            discard_surface = fonts["micro"].render("DISCARD", True, WHITE)
            surface.blit(discard_surface, discard_surface.get_rect(center=tag_rect.center))

    if game.current_stage == "showdown" and not game.player_folded:
        hand_name = game.get_player_hand_name()
        if hand_name:
            hand_surface = fonts["small"].render(f"Your hand: {hand_name}", True, GOLD)
            surface.blit(hand_surface, hand_surface.get_rect(center=(683, 505)))

    if game.result_text and game.current_stage != "showdown":
        result_surface = render_text_fit(game.result_text, fonts["small"], WHITE, 650, minimum_size=12)
        surface.blit(result_surface, result_surface.get_rect(center=(683, 470)))

    if game.player_action_text and game.current_stage != "showdown":
        action_surface = fonts["tiny"].render(game.player_action_text, True, GOLD)
        surface.blit(action_surface, action_surface.get_rect(center=(683, 662)))

    draw_player_hud(surface, game, player_name)

    draw_draw_payout_animation(
        surface,
        game,
        npc_anchors
    )

    draw_draw_showdown_banner(
        surface,
        game
    )

    status = poker_session_status(game, getattr(game, 'career_session_rated', True))
    status_image = pygame.font.Font(None, 23).render(status, True, (231, 239, 234))
    surface.blit(status_image, (22, 553))
    draw_log_panel(surface, game)

    # Like Hold'em, show the player's current made hand just above controls.
    current_hand = game.get_player_hand_name() if len(game.player_hand) == 5 else None
    if current_hand and game.current_stage != "draw":
        hand_surface = fonts["small"].render(current_hand, True, WHITE)
        surface.blit(hand_surface, hand_surface.get_rect(bottomright=(DRAW_ACTION_PANEL_RECT.right - 6, DRAW_ACTION_PANEL_RECT.y - 8)))

    draw_action_panel(surface, mouse_pos, game, next_hand_seconds=next_hand_seconds)

    # Final speech-bubble overlay pass keeps chatter above cards and chips.
    if is_poker_chat_popups_enabled():
        for index, _npc in enumerate(game.npcs[:4]):
            anchor_x, anchor_y = npc_anchors[index]
            name_rect = pygame.Rect(anchor_x, anchor_y + 6, 165, 40)
            _draw_speech_overlay.draw(
                surface,
                game.get_table_player_name(index + 1),
                name_rect,
                fonts["tiny"]
            )

