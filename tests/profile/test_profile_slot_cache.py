"""Profile-select screen: the save slots are read once, not every frame (B10).

Drawing the screen used to call load_profile for each of the three slots every frame (reading,
parsing and migrating each save, and hashing a damaged one). The slot data is now kept by the
screen and read again when the screen is entered and after a profile is saved, created or deleted.
"""
import ast
import copy
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame

from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.profile import profile_editor
from solitaireplus.profile import profile_select
from solitaireplus.profile.saves import ProfileDamaged
from tests.support import locate

_MISSING = object()


class FakeFont:
    """Records every text it renders (stands in for the screen's fonts)."""

    def __init__(self, texts):
        self.texts = texts

    def render(self, text, *args, **kwargs):
        self.texts.append(text)
        return pygame.Surface((8, 8))


class AnyFont:
    """fonts stand-in: every font name gives a FakeFont that records into one list."""

    def __init__(self, texts):
        self._font = FakeFont(texts)

    def __getattr__(self, name):
        return self._font


def saved_profile(name, level):
    return {"identity": {"name": name}, "progression": {"level": level}}


class ProfileSlotCacheTests(unittest.TestCase):
    def setUp(self):
        if not pygame.get_init():
            pygame.init()
        # The save files: slot -> data (None = empty slot).
        self.saves = {1: saved_profile("Ann", 4), 2: saved_profile("Bo", 9), 3: None}
        self.loads = []
        self.texts = []

        def load_profile(slot):
            self.loads.append(slot)
            return copy.deepcopy(self.saves.get(slot))

        def delete_profile(slot):
            self.saves[slot] = None

        def save_profile(data, slot):
            self.saves[slot] = copy.deepcopy(data)
            return True

        self.save_profile = save_profile
        surface = pygame.Surface((profile_select.BASE_WIDTH, profile_select.BASE_HEIGHT))
        quiet = types.SimpleNamespace(audio=types.SimpleNamespace(play_sound=lambda *a, **k: None))
        images = types.SimpleNamespace(get_event_ui_asset=lambda *args, **kwargs: None)
        buttons = types.SimpleNamespace(draw_button=lambda *args, **kwargs: None)
        for target, name, value in (
                (profile_select, "load_profile", load_profile),
                (profile_select, "delete_profile", delete_profile),
                (profile_select, "window", types.SimpleNamespace(game_surface=surface)),
                (profile_select, "fonts", AnyFont(self.texts)),
                (profile_select, "images", images),
                (profile_select, "buttons", buttons),
                (profile_select, "sounds", quiet),
                (profile_select, "finish_profile_selection", lambda: None),
                (profile_editor, "save_profile", save_profile),
                (profile_editor, "sounds", quiet)):
            patcher = patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        # Don't leave this test's fake slots in the module's cache.
        self.addCleanup(profile_select.forget_slot_display_data)
        self.set_state(
            menu_mouse_pos=(0, 0),
            game_mouse_pos=(0, 0),
            profile_select_notice="",
            profile_select_return_state=state_names.STATE_MENU,
            profile_switch_snapshot=None,
            confirm_delete_profile=False,
            profile_delete_slot=None,
            current_profile_slot=None,     # no profile loaded, so any slot may be deleted
            guest_mode=False,
            current_state=state_names.STATE_PROFILE_SELECT,
        )

    def set_state(self, **values):
        """Set state values for this test only (the old values come back afterwards)."""
        for name, value in values.items():
            old = getattr(state, name, _MISSING)
            if old is _MISSING:
                self.addCleanup(lambda name=name: hasattr(state, name) and delattr(state, name))
            else:
                self.addCleanup(setattr, state, name, old)
            setattr(state, name, value)

    def draw_frames(self, count=1):
        del self.texts[:]
        for _ in range(count):
            profile_select.draw()
        return list(self.texts)

    def click(self, target, pos):
        state.game_mouse_pos = pos
        target.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))

    # ------------------------------------------------------------------ reading

    def test_ten_frames_read_each_slot_once(self):
        profile_select.enter()
        shown = self.draw_frames(10)
        self.assertEqual(sorted(self.loads), [1, 2, 3])
        self.assertEqual(shown.count("Ann"), 10)
        self.assertEqual(shown.count("Empty Slot"), 10)

    def test_entering_the_screen_reads_the_slots_again(self):
        profile_select.enter()
        self.draw_frames(3)
        self.saves[3] = saved_profile("Cy", 2)        # changed while the screen was not shown
        profile_select.enter()
        shown = self.draw_frames(3)
        self.assertEqual(sorted(self.loads), [1, 1, 2, 2, 3, 3])
        self.assertIn("Cy", shown)
        self.assertNotIn("Empty Slot", shown)

    def test_damaged_save_is_read_once(self):
        """A damaged save is hashed on every read, so it must not be read every frame either."""
        def damaged(slot):
            self.loads.append(slot)
            raise ProfileDamaged("damaged")

        with patch.object(profile_select, "load_profile", damaged):
            profile_select.enter()
            shown = self.draw_frames(10)
        self.assertEqual(sorted(self.loads), [1, 2, 3])
        self.assertEqual(shown.count(ProfileDamaged.short_label), 30)

    # ------------------------------------------------------------------ changes

    def test_deleting_a_profile_reads_the_slots_again(self):
        profile_select.enter()
        self.assertIn("Ann", self.draw_frames())
        state.confirm_delete_profile = True
        state.profile_delete_slot = 1
        self.click(profile_select, profile_select.confirm_delete_yes_rect.center)
        self.assertIsNone(self.saves[1])
        self.assertFalse(state.confirm_delete_profile)
        shown = self.draw_frames(5)
        self.assertNotIn("Ann", shown)
        self.assertEqual(shown.count("Empty Slot"), 10)   # slots 1 and 3, five frames
        self.assertEqual(self.loads.count(1), 2)          # once before the delete, once after

    def test_delete_clicks_follow_the_slots_shown(self):
        """The Delete buttons drawn come from the cache, so clicks must use it too (review of B10)."""
        profile_select.enter()
        self.draw_frames()
        self.saves[3] = saved_profile("Cy", 2)        # written by another copy of the game
        self.saves[1] = None                          # deleted by another copy of the game
        loaded = []
        with patch.object(profile_select, "save_data", types.SimpleNamespace(apply_profile_save_data=loaded.append)),                 patch.object(profile_select, "leveling", types.SimpleNamespace(sync_unlocks_for_current_level=lambda: None)):
            # Slot 3 shows no Delete button, so this is a click on the slot itself (it loads it).
            self.click(profile_select, profile_select.profile_delete_rects[2].center)
        self.assertFalse(state.confirm_delete_profile)
        self.assertEqual([data["identity"]["name"] for data in loaded], ["Cy"])
        state.current_state = state_names.STATE_PROFILE_SELECT
        self.click(profile_select, profile_select.profile_delete_rects[0].center)
        self.assertTrue(state.confirm_delete_profile)     # slot 1 still shows one
        self.assertEqual(state.profile_delete_slot, 1)

    def test_cancelling_a_delete_keeps_the_slots(self):
        profile_select.enter()
        self.draw_frames()
        state.confirm_delete_profile = True
        state.profile_delete_slot = 1
        self.click(profile_select, profile_select.confirm_delete_no_rect.center)
        self.draw_frames(5)
        self.assertEqual(sorted(self.loads), [1, 2, 3])

    def editor_save(self, **values):
        """Press Save on the profile editor with the given state."""
        defaults = dict(
            gender_dropdown_open=False,
            favorite_suit_dropdown_open=False,
            profile_country_text="",
            profile_age_text="",
            profile_name_text="Player",
            profile_name_active=False,
            profile_country_active=False,
            profile_age_active=False,
            profile_hometown_active=False,
            profile_bio_active=False,
            profile_message="",
            player_name="Player",
            profile_creation_mode=False,
            pending_profile_slot=None,
            guest_mode=False,
            current_profile_slot=None,
            current_state=state_names.STATE_PROFILE,
        )
        defaults.update(values)
        self.set_state(**defaults)
        built = saved_profile(defaults["profile_name_text"], 1)
        with patch.object(profile_editor, "save_data",
                          types.SimpleNamespace(build_profile_save_data=lambda: copy.deepcopy(built))):
            self.click(profile_editor, profile_editor.profile_save_rect.center)

    def test_creating_a_profile_reads_the_slots_again(self):
        profile_select.enter()
        self.assertIn("Empty Slot", self.draw_frames())
        self.editor_save(profile_creation_mode=True, pending_profile_slot=3, profile_name_text="Dee")
        self.assertEqual(self.saves[3]["identity"]["name"], "Dee")
        state.current_state = state_names.STATE_PROFILE_SELECT
        shown = self.draw_frames(5)
        self.assertEqual(shown.count("Dee"), 5)
        self.assertNotIn("Empty Slot", shown)

    def test_saving_an_edited_profile_reads_the_slots_again(self):
        profile_select.enter()
        self.assertIn("Ann", self.draw_frames())
        self.editor_save(current_profile_slot=1, profile_name_text="Ann Marie")
        self.assertEqual(self.saves[1]["identity"]["name"], "Ann Marie")
        state.current_state = state_names.STATE_PROFILE_SELECT
        shown = self.draw_frames(5)
        self.assertEqual(shown.count("Ann Marie"), 5)
        self.assertNotIn("Ann", shown)

    # ------------------------------------------------------------------ every writer

    def test_profile_screens_refresh_the_slots_after_every_write(self):
        """Code of the profile screens that saves or deletes a profile also forgets the slot data.

        Saves made on other screens (Career auto-saves) need nothing: the profile-select screen
        can only be shown again through a screen change, and enter() reads the slots again then.
        """
        writers = {"save_profile", "delete_profile"}
        checked = []
        for module in (profile_select, profile_editor):
            tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
            for function in tree.body:
                if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                called = set()
                for node in ast.walk(function):
                    if isinstance(node, ast.Call):
                        func = node.func
                        called.add(func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None))
                if called & writers:
                    checked.append(function.name)
                    self.assertIn("forget_slot_display_data", called,
                                  f"{module.__name__}.{function.name} writes a save but keeps old slot data")
        self.assertEqual(len(checked), 2, checked)   # the delete confirmation and the editor's Save

    def test_the_loop_enters_this_screen_module(self):
        """loop.run_screen_hooks calls enter() of the module SCREENS names for the profile-select state."""
        tree = ast.parse((locate.ROOT / "solitaireplus" / "app" / "loop.py").read_text(encoding="utf-8"))
        screens = next(node.value for node in tree.body
                       if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == "SCREENS")
        entries = {ast.unparse(key): value.value for key, value in zip(screens.keys, screens.values)}
        self.assertEqual(entries["state_names.STATE_PROFILE_SELECT"], profile_select.__name__)
        self.assertTrue(callable(profile_select.enter))


if __name__ == "__main__":
    unittest.main()
