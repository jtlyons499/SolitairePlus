"""Scripted playthroughs: replay player journeys headless and compare their checkpoints.

    python tools/replay.py list
    python tools/replay.py compare [--baseline REV] [--journey NAME ...]   # default REV: HEAD
    python tools/replay.py selfcheck [--journey NAME ...]   # run the working tree twice
    python tools/replay.py run [--checkout DIR] [--journey NAME ...]

Each journey (tools/harness/journeys.py) is a list of inputs plus frame counts, run by the
same deterministic runner as tools/screen_harness.py. At checkpoints it records
current_state, cash, XP, level, rating, career day and fans, plus a screenshot. `compare`
runs every journey at REV (in a git worktree) and in the working tree and prints
"IDENTICAL n/n journeys" only when every checkpoint value and screenshot matches.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import runner  # noqa: E402

KIND = "journey"


def journey_names(selected):
    from harness import scripts
    names = list(scripts.JOURNEYS)
    if not selected:
        return names
    unknown = [name for name in selected if name not in scripts.JOURNEYS]
    if unknown:
        raise SystemExit(f"unknown journey(s): {', '.join(unknown)}. Run 'list' to see them.")
    return list(selected)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    for name in ("compare", "selfcheck", "run"):
        command = sub.add_parser(name)
        command.add_argument("--journey", action="append", default=[])
        command.add_argument("--jobs", type=int, default=runner.DEFAULT_JOBS)
        if name == "selfcheck":
            command.add_argument("--tag", default="", help="separate output folder (for parallel runs)")
        if name == "compare":
            command.add_argument("--baseline", default="HEAD")
            command.add_argument("--no-cache", action="store_true", help="re-run the baseline")
        if name == "run":
            command.add_argument("--checkout", default=str(runner.ROOT))
            command.add_argument("--out", default=str(runner.OUT_ROOT / "journey-renders" / "manual"))
    args = parser.parse_args(argv)

    if args.command == "list":
        print("\n".join(journey_names([])))
        return 0
    names = journey_names(args.journey)
    if args.command == "compare":
        return runner.compare_command(KIND, "journeys", names, args.baseline, args.jobs, not args.no_cache, True)
    if args.command == "selfcheck":
        return runner.selfcheck_command(KIND, "journeys", names, args.jobs, True, args.tag)
    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    results = runner.render_side(Path(args.checkout).resolve(), KIND, names, out, args.jobs, "checkout")
    failed = [name for name, result in results.items() if not result.get("ok")]
    for name, result in results.items():
        print(f"--- {name}")
        for checkpoint in result.get("checkpoints", []):
            print(f"    {checkpoint['label']:<24} frame {checkpoint['frame']:<5} {json.dumps(checkpoint['values'])}")
    for name in failed:
        print(f"FAILED {name}:\n{results[name].get('error')}\n{results[name].get('output', '')[-1500:]}")
    print(f"{len(names) - len(failed)}/{len(names)} journeys ran; output in {out}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
