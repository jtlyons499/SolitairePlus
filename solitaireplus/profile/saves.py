from solitaireplus.career.case_opening import new_case_state, normalize_case_state
from solitaireplus.games.arcade.support import make_default_arcade_state, normalize_arcade_state
from solitaireplus.games.poker.learning import new_learning, normalize_learning
import hashlib
import json
import os
import shutil
import tempfile
import time
from pathlib import Path

from solitaireplus.career.ratings import migrate_profile_ratings, make_player_rating_bundle, RATING_SCHEMA_VERSION
from solitaireplus.games.cryptid.collection import new_collection, normalize_collection


# ==================================================
# SAVE CONFIG
# ==================================================

from solitaireplus.app.runtime_support import save_directory
SAVE_FOLDER = str(save_directory())

PROFILE_VERSION = 10

# ==================================================
# SAVE VERSIONS AND MIGRATIONS
#
# RULE: whenever the shape of a save changes, add 1 to PROFILE_VERSION and add a
# function to MIGRATIONS that turns a save of the OLD version into the new one.
#   MIGRATIONS = {10: upgrade_10_to_11, 11: upgrade_11_to_12}
# Each function receives the save dict and returns it. They run in order on load,
# so a save from any older version is brought up to date step by step.
# (Saves up to version 10 are already handled by the normalize_* calls below and by
# main.py, so the list starts empty.)
# A save from a NEWER version is never loaded or overwritten: an older game would
# silently drop the newer data. The player is told to update instead.
# ==================================================

MIGRATIONS = {}


class ProfileUnavailable(Exception):
    """A save exists but cannot be opened. str(error) is the message for the player."""
    short_label = "Can't open"


class ProfileDamaged(ProfileUnavailable):
    short_label = "Damaged save"


class ProfileTooNew(ProfileUnavailable):
    short_label = "Needs update"


def migrate(data):
    """Bring a loaded save up to PROFILE_VERSION. Raises ProfileTooNew for newer saves."""
    try:
        version = int(data.get("profile_version", 0) or 0)
    except (TypeError, ValueError):
        version = 0
    if version > PROFILE_VERSION:
        raise ProfileTooNew(
            "This save was made by a newer version of Solitaire+. "
            "Update the game (main menu or Options > Updates) to play it."
        )
    while version < PROFILE_VERSION:
        step = MIGRATIONS.get(version)
        if step is not None:
            data = step(data)
        version += 1
    data["profile_version"] = PROFILE_VERSION
    return data

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
        "cryptid_creatures": new_collection(),
        "poker_learning": new_learning(),
        "case_opening": new_case_state(),

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

            # Global is derived from Strategy, Poker and Casino.
            "rating_schema_version": RATING_SCHEMA_VERSION,
            "rating_results": {},
            "ratings": make_player_rating_bundle(),

            "cash": 0,
            "fans": 0,
            "fan_rewarded_jobs": [],
            "fan_news_milestones": [],

            # ----------------------------
            # Leaderboard Random GOAT
            # ----------------------------

            "leaderboard_state": {},
            "npc_world": {},
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

            "arcade": make_default_arcade_state(),
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
    profile_data.setdefault("career", {}).setdefault("npc_world", {})
    profile_data.setdefault("career", {}).setdefault("arcade", make_default_arcade_state())
    profile_data["career"]["arcade"] = normalize_arcade_state(profile_data["career"].get("arcade"))
    profile_data["cryptid_creatures"]=normalize_collection(profile_data.get("cryptid_creatures"),profile_data.get("progression",{}).get("level",1))
    profile_data["poker_learning"] = normalize_learning(profile_data.get("poker_learning"))
    profile_data["case_opening"] = normalize_case_state(profile_data.get("case_opening"))
    profile_data["profile_version"] = PROFILE_VERSION

    os.makedirs(
        SAVE_FOLDER,
        exist_ok=True
    )

    path = get_profile_path(
        slot
    )

    path = os.path.abspath(path)
    keep_backup(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=os.path.dirname(path), suffix=".tmp", delete=False) as file:
            temporary = file.name
            json.dump(profile_data, file, indent=4)
            file.flush()
            os.fsync(file.fileno())
        try:
            replace_with_retry(temporary, path)
        except PermissionError:
            # Keep the old save intact. A new filename avoids a lock on that file.
            recovery = f"{path}.recovery.{time.time_ns()}.json"
            os.replace(temporary, recovery)
            temporary = None
            print(f"Save file is locked. Latest progress preserved in: {recovery}")
            return False
        temporary = None
        # Only retire recovery copies after the normal save has committed.
        for recovery in recovery_paths(slot):
            try:
                recovery.unlink()
            except OSError:
                pass
        return True
    finally:
        if temporary and os.path.exists(temporary):
            try:
                os.remove(temporary)
            except OSError:
                pass


def backup_path(slot):
    return get_profile_path(slot) + ".bak"


def keep_backup(path):
    """Before overwriting a save, keep the previous one as <name>.bak if it is readable.

    A damaged file never replaces a good backup.
    """
    if not os.path.isfile(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as file:
            if not isinstance(json.load(file), dict):
                return
        shutil.copy2(path, path + ".bak")
    except (OSError, ValueError):
        pass


def replace_with_retry(source, destination):
    for attempt, delay in enumerate((0.05, 0.1, 0.2, 0.4, 0.8, 0)):
        try:
            os.replace(source, destination)
            return
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(delay)


def recovery_paths(slot):
    path = Path(get_profile_path(slot))
    return [p for p in path.parent.glob(path.name + ".recovery.*.json") if ".damaged-" not in p.name]


def latest_profile_path(slot):
    candidates = [Path(get_profile_path(slot)), *recovery_paths(slot)]
    candidates = [path for path in candidates if path.is_file()]
    return max(candidates, key=lambda path: path.stat().st_mtime_ns) if candidates else None


# ==================================================
# LOAD
# ==================================================

def _read_save(path):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("save is not a JSON object")
    return data


def _keep_damaged_copy(path):
    """Copy an unreadable save aside (never delete it) so it could be repaired by hand.

    The profile screen reloads saves every frame, so the copy is named after the
    file's content and made only once per damaged version.
    """
    try:
        digest = hashlib.sha1(Path(path).read_bytes()).hexdigest()[:10]
        copy = f"{path}.damaged-{digest}.json"
        if not os.path.exists(copy):
            shutil.copy2(path, copy)
            print(f"Save file could not be read; kept a copy at {copy} and tried older copies.")
    except OSError:
        pass


def load_profile(
        slot=1
):
    """Load a save slot. Returns None for an empty slot.

    Tries the newest file first, then older copies (recovery files, then the
    .bak of the previous good save). Raises ProfileDamaged if every copy is
    unreadable, and ProfileTooNew if the save comes from a newer game version.
    """
    newest = latest_profile_path(slot)
    candidates = [newest] if newest else []
    candidates += sorted((p for p in [Path(get_profile_path(slot)), *recovery_paths(slot)]
                          if p.is_file() and p != newest),
                         key=lambda p: p.stat().st_mtime_ns, reverse=True)
    if Path(backup_path(slot)).is_file():
        candidates.append(Path(backup_path(slot)))
    if not candidates:
        return None

    data = None
    for path in candidates:
        try:
            data = _read_save(path)
            break
        except (OSError, ValueError):
            _keep_damaged_copy(path)
    if data is None:
        raise ProfileDamaged(
            f"Profile {slot} is damaged and no readable backup was found. "
            "A copy was kept in the saves folder; delete this slot to start over."
        )

    data = migrate(data)
    migrate_profile_ratings(data)
    data.setdefault("career", {}).setdefault("npc_world", {})
    data["cryptid_creatures"]=normalize_collection(data.get("cryptid_creatures"),data.get("progression",{}).get("level",1))
    data["poker_learning"] = normalize_learning(data.get("poker_learning"))
    data["case_opening"] = normalize_case_state(data.get("case_opening"))
    data["profile_version"] = PROFILE_VERSION
    return data


# ==================================================
# SLOT CHECK
# ==================================================

def profile_exists(slot):
    return latest_profile_path(slot) is not None


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
    for recovery in recovery_paths(slot):
        recovery.unlink()
    if os.path.exists(backup_path(slot)):
        os.remove(backup_path(slot))

