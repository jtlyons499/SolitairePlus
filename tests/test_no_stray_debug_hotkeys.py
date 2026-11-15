"""D1 (complete): the F10 debug menu is the only debug entry point left in the game.

The designer keeps the F10 menu public and moved the Solitaire instant win into it. Every other
debug hotkey or button outside it is gone; this checks the whole game source (main.py and
solitaireplus/, through tests/support/locate.py) for them:
* Solitaire F8 (instant win) and F7 (auto-solve);
* Texas Hold'em F7 (rigged heads-up hand, debug_setup_holdem_heads_up), Space (deal the next
  street) and B (bet $50 and print the table);
* Score Four F6 (complete the training);
* the Customize screen's 'DEBUG +100 XP' button (debug_xp_rect).
The only function keys the game binds are F10 (the debug menu) and F11 (fullscreen).
"""
import ast
import re
import unittest
from pathlib import Path

from tests.support import locate

HOLDEM_FILES = ('solitaireplus/games/poker/holdem_screen.py', 'solitaireplus/games/poker/holdem_ui.py')
FUNCTION_KEY = re.compile(r'^K_F\d+$')
ALLOWED_FUNCTION_KEYS = {('solitaireplus/app/loop.py', 'K_F10'), ('solitaireplus/app/loop.py', 'K_F11')}


def relative(path):
    return Path(path).resolve().relative_to(locate.ROOT).as_posix()


class NoStrayDebugHotkeys(unittest.TestCase):

    def assert_not_in_source(self, *markers, source=None):
        source = locate.source() if source is None else source
        self.assertEqual([marker for marker in markers if marker in source], [],
                         'a removed debug hotkey or button is still in the game source')

    def test_no_solitaire_f7_or_f8(self):
        self.assert_not_in_source('K_F7', 'K_F8')

    def test_no_holdem_f7_space_or_b(self):
        self.assert_not_in_source('K_F7', 'debug_setup_holdem_heads_up')
        for path in HOLDEM_FILES:
            with self.subTest(file=path):
                tree = ast.parse((locate.ROOT / path).read_text(encoding='utf-8'))
                keys = {node.attr for node in ast.walk(tree)
                        if isinstance(node, ast.Attribute) and node.attr in ('K_F7', 'K_SPACE', 'K_b')}
                self.assertEqual(keys, set(), "the Hold'em table still binds a debug key")

    def test_no_customize_debug_xp_button(self):
        self.assert_not_in_source('debug_xp_rect', 'DEBUG +100 XP')

    def test_no_score_four_f6(self):
        self.assert_not_in_source('K_F6')

    def test_only_f10_and_f11_are_bound(self):
        bound = set()
        for path, tree in locate.trees():
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) and FUNCTION_KEY.match(node.attr):
                    bound.add((relative(path), node.attr))
        self.assertEqual(bound, ALLOWED_FUNCTION_KEYS)

    def test_the_f10_debug_menu_stays(self):
        # The designer keeps the menu in public builds.
        loop = locate.function('run', path='solitaireplus/app/loop.py')
        self.assertIn('K_F10', loop)
        self.assertIn('STATE_DEBUG_MENU', loop)


if __name__ == '__main__':
    unittest.main()
