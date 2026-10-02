import json
import os


# ==================================================
# SAVE CONFIG
# ==================================================

SAVE_FOLDER = "saves"

PROFILE_VERSION = 2

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

            # Temporary until the avatar system
            # replaces the old gender avatars.
            "gender": "non-binary",

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
            "cash": 0,
            "fans": 0,

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

        "settings": {
            "preferred_difficulty":
                "normal",
        },
    }


# ==================================================
# SAVE
# ==================================================

def save_profile(
        profile_data,
        slot=1
):
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