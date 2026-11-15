"""B60: a Cryptid deck with fewer than two creatures cannot open a battle.

The opener draws two creatures (one active, one on the Docket). A deck without
them used to crash with StopIteration; now the battle refuses with a clear
ValueError and the screen shows that message instead of starting.
"""
import os
import unittest
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
from solitaireplus.games.cryptid.collection import new_collection
from solitaireplus.games.cryptid.creatures import CryptidBattle, CryptidCatalog
from solitaireplus.games.cryptid.ui import CryptidScreen


def thin_deck(catalog, key, creatures):
    """Keep only the first `creatures` creature cards of a starter deck, the
    rest become support cards (simulates edited data past validation)."""
    support = next(cid for cid, card in catalog.cards.items() if card['kind'] == 'support')
    cards, kept = [], 0
    for cid in catalog.decks[key]['cards']:
        if catalog.cards[cid]['kind'] == 'creature':
            if kept < creatures:
                kept += 1
            else:
                cid = support
        cards.append(cid)
    catalog.decks[key]['cards'] = cards


class OpenerEngineTests(unittest.TestCase):
    def setUp(self):
        self.catalog = CryptidCatalog()
        self.keys = list(self.catalog.decks)

    def test_player_deck_with_zero_or_one_creature_raises_clear_error(self):
        for count in (0, 1):
            catalog = CryptidCatalog()
            thin_deck(catalog, self.keys[0], count)
            with self.subTest(creatures=count):
                with self.assertRaises(ValueError) as caught:
                    CryptidBattle(catalog, self.keys[0], self.keys[1], seed=4)
                message = str(caught.exception)
                self.assertIn('Your deck', message)
                self.assertIn(f'{count} creature', message)
                self.assertIn('at least two', message)

    def test_opponent_deck_with_one_creature_names_the_opponent(self):
        thin_deck(self.catalog, self.keys[1], 1)
        with self.assertRaises(ValueError) as caught:
            CryptidBattle(self.catalog, self.keys[0], self.keys[1], seed=4)
        self.assertIn("opponent's deck", str(caught.exception))

    def test_two_creatures_still_open_a_battle(self):
        thin_deck(self.catalog, self.keys[0], 2)
        battle = CryptidBattle(self.catalog, self.keys[0], self.keys[1], seed=4)
        side = battle.sides[0]
        self.assertIsNotNone(side.active)
        self.assertEqual(len(side.docket), 1)


class OpenerScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def test_practice_start_shows_message_instead_of_starting(self):
        for count in (0, 1):
            with self.subTest(creatures=count):
                catalog = CryptidCatalog()
                screen = CryptidScreen(catalog)
                screen.enter()
                thin_deck(catalog, screen.deck_keys[screen.deck_index], count)
                screen.start_battle(5)
                self.assertEqual(screen.page, 'menu')
                self.assertIsNone(screen.battle)
                self.assertIn('at least two', screen.start_error)
                drawn = []
                original = screen._text
                screen._text = lambda surface, value, *rest, **kw: (drawn.append(str(value)), original(surface, value, *rest, **kw))[1]
                screen.draw(pygame.Surface((1366, 768)), (0, 0))
                self.assertIn(screen.start_error, drawn)

    def test_message_clears_after_a_good_start_and_on_reenter(self):
        catalog = CryptidCatalog()
        screen = CryptidScreen(catalog)
        screen.enter()
        good = list(catalog.decks[screen.deck_keys[0]]['cards'])
        thin_deck(catalog, screen.deck_keys[0], 1)
        screen.start_battle(5)
        self.assertTrue(screen.start_error)
        screen.enter()
        self.assertEqual(screen.start_error, '')
        screen.start_battle(5)
        self.assertTrue(screen.start_error)
        catalog.decks[screen.deck_keys[0]]['cards'] = good
        screen.start_battle(5)
        self.assertEqual(screen.page, 'battle')
        self.assertEqual(screen.start_error, '')

    def test_career_start_shows_message_and_keeps_battle_serial(self):
        catalog = CryptidCatalog()
        screen = CryptidScreen(catalog)
        state = new_collection(cards=catalog)
        screen.enter_career([], state)
        opponent = screen.deck_keys[(screen.deck_index+1) % len(screen.deck_keys)]
        thin_deck(catalog, opponent, 1)
        screen.start_battle(5)
        self.assertEqual(screen.page, 'career_home')
        self.assertIsNone(screen.battle)
        self.assertEqual(state['battle_serial'], 0)
        self.assertIn("opponent's deck", screen.collection_view.message)

    def test_career_start_saves_battle_serial_before_building_the_battle(self):
        # The career battle_serial save runs before the battle is built, as it
        # did before B60. Saving can create an unseeded random.Random (the
        # tempfile name generator), and the harness seeds those from one shared
        # counter, so swapping the order deals a different harness battle.
        import solitaireplus.games.cryptid.ui as cryptid_ui
        calls = []
        catalog = CryptidCatalog()
        screen = CryptidScreen(catalog)
        state = new_collection(cards=catalog)
        screen.enter_career([], state, persist=lambda: calls.append('save'))
        real_battle = cryptid_ui.CryptidBattle

        def recording_battle(*args, **kwargs):
            calls.append('build')
            return real_battle(*args, **kwargs)

        cryptid_ui.CryptidBattle = recording_battle
        try:
            screen.start_battle(5)
        finally:
            cryptid_ui.CryptidBattle = real_battle
        self.assertEqual(screen.page, 'battle')
        self.assertEqual(state['battle_serial'], 1)
        self.assertEqual(calls, ['save', 'build'])


if __name__ == '__main__':
    unittest.main()
