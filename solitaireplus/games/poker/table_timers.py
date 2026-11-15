"""Screen timers shared by the Hold'em, Five-Card Draw and Seven-Card Stud tables.

Each table keeps its timers in solitaireplus/app/state.py as f"{prefix}_{name}" for every name in
TABLE_TIMERS (prefixes: texas_holdem, five_card_draw, seven_card_stud). A value of 0 means "not
scheduled"; otherwise it is the pygame tick at which the timer fires.
"""
from solitaireplus.app import state

TABLE_TIMERS = (
    "next_npc_action_at",
    "round_advance_at",
    "next_hand_at",
    "session_end_at",
    "hand_win_sound_at",
)


def reset_table_timers(prefix):
    """Cancel every pending timer of one table (session finish)."""
    for name in TABLE_TIMERS:
        setattr(state, f"{prefix}_{name}", 0)


def reset_table_session(prefix):
    """Session start: cancel the timers and forget the last session's showdown and sweep bonus."""
    reset_table_timers(prefix)
    setattr(state, f"{prefix}_last_processed_showdown_hand", 0)
    setattr(state, f"{prefix}_table_sweep_rewarded", False)
