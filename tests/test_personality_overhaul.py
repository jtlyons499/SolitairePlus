"""Run from the project root: python -m unittest discover -s tests -v."""
import copy
import random
import unittest
from collections import Counter

from npc_personality import (TRAIT_NAMES, get_npc_traits, build_trait_profile,
                             PokerGrudgeMemory, npc_identity)
from npc_manager import NPCS
from poker_ai import decide_poker_action, choose_poker_open_bet_amount, choose_poker_raise_to_amount
from blind_mans_bluff import BlindMansBluffGame
from texas_holdem import TexasHoldemGame
from five_card_draw import FiveCardDrawGame
from seven_card_stud import SevenCardStudGame


def traits(**changes):
    return dict(dict.fromkeys(TRAIT_NAMES, 5), **changes)


def npc(identity="bob", **changes):
    return {"id": identity, "name": identity.title(), "skill_tier": "strong",
            "personality_traits": traits(**changes)}


class PersonalityTests(unittest.TestCase):
    def rates(self, values, **context_changes):
        context = dict(stage="preflop", position="middle", hand_strength=0.28,
                       skill_factor=0.7, amount_to_call=180, stack=200,
                       pot=200, current_bet=180, can_raise=False,
                       opponents_remaining=1, last_raiser=0)
        context.update(context_changes)
        context["personality_traits"] = values
        return Counter(decide_poker_action("balanced", context, random.Random(i))["action"]
                       for i in range(2500))

    def test_roster_and_legacy_migration(self):
        for entry in NPCS:
            self.assertEqual(set(entry["personality_traits"]), set(TRAIT_NAMES))
            self.assertTrue(all(isinstance(v, int) and 1 <= v <= 10
                                for v in entry["personality_traits"].values()))
        old = {"id": "custom", "game_personality": "aggressive"}
        self.assertEqual(get_npc_traits(old), get_npc_traits(old.copy()))
        self.assertGreater(get_npc_traits(old)["aggressiveness"], get_npc_traits(old)["caution"])
        self.assertNotIn("personality_traits", old)
        broken = {"personality_traits": {"caution": 99, "bitterness": -5, "tenacity": None}}
        self.assertEqual(get_npc_traits(broken)["caution"], 10)
        self.assertEqual(get_npc_traits(broken)["bitterness"], 1)

    def test_traits_change_observable_play(self):
        low = self.rates(traits(tenacity=1), hand_strength=0.5)
        high = self.rates(traits(tenacity=10), hand_strength=0.5)
        self.assertGreater(high["fold"], low["fold"] + 100)
        low = self.rates(traits(pessimism=1), amount_to_call=40, stack=200)
        high = self.rates(traits(pessimism=10), amount_to_call=40, stack=200)
        self.assertGreater(high["fold"], low["fold"] + 100)
        low = self.rates(traits(aggressiveness=1), amount_to_call=0, current_bet=0)
        high = self.rates(traits(aggressiveness=10), amount_to_call=0, current_bet=0)
        self.assertGreater(high["bet"], low["bet"] + 100)
        high = self.rates(traits(selectivity=10), amount_to_call=0, current_bet=0, hand_strength=0.10)
        low = self.rates(traits(selectivity=1), amount_to_call=0, current_bet=0, hand_strength=0.10)
        self.assertLess(high["bet"], low["bet"])
        neutral = self.rates(traits(bitterness=10), amount_to_call=40, stack=200)
        angry = self.rates(traits(bitterness=10), amount_to_call=40, stack=200, grudge_pressure=1)
        self.assertLess(angry["fold"], neutral["fold"])
        low = self.rates(traits(escalation=1), can_raise=True, hand_strength=0.55, amount_to_call=20, stack=1000)
        high = self.rates(traits(escalation=10), can_raise=True, hand_strength=0.55, amount_to_call=20, stack=1000)
        self.assertGreater(high["raise"], low["raise"] + 100)

    def test_memory_is_opponent_specific_and_cools(self):
        memory = PokerGrudgeMemory()
        memory.record_loss("bob", "amy", 1, 10, 1)
        original = memory.intensity("bob", "amy", 1, 10)
        memory.record_loss("bob", "amy", 1, 10, 1)
        self.assertEqual(original, memory.intensity("bob", "amy", 1, 10))
        self.assertEqual(memory.intensity("bob", "player", 2, 10), 0)
        self.assertGreater(memory.intensity("bob", "amy", 10, 10), 0)
        self.assertLess(memory.intensity("bob", "amy", 10, 10), original)
        memory.clear()
        self.assertEqual(memory.intensity("bob", "amy", 1, 10), 0)

    def test_exact_knockout_amount_and_stud_limit(self):
        profile = build_trait_profile(traits(bitterness=10, tenacity=1), random.Random(1))
        context = dict(grudge_intensity=1, grudge_target_round_total=23549,
                       minimum_open_bet=50, maximum_open_bet=5000, stack=50000,
                       current_round_bet=0, pot=3000)
        self.assertEqual(choose_poker_open_bet_amount(context, profile, 0.6), 23549)
        context.update(current_bet=100, minimum_raise_to=200, maximum_raise_to=50000,
                       minimum_raise_size=100, soft_maximum_raise_to=5000)
        self.assertEqual(choose_poker_raise_to_amount(context, profile, 0.6), 23549)
        context["fixed_limit"] = True
        self.assertLessEqual(choose_poker_raise_to_amount(context, profile, 0.6), 5000)
        context["stack"] = 100
        self.assertLessEqual(choose_poker_open_bet_amount(context, profile, 0.6), 5000)

    def test_real_showdown_grudges_respect_side_pot_eligibility(self):
        game = TexasHoldemGame()
        game.start_session([npc("bob", bitterness=10), npc("amy", bitterness=10)], 1000, 10)
        game.hand_number = 1
        game.npc_hand_contributions = [100, 500]
        game.last_pot_awards = [{"amount": 300, "eligible": [0, 1, 2], "winners": [2]},
                                {"amount": 800, "eligible": [0, 2], "winners": [0]}]
        game.record_personality_showdown({0: (), 1: (), 2: ()})
        self.assertGreater(game.personality_memory.intensity("bob", "amy", 1, 10), 0)
        self.assertEqual(game.personality_memory.intensity("bob", "player", 1, 10), 0)
        self.assertGreater(game.personality_memory.intensity("amy", "player", 1, 10), 0)
        game.start_session([npc("bob")], 1000, 10)
        self.assertEqual(game.personality_memory.entries, {})


class BluffTests(unittest.TestCase):
    def game(self):
        game = BlindMansBluffGame(random.Random(4))
        game.start_session([npc("bob"), npc("amy")], 1000)
        return game

    def test_hidden_own_card_never_influences_ai(self):
        game = self.game()
        before = game._npc_context(1)
        game.cards[1] = {"rank": "A", "suit": "Spades"}
        self.assertEqual(before, game._npc_context(1))
        game.cards[1] = {"rank": "2", "suit": "Clubs"}
        self.assertEqual(before, game._npc_context(1))

    def test_raise_reopens_action_and_only_charges_difference(self):
        game = self.game()
        self.assertTrue(game._act(0, "bet", 20))
        self.assertTrue(game._act(1, "call"))
        self.assertTrue(game._act(2, "raise", 50))
        self.assertIn(0, game.pending)
        self.assertIn(1, game.pending)
        stack = game.player_stack
        self.assertTrue(game._act(0, "call"))
        self.assertEqual(stack - game.player_stack, 30)
        self.assertEqual(game.round_bets[0], 50)

    def test_short_all_in_does_not_reopen_raises(self):
        game = self.game()
        game._act(0, "bet", 20)
        game._act(1, "call")
        game.npc_stacks[1] = 25
        self.assertTrue(game._act(2, "raise", 25))
        self.assertIn(0, game.pending)
        self.assertFalse(game._can_raise(0))
        self.assertFalse(game._can_raise(1))

    def test_side_pots_and_ties_conserve_chips(self):
        game = self.game()
        game.hand_contributions = [100, 200, 200]
        game.round_bets = [100, 200, 200]
        game.player_stack = 0
        game.npc_stacks = [0, 0]
        game.pot = 500
        game.cards = [{"rank": "A", "suit": "Clubs"}, {"rank": "K", "suit": "Hearts"},
                      {"rank": "K", "suit": "Spades"}]
        game._showdown()
        self.assertEqual(game.player_stack, 300)
        self.assertEqual(game.npc_stacks, [100, 100])
        self.assertEqual(game.pot, 0)

    def test_random_tables_finish_without_lost_chips(self):
        for seed in range(100):
            rng = random.Random(seed)
            game = BlindMansBluffGame(rng)
            game.start_session([npc(str(i), aggressiveness=(seed % 10) + 1) for i in range(3)], 1000)
            for _ in range(10):
                for turn in range(200):
                    self.assertEqual(game.player_stack + sum(game.npc_stacks) + game.pot, 4000)
                    self.assertTrue(all(value >= 0 for value in [game.player_stack, *game.npc_stacks]))
                    if game.hand_complete:
                        break
                    action = rng.choice(game.get_player_actions())
                    method = getattr(game, "player_" + action)
                    self.assertTrue(method(rng.choice(game.get_player_bet_presets())[1])
                                    if action in ("bet", "raise") else method())
                else:
                    self.fail(f"Bluff hand stalled: seed {seed}")
                if game.session_complete:
                    break
                game.start_hand()


class SharedPokerIntegrationTests(unittest.TestCase):
    def test_full_holdem_draw_stud_tables(self):
        for cls in (TexasHoldemGame, FiveCardDrawGame, SevenCardStudGame):
            completed = 0
            for seed in range(15):
                random.seed(seed)
                game = cls()
                game.start_session(NPCS[:3], 1000, 10)
                for hand in range(8):
                    if not game.start_hand():
                        break
                    for turn in range(1000):
                        self.assertEqual(game.player_stack + sum(game.npc_stacks) + game.pot, 4000)
                        if game.hand_complete:
                            completed += 1
                            break
                        if game.current_stage == "draw":
                            self.assertTrue(game.player_draw([0, 1, 2]))
                        elif game.is_betting_round_complete():
                            self.assertTrue(game.advance_after_betting_round())
                        elif game.current_actor == 0:
                            if game.can_player_call():
                                self.assertTrue(game.player_call())
                            elif game.can_player_check():
                                self.assertTrue(game.player_check())
                            else:
                                self.assertTrue(game.player_fold())
                        else:
                            game.run_next_npc_action()
                    else:
                        self.fail(f"{cls.__name__} stalled, seed {seed}, stage {game.current_stage}")
            self.assertGreater(completed, 40, cls.__name__)


if __name__ == "__main__":
    unittest.main()
