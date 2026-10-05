"""Damage explanations must agree with resolution; fast controls preserve choice."""
import random
import unittest
import pygame
from cryptid_creatures import Action, CryptidBattle, damage_breakdown, damage_values
from cryptid_creatures_ui import CryptidScreen


class PolishTests(unittest.TestCase):
    def test_breakdown_matches_real_hit_across_guards_and_arenas(self):
        b=CryptidBattle(seed=9)
        for _ in range(100):
            own,enemy=b.sides[0].active,b.sides[1].active
            enemy.ap=random.Random(_).randrange(151)
            enemy.hp=100
            enemy.guard={'guard':.5,'guard_ap':12,'guard_hp':3}
            m=b.catalog.moves[b.card(own.card_id)['moves'][0]]
            result=damage_breakdown(m,own,enemy,b.card(own.card_id),b.card(enemy.card_id))
            expected=damage_values(m,own,enemy,b.card(own.card_id),b.card(enemy.card_id))
            self.assertEqual((result['ap_loss'],result['hp_loss']),expected)
            before=(enemy.ap,enemy.hp)
            b._attack(0,m)
            self.assertEqual((before[0]-enemy.ap,before[1]-enemy.hp),expected)
            self.assertTrue(any('Guard:' in x for x in result['steps']))

    def test_auto_end_can_be_disabled_and_modals_pause_fast_ai(self):
        pygame.init()
        try:
            for auto in (True,False):
                s=CryptidScreen();s.enter();s.start_battle(3);s.auto_end=auto
                move=next(a for a in s.battle.legal_actions(0) if a.kind=='move')
                s._act(move)
                self.assertEqual(s.battle.turn,0)
                self.assertTrue(s.feedback.active)
                s.update(s._last_update+s.feedback.duration+1)
                self.assertEqual(s.battle.turn,1 if auto else 0)
                if auto:
                    s.damage_open=True
                    turn=s.battle.turn_number
                    s.update(100000)
                    self.assertEqual(s.battle.turn_number,turn)
        finally:pygame.quit()


if __name__=='__main__':unittest.main()
