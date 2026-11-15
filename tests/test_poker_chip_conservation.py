"""Chips are never created or destroyed at any poker table (B86 groups 1 and 2; the B37 test).

Each variant plays 1,000 seeded random hands through tests/support/poker_variants.py. Every
session draws its per-seat stacks from STACK_CHOICES, so forced bets are often short and
all-ins and side pots are common. After every single step the chips on the table (stacks plus
pot) must equal the session's total and no stack may be negative; after every hand the pot is
empty. A new session starts whenever the old one is over or a hand cannot start.

After every hand the shared award records must also add up (group 2): the pots awarded plus
the chips returned equal the chips put in that hand, each pot's payouts add up to the pot, and
every winner was paid. No seat may get back more than its own chips plus what it matched of
each other seat's (B86 review: a short all-in left alone by the folds won unmatched chips).

B36 (group 3): the same hands are replayed with every bet/raise entry point wrapped. Whenever a
bet or raise lifts the current bet, another seat still in the hand must have had chips to
answer it; nobody may bet or raise into a table where nobody can respond.
"""
import random
import unittest

from tests.support.poker_variants import ADAPTERS

HANDS_PER_VARIANT = 1000
STACK_CHOICES = (1, 3, 8, 20, 60, 150, 400, 1000, 2500)
MAX_STEPS_PER_HAND = 3000


class ChipConservationTests(unittest.TestCase):
    def check_table(self, adapter, game, total, where):
        stacks, pot = adapter.stacks(game), adapter.pot(game)
        self.assertEqual(adapter.total_chips(game), total, f"{where}: stacks {stacks}, pot {pot}")
        self.assertGreaterEqual(min(stacks), 0, f"{where}: negative stack in {stacks}")
        self.assertGreaterEqual(pot, 0, f"{where}: negative pot")

    def check_awards(self, adapter, game, where):
        awards, refunds = adapter.awards(game), adapter.refunds(game)
        self.assertTrue(awards, f"{where}: a finished hand left no award record")
        self.assertEqual(sum(award["amount"] for award in awards) + sum(refunds.values()),
                         sum(adapter.contributions(game)),
                         f"{where}: awards {awards}, refunds {refunds}")
        paid = set()
        for award in awards:
            self.assertEqual(sum(award["payouts"].values()), award["amount"], f"{where}: {award}")
            paid.update(seat for seat, chips in award["payouts"].items() if chips > 0)
        self.assertLessEqual(set(adapter.winners(game)), paid, f"{where}: a winner without a payout")
        self.assertEqual(game.last_resolved_pot, sum(award["amount"] for award in awards), where)
        # Nobody gets back more than its own chips plus what it matched of every other seat's
        # (a short all-in wins at most its own stake from each opponent, fold wins included).
        contributions = adapter.contributions(game)
        for seat, own in enumerate(contributions):
            received = sum(award["payouts"].get(seat, 0) for award in awards) + refunds.get(seat, 0)
            matched = own + sum(min(own, other) for other_seat, other in enumerate(contributions)
                                if other_seat != seat)
            self.assertLessEqual(received, matched,
                                 f"{where}: seat {seat} got {received} from contributions {contributions}")

    def play_variant(self, adapter, wagers=None):
        """Play HANDS_PER_VARIANT seeded hands; with a `wagers` list, log every bet and raise."""
        rng = random.Random("chips-" + adapter.key)
        choices = [value for value in STACK_CHOICES if value >= adapter.minimum_stack()]
        hands = sessions = all_in_hands = 0
        while hands < HANDS_PER_VARIANT:
            stacks = [rng.choice(choices) for _ in range(adapter.seat_count)]
            game = adapter.new_game(rng, stacks)
            if wagers is not None:
                adapter.record_wagers(game, wagers)
            sessions += 1
            total = sum(stacks)
            self.check_table(adapter, game, total, f"{adapter.key} session {sessions} start")
            while hands < HANDS_PER_VARIANT and not adapter.session_over(game):
                had_chips = [stack > 0 for stack in adapter.stacks(game)]
                if not adapter.start_hand(game):
                    break
                where = f"{adapter.key} session {sessions} hand {game.hand_number}"
                self.check_table(adapter, game, total, f"{where} after the deal")
                went_all_in = False
                for step in range(MAX_STEPS_PER_HAND):
                    if adapter.hand_complete(game):
                        break
                    went_all_in |= any(chips and stack == 0
                                       for chips, stack in zip(had_chips, adapter.stacks(game)))
                    label = adapter.step(game, rng)
                    self.check_table(adapter, game, total, f"{where} after step {step} ({label})")
                else:
                    self.fail(f"{where} did not finish in {MAX_STEPS_PER_HAND} steps")
                self.assertEqual(adapter.pot(game), 0, f"{where}: chips left in the pot")
                self.check_awards(adapter, game, where)
                all_in_hands += went_all_in
                hands += 1
        # The short stacks really do force all-ins (Five-O: a stack that only covers the ante).
        self.assertGreater(all_in_hands, 0, f"{adapter.key}: no all-in in {hands} hands")
        return sessions


def _conservation_test(adapter):
    def test(self):
        self.play_variant(adapter)

    test.__doc__ = f"{adapter.key}: {HANDS_PER_VARIANT} seeded random hands conserve every chip."
    return test


def _nobody_to_respond_test(adapter):
    def test(self):
        wagers = []
        self.play_variant(adapter, wagers)
        self.assertTrue(wagers, f"{adapter.key}: no bet or raise in {HANDS_PER_VARIANT} hands")
        unanswerable = [seat for seat, others_can_respond in wagers if not others_can_respond]
        self.assertEqual(unanswerable, [],
                         f"{adapter.key}: {len(unanswerable)} of {len(wagers)} bets/raises had "
                         f"nobody left to respond (seats {sorted(set(unanswerable))})")

    test.__doc__ = (f"{adapter.key}: in {HANDS_PER_VARIANT} seeded random hands nobody bets or "
                    f"raises when nobody can respond (B36).")
    return test


for _adapter in ADAPTERS:
    setattr(ChipConservationTests, f"test_{_adapter.key}_conserves_chips", _conservation_test(_adapter))
    setattr(ChipConservationTests, f"test_{_adapter.key}_never_wagers_with_nobody_to_respond",
            _nobody_to_respond_test(_adapter))
del _adapter


if __name__ == "__main__":
    unittest.main()
