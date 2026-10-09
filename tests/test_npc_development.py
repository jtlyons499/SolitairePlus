from career_activities import normalize_story, reconcile_story_cosmetics
"""Career-world regression tests; run from the project root with unittest."""
import ast
import copy
import json
import random
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import profile as profiles
import npc_manager
from achievements import normalize_achievement_state
from career_fans import clamp_fans
from career_npc_development import (ability_target, advance_npc_development,
                                    choose_prospect_band, development_stage,
                                    ensure_npc_development, month_index)
from career_npc_world import (add_prospect, advance_career_world, career_roster,
                              ensure_career_world)
from career_ratings import CATEGORY_KEYS as GAME_RATING_KEYS, derive_overall, normalize_rating_bundle
from npc_personality import TRAIT_NAMES
from career_event_progress import store_event_progress

ROOT = Path(__file__).resolve().parents[1]
MAIN_TREE = ast.parse((ROOT / "main.py").read_text(encoding="utf-8"))


def world(seed=42, base=None, year=2026, month=1):
    states = {}
    data = ensure_career_world({}, states, npc_manager.BASE_NPCS if base is None else base,
                               year, month, seed=seed)
    return data, states


def main_functions(names, values):
    nodes = [node for node in MAIN_TREE.body if isinstance(node, ast.FunctionDef) and node.name in names]
    if len(nodes) != len(names):
        raise AssertionError("Requested main functions were not found")
    namespace = dict(values)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "main NPC integration", "exec"), namespace)
    return namespace


class DevelopmentTests(unittest.TestCase):
    def test_old_profile_migrates_at_current_date_without_age_or_rating_shock(self):
        base = [{"id": "veteran", "name": "Veteran", "age": 31, "skill_tier": "elite"}]
        ratings = {key: 2300 + index * 10 for index, key in enumerate(GAME_RATING_KEYS)}
        states = {"veteran": {"age": 71, "birthday_month": 4,
                              "ratings": ratings.copy(), "rating": derive_overall(ratings),
                              "custom_data": {"preserve": True}}}
        data = ensure_career_world({}, states, base, 2041, 10, seed=42)
        self.assertEqual(states["veteran"]["age"], 71)
        self.assertEqual({key: states["veteran"]["ratings"][key] for key in GAME_RATING_KEYS}, ratings)
        self.assertEqual(states["veteran"]["custom_data"], {"preserve": True})
        snapshot = copy.deepcopy((data, states))
        data, stories = advance_career_world(data, states, base, (), 2041, 10)
        self.assertEqual((data, states), snapshot)
        self.assertEqual(stories, [])

    def test_birthdays_are_distributed_and_once_per_year(self):
        data, states = world()
        before = {key: state["age"] for key, state in states.items()}
        self.assertGreaterEqual(len({state["birthday_month"] for state in states.values()}), 10)
        data, _ = advance_career_world(data, states, npc_manager.BASE_NPCS, (), 2027, 1)
        self.assertTrue(all(states[key]["age"] == age + 1 for key, age in before.items()))
        snapshot = copy.deepcopy((data, states))
        advance_career_world(data, states, npc_manager.BASE_NPCS, (), 2027, 1)
        self.assertEqual((data, states), snapshot)

    def test_birthday_month_is_not_replayed_on_reload(self):
        base = [{"id": "junior", "name": "Junior", "age": 9, "birthday_month": 12}]
        data, states = world(base=base, month=11)
        advance_career_world(data, states, base, (), 2026, 12)
        self.assertEqual(states["junior"]["age"], 10)
        data, states = json.loads(json.dumps((data, states)))
        ensure_career_world(data, states, base, 2026, 12)
        advance_career_world(data, states, base, (), 2026, 12)
        self.assertEqual(states["junior"]["age"], 10)
        advance_career_world(data, states, base, (), 2027, 12)
        self.assertEqual(states["junior"]["age"], 11)

    def test_saved_and_uninterrupted_monthly_paths_match(self):
        data, states = world()
        continuous = copy.deepcopy((data, states))
        advance_career_world(*continuous, npc_manager.BASE_NPCS, npc_manager.PROSPECT_POOL, 2028, 1)
        advance_career_world(data, states, npc_manager.BASE_NPCS, npc_manager.PROSPECT_POOL, 2027, 1)
        data, states = json.loads(json.dumps((data, states)))
        advance_career_world(data, states, npc_manager.BASE_NPCS, npc_manager.PROSPECT_POOL, 2028, 1)
        self.assertEqual((data, states), continuous)

    def test_different_careers_have_different_saved_paths(self):
        first, _ = world(seed=42)
        second, _ = world(seed=43)
        self.assertNotEqual(first["seed"], second["seed"])
        data, states = world(seed=42)
        development = copy.deepcopy(next(iter(states.values()))["development"])
        ensure_career_world(data, states, npc_manager.BASE_NPCS, 2026, 1, seed=999)
        self.assertEqual(data["seed"], 42)
        self.assertEqual(next(iter(states.values()))["development"], development)

    def test_monthly_updates_preserve_derived_overall_and_game_specialties(self):
        data, states = world()
        advance_career_world(data, states, npc_manager.BASE_NPCS, (), 2027, 1)
        for state in states.values():
            self.assertEqual(state["rating"], derive_overall(state["ratings"]))
            self.assertEqual(state["ratings"]["overall"], state["rating"])
            self.assertEqual(set(state["development"]["peak_ratings"]), set(GAME_RATING_KEYS))
            self.assertTrue(all(rating >= 100 for rating in state["ratings"].values()))
        self.assertTrue(any(len(set(s["ratings"][key] for key in GAME_RATING_KEYS)) > 1
                            for s in states.values()))

    def test_decline_is_gentle_capped_and_does_not_retroactively_reset_veterans(self):
        npc = {"id": "old", "age": 71, "birthday_month": 1}
        state = {"age": 71, "birthday_month": 1, "rating": 2500,
                 "ratings": dict.fromkeys(GAME_RATING_KEYS, 2500)}
        curve = ensure_npc_development(state, npc, 2026, 1, 10)
        self.assertEqual(ability_target(curve, "strategy", 71), 2500)
        self.assertTrue(38 <= curve["decline_start"] <= 45)
        self.assertTrue(3 <= 2500 - ability_target(curve, "strategy", 72) <= 7)
        self.assertGreaterEqual(ability_target(curve, "strategy", 200), 2000)
        self.assertEqual(development_stage(state, 1), "Veteran · gradual decline")

    def test_supernatural_original_character_is_preserved(self):
        data, states = world()
        npc = next(entry for entry in npc_manager.BASE_NPCS if entry["age"] > 120)
        state = states[npc["id"]]
        self.assertEqual(development_stage(state, 1), "Timeless")
        curve = state["development"]
        for key in GAME_RATING_KEYS:
            self.assertEqual(ability_target(curve, key, 1000), curve["anchor_ratings"][key])
        self.assertEqual(state["age"], npc["age"])


class ProspectTests(unittest.TestCase):
    def tearDown(self):
        npc_manager.sync_npc_runtime_state({})

    def test_complete_named_pool_has_unique_identities_and_all_traits(self):
        pool = npc_manager.PROSPECT_POOL
        self.assertEqual(len(pool), 160)
        self.assertEqual(len({npc["id"] for npc in pool}), 160)
        self.assertEqual(len({npc["name"] for npc in pool}), 160)
        for npc in pool:
            self.assertTrue(npc["name"] and npc["bio"] and npc["hometown"] and npc["country"])
            self.assertEqual(set(npc["personality_traits"]), set(TRAIT_NAMES))
            self.assertTrue(all(1 <= value <= 10 for value in npc["personality_traits"].values()))
            self.assertTrue(npc["avatar"])

    def test_arrivals_are_gradual_and_stay_saved(self):
        data, states = world()
        self.assertEqual(len(career_roster(npc_manager.BASE_NPCS, states)), len(npc_manager.BASE_NPCS))
        _, stories = advance_career_world(data, states, npc_manager.BASE_NPCS,
                                          npc_manager.PROSPECT_POOL, 2027, 1)
        arrivals = [story for story in stories if story["headline"].startswith("NEW ")]
        self.assertTrue(2 <= len(arrivals) <= 4)
        for story in arrivals:
            state = states[story["npc_id"]]
            self.assertTrue(5 <= state["prospect_record"]["age"] <= 10)
            self.assertEqual(month_index(story["year"], story["month"]), state["joined_month"])
        self.assertEqual(len(career_roster(npc_manager.BASE_NPCS, states)), len(npc_manager.BASE_NPCS) + len(arrivals))
        saved = json.loads(json.dumps((data, states)))
        self.assertEqual(saved[0]["used_prospect_ids"], data["used_prospect_ids"])
        self.assertEqual(career_roster(npc_manager.BASE_NPCS, saved[1]), career_roster(npc_manager.BASE_NPCS, states))

    def test_profile_switch_restores_original_ages_and_removes_other_career_prospects(self):
        data, states = world()
        story = add_prospect(data, states, npc_manager.PROSPECT_POOL, 2026, 1)
        base_id = npc_manager.BASE_NPCS[0]["id"]
        states[base_id]["age"] = 99
        live_list = npc_manager.NPCS
        live_first = next(npc for npc in live_list if npc["id"] == base_id)
        npc_manager.sync_npc_runtime_state(states)
        self.assertIs(npc_manager.NPCS, live_list)
        self.assertIs(next(npc for npc in live_list if npc["id"] == base_id), live_first)
        self.assertEqual(live_first["age"], 99)
        self.assertTrue(any(npc["id"] == story["npc_id"] for npc in live_list))
        npc_manager.sync_npc_runtime_state({})
        self.assertEqual(len(live_list), len(npc_manager.BASE_NPCS))
        self.assertEqual(live_first["age"], npc_manager.BASE_NPCS[0]["age"])
        self.assertFalse(any(npc["id"] == story["npc_id"] for npc in live_list))

    def test_active_prospects_enter_normal_opponent_selection(self):
        data, states = world()
        story = add_prospect(data, states, npc_manager.PROSPECT_POOL, 2026, 1)
        npc_manager.sync_npc_runtime_state(states)
        exclude = [npc["id"] for npc in npc_manager.BASE_NPCS]
        self.assertEqual(npc_manager.get_random_npc(exclude_ids=exclude)["id"], story["npc_id"])
        self.assertEqual(npc_manager.get_random_npc_by_tier("low", exclude, "score_four")["id"], story["npc_id"])
        self.assertIsNone(npc_manager.get_random_npc(minimum_age=18, exclude_ids=exclude))

    def test_pool_exhaustion_never_duplicates_or_removes_established_roster(self):
        data, states = world()
        for _ in range(160):
            self.assertIsNotNone(add_prospect(data, states, npc_manager.PROSPECT_POOL, 2026, 1))
        self.assertIsNone(add_prospect(data, states, npc_manager.PROSPECT_POOL, 2026, 1))
        advance_career_world(data, states, npc_manager.BASE_NPCS, npc_manager.PROSPECT_POOL, 2027, 1)
        self.assertEqual(len(states), len(npc_manager.BASE_NPCS) + len(npc_manager.PROSPECT_POOL))
        self.assertEqual(len(set(data["used_prospect_ids"])), 160)
        self.assertTrue(all(npc["id"] in states for npc in npc_manager.BASE_NPCS))

    def test_club_junior_settles_near_1100_then_holds_plateau(self):
        data, states = world(base=[])
        story = add_prospect(data, states, npc_manager.PROSPECT_POOL, 2026, 1)
        state = states[story["npc_id"]]
        self.assertEqual(state["development"]["band"], "club")
        record = state["prospect_record"]
        values = {}
        for serial in range(month_index(2026, 2), month_index(2057, 1)):
            year, zero_month = divmod(serial, 12)
            advance_npc_development(state, record, year, zero_month + 1, data["seed"])
            if state["age"] in (15, 20, 30):
                values[state["age"]] = state["rating"]
        self.assertTrue(950 <= values[15] <= 1350)
        self.assertLess(abs(values[30] - values[20]), 60)

    def test_rare_prodigy_reaches_2500_then_continues_towards_top_five(self):
        data, states = world()
        story = add_prospect(data, states, npc_manager.PROSPECT_POOL, 2026, 1, force_prodigy=True)
        identity = story["npc_id"]
        state = states[identity]
        self.assertTrue(state["development"]["prodigy"])
        news = []
        at_eighteen = None
        for year in range(2027, 2052):
            _, stories = advance_career_world(data, states, npc_manager.BASE_NPCS, (), year, 1)
            news.extend(s for s in stories if s["npc_id"] == identity)
            if state["age"] == 18:
                at_eighteen = state["rating"]
        self.assertTrue(2400 <= at_eighteen <= 2750)
        self.assertGreater(state["rating"], at_eighteen + 80)
        self.assertIn(identity, sorted(states, key=lambda key: states[key]["rating"], reverse=True)[:5])
        headlines = [s["headline"] for s in news]
        self.assertEqual(len(headlines), len(set(headlines)))
        self.assertTrue(any("TOP FIVE" in headline for headline in headlines))

    def test_majority_are_club_strength_and_prodigies_are_rare(self):
        bands = [choose_prospect_band(random.Random(seed))[0] for seed in range(10000)]
        self.assertTrue(6300 <= bands.count("club") <= 7100)
        self.assertTrue(60 <= bands.count("prodigy") <= 140)

    def test_save_slots_preserve_their_own_world_identity_and_potential(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(profiles, "SAVE_FOLDER", folder):
            for slot in (1, 2, 3):
                data, states = world(seed=slot)
                story = add_prospect(data, states, npc_manager.PROSPECT_POOL, 2026, 1)
                profile = profiles.make_default_profile()
                profile["career"].update(npc_world=data, leaderboard_state=states, cash=23549,
                                          fans=420, current_job="programmer", custom_value="keep")
                profiles.save_profile(profile, slot)
                loaded = profiles.load_profile(slot)
                self.assertEqual(loaded["profile_version"], profiles.PROFILE_VERSION)
                self.assertEqual(loaded["career"], profile["career"])
                self.assertEqual(loaded["career"]["npc_world"]["seed"], slot)
                self.assertEqual(loaded["career"]["leaderboard_state"][story["npc_id"]], states[story["npc_id"]])


class MainIntegrationTests(unittest.TestCase):
    def test_actual_profile_load_anchors_world_at_saved_date_and_save_is_independent(self):
        self.addCleanup(npc_manager.sync_npc_runtime_state, {})
        profile = profiles.make_default_profile()
        profile["profile_version"] = 6
        profile["settings"]["score_four_layout"] = "wide"
        profile["career"]["interview_recent_ids"] = ["learning", "future"]
        profile["identity"].update(country="CAN", age=37, hometown="Ottawa",
                                    bio="A patient card player.", favorite_suit="Hearts")
        npc = npc_manager.BASE_NPCS[0]
        profile["career"].update(year=2045, month=9, cash=23549,
                                  leaderboard_state={npc["id"]: {
                                      "age": 71, "rating": 2100,
                                      "ratings": dict.fromkeys(GAME_RATING_KEYS, 2100)}})
        game = SimpleNamespace(deal_mode="random")
        game.set_deal_mode = lambda mode: setattr(game, "deal_mode", mode)
        env = main_functions(("apply_profile_save_data", "build_profile_save_data",
                              "sync_career_npc_runtime_state"), dict(
            copy=copy, normalize_story=normalize_story, reconcile_story_cosmetics=reconcile_story_cosmetics, game=game, score_four_game=SimpleNamespace(layout="compact"), store_event_progress=store_event_progress, make_default_profile=profiles.make_default_profile,
            avatar_bases=["base_01"], avatar_eyes=["eyes_01"], avatar_hair=["hair_01"],
            avatar_tops=["top_01"], avatar_glasses=[], favorite_suit_options=["Hearts"],
            cursor_runtime_surfaces={"cursor": None}, VERIFIED_DEALS_ENABLED=False,
            clamp_fans=clamp_fans, normalize_rating_bundle=normalize_rating_bundle,
            normalize_achievement_state=normalize_achievement_state,
            get_next_level_xp=lambda level: 100, sync_achievement_cosmetic_rewards=lambda: None,
            grant_rating_cosmetics=lambda **kwargs: None,
            sync_selected_cosmetics=lambda: None, apply_selected_cursor=lambda: None,
            BASE_NPCS=npc_manager.BASE_NPCS, ensure_career_world=ensure_career_world,
            sync_npc_runtime_state=npc_manager.sync_npc_runtime_state))
        env["apply_profile_save_data"](profile)
        self.assertEqual(env["career_npc_world"]["started_month"], month_index(2045, 9))
        self.assertEqual(env["career_leaderboard_state"][npc["id"]]["age"], 71)
        self.assertEqual(env["score_four_game"].layout, "wide")
        saved = env["build_profile_save_data"]()
        self.assertEqual(saved["settings"]["score_four_layout"], "wide")
        self.assertEqual(saved["career"]["interview_recent_ids"], ["learning", "future"])
        self.assertEqual(saved["cryptid_creatures"], env["cryptid_collection_state"])
        self.assertEqual(saved["profile_version"], profiles.PROFILE_VERSION)
        self.assertEqual(saved["career"]["cash"], 23549)
        self.assertEqual(saved["identity"], profile["identity"])
        self.assertEqual(saved["career"]["npc_world"], env["career_npc_world"])
        env["career_leaderboard_state"][npc["id"]]["age"] = 72
        self.assertEqual(saved["career"]["leaderboard_state"][npc["id"]]["age"], 71)
        self.assertEqual(profile["career"]["leaderboard_state"][npc["id"]]["age"], 71)

    def test_monthly_orchestration_is_free_play_safe_and_keeps_actual_story_dates(self):
        data, states = world()
        news = []
        env = main_functions(("update_career_leaderboard_ratings",), dict(
            current_game_mode="career", career_npc_world=data, career_leaderboard_state=states,
            BASE_NPCS=npc_manager.BASE_NPCS, PROSPECT_POOL=npc_manager.PROSPECT_POOL,
            career_year=2027, career_month=1, advance_career_world=advance_career_world,
            sync_career_npc_runtime_state=lambda: None, get_npc_leaderboard_snapshot=lambda: {},
            add_monthly_leaderboard_news=lambda *args: None,
            add_career_news=lambda headline, body, category, **date: news.append(date)))
        original = copy.deepcopy((data, states))
        env["current_game_mode"] = "free"
        self.assertFalse(env["update_career_leaderboard_ratings"]())
        self.assertEqual((data, states), original)
        env["current_game_mode"] = "career"
        self.assertTrue(env["update_career_leaderboard_ratings"]())
        self.assertTrue(any(date["year"] == 2026 and date["month"] != 1 for date in news))
        self.assertTrue(all(set(date) == {"year", "month"} for date in news))
        saved_news = copy.deepcopy(news)
        self.assertFalse(env["update_career_leaderboard_ratings"]())
        self.assertEqual(news, saved_news)

    def test_debug_year_advances_twelve_real_months_and_saves_once(self):
        calls = []
        env = main_functions(("debug_start_next_career_month", "debug_advance_career_year"), dict(
            current_game_mode="free", current_state="free", STATE_CAREER_HUB="hub",
            career_year=2026, career_month=11, career_day=1, career_day_of_month=1,
            career_weekday_index=0, career_current_schedule=[None] * 30,
            finish_free_play_sandbox=lambda: calls.append("restore"),
            ensure_career_leaderboard=lambda: None, reset_career_hub_runtime=lambda: None,
            update_career_leaderboard_ratings=lambda: calls.append("develop"),
            maybe_add_monthly_flavor_news=lambda: None,
            build_default_career_schedule=lambda: [None] * 30,
            auto_save_career=lambda: calls.append("save")))
        env["debug_advance_career_year"]()
        self.assertEqual((env["career_year"], env["career_month"]), (2027, 11))
        self.assertEqual(calls.count("restore"), 1)
        self.assertEqual(calls.count("develop"), 12)
        self.assertEqual(calls.count("save"), 1)
        self.assertEqual(env["current_state"], "hub")

    def test_debug_forced_prodigy_uses_saved_world_and_returns_to_career(self):
        data, states = world()
        calls = []
        env = main_functions(("debug_add_career_prospect",), dict(
            current_game_mode="free", current_state="free", STATE_CAREER_HUB="hub",
            career_year=2026, career_month=1, career_npc_world=data,
            career_leaderboard_state=states, PROSPECT_POOL=npc_manager.PROSPECT_POOL,
            finish_free_play_sandbox=lambda: calls.append("restore"),
            ensure_career_leaderboard=lambda: None, add_prospect=add_prospect,
            sync_career_npc_runtime_state=lambda: None, add_career_news=lambda *args: None,
            auto_save_career=lambda: calls.append("save"), show_debug_message=lambda *args: None))
        self.assertTrue(env["debug_add_career_prospect"](True))
        self.assertTrue(states[data["used_prospect_ids"][-1]]["development"]["prodigy"])
        self.assertEqual(calls, ["restore", "save"])
        self.assertEqual(env["current_game_mode"], "career")
        self.assertEqual(env["current_state"], "hub")


if __name__ == "__main__":
    unittest.main()

