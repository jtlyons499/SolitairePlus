"""B35: a Hold'em session-end timer left over from a busted session must not end the next session."""
import unittest
from types import SimpleNamespace
from unittest import mock

import pygame

from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.games.poker import holdem_screen
from solitaireplus.games.poker.holdem import TexasHoldemGame


def _no_op(*args, **kwargs):
    return None


OPPONENTS = [{"id": f"npc{i}", "name": f"Rival {i}"} for i in range(4)]


class HoldemSessionEndTimerTests(unittest.TestCase):
    def setUp(self):
        saved = {name: value for name, value in vars(state).items() if not name.startswith("__")}

        def restore_state():
            for name, value in saved.items():
                setattr(state, name, value)

        self.addCleanup(restore_state)
        self.ticks = 0
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
            "leveling": SimpleNamespace(award_game_xp=_no_op, process_achievement_event=_no_op),
            "career_rewards": SimpleNamespace(
                rate_poker_cash_out=_no_op,
                award_fans_for_cash_win=_no_op,
                award_fans_for_rating_win=lambda *args: 0,
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
        ticks_patcher = mock.patch.object(pygame.time, "get_ticks", lambda: self.ticks)
        ticks_patcher.start()
        self.addCleanup(ticks_patcher.stop)

        state.current_game_mode = "career"
        state.career_cash = 5000
        state.texas_holdem_session_end_at = 0
        state.texas_holdem_hand_win_sound_at = 0

    def bust_player(self):
        game = holdem_screen.texas_holdem_game
        game.hand_complete = True
        game.current_stage = "showdown"
        game.winner_indexes = [1]
        game.player_stack = 0
        game.player_busted = True
        holdem_screen.process_texas_holdem_showdown()

    def test_bust_return_and_start_again_does_not_end_on_first_frame(self):
        self.assertTrue(holdem_screen.start_texas_holdem_session(1000, OPPONENTS))
        self.assertEqual(state.current_state, state_names.STATE_TEXAS_HOLDEM)

        # Bust: the showdown schedules the end-of-session countdown.
        self.bust_player()
        self.assertGreater(state.texas_holdem_session_end_at, 0)

        # Return before the countdown fires.
        self.ticks = 1000
        holdem_screen.finish_texas_holdem_session()
        self.assertEqual(state.current_state, state_names.STATE_CAREER_EVENT_SELECT)

        # Start again later, after the old countdown would have expired.
        self.ticks = 20000
        self.assertTrue(holdem_screen.start_texas_holdem_session(1000, OPPONENTS))
        self.assertEqual(state.texas_holdem_session_end_at, 0)

        # First frame of the new session.
        self.ticks = 20016
        holdem_screen.loop_late_texas_holdem()
        self.assertEqual(state.current_state, state_names.STATE_TEXAS_HOLDEM)
        self.assertTrue(state.texas_holdem_buy_in_active)


if __name__ == "__main__":
    unittest.main()
