# -*- mode: python ; coding: utf-8 -*-
#
# Builds the Solitaire+ install folder (dist/SolitairePlus/):
#
#   SolitairePlus.exe        the game (also runs the Multiplayer window with --multiplayer)
#   SolitaireNet.exe         online-play network service (netservice/)
#   SolitaireUpdater.exe     updater (updater/)
#   SolitairePlus_Data/      shared Python runtime + assets/, data/, multiplayer/, version.py
#
# All three exes share one runtime folder. Each exe only contains its own Python code,
# so a change to netservice/ rebuilds SolitaireNet.exe but not the game, and an
# asset change rebuilds neither (see tools/make_manifest.py).
#
# Build with build_release.ps1 (local) or the GitHub workflow; both write the
# version resources first (tools/write_version_info.py).

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

project = Path(SPECPATH)
CONTENTS = 'SolitairePlus_Data'

# multiplayer/*.py ship as loose source files (multiplayer_launcher runs them),
# so multiplayer updates do not change the game exe. Server-only and test-only
# modules are left out of the player install.
MP_EXCLUDED = {'relay_server.py', 'room_relay.py', 'relay_websocket.py', 'relay_transport.py'}
mp_files = [
    (str(p), str(p.parent.relative_to(project)))
    for p in (project / 'multiplayer').rglob('*.py')
    if not any(part in {'tests', '__pycache__', '.venv'} for part in p.relative_to(project).parts)
    and p.name not in MP_EXCLUDED
]


def optional(path):
    return str(path) if path.exists() else None


icon_file = optional(project / 'assets' / 'app_icon.ico')


# ----------------------------------------------------------------------------- game
game = Analysis(
    ['main.py'],
    pathex=[str(project)],
    binaries=[],
    datas=[
        (str(project / 'assets'), 'assets'),
        (str(project / 'data'), 'data'),
        # Loose, so a release that only changes the version number does not change the exe.
        (str(project / 'version.py'), '.'),
    ] + mp_files,
    # Standard-library modules that only the loose multiplayer/*.py files use.
    # PyInstaller cannot see those imports. If the frozen self-test fails with
    # "No module named X", add X here (see docs/TESTING.md).
    hiddenimports=[
        'asyncio',
        'socket',
        'ssl',
        'queue',
        'threading',
        'secrets',
        'argparse',
        'uuid',
        'base64',
        'io',
    ]
    # Every game module. The main loop opens screens by module name
    # (solitaireplus/app/loop.py SCREENS) and some modules reach each other through
    # solitaireplus.app.lazy, so PyInstaller cannot see those imports.
    + collect_submodules('solitaireplus'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['version', 'netservice', 'updater'],
    noarchive=False,
    optimize=0,
)
game_pyz = PYZ(game.pure)
game_exe = EXE(
    game_pyz,
    game.scripts,
    [],
    exclude_binaries=True,
    name='SolitairePlus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    contents_directory=CONTENTS,
    version=optional(project / 'build_version_info.txt'),
    icon=icon_file,
)


# ----------------------------------------------------------------------------- network service
net = Analysis(
    [str(project / 'netservice' / '__main__.py')],
    pathex=[str(project)],
    binaries=[],
    datas=[],
    hiddenimports=['netservice.connectors.relay', 'netservice.connectors.websocket', 'websockets.asyncio.client'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pygame', 'tkinter', 'version'],
    noarchive=False,
    optimize=0,
)
net_pyz = PYZ(net.pure)
net_exe = EXE(
    net_pyz,
    net.scripts,
    [],
    exclude_binaries=True,
    name='SolitaireNet',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    # Console program: the game talks to it over stdin/stdout pipes and starts it
    # with CREATE_NO_WINDOW, so players never see a window.
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    contents_directory=CONTENTS,
    version=optional(project / 'build_version_info_net.txt'),
    icon=icon_file,
)


# ----------------------------------------------------------------------------- updater
# Part of the shared folder on purpose (not a single self-extracting file, and it
# never runs a copy of itself from %TEMP%): Microsoft Defender flagged that pattern
# as malware. Files it is using during an update are renamed aside instead.
upd = Analysis(
    [str(project / 'updater' / '__main__.py')],
    pathex=[str(project)],
    binaries=[],
    datas=[],
    hiddenimports=['tkinter', 'tkinter.ttk', 'updater.trusted_publishers'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pygame', 'version', 'netservice'],
    noarchive=False,
    optimize=0,
)
upd_pyz = PYZ(upd.pure)
upd_exe = EXE(
    upd_pyz,
    upd.scripts,
    [],
    exclude_binaries=True,
    name='SolitaireUpdater',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    contents_directory=CONTENTS,
    version=optional(project / 'build_version_info_updater.txt'),
    icon=icon_file,
)


coll = COLLECT(
    game_exe,
    game.binaries,
    game.datas,
    net_exe,
    net.binaries,
    net.datas,
    upd_exe,
    upd.binaries,
    upd.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='SolitairePlus',
)
