"""Repeated Five-O hands and short-stack all-in calls through real engines."""
import ast
import copy
import random
import unittest
from pathlib import Path
import pygame
from five_o_poker import FiveOPokerGame
from niche_poker_common import evaluate_five_card_hand, compare_scores
from texas_holdem import TexasHoldemGame
from five_o_poker_ui import draw_five_o_poker, get_five_o_action, FIVE_O_NEXT_RECT


class TablePolishTests(unittest.TestCase):
    def test_repeated_deals_compare_both_hands_and_conserve_chips(self):
        game = FiveOPokerGame(random.Random(17))
        game.start_session({'name': 'Rival'}, 100000)
        signatures = set()
        for hand in range(40):
            while game.phase == 'placement':
                self.assertTrue(game.place_player_card(game.get_available_player_columns()[0]))
            cards = [c for columns in (game.player_columns, game.npc_columns) for col in columns for c in col]
            self.assertEqual(len(cards), 50)
            self.assertEqual(len({(c['rank'], c['suit']) for c in cards}), 50)
            signatures.add(tuple((c['rank'], c['suit']) for c in cards))
            expected = [compare_scores(evaluate_five_card_hand(p), evaluate_five_card_hand(n))
                        for p, n in zip(game.player_columns, game.npc_columns)]
            game._showdown()
            self.assertEqual(game.column_results, [{1:'player', -1:'npc', 0:'tie'}[x] for x in expected])
            after = (game.player_stack, game.npc_stack, game.hands_won, game.hands_lost, game.hands_tied)
            game._showdown()
            self.assertEqual(after, (game.player_stack, game.npc_stack, game.hands_won, game.hands_lost, game.hands_tied))
            self.assertEqual(game.player_stack + game.npc_stack + game.pot, 200000)
            game.showdown_pending_finish = False
            game._finish_hand()
            self.assertTrue(game.start_hand())
        self.assertEqual(len(signatures), 40)

    def test_reported_high_card_example_is_not_a_tie(self):
        def cards(ranks):
            return [{'rank': r, 'suit': ['Clubs','Hearts','Spades','Diamonds','Clubs'][i]} for i,r in enumerate(ranks)]
        self.assertEqual(compare_scores(evaluate_five_card_hand(cards(['A','K','9','8','5'])),
                                        evaluate_five_card_hand(cards(['K','Q','6','4','2']))), 1)

    def test_all_in_raise_button_routes_short_stack_to_real_call(self):
        game = TexasHoldemGame()
        game.start_session([{'name':'Rival'}], 50000, 10)
        game.start_hand()
        game.current_actor = 0
        game.current_bet = 34500
        game.player_round_bet = 0
        game.player_stack = 24300
        game.player_has_acted = False
        self.assertFalse(game.can_player_raise())
        before = game.pot
        self.assertTrue(game.player_raise(24300))
        self.assertEqual(game.player_stack, 0)
        self.assertEqual(game.pot - before, 24300)
        self.assertTrue(game.player_all_in)

    def test_large_card_layout_and_next_hand_hit_target_render(self):
        pygame.init()
        try:
            pygame.display.set_mode((1366,768))
            out = pygame.Surface((1366,768))
            fonts = [pygame.font.Font(None,n) for n in (40,30,23)]
            game = FiveOPokerGame(random.Random(6))
            game.start_session({'name':'Rival'}, 1000)
            while game.phase == 'placement':
                game.place_player_card(game.get_available_player_columns()[0])
            game._showdown();game.showdown_pending_finish=False;game._finish_hand()
            game.showdown_revealed_columns=5
            game.result_text=game.pending_showdown_result_text
            draw_five_o_poker(out, None, game, 'Player', lambda **kw: out.fill((10,20,20)), *fonts)
            self.assertEqual(get_five_o_action(FIVE_O_NEXT_RECT.center, game), 'next_hand')
            pygame.image.save(out, '/workspace/scratch/8857fb6c22d0/five_o_polish_preview.png')
        finally:
            pygame.quit()
