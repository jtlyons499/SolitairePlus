"""B49: the four arcade machines run on the real frame time, not a fixed 1/60 s per frame.

The main loop keeps the length of the last frame (the value window.clock.tick returns, in
seconds) in state.frame_dt. Each machine's per-frame update (the loop_draw_* branches of
solitaireplus/games/arcade/machine_screens.py) passes it on, capped at 1/20 s. So one frame of
1/30 s must leave a machine in the same state as two frames of 1/60 s, within a small tolerance
(the machines still round some positions to whole pixels). Every run is seeded.
"""
from tests.support import locate  # noqa: F401  (puts the repository on the import path)

import ast
import os
import random
import types
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from solitaireplus.app import state
from solitaireplus.games.arcade import machine_screens
from solitaireplus.games.arcade.ace_invaders_game import AceInvadersGame
from solitaireplus.games.arcade.battle_bosses import BATTLE_BOSSES_DIFFICULTIES
from solitaireplus.games.arcade.battle_bosses_game import BattleBossesGame
from solitaireplus.games.arcade.king_pong import KingPongGame
from solitaireplus.games.arcade.suit_snake_game import SuitSnakeGame
from tests import test_loop_mouse_and_screen_hooks as loop_hooks

START_MS = 10_000
SEED = 4049
PIXELS = 1.5       # whole-pixel rounding: two rounded steps vs one rounded double step
# Battle Bosses moves its ball in sub-steps of at most 5 px, each rounded to whole pixels (two
# frames of 1/60 s take 2 + 2 sub-steps, one frame of 1/30 s takes 3): up to 0.5 px per sub-step.
BALL_SUBSTEP_PIXELS = 3.5
DEGREES = 0.75     # Battle Bosses rival shields add a small random aim error each frame


class _Keys:
    """Stands in for pygame.key.get_pressed(): only the given keys are held."""

    def __init__(self, *held):
        self._held = set(held)

    def __getitem__(self, key):
        return key in self._held


def _no_op(*args, **kwargs):
    return None


# ------------------------------------------------------------------ the four machines

def _king_pong():
    game = KingPongGame()
    game.start_match({"name": "Arcade Rival"}, difficulty_id="medium", target_score=5)
    return game


def _king_pong_snapshot(game):
    return {
        "player paddle": (tuple(game.player_paddle.topleft), PIXELS),
        "rival paddle": (tuple(game.opponent_paddle.topleft), PIXELS),
        "ball": (tuple(game.ball_rect.topleft), PIXELS),
        "ball velocity": (tuple(game._ball_velocity), 1e-6),
        "score": ((game.player_score, game.opponent_score), 0),
    }


def _battle_bosses():
    game = BattleBossesGame()
    game.start_match([], "standard", BATTLE_BOSSES_DIFFICULTIES["standard"], player_name="You")
    return game


def _battle_bosses_snapshot(game):
    return {
        "player shield": ((game.forts[0]["angle"],), 1e-6),
        "ball": (tuple(game.ball_rect.topleft), BALL_SUBSTEP_PIXELS),
        "ball velocity": (tuple(game.ball_velocity), 1e-6),
        "rival shields": (tuple(fort["angle"] for fort in game.forts[1:]), DEGREES),
        "fort hp": (tuple(fort["hp"] for fort in game.forts), 0),
    }


def _ace_invaders():
    game = AceInvadersGame()
    game.start_session("standard", rng_seed=SEED)
    return game


def _ace_invaders_snapshot(game):
    # A shot fired in the first frame leaves from where its shooter was after that frame, so the
    # bullet's x can trail the formation's movement by one step (about one pixel).
    return {
        "player": (tuple(game.player_rect.topleft), PIXELS),
        "formation": (tuple(value for enemy in game.enemies for value in enemy["rect"].topleft), PIXELS),
        "enemy bullets": (tuple(value for bullet in game.enemy_bullets for value in bullet["rect"].topleft),
                          PIXELS + 1),
        "player bullets": ((len(game.player_bullets), game.shots_fired), 0),
        "lives and score": ((game.lives, game.score), 0),
    }


def _suit_snake():
    game = SuitSnakeGame()
    game.start_session("classic_standard", rng_seed=SEED)
    game.queue_direction("right")
    # Started one step minus 15 ms ago: the next grid step falls inside the test's two frames.
    game._last_step_at = START_MS + 15 - int(game.mode_config["step_ms"])
    return game


def _suit_snake_snapshot(game):
    # The grid steps on the clock (every step_ms), not on dt: it must not change with dt either.
    return {
        "snake": (tuple(value for cell in game.snake for value in cell), 0),
        "last step": ((game._last_step_at,), 0),
        "score": ((game.score, game.cards_collected), 0),
    }


MACHINES = {
    "king_pong": (_king_pong, _king_pong_snapshot, _Keys(pygame.K_UP, pygame.K_RIGHT)),
    "battle_bosses": (_battle_bosses, _battle_bosses_snapshot, _Keys(pygame.K_RIGHT)),
    "ace_invaders": (_ace_invaders, _ace_invaders_snapshot, _Keys(pygame.K_RIGHT)),
    "suit_snake": (_suit_snake, _suit_snake_snapshot, _Keys(pygame.K_RIGHT)),
}


class MachinesUseTheRealFrameTime(unittest.TestCase):
    def setUp(self):
        saved = {name: value for name, value in vars(state).items() if not name.startswith("__")}

        def restore_state():
            for name in [name for name in vars(state) if not name.startswith("__") and name not in saved]:
                delattr(state, name)
            for name, value in saved.items():
                setattr(state, name, value)

        self.addCleanup(restore_state)
        self.now = [START_MS]
        self.keys = _Keys()
        patches = [
            mock.patch.object(pygame.time, "get_ticks", lambda: self.now[0]),
            mock.patch.object(pygame.key, "get_pressed", lambda: self.keys),
            mock.patch.object(machine_screens, "sounds", types.SimpleNamespace(
                audio=types.SimpleNamespace(play_sound=_no_op))),
        ]
        for name in dir(machine_screens):
            if (name.startswith("claim_") and name.endswith("_result")) or (
                    name.startswith("draw_") and name.endswith("_screen")):
                patches.append(mock.patch.object(machine_screens, name, _no_op))
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def play(self, machine, frames):
        """Start a fresh seeded game, then run the screen's per-frame branch once per (ms, dt) frame."""
        make, snapshot, keys = MACHINES[machine]
        random.seed(SEED)
        self.now[0] = START_MS
        game = make()
        self.keys = keys
        with mock.patch.object(machine_screens, f"{machine}_game", game):
            for at_ms, frame_dt in frames:
                self.now[0] = at_ms
                state.frame_dt = frame_dt
                getattr(machine_screens, f"loop_draw_{machine}")()
        self.assertFalse(game.finished, f"{machine} ended during the test")
        return snapshot(game)

    def assertSameState(self, machine, expected, actual, expected_how, actual_how):
        for part, (expected_values, tolerance) in expected.items():
            actual_values = actual[part][0]
            self.assertEqual(len(expected_values), len(actual_values), f"{machine}: {part}")
            for want, got in zip(expected_values, actual_values):
                self.assertLessEqual(
                    abs(want - got), tolerance,
                    f"{machine}: {part} {tuple(actual_values)} {actual_how}, "
                    f"{tuple(expected_values)} {expected_how}",
                )

    def test_one_long_frame_matches_two_short_frames(self):
        for machine in MACHINES:
            with self.subTest(machine=machine):
                two_short = self.play(machine, [(START_MS + 17, 1 / 60), (START_MS + 33, 1 / 60)])
                one_long = self.play(machine, [(START_MS + 33, 1 / 30)])
                self.assertSameState(machine, two_short, one_long,
                                     "after two 1/60 s frames", "after one 1/30 s frame")

    def test_a_long_hitch_counts_as_one_twentieth_of_a_second(self):
        # Only the dt-driven machines: Suit Snake steps on the clock.
        for machine in ("king_pong", "battle_bosses", "ace_invaders"):
            with self.subTest(machine=machine):
                make, snapshot, keys = MACHINES[machine]
                random.seed(SEED)
                self.now[0] = START_MS
                expected_game = make()
                self.now[0] = START_MS + 50
                expected_game.update(1 / 20, keys)
                expected = snapshot(expected_game)

                hitch = self.play(machine, [(START_MS + 50, 0.5)])
                self.assertSameState(machine, expected, hitch,
                                     "after update(1/20 s)", "after a 0.5 s frame")


class TheLoopStoresTheFrameTime(unittest.TestCase):
    def test_state_declares_frame_dt(self):
        tree = ast.parse((locate.ROOT / "solitaireplus" / "app" / "state.py").read_text(encoding="utf-8"))
        declared = {target.id for node in tree.body if isinstance(node, ast.Assign)
                    for target in node.targets if isinstance(target, ast.Name)}
        self.assertTrue("frame_dt" in declared, "solitaireplus/app/state.py does not declare frame_dt")

    def test_each_frame_stores_what_clock_tick_returned_in_seconds(self):
        seen = []
        ticks = iter([16, 40, 250])
        env_ref = {}

        def draw():
            seen.append(env_ref["env"]["frame_dt"])

        module = types.SimpleNamespace(loop_event_menu=_no_op, loop_draw_menu=draw, loop_late_menu=_no_op)
        frames = [((0, 0), [])] * 3
        env = env_ref["env"] = loop_hooks.loop_env(frames, module, {"menu": "menu"}, "menu")
        env["frame_dt"] = 1 / 60
        fake = env["pygame"]

        def tick(fps):
            fake.frame += 1
            if fake.frame >= len(fake.frames):
                env["running"] = False
            return next(ticks)

        env["clock"] = types.SimpleNamespace(tick=tick)
        loop_hooks.run_loop(env)

        # A frame sees the length of the frame before it; the first frame keeps the start value.
        self.assertEqual(seen, [1 / 60, 0.016, 0.040])
        self.assertEqual(env["frame_dt"], 0.25)


if __name__ == "__main__":
    unittest.main()
