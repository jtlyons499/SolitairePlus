"""Profile-select screen: the loaded profile cannot be deleted (B13)."""
import tempfile
import types
import unittest
from unittest.mock import patch

import pygame

from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.profile import profile_select
from solitaireplus.profile import saves


def click(point):
    state.game_mouse_pos = point
    profile_select.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=point))


def slot_body(slot):
    """A point on the slot itself, away from its Delete button."""
    rect = profile_select.profile_slot_rects[slot - 1]
    return (rect.x + 30, rect.centery)


def delete_button(slot):
    return profile_select.profile_delete_rects[slot - 1].center


class ProfileDeleteInUseTests(unittest.TestCase):
    def setUp(self):
        saved_state = dict(vars(state))

        def restore_state():
            for name in list(vars(state)):
                if name not in saved_state:
                    delattr(state, name)
            for name, value in saved_state.items():
                setattr(state, name, value)

        self.addCleanup(restore_state)

        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        folder_patch = patch.object(saves, "SAVE_FOLDER", folder.name)
        folder_patch.start()
        self.addCleanup(folder_patch.stop)
        for slot in (1, 2):
            data = saves.make_default_profile()
            data["identity"]["name"] = f"Player {slot}"
            self.assertTrue(saves.save_profile(data, slot))

        self.applied = []
        stand_ins = {
            "sounds": types.SimpleNamespace(audio=types.SimpleNamespace(play_sound=lambda *args: None)),
            "save_data": types.SimpleNamespace(
                apply_profile_save_data=self.applied.append,
                apply_fresh_profile=lambda: self.applied.append("fresh"),
            ),
            "leveling": types.SimpleNamespace(sync_unlocks_for_current_level=lambda: None),
            "legacy": types.SimpleNamespace(
                career_hub_controls=types.SimpleNamespace(profile_cancel_rect=pygame.Rect(0, 0, 1, 1)),
                reset_career_hub_runtime=lambda: None,
                ensure_career_schedule=lambda: None,
                ensure_career_leaderboard=lambda: None,
                ensure_career_news=lambda: None,
                auto_save_career=lambda: None,
            ),
        }
        for name, stand_in in stand_ins.items():
            module_patch = patch.object(profile_select, name, stand_in)
            module_patch.start()
            self.addCleanup(module_patch.stop)

        # The screen as it is at start-up, straight after the splash screen.
        state.current_state = state_names.STATE_PROFILE_SELECT
        state.profile_select_return_state = state_names.STATE_MENU
        state.profile_return_state = state_names.STATE_MENU
        state.profile_switch_snapshot = None
        state.confirm_delete_profile = False
        state.profile_delete_slot = None
        state.profile_select_notice = ""
        state.profile_message = ""
        state.profile_creation_mode = False
        state.pending_profile_slot = None
        state.guest_mode = False
        state.current_profile_slot = 1   # the start-up default: nothing is loaded yet

    def open_profile_select_again(self):
        """What Profile > Switch Profile does after a profile was picked."""
        state.current_state = state_names.STATE_PROFILE_SELECT
        state.profile_select_return_state = state_names.STATE_MENU
        state.confirm_delete_profile = False
        state.profile_delete_slot = None

    def load_slot(self, slot):
        click(slot_body(slot))
        self.assertEqual(state.current_profile_slot, slot)
        self.assertEqual(state.current_state, state_names.STATE_MENU)

    def try_to_delete(self, slot):
        click(delete_button(slot))
        if state.confirm_delete_profile:
            click(profile_select.confirm_delete_yes_rect.center)

    def test_the_loaded_profile_cannot_be_deleted(self):
        self.load_slot(2)
        self.open_profile_select_again()

        self.try_to_delete(2)

        self.assertTrue(saves.profile_exists(2))
        self.assertFalse(state.confirm_delete_profile)
        self.assertEqual(state.profile_select_notice, profile_select.PROFILE_IN_USE_NOTICE)
        self.assertIn("Load another profile first", state.profile_select_notice)
        # The Delete click explains itself; it does not load the profile and leave the screen.
        self.assertEqual(state.current_state, state_names.STATE_PROFILE_SELECT)

    def test_the_loaded_profile_is_shown_the_message_while_switching_from_career(self):
        self.load_slot(2)
        # What begin_career_profile_switch does.
        state.profile_switch_snapshot = (2, False, {"identity": {"name": "Player 2"}})
        self.open_profile_select_again()
        state.profile_select_return_state = state_names.STATE_CAREER_HUB

        self.try_to_delete(2)

        self.assertTrue(saves.profile_exists(2))
        self.assertEqual(state.profile_select_notice, profile_select.PROFILE_IN_USE_NOTICE)
        self.assertEqual(state.current_state, state_names.STATE_PROFILE_SELECT)

    def test_other_profiles_can_still_be_deleted(self):
        self.load_slot(2)
        self.open_profile_select_again()

        self.try_to_delete(1)

        self.assertFalse(saves.profile_exists(1))
        self.assertTrue(saves.profile_exists(2))
        self.assertEqual(state.profile_select_notice, "")

    def test_a_guest_session_has_no_loaded_profile(self):
        click(profile_select.guest_profile_rect.center)
        self.assertTrue(state.guest_mode)
        self.open_profile_select_again()

        self.try_to_delete(1)
        self.try_to_delete(2)

        self.assertFalse(saves.profile_exists(1))
        self.assertFalse(saves.profile_exists(2))

    def test_at_start_up_nothing_is_loaded_so_slot_one_can_be_deleted(self):
        # current_profile_slot starts as 1 before any profile is picked.
        click(delete_button(1))

        self.assertTrue(state.confirm_delete_profile)
        click(profile_select.confirm_delete_yes_rect.center)
        self.assertFalse(saves.profile_exists(1))
        self.assertEqual(state.profile_select_notice, "")

    def test_the_in_use_notice_is_gone_when_the_screen_opens_again(self):
        self.load_slot(2)
        self.open_profile_select_again()
        self.try_to_delete(2)
        self.assertEqual(state.profile_select_notice, profile_select.PROFILE_IN_USE_NOTICE)

        click(profile_select.guest_profile_rect.center)
        self.open_profile_select_again()
        profile_select.enter()   # the loop calls this when the screen opens

        self.assertEqual(state.profile_select_notice, "")

    def test_deleting_another_profile_clears_the_in_use_notice(self):
        self.load_slot(2)
        self.open_profile_select_again()
        self.try_to_delete(2)
        self.assertEqual(state.profile_select_notice, profile_select.PROFILE_IN_USE_NOTICE)

        self.try_to_delete(1)

        self.assertFalse(saves.profile_exists(1))
        self.assertEqual(state.profile_select_notice, "")


if __name__ == "__main__":
    unittest.main()
