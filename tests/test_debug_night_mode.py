"""B22: debug launchers must not leak the "debug" game mode or advance the real Career day.

The F10 debug menu opens nights and games outside the calendar. Ending such a night (End Night,
then Continue on the summary, or Return to the hub) must leave the Career day alone and put
current_game_mode back to what it was before the launcher switched it to "debug".

Starts the game's modules headless (as the game does, saves in a temporary folder) and drives
the real event-select and summary screens with mouse clicks.
"""
import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame


def click_event(pos):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)


class DebugNightModeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.data = tempfile.TemporaryDirectory()
        cls.old_local_app_data = os.environ.get('LOCALAPPDATA')
        os.environ['LOCALAPPDATA'] = cls.data.name
        from solitaireplus.app import runtime_support
        saves = os.path.join(cls.data.name, 'saves')
        os.makedirs(saves, exist_ok=True)
        runtime_support.save_directory = lambda: saves
        from solitaireplus import legacy
        from solitaireplus.app import state, state_names
        from solitaireplus.career import calendar, career_saving
        from solitaireplus.career.events import event_select_screen, summary_screen
        cls.legacy, cls.state, cls.names = legacy, state, state_names
        cls.calendar, cls.career_saving = calendar, career_saving
        cls.select, cls.summary = event_select_screen, summary_screen

    @classmethod
    def tearDownClass(cls):
        if cls.old_local_app_data is None:
            os.environ.pop('LOCALAPPDATA', None)
        else:
            os.environ['LOCALAPPDATA'] = cls.old_local_app_data
        cls.data.cleanup()

    def setUp(self):
        state = self.state
        self.day_advances = []

        def fake_advance_career_day(completed=True, save_after=True):
            # Stands in for the real calendar step: it moves the day on like the real one.
            self.day_advances.append(completed)
            state.career_day += 1
            state.career_day_of_month += 1

        for patcher in (
                patch.object(self.calendar, 'advance_career_day', fake_advance_career_day),
                patch.object(self.career_saving, 'auto_save_career', lambda: True),
                patch.object(self.select, 'career_event_card_rects', []),
                patch.object(self.legacy.sounds.audio, 'play_sound', lambda *a, **k: None),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

        state.current_game_mode = 'career'
        state.debug_saved_game_mode = None
        state.free_play_snapshot = None
        state.career_day = 7
        state.career_day_of_month = 7
        state.career_cash = 5000
        state.career_event_entry = None
        state.career_event_has_activity = False
        state.current_state = self.names.STATE_CAREER_HUB

    # ------------------------------------------------------------------
    # Driving the real screens
    # ------------------------------------------------------------------

    def end_night(self):
        """Play something, click End Night, then Continue on the summary."""
        state = self.state
        self.assertEqual(state.current_state, self.names.STATE_CAREER_EVENT_SELECT)
        state.career_event_has_activity = True
        state.menu_mouse_pos = self.select.career_event_end_rect.center
        self.select.handle_event(click_event(state.menu_mouse_pos))
        self.assertEqual(state.current_state, self.names.STATE_CAREER_EVENT_SUMMARY)
        state.game_mouse_pos = self.summary.career_event_summary_continue_rect.center
        self.summary.handle_event(click_event(state.game_mouse_pos))
        self.assertEqual(state.current_state, self.names.STATE_CAREER_HUB)

    def return_to_hub(self):
        state = self.state
        self.assertEqual(state.current_state, self.names.STATE_CAREER_EVENT_SELECT)
        state.menu_mouse_pos = self.select.career_event_return_rect.center
        self.select.handle_event(click_event(state.menu_mouse_pos))
        self.assertEqual(state.current_state, self.names.STATE_CAREER_HUB)

    def choose_debug_action(self, action, from_hotkey=True):
        """Click a debug menu button: opened with F10 first, or (from_hotkey=False) on the
        debug menu the game is already showing (after Back or a failed launch)."""
        state = self.state
        if from_hotkey:
            state.debug_previous_state = state.current_state   # what the F10 hotkey does
            state.current_state = self.names.STATE_DEBUG_MENU
        self.assertEqual(state.current_state, self.names.STATE_DEBUG_MENU)
        state.game_mouse_pos = (10, 10)
        with patch.object(self.legacy, 'get_debug_action', lambda pos: action):
            self.legacy.loop_event_debug_menu(click_event(state.game_mouse_pos))

    def choose_poker_select_back(self):
        state, legacy = self.state, self.legacy
        self.assertEqual(state.current_state, self.names.STATE_DEBUG_POKER_NPC_SELECT)
        state.game_mouse_pos = (10, 10)
        with patch.object(legacy, 'get_debug_poker_select_action',
                          lambda pos, can_start=True: (legacy.DEBUG_POKER_ACTION_BACK, None)):
            legacy.loop_event_debug_poker_npc_select(click_event(state.game_mouse_pos))
        self.assertEqual(state.current_state, self.names.STATE_DEBUG_MENU)

    def assert_career_untouched(self, previous_mode='career'):
        self.assertEqual(self.day_advances, [], 'ending a debug night advanced the Career day')
        self.assertEqual(self.state.career_day, 7)
        self.assertEqual(self.state.career_day_of_month, 7)
        self.assertEqual(self.state.current_game_mode, previous_mode)

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_ending_a_debug_night_keeps_the_day_and_the_game_mode(self):
        launchers = ('debug_open_casual_cards', 'debug_open_casino_night',
                     'debug_open_arcade_night', 'debug_open_poker_night')
        for previous_mode in ('career', None):
            for name in launchers:
                with self.subTest(launcher=name, previous_mode=previous_mode):
                    self.setUp()
                    self.state.current_game_mode = previous_mode
                    getattr(self.legacy, name)()
                    self.end_night()
                    self.assert_career_untouched(previous_mode)

    def test_returning_from_a_debug_night_restores_the_game_mode(self):
        self.legacy.debug_open_arcade_night()
        self.assertEqual(self.state.current_game_mode, 'debug')
        self.return_to_hub()
        self.assert_career_untouched()

    def test_debug_horse_races_session_restores_the_game_mode(self):
        legacy, state = self.legacy, self.state
        self.assertTrue(legacy.debug_open_horse_races())
        self.assertEqual(state.current_game_mode, 'debug')
        self.assertTrue(state.career_event_entry.get('debug'))
        legacy.finish_horse_races_session()
        self.end_night()
        self.assert_career_untouched()

    def test_debug_five_o_poker_session_restores_the_game_mode(self):
        legacy, state = self.legacy, self.state
        with patch.object(legacy, 'start_five_o_poker_session', lambda: True):
            self.assertTrue(legacy.debug_open_five_o_poker())
        self.assertEqual(state.current_game_mode, 'debug')
        self.assertTrue(state.career_event_entry.get('debug'))
        state.current_state = self.names.STATE_CAREER_EVENT_SELECT   # the session ended
        self.end_night()
        self.assert_career_untouched()

    def test_failed_debug_launch_does_not_leave_debug_mode(self):
        legacy, state = self.legacy, self.state
        for name, starter in (('debug_open_five_o_poker', 'start_five_o_poker_session'),
                              ('debug_open_blind_mans_bluff', 'start_blind_mans_bluff_session')):
            with self.subTest(launcher=name):
                state.current_game_mode = 'career'
                with patch.object(legacy, starter, lambda: False):
                    self.assertFalse(getattr(legacy, name)())
                self.assertEqual(state.current_game_mode, 'career')

    def test_debug_launcher_inside_a_debug_night_returns_to_the_first_mode(self):
        """Two debug launchers in a row (F10 again during a debug night) still end in the
        mode from before the first one, not in "debug"."""
        legacy, state = self.legacy, self.state
        legacy.debug_open_arcade_night()
        self.assertTrue(legacy.debug_open_horse_races())
        self.assertEqual(state.current_game_mode, 'debug')
        legacy.finish_horse_races_session()
        self.end_night()
        self.assert_career_untouched()

    def test_every_debug_night_launcher_marks_its_night(self):
        legacy, state = self.legacy, self.state
        stubs = {
            'start_crazy_eights_session': lambda: None,
            'start_bango_session': lambda: None,
            'start_faro_session': lambda: True,
            'start_horse_races_session': lambda: True,
            'start_five_o_poker_session': lambda: True,
            'start_blind_mans_bluff_session': lambda: True,
            'get_score_four_opponent_choices': lambda: [],
            'get_random_blackjack_dealer': lambda: None,
        }
        launchers = ('debug_open_casual_cards', 'debug_open_casino_night', 'debug_open_arcade_night',
                     'debug_open_poker_night', 'debug_open_crazy_eights', 'debug_open_bango',
                     'debug_open_score_four_solo', 'debug_open_score_four_competitive',
                     'debug_open_blackjack', 'debug_open_roulette', 'debug_open_horse_races',
                     'debug_open_faro', 'debug_open_five_o_poker', 'debug_open_blind_mans_bluff')
        with patch.multiple(legacy, **stubs), \
                patch.object(legacy.score_four_game, 'start_solo_session', lambda: None), \
                patch.object(legacy.roulette_game, 'reset_round', lambda: None):
            for name in launchers:
                with self.subTest(launcher=name):
                    state.career_event_entry = None
                    getattr(legacy, name)()
                    self.assertIsInstance(state.career_event_entry, dict)
                    self.assertIs(state.career_event_entry.get('debug'), True)

    def test_debug_career_jumps_leave_an_unfinished_debug_night(self):
        """F10 -> Career Hub (or a calendar jump) during a debug night: the real hub must not
        stay in "debug" mode, where real Career nights record nothing."""
        legacy, state = self.legacy, self.state
        for action in (legacy.ACTION_CAREER_HUB, legacy.ACTION_ADVANCE_CAREER_DAY,
                       legacy.ACTION_NEW_CAREER_MONTH, legacy.ACTION_CAREER_YEAR,
                       legacy.ACTION_ADD_PROSPECT):
            with self.subTest(action=action):
                self.setUp()
                legacy.debug_open_arcade_night()
                self.assertEqual(state.current_game_mode, 'debug')
                self.choose_debug_action(action)
                self.assertEqual(state.current_state, self.names.STATE_CAREER_HUB)
                self.assertEqual(state.current_game_mode, 'career')
                self.assertIsNone(state.debug_saved_game_mode)

    def test_debug_career_hub_jump_runs_the_hub_in_career_mode(self):
        # A debug session started before any mode was chosen (main menu: mode None) must not
        # leave the hub in a mode that records no results (review of B22).
        legacy, state = self.legacy, self.state
        state.current_game_mode = None   # nothing chosen yet (game start)
        self.assertTrue(legacy.debug_open_horse_races())
        self.choose_debug_action(legacy.ACTION_CAREER_HUB)
        self.assertEqual(state.current_state, self.names.STATE_CAREER_HUB)
        self.assertEqual(state.current_game_mode, 'career')
        self.assertIsNone(state.debug_saved_game_mode)

    def real_casino_night(self):
        state = self.state
        state.career_event_entry = {'activity_type': 'casino_night', 'title': 'Casino Night', 'game_ids': ['blackjack']}
        state.career_event_has_activity = True
        state.career_event_result_log = [{'game_id': 'blackjack', 'won': True, 'net': 40}]
        state.blackjack_session_net = 40
        state.current_state = self.names.STATE_CAREER_EVENT_SELECT
        return dict(entry=dict(state.career_event_entry), log=list(state.career_event_result_log))

    def test_back_from_the_debug_poker_select_keeps_the_real_night(self):
        # Review of B21/B22: opening the poker table picker replaced the night in progress with
        # a debug Poker Night (debug: True, results cleared); Back + Close lost the real night.
        legacy, state = self.legacy, self.state
        before = self.real_casino_night()
        self.choose_debug_action(legacy.ACTION_TEXAS_HOLDEM)
        self.assertTrue(state.career_event_entry.get('debug'))
        self.choose_poker_select_back()
        self.choose_debug_action(legacy.ACTION_CLOSE, from_hotkey=False)
        self.assertEqual(state.current_state, self.names.STATE_CAREER_EVENT_SELECT)
        self.assertEqual(state.career_event_entry, before['entry'])
        self.assertEqual(state.career_event_result_log, before['log'])
        self.assertTrue(state.career_event_has_activity)
        self.assertEqual(state.blackjack_session_net, 40)
        self.assertEqual(state.current_game_mode, 'career')

    def test_failed_debug_niche_launch_keeps_the_real_night(self):
        legacy, state = self.legacy, self.state
        for launcher in (legacy.debug_open_five_o_poker, legacy.debug_open_blind_mans_bluff):
            with self.subTest(launcher=launcher.__name__):
                self.setUp()
                before = self.real_casino_night()
                state.career_cash = 50   # below the minimum buy-in: the launch fails
                self.assertFalse(launcher())
                self.assertEqual(state.career_event_entry, before['entry'])
                self.assertEqual(state.career_event_result_log, before['log'])
                self.assertEqual(state.blackjack_session_net, 40)
                self.assertEqual(state.current_game_mode, 'career')

    def test_back_from_the_debug_poker_select_leaves_its_debug_mode(self):
        legacy, state = self.legacy, self.state
        for action in (legacy.ACTION_TEXAS_HOLDEM, legacy.ACTION_FIVE_CARD_DRAW,
                       legacy.ACTION_SEVEN_CARD_STUD):
            with self.subTest(action=action):
                self.setUp()
                self.choose_debug_action(action)   # from the Career Hub
                self.assertEqual(state.current_game_mode, 'debug')
                self.choose_poker_select_back()
                self.choose_debug_action(legacy.ACTION_CLOSE, from_hotkey=False)
                self.assertEqual(state.current_state, self.names.STATE_CAREER_HUB)
                self.assertEqual(state.current_game_mode, 'career')
                self.assertIsNone(state.debug_saved_game_mode)

    def test_back_from_the_debug_poker_select_keeps_an_earlier_debug_session(self):
        """F10 during a debug Horse Races session -> Texas Hold'em -> Back -> Close: the player is
        back in the debug session, which must stay in "debug" mode (no real results)."""
        legacy, state = self.legacy, self.state
        self.assertTrue(legacy.debug_open_horse_races())
        self.choose_debug_action(legacy.ACTION_TEXAS_HOLDEM)
        self.choose_poker_select_back()
        self.choose_debug_action(legacy.ACTION_CLOSE, from_hotkey=False)
        self.assertEqual(state.current_state, self.names.STATE_HORSE_RACES)
        self.assertEqual(state.current_game_mode, 'debug')
        legacy.finish_horse_races_session()
        self.end_night()
        self.assert_career_untouched()

    def test_failed_debug_launch_inside_a_debug_session_keeps_its_debug_mode(self):
        """A Five-O / Blind Man's Bluff launch that cannot start (not enough cash) during a debug
        Horse Races session must not drop that session's "debug" mode."""
        legacy, state = self.legacy, self.state
        self.assertTrue(legacy.debug_open_horse_races())
        for action, starter in ((legacy.ACTION_FIVE_O_POKER, 'start_five_o_poker_session'),
                                (legacy.ACTION_BLIND_MANS_BLUFF, 'start_blind_mans_bluff_session')):
            with self.subTest(action=action):
                with patch.object(legacy, starter, lambda: False):
                    self.choose_debug_action(action)   # F10 from the horse races
                self.assertEqual(state.current_state, self.names.STATE_DEBUG_MENU)
                self.assertEqual(state.current_game_mode, 'debug')
                self.assertEqual(state.debug_saved_game_mode, 'career')
                self.choose_debug_action(legacy.ACTION_CLOSE, from_hotkey=False)
                self.assertEqual(state.current_state, self.names.STATE_HORSE_RACES)
        legacy.finish_horse_races_session()
        self.end_night()
        self.assert_career_untouched()

    def test_failed_solitaire_challenge_launch_does_not_leave_debug_mode(self):
        legacy, state = self.legacy, self.state
        with patch.object(legacy.game, 'set_challenge', lambda challenge_id: False):
            self.assertFalse(legacy.debug_open_solitaire_challenge('draw_3'))
        self.assertEqual(state.current_game_mode, 'career')
        self.assertTrue(legacy.debug_open_horse_races())
        with patch.object(legacy.game, 'set_challenge', lambda challenge_id: False):
            self.assertFalse(legacy.debug_open_solitaire_challenge('draw_3'))
        self.assertEqual(state.current_game_mode, 'debug')
        legacy.finish_horse_races_session()
        self.end_night()
        self.assert_career_untouched()


if __name__ == '__main__':
    unittest.main()
