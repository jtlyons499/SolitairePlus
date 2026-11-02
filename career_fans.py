import math

MAX_FANS = 1_000_000

PUBLIC_APPEAL_TRAITS = {
    "camera_shy": ("Camera Shy", 0.72),
    "reserved": ("Reserved", 0.88),
    "steady": ("Steady", 1.00),
    "charming": ("Charming", 1.16),
    "magnetic": ("Magnetic", 1.30),
}


def clamp_fans(value):
    try:
        value = int(round(value))
    except (TypeError, ValueError):
        value = 0
    return max(0, min(MAX_FANS, value))


def normalize_fan_trend(history, limit=24):
    cleaned = []
    if not isinstance(history, (list, tuple)):
        return cleaned
    for entry in history[-max(1, int(limit)):]:
        if isinstance(entry, dict):
            raw = entry.get("change", 0)
            reason = str(entry.get("reason", "") or "")[:80]
            day = entry.get("day")
        else:
            raw, reason, day = entry, "", None
        try:
            change = int(round(raw))
        except (TypeError, ValueError):
            continue
        if not change:
            continue
        row = {"change": change}
        if reason:
            row["reason"] = reason
        if isinstance(day, int):
            row["day"] = day
        cleaned.append(row)
    return cleaned[-limit:]


def record_fan_trend(history, change, reason="", day=None, limit=24):
    rows = normalize_fan_trend(history, limit=limit)
    try:
        change = int(round(change))
    except (TypeError, ValueError):
        return rows
    if not change:
        return rows
    row = {"change": change}
    if reason:
        row["reason"] = str(reason)[:80]
    if isinstance(day, int):
        row["day"] = day
    rows.append(row)
    return rows[-limit:]


def get_player_public_appeal_trait(history, current_fans=0):
    """Derive player appeal from recent fan momentum rather than raw fame.

    Recent changes weigh most.  A huge established fanbase cannot hide a long
    losing trend, while a smaller player on a sustained upswing can become
    Charming/Magnetic quickly.
    """
    rows = normalize_fan_trend(history)
    if not rows:
        return "steady"
    weighted_net = 0.0
    weighted_abs = 0.0
    positive_weight = 0.0
    total_weight = 0.0
    for age, row in enumerate(reversed(rows[-12:])):
        weight = 0.86 ** age
        change = float(row["change"])
        weighted_net += change * weight
        weighted_abs += abs(change) * weight
        total_weight += weight
        if change > 0:
            positive_weight += weight
    direction = weighted_net / max(25.0, weighted_abs)
    consistency = positive_weight / max(0.001, total_weight)
    # Consistency breaks ties: many modest gains are more magnetic than one
    # jackpot followed by losses.
    score = direction * 0.78 + (consistency - 0.5) * 0.44
    if score <= -0.48:
        return "camera_shy"
    if score <= -0.14:
        return "reserved"
    if score < 0.18:
        return "steady"
    if score < 0.52:
        return "charming"
    return "magnetic"


def get_player_public_appeal_display_name(history, current_fans=0):
    return get_public_appeal_display_name(get_player_public_appeal_trait(history, current_fans))


def _stable_value(identity):
    text = str(identity or "npc")
    return sum((index + 1) * ord(char) for index, char in enumerate(text))


def get_npc_public_appeal_trait(npc):
    if isinstance(npc, dict):
        explicit = npc.get("public_appeal")
        if explicit in PUBLIC_APPEAL_TRAITS:
            return explicit
        identity = npc.get("id") or npc.get("name") or "npc"
    else:
        identity = npc or "npc"
    bucket = _stable_value(identity) % 100
    if bucket < 10: return "camera_shy"
    if bucket < 30: return "reserved"
    if bucket < 72: return "steady"
    if bucket < 94: return "charming"
    return "magnetic"


def get_public_appeal_display_name(trait):
    return PUBLIC_APPEAL_TRAITS.get(trait, PUBLIC_APPEAL_TRAITS["steady"])[0]


def get_public_appeal_multiplier(trait):
    return PUBLIC_APPEAL_TRAITS.get(trait, PUBLIC_APPEAL_TRAITS["steady"])[1]


def calculate_npc_fans(rating, trait="steady"):
    try: rating = int(rating)
    except (TypeError, ValueError): rating = 1000
    normalized = max(0.0, min(1.0, (rating - 650) / 2500.0))
    base = 350 + (normalized ** 3) * 920_000
    return clamp_fans(base * get_public_appeal_multiplier(trait))


def ensure_npc_fan_state(state, npc):
    if not isinstance(state, dict): state = {}
    trait = state.get("public_appeal")
    if trait not in PUBLIC_APPEAL_TRAITS:
        trait = get_npc_public_appeal_trait(npc); state["public_appeal"] = trait
    overall = state.get("rating", 1000)
    if isinstance(state.get("ratings"), dict): overall = state["ratings"].get("overall", overall)
    state["fans"] = calculate_npc_fans(overall, trait)
    return state


def fan_gain_from_rating_win(rating_gain, current_rating=1000):
    try:
        rating_gain=max(0,int(rating_gain)); current_rating=max(100,int(current_rating))
    except (TypeError,ValueError): return 0
    if rating_gain<=0:return 0
    fame_scale=max(1.0,(current_rating/650.0)**1.55)
    return max(5,int(round(rating_gain*3.0*fame_scale)))


def fan_gain_from_cash_win(net_win, current_rating=1000):
    try:
        net_win=max(0,int(net_win)); current_rating=max(100,int(current_rating))
    except (TypeError,ValueError): return 0
    if net_win<=0:return 0
    fame_scale=max(0.75,current_rating/1400.0)
    return max(2,int(round(math.sqrt(net_win)*4.5*fame_scale)))


def fan_bonus_for_job(required_rating=0,pay=0):
    try: required_rating=max(0,int(required_rating));pay=max(0,int(pay))
    except (TypeError,ValueError):return 0
    return max(25,int(round(required_rating*0.55+pay*3.0)))


def fan_bonus_for_residence(price=0):
    try: price=max(0,int(price))
    except (TypeError,ValueError):return 0
    if price<=0:return 0
    return max(50,int(round(math.sqrt(price)*95)))


def fan_bonus_for_achievement(difficulty="normal"):
    values={"easy":250,"normal":750,"hard":2500,"elite":8000,"legendary":25000,"secret":12000}
    return values.get(str(difficulty or "normal").lower(),values["normal"])


def fan_change_from_autograph_accuracy(accuracy,current_fans=0,current_rating=1000):
    try:
        accuracy=max(0.0,min(100.0,float(accuracy)));current_fans=max(0,int(current_fans));current_rating=max(100,int(current_rating))
    except (TypeError,ValueError):return 0
    audience=max(85.0,110.0+current_rating*0.10+math.sqrt(current_fans)*1.15)
    if accuracy>=92:multiplier=1.45
    elif accuracy>=82:multiplier=1.00
    elif accuracy>=70:multiplier=.62
    elif accuracy>=58:multiplier=.28
    elif accuracy>=45:multiplier=.08
    elif accuracy>=30:multiplier=-.18
    else:multiplier=-.38
    change=int(round(audience*multiplier))
    if multiplier>0:return max(5,change)
    if multiplier<0:return min(-5,change)
    return 0


def fan_loss_from_bad_result(current_fans=0,net_loss=0,severity=1.0):
    try:
        current_fans=max(0,int(current_fans));net_loss=max(0,int(net_loss));severity=max(.25,float(severity))
    except (TypeError,ValueError):return 0
    if current_fans<=0:return 0
    audience_component=5.0+math.sqrt(current_fans)*.32
    cash_component=math.sqrt(net_loss)*.85 if net_loss>0 else 0.0
    loss=int(round((audience_component+cash_component)*severity))
    maximum=max(10,int(round(current_fans*.035)))
    return max(1,min(current_fans,maximum,loss))
