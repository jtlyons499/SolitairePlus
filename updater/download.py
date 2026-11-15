"""HTTPS downloads (standard library only). file:// URLs also work, which tests use."""
from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path

from . import config
from .plan import UpdateError


def _open(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT})
    return urllib.request.urlopen(request, timeout=config.DOWNLOAD_TIMEOUT)


def fetch_bytes(url: str, limit: int = config.MAX_MANIFEST_BYTES, missing_ok: bool = False) -> bytes | None:
    try:
        with _open(url) as response:
            data = response.read(limit + 1)
    except urllib.error.HTTPError as error:
        if missing_ok and error.code == 404:
            return None
        raise UpdateError(f"The update server answered {error.code}. Try again later.") from None
    except (urllib.error.URLError, OSError) as error:
        if missing_ok and isinstance(getattr(error, "reason", None), FileNotFoundError):
            return None
        if missing_ok and isinstance(error, FileNotFoundError):
            return None
        raise UpdateError("Could not reach the update server. Check your internet connection.") from None
    if len(data) > limit:
        raise UpdateError("The update information is unexpectedly large. Nothing was changed.")
    return data


def fetch_file(url: str, destination: Path, progress=None) -> Path:
    """Download to destination (via a .part file). progress(done_bytes, total_bytes_or_0)."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    try:
        with _open(url) as response, partial.open("wb") as out:
            total = int(response.headers.get("Content-Length") or 0)
            done = 0
            while True:
                block = response.read(1 << 16)
                if not block:
                    break
                out.write(block)
                done += len(block)
                if progress:
                    progress(done, total)
        partial.replace(destination)
    except urllib.error.HTTPError as error:
        raise UpdateError(f"Download failed (server answered {error.code}). Try again later.") from None
    except (urllib.error.URLError, OSError):
        raise UpdateError("The download was interrupted. Check your internet connection and try again.") from None
    finally:
        if partial.exists():
            try:
                partial.unlink()
            except OSError:
                pass
    return destination
