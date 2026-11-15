"""Facts about a module's globals, for deciding what moves into solitaireplus/app/state.py.

A module-level name is *mutable* (shared runtime state) when anything rebinds it after its
first module-level binding: a second module-level binding (including inside the main loop),
an augmented assignment, `del`, or a store inside a function that declares it `global`.
Names bound only once and never rebound are *constants* (they may still be objects that are
changed in place, which is fine: the binding never changes).
"""
from __future__ import annotations

import collections
from dataclasses import dataclass, field

import libcst as cst
from libcst.metadata import (ExpressionContext, ExpressionContextProvider, FunctionScope, GlobalScope,
                             MetadataWrapper, ParentNodeProvider, PositionProvider, ScopeProvider)


@dataclass
class NameFacts:
    name: str
    module_bindings: list = field(default_factory=list)     # line numbers of module-level bindings
    function_stores: list = field(default_factory=list)     # (function, line) stores through `global`
    kinds: set = field(default_factory=set)                 # assign/augassign/for/with/import/def/del/except/...
    global_reads: collections.Counter = field(default_factory=collections.Counter)  # function -> count

    @property
    def is_import(self):
        return "import" in self.kinds

    @property
    def is_function(self):
        return self.kinds == {"def"}

    @property
    def mutable(self):
        if self.is_import or "def" in self.kinds or "class" in self.kinds:
            return False
        return (len(self.module_bindings) > 1 or bool(self.function_stores)
                or bool(self.kinds & {"augassign", "del", "for", "with"}))


def binding_kind(parents, node) -> str:
    parent = parents[node]
    while isinstance(parent, (cst.Tuple, cst.List, cst.Element, cst.StarredElement, cst.AssignTarget)):
        if isinstance(parent, cst.AssignTarget):
            return "assign"
        parent = parents[parent]
    if isinstance(parent, cst.AugAssign):
        return "augassign"
    if isinstance(parent, cst.AnnAssign):
        return "assign"
    if isinstance(parent, cst.For):
        return "for"
    if isinstance(parent, (cst.WithItem, cst.AsName)):
        grand = parents[parent]
        if isinstance(parent, cst.AsName) and isinstance(grand, cst.ExceptHandler):
            return "except"
        if isinstance(parent, cst.AsName) and isinstance(grand, (cst.ImportAlias,)):
            return "import"
        return "with"
    if isinstance(parent, cst.Del):
        return "del"
    if isinstance(parent, cst.NamedExpr):
        return "walrus"
    if isinstance(parent, (cst.ImportAlias,)):
        return "import"
    if isinstance(parent, cst.CompFor):
        return "comprehension"
    return type(parent).__name__


class _Collector(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (ScopeProvider, ExpressionContextProvider, ParentNodeProvider, PositionProvider)

    def __init__(self):
        self.facts: dict[str, NameFacts] = {}
        self.functions: list[str] = []

    def fact(self, name) -> NameFacts:
        if name not in self.facts:
            self.facts[name] = NameFacts(name)
        return self.facts[name]

    def visit_FunctionDef(self, node):
        scope = self.get_metadata(ScopeProvider, node)
        if isinstance(scope, GlobalScope):
            fact = self.fact(node.name.value)
            fact.kinds.add("def")
            fact.module_bindings.append(self.get_metadata(PositionProvider, node).start.line)
        self.functions.append(node.name.value)

    def leave_FunctionDef(self, node):
        self.functions.pop()

    def visit_ClassDef(self, node):
        scope = self.get_metadata(ScopeProvider, node)
        if isinstance(scope, GlobalScope):
            self.fact(node.name.value).kinds.add("class")

    def visit_ImportAlias(self, node):
        scope = self.get_metadata(ScopeProvider, node, None)
        if isinstance(scope, GlobalScope):
            bound = (node.asname.name.value if node.asname else
                     (node.name.value if isinstance(node.name, cst.Name) else node.name.value.value))
            if isinstance(bound, str):
                fact = self.fact(bound)
                fact.kinds.add("import")
                fact.module_bindings.append(self.get_metadata(PositionProvider, node).start.line)
        return False

    def visit_Name(self, node):
        context = self.get_metadata(ExpressionContextProvider, node, None)
        if context is None:
            return
        scope = self.get_metadata(ScopeProvider, node, None)
        if scope is None:
            return
        line = self.get_metadata(PositionProvider, node).start.line
        name = node.value
        parents = self.metadata[ParentNodeProvider]
        if isinstance(parents[node], (cst.FunctionDef, cst.ClassDef)):
            return  # the def/class name itself is recorded by visit_FunctionDef/visit_ClassDef
        if context in (ExpressionContext.STORE, ExpressionContext.DEL):
            kind = binding_kind(parents, node)
            if kind in ("import",):
                return
            if isinstance(scope, GlobalScope):
                fact = self.fact(name)
                fact.kinds.add("del" if context is ExpressionContext.DEL else kind)
                if context is ExpressionContext.STORE:
                    fact.module_bindings.append(line)
            elif is_declared_global(scope, name):
                fact = self.fact(name)
                fact.function_stores.append((self.functions[-1] if self.functions else "?", line))
                if kind == "augassign":
                    fact.kinds.add("augassign")
        elif context is ExpressionContext.LOAD and not isinstance(scope, GlobalScope):
            if refers_to_global(scope, node):
                self.fact(name).global_reads[self.functions[-1] if self.functions else "?"] += 1


def is_declared_global(scope, name) -> bool:
    while scope is not None and not isinstance(scope, GlobalScope):
        overwrites = getattr(scope, "_scope_overwrites", {})   # libcst records `global x` here
        if isinstance(scope, FunctionScope) and isinstance(overwrites.get(name), GlobalScope):
            return True
        if isinstance(scope, FunctionScope) and name in scope.assignments:
            # a real local binding in this function
            if any(a.scope is scope for a in scope.assignments[name]):
                return False
        scope = scope.parent
    return False


def refers_to_global(scope, node) -> bool:
    referents = set()
    for access in scope.accesses[node]:
        referents |= set(access.referents)
    if referents:
        return all(isinstance(r.scope, GlobalScope) for r in referents)
    return False


def analyse(source: str) -> dict[str, NameFacts]:
    wrapper = MetadataWrapper(cst.parse_module(source))
    collector = _Collector()
    wrapper.visit(collector)
    return collector.facts


if __name__ == "__main__":
    import sys
    from pathlib import Path
    facts = analyse(Path(sys.argv[1] if len(sys.argv) > 1 else "main.py").read_text(encoding="utf-8"))
    mutable = sorted(n for n, f in facts.items() if f.mutable)
    functions = sorted(n for n, f in facts.items() if f.is_function)
    imports = sorted(n for n, f in facts.items() if f.is_import)
    constants = sorted(n for n, f in facts.items() if not f.mutable and not f.is_function and not f.is_import
                       and "class" not in f.kinds)
    print(f"{len(facts)} module names: {len(mutable)} mutable, {len(constants)} constants, "
          f"{len(functions)} functions, {len(imports)} imports")
    odd = sorted(n for n, f in facts.items() if f.kinds & {"walrus", "except", "comprehension"})
    print("unusual bindings:", {n: sorted(facts[n].kinds) for n in odd})
