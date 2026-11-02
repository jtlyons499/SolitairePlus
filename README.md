# Solitaire+

A game about card games with progression, minigames, and aliens.

![](https://i.imgur.com/pwxPPd0.png)

## Play the game

### Windows

**[Download the latest Windows release](https://github.com/jtlyons499/SolitairePlus/releases/latest/download/Solitaire-Windows.zip)**

1. Download `Solitaire-Windows.zip`.
2. Extract the ZIP to a folder.
3. Double-click `Simple Solitaire.exe`.

You do **not** need to install Python to use the packaged Windows release.

##  Quick Play / Debug / Bypass Progression / 
Press F10 to pull up the debug menu, which lets you select from some of the following options:
1. Trigger career "event nights" which present different games
2. Trigger career modifications (simulate time, add reserve NPCs, etc.)
3. Play solitaire challenge modes and all minigames
4. Advance progression by adding cash / profile XP / level / rating / customization unlocks


## Source code

The files in this repository are the development source code. If you only want to play the game, use the Windows download above instead of GitHub's auto **Source code (zip)** download.

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
