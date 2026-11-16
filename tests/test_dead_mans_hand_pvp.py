"""Dead Man's Hand PvP lives in the package (solitaireplus.games.dead_mans_hand.pvp).

multiplayer/main.py creates the mode and passes in the function that opens the
online connection (open_peer), so the module itself imports no network code.
These tests drive the mode with a fake connection: no sockets, no relay.

B82: the host checks every guest pose and shot (types, ranges, walls, speed,
shot origin, fire rate) and ignores bad ones; the guest ignores bad host data.
B83: a disconnect after hello ends the duel on a result screen.
The 1-second spawn protection would hide every hit, so the tests switch it off.
"""
import json
import math
import os
from pathlib import Path
import queue
import subprocess
import sys
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from solitaireplus.games.dead_mans_hand import pvp
from solitaireplus.games.dead_mans_hand.levels import wall_at
from solitaireplus.games.dead_mans_hand.pvp import PVP_DAMAGE, SPAWNS, DeadMansHandPvPMode
from solitaireplus.ui import text as ui_text

ROOT = Path(__file__).resolve().parents[1]
MULTIPLAYER_ONLY = ("net_client", "mp_toast", "relay_transport")
RELAY_LEFT_TEXT = "Other player disconnected. Table paused; create a new room."
LOBBY_COLOUR = (17, 23, 27)


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


class FakeClock:
    """Replaces time.monotonic so the tests set the time between network messages."""

    def __init__(self, start=1000.0):
        self.now = float(start)

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class RecordingFont:
    """Wraps a real font and records every text it renders."""

    def __init__(self, font, texts):
        self._font = font
        self._texts = texts

    def render(self, text, *args, **kwargs):
        self._texts.append(str(text))
        return self._font.render(text, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._font, name)


def record_texts(mode):
    """Make the mode and its game record what they draw; returns the list of texts."""
    texts = []
    for name in ("font", "small", "title"):
        setattr(mode, name, RecordingFont(getattr(mode, name), texts))
    game = mode.game
    if game is not None:
        font, dmh_font = game._font, game._dmh_font
        game._font = lambda *a, **k: RecordingFont(font(*a, **k), texts)
        game._dmh_font = lambda *a, **k: RecordingFont(dmh_font(*a, **k), texts)
    return texts


def pose(x, y, angle=0.0, weapon="pistol", z=0.0, ads=0.0, dead=False):
    return {"x": x, "y": y, "z": z, "angle": angle, "weapon": weapon, "ads": ads, "dead": dead}


def send_pose(mode, peer, data):
    peer.inbox.put({"type": "action", "action": "pose", "pose": data})
    mode._process_network()


def send_shot(mode, peer, data):
    peer.inbox.put({"type": "action", "action": "shot", "shot": data})
    mode._process_network()


def shot_events(mode, side=1):
    return [e for e in mode.event_log if e["kind"] == "shot" and e.get("side") == side]


def hit_events(mode):
    return [e for e in mode.event_log if e["kind"] == "hit"]


def host_facing_guest_spawn(mode):
    """Stand the host 2 tiles in front of the guest spawn; returns the guest's aim at the host."""
    gx, gy, gangle = SPAWNS[1]
    hx, hy = spot_in_front_of(gx, gy, gangle, mode.game.level)
    mode.game.player_x, mode.game.player_y = hx, hy
    mode.game.player_angle = math.atan2(gy - hy, gx - hx)
    return math.atan2(hy - gy, hx - gx)


def guest_after_hello(host_name="Hosty"):
    opener = RecordingOpenPeer()
    mode = DeadMansHandPvPMode("Guesty", "", open_peer=opener)
    click(mode, mode.code_rect)
    type_text(mode, "abcde")
    click(mode, mode.join_rect)
    opener.peer.inbox.put({"type": "hello", "name": host_name})
    mode._process_network()
    assert mode.connected
    return mode, opener


class PvPCase(unittest.TestCase):
    """Shared set-up; holds no tests itself."""

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

    def guest_at_spawn(self, mode, peer):
        """The guest's first pose: at its spawn, facing the way it spawns."""
        gx, gy, gangle = SPAWNS[1]
        send_pose(mode, peer, pose(gx, gy, gangle))
        self.assertIsNotNone(mode.remote_pose)
        return gx, gy

    def assert_unhurt(self, mode):
        self.assertEqual(mode.authority[0]["health"], 100)
        self.assertEqual(mode.game.health, 100)
        self.assertEqual(hit_events(mode), [])


class DeadMansHandPvPTests(PvPCase):
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
        # B83: no result screen before hello; today's lobby stays.
        self.assertFalse(mode.finished)
        self.assertFalse(mode.game.match_over)
        self.assertIs(mode.peer, opener.peer)
        canvas = pygame.Surface((1366, 768))
        texts = record_texts(mode)
        mode.draw(canvas, (0, 0))
        self.assertIn("Could not reach the server.", texts)
        self.assertEqual(canvas.get_at((5, 760))[:3], LOBBY_COLOUR)

    def test_draw_lobby_and_match_without_a_toast(self):
        # The leave toast now belongs to multiplayer/main.py; the mode draws without one.
        canvas = pygame.Surface((1366, 768))
        lobby = DeadMansHandPvPMode("Hosty", "", open_peer=RecordingOpenPeer())
        self.assertFalse(hasattr(lobby, "leave_toast"))
        lobby.draw(canvas, (0, 0))
        mode, _peer = self.host_after_hello()
        mode.draw(canvas, (0, 0))


NAN, INF = float("nan"), float("inf")


class HostChecksGuestDataTests(PvPCase):
    """B82: the host ignores malformed, impossible or too fast guest poses and shots."""

    def test_malformed_shots_raise_nothing_and_do_no_damage(self):
        mode, peer = self.host_after_hello()
        gx, gy = self.guest_at_spawn(mode, peer)
        aim = host_facing_guest_spawn(mode)
        good = {"weapon": "pistol", "x": gx, "y": gy, "z": 0.0, "angle": aim}
        without = lambda key: {k: v for k, v in good.items() if k != key}  # noqa: E731
        bad_shots = [
            "abc", "ab", 5, [1, 2], None, {}, True,
            dict(good, x="abc"), dict(good, angle=None), dict(good, x=NAN), dict(good, y=INF),
            dict(good, angle=NAN), dict(good, angle=INF), dict(good, angle="0"), dict(good, z="ab"),
            dict(good, z=NAN), dict(good, x=[1, 2]), dict(good, x=True), dict(good, x=10 ** 400),
            dict(good, weapon="bazooka"), dict(good, weapon=5), dict(good, weapon=["pistol"]),
            dict(good, weapon=None), without("angle"), without("weapon"), without("x"),
            dict(good, x=gx + 0.7), dict(good, y=gy + 0.6),  # inside the arena wall next to the spawn
            dict(good, x=-3.0),  # off the map
        ]
        canvas = pygame.Surface((1366, 768))
        for bad in bad_shots:
            with self.subTest(shot=bad):
                send_shot(mode, peer, bad)
                mode.update(0.0)
                mode.draw(canvas, (0, 0))
                self.assert_unhurt(mode)
                self.assertEqual(shot_events(mode), [])
        # The same set-up with a good shot does hit, so the shots above were really refused.
        send_shot(mode, peer, good)
        self.assertEqual(mode.authority[0]["health"], 100 - PVP_DAMAGE["pistol"])
        self.assertEqual(len(shot_events(mode)), 1)

    def test_malformed_poses_raise_nothing_and_keep_the_last_good_pose(self):
        mode, peer = self.host_after_hello()
        gx, gy = self.guest_at_spawn(mode, peer)
        kept = dict(mode.remote_pose)
        good = pose(gx, gy, 0.0)
        bad_poses = [
            "abc", "ab", 5, [1, 2], None, {}, True,
            dict(good, x="abc"), dict(good, y=None), dict(good, x=NAN), dict(good, y=INF),
            dict(good, angle=NAN), dict(good, angle="0"), dict(good, z=[1]), dict(good, ads="x"),
            dict(good, ads=NAN), dict(good, angle=True), dict(good, ads=True),  # JSON true is not a number
            dict(good, weapon="bazooka"), dict(good, weapon=7),
            dict(good, x=gx + 0.7), dict(good, y=gy + 0.6),  # inside the arena wall
            dict(good, x=25.0), dict(good, y=-1.0),  # off the map
        ]
        canvas = pygame.Surface((1366, 768))
        for bad in bad_poses:
            with self.subTest(pose=bad):
                send_pose(mode, peer, bad)
                mode.update(0.0)
                mode.draw(canvas, (0, 0))
                self.assertEqual(mode.remote_pose, kept)
                self.assert_unhurt(mode)
        # The host's shot at the kept pose still lands: a bad pose cannot move or hide the guest.
        host_facing_guest_spawn(mode)
        self.assertTrue(mode.game.fire())
        mode.update(0.0)
        self.assertEqual(mode.authority[1]["health"], 100 - PVP_DAMAGE["pistol"])

    def test_pose_is_clamped_and_teleports_are_refused(self):
        clock = FakeClock()
        with mock.patch.object(pvp.time, "monotonic", clock):
            mode, peer = self.host_after_hello()
            gx, gy, gangle = SPAWNS[1]
            # Extra keys are dropped, z and ads are clamped and the angle is normalised.
            send_pose(mode, peer, dict(pose(gx, gy, gangle + 2 * math.pi, z=5.0, ads=7.0),
                                       health=999, score=5, protected=True, respawn=True))
            remote = mode.remote_pose
            self.assertEqual(set(remote), {"x", "y", "z", "angle", "weapon", "ads", "dead"})
            self.assertAlmostEqual(remote["z"], pvp.JUMP_IMPULSE ** 2 / (2 * pvp.JUMP_GRAVITY) + 0.05)
            self.assertEqual(remote["ads"], 1.0)
            self.assertAlmostEqual(remote["angle"], gangle)
            # Claiming z=5 no longer dodges the hitscan (the jump dodge needs z > .72).
            host_facing_guest_spawn(mode)
            self.assertTrue(mode.game.fire())
            mode.update(0.0)
            self.assertEqual(mode.authority[1]["health"], 100 - PVP_DAMAGE["pistol"])

            # A teleport across the arena is refused; a walking step is accepted.
            far = (2.5, 13.5)
            self.assertIsNone(wall_at(mode.game.level, *far))
            send_pose(mode, peer, pose(*far))
            self.assertEqual((mode.remote_pose["x"], mode.remote_pose["y"]), (gx, gy))
            clock.advance(0.05)
            step = (gx - 0.1, gy)
            send_pose(mode, peer, pose(*step))
            self.assertEqual((mode.remote_pose["x"], mode.remote_pose["y"]), step)
            # With enough time gone by, the same distance is a walk again.
            clock.advance(5.0)
            send_pose(mode, peer, pose(*far))
            self.assertEqual((mode.remote_pose["x"], mode.remote_pose["y"]), far)

            # While the guest is dead its poses are ignored.
            mode.authority[1]["health"] = 0
            mode.authority[1]["dead_until"] = clock.now + pvp.RESPAWN_SECONDS
            clock.advance(0.05)
            send_pose(mode, peer, pose(far[0] + 0.1, far[1]))
            self.assertEqual((mode.remote_pose["x"], mode.remote_pose["y"]), far)

    def test_first_pose_after_a_respawn_is_measured_from_the_spawn(self):
        clock = FakeClock()
        with mock.patch.object(pvp.time, "monotonic", clock):
            mode, peer = self.host_after_hello()
            self.guest_at_spawn(mode, peer)
            level = mode.game.level
            # The guest walks across the arena (time passes, so the long move is allowed).
            death = (14.5, 9.5)  # about 6.4 tiles from the guest spawn
            clock.advance(5.0)
            send_pose(mode, peer, pose(*death))
            self.assertEqual((mode.remote_pose["x"], mode.remote_pose["y"]), death)
            # The host kills it there with three pistol shots.
            hx, hy = spot_in_front_of(death[0], death[1], 0.0, level)
            mode.game.player_x, mode.game.player_y = hx, hy
            mode.game.player_angle = math.atan2(death[1] - hy, death[0] - hx)
            for _ in range(3):
                mode.game.shot_timer = 0.0
                self.assertTrue(mode.game.fire())
                mode.update(0.0)
            self.assertEqual(mode.authority[1]["health"], 0)
            # Its poses while dead are ignored.
            clock.advance(0.05)
            send_pose(mode, peer, pose(death[0] + 0.1, death[1], dead=True))
            self.assertEqual((mode.remote_pose["x"], mode.remote_pose["y"]), death)

            # The host respawns it at its spawn.
            clock.advance(pvp.RESPAWN_SECONDS + 0.1)
            mode.update(0.0)
            self.assertTrue(peer.sent[-1]["guest"]["respawn"])
            gx, gy, gangle = SPAWNS[1]
            self.assertEqual((mode.remote_pose["x"], mode.remote_pose["y"]), (gx, gy))
            # A pose sent before the guest saw the respawn (still at the death spot) is refused...
            clock.advance(0.03)
            send_pose(mode, peer, pose(*death, dead=True))
            self.assertEqual((mode.remote_pose["x"], mode.remote_pose["y"]), (gx, gy))
            # ...and its first real pose, at the spawn, is accepted.
            clock.advance(0.05)
            send_pose(mode, peer, pose(gx - 0.05, gy, gangle))
            self.assertEqual((mode.remote_pose["x"], mode.remote_pose["y"]), (gx - 0.05, gy))
            # It can shoot from there straight away.
            send_shot(mode, peer, {"weapon": "pistol", "x": gx - 0.05, "y": gy, "z": 0.0, "angle": gangle})
            self.assertEqual(len(shot_events(mode)), 1)

    def test_stale_dead_pose_near_the_spawn_does_not_undo_the_respawn(self):
        # The guest died 1.2 tiles from its spawn: close enough that a pose from there
        # passes the speed check a quarter of a second after the respawn.
        clock = FakeClock()
        with mock.patch.object(pvp.time, "monotonic", clock):
            mode, peer = self.host_after_hello()
            gx, gy = self.guest_at_spawn(mode, peer)
            gangle = SPAWNS[1][2]
            death = (gx - 1.2, gy)
            self.assertIsNone(wall_at(mode.game.level, *death))
            clock.advance(1.0)
            send_pose(mode, peer, pose(*death))
            self.assertEqual((mode.remote_pose["x"], mode.remote_pose["y"]), death)
            mode.authority[1]["health"] = 0
            mode.authority[1]["dead_until"] = clock.now + pvp.RESPAWN_SECONDS
            clock.advance(pvp.RESPAWN_SECONDS + 0.01)
            mode.update(0.0)
            self.assertTrue(peer.sent[-1]["guest"]["respawn"])
            self.assertEqual((mode.remote_pose["x"], mode.remote_pose["y"]), (gx, gy))
            # One round trip later the guest's last pose from before the respawn arrives.
            clock.advance(0.25)
            send_pose(mode, peer, pose(*death, dead=True))
            self.assertEqual((mode.remote_pose["x"], mode.remote_pose["y"]), (gx, gy))
            # Its real poses and shots from the spawn are accepted at once.
            clock.advance(0.05)
            send_pose(mode, peer, pose(gx, gy, gangle))
            send_shot(mode, peer, {"weapon": "pistol", "x": gx, "y": gy, "z": 0.0, "angle": gangle})
            self.assertEqual(len(shot_events(mode)), 1)

    def test_three_shot_burst_gives_at_most_two_hits(self):
        clock = FakeClock()
        with mock.patch.object(pvp.time, "monotonic", clock):
            mode, peer = self.host_after_hello()
            gx, gy = self.guest_at_spawn(mode, peer)
            aim = host_facing_guest_spawn(mode)
            shot = {"weapon": "pistol", "x": gx, "y": gy, "z": 0.0, "angle": aim}
            for _ in range(3):
                peer.inbox.put({"type": "action", "action": "shot", "shot": dict(shot)})
            mode._process_network()
            self.assertEqual(len(hit_events(mode)), 2)
            self.assertEqual(len(shot_events(mode)), 2)
            self.assertEqual(mode.authority[0]["health"], 100 - 2 * PVP_DAMAGE["pistol"])
            # One pistol interval later the next shot is accepted again.
            clock.advance(pvp.WEAPON_DEFINITIONS["pistol"]["fire_interval"])
            send_shot(mode, peer, dict(shot))
            self.assertEqual(len(shot_events(mode)), 3)
            self.assertEqual(mode.authority[0]["health"], 0)

    def shots_accepted(self, mode, peer, clock, plan):
        """Send (weapon, wait) shots that all miss; returns how many the host accepted."""
        gx, gy = mode.remote_pose["x"], mode.remote_pose["y"]
        away = SPAWNS[1][2] + math.pi  # towards the corner wall behind the guest spawn
        before = mode.event_seq
        for weapon, wait in plan:
            clock.advance(wait)
            send_shot(mode, peer, {"weapon": weapon, "x": gx, "y": gy, "z": 0.0, "angle": away})
        self.assert_unhurt(mode)
        return mode.event_seq - before  # every event here is a 'shot'

    def test_thompson_at_its_fire_interval_is_not_dropped(self):
        clock = FakeClock()
        with mock.patch.object(pvp.time, "monotonic", clock):
            mode, peer = self.host_after_hello()
            self.guest_at_spawn(mode, peer)
            interval = pvp.WEAPON_DEFINITIONS["thompson"]["fire_interval"]
            self.assertEqual(interval, 0.085)
            self.assertEqual(self.shots_accepted(mode, peer, clock, [("thompson", interval)] * 30), 30)
            # Faster than the gun can fire, only some get through (2 at once, then 1 per 0.085 s).
            clock.advance(1.0)
            self.assertEqual(self.shots_accepted(mode, peer, clock, [("thompson", 0.02)] * 10), 4)

    def test_switching_guns_at_game_speed_is_not_dropped(self):
        # All guns share one shot timer: after a Thompson shot any gun may fire 0.085 s later,
        # after a pistol shot 0.245 s later, and the Kar98k's bolt blocks switching for 0.82 s.
        clock = FakeClock()
        with mock.patch.object(pvp.time, "monotonic", clock):
            mode, peer = self.host_after_hello()
            self.guest_at_spawn(mode, peer)
            plan = [("thompson", 0.0), ("thompson", 0.085), ("pistol", 0.085), ("kar98k", 0.245),
                    ("pistol", 0.82), ("scar20", 0.245), ("kar98k", 0.31), ("thompson", 0.82)]
            self.assertEqual(self.shots_accepted(mode, peer, clock, plan), len(plan))

    def test_shot_from_far_away_from_the_guest_misses(self):
        mode, peer = self.host_after_hello()
        self.guest_at_spawn(mode, peer)
        # The shot claims to come from 2 tiles in front of the host, far from the guest's pose.
        hx, hy, hangle = SPAWNS[0]
        ox, oy = spot_in_front_of(hx, hy, hangle, mode.game.level)
        send_shot(mode, peer, {"weapon": "pistol", "x": ox, "y": oy, "z": 0.0,
                               "angle": math.atan2(hy - oy, hx - ox)})
        self.assert_unhurt(mode)
        self.assertEqual(shot_events(mode), [])

    def test_shot_before_any_pose_is_ignored(self):
        mode, peer = self.host_after_hello()
        gx, gy, _angle = SPAWNS[1]
        aim = host_facing_guest_spawn(mode)
        send_shot(mode, peer, {"weapon": "pistol", "x": gx, "y": gy, "z": 0.0, "angle": aim})
        self.assert_unhurt(mode)
        self.assertEqual(shot_events(mode), [])

    def test_shot_hits_is_false_for_bad_numbers(self):
        level = pvp.LEVELS[pvp.ARENA_LEVEL_INDEX]
        gx, gy, gangle = SPAWNS[1]
        hx, hy = spot_in_front_of(gx, gy, gangle, level)
        shooter = {"x": gx, "y": gy, "angle": math.atan2(hy - gy, hx - gx)}
        target = {"x": hx, "y": hy, "z": 0.0}
        self.assertTrue(pvp._shot_hits(level, shooter, target))
        for key, value in (("x", "abc"), ("x", None), ("x", NAN), ("y", INF), ("angle", NAN),
                           ("angle", INF), ("angle", [1]), ("x", 10 ** 400)):
            with self.subTest(shooter_key=key, value=value):
                self.assertFalse(pvp._shot_hits(level, dict(shooter, **{key: value}), target))
        for key, value in (("x", "abc"), ("y", NAN), ("z", INF), ("z", "ab"), ("z", None)):
            with self.subTest(target_key=key, value=value):
                self.assertFalse(pvp._shot_hits(level, shooter, dict(target, **{key: value})))

    def test_actions_before_hello_are_ignored(self):
        opener = RecordingOpenPeer()
        mode = DeadMansHandPvPMode("Hosty", "", open_peer=opener)
        click(mode, mode.host_rect)
        gx, gy, gangle = SPAWNS[1]
        send_pose(mode, opener.peer, pose(gx, gy, gangle))
        self.assertIsNone(mode.remote_pose)
        self.assertEqual(mode.event_log, [])

    def test_second_hello_changes_nothing(self):
        mode, peer = self.host_after_hello("Guesty")
        mode.update(0.0)  # copies the switched-off protection into the game
        self.assertEqual(mode.game.spawn_protection_timer, 0.0)
        status = mode.status
        peer.inbox.put({"type": "hello", "name": "Mallory"})
        mode._process_network()
        self.assertEqual(mode.remote_name, "Guesty")
        self.assertEqual(mode.game.remote_name, "Guesty")
        self.assertEqual(mode.status, status)
        self.assertEqual([a["protected_until"] for a in mode.authority.values()], [0.0, 0.0])
        self.assertEqual(mode.game.spawn_protection_timer, 0.0)
        # The guest ignores a second hello as well.
        guest, opener = guest_after_hello("Hosty")
        guest.game.spawn_protection_timer = 0.0
        opener.peer.inbox.put({"type": "hello", "name": "Mallory"})
        guest._process_network()
        self.assertEqual(guest.remote_name, "Hosty")
        self.assertEqual(guest.game.remote_name, "Hosty")
        self.assertEqual(guest.game.spawn_protection_timer, 0.0)


class LinkedPeer(FakePeer):
    """One end of a fake relay: what it sends arrives, as JSON, in the other end's inbox."""

    def __init__(self):
        super().__init__()
        self.other = None

    def send(self, msg):
        super().send(msg)
        self.other.inbox.put(json.loads(json.dumps(msg)))


class HeldKeys:
    def __init__(self, *held):
        self.held = set(held)

    def __getitem__(self, key):
        return key in self.held


class RealTrafficTests(PvPCase):
    """A real guest's poses and shots pass the host's checks (nothing legal is dropped)."""

    def test_walking_and_full_auto_from_a_real_guest_are_accepted(self):
        clock = FakeClock()
        host_peer, guest_peer = LinkedPeer(), LinkedPeer()
        host_peer.other, guest_peer.other = guest_peer, host_peer
        with mock.patch.object(pvp.time, "monotonic", clock):
            host = DeadMansHandPvPMode("Hosty", "", open_peer=lambda *a, **k: host_peer)
            guest = DeadMansHandPvPMode("Guesty", "", open_peer=lambda *a, **k: guest_peer)
            click(host, host.host_rect)
            click(guest, guest.code_rect)
            type_text(guest, "ABCDE")
            click(guest, guest.join_rect)
            host_peer.inbox.put({"type": "hello", "name": "Guesty"})
            guest_peer.inbox.put({"type": "hello", "name": "Hosty"})
            for side in host.authority:
                host.authority[side]["protected_until"] = 0.0

            def frame(guest_keys=HeldKeys()):
                clock.advance(1 / 60)
                with mock.patch.object(pygame.key, "get_pressed", lambda: guest_keys):
                    guest.update(1 / 60)
                with mock.patch.object(pygame.key, "get_pressed", lambda: HeldKeys()):
                    host.update(1 / 60)

            # The guest walks forward for a second and strafes for half a second.
            for _ in range(60):
                frame(HeldKeys(pygame.K_w))
            for _ in range(30):
                frame(HeldKeys(pygame.K_w, pygame.K_d))
            frame()
            g = guest.game
            self.assertGreater(math.hypot(g.player_x - SPAWNS[1][0], g.player_y - SPAWNS[1][1]), 2.0)
            self.assertLess(math.hypot(host.remote_pose["x"] - g.player_x, host.remote_pose["y"] - g.player_y), 0.1)

            # Full auto with the Thompson, aimed away from the host: every shot reaches the host.
            g.switch_weapon("thompson")
            g.player_angle = math.atan2(host.game.player_y - g.player_y, host.game.player_x - g.player_x) + math.pi
            before = host.event_seq
            sent_before = sum(1 for m in guest_peer.sent if m.get("action") == "shot")
            g.set_trigger_held(True)
            g.fire()
            for _ in range(60):
                frame()
            g.set_trigger_held(False)
            frame()
            fired = sum(1 for m in guest_peer.sent if m.get("action") == "shot") - sent_before
            self.assertGreaterEqual(fired, 9)
            self.assertEqual(host.event_seq - before, fired)

            # A guest shot at the host lands, and the guest is told about the hit.
            hx, hy = spot_in_front_of(g.player_x, g.player_y, g.player_angle, host.game.level)
            host.game.player_x, host.game.player_y = hx, hy
            g.switch_weapon("pistol")
            g.player_angle = math.atan2(hy - g.player_y, hx - g.player_x)
            for _ in range(30):
                frame()  # let the reload and shot timers run out
            self.assertTrue(g.fire())
            markers = []
            for _ in range(6):  # the host's next state message carries the hit back
                frame()
                markers.append(g.hit_marker_timer)
            self.assertEqual(host.authority[0]["health"], 100 - PVP_DAMAGE["pistol"])
            self.assertEqual(host.game.health, 100 - PVP_DAMAGE["pistol"])
            self.assertEqual(g.health, 100)
            self.assertGreater(max(markers), 0.0)


class GuestChecksHostDataTests(PvPCase):
    """B82, guest side: malformed host messages are ignored instead of crashing the guest."""

    def test_guest_ignores_malformed_host_messages(self):
        mode, opener = guest_after_hello()
        peer = opener.peer
        hx, hy, hangle = SPAWNS[0]
        host = dict(pose(hx, hy, hangle), health=100, score=0, protected=False, respawn=False)
        guest = {"health": 100, "score": 0, "dead": False, "respawn": False, "respawn_in": 0.0,
                 "protection_in": 0.0}
        good = {"type": "state", "host": host, "guest": guest, "host_name": "Hosty", "events": [],
                "match_over": False}
        bad_messages = [
            "abc", 5, None, [1, 2],
            dict(good, host="abc"), dict(good, guest=5), dict(good, host=None), dict(good, guest=[1, 2]),
            dict(good, host=dict(host, x="abc")), dict(good, host=dict(host, y=NAN)),
            dict(good, host=dict(host, angle=None)), dict(good, host=dict(host, z=INF)),
            dict(good, host=dict(host, health="abc")), dict(good, host=dict(host, health=NAN)),
            dict(good, host=dict(host, weapon=[1])), dict(good, host=dict(host, ads="x")),
            dict(good, guest=dict(guest, health="abc")), dict(good, guest=dict(guest, score=None)),
            dict(good, guest=dict(guest, score=INF)),
            dict(good, guest=dict(guest, dead=True, respawn_in=INF)),
            dict(good, guest=dict(guest, dead=True, respawn_in="x")),
            dict(good, guest=dict(guest, protection_in=NAN)),
            dict(good, guest=dict(guest, respawn=True, protection_in="x")),
            dict(good, events=[5, "x", None, [1], {"seq": "abc"}, {"seq": NAN}, {"seq": INF},
                               {"seq": 1, "kind": "hit", "shooter": "abc", "target": 1},
                               {"seq": 2, "kind": "hit", "shooter": 0, "target": None},
                               {"seq": 3, "kind": "hit", "shooter": INF, "target": 1},
                               {"seq": 4, "kind": "shot", "side": [0]}]),
            dict(good, events="abc"),
            {"type": "status", "text": 5},
        ]
        canvas = pygame.Surface((1366, 768))
        for bad in bad_messages:
            with self.subTest(message=bad):
                peer.inbox.put(bad)
                mode._process_network()
                mode.update(0.0)
                mode.draw(canvas, (0, 0))
                self.assertIsInstance(mode.status, str)
        # A good state still applies afterwards, events included.
        peer.inbox.put(dict(good, guest=dict(guest, health=66, score=2), host=dict(host, score=1),
                            events=[{"seq": 50, "kind": "hit", "shooter": 0, "target": 1,
                                     "weapon": "pistol", "killed": False}]))
        mode._process_network()
        self.assertEqual(mode.game.health, 66)
        self.assertEqual((mode.game.local_score, mode.game.remote_score), (2, 1))
        self.assertGreater(mode.game.damage_flash_timer, 0.0)
        mode.update(0.0)
        mode.draw(canvas, (0, 0))


def good_state(**extra):
    """A well-formed host state message, as the guest receives it."""
    hx, hy, hangle = SPAWNS[0]
    message = {
        "type": "state",
        "host": dict(pose(hx, hy, hangle), health=100, score=0, protected=False, respawn=False),
        "guest": {"health": 100, "score": 0, "dead": False, "respawn": False, "respawn_in": 0.0,
                  "protection_in": 0.0},
        "host_name": "Hosty", "events": [], "match_over": False,
    }
    message.update(extra)
    return message


class PeerTextTests(PvPCase):
    """B82, text: names and gun names from the other side are drawn on every frame, and
    pygame cannot render a NUL or a lone surrogate (both survive JSON)."""

    SURROGATE = json.loads('"\\ud800"')

    def test_guest_name_is_cleaned_on_the_host(self):
        canvas = pygame.Surface((1366, 768))
        for name, shown in (("Gu\u0000esty", "Guesty"), (self.SURROGATE, "Opponent"),
                            ("\u0000\n", "Opponent"), ("Guesty", "Guesty")):
            with self.subTest(name=ascii(name)):
                mode, _peer = self.host_after_hello(name)
                self.assertEqual(mode.remote_name, shown)
                self.assertEqual(mode.game.remote_name, shown)
                mode.update(1 / 60)
                mode.draw(canvas, (0, 0))

    def test_host_names_are_cleaned_on_the_guest(self):
        canvas = pygame.Surface((1366, 768))
        mode, opener = guest_after_hello("Ho\u0000sty")
        self.assertEqual(mode.remote_name, "Hosty")
        mode.update(1 / 60)
        mode.draw(canvas, (0, 0))
        for host_name in (self.SURROGATE, "\u0000", "Ho" + self.SURROGATE + "sty"):
            with self.subTest(host_name=ascii(host_name)):
                opener.peer.inbox.put(good_state(host_name=host_name))
                mode._process_network()
                self.assertEqual(mode.remote_name, "Hosty")
                mode.update(1 / 60)
                mode.draw(canvas, (0, 0))

    def test_events_with_a_strange_gun_are_skipped(self):
        canvas = pygame.Surface((1366, 768))
        mode, opener = guest_after_hello()
        opener.peer.inbox.put(good_state(events=[
            {"seq": 1, "kind": "hit", "shooter": 0, "target": 1, "weapon": "pi\u0000stol", "killed": True},
            {"seq": 2, "kind": "hit", "shooter": 0, "target": 1, "weapon": self.SURROGATE, "killed": True},
            {"seq": 3, "kind": "hit", "shooter": 0, "target": 1, "weapon": ["pistol"], "killed": True},
            {"seq": 4, "kind": "shot", "side": 0, "weapon": "bazooka"},
        ]))
        mode._process_network()
        mode.update(1 / 60)
        mode.draw(canvas, (0, 0))
        self.assertEqual(mode.game.kill_feed, [])
        self.assertEqual(mode.game.remote_weapon, "pistol")
        # A real gun still makes the kill feed.
        opener.peer.inbox.put(good_state(events=[
            {"seq": 5, "kind": "hit", "shooter": 0, "target": 1, "weapon": "kar98k", "killed": True}]))
        mode._process_network()
        mode.draw(canvas, (0, 0))
        self.assertEqual(len(mode.game.kill_feed), 1)
        self.assertIn(pvp.WEAPON_DEFINITIONS["kar98k"]["name"], mode.game.kill_feed[0][0])


class DisconnectResultTests(PvPCase):
    """B83: a disconnect after hello ends the duel on a result screen."""

    def drawn_texts(self, mode):
        canvas = pygame.Surface((1366, 768))
        texts = record_texts(mode)
        mode.draw(canvas, (0, 0))
        return texts, canvas

    def test_opponent_leaving_mid_match_is_a_forfeit_win(self):
        mode, peer = self.host_after_hello("Guesty")
        mode.authority[0]["score"], mode.authority[1]["score"] = 2, 1
        mode.update(0.0)
        mode.game.spawn_protection_timer = 0.8  # left early: the countdown is not frozen on screen
        seq = mode.leave_notice_seq
        peer.inbox.put({"type": "disconnected", "text": RELAY_LEFT_TEXT})
        mode._process_network()
        game = mode.game
        self.assertTrue(mode.finished)
        self.assertFalse(mode.connected)
        self.assertTrue(game.match_over)
        self.assertEqual(game.winner_text, "YOU WIN")
        self.assertEqual(game.winner_detail, "Guesty left the duel - win by forfeit")
        self.assertEqual((game.local_score, game.remote_score), (2, 1))
        self.assertTrue(peer.closed)
        self.assertIsNone(mode.peer)
        # The relay's poker wording ("Table paused") is not shown.
        self.assertEqual(mode.status, "Guesty left the duel.")
        self.assertEqual(mode.leave_notice, "Guesty left the game.")
        self.assertEqual(mode.leave_notice_seq, seq + 1)
        mode.update(0.05)  # nothing to send to any more, and no crash
        texts, _canvas = self.drawn_texts(mode)
        for text in ("YOU WIN", "Guesty left the duel - win by forfeit", "2  -  1"):
            self.assertIn(text, texts)
        self.assertTrue(any("ENTER" in text for text in texts), texts)
        self.assertFalse([text for text in texts if text.startswith("SPAWN PROTECTED")], texts)
        self.assertNotIn("DEAD MAN'S HAND • PvP", texts)  # the result, not the lobby

    def test_own_connection_lost_shows_connection_lost_with_the_score(self):
        mode, peer = self.host_after_hello("Guesty")
        mode.authority[0]["score"], mode.authority[1]["score"] = 1, 3
        mode.update(0.0)
        text = "Lost contact with the server (no reply for 20 seconds)"
        peer.inbox.put({"type": "disconnected", "text": text})
        mode._process_network()
        game = mode.game
        self.assertTrue(mode.finished)
        self.assertTrue(game.match_over)
        self.assertEqual(game.winner_text, "CONNECTION LOST")
        self.assertEqual((game.local_score, game.remote_score), (1, 3))
        self.assertEqual(mode.status, text)
        self.assertTrue(peer.closed)
        self.assertIsNone(mode.peer)
        texts, _canvas = self.drawn_texts(mode)
        self.assertIn("CONNECTION LOST", texts)
        self.assertIn("1  -  3", texts)

    def test_disconnect_after_a_normal_end_keeps_the_real_winner(self):
        # The guest's fifth kill and its leaving arrive together: the guest still won.
        mode, peer = self.host_after_hello("Guesty")
        gx, gy = self.guest_at_spawn(mode, peer)
        aim = host_facing_guest_spawn(mode)
        mode.authority[0]["score"], mode.authority[1]["score"] = 2, pvp.FIRST_TO_KILLS - 1
        mode.authority[0]["health"] = mode.game.health = PVP_DAMAGE["pistol"]
        peer.inbox.put({"type": "action", "action": "shot",
                        "shot": {"weapon": "pistol", "x": gx, "y": gy, "z": 0.0, "angle": aim}})
        peer.inbox.put({"type": "disconnected", "text": RELAY_LEFT_TEXT})
        mode._process_network()
        game = mode.game
        self.assertEqual(mode.authority[1]["score"], pvp.FIRST_TO_KILLS)
        self.assertTrue(mode.finished)
        self.assertTrue(game.match_over)
        self.assertEqual(game.winner_text, "GUESTY WINS")
        self.assertEqual(game.winner_detail, "")
        self.assertEqual((game.local_score, game.remote_score), (2, pvp.FIRST_TO_KILLS))
        texts, _canvas = self.drawn_texts(mode)
        self.assertIn("GUESTY WINS", texts)
        self.assertNotIn("Respawning…", texts)  # the dead host's respawn line is not drawn under the result

        # A host win that is already on screen stays as it was.
        mode, peer = self.host_after_hello("Guesty")
        mode.authority[0]["score"], mode.authority[1]["score"] = pvp.FIRST_TO_KILLS, 3
        mode.update(0.0)
        self.assertEqual(mode.game.winner_text, "YOU WIN")
        peer.inbox.put({"type": "disconnected", "text": RELAY_LEFT_TEXT})
        mode._process_network()
        self.assertTrue(mode.finished)
        self.assertEqual(mode.game.winner_text, "YOU WIN")
        self.assertEqual(mode.game.winner_detail, "")
        self.assertEqual((mode.game.local_score, mode.game.remote_score), (pvp.FIRST_TO_KILLS, 3))

    def test_result_screen_hides_the_respawn_countdown(self):
        # A normal end where the host lost: its "Respawning" line is not drawn under the result.
        mode, peer = self.host_after_hello("Guesty")
        gx, gy = self.guest_at_spawn(mode, peer)
        aim = host_facing_guest_spawn(mode)
        mode.authority[1]["score"] = pvp.FIRST_TO_KILLS - 1
        mode.authority[0]["health"] = mode.game.health = PVP_DAMAGE["pistol"]
        send_shot(mode, peer, {"weapon": "pistol", "x": gx, "y": gy, "z": 0.0, "angle": aim})
        mode.update(0.0)
        self.assertTrue(mode.game.match_over)
        self.assertTrue(mode.game.respawn_text.startswith("Respawning"))
        texts, _canvas = self.drawn_texts(mode)
        self.assertIn("GUESTY WINS", texts)
        self.assertIn("ESC to return to Multiplayer", texts)
        self.assertFalse([text for text in texts if text.startswith("Respawning")], texts)
        # During play the countdown is still drawn.
        mode, peer = self.host_after_hello("Guesty")
        mode.game.respawn_text = "Respawning in 2"
        texts, _canvas = self.drawn_texts(mode)
        self.assertIn("Respawning in 2", texts)

    def test_guest_sees_a_forfeit_win_when_the_host_leaves(self):
        mode, opener = guest_after_hello("Hosty")
        hx, hy, hangle = SPAWNS[0]
        opener.peer.inbox.put({"type": "state", "host": dict(pose(hx, hy, hangle), health=100, score=1),
                               "guest": {"health": 100, "score": 3}, "host_name": "Hosty",
                               "events": [], "match_over": False})
        opener.peer.inbox.put({"type": "disconnected", "text": RELAY_LEFT_TEXT})
        mode._process_network()
        game = mode.game
        self.assertTrue(mode.finished)
        self.assertEqual(game.winner_text, "YOU WIN")
        self.assertEqual(game.winner_detail, "Hosty left the duel - win by forfeit")
        self.assertEqual((game.local_score, game.remote_score), (3, 1))
        self.assertEqual(mode.status, "Hosty left the duel.")
        self.assertTrue(opener.peer.closed)
        self.assertIsNone(mode.peer)

    def test_a_click_right_after_the_disconnect_is_still_a_shot(self):
        clock = FakeClock()
        with mock.patch.object(pvp.time, "monotonic", clock):
            mode, peer = self.host_after_hello()
            peer.inbox.put({"type": "disconnected", "text": RELAY_LEFT_TEXT})
            mode._process_network()
            self.assertTrue(mode.finished)
            for _ in range(3):
                clock.advance(0.2)
                click(mode, mode.host_rect)
            self.assertTrue(mode.finished)
            self.assertEqual(mode.game.winner_text, "YOU WIN")
            clock.advance(pvp.RESULT_CLICK_DELAY)
            click(mode, mode.host_rect)
            self.assertFalse(mode.finished)
            self.assertIsNone(mode.game)

    def test_enter_or_click_returns_to_the_lobby_and_esc_still_closes(self):
        for how in ("click", "enter", "keypad enter"):
            clock = FakeClock()
            with self.subTest(how=how), mock.patch.object(pvp.time, "monotonic", clock):
                opener = RecordingOpenPeer()
                mode = DeadMansHandPvPMode("Hosty", "", open_peer=opener)
                click(mode, mode.host_rect)
                opener.peer.inbox.put({"type": "hello", "name": "Guesty"})
                opener.peer.inbox.put({"type": "disconnected", "text": RELAY_LEFT_TEXT})
                mode._process_network()
                self.assertTrue(mode.finished)
                code = mode.code
                type_text(mode, "zz")  # typing on the result screen goes nowhere
                self.assertEqual(mode.code, code)
                if how == "click":
                    clock.advance(pvp.RESULT_CLICK_DELAY)  # Enter works at once, a click after a moment
                    click(mode, mode.host_rect)  # where the Host button is in the lobby
                else:
                    key = pygame.K_RETURN if how == "enter" else pygame.K_KP_ENTER
                    mode.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key), (0, 0))
                self.assertFalse(mode.finished)
                self.assertIsNone(mode.game)
                self.assertFalse(mode.closed)
                self.assertEqual(len(opener.calls), 1)  # that click did not host a new duel
                texts, canvas = self.drawn_texts(mode)
                self.assertIn("Guesty left the duel.", texts)
                self.assertEqual(canvas.get_at((5, 760))[:3], LOBBY_COLOUR)
                # From the lobby a new duel can be hosted.
                click(mode, mode.host_rect)
                self.assertEqual(len(opener.calls), 2)
                self.assertIsNotNone(mode.game)
                self.assertFalse(mode.finished)
                self.assertFalse(mode.game.match_over)
        # ESC on the result screen still leaves PvP.
        mode, peer = self.host_after_hello()
        peer.inbox.put({"type": "disconnected", "text": RELAY_LEFT_TEXT})
        mode._process_network()
        self.assertTrue(mode.finished)
        mode.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE), (0, 0))
        self.assertTrue(mode.closed)


class FontCounter:
    """Stands in for pygame.font.Font or SysFont: builds the real font and records its arguments."""

    def __init__(self, real, built):
        self.real, self.built = real, built

    def __call__(self, *args, **kwargs):
        self.built.append(args)
        return self.real(*args, **kwargs)


class FrameFontTests(PvPCase):
    """N73: the duel builds its fonts on the first frame only, and opening the lobby again builds none.

    The opponent's name and gun plate used new fonts every frame. They now come from the shared
    font cache (solitaireplus.ui.text.get_font), so the tests empty it first."""

    def setUp(self):
        ui_text.clear_font_cache()

    def count_fonts(self, action):
        """The font arguments built by the first and by the second call of action()."""
        built = []
        with mock.patch("pygame.font.Font", FontCounter(pygame.font.Font, built)), \
                mock.patch("pygame.font.SysFont", FontCounter(pygame.font.SysFont, built)):
            action()
            first = list(built)
            del built[:]
            action()
        return first, built

    def test_duel_with_the_opponent_in_view_builds_fonts_once(self):
        mode, peer = self.host_after_hello()
        gx, gy = self.guest_at_spawn(mode, peer)
        host_facing_guest_spawn(mode)
        mode.game.set_remote(dict(pose(gx, gy), health=100), "Guesty")
        canvas = pygame.Surface((1366, 768))
        first, second = self.count_fonts(lambda: mode.draw(canvas, (0, 0)))
        # The first frame drew the opponent's name (size 10) and gun (size 8) plate.
        self.assertIn((None, 10), first)
        self.assertIn((None, 8), first)
        self.assertEqual(second, [], "fonts were built again on the second frame")

    def test_opening_the_lobby_again_builds_no_font(self):
        # multiplayer/main.py makes a new mode each time the duel lobby opens.
        canvas = pygame.Surface((1366, 768))

        def open_and_draw_lobby():
            DeadMansHandPvPMode("Hosty", "", open_peer=RecordingOpenPeer()).draw(canvas, (0, 0))

        first, second = self.count_fonts(open_and_draw_lobby)
        self.assertTrue(first, "the lobby did not reach its font code")
        self.assertEqual(second, [], "opening the lobby again built its fonts again")


if __name__ == "__main__":
    unittest.main()
