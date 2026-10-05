"""Rules, hidden-information boundary, Free Play integration and artist assets."""
import ast
from collections import Counter
import copy
import json
import os
from pathlib import Path
import random
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import pygame

from cryptid_creatures import (Action, Creature, CryptidBattle, CryptidCatalog,
                               HAND_LIMIT, damage_values)
from cryptid_creatures_ai import choose_cryptid_action
from cryptid_cards import ART_RECT, CryptidCardRenderer
from cryptid_creatures_ui import CryptidScreen

ROOT=Path(__file__).resolve().parents[1]


class CryptidRulesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=CryptidCatalog()

    def battle(self,seed=4):
        return CryptidBattle(self.catalog,seed=seed)

    def test_complete_catalog_and_valid_starters(self):
        self.assertEqual(len(self.catalog.cards),60)
        self.assertEqual(sum(c["kind"]=="creature" for c in self.catalog.cards.values()),45)
        self.assertEqual(len(self.catalog.moves),83)
        for card in self.catalog.cards.values():
            self.assertTrue(card["description"])
        for deck in self.catalog.decks.values():
            self.assertEqual(len(deck["cards"]),30)
            self.assertEqual(sum(self.catalog.cards[c]["kind"]=="creature" for c in deck["cards"]),8)
            self.assertLessEqual(max(Counter(deck["cards"]).values()),2)

    def test_user_armor_examples_and_health_branch(self):
        attacker=Creature("test",1,100,0,{})
        own={"attack_style":"Slam"}
        enemy={"defense_style":"Brute"}
        for ap,hp,attack_ap,attack_hp,expected in [(70,100,50,30,(50,0)),(0,60,30,20,(0,20)),(40,100,50,30,(40,10))]:
            defender=Creature("test",2,hp,ap,{})
            move=dict(id="example",style="Air",ap_damage=attack_ap,hp_damage=attack_hp)
            self.assertEqual(damage_values(move,attacker,defender,own,enemy),expected)

    def test_zero_armor_damage_does_not_bypass_live_armor(self):
        attacker=Creature("a",1,100,0,{})
        defender=Creature("b",2,100,1,{})
        move=dict(id="end",style="Air",ap_damage=0,hp_damage=100)
        self.assertEqual(damage_values(move,attacker,defender,{"attack_style":"Slam"},{"defense_style":"Brute"}),(0,0))

    def test_modifier_cap_and_opposing_conditions(self):
        a=Creature("a",1,100,0,{},conditions={"sharpened":2})
        d=Creature("d",2,100,0,{})
        move=dict(id="example",style="Slam",ap_damage=30,hp_damage=30)
        arena=dict(styles=["Slam"],factor=2,duration=5,scope="all",owner=0)
        self.assertEqual(damage_values(move,a,d,{"attack_style":"Slam"},{"defense_style":"Shield"},arena),(0,60))
        d.conditions["steeled"]=2
        self.assertEqual(damage_values(move,a,d,{"attack_style":"Air"},{"defense_style":"Shield"}),(0,30))

    def test_repairs_respect_printed_maximum_and_do_not_remove_extra_armor(self):
        b=self.battle()
        c=b.sides[0].active
        card=b.card(c.card_id)
        c.hp=card["hp"]-1;c.ap=card["ap"]-2
        b._effects(0,{"heal_hp":50,"heal_ap":50})
        self.assertEqual((c.hp,c.ap),(card["hp"],card["ap"]))
        b._effects(0,{"barrier_ap":80})
        self.assertEqual(c.ap,card["ap"]+30)
        b._effects(0,{"heal_ap":30})
        self.assertEqual(c.ap,card["ap"]+30)

    def test_switch_cannot_grant_a_second_move_and_costs_focus(self):
        b=self.battle()
        s=b.sides[0]
        s.focus=6
        action=next(a for a in b.legal_actions() if a.kind=="move")
        self.assertTrue(b.act(action))
        before=s.focus
        self.assertTrue(b.act(Action("switch",0)))
        self.assertEqual(s.focus,before-1)
        self.assertFalse(any(a.kind in ("move","struggle") for a in b.legal_actions()))
        self.assertFalse(b.act(Action("switch",0)))

    def test_rearm_caps_limited_charges_and_keeps_unlimited_moves(self):
        b=self.battle()
        c=b.make_creature("sea_scorpion_grene");b.sides[0].active=c
        c.uses["precision_pierce"]=0
        b._effects(0,{"rearm":5})
        self.assertEqual(c.uses["precision_pierce"],2)
        self.assertIsNone(c.uses["claw"])

    def test_exhausted_moves_have_legal_struggle(self):
        b=self.battle()
        c=b.sides[0].active
        for mid in c.uses:c.uses[mid]=0
        self.assertIn(Action("struggle"),b.legal_actions())
        hp=c.hp
        self.assertTrue(b.act(Action("struggle")))
        self.assertEqual(c.hp,hp-3)

    def test_guard_refresh_and_reflection_resolve_once(self):
        b=self.battle()
        a=b.make_creature("bortle_grene");d=b.make_creature("bortle_grene")
        b.sides[0].active=a;b.sides[1].active=d
        a.ap=d.ap=0
        b._effects(1,{"guard":.5,"reflect":True})
        b._effects(1,{"guard":.5,"reflect":True})
        a.guard={"guard":.5,"reflect":True}
        before=a.hp,d.hp
        b._attack(0,b.catalog.moves["punch"])
        lost=before[1]-d.hp
        self.assertGreater(lost,0)
        self.assertEqual(before[0]-a.hp,lost)
        self.assertFalse(d.guard)
        self.assertTrue(a.guard)

    def test_hand_overflow_requires_discard_and_ko_requires_promotion(self):
        b=self.battle()
        b.sides[0].hand=["support_salve"]*(HAND_LIMIT+1)
        self.assertTrue(all(a.kind=="discard" for a in b.legal_actions()))
        self.assertTrue(b.act(Action("discard",0)))
        b.sides[0].active.hp=0;b._resolve_knockouts()
        self.assertEqual(b.sides[1].knockouts,1)
        self.assertTrue(all(a.kind=="promote" for a in b.legal_actions()))
        self.assertTrue(b.act(Action("promote",0,1)))
        self.assertIsNotNone(b.sides[0].active)

    def test_stun_can_skip_only_one_turn_and_sickness_bypasses_armor(self):
        b=self.battle()
        b.sides[1].active.conditions={"stunned":2,"sick":3}
        before_hp=b.sides[1].active.hp;before_ap=b.sides[1].active.ap
        self.assertTrue(b.act(Action("end")))
        self.assertNotIn("stunned",b.sides[1].active.conditions)
        self.assertLess(b.sides[1].active.hp,before_hp)
        self.assertEqual(b.sides[1].active.ap,before_ap)

    def test_arena_replacement_and_expiry(self):
        b=self.battle()
        rust=b.catalog.moves["rust"]["effects"]
        skies=b.catalog.moves["clear_skies"]["effects"]
        b._effects(0,rust);b._effects(1,skies)
        self.assertEqual(b.arena["styles"],["Air"])
        b.arena["duration"]=1
        b.act(Action("end"))
        self.assertIsNone(b.arena)

    def test_knockout_and_simultaneous_draw(self):
        b=self.battle()
        b.sides[0].knockouts=b.sides[1].knockouts=2
        b.sides[0].active.hp=b.sides[1].active.hp=0
        b._resolve_knockouts()
        self.assertEqual(b.winner,2)
        self.assertEqual(b.legal_actions(),[])

    def test_public_snapshot_has_no_hidden_cards_or_mutable_aliases(self):
        b=self.battle()
        snapshot=b.public_snapshot()
        for side in snapshot["sides"]:
            self.assertNotIn("hand",side);self.assertNotIn("deck",side)
        snapshot["sides"][0]["active"]["hp"]=0
        self.assertGreater(b.sides[0].active.hp,0)

    def test_ai_cannot_read_opponent_hand_or_deck_and_does_not_mutate(self):
        b=self.battle();b.act(Action("end"))
        before=copy.deepcopy((b.sides,b._next_uid,b.arena,list(b.log)))
        expected=choose_cryptid_action(b,rng=random.Random(3))
        self.assertEqual(before,(b.sides,b._next_uid,b.arena,list(b.log)))
        b.sides[0].hand=["fortress_polis"]*len(b.sides[0].hand)
        b.sides[0].deck=["polven_grene"]*len(b.sides[0].deck)
        self.assertEqual(choose_cryptid_action(b,rng=random.Random(3)),expected)

    def test_random_and_ai_matches_finish_without_lost_cards_or_illegal_stats(self):
        data_before=json.dumps(self.catalog.cards,sort_keys=True)+json.dumps(self.catalog.moves,sort_keys=True)
        keys=list(self.catalog.decks)
        for seed in range(150):
            b=CryptidBattle(self.catalog,keys[seed%3],keys[(seed//3)%3],seed)
            rng=random.Random(seed+500)
            for step in range(2000):
                for s in b.sides:
                    self.assertEqual(len(s.deck)+len(s.hand)+len(s.discard)+len(s.creatures()),30)
                    self.assertTrue(0<=s.focus<=6)
                    self.assertLessEqual(len(s.docket),3)
                    for c in s.creatures():
                        card=b.card(c.card_id)
                        self.assertTrue(0<c.hp<=card["hp"])
                        self.assertTrue(0<=c.ap<=card["ap"]+30)
                        self.assertTrue(all(n is None or 0<=n<=self.catalog.moves[mid]["uses"] for mid,n in c.uses.items()))
                if b.winner is not None:break
                a=(rng.choice(b.legal_actions()) if seed%3==0
                   else choose_cryptid_action(b,rng=rng,seat=b.turn))
                self.assertTrue(b.act(a))
            else:self.fail(f"Match stalled: seed={seed}, turn={b.turn_number}")
        self.assertEqual(data_before,json.dumps(self.catalog.cards,sort_keys=True)+json.dumps(self.catalog.moves,sort_keys=True))


class CryptidUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init();pygame.display.set_mode((1366,768))
        cls.catalog=CryptidCatalog()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def screen(self):
        screen=CryptidScreen(self.catalog)
        screen.enter([{"id":"rival","name":"Rival"}])
        return screen

    def test_original_artist_asset_dimensions_and_transparency(self):
        frame=pygame.image.load(str(ROOT/"assets/cryptid_creatures/card_frame.png"))
        panel=pygame.image.load(str(ROOT/"assets/cryptid_creatures/move_panel.png"))
        self.assertEqual(frame.get_size(),(900,1260))
        self.assertEqual(panel.get_size(),(800,96))
        self.assertEqual(frame.get_at((450,300)).a,0)
        self.assertEqual(frame.get_at((450,850)).a,255)
        self.assertEqual(panel.get_at((0,0)).a,0)
        self.assertEqual(panel.get_at((400,48)).a,255)

    def test_every_card_renders_at_native_inspector_and_hand_sizes(self):
        renderer=CryptidCardRenderer(self.catalog);renderer.refresh()
        for cid in self.catalog.cards:
            face=renderer.render(cid,(180,252))
            self.assertEqual(face.get_size(),(180,252))
        face=renderer.render("sea_scorpion_grene",(410,574))
        self.assertEqual(face.get_at((0,0)).a,0)
        self.assertGreaterEqual(face.get_at((205,130)).a,250)
        self.assertIs(renderer.render("sea_scorpion_grene",(410,574)),face)

    def test_custom_square_art_is_not_cropped_and_can_refresh(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/"creatures").mkdir()
            image=pygame.Surface((768,768),pygame.SRCALPHA);image.fill((240,20,60,255))
            pygame.draw.rect(image,(20,60,240),(0,0,128,768))
            pygame.draw.rect(image,(240,200,20),(640,0,128,768))
            pygame.image.save(image,str(root/"creatures/sea_scorpion_grene.png"))
            renderer=CryptidCardRenderer(self.catalog,root);renderer.refresh()
            first=renderer.render("sea_scorpion_grene",(900,1260))
            self.assertTrue(all(abs(a-b)<=3 for a,b in zip(first.get_at(ART_RECT.center)[:3],(240,20,60))))
            self.assertTrue(all(abs(a-b)<=3 for a,b in zip(first.get_at((250,392))[:3],(20,60,240))))
            self.assertTrue(all(abs(a-b)<=3 for a,b in zip(first.get_at((650,392))[:3],(240,200,20))))
            image.fill((10,220,70,255));pygame.image.save(image,str(root/"creatures/sea_scorpion_grene.png"))
            renderer.refresh()
            self.assertTrue(all(abs(a-b)<=3 for a,b in zip(renderer.render("sea_scorpion_grene",(900,1260)).get_at(ART_RECT.center)[:3],(10,220,70))))

    def test_visible_buttons_fit_internal_resolution_and_no_game_button_overlaps_active_card(self):
        screen=self.screen();surface=pygame.Surface((1366,768));bounds=surface.get_rect()
        for page in ("menu","library","battle"):
            if page=="battle":screen.start_battle(5)
            else:screen.page=page
            screen.draw(surface)
            for rect,command in screen.buttons:self.assertTrue(bounds.contains(rect),command)
            for rect,*_ in screen.cards_on_screen:self.assertTrue(bounds.contains(rect))
            if page=="battle":
                active=next(rect for rect,cid,c,tag in screen.cards_on_screen if tag==("active",0))
                self.assertFalse(any(active.colliderect(rect) for rect,command in screen.buttons))

    def test_space_cannot_skip_npc_turn_and_inspector_pauses_ai(self):
        screen=self.screen();screen.start_battle(5)
        screen.battle.act(Action("end"))
        before=copy.deepcopy((screen.battle.turn,screen.battle.turn_number,screen.battle.sides))
        screen.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_SPACE))
        self.assertEqual(before,(screen.battle.turn,screen.battle.turn_number,screen.battle.sides))
        screen.inspect(screen.battle.sides[0].active.card_id)
        screen.update(999999)
        self.assertEqual(before,(screen.battle.turn,screen.battle.turn_number,screen.battle.sides))

    def test_catalog_inspector_and_target_picker_controls(self):
        screen=self.screen();surface=pygame.Surface((1366,768))
        screen.page="library";screen.draw(surface)
        screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1),screen.cards_on_screen[0][0].center)
        self.assertIsNotNone(screen.inspection)
        screen.draw(surface)
        screen.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
        self.assertIsNone(screen.inspection)
        screen.start_battle(5)
        s=screen.battle.sides[0];s.hand=["support_salve"];s.focus=6
        actions=[a for a in screen.battle.legal_actions(0) if a.kind=="play"]
        self.assertEqual(len(actions),2)
        screen._choose_actions(actions)
        screen.draw(surface)
        target_button=next(rect for rect,command in screen.buttons if command[0]=="act" and command[1].target==1)
        screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1),target_button.center)
        self.assertFalse(screen.targets)
        self.assertEqual(s.hand,[])

    def test_production_free_play_path_restores_actual_career_snapshot(self):
        tree=ast.parse((ROOT/"main.py").read_text())
        names={"start_free_play_game","begin_free_play_sandbox","finish_free_play_sandbox","leave_free_play_game"}
        nodes=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
        career=dict(career_rating=1234,career_ratings={"solitaire":1345,"overall":1234},career_cash=91234,
                    career_fans=600,career_fan_news_milestones={100,500},career_news_items=[{"headline":"original"}],
                    career_rounds_won=17,career_challenges_won=4,career_total_moves=5050,
                    career_event_result_log=[{"game":"solitaire"}],career_event_has_activity=False)
        screen=self.screen()
        env=dict(career,copy=copy,free_play_snapshot=None,FREE_PLAY_STARTING_CASH=5000,
                 current_game_mode="career",current_state="menu",career_event_entry=None,
                 free_play_achievement_fans_earned=0,cryptid_screen=screen,NPCS=screen.npcs,
                 STATE_CRYPTID_CREATURES="cryptid_creatures",STATE_FREE_PLAY_SELECT="free_play_select")
        original=copy.deepcopy(career)
        exec(compile(ast.Module(body=nodes,type_ignores=[]),"production Free Play","exec"),env)
        self.assertTrue(env["start_free_play_game"]("cryptid_creatures"))
        self.assertEqual(env["current_state"],"cryptid_creatures")
        self.assertEqual(env["career_cash"],original["career_cash"])
        screen.start_battle(3)
        rng=random.Random(5)
        for _ in range(2000):
            if screen.battle.winner is not None:break
            action=choose_cryptid_action(screen.battle,rng=rng,seat=screen.battle.turn)
            screen.battle.act(action)
        self.assertIsNotNone(screen.battle.winner)
        self.assertTrue(env["leave_free_play_game"]())
        self.assertEqual(env["current_state"],"free_play_select")
        self.assertEqual({key:env[key] for key in original},original)


if __name__=="__main__":
    unittest.main()
