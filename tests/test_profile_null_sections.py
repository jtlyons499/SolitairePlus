"""B63: a damaged or hand-edited save with null (or other non-dict) sections must still load."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from solitaireplus.games.arcade.support import make_default_arcade_state, normalize_arcade_state
from solitaireplus.profile import saves as profiles


class NullSectionLoadTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.patch = patch.object(profiles, "SAVE_FOLDER", self.folder.name)
        self.patch.start()
        self.path = Path(profiles.get_profile_path(1))

    def tearDown(self):
        self.patch.stop()
        self.folder.cleanup()

    def write_save(self, **sections):
        data = profiles.make_default_profile()
        data.update(sections)
        self.path.write_text(json.dumps(data), encoding="utf-8")

    def test_null_progression_and_career_load_without_error(self):
        self.write_save(progression=None, career=None)
        loaded = profiles.load_profile(1)
        self.assertEqual(loaded["progression"], {})
        self.assertIsInstance(loaded["career"], dict)
        self.assertEqual(loaded["career"]["npc_world"], {})
        self.assertIn("ratings", loaded["career"])            # ratings migration still ran
        self.assertEqual(loaded["career"]["arcade"], make_default_arcade_state())

    def test_other_non_dict_sections_become_empty_dicts(self):
        self.write_save(identity="oops", cosmetics=[], achievements=7, settings=None)
        loaded = profiles.load_profile(1)
        for key in ("identity", "cosmetics", "achievements", "settings"):
            self.assertEqual(loaded[key], {}, key)

    def test_good_sections_are_left_alone(self):
        self.write_save()
        loaded = profiles.load_profile(1)
        default = profiles.make_default_profile()
        for key in ("identity", "progression", "cosmetics", "achievements", "settings"):
            self.assertEqual(loaded[key], default[key], key)

    def test_career_arcade_is_normalised_on_load_like_on_save(self):
        raw_arcade = {"tokens": "7", "tickets": -3, "trophies": ["cup", "cup", ""], "stats": None}
        career = profiles.make_default_profile()["career"]
        career["arcade"] = raw_arcade
        self.write_save(career=career)
        loaded = profiles.load_profile(1)
        self.assertEqual(loaded["career"]["arcade"], normalize_arcade_state(raw_arcade))
        self.assertEqual(loaded["career"]["arcade"]["tokens"], 7)
        self.assertEqual(loaded["career"]["arcade"]["trophies"], ["cup"])

    def test_null_arcade_loads_as_default(self):
        career = profiles.make_default_profile()["career"]
        career["arcade"] = None
        self.write_save(career=career)
        self.assertEqual(profiles.load_profile(1)["career"]["arcade"], make_default_arcade_state())


if __name__ == "__main__":
    unittest.main()
