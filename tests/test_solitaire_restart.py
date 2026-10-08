import copy
import os
import unittest
from unittest.mock import Mock,patch
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
from game import Game
from solitaire_restart import restart_hand, RestartPrompt

class RestartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init();cls.screen=pygame.display.set_mode((1,1))
    def game(self):
        with patch.object(Game,'load_card_images',return_value=None):return Game(self.screen,Mock())
    def signature(self,g):
        return [[(c.rank,c.suit,c.face_up) for c in pile] for pile in g.tableau],[(c.rank,c.suit,c.face_up) for c in g.stock]
    def test_exact_deal_restored_repeatedly_without_awards(self):
        g=self.game();initial=self.signature(g);initial_hints=g.hints_remaining
        for _ in range(2):
            g.waste.append(g.stock.pop());g.tableau[0][0].face_up=False
            g.move_count=80;g.undo_stack=[{}];g.hint_data={'example':1};g.selected_card=object()
            with patch('solitaire_restart.pygame.time.get_ticks',return_value=2000):self.assertTrue(restart_hand(g))
            self.assertEqual(self.signature(g),initial);self.assertEqual(g.waste,[])
            self.assertEqual(g.move_count,0);self.assertEqual(g.round_start_ticks,2000)
            self.assertEqual(g.hints_remaining,initial_hints);self.assertIsNone(g.round_summary)
            self.assertEqual(g.undo_stack,[]);self.assertIsNone(g.selected_card)
    def test_restricted_challenges_finished_hand_and_race_button(self):
        g=self.game()
        for challenge in ('no_undo','all_or_nothing'):
            g.challenge_id=challenge;self.assertFalse(restart_hand(g))
        g.challenge_id=None;g.round_won=True;self.assertFalse(restart_hand(g))
        g.round_won=False;self.assertFalse(RestartPrompt().allowed(g,'head_to_head'))
    def test_new_deal_refreshes_restart_snapshot(self):
        g=self.game();g.new_game(play_shuffle=False);new=self.signature(g)
        g.waste.append(g.stock.pop());self.assertTrue(restart_hand(g));self.assertEqual(self.signature(g),new)
