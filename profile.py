import json
import os

from career_ratings import migrate_profile_ratings


# ==================================================
# SAVE CONFIG
# ==================================================

SAVE_FOLDER = "saves"

PROFILE_VERSION = 6

PROFILE_SLOT_COUNT = 3


# ==================================================
# PATH HELPERS
# ==================================================

def get_profile_path(slot):
    return os.path.join(
        SAVE_FOLDER,
        f"profile_{slot}.json"
    )


# ==================================================
# DEFAULT PROFILE
# ==================================================

def make_default_profile():
    return {
        "profile_version": PROFILE_VERSION,

        "identity": {
            "name": "Player",

            # Personal details shown on the Career leaderboard bio.
            # Older saves omit these fields and are migrated by main.py.
            "gender": "non-binary",
            "country": "",
            "age": "",
            "hometown": "",
            "favorite_suit": "",
            "bio": "",

            "avatar": {
                "base": "base_01",
                "eyes": "eyes_01",
                "hair": "hair_01",
                "glasses": None,
                "top": "top_01",
            },
        },

        "progression": {
            "level": 1,
            "xp": 0,
            "solitaire_points": 0,
        },



        "career": {
            "unlocked": False,

            # ----------------------------
            # Core progression
            # ----------------------------

            "rating": 1000,

            # Overall is derived from the seven game ratings. The legacy
            # field mirrors it for job unlocks and older UI callers.
            "rating_schema_version": 2,
            "rating_results": {},
            "ratings": {
                "overall": 1000,
                "solitaire": 1000,
                "texas_holdem": 1000,
                "five_card_draw": 1000,
                "seven_card_stud": 1000,
                "blackjack": 1000,
                "roulette": 1000,
                "score_four": 1000,
            },

            "cash": 0,
            "fans": 0,
            "fan_rewarded_jobs": [],
            "fan_news_milestones": [],

            # ----------------------------
            # Leaderboard Random GOAT
            # ----------------------------

            "leaderboard_state": {},
            "leaderboard_star_id": None,

            # ----------------------------
            # Calendar
            # ----------------------------

            "year": 2026,
            "month": 1,
            "day": 1,

            "weekday_index": 0,

            # 0 = Monday
            # 1 = Tuesday
            # 2 = Wednesday
            # 3 = Thursday
            # 4 = Friday

            "career_day": 1,

            # ----------------------------
            # Lifestyle
            # ----------------------------

            "residence": "dingy_apartment",

            "owned_residences": [
                "dingy_apartment"
            ],

            "job": "custodian",

            # ----------------------------
            # Career statistics
            # ----------------------------

            "rounds_won": 0,
            "challenges_won": 0,
            "total_moves": 0,

            # ----------------------------
            # Calendar / event state
            # ----------------------------

            "completed_days": [],

            "current_schedule": [],

            # ----------------------------
            # News
            # ----------------------------

            "news_items": [],
        },

        "cosmetics": {
            "selected_menu_background":
                "bg_default",

            "selected_felt":
                "f_default",

            "selected_title":
                "title_default",

            "selected_card_back":
                "back_default",

            "selected_cursor":
                "cursor",

            "unlocked_menu_backgrounds": [
                "bg_default"
            ],

            "unlocked_felts": [
                "f_default"
            ],

            "unlocked_titles": [
                "title_default"
            ],

            "unlocked_card_backs": [
                "back_default"
            ],
        },

        "achievements": {
            "unlocked": [],
            "stats": {},
        },

        "settings": {
            "preferred_difficulty":
                "normal",

            "solitaire_deal_mode":
                "random",
        },
    }


# ==================================================
# SAVE
# ==================================================

def save_profile(
        profile_data,
        slot=1
):
    migrate_profile_ratings(profile_data)
    profile_data["profile_version"] = PROFILE_VERSION

    os.makedirs(
        SAVE_FOLDER,
        exist_ok=True
    )

    path = get_profile_path(
        slot
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            profile_data,
            file,
            indent=4
        )


# ==================================================
# LOAD
# ==================================================

def load_profile(
        slot=1
):
    path = get_profile_path(
        slot
    )

    if not os.path.exists(
        path
    ):
        return None

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:
        data = json.load(
            file
        )

    migrate_profile_ratings(data)
    data["profile_version"] = PROFILE_VERSION
    return data


# ==================================================
# SLOT CHECK
# ==================================================

def profile_exists(slot):
    return os.path.exists(
        get_profile_path(
            slot
        )
    )


# ==================================================
# DELETE
# ==================================================

def delete_profile(slot):
    path = get_profile_path(
        slot
    )

    if os.path.exists(
        path
    ):
        os.remove(
            path
        )
