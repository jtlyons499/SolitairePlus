"""Five-Card Draw table and buy-in screens, sessions and timed NPC turns (moved out of legacy.py)."""
from solitaireplus.games.poker.five_card_draw_ui import ACTION_BET_RAISE as DRAW_ACTION_BET_RAISE
from solitaireplus.games.poker.five_card_draw_ui import ACTION_CHECK_CALL as DRAW_ACTION_CHECK_CALL
from solitaireplus.games.poker.five_card_draw_ui import ACTION_DRAW as DRAW_ACTION_DRAW
from solitaireplus.games.poker.five_card_draw_ui import ACTION_FOLD as DRAW_ACTION_FOLD
from solitaireplus.games.poker.five_card_draw_ui import ACTION_NEXT_HAND as DRAW_ACTION_NEXT_HAND
from solitaireplus.games.poker.five_card_draw_ui import ACTION_OPTIONS as DRAW_ACTION_OPTIONS
from solitaireplus.games.poker.five_card_draw_ui import ACTION_RETURN as DRAW_ACTION_RETURN
from solitaireplus.games.poker.five_card_draw_ui import DRAW_LOG_RECT
from solitaireplus.games.poker.five_card_draw import FiveCardDrawGame
from solitaireplus.games.poker.five_card_draw_ui import add_five_card_draw_chat_message
from solitaireplus.career import career_rewards
from solitaireplus.career import career_saving
from solitaireplus.games.poker.five_card_draw_ui import clear_five_card_draw_manual_bet
from solitaireplus.games.poker.five_card_draw_ui import clear_five_card_draw_selection
from solitaireplus.games.poker.five_card_draw_ui import drag_five_card_draw_bet_slider
from solitaireplus.games.poker.five_card_draw_ui import draw_five_card_draw
from solitaireplus.games.poker.five_card_draw_ui import draw_five_card_draw_buy_in
from solitaireplus.games.poker.holdem_ui import draw_holdem_options_overlay
from solitaireplus.games.poker.holdem_chat import generate_npc_action_chat
from solitaireplus.games.poker.holdem_chat import generate_player_action_reaction
from solitaireplus.games.poker.holdem_chat import generate_showdown_chat
from solitaireplus.games.poker.five_card_draw_ui import get_five_card_draw_action
from solitaireplus.games.poker.five_card_draw_ui import get_five_card_draw_bet_amount
from solitaireplus.games.poker.five_card_draw_ui import get_five_card_draw_buy_in_action
from solitaireplus.games.poker.holdem_ui import get_holdem_next_hand_delay
from solitaireplus.games.poker.holdem_ui import get_holdem_npc_delay
from solitaireplus.games.poker.holdem_ui import get_holdem_street_delay
from solitaireplus.npc.manager import get_random_npc
from solitaireplus.games.poker.five_card_draw_ui import get_selected_draw_indexes
from solitaireplus.games.poker.five_card_draw_ui import handle_five_card_draw_bet_preset
from solitaireplus.games.poker.five_card_draw_ui import handle_five_card_draw_card_click
from solitaireplus.games.poker.five_card_draw_ui import handle_five_card_draw_manual_bet_click
from solitaireplus.games.poker.five_card_draw_ui import handle_five_card_draw_manual_bet_key
from solitaireplus.games.poker.five_card_draw_ui import handle_five_card_draw_panel_click
from solitaireplus.games.poker.holdem_ui import handle_holdem_options_click
from solitaireplus.games.poker.holdem_ui import is_holdem_auto_deal_enabled
from solitaireplus.games.poker.holdem_ui import is_holdem_options_open
from solitaireplus.games.poker.holdem_ui import is_holdem_table_chat_enabled
import pygame
from solitaireplus.career.rating_events import record_poker_showdown
from solitaireplus.games.poker.five_card_draw_ui import reset_five_card_draw_ui_session
from solitaireplus.games.poker.table_timers import reset_table_session
from solitaireplus.games.poker.table_timers import reset_table_timers
from solitaireplus.games.poker.five_card_draw_ui import scroll_five_card_draw_panel
from solitaireplus.games.poker.recap import player_hand_net
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.games.poker.five_card_draw_ui import stop_five_card_draw_bet_slider
from solitaireplus.games.poker.holdem_ui import toggle_holdem_options
from solitaireplus.career.session_summary import track_night_cash
from solitaireplus.games.poker.five_card_draw_ui import update_five_card_draw_bet_slider
from solitaireplus.app.lazy import lazy
table_stakes = lazy("solitaireplus.games.poker.table_stakes")
holdem_screen = lazy("solitaireplus.games.poker.holdem_screen")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
panels = lazy("solitaireplus.ui.panels")
leveling = lazy("solitaireplus.profile.leveling")


# ==================================================
# FIVE-CARD DRAW RUNTIME
# ==================================================

five_card_draw_game = FiveCardDrawGame()

FIVE_CARD_DRAW_SESSION_END_DELAY = 5000
FIVE_CARD_DRAW_TABLE_SWEEP_RATING_BONUS = 100

# ==================================================
# FIVE-CARD DRAW HELPERS
# ==================================================

def post_five_card_draw_chat(
        chat_entry
):

    if not chat_entry or not is_holdem_table_chat_enabled():
        return

    speaker, message = chat_entry

    add_five_card_draw_chat_message(
        speaker,
        message
    )


def get_five_card_draw_opponents():

    opponents = []
    used_ids = []

    while len(opponents) < 4:

        npc = get_random_npc(
            exclude_ids=used_ids
        )

        if npc is None:
            break

        opponents.append(npc)
        used_ids.append(
            npc["id"]
        )

    return opponents


def schedule_five_card_draw_npc_action():

    if (
            not five_card_draw_game.hand_complete
            and five_card_draw_game.current_stage
            in (
                "preflop",
                "post_draw",
            )
            and not five_card_draw_game.betting_round_complete
            and five_card_draw_game.current_actor
            not in (
                0,
                -1,
            )
    ):
        state.five_card_draw_next_npc_action_at = (
                pygame.time.get_ticks()
                + get_holdem_npc_delay()
        )


def start_five_card_draw_session(
        starting_stack=None,
        opponents=None
):

    if starting_stack is None:
        starting_stack = (
            table_stakes.get_poker_starting_stack()
        )

    starting_stack = int(
        starting_stack
    )

    starting_stack = min(
        starting_stack,
        state.career_cash
    )

    if (
            starting_stack
            < table_stakes.FIVE_CARD_DRAW_MIN_BUY_IN
    ):
        print(
            "Not enough cash to enter Five-Card Draw."
        )
        return False

    blind_unit = table_stakes.get_poker_ante(
        starting_stack,
        high_stakes=False
    )

    if opponents is None:
        opponents = get_five_card_draw_opponents()
    else:
        opponents = list(opponents)[:4]

    if len(opponents) < 4:
        print(
            "Could not find four Five-Card Draw opponents."
        )
        return False

    state.career_cash -= (
        starting_stack
    )

    state.five_card_draw_starting_stack = (
        starting_stack
    )

    state.five_card_draw_session_net = 0
    state.five_card_draw_buy_in_active = True
    five_card_draw_game.session_xp_rewarded = False

    reset_table_session("five_card_draw")

    reset_five_card_draw_ui_session()

    five_card_draw_game.career_session_rated = state.current_game_mode == "career"
    five_card_draw_game.learning_store = legacy.game_namespace().get("career_poker_learning") if state.current_game_mode == "career" else None
    five_card_draw_game.start_session(
        opponents,
        starting_stack,
        blind_unit
    )

    if five_card_draw_game.start_hand():
        sounds.audio.play_sound(
            "card_draw"
        )

    state.career_event_has_activity = True

    state.current_state = state_names.STATE_FIVE_CARD_DRAW

    return True


def finish_five_card_draw_session():

    if state.five_card_draw_buy_in_active:

        state.career_cash += (
            five_card_draw_game.player_stack
        )

        state.five_card_draw_session_net = (
                five_card_draw_game.player_stack
                - state.five_card_draw_starting_stack
        )

        state.five_card_draw_buy_in_active = False
        track_night_cash(legacy.game_namespace(), "five_card_draw", state.five_card_draw_session_net)
        career_rewards.rate_poker_cash_out("five_card_draw", five_card_draw_game)

    if (
            five_card_draw_game.current_stage
            != "ready"
    ):
        state.career_event_has_activity = True

    reset_table_timers("five_card_draw")

    if (
            len(getattr(five_card_draw_game, "rating_seen_hands", ())) > 0
            and not getattr(five_card_draw_game, "session_xp_rewarded", False)
    ):
        won_session = state.five_card_draw_session_net > 0
        leveling.award_game_xp("five_card_draw", won=won_session)
        if state.current_game_mode == "career" and state.five_card_draw_session_net < 0:
            legacy.lose_fans_for_bad_result(
                "Rough Five-Card Draw session",
                net_loss=abs(state.five_card_draw_session_net),
            )
        five_card_draw_game.session_xp_rewarded = True

    if state.current_game_mode == "free":
        legacy.finish_free_play_sandbox()
        state.current_state = state_names.STATE_FREE_PLAY_SELECT
    else:
        state.current_state = state_names.STATE_CAREER_EVENT_SELECT
        career_saving.auto_save_career()


def play_five_card_draw_npc_action_sound(
        npc_index
):

    if not (
            0 <= npc_index
            < len(
                five_card_draw_game.npc_action_texts
            )
    ):
        return

    action_text = (
        five_card_draw_game
        .npc_action_texts[npc_index]
        .strip()
        .lower()
    )

    if action_text.startswith(
            "checked"
    ):
        sounds.audio.play_sound(
            "poker_check"
        )
        return

    if action_text.startswith(
            (
                "called",
                "bet",
                "raised",
            )
    ):
        holdem_screen.play_texas_holdem_chip_sound()


def process_five_card_draw_showdown():

    if not five_card_draw_game.hand_complete:
        return

    if (
            five_card_draw_game.current_stage
            != "showdown"
    ):
        return

    if (
            five_card_draw_game.hand_number
            == state.five_card_draw_last_processed_showdown_hand
    ):
        return

    state.five_card_draw_last_processed_showdown_hand = (
        five_card_draw_game.hand_number
    )
    record_poker_showdown(five_card_draw_game)

    sounds.audio.play_sound(
        "card_flip"
    )

    if 0 in five_card_draw_game.winner_indexes:
        state.five_card_draw_hand_win_sound_at = (
                pygame.time.get_ticks()
                + 450
        )
        # Fans on what the human made on the hand (its net), as every casino
        # game pays them: its own chips back (an uncalled shove, a refund)
        # earn none, and a hand that won a pot but lost money pays nothing.
        net_win = player_hand_net(five_card_draw_game)
        if net_win > 0:
            career_rewards.award_fans_for_cash_win(
                net_win,
                "Five-Card Draw hand win"
            )

    showdown_messages = (
        generate_showdown_chat(
            five_card_draw_game
        )
    )

    for chat_entry in showdown_messages:
        post_five_card_draw_chat(
            chat_entry
        )

    if five_card_draw_game.player_busted:

        state.five_card_draw_next_hand_at = 0

        if (
                "out of chips"
                not in five_card_draw_game.result_text.lower()
        ):
            five_card_draw_game.result_text += (
                " You are out of chips."
            )

        state.five_card_draw_session_end_at = (
                pygame.time.get_ticks()
                + FIVE_CARD_DRAW_SESSION_END_DELAY
        )

        return

    if five_card_draw_game.all_npcs_busted():

        state.five_card_draw_next_hand_at = 0

        fan_gain = 0

        if not state.five_card_draw_table_sweep_rewarded:
            leveling.process_achievement_event("poker_table_clear", game="five_card_draw")
            if state.current_game_mode == "career":
                fan_gain = career_rewards.award_fans_for_rating_win(
                    FIVE_CARD_DRAW_TABLE_SWEEP_RATING_BONUS,
                    "Five-Card Draw table clear"
                )
                state.career_event_has_activity = True
            state.five_card_draw_table_sweep_rewarded = True

        five_card_draw_game.result_text += " TABLE CLEARED!"
        if state.current_game_mode == "career":
            five_card_draw_game.result_text += (
                " Rating settles on cash-out. "
                f"+{fan_gain:,} Fans."
            )

        state.five_card_draw_session_end_at = (
                pygame.time.get_ticks()
                + FIVE_CARD_DRAW_SESSION_END_DELAY
        )


def loop_event_five_card_draw_buy_in(event):
    """Old main-loop event branch for STATE_FIVE_CARD_DRAW_BUY_IN."""

    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):

        buy_in_action = (
            get_five_card_draw_buy_in_action(
                state.game_mouse_pos,
                state.career_cash,
                table_stakes.FIVE_CARD_DRAW_MIN_BUY_IN
            )
        )

        if buy_in_action is not None:

            action_type, amount = (
                buy_in_action
            )

            if action_type == "back":
                sounds.audio.play_sound(
                    "button_click"
                )

                if state.current_game_mode == "free":
                    legacy.finish_free_play_sandbox()
                    state.current_state = state_names.STATE_FREE_PLAY_SELECT
                else:
                    state.current_state = state_names.STATE_CAREER_EVENT_SELECT

            elif action_type == "buy_in":

                sounds.audio.play_sound(
                    "button_click"
                )

                start_five_card_draw_session(
                    amount
                )


def loop_event_five_card_draw(event):
    """Old main-loop event branch for STATE_FIVE_CARD_DRAW."""

    if (
            is_holdem_options_open()
            and event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):
        option_changed = handle_holdem_options_click(
            state.game_mouse_pos
        )
        if option_changed:
            sounds.audio.play_sound("button_click")
            if not is_holdem_auto_deal_enabled():
                state.five_card_draw_next_hand_at = 0
        return

    if event.type == pygame.KEYDOWN:
        if handle_five_card_draw_manual_bet_key(
                event,
                five_card_draw_game
        ):
            return

    if (
            event.type == pygame.MOUSEMOTION
            and state.game_mouse_pos is not None
    ):
        drag_five_card_draw_bet_slider(
            state.game_mouse_pos
        )

    elif (
            event.type == pygame.MOUSEBUTTONUP
            and event.button == 1
    ):
        stop_five_card_draw_bet_slider()

    elif (
            event.type == pygame.MOUSEWHEEL
            and state.game_mouse_pos is not None
            and DRAW_LOG_RECT.collidepoint(
                state.game_mouse_pos
            )
    ):

        scroll_five_card_draw_panel(
            event.y,
            five_card_draw_game
        )

    elif (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):

        if handle_five_card_draw_manual_bet_click(
                state.game_mouse_pos,
                five_card_draw_game
        ):
            sounds.audio.play_sound("button_click")
            return

        if handle_five_card_draw_panel_click(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )
            return

        if handle_five_card_draw_card_click(
                state.game_mouse_pos,
                five_card_draw_game
        ):
            sounds.audio.play_sound(
                "button_click"
            )
            return

        if update_five_card_draw_bet_slider(
                state.game_mouse_pos,
                five_card_draw_game
        ):
            sounds.audio.play_sound("button_click")
            return

        if (
                five_card_draw_game.current_stage
                in (
                    "preflop",
                    "post_draw",
                )
                and handle_five_card_draw_bet_preset(
                    state.game_mouse_pos
                )
        ):
            sounds.audio.play_sound(
                "button_click"
            )
            return

        draw_action = (
            get_five_card_draw_action(
                state.game_mouse_pos,
                five_card_draw_game
            )
        )

        if (
                draw_action
                == DRAW_ACTION_NEXT_HAND
        ):

            if (
                    five_card_draw_game.all_npcs_busted()
                    and not five_card_draw_game.player_busted
            ):
                sounds.audio.play_sound(
                    "button_click"
                )

                process_five_card_draw_showdown()
                finish_five_card_draw_session()

            elif (
                    five_card_draw_game.player_stack > 0
                    and not five_card_draw_game.player_busted
            ):
                sounds.audio.play_sound(
                    "button_click"
                )

                state.five_card_draw_next_hand_at = 0

                if five_card_draw_game.start_hand():
                    sounds.audio.play_sound(
                        "card_draw"
                    )

                clear_five_card_draw_selection()

        elif (
                draw_action
                == DRAW_ACTION_DRAW
        ):

            discard_indexes = (
                get_selected_draw_indexes()
            )

            if five_card_draw_game.player_draw(
                    discard_indexes
            ):
                sounds.audio.play_sound(
                    "card_draw"
                )

                clear_five_card_draw_selection()

        elif (
                draw_action
                == DRAW_ACTION_FOLD
        ):

            if five_card_draw_game.player_fold():
                sounds.audio.play_sound(
                    "button_click"
                )

                state.five_card_draw_session_net = (
                        five_card_draw_game.player_stack
                        - state.five_card_draw_starting_stack
                )

                state.career_event_has_activity = True

        elif (
                draw_action
                == DRAW_ACTION_CHECK_CALL
        ):

            amount_to_call = (
                five_card_draw_game
                .get_player_amount_to_call()
            )

            if amount_to_call > 0:
                state.success = (
                    five_card_draw_game.player_call()
                )
                state.player_chat_action = "call"

            else:
                state.success = (
                    five_card_draw_game.player_check()
                )
                state.player_chat_action = "check"

            if state.success:

                if amount_to_call > 0:
                    holdem_screen.play_texas_holdem_chip_sound()

                else:
                    sounds.audio.play_sound(
                        "poker_check"
                    )

                post_five_card_draw_chat(
                    generate_player_action_reaction(
                        five_card_draw_game,
                        state.player_chat_action
                    )
                )

                schedule_five_card_draw_npc_action()

        elif (
                draw_action
                == DRAW_ACTION_BET_RAISE
        ):

            bet_amount = (
                get_five_card_draw_bet_amount(
                    five_card_draw_game
                )
            )

            if five_card_draw_game.current_bet == 0:
                state.player_chat_action = "bet"
                state.success = five_card_draw_game.player_bet(
                    bet_amount
                )

            else:
                state.player_chat_action = "raise"
                state.success = five_card_draw_game.player_raise(
                    bet_amount
                )

            if state.success:
                holdem_screen.play_texas_holdem_chip_sound()
                clear_five_card_draw_manual_bet()

                post_five_card_draw_chat(
                    generate_player_action_reaction(
                        five_card_draw_game,
                        state.player_chat_action
                    )
                )

                schedule_five_card_draw_npc_action()

        elif (
                draw_action
                == DRAW_ACTION_OPTIONS
        ):
            sounds.audio.play_sound("button_click")
            toggle_holdem_options()

        elif (
                draw_action
                == DRAW_ACTION_RETURN
        ):

            sounds.audio.play_sound(
                "button_click"
            )

            finish_five_card_draw_session()


def loop_draw_five_card_draw_buy_in():
    """Old draw-chain branch for STATE_FIVE_CARD_DRAW_BUY_IN."""

    draw_five_card_draw_buy_in(
        window.game_surface,
        state.game_mouse_pos,
        state.career_cash,
        panels.draw_submenu_background,
        minimum_buy_in=table_stakes.FIVE_CARD_DRAW_MIN_BUY_IN
    )


def loop_draw_five_card_draw():
    """Old draw-chain branch for STATE_FIVE_CARD_DRAW."""

    five_card_draw_next_hand_seconds = None

    if (
            five_card_draw_game.hand_complete
            and state.five_card_draw_next_hand_at > 0
    ):
        remaining_ms = max(
            0,
            state.five_card_draw_next_hand_at
            - pygame.time.get_ticks()
        )

        five_card_draw_next_hand_seconds = (
            remaining_ms + 999
        ) // 1000

    draw_five_card_draw(
        window.game_surface,
        state.game_mouse_pos,
        five_card_draw_game,
        legacy.game.card_fronts,
        legacy.game.get_card_back_surface(),
        panels.draw_submenu_background,
        legacy.draw_npc_portrait,
        state.player_name,
        legacy.game.felt_surface,
        next_hand_seconds=(
            five_card_draw_next_hand_seconds
        )
    )

    draw_holdem_options_overlay(
        window.game_surface,
        state.game_mouse_pos
    )


def loop_late_five_card_draw():
    """Old timed-NPC branch for STATE_FIVE_CARD_DRAW (runs after drawing, as before)."""

    now = pygame.time.get_ticks()

    # ==================================================
    # Make sure an NPC-first betting turn is scheduled
    # ==================================================

    if (
            not five_card_draw_game.hand_complete
            and five_card_draw_game.current_stage
            in (
                "preflop",
                "post_draw",
            )
            and five_card_draw_game.current_actor
            not in (
                0,
                -1,
            )
            and state.five_card_draw_next_npc_action_at == 0
            and not five_card_draw_game.is_betting_round_complete()
    ):
        state.five_card_draw_next_npc_action_at = (
                now
                + get_holdem_npc_delay()
        )

    # ==================================================
    # Delayed hand-win sound
    # ==================================================

    if (
            state.five_card_draw_hand_win_sound_at > 0
            and now >= state.five_card_draw_hand_win_sound_at
    ):
        sounds.audio.play_sound(
            "poker_hand_win"
        )

        state.five_card_draw_hand_win_sound_at = 0

    process_five_card_draw_showdown()

    # ==================================================
    # Start next-hand countdown
    # ==================================================

    if (
            five_card_draw_game.hand_complete
            and five_card_draw_game.current_stage == "showdown"
            and state.five_card_draw_next_hand_at == 0
            and state.five_card_draw_session_end_at == 0
            and is_holdem_auto_deal_enabled()
            and five_card_draw_game.player_stack > 0
            and not five_card_draw_game.player_busted
            and not five_card_draw_game.all_npcs_busted()
    ):
        state.five_card_draw_next_hand_at = (
                now
                + get_holdem_next_hand_delay()
        )

    # ==================================================
    # Run one NPC betting action
    # ==================================================

    if (
            state.five_card_draw_next_npc_action_at > 0
            and now >= state.five_card_draw_next_npc_action_at
            and not five_card_draw_game.hand_complete
    ):
        state.five_card_draw_next_npc_action_at = 0

        acting_actor = (
            five_card_draw_game.current_actor
        )

        action_success = (
            five_card_draw_game.run_next_npc_action()
        )

        if (
                action_success
                and acting_actor > 0
        ):
            acting_npc_index = (
                    acting_actor - 1
            )

            play_five_card_draw_npc_action_sound(
                acting_npc_index
            )

            post_five_card_draw_chat(
                generate_npc_action_chat(
                    five_card_draw_game,
                    acting_npc_index
                )
            )

        if (
                not five_card_draw_game.is_betting_round_complete()
                and five_card_draw_game.current_actor
                not in (
                    0,
                    -1,
                )
        ):
            state.five_card_draw_next_npc_action_at = (
                    now
                    + get_holdem_npc_delay()
            )

    # ==================================================
    # Finished betting round -> schedule transition
    # ==================================================

    if (
            not five_card_draw_game.hand_complete
            and five_card_draw_game.current_stage
            in (
                "preflop",
                "post_draw",
            )
            and five_card_draw_game.is_betting_round_complete()
            and state.five_card_draw_round_advance_at == 0
    ):
        state.five_card_draw_round_advance_at = (
                now
                + get_holdem_street_delay()
        )

        five_card_draw_game.current_actor = -1

    # ==================================================
    # First betting -> draw / final betting -> showdown
    # ==================================================

    if (
            state.five_card_draw_round_advance_at > 0
            and now >= state.five_card_draw_round_advance_at
    ):
        state.five_card_draw_round_advance_at = 0

        previous_stage = (
            five_card_draw_game.current_stage
        )

        advanced = (
            five_card_draw_game.advance_after_betting_round()
        )

        new_stage = (
            five_card_draw_game.current_stage
        )

        if (
                advanced
                and previous_stage == "preflop"
                and new_stage in (
                    "draw",
                    "post_draw",
                )
        ):
            sounds.audio.play_sound(
                "card_draw"
            )

        if (
                advanced
                and not five_card_draw_game.hand_complete
                and new_stage
                in (
                    "preflop",
                    "post_draw",
                )
                and five_card_draw_game.current_actor
                not in (
                    0,
                    -1,
                )
        ):
            schedule_five_card_draw_npc_action()

    # ==================================================
    # Automatically start next hand
    # ==================================================

    if (
            state.five_card_draw_next_hand_at > 0
            and now >= state.five_card_draw_next_hand_at
    ):
        state.five_card_draw_next_hand_at = 0

        if five_card_draw_game.start_hand():
            sounds.audio.play_sound(
                "card_draw"
            )

        clear_five_card_draw_selection()

    # ==================================================
    # Session finished
    # ==================================================

    if (
            state.five_card_draw_session_end_at > 0
            and now >= state.five_card_draw_session_end_at
    ):
        state.five_card_draw_session_end_at = 0

        finish_five_card_draw_session()
