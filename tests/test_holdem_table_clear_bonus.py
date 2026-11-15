"""Phase 7 follow-up: the Hold'em table-clear bonus is paid once per session, not once per app run.

process_texas_holdem_showdown sets state.texas_holdem_table_sweep_rewarded when the player
busts every opponent, and nothing reset it, so only the first table clear after starting the
game paid the fan bonus and sent the 'poker_table_clear' achievement event. Draw and Stud
reset their flag in their session starters; Hold'em now does the same.
"""
import unittest
from types import SimpleNamespace
from unittest import mock

import pygame

from solitaireplus.app import state
from solitaireplus.games.poker import holdem_screen
from solitaireplus.games.poker.holdem import TexasHoldemGame


def _no_op(*args, **kwargs):
    return None


OPPONENTS = [{"id": f"npc{i}", "name": f"Rival {i}"} for i in range(4)]


class HoldemTableClearBonusTests(unittest.TestCase):
    def setUp(self):
        saved = {name: value for name, value in vars(state).items() if not name.startswith("__")}

        def restore_state():
            for name, value in saved.items():
                setattr(state, name, value)

        self.addCleanup(restore_state)
        self.achievements = []
        self.fan_awards = []

        def award_fans_for_rating_win(amount, reason):
            self.fan_awards.append((amount, reason))
            return 250

        stubs = {
            "texas_holdem_game": TexasHoldemGame(),
            "table_stakes": SimpleNamespace(
                TEXAS_HOLDEM_MIN_BUY_IN=100,
                get_poker_starting_stack=lambda: 1000,
                get_poker_ante=lambda stack, high_stakes=False: 10,
            ),
            "legacy": SimpleNamespace(
                game_namespace=dict,
                lose_fans_for_bad_result=_no_op,
                finish_free_play_sandbox=_no_op,
            ),
            "sounds": SimpleNamespace(audio=SimpleNamespace(play_sound=_no_op)),
            "leveling": SimpleNamespace(
                award_game_xp=_no_op,
                process_achievement_event=lambda name, **data: self.achievements.append((name, data)),
            ),
            "career_rewards": SimpleNamespace(
                rate_poker_cash_out=_no_op,
                award_fans_for_cash_win=_no_op,
                award_fans_for_rating_win=award_fans_for_rating_win,
            ),
            "career_saving": SimpleNamespace(auto_save_career=_no_op),
            "track_night_cash": _no_op,
            "record_poker_showdown": _no_op,
            "generate_showdown_chat": lambda game: [],
        }
        for name, value in stubs.items():
            patcher = mock.patch.object(holdem_screen, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        ticks_patcher = mock.patch.object(pygame.time, "get_ticks", lambda: 1000)
        ticks_patcher.start()
        self.addCleanup(ticks_patcher.stop)

        state.current_game_mode = "career"
        state.career_cash = 5000
        state.texas_holdem_table_sweep_rewarded = False

    def clear_the_table(self):
        """Finish the current hand at showdown with the player having busted everyone."""
        game = holdem_screen.texas_holdem_game
        game.hand_complete = True
        game.current_stage = "showdown"
        game.winner_indexes = [1]  # Not the player: only the table clear is rewarded here.
        game.player_busted = False
        game.npc_busted = [True for _ in game.npcs]
        game.npc_stacks = [0 for _ in game.npcs]
        game.result_text = ""
        holdem_screen.process_texas_holdem_showdown()
        return game

    def table_clear_events(self):
        return [data for name, data in self.achievements if name == "poker_table_clear"]

    def test_second_session_table_clear_is_rewarded_again(self):
        self.assertTrue(holdem_screen.start_texas_holdem_session(1000, OPPONENTS))
        game = self.clear_the_table()
        self.assertIn("TABLE CLEARED!", game.result_text)
        self.assertIn("+250 Fans.", game.result_text)
        self.assertEqual(len(self.fan_awards), 1)
        self.assertEqual(len(self.table_clear_events()), 1)

        holdem_screen.finish_texas_holdem_session()

        self.assertTrue(holdem_screen.start_texas_holdem_session(1000, OPPONENTS))
        game = self.clear_the_table()
        self.assertIn("+250 Fans.", game.result_text)
        self.assertEqual(
            self.fan_awards,
            [(holdem_screen.TEXAS_HOLDEM_TABLE_SWEEP_RATING_BONUS, "Hold'em table clear")] * 2,
        )
        self.assertEqual(self.table_clear_events(), [{"game": "texas_holdem"}] * 2)

    def test_table_clear_is_rewarded_once_within_a_session(self):
        self.assertTrue(holdem_screen.start_texas_holdem_session(1000, OPPONENTS))
        self.clear_the_table()
        # The same session's showdown seen again on a later hand pays nothing more.
        holdem_screen.texas_holdem_game.hand_number += 1
        game = self.clear_the_table()
        self.assertIn("+0 Fans.", game.result_text)
        self.assertEqual(len(self.fan_awards), 1)
        self.assertEqual(len(self.table_clear_events()), 1)

    def test_starting_a_session_resets_the_flag(self):
        state.texas_holdem_table_sweep_rewarded = True
        self.assertTrue(holdem_screen.start_texas_holdem_session(1000, OPPONENTS))
        self.assertFalse(state.texas_holdem_table_sweep_rewarded)


if __name__ == "__main__":
    unittest.main()
