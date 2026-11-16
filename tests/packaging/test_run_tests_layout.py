"""tools/run_tests.py: the test folders must not be packages, whatever target the runner is given.

A tests/updater/__init__.py would hide the real updater package (docs/TESTING.md). The runner checks for one.
That check used to run only when it searched the suite, so a worker given a .py path skipped it. Full runs give
every worker a .py path."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]


def load_runner():
    spec = importlib.util.spec_from_file_location("run_tests_under_test", ROOT / "tools" / "run_tests.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


class FakeSuite:
    """A scratch repository with a game suite: tests/__init__.py, tests/support/__init__.py and
    tests/updater/test_fake_updater.py. The runner's ROOT and SUITES point at it."""

    def __init__(self, runner):
        self.runner = runner

    def __enter__(self):
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)
        tests = self.root / "tests"
        for name in ("__init__.py", "support/__init__.py", "updater/test_fake_updater.py"):
            (tests / name).parent.mkdir(parents=True, exist_ok=True)
            (tests / name).write_text("", encoding="utf-8")
        self.test_file = tests / "updater" / "test_fake_updater.py"
        self._patches = [mock.patch.object(self.runner, "ROOT", self.root),
                         mock.patch.object(self.runner, "SUITES", {"game": (tests, [tests, self.root])})]
        for patch in self._patches:
            patch.start()
        return self

    def __exit__(self, *exc):
        for patch in reversed(self._patches):
            patch.stop()
        self._temp.cleanup()

    def make_package(self):
        (self.root / "tests" / "updater" / "__init__.py").write_text("", encoding="utf-8")


class PackageGuardTests(unittest.TestCase):
    def setUp(self):
        self.runner = load_runner()

    def assert_stops(self, target):
        with self.assertRaises(SystemExit) as stopped:
            self.runner.resolve_target("game", target)
        message = str(stopped.exception)
        self.assertIn("must not exist", message)
        self.assertIn("updater", message)

    def test_relative_path_target_stops_when_a_test_folder_is_a_package(self):
        with FakeSuite(self.runner) as suite:
            suite.make_package()
            self.assert_stops("tests/updater/test_fake_updater.py")
            self.assert_stops("tests\\updater\\test_fake_updater.py")

    def test_absolute_path_target_stops_when_a_test_folder_is_a_package(self):
        with FakeSuite(self.runner) as suite:
            suite.make_package()
            self.assert_stops(str(suite.test_file))

    def test_name_target_and_discovery_stop_when_a_test_folder_is_a_package(self):
        with FakeSuite(self.runner) as suite:
            suite.make_package()
            self.assert_stops("test_fake_updater")
            self.assert_stops("test_fake_updater.SomeTests.test_x")
            with self.assertRaises(SystemExit):
                self.runner.discover("game")

    def test_suite_root_and_helper_folder_may_have_one(self):
        with FakeSuite(self.runner) as suite:
            self.assertEqual(self.runner.discover("game"), [suite.test_file])
            path, wanted = self.runner.resolve_target("game", "tests/updater/test_fake_updater.py")
            self.assertEqual((path, wanted), (suite.test_file.resolve(), "test_fake_updater"))
            path, wanted = self.runner.resolve_target("game", "test_fake_updater.SomeTests")
            self.assertEqual((path, wanted), (suite.test_file, "test_fake_updater.SomeTests"))

    def test_the_real_suites_pass_the_guard(self):
        for suite in self.runner.SUITES:
            with self.subTest(suite=suite):
                self.assertTrue(self.runner.discover(suite))


if __name__ == "__main__":
    unittest.main()
