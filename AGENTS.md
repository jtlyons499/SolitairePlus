# Solitaire+: guide for AI assistants (and the people working with them)

## For the game's creator, in plain words

Solitaire+ now installs like a normal Windows program (`SolitairePlus-Setup-<version>.exe`, no administrator
rights needed) and updates itself: when a new version is out, the main menu shows an **Update to …** button, and
only the files that changed are downloaded. Players' saves are not touched by installing, updating or (unless
they ask) uninstalling; they stay in `%LOCALAPPDATA%\SimpleSolitaire` as before. Online play now runs through a
small separate program (`SolitaireNet.exe`), so new ways of connecting can be added without touching the game.
The code was reorganised into one file per game and per screen (`solitaireplus/`), and about 90 bugs were fixed;
see `CHANGELOG.md`.

What you need to do:
1. **Once:** set up the signing certificate and the two GitHub secrets ([docs/CODE_SIGNING.md](docs/CODE_SIGNING.md),
   part 1). Until then, releases cannot be published (on purpose: they are never published unsigned).
2. **Once:** point Railway at this repository's relay ([docs/RAILWAY_DEPLOY.md](docs/RAILWAY_DEPLOY.md)).
3. **Every release:** merge your changes, then run `.\tools\release.ps1 -Version X.Y.Z`
   ([docs/RELEASING.md](docs/RELEASING.md)). GitHub builds, signs and publishes it; players get it on their next
   launch.
4. **Before each release, test:** start the game from a local build, play what changed, try windowed and
   fullscreen (F11), and for online changes play one round with two Multiplayer windows
   ([docs/TESTING.md](docs/TESTING.md), "Local two-player test").
5. Open questions waiting for you are in `docs/dev/HANDBACK.md`, section 5(c).

Hand this file to ChatGPT (attach it) or any coding assistant before asking it to change the game. Codex and
similar tools read it automatically from the repository root.

---

## Everything below is for AI assistants

Read this section completely before changing anything. When a rule here conflicts with what seems convenient,
follow the rule and say why in your answer.

### The project in one paragraph

A single-player card-game collection with a career mode (Solitaire, poker variants, casino games, casual card
games, an arcade, Cryptid Creatures, Dead Man's Hand) plus an online Multiplayer window. Python with pygame-ce,
packaged with PyInstaller into three Windows programs, installed with Inno Setup, updated by its own updater from
GitHub Releases. Everything is drawn on a fixed 1366x768 surface and scaled to the window.

### Setting up and running

```powershell
py -3.14 -m venv .venv                     # once (3.12 also works locally; CI uses 3.14)
.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-build.txt
.venv\Scripts\python.exe main.py           # the game; add --multiplayer for the Multiplayer window
.venv\Scripts\python.exe tools\run_tests.py   # all tests
.\build_release.ps1                        # local unsigned build into dist\SolitairePlus (add -Installer)
```

### The three programs

| Program | Built from | Role |
|---|---|---|
| `SolitairePlus.exe` | `main.py`, `solitaireplus/` (+ `multiplayer/*.py` shipped as loose files) | The game and the Multiplayer window (`--multiplayer`) |
| `SolitaireNet.exe` | `netservice/` | All internet connections for online play. The Multiplayer window starts it and talks to it over stdin/stdout |
| `SolitaireUpdater.exe` | `updater/` | Checks GitHub Releases, verifies signatures, downloads changed files, replaces them all-or-nothing with rollback |

They share one folder (`SolitairePlus_Data`). Assets, data, `multiplayer/*.py` and `version.py` ship as loose
files, so updates replace only what changed. [docs/RELEASING.md](docs/RELEASING.md) has the table "which part
changes when you edit what".

### Where things are

- `main.py`: start-up only (about 30 lines).
- `solitaireplus/app/`: start-up, the main loop and screen registry (`loop.py`), shared runtime state
  (`state.py`), window and scaling (`window.py`), fonts, sounds, asset and data paths (`paths.py`), settings,
  update check.
- `solitaireplus/ui/`: shared drawing helpers (text and font cache, buttons, panels, cursors, image caches).
- `solitaireplus/menus/`, `profile/`, `career/` (+ `events/`), `npc/`, `debug/`: screens and their logic.
- `solitaireplus/games/<family>/<game>`: each game as rules (no pygame), UI and screen modules. Families:
  `solitaire`, `poker`, `casino`, `cards`, `arcade`, `cryptid`, `dead_mans_hand`.
- `multiplayer/`: the Multiplayer window, rooms, party games, the relay server. It imports the game engines from
  `solitaireplus`; it has no copies of them.
- `netservice/`, `updater/`, `installer/`, `tools/`, `tests/<area>/`, `docs/`.
- Full map: `docs/dev/HANDBACK.md`, section 6.

### Rules for changing code

**Structure**
1. Shared runtime values live in `solitaireplus/app/state.py`: write `state.cash = …`. Never use `global` or
   `globals()`; a test fails if you do.
2. Import modules, not names: `from solitaireplus.career import saving`, then `saving.auto_save_career()`.
   This prevents circular-import bugs.
3. Every screen module has `handle_event(event)`, optionally `update(now)`, and `draw(surface)`, and is listed
   in the registry in `solitaireplus/app/loop.py`.
4. Game rules modules (`rules.py`, engines) never import pygame, so they can be unit-tested.
5. Find files with `solitaireplus/app/paths.py` (`paths.asset("cards", "fronts", "AS.png")`,
   `paths.data(...)`). Never build paths from the working folder or from `__file__`.
6. Create fonts and scaled images once (the caches in `ui/` and `app/fonts.py`), never every frame.

**Window and input**
7. Draw on `window.game_surface` (1366x768) only. `window.present()` scales it to the window. Never use
   pygame's `SCALED` mode: it does not rescale after a resize (the cause of the old black borders).
8. Mouse positions reach screens in game coordinates (`window.translate_event`). If you read
   `pygame.mouse.get_pos()` yourself, pass it through `window.window_to_game_coords()`.
9. Function keys: F10 opens the debug menu and F11 toggles fullscreen. Do not add other function-key hotkeys
   (`tests/debug/test_no_stray_debug_hotkeys.py` checks this); put debug actions in the F10 menu.

**Online play** ([docs/NETWORKING.md](docs/NETWORKING.md))
10. No socket, HTTP or WebSocket code in `solitaireplus/` or `multiplayer/` screens. Connections live in
    `netservice/connectors/`; the game talks to `SolitaireNet.exe` through `multiplayer/net_client.py`.
11. A new way to connect is a new connector module registered by URL scheme. The game does not change.
12. Tests and tools only listen on `127.0.0.1`. Never run `tools/relay_probe.py` against the live Railway relay.

**Saves**
13. Saves live in `%LOCALAPPDATA%\SimpleSolitaire` and `%LOCALAPPDATA%\SolitaireMultiplayer`, never in the game
    folder. Do not rename these folders.
14. If you change what a profile save contains, raise `PROFILE_VERSION` in `solitaireplus/profile/saves.py` and
    add a function to `MIGRATIONS` that upgrades the previous version. Never make the loader accept a newer save
    (it shows "Needs update" on purpose).

**Updater and signing** ([docs/CODE_SIGNING.md](docs/CODE_SIGNING.md))
15. Never weaken the signature check or remove the two "could not be verified" warnings. Never trust a
    certificate other than the thumbprints in `updater/trusted_publishers.py`.
16. Never copy the updater or any exe to `%TEMP%` (or anywhere else) and run it from there. Windows Defender
    flagged exactly that once. The updater works inside the install folder (`.update/`) and renames files in use
    aside (`*.updating-old`).
17. Never put a certificate, private key, password or Base64 key text in the repository, a log or an answer.

**Releases** ([docs/RELEASING.md](docs/RELEASING.md))
18. Never edit `version.py`, never create or move a git tag. Only `tools/release.ps1` does that, run by a person.
19. Add player-visible changes under **[Unreleased]** in `CHANGELOG.md`.
20. Changing `netservice/` or `updater/`: raise that folder's `__version__`.

**Tests** ([docs/TESTING.md](docs/TESTING.md))
21. Run `tools/run_tests.py` before saying something works, and report its result exactly.
22. `tests/KNOWN_FAILURES.txt` lists tests that were already broken. Never add a test there to hide a new
    failure; delete its line when you fix it.
23. When you move code without meaning to change behaviour, `tools/screen_harness.py compare` and
    `tools/replay.py compare` must report every screen identical. List every screen you changed on purpose.
24. For window changes, run `tools/window_check.py source` (and `packaged` after a build) on a real screen.

### Things that look odd but are intended

- The F10 debug menu is in public builds on purpose (the creator's friends use it). Its "Win this Solitaire
  round" button replaced the old F7/F8 keys.
- Unused images in `assets/` are kept on purpose. Do not delete them.
- The two save folders (`SimpleSolitaire`, `SolitaireMultiplayer`) are separate for historical reasons; merging
  them needs a save migration and is not planned yet.
- Multiplayer Hold'em and single-player Hold'em share one engine; differences between them (chat, spectators,
  customization) are options of that engine, not copies.
- Multiplayer `.py` files ship as loose source files, so a module they import may need to be listed in
  `hiddenimports` in `SolitairePlus.spec`. The packaged self-test (`--selftest`) catches a missing one.

### Do not

- Do not reintroduce `global`, `globals()`, per-frame font creation, or working-folder-relative paths.
- Do not copy a game engine into `multiplayer/`; import it.
- Do not add network code outside `netservice/`.
- Do not change saves' location, the exe names, or the installer's `AppId`.
- Do not change the Windows certificate stores from code or scripts, and do not ask a person to trust a
  certificate other than the official one.
- Do not delete the F10 debug menu or its features.
- Do not publish, tag or push releases yourself.

### Open work (as of November 2026)

Waiting for the creator (`docs/dev/HANDBACK.md`, section 5): the open rule questions in 5(c), including the
expected numbers for the three quarantined `test_npc_development` tests, and whether players with different
versions may share an online room.

Known issues not fixed yet: `docs/dev/HANDBACK.md`, section 5(d) (numbered N3 to N81).

Future work:
- Horse-race place/show odds can favour the player (B32, left as is for now).
- Lossless recompression of the large PNG files.
- Merging the two save folders (needs a save migration).
- Microsoft's paid signing service instead of the self-signed certificate (see the end of
  [docs/CODE_SIGNING.md](docs/CODE_SIGNING.md)).
