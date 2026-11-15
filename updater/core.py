"""The update flow, independent of any window (ui.py draws it; tests drive it directly).

The `ui` object passed in needs these methods:
    status(text)                    show what is happening
    progress(fraction or None)      0.0-1.0, or None for "busy"
    confirm_unverified(details)     the two warnings; True only if the player accepted BOTH
    retry_locked(files)             files are in use; True = player clicked Retry
    done(text) / error(text)        final message
"""
from __future__ import annotations

import logging
import shutil
import time
import urllib.parse
import zipfile
from dataclasses import dataclass
from pathlib import Path

from . import config, signing, transaction
from .download import fetch_bytes, fetch_file
from .plan import Plan, UpdateError, installed_version, make_plan, parse_manifest, safe_relpath, sha256_file
from .versions import is_newer

log = logging.getLogger("updater")


@dataclass
class Release:
    manifest: dict
    manifest_bytes: bytes
    signature_bytes: bytes | None
    asset_base: str      # URL prefix for this release's other files

    @property
    def version(self) -> str:
        return self.manifest["version"]


def asset_base_for(manifest_url: str, version: str) -> str:
    # The default "latest" URL could move to a newer release mid-download, so pin the exact tag.
    if manifest_url == config.DEFAULT_MANIFEST_URL:
        return f"{config.RELEASE_DOWNLOAD_BASE}/v{version}/"
    return urllib.parse.urljoin(manifest_url, ".")


def fetch_release(manifest_url: str) -> Release:
    raw = fetch_bytes(manifest_url)
    manifest = parse_manifest(raw)
    base = asset_base_for(manifest_url, manifest["version"])
    signature = fetch_bytes(base + config.SIGNATURE_NAME, limit=1 << 20, missing_ok=True)
    return Release(manifest, raw, signature, base)


# ----------------------------------------------------------------------------- check (used by the game)

def check(install_dir: Path, manifest_url: str) -> dict:
    current = installed_version(install_dir)
    try:
        release = fetch_release(manifest_url)
    except UpdateError as error:
        return {"status": "error", "installed": current, "message": str(error)}
    status = "update_available" if is_newer(release.version, current) else "up_to_date"
    return {"status": status, "installed": current, "latest": release.version}


# ----------------------------------------------------------------------------- apply

def run_update(install_dir: Path, manifest_url: str, ui, repair: bool = False) -> int:
    """Returns 0 = updated or already current, 1 = failed, 2 = cancelled by the player."""
    try:
        return _run_update(install_dir, manifest_url, ui, repair)
    except UpdateError as error:
        log.warning("Update failed: %s", error)
        ui.error(str(error))
        return 1
    except Exception:
        log.exception("Unexpected updater error")
        ui.error("Something went wrong while updating. Nothing was changed, or your previous version was "
                 "restored. Details are in %LOCALAPPDATA%\\SimpleSolitaire\\logs\\updater.log.")
        return 1


def _run_update(install_dir: Path, manifest_url: str, ui, repair: bool) -> int:
    if transaction.needs_recovery(install_dir):
        ui.status("Undoing an unfinished update…")
        transaction.rollback(install_dir)

    ui.status("Checking for updates…")
    ui.progress(None)
    release = fetch_release(manifest_url)
    current = installed_version(install_dir)
    if not repair and not is_newer(release.version, current):
        ui.done(f"Solitaire+ is up to date (version {current}).")
        return 0

    ui.status("Checking your installed files…")
    plan = make_plan(install_dir, release.manifest, progress=lambda done, total: ui.progress(done / total))
    log.info("Update %s -> %s: %d changed, %d removed, delta=%s",
             plan.version_from, plan.version_to, len(plan.changed), len(plan.removed), plan.use_delta)
    work = transaction.work_dir(install_dir)
    try:
        if not plan.empty:
            _download_and_stage(install_dir, release, plan, ui)
        if not _verified_or_accepted(install_dir, release, plan, ui):
            ui.done("Update cancelled. Nothing was changed.")
            return 2
        while True:
            locked = transaction.locked_files(install_dir, plan)
            if not locked:
                break
            if not ui.retry_locked(locked):
                ui.done("Update cancelled. Nothing was changed.")
                return 2
        ui.status("Installing…")
        ui.progress(None)
        transaction.apply(install_dir, plan, release.manifest_bytes)
    finally:
        if not transaction.needs_recovery(install_dir):
            shutil.rmtree(work, ignore_errors=True)
    log.info("Updated to %s", release.version)
    ui.done(f"Solitaire+ is now version {release.version}.")
    return 0


def _download_and_stage(install_dir: Path, release: Release, plan: Plan, ui) -> None:
    work = transaction.work_dir(install_dir)
    staging = transaction.staging_dir(install_dir)
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True)
    asset = release.manifest["delta"]["asset"] if plan.use_delta else release.manifest.get("full_asset", "Solitaire-Windows.zip")
    ui.status(f"Downloading update {release.version}…")
    archive_path = fetch_file(release.asset_base + urllib.parse.quote(asset), work / "download" / asset,
                              progress=lambda done, total: ui.progress(done / total if total else None))
    ui.status("Checking the download…")
    files = release.manifest["files"]
    needed = set(plan.changed)
    try:
        with zipfile.ZipFile(archive_path) as archive:
            names = {info.filename: info for info in archive.infolist() if not info.is_dir()}
            missing = needed - set(names)
            if missing:
                raise UpdateError(f"The download is missing {len(missing)} file(s). Nothing was changed.")
            for index, relpath in enumerate(sorted(needed)):
                target = staging / safe_relpath(relpath)
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(names[relpath]) as source, target.open("wb") as out:
                    shutil.copyfileobj(source, out, 1 << 20)
                if sha256_file(target) != files[relpath]["sha256"]:
                    raise UpdateError(f"A downloaded file is damaged ({relpath}). Nothing was changed.")
                ui.progress((index + 1) / len(needed))
    except zipfile.BadZipFile:
        raise UpdateError("The download is damaged. Nothing was changed; please try again.") from None


def _verified_or_accepted(install_dir: Path, release: Release, plan: Plan, ui) -> bool:
    ui.status("Checking the update's signature…")
    ui.progress(None)
    work = transaction.work_dir(install_dir)
    work.mkdir(parents=True, exist_ok=True)
    manifest_file = work / config.MANIFEST_NAME
    manifest_file.write_bytes(release.manifest_bytes)
    signature_file = None
    if release.signature_bytes:
        signature_file = work / config.SIGNATURE_NAME
        signature_file.write_bytes(release.signature_bytes)
    exes = [transaction.staging_dir(install_dir) / p for p in plan.changed if p.lower().endswith(".exe")]
    result = signing.verify(manifest_file, signature_file, exes)
    if result.verified:
        log.info("Signatures verified")
        return True
    log.warning("Update NOT verified:\n%s", result.details())
    accepted = ui.confirm_unverified(result.details())
    if accepted:
        log.warning("Player accepted both warnings and installed the unverified update %s", release.version)
    return bool(accepted)


def recover(install_dir: Path) -> bool:
    return transaction.rollback(install_dir)


def wait_for_exit(pid: int, timeout: float = 60.0) -> bool:
    """Wait for the game to close (Windows). Returns True once it has exited."""
    try:
        import ctypes
        SYNCHRONIZE = 0x00100000
        handle = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, False, int(pid))
        if not handle:
            return True  # already gone
        try:
            return ctypes.windll.kernel32.WaitForSingleObject(handle, int(timeout * 1000)) == 0
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    except (AttributeError, OSError):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            time.sleep(0.25)
        return True
