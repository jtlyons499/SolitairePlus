"""Move top-level definitions out of solitaireplus/legacy.py into an area module (Phases 3-10).

    python tools/refactor/move.py PLAN.json [--dry-run]

PLAN.json:
    {"moves": [
        {"target": "solitaireplus/games/casino/roulette_screen.py",
         "doc": "Roulette screen (moved out of legacy.py).",
         "names": ["draw_roulette_table", "ROULETTE_BET_RECT", "loop_event_roulette", "loop_draw_roulette"],
         "renames": {"loop_event_roulette": "handle_event", "loop_draw_roulette": "draw"},
         "screens": ["STATE_ROULETTE"]}
    ]}

For each move:
* every top-level statement of legacy.py that binds one of `names` (a def, or an assignment whose
  targets are all listed) is cut from legacy.py and appended, in order, to the target module
  (created if needed; an existing target keeps its code and gets the new statements appended);
* references are rewritten everywhere in solitaireplus/: inside the target, moved names are bare
  and remaining legacy names become ``legacy.name``; inside legacy.py and every other module,
  moved names become ``<alias>.name`` (and ``legacy.name`` attribute uses become ``<alias>.name``);
* imports the moved code needs are copied from legacy.py; references back to legacy (and to other
  modules that are not plain-importable at the top) go through LazyModule proxies;
* legacy.py imports the target at the place of the first moved statement that is not a def, so
  start-up code still runs in the old order (the tool refuses a move whose statements need legacy
  names that are only defined later);
* `screens`: the SCREENS registry in app/loop.py points those screens at the target module, which
  must then define handle_event/draw (and optionally late_update, update, enter, leave, DRAWS_LATE).
Prints every name it could not place; nothing is guessed.
"""
from __future__ import annotations

import argparse
import ast
import collections
import json
import re
import sys
from pathlib import Path

import libcst as cst
from libcst.metadata import (ExpressionContext, ExpressionContextProvider, GlobalScope, MetadataWrapper,
                             ParentNodeProvider, PositionProvider, ScopeProvider)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from refactor.analysis import is_declared_global, refers_to_global  # noqa: E402

PACKAGE_DIR = ROOT / "solitaireplus"
LEGACY = PACKAGE_DIR / "legacy.py"
LOOP = PACKAGE_DIR / "app" / "loop.py"
# modules that are safe to import at the top of any module (no start-up side effects)
PLAIN_IMPORTS = {"state", "state_names", "paths", "lazy"}


def module_name(path: Path) -> str:
    return ".".join(path.relative_to(ROOT).with_suffix("").parts)


def alias_for(dotted: str) -> str:
    return dotted.rsplit(".", 1)[1]


class LegacyIndex:
    """What legacy.py binds at top level, and where each name's uses are global."""

    def __init__(self, source: str):
        self.source = source
        self.wrapper = MetadataWrapper(cst.parse_module(source))
        self.module = self.wrapper.module
        self.positions = self.wrapper.resolve(PositionProvider)
        self.parents = self.wrapper.resolve(ParentNodeProvider)
        self.scopes = self.wrapper.resolve(ScopeProvider)
        self.contexts = self.wrapper.resolve(ExpressionContextProvider)
        self.body = list(self.module.body)
        self.bound_by: dict[int, set] = {}          # statement id -> names it binds
        self.binder: dict[str, list] = collections.defaultdict(list)
        self.import_names: dict[str, cst.CSTNode] = {}
        for statement in self.body:
            names = self._bound_names(statement)
            self.bound_by[id(statement)] = names
            for name in names:
                self.binder[name].append(statement)

    def code(self, node) -> str:
        return self.module.code_for_node(node)

    def _bound_names(self, statement) -> set:
        names = set()
        if isinstance(statement, (cst.FunctionDef, cst.ClassDef)):
            return {statement.name.value}
        if isinstance(statement, cst.SimpleStatementLine):
            for small in statement.body:
                if isinstance(small, (cst.Import, cst.ImportFrom)):
                    if isinstance(small, cst.ImportFrom) and isinstance(small.names, cst.ImportStar):
                        continue
                    for alias in small.names:
                        bound = alias.asname.name.value if alias.asname else self.code(alias.name).split(".")[0]
                        names.add(bound)
                        self.import_names.setdefault(bound, statement)
                elif isinstance(small, cst.Assign):
                    for target in small.targets:
                        names |= self._target_names(target.target)
                elif isinstance(small, (cst.AnnAssign, cst.AugAssign)):
                    names |= self._target_names(small.target)
        return names

    def _target_names(self, target) -> set:
        if isinstance(target, cst.Name):
            return {target.value}
        if isinstance(target, (cst.Tuple, cst.List)):
            out = set()
            for element in target.elements:
                out |= self._target_names(element.value)
            return out
        return set()      # attribute/subscript targets (state.x = ...) bind nothing here


def is_def(statement) -> bool:
    return isinstance(statement, (cst.FunctionDef, cst.ClassDef))


class TargetRewriter(cst.CSTTransformer):
    """Rewrites the moved statements (inside legacy's tree) for their new module."""
    METADATA_DEPENDENCIES = (ScopeProvider, ExpressionContextProvider, ParentNodeProvider)

    def __init__(self, index: LegacyIndex, moved: set, renames: dict, remaining: set, statements: set):
        super().__init__()
        self.index = index
        self.moved = moved
        self.renames = renames
        self.remaining = remaining           # legacy top-level names that stay in legacy
        self.statements = statements         # ids of the top-level statements moving to this target
        self.used_imports: set[str] = set()
        self.uses_legacy = False
        self.active = 0

    def on_visit(self, node):
        if id(node) in self.statements:
            self.active += 1
        return super().on_visit(node)

    def on_leave(self, original, updated):
        result = super().on_leave(original, updated)
        if id(original) in self.statements:
            self.active -= 1
        return result

    def leave_Name(self, original, updated):
        if not self.active:
            return updated
        context = self.get_metadata(ExpressionContextProvider, original, None)
        parent = self.get_metadata(ParentNodeProvider, original)
        if isinstance(parent, (cst.FunctionDef, cst.ClassDef)):
            if parent.name is original and original.value in self.renames:
                return updated.with_changes(value=self.renames[original.value])
            return updated
        if context is None:
            return updated
        scope = self.get_metadata(ScopeProvider, original, None)
        if scope is None:
            return updated
        if isinstance(scope, GlobalScope):
            is_global = True
        elif context is ExpressionContext.LOAD:
            is_global = refers_to_global(scope, original)
        else:
            is_global = is_declared_global(scope, original.value)
        if not is_global:
            return updated
        name = original.value
        if name in self.moved:
            return updated.with_changes(value=self.renames.get(name, name))
        if name in self.index.import_names:
            self.used_imports.add(name)
            return updated
        if name in self.remaining:
            self.uses_legacy = True
            return cst.Attribute(value=cst.Name("legacy"), attr=cst.Name(name))
        return updated     # builtins / unknown


class ReferenceRewriter(cst.CSTTransformer):
    """In legacy.py's remaining code: bare uses of moved names -> alias.name."""
    METADATA_DEPENDENCIES = (ScopeProvider, ExpressionContextProvider, ParentNodeProvider)

    def __init__(self, owner_alias: dict, renames: dict, skip: set):
        super().__init__()
        self.owner_alias = owner_alias       # moved name -> alias of its new module
        self.renames = renames               # moved name -> new name (for loop_* functions)
        self.skip = skip                     # ids of statements being moved (left untouched here)
        self.used: set[str] = set()
        self._skipping = 0

    def visit_SimpleStatementLine(self, node):
        if id(node) in self.skip:
            self._skipping += 1
        return True

    def leave_SimpleStatementLine(self, original, updated):
        if id(original) in self.skip:
            self._skipping -= 1
        return updated

    def visit_FunctionDef(self, node):
        if id(node) in self.skip:
            self._skipping += 1
        return True

    def leave_FunctionDef(self, original, updated):
        if id(original) in self.skip:
            self._skipping -= 1
        return updated

    def leave_Name(self, original, updated):
        if self._skipping:
            return updated
        name = original.value
        if name not in self.owner_alias:
            return updated
        context = self.get_metadata(ExpressionContextProvider, original, None)
        parent = self.get_metadata(ParentNodeProvider, original)
        if context is None or isinstance(parent, (cst.FunctionDef, cst.ClassDef)):
            return updated
        scope = self.get_metadata(ScopeProvider, original, None)
        if scope is None:
            return updated
        if not isinstance(scope, GlobalScope):
            if context is ExpressionContext.LOAD and not refers_to_global(scope, original):
                return updated
            if context is not ExpressionContext.LOAD and not is_declared_global(scope, name):
                return updated
        alias = self.owner_alias[name]
        self.used.add(alias)
        return cst.Attribute(value=cst.Name(alias), attr=cst.Name(self.renames.get(name, name)))


def rewrite_attribute_uses(code: str, moved_to: dict, renames: dict, this_module: str) -> tuple[str, set]:
    """In other modules: `legacy.NAME` -> `alias.NAME` for moved names (alias per moved_to)."""
    used = set()

    class Rewriter(cst.CSTTransformer):
        def leave_Attribute(self, original, updated):
            if (isinstance(updated.value, cst.Name) and updated.value.value == "legacy"
                    and updated.attr.value in moved_to):
                target = moved_to[updated.attr.value]
                if target == this_module:
                    return cst.Name(renames.get(updated.attr.value, updated.attr.value))
                alias = alias_for(target)
                used.add(target)
                return updated.with_changes(value=cst.Name(alias), attr=cst.Name(renames.get(updated.attr.value, updated.attr.value)))
            return updated

    new = cst.parse_module(code).visit(Rewriter()).code
    return new, used


def import_copies(index: LegacyIndex, names: set) -> list[str]:
    lines, done = [], set()
    for statement in index.body:
        if id(statement) in done or not isinstance(statement, cst.SimpleStatementLine):
            continue
        tree = ast.parse(index.code(statement).strip())
        for node in tree.body:
            if isinstance(node, ast.Import):
                keep = [a for a in node.names if (a.asname or a.name.split(".")[0]) in names]
                if keep:
                    lines.append(ast.unparse(ast.Import(names=keep)))
                    done.add(id(statement))
            elif isinstance(node, ast.ImportFrom):
                keep = [a for a in node.names if (a.asname or a.name) in names]
                if keep:
                    lines.append(ast.unparse(ast.ImportFrom(module=node.module, names=keep, level=node.level)))
                    done.add(id(statement))
    return lines


def insert_import(code: str, line: str) -> str:
    """Add an import line after the module docstring / existing top imports, if missing."""
    if line in code.splitlines():
        return code
    module = cst.parse_module(code)
    body = list(module.body)
    index = 0
    for i, statement in enumerate(body):
        if isinstance(statement, cst.SimpleStatementLine) and statement.body and (
                isinstance(statement.body[0], (cst.Import, cst.ImportFrom))
                or (i == 0 and isinstance(statement.body[0], cst.Expr)
                    and isinstance(statement.body[0].value, (cst.SimpleString, cst.ConcatenatedString)))):
            index = i + 1
            continue
        break
    body.insert(index, cst.parse_statement(line + "\n"))
    return module.with_changes(body=body).code


def apply_plan(plan: dict, dry_run: bool, out_dir: Path | None = None) -> int:
    legacy_source = LEGACY.read_text(encoding="utf-8")
    index = LegacyIndex(legacy_source)
    moved_to: dict[str, str] = {}          # name -> target dotted module
    renames: dict[str, str] = {}
    problems: list[str] = []
    statements_for: dict[str, list] = collections.defaultdict(list)
    moving_ids: set[int] = set()
    for move in plan["moves"]:
        target = module_name(ROOT / move["target"])
        for name in move["names"]:
            if name not in index.binder:
                problems.append(f"{name}: not a top-level name of legacy.py")
                continue
            moved_to[name] = target
        renames.update(move.get("renames", {}))
    # bare start-up statements (loops, calls) chosen by the start of their first code line
    for move in plan["moves"]:
        target = module_name(ROOT / move["target"])
        for prefix in move.get("statements", []):
            matches = [s for s in index.body if index.code(s).lstrip().startswith(prefix)
                       or _first_code_line(index.code(s)).startswith(prefix)]
            if len(matches) != 1:
                problems.append(f"statement starting {prefix!r}: found {len(matches)}, expected 1")
                continue
            statement = matches[0]
            statements_for[target].append(statement)
            moving_ids.add(id(statement))
            for name in index.bound_by[id(statement)]:
                moved_to.setdefault(name, target)
    for statement in index.body:
        names = index.bound_by[id(statement)]
        if not names or id(statement) in moving_ids:
            continue
        targets = {moved_to.get(n) for n in names}
        if targets == {None}:
            continue
        if None in targets or len(targets) > 1:
            problems.append(f"statement at line {index.positions[statement].start.line} binds "
                            f"{sorted(names)}; list all of them for one target")
            continue
        if isinstance(statement, cst.SimpleStatementLine) and any(
                isinstance(s, (cst.Import, cst.ImportFrom)) for s in statement.body):
            problems.append(f"import statement at line {index.positions[statement].start.line} cannot be moved")
            continue
        statements_for[targets.pop()].append(statement)
        moving_ids.add(id(statement))
    position = {id(s): i for i, s in enumerate(index.body)}
    for target in statements_for:
        statements_for[target].sort(key=lambda s: position[id(s)])   # keep the old order
    for name, target in moved_to.items():
        if name not in index.binder:
            continue
        if len(index.binder[name]) > 1 and not all(id(s) in moving_ids for s in index.binder[name]):
            problems.append(f"{name} is bound by several statements; not all of them move")
    if problems:
        print("\n".join("PROBLEM: " + p for p in problems))
        return 1

    remaining = {name for name in index.binder if name not in moved_to}
    # 1. target code (rewritten inside legacy's tree so scope analysis is exact)
    targets_code: dict[str, dict] = {}
    for move in plan["moves"]:
        target = module_name(ROOT / move["target"])
        moved_here = {n for n, t in moved_to.items() if t == target}
        rewriter = TargetRewriter(index, moved_here, move.get("renames", {}),
                                  remaining | {n for n, t in moved_to.items() if t != target},
                                  {id(s) for s in statements_for[target]})
        new_module = index.wrapper.visit(rewriter)
        new_body = list(new_module.body)
        pieces = [new_module.code_for_node(new_body[index.body.index(s)]) for s in statements_for[target]]
        # names moved to OTHER targets in this same plan: refer to them via their module
        other = {n: t for n, t in moved_to.items() if t != target}
        text = "".join(pieces)
        if other:
            text, other_used = rewrite_attribute_uses(text, other, renames, target)
        else:
            other_used = set()
        targets_code[target] = {"move": move, "code": text, "imports": rewriter.used_imports,
                                "uses_legacy": rewriter.uses_legacy, "others": other_used}

    # 1b. start-up order check: moved start-up statements run when legacy imports the target (at the
    # first moved non-def statement), so every legacy name they use at module level must exist by then
    first_index = {}
    for target, statements in statements_for.items():
        non_defs = [position[id(s)] for s in statements if not is_def(s)]
        first_index[target] = min(non_defs) if non_defs else None
    late_problems = []
    for target, info in targets_code.items():
        if first_index[target] is None:
            continue
        for node in _module_level_nodes(ast.parse(info["code"])):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "legacy":
                binders = index.binder.get(node.attr, [])
                if binders and min(position[id(s)] for s in binders) > first_index[target]:
                    late_problems.append(f"{target}: start-up code uses legacy.{node.attr}, defined later in legacy.py")
    if late_problems:
        print("\n".join("PROBLEM: " + p for p in sorted(set(late_problems))))
        return 1

    # 2. legacy without the moved statements, references rewritten
    owner_alias = {name: alias_for(target) for name, target in moved_to.items()}
    ref = ReferenceRewriter(owner_alias, renames, moving_ids)
    new_legacy_module = index.wrapper.visit(ref)
    first_position: dict[str, int] = {}
    for target, statements in statements_for.items():
        non_defs = [index.body.index(s) for s in statements if not is_def(s)]
        first_position[target] = min(non_defs) if non_defs else None
    out_body = []
    new_body = list(new_legacy_module.body)
    imported_targets = set()
    for position, statement in enumerate(index.body):
        for target, first in first_position.items():
            if first == position:
                package, leaf = target.rsplit(".", 1)
                out_body.append(cst.parse_statement(
                    f"from {package} import {leaf}  # start-up code of this module runs here, as before\n"))
                imported_targets.add(target)
        if id(statement) in moving_ids:
            continue
        out_body.append(new_body[position])
    legacy_text = new_legacy_module.with_changes(body=out_body).code
    for target in sorted(set(moved_to.values()) - imported_targets):
        if alias_for(target) in ref.used:
            package, leaf = target.rsplit(".", 1)
            legacy_text = insert_import(legacy_text, f"from {package} import {leaf}")

    # 3. other modules: legacy.NAME -> alias.NAME
    others: dict[Path, str] = {}
    for path in sorted(PACKAGE_DIR.rglob("*.py")):
        if path == LEGACY or "__pycache__" in path.parts:
            continue
        code = path.read_text(encoding="utf-8")
        if "legacy." not in code:
            continue
        this_module = module_name(path)
        new, used = rewrite_attribute_uses(code, moved_to, renames, this_module)
        if new != code:
            for target in sorted(used):
                alias = alias_for(target)
                if path == LOOP:
                    new = insert_import(new, f"from {target.rsplit('.', 1)[0]} import {alias}")
                elif f"{alias} = lazy(" not in new:
                    new = insert_import(new, "from solitaireplus.app.lazy import lazy")
                    new = insert_import(new, f'{alias} = lazy("{target}")')
            others[path] = new

    # 4. write target modules
    writes: dict[Path, str] = {LEGACY: legacy_text, **others}
    for target, info in targets_code.items():
        path = ROOT / (target.replace(".", "/") + ".py")
        existing = path.read_text(encoding="utf-8") if path.is_file() else f'"""{info["move"].get("doc", "")}"""\n'
        if path in writes:
            existing = writes[path]
        head = []
        plain, late, own_aliases = split_imports(index, info["imports"], target)
        head += plain
        if late:
            head.append("from solitaireplus.app.lazy import lazy")
            head += [f'{alias} = lazy("{dotted}")' for alias, dotted in sorted(late.items())]
        if info["uses_legacy"]:
            head.append("from solitaireplus.app.lazy import lazy")
            head.append('legacy = lazy("solitaireplus.legacy")')
        for other_target in sorted(info["others"]):
            head.append("from solitaireplus.app.lazy import lazy")
            head.append(f'{alias_for(other_target)} = lazy("{other_target}")')
        text = existing
        for line in head:
            text = insert_import(text, line)
        own = ("".join(line + "\n" for line in own_aliases) + "\n") if own_aliases else ""
        text = text.rstrip("\n") + "\n\n\n" + own + info["code"].lstrip("\n")
        writes[path] = text

    # 5. registry
    loop_text = writes.get(LOOP, LOOP.read_text(encoding="utf-8"))
    for move in plan["moves"]:
        target = module_name(ROOT / move["target"])
        # a module with one screen renames loop_event_<screen> to handle_event etc. and is registered
        # by module name; a module holding several screens keeps the loop_* names ("module:screen")
        single = "handle_event" in move.get("renames", {}).values() or "draw" in move.get("renames", {}).values()
        for screen in move.get("screens", []):
            pattern = re.compile(rf'(    state_names\.{screen}: )"[^"]*"')
            if not pattern.search(loop_text):
                print(f"PROBLEM: {screen} is not in the SCREENS registry")
                return 1
            entry = target if single else f"{target}:{screen[len('STATE_'):].lower()}"
            loop_text = pattern.sub(lambda match: f'{match.group(1)}"{entry}"', loop_text)
            drawn_late = re.search(r"DRAWN_LATE = \{([^}]*)\}", loop_text)
            if single and drawn_late and f"state_names.{screen}" in drawn_late.group(1):
                path = ROOT / (target.replace(".", "/") + ".py")
                text = writes[path]
                if "DRAWS_LATE = True" not in text:
                    writes[path] = text.rstrip("\n") + (
                        "\n\n\n# The old loop drew this screen in its second draw chain (see app/loop.py).\n"
                        "DRAWS_LATE = True\n")
    writes[LOOP] = loop_text

    # a module alias must never also be a local name where it is used (state/text lesson of Phase 2)
    aliases = {alias_for(t) for t in set(moved_to.values())}
    conflicts = []
    for path, text in writes.items():
        for problem in _alias_conflicts(text, aliases):
            conflicts.append(f"{path.relative_to(ROOT)}: {problem}")
        # two different modules bound to one alias (games/solitaire/screen vs games/cryptid/screen)
        bound = {}
        for package, name in re.findall(r"^from ([\w.]+) import (\w+)\b", text, re.M):
            bound.setdefault(name, set()).add(f"{package}.{name}")
        for name, dotted in re.findall(r'^(\w+) = lazy\("([\w.]+)"\)', text, re.M):
            bound.setdefault(name, set()).add(dotted)
        for name, modules in bound.items():
            if name in aliases and len(modules) > 1:
                conflicts.append(f"{path.relative_to(ROOT)}: alias '{name}' bound to {sorted(modules)}")
    if conflicts:
        print("\n".join("PROBLEM: " + c for c in conflicts))
        print("Rename the target module (or the local variable) so its alias is unique.")
        return 1

    for path, text in writes.items():
        compile(text, str(path), "exec")
        if out_dir is not None:
            destination = out_dir / path.relative_to(ROOT)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(text, encoding="utf-8")
            print(f"  wrote {destination} ({len(text.splitlines())} lines)")
            continue
        if dry_run:
            print(f"  would write {path.relative_to(ROOT)} ({len(text.splitlines())} lines)")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            print(f"  wrote {path.relative_to(ROOT)} ({len(text.splitlines())} lines)")
    if not dry_run and out_dir is None:
        known = set(json.loads(MOVED_REGISTRY.read_text(encoding="utf-8"))) if MOVED_REGISTRY.is_file() else set()
        known |= {t for t in targets_code if statements_for.get(t) and any(not is_def(s) for s in statements_for[t])}
        MOVED_REGISTRY.write_text(json.dumps(sorted(known), indent=1) + "\n", encoding="utf-8")
    return 0


# Modules with start-up code (or that depend on the start-up order). Moved code refers to them
# through LazyModule proxies, so importing a moved module never runs their code early.
STARTUP_MODULES = {
    "solitaireplus.legacy", "solitaireplus.app.sounds", "solitaireplus.app.fonts", "solitaireplus.app.assets",
    "solitaireplus.app.window", "solitaireplus.app.loop", "solitaireplus.ui.cursors", "solitaireplus.ui.buttons",
    "solitaireplus.ui.text", "solitaireplus.ui.panels", "solitaireplus.ui.backgrounds",
}
MOVED_REGISTRY = ROOT / "tools" / "refactor" / "moved_modules.json"


def startup_modules() -> set:
    extra = set(json.loads(MOVED_REGISTRY.read_text(encoding="utf-8"))) if MOVED_REGISTRY.is_file() else set()
    return STARTUP_MODULES | extra


def split_imports(index: LegacyIndex, names: set, target: str = "") -> tuple[list, dict, list]:
    """legacy.py's imports of `names`: plain import lines, {alias: module} to reach lazily, and
    "alias = name" lines for names legacy imported from the target module itself."""
    plain, late, own = [], {}, []
    startup = startup_modules()
    for name in sorted(names):
        statement = index.import_names.get(name)
        if statement is None:
            continue
        for node in ast.parse(index.code(statement).strip()).body:
            if isinstance(node, ast.ImportFrom):
                for item in node.names:
                    if (item.asname or item.name) != name:
                        continue
                    dotted = f"{node.module}.{item.name}"
                    if node.module == target:
                        if item.asname and item.asname != item.name:
                            own.append(f"{item.asname} = {item.name}")
                        continue
                    if dotted in startup:
                        late[name] = dotted
                    else:
                        plain.append(ast.unparse(ast.ImportFrom(module=node.module, names=[item], level=0)))
            elif isinstance(node, ast.Import):
                for item in node.names:
                    if (item.asname or item.name.split(".")[0]) == name:
                        plain.append(ast.unparse(ast.Import(names=[item])))
    return plain, late, own


def _alias_conflicts(text: str, aliases: set) -> list:
    """Aliases used as `alias.x` in this module that some function scope binds as a local."""
    import symtable
    used = set(re.findall(r"\b([A-Za-z_][A-Za-z_0-9]*)\.[A-Za-z_]", text)) & aliases
    if not used:
        return []
    # only aliases this module binds at module level (imports / lazy aliases) can clash; a
    # module that merely has a local of that name (loop.run's `screen`) imports no such alias
    top = symtable.symtable(text, "<module>", "exec")
    used &= {symbol.get_name() for symbol in top.get_symbols()
             if symbol.is_imported() or symbol.is_assigned()}
    if not used:
        return []
    problems = []

    def walk(table):
        if table.get_type() == "function":
            for symbol in table.get_symbols():
                if symbol.get_name() in used and (symbol.is_local() or symbol.is_parameter()) \
                        and not symbol.is_global():
                    problems.append(f"'{symbol.get_name()}' is a local name in {table.get_name()}() "
                                    f"(line {table.get_lineno()})")
        for child in table.get_children():
            walk(child)

    walk(symtable.symtable(text, "<moved>", "exec"))
    return problems


def _module_level_nodes(tree):
    """AST nodes that run when the module is imported (not inside def/lambda/class bodies)."""
    stack = list(tree.body)
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # only decorators and default values run at import time (class bodies do too)
            stack.extend(node.decorator_list)
            if isinstance(node, ast.ClassDef):
                stack.extend(node.body)
            else:
                stack.extend(node.args.defaults + [d for d in node.args.kw_defaults if d])
            continue
        if isinstance(node, ast.Lambda):
            stack.extend(node.args.defaults + [d for d in node.args.kw_defaults if d])
            continue
        yield node
        stack.extend(ast.iter_child_nodes(node))


def _first_code_line(code: str) -> str:
    for line in code.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return ""


def _legacy_import_of(index: LegacyIndex, alias: str):
    """The line legacy.py uses to import module alias `alias` (e.g. 'from solitaireplus.app import fonts')."""
    statement = index.import_names.get(alias)
    if statement is None:
        return None
    tree = ast.parse(index.code(statement).strip())
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            for item in node.names:
                if (item.asname or item.name) == alias:
                    return ast.unparse(ast.ImportFrom(module=node.module, names=[item], level=0))
        if isinstance(node, ast.Import):
            for item in node.names:
                if (item.asname or item.name.split(".")[0]) == alias:
                    return ast.unparse(ast.Import(names=[item]))
    return None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plan")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out", help="write the result under this folder instead of the repository")
    args = parser.parse_args(argv)
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    return apply_plan(plan, args.dry_run, Path(args.out) if args.out else None)


if __name__ == "__main__":
    sys.exit(main())
