"""The packaged game must contain every module the game opens by name.

The main loop opens screens from module-name strings (solitaireplus/app/loop.py
SCREENS) and some modules reach each other through solitaireplus.app.lazy. PyInstaller
only follows import statements, so those modules were missing from the packaged game:
it crashed at start-up with "No module named 'solitaireplus.menus.splash'".
SolitairePlus.spec now collects every solitaireplus module for the game exe.
"""

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "solitaireplus"


def module_exists(name):
    path = ROOT.joinpath(*name.split("."))
    return path.with_suffix(".py").is_file() or (path / "__init__.py").is_file()


def screen_module_names():
    tree = ast.parse((PACKAGE / "app" / "loop.py").read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            if re.fullmatch(r"solitaireplus(\.\w+)+(:\w+)?", value):
                names.add(value.split(":")[0])
    return names


def lazy_module_names():
    names = set()
    for path in PACKAGE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "lazy"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                names.add(node.args[0].value)
    return names


def game_analysis_source():
    spec = (ROOT / "SolitairePlus.spec").read_text(encoding="utf-8")
    start = spec.index("game = Analysis(")
    end = spec.index("game_pyz = PYZ(", start)
    return spec[start:end]


class PackagedGameModulesTests(unittest.TestCase):

    def test_the_game_exe_collects_every_solitaireplus_module(self):
        analysis = re.sub(r"#.*", "", game_analysis_source())
        self.assertRegex(analysis, r"collect_submodules\(\s*['\"]solitaireplus['\"]\s*\)")

    def test_modules_opened_by_name_are_solitaireplus_modules(self):
        names = screen_module_names() | lazy_module_names()
        self.assertIn("solitaireplus.menus.splash", names)
        for name in sorted(names):
            with self.subTest(module=name):
                self.assertTrue(name.startswith("solitaireplus."), name)
                self.assertTrue(module_exists(name), f"{name} has no source file")


if __name__ == "__main__":
    unittest.main()
