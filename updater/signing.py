"""Check that an update really comes from the Solitaire+ developers.

Two checks, both compared against the thumbprints in trusted_publishers.py:

1. manifest.json must carry a valid detached signature (manifest.json.p7s).
   The manifest lists the SHA-256 of every file, so this one signature
   protects every asset, DLL and exe in the update.
2. Each new .exe must carry an Authenticode signature from a trusted
   publisher (what Windows shows as "Verified publisher").

Comparing thumbprints works even if the player never imported the
certificate. Windows' own trust store is not needed for this check.

The checks run through Windows PowerShell (built into Windows 10/11) using
.NET's signature classes, so the updater needs no extra libraries. If
PowerShell cannot run, the update counts as unverified and the player sees
the two warnings. It never silently counts as verified.
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from . import config

_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$result = @{ manifest = $null; exes = @{} }
try {
  Add-Type -AssemblyName System.Security
  $content = [IO.File]::ReadAllBytes($env:SP_MANIFEST)
  $signature = [IO.File]::ReadAllBytes($env:SP_SIGNATURE)
  $info = New-Object System.Security.Cryptography.Pkcs.ContentInfo -ArgumentList (,$content)
  $cms = New-Object System.Security.Cryptography.Pkcs.SignedCms -ArgumentList $info, $true
  $cms.Decode($signature)
  $cms.CheckSignature($true)
  $cert = $cms.SignerInfos[0].Certificate
  $result.manifest = @{ ok = $true; thumbprint = $cert.Thumbprint; subject = $cert.Subject }
} catch {
  $result.manifest = @{ ok = $false; error = $_.Exception.Message }
}
foreach ($path in ($env:SP_EXES -split '\|')) {
  if (-not $path) { continue }
  try {
    $s = Get-AuthenticodeSignature -LiteralPath $path
    $thumb = $null; $subject = $null
    if ($s.SignerCertificate) { $thumb = $s.SignerCertificate.Thumbprint; $subject = $s.SignerCertificate.Subject }
    $result.exes[$path] = @{ status = [string]$s.Status; thumbprint = $thumb; subject = $subject }
  } catch {
    $result.exes[$path] = @{ status = 'Error'; error = $_.Exception.Message }
  }
}
$result | ConvertTo-Json -Depth 5 -Compress
"""

# Get-AuthenticodeSignature statuses that mean "no usable signature".
# (UnknownError/NotTrusted just mean Windows does not trust the certificate yet;
# the thumbprint comparison decides that instead.)
_BROKEN = {"NotSigned", "HashMismatch", "NotSupportedFileFormat", "Incompatible", "Error"}


@dataclass
class Verification:
    verified: bool
    problems: list[str] = field(default_factory=list)
    found: list[str] = field(default_factory=list)   # who actually signed, for the warning text

    def details(self) -> str:
        expected = config.trusted_publishers()
        lines = ["Expected publisher:"]
        lines += [f"  {p['name']} (thumbprint {p['thumbprint']})" for p in expected] or \
                 ["  (none configured in this updater yet)"]
        lines.append("Found:")
        lines += [f"  {item}" for item in self.found] or ["  no signature"]
        lines.append("Problems:")
        lines += [f"  - {problem}" for problem in self.problems]
        return "\n".join(lines)


def _run_powershell(manifest: Path, signature: Path, exes: list[Path]) -> dict:
    encoded = base64.b64encode(_SCRIPT.encode("utf-16-le")).decode("ascii")
    env = dict(os.environ, SP_MANIFEST=str(manifest), SP_SIGNATURE=str(signature),
               SP_EXES="|".join(str(path) for path in exes))
    done = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded],
        env=env, capture_output=True, timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    text = done.stdout.decode("utf-8", "replace").strip().splitlines()
    return json.loads(text[-1]) if text else {}


def verify(manifest: Path, signature: Path | None, exes: list[Path], runner=_run_powershell) -> Verification:
    trusted = {p["thumbprint"] for p in config.trusted_publishers()}
    result = Verification(verified=False)
    if not trusted:
        result.problems.append("This updater has no trusted publisher configured.")
    has_signature = signature is not None and signature.is_file()
    if not has_signature:
        result.problems.append("The update's file list (manifest.json) is not signed.")
        signature = manifest.with_name("missing.p7s")
    try:
        report = runner(manifest, signature, exes)
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        result.problems.append(f"Signatures could not be checked on this PC ({error.__class__.__name__}).")
        return result

    manifest_report = report.get("manifest") or {}
    manifest_ok = False
    if has_signature and manifest_report.get("ok"):
        thumbprint = config.normalize_thumbprint(manifest_report.get("thumbprint"))
        result.found.append(f"manifest.json signed by {manifest_report.get('subject')} (thumbprint {thumbprint})")
        if thumbprint in trusted:
            manifest_ok = True
        else:
            result.problems.append("manifest.json is signed by a certificate that is not trusted.")
    elif has_signature:
        result.problems.append("manifest.json's signature is invalid: " + str(manifest_report.get("error", ""))[:120])

    exes_ok = True
    exe_reports = report.get("exes") or {}
    for exe in exes:
        entry = exe_reports.get(str(exe)) or {}
        status = entry.get("status", "Error")
        thumbprint = config.normalize_thumbprint(entry.get("thumbprint"))
        if status in _BROKEN or not thumbprint:
            exes_ok = False
            result.problems.append(f"{exe.name} is not signed ({status}).")
        elif thumbprint not in trusted:
            exes_ok = False
            result.found.append(f"{exe.name} signed by {entry.get('subject')} (thumbprint {thumbprint})")
            result.problems.append(f"{exe.name} is signed by a certificate that is not trusted.")
        else:
            result.found.append(f"{exe.name} signed by {entry.get('subject')}")
    result.verified = bool(trusted) and manifest_ok and exes_ok
    return result
