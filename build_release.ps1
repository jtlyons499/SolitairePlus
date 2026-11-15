<#
.SYNOPSIS
  Build Solitaire+ for Windows on this PC (unsigned), the same way GitHub does.

.DESCRIPTION
  1. Uses the project's .venv Python (create it once: py -3.14 -m venv .venv).
  2. Installs the pinned dependencies (requirements.txt + requirements-build.txt).
  3. Runs all unit tests (tools/run_tests.py) and the asset preflight. Any failure stops the build.
  4. Writes the Windows version resource from version.py and runs PyInstaller.
  5. Puts a playable ZIP in release\Solitaire-Windows.zip.

  Local builds are NOT signed. Official, signed builds are made only by GitHub
  when a version tag is pushed (see docs/RELEASING.md).

.PARAMETER SkipTests
  Skip step 3. Only use this when tools/release.ps1 has just run the tests.

.EXAMPLE
  .\build_release.ps1
#>
param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Project Python not found: $python`nCreate it once with:  py -3.14 -m venv .venv"
}

function Invoke-Step([string]$Title, [scriptblock]$Command) {
    Write-Host "`n=== $Title ===" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "$Title failed (exit code $LASTEXITCODE)" }
}

Invoke-Step "Installing dependencies" {
    & $python -m pip install --disable-pip-version-check -q -r requirements.txt -r requirements-build.txt
}

if (-not $SkipTests) {
    Invoke-Step "Running unit tests" { & $python tools/run_tests.py --skip-quarantined }
    Invoke-Step "Checking game assets (preflight)" { & $python tools/release_preflight.py }
}

Invoke-Step "Writing version information" { & $python tools/write_version_info.py }
Invoke-Step "Building with PyInstaller" { & $python -m PyInstaller --noconfirm --clean "SolitairePlus.spec" }

$dist = Join-Path $PSScriptRoot "dist\SolitairePlus"
if (-not (Test-Path (Join-Path $dist "SolitairePlus.exe"))) { throw "Build did not produce dist\SolitairePlus\SolitairePlus.exe" }

Write-Host "`n=== Packaging ZIP ===" -ForegroundColor Cyan
$stage = Join-Path $PSScriptRoot "release\Solitaire-Windows"
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
New-Item -ItemType Directory -Force -Path $stage | Out-Null
Copy-Item -Path "$dist\*" -Destination $stage -Recurse -Force
Copy-Item -Path "PLAYING.txt" -Destination $stage -Force
$archive = Join-Path $PSScriptRoot "release\Solitaire-Windows.zip"
Compress-Archive -Path "$stage\*" -DestinationPath $archive -Force
Write-Host "Done. Playable folder: $dist"
Write-Host "Shareable ZIP (unsigned test build): $archive"
