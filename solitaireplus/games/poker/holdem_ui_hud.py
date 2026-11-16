"""Texas Hold'em table UI: the player's hand text, the dealer / blind badges and the player HUD.

One part of the Hold'em table UI (see holdem_ui.py, which re-exports every name here).
"""
import pygame

from solitaireplus.games.poker.holdem_ui_state import WHITE, get_holdem_fonts
from solitaireplus.games.poker.holdem_ui_widgets import draw_translucent_panel


def get_holdem_player_hand_text(
        holdem_game
):

    # ==================================================
    # Rank helpers
    # ==================================================

    rank_values = {
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "10": 10,
        "J": 11,
        "Q": 12,
        "K": 13,
        "A": 14,
    }

    singular_names = {
        "A": "Ace",
        "K": "King",
        "Q": "Queen",
        "J": "Jack",
        "10": "Ten",
        "9": "Nine",
        "8": "Eight",
        "7": "Seven",
        "6": "Six",
        "5": "Five",
        "4": "Four",
        "3": "Three",
        "2": "Two",
    }

    plural_names = {
        "A": "Aces",
        "K": "Kings",
        "Q": "Queens",
        "J": "Jacks",
        "10": "Tens",
        "9": "Nines",
        "8": "Eights",
        "7": "Sevens",
        "6": "Sixes",
        "5": "Fives",
        "4": "Fours",
        "3": "Threes",
        "2": "Twos",
    }

    # ==================================================
    # PREFLOP
    # ==================================================

    if (
            holdem_game.current_stage
            == "preflop"
            and len(
                holdem_game.player_hand
            ) >= 2
    ):

        card_1 = (
            holdem_game.player_hand[0]
        )

        card_2 = (
            holdem_game.player_hand[1]
        )

        rank_1 = str(
            card_1["rank"]
        )

        rank_2 = str(
            card_2["rank"]
        )

        # ------------------------------------------
        # Pocket pair
        # ------------------------------------------

        if rank_1 == rank_2:

            return (
                f"A pair of "
                f"{plural_names.get(rank_1, rank_1)}"
            )

        # ------------------------------------------
        # High card
        # ------------------------------------------

        high_rank = max(
            (
                rank_1,
                rank_2
            ),
            key=lambda rank:
                rank_values.get(
                    rank,
                    0
                )
        )

        return (
            f"{singular_names.get(high_rank, high_rank)} "
            f"high"
        )

    # ==================================================
    # FLOP / TURN / RIVER / SHOWDOWN
    # ==================================================

    raw_text = ""

    if hasattr(
            holdem_game,
            "get_player_hand_name"
    ):

        raw_text = (
            holdem_game
            .get_player_hand_name()
            or ""
        )

    if not raw_text:
        return ""

    lowered = (
        str(raw_text)
        .strip()
        .lower()
    )

    all_cards = (
        holdem_game.player_hand
        + holdem_game.community_cards
    )

    # ==================================================
    # Pair
    # ==================================================

    if lowered in (
            "pair",
            "one pair",
    ):

        rank_counts = {}

        for card in all_cards:

            rank = str(
                card["rank"]
            )

            rank_counts[rank] = (
                rank_counts.get(
                    rank,
                    0
                )
                + 1
            )

        paired_ranks = [
            rank
            for rank, count
            in rank_counts.items()
            if count >= 2
        ]

        if paired_ranks:

            best_pair_rank = max(
                paired_ranks,
                key=lambda rank:
                    rank_values.get(
                        rank,
                        0
                    )
            )

            return (
                f"A pair of "
                f"{plural_names.get(
                    best_pair_rank,
                    best_pair_rank
                )}"
            )

        return "A pair"

    # ==================================================
    # Other hand names
    # ==================================================

    hand_names = {
        "high card":
            "High card",

        "two pair":
            "Two pair",

        "two pairs":
            "Two pair",

        "three of a kind":
            "Three of a kind",

        "straight":
            "A straight",

        "flush":
            "A flush",

        "full house":
            "A full house",

        "four of a kind":
            "Four of a kind",

        "straight flush":
            "A straight flush",

        "royal flush":
            "A royal flush",
    }

    return hand_names.get(
        lowered,
        str(raw_text)
    )


# ==================================================
# DEALER / BLIND POSITION BADGES
# ==================================================

def get_holdem_position_labels(
        holdem_game,
        table_index
):

    labels = []

    if getattr(
            holdem_game,
            "dealer_index",
            None
    ) == table_index:
        labels.append("D")

    if getattr(
            holdem_game,
            "small_blind_index",
            None
    ) == table_index:
        labels.append("SB")

    if getattr(
            holdem_game,
            "big_blind_index",
            None
    ) == table_index:
        labels.append("BB")

    return labels


def draw_holdem_position_badges(
        game_surface,
        holdem_game,
        table_index,
        start_x,
        y
):

    labels = (
        get_holdem_position_labels(
            holdem_game,
            table_index
        )
    )

    if not labels:
        return

    holdem_fonts = get_holdem_fonts()
    font = holdem_fonts["tiny"]

    badge_styles = {
        "D": (
            (122, 92, 24, 245),
            (245, 205, 90)
        ),
        "SB": (
            (52, 72, 92, 245),
            (155, 190, 220)
        ),
        "BB": (
            (92, 48, 48, 245),
            (220, 145, 145)
        ),
    }

    x = int(start_x)

    for label in labels:

        width = (
            30
            if label == "D"
            else 36
        )

        rect = pygame.Rect(
            x,
            int(y),
            width,
            22
        )

        fill_color, border_color = (
            badge_styles[label]
        )

        draw_translucent_panel(
            game_surface,
            rect,
            fill_color,
            border_color=border_color,
            border_width=2,
            radius=8
        )

        text_surface = font.render(
            label,
            True,
            WHITE
        )

        text_rect = text_surface.get_rect(
            center=rect.center
        )

        game_surface.blit(
            text_surface,
            text_rect
        )

        x += width + 5


def draw_holdem_player_hud(
        game_surface,
        player_name,
        player_stack,
        panel_center_x,
        panel_y,
        label_font,
        detail_font,
        panel_width=270,
        panel_height=78,
        is_current_actor=False,
        is_winner=False
):

    # ==================================================
    # Dedicated poker fonts
    # ==================================================

    holdem_fonts = get_holdem_fonts()

    name_font = holdem_fonts["title"]
    stack_font = holdem_fonts["small"]

    # ==================================================
    # Main HUD rectangle
    # ==================================================

    panel_rect = pygame.Rect(
        panel_center_x - panel_width // 2,
        panel_y,
        panel_width,
        panel_height
    )

    draw_translucent_panel(
        game_surface,
        panel_rect,
        (
            18,
            20,
            24,
            255
        ),
        border_color=(
            (235, 190, 70)
            if (is_current_actor or is_winner)
            else (185, 185, 190)
        ),
        border_width=(
            4
            if is_winner
            else (
                3
                if is_current_actor
                else 2
            )
        ),
        radius=12
    )

    # ==================================================
    # Player name
    # ==================================================

    name_text = player_name

    name_surface = name_font.render(
        name_text,
        True,
        (255, 255, 255)
    )

    name_rect = name_surface.get_rect(
        center=(
            panel_rect.centerx,
            panel_rect.y + 24
        )
    )

    # 1px black outline
    for offset_x, offset_y in (
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
            (-1, -1),
            (1, -1),
            (-1, 1),
            (1, 1),
    ):
        outline_surface = name_font.render(
            name_text,
            True,
            (0, 0, 0)
        )

        game_surface.blit(
            outline_surface,
            (
                name_rect.x + offset_x,
                name_rect.y + offset_y
            )
        )

    game_surface.blit(
        name_surface,
        name_rect
    )

    # ==================================================
    # Money box
    # ==================================================

    money_rect = pygame.Rect(
        panel_rect.centerx - 60,
        panel_rect.y + 43,
        120,
        24
    )

    draw_translucent_panel(
        game_surface,
        money_rect,
        (
            10,
            12,
            14,
            255
        ),
        border_color=(
            120,
            120,
            125
        ),
        border_width=1,
        radius=10
    )

    # ==================================================
    # Money text
    # ==================================================

    stack_text = (
        f"${player_stack:,}"
    )

    stack_surface = stack_font.render(
        stack_text,
        True,
        (
            240,
            255,
            235
        )
    )

    stack_rect = stack_surface.get_rect(
        center=money_rect.center
    )

    # Small shadow
    stack_shadow = stack_font.render(
        stack_text,
        True,
        (
            0,
            0,
            0
        )
    )

    game_surface.blit(
        stack_shadow,
        (
            stack_rect.x + 1,
            stack_rect.y + 1
        )
    )

    game_surface.blit(
        stack_surface,
        stack_rect
    )
