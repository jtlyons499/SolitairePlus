"""B2: Restart after a race deal must restore the race deal, not the discarded random deal."""
import os
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from solitaireplus.games.solitaire.restart import restart_hand
from solitaireplus.games.solitaire.rules import Game


def signature(tableau, stock):
    return (
        [[(card.rank, card.suit, card.face_up) for card in pile] for pile in tableau],
        [(card.rank, card.suit, card.face_up) for card in stock],
    )


class RaceRestartSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.Surface((1366, 768))

    def make_game(self):
        with patch.object(Game, "load_card_images", return_value=None):
            game = Game(self.screen, Mock())
        game.stock_draw_count = 1
        game.set_deal_mode("random")
        return game

    def test_restart_snapshot_is_the_race_deal(self):
        game = self.make_game()
        game.new_race_game()
        race = signature(game.tableau, game.stock)
        snapshot = game._restart_deal
        self.assertEqual(signature(snapshot["tableau"], snapshot["stock"]), race)
        self.assertEqual(snapshot["deal_status"], "race_verified")
        self.assertEqual(snapshot["waste"], [])
        self.assertEqual(snapshot["foundations"], [[], [], [], []])

    def test_restart_reproduces_the_race_deal(self):
        game = self.make_game()
        game.new_race_game()
        race = signature(game.tableau, game.stock)
        game.click_stock()
        game.tableau[0][-1].face_up = False
        self.assertTrue(restart_hand(game))
        self.assertEqual(signature(game.tableau, game.stock), race)
        self.assertEqual(game.waste, [])
        self.assertEqual(game.deal_status, "race_verified")

    def test_snapshot_is_independent_of_the_live_race_cards(self):
        game = self.make_game()
        game.new_race_game()
        race = signature(game.tableau, game.stock)
        game.tableau[6][-1].face_up = False
        game.stock.pop()
        snapshot = game._restart_deal
        self.assertEqual(signature(snapshot["tableau"], snapshot["stock"]), race)


if __name__ == "__main__":
    unittest.main()
