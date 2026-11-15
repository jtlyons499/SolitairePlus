"""The modules that used to live in shared/ import correctly in both launch contexts.

Single-player imports them from solitaireplus/. Multiplayer still imports them by their
old names through the compatibility shims in multiplayer/ (until Phase 11 of the
restructure), which must hand back the very same module objects.
"""
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULES = {
    'npc_personality': 'solitaireplus.npc.personality',
    'npc_personality_chat': 'solitaireplus.npc.personality_chat',
    'poker_core': 'solitaireplus.games.poker.core',
    'poker_learning': 'solitaireplus.games.poker.learning',
    'poker_speech': 'solitaireplus.games.poker.speech',
    'poker_strategy': 'solitaireplus.games.poker.strategy',
    'poker_ui_assets': 'solitaireplus.games.poker.ui_assets',
    'texas_holdem_chat': 'solitaireplus.games.poker.holdem_chat',
}

COMMON_CHECKS = '''
from solitaireplus.games.poker.strategy import RivalLearning
from solitaireplus.games.poker.learning import RivalLearning as canonical
assert RivalLearning is canonical
from solitaireplus.npc.personality import get_npc_traits
assert isinstance(get_npc_traits({}), dict)
'''


class SharedImportTests(unittest.TestCase):
    def run_program(self, cwd, program):
        env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
        env.pop('PYTHONPATH', None)
        result = subprocess.run([sys.executable, '-c', program], cwd=cwd,
                                env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_singleplayer_imports(self):
        program = '''import importlib
for name in %r:
    module = importlib.import_module(name)
    assert module.__file__.replace('\\\\', '/').endswith('/' + name.replace('.', '/') + '.py'), module.__file__
''' % (sorted(MODULES.values()),) + COMMON_CHECKS
        self.run_program(ROOT, program)

    def test_direct_multiplayer_imports(self):
        program = '''import importlib
for old, new in %r.items():
    legacy = importlib.import_module(old)
    real = importlib.import_module(new)
    assert legacy is real, old
    legacy._compatibility_probe = object()
    assert real._compatibility_probe is legacy._compatibility_probe
''' % (MODULES,) + COMMON_CHECKS
        self.run_program(ROOT / 'multiplayer', program)


if __name__ == '__main__':
    unittest.main()
