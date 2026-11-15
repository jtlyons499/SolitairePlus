"""Run every Solitaire+ unit test suite the same way locally and in CI.

    python tools/run_tests.py                     # everything; quarantined tests reported but non-blocking
    python tools/run_tests.py --skip-quarantined  # faster: skip retrying quarantined tests marked HANGS
    python tools/run_tests.py --suite multiplayer # one suite only

How it works (see docs/TESTING.md for the full explanation):
* There are two suites. "game" is tests/ (single-player code). "multiplayer"
  is multiplayer/tests/ and needs multiplayer/ first on the import path,
  because multiplayer/ has its own copies of some modules.
* Each test file runs in its own Python process with a time limit, so a test
  that hangs cannot freeze the whole run.
* Tests listed in tests/KNOWN_FAILURES.txt were already broken before this
  runner existed. They still run with the rest of their file. If they fail,
  they are reported but never fail the run. Entries whose reason starts with
  "HANGS" are left out of their file and tried alone with a short time limit,
  unless you pass --skip-quarantined.
* pygame is initialised (headless) before tests run, like the real game does.
  Some tests rely on that, and used to get it by accident from earlier test files.
* Exit code 0 means every non-quarantined test passed. Anything else means
  the release must stop.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KNOWN_FAILURES = ROOT / "tests" / "KNOWN_FAILURES.txt"

SUITES = {
    # name: (test directory, import path in priority order)
    "game": (ROOT / "tests", [ROOT / "tests", ROOT]),
    "multiplayer": (ROOT / "multiplayer" / "tests",
                    [ROOT / "multiplayer" / "tests", ROOT / "multiplayer", ROOT]),
}

MODULE_TIMEOUT = 300      # seconds per test file
QUARANTINE_TIMEOUT = 30   # seconds per quarantined test


def load_known_failures() -> dict[str, dict[str, str]]:
    """Return {suite: {test_id: reason}} from tests/KNOWN_FAILURES.txt."""
    known: dict[str, dict[str, str]] = {name: {} for name in SUITES}
    if not KNOWN_FAILURES.is_file():
        return known
    for number, raw in enumerate(KNOWN_FAILURES.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        entry, _, reason = line.partition("#")
        suite, sep, test_id = entry.strip().partition(":")
        if not sep or suite not in known or not test_id:
            raise SystemExit(f"{KNOWN_FAILURES.name} line {number} is not 'suite:test.id  # reason': {raw!r}")
        known[suite][test_id.strip()] = reason.strip() or "no reason given"
    return known


def child_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("SDL_VIDEODRIVER", "dummy")   # no real window
    env.setdefault("SDL_AUDIODRIVER", "dummy")   # no real sound device
    env.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop("PYTHONPATH", None)                  # the worker sets sys.path itself
    return env


def run_child(args: list[str], timeout: int) -> tuple[str, dict | None, str]:
    """Run this script as a worker. Returns (status, result, output)."""
    command = [sys.executable, str(Path(__file__).resolve()), *args]
    try:
        done = subprocess.run(command, cwd=ROOT, env=child_env(), capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired as expired:
        output = (expired.stdout or "") + (expired.stderr or "")
        if isinstance(output, bytes):
            output = output.decode("utf-8", "replace")
        return "timeout", None, output
    output = done.stdout + done.stderr
    for line in reversed(done.stdout.splitlines()):
        if line.startswith("@@RESULT "):
            return "finished", json.loads(line[len("@@RESULT "):]), output
    return "crashed", None, output


# ---------------------------------------------------------------- worker side

def iter_tests(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from iter_tests(item)
        else:
            yield item


def worker(suite_name: str, target: str, skip_ids: list[str]) -> None:
    _, paths = SUITES[suite_name]
    for path in reversed(paths):
        sys.path.insert(0, str(path))
    os.chdir(ROOT)
    try:
        import pygame
        pygame.init()  # headless thanks to the dummy SDL drivers set in child_env()
    except Exception as error:  # a broken pygame install should still let pure-logic tests run
        print(f"warning: pygame could not be initialised: {error}", file=sys.stderr)
    loaded = unittest.defaultTestLoader.loadTestsFromName(target)
    selected = unittest.TestSuite(t for t in iter_tests(loaded) if t.id() not in set(skip_ids))
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=1).run(selected)
    summary = {
        "ran": result.testsRun,
        "failed": [test.id() for test, _ in result.failures + result.errors],
        "unexpected_success": [test.id() for test in result.unexpectedSuccesses],
    }
    sys.stdout.flush()
    print("@@RESULT " + json.dumps(summary), flush=True)


# ---------------------------------------------------------------- runner side

def run_suite(name: str, known: dict[str, str], skip_quarantined: bool) -> tuple[bool, list[str]]:
    directory, _ = SUITES[name]
    problems: list[str] = []
    report: list[str] = []
    print(f"\n=== Suite '{name}' ({directory.relative_to(ROOT)}) ===", flush=True)
    hanging = {test_id for test_id, reason in known.items() if reason.upper().startswith("HANGS")}
    for test_file in sorted(directory.glob("test_*.py")):
        module = test_file.stem
        skip = sorted(test_id for test_id in hanging if test_id.startswith(module + "."))
        args = ["--worker", name, module, *(f"--skip={test_id}" for test_id in skip)]
        started = time.monotonic()
        status, result, output = run_child(args, MODULE_TIMEOUT)
        seconds = time.monotonic() - started
        if status == "timeout":
            problems.append(f"{name}:{module} did not finish within {MODULE_TIMEOUT}s (a test is hanging)")
            print(f"  TIMEOUT  {module} ({seconds:.0f}s)")
            continue
        if status == "crashed":
            problems.append(f"{name}:{module} crashed before reporting results")
            print(f"  CRASH    {module}\n" + _indent(output[-3000:]))
            continue
        failed = set(result["failed"])
        new_failures = sorted(failed - set(known))
        for test_id in sorted(t for t in known if t.startswith(module + ".") and t not in hanging):
            if test_id in failed:
                report.append(f"  still fails {name}:{test_id}  ({known[test_id]})")
            else:
                report.append(f"  NOW PASSES  {name}:{test_id} -> remove it from tests/KNOWN_FAILURES.txt")
        if new_failures:
            problems += [f"{name}:{test_id}" for test_id in new_failures]
            print(f"  FAIL     {module}: {len(new_failures)} new failure(s) of {result['ran']} tests ({seconds:.0f}s)\n"
                  + _indent(output[-6000:]))
        else:
            quarantined = len(failed)
            note = f", {quarantined} quarantined failure(s)" if quarantined else ""
            print(f"  ok       {module}: {result['ran']} tests{note} ({seconds:.0f}s)", flush=True)

    for test_id in sorted(hanging):
        if skip_quarantined:
            report.append(f"  not run     {name}:{test_id}  ({known[test_id]})")
            continue
        status, result, _ = run_child(["--worker", name, test_id], QUARANTINE_TIMEOUT)
        if status == "finished" and result["ran"] and not result["failed"]:
            report.append(f"  NOW PASSES  {name}:{test_id} -> remove it from tests/KNOWN_FAILURES.txt")
        else:
            label = {"timeout": "still hangs", "crashed": "still crashes"}.get(status, "still fails")
            report.append(f"  {label:<11} {name}:{test_id}  ({known[test_id]})")
    if known:
        print(f"  Quarantined (non-blocking, see tests/KNOWN_FAILURES.txt):")
        print("\n".join(report))
    return not problems, problems


def _indent(text: str) -> str:
    return "\n".join("      " + line for line in text.rstrip().splitlines())


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--suite", choices=sorted(SUITES), action="append",
                        help="run only this suite (repeatable); default: all")
    parser.add_argument("--skip-quarantined", action="store_true",
                        help="do not retry quarantined tests marked HANGS (they are already left out of their files)")
    parser.add_argument("--worker", nargs=2, metavar=("SUITE", "TARGET"), help=argparse.SUPPRESS)
    parser.add_argument("--skip", action="append", default=[], help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.worker:
        worker(args.worker[0], args.worker[1], args.skip)
        return 0

    known = load_known_failures()
    all_problems: list[str] = []
    for name in args.suite or list(SUITES):
        _, problems = run_suite(name, known[name], args.skip_quarantined)
        all_problems += problems

    print("\n=== Result ===")
    if all_problems:
        print("FAILED - these must be fixed before releasing:")
        for problem in all_problems:
            print("  - " + problem)
        print("Read docs/TESTING.md for how to investigate a failure.")
        return 1
    print("PASSED - all non-quarantined tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
