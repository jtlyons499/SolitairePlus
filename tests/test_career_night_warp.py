import ast,copy,unittest
from pathlib import Path
import pygame
from career_event_progress import store_event_progress,restore_event_progress
from career_time_warp import advance_months
from career_hub_controls import CareerHubControls
from texas_holdem import TexasHoldemGame

class NightWarpTests(unittest.TestCase):
 def test_night_snapshot_roundtrip_and_isolation(self):
  e={'activity_type':'niche_night'};n={'current_game_mode':'career','career_event_has_activity':True,'career_event_result_log':[{'game_id':'faro','net':20}],'faro_session_net':20}
  store_event_progress(e,n);n['career_event_result_log'].clear();restored={}
  self.assertTrue(restore_event_progress(e,restored));self.assertTrue(restored['career_event_has_activity']);self.assertEqual(restored['faro_session_net'],20);self.assertEqual(len(restored['career_event_result_log']),1)
  self.assertFalse(restore_event_progress({},restored))
  debug={'debug':True};store_event_progress(debug,n);self.assertNotIn('night_progress',debug)
 def test_month_jump_keeps_day_and_runs_every_skipped_day(self):
  for months in (1,3,6,12,60):
   date=[2026,11,19];calls=[]
   def advance(**kwargs):
    calls.append(kwargs);date[2]+=1
    if date[2]>30:
     date[2]=1;date[1]+=1
     if date[1]>12:date[1]=1;date[0]+=1
   count=advance_months(months,lambda:tuple(date),advance)
   self.assertEqual(count,months*30);self.assertEqual(date[2],19);self.assertTrue(all(c=={'completed':False,'save_after':False} for c in calls))
 def test_runout_exposes_only_when_calls_settled(self):
  g=TexasHoldemGame();g.start_session([{'id':'a','name':'A'},{'id':'b','name':'B'}],1000,10);g.start_hand()
  g.current_stage='preflop';g.player_stack=0;g.player_all_in=True;g.npc_stacks=[0,100];g.npc_all_in=[True,False];g.npc_folded=[False,True];g.current_bet=100
  self.assertTrue(g.should_reveal_runout_hands())
  g.npc_folded[1]=False;g.npc_round_bets[1]=0
  self.assertFalse(g.should_reveal_runout_hands())
  g.npc_round_bets[1]=100;self.assertTrue(g.should_reveal_runout_hands())
  g.player_stack=100;g.player_all_in=False;self.assertFalse(g.should_reveal_runout_hands())
 def test_warp_menu_clicks_and_header_placement(self):
  pygame.init();controls=CareerHubControls();out=pygame.Surface((1366,768));header=pygame.Rect(335,64,830,80)
  def draw(rect,label,font=None):pass
  controls.draw_time_warp(out,header,draw,controls.font)
  self.assertTrue(header.contains(controls.warp_rect));self.assertEqual(controls.get_action(controls.warp_rect.center),'warp_menu')
  controls.draw_time_warp(out,header,draw,controls.font)
  self.assertEqual(len(controls.warp_choices),5);self.assertEqual(controls.get_action(controls.warp_choices[60].center),'warp:60');self.assertFalse(controls.warp_open);pygame.quit()
 def test_production_entry_restore_and_return_save_hooks(self):
  s=Path('main.py').read_text();self.assertIn('if not restore_event_progress(career_event_entry, globals()):',s)
  select=s[s.index('elif current_state == STATE_CAREER_EVENT_SELECT:'):s.index('elif current_state == STATE_CAREER_REAL_ESTATE:',s.index('elif current_state == STATE_CAREER_EVENT_SELECT:'))]
  self.assertIn('store_event_progress(career_event_entry, globals())',select)
