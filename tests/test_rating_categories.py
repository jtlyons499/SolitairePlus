import json, random, unittest
from fractions import Fraction
from itertools import combinations_with_replacement
from unittest.mock import patch
from career_ratings import *
from career_rating_events import settle_competitive_result, settle_house_result
from career_npc_development import ensure_npc_development, advance_npc_development
from score_four import ScoreFourGame
from score_four_difficulty import puzzle_pool
from five_o_poker import FiveOPokerGame
from rating_unlocks import add_rating_catalogs, unlock_ratings, lock_reason

class CategoryRatings(unittest.TestCase):
    def test_migration(self):
        old={'solitaire':1600,'score_four':1200,'texas_holdem':1800,'five_card_draw':1200,'seven_card_stud':1500,'blackjack':1200,'roulette':800,'overall':9999}
        r=normalize_rating_bundle(old)
        self.assertEqual([r[k] for k in RATING_KEYS],[1395,1400,1500,1000])
        self.assertEqual(r,normalize_rating_bundle(json.loads(json.dumps(r))))
        profile={'career':{'ratings':old,'cash':123,'leaderboard_state':{'npc':{'ratings':old,'rating':9999}}},'custom':True}
        migrate_profile_ratings(profile)
        self.assertEqual(profile['career']['leaderboard_state']['npc']['rating'],1395)
        self.assertEqual(profile['career']['cash'],123);self.assertTrue(profile['custom'])
    def test_categories_and_precision(self):
        r=normalize_rating_bundle({'strategy':1400});apply_rating_change(r,'score_four',45)
        self.assertAlmostEqual(r['strategy'],1444.1)
        self.assertEqual(r['solitaire'],r['strategy'])
        self.assertEqual(format(r['strategy'],','),'1,444')
        self.assertAlmostEqual(normalize_rating_bundle(json.loads(json.dumps(r)))['strategy'],1444.1)
        self.assertAlmostEqual(reward_scale(3000),.9)
        apply_rating_change(r,'solitaire',-5);self.assertAlmostEqual(r['strategy'],1439.1)
        with self.assertRaises(ValueError):apply_rating_change(r,'bango',1)
    def test_house(self):
        r=normalize_rating_bundle({})
        self.assertEqual(settle_house_result(r,{},'blackjack',100),15)
        self.assertEqual(settle_house_result(r,{},'blackjack',-100),-5)
        self.assertEqual(settle_house_result(r,{},'blackjack',0),0)
        self.assertEqual(settle_house_result(r,{},'faro',50),12)
    def test_competitive(self):
        for tier,reward in {'low':45,'mid':60,'strong':50,'elite':65}.items():
            self.assertEqual(settle_competitive_result(normalize_rating_bundle({}),{},{},'score_four',{'id':tier,'skill_tier':tier},1),reward)
    def test_development(self):
        npc={'id':'test','age':25,'skill_tier':'mid'};state=ensure_npc_career_state({'rating':1200},npc,random.Random(1))
        d=ensure_npc_development(state,npc,2026,1)
        self.assertEqual(set(d['anchor_ratings']),set(CATEGORY_KEYS))
        self.assertTrue(advance_npc_development(state,npc,2026,2))
        self.assertEqual(state['rating'],derive_overall(state['ratings']))
        self.assertFalse(advance_npc_development(state,npc,2026,2))
    def test_unlocks(self):
        catalogs=[{}, {}, {}];unlocked=[set(),set(),set()];add_rating_catalogs(*catalogs)
        self.assertTrue(all(len(c)==11 for c in catalogs))
        unlock_ratings({'strategy':1400},catalogs,unlocked)
        self.assertIn('bg_rating_strategy_1400',unlocked[0]);self.assertNotIn('bg_rating_strategy_1950',unlocked[0])
        unlock_ratings({'strategy':1000},catalogs,unlocked);self.assertIn('bg_rating_strategy_1400',unlocked[0])
        self.assertEqual(lock_reason('win',{},'felts',{},[{'title':'Wheel Winner','reward':{'type':'felt','id':'win'}}]),'Get Achievement: Wheel Winner')

class Puzzles(unittest.TestCase):
    def test_standard_complete(self):
        g=ScoreFourGame();expected={n for n in combinations_with_replacement(range(1,11),4) if g.solve_numbers([Fraction(v) for v in n])}
        self.assertEqual(set(puzzle_pool('standard')),expected)
        self.assertEqual(len(puzzle_pool('extreme')),300)
        self.assertTrue(any(max(v)>10 for v in puzzle_pool('extreme')))
    def test_solvable(self):
        g=ScoreFourGame()
        for difficulty in ('easy','standard','difficult','extreme'):
            g.start_solo_session(difficulty);self.assertIsNotNone(g.solution)
            for values in puzzle_pool(difficulty):self.assertIsNotNone(g.solve_numbers([Fraction(v) for v in values]))
    def test_hint(self):
        g=ScoreFourGame();g.original_numbers=[6,8,3,4];g.values=[Fraction(6),Fraction(8),Fraction(1),None];g.puzzle_start_time-=31
        self.assertTrue(g.request_solo_hint());self.assertIn('Reset',g.hint_text);self.assertIn('Try',g.hint_text)
        self.assertFalse(g.request_solo_hint())
        g.last_hint_at -= 31
        self.assertTrue(g.request_solo_hint());self.assertEqual(g.values,[Fraction(6),Fraction(8),Fraction(1),None])

class FiveO(unittest.TestCase):
    def game(self):
        g=FiveOPokerGame(random.Random(5));g.start_session({'id':'bob','name':'Bob','skill_tier':'mid'},1000)
        while g.phase=='placement':g.place_player_card(g.get_available_player_columns()[0])
        return g
    def test_raise_conserves_money(self):
        g=self.game();g.phase='betting';g.pending_npc_at=0;g.player_betting_paid=0;g.npc_betting_paid=0
        g.current_bet=g._commit_npc(20);g.npc_betting_paid=20;g.bet_state='player_response'
        with patch.object(g,'_npc_decision',return_value={'action':'call'}):
            g.bet_fraction=1;self.assertIn('bet',g.get_player_actions());self.assertTrue(g.player_bet())
            self.assertGreater(g.pending_npc_at,0);self.assertEqual(g.get_player_actions(),[])
            g.pending_npc_at-=2;g.update()
        self.assertTrue(g.showdown_pending_finish);self.assertEqual(g.player_betting_paid,g.npc_betting_paid)
        self.assertEqual(g.player_stack+g.npc_stack+g.pot,2000)
    def test_fast_reveal(self):
        g=self.game();g.pending_npc_at=0;g._showdown();g.fast_reveal=True;g.showdown_reveal_started_at-=2;g.update()
        self.assertTrue(g.hand_complete)

if __name__=='__main__':unittest.main()
