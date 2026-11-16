# Solitaire+ restructure sprint: hand-back (brief §10.3)

Dan's decisions before the sprint (2026-11-15): run unattended, commit each phase locally (never pushed), no stop
between phases; B86 does not wait for the audit table; defaults for open choices are listed in section 5(c).
Details for every phase are in `docs/dev/PHASE_REPORTS.md`.

## 1. Commits

`git log --oneline 154b890..HEAD` (newest first; the top line is the commit that adds this file):

```text
<Phase 12 hash> Phase 12: cleanup
ad05ea4 Phase 11 (fix): per-frame fonts in the Dead Man's Hand duel and the Multiplayer screens
2448d18 Phase 7 (fix): B44 per-frame fonts in Score Four, career activities and Head-to-Head
e328c11 Phase 11 (fix): B67-B85, W1 multiplayer
6da9961 Phase 11 (move): merge multiplayer copies into solitaireplus, remove LAN and Practice
73dc94c Phase 7 (fix): packaged game ships every solitaireplus module
2735933 Phase 10 (fix): cryptid, Dead Man's Hand, debug
a710d56 Phase 10 (move): cryptid, Dead Man's Hand and debug menu screens out of legacy.py
54a29ef Phase 9 (fix): arcade
4106fd5 Phase 9 (move): arcade screens out of legacy.py
1c49f73 Phase 8 (fix): casual cards
d3aa68c Phase 8 (move): casual card screens out of legacy.py
707be96 Phase 7 (fix): B86 poker rules alignment (B36-B39, B42)
7195fb3 Phase 7 (fix): poker
a2f9687 Phase 7 (move): poker screens out of legacy.py
ab7f1cc Phase 6 (fix): casino
3103f2e Phase 6 (move): casino screens out of legacy.py
6ed72fe Phase 5 (fix): career
d8ed4d0 Phase 5 (move): career screens and career engine out of legacy.py
3a1784d Phase 4 (fix): Solitaire
0df2c68 Phase 4 (move): Solitaire table and Head-to-Head out of legacy.py
9890c12 Phase 3 (fix): menus and profile
1ddab50 Phase 3 (move): menus and profile screens out of legacy.py
2c62abd Phase 2 (fix): W1 windowing, B15, B16, B17, B62, B63, B64, B65
4bf1db8 Phase 2 (move): engine out of main.py (state, loop, legacy, window, fonts, sounds, assets, ui)
d924025 Phase 1 (move): package skeleton, all modules into solitaireplus/, paths helper
bba00a0 Phase 0: safety net (screenshot harness, replays, code locator)
f65f6cf Add restructure and bug-fix brief for the next session
```

Nothing is pushed. Every commit was checked on its own: full tests, then both compares against its parent.

Note: two commits carry an earlier phase's name because they were found late: "Phase 7 (fix): packaged game ships
every solitaireplus module" comes after Phase 10, and "Phase 7 (fix): B44 per-frame fonts in Score Four, career
activities and Head-to-Head" comes after the Phase 11 fix.

## 2. Tests

Final run, `tools
un_tests.py` on the Phase 12 tree: **PASSED**.

| Suite | Files | Tests | Quarantined |
|---|---|---|---|
| game (`tests/<area>/`) | 146 | 1,246 | 3 (still failing, listed below) |
| multiplayer (`multiplayer/tests/`) | 18 | 148 | 0 |

Final `tests/KNOWN_FAILURES.txt` (3 lines, all game suite, all `test_npc_development`; the multiplayer list is empty):

| Quarantined test | Reason |
|---|---|
| `game:test_npc_development.DevelopmentTests.test_decline_is_gentle_capped_and_does_not_retroactively_reset_veterans` | The NPC aging and rating rebalance changed the decline numbers; the expected numbers predate it. Designer decision: stays quarantined until the designer confirms the intended values. |
| `game:test_npc_development.ProspectTests.test_majority_are_club_strength_and_prodigies_are_rare` | The rebalance changed the prospect bands. Same designer decision. |
| `game:test_npc_development.ProspectTests.test_rare_prodigy_reaches_2500_then_continues_towards_top_five` | The rebalance changed the prodigy curve. Same designer decision. |

All three already failed on `main` on 2026-11-14. Every other line was fixed, or went with its deleted test,
during the sprint: three repaired in Phase 0; the multiplayer lines in Phase 11 (fixed, or deleted with LAN and
Practice) and Phase 12; the three `/workspace/scratch` image tests and the two Dead Man's Hand source checks in
Phase 12. The B23 numbers in section 5(b) may help decide the expected values.

## 3. Behaviour changes by phase

The safety net: `tools/screen_harness.py compare` (63 scenes in Phase 0, 64 from the Phase 2 fix on) and
`tools/replay.py compare` (18 journeys), each against the commit before. **Every move commit was IDENTICAL**
(Phases 1 to 11, all scenes and all journeys). Every checkpoint value (cash, XP, level, rating, day, fans) was
identical in every commit except the one Stud checkpoint under Phase 7 B86. Scene names with `__` are extra shots
of one scene.

### Changes the harness shows (all intended)

| Phase (commit) | Scenes that differ | Journey checkpoints that differ | Why |
|---|---|---|---|
| 0, 1, 2 move | none | none | |
| 2 fix | `menu_hover_after_key__options` (scene added with B15), `debug_menu`, `arcade_battle_bosses` | `15_debug_menu_quit`, `13_arcade_battle_bosses` (screenshots) | B15: the button under a resting mouse stays highlighted after a key press, F10 or arrow keys. |
| 2 fix | `menu_options`, `menu_options_update_available` | `02_options` (screenshot) | W1: 1920x1080 and 2560x1440 greyed out ("Too large for this screen."); at 1600x900 SDL now scales the picture that the old code scaled by hand. |
| 3 fix | `menu_customize` (+`__felts`, `__cursors`) | none | D1: the "DEBUG +100 XP" button (its 180x45 area) is gone. |
| 3 fix | `profile_select`, `profile_select_delete_confirm`, `profile_select_damaged` (+`__notice`) | `01_create_profile` (the profile-select screenshot) | B9: "Level N" / "Can't open" moved left of the Delete button. |
| 4 fix, 5 fix, 6 fix, 7 fix (poker) | none | none | These fixes change no static screen and no scripted journey. |
| 7 fix (B86) | `poker_blind_mans_bluff__start` | none | P7: shorter hint "Everyone else can see your card. Read their betting." |
| 7 fix (B86) | `poker_blind_mans_bluff__showdown` | none | P7: the stake line reads "Ante $10" without "Open $0-$0"; van Dijk's "+$40" payout chips now show (the shared who-won rule drives the payout animation). |
| 7 fix (B86) | none | `11_seven_card_stud` `cp_01_hand_complete` | NEW-2: the pot after the hand reads $82 with payout chips instead of $0; the two bogus "Side pot N: You wins." lines are gone and the log shows both showdown lines. Checkpoint `career_fans` 3 → 24 (fans are paid on the hand's net). |
| 7 packaged fix, 8 fix | none | none | Phase 8: no scene or journey draws from an empty Crazy Eights pile, asks for a Score Four hint, presses F6 or opens the Crazy Eights help pages. |
| 9 fix | `arcade_king_pong` | `13_arcade_king_pong` `cp_01_after_five_seconds` (screenshot; score 0-0 instead of 0-1 at 5 s) | B49 real frame time and B54 sub-pixel motion: the ball and the rival paddle are elsewhere. No point is scored in the window, so B53 does not show. |
| 9 fix | `arcade_ace_invaders` | `13_arcade_ace_invaders` `cp_01_after_five_seconds` (screenshot) | B54, B49: the CASUAL formation is about 12 px further left (0.9 px per frame was rounded up to 1); one more kill in the scene (SCORE/HIGH 30 instead of 20); bullets, ship and two shield blocks moved. Score and lives in the journey are the same. |
| 9 fix | none | `13_arcade_battle_bosses` `cp_01_after_five_seconds` (screenshot) | B49: the ball and the three rival shields are elsewhere; the player's shield is unchanged. |
| 10 fix | `debug_menu` (12,472 px) | `15_debug_menu_quit` `cp_00_debug_menu` (screenshot) | D1: the new greyed-out "Win this Solitaire round" button in the SOLITAIRE CHALLENGES column (the menu was opened from the main menu). |
| 11 move, 11 fix | none | none | The harness has no multiplayer scenes. Single-player was IDENTICAL. |
| 7 late fix (B44), 11 late fix (fonts) | none | none | Fonts now come from the cache; same pixels. The Multiplayer screens were checked with a separate pixel hash (same before and after). |
| 12 | none | none (journey `03_solitaire` now wins through the F10 button: one new checkpoint `debug_menu_from_table`, the last two 12 frames later, same values and screenshots) | Cleanup only. Every Phase 12 part, and the squashed commit, was IDENTICAL 64/64 and 18/18 (the harness runs the working tree's journey scripts on both sides). |

### Changes the harness cannot see, called out in the reports

- **Phase 2 fix:**
  - W1 on a real screen: DPI aware, a default size that fits the work area, centred, letterboxed desktop
    fullscreen on F11, oversize sizes greyed out, a saved oversize size replaced by the default.
  - The large software cursor no longer switches on at 125-200% scaling (sizes compared at 100%).
  - B17: "nearly opaque" menu backgrounds are flattened once (at most a few colour levels from the old picture,
    without the faint ghosting of the previous frame); the default background is pixel-identical.
  - B62 music no longer skips every other track.
- **Phase 3 fix:** B14 the splash keeps the saved music mode; B12/B13 new profile messages; B11 no avatar crash;
  B7 level-ups kept.
- **Phase 4 fix:** B1 auto-solve; B2 Restart after a race; B3 and B8 race clocks; B4 the invisible Career hotspot
  is gone; B5 Recap "No" in career goes to the hub; B6; D1 Solitaire F7/F8 removed.
- **Phase 5 fix:** B18 roster sync; B19 one job story a day; B20 bad activity data skipped; B21 sandbox cash never
  saved; B22 debug mode restored; B12 hub recovery-file message.
- **Phase 6 fix:** roulette re-spin pays, stake taken only when the spin starts, result cleared on a bet change,
  chip label "1.5k"; blackjack never shows a duplicate card, naturals pay half-up ($5 wins $8), Low Roller needs a
  Stand; horse-race music restored; Faro gives no free rating.
- **Phase 7 fix:** B35 Hold'em session timer and table-clear bonus; B40 Stud bring-in; B41 Draw reshuffles the
  muck; B43 recap "Eligible:" line; D1 Hold'em F7, Space and B removed.
- **Phase 7 B86:** every table rule change in `docs/POKER_RULE_CHANGES.md`. The main ones: uncalled chips are
  returned, not won (also on fold wins); no bet nobody can answer; odd chips from the first winner left of the
  dealer; Hold'em NPCs keep betting after you fold (about 30 s at slow speed with 4 NPCs); the Five-O NPC can raise;
  Five-O and Blind Man's Bluff NPCs take the table-speed thinking time; Blind Man's Bluff short stacks play all-in
  and the session ends only at $0; career fans paid on the hand's net; GAME LOG lines wrap; every NPC gets the same
  inputs (cash on hand, grudges, career skill, reads, learning). Seeded Five-O and BMB runs recorded before B86
  deal differently after the first NPC chat.
- **Phase 7 packaged fix:** the packaged game starts again. Since the Phase 3 move it crashed at start
  (`No module named 'solitaireplus.menus.splash'`); only the packaged check could see it.
- **Phase 8 fix:** Crazy Eights passes and the blocked-game rule (B46), the new Pass button at (942, 545, 170, 48)
  and the hint "Play the card you drew, or pass." (B47), two How to Play pages changed and one added; Score Four
  "No hint" instead of a crash (B48); F6 removed.
- **Phase 9 fix:** B53 King Pong serves to the side that lost the point; B56 Enter no longer forfeits; B57 no
  "NEW HIGH SCORE!" on a first game; B50 Suit Snake no longer races after a pause; B55 wave-break shots don't count.
- **Phase 10 fix:** B59 Close recaptures the Dead Man's Hand mouse; B60 Cryptid deck message; B61 reachable
  spawns (authored levels unchanged); F10 ignored while typing.
- **Phase 11 move (multiplayer):** LAN play and the offline Practice table are gone. Room Hold'em runs on the
  single-player engine with the B86 rules: a fold win shows a $125 main pot plus "Returned (uncalled): Uncalled
  $100 returned to Guest 3" (was a $225 pot), with a new Payout History footnote; uncalled and folded chips no
  longer make extra side pots; nobody can raise when everyone else is all-in; a seat whose blind puts it all in
  plays the hand; no empty "You are dealt ." line for a busted host. Room NPCs use the shared AI (a high-tenacity
  short stack folds 38.4% instead of 66.2% in the measured spot). Layered portraits gain the `outline.png` layer.
- **Phase 11 fix (rooms):** local countdowns ("Starting next hand…" for 2 s at the end), late joiners seated
  (Hold'em: a busted NPC seat with a buy-in first; party games at the next hand, spin or lobby), takeover seats
  start with fresh NPC reads, no XP for returned chips or own-chip pots, the version-mismatch notice (protocol
  stamp 3), a disconnected BMB seat checks or folds, BMB "Table finished", room BMB uses the shared pot, raise and
  winner rules, Score Four solves checked and retried, Roulette bets below $1 refused. DMH duels: forfeit /
  CONNECTION LOST result screen, invalid guest data ignored, mouse-look scales with the window. The Multiplayer
  window follows the single-player window rules.
- **Phase 11 fix (single-player):** on a work area smaller than about 1366x800 (for example a 1366x768 laptop) the
  window now really gets its smaller default size (1088x612) and keeps a smaller dragged size; before, SDL held it
  at 1366x768 and `present()` retried every frame (`_allow_small_window()`, a W1 fix).
- **Phase 12:** start-up keeps the newest 10 `game-*.log` files and deletes older ones (#15; files only, locked
  files skipped silently). README now points to the F10 "Win this Solitaire round" button. Tests no longer write
  into the real `%LOCALAPPDATA%`. Nothing else a player sees.

## 4. Bugs

88 IDs: **86 fixed**, **2 no change (designer)**, **0 not reproducible**. Tests are cited by file or test name; since
Phase 12 the game tests live in `tests/<area>/` folders.

| ID | Status | What changed |
|---|---|---|
| W1 | fixed (test_window incl. test_small_window_sizes_really_apply and test_open_window_sets_caption_and_clamps_size; test_mp_window; `tools/window_check.py`) | Phase 2: DPI-aware, SDL-scaled letterboxed window; default = largest 16:9 within 90% of the work area (1024x576 to 2560x1440); centred; oversize Options sizes greyed out; a saved oversize size clamped. Phase 11: small screens really get the smaller size; the Multiplayer window uses the same `app/window.py`. Rectangles below. |
| B1 | fixed (test_solitaire_auto_solve) | Auto-solve waits for the stock flip animation, and stops after a stock pass that plays no card. |
| B2 | fixed (test_solitaire_race_restart) | The Restart snapshot is taken after the race layout is set. |
| B3 | fixed (test_head_to_head_countdown_clock) | The player's round clock starts when the 3-2-1 countdown ends. |
| B4 | fixed (test_career_hub_hotspot) | The invisible Career Solitaire hotspot, its handler and both rect definitions are gone. |
| B5 | fixed (test_recap_no_career) | Career Recap "No" goes to the Career hub (after level-ups) without dealing a paid game. |
| B6 | fixed (test_career_abandon_round, test_difficulty_back_clears_career_activity) | Abandoning a career round (pause menu or difficulty Back) clears the pending activity and challenge. |
| B7 | fixed (test_recap_level_up_queue) | Recap Yes/No add to the level-up queue instead of replacing it. |
| B8 | fixed (test_head_to_head_pause) | The race clocks (countdown, timer, opponent, player clock) stand still on any screen except the table. |
| B9 | fixed (test_profile_select_layout) | Slot "Level N" / "Can't open" text ends 16 px left of the Delete button. |
| B10 | fixed (test_profile_slot_cache) | Profile select caches slot data; refreshed on enter, save, delete and create. |
| B11 | fixed (test_avatar_cycle_option) | Avatar arrows, selector label and avatar drawing cope with parts missing from the bank. |
| B12 | fixed (test_profile_save_failed_message, test_career_hub_save_recovery) | Profile screen and Career hub show the recovery-file message; disk errors are reported, not raised. (N9: not seen while creating a profile.) |
| B13 | fixed (test_profile_delete_in_use) | The loaded profile can't be deleted; a message says why. |
| B14 | fixed (test_splash_music_mode) | Leaving the splash keeps the saved music mode; Ambient only when nothing is saved. |
| B15 | fixed (test_loop_mouse_and_screen_hooks.DrawingUsesTheFramesMousePosition; scene menu_hover_after_key) | Drawing uses the frame's mouse position, events their own; no hover in letterbox bars. |
| B16 | fixed (test_loop_mouse_and_screen_hooks.ScreenEnterAndLeaveHooks) | Screens get enter/leave hooks; Options resets both slider drags. |
| B17 | fixed (test_frame_caches, test_frame_font_sites) | Font cache, scaled-image caches for buttons and plaques, pre-scaled menu drift. |
| B18 | fixed (test_career_roster_sync) | The NPC roster syncs only after the date or roster changed. |
| B19 | fixed (test_career_job_news) | Job news only on a real job change, one story per career day. |
| B20 | fixed (test_career_activity_bad_data, test_career_activities) | Bad activity data is skipped or replaced; it never crashes, pays twice or replays a day. |
| B21 | fixed (test_debug_menu_ends_free_play_sandbox) | F10 launches end a Free Play sandbox; saves during a sandbox write the real career values. |
| B22 | fixed (test_debug_night_mode) | Debug launchers restore the earlier game mode; debug nights are marked and never use a career day. |
| B23 | no change (designer) | NPC monthly decline kept. Pinned by test_npc_monthly_rating_pins (also the real path, `npc_development.advance_npc_development`). Numbers in 5(b). |
| B24 | fixed (test_roulette_respin, test_career_ratings) | `start_spin` resets `payout_claimed`, so a re-spin pays. |
| B25 | fixed (test_roulette_spin_cash) | The stake is taken only after `start_spin()` succeeds. |
| B26 | fixed (test_roulette_bet_change_clears_result) | Changing, removing or clearing chips after a round clears the old result. |
| B27 | fixed (test_blackjack_deck) | Reshuffle before a round below 15 cards; never rebuild mid-hand. |
| B28 | fixed (test_blackjack_payout_rounding) | A natural pays bet + (bet*3+1)//2 ($1/$3/$5 win $2/$5/$8). |
| B29 | fixed (test_blackjack_single_hand_bust) | An unsplit bust is recorded as "dealer", not "split". |
| B30 | fixed (test_blackjack_low_stand_achievement) | "Low Roller" needs a real Stand. |
| B31 | fixed (test_horse_race_music_ducking) | Base volume captured only when not ducked; restored on every exit. |
| B32 | no change (designer) | Horse-race place and show odds left as they are. No test pins them. |
| B33 | fixed (test_faro_risk_free_rating) | Faro counts only stakes a deal settled. |
| B34 | fixed (test_blackjack_fonts, test_casino_frame_caches) | Blackjack labels use the font cache; background and logo scaled once. |
| B35 | fixed (test_holdem_session_end_timer, test_holdem_table_clear_bonus) | Hold'em session start resets the end timer and the table-clear bonus flag. |
| B36 | fixed (test_poker_betting_rules.NobodyToRespondTests, test_poker_chip_conservation `test_<variant>_never_wagers_with_nobody_to_respond`) | Shared `core.can_raise`: no bet or raise nobody can answer, for the human and NPCs. |
| B37 | fixed (test_poker_pots.BuildPotsTests, test_poker_pots.VariantPotTests, test_poker_chip_conservation) | A pot layer no live seat paid into goes back to whoever paid it. |
| B38 | fixed (test_poker_pots.OddChipTests, test_odd_chips_go_to_the_first_tied_winner_left_of_the_dealer) | Odd chips go one at a time from the first tied winner left of the dealer, in every variant and in rooms. |
| B39 | fixed (test_poker_betting_rules.OpeningBetTests, test_poker_hand_flow.BetToMatchTests, LoneSeatAfterFoldsTests) | After a short all-in forced bet, a lone seat able to act only matches what was posted. |
| B40 | fixed (test_stud_bring_in) | The Stud bring-in skips seats with no chips. Designer question in 5(c). |
| B41 | fixed (test_five_card_draw_deck_exhaustion) | Draw reshuffles the muck when the deck runs out; otherwise the log says so. |
| B42 | fixed (test_blind_mans_bluff_counts_wins_ties_and_losses_by_pot, test_a_layer_no_live_seat_paid_into_goes_back_exactly) | Blind Man's Bluff uses `core.build_pots` (exact refunds), `award_pots` and `core.hand_outcome` (a tie only when the human shared a pot and won none alone). |
| B43 | fixed (test_poker_recap_single_winner) | A single-winner pot's recap lists its eligible player. |
| B44 | fixed (test_poker_ui_fonts, test_poker_ui_font_cache, test_frame_font_sites) | Poker UIs, recap and Five-O use the font cache (Phase 7); Score Four, career activities, Head-to-Head, the restart prompt and the Ace Invaders fallback glyph too (late Phase 7 fix). |
| B45 | fixed (test_b45_duplicates) | One definition each of the Hold'em sound helpers, STATE_CAREER_NEWS and the duplicated assignments. |
| B46 | fixed (test_crazy_eights_blocked_game) | A player who can't play or draw passes; blocked only after everyone passes in a row. |
| B47 | fixed (test_crazy_eights_draw_rule) | After a draw only the drawn card may be played, or the player passes (new Pass button). |
| B48 | fixed (test_score_four_hint_limit) | The hint resets to the original cards once; an unsolvable puzzle gets "No hint". |
| B49 | fixed (test_arcade_frame_time) | The machines move by the real frame time (`state.frame_dt`), capped at 1/20 s. |
| B50 | fixed (test_suit_snake_pause_catchup) | After a gap of more than 2 steps, Suit Snake's step clock jumps to now. |
| B51 | fixed (test_suit_snake_font_cache) | Suit Snake card tokens use the font cache. |
| B52 | fixed (test_ace_invaders_background_cache) | Ace Invaders scales its background once per size. |
| B53 | fixed (test_king_pong_serve) | King Pong serves toward the side that gave up the point. |
| B54 | fixed (test_arcade_subpixel_motion) | King Pong and Ace Invaders keep float positions (`motion.move_rect`). |
| B55 | fixed (test_ace_invaders_wave_break_accuracy) | Shots during the wave break don't count toward accuracy (sprint default). |
| B56 | fixed (test_king_pong_enter_key) | Enter leaves King Pong only after the match ends. |
| B57 | fixed (test_suit_snake_high_score) | "New high score" only when a previous score above 0 is beaten. |
| B58 | fixed (test_battle_bosses_font_cache) | Battle Bosses' fallback ball and fort letters use the font cache. |
| B59 | fixed (test_debug_menu_close_recaptures_mouse) | F10 and Close share `close_debug_menu()`; Close into Dead Man's Hand recaptures the mouse. |
| B60 | fixed (test_cryptid_opener) | A deck with fewer than 2 creatures shows a message instead of crashing. |
| B61 | fixed (test_dead_mans_hand_spawn_reachability) | Enemies spawn only in floor cells the player can reach; authored levels unchanged. |
| B62 | fixed (test_music_playlist) | The playlist advances only on the end-of-music event. |
| B63 | fixed (test_profile_null_sections) | Non-dict save sections load as empty; `career.arcade` normalised on load. |
| B64 | fixed (test_npc_runtime_ratings) | A missing `ratings["overall"]` is derived from the category ratings. |
| B65 | fixed (test_rating_format) | RatingPoints formats "f" specs as whole points; "d" specs unchanged. |
| B66 | fixed (test_roulette_chip_label, test_casino_frame_caches) | Chip labels show "1.5k"; from $10k without the decimal; chip font built once. |
| B67 | fixed (test_clock_going_backwards_rearms_timer; SixRelayTests.test_six_clients_and_late_join un-quarantined) | One fake clock in the six-seat test; the room re-arms its timers when the clock jumps back more than 60 s. |
| B68 | fixed (test_late_join_takes_busted_npc_seat_with_buy_in; test_late_join_no_mid_hand_takeover un-quarantined) | A late joiner takes a busted NPC seat first with the starting stack and a notice; otherwise a funded NPC seat as before. |
| B69 | fixed (test_unseatable_waiter_does_not_bump_revision) | The revision is bumped only when someone left a seat or was seated. |
| B70 | fixed (test_countdown_does_not_bump_revision, test_client_countdown_from_timestamp, test_malformed_countdown_is_ignored, test_roulette_countdown_keeps_revision, test_countdown_uses_local_timestamp, test_countdown_runs_on_the_local_clock, test_draw_shows_the_local_countdown, test_malformed_countdown_falls_back_to_seconds_left) | No per-second revision bump (Hold'em, Roulette); the countdown is sent as a "starts at" time and counted on each screen's clock. |
| B71 | fixed (test_bluff_late_joiner_seated_at_next_hand, test_roulette_late_joiner_seated_at_next_spin, test_score_four_late_joiner_seated_on_return_to_lobby, test_waiter_takes_ghost_then_npc_seat_and_is_queued_once, test_lobby_waiter_takes_a_seat_freed_in_the_lobby, test_broke_seat_buys_in_for_the_joiner) | Party late joiners sit down at the next BMB hand, the next Roulette spin, or the Score Four lobby; never queued twice. |
| B72 | fixed (test_disconnected_actor_checks_after_a_pause, test_disconnected_actor_folds_to_a_bet, test_disconnected_seat_acts_when_its_turn_comes) | A disconnected BMB seat checks, or folds when it owes chips, after 600 ms (sprint default). |
| B73 | fixed (test_bluff_finishes_when_fewer_than_two_can_ante, test_late_joiner_deals_a_finished_bluff_table_back_in, test_full_finished_bluff_table_keeps_its_revision, test_late_joiner_restarts_a_finished_roulette_table) | Fewer than 2 seats can ante → "Table finished"; a newcomer's buy-in restarts the table. |
| B74 | fixed (test_score_four_return_lobby_frees_ghost_seats) | Score Four frees the seats of players who left when it returns to the lobby. |
| B75 | fixed (test_solve_is_retried_until_the_room_takes_it, test_a_new_room_on_the_same_round_gets_its_own_cards) | A solve is re-sent until the room takes it; the board is kept per room. |
| B76 | fixed (test_score_four_host_checks_the_guest_solve, test_sent_steps_pass_the_host_check, test_steps_follow_undo_reset_and_a_new_round, test_score_four_check_solution) | The host checks the guest's steps with `score_four.check_solution`. |
| B77 | fixed (test_short_all_in_raise_is_recorded_as_the_real_amount, test_npc_short_stack_bet_is_its_stack) | A short-stack raise is clamped to what the stack has; a target that doesn't beat the bet is a call. |
| B78 | fixed (test_roulette_rejects_bets_below_the_minimum) | A room Roulette bet must be a whole number of at least $1. |
| B79 | fixed (test_returned_chips_give_no_xp, test_dead_money_layer_still_gives_xp, test_room_showdown_split_of_own_chips_gives_no_xp, test_holdem_pot_contributors) | Rooms record each pot's contributors; no XP for a pot paid only by its winners. |
| B80 | fixed (test_room_engine, test_guest_cannot_raise_when_no_one_can_respond, test_can_raise_agrees_for_every_human_seat) | Resolved by the merge onto the shared engine with the B86 rules; a guest raise nobody can answer is refused early. (N70: these tests also pass on the code before the fix.) |
| B81 | fixed (test_takeover_resets_seat_ai_state) | A takeover seat is built from the room's current state and its NPC reads, reveals and learning are reset. |
| B82 | fixed (test_dead_mans_hand_pvp) | The host validates guest poses and shots (open tile, weapon, speed, shot origin, fire rate, one hello) and cleans peer names. |
| B83 | fixed (test_opponent_leaving_mid_match_is_a_forfeit_win, test_own_connection_lost_shows_connection_lost_with_the_score, test_disconnect_after_a_normal_end_keeps_the_real_winner, test_guest_sees_a_forfeit_win_when_the_host_leaves, test_enter_or_click_returns_to_the_lobby_and_esc_still_closes, test_a_click_right_after_the_disconnect_is_still_a_shot) | A disconnect ends the duel on a result screen: "YOU WIN" by forfeit or "CONNECTION LOST" with the score. |
| B84 | fixed (test_wide_button_font_built_once, test_card_cache_reuses_scaled_card, test_panels_share_layer, test_portrait_cached, test_appearance_layers_built_once, test_host_builds_view_only_on_revision_change) | Room view and appearance caches; the host rebuilds its own view only when the revision changes. |
| B85 | fixed (test_shared_ui_usage.test_keywords_accepted) | Resolved by the merge: the Practice table's `TableView.draw` is deleted; a guard test checks every holdem_ui keyword multiplayer uses. |
| B86 | fixed (test_poker_core_eval, test_poker_pots, test_poker_betting_rules, test_poker_hand_flow, test_poker_npc_inputs, test_poker_npc_timing, test_poker_session_resets, test_poker_table_text, test_poker_log_panels, test_poker_cash_round_trip, test_poker_chip_conservation; rooms: test_bmb_pots_use_the_shared_rules, test_folded_to_bettor_gets_uncalled_bet_back, test_reraise_rights_follow_the_shared_rule, test_raise_button_follows_the_host_rule) | The five single-player tables share one set of rules (`core.py`) and NPC inputs (`npc_inputs.py`); Stud bring-in, BMB single card and Five-O columns kept. Room Hold'em runs on the shared engine and room BMB uses the shared pot, raise and winner rules (Phase 11). Audit in 5(a). |
| D1 | fixed (test_customize_no_debug_button, test_solitaire_debug_hotkeys, test_holdem_debug_hotkeys, test_score_four_debug_hotkey, test_debug_menu_solitaire_win, test_f10_ignored_while_typing, test_no_stray_debug_hotkeys) | Customize "DEBUG +100 XP", Solitaire F7/F8, Hold'em F7/Space/B and Score Four F6 removed; the F10 menu has "Win this Solitaire round"; F10 ignored while typing. The journey still uses a copy of the F8 body (N59). |

### W1 window rectangles (manual checks, `tools/window_check.py`)

Dan's PC: monitor 1920x1200, work area (0, 0, 1920, 1152). Rectangles are the outer window (left, top, right,
bottom). Every windowed rectangle lies inside the work area with the title bar visible.

| Check | Phase 2 (125% scaling) | Phase 11 (100% scaling, window DPI 96) |
|---|---|---|
| Single-player from source | 39/39 ok | 41/41 ok |
| Start-up (no saved size) | (103, 87, 1817, 1082), client 1712x963, centred | the same |
| F11, 5 times each way | (0, 0, 1920, 1200), then back to the same centred window | the same |
| Options 1366x768 | (276, 185, 1644, 985) | the same |
| Options 1600x900 | (159, 119, 1761, 1051) | the same |
| Options 1920x1080, 2560x1440 | greyed out ("Too large for this screen.") | the same |
| Saved 2560x1440 | clamped to the default | clamped to 1712x963 |
| Saved fullscreen | starts fullscreen | starts at (0, 0, 1920, 1200) |
| Single-player packaged | 11/11 ok: opens at (103, 87, 1817, 1082); F11 alternates with (0, 0, 1920, 1200) | 11/11 ok (start-up and 5 x F11) |
| Multiplayer from source | (not yet merged) | 110/110 ok, DPI awareness 2, caption "Solitaire+ Multiplayer", no single-player start-up or cursor module loaded |
| MP: no saved size, saved 2560x1440, handed-over 2560x1440 | | client 1712x963, centred |
| MP: handed-over 1600x900 | | client 1600x900 at (159, 119, 1761, 1051) |
| MP: handed-over 1088x612 | | client 1088x612 at (415, 263, 1505, 907) |
| MP: saved fullscreen; handed-over 1600x900 + FULLSCREEN=1 | | (0, 0, 1920, 1200) |
| Multiplayer packaged | | 84/84 ok, the same rectangles, DPI awareness 2 |
| Two-window test (source and packaged Multiplayer windows) | | both client 1712x963 at (103, 87, 1817, 1082), centre offset (0, -0.5), DPI awareness 2 |

Re-run on the final Phase 12 build (100% scaling): source 41/41, packaged 11/11, Multiplayer source 110/110,
Multiplayer packaged 84/84, with the same rectangles as the Phase 11 column.

Not covered yet: the Multiplayer window at 125% scaling, and a person looking at the screen (a screen-saver desktop
was active during the scripted runs). See section 7.

## 5. For the designer

### (a) B86 audit table

As approved by Dan's decision before the sprint: unify the poker variants, keep the deliberate differences
(Stud's bring-in, Blind Man's Bluff's single card, Five-O's columns), and NPC behaviour the same in every
variant, including grudges and behaving differently by cash on hand. The table below is §1 of
`docs/dev/B86_POKER_AUDIT.md` (how each variant behaved before B86). §2 of that file lists the shared rules now in
force, §3 what stays different on purpose, §4 the default choices (also in 5(c) below). What players see is in
`docs/POKER_RULE_CHANGES.md`.

Paths: single-player files are under solitaireplus/games/poker/ (holdem.py, five_card_draw.py, seven_card_stud.py, five_o.py, blind_mans_bluff.py, niche_common.py, ai.py, strategy.py, learning.py, *_screen.py, *_ui.py). solitaireplus/npc/personality.py is written as personality.py. mp/ = multiplayer/. Line numbers are for commit 7195fb3 (before B86). Since Phase 12, holdem.py is split into topic mixins (holdem_seats.py, holdem_npc.py, holdem_betting.py, holdem_pots.py, holdem_showdown.py) and holdem_ui.py into topic modules (holdem_ui_state.py, holdem_ui_widgets.py, holdem_ui_options.py, holdem_ui_pot.py, holdem_ui_cards.py, holdem_ui_log.py, holdem_ui_controls.py, holdem_ui_hud.py); the function names below did not change, and the line numbers still mean the old single files at 7195fb3. NEW-n marks problems not in the brief: NEW-1 an uncalled-bet refund is counted as a won pot; NEW-2 Stud never sets last_resolved_pot at showdown; NEW-3 a human fold in Hold'em fast-forwards the board; NEW-4 the Five-O NPC can never raise; NEW-5 Hold'em chat history is never cleared; NEW-6 a short all-in counts toward Stud's raise cap. Seeded sims (scratchpad only, no repo edits): 0 chips lost in about 1,260 random Hold'em/Draw/Stud hands; B36 seen 2 times in Hold'em and 3 times in Stud; NEW-1 seen in Hold'em and Draw; NEW-2 seen in 25 of 25 Stud showdowns.

| Rule | Hold'em | Five-Card Draw | Seven-Card Stud | Five-O | Blind Man's Bluff | Multiplayer Hold'em |
|---|---|---|---|---|---|---|
| Forced bets a seat can't cover | SB = 1% of buy-in (min 1), BB = 2xSB. A short seat posts what it has and is all-in (post_blind holdem.py:836-945 via commit_*_chips 544-659). 0-chip seats are skipped (get_live_player_indexes 661-685). | Same blinds through inherited post_blind (five_card_draw.py:188-197). | Ante = 20% of small bet, dead money (count_round_bet=False), short ante posts what it has (seven_card_stud.py:234-300, loop 554-557). Bring-in = 50% of small bet from the lowest door card. Seats with no chips are skipped (seat_has_chips 302-324, get_bring_in_index 326-367). A short bring-in posts what it has (369-458). | Ante = 1% (min 5) each. Both stacks must cover it in full, otherwise the session ends (five_o.py:146-156, posts 190-191, _finish_hand 708). | Ante 0.8% (min 5), dead. A seat with stack < ante is not dealt in and sits out. Player < ante ends the session (blind_mans_bluff.py:81-86, 102-105). | Same as SP Hold'em (mp/texas_holdem.py:834-943). A busted host can spectate and gets no cards (953, 1114-1115). |
| current_bet after a short all-in forced bet | Nominal BB. Heads-up, when the other seat can't act: the largest amount actually posted (holdem.py:1085-1090). | Always nominal BB (five_card_draw.py:199) - B39 | Always nominal bring-in (seven_card_stud.py:600-605) - B39 | Not applicable: ante is dead, current_bet = 0 when betting starts (five_o.py:345). | Not applicable: antes are dead, current_bet = 0 (blind_mans_bluff.py:96, 104). | Always nominal BB (mp/texas_holdem.py:1083-1087). This copy predates the fix. |
| Minimum raise and re-raise | Open bet >= BB (holdem.py:3578). Raise-to >= current_bet + last full raise, which starts each street at BB (3586-3604). A short all-in raise lifts current_bet but does not change last_raise_size and does not reopen action (npc_raise 1253-1290, npc_bet 1410, player_bet 3845, player_raise 3950-3962). | Inherited from Hold'em, no changes. | Fixed limit: open = street bet (small bet on 3rd/4th street, big bet on 5th-7th) (seven_card_stud.py:641-654, 1020). Raise = +1 street bet. On 3rd street the bring-in is completed to the small bet (1023-1060). Cap of 3 raises per round; completion is not counted (62, 1075-1093). A short all-in raise still counts toward the cap (1095-1154) - NEW-6 | One size for every bet: round(max(pot, 4xante) x 0.5), at least max(2xante, 2xcurrent_bet), capped at the smaller stack (five_o.py:372-376). A raise uses the same size. At most 3 raises (385, 413). | Open >= max(ante, 1% of buy-in) (blind_mans_bluff.py:163-164). Raise-to >= current_bet + last full raise (180-181). A short all-in does not reopen raise_rights (280-303). No raise cap. | Same as SP Hold'em (mp/texas_holdem.py:3568-3594). |
| Raise allowed when 1 or fewer players can still act (player AND NPC) | Player: blocked (can_player_raise holdem.py:3660-3661). NPC: allowed. can_npc_raise (2982-3030) checks only has_acted and stack - B36 | Inherited: player blocked, NPC allowed - B36 | Inherited, plus the raise cap (seven_card_stud.py:1075-1093): player blocked, NPC allowed - B36 | Player: allowed only if the bet size > current_bet. The size is capped at the smaller stack, so there is never a raise over an all-in (five_o.py:373, 385). NPC: never raises, because context can_raise is hard-coded False (504) and the raise branch at 413 is unreachable - NEW-4 | Both blocked: _can_raise needs another active seat with chips (blind_mans_bluff.py:169-172). _advance drops free options when 1 or fewer can act (320-323). | Neither is guarded: can_player_raise has no such check (mp/texas_holdem.py:3646-3661), and neither does can_npc_raise (2972). Remote humans act through npc_* calls (mp/lan_table.py:48, mp/room_table.py:150-157) - B36 |
| Side-pot building, including layers with no eligible player | build_side_pots makes one layer per contribution level; eligible = not folded and at least 2 cards (holdem.py:1792-1889). At showdown a layer with no eligible player is skipped and the pot is then zeroed, so those chips vanish (4576-4577, 4798) - B37 (not reached in sims; defensive). An uncalled layer with a single contributor is paid out as a won pot, so the over-bettor appears in winner_indexes and in 'Payouts' after losing, and gets the win sound, fans and achievements (holdem_screen.py:132) - NEW-1 | Inherited builder. Same skip (five_card_draw.py:936-937) - B37. Also NEW-1 (seen in sim). | Inherited builder. Same skip (seven_card_stud.py:1678-1679) - B37. Also NEW-1. | No side pots: one pot, bets capped at the smaller stack, and both seats must cover the ante (five_o.py:372-376). | Own inline builder in _showdown (blind_mans_bluff.py:379-398). An uncalled single-contributor layer is refunded and not counted as a win (391-393). A layer with no eligible player is refunded with //, which drops the remainder (394-398) - B42 | Copy of the SP builder (mp/texas_holdem.py:1821-1885). Skip at 4564-4565 - B37. Also NEW-1. |
| Odd-chip distribution | Winners sorted by seat number, so the lowest seat (the human) gets the odd chip first (holdem.py:4602-4620) - B38 | One chip at a time, starting left of the dealer (five_card_draw.py:953-972). | Starting left of the rotating dealer position (seven_card_stud.py:1700-1725). | Split pot: player gets pot//2, NPC gets the rest, so the odd chip always goes to the NPC (five_o.py:631-633). In practice the pot is always even because contributions are equal. | Winners in seat order, lowest seat first (blind_mans_bluff.py:402-403). The no-eligible refund loses the remainder (397) - B38/B42 | Lowest seat first (mp/texas_holdem.py:4590-4605). |
| Ties and split pots | Equal score tuples split each pot separately. Each award record holds amount/eligible/winners/share/remainder/hand (holdem.py:4580-4655). History uses has_true_side_pots (1907-1989), and the recap reads these records (recap.py:12-36). No tie stat. | Same split. The award record has no 'hand' (five_card_draw.py:980-986). Same history logging (1037). | Same split. The record has no 'hand' (seven_card_stud.py:1740-1746). Per-pot lines are logged whenever there is more than one pot, including dead-money layers (1825-1870). | Columns compared one by one; equal columns are ties. 3 or more column wins take the pot; otherwise the pot is split and hands_tied +1 (five_o.py:587-636). | Equal rank splits each pot; suits are ignored. hands_tied counts any hand where the player shared the winnings with others across main and side pots, so it miscounts (blind_mans_bluff.py:399-423) - B42 | Same as SP Hold'em. |
| Showdown order and mucking | Every non-folded hand is shown and logged in seat order, seat 0 first. No mucking (holdem.py:4498-4530). Live hands are shown during an all-in run-out (should_reveal_runout_hands 3388-3399). | Same (five_card_draw.py:885-917). | Same, all 7 cards (seven_card_stud.py:1615-1652). | Both players' columns are revealed from column 1 to 5, 1.1 s each (0.25 s in fast mode), then the result. No mucking (five_o.py:87, 652-684). | All other cards are visible all hand. At showdown the player's own card is shown; no log, no mucking (blind_mans_bluff.py:379-426). | Same as SP Hold'em (mp/texas_holdem.py:4486-4520). |
| All-in run-outs (deal remaining streets/draws without betting) | Once calls are settled and 1 or fewer seats can act, the round is complete (holdem.py:3446-3461). The screen deals one street per street delay (holdem_screen.py:1100-1140). When the human folds and 2 or more NPCs remain, the board is dealt out at once with no more NPC betting, even with unanswered bets (resolve_after_fold 2228-2270 -> complete_board_after_fold 2186-2226) - NEW-3 | Same shortcut. Before the draw: NPCs draw instantly and an all-in human still picks discards (five_card_draw.py:576-617). The post-draw round then closes at once. After a human fold, NPCs keep betting (691-710). | Same shortcut. Every street is dealt to all-in seats too (seven_card_stud.py:809-961). If the antes leave 1 or fewer able to act, the actor is cleared at the start (632-633). After a human fold, NPCs keep betting (980-1006). | Not applicable: all cards are placed before the single betting round. A seat with 0 chips can only check (five_o.py:372-388). | One round only. When nobody is pending, the showdown happens immediately (blind_mans_bluff.py:320-326). | Same shortcut (mp/texas_holdem.py:3449-3451). The standalone table keeps the SP fold fast-forward (2219-2265). The LAN/room TwoHumanGame override keeps play going after a fold (mp/lan_table.py:12-15). |
| Busted players (sit out / removed / rebuy) | Stack 0 after the hand means busted (refresh_busted_state holdem.py:1517-1589). The seat stays, labelled 'Busted', and is dealt out. A human bust or all NPCs busted ends the session after 5 s (holdem_screen.py:178-226). No rebuy. | Same (five_card_draw_screen.py:344-397). | Same (seven_card_stud_screen.py:292-383). | The session is over when either stack < ante (five_o.py:150-156, 708-709, 729-737). Chips left under the ante are returned at cash-out. Next hand and return are manual. | A seat with stack < ante sits out but stays at the table. The session is over when the player < ante or no NPC >= ante (blind_mans_bluff.py:81-86, 433-434). Next hand is manual. | Standalone table: same as SP (mp/standalone_table.py:58, 77). LAN: a busted host spectates (mp/texas_holdem.py:953, 1114). Room: a human can buy back for the starting stack, a busted NPC is replaced by a new NPC with the starting stack, and humans can sit out (mp/room_table.py:10-33, 128-209). |
| Session start and end resets (timers, logs, quick chat, learning store) | Engine start_session resets hand number, rating, hand history, player model, table reads, grudges and quick chat, and binds the learning store in career mode only (holdem.py:365-543; holdem_screen.py:441). The screen resets the 4 timers, the showdown marker and the table-clear (sweep) bonus flag (holdem_screen.py:418-434; B35 fixed). The UI chat history is never cleared (holdem_ui.py:283) - NEW-5. finish_texas_holdem_session does not zero the timers (458-503); only the loop's end path does (1207-1210). | Inherits the engine reset, plus draw state (five_card_draw.py:43-64). The screen resets the timers, the win sound and the UI session including chat (five_card_draw_screen.py:184-199). Finish zeroes the timers (241-246). | Inherits the engine reset. The screen resets the timers and the UI (seven_card_stud_screen.py:171-186). Finish zeroes the timers (227-232). start_hand and showdown never set last_resolved_pot, so the pot shows $0 after a showdown and the fan award uses $1 (seven_card_stud_screen.py:324) - NEW-2 | start_session resets grudges, the chat line, quick chat, stats and rating (five_o.py:103-129). No hand history, table reads, player model or learning store. No screen timers; pending_npc_at is reset each hand (148). | start_session resets NPCs, quick chat, stats and grudges (blind_mans_bluff.py:39-52). No hand history, reads or learning. Presentation events are cleared each hand (87). | Same engine reset as SP except quick chat (mp/texas_holdem.py:364-540). learning_store is never set (114, 394). The standalone table clears the UI chat (mp/standalone_table.py:25-27). |
| NPC action timing and delays | NPC delay 1800/1200/600 ms (slow/normal/fast); street delay 1700/1200/950; auto-deal 18/15/9 s; session end 5 s (holdem_ui.py:542-585; holdem_screen.py:57-63, 973-1213). | Same delay functions (five_card_draw_screen.py:110-130, 775-990). NPC draws are instant (five_card_draw.py:603-612). | Same delay functions (seven_card_stud_screen.py:100-117, 665-865). | NPC response is a fixed 0.65 s (five_o.py:391, 652-654). The NPC's opening bet and card placements are instant (357-370, 301-318). Table speed is ignored. Next hand is manual. | NPC turns are resolved instantly inside _advance (blind_mans_bluff.py:312-336). Only chip animations run, about 520 ms (bluff_presentation.py:27-44). Next hand is manual. | Same delay functions (mp/texas_holdem_ui.py:542-585), used by mp/standalone_table.py:36-45, mp/lan_table.py:55-66 and mp/room_table.py:214-240. The room waits 6 s between hands, and an absent human is auto-folded after the NPC delay. |
| Hand evaluation | evaluate_five_cards (holdem.py:4097-4392) plus best 5 of 7 (4394-4439). | The same inherited code: best of 5 via get_showdown_result (holdem.py:2020-2040). NPC strength calls evaluate_five_cards (five_card_draw.py:787-850). | The same inherited evaluate_best_hand over 7 cards. | niche_common.evaluate_five_card_hand (niche_common.py:51-137), a line-for-line duplicate of Hold'em's evaluator; compare_scores (140-151). | Single card: RANK_VALUES (niche_common.py:6-20). Suits never break ties (blind_mans_bluff.py:399-400). | Its own identical copy (mp/texas_holdem.py:4085-4427). |
| NPC grudges (PokerGrudgeMemory) | PokerGrudgeMemory (personality.py:103-159). Recorded at showdown, per pot: each losing eligible NPC vs each winner, severity = contribution / buy-in (holdem.py:2762-2782, 4796). Never on fold wins. Used by get_npc_grudge_context (2747-2760): pressure only against the last raiser, plus intensity and target stack for knockout bet sizing (ai.py:595-610, 1006). Cleared at session start (382). | Inherited (five_card_draw.py:1052). | Inherited (seven_card_stud.py:1888). Knockout sizing is off because the game is fixed limit (ai.py:596-597). | Own memory (five_o.py:38). Recorded only when the player wins the showdown, with fixed severity 0.5 (642-644); never on folds. Pressure = intensity whenever the NPC faces a bet (515-518); no intensity or target fields. Cleared at start (104). | Inline per-pot recording: losing NPC vs each winner, severity = contribution / buy-in (blind_mans_bluff.py:404-412). Same context helper, with the bettor as last raiser (212-218, 237). Cleared at start (51). | Same as SP Hold'em (mp/texas_holdem.py:2737-2772, 4784). |
| NPC behaviour by cash on hand (stack size, short stack, tenacity) | wealth_pressure ramps up from 115% of buy-in (holdem.py:3049-3075) and makes the profile bolder (ai.py:910-958). The soft per-street bet cap is a fraction of the buy-in, widened by wealth (holdem.py:3077-3135). Survival/tenacity: risk = amount_to_call / stack; tenacity capped at 0.72 and scaled by 0.55 when stack <= 6x BB (ai.py:1006-1009, 1124-1133). | The same signal, scaled by 0.80 before the draw (five_card_draw.py:767-783). Own soft cap (712-750). Short stack = 6x BB. | The signal is scaled 0.45-0.85 by street (seven_card_stud.py:1256-1272). The cap is the fixed-limit amount (1156-1178). Short stack = 6x street bet. | Duplicated wealth formula (five_o.py:427-442), passed at 499-501. No soft cap (fixed bet size). Short stack = 6x bet size. | No starting_stack, wealth_ratio or wealth_pressure in the context (blind_mans_bluff.py:220-236), so wealth has no effect. Maximum bet = whole stack, with no soft cap. Short stack = 6x base minimum. | Wealth works as in SP (mp/texas_holdem.py:3039-3125). Older AI: full tenacity, no short-stack scaling (mp/poker_ai.py:1082). No quick-chat effects. |
| NPC personality traits and rival learning | 8 traits feed build_trait_profile (holdem.py:2710; personality.py:70-94). Skill comes from the NPC's texas_holdem rating (2544-2558; ai.py:198-221). Public reads per opponent (2721-2725, strategy.py) enable advanced strategy. The rival learning store is bound in career mode (holdem.py:392-396, holdem_screen.py:441, learning.py:3). Also a player tendency model and quick-chat effects (2718). | Inherited, with rating key five_card_draw; draw counts go into the reads (five_card_draw.py:752-785; five_card_draw_screen.py:199). | Inherited, with key seven_card_stud; exposed cards go into the reads (seven_card_stud.py:1232-1290; seven_card_stud_screen.py:186). | Traits: yes (five_o.py:491). Skill from the skill tier only, no rating key (496). No table reads, so advanced strategy is off. No learning (learning.GAMES excludes five_o). Quick chat: yes (510-513). Trait chat 25% of the time (520-521). | Traits: yes (blind_mans_bluff.py:224). Skill from the tier only (226). No reads and no learning. Quick chat: yes (238-243). Trait chat 22% of the time (260-262). | Traits, rating-based skill and in-session reads. The learning store is never bound (mp/texas_holdem.py:114, 394). No quick chat. |

### (b) B23 numbers (NPC monthly decline, no change)

The game never calls `simulate_npc_rating_month` (only tests do). The monthly change players see comes from
`npc_development.advance_npc_development` (age curves). Real roster, 12 months from 2026-01, world seed 2026:

| NPC | Age | Start | End | Change |
|---|---|---|---|---|
| Jiu Wang | 21 | 1795.95 | 1814.90 | +18.95 |
| Mary LaFleur | 22 | 1234.75 | 1230.75 | −4.00 |
| Luke Jingle | 37 | 1808.40 | 1807.80 | −0.60 |
| Gary Undo (star) | 38 | 3123.50 | 3119.95 | −3.55 |
| Shelly Barn | 42 | 2818.50 | 2808.60 | −9.90 |
| Monkus Carlton | 46 | 2496.05 | 2483.40 | −12.65 |

Across 20 careers (world seeds 1–20): age 22 or younger (200 samples) mean +15.3, median +14.1, 7% went down; age 35
or older (440 samples) mean −13.8, median −21.8, 90% went down (the 89-year-old Addled Grandfather about −60 a
year). See also N21 in (c).

### (c) Open questions, with the default taken

Sprint-wide (Dan, 2026-11-15):
- B86 [unified without waiting for approval of the audit table; the table is in (a) for review].
- B5 [Recap "Leave table? → No" after a career round returns to the Career hub]. N13: Yes and No now both go to
  the hub; relabel or hide No in career mode? [no change].
- B55 [shots fired during the Ace Invaders wave break don't count; firing is still allowed]. N51: block firing
  during the break? [no change].
- B70 [the room countdown is sent as a "starts at" time, with no relay or room version bump].
- B72 [a disconnected Blind Man's Bluff seat checks, or folds if it can't check].
- NPC development [the three "rebalance" tests stay quarantined until the designer confirms the intended
  numbers; section 2].

Phases 4 to 6:
- N14: the in-game pause menu does not stop the Head-to-Head opponent, countdown or timer [no change; B8 pauses
  only on other screens].
- N20: debug launchers that don't switch to debug mode (Casual Cards, Casino, Poker Night, Crazy Eights, Bango,
  Score Four, Blackjack, Roulette, Faro) play inside the Career: real ratings, fans, cash and news, only the day
  advance is skipped. Sandbox them fully? [no change].
- N21: some late-30s NPCs gain +200 to +250 in one year when their rolled `peak_age` is just above their age
  [no change].
- B23 [no change] and B32 [no change], as the brief's designer decisions (§9) say.

Phase 7 and B86:
- B40: when the lowest Stud door card is all-in [the bring-in goes to the next-lowest card that can post; the usual
  casino rule gives it to the player left of the all-in seat; they differ only with 4+ seats].
- B86 §4 defaults: (1) BMB short stacks play all-in, the session ends at 0 chips; (2) Hold'em after you fold: NPCs
  play out at normal delays (about 30 s at slow speed, up to about 50 s; a spectator fast-forward could be added);
  (3) Stud short all-ins never re-open betting or count toward the 3-raise cap; (4) the B40 bring-in rule above;
  (5) fold wins return the winner's own uncalled bet; (6) winning a contested side pot while losing on the hand
  still plays the win sound, only fans need a profit; (7) the who-won rule also applies to NPC seats; (8) "shown
  weak" read = weak hand category in Hold'em, Draw and Stud, "won nothing" in Five-O and BMB; (9) Five-O has no
  hand-win sound; (10) the Five-O NPC sizes its bets from the human's last preset; (11) Quick Chat after you fold
  hides the lines that sway NPCs; (12) only Hold'em shows the Payout details recap; (13) seeded Five-O and BMB runs
  recorded before B86 deal differently after the first NPC chat. Per-table detail: `docs/POKER_RULE_CHANGES.md`.

Phases 8 to 10:
- B47 [Pass is its own button, not a relabelled Draw Card; NPCs never pass voluntarily] and [a voluntary pass does
  not count toward the B46 blocked-game count].
- B46 [with nothing left to draw the hint still says "No legal play. Draw one card." and Draw Card passes; N39].
- B48 [a "no hint" answer still starts the 30 s cooldown and sets `hint_used`; N42].
- B50 [the rest of a gap is dropped only when more than 2 steps were owed]; B49 [`state.frame_dt` holds the raw
  frame time, the 1/20 s cap is applied at the machines]; B57 [a missing, invalid or 0 previous score counts as no
  previous score]; B54 [only King Pong and Ace Invaders; Battle Bosses is N44].
- B60 [the message stays on the practice menu until the next Start or until the screen is entered again].
- B61 [if no reachable cell qualifies, the level gets no enemies; N57].
- D1 [the F10 button is greyed out, not hidden, away from the Solitaire table]; [the Cryptid search box does not
  hold F10 back, because it has no focus state].

Phase 11 (multiplayer):
- NPC raise rule [no change needed: B86 already applies "somebody must be able to answer" to every NPC and the
  room adds it for guests].
- Mixed-version rooms [no relay change; a protocol stamp and an "Update both games" notice for new guests]. Guests
  on the current release can still join a new host: their Score Four solves are refused, their next-hand countdown
  stays at "Next hand in 6 seconds" (N69), and they get no warning. Redeploy the relay with a version-3 gate
  instead?
- B68 [a busted NPC seat with the normal buy-in first; otherwise take over a funded NPC seat and its stack]. Should
  humans still inherit a funded NPC's stack at all?
- B71 party late joiners [seat order: empty, then a disconnected human's seat, then an NPC seat (a broke NPC's
  first); the buy-in goes to an empty or broke seat, otherwise the joiner inherits the stack; Score Four seats
  joiners only on return to the lobby]. Confirm.
- B72 follow-on [a disconnected BMB seat keeps being dealt in and paying antes until a waiter takes it or it can't
  ante]. Sit it out from the next hand instead?
- B73 ["Table finished" with no new button; a newcomer's buy-in restarts the table]. Give the host a "Room lobby"
  button?
- B78 [minimum Roulette bet $1]. A $10 minimum would match the chip tray.
- B83 [a forfeit "YOU WIN" only when the relay reports the other player left; otherwise "CONNECTION LOST" with the
  last score; PvP records no stats or XP]. OK?
- Multiplayer imports neither `app.audio` nor `app.sounds` (its own sound adapter reads `paths.asset('sounds')`)
  [kept; this departs from the brief's wording of §7 Phase 11 step 2].
- N76: the room lobby still says "Share only this 5-digit code." although codes are 6 letters/digits [left alone,
  because changing it changes what the lobby shows].

Not asked in any report, but worth a look: `docs/POKER_RULE_CHANGES.md` ("Online play") says room Blind Man's
Bluff NPCs still use their own simpler decisions, not the single-player NPC code, and a room BMB seat below the ante
sits out instead of playing all-in [left room-specific]. That differs from the maintainer's request that NPC
behaviour be the same in every variant.

### (d) New findings not fixed

Designer findings N13, N14, N20, N21 are in (c). Findings fixed or resolved later are left out (N1, N2, N7, N8,
N19, N24, N34, N35, N36, N49, N59, N60, N61, N65, N66, N68, N71, N73, N74, N75). N33 is left out too: no report marks it
fixed, but in the tree the fold-win award record has a `remainder` key since B86 (P1). Phase 12 findings are N78 to N81.

App, window, saves, music:
- N3: a save with a null field inside a section (`identity.avatar`, `progression.level`, ...) still crashes
  `apply_profile_save_data` after it loads.
- N4: a non-numeric NPC category rating (`"strategy": "abc"`) still raises in `derive_overall`.
- N5: B62 removed the "start the next track when the mixer is idle" fallback; a lost end-of-music event would
  leave music off until the next mode change.
- N6: `ui/text.get_font` clears on `pygame.quit()` but not on `pygame.font.quit()` (nothing calls that).
- N12: a saved "ambient" music mode starts during the splash, a saved "instrumental" when the splash is left (both
  end up right).
- N52: `state.arcade_state` is not declared in `app/state.py` (start-up sets it), so a test that skips start-up
  gets an AttributeError.
- N78: log pruning (Phase 12): on a non-Windows build pruning could delete the log of a copy that is still running
  (Windows refuses to delete an open file).
- N80: `multiplayer/multiplayer_paths.py:5` and `multiplayer/relay_transport.py:19` find the repo root with
  `Path(__file__)` (for `sys.path` and the working folder, not asset lookups); §10.4 may want them on `app.paths`.

Profile and menus:
- N9: when a new profile's save goes to a recovery file, the B12 message is set but never shown.
- N11: after a Solitaire round with no level-up, "No (deal again)" goes straight back to the table, so a level-up
  queued earlier waits until the next menu or hub screen.

Solitaire and Head-to-Head:
- N15: `finish_head_to_head_race` ignores the player's round summary (why B3 is not visible).
- N16: `Game.get_elapsed_seconds()` counts time spent in Options in every mode except Head-to-Head (lowers the time
  bonus).
- N17: a stale stock flip (the card dragged within 220 ms) can block the player's own stock clicks until another
  flip finishes.
- N18: `new_race_game()` still deals and discards a full random deal first (and plays the shuffle sound).
- N63: `Game.debug_auto_solve_state` (now in `games/solitaire/auto_solve.py`) has no caller.

Career:
- N22: `get_career_leaderboard()` rebuilds and sorts the whole leaderboard on every call (twice per hub frame).
- N23: clicking the job you already have re-rolls future work-day titles and saves.
- N25: the ~40 other `auto_save_career()` callers show the locked-save toast only on the hub, so a locked save
  elsewhere is silent unless the player returns within 8 s.
- N26: switching jobs A → B → A in one day leaves one rewritten story although the day ends on the starting job.
- N27: a shown rating rounds .5 to even (2818.50 shows as 2818), so a shown change can be one point off.

Casino:
- N28: the roulette WIN/LOSE status line is computed from the bets on the table at draw time, not the settled
  result.
- N29: `claim_faro_session_result` computes a rating tier it never uses; a break-even Faro night costs at least 1
  fan.
- N30: on split blackjack rounds the Low Roller flag is per round, not per hand.
- N31: after leaving the horse races mid-race through F10 and coming back, the race continues without its cue.

Poker:
- N37: `strategy.LATE_STREETS` changed value with B86 (single-round stages count as final rounds). Room NPCs now
  get it through the merged code; no separate room check was reported.

Casual cards:
- N38: Crazy Eights can loop forever when the pile is empty and players keep drawing and replaying recycled
  discards (2 of 2,000 simulated games with the pile emptied at the deal).
- N39: with no legal play and nothing to draw, the hint still says "No legal play. Draw one card." though Draw
  Card now passes.
- N40: the Crazy Eights suit choice has no cancel.
- N41: `CrazyEightsGame._choose_npc_card` gives face cards and tens two bonuses under two identical `if` tests
  (redundant).
- N42: a Score Four "no hint" answer still starts the cooldown and sets `hint_used`.
- N43: the Crazy Eights hand highlight's switch to `is_player_card_playable` has no test of its own.

Arcade:
- N44: Battle Bosses still rounds its ball to whole pixels on every collision sub-step, so its speed varies with
  the real frame time.
- N45: Dead Man's Hand reads `window.clock.get_time()` for its dt; it could use `state.frame_dt` (not a bug).
- N46: Suit Snake smooth movement: after a clamped long gap the snake snaps to its cell, then sits still for one
  step (cosmetic).
- N47: Ace Invaders `_draw_background` builds a full-screen SRCALPHA veil every frame.
- N48: `assets/arcade/bg.png` has never been in git; King Pong and the arcade hub pages always draw a plain fill.
- N50: Battle Bosses and King Pong smoothscale and mask NPC portraits every frame; Battle Bosses also builds several
  full-size surfaces per frame.
- N51: Ace Invaders: firing during the wave break still plays the sound, the bullets freeze and vanish; shots in
  flight when a wave ends or a life is lost still count.
- N53: the Ace Invaders game-over footer works out "NEW HIGH SCORE!" itself, so a first-ever game still shows it.

Dead Man's Hand:
- N56: B61's second pass can put two enemies in one cell when the 1.35 spacing can't be met (only maps with a sealed
  room; no shipped level).
- N57: with no reachable candidate cell a level gets no enemies, clears at once and still pays the clear bonus (no
  shipped level).
- N58: `validate_levels()` checks only that enemies are not in walls, not that they are reachable;
  `_reachable_floor()` repeats `DeadMansHandGame._reachable_open_cells()`.
- N77: `DeadMansHandGame` caches its HUD fonts per game object, so each run or duel builds them again on its first
  frame (once per game, not per frame).

Debug menu:
- N10: before any profile is picked, an F10 debug career started from the start-up profile screen auto-saves into
  slot 1.
- N55: only the way back from the debug menu is shared (`close_debug_menu()`); the way in is still inline in
  `app/loop.py`.
- N62: `state.holdem_manual_bet_active` is not cleared when the Hold'em recap opens, so F10 could stay ignored
  (mostly theoretical).
- N64: `test_no_stray_debug_hotkeys` allows no function key other than F10 and F11; a new key binding must update
  it.

Multiplayer:
- N69: an old guest at a new host sees a frozen "Next hand in 6 seconds" for the whole pause (part of the
  mixed-version question in (c)).

Tests and tools:
- N32: `test_career_ratings` still sets the blackjack `round_complete`/`payout_claimed` flags by hand.
- N54: `screen_harness.py compare` and `replay.py compare` for the same uncached baseline fail when run at the same
  time (both `git worktree add` the same folder).
- N67: `test_debug_menu_close_recaptures_mouse` opens the menu with its own copy of the F10 code;
  `test_debug_no_globals`' 250 ms assertion is close to always true.
- N70: the B80 guest-raise tests also pass on the code before the fix (they guard the behaviour, not the change).
- N72: posted mouse input does not reliably reach an SDL window; a scripted two-window hand needs a test-only
  input hook, or a person.
- N79: `tests/updater/test_updater.py` ApplyTests fail now and then on this PC (`OSError` or
  `PermissionError` while applying an update in a temporary folder, a different test each time, probably a virus
  scanner). Not quarantined.
- N81: `updater/__init__.py:12` says "See docs/RELEASING.md and AGENTS.md"; neither file exists yet (section 7).

## 6. Layout

- `main.py` (27 lines): bootstrap, `--multiplayer`, update recovery, then the main loop. `version.py` stays at the
  root; so do `SolitairePlus.spec`, `build_release.ps1`, `README.md`, `CHANGELOG.md`, `PLAYING.txt`.
- `solitaireplus/app/`: start-up in the old order (`startup.py`), the main loop and screen registry (`loop.py`),
  shared state (`state.py`, `state_names.py`), window, fonts, sounds and audio, assets, paths, settings, update
  check, runtime support (logs, log pruning, crash hooks), multiplayer launcher, `game_globals.py`, `lazy.py`.
- `solitaireplus/ui/`: shared drawing helpers: text and the font cache, buttons, panels, backgrounds, cursors,
  image caches.
- `solitaireplus/menus/`: splash, main menu, mode select, Free Play select, difficulty, Options, Customize, help
  screen and help content, achievements screen.
- `solitaireplus/profile/`: profile select and editor, saves and save data, avatars, leveling, level-up, recap,
  achievements, cosmetics, unlocks.
- `solitaireplus/career/` (+ `events/`): the Career hub and its screens (jobs, real estate, leaderboards, bio, news,
  case opening, activities), calendar, ratings, fans, NPC world and development, saving, rewards; `events/` holds
  event select, event screen, summary, night results, press interview, autographs.
- `solitaireplus/npc/`: NPC manager, personalities and their chat, portraits (`game_portraits.py` for the table
  portraits), avatars.
- `solitaireplus/games/solitaire/`: the Solitaire engine (`rules.py` with 8 topic mixins and `constants.py`), the
  table screen and engine instance (`screen.py`, `table.py`), race deals, the restart prompt, Head-to-Head.
- `solitaireplus/games/poker/`: shared rules (`core.py`, `npc_inputs.py`, `table_timers.py`, `log_rows.py`), AI,
  strategy, learning, speech, quick chat, recap, and each table with engine, UI and screen: Hold'em (split into
  `holdem_*` and `holdem_ui_*` topic modules), Five-Card Draw, Seven-Card Stud, Five-O, Blind Man's Bluff.
- `solitaireplus/games/casino/`: blackjack, roulette, horse races, Faro (engine, UI, screen each).
- `solitaireplus/games/cards/`: Crazy Eights, Bango, Score Four (engine, UI, screen; Score Four difficulty and
  tiers).
- `solitaireplus/games/arcade/`: the arcade hub screens, machine pickers, the four machines (King Pong, Battle
  Bosses, Ace Invaders, Suit Snake), machine screens and music, `motion.py`, `support.py`.
- `solitaireplus/games/cryptid/`: Cryptid Creatures cards, creatures, AI, collection, battle views, collection
  screen.
- `solitaireplus/games/dead_mans_hand/`: levels, game, weapons, screen, and the only PvP duel code (`pvp.py`).
- `solitaireplus/debug/`: the F10 menu (`menu.py`, `menu_screen.py`), what its buttons do (`actions.py`), debug game
  mode, the poker table picker, unlocks.
- `multiplayer/`: the Multiplayer window (`main.py`, hub, options, profile, appearance, chat, widgets), rooms
  (`room_protocol.py`, `room_game.py`, `room_session.py`, `room_table.py`, `room_view.py`, `room_relay.py`), party
  games (`party_authority.py`, `party_view.py`), the relay server and transports, `net_client.py`; tests in
  `multiplayer/tests/`. No copies of game engines.
- `netservice/`: `SolitaireNet.exe`, the separate network service (protocol, service, relay and WebSocket
  connectors).
- `updater/`: `SolitaireUpdater`: update plan, download, signature checks, transactional apply and rollback, UI.
- `tests/<area>/`: `app`, `ui`, `menus`, `profile`, `career`, `npc`, `games/{solitaire, poker, casino, cards,
  arcade, cryptid, dead_mans_hand}`, `debug`, `packaging`, `updater`, `netservice` (no `__init__.py` in them, on
  purpose); `tests/support/` helpers and the profile fixture; `tests/KNOWN_FAILURES.txt`.
- `tools/`: the test runner, screen harness (+ `harness/`), replay, window check, release and signing scripts,
  manifest, preflight, relay probe, project audit, `verify_solitaire_state.py`.
- `docs/`: `NETWORKING.md`, `POKER_RULE_CHANGES.md`, `RAILWAY_DEPLOY.md`, `TESTING.md`; `docs/dev/`: the brief,
  the phase reports, the B86 audit, the Phase 11 plan, `DEBUG_MENU_CHANGES.md` (every debug menu and debug key change, for
  the maintainer) and this file.
- Also: `installer/` (Inno Setup script), `assets/`, `data/`, `.github/workflows/`.

## 7. Manual items for Dan

1. **Play one Hold'em hand through two Multiplayer windows** (one from source and one packaged, or two packaged
   with different LOCALAPPDATA folders) against a relay on 127.0.0.1. The recipe is in `docs/TESTING.md`, "Local
   two-player test". Creating and joining the room was scripted; starting the table and the hand could not be
   (posted clicks did not register, N72).
2. While doing that, **check that the picture fills the window.** The `PrintWindow` captures showed the 1366x768
   picture at 1:1 in the middle of the 1712x963 client, while the mouse was mapped as if it filled it. Most likely
   a capture artefact (a screen-saver desktop was active).
3. **On-screen window check on your PC (§10.4, W1).** The game window and the Multiplayer window must open fully
   on-screen with the title bar visible, and stay that way after F11 in and out of fullscreen and after every
   Options window size. The scripted checks passed (section 4), but nobody looked at the screen, the Multiplayer
   window was only checked at 100% scaling (your PC was at 125% in Phase 2). They were re-run on the final build
   and passed. Run `tools\window_check.py source` and `packaged`, each also with `--multiplayer`, and watch.
4. **Delete the stray file** `C:\Users\Dan Fiscus\Documents\standalone_preview.png` (outside the repository; still
   there on 2026-11-16). The deleted `multiplayer/tests/test_standalone.py` wrote it.
5. **User docs:** `docs/RELEASING.md`, `docs/INSTALLING.md`, `docs/CODE_SIGNING.md` and `AGENTS.md` are not written;
   the original session writes them (brief §7 Phase 12). `updater/__init__.py` already points at `RELEASING.md` and
   `AGENTS.md`.
6. **Answer the designer questions** in 5(c), including the expected numbers for the three quarantined
   `test_npc_development` tests, and decide on mixed-version rooms before the next release.

## 8. Return checklist (§10.4) as checked at the end

| Item | State |
|---|---|
| `main.py` is the small entry point; no file in `solitaireplus/` over about 3,000 lines | yes: 27 lines; the largest is `games/poker/five_card_draw_ui.py` (2,599) |
| `solitaireplus/legacy.py`, `tools/refactor/` and `requirements-dev.txt` are gone | yes (and `libcst` is uninstalled from the venv) |
| No `global` statements and no `globals()` calls in `solitaireplus/` or `main.py` | yes; `tests/app/test_no_global_statements.py` keeps it so |
| No duplicate engine modules in `multiplayer/` | yes: no file shares a name with a game module, and no 12-line block is shared |
| No `Path(__file__)` asset lookups outside `app/paths.py` | yes in `solitaireplus/` and `main.py`; `multiplayer/` has two repo-root lookups that are not asset lookups (N80) |
| `grep` finds none of the deleted hotkeys | yes: no K_F6/K_F7/K_F8 or `debug_xp_rect`, no Hold'em K_SPACE/K_b |
| Packaged build, self-tests, launch and the local multiplayer test pass | yes, on the final build (installer included): see the Phase 12 results in `PHASE_REPORTS.md` |
| On Dan's PC, both windows open fully on-screen and stay that way after F11 and every Options size (W1) | the scripted checks pass at 100% scaling; a person still needs to look, and check 125% (section 7) |
| Every bug ID is accounted for in the hand-back table | yes: 88 IDs in section 4 |
