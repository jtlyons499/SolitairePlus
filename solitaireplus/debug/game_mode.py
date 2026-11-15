"""The "debug" game mode of the F10 debug launchers, and the way back out of it (B22).

Some debug launchers play a night or game outside the Career rules by setting
state.current_game_mode to "debug". The mode they replaced is kept here and put back when the
debug night ends, so later real Career nights record their results again.
"""
import copy

from solitaireplus.app import state


def enter_debug_game_mode():
    """Switch to the "debug" game mode, remembering the mode to go back to.

    A second debug launcher during a debug night keeps the mode from before the first one.
    Returns True when this call switched the mode on, False when it was already "debug": a
    launcher that then fails to start ends the debug mode only if it switched it on, so an
    earlier debug session the player goes back to stays in "debug" mode.
    """
    if state.current_game_mode == "debug":
        return False
    state.debug_saved_game_mode = state.current_game_mode
    state.current_game_mode = "debug"
    return True


def end_debug_game_mode():
    """Leave the "debug" game mode for the mode from before the debug launcher.

    Does nothing to the mode when it is not "debug" (a debug night that kept the Career mode).
    """
    if state.current_game_mode == "debug":
        state.current_game_mode = state.debug_saved_game_mode
    state.debug_saved_game_mode = None


# What a debug launcher replaces when it prepares its own night: the night in progress (entry,
# result log, session totals). Kept so Back from the poker table picker, or a launcher that fails
# to start, can put the player's real night back untouched (review of B21/B22).
NIGHT_FIELDS = (
    "career_event_entry", "career_event_has_activity", "career_event_result_log", "career_event_news_posted",
    "texas_holdem_session_net", "five_card_draw_session_net", "seven_card_stud_session_net",
    "blackjack_session_net", "blackjack_session_rating_change", "roulette_session_net",
    "horse_races_session_net", "horse_races_last_rewarded_races",
    "faro_session_net", "five_o_poker_session_net", "blind_mans_bluff_session_net",
    "arcade_night_tokens_spent", "arcade_night_tickets_won",
)
_MISSING = object()


def keep_night_context():
    """A copy of the night in progress, for restore_night_context()."""
    return {name: copy.deepcopy(getattr(state, name, _MISSING)) for name in NIGHT_FIELDS}


def restore_night_context(saved):
    """Put back a night kept by keep_night_context() (None: nothing kept, nothing to do)."""
    if not saved:
        return
    for name, value in saved.items():
        if value is _MISSING:
            if hasattr(state, name):
                delattr(state, name)
        else:
            setattr(state, name, value)
