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
    runpy.run_path(str(folder / 'main.py'), run_name='__main__')


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
