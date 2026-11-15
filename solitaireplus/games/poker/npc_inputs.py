"""The NPC decision inputs every poker variant shares (B86 group 5).

The maintainer asked that NPC behaviour be consistent between all variants,
including holding grudges and behaving differently based on the cash on hand.
Each engine still supplies its own variant facts (stage, hand strength, bet
sizes, can_raise ...); everything else an NPC decides from comes from here:

* cash on hand: the wealth ratio and the wealth pressure (none up to 1.15x the
  buy-in, full at 2.5x), scaled by the variant, and the soft bet cap formula;
* personality traits and the rating-based skill factor;
* grudges (npc.personality.PokerGrudgeMemory) against the last full bettor;
* public table reads, the human's tendencies and profile-owned rival learning;
* the session reset of all that memory.

Seat 0 is the human, seat i is npcs[i-1], as in the table rules in core.py.
"""
from solitaireplus.games.poker.ai import get_poker_skill_factor
from solitaireplus.games.poker.quick_chat import reset_holdem_quick_chat
from solitaireplus.npc.personality import get_npc_traits, npc_identity

# Hold'em's river entries of its stage cap tables (fraction of the buy-in, wealth
# boost): the cap of a variant with a single, final betting round.
FINAL_ROUND_CAP = (1.00, 0.50)


def wealth_pressure(stack, starting_stack):
    """0..1 pressure from a stack that has grown beyond the buy-in.

    A small run-good bump should not rewrite a personality, so the effect begins
    only above 1.15x the starting stack and reaches full strength at 2.5x.
    """
    ratio = max(0, int(stack or 0)) / max(1, int(starting_stack or 0))
    if ratio <= 1.15:
        return 0.0
    return max(0.0, min(1.0, (ratio - 1.15) / 1.35))


def soft_bet_cap(starting_stack, fraction, wealth, wealth_boost, minimum_bet, maximum_total):
    """The NPC's soft (AI, not rules) cap on its total wager this round.

    fraction of the buy-in, raised by wealth * wealth_boost for a rich stack; at
    least minimum_bet and never more than maximum_total (round bet + stack).
    """
    scaled = fraction * (1.0 + wealth * wealth_boost)
    return min(maximum_total, max(minimum_bet, int(max(1, starting_stack) * scaled)))


def table_identities(npcs):
    """{seat: identity}: seat 0 is "player", seat i the identity of npcs[i-1]."""
    identities = {0: "player"}
    identities.update({seat: npc_identity(npc, seat) for seat, npc in enumerate(npcs, 1)})
    return identities


def opponent_rows(seat, in_hand_seats, names, identities, stacks, round_bets):
    """Public rows for every other seat still in the hand.

    names, identities, stacks and round_bets are indexed by seat (lists or dicts).
    """
    return [
        {"seat": other, "id": identities[other], "name": names[other],
         "stack": stacks[other], "round_bet": round_bets[other]}
        for other in in_hand_seats if other != seat
    ]


def npc_decision_inputs(*, npc, seat, rating_game_key, stack, starting_stack, hand_number,
                        opponents, last_raiser, grudge_memory, table_reads,
                        player_model=None, player_active=True, wealth_scale=1.0):
    """The shared part of an NPC's decision context.

    opponents: opponent_rows for the NPC. last_raiser: the seat of the last full
    bet or raise this round (None if nobody), the only seat a grudge presses.
    wealth_scale: the variant's weighting of the wealth pressure.
    """
    identity = npc_identity(npc, seat)
    pressure = wealth_pressure(stack, starting_stack) * wealth_scale
    inputs = {
        "personality_traits": get_npc_traits(npc),
        "skill_factor": get_poker_skill_factor(npc, rating_game_key),
        "npc_identity": identity,
        "hand_number": hand_number,
        "starting_stack": starting_stack,
        "wealth_ratio": stack / max(1, starting_stack),
        "wealth_pressure": max(0.0, min(1.0, pressure)),
        "wealth_variant_scale": wealth_scale,
        "opponent_reads": [table_reads.snapshot(row["seat"], observer=identity) for row in opponents],
        "public_opponents": [{"seat": row["seat"], "stack": row["stack"], "round_bet": row["round_bet"]}
                             for row in opponents],
        "player_tendencies": player_model.snapshot() if player_model is not None else {},
        "player_active": player_active,
    }
    inputs.update(grudge_memory.context(npc, seat, opponents, last_raiser, hand_number))
    return inputs


def grudge_seats(npcs, contributions):
    """The seats argument of PokerGrudgeMemory.record_showdown for this table."""
    identities = table_identities(npcs)
    return {
        seat: {"id": identities[seat],
               "bitterness": None if seat == 0 else get_npc_traits(npcs[seat - 1])["bitterness"],
               "contribution": contributions[seat]}
        for seat in range(min(len(contributions), len(npcs) + 1))
    }


def reset_session_memory(game, rating_game_key):
    """Forget the last session: grudges, quick chat, the human's tendencies and the
    table reads, then bind the reads to the rival-learning store (career only)."""
    game.personality_memory.clear()
    reset_holdem_quick_chat(game)
    game._quick_chat_event_counter = 0
    game._quick_chat_event_signature = None
    game.player_model.reset()
    game.table_reads.clear()
    game.table_reads.bind_learning(getattr(game, "learning_store", None), rating_game_key,
                                   table_identities(game.npcs))


def _observing_identities(game):
    """NPCs still at the table (the engine's seat_at_table()).

    One rule at every table: an NPC knocked out before this hand stops reading;
    an NPC all-in with 0 chips keeps reading the hand it is still playing.
    """
    at_table = game.seat_at_table()
    return {npc_identity(npc, seat) for seat, npc in enumerate(game.npcs, 1)
            if seat < len(at_table) and at_table[seat]}


def observe_public_action(game, event, seat, *, stage, amount=0, round_total=0,
                          facing_amount=None, hand_name=None, weak=None, draw_count=None):
    """Let every NPC still at the table read one public action or showdown reveal.

    Call it after the action's chips are in the pot. round_total: the seat's
    chips in this betting round; facing_amount: what it had to call.
    """
    reads = game.table_reads
    if reads.learning:
        reads.learning.active_observers = _observing_identities(game)
    reads.observe(
        event, seat, hand_number=game.hand_number, stage=stage, amount=amount,
        round_total=round_total, pot=game.pot, draw_count=draw_count,
        hand_name=hand_name, facing_amount=facing_amount, weak=weak,
    )
