"""Collection migration, committed rewards, deck legality and UI integration."""
import ast
from collections import Counter
import copy
import json
import os
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
import profile as profiles
from cryptid_collection import (new_collection,normalize_collection,deck_errors,
    award_level_packs,open_pack,save_deck,reward_battle,transaction)
from cryptid_creatures import CryptidBattle,CryptidCatalog
from cryptid_creatures_ui import CryptidScreen
from career_hub_controls import CareerHubControls
from cryptid_creatures_ai import choose_cryptid_action

ROOT=Path(__file__).resolve().parents[1]
TREE=ast.parse((ROOT/'main.py').read_text())


def main_functions(names,env):
    nodes=[n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert len(nodes)==len(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'main orchestration','exec'),env)
    return env


class CollectionTests(unittest.TestCase):
    def setUp(self):self.cards=CryptidCatalog();self.state=new_collection(cards=self.cards)

    def test_new_and_legacy_profiles_have_legal_starters_and_only_welcome_packs(self):
        for level in (1,5,100):
            state=normalize_collection(None,level,self.cards)
            self.assertEqual(state['packs']['creature'],2)
            self.assertEqual(state['rewarded_through_level'],level)
            for d in state['decks']:self.assertEqual(deck_errors(d['cards'],state['owned'],self.cards),[])
            self.assertEqual(award_level_packs(state,level),0)
            self.assertEqual(award_level_packs(state,level+1),2)

    def test_level_grants_are_once_per_crossed_level(self):
        self.assertEqual(award_level_packs(self.state,4),6)
        self.assertEqual(award_level_packs(self.state,4),0)
        self.assertEqual(award_level_packs(self.state,2),0)
        self.assertEqual(self.state['packs']['creature'],8)

    def test_pack_is_awarded_before_reveal_and_resume_cannot_reroll_or_duplicate(self):
        before=Counter(self.state['owned'])
        receipt=open_pack(self.state,self.cards)
        self.assertEqual(self.state['packs']['creature'],1)
        self.assertEqual(Counter(self.state['owned'])-before,Counter(e['id'] for e in receipt['cards']))
        saved=copy.deepcopy(self.state)
        self.assertEqual(open_pack(self.state,self.cards),receipt)
        self.assertEqual(self.state,saved)
        loaded=normalize_collection(json.loads(json.dumps(saved)),1,self.cards)
        self.assertEqual(open_pack(loaded,self.cards),receipt)
        self.assertEqual(loaded['owned'],saved['owned'])

    def test_pack_guarantees_and_all_cards_are_reachable(self):
        self.state['packs']['creature']=1000;seen=set()
        for _ in range(1000):
            receipt=open_pack(self.state,self.cards);ids=[e['id'] for e in receipt['cards']]
            self.assertEqual(len(ids),5)
            self.assertGreaterEqual(sum(self.cards.cards[c]['kind']=='creature' for c in ids),3)
            self.assertTrue(any(self.cards.cards[c]['kind']!='creature' for c in ids))
            self.assertTrue(any(self.cards.cards[c]['rarity']=='Uncommon' for c in ids))
            seen.update(ids);self.state['pending_reveal']=None
        self.assertEqual(seen,set(self.cards.cards))

    def test_new_copy_labels_and_duplicate_counts(self):
        self.state['packs']['creature']=100
        for _ in range(100):
            old=dict(self.state['owned']);receipt=open_pack(self.state,self.cards)
            running=Counter(old)
            for e in receipt['cards']:
                self.assertEqual(e['new'],running[e['id']]==0)
                running[e['id']]+=1;self.assertEqual(e['copies_after'],running[e['id']])
            self.assertEqual(dict(running),self.state['owned'])
            self.state['pending_reveal']=None

    def test_deck_enforces_owned_copies_and_custom_battle_uses_saved_cards(self):
        deck=list(self.state['decks'][1]['cards'])
        save_deck(self.state,0,deck,'My Steel Deck',self.cards)
        b=CryptidBattle(self.cards,player_cards=deck,seed=8)
        side=b.sides[0]
        actual=side.deck+side.hand+[c.card_id for c in side.creatures()]
        self.assertEqual(Counter(actual),Counter(deck))
        self.assertEqual(self.state['active_deck'],0)
        deck[0]='snow_goblin_grene'
        self.assertTrue(deck_errors(deck,self.state['owned'],self.cards))
        with self.assertRaises(ValueError):save_deck(self.state,0,deck,'Illegal',self.cards)
        with self.assertRaises(ValueError):CryptidBattle(self.cards,player_cards=deck[:-1])

    def test_corrupt_collection_is_repaired_without_losing_valid_cards(self):
        value=copy.deepcopy(self.state);value['owned'].update(unknown=9,polven_grene=7)
        value['packs']={'creature':-8};value['active_deck']=500
        value['decks'][1]['cards']=['unknown'];value['pending_reveal']={'cards':[{}]*5}
        repaired=normalize_collection(value,1,self.cards)
        self.assertNotIn('unknown',repaired['owned']);self.assertEqual(repaired['owned']['polven_grene'],7)
        self.assertEqual(repaired['packs']['creature'],0);self.assertIsNone(repaired['pending_reveal'])
        for d in repaired['decks']:self.assertFalse(deck_errors(d['cards'],repaired['owned'],self.cards))

    def test_transaction_rolls_back_on_failed_save_and_retry_is_same_pack(self):
        before=copy.deepcopy(self.state)
        def failed():raise OSError('disk full')
        with self.assertRaises(OSError):transaction(self.state,lambda:open_pack(self.state),failed)
        self.assertEqual(self.state,before)
        self.assertEqual(open_pack(self.state),open_pack(before))

    def test_atomic_profile_save_and_three_slot_isolation(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(profiles,'SAVE_FOLDER',folder):
            for slot in (1,2,3):
                data=profiles.make_default_profile();data['cryptid_creatures']['pack_seed']=slot
                data['cryptid_creatures']['packs']['creature']=slot
                if slot==1:open_pack(data['cryptid_creatures'])
                profiles.save_profile(data,slot)
            for slot in (1,2,3):
                data=profiles.load_profile(slot)
                self.assertEqual(data['profile_version'],8)
                self.assertEqual(data['cryptid_creatures']['pack_seed'],slot)
                self.assertEqual(data['cryptid_creatures']['packs']['creature'],0 if slot==1 else slot)
            original=Path(profiles.get_profile_path(1)).read_bytes()
            data=profiles.load_profile(1);data['cryptid_creatures']['packs']['creature']=99
            with patch.object(profiles.os,'replace',side_effect=OSError('locked')):
                with self.assertRaises(OSError):profiles.save_profile(data,1)
            self.assertEqual(Path(profiles.get_profile_path(1)).read_bytes(),original)
            self.assertFalse(list(Path(folder).glob('*.tmp')))

    def test_real_xp_path_grants_and_displays_packs_on_each_level(self):
        env=main_functions({'add_player_xp','get_level_from_xp','get_next_level_xp'},
            dict(player_xp=0,player_level=1,player_xp_to_next=100,
                 LEVEL_XP_THRESHOLDS={1:0,2:100,3:200},cryptid_collection_state=self.state,
                 unlock_rewards_for_level=lambda level:[]))
        result=env['add_player_xp'](250)
        self.assertEqual(self.state['packs']['creature'],6)
        self.assertEqual([s['unlocks'] for s in result['level_up_screens']],[[('cryptid_pack','2')],[('cryptid_pack','2')]])
        env['add_player_xp'](0);self.assertEqual(self.state['packs']['creature'],6)

    def test_real_reward_path_once_only_and_save_failure_restores_xp_cosmetics_and_packs(self):
        state=self.state;state['battle_serial']=1
        def save():return None
        env=dict(copy=copy,cryptid_collection_state=state,reward_battle=reward_battle,
                 player_xp=0,player_level=1,player_xp_to_next=100,level_up_queue=[],auto_save_career=save,
                 LEVEL_XP_THRESHOLDS={1:0,2:100,3:200},unlocked_titles={'default'},
                 unlock_rewards_for_level=lambda level:[])
        main_functions({'settle_career_cryptid','add_player_xp','get_level_from_xp','get_next_level_xp'},env)
        def unlock(level):env['unlocked_titles'].add('reward');return [('title','reward')]
        env['unlock_rewards_for_level']=unlock
        before=copy.deepcopy(state)
        def failed():raise OSError('disk full')
        env['auto_save_career']=failed
        with self.assertRaises(OSError):env['settle_career_cryptid'](1,0)
        self.assertEqual(state,before);self.assertEqual(env['player_xp'],0)
        self.assertEqual(env['unlocked_titles'],{'default'});self.assertEqual(env['level_up_queue'],[])
        env['auto_save_career']=save
        self.assertEqual(env['settle_career_cryptid'](1,0),{'xp':120,'packs':1})
        self.assertEqual(state['packs']['creature'],5)
        self.assertIsNone(env['settle_career_cryptid'](1,0));self.assertEqual(env['player_xp'],120)

    def test_loss_draw_and_invalid_battle_serial_do_not_grant_win_packs(self):
        self.state['battle_serial']=2
        self.assertIsNone(reward_battle(self.state,3,0))
        self.assertEqual(reward_battle(self.state,1,1),{'xp':55,'packs':0})
        self.assertEqual(reward_battle(self.state,2,2),{'xp':70,'packs':0})
        self.assertEqual(self.state['packs']['creature'],2)
        self.assertEqual(self.state['matches'],2)
        self.assertEqual(self.state['draws'],1)


class CollectionUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):pygame.init();pygame.display.set_mode((1366,768))
    @classmethod
    def tearDownClass(cls):pygame.quit()
    def screen(self,persist=None,result=None):
        s=CryptidScreen();s.enter_career([],new_collection(),persist,result);return s

    def test_all_collection_pages_fit_and_toolbar_does_not_overlap_exit(self):
        s=self.screen();out=pygame.Surface((1366,768));bounds=out.get_rect()
        for page in ('career_home','collection','builder','packs'):
            s.collection_view.navigate(page);s.draw(out)
            self.assertTrue(all(bounds.contains(r) for r,_ in s.buttons))
            self.assertTrue(all(bounds.contains(r) for r,*_ in s.cards_on_screen))
        controls=CareerHubControls()
        self.assertTrue(all(r.right<=1165 for r in controls.toolbar_rects.values()))
        self.assertEqual(controls.get_action(controls.toolbar_rects['cryptid'].center),'cryptid')

    def test_opening_is_saved_then_revealed_and_resumes_after_profile_load(self):
        commits=[];s=self.screen(persist=lambda:commits.append(copy.deepcopy(s.collection)))
        view=s.collection_view;view.command(('cc_open',))
        self.assertEqual(s.page,'pack_open');self.assertEqual(len(commits),1)
        self.assertEqual(commits[0]['packs']['creature'],1)
        self.assertEqual(view.revealed,0)
        s.update(100);s.update(1100);self.assertGreater(view.revealed,0)
        receipt=copy.deepcopy(s.collection['pending_reveal'])
        resumed=CryptidScreen();resumed.enter_career([],normalize_collection(commits[0]))
        resumed.collection_view.command(('cc_open',))
        self.assertEqual(resumed.collection['pending_reveal'],receipt)
        resumed.collection_view.command(('cc_reveal_all',));resumed.draw(pygame.Surface((1366,768)))
        resumed.collection_view.command(('cc_done',))
        self.assertIsNone(resumed.collection['pending_reveal'])

    def test_pack_and_deck_save_failures_leave_live_inventory_unchanged(self):
        def failed():raise OSError('read only')
        s=self.screen(failed);before=copy.deepcopy(s.collection)
        s.collection_view.command(('cc_open',));self.assertEqual(s.collection,before)
        self.assertEqual(s.page,'career_home');self.assertIn('Could not save',s.collection_view.message)
        s.collection_view.navigate('builder');s.collection_view.slot=1
        s.collection_view.draft=list(s.collection['decks'][1]['cards'])
        s.collection_view.command(('cc_save',));self.assertEqual(s.collection,before)

    def test_search_builder_and_saved_deck_are_playable(self):
        s=self.screen();view=s.collection_view;view.navigate('builder')
        for char in 'bortle':s.handle_event(pygame.event.Event(pygame.KEYDOWN,key=ord(char),unicode=char))
        self.assertEqual(view.ids(),['bortle_grene'])
        cid=view.draft[0];view.command(('cc_remove',cid));self.assertEqual(len(view.draft),29)
        view.command(('cc_add',cid));view.command(('cc_save',));self.assertEqual(len(view.draft),30)
        expected=Counter(view.draft);s.start_battle(4)
        side=s.battle.sides[0]
        self.assertEqual(Counter(side.deck+side.hand+[c.card_id for c in side.creatures()]),expected)

    def test_free_play_detaches_collection_and_awards_no_career_result(self):
        called=[];s=self.screen(result=lambda *args:called.append(args));state=copy.deepcopy(s.collection)
        s.enter([]);s.start_battle(4);s.battle.winner=0;s.update(100000)
        self.assertFalse(s.career_mode);self.assertIsNone(s.collection);self.assertEqual(called,[])
        self.assertEqual(state['packs']['creature'],2)

    def test_escaping_finished_battle_claims_rewards_before_leaving(self):
        calls=[]
        s=self.screen(result=lambda *args:calls.append(args) or {'xp':120,'packs':1})
        s.start_battle(4);s.battle.winner=0;s.feedback.active=True
        s.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
        self.assertEqual(s.page,'career_home');self.assertEqual(calls,[(1,0)])
        s.claim_result();self.assertEqual(len(calls),1)

    def test_actual_career_entry_exit_and_save_failure_stay_on_same_screen(self):
        screen=self.screen()
        state=screen.collection
        env=main_functions({'start_career_cryptid','leave_career_cryptid'},dict(
            cryptid_screen=screen,cryptid_collection_state=state,NPCS=[],
            auto_save_career=lambda:None,settle_career_cryptid=lambda *args:None,
            STATE_CRYPTID_CREATURES='cryptid',STATE_CAREER_HUB='hub',current_state='hub',current_game_mode='free'))
        env['start_career_cryptid']()
        self.assertEqual(env['current_state'],'cryptid');self.assertEqual(env['current_game_mode'],'career')
        self.assertIs(screen.collection,state)
        def failed():raise OSError('locked')
        env['auto_save_career']=failed
        self.assertFalse(env['leave_career_cryptid']());self.assertEqual(env['current_state'],'cryptid')
        env['auto_save_career']=lambda:None
        self.assertTrue(env['leave_career_cryptid']());self.assertEqual(env['current_state'],'hub')

    def test_eight_level_up_rewards_fit_above_xp_and_continue_button(self):
        out=pygame.Surface((1366,768));font=pygame.font.Font(None,25)
        env=main_functions({'draw_level_up_screen'},dict(
            pygame=pygame,game_surface=out,BASE_WIDTH=1366,
            current_level_up_data={'level':5,'unlocks':[('cryptid_pack','2')]*8},
            menu_title_font=font,options_title_font=font,difficulty_detail_font=font,
            option_value_font=font,option_label_font=font,player_xp_to_next=1000,
            player_xp=850,player_name='Player',level_up_continue_rect=pygame.Rect(533,690,300,50),
            get_unlock_asset_data=lambda *args:({'name':'2 Creature Card Packs'},None,'Cryptid Creatures'),
            draw_button=lambda *args,**kwargs:None))
        original=pygame.draw.rect;panels=[]
        def record(surface,color,rect,*args,**kwargs):
            if color==(245,245,245):panels.append(pygame.Rect(rect))
            return original(surface,color,rect,*args,**kwargs)
        with patch.object(pygame.draw,'rect',side_effect=record):env['draw_level_up_screen']()
        self.assertEqual(len(panels),8)
        self.assertTrue(all(rect.bottom<=595 for rect in panels))
        self.assertFalse(any(a.colliderect(b) for i,a in enumerate(panels) for b in panels[i+1:]))

    def test_pack_inspector_pauses_reveal_and_click_controls_complete_opening(self):
        s=self.screen();out=pygame.Surface((1366,768))
        s.collection_view.navigate('packs');s.draw(out)
        rect=next(r for r,c in s.buttons if c==('cc_open',))
        s.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1),rect.center)
        self.assertEqual(s.page,'pack_open');s.update(0);s.update(1100);s.draw(out)
        card=next(r for r,*_ in s.cards_on_screen)
        s.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1),card.center)
        self.assertIsNotNone(s.inspection)
        clock=s.collection_view.clock;s.update(30000);self.assertEqual(s.collection_view.clock,clock)
        s.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
        s.update(30016);self.assertEqual(s.collection_view.clock,clock+16)
        s.collection_view.command(('cc_reveal_all',));s.draw(out)
        done=next(r for r,c in s.buttons if c==('cc_done',))
        s.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1),done.center)
        self.assertEqual(s.page,'packs');self.assertIsNone(s.collection['pending_reveal'])

    def test_failed_result_save_is_throttled_and_cannot_be_discarded_on_escape(self):
        calls=[]
        def failed(*args):calls.append(args);raise OSError('locked')
        s=self.screen(result=failed);s.start_battle(3);s.battle.winner=0
        for _ in range(20):self.assertFalse(s.claim_result())
        self.assertEqual(len(calls),1)
        s.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
        self.assertEqual(s.page,'battle')
        s.feedback_now+=1501;self.assertFalse(s.claim_result());self.assertEqual(len(calls),2)

    def test_full_career_flow_opens_pack_plays_equipped_deck_and_persists_rewards(self):
        s=CryptidScreen();state=new_collection()
        with tempfile.TemporaryDirectory() as folder,patch.object(profiles,'SAVE_FOLDER',folder):
            env=dict(cryptid_screen=s,cryptid_collection_state=state,NPCS=[],copy=copy,
                     player_xp=0,player_level=1,player_xp_to_next=100,level_up_queue=[],
                     LEVEL_XP_THRESHOLDS={1:0,2:100,3:200},unlock_rewards_for_level=lambda level:[],
                     reward_battle=reward_battle,guest_mode=False,current_profile_slot=1,
                     save_profile=profiles.save_profile,STATE_CRYPTID_CREATURES='cryptid',
                     STATE_CAREER_HUB='hub',current_state='hub',current_game_mode='career')
            def build():
                p=profiles.make_default_profile();p['identity']['name']='Test Player'
                p['career'].update(cash=23549,fans=420)
                p['progression'].update(xp=env['player_xp'],level=env['player_level'])
                p['cryptid_creatures']=copy.deepcopy(state)
                return p
            env['build_profile_save_data']=build
            main_functions({'start_career_cryptid','leave_career_cryptid','settle_career_cryptid',
                            'auto_save_career','add_player_xp','get_level_from_xp','get_next_level_xp'},env)
            env['start_career_cryptid']()
            s.collection_view.command(('cc_open',));s.collection_view.command(('cc_reveal_all',));s.collection_view.command(('cc_done',))
            self.assertEqual(profiles.load_profile(1)['cryptid_creatures']['packs_opened'],1)
            s.start_battle(13);now=s._last_update;rng=random.Random(44)
            for _ in range(3000):
                now+=1500;s.update(now)
                if s.result_claimed:break
                if s.battle.turn==0 and not s.feedback.active:
                    s._act(choose_cryptid_action(s.battle,seat=0,rng=rng))
            self.assertTrue(s.result_claimed);self.assertEqual(state['matches'],1)
            self.assertTrue(env['leave_career_cryptid']());self.assertEqual(env['current_state'],'hub')
            loaded=profiles.load_profile(1)
            self.assertEqual(loaded['cryptid_creatures'],state)
            self.assertEqual(loaded['identity']['name'],'Test Player')
            self.assertEqual(loaded['career']['cash'],23549);self.assertEqual(loaded['career']['fans'],420)
            self.assertEqual(loaded['progression']['xp'],120 if s.battle.winner==0 else 70 if s.battle.winner==2 else 55)


if __name__=='__main__':unittest.main()
