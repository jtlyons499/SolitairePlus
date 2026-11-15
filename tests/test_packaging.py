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
        from solitaireplus.app import multiplayer_launcher
        excluded = {name.removesuffix(".py") for name in spec_constant("MP_EXCLUDED")}
        self.assertEqual(excluded, multiplayer_launcher.SELFTEST_SKIP)

    def test_version_ships_as_a_loose_file_not_inside_the_game_exe(self):
        spec = (ROOT / "SolitairePlus.spec").read_text(encoding="utf-8")
        self.assertIn("excludes=['version', 'netservice', 'updater']", spec)
        self.assertIn("(str(project / 'version.py'), '.')", spec)
        self.assertEqual(spec_constant("CONTENTS"), "SolitairePlus_Data")


class InstallerAndSigningTests(unittest.TestCase):
    ISS = (ROOT / "installer" / "SolitairePlus.iss").read_text(encoding="utf-8")

    def test_installer_is_per_user_and_never_needs_admin(self):
        self.assertIn("PrivilegesRequired=lowest", self.ISS)
        self.assertIn(r"DefaultDirName={autopf}\SolitairePlus", self.ISS)

    def test_installer_identity_never_changes(self):
        # Windows recognises an existing install by AppId; changing it would break upgrades.
        self.assertIn("AppId={{6B0E4C5A-3D7F-4B0E-9A61-2F7C1D9E5A42}", self.ISS)

    def test_uninstaller_only_deletes_saves_when_the_player_says_yes(self):
        section = self.ISS.split("[UninstallDelete]")[1].split("[Code]")[0]
        self.assertNotIn("localappdata", section.lower())
        self.assertIn("MB_DEFBUTTON2", self.ISS)  # "No" is the default answer to deleting saves

    def test_signing_script_understands_the_trusted_publisher_list(self):
        """tools/sign_release.ps1 -CheckTrusted must find a thumbprint written the documented way."""
        import re
        script = (ROOT / "tools" / "sign_release.ps1").read_text(encoding="utf-8")
        pattern = re.compile(re.search(r"-Pattern '([^']+)'", script).group(1))
        publishers = (ROOT / "updater" / "trusted_publishers.py").read_text(encoding="utf-8")
        example = next(line for line in publishers.splitlines() if '"thumbprint"' in line)
        uncommented = example.replace("# ", "", 1)   # what a maintainer gets by removing the "#"
        self.assertRegex(uncommented, pattern)
        self.assertIsNone(pattern.match(example))    # a commented-out entry must NOT count as trusted

    def test_release_builds_refuse_to_publish_unsigned(self):
        workflow = (ROOT / ".github" / "workflows" / "release-windows.yml").read_text(encoding="utf-8")
        self.assertIn("Release builds must be signed", workflow)
        self.assertIn("-CheckTrusted", workflow)


if __name__ == "__main__":
    unittest.main()
