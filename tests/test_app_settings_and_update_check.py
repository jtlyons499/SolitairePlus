"""app_settings.py (saved Options) and update_check.py (the game's side of updating)."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from solitaireplus.app import app_settings
from solitaireplus.app import update_check


class AppSettingsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "app_settings.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_defaults_when_there_is_no_file(self):
        settings = app_settings.AppSettings(self.path)
        self.assertTrue(settings.get("auto_update_check"))
        self.assertIsNone(settings.get("music_volume"))

    def test_changes_are_written_after_a_short_pause_and_read_back(self):
        settings = app_settings.AppSettings(self.path)
        settings.update({"music_volume": 0.3, "fullscreen": True, "window_size": [1600, 900]}, now=100.0)
        self.assertFalse(self.path.exists())            # still dragging the slider
        settings.tick(now=101.0)
        again = app_settings.AppSettings(self.path)
        self.assertEqual(again.get("music_volume"), 0.3)
        self.assertTrue(again.get("fullscreen"))
        self.assertEqual(again.get("window_size"), [1600, 900])

    def test_damaged_or_odd_values_are_ignored(self):
        self.path.write_text(json.dumps({"music_volume": 7, "music_mode": "polka", "window_size": [1, 2],
                                         "auto_update_check": "yes", "fullscreen": False}))
        settings = app_settings.AppSettings(self.path)
        self.assertEqual(settings.get("music_volume"), 1.0)  # clamped
        self.assertIsNone(settings.get("music_mode"))
        self.assertIsNone(settings.get("window_size"))
        self.assertTrue(settings.get("auto_update_check"))
        self.assertFalse(settings.get("fullscreen"))

    def test_unreadable_file_never_crashes(self):
        self.path.write_text("{not json")
        self.assertTrue(app_settings.AppSettings(self.path).get("auto_update_check"))


class UpdateCheckTests(unittest.TestCase):
    def test_everything_is_off_when_running_from_source(self):
        self.assertFalse(update_check.available())
        self.assertFalse(update_check.recover_if_needed())
        checker = update_check.UpdateChecker()
        self.assertFalse(checker.start())
        self.assertIn("installed game", checker.status_text())

    def test_result_of_a_finished_check_is_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = Path(tmp) / "result.json"
            result.write_text(json.dumps({"status": "update_available", "installed": "0.0.7", "latest": "0.0.8"}))
            checker = update_check.UpdateChecker()
            checker.process = mock.Mock(poll=mock.Mock(return_value=0))
            checker.result_file = result
            with mock.patch.object(update_check, "available", return_value=True):
                checker.poll()
                self.assertTrue(checker.update_available)
                self.assertEqual(checker.latest, "0.0.8")
                self.assertEqual(checker.status_text(), "Version 0.0.8 is available.")
            self.assertFalse(result.exists())         # temporary file cleaned up

    def test_a_failed_check_is_reported_not_raised(self):
        checker = update_check.UpdateChecker()
        checker.process = mock.Mock(poll=mock.Mock(return_value=1))
        checker.result_file = Path(tempfile.gettempdir()) / "does-not-exist-solitaire.json"
        checker.poll()
        self.assertFalse(checker.update_available)
        self.assertEqual(checker.result["status"], "error")


if __name__ == "__main__":
    unittest.main()
