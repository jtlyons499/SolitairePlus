"""Career event nights: activity kinds, the games of each night, results and session totals (moved out of legacy.py)."""
from solitaireplus.career.session_summary import night_cash_total
from solitaireplus.career.session_summary import night_game_net
from solitaireplus.app import state
from solitaireplus.app.lazy import lazy
legacy = lazy("solitaireplus.legacy")


# ==================================================
# CAREER CALENDAR # CAREER HELPER FUNCTIONS
# ==================================================

CAREER_ACTIVITY_ROUND = "round"
CAREER_ACTIVITY_WORK = "work"
CAREER_ACTIVITY_CHALLENGE = "challenge"
CAREER_ACTIVITY_EVENT = "event"

# ==================================================
# CAREER CARD EVENT TYPES
# ==================================================

CAREER_ACTIVITY_CASUAL_CARDS = (
    "casual_cards"
)

CAREER_ACTIVITY_POKER_NIGHT = (
    "poker_night"
)

CAREER_ACTIVITY_CASINO_NIGHT = (
    "casino_night"
)

CAREER_ACTIVITY_NICHE_NIGHT = (
    "niche_night"
)

CAREER_ACTIVITY_ARCADE_NIGHT = (
    "arcade_night"
)

# ==================================================
# CAREER CARD EVENT GAME POOLS
# ==================================================

CAREER_EVENT_GAMES = {
    CAREER_ACTIVITY_CASUAL_CARDS: [
        "score_four",
        "bango",
        "crazy_eights",
    ],

    CAREER_ACTIVITY_POKER_NIGHT: [
        "texas_holdem",
        "seven_card_stud",
        "five_card_draw",
    ],

    CAREER_ACTIVITY_CASINO_NIGHT: [
        "blackjack",
        "roulette",
        "horse_races",
    ],

    CAREER_ACTIVITY_NICHE_NIGHT: [
        "faro",
        "five_o_poker",
        "blind_mans_bluff",
    ],

    CAREER_ACTIVITY_ARCADE_NIGHT: [
        "king_pong",
        "battle_bosses",
        "ace_invaders",
        "suit_snake",
        "prize_counter",
    ],
}

CAREER_EVENT_NAMES = {
    CAREER_ACTIVITY_CASUAL_CARDS:
        "Casual Cards",

    CAREER_ACTIVITY_POKER_NIGHT:
        "Poker Night",

    CAREER_ACTIVITY_CASINO_NIGHT:
        "Casino Night",

    CAREER_ACTIVITY_NICHE_NIGHT:
        "Niche Game Night",

    CAREER_ACTIVITY_ARCADE_NIGHT:
        "Arcade Night",
}

CAREER_CHALLENGES = [
    {
        "id": "draw_3",
        "name": "3 Draw",
    },
    {
        "id": "no_undo",
        "name": "No Undo",
    },
    {
        "id": "no_hints",
        "name": "No Hints",
    },
    {
        "id": "all_or_nothing",
        "name": "All or Nothing",
    },
]

def _build_career_event_summary():

    state.career_event_summary_title = (
        "EVENT COMPLETE"
    )

    state.career_event_summary_lines = []

    # ==================================================
    # No event data
    # ==================================================

    if state.career_event_entry is None:

        state.career_event_summary_lines = [
            "Event completed."
        ]

        return

    activity_type = (
        state.career_event_entry.get(
            "activity_type"
        )
    )

    event_name = (
        CAREER_EVENT_NAMES.get(
            activity_type,
            "Event"
        )
    )

    state.career_event_summary_title = (
        f"{event_name.upper()} COMPLETE"
    )

    if activity_type == CAREER_ACTIVITY_CASINO_NIGHT:
        blackjack_night_net = night_cash_total(legacy.game_namespace(), "blackjack", state.blackjack_session_net)
        roulette_night_net = night_cash_total(legacy.game_namespace(), "roulette", state.roulette_session_net)
        horse_races_night_net = night_cash_total(legacy.game_namespace(), "horse_races", state.horse_races_session_net)

        state.career_event_summary_title = (
            "CASINO NIGHT COMPLETE"
        )

        # ==========================================
        # Blackjack
        # ==========================================

        if blackjack_night_net > 0:

            blackjack_text = (
                f"Blackjack: +${blackjack_night_net:,}"
            )

        elif blackjack_night_net < 0:

            blackjack_text = (
                f"Blackjack: -${abs(blackjack_night_net):,}"
            )

        else:

            blackjack_text = (
                "Blackjack: $0"
            )

        # ==========================================
        # Roulette
        # ==========================================

        if roulette_night_net > 0:

            roulette_text = (
                f"Roulette: +${roulette_night_net:,}"
            )

        elif roulette_night_net < 0:

            roulette_text = (
                f"Roulette: -${abs(roulette_night_net):,}"
            )

        else:

            roulette_text = (
                "Roulette: $0"
            )

        # ==========================================
        # Horse Races
        # ==========================================

        if horse_races_night_net > 0:
            horse_races_text = f"Horse Races: +${horse_races_night_net:,}"
        elif horse_races_night_net < 0:
            horse_races_text = f"Horse Races: -${abs(horse_races_night_net):,}"
        else:
            horse_races_text = "Horse Races: $0"

        # ==========================================
        # Summary
        # ==========================================

        state.career_event_summary_lines = [
            blackjack_text,
            roulette_text,
            horse_races_text,
            f"Total: ${blackjack_night_net + roulette_night_net + horse_races_night_net:+,}",
            f"Blackjack rating: {state.blackjack_session_rating_change:+d}",
            f"Current Cash: ${state.career_cash:,}",
            f"Current Fans: {state.career_fans:,}",
        ]
        return

    # ==================================================
    # Casual Cards
    # ==================================================

    if (
            activity_type
            == CAREER_ACTIVITY_CASUAL_CARDS
    ):

        state.career_event_summary_lines = [
            "Casual Cards completed.",
            f"Current Rating: {state.career_rating:,}",
            f"Current Fans: {state.career_fans:,}",
        ]

        return

    # ==================================================
    # Poker Night
    # ==================================================

    if (
            activity_type
            == CAREER_ACTIVITY_POKER_NIGHT
    ):

        state.career_event_summary_lines = [
            "Poker Night completed.",
            f"Current Cash: ${state.career_cash:,}",
            f"Current Rating: {state.career_rating:,}",
            f"Current Fans: {state.career_fans:,}",
        ]

        return

    # ==================================================
    # Niche Game Night
    # ==================================================

    if (
            activity_type
            == CAREER_ACTIVITY_NICHE_NIGHT
    ):

        def _session_money_line(label, net):
            if net > 0:
                return f"{label}: +${net:,}"
            if net < 0:
                return f"{label}: -${abs(net):,}"
            return f"{label}: $0"

        faro_text = _session_money_line("Faro", night_cash_total(legacy.game_namespace(), "faro", night_game_net(state.career_event_result_log, "faro", state.faro_session_net)))
        five_o_text = _session_money_line("Five-O Poker", night_cash_total(legacy.game_namespace(), "five_o_poker", night_game_net(state.career_event_result_log, "five_o_poker", state.five_o_poker_session_net)))
        bluff_text = _session_money_line("Blind Man's Bluff", night_cash_total(legacy.game_namespace(), "blind_mans_bluff", night_game_net(state.career_event_result_log, "blind_mans_bluff", state.blind_mans_bluff_session_net)))
        state.career_event_summary_lines = [
            "Niche Game Night completed.",
            faro_text,
            five_o_text,
            bluff_text,
            f"Current Cash: ${state.career_cash:,}",
            f"Current Rating: {state.career_rating:,}",
            f"Current Fans: {state.career_fans:,}",
        ]

        return

    # ==================================================
    # Arcade Night
    # ==================================================

    if (
            activity_type
            == CAREER_ACTIVITY_ARCADE_NIGHT
    ):

        starting_tokens = int(legacy.game_namespace().get("career_event_start_arcade_tokens", state.arcade_state.get("tokens", 0)))
        starting_tickets = int(legacy.game_namespace().get("career_event_start_arcade_tickets", state.arcade_state.get("tickets", 0)))
        token_delta = int(state.arcade_state.get("tokens", 0)) - starting_tokens
        ticket_delta = int(state.arcade_state.get("tickets", 0)) - starting_tickets

        def _format_signed(value, prefix=""):
            sign = "+" if value >= 0 else "-"
            return f"{sign}{prefix}{abs(int(value)):,}"

        state.career_event_summary_lines = [
            "Arcade Night completed.",
            f"Tokens: {int(state.arcade_state.get('tokens', 0)):,} ({_format_signed(token_delta)})",
            f"Tickets: {int(state.arcade_state.get('tickets', 0)):,} ({_format_signed(ticket_delta)})",
            f"Tokens spent tonight: {int(legacy.game_namespace().get('arcade_night_tokens_spent', 0)):,}",
            f"Tickets won tonight: +{int(legacy.game_namespace().get('arcade_night_tickets_won', 0)):,}",
            f"Current Cash: ${state.career_cash:,}",
            f"Current Fans: {state.career_fans:,}",
        ]

        return

    # ==================================================
    # Generic fallback
    # ==================================================

    state.career_event_summary_lines = [
        f"{event_name} completed."
    ]

def build_career_event_summary():
    _build_career_event_summary()
    lines = [line for line in state.career_event_summary_lines if not line.startswith(("Current Rating:", "Current Fans:", "Blackjack rating:"))]
    delta = int(round(float(state.career_rating) - legacy.game_namespace().get("career_event_start_global", float(state.career_rating))))
    lines.append(f"Global Rating: {round(state.career_rating):,} ({delta:+d})")
    changes = []
    for key in ("strategy", "poker", "casino"):
        diff = int(round(float(state.career_ratings[key]) - legacy.game_namespace().get("career_event_start_"+key, float(state.career_ratings[key]))))
        if diff: changes.append(f"{key.title()} {diff:+d}")
    if changes: lines.append("  |  ".join(changes))
    fans = state.career_fans - legacy.game_namespace().get("career_event_start_fans", state.career_fans)
    lines.append(f"Fans: {state.career_fans:,} ({fans:+d})")
    if legacy.game_namespace().get("career_event_entry") and state.career_event_entry.get("activity_type") in (
            CAREER_ACTIVITY_CASUAL_CARDS, CAREER_ACTIVITY_POKER_NIGHT,
            CAREER_ACTIVITY_CASINO_NIGHT, CAREER_ACTIVITY_NICHE_NIGHT,
            legacy.game_namespace().get("CAREER_ACTIVITY_ARCADE_NIGHT", "arcade_night")):
        cash_change = int(state.career_cash - legacy.game_namespace().get("career_event_start_cash", state.career_cash))
        xp_change = max(0, int(state.player_xp - legacy.game_namespace().get("career_event_start_xp", state.player_xp)))
        sign = "+" if cash_change >= 0 else "-"
        lines.append(f"Night cash: {sign}${abs(cash_change):,}  |  XP earned: +{xp_change:,}")
    state.career_event_summary_lines = lines


CAREER_WORK_ACTIVITIES = {
    "custodian": [
        "Clean Toilets",
        "Mop Spill",
        "Dump Trash",
        "Wax Floors",
        "Fix A/C",
        "Start Fire",
    ],

    "satellite_repair": [
        "Repair Satellite",
        "Replace Antenna",
        "Fix Solar Panel",
        "Stop Thieves",
        "Cut Cables",
    ],

    "videographer": [
        "Film Tony Hawk",
        "Make Sports Montage",
        "Edit Footage",
        "Record Interview",
        "Render 4-Hour Video",
    ],

    "airline_pilot": [
        "Fly Route",
        "Red-Eye Flight",
        "Illicit Cargo Trip",
        "Drink in Pilot's Lounge",
        "Train Student",
    ],

    "spiritual_guru": [
        "Lead Retreat",
        "Teach Meditation",
        "Go on Podcast",
        "Guide Vision Quest",
        "Manage Cult",
    ],

    "solitaire_pensioner": [
        "Play Golf",
        "Feed Pigeons",
        "Watch Television",
        "Nap",
        "Complain",
    ],
}


def reset_career_event_result_log():
    state.career_event_result_log = []
    state.career_event_news_posted = False


def record_career_event_result(game_id, won=None, **details):
    fan_impact = details.pop("fan_impact", True)
    entry = {
        "game_id": game_id,
        "won": won,
    }
    entry.update(details)
    state.career_event_result_log.append(entry)

    # Career popularity can move in both directions now. Arcade machines use
    # their own ticket economy, so their results can explicitly opt out.
    if state.current_game_mode == "career" and won is False and fan_impact:
        net_value = details.get("net", 0)
        try:
            net_loss = max(0, -int(net_value))
        except (TypeError, ValueError):
            net_loss = 0
        legacy.lose_fans_for_bad_result(
            f"Poor {FREE_PLAY_GAME_NAMES.get(game_id, game_id.replace('_', ' ').title())} result",
            net_loss=net_loss,
            severity=1.0,
        )


def reset_career_event_session_totals(activity_type):

    if activity_type == CAREER_ACTIVITY_POKER_NIGHT:
        state.texas_holdem_session_net = 0
        state.five_card_draw_session_net = 0
        state.seven_card_stud_session_net = 0

    elif activity_type == CAREER_ACTIVITY_CASINO_NIGHT:
        state.blackjack_session_net = 0
        state.blackjack_session_rating_change = 0
        state.roulette_session_net = 0
        state.horse_races_session_net = 0
        state.horse_races_last_rewarded_races = 0

    elif activity_type == CAREER_ACTIVITY_NICHE_NIGHT:
        state.faro_session_net = 0
        state.five_o_poker_session_net = 0
        state.blind_mans_bluff_session_net = 0

    elif activity_type == CAREER_ACTIVITY_ARCADE_NIGHT:
        state.arcade_night_tokens_spent = 0
        state.arcade_night_tickets_won = 0

FREE_PLAY_GAME_NAMES = {
    "case_opening": "Case Opening",
    "solitaire": "Klondike Solitaire",
    "score_four": "Score-Four",
    "crazy_eights": "Crazy Eights",
    "bango": "Bango",
    "blackjack": "Blackjack",
    "roulette": "Roulette",
    "horse_races": "Horse Races",
    "texas_holdem": "Texas Hold'em",
    "five_card_draw": "Five-Card Draw",
    "seven_card_stud": "Seven-Card Stud",
    "faro": "Faro",
    "five_o_poker": "Five-O Poker",
    "blind_mans_bluff": "Blind Man's Bluff",
    "king_pong": "King Pong",
    "battle_bosses": "Battle Bosses",
    "cryptid_creatures": "Cryptid Creatures",
}
