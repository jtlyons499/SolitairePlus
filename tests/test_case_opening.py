"""Case odds, committed rewards, save rollback, isolated practice and reel alignment."""
import ast
import copy
import random
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pygame
import profile as profiles
from case_opening import CASES,ITEMS,new_case_state,normalize_case_state,case_price,purchase,award_earned_trophies
from case_opening_ui import CaseOpeningScreen
from career_ratings import make_player_rating_bundle,apply_rating_change


class CaseTests(unittest.TestCase):
 def test_prices_scale_and_failed_purchase_does_not_mutate(self):
  for key in CASES:
   self.assertGreater(case_price(key,100000),case_price(key,1000))
   state=new_case_state();before=copy.deepcopy(state)
   with self.assertRaises(ValueError):purchase(state,key,0)
   self.assertEqual(state,before)
 def test_all_odds_sum_to_100_and_every_category_has_real_items(self):
  for case in CASES.values():
   self.assertEqual(sum(case['weights'].values()),100)
   for kind in case['weights']:self.assertTrue(any(x['kind']==kind and not x.get('earned') for x in ITEMS.values()))
 def test_rewards_come_from_paid_price_and_preserve_receipt(self):
  for identity in ('cold_pizza','golden_shuffler','cash_vault','rating_blackjack','fan_club','midnight_felt'):
   state=new_case_state()
   with patch('case_opening.choose_item',return_value=ITEMS[identity]):receipt,cash=purchase(state,'collector',10000)
   self.assertEqual(state['opened'],1);self.assertEqual(state['inventory'][identity],1)
   self.assertEqual(state['history'][0],receipt)
   self.assertEqual(cash,10000-receipt['cost']+(receipt['amount'] if receipt['kind']=='cash' else 0))
   self.assertEqual(normalize_case_state(state),state)
 def test_history_is_bounded_and_duplicates_remain_collectible(self):
  state=new_case_state()
  with patch('case_opening.choose_item',return_value=ITEMS['cold_pizza']):
   for i in range(45):purchase(state,'street',100000)
  self.assertEqual(len(state['history']),30);self.assertEqual(state['inventory']['cold_pizza'],45)
 def test_profile_slots_and_old_save_defaults(self):
  with tempfile.TemporaryDirectory() as directory,patch.object(profiles,'SAVE_FOLDER',directory):
   for slot in (1,2):
    data=profiles.make_default_profile();data['case_opening']['opened']=slot;profiles.save_profile(data,slot)
   self.assertEqual(profiles.load_profile(1)['case_opening']['opened'],1)
   self.assertEqual(profiles.load_profile(2)['case_opening']['opened'],2)
  self.assertEqual(normalize_case_state(None),new_case_state())
  self.assertEqual(normalize_case_state({'history':[{'item_id':[]}],'inventory':{'bogus':5}}),new_case_state())
 def test_earned_trophies_are_idempotent_and_not_case_pulls(self):
  state=new_case_state();data={'stats':{'solitaire_wins':100},'unlocked':['table_clear']}
  award_earned_trophies(state,data);award_earned_trophies(state,data)
  self.assertEqual(state['inventory'],{'hundred_wins':1,'table_champion':1});self.assertEqual(state['opened'],0)
 def transaction_env(self,save):
  tree=ast.parse(Path('main.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='buy_case_for_screen')
  env=dict(copy=copy,current_game_mode='career',case_collection_state=new_case_state(),career_cash=10000,
           career_ratings=make_player_rating_bundle(1000),career_rating=1000,career_fans=50,unlocked_felts=set(),
           purchase_loot_case=purchase,apply_rating_change=apply_rating_change,clamp_fans=lambda n:max(0,n),auto_save_career=save)
  exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual case transaction','exec'),env);return env
 def test_save_failure_rolls_back_cash_ratings_fans_and_cosmetics(self):
  for identity in ('cash_vault','rating_blackjack','fan_club','midnight_felt'):
   def fail():raise OSError('disk full')
   env=self.transaction_env(fail);keys=['case_collection_state','career_cash','career_ratings','career_rating','career_fans','unlocked_felts']
   before=copy.deepcopy([env[k] for k in keys])
   with patch('case_opening.choose_item',return_value=ITEMS[identity]):
    with self.assertRaises(OSError):env['buy_case_for_screen']('prestige')
   self.assertEqual([env[k] for k in keys],before)
 def test_actual_career_rewards_and_free_play_do_not_touch_career(self):
  saves=[];env=self.transaction_env(lambda:saves.append(True))
  with patch('case_opening.choose_item',return_value=ITEMS['rating_blackjack']):receipt,wallet=env['buy_case_for_screen']('prestige')
  self.assertEqual(env['career_ratings']['blackjack'],1035);self.assertEqual(env['career_rating'],env['career_ratings']['overall'])
  self.assertEqual(len(saves),1)
  before=copy.deepcopy((env['case_collection_state'],env['career_cash'],env['career_ratings'],env['career_fans'],env['unlocked_felts']))
  env['current_game_mode']='free';env['case_screen']=SimpleNamespace(state=new_case_state(),wallet=5000)
  with patch('case_opening.choose_item',return_value=ITEMS['midnight_felt']):env['buy_case_for_screen']('street')
  self.assertEqual((env['case_collection_state'],env['career_cash'],env['career_ratings'],env['career_fans'],env['unlocked_felts']),before)
 def test_reel_ends_on_committed_item_and_skip_does_not_purchase_twice(self):
  pygame.init()
  try:
   pygame.display.set_mode((1366,768));screen=CaseOpeningScreen();state=new_case_state();calls=[]
   def buy(key):calls.append(key);return purchase(state,key,5000,random.Random(8))
   screen.enter(state,5000,buy);screen.begin('street');receipt=copy.deepcopy(screen.receipt)
   screen.update(screen.started+3800)
   self.assertEqual(screen.reel[36],receipt['item_id']);self.assertEqual(screen.phase,'result')
   winner_left=80+36*184-screen.target
   self.assertTrue(winner_left<=683<=winner_left+172)
   screen.begin('collector');screen.draw(pygame.Surface((1366,768)))
   rect=next(r for r,a in screen.buttons if a=='skip')
   screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1),rect.center)
   self.assertEqual(screen.phase,'result');self.assertEqual(len(calls),2);self.assertEqual(state['opened'],2)
   out=pygame.Surface((1366,768))
   for phase in ('shop','result','collection','trophies'):
    screen.phase=phase;screen.draw(out)
    pygame.image.save(out,'/workspace/scratch/8857fb6c22d0/cases_'+phase+'_preview.png')
  finally:pygame.quit()
