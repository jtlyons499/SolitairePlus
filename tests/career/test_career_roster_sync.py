"""B18: the Career NPC roster is re-synced only after the roster or the date changed.

sync_career_npc_runtime_state() rebuilds every live NPC from its template (deep copies, a seeded RNG
per NPC). The Career hub used to run it three times per frame (ensure_career_leaderboard() plus two
get_career_leaderboard() calls), and the leaderboards screen and rank lookups did the same. Now a
dirty flag (state.career_roster_dirty) is set when the roster or the career date changes, and the
per-frame callers sync only when it is set.

Starts the game's modules headless (saves in a temporary folder), then counts the expensive roster
rebuild (sync_npc_runtime_state, as leaderboard_engine calls it) while drawing the real hub.
"""
import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame  # noqa: E402,F401  (initialised by the test runner like the real game)


class CareerRosterSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = tempfile.TemporaryDirectory()
        cls.old_local_app_data = os.environ.get('LOCALAPPDATA')
        os.environ['LOCALAPPDATA'] = cls.data.name
        from solitaireplus.app import runtime_support
        saves = os.path.join(cls.data.name, 'saves')
        os.makedirs(saves, exist_ok=True)
        runtime_support.save_directory = lambda: saves
        from solitaireplus.app import startup  # noqa: F401 (the game's start-up)
        from solitaireplus.app import state
        from solitaireplus.career import calendar, hub_screen, leaderboard_engine, leaderboards_screen, news_screen
        from solitaireplus.npc import manager as npc_manager
        cls.state, cls.calendar = state, calendar
        cls.hub_screen, cls.leaderboard_engine = hub_screen, leaderboard_engine
        cls.leaderboards_screen, cls.npc_manager = leaderboards_screen, npc_manager
        state.game_mouse_pos = None
        state.menu_mouse_pos = None
        # What clicking Career on the mode-select screen does.
        state.current_game_mode = 'career'
        calendar.ensure_career_schedule()
        leaderboard_engine.ensure_career_leaderboard()
        news_screen.ensure_career_news()

    @classmethod
    def tearDownClass(cls):
        if cls.old_local_app_data is None:
            os.environ.pop('LOCALAPPDATA', None)
        else:
            os.environ['LOCALAPPDATA'] = cls.old_local_app_data
        cls.data.cleanup()

    def setUp(self):
        self.state.current_game_mode = 'career'
        # Mid-month, so advancing one day does not start a new month.
        self.state.career_day_of_month = 3
        self.state.career_weekday_index = 2

    def count_syncs(self, action):
        calls = []
        real = self.npc_manager.sync_npc_runtime_state

        def counting(*args, **kwargs):
            calls.append(args)
            return real(*args, **kwargs)

        with patch.object(self.leaderboard_engine, 'sync_npc_runtime_state', counting):
            action()
        return len(calls)

    def draw_hub(self, frames=10):
        for _ in range(frames):
            self.hub_screen.draw_career_hub()

    def test_drawing_the_hub_ten_frames_syncs_the_roster_at_most_once(self):
        self.assertLessEqual(self.count_syncs(self.draw_hub), 1)
        self.assertEqual(self.count_syncs(self.draw_hub), 0, 'an unchanged roster was synced again')

    def test_leaderboards_screen_and_rank_lookups_do_not_resync_an_unchanged_roster(self):
        self.draw_hub(1)

        def frames():
            for _ in range(10):
                self.leaderboards_screen.draw_career_leaderboards()
                self.leaderboard_engine.get_player_leaderboard_rank()
                self.leaderboard_engine.get_career_leaderboard('solitaire')

        self.assertEqual(self.count_syncs(frames), 0)

    def test_advancing_a_day_syncs_the_roster_again_once(self):
        self.draw_hub(1)
        day = self.state.career_day

        def advance_then_draw():
            self.calendar.advance_career_day(completed=False, save_after=False)
            self.draw_hub()

        self.assertEqual(self.count_syncs(advance_then_draw), 1)
        self.assertEqual(self.state.career_day, day + 1)
        self.assertEqual(self.count_syncs(self.draw_hub), 0)

    def test_a_new_month_reaches_the_live_roster_once(self):
        self.draw_hub(1)
        month = self.state.career_month

        def new_month_then_draw():
            from solitaireplus.debug import actions as debug_actions   # the F10 actions (Phase 10)
            debug_actions.debug_start_next_career_month(save=False)
            self.draw_hub()

        self.assertEqual(self.count_syncs(new_month_then_draw), 1)
        self.assertEqual(self.state.career_month, month % 12 + 1)
        self.assertFalse(self.state.career_roster_dirty)

    def test_a_changed_roster_or_date_marks_the_roster_dirty_until_the_next_sync(self):
        self.draw_hub(1)
        self.assertFalse(self.state.career_roster_dirty)
        self.calendar.advance_career_day(completed=False, save_after=False)
        self.assertTrue(self.state.career_roster_dirty)
        self.leaderboard_engine.ensure_career_leaderboard()
        self.assertFalse(self.state.career_roster_dirty)
        # A dirty roster always reaches the live NPC list on the next frame.
        self.state.career_roster_dirty = True
        self.assertEqual(self.count_syncs(lambda: self.draw_hub(1)), 1)


if __name__ == '__main__':
    unittest.main()
