"""The career calendar: days, weeks, the schedule and moving to the next day (moved out of legacy.py)."""
import random
from solitaireplus.career.alien_night import refresh_adventure_schedule
from solitaireplus.app import state
from solitaireplus.app.lazy import lazy
leaderboard_engine = lazy("solitaireplus.career.leaderboard_engine")
night = lazy("solitaireplus.career.events.night")
career_saving = lazy("solitaireplus.career.career_saving")
legacy = lazy("solitaireplus.legacy")


CAREER_WEEKDAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
]


def get_career_weekday_name():
    if (
        0
        <= state.career_weekday_index
        < len(
            CAREER_WEEKDAY_NAMES
        )
    ):
        return (
            CAREER_WEEKDAY_NAMES[
                state.career_weekday_index
            ]
        )

    return "Unknown"

def get_career_work_activity_name():

    activities = (
        night.CAREER_WORK_ACTIVITIES.get(
            state.career_job
        )
    )

    if not activities:
        return "Go to Work"

    return random.choice(
        activities
    )


def advance_career_day(
        completed=True,
        save_after=True
):

    # ==================================================
    # Record current day
    # ==================================================

    current_index = (
        legacy.get_current_career_activity_index()
    )

    if current_index is not None:

        current_entry = (
            state.career_current_schedule[
                current_index
            ]
        )

        current_entry[
            "completed"
        ] = completed

        state.career_completed_days.append(
            {
                "year": state.career_year,
                "month": state.career_month,
                "day": state.career_day_of_month,
                "completed": completed,
                "activity_type":
                    current_entry.get(
                        "activity_type"
                    ),
            }
        )

    # ==================================================
    # Advance Career clock
    # ==================================================

    state.career_day += 1

    state.career_day_of_month += 1

    state.career_weekday_index += 1

    if state.career_weekday_index >= 5:
        state.career_weekday_index = 0

    # ==================================================
    # End of current 15-day calendar block
    # ==================================================

    if (
            state.career_day_of_month
            > len(
        state.career_current_schedule
    )
    ):
        state.career_month += 1

        if state.career_month > 12:
            state.career_month = 1
            state.career_year += 1

        state.career_day_of_month = 1
        state.career_weekday_index = 0

        # Update the competitive world
        # once per new Career month.
        leaderboard_engine.update_career_leaderboard_ratings()
        legacy.maybe_add_monthly_flavor_news()

        state.career_current_schedule = (
            build_default_career_schedule()
        )

    if save_after:
        career_saving.auto_save_career()


def reset_career_hub_runtime():
    """Clear calendar/event selections before advancing or loading a profile."""
    state.pending_career_activity_index = None
    state.pending_career_activity_type = None
    state.pending_career_challenge_id = None
    state.career_event_entry = None
    state.career_event_has_activity = False
    state.career_event_summary_title = ""
    state.career_event_summary_lines = []
    state.career_news_page = 0
    state.career_leaderboard_page = 0
    legacy.career_hub_controls.reset()
    legacy.game.clear_challenge()


def build_default_career_schedule():
    schedule = []
    challenge_index = 0
    card_event_index = 0
    public_event_index = 0

    # Career months contain 30 weekdays, shown as two 15-day calendar halves.
    # Each half keeps the same overall rhythm: two normal Solitaire rounds,
    # three challenges, five card events, three work days, and two public events.
    monthly_challenges = []
    while len(monthly_challenges) < 6:
        cycle = list(night.CAREER_CHALLENGES)
        random.shuffle(cycle)
        monthly_challenges.extend(cycle)
    monthly_challenges = monthly_challenges[:6]

    monthly_card_events = []
    for _half in range(2):
        # Each half-month now features one of every themed night: Casual
        # Cards, Poker Night, Casino Night, Niche Game Night, and Arcade Night.
        half_events = [
            night.CAREER_ACTIVITY_CASUAL_CARDS,
            night.CAREER_ACTIVITY_POKER_NIGHT,
            night.CAREER_ACTIVITY_CASINO_NIGHT,
            night.CAREER_ACTIVITY_NICHE_NIGHT,
            night.CAREER_ACTIVITY_ARCADE_NIGHT,
        ]
        random.shuffle(half_events)
        monthly_card_events.extend(half_events)

    monthly_public_events = [
        {"title": "Press Interview", "event_id": "press_interview_01"},
        {"title": "Sign Autographs", "event_id": "sign_autographs_01"},
        {"title": "Head-to-Head", "event_id": "head_to_head_01"},
        {"title": "Bigfoot Night", "event_id": "bigfoot_night"},
    ]
    random.shuffle(monthly_public_events)

    half_patterns = (
        (
            night.CAREER_ACTIVITY_ROUND,
            "card",
            night.CAREER_ACTIVITY_WORK,
            "card",
            night.CAREER_ACTIVITY_CHALLENGE,
        ),
        (
            night.CAREER_ACTIVITY_EVENT,
            "card",
            night.CAREER_ACTIVITY_CHALLENGE,
            night.CAREER_ACTIVITY_WORK,
            night.CAREER_ACTIVITY_ROUND,
        ),
        (
            "card",
            night.CAREER_ACTIVITY_WORK,
            night.CAREER_ACTIVITY_CHALLENGE,
            "card",
            night.CAREER_ACTIVITY_EVENT,
        ),
    )
    week_patterns = half_patterns + half_patterns

    for week_index, pattern in enumerate(week_patterns):
        for weekday_index, slot_type in enumerate(pattern):
            day_number = week_index * 5 + weekday_index + 1

            if slot_type == "card":
                activity_type = monthly_card_events[card_event_index]
                card_event_index += 1
            else:
                activity_type = slot_type

            entry = {
                "day_number": day_number,
                "weekday_index": weekday_index,
                "activity_type": activity_type,
                "completed": False,
            }

            if activity_type == night.CAREER_ACTIVITY_ROUND:
                entry["title"] = "Play Solitaire"

            elif activity_type == night.CAREER_ACTIVITY_WORK:
                entry["title"] = get_career_work_activity_name()

            elif activity_type == night.CAREER_ACTIVITY_CHALLENGE:
                challenge = monthly_challenges[challenge_index]
                challenge_index += 1
                entry["title"] = "Challenge Round"
                entry["challenge_id"] = challenge["id"]
                entry["challenge_name"] = challenge["name"]

            elif activity_type == night.CAREER_ACTIVITY_EVENT:
                event_data = monthly_public_events[public_event_index]
                public_event_index += 1
                entry["title"] = event_data["title"]
                entry["event_id"] = event_data["event_id"]

            elif activity_type in (
                    night.CAREER_ACTIVITY_CASUAL_CARDS,
                    night.CAREER_ACTIVITY_POKER_NIGHT,
                    night.CAREER_ACTIVITY_CASINO_NIGHT,
                    night.CAREER_ACTIVITY_NICHE_NIGHT,
                    night.CAREER_ACTIVITY_ARCADE_NIGHT
            ):
                entry["title"] = night.CAREER_EVENT_NAMES[activity_type]
                entry["game_ids"] = night.CAREER_EVENT_GAMES[activity_type].copy()

                if activity_type == night.CAREER_ACTIVITY_POKER_NIGHT:
                    entry["high_stakes_game_id"] = random.choice(
                        entry["game_ids"]
                    ) if entry["game_ids"] else None

            schedule.append(entry)

    refresh_adventure_schedule(schedule, state.career_bigfoot_story, state.career_alien_story)
    return schedule

def ensure_career_schedule():

    if not state.career_current_schedule:
        state.career_current_schedule = build_default_career_schedule()
        return

    # Migrate existing 15-day saves in place. Keep the player's current first
    # half intact and append a freshly generated days 16-30 second half.
    if len(state.career_current_schedule) == 15:
        second_half = build_default_career_schedule()[15:30]
        state.career_current_schedule.extend(second_half)
