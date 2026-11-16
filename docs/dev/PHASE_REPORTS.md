# Restructure sprint: phase reports

Reports for the phases in [RESTRUCTURE_BRIEF.md](RESTRUCTURE_BRIEF.md), newest at the bottom.

Phases 8 to 12 were built at the same time in separate worktrees and then applied to this branch in order, each
checked again there. Some of their reports name the worktree commits, which are not on the branch: `1184437`
(Phase 8), `8a0775b` and `fde74a4` (Phase 9), `3ce7a33` and `070b45e` (Phase 10), `ff82492` and `e795414`
(Phase 11), and `e7d8e80` (the base the Phase 12 groups worked on). The branch commits have the same first lines:
use `git log --oneline` to find them. Two late fixes carry the label of the phase whose bug they finish
("Phase 7 (fix): packaged game ..." after Phase 10, "Phase 7 (fix): B44 ..." and "Phase 11 (fix): per-frame
fonts ..." after Phase 11).

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
`texas_holdem.py` → `games/poker/holdem.py`, …; full table in `tools/refactor/phase1_move.py`, deleted in
Phase 12; read it with `git show d924025:tools/refactor/phase1_move.py`). `shared/` was
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

## Phase 3 (fix): B7, B9, B10, B11, B12, B13, B14, D1 (Customize)

Fixed by a workflow (`tools/refactor/workflows/phase_fixes.js`): one agent per bug, test first (each new test
failed on the Phase 3 move commit), each fix checked by an independent adversarial reviewer; the lead fixed what
the reviews found.

- **B7** — the Recap screen's Yes/No handlers (`profile/recap.py`) extend `level_up_queue` instead of replacing
  it, so a level-up queued before the recap still shows (first, then the round's). `test_recap_level_up_queue`.
- **B9** — the profile-select slot's "Level N" / "Can't open" text is right-aligned 16 px left of the slot's
  Delete button (every slot that shows the text has one). `test_profile_select_layout`.
- **B10** — the profile-select screen caches each slot's display data (`profile_select._slot_display_cache`, no
  `global`); `enter()` and every save/delete/create clear it. 10 frames now read each save once (was 30 reads).
  Review finding fixed: the Delete hit-test uses the same cached data as the drawn buttons (it checked the disk,
  so a save changed by another copy of the game could make the click and the picture disagree).
  `test_profile_slot_cache`.
- **B11** — `cycle_option` treats a value missing from the options as index 0 and returns the value unchanged
  for an empty list. Review findings fixed: the selector label (`avatar_selector_label`, shows `-/N`) and
  `legacy.get_profile_avatar` (skips a layer whose picture is missing) crashed on the same missing part before
  any arrow could be pressed. `test_avatar_cycle_option`.
- **B12** — the Profile screen shows "Saved to a recovery file (the save is in use). Close other copies of the
  game." when `save_profile` returns False. Also (review finding): an `OSError` from `save_profile` (disk full,
  read-only saves folder) no longer crashes the game: "Could not save. Check the saves folder and try again.";
  while creating a profile the screen stays in creation mode so Save can be retried.
  `test_profile_save_failed_message`.
- **B13** — the loaded profile can't be deleted: "This profile is in use. Load another profile first to delete
  it." (`profile_select.profile_in_use`; `state.profile_chosen` tells the start-up default slot 1 from a real
  pick; a guest has no slot; the Career switch guard is kept). Review finding fixed: the notice is cleared when
  the screen opens and when a delete confirmation opens. `test_profile_delete_in_use`.
- **B14** — leaving the splash screen uses the saved music mode (`app_settings["music_mode"]`), Ambient only when
  nothing was saved (first launch, as before). `test_splash_music_mode`.
- **D1 (Customize)** — the "DEBUG +100 XP" button is gone (rect, drawing, click). `test_customize_no_debug_button`.

**Results:** tests `PASSED` (quarantine unchanged; `test_six_clients_and_late_join` passed this run but is flaky,
left for B67). `screen_harness compare` (baseline `1ddab50`): 60/64 identical; the 4 that differ are intended:
`menu_customize` (+`__felts`, `__cursors`; D1: the debug button's 180x45 area), `profile_select`,
`profile_select_delete_confirm`, `profile_select_damaged` (+`__notice`) (B9: level / "Can't open" moved left of
Delete). `replay compare`: all checkpoint values identical; pixels differ only in `01_create_profile`'s
profile-select picture (B9).

**New findings (not fixed):**
- **N8:** the career hub's Save (`save_career_from_hub`) overwrites `auto_save_career`'s "Save file locked" toast
  with "Profile saved to slot N." (same class as B12). Queued as `B12-career` in the Phase 5 fixes.
- **N9:** when creating a profile and the save goes to a recovery file, the B12 message is set but never seen:
  the screen changes straight away and nothing else draws `profile_message` (the old code was silent too).
- **N10:** before any profile is picked `current_profile_slot` defaults to 1, so an F10 debug career started
  straight from the start-up profile-select screen auto-saves into slot 1 (debug-only).
- **N11:** after a Solitaire round with no level-up, "No (deal again)" goes straight back to the table, so a
  level-up queued earlier waits until the next menu/hub screen (not lost).
- **N12:** `apply_saved_app_settings` only calls `set_music_mode` when the saved mode differs from the built-in
  "instrumental", so a saved "ambient" starts during the splash while a saved "instrumental" starts when the
  splash is left (both end up right).

## Phase 4 (move): Solitaire

**What moved** (`tools/refactor/split_post_event.py`, then `move.py` with the plan from
`tools/refactor/specs/phase4.json`; `legacy.py` 22047 → 20754 lines):
- Pre-step: the first three blocks of `legacy.loop_post_event_updates` (Head-to-Head opponent progress and the
  Solitaire round completion, all guarded by `current_state == PLAYING`) became `update_solitaire_round()`,
  called at the same place, so the frame order is unchanged (checked: no local variable shared with the
  blocks after them).
- `solitaireplus/games/solitaire/screen.py`: the Solitaire table screen (`handle_event`/`draw`, `DRAWS_LATE`),
  its mini buttons, tooltips, pause menu, return confirmation, the restart prompt and `update_solitaire_round`.
- `solitaireplus/games/solitaire/head_to_head_screen.py`: `start_head_to_head_event`, `finish_head_to_head_race`,
  `restore_head_to_head_game_settings`.
- `move.py`'s alias-clash check now only looks at modules that bind the alias at module level (`loop.run()`
  has a local `screen` but imports no such module).

**Results:** `screen_harness compare` → `IDENTICAL 64/64`; `replay compare` → `IDENTICAL 18/18` (baseline
`9890c12`). Tests `PASSED` (no test needed changes).

## Phase 4 (fix): B1, B2, B3, B4, B5, B6, B8, D1 (Solitaire)

Fixed by the fix workflow (one agent per bug, test first, adversarial review of each); the lead fixed what the
reviews found.

- **B1** — auto-solve waits for the stock flip animation (`Game.is_flip_animating()`, which also clears a
  finished flip without the renderer) instead of taking an ignored recycle for "nothing left". Review finding
  fixed: with draw 3 and unlimited passes an ending auto-solve can't finish now cycled draw/wait/recycle until
  the 500-step cap (~72 s, table locked); auto-solve now stops when a whole stock pass plays no card (same
  stock+waste count and foundation count as at the previous recycle). `test_solitaire_auto_solve`.
- **B2** — `Game.new_race_game()` captures the Restart snapshot after the race layout is set.
  `test_solitaire_race_restart`.
- **B3** — the player's round clock (`game.round_start_ticks`) starts at the end of the 3-2-1 countdown
  (`begin_selected_head_to_head_race`). `test_head_to_head_countdown_clock`.
- **B4** — the invisible `career_play_rect` hotspot, its handler and both rect definitions are gone; the other hub
  buttons behave as before. `test_career_hub_hotspot`.
- **B5** — Recap "No" after a career round goes to the Career hub (after any level-up screens) without dealing;
  free play still deals a new game. `test_recap_no_career`.
- **B6** — abandoning a career round from the pause menu clears `pending_career_activity_*` and the game's
  challenge. Review finding fixed: Back on the difficulty screen in career mode did the same kind of abandon and
  left them set. `test_career_abandon_round`, `test_difficulty_back_clears_career_activity`.
- **B8** — `HeadToHeadRace.pause()/resume()`: on any screen other than the table the race clock (countdown, timer,
  opponent) stands still and resumes where it was; a race the player never leaves is frame-for-frame the same.
  Review finding fixed (B3 + B8): the player's round clock skips the same time away, so both clocks keep showing
  the same race time. `test_head_to_head_pause`.
- **D1 (Solitaire)** — F7/F8 removed from the table; the old F8 body is `screen.instant_win_round()` (unused until
  the F10 button in Phase 10). `test_solitaire_debug_hotkeys`.

**Results:** tests `PASSED`. `screen_harness compare` → `IDENTICAL 64/64`; `replay compare` → `IDENTICAL 18/18`
(baseline `0df2c68`): none of these fixes changes a static screen or a scripted journey's values.

**New findings (not fixed):**
- **N13 (designer):** after a career round, Recap still asks "Leave table?" but Yes and No now both go to the
  Career hub; you may want to relabel or hide No in career mode.
- **N14 (designer):** the in-game pause menu (still `STATE_PLAYING`) does not stop the Head-to-Head opponent, the
  countdown or the player's timer; B8 pauses only on other screens, as the brief says.
- **N15:** `finish_head_to_head_race` ignores the player's round summary (moves, score, elapsed time), which is
  why B3 is not visible today.
- **N16:** `Game.get_elapsed_seconds()` counts time spent in Options in every Solitaire mode (lowers the time
  bonus); only Head-to-Head now skips it.
- **N17:** a stale stock flip (the flipped card not drawn within 220 ms, e.g. dragged) can block the player's own
  stock clicks until another flip finishes (auto-solve no longer has this problem).
- **N18:** `new_race_game()` still deals and discards a full random deal first (and plays the shuffle sound).
- **N19:** `legacy.py` still has a dead first set of the Career hub rects (`career_jobs_rect` etc.); removed with
  the §5.1 duplicates (B45 in Phase 7).

## Phase 5 (move): Career

**What moved** (`move.py` with the plan from `tools/refactor/specs/phase5.json`; `legacy.py` 20,754 → 12,221
lines):
- Career screens, each with `handle_event`/`draw` (+ exclusive helpers and rects): `career/hub_screen.py`,
  `activity_screen.py`, `jobs_screen.py`, `real_estate_screen.py`, `leaderboards_screen.py`,
  `leaderboard_bio_screen.py`, `news_screen.py` (+ `ensure_career_news`, `add_career_news`),
  `case_opening_screen.py`, `events/event_select_screen.py`, `events/event_screen.py`, `events/summary_screen.py`.
- Shared career code: `career/calendar.py` (days, schedule, advancing the day), `career/career_saving.py`
  (`auto_save_career`, `save_career_from_hub`), `career/career_rewards.py` (ratings and fans from games; named so
  it doesn't clash with local variables called `rewards`), `career/leaderboard_engine.py` (leaderboard and NPC
  roster sync), `career/events/night.py` (activity kinds, event-night results), `career/web_pages.py`,
  `career/career_names.py`.
- 3 tests re-pointed at the new modules: `test_career_hub_hotspot` (the hub handler is now
  `hub_screen.handle_event`; its rects come from legacy start-up code and the hub module),
  `test_career_night_warp` (moved code calls `legacy.game_namespace()`), `test_frame_font_sites` (draws the moved
  screens and now counts fonts built anywhere in the package, not only in legacy.py, so moving a screen can't hide
  a per-frame font).

**Results:** `screen_harness compare` → `IDENTICAL 64/64`; `replay compare` → `IDENTICAL 18/18` (baseline
`3a1784d`). Tests `PASSED`.

## Phase 5 (fix): B18, B19, B20, B21, B22, B23, B12 (career hub)

Fixed by the fix workflow (one agent per bug, test first, adversarial review), then a repair workflow for the
two fixes the reviews rejected (B20, B21+B22; each repair reviewed again), then the lead closed what the
second reviews still found.

- **B18** — `state.career_roster_dirty`: the NPC roster syncs only after the date or roster changed (day advance,
  debug month/prospect, profile load); the hub and leaderboards no longer sync every frame (10 hub frames: 30
  syncs → at most 1). `test_career_roster_sync`.
- **B19** — job news only when the job really changes, one story per career day (a second switch rewrites that
  day's story to name the latest job). `test_career_job_news`.
- **B20** — bad story-activity data never crashes or pays: `activities.night_is_valid()` (what the real
  `CareerActivityScreen` and `choose_option()` index, incl. text pygame can render), one bounds-and-dict check
  for today's calendar entry (`hub_screen.current_career_schedule_entry()`), guarded Work day and adventure
  refresh. A malformed night is skipped (back to the hub); an unplayed one is replaced by a fresh night; a played
  one is never replaced, also when its claimed flag is damaged or it belongs to the other story (so a day can't
  pay twice). `test_career_activity_bad_data`, `test_career_activities`.
- **B21** — the F10 menu ends a running Free Play sandbox before every game, night or career launch (only its
  own controls keep it); ending it also turns a saved "free" mode into "career". And at the root: any save
  during a sandbox (a level-up, an achievement, a debug action) writes the real career values kept in the
  sandbox snapshot, never the sandbox stake (`save_data.build_profile_save_data`).
  `test_debug_menu_ends_free_play_sandbox`.
- **B22** — `debug/game_mode.py` (`enter_debug_game_mode` / `end_debug_game_mode`): the mode before a debug
  launcher comes back when its night ends, on the debug menu's career jumps (which then run in "career" mode),
  and on Back from the poker table picker; a failed launch ends debug mode only if it switched it on. Every
  debug night is marked `debug: True`, so ending it never uses a career day. Back from the poker table picker and
  a failed Five-O / Blind Man's Bluff launch put the night in progress back untouched (entry, results, session
  totals). `test_debug_night_mode`.
- **B23 (no change, designer)** — pinned by `test_npc_monthly_rating_pins`. Finding: the game never calls
  `simulate_npc_rating_month` (only tests do); the monthly change players see comes from
  `npc_development.advance_npc_development` (age curves, `scale_rewards=False`), now pinned too.
  **Numbers for Dan** (real monthly path, real roster, 12 months from 2026-01, world seed 2026):

  | NPC | Age | Start | End | Change |
  |---|---|---|---|---|
  | Jiu Wang | 21 | 1795.95 | 1814.90 | +18.95 |
  | Mary LaFleur | 22 | 1234.75 | 1230.75 | −4.00 |
  | Luke Jingle | 37 | 1808.40 | 1807.80 | −0.60 |
  | Gary Undo (star) | 38 | 3123.50 | 3119.95 | −3.55 |
  | Shelly Barn | 42 | 2818.50 | 2808.60 | −9.90 |
  | Monkus Carlton | 46 | 2496.05 | 2483.40 | −12.65 |

  Across 20 careers (world seeds 1–20): age ≤ 22 (200 samples) mean +15.3, median +14.1, 7% went down; age ≥ 35
  (440 samples) mean −13.8, median −21.8, 90% went down (the 89-year-old Addled Grandfather about −60 a year).
- **B12 (career hub)** — `auto_save_career()` returns whether the save reached the slot file; the hub shows the
  recovery-file message instead of "Profile saved to slot N." after a locked save. `test_career_hub_save_recovery`.

**Results:** tests `PASSED`. `screen_harness compare` → `IDENTICAL 64/64`; `replay compare` → `IDENTICAL 18/18`
(baseline `d8ed4d0`): no static screen or journey value changes.

**New findings (not fixed):**
- **N20 (designer):** debug launchers that don't switch to "debug" mode (Casual Cards, Casino, Poker Night, Crazy
  Eights, Bango, Score Four, Blackjack, Roulette, Faro) play inside the Career: real ratings, fans, cash and
  Career news, only the day advance is skipped. Should debug nights be fully sandboxed?
- **N21 (designer):** some late-30s NPCs gain +200 to +250 in one year when their rolled `peak_age` is just above
  their age (`npc_development.ability_target` spreads the bonus over a very short gap).
- **N22:** `get_career_leaderboard()` still rebuilds and sorts the whole leaderboard on every call (twice per hub
  frame); cheaper than the roster sync B18 removed, but repeated work.
- **N23:** clicking the job you already have still re-rolls future work-day titles and saves.
- **N24:** moved code still uses `state.<name>` as a for-loop variable (`for job_id, state.rect in ...`), a
  leftover of the conversion from globals; to clean up in Phase 12.
- **N25:** the ~40 other `auto_save_career()` callers show the locked-save toast on the hub controls, which are
  only drawn on the hub, so a locked save from another screen is silent unless the player returns within 8 s.
- **N26:** switching jobs A → B → A in one day leaves one (rewritten) story although the day ends with the
  starting job.
- **N27:** a shown rating rounds .5 to even (2818.50 shows as 2818), so a shown change can be one point off.

## Phase 6 (move): Casino

**What moved** (`move.py`, plan from `tools/refactor/specs/phase6.json`; `legacy.py` 12,2xx → 10,096 lines):
`solitaireplus/games/casino/blackjack_screen.py` (bet and table screens, `settle_blackjack_round`, the
blackjack engine instance), `roulette_screen.py` (+ `settle_roulette_round`, bet placement, `roulette_game`),
`horse_races_screen.py` (+ `start_horse_races_session`, `finish_horse_races_session`, `settle_horse_race_result`,
`stop_horse_race_music`, `horse_races_game`), `faro_screen.py` (+ `start_faro_session`,
`claim_faro_session_result`, `faro_game`). The F10 debug launchers (still in legacy.py) call them through the
new modules.

`tests/support/locate.py` gained `module_defining(name)` (the imported module whose top level defines a name);
the two debug-night tests now patch and call the casino functions wherever they live, so later moves don't
break them again.

**Results:** `screen_harness compare` → `IDENTICAL 64/64`; `replay compare` → `IDENTICAL 18/18` (baseline
`6ed72fe`). Tests `PASSED`.

## Phase 6 (fix): B24–B31, B33, B34, B66 (B32 no change)

Fixed by the fix workflow (one agent per bug, test first, adversarial review); the lead closed the review
findings.

- **B24** — `RouletteGame.start_spin()` resets `payout_claimed`, so a re-spin with the same bets pays (cash, XP,
  achievement, rating); `test_career_ratings` no longer hides it by resetting flags by hand.
  `test_roulette_respin`, `test_career_ratings`.
- **B25** — the Spin handler takes the stake only after `start_spin()` returned True. `test_roulette_spin_cash`.
- **B26** — changing, removing or clearing chips after a round clears the old result
  (`RouletteGame.clear_finished_result`). `test_roulette_bet_change_clears_result`.
- **B27** — blackjack reshuffles a fresh deck before a round when fewer than 15 cards remain and never rebuilds
  mid-hand (an empty deck mid-hand deals only cards not in play); 4 × 200 seeded rounds, no duplicate.
  `test_blackjack_deck`.
- **B28** — a natural pays `bet + (bet * 3 + 1) // 2` (whole dollars, half-up): $1/$3/$5 → +2/+5/+8.
  `test_blackjack_payout_rounding`.
- **B29** — an unsplit bust resolves as "dealer", not "split". `test_blackjack_single_hand_bust`.
- **B30** — "Low Roller" needs a real Stand (a per-round flag set only by the Stand button).
  `test_blackjack_low_stand_achievement`.
- **B31** — the horse-race cue captures the base music volume only when not already ducked and restores it on
  every exit (incl. the screen's new `leave()`). `test_horse_race_music_ducking`.
- **B32** — no change (designer decision).
- **B33** — Faro tracks the money a deal actually settled (`settled_total`); place/remove/deal/cash out gives no
  rating, XP, fans or night activity. `test_faro_risk_free_rating`.
- **B34** — blackjack fitted labels use the shared font cache (pixel-identical). Also (review): the blackjack
  background and logo are scaled once instead of every frame, and `blackjack_presentation.py` has no `global`
  any more. `test_blackjack_fonts`, `test_casino_frame_caches`.
- **B66** — roulette chip labels: "1.5k" for $1,500; from $10k up the decimal is dropped ("12k") so the label
  fits on the 26 px chip; the chip font is built once. `test_roulette_chip_label`, `test_casino_frame_caches`.

**Results:** tests `PASSED`. `screen_harness compare` → `IDENTICAL 64/64`; `replay compare` → `IDENTICAL 18/18`
(baseline `3103f2e`; the scripted roulette/blackjack journeys use stakes and spins these fixes don't change).

**New findings (not fixed):**
- **N28:** the roulette status line computes WIN/LOSE from the bets on the table at draw time, not from the
  settled result (B26 hides the stale value, but storing the settled net would be more robust).
- **N29:** `claim_faro_session_result` computes a session rating tier (`TRAINING_RATING_REWARDS['faro']`) and
  never uses it; a break-even Faro night costs at least 1 fan (`lose_fans_for_bad_result` with net 0).
- **N30:** on split blackjack rounds the Low Roller flag is per round, not per hand (stand on one hand, double
  the other, only the doubled one wins → still awarded).
- **N31:** after leaving the horse races mid-race via F10 and coming back, the race continues without its cue.
- **N32:** `test_career_ratings` still sets the blackjack `round_complete`/`payout_claimed` flags by hand.

## Phase 7 (move): Poker

**What moved** (`move.py`, plan from `tools/refactor/specs/phase7.json`; `legacy.py` 10,096 → 6328 lines):
- `solitaireplus/games/poker/holdem_screen.py` (table + buy-in screens, sessions, showdown processing, timed NPC
  turns, the street/NPC/next-hand delays, chip sound), `five_card_draw_screen.py`, `seven_card_stud_screen.py`
  (each with its session starter, opponents and engine instance), `five_o_screen.py`, `blind_mans_bluff_screen.py`
  (+ session starters and engine instances), `debug/poker_select_screen.py` (the F10 poker table picker).
- `games/poker/table_stakes.py`: career starting stacks, antes and minimum buy-ins shared by the tables.
- `career/training.py`: `TRAINING_RATING_REWARDS` and `TRAINING_GAMES`. First try: the planner put this shared
  table into the Blind Man's Bluff module; its definition is early in start-up, so the module (and its engine
  instance) loaded early and shifted the seeded random draws of later games: `compare` showed Blind Man's Bluff
  and horse-race differences. Reverted and redone with this module; the engines are created in the old order.
- 2 debug tests re-pointed at the poker picker screen and the moved launchers.

**Results:** `screen_harness compare` → `IDENTICAL 64/64`; `replay compare` → `IDENTICAL 18/18` (baseline
`ab7f1cc`). Tests `PASSED`.

## Phase 7 (fix): B35, B40, B41, B43, B44, B45, D1 (Hold'em), no `global` in the poker UIs

Fixed by the fix workflow (one agent per item, test first, adversarial review), then a repair workflow for the
review follow-ups (each reviewed again). B36–B39, B42 and B86 follow in the B86 alignment (next section).

- **B35** — `start_texas_holdem_session` resets `texas_holdem_session_end_at`. Also (review finding): it resets
  `texas_holdem_table_sweep_rewarded`, like Draw and Stud, so the table-clear bonus is earned once per session
  instead of once per app run. `test_holdem_session_end_timer`, `test_holdem_table_clear_bonus`.
- **B40** — the Stud bring-in skips seats with no chips (next-lowest door card that can post); if nobody has chips
  the old lowest-card pick stays. `test_stud_bring_in`. *Designer question:* the usual casino rule gives the
  bring-in to the player left of the all-in low card instead; the two differ only with 4+ seats.
- **B41** — Draw keeps a per-hand muck; an empty deck reshuffles the muck in; if even that is empty the old card
  stays and the log says so ("The deck ran out: X keeps N cards."). Table reads still see the count the seat
  asked for; the seat badge shows "Drew N" with what it received. Unreachable with today's 4-opponent tables.
  `test_five_card_draw_deck_exhaustion`.
- **B43** — a single-winner pot's recap lists its eligible player. `test_poker_recap_single_winner`.
- **B44** — every per-frame `Font`/`SysFont` in the poker UIs, the recap and Five-O uses `ui_text.get_font`
  (B44's list plus the review's: the Draw/Stud fit helpers and status lines, the Hold'em banner and rating line,
  Blind Man's Bluff presentation, the variant quick chat). Pixel-identical. `test_poker_ui_fonts`,
  `test_poker_ui_font_cache`.
- **B45** — one definition each for the Hold'em sound helpers (the later ones kept), `STATE_CAREER_NEWS`,
  `play_background_image`, `profile_switch_rect` and the career hub rects (the values in effect kept);
  `blackjack_dealer_npc` keeps its `None` default in state.py. `test_b45_duplicates`.
- **D1 (Hold'em)** — F7, Space and B are gone from the table; `debug_setup_holdem_heads_up` (unused) deleted.
  `test_holdem_debug_hotkeys`.
- **N7 (poker)** — all 144 `global` statements in holdem_ui, five_card_draw_ui, seven_card_stud_ui,
  blind_mans_bluff_ui, five_o_ui and speech.py are gone: the 14 shared Hold'em UI values live in state.py
  (`state.holdem_options_open` etc.), private caches in one module holder each; `speech.POKER_CHAT_POPUPS_ENABLED`
  is `state.poker_chat_popups_enabled` (a module `__getattr__` keeps the old name for multiplayer until Phase 11).
  All poker scenes and journeys 09–11 byte-identical. `test_poker_ui_no_globals`.

**Results:** tests `PASSED`. `screen_harness compare` → `IDENTICAL 64/64`; `replay compare` → `IDENTICAL 18/18`
(baseline `a2f9687`).

**New findings (not fixed):**
- **N33:** `award_pot_to_single_player`'s award entry has no `remainder` key (readers default it to 0).
- **N34:** `multiplayer/texas_holdem_ui.py` still has its own `global` statements and module-level Hold'em UI
  state; the Phase 11 merge must move multiplayer's `ui.holdem_*` writes to `state.holdem_*` and drop the
  `speech.POKER_CHAT_POPUPS_ENABLED` shim.
- **N35:** `tests/test_poker_recap.py` and `tests/test_table_polish.py` save previews to a hard-coded
  `/workspace/scratch` path (already quarantined; Phase 12 points them at a temporary folder).

## Phase 7 (fix): B86 poker rules alignment (B36, B37, B38, B39, B42)

B86 asked for one set of table rules across the five single-player poker tables, with the deliberate differences
kept. Dan decided before the sprint that B86 would not stop for approval of the audit table: unify the shared rules,
keep Stud's bring-in, Blind Man's Bluff's single card and Five-O's columns, and record the table for review. The
original maintainer added that NPC behaviour should be the same in every variant, grudges and cash on hand included.

- **The audit, the shared rules and the designer choices** are in [B86_POKER_AUDIT.md](B86_POKER_AUDIT.md):
  §1 how each variant behaved before (the table Dan was to approve), §2 the shared rules now in force, §3 what
  stays different on purpose, §4 thirteen choices taken by default.
- **What changed for players, game by game** is in [../POKER_RULE_CHANGES.md](../POKER_RULE_CHANGES.md) (Dan
  asked for this separate file).
- **How it was done:** an audit workflow (one reader per variant), a design pass, six sequential implementation
  steps (G1 hand evaluation and seat views, G2 pots, G3 betting, G4 hand flow and session resets, G5 NPC decision
  inputs, G6 NPC timing), then three rounds of independent review and repair. The reviewers replayed thousands of
  seeded hands per variant looking for created or lost chips, unanswerable bets, wrong winners and wrong texts.
  The rounds found and fixed: fold wins paying a short all-in more than it matched; the bet to call after a short
  all-in blind when the last seat had already covered it (F1); TDA Rule 47 re-opening (F2); Stud completion after
  a short bring-in; and a polish round of texts and layout (P1–P11 below).
- **New shared code:** `games/poker/core.py` (hand evaluation, pots, odd chips, betting, who won, session end),
  `npc_inputs.py` (NPC decision inputs, cash-on-hand boldness and the soft bet cap), `table_timers.py`,
  `log_rows.py` (GAME LOG wrapping), `PokerGrudgeMemory.record_showdown` in `npc/personality.py`,
  `strategy.EARLY_STREETS`, and `learning.GAMES` now includes Five-O and Blind Man's Bluff.
- **B36:** no bet or raise that nobody can answer, for the human and NPCs (`core.can_raise`).
- **B37:** a pot layer that no live seat paid into goes back to whoever paid it; chips no longer vanish.
- **B38:** odd chips go one at a time from the first tied winner left of the dealer (the opener first in Blind
  Man's Bluff and Five-O). The history names who got them: "(odd chip to Ada)".
- **B39:** after a short all-in blind or bring-in, a seat that is the only one left able to act only matches what
  the others put in; if it already has, betting ends and the cards are dealt out.
- **B42:** Blind Man's Bluff refunded a pot layer that no live seat paid into with `//`, which lost the remainder,
  and it counted a hand as tied whenever the human shared winnings across the main and side pots. It now uses the
  shared `core.build_pots` (exact refunds) and `award_pots` (B38 odd chips), and `core.hand_outcome` counts a tie
  only when the human shared a pot and won none alone. Tests (`test_poker_pots`):
  `test_blind_mans_bluff_counts_wins_ties_and_losses_by_pot`, `test_a_layer_no_live_seat_paid_into_goes_back_exactly`.
- **NEW-1 (uncalled chips):** uncalled chips are returned, not won, in every variant, including fold wins
  ("Uncalled $980 returned to you." then "You win $50."). Stacks end the same as before; the win, fans and
  Hold'em pot achievements count only chips that were won. The Hold'em $1,000 and $25,000 pot achievements now
  look at the largest single pot.
- **The other audit items (NEW-1 to NEW-7):** a top layer only one seat paid is a refund (NEW-1); Stud's pot
  display after the hand no longer shows "Pot $0" and bogus side pots (NEW-2); Hold'em NPCs keep betting after you
  fold instead of the board being dealt out at once (NEW-3); the Five-O NPC can raise (NEW-4); every table resets
  its chat, quick chat and timers at session start and end (NEW-5); Stud short all-ins never use up one of the three
  raises (NEW-6); a dealer who ties gets odd chips last, not first (NEW-7).
- **NPCs, as the maintainer asked:** every variant now feeds NPCs the same inputs: personality, skill from their
  career rating for that game, boldness from cash on hand with a soft bet cap above the buy-in, grudges recorded at
  contested showdowns (severity = chips lost ÷ buy-in), table reads and advanced strategy, and career rival
  learning. Five-O and Blind Man's Bluff NPCs had fewer inputs (no reads or learning; Five-O's grudge had a fixed
  weight; Blind Man's Bluff had no big-stack boldness). Five-O and Blind Man's Bluff NPCs
  now think for the table-speed delay (1.8 / 1.2 / 0.6 s) like the other tables; Five-O waited 0.65 s and Blind
  Man's Bluff acted instantly.
- **Blind Man's Bluff short stacks** play all-in on a short ante instead of sitting out; the session ends only at 0
  chips. Five-O keeps its full-ante rule.
- **Career fans** for a poker hand are paid on the net for the hand when it is above 0, like the casino games
  (they used to count every pot, including other players' pots and the player's own uncalled chips).
- **Polish round (P1–P11):** fold wins settle like a showdown with one live seat (P1); GAME LOG lines the old code
  squashed below 65 % (Hold'em) or could not fit even at its minimum size (Draw 11 px, Stud 10 px) wrap onto extra
  rows at the normal font; every other line is drawn on one row exactly as before, the row decision is cached,
  scrolling goes by rows and text is clipped to the panel (P2; an earlier wrap-everything version lost the
  end-of-hand lines in real hands, so the floors were set from 1,000+ simulated hands); odd-chip wording (P3); a pot only one seat could win reads
  "nobody else could win it; X collects $N" (P4); NPC chat says "split" only for a shared pot (P5); "You win" instead
  of "You wins" in Blind Man's Bluff and Five-O (P6); Blind Man's Bluff stake line "All-in raise to $X", no "Open
  $0-$0", shorter prompt (P7); "(continued)" headings in the Hold'em payout recap (P8); Stud speech bubbles follow
  the pop-ups option (P9); the Five-O chat strip follows Table Chat and shows NPC talk during the column reveal
  (P10, P11).
- **Tests added:** test_poker_core_eval (30), test_poker_pots (64), test_poker_betting_rules (43),
  test_poker_hand_flow (28), test_poker_npc_inputs (43), test_poker_npc_timing (21), test_poker_session_resets (11),
  test_poker_table_text (16), test_poker_log_panels (21), test_poker_cash_round_trip (3) and
  test_poker_chip_conservation (1,000 seeded hands per variant, every seat's stack change equal to its net). The
  per-variant tests run every variant through shared adapters in `tests/support/poker_variants.py` and
  `poker_screens.py`. Updated: test_career_polish, test_career_ratings, test_poker_recap, test_rival_learning,
  test_table_polish (fans on net, the new texts).

**Results:** tests `PASSED`. `screen_harness compare` → `DIFFERENT 63/64`; `replay compare` → `DIFFERENT 17/18`
(baseline `7195fb3`). Intended differences:
- `poker_blind_mans_bluff__start`: the shorter hint "Everyone else can see your card. Read their betting." (P7).
- `poker_blind_mans_bluff__showdown`: the stake line reads "Ante $10" without "Open $0-$0" (P7), and van Dijk's
  "+$40" payout chips now show (the shared who-won rule drives the payout animation).
- `11_seven_card_stud__cp_01_hand_complete`: the pot after the hand reads $82 with payout chips instead of $0
  (NEW-2); the two bogus "Side pot N: You wins." lines are gone and the log shows both showdown lines; checkpoint
  `career_fans` 3 → 24 (fans paid on the hand's net).
- Every other scene and journey, including the Hold'em and Draw end-of-hand logs, is identical to `7195fb3`.

**New findings (not fixed):**
- **N36:** multiplayer Hold'em and Blind Man's Bluff (`multiplayer/`) still use their own pot, odd-chip and
  fold-win code (BlindBluffAuthority drops dead layers, awards a lone top layer, gives odd chips to the lowest
  seat). Phase 11 moves them onto `core.py`; the steps are in `docs/dev/PHASE11_PLAN.md`.
- **N37:** `strategy.LATE_STREETS` changed value (single-round stages count as final rounds); multiplayer imports
  `strategy` through a shim and gets the new value. Phase 11 confirms the room NPCs.

## Phase 7: packaged check (and a packaged-build fix)

`build_release.ps1 -SkipTests` at `707be96` built, and the three packaged self-tests passed (SolitaireNet,
SolitaireUpdater, every multiplayer module). The 10-second launch did **not** pass: the packaged game crashed at
start-up with `ModuleNotFoundError: No module named 'solitaireplus.menus.splash'` (written to `game-*.log`).

- **Cause:** since the Phase 3 move, the main loop opens screens from module-name strings (`app/loop.py`
  `SCREENS`), and some modules reach each other through `solitaireplus.app.lazy`. PyInstaller only follows import
  statements, so those modules were left out of the game exe. Source runs, tests and the harness import them
  normally, so only the packaged check could see it. The last packaged check before this was after Phase 2.
- **Fix:** `SolitairePlus.spec` adds `collect_submodules('solitaireplus')` to the game's hidden imports, so every
  game module ships. `tests/test_packaged_game_modules.py` checks that the spec does this and that every module
  named in `SCREENS` or a `lazy(...)` call is a real `solitaireplus` module (it fails without the spec change).
- **After the fix:** rebuilt; all three self-tests pass; the packaged game ran 10 s with an empty `game-*.log`.
  The same check runs again after Phases 11 and 12.

## Phase 8 (move): Casual cards

**What moved** (`move.py`, plan from `tools/refactor/specs/phase8.json`; `legacy.py` 6285 → 5126 lines; no
cards-area names are left in it):
- `solitaireplus/games/cards/crazy_eights_screen.py` (the screen as `handle_event`/`draw`,
  `start_crazy_eights_session`, `claim_crazy_eights_result`, the `crazy_eights_game` engine instance) and
  `bango_screen.py` (same pattern: `start_bango_session`, `claim_bango_result`, `bango_game`).
- `score_four_screen.py`: the table, mode select and opponent select screens (a multi-screen module, so the
  `loop_event_`/`loop_draw_` names stay), `draw_score_four*`, `settle_score_four_session_result`,
  `get_score_four_npc_progress`, the `score_four_*_rect(s)` and `score_four_game`. The unused
  `draw_score_four_npc_panel` moved with them (Phase 12 deletes it).
- `games/cards/score_four_tiers.py`: `SCORE_FOUR_TIER_DISPLAY_NAMES`. This is a start-up table near the top of
  legacy.py. The prepared spec put it in the Score Four screen module, which would then load at that early point and
  create `score_four_game` (whose constructor draws a seeded random puzzle) ahead of the other start-up code. That is
  the Phase 7 lesson, so it got its own module and the three engines are still created in the old order.
- The SCORE_FOUR*, CRAZY_EIGHTS and BANGO screens are registered in `app/loop.py`. The F10 launchers (still in
  legacy.py), free play, the career event select screen and `profile/save_data.py` (Score Four layout setting) call
  through the new modules.

**Problems met:**
- `score_four_ui` reads and writes Score Four names through the namespace it is given (`namespace['score_four_solo_rect']`,
  `namespace.get('get_score_four_npc_progress')`, `namespace.get('score_four_game')` ...). That namespace was
  `legacy.game_namespace()`, which no longer holds those names, so the mode select would raise KeyError and the rival
  progress bar would fall back to its own timer. Fix: `score_four_screen.score_four_namespace()` is
  `legacy.game_namespace()` with the screen module added last. Every name the old namespace had is still found
  first, and writes still go to state, as before.
- `make_plan.py` pulled the shared `draw_npc_portrait` (and the `NPC_PORTRAIT_STYLES` start-up table) into Score Four,
  because inside legacy.py only Score Four code uses it. Blackjack and the poker screens also use it, through
  `legacy.draw_npc_portrait`. The planner now treats any legacy name that another module uses as `legacy.<name>`
  as shared: it is never pulled in as an exclusive helper, only moved when a spec names it.

**Tests re-pointed:** `test_frame_font_sites` draws the Score Four opponent select from `score_four_screen`.
`tools/refactor/specs/phase8_fixes.json`'s layout note now names the new homes for the fix agents.

**What is still in legacy.py for this area:** the cards import lines it no longer uses (earlier phases left theirs
too; Phase 12 cleanup), the F10 launchers `debug_open_crazy_eights` / `debug_open_bango` / `debug_open_score_four_*`
(Phase 10, debug area), and shared tables and helpers used by several areas (`HELP_NAVIGATION`/`HELP_CONTENT` entries,
`FREE_PLAY_GAME_IDS`, `NPC_PORTRAIT_STYLES`, `draw_npc_portrait`, `get_npc_portrait_surface`). legacy.py would not be
empty after this phase. In this checkout it still holds arcade (96 names), cryptid (5), Dead Man's Hand (5),
debug (36) and 41 shared names.

**Results:** `screen_harness compare` → `IDENTICAL 64/64`; `replay compare` → `IDENTICAL 18/18` (baseline
`7195fb3`). Tests `PASSED`.

## Phase 8 (fix): B46, B47, B48, D1 (Score Four), no `global` in the cards UIs

Fixed by the fix workflow (one agent per item, test first, adversarial review). The finalizer closed the review
follow-ups: a test for the "in a row" part of B46, a test for the B47 hint line, a B48 test that no longer depends
on the PC's uptime, and the Crazy Eights help pages.

- **B46** — Crazy Eights: a player who can neither play nor draw now passes (`_pass_turn`). A new `consecutive_passes`
  count goes up by one per pass, and any play or successful draw sets it back to 0. The game ends as blocked only
  once every player has passed in a row. Then the existing `_resolve_blocked_game` picks the smallest hand, or calls
  a tie. `_draw_one` no longer ends the game on an empty pile. Both "can't draw" lines ("No cards remain to draw." /
  "<NPC> cannot draw.") are logged before the result, so the result is always the last line of the log. When the
  pile is empty, pressing Draw Card is how you pass. `test_crazy_eights_blocked_game`, including the review
  follow-up `test_a_play_or_a_draw_restarts_the_count_of_passes_in_a_row`.
- **B47** — after a draw, only the drawn card may be played (`is_player_card_playable`, which checks by object
  identity), or the player passes:
  - a new Pass button at (942, 545, 170, 48), left of Draw Card, shown only while a playable drawn card waits
    (`can_player_pass`, `pass_player_turn`, `ACTION_PASS`);
  - the hint line reads "Play the card you drew, or pass.";
  - only the drawn card is highlighted.

  A drawn eight still opens the suit choice; Pass is off while that choice is open. An unplayable drawn card still
  ends the turn. NPCs already played only the card they drew; their code is unchanged, and the test now covers it.
  The "any other card" half of B47 could not actually happen before, because Draw is only enabled when no card in
  the hand is playable. The real gap was the missing pass. The rule is now in the engine, not only in the Draw
  button's check. The How to Play pages "Crazy Eights: Basics" and "Crazy Eights: Controls" (`HELP_CONTENT` in
  legacy.py; 2 text entries changed, 1 added) now describe the pass and the B46 blocked-game rule.
  `test_crazy_eights_draw_rule`, including the review follow-up
  `test_hint_line_offers_play_or_pass_after_drawing_a_playable_card`.
- **B48** — `ScoreFourGame.get_hint_step` tries the reset to the original four cards only once (private
  `_reset_depth`). If the original cards cannot make 24, or there are no cards, it returns
  `NO_HINT = "No hint: these cards can't make 24."` on the normal hint row. That takes about 25 ms, instead of a
  RecursionError after about 12 s, which crashed the game. Solvable puzzles get exactly the same hints as before:
  the reviewer compared old and new code on 6,810 states and found 0 differences. Only debug or test states can
  reach this, because `new_puzzle` deals only solvable puzzles. `test_score_four_hint_limit`.
- **D1 (Score Four)** — the F6 "TEMP DEBUG: complete training" key is gone from `loop_event_score_four` (it set
  `puzzles_completed = 3`, `round_complete` and `session_complete`). F6 now does nothing on that screen.
  `test_score_four_debug_hotkey`.
- **N7 (cards)** — the 3 `global` statements in crazy_eights_ui (`_fonts`, `_player_card_rects`) and bango_ui
  (`_fonts`) are gone. Each module keeps its private caches in one `_ui` holder, the Phase 7 convention, and nothing
  goes to state.py. `solitaireplus/games/cards/` has no `global` and no `globals()` call left (the only match is
  the word in a docstring). All 5 cards scenes are byte-identical. `test_cards_ui_no_globals`.

**Designer choices taken (defaults, can be changed):**
- B47: Pass is its own button, not a relabelled Draw Card, so a fast double click cannot draw and then pass.
  NPCs always play a playable drawn card and never choose to pass, so no seeded random draws shift.
- B47: a voluntary pass after a draw does not count toward the B46 blocked-game count (the draw already reset it).
- B46: with nothing left to draw, the hint still says "No legal play. Draw one card." and Draw Card passes, so the
  table looks the same.
- B48: a "no hint" answer still starts the 30-second hint cooldown and sets `hint_used`, like any hint.

**Results:** tests `PASSED`. `screen_harness compare` → `IDENTICAL 64/64`; `replay compare` → `IDENTICAL 18/18`
(baseline `1184437`). No intended differences: no scene or journey draws a card from the Crazy Eights pile, empties
it, asks for a Score Four hint, presses F6 or opens the Crazy Eights help pages. The finalizer rendered both help
pages separately: the new text wraps inside the page and needs no scrolling. The fix reviewers rendered the
post-draw Pass button and hint: they sit below the table and above the hand and overlap nothing. legacy.py would
still not be empty after this phase, and this fix only touched its Crazy Eights help text.

**New findings (not fixed):**
- **N38:** Crazy Eights can loop forever when the draw pile is empty and players keep drawing and replaying the
  same recycled discards (seen in 2 of 2,000 simulated games with the pile emptied at the deal, 4 of 3,000 on the
  old engine; practically never with a full 52-card deck). A turn or cycle limit would rule it out.
- **N39:** with no legal play and nothing left to draw, the Crazy Eights hint still says "No legal play. Draw
  one card." even though Draw Card now passes. A "No cards left: pass." wording would be clearer.
- **N40:** the Crazy Eights suit choice has no cancel. After clicking an eight, including one just drawn, the
  player must pick a suit.
- **N41:** `CrazyEightsGame._choose_npc_card` gives face cards and tens two bonuses under two identical
  `if` tests (+2 and +3 × aggressiveness). It works, but the duplicate test is redundant.
- **N42:** Score Four: a hint request that returns the "no hint" text still starts the cooldown and sets
  `hint_used`. Nothing reads `hint_used` today, but a future no-hint bonus must decide whether that counts.
- **N43:** the Crazy Eights hand highlight's switch to `is_player_card_playable` has no test of its own. It
  looks the same in real play, because before B47 no other card could become playable after a draw.

## Phase 9 (move): Arcade

**What moved** (`move.py`, plan from `tools/refactor/specs/phase9.json`; `legacy.py` 6285 → 4087 lines), into
`solitaireplus/games/arcade/`:
- `hub_screens.py`: the token exchange, prize counter and trophy room screens (`loop_event_`/`loop_draw_`
  per screen), their rects (incl. `arcade_token_package_rects` and the start-up loop that fills it),
  `set_arcade_status_message`, `open_arcade_token_exchange`, `redeem_arcade_prize_for_career`, the arcade
  action-button art (`ARCADE_ACTION_BUTTON_ASSET_PATHS`, `draw_arcade_action_image_button`) and
  `draw_arcade_page_background`.
- `machine_select.py`: the King Pong and Battle Bosses opponent pickers and the Ace Invaders and Suit Snake
  difficulty pickers, with their `open_*`, `build_*` and `get_selected_*` helpers (incl. the unused
  `get_selected_suit_snake_difficulty`) and rects.
- `machine_screens.py`: the four machines in play, their engine instances, the start/claim/finish session
  functions, the draw functions and the quit/return rects. The machines' `update(1/60, ...)` calls are in
  their `loop_draw_` functions, as in the old draw chain.
- `machine_music.py`: `ARCADE_MACHINE_MUSIC_BY_STATE`, read by the main loop.

The modules hold several screens each, so the `loop_event_*`/`loop_draw_*` names stay and `app/loop.py`
registers them as `module:screen`. The career arcade night select (`event_select_screen.py`) and the F10
arcade launchers (still in legacy.py, Phase 10) call the new modules.

**Problems and how they were solved:**
- The prepared spec put `ARCADE_MACHINE_MUSIC_BY_STATE` into `machine_screens`. It is defined early in
  start-up (old line 573, the engines at 1356), so legacy.py would have imported the module there and
  created the four engines early. `KingPongGame()` draws from the global random generator in
  `reset_positions()`, so this would have moved the seeded random draws of later games. Fixed before the
  move: the table has its own module (`machine_music.py`), as `career/training.py` was in Phase 7. The
  engines are still created at the old place.
- The planner only sees users inside legacy.py, so it would have moved `get_profile_avatar` into
  `machine_screens` (career hub, career events, leaderboard bio and profile editor call it too) and
  `get_cover_scaled_ui_asset` into `hub_screens` (it shares the event-UI image cache with
  `get_event_ui_asset`, which career's event select uses). Both stay in legacy.py with the shared
  helpers. `make_plan.py` gained an optional `"keep"` list in the spec for names that stay in legacy.py.
- `arcade_token_package_rects` is filled by a bare start-up loop, which the planner doesn't pick up. It is
  now listed under `names`, and the loop under `statements` (the first spec to use them). The loop's
  `row`/`column` become module names of `hub_screens` (nothing reads them).
- `phase9_fixes.json`'s layout note now also names `machine_music.py` and the shared helpers that stay in
  legacy.py.

**Tests re-pointed:** `test_frame_font_sites` draws the Battle Bosses picker through `machine_select`. The
import is inside that test's helper, so the shared `screens()` import line is unchanged for the other
phases. The other arcade tests (`test_arcade_support`, `test_arcade_audio`, `test_loop_mouse_and_screen_hooks`,
`test_rewards_overhaul` and others) find the code through `tests/support/locate.py` and passed unchanged.

**Left in legacy.py from this area:** nothing arcade-only. Still there: `get_profile_avatar`,
`get_event_ui_asset` with `_event_ui_asset_cache`, and `get_cover_scaled_ui_asset` (shared with
career/profile, see above), the F10 arcade launchers (`debug_prepare_arcade_night`, `debug_open_arcade_night`,
`debug_open_king_pong` … `debug_open_suit_snake`; Phase 10), and the career event counters
`career_event_start_arcade_tokens`/`_tickets` (read through `game_namespace()` by `career/events/night.py`
and `career/event_progress.py`). legacy.py is not empty: the Phase 8 (casual cards) and Phase 10 (cryptid,
Dead Man's Hand, debug) code and the shared names are still in this copy.

**Results:** `screen_harness compare` → `IDENTICAL 64/64 scenes`; `replay compare` → `IDENTICAL 18/18 journeys`
(baseline `7195fb3`; incl. the 7 arcade scenes and the 4 `13_arcade_*` journeys). Tests: `PASSED - all
non-quarantined tests passed.` Commit `8a0775b`.

## Phase 9 (fix): B49, B50, B51, B52, B53, B54, B55, B56, B57, B58

Fixed by the fix workflow (one agent per bug, test first, adversarial review). Every review passed and no repair
was needed. Each new test failed on the old code; the reviewers checked this by putting the old code back in a
scratch copy.

- **B49** — the four machines move by the real frame time instead of a fixed 1/60 s. `app/loop.py` stores what
  `window.clock.tick` returned, in seconds, in the new `state.frame_dt` (one statement; the frame order is the same).
  `machine_screens.machine_frame_dt()` caps it at `MACHINE_MAX_FRAME_DT = 1/20` s, and the four `loop_draw_*`
  branches pass it to `update()`. The shared `test_loop_mouse_and_screen_hooks` fake clock now returns 16 ms, as
  pygame's `Clock.tick` does. `test_arcade_frame_time` (one 1/30 s frame equals two 1/60 s frames for each machine;
  a 0.5 s hitch counts as 1/20 s; the loop stores each tick in seconds).
- **B50** — Suit Snake still catches up at most 2 cells after a gap. When more steps were owed, `_last_step_at` now
  jumps to `now`, so the next frames step at the normal rate instead of stepping twice until the gap is paid off.
  `test_suit_snake_pause_catchup`.
- **B51** — `SuitSnakeGame._draw_card_token` gets its rank and suit fonts from `ui_text.get_font(..., sysfont=True)`
  instead of building 2 `SysFont`s per token per frame (a 40-card snake built 82 per frame). Same sizes,
  pixel-identical. `test_suit_snake_font_cache`.
- **B52** — Ace Invaders scales its background once per target size (`AceInvadersGame._scaled_background`, kept in
  `_asset_cache` like `_fit_image`) instead of every frame. Pixel-identical. `test_ace_invaders_background_cache`.
- **B53** — King Pong serves toward the side that gave up the point (`_pending_serve_to_player = not player_scored`).
  The first serve of a match is still random. `test_king_pong_serve`.
- **B54** — King Pong (both paddles, ball) and Ace Invaders (ship, formation, bullets) keep float positions. The new
  `games/arcade/motion.py` `move_rect()` keeps the exact top-left in a `Vector2` and copies the rounded value into
  the Rect used for drawing and collisions. When other code places a Rect directly (resets, zone clamps, bounces,
  the formation drop), that axis starts again from the Rect, so that code did not change. `test_arcade_subpixel_motion`.
- **B55** — shots fired during the Ace Invaders wave-break pause no longer count toward `shots_fired`/accuracy. That
  includes the spawn frame, whose bullet the new wave clears. Firing itself still works as before.
  `test_ace_invaders_wave_break_accuracy`. The accuracy is not shown on screen: it only goes into the career event
  result log.
- **B56** — in King Pong, Enter (and keypad Enter) only leaves once the match is finished, like the other machines.
  Escape and the Quit button still forfeit mid-match, and Space still starts a rematch. `test_king_pong_enter_key`.
- **B57** — Suit Snake sets "NEW HIGH SCORE!" only when a previous high score above 0 is beaten, like Ace Invaders.
  The HIGH display and the saved best score do not change. `test_suit_snake_high_score`.
- **B58** — Battle Bosses' fallback "J" on the ball (`_draw_ball`) and the fallback suit letter on a fort with no
  portrait (`_draw_portrait`, a second per-frame font in the same draw) use `ui_text.get_font`. Pixel-identical.
  `test_battle_bosses_font_cache`.

**Choices made (designer can change them):**
- B55: the sprint default. Shots during the break don't count, and firing during the break is still allowed.
- B50: the rest of a gap is dropped only when more than 2 steps were owed. The brief's literal wording would also
  throw away the leftover time after an ordinary 2-step hitch. Gaps of 2 steps or less keep their exact cadence.
- B49: `state.frame_dt` holds the raw frame time. The 1/20 s cap is applied where the value goes to the machines,
  as Dead Man's Hand does with `window.clock.get_time()`. Suit Snake gets the value too, but it steps by the clock, so
  it behaves the same.
- B57: a missing or invalid saved score counts as "no previous score". A real previous score of 0 also counts as
  none, because the brief asks for "a previous score above 0".
- B54: only the two engines the brief names. Battle Bosses rounds its ball the same way (N44 below).

**Results:** tests `PASSED`. Baseline for both compares: `8a0775bb86704ef441b27ccd7450f9a3370b280e`.
- `screen_harness compare` → `DIFFERENT: 62/64 scenes identical`. Each difference was opened and is intended:
  - `arcade_king_pong`, shot `arcade_king_pong.png`: the ball and the rival paddle are a few pixels away from where
    they were (B54 sub-pixel motion, B49 frame time).
  - `arcade_ace_invaders`, shot `arcade_ace_invaders.png`: the CASUAL formation is about 12 px further left. Before,
    its 0.9 px per frame was rounded up to 1. Because of the shifted positions there is one more kill (SCORE/HIGH 30
    instead of 20), and the bullets, two shield blocks and the ship differ slightly (B54, B49).
  - Both select shots and every other arcade scene (hub, Battle Bosses, Suit Snake) are identical.
- `replay compare` → `DIFFERENT: 15/18 journeys identical`. Only screenshots differ, and every checkpoint value is
  identical:
  - `13_arcade_king_pong` `cp_01_after_five_seconds`: the rally plays out differently. At 5 s the score is 0–0
    instead of 0–1, and the ball and rival paddle are elsewhere (B49, B54). No point is scored in this window, so
    B53's serve direction does not show here.
  - `13_arcade_battle_bosses` `cp_01_after_five_seconds`: the ball and the three rival shields are elsewhere (B49).
    The player's shield is unchanged.
  - `13_arcade_ace_invaders` `cp_01_after_five_seconds`: the formation, ship, bullets and two shield blocks are in
    different places (B54, B49). Score and lives are the same.
  - `machine_started` and the whole `13_arcade_suit_snake` journey are identical.

Commit `fde74a4`.

legacy.py is not empty after this phase (4087 lines). The Phase 8 and Phase 10 code and the shared helpers are
still there. The fixes did not touch it.

**New findings (not fixed):**
1. **N44:** Battle Bosses still rounds its ball to whole pixels on every collision sub-step
   (`battle_bosses_game.py` `update`: `self.ball_rect.x += int(round(self.ball_velocity.x * step_dt))`, same for y).
   This is the B54 speed loss, worse because it happens per sub-step. Now that B49 passes the real (uneven) frame
   time, the ball speed varies slightly from frame to frame. `motion.move_rect` would fix it.
2. **N45:** Dead Man's Hand (legacy.py, Phase 10 area) reads `window.clock.get_time()` for its own dt. It could
   use `state.frame_dt` now. Not a bug.
3. **N46:** Suit Snake Smooth Movement: after a clamped long gap (B50), the last catch-up step's render start
   time is in the past. So the snake snaps to its cell, then sits still for one step instead of gliding. Cosmetic.
4. **N47:** Ace Invaders `_draw_background` still builds and fills a full-screen SRCALPHA veil every frame. It
   could be cached per size with the same pixels.
5. **N48:** `assets/arcade/bg.png` has never been in git, yet `ace_invaders_game.ARCADE_BACKGROUND`,
   `battle_bosses_game`/`king_pong` `ARCADE_BACKGROUND_PATH`, `suit_snake_game.ARCADE_BACKGROUND` and
   `hub_screens.draw_arcade_page_background` point at it. Ace Invaders, Battle Bosses and Suit Snake try their own
   `background.png` first. King Pong and the arcade hub pages have no other picture, so they always draw a plain
   fill. Either add the picture or remove the dead path.
6. **N49:** Ace Invaders builds `pygame.font.Font(None, 34)` for each enemy on every frame when the enemy art
   fails to load (`ace_invaders_game.py`, the enemy fallback in `draw`, about line 611). This only happens on the
   fallback path.
7. **N50:** other per-frame work in the machines: Battle Bosses `_draw_portrait` and King Pong's NPC portrait
   (`king_pong.py` about line 561) smoothscale and ellipse-mask the portrait every frame. Battle Bosses `draw()` also
   allocates a full-screen shade, a header panel, an arena surface and four status plates every frame.
8. **N51:** Ace Invaders: during the wave break the player can still fire and hear the shoot sound, but the
   bullets stay frozen and vanish when the next wave spawns (kept per the B55 default). Blocking fire during the
   break might feel better. Shots still in flight when a wave ends or a life is lost also count without being able
   to hit (outside B55's definition).
9. **N52:** `state.arcade_state` is not declared in `solitaireplus/app/state.py`. It only exists once something
   assigns it, so a test that reaches a `claim_*_result`/`start_*_session` without setting it gets an AttributeError.
10. **N53:** the Ace Invaders game-over footer works out "NEW HIGH SCORE!" itself (`score >= high_score and
    score > starting_high_score`, `ace_invaders_game.py` `draw`, about line 747). It ignores `new_high_score` and the
    `starting_high_score > 0` guard, so a first-ever Ace Invaders game still shows it (the B57 problem, in the
    reference machine's footer).
11. **N54:** tooling: running `screen_harness.py compare` and `replay.py compare` for the same uncached baseline
    at the same time fails. Both run `git worktree add` for `.harness_out/worktrees/<sha12>`, and the second one stops
    with "already exists". Run them one after the other, or have the harness reuse or lock the worktree.

## Phase 10 (move): Cryptid, Dead Man's Hand, debug

**What moved** (`move.py`, plan from `tools/refactor/specs/phase10.json`; `legacy.py` 6285 → 5340 lines, or
2936 → 1992 lines on the integration line after Phases 8 and 9):
- `solitaireplus/games/cryptid/collection_screen.py`: the Cryptid Creatures screen (`handle_event`/`draw`), the
  `cryptid_screen` engine instance and `leave_career_cryptid`. The Career hub and Free Play select now reach
  `collection_screen.cryptid_screen`.
- `solitaireplus/games/dead_mans_hand/game_screen.py`: the Dead Man's Hand screen (`handle_event`/`draw`), the
  `dead_mans_hand_game` instance, `start_dead_mans_hand` and `exit_dead_mans_hand`. The F10 hotkey in
  `app/loop.py` releases and recaptures the mouse through `game_screen.dead_mans_hand_game`.
- `solitaireplus/debug/menu_screen.py`: the F10 debug menu screen (`handle_event`/`draw`, `DRAWS_LATE`). The menu
  stays public.
- `solitaireplus/debug/actions.py` (the `actions.py` of the brief's layout, §6.1): what the menu's buttons do.
  That covers the `debug_open_*` launchers, `debug_prepare_arcade_night`/`debug_prepare_poker_night`,
  `open_debug_poker_npc_select`, `debug_open_solitaire_challenge`, `debug_set_player_level`,
  `adjust_debug_ratings`, `debug_unlock_next_achievement`, `debug_end_free_play_sandbox` and the Career calendar
  jumps (`debug_start_next_career_month`, `debug_add_career_prospect`, `debug_advance_career_year`).
- The SCREENS registry points `DEBUG_MENU`, `CRYPTID_CREATURES` and `DEAD_MANS_HAND` at their modules. The engine
  instances are still created at their old place in the start-up order: legacy.py imports the two game modules
  there, so the seeded random draws don't change.

**Problems and how they were solved:**
- **Wrong module, and names from other areas.** The prepared spec put `start_dead_mans_hand` in the Dead Man's
  Hand module, but make_plan sent it to the debug menu: the debug screen's group came later in the spec and
  overrode the explicit name. The plan also pulled six names into the debug menu: `leave_free_play_game`,
  `start_crazy_eights_session`, `start_bango_session`, `queue_achievement_popup`, `unlock_achievement_cosmetic`
  and `maybe_add_monthly_flavor_news`. Their only remaining callers in legacy.py are debug or cryptid code, but
  other package modules call them too (case opening, Free Play select, event select, leveling, profile select,
  calendar), or they belong to another area (Phase 8 moves the two session starters). Fix:
  `tools/refactor/make_plan.py` takes a `"keep"` list (names that stay in legacy.py). Explicit `"names"` now win
  over screen groups, and a screen-group helper follows its users. Checked: the Phase 7, 8 and 9 specs still give
  exactly the same plans as before.
  - At integration, Phases 8 and 9 had already changed make_plan.py. Phase 8 treats a name that another module
    reaches as `legacy.<name>` as shared, and Phase 9 added its own `"keep"` list. Now there is one `"keep"`
    implementation, which has this phase's checks. `phase10.json` no longer keeps `start_crazy_eights_session` and
    `start_bango_session`, because Phase 8 moved them. Checked with the merged make_plan: the Phase 7, 8 and 9 specs
    give the same plans as on the integration line before. `phase10.json` gives this phase's plan on both `7195fb3`
    and `54a29ef`.
- **The debug actions were no longer loaded at start-up.** Once moved, nothing in legacy.py calls the debug
  actions, so their module would only be imported lazily, the first time the menu handles a click. The harness
  looks functions up by name among the loaded modules: the `career_event_select`, `career_event_summary`, arcade
  and Head-to-Head scenes call `debug_open_casino_night`, `debug_open_arcade_night` and `debug_open_head_to_head`
  before the menu ever opens. Fix: `app/loop.py` imports `solitaireplus.debug.actions` right after `legacy`.
  This has no side effects: the module holds only defs, and every module it imports eagerly is already loaded by
  then.
- **For the integration after Phases 8 and 9:** `debug/actions.py` still calls these through `legacy.`:
  - Phase 9 moves `open_king_pong_opponent_select`, `open_battle_bosses_opponent_select`,
    `open_ace_invaders_difficulty_select` and `open_suit_snake_difficulty_select` to
    `games/arcade/machine_select.py`.
  - Phase 8 moves `start_crazy_eights_session`, `start_bango_session` and `score_four_game` to
    `games/cards/crazy_eights_screen.py`, `bango_screen.py` and `score_four_screen.py`.

  Re-point those calls, or re-run this spec on the integrated base. No Phase 8 or 9 code uses a name this phase
  moves, and no name is in two plans. During integration these seven launchers were re-pointed at the Phase 8 and 9
  modules (`machine_select.`, `crazy_eights_screen.`, `bango_screen.`, `score_four_screen.score_four_game`, lazy
  imports in `debug/actions.py`). They now make exactly the calls that Phases 8 and 9 had put in their legacy.py
  copies.
- **Tests re-pointed:**
  - `test_debug_menu_ends_free_play_sandbox` and `test_debug_night_mode` now use `menu_screen.handle_event` (and
    patch `get_debug_action` there), the launchers in `debug.actions`, the `ACTION_*` constants from
    `debug.menu`, and the Dead Man's Hand module.
  - `test_blackjack_fonts`, `test_career_roster_sync` and `test_frame_font_sites` now call the launcher they need
    from `debug.actions`.
- **Still in legacy.py from this area:** two start-up state defaults (`state.cryptid_collection_state =
  new_collection()` and `state.dead_mans_hand_return_state = STATE_DEBUG_MENU`; earlier phases also left theirs
  in the start-up sequence) and imports that only the moved code used (`CryptidScreen`, `DeadMansHandGame`, the
  `debug.menu` names). legacy.py would not be empty after Phases 8–10. About 40 shared names remain, plus the
  import block and the start-up sequence: the Free Play sandbox, the achievement popup, help content, NPC
  portraits, `game_namespace`, `loop_post_event_updates` and others.

**New findings (not fixed):**
- `multiplayer/tests/test_standalone.py` saves `../standalone_preview.png`, which is outside the checkout. For
  worktrees that is `.harness_out/wt/`, a folder all of them share. It failed once ("Couldn't open") while the
  parallel phases were running their suites, then passed alone and in the full re-run. Phase 12 should point it at
  a temporary folder, like N35.

**Results:** `screen_harness compare` → `IDENTICAL 64/64 scenes`; `replay compare` → `IDENTICAL 18/18 journeys`
(baseline `7195fb3`). Tests `PASSED - all non-quarantined tests passed.` Re-checked on the integration line
against `54a29ef`: `IDENTICAL 64/64 scenes`, `IDENTICAL 18/18 journeys`, tests `PASSED`.

## Phase 10 (fix): B59, B60, B61, D1 (complete), no `global` in the debug code

Fixed by the fix workflow (one agent per item, test first, adversarial review). Two review findings were then
repaired:
- B60: a repair workflow, reviewed against the harness renders.
- D1: the restart-prompt gate, added while finalizing.

Each new test failed on the old code. The reviewers checked this by putting the old code back in a scratch copy.

- **B59** — the F10 hotkey and the menu's Close button now leave the debug menu through one function,
  `close_debug_menu()` in `debug/actions.py`. It goes back to `state.debug_previous_state`. When that screen is Dead
  Man's Hand, it also calls `dead_mans_hand_game.capture_mouse()`. With no previous screen the menu stays open.
  `game_screen` is a lazy import there, so the start-up order is unchanged. Close still plays its click sound. The
  opening side (release the mouse, remember the screen) stays inline in `app/loop.py`, because only F10 opens the
  menu. The shared `test_loop_mouse_and_screen_hooks` fake namespace also loads the real `close_debug_menu`.
  `test_debug_menu_close_recaptures_mouse` (Close back to Dead Man's Hand grabs the mouse, Close to other screens
  leaves it alone, F10 twice gives release then capture, an AST check that both ways back call the function).
- **B60** — `games/cryptid/creatures.py` has a new `opener_error(catalog, decks)`. It counts the creatures in both
  seats' decks without any randomness. A deck with fewer than 2 gets "Your deck / The opponent's deck has N creature
  card(s); a battle needs at least two to start." Unknown card ids count as non-creatures. `CryptidBattle.__init__`
  raises `ValueError` with that text before the shuffle, instead of the opener's `StopIteration`.
  - `CryptidScreen.start_battle` runs the same check after the career deck check and before the career
    `battle_serial` save. On failure it changes nothing (page, battle, `result_claimed`, `battle_serial`). It shows
    the message in gold in place of the bottom hint on the practice menu, or in the collection message bar on the
    career home. `start_error` is cleared on `enter()` and on a good start.
  - First attempt: the fixer built the battle before the save. Under the harness's shared seed counter that dealt a
    different career battle (scene `cryptid_creatures` battle shot, journey 14 checkpoint `cryptid_battle`). The
    repair keeps the original save-then-build order. Both are byte-identical to the baseline again.
  - Normal play cannot reach this: starter and career decks are validated to exactly 8 creatures.
  - `test_cryptid_opener` (engine errors for either seat, two creatures still open; practice and career starts show
    the message and keep `battle_serial`; the message clears; the career save comes before the battle build).
- **B61** — `games/dead_mans_hand/levels.py` has a new `_reachable_floor(rows, player)`. It flood-fills the floor
  cells the player can reach, in 4 directions only: the square collision box cannot slip between walls that touch at
  a corner. `_enemy_spawns` now runs in two passes:
  - Pass 1 is the old picker, unchanged.
  - Pass 2 moves only the cards that pass 1 put in an unreachable cell. Each goes to the first reachable cell in its
    own stride order that keeps the 1.35 spacing.

  So spawns that were already reachable keep their cells. All 10 authored levels give identical enemy tuples, and
  `LEVEL_VALIDATION_ERRORS` is still `[]`. A random sweep of 20,000 maps found no spawn left unreachable and no
  reachable spawn moved. `test_dead_mans_hand_spawn_reachability` (a 16x12 map with a sealed 4x4 room: no spawn
  inside, every spawn reachable, cards already reachable keep their cells, no shared cells, authored levels pinned, a
  boxed-in player gets none).
- **D1 (complete)** — three parts:
  - **The button.** The F10 menu has a "Win this Solitaire round" button (`ACTION_WIN_SOLITAIRE_ROUND`) in the
    SOLITAIRE CHALLENGES column, one empty row below "All or Nothing". `menu_screen.solitaire_win_available()` is
    true only when the menu was opened from the Solitaire table (`debug_previous_state == STATE_PLAYING`) and the
    table's "Restart this hand?" prompt is not open. That prompt swallowed the old F8 key too. This gate comes from
    a review finding, added while finalizing: before it, the round could be won behind the open prompt, which then
    sat over the victory animation and came back next round.
  - **What a click does.** When available, it plays the click, goes back through `close_debug_menu()` and calls
    `games.solitaire.screen.instant_win_round()` (the old F8 body). Otherwise the button is drawn greyed out (the
    Options disabled look), and a click does nothing and plays no sound. It is not a launch action, so it keeps a
    running Free Play sandbox.
  - **F10 while typing.** F10 is ignored while a text field has the keyboard focus: `app/loop.py`
    `typing_in_a_text_field()`, keyed on the current screen. That covers the five Profile fields, the Hold'em
    manual bet box (`state.holdem_manual_bet_active`) and the Five-Card Draw bet box (new public
    `five_card_draw_manual_bet_active()`, reached through a lazy module). The key then goes to the screen, and the
    field ignores it.
  - **Confirmation.** A grep test finds no Solitaire F7/F8, no Hold'em F7/Space/B or `debug_setup_holdem_heads_up`,
    and no Customize `debug_xp_rect`/"DEBUG +100 XP". It also checks that F10 and F11 are the only function keys
    bound. In the Phase 10 worktree, Score Four F6 was still in `legacy.loop_event_score_four`, because Phase 8
    deletes it, so that one check reported a skip. On the integration line Phase 8 is in and no `K_F6` is left. The
    check now runs and passes, and the temporary skip was taken out of the test during integration.
  - `test_debug_menu_solitaire_win`, `test_f10_ignored_while_typing`, `test_no_stray_debug_hotkeys`.
- **N7 (debug)** — the 5 `global` statements in the F10 debug code are gone:
  - `debug/menu.py` keeps the open Minigames section and the transient message in a module-private
    `_ui = SimpleNamespace()`.
  - `debug/poker_select.py` keeps its font cache in `_cache = SimpleNamespace(fonts=None)`.

  Every name was module-private and other modules use only the public functions, so `state.py` is not touched. An
  AST comparison (holder attributes mapped back to the old names) shows both files are equivalent to the move commit.
  The poker picker scenes are byte-identical. `test_debug_menu_arcade` now looks for
  `_ui.expanded_minigame_category = None`. `test_debug_no_globals` (no `global`/`globals()` anywhere in
  `solitaireplus/debug/`, plus accordion, message and font-cache behaviour).

**Choices made (designer can change them):**
- B60: the message stays on the practice menu after the player picks another deck, until the next Start or until the
  screen is entered again.
- B61: if the player's reachable area holds no candidate cell (all reachable floor is within 3.0 of the start), the
  level gets no enemies instead of enemies it can never reach. Such a level clears at once (N57). No authored
  level hits this.
- D1: the button is shown greyed out, not hidden, when the menu was not opened from the Solitaire table or the
  restart prompt is open.
- D1: the Cryptid collection's search box does not hold F10 back. It has no focus state (every key types into it), so
  blocking F10 there would make the public menu unreachable on those pages.
- D1: journey `03_solitaire` still wins through the `instant_solitaire_win()` helper (a copy of the F8 body) and not
  through the new button. A journey that clicks the button would fail when replayed on a baseline without it
  (N59).

**Results** (integration line): tests `PASSED`. Baseline for both compares: `a710d567dd2913b8758e95cbb776cee2ef9596a2`,
the integrated Phase 10 move. The Phase 10 worktree gave the same results against `3ce7a33`.
- `screen_harness compare` → `DIFFERENT: 63/64 scenes identical`. The one difference was opened and is intended:
  - `debug_menu`, shot `debug_menu.png` (12,472 pixels): the new greyed-out "Win this Solitaire round" button in the
    SOLITAIRE CHALLENGES column, one empty row below "All or Nothing" (D1). The scene opens the menu from the main
    menu, so the button is disabled. Nothing else on the menu changed.
  - `cryptid_creatures` (menu and battle shots), `dmh_dead_mans_hand` and the two poker picker scenes are identical.
- `replay compare` → `DIFFERENT: 17/18 journeys identical`. Only one screenshot differs; every checkpoint value is
  identical:
  - `15_debug_menu_quit` `cp_00_debug_menu` (12,472 pixels): the same greyed-out button (D1).
  - `14_cryptid_and_dead_mans_hand` is identical. It covers the Cryptid collection, the career battle, Dead Man's
    Hand start and movement, and it passes through the menu with no checkpoint on it.

Commit `070b45e` in the Phase 10 worktree, cherry-picked onto the integration line.

legacy.py is not empty after this phase: 1992 lines on the integration line (5340 in the Phase 10 checkout). Two
start-up defaults and a few imports of this area remain, as the move report says. So do the Phase 11 code and the
shared helpers. The fixes did not touch it.

**New findings (not fixed):**
1. **N55:** only the way back from the debug menu is shared (B59). The way in (release the Dead Man's Hand
   mouse, remember the previous screen) is still inline in `app/loop.py` `run()`. A second way to open the menu
   would need the same release step. An `open_debug_menu()` next to `close_debug_menu()` would close this off.
2. **N56:** B61 pass 2 can put two enemies in the same cell even when free reachable cells exist. When the 1.35
   spacing cannot be met, `pick()` falls back to `pool[0]` without checking whether that cell is taken. The old
   picker had the same fallback, but the smaller reachable pool makes it happen more often. This only happens on
   maps with a sealed room; no shipped level has one. Example from the review: `_build_map(14, 9, ...)` with player
   (9.5, 1.5) and salt 14 puts C1 and C2 both at (6.5, 2.5).
3. **N57:** B61 returns `()` when no candidate cell is reachable. In `DeadMansHandGame.update()`, `all()` over
   an empty enemy list is true, so such a level clears at once and still pays the 500 + level_index*250 clear bonus.
   A gentler fallback would place the enemies in reachable cells closer than 3.0. No authored level hits this.
4. **N58:** `validate_levels()` in `games/dead_mans_hand/levels.py` checks only that enemies are not inside
   walls, not that they are reachable. A hand-authored enemy list that bypasses `_enemy_spawns` could still be
   unreachable. Also, `_reachable_floor()` repeats `DeadMansHandGame._reachable_open_cells()` in `game.py` (same
   4-way flood fill, used for pickups). The two could share one helper.
5. **N59:** `tools/harness/journeys.py` `03_solitaire` still wins through `instant_solitaire_win()`, which
   copies the F8 body. The brief (§7, Phase 0, step 0.2, journey 3) wants it to win through the F10 button once D1
   exists. Switch it once the
   baseline commit has the button.
6. **N60:** `README.md` line 81 still says "Press F9 during games of Solitaire to automatically win." It was
   already wrong (the key was F8, and Phase 4 removed it). It should point to the F10 menu's "Win this Solitaire
   round" button.
7. **N61:** `solitaireplus/games/dead_mans_hand/pvp.py` (`DeadMansHandPvPMode`, with relay and room-code text
   fields) is imported by nothing; only `multiplayer/dead_mans_hand_pvp.py` is used. It looks like dead code, and it
   has text fields that the D1 F10 guard does not cover.
8. **N62:** `state.holdem_manual_bet_active` is not cleared when the Hold'em recap overlay opens. If the bet box
   had the focus then, F10 stays ignored until the box loses focus. This is mostly theoretical: both bet-box click
   handlers run before every other table click, so the flag normally clears before a hand ends.
9. **N63:** `Game.debug_auto_solve_state` in `games/solitaire/rules.py` has had no caller since Solitaire F7 was
   removed.
10. **N64:** `test_no_stray_debug_hotkeys.test_only_f10_and_f11_are_bound` allows no function key other than
    F10/F11 anywhere in `main.py` or `solitaireplus/`. Any later legitimate function-key binding must update the
    test.
11. **N65:** a `global` statement outside this phase's area remains in `solitaireplus/`:
    `games/solitaire/race_deals.py` (`_pool`). The end-state checklist wants none. `race_deals.py` belongs to
    Solitaire (Phase 4, already done), so no remaining phase owns it. The Phase 10 checkout also had some in
    `games/cards/bango_ui.py` and `crazy_eights_ui.py`, but Phase 8 has removed them on the integration line.
12. **N66:** a tracked stray copy of `test_dead_mans_hand_weapon_system.py` sits at the repository root, next to
    `tests/test_dead_mans_hand_weapon_system.py`.
13. **N67:** two weak spots in the new tests, not defects in the fixes:
    - `test_debug_menu_close_recaptures_mouse` opens the menu with its own copy of the F10 opening code, not the real
      loop, so a later change to the opening side would not be caught there.
    - `test_debug_no_globals`'s "clamped to 250 ms" assertion (`drawn() or elapsed >= 250`) is close to always true.
      The AST check is the real regression test.

## Phase 11 (move): merge the multiplayer copies

Built as `ff82492` on B86 (`707be96`) in its own worktree, then applied on top of Phase 10; the only conflict was the spec's game `hiddenimports`, where both the PvP entry and `collect_submodules('solitaireplus')` were kept. The plan is `docs/dev/PHASE11_PLAN.md`. Multiplayer has no copies of
game code left: room Hold'em runs on the shared engine and UI in `solitaireplus/`, and the LAN table and the offline
Practice table are gone. `multiplayer/` shrank by about 15,700 lines.

**LAN and Practice removed** (lan-removal). The parts the rooms still use moved unchanged into three new modules:
- `multiplayer/room_protocol.py`: `PAIRS`, `FIELDS`, `snapshot()`, `ClientGame` (from `lan_protocol.py`) and
  `clean_name()` (from `lan_session.py`).
- `multiplayer/room_game.py`: `TwoHumanGame` (from `lan_table.py`), `RoomGame` (from `room_table.py`) and
  `load_roster()` (from `standalone_table.py`).
- `multiplayer/mp_assets.py`: `TableView` as an asset loader only (card faces, card back, font, NPC portraits). The
  Practice drawing code was not moved.

Deleted: `lan_transport.py`, `lan_session.py`, `lan_protocol.py`, `lan_table.py`, `standalone_table.py`,
`standalone_view.py`, `tests/test_lan.py`, `tests/test_standalone.py` and `test_relay.test_online_table_hand`. The
launcher test moved into `test_menu_followup.py` as `test_launcher_starts_and_quits`, with a temporary LOCALAPPDATA.
Two quarantine lines went with the deleted tests. Coverage moved first, into the new `test_room_protocol.py` (8
tests), and passed before anything was moved. In `relay_transport.py` only the docstring changed.

**Engine merged** (engine-flags, engine-merge).
- `TexasHoldemGame` has three new class options. Each defaults to single-player behaviour:
  - `allow_network_spectator=False`
  - `finish_hand_after_player_fold=True`
  - `quick_chat_enabled=True` (room tables set it to False: no quick-chat state and no NPC quick-chat context)
- A busted seat 0 is never dealt hole cards and gets no "You are dealt" line. Single-player has already stopped by
  then, so its deal order does not change.
- `TwoHumanGame` is now just those three settings.
- `multiplayer/texas_holdem.py` is deleted, so room tables follow the B86 pot and betting rules (see Deviations).
- New tests: `tests/test_holdem_network_options.py` (13) and `multiplayer/tests/test_room_engine.py` (6).
- `test_multiplayer_launcher` now checks that the shared engine is used.

**UI merged** (ui-merge).
- Multiplayer imports `solitaireplus.games.poker.holdem_ui`, and `texas_holdem_ui.py` is deleted.
- The three Hold'em delay helpers take an optional `speed`. A room table passes its own speed. Table speed lives in
  `solitaireplus.app.state`.
- A pygame quit hook clears the Hold'em font cache.
- No draw options were added: no multiplayer code draws the full Hold'em screen any more. B85 is resolved because the
  code that caused it was deleted.
- New `test_shared_ui_usage.py` (7). It checks every holdem_ui attribute and keyword that multiplayer uses (the B85
  guard), and that importing multiplayer does not load the single-player game.

**AI and recap** (ai-recap). `poker_ai.py` and `poker_recap.py` are deleted; the single-player versions are used with
no flags. New `test_room_ai.py` (6). It checks that the Payout History amounts match the real stack changes for a split
pot with an odd chip and for a side pot. Measured NPC fold rates, 3,000 seeded decisions each (flop, strength 0.40, 100
to call into 300):

| Spot | Old multiplayer copy | Shared `ai.py` |
|---|---|---|
| tenacity 10, stack 200 | 66.2% | 38.4% |
| tenacity 5, stack 200 | 40.0% | 32.2% |
| tenacity 1, stack 200 | 22.7% | 22.7% |
| tenacity 10, stack 5000 | 0% | 0% |

**NPC, audio and shim copies** (npc-audio-shims).
- Deleted: `npc_portraits.py`, `npc_avatars.py`, `audio.py`, `npc_personality.py`, `npc_personality_chat.py`,
  `poker_core.py`, `poker_learning.py`, `poker_speech.py`, `poker_strategy.py`, `poker_ui_assets.py` and
  `texas_holdem_chat.py`.
- Portraits, card art, button art, appearance images and the NPC roster load through `solitaireplus.npc.portraits` and
  `solitaireplus.app.paths`. Layered portraits now include the `outline.png` layer.
- The sound adapter is still in `multiplayer/main.py`. It reads `paths.asset('sounds')` (all subfolders), keeps its
  file-name keys and aliases, and imports neither `app.sounds` nor `app.audio`.
- `speech.py` no longer has the `POKER_CHAT_POPUPS_ENABLED` shim.
- `tests/test_shared_imports.py` now checks that none of the 22 old names exists as a file or is imported anywhere.

**Dead Man's Hand PvP** (dmh-merge, dmh-wire).
- The newest multiplayer copy is now `solitaireplus/games/dead_mans_hand/pvp.py`. It imports only the standard
  library, pygame and solitaireplus modules.
- `open_peer` is passed in. Without it the lobby says "Online play is not available."
- The leave toast is drawn by `multiplayer/main.py`. `make_duel()` creates the duel and its toast.
- `multiplayer/dead_mans_hand_pvp.py` is deleted, and the spec's game `hiddenimports` gain the module.
- New tests: `tests/test_dead_mans_hand_pvp.py` (7) and `multiplayer/tests/test_duel_launch.py` (3).

**Packaging** (packaging-lists).
- `SELFTEST_SKIP` and `MP_EXCLUDED` are unchanged (the four server and test-only files).
- The installer gets an `[InstallDelete]` entry for the loose `SolitairePlus_Data\multiplayer\*.py` files and their
  `__pycache__`, so files deleted in a release do not stay behind after an upgrade.
- The function-level imports in `room_session.py` moved to module level. The ones that remain are allowlisted in
  `test_packaging.py`, each with a reason: `net_client.open_peer` imports the test-only `relay_transport`, and
  `mp_profile.py` was not in this group's files.
- Three new tests in `test_packaging.py`: the self-test report lists the new modules and none of the deleted ones, the
  function-import scan, and the installer delete lines.
- Docs: `docs/NETWORKING.md` and `docs/TESTING.md` describe rooms only, and the `tools/run_tests.py` docstring says why
  `multiplayer/` still comes first on the import path.

**Decisions** (plan section 1):
1. LAN and Practice were removed first, with the shared parts moved unchanged.
2. The engine options are class attributes with single-player defaults. Sit-out stays in `RoomGame`.
3. No draw options on holdem_ui. B85 is resolved by the deletion, plus a guard test.
4. The single-player AI and recap win, with no flags.
5. Multiplayer imports neither `app.audio` nor `app.sounds`. This departs from the brief's wording of section 7, step
   2.
6. DMH PvP is in the package, with `open_peer` passed in and `LeaveToast` owned by `multiplayer/main.py`.
7. The packaging lists are unchanged, apart from the PvP `hiddenimports` entry and the installer `[InstallDelete]`.
8. The relay room versions stay at 1 and 2. The protocol stamp comes in the fix stage.
9. B68 seating order (applies in the fix stage).
10. Two room state fields were added: `data.last_refunds` and per-pot `payouts`, both seat-relative with string keys.
    `ClientGame` turns the keys back into numbers and drops malformed entries without raising. The Payout History reads
    `last_refunds`.
11. `RoomGame.start_hand` changed (see Deviations).

**Deviations**
- **`RoomGame.start_hand` changed**, although the plan said to move it unchanged. After the deal it no longer marks a
  seat that was dealt in as busted when posting its blind put it all in. The old code left such a seat out of every pot
  it had paid into, which clashes with the shared engine's rule that busted is set only between hands. Seats sitting
  out are still marked busted and folded. The guard is `test_room_engine`
  `test_preflop_first_actor_with_all_in_blinds_matches_shared_engine`.
- **Room Hold'em now follows the single-player B86 rules.** This came with deleting the engine copy. Players will
  notice it (plan section 4):
  - A fold win settles like a one-seat showdown: the uncalled bet is returned and stacks end the same. In the plan's
    example the Payout History shows a $125 main pot plus "Returned (uncalled): Uncalled $100 returned to Guest 3",
    where it used to show a $225 pot. The footnote now reads "Amounts above are gross payouts and returned uncalled
    bets; your own wagers were already deducted."
  - Uncalled chips and folded players' chips no longer make extra side pots.
  - When every other seat still in the hand is all in, the host and guests can no longer raise.
  - A seat whose blind puts it all in plays the hand.
  - A busted host who spectates no longer gets an empty "You are dealt ." line.
- **Do not release this commit on its own.** Until the fix stage adds the room protocol stamp, a guest on an older
  Solitaire+ can join without a warning. Its old `ClientGame` then offers a Raise over an all-in, which the host
  silently refuses.

**Found here, already fixed on the branch**: the packaged single-player game crashed at start (`No module named
'solitaireplus.menus.splash'`), because `solitaireplus/app/loop.py` opens screens through module-name strings that
PyInstaller cannot follow. The base `707be96` has the same problem. It is fixed by "Phase 7 (fix): packaged game ships
every solitaireplus module" (`collect_submodules('solitaireplus')` in the spec, guarded by
`tests/test_packaged_game_modules.py`).

**Results**
- Tests `PASSED`: game 118 files, 1,056 tests; multiplayer 14 files, 78 tests.
- Quarantine: the game list is unchanged. Multiplayer has 5 left, after removing the 2 entries for deleted tests.
- `test_six_seat.SixSeatTests.test_late_join_no_mid_hand_takeover` (quarantined, flaky) failed once in the full run. It
  then passed 10 of 10 runs alone and 8 of 8 runs of the whole file.
- `screen_harness compare` → `IDENTICAL 64/64`; `replay compare` → `IDENTICAL 18/18` (baseline
  `707be96fde55c792a4a112f3901ec84c7bc8bf53`). There was no `contributors` difference at this stage.
- Packaged (`build_release.ps1 -SkipTests`):
  - All three self-tests pass. `SolitaireNet 1.1.0 ok; connectors: tcp, tls, ws, wss`. The updater self-test exited 0.
  - `release/selftest-multiplayer.txt` lists 22 modules, including `room_protocol`, `room_game` and `mp_assets`, and
    ends with `PASSED: every multiplayer module imported`.
  - Every solitaireplus module imported by the shipped `multiplayer/*.py` is in `PYZ-00.toc` (19 checked).
  - A 10 s packaged `--multiplayer` run with a temporary LOCALAPPDATA left an empty `game-*.log`.

Hand-back: `test_standalone.py` (now deleted) left a stray file at
`%USERPROFILE%\Documents\standalone_preview.png`, outside the repository. Dan can delete it.

## Phase 11 (fix): B67-B85, W1 (multiplayer)

Built as `e795414` in the Phase 11 worktree, on top of the move commit `ff82492` (which sits on B86, `707be96`), then applied on top of the integrated move. At integration the spec conflict was settled in favour of the branch's `collect_submodules('solitaireplus')` (see N68), and the two out-of-date docs in N71 were updated. The plan is
`docs/dev/PHASE11_PLAN.md`. This stage fixed B67-B84 in the merged multiplayer code, moved the
Multiplayer window onto `solitaireplus/app/window.py` (W1, multiplayer part), and fixed the packaged game, which
crashed at start (found in the move stage). B80 and B85 were resolved by the merge itself. Single-player is
unchanged on the safety net: `screen_harness compare` IDENTICAL 64/64 and `replay compare` IDENTICAL 18/18 against
`ff82492`, with no `contributors` difference (single-player never records it).

**Group outcomes**

- **bugs-holdem-room** (`room_table.py`, `room_session.py`, `room_protocol.py`, `mp_profile.py`, `holdem.py`):
  - B67: one fake clock in `SixRelayTests`. `RoomAuthority.update()` re-arms `due` and `resume_at` when the clock
    jumps back by more than `CLOCK_JUMP_MS` (60 s).
  - B69: `boundary()` returns True only when someone left a seat or was seated, and `update()` bumps the revision
    only then.
  - B70 (host and client): the per-second revision bump is gone. A view carries `countdown_at` (the "starts at"
    time on the host clock) and `host_now`. The guest sets `countdown_until` on its own clock. A malformed or
    absurd countdown (over 1 hour either way) is ignored (`room_protocol.countdown_offset`, added in the repair).
    `next_hand_seconds` is still sent, for older guests.
  - B68: a late joiner takes a busted NPC seat first, with the starting stack and the notice
    "{name} buys in for ${amount} in {old}'s seat." Otherwise it takes a funded NPC seat as before.
    `next_if_ready()` seats waiters before replacement NPCs are made. The waiting text is now "Waiting for a seat
    at the next hand".
  - B81: new `TexasHoldemGame.reset_seat_ai_state(seat)`, which single-player never calls.
    `RoomAuthority._install_seat()` builds the seat record from the room's current state and resets that seat's
    reads, reveals, last AI decision and rival-learning binding. It is used by `assign()`, `boundary()` and
    `replace_busted_npcs()`.
  - B79:
    - `TexasHoldemGame.record_pot_contributors` (class option, default False) adds `contributors` to each
      showdown pot record. Rooms turn it on.
    - `snapshot()` remaps the key per viewer.
    - `winning_xp()` skips a pot whose contributors are all winners. Pot records without the key, from an older
      host, count as before.
  - B80 remainder: a guest `bet_raise` is refused before the engine changes anything unless `can_npc_raise()`
    allows it (B86 already includes "somebody must be able to answer").
  - B84 (host): the host rebuilds its own `view(0)` only when the revision changes.
  - Protocol stamp: `ROOM_PROTOCOL = 3` on every host-to-guest message (`send_stamped`). A guest that sees no
    stamp, or another number, shows the notice "The host's Solitaire+ is a different version. Update both games
    to play together." once, and play goes on. The relay room version stays 2.
  - Quarantine: `test_last_payout_survives_new_hand` was fixed (`room.mode=None`). Both six-seat quarantine
    lines were removed after the repeated runs (see "Un-quarantine").
- **bugs-room-view** (`room_view.py`, `mp_assets.py`):
  - B70 display: the countdown comes from `table.countdown_until` and `pygame.time.get_ticks()`, with the
    message's `next_hand_seconds` as the fallback.
  - B84 caches:
    - the smaller Georgia font of a too-wide button label, built once per size;
    - scaled cards and their shadows (bounded 96, keyed by image identity and size, and keeping the image alive);
    - `panel()` layers, and translucent fill layers (turn banner, result banner, details shade);
    - finished NPC portraits in `TableView.portrait`, keyed by id, portrait path, look and size.
  - The drawing output is unchanged.
  - The repair added two things:
    - "Starting next hand…" for 2 seconds after a guest's local countdown ends, before "Waiting for players to
      rejoin" (review finding: guests flashed "Waiting" before every hand);
    - the same kind of caches in `mp_appearance.py`: background shade, oval felt and avatar layers, and the
      avatar initial's font (review finding: B84 work left there).
- **bugs-party** (`party_authority.py`, `party_view.py`, `score_four.py`):
  - B70 Roulette: no per-second bump; the view sends `seconds_left`, `countdown_at` and `host_now`.
    `party_view` counts down locally.
  - B71/B74: seat helpers on `FourSeatAuthority` (`_disconnected`, `_free_seat`, `_free_disconnected_seats`,
    `_seat_waiters`, `_return_to_lobby`, and the `_on_seated`/`_seat_is_broke` hooks). Waiters sit down at the
    next Blind Man's Bluff hand, at the next Roulette spin, or when Score Four returns to the lobby. A joiner is
    never queued twice.
  - B72 (designer): a disconnected Blind Man's Bluff seat checks, or folds when it owes chips, after 600 ms.
  - B73: fewer than 2 seats can ante → `finished` and phase 'finished' ("Table finished"). The repair added
    that a late joiner's buy-in deals a finished Blind Man's Bluff table, or a finished Roulette table, back in.
    A full finished table does not bump the revision.
  - B75: the solve is sent until the room takes it, at most once per revision. The board is kept per room
    (repair: a new room on the same round number gets its own cards).
  - B76: new pure `score_four.check_solution(numbers, steps)`. The host checks the guest's steps; `party_view`
    records them, and Undo and Reset trim them.
  - B77: a short-stack raise is clamped as min(maximum, max(minimum, amount)); a target that does not beat the
    bet is a call. The same order is used for NPC bets.
  - B78: a Roulette bet must be a whole number of at least `ROULETTE_MIN_BET` = 1.
  - B86 review (Blind Man's Bluff pots): the room now settles with
    `core.build_pots`/`award_pots`/`settle_fold_win`, raises with `core.can_raise`/`betting_reopened`, and
    picks winners with `core.hand_winners`/`hand_nets`. The view sends `can_raise`, which the Raise button follows.
- **bugs-dmh** (`solitaireplus/games/dead_mans_hand/pvp.py`):
  - B82: the host checks every guest pose and shot (`_pose_fields`, `_clean_pose`, `_clean_shot`):
    - an open floor tile;
    - a PvP weapon;
    - z and ads clamped;
    - a move no longer than walking speed allows;
    - a shot origin within 0.75 tiles of the last pose;
    - a 2-shot token bucket refilled at the gun's fire interval;
    - `hello` only before connecting;
    - `_shot_hits` safe on bad numbers;
    - guest-side checks on the host's state messages.
  - The repair added:
    - cleaning of peer names (a NUL or lone surrogate crashed rendering);
    - kill-feed gun names checked;
    - a stale dead pose no longer undoes a respawn;
    - a 1 s delay before a click leaves the result screen, so a shot fired at the moment of a disconnect is
      not taken as "back to lobby".
  - B83: a disconnect after hello ends the duel on a result screen:
    - "YOU WIN" with "{opponent} left the duel - win by forfeit" when the relay says the other player left;
    - "CONNECTION LOST" with the score for any other disconnect;
    - Enter or a click goes back to the lobby; ESC still closes.
- **window-shared** (`window.py`, `state.py`, root `main.py`):
  - `open_window(caption="Solitaire", size=None)` clamps the size.
  - `state.window_custom_cursor` (default True) keeps the single-player cursor code out of multiplayer.
  - The `main.py` comment was corrected.
  - The repair added `_allow_small_window()`. pygame's SCALED mode sets the 1366x768 picture size as the
    window's minimum size, so SDL silently kept a smaller requested size (for example the 1088x612 default on a
    1366x768 laptop) at 1366x768, and `present()` kept retrying. The minimum is now `MIN_WINDOW_SIZE`
    (1024x576). This also affects single-player on screens smaller than about 1366x800 (see "Single-player").
- **window-mp** (`mp_options.py`, `multiplayer/main.py`, `tools/window_check.py`):
  - `Options.open_window()`, `set_fullscreen()` and `set_size()` go through `app/window.py`.
  - `inherited_window()` reads any positive `SOLITAIRE_MP_WINDOW` and `SOLITAIRE_MP_FULLSCREEN` on its own.
    Inherited values are never saved, and the default size writes no `size` key.
  - `main.py` calls `window.enable_dpi_awareness()`, draws on `window.game_surface`, maps the mouse with
    `window_to_game_coords`, and shows frames with `window.present()`.
  - B84: the hub's button and status fonts are made once.
  - `window_check.py --multiplayer` added.
  - `test_menu_followup.test_lobby_quit_button_ends_the_loop` was rewritten for the current hub and passes, so
    its quarantine line went.
- **Review and repair**: the reviewers' findings were repaired as listed above. Findings left as notes are under
  "New findings".
- **final-packaged** (this group):
  - spec `hiddenimports` gained the three importlib-only screens (N68; dropped at integration, because the branch already collects every solitaireplus module);
  - full tests, both compares, the packaged build and checks, the local two-player test, and the window checks;
  - docs: `docs/TESTING.md`, `docs/POKER_RULE_CHANGES.md` ("Online play"), and the brief's section 5.6.

**Decisions** (plan section 1, as carried out)
1. LAN and Practice were removed first. The shared parts moved unchanged into `room_protocol.py`, `room_game.py`
   and `mp_assets.py`.
2. Engine options on `TexasHoldemGame` with single-player defaults: `allow_network_spectator=False`,
   `finish_hand_after_player_fold=True`, `quick_chat_enabled=True`. No hole cards for a busted seat 0
   (unconditional). Sit-out stays in `RoomGame`. The fix stage added `record_pot_contributors=False` (B79, rooms
   only) and `reset_seat_ai_state()` (B81, rooms only).
3. No draw options on `holdem_ui`. B85 is resolved by the deletion, with a guard test. The only UI addition is
   `speed=None` on the three delay helpers.
4. The single-player AI and recap win, with no flags. Room NPCs gain the short-stack tenacity cap (table below).
5. Multiplayer imports neither `app.audio` nor `app.sounds`. Its sound adapter reads `paths.asset('sounds')`.
6. DMH PvP is `solitaireplus/games/dead_mans_hand/pvp.py`, with `open_peer` passed in, `LeaveToast` in
   `multiplayer/main.py`, and the module in `hiddenimports`.
7. `SELFTEST_SKIP` and `MP_EXCLUDED` are unchanged. `hiddenimports` gained the PvP module (move) and three
   screens (this commit, N68; on the branch `collect_submodules('solitaireplus')` covers them). The installer has `[InstallDelete]` for loose `multiplayer\*.py`.
8. The relay room versions stay 1 and 2. Room messages carry the app-level `protocol` stamp (3).
9. B68 seating: busted NPC seats first, with the normal buy-in; otherwise a funded NPC seat as before.
10. Additive room state fields: `data.last_refunds` and per-pot `payouts` (move stage), and per-pot
    `contributors` (this stage). All are seat-relative, and older clients ignore them.
11. `RoomGame.start_hand` no longer marks a dealt-in, all-in-from-the-blind seat as busted (move stage).
- Orchestrator and designer defaults (final):
  - B72: a disconnected Blind Man's Bluff seat auto-checks, or folds if it cannot check.
  - B70: the countdown is sent as a "starts at" time, with no relay or room version bump.

**Bug table**

| Bug | Result | Tests |
|---|---|---|
| W1 (multiplayer) | fixed: the multiplayer window uses `app/window.py` (DPI aware, clamped and centred start, letterboxed desktop fullscreen, handed-over size honoured, too-large sizes greyed out) | `tests/test_window.py` (`test_open_window_sets_caption_and_clamps_size`, `test_small_window_sizes_really_apply`, `test_open_window_default_unchanged`, `test_custom_cursor_is_applied_only_when_enabled`, `test_no_cursor_import_when_custom_cursor_off`, handoff tests), `multiplayer/tests/test_mp_window.py` (12), `tools/window_check.py --multiplayer` |
| B67 | fixed | `test_clock_going_backwards_rearms_timer`; `SixRelayTests.test_six_clients_and_late_join` un-quarantined |
| B68 | fixed | `test_late_join_takes_busted_npc_seat_with_buy_in`; `test_late_join_no_mid_hand_takeover` un-quarantined |
| B69 | fixed | `test_unseatable_waiter_does_not_bump_revision` |
| B70 | fixed (Hold'em, Roulette, client display) | `test_countdown_does_not_bump_revision`, `test_client_countdown_from_timestamp`, `test_malformed_countdown_is_ignored`, `test_roulette_countdown_keeps_revision`, `test_countdown_uses_local_timestamp`, `test_countdown_runs_on_the_local_clock`, `test_draw_shows_the_local_countdown`, `test_malformed_countdown_falls_back_to_seconds_left` |
| B71 | fixed | `test_bluff_late_joiner_seated_at_next_hand`, `test_roulette_late_joiner_seated_at_next_spin`, `test_score_four_late_joiner_seated_on_return_to_lobby`, `test_waiter_takes_ghost_then_npc_seat_and_is_queued_once`, `test_lobby_waiter_takes_a_seat_freed_in_the_lobby`, `test_broke_seat_buys_in_for_the_joiner` |
| B72 | fixed (auto-check, else fold) | `test_disconnected_actor_checks_after_a_pause`, `test_disconnected_actor_folds_to_a_bet`, `test_disconnected_seat_acts_when_its_turn_comes` |
| B73 | fixed | `test_bluff_finishes_when_fewer_than_two_can_ante`, `test_late_joiner_deals_a_finished_bluff_table_back_in`, `test_full_finished_bluff_table_keeps_its_revision`, `test_late_joiner_restarts_a_finished_roulette_table` |
| B74 | fixed | `test_score_four_return_lobby_frees_ghost_seats` |
| B75 | fixed | `test_solve_is_retried_until_the_room_takes_it`, `test_a_new_room_on_the_same_round_gets_its_own_cards` |
| B76 | fixed | `test_score_four_host_checks_the_guest_solve`, `test_sent_steps_pass_the_host_check`, `test_steps_follow_undo_reset_and_a_new_round`, `tests/test_score_four_check_solution.py` (8) |
| B77 | fixed | `test_short_all_in_raise_is_recorded_as_the_real_amount`, `test_npc_short_stack_bet_is_its_stack` |
| B78 | fixed | `test_roulette_rejects_bets_below_the_minimum` |
| B79 | fixed | `test_returned_chips_give_no_xp`, `test_dead_money_layer_still_gives_xp`, `test_room_showdown_split_of_own_chips_gives_no_xp`, `tests/test_holdem_pot_contributors.py` (5) |
| B80 | resolved by the merge and B86; guest raise rule added | `multiplayer/tests/test_room_engine.py` (6), `test_guest_cannot_raise_when_no_one_can_respond`, `test_can_raise_agrees_for_every_human_seat` (see N70) |
| B81 | fixed | `test_takeover_resets_seat_ai_state` |
| B82 | fixed | `tests/test_dead_mans_hand_pvp.py` (malformed shots/poses, teleports, bursts, distant origin, second hello, legal shots and full-auto still accepted, guest-side checks, name cleaning) |
| B83 | fixed | `test_opponent_leaving_mid_match_is_a_forfeit_win`, `test_own_connection_lost_shows_connection_lost_with_the_score`, `test_disconnect_after_a_normal_end_keeps_the_real_winner`, `test_guest_sees_a_forfeit_win_when_the_host_leaves`, `test_enter_or_click_returns_to_the_lobby_and_esc_still_closes`, `test_a_click_right_after_the_disconnect_is_still_a_shot` |
| B84 | fixed | `test_wide_button_font_built_once`, `test_card_cache_reuses_scaled_card`, `test_panels_share_layer`, `test_portrait_cached`, `test_appearance_layers_built_once`, `test_host_builds_view_only_on_revision_change` |
| B85 | resolved by the merge (Practice `TableView.draw` deleted) | `test_shared_ui_usage.test_keywords_accepted` |
| B86 review (room Blind Man's Bluff pots) | fixed | `test_bmb_pots_use_the_shared_rules`, `test_folded_to_bettor_gets_uncalled_bet_back`, `test_reraise_rights_follow_the_shared_rule`, `test_raise_button_follows_the_host_rule` |

Deviation: plan step B79 "extend test_sidepots_allin the same way" was not done as such.
`tests/test_holdem_pot_contributors.py` covers it instead: a forced side pot names every contributor, every
showdown pot in played side-pot hands has contributors, the recap and pot log ignore the key, and the default-off
record is unchanged.

**Multiplayer changes players will notice** (move and fix stages)
- **Room Hold'em now follows the single-player B86 rules** (shared engine; `docs/POKER_RULE_CHANGES.md` "Online
  play" is updated):
  - A fold win settles like a one-seat showdown. Example: seat 3 raises to 150 and everyone folds. "Last pot"
    and the Payout History show a $125 main pot, plus "Returned (uncalled): Uncalled $100 returned to Guest 3".
    Before: a $225 pot.
  - Uncalled chips and folded players' chips are refunds, or join the pot they were paid into.
  - No bet or raise that nobody can answer, for the host and for guests.
  - A seat whose blind puts it all in plays the hand.
  - Single-player odd-chip and winner rules apply.
  - The new Payout History footnote.
  - No empty "You are dealt ." line for a busted host.
- **Room NPCs fold less with high-tenacity short stacks.** Measured on 3,000 seeded decisions each (flop,
  strength 0.40, 100 to call into 300):

  | Spot | Old multiplayer copy | Shared `ai.py` |
  |---|---|---|
  | tenacity 10, stack 200 | 66.2% | 38.4% |
  | tenacity 5, stack 200 | 40.0% | 32.2% |
  | tenacity 1, stack 200 | 22.7% | 22.7% |
  | tenacity 10, stack 5000 | 0% | 0% |

- **Portraits:** layered NPC portraits gain the `outline.png` layer.
- **Rooms:**
  - countdowns no longer reject guest actions;
  - each screen counts down locally, and guests see "Starting next hand…" for a moment at the end;
  - Hold'em late joiners take busted NPC seats with a buy-in;
  - a waiter no longer freezes the table;
  - a takeover seat starts with fresh NPC reads;
  - no XP for returned chips or own-chip pots;
  - a version-mismatch notice;
  - party late joiners get seated;
  - a disconnected Blind Man's Bluff seat auto-checks or folds;
  - Blind Man's Bluff "Table finished" when fewer than 2 can ante (a newcomer restarts it);
  - room Blind Man's Bluff uses the single-player pot, raise and winner rules;
  - Score Four solves are checked by the host and retried;
  - Roulette bets below $1 are refused.
- **DMH PvP:**
  - mouse-look speed scales with the window (as single-player);
  - a disconnect shows a result screen (forfeit win or CONNECTION LOST);
  - invalid guest data is ignored.
- **Window:**
  - opens at the single-player default size for the screen, clamped and centred;
  - F11 is letterboxed desktop fullscreen;
  - the handed-over size and fullscreen choice are honoured;
  - DPI aware when started on its own;
  - Options greys out sizes too large for the screen.

**Single-player**
- The harness is IDENTICAL (64/64 scenes, 18/18 journeys, baseline `ff82492`). No scene or checkpoint changed.
- Two single-player-visible changes are outside what the harness can see:
  - The packaged game starts again (N68). The move-stage build crashed with `ModuleNotFoundError:
    solitaireplus.menus.splash`, as the B86 base does.
  - On screens whose work area is smaller than about 1366x800, the window now really gets its smaller default
    size (for example 1088x612 on a 1366x768 laptop), and a smaller size the player drags to stays. Before, SDL
    held it at 1366x768, so the window did not fit, and `present()` retried the resize on every frame. This is
    the repair's `_allow_small_window()`. It is a W1 fix, guarded by `test_small_window_sizes_really_apply`.

**Un-quarantine** (`tests/KNOWN_FAILURES.txt`)
- Removed (4):
  - `test_menu_followup.test_lobby_quit_button_ends_the_loop`: rewritten for the current hub; passes.
  - `test_table_flow.test_last_payout_survives_new_hand`: `room.mode=None` in its setup; passes.
  - `test_six_seat.SixSeatTests.test_late_join_no_mid_hand_takeover` (B68): re-run here 50 times with
    `run_tests.py --worker`, 50/50 passed. Every `@@RESULT` was read: the worker exits 0 even when a test fails.
  - `test_six_seat.SixRelayTests.test_six_clients_and_late_join` (B67): re-run here 20 times, 20/20 passed.
- Left: `multiplayer:test_table_polish.PolishTests.test_local_animation_never_mutates_game_and_sound_edges_once`
  (the fake game lacks `player_action_text`) is the only multiplayer line. The 8 game lines are unchanged:
  3 `/workspace/scratch` paths, 2 DMH weapon, and 3 NPC development.

**Verification**
- `tools/run_tests.py`: PASSED.
  - game: 120 files, 1,100 tests (8 quarantined failures, as before);
  - multiplayer: 17 files, 141 tests (1 quarantined failure);
  - the move stage had game 118/1,056 and multiplayer 14/78.
  - Run again after the build and the docs: PASSED.
- `screen_harness.py compare --baseline ff82492…`: IDENTICAL 64/64. Then `replay.py compare --baseline ff82492…`:
  IDENTICAL 18/18. They ran one after the other.
- Packaged (`build_release.ps1 -SkipTests`, in this worktree):
  - `SolitaireNet 1.1.0 ok; connectors: tcp, tls, ws, wss`; the updater self-test exited 0;
  - `release/selftest-multiplayer.txt` lists 22 modules and ends with `PASSED: every multiplayer module
    imported`.
  - `build/SolitairePlus/PYZ-00.toc`: all 20 solitaireplus modules imported by the shipped `multiplayer/*.py`
    are present. So are all 58 modules named in importlib or `lazy()` strings, including
    `solitaireplus.menus.splash`, `solitaireplus.debug.poker_select_screen` and
    `solitaireplus.career.leaderboard_bio_screen` (missing before this commit).
  - 10 s runs with a temporary LOCALAPPDATA (`auto_update_check` false, so no update check went to the
    internet): `SolitairePlus.exe` was still running after 10 s, and its newest `game-*.log` is 0 bytes;
    `SolitairePlus.exe --multiplayer` the same, 0 bytes.
- Local two-player test (relay started from source with `--bind 127.0.0.1 --port 50111 --ws-port 50112`; it
  listened on 127.0.0.1 only):
  - `relay_probe.py tcp://127.0.0.1:50111`: 6-character code, party games supported, "this relay is up to date".
  - Scratch `two_player.py` (every address checked to be 127.0.0.1 before a peer opens) printed 72/72 OK,
    `TWO_PLAYER PASSED`:
    - raw `NetPeer`, with the packaged `SolitaireNet.exe` and with the source service, over tcp:// and ws://:
      v2 room code, joined/peer_joined, guest action and chat to the host, host lobby to the guest,
      `'wss'` in the connectors, a v1 duel pair with hello both ways, and every peer and service closed;
    - `RoomTable` games through the packaged service:
      - a Hold'em hand to the end: chips conserved 30,000 = 30,000; guest revision = host revision (30); 162
        guest views checked with no other seat's cards before the showdown; every state message the guest
        received carried `protocol` 3, and no version notice;
      - a Blind Man's Bluff hand: chips conserved, and the guest never saw its own card;
      - a Score Four round: a wrong `solved` claim was refused, and a valid steps solve won the round;
    - no log files in the run's temporary LOCALAPPDATA.
  - Windows. Two temporary LOCALAPPDATA folders ("Alice", "Bob"), with UTF-8 files without a BOM.
    `connection_settings.load()` was checked to give `tcp://127.0.0.1:50111` before either window started.
    - The source window (`main.py --multiplayer`) and the packaged window (`SolitairePlus.exe --multiplayer`)
      both opened at client 1712x963, window (103, 87, 1817, 1082), centre offset (0, -0.5), inside the work
      area (0, 0, 1920, 1152), caption "Solitaire+ Multiplayer", DPI awareness 2, window DPI 96.
    - With posted input, the source window created a room (code TBCD8Q) and the packaged window joined it: both
      lobbies showed Alice and Bob "Connected".
    - The only TCP connections to anywhere outside the processes were from `python -m netservice` (the source
      window's service) and `SolitaireNet.exe` (the packaged window's) to 127.0.0.1:50111.
    - Starting the table and playing a hand by posted clicks did not work (see Manual items).
    - Both `game-*.log` files are 0 bytes, and there is no `netservice.log`. That file is written only when the
      service crashes, so the plan's "netservice.log shows the connection" cannot be checked from it.
  - The relay, both windows and every service process were stopped afterwards.
- Window checks. This PC now runs at 100% (window DPI 96): monitor 1920x1200, work area (0, 0, 1920, 1152).
  Default start: client 1712x963, window (103, 87, 1817, 1082). F11: (0, 0, 1920, 1200). Options 1366x768 →
  (276, 185, 1644, 985); 1600x900 → (159, 119, 1761, 1051); 1920x1080 and 2560x1440 greyed out.
  - `window_check.py source`: 41/41 ok. Saved 2560x1440 was clamped to 1712x963; saved fullscreen started at
    (0, 0, 1920, 1200).
  - `window_check.py packaged`: 11/11 ok (start-up and 5 x F11).
  - `window_check.py source --multiplayer`: 110/110 ok, with DPI awareness 2, caption right, and no legacy or
    cursors module loaded:
    - no saved size, saved 2560x1440 and inherited 2560x1440 → 1712x963, centred;
    - inherited 1600x900 → client 1600x900 at (159, 119, 1761, 1051);
    - inherited 1088x612 → client 1088x612 at (415, 263, 1505, 907);
    - saved fullscreen and inherited 1600x900 + FULLSCREEN=1 → (0, 0, 1920, 1200).
  - `window_check.py packaged --multiplayer`: 84/84 ok, the same rectangles and DPI awareness 2.

**Open questions** (default taken in brackets)
- NPC raise rule [no change needed]. B86 already put "no bet or raise unless somebody can answer" into
  `can_npc_raise`/`npc_raise` for every table, so single-player and room NPCs follow it. The room adds the same
  check for guest humans, and the host has it through `can_player_raise`.
- Mixed-version rooms [no relay change; a protocol stamp and an "Update both games" notice for new guests].
  Guests on the current release can still join a new host, with three effects:
  - their Score Four solves are refused (they send no steps), so they cannot win a round;
  - their next-hand countdown stays at "Next hand in 6 seconds" for the whole pause, because the host no longer
    bumps the revision every second;
  - they get no warning, because only new guests check the stamp.
  - A new guest at an old host sees the notice. Redeploy the relay with a version-3 gate instead?
- B68 seating [a busted NPC seat with the normal buy-in first; otherwise take over a funded NPC seat and its stack,
  as today]. Should humans still inherit a funded NPC's stack at all?
- Party late joiners, B71 [seat order: Empty, then a disconnected human's seat, then an NPC seat (a broke NPC's
  first). The buy-in goes to an empty or broke seat; otherwise the joiner inherits the stack. Score Four seats
  joiners only on return to the lobby]. Confirm.
- B72 follow-on [keep dealing a disconnected Blind Man's Bluff seat in, paying antes, until a waiter takes it or it
  cannot ante]. Sit it out from the next hand instead?
- B73 ["Table finished" with no new button; a newcomer's buy-in restarts the table]. Give the host a "Room lobby"
  button?
- B78 [minimum Roulette bet $1]. A $10 minimum would match the chip tray.
- B83 [a forfeit "YOU WIN" only when the relay reports that the other player disconnected; otherwise "CONNECTION
  LOST" with the last score; PvP records no stats or XP]. OK?
- For information: the plan section 4 items above (NPC fold rates, outline layer, mouse-look scaling,
  single-player window rules) came with the merge.

**New findings**
- **N68 (H, already fixed on the branch): the packaged game crashed at start.**
  - `solitaireplus/app/loop.py` loads `solitaireplus.menus.splash`, `solitaireplus.debug.poker_select_screen` and
    `solitaireplus.career.leaderboard_bio_screen` only through importlib strings, so PyInstaller left them out.
  - The newest `game-*.log` showed `ModuleNotFoundError: No module named 'solitaireplus.menus.splash'`. The B86
    base `707be96` has the same `loop.py` and spec, so the bug came in when the screens moved to `SCREENS`
    strings.
  - Fix in the Phase 11 worktree: the three modules in the spec's game `hiddenimports`. The branch already had
    the wider fix, "Phase 7 (fix): packaged game ships every solitaireplus module" (`collect_submodules`), so at
    integration the three entries were dropped. A check of `PYZ-00.toc` finds every module named in an importlib
    or `lazy()` string.
  - The packaged self-tests did not catch it, because the multiplayer self-test imports only `multiplayer/`
    modules. `tests/test_packaged_game_modules.py` (from the Phase 7 packaged fix) now guards it.
- **N69 (L): an old guest at a new host sees a frozen next-hand countdown.**
  - The new host bumps the revision once per finished hand (B70). The current release's `room_view` reads only
    `next_hand_seconds`, so the guest shows "Next hand in 6 seconds" for the whole pause until the deal arrives.
  - Nothing breaks, and new guests count down from `countdown_at`.
  - It follows from the chosen B70 design and is part of the mixed-version open question.
- **N70 (L, test evidence): the B80 guest-raise tests also pass on the code before the fix.**
  - On `ff82492` a guest's raise over an all-in was already refused twice: `room_table` checked `can_npc_raise`
    when there was a bet, and B86's `npc_bet`/`npc_raise` run the "somebody can answer" check themselves.
  - The new early refusal changes no outcome. It only returns before `npc_bet`'s `ensure_*` calls.
  - `test_guest_cannot_raise_when_no_one_can_respond` and `test_can_raise_agrees_for_every_human_seat` guard
    the behaviour but do not prove the change.
- **N71 (L, docs, fixed at integration): wording outside this group's sections was out of date.**
  - The intro of `docs/POKER_RULE_CHANGES.md` said "Online play is unchanged until Phase 11" (only the
    "Online play" section was in scope).
  - `docs/NETWORKING.md` did not describe the room message stamp (`protocol`, `ROOM_PROTOCOL = 3`) or the
    `countdown_at`/`host_now` countdown fields. Both are updated now.
- **N72 (info, test tooling): posted mouse input does not reliably reach an SDL window.**
  - With another process's window, or the cursor, elsewhere, SDL's `WM_MOUSELEAVE` handling moves its mouse
    position back to the real cursor, and the room and hub use the frame's mouse position.
  - Moving the real cursor (`SetCursorPos`) and raising the target window made some clicks work, but not all.
    The Start table click never registered.
  - A scripted full hand through two windows needs another way in (for example a test-only input hook), or a
    person.

**Stray files**
- `%USERPROFILE%\Documents\standalone_preview.png` (outside the repository) was written by the now-deleted
  `multiplayer/tests/test_standalone.py` (`'../standalone_preview.png'`). Dan may delete it.
- The same test, run at the base inside a sprint worktree, also left
  `%USERPROFILE%\Documents\SolitairePlus\.harness_out\wt\standalone_preview.png` (harness area, never
  committed). Deleted at integration.

**Manual items for Dan**
- Play one Hold'em hand through two Multiplayer windows: one from source and one packaged, or two packaged with
  different LOCALAPPDATA folders, against a relay on 127.0.0.1. The recipe is in `docs/TESTING.md`, "Local
  two-player test". Room creation and joining were done by script; starting the table and the hand were not.
- While doing that, check that the picture fills the window. The `PrintWindow` captures taken during the test
  showed the 1366x768 picture at 1:1 in the middle of the 1712x963 client, while mouse input was mapped as if it
  filled it. That is most likely a capture artefact: the screen itself could not be seen (a screen saver desktop
  was active). The window code is the one single-player has used since Phase 2.
- Answer the open questions above.

## Phase 7 (fix, late): B44 in Score Four, career activities and Head-to-Head

The brief's B44 list also names Score Four, the career activities UI and Head-to-Head, and says they may be fixed in
their own phases. Phases 4, 5 and 8 did not fix them, so this commit does. It was found while drafting the hand-back
bug table. Every font now comes from the shared cache (`ui_text.get_font`) with the same font, size and flags as
before, so the screens look the same.

- **`games/cards/score_four_ui.py`**: these now use `ui_text.get_font(None, size)`:
  - the opponent name fit loop (`draw_opponent_panel`, 2 sites);
  - the `text()` helper that every Score Four screen uses;
  - the hint line wrap in `draw_score_four_table`;
  - the solution fit loop in `draw_round_solution`.
- **`career/activities_ui.py`** (Bigfoot and Alien nights): `lines()`, `text()`, the map labels in `draw_map` and the
  story page font in `draw` now use `ui_text.get_font(None, size)`.
- **`games/solitaire/head_to_head_ui.py`**:
  - the "Rated race" note on the opponent screen uses `ui_text.get_font(None, 27)`;
  - the race countdown digit uses `ui_text.get_font("georgia", 96, bold=True, sysfont=True)`.
- A scan of the rest of `solitaireplus/` found the same pattern in more places, fixed the same way:
  - **`games/solitaire/restart.py`**: the "Restart this hand?" prompt built 5 fonts per frame. This one is live.
  - **`games/arcade/ace_invaders_game.py`**: `_draw_enemy` built a font per enemy per frame for the enemy glyph. The
    glyph is drawn only when both the enemy art and the card-front art are missing; both ship, so normal play never
    reaches it.
  - **`games/solitaire/card.py`**: `Card.draw` built a `SysFont(None, 28)` per face-up card. Nothing in the game
    calls `Card.draw` (the table draws its own cards in `rules.py`), so this change is only for consistency.
- After the fix, every `Font`/`SysFont` call in `solitaireplus/` outside `ui/text.py` runs at import time, in a
  constructor that runs once, or behind a cache. The one exception is the Dead Man's Hand PvP duel (N73), which
  Phase 11 was editing at the time.

**Test:** `tests/test_frame_font_sites.py` (extended).
- `test_screens_build_their_fonts_only_once` draws each screen twice and counts `pygame.font.Font` / `SysFont`
  calls. The second frame must build no font.
- `test_shared_fonts_draw_the_same_pixels_as_fresh_ones` checks that cached fonts draw the same pixels as fresh ones.
- New screens, each with a fixed state (and a fixed `time.monotonic` for the Score Four timers):
  `score_four_mode_select` (with the rating overlay), `score_four_difficulty_select`, `score_four_table_solo_hint`,
  `score_four_table_competitive_npc_solved` (long opponent name and long solution, so both fit loops run),
  `career_activity_intro`, `career_activity_choices`, `career_activity_alien_intro`,
  `draw_head_to_head_selection`, `draw_head_to_head_hud_countdown`, `restart_prompt`, `ace_invaders_fallback_enemy`
  and `card_draw_unused_by_game`.
- The old `NOT_COUNTED = {'score_four_ui.py'}` exception is gone, so `draw_score_four_opponent_select` now counts
  Score Four's helpers too.
- Before the fix, 13 subtests failed. A reviewer put the old call back at each of the 15 fixed lines, one at a time:
  every one made the test fail. A seeded pixel hash of all 21 test screens matched before and after.

**Results:**
- `tools\run_tests.py` → `PASSED`. No new `KNOWN_FAILURES.txt` lines.
- `screen_harness compare` against "Phase 11 (move)" → `IDENTICAL 64/64 scenes`; `replay compare` →
  `IDENTICAL 18/18 journeys`.

**New findings (not fixed here):**
- **N73:** `games/dead_mans_hand/pvp.py` (`PvPGame._render_remote`, about lines 407 and 412) builds
  `Font(None, 10)` and `Font(None, 8)` every frame for the opponent's name and weapon plate. Fix:
  `ui_text.get_font(None, 10)` and `ui_text.get_font(None, 8)`.
- **N74:** `multiplayer/` still builds fonts per frame: `main.py` (hub and room buttons and the table status),
  `mp_appearance.py` (the avatar initial when there is no image), `mp_hub.py` (the title fallback), `party_view.py`
  (lobby code and roulette chip labels) and `room_view.py` (a `SysFont` per button whose label is too wide; see B84).
- **N75:** `Card.draw` in `games/solitaire/card.py` has no caller in the game. It is dead code.

## Phase 11 (fix, late): per-frame fonts in the Dead Man's Hand duel and the Multiplayer screens

This fixes N73 and N74 from the B44 late fix report. Every changed font now comes from the shared cache (`ui_text.get_font`), with the same font, size and flags as before, so the screens look the same. Multiplayer already imported `solitaireplus.ui.text` (through `score_four_ui`), so no new single-player module is loaded.

- **N73, fixed.** `games/dead_mans_hand/pvp.py`:
  - `PvPGame._render_remote` built `Font(None, 10)` and `Font(None, 8)` every frame for the opponent's name and gun plate. It now uses `ui_text.get_font(None, 10)` and `ui_text.get_font(None, 8)`.
  - `DeadMansHandPvPMode.__init__` built 3 fonts (34, 25, 60). `multiplayer/main.py` makes a new mode each time the duel lobby opens, so these were built on every click. They now come from the cache too.
- **N74, fixed.** Each site in the base was checked:
  - `main.py` (top buttons, table status), `mp_appearance.py` (avatar initial) and `room_view.py` (smaller font for a too-wide button): B84 had already cached these. No change.
  - `mp_hub.py`: the "SOLITAIRE+" title, drawn when the logo picture is missing, uses `ui_text.get_font(None, 64)`.
  - `party_view.py`: the lobby room code uses `ui_text.get_font(None, 48)`. The Roulette chip labels on the board use `ui_text.get_font(None, 13)`. That one ran on every Roulette frame, with or without bets.
- **Scan.** Every other `Font`/`SysFont` call in `multiplayer/` and `solitaireplus/` was checked (`legacy.py` has none and was not touched). Each one runs at import time, in a constructor that runs once, or behind a cache.

**Tests (written first; they failed before the fix):**
- `tests/test_dead_mans_hand_pvp.py`, new `FrameFontTests`. It empties the font cache, then counts `pygame.font.Font` / `SysFont` calls.
  - `test_duel_with_the_opponent_in_view_builds_fonts_once`: the host faces the guest, and the duel is drawn twice. The first frame must build `(None, 10)` and `(None, 8)`. The second frame must build nothing.
  - `test_opening_the_lobby_again_builds_no_font`: opening and drawing the lobby a second time builds no font.
- `multiplayer/tests/test_frame_fonts.py` (new) draws each Multiplayer screen twice. The second draw must build no font. The tables come from the real host code (`party_authority`, seeded), and `get_ticks` is fixed.
  - The three fixed screens must build their font on the first draw: hub without the logo, party lobby, and Roulette with chips and chat open.
  - Also covered: hub with the logo (Hold'em and duel panels), Score-Four, Blind Man's Bluff, the Hold'em room table, the profile screen and the options panel (with a temporary LOCALAPPDATA).
- Before the fix, 5 tests failed (2 pvp, 3 multiplayer). Putting the old call back at each of the 8 fixed lines, one at a time, made a test fail every time.
- A pixel hash of the hub fallback, party lobby, Roulette board, duel frame and duel lobby was the same before and after the fix. The screen harness has no multiplayer scenes, so this was checked separately.

**Results:**
- `tools\run_tests.py` printed `PASSED`. No new `KNOWN_FAILURES.txt` lines. `test_shared_ui_usage` (including `test_multiplayer_import_does_not_start_single_player`) passes.
- `screen_harness compare --baseline 2448d18` gave `IDENTICAL 64/64 scenes`. `replay compare --baseline 2448d18` gave `IDENTICAL 18/18 journeys`.
- `tools\window_check.py source --multiplayer` was not run. It is optional, and it sends F11 to a real window on the desktop.

**New findings (not fixed here):**
- **N76:** `multiplayer/party_view.py` `draw_lobby` still says "Share only this 5-digit code." Room codes are now 6 letters/digits (CHANGELOG, Online play). Changing it changes what the lobby shows, so it was left alone.
- **N77:** `DeadMansHandGame._font` / `_dmh_font` (`games/dead_mans_hand/game.py`) cache fonts per game object. Each new duel (`PvPGame`) and each single-player run builds its HUD fonts again on its first frame, including the Dead Man's Hand TTF files. That is once per game, not per frame. A move to `ui_text.get_font` would need `set_bold` to move into `get_font`'s `bold` flag.

## Phase 12: cleanup

One commit. The work was done in detached worktrees: the parts that did not depend on Phase 11 on top of Phase 10
(`73dc94c`), and the rest in four groups on top of Phase 11 and the late fixes, each reviewed. It was then put
together on top of "Phase 11 (fix): per-frame fonts in the Dead Man's Hand duel and the Multiplayer screens" and
squashed into this commit. Nothing in it changes what the game shows. The one change a player can notice is log
pruning (#15). Test file paths in the first sections are the paths before the move into `tests/<area>/`.

### legacy.py emptied and deleted
- `solitaireplus/legacy.py` (1,992 lines on the integration line) is gone. Every name it still held has a home.
  Every `legacy.<name>` use in `solitaireplus/`, `tests/`, `tests/support/`, `tools/harness/sim.py` and
  `docs/TESTING.md` now points at that home, through lazy imports as before.
- **Start-up** runs from the new `app/startup.py`. `app/loop.py` imports it where it used to import `legacy`, so
  modules are first imported, engines built and state defaults set in the same order as before. Start-up does
  this, in order:
  - imports the modules in the old order;
  - registers the reward cosmetics;
  - starts pygame and opens the window;
  - sets the state defaults;
  - prints the NPC portrait count.

  `app/startup.py` defines nothing that other modules use.
- Where the rest went:
  - `games/solitaire/table.py` (new): the Solitaire engine `game` (still built at its old place in start-up),
    `VERIFIED_DEALS_ENABLED`, `sync_selected_cosmetics`.
  - `menus/help_content.py` (new): `HOW_TO_PLAY_CONTENT`, `HELP_NAVIGATION`, `HELP_CONTENT` and the History pages
    merge.
  - `npc/game_portraits.py` (new): `NPC_PORTRAIT_STYLES`, `draw_npc_portrait`, `get_npc_portrait_surface`,
    `npc_icon_cache`. `get_npc_icon_surface` came here too and was then deleted as dead code (below).
  - `ui/images.py` (new): `get_event_ui_asset` and its cache, `get_cover_scaled_ui_asset`,
    `scale_surface_to_fit`.
  - `app/game_globals.py` (new): `game_namespace()`. It now adds by name the 8 things it could only find in
    `legacy.py`: `game`, `draw_npc_portrait`, `REWARD_CURSOR_IDS`, `CASE_ITEMS`, `ARCADE_PRIZE_CATALOG`,
    `ACHIEVEMENT_DEFINITIONS`, `LEVEL_XP_THRESHOLDS` and `award_level_packs`.
  - `app/state.py`: `career_event_start_arcade_tokens` and `_tickets` (default 0). `app/loop.py`:
    `loop_post_event_updates`.
  - `menus/free_play_select.py`: `FREE_PLAY_GAME_IDS`, `free_play_game_rects`, `finish_free_play_sandbox`,
    `leave_free_play_game`, `get_free_play_return_state`.
  - `profile/leveling.py`: `is_game_unlocked`, `unlock_achievement_cosmetic`, `queue_achievement_popup`,
    `update_achievement_popup`.
  - `profile/cosmetics.py`: `REWARD_CURSOR_IDS`, `register_reward_cosmetics()`.
  - `profile/profile_editor.py`: `get_profile_avatar`.
  - `career/hub_screen.py`: `career_hub_controls`.
  - `career/calendar.py`: `get_current_career_activity_index`.
  - `career/news_screen.py`: `maybe_add_monthly_flavor_news`.
  - `career/career_rewards.py`: `lose_fans_for_bad_result`.
  - `career/events/event_select_screen.py`: `get_unlocked_games_for_event`.
  - `menus/customize.py`: `CUSTOMIZE_BACKGROUNDS`.
  - Deleted, because nothing read them: `how_to_play_tab`, `how_to_play_tab_rects`, `free_play_rect`,
    `career_mode_rect`.
- Checked: after start-up the state, the random state, the catalogs and the help pages are identical, and every
  module that existed before is first imported in the same order.

### rules.py split
- `games/solitaire/rules.py` went from 4,360 lines to 571. It keeps 9 methods of `Game`: `__init__`,
  `set_deal_mode`, `get_deal_status_label`, `new_race_game`, `new_game`, `set_difficulty`,
  `apply_difficulty_rules`, `set_challenge` and `clear_challenge`. It also has a new module docstring that maps the
  package.
- `Game` gets its other 65 methods from 8 topic mixins:
  `class Game(LayoutMixin, MovesMixin, ScoringMixin, HintMixin, AutoSolveMixin, AnimationMixin, DrawingMixin, ControlsMixin)`.
  - `layout.py` `LayoutMixin` (6 methods, 226 lines): tableau spacing, card and drop-target rects, the card, column
    or foundation under the mouse.
  - `moves.py` `MovesMixin` (15 methods, 833 lines): placement rules, the stock, the `move_*` methods, the
    all-or-nothing rule, auto-moves, `save_undo_state`, `undo`.
  - `scoring.py` `ScoringMixin` (8 methods, 227 lines): `record_move`, elapsed time, round score, XP and remark, the
    round summary, `is_game_won`, `check_for_win`.
  - `hints.py` `HintMixin` (4 methods, 544 lines): the hint system.
  - `auto_solve.py` `AutoSolveMixin` (4 methods, 366 lines): auto-solve and `debug_auto_solve_state`.
  - `animation.py` `AnimationMixin` (6 methods, 320 lines): the flip and victory animations.
  - `drawing.py` `DrawingMixin` (13 methods, 650 lines): card art and every `draw_*` table method.
  - `controls.py` `ControlsMixin` (9 methods, 759 lines): mouse input and `handle_event`.
- `constants.py` (45 lines) holds the module constants (base size, colours, tableau layout, animation timings).
  `rules.py` imports each one by name, without a star-import. So every old `rules.<name>` still works, including
  `BASE_WIDTH`/`BASE_HEIGHT`, which about 40 callers import, and the `rules.pygame` patch target. No caller changed.
- Verified by an AST check against the parent commit:
  - all 74 methods are present, each exactly once;
  - every method body is AST-identical, with no renames;
  - no name a method uses is left unresolved in its new module;
  - all 44 old module-level names can still be imported from `rules`, and the 17 constants have their old values;
  - the MRO is `Game` first, then the 8 mixins in order.
- Start-up order is unchanged. `rules.py` keeps its original import block word for word and in the same order.
  The mixins import only modules that block already loads.
- Five 3-line section headers were added. In each place the original header had moved to another module with its
  neighbouring method.
- New files use CRLF, like their siblings. Packaging needs no change: the `.spec` uses
  `collect_submodules('solitaireplus')`, and `make_manifest` globs `solitaireplus/**/*.py`.

### Dead code deleted
How each name was checked:
- `grep -w` over `main.py`, `solitaireplus/`, `tests/`, `tools/` (including `tools/harness`), `multiplayer/`,
  `netservice/`, `updater/` and `installer/`, in `*.py/json/spec/ps1/md/txt`, string literals included. The only
  hits were the definition, the brief and report text, and old move plans in `tools/refactor/specs/`.
- An AST scan: no Name or Attribute load, string constant or keyword argument uses any of these names.
- At the `154b890` baseline (`git grep -w -c`), each name appears exactly once in `main.py` (its definition), so it
  was already dead before the restructure. Two exceptions, both explained below: `score_four_npc_font` and
  `blackjack_bet_dropdown_open`.
- Re-checked after the commit: `grep -w` finds none of them anywhere outside `tools/refactor/`.

From brief §5.1:
- `STATE_WIN` (`app/state_names.py`).
- `get_unlocked_games_for_event` (`career/events/event_select_screen.py`).
- `get_career_weekday_name` (`career/calendar.py`). `CAREER_WEEKDAY_NAMES` stays because `hub_screen` uses it.
- `get_npc_icon_surface` (`npc/game_portraits.py`). `npc_icon_cache` stays because `get_npc_portrait_surface` uses
  it.
- `get_selected_suit_snake_difficulty` (`games/arcade/machine_select.py`), a "backward-compatible alias" for
  `get_selected_suit_snake_mode`.
- `get_free_play_return_state` (`menus/free_play_select.py`).
- `draw_score_four_npc_panel` (`games/cards/score_four_screen.py`, 200 lines). Its helpers stay:
  `get_score_four_npc_progress` is read by `score_four_ui` through `namespace.get`.

Duplicate definitions and assignments from §5.1 were already fixed earlier:
- B45 (Phase 7) left one binding each for the three Hold'em sound helpers, `STATE_CAREER_NEWS`,
  `play_background_image`, `profile_switch_rect` and the career hub rects. `test_b45_duplicates` passes.
- `career_play_rect` was removed under B4.
- `blackjack_dealer_npc` is bound once, as `None`, in `state.py`.

Other dead code, clearly from `main.py` and never read:
- `fonts.score_four_npc_font`: its only reader was the deleted panel, so at `154b890` it had 2 hits, the definition
  and the panel's render.
- `fonts.blackjack_title_font`: never read. The casino-typography comment stays on the other blackjack fonts.
- `state.blackjack_bet_dropdown_open` (N2): write-only since the baseline. At `154b890` it had 9 hits: the default,
  2 `global` lines and 6 writes, with no reads. Removed: the default in `state.py` and the 6 writes in
  `event_select_screen`, `debug/actions`, `free_play_select` and `blackjack_screen` (3).
- `blackjack_screen.blackjack_change_bet_rect`: a zero-size Rect "kept for compatibility", and its comment.
- `holdem_screen` `TEXAS_HOLDEM_NPC_DELAY`, `TEXAS_HOLDEM_STREET_DELAY` and `TEXAS_HOLDEM_NEXT_HAND_DELAY`: never
  read. `TEXAS_HOLDEM_SESSION_END_DELAY` stays.
- `career/training.TRAINING_GAMES`: never read.
- `suit_snake.SUIT_SNAKE_DIFFICULTIES` and `get_suit_snake_difficulty`: labelled backward-compatible aliases, dead
  since the baseline. They are the engine-side twin of the `machine_select` alias.
- No import was added or removed, so start-up order is unchanged.

### Stray root files
- `verify_solitaire_state.py` is now `tools/verify_solitaire_state.py`.
  - `ROOT` is now `Path(__file__).resolve().parents[1]`, so the script still checks the repository root and still
    writes `SOLITAIRE_STATE_REPORT.txt` there. The docstring says how to run it.
  - Its "possibly misplaced files" scan now skips `.harness_out`. Without that, the harness worktrees were listed as
    misplaced copies of `main.py`.
  - Run from another folder, it found the right root and the report contained the expected sections. The report it
    wrote was deleted.
  - Nothing else referenced the old path. The only other mentions are in the brief and `tools/refactor/`.
- The root `test_dead_mans_hand_weapon_system.py` (N66) was merged into `tests/test_dead_mans_hand_weapon_system.py`
  and deleted. It now lives in `tests/games/dead_mans_hand/` (see "Tests moved into tests/<area>/" below); the test ids are
  unchanged. The root copy was an older prototype: 4 of its 8 tests failed on current code.
  - Ported: the right-mouse-button aiming wiring, and the sound-name map, now checked for every weapon's shot and
    reload.
  - New behaviour test `test_viewmodel_prefers_weapon_folders_but_keeps_old_pistol_fallback` (on a temporary art
    folder): `sniper/` beats `scar20/`, `pistol/pistol_ads.png` is found, the old `weapon.png` is used for the
    pistol, and a weapon with no art gets `None`.
  - New `test_hud_fonts_prefer_the_custom_font_files`: Scary Halloween, then `dead_mans_hand_numbers.ttf` or
    `dead_mans_hand_ui.ttf`, then the default font.
  - Dropped as duplicates or out of date: the old `assets/sounds/...` path strings, `PISTOL_VIEWMODEL` and
    `ADS_FOV`, and the old anchor numbers.
- `dead_mans_hand_pvp.py` is not at the root any more (§7 step 2). Phase 11 owns the pvp code.
- `main.py` (27 lines) and `version.py` stay at the root.

### Quarantine changes
Five lines left `tests/KNOWN_FAILURES.txt`. Each test now passes and checks current behaviour, and the two empty
section headers went too.
- The 3 `/workspace/scratch` preview-image tests now save into a `tempfile.TemporaryDirectory()` that is deleted
  afterwards (brief §7 step 6). Their assertions are unchanged:
  - `game:test_case_opening.CaseTests.test_reel_ends_on_committed_item_and_skip_does_not_purchase_twice`
  - `game:test_poker_recap.RecapTests.test_recap_render_and_chip_events_do_not_change_rules_or_repeat_sfx`
  - `game:test_table_polish.TablePolishTests.test_large_card_layout_and_next_hand_hit_target_render`
- The 2 out-of-date Dead Man's Hand source checks were rewritten as behaviour tests with the same names:
  - `test_hud_supports_custom_assets_without_health_or_ammo_numbers` builds a real `DeadMansHandGame` on a
    temporary folder of custom HUD PNGs and draws `_draw_hud`. It checks:
    - every custom file is used, including the Sniper icon found by its `asset_slug` name `sniper.png`;
    - the kill count is drawn and is the kills so far, not the enemies left (2 of 5 enemies dead, `total_kills = 7`,
      and a guard that the two numbers differ);
    - no drawn text contains the health (73), ammo (9) or magazine size (12). The text is recorded through the
      game's cached fonts and also through `pygame.font.Font` and `SysFont`;
    - the old weapon-id icon name `scar20.png` still loads, and a missing icon gives `None`.
  - `test_pistol_tuning_keeps_separate_ads_and_hip_muzzle_anchors`: for every weapon, the hip and ADS anchors and
    muzzle points differ, the hip anchor is right of centre, the ADS anchor is closer to the centre, and the ADS
    view is bigger. The pistol renderer puts the viewmodel exactly on the hip anchor and height when not aiming,
    and on the ADS anchor and height when fully aimed. The test no longer pins the numbers.
  - Mutation checks from the review repair, each run in memory:
    - showing the enemies left (`kill_count_value = alive`) now fails the HUD test;
    - so does a health number drawn through `pygame.font.Font`, `SysFont` or `self._font`;
    - so does an ammo number drawn through `self._dmh_font`.
- Still quarantined:
  - the 3 `test_npc_development` "rebalance" tests, by designer decision;
  - the multiplayer lines: Phase 11 removed six of them (fixed or deleted with their feature), and the last one
    went in the cleanups group (below).

### Tests that wrote outside a temporary folder
- `tests/test_packaging.py` `test_multiplayer_selftest_passes_from_source` now gives its child process
  `LOCALAPPDATA=<temp folder>`. A probe showed that without it, `main.py --multiplayer --selftest` wrote
  `SimpleSolitaire/logs/game-<pid>.log` into the real folder. With log pruning, the child could also delete real
  logs.
- `tests/test_multiplayer_launcher.py` `test_real_dispatch_uses_multiplayer_engine` had the same problem: its child
  runs `multiplayer/main.py`, which writes a game log and `SolitaireMultiplayer/profiles/profile_1.json`. It now
  runs in a `TemporaryDirectory` with `LOCALAPPDATA` pointed at it.
- `docs/TESTING.md`: new paragraph. Files a test writes go into a temporary folder. A test that runs `main.py` or
  `multiplayer/main.py` passes `LOCALAPPDATA=<temp folder>` in the child's `env`, because both start with
  `bootstrap()`. The quarantine section notes that the three image-folder tests were fixed, and its example line no
  longer names a test that now passes.
- Audit: each suite was run with `LOCALAPPDATA` pointed at an empty scratch folder. The game suite now writes
  nothing there. The multiplayer suite still did; see below.

### Log pruning (#15) and its test
- `app/runtime_support.py` has a new `prune_game_logs(logdir, current, keep=KEPT_GAME_LOGS)`, with
  `KEPT_GAME_LOGS = 10`. `bootstrap()` calls it right after `logging.basicConfig(...)`.
- It keeps the newest 10 `game-*.log` files by modification time, and this process's new log is always one of them.
- It only looks at files: a folder named `game-x.log` and any other file in `logs/` are never touched.
- It skips files it cannot delete silently and logs nothing, so a normal start still leaves the new log empty (the
  §10.2 packaged check). That covers a file locked by another running copy (Windows refuses to delete an open file)
  and a file that vanishes while it looks.
- An `OSError` from listing the folder skips pruning altogether.
- `tests/test_log_pruning.py` (6 tests) runs the real `bootstrap()` against a temporary `LOCALAPPDATA`, then puts
  back the working folder, root logger handlers and level, `sys.excepthook` and `threading.excepthook`. It checks:
  - the 10 newest are kept, the new log included, and older ones are deleted;
  - other files and a folder are left alone;
  - with only a few logs, all are kept;
  - an old log that has this process's name (a reused pid) is the current log: it is kept, appended to and counted;
  - a locked and a vanished log don't stop start-up, and nothing about them is written to the new log;
  - a log held open by another copy is skipped (Windows only);
  - the rest of `bootstrap()` is unchanged: working folder, WARNING level, one FileHandler on the new log, both
    exception hooks.
- Review repair: the fixture names are now `game-old00.log` and so on, from `old_log_names()`, so they can never
  match `game-<pid>.log`. Before that, the old numbered names failed under patched pids 90004, 80000 and 70008.
- `docs/TESTING.md` describes the test.

### Globals and the new no-globals test
- `games/solitaire/race_deals.py` keeps its verified deal pool in `_cache = SimpleNamespace(pool=None)` instead of
  `global _pool`. This was the last `global` statement in `solitaireplus/` (N65). The behaviour is the same: the
  pool loads and is verified once, on first use.
- `tests/test_no_global_statements.py` parses every `.py` file under `solitaireplus/`, plus `main.py`. It fails on
  any `ast.Global` node and on any call to `globals()` or `builtins.globals()`. Names that only contain the word
  pass, such as `game_globals` or a docstring that mentions `globals()`. It also checks:
  - that the scan really covers the game code (more than 100 files, `main.py` and `app/state.py` included);
  - that the detector catches all three forms;
  - that the race pool still loads and verifies once.
- Current state for checklist §10.4: no `global` statement and no `globals()` call in `solitaireplus/` or
  `main.py`. No `__file__` lookup outside `app/paths.py`.
- The per-area tests stay: `test_poker_ui_no_globals`, `test_cards_ui_no_globals`, `test_debug_no_globals` and
  `test_casino_frame_caches`. They also check each area's cache behaviour.

### Hold'em engine and UI split
holdem.py and holdem_ui.py are split into topic modules under solitaireplus/games/poker/. Game behaviour is unchanged. Every function and method moved verbatim and none were renamed. No file in solitaireplus/ is over 3,000 lines now. The largest is five_card_draw_ui.py at 2,599.

- holdem.py went from 4,714 lines to 1,399. TexasHoldemGame is now built from 5 mixins, the same way the solitaire rules.py split was done:
  - holdem_seats.py, 825 lines: SeatsMixin (chips, seat order, blinds, whose turn it is, seat views).
  - holdem_npc.py, 1,118 lines: NpcMixin (NPC actions, personality, hand strength, bet sizing).
  - holdem_betting.py, 492 lines: BettingMixin (apply_wager, the betting rules, the player's actions).
  - holdem_pots.py, 532 lines: PotsMixin (side pots, pot awards, fold wins).
  - holdem_showdown.py, 459 lines: ShowdownMixin (hand evaluation, the showdown, hand names).
  - holdem.py keeps the class settings, __init__, hand history, the deck, sessions, new hands, the betting-round reset and the streets. It also keeps run_next_npc_action. Tests patch holdem.decide_poker_action, and that patch only works where the method looks the name up.
- holdem_ui.py went from 7,241 lines to 1,867. It keeps draw_texas_holdem, get_texas_holdem_action and the session reset. It re-exports every old name with explicit imports. The 8 topic modules are:
  - holdem_ui_state.py, 325 lines: the one _ui holder, action names, log sizes, colours, HUD rects, the log and chat histories, the Quick Chat queue, fonts and chip images.
  - holdem_ui_widgets.py, 359 lines: translucent panels, buttons, fitted text.
  - holdem_ui_options.py, 1,077 lines: the buy-in screen, the Options overlay, table settings and delays.
  - holdem_ui_pot.py, 1,073 lines: the pot stack, chip and wager animations, payouts, the showdown banner.
  - holdem_ui_cards.py, 571 lines: card faces and backs, deal and flip animations.
  - holdem_ui_log.py, 887 lines: the GAME LOG / TABLE CHAT panel and Quick Chat.
  - holdem_ui_controls.py, 844 lines: the bet slider, manual bet entry, the action panel.
  - holdem_ui_hud.py, 554 lines: the player's hand text, the dealer and blind badges, the player HUD.
- Proof: an AST check against e7d8e80 finds all 71 functions, 108 methods and 6 class settings exactly once, with the same source. It also finds all 77 non-import module statements exactly once. Every old name still imports from holdem / holdem_ui. Every name a new module shares with the old module is the same object, so module state (_ui, the histories, the font cache) is still one object. Both old modules keep their import block first and in the same order, so the import order and seeded RNG do not change.
- Tests: the log-panel test now patches the squash helper in holdem_ui_log.py, where the log code looks it up. The font-cache test expects the showdown banner font in holdem_ui_pot.py. The no-globals and debug-hotkey checks scan the new modules. Each one now has a test that fails if a holdem_ui*.py file is not in its list: test_every_holdem_ui_module_is_checked and test_every_holdem_ui_module_is_scanned. A reviewer found that the debug-hotkey check had no such guard. I added it and checked that it fails when an unlisted holdem_ui_*.py module is added.
- Docs: POKER_RULE_CHANGES.md "Where the rules live", the paths note in B86_POKER_AUDIT.md, and the comment in state.py. docs/TESTING.md and docs/NETWORKING.md do not name these files, so they needed no change.
- Line counts in solitaireplus/games/poker/: five_card_draw_ui 2,599; seven_card_stud_ui 2,544; holdem_ui 1,867; seven_card_stud 1,646; ai 1,519; holdem 1,399; holdem_screen 1,259; holdem_npc 1,118; core 1,108; holdem_ui_options 1,077; holdem_ui_pot 1,073; five_o 989; five_card_draw_screen 988; holdem_ui_log 887; seven_card_stud_screen 865; five_card_draw 851; holdem_ui_controls 844; holdem_seats 825; blind_mans_bluff 592; quick_chat 582; holdem_ui_cards 571; holdem_ui_hud 554; holdem_pots 532; holdem_betting 492; holdem_chat 475; holdem_showdown 459; blind_mans_bluff_ui 432; five_o_ui 423; holdem_ui_widgets 359; holdem_ui_state 325; strategy 281; variant_quick_chat 274; recap 220; blind_mans_bluff_screen 207; five_o_screen 207; log_rows 191; speech 159; npc_inputs 146; quick_chat_adapter 142; bluff_presentation 82; learning 75; table_stakes 55; niche_common 40; ui_assets 38; table_timers 28; turn_flow 12; __init__ 1.
- Checks: full suite PASSED. screen_harness compare against e7d8e80 is IDENTICAL (64/64), then replay compare is IDENTICAL (18/18).

### Tests moved into tests/<area>/
The 145 game test files moved out of the flat `tests/` folder with `git mv`, so history follows. They now sit in `tests/app`, `ui`, `menus`, `profile`, `career`, `npc`, `games/<area>` (solitaire, poker, casino, cards, arcade, cryptid, dead_mans_hand), `debug`, `packaging`, `updater` and `netservice`. `tests/support/` and `tests/KNOWN_FAILURES.txt` stay. `multiplayer/tests/` did not change. Test ids still use the file name, so the quarantine list did not change.

- Fixed in the moved files: the repo-root depth from `__file__` (28 files), imports of other test files (`from tests.app import ...`, `tests.career`), the test_shared_imports path in test_packaging, and docstrings that name test paths. docs/NETWORKING.md and a `multiplayer/net_client.py` comment now use the new path.
- The new folders have no `__init__.py`. One there would hide the real `updater` and `netservice` packages and the standard-library `profile` module. `tools/run_tests.py` stops with an error if a test folder has one.
- Review fix: that check only ran when the runner searched the suite. A worker given a `.py` path skipped it, and full runs give every worker a path. The check now runs for every target. New test `tests/packaging/test_run_tests_layout.py` (5 tests). 2 of them failed before the fix.
- docs/TESTING.md has one line per folder, says where new tests go, and explains the no-`__init__.py` rule.
- Proof: the per-file test counts before (e7d8e80) and after match file for file for all 145 moved files and all 17 multiplayer files (game 1237 tests, multiplayer 141). The only new line is the review test, so the game suite now has 146 files and 1242 tests. The quarantine lines are the same. Each test file is found exactly once. Full suite PASSED. Screen compare 64/64 and replay compare 18/18 IDENTICAL against e7d8e80.

### tools/refactor, Card.draw, README, the last multiplayer quarantine line, B42, checklist
- **tools/refactor/ and requirements-dev.txt deleted.** References were searched in docs/, tools/ (harness included), tests/, multiplayer/tests/, build_release.ps1, SolitairePlus.spec, .github/workflows/, CHANGELOG.md and README.md. Only docs pointed at the tool. The one markdown document in it, `specs/phase11_plan.md`, moved to `docs/dev/PHASE11_PLAN.md` (git mv). The four links to it in `PHASE_REPORTS.md` (N36, Phase 11 move, Phase 11 fix) and `B86_POKER_AUDIT.md` now point there. The Phase 1 report sent readers to `tools/refactor/phase1_move.py` for the full old-to-new module table. It now says the file was deleted in Phase 12 and gives `git show d924025:tools/refactor/phase1_move.py` (d924025 is the Phase 1 commit on the branch). The other mentions in PHASE_REPORTS.md ("plan from tools/refactor/specs/phaseN.json" and the like) and RESTRUCTURE_BRIEF.md only describe what was done, so they stay. No test tested tools/refactor code, so no test was deleted. AGENTS.md does not exist in the repo yet, so there were no lines to report. libcst is still installed in the shared venv (the orchestrator removes it).
- **Card.draw deleted (N75).** A repo-wide search (solitaireplus, multiplayer, tools, tests, main.py, netservice, updater) found no caller. The Solitaire table draws cards with `DrawingMixin.draw_card_sprite`. Only Card.draw used the `import pygame` and `ui_text` imports in card.py, so they were removed too. The `card_draw_unused_by_game` entry, its Card setup and its docstring sentence were removed from `tests/test_frame_font_sites.py`.
- **README (N60).** The F9 line now says: press F10 at the Solitaire table and click "Win this Solitaire round" (under SOLITAIRE CHALLENGES). The build command had a backspace byte where the backslash should be (`.^Huild_release.ps1`). It now reads `.\build_release.ps1`. No other stale debug key, button or run step was found. README does not describe the code layout, and `python main.py` still works.
- **Multiplayer quarantine.** `test_local_animation_never_mutates_game_and_sound_edges_once` now uses a fake with every field that today's `Presentation.update` reads. It checks that each field is a real `ClientGame` field, so the fake cannot drift again. It checks one deal sound, then one chip, one check and one fold sound per edge (chip sounds are now `chips_1..3`, not `chip_move`), then one flip and one win sound at the end. It also checks that the game is never changed. Its KNOWN_FAILURES line and the empty "Multiplayer" header are gone. The three test_npc_development lines stay. In docs/TESTING.md, the bullet saying test_six_seat "may be a real bug" was stale: it was fixed as B67 and taken off the list. TESTING.md now says, in its own paragraph after the rules list, that only the three test_npc_development lines are left and that they wait for the designer. The KNOWN_FAILURES.txt header said fixing them was "on the future refactor sprint list (see AGENTS.md)". It now says "The three left wait for the designer (see docs/TESTING.md)."
- **B42 line reworded** in the Phase 7 fix report. B42 was Blind Man's Bluff losing the remainder of a refund (`//`) and counting split main/side pot wins as ties. The line now says that, says it was fixed with the shared `core.build_pots` (exact refunds), `award_pots` (B38 odd chips) and `core.hand_outcome` (a tie only when the human shared a pot and won none alone), and names the tests in `test_poker_pots` (`test_blind_mans_bluff_counts_wins_ties_and_losses_by_pot`, `test_a_layer_no_live_seat_paid_into_goes_back_exactly`). The old text (uncalled chips returned, not won) is kept as its own NEW-1 line.
- **§10.4 checklist** (all `git grep` on the commit):
  - `main.py` is the small entry point: 27 lines.
  - `solitaireplus/legacy.py`, `tools/refactor/`, `requirements-dev.txt`: all gone (`ls` finds none).
  - `git grep -nE '^\s*global\s' -- solitaireplus main.py`: no hits. `git grep -nE '\bglobals\s*\(' -- solitaireplus main.py`: no hits.
  - No duplicate engine modules in `multiplayer/`: no file name in `multiplayer/*.py` matches a file in `solitaireplus/`. A scan for any block of 12 identical non-blank, non-import lines shared by `multiplayer/*.py` and `solitaireplus/**/*.py` found 0.
  - `git grep -n __file__ -- solitaireplus main.py`: only `solitaireplus/app/paths.py:18`. In `multiplayer/` (tests excluded) there are two more `Path(__file__)` roots, and neither is an asset lookup. `multiplayer/multiplayer_paths.py:5` `ROOT` adds the repo to `sys.path`. `multiplayer/main.py:36` uses it for `os.chdir(ROOT)`, which is how relative paths in the Multiplayer window resolve, and `net_client.py:68` uses it as the cwd of the net service child. `multiplayer/relay_transport.py:19` `_ROOT` is only a `sys.path` entry. They are left as they are (see N80).
  - Deleted hotkeys: `git grep -nE 'K_F6|K_F7|K_F8|debug_xp_rect' -- solitaireplus main.py multiplayer ':!multiplayer/tests'`: no hits. `git grep -nE 'K_SPACE|K_b\b' -- 'solitaireplus/games/poker/holdem*.py'`: no hits. The remaining `K_SPACE` uses are normal game controls (Ace Invaders fire, arcade restart, Cryptid pack and battle, Dead Man's Hand jump, level-up dismiss).
  - Root files: `.github`, `.gitignore`, `CHANGELOG.md`, `PLAYING.txt` (copied into the build by build_release.ps1), `README.md`, `SolitairePlus.spec`, `build_release.ps1`, `main.py`, `requirements.txt`, `requirements-build.txt`, `version.py`, and the folders `assets`, `data`, `docs`, `installer`, `multiplayer`, `netservice`, `solitaireplus`, `tests`, `tools`, `updater`. No stray files.
  - Files over about 3,000 lines in `solitaireplus/`: none after the Hold'em split (above). The largest is `games/poker/five_card_draw_ui.py` (2,599).
  - The build, self-test, on-screen window and bug-table items are for the final Phase 12 run and the original session, not this group.
- Tests: full suite PASSED (game 145 files, 1237 tests, 3 quarantined; multiplayer 17 files, 141 tests, 0 quarantined). screen_harness compare against e7d8e80 IDENTICAL 64/64, then replay compare IDENTICAL 18/18.

### Loop variables (N24)
- N24 is fixed. Moving the old `main.py` globals to `app/state.py` had left 25 `for` loops in 13 modules writing
  their loop variable to state: `state.rect`, `state.index`, `state.package_index` or `state.free_game_id`. The
  finding listed 20; an AST scan found 5 more (`profile_editor.py` 678 and 737, `profile_select.py` 638 and 672,
  and a target split over several lines in `score_four_screen.py` 723). No comprehension or `with` target wrote to
  state.
- Each loop now uses a local name, such as `job_rect`, `bet_index`, `slot_rect` or `part_index`. Every read of the
  four names was inside its own loop body; no `getattr`, `vars(state)`, `game_namespace()` or harness Probe lookup
  and nothing in multiplayer reads them. The two module-level loops (`hub_screens.py`, `free_play_select.py`) leave
  `package_index` and `free_game_id` beside the loop names they already left, and nothing reads them.
- `app/state.py` had no defaults for these names; they left its "Set during start-up" list. Three tests stopped
  saving or patching `state.rect` and `state.index` (test_career_job_news, test_customize_no_debug_button,
  test_profile_save_failed_message).
- A reviewer found no problems. Full suite PASSED; scenes IDENTICAL 64/64 and journeys IDENTICAL 18/18.

### Journey 03_solitaire wins through the F10 button (N59)
- N59 is fixed. Journey `03_solitaire` (`tools/harness/journeys.py`) now wins the way a tester does: it presses F10
  on the Solitaire table, checks that "Win this Solitaire round" is enabled, and clicks it. It no longer calls
  `instant_solitaire_win()`, which stays only for the `solitaire_recap` scene (that scene pictures the animation and
  the recap, not how you get there).
- The journey has one new checkpoint, `debug_menu_from_table`, whose screenshot shows the button enabled.
  `recap_reward` and `after_recap` now come 12 frames later (620 and 650 instead of 608 and 638). Their values and
  screenshots are unchanged, because the button uses the same fixed round summary as the old F8 code.
- `replay compare` stays IDENTICAL: the harness runs the working tree's journey scripts against both checkouts. The
  old and new journey were compared with `replay.py run`; a second run and `replay.py selfcheck` matched exactly.

### Fitting Phase 12 onto Phase 11
- The two Phase 12 cleanup commits applied on top of Phase 11 with two small test conflicts
  (`tests/test_packaging.py` and `tests/test_multiplayer_launcher.py`). Phase 11's versions already run their
  child processes with a temporary `LOCALAPPDATA`, so they were kept.
- Four Phase 11 checks looked for `solitaireplus.legacy` to prove that the Multiplayer window does not start the
  single-player game. That module is gone, so the checks passed whatever happened. They now look for
  `solitaireplus.app.startup`, the module that starts the single-player game now:
  `multiplayer/tests/test_shared_ui_usage.py`, `multiplayer/tests/test_mp_window.py`, `tests/test_window.py` and
  `tools/window_check.py` (its printout now says "start-up/cursors").
- The B44 test (`test_frame_font_sites`) took two helpers from `legacy`; it now imports them from their new homes
  (`npc.manager.get_score_four_opponent_choices`, `npc.game_portraits.get_npc_portrait_surface`).
- The prep report expected the no-globals test to fail once Phase 11's merged modules arrived. It did not: the
  merge brought no `global` statement into `solitaireplus/`.
- `multiplayer/tests/test_menu_followup.py` imported `main` at module level, so `bootstrap()` wrote a game log into
  the real `%LOCALAPPDATA%` on every run and, with pruning, could delete the player's own old logs. It now points
  `LOCALAPPDATA` at a scratch folder before the import and cleans up afterwards, as `test_duel_launch.py` does.
- Checked: a full run of both suites with `LOCALAPPDATA` pointed at an empty folder now writes nothing there. The
  same check with the old `test_menu_followup.py` finds its `SimpleSolitaire\logs\game-<pid>.log`.

### Results
All on the final Phase 12 tree.
- Tests: `tools
un_tests.py` PASSED. game: 146 files, 1,246 tests; the 3 quarantined `test_npc_development` tests
  still fail, as listed. multiplayer: 18 files, 148 tests, none quarantined.
- Compares against "Phase 11 (fix): per-frame fonts in the Dead Man's Hand duel and the Multiplayer screens":
  `screen_harness compare` IDENTICAL 64/64 scenes, then `replay compare` IDENTICAL 18/18 journeys.
- Packaged (`build_release.ps1 -SkipTests -Installer`): `release\SolitairePlus-Setup-0.0.7.exe` and the zip were
  built, with a 1,794-file `manifest.json`. Self-tests: `SolitaireNet 1.1.0 ok; connectors: tcp, tls, ws, wss`, the
  updater exited 0, and the multiplayer report ends `PASSED: every multiplayer module imported`. `PYZ-00.toc` has
  all 22 `solitaireplus` modules the shipped `multiplayer/*.py` import and all 74 modules named in importlib or
  `lazy()` strings.
- 10 s packaged launches with a temporary `LOCALAPPDATA` and the update check off: `SolitairePlus.exe` and
  `SolitairePlus.exe --multiplayer` were still running, and each newest `game-*.log` was 0 bytes.
- Local two-player test (relay from source bound to 127.0.0.1:50111 and :50112; the packaged `SolitaireNet.exe`;
  every address checked to be 127.0.0.1 first): 72/72 OK. Hold'em (chips conserved, no hidden cards in 184 guest
  views, protocol stamp seen), Blind Man's Bluff (the guest never saw its own card) and Score Four (a wrong solve
  refused, a valid one won the round).
- Window checks on this PC (monitor 1920x1200, work area 1920x1152, 100% scaling): `window_check.py source` 41/41,
  `packaged` 11/11, `source --multiplayer` 110/110, `packaged --multiplayer` 84/84. Start-up (103, 87, 1817, 1082),
  client 1712x963, centred; F11 gives (0, 0, 1920, 1200); Options 1920x1080 and 2560x1440 greyed out.
- Checklist §10.4: `main.py` 27 lines; the largest file in `solitaireplus/` is `five_card_draw_ui.py` (2,599);
  `legacy.py`, `tools/refactor/` and `requirements-dev.txt` are gone; no `global` or `globals()`; no `multiplayer/`
  file shares a name with a game module; `__file__` only in `app/paths.py`; none of the deleted hotkeys; no
  `state.<name>` loop targets. `libcst` was uninstalled from the venv after this commit.

### New findings (not fixed)
- **N78:** on Windows, pruning cannot delete the log of a copy that is still running, because the file is
  open. On Linux or macOS it could: a long-running copy's log could be removed once 9 newer starts have happened.
  The game ships for Windows only, so this only matters if a non-Windows build appears.
- **N79:** `tests/updater/test_updater.py` (ApplyTests) failed now and then on this PC: 1 of 2 full runs and
  1 of 7 solo runs, a different test each time, with `OSError` or `PermissionError` while applying an update in a
  temporary folder. It does not touch game code. It looks like another program (for example a virus scanner)
  briefly holding a new file. Not quarantined (that would hide it).
- **N80:** `multiplayer/multiplayer_paths.py:5` and `multiplayer/relay_transport.py:19` find the repo root
  with `Path(__file__)`. They are not asset lookups: one sets `sys.path` and the working folder
  (`multiplayer/main.py`, `net_client.py`), the other only sets `sys.path`. The original session may still want them
  on `solitaireplus.app.paths` when it checks §10.4.
- **N81:** `updater/__init__.py:12` says "See docs/RELEASING.md and AGENTS.md". AGENTS.md is not in the repo
  yet. It is a user doc the original session writes, so the line was left alone.
- N63 (unchanged): `Game.debug_auto_solve_state` still has no caller. It moved verbatim to
  `games/solitaire/auto_solve.py`. It is not on the §5.1 list, so it was kept.
