"""B55: shots fired during Ace Invaders' wave-break pause must not count against accuracy.

Between waves the game pauses (WAVE_PAUSE_MS) before the next formation spawns.
The player can still press Space then, but those bullets never move and are
thrown away when the next wave spawns, so they cannot hit anything. Designer
default (2026-11-15): firing stays allowed during the break, but those shots are
not counted in shots-fired / accuracy. Shots fired during a wave still count.
"""
from tests.support import locate  # noqa: F401  (puts the repository on the import path)

import unittest

import pygame

from solitaireplus.games.arcade.ace_invaders_game import AceInvadersGame, WAVE_PAUSE_MS


class _Keys:
    """Stand-in for pygame.key.get_pressed(): only the given keys are held."""

    def __init__(self, *held):
        self._held = set(held)

    def __getitem__(self, key):
        return key in self._held


NO_KEYS = _Keys()
SPACE = _Keys(pygame.K_SPACE)
DT = 1 / 60


class AceInvadersWaveBreakAccuracyTest(unittest.TestCase):
    def setUp(self):
        self.game = AceInvadersGame()
        self.game.start_session("standard", rng_seed=7)
        # Space between shots comfortably above the fire cooldown.
        self.gap = max(120, int(self.game.difficulty_config.get("player_fire_ms", 245))) + 10

    def _start_wave_break(self, now):
        """Clear the formation so the next update completes the wave."""
        self.game.enemies = []
        self.game.update(DT, NO_KEYS, now=now)
        self.assertTrue(self.game._wave_resume_at, "the wave break should have started")
        self.assertEqual(self.game.wave, 2)

    def test_shot_during_a_wave_counts(self):
        self.game.update(DT, SPACE, now=1000)
        self.assertEqual(self.game.shots_fired, 1)

    def test_shots_during_the_break_do_not_count(self):
        game = self.game
        # One shot in wave 1 and one kill: 100% accuracy going into the break.
        game.update(DT, SPACE, now=1000)
        self.assertEqual(game.shots_fired, 1)
        game.enemies_destroyed = 1
        self.assertEqual(game.accuracy_percent, 100)

        break_start = 1000 + self.gap
        self._start_wave_break(break_start)
        resume_at = game._wave_resume_at
        self.assertEqual(resume_at, break_start + WAVE_PAUSE_MS)

        # Hold Space through the whole break.
        now = break_start + 1
        break_shots_attempted = 0
        while now < resume_at:
            bullets_before = len(game.player_bullets)
            game.update(DT, SPACE, now=now)
            self.assertTrue(game._wave_resume_at, "still in the break")
            if len(game.player_bullets) > bullets_before:
                break_shots_attempted += 1
            now += self.gap
        self.assertGreater(break_shots_attempted, 0,
                           "firing should still be allowed during the break")
        self.assertEqual(game.shots_fired, 1)
        self.assertEqual(game.accuracy_percent, 100)

        # The frame the next wave spawns on: Space fires before the spawn, and
        # the spawn throws that bullet away, so it must not count either.
        now = max(now, resume_at)
        game.update(DT, SPACE, now=now)
        self.assertEqual(game._wave_resume_at, 0, "the next wave should have spawned")
        self.assertTrue(game.enemies)
        self.assertEqual(game.player_bullets, [])

        self.assertEqual(game.shots_fired, 1)
        self.assertEqual(game.accuracy_percent, 100)

        # A shot in the new wave counts again.
        game.update(DT, SPACE, now=now + self.gap)
        self.assertEqual(game.shots_fired, 2)
        self.assertEqual(game.accuracy_percent, 50)


if __name__ == "__main__":
    unittest.main()
