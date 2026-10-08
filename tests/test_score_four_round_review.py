import unittest
from unittest.mock import patch
from score_four import ScoreFourGame

class RoundReviewTests(unittest.TestCase):
    def lost_round(self):
        game=ScoreFourGame();game.mode='competitive'
        with patch('score_four.time.monotonic',return_value=100):game.finish_competitive_round('npc')
        return game
    def test_loss_holds_puzzle_for_eight_seconds(self):
        game=self.lost_round();numbers=list(game.original_numbers);solution=game.solution
        with patch('score_four.time.monotonic',return_value=107.5):
            game.update();self.assertTrue(game.round_complete)
            self.assertEqual(game.original_numbers,numbers);self.assertEqual(game.solution,solution)
            self.assertAlmostEqual(game.round_countdown_remaining(),.5)
        with patch('score_four.time.monotonic',return_value=108):game.update()
        self.assertFalse(game.round_complete);self.assertEqual(game.round_number,2)
        self.assertEqual(game.npc_score,1)
    def test_continue_advances_once_and_restarts_npc_clock(self):
        game=self.lost_round()
        with patch('score_four.time.monotonic',return_value=101):
            self.assertTrue(game.continue_competitive_round())
            self.assertFalse(game.continue_competitive_round())
        self.assertEqual(game.round_number,2);self.assertEqual(game.round_start_time,101)
    def test_final_match_keeps_solution_and_does_not_auto_advance(self):
        game=self.lost_round();game.npc_score=2;game.round_complete=False
        with patch('score_four.time.monotonic',return_value=102):game.finish_competitive_round('npc')
        solution=game.solution
        with patch('score_four.time.monotonic',return_value=200):game.update()
        self.assertTrue(game.match_complete);self.assertFalse(game.continue_competitive_round())
        self.assertEqual(game.solution,solution)
