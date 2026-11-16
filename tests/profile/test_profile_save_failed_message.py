"""B12 (Profile screen): a failed save must not be reported as saved.

save_profile() returns False when the save file is locked: the progress goes to a recovery copy
instead. The Profile screen's Save button used to ignore that and show 'Profile saved to slot N.'
"""
import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

RECOVERY_MESSAGE = 'Saved to a recovery file (the save is in use). Close other copies of the game.'

STATE_NAMES = (
    'game_mouse_pos', 'gender_dropdown_open', 'favorite_suit_dropdown_open',
    'profile_name_active', 'profile_country_active', 'profile_age_active',
    'profile_hometown_active', 'profile_bio_active',
    'profile_name_text', 'profile_country_text', 'profile_age_text',
    'player_name', 'profile_creation_mode', 'pending_profile_slot',
    'current_profile_slot', 'guest_mode', 'profile_message',
    'direction', 'age_value',
)


class ProfileSaveFailedMessageTests(unittest.TestCase):
    def setUp(self):
        from solitaireplus.app import state
        from solitaireplus.profile import profile_editor
        self.state = state
        self.editor = profile_editor

        missing = object()
        saved = {name: getattr(state, name, missing) for name in STATE_NAMES}

        def restore():
            for name, value in saved.items():
                if value is missing:
                    if hasattr(state, name):
                        delattr(state, name)
                else:
                    setattr(state, name, value)

        self.addCleanup(restore)

        state.game_mouse_pos = profile_editor.profile_save_rect.center
        state.gender_dropdown_open = False
        state.favorite_suit_dropdown_open = False
        state.profile_name_text = 'Tester'
        state.profile_country_text = ''
        state.profile_age_text = ''
        state.profile_message = ''

        self.save_data = MagicMock()
        self.save_data.build_profile_save_data.return_value = {}
        self.profile_select = MagicMock()
        for target, value in (('save_data', self.save_data),
                              ('profile_select', self.profile_select),
                              ('sounds', MagicMock())):
            patcher = patch.object(profile_editor, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def click_save(self, save_result):
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                   pos=self.editor.profile_save_rect.center)
        with patch.object(self.editor, 'save_profile', return_value=save_result) as save_profile:
            self.editor.handle_event(event)
        return save_profile

    def test_failed_save_shows_recovery_message(self):
        self.state.profile_creation_mode = False
        self.state.guest_mode = False
        self.state.current_profile_slot = 2

        save_profile = self.click_save(False)

        save_profile.assert_called_once()
        self.assertEqual(self.state.profile_message, RECOVERY_MESSAGE)

    def test_successful_save_still_reports_the_slot(self):
        self.state.profile_creation_mode = False
        self.state.guest_mode = False
        self.state.current_profile_slot = 2

        self.click_save(True)

        self.assertEqual(self.state.profile_message, 'Profile saved to slot 2.')

    def test_failed_save_while_creating_a_profile_sets_recovery_message(self):
        self.state.profile_creation_mode = True
        self.state.pending_profile_slot = 3
        self.state.current_profile_slot = None
        self.state.guest_mode = False

        self.click_save(False)

        # Creation still finishes (the recovery copy loads like a normal save).
        self.profile_select.finish_profile_selection.assert_called_once()
        self.assertEqual(self.state.current_profile_slot, 3)
        self.assertFalse(self.state.profile_creation_mode)
        self.assertEqual(self.state.profile_message, RECOVERY_MESSAGE)

    def test_successful_create_clears_the_message(self):
        self.state.profile_creation_mode = True
        self.state.pending_profile_slot = 3
        self.state.current_profile_slot = None
        self.state.guest_mode = False
        self.state.profile_message = 'old message'

        self.click_save(True)

        self.profile_select.finish_profile_selection.assert_called_once()
        self.assertEqual(self.state.profile_message, '')

    def click_save_raising(self, error):
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                   pos=self.editor.profile_save_rect.center)
        with patch.object(self.editor, 'save_profile', side_effect=error):
            self.editor.handle_event(event)

    def test_disk_error_while_saving_is_reported_not_raised(self):
        self.state.profile_creation_mode = False
        self.state.guest_mode = False
        self.state.current_profile_slot = 2

        self.click_save_raising(OSError(28, 'No space left on device'))

        self.assertEqual(self.state.profile_message, self.editor.SAVE_FAILED_MESSAGE)

    def test_disk_error_while_creating_stays_on_the_profile_screen(self):
        self.state.profile_creation_mode = True
        self.state.pending_profile_slot = 3
        self.state.current_profile_slot = 1
        self.state.guest_mode = True

        self.click_save_raising(PermissionError(13, 'Access is denied'))

        # Nothing was written: still creating, so Save can be pressed again.
        self.profile_select.finish_profile_selection.assert_not_called()
        self.assertTrue(self.state.profile_creation_mode)
        self.assertEqual(self.state.pending_profile_slot, 3)
        self.assertEqual(self.state.current_profile_slot, 1)
        self.assertTrue(self.state.guest_mode)
        self.assertEqual(self.state.profile_message, self.editor.SAVE_FAILED_MESSAGE)


if __name__ == '__main__':
    unittest.main()
