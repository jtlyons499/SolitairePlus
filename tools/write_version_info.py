"""Write the Windows version resource that PyInstaller embeds in an exe.

The version always comes from version.py (the single source of truth).

Usage (defaults produce the game exe's resource):
    python tools/write_version_info.py
    python tools/write_version_info.py --name SolitaireNet --description "Solitaire+ network service" --output build_version_info_net.txt

Optional environment variables, used by CI for non-release builds:
    SOLITAIRE_BUILD_NUMBER  integer placed in the 4th FileVersion field (e.g. the CI run number)
    SOLITAIRE_BUILD_SUFFIX  text appended to ProductVersion (e.g. "+ci.123")
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "build_version_info.txt"

# MAJOR.MINOR.PATCH with an optional pre-release such as -beta.1 or -rc.2
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$")


def read_version() -> str:
    """Read __version__ from version.py without importing the game."""
    text = (ROOT / "version.py").read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
    if not match:
        raise SystemExit("version.py does not define __version__")
    return match.group(1)


def version_parts(label: str, build_number: int = 0) -> tuple[int, int, int, int]:
    match = SEMVER.match(label)
    if not match:
        raise SystemExit(
            f"version.py has {label!r}, which is not MAJOR.MINOR.PATCH[-prerelease] "
            "(for example 0.0.7 or 0.0.7-beta.1)"
        )
    major, minor, patch = (int(match.group(i)) for i in (1, 2, 3))
    return major, minor, patch, build_number


def tuple_text(parts: tuple[int, int, int, int]) -> str:
    return ", ".join(str(value) for value in parts)


def render(label: str, parts: tuple[int, int, int, int], name: str, description: str) -> str:
    numeric = ".".join(str(value) for value in parts)
    return f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({tuple_text(parts)}),
    prodvers=({tuple_text(parts)}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName', 'Solitaire+'),
          StringStruct('FileDescription', '{description}'),
          StringStruct('FileVersion', '{numeric}'),
          StringStruct('InternalName', '{name}'),
          StringStruct('OriginalFilename', '{name}.exe'),
          StringStruct('ProductName', 'Solitaire+'),
          StringStruct('ProductVersion', '{label}')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", default="SolitairePlus", help="exe name without .exe")
    parser.add_argument("--description", default="Solitaire+", help="FileDescription shown in Explorer")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    version = read_version()
    build_number = int(os.environ.get("SOLITAIRE_BUILD_NUMBER", "0") or 0) % 65536
    parts = version_parts(version, build_number)
    label = version + os.environ.get("SOLITAIRE_BUILD_SUFFIX", "")

    args.output.write_text(render(label, parts, args.name, args.description), encoding="utf-8")
    print(f"Wrote {args.output.name} for {args.name}.exe {label}")


if __name__ == "__main__":
    main(sys.argv[1:])
