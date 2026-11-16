"""B27: blackjack must never show the same card twice on the table.

The BlackjackGame object lives for the whole run, and draw_card used to
rebuild a full 52-card deck whenever the deck ran out, even in the middle of
a hand, so a card already on the table could be dealt again.
"""
import random
import unittest
from collections import Counter
from unittest import mock

from solitaireplus.games.casino import blackjack
from solitaireplus.games.casino.blackjack import BlackjackGame


class _FakeClock:
    """Stands in for the time module so dealer play runs without waiting."""

    def __init__(self):
        self.now = 1000.0

    def monotonic(self):
        return self.now


def _table_cards(game):
    cards = list(game.dealer_hand)
    for hand in game.get_player_hands():
        cards.extend(hand)
    return cards


def _duplicates(game):
    return sorted(card for card, count in Counter(_table_cards(game)).items() if count > 1)


class BlackjackDeckTests(unittest.TestCase):

    def setUp(self):
        self.clock = _FakeClock()
        patcher = mock.patch.object(blackjack, "time", self.clock)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _assert_no_duplicates(self, game, round_number, when):
        duplicates = _duplicates(game)
        self.assertEqual(
            duplicates,
            [],
            f"round {round_number} ({when}) shows the same card twice: {duplicates}; "
            f"dealer={game.dealer_hand} player={game.get_player_hands()}",
        )

    def _play_round(self, game, rng, round_number):
        game.start_round(10)
        self._assert_no_duplicates(game, round_number, "after the deal")

        for _ in range(200):
            if game.round_complete:
                break
            if not game.player_stood:
                if game.can_split():
                    game.split_hand()
                elif game.can_double_down() and rng.random() < 0.15:
                    game.double_down()
                elif game.player_value() < 17 and rng.random() < 0.85:
                    game.hit()
                else:
                    game.stand()
            else:
                self.clock.now += 5.0
                game.update()
            self._assert_no_duplicates(game, round_number, "mid-hand")

        self.assertTrue(game.round_complete, f"round {round_number} never finished")
        self._assert_no_duplicates(game, round_number, "at settlement")

    def test_two_hundred_seeded_rounds_never_show_a_duplicate_card(self):
        for seed in (1, 7, 27, 2026):
            with self.subTest(seed=seed):
                random.seed(seed)
                rng = random.Random(seed)
                game = BlackjackGame()
                for round_number in range(1, 201):
                    self._play_round(game, rng, round_number)

    def test_round_reshuffles_a_fresh_deck_when_the_shoe_is_low(self):
        random.seed(3)
        game = BlackjackGame()
        game.deck = game.deck[:BlackjackGame.RESHUFFLE_THRESHOLD - 1]

        game.start_round(10)

        # A fresh 52-card deck minus the four cards just dealt.
        self.assertEqual(len(game.deck), 52 - 4)
        self._assert_no_duplicates(game, 1, "after the deal")

    def test_round_keeps_the_current_deck_when_enough_cards_remain(self):
        random.seed(4)
        game = BlackjackGame()
        game.deck = game.deck[:BlackjackGame.RESHUFFLE_THRESHOLD]
        expected_deal = list(reversed(game.deck))[:4]

        game.start_round(10)

        self.assertEqual(len(game.deck), BlackjackGame.RESHUFFLE_THRESHOLD - 4)
        dealt = [game.player_hands[0][0], game.player_hands[0][1],
                 game.dealer_hand[0], game.dealer_hand[1]]
        self.assertEqual(dealt, expected_deal)

    def test_empty_deck_mid_hand_only_deals_cards_not_in_play(self):
        random.seed(5)
        game = BlackjackGame()
        game.start_round(10)
        while game.round_complete or game.player_stood:
            game.start_round(10)
        in_play = set(_table_cards(game))

        for _ in range(30):
            game.deck = []
            card = game.draw_card()
            self.assertNotIn(card, in_play)
            # The guard deck holds every card that is not on the table.
            self.assertEqual(len(game.deck), 52 - len(in_play) - 1)
            in_play.add(card)
            game.dealer_hand.append(card)

    def test_empty_deck_between_split_draws_does_not_repeat_the_first_new_card(self):
        random.seed(6)
        game = BlackjackGame()
        game.start_round(10)
        game.player_hands = [[("8", "C"), ("8", "D")]]
        game.player_hand_bets = [10]
        game.player_hand_done = [False]
        game.player_hand_results = [None]
        game.player_stood = False
        game.round_complete = False
        game._sync_player_hand_alias()
        game.dealer_hand = [("5", "H"), ("K", "S")]
        # One card left: the first split hand gets it, the second hand's card
        # comes from the guard deck while the first new card is still being
        # assembled into the new hand list.
        game.deck = [("2", "S")]

        self.assertTrue(game.split_hand())

        self.assertEqual(game.player_hands[0][1], ("2", "S"))
        self._assert_no_duplicates(game, 1, "after the split")
        for card in _table_cards(game):
            self.assertNotIn(card, game.deck, "a card on the table came back into the guard deck")


if __name__ == "__main__":
    unittest.main()
