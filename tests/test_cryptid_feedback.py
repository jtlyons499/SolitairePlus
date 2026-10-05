"""Visible resolution, presentation locks, safe sound and encounter input."""
import copy
import os
import random
import unittest
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
from cryptid_battle_feedback import BattleFeedback, BattleSounds, snapshot
from cryptid_creatures import Action, CryptidBattle
from cryptid_creatures_ui import CryptidScreen
from cryptid_encounter_view import ACTIVE_RECTS
from cryptid_creatures_ai import choose_cryptid_action


class FeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init();pygame.display.set_mode((1366,768))

    @classmethod
    def tearDownClass(cls):pygame.quit()

    def screen(self):
        s=CryptidScreen();s.enter();s.start_battle(3);return s

    def test_armor_ticks_between_old_and_actual_value_without_mutating_rules(self):
        s=self.screen();s.auto_end=False
        before=s.battle.sides[1].active.ap
        action=next(a for a in s.battle.legal_actions() if a.kind=='move')
        s._act(action);actual=s.battle.sides[1].active.ap
        start=s.feedback.started
        self.assertLess(actual,before)
        self.assertEqual(s.feedback.visual_sides(s.battle,start)[1].active.ap,before)
        halfway=s.feedback.visual_sides(s.battle,start+440)[1].active.ap
        self.assertGreater(halfway,actual);self.assertLess(halfway,before)
        self.assertEqual(s.feedback.visual_sides(s.battle,start+700)[1].active.ap,actual)
        self.assertEqual(s.battle.sides[1].active.ap,actual)

    def test_second_move_and_end_turn_are_locked_during_resolution(self):
        s=self.screen();move=next(a for a in s.battle.legal_actions() if a.kind=='move')
        s._act(move);before=copy.deepcopy(s.battle.public_snapshot())
        s._act(Action('end'))
        s.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_SPACE))
        self.assertEqual(before,s.battle.public_snapshot())
        out=pygame.Surface((1366,768));s.draw(out)
        self.assertFalse(any(c[0] in ('act','actions','auto_end') for _,c in s.buttons))

    def test_leaving_during_animation_allows_keyboard_rematch(self):
        s=self.screen();s._act(next(a for a in s.battle.legal_actions() if a.kind=='move'))
        s.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
        self.assertEqual(s.page,'menu');self.assertFalse(s.feedback.active)
        s.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN))
        self.assertEqual(s.page,'battle');self.assertEqual(s.battle.turn_number,1)

    def test_modal_pauses_clock_without_skipping_ticks_when_closed(self):
        s=self.screen();s._act(next(a for a in s.battle.legal_actions() if a.kind=='move'))
        wall=s._last_update;s.update(wall+300);elapsed=s.feedback.elapsed(s.feedback_now)
        s.damage_open=True;s.update(wall+30000)
        self.assertEqual(s.feedback.elapsed(s.feedback_now),elapsed)
        s.damage_open=False;s.update(wall+30016)
        self.assertEqual(s.feedback.elapsed(s.feedback_now),elapsed+16)

    def test_knockout_card_survives_visually_until_its_sequence_finishes(self):
        s=self.screen();s.auto_end=False
        enemy=s.battle.sides[1].active;enemy.hp=1;enemy.ap=0
        s._act(next(a for a in s.battle.legal_actions() if a.kind=='move'))
        self.assertIsNone(s.battle.sides[1].active)
        old=s.feedback.visual_sides(s.battle,s.feedback.started)[1].active
        self.assertEqual(old.uid,enemy.uid);self.assertEqual(old.hp,1)
        zero=s.feedback.visual_sides(s.battle,s.feedback.started+700)[1].active
        self.assertEqual(zero.hp,0)
        s.update(s._last_update+s.feedback.duration+1)
        self.assertIsNone(s.feedback.visual_sides(s.battle,s.feedback_now)[1].active)

    def test_healing_and_switching_have_distinct_feedback(self):
        s=self.screen();side=s.battle.sides[0];side.active.hp-=20
        side.hand=['support_salve'];side.focus=6
        s._act(Action('play',0,0))
        self.assertEqual(s.feedback.kind,'support')
        self.assertTrue(any(h>0 for _,h,_ in s.feedback.changes))
        s.update(s._last_update+s.feedback.duration+1)
        old=side.active.uid;s._act(Action('switch',0))
        self.assertEqual(s.feedback.kind,'switch')
        self.assertEqual(s.feedback.visual_sides(s.battle,s.feedback.started)[0].active.uid,old)
        self.assertNotEqual(s.feedback.visual_sides(s.battle,s.feedback.started+300)[0].active.uid,old)

    def test_eleventh_hand_card_is_reachable_on_second_page(self):
        s=self.screen();side=s.battle.sides[0]
        side.hand=['support_salve']*11
        s.hand_page=1;s.draw(pygame.Surface((1366,768)))
        tags=[tag for _,_,_,tag in s.cards_on_screen if isinstance(tag,tuple) and tag[0]=='hand']
        self.assertEqual(tags,[('hand',8),('hand',9),('hand',10)])
        rect=next(r for r,_,_,tag in s.cards_on_screen if tag==('hand',10))
        s.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1),rect.center)
        self.assertEqual(len(side.hand),10)

    def test_effect_frames_and_sounds_render_with_original_frame(self):
        s=self.screen();s._act(next(a for a in s.battle.legal_actions() if a.kind=='move'))
        out=pygame.Surface((1366,768))
        for elapsed in (0,160,300,440,700):
            s.feedback_now=s.feedback.started+elapsed;s.draw(out)
            self.assertTrue(all(out.get_rect().contains(rect) for rect in ACTIVE_RECTS.values()))
        sounds=BattleSounds()
        for key in ('attack_slam','attack_slash','attack_air','attack_munition','attack_ethereal','attack_elemental','attack_corruption','heal','shield','switch','arena','knockout'):
            sounds.play(key)
            self.assertGreater(sounds.cache[key].get_length(),0)

    def test_all_starters_finish_through_animated_controller(self):
        for deck in range(3):
            s=self.screen();s.deck_index=deck;s.start_battle(20+deck)
            now=s._last_update;rng=random.Random(4)
            for step in range(3000):
                now+=1500;s.update(now)
                if s.battle.winner is not None and not s.feedback.active:break
                if s.battle.turn==0 and not s.feedback.active:
                    action=choose_cryptid_action(s.battle,seat=0,rng=rng)
                    self.assertIsNotNone(action)
                    s._act(action)
                if step%100==0:s.draw(pygame.Surface((1366,768)))
            self.assertIsNotNone(s.battle.winner)
            self.assertFalse(s.feedback.active)


if __name__=='__main__':unittest.main()
