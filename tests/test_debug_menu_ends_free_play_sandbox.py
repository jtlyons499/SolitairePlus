"""F10 debug career jumps end a running Free Play sandbox first (B21).

A Free Play cash game swaps the real Career cash for a $5,000 sandbox stake and keeps the real
values in state.free_play_snapshot. The debug menu's "Career Hub" action jumped straight to the
hub without finish_free_play_sandbox(), so the next hub save wrote the sandbox $5,000 into the
real profile. Every debug jump to a career screen must restore the real Career state first.

The same holds for every debug launch of a game or night (arcade machines, casino and poker
games, the Solitaire challenges...): their exits reach the career event select, whose Return
saves the Career. Only the menu's own controls (Close, Add Cash...) keep the sandbox running.
"""
import os
import tempfile
import unittest
from unittest.mock import patch

import pygame

REAL_CASH = 777


class DebugMenuEndsFreePlaySandboxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Keep every save away from the real saves folder (same setup as test_frame_font_sites).
        cls.data = tempfile.TemporaryDirectory()
        cls.old_local_app_data = os.environ.get("LOCALAPPDATA")
        os.environ["LOCALAPPDATA"] = cls.data.name
        from solitaireplus.app import runtime_support
        saves = os.path.join(cls.data.name, "saves")
        os.makedirs(saves, exist_ok=True)
        runtime_support.save_directory = lambda: saves
        from solitaireplus import legacy
        from solitaireplus.app import state, state_names
        from solitaireplus.career import calendar, career_saving, leaderboard_engine
        from solitaireplus.menus import free_play_select
        from solitaireplus.career.events import event_select_screen
        from solitaireplus.debug import menu, game_mode
        cls.legacy, cls.state, cls.state_names = legacy, state, state_names
        cls.career_saving, cls.free_play_select = career_saving, free_play_select
        cls.event_select, cls.menu, cls.game_mode = event_select_screen, menu, game_mode
        state.game_mouse_pos = None
        state.menu_mouse_pos = None
        state.current_game_mode = "career"
        calendar.ensure_career_schedule()
        leaderboard_engine.ensure_career_leaderboard()

    @classmethod
    def tearDownClass(cls):
        if cls.old_local_app_data is None:
            os.environ.pop("LOCALAPPDATA", None)
        else:
            os.environ["LOCALAPPDATA"] = cls.old_local_app_data
        cls.data.cleanup()

    def setUp(self):
        state = self.state
        self.saved_cash = []

        def fake_save_profile(profile_data, slot=1):
            self.saved_cash.append(profile_data["career"]["cash"])
            return True

        for target, name, value in ((self.career_saving, "save_profile", fake_save_profile),
                                    (self.legacy.sounds.audio, "play_sound", lambda *a, **k: None)):
            patcher = patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        for name, value in (("guest_mode", False), ("current_profile_slot", 1)):
            patcher = patch.object(state, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.reset_to_career()

    def reset_to_career(self):
        state = self.state
        if state.free_play_snapshot is not None:
            self.legacy.finish_free_play_sandbox()
        state.free_play_snapshot = None
        state.career_event_entry = None
        state.career_cash = REAL_CASH
        state.current_game_mode = "career"
        state.debug_saved_game_mode = None
        state.current_state = self.state_names.STATE_MODE_SELECT
        self.legacy.dead_mans_hand_game.release_mouse()
        self.saved_cash.clear()

    def start_free_play_cash_game(self):
        self.assertTrue(self.free_play_select.start_free_play_game("roulette"))
        self.assertEqual(self.state.current_game_mode, "free")
        self.assertEqual(self.state.career_cash, self.free_play_select.FREE_PLAY_STARTING_CASH)

    def choose_debug_action(self, action, from_hotkey=True):
        """Click a debug menu button: opened with F10 first, or (from_hotkey=False) on the
        debug menu the game is already showing (after Back or a failed launch)."""
        state = self.state
        if from_hotkey:
            state.debug_previous_state = state.current_state   # what the F10 hotkey does
            state.current_state = self.state_names.STATE_DEBUG_MENU
        self.assertEqual(state.current_state, self.state_names.STATE_DEBUG_MENU)
        state.game_mouse_pos = (10, 10)
        with patch.object(self.legacy, "get_debug_action", lambda pos: action):
            self.legacy.loop_event_debug_menu(
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=state.game_mouse_pos))

    def choose_poker_select_back(self):
        state = self.state
        self.assertEqual(state.current_state, self.state_names.STATE_DEBUG_POKER_NPC_SELECT)
        state.game_mouse_pos = (10, 10)
        with patch.object(self.legacy, "get_debug_poker_select_action",
                          lambda pos, can_start=True: (self.legacy.DEBUG_POKER_ACTION_BACK, None)):
            self.legacy.loop_event_debug_poker_npc_select(
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=state.game_mouse_pos))

    def click_event_select_return(self):
        """The career event select's Return button (stores the night, saves, goes to the hub)."""
        state = self.state
        state.current_state = self.state_names.STATE_CAREER_EVENT_SELECT   # the debug game ended
        state.menu_mouse_pos = self.event_select.career_event_return_rect.center
        with patch.object(self.event_select, "career_event_card_rects", []):
            self.event_select.handle_event(
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=state.menu_mouse_pos))
        self.assertEqual(state.current_state, self.state_names.STATE_CAREER_HUB)

    def launch_actions(self):
        """Every debug menu button that opens a game, night or career screen."""
        menu = self.menu
        actions = [action for action, _label in menu.CAREER_ENTRIES + menu.CHALLENGE_ENTRIES]
        for _category, _toggle, _label, entries in menu.MINIGAME_CATEGORIES:
            actions.extend(action for action, _label in entries)
        return actions

    def assert_sandbox_ended(self):
        """No sandbox and no Free Play mode left; Career saves write the real cash (a launched
        session may have taken its buy-in out of it)."""
        state = self.state
        self.assertIsNone(state.free_play_snapshot)
        self.assertNotEqual(state.current_game_mode, "free")
        self.assertNotEqual(state.debug_saved_game_mode, "free")
        self.career_saving.auto_save_career()
        self.assertTrue(self.saved_cash)
        for cash in self.saved_cash:
            self.assertLessEqual(cash, REAL_CASH, "a Career save wrote the Free Play sandbox cash")

    def assert_real_career_kept(self):
        self.career_saving.auto_save_career()   # what the hub's Save button and hub actions do
        self.assertTrue(self.saved_cash)
        self.assertEqual(self.saved_cash, [REAL_CASH] * len(self.saved_cash))
        self.assertEqual(self.state.career_cash, REAL_CASH)
        self.assertIsNone(self.state.free_play_snapshot)

    def test_debug_career_hub_during_free_play_keeps_the_saved_career_cash(self):
        self.start_free_play_cash_game()
        self.choose_debug_action(self.legacy.ACTION_CAREER_HUB)
        self.assertEqual(self.state.current_state, self.state_names.STATE_CAREER_HUB)
        self.assertEqual(self.state.current_game_mode, "career")
        self.assert_real_career_kept()

    def test_debug_career_hub_after_a_debug_game_switched_the_sandbox_mode(self):
        # F10 -> a debug game sets current_game_mode to "debug" but the sandbox is still running.
        self.start_free_play_cash_game()
        self.state.current_game_mode = "debug"
        self.choose_debug_action(self.legacy.ACTION_CAREER_HUB)
        self.assertEqual(self.state.current_state, self.state_names.STATE_CAREER_HUB)
        self.assert_real_career_kept()

    def test_every_debug_career_jump_ends_the_sandbox(self):
        legacy = self.legacy
        for action in (legacy.ACTION_CASUAL_CARDS, legacy.ACTION_POKER_NIGHT, legacy.ACTION_CASINO_NIGHT,
                       legacy.ACTION_ARCADE_NIGHT, legacy.ACTION_HEAD_TO_HEAD,
                       legacy.ACTION_ADVANCE_CAREER_DAY, legacy.ACTION_NEW_CAREER_MONTH,
                       legacy.ACTION_ADD_PROSPECT, legacy.ACTION_ADD_PRODIGY, legacy.ACTION_CAREER_YEAR):
            with self.subTest(action=action):
                self.reset_to_career()
                self.start_free_play_cash_game()
                self.choose_debug_action(action)
                self.assertNotEqual(self.state.current_state, self.state_names.STATE_DEBUG_MENU)
                self.assert_real_career_kept()

    def test_debug_career_hub_outside_free_play_is_unchanged(self):
        entry = {"activity_type": "casino_night", "title": "Casino Night"}
        self.state.career_event_entry = entry
        self.choose_debug_action(self.legacy.ACTION_CAREER_HUB)
        self.assertEqual(self.state.current_state, self.state_names.STATE_CAREER_HUB)
        self.assertEqual(self.state.current_game_mode, "career")
        self.assertIs(self.state.career_event_entry, entry)
        self.assertEqual(self.state.career_cash, REAL_CASH)

    def test_close_and_add_cash_keep_the_sandbox_running(self):
        self.start_free_play_cash_game()
        stake = self.free_play_select.FREE_PLAY_STARTING_CASH
        self.choose_debug_action(self.legacy.ACTION_ADD_CASH)
        self.assertEqual(self.state.career_cash, stake + 5000)
        self.assertIsNotNone(self.state.free_play_snapshot)
        self.state.current_state = self.state.debug_previous_state
        self.choose_debug_action(self.legacy.ACTION_CLOSE)
        self.assertEqual(self.state.current_state, self.state_names.STATE_ROULETTE)
        self.assertEqual(self.state.current_game_mode, "free")
        self.assertIsNotNone(self.state.free_play_snapshot)

    def test_every_debug_launch_ends_the_sandbox(self):
        # Games and nights too, not only the career jumps: arcade machines, horse races, Five-O,
        # Blind Man's Bluff, the poker tables and the Solitaire challenges all kept the sandbox.
        launches = self.launch_actions()
        self.assertIn(self.legacy.ACTION_KING_PONG, launches)
        self.assertIn(self.legacy.ACTION_CHALLENGE_DRAW_3, launches)
        for action in launches:
            with self.subTest(action=action):
                self.reset_to_career()
                self.start_free_play_cash_game()
                self.choose_debug_action(action)
                self.assertNotEqual(self.state.current_state, self.state_names.STATE_DEBUG_MENU)
                self.assert_sandbox_ended()

    def test_debug_game_exit_to_the_event_select_return_saves_the_real_cash(self):
        legacy = self.legacy
        for action in (legacy.ACTION_KING_PONG, legacy.ACTION_SUIT_SNAKE, legacy.ACTION_HORSE_RACES,
                       legacy.ACTION_CHALLENGE_NO_UNDO):
            with self.subTest(action=action):
                self.reset_to_career()
                self.start_free_play_cash_game()
                self.choose_debug_action(action)
                if action == legacy.ACTION_HORSE_RACES:
                    legacy.finish_horse_races_session()
                self.click_event_select_return()
                self.assertEqual(self.state.current_game_mode, "career")
                self.assert_real_career_kept()

    def test_ending_the_sandbox_also_ends_free_play_as_the_mode_to_return_to(self):
        # A debug launcher that switched Free Play to "debug" remembers "free" as the mode to go
        # back to. Once the sandbox is over, that must be Career: no Free Play mode on the hub.
        state = self.state
        self.start_free_play_cash_game()
        self.game_mode.enter_debug_game_mode()   # what a debug launcher does
        self.assertEqual(state.debug_saved_game_mode, "free")
        self.choose_debug_action(self.legacy.ACTION_CASUAL_CARDS)   # a debug night: keeps "debug"
        self.assertEqual(state.current_game_mode, "debug")
        self.assertEqual(state.debug_saved_game_mode, "career")
        self.click_event_select_return()
        self.assertEqual(state.current_game_mode, "career")
        self.assert_real_career_kept()

    def test_saved_free_play_mode_without_a_sandbox_becomes_career(self):
        # Free Play select (no game, so no snapshot) -> a debug launcher -> F10 -> Career Hub.
        state = self.state
        state.current_game_mode = "free"
        self.game_mode.enter_debug_game_mode()
        self.assertIsNone(state.free_play_snapshot)
        self.assertTrue(self.legacy.debug_end_free_play_sandbox())
        self.assertEqual(state.current_game_mode, "debug")
        self.assertEqual(state.debug_saved_game_mode, "career")
        self.game_mode.end_debug_game_mode()
        self.assertEqual(state.current_game_mode, "career")

    def test_close_after_a_launch_that_came_back_to_the_menu_leaves_the_ended_free_play_game(self):
        # The sandbox ended when the poker NPC select / Dead Man's Hand opened, so Close must not
        # put the player back into the Free Play roulette game, now without its sandbox.
        legacy, state, names = self.legacy, self.state, self.state_names
        self.start_free_play_cash_game()
        self.choose_debug_action(legacy.ACTION_TEXAS_HOLDEM)
        self.choose_poker_select_back()
        self.choose_debug_action(legacy.ACTION_CLOSE, from_hotkey=False)
        self.assertEqual(state.current_state, names.STATE_FREE_PLAY_SELECT)
        self.assertEqual(state.current_game_mode, "career")
        self.assert_real_career_kept()

        self.reset_to_career()
        self.start_free_play_cash_game()
        self.choose_debug_action(legacy.ACTION_DEAD_MANS_HAND)
        self.assertEqual(state.current_state, names.STATE_DEAD_MANS_HAND)
        legacy.exit_dead_mans_hand()
        self.choose_debug_action(legacy.ACTION_CLOSE, from_hotkey=False)
        self.assertEqual(state.current_state, names.STATE_FREE_PLAY_SELECT)
        self.assert_real_career_kept()

    def test_menu_controls_that_stay_on_the_menu_keep_the_sandbox_running(self):
        legacy = self.legacy
        self.start_free_play_cash_game()
        # (the category is toggled twice: open, then closed again)
        for action in (legacy.ACTION_ZERO_CASH, legacy.ACTION_ADD_RATING, legacy.ACTION_ADD_XP,
                       self.menu.ACTION_MINIGAME_CATEGORY_CASINO, self.menu.ACTION_MINIGAME_CATEGORY_CASINO):
            with self.subTest(action=action):
                self.choose_debug_action(action)
                self.assertEqual(self.state.current_state, self.state_names.STATE_DEBUG_MENU)
                self.assertIsNotNone(self.state.free_play_snapshot)
                self.assertEqual(self.state.current_game_mode, "free")
                self.state.current_state = self.state.debug_previous_state
        self.assertEqual(self.state.career_cash, 0)   # Zero Cash emptied the sandbox, not the Career
        legacy.finish_free_play_sandbox()
        self.assertEqual(self.state.career_cash, REAL_CASH)

    def test_any_save_during_a_sandbox_writes_the_real_career(self):
        # Review of B21: "Unlock Next Achievement" keeps the sandbox running and saves; so can a
        # level-up during Free Play. Saving must write the real career, never the sandbox stake.
        self.start_free_play_cash_game()
        self.choose_debug_action(self.legacy.ACTION_ACHIEVEMENT_TEST)
        self.assertIsNotNone(self.state.free_play_snapshot)          # still playing Free Play
        self.career_saving.auto_save_career()
        self.assertTrue(self.saved_cash)
        self.assertEqual(set(self.saved_cash), {REAL_CASH})
        self.assertEqual(self.state.career_cash, self.free_play_select.FREE_PLAY_STARTING_CASH)


if __name__ == "__main__":
    unittest.main()
