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
