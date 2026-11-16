"""Multiplayer uses the single-player Hold'em UI module (Phase 11 ui-merge, B85 guard).

The multiplayer copy of the Hold'em UI module is gone: the room and party tables, the
options panel and the menus import solitaireplus.games.poker.holdem_ui. Two kinds of
mistake would only show up on the screen that runs the bad line:
  - an attribute the old copy had but the shared module keeps elsewhere. The table speed
    was a module global there and lives in solitaireplus.app.state now, so the old
    `ui.holdem_table_speed = ...` store would silently do nothing;
  - a keyword the shared function doesn't take (B85: the Practice table passed
    show_utility_buttons to draw_texas_holdem).
These tests read every multiplayer source and test file with ast and check each use
against the real module. They also check that the room clock passes its own table speed
to the shared delays, that the shared font cache is rebuilt after pygame.quit(), and that
importing the multiplayer client doesn't start the single-player game.
"""
import ast
import inspect
import os
import random
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import pygame

from multiplayer_paths import ROOT
from room_table import RoomAuthority
from solitaireplus.app import state
from solitaireplus.games.poker import holdem_ui

MODULE = 'solitaireplus.games.poker.holdem_ui'
PACKAGE, _, MODULE_NAME = MODULE.rpartition('.')
MULTIPLAYER = ROOT / 'multiplayer'
OLD_COPY = MULTIPLAYER / f'texas_{MODULE_NAME}.py'   # deleted in Phase 11


def dotted(node):
    """'a.b.c' for a Name/Attribute chain, else None."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return '.'.join(reversed(parts))


class HoldemUiUses(ast.NodeVisitor):
    """Every use of holdem_ui in one file: attributes read or written through a module
    alias, names from-imported from it, and calls to its functions.

    Each function or class body is a scope; a parameter or a plain assignment with the
    alias's name hides the module inside that scope.
    """

    def __init__(self):
        # name -> ('module',) | ('package',) | ('attr', name on holdem_ui) | None (hidden)
        self.scopes = [{}]
        self.attributes = []     # (line, attribute, 'load' | 'store' | 'del')
        self.imported = []       # (line, name)
        self.star_imports = []   # line
        self.calls = []          # (line, function name on holdem_ui, ast.Call)

    # ---- names
    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def is_module(self, node):
        if isinstance(node, ast.Name):
            return self.lookup(node.id) == ('module',)
        name = dotted(node)
        return name == MODULE and self.lookup(name.split('.')[0]) == ('package',)

    def bind(self, name, meaning):
        self.scopes[-1][name] = meaning

    # ---- imports
    def visit_Import(self, node):
        for alias in node.names:
            if alias.name == MODULE and alias.asname:
                self.bind(alias.asname, ('module',))
            elif alias.asname is None and (alias.name + '.').startswith('solitaireplus.'):
                self.bind('solitaireplus', ('package',))
            else:
                self.bind(alias.asname or alias.name.split('.')[0], None)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            local = alias.asname or alias.name
            if node.module == PACKAGE and alias.name == MODULE_NAME:
                self.bind(local, ('module',))
            elif node.module == MODULE:
                if alias.name == '*':
                    self.star_imports.append(node.lineno)
                    continue
                self.imported.append((node.lineno, alias.name))
                self.bind(local, ('attr', alias.name))
            else:
                self.bind(local, None)

    # ---- scopes
    def visit_function(self, node):
        for decorator in getattr(node, 'decorator_list', []):
            self.visit(decorator)
        for default in node.args.defaults + [d for d in node.args.kw_defaults if d is not None]:
            self.visit(default)
        args = node.args
        names = [a.arg for a in args.posonlyargs + args.args + args.kwonlyargs]
        names += [a.arg for a in (args.vararg, args.kwarg) if a is not None]
        if not isinstance(node, ast.Lambda):
            self.bind(node.name, None)
        self.scopes.append({name: None for name in names})
        for statement in node.body if isinstance(node.body, list) else [node.body]:
            self.visit(statement)
        self.scopes.pop()

    visit_FunctionDef = visit_AsyncFunctionDef = visit_Lambda = visit_function

    def visit_ClassDef(self, node):
        for expression in node.decorator_list + node.bases + [k.value for k in node.keywords]:
            self.visit(expression)
        self.bind(node.name, None)
        self.scopes.append({})
        for statement in node.body:
            self.visit(statement)
        self.scopes.pop()

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store) and self.lookup(node.id) is not None:
            self.bind(node.id, None)

    # ---- uses
    def visit_Attribute(self, node):
        if self.is_module(node.value):
            kind = {ast.Load: 'load', ast.Store: 'store', ast.Del: 'del'}[type(node.ctx)]
            self.attributes.append((node.lineno, node.attr, kind))
            return
        self.generic_visit(node)

    def visit_Call(self, node):
        function = None
        if isinstance(node.func, ast.Attribute) and self.is_module(node.func.value):
            function = node.func.attr
        elif isinstance(node.func, ast.Name):
            meaning = self.lookup(node.func.id)
            if meaning and meaning[0] == 'attr':
                function = meaning[1]
        if function is not None:
            self.calls.append((node.lineno, function, node))
        self.generic_visit(node)


def scan(source, filename='<source>'):
    uses = HoldemUiUses()
    uses.visit(ast.parse(source, filename))
    return uses


def missing_attributes(uses):
    """'line N: ui.<name> (kind)' for every attribute the shared module doesn't have."""
    problems = [f'line {line}: import of {name}' for line, name in uses.imported
                if not hasattr(holdem_ui, name)]
    problems += [f'line {line}: ui.{name} ({kind})' for line, name, kind in uses.attributes
                 if not hasattr(holdem_ui, name)]
    problems += [f'line {line}: "import *" cannot be checked' for line in uses.star_imports]
    return problems


def bad_calls(uses):
    """'line N: name(...): reason' for every call the function's signature refuses."""
    problems = []
    placeholder = object()
    for line, name, call in uses.calls:
        function = getattr(holdem_ui, name, None)
        if function is None:
            problems.append(f'line {line}: {name} is not on {MODULE}')
            continue
        if not callable(function):
            problems.append(f'line {line}: {name} is not callable')
            continue
        try:
            signature = inspect.signature(function)
        except (TypeError, ValueError):
            continue
        parameters = signature.parameters.values()
        takes_any_keyword = any(p.kind is p.VAR_KEYWORD for p in parameters)
        keywords = [k.arg for k in call.keywords if k.arg is not None]
        refused = []
        for keyword in keywords:
            parameter = signature.parameters.get(keyword)
            accepted = (takes_any_keyword if parameter is None
                        else parameter.kind in (parameter.POSITIONAL_OR_KEYWORD, parameter.KEYWORD_ONLY))
            if not accepted:
                refused.append(f'line {line}: {name}() does not take {keyword}=')
        problems += refused
        unpacked = (any(isinstance(a, ast.Starred) for a in call.args)
                    or any(k.arg is None for k in call.keywords))
        if not refused and not unpacked:
            # The argument count must fit too (placeholders stand in for the values).
            try:
                signature.bind(*[placeholder] * len(call.args), **{k: placeholder for k in keywords})
            except TypeError as error:
                problems.append(f'line {line}: {name}(): {error}')
    return problems


def multiplayer_sources():
    files = sorted(MULTIPLAYER.glob('*.py')) + sorted((MULTIPLAYER / 'tests').glob('*.py'))
    for path in files:
        yield path.relative_to(ROOT).as_posix(), scan(path.read_text(encoding='utf-8'), str(path))


# The B85 call and the dead table-speed store, as they would look after the import switch.
BROKEN = '''
from solitaireplus.games.poker import holdem_ui as ui
from solitaireplus.games.poker.holdem_ui import draw_texas_holdem as draw, get_card_key
import solitaireplus.games.poker.holdem_ui

ui.holdem_table_speed = 'fast'
solitaireplus.games.poker.holdem_ui.holdem_log_scroll = 3
ui.get_holdem_npc_delay(pace='fast')
draw(None, show_utility_buttons=False)
get_card_key({'rank': 'A', 'suit': 'Spades'}, 'extra')

def hidden(ui, draw):
    ui.not_the_module = 1
    draw(colour='red')
'''


class SharedUiUsageTests(unittest.TestCase):
    def test_attributes_exist(self):
        self.assertFalse(OLD_COPY.exists())
        problems, seen = [], set()
        for name, uses in multiplayer_sources():
            problems += [f'{name} {problem}' for problem in missing_attributes(uses)]
            seen.update(attribute for _line, attribute, _kind in uses.attributes)
            seen.update(imported for _line, imported in uses.imported)
        self.assertEqual(problems, [])
        # Not vacuous: the room table's delays, the menus' buttons and the views' fonts were found.
        self.assertLessEqual({'get_holdem_npc_delay', 'get_holdem_street_delay', 'draw_holdem_glossy_button',
                              'get_card_key', 'get_holdem_fonts'}, seen)

    def test_keywords_accepted(self):
        problems, speed_calls = [], []
        for name, uses in multiplayer_sources():
            problems += [f'{name} {problem}' for problem in bad_calls(uses)]
            speed_calls += [(name, function) for _line, function, call in uses.calls
                            if any(k.arg == 'speed' for k in call.keywords)]
        self.assertEqual(problems, [])
        # The host's room clock passes its own table speed to both delays.
        self.assertLessEqual({('multiplayer/room_table.py', 'get_holdem_npc_delay'),
                              ('multiplayer/room_table.py', 'get_holdem_street_delay')}, set(speed_calls))

    def test_checker_finds_old_copy_uses(self):
        """The two checks above catch B85 and the dead table-speed store."""
        uses = scan(BROKEN)
        self.assertEqual(missing_attributes(uses), ['line 6: ui.holdem_table_speed (store)',
                                                    'line 7: ui.holdem_log_scroll (store)'])
        self.assertEqual(bad_calls(uses), ['line 8: get_holdem_npc_delay() does not take pace=',
                                           'line 9: draw_texas_holdem() does not take show_utility_buttons=',
                                           'line 10: get_card_key(): too many positional arguments'])

    def test_delays_follow_the_room_table_speed(self):
        """None means state.holdem_table_speed (single-player); the room clock passes its own."""
        saved = state.holdem_table_speed
        self.addCleanup(setattr, state, 'holdem_table_speed', saved)
        delays = (holdem_ui.get_holdem_npc_delay, holdem_ui.get_holdem_street_delay,
                  holdem_ui.get_holdem_next_hand_delay)
        state.holdem_table_speed = 'slow'
        self.assertEqual([delay() for delay in delays], [1800, 1700, 18000])
        self.assertEqual([delay(speed='fast') for delay in delays], [600, 950, 9000])
        self.assertEqual([delay(speed='normal') for delay in delays], [1200, 1200, 15000])

        random.seed(3)
        room = RoomAuthority('Host')
        self.assertEqual(room.table_speed, 'slow')        # the host's saved pace
        room.set_speed('fast')
        self.assertEqual(state.holdem_table_speed, 'fast')
        state.holdem_table_speed = 'slow'                 # the room keeps its own pace
        room.start()
        game = room.game
        for _ in range(10):
            if game.current_actor != 0 or game.is_betting_round_complete():
                break
            self.assertTrue(room.act(0, 'check_call', 0, room.revision))
        complete = game.is_betting_round_complete()
        self.assertTrue(complete or game.current_actor != 0)
        room.due = 0
        room.update(5000)
        self.assertEqual(room.due - 5000, 950 if complete else 600)

    def test_fonts_rebuilt_after_pygame_quit(self):
        """Multiplayer tests call pygame.quit() between tests; the cached fonts die with it."""
        self.addCleanup(pygame.init)
        for _ in range(2):                       # pygame forgets a quit hook once it has run
            pygame.init()
            fonts = holdem_ui.get_holdem_fonts()
            self.assertIs(holdem_ui.get_holdem_fonts(), fonts)
            pygame.quit()
            self.assertIsNone(holdem_ui._ui.holdem_fonts)
        pygame.init()
        self.assertIsNot(holdem_ui.get_holdem_fonts(), fonts)
        self.assertGreater(holdem_ui.get_holdem_fonts()['small'].render('Fold', True, (0, 0, 0)).get_width(), 0)

    def test_direct_font_clear_does_not_register_a_second_quit_hook(self):
        """Only pygame.quit() re-arms the hook: clearing the cache by hand keeps the one hook."""
        self.addCleanup(pygame.init)

        def forget_fonts():                      # the mocked registrations never reached pygame
            holdem_ui._ui.holdem_fonts = None
            holdem_ui._ui.holdem_fonts_quit_hooked = False
        self.addCleanup(forget_fonts)
        pygame.quit()                            # runs (and drops) any hook left by other tests
        forget_fonts()
        pygame.init()
        hooks = []
        with mock.patch.object(holdem_ui.pygame, 'register_quit', side_effect=hooks.append):
            holdem_ui.get_holdem_fonts()
            self.assertEqual(len(hooks), 1)
            holdem_ui.clear_holdem_fonts()
            self.assertIsNone(holdem_ui._ui.holdem_fonts)
            fonts = holdem_ui.get_holdem_fonts()
            self.assertEqual(len(hooks), 1, 'a direct clear registered a second quit hook')
            hooks[0]()                           # what pygame.quit() does with the hook
            self.assertIsNone(holdem_ui._ui.holdem_fonts)
            self.assertIsNot(holdem_ui.get_holdem_fonts(), fonts)
            self.assertEqual(len(hooks), 2, 'the hook must be registered again after a quit')
        pygame.quit()

    def test_multiplayer_import_does_not_start_single_player(self):
        # As multiplayer_launcher does: multiplayer/ first on the path, as an absolute
        # path (main's bootstrap() changes the working folder to the game folder).
        script = '''
import os
import sys
from pathlib import Path
sys.path.insert(0, os.getcwd())
import main
assert Path(main.__file__).resolve().parent.name == 'multiplayer', main.__file__
assert 'solitaireplus.games.poker.holdem_ui' in sys.modules
started = [name for name in ('solitaireplus.legacy', 'solitaireplus.ui.cursors') if name in sys.modules]
assert not started, started
'''
        with tempfile.TemporaryDirectory() as profile_dir:
            env = os.environ.copy()
            env.pop('PYTHONPATH', None)
            # Importing main runs bootstrap(), which writes a log under LOCALAPPDATA.
            env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', LOCALAPPDATA=profile_dir)
            result = subprocess.run([sys.executable, '-c', script], cwd=MULTIPLAYER, env=env,
                                    capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
