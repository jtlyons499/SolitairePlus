# Debug menu and debug key changes (restructure sprint, November 2026)

For the original maintainer: what changed in the F10 debug menu, the debug keys and the debug tools during the
restructure sprint (Phases 2-12). The F10 debug menu is still public, and every button it had still works. Finding
numbers (N10 and so on) point to [PHASE_REPORTS.md](PHASE_REPORTS.md).

## Removed debug keys and buttons (D1)
- **Customize screen:** the "DEBUG +100 XP" button is gone (Phase 3).
- **Solitaire table:** F7 and F8 are gone (Phase 4). F8's instant win is now a button in the F10 menu (below).
- **Texas Hold'em table:** F7, Space and B are gone, and the unused `debug_setup_holdem_heads_up` was deleted
  (Phase 7).
- **Score Four table:** F6 ("TEMP DEBUG: complete training", which finished the training session at once) is gone
  (Phase 8).
- `tests/debug/test_no_stray_debug_hotkeys.py` keeps them gone. It also checks that F10 (debug menu) and F11
  (fullscreen) are the only function keys the game binds. Since Phase 12 it scans every `holdem_ui*.py` module and
  fails if a new one is not on its list.

## New in the F10 menu
- **"Win this Solitaire round"** (SOLITAIRE CHALLENGES column, one empty row below "All or Nothing"). This replaces
  F8. It works only when F10 was opened from the Solitaire table and the table's "Restart this hand?" prompt is not
  open. It then goes back to the table and wins the round with the normal victory animation and recap. Anywhere else
  it is greyed out and does nothing (Phase 10).

## Changed behaviour
- **F10 is ignored while typing** in a text field: the Profile screen's name, country, age, hometown and bio
  fields, and the Hold'em and Five-Card Draw manual bet boxes. The Cryptid card search box has no focus state, so
  F10 still opens the menu there (Phase 10).
- **Close works like F10:** both leave through `close_debug_menu()`. Closing back into Dead Man's Hand now grabs and
  hides the mouse again, so mouse look works; before, only F10 did that (Phase 10, B59).
- **Free Play sandbox:** the menu ends a running Free Play sandbox before every game, night or career launch, so the
  Free Play $5,000 no longer ends up in the career (Phase 5, B21).
- **Debug mode:** a launcher restores the previous mode when its night ends, on the career jumps and on Back from
  the poker table picker. Every debug night is marked `debug: True`, so ending it never uses a career day (Phase 5,
  B22).
- **Hover:** the button under a resting mouse stays highlighted after F10 or arrow keys (Phase 2, B15).
- **Side effect when testing through the menu:** opening F10 mid-game in Suit Snake and closing it no longer makes
  the snake race across the board to catch up (Phase 9, B50).
- **Packaged game:** the packaged game crashed at start, because `app/loop.py` opens screens by module name and
  PyInstaller left some out. One of them was the F10 menu's poker table picker
  (`solitaireplus.debug.poker_select_screen`). The spec now packs every `solitaireplus` module (Phase 7 packaged
  fix, guarded by `tests/packaging/test_packaged_game_modules.py`). The picker itself did not change.
- **No visible change:** `debug_open_blackjack()` (the menu's Blackjack launcher) no longer resets
  `blackjack_bet_dropdown_open`, a flag nothing in the game ever read (Phase 12).

## Where the code lives now
- Menu screen: `solitaireplus/debug/menu_screen.py`. Layout and labels: `solitaireplus/debug/menu.py`.
- What the buttons do (all `debug_open_*` launchers, debug nights, level, rating, achievement and Career calendar
  buttons, `debug_end_free_play_sandbox`, `close_debug_menu`): `solitaireplus/debug/actions.py`. The launchers start
  each game through that game's own screen module. Since Phase 12 (when `legacy.py` was deleted) they reach the
  helpers they used to find there through those helpers' new modules, for example `profile/leveling.py` for the
  achievement buttons and `games/solitaire/table.py` for the Solitaire engine. Same functions, same order.
- Poker table picker: `solitaireplus/debug/poker_select_screen.py` and `poker_select.py`. Debug game mode:
  `solitaireplus/debug/game_mode.py`.
- The F10 key itself: `solitaireplus/app/loop.py`.
- Tests for the menu: `tests/debug/` (for example `test_debug_menu_solitaire_win.py`,
  `test_debug_menu_close_recaptures_mouse.py`, `test_f10_ignored_while_typing.py`,
  `test_debug_menu_ends_free_play_sandbox.py`, `test_debug_night_mode.py`).

## Developer tools (not in the game)
- `README.md` no longer says F9 wins a Solitaire round. It now says to press F10 at the Solitaire table and click
  "Win this Solitaire round" (Phase 12, N60).
- The replay journey `03_solitaire` (`tools/harness/journeys.py`) wins through that button, as the brief asked, no
  longer through a copy of the old F8 code (Phase 12, N59).
- `Game.debug_auto_solve_state` (Solitaire) moved unchanged to `games/solitaire/auto_solve.py`. It has had no caller
  since the Solitaire F7 key was removed (N63).
- `verify_solitaire_state.py` (a read-only installation check, not part of the game) moved from the repository root
  to `tools/verify_solitaire_state.py`. Run it as `python tools/verify_solitaire_state.py`.
- `tools/window_check.py` has a `--multiplayer` flag that runs the same window checks on the Multiplayer window
  (Phase 11). Its printout now says "start-up/cursors" for the check that the Multiplayer window does not load the
  single-player start-up.
- `docs/TESTING.md` has a "Local two-player test" recipe (relay on 127.0.0.1, packaged `SolitaireNet.exe`, two
  windows) (Phase 11).
- The multiplayer Practice table and LAN play were removed (Phase 11). No menu entry pointed to them.

## Open questions (debug-only findings, not fixed)
- **N10:** before a profile is picked, an F10 debug career started from the start-up profile screen auto-saves
  into slot 1.
- **N20:** debug launchers that don't switch to debug mode (Casual Cards, Casino, Poker Night and others) still
  write career news; only the day advance is skipped. Should debug nights be fully sandboxed?
- **N31:** after leaving the horse races mid-race through F10 and coming back, the race continues without its cue.
