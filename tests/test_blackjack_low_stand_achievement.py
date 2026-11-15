"""B30: the "Low Roller" achievement needs the player to actually press Stand.

The engine's ``player_stood`` flag only means "the player's turn is over", so it
is True after a double down too. Settling a won double down to 11 used to
report ``stood=True`` with a total of 11 and award the low-stand achievement.
"""

import unittest
from unittest import mock

from solitaireplus.games.casino import blackjack
from solitaireplus.games.casino.blackjack import BlackjackGame
from solitaireplus.profile import achievements
from tests.support import locate

LOW_STAND = "blackjack_low_stand"


def rigged_game(cards):
    """A game whose draws come out in ``cards`` order, whatever the deck holds."""
    game = BlackjackGame()
    game.draw_card = iter(cards).__next__
    return game


def finish_dealer(game):
    """Run dealer play to the end, jumping the clock past every pause."""
    for step in range(30):
        if game.round_complete:
            return
        with mock.patch.object(blackjack.time, "monotonic", return_value=1e12 + step * 100):
            game.update()
    raise AssertionError("dealer play did not finish")


class Settler:
    """Runs the real settle_blackjack_round and feeds its achievement event to
    the real achievement rules, keeping the achievement state between rounds."""

    def __init__(self):
        self.achievement_state = achievements.make_default_achievement_state()
        self.unlocked = []
        no_op = lambda *args, **kwargs: 0
        self.env = dict(
            current_game_mode="free", career_cash=10_000, blackjack_session_net=0,
            blackjack_round_doubled=False, blackjack_round_all_in=False,
            blackjack_round_start_bet=0, award_game_xp=no_op,
            award_fans_for_cash_win=no_op, lose_fans_for_bad_result=no_op,
            track_night_cash=no_op, process_achievement_event=self._record,
        )
        locate.exec_functions(["settle_blackjack_round"], self.env)

    def _record(self, event_name, **data):
        self.achievement_state, newly = achievements.record_event(
            self.achievement_state, event_name, **data
        )
        self.unlocked += [definition["id"] for definition in newly]

    def settle(self, game, bet, doubled=False):
        self.env.update(blackjack_game=game, blackjack_round_start_bet=bet,
                        blackjack_round_doubled=doubled)
        self.env["settle_blackjack_round"]()

    @property
    def stats(self):
        return self.achievement_state["stats"]


def double_to_eleven_and_win(bet=10):
    # Player 5+3 doubles into a 3 (11); dealer 10+6 hits a 10 and busts.
    game = rigged_game([("5", "S"), ("3", "H"), ("10", "H"), ("6", "D"),
                        ("3", "D"), ("10", "C")])
    game.start_round(bet)
    assert game.double_down()
    finish_dealer(game)
    return game


class LowStandAchievementTests(unittest.TestCase):

    def test_doubling_down_to_eleven_does_not_award_low_stand(self):
        settler = Settler()
        game = double_to_eleven_and_win()
        self.assertEqual(game.player_value(), 11)
        self.assertEqual(game.result, "player")

        settler.settle(game, 10, doubled=True)

        # The win itself counts (so the low total really reached the rules) ...
        self.assertEqual(settler.stats.get("blackjack_wins"), 1)
        self.assertTrue(settler.stats.get("blackjack_double_win"))
        # ... but nobody pressed Stand.
        self.assertNotIn(LOW_STAND, settler.stats)
        self.assertNotIn(LOW_STAND, settler.unlocked)

    def test_standing_on_a_low_total_and_winning_awards_low_stand(self):
        settler = Settler()
        # Player 5+6 = 11 stands; dealer 10+6 hits a 10 and busts.
        game = rigged_game([("5", "S"), ("6", "H"), ("10", "H"), ("6", "D"),
                            ("10", "C")])
        game.start_round(10)
        self.assertTrue(game.stand())
        finish_dealer(game)
        self.assertEqual(game.result, "player")

        settler.settle(game, 10)

        self.assertTrue(settler.stats.get(LOW_STAND))
        self.assertIn(LOW_STAND, settler.unlocked)

    def test_a_stand_in_an_earlier_round_does_not_carry_into_the_next(self):
        settler = Settler()
        # Round 1: stand on 20 and win (too high for the achievement).
        first = rigged_game([("10", "S"), ("K", "H"), ("10", "H"), ("6", "D"),
                             ("10", "C"), ("5", "S"), ("3", "H"), ("10", "D"),
                             ("6", "C"), ("3", "D"), ("Q", "C")])
        first.start_round(10)
        self.assertTrue(first.stand())
        finish_dealer(first)
        self.assertEqual(first.result, "player")
        settler.settle(first, 10)
        self.assertNotIn(LOW_STAND, settler.stats)

        # Round 2 on the same table object: double down to 11 and win.
        first.start_round(10)
        self.assertTrue(first.double_down())
        finish_dealer(first)
        self.assertEqual(first.player_value(), 11)
        self.assertEqual(first.result, "player")
        settler.settle(first, 10, doubled=True)

        self.assertEqual(settler.stats.get("blackjack_wins"), 2)
        self.assertNotIn(LOW_STAND, settler.stats)
        self.assertNotIn(LOW_STAND, settler.unlocked)


if __name__ == "__main__":
    unittest.main()
