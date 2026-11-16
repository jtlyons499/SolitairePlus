"""multiplayer/ has no copies of game modules left, and nothing imports the old names.

Since Phase 11 of the restructure, multiplayer imports the shared code straight from
solitaireplus/ (engine, UI, AI, recap, NPC portraits, poker helpers, Dead Man's Hand
PvP). The modules that used to live in shared/ still import correctly from the
single-player side.
"""
import ast
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
MULTIPLAYER = ROOT / 'multiplayer'

# Module names multiplayer/ used to have its own copy, shim or LAN/Practice file for.
# Used by both tests below: no such file exists, and nothing imports the name.
OLD_NAMES = (
    'texas_holdem', 'texas_holdem_ui', 'texas_holdem_chat',
    'poker_ai', 'poker_recap', 'poker_core', 'poker_speech', 'poker_strategy',
    'poker_learning', 'poker_ui_assets',
    'npc_personality', 'npc_personality_chat', 'npc_portraits', 'npc_avatars',
    'audio',
    'dead_mans_hand_pvp',
    'lan_transport', 'lan_session', 'lan_protocol', 'lan_table',
    'standalone_table', 'standalone_view',
)

SHARED_MODULES = (
    'solitaireplus.games.poker.core',
    'solitaireplus.games.poker.holdem_chat',
    'solitaireplus.games.poker.learning',
    'solitaireplus.games.poker.speech',
    'solitaireplus.games.poker.strategy',
    'solitaireplus.games.poker.ui_assets',
    'solitaireplus.npc.personality',
    'solitaireplus.npc.personality_chat',
)

COMMON_CHECKS = '''
from solitaireplus.games.poker.strategy import RivalLearning
from solitaireplus.games.poker.learning import RivalLearning as canonical
assert RivalLearning is canonical
from solitaireplus.npc.personality import get_npc_traits
assert isinstance(get_npc_traits({}), dict)
'''

IMPORT_FUNCTIONS = {'import_module', '__import__'}


def old_name_imports(path, names=OLD_NAMES):
    """Every import of an old name in one file (see scan_source)."""
    return scan_source(path.read_text(encoding='utf-8'), path.relative_to(ROOT).as_posix(), names)


def scan_source(source, label, names=OLD_NAMES):
    """'<label>:<line>: <module>' for every import of a module in names, in line order.

    multiplayer/ is not a package: its modules import each other by bare name, so an
    old copy shows up as the first part of an import's module name (``import poker_core``,
    ``from poker_core import x``, ``import audio.sub``) or as the string given to
    importlib.import_module / __import__. ``from solitaireplus.app import audio`` is
    the shared module, not the old copy, so it does not count."""
    wanted = set(names)
    tree = ast.parse(source, filename=label)
    found = []
    for node in ast.walk(tree):
        modules = []
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                modules = [node.module]
            elif node.level:
                # A relative import inside multiplayer/ would also reach a sibling file.
                modules = [node.module] if node.module else [alias.name for alias in node.names]
        elif (isinstance(node, ast.Call) and node.args
              and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, 'id', None)
            if name in IMPORT_FUNCTIONS:
                modules = [node.args[0].value]
        for module in modules:
            if module.split('.')[0] in wanted:
                found.append((node.lineno, f'{label}:{node.lineno}: {module}'))
    return [line for _, line in sorted(found)]


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
''' % (list(SHARED_MODULES),) + COMMON_CHECKS
        self.run_program(ROOT, program)

    def test_no_copies_left(self):
        self.assertTrue((MULTIPLAYER / 'main.py').is_file())
        left = [f'multiplayer/{stem}.py' for stem in OLD_NAMES if (MULTIPLAYER / f'{stem}.py').exists()]
        self.assertEqual(left, [])

    def test_nothing_imports_old_names(self):
        files = sorted(MULTIPLAYER.rglob('*.py'))
        # The scan must really see the multiplayer code and its tests.
        self.assertIn(MULTIPLAYER / 'main.py', files)
        self.assertIn(MULTIPLAYER / 'mp_assets.py', files)
        self.assertTrue(any(path.parent.name == 'tests' for path in files))
        found = [line for path in files for line in old_name_imports(path)]
        self.assertEqual(found, [])

    def test_scan_sees_every_import_form(self):
        source = '\n'.join([
            'import poker_core',
            'import audio.mixer as mixer',
            'from npc_portraits import draw_layered_portrait',
            'from . import texas_holdem',
            'import importlib',
            "importlib.import_module('lan_table')",
            "__import__('standalone_view')",
            'from solitaireplus.app import audio',
            'from solitaireplus.games.poker.core import describe_poker_score',
            'import mp_assets',
        ])
        found = scan_source(source, 'probe.py')
        self.assertEqual([line.split(': ', 1)[1] for line in found],
                         ['poker_core', 'audio.mixer', 'npc_portraits', 'texas_holdem',
                          'lan_table', 'standalone_view'])
        self.assertEqual([int(line.split(':')[1]) for line in found], [1, 2, 3, 4, 6, 7])


if __name__ == '__main__':
    unittest.main()
