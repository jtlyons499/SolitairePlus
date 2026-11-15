"""Phase 2: take the engine out of main.py.

    python tools/refactor/phase2_engine.py --out DIR    # write the new files into DIR (dry run)
    python tools/refactor/phase2_engine.py --apply      # write them into the repository

What it does (docs/dev/RESTRUCTURE_BRIEF.md, Phase 2 "Move commit"):

* every module-level variable of main.py that is ever rebound becomes an attribute of
  solitaireplus/app/state.py (reads and writes become ``state.name``; ``global`` statements go);
* STATE_* screen names go to solitaireplus/app/state_names.py;
* blocks of main.py move to app/sounds.py, app/window.py, app/assets.py, app/fonts.py,
  ui/cursors.py, ui/buttons.py, ui/text.py, ui/panels.py, ui/backgrounds.py;
* the main loop goes to app/loop.py with a screen registry; every event-chain and draw-chain
  branch becomes a function in solitaireplus/legacy.py (``loop_event_<state>``,
  ``loop_draw_<state>``, ``loop_late_<state>``), and everything else of main.py goes there too;
* main.py keeps only its start-up header and calls ``loop.run()``.

Start-up order is kept exactly: legacy.py imports each extracted module at the place its first
block used to be, so their module code runs at the same moment as before. Extracted modules
refer to legacy.py and to each other through late-bound LazyModule proxies (app/lazy.py).
"""
from __future__ import annotations

import argparse
import ast
import collections
import re
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

import libcst as cst
from libcst.metadata import (ExpressionContext, ExpressionContextProvider, GlobalScope, MetadataWrapper,
                             ParentNodeProvider, PositionProvider, ScopeProvider)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from refactor.analysis import is_declared_global, refers_to_global  # noqa: E402
from refactor.lazy_template import TEXT as LAZY_TEXT  # noqa: E402

PACKAGE = "solitaireplus"

# module key -> (dotted module, alias used in code)
MODULES = {
    "legacy": (f"{PACKAGE}.legacy", "legacy"),
    "state": (f"{PACKAGE}.app.state", "state"),
    "state_names": (f"{PACKAGE}.app.state_names", "state_names"),
    "sounds": (f"{PACKAGE}.app.sounds", "sounds"),
    "window": (f"{PACKAGE}.app.window", "window"),
    "assets": (f"{PACKAGE}.app.assets", "assets"),
    "fonts": (f"{PACKAGE}.app.fonts", "fonts"),
    "cursors": (f"{PACKAGE}.ui.cursors", "cursors"),
    "buttons": (f"{PACKAGE}.ui.buttons", "buttons"),
    "text": (f"{PACKAGE}.ui.text", "ui_text"),   # "text" is a common local name
    "panels": (f"{PACKAGE}.ui.panels", "panels"),
    "backgrounds": (f"{PACKAGE}.ui.backgrounds", "backgrounds"),
    "loop": (f"{PACKAGE}.app.loop", "loop"),
}
EXTRACTED = ["sounds", "window", "assets", "fonts", "cursors", "buttons", "text", "panels", "backgrounds"]

DOCS = {
    "sounds": "Sound effects, music playlists and the horse-race music cue (moved out of main.py).",
    "window": "The game window: the fixed 1366x768 game surface, window size, fullscreen, mouse mapping and\n"
              "presenting each frame (moved out of main.py).",
    "assets": "Images loaded at start-up: avatar art, menu backgrounds, felts, card backs, titles, splash art,\n"
              "the drifting menu background constants and the cosmetic catalogs (moved out of main.py).",
    "fonts": "Fonts created at start-up and shared by many screens (moved out of main.py).",
    "cursors": "Mouse cursors: cosmetic cursor images, the accessible-size check and the software cursor\n"
               "fallback (moved out of main.py).",
    "buttons": "Wooden menu buttons and plain buttons (moved out of main.py).",
    "text": "Text helpers: fitting text into a width and word-wrapping (moved out of main.py).",
    "panels": "Submenu title plaques and darkened submenu backgrounds (moved out of main.py).",
    "backgrounds": "The slowly drifting main-menu background (moved out of main.py).",
}

# Top-level statements of main.py that move, by line range of the statement start (inclusive).
# Each range is checked against the expected text of its first line, so a shifted file is caught.
BLOCKS = {
    "sounds": [(556, 868, "# AUDIO")],
    "window": [(3422, 3427, "# DISPLAY"), (3442, 3474, "WINDOW_WIDTH, WINDOW_HEIGHT = DEFAULT_WINDOW_SIZE")],
    "assets": [(3967, 4166, "# LAYERED AVATAR ASSETS")],
    "backgrounds": [(3428, 3441, "# MENU BACKGROUND DRIFT")],
    "cursors": [(4167, 4390, "")],
    "fonts": [(4401, 4540, "# =================================================="), ],
}
FUNCTIONS = {
    "window": ["invalidate_scaled_surface_cache", "set_window_size", "set_fullscreen_enabled", "window_to_game_coords"],
    "buttons": ["draw_button", "draw_menu_button"],
    "text": ["render_text_fit", "draw_wrapped_text", "draw_wrapped_text_limited"],
    "panels": ["draw_submenu_title", "draw_submenu_background"],
    "backgrounds": ["draw_drifting_menu_background"],
}
HEADER_END_MARKER = "update_check.cleanup_leftovers()"
PRELOOP_FIRST = "apply_saved_app_settings()"

# Chain B branches that are per-frame logic (timed NPC poker actions) rather than drawing.
LATE_STATES = {"STATE_TEXAS_HOLDEM", "STATE_SEVEN_CARD_STUD", "STATE_FIVE_CARD_DRAW"}


@dataclass
class Unit:
    """A piece of the old loop that becomes one function (or the loop skeleton itself)."""
    key: str                      # "event:STATE_X", "draw:STATE_X", "late:STATE_X", "post", "present", "loop"
    module: str                   # module the code goes to
    first_line: int
    last_line: int
    nodes: list = field(default_factory=list)


class Plan:
    def __init__(self, source: str):
        self.source = source
        self.lines = source.splitlines()
        self.wrapper = MetadataWrapper(cst.parse_module(source))
        self.module = self.wrapper.module
        self.positions = self.wrapper.resolve(PositionProvider)
        self.parents = self.wrapper.resolve(ParentNodeProvider)
        self.scopes = self.wrapper.resolve(ScopeProvider)
        self.contexts = self.wrapper.resolve(ExpressionContextProvider)
        self.problems: list[str] = []
        self.body = list(self.module.body)
        self._find_segments()
        self._check_blocks()
        self._assign_statements()
        self._collect_bindings()
        self._find_units()
        self._classify_names()

    # ---------------------------------------------------------------- helpers
    def line(self, node) -> int:
        return self.positions[node].start.line

    def end_line(self, node) -> int:
        return self.positions[node].end.line

    def code(self, node) -> str:
        return self.module.code_for_node(node)

    def condition(self, node) -> str:
        """An if-test as normalised source (parentheses and line breaks removed)."""
        return ast.unparse(ast.parse(self.code(node).strip(), mode="eval").body)

    # ---------------------------------------------------------------- segments
    def _find_segments(self):
        header_end = preloop = loop = None
        for index, statement in enumerate(self.body):
            text = self.code(statement).strip()
            if header_end is None and text.endswith(HEADER_END_MARKER):
                header_end = index
            if preloop is None and text.endswith(PRELOOP_FIRST) and "def " not in text:
                preloop = index
            if isinstance(statement, cst.While):
                loop = index
        if None in (header_end, preloop, loop):
            raise SystemExit(f"could not find the header / pre-loop / loop ({header_end}, {preloop}, {loop})")
        self.header = self.body[:header_end + 1]
        self.main_body = self.body[header_end + 1:preloop]
        self.preloop = self.body[preloop:loop]
        self.loop = self.body[loop]
        self.postloop = self.body[loop + 1:]

    def _check_blocks(self):
        for module, ranges in BLOCKS.items():
            for first, last, expected in ranges:
                nearby = self.lines[first - 1:first + 3]
                if expected and not any(expected in line for line in nearby):
                    raise SystemExit(f"{module}: lines {first}-{first + 3} are {nearby!r}, expected {expected!r}")

    def _assign_statements(self):
        functions = {name: module for module, names in FUNCTIONS.items() for name in names}
        self.statement_module: dict[int, str] = {}
        for statement in self.main_body:
            line = self.line(statement)
            module = "legacy"
            if isinstance(statement, cst.FunctionDef) and statement.name.value in functions:
                module = functions[statement.name.value]
            else:
                for block, ranges in BLOCKS.items():
                    if any(first <= line <= last for first, last, _ in ranges):
                        module = block
                        break
            if module == "legacy" and self._assigns_only_state_names(statement):
                module = "state_names"
            self.statement_module[id(statement)] = module
        self._check_contiguous()
        missing = {name for name in functions if not any(
            isinstance(s, cst.FunctionDef) and s.name.value == name for s in self.main_body)}
        if missing:
            raise SystemExit(f"functions not found: {sorted(missing)}")

    def _check_contiguous(self):
        """A module's start-up code runs where its first statement was, so it must be one block."""
        order = [self.statement_module[id(s)] for s in self.main_body]
        defs = [isinstance(s, cst.FunctionDef) for s in self.main_body]
        for module in EXTRACTED:
            indexes = [i for i, m in enumerate(order) if m == module and not defs[i]]
            if not indexes:
                continue
            # other extracted modules' statements in between are fine here (pure constants);
            # legacy statements in between would run in the wrong order
            between = [i for i in range(indexes[0], indexes[-1] + 1)
                       if order[i] == "legacy" and not defs[i]]
            if between:
                lines = [self.line(self.main_body[i]) for i in between[:5]]
                raise SystemExit(f"{module}: its statements are split by other code at lines {lines}")

    @staticmethod
    def _assigns_only_state_names(statement) -> bool:
        if not isinstance(statement, cst.SimpleStatementLine) or len(statement.body) != 1:
            return False
        small = statement.body[0]
        return (isinstance(small, cst.Assign) and len(small.targets) == 1
                and isinstance(small.targets[0].target, cst.Name)
                and small.targets[0].target.value.startswith("STATE_")
                and isinstance(small.value, cst.SimpleString))

    # ---------------------------------------------------------------- bindings
    def _collect_bindings(self):
        """Module-level name facts: where each name is bound, rebound, declared global, imported."""
        self.import_node: dict[str, cst.CSTNode] = {}
        self.first_binding: dict[str, cst.CSTNode] = {}
        self.binding_count = collections.Counter()
        self.function_stored: set[str] = set()
        self.reassigned: set[str] = set()
        self.defined_functions: set[str] = set()
        self.except_names: set[str] = set()
        plan = self

        class Collector(cst.CSTVisitor):
            def __init__(self):
                self.top = None

            def on_visit(self, node):
                if plan.parents.get(node) is plan.module:
                    self.top = node
                return super().on_visit(node)

            def visit_FunctionDef(self, node):
                if plan.parents.get(node) is plan.module:
                    plan.defined_functions.add(node.name.value)
                    plan.first_binding.setdefault(node.name.value, node)
                    plan.binding_count[node.name.value] += 1

            def visit_ImportAlias(self, node):
                scope = plan.scopes.get(node)
                if isinstance(scope, GlobalScope):
                    if node.asname is not None:
                        bound = node.asname.name.value
                    else:
                        bound = node.name.value if isinstance(node.name, cst.Name) else plan.code(node.name).split(".")[0]
                    plan.import_node.setdefault(bound, self.top)
                return False

            def visit_Name(self, node):
                context = plan.contexts.get(node)
                if context is None:
                    return
                parent = plan.parents[node]
                if isinstance(parent, (cst.FunctionDef, cst.ClassDef)):
                    return
                scope = plan.scopes.get(node)
                name = node.value
                if context in (ExpressionContext.STORE, ExpressionContext.DEL):
                    if isinstance(parent, cst.AsName) and isinstance(plan.parents[parent], cst.ExceptHandler):
                        plan.except_names.add(name)
                        return
                    if isinstance(scope, GlobalScope):
                        plan.binding_count[name] += 1
                        plan.first_binding.setdefault(name, self.top)
                        if isinstance(parent, cst.AugAssign) or context is ExpressionContext.DEL:
                            plan.reassigned.add(name)
                    elif scope is not None and is_declared_global(scope, name):
                        plan.function_stored.add(name)

        self.wrapper.visit(Collector())
        self.module_names = set(self.first_binding) | set(self.import_node)
        self.mutable = {name for name in self.first_binding
                        if name not in self.defined_functions and name not in self.import_node
                        and (self.binding_count[name] > 1 or name in self.function_stored or name in self.reassigned)}
        both = set(self.import_node) & (set(self.first_binding) - self.defined_functions)
        for name in sorted(both):
            self.problems.append(f"{name!r} is both imported and assigned at module level; handled as a variable")

    # ---------------------------------------------------------------- the loop
    def _chain(self, node):
        branches = []
        while True:
            test = self.condition(node.test)
            match = re.fullmatch(r"current_state == (STATE_[A-Z_0-9]+)", test)
            if not match:
                raise SystemExit(f"unexpected branch condition {test!r} at line {self.line(node)}")
            branches.append((match.group(1), node))
            orelse = node.orelse
            if orelse is None:
                return branches
            if isinstance(orelse, cst.If):
                node = orelse
                continue
            raise SystemExit(f"else branch in a state chain at line {self.line(node)}")

    def _find_units(self):
        loop = self.loop
        body = list(loop.body.body)
        event_for = next(s for s in body if isinstance(s, cst.For))
        for_body = list(event_for.body.body)
        self.event_prelude = []
        self.event_branches = []           # (state, If node)
        for statement in for_body:
            if isinstance(statement, cst.If) and self.condition(statement.test).startswith("current_state == STATE_"):
                self.event_branches += self._chain(statement)
            else:
                if self.event_branches:
                    raise SystemExit(f"statement after the event chain at line {self.line(statement)}")
                self.event_prelude.append(statement)
        index = body.index(event_for)
        self.frame_prologue = body[:index]
        rest = body[index + 1:]
        state_ifs = [i for i, s in enumerate(rest) if isinstance(s, cst.If)
                     and re.fullmatch(r"current_state == STATE_[A-Z_0-9]+", self.condition(s.test))]
        # the two draw chains are the last two `if current_state == STATE_X:` statements (the
        # post-event block before them has single-state ifs of its own)
        if len(state_ifs) < 2:
            raise SystemExit(f"expected two draw chains, found {len(state_ifs)}")
        chain_a, chain_b = state_ifs[-2], state_ifs[-1]
        self.post_event = rest[:chain_a]
        self.draw_a = self._chain(rest[chain_a])
        self.draw_b = self._chain(rest[chain_b])
        tail = rest[chain_b + 1:]
        # tail: update_achievement_popup(), popup if, scale if, cursor if, flip, clock.tick
        flip_index = next(i for i, s in enumerate(tail) if "pygame.display.flip()" in self.code(s))
        self.popup = tail[:flip_index - 2]
        self.present_nodes = tail[flip_index - 2:flip_index + 1]
        self.after_flip = tail[flip_index + 1:]

        units = []

        def add(key, module, nodes):
            first = min(self.line(n) for n in nodes)
            last = max(self.end_line(n) for n in nodes)
            units.append(Unit(key, module, first, last, nodes))

        for state, branch in self.event_branches:
            add(f"event:{state}", "legacy", list(branch.body.body))
        for state, branch in self.draw_a:
            add(f"draw:{state}", "legacy", list(branch.body.body))
        for state, branch in self.draw_b:
            kind = "late" if state in LATE_STATES else "draw"
            add(f"{kind}:{state}", "legacy", list(branch.body.body))
        add("post", "legacy", self.post_event)
        add("present", "window", self.present_nodes)
        self.units = units
        keys = [u.key for u in units]
        duplicates = [k for k, n in collections.Counter(keys).items() if n > 1]
        if duplicates:
            raise SystemExit(f"a state has two branches of the same kind: {duplicates}")

    def unit_at(self, line) -> Unit | None:
        for unit in self.units:
            if unit.first_line <= line <= unit.last_line:
                return unit
        return None

    def module_at(self, line) -> str:
        """Which module the code at this line of main.py ends up in."""
        loop_first, loop_last = self.line(self.loop), self.end_line(self.loop)
        if loop_first <= line <= loop_last:
            unit = self.unit_at(line)
            return unit.module if unit else "loop"
        for statement in self.preloop + self.postloop:
            if self.line(statement) <= line <= self.end_line(statement):
                return "loop"
        for statement in self.header:
            if self.line(statement) <= line <= self.end_line(statement):
                return "main"
        for statement in self.main_body:
            if self.line(statement) <= line <= self.end_line(statement):
                return self.statement_module[id(statement)]
        return "legacy"

    # ---------------------------------------------------------------- name classes
    def _classify_names(self):
        """Owner module of every module-level name, and loop names that become function locals."""
        loop_first, loop_last = self.line(self.loop), self.end_line(self.loop)
        # where each module-level name occurs (by unit key; "loop" for the skeleton; "outside" elsewhere)
        occurrences = collections.defaultdict(list)       # name -> [(line, unit key, is_store)]
        read_by_functions = set()
        plan = self

        class Occ(cst.CSTVisitor):
            def visit_Name(self, node):
                context = plan.contexts.get(node)
                if context is None or isinstance(plan.parents[node], (cst.FunctionDef, cst.ClassDef)):
                    return
                scope = plan.scopes.get(node)
                line = plan.line(node)
                if isinstance(scope, GlobalScope):
                    if loop_first <= line <= loop_last:
                        unit = plan.unit_at(line)
                        key = unit.key if unit else "loop"
                    else:
                        key = "outside"
                    occurrences[node.value].append((line, key, context is not ExpressionContext.LOAD, node))
                elif scope is not None and (
                        (context is ExpressionContext.LOAD and refers_to_global(scope, node))
                        or (context is not ExpressionContext.LOAD and is_declared_global(scope, node.value))):
                    read_by_functions.add(node.value)
                    occurrences[node.value].append((line, "function", context is not ExpressionContext.LOAD, node))

        self.wrapper.visit(Occ())
        self.locals_by_unit: dict[str, set] = collections.defaultdict(set)
        self.fully_local: set[str] = set()     # local in every unit that uses it: not shared state at all
        bound_in_loop = {name for name, occ in occurrences.items()
                         if any(store and loop_first <= line <= loop_last for line, _, store, _ in occ)}
        for name in sorted(bound_in_loop):
            occ = occurrences[name]
            keys = {key for _, key, _, _ in occ}
            if name in read_by_functions or name in self.import_node or name in self.defined_functions:
                continue
            if keys & {"outside", "function"} or name.startswith("STATE_"):
                continue
            # A local in every unit that uses it, if each of those units stores it before any read
            # (then no value ever flows between units or frames through it).
            ok = True
            for key in keys:
                in_unit = sorted((o for o in occ if o[1] == key),
                                 key=lambda item: (item[0], plan.positions[item[3]].start.column))
                first_line, _, first_store, first_node = in_unit[0]
                if not first_store or not self._dominates(first_node, [o[3] for o in in_unit[1:] if not o[2]]):
                    ok = False
                    break
            if not ok:
                continue
            for key in keys:
                self.locals_by_unit[key].add(name)
            self.fully_local.add(name)
        self.loop_locals = {name for names in self.locals_by_unit.values() for name in names}
        # the event loop variable is a parameter / loop local everywhere in the loop
        self.locals_by_unit["loop"].add("event")
        for unit in self.units:
            if unit.key.startswith("event:"):
                self.locals_by_unit[unit.key].add("event")
        self.loop_locals.add("event")
        if not {key for _, key, _, _ in occurrences["event"]} & {"outside", "function"}:
            self.fully_local.add("event")
        self.except_locals = set(self.except_names)
        for name in self.except_locals:
            if not any(store and not isinstance(plan.parents[node], cst.AsName) for _, _, store, node in occurrences[name])                     and not {key for _, key, _, _ in occurrences[name]} & {"function"}:
                self.fully_local.add(name)

        self.owner: dict[str, str] = {}
        for name in self.module_names:
            if name in self.import_node and name not in self.first_binding:
                self.owner[name] = "import"
            elif name.startswith("STATE_"):
                self.owner[name] = "state_names"
            elif name in self.defined_functions:
                self.owner[name] = self._module_of(self.first_binding[name])
            elif name in self.fully_local:
                self.owner[name] = "local"
            elif name in self.mutable or name in bound_in_loop:
                self.owner[name] = "state"
            elif name in self.first_binding:
                self.owner[name] = self._module_of(self.first_binding[name])
        for name in self.function_stored - self.module_names:
            self.owner[name] = "state"      # created by a function through `global`
            self.module_names.add(name)

    def _module_of(self, statement) -> str:
        if statement is None:
            return "legacy"
        return self.module_at(self.line(statement))

    def _dominates(self, store_node, read_nodes) -> bool:
        """Rough check that every read comes after the store, inside the block that holds the store."""
        def blocks(node):
            chain = []
            current = self.parents.get(node)
            while current is not None and current is not self.loop:
                if isinstance(current, (cst.IndentedBlock, cst.SimpleStatementSuite)):
                    chain.append(id(current))
                current = self.parents.get(current)
            return list(reversed(chain))
        store_chain = blocks(store_node)
        store_line = self.line(store_node)
        for read in read_nodes:
            read_chain = blocks(read)
            if self.line(read) < store_line or read_chain[:len(store_chain)] != store_chain:
                return False
        return True


# ==================================================================== rewriting

class Rewriter(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (ScopeProvider, ExpressionContextProvider, ParentNodeProvider, PositionProvider)

    def __init__(self, plan: Plan):
        super().__init__()
        self.plan = plan
        self.used: dict[str, set] = collections.defaultdict(set)    # module -> owners/imports referenced

    def _line(self, node):
        return self.get_metadata(PositionProvider, node).start.line

    def _is_global(self, node) -> bool:
        scope = self.get_metadata(ScopeProvider, node, None)
        context = self.get_metadata(ExpressionContextProvider, node, None)
        if scope is None or context is None:
            return False
        if isinstance(scope, GlobalScope):
            return True
        if context is ExpressionContext.LOAD:
            return refers_to_global(scope, node)
        return is_declared_global(scope, node.value)

    def leave_Name(self, original, updated):
        plan = self.plan
        name = original.value
        if name not in plan.owner:
            return updated
        context = self.get_metadata(ExpressionContextProvider, original, None)
        if context is None:
            return updated
        parent = self.get_metadata(ParentNodeProvider, original)
        if isinstance(parent, (cst.FunctionDef, cst.ClassDef)):
            return updated
        if isinstance(parent, cst.AsName) and isinstance(self.get_metadata(ParentNodeProvider, parent), cst.ExceptHandler):
            return updated
        if not self._is_global(original):
            return updated
        line = self._line(original)
        here = plan.module_at(line)
        scope = self.get_metadata(ScopeProvider, original)
        if isinstance(scope, GlobalScope) and plan.line(plan.loop) <= line <= plan.end_line(plan.loop):
            unit = plan.unit_at(line)
            key = unit.key if unit else "loop"
            if name in plan.locals_by_unit.get(key, ()):
                return updated
        if name in plan.except_locals and isinstance(scope, GlobalScope):
            return updated
        owner = plan.owner[name]
        if owner == "local":
            return updated
        if owner == "import":
            self.used[here].add(("import", name))
            return updated
        if owner == here and owner != "state":
            return updated
        self.used[here].add(("module", owner))
        return cst.Attribute(value=cst.Name(MODULES[owner][1]), attr=cst.Name(name))

    def leave_Global(self, original, updated):
        return cst.RemoveFromParent()

    def leave_SimpleStatementLine(self, original, updated):
        if not updated.body:
            return cst.RemoveFromParent()
        return updated

    def leave_Call(self, original, updated):
        if isinstance(updated.func, cst.Name) and updated.func.value == "globals" and not updated.args:
            here = self.plan.module_at(self._line(original))
            if here == "legacy":
                return updated.with_changes(func=cst.Name("game_namespace"))
            self.used[here].add(("module", "legacy"))
            return updated.with_changes(func=cst.Attribute(value=cst.Name("legacy"), attr=cst.Name("game_namespace")))
        return updated


class ContinueToReturn(cst.CSTTransformer):
    """In an extracted event branch, `continue` of the event loop becomes `return`."""

    def __init__(self):
        super().__init__()
        self.depth = -1000          # the extracted function itself is the first FunctionDef visited

    def visit_For(self, node):
        self.depth += 1

    def leave_For(self, original, updated):
        self.depth -= 1
        return updated

    def visit_While(self, node):
        self.depth += 1

    def leave_While(self, original, updated):
        self.depth -= 1
        return updated

    def visit_FunctionDef(self, node):
        self.depth += 1000

    def leave_FunctionDef(self, original, updated):
        self.depth -= 1000
        return updated

    def leave_Continue(self, original, updated):
        if self.depth == 0:
            return cst.Return()
        return updated


# ==================================================================== output

def statement_code(module, node) -> str:
    return module.code_for_node(node)


def dedent_block(code: str) -> str:
    return textwrap.dedent(code)


def indent(code: str, prefix: str) -> str:
    return "".join(prefix + line if line.strip() else line for line in code.splitlines(True))


def import_line(owner: str) -> str:
    """`from package import leaf` (with `as alias` when the alias differs from the module name)."""
    package, leaf = MODULES[owner][0].rsplit(".", 1)
    alias = MODULES[owner][1]
    return f"from {package} import {leaf}" + ("" if alias == leaf else f" as {alias}")


def state_slug(state: str) -> str:
    return state[len("STATE_"):].lower()


# Local variables that share a name with a module alias used in the new code; renamed first
# (only inside these functions) so `state.x` keeps meaning the state module there.
LOCAL_RENAMES = {
    "handle_career_activity": {"state": "activity"},
    "preview_competitive_rating": {"state": "opponent_state"},
}


class LocalRenamer(cst.CSTTransformer):
    def __init__(self):
        super().__init__()
        self.stack: list[str] = []
        self.skip: set[int] = set()
        self.renamed = collections.Counter()

    def visit_FunctionDef(self, node):
        self.stack.append(node.name.value)

    def leave_FunctionDef(self, original, updated):
        self.stack.pop()
        return updated

    def visit_Attribute(self, node):
        self.skip.add(id(node.attr))

    def visit_Arg(self, node):
        if node.keyword is not None:
            self.skip.add(id(node.keyword))

    def leave_Name(self, original, updated):
        if not self.stack or id(original) in self.skip:
            return updated
        renames = LOCAL_RENAMES.get(self.stack[0], {})
        if updated.value in renames:
            self.renamed[self.stack[0]] += 1
            return updated.with_changes(value=renames[updated.value])
        return updated


def build(source: str) -> dict[str, str]:
    renamer = LocalRenamer()
    source = cst.parse_module(source).visit(renamer).code
    if set(renamer.renamed) != set(LOCAL_RENAMES):
        raise SystemExit(f"local renames not applied as expected: {dict(renamer.renamed)}")
    plan = Plan(source)
    rewriter = Rewriter(plan)
    new_module = plan.wrapper.visit(rewriter)

    # map original top-level statements to rewritten ones (same order; none removed at top level)
    new_body = list(new_module.body)
    if len(new_body) != len(plan.body):
        raise SystemExit("a top-level statement disappeared during rewriting")
    rewritten = {id(old): new for old, new in zip(plan.body, new_body)}

    def find_rewritten(old_node):
        """The rewritten copy of a nested original node (by matching the path from the top)."""
        path = []
        node = old_node
        while plan.parents.get(node) is not plan.module:
            parent = plan.parents[node]
            path.append((parent, node))
            node = parent
        top_new = rewritten[id(node)]
        current_old, current_new = node, top_new
        for parent, child in reversed(path):
            # walk children in parallel
            old_children = list(_children(current_old))
            new_children = list(_children(current_new))
            index = next(i for i, c in enumerate(old_children) if c is child)
            current_old, current_new = child, new_children[index]
        return current_new

    out: dict[str, list[str]] = collections.defaultdict(list)

    # ---- extracted unit functions (rewritten bodies)
    unit_functions: list[str] = []
    for unit in plan.units:
        if unit.key == "present":
            continue
        new_nodes = [find_rewritten(n) for n in unit.nodes]
        kind, _, state = unit.key.partition(":")
        if kind == "event":
            name, params = f"loop_event_{state_slug(state)}", "event"
        elif kind == "draw":
            name, params = f"loop_draw_{state_slug(state)}", ""
        elif kind == "late":
            name, params = f"loop_late_{state_slug(state)}", ""
        else:
            name, params = "loop_post_event_updates", ""
        if name in plan.module_names:
            raise SystemExit(f"generated function name {name} clashes with a main.py name")
        body = "".join(cst.Module(body=[n]).code for n in new_nodes)
        function = cst.parse_module(f"def {name}({params}):\n" + indent(dedent_block(body), "    "))
        if kind == "event":
            function = function.visit(ContinueToReturn())
        doc = {"event": f"Old main-loop event branch for {state}.",
               "draw": f"Old draw-chain branch for {state}.",
               "late": f"Old timed-NPC branch for {state} (runs after drawing, as before).",
               "post": "Old per-frame updates between the event loop and drawing."}[kind or "post"]
        code = function.code
        code = code.replace(f"def {name}({params}):\n", f'def {name}({params}):\n    """{doc}"""\n', 1)
        unit_functions.append(code)

    # ---- main body statements, by module, in order
    first_seen_module: list[str] = []
    for statement in plan.main_body:
        module = plan.statement_module[id(statement)]
        code = statement_code(new_module, rewritten[id(statement)])
        out[module].append(code)
        if module not in ("legacy",) and module not in first_seen_module:
            first_seen_module.append(module)
            out["legacy"].append(import_line(module)
                                 + "  # start-up code of this module runs here, as it did in main.py\n")

    # ---- state.py: literal first values
    files: dict[str, str] = {}
    files["main"] = _main_text(plan, new_module, rewritten)
    files["state"], literal_statements = _state_text(plan, new_module, rewritten)
    for code in literal_statements:          # their first value now lives in state.py
        holder = next(chunks for chunks in out.values() if code in chunks)
        holder.remove(code)
    files["state_names"] = _module_text("state_names", '"""Every screen\'s name (the values of state.current_state)."""\n',
                                        out["state_names"], rewriter, plan, imports=False)
    for module in EXTRACTED:
        extra = []
        if module == "window":
            present = "".join(cst.Module(body=[find_rewritten(n)]).code for n in plan.present_nodes)
            extra.append("def present():\n    \"\"\"Scale the 1366x768 game surface into the window and show the frame.\"\"\"\n"
                         + indent(dedent_block(present), "    "))
        files[module] = _module_text(module, f'"""{DOCS[module]}"""\n', out[module] + extra, rewriter, plan)
    files["legacy"] = _legacy_text(plan, out["legacy"], unit_functions, rewriter)
    files["loop"] = _loop_text(plan, new_module, rewritten, find_rewritten, rewriter)
    files["lazy"] = LAZY_TEXT
    for problem in plan.problems:
        print("NOTE:", problem)
    return files


def _children(node):
    return node.children


def _import_lines(plan: Plan, names: set) -> list[str]:
    """Copies of main.py's import statements, keeping only the aliases in `names`."""
    lines, done = [], set()
    by_statement = collections.defaultdict(list)
    for name in sorted(names):
        statement = plan.import_node.get(name)
        if statement is None:
            continue
        by_statement[id(statement)].append(name)
    for statement in plan.body:
        if id(statement) not in by_statement or id(statement) in done:
            continue
        done.add(id(statement))
        wanted = set(by_statement[id(statement)])
        tree = ast.parse(plan.code(statement).strip())
        for node in tree.body:
            if isinstance(node, ast.Import):
                keep = [a for a in node.names if (a.asname or a.name.split(".")[0]) in wanted]
                if keep:
                    lines.append(ast.unparse(ast.Import(names=keep)))
            elif isinstance(node, ast.ImportFrom):
                keep = [a for a in node.names if (a.asname or a.name) in wanted]
                if keep:
                    lines.append(ast.unparse(ast.ImportFrom(module=node.module, names=keep, level=node.level)))
            elif isinstance(node, (ast.If, ast.Try)):
                # an import nested in a top-level if/try: copy the whole statement
                lines.append(plan.code(statement).strip())
    return lines


def _references(rewriter, module):
    owners = sorted({owner for kind, owner in rewriter.used.get(module, ()) if kind == "module"} - {module})
    imports = {name for kind, name in rewriter.used.get(module, ()) if kind == "import"}
    return owners, imports


def _module_text(module, doc, chunks, rewriter, plan, imports=True) -> str:
    owners, import_names = _references(rewriter, module)
    head = [doc]
    if imports:
        head += [line + "\n" for line in _import_lines(plan, import_names)]
        real = [o for o in owners if o in ("state", "state_names")]
        late = [o for o in owners if o not in ("state", "state_names")]
        for owner in real:
            head.append(import_line(owner) + "\n")
        if late:
            head.append(f"from {PACKAGE}.app.lazy import lazy\n")
            for owner in late:
                head.append(f'{MODULES[owner][1]} = lazy("{MODULES[owner][0]}")\n')
    return "".join(head) + "\n" + "".join(chunks).lstrip("\n")


def _state_text(plan, new_module, rewritten):
    literal, other, literal_statements = [], [], []
    for statement in plan.main_body:
        if not isinstance(statement, cst.SimpleStatementLine) or len(statement.body) != 1:
            continue
        small = statement.body[0]
        if not isinstance(small, cst.Assign) or len(small.targets) != 1:
            continue
        target = small.targets[0].target
        if not isinstance(target, cst.Name) or plan.owner.get(target.value) != "state":
            continue
        if plan.first_binding.get(target.value) is not statement:
            continue
        try:
            ast.literal_eval(plan.code(small.value))
        except (ValueError, SyntaxError):
            continue
        literal.append(f"{target.value} = {plan.code(small.value).strip()}\n")
        literal_statements.append(statement_code(new_module, rewritten[id(statement)]))
    names = sorted(n for n, o in plan.owner.items() if o == "state")
    literal_names = {line.split(" = ")[0] for line in literal}
    later = [n for n in names if n not in literal_names]
    text = ['"""Shared runtime state: the variables that used to be globals of main.py.\n\n'
            'Read and write them as ``state.name``. Values below are the starting values; the names\n'
            'listed at the end get their first value during start-up (solitaireplus.legacy and the\n'
            'modules it imports), in the same order as in the old main.py.\n"""\n\n']
    text += literal
    text.append("\n# Set during start-up:\n")
    text += textwrap.wrap(", ".join(later), 100, initial_indent="#   ", subsequent_indent="#   ")
    return "".join(text[:-0] if False else text[:]) .replace("#   ", "\n#   ").lstrip() + "\n", literal_statements


def _legacy_text(plan, chunks, unit_functions, rewriter) -> str:
    owners, _ = _references(rewriter, "legacy")
    head = ['"""Everything from the old main.py that has not moved to its own module yet.\n\n'
            'Temporary: the restructure (docs/dev/RESTRUCTURE_BRIEF.md, Phases 3-10) empties this module\n'
            'area by area and then deletes it. Each old main-loop branch is a function here\n'
            '(loop_event_<screen>, loop_draw_<screen>, loop_late_<screen>), called through the screen\n'
            'registry in solitaireplus/app/loop.py.\n"""\n']
    head.append("import collections as _collections\n")
    # imports that legacy code uses but that were written outside its own statements (main.py's header)
    _, import_names = _references(rewriter, "legacy")
    foreign = {name for name in import_names
               if plan.statement_module.get(id(plan.import_node.get(name))) != "legacy"}
    head += [line + "\n" for line in _import_lines(plan, foreign)]
    head.append(f"from {PACKAGE}.app import state, state_names\n")
    for owner in owners:
        if owner in ("state", "state_names", "loop") or owner in EXTRACTED:
            continue
        head.append(import_line(owner) + "\n")
    body = "".join(chunks)
    namespace = ('\n\ndef game_namespace():\n'
                 '    """What globals() used to be in main.py: shared state first, then everything else.\n\n'
                 '    Writes go to solitaireplus.app.state. Temporary, like this module.\n    """\n'
                 '    import sys\n'
                 + "".join("    " + import_line(m) + "\n" for m in EXTRACTED)
                 + '    modules = [state, state_names, ' + ", ".join(MODULES[m][1] for m in EXTRACTED)
                 + ', sys.modules[__name__]]\n'
                 '    return _collections.ChainMap(*(vars(module) for module in modules))\n')
    return "".join(head) + "\n" + body + namespace + "\n\n" + "\n\n".join(unit_functions)


def _main_text(plan, new_module, rewritten) -> str:
    header = "".join(plan.code(s) for s in plan.header)
    return header.rstrip() + "\n\n# Everything else lives in the solitaireplus package; loop.run() is the old main loop.\n" \
        "from solitaireplus.app import loop\n\nloop.run()\n"


def _loop_text(plan, new_module, rewritten, find_rewritten, rewriter) -> str:
    def block(nodes, prefix):
        code = "".join(cst.Module(body=[find_rewritten(n)]).code for n in nodes)
        return indent(dedent_block(code), prefix)

    preloop = "".join(statement_code(new_module, rewritten[id(s)]) for s in plan.preloop)
    postloop = "".join(statement_code(new_module, rewritten[id(s)]) for s in plan.postloop)
    registry_lines = []
    states = []
    for unit in plan.units:
        kind, _, state = unit.key.partition(":")
        if state and state not in states:
            states.append(state)
    for state in states:
        registry_lines.append(f'    state_names.{state}: "{PACKAGE}.legacy:{state_slug(state)}",\n')
    owners, import_names = _references(rewriter, "loop")
    imports = _import_lines(plan, import_names)
    text = ['"""The main loop and the screen registry (the old `while running:` loop of main.py).\n\n'
            'Each frame: poll the update check and settings, sync audio, handle events (global keys,\n'
            'mouse mapping, then the current screen), run per-frame updates, draw the current screen,\n'
            'then overlays, then present. The order is exactly the old loop\'s order.\n\n'
            'SCREENS maps a screen name to the code that runs it: "package.module" for a screen module\n'
            '(functions handle_event(event), draw(), and optionally update() and late_update()), or\n'
            '"solitaireplus.legacy:<screen>" for screens still in solitaireplus/legacy.py.\n"""\n',
            "import importlib\n"]
    text += [line + "\n" for line in imports]
    text.append(f"from {PACKAGE}.app import state, state_names\n")
    # legacy first: importing it runs the old main.py start-up, which imports the other
    # modules at the right moments (fonts after pygame.font.init(), assets after the window...)
    text.append(f"from {PACKAGE} import legacy  # noqa: I001 (must come before the modules below)\n")
    for owner in owners:
        if owner in ("state", "state_names", "loop", "legacy"):
            continue
        text.append(import_line(owner) + "\n")
    text.append("\nSCREENS = {\n" + "".join(registry_lines) + "}\n")
    late_drawn = [state for state, _ in plan.draw_b if state not in LATE_STATES]
    text.append("\n# Screens the old loop drew in its second draw chain, after the timed poker turns. That chain\n"
                "# looked at current_state again, which the first chain may have changed.\n"
                "DRAWN_LATE = {" + ", ".join(f"state_names.{s}" for s in late_drawn) + "}\n")
    text.append('''

class _LegacyScreen:
    """A screen whose code is still in solitaireplus/legacy.py (loop_event_<screen>, loop_draw_<screen>, ...)."""

    def __init__(self, module, slug, draws_late):
        self.handle_event = getattr(module, f"loop_event_{slug}", None)
        self.draw = getattr(module, f"loop_draw_{slug}", None)
        self.late_update = getattr(module, f"loop_late_{slug}", None)
        self.update = None
        self.DRAWS_LATE = draws_late


_loaded = {}


def screen_for(name):
    """The screen object for a screen name (None for a name without code)."""
    if name not in _loaded:
        target = SCREENS.get(name)
        if target is None:
            _loaded[name] = None
        elif ":" in target:
            module_name, slug = target.split(":", 1)
            _loaded[name] = _LegacyScreen(importlib.import_module(module_name), slug, name in DRAWN_LATE)
        else:
            _loaded[name] = importlib.import_module(target)
    return _loaded[name]


def run():
''')
    text.append(indent(preloop, "    "))
    text.append("\n    while state.running:\n")
    text.append(block(plan.frame_prologue, "        "))
    text.append("\n        for event in pygame.event.get():\n")
    text.append(block(plan.event_prelude, "            "))
    text.append('''
            screen = screen_for(state.current_state)
            if screen is not None and screen.handle_event is not None:
                screen.handle_event(event)

''')
    text.append("        legacy.loop_post_event_updates()\n\n")
    text.append('''        # First draw chain: per-frame update, then draw.
        screen = screen_for(state.current_state)
        if screen is not None:
            if getattr(screen, "update", None) is not None:
                screen.update(pygame.time.get_ticks())
            if getattr(screen, "draw", None) is not None and not getattr(screen, "DRAWS_LATE", False):
                screen.draw()

        # Second draw chain (looks at current_state again): timed poker turns, and the screens
        # that are drawn late (debug menus, level-up, Solitaire).
        screen = screen_for(state.current_state)
        if screen is not None:
            if getattr(screen, "late_update", None) is not None:
                screen.late_update()
            elif getattr(screen, "draw", None) is not None and getattr(screen, "DRAWS_LATE", False):
                screen.draw()

''')
    text.append(block(plan.popup, "        "))
    text.append("\n        window.present()\n\n")
    text.append(block(plan.after_flip, "        "))
    text.append("\n")
    text.append(indent(postloop, "    "))
    return "".join(text)


TARGETS = {
    "main": "main.py",
    "legacy": f"{PACKAGE}/legacy.py",
    "state": f"{PACKAGE}/app/state.py",
    "state_names": f"{PACKAGE}/app/state_names.py",
    "loop": f"{PACKAGE}/app/loop.py",
    "lazy": f"{PACKAGE}/app/lazy.py",
    "sounds": f"{PACKAGE}/app/sounds.py",
    "window": f"{PACKAGE}/app/window.py",
    "assets": f"{PACKAGE}/app/assets.py",
    "fonts": f"{PACKAGE}/app/fonts.py",
    "cursors": f"{PACKAGE}/ui/cursors.py",
    "buttons": f"{PACKAGE}/ui/buttons.py",
    "text": f"{PACKAGE}/ui/text.py",
    "panels": f"{PACKAGE}/ui/panels.py",
    "backgrounds": f"{PACKAGE}/ui/backgrounds.py",
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=str(ROOT / "main.py"))
    parser.add_argument("--out", help="write the files under this folder instead of the repository")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    if not args.out and not args.apply:
        parser.error("give --out DIR or --apply")
    files = build(Path(args.source).read_text(encoding="utf-8"))
    base = Path(args.out) if args.out else ROOT
    for key, relative in TARGETS.items():
        path = base / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(files[key], encoding="utf-8")
        compile(files[key], str(path), "exec")
        print(f"  {len(files[key].splitlines()):6d} lines  {relative}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
