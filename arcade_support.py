"""Pure helpers for Arcade Night economy and rewards."""
from __future__ import annotations

import copy

ARCADE_MACHINE_COSTS = {
    "king_pong": 2,
    "battle_bosses": 3,
    "ace_invaders": 2,
    "suit_snake": 1,
}

ARCADE_MACHINE_NAMES = {
    "king_pong": "King Pong",
    "battle_bosses": "Battle Bosses",
    "ace_invaders": "Ace Invaders",
    "suit_snake": "Suit Snake",
    "prize_counter": "Prize Counter",
}

ARCADE_COMING_SOON_GAME_IDS = {
    "ace_invaders",
    "suit_snake",
}

ARCADE_TOKEN_PACKAGES = [
    {
        "id": "starter_roll",
        "name": "Starter Roll",
        "cash_cost": 5,
        "tokens": 20,
        "description": "$5 for 20 tokens",
    },
    {
        "id": "double_stack",
        "name": "Double Stack",
        "cash_cost": 10,
        "tokens": 45,
        "description": "$10 for 45 tokens",
    },
    {
        "id": "party_bucket",
        "name": "Party Bucket",
        "cash_cost": 25,
        "tokens": 120,
        "description": "$25 for 120 tokens",
    },
    {
        "id": "weekend_haul",
        "name": "Weekend Haul",
        "cash_cost": 50,
        "tokens": 260,
        "description": "$50 for 260 tokens",
    },
]

ARCADE_PRIZE_CATALOG = [
    {
        "id": "bronze_paddle_cup",
        "name": "Bronze Paddle Cup",
        "kind": "trophy",
        "cost": 120,
        "description": "A starter counter prize celebrating your first big ticket haul.",
    },
    {
        "id": "silver_satellite_trophy",
        "name": "Silver Satellite Trophy",
        "kind": "trophy",
        "cost": 340,
        "description": "A polished mid-tier arcade trophy with a little sci-fi flair.",
    },
    {
        "id": "golden_crown_marquee",
        "name": "Golden Crown Marquee",
        "kind": "trophy",
        "cost": 780,
        "description": "A flashy showpiece for dedicated arcade regulars.",
    },
]

_ARCADE_PRIZES_BY_ID = {
    entry["id"]: entry
    for entry in ARCADE_PRIZE_CATALOG
}


def make_default_arcade_state():
    return {
        "tokens": 0,
        "tickets": 0,
        "trophies": [],
        "stats": {
            "tokens_purchased": 0,
            "tokens_spent": 0,
            "tickets_won": 0,
            "king_pong_wins": 0,
            "king_pong_losses": 0,
            "battle_bosses_wins": 0,
            "battle_bosses_losses": 0,
            "battle_bosses_rivals_eliminated": 0,
            "prizes_redeemed": 0,
        },
    }


_DEF_STATS = make_default_arcade_state()["stats"]


def _as_int(value, fallback=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(fallback)



def normalize_arcade_state(data):
    state = make_default_arcade_state()
    if not isinstance(data, dict):
        return state

    state["tokens"] = max(0, _as_int(data.get("tokens"), 0))
    state["tickets"] = max(0, _as_int(data.get("tickets"), 0))

    trophies = data.get("trophies", [])
    if isinstance(trophies, (list, tuple)):
        seen = set()
        cleaned = []
        for trophy_id in trophies:
            trophy_id = str(trophy_id or "").strip()
            if trophy_id and trophy_id not in seen:
                cleaned.append(trophy_id)
                seen.add(trophy_id)
        state["trophies"] = cleaned

    stats = data.get("stats", {})
    if isinstance(stats, dict):
        merged = dict(_DEF_STATS)
        for key in merged:
            merged[key] = max(0, _as_int(stats.get(key), merged[key]))
        state["stats"] = merged

    return state



def clone_arcade_state(data):
    return normalize_arcade_state(copy.deepcopy(data))



def get_machine_cost(game_id):
    return max(0, _as_int(ARCADE_MACHINE_COSTS.get(game_id), 0))



def spend_tokens(state, amount):
    state = normalize_arcade_state(state)
    amount = max(0, _as_int(amount, 0))
    if amount <= 0:
        return True, state
    if state["tokens"] < amount:
        return False, state
    state["tokens"] -= amount
    state["stats"]["tokens_spent"] += amount
    return True, state



def add_tickets(state, amount):
    state = normalize_arcade_state(state)
    amount = max(0, _as_int(amount, 0))
    state["tickets"] += amount
    state["stats"]["tickets_won"] += amount
    return state



def register_king_pong_result(state, won, tickets):
    state = add_tickets(state, tickets)
    if won:
        state["stats"]["king_pong_wins"] += 1
    else:
        state["stats"]["king_pong_losses"] += 1
    return state



def buy_token_package(state, cash_balance, package_id):
    state = normalize_arcade_state(state)
    cash_balance = max(0, _as_int(cash_balance, 0))
    package = next((entry for entry in ARCADE_TOKEN_PACKAGES if entry["id"] == package_id), None)
    if package is None:
        return False, state, cash_balance, "Unknown token package."
    cash_cost = _as_int(package.get("cash_cost"), 0)
    token_amount = _as_int(package.get("tokens"), 0)
    if cash_balance < cash_cost:
        return False, state, cash_balance, "Not enough cash for that token package."
    state["tokens"] += token_amount
    state["stats"]["tokens_purchased"] += token_amount
    cash_balance -= cash_cost
    return True, state, cash_balance, f"Bought {token_amount} arcade tokens for ${cash_cost}."



def award_king_pong_tickets(player_score, opponent_score):
    player_score = max(0, _as_int(player_score, 0))
    opponent_score = max(0, _as_int(opponent_score, 0))
    won = player_score > opponent_score
    tickets = 35 + player_score * 10
    if won:
        tickets += 85
        margin = player_score - opponent_score
        tickets += max(0, margin) * 6
        if opponent_score == 0:
            tickets += 35
        if margin >= 3:
            tickets += 18
    else:
        tickets += max(0, player_score * 3)
        if player_score >= max(1, opponent_score - 1):
            tickets += 10
    return max(20, int(tickets))



def award_battle_bosses_tickets(rivals_eliminated, won, player_hp=0):
    rivals_eliminated = max(0, min(3, _as_int(rivals_eliminated, 0)))
    player_hp = max(0, min(5, _as_int(player_hp, 0)))
    tickets = 30 + rivals_eliminated * 45
    if won:
        tickets += 115 + player_hp * 8
    return max(20, int(tickets))


def register_battle_bosses_result(state, won, tickets, rivals_eliminated=0):
    state = add_tickets(state, tickets)
    key = "battle_bosses_wins" if won else "battle_bosses_losses"
    state["stats"][key] += 1
    state["stats"]["battle_bosses_rivals_eliminated"] += max(0, _as_int(rivals_eliminated, 0))
    return state


def get_prize(prize_id):
    return _ARCADE_PRIZES_BY_ID.get(str(prize_id or ""))



def can_redeem_prize(state, prize_id):
    state = normalize_arcade_state(state)
    prize = get_prize(prize_id)
    if prize is None:
        return False, "Unknown prize."
    if prize_id in state["trophies"]:
        return False, "You already own that trophy."
    if state["tickets"] < prize["cost"]:
        return False, "Not enough tickets yet."
    return True, ""



def redeem_prize(state, prize_id):
    state = normalize_arcade_state(state)
    allowed, reason = can_redeem_prize(state, prize_id)
    if not allowed:
        return False, state, reason, None
    prize = get_prize(prize_id)
    state["tickets"] -= prize["cost"]
    state["trophies"].append(prize_id)
    state["stats"]["prizes_redeemed"] += 1
    return True, state, f"Redeemed {prize['name']}.", prize
