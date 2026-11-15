"""Write the Windows version resources that PyInstaller embeds in each exe.

Usage:
    python tools/write_version_info.py --all     # every exe (what the build scripts run)
    python tools/write_version_info.py           # just the game exe
    python tools/write_version_info.py --name SolitaireNet --description "..." \\
        --version-file netservice/__init__.py --output build_version_info_net.txt

Each exe is stamped with the version of ITS OWN code: the game exe with
version.py, SolitaireNet.exe with netservice/__init__.py. Releases reuse an
unchanged exe from the previous release (tools/make_manifest.py), so
Explorer's "File version" shows the release in which that exe last changed.
The version shown in the game is always the installed release.

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
VERSION_LINE = re.compile(r"""^__version__\s*=\s*["']([^"']+)["']""", re.MULTILINE)

# Every exe this project builds: (name, description, version file, output file).
EXES = [
    ("SolitairePlus", "Solitaire+", "version.py", "build_version_info.txt"),
    ("SolitaireNet", "Solitaire+ online play service", "netservice/__init__.py", "build_version_info_net.txt"),
    ("SolitaireUpdater", "Solitaire+ updater", "updater/__init__.py", "build_version_info_updater.txt"),
]


def read_version(version_file: Path | str = "version.py") -> str:
    """Read __version__ from a .py file without importing it."""
    text = (ROOT / version_file).read_text(encoding="utf-8")
    match = VERSION_LINE.search(text)
    if not match:
        raise SystemExit(f"{version_file} does not define __version__")
    return match.group(1)


def version_parts(label: str, build_number: int = 0) -> tuple[int, int, int, int]:
    match = SEMVER.match(label)
    if not match:
        raise SystemExit(
            f"Version {label!r} is not MAJOR.MINOR.PATCH[-prerelease] "
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
    parser.add_argument("--all", action="store_true", help="write the resource for every exe")
    parser.add_argument("--name", default="SolitairePlus", help="exe name without .exe")
    parser.add_argument("--description", default="Solitaire+", help="FileDescription shown in Explorer")
    parser.add_argument("--version-file", default="version.py", help=".py file holding __version__")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    if args.all:
        jobs = [(name, description, vfile, ROOT / out) for name, description, vfile, out in EXES]
    else:
        jobs = [(args.name, args.description, args.version_file, args.output)]
    build_number = int(os.environ.get("SOLITAIRE_BUILD_NUMBER", "0") or 0) % 65536
    for name, description, version_file, output in jobs:
        version = read_version(version_file)
        label = version + os.environ.get("SOLITAIRE_BUILD_SUFFIX", "")
        Path(output).write_text(render(label, version_parts(version, build_number), name, description),
                                encoding="utf-8")
        print(f"Wrote {Path(output).name} for {name}.exe {label}")


if __name__ == "__main__":
    main(sys.argv[1:])
