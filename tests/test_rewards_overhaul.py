from unittest.mock import patch
from pathlib import Path

from arcade_support import ARCADE_PRIZE_CATALOG, make_default_arcade_state, redeem_prize
from case_opening import ITEMS, new_case_state, purchase
from reward_cosmetics import unlock_reward


def test_requested_trophy_names_are_preserved_on_stable_ids():
    assert ITEMS["table_champion"]["name"] == "3rd Grade Science Fair Runner-up"
    assert ITEMS["golden_shuffler"]["name"] == "Spelling Bee Champ"
    assert ITEMS["velvet_penguin"]["name"] == "Twitter Blue Check"
    assert ITEMS["neon_ace"]["name"] == "Meaningless Prem Title"
    assert ITEMS["origami_dragon"]["name"] == "Coolest Gambler Award"


def test_rating_case_rewards_are_category_based_with_custom_art_hooks():
    expected = {
        "rating_strategy": ("strategy", "items/rating_strategy.png"),
        "rating_poker": ("poker", "items/rating_poker.png"),
        "rating_casino": ("casino", "items/rating_casino.png"),
    }
    for item_id, (target, image) in expected.items():
        assert ITEMS[item_id]["kind"] == "rating"
        assert ITEMS[item_id]["game"] == target
        assert ITEMS[item_id]["image"] == image


def test_scaled_cash_and_fan_rewards_use_current_player_amounts():
    with patch("case_opening.choose_item", return_value=ITEMS["cash_pouch"]):
        receipt, _wallet = purchase(new_case_state(), "street", 400_000)
    assert receipt["amount"] == 40_000

    with patch("case_opening.choose_item", return_value=ITEMS["fan_club"]):
        receipt, _wallet = purchase(new_case_state(), "street", 400_000, fans=400_000)
    assert receipt["amount"] == 6_000


def test_fixed_super_jackpots_are_exactly_200k():
    for item_id in ("cash_jackpot", "fan_jackpot"):
        with patch("case_opening.choose_item", return_value=ITEMS[item_id]):
            receipt, _wallet = purchase(new_case_state(), "collector", 500_000, fans=500_000)
        assert receipt["amount"] == 200_000
        assert ITEMS[item_id]["weight"] == 0.08
        assert ITEMS[item_id]["jackpot"] is True


def test_case_cosmetics_include_all_requested_reward_types():
    wanted = {
        "Garden Gnomes": ("background", "bg_case_garden_gnomes"),
        "Ben Katz Cocoa": ("background", "bg_case_ben_katz_cocoa"),
        "Pigs on the Couch": ("background", "bg_case_pigs_on_the_couch"),
        "Dust Deux": ("felt", "f_case_dust_deux"),
        "Joseph Camel": ("felt", "f_case_joseph_camel"),
        "Case Cracker": ("title", "title_case_cracker"),
        "Gamble on Rose": ("title", "title_gamble_on_rose"),
        "Pocket Watch": ("cursor", "cursor_pocket_watch"),
    }
    found = {item["name"]: (item.get("cosmetic_type"), item.get("asset_id"))
             for item in ITEMS.values() if item.get("kind") == "cosmetic"}
    for name, metadata in wanted.items():
        assert found[name] == metadata


def test_arcade_counter_contains_requested_cosmetics_and_redeems_them():
    wanted = {
        "Full Shelf", "Saturday Cade", "Ticketz", "Halcyon Days",
        "8-bit", "Robofelt", "Cade Champ", "Joystick Jester",
        "Carpal Tunnel", "Joystick",
    }
    cosmetics = [p for p in ARCADE_PRIZE_CATALOG if p.get("kind") == "cosmetic"]
    assert {p["name"] for p in cosmetics} == wanted
    assert {p["cosmetic_type"] for p in cosmetics} == {"background", "felt", "title", "cursor"}

    prize = next(p for p in cosmetics if p["name"] == "Full Shelf")
    state = make_default_arcade_state()
    state["tickets"] = prize["cost"]
    success, state, _message, awarded = redeem_prize(state, prize["id"])
    assert success is True
    assert awarded["asset_id"] == "bg_arcade_full_shelf"
    assert prize["id"] in state["trophies"]  # legacy ownership bag; contains every redeemed counter prize


def test_shared_unlock_helper_supports_all_four_cosmetic_categories():
    backgrounds, felts, titles, cursors = set(), set(), set(), set()
    assert unlock_reward("background", "bg_x", backgrounds, felts, titles, cursors)
    assert unlock_reward("felt", "f_x", backgrounds, felts, titles, cursors)
    assert unlock_reward("title", "title_x", backgrounds, felts, titles, cursors)
    assert unlock_reward("cursor", "cursor_x", backgrounds, felts, titles, cursors)
    assert backgrounds == {"bg_x"}
    assert felts == {"f_x"}
    assert titles == {"title_x"}
    assert cursors == {"cursor_x"}


def test_main_wires_paged_counter_custom_buttons_and_cursor_ownership():
    source = Path("main.py").read_text(encoding="utf-8")
    for filename in (
        "continue.png", "redeem_tickets.png", "trophy_room.png", "back_to_prize_counter.png"
    ):
        assert f"assets/arcade/ui/{filename}" in source
    assert "ARCADE_PRIZES_PER_PAGE = 4" in source
    assert 'cosmetics[\n        "unlocked_cursors"\n    ]' in source
    assert "redeem_arcade_prize_for_career" in source


def _extract_function(name):
    import ast
    tree = ast.parse(Path("main.py").read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    return compile(ast.Module(body=[node], type_ignores=[]), f"extracted {name}", "exec")


def test_case_transaction_unlocks_non_felt_cosmetics_and_rolls_back_atomically():
    import copy
    from case_opening import purchase as purchase_case
    from career_ratings import apply_rating_change, make_player_rating_bundle

    env = {
        "copy": copy,
        "current_game_mode": "career",
        "case_collection_state": new_case_state(),
        "career_cash": 100_000,
        "career_ratings": make_player_rating_bundle(1000),
        "career_rating": 1000,
        "career_fans": 400_000,
        "unlocked_menu_backgrounds": {"bg_default"},
        "unlocked_felts": {"f_default"},
        "unlocked_titles": {"title_default"},
        "unlocked_cursors": {"cursor"},
        "purchase_loot_case": purchase_case,
        "apply_rating_change": apply_rating_change,
        "clamp_fans": lambda n: max(0, n),
        "CASE_ITEMS": ITEMS,
        "auto_save_career": lambda: None,
    }
    exec(_extract_function("buy_case_for_screen"), env)

    with patch("case_opening.choose_item", return_value=ITEMS["case_garden_gnomes"]):
        env["buy_case_for_screen"]("prestige")
    assert "bg_case_garden_gnomes" in env["unlocked_menu_backgrounds"]

    before = {
        "state": __import__("copy").deepcopy(env["case_collection_state"]),
        "cash": env["career_cash"],
        "cursors": set(env["unlocked_cursors"]),
    }
    env["auto_save_career"] = lambda: (_ for _ in ()).throw(OSError("disk full"))
    with patch("case_opening.choose_item", return_value=ITEMS["case_pocket_watch"]):
        try:
            env["buy_case_for_screen"]("prestige")
        except OSError:
            pass
        else:
            raise AssertionError("save failure should propagate")
    assert env["case_collection_state"] == before["state"]
    assert env["career_cash"] == before["cash"]
    assert env["unlocked_cursors"] == before["cursors"]


def test_arcade_cosmetic_redeem_unlocks_customize_reward():
    from arcade_support import clone_arcade_state

    prize = next(p for p in ARCADE_PRIZE_CATALOG if p["name"] == "Joystick")
    state = make_default_arcade_state()
    state["tickets"] = prize["cost"]
    env = {
        "arcade_state": state,
        "clone_arcade_state": clone_arcade_state,
        "redeem_prize": redeem_prize,
        "unlocked_menu_backgrounds": {"bg_default"},
        "unlocked_felts": {"f_default"},
        "unlocked_titles": {"title_default"},
        "unlocked_cursors": {"cursor"},
        "auto_save_career": lambda: None,
    }
    exec(_extract_function("redeem_arcade_prize_for_career"), env)
    success, _message, awarded = env["redeem_arcade_prize_for_career"](prize["id"])
    assert success is True
    assert awarded["name"] == "Joystick"
    assert "cursor_joystick" in env["unlocked_cursors"]
