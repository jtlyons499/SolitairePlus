import copy
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import pygame
from room_table import RoomAuthority
from room_session import RoomTable
from lan_protocol import ClientGame
from mp_widgets import TextInput,hand_type
from mp_options import Options
from mp_profile import MultiplayerProfile
from mp_appearance import Appearance
from standalone_view import TableView
from room_view import RoomView

class FlowTests(unittest.TestCase):
    def setUp(self):
        import texas_holdem_ui as ui
        ui.holdem_table_speed="normal"
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
        room=RoomTable.__new__(RoomTable);room.game=ClientGame();room.profile=None;room.last_payout=None
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
        with patch.dict(os.environ,SOLITAIRE_MP_WINDOW='1920x1080',SOLITAIRE_MP_FULLSCREEN='0'):
            options=Options();self.assertEqual(options.values['size'],[1920,1080]);self.assertFalse(options.values['fullscreen'])

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
