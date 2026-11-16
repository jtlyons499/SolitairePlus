import copy
import json
import os
from pathlib import Path
import queue
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import pygame
import room_protocol
from room_table import RoomAuthority
from room_session import RoomTable
from room_protocol import ClientGame
from mp_widgets import TextInput,hand_type
from mp_options import Options
from mp_profile import MultiplayerProfile
from mp_appearance import Appearance
from mp_assets import TableView
from room_view import RoomView
from solitaireplus.app import state


class FakePeer:
    """Stands in for net_client.open_peer: an inbox the test fills and a list of sent messages."""
    def __init__(self):
        self.inbox=queue.Queue();self.sent=[];self.code='ABCDEF';self.opened=None
    def __call__(self,*args,**kwargs):
        self.opened=(args,kwargs);return self
    def send(self,message):
        self.sent.append(json.loads(json.dumps(message)));return True
    def close(self):pass


class FlowTests(unittest.TestCase):
    def setUp(self):
        state.holdem_table_speed="normal"
    def finish(self,t,now=0):
        for _ in range(700):
            if t.game.hand_complete:return now
            g=t.game
            if g.current_actor in t.humans.values() and not g.is_betting_round_complete():
                who=next(i for i,s in t.humans.items() if s==g.current_actor)
                t.act(who,'check_call',0,t.revision)
            now+=10000;t.update(now)
        self.fail('hand did not finish')

    def test_auto_next_without_any_ready(self):
        t=RoomAuthority('Host');t.join(1,'Guest');t.start();now=self.finish(t);hand=t.game.hand_number
        t.update(now+1);self.assertEqual(t.view(1)["next_hand_seconds"],6)
        t.update(now+1001);self.assertEqual(t.view(1)["next_hand_seconds"],5)
        t.update(now+5999);self.assertEqual(t.game.hand_number,hand)
        t.update(now+6001);self.assertEqual(t.game.hand_number,hand+1)

    def test_countdown_does_not_bump_revision(self):
        # B70: the next-hand countdown is sent as a 'starts at' time; the revision stays, so a
        # guest's action made a second or two later is still accepted.
        t=RoomAuthority('Host');t.join(1,'Guest');t.start();now=self.finish(t)
        t.update(now+1);revision=t.revision
        t.update(now+1001);t.update(now+2001)
        self.assertEqual(t.revision,revision)
        view=t.view(1)
        self.assertEqual(view['next_hand_seconds'],4)
        self.assertEqual((view['countdown_at'],view['host_now']),(now+6001,now+2001))
        self.assertTrue(t.act(1,'next_hand',0,revision))
        t.update(now+6001);self.assertFalse(t.game.hand_complete)
        view=t.view(1);self.assertIsNone(view['countdown_at']);self.assertEqual(view['next_hand_seconds'],6)

    def test_client_countdown_from_timestamp(self):
        # The guest turns the host's 'starts at' time into its own clock when the message arrives.
        t=RoomAuthority('Host');t.join(1,'Guest');t.start();now=self.finish(t);t.update(now+1);t.update(now+2001)
        peer=FakePeer()
        with patch('room_session.open_peer',new=peer):guest=RoomTable('Guest',False,'','ABCDEF')
        message=dict(t.view(1),mode='holdem',protocol=room_protocol.ROOM_PROTOCOL)
        peer.inbox.put(json.loads(json.dumps(message)));guest.update(50000)
        self.assertEqual(guest.now,50000);self.assertEqual(guest.countdown_until,54000)
        # During a hand there is no countdown.
        playing=dict(message,countdown_at=None);peer.inbox.put(playing);guest.update(51000)
        self.assertIsNone(guest.countdown_until)
        # Roulette sends the same two keys at the top level of its party_state.
        guest.mode='roulette';peer.inbox.put({'type':'party_state','mode':'roulette','phase':'betting','revision':9,
                                              'countdown_at':7000,'host_now':2000,'protocol':room_protocol.ROOM_PROTOCOL})
        guest.update(60000);self.assertEqual(guest.countdown_until,65000)
        peer.inbox.put({'type':'lobby','revision':10,'protocol':room_protocol.ROOM_PROTOCOL});guest.update(61000)
        self.assertIsNone(guest.countdown_until)
        # A table built without update() (as older tests do) still applies messages.
        bare=RoomTable.__new__(RoomTable);bare.game=ClientGame();bare.profile=None;bare.last_payout=None;bare.mode=None
        bare.apply(message);self.assertEqual(bare.countdown_until,4000)

    def test_malformed_countdown_is_ignored(self):
        # A countdown that is text, NaN, infinite or absurdly far away (JSON allows huge
        # integers) gives no local countdown, so nothing that draws it can raise.
        bare=RoomTable.__new__(RoomTable);bare.game=ClientGame();bare.profile=None;bare.last_payout=None;bare.mode=None
        huge=json.loads('1'+'0'*400)
        for at,host_now in (('abc',5),(float('nan'),5),(float('inf'),5),([1],5),(None,5),(5,None),
                            (huge,5),(5,-huge),(1e300,0),(3_600_001,0)):
            with self.subTest(countdown_at=str(at)[:12],host_now=str(host_now)[:12]):
                bare.apply({'type':'lobby','revision':1,'countdown_at':at,'host_now':host_now})
                self.assertIsNone(bare.countdown_until)
                self.assertEqual(RoomView.countdown_seconds(bare,{'next_hand_seconds':4},1000),4)
        bare.apply({'type':'lobby','revision':2,'countdown_at':3_600_000,'host_now':0})
        self.assertEqual(bare.countdown_until,3_600_000)

    def test_host_builds_view_only_on_revision_change(self):
        # B84: the host rebuilds its own view (and the guests') only when the revision moves.
        peer=FakePeer()
        with patch('room_session.open_peer',new=peer):host=RoomTable('Host',True,'')
        built=[];real=host.view
        def counting(identity):built.append(identity);return real(identity)
        host.view=counting
        for frame in range(10):host.update(frame*16)
        self.assertEqual(built,[0])
        peer.inbox.put({'type':'peer_joined','identity':1,'name':'Guest'});host.update(200)
        self.assertEqual(built,[0,0,1]);self.assertEqual(peer.sent[-1]['target'],1)
        self.assertTrue(host.act('start'));host.update(216);built.clear()
        revision=host.authority.revision
        for frame in range(10):host.update(216)   # same clock: nothing is due, nothing changes
        self.assertEqual(host.authority.revision,revision);self.assertEqual(built,[])
        self.assertTrue(host.act('chat','hi'));host.update(216)
        self.assertEqual(built,[0,1])
        self.assertEqual(host.message['chat_messages'][-1]['text'],'hi')

    def test_protocol_stamp(self):
        # The host stamps every message it sends; a guest warns once when the stamp is missing or
        # different, and still plays.
        peer=FakePeer()
        with patch('room_session.open_peer',new=peer):host=RoomTable('Host',True,'')
        peer.inbox.put({'type':'peer_joined','identity':1,'name':'Guest'});host.update(0)
        peer.inbox.put({'type':'action','sender':1,'action':'next_hand','revision':-5});host.update(16)
        kinds={m['type'] for m in peer.sent}
        self.assertLessEqual({'lobby','ack'},kinds)
        self.assertTrue(all(m.get('protocol')==room_protocol.ROOM_PROTOCOL for m in peer.sent),peer.sent)
        self.assertEqual(room_protocol.ROOM_PROTOCOL,3)
        self.assertEqual(peer.opened[1].get('version'),2)  # relay room version unchanged
        guest_peer=FakePeer()
        with patch('room_session.open_peer',new=guest_peer):guest=RoomTable('Guest',False,'','ABCDEF')
        lobby=[m for m in peer.sent if m['type']=='lobby'][-1]
        guest_peer.inbox.put(dict(lobby));guest.update(0)
        self.assertEqual(guest.version_notice,'');self.assertEqual(guest.leave_notice_seq,0)
        old=dict(lobby,revision=lobby['revision']+1);old.pop('protocol')
        guest_peer.inbox.put(old);guest.update(16)
        text="The host's Solitaire+ is a different version. Update both games to play together."
        self.assertEqual(guest.version_notice,text);self.assertEqual(guest.leave_notice,text)
        self.assertEqual(guest.leave_notice_seq,1);self.assertEqual(guest.message['revision'],old['revision'])
        guest_peer.inbox.put(dict(lobby,protocol=4,revision=lobby['revision']+2));guest.update(32)
        self.assertEqual(guest.leave_notice_seq,1);self.assertEqual(guest.message['revision'],lobby['revision']+2)
        # A later 'X left the game' notice from the host still shows.
        guest_peer.inbox.put({'type':'ack','leave_notice':'Bob left the game.','leave_seq':1,'protocol':3});guest.update(48)
        self.assertEqual(guest.leave_notice,'Bob left the game.');self.assertEqual(guest.leave_notice_seq,2)
        guest_peer.inbox.put({'type':'ack','leave_notice':'Bob left the game.','leave_seq':1,'protocol':3});guest.update(64)
        self.assertEqual(guest.leave_notice_seq,2)

    def test_sit_out_defers_preserves_chips_skips_blinds_and_rejoins(self):
        for who in (0,1):
            t=RoomAuthority('Host')
            for identity in range(1,6):t.join(identity,f'Guest {identity}')
            t.start();seat=t.humans[who]
            hand=copy.deepcopy(t.game.player_hand if not seat else t.game.npc_hands[seat-1])
            self.assertTrue(t.act(who,'sit_out',0,t.revision))
            self.assertEqual(t.game.player_hand if not seat else t.game.npc_hands[seat-1],hand)
            now=self.finish(t);stack=([t.game.player_stack,*t.game.npc_stacks])[seat]
            t.update(now+1);t.update(now+6001)
            self.assertNotIn(seat,t.game.hand_seat_indexes)
            self.assertNotIn(seat,(t.game.small_blind_index,t.game.big_blind_index))
            self.assertEqual(([t.game.player_stack,*t.game.npc_stacks])[seat],stack)
            self.assertEqual(t.game.player_hand if not seat else t.game.npc_hands[seat-1],[])
            self.assertTrue(t.game.player_folded if not seat else t.game.npc_folded[seat-1])
            self.assertTrue(t.act(who,'sit_out',0,t.revision))
            now=self.finish(t,now+8000);t.update(now+1);t.update(now+6001)
            self.assertIn(seat,t.game.hand_seat_indexes)

    def test_last_payout_survives_new_hand(self):
        t=RoomAuthority('Host');t.start();self.finish(t)
        room=RoomTable.__new__(RoomTable);room.game=ClientGame();room.profile=None;room.last_payout=None;room.mode=None
        room.apply(t.view(0));hand=room.last_payout.hand_number
        room.apply(t.view(0));self.assertEqual(len(room.payout_history),1)
        t.act(0,'next_hand',0,t.revision);room.apply(t.view(0))
        self.assertEqual(room.last_payout.hand_number,hand);self.assertGreater(room.game.hand_number,hand)

    def test_clipboard_replace_uppercase_copy_cut(self):
        pygame.init();pygame.display.set_mode((1366,768));field=TextInput()
        def key(k):return pygame.event.Event(pygame.KEYDOWN,key=k,mod=pygame.KMOD_CTRL)
        field.event(key(pygame.K_a),'OLD',5,True)
        with patch('pygame.scrap.get_text',return_value='ab123456'):
            value=field.event(key(pygame.K_v),'OLD',5,True)
        self.assertEqual(value,'AB123')
        with patch('pygame.scrap.put_text') as copy_text:
            field.event(key(pygame.K_c),value,5,True);copy_text.assert_called_once_with('AB123')
            self.assertEqual(field.event(key(pygame.K_x),value,5,True),'')

    def test_hand_type_before_and_after_flop(self):
        t=RoomAuthority('Host');t.start();g=t.game
        g.player_hand=[{'rank':'A','suit':'Spades'},{'rank':'A','suit':'Hearts'}];g.community_cards=[]
        self.assertEqual(hand_type(g),'One pair')
        g.community_cards=[{'rank':'2','suit':'Spades'},{'rank':'2','suit':'Hearts'},{'rank':'6','suit':'Clubs'}]
        self.assertIn('two pair',hand_type(g).lower())

    def test_speed_notice_and_inherited_display(self):
        t=RoomAuthority('Host');t.set_speed('normal');t.table_notices=[];t.set_speed('fast');t.set_speed('fast')
        self.assertEqual(t.table_notices,['Host has set table speed from Normal to Fast.'])
        pygame.init()
        # The window handed over by single-player is used for this start only (W1): it is the
        # start size and fullscreen choice, but it is not copied into the saved options.
        with tempfile.TemporaryDirectory() as folder, \
             patch.dict(os.environ,LOCALAPPDATA=folder,SOLITAIRE_MP_WINDOW='1920x1080',SOLITAIRE_MP_FULLSCREEN='0'):
            options=Options()
            self.assertEqual(options.start_size,(1920,1080));self.assertIs(options.start_fullscreen,False)
            self.assertIsNone(options.values['size']);self.assertFalse(options.values['fullscreen'])

    def test_all_in_label_and_persistent_details_button(self):
        pygame.init();surface=pygame.display.set_mode((1366,768))
        with tempfile.TemporaryDirectory() as directory:
            profile=MultiplayerProfile(directory=directory);view=RoomView(surface,TableView(surface),Appearance(profile))
            t=RoomAuthority('Host');t.start();m=t.view(0);g=ClientGame();g.apply(m);g.player_stack=0
            table=SimpleNamespace(game=g,message=m,failed=False,status='',code='12345',public_profiles={},pending=False,last_payout=SimpleNamespace(hand_number=0))
            labels=[];real=view.text
            def capture(text,*args,**kwargs):labels.append(text);return real(text,*args,**kwargs)
            view.text=capture;view.draw(table)
            self.assertIn('All in',labels);self.assertNotIn('Busted',labels)
            self.assertIn('details',[a for _,a in view.buttons])
