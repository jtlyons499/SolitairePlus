"""Texas Hold'em table UI: the pot stack, chip and wager animations, payouts and the showdown banner.

One part of the Hold'em table UI (see holdem_ui.py, which re-exports every name here).
The animation keys live on the shared _ui holder (holdem_ui_state.py); their starting
values are set here, next to the code that uses them.
"""
from solitaireplus.games.poker.core import collected_uncontested
from solitaireplus.games.poker.recap import pot_explanation, received_total
import math

import pygame

from solitaireplus.ui import text as ui_text
from solitaireplus.games.poker.holdem_ui_state import (
    WHITE,
    _ui,
    get_holdem_fonts,
    get_poker_chip_images,
)
from solitaireplus.games.poker.holdem_ui_widgets import draw_translucent_panel


# ==================================================
# CHIP ANIMATION STATE
# ==================================================

_ui.holdem_chip_fx_hand_number = -1
_ui.holdem_chip_fx_stage = None

_ui.holdem_chip_fx_signatures = {}
_ui.holdem_chip_fx_started_at = {}
_ui.holdem_chip_fx_indexes = {}

HOLDEM_CHIP_FX_DURATION = 280

# ==================================================
# WAGER SWEEP ANIMATION STATE
# ==================================================

_ui.holdem_wager_sweep_key = None
_ui.holdem_wager_sweep_started_at = 0

HOLDEM_WAGER_SWEEP_DELAY = 200
HOLDEM_WAGER_SWEEP_DURATION = 700

# ==================================================
# POT DISPLAY / PAYOUT ANIMATION
# ==================================================

_ui.holdem_payout_fx_key = None
_ui.holdem_payout_fx_started_at = 0

HOLDEM_PAYOUT_FX_DURATION = 1050


def _holdem_chip_key_for_amount(
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


def _holdem_pot_chip_count(
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


def draw_holdem_pot_stack(
        surface,
        amount,
        center,
        base_unit
):
    amount = max(
        0,
        int(amount)
    )

    count = _holdem_pot_chip_count(
        amount,
        base_unit
    )

    if count <= 0:
        return

    chip_images = get_poker_chip_images()
    chip_key = _holdem_chip_key_for_amount(
        amount,
        base_unit
    )
    chip = chip_images.get(
        chip_key
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


def get_holdem_payout_fx_progress(
        holdem_game
):
    if (
            holdem_game.current_stage
            != "showdown"
            or not holdem_game.hand_complete
            or not holdem_game.winner_indexes
            or holdem_game.get_display_pot_amount()
            <= 0
    ):
        return None

    key = (
        getattr(
            holdem_game,
            "hand_number",
            0
        ),
        tuple(
            holdem_game.winner_indexes
        ),
        int(
            holdem_game.get_display_pot_amount()
        )
    )

    now = pygame.time.get_ticks()

    if key != _ui.holdem_payout_fx_key:
        _ui.holdem_payout_fx_key = key
        _ui.holdem_payout_fx_started_at = now

    progress = (
        now
        - _ui.holdem_payout_fx_started_at
    ) / HOLDEM_PAYOUT_FX_DURATION

    progress = max(
        0.0,
        min(
            1.0,
            progress
        )
    )

    return get_holdem_chip_ease(
        progress
    )


def draw_holdem_payout_animation(
        surface,
        holdem_game,
        npc_anchors,
        base_unit
):
    progress = get_holdem_payout_fx_progress(
        holdem_game
    )

    if (
            progress is None
            or progress >= 1.0
    ):
        return

    winners = list(
        holdem_game.winner_indexes
    )

    if not winners:
        return

    amount = max(
        1,
        int(
            holdem_game.get_display_pot_amount()
        )
    )

    chip_images = get_poker_chip_images()
    chip = chip_images.get(
        _holdem_chip_key_for_amount(
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
            696
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
            _holdem_pot_chip_count(
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


def draw_holdem_showdown_banner(
        surface,
        holdem_game
):
    if (
            holdem_game.current_stage
            != "showdown"
            or not holdem_game.result_text
    ):
        return

    fonts = get_holdem_fonts()

    player_won = (
        0 in holdem_game.winner_indexes
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

    # Keep the explanation readable and fit the banner to its contents.
    result = holdem_game.result_text.strip()
    awards = getattr(holdem_game, 'last_pot_awards', [])
    if ' with ' not in result.lower() and 'fold' not in result.lower():
        # A pot nobody else could win beat nobody: the banner names no hand for it.
        explanations = list(dict.fromkeys(pot_explanation(pot, awards) for pot in awards
                                          if not collected_uncontested(pot, awards)))
        if explanations:
            result += ' — ' + '; '.join(explanations)
    font = ui_text.get_font(None, 32)
    rows = ['']
    for word in result.split():
        trial = (rows[-1] + ' ' + word).strip()
        if font.size(trial)[0] > 630 and rows[-1]: rows.append(word)
        else: rows[-1] = trial
    # Keep the table visible; full pot-by-pot explanations remain in Payout details.
    if len(rows) > 3:
        if awards:
            # The same amount as the recap's 'You received': pot payouts plus refunds.
            received = received_total(holdem_game, 0)
            rows = [f"You received ${received:,} • {len(awards)} pot(s) resolved",
                    "See Payout details for winning hands and side pots."]
        else:
            rows = rows[:2] + ["See Payout details for the full result."]
    width = min(666, max(220, max(font.size(row)[0] for row in rows) + 36))
    height = 20 + len(rows)*32
    rect = pygame.Rect(683-width//2, 495-height, width, height)
    draw_translucent_panel(surface, rect, (10, 12, 14, 240), border_color=border, border_width=2, radius=12)
    for index, row in enumerate(rows):
        label = font.render(row, True, WHITE)
        surface.blit(label, label.get_rect(center=(rect.centerx, rect.y+10+32*index+16)))


# ==================================================
# CHIP MOVEMENT ANIMATION
# ==================================================

def sync_holdem_chip_fx_context(
        holdem_game
):

    hand_number = getattr(
        holdem_game,
        "hand_number",
        0
    )

    stage = (
        holdem_game.current_stage
    )

    # ==================================================
    # New hand or new betting street
    # ==================================================

    if (
            hand_number
            != _ui.holdem_chip_fx_hand_number
            or stage
            != _ui.holdem_chip_fx_stage
    ):

        _ui.holdem_chip_fx_hand_number = (
            hand_number
        )

        _ui.holdem_chip_fx_stage = (
            stage
        )

        _ui.holdem_chip_fx_signatures = {}
        _ui.holdem_chip_fx_started_at = {}
        _ui.holdem_chip_fx_indexes = {}

        _ui.holdem_wager_sweep_key = None
        _ui.holdem_wager_sweep_started_at = 0

def get_holdem_chip_fx(
        animation_key,
        chunks
):

    if animation_key is None:
        return None, 1.0

    signature = tuple(
        int(amount)
        for amount in chunks
    )

    previous_signature = (
        _ui.holdem_chip_fx_signatures.get(
            animation_key
        )
    )

    now = pygame.time.get_ticks()

    # ==================================================
    # First contribution for this seat
    # ==================================================

    if previous_signature is None:

        _ui.holdem_chip_fx_signatures[
            animation_key
        ] = signature

        if signature:

            _ui.holdem_chip_fx_indexes[
                animation_key
            ] = (
                len(signature) - 1
            )

            _ui.holdem_chip_fx_started_at[
                animation_key
            ] = now

    # ==================================================
    # New wager contribution appeared
    # ==================================================

    elif signature != previous_signature:

        old_length = len(
            previous_signature
        )

        new_length = len(
            signature
        )

        _ui.holdem_chip_fx_signatures[
            animation_key
        ] = signature

        if new_length > old_length:

            _ui.holdem_chip_fx_indexes[
                animation_key
            ] = (
                new_length - 1
            )

            _ui.holdem_chip_fx_started_at[
                animation_key
            ] = now

        else:

            _ui.holdem_chip_fx_indexes.pop(
                animation_key,
                None
            )

            _ui.holdem_chip_fx_started_at.pop(
                animation_key,
                None
            )

    animated_index = (
        _ui.holdem_chip_fx_indexes.get(
            animation_key
        )
    )

    started_at = (
        _ui.holdem_chip_fx_started_at.get(
            animation_key
        )
    )

    if (
            animated_index is None
            or started_at is None
    ):

        return None, 1.0

    progress = (
        (now - started_at)
        / HOLDEM_CHIP_FX_DURATION
    )

    progress = max(
        0.0,
        min(
            progress,
            1.0
        )
    )

    return (
        animated_index,
        progress
    )


def get_holdem_chip_ease(
        progress
):

    progress = max(
        0.0,
        min(
            progress,
            1.0
        )
    )

    return (
        1.0
        - pow(
            1.0 - progress,
            3
        )
    )

def get_holdem_wager_sweep_progress(
        holdem_game
):

    # ==================================================
    # Only betting streets can sweep
    # ==================================================

    if holdem_game.current_stage not in (
            "preflop",
            "flop",
            "turn",
            "river",
    ):
        return 0.0

    # ==================================================
    # There must actually be chips on the felt
    # ==================================================

    has_player_chips = bool(
        holdem_game.player_bet_chunks
    )

    has_npc_chips = any(
        bool(chunks)
        for chunks
        in holdem_game.npc_bet_chunks
    )

    if not (
            has_player_chips
            or has_npc_chips
    ):
        return 0.0

    # ==================================================
    # main.py sets current_actor to -1 once the
    # betting round is finished and the game is
    # waiting to deal the next street.
    #
    # This is our reliable animation trigger.
    # ==================================================

    if holdem_game.current_actor != -1:
        return 0.0

    hand_number = getattr(
        holdem_game,
        "hand_number",
        0
    )

    sweep_key = (
        hand_number,
        holdem_game.current_stage
    )

    now = pygame.time.get_ticks()

    # ==================================================
    # Start sweep once per street
    # ==================================================

    if (
            _ui.holdem_wager_sweep_key
            != sweep_key
    ):

        _ui.holdem_wager_sweep_key = (
            sweep_key
        )

        _ui.holdem_wager_sweep_started_at = (
            now
        )

    elapsed = (
        now
        - _ui.holdem_wager_sweep_started_at
    )

    # Brief pause after final wager lands.
    if elapsed < HOLDEM_WAGER_SWEEP_DELAY:
        return 0.0

    progress = (
        (
            elapsed
            - HOLDEM_WAGER_SWEEP_DELAY
        )
        / HOLDEM_WAGER_SWEEP_DURATION
    )

    progress = max(
        0.0,
        min(
            progress,
            1.0
        )
    )

    return get_holdem_chip_ease(
        progress
    )

def draw_holdem_chip_chunks(
        game_surface,
        chunks,
        center_x,
        y,
        chip_images,
        base_unit=50,
        origin=None,
        animation_key=None,
        sweep_target=None,
        sweep_progress=0.0
):

    if not chunks:
        return

    # Once they fully reach the pot, hide them.
    if (
            sweep_target is not None
            and sweep_progress >= 1.0
    ):
        return

    holdem_fonts = (
        get_holdem_fonts()
    )

    amount_font = (
        holdem_fonts["tiny"]
    )

    # ==================================================
    # Incoming wager animation
    # ==================================================

    animated_index, progress = (
        get_holdem_chip_fx(
            animation_key,
            chunks
        )
    )

    eased_progress = (
        get_holdem_chip_ease(
            progress
        )
    )

    # ==================================================
    # Chip layout
    # ==================================================

    chip_size = 22
    stack_spacing = 13

    total_width = (
        (len(chunks) - 1)
        * stack_spacing
    )

    start_x = (
        center_x
        - total_width // 2
    )

    # ==================================================
    # Draw each contribution
    # ==================================================

    for chunk_index, amount in enumerate(
            chunks
    ):

        if amount <= 0:
            continue

        # ------------------------------------------
        # Chip color
        # ------------------------------------------

        if amount >= base_unit * 20:
            chip_key = "black"

        elif amount >= base_unit * 10:
            chip_key = "yellow"

        elif amount >= base_unit * 5:
            chip_key = "green"

        elif amount >= base_unit * 2:
            chip_key = "blue"

        else:
            chip_key = "red"

        chip_image = (
            chip_images.get(
                chip_key
            )
        )

        if chip_image is None:
            continue

        # ==================================================
        # Normal wager position
        # ==================================================

        target_x = (
            start_x
            + chunk_index
            * stack_spacing
        )

        target_y = y

        draw_x = target_x
        draw_y = target_y
        draw_size = chip_size

        # ==================================================
        # Newly-added wager slides from seat
        # ==================================================

        if (
                chunk_index
                == animated_index
                and progress < 1.0
                and origin is not None
                and sweep_progress <= 0.0
        ):

            origin_x, origin_y = (
                origin
            )

            draw_x = int(
                origin_x
                + (
                    target_x
                    - origin_x
                )
                * eased_progress
            )

            draw_y = int(
                origin_y
                + (
                    target_y
                    - origin_y
                )
                * eased_progress
            )

            arc = (
                math.sin(
                    progress
                    * math.pi
                )
                * 18
            )

            draw_y -= int(
                arc
            )

            scale = (
                0.78
                + 0.22
                * eased_progress
            )

            draw_size = max(
                10,
                int(
                    chip_size
                    * scale
                )
            )

        # ==================================================
        # Completed wagers sweep toward pot
        # ==================================================

        if (
                sweep_target is not None
                and sweep_progress > 0.0
        ):

            pot_x, pot_y = (
                sweep_target
            )

            draw_x = int(
                target_x
                + (
                    pot_x
                    - target_x
                )
                * sweep_progress
            )

            draw_y = int(
                target_y
                + (
                    pot_y
                    - target_y
                )
                * sweep_progress
            )

            # Slight arc inward
            sweep_arc = (
                math.sin(
                    sweep_progress
                    * math.pi
                )
                * 12
            )

            draw_y -= int(
                sweep_arc
            )

            # Chips shrink a little as they merge
            # into the center pile.
            draw_size = max(
                13,
                int(
                    chip_size
                    * (
                        1.0
                        - 0.30
                        * sweep_progress
                    )
                )
            )

        # ==================================================
        # Draw chip
        # ==================================================

        scaled_chip = (
            pygame.transform.smoothscale(
                chip_image,
                (
                    draw_size,
                    draw_size
                )
            )
        )

        chip_rect = (
            scaled_chip.get_rect(
                center=(
                    draw_x,
                    draw_y
                )
            )
        )

        game_surface.blit(
            scaled_chip,
            chip_rect
        )

    # ==================================================
    # Contribution amount
    #
    # Fade it away while chips move into the pot.
    # ==================================================

    total_amount = sum(
        chunks
    )

    total_surface = (
        amount_font.render(
            f"${total_amount:,}",
            True,
            WHITE
        )
    )

    if sweep_progress > 0.0:

        total_surface.set_alpha(
            max(
                0,
                int(
                    255
                    * (
                        1.0
                        - sweep_progress
                    )
                )
            )
        )

    total_rect = (
        total_surface.get_rect(
            center=(
                center_x,
                y + 27
            )
        )
    )

    game_surface.blit(
        total_surface,
        total_rect
    )
