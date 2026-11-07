# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

project = Path(SPECPATH)
mp_files = [
    (str(p), str(p.parent.relative_to(project)))
    for p in (project / 'multiplayer').rglob('*.py')
    if not any(part in {'tests', '__pycache__', '.venv'} for part in p.relative_to(project).parts)
]

version_path = project / 'build_version_info.txt'
version_file = str(version_path) if version_path.exists() else None

icon_path = project / 'assets' / 'app_icon.ico'
icon_file = str(icon_path) if icon_path.exists() else None


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[(str(project / 'assets'), 'assets'), (str(project / 'data'), 'data')] + mp_files,
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
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Simple Solitaire',
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
    contents_directory='.',
    version=version_file,
    icon=icon_file,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Simple Solitaire',
)
