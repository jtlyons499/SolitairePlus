"""Real pot resolution, odd chips, modal controls and production timer gating."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
import pygame
from texas_holdem import TexasHoldemGame
from poker_recap import recap_lines, draw_recap, get_recap_action, handle_recap_action, CLOSE, NEXT
from achievements import make_default_achievement_state, record_event
from blind_mans_bluff import BlindMansBluffGame
from bluff_presentation import effects_for, draw_bluff_effects, update_bluff_presentation


def card(rank,suit):return {'rank':rank,'suit':suit}


def showdown_game(split=False):
    g=TexasHoldemGame();g.start_session([{'id':'a','name':'Alex'},{'id':'b','name':'Blake'}],1000,10);g.start_hand()
    g.community_cards=[card('2','Clubs'),card('3','Diamonds'),card('4','Hearts'),card('8','Spades'),card('9','Clubs')]
    if split:
        g.player_hand=[card('A','Spades'),card('K','Diamonds')]
        g.npc_hands=[[card('A','Hearts'),card('K','Clubs')],[card('Q','Hearts'),card('J','Spades')]]
        g.player_hand_contribution=5;g.npc_hand_contributions=[5,5];g.pot=15
    else:
        g.player_hand=[card('A','Spades'),card('A','Diamonds')]
        g.npc_hands=[[card('K','Hearts'),card('K','Clubs')],[card('Q','Hearts'),card('Q','Spades')]]
        g.player_hand_contribution=100;g.npc_hand_contributions=[200,200];g.pot=500
    g.player_stack=1000-g.player_hand_contribution
    g.npc_stacks=[1000-x for x in g.npc_hand_contributions]
    g.player_folded=False;g.npc_folded=[False,False];g.player_busted=False;g.npc_busted=[False,False]
    g.current_stage='river';g.showdown()
    return g


class RecapTests(unittest.TestCase):
    def test_actual_main_and_side_pots_show_winning_hands_and_net(self):
        g=showdown_game();lines=recap_lines(g)
        self.assertFalse(g.recap_open)
        self.assertEqual([x['amount'] for x in g.last_pot_awards],[300,200])
        self.assertTrue(any('Main pot: $300' in x and 'Aces' in x for x in lines))
        self.assertTrue(any('Side pot 1: $200' in x and 'Kings' in x for x in lines))
        self.assertIn('You received: $300',lines)
        self.assertIn('Your net for this hand: +$200',lines)
        self.assertEqual(g.player_stack+sum(g.npc_stacks),3000)

    def test_split_odd_chip_is_assigned_to_exact_winner(self):
        g=showdown_game(True);lines=recap_lines(g)
        self.assertFalse(g.recap_open)
        self.assertIn('    You receive $8 (odd chip included)',lines)
        self.assertIn('    Alex receives $7',lines)
        self.assertIn('You received: $8',lines)
        self.assertIn('Your net for this hand: +$3',lines)

    def test_modal_blocks_underlying_actions_and_paginates(self):
        g=showdown_game();g.last_pot_awards *= 2
        handle_recap_action(g,"recap_open")
        self.assertEqual(get_recap_action((900,730),g),'recap_block')
        self.assertEqual(get_recap_action(NEXT.center,g),'recap_next')
        handle_recap_action(g,'recap_next');self.assertEqual(g.recap_page,1)
        handle_recap_action(g,'recap_close');self.assertFalse(g.recap_open)
        self.assertEqual(get_recap_action((900,730),g),None)
        handle_recap_action(g,'recap_open');self.assertEqual(g.recap_page,0)

    def test_production_timers_pause_and_restart_after_review(self):
        tree=ast.parse(Path('main.py').read_text())
        branches=[]
        for node in ast.walk(tree):
            if not isinstance(node,ast.If):continue
            condition=ast.unparse(node.test)
            if condition=='getattr(texas_holdem_game, \'recap_open\', False)' and any(isinstance(x,ast.Assign) for x in node.body):
                branches.append(node)
            elif 'texas_holdem_next_hand_at == 0' in condition and 'is_holdem_auto_deal_enabled()' in condition:
                branches.append(node)
        self.assertEqual(len(branches),2)
        branches.sort(key=lambda n:n.lineno)
        program=compile(ast.Module(body=branches,type_ignores=[]),'real recap timer gates','exec')
        g=showdown_game();env=dict(texas_holdem_game=g,texas_holdem_next_hand_at=500,texas_holdem_session_end_at=800,
                                 now=10000,is_holdem_auto_deal_enabled=lambda:True,get_holdem_next_hand_delay=lambda:15000)
        exec(program,env)
        self.assertEqual((env['texas_holdem_next_hand_at'],env['texas_holdem_session_end_at']),(500,800))
        handle_recap_action(g,'recap_open')
        exec(program,env)
        self.assertEqual((env['texas_holdem_next_hand_at'],env['texas_holdem_session_end_at']),(0,0))
        g.recap_open=False;exec(program,env)
        self.assertEqual(env['texas_holdem_next_hand_at'],25000)

    def test_table_clear_unlocks_once_and_old_stats_survive(self):
        state=make_default_achievement_state();state['stats']['holdem_hand_wins']=8
        state,unlocked=record_event(state,'poker_table_clear',game='texas_holdem')
        self.assertIn('table_clear',[x['id'] for x in unlocked])
        state,again=record_event(state,'poker_table_clear',game='five_card_draw')
        self.assertNotIn('table_clear',[x['id'] for x in again])
        self.assertEqual(state['stats']['holdem_hand_wins'],8)

    def test_actual_main_table_clear_hook_does_not_repeat_each_frame(self):
        tree=ast.parse(Path('main.py').read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='process_texas_holdem_showdown')
        g=TexasHoldemGame();g.start_session([{'name':'Rival'}],1000,10)
        g.hand_number=1;g.hand_complete=True;g.current_stage='showdown';g.npc_busted=[True];g.player_busted=False;g.winner_indexes=[]
        events=[]
        no_op=lambda *a,**k:None
        env=dict(texas_holdem_game=g,texas_holdem_last_processed_showdown_hand=0,texas_holdem_table_sweep_rewarded=False,
                 texas_holdem_next_hand_at=100,texas_holdem_session_end_at=0,current_game_mode='career',career_event_has_activity=False,
                 TEXAS_HOLDEM_TABLE_SWEEP_RATING_BONUS=100,TEXAS_HOLDEM_SESSION_END_DELAY=15000,
                 audio=SimpleNamespace(play_sound=no_op),pygame=SimpleNamespace(time=SimpleNamespace(get_ticks=lambda:50)),
                 record_poker_showdown=no_op,generate_showdown_chat=lambda game:[],post_texas_holdem_chat=no_op,
                 award_fans_for_rating_win=lambda *a:0,process_achievement_event=lambda name,**data:events.append(name))
        exec(compile(ast.Module(body=[function],type_ignores=[]),'actual table clear hook','exec'),env)
        env['process_texas_holdem_showdown']();env['process_texas_holdem_showdown']()
        self.assertEqual(events,['poker_table_clear'])

    def test_recap_render_and_chip_events_do_not_change_rules_or_repeat_sfx(self):
        pygame.init()
        try:
            pygame.display.set_mode((1366,768));surface=pygame.Surface((1366,768))
            g=showdown_game();draw_recap(surface,None,g)
            pygame.image.save(surface,'/workspace/scratch/8857fb6c22d0/holdem_recap_preview.png')
            bluff=BlindMansBluffGame();bluff.start_session([{'name':'Rival'}],1000)
            state=(bluff.player_stack,list(bluff.npc_stacks),bluff.pot,list(bluff.cards))
            sounds=[];update_bluff_presentation(bluff,sounds.append,100)
            fx=effects_for(bluff);self.assertTrue(fx.motions)
            first=list(sounds);update_bluff_presentation(bluff,sounds.append,200)
            self.assertEqual(sounds,first)
            draw_bluff_effects(surface,bluff,400)
            self.assertEqual((bluff.player_stack,list(bluff.npc_stacks),bluff.pot,list(bluff.cards)),state)
            update_bluff_presentation(bluff,sounds.append,1200);self.assertEqual(fx.motions,[])
        finally:pygame.quit()
