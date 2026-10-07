"""Heads-up all-in blind calls and missing turn owners."""
import unittest
from texas_holdem import TexasHoldemGame
from holdem_turn_flow import repair_betting_turn

class HeadsUpTurnTests(unittest.TestCase):
    def game(self):
        game = TexasHoldemGame()
        game.start_session([{'name': 'Rival'}], 1000, 5)
        game.dealer_index = 1
        game.npc_stacks = [7]
        game.start_hand()
        return game

    def test_short_all_in_big_blind_is_callable_and_runs_out(self):
        game = self.game()
        self.assertEqual(game.current_actor, 0)
        self.assertEqual(game.player_round_bet, 5)
        self.assertEqual(game.current_bet, 7)
        self.assertEqual(game.get_player_amount_to_call(), 2)
        self.assertTrue(game.can_player_act_now())
        self.assertFalse(game.can_player_raise())
        self.assertFalse(game.is_betting_round_complete())
        self.assertFalse(game.should_reveal_runout_hands())
        chips = game.player_stack + sum(game.npc_stacks) + game.pot
        self.assertTrue(game.player_call())
        self.assertTrue(game.should_reveal_runout_hands())
        for stage in ('flop', 'turn', 'river', 'showdown'):
            repair_betting_turn(game)
            self.assertTrue(game.advance_after_betting_round())
            self.assertEqual(game.current_stage, stage)
        self.assertTrue(game.hand_complete)
        self.assertEqual(game.player_stack + sum(game.npc_stacks), chips)

    def test_stale_actor_and_all_in_flag_do_not_disable_a_call(self):
        game = self.game()
        game.current_actor = -1
        game.player_all_in = True
        repair_betting_turn(game)
        self.assertFalse(game.player_all_in)
        self.assertEqual(game.current_actor, 0)
        self.assertTrue(game.can_player_call())
        self.assertFalse(game.advance_after_betting_round())

    def test_multiway_short_big_blind_keeps_nominal_wager(self):
        game = TexasHoldemGame()
        game.start_session([{'name':'A'}, {'name':'B'}], 1000, 5)
        game.dealer_index = 2
        game.npc_stacks = [1000, 7]
        game.start_hand()
        self.assertEqual(game.current_bet, 10)
