"""Result-driven rating transactions shared by player and NPC careers."""
from career_ratings import GAME_RATING_KEYS, apply_rating_change, elo_delta, ensure_npc_career_state, update_npc_rating


def record_result(results, game_key, score, change):
    record = results.setdefault(game_key, {})
    for key in ("played", "wins", "draws", "losses"):
        record.setdefault(key, 0)
    record["played"] += 1
    record["wins" if score > 0.5 else "losses" if score < 0.5 else "draws"] += 1
    record["last_change"] = int(change)


def settle_competitive_result(ratings, results, states, game_key, opponent, score):
    """A head-to-head result changes only that game's two ratings."""
    if game_key not in GAME_RATING_KEYS or not isinstance(opponent, dict):
        return 0
    npc_id = opponent.get("id")
    if npc_id is None:
        return 0
    state = ensure_npc_career_state(states.setdefault(npc_id, {}), opponent)
    states[npc_id] = state
    requested = elo_delta(ratings[game_key], state["ratings"][game_key], score)
    if game_key == "score_four":
        rewards = {"low": 45, "mid": 60, "strong": 50, "elite": 65}
        requested = rewards.get(opponent.get("skill_tier"), 60) if score == 1 else -10 if score == 0 else 0
    actual = apply_rating_change(ratings, game_key, requested)
    npc_actual = update_npc_rating(state, opponent, game_key, -actual)
    record_result(results, game_key, score, actual)
    record_result(state["rating_results"], game_key, 1 - score, npc_actual)
    return actual


def settle_house_result(ratings, results, game_key, net):
    """House games use a modest performance index; wagers cannot boost points."""
    if game_key not in ("blackjack", "roulette", "faro"):
        raise ValueError("Not a rated house game")
    score = 1.0 if net > 0 else 0.0 if net < 0 else 0.5
    unit = 15 if game_key == "blackjack" else 12
    actual = apply_rating_change(ratings, game_key, unit if net > 0 else -5 if net < 0 else 0)
    record_result(results, game_key, score, actual)
    return actual


def record_poker_showdown(game):
    """Snapshot banked stacks only; leaving an unfinished hand can't rate it."""
    hand = int(game.hand_number)
    seen = getattr(game, "rating_seen_hands", set())
    if not game.hand_complete or hand in seen:
        return False
    seen.add(hand)
    game.rating_seen_hands = seen
    game.rating_final_stacks = [int(game.player_stack), *map(int, game.npc_stacks)]
    return True


def settle_poker_session(ratings, results, states, game_key, game):
    """Pairwise Elo from the final completed-hand bankroll standings.

    Each participant began with the same stack. Session scores therefore use
    finishing order, never raw stakes. All participants' ratings are compared
    before any changes. Short sessions have a smaller maximum movement.
    """
    if game_key not in ("texas_holdem", "five_card_draw", "seven_card_stud"):
        raise ValueError("Not a rated poker format")
    if getattr(game, "session_rating_rewarded", False):
        return 0
    game.session_rating_rewarded = True
    hands = len(getattr(game, "rating_seen_hands", ()))
    stacks = getattr(game, "rating_final_stacks", None)
    if not hands or stacks is None:
        return 0
    npcs = list(game.npcs)
    if len(stacks) != len(npcs) + 1 or not npcs:
        return 0
    npc_states = []
    for npc in npcs:
        npc_id = npc.get("id")
        if npc_id is None:
            return 0
        state = ensure_npc_career_state(states.setdefault(npc_id, {}), npc)
        states[npc_id] = state
        npc_states.append(state)
    starting_ratings = [ratings[game_key], *(state["ratings"][game_key] for state in npc_states)]
    count = len(stacks)
    k = min(240.0, 12.0 * hands) / (count - 1)
    deltas, scores = [0] * count, [0.0] * count
    for left in range(count):
        for right in range(left + 1, count):
            score = 1.0 if stacks[left] > stacks[right] else 0.0 if stacks[left] < stacks[right] else 0.5
            delta = elo_delta(starting_ratings[left], starting_ratings[right], score, k=k)
            deltas[left] += delta
            deltas[right] -= delta
            scores[left] += score / (count - 1)
            scores[right] += (1 - score) / (count - 1)
    actual = apply_rating_change(ratings, game_key, deltas[0])
    record_result(results, game_key, scores[0], actual)
    for npc, state, delta, score in zip(npcs, npc_states, deltas[1:], scores[1:]):
        npc_actual = update_npc_rating(state, npc, game_key, delta)
        record_result(state["rating_results"], game_key, score, npc_actual)
    return actual

