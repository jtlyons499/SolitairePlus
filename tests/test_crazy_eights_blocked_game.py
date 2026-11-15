"""B46: Crazy Eights must not end the moment one player can't draw.

A player who can't play and can't draw passes. The game ends as blocked only
when every player has passed in a row; then the smallest hand wins. NPCs follow
the same rule, and the "cannot draw" log line must not overwrite the result.
"""
import random
import unittest

from solitaireplus.games.cards.crazy_eights import CrazyEightsGame


NPCS = [
    {"id": "b46_a", "name": "Alex"},
    {"id": "b46_b", "name": "Blake"},
    {"id": "b46_c", "name": "Casey"},
]


def card(text):
    return {"rank": text[:-1], "suit": text[-1]}


def cards(*texts):
    return [card(text) for text in texts]


class CrazyEightsBlockedGameTests(unittest.TestCase):
    def setUp(self):
        random.seed(46)
        self.game = CrazyEightsGame()
        self.game.start_game(NPCS)
        self.game.npc_action_delay = 0.0

    def set_table(self, hands, top="5H", current_player=0):
        game = self.game
        game.hands = [cards(*hand) for hand in hands]
        game.stock = []
        game.discard_pile = [card(top)]
        game.current_suit = top[-1]
        game.current_player = current_player
        game.player_has_drawn = False
        game.pending_eight_index = None
        game.waiting_for_suit_choice = False
        game.game_over = False
        game.winner_index = None
        game.result_text = ""
        game._schedule_npc_action()

    def test_players_with_playable_cards_continue_after_an_npc_cannot_draw(self):
        game = self.game
        # Empty draw pile, a single discard: nothing can be recycled either.
        self.set_table(
            [
                ["9H", "2C"],   # you: 9H plays
                ["3D", "4C"],   # Alex: no play, cannot draw
                ["6H", "KC"],   # Blake: 6H plays
                ["7H", "QD"],   # Casey: 7H plays
            ],
            current_player=1,
        )

        self.assertTrue(game.update())
        self.assertFalse(game.game_over, game.result_text)
        self.assertIsNone(game.winner_index)
        self.assertEqual(game.current_player, 2)
        self.assertEqual(game.last_action_text, "Alex cannot draw.")
        self.assertEqual(len(game.hands[1]), 2)

        self.assertTrue(game.update())
        self.assertFalse(game.game_over, game.result_text)
        self.assertEqual(game.get_top_discard(), card("6H"))
        self.assertEqual(len(game.hands[2]), 1)
        self.assertEqual(game.current_player, 3)

        self.assertTrue(game.update())
        self.assertFalse(game.game_over, game.result_text)
        self.assertEqual(game.get_top_discard(), card("7H"))
        self.assertEqual(len(game.hands[3]), 1)
        self.assertEqual(game.current_player, 0)

        self.assertEqual(game.play_player_card(0), "played")
        self.assertFalse(game.game_over, game.result_text)
        self.assertEqual(game.hands[0], cards("2C"))

    def test_players_with_playable_cards_continue_after_you_cannot_draw(self):
        game = self.game
        self.set_table(
            [
                ["3D", "4C"],   # you: no play, cannot draw
                ["6H", "KC"],   # Alex: 6H plays
                ["7H", "QD"],   # Blake: 7H plays
                ["2D", "JC"],   # Casey
            ],
            current_player=0,
        )

        self.assertTrue(game.can_player_draw())
        game.draw_player_card()
        self.assertFalse(game.game_over, game.result_text)
        self.assertIsNone(game.winner_index)
        self.assertEqual(game.current_player, 1)
        self.assertEqual(len(game.hands[0]), 2)

        self.assertTrue(game.update())
        self.assertFalse(game.game_over, game.result_text)
        self.assertEqual(game.get_top_discard(), card("6H"))
        self.assertEqual(game.current_player, 2)

        self.assertTrue(game.update())
        self.assertFalse(game.game_over, game.result_text)
        self.assertEqual(game.get_top_discard(), card("7H"))

    def test_all_players_passing_in_a_row_ends_with_smallest_hand_winning(self):
        game = self.game
        self.set_table(
            [
                ["2C", "3D", "4S"],         # you: 3 cards
                ["6C", "7D", "9S", "JC"],   # Alex: 4 cards
                ["QD", "KS"],               # Blake: 2 cards, smallest
                ["2D", "3S", "4C"],         # Casey: 3 cards
            ],
            current_player=0,
        )

        game.draw_player_card()   # you pass
        self.assertFalse(game.game_over, game.result_text)
        self.assertEqual(game.current_player, 1)

        self.assertTrue(game.update())   # Alex passes
        self.assertFalse(game.game_over, game.result_text)
        self.assertTrue(game.update())   # Blake passes
        self.assertFalse(game.game_over, game.result_text)

        self.assertTrue(game.update())   # Casey passes: everyone passed in a row
        self.assertTrue(game.game_over)
        self.assertEqual(game.winner_index, 2)
        self.assertEqual(game.result_text, "Blake wins the blocked game.")
        # The "cannot draw" line comes first; the result is the last word.
        self.assertEqual(game.action_log[-2], "Casey cannot draw.")
        self.assertEqual(game.last_action_text, game.result_text)
        self.assertEqual(game.action_log[-1], game.result_text)
        self.assertEqual([len(hand) for hand in game.hands], [3, 4, 2, 3])

        self.assertFalse(game.update())

    def test_round_of_passes_starting_with_an_npc_can_make_you_the_winner(self):
        game = self.game
        self.set_table(
            [
                ["2C"],                     # you: 1 card, smallest
                ["6C", "7D"],
                ["QD", "KS", "3S"],
                ["2D", "3C"],
            ],
            current_player=1,
        )

        for _ in range(3):   # Alex, Blake and Casey pass
            self.assertTrue(game.update())
            self.assertFalse(game.game_over, game.result_text)
        self.assertEqual(game.current_player, 0)

        game.draw_player_card()   # you pass last
        self.assertTrue(game.game_over)
        self.assertEqual(game.winner_index, 0)
        self.assertEqual(game.result_text, "You win the blocked game!")
        self.assertEqual(game.action_log[-2], "No cards remain to draw.")
        self.assertEqual(game.last_action_text, game.result_text)

    def test_a_play_or_a_draw_restarts_the_count_of_passes_in_a_row(self):
        game = self.game
        self.set_table(
            [
                ["2C", "3S"],          # you: no play on 5H
                ["4C", "6S"],          # Alex: no play
                ["8C", "KD", "QD"],    # Blake: plays 8C and names Diamonds
                ["2S", "3C"],          # Casey
            ],
            current_player=0,
        )

        game.draw_player_card()           # you pass (1)
        self.assertTrue(game.update())    # Alex passes (2)
        self.assertFalse(game.game_over, game.result_text)

        self.assertTrue(game.update())    # Blake plays: the passes no longer count
        self.assertEqual(game.get_top_discard(), card("8C"))
        self.assertEqual(game.current_suit, "D")

        # Casey has no Diamond: 5H is shuffled back, drawn, and can't be played.
        self.assertTrue(game.update())
        self.assertEqual(game.hands[3][-1], card("5H"))
        self.assertEqual(game.stock, [])
        self.assertEqual(game.discard_pile, [card("8C")])
        self.assertEqual(game.current_player, 0)

        game.draw_player_card()           # you pass (1 after the play and the draw)
        self.assertTrue(game.update())    # Alex passes (2): four passes in all, not in a row
        self.assertFalse(game.game_over, game.result_text)
        self.assertEqual(game.current_player, 2)

        self.assertTrue(game.update())    # Blake can still play a Diamond
        self.assertFalse(game.game_over, game.result_text)
        self.assertEqual(game.get_top_discard()["suit"], "D")

    def test_tied_smallest_hands_after_all_pass_is_a_blocked_tie(self):
        game = self.game
        self.set_table(
            [
                ["2C", "3D"],
                ["6C", "7D"],
                ["QD", "KS", "3S"],
                ["2D", "3C", "4S"],
            ],
            current_player=2,
        )

        self.assertTrue(game.update())   # Blake
        self.assertTrue(game.update())   # Casey
        game.draw_player_card()          # you
        self.assertFalse(game.game_over, game.result_text)
        self.assertTrue(game.update())   # Alex: the fourth pass in a row
        self.assertTrue(game.game_over)
        self.assertIsNone(game.winner_index)
        self.assertEqual(game.result_text, "Blocked game. Lowest-card tie: You, Alex.")
        self.assertEqual(game.last_action_text, game.result_text)


if __name__ == "__main__":
    unittest.main()
