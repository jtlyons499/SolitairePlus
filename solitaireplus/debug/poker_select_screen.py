"""The F10 menu's poker table opponent picker (moved out of legacy.py)."""
from solitaireplus.debug.poker_select import ACTION_BACK as DEBUG_POKER_ACTION_BACK
from solitaireplus.debug.poker_select import ACTION_CYCLE as DEBUG_POKER_ACTION_CYCLE
from solitaireplus.debug.poker_select import ACTION_RANDOMIZE as DEBUG_POKER_ACTION_RANDOMIZE
from solitaireplus.debug.poker_select import ACTION_START as DEBUG_POKER_ACTION_START
from solitaireplus.npc.manager import NPCS
from solitaireplus.debug.poker_select import cycle_selection as cycle_debug_poker_selection
from solitaireplus.debug.poker_select import draw_debug_poker_npc_select
from solitaireplus.debug.game_mode import end_debug_game_mode
from solitaireplus.debug.poker_select import get_debug_poker_select_action
from solitaireplus.debug.poker_select import make_default_selection as make_debug_poker_default_selection
import pygame
from solitaireplus.debug.game_mode import restore_night_context
from solitaireplus.debug.menu import show_debug_message
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
seven_card_stud_screen = lazy("solitaireplus.games.poker.seven_card_stud_screen")
holdem_screen = lazy("solitaireplus.games.poker.holdem_screen")
five_card_draw_screen = lazy("solitaireplus.games.poker.five_card_draw_screen")
game_portraits = lazy("solitaireplus.npc.game_portraits")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")


def get_debug_poker_selected_npcs():
    selected = []
    selected_ids = set(state.debug_poker_selected_ids)
    for npc_id in state.debug_poker_selected_ids:
        for npc in NPCS:
            if npc.get("id") == npc_id:
                selected.append(npc)
                break
    return selected[:4]


def start_debug_selected_poker_table():

    opponents = get_debug_poker_selected_npcs()
    if len(opponents) < 4:
        return False

    if state.debug_poker_select_game_id == "texas_holdem":
        return holdem_screen.start_texas_holdem_session(opponents=opponents)
    if state.debug_poker_select_game_id == "five_card_draw":
        return five_card_draw_screen.start_five_card_draw_session(opponents=opponents)
    if state.debug_poker_select_game_id == "seven_card_stud":
        return seven_card_stud_screen.start_seven_card_stud_session(opponents=opponents)
    return False


def handle_event(event):
    """Old main-loop event branch for STATE_DEBUG_POKER_NPC_SELECT."""
    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):
        selector_action = get_debug_poker_select_action(
            state.game_mouse_pos,
            can_start=(state.career_cash >= 100),
        )

        if selector_action is not None:
            action_name, action_value = selector_action

            if action_name == DEBUG_POKER_ACTION_BACK:
                sounds.audio.play_sound("button_click")
                # No table was played: leave the "debug" mode open_debug_poker_npc_select
                # switched on, so Close does not take it onto a real screen (B22). An earlier
                # debug session's mode stays.
                if state.debug_poker_select_entered_debug_mode:
                    end_debug_game_mode()
                state.debug_poker_select_entered_debug_mode = False
                restore_night_context(state.debug_poker_select_saved_night)
                state.debug_poker_select_saved_night = None
                state.current_state = state_names.STATE_DEBUG_MENU

            elif action_name == DEBUG_POKER_ACTION_RANDOMIZE:
                sounds.audio.play_sound("button_click")
                state.debug_poker_selected_ids = make_debug_poker_default_selection(
                    NPCS,
                    count=4,
                )

            elif action_name == DEBUG_POKER_ACTION_CYCLE:
                sounds.audio.play_sound("button_click")
                slot_index, state.direction = action_value
                state.debug_poker_selected_ids = cycle_debug_poker_selection(
                    NPCS,
                    state.debug_poker_selected_ids,
                    slot_index,
                    state.direction,
                )

            elif action_name == DEBUG_POKER_ACTION_START:
                sounds.audio.play_sound("button_click")
                if not start_debug_selected_poker_table():
                    show_debug_message("Add cash to play")

    return


def draw():
    """Old draw-chain branch for STATE_DEBUG_POKER_NPC_SELECT."""

    debug_game_labels = {
        "texas_holdem": "Texas Hold'em",
        "five_card_draw": "Five-Card Draw",
        "seven_card_stud": "Seven-Card Stud",
    }
    draw_debug_poker_npc_select(
        window.game_surface,
        state.game_mouse_pos,
        debug_game_labels.get(state.debug_poker_select_game_id, "Poker"),
        NPCS,
        state.debug_poker_selected_ids,
        portrait_loader=game_portraits.get_npc_portrait_surface,
        can_start=(state.career_cash >= 100),
        cash=state.career_cash,
    )


# The old loop drew this screen in its second draw chain (see app/loop.py).
DRAWS_LATE = True
