from career_session_summary import poker_session_status
import math

import pygame

from poker_speech import PokerSpeechOverlay


# ==================================================
# ACTIONS
# ==================================================

ACTION_RETURN = "return"
ACTION_FOLD = "fold"
ACTION_CHECK_CALL = "check_call"
ACTION_BET_RAISE = "bet_raise"
ACTION_NEXT_HAND = "next_hand"
ACTION_OPTIONS = "options"


# ==================================================
# COLORS
# ==================================================

WHITE = (245, 245, 245)
MUTED = (185, 190, 190)
GOLD = (235, 190, 70)
TABLE_EDGE = (95, 65, 35)
PANEL_DARK = (18, 20, 24)


# ==================================================
# LAYOUT
# ==================================================

STUD_LOG_RECT = pygame.Rect(
    18,
    610,
    410,
    140
)

STUD_ACTION_PANEL_RECT = pygame.Rect(
    925,
    610,
    420,
    140
)

STUD_FOLD_RECT = pygame.Rect(
    942,
    635,
    112,
    42
)

STUD_CALL_RECT = pygame.Rect(
    1064,
    635,
    132,
    42
)

STUD_RAISE_RECT = pygame.Rect(
    1206,
    635,
    122,
    42
)

STUD_NEXT_HAND_RECT = pygame.Rect(
    1010,
    650,
    250,
    48
)

STUD_OPTIONS_RECT = pygame.Rect(
    1180,
    20,
    90,
    38
)

STUD_EXIT_RECT = pygame.Rect(
    1280,
    20,
    68,
    38
)

STUD_BUY_IN_PANEL_RECT = pygame.Rect(
    283,
    180,
    800,
    410
)

STUD_BUY_IN_25_RECT = pygame.Rect(
    318,
    330,
    165,
    100
)

STUD_BUY_IN_50_RECT = pygame.Rect(
    506,
    330,
    165,
    100
)

STUD_BUY_IN_75_RECT = pygame.Rect(
    694,
    330,
    165,
    100
)

STUD_BUY_IN_MAX_RECT = pygame.Rect(
    882,
    330,
    165,
    100
)

STUD_BUY_IN_BACK_RECT = pygame.Rect(
    558,
    505,
    250,
    44
)

TABLE_RECT = pygame.Rect(
    233,
    105,
    900,
    460
)

INNER_TABLE_RECT = TABLE_RECT.inflate(
    -30,
    -30
)


# ==================================================
# UI STATE
# ==================================================

_stud_fonts = None
_stud_chip_images = None

_stud_chat_history = []
_stud_speech_overlay = PokerSpeechOverlay()
_stud_active_tab = "log"
_stud_log_scroll = 0
_stud_chat_scroll = 0
_stud_chat_unread = False


# ==================================================
# FONTS / BASIC DRAWING
# ==================================================

def get_stud_fonts():
    global _stud_fonts

    if _stud_fonts is None:
        if not pygame.font.get_init():
            pygame.font.init()

        _stud_fonts = {
            "title": pygame.font.SysFont(
                "cambria",
                31,
                bold=True
            ),
            "name": pygame.font.SysFont(
                "cambria",
                20,
                bold=True
            ),
            "small": pygame.font.SysFont(
                "cambria",
                17,
                bold=True
            ),
            "tiny": pygame.font.SysFont(
                "cambria",
                15,
                bold=True
            ),
            "micro": pygame.font.SysFont(
                "cambria",
                12,
                bold=True
            ),
        }

    return _stud_fonts


def draw_panel(
        surface,
        rect,
        fill=(18, 20, 24, 235),
        border=(145, 150, 155),
        radius=10,
        border_width=2
):
    panel = pygame.Surface(
        rect.size,
        pygame.SRCALPHA
    )

    pygame.draw.rect(
        panel,
        fill,
        panel.get_rect(),
        border_radius=radius
    )

    gloss_layer = pygame.Surface(
        rect.size,
        pygame.SRCALPHA
    )

    gloss_rect = pygame.Rect(
        3,
        3,
        max(
            1,
            rect.width - 6
        ),
        max(
            8,
            rect.height // 2 - 3
        )
    )

    pygame.draw.rect(
        gloss_layer,
        (255, 255, 255, 18),
        gloss_rect,
        border_radius=max(
            4,
            radius - 2
        )
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

    surface.blit(
        panel,
        rect.topleft
    )


def render_text_fit(
        text,
        font,
        color,
        max_width,
        minimum_size=10
):
    text = str(text)

    rendered = font.render(
        text,
        True,
        color
    )

    if rendered.get_width() <= max_width:
        return rendered

    current_size = max(
        minimum_size,
        font.get_height() - 2
    )

    while current_size >= minimum_size:
        smaller = pygame.font.SysFont(
            "cambria",
            current_size,
            bold=True
        )

        rendered = smaller.render(
            text,
            True,
            color
        )

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
    }.get(
        card.get("suit")
    )

    if suit_letter is None:
        return None

    return (
        f"{card.get('rank')}"
        f"{suit_letter}"
    )


def draw_card_face(
        surface,
        card,
        x,
        y,
        card_fronts,
        width,
        height
):
    key = get_card_key(
        card
    )

    if (
            key is None
            or key not in card_fronts
    ):
        return

    image = pygame.transform.smoothscale(
        card_fronts[key],
        (
            width,
            height
        )
    )

    surface.blit(
        image,
        (x, y)
    )


def draw_card_back(
        surface,
        card_back,
        x,
        y,
        width,
        height
):
    if card_back is None:
        return

    image = pygame.transform.smoothscale(
        card_back,
        (
            width,
            height
        )
    )

    surface.blit(
        image,
        (x, y)
    )


# ==================================================
# CHIP HELPERS
# ==================================================

def get_stud_chip_images():
    global _stud_chip_images

    if _stud_chip_images is None:
        _stud_chip_images = {
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

    return _stud_chip_images


def get_chip_key(
        amount,
        base_unit
):
    base_unit = max(
        1,
        int(base_unit)
    )

    if amount >= base_unit * 20:
        return "black"

    if amount >= base_unit * 10:
        return "yellow"

    if amount >= base_unit * 5:
        return "green"

    if amount >= base_unit * 2:
        return "blue"

    return "red"


def draw_wager_marker(
        surface,
        amount,
        center,
        base_unit
):
    if amount <= 0:
        return

    fonts = get_stud_fonts()
    chips = get_stud_chip_images()

    chip_key = get_chip_key(
        amount,
        base_unit
    )

    chip = chips.get(
        chip_key
    )

    if chip is not None:
        chip = pygame.transform.smoothscale(
            chip,
            (26, 26)
        )

        surface.blit(
            chip,
            chip.get_rect(
                center=center
            )
        )

    amount_surface = fonts[
        "tiny"
    ].render(
        f"${amount:,}",
        True,
        WHITE
    )

    surface.blit(
        amount_surface,
        amount_surface.get_rect(
            center=(
                center[0],
                center[1] + 25
            )
        )
    )



# ==================================================
# POT DISPLAY / PAYOUT ANIMATION
# ==================================================

_stud_payout_fx_key = None
_stud_payout_fx_started_at = 0

STUD_PAYOUT_FX_DURATION = 1050


def _stud_pot_chip_count(
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


def draw_stud_pot_stack(
        surface,
        amount,
        center,
        base_unit
):
    amount = max(
        0,
        int(amount)
    )

    count = _stud_pot_chip_count(
        amount,
        base_unit
    )

    if count <= 0:
        return

    chips = get_stud_chip_images()
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


def get_stud_payout_fx_progress(
        game
):
    global _stud_payout_fx_key
    global _stud_payout_fx_started_at

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

    if key != _stud_payout_fx_key:
        _stud_payout_fx_key = key
        _stud_payout_fx_started_at = now

    progress = (
        now
        - _stud_payout_fx_started_at
    ) / STUD_PAYOUT_FX_DURATION

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


def draw_stud_payout_animation(
        surface,
        game,
        npc_anchors
):
    progress = get_stud_payout_fx_progress(
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
                "small_bet",
                1
            )
        )
    )

    chips = get_stud_chip_images()
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
            _stud_pot_chip_count(
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


def draw_stud_showdown_banner(
        surface,
        game
):
    if (
            game.current_stage != "showdown"
            or not game.result_text
    ):
        return

    fonts = get_stud_fonts()

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

STUD_CHIP_FX_DURATION = 280
STUD_WAGER_SWEEP_DELAY = 180
STUD_WAGER_SWEEP_DURATION = 680

_stud_card_fx_hand_number = -1
_stud_card_fx_stage = None
_stud_card_fx_kind = None
_stud_card_fx_started_at = 0

_stud_chip_fx_hand_number = -1
_stud_chip_fx_stage = None
_stud_chip_fx_signatures = {}
_stud_chip_fx_started_at = {}
_stud_chip_fx_indexes = {}
_stud_wager_sweep_key = None
_stud_wager_sweep_started_at = 0


def _ease_out_cubic(progress):
    progress = max(0.0, min(1.0, float(progress)))
    return 1.0 - pow(1.0 - progress, 3)


def _fx_progress(elapsed, delay=0, duration=180):
    if elapsed <= delay:
        return 0.0
    return max(0.0, min(1.0, (elapsed - delay) / max(1, duration)))


def sync_stud_card_fx(game):
    global _stud_card_fx_hand_number
    global _stud_card_fx_stage
    global _stud_card_fx_kind
    global _stud_card_fx_started_at

    now = pygame.time.get_ticks()
    hand_number = getattr(game, "hand_number", 0)
    stage = getattr(game, "current_stage", None)

    if hand_number != _stud_card_fx_hand_number:
        _stud_card_fx_hand_number = hand_number
        _stud_card_fx_stage = stage
        _stud_card_fx_kind = "deal"
        _stud_card_fx_started_at = now
    elif stage != _stud_card_fx_stage:
        _stud_card_fx_stage = stage
        if stage == "fourth":
            _stud_card_fx_kind = "street"
        elif stage in ("fifth", "sixth", "seventh"):
            _stud_card_fx_kind = "street"
        elif stage == "showdown":
            _stud_card_fx_kind = "showdown"
        else:
            _stud_card_fx_kind = None
        _stud_card_fx_started_at = now

    elapsed = now - _stud_card_fx_started_at
    if elapsed > 1500:
        return None, elapsed
    return _stud_card_fx_kind, elapsed


def _stud_scaled_card(surface, image, x, y, width, height, progress):
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
    _stud_scaled_card(surface, image, x, y, width, height, progress)


def draw_popping_card_back(surface, card_back, x, y, width, height, progress):
    if card_back is None:
        return
    _stud_scaled_card(surface, card_back, x, y, width, height, progress)


def sync_stud_chip_fx_context(game):
    global _stud_chip_fx_hand_number
    global _stud_chip_fx_stage
    global _stud_chip_fx_signatures
    global _stud_chip_fx_started_at
    global _stud_chip_fx_indexes
    global _stud_wager_sweep_key
    global _stud_wager_sweep_started_at

    hand_number = getattr(game, "hand_number", 0)
    stage = getattr(game, "current_stage", None)

    if hand_number != _stud_chip_fx_hand_number or stage != _stud_chip_fx_stage:
        _stud_chip_fx_hand_number = hand_number
        _stud_chip_fx_stage = stage
        _stud_chip_fx_signatures = {}
        _stud_chip_fx_started_at = {}
        _stud_chip_fx_indexes = {}
        _stud_wager_sweep_key = None
        _stud_wager_sweep_started_at = 0


def _get_stud_chip_fx(key, chunks):
    global _stud_chip_fx_signatures
    global _stud_chip_fx_started_at
    global _stud_chip_fx_indexes

    signature = tuple(int(v) for v in chunks)
    previous = _stud_chip_fx_signatures.get(key)
    now = pygame.time.get_ticks()

    if previous is None:
        _stud_chip_fx_signatures[key] = signature
        if signature:
            _stud_chip_fx_indexes[key] = len(signature) - 1
            _stud_chip_fx_started_at[key] = now
    elif previous != signature:
        old_len = len(previous)
        _stud_chip_fx_signatures[key] = signature
        if len(signature) > old_len:
            _stud_chip_fx_indexes[key] = len(signature) - 1
            _stud_chip_fx_started_at[key] = now
        else:
            _stud_chip_fx_indexes.pop(key, None)
            _stud_chip_fx_started_at.pop(key, None)

    idx = _stud_chip_fx_indexes.get(key)
    started = _stud_chip_fx_started_at.get(key)
    if idx is None or started is None:
        return None, 1.0

    progress = max(0.0, min(1.0, (now - started) / STUD_CHIP_FX_DURATION))
    return idx, progress


def get_stud_wager_sweep_progress(game):
    global _stud_wager_sweep_key
    global _stud_wager_sweep_started_at

    if game.current_stage not in getattr(game, "STUD_STAGES", ("third", "fourth", "fifth", "sixth", "seventh")):
        return 0.0

    has_chips = bool(game.player_bet_chunks) or any(bool(c) for c in game.npc_bet_chunks)
    if not has_chips or game.current_actor != -1:
        return 0.0

    key = (getattr(game, "hand_number", 0), game.current_stage)
    now = pygame.time.get_ticks()

    if _stud_wager_sweep_key != key:
        _stud_wager_sweep_key = key
        _stud_wager_sweep_started_at = now

    elapsed = now - _stud_wager_sweep_started_at
    if elapsed < STUD_WAGER_SWEEP_DELAY:
        return 0.0

    progress = (elapsed - STUD_WAGER_SWEEP_DELAY) / STUD_WAGER_SWEEP_DURATION
    return _ease_out_cubic(max(0.0, min(1.0, progress)))


def draw_stud_animated_wager_chunks(
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

    fonts = get_stud_fonts()
    chips = get_stud_chip_images()
    animated_index, progress = _get_stud_chip_fx(animation_key, chunks)
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

def get_seven_card_stud_buy_in_amounts(
        career_cash
):
    career_cash = max(
        0,
        int(career_cash)
    )

    return {
        "25": int(
            career_cash * 0.25
        ),
        "50": int(
            career_cash * 0.50
        ),
        "75": int(
            career_cash * 0.75
        ),
        "max": career_cash,
    }


def get_seven_card_stud_buy_in_action(
        mouse_pos,
        career_cash,
        minimum_buy_in=100
):
    if mouse_pos is None:
        return None

    if STUD_BUY_IN_BACK_RECT.collidepoint(
            mouse_pos
    ):
        return (
            "back",
            None
        )

    amounts = (
        get_seven_card_stud_buy_in_amounts(
            career_cash
        )
    )

    choices = (
        (
            STUD_BUY_IN_25_RECT,
            amounts["25"]
        ),
        (
            STUD_BUY_IN_50_RECT,
            amounts["50"]
        ),
        (
            STUD_BUY_IN_75_RECT,
            amounts["75"]
        ),
        (
            STUD_BUY_IN_MAX_RECT,
            amounts["max"]
        ),
    )

    for rect, amount in choices:
        if (
                rect.collidepoint(
                    mouse_pos
                )
                and amount >= minimum_buy_in
        ):
            return (
                "buy_in",
                amount
            )

    return None


def draw_seven_card_stud_buy_in(
        surface,
        mouse_pos,
        career_cash,
        draw_submenu_background,
        minimum_buy_in=100
):
    draw_submenu_background(
        overlay_alpha=125
    )

    fonts = get_stud_fonts()

    draw_panel(
        surface,
        STUD_BUY_IN_PANEL_RECT,
        (
            10,
            18,
            18,
            245
        ),
        (
            185,
            190,
            195
        ),
        radius=16
    )

    title = fonts["title"].render(
        "SEVEN-CARD STUD BUY-IN",
        True,
        WHITE
    )

    surface.blit(
        title,
        title.get_rect(
            center=(
                STUD_BUY_IN_PANEL_RECT.centerx,
                225
            )
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
            center=(
                STUD_BUY_IN_PANEL_RECT.centerx,
                275
            )
        )
    )

    amounts = (
        get_seven_card_stud_buy_in_amounts(
            career_cash
        )
    )

    choices = (
        (
            STUD_BUY_IN_25_RECT,
            "25%",
            amounts["25"]
        ),
        (
            STUD_BUY_IN_50_RECT,
            "50%",
            amounts["50"]
        ),
        (
            STUD_BUY_IN_75_RECT,
            "75%",
            amounts["75"]
        ),
        (
            STUD_BUY_IN_MAX_RECT,
            "MAX",
            amounts["max"]
        ),
    )

    for rect, label, amount in choices:
        enabled = (
            amount >= minimum_buy_in
        )

        draw_button(
            surface,
            rect,
            label,
            mouse_pos,
            fonts["name"],
            enabled=enabled
        )

        amount_surface = fonts[
            "small"
        ].render(
            f"${amount:,}",
            True,
            (
                WHITE
                if enabled
                else (
                    130,
                    130,
                    130
                )
            )
        )

        surface.blit(
            amount_surface,
            amount_surface.get_rect(
                center=(
                    rect.centerx,
                    rect.centery + 26
                )
            )
        )

    info = fonts["small"].render(
        (
            "Unused cash stays in your Career wallet. "
            "Stud uses antes, a bring-in, and fixed betting limits."
        ),
        True,
        MUTED
    )

    surface.blit(
        info,
        info.get_rect(
            center=(
                STUD_BUY_IN_PANEL_RECT.centerx,
                466
            )
        )
    )

    if career_cash < minimum_buy_in:
        warning = fonts["small"].render(
            (
                f"At least "
                f"${minimum_buy_in:,} "
                f"is required to play."
            ),
            True,
            (
                235,
                135,
                135
            )
        )

        surface.blit(
            warning,
            warning.get_rect(
                center=(
                    STUD_BUY_IN_PANEL_RECT.centerx,
                    495
                )
            )
        )

    draw_button(
        surface,
        STUD_BUY_IN_BACK_RECT,
        "BACK",
        mouse_pos,
        fonts["small"],
        enabled=True
    )


# ==================================================
# SESSION / CHAT / LOG STATE
# ==================================================

def reset_seven_card_stud_ui_session():
    global _stud_chat_history
    global _stud_active_tab
    global _stud_log_scroll
    global _stud_chat_scroll
    global _stud_chat_unread

    _stud_chat_history = []
    _stud_speech_overlay.clear()
    _stud_active_tab = "log"
    _stud_log_scroll = 0
    _stud_chat_scroll = 0
    _stud_chat_unread = False


def add_seven_card_stud_chat_message(
        speaker,
        message
):
    global _stud_chat_unread
    global _stud_chat_scroll

    if not message:
        return

    if speaker:
        _stud_speech_overlay.post(
            speaker,
            message
        )

    text = (
        f"{speaker}: {message}"
        if speaker
        else str(message)
    )

    _stud_chat_history.append(
        text
    )

    if len(_stud_chat_history) > 100:
        del _stud_chat_history[
            :-100
        ]

    _stud_chat_scroll = 0

    if _stud_active_tab != "chat":
        _stud_chat_unread = True


def handle_seven_card_stud_panel_click(
        mouse_pos
):
    global _stud_active_tab
    global _stud_chat_unread

    if mouse_pos is None:
        return False

    log_rect = pygame.Rect(
        STUD_LOG_RECT.x + 12,
        STUD_LOG_RECT.y + 10,
        100,
        28
    )

    chat_rect = pygame.Rect(
        STUD_LOG_RECT.x + 118,
        STUD_LOG_RECT.y + 10,
        76,
        28
    )

    if log_rect.collidepoint(
            mouse_pos
    ):
        _stud_active_tab = "log"
        return True

    if chat_rect.collidepoint(
            mouse_pos
    ):
        _stud_active_tab = "chat"
        _stud_chat_unread = False
        return True

    return False


def scroll_seven_card_stud_panel(
        wheel_y,
        game
):
    global _stud_log_scroll
    global _stud_chat_scroll

    visible = 3

    if _stud_active_tab == "chat":
        max_scroll = max(
            0,
            len(_stud_chat_history)
            - visible
        )

        _stud_chat_scroll = max(
            0,
            min(
                _stud_chat_scroll
                + wheel_y,
                max_scroll
            )
        )

    else:
        lines = (
            game.get_hand_history_lines()
        )

        max_scroll = max(
            0,
            len(lines)
            - visible
        )

        _stud_log_scroll = max(
            0,
            min(
                _stud_log_scroll
                + wheel_y,
                max_scroll
            )
        )


# ==================================================
# ACTION HELPERS
# ==================================================

def get_seven_card_stud_action(
        mouse_pos,
        game
):
    if mouse_pos is None:
        return None

    if STUD_OPTIONS_RECT.collidepoint(mouse_pos):
        return ACTION_OPTIONS

    if STUD_EXIT_RECT.collidepoint(
            mouse_pos
    ):
        return ACTION_RETURN

    if game.hand_complete:
        if STUD_NEXT_HAND_RECT.collidepoint(
                mouse_pos
        ):
            return ACTION_NEXT_HAND

        return None

    if (
            game.current_stage
            not in game.STUD_STAGES
            or game.current_actor != 0
            or game.player_folded
            or game.player_all_in
            or game.player_stack <= 0
    ):
        return None

    if (
            STUD_FOLD_RECT.collidepoint(
                mouse_pos
            )
            and game.can_player_act_now()
    ):
        return ACTION_FOLD

    if STUD_CALL_RECT.collidepoint(
            mouse_pos
    ):
        if (
                game.can_player_check()
                or game.can_player_call()
        ):
            return ACTION_CHECK_CALL

    if STUD_RAISE_RECT.collidepoint(
            mouse_pos
    ):
        if game.current_bet <= 0:
            if game.can_player_act_now():
                return ACTION_BET_RAISE

        elif game.can_player_raise():
            return ACTION_BET_RAISE

    return None


# ==================================================
# LOG / CHAT
# ==================================================

def draw_stud_tab_button(
        surface,
        rect,
        text,
        active=False,
        unread=False
):
    fonts = get_stud_fonts()

    if unread and not active:
        phase = (pygame.time.get_ticks() % 1200) / 1200.0
        pulse = 0.5 + 0.5 * math.sin(phase * math.pi * 2)
        fill = (int(92 + 26 * pulse), int(72 + 20 * pulse), 30, 235)
        border = (255, int(195 + 45 * pulse), 80)
    elif active:
        fill = (58, 82, 108, 235)
        border = (165, 205, 240)
    else:
        fill = (55, 58, 64, 225)
        border = (125, 130, 138)

    draw_panel(
        surface,
        rect,
        fill,
        border,
        radius=9,
        border_width=2
    )

    label = fonts["micro"].render(text, True, WHITE)
    surface.blit(label, label.get_rect(center=rect.center))


def draw_log_panel(
        surface,
        game
):
    fonts = get_stud_fonts()

    draw_panel(
        surface,
        STUD_LOG_RECT,
        (
            10,
            24,
            18,
            240
        ),
        (
            170,
            180,
            178
        ),
        radius=12
    )

    log_tab_rect = pygame.Rect(
        STUD_LOG_RECT.x + 12,
        STUD_LOG_RECT.y + 10,
        100,
        28
    )

    chat_tab_rect = pygame.Rect(
        STUD_LOG_RECT.x + 118,
        STUD_LOG_RECT.y + 10,
        76,
        28
    )

    draw_stud_tab_button(
        surface,
        log_tab_rect,
        "GAME LOG",
        active=(_stud_active_tab == "log"),
        unread=False
    )

    draw_stud_tab_button(
        surface,
        chat_tab_rect,
        "CHAT",
        active=(_stud_active_tab == "chat"),
        unread=(
            _stud_chat_unread
            and _stud_active_tab != "chat"
        )
    )

    if _stud_active_tab == "chat":
        lines = list(
            _stud_chat_history
        )
        scroll = _stud_chat_scroll
    else:
        lines = (
            game.get_hand_history_lines()
        )
        scroll = _stud_log_scroll

    visible_count = (
        4
        if _stud_active_tab == "chat"
        else 3
    )
    line_step = (
        19
        if _stud_active_tab == "chat"
        else 29
    )

    max_scroll = max(
        0,
        len(lines)
        - visible_count
    )

    scroll = max(
        0,
        min(
            scroll,
            max_scroll
        )
    )

    start = max(
        0,
        len(lines)
        - visible_count
        - scroll
    )

    visible_lines = lines[
        start:
        start + visible_count
    ]

    y = (
        STUD_LOG_RECT.y + 52
    )

    for line in visible_lines:
        text_surface = render_text_fit(
            line,
            fonts["tiny"],
            (
                232,
                234,
                230
            ),
            STUD_LOG_RECT.width - 28,
            minimum_size=10
        )

        surface.blit(
            text_surface,
            (
                STUD_LOG_RECT.x + 14,
                y
            )
        )

        y += line_step


# ==================================================
# TABLE / BADGES
# ==================================================

def draw_table(
        surface,
        felt_surface
):
    pygame.draw.ellipse(
        surface,
        TABLE_EDGE,
        TABLE_RECT
    )

    pygame.draw.ellipse(
        surface,
        (
            245,
            245,
            235
        ),
        TABLE_RECT.inflate(
            -10,
            -10
        ),
        2
    )

    if felt_surface is not None:
        felt = pygame.transform.smoothscale(
            felt_surface,
            INNER_TABLE_RECT.size
        )

        mask = pygame.Surface(
            INNER_TABLE_RECT.size,
            pygame.SRCALPHA
        )

        pygame.draw.ellipse(
            mask,
            (
                255,
                255,
                255,
                255
            ),
            mask.get_rect()
        )

        felt_copy = pygame.Surface(
            INNER_TABLE_RECT.size,
            pygame.SRCALPHA
        )

        felt_copy.blit(
            felt,
            (0, 0)
        )

        felt_copy.blit(
            mask,
            (0, 0),
            special_flags=pygame.BLEND_RGBA_MULT
        )

        surface.blit(
            felt_copy,
            INNER_TABLE_RECT
        )

    else:
        pygame.draw.ellipse(
            surface,
            (
                0,
                132,
                24
            ),
            INNER_TABLE_RECT
        )


def draw_bring_in_badge(
        surface,
        game,
        player_index,
        x,
        y
):
    if game.current_stage != "third":
        return

    if (
            game.bring_in_index
            != player_index
    ):
        return

    fonts = get_stud_fonts()

    badge = pygame.Rect(
        x,
        y,
        34,
        22
    )

    pygame.draw.rect(
        surface,
        (
            78,
            55,
            30
        ),
        badge,
        border_radius=8
    )

    pygame.draw.rect(
        surface,
        GOLD,
        badge,
        2,
        border_radius=8
    )

    text = fonts[
        "micro"
    ].render(
        "BI",
        True,
        WHITE
    )

    surface.blit(
        text,
        text.get_rect(
            center=badge.center
        )
    )


# ==================================================
# NPC SEATS
# ==================================================

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
    fonts = get_stud_fonts()
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
            overlay, (5, 5, 5, 205 if busted else 165),
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
        pygame.draw.rect(surface, GOLD, portrait_rect.inflate(6, 6),
                         4 if winner else 3, border_radius=9)

    hand = game.npc_hands[index] if index < len(game.npc_hands) else []
    if not busted:
        card_w, card_h, step_x = 88, 123, 35
        card_count = min(7, len(hand))
        total_width = card_w + max(0, card_count - 1) * step_x
        cards_center_x = anchor_x + 46
        cards_x = cards_center_x - total_width // 2
        cards_y = anchor_y - 132
        reveal_all = game.current_stage == "showdown" and not folded

        for card_index in range(card_count):
            x = cards_x + card_index * step_x
            y = cards_y + (2 if card_index in (0, 6) else 0)
            exposed = reveal_all or game.is_stud_card_exposed(card_index)

            shadow = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(shadow, (0, 0, 0, 75), shadow.get_rect(), border_radius=5)
            surface.blit(shadow, (x + 3, y + 4))

            # On a new street, the newest card gets the strongest pop. Third
            # Street staggers all three starting cards.
            if card_fx_kind == "deal":
                delay = (index * 3 + card_index) * 45
                animate = card_index < 3
            elif card_fx_kind == "street":
                delay = index * 55
                animate = card_index == card_count - 1
            elif card_fx_kind == "showdown":
                delay = (index * 7 + card_index) * 22
                animate = not exposed or reveal_all
            else:
                delay = 0
                animate = False

            progress = _fx_progress(card_fx_elapsed, delay=delay, duration=210)

            if exposed:
                if animate and progress < 1.0:
                    draw_popping_card_face(surface, hand[card_index], x, y, card_fronts, card_w, card_h, progress)
                else:
                    draw_card_face(surface, hand[card_index], x, y, card_fronts, card_w, card_h)
            else:
                if animate and progress < 1.0:
                    draw_popping_card_back(surface, card_back, x, y, card_w, card_h, progress)
                else:
                    draw_card_back(surface, card_back, x, y, card_w, card_h)

            # Stud exposure cue: every face-up/public card gets a gold underline.
            # This includes the Third Street upcard (card index 2).
            if exposed and game.current_stage != "showdown":
                pygame.draw.line(
                    surface,
                    GOLD,
                    (x + 7, y + card_h + 2),
                    (x + card_w - 7, y + card_h + 2),
                    3,
                )

            if folded:
                fold_tint = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                fold_tint.fill((105, 105, 105, 185))
                surface.blit(fold_tint, (x, y))

    draw_bring_in_badge(surface, game, index + 1, portrait_rect.left - 31, portrait_rect.top + 4)

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

    _stud_speech_overlay.draw(
        surface,
        game.get_table_player_name(index + 1),
        name_rect,
        fonts["tiny"]
    )

    money_rect = pygame.Rect(name_rect.centerx - 59, name_rect.bottom - 2, 118, 28)
    stack = game.npc_stacks[index] if index < len(game.npc_stacks) else 0
    draw_panel(surface, money_rect, (12, 14, 16, 242), (90, 95, 100), radius=8, border_width=1)
    money_surface = fonts["small"].render("OUT" if busted else f"${stack:,}", True,
                                           MUTED if busted else (240, 255, 235))
    surface.blit(money_surface, money_surface.get_rect(center=money_rect.center))

    action_rect = pygame.Rect(money_rect.x, money_rect.bottom + 4, money_rect.width, 27)
    action = game.npc_action_texts[index] if index < len(game.npc_action_texts) else ""
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

# ==================================================


# ==================================================

def draw_player_hud(surface, game, player_name):
    fonts = get_stud_fonts()
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

    draw_bring_in_badge(surface, game, 0, panel_rect.right + 10, panel_rect.y + 9)

# ==================================================


# ==================================================

def draw_action_panel(
        surface,
        mouse_pos,
        game,
        next_hand_seconds=None
):
    fonts = get_stud_fonts()

    draw_panel(surface, STUD_ACTION_PANEL_RECT, (10, 15, 15, 235), (115, 125, 120), radius=12)

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
            if next_hand_seconds is not None and next_hand_seconds > 0:
                label += f" ({next_hand_seconds})"
            enabled = (
                game.player_stack > 0
                and not game.player_busted
            )

        draw_button(
            surface,
            STUD_NEXT_HAND_RECT,
            label,
            mouse_pos,
            fonts["small"],
            enabled=enabled,
            attention=enabled
        )
        return

    if game.player_all_in or game.player_stack <= 0:
        info = fonts["small"].render("ALL IN - dealing remaining streets", True, GOLD)
        surface.blit(info, info.get_rect(center=STUD_ACTION_PANEL_RECT.center))
        return

    player_turn = (
        game.current_actor == 0
        and game.current_stage in game.STUD_STAGES
        and not game.player_folded
    )

    amount_to_call = game.get_player_amount_to_call()
    fold_enabled = player_turn and game.can_player_act_now()
    call_enabled = player_turn and (game.can_player_check() or game.can_player_call())
    raise_enabled = player_turn and ((game.current_bet <= 0 and game.can_player_act_now()) or game.can_player_raise())

    call_label = f"CALL ${amount_to_call:,}" if amount_to_call > 0 else "CHECK"
    target = game.get_player_fixed_bet_or_raise_to()
    if game.current_bet <= 0:
        raise_label = f"BET ${target:,}"
    elif game.current_stage == "third" and game.current_bet < game.small_bet:
        raise_label = f"COMPLETE ${target:,}"
    else:
        raise_label = f"RAISE ${target:,}"

    # Match Hold'em's control row placement.
    fold_rect = pygame.Rect(942, 622, 112, 40)
    call_rect = pygame.Rect(1064, 622, 132, 40)
    raise_rect = pygame.Rect(1206, 622, 122, 40)

    draw_button(surface, fold_rect, "FOLD", mouse_pos, fonts["small"], enabled=fold_enabled)
    draw_button(surface, call_rect, call_label, mouse_pos, fonts["small"], enabled=call_enabled)
    draw_button(surface, raise_rect, raise_label, mouse_pos, fonts["tiny"], enabled=raise_enabled,
                attention=raise_enabled and game.current_bet <= 0)

    pygame.draw.line(
        surface, (85, 90, 92),
        (STUD_ACTION_PANEL_RECT.x + 18, STUD_ACTION_PANEL_RECT.y + 62),
        (STUD_ACTION_PANEL_RECT.right - 18, STUD_ACTION_PANEL_RECT.y + 62), 1
    )

    if player_turn:
        status_text = f"Fixed limit: ${game.small_bet:,} early / ${game.big_bet:,} late"
    elif game.current_actor == -1:
        status_text = "Dealing next street..."
    else:
        status_text = "Waiting for opponent..."

    status = fonts["tiny"].render(status_text, True, MUTED)
    surface.blit(status, status.get_rect(center=(STUD_ACTION_PANEL_RECT.centerx, STUD_ACTION_PANEL_RECT.y + 92)))

    if game.raises_this_round >= game.max_raises_per_round:
        cap = fonts["micro"].render("Raise cap reached for this street.", True, GOLD)
        surface.blit(cap, cap.get_rect(center=(STUD_ACTION_PANEL_RECT.centerx, STUD_ACTION_PANEL_RECT.y + 118)))

# ==================================================


# ==================================================

def draw_seven_card_stud(
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
    draw_submenu_background(overlay_alpha=110)
    fonts = get_stud_fonts()

    card_fx_kind, card_fx_elapsed = sync_stud_card_fx(game)
    sync_stud_chip_fx_context(game)
    sweep_progress = get_stud_wager_sweep_progress(game)
    sweep_target = (TABLE_RECT.centerx, 250)

    draw_table(surface, felt_surface)

    title = fonts["small"].render("SEVEN-CARD STUD", True, WHITE)
    surface.blit(title, (22, 580))

    draw_button(surface, STUD_OPTIONS_RECT, "OPTIONS", mouse_pos, fonts["tiny"], enabled=True)
    draw_button(surface, STUD_EXIT_RECT, "EXIT", mouse_pos, fonts["tiny"], enabled=True)

    draw_panel(
        surface,
        pygame.Rect(493, 184, 380, 98),
        (0, 0, 0, 88),
        (105, 115, 110),
        radius=10,
        border_width=1
    )

    stage_names = {
        "third": "THIRD STREET",
        "fourth": "FOURTH STREET",
        "fifth": "FIFTH STREET",
        "sixth": "SIXTH STREET",
        "seventh": "SEVENTH STREET",
        "showdown": "SHOWDOWN",
        "busted": "SESSION OVER",
    }
    stage_surface = fonts["small"].render(stage_names.get(game.current_stage, game.current_stage.upper()), True, GOLD)
    surface.blit(stage_surface, stage_surface.get_rect(center=(683, 202)))

    limits_surface = fonts["tiny"].render(
        f"Ante ${game.ante_amount:,}  |  Bring-in ${game.bring_in_amount:,}  |  Limits ${game.small_bet:,}/${game.big_bet:,}",
        True, (225, 225, 230)
    )
    surface.blit(limits_surface, limits_surface.get_rect(center=(683, 228)))

    display_pot = game.get_display_pot_amount() if hasattr(game, "get_display_pot_amount") else game.pot
    pot_base_unit = max(
        1,
        int(
            getattr(
                game,
                "small_bet",
                1
            )
        )
    )

    draw_stud_pot_stack(
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

    npc_anchors = [(180, 430), (320, 190), (1020, 190), (1090, 430)]
    for index, npc in enumerate(game.npcs[:4]):
        draw_npc_seat(
            surface, game, index, npc, npc_anchors[index], card_fronts, card_back,
            draw_npc_portrait, card_fx_kind=card_fx_kind, card_fx_elapsed=card_fx_elapsed
        )

    wager_positions = [(390, 445), (525, 285), (842, 285), (970, 445)]
    if game.current_stage != "showdown":
        for index in range(min(4, len(game.npcs))):
            chunks = game.npc_bet_chunks[index] if index < len(game.npc_bet_chunks) else []
            anchor_x, anchor_y = npc_anchors[index]
            draw_stud_animated_wager_chunks(
                surface, chunks, wager_positions[index][0], wager_positions[index][1],
                game.small_bet, origin=(anchor_x + 82, anchor_y + 58),
                animation_key=f"npc_{index}", sweep_target=sweep_target,
                sweep_progress=sweep_progress
            )

        draw_stud_animated_wager_chunks(
            surface, game.player_bet_chunks, 815, 520, game.small_bet,
            origin=(683, 714), animation_key="player",
            sweep_target=sweep_target, sweep_progress=sweep_progress
        )

    # Larger, more intentional seven-card player spread.
    card_w, card_h, step_x = 110, 154, 62
    hand = game.player_hand[:7]
    total_width = card_w + max(0, len(hand) - 1) * step_x
    start_x = 683 - total_width // 2
    player_card_y = 502

    for card_index, card in enumerate(hand):
        x = start_x + card_index * step_x
        y = player_card_y

        shadow = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 85), shadow.get_rect(), border_radius=6)
        surface.blit(shadow, (x + 4, y + 5))

        if card_fx_kind == "deal":
            animate = card_index < 3
            delay = (12 + card_index) * 45
        elif card_fx_kind == "street":
            animate = card_index == len(hand) - 1
            delay = 180
        else:
            animate = False
            delay = 0

        progress = _fx_progress(card_fx_elapsed, delay=delay, duration=210)
        if animate and progress < 1.0:
            draw_popping_card_face(surface, card, x, y, card_fronts, card_w, card_h, progress)
        else:
            draw_card_face(surface, card, x, y, card_fronts, card_w, card_h)

        # Gold underline marks every public/showing card. On Third Street the
        # first two cards are private hole cards and the third card is exposed.
        # Fourth through Sixth Street are exposed; Seventh Street is private.
        if (
                game.current_stage != "showdown"
                and game.is_stud_card_exposed(card_index)
        ):
            pygame.draw.line(
                surface,
                GOLD,
                (x + 10, y + card_h + 3),
                (x + card_w - 10, y + card_h + 3),
                3
            )

    if game.result_text and game.current_stage != "showdown":
        result_surface = render_text_fit(game.result_text, fonts["small"], WHITE, 650, minimum_size=12)
        surface.blit(result_surface, result_surface.get_rect(center=(683, 470)))

    if game.player_action_text and game.current_stage != "showdown":
        action_surface = fonts["tiny"].render(game.player_action_text, True, GOLD)
        surface.blit(action_surface, action_surface.get_rect(center=(683, 662)))

    draw_player_hud(surface, game, player_name)

    draw_stud_payout_animation(
        surface,
        game,
        npc_anchors
    )

    draw_stud_showdown_banner(
        surface,
        game
    )

    status = poker_session_status(game, getattr(game, 'career_session_rated', True))
    status_image = pygame.font.Font(None, 23).render(status, True, (231, 239, 234))
    surface.blit(status_image, (22, 553))
    draw_log_panel(surface, game)

    current_hand = game.get_player_hand_name() if len(game.player_hand) >= 5 else None
    if current_hand:
        hand_surface = fonts["small"].render(current_hand, True, WHITE)
        surface.blit(hand_surface, hand_surface.get_rect(bottomright=(STUD_ACTION_PANEL_RECT.right - 6, STUD_ACTION_PANEL_RECT.y - 8)))

    draw_action_panel(surface, mouse_pos, game, next_hand_seconds=next_hand_seconds)


# === POKER CAREER POLISH BATCH: shared Quick Chat / status ribbon ===
from poker_variant_quick_chat import controller_for as _variant_qc_controller_for
_stud_variant_qc = _variant_qc_controller_for("seven_card_stud")
_stud_draw_base = draw_seven_card_stud
_stud_panel_click_base = handle_seven_card_stud_panel_click


def draw_seven_card_stud(*args, **kwargs):
    result = _stud_draw_base(*args, **kwargs)
    surface = args[0] if len(args) > 0 else kwargs.get("surface")
    mouse_pos = args[1] if len(args) > 1 else kwargs.get("mouse_pos")
    game = args[2] if len(args) > 2 else kwargs.get("game")
    if surface is not None and game is not None:
        _stud_variant_qc.draw(surface, mouse_pos, game, STUD_LOG_RECT, add_seven_card_stud_chat_message)
        _stud_variant_qc.draw_status_ribbon(surface, game)
    return result


def handle_seven_card_stud_panel_click(mouse_pos):
    global _stud_active_tab, _stud_chat_unread
    if _stud_variant_qc.handle_click(mouse_pos, add_seven_card_stud_chat_message):
        _stud_active_tab = "chat"
        _stud_chat_unread = False
        return True
    return _stud_panel_click_base(mouse_pos)
