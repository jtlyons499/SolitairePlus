"""Career poker stakes: starting stacks, antes and minimum buy-ins shared by the poker tables (moved out of legacy.py)."""
from solitaireplus.app import state


TEXAS_HOLDEM_MIN_BUY_IN = 100
FIVE_CARD_DRAW_MIN_BUY_IN = 100
SEVEN_CARD_STUD_MIN_BUY_IN = 100
FIVE_O_POKER_MIN_BUY_IN = 100
BLIND_MANS_BLUFF_MIN_BUY_IN = 100


def get_poker_starting_stack():
    if state.career_cash <= 2000:
        return max(
            0,
            state.career_cash
        )

    return round(
        state.career_cash / 1000
    ) * 1000

def get_poker_ante(
        starting_stack,
        high_stakes=False
):
    if high_stakes:
        percentage = 0.05

    else:
        percentage = 0.01

    return max(
        1,
        round(
            starting_stack
            * percentage
        )
    )


# ==================================================
# FIVE-O POKER / BLIND MAN'S BLUFF HELPERS
# ==================================================

def get_niche_poker_starting_stack(minimum_buy_in=100):
    if state.career_cash < minimum_buy_in:
        return 0
    if state.career_cash <= 500:
        return state.career_cash
    return min(
        state.career_cash,
        2000,
        max(minimum_buy_in, int(round(state.career_cash * 0.25)))
    )
