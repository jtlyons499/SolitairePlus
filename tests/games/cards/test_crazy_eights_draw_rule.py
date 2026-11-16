"""B47: after drawing in Crazy Eights, only the drawn card may be played, or the player passes.

Standard draw rule (designer accepted): a player with no legal play draws one card. If that
card is playable they may play it (an eight still asks for a suit) or pass; no other card from
the hand may be played on that turn. An unplayable drawn card ends the turn as before. NPCs
follow the same rule: an NPC that draws only ever plays the card it drew.

The table shows a Pass button beside Draw Card only while the drawn card waits to be played.
"""
import os
import random
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from solitaireplus.app import state
from solitaireplus.games.cards import crazy_eights_screen
from solitaireplus.games.cards import crazy_eights_ui
from solitaireplus.games.cards.crazy_eights import CrazyEightsGame


NPCS = [
    {"id": "c8_a", "name": "Alex", "skill_tier": "mid"},
    {"id": "c8_b", "name": "Blake", "skill_tier": "low"},
    {"id": "c8_c", "name": "Casey", "skill_tier": "high"},
]


def card(text):
    return {"rank": text[:-1], "suit": text[-1]}


def cards(*texts):
    return [card(text) for text in texts]


def labels(hand):
    return [f"{c['rank']}{c['suit']}" for c in hand]


class DrawRuleSetup(unittest.TestCase):
    def setUp(self):
        random.seed(47)
        self.game = CrazyEightsGame()
        self.game.start_game(NPCS)
        self.game.npc_action_delay = 0.0
        # Fixed table: 9 of Hearts is up, Hearts active, the human has no legal play.
        self.deal(
            human=("KS", "4D"),
            stock=("2C", "3C", "6S", "5H"),     # popped from the end: 5H is drawn first
        )

    def deal(self, human, stock, top="9H"):
        g = self.game
        g.hands = [
            cards(*human),
            cards("JC", "7S", "QD"),
            cards("2S", "3D", "4C"),
            cards("6C", "10S", "AD"),
        ]
        g.stock = cards(*stock)
        g.discard_pile = [card(top)]
        g.current_suit = card(top)["suit"]
        g.current_player = 0
        g.player_has_drawn = False
        g.pending_eight_index = None
        g.waiting_for_suit_choice = False
        g.game_over = False
        g.winner_index = None


class HumanDrawRuleTests(DrawRuleSetup):
    def test_no_pass_before_drawing(self):
        self.assertFalse(self.game.can_player_pass())
        self.assertFalse(self.game.pass_player_turn())
        self.assertEqual(self.game.current_player, 0)
        self.assertTrue(self.game.can_player_draw())

    def test_other_card_from_hand_is_rejected_after_drawing_a_playable_card(self):
        g = self.game
        self.assertTrue(g.draw_player_card())
        self.assertEqual(labels(g.hands[0]), ["KS", "4D", "5H"])
        self.assertEqual(g.current_player, 0)

        for index in (0, 1):
            with self.subTest(index=index):
                self.assertEqual(g.play_player_card(index), "invalid")
        self.assertEqual(labels(g.hands[0]), ["KS", "4D", "5H"])
        self.assertEqual(labels(g.discard_pile), ["9H"])
        self.assertEqual(g.current_player, 0)

    def test_only_the_drawn_card_counts_as_playable_after_a_draw(self):
        """The rule is the engine's own, not a side effect of the draw gate.

        A card that matches the table is put into the hand next to the drawn one: it still may not
        be played this turn, and the table only highlights the drawn card.
        """
        g = self.game
        self.assertTrue(g.draw_player_card())
        g.hands[0].insert(0, card("QH"))      # matches the active suit
        self.assertTrue(g.is_card_playable(g.hands[0][0]))

        self.assertFalse(g.is_player_card_playable(0))
        self.assertTrue(g.is_player_card_playable(3))
        self.assertEqual(g.play_player_card(0), "invalid")
        self.assertEqual(labels(g.hands[0]), ["QH", "KS", "4D", "5H"])
        self.assertEqual(labels(g.discard_pile), ["9H"])

        self.assertEqual(g.play_player_card(3), "played")
        self.assertEqual(labels(g.discard_pile), ["9H", "5H"])
        self.assertEqual(labels(g.hands[0]), ["QH", "KS", "4D"])

    def test_playing_the_drawn_card_works(self):
        g = self.game
        self.assertTrue(g.draw_player_card())
        self.assertTrue(g.can_player_pass())
        self.assertEqual(g.play_player_card(2), "played")
        self.assertEqual(labels(g.discard_pile), ["9H", "5H"])
        self.assertEqual(labels(g.hands[0]), ["KS", "4D"])
        self.assertEqual(g.current_player, 1)
        self.assertFalse(g.can_player_pass())

    def test_drawn_eight_still_asks_for_a_suit(self):
        g = self.game
        self.deal(human=("KS", "4D"), stock=("2C", "3C", "8C"))
        self.assertTrue(g.draw_player_card())
        self.assertEqual(g.play_player_card(0), "invalid")
        self.assertEqual(g.play_player_card(2), "choose_suit")
        self.assertFalse(g.can_player_pass())   # the suit overlay is up; pick a suit first
        self.assertTrue(g.choose_player_suit("S"))
        self.assertEqual(g.current_suit, "S")
        self.assertEqual(labels(g.discard_pile), ["9H", "8C"])
        self.assertEqual(labels(g.hands[0]), ["KS", "4D"])
        self.assertEqual(g.current_player, 1)

    def test_passing_after_drawing_a_playable_card_keeps_the_card_and_ends_the_turn(self):
        g = self.game
        self.assertTrue(g.draw_player_card())
        self.assertTrue(g.pass_player_turn())
        self.assertEqual(labels(g.hands[0]), ["KS", "4D", "5H"])
        self.assertEqual(labels(g.discard_pile), ["9H"])
        self.assertEqual(g.current_player, 1)
        self.assertFalse(g.player_has_drawn)
        self.assertFalse(g.pass_player_turn())
        self.assertIn("pass", g.last_action_text.lower())

    def test_unplayable_drawn_card_still_ends_the_turn(self):
        g = self.game
        self.deal(human=("KS", "4D"), stock=("2C", "3C"))
        self.assertTrue(g.draw_player_card())
        self.assertEqual(labels(g.hands[0]), ["KS", "4D", "3C"])
        self.assertEqual(g.current_player, 1)
        self.assertFalse(g.can_player_pass())

    def test_next_turn_allows_any_legal_card_again(self):
        g = self.game
        self.assertTrue(g.draw_player_card())
        self.assertTrue(g.pass_player_turn())
        for _ in range(len(g.hands) - 1):
            g._advance_turn()
        self.assertEqual(g.current_player, 0)
        g.hands[0].insert(0, card("QH"))
        self.assertTrue(g.is_player_card_playable(0))
        self.assertEqual(g.play_player_card(0), "played")


class NpcDrawRuleTests(DrawRuleSetup):
    def test_npc_that_draws_a_playable_card_plays_only_that_card(self):
        g = self.game
        self.deal(human=("KS", "4D"), stock=("2C", "3C", "5H"))
        g.current_player = 1
        g.hands[1] = cards("JC", "7S", "QD")
        self.assertTrue(g._take_npc_turn(1))
        self.assertEqual(labels(g.discard_pile), ["9H", "5H"])
        self.assertEqual(labels(g.hands[1]), ["JC", "7S", "QD"])
        self.assertEqual(g.current_player, 2)

    def test_npc_draws_only_ever_play_the_drawn_card(self):
        """Seeded games: whenever an NPC has no legal play, it never plays a card it held before."""
        checked_draws = 0
        for seed in range(60):
            random.seed(1000 + seed)
            g = CrazyEightsGame()
            g.start_game(NPCS)
            for _ in range(400):
                if g.game_over:
                    break
                seat = g.current_player
                if seat == 0:
                    self.play_human_turn(g)
                    continue
                before = list(g.hands[seat])
                top_before = g.get_top_discard()
                had_play = g.has_playable_card(seat)
                g._take_npc_turn(seat)
                if had_play:
                    continue
                checked_draws += 1
                after = g.hands[seat]
                played = g.get_top_discard() is not top_before
                with self.subTest(seed=seed, seat=seat):
                    if played:
                        # Drew X and played X: what is left is exactly the old hand.
                        self.assertEqual(len(after), len(before))
                        self.assertTrue(all(a is b for a, b in zip(after, before)))
                        self.assertFalse(any(g.get_top_discard() is c for c in before))
                    else:
                        self.assertTrue(all(a is b for a, b in zip(after, before)))
                        self.assertIn(len(after), (len(before), len(before) + 1))
        self.assertGreater(checked_draws, 20)

    @staticmethod
    def play_human_turn(g):
        playable = g.get_playable_indexes(0)
        if not playable:
            if not g.draw_player_card() or g.current_player != 0 or g.game_over:
                return
            playable = [len(g.hands[0]) - 1]
        result = g.play_player_card(playable[0])
        if result == "choose_suit":
            g.choose_player_suit("H")
        elif result != "played" and g.current_player == 0 and not g.game_over:
            g._advance_turn()


class TablePassButtonTests(DrawRuleSetup):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def render(self, mouse_pos=(0, 0)):
        surface = pygame.Surface((1366, 768))
        crazy_eights_ui.draw_crazy_eights(surface, mouse_pos, self.game, {}, None)
        return surface

    def test_pass_button_only_appears_after_drawing_a_playable_card(self):
        g = self.game
        pass_rect = crazy_eights_ui._PASS_RECT
        self.assertFalse(pass_rect.colliderect(crazy_eights_ui._DRAW_RECT))

        plain = self.render()
        self.assertIsNone(crazy_eights_ui.get_crazy_eights_action(pass_rect.center, g))

        self.assertTrue(g.draw_player_card())
        drawn = self.render()
        self.assertNotEqual(plain.get_at(pass_rect.center), drawn.get_at(pass_rect.center))
        self.assertEqual(
            crazy_eights_ui.get_crazy_eights_action(pass_rect.center, g),
            (crazy_eights_ui.ACTION_PASS, None),
        )
        # Draw Card is still disabled after the draw.
        self.assertIsNone(
            crazy_eights_ui.get_crazy_eights_action(crazy_eights_ui._DRAW_RECT.center, g))

    def rendered_text(self):
        """Render the table and return every string drawn with the table's fonts."""
        texts = []

        class RecordingFont:
            def __init__(self, font):
                self.font = font

            def render(self, text, *args, **kwargs):
                texts.append(text)
                return self.font.render(text, *args, **kwargs)

            def __getattr__(self, name):
                return getattr(self.font, name)

        fonts = {key: RecordingFont(font) for key, font in crazy_eights_ui._get_fonts().items()}
        with patch.object(crazy_eights_ui._ui, "fonts", fonts):
            self.render()
        return texts

    def test_hint_line_offers_play_or_pass_after_drawing_a_playable_card(self):
        g = self.game
        before = self.rendered_text()
        self.assertIn("No legal play. Draw one card.", before)
        self.assertNotIn("Pass", before)

        self.assertTrue(g.draw_player_card())
        after = self.rendered_text()
        self.assertIn("Play the card you drew, or pass.", after)
        self.assertIn("Pass", after)
        self.assertNotIn("No legal play. Draw one card.", after)

    def test_pass_click_on_the_table_screen_ends_the_turn(self):
        g = self.game
        self.assertTrue(g.draw_player_card())
        self.render()
        sounds = MagicMock()
        saved_pos = getattr(state, "menu_mouse_pos", None)
        self.addCleanup(setattr, state, "menu_mouse_pos", saved_pos)
        state.menu_mouse_pos = crazy_eights_ui._PASS_RECT.center
        with patch.object(crazy_eights_screen, "crazy_eights_game", g), \
                patch.object(crazy_eights_screen, "sounds", sounds):
            crazy_eights_screen.handle_event(
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=state.menu_mouse_pos))
        self.assertEqual(g.current_player, 1)
        self.assertEqual(labels(g.hands[0]), ["KS", "4D", "5H"])
        sounds.audio.play_sound.assert_called_once_with("button_click")


if __name__ == "__main__":
    unittest.main()
