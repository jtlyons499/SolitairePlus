"""Repeated Five-O hands and short-stack all-in calls through real engines."""
import ast
import copy
import random
import tempfile
import unittest
from pathlib import Path
import pygame
from solitaireplus.games.poker.five_o import FiveOPokerGame
from solitaireplus.games.poker.niche_common import evaluate_five_card_hand, compare_scores
from solitaireplus.games.poker.holdem import TexasHoldemGame
from solitaireplus.games.poker.five_o_ui import draw_five_o_poker, get_five_o_action, FIVE_O_NEXT_RECT


class TablePolishTests(unittest.TestCase):
    def test_repeated_deals_compare_both_hands_and_conserve_chips(self):
        # Every hand is played through the real betting flow: the NPC's queued turns (its
        # opening on even hands included) run through update() once their pause is over, the
        # human checks or calls, and the column reveal finishes through update() too.
        game = FiveOPokerGame(random.Random(17))
        game.start_session({'name': 'Rival'}, 100000)
        signatures = set()
        npc_opening_bets = 0
        for hand in range(40):
            while game.phase == 'placement':
                self.assertTrue(game.place_player_card(game.get_available_player_columns()[0]))
            cards = [c for columns in (game.player_columns, game.npc_columns) for col in columns for c in col]
            self.assertEqual(len(cards), 50)
            self.assertEqual(len({(c['rank'], c['suit']) for c in cards}), 50)
            signatures.add(tuple((c['rank'], c['suit']) for c in cards))
            expected = [compare_scores(evaluate_five_card_hand(p), evaluate_five_card_hand(n))
                        for p, n in zip(game.player_columns, game.npc_columns)]
            self.assertEqual(game.phase, 'betting')
            self.assertEqual(game.bet_state, 'npc_open' if game.opening_index == 1 else 'player_open')
            for _ in range(10):
                if game.phase != 'betting':
                    break
                if game.pending_npc_at:
                    opening = game.bet_state == 'npc_open'
                    game.pending_npc_at -= 1000.0   # the NPC's thinking pause is over
                    game.update()
                    npc_opening_bets += opening and game.bet_state == 'player_response'
                    continue
                actions = game.get_player_actions()
                self.assertTrue(game.player_call() if 'call' in actions else game.player_check())
            self.assertEqual(game.phase, 'showdown')
            self.assertTrue(game.showdown_pending_finish)
            self.assertEqual(game.column_results, [{1:'player', -1:'npc', 0:'tie'}[x] for x in expected])
            after = (game.player_stack, game.npc_stack, game.hands_won, game.hands_lost, game.hands_tied)
            game._showdown()
            self.assertEqual(after, (game.player_stack, game.npc_stack, game.hands_won, game.hands_lost, game.hands_tied))
            self.assertEqual(game.player_stack + game.npc_stack + game.pot, 200000)
            game.showdown_reveal_started_at -= 1000.0   # every column has been revealed
            game.update()
            self.assertTrue(game.hand_complete)
            self.assertEqual(game.pending_npc_at, 0.0)
            self.assertTrue(game.start_hand())
        self.assertEqual(len(signatures), 40)
        self.assertGreater(npc_opening_bets, 0)   # the NPC's opening bets are exercised

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
            with tempfile.TemporaryDirectory() as folder:   # preview image, deleted afterwards
                pygame.image.save(out, str(Path(folder) / 'five_o_polish_preview.png'))
        finally:
            pygame.quit()
