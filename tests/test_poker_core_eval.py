"""The shared poker hand evaluator in core.py and the per-seat views of every poker engine.

B86 group 1 moved the one hand evaluator into games/poker/core.py. Texas Hold'em (and so
Draw and Stud), Five-O and Blind Man's Bluff all score hands through it. The seat views are
plain read-only per-seat lists (seat 0 = human, seat i = npcs[i-1]) that the shared table
rules use; they must agree with each engine's existing index helpers.
"""
import ast
import random
import sys
import unittest
from itertools import combinations
from pathlib import Path

from solitaireplus.games.poker import core, niche_common
from solitaireplus.games.poker import holdem
from solitaireplus.games.poker.five_o import FiveOPokerGame
from solitaireplus.games.poker.holdem import TexasHoldemGame
from tests.support.poker_variants import ADAPTERS_BY_KEY

ROOT = Path(__file__).resolve().parents[1]
SUITS = {"C": "Clubs", "D": "Diamonds", "H": "Hearts", "S": "Spades"}
DECK = [{"rank": rank, "suit": suit} for suit in niche_common.SUITS for rank in niche_common.RANKS]


def cards(text):
    """'AS 10H 2C' -> card dicts."""
    return [{"rank": item[:-1], "suit": SUITS[item[-1]]} for item in text.split()]


def score(text):
    return core.evaluate_five_cards(cards(text))


# One hand per category, lowest category first, with its exact score.
CATEGORY_CASES = [
    ("AC QD 9H 6S 3C", (0, 14, 12, 9, 6, 3)),          # high card
    ("8C 8D AH 10S 3C", (1, 8, 14, 10, 3)),            # one pair
    ("QC QD 5H 5S 9C", (2, 12, 5, 9)),                 # two pair
    ("7C 7D 7H KS 2C", (3, 7, 13, 2)),                 # three of a kind
    ("10C 9D 8H 7S 6C", (4, 10)),                      # straight
    ("AH JH 8H 6H 2H", (5, 14, 11, 8, 6, 2)),          # flush
    ("10C 10D 10H 4S 4D", (6, 10, 4)),                 # full house
    ("9C 9D 9H 9S KD", (7, 9, 13)),                    # four of a kind
    ("9H 8H 7H 6H 5H", (8, 9)),                        # straight flush
]


class HandEvaluationTests(unittest.TestCase):
    def assertBeats(self, winner, loser):
        self.assertGreater(score(winner), score(loser), f"{winner} should beat {loser}")
        self.assertEqual(core.compare_scores(score(winner), score(loser)), 1)
        self.assertEqual(core.compare_scores(score(loser), score(winner)), -1)

    def test_every_category_scores_exactly(self):
        for text, expected in CATEGORY_CASES:
            with self.subTest(text):
                self.assertEqual(score(text), expected)
                self.assertEqual(core.HAND_NAMES[expected[0]],
                                 ["High Card", "Pair", "Two Pair", "Three of a Kind", "Straight",
                                  "Flush", "Full House", "Four of a Kind", "Straight Flush"][expected[0]])

    def test_categories_rank_in_order(self):
        for (low, _), (high, _) in zip(CATEGORY_CASES, CATEGORY_CASES[1:]):
            with self.subTest(f"{high} > {low}"):
                self.assertBeats(high, low)

    def test_royal_flush_is_the_ace_high_straight_flush(self):
        self.assertEqual(score("AS KS QS JS 10S"), (8, 14))
        self.assertEqual(core.describe_poker_score(score("AS KS QS JS 10S")), "Royal Flush")
        self.assertBeats("AS KS QS JS 10S", "KD QD JD 10D 9D")

    def test_wheel_straight_ranks_below_six_high(self):
        self.assertEqual(score("AC 2D 3H 4S 5C"), (4, 5))
        self.assertBeats("6C 5D 4H 3S 2C", "AC 2D 3H 4S 5C")
        self.assertBeats("AC 2D 3H 4S 5C", "KC KD KH 2S 3C")    # still a straight

    def test_wheel_straight_flush_ranks_below_six_high(self):
        self.assertEqual(score("5D 4D 3D 2D AD"), (8, 5))
        self.assertBeats("6D 5D 4D 3D 2D", "5D 4D 3D 2D AD")
        self.assertBeats("5D 4D 3D 2D AD", "AC AD AH AS KC")    # still beats four aces

    def test_broadway_is_the_highest_straight(self):
        self.assertEqual(score("AC KD QH JS 10C"), (4, 14))
        self.assertBeats("AC KD QH JS 10C", "KC QD JH 10S 9C")
        # An ace cannot wrap round the corner.
        self.assertEqual(score("QC KD AH 2S 3C")[0], 0)

    def test_high_card_kickers_compare_in_order(self):
        self.assertBeats("AC KD 9H 8S 5C", "AH KS 9D 8C 4D")    # fifth card
        self.assertBeats("AC KD 9H 8S 5C", "AD QC JH 10S 8C")   # second card beats the rest
        self.assertEqual(core.compare_scores(score("AC KD 9H 8S 5C"), score("AH KS 9D 8C 5D")), 0)

    def test_one_pair_kickers_compare_in_order(self):
        self.assertBeats("8C 8D AH 10S 3C", "8H 8S KH QS JC")   # first kicker
        self.assertBeats("8C 8D AH 10S 3C", "8H 8S AD 9C 7D")   # second kicker
        self.assertBeats("8C 8D AH 10S 4C", "8H 8S AD 10C 3D")  # third kicker
        self.assertBeats("9C 9D 2H 3S 4C", "8H 8S AD KC QD")    # the pair comes first

    def test_two_pair_compares_top_pair_then_low_pair_then_kicker(self):
        self.assertBeats("KC KD 2H 2S 3C", "QH QS JC JD AH")    # top pair
        self.assertBeats("QC QD 6H 6S 2C", "QH QS 5C 5D AH")    # low pair
        self.assertBeats("QC QD 5H 5S 9C", "QH QS 5C 5D 8H")    # kicker
        self.assertEqual(score("QC QD 5H 5S 9C"), (2, 12, 5, 9))

    def test_full_house_compares_the_trips_first(self):
        self.assertBeats("KC KD KH 2S 2C", "QC QD QH AS AC")
        self.assertBeats("KC KD KH 5S 5C", "KH KS KD 4S 4C")    # equal trips: the pair decides

    def test_flush_compares_every_card(self):
        self.assertBeats("AH JH 8H 6H 3H", "AS JS 8S 6S 2S")
        self.assertBeats("AH 4H 3H 2H 7H", "KS QS JS 9S 8S")

    def test_invalid_hands_score_none_and_lose(self):
        self.assertIsNone(core.evaluate_five_cards(cards("AS KS QS JS")))
        self.assertIsNone(core.evaluate_five_cards(cards("AS KS QS JS 10S 9S")))
        self.assertIsNone(core.evaluate_five_cards([*cards("AS KS QS JS"), None]))
        self.assertIsNone(core.evaluate_five_cards(None))
        self.assertEqual(core.compare_scores(None, score("2C 3D 4H 5S 7C")), -1)
        self.assertEqual(core.compare_scores(score("2C 3D 4H 5S 7C"), None), 1)
        self.assertEqual(core.compare_scores(None, None), 0)

    def test_holdem_method_core_and_niche_common_agree_on_seeded_hands(self):
        game = TexasHoldemGame()
        rng = random.Random("core-eval-agreement")
        for _ in range(5000):
            hand = rng.sample(DECK, 5)
            expected = core.evaluate_five_cards(hand)
            self.assertEqual(game.evaluate_five_cards(hand), expected)
            self.assertEqual(niche_common.evaluate_five_card_hand(hand), expected)

    def test_shared_names_are_the_core_objects(self):
        self.assertIs(holdem.RANK_VALUES, core.RANK_VALUES)
        self.assertIs(holdem.HAND_NAMES, core.HAND_NAMES)
        self.assertIs(niche_common.RANK_VALUES, core.RANK_VALUES)
        self.assertIs(niche_common.evaluate_five_card_hand, core.evaluate_five_cards)
        self.assertIs(niche_common.compare_scores, core.compare_scores)
        from solitaireplus.games.poker.five_card_draw import HAND_NAMES as draw_names, RANK_VALUES as draw_values
        from solitaireplus.games.poker.seven_card_stud import HAND_NAMES as stud_names, RANK_VALUES as stud_values
        self.assertIs(draw_names, core.HAND_NAMES)
        self.assertIs(stud_values, core.RANK_VALUES)
        self.assertIs(stud_names, draw_names)
        self.assertIs(draw_values, stud_values)

    def test_core_imports_no_project_module(self):
        # Multiplayer re-exports core.py through a shim, so it must stay import-free.
        tree = ast.parse((ROOT / "solitaireplus/games/poker/core.py").read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                self.assertEqual(node.level, 0, "relative import in core.py")
                names = [node.module]
            elif isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            else:
                continue
            for name in names:
                self.assertIn(name.split(".")[0], sys.stdlib_module_names, f"core.py imports {name}")


class BestHandTests(unittest.TestCase):
    def test_best_of_seven_picks_the_royal_flush(self):
        best_score, best_cards = core.evaluate_best_hand(cards("AH KH QH JH 2C 10H 3D"))
        self.assertEqual(best_score, (8, 14))
        self.assertEqual({(c["rank"], c["suit"]) for c in best_cards},
                         {(c["rank"], c["suit"]) for c in cards("AH KH QH JH 10H")})

    def test_best_of_seven_prefers_the_flush_to_the_straight(self):
        best_score, best_cards = core.evaluate_best_hand(cards("9H 8H 7C 6H 5D 2H KH"))
        self.assertEqual(best_score, (5, 13, 9, 8, 6, 2))
        self.assertTrue(all(card["suit"] == "Hearts" for card in best_cards))

    def test_best_of_seven_uses_the_best_kickers_and_pairs(self):
        self.assertEqual(core.evaluate_best_hand(cards("KC KD KH 5S 5C 5D 2H"))[0], (6, 13, 5))
        self.assertEqual(core.evaluate_best_hand(cards("QC QD 5H 5S 3C 3D AH"))[0], (2, 12, 5, 14))
        self.assertEqual(core.evaluate_best_hand(cards("AC 2D 3H 4S 5C 6D KH"))[0], (4, 6))

    def test_best_hand_is_the_maximum_over_every_five_card_combination(self):
        game = TexasHoldemGame()
        rng = random.Random("core-eval-best-of-seven")
        for size in (5, 6, 7):
            for _ in range(300):
                hand = rng.sample(DECK, size)
                with self.subTest(size=size, hand=hand):
                    best_score, best_cards = core.evaluate_best_hand(hand)
                    self.assertEqual(best_score, max(core.evaluate_five_cards(c) for c in combinations(hand, 5)))
                    self.assertEqual(len(best_cards), 5)
                    self.assertTrue(all(any(card is held for held in hand) for card in best_cards))
                    self.assertEqual(core.evaluate_five_cards(best_cards), best_score)
                    self.assertEqual(game.evaluate_best_hand(hand), (best_score, best_cards))

    def test_five_cards_return_themselves(self):
        hand = cards("AC QD 9H 6S 3C")
        self.assertEqual(core.evaluate_best_hand(hand), ((0, 14, 12, 9, 6, 3), hand))

    def test_fewer_than_five_cards_give_none(self):
        game = TexasHoldemGame()
        for size in range(5):
            with self.subTest(size=size):
                self.assertIsNone(core.evaluate_best_hand(DECK[:size]))
                self.assertIsNone(game.evaluate_best_hand(DECK[:size]))


class SeatViewTests(unittest.TestCase):
    """The seat views agree with each engine's own index helpers at every step of real hands."""

    STACKS = (3, 8, 20, 60, 400, 1000)

    def play(self, key, check, hands=40, seed="seat-views"):
        adapter = ADAPTERS_BY_KEY[key]
        rng = random.Random(f"{seed}-{key}")
        played = 0
        while played < hands:
            choices = [value for value in self.STACKS if value >= adapter.minimum_stack()]
            game = adapter.new_game(rng, [rng.choice(choices) for _ in range(adapter.seat_count)])
            while played < hands and not adapter.session_over(game):
                if not adapter.start_hand(game):
                    break
                check(game, "start")
                for _ in range(3000):
                    if adapter.hand_complete(game):
                        break
                    label = adapter.step(game, rng)
                    check(game, label)
                else:
                    self.fail(f"{key}: hand did not finish")
                check(game, "end")
                played += 1

    def check_holdem_family(self, game, label):
        where = f"hand {game.hand_number} after {label}"
        self.assertEqual(game.seat_count(), len(game.npcs) + 1, where)
        self.assertEqual(game.seat_stacks(), [game.player_stack, *game.npc_stacks], where)
        self.assertEqual(game.seat_round_bets(), [game.player_round_bet, *game.npc_round_bets], where)
        self.assertEqual(game.seat_has_acted(), [game.player_has_acted, *game.npc_has_acted], where)
        in_hand, can_act = game.seat_in_hand(), game.seat_can_act()
        self.assertEqual(len(in_hand), game.seat_count(), where)
        self.assertEqual(len(can_act), game.seat_count(), where)
        self.assertEqual([seat for seat, flag in enumerate(in_hand) if flag], game.get_active_player_indexes(), where)
        self.assertEqual([seat for seat, flag in enumerate(can_act) if flag],
                         game.get_actionable_player_indexes(), where)

    def test_holdem_seat_views_match_index_helpers(self):
        self.play("texas_holdem", self.check_holdem_family)

    def test_five_card_draw_seat_views_match_index_helpers(self):
        self.play("five_card_draw", self.check_holdem_family)

    def test_seven_card_stud_seat_views_match_index_helpers(self):
        self.play("seven_card_stud", self.check_holdem_family)

    def test_holdem_family_seat_views_cover_busted_and_folded_seats(self):
        game = TexasHoldemGame()
        game.start_session([{"id": f"npc{i}", "name": f"N{i}"} for i in range(4)], 1000, 10)
        game.npc_stacks[1] = 0
        self.assertTrue(game.start_hand())
        game.player_folded = True
        game.npc_stacks[2] = 0                     # all-in: still in the hand, cannot act
        self.assertEqual(game.seat_in_hand(), [False, True, False, True, True])
        self.assertEqual(game.seat_can_act(), [False, True, False, False, True])
        self.assertEqual(game.get_active_player_indexes(), [1, 3, 4])
        self.assertEqual(game.get_actionable_player_indexes(), [1, 4])

    def check_blind_mans_bluff(self, game, label):
        where = f"hand {game.hand_number} after {label}"
        self.assertEqual(game.seat_stacks(), [game._stack_for(seat) for seat in range(len(game.npcs) + 1)], where)
        in_hand = game.seat_in_hand()
        self.assertEqual(len(in_hand), len(game.cards), where)
        self.assertEqual([seat for seat, flag in enumerate(in_hand) if flag], game.get_active_indexes(), where)

    def test_blind_mans_bluff_seat_views_match_index_helpers(self):
        self.play("blind_mans_bluff", self.check_blind_mans_bluff, hands=80)

    def test_blind_mans_bluff_seat_out_busted_stack_is_not_in_hand(self):
        # B86 group 4: a seat below the ante now antes all it has and plays all-in, so only
        # a seat with 0 chips sits out.
        adapter = ADAPTERS_BY_KEY["blind_mans_bluff"]
        game = adapter.new_game(random.Random(3), [1000, 0, 1000, 1000])   # seat 1 is busted
        self.assertEqual(game.seat_in_hand(), [])
        self.assertTrue(adapter.start_hand(game))
        self.assertFalse(game.seat_in_hand()[1])
        self.assertEqual(len(game.seat_in_hand()), 4)
        game = adapter.new_game(random.Random(3), [1000, 1, 1000, 1000])   # seat 1 is below the ante
        self.assertTrue(adapter.start_hand(game))
        self.assertTrue(game.seat_in_hand()[1])

    def check_five_o(self, game, label):
        where = f"hand {game.hand_number} after {label}"
        self.assertEqual(game.npcs, [game.npc], where)
        self.assertEqual(game.seat_stacks(), [game.player_stack, game.npc_stack], where)
        self.assertEqual(game.seat_round_bets(), [game.player_betting_paid, game.npc_betting_paid], where)
        self.assertEqual(game.seat_in_hand(), [not game.player_folded, not game.npc_folded], where)
        if game.pot:
            # Until the pot is paid out it holds exactly what both seats put in.
            self.assertEqual(sum(game.hand_contributions), game.pot, where)
            self.assertEqual([self.five_o_stacks_before[seat] - game.seat_stacks()[seat] for seat in (0, 1)],
                             game.hand_contributions, where)
        self.assertGreaterEqual(game.hand_contributions[0], game.player_betting_paid, where)
        self.assertGreaterEqual(game.hand_contributions[1], game.npc_betting_paid, where)

    def test_five_o_seat_views_and_hand_contributions(self):
        adapter = ADAPTERS_BY_KEY["five_o_poker"]
        rng = random.Random("seat-views-five_o")
        game = adapter.new_game(rng, [400, 400])
        self.assertEqual(game.hand_contributions, [0, 0])
        for _ in range(25):
            if adapter.session_over(game):
                break
            self.five_o_stacks_before = game.seat_stacks()
            self.assertTrue(adapter.start_hand(game))
            self.assertEqual(game.hand_contributions, [game.ante, game.ante])   # reset, then the antes
            self.check_five_o(game, "start")
            while not adapter.hand_complete(game):
                label = adapter.step(game, rng)
                self.check_five_o(game, label)

    def test_five_o_contribution_counts_only_the_chips_actually_paid(self):
        adapter = ADAPTERS_BY_KEY["five_o_poker"]
        game = adapter.new_game(random.Random(5), [400, 400])
        self.assertTrue(adapter.start_hand(game))
        game.player_stack, game.npc_stack = 7, 3
        self.assertEqual(game._commit_player(50), 7)
        self.assertEqual(game._commit_npc(50), 3)
        self.assertEqual(game.hand_contributions, [game.ante + 7, game.ante + 3])

    def test_five_o_npcs_is_empty_without_an_opponent(self):
        game = FiveOPokerGame(random.Random(1))
        self.assertEqual(game.npcs, [])
        self.assertEqual(game.seat_stacks(), [0, 0])
        self.assertEqual(game.hand_contributions, [0, 0])


if __name__ == "__main__":
    unittest.main()
