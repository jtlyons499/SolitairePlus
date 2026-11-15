"""Screenshot safety net: render every game screen headless and compare two versions pixel by pixel.

    python tools/screen_harness.py list
    python tools/screen_harness.py compare [--baseline REV] [--scene NAME ...]   # default REV: HEAD
    python tools/screen_harness.py selfcheck [--scene NAME ...]   # render the working tree twice
    python tools/screen_harness.py render [--checkout DIR] [--scene NAME ...]
    python tools/screen_harness.py make-fixture   # rebuild tests/support/fixtures/profile_1.json

`compare` checks out REV in a git worktree (kept under .harness_out/worktrees/), renders every
scene there and in the working tree on this machine, and diffs the pixels. It prints
"IDENTICAL n/n scenes" or lists what differs and writes diff images to .harness_out/scene-diff/.
Baselines are never committed: both sides are rendered on the same machine, so system fonts
cannot cause false differences. Rendered baselines are cached per commit and harness version.

How the game is driven (virtual clock, fixed seeds, scripted input, temporary LOCALAPPDATA)
is described in tools/harness/__init__.py. Scenes live in tools/harness/scenes.py.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import runner  # noqa: E402

KIND = "scene"


def scene_names(selected):
    from harness import scripts
    names = list(scripts.SCENES)
    if not selected:
        return names
    unknown = [name for name in selected if name not in scripts.SCENES]
    if unknown:
        raise SystemExit(f"unknown scene(s): {', '.join(unknown)}. Run 'list' to see them.")
    return list(selected)


def make_fixture() -> int:
    out_dir = runner.OUT_ROOT / "fixture"
    with tempfile.TemporaryDirectory(prefix="harness-fixture-") as temporary:
        out_dir.mkdir(parents=True, exist_ok=True)
        # The fixture script runs with an empty saves folder and saves slot 1 itself, so
        # run it by hand here instead of through run_script (which copies the fixture in).
        import os
        import subprocess
        appdata = runner.prepare_appdata(Path(temporary) / "appdata", with_profile=False)
        command = [sys.executable, str(runner.CHILD), "--checkout", str(runner.ROOT), "--kind", "fixture",
                   "--name", "profile_1", "--out", str(out_dir)]
        done = subprocess.run(command, cwd=runner.ROOT, env=runner.child_env(appdata), capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=runner.CHILD_TIMEOUT)
        result = json.loads((out_dir / "profile_1.json").read_text(encoding="utf-8"))
        if not result["ok"]:
            print(done.stdout + done.stderr)
            print(result["error"])
            return 1
        save = appdata / "SimpleSolitaire" / "saves" / "profile_1.json"
        data = json.loads(save.read_text(encoding="utf-8"))
        runner.FIXTURES.mkdir(parents=True, exist_ok=True)
        target = runner.FIXTURES / "profile_1.json"
        target.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {target.relative_to(runner.ROOT)} ({target.stat().st_size} bytes)")
        _ = os
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    for name in ("compare", "selfcheck", "render"):
        command = sub.add_parser(name)
        command.add_argument("--scene", action="append", default=[])
        command.add_argument("--jobs", type=int, default=runner.DEFAULT_JOBS)
        if name == "selfcheck":
            command.add_argument("--tag", default="", help="separate output folder (for parallel runs)")
        if name == "compare":
            command.add_argument("--baseline", default="HEAD")
            command.add_argument("--no-cache", action="store_true", help="re-render the baseline")
        if name == "render":
            command.add_argument("--checkout", default=str(runner.ROOT))
            command.add_argument("--out", default=str(runner.OUT_ROOT / "scene-renders" / "manual"))
    sub.add_parser("make-fixture")
    args = parser.parse_args(argv)

    if args.command == "list":
        print("\n".join(scene_names([])))
        return 0
    if args.command == "make-fixture":
        return make_fixture()
    names = scene_names(args.scene)
    if args.command == "compare":
        return runner.compare_command(KIND, "scenes", names, args.baseline, args.jobs, not args.no_cache, False)
    if args.command == "selfcheck":
        return runner.selfcheck_command(KIND, "scenes", names, args.jobs, False, args.tag)
    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    results = runner.render_side(Path(args.checkout).resolve(), KIND, names, out, args.jobs, "checkout")
    failed = [name for name, result in results.items() if not result.get("ok")]
    for name in failed:
        print(f"FAILED {name}:\n{results[name].get('error')}\n{results[name].get('output', '')[-1500:]}")
    print(f"{len(names) - len(failed)}/{len(names)} scenes rendered into {out}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
