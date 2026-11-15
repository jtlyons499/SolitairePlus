"""Find game code by name, wherever it currently lives.

Many tests check or run real functions from the game without starting it.
They used to read ``main.py`` directly. The code is being moved out of
``main.py`` into the ``solitaireplus`` package, so tests ask this module
instead. It searches ``main.py`` and every ``solitaireplus/**/*.py`` file.

    from tests.support import locate

    locate.function_node("auto_save_career")      # the ast.FunctionDef
    locate.function("auto_save_career")           # its source text
    locate.function_nodes("a", "b")               # one node per name, in order
    locate.exec_functions(["a", "b"], env)        # define them in env (a fake namespace)
    locate.source_contains('"assets/arcade/bg.png"')
    locate.source()                               # all searched files' text, main.py first
    for node in locate.walk(): ...                # every AST node of every searched file
    locate.file_of("auto_save_career")            # Path of the file that defines it

Rules:
* Only top-level ``def`` statements count as functions.
* If one file defines a name twice, the LAST definition wins (that is the one
  Python uses at run time).
* If two different files define the same name, it is ambiguous: an error names
  both files. Pass ``path=`` (a Path or a path relative to the repo root) to pick.
"""
from __future__ import annotations

import ast
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Iterator

ROOT = Path(__file__).resolve().parents[2]


def source_files() -> list[Path]:
    """main.py first, then solitaireplus/**/*.py in a stable (sorted) order."""
    files = [ROOT / "main.py"]
    package = ROOT / "solitaireplus"
    if package.is_dir():
        files += sorted(p for p in package.rglob("*.py") if "__pycache__" not in p.parts)
    return [p for p in files if p.is_file()]


@lru_cache(maxsize=None)
def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def _tree(path: Path) -> ast.Module:
    return ast.parse(_text(path), filename=str(path))


def _resolve(path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


@lru_cache(maxsize=None)
def _definitions() -> dict[str, list[tuple[Path, ast.FunctionDef]]]:
    """name -> [(file, last top-level definition in that file), ...]."""
    found: dict[str, dict[Path, ast.FunctionDef]] = {}
    for path in source_files():
        for node in _tree(path).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                found.setdefault(node.name, {})[path] = node  # later definitions replace earlier ones
    return {name: list(per_file.items()) for name, per_file in found.items()}


def _lookup(name: str, path=None) -> tuple[Path, ast.FunctionDef]:
    candidates = _definitions().get(name, [])
    if path is not None:
        wanted = _resolve(path).resolve()
        candidates = [c for c in candidates if c[0].resolve() == wanted]
    if not candidates:
        where = f" in {path}" if path is not None else " in main.py or solitaireplus/"
        raise LookupError(f"no top-level function {name!r}{where}")
    if len(candidates) > 1:
        files = ", ".join(str(p.relative_to(ROOT)) for p, _ in candidates)
        raise LookupError(f"function {name!r} is defined in several files ({files}); pass path= to choose")
    return candidates[0]


def function_node(name: str, path=None) -> ast.FunctionDef:
    """The top-level ``def name`` node (see the module rules for duplicates)."""
    return _lookup(name, path)[1]


def function_nodes(*names: str, path=None) -> list[ast.FunctionDef]:
    """One node per name, in the order given. Raises if any is missing."""
    return [function_node(name, path) for name in names]


def file_of(name: str, path=None) -> Path:
    """The file that defines top-level function ``name``."""
    return _lookup(name, path)[0]


def function(name: str, path=None) -> str:
    """Source text of top-level function ``name`` (decorators not included)."""
    file, node = _lookup(name, path)
    return ast.get_source_segment(_text(file), node)


def compile_functions(*names: str, filename: str = "located functions", path=None):
    """A code object that defines the named functions when exec'd."""
    module = ast.Module(body=function_nodes(*names, path=path), type_ignores=[])
    return compile(module, filename, "exec")


# Module aliases that game code uses for shared state and for code moved out of main.py
# (``state.career_cash``, ``fonts.option_label_font``, ``legacy.auto_save_career()`` ...).
MODULE_ALIASES = {"state", "state_names", "legacy", "sounds", "window", "assets", "fonts", "cursors",
                  "buttons", "ui_text", "panels", "backgrounds"}


class EnvModule:
    """Stands in for a game module inside a fake namespace: attribute access reads and writes the
    namespace dict itself, so ``state.career_cash += 5`` changes ``env["career_cash"]``."""

    def __init__(self, env: dict):
        object.__setattr__(self, "_env", env)

    def __getattr__(self, name):
        try:
            return self._env[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name, value):
        self._env[name] = value


def namespace(env: dict, nodes=()) -> dict:
    """Make ``env`` usable as the fake global namespace of game code.

    For every module alias the given AST nodes use (``state.x``, ``fonts.y`` ...) and that env does
    not define itself, env gets an EnvModule backed by env, so tests keep writing plain names
    (``env["career_cash"]``) whether the code says ``career_cash`` or ``state.career_cash``. The
    old ``globals()`` calls became ``game_namespace()``; that returns env.
    """
    used = {node.value.id for root in nodes for node in ast.walk(root)
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)}
    called = {node.func.id for root in nodes for node in ast.walk(root)
              if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
    for alias in (used & MODULE_ALIASES) - set(env):
        env[alias] = EnvModule(env)
    if "game_namespace" in called and "game_namespace" not in env:
        env["game_namespace"] = lambda: env
    return env


def exec_functions(names: Iterable[str], env: dict, filename: str = "located functions", path=None) -> dict:
    """Define the named functions inside ``env`` (a fake global namespace) and return env."""
    if isinstance(names, str):
        names = [names]
    nodes = function_nodes(*names, path=path)
    namespace(env, nodes)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), filename, "exec"), env)
    return env


def exec_nodes(nodes, env: dict, filename: str = "located code") -> dict:
    """Exec arbitrary located AST statements (e.g. one branch of a function) in a fake namespace."""
    nodes = list(nodes)
    namespace(env, nodes)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), filename, "exec"), env)
    return env


def source() -> str:
    """Text of every searched file joined together, main.py first."""
    return "\n".join(_text(path) for path in source_files())


def source_contains(snippet: str) -> bool:
    """True if any searched file contains ``snippet`` exactly."""
    return any(snippet in _text(path) for path in source_files())


def trees() -> list[tuple[Path, ast.Module]]:
    """(file, parsed module) for every searched file."""
    return [(path, _tree(path)) for path in source_files()]


def walk() -> Iterator[ast.AST]:
    """Every AST node of every searched file (ast.walk order, file by file)."""
    for _, tree in trees():
        yield from ast.walk(tree)
