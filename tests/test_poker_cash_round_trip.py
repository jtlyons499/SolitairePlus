"""Career cash and the table stack in every poker variant (B86 review F16).

The real session starters and finishers of all five poker screens run with their career side
effects stubbed (tests/support/poker_screens.py):

* starting a session moves exactly the buy-in from career cash to the table (the stack plus
  the chips the human already put into the first hand), so career cash + table is unchanged;
* finishing (cashing out) after a hand credits exactly the table stack back, once;
* Five-O and Blind Man's Bluff: when the engine cannot start the session, the buy-in goes back
  to career cash and the buy-in is no longer active.
"""
import random
import unittest
from unittest import mock

from solitaireplus.app import state
from solitaireplus.games.poker import (
    blind_mans_bluff_screen,
    five_card_draw_screen,
    five_o_screen,
    holdem_screen,
    seven_card_stud_screen,
)
from solitaireplus.games.poker.blind_mans_bluff import BlindMansBluffGame
from solitaireplus.games.poker.five_card_draw import FiveCardDrawGame
from solitaireplus.games.poker.five_o import FiveOPokerGame
from solitaireplus.games.poker.holdem import TexasHoldemGame
from solitaireplus.games.poker.seven_card_stud import SevenCardStudGame
from tests.support.poker_screens import OPPONENTS, ScreenHarness
from tests.support.poker_variants import ADAPTERS_BY_KEY

BUY_IN = 1000
CAREER_CASH = 5000

# key, screen module, engine class, session starter, session finisher, state prefix
TABLES = (
    ("texas_holdem", holdem_screen, TexasHoldemGame,
     "start_texas_holdem_session", "finish_texas_holdem_session", "texas_holdem"),
    ("five_card_draw", five_card_draw_screen, FiveCardDrawGame,
     "start_five_card_draw_session", "finish_five_card_draw_session", "five_card_draw"),
    ("seven_card_stud", seven_card_stud_screen, SevenCardStudGame,
     "start_seven_card_stud_session", "finish_seven_card_stud_session", "seven_card_stud"),
    ("five_o_poker", five_o_screen, FiveOPokerGame,
     "start_five_o_poker_session", "finish_five_o_poker_session", "five_o_poker"),
    ("blind_mans_bluff", blind_mans_bluff_screen, BlindMansBluffGame,
     "start_blind_mans_bluff_session", "finish_blind_mans_bluff_session", "blind_mans_bluff"),
)
NICHE = ("five_o_poker", "blind_mans_bluff")


def table_chips(key, game):
    """The human's chips at the table: its stack plus what it put into the hand in play."""
    if key in NICHE:
        return game.player_stack + game.hand_contributions[0]
    return game.player_stack + game.player_hand_contribution


class CashRoundTripTests(unittest.TestCase):
    def open_table(self, key, module, game_class):
        screen = ScreenHarness(self, seed=f"cash-{key}")
        game = screen.stub(module, game_class())
        state.career_cash = CAREER_CASH
        return screen, game

    def start(self, key, module, starter):
        if key in NICHE:
            return getattr(module, starter)(BUY_IN)
        return getattr(module, starter)(BUY_IN, OPPONENTS)

    def test_start_moves_exactly_the_buy_in_and_finish_credits_exactly_the_stack(self):
        for key, module, game_class, starter, finisher, prefix in TABLES:
            with self.subTest(key):
                screen, game = self.open_table(key, module, game_class)
                self.assertTrue(self.start(key, module, starter))
                self.assertTrue(getattr(state, f"{prefix}_buy_in_active"))
                self.assertEqual(getattr(state, f"{prefix}_starting_stack"), BUY_IN)
                self.assertEqual(state.career_cash, CAREER_CASH - BUY_IN)
                self.assertEqual(table_chips(key, game), BUY_IN)
                self.assertEqual(state.career_cash + table_chips(key, game), CAREER_CASH)

                # Play the first hand to its end, then cash out.
                adapter = ADAPTERS_BY_KEY[key]
                if key == "blind_mans_bluff":
                    game.npc_delay_seconds = 0
                adapter.play_hand(game, random.Random(f"cash-{key}"))
                self.assertTrue(game.hand_complete)
                stack = game.player_stack
                cash = state.career_cash
                getattr(module, finisher)()
                self.assertEqual(state.career_cash, cash + stack)
                self.assertFalse(getattr(state, f"{prefix}_buy_in_active"))
                self.assertEqual(getattr(state, f"{prefix}_session_net"), stack - BUY_IN)
                # A second cash-out credits nothing more.
                getattr(module, finisher)()
                self.assertEqual(state.career_cash, cash + stack)

    def test_finish_right_after_the_buy_in_returns_the_untouched_buy_in(self):
        # Five-O and Blind Man's Bluff deal the first hand inside start_session, so only the
        # Hold'em family can be checked before anything is posted.
        for key, module, game_class, starter, finisher, prefix in TABLES[:3]:
            with self.subTest(key):
                screen, game = self.open_table(key, module, game_class)
                with mock.patch.object(game_class, "start_hand", return_value=False):
                    self.assertTrue(self.start(key, module, starter))
                self.assertEqual(game.player_stack, BUY_IN)
                getattr(module, finisher)()
                self.assertEqual(state.career_cash, CAREER_CASH)
                self.assertFalse(getattr(state, f"{prefix}_buy_in_active"))

    def test_a_failed_niche_start_refunds_the_buy_in(self):
        for key, module, game_class, starter, finisher, prefix in TABLES:
            if key not in NICHE:
                continue
            with self.subTest(key):
                screen, game = self.open_table(key, module, game_class)
                setattr(state, f"{prefix}_buy_in_active", False)
                with mock.patch.object(game, "start_session", return_value=False):
                    self.assertFalse(self.start(key, module, starter))
                self.assertEqual(state.career_cash, CAREER_CASH)
                self.assertFalse(getattr(state, f"{prefix}_buy_in_active"))


if __name__ == "__main__":
    unittest.main()
