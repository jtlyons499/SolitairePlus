# Solitaire+

A game about card games with progression, multiplayer, minigames, and aliens.

![](https://i.imgur.com/jR7gUMW.png)

## Play the game

### Windows

**[Download the latest Windows release (v0.0.6)](https://github.com/jtlyons499/SolitairePlus/releases/latest/download/Solitaire-Windows.zip)**

1. Download `Solitaire-Windows.zip`.
2. Extract the ZIP to a folder.
3. Double-click `Simple Solitaire.exe`.

You do **not** need to install Python to use the packaged Windows release.

## Latest changelog
Solitaire+ 0.0.6
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

##  Instant play / debug / bypass progression / 
Press F10 to pull up the debug menu, which lets you select from some of the following options:
1. Trigger career "event nights" which present different games
2. Trigger career modifications (simulate time, add reserve NPCs, etc.)
3. Play solitaire challenge modes and all minigames
4. Advance progression by adding cash / profile XP / level / rating / customization unlocks
Press F9 during games of Solitaire to automatically win.

## Historic changelog
- v0.0.5
  - to fill later

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
