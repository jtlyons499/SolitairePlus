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
from standalone_view import TableView
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

    def test_avatar_import_frame_limits(self):
        pygame.init();pygame.display.set_mode((1366,768))
        path=Path(self.temp.name)/'my_avatar.png';image=pygame.Surface((256,256));image.fill((92,145,70));pygame.image.save(image,path)
        self.p.import_avatar(path);self.assertIsNotNone(clean_public(self.p.public()))
        self.assertLess(len(json.dumps(self.p.public())),25000)
        self.assertIsNone(clean_public({'avatar':'x'*24001,'level':1}))
        self.assertIsNone(clean_public({'avatar':'not_png','level':1}))

    def test_profile_screen_locks_and_table_slider(self):
        from room_table import RoomAuthority
        from lan_protocol import ClientGame
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
