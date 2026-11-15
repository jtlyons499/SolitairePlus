<#
.SYNOPSIS
  Make a new Solitaire+ release. This is the ONLY supported way to release.

.DESCRIPTION
  Run this on your PC from the repository folder, on the main branch, after
  your changes are merged and hand-tested, with CHANGELOG.md "[Unreleased]" filled in.

  What it does, in order. It stops at the first problem.
    1. Checks you are on an up-to-date, clean main branch and the tag is new.
    2. Checks the version number and that CHANGELOG.md has release notes.
    3. Runs every unit test and the asset preflight (tools/run_tests.py, tools/release_preflight.py).
    4. (Optional, -Build) builds the game locally as a quick smoke test.
    5. Updates version.py and CHANGELOG.md, commits "Release vX.Y.Z", and creates tag vX.Y.Z.
    6. Asks Y/N, then pushes the commit and tag to GitHub.

  After the push, GitHub (cloud) re-runs the tests, builds, signs, and
  publishes the Release. Players' games see the update on their next launch.
  Watch progress on the repository's "Actions" tab.

.PARAMETER Version
  The new version, for example 0.0.8 or 0.0.8-beta.1 (no leading "v").

.PARAMETER Build
  Also build the exe locally before tagging (slower, optional).

.PARAMETER NoPush
  Do everything except the final push. Undo with:
  git tag -d vX.Y.Z; git reset --hard HEAD~1

.EXAMPLE
  .\tools\release.ps1 -Version 0.0.8
#>
param(
    [Parameter(Mandatory = $true)][string]$Version,
    [switch]$Build,
    [switch]$NoPush
)

$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent
Set-Location $repo
$python = Join-Path $repo ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Project Python not found: $python`nCreate it once with:  py -3.14 -m venv .venv" }
$Version = $Version.TrimStart("v")
$tag = "v$Version"

function Invoke-Step([string]$Title, [scriptblock]$Command) {
    Write-Host "`n=== $Title ===" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "STOPPED: $Title failed. Nothing was committed, tagged or pushed." }
}

Invoke-Step "Checking git state" {
    $branch = (git rev-parse --abbrev-ref HEAD).Trim()
    if ($branch -ne "main") { Write-Host "You are on '$branch'. Releases are made from 'main' after your PR is merged."; $global:LASTEXITCODE = 1; return }
    if (git status --porcelain) { Write-Host "You have uncommitted changes. Commit or stash them first."; $global:LASTEXITCODE = 1; return }
    git fetch origin main --tags --quiet
    if ((git rev-parse HEAD).Trim() -ne (git rev-parse origin/main).Trim()) { Write-Host "Your main is not the same as GitHub's. Run: git pull"; $global:LASTEXITCODE = 1; return }
    if (git tag --list $tag) { Write-Host "Tag $tag already exists. Pick a higher version; never reuse a tag."; $global:LASTEXITCODE = 1; return }
    $global:LASTEXITCODE = 0
}

Invoke-Step "Checking version and changelog" { & $python tools/release_helpers.py check $Version }
Invoke-Step "Installing dependencies" { & $python -m pip install --disable-pip-version-check -q -r requirements.txt -r requirements-build.txt }
Invoke-Step "Running unit tests" { & $python tools/run_tests.py --skip-quarantined }
Invoke-Step "Checking game assets (preflight)" { & $python tools/release_preflight.py }

if ($Build) {
    Invoke-Step "Local smoke-test build" { & (Join-Path $repo "build_release.ps1") -SkipTests; $global:LASTEXITCODE = 0 }
}

Invoke-Step "Updating version.py and CHANGELOG.md" { & $python tools/release_helpers.py bump $Version }
Invoke-Step "Committing and tagging" {
    git add version.py CHANGELOG.md
    git commit -m "Release $tag" --quiet
    if ($LASTEXITCODE -ne 0) { return }
    git tag -a $tag -m "Solitaire+ $tag"
}

if ($NoPush) {
    Write-Host "`nCommitted and tagged $tag locally (not pushed). To undo: git tag -d $tag; git reset --hard HEAD~1" -ForegroundColor Yellow
    exit 0
}

$answer = Read-Host "`nPush $tag to GitHub now? This publishes the release to players. (Y/N)"
if ($answer -notmatch '^[Yy]') {
    Write-Host "Not pushed. To undo the local release commit: git tag -d $tag; git reset --hard HEAD~1" -ForegroundColor Yellow
    exit 0
}
Invoke-Step "Pushing to GitHub" { git push --atomic origin main $tag }
Write-Host "`nPushed $tag. GitHub is now building and publishing it." -ForegroundColor Green
Write-Host "Watch it on the repository's Actions tab; the Release appears when the workflow finishes."
