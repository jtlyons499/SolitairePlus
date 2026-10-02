import math

import pygame

from roulette import (
    AMERICAN_WHEEL_ORDER,
)


# ==================================================
# ACTIONS
# ==================================================

ACTION_RETURN = "return"
ACTION_SPIN = "spin"

ACTION_BET_RED = "bet_red"
ACTION_BET_BLACK = "bet_black"

ACTION_BET_ODD = "bet_odd"
ACTION_BET_EVEN = "bet_even"

ACTION_BET_LOW = "bet_low"
ACTION_BET_HIGH = "bet_high"

ACTION_BET_NUMBER_PREFIX = "bet_number_"

ACTION_CLEAR_BETS = "clear_bets"

ACTION_CHIP_10 = "chip_10"
ACTION_CHIP_50 = "chip_50"
ACTION_CHIP_100 = "chip_100"
ACTION_CHIP_500 = "chip_500"

ACTION_BET_DOZEN_1 = "bet_dozen_1"
ACTION_BET_DOZEN_2 = "bet_dozen_2"
ACTION_BET_DOZEN_3 = "bet_dozen_3"

ACTION_BET_COLUMN_1 = "bet_column_1"
ACTION_BET_COLUMN_2 = "bet_column_2"
ACTION_BET_COLUMN_3 = "bet_column_3"


# ==================================================
# COLORS
# ==================================================

WHITE = (
    255,
    255,
    255
)

BLACK = (
    20,
    20,
    20
)

DARK_PANEL = (
    25,
    25,
    25
)

RED = (
    170,
    40,
    40
)

GREEN = (
    35,
    120,
    70
)

GRAY = (
    90,
    90,
    90
)


# ==================================================
# MAIN RECTS
# ==================================================

roulette_board_rect = pygame.Rect(
    145,
    135,
    795,
    565
)

roulette_info_rect = pygame.Rect(
    970,
    135,
    255,
    565
)

roulette_spin_rect = pygame.Rect(
    980,
    580,
    220,
    50
)

roulette_return_rect = pygame.Rect(
    980,
    640,
    220,
    42
)



roulette_chip_10_rect = pygame.Rect(
    470,
    650,
    70,
    36
)

roulette_chip_50_rect = pygame.Rect(
    550,
    650,
    70,
    36
)

roulette_chip_100_rect = pygame.Rect(
    630,
    650,
    80,
    36
)

roulette_chip_500_rect = pygame.Rect(
    720,
    650,
    80,
    36
)

roulette_clear_rect = pygame.Rect(
    980, 525, 220, 42
)

# ==================================================
# OUTSIDE BET RECTS
# ==================================================

roulette_red_rect = pygame.Rect(
    180,
    555,
    155,
    46
)

roulette_black_rect = pygame.Rect(
    345,
    555,
    155,
    46
)

roulette_odd_rect = pygame.Rect(
    510,
    555,
    155,
    46
)

roulette_even_rect = pygame.Rect(
    675,
    555,
    155,
    46
)

roulette_low_rect = pygame.Rect(
    260,
    605,
    220,
    40
)

roulette_high_rect = pygame.Rect(
    510,
    605,
    220,
    40
)

# ==================================================
# DOZEN BETS
# ==================================================

roulette_dozen_1_rect = pygame.Rect(
    275,
    478,
    210,
    32
)

roulette_dozen_2_rect = pygame.Rect(
    490,
    478,
    210,
    32
)

roulette_dozen_3_rect = pygame.Rect(
    705,
    478,
    210,
    32
)



# ==================================================
# COLUMN BETS
# ==================================================

roulette_column_1_rect = pygame.Rect(
    275,
    515,
    210,
    32
)

roulette_column_2_rect = pygame.Rect(
    490,
    515,
    210,
    32
)

roulette_column_3_rect = pygame.Rect(
    705,
    515,
    210,
    32
)

# ==================================================
# NUMBER GRID
# ==================================================

roulette_number_rects = {}


def build_number_rects():

    roulette_number_rects.clear()

    # 0 and 00
    roulette_number_rects["0"] = pygame.Rect(
        170,
        175,
        90,
        145
    )

    roulette_number_rects["00"] = pygame.Rect(
        170,
        325,
        90,
        145
    )

    # 1-36
    start_x = 275
    start_y = 175

    cell_width = 50
    cell_height = 95

    gap_x = 5
    gap_y = 5

    number = 1

    for column in range(12):

        for row in range(3):

            x = (
                start_x
                + column
                * (
                    cell_width
                    + gap_x
                )
            )

            y = (
                start_y
                + (
                    2 - row
                )
                * (
                    cell_height
                    + gap_y
                )
            )

            roulette_number_rects[
                str(
                    number
                )
            ] = pygame.Rect(
                x,
                y,
                cell_width,
                cell_height
            )

            number += 1


build_number_rects()


# ==================================================
# HELPER
# ==================================================

def get_number_color(
        number,
        red_numbers
):

    if number in (
            "0",
            "00"
    ):
        return GREEN

    number_int = int(
        number
    )

    if number_int in red_numbers:
        return RED

    return BLACK


def draw_bet_chip(
        game_surface,
        rect,
        amount,
        detail_font
):

    if amount <= 0:
        return

    chip_center = (
        rect.right - 14,
        rect.top + 14
    )

    pygame.draw.circle(
        game_surface,
        (
            225,
            210,
            150
        ),
        chip_center,
        13
    )

    pygame.draw.circle(
        game_surface,
        (
            40,
            40,
            40
        ),
        chip_center,
        13,
        2
    )

    if amount >= 1000:
        text = (
            f"{amount // 1000}k"
        )
    else:
        text = str(
            amount
        )

    chip_surface = (
        pygame.font.Font(
            None,
            18
        ).render(
            text,
            True,
            (
                20,
                20,
                20
            )
        )
    )

    chip_rect = (
        chip_surface.get_rect(
            center=chip_center
        )
    )

    game_surface.blit(
        chip_surface,
        chip_rect
    )

# ==================================================
# ROULETTE WHEEL
# ==================================================

def draw_roulette_wheel(
        game_surface,
        roulette_game,
        red_numbers,
        detail_font
):

    center_x = 1090
    center_y = 410

    outer_radius = 88
    inner_radius = 38
    ball_radius = 6

    slot_count = len(
        AMERICAN_WHEEL_ORDER
    )

    sector_angle = (
        math.tau
        / slot_count
    )

    # ==================================================
    # Animation progress
    # ==================================================

    if roulette_game.spinning:

        progress = (
            roulette_game.get_spin_progress()
        )

    elif roulette_game.round_complete:

        progress = 1.0

    else:

        progress = 0.0

    # Cubic ease-out
    eased = (
        1.0
        - (
            1.0
            - progress
        ) ** 3
    )

    # Wheel makes complete rotations and ends
    # in its original orientation.
    wheel_rotation = (
        math.tau
        * 4
        * eased
    )

    # ==================================================
    # Outer wheel shadow
    # ==================================================

    pygame.draw.circle(
        game_surface,
        (
            5,
            5,
            5
        ),
        (
            center_x + 4,
            center_y + 5
        ),
        outer_radius + 8
    )

    # ==================================================
    # Wheel sectors
    # ==================================================

    for index, number in enumerate(
            AMERICAN_WHEEL_ORDER
    ):

        start_angle = (
            -math.pi / 2
            + index * sector_angle
            + wheel_rotation
        )

        end_angle = (
            start_angle
            + sector_angle
        )

        if number in (
                "0",
                "00"
        ):

            sector_color = GREEN

        elif int(number) in red_numbers:

            sector_color = RED

        else:

            sector_color = BLACK

        point_1 = (
            center_x
            + math.cos(
                start_angle
            )
            * inner_radius,
            center_y
            + math.sin(
                start_angle
            )
            * inner_radius
        )

        point_2 = (
            center_x
            + math.cos(
                start_angle
            )
            * outer_radius,
            center_y
            + math.sin(
                start_angle
            )
            * outer_radius
        )

        point_3 = (
            center_x
            + math.cos(
                end_angle
            )
            * outer_radius,
            center_y
            + math.sin(
                end_angle
            )
            * outer_radius
        )

        point_4 = (
            center_x
            + math.cos(
                end_angle
            )
            * inner_radius,
            center_y
            + math.sin(
                end_angle
            )
            * inner_radius
        )

        pygame.draw.polygon(
            game_surface,
            sector_color,
            [
                point_1,
                point_2,
                point_3,
                point_4,
            ]
        )

    # ==================================================
    # Wheel borders
    # ==================================================

    pygame.draw.circle(
        game_surface,
        WHITE,
        (
            center_x,
            center_y
        ),
        outer_radius,
        3
    )

    pygame.draw.circle(
        game_surface,
        (
            180,
            150,
            75
        ),
        (
            center_x,
            center_y
        ),
        inner_radius
    )

    pygame.draw.circle(
        game_surface,
        WHITE,
        (
            center_x,
            center_y
        ),
        inner_radius,
        2
    )

    # ==================================================
    # Center display
    # ==================================================

    if roulette_game.spinning:

        center_text = "..."

    elif roulette_game.round_complete:

        center_text = str(
            roulette_game.display_result
        )

    else:

        center_text = "?"

    center_surface = (
        detail_font.render(
            center_text,
            True,
            WHITE
        )
    )

    center_rect = (
        center_surface.get_rect(
            center=(
                center_x,
                center_y
            )
        )
    )

    game_surface.blit(
        center_surface,
        center_rect
    )

    # ==================================================
    # Ball
    # ==================================================

    ball_track_radius = (
        outer_radius - 12
    )

    # Before first spin, park the ball at the top.
    ball_angle = (
        -math.pi / 2
    )

    if (
            roulette_game.result is not None
            and (
                roulette_game.spinning
                or roulette_game.round_complete
            )
    ):

        try:

            result_index = (
                AMERICAN_WHEEL_ORDER.index(
                    str(
                        roulette_game.result
                    )
                )
            )

        except ValueError:

            result_index = 0

        target_angle = (
            -math.pi / 2
            + (
                result_index
                + 0.5
            )
            * sector_angle
        )

        if roulette_game.spinning:

            starting_angle = (
                -math.pi / 2
            )

            # Six counter-clockwise laps,
            # gradually landing on the result.
            travel = (
                target_angle
                - starting_angle
                - math.tau * 6
            )

            ball_angle = (
                starting_angle
                + travel * eased
            )

        else:

            ball_angle = (
                target_angle
            )

    ball_x = int(
        center_x
        + math.cos(
            ball_angle
        )
        * ball_track_radius
    )

    ball_y = int(
        center_y
        + math.sin(
            ball_angle
        )
        * ball_track_radius
    )

    # Ball shadow
    pygame.draw.circle(
        game_surface,
        (
            25,
            25,
            25
        ),
        (
            ball_x + 2,
            ball_y + 2
        ),
        ball_radius + 1
    )

    pygame.draw.circle(
        game_surface,
        (
            235,
            235,
            220
        ),
        (
            ball_x,
            ball_y
        ),
        ball_radius
    )

    pygame.draw.circle(
        game_surface,
        WHITE,
        (
            ball_x,
            ball_y
        ),
        ball_radius,
        1
    )

# ==================================================
# DRAW
# ==================================================

def draw_roulette(
        game_surface,
        mouse_pos,
        roulette_game,
        red_numbers,
        draw_submenu_background,
        draw_submenu_title,
        draw_menu_button,
        title_font,
        label_font,
        detail_font,
        career_cash,
        session_net,
        selected_chip_value
):


    draw_submenu_background(
        overlay_alpha=120
    )

    draw_submenu_title(
        "ROULETTE",
        y=45,
        width=320
    )

    # ==================================================
    # Main panels
    # ==================================================

    pygame.draw.rect(
        game_surface,
        DARK_PANEL,
        roulette_board_rect
    )

    pygame.draw.rect(
        game_surface,
        WHITE,
        roulette_board_rect,
        2
    )

    pygame.draw.rect(
        game_surface,
        DARK_PANEL,
        roulette_info_rect
    )

    pygame.draw.rect(
        game_surface,
        WHITE,
        roulette_info_rect,
        2
    )

    # ==================================================
    # Number grid
    # ==================================================

    for number, rect in roulette_number_rects.items():

        cell_color = (
            get_number_color(
                number,
                red_numbers
            )
        )

        pygame.draw.rect(
            game_surface,
            cell_color,
            rect
        )

        border_width = 2

        if (
                roulette_game.get_bet_amount(
                    "number",
                    number
                ) > 0
        ):
            border_width = 5

        pygame.draw.rect(
            game_surface,
            WHITE,
            rect,
            border_width
        )

        number_surface = (
            detail_font.render(
                number,
                True,
                WHITE
            )
        )

        number_rect = (
            number_surface.get_rect(
                center=rect.center
            )
        )

        game_surface.blit(
            number_surface,
            number_rect
        )

        number_bet_amount = (
            roulette_game.get_bet_amount(
                "number",
                number
            )
        )

        draw_bet_chip(
            game_surface,
            rect,
            number_bet_amount,
            detail_font
        )

    # ==================================================
    # Dozens
    # ==================================================

    draw_menu_button(
        roulette_dozen_1_rect,
        "1st 12",
        mouse_pos,
        selected=(
                roulette_game.get_bet_amount(
                    "dozen",
                    1
                ) > 0
        ),
        font=detail_font
    )

    draw_menu_button(
        roulette_dozen_2_rect,
        "2nd 12",
        mouse_pos,
        selected=(
                roulette_game.get_bet_amount(
                    "dozen",
                    2
                ) > 0
        ),
        font=detail_font
    )

    draw_menu_button(
        roulette_dozen_3_rect,
        "3rd 12",
        mouse_pos,
        selected=(
                roulette_game.get_bet_amount(
                    "dozen",
                    3
                ) > 0
        ),
        font=detail_font
    )

    # ==================================================
    # Columns
    # ==================================================

    draw_menu_button(
        roulette_column_1_rect,
        "Column 1",
        mouse_pos,
        selected=(
                roulette_game.get_bet_amount(
                    "column",
                    1
                ) > 0
        ),
        font=detail_font
    )

    draw_menu_button(
        roulette_column_2_rect,
        "Column 2",
        mouse_pos,
        selected=(
                roulette_game.get_bet_amount(
                    "column",
                    2
                ) > 0
        ),
        font=detail_font
    )

    draw_menu_button(
        roulette_column_3_rect,
        "Column 3",
        mouse_pos,
        selected=(
                roulette_game.get_bet_amount(
                    "column",
                    3
                ) > 0
        ),
        font=detail_font
    )

    # ==================================================
    # Outside bets
    # ==================================================

    draw_menu_button(
        roulette_red_rect,
        "RED",
        mouse_pos,
        selected=(
                roulette_game.get_bet_amount(
                    "color",
                    "red"
                ) > 0
        ),
        font=detail_font
    )

    draw_menu_button(
        roulette_black_rect,
        "BLACK",
        mouse_pos,
        selected=(
                roulette_game.get_bet_amount(
                    "color",
                    "black"
                ) > 0
        ),
        font=detail_font
    )

    draw_menu_button(
        roulette_odd_rect,
        "ODD",
        mouse_pos,
        selected=(
                roulette_game.get_bet_amount(
                    "parity",
                    "odd"
                ) > 0
        ),
        font=detail_font
    )

    draw_menu_button(
        roulette_even_rect,
        "EVEN",
        mouse_pos,
        selected=(
                roulette_game.get_bet_amount(
                    "parity",
                    "even"
                ) > 0
        ),
        font=detail_font
    )

    draw_menu_button(
        roulette_low_rect,
        "1 - 18",
        mouse_pos,
        selected=(
                roulette_game.get_bet_amount(
                    "range",
                    "low"
                ) > 0
        ),
        font=detail_font
    )

    draw_menu_button(
        roulette_high_rect,
        "19 - 36",
        mouse_pos,
        selected=(
                roulette_game.get_bet_amount(
                    "range",
                    "high"
                ) > 0
        ),
        font=detail_font
    )

    draw_menu_button(
        roulette_clear_rect,
        "CLEAR ALL BETS",
        mouse_pos,
        font=detail_font
    )

    instruction_surface = (
        detail_font.render(
            "Left click: place chip   •   Right click: remove chip",
            True,
            (
                235,
                235,
                235
            )
        )
    )

    instruction_rect = (
        instruction_surface.get_rect(
            center=(
                roulette_board_rect.centerx,
                155
            )
        )
    )

    chip_label_surface = (
        detail_font.render(
            "Chip:",
            True,
            WHITE
        )
    )

    game_surface.blit(
        chip_label_surface,
        (
            390,
            657
        )
    )

    draw_menu_button(
        roulette_chip_10_rect,
        "$10",
        mouse_pos,
        selected=(
                selected_chip_value == 10
        ),
        font=detail_font
    )

    draw_menu_button(
        roulette_chip_50_rect,
        "$50",
        mouse_pos,
        selected=(
                selected_chip_value == 50
        ),
        font=detail_font
    )

    draw_menu_button(
        roulette_chip_100_rect,
        "$100",
        mouse_pos,
        selected=(
                selected_chip_value == 100
        ),
        font=detail_font
    )

    draw_menu_button(
        roulette_chip_500_rect,
        "$500",
        mouse_pos,
        selected=(
                selected_chip_value == 500
        ),
        font=detail_font
    )

    game_surface.blit(
        instruction_surface,
        instruction_rect
    )

    draw_bet_chip(
        game_surface,
        roulette_red_rect,
        roulette_game.get_bet_amount(
            "color",
            "red"
        ),
        detail_font
    )

    draw_bet_chip(
        game_surface,
        roulette_black_rect,
        roulette_game.get_bet_amount(
            "color",
            "black"
        ),
        detail_font
    )

    draw_bet_chip(
        game_surface,
        roulette_odd_rect,
        roulette_game.get_bet_amount(
            "parity",
            "odd"
        ),
        detail_font
    )

    draw_bet_chip(
        game_surface,
        roulette_even_rect,
        roulette_game.get_bet_amount(
            "parity",
            "even"
        ),
        detail_font
    )

    draw_bet_chip(
        game_surface,
        roulette_low_rect,
        roulette_game.get_bet_amount(
            "range",
            "low"
        ),
        detail_font
    )

    draw_bet_chip(
        game_surface,
        roulette_high_rect,
        roulette_game.get_bet_amount(
            "range",
            "high"
        ),
        detail_font
    )

    draw_bet_chip(
        game_surface,
        roulette_dozen_1_rect,
        roulette_game.get_bet_amount(
            "dozen",
            1
        ),
        detail_font
    )

    draw_bet_chip(
        game_surface,
        roulette_dozen_2_rect,
        roulette_game.get_bet_amount(
            "dozen",
            2
        ),
        detail_font
    )

    draw_bet_chip(
        game_surface,
        roulette_dozen_3_rect,
        roulette_game.get_bet_amount(
            "dozen",
            3
        ),
        detail_font
    )

    draw_bet_chip(
        game_surface,
        roulette_column_1_rect,
        roulette_game.get_bet_amount(
            "column",
            1
        ),
        detail_font
    )

    draw_bet_chip(
        game_surface,
        roulette_column_2_rect,
        roulette_game.get_bet_amount(
            "column",
            2
        ),
        detail_font
    )

    draw_bet_chip(
        game_surface,
        roulette_column_3_rect,
        roulette_game.get_bet_amount(
            "column",
            3
        ),
        detail_font
    )

    # ==================================================
    # Info panel
    # ==================================================

    cash_surface = (
        label_font.render(
            f"Cash: ${career_cash:,}",
            True,
            WHITE
        )
    )

    game_surface.blit(
        cash_surface,
        (
            980,
            155
        )
    )

    if session_net > 0:

        session_text = (
            f"Session: +${session_net:,}"
        )

    elif session_net < 0:

        session_text = (
            f"Session: -${abs(session_net):,}"
        )

    else:

        session_text = (
            "Session: $0"
        )

    session_surface = (
        detail_font.render(
            session_text,
            True,
            WHITE
        )
    )

    game_surface.blit(
        session_surface,
        (
            980,
            195
        )
    )

    # ==================================================
    # Bet information
    # ==================================================

    bet_label_surface = (
        detail_font.render(
            "Selected Bet:",
            True,
            WHITE
        )
    )

    game_surface.blit(
        bet_label_surface,
        (
            980,
            235
        )
    )

    bet_name_surface = (
        detail_font.render(
            roulette_game.get_bet_label(),
            True,
            WHITE
        )
    )

    game_surface.blit(
        bet_name_surface,
        (
            980,
            265
        )
    )

    total_bet = (
        roulette_game.get_total_bet()
    )

    if total_bet > 0:

        bet_amount_text = (
            f"Total Wager: "
            f"${total_bet:,}"
        )

    else:

        bet_amount_text = (
            "Total Wager: none"
        )

    bet_amount_surface = (
        detail_font.render(
            bet_amount_text,
            True,
            WHITE
        )
    )

    game_surface.blit(
        bet_amount_surface,
        (
            980,
            285
        )
    )

    # ==================================================
    # Animated wheel
    # ==================================================

    draw_roulette_wheel(
        game_surface,
        roulette_game,
        red_numbers,
        detail_font
    )

    # ==================================================
    # Status / result
    # ==================================================

    if roulette_game.spinning:

        status_text = (
            "Spinning..."
        )

    elif roulette_game.round_complete:

        net_result = (
            roulette_game.get_net_result()
        )

        if net_result > 0:

            status_text = (
                f"WIN +${net_result:,}"
            )

        elif net_result < 0:

            status_text = (
                f"LOSE ${abs(net_result):,}"
            )

        else:

            status_text = (
                "PUSH"
            )


    elif roulette_game.bets:

        status_text = (

            "Ready to spin"

        )

    else:

        status_text = (
            "Place a bet"
        )

    status_surface = (
        detail_font.render(
            status_text,
            True,
            WHITE
        )
    )

    status_rect = (
        status_surface.get_rect(
            center=(
                roulette_info_rect.centerx,
                515
            )
        )
    )

    game_surface.blit(
        status_surface,
        status_rect
    )

    # ==================================================
    # Buttons
    # ==================================================

    if not roulette_game.spinning:

        draw_menu_button(
            roulette_spin_rect,
            "SPIN",
            mouse_pos,
            font=detail_font
        )

    draw_menu_button(
        roulette_return_rect,
        "RETURN",
        mouse_pos,
        font=detail_font
    )


# ==================================================
# CLICK DETECTION
# ==================================================

def get_roulette_action(
        mouse_pos
):

    if mouse_pos is None:
        return None

    # Number bets
    for number, rect in roulette_number_rects.items():

        if rect.collidepoint(
                mouse_pos
        ):

            return (
                ACTION_BET_NUMBER_PREFIX
                + number
            )

    if roulette_dozen_1_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_BET_DOZEN_1

    if roulette_dozen_2_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_BET_DOZEN_2

    if roulette_dozen_3_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_BET_DOZEN_3

    if roulette_column_1_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_BET_COLUMN_1

    if roulette_column_2_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_BET_COLUMN_2

    if roulette_column_3_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_BET_COLUMN_3

    # Outside bets
    if roulette_red_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_BET_RED

    if roulette_black_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_BET_BLACK

    if roulette_odd_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_BET_ODD

    if roulette_even_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_BET_EVEN

    if roulette_low_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_BET_LOW

    if roulette_high_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_BET_HIGH

    if roulette_chip_10_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_CHIP_10

    if roulette_chip_50_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_CHIP_50

    if roulette_chip_100_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_CHIP_100

    if roulette_chip_500_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_CHIP_500

    if roulette_clear_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_CLEAR_BETS

    if roulette_spin_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_SPIN

    if roulette_return_rect.collidepoint(
            mouse_pos
    ):
        return ACTION_RETURN

    return None