"""B76: score_four.check_solution replays a multiplayer solve with ScoreFourGame's rules.

The room host checks a guest's 'solved' claim with it, so it must accept exactly the
three-step solves a player can build with select_number/select_operator (the first tile
is removed and the result goes into the second, Fraction arithmetic, no division by
zero) and refuse everything else without raising.
"""
import random
import unittest
from fractions import Fraction

from solitaireplus.games.cards.score_four import ScoreFourGame, check_solution

SOLVE = [[0, '*', 1], [1, '*', 2], [2, '*', 3]]


def play(numbers, steps, game=None):
    """Play ``steps`` through the real ScoreFourGame calculator; True if it shows 24."""
    game = game or ScoreFourGame()
    game.mode = 'multiplayer'
    game.round_complete = False
    game.original_numbers = list(numbers)
    game.values = [Fraction(n) for n in numbers]
    game.selected_index = game.selected_operator = None
    game.undo_stack = []
    for first, operator, second in steps:
        game.select_number(first)
        game.select_operator(operator)
        game.select_number(second)
    return game.is_solved()


def legal_claims(numbers):
    """Every three-step claim a player could make on ``numbers`` (no division by zero)."""
    def walk(values, steps):
        if len(steps) == 3:
            yield [list(step) for step in steps]
            return
        live = [index for index, value in enumerate(values) if value is not None]
        for first in live:
            for second in live:
                if first == second:
                    continue
                for operator in '+-*/':
                    a, b = values[first], values[second]
                    if operator == '/' and b == 0:
                        continue
                    result = {'+': lambda: a + b, '-': lambda: a - b, '*': lambda: a * b, '/': lambda: a / b}[operator]()
                    following = list(values)
                    following[first] = None
                    following[second] = result
                    yield from walk(following, steps + [(first, operator, second)])
    yield from walk([Fraction(n) for n in numbers], [])


class CheckSolutionTests(unittest.TestCase):
    def test_plan_example_is_accepted(self):
        self.assertTrue(check_solution([8, 3, 1, 1], SOLVE))
        self.assertTrue(check_solution([8, 3, 1, 1], tuple(tuple(step) for step in SOLVE)))
        self.assertTrue(play([8, 3, 1, 1], SOLVE))

    def test_fractions_and_order_follow_the_calculator(self):
        # 8 / (3 - 8 / 3) = 24 needs exact fractions; the result always lands in the
        # second tile, so "first - second" is first minus second.
        numbers = [8, 3, 3, 8]
        steps = [[3, '/', 2], [1, '-', 2], [0, '/', 2]]
        self.assertTrue(play(numbers, steps))
        self.assertTrue(check_solution(numbers, steps))
        # The same steps with the subtraction the other way round give -24.
        self.assertFalse(check_solution(numbers, [[3, '/', 2], [2, '-', 1], [0, '/', 1]]))

    def test_rejects_bad_claims(self):
        numbers = [8, 3, 1, 1]
        bad = {
            'zero': 0,
            'none': None,
            'garbage string': 'garbage',
            'dict': {'steps': SOLVE},
            'garbage step': [[0, '*', 1], 'x', [2, '*', 3]],
            'short step': [[0, '*'], [1, '*', 2], [2, '*', 3]],
            'long step': [[0, '*', 1, 9], [1, '*', 2], [2, '*', 3]],
            'reused tile': [[0, '*', 1], [0, '*', 2], [2, '*', 3]],
            'same tile twice': [[0, '*', 0], [1, '*', 2], [2, '*', 3]],
            'index out of range': [[0, '*', 4], [1, '*', 2], [2, '*', 3]],
            'negative index': [[-1, '*', 1], [1, '*', 2], [2, '*', 3]],
            'string index': [['0', '*', 1], [1, '*', 2], [2, '*', 3]],
            'float index': [[0.0, '*', 1], [1, '*', 2], [2, '*', 3]],
            'bool index': [[False, '*', True], [1, '*', 2], [2, '*', 3]],
            'bad operator': [[0, 'x', 1], [1, '*', 2], [2, '*', 3]],
            'operator not a string': [[0, 3, 1], [1, '*', 2], [2, '*', 3]],
            'two steps': SOLVE[:2],
            'four steps': SOLVE + [[3, '+', 0]],
            'no steps': [],
            'wrong total': [[0, '+', 1], [1, '+', 2], [2, '+', 3]],
        }
        for name, steps in bad.items():
            with self.subTest(name):
                self.assertIs(check_solution(numbers, steps), False)

    def test_division_by_zero_is_refused(self):
        # 0 as the divisor: [4, 0, 6, 1]; "6 / (4 - 4)" style claims must not raise.
        self.assertIs(check_solution([4, 4, 6, 1], [[0, '-', 1], [2, '/', 1], [1, '*', 3]]), False)
        self.assertIs(check_solution([0, 6, 4, 1], [[1, '/', 0], [0, '*', 2], [2, '*', 3]]), False)

    def test_bad_numbers_are_refused(self):
        for numbers in ([8, 3, 1], [8, 3, 1, 1, 1], None, 'abcd', [8, 3, 'x', 1]):
            with self.subTest(numbers=numbers):
                self.assertIs(check_solution(numbers, SOLVE), False)

    def test_does_not_change_its_inputs(self):
        numbers = [8, 3, 1, 1]
        steps = [list(step) for step in SOLVE]
        check_solution(numbers, steps)
        self.assertEqual(numbers, [8, 3, 1, 1])
        self.assertEqual(steps, SOLVE)

    def test_agrees_with_the_calculator_on_every_legal_claim(self):
        game = ScoreFourGame()
        accepted = checked = 0
        for numbers in ([8, 3, 1, 1], [8, 3, 3, 8], [1, 2, 3, 4], [1, 5, 5, 5], [6, 6, 6, 6]):
            for steps in legal_claims(numbers):
                expected = play(numbers, steps, game)
                accepted += expected
                checked += 1
                self.assertIs(check_solution(numbers, steps), expected, (numbers, steps))
        self.assertGreater(checked, 40000)                  # 46,080 minus the divisions by zero
        self.assertGreater(accepted, 50)

    def test_random_garbage_never_raises(self):
        rng = random.Random(24)
        pool = [0, 1, 2, 3, 4, -1, True, None, '1', 1.0, '+', '-', '*', '/', 'x', [], [0, '+', 1]]
        for _ in range(3000):
            steps = [[rng.choice(pool) for _ in range(rng.choice((2, 3, 3, 3, 4)))]
                     for _ in range(rng.choice((2, 3, 3, 4)))]
            self.assertIn(check_solution([8, 3, 1, 1], steps), (True, False))


if __name__ == '__main__':
    unittest.main()
