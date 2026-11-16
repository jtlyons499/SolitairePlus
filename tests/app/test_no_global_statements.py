"""No 'global' statements and no globals() calls in the game code (restructure checklist 10.4).

Shared runtime state goes through solitaireplus/app/state.py; a module's private caches live in one
mutable holder object in that module. This parses every .py file under solitaireplus/ plus main.py
and fails on any ast.Global node or any call to globals(), and checks that the race deal pool cache
(the last module-level 'global' to go) still loads the pool once.
"""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def scanned_files():
    return sorted((ROOT / "solitaireplus").rglob("*.py")) + [ROOT / "main.py"]


def global_uses(source, name="<source>"):
    tree = ast.parse(source, filename=name)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Global):
            found.append(f"{name}:{node.lineno}: global {', '.join(node.names)}")
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "globals":
                found.append(f"{name}:{node.lineno}: globals()")
            elif (isinstance(func, ast.Attribute) and func.attr == "globals"
                  and isinstance(func.value, ast.Name) and func.value.id == "builtins"):
                found.append(f"{name}:{node.lineno}: builtins.globals()")
    return found


class NoGlobalStatementsTests(unittest.TestCase):
    def test_scan_covers_the_game_code(self):
        files = scanned_files()
        self.assertTrue((ROOT / "main.py").is_file())
        self.assertGreater(len(files), 100)
        self.assertIn(ROOT / "solitaireplus" / "app" / "state.py", files)

    def test_detector_flags_global_and_globals_calls(self):
        source = (
            "import builtins\n"
            "def f():\n"
            "    global x\n"
            "    x = globals()\n"
            "    return builtins.globals()\n"
        )
        self.assertEqual(global_uses(source), [
            "<source>:3: global x",
            "<source>:4: globals()",
            "<source>:5: builtins.globals()",
        ])
        # Names that merely contain the word are fine (game_globals, a docstring mentioning globals()).
        self.assertEqual(global_uses('"""globals() went away."""\ngame_globals = 1\n'), [])

    def test_no_global_statements_or_globals_calls(self):
        problems = []
        for path in scanned_files():
            relative = path.relative_to(ROOT).as_posix()
            problems.extend(global_uses(path.read_text(encoding="utf-8"), relative))
        self.assertEqual(problems, [])


class RaceDealPoolCacheTests(unittest.TestCase):
    def test_pool_is_loaded_and_verified_once(self):
        from unittest.mock import patch
        from solitaireplus.games.solitaire import race_deals
        saved = race_deals._cache.pool
        try:
            race_deals._cache.pool = None
            with patch.object(race_deals, "verify_deal", wraps=race_deals.verify_deal) as verify:
                first = race_deals._load_pool()
                calls = verify.call_count
                self.assertEqual(calls, len(first))
                self.assertIs(race_deals._load_pool(), first)
                self.assertEqual(verify.call_count, calls)
            self.assertIs(race_deals._cache.pool, first)
        finally:
            race_deals._cache.pool = saved


if __name__ == "__main__":
    unittest.main()
