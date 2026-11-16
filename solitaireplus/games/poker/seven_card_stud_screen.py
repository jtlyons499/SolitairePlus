"""Seven-Card Stud table and buy-in screens, sessions and timed NPC turns (moved out of legacy.py)."""
from solitaireplus.games.poker.seven_card_stud_ui import ACTION_BET_RAISE as STUD_ACTION_BET_RAISE
from solitaireplus.games.poker.seven_card_stud_ui import ACTION_CHECK_CALL as STUD_ACTION_CHECK_CALL
from solitaireplus.games.poker.seven_card_stud_ui import ACTION_FOLD as STUD_ACTION_FOLD
from solitaireplus.games.poker.seven_card_stud_ui import ACTION_NEXT_HAND as STUD_ACTION_NEXT_HAND
from solitaireplus.games.poker.seven_card_stud_ui import ACTION_OPTIONS as STUD_ACTION_OPTIONS
from solitaireplus.games.poker.seven_card_stud_ui import ACTION_RETURN as STUD_ACTION_RETURN
from solitaireplus.games.poker.seven_card_stud_ui import STUD_LOG_RECT
from solitaireplus.games.poker.seven_card_stud import SevenCardStudGame
from solitaireplus.games.poker.seven_card_stud_ui import add_seven_card_stud_chat_message
from solitaireplus.career import career_rewards
from solitaireplus.career import career_saving
from solitaireplus.games.poker.holdem_ui import draw_holdem_options_overlay
from solitaireplus.games.poker.seven_card_stud_ui import draw_seven_card_stud
from solitaireplus.games.poker.seven_card_stud_ui import draw_seven_card_stud_buy_in
from solitaireplus.games.poker.holdem_chat import generate_npc_action_chat
from solitaireplus.games.poker.holdem_chat import generate_player_action_reaction
from solitaireplus.games.poker.holdem_chat import generate_showdown_chat
from solitaireplus.games.poker.holdem_ui import get_holdem_next_hand_delay
from solitaireplus.games.poker.holdem_ui import get_holdem_npc_delay
from solitaireplus.games.poker.holdem_ui import get_holdem_street_delay
from solitaireplus.npc.manager import get_random_npc
from solitaireplus.games.poker.seven_card_stud_ui import get_seven_card_stud_action
from solitaireplus.games.poker.seven_card_stud_ui import get_seven_card_stud_buy_in_action
from solitaireplus.games.poker.holdem_ui import handle_holdem_options_click
from solitaireplus.games.poker.seven_card_stud_ui import handle_seven_card_stud_panel_click
from solitaireplus.games.poker.holdem_ui import is_holdem_auto_deal_enabled
from solitaireplus.games.poker.holdem_ui import is_holdem_options_open
from solitaireplus.games.poker.holdem_ui import is_holdem_table_chat_enabled
import pygame
from solitaireplus.career.rating_events import record_poker_showdown
from solitaireplus.games.poker.seven_card_stud_ui import reset_seven_card_stud_ui_session
from solitaireplus.games.poker.table_timers import reset_table_session
from solitaireplus.games.poker.table_timers import reset_table_timers
from solitaireplus.games.poker.seven_card_stud_ui import scroll_seven_card_stud_panel
from solitaireplus.games.poker.recap import player_hand_net
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.games.poker.holdem_ui import toggle_holdem_options
from solitaireplus.career.session_summary import track_night_cash
from solitaireplus.app.lazy import lazy
table_stakes = lazy("solitaireplus.games.poker.table_stakes")
holdem_screen = lazy("solitaireplus.games.poker.holdem_screen")
free_play_select = lazy("solitaireplus.menus.free_play_select")
game_globals = lazy("solitaireplus.app.game_globals")
game_portraits = lazy("solitaireplus.npc.game_portraits")
table = lazy("solitaireplus.games.solitaire.table")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
panels = lazy("solitaireplus.ui.panels")
leveling = lazy("solitaireplus.profile.leveling")


# ==================================================
# SEVEN-CARD STUD RUNTIME
# ==================================================

seven_card_stud_game = SevenCardStudGame()

SEVEN_CARD_STUD_SESSION_END_DELAY = 5000
SEVEN_CARD_STUD_TABLE_SWEEP_RATING_BONUS = 100



# ==================================================
# SEVEN-CARD STUD HELPERS
# ==================================================

def post_seven_card_stud_chat(
        chat_entry
):
    if not chat_entry or not is_holdem_table_chat_enabled():
        return

    speaker, message = chat_entry

    add_seven_card_stud_chat_message(
        speaker,
        message
    )


def get_seven_card_stud_opponents():
    opponents = []
    used_ids = []

    while len(opponents) < 4:
        npc = get_random_npc(
            exclude_ids=used_ids
        )

        if npc is None:
            break

        opponents.append(
            npc
        )

        used_ids.append(
            npc["id"]
        )

    return opponents


def schedule_seven_card_stud_npc_action():

    if (
            not seven_card_stud_game.hand_complete
            and seven_card_stud_game.current_stage
            in seven_card_stud_game.STUD_STAGES
            and not seven_card_stud_game.betting_round_complete
            and seven_card_stud_game.current_actor
            not in (
                0,
                -1,
            )
    ):
        state.seven_card_stud_next_npc_action_at = (
                pygame.time.get_ticks()
                + get_holdem_npc_delay()
        )


def start_seven_card_stud_session(
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
            < table_stakes.SEVEN_CARD_STUD_MIN_BUY_IN
    ):
        print(
            "Not enough cash to enter Seven-Card Stud."
        )
        return False

    base_unit = table_stakes.get_poker_ante(
        starting_stack,
        high_stakes=False
    )

    if opponents is None:
        opponents = get_seven_card_stud_opponents()
    else:
        opponents = list(opponents)[:4]

    if len(opponents) < 4:
        print(
            "Could not find four Seven-Card Stud opponents."
        )
        return False

    state.career_cash -= (
        starting_stack
    )

    state.seven_card_stud_starting_stack = (
        starting_stack
    )

    state.seven_card_stud_session_net = 0
    state.seven_card_stud_buy_in_active = True
    seven_card_stud_game.session_xp_rewarded = False

    reset_table_session("seven_card_stud")

    reset_seven_card_stud_ui_session()

    seven_card_stud_game.career_session_rated = state.current_game_mode == "career"
    seven_card_stud_game.learning_store = game_globals.game_namespace().get("career_poker_learning") if state.current_game_mode == "career" else None
    seven_card_stud_game.start_session(
        opponents,
        starting_stack,
        base_unit
    )

    if seven_card_stud_game.start_hand():
        sounds.audio.play_sound(
            "card_draw"
        )

    state.career_event_has_activity = True

    state.current_state = state_names.STATE_SEVEN_CARD_STUD

    return True


def finish_seven_card_stud_session():

    if state.seven_card_stud_buy_in_active:
        state.career_cash += (
            seven_card_stud_game.player_stack
        )

        state.seven_card_stud_session_net = (
                seven_card_stud_game.player_stack
                - state.seven_card_stud_starting_stack
        )

        state.seven_card_stud_buy_in_active = False
        track_night_cash(game_globals.game_namespace(), "seven_card_stud", state.seven_card_stud_session_net)
        career_rewards.rate_poker_cash_out("seven_card_stud", seven_card_stud_game)

    if (
            seven_card_stud_game.current_stage
            != "ready"
    ):
        state.career_event_has_activity = True

    reset_table_timers("seven_card_stud")

    if (
            len(getattr(seven_card_stud_game, "rating_seen_hands", ())) > 0
            and not getattr(seven_card_stud_game, "session_xp_rewarded", False)
    ):
        won_session = state.seven_card_stud_session_net > 0
        leveling.award_game_xp("seven_card_stud", won=won_session)
        if state.current_game_mode == "career" and state.seven_card_stud_session_net < 0:
            career_rewards.lose_fans_for_bad_result(
                "Rough Seven-Card Stud session",
                net_loss=abs(state.seven_card_stud_session_net),
            )
        seven_card_stud_game.session_xp_rewarded = True

    if state.current_game_mode == "free":
        free_play_select.finish_free_play_sandbox()
        state.current_state = state_names.STATE_FREE_PLAY_SELECT
    else:
        state.current_state = state_names.STATE_CAREER_EVENT_SELECT
        career_saving.auto_save_career()


def play_seven_card_stud_npc_action_sound(
        npc_index
):
    if not (
            0 <= npc_index
            < len(
                seven_card_stud_game.npc_action_texts
            )
    ):
        return

    action_text = (
        seven_card_stud_game
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
                "bring-in",
            )
    ):
        holdem_screen.play_texas_holdem_chip_sound()


def process_seven_card_stud_showdown():

    if not seven_card_stud_game.hand_complete:
        return

    if (
            seven_card_stud_game.current_stage
            != "showdown"
    ):
        return

    if (
            seven_card_stud_game.hand_number
            == state.seven_card_stud_last_processed_showdown_hand
    ):
        return

    state.seven_card_stud_last_processed_showdown_hand = (
        seven_card_stud_game.hand_number
    )
    record_poker_showdown(seven_card_stud_game)

    sounds.audio.play_sound(
        "card_flip"
    )

    if 0 in seven_card_stud_game.winner_indexes:
        state.seven_card_stud_hand_win_sound_at = (
                pygame.time.get_ticks()
                + 450
        )
        # Fans on what the human made on the hand (its net), as every casino
        # game pays them: its own chips back (an uncalled shove, a refund)
        # earn none, and a hand that won a pot but lost money pays nothing.
        net_win = player_hand_net(seven_card_stud_game)
        if net_win > 0:
            career_rewards.award_fans_for_cash_win(
                net_win,
                "Seven-Card Stud hand win"
            )

    showdown_messages = (
        generate_showdown_chat(
            seven_card_stud_game
        )
    )

    for chat_entry in showdown_messages:
        post_seven_card_stud_chat(
            chat_entry
        )

    if seven_card_stud_game.player_busted:
        state.seven_card_stud_next_hand_at = 0

        if (
                "out of chips"
                not in seven_card_stud_game.result_text.lower()
        ):
            seven_card_stud_game.result_text += (
                " You are out of chips."
            )

        state.seven_card_stud_session_end_at = (
                pygame.time.get_ticks()
                + SEVEN_CARD_STUD_SESSION_END_DELAY
        )

        return

    if seven_card_stud_game.all_npcs_busted():
        state.seven_card_stud_next_hand_at = 0

        fan_gain = 0

        if not state.seven_card_stud_table_sweep_rewarded:
            leveling.process_achievement_event("poker_table_clear", game="seven_card_stud")
            if state.current_game_mode == "career":
                fan_gain = career_rewards.award_fans_for_rating_win(
                    SEVEN_CARD_STUD_TABLE_SWEEP_RATING_BONUS,
                    "Seven-Card Stud table clear"
                )
                state.career_event_has_activity = True
            state.seven_card_stud_table_sweep_rewarded = True

        seven_card_stud_game.result_text += " TABLE CLEARED!"
        if state.current_game_mode == "career":
            seven_card_stud_game.result_text += (
                " Rating settles on cash-out. "
                f"+{fan_gain:,} Fans."
            )

        state.seven_card_stud_session_end_at = (
                pygame.time.get_ticks()
                + SEVEN_CARD_STUD_SESSION_END_DELAY
        )


def loop_event_seven_card_stud_buy_in(event):
    """Old main-loop event branch for STATE_SEVEN_CARD_STUD_BUY_IN."""
    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):
        buy_in_action = (
            get_seven_card_stud_buy_in_action(
                state.game_mouse_pos,
                state.career_cash,
                table_stakes.SEVEN_CARD_STUD_MIN_BUY_IN
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
                    free_play_select.finish_free_play_sandbox()
                    state.current_state = state_names.STATE_FREE_PLAY_SELECT
                else:
                    state.current_state = state_names.STATE_CAREER_EVENT_SELECT

            elif action_type == "buy_in":
                sounds.audio.play_sound(
                    "button_click"
                )

                start_seven_card_stud_session(
                    amount
                )


def loop_event_seven_card_stud(event):
    """Old main-loop event branch for STATE_SEVEN_CARD_STUD."""

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
                state.seven_card_stud_next_hand_at = 0
        return

    if (
            event.type == pygame.MOUSEWHEEL
            and state.game_mouse_pos is not None
            and STUD_LOG_RECT.collidepoint(
                state.game_mouse_pos
            )
    ):
        scroll_seven_card_stud_panel(
            event.y,
            seven_card_stud_game
        )

    elif (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):
        if handle_seven_card_stud_panel_click(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )
            return

        stud_action = (
            get_seven_card_stud_action(
                state.game_mouse_pos,
                seven_card_stud_game
            )
        )

        if (
                stud_action
                == STUD_ACTION_NEXT_HAND
        ):
            if (
                    seven_card_stud_game.all_npcs_busted()
                    and not seven_card_stud_game.player_busted
            ):
                sounds.audio.play_sound(
                    "button_click"
                )

                process_seven_card_stud_showdown()
                finish_seven_card_stud_session()

            elif (
                    seven_card_stud_game.player_stack > 0
                    and not seven_card_stud_game.player_busted
            ):
                sounds.audio.play_sound(
                    "button_click"
                )

                state.seven_card_stud_next_hand_at = 0

                if seven_card_stud_game.start_hand():
                    sounds.audio.play_sound(
                        "card_draw"
                    )

        elif (
                stud_action
                == STUD_ACTION_FOLD
        ):
            if seven_card_stud_game.player_fold():
                sounds.audio.play_sound(
                    "button_click"
                )

                state.seven_card_stud_session_net = (
                        seven_card_stud_game.player_stack
                        - state.seven_card_stud_starting_stack
                )

                state.career_event_has_activity = True

        elif (
                stud_action
                == STUD_ACTION_CHECK_CALL
        ):
            amount_to_call = (
                seven_card_stud_game
                .get_player_amount_to_call()
            )

            if amount_to_call > 0:
                state.success = (
                    seven_card_stud_game.player_call()
                )
                state.player_chat_action = "call"
            else:
                state.success = (
                    seven_card_stud_game.player_check()
                )
                state.player_chat_action = "check"

            if state.success:
                if amount_to_call > 0:
                    holdem_screen.play_texas_holdem_chip_sound()
                else:
                    sounds.audio.play_sound(
                        "poker_check"
                    )

                post_seven_card_stud_chat(
                    generate_player_action_reaction(
                        seven_card_stud_game,
                        state.player_chat_action
                    )
                )

                schedule_seven_card_stud_npc_action()

        elif (
                stud_action
                == STUD_ACTION_BET_RAISE
        ):
            wager_target = (
                seven_card_stud_game
                .get_player_fixed_bet_or_raise_to()
            )

            if seven_card_stud_game.current_bet == 0:
                state.player_chat_action = "bet"
                state.success = (
                    seven_card_stud_game.player_bet(
                        wager_target
                    )
                )
            else:
                state.player_chat_action = "raise"
                state.success = (
                    seven_card_stud_game.player_raise(
                        wager_target
                    )
                )

            if state.success:
                holdem_screen.play_texas_holdem_chip_sound()

                post_seven_card_stud_chat(
                    generate_player_action_reaction(
                        seven_card_stud_game,
                        state.player_chat_action
                    )
                )

                schedule_seven_card_stud_npc_action()

        elif (
                stud_action
                == STUD_ACTION_OPTIONS
        ):
            sounds.audio.play_sound("button_click")
            toggle_holdem_options()

        elif (
                stud_action
                == STUD_ACTION_RETURN
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            finish_seven_card_stud_session()


def loop_draw_seven_card_stud_buy_in():
    """Old draw-chain branch for STATE_SEVEN_CARD_STUD_BUY_IN."""
    draw_seven_card_stud_buy_in(
        window.game_surface,
        state.game_mouse_pos,
        state.career_cash,
        panels.draw_submenu_background,
        minimum_buy_in=table_stakes.SEVEN_CARD_STUD_MIN_BUY_IN
    )


def loop_draw_seven_card_stud():
    """Old draw-chain branch for STATE_SEVEN_CARD_STUD."""
    seven_card_stud_next_hand_seconds = None

    if (
            seven_card_stud_game.hand_complete
            and state.seven_card_stud_next_hand_at > 0
    ):
        remaining_ms = max(
            0,
            state.seven_card_stud_next_hand_at
            - pygame.time.get_ticks()
        )

        seven_card_stud_next_hand_seconds = (
            remaining_ms + 999
        ) // 1000

    draw_seven_card_stud(
        window.game_surface,
        state.game_mouse_pos,
        seven_card_stud_game,
        table.game.card_fronts,
        table.game.get_card_back_surface(),
        panels.draw_submenu_background,
        game_portraits.draw_npc_portrait,
        state.player_name,
        table.game.felt_surface,
        next_hand_seconds=(
            seven_card_stud_next_hand_seconds
        )
    )

    draw_holdem_options_overlay(
        window.game_surface,
        state.game_mouse_pos
    )


def loop_late_seven_card_stud():
    """Old timed-NPC branch for STATE_SEVEN_CARD_STUD (runs after drawing, as before)."""

    now = pygame.time.get_ticks()

    # ==================================================
    # Make sure NPC-first Stud streets are scheduled
    # ==================================================

    if (
            not seven_card_stud_game.hand_complete
            and seven_card_stud_game.current_stage
            in seven_card_stud_game.STUD_STAGES
            and seven_card_stud_game.current_actor
            not in (
                0,
                -1,
            )
            and state.seven_card_stud_next_npc_action_at == 0
            and not seven_card_stud_game.is_betting_round_complete()
    ):
        state.seven_card_stud_next_npc_action_at = (
                now
                + get_holdem_npc_delay()
        )

    # ==================================================
    # Delayed player win sound
    # ==================================================

    if (
            state.seven_card_stud_hand_win_sound_at > 0
            and now >= state.seven_card_stud_hand_win_sound_at
    ):
        sounds.audio.play_sound(
            "poker_hand_win"
        )

        state.seven_card_stud_hand_win_sound_at = 0

    process_seven_card_stud_showdown()

    # ==================================================
    # Start next-hand countdown
    # ==================================================

    if (
            seven_card_stud_game.hand_complete
            and seven_card_stud_game.current_stage == "showdown"
            and state.seven_card_stud_next_hand_at == 0
            and state.seven_card_stud_session_end_at == 0
            and is_holdem_auto_deal_enabled()
            and seven_card_stud_game.player_stack > 0
            and not seven_card_stud_game.player_busted
            and not seven_card_stud_game.all_npcs_busted()
    ):
        state.seven_card_stud_next_hand_at = (
                now
                + get_holdem_next_hand_delay()
        )

    # ==================================================
    # Run one NPC betting action
    # ==================================================

    if (
            state.seven_card_stud_next_npc_action_at > 0
            and now >= state.seven_card_stud_next_npc_action_at
            and not seven_card_stud_game.hand_complete
    ):
        state.seven_card_stud_next_npc_action_at = 0

        acting_actor = (
            seven_card_stud_game.current_actor
        )

        action_success = (
            seven_card_stud_game.run_next_npc_action()
        )

        if (
                action_success
                and acting_actor > 0
        ):
            acting_npc_index = (
                    acting_actor - 1
            )

            play_seven_card_stud_npc_action_sound(
                acting_npc_index
            )

            post_seven_card_stud_chat(
                generate_npc_action_chat(
                    seven_card_stud_game,
                    acting_npc_index
                )
            )

        if (
                not seven_card_stud_game.is_betting_round_complete()
                and seven_card_stud_game.current_actor
                not in (
                    0,
                    -1,
                )
        ):
            state.seven_card_stud_next_npc_action_at = (
                    now
                    + get_holdem_npc_delay()
            )

    # ==================================================
    # Finished betting round -> schedule next street
    # ==================================================

    if (
            not seven_card_stud_game.hand_complete
            and seven_card_stud_game.current_stage
            in seven_card_stud_game.STUD_STAGES
            and seven_card_stud_game.is_betting_round_complete()
            and state.seven_card_stud_round_advance_at == 0
    ):
        state.seven_card_stud_round_advance_at = (
                now
                + get_holdem_street_delay()
        )

        seven_card_stud_game.current_actor = -1

    # ==================================================
    # Advance Third -> Fourth -> ... -> Showdown
    # ==================================================

    if (
            state.seven_card_stud_round_advance_at > 0
            and now >= state.seven_card_stud_round_advance_at
    ):
        state.seven_card_stud_round_advance_at = 0

        previous_stage = (
            seven_card_stud_game.current_stage
        )

        advanced = (
            seven_card_stud_game.advance_after_betting_round()
        )

        new_stage = (
            seven_card_stud_game.current_stage
        )

        if (
                advanced
                and previous_stage != new_stage
                and new_stage
                in seven_card_stud_game.STUD_STAGES
        ):
            sounds.audio.play_sound(
                "card_draw"
            )

        if (
                advanced
                and not seven_card_stud_game.hand_complete
                and new_stage
                in seven_card_stud_game.STUD_STAGES
                and seven_card_stud_game.current_actor
                not in (
                    0,
                    -1,
                )
        ):
            schedule_seven_card_stud_npc_action()

    # ==================================================
    # Automatically start next hand
    # ==================================================

    if (
            state.seven_card_stud_next_hand_at > 0
            and now >= state.seven_card_stud_next_hand_at
    ):
        state.seven_card_stud_next_hand_at = 0

        if seven_card_stud_game.start_hand():
            sounds.audio.play_sound(
                "card_draw"
            )

    # ==================================================
    # Session finished
    # ==================================================

    if (
            state.seven_card_stud_session_end_at > 0
            and now >= state.seven_card_stud_session_end_at
    ):
        state.seven_card_stud_session_end_at = 0

        finish_seven_card_stud_session()
