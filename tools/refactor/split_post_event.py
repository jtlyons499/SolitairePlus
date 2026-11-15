"""Phase 4 pre-step: split the Solitaire part out of legacy.loop_post_event_updates.

    python tools/refactor/split_post_event.py

The first three blocks of loop_post_event_updates (after its docstring) are the Head-to-Head
opponent updates and the Solitaire round completion; they only run while current_state is
PLAYING. They become a function update_solitaire_round(), called at exactly the same place, so
the order of everything in the frame stays the same (the level-up check after them still sees a
level-up queued by a round in the same frame). None of their local variables is used by the
blocks that follow (checked below). move.py then moves update_solitaire_round to the Solitaire
screen module.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import libcst as cst

ROOT = Path(__file__).resolve().parents[2]
LEGACY = ROOT / "solitaireplus" / "legacy.py"
COUNT = 3


def main() -> int:
    source = LEGACY.read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "loop_post_event_updates")
    blocks, rest = function.body[1:1 + COUNT], function.body[1 + COUNT:]
    for block in blocks:
        if not (isinstance(block, ast.If) and "STATE_PLAYING" in ast.unparse(block.test)):
            raise SystemExit(f"unexpected block at line {block.lineno}: {ast.unparse(block.test)[:80]}")
    stored = {n.id for b in blocks for n in ast.walk(b) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    read_later = {n.id for b in rest for n in ast.walk(b) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    if stored & read_later:
        raise SystemExit(f"locals shared with the remaining blocks: {sorted(stored & read_later)}")

    module = cst.parse_module(source)
    body = list(module.body)
    index = next(i for i, s in enumerate(body) if isinstance(s, cst.FunctionDef) and s.name.value == "loop_post_event_updates")
    old = body[index]
    statements = list(old.body.body)
    moved = statements[1:1 + COUNT]
    call = cst.parse_statement("update_solitaire_round()\n")
    new_old = old.with_changes(body=old.body.with_changes(body=[statements[0], call, *statements[1 + COUNT:]]))
    doc = cst.parse_statement('"""Head-to-Head opponent progress and Solitaire round completion (every frame while playing)."""\n')
    new_function = cst.FunctionDef(name=cst.Name("update_solitaire_round"), params=cst.Parameters(),
                                   body=cst.IndentedBlock(body=[doc, *moved]),
                                   leading_lines=[cst.EmptyLine(), cst.EmptyLine()])
    body[index:index + 1] = [new_function, new_old]
    LEGACY.write_text(module.with_changes(body=body).code, encoding="utf-8")
    print(f"update_solitaire_round(): {COUNT} blocks split out of loop_post_event_updates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
