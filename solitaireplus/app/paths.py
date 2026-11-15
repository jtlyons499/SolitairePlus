"""One place that knows where game files are, from source and in the packaged build.

From source the root is the repository folder; in the packaged game it is the
``SolitairePlus_Data`` folder PyInstaller unpacks next to the exes. Every asset and data
path in the game is built here, so nothing depends on the current working folder.
"""
from __future__ import annotations

import sys
from pathlib import Path


def root() -> Path:
    """Folder that contains assets/, data/ and multiplayer/."""
    bundle = getattr(sys, "_MEIPASS", None)
    if bundle:
        return Path(bundle).resolve()
    return Path(__file__).resolve().parents[2]


def asset(*parts) -> Path:
    return root().joinpath("assets", *parts)


def data(*parts) -> Path:
    return root().joinpath("data", *parts)


def resolve(path) -> Path:
    """A path from a data file ("assets/npcs/x.png"): relative ones are taken from the root."""
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root() / candidate
