import json
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
import pygame

from mp_profile import MultiplayerProfile, clean_public, winning_xp
from mp_appearance import Appearance
from mp_profile_ui import ProfileScreen
from room_session import RoomTable
from room_view import RoomView
from mp_assets import TableView
import test_relay


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.p=MultiplayerProfile(directory=self.temp.name)

    def test_awards_deduplicate_and_unlock_persist(self):
        key=next(k for k in self.p.catalog['felt'] if k!='f_default')
        self.assertFalse(self.p.select('felt',key))
        for i in range(5):self.assertTrue(self.p.award({'id':f'room:{i}','xp':20}))
        self.assertFalse(self.p.award({'id':'room:4','xp':20}))
        self.assertEqual(self.p.level,2);self.assertTrue(self.p.select('felt',key))
        other=MultiplayerProfile(directory=self.temp.name)
        self.assertEqual(other.data['xp'],100);self.assertEqual(other.data['selected']['felt'],key)
        self.assertNotIn('xp',self.p.public());self.assertNotIn('awards',self.p.public())

    def test_slots_and_corrupt_fields(self):
        self.p.data['name']='First';self.p.save();self.p.load(2)
        self.assertEqual(self.p.data['name'],'Player');self.p.load(1)
        self.assertEqual(self.p.data['name'],'First')
        self.p.path.write_text(json.dumps({'xp':'oops','selected':None,'awards':None}),encoding='utf-8')
        self.p.load(1);self.assertEqual(self.p.data['xp'],0)

    def test_split_sidepot_and_waiter_rewards(self):
        game=SimpleNamespace(last_pot_awards=[{'amount':100,'winners':[0,1]},{'amount':50,'winners':[2]}])
        self.assertEqual(winning_xp(game,{0:0,1:1,2:2,3:3},{0,1,2}),{0:10,1:10,2:20})
        self.assertEqual(winning_xp(game,{0:0,4:2},{0}),{0:10})

    def test_returned_chips_give_no_xp(self):
        # B79: a pot made only of the winners' own chips (contributors within winners) is not a win.
        game=SimpleNamespace(last_pot_awards=[{'amount':300,'winners':[0],'eligible':[0],'contributors':[0]},
                                              {'amount':400,'winners':[1,2],'eligible':[1,2],'contributors':[2,1]}])
        self.assertEqual(winning_xp(game,{0:0,1:1,2:2},{0,1,2}),{})
        # A real win elsewhere in the hand still counts, once.
        game.last_pot_awards.append({'amount':90,'winners':[0],'eligible':[0,3],'contributors':[0,3]})
        self.assertEqual(winning_xp(game,{0:0,1:1,2:2},{0,1,2}),{0:20})

    def test_dead_money_layer_still_gives_xp(self):
        # A pot only the winner could take still holds other seats' (folded) chips: XP as before.
        game=SimpleNamespace(last_pot_awards=[{'amount':150,'winners':[0],'eligible':[0],'contributors':[0,3,4]},
                                              {'amount':200,'winners':[1,2],'eligible':[1,2],'contributors':[1,2,5]}])
        self.assertEqual(winning_xp(game,{0:0,1:1,2:2},{0,1,2}),{0:20,1:10,2:10})
        # Pot records from an older host have no contributors: today's rule.
        old=SimpleNamespace(last_pot_awards=[{'amount':100,'winners':[0]},{'amount':60,'winners':[1,2],'contributors':[]}])
        self.assertEqual(winning_xp(old,{0:0,1:1,2:2},{0,1,2}),{0:20,1:10,2:10})

    def test_room_showdown_split_of_own_chips_gives_no_xp(self):
        # Through the real room engine: heads-up, both all in, a tie splits only their own chips.
        import random
        from room_table import RoomAuthority
        suits={'c':'Clubs','d':'Diamonds','h':'Hearts','s':'Spades'}
        def card(text):return {'rank':text[:-1],'suit':suits[text[-1]]}
        random.seed(6)
        t=RoomAuthority('Host')
        for identity in range(1,6):t.join(identity,f'Guest {identity}')
        t.start();g=t.game
        self.assertTrue(g.record_pot_contributors)
        g.player_stack,g.npc_stacks=1000,[1000,0,0,0,0];g.refresh_busted_state();g.hand_complete=True
        for identity in sorted(t.humans):t.act(identity,'next_hand',0,t.revision)
        self.assertEqual(sorted(g.hand_seat_indexes),[0,1])
        g.player_hand=[card('Ah'),card('Qh')];g.npc_hands[0]=[card('As'),card('Qs')]
        board=['2c','7d','9h','Js','Kc']  # each street burns one card first; the deck pops from its end
        g.deck=[card(c) for c in (board[4],'8c',board[3],'8d',board[2],board[1],board[0],'8h')]
        now=0
        for _ in range(200):
            if g.hand_complete:break
            seat=g.current_actor
            if not g.is_betting_round_complete() and g.actor_needs_action(seat):
                stack=[g.player_stack,*g.npc_stacks][seat];bet=[g.player_round_bet,*g.npc_round_bets][seat]
                if not t.act(seat,'bet_raise',stack+bet,t.revision):self.assertTrue(t.act(seat,'check_call',0,t.revision))
            else:now+=10000;t.update(now)
        self.assertTrue(g.hand_complete);self.assertEqual([g.player_stack,g.npc_stacks[0]],[1000,1000])
        [pot]=g.last_pot_awards
        self.assertEqual((pot['amount'],sorted(pot['winners']),sorted(pot['contributors'])),(2000,[0,1],[0,1]))
        self.assertEqual(winning_xp(g,dict(t.humans),set(t.humans)),{})
        # The guest's view carries the contributors seat-relative.
        self.assertEqual(sorted(t.view(1)['data']['last_pot_awards'][0]['contributors']),[0,1])

    def test_avatar_import_frame_limits(self):
        pygame.init();pygame.display.set_mode((1366,768))
        path=Path(self.temp.name)/'my_avatar.png';image=pygame.Surface((256,256));image.fill((92,145,70));pygame.image.save(image,path)
        self.p.import_avatar(path);self.assertIsNotNone(clean_public(self.p.public()))
        self.assertLess(len(json.dumps(self.p.public())),25000)
        self.assertIsNone(clean_public({'avatar':'x'*24001,'level':1}))
        self.assertIsNone(clean_public({'avatar':'not_png','level':1}))

    def test_profile_screen_locks_and_table_slider(self):
        from room_table import RoomAuthority
        from room_protocol import ClientGame
        pygame.init();surface=pygame.display.set_mode((1366,768));appearance=Appearance(self.p)
        panel=ProfileScreen(self.p,appearance);panel.draw(surface)
        t=RoomAuthority('Host');t.start();g=ClientGame();m=t.view(0);g.apply(m);g.current_actor=0
        table=SimpleNamespace(game=g,message=m,failed=False,status='Your turn',code='TESTCODE',public_profiles={},pending=False,act=lambda *a:True)
        view=RoomView(surface,TableView(surface),appearance);view.draw(table)
        self.assertTrue(all(surface.get_rect().contains(rect) for rect,_ in view.buttons))
        self.assertTrue(any(action=='check_call' for _,action in view.buttons))
        if view.slider:
            view.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1),view.slider.center,table)
            view.event(pygame.event.Event(pygame.MOUSEMOTION),view.slider.midright,table)
            self.assertEqual(view.raise_amount,view.maximum)


class ProfileRelayTests(unittest.TestCase):
    setUp=test_relay.RelayTests.setUp
    tearDown=test_relay.RelayTests.tearDown

    def test_live_avatars_xp_and_repeated_snapshots(self):
        with tempfile.TemporaryDirectory() as directory:
            hp=MultiplayerProfile(directory=Path(directory)/'host');gp=MultiplayerProfile(directory=Path(directory)/'guest')
            pygame.init();pygame.display.set_mode((1,1));path=Path(directory)/'avatar.png'
            pic=pygame.Surface((96,96));pic.fill((200,150,50));pygame.image.save(pic,path);gp.import_avatar(path)
            host=RoomTable('Host',True,self.address,profile=hp);self.peers.append(host.peer)
            deadline=time.monotonic()+4
            while not host.code and time.monotonic()<deadline:host.update(0);time.sleep(.005)
            guest=RoomTable('Guest',False,self.address,host.code,profile=gp);self.peers.append(guest.peer)
            def pump(predicate):
                deadline=time.monotonic()+5
                while time.monotonic()<deadline:
                    host.update(pygame.time.get_ticks());guest.update(0)
                    if predicate():return
                    time.sleep(.005)
                self.fail('Room update timed out')
            pump(lambda:1 in host.public_profiles and 1 in guest.public_profiles)
            self.assertEqual(guest.public_profiles[1]['avatar'],gp.data['avatar'])
            self.assertTrue(host.act('start'));pump(lambda:guest.message['type']=='state')
            # Finish a known public payout without letting a waiting newcomer earn it.
            game=host.authority.game;game.last_pot_awards=[{'amount':100,'winners':[1]}];game.hand_complete=True
            host.collect_awards();host.last_sent=-1
            pump(lambda:gp.data['xp']==20)
            for _ in range(5):host.last_sent=-1;host.update(0);guest.update(0)
            self.assertEqual(gp.data['xp'],20);self.assertEqual(hp.data['xp'],0)
            self.assertNotIn('avatar',guest.message['seats'][1])
            self.assertNotIn('deck',guest.message['data'])


if __name__=='__main__':unittest.main()
