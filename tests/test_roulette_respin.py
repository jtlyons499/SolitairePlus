"""B24: spinning the roulette wheel again with the same bets must pay again.

start_spin() used to leave payout_claimed set from the previous spin, so
settle_roulette_round() returned early on every re-spin with unchanged bets:
the stake was taken but nothing was paid, and no XP or achievements followed.
"""
import unittest
from unittest.mock import patch

from tests.support import locate
from solitaireplus.games.casino import roulette as roulette_module
from solitaireplus.games.casino.roulette import RouletteGame


def finish_spin(game, landing):
    """Spin the real engine and let the wheel stop on ``landing``."""
    game.spin_duration = 0
    with patch.object(roulette_module.random, "choice", return_value=landing):
        started = game.start_spin()
    game.update()
    return started


class RouletteGameRespinTests(unittest.TestCase):
    def test_start_spin_clears_the_previous_rounds_payout_flag(self):
        game = RouletteGame()
        game.place_bet("number", 7, 100)
        self.assertTrue(finish_spin(game, "7"))
        self.assertTrue(game.round_complete)
        game.payout_claimed = True  # what settle_roulette_round() leaves behind

        with patch.object(roulette_module.random, "choice", return_value="8"):
            self.assertTrue(game.start_spin())
        self.assertFalse(game.payout_claimed)
        self.assertFalse(game.round_complete)
        self.assertEqual(game.result, "8")
        self.assertIsNone(game.display_result)


class SettleRouletteRespinTests(unittest.TestCase):
    def make_env(self, game):
        self.xp = []
        self.achievements = []
        self.ratings = []
        env = dict(
            roulette_game=game,
            career_cash=1000,
            roulette_session_net=0,
            current_game_mode="career",
            rate_house_game=lambda key, net: self.ratings.append((key, net)) or 12,
            award_fans_for_cash_win=lambda *args, **kwargs: None,
            lose_fans_for_bad_result=lambda *args, **kwargs: None,
            award_game_xp=lambda *args, **kwargs: self.xp.append((args, kwargs)),
            process_achievement_event=lambda *args, **kwargs: self.achievements.append((args, kwargs)),
            track_night_cash=lambda *args, **kwargs: None,
        )
        return locate.exec_functions(["settle_roulette_round"], env)

    def spin_and_settle(self, env, landing):
        game = env["roulette_game"]
        # The SPIN button takes the stake before the wheel starts (roulette_screen.handle_event).
        env["career_cash"] -= game.get_total_bet()
        self.assertTrue(finish_spin(game, landing))
        env["settle_roulette_round"]()

    def test_two_spins_with_the_same_bets_both_pay(self):
        game = RouletteGame()
        game.place_bet("number", 7, 100)
        env = self.make_env(game)

        self.spin_and_settle(env, "7")
        self.assertEqual(env["career_cash"], 1000 - 100 + 3600)
        self.assertEqual(env["roulette_session_net"], 3500)

        # Same bets left on the table, spin again.
        self.spin_and_settle(env, "7")
        self.assertEqual(env["career_cash"], 1000 - 100 + 3600 - 100 + 3600)
        self.assertEqual(env["roulette_session_net"], 7000)
        self.assertEqual(len(self.xp), 2)
        self.assertEqual(len(self.achievements), 2)
        self.assertEqual(self.ratings, [("roulette", 3500), ("roulette", 3500)])
        self.assertTrue(game.payout_claimed)

        # Each spin still settles exactly once.
        env["settle_roulette_round"]()
        self.assertEqual(env["career_cash"], 1000 - 100 + 3600 - 100 + 3600)
        self.assertEqual(len(self.xp), 2)

    def test_losing_respin_still_counts_for_xp_and_achievements(self):
        game = RouletteGame()
        game.place_bet("color", "red", 100)
        env = self.make_env(game)

        self.spin_and_settle(env, "1")   # red wins
        self.spin_and_settle(env, "2")   # black: the red bet loses
        self.assertEqual(env["career_cash"], 1000 - 100 + 200 - 100)
        self.assertEqual(env["roulette_session_net"], 0)
        self.assertEqual(len(self.xp), 2)
        self.assertEqual(self.xp[1][1]["won"], False)
        self.assertEqual(len(self.achievements), 2)
        self.assertEqual(self.achievements[1][1]["net"], -100)


if __name__ == "__main__":
    unittest.main()
