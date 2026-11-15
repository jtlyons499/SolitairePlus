# Changelog

All notable changes to Solitaire+ are recorded here. The newest version is at the top.

How to use this file (maintainers and AI agents):
* While working, add a short line under **[Unreleased]** for every player-visible change.
* `tools/release.ps1` turns the **[Unreleased]** heading into the new version number and date.
  It refuses to release when **[Unreleased]** is empty.
* GitHub Release notes are copied from the matching section here automatically.

## [Unreleased]

### New
- **A real installer.** `SolitairePlus-Setup-<version>.exe` installs the game for your Windows account only (no administrator prompt), adds Start Menu shortcuts (and an optional desktop shortcut), can bring over saves from an old unzipped copy, and uninstalls cleanly from Windows Settings. Your saves are only deleted if you say so.
- The installer can mark the Solitaire+ developers as a trusted publisher (Windows asks you to confirm), so the game and its updates show as verified.
- **In-game updates.** The game checks for a new version when it starts and shows an "Update to …" button on the main menu. Click it and the game saves, closes, updates only the files that changed, and reopens. You can also check by hand (Options → Updates → Check now), or turn the automatic check off.
- Updates are checked for the developers' signature. If an update can't be verified, the updater warns you twice before it will install anything.
- An interrupted update (for example a power cut) is undone automatically the next time you start the game.
- Your Options choices (music, volume, sound effects, window size, fullscreen, double-click) are now remembered between launches.

### Fixes
- **The game window now fits your screen.** It opens at the largest size that fits comfortably (title bar and taskbar included), centred, and it stays fully on-screen when you leave fullscreen or pick a window size. Options only offers window sizes that fit; the others are greyed out. Fullscreen fills your monitor without stretching the picture (black bars where the shape differs). The game is sharp on screens with Windows display scaling (125% and up) instead of being blurry and oversized. A window size saved on a bigger monitor no longer breaks the game on a smaller one.
- Music no longer skips every other track, and changing the music mode no longer jumps past the first song.
- Buttons stay highlighted under the mouse after you press a key (before, nothing lit up until the mouse moved).
- Leaving Options while dragging a volume slider no longer leaves the slider stuck to the mouse when you come back.
- A save whose progression or career section is empty (null) no longer crashes the profile screen.
- A damaged save file no longer crashes the game on the profile screen. The game opens the previous good copy (a backup is now kept on every save). If no copy is readable, the slot says "Damaged save" and the damaged file is kept so it can be repaired.
- A save made by a newer version of the game is no longer opened (and silently damaged) by an older version; the slot says "Needs update".
- Level-up screens earned elsewhere (another game, a battle) are no longer lost when a Solitaire round ends.
- On the profile screen, a slot's level no longer sits underneath its Delete button.
- The profile screen no longer re-reads all three save files 60 times a second.
- A missing avatar picture no longer crashes the profile editor; that part is left out instead.
- If the profile can't be saved because the save is in use (another copy of the game is open), the Profile screen now says so instead of "Profile saved".
- You can no longer delete the profile you're playing; the screen asks you to load another profile first.
- The game no longer switches the music to Ambient after the splash screen when you chose another mode (or Off) in Options.
- The Customize screen no longer shows a leftover "DEBUG +100 XP" button.
- Solitaire's Auto-solve no longer stops halfway when it has to turn the waste pile over, and it no longer spins through the stock for a minute when the ending can't be finished.
- Restart after a Head-to-Head race deal now restores the race deal, not a different one.
- In Head-to-Head, the 3-2-1 countdown no longer counts against your time, and the opponent no longer keeps racing while you're in Options (both clocks pick up where they left off).
- Clicking the top row of the Career calendar no longer opens a free Solitaire round that paid career rewards without using a day.
- After a career Solitaire round, "Leave table? → No" now returns to the Career hub instead of dealing an extra round that paid full rewards.
- Leaving a career round from the pause menu, or backing out of the difficulty screen, no longer leaves the round's challenge rules on the next game.
- Removed the Solitaire F7/F8 debug keys (the instant win moves to the F10 debug menu later).
- The Career hub and leaderboards no longer rebuild the whole NPC roster several times a frame.
- Switching side jobs several times in one day now gives one news story (naming your latest job) instead of one per click.
- Damaged career activity data (a Bigfoot or Alien night) no longer crashes the game every frame; the night is skipped safely.
- After a locked save, the Career hub now says the progress went to a recovery file instead of "Profile saved".
- Roulette: spinning again with the same bets now pays out (it used to take the stake and pay nothing), a spin that doesn't start no longer takes your money, changing your chips after a spin clears the old result, and a $1,500 stake shows as "1.5k" instead of "1k".
- Blackjack: a round can no longer show the same card twice, a natural pays 3:2 rounded up to the dollar (a $5 bet wins $8, not $7), and the "Low Roller" achievement now needs a real Stand.
- The horse races no longer leave the music permanently quieter after you leave them.
- Faro: placing a bet, taking it back and cashing out no longer counts as a played session (no free rating, XP or fans).
- The blackjack table does much less work every frame (fonts and the background picture are made once).
- Hold'em: starting a new session after busting no longer ends it on the first frame, the table-clear bonus can be earned again in later sessions, and the hand recap's "Eligible:" line is no longer blank when everyone else folded.
- Seven-Card Stud: a player who is all-in from the ante no longer has to "post" the bring-in.
- Five-Card Draw: if the deck ever runs out during the draw, the discards are shuffled back in instead of silently keeping your old card.
- Removed the Hold'em F7/Space/B debug keys.
- The poker tables and the hand recap do less work every frame (fonts are made once).
- F10 debug menu: jumping to the Career hub or a debug night during Free Play no longer saves the Free Play $5,000 into your career, debug nights no longer use up a career day, and leaving a debug session no longer leaves the game in debug mode (where real career nights weren't recorded).

### Online play
- Room codes are now 6 letters/digits instead of 5 digits, and guessing other people's room codes is slowed down and then blocked. Old 5-digit codes still work with players who haven't updated.
- Online play can now use an encrypted connection (wss://) once the relay server is switched over. It needs no setup for players.

### Behind the scenes
- The game's version number now comes from one place (`version.py`), so the in-game version always matches the GitHub release.
- The game program is now called `SolitairePlus.exe` (was `Simple Solitaire.exe`). Saves are not affected.
- Unit tests now run automatically before every release, both on the maintainer's PC (`tools/release.ps1`) and on GitHub.
- Online play now runs through a small separate program, `SolitaireNet.exe`, so connection fixes and new connection types can ship without changing the game itself.
- Online games now notice a dead connection (no reply for 45 seconds) instead of waiting forever, and a malformed server reply no longer leaves the game stuck on "Waiting for friend".
- The game no longer remembers the default server address as if you had chosen it, so moving the server to a new address won't strand anyone.
- The game folder is tidier: `SolitairePlus.exe` and `SolitaireNet.exe` sit next to one `SolitairePlus_Data` folder that holds everything else.
- Each release now lists every file with a checksum (`manifest.json`) and ships a small "changes only" download, so future in-game updates only fetch what actually changed.
- The game's code now lives in one `solitaireplus/` package, organised by area (app, menus, profile, career, NPCs, and one folder per game family) instead of 110 files in the top folder. Game files are found from the install folder, not the current folder. Nothing changes for players.
- New developer safety net for the upcoming code reorganisation: every screen is rendered headless and compared pixel by pixel between versions, and 18 scripted playthroughs check that money, XP and progress come out the same (`tools/screen_harness.py`, `tools/replay.py`).
- Menus and career screens do much less work every frame: fonts and scaled button art are made once and reused, and the drifting main-menu background is pre-scaled instead of shrinking a 4300x2500 picture 60 times a second. The picture is exactly the same.

## [0.0.6b] - 2026-11-02

**MULTIPLAYER**
-  Added three more games to multiplayer
  - Score-Four (24), up to four users, optional NPCs of varying difficulty
    - Users/NPCs compete to solve each puzzle first, first to 3 wins
  - Blind Man's Bluff, up to four users, optional NPCs of varying difficulty
    - Everyone's playing card is visible except your own, whoever has the highest card wins
    - Players who go broke switch to spectators
  - Roulette, up to four users, optional NPCs of varying difficulty
    - Users and/or NPCs can play roulette together, host can change time available to bet before each spin
    - Players who go broke switch to spectators
- Re-worked the multiplayer hub UI, streamlined joining/hosting lobbies
  - Can now quickly select one of five available modes
  - Replaced custom PNG avatars with the singleplayer avatar builder 
  - Lobby/room codes are shorter and apply to whichever game the host selected
  - LAN and Practice options removed
  - Game defaults to using the server running on Railway, no need to know an IP
  - Blind Man's Bluff, Roulette, and Hold'em now have live chat for users to interact
- Updated multiplayer Texas Hold'em to be current with the singeplayer version
  - Copied over more polished UI, improvements in AI behavior 
  - Clearer animations and card details
    
**SINGLEPLAYER**
- Reworked how the poker rating is calculated in Career Mode
  - Increases/decreases are based more on the user's own change in money
  - More generous rating rewards for cash gains, less punishing for cash losses
- Rating decline caused by age in NPCs is now much stronger, 
- User now has a public appeal status based on recent trends in fan engagement
- News now addresses major milestones in user's rating progression, oddity stories re-written
- NPC decision making now accounts for having larger amounts of money in all poker games
  - NPCs may bet more, may raise instead of calling, call instead of backing down, etc.
  - Personality traits still control the degree to which this impacts NPCs
- Added a "Quick Chat" option in Texas Hold'em with ~180 possible replies
  - Depending on the context of the game, the user can select messages to send to NPCs
  - Responses are determined by the NPCs strongest personality traits with a mix of randomization
  - NPCs may shift their behavior based on the user's quick chats (e.g. bet more aggressively)
  - During a hand of poker...
    - How's it going?
    - I have a crush on...(select NPC)
    - I despise...(select NPC)
    - Favorite suits?
    - Where's everyone from?
    - Anything going on with y'all?
    - I'm bored
    - I've got a great hand
  - Between hands of poker...
    - Easy win (response pool will vary if used after a loss)
    - Nice hand
    - Well played

## [0.0.6]

- Added "Arcade Night" event with four unrated minigames in the style of retro Atari games
  - Win tickets, set high scores, cash in tickets for customization unlocks 
    - King Pong (Pong)
    - Ace Invaders (Space Invaders)
    - Battle Bosses (Warlords)
    - Suit Snake (Snake)
  - Added a very basic DOOM-inspired FPS minigame where you fight against playing card monsters through 10 levels
    - CURRENTLY CAN ONLY ACCESS THROUGH DEBUG MENU (F10)
    - Enemy health is based on the card number, one starting weapon and three bonus weapons to pick up
    - Handful of custom skyboxes and floors
  - Added a very basic PVP multiplayer version of the game, 1v1, first to five kills   
  - Added dozens of missing assets


