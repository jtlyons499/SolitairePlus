"""The F10 debug menu modules keep their state without 'global' statements (N7-debug).

The accordion state, the transient debug message and the opponent picker's font cache are
module-private, so they live in one mutable holder per module. This checks the source for
ast.Global nodes and globals() calls, and that the moved state still behaves as before.
"""
import ast
import os
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

ROOT = Path(__file__).resolve().parents[1]
DEBUG = ROOT / "solitaireplus" / "debug"
MODULES = [
    "menu.py",
    "poker_select.py",
]


def global_uses(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Global):
            found.append(f"{path.name}:{node.lineno}: global {', '.join(node.names)}")
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
              and node.func.id == "globals"):
            found.append(f"{path.name}:{node.lineno}: globals()")
    return found


class DebugNoGlobalsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def test_no_global_statements_or_globals_calls(self):
        for name in MODULES:
            with self.subTest(module=name):
                self.assertEqual(global_uses(DEBUG / name), [])

    def test_whole_debug_package_has_no_globals(self):
        # The rest of the F10 debug code (actions, menu_screen, ...) must stay that way too.
        for path in sorted(DEBUG.glob("*.py")):
            with self.subTest(module=path.name):
                self.assertEqual(global_uses(path), [])

    def test_minigame_accordion_toggle_round_trip(self):
        from solitaireplus.debug import menu
        before = menu.get_expanded_minigame_category()
        try:
            if before is not None:
                # Collapse whatever is open so the test starts from the default.
                for _category_id, action, _label, _entries in menu.MINIGAME_CATEGORIES:
                    if _category_id == before:
                        menu.toggle_minigame_category(action)
            self.assertIsNone(menu.get_expanded_minigame_category())
            category_id, action, _label, entries = menu.MINIGAME_CATEGORIES[0]
            child_action = entries[0][0]
            self.assertNotIn(child_action, menu._ACTION_RECTS)

            self.assertTrue(menu.toggle_minigame_category(action))
            self.assertEqual(menu.get_expanded_minigame_category(), category_id)
            self.assertIn(child_action, menu._ACTION_RECTS)

            other_id, other_action, _other_label, _other_entries = menu.MINIGAME_CATEGORIES[1]
            self.assertTrue(menu.toggle_minigame_category(other_action))
            self.assertEqual(menu.get_expanded_minigame_category(), other_id)
            self.assertNotIn(child_action, menu._ACTION_RECTS)

            self.assertTrue(menu.toggle_minigame_category(other_action))
            self.assertIsNone(menu.get_expanded_minigame_category())
            self.assertFalse(menu.toggle_minigame_category("not_a_category"))
            self.assertIsNone(menu.get_expanded_minigame_category())
        finally:
            if menu.get_expanded_minigame_category() != before:
                for _category_id, action, _label, _entries in menu.MINIGAME_CATEGORIES:
                    if _category_id == before:
                        menu.toggle_minigame_category(action)

    def test_debug_message_is_drawn_until_it_expires(self):
        from solitaireplus.debug import menu
        font = pygame.font.Font(None, 24)
        surface = pygame.Surface((1366, 768))

        def drawn():
            surface.fill((0, 0, 0))
            menu._draw_debug_message(surface, font)
            return surface.get_at((683, 662))[:3] != (0, 0, 0) or any(
                surface.get_at((x, 662))[:3] != (0, 0, 0) for x in range(560, 800, 4))

        now = pygame.time.get_ticks()
        menu.show_debug_message("Hello debug", duration=100000)
        self.assertTrue(drawn())
        # Very short durations are clamped up to 250 ms; an empty message draws nothing.
        menu.show_debug_message("", duration=1)
        self.assertFalse(drawn())
        menu.show_debug_message("Gone", duration=1)
        self.assertTrue(drawn() or pygame.time.get_ticks() - now >= 250)
        # Leave a message that has already expired, as at start-up.
        menu.show_debug_message("", duration=1800)

    def test_poker_select_fonts_are_built_once(self):
        from solitaireplus.debug import poker_select
        first = poker_select._get_fonts()
        self.assertEqual(set(first), {"title", "large", "medium", "small"})
        self.assertIs(poker_select._get_fonts(), first)


if __name__ == "__main__":
    unittest.main()
