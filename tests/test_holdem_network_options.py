"""The network table options on the shared Hold'em engine (Phase 11).

TexasHoldemGame has three class attributes that only the multiplayer room
subclasses change: allow_network_spectator, finish_hand_after_player_fold
and quick_chat_enabled. Their defaults are single-player behaviour.
"""
import os
import random
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from solitaireplus.games.poker.holdem import TexasHoldemGame


class SpectatorGame(TexasHoldemGame):
    allow_network_spectator = True


class RoomFoldGame(TexasHoldemGame):
    finish_hand_after_player_fold = False


class NoQuickChatGame(TexasHoldemGame):
    quick_chat_enabled = False


def npcs(count):
    return [
        {"id": f"npc{index}", "name": f"Rival {index}", "skill_tier": "mid"}
        for index in range(count)
    ]


def started(game_class, npc_count=2, stack=1000, blind=5, seed=7, **stacks):
    random.seed(seed)
    game = game_class()
    game.start_session(npcs(npc_count), stack, blind)
    if "player_stack" in stacks:
        game.player_stack = stacks["player_stack"]
    return game


def dealt_lines(game):
    return [line for line in game.get_hand_history_lines() if "You are dealt" in line]


class DefaultTests(unittest.TestCase):

    def test_defaults_match_single_player(self):
        self.assertFalse(TexasHoldemGame.allow_network_spectator)
        self.assertTrue(TexasHoldemGame.finish_hand_after_player_fold)
        self.assertTrue(TexasHoldemGame.quick_chat_enabled)
        game = TexasHoldemGame()
        self.assertFalse(game.allow_network_spectator)
        self.assertTrue(game.finish_hand_after_player_fold)
        self.assertTrue(game.quick_chat_enabled)

    def test_busted_player_stops_session_by_default(self):
        game = started(TexasHoldemGame, player_stack=0)
        deck_before = list(game.deck)
        self.assertFalse(game.start_hand())
        self.assertTrue(game.player_busted)
        self.assertTrue(game.hand_complete)
        self.assertEqual(game.current_actor, -1)
        self.assertEqual(game.current_stage, "busted")
        self.assertEqual(game.result_text, "You are out of chips.")
        self.assertEqual(game.hand_number, 0)
        self.assertEqual(game.deck, deck_before)

    def test_funded_player_is_dealt_in_by_default(self):
        game = started(TexasHoldemGame)
        self.assertTrue(game.start_hand())
        self.assertEqual(len(game.player_hand), 2)
        self.assertEqual([len(hand) for hand in game.npc_hands], [2, 2])
        self.assertEqual(len(dealt_lines(game)), 1)

    def test_single_player_deal_order_unchanged(self):
        # Hole cards go seat 0, seat 1, seat 2, seat 0, ... from the top of
        # the shuffled deck (draw_card pops the end), as before the options.
        random.seed(11)
        game = TexasHoldemGame()
        game.start_session(npcs(2), 1000, 5)
        real_build_deck = game.build_deck
        captured = []

        def build_deck():
            real_build_deck()
            captured.extend(dict(card) for card in game.deck)

        game.build_deck = build_deck
        self.assertTrue(game.start_hand())
        dealt = [game.player_hand[0], game.npc_hands[0][0], game.npc_hands[1][0],
                 game.player_hand[1], game.npc_hands[0][1], game.npc_hands[1][1]]
        self.assertEqual(dealt, captured[::-1][:6])
        self.assertEqual(game.deck, captured[:-6])


class SpectatorTests(unittest.TestCase):

    def test_spectator_busted_seat_zero_gets_no_cards(self):
        game = started(SpectatorGame, player_stack=0)
        self.assertTrue(game.start_hand())
        self.assertTrue(game.player_busted)
        self.assertFalse(game.hand_complete)
        self.assertEqual(game.current_stage, "preflop")
        self.assertEqual(game.hand_number, 1)
        self.assertEqual(game.player_hand, [])
        self.assertEqual([len(hand) for hand in game.npc_hands], [2, 2])
        self.assertEqual(dealt_lines(game), [])
        self.assertNotIn(0, game.get_active_player_indexes())
        self.assertNotEqual(game.current_actor, 0)
        self.assertEqual(game.player_hand_contribution, 0)
        self.assertEqual(game.pot, game.small_blind + game.big_blind)

    def test_spectator_with_chips_is_dealt_in(self):
        game = started(SpectatorGame)
        self.assertTrue(game.start_hand())
        self.assertEqual(len(game.player_hand), 2)
        self.assertEqual(len(dealt_lines(game)), 1)

    def test_spectator_hand_plays_out_and_conserves_chips(self):
        for seed in range(10):
            game = started(SpectatorGame, npc_count=3, seed=seed, player_stack=0)
            self.assertTrue(game.start_hand())
            chips = sum(game.npc_stacks) + game.pot
            for _ in range(400):
                if game.hand_complete:
                    break
                if game.betting_round_complete or game.current_actor < 0:
                    game.advance_after_betting_round()
                else:
                    self.assertNotEqual(game.current_actor, 0)
                    game.run_next_npc_action()
            self.assertTrue(game.hand_complete, seed)
            self.assertEqual(game.player_stack, 0)
            self.assertEqual(sum(game.npc_stacks), chips, seed)


class FoldTests(unittest.TestCase):

    def player_to_act(self, game_class, npc_count, seed=3):
        # Seat 0 deals: with two NPCs it opens preflop (under the gun),
        # with one NPC it is the small blind and opens heads-up.
        game = started(game_class, npc_count=npc_count, seed=seed)
        game.dealer_index = npc_count
        self.assertTrue(game.start_hand())
        self.assertEqual(game.current_actor, 0)
        return game

    def test_fold_without_finishing_hand(self):
        game = self.player_to_act(RoomFoldGame, 2)
        community = list(game.community_cards)
        chips = game.player_stack + sum(game.npc_stacks) + game.pot
        self.assertTrue(game.player_fold())
        self.assertTrue(game.player_folded)
        self.assertFalse(game.hand_complete)
        self.assertEqual(game.community_cards, community)
        self.assertEqual(game.current_stage, "preflop")
        # The room moves the turn on itself after a fold.
        self.assertEqual(game.current_actor, 0)
        self.assertFalse(game.resolve_after_fold())
        self.assertEqual(game.player_stack + sum(game.npc_stacks) + game.pot, chips)

    def test_fold_to_one_npc_awards_the_pot(self):
        game = self.player_to_act(RoomFoldGame, 1)
        chips = game.player_stack + sum(game.npc_stacks) + game.pot
        npc_before = game.npc_stacks[0]
        player_in = game.player_hand_contribution
        self.assertTrue(game.player_fold())
        self.assertTrue(game.hand_complete)
        self.assertEqual(game.winner_indexes, [1])
        self.assertEqual(game.pot, 0)
        self.assertEqual(game.npc_stacks[0] - npc_before, game.npc_hand_contributions[0] + player_in)
        self.assertEqual(game.last_pot_awards[0]["winners"], [1])
        self.assertEqual(game.last_pot_awards[0]["eligible"], [1])
        self.assertEqual(game.player_stack + sum(game.npc_stacks), chips)
        self.assertFalse(game.resolve_after_fold())

    def test_default_fold_moves_the_turn_on(self):
        game = self.player_to_act(TexasHoldemGame, 2)
        community = list(game.community_cards)
        self.assertTrue(game.player_fold())
        self.assertFalse(game.hand_complete)
        self.assertEqual(game.community_cards, community)
        self.assertEqual(game.current_actor, 1)


class QuickChatTests(unittest.TestCase):

    def play_npc_decisions(self, game, decisions):
        made = 0
        for _ in range(400):
            if made >= decisions or game.hand_complete:
                break
            if game.betting_round_complete or game.current_actor < 0:
                game.advance_after_betting_round()
            elif game.current_actor == 0:
                if game.get_player_amount_to_call() > 0:
                    game.player_call()
                else:
                    game.player_check()
            else:
                game.run_next_npc_action()
                made += 1
        return made

    def test_quick_chat_disabled(self):
        game = started(NoQuickChatGame, npc_count=3)
        self.assertFalse(hasattr(game, "quick_chat_state"))
        self.assertTrue(game.start_hand())
        context = game.build_npc_ai_context(0)
        self.assertEqual([key for key in context if key.startswith("quick_chat")], [])
        made = 0
        for _ in range(3):
            made += self.play_npc_decisions(game, 6)
            self.assertFalse(hasattr(game, "quick_chat_state"))
            if game.hand_complete and not game.table_is_over():
                game.start_hand()
        self.assertGreaterEqual(made, 6)
        self.assertFalse(hasattr(game, "quick_chat_state"))
        self.assertFalse(hasattr(game, "_quick_chat_event_counter"))
        self.assertFalse(hasattr(game, "_quick_chat_event_signature"))

    def test_quick_chat_disabled_keeps_other_session_resets(self):
        game = started(NoQuickChatGame)
        game.start_hand()
        game.player_model.record_action("raise", "preflop")
        self.assertNotEqual(game.player_model.snapshot(), started(TexasHoldemGame).player_model.snapshot())
        game.start_session(npcs(2), 1000, 5)
        self.assertEqual(game.player_model.snapshot(), started(TexasHoldemGame).player_model.snapshot())
        self.assertFalse(hasattr(game, "quick_chat_state"))

    def test_quick_chat_enabled_by_default(self):
        game = started(TexasHoldemGame, npc_count=3)
        self.assertIsInstance(game.quick_chat_state, dict)
        self.assertTrue(game.start_hand())
        context = game.build_npc_ai_context(0)
        self.assertIn("quick_chat_aggression", context)
        self.assertIn("quick_chat_call_requirement_delta", context)
        self.assertIn("quick_chat_bluff_delta", context)


if __name__ == "__main__":
    unittest.main()
