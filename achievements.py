from __future__ import annotations

import os
from copy import deepcopy


ACHIEVEMENT_DEFINITIONS = [
    {
        "id": "table_clear", "category": "Poker", "title": "Table Clear",
        "description": "Knock out every rival at a Hold'em, Draw, or Stud table.",
        "difficulty": "elite", "icon": "assets/achievements/icons/table_clear.png",
        "condition": ("stat_gte", "poker_tables_cleared", 1),
    },
    # ==================================================
    # SOLITAIRE
    # ==================================================
    {
        "id": "first_solitaire_win",
        "category": "Solitaire",
        "title": "First Foundation",
        "description": "Win your first game of Klondike Solitaire.",
        "difficulty": "easy",
        "icon": "assets/achievements/icons/first_solitaire_win.png",
        "condition": ("stat_gte", "solitaire_wins", 1),
    },
    {
        "id": "solitaire_10_wins",
        "category": "Solitaire",
        "title": "Getting the Hang of It",
        "description": "Win 10 games of Klondike Solitaire.",
        "difficulty": "normal",
        "icon": "assets/achievements/icons/solitaire_10_wins.png",
        "condition": ("stat_gte", "solitaire_wins", 10),
    },
    {
        "id": "solitaire_50_wins",
        "category": "Solitaire",
        "title": "Foundation Regular",
        "description": "Win 50 games of Klondike Solitaire.",
        "difficulty": "hard",
        "icon": "assets/achievements/icons/solitaire_50_wins.png",
        "condition": ("stat_gte", "solitaire_wins", 50),
    },
    {
        "id": "under_100_moves",
        "category": "Solitaire",
        "title": "Efficient Hands",
        "description": "Win a Klondike game in fewer than 100 moves.",
        "difficulty": "normal",
        "icon": "assets/achievements/icons/under_100_moves.png",
        "condition": ("flag", "solitaire_under_100_moves"),
    },
    {
        "id": "under_5_minutes",
        "category": "Solitaire",
        "title": "Five-Minute Foundation",
        "description": "Win a Klondike game in under five minutes.",
        "difficulty": "hard",
        "icon": "assets/achievements/icons/under_5_minutes.png",
        "condition": ("flag", "solitaire_under_5_minutes"),
    },
    {
        "id": "challenge_no_undo",
        "category": "Solitaire",
        "title": "No Going Back",
        "description": "Win the No Undo Career challenge.",
        "difficulty": "hard",
        "icon": "assets/achievements/icons/challenge_no_undo.png",
        "condition": ("flag", "challenge_no_undo"),
    },
    {
        "id": "challenge_no_hints",
        "category": "Solitaire",
        "title": "On Your Own",
        "description": "Win the No Hints Career challenge.",
        "difficulty": "hard",
        "icon": "assets/achievements/icons/challenge_no_hints.png",
        "condition": ("flag", "challenge_no_hints"),
    },
    {
        "id": "challenge_draw_3",
        "category": "Solitaire",
        "title": "Three at a Time",
        "description": "Win the 3 Draw Career challenge.",
        "difficulty": "hard",
        "icon": "assets/achievements/icons/challenge_draw_3.png",
        "condition": ("flag", "challenge_draw_3"),
    },

    # ==================================================
    # BLACKJACK
    # ==================================================
    {
        "id": "first_blackjack",
        "category": "Blackjack",
        "title": "Natural",
        "description": "Be dealt your first natural blackjack.",
        "difficulty": "easy",
        "icon": "assets/achievements/icons/first_blackjack.png",
        "condition": ("stat_gte", "blackjack_naturals", 1),
    },
    {
        "id": "blackjack_double_win",
        "category": "Blackjack",
        "title": "Double Trouble",
        "description": "Win a hand after doubling down.",
        "difficulty": "normal",
        "icon": "assets/achievements/icons/blackjack_double_win.png",
        "condition": ("flag", "blackjack_double_win"),
    },
    {
        "id": "blackjack_low_stand",
        "category": "Blackjack",
        "title": "Low Roller",
        "description": "Win after standing on a total below 12.",
        "difficulty": "secret",
        "secret": True,
        "locked_description": "Win a Blackjack hand in an unusually stubborn way.",
        "icon": "assets/achievements/icons/blackjack_low_stand.png",
        "condition": ("flag", "blackjack_low_stand"),
        "reward": {"type": "title", "id": "title_low_roller"},
    },
    {
        "id": "blackjack_five_hits",
        "category": "Blackjack",
        "title": "Hit Parade",
        "description": "Win after taking at least five hits.",
        "difficulty": "hard",
        "icon": "assets/achievements/icons/blackjack_five_hits.png",
        "condition": ("flag", "blackjack_five_hits"),
    },
    {
        "id": "blackjack_1000_win",
        "category": "Blackjack",
        "title": "Four Figures",
        "description": "Win at least $1,000 on a single Blackjack hand.",
        "difficulty": "hard",
        "icon": "assets/achievements/icons/blackjack_1000_win.png",
        "condition": ("flag", "blackjack_1000_win"),
    },
    {
        "id": "blackjack_5000_total",
        "category": "Blackjack",
        "title": "Blackjack Bankroll",
        "description": "Accumulate $5,000 in Blackjack winnings.",
        "difficulty": "elite",
        "icon": "assets/achievements/icons/blackjack_5000_total.png",
        "condition": ("stat_gte", "blackjack_total_profit", 5000),
    },
    {
        "id": "blackjack_all_in",
        "category": "Blackjack",
        "title": "Nothing Left Behind",
        "description": "Win a Blackjack hand after wagering everything available.",
        "difficulty": "legendary",
        "secret": True,
        "locked_description": "Risk absolutely everything and survive.",
        "icon": "assets/achievements/icons/blackjack_all_in.png",
        "condition": ("flag", "blackjack_all_in_win"),
        "reward": {"type": "background", "id": "bg_blackjack_all_in"},
    },

    # ==================================================
    # ROULETTE
    # ==================================================
    {
        "id": "first_roulette_win",
        "category": "Roulette",
        "title": "Wheel Winner",
        "description": "Finish a Roulette spin with a profit.",
        "difficulty": "easy",
        "icon": "assets/achievements/icons/first_roulette_win.png",
        "condition": ("stat_gte", "roulette_wins", 1),
    },
    {
        "id": "roulette_1000_win",
        "category": "Roulette",
        "title": "Wheel of Fortune",
        "description": "Win at least $1,000 on one Roulette spin.",
        "difficulty": "hard",
        "icon": "assets/achievements/icons/roulette_1000_win.png",
        "condition": ("flag", "roulette_1000_win"),
        "reward": {"type": "background", "id": "bg_roulette_1000"},
    },
    {
        "id": "roulette_5000_total",
        "category": "Roulette",
        "title": "House Money",
        "description": "Accumulate $5,000 in Roulette winnings.",
        "difficulty": "elite",
        "icon": "assets/achievements/icons/roulette_5000_total.png",
        "condition": ("stat_gte", "roulette_total_profit", 5000),
    },
    {
        "id": "roulette_number_9",
        "category": "Roulette",
        "title": "Nine Lives",
        "description": "Win a spin after betting only on number 9.",
        "difficulty": "secret",
        "secret": True,
        "locked_description": "A single number. A very specific number.",
        "icon": "assets/achievements/icons/roulette_number_9.png",
        "condition": ("flag", "roulette_only_9_win"),
    },
    {
        "id": "roulette_6_7",
        "category": "Roulette",
        "title": "Six Seven",
        "description": "Win a spin with your only number bets placed on 6 and 7.",
        "difficulty": "secret",
        "secret": True,
        "locked_description": "Two neighboring numbers are all you need.",
        "icon": "assets/achievements/icons/roulette_6_7.png",
        "condition": ("flag", "roulette_only_6_7_win"),
    },

    # ==================================================
    # TEXAS HOLD'EM
    # ==================================================
    {
        "id": "first_holdem_win",
        "category": "Texas Hold'em",
        "title": "First Pot",
        "description": "Win your first Texas Hold'em pot.",
        "difficulty": "easy",
        "icon": "assets/achievements/icons/first_holdem_win.png",
        "condition": ("stat_gte", "holdem_hand_wins", 1),
    },
    {
        "id": "holdem_1000_win",
        "category": "Texas Hold'em",
        "title": "Four-Figure Pot",
        "description": "Win at least $1,000 from a single Hold'em pot.",
        "difficulty": "normal",
        "icon": "assets/achievements/icons/holdem_1000_win.png",
        "condition": ("flag", "holdem_1000_win"),
    },
    {
        "id": "holdem_25000_win",
        "category": "Texas Hold'em",
        "title": "Monster Pot",
        "description": "Win at least $25,000 from a single Hold'em pot.",
        "difficulty": "legendary",
        "icon": "assets/achievements/icons/holdem_25000_win.png",
        "condition": ("flag", "holdem_25000_win"),
        "reward": {"type": "background", "id": "bg_holdem_25000"},
    },
    {
        "id": "holdem_5000_total",
        "category": "Texas Hold'em",
        "title": "Table Profit",
        "description": "Accumulate $5,000 in Hold'em pot winnings.",
        "difficulty": "hard",
        "icon": "assets/achievements/icons/holdem_5000_total.png",
        "condition": ("stat_gte", "holdem_total_winnings", 5000),
        "reward": {"type": "background", "id": "bg_holdem_5000_total"},
    },
    {
        "id": "holdem_10_wins",
        "category": "Texas Hold'em",
        "title": "Ten Pots",
        "description": "Win 10 Texas Hold'em hands.",
        "difficulty": "normal",
        "icon": "assets/achievements/icons/holdem_10_wins.png",
        "condition": ("stat_gte", "holdem_hand_wins", 10),
    },
    {
        "id": "holdem_50_wins",
        "category": "Texas Hold'em",
        "title": "Table Regular",
        "description": "Win 50 Texas Hold'em hands.",
        "difficulty": "elite",
        "icon": "assets/achievements/icons/holdem_50_wins.png",
        "condition": ("stat_gte", "holdem_hand_wins", 50),
        "reward": {"type": "felt", "id": "f_holdem_50"},
    },
    {
        "id": "holdem_100_wins",
        "category": "Texas Hold'em",
        "title": "Centurion",
        "description": "Win 100 Texas Hold'em hands.",
        "difficulty": "legendary",
        "icon": "assets/achievements/icons/holdem_100_wins.png",
        "condition": ("stat_gte", "holdem_hand_wins", 100),
    },
    {
        "id": "holdem_straight_flush",
        "category": "Texas Hold'em",
        "title": "Straight Flush",
        "description": "Win a Hold'em showdown with a straight flush.",
        "difficulty": "legendary",
        "icon": "assets/achievements/icons/holdem_straight_flush.png",
        "condition": ("flag", "holdem_straight_flush"),
        "reward": {"type": "title", "id": "title_straight_flush"},
    },
    {
        "id": "holdem_royal_flush",
        "category": "Texas Hold'em",
        "title": "Royal Flush",
        "description": "Win a Hold'em showdown with a royal flush.",
        "difficulty": "legendary",
        "secret": True,
        "locked_description": "Win a poker hand in a royal fashion *wink wink*.",
        "icon": "assets/achievements/icons/holdem_royal_flush.png",
        "condition": ("flag", "holdem_royal_flush"),
        "rewards": [
            {"type": "background", "id": "bg_holdem_royal"},
            {"type": "felt", "id": "f_holdem_royal"},
            {"type": "title", "id": "title_royal_flush"},
        ],
    },

    # ==================================================
    # SCORE-FOUR
    # ==================================================
    {
        "id": "first_score_four_win",
        "category": "Score-Four",
        "title": "Twenty-Four",
        "description": "Win your first Score-Four game.",
        "difficulty": "easy",
        "icon": "assets/achievements/icons/first_score_four_win.png",
        "condition": ("stat_gte", "score_four_wins", 1),
    },
    {
        "id": "score_four_10_comp_wins",
        "category": "Score-Four",
        "title": "Competitive Arithmetic",
        "description": "Win 10 competitive Score-Four matches.",
        "difficulty": "hard",
        "icon": "assets/achievements/icons/score_four_10_comp_wins.png",
        "condition": ("stat_gte", "score_four_comp_wins", 10),
        "reward": {"type": "background", "id": "bg_score_four_10"},
    },
    {
        "id": "score_four_50_wins",
        "category": "Score-Four",
        "title": "Mental Mathlete",
        "description": "Win 50 Score-Four games.",
        "difficulty": "elite",
        "icon": "assets/achievements/icons/score_four_50_wins.png",
        "condition": ("stat_gte", "score_four_wins", 50),
    },
    {
        "id": "score_four_100_wins",
        "category": "Score-Four",
        "title": "One Hundred Twenty-Fours",
        "description": "Win 100 Score-Four games.",
        "difficulty": "legendary",
        "icon": "assets/achievements/icons/score_four_100_wins.png",
        "condition": ("stat_gte", "score_four_wins", 100),
    },
]


DEFINITION_BY_ID = {
    item["id"]: item
    for item in ACHIEVEMENT_DEFINITIONS
}


OPTIONAL_COSMETICS = {
    "background": {
        "bg_blackjack_all_in": {
            "name": "All In",
            "path": "assets/ui/menu_ui/backgrounds/bg_blackjack_all_in.png",
            "order": 1000,
        },
        "bg_roulette_1000": {
            "name": "Wheel of Fortune",
            "path": "assets/ui/menu_ui/backgrounds/bg_roulette_1000.png",
            "order": 1010,
        },
        "bg_holdem_5000_total": {
            "name": "Table Profit",
            "path": "assets/ui/menu_ui/backgrounds/bg_holdem_5000_total.png",
            "order": 1020,
        },
        "bg_holdem_25000": {
            "name": "Monster Pot",
            "path": "assets/ui/menu_ui/backgrounds/bg_holdem_25000.png",
            "order": 1030,
        },
        "bg_holdem_royal": {
            "name": "Royal Flush",
            "path": "assets/ui/menu_ui/backgrounds/bg_holdem_royal.png",
            "order": 1040,
        },
        "bg_score_four_10": {
            "name": "Competitive Arithmetic",
            "path": "assets/ui/menu_ui/backgrounds/bg_score_four_10.png",
            "order": 1050,
        },
    },
    "felt": {
        "f_holdem_50": {
            "name": "Table Regular",
            "path": "assets/ui/menu_ui/felts/f_holdem_50.png",
            "order": 1000,
        },
        "f_holdem_royal": {
            "name": "Royal Flush",
            "path": "assets/ui/menu_ui/felts/f_holdem_royal.png",
            "order": 1010,
        },
    },
    "title": {
        "title_low_roller": {
            "name": "Low Roller",
            "path": "assets/ui/menu_ui/titles/title_low_roller.png",
            "order": 1000,
        },
        "title_straight_flush": {
            "name": "Straight Flush",
            "path": "assets/ui/menu_ui/titles/title_straight_flush.png",
            "order": 1010,
        },
        "title_royal_flush": {
            "name": "Royal Flush",
            "path": "assets/ui/menu_ui/titles/title_royal_flush.png",
            "order": 1020,
        },
    },
}


# New cosmetics are granted retroactively by the existing reward reconciliation.
for definition in ACHIEVEMENT_DEFINITIONS:
    reward = {
        "first_roulette_win": {"type": "felt", "id": "f_wheel_winner"},
        "challenge_no_undo": {"type": "background", "id": "bg_no_going_back"},
        "table_clear": {"type": "title", "id": "title_table_clear"},
    }.get(definition["id"])
    if reward:
        definition.setdefault("rewards", []).append(reward)
OPTIONAL_COSMETICS["felt"]["f_wheel_winner"] = {"name": "Wheel Winner", "path": "assets/ui/menu_ui/felts/f_wheel_winner.png", "order": 990}
OPTIONAL_COSMETICS["background"]["bg_no_going_back"] = {"name": "No Going Back", "path": "assets/ui/menu_ui/backgrounds/bg_no_going_back.png", "order": 990}
OPTIONAL_COSMETICS["title"]["title_table_clear"] = {"name": "Table Clear", "path": "assets/ui/menu_ui/titles/title_table_clear.png", "order": 990}


def make_default_achievement_state():
    return {
        "unlocked": [],
        "stats": {},
    }


def normalize_achievement_state(value):
    result = make_default_achievement_state()

    if not isinstance(value, dict):
        return result

    unlocked = value.get("unlocked", [])
    if isinstance(unlocked, (list, tuple, set)):
        result["unlocked"] = [
            achievement_id
            for achievement_id in unlocked
            if achievement_id in DEFINITION_BY_ID
        ]

    stats = value.get("stats", {})
    if isinstance(stats, dict):
        result["stats"] = deepcopy(stats)

    return result


def _increment(stats, key, amount=1):
    stats[key] = int(stats.get(key, 0) or 0) + int(amount)


def _set_flag(stats, key, value=True):
    if value:
        stats[key] = True


def record_event(state, event_name, **data):
    """Update achievement stats and return newly unlocked definitions."""
    state = normalize_achievement_state(state)
    stats = state["stats"]

    event_name = str(event_name or "")

    if event_name == "solitaire_win":
        _increment(stats, "solitaire_wins")
        moves = int(data.get("moves", 999999) or 999999)
        elapsed = float(data.get("elapsed_seconds", 999999) or 999999)
        if moves < 100:
            _set_flag(stats, "solitaire_under_100_moves")
        if elapsed < 300:
            _set_flag(stats, "solitaire_under_5_minutes")
        challenge_id = data.get("challenge_id")
        if challenge_id in ("draw_3", "no_undo", "no_hints"):
            _set_flag(stats, f"challenge_{challenge_id}")

    elif event_name == "blackjack_round":
        result = str(data.get("result", ""))
        net = int(data.get("net", 0) or 0)
        won = net > 0
        if bool(data.get("natural")):
            _increment(stats, "blackjack_naturals")
        if won:
            _increment(stats, "blackjack_wins")
            if bool(data.get("doubled")):
                _set_flag(stats, "blackjack_double_win")
            if bool(data.get("stood")) and int(data.get("player_total", 99) or 99) < 12:
                _set_flag(stats, "blackjack_low_stand")
            if int(data.get("hit_count", 0) or 0) >= 5:
                _set_flag(stats, "blackjack_five_hits")
            if net >= 1000:
                _set_flag(stats, "blackjack_1000_win")
            if bool(data.get("all_in")):
                _set_flag(stats, "blackjack_all_in_win")
            _increment(stats, "blackjack_total_profit", max(0, net))

    elif event_name == "roulette_round":
        net = int(data.get("net", 0) or 0)
        bets = list(data.get("bets") or [])
        if net > 0:
            _increment(stats, "roulette_wins")
            _increment(stats, "roulette_total_profit", net)
            if net >= 1000:
                _set_flag(stats, "roulette_1000_win")

            number_bets = [
                bet for bet in bets
                if bet.get("type") == "number"
            ]
            other_bets = [
                bet for bet in bets
                if bet.get("type") != "number"
            ]
            number_values = {
                str(bet.get("value"))
                for bet in number_bets
            }
            if not other_bets and len(number_bets) == 1 and number_values == {"9"}:
                _set_flag(stats, "roulette_only_9_win")
            if not other_bets and number_values == {"6", "7"} and len(number_bets) == 2:
                _set_flag(stats, "roulette_only_6_7_win")

    elif event_name == "poker_table_clear":
        _increment(stats, "poker_tables_cleared")

    elif event_name == "holdem_hand_win":
        winnings = max(0, int(data.get("winnings", 0) or 0))
        _increment(stats, "holdem_hand_wins")
        _increment(stats, "holdem_total_winnings", winnings)
        if winnings >= 1000:
            _set_flag(stats, "holdem_1000_win")
        if winnings >= 25000:
            _set_flag(stats, "holdem_25000_win")

        category = data.get("category")
        high = data.get("high")
        if category == 8:
            _set_flag(stats, "holdem_straight_flush")
            if high == 14:
                _set_flag(stats, "holdem_royal_flush")

    elif event_name == "score_four_win":
        _increment(stats, "score_four_wins")
        if data.get("mode") == "competitive":
            _increment(stats, "score_four_comp_wins")

    newly_unlocked = evaluate_unlocks(state)
    return state, newly_unlocked


def _condition_met(definition, stats):
    condition = definition.get("condition")
    if not condition:
        return False

    kind = condition[0]
    if kind == "stat_gte":
        _kind, key, threshold = condition
        try:
            return int(stats.get(key, 0) or 0) >= int(threshold)
        except (TypeError, ValueError):
            return False

    if kind == "flag":
        _kind, key = condition
        return bool(stats.get(key, False))

    return False


def evaluate_unlocks(state):
    unlocked = set(state.get("unlocked", []))
    stats = state.get("stats", {})
    newly_unlocked = []

    for definition in ACHIEVEMENT_DEFINITIONS:
        achievement_id = definition["id"]
        if achievement_id in unlocked:
            continue
        if _condition_met(definition, stats):
            unlocked.add(achievement_id)
            newly_unlocked.append(definition)

    state["unlocked"] = [
        definition["id"]
        for definition in ACHIEVEMENT_DEFINITIONS
        if definition["id"] in unlocked
    ]

    return newly_unlocked


def get_progress_text(definition, state):
    stats = state.get("stats", {}) if isinstance(state, dict) else {}
    condition = definition.get("condition")
    if not condition:
        return ""

    if condition[0] == "stat_gte":
        _, key, threshold = condition
        current = max(0, int(stats.get(key, 0) or 0))
        return f"{min(current, threshold):,}/{threshold:,}"

    return ""


def get_unlock_count(state):
    unlocked = set((state or {}).get("unlocked", []))
    return sum(
        1 for definition in ACHIEVEMENT_DEFINITIONS
        if definition["id"] in unlocked
    )


def get_definition(achievement_id):
    return DEFINITION_BY_ID.get(achievement_id)


def iter_rewards(definition):
    rewards = []
    reward = definition.get("reward")
    if isinstance(reward, dict):
        rewards.append(reward)
    extra = definition.get("rewards")
    if isinstance(extra, list):
        rewards.extend(item for item in extra if isinstance(item, dict))
    return rewards


def register_optional_cosmetics(menu_backgrounds, felts, titles):
    """Register achievement cosmetic rewards only when their PNGs exist.

    This keeps a partially-complete art folder from making startup fail.
    """
    targets = {
        "background": menu_backgrounds,
        "felt": felts,
        "title": titles,
    }

    for reward_type, entries in OPTIONAL_COSMETICS.items():
        target = targets[reward_type]
        for asset_id, metadata in entries.items():
            if os.path.exists(metadata["path"]):
                target.setdefault(asset_id, dict(metadata))


