"""Small helpers used by tools/release.ps1 and the GitHub workflow.

    python tools/release_helpers.py current              # print the version in version.py
    python tools/release_helpers.py check 0.0.8          # is 0.0.8 a valid next version?
    python tools/release_helpers.py bump 0.0.8           # write version.py + date the CHANGELOG section
    python tools/release_helpers.py notes 0.0.8          # print that version's CHANGELOG section
    python tools/release_helpers.py verify-tag v0.0.8    # CI: does the tag match version.py?

Exit code 0 = OK; anything else = stop, and the message says why.
"""
from __future__ import annotations

import datetime as _dt
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "version.py"
CHANGELOG = ROOT / "CHANGELOG.md"

VERSION_LINE = re.compile(r"""^__version__\s*=\s*["']([^"']+)["']""", re.MULTILINE)
UNRELEASED = "## [Unreleased]"

# One implementation of the version rules, shared with the in-game updater.
sys.path.insert(0, str(ROOT))
from updater.versions import is_newer, parse  # noqa: E402


def current_version() -> str:
    match = VERSION_LINE.search(VERSION_FILE.read_text(encoding="utf-8"))
    if not match:
        raise SystemExit("version.py does not contain __version__")
    return match.group(1)


def changelog_section(version: str) -> str | None:
    text = CHANGELOG.read_text(encoding="utf-8")
    pattern = re.compile(r"^## \[" + re.escape(version) + r"\][^\n]*\n(.*?)(?=^## \[|\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(text)
    return match.group(1).strip() if match else None


def unreleased_body(text: str) -> str:
    start = text.index(UNRELEASED) + len(UNRELEASED)
    following = text.find("\n## [", start)
    return text[start:following if following != -1 else len(text)].strip()


def cmd_check(new: str) -> None:
    parse(new)
    current = current_version()
    # Releasing the version already in version.py is allowed (first release after setting it by hand).
    if new != current and not is_newer(new, current):
        raise SystemExit(f"{new} is not newer than the current version {current}")
    text = CHANGELOG.read_text(encoding="utf-8")
    if UNRELEASED not in text:
        raise SystemExit(f"CHANGELOG.md has no '{UNRELEASED}' heading")
    if not unreleased_body(text):
        raise SystemExit("CHANGELOG.md 'Unreleased' section is empty - describe the changes first")
    print(f"OK: {current} -> {new}")


def cmd_bump(new: str) -> None:
    cmd_check(new)
    source = VERSION_FILE.read_text(encoding="utf-8")
    VERSION_FILE.write_text(VERSION_LINE.sub(f'__version__ = "{new}"', source, count=1), encoding="utf-8")
    text = CHANGELOG.read_text(encoding="utf-8")
    today = _dt.date.today().isoformat()
    text = text.replace(UNRELEASED, f"{UNRELEASED}\n\n## [{new}] - {today}", 1)
    CHANGELOG.write_text(text, encoding="utf-8")
    print(f"version.py and CHANGELOG.md updated to {new}")


def cmd_notes(version: str) -> None:
    section = changelog_section(version)
    print(section if section else f"Solitaire+ {version}")


def cmd_verify_tag(tag: str) -> None:
    current = current_version()
    if tag != f"v{current}":
        raise SystemExit(f"Tag {tag} does not match version.py ({current}); expected v{current}. "
                         "Use tools/release.ps1 to make releases.")
    parse(current)
    print(f"OK: tag {tag} matches version.py")


def main(argv: list[str]) -> None:
    commands = {"check": cmd_check, "bump": cmd_bump, "notes": cmd_notes, "verify-tag": cmd_verify_tag}
    if argv[:1] == ["current"]:
        print(current_version())
        return
    if len(argv) != 2 or argv[0] not in commands:
        raise SystemExit(__doc__)
    try:
        commands[argv[0]](argv[1])
    except ValueError as error:
        raise SystemExit(str(error))


if __name__ == "__main__":
    main(sys.argv[1:])
