"""Player quick-chat and personality-driven Hold'em table reactions.

This module intentionally keeps the social layer session-local. It stores state on
TexasHoldemGame instead of profile/NPC records so table banter can influence a few
subsequent decisions without permanently changing an NPC's personality.
"""
from __future__ import annotations

import random

from npc_personality import get_npc_traits

QUICK_CHAT_OPTIONS = (
    ("nice_hand", "Nice hand"),
    ("well_played", "Well played"),
    ("easy_win", "Easy win"),
    ("bored", "I'm bored"),
    ("great_hand", "I've got a great hand"),
)

QUICK_CHAT_LABELS = dict(QUICK_CHAT_OPTIONS)
MANIPULATIVE_QUICK_CHAT = {"easy_win", "bored", "great_hand"}


def _event_count(game):
    getter = getattr(game, "get_hand_history_events", None)
    if callable(getter):
        try:
            return len(getter())
        except Exception:
            pass
    history = getattr(game, "hand_history", None)
    events = getattr(history, "events", ())
    try:
        return len(events)
    except TypeError:
        return 0


def _state(game):
    state = getattr(game, "quick_chat_state", None)
    if not isinstance(state, dict):
        state = {
            "last_event": -999,
            "last_manipulative_event": -999,
            "uses_by_hand": {},
            "effects": [],
        }
        game.quick_chat_state = state
    return state


def reset_holdem_quick_chat(game):
    game.quick_chat_state = {
        "last_event": -999,
        "last_manipulative_event": -999,
        "uses_by_hand": {},
        "effects": [],
    }


def _uses_for_hand(game):
    state = _state(game)
    hand = int(getattr(game, "hand_number", 0))
    uses_by_hand = state.setdefault("uses_by_hand", {})
    # Keep this bounded during very long sessions.
    for old_hand in list(uses_by_hand):
        if old_hand < hand - 2:
            uses_by_hand.pop(old_hand, None)
    return uses_by_hand.setdefault(hand, {})


def quick_chat_availability(game, key):
    """Return (enabled, reason) for a quick-chat line."""
    if key not in QUICK_CHAT_LABELS:
        return False, "Unknown line"
    if game is None or not getattr(game, "npcs", None):
        return False, "No table"
    if getattr(game, "current_stage", "idle") in ("idle", "ready", "busted"):
        return False, "Deal a hand first"

    state = _state(game)
    events = _event_count(game)
    uses = _uses_for_hand(game)

    # Require at least one actual poker event between table comments. This is
    # effectively "let action move past somebody before talking again."
    if events - int(state.get("last_event", -999)) < 2:
        return False, "Let the action move first"

    count = int(uses.get(key, 0))
    if key in MANIPULATIVE_QUICK_CHAT:
        if count >= 1:
            return False, "Once per hand"
        if events - int(state.get("last_manipulative_event", -999)) < 5:
            return False, "Give the table a moment"
    elif count >= 2:
        return False, "Used enough this hand"

    return True, ""


def _unit(traits, name):
    return (max(1, min(10, int(traits.get(name, 5)))) - 1) / 9.0


def _reaction_effect(key, traits, skill_factor):
    """Return temporary AI deltas for one NPC.

    aggression feeds bet/raise willingness. call_requirement_delta is added to
    the strength required to continue versus a wager, so negative means more
    skeptical/sticky and positive means the NPC gives the player's claim more
    credit. Effects are deliberately modest and never replace hand strength.
    """
    a = _unit(traits, "aggressiveness")
    c = _unit(traits, "caution")
    s = _unit(traits, "selectivity")
    e = _unit(traits, "escalation")
    u = _unit(traits, "unpredictability")
    t = _unit(traits, "tenacity")
    p = _unit(traits, "pessimism")
    b = _unit(traits, "bitterness")
    skill = max(0.0, min(1.0, float(skill_factor)))

    aggression = 0.0
    call_delta = 0.0
    bluff_delta = 0.0
    duration = 4

    if key == "nice_hand":
        aggression = -0.025 * (0.35 + c + s) + 0.010 * b
        duration = 3

    elif key == "well_played":
        aggression = -0.018 * (0.45 + c) + 0.008 * u
        duration = 3

    elif key == "easy_win":
        tilt = max(0.0, 0.15 + 0.55*b + 0.35*a + 0.25*e - 0.25*c)
        aggression = min(0.16, 0.075 * tilt + 0.035 * a)
        call_delta = -min(0.055, 0.030 * (b + t + a))
        bluff_delta = min(0.035, 0.020 * (a + u))
        duration = 7

    elif key == "bored":
        bait = max(0.0, 0.20 + 0.55*a + 0.60*e + 0.25*u - 0.35*c - 0.15*s)
        aggression = min(0.18, 0.085 * bait)
        bluff_delta = min(0.045, 0.026 * (a + e + u))
        duration = 6

    elif key == "great_hand":
        # Skilled/selective/unpredictable players are more likely to treat the
        # announcement as information to interrogate rather than gospel.
        skepticism = max(0.0, min(1.0, 0.34*skill + 0.30*s + 0.18*u + 0.18*t))
        belief = max(0.0, min(1.0, 0.42*c + 0.34*p + 0.20*(1.0-skill)))
        call_delta = max(-0.075, min(0.075, 0.080*(belief - skepticism)))
        aggression = max(-0.04, min(0.08, 0.055*(skepticism + e + a - c - 0.7)))
        duration = 6

    return {
        "aggression": aggression,
        "call_requirement_delta": call_delta,
        "bluff_delta": bluff_delta,
        "duration_events": duration,
    }


def _response_for(key, traits, skill_factor, rng):
    a = _unit(traits, "aggressiveness")
    c = _unit(traits, "caution")
    s = _unit(traits, "selectivity")
    e = _unit(traits, "escalation")
    u = _unit(traits, "unpredictability")
    b = _unit(traits, "bitterness")
    skill = max(0.0, min(1.0, float(skill_factor)))

    if key == "nice_hand":
        if b + a > 1.25:
            choices = ("ty, taking this table fr", "Thanks, gotta show my prowess.")
        elif c + s > 1.15:
            choices = ("ty friendo", "much love", "thanks, good vibes on jah")
        else:
            choices = ("Thanks.", "Appreciate it.", "The cards are vibing with me.")

    elif key == "well_played":
        if a + e > 1.25:
            choices = ("Yall too tbh", "run it back wooh", "you aight too.")
        else:
            choices = ("Likewise.", "You too.", "Appreciate it.")

    elif key == "easy_win":
        if b + a + e > 1.55:
            choices = ("clown behavior", "everyone ignore them", "toxic")
        elif s + c > 1.25:
            choices = ("wow im so impressed", "just you wait buddy", "Running your mouth a lot huh?")
        else:
            choices = ("We'll see.", "Bold claim.", "Don't celebrate so soon.")

    elif key == "bored":
        if a + e > 1.20:
            choices = ("rude but ok, ill mix it up", "Bet some more then dumbo", "goosebumps careful what u wish 4 book")
        elif c + s > 1.20:
            choices = ("Called patience, deal with it bro.", "then gtfo.", "ok and?")
        else:
            choices = ("wait and see fam", "sorry but that's poker", "u spice things up then")

    else:  # great_hand
        skepticism = 0.40*skill + 0.30*s + 0.18*u
        if skepticism > 0.55:
            choices = ("hmmm ok", "Good to know that pal.")
        elif c > 0.65:
            choices = ("Noted.", "Lima Charlie on that", "five by five")
        else:
            choices = ("eh ok", "We'll find out.", "Let's see it, then.")

    return rng.choice(choices)


def submit_holdem_quick_chat(game, key, rng=None):
    rng = rng or random
    enabled, reason = quick_chat_availability(game, key)
    if not enabled:
        return {"accepted": False, "reason": reason, "responses": []}

    state = _state(game)
    events = _event_count(game)
    hand = int(getattr(game, "hand_number", 0))
    uses = _uses_for_hand(game)
    uses[key] = int(uses.get(key, 0)) + 1
    state["last_event"] = events
    if key in MANIPULATIVE_QUICK_CHAT:
        state["last_manipulative_event"] = events

    candidates = []
    for npc_index, npc in enumerate(getattr(game, "npcs", ())):
        if npc_index < len(getattr(game, "npc_busted", ()) or ()) and game.npc_busted[npc_index]:
            continue
        if npc_index < len(getattr(game, "npc_folded", ()) or ()) and game.npc_folded[npc_index] and not getattr(game, "hand_complete", False):
            # Folded players can still talk occasionally, but prioritize live seats.
            live_weight = 0.45
        else:
            live_weight = 1.0

        traits = get_npc_traits(npc)
        skill_getter = getattr(game, "get_npc_skill_factor", None)
        skill = skill_getter(npc_index) if callable(skill_getter) else 0.55
        effect = _reaction_effect(key, traits, skill)

        magnitude = (
            abs(effect["aggression"])
            + abs(effect["call_requirement_delta"])
            + abs(effect["bluff_delta"])
        )
        personality_noise = 0.08 * _unit(traits, "unpredictability")
        score = live_weight * (0.15 + magnitude + personality_noise + rng.random()*0.08)
        candidates.append((score, npc_index, traits, skill, effect))

        state.setdefault("effects", []).append({
            "npc_index": npc_index,
            "hand": hand,
            "expires_event": events + int(effect["duration_events"]),
            "aggression": effect["aggression"],
            "call_requirement_delta": effect["call_requirement_delta"],
            "bluff_delta": effect["bluff_delta"],
            "source": key,
        })

    candidates.sort(reverse=True, key=lambda item: item[0])
    response_count = 0 if not candidates else 1
    if len(candidates) > 1 and rng.random() < (0.32 if key in MANIPULATIVE_QUICK_CHAT else 0.20):
        response_count = 2

    responses = []
    for _score, npc_index, traits, skill, _effect in candidates[:response_count]:
        name_getter = getattr(game, "get_table_player_name", None)
        name = name_getter(npc_index + 1) if callable(name_getter) else str(game.npcs[npc_index].get("name", "Opponent"))
        responses.append((name, _response_for(key, traits, skill, rng)))

    # Bound old effects.
    state["effects"] = [
        effect for effect in state.get("effects", [])
        if effect.get("hand", hand) >= hand - 1 and effect.get("expires_event", events) >= events
    ][-32:]

    return {
        "accepted": True,
        "reason": "",
        "label": QUICK_CHAT_LABELS[key],
        "responses": responses,
    }


def get_npc_quick_chat_context(game, npc_index):
    state = _state(game)
    events = _event_count(game)
    hand = int(getattr(game, "hand_number", 0))

    aggression = 0.0
    call_delta = 0.0
    bluff_delta = 0.0
    kept = []

    for effect in state.get("effects", []):
        if int(effect.get("hand", -1)) != hand:
            continue
        if int(effect.get("expires_event", -1)) < events:
            continue
        kept.append(effect)
        if int(effect.get("npc_index", -1)) != int(npc_index):
            continue
        aggression += float(effect.get("aggression", 0.0))
        call_delta += float(effect.get("call_requirement_delta", 0.0))
        bluff_delta += float(effect.get("bluff_delta", 0.0))

    state["effects"] = kept
    return {
        "quick_chat_aggression": max(-0.12, min(0.22, aggression)),
        "quick_chat_call_requirement_delta": max(-0.10, min(0.10, call_delta)),
        "quick_chat_bluff_delta": max(-0.06, min(0.08, bluff_delta)),
    }
