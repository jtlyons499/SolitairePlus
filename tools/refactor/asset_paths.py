"""Turn working-folder-relative asset/data paths into solitaireplus.app.paths calls.

    "assets/ui/x.png"                    -> str(paths.asset("ui/x.png"))
    f"assets/cards/{name}.png"           -> str(paths.asset(f"cards/{name}.png"))
    "assets/sounds/a_" + kind + ".wav"   -> str(paths.asset("sounds/a_" + kind + ".wav"))
    os.path.join("assets", "arcade", x)  -> str(paths.asset("arcade", x))
    Path("assets/poker/logo.png")        -> paths.asset("poker/logo.png")
    Path("assets/a") / name              -> paths.asset("a") / name
    "assets"                             -> str(paths.asset())
    (same for "data/...")

Values keep their type (str stays str, Path stays Path); they become absolute, so the
game no longer depends on the working folder. Adds `from solitaireplus.app import paths`.

    python tools/refactor/asset_paths.py FILE...   # rewrite in place, print a summary
"""
from __future__ import annotations

import sys
from pathlib import Path

import libcst as cst

ROOTS = {"assets": "asset", "data": "data"}
IMPORT_LINE = "from solitaireplus.app import paths\n"


def _helper_call(helper: str, args: list) -> cst.Call:
    return cst.Call(func=cst.Attribute(value=cst.Name("paths"), attr=cst.Name(helper)),
                    args=[cst.Arg(value=a) for a in args])


def _str_call(inner) -> cst.Call:
    return cst.Call(func=cst.Name("str"), args=[cst.Arg(value=inner)])


def _split_literal(text: str):
    """'assets/ui/x.png' -> ('asset', 'ui/x.png'); 'assets' -> ('asset', ''); else None."""
    for root, helper in ROOTS.items():
        if text == root or text == root + "/":
            return helper, ""
        if text.startswith(root + "/"):
            return helper, text[len(root) + 1:]
    return None


def _string_with(node: cst.SimpleString, text: str) -> cst.SimpleString:
    prefix = node.prefix
    quote = node.quote
    return cst.SimpleString(f"{prefix}{quote}{text}{quote}")


class AssetPathRewriter(cst.CSTTransformer):
    def __init__(self):
        self.changes = 0
        self.skipped: list[str] = []
        self._handled: set[int] = set()

    def _literal(self, node):
        if isinstance(node, cst.SimpleString) and "b" not in node.prefix.lower():
            value = node.evaluated_value
            if isinstance(value, str):
                return _split_literal(value)
        return None

    def _fstring(self, node):
        if isinstance(node, cst.FormattedString) and node.parts and isinstance(node.parts[0], cst.FormattedStringText):
            first = node.parts[0].value
            split = _split_literal(first) if "/" in first or first in ROOTS else None
            if split:
                helper, rest = split
                parts = list(node.parts)
                parts[0] = node.parts[0].with_changes(value=rest)
                if not rest:
                    parts = parts[1:]
                return helper, node.with_changes(parts=parts)
        return None

    def leave_SimpleString(self, original, updated):
        split = self._literal(updated)
        if split is None or id(original) in self._handled:
            return updated
        helper, rest = split
        self.changes += 1
        args = [_string_with(updated, rest)] if rest else []
        return _str_call(_helper_call(helper, args))

    def visit_ConcatenatedString(self, node):
        # "assets/career/residences/" "dingy_apartment.png": handled as one string below
        if self._concat_value(node) is not None:
            for part in self._concat_parts(node):
                self._handled.add(id(part))
        return True

    def leave_ConcatenatedString(self, original, updated):
        value = self._concat_value(original)
        if value is None:
            return updated
        helper, rest = _split_literal(value)
        self.changes += 1
        first = self._concat_parts(original)[0]
        return _str_call(_helper_call(helper, [_string_with(first, rest)] if rest else []))

    def _concat_parts(self, node):
        parts = []
        for side in (node.left, node.right):
            if isinstance(side, cst.ConcatenatedString):
                parts += self._concat_parts(side)
            else:
                parts.append(side)
        return parts

    def _concat_value(self, node):
        parts = self._concat_parts(node)
        if not all(isinstance(p, cst.SimpleString) and "b" not in p.prefix.lower() for p in parts):
            return None
        value = "".join(p.evaluated_value for p in parts)
        return value if _split_literal(value) else None

    def visit_FormattedString(self, node):
        return True

    def leave_FormattedString(self, original, updated):
        found = self._fstring(updated)
        if found is None:
            return updated
        helper, rest = found
        self.changes += 1
        return _str_call(_helper_call(helper, [rest]))

    def visit_BinaryOperation(self, node):
        # "assets/x_" + name + ".wav": mark the leftmost literal so it is handled here, not alone.
        left = node
        while isinstance(left, cst.BinaryOperation) and isinstance(left.operator, cst.Add):
            left = left.left
        if left is not node and self._literal(left) is not None and isinstance(node.operator, cst.Add):
            self._handled.add(id(left))
        return True

    def leave_BinaryOperation(self, original, updated):
        if not isinstance(original.operator, cst.Add):
            return updated
        chain_original, chain_updated = original, updated
        while isinstance(chain_original.left, cst.BinaryOperation) and isinstance(chain_original.left.operator, cst.Add):
            chain_original, chain_updated = chain_original.left, chain_updated.left
        leftmost_original = chain_original.left
        if id(leftmost_original) not in self._handled:
            return updated
        # only the outermost Add of the chain rewrites
        self._handled.discard(id(leftmost_original))
        split = self._literal(leftmost_original)
        helper, rest = split

        def replace_leftmost(node):
            if isinstance(node, cst.BinaryOperation) and isinstance(node.operator, cst.Add) and \
                    isinstance(node.left, (cst.BinaryOperation, cst.SimpleString)):
                if isinstance(node.left, cst.SimpleString):
                    return node.with_changes(left=_string_with(node.left, rest))
                return node.with_changes(left=replace_leftmost(node.left))
            return node

        self.changes += 1
        return _str_call(_helper_call(helper, [replace_leftmost(updated)]))

    def leave_Call(self, original, updated):
        func = updated.func
        name = None
        if isinstance(func, cst.Attribute) and isinstance(func.value, cst.Attribute):
            if isinstance(func.value.value, cst.Name) and func.value.value.value == "os" and \
                    func.value.attr.value == "path" and func.attr.value == "join":
                name = "os.path.join"
        elif isinstance(func, cst.Name) and func.value == "Path":
            name = "Path"
        if name is None or not original.args:
            return updated
        first_original = original.args[0].value
        split = self._literal(first_original)
        if split is None:
            return updated
        helper, rest = split
        inner_args = ([_string_with(first_original, rest)] if rest else []) + [a.value for a in updated.args[1:]]
        call = _helper_call(helper, inner_args)
        return call if name == "Path" else _str_call(call)


def _is_str_paths_call(node) -> bool:
    return (isinstance(node, cst.Call) and isinstance(node.func, cst.Name) and node.func.value == "str"
            and len(node.args) == 1 and isinstance(node.args[0].value, cst.Call)
            and isinstance(node.args[0].value.func, cst.Attribute)
            and isinstance(node.args[0].value.func.value, cst.Name)
            and node.args[0].value.func.value.value == "paths")


def _unwrap_str_paths_call(node):
    inner = node.args[0].value
    return inner.func.attr.value, [a.value for a in inner.args]


def add_import(code: str) -> str:
    if IMPORT_LINE in code:
        return code
    module = cst.parse_module(code)
    body = list(module.body)
    insert_at = 0
    # after the module docstring and any `from __future__` imports
    for index, statement in enumerate(body):
        if isinstance(statement, cst.SimpleStatementLine) and statement.body and \
                isinstance(statement.body[0], cst.Expr) and isinstance(statement.body[0].value, cst.SimpleString) \
                and index == 0:
            insert_at = 1
            continue
        if isinstance(statement, cst.SimpleStatementLine) and statement.body and \
                isinstance(statement.body[0], cst.ImportFrom) and statement.body[0].module is not None and \
                isinstance(statement.body[0].module, cst.Name) and statement.body[0].module.value == "__future__":
            insert_at = index + 1
            continue
        break
    body.insert(insert_at, cst.parse_statement(IMPORT_LINE))
    return module.with_changes(body=body).code


def rewrite_source(code: str) -> tuple[str, int]:
    module = cst.parse_module(code)
    rewriter = AssetPathRewriter()
    new = module.visit(rewriter).code
    if rewriter.changes:
        new = add_import(new)
    return new, rewriter.changes


def main(argv) -> int:
    total = 0
    for name in argv:
        path = Path(name)
        code = path.read_text(encoding="utf-8")
        new, changes = rewrite_source(code)
        if changes:
            path.write_text(new, encoding="utf-8")
            print(f"  {changes:4d}  {path}")
            total += changes
    print(f"{total} path(s) rewritten")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
