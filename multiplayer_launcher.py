"""Launch isolated multiplayer in source and PyInstaller builds."""
from pathlib import Path
import os
import runpy
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def launch_command():
    if getattr(sys, 'frozen', False):
        return [sys.executable, '--multiplayer']
    return [sys.executable, str(ROOT / 'main.py'), '--multiplayer']


def run_multiplayer():
    """Called before any single-player imports: avoid overlapping module names."""
    folder = ROOT / 'multiplayer'
    if not (folder / 'main.py').is_file():
        raise FileNotFoundError('Missing multiplayer/main.py. Extract the complete consolidation batch.')
    sys.path.insert(0, str(folder))
    os.chdir(ROOT)
    if '--selftest' in sys.argv:
        raise SystemExit(run_selftest(folder))
    runpy.run_path(str(folder / 'main.py'), run_name='__main__')


# Server-only and test-only modules. The packaged game does not ship them
# (keep in sync with MP_EXCLUDED in SolitairePlus.spec).
SELFTEST_SKIP = {'relay_server', 'room_relay', 'relay_websocket', 'relay_transport'}


def run_selftest(folder):
    """`SolitairePlus.exe --multiplayer --selftest [--selftest-report FILE]`

    Imports every multiplayer module the way the packaged game would, without
    opening a window. The multiplayer files ship as loose .py source, so
    PyInstaller cannot see what they import. A standard-library module they
    need may be missing from the exe; this finds that before players do.
    Exit code 0 = all imported; 1 = at least one failed (details in the report).
    """
    import importlib
    import traceback
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
    lines, failed = [], 0
    try:
        import pygame
        pygame.init()
    except Exception as error:
        lines.append(f'FAILED pygame: {error!r}')
        failed += 1
    for path in sorted(folder.glob('*.py')):
        if path.stem in SELFTEST_SKIP:
            continue
        try:
            importlib.import_module(path.stem)
            lines.append(f'ok     {path.stem}')
        except BaseException as error:  # SystemExit/ImportError alike: report, keep going
            failed += 1
            detail = traceback.format_exception_only(type(error), error)[-1].strip()
            lines.append(f'FAILED {path.stem}: {detail}')
    lines.append(f'FAILED: {failed} check(s) failed; see the lines above' if failed
                 else 'PASSED: every multiplayer module imported')
    report = '\n'.join(lines) + '\n'
    if '--selftest-report' in sys.argv:
        index = sys.argv.index('--selftest-report')
        if index + 1 < len(sys.argv):
            Path(sys.argv[index + 1]).write_text(report, encoding='utf-8')
    if sys.stdout is not None:
        try:
            sys.stdout.write(report)
        except (OSError, ValueError):
            pass
    return 1 if failed else 0


class MultiplayerLauncher:
    def __init__(self):
        self.process = None
        self.error = ''

    def launch(self):
        if self.process is not None and self.process.poll() is None:
            return False
        self.error = ''
        if not (ROOT / 'multiplayer' / 'main.py').is_file():
            self.error = 'Missing multiplayer files. Extract the complete batch.'
            return False
        # A frozen child must outlive the parent without inheriting its bootloader state.
        env = os.environ.copy()
        try:
            import pygame
            surface=pygame.display.get_surface()
            if surface:
                width,height=surface.get_size();env['SOLITAIRE_MP_WINDOW']=f'{width}x{height}'
                env['SOLITAIRE_MP_FULLSCREEN']='1' if surface.get_flags() & pygame.FULLSCREEN else '0'
        except (ImportError,RuntimeError):pass
        if getattr(sys, 'frozen', False):
            env['PYINSTALLER_RESET_ENVIRONMENT'] = '1'
        try:
            self.process = subprocess.Popen(launch_command(), cwd=str(ROOT), env=env)
            return True
        except OSError:
            self.error = 'Could not launch Multiplayer. Check the game installation.'
            return False
