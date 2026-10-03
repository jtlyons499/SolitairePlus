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

    # Weighted toward ordinary/steady personalities, with rare extremes.
    bucket = _stable_value(identity) % 100
    if bucket < 10:
        return "camera_shy"
    if bucket < 30:
        return "reserved"
    if bucket < 72:
        return "steady"
    if bucket < 94:
        return "charming"
    return "magnetic"


def get_public_appeal_display_name(trait):
    return PUBLIC_APPEAL_TRAITS.get(trait, PUBLIC_APPEAL_TRAITS["steady"])[0]


def get_public_appeal_multiplier(trait):
    return PUBLIC_APPEAL_TRAITS.get(trait, PUBLIC_APPEAL_TRAITS["steady"])[1]


def calculate_npc_fans(rating, trait="steady"):
    """Translate competitive strength into a broad fanbase, then apply appeal.

    The cubic curve keeps ordinary competitors modest while allowing the truly
    elite to become celebrity-level figures. The cap matches the player's cap.
    """
    try:
        rating = int(rating)
    except (TypeError, ValueError):
        rating = 1000

    normalized = max(0.0, min(1.0, (rating - 650) / 2500.0))
    base = 350 + (normalized ** 3) * 920_000
    return clamp_fans(base * get_public_appeal_multiplier(trait))


def ensure_npc_fan_state(state, npc):
    if not isinstance(state, dict):
        state = {}

    trait = state.get("public_appeal")
    if trait not in PUBLIC_APPEAL_TRAITS:
        trait = get_npc_public_appeal_trait(npc)
        state["public_appeal"] = trait

    overall = state.get("rating", 1000)
    if isinstance(state.get("ratings"), dict):
        overall = state["ratings"].get("overall", overall)

    # Recalculate from rating so NPC popularity naturally follows their career.
    state["fans"] = calculate_npc_fans(overall, trait)
    return state


def fan_gain_from_rating_win(rating_gain, current_rating=1000):
    try:
        rating_gain = max(0, int(rating_gain))
        current_rating = max(100, int(current_rating))
    except (TypeError, ValueError):
        return 0

    if rating_gain <= 0:
        return 0

    fame_scale = max(1.0, (current_rating / 650.0) ** 1.55)
    return max(5, int(round(rating_gain * 3.0 * fame_scale)))


def fan_gain_from_cash_win(net_win, current_rating=1000):
    try:
        net_win = max(0, int(net_win))
        current_rating = max(100, int(current_rating))
    except (TypeError, ValueError):
        return 0

    if net_win <= 0:
        return 0

    # Casino wins create attention, but much more slowly than competitive wins.
    fame_scale = max(0.75, current_rating / 1400.0)
    return max(2, int(round(math.sqrt(net_win) * 4.5 * fame_scale)))


def fan_bonus_for_job(required_rating=0, pay=0):
    try:
        required_rating = max(0, int(required_rating))
        pay = max(0, int(pay))
    except (TypeError, ValueError):
        return 0
    return max(25, int(round(required_rating * 0.55 + pay * 3.0)))


def fan_bonus_for_residence(price=0):
    try:
        price = max(0, int(price))
    except (TypeError, ValueError):
        return 0
    if price <= 0:
        return 0
    return max(50, int(round(math.sqrt(price) * 95)))


def fan_bonus_for_achievement(difficulty="normal"):
    values = {
        "easy": 250,
        "normal": 750,
        "hard": 2_500,
        "elite": 8_000,
        "legendary": 25_000,
        "secret": 12_000,
    }
    return values.get(str(difficulty or "normal").lower(), values["normal"])


def fan_change_from_autograph_accuracy(accuracy, current_fans=0, current_rating=1000):
    """Translate autograph tracing accuracy into a signed fan change.

    Better-known players have more people waiting in line, so both gains and
    embarrassments scale gently with existing fame and rating. The curve stays
    intentionally modest so the event matters without becoming a fan farm.
    """
    try:
        accuracy = max(0.0, min(100.0, float(accuracy)))
        current_fans = max(0, int(current_fans))
        current_rating = max(100, int(current_rating))
    except (TypeError, ValueError):
        return 0

    audience = max(
        85.0,
        110.0
        + current_rating * 0.10
        + math.sqrt(current_fans) * 1.15,
    )

    if accuracy >= 92:
        multiplier = 1.45
    elif accuracy >= 82:
        multiplier = 1.00
    elif accuracy >= 70:
        multiplier = 0.62
    elif accuracy >= 58:
        multiplier = 0.28
    elif accuracy >= 45:
        multiplier = 0.08
    elif accuracy >= 30:
        multiplier = -0.18
    else:
        multiplier = -0.38

    change = int(round(audience * multiplier))
    if multiplier > 0:
        return max(5, change)
    if multiplier < 0:
        return min(-5, change)
    return 0
