"""B56: Enter in King Pong must not forfeit a match that is still being played."""
import unittest
from types import SimpleNamespace
from unittest import mock

import pygame

from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.games.arcade import machine_screens
from solitaireplus.games.arcade.king_pong import KingPongGame


def _no_op(*args, **kwargs):
    return None


def _key_event(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode="", scancode=0)


class KingPongEnterKeyTests(unittest.TestCase):
    def setUp(self):
        saved = {name: value for name, value in vars(state).items() if not name.startswith("__")}

        def restore_state():
            for name in [name for name in vars(state) if not name.startswith("__") and name not in saved]:
                delattr(state, name)
            for name, value in saved.items():
                setattr(state, name, value)

        self.addCleanup(restore_state)
        state.arcade_state = {}
        self.game = KingPongGame()
        self.registered = []

        def register(arcade_state, won, tickets):
            self.registered.append((won, tickets))
            return arcade_state

        stubs = {
            "king_pong_game": self.game,
            "night": SimpleNamespace(record_career_event_result=_no_op),
            "career_saving": SimpleNamespace(auto_save_career=_no_op),
            "sounds": SimpleNamespace(audio=SimpleNamespace(play_sound=_no_op)),
            "register_king_pong_result": register,
            "start_king_pong_session": mock.Mock(return_value=True),
        }
        for name, value in stubs.items():
            patcher = mock.patch.object(machine_screens, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

        self.game.start_match({"name": "Arcade Rival"}, difficulty_id="medium", target_score=5)
        state.current_state = state_names.STATE_KING_PONG

    def finish_match_by_scoring(self):
        while not self.game.finished:
            self.game._score_point(True)

    def test_enter_mid_match_does_nothing(self):
        for key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            with self.subTest(key=pygame.key.name(key)):
                machine_screens.loop_event_king_pong(_key_event(key))

                self.assertFalse(self.game.finished)
                self.assertFalse(self.game.forfeited)
                self.assertEqual(self.game.opponent_score, 0)
                self.assertEqual(state.current_state, state_names.STATE_KING_PONG)
                self.assertEqual(self.registered, [])

    def test_enter_after_match_end_returns_to_arcade_night(self):
        for key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            with self.subTest(key=pygame.key.name(key)):
                self.game.start_match({"name": "Arcade Rival"}, difficulty_id="medium", target_score=5)
                state.current_state = state_names.STATE_KING_PONG
                self.registered.clear()
                self.finish_match_by_scoring()

                machine_screens.loop_event_king_pong(_key_event(key))

                self.assertFalse(self.game.forfeited)
                self.assertTrue(self.game.player_won)
                self.assertTrue(self.game.reward_claimed)
                self.assertEqual(len(self.registered), 1)
                self.assertTrue(self.registered[0][0])
                self.assertEqual(state.current_state, state_names.STATE_CAREER_EVENT_SELECT)

    def test_escape_mid_match_still_forfeits(self):
        machine_screens.loop_event_king_pong(_key_event(pygame.K_ESCAPE))

        self.assertTrue(self.game.finished)
        self.assertTrue(self.game.forfeited)
        self.assertEqual(self.registered, [(False, 0)])
        self.assertEqual(state.current_state, state_names.STATE_CAREER_EVENT_SELECT)

    def test_space_after_match_end_still_starts_a_rematch(self):
        self.finish_match_by_scoring()

        machine_screens.loop_event_king_pong(_key_event(pygame.K_SPACE))

        machine_screens.start_king_pong_session.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
