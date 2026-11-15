"""Read manifests and work out exactly which files an update must change."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from . import config
from .versions import is_valid


class UpdateError(Exception):
    """A problem the player should see (the text is shown as-is)."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_relpath(relpath: str) -> str:
    """Reject anything that could write outside the install folder."""
    path = PurePosixPath(relpath)
    if (not relpath or "\\" in relpath or path.is_absolute() or ":" in relpath
            or any(part in ("", ".", "..") for part in path.parts)
            or path.parts[0].lower() == config.WORK_DIR):
        raise UpdateError(f"The update lists an unsafe file path ({relpath[:80]!r}). Nothing was changed.")
    return relpath


def parse_manifest(raw: bytes) -> dict:
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError):
        raise UpdateError("The update information could not be read.") from None
    if not isinstance(manifest, dict) or manifest.get("schema") != 1:
        raise UpdateError("This update needs a newer updater. Please download the latest installer.")
    if not is_valid(manifest.get("version", "")):
        raise UpdateError("The update information has an invalid version number.")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise UpdateError("The update information lists no files.")
    for relpath, info in files.items():
        safe_relpath(relpath)
        if not (isinstance(info, dict) and isinstance(info.get("sha256"), str) and len(info["sha256"]) == 64
                and isinstance(info.get("size"), int)):
            raise UpdateError("The update information is damaged.")
    return manifest


def installed_manifest(install_dir: Path) -> dict | None:
    path = install_dir / config.MANIFEST_NAME
    try:
        return parse_manifest(path.read_bytes())
    except (OSError, UpdateError):
        return None


def installed_version(install_dir: Path) -> str:
    """The installed release: manifest.json, else the loose version.py, else 0.0.0."""
    manifest = installed_manifest(install_dir)
    if manifest:
        return manifest["version"]
    for candidate in (install_dir / "SolitairePlus_Data" / "version.py", install_dir / "version.py"):
        try:
            for line in candidate.read_text(encoding="utf-8").splitlines():
                if line.startswith("__version__"):
                    value = line.split("=", 1)[1].strip().strip("\"'")
                    if is_valid(value):
                        return value
        except OSError:
            continue
    return "0.0.0"


@dataclass
class Plan:
    version_from: str
    version_to: str
    changed: list[str] = field(default_factory=list)   # files to write (new or different)
    removed: list[str] = field(default_factory=list)   # files the new version no longer has
    use_delta: bool = False

    @property
    def empty(self) -> bool:
        return not self.changed and not self.removed


def make_plan(install_dir: Path, new: dict, progress=None) -> Plan:
    """Compare the real files on disk (not just the old manifest) with the new manifest."""
    old = installed_manifest(install_dir)
    plan = Plan(installed_version(install_dir), new["version"])
    files = new["files"]
    for index, (relpath, info) in enumerate(sorted(files.items())):
        target = install_dir / relpath
        if not target.is_file() or target.stat().st_size != info["size"] or sha256_file(target) != info["sha256"]:
            plan.changed.append(relpath)
        if progress:
            progress(index + 1, len(files))
    if old:
        plan.removed = sorted(p for p in old["files"] if p not in files and (install_dir / safe_relpath(p)).is_file())
    delta = new.get("delta") or {}
    delta_paths = set(delta.get("paths", []))
    plan.use_delta = bool(delta.get("asset")) and delta.get("from") == plan.version_from and set(plan.changed) <= delta_paths
    return plan
