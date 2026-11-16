"""B59: the F10 debug menu's Close button must recapture the mouse in Dead Man's Hand.

Dead Man's Hand grabs and hides the mouse (mouse look). Opening the F10 debug menu releases it;
pressing F10 again goes back to the game and recaptures it, but the menu's Close button only
went back to the game, so the mouse stayed free and visible. Both ways back now share one
function (close_debug_menu in solitaireplus/debug/actions.py).

The Close tests start the game's modules headless (saves in a temporary folder) and click the
real debug menu screen. The F10 test runs the real main loop in a fake namespace (the helpers
of test_loop_mouse_and_screen_hooks).
"""
import ast
import os
import tempfile
import types
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

from tests.support import locate

LOOP_FILE = 'solitaireplus/app/loop.py'
MENU_SCREEN_FILE = 'solitaireplus/debug/menu_screen.py'


def click_event(pos):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)


class CloseButtonRecapturesTheMouse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.data = tempfile.TemporaryDirectory()
        cls.old_local_app_data = os.environ.get('LOCALAPPDATA')
        os.environ['LOCALAPPDATA'] = cls.data.name
        from solitaireplus.app import runtime_support
        saves = os.path.join(cls.data.name, 'saves')
        os.makedirs(saves, exist_ok=True)
        runtime_support.save_directory = lambda: saves
        from solitaireplus.app import startup  # noqa: F401 (the game's start-up, first, as in the game)
        from solitaireplus.app import sounds, state, state_names
        from solitaireplus.debug import menu, menu_screen
        from solitaireplus.games.dead_mans_hand import game_screen
        cls.sounds, cls.state, cls.names = sounds, state, state_names
        cls.menu, cls.menu_screen, cls.game_screen = menu, menu_screen, game_screen

    @classmethod
    def tearDownClass(cls):
        if cls.old_local_app_data is None:
            os.environ.pop('LOCALAPPDATA', None)
        else:
            os.environ['LOCALAPPDATA'] = cls.old_local_app_data
        cls.data.cleanup()

    def setUp(self):
        # Record what the game does to the real mouse instead of grabbing it.
        self.grabs, self.visible = [], []
        for patcher in (
                patch.object(pygame.event, 'set_grab', self.grabs.append),
                patch.object(pygame.mouse, 'set_visible', self.visible.append),
                patch.object(pygame.mouse, 'get_rel', lambda: (0, 0)),
                patch.object(self.sounds.audio, 'play_sound', lambda *a, **k: None),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        game = self.game_screen.dead_mans_hand_game
        game.release_mouse()
        del self.grabs[:], self.visible[:]
        self.addCleanup(game.release_mouse)
        self.state.debug_previous_state = None

    def open_debug_menu_like_f10(self):
        """What the F10 hotkey in app/loop.py does when the menu is not open."""
        state, names = self.state, self.names
        state.debug_previous_state = state.current_state
        if state.current_state == names.STATE_DEAD_MANS_HAND:
            self.game_screen.dead_mans_hand_game.release_mouse()
        state.current_state = names.STATE_DEBUG_MENU

    def click_close(self):
        state = self.state
        self.assertEqual(state.current_state, self.names.STATE_DEBUG_MENU)
        state.game_mouse_pos = (10, 10)
        with patch.object(self.menu_screen, 'get_debug_action', lambda pos: self.menu.ACTION_CLOSE):
            self.menu_screen.handle_event(click_event(state.game_mouse_pos))

    def test_close_from_dead_mans_hand_recaptures_the_mouse(self):
        state, names, game = self.state, self.names, self.game_screen.dead_mans_hand_game
        game.capture_mouse()                     # playing: the game holds the mouse
        state.current_state = names.STATE_DEAD_MANS_HAND
        self.open_debug_menu_like_f10()
        self.assertFalse(game._mouse_captured)
        self.assertEqual((self.grabs, self.visible), ([True, False], [False, True]))

        self.click_close()

        self.assertEqual(state.current_state, names.STATE_DEAD_MANS_HAND)
        self.assertTrue(game._mouse_captured, 'Close went back to Dead Man\'s Hand without the mouse')
        self.assertEqual(self.grabs[-1], True)
        self.assertEqual(self.visible[-1], False)

    def test_close_from_another_screen_leaves_the_mouse_alone(self):
        state, names, game = self.state, self.names, self.game_screen.dead_mans_hand_game
        state.current_state = names.STATE_MENU
        self.open_debug_menu_like_f10()

        self.click_close()

        self.assertEqual(state.current_state, names.STATE_MENU)
        self.assertFalse(game._mouse_captured)
        self.assertEqual((self.grabs, self.visible), ([], []))

    def test_close_without_a_previous_screen_stays_on_the_menu(self):
        state, names = self.state, self.names
        state.current_state = names.STATE_DEBUG_MENU
        state.debug_previous_state = None

        self.click_close()

        self.assertEqual(state.current_state, names.STATE_DEBUG_MENU)
        self.assertEqual(self.grabs, [])


class F10RecapturesTheMouse(unittest.TestCase):
    def test_f10_back_to_dead_mans_hand_recaptures_the_mouse(self):
        from solitaireplus.app import state_names
        from tests.app import test_loop_mouse_and_screen_hooks as loop_test

        log = []
        game = types.SimpleNamespace(capture_mouse=lambda: log.append('capture'),
                                     release_mouse=lambda: log.append('release'))
        module = types.SimpleNamespace(loop_event_dmh=lambda event: None)
        f10 = loop_test.key(pygame.KEYDOWN, pygame.K_F10)
        frames = [((0, 0), []), ((0, 0), [f10]), ((0, 0), [f10]), ((0, 0), [])]
        env = loop_test.loop_env(frames, module, {state_names.STATE_DEAD_MANS_HAND: 'dmh',
                                                  state_names.STATE_DEBUG_MENU: 'debug_menu'},
                                 state_names.STATE_DEAD_MANS_HAND)
        env['dead_mans_hand_game'] = game
        loop_test.run_loop(env)

        self.assertEqual(log, ['release', 'capture'])
        self.assertEqual(env['current_state'], state_names.STATE_DEAD_MANS_HAND)


def called_names(node):
    """Names of the functions a piece of code calls (f() or module.f())."""
    names = set()
    for call in ast.walk(node):
        if isinstance(call, ast.Call):
            func = call.func
            if isinstance(func, ast.Attribute):
                names.add(func.attr)
            elif isinstance(func, ast.Name):
                names.add(func.id)
    return names


class BothWaysBackShareOneFunction(unittest.TestCase):
    def test_f10_and_close_call_close_debug_menu(self):
        # The F10 hotkey's "menu is open" branch in the main loop ...
        loop_branches = [node for node in ast.walk(locate.function_node('run', path=LOOP_FILE))
                         if isinstance(node, ast.If) and 'STATE_DEBUG_MENU' in ast.unparse(node.test)
                         and 'current_state' in ast.unparse(node.test)]
        self.assertTrue(loop_branches, 'no "debug menu is open" branch found in the main loop')
        self.assertIn('close_debug_menu', called_names(loop_branches[0]))

        # ... and the menu's Close button.
        close_branches = [node for node in ast.walk(locate.function_node('handle_event', path=MENU_SCREEN_FILE))
                          if isinstance(node, ast.If) and 'ACTION_CLOSE' in ast.unparse(node.test)]
        self.assertTrue(close_branches, 'no Close branch found in the debug menu screen')
        close_body = ast.Module(body=close_branches[0].body, type_ignores=[])
        self.assertIn('close_debug_menu', called_names(close_body))


if __name__ == '__main__':
    unittest.main()
