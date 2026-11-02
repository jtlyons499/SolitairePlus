"""Player quick-chat and personality-driven Hold'em table reactions.

Creative NPC dialogue intentionally lives in explicit reply tables below. Existing
user-authored lines are preserved; new lines are PLACEHOLDER_* entries so they can
be rewritten without touching the interaction logic.
"""
from __future__ import annotations

import random

from npc_personality import get_npc_traits

BETWEEN_HAND_OPTIONS = (
    ("nice_hand", "Nice hand"),
    ("well_played", "Well played"),
    ("easy_win", "Easy win"),
)

IN_HAND_OPTIONS = (
    ("how_going", "How's it going?"),
    ("crush", "I have a crush on…"),
    ("despise", "I despise…"),
    ("favorite_suits", "Favorite suits?"),
    ("where_from", "Where's everyone from?"),
    ("anything_going", "Anything going on with y'all?"),
    ("bored", "I'm bored"),
    ("great_hand", "I've got a great hand"),
)

QUICK_CHAT_OPTIONS = BETWEEN_HAND_OPTIONS + IN_HAND_OPTIONS
QUICK_CHAT_LABELS = dict(QUICK_CHAT_OPTIONS)
TARGETED_QUICK_CHAT = {"crush", "despise"}
MANIPULATIVE_QUICK_CHAT = {"easy_win", "bored", "great_hand"}
CONVERSATIONAL_ONCE_PER_HAND = {
    "how_going", "crush", "despise", "favorite_suits", "where_from", "anything_going"
}

TRAIT_ORDER = (
    "caution",
    "aggressiveness",
    "unpredictability",
    "escalation",
    "selectivity",
    "tenacity",
    "pessimism",
    "bitterness",
)

# ---------------------------------------------------------------------------
# User-authored existing replies. Keep these intact when changing logic.
# New slots are deliberately plain placeholders for the user to rewrite.
# ---------------------------------------------------------------------------

EXISTING_REPLIES = {
    "nice_hand": {
        "aggressive": (
            "ty, taking this table fr", "Thanks, gotta show my prowess.",
            "anotha one", "all skill but ty ig",
        ),
        "careful": (
            "ty friendo", "much love", "thanks, good vibes on jah",
            "thanksssss", "yip yip",
        ),
        "default": (
            "Thanks.", "Appreciate it.", "The cards are vibing with me.",
            "tony weedle", "danke",
        ),
    },
    "well_played": {
        "aggressive": (
            "Yall too tbh", "run it back wooh", "you aight too.",
            "leggoooo", "ye indeed",
        ),
        "default": (
            "Likewise.", "You too.", "Appreciate it.",
            "Thanksssss", "Merci mon ami bro",
        ),
    },
    "easy_win": {
        "aggressive": (
            "clown behavior", "everyone ignore them", "toxic",
            "im about to mute u", "are u 5 years old???",
        ),
        "careful": (
            "wow im so impressed", "just you wait buddy", "Running your mouth a lot huh?",
            "uh huh", "zzzzzzzzzzzz",
        ),
        "default": (
            "We'll see.", "Bold claim.", "Don't celebrate so soon.",
            "Time will tell", "what comes around is all around Ricky",
        ),
    },
    "bored": {
        "aggressive": (
            "rude but ok, ill mix it up", "Bet some more then dumbo", "goosebumps careful what u wish 4 book",
            "blablabla", "good for u",
        ),
        "careful": (
            "Called patience, deal with it bro.", "then gtfo.", "ok and?",
            "i like to be careful chill", "boo hoo",
        ),
        "default": (
            "wait and see fam", "sorry but that's poker", "u spice things up then",
            "same lol ngl", "yea just let me expire",
        ),
    },
    "great_hand": {
        "skeptical": (
            "hmmm ok", "Good to know that pal.",
            "lol sure", "u R loosr bluff",
        ),
        "careful": (
            "Noted.", "Lima Charlie on that", "five by five",
            "Okey doke...", "We will see I guess.",
        ),
        "default": (
            "eh ok", "We'll find out.", "Let's see it, then.",
            "alright then", "sure sure",
        ),
    },
}

# Saying "Easy win" after losing reads as sarcasm / a joke, not the normal taunt.
EASY_WIN_AFTER_LOSS_REPLIES = (
    "you lost you daft dotard",
    "lol cope",
    "idk if u won tho?",
    "yea looked easy for you",
    "easy yap more like",
)


HOW_GOING_REPLIES = {
    "caution": ("meh", "buh", "eh", "aight"),
    "aggressiveness": ("i am v angry", "i feel but rage", "shush", "dont ask"),
    "unpredictability": ("i feel electric", "good just ripped my bong", "trash day", "im tired"),
    "escalation": ("none of your business", "who cares really", "how YOU doin lol", "idk"),
    "selectivity": ("doin good", "just chillin", "going is going", "it be like it is"),
    "tenacity": ("good, love me some poker", "vibing like a Friday", "tis whatever", "bored and sad"),
    "pessimism": ("going terribly thanks", "u dont rly care about me", "u fake", "im depressed"),
    "bitterness": ("going painfully buddy", "stop talking RIGHT now", "pfff idk", "buzzed and crunchy"),
}

CRUSH_REPLIES = {
    "caution": ("what...", "creep...", "oh...thanks", "i like u as a friend"),
    "aggressiveness": ("i will sue you so quick", "gonna block u", "respect my boundaries", "thats pretty cool"),
    "unpredictability": ("we should go stargazing then", "my parents wouldnt like u", "well how swell", "slap me silly"),
    "escalation": ("i wanna crush u too", "slayyyyy", "rock my world then hehe", "im a 50 year old man pretending to be this person"),
    "selectivity": ("will keep in mind", "neato", "many people do", "i feel the same way about myself"),
    "tenacity": ("ill fight to stay at this table for u", "ooooh im not letting that go", "say more omg", "wanna watch Radiohead vids together?"),
    "pessimism": ("ur lying", "jerk", "stop being sarcastic u fiend", "another lie from whom I would expect"),
    "bitterness": ("stop interrupting my thoughts", "then give me money", "shhhhh", "really dont care bb"),
}

DESPISE_REPLIES = {
    "caution": ("ouch...", "thanks for killing my vibe", "why u so mean", "rude?"),
    "aggressiveness": ("mutual", "blockhead", "dont care what a goblin thinks", "idc stfu"),
    "unpredictability": ("that excites me", "haters gon hate", "lol tilted?", "cry more"),
    "escalation": ("then come fight me", "i will tear u apart", "ur pathetic", "uh huh clown"),
    "selectivity": ("who even r u", "ok?", "...making me sad", "i dont feel happy anymore"),
    "tenacity": ("please stop being mean", "i hate u too", "my tears will drown me", "but I liked you..."),
    "pessimism": ("u were my hero once...", "go away", "im calling a referee", "yap yap yap"),
    "bitterness": ("i despise me 2", "same", "join the list loser", "gonna remember that"),
}

ANYTHING_GOING_REPLIES = {
    "caution": ("nope", "just vibes and cards", "just gambling on basketball", "im eatin three blueberries"),
    "aggressiveness": ("prepping some powders wink wink", "playing poker obviously?", "ehhh not really", "shhh"),
    "unpredictability": ("kybrd brkn sry", "just washed my camero", "playin cs2 on my other monitor", "mostly gaming"),
    "escalation": ("i just punched my neighbor", "nah im on house arrest doin nuthin", "planning my AstroWorld trip", "watching sopranos"),
    "selectivity": ("listening to Coldplay", "eating chicken", "mostly working out these days", "took some shrooms an hour ago"),
    "tenacity": ("playing geoguessr soon", "no, life is lame", "praying in a bit", "reading Dante again"),
    "pessimism": ("chopping onions for later", "eating crayons", "reading some wikipedia", "waiting on friends to party"),
    "bitterness": ("not much fam", "waiting to die", "everything and nothing", "i guess?"),
}

def quick_chat_options_for_game(game):
    """Return only lines that make sense in the game's current situation."""
    if game is None or not getattr(game, "npcs", None):
        return ()
    if getattr(game, "hand_complete", False):
        return BETWEEN_HAND_OPTIONS
    stage = str(getattr(game, "current_stage", "idle") or "idle")
    if stage in ("preflop", "flop", "turn", "river"):
        return IN_HAND_OPTIONS
    return ()


def quick_chat_target_options(game, key):
    if key not in TARGETED_QUICK_CHAT or game is None:
        return ()
    rows = []
    busted = list(getattr(game, "npc_busted", ()) or ())
    for npc_index, npc in enumerate(getattr(game, "npcs", ()) or ()):
        if npc_index < len(busted) and busted[npc_index]:
            continue
        name = _npc_name(game, npc_index)
        rows.append((npc_index, name))
    return tuple(rows)


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
    for old_hand in list(uses_by_hand):
        if old_hand < hand - 2:
            uses_by_hand.pop(old_hand, None)
    return uses_by_hand.setdefault(hand, {})


def quick_chat_availability(game, key, target_index=None):
    """Return (enabled, reason) for a currently visible quick-chat line."""
    visible = dict(quick_chat_options_for_game(game))
    if key not in visible:
        return False, "Not available right now"
    if key in TARGETED_QUICK_CHAT and target_index is not None:
        if target_index not in {index for index, _name in quick_chat_target_options(game, key)}:
            return False, "That player isn't available"

    state = _state(game)
    events = _event_count(game)
    uses = _uses_for_hand(game)
    count = int(uses.get(key, 0))

    # Between-hands lines are naturally constrained to the result window and
    # are each allowed once for that completed hand.
    if getattr(game, "hand_complete", False):
        return (count < 1, "" if count < 1 else "Already said this hand")

    if events - int(state.get("last_event", -999)) < 2:
        return False, "Let the action move first"

    if key in MANIPULATIVE_QUICK_CHAT:
        if count >= 1:
            return False, "Once per hand"
        if events - int(state.get("last_manipulative_event", -999)) < 5:
            return False, "Give the table a moment"
    elif key in CONVERSATIONAL_ONCE_PER_HAND and count >= 1:
        return False, "Once per hand"
    elif count >= 2:
        return False, "Used enough this hand"

    return True, ""


def _unit(traits, name):
    return (max(1, min(10, int(traits.get(name, 5)))) - 1) / 9.0


def _dominant_trait(traits):
    return max(TRAIT_ORDER, key=lambda trait: float(traits.get(trait, 0) or 0))


def _reaction_effect(key, traits, skill_factor):
    """Return the modest temporary AI effect used by the original five lines."""
    a = _unit(traits, "aggressiveness")
    c = _unit(traits, "caution")
    s = _unit(traits, "selectivity")
    e = _unit(traits, "escalation")
    u = _unit(traits, "unpredictability")
    t = _unit(traits, "tenacity")
    p = _unit(traits, "pessimism")
    b = _unit(traits, "bitterness")
    skill = max(0.0, min(1.0, float(skill_factor)))

    aggression = call_delta = bluff_delta = 0.0
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


def _existing_response_for(key, traits, skill_factor, rng):
    a = _unit(traits, "aggressiveness")
    c = _unit(traits, "caution")
    s = _unit(traits, "selectivity")
    e = _unit(traits, "escalation")
    u = _unit(traits, "unpredictability")
    b = _unit(traits, "bitterness")
    skill = max(0.0, min(1.0, float(skill_factor)))

    if key == "nice_hand":
        bucket = "aggressive" if b + a > 1.25 else "careful" if c + s > 1.15 else "default"
    elif key == "well_played":
        bucket = "aggressive" if a + e > 1.25 else "default"
    elif key == "easy_win":
        bucket = "aggressive" if b + a + e > 1.55 else "careful" if s + c > 1.25 else "default"
    elif key == "bored":
        bucket = "aggressive" if a + e > 1.20 else "careful" if c + s > 1.20 else "default"
    else:
        skepticism = 0.40*skill + 0.30*s + 0.18*u
        bucket = "skeptical" if skepticism > 0.55 else "careful" if c > 0.65 else "default"
    return rng.choice(EXISTING_REPLIES[key][bucket])


def _npc_name(game, npc_index):
    getter = getattr(game, "get_table_player_name", None)
    if callable(getter):
        try:
            return str(getter(npc_index + 1))
        except Exception:
            pass
    return str(game.npcs[npc_index].get("name", "Opponent"))


def _eligible_npcs(game, include_folded=True):
    busted = list(getattr(game, "npc_busted", ()) or ())
    folded = list(getattr(game, "npc_folded", ()) or ())
    result = []
    for index, npc in enumerate(getattr(game, "npcs", ()) or ()):
        if index < len(busted) and busted[index]:
            continue
        if not include_folded and index < len(folded) and folded[index]:
            continue
        result.append(index)
    return result


def _winner_npcs(game):
    winners = set(getattr(game, "winner_indexes", ()) or ())
    return [index - 1 for index in sorted(winners) if index > 0 and index - 1 < len(getattr(game, "npcs", ())) ]


def _reply(game, npc_index, message, delay_ms=0):
    return {
        "npc_index": int(npc_index),
        "speaker": _npc_name(game, npc_index),
        "message": str(message),
        "delay_ms": max(0, int(delay_ms)),
    }


def _random_responders(game, rng, minimum=1, maximum=2):
    pool = _eligible_npcs(game)
    if not pool:
        return []
    count = rng.randint(max(1, minimum), min(maximum, len(pool)))
    return rng.sample(pool, count)


def _apply_effect(game, key, npc_index, hand, events, state, next_hand=False):
    npc = game.npcs[npc_index]
    traits = get_npc_traits(npc)
    skill_getter = getattr(game, "get_npc_skill_factor", None)
    skill = skill_getter(npc_index) if callable(skill_getter) else 0.55
    effect = _reaction_effect(key, traits, skill)
    effect_hand = hand + 1 if next_hand else hand
    expires_event = int(effect["duration_events"]) if next_hand else events + int(effect["duration_events"])
    state.setdefault("effects", []).append({
        "npc_index": npc_index,
        "hand": effect_hand,
        "expires_event": expires_event,
        "aggression": effect["aggression"],
        "call_requirement_delta": effect["call_requirement_delta"],
        "bluff_delta": effect["bluff_delta"],
        "source": key,
    })
    return traits, skill, effect


def submit_holdem_quick_chat(game, key, target_index=None, rng=None):
    rng = rng or random
    enabled, reason = quick_chat_availability(game, key, target_index)
    if not enabled:
        return {"accepted": False, "reason": reason, "responses": []}
    if key in TARGETED_QUICK_CHAT and target_index is None:
        return {"accepted": False, "reason": "Choose a player", "needs_target": True, "responses": []}

    state = _state(game)
    events = _event_count(game)
    hand = int(getattr(game, "hand_number", 0))
    uses = _uses_for_hand(game)
    uses[key] = int(uses.get(key, 0)) + 1
    state["last_event"] = events
    if key in MANIPULATIVE_QUICK_CHAT and not getattr(game, "hand_complete", False):
        state["last_manipulative_event"] = events

    responses = []
    player_label = QUICK_CHAT_LABELS[key]

    if key in ("nice_hand", "well_played"):
        winners = _winner_npcs(game)
        if winners:
            npc_index = rng.choice(winners)
            traits, skill, _effect = _apply_effect(game, key, npc_index, hand, events, state, next_hand=True)
            responses.append(_reply(game, npc_index, _existing_response_for(key, traits, skill, rng)))

    elif key == "easy_win":
        player_won = 0 in set(getattr(game, "winner_indexes", ()) or ())
        if not player_won:
            # Sarcastic/joking use after a loss: no normal taunt/tilt modifier.
            pool = _winner_npcs(game) or _eligible_npcs(game)
            if pool:
                npc_index = rng.choice(pool)
                responses.append(_reply(game, npc_index, rng.choice(EASY_WIN_AFTER_LOSS_REPLIES)))
        else:
            candidates = []
            for npc_index in _eligible_npcs(game):
                traits, skill, effect = _apply_effect(game, key, npc_index, hand, events, state, next_hand=True)
                magnitude = abs(effect["aggression"]) + abs(effect["call_requirement_delta"]) + abs(effect["bluff_delta"])
                score = 0.15 + magnitude + 0.08 * _unit(traits, "unpredictability") + rng.random() * 0.08
                candidates.append((score, npc_index, traits, skill))
            candidates.sort(reverse=True)
            count = min(len(candidates), 2 if len(candidates) > 1 and rng.random() < 0.32 else 1)
            for _score, npc_index, traits, skill in candidates[:count]:
                responses.append(_reply(game, npc_index, _existing_response_for(key, traits, skill, rng)))

    elif key in ("bored", "great_hand"):
        candidates = []
        for npc_index in _eligible_npcs(game):
            traits, skill, effect = _apply_effect(game, key, npc_index, hand, events, state)
            magnitude = abs(effect["aggression"]) + abs(effect["call_requirement_delta"]) + abs(effect["bluff_delta"])
            score = 0.15 + magnitude + 0.08 * _unit(traits, "unpredictability") + rng.random() * 0.08
            candidates.append((score, npc_index, traits, skill))
        candidates.sort(reverse=True)
        count = min(len(candidates), 2 if len(candidates) > 1 and rng.random() < 0.32 else 1)
        for _score, npc_index, traits, skill in candidates[:count]:
            responses.append(_reply(game, npc_index, _existing_response_for(key, traits, skill, rng)))

    elif key == "how_going":
        for offset, npc_index in enumerate(_random_responders(game, rng, 1, 2)):
            traits = get_npc_traits(game.npcs[npc_index])
            responses.append(_reply(game, npc_index, rng.choice(HOW_GOING_REPLIES[_dominant_trait(traits)]), offset * 420))

    elif key in TARGETED_QUICK_CHAT:
        npc_index = int(target_index)
        target_name = _npc_name(game, npc_index)
        player_label = ("I have a crush on " if key == "crush" else "I despise ") + target_name
        traits = get_npc_traits(game.npcs[npc_index])
        table = CRUSH_REPLIES if key == "crush" else DESPISE_REPLIES
        responses.append(_reply(game, npc_index, rng.choice(table[_dominant_trait(traits)])))

    elif key == "favorite_suits":
        for offset, npc_index in enumerate(_random_responders(game, rng, 1, 2)):
            suit = str(game.npcs[npc_index].get("favorite_suit") or "Unknown")
            responses.append(_reply(game, npc_index, suit, offset * 400))

    elif key == "where_from":
        responders = _random_responders(game, rng, 1, 3)
        for offset, npc_index in enumerate(responders):
            hometown = str(game.npcs[npc_index].get("hometown") or "Unknown")
            responses.append(_reply(game, npc_index, hometown, offset * 550))

    elif key == "anything_going":
        for offset, npc_index in enumerate(_random_responders(game, rng, 1, 2)):
            traits = get_npc_traits(game.npcs[npc_index])
            responses.append(_reply(game, npc_index, rng.choice(ANYTHING_GOING_REPLIES[_dominant_trait(traits)]), offset * 500))

    state["effects"] = [
        effect for effect in state.get("effects", [])
        if effect.get("hand", hand) >= hand - 1 and effect.get("expires_event", events) >= events
    ][-32:]

    return {
        "accepted": True,
        "reason": "",
        "label": player_label,
        "responses": responses,
    }


def get_npc_quick_chat_context(game, npc_index):
    state = _state(game)
    events = _event_count(game)
    hand = int(getattr(game, "hand_number", 0))
    aggression = call_delta = bluff_delta = 0.0
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
