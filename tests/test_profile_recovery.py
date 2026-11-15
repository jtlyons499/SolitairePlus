"""Damaged saves, backups, and saves from newer versions (profile.py)."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from solitaireplus.profile import saves as profiles


class ProfileRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.patch = patch.object(profiles, "SAVE_FOLDER", self.folder.name)
        self.patch.start()
        self.path = Path(profiles.get_profile_path(1))

    def tearDown(self):
        self.patch.stop()
        self.folder.cleanup()

    def save(self, cash):
        data = profiles.make_default_profile()
        data["career"]["cash"] = cash
        self.assertTrue(profiles.save_profile(data, 1))

    def test_each_save_keeps_the_previous_good_one_as_bak(self):
        self.save(10)
        self.save(20)
        self.assertEqual(json.loads(Path(profiles.backup_path(1)).read_text())["career"]["cash"], 10)

    def test_damaged_save_falls_back_to_the_backup_instead_of_crashing(self):
        self.save(10)
        self.save(20)
        self.path.write_text('{"career": {"cash": 2', encoding="utf-8")   # cut off mid-write
        self.assertEqual(profiles.load_profile(1)["career"]["cash"], 10)
        damaged = list(self.path.parent.glob("profile_1.json.damaged-*.json"))
        self.assertEqual(len(damaged), 1)                                   # kept for repair, never deleted
        profiles.load_profile(1)
        profiles.load_profile(1)                                            # the profile screen reloads every frame
        self.assertEqual(len(list(self.path.parent.glob("*.damaged-*"))), 1)

    def test_a_damaged_save_never_replaces_a_good_backup(self):
        self.save(10)
        self.save(20)
        self.path.write_text("garbage", encoding="utf-8")
        profiles.keep_backup(str(self.path))
        self.assertEqual(json.loads(Path(profiles.backup_path(1)).read_text())["career"]["cash"], 10)

    def test_no_readable_copy_is_reported_not_treated_as_empty(self):
        self.path.write_text("garbage", encoding="utf-8")
        with self.assertRaises(profiles.ProfileDamaged) as caught:
            profiles.load_profile(1)
        self.assertIn("damaged", str(caught.exception))
        self.assertTrue(profiles.profile_exists(1))   # the slot is not "empty", so it is not overwritten

    def test_save_from_a_newer_version_is_refused(self):
        data = profiles.make_default_profile()
        data["profile_version"] = profiles.PROFILE_VERSION + 1
        self.path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(profiles.ProfileTooNew):
            profiles.load_profile(1)

    def test_migrations_run_in_order_from_old_versions(self):
        calls = []
        steps = {8: lambda d: calls.append(8) or d, 9: lambda d: calls.append(9) or dict(d, upgraded=True)}
        with patch.object(profiles, "MIGRATIONS", steps):
            result = profiles.migrate({"profile_version": 8})
        self.assertEqual(calls, [8, 9])
        self.assertTrue(result["upgraded"])
        self.assertEqual(result["profile_version"], profiles.PROFILE_VERSION)

    def test_delete_removes_the_backup_too(self):
        self.save(10)
        self.save(20)
        profiles.delete_profile(1)
        self.assertFalse(os.path.exists(profiles.backup_path(1)))
        self.assertIsNone(profiles.load_profile(1))


if __name__ == "__main__":
    unittest.main()
