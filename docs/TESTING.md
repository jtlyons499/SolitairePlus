# Testing Solitaire+

This page is for maintainers and for AI coding assistants (ChatGPT/Codex, Claude, etc.).
It explains how to run the automated tests, what they cover, and how to read a failure.

## TL;DR

```powershell
# one-time setup (from the repository folder)
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# run every test (about 1-2 minutes)
.\.venv\Scripts\python.exe tools\run_tests.py
```

The last lines tell you the result:

* `PASSED - all non-quarantined tests passed.` means you're fine.
* `FAILED - these must be fixed before releasing:` is followed by a list of exactly what broke.

You rarely need to run this by hand: `tools/release.ps1` and `build_release.ps1` run it automatically
and stop if anything fails, and GitHub runs it again on every pull request and every release.

## Where tests run

| When | Where | What happens on failure |
|---|---|---|
| You run `tools\run_tests.py` | your PC | You see the failure. Nothing else happens. |
| You run `build_release.ps1` | your PC | The build stops before PyInstaller. |
| You run `tools\release.ps1 -Version X` | your PC | The release stops **before** anything is committed, tagged or pushed. |
| You open or update a pull request, or push to `main` | GitHub (cloud) | The PR shows a red ❌ and no build is produced. |
| A `vX.Y.Z` tag is pushed (by `release.ps1`) | GitHub (cloud) | **Nothing is published to players.** |

GitHub Actions is free for public repositories, so this costs nothing.

## The two test suites

| Suite name | Folder | Tests | Import path |
|---|---|---|---|
| `game` | `tests/` | single-player game code (career, poker, arcade, saves, assets, ...) | the test file's folder, `tests/`, then the repository root |
| `multiplayer` | `multiplayer/tests/` | multiplayer tables, relay server, the game's network client, profiles | the test file's folder, `multiplayer/tests/`, `multiplayer/`, then the root |

Test files are found **recursively**: any `test_*.py` in the suite folder or a subfolder (for example
`tests/career/test_x.py`), except helper folders (`tests/support/`, `fixtures/`). A test's id is always
`<file name>.Class.test` (or `<file name>.test_function` for a plain pytest-style function), whatever folder the
file is in, so two test files in one suite must not share a name; the runner stops with an error if they do.
Both `unittest.TestCase` classes and plain module-level `test_*` functions (no arguments) are run. (Before
2026-11-15 the plain functions were silently skipped.)

Tests that check or run real game code without starting the game (for example, running `auto_save_career` in a
fake namespace, or checking that a sound name is wired up) must not read `main.py` directly, because that code is
moving into the `solitaireplus/` package. Use the code locator instead: `from tests.support import locate`, then
`locate.function_node(name)`, `locate.exec_functions([...], env)`, `locate.source_contains(snippet)` or
`locate.source()`. It searches `main.py` and `solitaireplus/**/*.py`; see the docstring in
`tests/support/locate.py`.

Moved game code reads shared variables as `state.career_cash` (and constants as `fonts.x`, `legacy.y`, ...).
`locate.exec_functions` and `locate.exec_nodes` make a fake namespace work anyway: each module alias the code uses
becomes a stand-in object backed by the env dict, so a test still sets and checks `env["career_cash"]`. Tests that
compile AST nodes themselves call `locate.namespace(env, nodes)` first.

The updater (`updater/`, built as `SolitaireUpdater.exe`) is tested in the `game` suite by `tests/test_updater.py`
(planning, downloading, applying, rolling back an update, using fake releases on disk via `file://` URLs) and
`tests/test_updater_signatures.py` (the real Windows signature check, using a throwaway certificate created in memory;
skipped on PCs without Windows PowerShell).

Saves: `tests/test_profile_recovery.py` covers damaged saves (fall back to the `.bak` copy), saves from newer
versions (refused), and the migration chain.

Relay room codes and guessing protection: `multiplayer/tests/test_relay_codes.py`. Encrypted WebSocket play:
`multiplayer/tests/test_relay_websocket.py` (TCP and WebSocket players in one room, plus a real `SolitaireNet` process).

The network service (`netservice/`, built as `SolitaireNet.exe`) is tested in the `game` suite by
`tests/test_netservice.py`, which uses small fake servers on `127.0.0.1` (no internet needed). The real
game path (game → `SolitaireNet` child process → relay server) is tested in `multiplayer/tests/test_net_client.py`.

The multiplayer suite **must** have `multiplayer/` ahead of the root on the import path. `multiplayer/` contains
its own versions of some modules (for example `texas_holdem.py`), and those must win. The runner handles this; don't
run `python -m unittest discover` from the root yourself, because it picks the wrong modules.

Useful options:

```powershell
.\.venv\Scripts\python.exe tools\run_tests.py --suite game          # only one suite
.\.venv\Scripts\python.exe tools\run_tests.py --skip-quarantined    # faster: don't retry quarantined tests marked HANGS
```

To run a single test file or test while debugging, use the runner's worker mode. It sets the correct
import path and starts pygame headless:

```powershell
.\.venv\Scripts\python.exe tools\run_tests.py --worker game test_runtime_support
.\.venv\Scripts\python.exe tools\run_tests.py --worker multiplayer test_relay.RelayTests.test_pair_forward_disconnect
.\.venv\Scripts\python.exe tools\run_tests.py --worker game test_arcade_audio.test_arcade_cabinets_have_optional_individual_music_hooks
.\.venv\Scripts\python.exe tools\run_tests.py --worker game tests\test_runtime_support.py
```

The target is a file name (found in any subfolder), a dotted test id, or the path of a test file.

## How the runner works

`tools/run_tests.py` does the following:

1. Runs **each test file in its own Python process** with a 5-minute limit. A test that hangs fails that file
   instead of freezing everything.
2. Starts pygame in **headless mode** (`SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy`) before tests run, the same
   way the game does at startup. No window opens and no sound plays.
3. Sets `SOLITAIRE_NET_INPROCESS=1`. Room and table tests then run the network connector code **inside** the test
   process instead of starting a `SolitaireNet` child process for every simulated player. That's faster and avoids
   start-up timing races. Only `test_net_client.py` starts real child processes, which is what the game does.
4. Treats tests listed in `tests/KNOWN_FAILURES.txt` as **quarantined**: they still run, and their results are
   reported, but they never make the run fail.
5. Exits with code `0` only when every non-quarantined test passed. The release scripts and GitHub check this
   exit code.

## Quarantined tests (`tests/KNOWN_FAILURES.txt`)

When automated testing was switched on (November 2026), 14 tests were **already broken on `main`**, and one more
(`test_relay...test_online_table_hand`) was found to fail about 1 run in 5. Most were
outdated tests rather than game bugs: they expected older menus or numbers, or wrote images to a folder that only
existed on the original author's AI tool. So that releases weren't blocked from day one, each one is listed in
`tests/KNOWN_FAILURES.txt` with a one-line reason.

The runner reports them like this (non-blocking):

```text
  still fails game:test_poker_recap.RecapTests.test_recap_render_...  (hard-coded /workspace/scratch path)
  NOW PASSES  multiplayer:test_x.Tests.test_y -> remove it from tests/KNOWN_FAILURES.txt
```

Rules for the list:

* **Never add a test to the list just to get a release through.** A new failure means something broke.
* If the runner says **NOW PASSES**, delete that line from the file.
* Each line is `suite:module.Class.test_name   # reason`. A reason starting with `HANGS` means the test is run alone
  with a 30-second limit instead of inside its file. A reason starting with `FLAKY` means it fails only some of the
  time, so one pass doesn't prove it's fixed. The runner prints `passed (flaky...)` instead of `NOW PASSES`.
* `multiplayer:test_six_seat.SixRelayTests.test_six_clients_and_late_join` **may be a real bug** (six-seat late
  joiners). The designer should look at it.

Fixing the rest is on the future refactor sprint list.

## Reading a failure

A blocking failure looks like this (an illustrative example, not a real test):

```text
  FAIL     test_profile_save_lock: 1 new failure(s) of 3 tests (0s)
      ======================================================================
      FAIL: test_locked_save_creates_recovery (test_profile_save_lock.SaveLockTests...)
      Traceback (most recent call last):
        File "...\tests\test_profile_save_lock.py", line 40, in test_locked_save_creates_recovery
          self.assertTrue(recovery.exists())
      AssertionError: False is not true
...
=== Result ===
FAILED - these must be fixed before releasing:
  - game:test_profile_save_lock.SaveLockTests.test_locked_save_creates_recovery
```

How to read it:

1. The **last line of the traceback** says what went wrong (`AssertionError` means the game gave a different
   answer than the test expected; `NameError` or `AttributeError` usually means something was renamed or removed).
2. The **`File ... line N`** lines show where. The first one inside `tests/` is the check that failed. Lines in
   game files show the code that ran.
3. Decide which side is wrong:
   * The game code broke something it shouldn't have. **Fix the game code.**
   * The behaviour changed on purpose (for example a rebalance). **Update the test** to the new expected
     behaviour and say so in the commit message.
4. Re-run `tools\run_tests.py` until it prints `PASSED`.

Other result types:

| Message | Meaning | What to do |
|---|---|---|
| `TIMEOUT  test_x (300s)` | A test in that file never finished, usually waiting for a window or input that never comes. | Find the test that hangs (run it with `--worker`) and fix it, or quarantine it with a `HANGS` reason if it was already broken. |
| `CRASH  test_x` | The file couldn't even be imported, usually a syntax error or a missing module. | Read the printed error. The file and line are shown. |
| `NOW PASSES ...` | A quarantined test works again. | Delete its line from `tests/KNOWN_FAILURES.txt`. |

## Packaged self-tests (after the exe is built)

The unit tests run on the source code. Two more checks run on the **built** game, in `build_release.ps1` and on
GitHub:

| Command | What it proves |
|---|---|
| `dist\SolitairePlus\SolitaireNet.exe --selftest` | The network service starts, and all its connectors load. |
| `dist\SolitairePlus\SolitaireUpdater.exe --selftest` | The updater starts, including its window toolkit (exit code 0). |
| `dist\SolitairePlus\SolitairePlus.exe --multiplayer --selftest --selftest-report report.txt` | Every multiplayer module imports inside the real packaged game. |

Why the second one matters: the files in `multiplayer/` ship as loose `.py` files, so PyInstaller can't see what
they import. If a multiplayer change starts using a standard-library module the game exe doesn't contain, multiplayer
would crash **only in the packaged game**, never from source. The report then contains a line like:

```text
FAILED room_view: ModuleNotFoundError: No module named 'fractions'
```

**Fix:** add that module name (here `fractions`) to the `hiddenimports` list in `SolitairePlus.spec`, rebuild, and run
the self-test again. Lines starting with `ok` passed. The last line says `PASSED` or `FAILED`.

## Asset preflight

`tools/release_preflight.py` loads every image in `assets/` and every JSON file in `data/`, and checks that the
required files exist. It runs after the tests in the same places. A failure prints the broken file's path. Missing
*optional* cosmetics are listed but don't fail.

## Screenshot and replay safety net (restructure work)

Two tools prove that moving code around changed nothing a player can see:

```
.venv\Scripts\python.exe tools\screen_harness.py compare            # every screen, pixel by pixel
.venv\Scripts\python.exe tools\replay.py compare                    # 18 scripted playthroughs
.venv\Scripts\python.exe tools\screen_harness.py compare --baseline HEAD~1 --scene casino_roulette
```

- `compare` checks out the baseline commit (default `HEAD`) in a git worktree under
  `.harness_out/worktrees/`, runs every script there and in the working tree, and compares.
  It prints `IDENTICAL n/n` or lists what differs; diff images (changed pixels in red) go to
  `.harness_out/scene-diff/` or `.harness_out/journey-diff/`. Nothing in `.harness_out/` is
  committed. Both sides render on the same machine, so fonts can't cause false differences.
  Rendered baselines are cached per commit and harness version.
- `selfcheck` renders the working tree twice and must say `IDENTICAL` (proves a new script is
  deterministic). `render` / `run` just produce the PNGs (`list` shows the names).
- `screen_harness.py` has about 60 scenes (one or more screenshots per screen, including open
  dialogs, mid-hand poker and results). `replay.py` has 18 journeys; at each checkpoint it
  records the state, cash, XP, level, rating, career day and fans, plus a screenshot, and
  `compare` checks the values too.
- How it works: each script runs `main.py` in a child process with the dummy SDL drivers, a
  1366x768 window, a virtual clock (exactly 1/60 s per frame), fixed random seeds, scripted
  mouse/keyboard input, a fake music player and a temporary `LOCALAPPDATA` holding
  `tests/support/fixtures/profile_1.json` (rebuild it with `screen_harness.py make-fixture`).
  Scripts run inside `pygame.display.flip()`, one step per frame, and read or change game state
  through a probe that finds names in `main.py` or in `solitaireplus.app.state`.
- Scripts live in `tools/harness/` (`scenes*.py`, `journeys.py`; API in `scripts.py` and
  `sim.py`). Use only function and variable names that stay stable through the restructure.
- A fix that changes a screen on purpose shows up as `DIFFERS`; list those scenes in the commit
  message. A move commit must be `IDENTICAL`.

## Notes for AI assistants

* Always run `python tools/run_tests.py` after changing code. Treat any `FAILED` result as blocking.
* Don't edit `tests/KNOWN_FAILURES.txt` to hide a failure you caused.
* Don't run `python -m unittest discover` from the repository root (wrong import order for multiplayer).
* New tests go in `tests/` (single-player) or `multiplayer/tests/` (multiplayer), named `test_*.py`, using
  `unittest`. They must not open real windows, play real audio, write outside a temporary folder, or need the internet.
