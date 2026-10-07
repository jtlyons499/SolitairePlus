"""Consolidated launch paths and child-process isolation."""
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

import multiplayer_launcher as launcher


class LauncherTests(unittest.TestCase):
    def test_source_command(self):
        self.assertEqual(launcher.launch_command(), [sys.executable, str(launcher.ROOT / 'main.py'), '--multiplayer'])

    def test_frozen_command_and_independent_bootloader(self):
        with patch.object(sys, 'frozen', True, create=True), patch.object(subprocess, 'Popen') as popen:
            self.assertTrue(launcher.MultiplayerLauncher().launch())
            args, kwargs = popen.call_args
            self.assertEqual(args[0], [sys.executable, '--multiplayer'])
            self.assertEqual(kwargs['env']['PYINSTALLER_RESET_ENVIRONMENT'], '1')

    def test_duplicate_launch_and_reopen(self):
        process = Mock()
        process.poll.return_value = None
        with patch.object(subprocess, 'Popen', return_value=process) as popen:
            ui = launcher.MultiplayerLauncher()
            self.assertTrue(ui.launch())
            self.assertFalse(ui.launch())
            process.poll.return_value = 0
            self.assertTrue(ui.launch())
            self.assertEqual(popen.call_count, 2)

    def test_missing_installation(self):
        with patch.object(launcher, 'ROOT', Path('/missing-solitaire-installation')):
            ui = launcher.MultiplayerLauncher()
            self.assertFalse(ui.launch())
            self.assertIn('Missing multiplayer', ui.error)

    def test_real_dispatch_uses_multiplayer_engine(self):
        script = '''
import pygame
import multiplayer_launcher
pygame.event.get = lambda: [pygame.event.Event(pygame.QUIT)]
multiplayer_launcher.run_multiplayer()
import texas_holdem
from pathlib import Path
assert Path(texas_holdem.__file__).parent.name == 'multiplayer'
'''
        env = os.environ.copy()
        env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
        result = subprocess.run([sys.executable, '-c', script], cwd=launcher.ROOT, env=env,
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
