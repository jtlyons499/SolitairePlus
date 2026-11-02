# Solitaire+

A game about card games with progression, minigames, and aliens.

## Play the game

### Windows

**[Download the latest Windows release](https://github.com/jtlyons499/Solitaire/releases/latest/download/Solitaire-Windows.zip)**

1. Download `Solitaire-Windows.zip`.
2. Extract the ZIP to a folder.
3. Double-click `Simple Solitaire.exe`.

You do **not** need to install Python to use the packaged Windows release.

> If there is not a public release yet, use the repository's **Actions** tab, open the latest successful **Build Windows Release** run, and download the `Solitaire-Windows` artifact. GitHub requires you to be signed in to download workflow artifacts.

## Source code

The files in this repository are the development source code. If you only want to play the game, use the Windows download above instead of GitHub's automatically generated **Source code (zip)** download.

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
