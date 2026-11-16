import base64
import copy
import io
import os
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import pygame

from solitaireplus.app import paths, window
import mp_assets
from room_game import load_roster

from room_table import RoomAuthority
from room_protocol import ClientGame, snapshot
from mp_showdown import payout_lines
from mp_profile import MultiplayerProfile
from mp_appearance import Appearance
from mp_presentation import Presentation
from room_view import RoomView
from mp_assets import TableView
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
        # The fake holds the fields Presentation.update reads. Each one must be a real ClientGame field,
        # so the fake cannot drift from the engine again.
        g=SimpleNamespace(hand_number=1,current_stage='preflop',player_round_bet=0,npc_round_bets=[0]*5,
                          player_action_text='',npc_action_texts=['']*5,player_folded=False,npc_folded=[False]*5,
                          community_cards=[],hand_complete=False,winner_indexes=[],last_resolved_pot=0)
        t=RoomAuthority('Host');t.start();real=ClientGame();real.apply(t.view(0))
        self.assertEqual([name for name in vars(g) if not hasattr(real,name)],[])
        events=[];a=Presentation(None,sound=events.append)
        a.update(g,0);self.assertEqual(events,['card_draw'])   # a new hand: one deal sound
        # One update brings a bet, a check and a fold: one sound each, and none again on the next frame.
        g.player_round_bet=100;g.player_action_text='Bet $100'
        g.npc_action_texts[1]='Checked';g.npc_action_texts[2]='Folded';g.npc_folded[2]=True
        before=copy.deepcopy(vars(g));events.clear();a.update(g,100);a.update(g,110)
        self.assertEqual(vars(g),before)
        self.assertEqual(len([e for e in events if e.startswith('chips_')]),1)
        self.assertEqual(events.count('check'),1);self.assertEqual(events.count('card_move'),1);self.assertEqual(len(events),3)
        self.assertNotEqual(a.card_position(('seat',0,0),200,300,96,134,200)[:2],(200,300))
        self.assertEqual(a.card_position(('seat',0,0),200,300,96,134,1000)[:2],(200,300))
        # The player wins the hand: one flip at once, one win sound later, never repeated.
        g.hand_complete=True;g.winner_indexes=[0];g.last_resolved_pot=300
        before=copy.deepcopy(vars(g));events.clear()
        for now in (200,300,700,800):a.update(g,now)
        self.assertEqual(vars(g),before);self.assertEqual(events,['card_flip','hand_win'])

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
        pygame.init();surface=pygame.display.set_mode((1366,768))
        # A screen where every Options size fits; app/window.py resizes the window (W1).
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ,{'LOCALAPPDATA':folder}), \
             patch.object(window,'usable_area',return_value=(3840,2082)), \
             patch.object(window,'set_window_size') as resize:
            options=Options()
            guest=SimpleNamespace(hosting=False)
            options.draw(surface,guest)
            self.assertFalse(any(isinstance(a,tuple) and a[0]=='speed' for _,a in options.buttons))
            for size in SIZES:
                rect=next(rect for rect,action in options.buttons if action==('size',size))
                resize.reset_mock();options.values['fullscreen']=True
                options.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=rect.center),rect.center,guest)
                resize.assert_called_once_with(*size)
                self.assertEqual(options.values['size'],list(size));self.assertFalse(options.values['fullscreen'])


class ViewCacheTests(unittest.TestCase):
    """B84: RoomView and TableView reuse per-frame surfaces; B70: local countdown display."""
    def setUp(self):
        pygame.init();self.screen=pygame.display.set_mode((1366,768))
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)

    def make_view(self):
        appearance=Appearance(MultiplayerProfile(directory=self.directory.name))
        room=RoomAuthority('Al');room.start();message=room.view(0);game=ClientGame();game.apply(message)
        table=SimpleNamespace(game=game,message=message,failed=False,status='',code='TESTCODE',public_profiles={},pending=False)
        return RoomView(self.screen,TableView(self.screen),appearance),table

    @staticmethod
    def pixels(surface):
        return pygame.image.tobytes(surface,'RGBA')

    def test_wide_button_font_built_once(self):
        view,table=self.make_view()
        label='A label that is far too wide for this little button'
        self.assertGreater(view.small.size(label)[0],90-14)
        real=pygame.font.SysFont
        with patch('pygame.font.SysFont',side_effect=real) as sysfont:
            for _ in range(5):
                view.draw(table);view.button(label,(20,20,90,30),'x')
        requests=[(call.args,tuple(sorted(call.kwargs.items()))) for call in sysfont.call_args_list]
        self.assertTrue(requests)  # the wide label really took the smaller-font path
        self.assertEqual(len(requests),len(set(requests)),requests)  # each size built at most once

    def test_card_cache_reuses_scaled_card(self):
        view,_=self.make_view()
        canvas=pygame.Surface((400,300));view.surface=canvas
        queen={'rank':'Q','suit':'Hearts'}
        real=pygame.transform.smoothscale
        with patch('pygame.transform.smoothscale',side_effect=real) as smooth:
            for _ in range(4):
                canvas.fill((20,90,60));view.card(queen,30,40,96,134)
            cached=self.pixels(canvas)
            view.card(queen,200,40,60,84);view.card(None,300,40,60,84);view.card(None,300,140,60,84)
        sizes=[call.args[1] for call in smooth.call_args_list]
        self.assertEqual(sizes,[(96,134),(60,84),(60,84)])
        # The cached surfaces draw exactly what the old per-frame code drew.
        expected=pygame.Surface((400,300));expected.fill((20,90,60))
        shadow=pygame.Surface((96,134),pygame.SRCALPHA)
        pygame.draw.rect(shadow,(0,0,0,80),shadow.get_rect(),border_radius=max(3,96//12))
        expected.blit(shadow,(34,45));expected.blit(real(view.assets.cards['QH'],(96,134)),(30,40))
        self.assertEqual(cached,self.pixels(expected))
        for width in range(2,130):view.card(queen,0,0,width,84)
        self.assertLessEqual(len(view._card_cache),96)

    def test_panels_share_layer(self):
        view,_=self.make_view()
        canvas=pygame.Surface((500,300));view.surface=canvas;canvas.fill((40,60,50))
        real=pygame.Surface
        with patch('pygame.Surface',side_effect=real) as surface_class:
            view.panel((10,10,200,40));view.panel((10,100,200,40),True);view.panel((250,10,120,27))
            for _ in range(3):view.panel((10,10,200,40))
        self.assertEqual(sorted(call.args[0] for call in surface_class.call_args_list),[(120,27),(200,40)])
        expected=real((500,300));expected.fill((40,60,50))
        for rect,active in (((10,10,200,40),False),((10,100,200,40),True),((250,10,120,27),False),((10,10,200,40),False)):
            rect=pygame.Rect(rect);layer=real(rect.size,pygame.SRCALPHA)
            pygame.draw.rect(layer,(12,23,25,220),layer.get_rect(),border_radius=10);expected.blit(layer,rect)
            pygame.draw.rect(expected,(230,190,72) if active else (144,165,159),rect,3 if active else 1,border_radius=10)
        self.assertEqual(self.pixels(canvas),self.pixels(expected))

    def test_portrait_cached(self):
        canvas=pygame.Surface((400,200));canvas.fill((5,10,15));assets=TableView(canvas)
        roster={npc['id']:npc for npc in load_roster()}
        drawn=dict(roster['big_mike']);rect=pygame.Rect(20,20,64,64)
        real=pygame.transform.smoothscale
        with patch('pygame.transform.smoothscale',side_effect=real) as smooth:
            for _ in range(5):assets.portrait(drawn,rect)
        self.assertEqual(smooth.call_count,1)
        # Same pixels as building the layer, scale and mask every frame.
        expected=pygame.Surface((400,200));expected.fill((5,10,15))
        image=pygame.image.load(paths.resolve(drawn['portrait'])).convert_alpha()
        layer=pygame.Surface(rect.size,pygame.SRCALPHA);pygame.draw.ellipse(layer,(36,65,58),layer.get_rect())
        layer.blit(real(image,rect.size),(0,0))
        mask=pygame.Surface(rect.size,pygame.SRCALPHA);pygame.draw.ellipse(mask,(255,255,255,255),mask.get_rect())
        layer.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT);expected.blit(layer,rect)
        pygame.draw.ellipse(expected,(226,235,220),rect,2)
        self.assertEqual(self.pixels(canvas),self.pixels(expected))
        # A layered NPC is composed once per look; a new look with the same id is rebuilt.
        layered=dict(roster['desmond_doss'])
        with patch('mp_assets.draw_layered_portrait',wraps=mp_assets.draw_layered_portrait) as compose:
            for _ in range(3):assets.portrait(layered,pygame.Rect(200,20,64,64))
            self.assertEqual(compose.call_count,1)
            layered['avatar']={'hair':'hair_02','eyes':'eyes_03'}
            assets.portrait(layered,pygame.Rect(200,20,64,64))
            self.assertEqual(compose.call_count,2)
        for size in range(10,120):assets.portrait(drawn,pygame.Rect(0,0,size,size))
        self.assertLessEqual(len(assets.portraits),96)

    def test_appearance_layers_built_once(self):
        # The table background shade, the oval felt and the human avatars (picture or initial)
        # are drawn on every frame from surfaces built once.
        view,table=self.make_view()
        real_surface,real_font,real_smooth=pygame.Surface,pygame.font.Font,pygame.transform.smoothscale
        with patch('pygame.Surface',side_effect=real_surface) as surfaces,\
                patch('pygame.font.Font',side_effect=real_font) as fonts:
            for _ in range(5):view.draw(table)
        sizes=[tuple(call.args[0]) for call in surfaces.call_args_list if call.args]
        self.assertLessEqual(sizes.count((1366,768)),1,sizes)
        self.assertLessEqual(sizes.count((1030,405)),1,sizes)
        self.assertLessEqual(len([call for call in fonts.call_args_list if call.args==(None,36)]),1)
        # Same pixels as the old per-frame code, for the shade, the felt and a picture avatar.
        appearance=view.appearance
        picture=real_surface((40,30),pygame.SRCALPHA);picture.fill((200,40,90,255))
        pygame.draw.circle(picture,(20,220,60,180),(12,10),8)
        data=io.BytesIO();pygame.image.save(picture,data,'avatar.png')
        public={'avatar':base64.b64encode(data.getvalue()).decode('ascii')}
        rect=pygame.Rect(30,40,64,64);felt=pygame.Rect(174,176,1030,405)
        def frame(target):
            target.fill((50,60,70));appearance.background(target);appearance.felt(target,felt)
            appearance.avatar(target,public,rect,'Ann');appearance.avatar(target,{},rect.move(100,0),'bob')
        canvas=real_surface((1366,768))
        with patch('pygame.transform.smoothscale',side_effect=real_smooth) as smooth:
            for _ in range(4):frame(canvas)
        self.assertEqual([tuple(call.args[1]) for call in smooth.call_args_list],[(64,64)])
        expected=real_surface((1366,768));expected.fill((50,60,70))
        image=appearance.selected('background',expected.get_size())
        if image:expected.blit(image,(0,0))
        else:expected.fill((30,56,47))
        shade=real_surface(expected.get_size(),pygame.SRCALPHA);shade.fill((0,0,0,35));expected.blit(shade,(0,0))
        pygame.draw.ellipse(expected,(109,77,45),felt.inflate(24,24));pygame.draw.ellipse(expected,(143,204,180),felt)
        image=appearance.selected('felt',felt.size)
        if image:
            layer=image.copy();mask=real_surface(felt.size,pygame.SRCALPHA)
            pygame.draw.ellipse(mask,(255,255,255,255),mask.get_rect())
            layer.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT);expected.blit(layer,felt)
        pygame.draw.ellipse(expected,(224,239,220),felt,2)
        pygame.draw.ellipse(expected,(36,65,58),rect)
        layer=real_smooth(appearance.avatars[public['avatar']],rect.size);mask=real_surface(rect.size,pygame.SRCALPHA)
        pygame.draw.ellipse(mask,(255,255,255,255),mask.get_rect());layer.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
        expected.blit(layer,rect);pygame.draw.ellipse(expected,(226,235,220),rect,2)
        other=rect.move(100,0);pygame.draw.ellipse(expected,(36,65,58),other)
        text=real_font(None,36).render('B',True,(249,235,199));expected.blit(text,text.get_rect(center=other.center))
        pygame.draw.ellipse(expected,(226,235,220),other,2)
        self.assertEqual(self.pixels(canvas),self.pixels(expected))
        # Bounded, like the other caches.
        for width in range(10,140):appearance.avatar(canvas,public,pygame.Rect(0,0,width,width))
        self.assertLessEqual(len(appearance._ovals),96)

    def test_countdown_uses_local_timestamp(self):
        view,table=self.make_view()
        table.game.hand_complete=True;table.message['next_hand_seconds']=6
        def shown(now):
            with patch('pygame.time.get_ticks',return_value=now),patch.object(view,'text',wraps=view.text) as text:
                view.draw(table)
            return [call.args[0] for call in text.call_args_list]
        table.countdown_until=10000
        self.assertIn('Next hand in 3 seconds',shown(7600))
        self.assertIn('Next hand in 1 seconds',shown(9001))
        # The guest's clock ends the countdown a moment before the host's new hand arrives:
        # the hand is starting, not waiting for anyone, until the grace time is over.
        self.assertIn('Starting next hand…',shown(10000))
        self.assertIn('Starting next hand…',shown(11999))
        self.assertIn('Waiting for players to rejoin',shown(12000))
        self.assertIn('Waiting for players to rejoin',shown(12500))
        table.hosting=True  # the host's own table knows the hand did not start
        self.assertIn('Waiting for players to rejoin',shown(10000))
        table.hosting=False
        table.countdown_until=None  # no timestamp from the host: the message's seconds, as before
        self.assertIn('Next hand in 6 seconds',shown(7600))
        del table.countdown_until
        table.message['next_hand_seconds']=2
        self.assertIn('Next hand in 2 seconds',shown(7600))
        table.message['next_hand_seconds']=0
        self.assertIn('Waiting for players to rejoin',shown(7600))
        table.message['next_hand_seconds']='abc'  # a malformed message draws, as the default
        self.assertIn('Next hand in 6 seconds',shown(7600))


if __name__=='__main__':unittest.main()
