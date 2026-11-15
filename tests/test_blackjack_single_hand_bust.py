"""B29: a single-hand bust resolves as a dealer win, not as a "split" round."""

import unittest
from unittest import mock

from solitaireplus.games.casino import blackjack
from solitaireplus.games.casino.blackjack import BlackjackGame


def rigged_game(cards):
    """A game whose draws come out in ``cards`` order (draw_card pops the end)."""
    game = BlackjackGame()
    # Keep the rest of the deck underneath: start_round reshuffles a fresh
    # deck when fewer than RESHUFFLE_THRESHOLD cards remain (B27).
    rest = [card for card in game.deck if card not in cards]
    game.deck = rest + list(reversed(cards))
    return game


def run_pending_resolution(game):
    # The bust waits for the hole-card flip; jump the clock past it.
    with mock.patch.object(blackjack.time, "monotonic", return_value=1e12):
        game.update()


class SingleHandBustTests(unittest.TestCase):

    def test_single_hand_bust_is_a_dealer_win(self):
        # Player 10+6=16, dealer 9+7=16 (no naturals), then the hit busts.
        game = rigged_game([
            ("10", "H"), ("6", "S"),
            ("9", "C"), ("7", "D"),
            ("K", "S"),
        ])
        game.start_round(50)
        self.assertTrue(game.hit())
        self.assertGreater(game.player_value(), 21)
        self.assertFalse(game.round_complete)

        run_pending_resolution(game)

        self.assertTrue(game.round_complete)
        self.assertEqual(game.result, "dealer")
        self.assertEqual(game.get_payout(), 0)
        self.assertEqual(game.get_net_result(), -50)
        # Split-round bookkeeping is untouched for an unsplit round.
        self.assertFalse(game.was_split)
        self.assertFalse(game.is_split_round())
        self.assertEqual(len(game.player_hands), 1)
        self.assertEqual(game.player_hand_bets, [50])
        self.assertEqual(game.player_hand_results, ["dealer"])
        self.assertIsNone(game.pending_split_finish_time)
        self.assertFalse(game.dealer_playing)

    def test_double_down_bust_is_a_dealer_win(self):
        # Player 10+6=16 doubles into a king; dealer 9+7=16.
        game = rigged_game([
            ("10", "H"), ("6", "S"),
            ("9", "C"), ("7", "D"),
            ("K", "S"),
        ])
        game.start_round(20)
        self.assertTrue(game.double_down())

        run_pending_resolution(game)

        self.assertEqual(game.result, "dealer")
        self.assertEqual(game.player_hand_results, ["dealer"])
        self.assertEqual(game.get_net_result(), -40)

    def test_split_round_where_every_hand_busts_stays_split(self):
        # Two eights split onto tens (18 each), each hand then hits a king.
        game = rigged_game([
            ("8", "H"), ("8", "S"),
            ("9", "C"), ("7", "D"),
            ("10", "C"), ("10", "D"),
            ("K", "S"), ("K", "H"),
        ])
        game.start_round(10)
        self.assertTrue(game.split_hand())
        self.assertTrue(game.hit())
        self.assertTrue(game.hit())

        run_pending_resolution(game)

        self.assertTrue(game.round_complete)
        self.assertEqual(game.result, "split")
        self.assertTrue(game.is_split_round())
        self.assertEqual(game.player_hand_results, ["dealer", "dealer"])
        self.assertEqual(game.get_net_result(), -20)


if __name__ == "__main__":
    unittest.main()
