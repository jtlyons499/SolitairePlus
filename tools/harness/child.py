"""One harness run: start a checkout's main.py headless and drive one script.

    python tools/harness/child.py --checkout DIR --kind scene|journey|fixture --name NAME --out DIR

The parent (tools/harness/runner.py) sets the environment: dummy SDL drivers,
PYTHONHASHSEED=0 and a temporary LOCALAPPDATA with the fixture save. Writes
``<out>/<name>.json`` with the result and one PNG per screenshot.
"""
from __future__ import annotations

import argparse
import json
import os
import runpy
import sys
import traceback
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

from harness import scripts, sim  # noqa: E402  (must be imported before sys.path points at the game)


def _patch_save_folder(saves: Path) -> None:
    """From source the game saves into <checkout>/saves; send it to the temporary profile folder."""
    try:
        import runtime_support as module
    except ImportError:
        from solitaireplus.app import runtime_support as module

    def save_directory():
        saves.mkdir(parents=True, exist_ok=True)
        return saves

    module.save_directory = save_directory


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", required=True)
    parser.add_argument("--kind", required=True, choices=sorted(scripts.KINDS))
    parser.add_argument("--name", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    checkout = Path(args.checkout).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    function = scripts.KINDS[args.kind][args.name]
    driver = sim.Driver(args.name, function, out_dir)

    # The game's own folder comes first on the import path; the harness folder goes away.
    sys.path[:] = [str(checkout)] + [p for p in sys.path if Path(p or ".").resolve() not in (TOOLS, TOOLS / "harness")]
    os.chdir(checkout)
    sys.argv = [str(checkout / "main.py")]
    sim.install(driver)
    _patch_save_folder(Path(os.environ["LOCALAPPDATA"]) / "SimpleSolitaire" / "saves")

    try:
        runpy.run_path(str(checkout / "main.py"), run_name="__main__")
        if driver.expect_quit:
            driver.done = True
        elif not driver.done and driver.result["error"] is None:
            driver.result["error"] = f"the game quit after {sim.CLOCK.frame} frames, before the script finished"
    except sim.ScriptDone:
        pass
    except sim.ScriptFailed:
        pass
    except SystemExit as stop:
        driver.result["error"] = f"the game exited (SystemExit {stop.code!r}) at frame {sim.CLOCK.frame}"
    except BaseException:
        driver.result["error"] = f"game error at frame {sim.CLOCK.frame}:\n" + traceback.format_exc()
    driver.result["ok"] = driver.done and driver.result["error"] is None
    (out_dir / f"{args.name}.json").write_text(json.dumps(driver.result, indent=1), encoding="utf-8")
    sys.stdout.flush()
    os._exit(0 if driver.result["ok"] else 1)   # skip pygame/atexit teardown; the process is disposable


if __name__ == "__main__":
    main()
