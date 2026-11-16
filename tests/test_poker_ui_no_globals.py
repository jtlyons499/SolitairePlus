"""The poker table UI modules keep their state without 'global' statements (restructure end state).

Shared table settings and screen state live in solitaireplus/app/state.py; module-private
caches (fonts, chip images, animation keys) live in one mutable holder per module. This
checks the source for ast.Global nodes and globals() calls, and that the moved state still
behaves as before.
"""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POKER = ROOT / "solitaireplus" / "games" / "poker"
MODULES = [
    "holdem_ui.py",
    "five_card_draw_ui.py",
    "seven_card_stud_ui.py",
    "blind_mans_bluff_ui.py",
    "five_o_ui.py",
    "speech.py",
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


class PokerUiNoGlobalsTests(unittest.TestCase):
    def test_no_global_statements_or_globals_calls(self):
        for name in MODULES:
            with self.subTest(module=name):
                self.assertEqual(global_uses(POKER / name), [])

    def test_chat_popup_setting_round_trip(self):
        from solitaireplus.games.poker import speech
        before = speech.is_poker_chat_popups_enabled()
        try:
            speech.set_poker_chat_popups_enabled(False)
            self.assertFalse(speech.is_poker_chat_popups_enabled())
            speech.set_poker_chat_popups_enabled(1)
            self.assertIs(speech.is_poker_chat_popups_enabled(), True)
        finally:
            speech.set_poker_chat_popups_enabled(before)

    def test_holdem_options_toggle_and_manual_bet_clear(self):
        from solitaireplus.games.poker import holdem_ui
        was_open = holdem_ui.is_holdem_options_open()
        try:
            holdem_ui.toggle_holdem_options()
            self.assertIs(holdem_ui.is_holdem_options_open(), not was_open)
            holdem_ui.close_holdem_options()
            self.assertFalse(holdem_ui.is_holdem_options_open())
        finally:
            if was_open:
                holdem_ui.toggle_holdem_options()
        holdem_ui.clear_holdem_manual_bet()


if __name__ == "__main__":
    unittest.main()
