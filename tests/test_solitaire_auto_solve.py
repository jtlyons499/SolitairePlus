"""B1: auto-solve stopped early when it had to recycle the waste.

Auto-solve steps every 140 ms, but click_stock() ignores clicks while the 220 ms card flip
animates. When the last stock card it drew could not be played, the next step tried to
recycle the waste while that flip was still running, the click was ignored, and auto-solve
took the unchanged stock for "nothing left to do" and switched itself off. It now waits for
the flip to finish and tries again.

The Game is driven headless with a controlled clock (pygame.time.get_ticks is patched).
"""
import contextlib
import io
import os
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

from solitaireplus.games.solitaire.card import Card
from solitaireplus.games.solitaire.deck import RANKS
from solitaireplus.games.solitaire.rules import BASE_HEIGHT, BASE_WIDTH, Game

FRAME_MS = 16
TIME_LIMIT_MS = 20000


class Clock:
    def __init__(self, now=1000):
        self.now = now

    def __call__(self):
        return self.now


def face_up(suit, rank):
    card = Card(suit, rank)
    card.face_up = True
    return card


def face_down(suit, rank):
    return Card(suit, rank)


class AutoSolveRecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))  # convert_alpha() for the real card images

    def setUp(self):
        self.clock = Clock()
        ticks_patch = patch('solitaireplus.games.solitaire.rules.pygame.time.get_ticks',
                            side_effect=self.clock)
        ticks_patch.start()
        self.addCleanup(ticks_patch.stop)

    def make_game(self, load_images):
        surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
        if load_images:
            game = Game(surface, Mock())
        else:
            with patch.object(Game, 'load_card_images', return_value=None):
                game = Game(surface, Mock())
        game.challenge_id = None
        game.stock_draw_count = 1
        game.stock_pass_limit = None
        self.set_up_recycle_ending(game)
        return game

    def set_up_recycle_ending(self, game):
        """Every card face-up except four spades in the stock, which need a second pass.

        Draw order 9, 10, 8, J: the 8 plays, but the 9 stays buried under the 10 and the
        J, so after drawing the J the stock is empty and the waste must be recycled.
        """
        game.foundations = [[face_up(suit, rank) for rank in RANKS]
                            for suit in ('Hearts', 'Diamonds', 'Clubs')]
        game.foundations.append([face_up('Spades', rank) for rank in RANKS[:7]])  # A..7
        game.tableau = [[face_up('Spades', 'K')], [face_up('Spades', 'Q')], [], [], [], [], []]
        game.stock = [face_down('Spades', rank) for rank in ('J', '8', '10', '9')]  # pops 9 first
        game.waste = []
        game.flip_animation = None
        game.round_won = False
        game.stock_passes_used = 1

    def run_auto_solve(self, game, draw_frames):
        """Run frames like screen.draw(): update_auto_solve(), then (optionally) game.draw()."""
        self.assertTrue(game.can_auto_solve())
        self.assertTrue(game.auto_solve())
        deadline = self.clock.now + TIME_LIMIT_MS
        with contextlib.redirect_stdout(io.StringIO()):  # check_for_win prints the summary
            while game.auto_solving and self.clock.now < deadline:
                self.clock.now += FRAME_MS
                game.update_auto_solve()
                if draw_frames:
                    game.draw()

    def assert_solved(self, game):
        self.assertTrue(game.round_won, (
            f'auto-solve stopped early: stock={game.stock} waste={game.waste} '
            f'spades foundation top={game.foundations[3][-1]}'))
        self.assertEqual(sum(map(len, game.foundations)), 52)
        self.assertEqual(game.stock_passes_used, 2)  # it really recycled the waste
        self.assertFalse(game.auto_solving)

    def test_deal_needing_a_recycle_completes_with_the_table_drawn_every_frame(self):
        # The real frame order: the renderer clears a finished flip when it draws the card.
        game = self.make_game(load_images=True)
        self.run_auto_solve(game, draw_frames=True)
        self.assert_solved(game)

    def test_deal_needing_a_recycle_completes_without_drawing(self):
        # Auto-solve must not depend on the renderer to notice that a flip has finished.
        game = self.make_game(load_images=False)
        self.run_auto_solve(game, draw_frames=False)
        self.assert_solved(game)

    def test_recycle_is_still_refused_when_the_pass_limit_is_used_up(self):
        # Waiting for the flip must not turn a refused recycle into an endless wait.
        game = self.make_game(load_images=False)
        game.stock_pass_limit = 1
        self.run_auto_solve(game, draw_frames=False)
        self.assertFalse(game.auto_solving)
        self.assertFalse(game.round_won)
        self.assertEqual(game.stock, [])
        self.assertEqual([card.rank for card in game.waste], ['9', '10', 'J'])
        self.assertLess(game.auto_solve_steps, 20)

    def test_draw_three_ending_that_cannot_finish_stops_after_a_pass_without_progress(self):
        # Review of B1: with draw 3 and unlimited passes an unplayable ending used to cycle
        # draw / wait / recycle until the 500-step cap (about 72 s with the table locked).
        game = self.make_game(load_images=False)
        game.stock_draw_count = 3
        game.foundations[3] = [face_up('Spades', rank) for rank in RANKS[:7]]   # A..7
        game.tableau = [[], [], [], [], [], [], []]
        # The first draw of 3 (10, 9, 8) plays all three; every later draw shows J, Q, K with
        # the K on top, which can never be played, so auto-solve can't finish.
        game.stock = [face_down('Spades', rank) for rank in ('K', 'Q', 'J', '8', '9', '10')]
        start = self.clock.now
        self.run_auto_solve(game, draw_frames=False)
        self.assertFalse(game.auto_solving)
        self.assertFalse(game.round_won)
        self.assertLess(game.auto_solve_steps, 30)
        self.assertLessEqual(game.stock_passes_used, 3)
        self.assertLess(self.clock.now - start, 5000)


if __name__ == '__main__':
    unittest.main()
