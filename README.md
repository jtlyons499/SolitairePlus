# Solitaire+

A game about card games. Dynamic career progression, streamlined multiplayer, intelligent NPCs, minigames, and aliens.

![](https://i.imgur.com/jR7gUMW.png)

## Play the Game

### Windows

**[Download the installer from the latest release](https://github.com/jtlyons499/SolitairePlus/releases/latest)**
(`SolitairePlus-Setup-<version>.exe`).

1. Run the installer. If Windows says "Windows protected your PC", click **More info**, then **Run anyway**.
2. Keep "Trust the Solitaire+ publisher" ticked, and when Windows asks to install the certificate, check that
   its thumbprint matches the one below before clicking **Yes**.
3. Play from the Start Menu. The game updates itself from then on (an **Update to …** button appears on the
   main menu).

**Publisher certificate thumbprint:** not set yet (the first signed release adds it here).

Already playing an older version, or prefer the ZIP? Step-by-step instructions, including how to keep your saves:
[docs/INSTALLING.md](docs/INSTALLING.md). You do **not** need Python to play.

This application has been verified Stuxnet free since September 2026.

## What's new
See [CHANGELOG.md](CHANGELOG.md) for every version's changes.

##  Instant play / debug / bypass progression / 
Press F10 to pull up the debug menu, which lets you select from some of the following options:
1. Trigger career "event nights" which present different games
2. Trigger career modifications (simulate time, add reserve NPCs, etc.)
3. Play solitaire challenge modes and all minigames
4. Advance progression by adding cash / profile XP / level / rating / customization unlocks

To win a Solitaire round automatically, press F10 at the Solitaire table and click
"Win this Solitaire round" (under SOLITAIRE CHALLENGES).

## Prioritized changes to come
- Overhaul Dead Man's Hand minigame in both singleplayer and multiplayer
- Continue adding missing assets
  - Achievements, Cryptid Creatures, case opening rewards
- Overhaul gameplay of Cryptid Creatures
  - Reduce stagnancy and repetition
  - Increase speed of battles
  - Improve gameplay flow and eliminate confusion
 - Additional choose-your-own adventure story events in Career Mode

## Source code

The files in this repository are the development source code. If you only want to play the game, use the Windows download above instead of GitHub's auto **Source code (zip)** download. But I mean if you _do_ want to download the src and everything...

### Running from source

The project targets Python 3.14 (3.12 also works) and uses pygame-ce.

```bash
python -m pip install -r requirements.txt
python main.py
```

## Building a Windows package locally

Create the project's Python environment once, then run the build script. It installs the pinned
dependencies, runs all tests and the asset check, and builds the game:

```powershell
py -3.14 -m venv .venv
.\build_release.ps1
```

The playable folder is created at `dist/SolitairePlus/` and a test ZIP at `release/Solitaire-Windows.zip`.
Local builds are unsigned test builds. Official releases are made with `tools/release.ps1`
([docs/RELEASING.md](docs/RELEASING.md)); signing is explained in [docs/CODE_SIGNING.md](docs/CODE_SIGNING.md),
the tests in [docs/TESTING.md](docs/TESTING.md). AI assistants: read [AGENTS.md](AGENTS.md) first.
