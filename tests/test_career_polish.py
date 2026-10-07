import ast
import copy
import random
from pathlib import Path
from types import SimpleNamespace
import unittest
from press_interview import PRESS_INTERVIEW_QUESTION_POOL, select_interview, answer_outcome
from career_session_summary import poker_session_status, night_game_net, night_cash_total, track_night_cash
from career_event_progress import store_event_progress, restore_event_progress
from rating_unlocks import add_rating_catalogs, unlock_ratings, rating_lock_progress, lock_reason

SOURCE=ast.parse(Path('main.py').read_text())
def production_function(name, env):
 node=next(n for n in SOURCE.body if isinstance(n,ast.FunctionDef) and n.name==name)
 exec(compile(ast.Module(body=[node],type_ignores=[]),'production Career function','exec'),env)
 return env[name]

class CareerPolishTests(unittest.TestCase):
 def test_fixed_dialogue_valid_and_selection_does_not_modify_catalog(self):
  original=copy.deepcopy(PRESS_INTERVIEW_QUESTION_POOL)
  self.assertEqual(len(original),30)
  self.assertEqual(len({q['id'] for q in original}),30)
  for question in original:
   self.assertEqual(len(question['answers']),3)
   self.assertTrue(all(len(answer)==3 and answer[0] and len(answer[0])<90 for answer in question['answers']))
  history=[]
  for seed in range(20):
   batch=select_interview(history,random.Random(seed))
   self.assertEqual(len({q['topic'] for q in batch}),3)
   self.assertFalse(set(history)&{q['id'] for q in batch})
   history=(history+[q['id'] for q in batch])[-12:]
  self.assertEqual(original,PRESS_INTERVIEW_QUESTION_POOL)
 def test_answer_positions_vary_and_heat_is_bounded(self):
  positions=set()
  for seed in range(40):
   for q in select_interview([],random.Random(seed)):
    positions.add(max(range(3),key=lambda i:q['answers'][i][2]))
  self.assertEqual(positions,{0,1,2})
  self.assertEqual(answer_outcome(95,('Good',30,1),1000,0)[0],100)
  self.assertEqual(answer_outcome(-95,('Bad',-30,-1),1000,0)[0],-100)
  self.assertLess(answer_outcome(0,('Bad',-30,-1),1000,0)[1],0)
 def test_cash_xp_snapshots_survive_reentry_and_legacy_progress(self):
  env={'current_game_mode':'career','career_cash':1000,'player_xp':90}
  entry={};restore_event_progress(entry,env)
  env.update(career_cash=1150,player_xp=200)
  store_event_progress(entry,env);restore_event_progress(entry,env)
  self.assertEqual(env['career_event_start_cash'],1000)
  self.assertEqual(env['career_event_start_xp'],90)
  restore_event_progress({'night_progress':{}},env)
  self.assertEqual(env['career_event_start_cash'],1150)
  self.assertEqual(env['career_event_start_xp'],200)
 def test_niche_money_sums_sessions(self):
  self.assertEqual(night_game_net([dict(game_id='faro',net=150),dict(game_id='faro',net=-50),dict(game_id='five_o_poker',net=80)],'faro',-50),100)
  self.assertEqual(night_game_net([],'faro',12),12)
 def test_casino_summary_keeps_cash_results_instead_of_generic_fallback(self):
  env=dict(career_event_entry={'activity_type':'casino'},CAREER_ACTIVITY_CASINO_NIGHT='casino',CAREER_ACTIVITY_CASUAL_CARDS='casual',CAREER_ACTIVITY_POKER_NIGHT='poker',CAREER_ACTIVITY_NICHE_NIGHT='niche',CAREER_EVENT_NAMES={'casino':'Casino Night'},blackjack_session_net=30,roulette_session_net=-10,horse_races_session_net=0,blackjack_session_rating_change=15,career_cash=1020,career_fans=10)
  env['night_cash_total']=night_cash_total
  production_function('_build_career_event_summary',env)()
  self.assertIn('Blackjack: +$30',env['career_event_summary_lines'])
  self.assertIn('Roulette: -$10',env['career_event_summary_lines'])
  self.assertEqual(env['career_event_summary_title'],'CASINO NIGHT COMPLETE')
 def test_night_summary_reports_whole_rating_fans_cash_and_xp(self):
  env=dict(career_event_entry={'activity_type':'niche'},CAREER_ACTIVITY_CASINO_NIGHT='casino',CAREER_ACTIVITY_CASUAL_CARDS='casual',CAREER_ACTIVITY_POKER_NIGHT='poker',CAREER_ACTIVITY_NICHE_NIGHT='niche',career_rating=1045.5,career_ratings={'strategy':1050,'poker':1050,'casino':1005},career_event_start_global=1000,career_event_start_strategy=1000,career_event_start_poker=1000,career_event_start_casino=1000,career_fans=107,career_event_start_fans=100,career_cash=930,career_event_start_cash=1000,player_xp=220,career_event_start_xp=90)
  env['_build_career_event_summary']=lambda:env.update(career_event_summary_lines=['Niche Game Night completed.'])
  production_function('build_career_event_summary',env)()
  self.assertIn('Global Rating: 1,046 (+46)',env['career_event_summary_lines'])
  self.assertIn('Fans: 107 (+7)',env['career_event_summary_lines'])
  self.assertIn('Night cash: -$70  |  XP earned: +130',env['career_event_summary_lines'])
 def test_poker_exit_before_first_completed_hand_does_not_reward_xp(self):
  for key in ('texas_holdem','five_card_draw','seven_card_stud'):
   game=SimpleNamespace(current_stage='preflop',player_stack=1000,rating_seen_hands=set(),session_xp_rewarded=False)
   xp=[];env={f'{key}_game':game,f'{key}_buy_in_active':True,f'{key}_starting_stack':1000,f'{key}_session_net':0,'career_cash':0,'current_game_mode':'career','STATE_CAREER_EVENT_SELECT':'select','award_game_xp':lambda *a,**k:xp.append((a,k)),'rate_poker_cash_out':lambda *a:0,'track_night_cash':track_night_cash,'auto_save_career':lambda:None,'lose_fans_for_bad_result':lambda *a,**k:None}
   finish=production_function('finish_'+key+'_session',env);finish()
   self.assertEqual(xp,[],key)
   game.rating_seen_hands.add(1);finish();finish()
   self.assertEqual(len(xp),1,key)
   self.assertIn('Session counts',poker_session_status(game))
  self.assertIn('Complete 1 hand',poker_session_status(SimpleNamespace()))
  self.assertIn('Practice',poker_session_status(SimpleNamespace(),False))
 def test_night_money_ledger_accumulates_and_survives_reentry(self):
  env={'current_game_mode':'career','career_cash':1000,'player_xp':0}
  entry={};restore_event_progress(entry,env)
  track_night_cash(env,'blackjack',150)
  track_night_cash(env,'blackjack',-30)
  track_night_cash(env,'five_o_poker',80)
  store_event_progress(entry,env);restore_event_progress(entry,env)
  self.assertEqual(night_cash_total(env,'blackjack'),120)
  self.assertEqual(night_cash_total(env,'five_o_poker'),80)
  env['current_game_mode']='free';track_night_cash(env,'blackjack',999)
  self.assertEqual(night_cash_total(env,'blackjack'),120)
  restore_event_progress({},env)
  self.assertEqual(night_cash_total(env,'blackjack'),0)

 def test_rating_cosmetics_reconcile_on_load_and_remain_unlocked(self):
  catalogs=[{}, {}, {}];add_rating_catalogs(*catalogs);sets=[set(),set(),set()]
  env=dict(current_game_mode='menu',career_ratings={'strategy':1400,'poker':1000,'casino':1000,'overall':1300},MENU_BACKGROUNDS=catalogs[0],FELTS=catalogs[1],TITLES=catalogs[2],unlocked_menu_backgrounds=sets[0],unlocked_felts=sets[1],unlocked_titles=sets[2],unlock_ratings=unlock_ratings)
  grant=production_function('grant_rating_cosmetics',env);grant(force=True)
  self.assertIn('bg_rating_strategy_1400',sets[0])
  env['career_ratings']['strategy']=1000;grant(force=True)
  self.assertIn('bg_rating_strategy_1400',sets[0])
  data=catalogs[0]['bg_rating_strategy_1950']
  self.assertEqual(rating_lock_progress(data,{'strategy':1400.4}),'Current: 1,400 / 1,950')
  self.assertEqual(lock_reason('',data,'backgrounds',{},[]),'Reach 1,950 in Strategy Rating')
