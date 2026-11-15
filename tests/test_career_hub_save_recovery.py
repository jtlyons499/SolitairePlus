"""B12 (Career hub): a save that went to a recovery file must not be reported as saved.

save_profile() returns False when the save file is locked: the progress goes to a recovery copy
instead. auto_save_career() showed a 'Save file locked' toast for that, but the hub's Save / Switch
Profile (save_career_from_hub) then always replaced it with 'Profile saved to slot N.'.
"""
import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from solitaireplus.app import state
from solitaireplus.career import career_saving
from solitaireplus.career.hub_controls import CareerHubControls
from solitaireplus.profile import profile_editor

LOCKED_TOAST = "Save file locked: progress kept in a recovery save. Close any other game instance."


class CareerHubSaveRecoveryTests(unittest.TestCase):
    def setUp(self):
        pygame.init()   # CareerHubControls builds a font (also when run on its own)
        missing = object()
        saved = {name: getattr(state, name, missing) for name in ("guest_mode", "current_profile_slot")}

        def restore():
            for name, value in saved.items():
                if value is missing:
                    if hasattr(state, name):
                        delattr(state, name)
                else:
                    setattr(state, name, value)

        self.addCleanup(restore)
        state.guest_mode = False
        state.current_profile_slot = 2

        self.controls = CareerHubControls()
        self.save_data = MagicMock()
        self.save_data.build_profile_save_data.return_value = {}
        for target, value in (("legacy", MagicMock(career_hub_controls=self.controls)),
                              ("save_data", self.save_data)):
            patcher = patch.object(career_saving, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def save_from_hub(self, saved):
        with patch.object(career_saving, "save_profile", return_value=saved) as save_profile:
            result = career_saving.save_career_from_hub()
        save_profile.assert_called_once_with({}, 2)
        return result

    def test_recovery_save_is_not_reported_as_saved(self):
        self.save_from_hub(False)
        self.assertEqual(self.controls.message, profile_editor.SAVE_IN_USE_MESSAGE)
        self.assertNotIn("Profile saved", self.controls.message)

    def test_normal_save_still_reports_the_slot(self):
        self.assertTrue(self.save_from_hub(True))
        self.assertEqual(self.controls.message, "Profile saved to slot 2.")

    def test_recovery_save_still_lets_the_switch_go_on(self):
        # The progress is kept (in the recovery file), so Switch Profile still proceeds as before.
        self.assertTrue(self.save_from_hub(False))

    def test_auto_save_career_reports_whether_the_normal_save_worked(self):
        with patch.object(career_saving, "save_profile", return_value=True):
            self.assertIs(career_saving.auto_save_career(), True)
        self.assertEqual(self.controls.message, "")
        with patch.object(career_saving, "save_profile", return_value=False):
            self.assertIs(career_saving.auto_save_career(), False)
        # Other callers still get the existing locked-save toast.
        self.assertEqual(self.controls.message, LOCKED_TOAST)

    def test_auto_save_career_still_raises_os_errors(self):
        with patch.object(career_saving, "save_profile", side_effect=OSError("disk")):
            with self.assertRaises(OSError):
                career_saving.auto_save_career()
            self.assertFalse(career_saving.save_career_from_hub())
        self.assertEqual(self.controls.message, "Could not save. Check the saves folder and try again.")

    def test_guest_save_is_unchanged(self):
        state.guest_mode = True
        with patch.object(career_saving, "save_profile") as save_profile:
            self.assertTrue(career_saving.save_career_from_hub())
            self.assertFalse(career_saving.auto_save_career())
        save_profile.assert_not_called()
        self.assertEqual(self.controls.message, "Guest progress is temporary. Choose a profile to save.")


if __name__ == "__main__":
    unittest.main()
