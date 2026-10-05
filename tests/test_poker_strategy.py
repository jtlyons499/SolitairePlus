"""Public-information learning, rating scaling, wager legality and live tables."""
import copy
import random
import unittest
from collections import Counter

from npc_personality import TRAIT_NAMES, build_trait_profile
from poker_ai import decide_poker_action, choose_poker_open_bet_amount, choose_poker_raise_to_amount
from poker_strategy import (PokerTableReads, estimate_range, signature_for,
                            strategic_context, strategy_chat_line)
from texas_holdem import TexasHoldemGame
from five_card_draw import FiveCardDrawGame
from seven_card_stud import SevenCardStudGame


def npc(identity, rating=2600):
    return {"id": identity, "name": identity, "skill_tier": "elite",
            "personality_traits": dict.fromkeys(TRAIT_NAMES, 5),
            "career_ratings": {g: rating for g in
                               ("texas_holdem", "five_card_draw", "seven_card_stud")}}


def learned_read(action, seat=0):
    memory = PokerTableReads()
    for hand in range(30):
        memory.observe("bet", 9, hand_number=hand, stage="flop", amount=100,
                       round_total=100, pot=200)
        memory.observe(action, seat, hand_number=hand, stage="flop",
                       amount=100 if action == "call" else 0,
                       round_total=100 if action == "call" else 0, pot=300)
    # New hand: historical habits persist, the previous folded hand's cards do not.
    memory.observe("dealer", None, hand_number=31, stage="preflop")
    return memory.snapshot(seat)


def context(read, **changes):
    result = dict(npc_identity="example", game="texas_holdem", stage="flop",
                  personality_traits=dict.fromkeys(TRAIT_NAMES, 5),
                  skill_factor=.95, hand_strength=.3, amount_to_call=0,
                  stack=10000, pot=1000, current_bet=0, current_round_bet=0,
                  minimum_open_bet=20, maximum_open_bet=10000,
                  minimum_raise_size=100, minimum_raise_to=200,
                  maximum_raise_to=10000, soft_maximum_raise_to=10000,
                  can_raise=True, opponents_remaining=1, opponent_reads=[read])
    result.update(changes)
    return result


class PublicReadsTests(unittest.TestCase):
    def test_pressure_is_seat_specific_and_forced_chips_are_not_decisions(self):
        memory = PokerTableReads()
        memory.observe("blind", 1, hand_number=1, stage="preflop",
                       amount=20, round_total=20, pot=30)
        memory.observe("fold", 0, hand_number=1, stage="preflop", pot=30)
        self.assertGreater(memory.snapshot(0)["fold_to_pressure"], .5)
        self.assertEqual(memory.snapshot(1)["decisions"], 0)
        memory.observe("check", 1, hand_number=1, stage="flop", pot=30)
        self.assertEqual(memory.snapshot(1)["fold_to_pressure"], .5)
        self.assertEqual(memory.snapshot(1)["call_under_pressure"], .25)

    def test_learning_is_bounded_and_new_hand_clears_tactical_state(self):
        memory = PokerTableReads()
        for hand in range(200):
            memory.observe("bet", 0, hand_number=hand, stage="river", amount=100,
                           round_total=100, pot=200)
        self.assertEqual(memory.snapshot(0)["decisions"], 96)
        memory.observe("draw", 0, hand_number=199, stage="draw", draw_count=1)
        memory.observe("dealer", None, hand_number=200, stage="preflop")
        self.assertEqual(memory.snapshot(0)["hand_actions"], [])
        self.assertIsNone(memory.snapshot(0)["draw_count"])
        self.assertEqual(memory.snapshot(0)["decisions"], 96)
        memory.clear()
        self.assertEqual(memory.snapshot(0)["decisions"], 0)

    def test_only_revealed_showdowns_supply_bluff_evidence(self):
        memory = PokerTableReads()
        for hand in range(8):
            memory.observe("bet", 0, hand_number=hand, stage="river", amount=100,
                           round_total=100, pot=200)
            memory.observe("player_hand", 0, hand_number=hand, stage="river", hand_name="High Card")
        self.assertEqual(memory.snapshot(0)["reveal_confidence"], 0)
        memory.observe("showdown_hand", 0, hand_number=7, stage="showdown", hand_name="High Card")
        self.assertGreater(memory.snapshot(0)["shown_weak_aggression"], .2)
        memory.observe("showdown_hand", 1, hand_number=7, stage="showdown", hand_name="High Card")
        self.assertEqual(memory.snapshot(1)["reveal_confidence"], 0)

    def test_private_hand_changes_do_not_change_opponent_reads(self):
        for cls in (TexasHoldemGame, FiveCardDrawGame, SevenCardStudGame):
            game = cls()
            game.start_session([npc("observer"), npc("other")], 1000, 10)
            game.start_hand()
            before = game.build_npc_ai_context(0, strength=.55)
            game.player_hand[0] = {"rank": "A", "suit": "Spades"}
            game.npc_hands[1][0] = {"rank": "2", "suit": "Clubs"}
            game.deck.reverse()
            after = game.build_npc_ai_context(0, strength=.55)
            self.assertEqual(before, after, cls.__name__)


class StrategyTests(unittest.TestCase):
    def test_rating_is_per_format_and_does_not_use_overall_or_tier(self):
        player = npc("specialist")
        player["career_ratings"].update(texas_holdem=900, five_card_draw=2600, seven_card_stud=1400)
        weights = []
        for cls in (TexasHoldemGame, FiveCardDrawGame, SevenCardStudGame):
            game = cls()
            game.start_session([player], 1000, 10)
            game.start_hand()
            weights.append(strategic_context(game.build_npc_ai_context(0))["advanced_strategy"]["weight"])
        self.assertEqual(weights[0], 0)
        self.assertGreater(weights[1], .8)
        self.assertEqual(weights[2], 0)

    def test_signature_is_stable_and_preserves_trait_differences(self):
        balanced = dict.fromkeys(TRAIT_NAMES, 5)
        aggressive = dict(balanced, aggressiveness=10, unpredictability=10)
        selective = dict(balanced, selectivity=10, pessimism=10)
        self.assertEqual(signature_for("same", aggressive), "pressure")
        self.assertEqual(signature_for("same", selective), "value")
        self.assertEqual(signature_for("same", balanced), signature_for("same", copy.deepcopy(balanced)))

    def test_opponents_that_fold_are_bluffed_more_than_persistent_callers(self):
        folders = context(learned_read("fold"))
        callers = context(learned_read("call"))
        folder_bets = Counter(decide_poker_action("balanced", folders, random.Random(i))["action"]
                              for i in range(2000))
        caller_bets = Counter(decide_poker_action("balanced", callers, random.Random(i))["action"]
                              for i in range(2000))
        self.assertGreater(folder_bets["bet"], caller_bets["bet"] + 100)
        self.assertEqual(strategic_context(folders)["advanced_strategy"]["tactic"], "pressure_folders")

    def test_better_ranges_respect_rare_aggression_and_public_draws(self):
        cautious = learned_read("fold")
        loose = learned_read("call")
        loose["aggression"] = .8
        for read in (cautious, loose):
            read["hand_actions"] = [("raise", "river", True, 1.0)]
        self.assertGreater(estimate_range(cautious, "texas_holdem", "river")["strong"],
                           estimate_range(loose, "texas_holdem", "river")["strong"])
        pat = dict(cautious, draw_count=0, hand_actions=[])
        three = dict(cautious, draw_count=3, hand_actions=[])
        self.assertGreater(estimate_range(pat, "five_card_draw", "post_draw")["strong"],
                           estimate_range(three, "five_card_draw", "post_draw")["strong"])
        ranges = estimate_range(pat, "five_card_draw", "post_draw")
        self.assertAlmostEqual(sum(ranges[k] for k in ("weak", "medium", "strong")), 1)

    def test_stud_uses_public_pairs_and_flush_threats(self):
        read = learned_read("call")
        paired = [{"rank": "K", "suit": "Spades"}, {"rank": "K", "suit": "Hearts"}]
        empty = estimate_range(read, "seven_card_stud", "fifth")
        seen = estimate_range(read, "seven_card_stud", "fifth", paired)
        self.assertGreater(seen["strong"], empty["strong"])

    def test_bets_from_tight_ranges_produce_more_folds(self):
        tight = learned_read("fold")
        loose = dict(tight, aggression=.90)
        for read in (tight, loose):
            read["hand_actions"] = [("raise", "river", True, .8)]
        a = context(tight, amount_to_call=180, current_bet=180,
                    can_raise=False, hand_strength=.22, last_raiser=0)
        b = context(loose, amount_to_call=180, current_bet=180,
                    can_raise=False, hand_strength=.22, last_raiser=0)
        tight_folds = sum(decide_poker_action("balanced", a, random.Random(i))["action"] == "fold"
                          for i in range(1500))
        loose_folds = sum(decide_poker_action("balanced", b, random.Random(i))["action"] == "fold"
                          for i in range(1500))
        self.assertGreater(tight_folds, loose_folds + 40)

    def test_value_sizes_charge_callers_and_cover_bluffs(self):
        profile = build_trait_profile(dict.fromkeys(TRAIT_NAMES, 5), random.Random(0))
        folder = context(learned_read("fold"), hand_strength=.8)
        caller = context(learned_read("call"), hand_strength=.8)
        a = choose_poker_open_bet_amount(folder, profile, .8)
        b = choose_poker_open_bet_amount(caller, profile, .8)
        self.assertGreater(b, a)
        # Full-strength signatures don't advertise cards through a fixed
        # weak-hand/small-bet versus strong-hand/large-bet rule.
        neutral = context(PokerTableReads().snapshot(0))
        self.assertEqual(choose_poker_open_bet_amount(neutral, profile, .8),
                         choose_poker_open_bet_amount(neutral, profile, .2, bluff=True))

    def test_size_caps_are_legal_and_short_all_in_remains_possible(self):
        profile = build_trait_profile(dict.fromkeys(TRAIT_NAMES, 5), random.Random(0))
        c = context(learned_read("call"), public_opponents=[{"round_bet": 0, "stack": 140}])
        self.assertLessEqual(choose_poker_open_bet_amount(c, profile, .9), 140)
        c.update(current_bet=100, public_opponents=[{"round_bet": 100, "stack": 40}])
        self.assertEqual(choose_poker_raise_to_amount(c, profile, .9), 200)
        c.update(maximum_raise_to=150)
        self.assertEqual(choose_poker_raise_to_amount(c, profile, .9), 150)
        c.update(fixed_limit=True, maximum_raise_to=10000, soft_maximum_raise_to=200)
        self.assertEqual(choose_poker_raise_to_amount(c, profile, .9), 200)

    def test_matching_chat_does_not_claim_hidden_cards_or_react_to_stale_actions(self):
        decision = decide_poker_action("balanced", context(learned_read("fold")), random.Random(1))
        decision["action"] = "bet"
        lines = [strategy_chat_line(decision, "bet", random.Random(i)) for i in range(30)]
        self.assertIn("Let's see who stays.", lines)
        self.assertIsNone(strategy_chat_line(decision, "fold", random.Random(1)))
        self.assertIsNone(strategy_chat_line(decision, "player_bet", random.Random(1)))


class AdvancedTablesTests(unittest.TestCase):
    def test_forced_all_in_blinds_and_antes_still_receive_cards(self):
        for cls, count in ((FiveCardDrawGame, 5), (SevenCardStudGame, 3)):
            for short_seat in (0, 1, 2):
                game = cls()
                game.start_session([npc("one"), npc("two")], 1000, 10)
                if short_seat == 0:
                    game.player_stack = 1
                else:
                    game.npc_stacks[short_seat - 1] = 1
                game.start_hand()
                hands = [game.player_hand, *game.npc_hands]
                self.assertEqual([len(h) for h in hands], [count]*3, cls.__name__)
                self.assertEqual(len({(c["rank"], c["suit"]) for h in hands for c in h}), count*3)

    def test_elite_tables_finish_conserve_chips_and_use_strategy(self):
        for cls in (TexasHoldemGame, FiveCardDrawGame, SevenCardStudGame):
            completions = 0
            observed_strategy = False
            for seed in range(20):
                random.seed(seed + 500)
                game = cls()
                game.start_session([npc(str(i)) for i in range(3)], 1000, 10)
                for _ in range(8):
                    if not game.start_hand():
                        break
                    for turn in range(1000):
                        self.assertEqual(game.player_stack + sum(game.npc_stacks) + game.pot, 4000)
                        self.assertTrue(all(s >= 0 for s in [game.player_stack, *game.npc_stacks]))
                        if game.hand_complete:
                            completions += 1
                            break
                        if game.current_stage == "draw":
                            self.assertTrue(game.player_draw([0, 1, 2]))
                        elif game.is_betting_round_complete():
                            self.assertTrue(game.advance_after_betting_round(), f"{cls.__name__} seed={seed}, stage={game.current_stage}, complete={game.hand_complete}, cards={len(game.player_hand)}, active={game.get_active_player_indexes()}")
                        elif game.current_actor == 0:
                            self.assertTrue(game.player_call() if game.can_player_call() else game.player_check())
                        else:
                            self.assertTrue(game.run_next_npc_action())
                            observed_strategy |= any(d and d["strategy"]["enabled"]
                                                     for d in game.npc_ai_last_decisions)
                    else:
                        self.fail(f"{cls.__name__} stalled: seed={seed}, stage={game.current_stage}")
            self.assertGreater(completions, 60, cls.__name__)
            self.assertTrue(observed_strategy, cls.__name__)
            self.assertGreater(sum(len(h) for h in game.table_reads.histories.values()), 0)
            game.start_session([npc("new_table")], 1000, 10)
            self.assertEqual(game.table_reads.histories, {})


if __name__ == "__main__":
    unittest.main()
