# Solitaire+ restructure and bug-fix brief

**Audience:** a new Claude Code session with no memory of earlier work. Read this whole file before doing anything.
Then follow **§0 First actions**.

**Written:** 2026-11-15, on branch `feature/installer-updater-netcode`, at commit `154b890`. File/line references are
from that commit. If code has moved by a few lines, find it by the function name or quoted snippet given; never by
line number alone.

**Top priority complaint from the designer:** windowing and resolution (W1, Phase 2). The game often opens
cut off or looking fullscreen, and returning to window mode can hide the title bar.

**Who you are working for:** the user (Dan). Dan coordinates with the game's original designer, who is not a
programmer and uses ChatGPT for code. When a rule or balance question comes up, Dan relays it to the designer.

---

## Contents

0. First actions
1. What Solitaire+ is
2. What already exists (Steps 1–6) and must not be undone
3. Environment and tools
4. Working rules
5. Current architecture map
6. Target layout and mechanics
7. Phases 0–12, step by step
8. Bug list (W1, B1–B86, D1)
9. Designer decisions
10. Verification, hand-back, and the return checklist
11. Pitfalls already learned the hard way

---

## 0. First actions

1. `git status` must be clean on `feature/installer-updater-netcode`. Don't create a new branch; this work continues
   on this one. Don't push unless Dan asks.
2. Make sure the Python environment works:
   `.venv\Scripts\python.exe -c "import pygame, websockets; print('ok')"`.
   If `.venv` is missing: `py -3.12 -m venv .venv`, then
   `.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-build.txt`.
3. Run the full test suite once: `.venv\Scripts\python.exe tools\run_tests.py`. It must print
   `PASSED - all non-quarantined tests passed.` Note the quarantined tests it reports; that list is the starting
   point.
4. Read §4 (working rules), then start **Phase 0**. Stop and report to Dan at the end of every phase (§4.2).

---

## 1. What Solitaire+ is

- A single-player Windows card game written in Python with pygame-ce (about 112,000 lines). It has:
  - Klondike Solitaire with challenges and Head-to-Head races;
  - a Career mode (calendar, jobs, homes, NPC leaderboards, news, event nights);
  - poker variants (Texas Hold'em, Five-Card Draw, Seven-Card Stud, Five-O, Blind Man's Bluff);
  - casino games (Blackjack, Roulette, Horse Races, Faro);
  - casual card games (Crazy Eights, Bango, Score Four);
  - four arcade machines (King Pong, Battle Bosses, Ace Invaders, Suit Snake);
  - a creature card battler (Cryptid Creatures) and a Doom-like shooter (Dead Man's Hand);
  - progression, customization and achievements.
- **Multiplayer** is a separate window (the same exe run with `--multiplayer`). It plays through a relay server
  hosted on Railway.
- The game draws to a fixed 1366×768 surface (`game_surface`), which is scaled to the window.

---

## 2. What already exists (Steps 1–6) and must not be undone

All of this is on this branch, committed, with tests. Keep it working through every phase.

| Area | What it is | Key files |
|---|---|---|
| Version | Single source `version.py` (SemVer). Shipped as a loose file so a version bump doesn't change the game exe. | `version.py`, `tools/write_version_info.py`, `tools/release_helpers.py` |
| Release flow | `tools/release.ps1` (local: tests, then bump, then tag), CI workflow (test, build, sign, publish) | `.github/workflows/release-windows.yml` |
| Tests | One runner for both suites, a process per file, headless pygame, quarantine list | `tools/run_tests.py`, `tests/KNOWN_FAILURES.txt`, `docs/TESTING.md` |
| Netcode | All sockets live in `SolitaireNet.exe` (`netservice/`). The game talks to it over stdin/stdout. Connectors: tcp, tls, ws, wss. | `netservice/**`, `multiplayer/net_client.py`, `docs/NETWORKING.md` |
| Packaging | One PyInstaller spec builds `SolitairePlus.exe`, `SolitaireNet.exe` and `SolitaireUpdater.exe` into one folder with `SolitairePlus_Data\`. Packaged self-tests. | `SolitairePlus.spec`, `build_release.ps1`, `multiplayer_launcher.py` (`--selftest`) |
| Manifest | `manifest.json` (SHA-256 of every file), delta zips, and reuse of unchanged exes between releases | `tools/make_manifest.py` |
| Updater | In-game check, main-menu banner, Options → Updates, signed-manifest and Authenticode checks, two-warning override, transactional apply with rollback, files renamed aside when in use | `updater/**`, `update_check.py`, `app_settings.py` |
| Installer | Inno Setup per-user install, optional publisher-certificate trust, uninstall keeps saves | `installer/SolitairePlus.iss`, `tools/sign_release.ps1` |
| Saves | `%LOCALAPPDATA%\SimpleSolitaire\saves` (single-player) and `%LOCALAPPDATA%\SolitaireMultiplayer` (multiplayer). `.bak` of the last good save, damaged-save fallback, newer-version guard, migration chain. | `profile.py` |
| Relay | Room codes (6 characters for new clients), guessing protection, optional WebSocket listener, probe tool, Railway guide | `multiplayer/relay_server.py`, `room_relay.py`, `relay_websocket.py`, `tools/relay_probe.py`, `docs/RAILWAY_DEPLOY.md` |

**Must not be undone:**
- **Updater self-copy.** Never make the updater (or any exe) copy itself to `%TEMP%` and run the copy. Microsoft
  Defender flagged that as `Trojan:Win32/Bearfoos.A!ml`. A test guards it
  (`tests/test_updater.py::test_updater_never_runs_a_copy_of_itself_from_temp`).
- **Names that stay fixed:**
  - exe names: `SolitairePlus.exe`, `SolitaireNet.exe`, `SolitaireUpdater.exe`;
  - the data folder: `SolitairePlus_Data`;
  - the save folder names;
  - the installer's `AppId`.
- **`version.py` stays at the repository root,** and `main.py` stays at the root as the entry point. Release tooling,
  the spec, the updater and CI all read `ROOT/version.py`.
- **The F10 debug menu stays in public builds** (designer decision). Only the stray hotkeys and buttons outside it are
  removed (D1).
- **No game code may open sockets or do HTTP.** Networking lives in `netservice/`, updates in `updater/`.
- **Never modify the Windows certificate trust store, and never bind non-loopback ports.** Tests use `127.0.0.1`.
- **Don't run `tools/relay_probe.py` against the live Railway relay.** That's for the designer.

---

## 3. Environment and tools

- **OS:** Windows 11. The **Bash** tool is Git Bash; a **PowerShell** tool is also available.
- **Python:** `.venv` uses **3.12** locally; CI uses **3.14**. Write code that works on both.
- **Dependencies:**
  - Runtime: `requirements.txt` (pygame-ce 2.5.8, websockets 15.0.1).
  - Build: `requirements-build.txt` (pyinstaller 6.22.3).
  - For this work, add `requirements-dev.txt` with `libcst` pinned to a version at least two weeks old, used only by
    the refactoring tool. Delete the file in Phase 12, together with the tool.
- **Tests:**
  - `.venv\Scripts\python.exe tools\run_tests.py` runs everything.
  - Add `--suite game` or `--suite multiplayer` to run one suite.
  - Debug a single test or file with `--worker game test_x` or
    `--worker multiplayer test_x.Class.test_y`.
  - The runner sets `SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy` and `SOLITAIRE_NET_INPROCESS=1`, and starts
    pygame headless.
  - **Quarantine rules** (`tests/KNOWN_FAILURES.txt`, explained in `docs/TESTING.md`):
    - Only tests that were already broken are listed.
    - A reason starting `HANGS` means the test runs alone with a time limit.
    - A reason starting `FLAKY` means one pass proves nothing.
    - **Never add a test to hide a failure you caused.**
- **Build:**
  - `powershell -NoProfile -ExecutionPolicy Bypass -File build_release.ps1 -SkipTests` (about 5 minutes) builds
    `dist\SolitairePlus\` and runs the packaged self-tests.
  - Add `-Installer` to also build the installer. Inno Setup 6 is at
    `%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe`.
- **Packaged self-tests:** `SolitaireNet.exe --selftest`, `SolitaireUpdater.exe --selftest`, and
  `SolitairePlus.exe --multiplayer --selftest --selftest-report FILE`. The last imports every shipped multiplayer
  module inside the real build.
- **Headless rendering:**
  - Set `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy`. Then execute `main.py`'s source up to the marker
    `running = True\n\n\nwhile running:`, call draw functions and `pygame.image.save(game_surface, ...)`.
  - Read the PNG with your file-read tool to look at it.
  - This is how the profile, options and main-menu screens were checked before. Example scripts are described in §7,
    Phase 0.
- **Long commands** (builds, the full test suite) can run in the background. Don't poll; wait for the notification.

---

## 4. Working rules

### 4.1 Commits
- Each area gets **two commits**:
  1. **"Move"**: code relocated, **no behaviour change**. It must pass the Phase-0 safety net exactly:
     pixel-identical screenshots and identical replay checkpoints.
  2. **"Fix"**: that area's bugs from §8. Each fix comes with a regression test that fails before the fix and passes
     after. Screenshots or replays may change **only** where a fix intends it; list every changed screenshot in the
     commit message.
- Phases 0, 1 and 12 are single commits (there are no bugs to fix in them).
- Commit messages:
  - The first line is `Phase N (move|fix): <area>`.
  - The body is a plain list of what moved or what was fixed (bug IDs).
  - End with the attribution trailer your environment specifies.
- Never commit generated output: `dist/`, `build/`, `release/`, baselines, `.venv`.

### 4.2 Stop after every phase
At the end of each phase, report to Dan:
- what moved or what was fixed;
- the test results (`PASSED` line, plus any quarantine changes);
- the safety-net result (screens compared, any intended changes);
- anything surprising.

Then wait for Dan's go-ahead before the next phase.

The one extra stop is **B86**: show the poker rules audit table before its fix commit (§8, Phase 7).

### 4.3 Names stay stable while moving
- Keep every function name and every `STATE_*` value **unchanged** through the move commits. The safety net and the
  test locator find code by name.
- Renames, if any, only happen in Phase 12, and only when they clearly help.

### 4.4 Scope discipline
- Fix only the listed bugs. If you find a new bug, add it to a "New findings" list in your phase report; don't fix it
  silently.
- If something is ambiguous (a rule or balance question), ask Dan instead of guessing.
- Keep each commit reviewable. A move commit is mostly file moves and import rewrites.

---

## 5. Current architecture map (commit 154b890)

### 5.1 `main.py` at a glance
- **32,041 lines.** 322 top-level functions, no classes, one loop: `while running:` (lines 24167–32037).
- **60 screens,** named by `STATE_*` constants at lines 877–985 (plus `STATE_CAREER_LEADERBOARD_BIO` at 1683). Each
  value equals the lowercase name.
- **State sharing:**
  - 544 `global` statements across 135 functions (201 distinct globals);
  - about 645 module-level assignment targets (143 of them UPPERCASE constants);
  - **47 calls that pass `globals()`** to other modules, which read and write `main.py`'s namespace by name:
    - `track_night_cash` and `night_cash_total`;
    - `store_event_progress` and `restore_event_progress` (10578, 25246, 28708);
    - `draw_score_four_table(…, globals())` (12036, 12280);
    - `debug_unlocks.debug_unlock_everything(globals())` (24567);
    - `globals().get(...)` reads.
- **Problems in the file itself** (fix in Phase 12, except B45 in Phase 7):
  - `play_texas_holdem_npc_action_sound`, `play_texas_holdem_new_hand_sound` and `play_texas_holdem_street_sound` are
    each defined twice (6973/7056, 7024/7101, 7031/7108).
  - `STATE_CAREER_NEWS` is assigned twice (979 and 980).
  - `blackjack_dealer_npc`, `play_background_image`, `profile_switch_rect` and `career_{back,jobs,leaderboards,news,
    play,real_estate}_rect` are each assigned twice.
  - `STATE_WIN` is never used.
  - Probably-dead functions: `get_unlocked_games_for_event`@2347, `get_career_weekday_name`@2433,
    `get_npc_icon_surface`@8225, `get_selected_suit_snake_difficulty`@8762, `get_free_play_return_state`@10186 and
    `draw_score_four_npc_panel`@11802.

### 5.2 Main loop phases
1. **Before the loop (24156–24165):** `apply_saved_app_settings()`, optionally `update_checker.start()`, then
   `running = True`.
2. **Per-frame settings and audio (24169–24190):**
   - `update_checker.poll()`;
   - Options settings: `app_settings.update(current_app_settings_values())` while on Options, otherwise `tick()`;
   - `audio.sync_machine_music(...)`, then `audio.update()`.
3. **Events (`for event in pygame.event.get()`, from 24196):**
   1. `QUIT`, then `audio.handle_event`.
   2. F11 fullscreen (24207, `continue`), then F10 debug toggle (24223–24253, `continue`).
   3. Mouse mapping at 24255–24268: `game_mouse_pos = None`; if the event has `.pos`, it becomes
      `window_to_game_coords(event.pos)`, and `menu_mouse_pos` is copied from it.
   4. The debug branches (DEBUG_POKER_NPC_SELECT 24274–24314, DEBUG_MENU 24320–24594, both `continue`).
   5. The **main `if/elif current_state` event chain, 24600–30487 (57 branches).**
4. **Post-event per-state updates (30487–30680):** Head-to-Head, solitaire round completion and rewards, the
   horse-music guard (30660), and the level-up queue.
5. **Drawing, in two separate chains:**
   - **Chain A (30686–31212):** most screens.
   - **Chain B (31218–31952):** Hold'em, Stud and Draw **timed NPC actions** (31218–31875, imports
     `holdem_turn_flow` every frame), then draws for DEBUG_POKER_NPC_SELECT, DEBUG_MENU, LEVEL_UP and PLAYING.
   - Then the achievement popup (31954–31965).
6. **Present (31967–32037):** scale `game_surface` into the window (`scaled_surface_cache`), the software cursor
   fallback, `pygame.display.flip()`, `clock.tick(FPS)` (FPS = 60, line 3425). After the loop:
   `app_settings.flush(); pygame.quit()`.
- **Scaling helpers:** `window_to_game_coords`@12367, `invalidate_scaled_surface_cache`@12288,
  `set_window_size`@12293, `set_fullscreen_enabled`@12322.
- **Mouse position:** `game_mouse_pos` has no module-level initialiser and is read 322 times. `menu_mouse_pos` starts
  at 22887.

### 5.3 Per-screen map (EV = event-chain lines, DR = draw-chain lines)

| Area | State | EV | DR | Main functions (line) |
|---|---|---|---|---|
| Debug | DEBUG_POKER_NPC_SELECT | 24274–24314 | 31878–31894 | `open_debug_poker_npc_select`@9993, `start_debug_selected_poker_table`@10020 |
| Debug | DEBUG_MENU | 24320–24594 | 31896–31914 | `debug_open_*` (8505–10036), `debug_prepare_arcade_night`@8559, `debug_prepare_poker_night`@9959, `debug_setup_holdem_heads_up`@7119, `adjust_debug_ratings`@6490, `debug_set_player_level`@10070, `debug_start_next_career_month`@10309, `debug_add_career_prospect`@10350, `debug_advance_career_year`@10369 |
| Menus | SPLASH | 24600–24617 | 30686 | `draw_splash_screen` 22029–22193; assets 4007–4070 |
| Menus | MENU | 24811–24916 | 30699 | `draw_main_menu` 22276–22385, `draw_drifting_menu_background`@22194, `draw_update_banner`@5685, `start_game_update`@5633; rects 4542–4555 |
| Menus | MODE_SELECT | 24922–25012 | 30722 | `draw_mode_select` 14275–14388 |
| Menus | FREE_PLAY_SELECT | 25035–25053 | 30738 | `draw_free_play_select` 14207–14274; `begin_free_play_sandbox`@10097, `finish_free_play_sandbox`@10130, `leave_free_play_game`@10190, `start_free_play_game`@10199, `is_game_unlocked`@10383 |
| Menus | DIFFICULTY | 29214–29297 | 30826 | `draw_difficulty_screen` 21843–22025 |
| Menus | HOW_TO_PLAY | 28062–28123 | 30718 | `draw_how_to_play` 14497–14832, `draw_solitaire_help_diagram` 12039–12276; data `HOW_TO_PLAY_CONTENT`@987, `HELP_*` 1122–1682 |
| Menus | ACHIEVEMENTS | 28046–28060 | 30703–30716 | `achievements_ui.draw_achievements_screen`; `award_game_xp`, `process_achievement_event`@6714, popups 6706/6781 |
| Menus | OPTIONS | 29299–29620 | 30831 | `draw_options_menu` 22388–22886; rects 5445–5617; `handle_update_button`@5647, `current_app_settings_values`@5656, `apply_saved_app_settings`@5667, `draw_update_options_panel`@5694 |
| Menus | CUSTOMIZE | 29626–29807 | 30836 | `draw_customize_menu` 22896–23322; helpers 12389–12596; cursors 4167–4390 |
| Profile | PROFILE_SELECT | 24623–24805 | 30690–30695 | `draw_profile_select_screen` 21267–21533, `draw_delete_profile_confirmation`@21635, `get_profile_slot_display_data`@10430, `finish_profile_selection`@2979 |
| Profile | PROFILE | 29911–30214 | 30840 | `draw_profile_screen` 23323–23723; `apply_fresh_profile`@10493, `build_profile_save_data`@10576, `apply_profile_save_data`@10893 (533 lines, 61 globals) |
| Solitaire | PLAYING | 30220–30487 | 31921–31952 | `game.*` (game.py), `draw_gameplay_ui` 20900–21266, pause/return dialogs 21534/21740; round completion 30526–30658 |
| Solitaire | RECAP | 29813–29875 | 30844 | `draw_round_recap` 23729–23989 |
| Solitaire | LEVEL_UP | 29882–29904 | 31916 | `draw_level_up_screen` 23994–24155; XP helpers 12876–13253 (`add_player_xp`@13032, `apply_round_rewards`@13107) |
| Solitaire | Head-to-Head (uses PLAYING) | — | — | 18591–18812 (`start_head_to_head_event`, `finish_head_to_head_race`@18683) |
| Career | CAREER_HUB | 25069–25358 | 30749 | `draw_career_hub` 14833–16502 (1,669 lines); career helpers 2071–3421 (`auto_save_career`@2575, called from 32 functions; `advance_career_day`@2594) |
| Career | CAREER_ACTIVITY | 25059–25067 | 30743–30747 | `career_activity_screen` (`career_activities_ui.py`) |
| Career | CAREER_JOBS | 28129–28217 | 30755 | `draw_career_jobs` 16564–16927 |
| Career | CAREER_REAL_ESTATE | 29100–29208 | 30761 | `draw_career_real_estate` 16928–17375 |
| Career | CAREER_LEADERBOARDS | 28241–28384 | 30767 | `draw_career_leaderboards` 17540–18111; engine 13254–13608 |
| Career | CAREER_LEADERBOARD_BIO | 28219–28239 | 30771 | `draw_career_leaderboard_bio` 17376–17539 |
| Career | CAREER_NEWS | 28387–28445 | 30779 | `draw_career_news` 18112–18451 |
| Career | CAREER_EVENT_SELECT | 28588–28719 | 30785 | `_draw_career_event_select` 19620–19815, `draw_arcade_night_select` 19400–19619 |
| Career | CAREER_EVENT | 28447–28540 | 30817 | `draw_career_event` 18945–19127; press 18452–18534; autographs 18535–18590/18813–18944 |
| Career | CAREER_EVENT_SUMMARY | 28546–28586 | 30821 | `draw_career_event_summary` 13719–13875; `_build_career_event_summary` 2071–2293 |
| Career | CASE_OPENING | 25018–25027 | 30729 | `case_screen` (`case_opening_ui.py`) |
| Cryptid | CRYPTID_CREATURES | 25029–25033 | 30733 | `cryptid_screen` |
| Cards | CRAZY_EIGHTS | 27757–27803 | 30848 | `start_crazy_eights_session`@9183, `claim_crazy_eights_result`@9194 |
| Cards | BANGO | 27805–27835 | 30861 | 9221–9261 |
| Cards | SCORE_FOUR(_MODE/OPPONENT_SELECT) | 25360–25459, 25466–25539, 27837–28044 | 30872/30882/30876 | `draw_score_four_opponent_select` 11611–11801, `draw_score_four`@12033, `settle_score_four_session_result`@12003 |
| Poker | TEXAS_HOLDEM(_BUY_IN) | 26112–26168, 26174–26689 | 31161, 31176–31212 (+ timed NPC 31218–31457) | helpers 6801–7432 (`process_texas_holdem_showdown`@6833, `start_texas_holdem_session`@7249, `finish_texas_holdem_session`@7377) |
| Poker | FIVE_CARD_DRAW(_BUY_IN) | 25783–25828, 25834–26106 | 31108, 31123–31159 (+ timed NPC 31663–31875) | 7433–7811 |
| Poker | SEVEN_CARD_STUD(_BUY_IN) | 25546–25587, 25593–25777 | 31057, 31071–31106 (+ timed NPC 31461–31660) | 7812–8175 |
| Poker | FIVE_O_POKER | 27661–27711 | 31019 | 9688–9818 |
| Poker | BLIND_MANS_BLUFF | 27713–27755 | 31036 | 9819–9941 |
| Casino | BLACKJACK_BET / BLACKJACK | 26693–26830, 26832–27018 | 31052, 30887 | draw 5742–6459; `settle_blackjack_round`@8384 |
| Casino | ROULETTE | 27024–27516 | 30895 | `settle_roulette_round`@8328, `try_place_or_remove_roulette_bet`@8176 |
| Casino | HORSE_RACES | 27518–27593 | 30917 | `settle_horse_race_result`@8467, music 9475/9513, sessions 9531/9543 |
| Casino | FARO | 27595–27659 | 31002 | 9598–9687 |
| Arcade | TOKEN_EXCHANGE / PRIZE_COUNTER / TROPHY_ROOM | 28883–28937 / 28939–28969 / 28971–28976 | 30805/30809/30813 | 19856–20158 |
| Arcade | *_OPPONENT_SELECT / *_DIFFICULTY_SELECT (4) | 28721–28881 | 30789–30801 | 20159–20882 |
| Arcade | KING_PONG / BATTLE_BOSSES / ACE_INVADERS / SUIT_SNAKE | 28978–29065 | 30934–30975 | sessions 8559–9182 |
| DMH | DEAD_MANS_HAND | 29067–29098 | 30977–31000 | `start_dead_mans_hand`@8603, `exit_dead_mans_hand`@8614 |

### 5.4 Shared things almost every screen uses
- **Drawing helpers:** `draw_button`@14008, `draw_menu_button`@14067, `draw_submenu_background`@14459,
  `draw_submenu_title`@14389, `render_text_fit`@14161, `draw_wrapped_text(_limited)`@11536/11427.
- **Fonts, created at import (4403–4540):** `difficulty_detail_font`, `option_label_font`, `option_value_font`,
  `options_title_font`, `ui_small_font` and `menu_title_font`. They are passed into many `*_ui` modules.
- **Audio:** `audio = AudioManager()`@560. Sounds are played by name, `audio.play_sound("button_click")`, from
  everywhere. SFX are loaded at 671–849.
- **Cards:** `game.card_fronts`, `game.get_card_back_surface()` and `game.felt_surface` (from `game.py`) are used by
  every card game.
- **Career and economy:**
  - Saving: `auto_save_career`@2575.
  - Ratings and fans: 6460–6700 (`award_career_rating`, `rate_competitive_game`, `rate_house_game`,
    `rate_poker_cash_out`, `award_fans_for_*`).
  - Night tracking: `record_career_event_result`.

### 5.5 Root files (114) and which area they belong to

| Area | Files |
|---|---|
| App / core | runtime_support, version (stays at root), app_settings, update_check, multiplayer_launcher, audio, settings, cosmetic_assets, help_history |
| Solitaire | game, card, deck, solitaire_assist, solitaire_race_deals, solitaire_restart, head_to_head, head_to_head_ui |
| Poker | texas_holdem, texas_holdem_ui, five_card_draw(_ui), seven_card_stud(_ui), five_o_poker(_ui), blind_mans_bluff(_ui), bluff_presentation, niche_poker_common, poker_ai, poker_recap, poker_quick_chat, poker_quick_chat_adapter, poker_variant_quick_chat, holdem_turn_flow; shims to `shared/`: poker_core, poker_strategy, poker_speech, poker_ui_assets, poker_learning, texas_holdem_chat |
| Casino | blackjack, blackjack_presentation, roulette, roulette_ui, horse_races, horse_races_ui, faro, faro_ui |
| Casual cards | crazy_eights(_ui), bango(_ui), score_four, score_four_ui, score_four_difficulty |
| Arcade | arcade_support, king_pong, battle_bosses, battle_bosses_game, ace_invaders, ace_invaders_game, suit_snake, suit_snake_game |
| Cryptid | cryptid_creatures, cryptid_creatures_ai, cryptid_creatures_ui, cryptid_cards, cryptid_collection, cryptid_collection_ui, cryptid_battle_feedback, cryptid_encounter_view |
| Dead Man's Hand | dead_mans_hand, dead_mans_hand_game, dead_mans_hand_weapons, dead_mans_hand_pvp (stale; the live copy is in `multiplayer/`) |
| Career | career_activities, career_activities_ui, alien_night, career_asset_images, career_event_progress, career_fans, career_hub_controls, career_news, career_npc_development, career_npc_world, career_rating_events, career_ratings, career_session_summary, career_time_warp, career_world_flavor, press_interview, autograph_event, case_opening, case_opening_ui |
| NPC | npc_manager, npc_avatars, npc_portraits, npc_portrait_ui, npc_personality_ui; shims npc_personality, npc_personality_chat |
| Profile / progression | profile, profile_avatar_assets, achievements, achievements_ui, reward_cosmetics, rating_unlocks |
| Debug | debug_menu, debug_poker_select, debug_unlocks |
| Misplaced | `verify_solitaire_state.py` (move to `tools/`), `test_dead_mans_hand_weapon_system.py` (merge into `tests/`; a different file with the same name already exists there) |

`shared/` holds the real code behind the eight root shims (poker_core, poker_strategy, poker_speech, poker_ui_assets,
poker_learning, npc_personality, npc_personality_chat, texas_holdem_chat).

### 5.6 Multiplayer facts
- **Run path:**
  - `multiplayer_launcher.run_multiplayer()` puts `multiplayer/` first on `sys.path`, `chdir`s to ROOT, and runs
    `multiplayer/main.py` with `runpy`.
  - In the packaged game, `multiplayer/*.py` ship as **loose source files** in `SolitairePlus_Data\multiplayer\`.
    They import other modules from the game exe's bundled code, so any standard-library or game module they need
    must be imported by the game. The packaged self-test checks this.
- **17 duplicated module names** in `multiplayer/`: texas_holdem, texas_holdem_ui, poker_ai, audio, npc_portraits,
  poker_recap, npc_avatars, dead_mans_hand_pvp, plus shims for poker_core, poker_strategy, poker_speech,
  poker_ui_assets, poker_learning, npc_personality, npc_personality_chat and texas_holdem_chat. The multiplayer copy
  wins on `sys.path`.
- **Real differences between copies:**
  - `texas_holdem.py`, 25 lines differ:
    - multiplayer adds `allow_network_spectator`, `get_live_player_indexes` and busted-seat dealing;
    - root has the short-big-blind fix, the raise guard and the quick-chat reset.
  - `poker_ai.py`: multiplayer lacks quick-chat aggression and bluff deltas, and the short-stack tenacity cap.
  - `texas_holdem_ui.py`: about 358 lines differ (multiplayer has `show_utility_buttons`).
  - `audio.py`: multiplayer has a trimmed copy.
  - `dead_mans_hand_pvp.py`: the multiplayer copy is newer (mouse capture, leave toast, 5-character code).
- **Root modules imported by `multiplayer/`** (must keep working after Phase 1):
  - dead_mans_hand, dead_mans_hand_game, dead_mans_hand_weapons;
  - niche_poker_common, roulette;
  - score_four, score_four_ui, score_four_difficulty;
  - runtime_support, achievements, npc_avatars, profile_avatar_assets, settings.
- **Server-only and test-only modules** not shipped to players: `relay_server.py`, `room_relay.py`,
  `relay_websocket.py`, `relay_transport.py`. These are listed in `MP_EXCLUDED` in the spec **and** `SELFTEST_SKIP`
  in `multiplayer_launcher.py`, and a test keeps the two lists in sync.

### 5.7 Tests and tools tied to the current layout
- **22 test files read `main.py` source.** Most use `ast.parse(Path('main.py').read_text())`, pick top-level
  `FunctionDef`s by name, and `exec` them in a fake environment:
  - `test_career_polish` (`production_function`): `_build_career_event_summary`, `build_career_event_summary`,
    `finish_*_session`, `grant_rating_cosmetics`.
  - `test_career_ratings` (`main_functions`): `award_career_rating`, `rate_*`, `settle_blackjack_round`,
    `settle_roulette_round`, `finish_head_to_head_race`, `finish_*_session`.
  - `test_npc_development`: `apply/build_profile_save_data`, `sync_career_npc_runtime_state`,
    `update_career_leaderboard_ratings`, debug career functions.
  - `test_cryptid_collection`: `add_player_xp`, `get_level_from_xp`, `get_next_level_xp`,
    `start/leave/settle_career_cryptid`, `auto_save_career`, `draw_level_up_screen`.
  - `test_cryptid_creatures` (297): the free-play sandbox functions.
  - `test_career_activities` (86), `test_case_opening` (54), `test_rewards_overhaul` (109),
    `test_customization_finish` (41), `test_leaderboard_decimal_display` (8), `test_npc_avatars` (252),
    `test_npc_portrait_ui` (38).
  - `test_poker_recap` (65, 96): also walks the loop for the `recap_open` branch.
  - `test_readability_polish` (39), `test_rival_learning` (109).
- **Source-string checks:** `test_arcade_support` (16 reads, about 66 assertions such as
  `"suit_snake_quit_rect = pygame.Rect(1155, 660, 190, 50)"`), `test_arcade_audio`, `test_dead_mans_hand_integration`,
  `test_dead_mans_hand_weapon_system` (both copies), `test_debug_menu_arcade`, `test_career_night_warp` (42).
- **Tools and files to update when files move:**
  - `SolitairePlus.spec`: `Analysis(['main.py'])` stays, but update `MP_EXCLUDED` and datas.
  - `tools/make_manifest.py`: `COMPONENT_INPUTS["game"]` is root `*.py` + `shared/**/*.py`; it must become
    `solitaireplus/**/*.py` + `main.py`, still excluding `version.py`.
  - `tools/release_preflight.py` and `tools/build_race_pool.py` import `settings` and `solitaire_race_deals`.
  - `verify_solitaire_state.py` reads `main.py`.
  - `multiplayer_launcher.py` uses `ROOT = Path(__file__).resolve().parent` to find `multiplayer/`.
  - Seventeen root modules build paths from their own location (`Path(__file__)`): `alien_night`,
    `career_activities`, `autograph_event`, `case_opening`, `case_opening_ui`, `horse_races`, `npc_manager`,
    `npc_portraits`, `profile_avatar_assets`, `score_four_difficulty`, `solitaire_race_deals`, `cryptid_creatures`
    (reused by `cryptid_cards` and `cryptid_battle_feedback`), `career_asset_images`, and others. Moving them breaks
    asset lookup unless they use `paths.py`.
  - About 220 asset paths are relative to the working folder (`"assets/..."`). They work only because
    `runtime_support.bootstrap()` `chdir`s to ROOT.
  - **Stdlib name clash:** `profile.py` has the same name as Python's standard-library `profile` module. Renaming it
    (to `saves.py`) removes the clash.

---

## 6. Target layout and mechanics

### 6.1 Layout (create in Phase 1, fill in Phases 2–11)

```text
main.py                   ~40 lines (Phase 2+): bootstrap, --multiplayer, update recovery, then app.run()
version.py                stays at the root (release tooling reads it)
solitaireplus/
  __init__.py
  app/        loop.py, state.py, window.py, assets.py, fonts.py, sounds.py, audio.py, paths.py, app_settings.py,
              update_check.py, runtime_support.py, settings.py, multiplayer_launcher.py, cosmetic_assets.py
  ui/         buttons.py, text.py, panels.py, backgrounds.py, cursors.py, popups.py
  menus/      splash.py, main_menu.py, mode_select.py, free_play_select.py, difficulty.py, options.py,
              customize.py, help.py, help_content.py, achievements_screen.py
  profile/    profile_select.py, profile_editor.py, saves.py (was profile.py), avatar.py, progression.py,
              recap.py, level_up.py, achievements.py, cosmetics.py (reward_cosmetics), unlocks.py (rating_unlocks)
  career/     hub.py, calendar.py, jobs.py, real_estate.py, leaderboards.py, leaderboard_bio.py, news.py,
              activities.py, ratings.py, rating_events.py, fans.py, npc_world.py, npc_development.py, time_warp.py,
              world_flavor.py, case_opening.py, case_opening_screen.py, session_summary.py, event_progress.py,
              hub_controls.py, asset_images.py, alien_night.py,
              events/ event_select.py, event_screen.py, summary.py, press_interview.py, autographs.py, night.py
  npc/        manager.py, personality.py, personality_chat.py, portraits.py, portrait_ui.py, avatars.py,
              personality_ui.py
  games/
    solitaire/       rules.py (was game.py), card.py, deck.py, assist.py, race_deals.py, restart.py, screen.py,
                     head_to_head.py, head_to_head_ui.py, head_to_head_screen.py
    poker/           core.py, strategy.py, ai.py, learning.py, speech.py, ui_assets.py, quick_chat.py,
                     quick_chat_adapter.py, variant_quick_chat.py, recap.py, turn_flow.py, niche_common.py,
                     holdem.py, holdem_ui.py, holdem_screen.py, holdem_chat.py,
                     five_card_draw.py, five_card_draw_ui.py, five_card_draw_screen.py,
                     seven_card_stud.py, seven_card_stud_ui.py, seven_card_stud_screen.py,
                     five_o.py, five_o_ui.py, five_o_screen.py,
                     blind_mans_bluff.py, blind_mans_bluff_ui.py, bluff_presentation.py, blind_mans_bluff_screen.py
    casino/          blackjack.py, blackjack_presentation.py, blackjack_screen.py, roulette.py, roulette_ui.py,
                     roulette_screen.py, horse_races.py, horse_races_ui.py, horse_races_screen.py, faro.py,
                     faro_ui.py, faro_screen.py
    cards/           crazy_eights(.py,_ui.py,_screen.py), bango(...), score_four(.py,_ui.py,_difficulty.py,_screen.py)
    arcade/          support.py (was arcade_support), hub_screens.py, machine_select.py, king_pong.py,
                     king_pong_screen.py, battle_bosses.py, battle_bosses_game.py, ace_invaders.py,
                     ace_invaders_game.py, suit_snake.py, suit_snake_game.py, machine_screens.py
    cryptid/         creatures.py, ai.py, ui.py, cards.py, collection.py, collection_ui.py, battle_feedback.py,
                     encounter_view.py, screen.py
    dead_mans_hand/  levels.py (was dead_mans_hand.py), game.py, weapons.py, screen.py, pvp.py (single copy)
  debug/      menu.py, poker_select.py, unlocks.py, actions.py (the debug_open_* functions)
multiplayer/  main.py, mp_*.py, room_*.py, party_*.py, net_client.py, connection_settings.py,
              multiplayer_paths.py, relay_server.py, room_relay.py, relay_websocket.py, relay_transport.py, tests/
              (no copies of game engines after Phase 11)
tests/        app/, ui/, menus/, profile/, career/, npc/, games/<area>/, debug/, packaging/, updater/, netservice/,
              support/ (helpers: locate.py, harness fixtures)
```

Exact file names inside an area may change if it makes the split cleaner. Keep the **area boundaries** above.

### 6.2 The screen interface

Every screen module exposes:

```python
# solitaireplus/games/casino/roulette_screen.py
from solitaireplus.app import state, sounds
from solitaireplus.games.casino import roulette_ui

def enter():               # optional: called when the state becomes this screen
    ...

def handle_event(event):   # body = the old event-chain branch for STATE_ROULETTE
    ...

def update(now):           # optional: per-frame logic that used to sit in the draw chain / post-event block
    ...

def draw(surface):         # body = the old draw-chain branch for STATE_ROULETTE
    ...
```

`app/loop.py` keeps a registry, built lazily so imports stay cheap and circular imports can't bite:

```python
SCREENS = {
    state_names.ROULETTE: "solitaireplus.games.casino.roulette_screen",
    ...
}
```

Each frame, the loop:
1. polls the update check, ticks app settings, and syncs audio;
2. handles global keys (F11, F10) and mouse mapping;
3. calls the debug screens, then `screen.handle_event`;
4. calls `screen.update(now)`, then `screen.draw(game_surface)`;
5. draws overlays (achievement popup, update banner on the main menu);
6. presents the frame.

**Order matters:** keep the exact order of the old loop. That includes where the timed NPC poker actions ran
(Chain B, after Chain A) and the post-event block. Pixel-identical baselines depend on it.

### 6.3 Shared state

`solitaireplus/app/state.py` holds the runtime variables that used to be `main.py` globals:

```python
# before (main.py)
career_cash = 0
def win(amount):
    global career_cash
    career_cash += amount

# after
# solitaireplus/app/state.py
career_cash = 0
# solitaireplus/career/economy.py
from solitaireplus.app import state
def win(amount):
    state.career_cash += amount
```

- **`globals()` callers:** pass `vars(state)` instead. It's the same dictionary interface, so `track_night_cash`,
  `store_event_progress`, `draw_score_four_table` and `debug_unlock_everything` work unchanged.
- **Constants, rects, fonts and images that are never reassigned** go to the module of the area that uses them (or
  `app/fonts.py` / `ui/` when shared), not to `state.py`.
- **Screen-only variables:** once an area is extracted, variables used by only that screen move into the screen
  module.
- **Import rule:** import modules, not names, for anything inside `solitaireplus` that might import back:
  `from solitaireplus.career import saving` → `saving.auto_save_career()`. Plain constants may be imported by name.

### 6.4 The refactoring tool (`tools/refactor/`)
- Write a small `libcst`-based tool. Don't hand-copy thousands of lines. It needs to:
  1. **Move** named top-level functions, assignments and block ranges from `main.py` into a target module, keeping
     comments.
  2. **Rewrite** reads and writes of names that now live in `state` to `state.<name>`, and remove the matching
     `global` statements.
  3. **Add imports** for moved functions, as `module.function` calls, in every place that calls them.
  4. **Report** any name it can't resolve. Fix those by hand, never by guessing.
- Run it area by area. After each run: `py_compile` everything, run the tests, then the safety net.
- Delete `tools/refactor/` and `requirements-dev.txt` in Phase 12.

### 6.5 `app/paths.py`

```python
"""One place that knows where game files are, from source and in the packaged build."""
import sys
from pathlib import Path

def root() -> Path:          # folder that contains assets/, data/, multiplayer/
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)                      # SolitairePlus_Data
    return Path(__file__).resolve().parents[2]         # repository root

def asset(*parts) -> Path: return root().joinpath("assets", *parts)
def data(*parts) -> Path:  return root().joinpath("data", *parts)
```

- Every `Path(__file__).parent / "assets"` and `"assets/..."` string becomes `paths.asset(...)`. Keep the string
  conversion where pygame needs `str`.
- `runtime_support.bootstrap()` may keep its `chdir`, for safety; nothing should rely on it any more.

---

## 7. Phases, step by step

### Phase 0: safety net (one commit, no game changes)

Build three things. All of them must run against **both** today's code and the code after each later phase.

**0.1 `tools/screen_harness.py`: screenshot comparison.**
- **How it runs the game:** it runs a given checkout's `main.py` through `runpy` in a subprocess, with
  `SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy` and a fixed window of 1366×768 (no scaling).
- **Determinism** before the game starts:
  - `random.seed(1234)`;
  - a virtual clock: patch `time.time`, `time.monotonic`, `time.perf_counter`, `pygame.time.get_ticks` and
    `pygame.time.Clock.tick` so each frame advances exactly 1/60 s;
  - a temporary `LOCALAPPDATA` with a fixed test profile save copied in (`tests/support/fixtures/profile_1.json`;
    create it from a fresh profile plus career unlocked, cash, a few NPCs);
  - `app_settings.json` set to auto-check off.
- **Driving it:** patch `pygame.event.get` to return scripted events, and `pygame.display.flip` to a hook. The hook
  runs once per frame. It can read **and write** the game's state:
  - **before the refactor**, through `sys._getframe(1).f_globals`, which is `main.py`'s namespace at the `flip()`
    call;
  - **after**, through `sys.modules["solitaireplus.app.state"]`.

  Put this in one probe function so scripts don't care which it is.
- **Reaching the screens:** for each of the 60 screens, a "scene" script reaches it the way a player would, or
  through the existing debug openers (`debug_open_blackjack`, `debug_prepare_poker_night`, `open_*`, `start_*`,
  …). Function names stay stable (§4.3), so the same scene works before and after.
  - Also capture key sub-states: dialogs open (pause, delete confirmation), mid-hand poker after a few NPC turns,
    results screens, the Options update panel, damaged-save slots.
- **Output:** one PNG per scene.
- **Comparison:** `tools/screen_harness.py compare --baseline <commit>`:
  1. creates a temporary `git worktree` at the baseline commit (default: the commit before the phase started);
  2. renders every scene there and in the working tree;
  3. diffs the pixels.

  It prints `IDENTICAL n/n`, or lists the scenes that differ and writes diff images to a git-ignored folder. Because
  it always compares two renders made on the same machine, baselines never need to be committed, and system fonts
  can't cause false differences.

**0.2 `tools/replay.py`: scripted playthroughs.**
- Same runner. About 15 journeys, each a list of events plus frame counts:
  1. create a profile;
  2. Options (change music mode, volume, window size);
  3. Solitaire: start, a few moves, win through the F10 menu once D1 exists (before that, F8); record the
     reward;
  4. a career day (hub, then jobs, real estate, news, leaderboards);
  5. blackjack: bet, hit, stand;
  6. roulette: bet and spin;
  7. a horse race;
  8. Faro;
  9. a Hold'em hand with NPC turns;
  10. Five-Card Draw;
  11. Seven-Card Stud;
  12. Crazy Eights and Score Four;
  13. each arcade machine for 5 seconds;
  14. Cryptid and Dead Man's Hand for a few seconds;
  15. the debug menu, then quit.
- At checkpoints it records `current_state`, cash, XP, level, rating, career day, and a screenshot.
- `compare` works like the screen harness (baseline worktree vs the working tree) and must say `IDENTICAL`.

**0.3 `tests/support/locate.py`: find code wherever it lives.**
- `locate.function("auto_save_career")` searches `main.py` and `solitaireplus/**` with `ast` and returns the
  source.
- Rewrite the 22 tests in §5.7 to use it, instead of reading `main.py` directly.
- Tests that check **source strings** (`test_arcade_support` and others): `locate.source_contains(snippet)` searches
  the same set of files.
- **Repair the three quarantined "fake environment out of date" tests:** `test_career_polish …reconcile_on_load…`,
  `test_cryptid_creatures …free_play…` and `test_npc_development …profile_load_anchors…`. Add the missing names to
  their fake environments, then remove them from `tests/KNOWN_FAILURES.txt`.
- **Also update `tools/run_tests.py`:** discover `test_*.py` **recursively** under each suite folder (tests move into
  subfolders later). Run each file by path; the import path must include the file's folder, the repo root, and (for
  multiplayer) `multiplayer/`.

**Done when:**
- `screen_harness compare` and `replay compare` against the current commit say IDENTICAL;
- all tests pass;
- the three repaired tests are out of quarantine.
- Commit: `Phase 0: safety net (screenshot harness, replays, code locator)`.

### Phase 1: package skeleton and paths (one commit)
1. Create `solitaireplus/` and its sub-packages (each with `__init__.py`, docstring only).
2. `git mv` every root module except `main.py` and `version.py` into its area (§6.1, mapping in §5.5). Merge
   `shared/` into `games/poker` and `npc` (`shared/poker_core.py` → `games/poker/core.py`, etc.), and **delete the
   root shims**.
3. **Rewrite imports everywhere** with the tool: the moved modules themselves, `main.py`, `multiplayer/*.py` (the 13
   root modules it imports, §5.6), `tests/**`, `tools/**`, `netservice` (none expected) and `updater` (none expected).
4. **Add `app/paths.py`** and convert the 17 `Path(__file__)`-based lookups and the `"assets/…"` / `"data/…"` strings
   in the moved modules. `main.py`'s own strings can wait for Phase 2.
5. **Update the build files:**
   - `SolitairePlus.spec`: `Analysis(['main.py'])` is unchanged. Keep `pathex=[project]`, check `hiddenimports`, and
     keep the `excludes` for `version`, `netservice` and `updater`. `MP_EXCLUDED` is unchanged.
   - `tools/make_manifest.py`: `COMPONENT_INPUTS["game"]` = `main.py` + `solitaireplus/**/*.py` + build tooling
     (still excluding `version.py`); update its tests.
   - `multiplayer_launcher.py`: now `solitaireplus/app/multiplayer_launcher.py`. Find the `multiplayer/` folder with
     `paths.root()`, not its own `__file__`. `main.py` imports it from the new place.
6. **Fix any test that imported moved modules by name.**
7. **Prove it:** all tests pass; screen and replay compares are IDENTICAL; a full `build_release.ps1 -SkipTests`
   passes all packaged self-tests; the packaged game launches (check the newest
   `%LOCALAPPDATA%\SimpleSolitaire\logs\game-*.log` is empty after 10 s).

Commit: `Phase 1 (move): package skeleton, all modules into solitaireplus/, paths helper`.

### Phase 2: the engine out of `main.py`
- **Move commit:**
  1. Create `app/state.py`. Use the tool to move **all** remaining module-level variables into it and rewrite the
     uses. `globals()` callers get `vars(state)`.
  2. Move window and scaling (12286–12386, 3424–3487, present 31967–32037) into `app/window.py`.
  3. Move fonts (4403–4540) into `app/fonts.py`.
  4. Move SFX, playlists and arcade tracks (556–868) into `app/sounds.py`.
  5. Move images, the menu drift, the catalogs and cursors (3967–4400) into `app/assets.py` and `ui/cursors.py`.
  6. Move the shared drawing helpers (14004–14500: `draw_button`, `draw_menu_button`, `render_text_fit`,
     `draw_wrapped_text*`, `draw_submenu_*`) into `ui/`.
  7. Move the **main loop into `app/loop.py`**, with the screen registry. In this phase every registry entry may
     point to a temporary `solitaireplus/legacy.py` module that still contains the old functions and the old
     event/draw branches, each wrapped as `handle_event` / `update` / `draw` per state.
  8. `main.py` becomes the ~40-line entry point.
  9. **Done when** compares are IDENTICAL and tests pass.
- **Fix commit:** **W1 (windowing, high priority)**, B15, B16, B17, B62, B63, B64, B65 (§8).

### Phases 3–10: one area at a time
For each phase:
1. Move that area's functions, rects, fonts, screen variables and event/draw/update branches out of `legacy.py`
   into the area's modules. Register the screens.
2. Move that area's tests into `tests/<area>/`.
3. Prove IDENTICAL, then commit the move.
4. Fix the area's bugs (§8), each with a test.
5. Re-run the compares and confirm that only the intended scenes changed (list them).
6. Commit the fix and report.

| Phase | Area (states) | Bugs |
|---|---|---|
| 3 | Menus and profile: SPLASH, MENU, MODE_SELECT, FREE_PLAY_SELECT, DIFFICULTY, HOW_TO_PLAY, ACHIEVEMENTS, OPTIONS, CUSTOMIZE, PROFILE_SELECT, PROFILE, RECAP, LEVEL_UP | B7, B9–B14, D1 (Customize "+100 XP" button) |
| 4 | Solitaire: PLAYING, round completion and rewards, Head-to-Head | B1–B6, B8, D1 (F7/F8) |
| 5 | Career: CAREER_* states, CASE_OPENING, ratings/fans/news, NPC world | B18–B23 |
| 6 | Casino: BLACKJACK*, ROULETTE, HORSE_RACES, FARO | B24–B34, B66 |
| 7 | Poker: TEXAS_HOLDEM*, FIVE_CARD_DRAW*, SEVEN_CARD_STUD*, FIVE_O_POKER, BLIND_MANS_BLUFF, DEBUG_POKER_NPC_SELECT, timed NPC actions | B35–B45, **B86 (stop and show the audit table first)**, D1 (Hold'em F7/Space/B) |
| 8 | Casual cards: CRAZY_EIGHTS, BANGO, SCORE_FOUR* | B46–B48, D1 (Score Four F6) |
| 9 | Arcade: ARCADE_* hub states, the four machines and their select screens | B49–B58 |
| 10 | Cryptid, Dead Man's Hand, debug: CRYPTID_CREATURES, DEAD_MANS_HAND, DEBUG_MENU | B59–B61, D1 (instant-win button in F10, F10 ignored while typing) |

After Phase 10, `solitaireplus/legacy.py` should be empty; delete it.

**Packaged build checkpoints:** after Phases 2 and 7, run a full `build_release.ps1 -SkipTests`, the packaged
self-tests, and a 10-second launch of the packaged game.

### Phase 11: merge the multiplayer copies
1. **Make the shared engines support both modes** with explicit options instead of copies. Typical options:
   `allow_network_spectator`, `show_utility_buttons`, `quick_chat_enabled`, and customization on/off. Where a
   multiplayer-only behaviour exists (e.g. busted-seat dealing), add it to the shared engine behind a flag.
2. **Delete the 17 copies and shims** from `multiplayer/`. `multiplayer/*.py` now import from
   `solitaireplus.games.poker…`, `solitaireplus.app.audio`, `solitaireplus.npc…` and
   `solitaireplus.games.dead_mans_hand.pvp`.
3. **Remove LAN play** (designer: not needed): `lan_transport.py` and `lan_session.py`, plus `test_lan.py` and the
   LAN-only tests.
   - **Keep the parts the room code still uses:** `ClientGame` and `snapshot` (from `lan_protocol.py`), and
     `TwoHumanGame` (from `lan_table.py`). Move them into `room_protocol.py` and `room_game.py`.
   - Also remove the unreachable offline Practice table (`standalone_table.py`, `standalone_view.py`) **only if**
     nothing reachable uses them; `TableView` is used as an asset loader, so check first.
   - Remove the quarantine entries for the deleted tests.
4. **Update `SELFTEST_SKIP` / `MP_EXCLUDED`** if file names change, and the spec's `hiddenimports`. The packaged
   multiplayer self-test **must pass**.
5. **Fix B67–B85.** Then make a full packaged build and run a local two-player game:
   - start `relay_server.py --bind 127.0.0.1 --port 50111`;
   - drive two `NetPeer` clients through the packaged `SolitaireNet.exe`, as in `tests/test_relay_websocket.py`;
   - also run a multiplayer window from source against `127.0.0.1`.

### Phase 12: cleanup (one commit)
1. Delete the dead code listed in §5.1 (duplicate defs, duplicate assignments, `STATE_WIN`, the probably-dead
   functions, after confirming with `locate` that nothing calls them).
2. Delete the stale root `dead_mans_hand_pvp.py`, if it wasn't already handled in Phase 11.
3. Delete `tools/refactor/` and `requirements-dev.txt`.
4. Move `verify_solitaire_state.py` to `tools/` and update its paths. Merge the stray root
   `test_dead_mans_hand_weapon_system.py` into `tests/games/dead_mans_hand/`.
5. **Prune old log files (#15):** in `runtime_support.bootstrap()`, keep the newest 10 `game-*.log` files, and add a
   test.
6. Empty `tests/KNOWN_FAILURES.txt` as far as possible:
   - each remaining entry must still be genuinely broken, with a reason;
   - the `/workspace/scratch` image-path tests: point them at a temporary folder and un-quarantine;
   - the tests for old UI layouts: rewrite them or delete them if their feature is gone.
7. Final full build with `-Installer`, all self-tests, a packaged launch, full tests, compares.

Commit: `Phase 12: cleanup`. Then hand back (§10). **Don't write the user docs** (`docs/RELEASING.md`,
`docs/INSTALLING.md`, `docs/CODE_SIGNING.md`, `AGENTS.md`); the original session does that. Do keep
`docs/TESTING.md`, `docs/NETWORKING.md` and the CHANGELOG accurate as you go.

---

## 8. Bug list

W1 (windowing) is under Phase 2 below. The designer reported it as the most visible problem, so give it extra care.

Each entry gives the location (at commit `154b890`), what goes wrong, the intended fix, and the regression test.
Severity is H, M or L.

### Phase 2: app-wide
- **B15 (M): hover lost after any key press.**
  - Where: `main.py` 24255–24268 sets `game_mouse_pos = None` for every event without `.pos`; draw code uses it
    (e.g. 30707, 30854, 31952).
  - Fix: keep `state.mouse_pos` from `pygame.mouse.get_pos()` mapped once per frame. Event handlers use the event's
    position; drawing uses the per-frame position.
  - Test: press a key while hovering a button; the button stays highlighted (render compare of a scene).
- **B16 (L): Options slider stuck dragging.**
  - Where: the `music_slider_dragging` / `sfx_slider_dragging` handling (29356, 29387). If F10 switches screen
    mid-drag, the release goes elsewhere.
  - Fix: reset the drag flags in Options `enter()` and when leaving it.
  - Test: start a drag, switch state, come back, move the mouse; the volume is unchanged.
- **B17 (M): heavy work every frame.**
  - Where:
    - `draw_drifting_menu_background` (22194–22275) blits a ~4300×2500 image and smoothscales it every frame;
    - `draw_menu_button`@14092 and `draw_submenu_title`@14403 smoothscale their images per call;
    - fonts created per frame at 11792, 13838, 14188, 17148, 17947, 19830, 20354 and 23203, plus `SysFont` in
      `draw_career_hub` (15348) and `draw_profile_screen` (23334).
  - Fix:
    - a `ui/text.py` font cache, `get_font(name_or_None, size, bold=False)`, memoised;
    - a `ui/buttons.py` scaled-image cache keyed by `(image id, size)`;
    - the menu drift pre-scaled once per window size.
  - Test: call each draw function twice and assert the font or scaling constructor is called only once (patch
    `pygame.font.Font` / `SysFont` / `smoothscale` with counters). Render compare stays IDENTICAL.
- **B62 (H): every other music track skipped.**
  - Where: `audio.py` `update()`@379–410 starts the next track when the mixer is idle, and `handle_event()`@369–377
    also advances on the end-of-music event.
  - Fix: advance the playlist in exactly one place (the end event), and have `update()` only handle fades and
    transitions. Check that `set_music_mode` and arcade fade-outs don't trigger a double advance.
  - Test: simulate one end-of-music event and the next `update()`; the playlist index advanced by 1.
- **W1 (H, reported by the designer: "Resolution and windowing is fucked").**
  - **Symptoms:**
    - The game often launches looking fullscreen, with controls partly cut off.
    - At other times, switching back to window mode leaves the window's title bar (with its minimise, maximise and
      close buttons) off-screen, cut off along with parts of the game.
  - **Causes found** (reproducible on Dan's PC, where SDL reports the desktop as **1536×960**):
    1. **Fixed 1920×1080 default window, whatever the monitor.** `settings.py` `DEFAULT_WINDOW_SIZE = (1920, 1080)`,
       used at `main.py` 3443 (`WINDOW_WIDTH, WINDOW_HEIGHT = DEFAULT_WINDOW_SIZE`, then
       `pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))`). On any screen whose usable area is smaller than
       1920×1080 plus the title bar and taskbar (most laptops, and all screens with display scaling of 125% or more),
       the window is bigger than the screen. It looks "fullscreen", and its title bar and edges sit off-screen.
    2. **The process isn't DPI-aware.** Nothing calls `SetProcessDpiAwareness` or sets SDL's DPI hint (searched:
       none), so Windows treats sizes as logical pixels and stretches the window by the scaling factor. That's why
       SDL sees 1536×960 on this PC, and why windows can look blurry.
    3. **Leaving fullscreen doesn't re-centre the window.** `set_fullscreen_enabled(False)` (`main.py` 12350–12361)
       calls `set_mode((WINDOWED_WIDTH, WINDOWED_HEIGHT))` without positioning the window. SDL can leave the client
       area at (0, 0), so the title bar lands above the top of the screen. `set_window_size` (12293) has the same
       problem.
    4. **The Options window sizes ignore the screen.** `RESOLUTION_OPTIONS` (`settings.py`) always offers 1600×900,
       1920×1080 and 2560×1440, even when they can't fit.
    5. **Saved sizes are never clamped.** Since Step 4, `app_settings.json` remembers `window_size` and `fullscreen`,
       and `apply_saved_app_settings()` (5667) restores them without checking that they fit the current screen. A size
       saved on a big monitor breaks the game on a laptop.
    6. **Fullscreen distorts the picture.** The 1366×768 (16:9) `game_surface` is stretched separately in x and y
       (present code 31967–32010, `window_to_game_coords`@12367). On a 16:10 or 3:2 screen it's distorted (not cut
       off, but wrong).
    7. **The multiplayer window has the same problems.** `multiplayer/mp_options.py:35` uses its own
       `set_mode(... size or (0, 0) FULLSCREEN, RESIZABLE)` with fixed sizes, and inherits the single-player window
       size through `SOLITAIRE_MP_WINDOW` (`multiplayer_launcher.py`).
  - **Fix, in `solitaireplus/app/window.py`** (Phase 2 fix commit; multiplayer switches to the same helper in
    Phase 11):
    1. **Make the process DPI-aware** before `pygame.display.init()`: set `SDL_WINDOWS_DPI_AWARENESS=permonitorv2` in
       the environment. If needed, also call `ctypes.windll.shcore.SetProcessDpiAwareness(2)` in a try/except; Windows
       only.
       - Re-check `detect_accessible_cursor_mode()` (`main.py` 4305), which reads system metrics and may now return
         physical sizes.
    2. **Use pygame's built-in scaling.** `pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.SCALED |
       pygame.RESIZABLE)` makes SDL scale the 1366×768 picture to the window with **letterboxing** (no distortion) and
       map mouse positions automatically. The manual scaling (31967–32010), `scaled_surface_cache` and
       `window_to_game_coords` can then go.
       - Spike this first (half an hour): confirm with pygame-ce 2.5.8 on Windows that `SCALED | RESIZABLE`,
         `pygame.display.toggle_fullscreen()`, the software cursor fallback, and window resizing through
         `pygame.Window.from_display_module()` all work.
       - If `SCALED` can't do something needed, keep manual scaling but add letterboxing and fix the size and
         position rules below.
    3. **Size rules:**
       - Compute the usable area of the monitor the window is on: the work area without the taskbar
         (`SystemParametersInfoW(SPI_GETWORKAREA)` via ctypes, or `MonitorFromWindow` + `GetMonitorInfoW`), minus the
         title bar height (`GetSystemMetrics(SM_CYCAPTION)` + frame).
       - **Default window** = the largest 16:9 size that fits within 90% of that area (never above 2560×1440, never
         below 1024×576).
       - **Options → Window Size** offers only sizes that fit. Show the others greyed out with "too large for this
         screen".
       - **On startup**, clamp a saved `window_size` that no longer fits.
    4. **Always centre the window** when it's created, when its size changes, and when leaving fullscreen
       (`window.position = pygame.WINDOWPOS_CENTERED`, or the `SDL_VIDEO_CENTERED=1` environment variable before
       `set_mode`).
    5. **Fullscreen = desktop fullscreen** on the window's current monitor (`toggle_fullscreen()` with `SCALED`),
       letterboxed. If the game is started fullscreen from saved settings and the monitor changed, still fit
       correctly. F11 and Options keep working; `app_settings` keeps saving the choice.
  - **Tests:**
    - Unit-test the pure size logic in `window.py`: given a work area, the DPI scale and a saved size, it returns the
      default size, the allowed Options sizes and the clamped saved size. Use cases: 1366×768 laptop; 1920×1080 at
      125%; 2560×1600 at 150%; 1536×960 logical (this PC); 3840×2160 at 200%; ultrawide 3440×1440.
    - Mouse mapping test: with letterboxing, a click on a known button lands on it. With `SCALED`, test through a
      posted `MOUSEBUTTONDOWN` at the window position converted by SDL.
  - **Manual check on Dan's PC (you can run it; it doesn't change system settings):**
    1. Launch from source and the packaged build.
    2. Read the window rectangle with `GetWindowRect` via ctypes. It must lie fully inside the work area: title bar
       visible, nothing off-screen.
    3. Toggle F11 five times and confirm the same after each return to windowed mode.
    4. Pick every offered Options size and check the same.
    5. Start with a saved `window_size` of 2560×1440 and confirm it's clamped.
    6. Repeat for the multiplayer window in Phase 11.
- **B63 (L): `null` sections in a save crash loading.**
  - Where: `profile.py` load path (`data.get("progression",{}).get(...)` where `progression` is `null`; `career`
    likewise). Loading also doesn't normalise `career.arcade` (saving does).
  - Fix: treat non-dict sections as empty dicts. Normalise `arcade` on load.
  - Test: save JSON with `"progression": null` and `"career": null` loads without error.
- **B64 (L): missing rating key crashes.**
  - Where: `npc_manager.py:58` `state["ratings"]["overall"]` raises KeyError.
  - Fix: `.get` with a sensible default.
  - Test: a state without `"overall"`.
- **B65 (L): `RatingPoints.__format__` condition reversed** (`career_ratings.py:26-27`), so the replace never runs.
  - Fix the condition. Test: formatting with `"d"` / `"f"` specs.

### Phase 3: menus and profile
- **B7 (L): level-up screens lost.**
  - Where: the recap handlers at 29836 and 29870 assign `level_up_queue = …` instead of extending it.
  - Fix: extend. Test: two queued level-ups both show.
- **B9 (H): "Level N" hidden under the Delete button.**
  - Where: `draw_profile_select_screen`: the level text uses `right=rect.right - 20` (around 21410–21415), inside
    `profile_delete_rects` (4810–4818: `right-110 … right-20`). Also hides "Can't open" for damaged saves.
  - Fix: `right = delete_rect.left - 16` when a slot has a Delete button.
  - Test: render compare (intended change); assert the text rect doesn't intersect the delete rect.
- **B10 (M): saves read every frame.**
  - Where: `get_profile_slot_display_data`@10430 is called 3× per frame (around 21312). Each call reads, parses and
    migrates a save; for a damaged save it also hashes the file (`profile.py` `_keep_damaged_copy`).
  - Fix: cache slot data in the profile-select screen. Refresh on `enter()`, after save, delete, or create.
  - Test: draw 10 frames and count `load_profile` calls (1 per slot).
- **B11 (L): avatar arrows crash.**
  - Where: `cycle_option`@10476 uses `options.index(current)`; fallbacks such as `"base_01"` (10994–11000) may not be
    in the bank.
  - Fix: if not found, start from index 0.
  - Test: `cycle_option("missing", ["a", "b"], 1)` returns `"a"` or `"b"`, with no exception.
- **B12 (L): failed save reported as saved.**
  - Where: around 30135–30151 ignores `save_profile`'s `False` (locked file → recovery copy).
  - Fix: show "Saved to a recovery file (the save is in use). Close other copies of the game."
  - Test: patch `save_profile` to return False; check the message.
- **B13 (L): the loaded profile can be deleted.**
  - Where: around 24672–24676 only guards when `profile_switch_snapshot` is set.
  - Fix: block deleting `current_profile_slot` (show a message).
  - Test: try to delete the loaded slot; the file still exists.
- **B14 (H): splash screen forces Ambient music.**
  - Where: 24615 calls `audio.set_music_mode("ambient")` when leaving the splash screen, overriding the restored
    setting.
  - Fix: use the saved mode (`app_settings.get("music_mode")`, or the current `audio.music_mode`).
  - Test: with saved mode `"off"`, leaving the splash keeps `"off"`.

### Phase 4: Solitaire
- **B1 (M): auto-solve stops early.**
  - Where: `game.py:2172-2173` (auto-solve steps every 140 ms, `:162`) vs `click_stock`, which does nothing during the
    220 ms flip animation (`:1613-1628`).
  - Fix: when a stock move is blocked by the animation, auto-solve waits instead of giving up.
  - Test: a deal needing a recycle completes.
- **B2 (L): Restart after a race deal restores the wrong deal.**
  - Where: `game.py:439-446` `new_race_game()` calls `new_game()`, which captures the random deal (`:523-524`), before
    swapping in the race layout.
  - Fix: capture after the race layout is set.
  - Test: after `new_race_game`, the restart snapshot equals the race deal.
- **B3 (L): the Head-to-Head countdown counts against the player.**
  - Where: `game.py:508` and `head_to_head.py`: the timer starts at deal time.
  - Fix: start the player's timer when the countdown ends.
  - Test: elapsed time at the end of the countdown is 0.
- **B4 (H): invisible Career Solitaire hotspot.**
  - Where: `career_play_rect` (defined at 14347; also 5182) handled at 25136–25149 but never drawn. It sits over
    calendar row 0 and opens Career Solitaire with no pending activity; wins pay without using a day. It's an `if`,
    so the jobs, real-estate, news and back checks also run on the same click.
  - Fix: remove the hotspot and its handler. Remove the duplicate rect too.
  - Test: clicking that area doesn't change state to PLAYING.
- **B5 (M-H): "Leave table? → No" deals a new paid game.**
  - Where: 29853–29875: after the pending activity was cleared (30652–30654), it deals a fresh career game, and later
    wins pay full career rewards with no day used.
  - Fix: "No" returns to the finished round (or the hub) without dealing a paid game.
  - Test: the reward-eligible flag is not set after "No".
- **B6 (L): abandoning a career round leaves stale state.**
  - Where: around 30349–30350 ("Yes, return to menu").
  - Fix: clear `pending_career_activity_*` and call `game.clear_challenge()`.
  - Test: both are cleared after abandoning.
- **B8 (L): Head-to-Head opponent keeps racing in Options.**
  - Where: 30494–30521 uses wall-clock progress while the pause → Options screen is open.
  - Fix: pause the opponent while not in PLAYING.
  - Test: time spent in Options doesn't advance the opponent.
- **D1 (part):** delete Solitaire F8 (30250–30271) and F7 (30273–30278). In Phase 10, the F10 menu gets a
  "Win this Solitaire round" button that calls the same code F8 called (it is the designer's instant win).

### Phase 5: Career
- **B18 (M-H): the NPC roster re-syncs several times per frame.**
  - Where: `draw_career_hub` calls `ensure_career_leaderboard()` (15434) and `get_career_leaderboard()` (16114, which
    calls ensure again, 13439). Each runs `sync_career_npc_runtime_state` (13254–13263), which builds a seeded RNG per
    NPC and deep-copies the templates. The leaderboards screen (17677) and rank lookups do the same.
  - Fix: a "dirty" flag set when the roster or date changes. Sync only when dirty.
  - Test: draw the hub 10 frames, and sync runs at most once.
- **B19 (L): job switching spams news.**
  - Where: 28192 adds news on every change.
  - Fix: only when the job actually changes, and at most once per day.
- **B20 (L): KeyError every frame on bad activity data.**
  - Where: 2697–2698 and 30746–30747 index `["career_activity"]` and `state["claimed"]`.
  - Fix: `.get` with defaults, and skip a malformed activity.
- **B21 (M-L): sandbox cash saved into the real profile.**
  - Where: debug "Career Hub" (24346–24348) during a Free Play sandbox doesn't call `finish_free_play_sandbox`. Hub
    saves (2926–2947) then write the sandbox $5,000.
  - Fix: the debug menu ends any sandbox before jumping.
  - Test: no saved cash change.
- **B22 (L): debug launchers leak "debug" mode.**
  - Where: `debug_prepare_arcade_night` (8565), `debug_open_horse_races` (9584) and `debug_open_five_o_poker` (9807)
    set `current_game_mode = "debug"` and never restore it. Debug Casual and Casino nights lack `debug: True`, so
    ending them advances the real day (28568–28576).
  - Fix: restore the previous mode on exit, and mark debug nights.
  - Test: a debug night doesn't change the career day.
- **B23: no change (designer decision).** The monthly NPC rating decline is intended (NPCs age and are replaced).
  - Add a test that pins today's behaviour (`career_ratings.simulate_npc_rating_month` with `scale_rewards=True`), so
    the refactor can't change it.
  - **Report to Dan:** simulate 12 months for a young NPC (age ≤ 22) and a veteran (age ≥ 35), and give the rating
    change of each. Do not change the code.

### Phase 6: Casino
- **B24 (H): roulette re-spin never pays.**
  - Where: `roulette.py:235` `start_spin` doesn't reset `payout_claimed`; only adding a new bet type does (`:227`).
    `settle_roulette_round` (`main.py:8328`, early return at 8336) then skips the payout, XP and achievements.
    Adding chips (`:201-211`) and `clear_bets` (`:536-543`) don't reset it either.
  - Fix: reset `payout_claimed` (and `round_complete` / `result`) in `start_spin`. Also fix
    `tests/test_career_ratings.py:328`, which hid this by resetting the flag by hand.
  - Test: two spins with the same bets both pay.
- **B25 (M): roulette cash taken when the spin doesn't start.**
  - Where: 27484–27489 deducts before checking `start_spin()`.
  - Fix: deduct only when it returns True (or refund).
  - Test: a refused spin leaves cash unchanged.
- **B26 (L):** adding chips after a round shows the old result against the new stake (`roulette.py:201-211`).
  - Fix: clear `result` and `round_complete` when bets change after a round.
- **B27 (H): blackjack duplicate cards.**
  - Where: `blackjack.py:66-69` `draw_card` rebuilds a full 52-card deck mid-hand; the game object lives for the whole
    run (`main.py:3528`).
  - Fix: before dealing a round, reshuffle if fewer than ~15 cards remain; never rebuild mid-hand. If the deck still
    runs out (impossible with a reshuffle threshold, but guard it), build from cards not in play.
  - Test: deal 200 rounds; no round ever shows a duplicate card.
- **B28 (H): wrong blackjack 3:2 rounding.**
  - Where: `blackjack.py:444` `int(round(self.bet * 2.5))` uses banker's rounding.
  - Fix: `self.bet * 5 // 2` plus a half-up rule. The designer's chips are whole dollars, so pay
    `bet + (bet * 3 + 1) // 2`, or keep the cents if the game supports them; check the money type first.
  - Test: bets 1, 3 and 5 return 1+2, 3+5 and 5+8 (half-up on 1.5, 4.5 and 7.5).
- **B29 (L): a single-hand bust is recorded as "split".**
  - Where: `blackjack.py:316-320`, which routes to `_resolve_split_round` (`:378-397`).
  - Fix: unsplit rounds use the unsplit resolution.
  - Test: `.result == "dealer"` after a single-hand bust.
- **B30 (L): "low stand" achievement without standing.**
  - Where: `achievements.py:507` relies on `stood`, which is True on every round-ending path.
  - Fix: pass a real "player chose Stand" flag.
  - Test: doubling to 11 doesn't award it.
- **B31 (M): horse-race music ducking becomes permanent.**
  - Where: 9482–9490 captures the "previous" volume while already ducked; `stop_horse_race_music` (9525) restores the
    ducked value; Options then saves it.
  - Fix: capture the base volume only when not already ducked, and restore on every exit path.
  - Test: enter and leave twice; the volume is back to the original.
- **B32: no change (designer).** Place and show odds stay as they are.
- **B33 (M): Faro risk-free rating.**
  - Where: `faro.py:108-139` remove and clear don't lower `wagered_total`; `main.py:9622` uses `wagered_total > 0` as
    "really played".
  - Fix: track the money actually at risk when a turn resolves.
  - Test: place, remove, deal and cash out gives no rating change.
- **B34 (M): blackjack fonts every frame.**
  - Where: `_render_blackjack_fit` (5741–5749) builds up to 9 `SysFont` per label per frame.
  - Fix: use the B17 font cache.
- **B66 (L): roulette chip labels truncate** "$1,500" to "1k" (`roulette_ui.py:391-394`).
  - Fix: show "1.5k".

### Phase 7: Poker (single-player)
- **B35 (M): stale Hold'em session-end timer.**
  - Where: `start_texas_holdem_session`@7249 never resets `texas_holdem_session_end_at` (Draw resets it at 7574, Stud
    at 7946).
  - Fix: reset it at session start.
  - Test: bust, return, start again; the session doesn't end on frame 1.
- **B36 (L): NPCs can raise when nobody can respond.**
  - Where: `texas_holdem.py` `can_npc_raise` (around 2977–3030) lacks the guard in `can_player_raise` (`:3655`).
  - Fix: shared guard (B86).
- **B37 (M): chips vanish from a pot layer with no eligible player.**
  - Where: `texas_holdem.py:4571-4572` and `five_card_draw.py:873-874`.
  - Fix: return such chips to their contributors (or fold them into the next eligible layer); the B86 shared side-pot
    builder.
  - Test: total chips are conserved over 1,000 random all-in hands.
- **B38 (L, designer: fix everywhere): odd chips.** Hold'em gives them to the lowest seat (`texas_holdem.py:4601`),
  Draw from the dealer's left (`five_card_draw.py:891-901`).
  - Fix: one shared function in `games/poker/core.py`: odd chips go one at a time, starting at the first eligible
    winner left of the dealer. Use it in every variant (and multiplayer Hold'em after Phase 11).
- **B39 (M): Draw and Stud require the full forced bet against a short all-in.**
  - Where: `five_card_draw.py:196` and `seven_card_stud.py:570-573`. The Hold'em fix is at `texas_holdem.py:1085-1090`.
  - Fix: shared rule (B86).
- **B40 (L): Stud picks an all-in player for the bring-in.**
  - Where: `seven_card_stud.py:302-335`.
  - Fix: skip players with no chips.
- **B41 (L): a Draw discard silently keeps the old card** when the deck runs out (`five_card_draw.py:451-456`).
  - Fix: reshuffle the muck if the deck is empty, or log correctly.
- **B42 (L): Blind Man's Bluff refund remainder lost; ties miscounted.**
  - Where: `blind_mans_bluff.py:394-398` (`//` drops the remainder) and `:417-421` (`hands_tied` counts split
    main/side wins as ties).
  - Fix: distribute the remainder with the B38 rule; count a tie only for an equal-rank split of one pot.
- **B43 (L): blank "Eligible:" line in the recap** for a single-winner pot (`texas_holdem.py:2134-2145`).
  - Fix: fill `eligible`.
- **B44 (M): fonts created per frame** in `poker_recap.py:39, 83, 88, 105` (plus a font per click in
  `recap_display_lines`), `five_o_poker_ui.py:110` (per card), `:279`, `:331`, `:344`, `score_four_ui.py:68-71, 131,
  247, 304`, `career_activities_ui.py:21, 34, 74, 104` and `head_to_head_ui.py:139, 302`.
  - Fix: the B17 font cache. (The Score Four, career and Head-to-Head ones may be fixed in their own phases; list them
    there if so.)
- **B45 (L): duplicates.** Remove the three duplicated Hold'em sound functions (keep the version Python currently
  uses: the later definition), the duplicate `STATE_CAREER_NEWS`, and the duplicate assignments (§5.1).
- **B86 (M, designer request): align the poker variants.** Do this inside the fix commit, **after showing Dan the
  audit table**.
  1. **Audit:** for Hold'em, Five-Card Draw, Seven-Card Stud, Five-O, Blind Man's Bluff, and multiplayer Hold'em
     (`multiplayer/texas_holdem.py`), make a table with one row per shared rule and one column per variant. Show the
     current behaviour and file:line in each cell. Rows:
     - forced bets (blinds, antes, bring-in) when a player can't cover them;
     - `current_bet` after a short all-in forced bet;
     - minimum raise and minimum re-raise;
     - raise allowed when ≤ 1 player can still act (player **and** NPC);
     - side-pot building, including layers with no eligible player;
     - odd-chip distribution;
     - ties and split pots;
     - showdown order and mucking;
     - all-in run-outs (deal remaining streets without betting);
     - busted players (sit out / removed / rebuy);
     - session start and end resets (timers, logs, quick chat, learning store);
     - NPC action timing and delays;
     - hand evaluation (the same evaluator for the same hand type).
  2. **Stop.** Send Dan the table and mark the differences you intend to unify, plus the ones that look deliberately
     different (e.g. Stud's bring-in, Blind Man's Bluff's single card). Wait for the answer.
  3. **Unify:** implement each shared rule once in `games/poker/core.py` and call it from every variant. Multiplayer
     Hold'em picks these up in Phase 11.
  4. **Tests:** one test per shared rule, run against every variant through a small adapter, including chip
     conservation (property-style: 1,000 random hands per variant, seeded).
- **D1 (part):** delete Hold'em F7 (26210–26217 with `debug_setup_holdem_heads_up`@7119–7191, which stays reachable
  from the F10 menu if it's already there), Space (26223–26305, deals streets without betting) and B (26311–26360,
  bets $50 and prints).

### Phase 8: Casual cards
- **B46 (M, designer accepted): Crazy Eights ends when one player can't draw.**
  - Where: `crazy_eights.py:460-466` `_draw_one` calls `_resolve_blocked_game` immediately. The NPC path then logs
    "cannot draw" (`:315`) over the result.
  - Fix: a player who can't play and can't draw passes. The game ends as blocked only when every player passes in a
    row; then the smallest hand wins.
  - Test: two players with playable cards continue after a third can't draw.
- **B47 (L, designer accepted): after drawing a playable card, any card can be played** (`crazy_eights.py:256-275`).
  - Fix: standard rule: after a draw, the player may play only the drawn card, or pass. NPCs follow the same rule.
- **B48 (L): Score Four hint recursion** (`score_four.py:291-301`) can loop forever on an unsolvable puzzle.
  - Fix: a depth limit and a "no hint" result.
- **D1 (part):** delete Score Four F6 (27859–27865).

### Phase 9: Arcade
- **B49 (M): fixed time step.**
  - Where: `main.py` 30936, 30952, 30961 and 30970 pass `1/60`.
  - Fix: pass the real frame time from the loop's clock, capped at 1/20 s.
  - Test: the game state after one update with dt = 1/30 equals two updates with 1/60, within tolerance, for each
    machine.
- **B50 (H): Suit Snake races ahead after any pause.**
  - Where: `suit_snake_game.py:383-386`: steps owed grow without limit (`_last_step_at` isn't clamped).
  - Fix: after catching up 2 steps, set `_last_step_at = now`.
  - Test: a 3-second gap then normal frames: the snake moves at its normal rate.
- **B51 (H): Suit Snake creates 2 fonts per token per frame** (`:499-508`). Fix: cache.
- **B52 (H): Ace Invaders rescales its background every frame** (`ace_invaders_game.py:554-564`). Fix: cache per size,
  like `_fit_image`.
- **B53 (M): King Pong serve goes the wrong way.**
  - Where: `king_pong.py:440` `_pending_serve_to_player = bool(player_scored)` contradicts the comment (`:433`).
  - Fix: invert.
  - Test: after the player scores, the serve heads to the NPC.
- **B54 (M): whole-pixel rounding.** Rect positions are rounded to whole pixels
  (`ace_invaders_game.py:395`, `king_pong.py:311-354`), losing 12–17% speed unevenly.
  - Fix: keep float positions and copy them into the Rects for drawing and collisions.
- **B55 (L): Ace Invaders shots during the wave break count against accuracy** (`:489-496`). Fix: don't fire, or
  don't count, during the pause.
- **B56 (L): Enter in King Pong forfeits mid-match** (`main.py:28985-28988`). Fix: Enter only works when the match is
  finished, like the other machines.
- **B57 (L): Suit Snake "new high score" fires on the first card** (`suit_snake_game.py:298-304`). Fix: require a
  previous score above 0, like Ace Invaders (`:438-443`).
- **B58 (L): Battle Bosses font per frame** (`battle_bosses_game.py:637`). Fix: cache.

### Phase 10: Cryptid, Dead Man's Hand, debug
- **B59 (M): the debug menu's Close button doesn't recapture the mouse in Dead Man's Hand** (24588–24592; only the F10
  path at 24238 does). Fix: share the "return to previous state" code.
- **B60 (L): StopIteration for a Cryptid deck with fewer than 2 creatures** (`cryptid_creatures.py:199`). Fix: guard
  and show a message.
- **B61 (L): Dead Man's Hand enemies can spawn in unreachable spots** (`dead_mans_hand.py:43-78`). Fix: flood-fill
  from the player start and spawn only in reachable cells.
- **D1 (complete):**
  - Add a **"Win this Solitaire round"** button to the F10 menu. It is enabled only while in PLAYING and calls the old
    F8 code path.
  - **Ignore F10 while a text field is active** (profile name and bio, multiplayer code, and so on).
  - **Confirm** none of these remain: Solitaire F7/F8, Hold'em F7/Space/B, Score Four F6, and the Customize "DEBUG +100
    XP" button (`debug_xp_rect`, 12425, 23319, 29634).

### Phase 11: Multiplayer
- **B67 (M): the six-seat test mixes two clocks.**
  - Where: `multiplayer/tests/test_six_seat.py` `pump()` uses `int(time.monotonic()*1000)`, while the main loop
    restarts `now` from 0. `room_table.py` `self.due` (230) and `resume_at` (221–224) then never pass.
  - Fix: use one clock in the test. In `RoomAuthority`, if `now < self.due - big_gap` (time went backwards), re-arm
    `due`.
  - Un-quarantine `test_six_clients_and_late_join`.
- **B68 (M, designer accepted): humans replace busted NPCs.**
  - Where: `room_table.py` `assign()` (52–53) skips 0-chip NPC seats; `update()` calls `boundary()` (218) before
    `replace_busted_npcs()` (190).
  - Fix: at the hand boundary, seat a waiting human in a busted NPC's seat with the normal buy-in, **before** creating
    a replacement NPC.
  - Un-quarantine `test_late_join_no_mid_hand_takeover` (FLAKY) once 50 runs pass.
- **B69 (H): revision spam while a waiter can't be seated.**
  - Where: `room_table.py:218` bumps the revision every frame; guests' actions (`act()` at 120 requires an exact
    revision) are all rejected.
  - Fix: bump only when something changed.
- **B70 (M): the countdown rejects guest actions.**
  - Where: Hold'em `room_table.py:223` and Roulette `party_authority.py:762-764` bump the revision every second.
  - Fix: send the countdown as a timestamp ("starts at") or field without bumping the revision; or accept actions for
    the previous revision when they're still legal.
- **B71 (H): party-game late joiners never seated** (`party_authority.py` 87–95, 304–305; Blind Man's Bluff and
  Roulette never return to the lobby).
  - Fix: seat waiters at the next hand or spin boundary, as in Hold'em.
- **B72 (H): a disconnect hangs Blind Man's Bluff** (`leave()` 111–123 keeps the seat as Human; `update` auto-acts only
  for NPCs, 592–593).
  - Fix: a disconnected seat auto-folds or auto-checks (or becomes an NPC).
- **B73 (M-H): Blind Man's Bluff spins every frame when fewer than 2 seats can ante** (404–413 with 588–590).
  - Fix: enter a "finished" phase.
- **B74 (M): Score Four ghost seats after a disconnect** (117–120, 125–126). Fix: free disconnected seats at
  `return_lobby`.
- **B75 (M): a Score Four solve can be lost** (`party_view.py:353-354` marks it sent before success). Fix: mark only
  on a successful act; retry on the next frame.
- **B76 (L-M): Score Four "solved" trusted without checking** (295–296). Fix: the guest sends the expression; the host
  validates it with `score_four` rules.
- **B77 (L): Blind Man's Bluff short all-in raise recorded wrongly** (534, `_clamp_int` with min > max). Fix: treat as
  an all-in call or raise of the actual amount.
- **B78 (L): a $0 roulette bet becomes $1** (683). Fix: reject amounts below the minimum.
- **B79 (M): XP for returned chips** (`mp_profile.py:219-220` counts single-winner pots that are only the player's own
  uncalled excess). Fix: ignore pots where the winner is the only contributor.
- **B80 (M): fixes missing in multiplayer Hold'em** (short all-in blind, raise guard, quick-chat reset). Resolved by
  the merge and B86.
- **B81 (L): late-join takeover keeps stale NPC data** (`room_table.py:57`). Fix: build the seat from current
  `self.npcs`.
- **B82 (L-M): Dead Man's Hand PvP trusts guest shots** (`dead_mans_hand_pvp.py` 714–719, 793–798; non-numeric data
  crashes `_shot_hits`). Fix: validate types and ranges; ignore invalid shots.
- **B83 (L): no result on a PvP disconnect** (773–782). Fix: award the win to the remaining player and show a result.
- **B84 (L-M): per-frame work in `room_view.py`** (SysFont per button at 24; smoothscale and shadow per card at
  96–99; alpha surface per `panel()` at 284), and the Hold'em host rebuilds its own view every frame
  (`room_session.py:77`). Fix: caches; rebuild the host view only when the revision changes.
- **W1 (multiplayer part):** `multiplayer/mp_options.py` `display()` and the inherited `SOLITAIRE_MP_WINDOW` size
  switch to `solitaireplus/app/window.py` (DPI awareness, size rules, centring, letterboxed fullscreen). Repeat the
  W1 manual check for the multiplayer window.
- **B85 (M): `standalone_view.py:45` passes `show_utility_buttons`,** which the root UI doesn't accept. Resolved by
  the merge (one UI with the option) and by removing the unreachable Practice table.

---

## 9. Designer decisions (already made; don't re-ask)

| Item | Decision |
|---|---|
| Multiplayer duplicates | Merge (Phase 11). |
| Debug | Keep the F10 menu public. Move the Solitaire instant-win into it. Delete every other hotkey or button outside it. |
| B23 NPC decline | Intended; no change. Report young vs veteran numbers. |
| B32 horse odds | Leave alone for now. |
| B38 + B86 | Fix odd chips everywhere; align all poker variants (show the audit table first). |
| B46, B47 Crazy Eights | Accepted. |
| B68 late joiners | Accepted: humans replace busted NPCs. |
| Not in scope | PNG recompression; merging the two save folders; user docs (`RELEASING`, `INSTALLING`, `CODE_SIGNING`, `AGENTS.md`). |

---

## 10. Verification, hand-back, and the return checklist

### 10.1 After every commit
- `tools\run_tests.py` prints PASSED.
- Move commits: `tools\screen_harness.py compare` and `tools\replay.py compare` print IDENTICAL.
- Fix commits: only the scenes and checkpoints you list differ, and each bug has a test that failed before the fix.

### 10.2 After Phases 1, 2, 7, 11 and 12: the packaged check
1. `build_release.ps1 -SkipTests` (`-Installer` in Phase 12).
2. All three packaged self-tests pass.
3. The packaged game runs for 10 seconds with an empty newest `game-*.log`.
4. Phase 11 also needs the local two-player test (§7, Phase 11).

### 10.3 Hand-back report (when Phase 12 is committed)
Give Dan one message containing:
1. **Commits:** `git log --oneline 154b890..HEAD`.
2. **Tests:** counts per suite, and the final contents of `tests/KNOWN_FAILURES.txt` with a reason for each line.
3. **Behaviour changes:** every intended screenshot or replay change, by phase.
4. **Bugs:** a table of W1, B1–B86 and D1, each "fixed (test name)", "no change (designer)" or "not reproducible
   (why)". For W1, include the window rectangles measured in the manual check.
5. **For the designer:** the B86 audit table as approved, the B23 numbers, and any new findings you didn't fix.
6. **Layout:** a short tour of the new layout (one line per folder).

### 10.4 Return checklist (the original session will verify these)
- [ ] `main.py` is the small entry point; no file in `solitaireplus/` is over about 3,000 lines.
- [ ] `solitaireplus/legacy.py`, `tools/refactor/` and `requirements-dev.txt` are gone.
- [ ] No `global` statements and no `globals()` calls anywhere in `solitaireplus/` or `main.py`. Shared state goes
  through `solitaireplus/app/state.py`.
- [ ] No duplicate engine modules in `multiplayer/`.
- [ ] No `Path(__file__)` asset lookups outside `app/paths.py`.
- [ ] `grep` finds none of the deleted hotkeys (K_F6/K_F7/K_F8 in gameplay handlers, the Hold'em Space/B keys,
  `debug_xp_rect`).
- [ ] Packaged build, self-tests, launch, and the local multiplayer test all pass.
- [ ] On Dan's PC, the game window and the multiplayer window open fully on-screen with the title bar visible. They
  stay that way after F11 in and out of fullscreen and after every Options window size (W1).
- [ ] Every bug ID is accounted for in the hand-back table.

---

## 11. Pitfalls already learned the hard way

- **Defender** flags an exe that copies itself to `%TEMP%` and runs the copy. Never do it.
- **Loose multiplayer files** only see modules the game exe imports. After moving or merging, the packaged multiplayer
  self-test is the only thing that catches a missing module.
- **Server-only modules** must stay out of the player install, in both `MP_EXCLUDED` and `SELFTEST_SKIP`.
- **Asyncio streams:** after writing a handshake, `await writer.drain()`. WebSocket adapters only send on drain.
- **Some tests depend on pygame being initialised.** The runner calls `pygame.init()` per file. Don't remove that.
- **Timing-based tests** are often flaky. Measure flakiness (20+ runs) before and after a change, and compare with
  the unmodified code in a `git worktree` before blaming yourself.
- **Escaping in shell heredocs** has broken edits several times. Prefer the file-editing tools, or write Python
  scripts to a file and run them.
- **`profile`** clashes with the standard-library module name (renamed to `saves.py` in Phase 1).
- **Windows line endings:** git converts LF to CRLF. When hashing source files (`tools/make_manifest.py`), CRLF is
  normalised. Keep it that way.
- **Never add tests to `tests/KNOWN_FAILURES.txt` to get green.** Fix the cause.
