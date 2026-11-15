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

## Phase 2 (fix): W1, B15, B16, B17, B62, B63, B64, B65

Fixed by the lead (W1) and by a workflow of six agents (one per bug group, test first), each fix
checked by an independent adversarial reviewer.

- **W1 (windowing, designer's top complaint)** — `solitaireplus/app/window.py` rewritten:
  - DPI-aware process (`SDL_WINDOWS_DPI_AWARENESS=permonitorv2` + `SetProcessDpiAwareness(2)`, called by
    `main.py` before pygame opens the display; multiplayer keeps its old window until Phase 11).
  - `SCALED | RESIZABLE`: SDL scales the 1366x768 picture with letterboxing and maps the mouse; the manual
    smoothscale, `scaled_surface_cache` and coordinate scaling are gone. Spike first: `Window.size` works
    after a few frames, so the window is re-centred once SDL has applied the size (`present()`).
  - Size rules (pure, unit-tested in `tests/test_window.py` for the six screens in the brief plus Dan's PC):
    default = largest 16:9 within 90% of the work area minus frame and title bar, clamped to
    1024x576..2560x1440; Options greys out sizes that don't fit ("Too large for this screen." tooltip, clicks
    ignored); a saved size that no longer fits is replaced by the default on start-up.
  - Centred on creation, on every resize and when leaving fullscreen; fullscreen = `toggle_fullscreen()`
    (desktop fullscreen, letterboxed); F11 and Options keep working and are still saved.
  - `ui/cursors.py`: the accessible-cursor check compares cursor sizes at 100% scaling (a DPI-aware process
    sees 40-64 px cursors at 125-200% and would have switched to the large software cursor).
  - The multiplayer launcher passes the player's real window size and fullscreen choice (the display
    surface is always 1366x768 now).
  - **Manual check (`tools/window_check.py`, real screen, Dan's PC: 1920x1200 at 125%, work area
    1920x1152):** 39/39 ok from source — start-up window (103, 87, 1817, 1082) = 1712x963 client, centred,
    title bar visible; 5 x F11 each way: fullscreen (0, 0, 1920, 1200), back to the same centred window;
    Options 1366x768 → (276, 185, 1644, 985), 1600x900 → (159, 119, 1761, 1051); 1920x1080 and 2560x1440
    greyed out; saved 2560x1440 → clamped to the default; saved fullscreen → starts fullscreen. Packaged:
    11/11 ok — the packaged game opens at (103, 87, 1817, 1082), 5 x F11 alternate between (0, 0, 1920, 1200) and the same centred window; the 10-second launch leaves an empty log.
- **B15** — drawing uses the frame's mouse position (`state.mouse_pos`); event handlers still get the event's
  own position. Also no hover while the pointer is in a letterbox bar or outside the window (review
  findings). Tests: `test_loop_mouse_and_screen_hooks` + scene `menu_hover_after_key`.
- **B16** — screens can have `enter()`/`leave()` (legacy: `loop_enter_<screen>`/`loop_leave_<screen>`);
  the loop runs them on every screen change; Options resets both slider drags.
- **B17** — `ui/text.get_font()` font cache (no `global`; cleared on `pygame.quit()`), scaled-image caches
  for wooden buttons and submenu plaques, pre-scaled menu drift (9 sub-pixel phases per background, built
  on first use); every per-frame font construction in legacy.py replaced. The reviewer found the drift cache
  only covered fully opaque art, while scaling opaque art to 3x leaves alpha 251-254 in places; such
  "nearly opaque" backgrounds are now flattened once and use the cache too (at most a few colour levels from
  the old picture, without the faint ghosting of the previous frame). Backgrounds with real transparency
  (`bg_the_reverent`, `bg_wall`) keep the exact old path. The default background is pixel-identical.
- **B62** — the playlist advances only on the end-of-music event (and ignores the stale event after a
  stop/fade); `update()` only finishes fades and recovers cabinet music.
- **B63** — non-dict save sections load as empty; `career.arcade` normalised on load like on save.
- **B64** — a missing `ratings["overall"]` is derived from the category ratings.
- **B65** — `RatingPoints` formats "f" specs as whole points (precision dropped), "d" specs unchanged.

**Results:** tests `PASSED`. `screen_harness compare` (baseline `4bf1db8`): 59/64 identical; the 5 that differ
are intended: `menu_hover_after_key__options` (B15: hover kept after a key press), `debug_menu` and
`arcade_battle_bosses` (B15: the button under the resting mouse stays highlighted after F10 / arrow keys),
`menu_options` and `menu_options_update_available` (W1: 1920x1080 and 2560x1440 greyed out on this screen).
`replay compare`: all checkpoint values identical; pixel differences only in `02_options` (W1 greyed sizes; at
1600x900 SDL now does the scaling the old code did by hand), `15_debug_menu_quit` and `13_arcade_battle_bosses`
(B15 hover). Packaged build: all self-tests pass; W1 packaged check 11/11; 10-second launch, empty log.

**New findings (not fixed):**
- **N3:** a save with a null field *inside* a section (e.g. `identity.avatar`, `progression.level`,
  `cosmetics.unlocked_felts`, `career.owned_residences`) still crashes in `apply_profile_save_data` after it
  loads (B63 covers whole sections only).
- **N4:** `npc/manager.py` with a non-numeric category rating (`"strategy": "abc"`) still raises in
  `derive_overall` (malformed data, beyond B64's missing key).
- **N5:** B62 removed `update()`'s "start the next track when the mixer is idle" safety net, as the brief
  asked: if an end-of-music event were ever lost (nothing loses one today), music would stay off until the
  next mode change.
- **N6:** `ui/text.get_font` clears on `pygame.quit()` but not on `pygame.font.quit()` (nothing calls that).
- **N7:** 156 module-private `global` statements remain in modules that moved in Phase 1 (mostly the poker
  table UIs' animation caches); the brief's end-state checklist forbids them, so they go during the area
  phases (poker in Phase 7) or Phase 12.
- `multiplayer/audio.py` has the same double-advance as B62, but nothing imports it (dead code, Phase 11).

## Phase 3 (move): menus and profile

**What moved** (`tools/refactor/move.py` with the plan from `tools/refactor/specs/phase3.json`; `legacy.py`
29,242 → 22,065 lines):
- `solitaireplus/menus/`: `splash.py`, `main_menu.py` (+ update checker, update start, multiplayer launcher),
  `mode_select.py`, `free_play_select.py`, `difficulty_screen.py`, `help_screen.py`, `achievements_screen.py`
  (the Achievements screen handlers joined the existing module), `options_screen.py` (+ the app settings it
  saves), `customize.py`.
- `solitaireplus/profile/`: `profile_select.py` (+ `finish_profile_selection`), `profile_editor.py`,
  `recap.py`, `level_up.py` (+ the level-up queue), `leveling.py` (XP, levels, round rewards, unlocks by level,
  achievement events), `save_data.py` (fresh profile, building and applying save data).
- Each screen module exposes `handle_event`/`draw` (Options also `enter`/`leave`; Level-up `DRAWS_LATE`); the
  SCREENS registry points at the modules. A screen's exclusive helpers, rects and constants moved with it.
- Module names avoid clashes with local variables (`options_screen`, `difficulty_screen`, `help_screen`,
  `leveling`, `save_data`): the mover now refuses any alias that some function also uses as a local name, and
  turns an import of a name from the target module itself into a plain alias assignment.
- `tests/support/locate.py` treats every package module name as a possible alias in fake namespaces; 6 test
  files re-pointed at the new modules (workflow with an independent review of each diff).

**Results:** `screen_harness compare` → `IDENTICAL 64/64`; `replay compare` → `IDENTICAL 18/18` (baseline
`2c62abd`). Tests `PASSED`.
