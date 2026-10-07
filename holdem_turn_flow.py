"""Keep a live betting decision assigned, including a lone caller facing an all-in."""
def repair_betting_turn(game):
    if game.hand_complete or game.current_stage not in ('preflop', 'flop', 'turn', 'river'):
        return
    # actor_needs_action also repairs stale all-in flags on positive stacks.
    candidates = [seat for seat in range(len(game.npcs) + 1) if game.actor_needs_action(seat)]
    if game.is_betting_round_complete():
        game.current_actor = -1
        return
    if game.current_actor not in candidates:
        start = game.get_preflop_first_actor_index() if game.current_stage == 'preflop' else game.get_postflop_first_actor_index()
        game.set_first_actor_from(start)
