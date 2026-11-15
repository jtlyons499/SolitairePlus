"""B64: restoring an NPC whose saved ratings lack "overall" must not crash.

sync_npc_runtime_state() rebuilds the live NPC list from the save. A save whose
NPC ratings dict has the category ratings but no "overall" key used to raise
KeyError there. The tier must come from the same derived Global rating the rest
of the career code uses (career.ratings.derive_overall).
"""
import copy
import unittest

from solitaireplus.career.npc_development import rating_tier
from solitaireplus.career.ratings import derive_overall
from solitaireplus.npc import manager as npc_manager


def live_npc(npc_id):
    return next(npc for npc in npc_manager.NPCS if npc["id"] == npc_id)


class MissingOverallRatingTests(unittest.TestCase):
    def setUp(self):
        self.npc_id = npc_manager.BASE_NPCS[0]["id"]
        self.addCleanup(npc_manager.sync_npc_runtime_state, {})

    def sync(self, ratings):
        states = {self.npc_id: {"ratings": ratings}}
        saved = copy.deepcopy(states)
        npc_manager.sync_npc_runtime_state(states)
        # Restoring the runtime roster never rewrites the save itself.
        self.assertEqual(states, saved)
        return live_npc(self.npc_id)

    def test_tier_is_derived_from_categories_when_overall_missing(self):
        for value, expected in ((2400, "elite"), (1800, "strong"), (1300, "mid"), (900, "low")):
            with self.subTest(value=value):
                ratings = {"strategy": value, "poker": value, "casino": value}
                npc = self.sync(ratings)
                self.assertEqual(npc["skill_tier"], expected)
                self.assertEqual(npc["skill_tier"], rating_tier(derive_overall(ratings)))
                self.assertEqual(npc["career_ratings"]["overall"], derive_overall(ratings))

    def test_weighted_categories_decide_the_tier(self):
        # Strategy carries most of the Global weight: .55*2400 + .35*1200 + .10*1000 = 1840.
        ratings = {"strategy": 2400, "poker": 1200, "casino": 1000}
        npc = self.sync(ratings)
        self.assertEqual(npc["skill_tier"], "strong")

    def test_empty_ratings_dict_gets_the_neutral_default_rating(self):
        npc = self.sync({})
        self.assertEqual(npc["skill_tier"], rating_tier(1000))
        self.assertEqual(npc["career_ratings"]["overall"], 1000)

    def test_saved_overall_is_still_used_when_present(self):
        # Behaviour unchanged when the key exists, even if it disagrees with the categories.
        ratings = {"overall": 2500, "strategy": 900, "poker": 900, "casino": 900}
        npc = self.sync(ratings)
        self.assertEqual(npc["skill_tier"], "elite")
        self.assertEqual(npc["career_ratings"], ratings)


if __name__ == "__main__":
    unittest.main()
