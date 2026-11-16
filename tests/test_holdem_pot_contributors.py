"""Showdown pot records can name the seats that paid into each pot (Phase 11, B79).

Multiplayer rooms give XP for winning a pot, but a pot made only of the
winners' own chips (for example two all-in players splitting what they both
put in) is not a win. TexasHoldemGame.record_pot_contributors (default False)
adds 'contributors' to every showdown pot record; the room tables turn it on.
Single-player keeps the shared record shape, and the recap and pot log read
the same with and without the key.
"""
import os
import random
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from solitaireplus.games.poker import recap
from solitaireplus.games.poker.core import build_pots
from solitaireplus.games.poker.holdem import TexasHoldemGame
from tests.support.poker_variants import ADAPTERS_BY_KEY

SHARED_KEYS = {"amount", "eligible", "winners", "payouts", "share", "remainder", "hand"}
HOLDEM_FAMILY = ("texas_holdem", "five_card_draw", "seven_card_stud")
# Seats 1 and 3 tie; seat 0 is a short all-in; seats 2 and 4 folded dead money.
CONTRIBUTIONS = [50, 100, 20, 100, 20]
LIVE = [True, True, False, True, False]
RANKS = [10, 13, 2, 13, 2]


def forced(adapter, record, seed=1):
    game = adapter.new_game(random.Random(f"contributors-{adapter.key}-{seed}"))
    if record:
        game.record_pot_contributors = True
    return adapter.force_showdown(game, CONTRIBUTIONS, LIVE, RANKS, 0)


def hand_log(game):
    return [(event["type"], event["text"]) for event in game.get_hand_history_events()]


class PotContributorTests(unittest.TestCase):
    def test_default_off_keeps_the_shared_record_shape(self):
        self.assertFalse(TexasHoldemGame.record_pot_contributors)
        for key in HOLDEM_FAMILY:
            with self.subTest(key):
                game = forced(ADAPTERS_BY_KEY[key], record=False)
                self.assertEqual(len(game.last_pot_awards), 2)
                for award in game.last_pot_awards:
                    self.assertEqual(set(award), SHARED_KEYS)

    def test_forced_side_pot_names_every_contributor(self):
        for key in HOLDEM_FAMILY:
            with self.subTest(key):
                game = forced(ADAPTERS_BY_KEY[key], record=True)
                awards = game.last_pot_awards
                self.assertEqual([award["amount"] for award in awards], [190, 100])
                # The main pot holds a chip from every seat (the folded seats' dead money too);
                # the side pot only the two 100-chip stacks.
                self.assertEqual([award["contributors"] for award in awards], [[0, 1, 2, 3, 4], [1, 3]])
                for award in awards:
                    self.assertEqual(set(award), SHARED_KEYS | {"contributors"})
                    self.assertLessEqual(set(award["eligible"]), set(award["contributors"]))
                # The side pot is only the winners' own chips: its contributors are its winners.
                self.assertEqual(set(awards[1]["contributors"]), set(awards[1]["winners"]))

    def test_every_showdown_pot_in_played_side_pot_hands_has_contributors(self):
        adapter = ADAPTERS_BY_KEY["texas_holdem"]
        side_pot_hands = 0
        for seed in range(40):
            rng = random.Random(seed)
            game = adapter.new_game(rng, stacks=[rng.choice((60, 150, 400, 1000)) for _ in range(5)])
            game.record_pot_contributors = True
            adapter.start_hand(game)
            adapter.play_hand(game, rng)
            if game.current_stage != "showdown" or not game.community_cards or len(game.last_pot_awards) < 2:
                continue
            if all(award["hand"] == "" for award in game.last_pot_awards):
                continue    # a fold win: one record, no contributors needed
            side_pot_hands += 1
            contributions = adapter.contributions(game)
            pots, _ = build_pots(contributions, [seat in award_seats(game) for seat in range(5)])
            self.assertEqual([award["contributors"] for award in game.last_pot_awards],
                             [pot["contributors"] for pot in pots], f"seed {seed}")
            for award in game.last_pot_awards:
                self.assertGreaterEqual(len(award["contributors"]), 2)
                self.assertTrue(all(contributions[seat] > 0 for seat in award["contributors"]))
                self.assertLessEqual(set(award["eligible"]), set(award["contributors"]))
        self.assertGreater(side_pot_hands, 3)

    def test_recap_and_pot_log_ignore_the_key(self):
        for key in HOLDEM_FAMILY:
            with self.subTest(key):
                plain = forced(ADAPTERS_BY_KEY[key], record=False)
                marked = forced(ADAPTERS_BY_KEY[key], record=True)
                self.assertEqual(recap.recap_lines(marked), recap.recap_lines(plain))
                self.assertEqual(recap.recap_display_lines(marked), recap.recap_display_lines(plain))
                self.assertEqual(hand_log(marked), hand_log(plain))
                self.assertIn("pot_award", [kind for kind, _ in hand_log(plain)])   # the side-pot log ran
                self.assertEqual(marked.result_text, plain.result_text)
                self.assertEqual(marked.seat_stacks(), plain.seat_stacks())
                self.assertEqual(marked.winner_indexes, plain.winner_indexes)

    def test_fold_win_record_is_unchanged(self):
        adapter = ADAPTERS_BY_KEY["texas_holdem"]
        game = adapter.new_game(random.Random("contributors-fold"))
        game.record_pot_contributors = True
        adapter.force_fold_win(game, [60, 20, 0, 0, 0], 0)
        [award] = game.last_pot_awards
        self.assertEqual(set(award), SHARED_KEYS)


def award_seats(game):
    """Seats that held a live hand at the showdown (every eligible seat of some pot)."""
    return {seat for award in game.last_pot_awards for seat in award["eligible"]}


if __name__ == "__main__":
    unittest.main()
