"""The casual card modules keep their state without 'global' statements (restructure end state, N7).

Module-private caches (fonts, the player's card rects) live in one mutable holder per module.
This checks the source of every module in solitaireplus/games/cards/ for ast.Global nodes and
globals() calls, and that the moved caches still behave as before.
"""
import ast
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "solitaireplus" / "games" / "cards"
LISTED = ["crazy_eights_ui.py", "bango_ui.py"]


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


class CardsUiNoGlobalsTests(unittest.TestCase):
    def test_listed_modules_have_no_global_statements_or_globals_calls(self):
        for name in LISTED:
            with self.subTest(module=name):
                self.assertEqual(global_uses(CARDS / name), [])

    def test_no_cards_module_uses_global(self):
        for path in sorted(CARDS.glob("*.py")):
            with self.subTest(module=path.name):
                self.assertEqual(global_uses(path), [])


class CardsUiCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        import pygame
        pygame.font.init()

    def test_fonts_are_built_once(self):
        from solitaireplus.games.cards import bango_ui, crazy_eights_ui
        for module in (crazy_eights_ui, bango_ui):
            with self.subTest(module=module.__name__):
                first = module._get_fonts()
                self.assertEqual(set(first), {"title", "large", "medium", "small", "tiny"})
                self.assertIs(module._get_fonts(), first)

    def test_crazy_eights_card_click_uses_last_drawn_layout(self):
        import random
        import pygame
        from solitaireplus.games.cards import crazy_eights_ui
        from solitaireplus.games.cards.crazy_eights import CrazyEightsGame

        state = random.getstate()
        try:
            random.seed(8)
            game = CrazyEightsGame()
            game.start_game([{"name": "Ann"}, {"name": "Bo"}, {"name": "Cy"}], hand_size=5)
        finally:
            random.setstate(state)
        self.assertEqual(game.current_player, 0)
        surface = pygame.Surface((1366, 768))

        # The rects drawn for a five-card hand are the ones a click is tested against.
        crazy_eights_ui.draw_crazy_eights(surface, None, game, {}, None)
        five = crazy_eights_ui._player_hand_layout(5)
        self.assertEqual(crazy_eights_ui.get_crazy_eights_action(five[4].center, game),
                         (crazy_eights_ui.ACTION_CARD, 4))

        # Drawing a one-card hand replaces them: the old fifth card's spot is empty now.
        game.hands[0] = game.hands[0][:1]
        crazy_eights_ui.draw_crazy_eights(surface, None, game, {}, None)
        self.assertIsNone(crazy_eights_ui.get_crazy_eights_action(five[4].center, game))
        one = crazy_eights_ui._player_hand_layout(1)
        self.assertEqual(crazy_eights_ui.get_crazy_eights_action(one[0].center, game),
                         (crazy_eights_ui.ACTION_CARD, 0))


if __name__ == "__main__":
    unittest.main()
