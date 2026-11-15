"""The F10 debug menu's actions: the debug_open_* launchers, levels, ratings and the Career calendar (moved out of legacy.py)."""
from solitaireplus.profile.achievements import ACHIEVEMENT_DEFINITIONS
from solitaireplus.app.settings import DEFAULT_DIFFICULTY
from solitaireplus.app.settings import LEVEL_XP_THRESHOLDS
from solitaireplus.npc.manager import NPCS
from solitaireplus.npc.manager import PROSPECT_POOL
from solitaireplus.career.npc_world import add_prospect
from solitaireplus.career.ratings import apply_rating_change
from solitaireplus.career import career_rewards
from solitaireplus.career import career_saving
from solitaireplus.debug.game_mode import end_debug_game_mode
from solitaireplus.debug.game_mode import enter_debug_game_mode
from solitaireplus.npc.manager import get_random_blackjack_dealer
from solitaireplus.npc.manager import get_score_four_opponent_choices
from solitaireplus.games.solitaire import head_to_head_screen
from solitaireplus.profile.achievements import iter_rewards as iter_achievement_rewards
from solitaireplus.debug.game_mode import keep_night_context
from solitaireplus.debug.poker_select import make_default_selection as make_debug_poker_default_selection
import random
from solitaireplus.debug.game_mode import restore_night_context
from solitaireplus.debug.menu import show_debug_message
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
legacy = lazy("solitaireplus.legacy")
score_four_screen = lazy("solitaireplus.games.cards.score_four_screen")
roulette_screen = lazy("solitaireplus.games.casino.roulette_screen")
night = lazy("solitaireplus.career.events.night")
news_screen = lazy("solitaireplus.career.news_screen")
machine_select = lazy("solitaireplus.games.arcade.machine_select")
leveling = lazy("solitaireplus.profile.leveling")
leaderboard_engine = lazy("solitaireplus.career.leaderboard_engine")
horse_races_screen = lazy("solitaireplus.games.casino.horse_races_screen")
game_screen = lazy("solitaireplus.games.dead_mans_hand.game_screen")
five_o_screen = lazy("solitaireplus.games.poker.five_o_screen")
faro_screen = lazy("solitaireplus.games.casino.faro_screen")
crazy_eights_screen = lazy("solitaireplus.games.cards.crazy_eights_screen")
calendar = lazy("solitaireplus.career.calendar")
blind_mans_bluff_screen = lazy("solitaireplus.games.poker.blind_mans_bluff_screen")
bango_screen = lazy("solitaireplus.games.cards.bango_screen")


def adjust_debug_ratings(amount):
    for key in ("strategy", "poker", "casino"):
        apply_rating_change(state.career_ratings, key, amount, scale_rewards=False)
    state.career_rating = state.career_ratings["overall"]
    career_rewards.grant_rating_cosmetics()


def debug_unlock_next_achievement():
    unlocked = set(state.achievement_state.get("unlocked", []))
    for definition in ACHIEVEMENT_DEFINITIONS:
        if definition["id"] in unlocked:
            continue

        state.achievement_state.setdefault("unlocked", []).append(definition["id"])
        fan_reward = leveling.award_achievement_fans(
            definition.get("difficulty", "normal"),
            definition.get("title", "Achievement"),
        )
        cosmetic_labels = []
        for reward in iter_achievement_rewards(definition):
            label = legacy.unlock_achievement_cosmetic(reward)
            if label:
                cosmetic_labels.append(label)
        legacy.queue_achievement_popup(
            definition,
            fan_reward,
            ", ".join(cosmetic_labels),
        )
        career_saving.auto_save_career()
        return definition.get("title", "Achievement")

    return None

def debug_open_casual_cards():

    state.career_event_entry = {
        "activity_type": night.CAREER_ACTIVITY_CASUAL_CARDS,
        "title": "Casual Cards",
        "game_ids": (
            night.CAREER_EVENT_GAMES[
                night.CAREER_ACTIVITY_CASUAL_CARDS
            ].copy()
        ),
        "debug": True,
    }

    state.career_event_has_activity = False
    night.reset_career_event_result_log()
    night.reset_career_event_session_totals(night.CAREER_ACTIVITY_CASUAL_CARDS)

    state.current_state = state_names.STATE_CAREER_EVENT_SELECT


def debug_open_casino_night():

    state.career_event_entry = {
        "activity_type": night.CAREER_ACTIVITY_CASINO_NIGHT,
        "title": "Casino Night",
        "game_ids": (
            night.CAREER_EVENT_GAMES[
                night.CAREER_ACTIVITY_CASINO_NIGHT
            ].copy()
        ),
        "debug": True,
    }

    state.career_event_has_activity = False
    night.reset_career_event_result_log()
    night.reset_career_event_session_totals(night.CAREER_ACTIVITY_CASINO_NIGHT)

    state.current_state = state_names.STATE_CAREER_EVENT_SELECT


def debug_prepare_arcade_night():
    """Create a standalone Arcade Night context for F10 testing."""

    enter_debug_game_mode()
    state.career_event_entry = {
        "activity_type": night.CAREER_ACTIVITY_ARCADE_NIGHT,
        "title": "Arcade Night",
        "game_ids": night.CAREER_EVENT_GAMES[night.CAREER_ACTIVITY_ARCADE_NIGHT].copy(),
        "debug": True,
    }
    state.career_event_has_activity = False
    night.reset_career_event_result_log()
    night.reset_career_event_session_totals(night.CAREER_ACTIVITY_ARCADE_NIGHT)


def debug_open_arcade_night():
    debug_prepare_arcade_night()
    state.current_state = state_names.STATE_CAREER_EVENT_SELECT


def debug_open_king_pong():
    debug_prepare_arcade_night()
    machine_select.open_king_pong_opponent_select(refresh=True)


def debug_open_battle_bosses():
    debug_prepare_arcade_night()
    machine_select.open_battle_bosses_opponent_select(refresh=True)


def debug_open_ace_invaders():
    debug_prepare_arcade_night()
    machine_select.open_ace_invaders_difficulty_select(reset_selection=True)


def debug_open_suit_snake():
    debug_prepare_arcade_night()
    machine_select.open_suit_snake_difficulty_select(reset_selection=True)



def debug_open_crazy_eights():

    state.career_event_entry = {
        "activity_type": night.CAREER_ACTIVITY_CASUAL_CARDS,
        "title": "Casual Cards",
        "game_ids": night.CAREER_EVENT_GAMES[
            night.CAREER_ACTIVITY_CASUAL_CARDS
        ].copy(),
        "debug": True,
    }

    state.career_event_has_activity = False
    crazy_eights_screen.start_crazy_eights_session()



def debug_open_bango():

    state.career_event_entry = {
        "activity_type": night.CAREER_ACTIVITY_CASUAL_CARDS,
        "title": "Casual Cards",
        "game_ids": night.CAREER_EVENT_GAMES[
            night.CAREER_ACTIVITY_CASUAL_CARDS
        ].copy(),
        "debug": True,
    }

    state.career_event_has_activity = False
    bango_screen.start_bango_session()



def debug_open_score_four_solo():

    state.career_event_entry = {
        "activity_type": night.CAREER_ACTIVITY_CASUAL_CARDS,
        "title": "Casual Cards",
        "game_ids": (
            night.CAREER_EVENT_GAMES[
                night.CAREER_ACTIVITY_CASUAL_CARDS
            ].copy()
        ),
        "debug": True,
    }

    state.career_event_has_activity = False

    score_four_screen.score_four_game.start_solo_session()

    state.current_state = state_names.STATE_SCORE_FOUR


def debug_open_score_four_competitive():

    state.career_event_entry = {
        "activity_type": night.CAREER_ACTIVITY_CASUAL_CARDS,
        "title": "Casual Cards",
        "game_ids": (
            night.CAREER_EVENT_GAMES[
                night.CAREER_ACTIVITY_CASUAL_CARDS
            ].copy()
        ),
        "debug": True,
    }

    state.career_event_has_activity = False

    state.score_four_opponent_choices = (
        get_score_four_opponent_choices()
    )

    state.score_four_opponent_npc = None

    state.current_state = state_names.STATE_SCORE_FOUR_OPPONENT_SELECT


def debug_open_blackjack():

    state.career_event_entry = {
        "activity_type": night.CAREER_ACTIVITY_CASINO_NIGHT,
        "title": "Casino Night",
        "game_ids": (
            night.CAREER_EVENT_GAMES[
                night.CAREER_ACTIVITY_CASINO_NIGHT
            ].copy()
        ),
        "debug": True,
    }

    state.career_event_has_activity = False

    state.blackjack_dealer_npc = (
        get_random_blackjack_dealer()
    )

    state.blackjack_selected_bet_percentage = None
    state.blackjack_bet_dropdown_open = False
    state.blackjack_session_net = 0
    state.blackjack_session_rating_change = 0

    state.current_state = state_names.STATE_BLACKJACK_BET

def debug_open_roulette():

    state.career_event_entry = {
        "activity_type": night.CAREER_ACTIVITY_CASINO_NIGHT,
        "title": "Casino Night",
        "game_ids": (
            night.CAREER_EVENT_GAMES[
                night.CAREER_ACTIVITY_CASINO_NIGHT
            ].copy()
        ),
        "debug": True,
    }

    state.career_event_has_activity = False

    state.roulette_session_net = 0

    roulette_screen.roulette_game.reset_round()

    state.current_state = state_names.STATE_ROULETTE


def debug_open_horse_races():

    enter_debug_game_mode()
    state.career_event_entry = {
        "activity_type": night.CAREER_ACTIVITY_CASINO_NIGHT,
        "title": "Casino Night",
        "game_ids": night.CAREER_EVENT_GAMES[
            night.CAREER_ACTIVITY_CASINO_NIGHT
        ].copy(),
        "debug": True,
    }
    state.career_event_has_activity = False
    night.reset_career_event_result_log()
    night.reset_career_event_session_totals(night.CAREER_ACTIVITY_CASINO_NIGHT)
    return horse_races_screen.start_horse_races_session()


def debug_open_faro():

    state.career_event_entry = {
        "activity_type": night.CAREER_ACTIVITY_NICHE_NIGHT,
        "title": "Niche Game Night",
        "game_ids": night.CAREER_EVENT_GAMES[
            night.CAREER_ACTIVITY_NICHE_NIGHT
        ].copy(),
        "debug": True,
    }

    state.career_event_has_activity = False
    night.reset_career_event_result_log()
    night.reset_career_event_session_totals(night.CAREER_ACTIVITY_NICHE_NIGHT)
    faro_screen.start_faro_session()


def debug_open_five_o_poker():

    saved_night = keep_night_context()
    entered_debug_mode = enter_debug_game_mode()
    state.career_event_entry = {
        "activity_type": night.CAREER_ACTIVITY_NICHE_NIGHT,
        "title": "Niche Game Night",
        "game_ids": night.CAREER_EVENT_GAMES[night.CAREER_ACTIVITY_NICHE_NIGHT].copy(),
        "debug": True,
    }
    state.career_event_has_activity = False
    night.reset_career_event_result_log()
    night.reset_career_event_session_totals(night.CAREER_ACTIVITY_NICHE_NIGHT)
    if five_o_screen.start_five_o_poker_session():
        return True
    # Nothing started (not enough cash). Leave "debug" only if this launcher switched it on:
    # an earlier debug session the player goes back to must stay in "debug" mode.
    if entered_debug_mode:
        end_debug_game_mode()
    restore_night_context(saved_night)   # the night in progress, untouched
    return False


def debug_open_blind_mans_bluff():

    saved_night = keep_night_context()
    entered_debug_mode = enter_debug_game_mode()
    state.career_event_entry = {
        "activity_type": night.CAREER_ACTIVITY_NICHE_NIGHT,
        "title": "Niche Game Night",
        "game_ids": night.CAREER_EVENT_GAMES[night.CAREER_ACTIVITY_NICHE_NIGHT].copy(),
        "debug": True,
    }
    state.career_event_has_activity = False
    night.reset_career_event_result_log()
    night.reset_career_event_session_totals(night.CAREER_ACTIVITY_NICHE_NIGHT)
    if blind_mans_bluff_screen.start_blind_mans_bluff_session():
        return True
    # Nothing started (not enough cash). Leave "debug" only if this launcher switched it on:
    # an earlier debug session the player goes back to must stay in "debug" mode.
    if entered_debug_mode:
        end_debug_game_mode()
    restore_night_context(saved_night)   # the night in progress, untouched
    return False


def debug_open_head_to_head():

    state.career_event_entry = {
        "activity_type": night.CAREER_ACTIVITY_EVENT,
        "title": "Head-to-Head",
        "event_id": "head_to_head_01",
        "debug": True,
    }
    state.career_event_has_activity = False
    head_to_head_screen.start_head_to_head_event()
    state.current_state = state_names.STATE_CAREER_EVENT
    return True


def debug_prepare_poker_night():

    game_ids = (
        night.CAREER_EVENT_GAMES[
            night.CAREER_ACTIVITY_POKER_NIGHT
        ].copy()
    )

    state.career_event_entry = {
        "activity_type": night.CAREER_ACTIVITY_POKER_NIGHT,
        "title": "Poker Night",
        "game_ids": game_ids,
        "high_stakes_game_id": random.choice(
            game_ids
        ) if game_ids else None,
        "debug": True,
    }

    state.career_event_has_activity = False
    night.reset_career_event_result_log()
    night.reset_career_event_session_totals(night.CAREER_ACTIVITY_POKER_NIGHT)


def debug_open_poker_night():

    debug_prepare_poker_night()

    state.current_state = state_names.STATE_CAREER_EVENT_SELECT


def open_debug_poker_npc_select(game_id):

    # Back (no table played) puts the night in progress back as it was.
    state.debug_poker_select_saved_night = keep_night_context()
    debug_prepare_poker_night()
    # Back from the selector (no table played) ends the debug mode, if this switched it on (B22).
    state.debug_poker_select_entered_debug_mode = enter_debug_game_mode()
    state.debug_poker_select_game_id = str(game_id)
    state.debug_poker_selected_ids = make_debug_poker_default_selection(
        NPCS,
        count=4,
    )
    state.current_state = state_names.STATE_DEBUG_POKER_NPC_SELECT


def debug_open_solitaire_challenge(
        challenge_id
):

    state.pending_career_activity_index = None
    state.pending_career_activity_type = None
    state.pending_career_challenge_id = None

    entered_debug_mode = enter_debug_game_mode()

    legacy.game.clear_challenge()
    legacy.game.set_difficulty(
        DEFAULT_DIFFICULTY
    )

    if not legacy.game.set_challenge(
            challenge_id
    ):
        if entered_debug_mode:
            end_debug_game_mode()   # nothing started: leave only the "debug" mode this switched on
        return False

    legacy.game.new_game()

    state.current_state = state_names.STATE_PLAYING

    return True


def debug_set_player_level(
        target_level
):

    target_level = max(
        1,
        min(
            int(target_level),
            max(LEVEL_XP_THRESHOLDS)
        )
    )

    state.player_level = target_level
    state.player_xp = LEVEL_XP_THRESHOLDS.get(
        target_level,
        0
    )
    state.player_xp_to_next = leveling.get_next_level_xp(
        target_level
    )

    leveling.sync_unlocks_for_current_level()


def close_debug_menu():
    """Leave the F10 debug menu for the screen it was opened from (state.debug_previous_state).

    The one way back for both the F10 hotkey (app/loop.py) and the menu's Close button (B59):
    going back to Dead Man's Hand recaptures the mouse that opening the menu released. Without a
    previous screen the menu stays open.
    """

    if state.debug_previous_state is not None:
        state.current_state = state.debug_previous_state
        if state.current_state == state_names.STATE_DEAD_MANS_HAND:
            game_screen.dead_mans_hand_game.capture_mouse()


def debug_end_free_play_sandbox():
    """An F10 launch of a game, night or career screen: end a running Free Play sandbox first (B21).

    Restores the real Career cash/ratings/fans, so later Career saves never write the
    sandbox values. Free Play mode becomes Career mode (like debug_start_next_career_month),
    also as the mode a debug launcher goes back to (state.debug_saved_game_mode), so ending
    a debug night never brings back Free Play mode without its sandbox. The Free Play game
    the debug menu was opened from is over, so Close / F10 go to the Free Play select instead.
    Returns True when a sandbox (or Free Play mode) was ended.
    """

    sandbox_running = state.free_play_snapshot is not None
    free_mode = state.current_game_mode == "free"
    saved_free_mode = state.debug_saved_game_mode == "free"

    if not (sandbox_running or free_mode or saved_free_mode):
        return False

    if sandbox_running or free_mode:
        legacy.finish_free_play_sandbox()

    if free_mode:
        state.current_game_mode = "career"
    if saved_free_mode:
        state.debug_saved_game_mode = "career"

    if sandbox_running:
        state.debug_previous_state = state_names.STATE_FREE_PLAY_SELECT

    return True


def debug_start_next_career_month(save=True):

    if state.current_game_mode == "free":
        legacy.finish_free_play_sandbox()
    state.current_game_mode = "career"
    leaderboard_engine.ensure_career_leaderboard()

    remaining_days = max(
        1,
        len(state.career_current_schedule)
        - state.career_day_of_month
        + 1
    )

    state.career_day += remaining_days
    state.career_month += 1

    if state.career_month > 12:
        state.career_month = 1
        state.career_year += 1

    state.career_day_of_month = 1
    state.career_weekday_index = 0
    state.career_roster_dirty = True  # B18: new date, so the live roster is re-synced

    leaderboard_engine.update_career_leaderboard_ratings()
    legacy.maybe_add_monthly_flavor_news()

    state.career_current_schedule = (
        calendar.build_default_career_schedule()
    )

    if save:
        career_saving.auto_save_career()

def debug_add_career_prospect(prodigy=False):
    if state.current_game_mode == "free":
        legacy.finish_free_play_sandbox()
    state.current_game_mode = "career"
    leaderboard_engine.ensure_career_leaderboard()
    story = add_prospect(state.career_npc_world, state.career_leaderboard_state, PROSPECT_POOL,
                         state.career_year, state.career_month, force_prodigy=prodigy)
    if story:
        state.career_roster_dirty = True  # B18: an NPC joined (the sync below clears it)
        leaderboard_engine.sync_career_npc_runtime_state()
        news_screen.add_career_news(story["headline"], story["body"], story["category"])
        career_saving.auto_save_career()
        show_debug_message("Prodigy added to Career" if prodigy else "Prospect added to Career")
    else:
        show_debug_message("All 160 prospects have joined this Career")
    state.current_state = state_names.STATE_CAREER_HUB
    return bool(story)


def debug_advance_career_year():
    if state.current_game_mode == "free":
        legacy.finish_free_play_sandbox()
    state.current_game_mode = "career"
    leaderboard_engine.ensure_career_leaderboard()
    calendar.reset_career_hub_runtime()
    for _ in range(12):
        debug_start_next_career_month(save=False)
    career_saving.auto_save_career()
    state.current_state = state_names.STATE_CAREER_HUB
