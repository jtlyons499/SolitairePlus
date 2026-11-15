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
- **B42:** uncalled chips are returned, not won, in every variant, including fold wins ("Uncalled $980 returned to
  you." then "You win $50."). Stacks end the same as before; the win, fans and Hold'em pot achievements count only
  chips that were won. The Hold'em $1,000 and $25,000 pot achievements now look at the largest single pot.
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
  seat). Phase 11 moves them onto `core.py`; the steps are in `tools/refactor/specs/phase11_plan.md`.
- **N37:** `strategy.LATE_STREETS` changed value (single-round stages count as final rounds); multiplayer imports
  `strategy` through a shim and gets the new value. Phase 11 confirms the room NPCs.

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
