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

ARCADE_COMING_SOON_GAME_IDS = set()

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
        "id": "machine_mania_pass",
        "name": "Machine Mania Pass",
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
            # Ace Invaders is an endless score-attack cabinet. The older
            # wins/losses keys stay in the save schema for compatibility with
            # profiles created by the original four-wave version.
            "ace_invaders_wins": 0,
            "ace_invaders_losses": 0,
            "ace_invaders_runs": 0,
            "ace_invaders_enemies_destroyed": 0,
            "ace_invaders_waves_cleared": 0,
            "ace_invaders_high_wave": 0,
            "ace_invaders_high_score": 0,
            "suit_snake_runs": 0,
            "suit_snake_cards_collected": 0,
            "suit_snake_decks_completed": 0,
            "suit_snake_longest_chain": 0,
            "suit_snake_high_score": 0,
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



def award_ace_invaders_tickets(score, waves_cleared, won=None, lives=0):
    """Return the base ticket payout for one endless Ace Invaders run.

    ``won`` and ``lives`` remain accepted for save/test compatibility with the
    original finite four-wave version, but endless mode is scored entirely by
    how far the player gets. Difficulty is applied by main.py afterwards.
    """
    score = max(0, _as_int(score, 0))
    waves_cleared = max(0, _as_int(waves_cleared, 0))

    # Score is the main reward signal while wave depth gives a meaningful
    # survival bonus. This grows steadily without producing enormous payouts
    # on long high-score attempts.
    tickets = 18 + (score // 25) * 3 + waves_cleared * 18
    return max(18, int(tickets))


def register_ace_invaders_result(
        state,
        won,
        tickets,
        *,
        score=0,
        enemies_destroyed=0,
        waves_cleared=0
):
    state = add_tickets(state, tickets)
    state["stats"]["ace_invaders_runs"] += 1

    # Preserve the old counters if an older caller still supplies a decisive
    # result. Endless runs use won=None and therefore do not masquerade as a
    # loss simply because every score attack eventually ends.
    if won is True:
        state["stats"]["ace_invaders_wins"] += 1
    elif won is False:
        state["stats"]["ace_invaders_losses"] += 1

    state["stats"]["ace_invaders_enemies_destroyed"] += max(
        0, _as_int(enemies_destroyed, 0)
    )
    state["stats"]["ace_invaders_waves_cleared"] += max(
        0, _as_int(waves_cleared, 0)
    )
    state["stats"]["ace_invaders_high_wave"] = max(
        state["stats"].get("ace_invaders_high_wave", 0),
        max(1, _as_int(waves_cleared, 0) + 1),
    )
    state["stats"]["ace_invaders_high_score"] = max(
        state["stats"]["ace_invaders_high_score"],
        max(0, _as_int(score, 0)),
    )
    return state



def award_suit_snake_tickets(score, cards_collected, decks_completed=0):
    """Return the base ticket payout for one Suit Snake run."""
    score = max(0, _as_int(score, 0))
    cards_collected = max(0, _as_int(cards_collected, 0))
    decks_completed = max(0, _as_int(decks_completed, 0))

    # Collection depth is the main reward signal. Score contributes a smaller
    # milestone bonus so rank/deck completion bonuses still matter.
    tickets = 12 + cards_collected * 4 + (score // 500) * 6 + decks_completed * 65
    return max(12, int(tickets))


def register_suit_snake_result(
        state,
        tickets,
        *,
        score=0,
        cards_collected=0,
        decks_completed=0,
        chain_length=1,
):
    state = add_tickets(state, tickets)
    stats = state["stats"]
    stats["suit_snake_runs"] += 1
    stats["suit_snake_cards_collected"] += max(0, _as_int(cards_collected, 0))
    stats["suit_snake_decks_completed"] += max(0, _as_int(decks_completed, 0))
    stats["suit_snake_longest_chain"] = max(
        stats["suit_snake_longest_chain"],
        max(1, _as_int(chain_length, 1)),
    )
    stats["suit_snake_high_score"] = max(
        stats["suit_snake_high_score"],
        max(0, _as_int(score, 0)),
    )
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
