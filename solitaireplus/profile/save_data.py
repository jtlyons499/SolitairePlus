"""Building a save from the game's state and putting a loaded save back into it (moved out of legacy.py)."""
from solitaireplus.games.arcade.support import ARCADE_PRIZE_CATALOG
from solitaireplus.career.case_opening import ITEMS as CASE_ITEMS
from solitaireplus.career.fans import clamp_fans
import copy
from solitaireplus.profile.saves import make_default_profile
from solitaireplus.profile.achievements import normalize_achievement_state
from solitaireplus.career.fans import normalize_fan_trend
from solitaireplus.career.ratings import normalize_rating_bundle
from solitaireplus.career.activities import normalize_story
from solitaireplus.career.activities import reconcile_story_cosmetics
from solitaireplus.app import state
from solitaireplus.career.event_progress import store_event_progress
from solitaireplus.app.lazy import lazy
leaderboard_engine = lazy("solitaireplus.career.leaderboard_engine")
career_rewards = lazy("solitaireplus.career.career_rewards")
profile_select = lazy("solitaireplus.profile.profile_select")
leveling = lazy("solitaireplus.profile.leveling")
legacy = lazy("solitaireplus.legacy")
cursors = lazy("solitaireplus.ui.cursors")
assets = lazy("solitaireplus.app.assets")


def apply_fresh_profile():

    default_data = (
        make_default_profile()
    )

    apply_profile_save_data(
        default_data
    )

    state.player_name = "Player"
    state.profile_name_text = "Player"

def build_profile_save_data():
    from solitaireplus.games.arcade.support import clone_arcade_state as clone_arcade_save_state
    store_event_progress(legacy.game_namespace().get("career_event_entry"), legacy.game_namespace())

    profile_data = (
        make_default_profile()
    )

    # ----------------------------
    # Identity
    # ----------------------------

    profile_data[
        "identity"
    ][
        "name"
    ] = state.player_name

    profile_data[
        "identity"
    ][
        "gender"
    ] = state.profile_gender

    identity_data = profile_data["identity"]
    identity_data["country"] = state.profile_country_text.strip().upper()[:3]
    age_text = state.profile_age_text.strip()
    identity_data["age"] = int(age_text) if age_text.isdigit() else ""
    identity_data["hometown"] = state.profile_hometown_text.strip()
    identity_data["favorite_suit"] = state.profile_favorite_suit
    identity_data["bio"] = state.profile_bio_text.strip()

    avatar_data = profile_data[
        "identity"
    ][
        "avatar"
    ]

    avatar_data[
        "base"
    ] = state.selected_avatar_base

    avatar_data[
        "eyes"
    ] = state.selected_avatar_eyes

    avatar_data[
        "hair"
    ] = state.selected_avatar_hair

    avatar_data[
        "glasses"
    ] = state.selected_avatar_glasses

    avatar_data[
        "top"
    ] = state.selected_avatar_top

    # ----------------------------
    # Progression
    # ----------------------------

    profile_data[
        "progression"
    ][
        "level"
    ] = state.player_level

    profile_data[
        "progression"
    ][
        "xp"
    ] = state.player_xp

    profile_data[
        "progression"
    ][
        "solitaire_points"
    ] = state.player_solitaire_points

    career_data = profile_data[
        "career"
    ]

    # ----------------------------
    # Core progression
    # ----------------------------

    career_data[
        "news_items"
    ] = list(
        state.career_news_items
    )

    career_data[
        "leaderboard_state"
    ] = copy.deepcopy(
        state.career_leaderboard_state
    )

    career_data[
        "leaderboard_star_id"
    ] = state.career_leaderboard_star_id

    career_data[
        "rating"
    ] = state.career_rating

    career_data[
        "ratings"
    ] = dict(
        state.career_ratings
    )
    career_data["rating_schema_version"] = 2
    career_data["rating_results"] = copy.deepcopy(state.career_rating_results)
    career_data["npc_world"] = copy.deepcopy(state.career_npc_world)

    career_data[
        "cash"
    ] = state.career_cash

    career_data[
        "fans"
    ] = state.career_fans

    career_data[
        "fan_rewarded_jobs"
    ] = sorted(state.career_fan_rewarded_jobs)

    career_data[
        "fan_news_milestones"
    ] = sorted(state.career_fan_news_milestones)

    career_data["fan_trend"] = list(state.career_fan_trend)
    career_data["rating_news_flags"] = sorted(state.career_rating_news_flags)

    # ----------------------------
    # Calendar
    # ----------------------------

    career_data[
        "year"
    ] = state.career_year

    career_data[
        "month"
    ] = state.career_month

    career_data[
        "day"
    ] = state.career_day_of_month

    career_data[
        "weekday_index"
    ] = state.career_weekday_index

    career_data[
        "career_day"
    ] = state.career_day

    # ----------------------------
    # Lifestyle
    # ----------------------------

    career_data[
        "residence"
    ] = state.career_residence

    career_data[
        "owned_residences"
    ] = list(
        state.career_owned_residences
    )

    career_data[
        "job"
    ] = state.career_job

    # ----------------------------
    # Statistics
    # ----------------------------

    career_data[
        "rounds_won"
    ] = state.career_rounds_won

    career_data[
        "challenges_won"
    ] = state.career_challenges_won

    career_data[
        "total_moves"
    ] = state.career_total_moves

    # ----------------------------
    # Calendar / event history
    # ----------------------------

    career_data["interview_recent_ids"] = list(state.career_interview_recent_ids)
    career_data["bigfoot_story"] = copy.deepcopy(state.career_bigfoot_story)
    career_data["alien_story"] = copy.deepcopy(state.career_alien_story)

    career_data[
        "completed_days"
    ] = list(
        state.career_completed_days
    )

    career_data[
        "current_schedule"
    ] = list(
        state.career_current_schedule
    )

    # ----------------------------
    # News
    # ----------------------------

    career_data[
        "news_items"
    ] = list(
        state.career_news_items
    )

    career_data[
        "arcade"
    ] = clone_arcade_save_state(
        state.arcade_state
    )

    # Solitaire Points are not
    # implemented yet, so keep
    # the default value for now.

    # ----------------------------
    # Cosmetics
    # ----------------------------

    cosmetics = (
        profile_data[
            "cosmetics"
        ]
    )

    cosmetics[
        "selected_menu_background"
    ] = state.selected_menu_background

    cosmetics[
        "selected_felt"
    ] = state.selected_felt

    cosmetics[
        "selected_title"
    ] = state.selected_title

    cosmetics[
        "selected_cursor"
    ] = state.selected_cursor

    cosmetics[
        "unlocked_menu_backgrounds"
    ] = list(
        state.unlocked_menu_backgrounds
    )

    cosmetics[
        "unlocked_felts"
    ] = list(
        state.unlocked_felts
    )

    cosmetics[
        "unlocked_titles"
    ] = list(
        state.unlocked_titles
    )

    cosmetics[
        "unlocked_cursors"
    ] = list(
        cursors.unlocked_cursors
    )

    # Card backs exist in the game
    # now, but are not part of the
    # customization system yet.

    profile_data["achievements"] = {
        "unlocked": list(state.achievement_state.get("unlocked", [])),
        "stats": dict(state.achievement_state.get("stats", {})),
    }

    # ----------------------------
    # Gameplay settings
    # ----------------------------

    profile_settings = profile_data.setdefault(
        "settings",
        {}
    )

    profile_settings["score_four_layout"] = getattr(legacy.score_four_game, "layout", "compact")

    profile_settings[
        "solitaire_deal_mode"
    ] = legacy.game.deal_mode

    profile_data["cryptid_creatures"] = copy.deepcopy(legacy.game_namespace().get("cryptid_collection_state", profile_data["cryptid_creatures"]))
    from solitaireplus.games.poker.learning import normalize_learning
    profile_data["poker_learning"] = normalize_learning(legacy.game_namespace().get("career_poker_learning"))
    from solitaireplus.career.case_opening import normalize_case_state
    profile_data["case_opening"] = normalize_case_state(legacy.game_namespace().get("case_collection_state"))
    return profile_data

def apply_profile_save_data(
        data
):
    from solitaireplus.games.arcade.support import normalize_arcade_state as normalize_arcade_save_state
    from solitaireplus.career.alien_night import STORY as ALIEN_STORY, refresh_adventure_schedule
    state.career_bigfoot_story = normalize_story(data.get("career", {}).get("bigfoot_story"))
    state.career_alien_story = normalize_story(data.get("career", {}).get("alien_story"), data=ALIEN_STORY)
    from solitaireplus.games.poker.learning import normalize_learning
    state.career_poker_learning = normalize_learning(data.get("poker_learning"))
    from solitaireplus.career.case_opening import normalize_case_state
    state.case_collection_state = normalize_case_state(data.get("case_opening"))
    from solitaireplus.games.cryptid.collection import normalize_collection
    state.cryptid_collection_state = normalize_collection(data.get('cryptid_creatures'),data.get('progression',{}).get('level',1))

    # ----------------------------
    # Identity
    # ----------------------------

    identity = data.get(
        "identity",
        {}
    )

    avatar_data = identity.get(
        "avatar",
        {}
    )

    state.selected_avatar_base = avatar_data.get(
        "base",
        "base_01"
    )

    if state.selected_avatar_base not in assets.avatar_bases:
        state.selected_avatar_base = "base_01"

    state.selected_avatar_eyes = avatar_data.get(
        "eyes",
        "eyes_01"
    )

    if state.selected_avatar_eyes not in assets.avatar_eyes:
        state.selected_avatar_eyes = "eyes_01"

    state.selected_avatar_hair = avatar_data.get(
        "hair",
        "hair_01"
    )

    if state.selected_avatar_hair not in assets.avatar_hair:
        state.selected_avatar_hair = "hair_01"

    state.selected_avatar_glasses = avatar_data.get(
        "glasses",
        None
    )

    if (
            state.selected_avatar_glasses is not None
            and state.selected_avatar_glasses not in assets.avatar_glasses
    ):
        state.selected_avatar_glasses = None

    state.selected_avatar_top = avatar_data.get(
        "top",
        "top_01"
    )

    if state.selected_avatar_top not in assets.avatar_tops:
        state.selected_avatar_top = "top_01"

    state.player_name = identity.get(
        "name",
        "Player"
    )

    state.profile_name_text = state.player_name

    state.profile_gender = identity.get(
        "gender",
        "non-binary"
    )

    state.profile_country_text = str(identity.get("country", "") or "").upper()[:3]
    raw_age = identity.get("age", "")
    state.profile_age_text = str(raw_age) if raw_age not in (None, "") else ""
    state.profile_hometown_text = str(identity.get("hometown", "") or "")[:48]
    state.profile_bio_text = str(identity.get("bio", "") or "")[:180]
    state.profile_favorite_suit = str(identity.get("favorite_suit", "") or "")
    if state.profile_favorite_suit not in profile_select.favorite_suit_options:
        state.profile_favorite_suit = ""

    # ----------------------------
    # Progression
    # ----------------------------

    progression = data.get(
        "progression",
        {}
    )

    state.player_level = progression.get(
        "level",
        1
    )

    state.player_xp = progression.get(
        "xp",
        0
    )

    state.player_solitaire_points = progression.get(
        "solitaire_points",
        0
    )

    state.player_xp_to_next = (
        leveling.get_next_level_xp(
            state.player_level
        )
    )


    # ----------------------------
    # Core progression
    # ----------------------------

    career_data = data.get(
        "career",
        {}
    )

    state.career_leaderboard_state = copy.deepcopy(
        career_data.get(
            "leaderboard_state",
            {}
        )
    )

    state.career_leaderboard_star_id = (
        career_data.get(
            "leaderboard_star_id"
        )
    )
    state.career_npc_world = copy.deepcopy(career_data.get("npc_world", {}))

    state.career_rating = career_data.get(
        "rating",
        1000
    )

    state.career_ratings = normalize_rating_bundle(
        career_data.get(
            "ratings"
        ),
        legacy_rating=state.career_rating
    )

    state.career_rating = state.career_ratings[
        "overall"
    ]
    state.career_rating_results = copy.deepcopy(career_data.get("rating_results", {}))

    state.career_cash = career_data.get(
        "cash",
        0
    )

    state.career_fans = clamp_fans(
        career_data.get(
            "fans",
            0
        )
    )

    state.career_fan_rewarded_jobs = set(
        career_data.get(
            "fan_rewarded_jobs",
            []
        )
    )

    state.career_fan_news_milestones = set(
        int(value)
        for value in career_data.get(
            "fan_news_milestones",
            []
        )
        if str(value).isdigit()
    )

    state.career_fan_trend = normalize_fan_trend(career_data.get("fan_trend", []))
    state.career_rating_news_flags = set(str(value) for value in career_data.get("rating_news_flags", []))

    state.arcade_state = normalize_arcade_save_state(
        career_data.get(
            "arcade",
            {}
        )
    )

    # ----------------------------
    # Calendar
    # ----------------------------

    state.career_year = career_data.get(
        "year",
        2026
    )

    state.career_month = career_data.get(
        "month",
        1
    )

    state.career_day_of_month = career_data.get(
        "day",
        1
    )

    state.career_weekday_index = (
        career_data.get(
            "weekday_index",
            0
        )
    )

    state.career_day = career_data.get(
        "career_day",
        1
    )

    # ----------------------------
    # Lifestyle
    # ----------------------------

    state.career_residence = (
        career_data.get(
            "residence",
            "dingy_apartment"
        )
    )

    state.career_owned_residences = list(
        career_data.get(
            "owned_residences",
            [
                "dingy_apartment"
            ]
        )
    )

    if (
            "dingy_apartment"
            not in state.career_owned_residences
    ):
        state.career_owned_residences.append(
            "dingy_apartment"
        )

    state.career_job = career_data.get(
        "job",
        "custodian"
    )

    # ----------------------------
    # Statistics
    # ----------------------------

    state.career_rounds_won = (
        career_data.get(
            "rounds_won",
            0
        )
    )

    state.career_challenges_won = (
        career_data.get(
            "challenges_won",
            0
        )
    )

    state.career_total_moves = (
        career_data.get(
            "total_moves",
            0
        )
    )

    # ----------------------------
    # Calendar / events
    # ----------------------------

    state.career_completed_days = list(
        career_data.get(
            "completed_days",
            []
        )
    )

    state.career_current_schedule = list(
        career_data.get(
            "current_schedule",
            []
        )
    )

    # ----------------------------
    # News
    # ----------------------------

    state.career_news_items = list(
        career_data.get(
            "news_items",
            []
        )
    )

    # ----------------------------
    # Achievements
    # ----------------------------

    state.achievement_state = normalize_achievement_state(
        data.get("achievements", {})
    )
    state.achievements_scroll_y = 0
    state.achievement_popup_queue = []
    state.achievement_popup_current = None

    # ----------------------------
    # Cosmetics
    # ----------------------------

    cosmetics = data.get(
        "cosmetics",
        {}
    )

    state.selected_menu_background = (
        cosmetics.get(
            "selected_menu_background",
            "bg_default"
        )
    )

    state.selected_felt = cosmetics.get(
        "selected_felt",
        "f_default"
    )

    state.selected_title = cosmetics.get(
        "selected_title",
        "title_default"
    )

    state.selected_cursor = cosmetics.get(
        "selected_cursor",
        "cursor"
    )

    if state.selected_cursor not in cursors.cursor_runtime_surfaces:
        if "cursor" in cursors.cursor_runtime_surfaces:
            state.selected_cursor = "cursor"
        elif cursors.cursor_runtime_surfaces:
            state.selected_cursor = next(
                iter(cursors.cursor_runtime_surfaces)
            )

    state.unlocked_menu_backgrounds = set(
        cosmetics.get(
            "unlocked_menu_backgrounds",
            [
                "bg_default"
            ]
        )
    )

    state.unlocked_felts = set(
        cosmetics.get(
            "unlocked_felts",
            [
                "f_default"
            ]
        )
    )

    state.unlocked_titles = set(
        cosmetics.get(
            "unlocked_titles",
            [
                "title_default"
            ]
        )
    )

    # Older profiles predate cursor ownership. Preserve all legacy cursors as
    # owned while keeping new Case/Arcade reward cursors locked until earned.
    legacy_cursor_ids = set(cursors.cursor_cosmetics.keys()) - legacy.REWARD_CURSOR_IDS
    unlocked_cursors = set(
        cosmetics.get(
            "unlocked_cursors",
            legacy_cursor_ids,
        )
    )
    unlocked_cursors.add("cursor")
    unlocked_cursors.intersection_update(set(cursors.cursor_cosmetics.keys()) | legacy.REWARD_CURSOR_IDS)

    # Reconcile possession-backed cosmetics so an earned reward remains owned
    # even if it was earned before its PNG existed or came from an older save.
    from solitaireplus.profile.cosmetics import unlock_reward
    for item_id, count in state.case_collection_state.get("inventory", {}).items():
        item = CASE_ITEMS.get(item_id, {})
        if count and item.get("kind") == "cosmetic":
            unlock_reward(
                item.get("cosmetic_type"), item.get("asset_id"),
                state.unlocked_menu_backgrounds, state.unlocked_felts, state.unlocked_titles, unlocked_cursors,
            )
    redeemed_arcade_ids = set(state.arcade_state.get("trophies", []))
    for prize in ARCADE_PRIZE_CATALOG:
        if prize.get("kind") == "cosmetic" and prize.get("id") in redeemed_arcade_ids:
            unlock_reward(
                prize.get("cosmetic_type"), prize.get("asset_id"),
                state.unlocked_menu_backgrounds, state.unlocked_felts, state.unlocked_titles, unlocked_cursors,
            )

    if state.selected_cursor not in unlocked_cursors:
        state.selected_cursor = "cursor" if "cursor" in cursors.cursor_runtime_surfaces else next(iter(unlocked_cursors), state.selected_cursor)

    gameplay_settings = data.get(
        "settings",
        {}
    )

    legacy.score_four_game.layout = "wide" if gameplay_settings.get("score_four_layout") == "wide" else "compact"

    requested_deal_mode = gameplay_settings.get(
        "solitaire_deal_mode",
        "random"
    )
    if not legacy.VERIFIED_DEALS_ENABLED and requested_deal_mode == "verified":
        requested_deal_mode = "random"
    legacy.game.set_deal_mode(requested_deal_mode)
    for entry in state.career_current_schedule:
        if entry.get("event_id") == "career_encounter" and not entry.get("completed"):
            entry.update(title="Bigfoot Night", event_id="bigfoot_night")
    history = data.get("career", {}).get("interview_recent_ids", [])
    state.career_interview_recent_ids = [value for value in history if isinstance(value, str)][-12:] if isinstance(history, list) else []
    reconcile_story_cosmetics(state.career_bigfoot_story, state.unlocked_menu_backgrounds, state.unlocked_felts, state.unlocked_titles)
    reconcile_story_cosmetics(state.career_alien_story, state.unlocked_menu_backgrounds, state.unlocked_felts, state.unlocked_titles, data=ALIEN_STORY)
    refresh_adventure_schedule(state.career_current_schedule, state.career_bigfoot_story, state.career_alien_story, state.career_day_of_month)
    profile_select.sync_achievement_cosmetic_rewards()
    career_rewards.grant_rating_cosmetics(force=True)
    leaderboard_engine.sync_career_npc_runtime_state()
    legacy.sync_selected_cosmetics()
    cursors.apply_selected_cursor()
