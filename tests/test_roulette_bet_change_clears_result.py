"""B26: changing the stake after a finished roulette round must clear the old result.

Before the fix, stacking chips onto an existing bet (and removing or clearing
chips) after a spin kept ``result``/``display_result``/``round_complete``, so
the table showed the previous number and a WIN/LOSE figure computed against
the new stake.
"""
import time
import unittest

from solitaireplus.games.casino.roulette import RouletteGame


def finished_round(bet_type="color", bet_value="red", amount=100):
    """A game whose spin has landed and whose payout has been settled."""
    game = RouletteGame()
    assert game.place_bet(bet_type, bet_value, amount)
    assert game.start_spin()
    game.spin_start_time = time.monotonic() - game.spin_duration - 1.0
    game.update()
    assert game.round_complete and not game.spinning
    assert game.result is not None and game.display_result == game.result
    game.payout_claimed = True  # settle_roulette_round has run
    return game


class RouletteBetChangeClearsResultTests(unittest.TestCase):

    def assert_result_cleared(self, game):
        self.assertIsNone(game.result)
        self.assertIsNone(game.display_result)
        self.assertFalse(game.round_complete)
        self.assertEqual(game.get_net_result(), 0)
        self.assertEqual(game.get_payout(), 0)

    def test_stacking_a_chip_after_a_round_clears_the_shown_result(self):
        game = finished_round("color", "red", 100)
        self.assertTrue(game.place_bet("color", "red", 50))
        self.assertEqual(game.get_bet_amount("color", "red"), 150)
        self.assert_result_cleared(game)

    def test_new_bet_type_after_a_round_clears_the_shown_result(self):
        game = finished_round("color", "red", 100)
        self.assertTrue(game.place_bet("number", "7", 10))
        self.assert_result_cleared(game)

    def test_removing_a_chip_after_a_round_clears_the_shown_result(self):
        game = finished_round("color", "red", 100)
        self.assertTrue(game.remove_bet("color", "red", 50))
        self.assertEqual(game.get_bet_amount("color", "red"), 50)
        self.assert_result_cleared(game)

    def test_clearing_bets_after_a_round_clears_the_shown_result(self):
        game = finished_round("color", "red", 100)
        self.assertTrue(game.clear_bets())
        self.assertEqual(game.bets, [])
        self.assert_result_cleared(game)

    def test_refused_bet_changes_keep_the_result(self):
        game = finished_round("color", "red", 100)
        result = game.result
        self.assertFalse(game.remove_bet("number", "7", 10))  # no such bet
        self.assertFalse(game.place_bet("color", "red", 0))
        self.assertFalse(game.remove_bet("color", "red", 0))
        self.assertEqual(game.result, result)
        self.assertEqual(game.display_result, result)
        self.assertTrue(game.round_complete)

    def test_bets_cannot_change_mid_spin(self):
        game = RouletteGame()
        game.place_bet("color", "red", 100)
        game.start_spin()
        result = game.result
        self.assertFalse(game.place_bet("color", "red", 50))
        self.assertFalse(game.remove_bet("color", "red", 50))
        self.assertFalse(game.clear_bets())
        self.assertEqual(game.result, result)
        self.assertTrue(game.spinning)
        self.assertEqual(game.get_total_bet(), 100)

    def test_next_spin_after_restake_still_settles(self):
        game = finished_round("color", "red", 100)
        game.place_bet("color", "red", 50)
        self.assertTrue(game.start_spin())
        game.spin_start_time = time.monotonic() - game.spin_duration - 1.0
        game.update()
        self.assertTrue(game.round_complete)
        self.assertEqual(game.display_result, game.result)
        self.assertEqual(game.get_total_bet(), 150)


if __name__ == "__main__":
    unittest.main()
