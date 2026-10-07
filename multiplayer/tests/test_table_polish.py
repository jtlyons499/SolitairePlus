import copy
import tempfile
from types import SimpleNamespace
import unittest
import pygame

from room_table import RoomAuthority
from lan_protocol import ClientGame, snapshot
from mp_showdown import payout_lines
from mp_profile import MultiplayerProfile
from mp_appearance import Appearance
from mp_presentation import Presentation
from room_view import RoomView
from standalone_view import TableView
from mp_options import Options,SIZES


class PolishTests(unittest.TestCase):
    def test_buyback_only_between_hands_once_and_stale_rejection(self):
        t=RoomAuthority('Host');t.join(1,'Guest');t.start()
        self.assertFalse(t.act(1,'buyback',0,t.revision))
        t.game.hand_complete=True;t.game.npc_stacks[0]=0;t.game.npc_busted[0]=True
        self.assertFalse(t.act(1,'buyback',0,t.revision-1))
        self.assertTrue(t.act(1,'buyback',0,t.revision))
        self.assertEqual(t.game.npc_stacks[0],5000);self.assertEqual(t.chips_added,5000)
        self.assertFalse(t.game.npc_busted[0]);self.assertFalse(t.act(1,'buyback',0,t.revision))

    def test_npc_replacement_waits_for_ready_and_accounts_new_chips(self):
        t=RoomAuthority('Host');t.start();old=t.names[1]
        t.game.hand_complete=True;t.game.npc_stacks[0]=0;t.game.npc_busted[0]=True
        t.game.pot=0;before=sum([t.game.player_stack,*t.game.npc_stacks])
        t.update(99999);self.assertEqual(t.names[1],old)
        self.assertTrue(t.act(0,'next_hand',0,t.revision))
        self.assertNotEqual(t.names[1],old);self.assertEqual(t.chips_added,5000)
        self.assertEqual(sum([t.game.player_stack,*t.game.npc_stacks])+t.game.pot,before+5000)
        self.assertFalse(t.game.npc_busted[0])

    def test_all_humans_stay_busted_until_buyback(self):
        t=RoomAuthority('Host')
        for i in range(1,6):t.join(i,f'Human {i}')
        t.start();t.game.hand_complete=True;t.game.player_stack=0;t.game.player_busted=True
        old=t.game.hand_number
        for identity in t.connections:t.act(identity,'next_hand',0,t.revision)
        self.assertEqual(t.chips_added,0);self.assertGreater(t.game.hand_number,old)
        self.assertEqual(t.game.player_stack,0)

    def test_split_payouts_include_remainders_and_hand_description(self):
        g=SimpleNamespace(names=['A','B','C'],result_text='',last_pot_awards=[{'amount':101,'winners':[0,1],'share':50,'remainder':1,'hand':'Pair of aces, king kicker'},{'amount':60,'winners':[2],'share':60,'hand':'Straight, king high'}])
        lines=payout_lines(g)
        self.assertIn('A receives $51',lines);self.assertIn('B receives $50',lines)
        self.assertIn('Side pot 1: $60',lines);self.assertIn('Straight, king high',lines)

    def test_snapshot_showdown_descriptions_do_not_reveal_folded_cards(self):
        t=RoomAuthority('Host');t.start();g=t.game
        self.assertEqual(snapshot(g,0,1,t.names)['data']['showdown_hands'],{})
        g.community_cards=[{'rank':r,'suit':'Spades'} for r in ('2','3','4','5','6')]
        g.current_stage='showdown';g.npc_folded[0]=True
        data=snapshot(g,0,2,t.names)['data']
        self.assertNotIn('1',data['showdown_hands']);self.assertEqual(data['npc_hands'][0],[])
        self.assertIn('straight flush',data['showdown_hands']['0'].lower())

    def test_local_animation_never_mutates_game_and_sound_edges_once(self):
        events=[];a=Presentation(None,sound=events.append)
        g=SimpleNamespace(hand_number=1,player_round_bet=0,npc_round_bets=[0]*5,community_cards=[],hand_complete=False,winner_indexes=[])
        a.update(g,0);g.player_round_bet=100;before=copy.deepcopy(vars(g));a.update(g,100);a.update(g,110)
        self.assertEqual(vars(g),before);self.assertEqual(events.count('chip_move'),1)
        self.assertNotEqual(a.card_position(('seat',0,0),200,300,96,134,200)[:2],(200,300))
        self.assertEqual(a.card_position(('seat',0,0),200,300,96,134,1000)[:2],(200,300))

    def test_dynamic_names_shorter_and_buyback_controls(self):
        pygame.init();s=pygame.display.set_mode((1366,768))
        with tempfile.TemporaryDirectory() as directory:
            profile=MultiplayerProfile(directory=directory);appearance=Appearance(profile)
            a=RoomAuthority('Al');a.start();m=a.view(0);g=ClientGame();g.apply(m)
            table=SimpleNamespace(game=g,message=m,failed=False,status='',code='TESTCODE',public_profiles={},pending=False)
            view=RoomView(s,TableView(s),appearance);view.draw(table);short=view.badge_rects[0].width
            g.names[0]='A considerably longer player';view.draw(table)
            self.assertGreater(view.badge_rects[0].width,short)
            g.hand_complete=True;g.player_stack=0;view.draw(table)
            self.assertIn('buyback',[action for _,action in view.buttons])
            self.assertIn('details',[action for _,action in view.buttons])
            view.details=True;view.draw(table)

    def test_options_each_resolution_and_guest_pace_disabled(self):
        pygame.init();surface=pygame.display.set_mode((1366,768));options=Options()
        guest=SimpleNamespace(hosting=False)
        options.draw(surface,guest)
        self.assertFalse(any(isinstance(a,tuple) and a[0]=='speed' for _,a in options.buttons))
        for size in SIZES:
            options.values['size']=list(size);options.values['fullscreen']=False
            self.assertEqual(options.display().get_size(),size)


if __name__=='__main__':unittest.main()
