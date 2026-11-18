# Releasing Solitaire+

**Who this is for:** whoever publishes a new version (people and AI assistants). Signing is set up once and
explained in [CODE_SIGNING.md](CODE_SIGNING.md); installing and updating for players is in
[INSTALLING.md](INSTALLING.md).

> **In short:** merge your changes into `main` through a pull request, then run
> `.\tools\release.ps1 -Version X.Y.Z` on your PC. It tests, bumps the version, tags and pushes. GitHub builds,
> signs and publishes the release, and players' games offer the update on their next launch. Never edit
> `version.py` by hand, never create or move a tag by hand, and never reuse a version number.

## Who does what

| Where | What happens | Tool |
|---|---|---|
| **Your PC** | 1. Unit tests and the asset preflight run. Any failure stops everything; nothing is committed. | `tools/release.ps1` |
| Your PC | 2. Optional `-Build`: builds the three exes locally (unsigned) as a quick smoke test. | same script, calls `build_release.ps1` |
| Your PC | 3. Writes the version into `version.py`, turns CHANGELOG's **[Unreleased]** into `[X.Y.Z] - date`, commits "Release vX.Y.Z", tags `vX.Y.Z`, and pushes after asking Y/N. | same script |
| **GitHub (cloud)** | 4. Re-runs the tests, builds the three exes, reuses unchanged ones from the last release, signs, scans with Defender, writes the signed manifest and the delta, builds and signs the installer, publishes the Release. | `.github/workflows/release-windows.yml`, started by the tag |
| **Players** | 5. The game checks for a new release when it starts and shows an "Update to X.Y.Z" button on the main menu. | `SolitaireUpdater.exe` |

Every pull request and every push to `main` also runs the tests and an **unsigned** build on GitHub (the
"Actions" tab; the build is downloadable there for 14 days), except changes that only touch `.md` files or
`docs/`. Only a version tag publishes anything.

## Everyday work (before any release)

1. Work on a branch, never directly on `main`.
2. For every change a player would notice, add a short line under **[Unreleased]** in `CHANGELOG.md` (New /
   Fixes / Changes). The release notes on GitHub are copied from there.
3. Run the tests: `.venv\Scripts\python.exe tools\run_tests.py` (see [TESTING.md](TESTING.md)).
4. Open a pull request. Wait for the GitHub checks to pass, then merge.

If you changed anything in `netservice/` or `updater/`, also raise the `__version__` in that folder's
`__init__.py` (for example 1.1.0 → 1.1.1). Those are versions of those programs only, not the game version.

## Release checklist (people)

1. Your changes are merged into `main` and the GitHub checks on `main` passed.
2. You played the game from a local build (`.\build_release.ps1`, then `dist\SolitairePlus\SolitairePlus.exe`),
   including the areas you changed. For window or display changes, also run
   `.venv\Scripts\python.exe tools\window_check.py packaged` and watch the screen.
3. `CHANGELOG.md` **[Unreleased]** describes the changes in words players understand.
4. On your PC: `git checkout main`, `git pull`.
5. Pick the version (see "Version numbers" below), then run:

   ```powershell
   .\tools\release.ps1 -Version 0.0.8
   ```

   It stops with a plain message at the first problem (wrong branch, uncommitted changes, `main` behind GitHub,
   tag already used, empty changelog, a failing test). Fix that and run it again.
6. Answer **Y** when it asks to push. (Answer N to stop; it prints how to undo the local commit and tag.)
7. Open the repository's **Actions** tab and watch "Build Windows Release" for the tag until it finishes.
8. When it is green, open **Releases**: the new release should list `SolitairePlus-Setup-X.Y.Z.exe`,
   `Solitaire-Windows.zip`, `manifest.json`, `manifest.json.p7s`, `SolitairePlus-X.Y.Z-delta-from-<old>.zip`
   (when there was a previous release with a manifest), `SolitairePlus-Publisher.cer` and `SHA256SUMS.txt`.
9. Check the update path: start an installed older version. Within a few seconds the main menu shows
   "Update to X.Y.Z". Click it; the game closes, updates and reopens. Options → Updates → **Check now** then
   says "You have the latest version (X.Y.Z)".

Options of `tools/release.ps1`:

| Option | What it does |
|---|---|
| `-Version 0.0.8` | Required. The new version, without a leading "v". |
| `-Build` | Also builds the exes locally before tagging (slower; a smoke test). |
| `-NoPush` | Does everything except the push. Undo with `git tag -d v0.0.8; git reset --hard HEAD~1`. |

## Release checklist (AI assistants)

You prepare releases; a person publishes them.

1. Never edit `version.py`, never create, move or delete a git tag, and never push to `main` directly.
2. Do put the player-visible changes under **[Unreleased]** in `CHANGELOG.md` as part of the pull request that
   makes them.
3. Before saying a change is ready, run `tools/run_tests.py` and report its result word for word (see
   [TESTING.md](TESTING.md)). Never add a test to `tests/KNOWN_FAILURES.txt` to make it pass.
4. If you changed `netservice/` or `updater/`, raise that folder's `__version__`.
5. Only run `tools/release.ps1` when the person asks you to, and let them answer the final Y/N prompt themselves.
   If you run it with `-NoPush`, say so and give them the undo command.
6. Never handle the signing key, its password, or the GitHub secrets.

## Version numbers

Versions follow Semantic Versioning, `MAJOR.MINOR.PATCH`: 0.0.7 → 0.0.8 for fixes and small features, 0.1.0 for
a big update. Letter suffixes like `0.0.6b` are not allowed (the updater cannot compare them).

**Test versions (pre-releases).** A version with a suffix, such as `0.0.8-beta.1`, is published as a GitHub
*pre-release*. The in-game updater ignores pre-releases, so players never get it; testers download the
installer from the release page by hand. Later `0.0.8-beta.2` and finally `0.0.8` follow as usual.

**Hotfix.** For an urgent fix: branch from `main`, fix, pull request, merge, then release the next patch version
(0.0.8 → 0.0.9). There is no separate hotfix process.

## Undoing a bad release

Never delete a release, re-use a version number or move a tag: players who already updated would not be offered
the "same" version again, and the updater only ever moves forward.

Instead, release a **higher** version that undoes the problem: revert the bad change on a branch
(`git revert <commit>`), merge it, and run `tools/release.ps1` with the next version. Players get it as a
normal update.

If the GitHub workflow **failed** for a tag (nothing was published), fix the cause:
- a temporary problem (network, a GitHub outage): on the Actions tab, **Re-run failed jobs**;
- a real problem in the code or the build: fix it on `main` and release the next version number. The broken tag
  stays as it is.

If it failed only at the last step, "Create or update the Release", re-running the workflow is safe: it replaces
the release's files.

## Which part of the game changes when you edit what

Players' updaters only download files that changed. The release workflow reuses each program from the previous
release when its source did not change (`tools/make_manifest.py`).

| You edit | What players download | Notes |
|---|---|---|
| `main.py`, anything in `solitaireplus/` | `SolitairePlus.exe` | |
| `netservice/` | `SolitaireNet.exe` | Raise `netservice/__init__.py` `__version__` |
| `updater/` | `SolitaireUpdater.exe` | Raise `updater/__init__.py` `__version__`. The **old** updater installs this update, so a new updater only takes effect for the release after |
| `multiplayer/*.py` | Only those `.py` files (they ship as loose files) | A new import they need may have to go into `hiddenimports` in `SolitairePlus.spec`; the packaged self-test catches this |
| `assets/`, `data/` | Only the changed files | |
| `version.py` (done by `release.ps1`) | Only `version.py` | A version bump alone does not rebuild any exe |
| `requirements.txt`, `SolitairePlus.spec`, `requirements-build.txt` | Everything (all exes and the Python runtime) | Avoid in small updates |

## What the GitHub workflow checks, and common failures

| Step | Fails when | What to do |
|---|---|---|
| Check tag matches version.py | Someone tagged by hand | Release the next version with `tools/release.ps1` |
| Run unit tests | A test fails on GitHub's PC | Read the log; run `tools/run_tests.py` locally |
| Self-test packaged game | A multiplayer file imports a module PyInstaller didn't include | Add it to `hiddenimports` in `SolitairePlus.spec` ([TESTING.md](TESTING.md)) |
| Prepare signing certificate | The `SIGNING_CERT_PFX_BASE64` secret is missing | [CODE_SIGNING.md](CODE_SIGNING.md), part 1 |
| Sign freshly built programs | The certificate is not listed in `updater/trusted_publishers.py`, or the password is wrong | [CODE_SIGNING.md](CODE_SIGNING.md), part 1 step 3 |
| Scan build with Microsoft Defender | Defender flagged a file | Do not publish. Find what changed (often a packaging change) before trying again |

## Multiplayer and mixed versions

Online rooms work best when everyone has the same version. If a release changes what the game sends over the
network (`multiplayer/room_protocol.py`, `party_authority.py`, `netservice/protocol.py`), say in the changelog
that everyone should update before playing together.
