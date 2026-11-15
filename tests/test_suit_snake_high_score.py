"""B57: Suit Snake must not announce a new high score when there was no previous score.

SuitSnakeGame._collect_target used to set new_high_score as soon as the score passed the
starting high score, so the very first card of the very first game (score 100 against a
saved high score of 0) already counted as a "NEW HIGH SCORE!" on the game-over footer.
Like Ace Invaders, a new high score now needs a previous score above 0 to beat.

Runs the engine headless; no window is opened.
"""
import os
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

from solitaireplus.games.arcade.suit_snake_game import SuitSnakeGame


def new_game(previous_high_score):
    game = SuitSnakeGame()
    game.start_session(rng_seed=57, high_score=previous_high_score)
    return game


class SuitSnakeNewHighScoreTests(unittest.TestCase):
    def test_first_ever_game_never_announces_a_new_high_score(self):
        game = new_game(0)
        game._collect_target()
        self.assertEqual(game.score, 100)
        self.assertFalse(game.new_high_score)
        for _ in range(20):
            game._collect_target()
        self.assertGreater(game.score, 0)
        self.assertEqual(game.high_score, game.score)
        self.assertFalse(game.new_high_score)

    def test_missing_or_bad_saved_score_counts_as_no_previous_score(self):
        for saved in (None, '', 'not a number', -50):
            with self.subTest(saved=saved):
                game = new_game(saved)
                game._collect_target()
                self.assertFalse(game.new_high_score)

    def test_beating_a_previous_score_announces_it(self):
        game = new_game(150)
        game._collect_target()
        self.assertEqual(game.score, 100)
        self.assertFalse(game.new_high_score)
        self.assertEqual(game.high_score, 150)
        game._collect_target()
        self.assertEqual(game.score, 200)
        self.assertTrue(game.new_high_score)
        self.assertEqual(game.high_score, 200)
        game._collect_target()
        self.assertTrue(game.new_high_score)
        self.assertEqual(game.high_score, 300)

    def test_matching_a_previous_score_is_not_a_new_high_score(self):
        game = new_game(200)
        game._collect_target()
        game._collect_target()
        self.assertEqual(game.score, 200)
        self.assertFalse(game.new_high_score)
        self.assertEqual(game.high_score, 200)

    def test_a_new_session_clears_the_announcement(self):
        game = new_game(150)
        game._collect_target()
        game._collect_target()
        self.assertTrue(game.new_high_score)
        game.start_session(rng_seed=57, high_score=game.high_score)
        self.assertFalse(game.new_high_score)


if __name__ == '__main__':
    unittest.main()
