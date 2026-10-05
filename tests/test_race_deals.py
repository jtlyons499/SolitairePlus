import json
import os
from pathlib import Path
import random
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame
from card import Card
from game import Game
from solitaire_race_deals import (RANKS, SUITS, _recent, build_race_deal,
                                 initial_state, opening_is_varied, verify_deal)

ROOT = Path(__file__).resolve().parents[1]
DEALS = json.loads((ROOT / "data" / "solitaire_race_deals.json").read_text())["deals"]


class SilentAudio:
    def play_sound(self, *args, **kwargs):
        pass


def card_from_id(identity):
    return Card(SUITS[identity // 13], RANKS[identity % 13])


def identity(card):
    return SUITS.index(card.suit) * 13 + card.value - 1


class RaceDealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.Surface((1366, 768))

    def test_pool_is_diverse_and_every_colour_permutation_is_solvable(self):
        self.assertGreaterEqual(len(DEALS), 160)
        self.assertEqual(len({tuple(entry["deck"]) for entry in DEALS}), len(DEALS))
        for entry in DEALS:
            self.assertTrue(opening_is_varied(entry["deck"]))
            self.assertGreaterEqual(len(entry["solution"]), 68)
            for black_swap in (False, True):
                for red_swap in (False, True):
                    for colour_swap in (False, True):
                        black = [3, 0] if black_swap else [0, 3]
                        red = [2, 1] if red_swap else [1, 2]
                        if colour_swap:
                            black, red = red, black
                        suits = {0: black[0], 3: black[1], 1: red[0], 2: red[1]}
                        remap = lambda card: suits[card // 13] * 13 + card % 13
                        deck = [remap(card) for card in entry["deck"]]
                        solution = [[kind, remap(source) if kind.startswith("r") else source, destination, count]
                                    for kind, source, destination, count in entry["solution"]]
                        self.assertTrue(verify_deal(deck, solution))

    def test_actual_klondike_engine_finishes_every_pool_deal(self):
        # Only asset loading and visual animation timing are replaced. Moves,
        # stock recycling, card exposure, foundation rules and win detection
        # all run through the production Game implementation.
        with patch.object(Game, "load_card_images", return_value=None):
            game = Game(self.screen, SilentAudio())
        for number, entry in enumerate(DEALS):
            game.new_game(play_shuffle=False)
            columns, reserve, _ = initial_state(entry["deck"])
            game.tableau = [[card_from_id(card) for card in cards] for _, cards in columns]
            for column in game.tableau:
                column[-1].face_up = True
            game.stock = [card_from_id(card) for card in reversed(reserve)]
            for kind, source, destination, count in entry["solution"]:
                game.flip_animation = None
                if kind.startswith("r"):
                    clicks = 0
                    while not game.waste or identity(game.waste[-1]) != source:
                        game.flip_animation = None
                        game.click_stock()
                        clicks += 1
                        self.assertLess(clicks, 110, f"Unreachable reserve card in deal {number}")
                    self.assertTrue(game.waste[-1].face_up)
                    if kind.endswith("f"):
                        moved = game.move_waste_to_foundation(source // 13)
                    else:
                        moved = game.move_waste_to_tableau(destination)
                else:
                    selected = game.tableau[source][-count]
                    self.assertTrue(selected.face_up, f"Hidden selection in deal {number}")
                    if kind.endswith("f"):
                        moved = game.move_tableau_to_foundation(source, selected, SUITS.index(selected.suit))
                    else:
                        moved = game.move_tableau_stack(source, selected, destination)
                self.assertTrue(moved, f"Illegal production move {kind} in deal {number}")
            self.assertTrue(game.round_won, f"Deal {number} did not finish")
            self.assertEqual(sum(map(len, game.foundations)), 52)

    def test_game_race_entry_resets_a_previous_board_and_reports_proven_status(self):
        with patch.object(Game, "load_card_images", return_value=None):
            game = Game(self.screen, SilentAudio())
        game.new_game(play_shuffle=False)
        game.click_stock()
        game.new_race_game()
        self.assertEqual(game.waste, [])
        self.assertEqual(game.foundations, [[], [], [], []])
        self.assertEqual(game.move_count, 0)
        self.assertFalse(game.round_won)
        self.assertEqual(game.stock_draw_count, 1)
        self.assertEqual(game.deal_status, "race_verified")
        self.assertGreaterEqual(game.race_deal_metadata["solution_steps"], 68)
        self.assertEqual([len(column) for column in game.tableau], list(range(1, 8)))

    def test_runtime_selection_has_no_recent_repeat_and_standard_masks(self):
        _recent.clear()
        chosen = []
        rng = random.Random(7)
        for _ in range(400):
            tableau, stock, metadata = build_race_deal(rng)
            pool_id = metadata["pool_id"]
            self.assertNotIn(pool_id, chosen[-128:])
            chosen.append(pool_id)
            self.assertEqual([len(column) for column in tableau], list(range(1, 8)))
            self.assertEqual(len(stock), 24)
            for column in tableau:
                self.assertEqual([card.face_up for card in column], [False] * (len(column) - 1) + [True])
            self.assertFalse(any(card.face_up for card in stock))
            self.assertEqual(sorted([identity(card) for column in tableau for card in column] + [identity(card) for card in stock]), list(range(52)))


if __name__ == "__main__":
    unittest.main()
