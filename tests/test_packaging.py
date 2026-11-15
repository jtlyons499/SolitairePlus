"""Packaging guards that can be checked without building the exe."""
import ast
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def spec_constant(name):
    tree = ast.parse((ROOT / "SolitairePlus.spec").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name} not found in SolitairePlus.spec")


class PackagingTests(unittest.TestCase):
    def test_multiplayer_selftest_passes_from_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.txt"
            env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
            done = subprocess.run([sys.executable, "main.py", "--multiplayer", "--selftest", "--selftest-report", str(report)],
                                  cwd=ROOT, env=env, capture_output=True, timeout=120)
            text = report.read_text(encoding="utf-8") if report.exists() else done.stdout.decode(errors="replace")
            self.assertEqual(done.returncode, 0, text)
            self.assertIn("PASSED", text)
            self.assertIn("ok     net_client", text)

    def test_selftest_skips_exactly_the_modules_the_package_leaves_out(self):
        sys.path.insert(0, str(ROOT))
        import multiplayer_launcher
        excluded = {name.removesuffix(".py") for name in spec_constant("MP_EXCLUDED")}
        self.assertEqual(excluded, multiplayer_launcher.SELFTEST_SKIP)

    def test_version_ships_as_a_loose_file_not_inside_the_game_exe(self):
        spec = (ROOT / "SolitairePlus.spec").read_text(encoding="utf-8")
        self.assertIn("excludes=['version', 'netservice', 'updater']", spec)
        self.assertIn("(str(project / 'version.py'), '.')", spec)
        self.assertEqual(spec_constant("CONTENTS"), "SolitairePlus_Data")


if __name__ == "__main__":
    unittest.main()
