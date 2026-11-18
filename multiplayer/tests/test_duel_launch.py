"""Multiplayer opens the shared Dead Man's Hand PvP lobby and draws its leave toast.

Since Phase 11 the PvP mode lives in solitaireplus/games/dead_mans_hand/pvp.py and has
no network code: multiplayer/main.py's make_duel() hands it net_client.open_peer, and
main() draws a LeaveToast over it. Host and Join are never clicked here, so no test
opens a connection or starts SolitaireNet.exe.
"""
import logging
import os
import tempfile
import unittest
from unittest.mock import patch

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

# Importing main runs runtime_support.bootstrap(), which opens a log file under
# %LOCALAPPDATA%. Each test file runs in its own process, so use a scratch folder.
_DATA = tempfile.TemporaryDirectory(prefix='duel_launch_', ignore_cleanup_errors=True)
_REAL_LOCALAPPDATA = os.environ.get('LOCALAPPDATA')
os.environ['LOCALAPPDATA'] = _DATA.name

import pygame

import main
import net_client
from mp_toast import LeaveToast
from solitaireplus.games.dead_mans_hand.pvp import DeadMansHandPvPMode
from solitaireplus.app import window

GOLD = (226, 191, 80)    # LeaveToast border colour
LOBBY = (17, 23, 27)     # duel lobby background
TOAST_TOP = (683, 92)    # top centre of the toast panel on the 1366x768 canvas
DMH_ROW = (672, 604)     # hub game list: "Dead Man's Hand PvP" (fifth row)
OPEN_LOBBY = (1147, 437)  # hub button "OPEN DUEL LOBBY", shown once that row is selected


def tearDownModule():
    # Close bootstrap()'s log so the scratch folder can be removed.
    root = logging.getLogger()
    folder = os.path.normcase(_DATA.name)
    for handler in list(root.handlers):
        if os.path.normcase(str(getattr(handler, 'baseFilename', ''))).startswith(folder):
            root.removeHandler(handler)
            handler.close()
    if _REAL_LOCALAPPDATA is None:
        os.environ.pop('LOCALAPPDATA', None)
    else:
        os.environ['LOCALAPPDATA'] = _REAL_LOCALAPPDATA
    _DATA.cleanup()


def wait_for_ticks():
    # LeaveToast treats a start time of 0 as "nothing to show".
    while pygame.time.get_ticks() == 0:
        pygame.time.wait(1)


class MakeDuelTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.display.set_mode((1366, 768))
        wait_for_ticks()

    def tearDown(self):
        pygame.quit()

    def test_make_duel_injects_net_client_open_peer(self):
        played = []
        mode, toast = main.make_duel('Hosty', 'tcp://127.0.0.1:50111', played.append)
        self.assertIsInstance(mode, DeadMansHandPvPMode)
        self.assertIsInstance(toast, LeaveToast)
        self.assertIs(mode._open_peer, net_client.open_peer)
        self.assertEqual((mode.name, mode.relay_address), ('Hosty', 'tcp://127.0.0.1:50111'))
        mode.sound('button_click')
        self.assertEqual(played, ['button_click'])
        # Opening the lobby connects nothing; that waits for Host or Join.
        self.assertIsNone(mode.peer)
        other_mode, other_toast = main.make_duel('Guesty', None, None)
        self.assertIsNot(other_mode, mode)
        self.assertIsNot(other_toast, toast)
        self.assertIs(other_mode._open_peer, net_client.open_peer)
        self.assertEqual(other_mode.relay_address, '')

    def test_leave_notice_makes_toast_visible(self):
        mode, toast = main.make_duel('Hosty', None, None)
        canvas = pygame.Surface((1366, 768))
        mode.draw(canvas, (0, 0))
        toast.sync(mode)
        toast.draw(canvas, mode.small)
        self.assertEqual(toast.text, '')
        self.assertEqual(tuple(canvas.get_at(TOAST_TOP))[:3], LOBBY)

        mode.leave_notice = 'X left the game.'
        mode.leave_notice_seq += 1
        toast.sync(mode)
        self.assertEqual(toast.text, 'X left the game.')
        mode.draw(canvas, (0, 0))
        toast.draw(canvas, mode.small)
        self.assertEqual(tuple(canvas.get_at(TOAST_TOP))[:3], GOLD)

        # The same notice does not restart the toast.
        started = toast.started
        pygame.time.wait(5)
        toast.sync(mode)
        self.assertEqual(toast.started, started)


class DuelLoopTests(unittest.TestCase):
    """Drive the real main() loop: hub -> duel lobby -> opponent leaves -> ESC -> hub."""

    def setUp(self):
        self.original_cwd = os.getcwd()
        pygame.init()
        pygame.display.set_mode((1366, 768))

    def tearDown(self):
        os.chdir(self.original_cwd)
        pygame.quit()

    def test_hub_opens_duel_and_draws_toast_until_closed(self):
        made = []
        real_make_duel = main.make_duel
        frame = [-1]

        def recording_make_duel(name, relay_address, sound):
            mode, toast = real_make_duel(name, relay_address, sound)
            record = {'args': (name, relay_address, sound), 'mode': mode, 'toast': toast, 'draws': []}
            real_draw = toast.draw

            def draw(surface, font):
                real_draw(surface, font)
                record['draws'].append((frame[0], surface, font, toast.text,
                                        tuple(surface.get_at(TOAST_TOP))[:3]))
            toast.draw = draw
            made.append(record)
            return mode, toast

        def click():
            return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(0, 0))

        frames = [  # (mouse position, events) for each pass of the loop
            ((0, 0), []),                       # 0: hub, Hold'em selected
            (DMH_ROW, [click()]),               # 1: select Dead Man's Hand PvP
            (OPEN_LOBBY, [click()]),            # 2: OPEN DUEL LOBBY -> make_duel
            ((0, 0), []),                       # 3: the opponent leaves (set in events())
            ((0, 0), [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]),  # 4: ESC
            ((0, 0), []),                       # 5: back on the hub
            ((0, 0), [pygame.event.Event(pygame.QUIT)]),
        ]

        def mouse_position():
            # main() reads the mouse once per pass, before the events.
            return frames[min(frame[0] + 1, len(frames) - 1)][0]

        def events(*_args, **_kwargs):
            frame[0] += 1
            if frame[0] == 3:
                mode = made[0]['mode']
                mode.leave_notice = 'Guesty left the game.'
                mode.leave_notice_seq += 1
            return frames[frame[0]][1]

        shown = {}

        def flip():
            # What the window shows at the toast's top edge once the whole pass has drawn.
            shown[frame[0]] = tuple(window.game_surface.get_at(TOAST_TOP))[:3]

        with tempfile.TemporaryDirectory() as folder, \
                patch.dict(os.environ, {'LOCALAPPDATA': folder}), \
                patch('pygame.event.get', side_effect=events), \
                patch('pygame.mouse.get_pos', side_effect=mouse_position), \
                patch('pygame.display.flip', side_effect=flip), \
                patch.object(window, '_current_picture_rect', return_value=pygame.Rect(0, 0, 1366, 768)), \
                patch.object(main, 'make_duel', recording_make_duel):
            # main() opens its own window through app/window.py (W1); positions above are game
            # coordinates, so the window-to-game mapping is pinned to 1:1.
            main.main()

        self.assertEqual(frame[0], len(frames) - 1)
        self.assertEqual(len(made), 1)
        record = made[0]
        mode, toast = record['mode'], record['toast']
        name, relay_address, sound = record['args']
        self.assertEqual(mode.name, name[:24])
        self.assertIsNone(relay_address)  # no saved relay: the default server
        self.assertTrue(callable(sound))
        self.assertIs(mode._open_peer, net_client.open_peer)
        self.assertIsNone(mode.peer)
        self.assertTrue(mode.closed)

        draws = record['draws']
        # Drawn on every pass while the duel is open, never after ESC closed it.
        self.assertEqual([d[0] for d in draws], [2, 3])
        for _frame, surface, font, _text, _pixel in draws:
            self.assertIs(font, mode.small)
            self.assertIs(surface, draws[0][1])
            self.assertEqual(surface.get_size(), (1366, 768))
        self.assertEqual(draws[0][3:], ('', LOBBY))
        self.assertEqual(draws[1][3:], ('Guesty left the game.', GOLD))
        self.assertEqual(toast.text, 'Guesty left the game.')
        # The toast is on top of the duel in the frame the player sees, and gone with it.
        self.assertEqual((shown[2], shown[3]), (LOBBY, GOLD))
        self.assertNotEqual(shown[5], GOLD)


if __name__ == '__main__':
    unittest.main()
