"""Hand and session flow in every poker variant (B86 group 4).

Covers:
* short forced bets: a seat with fewer chips than its forced bet is dealt in, posts what it has
  and plays all-in. Blind Man's Bluff used to sit such a seat out and end the session once a
  stack fell below the ante; Five-O keeps its rule that a stack below the ante ends the session;
* busted seats and the end of a session (core.session_over: the human has 0 chips, or nobody
  else has chips); a 0-chip seat is never dealt in;
* all-in run-outs (core.betting_closed): with every opponent all-in and the calls settled nobody
  is offered a bet and the hand reaches showdown through advance steps only;
* NEW-3: after the human folds, the NPCs still in the hand keep betting street by street.
  Hold'em used to deal the rest of the board and show down at once. This is also checked
  through the Hold'em screen's NPC-delay and street-delay timers.
* B86 review F1 (core.bet_to_match): once folds or all-ins leave a single seat with chips, it
  only has to match what the other seats in the hand put in this round. Before, a fold that left
  the human's posted small blind against an all-in short big blind still asked it to call the
  nominal big blind (chips that were only refunded).

The pure core.py functions are tested directly; every table rule then runs against every
variant through tests/support/poker_variants.py. A variant where a rule does not apply asserts
the rule it keeps instead.
"""
import contextlib
import random
import unittest
from unittest import mock

import pygame

from solitaireplus.app import state
from solitaireplus.games.poker import blind_mans_bluff as bluff_module
from solitaireplus.games.poker import holdem_screen
from solitaireplus.games.poker.ai import get_poker_personality_profile
from solitaireplus.games.poker.core import bet_to_match, betting_closed, session_over
from solitaireplus.games.poker.holdem_ui import get_holdem_npc_delay, get_holdem_street_delay
from tests.support.poker_screens import ScreenHarness
from tests.support.poker_variants import ADAPTERS, ADAPTERS_BY_KEY, FORCED_STACK

HOLDEM_FAMILY = ("texas_holdem", "five_card_draw", "seven_card_stud")
BMB = ADAPTERS_BY_KEY["blind_mans_bluff"]
FIVE_O = ADAPTERS_BY_KEY["five_o_poker"]

# Where each engine looks up its NPC decision (the Hold'em family shares run_next_npc_action).
DECISION_FUNCTION = {
    "texas_holdem": "solitaireplus.games.poker.holdem.decide_poker_action",
    "five_card_draw": "solitaireplus.games.poker.holdem.decide_poker_action",
    "seven_card_stud": "solitaireplus.games.poker.holdem.decide_poker_action",
    "blind_mans_bluff": "solitaireplus.games.poker.blind_mans_bluff.decide_poker_action",
    "five_o_poker": "solitaireplus.games.poker.five_o.decide_poker_action",
}

# The street a 3-handed Hold'em-family hand reaches once the first betting round is called.
OPEN_STREET = {"texas_holdem": "flop", "five_card_draw": "post_draw", "seven_card_stud": "fourth"}


def rng_for(adapter, name):
    return random.Random(f"flow-{name}-{adapter.key}")


def forced_ai(adapter, *actions):
    """Patch the variant's NPC decision to return `actions` in turn (the last one repeats)."""
    queue = list(actions)

    def decide(personality, context, rng=None):
        action = queue.pop(0) if len(queue) > 1 else queue[0]
        return {"action": action, "profile": get_poker_personality_profile("balanced"), "bluff": False}

    return mock.patch(DECISION_FUNCTION[adapter.key], decide)


def cards_of(adapter, game, seat):
    if adapter.key == "blind_mans_bluff":
        return [game.cards[seat]] if game.cards[seat] is not None else []
    return list(game.player_hand if seat == 0 else game.npc_hands[seat - 1])


def table_cards(adapter, game):
    """Every card dealt so far: the board and each seat's cards."""
    seats = [cards_of(adapter, game, seat) for seat in range(len(adapter.stacks(game)))]
    return list(getattr(game, "community_cards", [])), seats


def call_down_round(testcase, adapter, game, max_steps=100):
    """Finish the current betting round: every NPC calls or checks, the human calls or checks."""
    for _ in range(max_steps):
        if game.hand_complete or game.is_betting_round_complete():
            return
        seat = game.current_actor
        if seat == 0:
            testcase.assertTrue(game.player_call() if game.can_player_call() else game.player_check())
        elif 0 < seat < len(game.npcs) + 1:
            adapter.npc_turn(game, seat, "call")
        else:
            testcase.fail(f"{adapter.key}: round open at {game.current_stage} but nobody to act")
    testcase.fail(f"{adapter.key}: round at {game.current_stage} did not finish")


def play_out_with_calls(testcase, adapter, game, max_steps=200):
    """Play a Hold'em-family hand to its end with every NPC calling or checking.

    The human has folded, so it is never asked to act. Returns the board size after each
    street advance."""
    boards = []
    for _ in range(max_steps):
        if game.hand_complete:
            return boards
        if game.is_betting_round_complete():
            testcase.assertTrue(game.advance_after_betting_round())
            boards.append(len(game.community_cards))
            continue
        testcase.assertNotEqual(game.current_actor, 0, "the folded human was asked to act")
        adapter.npc_turn(game, game.current_actor, "call")
    testcase.fail(f"{adapter.key}: hand did not finish")


# ==================================================
# PURE CORE FUNCTIONS
# ==================================================

class BettingClosedTests(unittest.TestCase):
    def test_at_most_one_seat_with_chips_and_every_call_settled(self):
        # The only seat with chips has matched; the others are all-in.
        self.assertTrue(betting_closed([True, True, True], [500, 0, 0], [20, 20, 5], 20))
        # Nobody in the hand has chips.
        self.assertTrue(betting_closed([True, True], [0, 0], [10, 20], 20))
        # Nothing bet, one seat with chips: no free option left to take.
        self.assertTrue(betting_closed([True, True], [500, 0], [0, 0], 0))

    def test_an_unsettled_call_keeps_betting_open(self):
        self.assertFalse(betting_closed([True, True], [500, 0], [5, 20], 20))
        self.assertFalse(betting_closed([True, True, True], [1, 0, 0], [0, 40, 30], 40))

    def test_two_seats_with_chips_keep_betting_open(self):
        self.assertFalse(betting_closed([True, True, True], [500, 400, 0], [20, 20, 20], 20))
        self.assertFalse(betting_closed([True, True], [500, 400], [0, 0], 0))

    def test_seats_out_of_the_hand_do_not_count(self):
        # Folded seat 1 still has chips and owes nothing that matters.
        self.assertTrue(betting_closed([True, False, True], [500, 900, 0], [20, 0, 20], 20))
        self.assertTrue(betting_closed([True, False, True], [500, 900, 0], [20, 5, 20], 20))
        # Nobody in the hand at all.
        self.assertTrue(betting_closed([False, False], [500, 500], [0, 0], 0))


class BetToMatchTests(unittest.TestCase):
    def test_a_lone_seat_with_chips_matches_only_what_the_others_put_in(self):
        # The human's small blind 10 covers the all-in big blind 5 once the dealer folds.
        self.assertEqual(bet_to_match([True, True, False], [990, 0, 1000], [10, 5, 0], 20), 5)
        self.assertTrue(betting_closed([True, True, False], [990, 0, 1000], [10, 5, 0], 20))
        # Below it, it only has to call up to it.
        self.assertEqual(bet_to_match([True, True, False], [1000, 0, 990], [0, 3, 5], 5), 3)
        self.assertFalse(betting_closed([True, True, False], [1000, 0, 990], [0, 3, 5], 5))
        self.assertTrue(betting_closed([True, True, False], [997, 0, 990], [3, 3, 5], 5))
        # The largest of the other seats in the hand, and never more than the current bet.
        self.assertEqual(bet_to_match([True, True, True, False], [500, 0, 0, 9], [10, 5, 15, 20], 20), 15)
        self.assertEqual(bet_to_match([True, True], [500, 0], [0, 40], 30), 30)

    def test_the_bet_to_call_stands_otherwise(self):
        # Two seats with chips: the current bet stands.
        self.assertEqual(bet_to_match([True, True, True], [500, 500, 0], [10, 0, 5], 20), 20)
        # Nobody else in the hand: unchanged (the hand is over by folds).
        self.assertEqual(bet_to_match([True, False], [500, 500], [10, 0], 20), 20)
        # Nobody with chips: the most anyone really put in (nobody has anything to call).
        self.assertEqual(bet_to_match([True, True], [0, 0], [10, 5], 20), 10)


class SessionOverTests(unittest.TestCase):
    def test_the_human_with_no_chips(self):
        self.assertTrue(session_over([0, 100, 100]))
        self.assertTrue(session_over([-5, 100]))

    def test_nobody_else_with_chips(self):
        self.assertTrue(session_over([100, 0, 0]))
        self.assertTrue(session_over([100]))

    def test_play_goes_on_while_the_human_and_someone_else_have_chips(self):
        self.assertFalse(session_over([1, 1]))
        self.assertFalse(session_over([100, 0, 5]))

    def test_human_seat(self):
        self.assertTrue(session_over([100, 0], human_seat=1))
        self.assertFalse(session_over([0, 100, 3], human_seat=1))
        self.assertTrue(session_over([0, 100, 0], human_seat=1))


# ==================================================
# SHORT FORCED BETS
# ==================================================

class ShortForcedBetTests(unittest.TestCase):
    """A seat with fewer chips than its forced bet is dealt in, posts all it has and is all-in."""

    def deal_short(self, adapter, seat, rng):
        stacks = [1000] * adapter.seat_count
        stacks[seat] = 1
        game = adapter.new_game(rng)
        if adapter.key == "blind_mans_bluff":
            # start_hand posts the antes, then runs NPC turns until the human must act.
            adapter.set_stacks(game, stacks)
            return game, stacks, adapter.start_hand(game)
        # Hold'em and Draw: the short seat is the big blind. Stud: every seat antes.
        dealer = (seat - 2) % adapter.seat_count if adapter.forced_bets == "blinds" else 0
        return game, stacks, adapter.deal_forced_bets(game, stacks, dealer_seat=dealer)

    def test_a_one_chip_seat_posts_it_all_in_and_the_hand_completes(self):
        for adapter in ADAPTERS:
            if adapter.key == "five_o_poker":
                continue   # its kept rule: test_five_o_still_needs_the_full_ante
            for seat in (0, 2):
                with self.subTest(adapter.key, short_seat=seat):
                    rng = rng_for(adapter, f"short-{seat}")
                    game, stacks, started = self.deal_short(adapter, seat, rng)
                    self.assertTrue(started)
                    self.assertTrue(adapter.in_hand(game)[seat])
                    self.assertTrue(cards_of(adapter, game, seat))
                    self.assertEqual(adapter.contributions(game)[seat], 1)
                    if not adapter.hand_complete(game):
                        # (Blind Man's Bluff may already have settled the hand in start_hand.)
                        self.assertEqual(adapter.stacks(game)[seat], 0)
                    adapter.play_hand(game, rng)
                    self.assertTrue(adapter.hand_complete(game))
                    self.assertEqual(adapter.contributions(game)[seat], 1)
                    self.assertEqual(adapter.pot(game), 0)
                    self.assertEqual(adapter.total_chips(game), sum(stacks))
                    self.assertEqual(adapter.session_over(game), session_over(adapter.stacks(game)))

    def test_blind_mans_bluff_short_antes_make_side_pots(self):
        game = BMB.new_game(rng_for(BMB, "short-antes"))
        stacks = [3, 1, game.ante, 1000]
        BMB.set_stacks(game, stacks)
        self.assertTrue(BMB.start_hand(game))
        self.assertEqual(game.live_at_start, [0, 1, 2, 3])
        self.assertEqual(BMB.contributions(game), [3, 1, game.ante, game.ante])
        # Only seat 3 has chips left, so nobody can bet: straight to the showdown.
        self.assertTrue(game.hand_complete)
        self.assertEqual(sum(award["amount"] for award in game.last_pot_awards)
                         + sum(game.last_refunds.values()), 4 + 2 * game.ante)
        self.assertEqual(game.last_pot_awards[0]["amount"], 4)          # everyone's first chip
        self.assertEqual(sorted(game.last_pot_awards[0]["eligible"]), [0, 1, 2, 3])
        self.assertEqual(BMB.total_chips(game), sum(stacks))

    def test_five_o_still_needs_the_full_ante(self):
        # Kept different: a Five-O stack below the ante ends the session before anything is posted.
        rng = rng_for(FIVE_O, "short")
        ante = FIVE_O.new_game(rng).ante
        for stacks in ([1, 500], [500, 1], [ante - 1, 500], [500, ante - 1], [0, 500]):
            with self.subTest(stacks=stacks):
                game = FIVE_O.new_game(rng, stacks)
                self.assertFalse(FIVE_O.start_hand(game))
                self.assertTrue(FIVE_O.session_over(game))
                self.assertEqual(FIVE_O.stacks(game), stacks)
        game = FIVE_O.new_game(rng, [ante, 500])
        self.assertTrue(FIVE_O.start_hand(game))
        self.assertEqual(FIVE_O.contributions(game), [ante, ante])


# ==================================================
# BUSTED SEATS AND THE END OF A SESSION
# ==================================================

class BustedAndSessionOverTests(unittest.TestCase):
    def test_the_human_with_no_chips_ends_the_session(self):
        for adapter in ADAPTERS:
            with self.subTest(adapter.key):
                stacks = [0] + [1000] * (adapter.seat_count - 1)
                game = adapter.new_game(rng_for(adapter, "human-bust"), stacks)
                self.assertFalse(adapter.start_hand(game))
                self.assertTrue(adapter.session_over(game))
                self.assertEqual(adapter.stacks(game), stacks)

    def test_every_npc_with_no_chips_ends_the_session(self):
        for adapter in ADAPTERS:
            with self.subTest(adapter.key):
                stacks = [1000] + [0] * (adapter.seat_count - 1)
                game = adapter.new_game(rng_for(adapter, "npc-bust"), stacks)
                self.assertFalse(adapter.start_hand(game))
                self.assertTrue(adapter.session_over(game))
                self.assertEqual(adapter.stacks(game), stacks)

    def test_a_zero_chip_npc_is_not_dealt_in(self):
        for adapter in ADAPTERS:
            with self.subTest(adapter.key):
                rng = rng_for(adapter, "zero-npc")
                if adapter.seat_count == 2:
                    # Five-O is heads-up: its only NPC at 0 chips ends the session instead.
                    game = adapter.new_game(rng, [1000, 0])
                    self.assertFalse(adapter.start_hand(game))
                    self.assertTrue(adapter.session_over(game))
                    continue
                stacks = [1000] * adapter.seat_count
                stacks[2] = 0
                game = adapter.new_game(rng, stacks)
                self.assertTrue(adapter.start_hand(game))
                self.assertFalse(adapter.session_over(game))
                self.assertFalse(adapter.in_hand(game)[2])
                self.assertEqual(cards_of(adapter, game, 2), [])
                self.assertEqual(adapter.contributions(game)[2], 0)
                adapter.play_hand(game, rng)
                self.assertFalse(adapter.in_hand(game)[2])
                self.assertEqual(adapter.stacks(game)[2], 0)
                self.assertEqual(adapter.contributions(game)[2], 0)
                self.assertEqual(adapter.total_chips(game), sum(stacks))

    def test_session_over_follows_the_shared_rule_after_every_hand(self):
        small = [1, 2, 4, 7, 12, 25, 60, 200]
        for adapter in ADAPTERS:
            with self.subTest(adapter.key):
                rng = rng_for(adapter, "session-rule")
                hands = 0
                while hands < 150:
                    stacks = [rng.choice(small) for _ in range(adapter.seat_count)]
                    game = adapter.new_game(rng, stacks)
                    for _ in range(40):
                        if not adapter.start_hand(game):
                            self.assertTrue(adapter.session_over(game))
                            break
                        adapter.play_hand(game, rng)
                        hands += 1
                        after = adapter.stacks(game)
                        if adapter.key == "five_o_poker":
                            expected = min(after) < game.ante   # kept: below the ante ends it
                        else:
                            # Written out, not core.session_over (which most adapters call):
                            # the human has no chips, or no NPC has any.
                            expected = after[0] <= 0 or all(stack <= 0 for stack in after[1:])
                        self.assertEqual(adapter.session_over(game), expected, after)
                        if adapter.key in HOLDEM_FAMILY:
                            # The busted flags refreshed at the end of the hand say the same.
                            self.assertEqual(game.player_busted or game.all_npcs_busted(), expected)
                        if expected:
                            break

    def test_blind_mans_bluff_plays_on_below_the_ante_and_ends_at_zero(self):
        real_deck = bluff_module.build_standard_deck

        def human_gets_the_two(rng=None):
            # start_hand pops one card per seat from the end: the human gets the 2 of Clubs
            # and the NPCs an ace, a king and a queen, so the human loses every showdown.
            deck = real_deck(rng)
            top = [next(card for card in deck if card["rank"] == rank and card["suit"] == suit)
                   for rank, suit in (("Q", "Hearts"), ("K", "Hearts"), ("A", "Hearts"), ("2", "Clubs"))]
            return [card for card in deck if card not in top] + top

        game = BMB.new_game(rng_for(BMB, "below-ante"))
        ante = game.ante
        game.player_stack = ante + 2
        with forced_ai(BMB, "check"), mock.patch.object(bluff_module, "build_standard_deck", human_gets_the_two):
            # Hand 1: the human opens and checks; everyone checks; the human loses its ante.
            self.assertTrue(BMB.start_hand(game))
            self.assertTrue(game.player_check())
            self.assertTrue(game.hand_complete)
            self.assertEqual(game.player_stack, 2)
            self.assertFalse(game.session_complete)
            self.assertTrue(game.can_start_next_hand())
            # Hand 2: dealt in with 2 chips, all-in on the ante; no action is offered.
            self.assertTrue(BMB.start_hand(game))
            self.assertIn(0, game.live_at_start)
            self.assertEqual(game.hand_contributions[0], 2)
            self.assertTrue(game.hand_complete)
            self.assertEqual(game.player_stack, 0)
            self.assertTrue(game.session_complete)
            self.assertFalse(game.can_start_next_hand())
            self.assertFalse(BMB.start_hand(game))


# ==================================================
# ALL-IN RUN-OUTS
# ==================================================

class RunOutTests(unittest.TestCase):
    """With every opponent all-in and the calls settled, the hand runs out without more betting."""

    SHORT = 3   # below every forced bet: an opponent is all-in once it posts or calls

    def test_every_opponent_all_in_runs_out_to_showdown(self):
        for adapter in ADAPTERS:
            with self.subTest(adapter.key):
                if adapter.key == "five_o_poker":
                    self.five_o_never_runs_out()
                    continue
                rng = rng_for(adapter, "run-out")
                stacks = [1000] + [self.SHORT] * (adapter.seat_count - 1)
                game = adapter.new_game(rng, stacks)
                with forced_ai(adapter, "call"):
                    self.assertTrue(adapter.start_hand(game))
                    if adapter.key in HOLDEM_FAMILY:
                        call_down_round(self, adapter, game)
                    # Every opponent has put in all it had and is still in the hand.
                    self.assertEqual(adapter.contributions(game)[1:], [self.SHORT] * (adapter.seat_count - 1))
                    self.assertTrue(all(adapter.in_hand(game)))
                    if not adapter.hand_complete(game):
                        self.assertEqual(adapter.stacks(game)[1:], [0] * (adapter.seat_count - 1))
                    self.assertFalse(adapter.can_raise(game, 0))
                    labels = []
                    while not adapter.hand_complete(game):
                        self.assertLess(len(labels), 20)
                        if adapter.key in HOLDEM_FAMILY and game.current_stage != "draw":
                            self.assertTrue(game.is_betting_round_complete(), game.current_stage)
                            self.assertFalse(game.can_player_raise())
                            if adapter.key == "texas_holdem":
                                self.assertTrue(game.should_reveal_runout_hands())
                        labels.append(adapter.step(game, rng))
                self.assertTrue(adapter.hand_complete(game))
                self.assertEqual(adapter.total_chips(game), sum(stacks))
                # Settled at a showdown that every seat took part in, not by folds.
                self.assertEqual(sorted(adapter.awards(game)[0]["eligible"]), list(range(adapter.seat_count)))
                if adapter.key == "texas_holdem":
                    self.assertEqual(labels, ["advance"] * 4)     # flop, turn, river, showdown
                    self.assertEqual(len(game.community_cards), 5)
                elif adapter.key == "seven_card_stud":
                    self.assertEqual(labels, ["advance"] * 5)     # fourth .. seventh, showdown
                    for seat in range(adapter.seat_count):
                        self.assertEqual(len(cards_of(adapter, game, seat)), 7)
                elif adapter.key == "five_card_draw":
                    self.assertEqual(labels, ["advance", "draw", "advance"])
                    self.assertEqual(game.current_stage, "showdown")
                else:
                    self.assertEqual(labels, [])                  # BMB: showdown at once

    def five_o_never_runs_out(self):
        # Not applicable to Five-O: one betting round after every card is placed, and the bet is
        # capped by the smaller stack, so a seat is never short of a call and nothing is left
        # to deal.
        adapter = FIVE_O
        rng = rng_for(adapter, "run-out")
        for _ in range(80):
            stacks = [rng.choice([5, 8, 15, 40, 120, 500]) for _ in range(2)]
            game = adapter.new_game(rng, stacks)
            if not adapter.start_hand(game):
                continue
            while not adapter.hand_complete(game):
                if game.phase == "betting":
                    self.assertTrue(all(len(column) == 5 for column in game.player_columns + game.npc_columns))
                    owed = [game.current_bet - game.player_betting_paid,
                            game.current_bet - game.npc_betting_paid]
                    for seat in (0, 1):
                        self.assertGreaterEqual(adapter.stacks(game)[seat], owed[seat])
                adapter.step(game, rng)

    def test_one_seat_with_chips_still_answers_a_short_all_in(self):
        # The run-out waits for the last call (Blind Man's Bluff runs its turns in the engine).
        game = BMB.new_game(rng_for(BMB, "answer"))
        BMB.force_all_in_opponents(game, 0, 40)
        game._advance(0, inclusive=True)
        self.assertFalse(game.hand_complete)
        self.assertEqual(game.current_actor, 0)
        self.assertEqual(game.get_player_actions(), ["fold", "call"])
        self.assertTrue(game.player_call())
        self.assertTrue(game.hand_complete)
        # With nothing to call there is no free option to take: straight to the showdown.
        game = BMB.new_game(rng_for(BMB, "answer"))
        BMB.force_all_in_opponents(game, 0, 0)
        game._advance(0, inclusive=True)
        self.assertTrue(game.hand_complete)
        self.assertEqual(game.player_stack, FORCED_STACK + game.last_refunds.get(0, 0)
                         + sum(award["payouts"].get(0, 0) for award in game.last_pot_awards))


class LoneSeatAfterFoldsTests(unittest.TestCase):
    """F1: a fold that leaves one seat with chips against all-in seats asks only for what they put in."""

    def test_a_posted_small_blind_that_covers_the_all_in_big_blind_is_not_asked_to_call(self):
        # The repro: 3-handed, the human posts the small blind 10, the big blind is all-in for 5
        # and the dealer folds. The human used to be asked to call 10 more, only to get it back.
        for key in ("texas_holdem", "five_card_draw"):
            adapter = ADAPTERS_BY_KEY[key]
            with self.subTest(key):
                rng = rng_for(adapter, "lone-blind")
                game = adapter.new_game(rng, seats=3)
                self.assertTrue(adapter.deal_forced_bets(game, [1000, 5, 1000], dealer_seat=2))
                self.assertEqual((game.small_blind_index, game.big_blind_index), (0, 1))
                self.assertEqual(game.seat_round_bets(), [10, 5, 0])
                self.assertEqual(game.current_bet, 20)    # two seats can still act: the nominal blind
                self.assertEqual(game.current_actor, 2)
                total = adapter.total_chips(game)

                adapter.npc_turn(game, 2, "fold")
                self.assertEqual(game.current_bet, 5)
                self.assertEqual(game.get_player_amount_to_call(), 0)
                self.assertFalse(game.can_player_call())
                self.assertFalse(game.can_player_raise())
                self.assertTrue(game.is_betting_round_complete())
                self.assertNotEqual(game.current_actor, 0)

                labels = adapter.play_hand(game, rng)
                self.assertFalse([label for label in labels if label.startswith("human:")], labels)
                self.assertEqual(game.current_stage, "showdown")
                self.assertEqual(game.player_hand_contribution, 10)
                self.assertEqual(adapter.refunds(game), {0: 5})   # the uncalled half of the blind
                self.assertEqual(adapter.total_chips(game), total)

    def test_stud_a_lone_seat_calls_only_the_short_bring_in(self):
        # Stud's version: seat 1 posts a short all-in bring-in of 3 (the bring-in is 5); seat 2
        # folds, so the human only has to call the 3, not the nominal 5.
        adapter = ADAPTERS_BY_KEY["seven_card_stud"]
        rng = rng_for(adapter, "lone-bring-in")
        game = adapter.new_game(rng, seats=3)
        self.assertTrue(adapter.deal_forced_bets(game, [1000, game.ante_amount + 3, 1000], bring_in_seat=1))
        self.assertEqual(game.seat_round_bets(), [0, 3, 0])
        self.assertEqual(game.current_bet, game.bring_in_amount)
        self.assertEqual(game.current_actor, 2)
        total = adapter.total_chips(game)

        adapter.npc_turn(game, 2, "fold")
        self.assertEqual(game.current_actor, 0)
        self.assertEqual(game.get_player_amount_to_call(), 3)
        self.assertFalse(game.can_player_raise())
        self.assertTrue(game.player_call())
        self.assertEqual(game.player_round_bet, 3)
        self.assertTrue(game.is_betting_round_complete())
        labels = adapter.play_hand(game, rng)
        self.assertFalse([label for label in labels if label.startswith("human:")], labels)
        self.assertEqual(adapter.refunds(game), {})
        self.assertEqual(adapter.total_chips(game), total)

    def test_blind_mans_bluff_uses_the_same_rule(self):
        # Blind Man's Bluff has no forced round bets (its antes are dead), so its current bet is
        # always some seat's round bet and the case cannot arise in play. Its run-out check is the
        # same shared rule: forced into the state, the hand goes straight to the showdown.
        game = BMB.new_game(rng_for(BMB, "lone-seat"))
        BMB.force_all_in_opponents(game, 0, 20)
        game.round_bets = [10, 5, 0, 0]
        game.hand_contributions = list(game.round_bets)
        game.folded = [False, False, True, True]
        game.pot = sum(game.round_bets)
        total = BMB.total_chips(game)
        game._advance(0, inclusive=True)
        self.assertTrue(game.hand_complete)
        self.assertEqual(game.last_refunds, {0: 5})
        self.assertEqual(BMB.total_chips(game), total)


def old_should_reveal_runout_hands(game):
    """TexasHoldemGame.should_reveal_runout_hands before group 4."""
    if game.current_stage not in ("preflop", "flop", "turn", "river") or game.hand_complete:
        return False
    if len(game.get_active_player_indexes()) < 2 or len(game.get_actionable_player_indexes()) > 1:
        return False
    if (not game.player_folded and not game.player_busted and game.player_stack > 0
            and game.player_round_bet < game.current_bet):
        return False
    for index in range(len(game.npcs)):
        if (not game.npc_folded[index] and not game.npc_busted[index] and game.npc_stacks[index] > 0
                and game.npc_round_bets[index] < game.current_bet):
            return False
    return True


def old_is_betting_round_complete(game):
    """TexasHoldemGame.is_betting_round_complete before group 4, without its flag repairs."""
    active = game.get_active_player_indexes()
    actionable = game.get_actionable_player_indexes()
    bets = game.seat_round_bets()
    if any(bets[seat] < game.current_bet for seat in actionable):
        return False
    if len(active) > 1 and len(actionable) <= 1:
        return True
    if 0 in actionable and not game.player_has_acted:
        return False
    return all(game.npc_has_acted[seat - 1] for seat in actionable if seat != 0)


class SameAnswersTests(unittest.TestCase):
    """The run-out predicates now use core.betting_closed and give the same answers as before."""

    def test_holdem_family_predicates_match_the_old_rules(self):
        small = [1, 3, 8, 20, 60, 150, 1000]
        for key in HOLDEM_FAMILY:
            adapter = ADAPTERS_BY_KEY[key]
            with self.subTest(key):
                rng = rng_for(adapter, "same-answers")
                checked = 0
                for _ in range(120):
                    stacks = [rng.choice(small) for _ in range(adapter.seat_count)]
                    game = adapter.new_game(rng, stacks)
                    if not adapter.start_hand(game):
                        continue
                    for _ in range(3000):
                        reveal, complete = old_should_reveal_runout_hands(game), old_is_betting_round_complete(game)
                        self.assertEqual(game.should_reveal_runout_hands(), reveal)
                        if game.current_stage != "draw":
                            self.assertEqual(game.is_betting_round_complete(), complete)
                        checked += 1
                        if adapter.hand_complete(game):
                            break
                        adapter.step(game, rng)
                self.assertGreater(checked, 1000)


# ==================================================
# NEW-3: PLAY GOES ON AFTER THE HUMAN FOLDS
# ==================================================

def open_street(testcase, adapter, game):
    """Deal a 3-handed hand and call the first round, so the next street opens with nothing bet.

    Hold'em: the flop; Draw: after the draw; Stud: fourth street."""
    testcase.assertTrue(adapter.deal_forced_bets(game, [1000, 1000, 1000], dealer_seat=1))
    call_down_round(testcase, adapter, game)
    testcase.assertTrue(game.advance_after_betting_round())
    if game.current_stage == "draw":
        testcase.assertTrue(game.player_draw([]))
    testcase.assertEqual(game.current_stage, OPEN_STREET[adapter.key])
    testcase.assertEqual(game.current_bet, 0)


def bet_into_the_human_and_fold(testcase, adapter, game):
    """NPC seat 2 bets, the human folds with NPC seat 1 still to act. Returns the cards dealt."""
    adapter.give_turn(game, 2)
    adapter.npc_turn(game, 2, "bet")
    testcase.assertGreater(game.current_bet, 0)
    testcase.assertEqual(game.current_actor, 0)
    testcase.assertTrue(game.can_player_call())
    return table_cards(adapter, game)


class PlayAfterHumanFoldsTests(unittest.TestCase):
    def test_the_last_npc_still_answers_the_bet(self):
        for key in HOLDEM_FAMILY:
            adapter = ADAPTERS_BY_KEY[key]
            for answer in ("call", "fold"):
                with self.subTest(key, answer=answer):
                    game = adapter.new_game(rng_for(adapter, f"fold-{answer}"), seats=3)
                    open_street(self, adapter, game)
                    total = adapter.total_chips(game)
                    stage = game.current_stage
                    dealt = bet_into_the_human_and_fold(self, adapter, game)

                    self.assertTrue(game.player_fold())
                    self.assertFalse(game.hand_complete)
                    self.assertEqual(game.current_stage, stage)
                    self.assertEqual(table_cards(adapter, game), dealt)   # nothing dealt out
                    self.assertEqual(game.current_actor, 1)
                    self.assertFalse(game.is_betting_round_complete())

                    adapter.npc_turn(game, 1, answer)
                    self.assertTrue(game.npc_action_texts[0].startswith(
                        "Called" if answer == "call" else "Folded"))
                    if answer == "fold":
                        self.assertTrue(game.hand_complete)
                        self.assertEqual(adapter.winners(game), [2])
                        self.assertEqual(table_cards(adapter, game), dealt)
                    else:
                        boards = play_out_with_calls(self, adapter, game)
                        self.assertEqual(game.current_stage, "showdown")
                        self.assertEqual(sorted(adapter.awards(game)[0]["eligible"]), [1, 2])
                        self.assertTrue(set(adapter.winners(game)) <= {1, 2})
                        if key == "texas_holdem":
                            self.assertEqual(boards, [4, 5, 5])    # turn, river, showdown
                        if key == "seven_card_stud":
                            for seat in (1, 2):
                                self.assertEqual(len(cards_of(adapter, game, seat)), 7)
                    self.assertEqual(adapter.total_chips(game), total)

    def test_blind_mans_bluff_npcs_play_on_after_the_human_folds(self):
        # Blind Man's Bluff runs NPC turns inside the engine: after the human folds, the NPC
        # still to act answers the bet at once and the NPCs settle the hand between them.
        game = BMB.new_game(rng_for(BMB, "fold"), seats=3)
        total = BMB.total_chips(game)
        game.hand_number = 2   # hand 3: seat 2 opens, then the human, then seat 1
        with forced_ai(BMB, "bet", "call"):
            self.assertTrue(BMB.start_hand(game))
            self.assertEqual(game.opening_index, 2)
            self.assertGreater(game.current_bet, 0)
            self.assertEqual(game.current_actor, 0)
            self.assertIn(1, game.pending)
            self.assertTrue(game.player_fold())
        self.assertTrue(game.hand_complete)
        self.assertTrue(game.last_actions[1].startswith("Called"))
        self.assertEqual(sorted(game.last_pot_awards[0]["eligible"]), [1, 2])
        self.assertEqual(BMB.total_chips(game), total)

    def test_five_o_heads_up_fold_ends_the_hand(self):
        # Not applicable to Five-O: it is heads-up, so the human's fold leaves one seat, which
        # takes the pot at once.
        game = FIVE_O.new_game(rng_for(FIVE_O, "fold"))
        total = FIVE_O.total_chips(game)
        with forced_ai(FIVE_O, "bet"):
            self.assertTrue(FIVE_O.start_hand(game))
            FIVE_O.place_all_cards(game)
            self.assertTrue(game.player_check())          # hand 1: the human opens
            game.pending_npc_at -= 1000.0
            game.update()
        self.assertEqual(game.bet_state, "player_response")
        self.assertTrue(game.player_fold())
        self.assertTrue(game.hand_complete)
        self.assertEqual(FIVE_O.winners(game), [1])
        self.assertEqual(FIVE_O.total_chips(game), total)


class HoldemScreenAfterFoldTests(unittest.TestCase):
    """After a fold the Hold'em screen runs the NPC turns and streets on its timers."""

    def setUp(self):
        self.screen = ScreenHarness(self)
        self.adapter = ADAPTERS_BY_KEY["texas_holdem"]
        self.game = self.screen.stub(
            holdem_screen, self.adapter.new_game(rng_for(self.adapter, "screen-fold"), seats=3))
        for name in ("next_npc_action_at", "round_advance_at", "next_hand_at", "session_end_at",
                     "hand_win_sound_at"):
            setattr(state, "texas_holdem_" + name, 0)
        state.texas_holdem_starting_stack = 1000
        state.texas_holdem_last_processed_showdown_hand = 0
        for name, value in (("post_texas_holdem_chat", lambda entry: None),
                            ("generate_npc_action_chat", lambda game, index: None)):
            patcher = mock.patch.object(holdem_screen, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def click(self, action):
        state.game_mouse_pos = (500, 500)
        patches = (
            mock.patch.object(holdem_screen, "is_holdem_options_open", return_value=False),
            mock.patch.object(holdem_screen, "handle_holdem_manual_bet_click", return_value=False),
            mock.patch.object(holdem_screen, "handle_holdem_panel_click", return_value=False),
            mock.patch.object(holdem_screen, "update_holdem_bet_slider", return_value=False),
            mock.patch.object(holdem_screen, "get_texas_holdem_action", return_value=action),
        )
        with contextlib.ExitStack() as stack:
            for patcher in patches:
                stack.enter_context(patcher)
            holdem_screen.loop_event_texas_holdem(
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(500, 500), button=1))

    def frame(self, ticks):
        self.screen.ticks = ticks
        holdem_screen.loop_late_texas_holdem()

    def test_npc_turns_and_streets_follow_the_timers_after_a_fold(self):
        game = self.game
        open_street(self, self.adapter, game)
        bet_into_the_human_and_fold(self, self.adapter, game)
        npc_delay, street_delay = get_holdem_npc_delay(), get_holdem_street_delay()
        total = self.adapter.total_chips(game)

        with forced_ai(self.adapter, "call"):
            self.screen.ticks = 10_000
            self.click(holdem_screen.HOLDEM_ACTION_FOLD)
            self.assertTrue(game.player_folded)
            self.assertFalse(game.hand_complete)
            self.assertEqual(len(game.community_cards), 3)
            self.assertEqual(game.current_actor, 1)

            # The NPC waits for the table's NPC delay, as after any human action.
            self.frame(10_000)
            self.assertEqual(state.texas_holdem_next_npc_action_at, 10_000 + npc_delay)
            self.frame(10_000 + npc_delay - 1)
            self.assertFalse(game.npc_has_acted[0])
            self.frame(10_000 + npc_delay)
            self.assertTrue(game.npc_action_texts[0].startswith("Called"))

            # The round is closed; the turn waits for the street delay.
            closed_at = 10_000 + npc_delay
            self.assertEqual(len(game.community_cards), 3)
            self.assertEqual(state.texas_holdem_round_advance_at, closed_at + street_delay)
            self.frame(closed_at + street_delay - 1)
            self.assertEqual(len(game.community_cards), 3)

            # Play on, 50 ms a frame: one street at a time, each after its delays.
            ticks, boards, dealt_at = closed_at + street_delay - 1, [3], [closed_at]
            while not game.hand_complete:
                ticks += 50
                self.assertLess(ticks, 200_000)
                self.frame(ticks)
                if len(game.community_cards) != boards[-1]:
                    boards.append(len(game.community_cards))
                    dealt_at.append(ticks)
        self.assertEqual(boards, [3, 4, 5])
        self.assertGreaterEqual(dealt_at[1] - dealt_at[0], street_delay)
        # The river waits for both NPCs to check (an NPC delay each) and the street delay.
        self.assertGreaterEqual(dealt_at[2] - dealt_at[1], 2 * npc_delay + street_delay)
        self.assertEqual(game.current_stage, "showdown")
        self.assertEqual(sorted(game.last_pot_awards[0]["eligible"]), [1, 2])
        self.assertEqual(self.adapter.total_chips(game), total)


if __name__ == "__main__":
    unittest.main()
