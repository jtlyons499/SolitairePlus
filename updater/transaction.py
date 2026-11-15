"""All-or-nothing file replacement with a journal, so an interrupted update can be undone.

Order of operations (apply):
  1. Every new file is already downloaded and SHA-256 checked in .update/staging.
  2. Each file that will be overwritten or removed is COPIED to .update/backup
     (and the current manifest.json too).
  3. journal.json is written: "this update is in progress, here is what it touches".
  4. New files are moved into place; removed files are deleted.
  5. The new manifest.json is written. This is the "update finished" marker.
  6. journal.json, staging and backup are deleted.

If anything fails during 4-5, rollback() puts the backups back and deletes
newly added files. If the PC loses power during 4-5, the journal is still
there next time; the game notices and runs `SolitaireUpdater.exe --recover`,
which performs the same rollback.

Files in use: Windows will not overwrite or delete a file a program is
using (for example the updater's own exe and the runtime DLLs it loaded),
but it does allow RENAMING it. Such a file is renamed to
"<name>.updating-old", the new file takes its place, and the old name is
listed in pending-delete.txt. The game and the updater delete those leftovers
the next time they start. (An earlier design ran a copy of the updater from
%TEMP% instead; Microsoft Defender's machine-learning scanner flagged that
pattern as malware, so it must not come back.)
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from . import config
from .plan import Plan, UpdateError, safe_relpath

# While these run, their exe files are locked: a sure sign the game is still open.
GAME_PROCESS_FILES = (config.GAME_EXE, "SolitaireNet.exe")


def work_dir(install_dir: Path) -> Path:
    return install_dir / config.WORK_DIR


def journal_path(install_dir: Path) -> Path:
    return work_dir(install_dir) / "journal.json"


def staging_dir(install_dir: Path) -> Path:
    return work_dir(install_dir) / "staging"


def backup_dir(install_dir: Path) -> Path:
    return work_dir(install_dir) / "backup"


def locked_files(install_dir: Path, plan: Plan | None = None) -> list[str]:
    """The game's own programs that are still running (their files cannot be opened for writing)."""
    locked = []
    for name in GAME_PROCESS_FILES:
        target = install_dir / name
        if not target.is_file():
            continue
        try:
            with target.open("r+b"):
                pass
        except PermissionError:
            locked.append(name)
        except OSError:
            pass
    return locked


# ----------------------------------------------------------------------------- leftovers of in-use files

def _pending_file(install_dir: Path) -> Path:
    return install_dir / config.PENDING_DELETE


def _remember_for_deletion(install_dir: Path, path: Path) -> None:
    with _pending_file(install_dir).open("a", encoding="utf-8") as stream:
        stream.write(path.relative_to(install_dir).as_posix() + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def cleanup_pending(install_dir: Path) -> int:
    """Delete files renamed aside by an earlier update. Returns how many are still in use."""
    listing = _pending_file(install_dir)
    if not listing.is_file():
        return 0
    remaining = []
    for line in listing.read_text(encoding="utf-8").splitlines():
        relpath = line.strip()
        if not relpath or not relpath.endswith(config.OLD_SUFFIX) or ".." in relpath.split("/"):
            continue
        target = install_dir / relpath
        try:
            if target.exists():
                target.unlink()
        except OSError:
            remaining.append(relpath)
    if remaining:
        listing.write_text("\n".join(remaining) + "\n", encoding="utf-8")
    else:
        listing.unlink()
    return len(remaining)


def _move_aside(install_dir: Path, target: Path) -> None:
    """Rename an in-use file out of the way (allowed by Windows even while it runs)."""
    aside = target.with_name(target.name + config.OLD_SUFFIX)
    counter = 1
    while aside.exists():
        try:
            aside.unlink()
            break
        except OSError:
            counter += 1
            aside = target.with_name(f"{target.name}.{counter}{config.OLD_SUFFIX}")
    _remember_for_deletion(install_dir, aside)
    os.replace(target, aside)


def _put(install_dir: Path, source: Path, target: Path) -> None:
    try:
        os.replace(source, target)
    except PermissionError:
        _move_aside(install_dir, target)
        os.replace(source, target)


def _remove(install_dir: Path, target: Path) -> None:
    try:
        target.unlink()
    except PermissionError:
        _move_aside(install_dir, target)


# ----------------------------------------------------------------------------- apply / rollback

def _write_json(path: Path, data: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, indent=1), encoding="utf-8")
    with temporary.open("rb+") as stream:
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def apply(install_dir: Path, plan: Plan, new_manifest_bytes: bytes) -> None:
    staging, backup = staging_dir(install_dir), backup_dir(install_dir)
    if backup.exists():
        shutil.rmtree(backup)
    backup.mkdir(parents=True)

    added = []
    for relpath in plan.changed + plan.removed + [config.MANIFEST_NAME]:
        source = install_dir / relpath
        if source.is_file():
            destination = backup / relpath
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        elif relpath in plan.changed:
            added.append(relpath)
    journal = {"from": plan.version_from, "to": plan.version_to, "changed": plan.changed,
               "removed": plan.removed, "added": added}
    _write_json(journal_path(install_dir), journal)

    try:
        for relpath in plan.changed:
            target = install_dir / safe_relpath(relpath)
            target.parent.mkdir(parents=True, exist_ok=True)
            _put(install_dir, staging / relpath, target)
        for relpath in plan.removed:
            target = install_dir / safe_relpath(relpath)
            if target.exists():
                _remove(install_dir, target)
        manifest_tmp = install_dir / (config.MANIFEST_NAME + ".new")
        manifest_tmp.write_bytes(new_manifest_bytes)
        os.replace(manifest_tmp, install_dir / config.MANIFEST_NAME)
    except OSError as error:
        rollback(install_dir)
        raise UpdateError(f"The update could not be applied ({error.__class__.__name__}); "
                          "your previous version was restored. Close every Solitaire+ window and try again.") from None
    finish(install_dir)


def rollback(install_dir: Path) -> bool:
    """Undo a half-applied update. Returns True if there was something to undo."""
    journal_file = journal_path(install_dir)
    if not journal_file.is_file():
        return False
    try:
        journal = json.loads(journal_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        journal = {}
    backup = backup_dir(install_dir)
    for relpath in journal.get("added", []):
        target = install_dir / safe_relpath(relpath)
        if target.exists():
            _remove(install_dir, target)
    for relpath in journal.get("changed", []) + journal.get("removed", []) + [config.MANIFEST_NAME]:
        saved = backup / relpath
        if saved.is_file():
            target = install_dir / safe_relpath(relpath)
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(saved, target)
            except PermissionError:
                _move_aside(install_dir, target)
                shutil.copy2(saved, target)
    finish(install_dir)
    return True


def finish(install_dir: Path) -> None:
    """Remove the journal first (the commit point), then the temporary folders."""
    journal_file = journal_path(install_dir)
    if journal_file.exists():
        journal_file.unlink()
    shutil.rmtree(work_dir(install_dir), ignore_errors=True)


def needs_recovery(install_dir: Path) -> bool:
    return journal_path(install_dir).is_file()
