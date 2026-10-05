"""Public-board evaluation plus the NPC's own hand; no hidden opponent reads."""
import random

from cryptid_creatures import Creature, damage_values, matchup
from npc_personality import get_npc_traits


def _effect_value(battle, seat, effects, target, aggression, caution):
    side = battle.sides[seat]
    if "arena" in effects:
        arena = effects["arena"]
        own = side.active
        enemy = battle.sides[1-seat].active
        styles = arena["styles"]
        own_match = own and ("*" in styles or battle.card(own.card_id)["attack_style"] in styles)
        enemy_match = enemy and ("*" in styles or battle.card(enemy.card_id)["attack_style"] in styles)
        if arena["scope"] == "enemy":
            return 13 if enemy_match else -2
        benefit = (15 if own_match else 0) - (8 if enemy_match and arena["scope"] == "all" else 0)
        # Replaying an unchanged arena is a poor use of a limited card.
        if battle.arena and all(battle.arena.get(k) == v for k, v in arena.items() if k != "duration"):
            benefit -= 12
        return benefit
    creature = battle._target(side, target)
    card = battle.card(creature.card_id)
    healing = min(effects.get("heal_hp", 0), max(0, card["hp"]-creature.hp))
    armor = min(effects.get("heal_ap", 0), max(0, card["ap"]-creature.ap))
    score = healing*(1.0+.7*caution) + armor*.55
    if target > 0:
        score *= .65
    score += min(effects.get("barrier_ap", 0), max(0, card["ap"]+30-creature.ap))*.45
    if effects.get("rearm"):
        score += 8*sum(min(effects["rearm"], battle.catalog.moves[mid]["uses"]-count)
                       for mid, count in creature.uses.items() if count is not None)
    if effects.get("cleanse"):
        score += sum({"sick":18, "spent":12, "stunned":8}.get(c, 0) for c in creature.conditions)
    condition = effects.get("condition")
    if condition and condition not in creature.conditions:
        score += (12+6*aggression if condition == "sharpened" else 14+5*caution)
    if any(k in effects for k in ("guard", "guard_ap", "guard_hp", "reflect")) and not creature.guard:
        score += (11+8*caution) if target == 0 else 6
        score += 7 if effects.get("reflect") else 0
    return score


def _attack_value(battle, seat, creature, move):
    opponent = battle.sides[1-seat].active
    if not opponent:
        return 0
    armor, hp = damage_values(move, creature, opponent, battle.card(creature.card_id),
                              battle.card(opponent.card_id), battle.arena, seat)
    return armor*.65 + hp*1.25 + (50 if hp >= opponent.hp else 0)


def choose_cryptid_action(battle, npc=None, rng=None, seat=1):
    """The caller may also use this for simulated human play during balancing."""
    rng = rng or random
    actions = battle.legal_actions(seat)
    if not actions:
        return None
    traits = get_npc_traits(npc or {"id":"cryptid_practice"})
    t = {k:(v-1)/9 for k,v in traits.items()}
    aggression, caution = t["aggressiveness"], t["caution"]
    side = battle.sides[seat]
    values = []
    for action in actions:
        value = 0.0
        if action.kind == "end":
            value = 2 + side.focus*.55
        elif action.kind == "discard":
            card = battle.card(side.hand[action.index])
            value = (-25 if card["kind"] == "creature" and len(side.docket) < 2 else 0)
            if card["kind"] != "creature":
                value -= _effect_value(battle, seat, card["effects"], 0, aggression, caution)
        elif action.kind == "promote":
            if action.target == 1:
                creature = side.docket[action.index]
            else:
                cid = side.hand[action.index]
                card = battle.card(cid)
                creature = Creature(cid,-1,card["hp"],card["ap"],
                                    {mid:battle.catalog.moves[mid]["uses"] for mid in card["moves"]})
            card = battle.card(creature.card_id)
            value = creature.hp*.2 + creature.ap*.08
            value += max((_attack_value(battle,seat,creature,battle.catalog.moves[m])
                          for m in card["moves"] if battle.catalog.moves[m]["kind"] == "attack"), default=0)*.45
        elif action.kind == "switch":
            old, new = side.active, side.docket[action.index]
            enemy = battle.sides[1-seat].active
            if enemy:
                own_card, new_card = battle.card(old.card_id), battle.card(new.card_id)
                best_old = max((_attack_value(battle,seat,old,battle.catalog.moves[m])
                                for m in own_card["moves"] if battle.catalog.moves[m]["kind"] == "attack"
                                and (old.uses[m] is None or old.uses[m]>0)
                                and battle.catalog.moves[m]["focus"] <= side.focus), default=0)
                best_new = max((_attack_value(battle,seat,new,battle.catalog.moves[m])
                                for m in new_card["moves"] if battle.catalog.moves[m]["kind"] == "attack"
                                and (new.uses[m] is None or new.uses[m]>0)
                                and battle.catalog.moves[m]["focus"] <= side.focus-1), default=0)
                enemy_style = battle.card(enemy.card_id)["attack_style"]
                defense_gain = matchup(enemy_style, own_card["defense_style"])-matchup(enemy_style,new_card["defense_style"])
                value = (best_new-best_old)*.65 + defense_gain*8*caution - 8
                value += 16*t["tenacity"] if old.hp < own_card["hp"]*.35 and new.hp > old.hp else 0
        elif action.kind == "play":
            card = battle.card(side.hand[action.index])
            if card["kind"] == "creature":
                value = (18 if len(side.docket)<2 else 5) + card["hp"]*.02 - 4
            else:
                value = _effect_value(battle,seat,card["effects"],action.target,aggression,caution) - card["focus"]*4
        else:
            move = (battle.catalog.moves["struggle"] if action.kind == "struggle"
                    else battle.catalog.moves[battle.card(side.active.card_id)["moves"][action.index]])
            if move["kind"] == "attack":
                value = _attack_value(battle,seat,side.active,move)*(1+.25*aggression)
                value += move.get("condition_chance",0)*12
                value -= 12 if move.get("self_damage") else 0
                value += 5*t["escalation"] if battle.sides[1-seat].knockouts > side.knockouts else 0
                value += 4*t["bitterness"]*battle.sides[1-seat].knockouts
                value -= 7*t["pessimism"] if value < 15 else 0
            else:
                value = _effect_value(battle,seat,move["effects"],action.target,aggression,caution)
            value -= move["focus"]*(2+3*t["selectivity"])
        value += rng.uniform(-1,1)*(1+9*t["unpredictability"])
        values.append(value)
    return actions[max(range(len(actions)), key=lambda i: values[i])]
