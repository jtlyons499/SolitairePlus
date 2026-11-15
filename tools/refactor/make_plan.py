"""Build a move.py plan for one phase from screen -> module assignments.

    python tools/refactor/make_plan.py SPEC.json OUT_PLAN.json

SPEC.json:
    {"modules": {
        "solitaireplus/menus/options.py": {
            "doc": "Options screen.",
            "screens": ["options"],                  # screen slugs: their loop_* functions + exclusive helpers
            "names": ["app_settings", "apply_saved_app_settings"],   # extra names (+ their exclusive helpers)
            "statements": []                          # bare start-up statements, by first line
        }, ...},
     "keep": ["get_profile_avatar"]}                  # optional: names that stay in legacy.py even when
                                                      # every legacy user moves (shared with moved modules)

A screen module with exactly one screen gets the loop_* functions renamed to handle_event / draw /
late_update / enter / leave. Helpers are added when every user of a helper moves to the same module
(computed with tools/refactor/areas.py's use graph, repeated until nothing changes). A legacy name that
another module already reaches as ``legacy.<name>`` is shared and never added as a helper (name it
explicitly to move it).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from refactor import areas  # noqa: E402

PREFIX_RENAMES = {"loop_event_": "handle_event", "loop_draw_": "draw", "loop_late_": "late_update",
                  "loop_enter_": "enter", "loop_leave_": "leave"}


def external_names(top_names) -> set:
    """Legacy top-level names that other solitaireplus modules use as legacy.<name>."""
    found = set()
    for path in (ROOT / "solitaireplus").rglob("*.py"):
        if path != areas.LEGACY and "__pycache__" not in path.parts:
            found |= set(re.findall(r"\blegacy\.([A-Za-z_]\w*)", path.read_text(encoding="utf-8")))
    return found & set(top_names)


def build(spec: dict) -> dict:
    top_names, users = areas.analyse(areas.LEGACY.read_text(encoding="utf-8"))
    for name in external_names(top_names):
        users[name].add("<other module>")      # a user outside legacy.py: shared, not an exclusive helper
    by_screen = areas.assign(top_names, users, by_screen=True)
    keep = set(spec.get("keep", []))
    target_of: dict[str, str] = {}
    for target, entry in spec["modules"].items():
        for slug in entry.get("screens", []):
            for name, group in by_screen.items():
                if group == slug and name not in keep:
                    target_of[name] = target
        for name in entry.get("names", []):
            if name not in top_names:
                raise SystemExit(f"{name}: not a top-level name of legacy.py")
            target_of[name] = target
    # exclusive helpers of explicit names
    changed = True
    while changed:
        changed = False
        for name in top_names:
            if name in target_of or name in keep:
                continue
            user_set = users.get(name, set())
            if not user_set or "<module>" in user_set:
                continue
            owners = {target_of.get(user) for user in user_set}
            if len(owners) == 1 and None not in owners:
                target_of[name] = owners.pop()
                changed = True
    moves = []
    for target, entry in spec["modules"].items():
        names = sorted(n for n, t in target_of.items() if t == target)
        screens = entry.get("screens", [])
        renames = {}
        if len(screens) == 1:
            for prefix, new in PREFIX_RENAMES.items():
                if prefix + screens[0] in names:
                    renames[prefix + screens[0]] = new
        moves.append({"target": target, "doc": entry.get("doc", ""), "names": names, "renames": renames,
                      "screens": ["STATE_" + s.upper() for s in screens], "statements": entry.get("statements", [])})
    return {"moves": moves}


def main(argv) -> int:
    spec = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    plan = build(spec)
    Path(argv[1]).write_text(json.dumps(plan, indent=1), encoding="utf-8")
    for move in plan["moves"]:
        print(f"  {len(move['names']):4d} names -> {move['target']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
