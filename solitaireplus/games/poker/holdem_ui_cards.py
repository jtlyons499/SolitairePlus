"""Texas Hold'em table UI: card faces and backs, and the card deal and flip animations.

One part of the Hold'em table UI (see holdem_ui.py, which re-exports every name here).
get_card_key is also used by the multiplayer table views. The animation keys live on the
shared _ui holder (holdem_ui_state.py); their starting values are set here.
"""
import pygame

from solitaireplus.games.poker.holdem_ui_state import _ui


# ==================================================
# CARD ANIMATION STATE
# ==================================================

_ui.holdem_card_fx_hand_number = -1
_ui.holdem_card_fx_stage = None

_ui.holdem_card_fx_kind = None
_ui.holdem_card_fx_started_at = 0


def get_card_key(
        card
):

    if card is None:
        return None

    rank = card["rank"]
    suit = card["suit"]

    suit_letter_map = {
        "Clubs": "C",
        "Diamonds": "D",
        "Hearts": "H",
        "Spades": "S",
    }

    return (
        f"{rank}"
        f"{suit_letter_map[suit]}"
    )


def draw_card_face(
        game_surface,
        card,
        x,
        y,
        card_fronts,
        width=72,
        height=101
):

    card_key = (
        get_card_key(
            card
        )
    )

    if (
            card_key is None
            or card_key not in card_fronts
    ):
        return

    card_image = (
        pygame.transform.smoothscale(
            card_fronts[
                card_key
            ],
            (
                width,
                height
            )
        )
    )

    game_surface.blit(
        card_image,
        (
            x,
            y
        )
    )


def draw_card_back(
        game_surface,
        card_back,
        x,
        y,
        width=72,
        height=101
):

    back_image = (
        pygame.transform.smoothscale(
            card_back,
            (
                width,
                height
            )
        )
    )

    game_surface.blit(
        back_image,
        (
            x,
            y
        )
    )

# ==================================================
# TEXAS HOLD'EM CARD ANIMATION HELPERS
# ==================================================

def sync_holdem_card_fx(
        holdem_game
):

    now = pygame.time.get_ticks()

    hand_number = getattr(
        holdem_game,
        "hand_number",
        0
    )

    stage = (
        holdem_game.current_stage
    )

    # ==================================================
    # New hand
    # ==================================================

    if (
            hand_number
            != _ui.holdem_card_fx_hand_number
    ):

        _ui.holdem_card_fx_hand_number = (
            hand_number
        )

        _ui.holdem_card_fx_stage = (
            stage
        )

        _ui.holdem_card_fx_kind = (
            "deal"
        )

        _ui.holdem_card_fx_started_at = (
            now
        )

    # ==================================================
    # New street
    # ==================================================

    elif stage != _ui.holdem_card_fx_stage:

        _ui.holdem_card_fx_stage = (
            stage
        )

        if stage in (
                "flop",
                "turn",
                "river",
                "showdown",
        ):

            _ui.holdem_card_fx_kind = (
                stage
            )

            _ui.holdem_card_fx_started_at = (
                now
            )

    elapsed = max(
        0,
        now
        - _ui.holdem_card_fx_started_at
    )

    return (
        _ui.holdem_card_fx_kind,
        elapsed
    )


def get_holdem_card_fx_progress(
        elapsed,
        delay=0,
        duration=180
):

    if elapsed <= delay:
        return 0.0

    progress = (
        (elapsed - delay)
        / max(
            1,
            duration
        )
    )

    return max(
        0.0,
        min(
            progress,
            1.0
        )
    )


def get_holdem_eased_progress(
        progress
):

    progress = max(
        0.0,
        min(
            progress,
            1.0
        )
    )

    # Ease-out cubic
    return (
        1.0
        - pow(
            1.0 - progress,
            3
        )
    )


def draw_holdem_popping_card_face(
        game_surface,
        card,
        x,
        y,
        card_fronts,
        width,
        height,
        progress
):

    if progress <= 0:
        return

    if progress >= 1:

        draw_card_face(
            game_surface,
            card,
            x,
            y,
            card_fronts,
            width=width,
            height=height
        )

        return

    eased = (
        get_holdem_eased_progress(
            progress
        )
    )

    scale = (
        0.58
        + 0.42
        * eased
    )

    temp_surface = pygame.Surface(
        (
            width,
            height
        ),
        pygame.SRCALPHA
    )

    draw_card_face(
        temp_surface,
        card,
        0,
        0,
        card_fronts,
        width=width,
        height=height
    )

    scaled_width = max(
        2,
        int(
            width
            * scale
        )
    )

    scaled_height = max(
        2,
        int(
            height
            * scale
        )
    )

    scaled_surface = (
        pygame.transform.smoothscale(
            temp_surface,
            (
                scaled_width,
                scaled_height
            )
        )
    )

    scaled_surface.set_alpha(
        int(
            255
            * progress
        )
    )

    target_rect = (
        scaled_surface.get_rect(
            center=(
                x + width // 2,
                y + height // 2
            )
        )
    )

    game_surface.blit(
        scaled_surface,
        target_rect
    )


def draw_holdem_popping_card_back(
        game_surface,
        card_back,
        x,
        y,
        width,
        height,
        progress
):

    if progress <= 0:
        return

    if progress >= 1:

        draw_card_back(
            game_surface,
            card_back,
            x,
            y,
            width=width,
            height=height
        )

        return

    eased = (
        get_holdem_eased_progress(
            progress
        )
    )

    scale = (
        0.58
        + 0.42
        * eased
    )

    temp_surface = pygame.Surface(
        (
            width,
            height
        ),
        pygame.SRCALPHA
    )

    draw_card_back(
        temp_surface,
        card_back,
        0,
        0,
        width=width,
        height=height
    )

    scaled_width = max(
        2,
        int(
            width
            * scale
        )
    )

    scaled_height = max(
        2,
        int(
            height
            * scale
        )
    )

    scaled_surface = (
        pygame.transform.smoothscale(
            temp_surface,
            (
                scaled_width,
                scaled_height
            )
        )
    )

    scaled_surface.set_alpha(
        int(
            255
            * progress
        )
    )

    target_rect = (
        scaled_surface.get_rect(
            center=(
                x + width // 2,
                y + height // 2
            )
        )
    )

    game_surface.blit(
        scaled_surface,
        target_rect
    )


def draw_holdem_flipping_card(
        game_surface,
        card,
        card_back,
        x,
        y,
        card_fronts,
        width,
        height,
        progress
):

    progress = max(
        0.0,
        min(
            progress,
            1.0
        )
    )

    # ==================================================
    # First half: card back narrows
    # ==================================================

    if progress < 0.5:

        phase = (
            progress
            / 0.5
        )

        width_scale = (
            1.0
            - phase
        )

        temp_surface = pygame.Surface(
            (
                width,
                height
            ),
            pygame.SRCALPHA
        )

        draw_card_back(
            temp_surface,
            card_back,
            0,
            0,
            width=width,
            height=height
        )

    # ==================================================
    # Second half: face expands
    # ==================================================

    else:

        phase = (
            (progress - 0.5)
            / 0.5
        )

        width_scale = (
            phase
        )

        temp_surface = pygame.Surface(
            (
                width,
                height
            ),
            pygame.SRCALPHA
        )

        draw_card_face(
            temp_surface,
            card,
            0,
            0,
            card_fronts,
            width=width,
            height=height
        )

    scaled_width = max(
        2,
        int(
            width
            * width_scale
        )
    )

    scaled_surface = (
        pygame.transform.smoothscale(
            temp_surface,
            (
                scaled_width,
                height
            )
        )
    )

    target_rect = (
        scaled_surface.get_rect(
            center=(
                x + width // 2,
                y + height // 2
            )
        )
    )

    game_surface.blit(
        scaled_surface,
        target_rect
    )
