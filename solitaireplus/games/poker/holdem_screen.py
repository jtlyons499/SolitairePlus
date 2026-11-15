"""Texas Hold'em table and buy-in screens, sessions, showdowns and timed NPC turns (moved out of legacy.py)."""
from solitaireplus.games.poker.holdem_ui import ACTION_BET_RAISE as HOLDEM_ACTION_BET_RAISE
from solitaireplus.games.poker.holdem_ui import ACTION_CHECK_CALL as HOLDEM_ACTION_CHECK_CALL
from solitaireplus.games.poker.holdem_ui import ACTION_FOLD as HOLDEM_ACTION_FOLD
from solitaireplus.games.poker.holdem_ui import ACTION_NEXT_HAND as HOLDEM_ACTION_NEXT_HAND
from solitaireplus.games.poker.holdem_ui import ACTION_RETURN as HOLDEM_ACTION_RETURN
from solitaireplus.games.poker.holdem_ui import HOLDEM_LOG_RECT
from solitaireplus.games.poker.holdem import TexasHoldemGame
from solitaireplus.games.poker.holdem_ui import add_holdem_chat_message
from solitaireplus.career import career_rewards
from solitaireplus.career import career_saving
from solitaireplus.games.poker.holdem_ui import clear_holdem_manual_bet
from solitaireplus.games.poker.holdem_ui import drag_holdem_bet_slider
from solitaireplus.games.poker.holdem_ui import draw_texas_holdem
from solitaireplus.games.poker.holdem_ui import draw_texas_holdem_buy_in
from solitaireplus.games.poker.holdem_chat import generate_npc_action_chat
from solitaireplus.games.poker.holdem_chat import generate_player_action_reaction
from solitaireplus.games.poker.holdem_chat import generate_showdown_chat
from solitaireplus.games.poker.holdem_ui import get_holdem_bet_amount
from solitaireplus.games.poker.holdem_ui import get_holdem_next_hand_delay
from solitaireplus.games.poker.holdem_ui import get_holdem_npc_delay
from solitaireplus.games.poker.holdem_ui import get_holdem_street_delay
from solitaireplus.npc.manager import get_random_npc
from solitaireplus.games.poker.holdem_ui import get_texas_holdem_action
from solitaireplus.games.poker.holdem_ui import get_texas_holdem_buy_in_action
from solitaireplus.games.poker.holdem_ui import handle_holdem_manual_bet_click
from solitaireplus.games.poker.holdem_ui import handle_holdem_manual_bet_key
from solitaireplus.games.poker.holdem_ui import handle_holdem_options_click
from solitaireplus.games.poker.holdem_ui import handle_holdem_panel_click
from solitaireplus.games.poker.recap import handle_recap_action
from solitaireplus.games.poker.holdem_ui import holdem_log_history
from solitaireplus.games.poker.holdem_ui import is_holdem_auto_deal_enabled
from solitaireplus.games.poker.holdem_ui import is_holdem_options_open
import pygame
import random
from solitaireplus.career.rating_events import record_poker_showdown
from solitaireplus.games.poker.holdem_ui import scroll_holdem_log
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.games.poker.holdem_ui import stop_holdem_bet_slider_drag
from solitaireplus.games.poker.holdem_ui import toggle_holdem_options
from solitaireplus.career.session_summary import track_night_cash
from solitaireplus.games.poker.holdem_ui import update_holdem_bet_slider
from solitaireplus.app.lazy import lazy
table_stakes = lazy("solitaireplus.games.poker.table_stakes")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
panels = lazy("solitaireplus.ui.panels")
leveling = lazy("solitaireplus.profile.leveling")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")


texas_holdem_game = TexasHoldemGame()

TEXAS_HOLDEM_NPC_DELAY = 1200
TEXAS_HOLDEM_STREET_DELAY = 1200

TEXAS_HOLDEM_NEXT_HAND_DELAY = 15000


TEXAS_HOLDEM_SESSION_END_DELAY = 5000

TEXAS_HOLDEM_TABLE_SWEEP_RATING_BONUS = 100


def get_holdem_player_winnings():
    total = 0
    for award in getattr(texas_holdem_game, "last_pot_awards", []):
        winners = list(award.get("winners", []))
        if 0 not in winners or not winners:
            continue
        ordered = sorted(winners)
        share = int(award.get("share", 0) or 0)
        remainder = int(award.get("remainder", 0) or 0)
        player_share = share
        if ordered.index(0) < remainder:
            player_share += 1
        total += player_share
    return total


def post_texas_holdem_chat(
        chat_entry
):

    if not chat_entry:
        return

    speaker, message = (
        chat_entry
    )

    add_holdem_chat_message(
        speaker,
        message
    )

def process_texas_holdem_showdown():

    # ==================================================
    # Only process completed showdowns
    # ==================================================

    if not texas_holdem_game.hand_complete:
        return

    if (
            texas_holdem_game.current_stage
            != "showdown"
    ):
        return

    # ==================================================
    # Don't process the same showdown every frame
    # ==================================================

    if (
            texas_holdem_game.hand_number
            == state.texas_holdem_last_processed_showdown_hand
    ):
        return

    state.texas_holdem_last_processed_showdown_hand = (
        texas_holdem_game.hand_number
    )
    record_poker_showdown(texas_holdem_game)

    # ==================================================
    # SHOWDOWN AUDIO
    # ==================================================

    sounds.audio.play_sound(
        "card_flip"
    )

    # Player won at least one pot.
    if 0 in texas_holdem_game.winner_indexes:
        state.texas_holdem_hand_win_sound_at = (
                pygame.time.get_ticks()
                + 450
        )
        career_rewards.award_fans_for_cash_win(
            max(1, int(getattr(texas_holdem_game, "last_resolved_pot", 0))),
            "Hold'em hand win"
        )

        holdem_result = texas_holdem_game.get_showdown_result(0)
        holdem_score = holdem_result[0] if holdem_result else None
        leveling.process_achievement_event(
            "holdem_hand_win",
            winnings=get_holdem_player_winnings(),
            category=(holdem_score[0] if holdem_score else None),
            high=(holdem_score[1] if holdem_score and len(holdem_score) > 1 else None),
        )

    # ==================================================
    # NPC showdown / knockout chat
    # ==================================================

    showdown_messages = (
        generate_showdown_chat(
            texas_holdem_game
        )
    )

    for chat_entry in showdown_messages:

        post_texas_holdem_chat(
            chat_entry
        )

    # ==================================================
    # PLAYER BUSTED
    # ==================================================

    if texas_holdem_game.player_busted:

        state.texas_holdem_next_hand_at = 0

        texas_holdem_game.result_text += (
            " You are out of chips."
        )

        state.texas_holdem_session_end_at = (
            pygame.time.get_ticks()
            + TEXAS_HOLDEM_SESSION_END_DELAY
        )

        return

    # ==================================================
    # PLAYER CLEARED THE TABLE
    # ==================================================

    if texas_holdem_game.all_npcs_busted():

        state.texas_holdem_next_hand_at = 0

        fan_gain = 0

        if not state.texas_holdem_table_sweep_rewarded:
            leveling.process_achievement_event("poker_table_clear", game="texas_holdem")
            if state.current_game_mode == "career":
                fan_gain = career_rewards.award_fans_for_rating_win(
                    TEXAS_HOLDEM_TABLE_SWEEP_RATING_BONUS,
                    "Hold'em table clear"
                )
                state.career_event_has_activity = True
            state.texas_holdem_table_sweep_rewarded = True

        texas_holdem_game.result_text += " TABLE CLEARED!"
        if state.current_game_mode == "career":
            texas_holdem_game.result_text += (
                " Rating settles on cash-out. "
                f"+{fan_gain:,} Fans."
            )

        state.texas_holdem_session_end_at = (
            pygame.time.get_ticks()
            + TEXAS_HOLDEM_SESSION_END_DELAY
        )

# ==================================================
# TEXAS HOLD'EM AUDIO HELPERS
# ==================================================

def play_texas_holdem_chip_sound():

    sound_name = random.choice(
        (
            "poker_chips_1",
            "poker_chips_2",
            "poker_chips_3",
        )
    )

    sounds.audio.play_sound(
        sound_name
    )


def play_texas_holdem_npc_action_sound(
        npc_index
):

    if not (
            0
            <= npc_index
            < len(
                texas_holdem_game.npc_action_texts
            )
    ):
        return

    action_text = (
        texas_holdem_game
        .npc_action_texts[
            npc_index
        ]
        .strip()
        .lower()
    )

    # Check
    if action_text.startswith(
            "checked"
    ):

        sounds.audio.play_sound(
            "poker_check"
        )

        return

    # Bet / Call / Raise
    if action_text.startswith(
            (
                "called",
                "bet",
                "raised",
            )
    ):

        play_texas_holdem_chip_sound()


def play_texas_holdem_new_hand_sound():

    sounds.audio.play_sound(
        "card_draw"
    )


def play_texas_holdem_street_sound():

    sounds.audio.play_sound(
        "card_draw"
    )


# ==================================================
# SCHEDULE NEXT NPC ACTION
# ==================================================

def schedule_texas_holdem_npc_action():

    if (
            not texas_holdem_game.hand_complete
            and not texas_holdem_game.betting_round_complete
            and texas_holdem_game.current_actor != 0
    ):
        state.texas_holdem_next_npc_action_at = (
                pygame.time.get_ticks()
                + get_holdem_npc_delay()
        )

def get_texas_holdem_opponents():

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

def start_texas_holdem_session(
        starting_stack=None,
        opponents=None
):

    # ==================================================
    # Determine / validate buy-in
    # ==================================================

    if starting_stack is None:

        # Debug/direct-entry fallback.
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
            < table_stakes.TEXAS_HOLDEM_MIN_BUY_IN
    ):

        print(
            "Not enough cash to enter Poker Night."
        )

        return False

    # ==================================================
    # Ante scales from selected buy-in
    # ==================================================

    ante = (
        table_stakes.get_poker_ante(
            starting_stack,
            high_stakes=False
        )
    )

    # ==================================================
    # Choose opponents
    # ==================================================

    if opponents is None:
        opponents = get_texas_holdem_opponents()
    else:
        opponents = list(opponents)[:4]

    if len(opponents) < 4:

        print(
            "Could not find four Hold'em opponents."
        )

        return False

    # ==================================================
    # Career cash -> poker stack
    # ==================================================

    state.career_cash -= (
        starting_stack
    )

    state.texas_holdem_starting_stack = (
        starting_stack
    )

    state.texas_holdem_session_net = 0

    state.texas_holdem_buy_in_active = True
    texas_holdem_game.session_xp_rewarded = False
    state.texas_holdem_last_processed_showdown_hand = 0
    # The table-clear bonus is paid once per session (as in Draw and Stud).
    state.texas_holdem_table_sweep_rewarded = False

    # ==================================================
    # Reset runtime timers
    # ==================================================

    state.texas_holdem_next_npc_action_at = 0
    state.texas_holdem_round_advance_at = 0
    state.texas_holdem_next_hand_at = 0
    state.texas_holdem_session_end_at = 0

    # ==================================================
    # Start poker session
    # ==================================================

    texas_holdem_game.career_session_rated = state.current_game_mode == "career"
    texas_holdem_game.learning_store = legacy.game_namespace().get("career_poker_learning") if state.current_game_mode == "career" else None
    texas_holdem_game.start_session(
        opponents,
        starting_stack,
        ante
    )

    if texas_holdem_game.start_hand():

        play_texas_holdem_new_hand_sound()

    state.career_event_has_activity = True

    state.current_state = state_names.STATE_TEXAS_HOLDEM

    return True

def finish_texas_holdem_session():

    if state.texas_holdem_buy_in_active:

        state.career_cash += (
            texas_holdem_game.player_stack
        )

        state.texas_holdem_session_net = (
            texas_holdem_game.player_stack
            - state.texas_holdem_starting_stack
        )

        state.texas_holdem_buy_in_active = False
        track_night_cash(legacy.game_namespace(), "texas_holdem", state.texas_holdem_session_net)
        career_rewards.rate_poker_cash_out("texas_holdem", texas_holdem_game)

    if (
            texas_holdem_game.current_stage
            != "ready"
    ):

        state.career_event_has_activity = True

    state.texas_holdem_hand_win_sound_at = 0

    if (
            len(getattr(texas_holdem_game, "rating_seen_hands", ())) > 0
            and not getattr(texas_holdem_game, "session_xp_rewarded", False)
    ):
        won_session = state.texas_holdem_session_net > 0
        leveling.award_game_xp("texas_holdem", won=won_session)
        if state.current_game_mode == "career" and state.texas_holdem_session_net < 0:
            legacy.lose_fans_for_bad_result(
                "Rough Hold'em session",
                net_loss=abs(state.texas_holdem_session_net),
            )
        texas_holdem_game.session_xp_rewarded = True

    if state.current_game_mode == "free":
        legacy.finish_free_play_sandbox()
        state.current_state = state_names.STATE_FREE_PLAY_SELECT
    else:
        state.current_state = state_names.STATE_CAREER_EVENT_SELECT
        career_saving.auto_save_career()


def loop_event_texas_holdem_buy_in(event):
    """Old main-loop event branch for STATE_TEXAS_HOLDEM_BUY_IN."""

    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):

        buy_in_action = (
            get_texas_holdem_buy_in_action(
                state.game_mouse_pos,
                state.career_cash,
                table_stakes.TEXAS_HOLDEM_MIN_BUY_IN
            )
        )

        if buy_in_action is not None:

            action_type, amount = (
                buy_in_action
            )

            # ------------------------------------------
            # Back
            # ------------------------------------------

            if action_type == "back":
                sounds.audio.play_sound(
                    "button_click"
                )

                if state.current_game_mode == "free":
                    legacy.finish_free_play_sandbox()
                    state.current_state = state_names.STATE_FREE_PLAY_SELECT
                else:
                    state.current_state = state_names.STATE_CAREER_EVENT_SELECT

            # ------------------------------------------
            # Buy in
            # ------------------------------------------

            elif (
                    action_type
                    == "buy_in"
            ):

                sounds.audio.play_sound(
                    "button_click"
                )

                start_texas_holdem_session(
                    amount
                )


def loop_event_texas_holdem(event):
    """Old main-loop event branch for STATE_TEXAS_HOLDEM."""

    if getattr(texas_holdem_game, "recap_open", False):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            from solitaireplus.games.poker.recap import get_recap_action
            handle_recap_action(texas_holdem_game, get_recap_action(state.game_mouse_pos, texas_holdem_game))
            if not texas_holdem_game.recap_open:
                state.texas_holdem_next_hand_at = 0
                if texas_holdem_game.player_busted or texas_holdem_game.all_npcs_busted():
                    state.texas_holdem_session_end_at = pygame.time.get_ticks() + TEXAS_HOLDEM_SESSION_END_DELAY
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            texas_holdem_game.recap_open = False
            state.texas_holdem_next_hand_at = 0
            if texas_holdem_game.player_busted or texas_holdem_game.all_npcs_busted():
                state.texas_holdem_session_end_at = pygame.time.get_ticks() + TEXAS_HOLDEM_SESSION_END_DELAY
        return

    # ==================================================
    # Keyboard: manual bet / raise-to entry only
    # ==================================================

    if event.type == pygame.KEYDOWN:

        handle_holdem_manual_bet_key(
            event,
            texas_holdem_game
        )

    # ==================================================
    # Game Log scrolling
    # ==================================================

    elif (
            event.type == pygame.MOUSEWHEEL
            and state.game_mouse_pos is not None
            and HOLDEM_LOG_RECT.collidepoint(
        state.game_mouse_pos
    )
    ):

        scroll_holdem_log(
            event.y,
            len(holdem_log_history)
        )

    # ==================================================
    # Drag bet slider
    # ==================================================

    elif (
            event.type == pygame.MOUSEMOTION
            and state.game_mouse_pos is not None
    ):

        drag_holdem_bet_slider(
            state.game_mouse_pos
        )


    # ==================================================
    # Release bet slider
    # ==================================================

    elif (
            event.type == pygame.MOUSEBUTTONUP
            and event.button == 1
    ):

        stop_holdem_bet_slider_drag()

    # ==================================================
    # Mouse controls
    # ==================================================

    elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):

        # ==================================================
        # Poker options overlay
        # ==================================================

        if is_holdem_options_open():

            option_changed = (
                handle_holdem_options_click(
                    state.game_mouse_pos
                )
            )

            if option_changed:
                sounds.audio.play_sound(
                    "button_click"
                )

            # Consume every click while overlay is open.
            return

        # ==================================================
        # Manual bet / raise-to entry
        # ==================================================

        if handle_holdem_manual_bet_click(
                state.game_mouse_pos,
                texas_holdem_game
        ):
            sounds.audio.play_sound("button_click")
            return

        # ==================================================
        # Log / Chat tabs
        # ==================================================

        panel_handled = (
            handle_holdem_panel_click(
                state.game_mouse_pos
            )
        )

        if panel_handled:

            sounds.audio.play_sound(
                "button_click"
            )

        else:

            # ==================================================
            # Bet slider / shortcut buttons
            # ==================================================

            slider_handled = (
                update_holdem_bet_slider(
                    state.game_mouse_pos,
                    texas_holdem_game
                )
            )

            if slider_handled:

                sounds.audio.play_sound(
                    "button_click"
                )

            else:

                # ==================================================
                # Main Hold'em controls
                # ==================================================

                holdem_action = (
                    get_texas_holdem_action(
                        state.game_mouse_pos,
                        texas_holdem_game
                    )
                )

                # ------------------------------------------
                # Next Hand
                # ------------------------------------------

                if handle_recap_action(texas_holdem_game, holdem_action):
                    if holdem_action != "recap_block":
                        sounds.audio.play_sound("button_click")
                    state.texas_holdem_next_hand_at = 0
                    if not texas_holdem_game.recap_open and (texas_holdem_game.player_busted or texas_holdem_game.all_npcs_busted()):
                        state.texas_holdem_session_end_at = pygame.time.get_ticks() + TEXAS_HOLDEM_SESSION_END_DELAY
                elif (
                        holdem_action
                        == HOLDEM_ACTION_NEXT_HAND
                ):

                    if (
                            texas_holdem_game.all_npcs_busted()
                            and not texas_holdem_game.player_busted
                    ):
                        sounds.audio.play_sound(
                            "button_click"
                        )

                        process_texas_holdem_showdown()

                        finish_texas_holdem_session()

                    elif (
                            texas_holdem_game.player_stack > 0
                            and not texas_holdem_game.player_busted
                    ):
                        sounds.audio.play_sound(
                            "button_click"
                        )

                        state.texas_holdem_next_hand_at = 0

                        if texas_holdem_game.start_hand():
                            play_texas_holdem_new_hand_sound()

                elif (
                        holdem_action
                        == HOLDEM_ACTION_FOLD
                ):

                    if texas_holdem_game.player_fold():
                        sounds.audio.play_sound(
                            "button_click"
                        )

                        state.texas_holdem_session_net = (
                                texas_holdem_game.player_stack
                                - state.texas_holdem_starting_stack
                        )

                        state.career_event_has_activity = True

                # ------------------------------------------
                # Check / Call
                # ------------------------------------------

                elif (
                        holdem_action
                        == HOLDEM_ACTION_CHECK_CALL
                ):

                    amount_to_call = (
                        texas_holdem_game
                        .get_player_amount_to_call()
                    )

                    if amount_to_call > 0:

                        state.success = (
                            texas_holdem_game
                            .player_call()
                        )

                    else:

                        state.success = (
                            texas_holdem_game
                            .player_check()
                        )

                    if state.success:

                        if amount_to_call > 0:

                            play_texas_holdem_chip_sound()

                            state.player_chat_action = (
                                "call"
                            )

                        else:

                            sounds.audio.play_sound(
                                "poker_check"
                            )

                            state.player_chat_action = (
                                "check"
                            )

                        post_texas_holdem_chat(
                            generate_player_action_reaction(
                                texas_holdem_game,
                                state.player_chat_action
                            )
                        )

                        schedule_texas_holdem_npc_action()

                # ------------------------------------------
                # Bet / Raise
                # ------------------------------------------

                elif (
                        holdem_action
                        == HOLDEM_ACTION_BET_RAISE
                ):

                    bet_amount = (
                        get_holdem_bet_amount(
                            texas_holdem_game
                        )
                    )

                    if (
                            texas_holdem_game.current_bet
                            == 0
                    ):

                        state.player_chat_action = (
                            "bet"
                        )

                        state.success = (
                            texas_holdem_game
                            .player_bet(
                                bet_amount
                            )
                        )

                    else:

                        state.player_chat_action = (
                            "raise"
                        )

                        state.success = (
                            texas_holdem_game
                            .player_raise(
                                bet_amount
                            )
                        )

                    if state.success:
                        play_texas_holdem_chip_sound()
                        clear_holdem_manual_bet()

                        post_texas_holdem_chat(
                            generate_player_action_reaction(
                                texas_holdem_game,
                                state.player_chat_action
                            )
                        )

                        schedule_texas_holdem_npc_action()

                # ------------------------------------------
                # Exit
                # ------------------------------------------

                elif (
                        holdem_action
                        == HOLDEM_ACTION_RETURN
                ):

                    sounds.audio.play_sound(
                        "button_click"
                    )

                    finish_texas_holdem_session()

                # ------------------------------------------
                # Options
                # ------------------------------------------

                elif holdem_action == "options":

                    sounds.audio.play_sound(
                        "button_click"
                    )

                    toggle_holdem_options()


def loop_draw_texas_holdem_buy_in():
    """Old draw-chain branch for STATE_TEXAS_HOLDEM_BUY_IN."""

    draw_texas_holdem_buy_in(
        window.game_surface,
        state.game_mouse_pos,
        state.career_cash,
        panels.draw_submenu_background,
        minimum_buy_in=table_stakes.TEXAS_HOLDEM_MIN_BUY_IN
    )


def loop_draw_texas_holdem():
    """Old draw-chain branch for STATE_TEXAS_HOLDEM."""

    texas_holdem_next_hand_seconds = None

    if (
            texas_holdem_game.hand_complete
            and state.texas_holdem_next_hand_at > 0
    ):
        remaining_ms = max(
            0,
            state.texas_holdem_next_hand_at
            - pygame.time.get_ticks()
        )

        texas_holdem_next_hand_seconds = (
            remaining_ms + 999
        ) // 1000

    draw_texas_holdem(
        window.game_surface,
        state.game_mouse_pos,
        texas_holdem_game,
        legacy.game.card_fronts,
        legacy.game.get_card_back_surface(),
        panels.draw_submenu_background,
        panels.draw_submenu_title,
        buttons.draw_menu_button,
        legacy.draw_npc_portrait,
        fonts.options_title_font,
        fonts.option_label_font,
        fonts.difficulty_detail_font,
        state.player_name,
        legacy.game.felt_surface,
        next_hand_seconds=(
            texas_holdem_next_hand_seconds
        )
    )


def loop_late_texas_holdem():
    """Old timed-NPC branch for STATE_TEXAS_HOLDEM (runs after drawing, as before)."""

    now = pygame.time.get_ticks()
    from solitaireplus.games.poker.turn_flow import repair_betting_turn
    repair_betting_turn(texas_holdem_game)

    # ==================================================
    # Make sure an NPC turn is always scheduled
    #
    # With rotating blinds, a new hand or street can
    # begin directly on an NPC rather than the player.
    # ==================================================

    if (
            not texas_holdem_game.hand_complete
            and texas_holdem_game.current_actor not in (
            0,
            -1
    )
            and state.texas_holdem_next_npc_action_at == 0
            and not texas_holdem_game.is_betting_round_complete()
    ):
        state.texas_holdem_next_npc_action_at = (
                now
                + get_holdem_npc_delay()
        )

    # ==================================================
    # Cancel pending auto-deal if user turns it off
    # ==================================================

    if not is_holdem_auto_deal_enabled():
        state.texas_holdem_next_hand_at = 0

    # ==================================================
    # Delayed winning-hand sound
    # ==================================================

    if (
            state.texas_holdem_hand_win_sound_at > 0
            and now
            >= state.texas_holdem_hand_win_sound_at
    ):
        sounds.audio.play_sound(
            "poker_hand_win"
        )

        state.texas_holdem_hand_win_sound_at = 0

    process_texas_holdem_showdown()
    if getattr(texas_holdem_game, "recap_open", False):
        state.texas_holdem_next_hand_at = 0
        state.texas_holdem_session_end_at = 0

    # ==================================================
    # Start next-hand countdown after showdown
    # ==================================================

    if (
            texas_holdem_game.hand_complete
            and texas_holdem_game.current_stage == "showdown"
            and state.texas_holdem_next_hand_at == 0
            and state.texas_holdem_session_end_at == 0
            and texas_holdem_game.player_stack > 0
            and not texas_holdem_game.player_busted
            and not texas_holdem_game.all_npcs_busted()
            and is_holdem_auto_deal_enabled()
            and not getattr(texas_holdem_game, "recap_open", False)
    ):
        state.texas_holdem_next_hand_at = (
                now
                + get_holdem_next_hand_delay()
        )

    # ==================================================
    # Run one scheduled NPC action
    # ==================================================

    if (
            state.texas_holdem_next_npc_action_at > 0
            and now >= state.texas_holdem_next_npc_action_at
            and not texas_holdem_game.hand_complete
    ):

        state.texas_holdem_next_npc_action_at = 0

        # Remember who is acting because
        # run_next_npc_action() advances current_actor.
        acting_actor = (
            texas_holdem_game.current_actor
        )

        action_success = (
            texas_holdem_game
            .run_next_npc_action()
        )

        if (
                action_success
                and acting_actor > 0
        ):
            acting_npc_index = (
                    acting_actor - 1
            )

            # ------------------------------------------
            # Action sound
            # ------------------------------------------

            play_texas_holdem_npc_action_sound(
                acting_npc_index
            )

            # ------------------------------------------
            # Personality chat
            # ------------------------------------------

            post_texas_holdem_chat(
                generate_npc_action_chat(
                    texas_holdem_game,
                    acting_npc_index
                )
            )

        # ------------------------------------------
        # Another NPC still needs to act
        # ------------------------------------------

        if (
                not texas_holdem_game
                        .is_betting_round_complete()
                and texas_holdem_game.current_actor != 0
        ):
            state.texas_holdem_next_npc_action_at = (
                    now
                    + get_holdem_npc_delay()
            )

    # ==================================================
    # Betting round has finished
    #
    # Schedule street advance ONCE.
    # This check happens every frame, so we cannot
    # get stuck after the final NPC acts.
    # ==================================================

    if (
            not texas_holdem_game.hand_complete
            and texas_holdem_game
            .is_betting_round_complete()
            and state.texas_holdem_round_advance_at == 0
    ):
        state.texas_holdem_round_advance_at = (
                now
                + get_holdem_street_delay()
        )

        # Nobody is actively taking a turn now.
        texas_holdem_game.current_actor = -1

    # ==================================================
    # Advance to flop / turn / river / showdown
    # ==================================================

    if (
            state.texas_holdem_round_advance_at > 0
            and now >= state.texas_holdem_round_advance_at
    ):

        state.texas_holdem_round_advance_at = 0

        previous_stage = (
            texas_holdem_game.current_stage
        )

        advanced = (
            texas_holdem_game
            .advance_after_betting_round()
        )

        new_stage = (
            texas_holdem_game.current_stage
        )

        # ==================================================
        # Flop / Turn / River card sound
        # ==================================================

        if (
                advanced
                and new_stage
                in (
                "flop",
                "turn",
                "river",
        )
                and new_stage
                != previous_stage
        ):
            play_texas_holdem_street_sound()

        # ==================================================
        # If the player is all-in, the new street may
        # begin directly with an NPC.
        # ==================================================

        if (
                advanced
                and not texas_holdem_game.hand_complete
                and texas_holdem_game.current_actor != 0
        ):
            schedule_texas_holdem_npc_action()

    # ==================================================
    # Automatically start next hand
    # ==================================================

    if (
            state.texas_holdem_next_hand_at > 0
            and now >= state.texas_holdem_next_hand_at
    ):
        state.texas_holdem_next_hand_at = 0

        texas_holdem_game.start_hand()

    # ==================================================
    # Poker session finished
    # ==================================================

    if (
            state.texas_holdem_session_end_at > 0
            and now >= state.texas_holdem_session_end_at
    ):
        state.texas_holdem_session_end_at = 0

        state.texas_holdem_next_hand_at = 0
        state.texas_holdem_next_npc_action_at = 0
        state.texas_holdem_round_advance_at = 0

        finish_texas_holdem_session()
