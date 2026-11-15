"""B48: the Score Four hint search must stop on an unsolvable puzzle.

A dead end used to recurse into get_hint_step from the original four cards
again and again when those cards could not make 24 (RecursionError after
about 12 seconds). The reset is now tried once; an unsolvable original gets
the "no hint" text the UI shows instead.
"""

import time
import unittest
from fractions import Fraction

from solitaireplus.games.cards import score_four
from solitaireplus.games.cards.score_four import ScoreFourGame


TIME_BOX_SECONDS = 2.0


def fractions(values):
    return [None if value is None else Fraction(value) for value in values]


class ScoreFourHintLimitTests(unittest.TestCase):

    def game(self, original, values=None):
        game = ScoreFourGame()
        game.mode = "solo"
        game.original_numbers = list(original)
        game.values = fractions(original if values is None else values)
        return game

    def timed_hint(self, game):
        started = time.monotonic()
        try:
            hint = game.get_hint_step()
        except RecursionError:
            self.fail("hint search recursed without a limit")
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, TIME_BOX_SECONDS)
        return hint

    def test_unsolvable_original_returns_no_hint_quickly(self):
        game = self.game([1, 1, 1, 1])
        self.assertEqual(self.timed_hint(game), score_four.NO_HINT)
        self.assertEqual(game.values, fractions([1, 1, 1, 1]))

    def test_dead_end_on_unsolvable_original_returns_no_hint(self):
        game = self.game([1, 1, 1, 1], [None, 1, 3, None])
        self.assertEqual(self.timed_hint(game), score_four.NO_HINT)
        self.assertEqual(game.values, fractions([None, 1, 3, None]))

    def test_no_cards_returns_no_hint(self):
        game = self.game([], [])
        self.assertEqual(self.timed_hint(game), score_four.NO_HINT)

    def test_requested_hint_shows_no_hint_text(self):
        game = self.game([1, 1, 1, 1])
        # The 30 s wait is over (also on a machine that started less than 30 s ago).
        game.puzzle_start_time = time.monotonic() - 31
        game.last_hint_at = float("-inf")
        self.assertTrue(game.request_solo_hint())
        self.assertEqual(game.hint_text, score_four.NO_HINT)
        self.assertTrue(game.hint_text.startswith("No hint"))

    def test_solvable_puzzles_keep_their_hints(self):
        # Hints the search gave before the B48 fix.
        cases = [
            ([6, 8, 3, 4], None, "Try dividing 6 by 3."),
            ([1, 5, 5, 5], None, "Try dividing 1 by 5."),
            ([3, 3, 8, 8], None, "Try dividing 8 by 3."),
            ([3, 3, 8, 8], [Fraction(8, 3), 3, None, 8],
             "Try subtracting 8/3 from 3."),
            ([6, 8, 3, 4], [6, 8, 1, None],
             "Reset to the original four cards. Try dividing 6 by 3."),
            ([6, 8, 3, 4], [None, None, 25, None],
             "Reset to the original four cards. Try dividing 6 by 3."),
            ([6, 8, 3, 4], [None, None, 24, None], "Solved: 24!"),
        ]
        for original, values, expected in cases:
            with self.subTest(original=original, values=values):
                game = self.game(original, values)
                before = list(game.values)
                self.assertEqual(self.timed_hint(game), expected)
                self.assertEqual(game.values, before)


if __name__ == "__main__":
    unittest.main()
