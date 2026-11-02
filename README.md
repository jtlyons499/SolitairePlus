# Solitaire+

A game about card games. Dynamic career progression, streamlined multiplayer, intelligent NPCs, minigames, and aliens.

![](https://i.imgur.com/jR7gUMW.png)

## Play the Game

### Windows

**[Download the latest Windows release (v0.0.6b)](https://github.com/jtlyons499/SolitairePlus/releases/latest/download/Solitaire-Windows.zip)**

1. Download `Solitaire-Windows.zip`.
2. Extract the ZIP to a folder.
3. Double-click `Simple Solitaire.exe`.

You do **not** need to install Python to use the packaged Windows release.
Yes, Windows typically will request permission to run the game the very first time, but that's how .exe files work.

This application has been verified Stuxnet free since September 2026.

## Latest changelog
Solitaire+ 0.0.6b
-------------------------------------------
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

##  Instant play / debug / bypass progression / 
Press F10 to pull up the debug menu, which lets you select from some of the following options:
1. Trigger career "event nights" which present different games
2. Trigger career modifications (simulate time, add reserve NPCs, etc.)
3. Play solitaire challenge modes and all minigames
4. Advance progression by adding cash / profile XP / level / rating / customization unlocks
Press F9 during games of Solitaire to automatically win.

## Prioritized changes to come
- Overhaul Dead Man's Hand minigame in both singleplayer and multiplayer
- Continue adding missing assets
  - Achievements, Cryptid Creatures, case opening rewards
- Overhaul gameplay of Cryptid Creatures
  - Reduce stagnancy and repetition
  - Increase speed of battles
  - Improve gameplay flow and eliminate confusion
 - Additional choose-your-own adventure story events in Career Mode

## Historic changelog
v0.0.6 - first pass
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


## Source code

The files in this repository are the development source code. If you only want to play the game, use the Windows download above instead of GitHub's auto **Source code (zip)** download. But I mean if you _do_ want to download the src and everything...

### Running from source

The project currently targets Python 3.14 and uses pygame-ce.

```bash
python -m pip install -r requirements.txt
python main.py
```

## Building a Windows package locally

Install the project dependencies and PyInstaller:

```bash
python -m pip install -r requirements.txt
python -m pip install pyinstaller
```

Optionally generate Windows version metadata, then build:

```bash
python tools/write_version_info.py
pyinstaller --clean --noconfirm "Simple Solitaire.spec"
```

The playable folder will be created at:

```text
dist/Simple Solitaire/
```
