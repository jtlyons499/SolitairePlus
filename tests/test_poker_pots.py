"""Shared pot resolution in every poker variant (B86 group 2).

Covers B37 (a pot layer nobody live paid into), B38 (odd chips start left of the dealer), B42
(Blind Man's Bluff tie counting), NEW-1 (uncalled chips are returned, not won), NEW-2
(last_resolved_pot and the per-hand records), NEW-7 (Draw and Stud gave the dealer the first odd
chip) and NEW-8 (the Hold'em win achievement recomputed the human's share by the old rule).

B86 review: F3 (a contested pot, with two or more eligible seats, counts as winning a hand; a
pot a seat collected uncontested counts only when the seat made money on the hand, otherwise it
still pays the seat but is not a win), F4 (cash-win fans are paid on the human's net for the
hand, as every casino game pays them), F10 (a second resolve_showdown pays nothing) and F13 (the
pot history's grammar).

The pure core.py functions are tested directly. Every table rule is then checked in every
variant through the adapters in tests/support/poker_variants.py; a variant where a rule cannot
happen asserts the rule it keeps instead.
"""
import random
import unittest
from types import SimpleNamespace
from unittest import mock

from solitaireplus.app import state
from solitaireplus.games.poker import five_card_draw_screen, holdem_screen, recap, seven_card_stud_screen
from solitaireplus.games.poker.core import (
    award_pots,
    build_pots,
    hand_nets,
    hand_outcome,
    hand_winners,
    odd_chip_order,
    settle_fold_win,
    split_pot,
)
from tests.support.poker_screens import ScreenHarness
from tests.support.poker_variants import ADAPTERS, ADAPTERS_BY_KEY, FORCED_STACK

RECORD_KEYS = {"amount", "eligible", "winners", "payouts", "share", "remainder", "hand"}
HOLDEM_FAMILY = ("texas_holdem", "five_card_draw", "seven_card_stud")
MULTI_SEAT = [adapter for adapter in ADAPTERS if adapter.seat_count > 2]
FIVE_O = ADAPTERS_BY_KEY["five_o_poker"]


def clockwise_after(dealer, seats, seat_count):
    """Independent statement of the odd-chip order: walk clockwise from the dealer's left."""
    return [(dealer + step) % seat_count for step in range(1, seat_count + 1)
            if (dealer + step) % seat_count in seats]


def gains(adapter, game):
    return [stack - FORCED_STACK for stack in adapter.stacks(game)]


def seat_name(game, seat):
    if hasattr(game, "get_table_player_name"):
        return game.get_table_player_name(seat)
    if hasattr(game, "get_name"):
        return game.get_name(seat)
    return "You" if seat == 0 else game.get_npc_name()


def new_game(adapter, seed=1):
    return adapter.new_game(random.Random(f"pots-{adapter.key}-{seed}"))


# ==================================================
# PURE CORE FUNCTIONS
# ==================================================

class BuildPotsTests(unittest.TestCase):
    def test_random_cases_conserve_chips_and_follow_the_layer_rules(self):
        rng = random.Random("build-pots")
        for case in range(2000):
            seats = rng.randint(2, 6)
            contributions = [rng.choice((0, rng.randint(0, 1000), rng.choice((5, 10, 50, 100, 1000))))
                             for _ in range(seats)]
            live = [rng.random() < 0.6 for _ in range(seats)]
            where = f"case {case}: contributions {contributions}, live {live}"
            pots, refunds = build_pots(contributions, live)

            self.assertEqual(sum(pot["amount"] for pot in pots) + sum(refunds.values()),
                             sum(contributions), where)

            # Refunds come only from single-contributor or no-eligible layers, exactly.
            expected_refunds, previous = {}, 0
            for level in sorted({amount for amount in contributions if amount > 0}):
                contributors = [seat for seat, amount in enumerate(contributions) if amount >= level]
                if len(contributors) == 1 or not any(live[seat] for seat in contributors):
                    for seat in contributors:
                        expected_refunds[seat] = expected_refunds.get(seat, 0) + level - previous
                previous = level
            self.assertEqual(refunds, expected_refunds, where)

            for index, pot in enumerate(pots):
                self.assertGreater(pot["amount"], 0, where)
                self.assertGreaterEqual(len(pot["contributors"]), 2, where)
                self.assertGreaterEqual(len(pot["eligible"]), 1, where)
                self.assertLessEqual(set(pot["eligible"]), set(pot["contributors"]), where)
                self.assertTrue(all(live[seat] for seat in pot["eligible"]), where)
                if index:
                    self.assertNotEqual(pot["eligible"], pots[index - 1]["eligible"], where)
                    # Side pots only ever narrow: a seat cannot win a higher pot without the lower.
                    self.assertLess(set(pot["eligible"]), set(pots[index - 1]["eligible"]), where)

    def test_uncalled_top_layer_is_a_refund(self):
        pots, refunds = build_pots([100, 300, 100], [True, True, True])
        self.assertEqual(pots, [{"amount": 300, "contributors": [0, 1, 2], "eligible": [0, 1, 2]}])
        self.assertEqual(refunds, {1: 200})

    def test_dead_money_layers_merge_into_one_pot(self):
        pots, refunds = build_pots([10, 50, 50, 30], [False, True, True, False])
        self.assertEqual(pots, [{"amount": 140, "contributors": [0, 1, 2, 3], "eligible": [1, 2]}])
        self.assertEqual(refunds, {})

    def test_a_layer_with_no_eligible_seat_goes_back_to_its_contributors(self):
        pots, refunds = build_pots([3, 5, 10, 10], [True, True, False, False])
        self.assertEqual(pots, [{"amount": 12, "contributors": [0, 1, 2, 3], "eligible": [0, 1]},
                                {"amount": 6, "contributors": [1, 2, 3], "eligible": [1]}])
        self.assertEqual(refunds, {2: 5, 3: 5})

    def test_nothing_in_gives_no_pots(self):
        self.assertEqual(build_pots([0, 0, 0], [True, True, False]), ([], {}))

    def test_a_seat_past_the_live_list_is_not_live(self):
        pots, refunds = build_pots([10, 10, 10], [True, True])
        self.assertEqual(pots[0]["eligible"], [0, 1])
        self.assertEqual(refunds, {})


class OddChipTests(unittest.TestCase):
    def test_order_starts_left_of_the_dealer_and_ends_with_the_dealer(self):
        self.assertEqual(odd_chip_order([0, 1, 2, 3, 4], 2, 5), [3, 4, 0, 1, 2])
        self.assertEqual(odd_chip_order([4, 1], 4, 5), [1, 4])
        self.assertEqual(odd_chip_order([0, 3], 3, 4), [0, 3])

    def test_order_wraps_round_the_table(self):
        self.assertEqual(odd_chip_order([1, 3], 2, 4), [3, 1])
        self.assertEqual(odd_chip_order([0, 2], 3, 4), [0, 2])

    def test_no_dealer_means_seat_zero_first(self):
        self.assertEqual(odd_chip_order([2, 0, 1], None, 3), [0, 1, 2])

    def test_repeated_seats_appear_once(self):
        self.assertEqual(odd_chip_order([1, 1, 0], 0, 3), [1, 0])

    def test_split_pot_gives_odd_chips_one_each_in_order(self):
        payouts = split_pot(25, [1, 3], 2, 5)
        self.assertEqual(list(payouts), [3, 1])
        self.assertEqual(payouts, {3: 13, 1: 12})
        self.assertEqual(split_pot(11, [0, 1, 2], 0, 3), {1: 4, 2: 4, 0: 3})
        self.assertEqual(split_pot(9, [0, 1, 2], 0, 3), {1: 3, 2: 3, 0: 3})
        self.assertEqual(split_pot(7, [2], 0, 3), {2: 7})

    def test_split_pot_always_sums_to_the_amount(self):
        rng = random.Random("split-pot")
        for _ in range(2000):
            seat_count = rng.randint(2, 9)
            winners = rng.sample(range(seat_count), rng.randint(1, seat_count))
            dealer = rng.choice([None, *range(seat_count)])
            amount = rng.randint(0, 5000)
            payouts = split_pot(amount, winners, dealer, seat_count)
            self.assertEqual(sum(payouts.values()), amount)
            self.assertEqual(list(payouts), odd_chip_order(winners, dealer, seat_count))
            share, remainder = divmod(amount, len(winners))
            self.assertEqual(list(payouts.values()), [share + (index < remainder) for index in range(len(winners))])

    def test_split_pot_needs_a_winner(self):
        with self.assertRaises(ValueError):
            split_pot(10, [], 0, 3)


class AwardPotsTests(unittest.TestCase):
    def test_each_pot_goes_to_its_best_eligible_hand(self):
        pots, _ = build_pots([50, 100, 100, 100], [True, True, True, False])
        awards, totals = award_pots(pots, {0: (9,), 1: (5,), 2: (5,)}, 0, 4, describe=lambda score: f"rank {score[0]}")
        self.assertEqual(len(awards), 2)
        main, side = awards
        self.assertEqual(set(main), RECORD_KEYS)
        self.assertEqual((main["amount"], main["winners"], main["payouts"], main["hand"]), (200, [0], {0: 200}, "rank 9"))
        self.assertEqual((side["amount"], side["winners"], side["payouts"]), (150, [1, 2], {1: 75, 2: 75}))
        self.assertEqual((side["share"], side["remainder"], side["eligible"]), (75, 0, [1, 2]))
        self.assertEqual(totals, {0: 200, 1: 75, 2: 75})

    def test_odd_chips_and_hand_text(self):
        pots, _ = build_pots([5, 5, 5], [True, True, True])
        awards, totals = award_pots(pots, {0: (3,), 1: (3,), 2: (1,)}, 0, 3)
        self.assertEqual(awards[0]["winners"], [1, 0])
        self.assertEqual(awards[0]["payouts"], {1: 8, 0: 7})
        self.assertEqual((awards[0]["share"], awards[0]["remainder"], awards[0]["hand"]), (7, 1, ""))
        self.assertEqual(totals, {1: 8, 0: 7})

    def test_only_scored_seats_can_win(self):
        pots = [{"amount": 10, "contributors": [0, 1], "eligible": [0, 1]}]
        awards, totals = award_pots(pots, {1: (1,)}, None, 2)
        self.assertEqual((awards[0]["winners"], awards[0]["eligible"], totals), ([1], [1], {1: 10}))
        with self.assertRaises(ValueError):
            award_pots(pots, {2: (5,)}, None, 3)


def entitlement(contributions, seat):
    """The most `seat` can get back from a hand: its own chips plus, from every other seat,
    what it matched of that seat's contribution."""
    own = contributions[seat]
    return own + sum(min(own, other) for index, other in enumerate(contributions) if index != seat)


class SettleFoldWinTests(unittest.TestCase):
    def test_the_winner_own_uncalled_chips_are_a_refund(self):
        # B86 polish P1: a fold win is settled like a showdown with one live seat. The
        # winner wins the pot of matched chips; its own uncalled chips go back to it.
        self.assertEqual(settle_fold_win([20, 60], 1), (40, {1: 40}))
        # A 1,000 shove that blinds of 10 and 20 fold to: the big blind's 20 matches the
        # first 20 of the shove, so the pot is 50 and 980 goes back (not "win $1,030").
        self.assertEqual(settle_fold_win([1000, 10, 20], 0), (50, {0: 980}))
        # A winner matched by a folded seat has nothing uncalled.
        self.assertEqual(settle_fold_win([10, 20, 20, 0, 5], 2), (55, {}))

    def test_chips_the_winner_never_matched_go_back(self):
        # Review repro: the human's small blind 10 against a big blind all-in for 5.
        self.assertEqual(settle_fold_win([10, 5, 0], 1), (10, {0: 5}))
        # The 1-chip big blind of the property run wins 2, not 11.
        self.assertEqual(settle_fold_win([0, 0, 0, 10, 1], 4), (2, {3: 9}))
        self.assertEqual(settle_fold_win([0, 10, 3, 0, 0], 2), (6, {1: 7}))
        # Two folded seats above the winner: each gets its own excess back.
        self.assertEqual(settle_fold_win([20, 5, 20, 0], 1), (15, {0: 15, 2: 15}))

    def test_random_cases_conserve_chips_and_respect_what_was_matched(self):
        rng = random.Random("settle-fold-win")
        for _ in range(3000):
            seats = rng.randint(2, 6)
            contributions = [rng.choice((0, 0, 1, 3, 5, 10, 20, 40)) for _ in range(seats)]
            winner = rng.randrange(seats)
            winnings, refunds = settle_fold_win(contributions, winner)
            self.assertEqual(winnings + sum(refunds.values()), sum(contributions))
            self.assertLessEqual(winnings + refunds.get(winner, 0), entitlement(contributions, winner),
                                 contributions)
            # The winner always gets back at least its own chips, as pot or refund.
            self.assertGreaterEqual(winnings + refunds.get(winner, 0), contributions[winner])
            others = [amount for seat, amount in enumerate(contributions) if seat != winner]
            # Its refund is exactly what no other seat matched.
            self.assertEqual(refunds.get(winner, 0), max(0, contributions[winner] - max(others, default=0)))
            for seat, amount in refunds.items():
                # A folded seat only gets back chips the winner did not match.
                if seat != winner:
                    self.assertLessEqual(amount, contributions[seat] - min(contributions[seat], contributions[winner]))
            # Exactly a showdown with the winner as the only live hand.
            pots, showdown_refunds = build_pots(contributions, [seat == winner for seat in range(seats)])
            self.assertEqual(winnings, sum(pot["amount"] for pot in pots))
            self.assertEqual(refunds, showdown_refunds)


class HandOutcomeTests(unittest.TestCase):
    @staticmethod
    def awards(*winner_lists):
        return [{"amount": 10, "winners": list(winners)} for winners in winner_lists]

    def test_won_main_and_lost_side_is_a_win(self):
        self.assertEqual(hand_outcome(self.awards([0], [2]), 0), "won")

    def test_split_main_only_is_a_tie(self):
        self.assertEqual(hand_outcome(self.awards([0, 2], [2]), 0), "tied")
        self.assertEqual(hand_outcome(self.awards([0, 2]), 0), "tied")

    def test_short_npc_wins_main_and_player_wins_side_is_a_win(self):
        self.assertEqual(hand_outcome(self.awards([1], [0]), 0), "won")

    def test_tied_main_and_won_side_is_a_win(self):
        self.assertEqual(hand_outcome(self.awards([0, 1], [0]), 0), "won")

    def test_nothing_won_is_a_loss(self):
        self.assertEqual(hand_outcome(self.awards([1], [2]), 0), "lost")
        self.assertEqual(hand_outcome([], 0), "lost")

    def test_a_pot_only_collected_uncontested_is_not_a_win(self):
        # F3: seat 1 won the contested main pot; the human only collected a side pot nobody
        # else could win (its own excess plus folded seats' dead money).
        awards = [{"amount": 248, "eligible": [0, 1], "winners": [1]},
                  {"amount": 20, "eligible": [0], "winners": [0]}]
        self.assertEqual(hand_outcome(awards, 0), "lost")
        self.assertEqual(hand_outcome(awards, 1), "won")
        self.assertEqual(hand_winners(awards), [1])
        # A contested side pot still counts.
        awards[1]["eligible"] = [0, 2]
        self.assertEqual(hand_outcome(awards, 0), "won")
        self.assertEqual(hand_winners(awards), [0, 1])

    def test_a_fold_win_is_a_win(self):
        # Everyone else folded: the one pot has only the winner eligible, and it is the win.
        awards = [{"amount": 80, "eligible": [1], "winners": [1]}]
        self.assertEqual(hand_outcome(awards, 1), "won")
        self.assertEqual(hand_outcome(awards, 0), "lost")
        self.assertEqual(hand_winners(awards), [1])

    def test_hand_nets_are_what_each_seat_got_back_minus_what_it_put_in(self):
        awards = [{"amount": 300, "eligible": [0, 1], "winners": [1], "payouts": {1: 300}},
                  {"amount": 600, "eligible": [0], "winners": [0], "payouts": {0: 600}}]
        nets = hand_nets([500, 100, 400, 0], awards, {0: 100})
        self.assertEqual(nets, {0: 200, 1: 200, 2: -400, 3: 0})
        self.assertEqual(sum(nets.values()), 0)

    def test_an_uncontested_pot_is_a_win_when_the_seat_made_money(self):
        # F3 review: seat 1 is all-in and wins the main pot; seat 2 folds its 400 to the
        # human's bet, so the human takes the side pot (seat 2's money) and is up 200. The
        # same fold heads-up is a fold win, so this is a win too.
        awards = [{"amount": 300, "eligible": [0, 1], "winners": [1], "payouts": {1: 300}},
                  {"amount": 600, "eligible": [0], "winners": [0], "payouts": {0: 600}}]
        nets = hand_nets([500, 100, 400], awards, {0: 100})
        self.assertEqual(hand_outcome(awards, 0, nets), "won")
        self.assertEqual(hand_outcome(awards, 1, nets), "won")
        self.assertEqual(hand_outcome(awards, 2, nets), "lost")
        self.assertEqual(hand_winners(awards, nets), [0, 1])
        # Without the nets such a pot is only collected.
        self.assertEqual(hand_winners(awards), [1])

    def test_an_uncontested_pot_is_not_a_win_when_the_seat_lost_money(self):
        # The earlier F3 case: the human gets back 20 + 10 of the 100 it put in.
        awards = [{"amount": 248, "eligible": [0, 1], "winners": [1], "payouts": {1: 248}},
                  {"amount": 20, "eligible": [0], "winners": [0], "payouts": {0: 20}}]
        nets = hand_nets([100, 80, 90, 8], awards, {0: 10})
        self.assertEqual(nets[0], -70)
        self.assertEqual(hand_outcome(awards, 0, nets), "lost")
        self.assertEqual(hand_winners(awards, nets), [1])

    def test_a_tied_main_pot_and_a_profitable_uncontested_side_pot_is_a_win(self):
        # Doing better in the main pot (a tie rather than a loss) never gives a worse result.
        awards = [{"amount": 300, "eligible": [0, 1], "winners": [0, 1], "payouts": {0: 150, 1: 150}},
                  {"amount": 600, "eligible": [0], "winners": [0], "payouts": {0: 600}}]
        nets = hand_nets([500, 100, 400], awards, {0: 100})
        self.assertEqual(hand_outcome(awards, 0, nets), "won")
        self.assertEqual(hand_outcome(awards, 1, nets), "tied")


# ==================================================
# EVERY VARIANT
# ==================================================

# The human (100, live, weakest) collects a 20 side pot only folded seat 2 also paid towards;
# seat 1 (80, live, best) wins the 248 main pot. The human's net is -70.
UNCONTESTED_SIDE_POT_CASE = ([100, 80, 90, 8], [True, True, False, False], [5, 14, 2, 2])


def odd_chip_case(seat_count, dealer, winners, folded):
    """Contributions where the single pot leaves len(winners) - 1 odd chips.

    Live seats put in 7; the folded seat's dead money is chosen to make the remainder.
    """
    for dead in range(1, 7):
        contributions = [dead if seat == folded else 7 for seat in range(seat_count)]
        if sum(contributions) % len(winners) == len(winners) - 1:
            break
    live = [seat != folded for seat in range(seat_count)]
    ranks = [14 if seat in winners else 5 for seat in range(seat_count)]
    return contributions, live, ranks


class VariantPotTests(unittest.TestCase):
    def test_every_variant_is_covered(self):
        self.assertEqual({adapter.key for adapter in ADAPTERS},
                         {*HOLDEM_FAMILY, "five_o_poker", "blind_mans_bluff"})
        self.assertEqual([adapter.key for adapter in ADAPTERS if adapter.seat_count == 2], ["five_o_poker"])

    # (a) B38 / NEW-7 ------------------------------------------------------------------------

    def test_odd_chips_go_to_the_first_tied_winner_left_of_the_dealer(self):
        for adapter in MULTI_SEAT:
            count = adapter.seat_count
            for dealer in range(count):
                configs = (
                    # the dealer ties with the seat two to its left; the seat between has folded
                    ({dealer, (dealer + 2) % count}, (dealer + 1) % count),
                    # a three-way tie with two odd chips
                    ({dealer, (dealer + 1) % count, (dealer + 3) % count}, (dealer + 2) % count),
                )
                for winners, folded in configs:
                    with self.subTest(adapter.key, dealer=dealer, winners=sorted(winners)):
                        contributions, live, ranks = odd_chip_case(count, dealer, winners, folded)
                        game = adapter.force_showdown(new_game(adapter), contributions, live, ranks, dealer)
                        pot = sum(contributions)
                        order = clockwise_after(dealer, winners, count)
                        share, remainder = divmod(pot, len(winners))
                        self.assertEqual(remainder, len(winners) - 1)
                        expected = {seat: share + (index < remainder) for index, seat in enumerate(order)}
                        self.assertEqual(order[-1], dealer)   # the dealer is last
                        self.assertEqual(gains(adapter, game),
                                         [expected.get(seat, 0) for seat in range(count)])
                        [award] = adapter.awards(game)
                        self.assertEqual(award["winners"], order)
                        self.assertEqual(award["payouts"], expected)
                        self.assertEqual(adapter.refunds(game), {})
                        self.assertEqual(sorted(adapter.winners(game)), sorted(winners))

    def test_five_o_split_pot_odd_chip_goes_to_the_opener(self):
        # Five-O's pots are even (equal antes and called bets), so its odd chip is theoretical;
        # the kept rule is an exact split, and a stray odd chip goes to the opener.
        for dealer in (0, 1):
            opener = 1 - dealer
            with self.subTest(dealer=dealer):
                game = FIVE_O.force_showdown(new_game(FIVE_O), [5, 5], [True, True], [9, 9], dealer)
                self.assertEqual(gains(FIVE_O, game), [5, 5])
                self.assertEqual(game.last_winner, "tie")
                game = FIVE_O.force_showdown(new_game(FIVE_O), [5, 5], [True, True], [9, 9], dealer, pot=11)
                self.assertEqual(game.opening_index, opener)
                self.assertEqual(gains(FIVE_O, game), [6 if seat == opener else 5 for seat in (0, 1)])
                [award] = game.last_pot_awards
                self.assertEqual(award["winners"], [opener, dealer])
                self.assertEqual(award["payouts"], {opener: 6, dealer: 5})

    # (b) NEW-1 -------------------------------------------------------------------------------

    def test_uncalled_chips_are_returned_not_won(self):
        for adapter in MULTI_SEAT:
            count = adapter.seat_count
            for over_bettor, winner, caller in ((2, 0, 1), (0, 1, 2)):
                with self.subTest(adapter.key, over_bettor=over_bettor):
                    contributions = [0] * count
                    contributions[over_bettor], contributions[winner], contributions[caller] = 300, 100, 100
                    live = [amount > 0 for amount in contributions]
                    ranks = [5] * count
                    ranks[winner], ranks[caller] = 14, 9
                    game = adapter.force_showdown(new_game(adapter), contributions, live, ranks, count - 1)
                    name = seat_name(game, over_bettor)

                    expected = [0] * count
                    expected[winner], expected[over_bettor] = 300, 200
                    self.assertEqual(gains(adapter, game), expected)
                    self.assertEqual(adapter.refunds(game), {over_bettor: 200})
                    self.assertEqual(adapter.winners(game), [winner])
                    for award in adapter.awards(game):
                        self.assertNotIn(over_bettor, award["winners"])
                        self.assertNotIn(over_bettor, award["payouts"])
                    payout_text = game.result_text.split(" Uncalled ")[0]
                    self.assertNotIn(f"{name} $", payout_text)
                    self.assertNotIn(f"{name} win", payout_text)

                    returned = "you" if over_bettor == 0 else name
                    if adapter.key in HOLDEM_FAMILY:
                        refunds = [event for event in game.get_hand_history_events()
                                   if event["type"] == "refund" and event["hand_number"] == game.hand_number]
                        self.assertEqual([(event["text"], event["actor_index"], event["amount"]) for event in refunds],
                                         [(f"Uncalled $200 returned to {returned}.", over_bettor, 200)])
                        [result] = [event for event in game.get_hand_history_events()
                                    if event["type"] == "result" and event["hand_number"] == game.hand_number]
                        self.assertEqual(result["winners"], [winner])
                        self.assertEqual(result["payouts"], {winner: 300})
                    else:
                        self.assertTrue(game.result_text.endswith(f" Uncalled $200 returned to {returned}."),
                                        game.result_text)

    def test_five_o_showdowns_never_have_uncalled_chips(self):
        game = FIVE_O.force_showdown(new_game(FIVE_O), [40, 40], [True, True], [14, 3], 1)
        self.assertEqual(game.last_refunds, {})
        self.assertEqual(gains(FIVE_O, game), [80, 0])
        # A fold leaves the winner's last bet uncalled: it goes back (P1), stacks as before.
        game = FIVE_O.force_fold_win(new_game(FIVE_O), [5, 25], 1)
        self.assertEqual(game.last_refunds, {1: 20})
        self.assertEqual(gains(FIVE_O, game), [0, 30])

    def test_a_fold_win_returns_the_winner_own_uncalled_chips(self):
        # B86 polish P1: settled like a showdown with one live seat. The winner's 40 that
        # nobody matched is a refund; it wins the 40 pot of matched chips. Stacks end as
        # before (it gets all 80 back), but the result, pot record and recap say $40.
        for adapter in ADAPTERS:
            for winner in (0, 1):
                with self.subTest(adapter.key, winner=winner):
                    contributions = [0] * adapter.seat_count
                    contributions[winner], contributions[1 - winner] = 60, 20
                    game = adapter.force_fold_win(new_game(adapter), contributions, winner)
                    expected = [0, 0]
                    expected[winner] = 80
                    self.assertEqual(gains(adapter, game)[:2], expected)
                    self.assertEqual(adapter.refunds(game), {winner: 40})
                    self.assertEqual(adapter.winners(game), [winner])
                    [award] = adapter.awards(game)
                    self.assertEqual(set(award), RECORD_KEYS)
                    self.assertEqual((award["amount"], award["winners"], award["payouts"]),
                                     (40, [winner], {winner: 40}))
                    self.assertEqual((award["share"], award["remainder"], award["hand"]), (40, 0, ""))
                    self.assertEqual(game.last_resolved_pot, 40)
                    self.assertEqual(adapter.pot(game), 0)
                    name = seat_name(game, winner)
                    owner = "you" if winner == 0 else name
                    self.assertIn("You win $40" if winner == 0 else f"{name} wins $40", game.result_text)
                    self.assertNotIn("$80", game.result_text)
                    self.assertNotIn("You wins", game.result_text)
                    if adapter.key in HOLDEM_FAMILY:
                        events = [event for event in game.get_hand_history_events()
                                  if event["hand_number"] == game.hand_number
                                  and event["type"] in ("refund", "result")]
                        self.assertEqual([(event["type"], event["text"]) for event in events],
                                         [("refund", f"Uncalled $40 returned to {owner}."),
                                          ("result", game.result_text)])
                        self.assertEqual(events[1]["amount"], 40)
                    elif adapter is FIVE_O:
                        # Every Five-O fold leaves the winner's bet uncalled: said briefly.
                        self.assertTrue(game.result_text.endswith(" $40 (uncalled $40 returned)."),
                                        game.result_text)
                    else:
                        self.assertTrue(game.result_text.endswith(f" Uncalled $40 returned to {owner}."),
                                        game.result_text)

    def test_a_fold_win_returns_chips_the_winner_never_matched(self):
        # Review finding: the last seat left is a short all-in. It wins what it matched from
        # each seat; the rest goes back to whoever put it in, as at a showdown.
        cases = (
            # (contributions, winner, gains, refunds); seats past the list put in nothing
            ([10, 5], 1, [5, 10], {0: 5}),
            ([20, 5, 20], 1, [15, 15, 15], {0: 15, 2: 15}),
            ([0, 10, 1], 2, [0, 9, 2], {1: 9}),
        )
        for adapter in ADAPTERS:
            for contributions, winner, expected, refunds in cases:
                if len(contributions) > adapter.seat_count:
                    continue   # Five-O is heads-up
                padding = [0] * (adapter.seat_count - len(contributions))
                contributions, expected = contributions + padding, expected + padding
                with self.subTest(adapter.key, contributions=contributions):
                    game = adapter.force_fold_win(new_game(adapter), contributions, winner)
                    won = expected[winner]
                    self.assertEqual(gains(adapter, game), expected)
                    self.assertEqual(adapter.refunds(game), refunds)
                    self.assertEqual(adapter.winners(game), [winner])
                    [award] = adapter.awards(game)
                    self.assertEqual(set(award), RECORD_KEYS)
                    self.assertEqual((award["amount"], award["winners"], award["payouts"]), (won, [winner], {winner: won}))
                    self.assertEqual(game.last_resolved_pot, won)
                    self.assertEqual(adapter.pot(game), 0)
                    for seat in range(adapter.seat_count):
                        self.assertLessEqual(gains(adapter, game)[seat], entitlement(contributions, seat))
                    name = seat_name(game, winner)
                    self.assertIn(f"{'win' if winner == 0 else name + ' wins'} ${won:,}", game.result_text)

    def test_a_short_all_in_big_blind_left_alone_by_the_folds_wins_only_what_it_matched(self):
        # The review repro in real play: the human posts the small blind (10), the big blind is
        # all-in for 5 and keeps the nominal 20 (B39); everyone else folds. The human's 10
        # already covers the big blind's 5 (core.bet_to_match, B86 review F1), so it is not
        # asked to call or fold: the hand runs out and the big blind can win only what it
        # matched, 5 from the human; the human's other 5 goes back uncalled.
        for key in ("texas_holdem", "five_card_draw"):
            adapter = ADAPTERS_BY_KEY[key]
            with self.subTest(key):
                game = new_game(adapter)
                stacks = [FORCED_STACK, 5, FORCED_STACK, FORCED_STACK, FORCED_STACK]
                self.assertTrue(adapter.deal_forced_bets(game, stacks, dealer_seat=4))
                self.assertEqual(adapter.contributions(game), [10, 5, 0, 0, 0])
                self.assertEqual(game.current_bet, 20)
                total = adapter.total_chips(game)
                for seat in (2, 3, 4):
                    self.assertEqual(game.current_actor, seat)
                    adapter.npc_turn(game, seat, "fold")
                self.assertEqual(game.current_bet, 5)
                self.assertNotEqual(game.current_actor, 0)
                self.assertTrue(game.is_betting_round_complete())
                labels = adapter.play_hand(game, random.Random(5))
                self.assertFalse([label for label in labels if label.startswith("human:")], labels)
                self.assertEqual(adapter.total_chips(game), total)
                self.assertEqual(game.last_refunds, {0: 5})
                [main] = game.last_pot_awards
                self.assertEqual((main["amount"], main["eligible"]), (10, [0, 1]))
                self.assertLessEqual(adapter.stacks(game)[1], 10)
                self.assertEqual(sum(adapter.stacks(game)[:2]), FORCED_STACK + 5)
                refunds = [event["text"] for event in game.get_hand_history_events()
                           if event["hand_number"] == game.hand_number and event["type"] == "refund"]
                self.assertEqual(refunds, ["Uncalled $5 returned to you."])

    # (c) B37 ---------------------------------------------------------------------------------

    def test_a_layer_no_live_seat_paid_into_goes_back_exactly(self):
        for adapter in MULTI_SEAT:
            count = adapter.seat_count
            with self.subTest(adapter.key):
                # Two short all-ins; two seats that put in more have since folded.
                contributions = ([3, 5, 10, 10] + [0] * count)[:count]
                live = ([True, True, False, False] + [False] * count)[:count]
                ranks = ([14, 9, 2, 2] + [2] * count)[:count]
                game = adapter.force_showdown(new_game(adapter), contributions, live, ranks, 0)
                self.assertEqual(gains(adapter, game), ([12, 6, 5, 5] + [0] * count)[:count])
                self.assertEqual(sum(gains(adapter, game)), sum(contributions))
                self.assertEqual(adapter.refunds(game), {2: 5, 3: 5})
                self.assertEqual([award["amount"] for award in adapter.awards(game)], [12, 6])
                # Seat 1 lost the contested main pot but takes the side pot (its own excess plus
                # folded dead money) and is up 1, so it won that pot too (core.hand_winners).
                self.assertEqual(sorted(adapter.winners(game)), [0, 1])
                self.assertEqual(game.last_resolved_pot, 18)

    def test_five_o_has_one_pot_paid_in_full(self):
        self.assertFalse(FIVE_O.has_side_pots)
        for ranks in ([14, 3], [3, 14], [8, 8]):
            with self.subTest(ranks=ranks):
                game = FIVE_O.force_showdown(new_game(FIVE_O), [30, 30], [True, True], ranks, 0)
                self.assertEqual(sum(gains(FIVE_O, game)), 60)
                self.assertEqual([award["amount"] for award in game.last_pot_awards], [60])
                self.assertEqual(game.last_refunds, {})

    # (d) ties and award records --------------------------------------------------------------

    def test_equal_best_hands_split_every_pot(self):
        for adapter in MULTI_SEAT:
            count = adapter.seat_count
            dealer = 2
            with self.subTest(adapter.key):
                # Seats 1 and 3 tie; seat 0 is a short all-in; the other seats folded dead money.
                contributions = [50, 100, 20, 100, 20][:count]
                live = [True, True, False, True, False][:count]
                ranks = [10, 13, 2, 13, 2][:count]
                game = adapter.force_showdown(new_game(adapter), contributions, live, ranks, dealer)
                awards = adapter.awards(game)
                main_pot = 20 * count + 90
                self.assertEqual([award["amount"] for award in awards], [main_pot, 100])
                for award in awards:
                    self.assertEqual(set(award), RECORD_KEYS)
                    self.assertEqual(award["winners"], [3, 1])    # clockwise from the dealer's left
                    self.assertEqual(sum(award["payouts"].values()), award["amount"])
                    self.assertEqual(award["payouts"], {3: award["amount"] // 2, 1: award["amount"] // 2})
                    self.assertEqual(award["remainder"], 0)
                self.assertEqual(awards[0]["eligible"], [0, 1, 3])
                self.assertEqual(awards[1]["eligible"], [1, 3])
                self.assertEqual(gains(adapter, game)[0], 0)
                self.assertEqual(gains(adapter, game)[1], main_pot // 2 + 50)
                self.assertEqual(sorted(adapter.winners(game)), [1, 3])
                each = main_pot // 2 + 50
                if adapter.key == "texas_holdem":
                    # Hold'em's banner wraps, so its payout text names each winner's hand.
                    self.assertEqual(game.result_text,
                                     f"Payouts: {seat_name(game, 1)} ${each:,} with K-high; "
                                     f"{seat_name(game, 3)} ${each:,} with K-high.")
                    self.assertTrue(all(award["hand"] == "K-high" for award in awards))
                elif adapter.key in HOLDEM_FAMILY:
                    # Draw's and Stud's banner is one fixed-width line: names and amounts only,
                    # as before the shared showdown; the hands are in the pot records.
                    self.assertEqual(game.result_text,
                                     f"Payouts: {seat_name(game, 1)} ${each:,}; {seat_name(game, 3)} ${each:,}.")
                    self.assertTrue(all(award["hand"] == "K-high" for award in awards))
                else:
                    self.assertEqual(game.result_text,
                                     f"Payouts: {seat_name(game, 1)} ${each:,}; {seat_name(game, 3)} ${each:,}.")

    def test_five_o_tie_records_match_the_shared_shape(self):
        game = FIVE_O.force_showdown(new_game(FIVE_O), [25, 25], [True, True], [7, 7], 1)
        [award] = game.last_pot_awards
        self.assertEqual(set(award), RECORD_KEYS)
        self.assertEqual(award, {"amount": 50, "eligible": [0, 1], "winners": [0, 1], "payouts": {0: 25, 1: 25},
                                 "share": 25, "remainder": 0, "hand": ""})
        game = FIVE_O.force_showdown(new_game(FIVE_O), [25, 25], [True, True], [3, 7], 1)
        [award] = game.last_pot_awards
        self.assertEqual(award, {"amount": 50, "eligible": [0, 1], "winners": [1], "payouts": {1: 50},
                                 "share": 50, "remainder": 0, "hand": ""})
        self.assertEqual(game.last_winner, "npc")

    def test_pot_history_lists_true_side_pots_with_the_winning_hand(self):
        for key in HOLDEM_FAMILY:
            adapter = ADAPTERS_BY_KEY[key]
            with self.subTest(key):
                # A true side pot: seat 0 is all-in short of seats 1 and 2.
                game = adapter.force_showdown(new_game(adapter), [50, 100, 100, 0, 0],
                                              [True, True, True, False, False], [14, 9, 12, 2, 2], 0)
                awards = [event for event in game.get_hand_history_events()
                          if event["type"] == "pot_award" and event["hand_number"] == game.hand_number]
                self.assertEqual([event["text"] for event in awards], [
                    "Main pot $150: You win. Winning hand: A-high. You receive $150.",
                    f"Side pot 1 $100: {seat_name(game, 2)} wins. Winning hand: Q-high. "
                    f"{seat_name(game, 2)} receives $100.",
                ])
                # Folded dead money alone is not a side pot, so nothing extra is logged.
                game = adapter.force_showdown(new_game(adapter), [10, 100, 100, 30, 0],
                                              [False, True, True, False, False], [2, 9, 12, 2, 2], 0)
                self.assertEqual(len(game.last_pot_awards), 1)
                self.assertFalse([event for event in game.get_hand_history_events()
                                  if event["type"] == "pot_award" and event["hand_number"] == game.hand_number])

    def test_pot_history_names_the_odd_chip_rule(self):
        for key in HOLDEM_FAMILY:
            adapter = ADAPTERS_BY_KEY[key]
            with self.subTest(key):
                # Main pot of 3 x 5 split between seats 0 and 1; seat 2's extra 10 is a side pot it wins.
                game = adapter.force_showdown(new_game(adapter), [5, 5, 15, 15, 0],
                                              [True, True, True, False, False], [14, 14, 9, 2, 2], 4)
                [main] = [event["text"] for event in game.get_hand_history_events()
                          if event["type"] == "pot_award" and event.get("pot_index") == 0
                          and event["hand_number"] == game.hand_number]
                self.assertEqual(main, "Main pot $20: split between you and Ada. Winning hand: A-high. "
                                       "Each winner receives $10.")
                # One more chip of folded dead money makes the main pot odd: $21, $11 to You (the
                # first seat left of the dealer, seat 4) and $10 to Ada.
                game = adapter.force_showdown(new_game(adapter), [5, 5, 15, 15, 1],
                                              [True, True, True, False, False], [14, 14, 9, 2, 2], 4)
                self.assertEqual(game.last_pot_awards[0]["payouts"], {0: 11, 1: 10})
                [main] = [event["text"] for event in game.get_hand_history_events()
                          if event["type"] == "pot_award" and event.get("pot_index") == 0
                          and event["hand_number"] == game.hand_number]
                # P3: the parenthetical names who got the odd chip ("you" mid-sentence).
                self.assertEqual(main, "Main pot $21: split between you and Ada. Winning hand: A-high. "
                                       "Each winner receives $10 (odd chip to you).")
                # Three winners: commas, then "and" before the last name.
                game = adapter.force_showdown(new_game(adapter), [5, 5, 5, 15, 15], [True] * 5,
                                              [14, 14, 14, 9, 2], 4)
                [main] = [event["text"] for event in game.get_hand_history_events()
                          if event["type"] == "pot_award" and event.get("pot_index") == 0
                          and event["hand_number"] == game.hand_number]
                self.assertTrue(main.startswith(
                    f"Main pot $25: split between you, {seat_name(game, 1)} and {seat_name(game, 2)}. "), main)
                # One odd chip, to an NPC: seat 1 is the first winner left of the dealer (seat 0).
                game = adapter.force_showdown(new_game(adapter), [5, 5, 5, 15, 15], [True] * 5,
                                              [14, 14, 14, 9, 2], 0)
                [main] = [event["text"] for event in game.get_hand_history_events()
                          if event["type"] == "pot_award" and event.get("pot_index") == 0
                          and event["hand_number"] == game.hand_number]
                self.assertEqual(game.last_pot_awards[0]["remainder"], 1)
                self.assertTrue(main.endswith(f"Each winner receives $8 (odd chip to {seat_name(game, 1)})."), main)
                self.assertNotIn("dealer", main)

    def test_pot_history_names_every_winner_of_an_odd_chip(self):
        # P3: two odd chips among three tied winners go to the first two in odd-chip order.
        # The dealer is seat 1, so the order is seat 2, you, seat 1: "(odd chips to Bo and you)".
        for key in HOLDEM_FAMILY:
            adapter = ADAPTERS_BY_KEY[key]
            with self.subTest(key):
                game = adapter.force_showdown(new_game(adapter), [7, 7, 7, 20, 20],
                                              [True, True, True, True, False], [14, 14, 14, 9, 2], 1)
                main_award = game.last_pot_awards[0]
                self.assertEqual((main_award["amount"], main_award["remainder"], main_award["winners"]),
                                 (35, 2, [2, 0, 1]))
                self.assertEqual(main_award["payouts"], {2: 12, 0: 12, 1: 11})
                [main] = [event["text"] for event in game.get_hand_history_events()
                          if event["type"] == "pot_award" and event.get("pot_index") == 0
                          and event["hand_number"] == game.hand_number]
                bo, ada = seat_name(game, 2), seat_name(game, 1)
                self.assertEqual(main, f"Main pot $35: split between {bo}, you and {ada}. Winning hand: "
                                       f"A-high. Each winner receives $11 (odd chips to {bo} and you).")

    def test_a_pot_nobody_else_could_win_is_collected_without_a_hand(self):
        # P4 (reviewer repro b86_rr/ui_text/uncontested_side.py): a side pot with one eligible
        # seat beat nobody. The history says it was collected and names no winning hand,
        # whether or not the collector is up on the hand; the recap heading names no hand.
        cases = (
            # The human (net -70) collects the 20 side pot that folded seat 2 paid towards.
            (UNCONTESTED_SIDE_POT_CASE, 0, 20, "you collect $20"),
            # Seat 3 (net +6) collects 26: its own 13 plus folded seat 4's 13.
            (([7, 7, 7, 20, 20], [True, True, True, True, False], [14, 14, 14, 9, 2]), 3, 26, None),
        )
        for key in HOLDEM_FAMILY:
            adapter = ADAPTERS_BY_KEY[key]
            for (contributions, live, ranks), collector, amount, collect_text in cases:
                with self.subTest(key, contributions=contributions):
                    padding = adapter.seat_count - len(contributions)
                    game = adapter.force_showdown(new_game(adapter), contributions + [0] * padding,
                                                  live + [False] * padding, ranks + [2] * padding, 1)
                    side = game.last_pot_awards[1]
                    self.assertEqual((side["eligible"], side["amount"]), ([collector], amount))
                    collect_text = collect_text or f"{seat_name(game, collector)} collects ${amount:,}"
                    [line] = [event["text"] for event in game.get_hand_history_events()
                              if event["type"] == "pot_award" and event.get("pot_index") == 1
                              and event["hand_number"] == game.hand_number]
                    self.assertEqual(line, f"Side pot 1 ${amount:,}: nobody else could win it; {collect_text}.")
                    self.assertNotIn("Winning hand", line)
                    self.assertNotIn(" win.", line)
                    heading = [row for row in recap.recap_lines(game) if row.startswith("Side pot 1:")]
                    self.assertEqual(heading, [f"Side pot 1: ${amount:,} — Nobody else could win it"])
                    # The contested main pot still names its hand.
                    self.assertIn("Winning hand", [event["text"] for event in game.get_hand_history_events()
                                                   if event["type"] == "pot_award"
                                                   and event.get("pot_index") == 0
                                                   and event["hand_number"] == game.hand_number][0])

    def test_a_fold_win_pot_still_says_everyone_else_folded(self):
        for key in HOLDEM_FAMILY:
            adapter = ADAPTERS_BY_KEY[key]
            with self.subTest(key):
                game = adapter.force_fold_win(new_game(adapter), [60, 20, 0, 0, 0], 0)
                self.assertEqual(recap.recap_lines(game)[0], "Main pot: $40 — Everyone else folded")

    def test_holdem_payouts_name_no_hand_for_a_seat_that_only_collected(self):
        adapter = ADAPTERS_BY_KEY["texas_holdem"]
        contributions, live, ranks = UNCONTESTED_SIDE_POT_CASE
        # Seat 1 wins the main pot; the human only collects the side pot nobody else could win.
        game = adapter.force_showdown(new_game(adapter), contributions + [0], live + [False], ranks + [2], 1)
        self.assertEqual(game.result_text, f"Payouts: You $20; {seat_name(game, 1)} $248 with A-high.")

    # (e) NEW-2 -------------------------------------------------------------------------------

    def test_last_resolved_pot_is_set_by_a_showdown_and_reset_by_the_next_hand(self):
        for adapter in ADAPTERS:
            count = adapter.seat_count
            with self.subTest(adapter.key):
                if count == 2:
                    game = adapter.force_showdown(new_game(adapter), [40, 40], [True, True], [14, 3], 0)
                    resolved = 80
                else:
                    contributions = [0] * count
                    contributions[0], contributions[1], contributions[2] = 100, 100, 300
                    live = [amount > 0 for amount in contributions]
                    ranks = [14, 9, 5] + [2] * (count - 3)
                    game = adapter.force_showdown(new_game(adapter), contributions, live, ranks, count - 1)
                    resolved = 300    # the 200 uncalled chips are not part of the resolved pot
                self.assertEqual(game.last_resolved_pot, resolved)
                self.assertEqual(sum(award["amount"] for award in adapter.awards(game)), resolved)
                if hasattr(game, "get_display_pot_amount"):
                    self.assertEqual(game.get_display_pot_amount(), resolved)

                game.recap_open, game.recap_page = True, 2
                if adapter.key == "blind_mans_bluff":
                    game.hand_number = 0    # the human opens hand 1, so no NPC acts inside start_hand
                self.assertTrue(adapter.start_hand(game))
                self.assertFalse(adapter.hand_complete(game))
                self.assertEqual(game.last_resolved_pot, 0)
                self.assertEqual(adapter.awards(game), [])
                self.assertEqual(game.last_refunds, {})
                self.assertEqual(adapter.winners(game), [])
                if adapter.key in HOLDEM_FAMILY:
                    self.assertEqual((game.recap_open, game.recap_page), (False, 0))

    # (f) B42 ---------------------------------------------------------------------------------

    def test_blind_mans_bluff_counts_wins_ties_and_losses_by_pot(self):
        adapter = ADAPTERS_BY_KEY["blind_mans_bluff"]
        cases = (
            # contributions, ranks, expected (won, tied, lost), why
            ([50, 100, 100, 0], [14, 9, 12, 2], (1, 0, 0), "won the main pot, lost the side pot"),
            ([50, 100, 100, 0], [14, 9, 14, 2], (0, 1, 0), "split the main pot only"),
            ([100, 50, 100, 0], [14, 14, 9, 2], (1, 0, 0), "split the main pot, won the side pot alone"),
            ([100, 50, 100, 0], [12, 14, 9, 2], (1, 0, 0), "a short NPC won the main pot, you the side pot"),
            ([100, 50, 100, 0], [2, 14, 9, 2], (0, 0, 1), "won nothing"),
            ([10, 10, 0, 0], [14, 14, 2, 2], (0, 1, 0), "an even split"),
            ([300, 100, 100, 0], [2, 14, 9, 2], (0, 0, 1), "a refund is not a win"),
        )
        for seed, (contributions, ranks, expected, why) in enumerate(cases):
            with self.subTest(why):
                game = new_game(adapter, seed)
                live = [amount > 0 for amount in contributions]
                adapter.force_showdown(game, contributions, live, ranks, 3)
                self.assertEqual((game.hands_won, game.hands_tied, game.hands_lost), expected)
                self.assertEqual(game.hands_played, 1)

    # F3: the BMB repro. The human lost the contested main pot to seat 1's all-in, collected
    # a 20 side pot of folded seat 2's dead money and got its own uncalled 10 back.
    UNCONTESTED_SIDE_POT = ([100, 80, 90, 8], [True, True, False, False], [5, 14, 2, 2])

    def test_blind_mans_bluff_an_uncontested_side_pot_is_not_a_win(self):
        adapter = ADAPTERS_BY_KEY["blind_mans_bluff"]
        contributions, live, ranks = self.UNCONTESTED_SIDE_POT
        reads = []
        with mock.patch("solitaireplus.games.poker.blind_mans_bluff.observe_public_action",
                        lambda game, event, seat, **kw: reads.append((event, seat, kw.get("weak")))):
            game = adapter.force_showdown(new_game(adapter), contributions, live, ranks, 3)
        self.assertEqual([award["amount"] for award in game.last_pot_awards], [248, 20])
        self.assertEqual(game.last_pot_awards[1]["eligible"], [0])
        self.assertEqual(game.last_refunds, {0: 10})
        self.assertEqual(gains(adapter, game), [30, 248, 0, 0])   # chips paid as before
        self.assertEqual(game.last_winner_indexes, [1])
        self.assertEqual((game.hands_won, game.hands_tied, game.hands_lost), (0, 0, 1))
        # The payout text still lists what each seat collected.
        self.assertEqual(game.result_text,
                         f"Payouts: You $20; {game.get_name(1)} $248. Uncalled $10 returned to you.")
        # The showdown reveal reads the human's card as weak: it won no contested pot.
        self.assertEqual([read for read in reads if read[0] == "showdown_hand"],
                         [("showdown_hand", 0, True), ("showdown_hand", 1, False)])
        # F6: the human's payout (its side pot and refund) is not a won payout.
        payouts = {event["seat"]: event for event in game.presentation_events if event["kind"] == "payout"}
        self.assertEqual((payouts[0]["amount"], payouts[0]["won"]), (30, False))
        self.assertEqual((payouts[1]["amount"], payouts[1]["won"]), (248, True))

    def test_holdem_family_an_uncontested_side_pot_is_not_a_win(self):
        contributions, live, ranks = self.UNCONTESTED_SIDE_POT
        for key in HOLDEM_FAMILY:
            adapter = ADAPTERS_BY_KEY[key]
            with self.subTest(key):
                game = adapter.force_showdown(new_game(adapter), contributions + [0], live + [False],
                                              ranks + [2], 3)
                self.assertEqual(gains(adapter, game), [30, 248, 0, 0, 0])
                self.assertEqual(game.winner_indexes, [1])
                self.assertIn("You $20", game.result_text)
                self.assertIn(f"{seat_name(game, 1)} $248", game.result_text)
                [result] = [event for event in game.get_hand_history_events()
                            if event["type"] == "result" and event["hand_number"] == game.hand_number]
                self.assertEqual(result["winners"], [1])
                self.assertEqual(result["payouts"], {0: 20, 1: 248})

    # F3 review: seat 1 is all-in for 100 and wins the main pot; seat 2 put in 400 and folded
    # to the human's last bet. The human gets back 600 + 100 of its 500: up 200, all of it
    # seat 2's money, as when seat 2 folds heads-up (a fold win).
    PROFITABLE_SIDE_POT = ([500, 100, 400], [True, True, False], [5, 14, 2])

    def test_an_uncontested_side_pot_that_made_money_is_a_win_in_every_variant(self):
        for adapter in MULTI_SEAT:
            count = adapter.seat_count
            contributions, live, ranks = (
                (values + [fill] * count)[:count]
                for values, fill in zip(self.PROFITABLE_SIDE_POT, (0, False, 2)))
            with self.subTest(adapter.key):
                game = adapter.force_showdown(new_game(adapter), contributions, live, ranks, 0)
                self.assertEqual([(award["amount"], award["eligible"], award["winners"])
                                  for award in adapter.awards(game)],
                                 [(300, [0, 1], [1]), (600, [0], [0])])
                self.assertEqual(adapter.refunds(game), {0: 100})
                self.assertEqual(gains(adapter, game)[0] - contributions[0], 200)
                self.assertEqual(sorted(adapter.winners(game)), [0, 1])
                if adapter.key == "blind_mans_bluff":
                    self.assertEqual((game.hands_won, game.hands_tied, game.hands_lost), (1, 0, 0))
                    payouts = {event["seat"]: event for event in game.presentation_events
                               if event["kind"] == "payout"}
                    self.assertEqual((payouts[0]["amount"], payouts[0]["won"]), (700, True))

    def test_holdem_family_resolve_showdown_pays_only_once(self):
        # F10: resolve_showdown (shared by Hold'em, Draw and Stud) on a finished hand pays nothing.
        for key in HOLDEM_FAMILY:
            adapter = ADAPTERS_BY_KEY[key]
            with self.subTest(key):
                game = adapter.force_showdown(new_game(adapter), [50, 100, 100, 0, 0],
                                              [True, True, True, False, False], [14, 9, 12, 2, 2], 0)
                self.assertTrue(game.hand_complete)
                stacks, awards = adapter.stacks(game), list(game.last_pot_awards)
                events = len(game.get_hand_history_events())
                self.assertFalse(game.resolve_showdown())
                self.assertEqual(adapter.stacks(game), stacks)
                self.assertEqual(game.last_pot_awards, awards)
                self.assertEqual(len(game.get_hand_history_events()), events)

    def test_blind_mans_bluff_payout_text_comes_from_pot_totals(self):
        adapter = ADAPTERS_BY_KEY["blind_mans_bluff"]
        game = adapter.force_showdown(new_game(adapter), [50, 100, 100, 0], [True, True, True, False],
                                      [14, 9, 12, 2], 3)
        self.assertEqual(game.result_text, f"Payouts: You $150; {game.get_name(2)} $100.")
        self.assertEqual(game.pot_awarded, 250)
        self.assertEqual(game.last_winner_indexes, [0, 2])

    # (g) NEW-8 -------------------------------------------------------------------------------

    def test_hold_em_win_achievement_reads_the_recorded_payouts(self):
        from solitaireplus.games.poker import holdem_screen

        def winnings(awards):
            with mock.patch.object(holdem_screen, "texas_holdem_game", SimpleNamespace(last_pot_awards=awards)):
                return holdem_screen.get_holdem_player_winnings()

        # The human ties with seat 2; the odd chip went to seat 2, first after the dealer.
        self.assertEqual(winnings([{"winners": [2, 0], "share": 7, "remainder": 1, "payouts": {2: 8, 0: 7}},
                                   {"winners": [0], "share": 20, "remainder": 0, "payouts": {0: 20}},
                                   {"winners": [1], "share": 9, "remainder": 0, "payouts": {1: 9}}]), 27)
        # A record without payouts keeps the old share and remainder rule.
        self.assertEqual(winnings([{"winners": [2, 0], "share": 7, "remainder": 1}]), 8)
        self.assertEqual(winnings([]), 0)

        # P1: the single-pot flags read the human's share of its largest pot.
        def largest(awards):
            with mock.patch.object(holdem_screen, "texas_holdem_game", SimpleNamespace(last_pot_awards=awards)):
                return holdem_screen.get_holdem_player_largest_pot()

        self.assertEqual(largest([{"winners": [2, 0], "share": 7, "remainder": 1, "payouts": {2: 8, 0: 7}},
                                  {"winners": [0], "share": 20, "remainder": 0, "payouts": {0: 20}},
                                  {"winners": [1], "share": 9, "remainder": 0, "payouts": {1: 9}}]), 20)
        self.assertEqual(largest([{"winners": [2, 0], "share": 7, "remainder": 1}]), 8)
        self.assertEqual(largest([{"winners": [1], "payouts": {1: 9}}]), 0)
        self.assertEqual(largest([]), 0)

        adapter = ADAPTERS_BY_KEY["texas_holdem"]
        contributions, live, ranks = odd_chip_case(5, 0, {0, 2}, 1)
        game = adapter.force_showdown(new_game(adapter), contributions, live, ranks, 0)
        self.assertEqual(game.last_pot_awards[0]["winners"], [2, 0])
        with mock.patch.object(holdem_screen, "texas_holdem_game", game):
            self.assertEqual(holdem_screen.get_holdem_player_winnings(), gains(adapter, game)[0])
        self.assertEqual(gains(adapter, game)[0] + 1, gains(adapter, game)[2])


class HoldemWinAchievementTests(unittest.TestCase):
    """B86 polish P1: what the Hold'em win achievement is told about a hand."""

    def events_after(self, settle):
        screen = ScreenHarness(self)
        adapter = ADAPTERS_BY_KEY["texas_holdem"]
        game = screen.stub(holdem_screen, new_game(adapter))
        events = []
        recorder = SimpleNamespace(award_game_xp=lambda *args, **kwargs: None,
                                   process_achievement_event=lambda name, **data: events.append((name, data)))
        patcher = mock.patch.object(holdem_screen, "leveling", recorder)
        patcher.start()
        self.addCleanup(patcher.stop)
        state.texas_holdem_last_processed_showdown_hand = -1
        settle(adapter, game)
        holdem_screen.process_texas_holdem_showdown()
        return [data for name, data in events if name == "holdem_hand_win"]

    @staticmethod
    def stats_after(payloads):
        from solitaireplus.profile.achievements import make_default_achievement_state, record_event
        achievement_state = make_default_achievement_state()
        for data in payloads:
            achievement_state, _unlocked = record_event(achievement_state, "holdem_hand_win", **data)
        return achievement_state["stats"]

    def test_a_shove_the_blinds_fold_to_wins_only_the_pot(self):
        # Before: winnings 1,030 (the shove's own 980 uncalled chips included) set the
        # Four-Figure Pot flag and added 1,030 to holdem_total_winnings every time.
        [data] = self.events_after(lambda adapter, game: adapter.force_fold_win(game, [1000, 10, 20, 0, 0], 0))
        self.assertEqual((data["winnings"], data["largest_pot"]), (50, 50))
        stats = self.stats_after([data] * 25)
        self.assertEqual(stats["holdem_total_winnings"], 50 * 25)
        self.assertFalse(stats.get("holdem_1000_win", False))
        self.assertFalse(stats.get("holdem_25000_win", False))

    def test_side_pots_count_toward_the_total_but_not_as_one_pot(self):
        # The human (600 in) wins the 1,800 main pot and the 800 side pot from seat 2 (1,000
        # in); seat 1 is all-in for 600 and seat 3 folded 0.
        [data] = self.events_after(lambda adapter, game: adapter.force_showdown(
            game, [1000, 600, 1000, 0, 0], [True, True, True, False, False], [14, 9, 5, 2, 2], 0))
        self.assertEqual((data["winnings"], data["largest_pot"]), (2600, 1800))
        stats = self.stats_after([data])
        self.assertEqual(stats["holdem_total_winnings"], 2600)
        self.assertTrue(stats["holdem_1000_win"])
        # Two pots of 900 and 800 make 1,700 in the hand but no single 1,000 pot.
        stats = self.stats_after([{"winnings": 1700, "largest_pot": 900}])
        self.assertEqual(stats["holdem_total_winnings"], 1700)
        self.assertFalse(stats.get("holdem_1000_win", False))

    def test_a_payload_without_largest_pot_counts_its_winnings_as_one_pot(self):
        stats = self.stats_after([{"winnings": 1200}])
        self.assertEqual(stats["holdem_total_winnings"], 1200)
        self.assertTrue(stats["holdem_1000_win"])


# ==================================================
# F4: CASH-WIN FANS ARE PAID ON WHAT THE HUMAN WON
# ==================================================

SCREENS = {
    "texas_holdem": (holdem_screen, "process_texas_holdem_showdown"),
    "five_card_draw": (five_card_draw_screen, "process_five_card_draw_showdown"),
    "seven_card_stud": (seven_card_stud_screen, "process_seven_card_stud_showdown"),
}


class CashWinFanTests(unittest.TestCase):
    def fans_after(self, key, settle):
        screen = ScreenHarness(self)
        module, process = SCREENS[key]
        adapter = ADAPTERS_BY_KEY[key]
        game = screen.stub(module, new_game(adapter))
        setattr(state, f"{key}_last_processed_showdown_hand", 0)
        settle(adapter, game)
        getattr(module, process)()
        return game, screen.cash_wins

    def test_a_showdown_pays_fans_on_the_human_net(self):
        # The human puts in 50 and wins the 150 main pot (up 100); seat 2 wins the 100 side
        # pot. Fans were paid on 250, then on the human's 150 payout.
        for key in HOLDEM_FAMILY:
            with self.subTest(key):
                game, fans = self.fans_after(key, lambda adapter, game: adapter.force_showdown(
                    game, [50, 100, 100, 0, 0], [True, True, True, False, False], [14, 9, 12, 2, 2], 0))
                self.assertEqual(game.last_resolved_pot, 250)
                self.assertEqual(fans, [100])

    def test_a_won_side_pot_on_a_losing_hand_pays_no_fans(self):
        # The human wins the contested 40 side pot from seat 2 but loses the 240 main pot to
        # seat 1: down 60. It won a pot (the win sound plays) but made no money.
        for key in HOLDEM_FAMILY:
            with self.subTest(key):
                game, fans = self.fans_after(key, lambda adapter, game: adapter.force_showdown(
                    game, [100, 80, 100, 0, 0], [True, True, True, False, False], [9, 14, 5, 2, 2], 0))
                self.assertIn(0, game.winner_indexes)
                self.assertEqual(fans, [])
                self.assertGreater(state.__dict__.get(f"{key}_hand_win_sound_at", 0), 0)

    def test_a_profitable_uncontested_side_pot_pays_fans_on_the_net(self):
        contributions, live, ranks = VariantPotTests.PROFITABLE_SIDE_POT
        for key in HOLDEM_FAMILY:
            with self.subTest(key):
                game, fans = self.fans_after(key, lambda adapter, game: adapter.force_showdown(
                    game, contributions + [0, 0], live + [False, False], ranks + [2, 2], 0))
                self.assertEqual(fans, [200])
                self.assertGreater(state.__dict__.get(f"{key}_hand_win_sound_at", 0), 0)

    def test_refunds_and_uncontested_pots_pay_no_fans(self):
        # F3: the human only collects an uncontested side pot and its refund: not a win.
        contributions, live, ranks = VariantPotTests.UNCONTESTED_SIDE_POT
        for key in HOLDEM_FAMILY:
            with self.subTest(key):
                game, fans = self.fans_after(key, lambda adapter, game: adapter.force_showdown(
                    game, contributions + [0], live + [False], ranks + [2], 3))
                self.assertEqual(fans, [])
                self.assertEqual(state.__dict__.get(f"{key}_hand_win_sound_at", 0), 0)

    def test_a_fold_win_pays_fans_on_the_chips_won_not_the_human_own(self):
        # Fans count only the other seats' chips: an uncalled 1000 shove against blinds of 10
        # and 20 wins the 50 pot (20 of it the human's own) and gets 980 back, a net of 30.
        for key in HOLDEM_FAMILY:
            for contributions, net in (([60, 20, 0, 0, 0], 20), ([1000, 10, 20, 0, 0], 30)):
                with self.subTest(key, contributions=contributions):
                    game, fans = self.fans_after(key, lambda adapter, game: adapter.force_fold_win(
                        game, contributions, 0))
                    self.assertEqual(fans, [net])


if __name__ == "__main__":
    unittest.main()
