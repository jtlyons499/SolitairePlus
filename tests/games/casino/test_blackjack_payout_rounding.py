"""B28: a blackjack natural pays 3:2 with half-up rounding on whole-dollar bets."""

import unittest

from solitaireplus.games.casino.blackjack import BlackjackGame


def finished_natural(bet):
    game = BlackjackGame()
    game.bet = bet
    game.player_hands = [[("A", "Spades"), ("K", "Hearts")]]
    game.player_hand_bets = [bet]
    game.player_hand_results = ["blackjack"]
    game.was_split = False
    game.result = "blackjack"
    game.round_complete = True
    return game


class BlackjackNaturalPayoutRoundingTests(unittest.TestCase):

    def test_odd_bets_round_the_half_dollar_up(self):
        # 3:2 on 1, 3 and 5 is 1.5, 4.5 and 7.5: half-up gives 2, 5 and 8.
        for bet, winnings in ((1, 2), (3, 5), (5, 8)):
            with self.subTest(bet=bet):
                game = finished_natural(bet)
                self.assertEqual(game.get_payout(), bet + winnings)
                self.assertEqual(game.get_net_result(), winnings)

    def test_even_bets_pay_exact_three_to_two(self):
        for bet in (2, 10, 100, 250):
            with self.subTest(bet=bet):
                game = finished_natural(bet)
                self.assertEqual(game.get_payout(), bet + bet * 3 // 2)

    def test_payout_stays_a_whole_dollar_int(self):
        for bet in range(1, 60):
            with self.subTest(bet=bet):
                payout = finished_natural(bet).get_payout()
                self.assertIs(type(payout), int)
                self.assertEqual(payout, bet + (bet * 3 + 1) // 2)


if __name__ == "__main__":
    unittest.main()
