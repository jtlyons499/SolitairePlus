# Changelog

All notable changes to Solitaire+ are recorded here. The newest version is at the top.

How to use this file (maintainers and AI agents):
* While working, add a short line under **[Unreleased]** for every player-visible change.
* `tools/release.ps1` turns the **[Unreleased]** heading into the new version number and date.
  It refuses to release when **[Unreleased]** is empty.
* GitHub Release notes are copied from the matching section here automatically.

## [Unreleased]

### Behind the scenes
- The game's version number now comes from one place (`version.py`), so the in-game version always matches the GitHub release.
- The game program is now called `SolitairePlus.exe` (was `Simple Solitaire.exe`). Saves are not affected.
- Unit tests now run automatically before every release, both on the maintainer's PC (`tools/release.ps1`) and on GitHub.
- Online play now runs through a small separate program, `SolitaireNet.exe`, so connection fixes and new connection types can ship without changing the game itself.
- Online games now notice a dead connection (no reply for 45 seconds) instead of waiting forever, and a malformed server reply no longer leaves the game stuck on "Waiting for friend".
- The game no longer remembers the default server address as if you had chosen it, so moving the server to a new address won't strand anyone.

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


