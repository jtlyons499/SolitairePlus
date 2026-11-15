"""Semantic Versioning (2.0) comparison, shared by the updater and tools/release_helpers.py.

    is_newer("0.0.8", "0.0.7")          -> True
    is_newer("0.0.8", "0.0.8-beta.2")   -> True   (a release beats its pre-releases)
    is_newer("0.0.8-beta.10", "0.0.8-beta.9") -> True
"""
from __future__ import annotations

import re

SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$")


def parse(version: str) -> tuple:
    """Return a sortable key following Semantic Versioning precedence rules."""
    match = SEMVER.match(str(version).strip())
    if not match:
        raise ValueError(f"{version!r} is not a valid version (expected e.g. 0.0.8 or 0.0.8-beta.1)")
    core = tuple(int(match.group(i)) for i in (1, 2, 3))
    pre = match.group(4)
    if pre is None:
        return core + ((1,),)  # a release sorts after any of its pre-releases
    parts = tuple((0, int(p), "") if p.isdigit() else (1, 0, p) for p in pre.split("."))
    return core + ((0,) + parts,)


def is_valid(version: str) -> bool:
    try:
        parse(version)
        return True
    except ValueError:
        return False


def is_newer(candidate: str, current: str) -> bool:
    return parse(candidate) > parse(current)
