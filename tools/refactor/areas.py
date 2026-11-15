"""Which top-level names of solitaireplus/legacy.py belong to which area (for Phases 3-10).

    python tools/refactor/areas.py [--json OUT] [--area NAME]

Seeds: each screen's loop_event_/loop_draw_/loop_late_ functions belong to that screen's area
(SCREEN_AREAS below, from the brief's per-screen map), plus explicit SEEDS. Then ownership spreads
backwards through the use graph: a legacy name whose users (other legacy top-level names) all
belong to one area joins that area. Names used by several areas, or by module-level start-up
code, stay unassigned (shared) and are listed separately.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

import libcst as cst
from libcst.metadata import (ExpressionContextProvider, GlobalScope, MetadataWrapper, ParentNodeProvider,
                             ScopeProvider)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from refactor.analysis import refers_to_global  # noqa: E402

LEGACY = ROOT / "solitaireplus" / "legacy.py"

AREAS = ["menus", "profile", "solitaire", "career", "casino", "poker", "cards", "arcade", "cryptid", "dmh", "debug"]

SCREEN_AREAS = {
    "splash": "menus", "menu": "menus", "mode_select": "menus", "free_play_select": "menus", "difficulty": "menus",
    "how_to_play": "menus", "achievements": "menus", "options": "menus", "customize": "menus",
    "profile_select": "profile", "profile": "profile", "recap": "profile", "level_up": "profile",
    "playing": "solitaire",
    "career_hub": "career", "career_activity": "career", "career_jobs": "career", "career_real_estate": "career",
    "career_leaderboards": "career", "career_leaderboard_bio": "career", "career_news": "career",
    "career_event_select": "career", "career_event": "career", "career_event_summary": "career",
    "case_opening": "career",
    "cryptid_creatures": "cryptid",
    "crazy_eights": "cards", "bango": "cards", "score_four": "cards", "score_four_mode_select": "cards",
    "score_four_opponent_select": "cards",
    "texas_holdem": "poker", "texas_holdem_buy_in": "poker", "five_card_draw": "poker",
    "five_card_draw_buy_in": "poker", "seven_card_stud": "poker", "seven_card_stud_buy_in": "poker",
    "five_o_poker": "poker", "blind_mans_bluff": "poker", "debug_poker_npc_select": "poker",
    "blackjack_bet": "casino", "blackjack": "casino", "roulette": "casino", "horse_races": "casino", "faro": "casino",
    "arcade_token_exchange": "arcade", "arcade_prize_counter": "arcade", "arcade_trophy_room": "arcade",
    "king_pong_opponent_select": "arcade", "battle_bosses_opponent_select": "arcade",
    "ace_invaders_difficulty_select": "arcade", "suit_snake_difficulty_select": "arcade",
    "king_pong": "arcade", "battle_bosses": "arcade", "ace_invaders": "arcade", "suit_snake": "arcade",
    "dead_mans_hand": "dmh", "debug_menu": "debug",
}

# Extra seeds from the brief's per-screen map (functions that clearly belong to an area even when
# other areas call them; they move with that area and the callers refer to them through it).
SEEDS = {
    "menus": ["draw_splash_screen", "draw_main_menu", "draw_mode_select", "draw_free_play_select",
              "draw_difficulty_screen", "draw_how_to_play", "draw_solitaire_help_diagram", "draw_options_menu",
              "draw_customize_menu", "draw_update_banner", "draw_update_options_panel"],
    "profile": ["draw_profile_select_screen", "draw_delete_profile_confirmation", "get_profile_slot_display_data",
                "draw_profile_screen", "draw_round_recap", "draw_level_up_screen"],
    "solitaire": ["draw_gameplay_ui", "start_head_to_head_event", "finish_head_to_head_race"],
    "career": ["draw_career_hub", "draw_career_jobs", "draw_career_real_estate", "draw_career_leaderboards",
               "draw_career_leaderboard_bio", "draw_career_news", "draw_career_event", "draw_career_event_summary",
               "_draw_career_event_select", "draw_arcade_night_select"],
    "casino": ["settle_blackjack_round", "settle_roulette_round", "settle_horse_race_result",
               "try_place_or_remove_roulette_bet"],
    "poker": ["process_texas_holdem_showdown", "start_texas_holdem_session", "finish_texas_holdem_session"],
    "cards": ["start_crazy_eights_session", "claim_crazy_eights_result", "draw_score_four_opponent_select",
              "draw_score_four", "settle_score_four_session_result"],
    "dmh": ["start_dead_mans_hand", "exit_dead_mans_hand"],
}


def analyse(source: str):
    wrapper = MetadataWrapper(cst.parse_module(source))
    module = wrapper.module
    scopes = wrapper.resolve(ScopeProvider)
    contexts = wrapper.resolve(ExpressionContextProvider)
    parents = wrapper.resolve(ParentNodeProvider)
    top_names: dict[str, int] = {}
    order = []
    for index, statement in enumerate(module.body):
        names = set()
        if isinstance(statement, (cst.FunctionDef, cst.ClassDef)):
            names.add(statement.name.value)
        elif isinstance(statement, cst.SimpleStatementLine):
            for small in statement.body:
                if isinstance(small, cst.Assign):
                    for target in small.targets:
                        for node in _names_in(target.target):
                            names.add(node)
        for name in names:
            top_names.setdefault(name, index)
        order.append(names)

    users = collections.defaultdict(set)        # name -> set of top-level names using it ("<module>" for start-up code)

    class Visitor(cst.CSTVisitor):
        def __init__(self):
            self.current = []

        def visit_Module(self, node):
            for index, statement in enumerate(node.body):
                # a def's body, or an assignment's value, is "used by" the name it defines;
                # only bare start-up statements (calls, loops, ifs) count as "<module>"
                owner = sorted(order[index])[0] if order[index] else None
                self.current.append(owner or "<module>")
                statement.visit(self)
                self.current.pop()
            return False

        def visit_Name(self, node):
            context = contexts.get(node)
            if context is None or node.value not in top_names:
                return
            if isinstance(parents.get(node), (cst.FunctionDef, cst.ClassDef)) and parents[node].name is node:
                return
            scope = scopes.get(node)
            if scope is None:
                return
            if isinstance(scope, GlobalScope) or refers_to_global(scope, node):
                user = self.current[-1] if self.current else "<module>"
                if user != node.value:
                    users[node.value].add(user)

    module.visit(Visitor())
    return top_names, users


def _names_in(target):
    if isinstance(target, cst.Name):
        return [target.value]
    if isinstance(target, (cst.Tuple, cst.List)):
        out = []
        for element in target.elements:
            out += _names_in(element.value)
        return out
    return []


def assign(top_names, users, by_screen=False, seeds=None):
    """Owner (area, or screen slug with by_screen=True) of every legacy name that has one."""
    owner: dict[str, str] = {}
    for name in top_names:
        for prefix in ("loop_event_", "loop_draw_", "loop_late_", "loop_enter_", "loop_leave_"):
            if name.startswith(prefix):
                slug = name[len(prefix):]
                group = slug if by_screen else SCREEN_AREAS.get(slug)
                if group:
                    owner[name] = group
    for group, names in (seeds if seeds is not None else ({} if by_screen else SEEDS)).items():
        for name in names:
            if name in top_names:
                owner.setdefault(name, group)
    changed = True
    while changed:
        changed = False
        for name in top_names:
            if name in owner:
                continue
            user_set = users.get(name, set())
            if not user_set or "<module>" in user_set:
                continue
            areas = {owner.get(user) for user in user_set}
            if len(areas) == 1 and None not in areas:
                owner[name] = areas.pop()
                changed = True
    return owner


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json")
    parser.add_argument("--area")
    parser.add_argument("--screens", action="store_true", help="group by screen instead of area")
    args = parser.parse_args(argv)
    top_names, users = analyse(LEGACY.read_text(encoding="utf-8"))
    owner = assign(top_names, users, by_screen=args.screens)
    if args.screens:
        groups = collections.defaultdict(list)
        for name, group in owner.items():
            groups[group].append(name)
        for group in sorted(groups):
            print(f"{group:32} {len(groups[group]):4d}")
        if args.json:
            Path(args.json).write_text(json.dumps({g: sorted(v) for g, v in groups.items()}, indent=1), encoding="utf-8")
        return 0
    by_area = collections.defaultdict(list)
    for name, area in owner.items():
        by_area[area].append(name)
    shared = sorted(name for name in top_names if name not in owner)
    for area in AREAS:
        print(f"{area:10} {len(by_area[area]):4d} names")
    print(f"{'shared':10} {len(shared):4d} names (used by several areas or by start-up code)")
    if args.area:
        print("\n".join(sorted(by_area[args.area])))
    if args.json:
        Path(args.json).write_text(json.dumps({"areas": {a: sorted(v) for a, v in by_area.items()}, "shared": shared,
                                               "users": {k: sorted(v) for k, v in users.items()}}, indent=1),
                                   encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
