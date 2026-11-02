"""Result-driven rating transactions shared by player and NPC careers."""
import math

from career_ratings import (
    GAME_RATING_KEYS,
    apply_rating_change,
    elo_delta,
    ensure_npc_career_state,
    update_npc_rating,
)


POKER_RATING_KEYS = (
    "texas_holdem",
    "five_card_draw",
    "seven_card_stud",
    "five_o_poker",
)


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


def _poker_npcs(game):
    npcs = getattr(game, "npcs", None)
    if isinstance(npcs, (list, tuple)):
        return list(npcs)
    npc = getattr(game, "npc", None)
    if isinstance(npc, dict):
        return [npc]
    return []


def _poker_stacks(game):
    npc_stacks = getattr(game, "npc_stacks", None)
    if isinstance(npc_stacks, (list, tuple)):
        return [int(game.player_stack), *map(int, npc_stacks)]
    if hasattr(game, "npc_stack"):
        return [int(game.player_stack), int(game.npc_stack)]
    return None


def record_poker_showdown(game):
    """Snapshot banked stacks only; leaving an unfinished hand can't rate it."""
    hand = int(getattr(game, "hand_number", 0) or 0)
    seen = getattr(game, "rating_seen_hands", set())
    if not getattr(game, "hand_complete", False) or hand <= 0 or hand in seen:
        return False
    stacks = _poker_stacks(game)
    if stacks is None:
        return False
    seen.add(hand)
    game.rating_seen_hands = seen
    game.rating_final_stacks = stacks
    return True


def _poker_standings_deltas(starting_ratings, stacks, hands):
    """Return modest Elo-style table-position deltas and pairwise scores.

    Hand count increases confidence slowly and is capped.  Unlike the previous
    model, a long session cannot make finishing position alone create a
    triple-digit rating swing.
    """
    count = len(stacks)
    session_k = min(48.0, 10.0 + 6.0 * math.sqrt(max(1, int(hands))))
    pair_k = session_k / max(1, count - 1)
    deltas = [0.0] * count
    scores = [0.0] * count

    for left in range(count):
        for right in range(left + 1, count):
            score = 1.0 if stacks[left] > stacks[right] else 0.0 if stacks[left] < stacks[right] else 0.5
            delta = elo_delta(starting_ratings[left], starting_ratings[right], score, k=pair_k)
            deltas[left] += delta
            deltas[right] -= delta
            scores[left] += score / (count - 1)
            scores[right] += (1 - score) / (count - 1)

    return deltas, scores


def _player_poker_rating_request(raw_standings_delta, final_stack, starting_stack):
    """Blend bankroll ROI with a deliberately small table-position signal.

    Poker Career rating is primarily about what the player actually did with
    their buy-in.  Final table position still matters, especially when the
    field is strong, but it should never turn a responsible cash-out into a
    giant rating loss.

    Tuning goals:
    - exact break-even is constrained to roughly +/-3 points;
    - small losses stay small (about -4 at -5% and -8 at -10%);
    - a profitable completed session never produces a negative rating change;
    - even a complete bust is capped at about -50 points;
    - table standings are a secondary modifier, not the main result.
    """
    starting_stack = max(1, int(starting_stack))
    roi = (float(final_stack) - starting_stack) / starting_stack
    bounded_roi = max(-1.0, min(1.0, roi))

    # ROI is the dominant signal.  The tanh curve keeps very large wins/losses
    # from exploding rating movement while remaining sensitive near break-even.
    financial_delta = 48.0 * math.tanh(1.35 * bounded_roi)
    blended = financial_delta + 0.22 * float(raw_standings_delta)

    magnitude = min(1.0, abs(roi))
    movement_cap = 3.0 + 47.0 * (magnitude ** 0.8)
    requested = max(-movement_cap, min(movement_cap, blended))

    # Cashing out ahead is always at least a small positive result.  A session
    # that returns exactly the starting stack can only move a few points either
    # way, regardless of hand count or opponent ratings.
    if roi > 0:
        requested = max(1.0, requested)
    elif roi == 0:
        requested = max(-3.0, min(3.0, requested))

    return requested


def settle_poker_session(ratings, results, states, game_key, game):
    """Rate a completed poker cash-out using banked stacks and session ROI.

    Final completed-hand standings still carry skill information, but bankroll
    profit/loss relative to the equal starting stack is the primary signal.
    The player's ROI guardrails prevent long, responsible sessions from being
    punished simply because rivals happened to finish with larger stacks.

    NPCs keep the pairwise table-order relationships from the Elo calculation.
    Their deltas are shifted together so the table remains approximately
    zero-sum relative to the player's *actual displayed* rating change.
    """
    if game_key not in POKER_RATING_KEYS:
        raise ValueError("Not a rated poker format")
    if getattr(game, "session_rating_rewarded", False):
        return 0

    hands = len(getattr(game, "rating_seen_hands", ()))
    stacks = getattr(game, "rating_final_stacks", None)
    npcs = _poker_npcs(game)
    try:
        starting_stack = int(getattr(game, "starting_stack", 0) or 0)
    except (TypeError, ValueError):
        starting_stack = 0

    if not hands or stacks is None or starting_stack <= 0:
        return 0
    if len(stacks) != len(npcs) + 1 or not npcs:
        return 0

    npc_states = []
    for npc in npcs:
        npc_id = npc.get("id") if isinstance(npc, dict) else None
        if npc_id is None:
            return 0
        state = ensure_npc_career_state(states.setdefault(npc_id, {}), npc)
        states[npc_id] = state
        npc_states.append(state)

    game.session_rating_rewarded = True

    starting_ratings = [
        ratings[game_key],
        *(state["ratings"][game_key] for state in npc_states),
    ]
    raw_deltas, scores = _poker_standings_deltas(starting_ratings, stacks, hands)
    requested = _player_poker_rating_request(raw_deltas[0], stacks[0], starting_stack)

    actual = apply_rating_change(ratings, game_key, requested)

    # Career W/L bookkeeping follows the session's bankroll result.  A player
    # who cashes out ahead should not be recorded as having lost the session
    # merely because one or more NPCs ended with an even larger stack.
    player_net = int(stacks[0]) - starting_stack
    player_score = 1.0 if player_net > 0 else 0.0 if player_net < 0 else 0.5
    record_result(results, game_key, player_score, actual)

    # Preserve NPC ordering/skill signal from the pairwise model while
    # compensating for the player's ROI guardrail.  This avoids gifting every
    # rival a huge rating bump when a break-even player is protected from what
    # used to be a very large standings-only loss.
    raw_npc_total = sum(raw_deltas[1:])
    target_npc_total = -float(actual)
    npc_offset = (target_npc_total - raw_npc_total) / len(npc_states)

    for npc, state, raw_delta, score in zip(npcs, npc_states, raw_deltas[1:], scores[1:]):
        npc_actual = update_npc_rating(state, npc, game_key, raw_delta + npc_offset)
        record_result(state["rating_results"], game_key, score, npc_actual)

    # Transient values are useful to cash-out/recap code and do not alter save
    # schemas.  UI-facing changes use the actual rounded reward, not the raw
    # requested amount.
    game.session_rating_change = actual
    game.session_rating_net = player_net
    game.session_rating_roi = game.session_rating_net / max(1, starting_stack)

    return actual
