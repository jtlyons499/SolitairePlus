"""B40: Seven-Card Stud must not hand the bring-in to a player with no chips."""
import unittest
from unittest.mock import patch

from solitaireplus.games.poker.seven_card_stud import SevenCardStudGame


def card(rank, suit):
    return {"rank": rank, "suit": suit}


def new_game(npc_count=2):
    game = SevenCardStudGame()
    game.start_session(
        [{"id": f"n{i}", "name": f"N{i}"} for i in range(npc_count)],
        1000,
        10,
    )
    return game


def set_door_cards(game, door_cards):
    """Give every seat two hole cards and the given door card."""
    game.player_hand = [card("A", "Spades"), card("A", "Hearts"), door_cards[0]]
    game.npc_hands = [
        [card("K", "Spades"), card("K", "Hearts"), door]
        for door in door_cards[1:]
    ]


class StudBringInTests(unittest.TestCase):
    def test_all_in_lowest_door_card_is_skipped(self):
        game = new_game()
        # Seat 1 holds the lowest door card but has no chips left.
        set_door_cards(game, [card("K", "Hearts"), card("2", "Clubs"), card("5", "Diamonds")])
        game.npc_stacks[0] = 0
        game.npc_all_in[0] = True
        self.assertEqual(game.get_bring_in_index(), 2)

    def test_human_with_no_chips_is_skipped(self):
        game = new_game()
        set_door_cards(game, [card("2", "Clubs"), card("9", "Hearts"), card("5", "Diamonds")])
        game.player_stack = 0
        game.player_all_in = True
        self.assertEqual(game.get_bring_in_index(), 2)

    def test_player_with_chips_still_gets_lowest_card_bring_in(self):
        game = new_game()
        set_door_cards(game, [card("K", "Hearts"), card("2", "Clubs"), card("5", "Diamonds")])
        self.assertEqual(game.get_bring_in_index(), 1)

    def test_nobody_with_chips_keeps_lowest_card(self):
        # Conservative fallback: if every live hand is all-in, keep the
        # old choice so the hand still starts and runs out.
        game = new_game()
        set_door_cards(game, [card("K", "Hearts"), card("2", "Clubs"), card("5", "Diamonds")])
        game.player_stack = 0
        game.player_all_in = True
        game.npc_stacks = [0, 0]
        game.npc_all_in = [True, True]
        self.assertEqual(game.get_bring_in_index(), 1)

    def test_start_hand_ante_all_in_seat_does_not_post_bring_in(self):
        game = new_game()
        # Seat 1 can only afford the ante, so it is all-in before the deal.
        game.npc_stacks[0] = game.ante_amount
        scripted = {
            0: [card("A", "Spades"), card("A", "Hearts"), card("K", "Hearts")],
            1: [card("K", "Spades"), card("K", "Clubs"), card("2", "Clubs")],
            2: [card("Q", "Spades"), card("Q", "Hearts"), card("5", "Diamonds")],
        }
        original_give = game._give_card_to_seat

        def give(seat, _card):
            original_give(seat, scripted[seat][len(game.get_seat_hand(seat))])

        with patch.object(game, "_give_card_to_seat", side_effect=give):
            self.assertTrue(game.start_hand())

        self.assertTrue(game.npc_all_in[0])
        self.assertEqual(game.npc_stacks[0], 0)
        self.assertEqual(game.bring_in_index, 2)
        self.assertEqual(
            game.npc_stacks[1],
            1000 - game.ante_amount - game.bring_in_amount,
        )
        self.assertEqual(
            game.pot,
            3 * game.ante_amount + game.bring_in_amount,
        )
        # Action starts left of the real bring-in seat (the human).
        self.assertEqual(game.current_actor, 0)


if __name__ == "__main__":
    unittest.main()
