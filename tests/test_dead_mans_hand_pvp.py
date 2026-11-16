"""Dead Man's Hand PvP lives in the package (solitaireplus.games.dead_mans_hand.pvp).

multiplayer/main.py creates the mode and passes in the function that opens the
online connection (open_peer), so the module itself imports no network code.
These tests drive the mode with a fake connection: no sockets, no relay.
"""
import math
import os
from pathlib import Path
import queue
import subprocess
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from solitaireplus.games.dead_mans_hand import pvp
from solitaireplus.games.dead_mans_hand.levels import wall_at
from solitaireplus.games.dead_mans_hand.pvp import PVP_DAMAGE, SPAWNS, DeadMansHandPvPMode

ROOT = Path(__file__).resolve().parents[1]
MULTIPLAYER_ONLY = ("net_client", "mp_toast", "relay_transport")


class FakePeer:
    """Stands in for the relay connection open_peer returns."""

    def __init__(self, code="ABCDE"):
        self.inbox = queue.Queue()
        self.sent = []
        self.code = code
        self.closed = False

    def send(self, msg):
        self.sent.append(msg)

    def close(self):
        self.closed = True


class RecordingOpenPeer:
    """An injected open_peer that records its arguments and returns one FakePeer."""

    def __init__(self):
        self.calls = []
        self.peer = FakePeer()

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.peer


def click(mode, rect):
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)
    mode.handle_event(event, rect.center)


def type_text(mode, text):
    mode.handle_event(pygame.event.Event(pygame.TEXTINPUT, text=text), (0, 0))


def spot_in_front_of(x, y, angle, level):
    """A floor point a short way in front of (x, y), with a clear line of sight back."""
    for distance in (2.0, 1.5, 2.5, 1.0, 3.0):
        px = x + math.cos(angle) * distance
        py = y + math.sin(angle) * distance
        if wall_at(level, px, py) is None and pvp._los(level, px, py, x, y):
            return px, py
    raise AssertionError("no open floor in front of the spawn")


class DeadMansHandPvPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1366, 768))

    def host_after_hello(self, guest_name="Guesty"):
        opener = RecordingOpenPeer()
        mode = DeadMansHandPvPMode("Hosty", "", open_peer=opener)
        click(mode, mode.host_rect)
        opener.peer.inbox.put({"type": "hello", "name": guest_name})
        mode._process_network()
        self.assertTrue(mode.connected)
        # The 1-second spawn protection would hide every hit; switch it off first.
        for side in mode.authority:
            mode.authority[side]["protected_until"] = 0.0
        return mode, opener.peer

    def test_module_has_no_multiplayer_imports(self):
        # multiplayer/ goes on the path, so a stray import would succeed and show up in sys.modules.
        program = (
            "import sys\n"
            f"sys.path.append({str(ROOT / 'multiplayer')!r})\n"
            "import solitaireplus.games.dead_mans_hand.pvp\n"
            f"bad = sorted(name for name in {MULTIPLAYER_ONLY!r} if name in sys.modules)\n"
            "assert not bad, bad\n"
        )
        env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        env.pop("PYTHONPATH", None)
        result = subprocess.run([sys.executable, "-c", program], cwd=ROOT, env=env,
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_open_peer_injected_with_todays_arguments(self):
        host_opener = RecordingOpenPeer()
        host = DeadMansHandPvPMode("Hosty", "", open_peer=host_opener)
        self.assertIs(host._open_peer, host_opener)
        click(host, host.host_rect)
        self.assertEqual(host_opener.calls, [((True, None, "Hosty", ""), {"version": 1})])
        self.assertIs(host.peer, host_opener.peer)
        self.assertTrue(host.hosting)

        guest_opener = RecordingOpenPeer()
        guest = DeadMansHandPvPMode("Guesty", "tcp://127.0.0.1:50111", open_peer=guest_opener)
        click(guest, guest.code_rect)
        type_text(guest, "abcde")
        click(guest, guest.join_rect)
        self.assertEqual(guest_opener.calls,
                         [((False, "tcp://127.0.0.1:50111", "Guesty", "ABCDE"), {"version": 1})])
        self.assertFalse(guest.hosting)

    def test_no_open_peer_means_no_online_play(self):
        mode = DeadMansHandPvPMode("Hosty", "")
        click(mode, mode.host_rect)
        self.assertEqual(mode.status, "Online play is not available.")
        self.assertIsNone(mode.peer)
        self.assertIsNone(mode.game)
        self.assertFalse(mode.connected)

    def test_host_legal_shot_hits(self):
        mode, peer = self.host_after_hello()
        level = mode.game.level
        gx, gy, gangle = SPAWNS[1]
        peer.inbox.put({"type": "action", "action": "pose",
                        "pose": {"x": gx, "y": gy, "z": 0.0, "angle": gangle, "weapon": "pistol",
                                 "ads": 0.0, "dead": False}})
        mode._process_network()

        # The host stands in front of the guest pose, facing it, and fires.
        hx, hy = spot_in_front_of(gx, gy, gangle, level)
        mode.game.player_x, mode.game.player_y = hx, hy
        mode.game.player_angle = math.atan2(gy - hy, gx - hx)
        self.assertTrue(mode.game.fire())
        mode.update(0.0)
        self.assertEqual(mode.authority[1]["health"], 100 - PVP_DAMAGE["pistol"])
        hits = [e for e in mode.event_log if e["kind"] == "hit"]
        self.assertEqual([(e["shooter"], e["target"]) for e in hits], [(0, 1)])

        # The guest fires back from its own pose at the host: the host confirms that hit too.
        peer.inbox.put({"type": "action", "action": "shot",
                        "shot": {"weapon": "pistol", "x": gx, "y": gy, "z": 0.0,
                                 "angle": math.atan2(hy - gy, hx - gx)}})
        mode._process_network()
        self.assertEqual(mode.authority[0]["health"], 100 - PVP_DAMAGE["pistol"])
        self.assertEqual(mode.game.health, 100 - PVP_DAMAGE["pistol"])

    def test_disconnect_sets_leave_notice(self):
        mode, peer = self.host_after_hello("Guesty")
        seq = mode.leave_notice_seq
        peer.inbox.put({"type": "disconnected", "text": "Other player disconnected."})
        mode._process_network()
        self.assertFalse(mode.connected)
        self.assertEqual(mode.leave_notice, "Guesty left the game.")
        self.assertEqual(mode.leave_notice_seq, seq + 1)

    def test_disconnect_before_hello_sets_no_leave_notice(self):
        opener = RecordingOpenPeer()
        mode = DeadMansHandPvPMode("Hosty", "", open_peer=opener)
        click(mode, mode.host_rect)
        opener.peer.inbox.put({"type": "disconnected", "text": "Could not reach the server."})
        mode._process_network()
        self.assertEqual(mode.leave_notice, "")
        self.assertEqual(mode.leave_notice_seq, 0)
        self.assertEqual(mode.status, "Could not reach the server.")

    def test_draw_lobby_and_match_without_a_toast(self):
        # The leave toast now belongs to multiplayer/main.py; the mode draws without one.
        canvas = pygame.Surface((1366, 768))
        lobby = DeadMansHandPvPMode("Hosty", "", open_peer=RecordingOpenPeer())
        self.assertFalse(hasattr(lobby, "leave_toast"))
        lobby.draw(canvas, (0, 0))
        mode, _peer = self.host_after_hello()
        mode.draw(canvas, (0, 0))


if __name__ == "__main__":
    unittest.main()
