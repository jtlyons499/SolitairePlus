"""Hint cadence, Undo selection cleanup, and automatic rating settlement."""
from fractions import Fraction
import unittest
from unittest.mock import patch
from score_four import ScoreFourGame
from tests.test_career_ratings import main_functions, npc
from career_ratings import make_player_rating_bundle

class ScoreFourFollowupTests(unittest.TestCase):
    def test_hint_meter_and_repeated_hints_use_same_clock(self):
        with patch('score_four.time.monotonic', return_value=100): g=ScoreFourGame()
        self.assertEqual(g.solo_hint_progress(100),0)
        self.assertAlmostEqual(g.solo_hint_progress(115),.5)
        with patch('score_four.time.monotonic', return_value=130):
            self.assertTrue(g.solo_hint_available())
            self.assertTrue(g.request_solo_hint())
            self.assertFalse(g.request_solo_hint())
        self.assertAlmostEqual(g.solo_hint_progress(145),.5)
        with patch('score_four.time.monotonic', return_value=160): self.assertTrue(g.request_solo_hint())
        with patch('score_four.time.monotonic', return_value=161):
            g.reset_current_puzzle()
            self.assertFalse(g.solo_hint_available())
            g.new_puzzle()
            self.assertEqual(g.solo_hint_progress(),0)

    def test_undo_restores_values_without_restoring_selection(self):
        g=ScoreFourGame();g.original_numbers=[6,8,3,4];g.values=list(map(Fraction,g.original_numbers))
        g.select_number(0);g.select_operator('+');g.select_number(1)
        self.assertEqual(g.values[1],14)
        g.select_number(2);g.select_operator('-')
        self.assertTrue(g.undo())
        self.assertEqual(g.values,list(map(Fraction,g.original_numbers)))
        self.assertIsNone(g.selected_index);self.assertIsNone(g.selected_operator)
        g.select_number(0);g.select_operator('+');self.assertTrue(g.undo())
        self.assertIsNone(g.selected_index);self.assertIsNone(g.selected_operator)

    def settlement(self, mode, winner):
        g=ScoreFourGame();g.start_competitive_session('mid');g.match_complete=True;g.match_winner=winner
        g.player_score,g.npc_score=(3,1) if winner=='player' else (1,3)
        events=[];noop=lambda *a,**k:0
        env=main_functions('settle_score_four_session_result','rate_competitive_game','award_career_rating',
            score_four_game=g,score_four_opponent_npc=npc(),current_game_mode=mode,
            award_fans_for_rating_win=noop,process_achievement_event=noop,award_game_xp=noop,
            record_career_event_result=lambda *a,**k:events.append((a,k)))
        return g,env,events

    def test_loss_is_banked_once_without_clicking_continue(self):
        g,env,events=self.settlement('career','npc')
        env['settle_score_four_session_result']()
        self.assertEqual(env['career_ratings']['strategy'],990)
        self.assertEqual(g.last_rating_change,-10)
        env['settle_score_four_session_result']()
        self.assertEqual(len(events),1)
        self.assertEqual(env['career_rating_results']['score_four']['losses'],1)

    def test_win_uses_current_rating_multiplier_and_stays_once_only(self):
        g,env,events=self.settlement('career','player')
        env['career_ratings']=make_player_rating_bundle(1400)
        env['settle_score_four_session_result']()
        self.assertEqual(g.last_rating_change,59)
        self.assertAlmostEqual(float(env["career_ratings"]["strategy"]),1458.8)
        env['settle_score_four_session_result']()
        self.assertEqual(len(events),1)

    def test_free_play_loss_has_no_career_rating_effect(self):
        g,env,events=self.settlement('free','npc')
        before=env['career_ratings'].copy()
        env['settle_score_four_session_result']()
        self.assertEqual(env['career_ratings'],before)
        self.assertEqual(g.last_rating_change,0)
