"""Run the real Hold'em, Five-Card Draw, Seven-Card Stud, Five-O and Blind Man's Bluff screens in a test.

    from tests.support.poker_screens import OPPONENTS, ScreenHarness

    def setUp(self):
        self.screen = ScreenHarness(self)          # restores app state when the test ends
        game = self.screen.stub(holdem_screen, TexasHoldemGame())
        self.screen.ticks = 1000                   # pygame.time.get_ticks() for the screen

stub() swaps the screen module's engine instance for `game` and replaces career cash-outs, rating
events, achievements, sounds and saving with no-ops (the approach of
tests/games/poker/test_holdem_session_end_timer.py), so the real session starters, finishers and timed loops
run without a window. Fan awards for cash wins are recorded in `cash_wins`. Only the names a
screen module has are replaced. The Five-O and Blind Man's Bluff screens pick their own
opponents, so for them the NPC pickers return OPPONENTS.

The engines shuffle with the module-level random, so the harness seeds it (seed=...) and
restores the previous random state when the test ends: every run deals the same cards.
"""
import os
import random
from types import SimpleNamespace
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from solitaireplus.app import state

# The engine instance each screen module keeps.
GAME_ATTRIBUTE = {
    "holdem_screen": "texas_holdem_game",
    "five_card_draw_screen": "five_card_draw_game",
    "seven_card_stud_screen": "seven_card_stud_game",
    "five_o_screen": "five_o_poker_game",
    "blind_mans_bluff_screen": "blind_mans_bluff_game",
}

# Four opponents: every Hold'em-family session starter needs four.
OPPONENTS = [{"id": f"screen_test_npc{seat}", "name": f"Rival {seat}"} for seat in range(1, 5)]


def _no_op(*args, **kwargs):
    return None


class ScreenHarness:
    def __init__(self, testcase, seed="poker-screens"):
        saved = {name: value for name, value in vars(state).items() if not name.startswith("__")}
        random_state = random.getstate()
        testcase.addCleanup(random.setstate, random_state)
        random.seed(seed)

        def restore_state():
            for name, value in saved.items():
                setattr(state, name, value)

        testcase.addCleanup(restore_state)
        self.testcase = testcase
        self.ticks = 0
        self.cash_wins = []
        ticks = mock.patch.object(pygame.time, "get_ticks", lambda: self.ticks)
        ticks.start()
        testcase.addCleanup(ticks.stop)

        state.current_game_mode = "career"
        state.career_cash = 5000
        state.holdem_table_speed = "normal"
        state.holdem_auto_deal_enabled = True

    def stub(self, module, game):
        """Point `module` (a table screen) at `game` and stub its career side effects."""
        screen = module.__name__.rsplit(".", 1)[-1]
        stubs = {
            GAME_ATTRIBUTE[screen]: game,
            "table_stakes": SimpleNamespace(
                TEXAS_HOLDEM_MIN_BUY_IN=100,
                FIVE_CARD_DRAW_MIN_BUY_IN=100,
                SEVEN_CARD_STUD_MIN_BUY_IN=100,
                FIVE_O_POKER_MIN_BUY_IN=100,
                BLIND_MANS_BLUFF_MIN_BUY_IN=100,
                get_poker_starting_stack=lambda: 1000,
                get_poker_ante=lambda stack, high_stakes=False: 10,
                get_niche_poker_starting_stack=lambda minimum_buy_in=100: 1000,
            ),
            "game_globals": SimpleNamespace(game_namespace=dict),
            "free_play_select": SimpleNamespace(finish_free_play_sandbox=_no_op),
            "sounds": SimpleNamespace(audio=SimpleNamespace(play_sound=_no_op)),
            "leveling": SimpleNamespace(award_game_xp=_no_op, process_achievement_event=_no_op),
            "career_rewards": SimpleNamespace(
                rate_poker_cash_out=_no_op,
                lose_fans_for_bad_result=_no_op,
                award_fans_for_cash_win=lambda amount, label: self.cash_wins.append(amount),
                award_fans_for_rating_win=lambda *args: 0,
            ),
            "career_saving": SimpleNamespace(auto_save_career=_no_op),
            "track_night_cash": _no_op,
            "record_poker_showdown": _no_op,
            "generate_showdown_chat": lambda game: [],
            "night": SimpleNamespace(record_career_event_result=_no_op),
            "training": SimpleNamespace(TRAINING_RATING_REWARDS={
                "blind_mans_bluff": {"profit": 0, "break_even": 0, "loss": 0}}),
        }
        if screen in ("five_o_screen", "blind_mans_bluff_screen"):
            stubs["get_random_npc"] = lambda *args, **kwargs: dict(OPPONENTS[0])
            stubs["get_random_npc_group"] = lambda count, *args, **kwargs: [dict(npc) for npc in OPPONENTS[:count]]
        for name, value in stubs.items():
            if not hasattr(module, name):
                continue
            patcher = mock.patch.object(module, name, value)
            patcher.start()
            self.testcase.addCleanup(patcher.stop)
        return game
