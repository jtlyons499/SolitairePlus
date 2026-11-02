# Solitaire+

A growing card-game and career-simulation project built with Python and pygame-ce, featuring Solitaire, poker, casino games, multiplayer, arcade games, and Dead Man's Hand.

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

Keep all generated files together when moving or sharing the build.

### Optional application icon

If `assets/app_icon.ico` exists, release builds automatically use it as the Windows executable icon. If it is absent, the build still succeeds with the default executable icon.

## Publishing a release

The repository includes a GitHub Actions workflow that automatically builds the Windows package.

For a public release:

1. Merge the release-ready changes into `main`.
2. Create and push a version tag such as `v0.1.0`.
3. GitHub Actions builds the game on Windows.
4. The workflow creates a GitHub Release and attaches `Solitaire-Windows.zip`.

Example:

```bash
git checkout main
git pull
git tag v0.1.0
git push origin v0.1.0
```

The permanent player-facing download URL remains:

```text
https://github.com/jtlyons499/Solitaire/releases/latest/download/Solitaire-Windows.zip
```

## Development builds

The Windows workflow can also be run manually from **Actions → Build Windows Release → Run workflow**. Non-release runs upload the packaged ZIP as a temporary GitHub Actions artifact without publishing a public release.
