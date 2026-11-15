"""Rewrite imports of moved modules, keeping every local name the same.

    import game                 ->  from solitaireplus.games.solitaire import rules as game
    import profile as pm        ->  from solitaireplus.profile import saves as pm
    from game import Game       ->  from solitaireplus.games.solitaire.rules import Game
    from shared import poker_core as impl -> from solitaireplus.games.poker import core as impl
    patch("score_four.random")  ->  patch("solitaireplus.games.cards.score_four.random")

Because the bound names never change, no other line of a module needs editing.
A file's own neighbours win, like on the real import path: inside multiplayer/ a module
that exists in multiplayer/ is not rewritten (its local copy is what gets imported).
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import libcst as cst

Resolver = Callable[[str], "str | None"]

STRING_CALLS = {"patch", "import_module", "setattr", "delattr", "reload"}


def dotted_name(node) -> str:
    if isinstance(node, cst.Name):
        return node.value
    if isinstance(node, cst.Attribute):
        return f"{dotted_name(node.value)}.{node.attr.value}"
    raise TypeError(node)


def dotted_node(name: str):
    parts = name.split(".")
    node = cst.Name(parts[0])
    for part in parts[1:]:
        node = cst.Attribute(value=node, attr=cst.Name(part))
    return node


def resolve_dotted(name: str, resolve: Resolver) -> str | None:
    """New dotted path for `name` (which may continue past the module, e.g. 'game.Game.x')."""
    parts = name.split(".")
    for length in range(len(parts), 0, -1):
        target = resolve(".".join(parts[:length]))
        if target is not None:
            return ".".join([target, *parts[length:]])
    return None


class ImportRewriter(cst.CSTTransformer):
    def __init__(self, resolve: Resolver, filename: str):
        self.resolve = resolve
        self.filename = filename
        self.changes = 0
        self.problems: list[str] = []

    # import x, import x as y
    def leave_Import(self, original, updated):
        statements, kept = [], []
        for alias in updated.names:
            name = dotted_name(alias.name)
            target = self.resolve(name)
            if target is None:
                kept.append(alias.with_changes(comma=cst.MaybeSentinel.DEFAULT))
                continue
            if "." in name and alias.asname is None:
                self.problems.append(f"{self.filename}: 'import {name}' binds the package name; fix by hand")
                kept.append(alias.with_changes(comma=cst.MaybeSentinel.DEFAULT))
                continue
            bound = alias.asname.name.value if alias.asname else name
            parent, leaf = target.rsplit(".", 1)
            statements.append(cst.ImportFrom(
                module=dotted_node(parent),
                names=[cst.ImportAlias(name=cst.Name(leaf),
                                       asname=None if bound == leaf else cst.AsName(name=cst.Name(bound)))],
            ))
            self.changes += 1
        if not statements:
            return updated
        if kept:
            statements.insert(0, updated.with_changes(names=kept))
        return cst.FlattenSentinel(statements) if len(statements) > 1 else statements[0]

    # from x import a, b
    def leave_ImportFrom(self, original, updated):
        if updated.relative or updated.module is None:
            return updated
        module = dotted_name(updated.module)
        target = self.resolve(module)
        if target is not None:
            self.changes += 1
            return updated.with_changes(module=dotted_node(target))
        if isinstance(updated.names, cst.ImportStar):
            return updated
        # `from shared import poker_core`: each name is itself a moved module.
        statements, kept = [], []
        for alias in updated.names:
            leaf_name = alias.name.value if isinstance(alias.name, cst.Name) else dotted_name(alias.name)
            sub_target = self.resolve(f"{module}.{leaf_name}")
            if sub_target is None:
                kept.append(alias.with_changes(comma=cst.MaybeSentinel.DEFAULT))
                continue
            bound = alias.asname.name.value if alias.asname else leaf_name
            parent, leaf = sub_target.rsplit(".", 1)
            statements.append(cst.ImportFrom(
                module=dotted_node(parent),
                names=[cst.ImportAlias(name=cst.Name(leaf),
                                       asname=None if bound == leaf else cst.AsName(name=cst.Name(bound)))],
            ))
            self.changes += 1
        if not statements:
            return updated
        if kept:
            statements.insert(0, updated.with_changes(names=kept))
        return cst.FlattenSentinel(statements) if len(statements) > 1 else statements[0]

    # patch("module.attr"), importlib.import_module("module"), monkeypatch.setattr("module.attr", ...)
    def leave_Call(self, original, updated):
        try:
            function = dotted_name(updated.func)
        except TypeError:
            return updated
        if function.rsplit(".", 1)[-1] not in STRING_CALLS or not updated.args:
            return updated
        first = updated.args[0].value
        if not isinstance(first, cst.SimpleString) or first.prefix:
            return updated
        text = first.evaluated_value
        if not isinstance(text, str) or not text or " " in text:
            return updated
        target = resolve_dotted(text, self.resolve)
        if target is None:
            return updated
        quote = first.quote
        self.changes += 1
        new_first = first.with_changes(value=f"{quote}{target}{quote}")
        return updated.with_changes(args=[updated.args[0].with_changes(value=new_first), *updated.args[1:]])


def rewrite_source(source: str, resolve: Resolver, filename: str) -> tuple[str, int, list[str]]:
    module = cst.parse_module(source)
    rewriter = ImportRewriter(resolve, filename)
    result = module.visit(rewriter)
    return result.code, rewriter.changes, rewriter.problems


def rewrite_file(path: Path, resolve: Resolver) -> tuple[int, list[str]]:
    raw = path.read_bytes()
    source = raw.decode("utf-8")
    new, changes, problems = rewrite_source(source, resolve, str(path))
    if changes:
        path.write_bytes(new.encode("utf-8"))
    return changes, problems
