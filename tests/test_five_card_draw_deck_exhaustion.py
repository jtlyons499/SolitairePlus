"""B41: a Five-Card Draw discard must not silently keep the old card when the deck runs out.

Follow-up: when nothing is left to draw, table reads still see how many cards a seat asked
for (what the table saw it throw), while the log and the seat badge show what it received.
"""
import os
import random
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from solitaireplus.games.poker import five_card_draw_ui
from solitaireplus.games.poker.five_card_draw import FiveCardDrawGame
from solitaireplus.games.poker.strategy import estimate_range


NPCS = [
    {"id": "a", "name": "Alex"},
    {"id": "b", "name": "Blake"},
    {"id": "c", "name": "Casey"},
]


def key(card):
    return (card["rank"], card["suit"])


class FiveCardDrawDeckExhaustionTests(unittest.TestCase):
    def setUp(self):
        random.seed(41)
        self.game = FiveCardDrawGame()
        self.game.start_session(NPCS, 1000, 10)
        self.assertTrue(self.game.start_hand())
        # Enter the draw step directly, with every seat still live.
        self.game.current_stage = "draw"
        self.game.player_draw_complete = False
        # Every NPC throws four cards so the stub is guaranteed to run dry.
        self.game.choose_npc_discard_indexes = lambda npc_index: [0, 1, 2, 3]
        self.game.start_second_betting_round = lambda: True

    def live_cards(self):
        cards = list(self.game.player_hand)
        for hand in self.game.npc_hands:
            cards.extend(hand)
        return cards

    def assert_no_duplicates(self):
        cards = (
            self.live_cards()
            + list(self.game.deck)
            + list(getattr(self.game, "draw_muck", []))
        )
        keys = [key(card) for card in cards]
        self.assertEqual(len(keys), len(set(keys)), "a card exists twice")

    def last_draw_event(self, actor_index):
        return [
            event
            for event in self.game.get_hand_history_events()
            if event["type"] == "draw" and event["actor_index"] == actor_index
        ][-1]

    def test_exhausted_deck_replaces_discards_from_reshuffled_muck(self):
        game = self.game
        game.deck = game.deck[:5]
        stub = {key(card) for card in game.deck}
        thrown = set()

        for npc_index in range(len(game.npcs)):
            before = [dict(card) for card in game.npc_hands[npc_index]]
            self.assertTrue(game.perform_npc_draw(npc_index))
            after = game.npc_hands[npc_index]
            hand_keys = {key(card) for card in after}
            for index in range(4):
                self.assertNotIn(key(before[index]), hand_keys,
                                 f"NPC {npc_index} kept discard {before[index]}")
            self.assertEqual(key(before[4]), key(after[4]))
            self.assertEqual(game.npc_draw_counts[npc_index], 4)
            self.assertEqual(self.last_draw_event(npc_index + 1)["draw_count"], 4)
            # Replacements come only from the stub or earlier players' discards.
            for index in range(4):
                self.assertIn(key(after[index]), stub | thrown)
            thrown |= {key(card) for card in before[:4]}
            self.assert_no_duplicates()

        player_before = [dict(card) for card in game.player_hand]
        self.assertTrue(game.player_draw([0, 1, 2, 3, 4]))
        player_keys = {key(card) for card in game.player_hand}
        self.assertFalse(player_keys & {key(card) for card in player_before},
                         "the player was given back an old card")
        self.assertTrue(player_keys <= stub | thrown)
        self.assertEqual(game.player_last_draw_count, 5)
        self.assertEqual(game.player_last_draw_indexes, [0, 1, 2, 3, 4])
        self.assertEqual(self.last_draw_event(0)["draw_count"], 5)
        self.assert_no_duplicates()
        self.assertEqual(len(self.live_cards()), 20)

    def test_nothing_left_to_draw_keeps_the_card_and_logs_it(self):
        game = self.game
        game.deck = game.deck[:1]
        if hasattr(game, "draw_muck"):
            game.draw_muck = []
        before = [dict(card) for card in game.player_hand]

        self.assertTrue(game.player_draw([1, 3]))

        # One card replaced from the stub; nothing is left for the other one,
        # and the player's own discard is never dealt straight back.
        changed = [index for index in range(5)
                   if key(game.player_hand[index]) != key(before[index])]
        self.assertEqual(changed, [1])
        self.assertEqual(game.player_last_draw_count, 1)
        self.assertEqual(game.player_last_draw_indexes, [1])
        event = self.last_draw_event(0)
        # The table saw two cards thrown; one came back.
        self.assertEqual(event["draw_count"], 2)
        self.assertEqual(event["received_count"], 1)
        self.assertEqual(event["text"], "You draw 1 card.")
        self.assertEqual(game.table_reads.snapshot(0)["draw_count"], 2)
        lines = game.get_hand_history_lines()
        self.assertTrue(any("deck" in line.lower() and "keep 1" in line.lower()
                            for line in lines), lines)
        self.assert_no_duplicates()

    def test_npc_that_cannot_draw_does_not_stand_pat(self):
        game = self.game
        game.deck = []
        if hasattr(game, "draw_muck"):
            game.draw_muck = []
        before = [dict(card) for card in game.npc_hands[0]]

        self.assertTrue(game.perform_npc_draw(0))

        self.assertEqual([key(card) for card in game.npc_hands[0]],
                         [key(card) for card in before])
        self.assertEqual(game.npc_draw_counts[0], 0)
        self.assertFalse(game.npc_stood_pat[0])
        event = self.last_draw_event(1)
        self.assertEqual(event["draw_count"], 4)
        self.assertEqual(event["received_count"], 0)
        self.assertNotIn("stands pat", event["text"])
        self.assertTrue(any("keeps 4" in line for line in game.get_hand_history_lines()))

    def test_table_reads_see_what_a_seat_asked_to_draw(self):
        """A seat that threw four and got nothing must not read as a pat hand."""
        game = self.game
        game.deck = []
        game.draw_muck = []

        self.assertTrue(game.perform_npc_draw(0))

        self.assertEqual(game.npc_draw_counts[0], 0)
        read = game.table_reads.snapshot(1)
        self.assertEqual(read["draw_count"], 4)
        asked = estimate_range(read, "five_card_draw", "post_draw")
        four = estimate_range(dict(read, draw_count=4), "five_card_draw", "post_draw")
        pat = estimate_range(dict(read, draw_count=0), "five_card_draw", "post_draw")
        self.assertEqual(asked, four)
        self.assertLess(asked["pressure_shift"], pat["pressure_shift"])

    def test_table_reads_match_the_draw_when_the_deck_holds_out(self):
        game = self.game
        self.assertTrue(game.perform_npc_draw(1))
        event = self.last_draw_event(2)
        self.assertEqual(event["draw_count"], 4)
        self.assertEqual(event["received_count"], 4)
        self.assertEqual(game.table_reads.snapshot(2)["draw_count"], 4)

    def test_a_seat_that_gets_nothing_logs_one_natural_line(self):
        game = self.game
        game.deck = []
        game.draw_muck = []
        name = game.get_table_player_name(1)
        start = len(game.get_hand_history_lines())

        self.assertTrue(game.perform_npc_draw(0))
        self.assertTrue(game.player_draw([0, 2]))

        lines = game.get_hand_history_lines()[start:]
        self.assertEqual(lines[0], f"The deck ran out: {name} keeps 4 cards.")
        self.assertEqual(lines[1], "The deck ran out: you keep 2 cards.")
        self.assertTrue(lines[2].startswith("Your hand:"), lines)
        self.assertEqual(len(lines), 3, lines)
        self.assertFalse(any("0 cards" in line for line in lines), lines)
        # The single line is still the seat's draw, so table reads see it.
        self.assertEqual(self.last_draw_event(1)["text"], lines[0])
        self.assertEqual(self.last_draw_event(0)["text"], lines[1])
        self.assertEqual(game.table_reads.snapshot(0)["draw_count"], 2)


    def test_new_hand_clears_the_muck(self):
        game = self.game
        game.player_draw([0, 1])
        self.assertEqual(len(game.draw_muck), 2)
        game.start_hand()
        self.assertEqual(game.draw_muck, [])
        self.assertEqual(len(game.deck), 52 - 5 * (len(NPCS) + 1))


class FiveCardDrawSeatBadgeTests(unittest.TestCase):
    """The seat badge says what a seat received; 'Stood pat' only for a real stand pat."""

    def setUp(self):
        pygame.init()
        random.seed(41)
        self.game = FiveCardDrawGame()
        self.game.start_session(NPCS, 1000, 10)
        self.assertTrue(self.game.start_hand())
        self.game.current_stage = "draw"
        self.game.player_draw_complete = False

    def badge_texts(self, index):
        texts = []
        real = five_card_draw_ui.render_text_fit

        def capture(text, *args, **kwargs):
            texts.append(str(text))
            return real(text, *args, **kwargs)

        surface = pygame.Surface((1366, 768), pygame.SRCALPHA)
        with mock.patch.object(five_card_draw_ui, "render_text_fit", capture):
            five_card_draw_ui.draw_npc_seat(
                surface, self.game, index, self.game.npcs[index], (300, 200),
                {}, None, lambda *args: None,
            )
        return texts

    def test_seat_that_could_not_draw_shows_drew_zero(self):
        game = self.game
        game.choose_npc_discard_indexes = lambda npc_index: [0, 1, 2, 3]
        game.deck = []
        game.draw_muck = []
        self.assertTrue(game.perform_npc_draw(0))

        texts = self.badge_texts(0)
        self.assertIn("Drew 0", texts)
        self.assertNotIn("Stood pat", texts)

    def test_real_stand_pat_and_normal_draw_are_unchanged(self):
        game = self.game
        game.choose_npc_discard_indexes = lambda npc_index: [] if npc_index == 0 else [1, 2]
        self.assertTrue(game.perform_npc_draw(0))
        self.assertTrue(game.perform_npc_draw(1))

        self.assertIn("Stood pat", self.badge_texts(0))
        self.assertIn("Drew 2", self.badge_texts(1))


if __name__ == "__main__":
    unittest.main()
