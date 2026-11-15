# Restructure sprint: phase reports

Reports for the phases in [RESTRUCTURE_BRIEF.md](RESTRUCTURE_BRIEF.md), newest at the bottom.

Dan's decisions before the sprint started (2026-11-15) changed two rules of the brief:

- **No stop between phases.** Dan is away, so each phase is committed locally (never pushed)
  and reported here instead of waiting for a go-ahead. Work stops only on a real blocker.
- **B86 does not wait for the audit table.** The shared poker rules are unified; deliberate
  differences (Stud's bring-in, Blind Man's Bluff's single card, Five-O's columns) stay. The
  table is recorded here for review. The original maintainer added: "NPC behavior should be
  consistent between all variants, including holding grudges and behaving differently based
  on the amount of cash on hand."

Defaults chosen for open choices (designer can change them later): B5 "Leave table? → No"
returns to the Career hub; B55 shots fired during the Ace Invaders wave break don't count; B70
the countdown is sent as a "starts at" time without bumping the revision; B72 a disconnected
Blind Man's Bluff seat auto-checks, or folds if it can't check; the three "rebalance" NPC tests
stay quarantined until the designer confirms the intended numbers.

How to check a phase yourself:

```
.venv\Scripts\python.exe tools\run_tests.py
.venv\Scripts\python.exe tools\screen_harness.py compare --baseline <commit before the phase>
.venv\Scripts\python.exe tools\replay.py compare --baseline <commit before the phase>
```

---

## Phase 0: safety net

**What was added (no game code changed):**
- `tools/screen_harness.py` + `tools/harness/`: 63 scenes covering every reachable `STATE_*` screen, with
  extra screenshots of open dialogs (pause, delete confirmation, damaged-save notice, update banner),
  mid-hand and showdown poker, round results, Head-to-Head countdown and race, arcade machines in play.
  `compare` renders a baseline commit (git worktree) and the working tree and diffs the pixels.
- `tools/replay.py`: 18 journeys (create a profile; Options; Solitaire win; a career day; blackjack;
  roulette; horse race; Faro; one hand each of Hold'em, Draw and Stud; Crazy Eights + Score Four; each
  arcade machine for 5 s; Cryptid + Dead Man's Hand; the debug menu then quit). Checkpoints record state,
  cash, XP, level, rating, career day and fans, plus a screenshot.
- `tests/support/locate.py`: finds functions and source text in `main.py` and `solitaireplus/**`. The 22
  tests that read `main.py` (plus the stray root copy of `test_dead_mans_hand_weapon_system.py`) now use it.
- `tools/run_tests.py`: finds test files recursively; runs each file by path; also runs plain
  module-level `test_*` functions.
- `tests/support/fixtures/profile_1.json`: the harness's test profile (level 12, $25,000, career started),
  made by `screen_harness.py make-fixture` through the real profile-creation screen.

**Safety net result:** `screen_harness compare` → `IDENTICAL 63/63 scenes`; `replay compare` →
`IDENTICAL 18/18 journeys` (baseline `f65f6cf`, the brief commit; same code as `154b890`). Both also pass
`selfcheck` (two renders of the same tree are identical).

**Quarantine changes:**
- Removed (repaired; their fake environments were missing names added later): `test_career_polish
  …reconcile_on_load…`, `test_cryptid_creatures …free_play…`, `test_npc_development …profile_load_anchors…`.
- Added: `test_dead_mans_hand_weapon_system.test_hud_supports_custom_assets_without_health_or_ammo_numbers`
  and `…test_pistol_tuning_keeps_separate_ads_and_hip_muzzle_anchors`. These are plain functions the old
  runner never collected, so they never ran; both already failed on `154b890` (stale expectations).

**Surprises / new findings (not fixed):**
- **N1:** the old test runner silently skipped every plain `test_*` function (pytest style), e.g. all of
  `test_arcade_audio.py`, `test_arcade_support.py`, `test_rewards_overhaul.py`. They run now; all but the two
  above pass.
- **N2:** the blackjack bet dropdown no longer exists (`blackjack_bet_dropdown_open` is assigned but never
  drawn); the next-hand bet buttons are always visible. Dead state, cleanup candidate for Phase 12.
- The game's `profile_select` screenshot shows bug B9 (level hidden under Delete) and the Customize screen
  shows the D1 "DEBUG +100 XP" button, as the brief describes.

## Phase 1: package skeleton and paths

**What moved:** every root module except `main.py`, `version.py` (and the two stray files left for Phase 12:
`verify_solitaire_state.py`, root `test_dead_mans_hand_weapon_system.py`) is now in `solitaireplus/`
(`app/`, `ui/`, `menus/`, `profile/`, `career/` + `career/events/`, `npc/`, `games/<family>/`, `debug/`), with
the names from brief §6.1 (`game.py` → `games/solitaire/rules.py`, `profile.py` → `profile/saves.py`,
`texas_holdem.py` → `games/poker/holdem.py`, …; full table in `tools/refactor/phase1_move.py`). `shared/` was
merged into `games/poker/` (core, strategy, speech, ui_assets, learning, holdem_chat), `npc/` (personality,
personality_chat) and `ui/image_cache.py`; the eight root shims are deleted. Multiplayer keeps its own shims
(they now point at `solitaireplus`) until Phase 11.

- Imports rewritten with `tools/refactor/imports.py` (libcst; 433 imports in the moved modules, `main.py`,
  `multiplayer/`, `tests/`, `tools/`). Every local name stays the same (`import game` became
  `from solitaireplus.games.solitaire import rules as game`), so no other line changed. Mock targets such as
  `patch("score_four.random")` were rewritten too.
- `solitaireplus/app/paths.py` (`root()`, `asset()`, `data()`, `resolve()`). All 15 `Path(__file__)` lookups
  now use it (`runtime_support.ROOT` and `multiplayer_launcher.ROOT` included), and 150 working-folder-relative
  `"assets/…"` / `"data/…"` strings in code became `paths.asset(...)` / `paths.data(...)`
  (`tools/refactor/asset_paths.py`).
- Data tables keep root-relative paths on purpose (`settings.py`, `achievements.py`, `unlocks.py`,
  `help_history.py`, `games/arcade/support.py`, and the JSON files in `data/`): they are data that could be
  saved or sent, so they must not become machine-specific absolute paths. The loaders in moved modules resolve
  them with `paths.resolve()` (`cosmetic_assets`, `achievements`, `achievements_screen`). Loaders still in
  `main.py` rely on the working folder until Phase 2. `runtime_support.bootstrap()` keeps its `chdir`.
- Build: `SolitairePlus.spec` unchanged (still `Analysis(['main.py'])`; PyInstaller follows `solitaireplus`).
  `tools/make_manifest.py`: the game exe's inputs are now `main.py` + `solitaireplus/**/*.py` (still not
  `version.py`). `tools/audit_project.py` understands `paths.asset(...)` and the new `unlocks.py` name.
- Tests: file-name references (`Path("audio.py")` …) point at the new files; `test_shared_imports.py` now checks
  the new modules and that the multiplayer shims return the very same module objects.

**Results:** tests `PASSED` (no quarantine changes). `screen_harness compare` → `IDENTICAL 63/63`,
`replay compare` → `IDENTICAL 18/18` (baseline `bba00a0`). `build_release.ps1 -SkipTests`: built; packaged
self-tests SolitaireNet, SolitaireUpdater and multiplayer modules all pass; the packaged game ran 10 s with an
empty `game-*.log`.

**Surprises:** the `shared/` modules used relative imports, which the rewrite tool skips; fixed by hand (4 lines).

## Phase 2 (move): the engine out of `main.py`

**What moved** (generated by `tools/refactor/phase2_engine.py`, libcst; then `tools/refactor/asset_paths.py`):
- `main.py` is now 21 lines: bootstrap, `--multiplayer` dispatch, update recovery, then `loop.run()`.
- `solitaireplus/app/state.py`: every module-level variable of the old `main.py` that is ever rebound (187 with
  literal starting values, 72 that get their first value during start-up). Code reads and writes `state.name`;
  all 544 `global` statements are gone. Loop temporaries that never carry a value between branches or frames
  became plain locals of the branch functions instead.
- `solitaireplus/app/state_names.py`: the 60 `STATE_*` screen names.
- `solitaireplus/app/loop.py`: the old `while running:` loop, same order, with the `SCREENS` registry. Every
  event-chain and draw-chain branch is a function in `solitaireplus/legacy.py` (`loop_event_<screen>`,
  `loop_draw_<screen>`, `loop_late_<screen>` for the timed NPC poker turns, `loop_post_event_updates`), 120 in
  all. The second draw chain looks at `current_state` again, like the old loop (`DRAWN_LATE`).
- Moved blocks: `app/window.py` (window, game surface, present), `app/fonts.py`, `app/sounds.py` (the
  `audio` instance, SFX, playlists, horse-race music), `app/assets.py` (avatar art, backgrounds, felts, card
  backs, titles, splash art), `ui/cursors.py`, `ui/buttons.py`, `ui/text.py` (imported as `ui_text`, because
  `text` is a common local name), `ui/panels.py`, `ui/backgrounds.py` (menu drift).
- `solitaireplus/legacy.py` (29,242 lines): everything else, temporary. It imports each moved module at the
  place its block used to be, so start-up runs in the old order; the moved modules refer back to legacy and to
  each other through late-bound `LazyModule` proxies (`app/lazy.py`), which avoids running start-up code early.
- `globals()` became `game_namespace()` (a ChainMap: state first; writes go to state).
- Two locals named `state` were renamed so they don't hide the module (`handle_career_activity`: `activity`;
  `preview_competitive_rating`: `opponent_state`).
- The 152 remaining working-folder-relative asset strings from `main.py` now use `paths.asset(...)`.
- Tests: `tests/support/locate.py` gives fake namespaces stand-ins for the module aliases
  (`locate.namespace`, `exec_nodes`); 17 test files were re-pointed at the new layout by a workflow (one agent
  per file, each diff checked by an independent reviewer: none weakened). The harness probe now skips module
  objects when looking a name up.

**Results:** `screen_harness compare` → `IDENTICAL 63/63`; `replay compare` → `IDENTICAL 18/18` (baseline
`d924025`). Tests `PASSED`.

**Surprises:** `multiplayer:test_six_seat…test_six_clients_and_late_join` passed in two runs (it is the B67
timing test; left quarantined until Phase 11 fixes the clock mix).
