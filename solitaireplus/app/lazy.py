"""Late-bound module references.

Some modules were cut out of the old main.py but still refer to one another (and to
solitaireplus.legacy) from inside functions. Importing them at the top would run their
start-up code out of order (for example, loading cursor images before the window exists).
A LazyModule looks the module up when an attribute is first used, which is always after
start-up has finished. Temporary: the restructure replaces these with plain imports as code
leaves solitaireplus.legacy.
"""
import importlib
import sys


class LazyModule:
    __slots__ = ("_name",)

    def __init__(self, name):
        object.__setattr__(self, "_name", name)

    def _module(self):
        return sys.modules.get(self._name) or importlib.import_module(self._name)

    def __getattr__(self, attribute):
        return getattr(self._module(), attribute)

    def __setattr__(self, attribute, value):
        setattr(self._module(), attribute, value)

    def __repr__(self):
        return f"<lazy module {self._name}>"


def lazy(name):
    return LazyModule(name)
