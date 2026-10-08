"""Verify shared modules in both supported launch contexts."""
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULES = ('npc_personality', 'npc_personality_chat', 'poker_core',
           'poker_learning', 'poker_speech', 'poker_strategy',
           'poker_ui_assets', 'texas_holdem_chat')

class SharedImportTests(unittest.TestCase):
    def check_context(self, cwd):
        program = '''import importlib
names = %r
for name in names:
    legacy = importlib.import_module(name)
    shared = importlib.import_module('shared.' + name)
    assert legacy is shared, name
    assert legacy.__file__.replace('\\\\', '/').endswith('/shared/' + name + '.py')
    legacy._compatibility_probe = object()
    assert shared._compatibility_probe is legacy._compatibility_probe
from poker_strategy import RivalLearning
from poker_learning import RivalLearning as canonical
assert RivalLearning is canonical
from npc_personality import get_npc_traits
assert isinstance(get_npc_traits({}), dict)
''' % (MODULES,)
        env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
        env.pop('PYTHONPATH', None)
        result = subprocess.run([sys.executable, '-c', program], cwd=cwd,
                                env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_singleplayer_imports(self):
        self.check_context(ROOT)

    def test_direct_multiplayer_imports(self):
        self.check_context(ROOT / 'multiplayer')
