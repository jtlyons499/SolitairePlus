"""D1 (Customize): the stray 'DEBUG +100 XP' button is gone from the Customize screen.

The designer keeps the F10 debug menu; debug buttons outside it must not ship. The old button
(debug_xp_rect, top-left corner of the Customize screen) added 100 XP on every click.
"""
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

PACKAGE = Path(__file__).resolve().parents[1] / 'solitaireplus'
OLD_BUTTON_SPOT = (30, 30)   # inside the old debug_xp_rect (20, 20, 180, 45)


class CustomizeDebugButtonRemovedTests(unittest.TestCase):
    def test_debug_xp_rect_is_gone_from_the_package(self):
        hits = []
        for path in PACKAGE.rglob('*.py'):
            text = path.read_text(encoding='utf-8')
            for marker in ('debug_xp_rect', 'DEBUG +100 XP'):
                if marker in text:
                    hits.append(f'{path.relative_to(PACKAGE.parent)}: {marker}')
        self.assertEqual(hits, [], 'the Customize debug XP button is still in solitaireplus/')

    def test_customize_module_has_no_debug_xp_rect(self):
        from solitaireplus.menus import customize
        self.assertFalse(hasattr(customize, 'debug_xp_rect'))

    def test_click_in_the_old_button_spot_gives_no_xp(self):
        from solitaireplus.app import state
        from solitaireplus.menus import customize

        names = ('game_mouse_pos', 'customize_page', 'index', 'rect')
        missing = object()
        saved = {name: getattr(state, name, missing) for name in names}

        def restore():
            for name, value in saved.items():
                if value is missing:
                    if hasattr(state, name):
                        delattr(state, name)
                else:
                    setattr(state, name, value)

        self.addCleanup(restore)
        state.game_mouse_pos = OLD_BUTTON_SPOT
        state.customize_page = 0

        leveling = MagicMock()
        sounds = MagicMock()
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=OLD_BUTTON_SPOT)
        with patch.object(customize, 'leveling', leveling, create=True), \
                patch.object(customize, 'sounds', sounds), \
                patch.object(customize, 'get_customize_asset_ids', return_value=[]):
            customize.handle_event(event)

        leveling.add_player_xp.assert_not_called()
        sounds.audio.play_sound.assert_not_called()


if __name__ == '__main__':
    unittest.main()
