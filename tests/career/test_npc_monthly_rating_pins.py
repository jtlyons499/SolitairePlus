"""B23 (designer decision, no change): pin today's monthly NPC rating behaviour.

The monthly NPC rating decline is intended (NPCs age and are replaced), so these tests only
freeze what the code does now, so a refactor cannot change it by accident.

* simulate_npc_rating_month (career/ratings.py) moves 1-3 categories by a seeded roll per
  month. It calls apply_rating_change with the default scale_rewards=True, so gains are
  shrunk by reward_scale(rating) and losses are not. It ignores age. The game itself no
  longer calls it every month (only tests do); it is pinned because the brief names it.
* The path the game really runs once per career month is
  leaderboard_engine.update_career_leaderboard_ratings -> npc_world.advance_career_world
  -> npc_development.advance_npc_development (scale_rewards=False, age curves). Its
  12-month young-versus-veteran result is pinned too.
"""
import random
import unittest

from solitaireplus.career.npc_world import advance_career_world, ensure_career_world
from solitaireplus.career.ratings import (CATEGORY_KEYS, derive_overall, ensure_npc_career_state,
                                          reward_scale, simulate_npc_rating_month)


def npc_state(tier, age, strategy, poker, casino):
    npc = {"id": f"pin_{tier}_{age}", "name": "Pinned NPC", "skill_tier": tier, "age": age}
    ratings = {"strategy": strategy, "poker": poker, "casino": casino}
    return npc, ensure_npc_career_state({"rating": strategy, "ratings": ratings}, npc)


class ScriptedRng:
    """Plays back simulate_npc_rating_month's draws: how many games, which ones, each roll."""

    def __init__(self, keys, rolls):
        self.keys, self.rolls = list(keys), list(rolls)
        self.ranges = []

    def randint(self, low, high):
        self.ranges.append((low, high))
        return len(self.keys) if (low, high) == (1, 3) and len(self.ranges) == 1 else self.rolls.pop(0)

    def sample(self, population, count):
        assert sorted(population) == sorted(CATEGORY_KEYS) and count == len(self.keys)
        return list(self.keys)


class SimulateNpcRatingMonthPinTests(unittest.TestCase):
    def assert_ratings(self, state, expected_categories, expected_overall, expected_changes):
        for key, value in zip(CATEGORY_KEYS, expected_categories):
            self.assertAlmostEqual(float(state["ratings"][key]), value, places=6, msg=key)
        self.assertAlmostEqual(float(state["rating"]), expected_overall, places=6)
        self.assertAlmostEqual(float(state["ratings"]["overall"]), expected_overall, places=6)
        self.assertEqual(state["rating"], derive_overall(state["ratings"]))
        for key, value in zip(CATEGORY_KEYS, expected_changes):
            self.assertEqual(state["last_changes"][key], value, msg=key)

    def test_gains_are_scaled_by_rating_and_losses_are_not(self):
        npc, state = npc_state("mid", 30, 2000, 900, 1500)
        self.assertEqual(reward_scale(2000), 0.95)
        self.assertEqual(reward_scale(900), 1.0)
        rng = ScriptedRng(("strategy", "poker", "casino"), (45, 40, -40))
        simulate_npc_rating_month(state, npc, rng=rng)
        # Rolls come from the "mid" tier limits after the 1-3 game count.
        self.assertEqual(rng.ranges, [(1, 3), (-55, 55), (-55, 55), (-55, 55)])
        # +45 at 2000 -> +42.75 (saved fractional, shown +43); +40 below 1000 is unscaled;
        # -40 is never scaled.
        self.assert_ratings(state, (2042.75, 940.0, 1460.0), 1598.5125, (43, 40, -40))
        self.assertAlmostEqual(float(state["last_change"]), 1598.5125 - 1565.0, places=6)
        self.assertAlmostEqual(float(state["last_changes"]["overall"]), 33.5125, places=6)

    def test_tier_and_star_roll_limits(self):
        for tier, star, limits in (("elite", False, (-45, 50)), ("strong", False, (-50, 45)),
                                   ("mid", False, (-55, 55)), ("low", False, (-60, 60)),
                                   ("unknown", False, (-55, 55)), ("low", True, (-25, 55))):
            npc, state = npc_state(tier, 30, 1500, 1500, 1500)
            rng = ScriptedRng(("poker",), (0,))
            simulate_npc_rating_month(state, npc, star=star, rng=rng)
            self.assertEqual(rng.ranges, [(1, 3), limits], msg=(tier, star))

    def test_seeded_single_months_are_pinned(self):
        cases = (
            # tier, age, (strategy, poker, casino), star, seed -> categories, overall, changes
            ("elite", 24, (2400, 2300, 2200), False, 1,
             (2400.0, 2300.0, 2163.0), 2341.3, (0, 0, -37)),
            ("mid", 30, (1500, 1450, 1550), False, 7,
             (1527.3, 1401.0, 1550.0), 1485.365, (27, -49, 0)),
            ("low", 52, (900, 950, 1000), False, 23,
             (915.0, 950.0, 979.0), 933.65, (15, 0, -21)),
            ("elite", 29, (2900, 2850, 2800), True, 5,
             (2881.0, 2880.94, 2805.46), 2873.425, (-19, 31, 5)),
        )
        for tier, age, values, star, seed, categories, overall, changes in cases:
            with self.subTest(tier=tier, star=star, seed=seed):
                npc, state = npc_state(tier, age, *values)
                before = float(state["rating"])
                simulate_npc_rating_month(state, npc, star=star, rng=random.Random(seed))
                self.assert_ratings(state, categories, overall, changes)
                self.assertAlmostEqual(float(state["last_change"]), overall - before, places=6)

    def test_twelve_seeded_months_are_pinned_and_ignore_age(self):
        results = []
        for age in (21, 44):
            npc, state = npc_state("strong", age, 1800, 1750, 1700)
            rng = random.Random(99)
            for _ in range(12):
                simulate_npc_rating_month(state, npc, rng=rng)
            self.assert_ratings(state, (1791.935, 1838.825, 1706.58), 1799.811, (9, 0, 27))
            self.assertAlmostEqual(float(state["last_change"]), 7.39575, places=6)
            self.assertEqual(state["age"], age)
            results.append({key: float(value) for key, value in state["ratings"].items()})
        self.assertEqual(results[0], results[1])


class RealMonthlyPathPinTests(unittest.TestCase):
    """The game's real monthly NPC update over 12 months, one call per career month."""

    def test_young_npc_rises_and_veteran_declines_over_twelve_months(self):
        base = [
            {"id": "b23_young", "name": "Young", "age": 20, "skill_tier": "strong", "birthday_month": 6},
            {"id": "b23_veteran", "name": "Veteran", "age": 45, "skill_tier": "elite", "birthday_month": 6},
        ]
        states = {
            "b23_young": {"rating": 1800, "ratings": {"strategy": 1800, "poker": 1750, "casino": 1700}},
            "b23_veteran": {"rating": 2500, "ratings": {"strategy": 2500, "poker": 2450, "casino": 2400}},
        }
        world = ensure_career_world({}, states, base, 2026, 1, seed=2030)
        self.assertAlmostEqual(float(states["b23_young"]["rating"]), 1772.5, places=6)
        self.assertAlmostEqual(float(states["b23_veteran"]["rating"]), 2472.5, places=6)
        year, month = 2026, 1
        for _ in range(12):
            month += 1
            if month > 12:
                year, month = year + 1, 1
            world, _ = advance_career_world(world, states, base, (), year, month)
        expected = {
            # id: (age, peak_age, decline_start, (strategy, poker, casino), overall)
            "b23_young": (21, 34, 35, (1827.0, 1756.0, 1719.0), 1791.35),
            "b23_veteran": (46, 34, 37, (2482.0, 2437.0, 2386.0), 2456.65),
        }
        for npc_id, (age, peak_age, decline_start, categories, overall) in expected.items():
            with self.subTest(npc=npc_id):
                state = states[npc_id]
                self.assertEqual(state["age"], age)
                self.assertEqual(state["development"]["peak_age"], peak_age)
                self.assertEqual(state["development"]["decline_start"], decline_start)
                for key, value in zip(CATEGORY_KEYS, categories):
                    self.assertAlmostEqual(float(state["ratings"][key]), value, places=6, msg=key)
                self.assertAlmostEqual(float(state["rating"]), overall, places=6)
        self.assertEqual(world["last_simulated_month"], 2027 * 12)


if __name__ == "__main__":
    unittest.main()
