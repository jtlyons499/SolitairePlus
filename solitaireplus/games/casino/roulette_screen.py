"""Roulette table screen (moved out of legacy.py)."""
from solitaireplus.games.casino.roulette_ui import ACTION_BET_BLACK
from solitaireplus.games.casino.roulette_ui import ACTION_BET_COLUMN_1
from solitaireplus.games.casino.roulette_ui import ACTION_BET_COLUMN_2
from solitaireplus.games.casino.roulette_ui import ACTION_BET_COLUMN_3
from solitaireplus.games.casino.roulette_ui import ACTION_BET_DOZEN_1
from solitaireplus.games.casino.roulette_ui import ACTION_BET_DOZEN_2
from solitaireplus.games.casino.roulette_ui import ACTION_BET_DOZEN_3
from solitaireplus.games.casino.roulette_ui import ACTION_BET_EVEN
from solitaireplus.games.casino.roulette_ui import ACTION_BET_HIGH
from solitaireplus.games.casino.roulette_ui import ACTION_BET_LOW
from solitaireplus.games.casino.roulette_ui import ACTION_BET_NUMBER_PREFIX
from solitaireplus.games.casino.roulette_ui import ACTION_BET_ODD
from solitaireplus.games.casino.roulette_ui import ACTION_BET_RED
from solitaireplus.games.casino.roulette_ui import ACTION_CHIP_10
from solitaireplus.games.casino.roulette_ui import ACTION_CHIP_100
from solitaireplus.games.casino.roulette_ui import ACTION_CHIP_50
from solitaireplus.games.casino.roulette_ui import ACTION_CHIP_500
from solitaireplus.games.casino.roulette_ui import ACTION_CLEAR_BETS
from solitaireplus.games.casino.roulette import RED_NUMBERS
from solitaireplus.games.casino.roulette_ui import ACTION_RETURN as ROULETTE_ACTION_RETURN
from solitaireplus.games.casino.roulette_ui import ACTION_SPIN as ROULETTE_ACTION_SPIN
from solitaireplus.games.casino.roulette import RouletteGame
from solitaireplus.career import career_rewards
from solitaireplus.games.casino.roulette_ui import draw_roulette
from solitaireplus.games.casino.roulette_ui import get_roulette_action
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.career.session_summary import track_night_cash
from solitaireplus.app.lazy import lazy
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
panels = lazy("solitaireplus.ui.panels")
leveling = lazy("solitaireplus.profile.leveling")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")


roulette_game = RouletteGame()


def try_place_or_remove_roulette_bet(
        bet_type,
        bet_value,
        is_right_click
):

    wager = state.roulette_chip_value

    if is_right_click:

        if roulette_game.remove_bet(
                bet_type,
                bet_value,
                wager
        ):

            sounds.audio.play_sound(
                "button_click"
            )

        return

    if (
            wager > 0
            and (
                roulette_game.get_total_bet()
                + wager
            ) <= state.career_cash
    ):

        roulette_game.place_bet(
            bet_type,
            bet_value,
            wager
        )

        sounds.audio.play_sound(
            "button_click"
        )

def settle_roulette_round():

    if not roulette_game.round_complete:
        return

    if roulette_game.payout_claimed:
        return

    payout = (
        roulette_game.get_payout()
    )

    state.career_cash += (
        payout
    )

    net_result = (
        roulette_game.get_net_result()
    )

    state.roulette_session_net += (
        net_result
    )
    roulette_game.rating_change = (career_rewards.rate_house_game("roulette", net_result)
                                   if state.current_game_mode == "career" else None)

    if net_result > 0:
        career_rewards.award_fans_for_cash_win(
            net_result,
            "Roulette win"
        )
    elif state.current_game_mode == "career" and net_result <= -500:
        legacy.lose_fans_for_bad_result(
            "Rough Roulette spin",
            net_loss=abs(net_result),
            severity=0.65,
        )

    leveling.award_game_xp(
        "roulette",
        won=(net_result > 0),
        bonus=8 if net_result >= 1000 else 0,
    )

    leveling.process_achievement_event(
        "roulette_round",
        net=net_result,
        bets=[dict(bet) for bet in roulette_game.bets],
    )

    track_night_cash(legacy.game_namespace(), "roulette", net_result)
    roulette_game.payout_claimed = True


def handle_event(event):
    """Old main-loop event branch for STATE_ROULETTE."""

    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button in (
            1,
            3
    )
            and state.game_mouse_pos is not None
    ):

        roulette_action = (
            get_roulette_action(
                state.game_mouse_pos
            )
        )

        is_right_click = (
                event.button == 3
        )

        # ==========================================
        # CHIP SELECTION
        # ==========================================

        if roulette_action == ACTION_CHIP_10:

            state.roulette_chip_value = 10

            sounds.audio.play_sound(
                "button_click"
            )

        elif roulette_action == ACTION_CHIP_50:

            state.roulette_chip_value = 50

            sounds.audio.play_sound(
                "button_click"
            )

        elif roulette_action == ACTION_CHIP_100:

            state.roulette_chip_value = 100

            sounds.audio.play_sound(
                "button_click"
            )

        elif roulette_action == ACTION_CHIP_500:

            state.roulette_chip_value = 500

            sounds.audio.play_sound(
                "button_click"
            )

        # ==========================================
        # CLEAR BETS
        # ==========================================

        elif (
                roulette_action == ACTION_CLEAR_BETS
                and not roulette_game.spinning
        ):

            if roulette_game.clear_bets():
                sounds.audio.play_sound(
                    "button_click"
                )

        # ==========================================
        # NUMBER BET
        # ==========================================

        elif (
                roulette_action is not None
                and roulette_action.startswith(
            ACTION_BET_NUMBER_PREFIX
        )
                and not roulette_game.spinning
        ):

            number = (
                roulette_action[
                    len(
                        ACTION_BET_NUMBER_PREFIX
                    ):
                ]
            )

            state.wager = state.roulette_chip_value

            if is_right_click:

                if roulette_game.remove_bet(
                        "number",
                        number,
                        state.wager
                ):
                    sounds.audio.play_sound(
                        "button_click"
                    )

            else:

                if (
                        state.wager > 0
                        and (
                        roulette_game.get_total_bet()
                        + state.wager
                ) <= state.career_cash
                ):
                    roulette_game.place_bet(
                        "number",
                        number,
                        state.wager
                    )

                    sounds.audio.play_sound(
                        "button_click"
                    )

        # ==========================================
        # DOZENS
        # ==========================================

        elif roulette_action == ACTION_BET_DOZEN_1:

            try_place_or_remove_roulette_bet(
                "dozen",
                1,
                is_right_click
            )

        elif roulette_action == ACTION_BET_DOZEN_2:

            try_place_or_remove_roulette_bet(
                "dozen",
                2,
                is_right_click
            )

        elif roulette_action == ACTION_BET_DOZEN_3:

            try_place_or_remove_roulette_bet(
                "dozen",
                3,
                is_right_click
            )

        # ==========================================
        # COLUMNS
        # ==========================================

        elif roulette_action == ACTION_BET_COLUMN_1:

            try_place_or_remove_roulette_bet(
                "column",
                1,
                is_right_click
            )

        elif roulette_action == ACTION_BET_COLUMN_2:

            try_place_or_remove_roulette_bet(
                "column",
                2,
                is_right_click
            )

        elif roulette_action == ACTION_BET_COLUMN_3:

            try_place_or_remove_roulette_bet(
                "column",
                3,
                is_right_click
            )

        # ==========================================
        # RED
        # ==========================================

        elif (
                roulette_action == ACTION_BET_RED
                and not roulette_game.spinning
        ):

            state.wager = state.roulette_chip_value

            if is_right_click:

                if roulette_game.remove_bet(
                        "color",
                        "red",
                        state.wager
                ):
                    sounds.audio.play_sound(
                        "button_click"
                    )

            else:

                if (
                        state.wager > 0
                        and (
                        roulette_game.get_total_bet()
                        + state.wager
                ) <= state.career_cash
                ):
                    roulette_game.place_bet(
                        "color",
                        "red",
                        state.wager
                    )

                    sounds.audio.play_sound(
                        "button_click"
                    )

        # ==========================================
        # BLACK
        # ==========================================

        elif (
                roulette_action == ACTION_BET_BLACK
                and not roulette_game.spinning
        ):

            state.wager = state.roulette_chip_value

            if is_right_click:

                if roulette_game.remove_bet(
                        "color",
                        "black",
                        state.wager
                ):
                    sounds.audio.play_sound(
                        "button_click"
                    )

            else:

                if (
                        state.wager > 0
                        and (
                        roulette_game.get_total_bet()
                        + state.wager
                ) <= state.career_cash
                ):
                    roulette_game.place_bet(
                        "color",
                        "black",
                        state.wager
                    )

                    sounds.audio.play_sound(
                        "button_click"
                    )

        # ==========================================
        # ODD
        # ==========================================

        elif (
                roulette_action == ACTION_BET_ODD
                and not roulette_game.spinning
        ):

            state.wager = state.roulette_chip_value

            if is_right_click:

                if roulette_game.remove_bet(
                        "parity",
                        "odd",
                        state.wager
                ):
                    sounds.audio.play_sound(
                        "button_click"
                    )

            else:

                if (
                        state.wager > 0
                        and (
                        roulette_game.get_total_bet()
                        + state.wager
                ) <= state.career_cash
                ):
                    roulette_game.place_bet(
                        "parity",
                        "odd",
                        state.wager
                    )

                    sounds.audio.play_sound(
                        "button_click"
                    )

        # ==========================================
        # EVEN
        # ==========================================

        elif (
                roulette_action == ACTION_BET_EVEN
                and not roulette_game.spinning
        ):

            state.wager = state.roulette_chip_value

            if is_right_click:

                if roulette_game.remove_bet(
                        "parity",
                        "even",
                        state.wager
                ):
                    sounds.audio.play_sound(
                        "button_click"
                    )

            else:

                if (
                        state.wager > 0
                        and (
                        roulette_game.get_total_bet()
                        + state.wager
                ) <= state.career_cash
                ):
                    roulette_game.place_bet(
                        "parity",
                        "even",
                        state.wager
                    )

                    sounds.audio.play_sound(
                        "button_click"
                    )

        # ==========================================
        # LOW
        # ==========================================

        elif (
                roulette_action == ACTION_BET_LOW
                and not roulette_game.spinning
        ):

            state.wager = state.roulette_chip_value

            if is_right_click:

                if roulette_game.remove_bet(
                        "range",
                        "low",
                        state.wager
                ):
                    sounds.audio.play_sound(
                        "button_click"
                    )

            else:

                if (
                        state.wager > 0
                        and (
                        roulette_game.get_total_bet()
                        + state.wager
                ) <= state.career_cash
                ):
                    roulette_game.place_bet(
                        "range",
                        "low",
                        state.wager
                    )

                    sounds.audio.play_sound(
                        "button_click"
                    )

        # ==========================================
        # HIGH
        # ==========================================

        elif (
                roulette_action == ACTION_BET_HIGH
                and not roulette_game.spinning
        ):

            state.wager = state.roulette_chip_value

            if is_right_click:

                if roulette_game.remove_bet(
                        "range",
                        "high",
                        state.wager
                ):
                    sounds.audio.play_sound(
                        "button_click"
                    )

            else:

                if (
                        state.wager > 0
                        and (
                        roulette_game.get_total_bet()
                        + state.wager
                ) <= state.career_cash
                ):
                    roulette_game.place_bet(
                        "range",
                        "high",
                        state.wager
                    )

                    sounds.audio.play_sound(
                        "button_click"
                    )

        # ==========================================
        # SPIN
        # ==========================================

        elif (

                roulette_action
                == ROULETTE_ACTION_SPIN
                and not roulette_game.spinning

        ):

            total_bet = (
                roulette_game.get_total_bet()
            )

            # Take the stake only once the wheel really starts: a refused
            # start_spin() runs no round, so nothing would ever pay it back.
            if (
                    total_bet > 0
                    and state.career_cash >= total_bet
                    and roulette_game.start_spin()
            ):

                state.career_cash -= (
                    total_bet

                )

                state.career_event_has_activity = True

                sounds.audio.play_sound(

                    "button_click"

                )

        # ==========================================
        # RETURN
        # ==========================================

        elif (
                roulette_action
                == ROULETTE_ACTION_RETURN
                and not roulette_game.spinning
        ):

            sounds.audio.play_sound(
                "button_click"
            )

            if state.current_game_mode == "free":
                legacy.finish_free_play_sandbox()
                state.current_state = state_names.STATE_FREE_PLAY_SELECT
            else:
                state.current_state = state_names.STATE_CAREER_EVENT_SELECT


def draw():
    """Old draw-chain branch for STATE_ROULETTE."""

    roulette_game.update()

    settle_roulette_round()

    draw_roulette(
        window.game_surface,
        state.game_mouse_pos,
        roulette_game,
        RED_NUMBERS,
        panels.draw_submenu_background,
        panels.draw_submenu_title,
        buttons.draw_menu_button,
        fonts.options_title_font,
        fonts.option_label_font,
        fonts.difficulty_detail_font,
        state.career_cash,
        state.roulette_session_net,
        state.roulette_chip_value
    )
