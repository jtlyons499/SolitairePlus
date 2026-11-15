"""B33: Faro gives career results only for money a deal really put at risk.

FaroGame.wagered_total grew on every place_bet() but remove_bet() and clear_bets() never lowered
it, and the Faro screen used ``wagered_total > 0`` to mean "really played". A player could put a
chip down, take it back, deal a turn and cash out to get XP, a logged night result and fan changes
without ever risking a dollar. Only stakes a dealt turn settles (lost to the banker card, won on
the player card, or split on a doublet) count now.
"""
import unittest
from unittest.mock import patch

import pygame

from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.games.casino import faro_screen
from solitaireplus.games.casino.faro import FaroGame
from solitaireplus.games.casino.faro_ui import ACTION_BET_RANK_PREFIX
from solitaireplus.games.casino.faro_ui import ACTION_CLEAR_BETS
from solitaireplus.games.casino.faro_ui import ACTION_DEAL
from solitaireplus.games.casino.faro_ui import ACTION_RETURN


def card(rank, suit="S"):
    return {"rank": rank, "suit": suit}


def stack_deck(game, banker_rank, player_rank):
    """The next deal shows ``banker_rank`` then ``player_rank`` (deal_turn pops from the end)."""
    game.deck = [card("K", "C"), card("K", "D"), card(player_rank, "H"), card(banker_rank, "S")]


class _QuietAudio:
    def play_sound(self, *args, **kwargs):
        pass


class _QuietSounds:
    audio = _QuietAudio()


class _Legacy:
    TRAINING_RATING_REWARDS = {"faro": {"strong_profit": 3, "profit": 2, "break_even": 0, "bad_session": -1}}

    @staticmethod
    def game_namespace():
        return {"current_game_mode": "career"}


class FaroEngineSettledTotalTests(unittest.TestCase):
    def setUp(self):
        self.game = FaroGame()
        self.game.start_session(1000)

    def test_removed_bet_then_deal_settles_nothing(self):
        self.assertTrue(self.game.place_bet("5", 100))
        self.assertTrue(self.game.remove_bet("5", 100))
        stack_deck(self.game, "5", "9")
        self.assertTrue(self.game.deal_turn())
        self.assertEqual(self.game.settled_total, 0)
        self.assertEqual(self.game.cash, 1000)

    def test_cleared_bets_then_deal_settles_nothing(self):
        self.game.place_bet("5", 100)
        self.game.place_bet("9", 50)
        self.assertTrue(self.game.clear_bets())
        stack_deck(self.game, "5", "9")
        self.game.deal_turn()
        self.assertEqual(self.game.settled_total, 0)

    def test_bet_on_a_rank_that_does_not_show_settles_nothing(self):
        self.game.place_bet("Q", 100)
        stack_deck(self.game, "5", "9")
        self.game.deal_turn()
        self.assertEqual(self.game.settled_total, 0)
        self.assertEqual(self.game.get_bet_amount("Q"), 100)

    def test_losing_and_winning_stakes_both_count(self):
        self.game.place_bet("5", 100)   # banker card: loses
        self.game.place_bet("9", 40)    # player card: wins even money
        self.game.place_bet("Q", 10)    # not dealt: stays, not settled
        stack_deck(self.game, "5", "9")
        self.game.deal_turn()
        self.assertEqual(self.game.settled_total, 140)

    def test_doublet_stake_counts(self):
        self.game.place_bet("7", 100)
        stack_deck(self.game, "7", "7")
        self.game.deal_turn()
        self.assertEqual(self.game.last_doublet_loss, 50)
        self.assertEqual(self.game.settled_total, 100)

    def test_new_session_resets_settled_total(self):
        self.game.place_bet("5", 100)
        stack_deck(self.game, "5", "9")
        self.game.deal_turn()
        self.game.start_session(500)
        self.assertEqual(self.game.settled_total, 0)


class FaroScreenRiskFreeRatingTests(unittest.TestCase):
    def setUp(self):
        self.game = FaroGame()
        self.xp = []
        self.results = []
        self.ratings = []
        self.fans = []
        self.night_cash = []
        self.action = None

        class _Leveling:
            @staticmethod
            def award_game_xp(*args, **kwargs):
                self.xp.append((args, kwargs))

        class _Night:
            @staticmethod
            def record_career_event_result(*args, **kwargs):
                self.results.append((args, kwargs))

        class _CareerRewards:
            @staticmethod
            def rate_house_game(game_key, net):
                self.ratings.append((game_key, net))
                return 1

            @staticmethod
            def award_fans_for_cash_win(*args, **kwargs):
                self.fans.append((args, kwargs))

        for target, name, value in (
                (faro_screen, "faro_game", self.game),
                (faro_screen, "get_faro_action", lambda pos, button, game: self.action),
                (faro_screen, "sounds", _QuietSounds()),
                (faro_screen, "legacy", _Legacy()),
                (faro_screen, "leveling", _Leveling()),
                (faro_screen, "night", _Night()),
                (faro_screen, "career_rewards", _CareerRewards()),
                (faro_screen, "track_night_cash",
                 lambda namespace, game_id, net: self.night_cash.append((game_id, net))),
                (state, "game_mouse_pos", (10, 10)),
                (state, "career_cash", 1000),
                (state, "career_event_has_activity", False),
                (state, "current_game_mode", "career"),
                (state, "current_state", state_names.STATE_FARO),
                (state, "faro_chip_value", 100),
                (state, "faro_session_net", 0),
                (state, "free_play_snapshot", None),
        ):
            # create=True: some state values (game_mouse_pos...) only exist once the loop ran.
            patcher = patch.object(target, name, value, create=True)
            patcher.start()
            self.addCleanup(patcher.stop)

        faro_screen.start_faro_session()

    def click(self, action, button=1):
        self.action = action
        faro_screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=button, pos=(10, 10)))

    def assert_no_career_result(self):
        self.assertEqual(self.xp, [])
        self.assertEqual(self.results, [])
        self.assertEqual(self.ratings, [])
        self.assertEqual(self.fans, [])
        self.assertEqual(self.night_cash, [])
        self.assertFalse(state.career_event_has_activity)

    def test_place_remove_deal_cash_out_changes_nothing(self):
        self.click(ACTION_BET_RANK_PREFIX + "5")             # place $100 on fives
        self.click(ACTION_BET_RANK_PREFIX + "5", button=3)   # take it back
        self.assertEqual(self.game.get_total_bet(), 0)
        stack_deck(self.game, "5", "9")
        self.click(ACTION_DEAL)
        self.assertEqual(self.game.turns_dealt, 1)
        self.assert_no_career_result()

        self.click(ACTION_RETURN)
        self.assertEqual(state.career_cash, 1000)
        self.assertEqual(state.current_state, state_names.STATE_CAREER_EVENT_SELECT)
        self.assert_no_career_result()

    def test_place_clear_deal_cash_out_changes_nothing(self):
        self.click(ACTION_BET_RANK_PREFIX + "5")
        self.click(ACTION_BET_RANK_PREFIX + "9")
        self.click(ACTION_CLEAR_BETS)
        stack_deck(self.game, "5", "9")
        self.click(ACTION_DEAL)
        self.click(ACTION_RETURN)
        self.assertEqual(state.career_cash, 1000)
        self.assert_no_career_result()

    def test_settled_losing_bet_still_counts(self):
        self.click(ACTION_BET_RANK_PREFIX + "5")
        stack_deck(self.game, "5", "9")   # the banker card takes the fives
        self.click(ACTION_DEAL)
        self.assertEqual(self.ratings, [("faro", -100)])
        self.assertTrue(state.career_event_has_activity)

        self.click(ACTION_RETURN)
        self.assertEqual(state.career_cash, 900)
        self.assertEqual(len(self.xp), 1)
        self.assertEqual(self.xp[0][1]["won"], False)
        self.assertEqual(len(self.results), 1)
        self.assertEqual(self.results[0][1]["net"], -100)
        self.assertEqual(self.night_cash, [("faro", -100)])

    def test_settled_winning_bet_counts_even_after_it_is_taken_back(self):
        self.click(ACTION_BET_RANK_PREFIX + "9")
        stack_deck(self.game, "5", "9")   # the player card pays the nines
        self.click(ACTION_DEAL)
        self.click(ACTION_BET_RANK_PREFIX + "9", button=3)   # pick the stake back up
        self.click(ACTION_RETURN)
        self.assertEqual(state.career_cash, 1100)
        self.assertEqual(len(self.xp), 1)
        self.assertEqual(self.xp[0][1]["won"], True)
        self.assertEqual(len(self.results), 1)
        self.assertEqual(len(self.fans), 1)
        self.assertTrue(state.career_event_has_activity)


if __name__ == "__main__":
    unittest.main()
