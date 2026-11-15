"""Phase 1: move every root module (except main.py and version.py) and shared/ into solitaireplus/.

    python tools/refactor/phase1_move.py --dry-run   # show the plan and the import rewrites
    python tools/refactor/phase1_move.py             # rewrite imports, then git mv the files

Steps: rewrite imports in every Python file of the repository (moved modules, main.py,
multiplayer/, tests/, tools/, the two stray root files), then `git mv` the modules to their
new homes, delete the root compatibility shims and create the package __init__ files.
Prints every import it could not handle; fix those by hand.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from refactor.imports import rewrite_file  # noqa: E402

PACKAGE = "solitaireplus"

# old module -> new module (inside solitaireplus/)
MOVES = {
    # app
    "runtime_support": "app.runtime_support",
    "app_settings": "app.app_settings",
    "update_check": "app.update_check",
    "multiplayer_launcher": "app.multiplayer_launcher",
    "audio": "app.audio",
    "settings": "app.settings",
    "cosmetic_assets": "app.cosmetic_assets",
    "help_history": "app.help_history",
    # shared UI helpers
    "shared.image_cache": "ui.image_cache",
    # solitaire
    "game": "games.solitaire.rules",
    "card": "games.solitaire.card",
    "deck": "games.solitaire.deck",
    "solitaire_assist": "games.solitaire.assist",
    "solitaire_race_deals": "games.solitaire.race_deals",
    "solitaire_restart": "games.solitaire.restart",
    "head_to_head": "games.solitaire.head_to_head",
    "head_to_head_ui": "games.solitaire.head_to_head_ui",
    # poker
    "texas_holdem": "games.poker.holdem",
    "texas_holdem_ui": "games.poker.holdem_ui",
    "five_card_draw": "games.poker.five_card_draw",
    "five_card_draw_ui": "games.poker.five_card_draw_ui",
    "seven_card_stud": "games.poker.seven_card_stud",
    "seven_card_stud_ui": "games.poker.seven_card_stud_ui",
    "five_o_poker": "games.poker.five_o",
    "five_o_poker_ui": "games.poker.five_o_ui",
    "blind_mans_bluff": "games.poker.blind_mans_bluff",
    "blind_mans_bluff_ui": "games.poker.blind_mans_bluff_ui",
    "bluff_presentation": "games.poker.bluff_presentation",
    "niche_poker_common": "games.poker.niche_common",
    "poker_ai": "games.poker.ai",
    "poker_recap": "games.poker.recap",
    "poker_quick_chat": "games.poker.quick_chat",
    "poker_quick_chat_adapter": "games.poker.quick_chat_adapter",
    "poker_variant_quick_chat": "games.poker.variant_quick_chat",
    "holdem_turn_flow": "games.poker.turn_flow",
    "shared.poker_core": "games.poker.core",
    "shared.poker_strategy": "games.poker.strategy",
    "shared.poker_speech": "games.poker.speech",
    "shared.poker_ui_assets": "games.poker.ui_assets",
    "shared.poker_learning": "games.poker.learning",
    "shared.texas_holdem_chat": "games.poker.holdem_chat",
    # casino
    "blackjack": "games.casino.blackjack",
    "blackjack_presentation": "games.casino.blackjack_presentation",
    "roulette": "games.casino.roulette",
    "roulette_ui": "games.casino.roulette_ui",
    "horse_races": "games.casino.horse_races",
    "horse_races_ui": "games.casino.horse_races_ui",
    "faro": "games.casino.faro",
    "faro_ui": "games.casino.faro_ui",
    # casual cards
    "crazy_eights": "games.cards.crazy_eights",
    "crazy_eights_ui": "games.cards.crazy_eights_ui",
    "bango": "games.cards.bango",
    "bango_ui": "games.cards.bango_ui",
    "score_four": "games.cards.score_four",
    "score_four_ui": "games.cards.score_four_ui",
    "score_four_difficulty": "games.cards.score_four_difficulty",
    # arcade
    "arcade_support": "games.arcade.support",
    "king_pong": "games.arcade.king_pong",
    "battle_bosses": "games.arcade.battle_bosses",
    "battle_bosses_game": "games.arcade.battle_bosses_game",
    "ace_invaders": "games.arcade.ace_invaders",
    "ace_invaders_game": "games.arcade.ace_invaders_game",
    "suit_snake": "games.arcade.suit_snake",
    "suit_snake_game": "games.arcade.suit_snake_game",
    # cryptid
    "cryptid_creatures": "games.cryptid.creatures",
    "cryptid_creatures_ai": "games.cryptid.ai",
    "cryptid_creatures_ui": "games.cryptid.ui",
    "cryptid_cards": "games.cryptid.cards",
    "cryptid_collection": "games.cryptid.collection",
    "cryptid_collection_ui": "games.cryptid.collection_ui",
    "cryptid_battle_feedback": "games.cryptid.battle_feedback",
    "cryptid_encounter_view": "games.cryptid.encounter_view",
    # dead man's hand
    "dead_mans_hand": "games.dead_mans_hand.levels",
    "dead_mans_hand_game": "games.dead_mans_hand.game",
    "dead_mans_hand_weapons": "games.dead_mans_hand.weapons",
    "dead_mans_hand_pvp": "games.dead_mans_hand.pvp",
    # career
    "career_activities": "career.activities",
    "career_activities_ui": "career.activities_ui",
    "alien_night": "career.alien_night",
    "career_asset_images": "career.asset_images",
    "career_event_progress": "career.event_progress",
    "career_fans": "career.fans",
    "career_hub_controls": "career.hub_controls",
    "career_news": "career.news",
    "career_npc_development": "career.npc_development",
    "career_npc_world": "career.npc_world",
    "career_rating_events": "career.rating_events",
    "career_ratings": "career.ratings",
    "career_session_summary": "career.session_summary",
    "career_time_warp": "career.time_warp",
    "career_world_flavor": "career.world_flavor",
    "case_opening": "career.case_opening",
    "case_opening_ui": "career.case_opening_ui",
    "press_interview": "career.events.press_interview",
    "autograph_event": "career.events.autographs",
    # npc
    "npc_manager": "npc.manager",
    "npc_avatars": "npc.avatars",
    "npc_portraits": "npc.portraits",
    "npc_portrait_ui": "npc.portrait_ui",
    "npc_personality_ui": "npc.personality_ui",
    "shared.npc_personality": "npc.personality",
    "shared.npc_personality_chat": "npc.personality_chat",
    # profile / progression
    "profile": "profile.saves",
    "profile_avatar_assets": "profile.avatar",
    "achievements": "profile.achievements",
    "achievements_ui": "menus.achievements_screen",
    "reward_cosmetics": "profile.cosmetics",
    "rating_unlocks": "profile.unlocks",
    # debug
    "debug_menu": "debug.menu",
    "debug_poker_select": "debug.poker_select",
    "debug_unlocks": "debug.unlocks",
}

# Root compatibility shims for shared/: deleted, their names now point at the real module.
SHIMS = {
    "poker_core": "shared.poker_core",
    "poker_strategy": "shared.poker_strategy",
    "poker_speech": "shared.poker_speech",
    "poker_ui_assets": "shared.poker_ui_assets",
    "poker_learning": "shared.poker_learning",
    "npc_personality": "shared.npc_personality",
    "npc_personality_chat": "shared.npc_personality_chat",
    "texas_holdem_chat": "shared.texas_holdem_chat",
}

PACKAGE_DOCS = {
    "": "Solitaire+ game code. main.py (repository root) is the entry point.",
    "app": "App-wide services: paths, settings, audio, windowing, the main loop and its state.",
    "ui": "Drawing helpers shared by every screen (buttons, text, panels, image caches).",
    "menus": "Menu screens: splash, main menu, mode select, options, customize, help, achievements.",
    "profile": "Profiles and progression: saves, avatar, XP and levels, achievements, cosmetics, unlocks.",
    "career": "Career mode: hub, calendar, jobs, homes, leaderboards, news, ratings, fans, nights.",
    "career.events": "Career event nights: event select, press interviews, autographs, summaries.",
    "npc": "NPC roster, personalities, chat, portraits and avatars.",
    "games": "The games, one package per family.",
    "games.solitaire": "Klondike Solitaire rules and screen, deals, restart, Head-to-Head races.",
    "games.poker": "Poker: shared core/strategy/AI and the Hold'em, Draw, Stud, Five-O and Blind Man's Bluff tables.",
    "games.casino": "Casino games: Blackjack, Roulette, Horse Races, Faro.",
    "games.cards": "Casual card games: Crazy Eights, Bango, Score Four.",
    "games.arcade": "Arcade machines: King Pong, Battle Bosses, Ace Invaders, Suit Snake, and the arcade hub.",
    "games.cryptid": "Cryptid Creatures card battler.",
    "games.dead_mans_hand": "Dead Man's Hand shooter.",
    "debug": "The F10 debug menu and its actions.",
}

SKIP_DIRS = {".venv", "venv", "build", "dist", "release", ".harness_out", "__pycache__", ".git", ".idea"}


def full_moves() -> dict[str, str]:
    moves = {old: f"{PACKAGE}.{new}" for old, new in MOVES.items()}
    for shim, real in SHIMS.items():
        moves[shim] = moves[real]
    return moves


def old_path(old: str) -> Path:
    return ROOT / (old.replace(".", "/") + ".py")


def new_path(new: str) -> Path:
    return ROOT / (new.replace(".", "/") + ".py")


def local_names(path: Path) -> set[str]:
    """Top-level module names that this file's own folder(s) provide on its import path."""
    rel = path.relative_to(ROOT)
    folders = []
    if rel.parts[0] == "multiplayer":
        folders = [ROOT / "multiplayer"] + ([ROOT / "multiplayer" / "tests"] if "tests" in rel.parts else [])
    elif rel.parts[0] in {"tests", "tools"}:
        folders = [path.parent, ROOT / rel.parts[0]]
    names = set()
    for folder in folders:
        names |= {p.stem for p in folder.glob("*.py")}
        names |= {p.name for p in folder.iterdir() if p.is_dir() and (p / "__init__.py").exists()}
    return names


def make_resolver(path: Path, moves: dict[str, str]):
    local = local_names(path)

    def resolve(name: str):
        if name.split(".")[0] in local:
            return None
        return moves.get(name)

    return resolve


# The harness must keep running old checkouts (it imports either layout on purpose), and the
# refactoring tools describe the old names.
SKIP_PATHS = {ROOT / "tools" / "harness", ROOT / "tools" / "refactor"}


def python_files():
    for current, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".harness")
                   and Path(current) / d not in SKIP_PATHS]
        for name in files:
            if name.endswith(".py"):
                yield Path(current) / name


def git(*args):
    subprocess.run(["git", *args], cwd=ROOT, check=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    moves = full_moves()

    # sanity: every root module is accounted for
    root_modules = {p.stem for p in ROOT.glob("*.py")}
    unplanned = root_modules - set(MOVES) - set(SHIMS) - {"main", "version", "verify_solitaire_state",
                                                          "test_dead_mans_hand_weapon_system"}
    if unplanned:
        raise SystemExit(f"no destination for root module(s): {sorted(unplanned)}")
    shared_modules = {f"shared.{p.stem}" for p in (ROOT / "shared").glob("*.py") if p.stem != "__init__"}
    if shared_modules - set(MOVES):
        raise SystemExit(f"no destination for: {sorted(shared_modules - set(MOVES))}")

    total, problems = 0, []
    for path in sorted(python_files()):
        if path.parent == ROOT and path.stem in SHIMS:
            continue
        if args.dry_run:
            from refactor.imports import rewrite_source
            new, changes, found = rewrite_source(path.read_text(encoding="utf-8"), make_resolver(path, moves), str(path))
        else:
            changes, found = rewrite_file(path, make_resolver(path, moves))
        problems += found
        if changes:
            total += changes
            print(f"  {changes:4d}  {path.relative_to(ROOT)}")
    print(f"{total} import(s) rewritten")
    for problem in problems:
        print("PROBLEM:", problem)
    if args.dry_run:
        return 1 if problems else 0

    # packages
    for package, doc in PACKAGE_DOCS.items():
        folder = ROOT / PACKAGE / package.replace(".", "/")
        folder.mkdir(parents=True, exist_ok=True)
        init = folder / "__init__.py"
        if not init.exists():
            init.write_text(f'"""{doc}"""\n', encoding="utf-8")
    # moves
    for old, new in MOVES.items():
        source, target = old_path(old), new_path(f"{PACKAGE}.{new}")
        target.parent.mkdir(parents=True, exist_ok=True)
        git("mv", str(source.relative_to(ROOT)), str(target.relative_to(ROOT)))
    for shim in SHIMS:
        git("rm", "-q", f"{shim}.py")
    git("rm", "-q", "shared/__init__.py")
    git("add", PACKAGE)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
