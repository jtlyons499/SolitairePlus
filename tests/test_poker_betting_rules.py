"""Shared betting rules in every poker variant (B86 group 3).

Covers B39 (after a short all-in forced bet with at most one seat able to act, the call is the
amount really posted), B36 (nobody bets or raises when nobody can respond), the shared minimum
raise and full-raise rule (a short all-in raise does not reopen raising for a seat that already
acted), NEW-6 (Seven-Card Stud's three-raise cap counts only full raises, never the completion of
the bring-in) and NEW-4 (the Five-O opponent can raise).

B86 review F2 (core.betting_reopened, TDA Rule 47): in the no-limit variants (Hold'em, Draw,
Blind Man's Bluff) short all-ins that together add up to a full raise reopen betting for a seat
that already acted; one short all-in below a full raise still does not. Fixed-limit Stud keeps
its rule that short all-ins never reopen betting (a designer item).

The pure core.py functions are tested directly. Every table rule is then checked in every
variant through the adapters in tests/support/poker_variants.py; a variant where a rule does not
apply asserts the rule it keeps instead.
"""
import random
import unittest
from unittest import mock

from solitaireplus.games.poker.ai import get_poker_personality_profile
from solitaireplus.games.poker.core import (
    betting_reopened,
    can_raise,
    classify_wager,
    minimum_raise_to,
    opening_current_bet,
)
from solitaireplus.games.poker.holdem import TexasHoldemGame
from tests.support.poker_variants import ADAPTERS, ADAPTERS_BY_KEY, FORCED_STACK

HOLDEM_FAMILY = ("texas_holdem", "five_card_draw", "seven_card_stud")
NO_LIMIT = ("texas_holdem", "five_card_draw", "blind_mans_bluff")
STUD = ADAPTERS_BY_KEY["seven_card_stud"]
FIVE_O = ADAPTERS_BY_KEY["five_o_poker"]


def new_game(adapter, seed=1):
    return adapter.new_game(random.Random(f"betting-{adapter.key}-{seed}"))


# ==================================================
# PURE CORE FUNCTIONS
# ==================================================

class OpeningCurrentBetTests(unittest.TestCase):
    def test_nobody_can_act(self):
        self.assertEqual(opening_current_bet(20, [10, 15], [False, False]), 15)
        self.assertEqual(opening_current_bet(20, [], []), 0)

    def test_one_seat_can_act(self):
        self.assertEqual(opening_current_bet(20, [10, 15], [True, False]), 15)
        self.assertEqual(opening_current_bet(20, [0, 5, 15], [True, False, False]), 15)
        # Only the posted wager can be called, however short it is.
        self.assertEqual(opening_current_bet(20, [0, 0, 3], [False, True, False]), 3)

    def test_two_or_more_can_act_keep_the_nominal_wager(self):
        self.assertEqual(opening_current_bet(20, [10, 15, 0], [True, False, True]), 20)
        self.assertEqual(opening_current_bet(20, [10, 20], [True, True]), 20)
        self.assertEqual(opening_current_bet(20, [10, 20, 0, 0], [True, True, True, True]), 20)
        # A posted wager above the nominal one is the bet to call.
        self.assertEqual(opening_current_bet(5, [0, 8], [True, True]), 8)

    def test_antes_only(self):
        # Dead antes are not round bets: nothing has been bet.
        self.assertEqual(opening_current_bet(0, [0, 0, 0], [True, True, False]), 0)

    def test_truthy_can_act_values_are_counted(self):
        self.assertEqual(opening_current_bet(20, [10, 15, 0], [1, 0, 1]), 20)
        self.assertEqual(opening_current_bet(20, [10, 15, 0], [1, 0, 0]), 15)


class CanRaiseTests(unittest.TestCase):
    def test_open_and_facing_a_bet(self):
        self.assertTrue(can_raise(0, [True, True], [100, 100], [0, 0], 0))
        self.assertTrue(can_raise(0, [True, True], [100, 100], [0, 20], 20))
        self.assertTrue(can_raise(1, [True, True, True], [0, 100, 50], [40, 20, 40], 40))

    def test_not_in_hand_or_no_chips(self):
        self.assertFalse(can_raise(0, [False, True], [100, 100], [0, 20], 20))
        self.assertFalse(can_raise(0, [True, True], [0, 100], [10, 20], 20))

    def test_not_reopened(self):
        self.assertFalse(can_raise(0, [True, True], [100, 100], [0, 20], 20, reopened=False))
        self.assertTrue(can_raise(0, [True, True], [100, 100], [0, 20], 20, reopened=True))

    def test_stack_equal_to_the_call(self):
        self.assertFalse(can_raise(0, [True, True], [20, 100], [0, 20], 20))
        self.assertFalse(can_raise(0, [True, True], [15, 100], [5, 20], 20))
        self.assertTrue(can_raise(0, [True, True], [21, 100], [0, 20], 20))

    def test_only_all_in_or_folded_opponents(self):
        self.assertFalse(can_raise(0, [True, True, True], [100, 0, 0], [0, 20, 15], 20))
        # A folded seat with chips cannot respond either.
        self.assertFalse(can_raise(0, [True, True, False], [100, 0, 300], [0, 20, 0], 20))
        self.assertTrue(can_raise(0, [True, True, True], [100, 0, 300], [0, 20, 0], 20))

    def test_nothing_bet_and_nobody_able_to_respond(self):
        self.assertFalse(can_raise(1, [True, True, True], [0, 50, 0], [0, 0, 0], 0))
        self.assertFalse(can_raise(1, [False, True, False], [80, 50, 90], [0, 0, 0], 0))

    def test_seat_outside_the_table(self):
        self.assertFalse(can_raise(2, [True, True], [100, 100], [0, 0], 0))
        self.assertFalse(can_raise(-1, [True, True], [100, 100], [0, 0], 0))


class BettingReopenedTests(unittest.TestCase):
    def test_a_seat_that_has_not_acted_may_raise(self):
        self.assertTrue(betting_reopened(False, 0, 100, 100))
        self.assertTrue(betting_reopened(False, 100, 100, 100))

    def test_short_all_ins_that_add_up_to_a_full_raise_reopen(self):
        # Bet 100, all-in to 150, all-in to 210: the bettor faces 110, at least the full 100.
        self.assertTrue(betting_reopened(True, 100, 210, 100))
        self.assertTrue(betting_reopened(True, 100, 200, 100))

    def test_less_than_a_full_raise_does_not_reopen(self):
        self.assertFalse(betting_reopened(True, 100, 150, 100))
        self.assertFalse(betting_reopened(True, 100, 199, 100))
        self.assertFalse(betting_reopened(True, 100, 100, 100))


class MinimumRaiseToTests(unittest.TestCase):
    def test_nothing_bet_is_the_minimum_bet(self):
        self.assertEqual(minimum_raise_to(0, 0, 20), 20)
        self.assertEqual(minimum_raise_to(0, 60, 20), 20)

    def test_after_a_full_raise(self):
        self.assertEqual(minimum_raise_to(100, 60, 20), 160)
        self.assertEqual(minimum_raise_to(130, 60, 20), 190)

    def test_without_a_full_raise_yet(self):
        # A short all-in blind: the next raise is still a full minimum bet.
        self.assertEqual(minimum_raise_to(15, 0, 20), 35)


class ClassifyWagerTests(unittest.TestCase):
    def test_bets(self):
        self.assertEqual(classify_wager(0, 40, 20), (40, True))
        self.assertEqual(classify_wager(0, 20, 20), (20, True))
        self.assertEqual(classify_wager(0, 15, 20), (15, False))

    def test_raises(self):
        self.assertEqual(classify_wager(40, 100, 40), (60, True))
        self.assertEqual(classify_wager(40, 80, 40), (40, True))
        self.assertEqual(classify_wager(100, 130, 60), (30, False))

    def test_no_increase_is_never_full(self):
        self.assertEqual(classify_wager(100, 100, 60), (0, False))
        self.assertEqual(classify_wager(100, 80, 60), (-20, False))
        self.assertEqual(classify_wager(10, 10, 0), (0, False))
        self.assertEqual(classify_wager(10, 11, 0), (1, True))


# ==================================================
# B39: THE OPENING CURRENT BET
# ==================================================

# Per variant: (stacks before the deal, bring-in seat, current_bet once the forced bets are in).
# Hold'em and Draw: blinds 10/20, seat 0 deals (heads-up the dealer posts the small blind).
# Stud: ante 2, bring-in 5, small bet 10. Five-O and Blind Man's Bluff: antes only (dead money).
BLIND_CASES = (
    ([1000, 15, 0, 0, 0], None, 15),       # heads-up, big blind all-in for 15: call what was posted
    ([5, 15, 0, 0, 0], None, 15),          # heads-up, both blinds all-in: nobody can act
    ([1000, 1000, 15, 0, 0], None, 20),    # 3-handed, two can act: the nominal big blind
    ([1000, 5, 15, 0, 0], None, 15),       # 3-handed, only the dealer can act
    ([1000, 1000, 15, 1000, 1000], None, 20),
    ([1000] * 5, None, 20),
)
OPENING_CASES = {
    "texas_holdem": BLIND_CASES,
    "five_card_draw": BLIND_CASES,
    "seven_card_stud": (
        ([1000, 6, 0, 0, 0], 1, 4),        # heads-up, the bring-in all-in for 4 after its ante
        ([1000, 2, 6, 0, 0], 2, 4),        # seat 1 all-in on its ante: only the human can act
        ([1000, 1000, 6, 0, 0], 2, 5),     # two can act: the nominal bring-in
        ([1000] * 5, 1, 5),
    ),
    "five_o_poker": (
        ([500, 500], None, 0),
        ([500, 5], None, 0),               # the opponent is all-in on its ante
    ),
    "blind_mans_bluff": (
        ([1000] * 4, None, 0),
        ([1000, 8, 1000, 1000], None, 0),  # seat 1 is all-in on its ante (8)
        ([8, 1000, 1000, 8], None, 0),
    ),
}


class OpeningBetTests(unittest.TestCase):
    def test_every_variant_has_cases(self):
        self.assertEqual(set(OPENING_CASES), {adapter.key for adapter in ADAPTERS})

    def test_short_forced_bet_with_at_most_one_seat_able_to_act(self):
        for adapter in ADAPTERS:
            for stacks, bring_in_seat, expected in OPENING_CASES[adapter.key]:
                with self.subTest(adapter.key, stacks=stacks):
                    game = new_game(adapter)
                    self.assertTrue(adapter.deal_forced_bets(game, stacks, 0, bring_in_seat))
                    self.assertEqual(game.current_bet, expected)
                    if adapter.forced_bets == "antes":
                        # Dead antes: nothing to call, and no round bets.
                        self.assertEqual(adapter.pot(game), sum(adapter.contributions(game)))
                        self.assertGreater(adapter.pot(game), 0)
                    else:
                        round_bets = game.seat_round_bets()
                        if sum(game.seat_can_act()) <= 1:
                            self.assertEqual(expected, max(round_bets))
                        self.assertEqual(game.last_raiser, None)

    def test_stud_completion_follows_the_opening_bet(self):
        # The short heads-up bring-in is not a completed small bet.
        game = new_game(STUD)
        STUD.deal_forced_bets(game, [1000, 6, 0, 0, 0], 0, 1)
        self.assertEqual(game.current_bet, 4)
        self.assertFalse(game.third_street_completed)
        self.assertEqual(game.get_player_amount_to_call(), 4)
        self.assertFalse(game.can_player_raise())

    def test_heads_up_short_blind_is_called_then_runs_out(self):
        for key in ("texas_holdem", "five_card_draw"):
            adapter = ADAPTERS_BY_KEY[key]
            with self.subTest(key):
                game = new_game(adapter)
                adapter.deal_forced_bets(game, [1000, 15, 0, 0, 0])
                total = adapter.total_chips(game)
                self.assertEqual(game.current_actor, 0)
                self.assertEqual(game.get_player_amount_to_call(), 5)
                self.assertFalse(game.can_player_raise())
                self.assertTrue(game.player_call())
                self.assertEqual(game.player_round_bet, 15)
                self.assertTrue(game.is_betting_round_complete())
                adapter.play_hand(game, random.Random(3))
                self.assertEqual(adapter.total_chips(game), total)


# ==================================================
# B36: NOBODY BETS OR RAISES WHEN NOBODY CAN RESPOND
# ==================================================

class NobodyToRespondTests(unittest.TestCase):
    def test_no_bet_or_raise_when_every_other_seat_is_all_in(self):
        for adapter in ADAPTERS:
            for actor in range(adapter.seat_count):
                for bet in (0, 40):
                    with self.subTest(adapter.key, actor=actor, bet=bet):
                        game = adapter.force_all_in_opponents(new_game(adapter), actor, bet)
                        self.assertFalse(adapter.others_can_respond(game, actor))
                        self.assertFalse(adapter.can_raise(game, actor))
                        if actor:
                            self.assertFalse(adapter.npc_context(game, actor)["can_raise"])
                        stacks, pot = adapter.stacks(game), adapter.pot(game)
                        self.assertFalse(adapter.try_wager(game, actor, bet + 200))
                        self.assertEqual(adapter.stacks(game), stacks)
                        self.assertEqual(adapter.pot(game), pot)
                        self.assertEqual(game.current_bet, bet)

    def test_an_npc_that_wants_to_wager_checks_or_calls_instead(self):
        for adapter in ADAPTERS:
            for seat in range(1, adapter.seat_count):
                for bet, wanted in ((0, "bet"), (40, "raise")):
                    with self.subTest(adapter.key, seat=seat, wanted=wanted):
                        game = adapter.force_all_in_opponents(new_game(adapter), seat, bet)
                        total = adapter.total_chips(game)
                        before = adapter.contributions(game)[seat]
                        adapter.npc_turn(game, seat, wanted)
                        # Exactly the call (nothing when there is nothing to call); no fold, no stall.
                        self.assertEqual(adapter.contributions(game)[seat] - before, bet - bet // 2)
                        self.assertEqual(game.current_bet, bet)
                        self.assertTrue(adapter.in_hand(game)[seat])
                        self.assertEqual(adapter.total_chips(game), total)
                        if adapter.key in HOLDEM_FAMILY:
                            self.assertTrue(game.npc_has_acted[seat - 1])
                            self.assertTrue(game.is_betting_round_complete())
                        elif adapter.key == "blind_mans_bluff":
                            self.assertNotIn(seat, game.pending)

    def test_raise_still_allowed_when_somebody_can_respond(self):
        # The same table, but seat (actor + 1) still has chips behind its all-in-sized bet.
        for adapter in ADAPTERS:
            for actor in range(adapter.seat_count):
                with self.subTest(adapter.key, actor=actor):
                    game = adapter.force_all_in_opponents(new_game(adapter), actor, 40)
                    responder = (actor + 1) % adapter.seat_count
                    if adapter.key in HOLDEM_FAMILY:
                        # Not set_stacks: it would mark the other all-in seats busted.
                        if responder == 0:
                            game.player_stack, game.player_all_in = FORCED_STACK, False
                        else:
                            game.npc_stacks[responder - 1] = FORCED_STACK
                            game.npc_all_in[responder - 1] = False
                    else:
                        stacks = adapter.stacks(game)
                        stacks[responder] = FORCED_STACK
                        adapter.set_stacks(game, stacks)
                    self.assertTrue(adapter.others_can_respond(game, actor))
                    self.assertTrue(adapter.can_raise(game, actor))
                    if actor:
                        self.assertTrue(adapter.npc_context(game, actor)["can_raise"])


# ==================================================
# MINIMUM RAISE AND FULL RAISES
# ==================================================

class MinimumRaiseTests(unittest.TestCase):
    def test_full_raise_sets_the_minimum_and_short_all_in_does_not_reopen(self):
        for adapter in ADAPTERS:
            for raiser in (0, 2):
                with self.subTest(adapter.key, raiser=raiser):
                    if adapter.key in NO_LIMIT:
                        self.check_no_limit(adapter, raiser)
                    elif adapter.key == "seven_card_stud":
                        self.check_fixed_limit(adapter, raiser)
                    else:
                        self.assertEqual(adapter.key, "five_o_poker")
                        self.check_five_o_fixed_size(adapter)

    def check_full_wager(self, adapter, game, full):
        if adapter.key in HOLDEM_FAMILY:
            self.assertIs(game.last_wager_full, full)

    def check_short_all_in_does_not_reopen(self, adapter, game, raiser, call_amount):
        # The raiser has acted since the last full raise: it may call, but not raise.
        adapter.give_turn(game, raiser)
        self.assertFalse(adapter.can_raise(game, raiser))
        stacks = adapter.stacks(game)
        self.assertFalse(adapter.try_wager(game, raiser, game.current_bet * 3))
        self.assertEqual(adapter.stacks(game), stacks)
        self.assertTrue(adapter.call(game, raiser))
        self.assertEqual(stacks[raiser] - adapter.stacks(game)[raiser], call_amount)
        # Seat 1 has not acted since the full raise, so it may still raise.
        adapter.give_turn(game, 1)
        self.assertTrue(adapter.can_raise(game, 1))

    def check_no_limit(self, adapter, raiser):
        game = new_game(adapter)
        stacks = [FORCED_STACK] * adapter.seat_count
        stacks[3] = 130
        adapter.force_open_round(game, stacks)
        self.assertTrue(adapter.try_wager(game, 1, 40))
        self.check_full_wager(adapter, game, True)
        self.assertEqual(game.get_minimum_raise_to(), 80)
        self.assertTrue(adapter.try_wager(game, raiser, 100))   # a full raise of R = 60
        self.check_full_wager(adapter, game, True)
        self.assertEqual(game.last_raise_size, 60)
        self.assertEqual(game.last_raiser, raiser)
        self.assertEqual(game.get_minimum_raise_to(), 160)
        # Seat 3 is all-in for 130: a raise of 30, short of the full 60.
        self.assertTrue(adapter.try_wager(game, 3, 160))
        self.check_full_wager(adapter, game, False)
        self.assertEqual(game.current_bet, 130)
        self.assertEqual(adapter.stacks(game)[3], 0)
        self.assertEqual(game.last_raise_size, 60)
        self.assertEqual(game.last_raiser, raiser)
        self.assertEqual(game.get_minimum_raise_to(), 190)
        self.check_short_all_in_does_not_reopen(adapter, game, raiser, 30)

    def check_fixed_limit(self, adapter, raiser):
        game = new_game(adapter)
        stacks = [FORCED_STACK] * adapter.seat_count
        stacks[3] = 50
        adapter.force_open_round(game, stacks)   # fifth street: the street bet is 20
        self.assertEqual(game.get_minimum_raise_to(), 20)
        self.assertTrue(adapter.try_wager(game, 1, 20))
        self.assertEqual(game.get_minimum_raise_to(), 40)
        self.assertTrue(adapter.try_wager(game, raiser, 40))
        self.check_full_wager(adapter, game, True)
        self.assertEqual(game.get_minimum_raise_to(), 60)   # current bet + the street bet
        self.assertEqual(game.raises_this_round, 1)
        # Seat 3 is all-in for 50: a raise of 10, short of the street bet.
        self.assertTrue(adapter.try_wager(game, 3, 60))
        self.check_full_wager(adapter, game, False)
        self.assertEqual(game.current_bet, 50)
        self.assertEqual(game.last_raise_size, 20)
        self.assertEqual(game.last_raiser, raiser)
        self.assertEqual(game.get_minimum_raise_to(), 70)
        self.assertEqual(game.raises_this_round, 1)
        self.check_short_all_in_does_not_reopen(adapter, game, raiser, 10)

    def check_five_o_fixed_size(self, adapter):
        # Kept rule: one fixed bet unit, whatever amount is asked for.
        game = new_game(adapter)
        adapter.start_hand(game)
        adapter.place_all_cards(game)
        unit = game.get_effective_bet_unit()
        self.assertTrue(adapter.try_wager(game, 0, unit * 7))
        self.assertEqual(game.current_bet, unit)
        unit = game.get_effective_bet_unit()
        self.assertTrue(adapter.try_wager(game, 1, unit * 7))
        self.assertEqual(game.current_bet, unit)
        self.assertEqual(game.npc_betting_paid, unit)
        self.assertEqual(game.raise_count, 1)

    def cumulative_short_all_ins(self, adapter, bet, short_totals):
        """The human bets `bet`; seats 1 and 2 go all-in short to short_totals; the rest call."""
        game = new_game(adapter, seed=7)
        stacks = [FORCED_STACK] * adapter.seat_count
        stacks[1], stacks[2] = short_totals
        adapter.force_open_round(game, stacks)
        adapter.give_turn(game, 0)
        self.assertTrue(adapter.try_wager(game, 0, bet))
        for seat, total in zip((1, 2), short_totals):
            adapter.give_turn(game, seat)
            self.assertTrue(adapter.try_wager(game, seat, total))
            self.assertEqual(adapter.stacks(game)[seat], 0)
            self.check_full_wager(adapter, game, False)     # each one is short of a full raise
        for seat in range(3, adapter.seat_count):
            adapter.give_turn(game, seat)
            self.assertTrue(adapter.call(game, seat))
        adapter.give_turn(game, 0)
        return game

    def test_short_all_ins_that_add_up_to_a_full_raise_reopen_no_limit_betting(self):
        # The repro: the human bets 100, seat 1 is all-in to 150, seat 2 all-in to 210 and the
        # others call. The human faces +110, more than the full 100, so it may raise again.
        for key in NO_LIMIT:
            adapter = ADAPTERS_BY_KEY[key]
            with self.subTest(key):
                game = self.cumulative_short_all_ins(adapter, 100, (150, 210))
                self.assertEqual(game.current_bet, 210)
                self.assertEqual(game.last_raise_size, 100)
                self.assertTrue(adapter.can_raise(game, 0))
                total = adapter.total_chips(game)
                self.assertTrue(adapter.try_wager(game, 0, 400))   # a full raise of 190
                self.assertEqual(game.current_bet, 400)
                self.assertEqual(adapter.total_chips(game), total)

    def test_short_all_ins_below_a_full_raise_still_do_not_reopen(self):
        # Kept: 100, then all-ins to 130 and 160 make only +60, short of the full 100.
        for key in NO_LIMIT:
            adapter = ADAPTERS_BY_KEY[key]
            with self.subTest(key):
                game = self.cumulative_short_all_ins(adapter, 100, (130, 160))
                self.assertEqual(game.current_bet, 160)
                self.assertFalse(adapter.can_raise(game, 0))
                stacks = adapter.stacks(game)
                self.assertTrue(adapter.call(game, 0))
                self.assertEqual(stacks[0] - adapter.stacks(game)[0], 60)

    def test_stud_short_all_ins_never_reopen_even_when_they_add_up(self):
        # Fixed limit keeps its rule (a designer item): fifth street, bet 20, all-ins to 30 and
        # 45 add up to +25, more than the street bet, and still do not reopen raising.
        game = self.cumulative_short_all_ins(STUD, 20, (30, 45))
        self.assertEqual(game.current_bet, 45)
        self.assertEqual(game.raises_this_round, 0)
        self.assertFalse(game.can_player_raise())
        self.assertTrue(game.can_player_call())

    def test_last_wager_full_starts_false_and_resets_each_round(self):
        game = TexasHoldemGame()
        self.assertIs(game.last_wager_full, False)
        adapter = ADAPTERS_BY_KEY["texas_holdem"]
        game = adapter.force_open_round(new_game(adapter), [FORCED_STACK] * adapter.seat_count)
        self.assertTrue(adapter.try_wager(game, 1, 40))
        self.assertIs(game.last_wager_full, True)
        game.reset_betting_round(assign_actor=False)
        self.assertIs(game.last_wager_full, False)

    def test_holdem_minimum_raise_to_matches_the_old_rule(self):
        # minimum_raise_to replaces the old method body with the same values.
        adapter = ADAPTERS_BY_KEY["texas_holdem"]
        game = adapter.force_open_round(new_game(adapter), [FORCED_STACK] * adapter.seat_count)
        for current_bet in (0, 7, 20, 150):
            for last_raise in (0, 5, 20, 60):
                game.current_bet, game.last_raise_size = current_bet, last_raise
                old = (max(1, game.big_blind) if current_bet <= 0
                       else current_bet + (last_raise if last_raise > 0 else max(1, game.big_blind)))
                self.assertEqual(game.get_minimum_raise_to(), old)

    def test_short_stack_raise_button_still_routes_to_a_call(self):
        for key in HOLDEM_FAMILY:
            adapter = ADAPTERS_BY_KEY[key]
            with self.subTest(key):
                game = adapter.force_open_round(new_game(adapter), [FORCED_STACK] * adapter.seat_count)
                self.assertTrue(adapter.try_wager(game, 1, 400 if key != "seven_card_stud" else 20))
                game.player_stack = game.current_bet // 2
                game.current_actor = 0
                self.assertFalse(game.can_player_raise())
                pot = game.pot
                self.assertTrue(game.player_raise(game.current_bet * 3))
                self.assertEqual(game.player_stack, 0)
                self.assertTrue(game.player_all_in)
                self.assertEqual(game.pot - pot, game.current_bet // 2)
                self.assertIs(game.last_wager_full, False)


# ==================================================
# NEW-6: STUD'S RAISE CAP COUNTS ONLY FULL RAISES
# ==================================================

class StudRaiseCapTests(unittest.TestCase):
    def check_raising_closed(self, game, seats):
        for seat in seats:
            STUD.give_turn(game, seat)
            self.assertFalse(STUD.can_raise(game, seat), seat)
            stacks = STUD.stacks(game)
            self.assertFalse(STUD.try_wager(game, seat, game.current_bet + 20), seat)
            self.assertEqual(STUD.stacks(game), stacks)

    def test_short_all_in_raise_does_not_use_up_the_cap(self):
        game = new_game(STUD)
        stacks = [FORCED_STACK] * STUD.seat_count
        stacks[3] = 50
        STUD.force_open_round(game, stacks)
        self.assertTrue(STUD.try_wager(game, 1, 20))     # the bet is not a raise
        self.assertEqual(game.raises_this_round, 0)
        self.assertTrue(STUD.try_wager(game, 2, 40))
        self.assertEqual(game.raises_this_round, 1)
        self.assertTrue(STUD.try_wager(game, 3, 60))     # all-in for 50: short
        self.assertEqual(game.raises_this_round, 1)
        self.assertTrue(STUD.try_wager(game, 4, 70))
        self.assertEqual(game.raises_this_round, 2)
        self.assertTrue(STUD.try_wager(game, 0, 90))
        self.assertEqual(game.raises_this_round, 3)
        # Three full raises close raising for everybody; calling is still open.
        self.check_raising_closed(game, (1, 2, 4))
        self.assertEqual(STUD.npc_context(game, 1)["raises_remaining"], 0)
        self.assertFalse(STUD.npc_context(game, 1)["can_raise"])
        stack = STUD.stacks(game)[2]
        self.assertTrue(STUD.call(game, 2))
        self.assertEqual(stack - STUD.stacks(game)[2], 50)

    def test_completing_the_bring_in_does_not_count(self):
        game = new_game(STUD)
        STUD.deal_forced_bets(game, [FORCED_STACK] * STUD.seat_count, 0, 1)
        self.assertEqual(game.current_bet, 5)
        self.assertFalse(game.third_street_completed)
        self.assertEqual(game.get_minimum_raise_to(), 10)
        self.assertTrue(STUD.try_wager(game, 2, 10))     # completes the bring-in to the small bet
        self.assertTrue(game.third_street_completed)
        self.assertIs(game.last_wager_full, True)
        self.assertEqual(game.raises_this_round, 0)
        self.assertEqual(game.get_minimum_raise_to(), 20)
        for count, (seat, total) in enumerate(((3, 20), (4, 30), (0, 40)), 1):
            self.assertTrue(STUD.try_wager(game, seat, total))
            self.assertEqual(game.raises_this_round, count)
        self.check_raising_closed(game, (1, 2))
        self.assertTrue(STUD.call(game, 1))

    def test_short_all_in_below_the_completion_does_not_count(self):
        game = new_game(STUD)
        STUD.deal_forced_bets(game, [FORCED_STACK, FORCED_STACK, FORCED_STACK, 10, FORCED_STACK], 0, 1)
        self.assertTrue(STUD.try_wager(game, 3, 10))     # ante 2, then all-in for 8: no completion
        self.assertEqual(game.current_bet, 8)
        self.assertFalse(game.third_street_completed)
        self.assertIs(game.last_wager_full, False)
        self.assertEqual(game.raises_this_round, 0)

    def test_completion_after_a_short_partial_completion_reopens_betting(self):
        # Review finding: bring-in 5 (seat 1), seat 2 calls it, seat 3 is all-in to 8, seat 4
        # completes to 10. The completion is the first full bet, measured from the bring-in:
        # the bring-in and the caller may raise, exactly as after a direct completion.
        for partial in (True, False):
            with self.subTest(partial=partial):
                game = new_game(STUD)
                stacks = [FORCED_STACK] * STUD.seat_count
                if partial:
                    stacks[3] = 10                       # ante 2, then 8 behind
                STUD.deal_forced_bets(game, stacks, 0, 1)
                self.assertEqual(game.current_bet, 5)
                self.assertTrue(STUD.call(game, 2))
                if partial:
                    self.assertTrue(STUD.try_wager(game, 3, 10))
                    self.assertEqual(game.current_bet, 8)
                    self.assertIs(game.last_wager_full, False)
                self.assertTrue(STUD.try_wager(game, 4, 10))     # completes to the small bet
                self.assertEqual(game.current_bet, 10)
                self.assertTrue(game.third_street_completed)
                self.assertIs(game.last_wager_full, True)
                self.assertEqual(game.last_raiser, 4)
                self.assertEqual(game.raises_this_round, 0)      # NEW-6: the completion is not a raise
                self.assertEqual(game.get_minimum_raise_to(), 20)
                for seat in (1, 2):
                    STUD.give_turn(game, seat)
                    self.assertTrue(STUD.can_raise(game, seat), seat)
                self.assertTrue(STUD.try_wager(game, 1, 20))     # the bring-in raises
                self.assertEqual(game.raises_this_round, 1)
                self.assertIs(game.last_wager_full, True)


# ==================================================
# NEW-4: THE FIVE-O OPPONENT CAN RAISE
# ==================================================

class FiveORaiseTests(unittest.TestCase):
    def decide(self, contexts):
        def decide(personality, context, rng=None):
            contexts.append(dict(context))
            action = "raise" if context.get("amount_to_call") else "bet"
            return {"action": action, "profile": get_poker_personality_profile("balanced"), "bluff": False}

        return decide

    @staticmethod
    def finish_npc(game):
        game.pending_npc_at -= 1000.0   # the opponent's thinking pause is over
        game.update()

    def test_opponent_raises_while_fewer_than_three_raises(self):
        game = new_game(FIVE_O)
        total = FIVE_O.total_chips(game)
        FIVE_O.start_hand(game)
        FIVE_O.place_all_cards(game)
        self.assertEqual(game.bet_state, "player_open")   # hand 1: the human opens
        contexts = []
        with mock.patch("solitaireplus.games.poker.five_o.decide_poker_action", self.decide(contexts)):
            self.assertTrue(game.player_bet())
            self.assertEqual(game.raise_count, 0)
            for raises in (1, 3):
                unit = game.get_effective_bet_unit()
                self.finish_npc(game)
                context = contexts[-1]
                self.assertTrue(context["can_raise"])
                self.assertEqual(context["minimum_raise_to"], unit)
                self.assertEqual(context["maximum_raise_to"], unit)
                self.assertEqual(game.raise_count, raises)
                self.assertEqual(game.current_bet, unit)
                self.assertEqual(game.npc_betting_paid, unit)
                self.assertEqual(game.bet_state, "player_response")
                self.assertEqual(FIVE_O.total_chips(game), total)
                if raises == 1:
                    self.assertEqual(game.get_player_actions(), ["fold", "call", "bet"])
                    self.assertTrue(game.player_bet())   # the human re-raises
                    self.assertEqual(game.raise_count, 2)
            # Three raises: the cap holds for the human too.
            self.assertEqual(game.get_player_actions(), ["fold", "call"])
            self.assertTrue(game.player_call())
        self.assertEqual(game.player_betting_paid, game.npc_betting_paid)
        FIVE_O.play_hand(game, random.Random(2))
        self.assertEqual(FIVE_O.total_chips(game), total)

    def test_cap_holds_for_the_opponent(self):
        game = new_game(FIVE_O)
        total = FIVE_O.total_chips(game)
        rng = random.Random(5)
        FIVE_O.start_hand(game)
        FIVE_O.play_hand(game, rng)
        self.assertTrue(FIVE_O.start_hand(game))
        self.assertEqual(game.opening_index, 1)   # hand 2: the opponent opens
        contexts = []
        with mock.patch("solitaireplus.games.poker.five_o.decide_poker_action", self.decide(contexts)):
            FIVE_O.place_all_cards(game)
            self.assertGreater(game.current_bet, 0)   # it bet
            self.assertEqual(game.raise_count, 0)
            self.assertTrue(game.player_bet())        # raise 1
            self.finish_npc(game)                     # raise 2
            self.assertEqual(game.raise_count, 2)
            self.assertTrue(game.player_bet())        # raise 3
            current = game.current_bet
            self.finish_npc(game)                     # wants to raise again, must call
            self.assertFalse(contexts[-1]["can_raise"])
        self.assertEqual(game.raise_count, 3)
        self.assertEqual(game.current_bet, current)
        self.assertEqual(game.npc_betting_paid, current)
        self.assertEqual(game.phase, "showdown")
        FIVE_O.play_hand(game, rng)
        self.assertEqual(FIVE_O.total_chips(game), total)

    def test_opponent_opening_bet_needs_a_player_with_chips(self):
        game = FIVE_O.force_all_in_opponents(new_game(FIVE_O), 1, 0)
        self.assertFalse(game._seat_can_raise(1))
        game.player_stack = 50
        self.assertTrue(game._seat_can_raise(1))


# ==================================================
# THE NEW RULE GIVES THE OLD ANSWERS WHEREVER SOMEBODY CAN RESPOND
# ==================================================

def old_holdem_can_raise(game, seat):
    """can_player_raise / can_npc_raise before group 3, Stud's raise cap included."""
    if getattr(game, "raises_this_round", 0) >= getattr(game, "max_raises_per_round", 1 << 30):
        return False
    if seat == 0:
        return (game.can_player_act_now()
                and len(game.get_actionable_player_indexes()) > 1
                and not game.player_has_acted
                and game.player_round_bet + game.player_stack > game.current_bet)
    i = seat - 1
    if game.npc_busted[i] or game.npc_folded[i] or game.npc_all_in[i]:
        return False
    return (game.npc_stacks[i] > game.get_npc_amount_to_call(i)
            and not game.npc_has_acted[i]
            and game.npc_round_bets[i] + game.npc_stacks[i] > game.current_bet)


def old_bmb_can_raise(game, seat):
    active = game.get_active_indexes()
    return (seat in game.raise_rights and game._stack_for(seat) + game.round_bets[seat] > game.current_bet
            and any(other != seat and game._stack_for(other) > 0 for other in active))


def old_five_o_player_actions(game):
    if game.phase != "betting" or game.hand_complete or game.pending_npc_at:
        return []
    if game.bet_state in ("player_open", "player_last_open"):
        return ["check", "bet"] if game.get_effective_bet_unit() > 0 else ["check"]
    if game.bet_state == "player_response":
        actions = ["fold", "call"]
        if game.raise_count < 3 and game.get_effective_bet_unit() > game.current_bet:
            actions.append("bet")
        return actions
    return []


class SameAnswersTests(unittest.TestCase):
    HANDS = 150

    def old_rule(self, adapter, game, seat):
        if adapter.key in HOLDEM_FAMILY:
            return old_holdem_can_raise(game, seat)
        if adapter.key == "blind_mans_bluff":
            return old_bmb_can_raise(game, seat)
        if seat == 0:
            return "bet" in old_five_o_player_actions(game)
        # The opponent used to open only; facing a bet it may now raise (NEW-4).
        if game.current_bet:
            return None
        return game.phase == "betting" and game.get_effective_bet_unit() > 0

    def test_can_raise_matches_the_old_rule_unless_nobody_can_respond(self):
        for adapter in ADAPTERS:
            with self.subTest(adapter.key):
                rng = random.Random("same-answers-" + adapter.key)
                compared = refused = hands = 0
                while hands < self.HANDS:
                    stacks = [rng.choice((3, 20, 60, 400, 1000)) for _ in range(adapter.seat_count)]
                    stacks = [max(stack, adapter.minimum_stack()) for stack in stacks]
                    game = adapter.new_game(rng, stacks)
                    while hands < self.HANDS and not adapter.session_over(game):
                        if not adapter.start_hand(game):
                            break
                        hands += 1
                        for _ in range(3000):
                            if adapter.hand_complete(game):
                                break
                            if adapter.key == "five_o_poker":
                                self.assertEqual(game.get_player_actions(), old_five_o_player_actions(game))
                            for seat in range(adapter.seat_count):
                                if adapter.key == "blind_mans_bluff":
                                    new = game._can_raise(seat)   # the rule itself, not the turn
                                else:
                                    new = adapter.can_raise(game, seat)
                                if not adapter.others_can_respond(game, seat):
                                    self.assertFalse(new, f"seat {seat} hand {game.hand_number}")
                                    refused += 1
                                    continue
                                old = self.old_rule(adapter, game, seat)
                                if old is not None:
                                    self.assertEqual(new, old, f"seat {seat} hand {game.hand_number}")
                                    compared += 1
                            adapter.step(game, rng)
                self.assertGreater(compared, 0)
                self.assertGreater(refused, 0)


if __name__ == "__main__":
    unittest.main()
