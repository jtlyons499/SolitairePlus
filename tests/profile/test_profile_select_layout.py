"""Profile-select screen layout: slot text must not sit under the slot's Delete button (B9)."""
import types
import unittest
from unittest.mock import patch

import pygame

from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.profile import profile_select


class RecordingFont:
    """Wraps a real font and remembers which text each rendered surface shows."""

    def __init__(self, font, texts):
        self.font = font
        self.texts = texts

    def render(self, text, *args, **kwargs):
        surface = self.font.render(text, *args, **kwargs)
        self.texts[id(surface)] = text
        return surface


class RecordingSurface(pygame.Surface):
    """A game surface that records where every text surface is blitted."""

    def __init__(self, size, texts):
        super().__init__(size)
        self.texts = texts
        self.placed = []   # (text, Rect)

    def blit(self, source, dest, *args, **kwargs):
        text = self.texts.get(id(source))
        if text is not None:
            self.placed.append((text, pygame.Rect(dest[0], dest[1], *source.get_size())))
        return super().blit(source, dest, *args, **kwargs)


SLOTS = {
    1: {"exists": True, "name": "Dan", "level": 12},             # normal save
    2: {"exists": True, "name": "Save damaged", "level": None},  # damaged save
    3: {"exists": False, "name": "Empty Slot", "level": None},   # no Delete button
}


class ProfileSelectLayoutTests(unittest.TestCase):
    def draw(self):
        if not pygame.font.get_init():
            pygame.font.init()
        texts = {}
        surface = RecordingSurface((profile_select.BASE_WIDTH, profile_select.BASE_HEIGHT), texts)
        fonts = types.SimpleNamespace(
            options_title_font=RecordingFont(pygame.font.SysFont(None, 60), texts),
            option_label_font=RecordingFont(pygame.font.SysFont(None, 34), texts),
            option_value_font=RecordingFont(pygame.font.SysFont(None, 27), texts),
            ui_small_font=RecordingFont(pygame.font.SysFont(None, 24), texts),
        )
        images = types.SimpleNamespace(get_event_ui_asset=lambda *args, **kwargs: None)
        with patch.object(profile_select, "window", types.SimpleNamespace(game_surface=surface)), \
                patch.object(profile_select, "fonts", fonts), \
                patch.object(profile_select, "images", images), \
                patch.object(profile_select, "get_profile_slot_display_data", SLOTS.__getitem__), \
                patch.object(state, "menu_mouse_pos", (0, 0), create=True), \
                patch.object(state, "profile_select_notice", "", create=True), \
                patch.object(state, "profile_select_return_state", state_names.STATE_MENU, create=True):
            profile_select.draw_profile_select_screen()
        return surface.placed

    def text_rect(self, placed, text):
        rects = [rect for shown, rect in placed if shown == text]
        self.assertEqual(len(rects), 1, f"{text!r} should be drawn once, got {placed}")
        return rects[0]

    def test_level_text_is_not_under_the_delete_button(self):
        placed = self.draw()
        level = self.text_rect(placed, "Level 12")
        delete_rect = profile_select.profile_delete_rects[0]
        self.assertFalse(level.colliderect(delete_rect), (level, delete_rect))
        self.assertTrue(profile_select.profile_slot_rects[0].contains(level))

    def test_damaged_notice_is_not_under_the_delete_button(self):
        placed = self.draw()
        notice = self.text_rect(placed, "Can't open")
        delete_rect = profile_select.profile_delete_rects[1]
        self.assertFalse(notice.colliderect(delete_rect), (notice, delete_rect))
        self.assertTrue(profile_select.profile_slot_rects[1].contains(notice))

    def test_existing_slots_still_draw_their_delete_buttons(self):
        placed = self.draw()
        deletes = [rect for shown, rect in placed if shown == "Delete"]
        self.assertEqual(len(deletes), 2)   # the empty slot has none
        for rect, delete_rect in zip(deletes, profile_select.profile_delete_rects[:2]):
            self.assertEqual(rect.center, delete_rect.center)


if __name__ == "__main__":
    unittest.main()
