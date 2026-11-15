"""Where updates come from, and which signing certificates are trusted."""
from __future__ import annotations

GITHUB_REPOSITORY = "jtlyons499/SolitairePlus"

# "latest" never points at a pre-release, so testers' beta builds are never offered to players.
DEFAULT_MANIFEST_URL = f"https://github.com/{GITHUB_REPOSITORY}/releases/latest/download/manifest.json"
RELEASE_DOWNLOAD_BASE = f"https://github.com/{GITHUB_REPOSITORY}/releases/download"

GAME_EXE = "SolitairePlus.exe"
UPDATER_EXE = "SolitaireUpdater.exe"
MANIFEST_NAME = "manifest.json"
SIGNATURE_NAME = "manifest.json.p7s"
WORK_DIR = ".update"  # inside the install folder: downloads, staging, backup, journal
# Files that were in use during an update are renamed to <name> + this suffix and
# deleted the next time the game or updater starts (see transaction.py).
OLD_SUFFIX = ".updating-old"
PENDING_DELETE = "pending-delete.txt"   # in the install folder: the list of those files

USER_AGENT = "SolitairePlusUpdater/1.0"
DOWNLOAD_TIMEOUT = 30          # seconds without any data before giving up
MAX_MANIFEST_BYTES = 8 << 20   # 8 MB


def trusted_publishers() -> list[dict]:
    """[{"name": ..., "thumbprint": ...}] from updater/trusted_publishers.py.

    The thumbprint is the SHA-1 fingerprint Windows shows for the signing
    certificate (40 hex characters). docs/CODE_SIGNING.md explains how to get it.
    Several entries are allowed so the certificate can be replaced safely.
    The list is compiled into SolitaireUpdater.exe, so a download cannot change it.
    """
    from .trusted_publishers import PUBLISHERS
    publishers = []
    for entry in PUBLISHERS:
        thumbprint = normalize_thumbprint(entry.get("thumbprint", ""))
        if len(thumbprint) == 40:
            publishers.append({"name": str(entry.get("name", "Solitaire+")), "thumbprint": thumbprint})
    return publishers


def normalize_thumbprint(value: str) -> str:
    return "".join(ch for ch in str(value or "").upper() if ch in "0123456789ABCDEF")
