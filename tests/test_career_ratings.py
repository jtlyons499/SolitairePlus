import ast
import copy
import json
from pathlib import Path
import random
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import profile as profile_module
from career_ratings import (GAME_RATING_KEYS, GAME_CATEGORIES, CATEGORY_KEYS, RATING_KEYS, apply_rating_change,
                            boost_npc_overall, derive_overall, elo_delta,
                            ensure_npc_career_state, make_npc_rating_bundle,
                            make_player_rating_bundle, migrate_profile_ratings,
                            normalize_rating_bundle, simulate_npc_rating_month)
from career_rating_events import (record_poker_showdown, record_result,
                                 settle_competitive_result, settle_house_result,
                                 settle_poker_session)
from texas_holdem import TexasHoldemGame
from five_card_draw import FiveCardDrawGame
from seven_card_stud import SevenCardStudGame
from score_four import ScoreFourGame

ROOT = Path(__file__).resolve().parents[1]
MAIN_TREE = ast.parse((ROOT / "main.py").read_text(encoding="utf-8"))


def main_functions(*names, **values):
    """Execute actual orchestration functions without launching the asset UI."""
    nodes = [node for node in MAIN_TREE.body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert len(nodes) == len(names)
    namespace = dict(grant_rating_cosmetics=lambda: None, current_game_mode="career", career_rating=1000,
                     career_ratings=make_player_rating_bundle(), career_rating_results={},
                     career_leaderboard_state={}, GAME_RATING_KEYS=GAME_RATING_KEYS,
                     apply_rating_change=apply_rating_change, settle_house_result=settle_house_result,
                     settle_competitive_result=settle_competitive_result,
                     settle_poker_session=settle_poker_session, record_poker_showdown=record_poker_showdown,
                     record_result=record_result, elo_delta=elo_delta,
                     sync_career_npc_runtime_state=lambda: None)
    namespace.update(values)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "main rating integration", "exec"), namespace)
    return namespace


def npc(identity="rival"):
    return {"id": identity, "name": identity, "skill_tier": "mid", "age": 30}


class RatingTests(unittest.TestCase):
    def test_only_played_game_changes_and_overall_is_derived(self):
        for key in GAME_RATING_KEYS:
            bundle = make_player_rating_bundle()
            self.assertEqual(apply_rating_change(bundle, key, 70), 70)
            self.assertAlmostEqual(bundle["overall"], 1000 + 70 * {"strategy":.55,"poker":.35,"casino":.1}[GAME_CATEGORIES[key]])
            self.assertTrue(all(bundle[other] == 1000 for other in GAME_RATING_KEYS if GAME_CATEGORIES[other] != GAME_CATEGORIES[key]))
        with self.assertRaises(ValueError):
            apply_rating_change(bundle, "overall", 100)
        bundle["strategy"] = 105
        self.assertEqual(apply_rating_change(bundle, "solitaire", -40), -5)
        self.assertEqual(bundle["overall"], derive_overall(bundle))

    def test_legacy_migration_preserves_progress_and_individual_values(self):
        old = profile_module.make_default_profile()
        old["profile_version"] = 5
        career = old["career"]
        career.update(rating=9000, cash=23549, job="developer", fans=420,
                      owned_residences=["dingy_apartment", "penthouse"], custom_feature={"keep": True})
        career["ratings"] = dict.fromkeys(("solitaire", "score_four", "texas_holdem", "five_card_draw", "seven_card_stud", "blackjack", "roulette"), 1000)
        career["ratings"].update(overall=9000, solitaire=1700, blackjack=1300)
        before = copy.deepcopy(career)
        migrate_profile_ratings(old)
        self.assertEqual(career["ratings"]["strategy"], 1350)
        self.assertEqual(career["ratings"]["casino"], 1150)
        self.assertEqual(career["rating"], 1207.5)
        for key in ("cash", "fans", "job", "owned_residences", "custom_feature"):
            self.assertEqual(career[key], before[key])
        migrated = copy.deepcopy(old)
        migrate_profile_ratings(old)
        self.assertEqual(old, migrated)
        oldest = {"career": {"rating": 1700, "cash": 100}}
        migrate_profile_ratings(oldest)
        self.assertEqual(oldest["career"]["ratings"]["solitaire"], 1700)
        self.assertEqual(oldest["career"]["ratings"]["texas_holdem"], 1000)
        self.assertEqual(oldest["career"]["rating"], 1385)

    def test_three_save_slots_migrate_and_round_trip(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(profile_module, "SAVE_FOLDER", folder):
            for slot in (1, 2, 3):
                old = {"profile_version": 5, "identity": {"name": f"Slot {slot}"},
                       "career": {"rating": 1000 + slot * 700, "cash": slot * 500,
                                  "leaderboard_state": {"rival": {"rating": 2000, "age": 71}}}}
                Path(profile_module.get_profile_path(slot)).write_text(json.dumps(old), encoding="utf-8")
                loaded = profile_module.load_profile(slot)
                self.assertEqual(loaded["profile_version"], profile_module.PROFILE_VERSION)
                self.assertEqual(loaded["career"]["rating"], 1000 + slot * 385)
                profile_module.save_profile(loaded, slot)
                self.assertEqual(profile_module.load_profile(slot), loaded)

    def test_npc_migration_never_overwrites_game_ratings_from_legacy_overall(self):
        bundle = dict.fromkeys(RATING_KEYS, 1500)
        bundle["casino"] = 2200
        state = {"rating": 9900, "age": 71, "ratings": bundle}
        ensure_npc_career_state(state, npc(), random.Random(1))
        self.assertEqual(state["rating"], 1570)
        self.assertEqual(state["ratings"]["solitaire"], 1500)
        self.assertEqual(state["ratings"]["blackjack"], 2200)
        self.assertEqual(state["age"], 71)
        saved = copy.deepcopy(state)
        ensure_npc_career_state(state, npc(), random.Random(2))
        self.assertEqual(state, saved)
        boost_npc_overall(state, 3000)
        self.assertEqual(state["rating"], 3000)
        self.assertEqual(state["ratings"]["blackjack"] - state["ratings"]["solitaire"], 700)

    def test_competitive_win_loss_and_rival_deltas(self):
        for score in (0.0, 1.0):
            ratings, stats = make_player_rating_bundle(), {}
            states = {"rival": {"rating": 1000, "ratings": make_player_rating_bundle()}}
            delta = settle_competitive_result(ratings, stats, states, "score_four", npc(), score)
            self.assertEqual(delta, 60 if score else -10)
            self.assertEqual(states["rival"]["ratings"]["score_four"], 1000 - delta)
            self.assertEqual(ratings["strategy"], 1000 + delta)
            self.assertEqual(states["rival"]["rating"], derive_overall(states["rival"]["ratings"]))
        self.assertGreater(elo_delta(1000, 2000, 1), elo_delta(1000, 800, 1))
        self.assertLess(abs(elo_delta(1000, 2000, 0)), abs(elo_delta(1000, 800, 0)))
        self.assertEqual(elo_delta(1000, 1000, 0.5), 0)

    def test_house_points_ignore_wager_size_and_push_is_neutral(self):
        for key, unit in (("blackjack", 15), ("roulette", 12), ("faro", 12)):
            for net in (1, 23549):
                ratings, stats = make_player_rating_bundle(), {}
                self.assertEqual(settle_house_result(ratings, stats, key, net), unit)
                self.assertEqual(stats[key]["wins"], 1)
                self.assertEqual(settle_house_result(ratings, stats, key, -net), -5)
                self.assertEqual(settle_house_result(ratings, stats, key, 0), 0)
                self.assertEqual(ratings[key], 1000 + unit - 5)
                self.assertEqual(stats[key]["played"], 3)

    def test_monthly_npc_updates_are_per_game_with_category_changes(self):
        state = ensure_npc_career_state({"rating": 1600}, npc(), random.Random(1))
        before = copy.deepcopy(state["ratings"])
        simulate_npc_rating_month(state, npc(), rng=random.Random(7))
        changed = [key for key in CATEGORY_KEYS if state["ratings"][key] != before[key]]
        self.assertGreaterEqual(len(changed), 1)
        self.assertLessEqual(len(changed), 3)
        self.assertEqual(state["last_changes"]["overall"], state["rating"] - before["overall"])
        self.assertEqual(state["rating"], derive_overall(state["ratings"]))

    def test_poker_session_is_format_specific_once_only_and_incomplete_safe(self):
        for cls, key in ((TexasHoldemGame, "texas_holdem"), (FiveCardDrawGame, "five_card_draw"),
                         (SevenCardStudGame, "seven_card_stud")):
            game = cls()
            opponents = [npc("one"), npc("two")]
            game.start_session(opponents, 1000, 10)
            ratings, stats = make_player_rating_bundle(), {}
            states = {entry["id"]: {"ratings": make_player_rating_bundle()} for entry in opponents}
            # A ready session contains no actual result.
            self.assertEqual(settle_poker_session(ratings, stats, states, key, game), 0)
            self.assertEqual(stats, {})
            game.start_session(opponents, 1000, 10)
            for hand in range(1, 6):
                game.hand_number, game.hand_complete = hand, True
                game.player_stack, game.npc_stacks = 2000, [500, 500]
                self.assertTrue(record_poker_showdown(game))
                self.assertFalse(record_poker_showdown(game))
            # Exiting a new unfinished hand must use the previous completed bankroll.
            game.player_stack, game.npc_stacks = 0, [2500, 500]
            game.hand_complete = False
            delta = settle_poker_session(ratings, stats, states, key, game)
            self.assertGreater(delta, 0)
            self.assertEqual(ratings[key], 1000 + delta)
            self.assertTrue(all(ratings[other] == 1000 for other in GAME_RATING_KEYS if GAME_CATEGORIES[other] != GAME_CATEGORIES[key]))
            after = copy.deepcopy((ratings, stats, states))
            self.assertEqual(settle_poker_session(ratings, stats, states, key, game), 0)
            self.assertEqual((ratings, stats, states), after)
            self.assertEqual(sum(state["ratings"][key] - 1000 for state in states.values()) + delta, 0)

    def test_orchestration_free_play_cannot_change_player_or_npc_ratings(self):
        env = main_functions("award_career_rating", "rate_competitive_game", "rate_house_game", "rate_poker_cash_out")
        env["current_game_mode"] = "free"
        before = copy.deepcopy((env["career_ratings"], env["career_rating_results"], env["career_leaderboard_state"]))
        for key in GAME_RATING_KEYS:
            self.assertEqual(env["award_career_rating"](key, 100), 0)
        env["rate_house_game"]("blackjack", 500)
        env["rate_competitive_game"]("score_four", npc(), True)
        env["rate_poker_cash_out"]("texas_holdem", None)
        self.assertEqual((env["career_ratings"], env["career_rating_results"], env["career_leaderboard_state"]), before)
        env["current_game_mode"] = "career"
        self.assertEqual(env["award_career_rating"]("solitaire", 70), 70)
        self.assertEqual(env["career_rating"], 1038.5)
        self.assertEqual(env["award_career_rating"]("overall", 500), 0)

    def test_house_payout_guards_rate_exactly_once_including_free_play(self):
        from blackjack import BlackjackGame
        from roulette import RouletteGame
        no_op = lambda *args, **kwargs: 0
        for mode in ("career", "free"):
            blackjack, roulette = BlackjackGame(), RouletteGame()
            blackjack.start_round(100)
            blackjack.player_hand_results = ["player"]
            blackjack.result = "player"
            blackjack.round_complete = True
            blackjack.payout_claimed = False
            roulette.place_bet("number", 7, 100)
            roulette.result = "7"
            roulette.round_complete = True
            roulette.payout_claimed = False
            env = main_functions("rate_house_game", "settle_blackjack_round", "settle_roulette_round",
                                 current_game_mode=mode, blackjack_game=blackjack, roulette_game=roulette,
                                 career_cash=1000, blackjack_session_net=0, roulette_session_net=0,
                                 blackjack_round_doubled=False, blackjack_round_all_in=False,
                                 blackjack_round_start_bet=100, award_game_xp=no_op,
                                 award_fans_for_cash_win=no_op, lose_fans_for_bad_result=no_op,
                                 process_achievement_event=no_op)
            env["settle_blackjack_round"]()
            env["settle_roulette_round"]()
            after = copy.deepcopy((env["career_cash"], env["career_ratings"], env["career_rating_results"]))
            env["settle_blackjack_round"]()
            env["settle_roulette_round"]()
            self.assertEqual((env["career_cash"], env["career_ratings"], env["career_rating_results"]), after)
            if mode == "career":
                self.assertEqual(env["career_rating_results"]["blackjack"]["played"], 1)
                self.assertEqual(env["career_rating_results"]["roulette"]["played"], 1)
                self.assertEqual(env["career_ratings"]["blackjack"], 1027)
                self.assertEqual(env["career_ratings"]["roulette"], 1027)
            else:
                self.assertEqual(env["career_rating_results"], {})
                self.assertEqual(env["career_ratings"], make_player_rating_bundle())

    def test_head_to_head_forfeit_is_loss_and_duplicate_finish_is_ignored(self):
        from head_to_head import HeadToHeadRace
        no_op = lambda *args, **kwargs: 0
        for won, forfeited in ((True, False), (False, False), (False, True)):
            race = HeadToHeadRace(random.Random(1))
            race.prepare(dict(npc(), rating=1000, race_rating=1000), 1000)
            env = main_functions("rate_competitive_game", "finish_head_to_head_race",
                                 current_game_mode="head_to_head", head_to_head_race=race,
                                 pygame=SimpleNamespace(time=SimpleNamespace(get_ticks=lambda: 4000)),
                                 game=SimpleNamespace(foundations=[[] for _ in range(4)]),
                                 career_leaderboard_state={"rival": {"ratings": make_player_rating_bundle()}},
                                 award_fans_for_rating_win=no_op, lose_fans_for_bad_result=no_op,
                                 award_game_xp=no_op, add_career_news=no_op,
                                 build_head_to_head_story=lambda *args, **kwargs: ("Result", "Story", "sport"),
                                 restore_head_to_head_game_settings=no_op,
                                 player_name="Player", career_fans=0, STATE_CAREER_EVENT_SUMMARY="summary")
            self.assertTrue(env["finish_head_to_head_race"](won, forfeited=forfeited))
            self.assertEqual(env["career_ratings"]["solitaire"], 1024 if won else 976)
            after = copy.deepcopy((env["career_ratings"], env["career_leaderboard_state"], env["career_rating_results"]))
            self.assertFalse(env["finish_head_to_head_race"](won, forfeited=forfeited))
            self.assertEqual((env["career_ratings"], env["career_leaderboard_state"], env["career_rating_results"]), after)

    def test_cash_out_guard_banks_poker_and_rates_once_for_all_formats(self):
        no_op = lambda *args, **kwargs: 0
        for cls, key in ((TexasHoldemGame, "texas_holdem"), (FiveCardDrawGame, "five_card_draw"),
                         (SevenCardStudGame, "seven_card_stud")):
            game = cls()
            game.start_session([npc("one"), npc("two")], 1000, 10)
            game.hand_number, game.hand_complete, game.current_stage = 1, True, "showdown"
            game.player_stack, game.npc_stacks = 2000, [500, 500]
            record_poker_showdown(game)
            values = dict(career_cash=500, award_game_xp=no_op, lose_fans_for_bad_result=no_op, auto_save_career=no_op,
                          STATE_CAREER_EVENT_SELECT="select", STATE_FREE_PLAY_SELECT="free")
            values.update({key + "_game": game, key + "_buy_in_active": True,
                           key + "_starting_stack": 1000, key + "_session_net": 0})
            env = main_functions("rate_poker_cash_out", "finish_" + key + "_session", **values)
            env["finish_" + key + "_session"]()
            self.assertEqual(env["career_cash"], 2500)
            self.assertEqual(env["career_rating_results"][key]["played"], 1)
            after = copy.deepcopy((env["career_cash"], env["career_ratings"], env["career_leaderboard_state"]))
            env["finish_" + key + "_session"]()
            self.assertEqual((env["career_cash"], env["career_ratings"], env["career_leaderboard_state"]), after)

    def test_rated_format_controls_npc_skill_without_leaking_other_ratings(self):
        entry = npc()
        entry["career_ratings"] = dict.fromkeys(GAME_RATING_KEYS, 800)
        entry["career_ratings"]["seven_card_stud"] = 2800
        factors = []
        for cls in (TexasHoldemGame, FiveCardDrawGame, SevenCardStudGame):
            game = cls()
            game.start_session([entry], 1000, 10)
            factors.append(game.get_npc_skill_factor(0))
        self.assertEqual(factors[0], factors[1])
        self.assertGreater(factors[2], factors[0])
        low, high = ScoreFourGame(), ScoreFourGame()
        random.seed(2)
        low.start_competitive_session(rating=800)
        random.seed(2)
        high.start_competitive_session(rating=2800)
        self.assertGreater(low.npc_solve_time_seconds, high.npc_solve_time_seconds)


if __name__ == "__main__":
    unittest.main()

