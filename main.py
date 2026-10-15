from runtime_support import bootstrap
bootstrap()

# Dispatch before importing single-player modules or initializing its window.
import sys as _launch_sys
if "--multiplayer" in _launch_sys.argv:
    from multiplayer_launcher import run_multiplayer
    run_multiplayer()
    raise SystemExit(0)

from alien_night import STORY as ALIEN_STORY, new_alien_story, refresh_adventure_schedule
from solitaire_restart import RestartPrompt
solitaire_restart_prompt = RestartPrompt()
from profile_avatar_assets import load_avatar_bank, avatar_options
from career_asset_images import (get_jobfinder_image, get_realestate_image,
                                 get_career_hub_image, get_country_flag_surface)
from career_activities import new_story, normalize_story, start_night, choose_option, reconcile_story_cosmetics
from career_activities_ui import CareerActivityScreen
from cosmetic_assets import CosmeticCatalog, SingleDriftCache
from press_interview import PRESS_INTERVIEW_QUESTION_POOL, select_interview, answer_outcome
from career_session_summary import poker_session_status, night_game_net, track_night_cash, night_cash_total
from rating_unlocks import unlock_ratings, lock_reason, rating_lock_progress
from multiplayer_launcher import MultiplayerLauncher
multiplayer_launcher = MultiplayerLauncher()

from career_event_progress import store_event_progress, restore_event_progress
from career_time_warp import advance_months
from case_opening import new_case_state, normalize_case_state, purchase as purchase_loot_case, award_earned_trophies
from case_opening_ui import CaseOpeningScreen
from arcade_support import (
    ARCADE_COMING_SOON_GAME_IDS,
    ARCADE_MACHINE_NAMES,
    ARCADE_PRIZE_CATALOG,
    ARCADE_TOKEN_PACKAGES,
    award_battle_bosses_tickets,
    award_king_pong_tickets,
    buy_token_package,
    clone_arcade_state,
    get_machine_cost,
    make_default_arcade_state,
    normalize_arcade_state,
    redeem_prize,
    register_battle_bosses_result,
    register_king_pong_result,
    spend_tokens,
)
from bluff_presentation import update_bluff_presentation
from poker_recap import handle_recap_action
from poker_learning import new_learning, normalize_learning
import os
import sys
import time
import copy
import ctypes

from career_hub_controls import CareerHubControls
from npc_personality import personality_summary
from npc_personality_ui import draw_npc_traits

import random

import math
import pygame
import json


from audio import AudioManager
from game import Game, BASE_WIDTH, BASE_HEIGHT

from score_four import ScoreFourGame
from crazy_eights import CrazyEightsGame
from crazy_eights_ui import (
    draw_crazy_eights,
    get_crazy_eights_action,
    ACTION_RETURN as CRAZY_EIGHTS_ACTION_RETURN,
    ACTION_DRAW as CRAZY_EIGHTS_ACTION_DRAW,
    ACTION_CONTINUE as CRAZY_EIGHTS_ACTION_CONTINUE,
    ACTION_CARD as CRAZY_EIGHTS_ACTION_CARD,
    ACTION_SUIT as CRAZY_EIGHTS_ACTION_SUIT,
)
from bango import BangoGame
from cryptid_creatures_ui import CryptidScreen
from cryptid_collection import new_collection, normalize_collection, award_level_packs, reward_battle
from bango_ui import (
    draw_bango,
    get_bango_action,
    ACTION_RETURN as BANGO_ACTION_RETURN,
    ACTION_CALL as BANGO_ACTION_CALL,
    ACTION_CONTINUE as BANGO_ACTION_CONTINUE,
)
from blackjack import BlackjackGame
from king_pong import KingPongGame, KING_PONG_DIFFICULTIES
from battle_bosses import (
    BATTLE_BOSSES_DIFFICULTIES,
    build_battle_bosses_choices,
)
from battle_bosses_game import BattleBossesGame

from texas_holdem import (
    TexasHoldemGame,
)

from texas_holdem_ui import (
    draw_texas_holdem,
    get_texas_holdem_action,
    ACTION_RETURN as HOLDEM_ACTION_RETURN,
    ACTION_FOLD as HOLDEM_ACTION_FOLD,
    ACTION_CHECK_CALL as HOLDEM_ACTION_CHECK_CALL,
    ACTION_BET_RAISE as HOLDEM_ACTION_BET_RAISE,
    ACTION_NEXT_HAND as HOLDEM_ACTION_NEXT_HAND,
    scroll_holdem_log,
    HOLDEM_LOG_RECT,
    holdem_log_history,
    update_holdem_bet_slider,
    drag_holdem_bet_slider,
    stop_holdem_bet_slider_drag,
    get_holdem_bet_amount,
    handle_holdem_panel_click,
    add_holdem_chat_message,
    toggle_holdem_options,
    is_holdem_options_open,
    handle_holdem_options_click,
    draw_holdem_options_overlay,
    is_holdem_auto_deal_enabled,
    is_holdem_table_chat_enabled,
    handle_holdem_manual_bet_click,
    handle_holdem_manual_bet_key,
    clear_holdem_manual_bet,
    get_holdem_npc_delay,
    get_holdem_street_delay,
    get_holdem_next_hand_delay,
    draw_texas_holdem_buy_in,
    get_texas_holdem_buy_in_action,
)

from texas_holdem_chat import (
    generate_npc_action_chat,
    generate_player_action_reaction,
    generate_showdown_chat,
)

from five_card_draw import (
    FiveCardDrawGame,
)

from five_card_draw_ui import (
    draw_five_card_draw,
    draw_five_card_draw_buy_in,
    get_five_card_draw_buy_in_action,
    get_five_card_draw_action,
    get_five_card_draw_bet_amount,
    handle_five_card_draw_bet_preset,
    update_five_card_draw_bet_slider,
    drag_five_card_draw_bet_slider,
    stop_five_card_draw_bet_slider,
    handle_five_card_draw_manual_bet_click,
    handle_five_card_draw_manual_bet_key,
    clear_five_card_draw_manual_bet,
    handle_five_card_draw_card_click,
    handle_five_card_draw_panel_click,
    scroll_five_card_draw_panel,
    get_selected_draw_indexes,
    clear_five_card_draw_selection,
    add_five_card_draw_chat_message,
    reset_five_card_draw_ui_session,
    DRAW_LOG_RECT,
    ACTION_RETURN as DRAW_ACTION_RETURN,
    ACTION_FOLD as DRAW_ACTION_FOLD,
    ACTION_CHECK_CALL as DRAW_ACTION_CHECK_CALL,
    ACTION_BET_RAISE as DRAW_ACTION_BET_RAISE,
    ACTION_DRAW as DRAW_ACTION_DRAW,
    ACTION_NEXT_HAND as DRAW_ACTION_NEXT_HAND,
    ACTION_OPTIONS as DRAW_ACTION_OPTIONS,
)

from seven_card_stud import (
    SevenCardStudGame,
)

from seven_card_stud_ui import (
    draw_seven_card_stud,
    draw_seven_card_stud_buy_in,
    get_seven_card_stud_buy_in_action,
    get_seven_card_stud_action,
    handle_seven_card_stud_panel_click,
    scroll_seven_card_stud_panel,
    add_seven_card_stud_chat_message,
    reset_seven_card_stud_ui_session,
    STUD_LOG_RECT,
    ACTION_RETURN as STUD_ACTION_RETURN,
    ACTION_FOLD as STUD_ACTION_FOLD,
    ACTION_CHECK_CALL as STUD_ACTION_CHECK_CALL,
    ACTION_BET_RAISE as STUD_ACTION_BET_RAISE,
    ACTION_NEXT_HAND as STUD_ACTION_NEXT_HAND,
    ACTION_OPTIONS as STUD_ACTION_OPTIONS,
)

from npc_manager import (
    NPCS,
    BASE_NPCS,
    PROSPECT_POOL,
    get_random_npc,
    get_random_blackjack_dealer,
    get_score_four_opponent_choices,
    get_random_npc_group,
    get_npcs_missing_portraits,
    sync_npc_runtime_state,
)

from roulette import (
    RouletteGame,
    RED_NUMBERS,
)

from roulette_ui import (
    draw_roulette,
    get_roulette_action,
    ACTION_RETURN as ROULETTE_ACTION_RETURN,
    ACTION_SPIN as ROULETTE_ACTION_SPIN,
    ACTION_BET_RED,
    ACTION_BET_BLACK,
    ACTION_BET_ODD,
    ACTION_BET_EVEN,
    ACTION_BET_LOW,
    ACTION_BET_HIGH,
    ACTION_BET_NUMBER_PREFIX,
    ACTION_CLEAR_BETS,
    ACTION_CHIP_10,
    ACTION_CHIP_50,
    ACTION_CHIP_100,
    ACTION_CHIP_500,
    ACTION_BET_DOZEN_1,
    ACTION_BET_DOZEN_2,
    ACTION_BET_DOZEN_3,
    ACTION_BET_COLUMN_1,
    ACTION_BET_COLUMN_2,
    ACTION_BET_COLUMN_3,
)

from horse_races import HorseRaceGame
from horse_races_ui import (
    draw_horse_races,
    get_horse_races_action,
    ACTION_RETURN as HORSE_RACES_ACTION_RETURN,
    ACTION_PLACE_BET as HORSE_RACES_ACTION_PLACE_BET,
    ACTION_CLEAR_BETS as HORSE_RACES_ACTION_CLEAR_BETS,
    ACTION_START_RACE as HORSE_RACES_ACTION_START_RACE,
    ACTION_WIN as HORSE_RACES_ACTION_WIN,
    ACTION_PLACE as HORSE_RACES_ACTION_PLACE,
    ACTION_SHOW as HORSE_RACES_ACTION_SHOW,
    ACTION_CHIP_10 as HORSE_RACES_ACTION_CHIP_10,
    ACTION_CHIP_50 as HORSE_RACES_ACTION_CHIP_50,
    ACTION_CHIP_100 as HORSE_RACES_ACTION_CHIP_100,
    ACTION_CHIP_500 as HORSE_RACES_ACTION_CHIP_500,
    ACTION_HORSE_PREFIX as HORSE_RACES_ACTION_HORSE_PREFIX,
)

from faro import FaroGame
from faro_ui import (
    draw_faro,
    get_faro_action,
    ACTION_RETURN as FARO_ACTION_RETURN,
    ACTION_DEAL as FARO_ACTION_DEAL,
    ACTION_CLEAR_BETS as FARO_ACTION_CLEAR_BETS,
    ACTION_CHIP_10 as FARO_ACTION_CHIP_10,
    ACTION_CHIP_50 as FARO_ACTION_CHIP_50,
    ACTION_CHIP_100 as FARO_ACTION_CHIP_100,
    ACTION_CHIP_500 as FARO_ACTION_CHIP_500,
    ACTION_BET_RANK_PREFIX as FARO_ACTION_BET_RANK_PREFIX,
)

from five_o_poker import FiveOPokerGame
from five_o_poker_ui import (
    draw_five_o_poker,
    get_five_o_action,
    ACTION_RETURN as FIVE_O_ACTION_RETURN,
    ACTION_NEXT_HAND as FIVE_O_ACTION_NEXT_HAND,
    ACTION_CHECK as FIVE_O_ACTION_CHECK,
    ACTION_BET as FIVE_O_ACTION_BET,
    ACTION_CALL as FIVE_O_ACTION_CALL,
    ACTION_FOLD as FIVE_O_ACTION_FOLD,
    ACTION_COLUMN_PREFIX as FIVE_O_ACTION_COLUMN_PREFIX,
)

from blind_mans_bluff import BlindMansBluffGame
from blind_mans_bluff_ui import (
    draw_blind_mans_bluff,
    get_blind_mans_bluff_action,
    get_blind_mans_bluff_bet_amount,
    ACTION_RETURN as BLUFF_ACTION_RETURN,
    ACTION_NEXT_HAND as BLUFF_ACTION_NEXT_HAND,
    ACTION_CHECK as BLUFF_ACTION_CHECK,
    ACTION_BET as BLUFF_ACTION_BET,
    ACTION_RAISE as BLUFF_ACTION_RAISE,
    ACTION_CALL as BLUFF_ACTION_CALL,
    ACTION_FOLD as BLUFF_ACTION_FOLD,
)

from debug_poker_select import (
    draw_debug_poker_npc_select,
    get_debug_poker_select_action,
    make_default_selection as make_debug_poker_default_selection,
    cycle_selection as cycle_debug_poker_selection,
    ACTION_BACK as DEBUG_POKER_ACTION_BACK,
    ACTION_START as DEBUG_POKER_ACTION_START,
    ACTION_RANDOMIZE as DEBUG_POKER_ACTION_RANDOMIZE,
    ACTION_CYCLE as DEBUG_POKER_ACTION_CYCLE,
)

from head_to_head import (
    HeadToHeadRace,
    select_head_to_head_opponents,
)
from head_to_head_ui import (
    draw_head_to_head_selection,
    draw_head_to_head_hud,
    get_selection_action as get_head_to_head_selection_action,
)

from debug_menu import (
    draw_debug_menu,
    get_debug_action,
    show_debug_message,
    ACTION_CAREER_HUB,
    ACTION_CASUAL_CARDS,
    ACTION_POKER_NIGHT,
    ACTION_CASINO_NIGHT,
    ACTION_HEAD_TO_HEAD,
    ACTION_ADVANCE_CAREER_DAY,
    ACTION_NEW_CAREER_MONTH,
    ACTION_ADD_PROSPECT,
    ACTION_ADD_PRODIGY,
    ACTION_CAREER_YEAR,
    ACTION_CHALLENGE_DRAW_3,
    ACTION_CHALLENGE_NO_UNDO,
    ACTION_CHALLENGE_NO_HINTS,
    ACTION_CHALLENGE_ALL_OR_NOTHING,
    ACTION_SCORE_FOUR_SOLO,
    ACTION_SCORE_FOUR_COMPETITIVE,
    ACTION_CRAZY_EIGHTS,
    ACTION_BANGO,
    ACTION_FARO,
    ACTION_FIVE_O_POKER,
    ACTION_BLIND_MANS_BLUFF,
    ACTION_BLACKJACK,
    ACTION_ROULETTE,
    ACTION_HORSE_RACES,
    ACTION_TEXAS_HOLDEM,
    ACTION_FIVE_CARD_DRAW,
    ACTION_SEVEN_CARD_STUD,
    ACTION_ADD_CASH,
    ACTION_ZERO_CASH,
    ACTION_ADD_RATING,
    ACTION_SUB_RATING,
    ACTION_ADD_XP,
    ACTION_LEVEL_3,
    ACTION_LEVEL_6,
    ACTION_LEVEL_10,
    ACTION_LEVEL_MAX,
    ACTION_ACHIEVEMENT_TEST,
    ACTION_CLOSE,
)

from profile import (
    make_default_profile,
    save_profile,
    load_profile,
    profile_exists,
    delete_profile,
    PROFILE_SLOT_COUNT,
)

from career_ratings import (
    RATING_KEYS,
    GAME_RATING_KEYS,
    apply_rating_change,
    boost_npc_overall,
    elo_delta,
    RATING_DISPLAY_NAMES,
    ensure_npc_career_state,
    make_npc_rating_bundle,
    make_player_rating_bundle,
    normalize_rating_bundle,
)

from career_rating_events import (
    record_result,
    record_poker_showdown,
    settle_competitive_result,
    settle_house_result,
    settle_poker_session,
)

from career_npc_world import ensure_career_world, advance_career_world, add_prospect
from career_npc_development import development_stage
from npc_portraits import draw_layered_portrait, register_player_avatar_art

from career_fans import (
    MAX_FANS,
    clamp_fans,
    fan_bonus_for_achievement,
    fan_bonus_for_job,
    fan_bonus_for_residence,
    fan_gain_from_cash_win,
    fan_gain_from_rating_win,
    fan_change_from_autograph_accuracy,
    fan_loss_from_bad_result,
    get_public_appeal_display_name,
)

from achievements import (
    ACHIEVEMENT_DEFINITIONS,
    make_default_achievement_state,
    normalize_achievement_state,
    record_event as record_achievement_event,
    iter_rewards as iter_achievement_rewards,
    get_definition as get_achievement_definition,
    register_optional_cosmetics,
)

from achievements_ui import (
    BACK_RECT as ACHIEVEMENTS_BACK_RECT,
    clamp_scroll as clamp_achievements_scroll,
    draw_achievements_screen,
    draw_achievement_popup,
)

from autograph_event import (
    AutographEvent,
    AUTOGRAPH_CANVAS_RECT,
    AUTOGRAPH_CLEAR_RECT,
    AUTOGRAPH_SUBMIT_RECT,
)

from career_news import (
    build_casual_cards_story,
    build_poker_story,
    build_casino_story,
    build_niche_story,
    build_arcade_story,
    build_monthly_flavor_story,
    build_head_to_head_story,
)

from help_history import HISTORY_HELP_PAGES

from settings import (
    DEFAULT_WINDOW_SIZE,
    RESOLUTION_OPTIONS,
    MENU_BACKGROUNDS,
    FELTS,
    TITLES,
    DEFAULT_UNLOCKED_MENU_BACKGROUNDS,
    DEFAULT_UNLOCKED_FELTS,
    DEFAULT_UNLOCKED_TITLES,
    DEFAULT_SELECTED_MENU_BACKGROUND,
    DEFAULT_SELECTED_FELT,
    DEFAULT_SELECTED_TITLE,
    DEFAULT_PLAYER_NAME,
    DEFAULT_LEVEL,
    DEFAULT_XP,
    DEFAULT_XP_TO_NEXT,
    LEVEL_XP_THRESHOLDS,
    LEVEL_UNLOCKS,
    DIFFICULTY_RULES,
    DEFAULT_DIFFICULTY,
    GAME_UNLOCK_LEVELS,
)

# ==================================================
# Working directory
# ==================================================

# Resource paths were set before imports by runtime_support.bootstrap().

register_optional_cosmetics(
    MENU_BACKGROUNDS,
    FELTS,
    TITLES,
)

# ==================================================
# PYGAME INITIALIZATION
# ==================================================

pygame.display.init()
pygame.font.init()

# ==================================================
# AUDIO
# ==================================================

audio = AudioManager()


# ----------------------------
# Instrumental soundtrack
# ----------------------------

instrumental_tracks = [
    "assets/music/hello.mp3",
    "assets/music/block.mp3",
    "assets/music/rock.mp3",
    "assets/music/rail_trail.mp3",
    "assets/music/rail_trail_pt2.mp3",
    "assets/music/electric.mp3",
    #"assets/music/on_death_and_dying.mp3",
    "assets/music/jay.mp3",
    "assets/music/high_note.mp3",
]

audio.add_playlist(
    "instrumental",
    instrumental_tracks
)


# ----------------------------
# Ambient soundtrack
# ----------------------------

ambient_tracks = [
    "assets/music/ambient_01.mp3",
    "assets/music/ambient_02.mp3",
    "assets/music/ambient_03.mp3",
    "assets/music/ambient_04.mp3",
]

audio.add_playlist(
    "ambient",
    ambient_tracks,
    startup_track="assets/music/ambient_01.mp3"
)


# ----------------------------
# Sound effects
# ----------------------------

audio.load_sound(
    "button_click",
    "assets/sounds/button_click.wav"
)

audio.load_sound(
    "card_draw",
    "assets/sounds/card_draw.wav"
)

audio.load_sound(
    "card_flip",
    "assets/sounds/card_flip.wav"
)

audio.load_sound(
    "poker_check",
    "assets/sounds/check.wav"
)

audio.load_sound(
    "poker_chips_1",
    "assets/sounds/chips_1.wav"
)

audio.load_sound(
    "poker_chips_2",
    "assets/sounds/chips_2.wav"
)

audio.load_sound(
    "poker_chips_3",
    "assets/sounds/chips_3.wav"
)

audio.load_sound(
    "poker_hand_win",
    "assets/sounds/hand_win.wav"
)

# Reused by both Five-O presentation and King Pong point scoring.
audio.load_sound(
    "five_o_column_win",
    "assets/sounds/five_o_column_win.wav"
)

audio.load_sound(
    "five_o_column_loss",
    "assets/sounds/five_o_column_loss.wav"
)

# Battle Bosses SFX are optional while the custom audio is being created.
# Dropping any of these WAVs into assets/sounds automatically activates the
# corresponding gameplay event without making missing work-in-progress audio
# a startup error.
for battle_sound_name, battle_sound_path in (
        ("battle_bosses_ricochet", "assets/sounds/battle_bosses_ricochet.wav"),
        ("battle_bosses_fort_hit", "assets/sounds/battle_bosses_fort_hit.wav"),
        ("battle_bosses_eliminate", "assets/sounds/battle_bosses_eliminate.wav"),
        ("battle_bosses_win", "assets/sounds/battle_bosses_win.wav"),
        ("battle_bosses_loss", "assets/sounds/battle_bosses_loss.wav"),
):
    if os.path.isfile(battle_sound_path):
        try:
            audio.load_sound(battle_sound_name, battle_sound_path)
        except pygame.error:
            pass

audio.load_sound(
    "card_move",
    "assets/sounds/card_move.wav"
)

audio.load_sound(
    "card_shuffle",
    "assets/sounds/card_shuffle.wav"
)

audio.load_sound(
    "startup",
    "assets/sounds/startup.wav"
)

audio.load_sound(
    "celebration_1",
    "assets/sounds/celebration_1.wav"
)

audio.load_sound(
    "celebration_2",
    "assets/sounds/celebration_2.wav"
)

audio.load_sound(
    "celebration_3",
    "assets/sounds/celebration_3.wav"
)

audio.load_sound(
    "celebration_4",
    "assets/sounds/celebration_4.wav"
)

audio.load_sound(
    "celebration_5",
    "assets/sounds/celebration_5.wav"
)

# Dedicated Horse Races music cue. It uses a Sound channel rather than the
# playlist music channel so the player's normal soundtrack can be ducked
# and restored without losing its current track/position.
horse_race_music_sound = None
horse_race_music_channel = None
horse_race_previous_music_volume = None

try:
    if os.path.exists("assets/music/horse_race.mp3"):
        horse_race_music_sound = pygame.mixer.Sound(
            "assets/music/horse_race.mp3"
        )
except (pygame.error, OSError):
    horse_race_music_sound = None


# ========================================================================================
# GAME STATES // CONSTANTS // CAREER CONSTANTS // CAREER STATES // BUILD VERSION
# ========================================================================================

BUILD_VERSION = "0.0.5-dantest"

STATE_SPLASH = "splash"
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_DIFFICULTY = "difficulty"
STATE_OPTIONS = "options"
STATE_CUSTOMIZE = "customize"
STATE_PROFILE = "profile"
STATE_RECAP = "recap"
STATE_WIN = "win"
STATE_LEVEL_UP = "level_up"
STATE_PROFILE_SELECT = "profile_select"
STATE_MODE_SELECT = "mode_select"
STATE_FREE_PLAY_SELECT = "free_play_select"
STATE_CRYPTID_CREATURES = "cryptid_creatures"
STATE_CASE_OPENING = "case_opening"
STATE_HOW_TO_PLAY = "how_to_play"
STATE_ACHIEVEMENTS = "achievements"

# MINIGAME STATE VARIABLE
STATE_SCORE_FOUR = "score_four"
STATE_SCORE_FOUR_MODE_SELECT = "score_four_mode_select"
STATE_CRAZY_EIGHTS = "crazy_eights"
STATE_BANGO = "bango"

STATE_SCORE_FOUR_OPPONENT_SELECT = (
    "score_four_opponent_select"
)
SCORE_FOUR_TIER_DISPLAY_NAMES = {
    "low": "Casual",
    "mid": "Skilled",
    "strong": "Expert",
    "elite": "Master",
}

STATE_BLACKJACK = "blackjack"
STATE_BLACKJACK_BET = "blackjack_bet"

STATE_TEXAS_HOLDEM_BUY_IN = (
    "texas_holdem_buy_in"
)

STATE_TEXAS_HOLDEM = (
    "texas_holdem"
)

STATE_FIVE_CARD_DRAW_BUY_IN = (
    "five_card_draw_buy_in"
)

STATE_FIVE_CARD_DRAW = (
    "five_card_draw"
)

STATE_SEVEN_CARD_STUD_BUY_IN = (
    "seven_card_stud_buy_in"
)

STATE_SEVEN_CARD_STUD = (
    "seven_card_stud"
)

TEXAS_HOLDEM_MIN_BUY_IN = 100
FIVE_CARD_DRAW_MIN_BUY_IN = 100
SEVEN_CARD_STUD_MIN_BUY_IN = 100
FIVE_O_POKER_MIN_BUY_IN = 100
BLIND_MANS_BLUFF_MIN_BUY_IN = 100

STATE_ROULETTE = "roulette"
STATE_HORSE_RACES = "horse_races"
STATE_FARO = "faro"
STATE_FIVE_O_POKER = "five_o_poker"
STATE_BLIND_MANS_BLUFF = "blind_mans_bluff"
STATE_KING_PONG = "king_pong"
STATE_KING_PONG_OPPONENT_SELECT = "king_pong_opponent_select"
STATE_BATTLE_BOSSES_OPPONENT_SELECT = "battle_bosses_opponent_select"
STATE_BATTLE_BOSSES = "battle_bosses"
STATE_ARCADE_TOKEN_EXCHANGE = "arcade_token_exchange"
STATE_ARCADE_PRIZE_COUNTER = "arcade_prize_counter"
STATE_ARCADE_TROPHY_ROOM = "arcade_trophy_room"

STATE_CAREER_EVENT_SUMMARY = (
    "career_event_summary"
)

STATE_CAREER_HUB = "career_hub"
STATE_CAREER_JOBS = "career_jobs"
STATE_CAREER_ACTIVITY = "career_activity"
career_activity_screen = CareerActivityScreen()
STATE_CAREER_REAL_ESTATE = "career_real_estate"
STATE_CAREER_LEADERBOARDS = "career_leaderboards"
STATE_CAREER_NEWS = "career_news"
STATE_CAREER_NEWS = "career_news"
STATE_CAREER_EVENT = "career_event"
STATE_CAREER_EVENT_SELECT = "career_event_select"

STATE_DEBUG_MENU = "debug_menu"
STATE_DEBUG_POKER_NPC_SELECT = "debug_poker_npc_select"

HOW_TO_PLAY_CONTENT = {

    "basics": {
        "title":
            "BASICS",

        "lines": [
            "The goal of Klondike Solitaire is to move all 52 cards to the four foundation piles.",
            "",
            "Each foundation is built upward by suit, beginning with an Ace and ending with a King.",
            "",
            "Cards in the tableau are arranged in descending order while alternating colors.",
            "",
            "Face-down tableau cards are revealed when the card covering them is moved.",
        ],
    },


    "rules": {
        "title":
            "RULES",

        "lines": [
            "TABLEAU",
            "Build downward in alternating colors.",
            "Kings may be moved into empty tableau spaces.",
            "",
            "FOUNDATIONS",
            "Build upward by suit from Ace through King.",
            "",
            "STOCK AND WASTE",
            "Draw cards from the stock into the waste pile.",
            "Only the top waste card may be played.",
            "",
            "You win when all four foundations are complete.",
        ],
    },


    "controls": {
        "title":
            "CONTROLS",

        "lines": [
            "Click a card to select it.",
            "",
            "Drag cards or valid stacks directly to their destination.",
            "",
            "Double-click a face-up card to attempt an automatic move.",
            "",
            "Use Undo to reverse a previous move when the current rules allow it.",
            "",
            "Use Hint to highlight a possible move when hints are available.",
            "",
            "Click the stock pile to draw more cards.",
        ],
    },


    "strategy": {
        "title":
            "STRATEGY",

        "lines": [
            "Prioritize revealing face-down tableau cards whenever possible.",
            "",
            "Avoid filling an empty tableau space unless the King move helps uncover more cards.",
            "",
            "Do not automatically move every card to the foundation if keeping it in the tableau creates useful moves.",
            "",
            "Look through available tableau moves before drawing from the stock.",
            "",
            "Pay attention to which cards become accessible when recycling the stock.",
        ],
    },


    "variants": {
        "title":
            "VARIANTS",

        "lines": [
            "DRAW 1 / TURN 1",
            "One card is drawn from the stock at a time.",
            "",
            "DRAW 3 / TURN 3",
            "Three cards are moved from the stock to the waste at once.",
            "",
            "Different difficulty levels in game may limit stock passes, hints, and undo history.",
            "",
            "Random deals are currently the standard. Verified Solvable deals are temporarily disabled while that generator is being rebuilt.",
            "",
            "Career challenges may use special rules such as No Undo, No Hints, or All or Nothing.",
        ],
    },


    "career": {
        "title":
            "CAREER MODE",

        "lines": [
            "Career Mode lets you play Solitaire+ while progressing your character over time. You can earn rating points, money, fame, and respect from the Solitaire community.",
            "",
            "Play regular rounds and challenge rounds to improve your career rating. Don\'t want to play a challenge round? Days in the calendar can be skipped without consequence!",
            "",
            "Work side jobs to earn bonus cash. Higher-paying jobs are unlocked by improving your rating; employers respect results.",
            "",
            "Overall is the rounded average of your seven game ratings. Wins and losses change only the game you played. Overall determines your main international ranking and job eligibility.",
            "",
            "Rivals age on their own birthdays. Young competitors develop toward varied peaks; veterans decline gently. New prospects enter every few months, with rare prodigies capable of challenging the leaders.",
        ],
    },
}

NPC_PORTRAIT_STYLES = {
    "score_four": {
        "shape": "rect",
        "border_width": 2,
        "padding": 5,
    },

    "blackjack": {
        "shape": "rect",
        "border_width": 2,
        "padding": 5,
    },

    "holdem": {
        "shape": "oval",
        "border_width": 3,
        "padding": 6,
    },
}

# ==================================================
# HELP MENU
# ==================================================

help_expanded_categories = {
    "solitaire": True,
    "poker": False,
    "casual_cards": False,
    "score_four": False,
    "blackjack": False,
    "roulette": False,
    "horse_races": False,
    "niche_games": False,
    "career": False,
}

help_category_rects = {}
help_page_rects = {}

help_current_page = (
    "solitaire_basics"
)

HELP_NAV_PANEL_RECT = pygame.Rect(40, 110, 280, 570)
HELP_CONTENT_RECT = pygame.Rect(345, 110, 980, 570)
HELP_NAV_SCROLL_STEP = 48
HELP_CONTENT_SCROLL_STEP = 42
help_nav_scroll = 0
help_nav_max_scroll = 0
help_content_scroll = 0
help_content_max_scroll = 0
help_history_image_cache = {}

HELP_NAVIGATION = {
    "solitaire": {
        "name": "Solitaire",
        "pages": [
            ("solitaire_basics", "Basics"),
            ("solitaire_rules", "Rules"),
            ("solitaire_controls", "Controls"),
            ("solitaire_strategy", "Strategy"),
            ("solitaire_variants", "Variants"),
        ],
    },

    "poker": {
        "name": "Poker",
        "pages": [
            ("holdem_basics", "Hold'em Basics"),
            ("holdem_controls", "Hold'em Controls"),
            ("draw_basics", "Five-Card Draw"),
            ("draw_controls", "Draw Controls"),
            ("stud_basics", "Seven-Card Stud"),
            ("stud_controls", "Stud Controls"),
        ],
    },

    "casual_cards": {
        "name": "Casual Cards",
        "pages": [
            ("crazy_eights_basics", "Crazy Eights"),
            ("crazy_eights_controls", "Eights Controls"),
            ("bango_basics", "Bango"),
            ("bango_controls", "Bango Controls"),
        ],
    },

    "score_four": {
        "name": "Score-Four",
        "pages": [
            ("score_four_basics", "Basics"),
            ("score_four_strategy", "Strategy"),
        ],
    },

    "blackjack": {
        "name": "Blackjack",
        "pages": [
            ("blackjack_basics", "Basics"),
            ("blackjack_controls", "Controls"),
        ],
    },

    "roulette": {
        "name": "Roulette",
        "pages": [
            ("roulette_basics", "Basics"),
            ("roulette_controls", "Controls"),
            ("roulette_strategy", "Strategy"),
            ("roulette_payouts", "Payouts"),
        ],
    },

    "horse_races": {
        "name": "Horse Races",
        "pages": [
            ("horse_races_basics", "Basics"),
            ("horse_races_betting", "Betting"),
        ],
    },

    "niche_games": {
        "name": "Niche Games",
        "pages": [
            ("faro_basics", "Faro Basics"),
            ("faro_controls", "Faro Controls"),
            ("five_o_basics", "Five-O Poker"),
            ("five_o_controls", "Five-O Controls"),
            ("bluff_basics", "Blind Man's Bluff"),
            ("bluff_controls", "Bluff Controls"),
        ],
    },

    "career": {
        "name": "Career",
        "pages": [
            ("career_basics", "Basics"),
            ("career_progression", "Progression"),
            ("career_money", "Money"),
            ("career_head_to_head", "Head-to-Head"),
        ],
    },
}

HELP_CONTENT = {
    "solitaire_basics": HOW_TO_PLAY_CONTENT[
        "basics"
    ],

    "solitaire_rules": HOW_TO_PLAY_CONTENT[
        "rules"
    ],

    "solitaire_controls": HOW_TO_PLAY_CONTENT[
        "controls"
    ],

    "solitaire_strategy": HOW_TO_PLAY_CONTENT[
        "strategy"
    ],

    "solitaire_variants": HOW_TO_PLAY_CONTENT[
        "variants"
    ],

    "holdem_basics": {
        "title": "Texas Hold'em: Basics",
        "lines": [
            "Each player receives two private hole cards.",
            "",
            "Five community cards are dealt across the flop, turn, and river. Make the best five-card poker hand using any combination of your hole cards and the board.",
            "",
            "The dealer button, small blind, and big blind rotate around the table. Heads-up play uses the standard dealer/small-blind exception.",
            "",
            "Hold'em uses no-limit betting, so legal raises may range from the minimum raise up to all-in.",
        ],
    },

    "holdem_controls": {
        "title": "Texas Hold'em: Controls",
        "lines": [
            "FOLD leaves the current hand.",
            "",
            "CHECK/CALL checks when no wager is owed or calls the current amount when facing a bet.",
            "",
            "BET/RAISE uses the slider, preset buttons, or manual amount field. When raising, the displayed amount is the total raise-to amount.",
            "",
            "The Game Log records betting and showdown details, while Chat shows table conversation. Options controls table speed, auto-deal, and table chat.",
            "",
            "All-ins and side pots are handled automatically.",
        ],
    },

    "draw_basics": {
        "title": "Five-Card Draw: Basics",
        "lines": [
            "Each player receives five private cards.",
            "",
            "After the first betting round, players may discard cards and draw replacements once. A second betting round follows before showdown.",
            "",
            "Players may also stand pat and keep all five cards.",
            "",
            "The best five-card poker hand wins the pot.",
        ],
    },

    "draw_controls": {
        "title": "Five-Card Draw: Controls",
        "lines": [
            "Use FOLD, CHECK/CALL, and BET/RAISE during betting rounds.",
            "",
            "During the draw phase, click cards to mark them for replacement. Selected cards lift visually from the hand.",
            "",
            "Choose DRAW to replace the selected cards. With no cards selected, DRAW stands pat.",
            "",
            "Bet sizing supports the slider, presets, and manual numeric entry just like Hold'em.",
        ],
    },

    "stud_basics": {
        "title": "Seven-Card Stud: Basics",
        "lines": [
            "Seven-Card Stud has no community cards and no dealer blinds.",
            "",
            "Each live player antes. Third Street begins with two cards face-down and one face-up. The lowest exposed card posts the bring-in.",
            "",
            "Fourth, Fifth, and Sixth Streets are dealt face-up. Seventh Street is dealt face-down.",
            "",
            "The strongest exposed hand acts first on later streets. The best five-card hand made from your seven cards wins at showdown.",
        ],
    },

    "stud_controls": {
        "title": "Seven-Card Stud: Controls",
        "lines": [
            "Stud uses fixed-limit betting rather than a free-form wager slider.",
            "",
            "Use FOLD, CHECK/CALL, and BET/RAISE when action reaches you.",
            "",
            "Third and Fourth Street use the small bet. Fifth, Sixth, and Seventh Street use the big bet.",
            "",
            "After a full opening wager, the table allows up to three additional full raises in a betting round.",
        ],
    },

    "crazy_eights_basics": {
        "title": "Crazy Eights: Basics",
        "lines": [
            "Be the first player to get rid of every card in your hand.",
            "",
            "On your turn, play a card that matches either the active suit or the rank of the top discard.",
            "",
            "Eights are wild. After playing an Eight, choose the suit that the next player must follow.",
            "",
            "If you have no legal play, draw one card. A playable drawn card may be played immediately; otherwise your turn ends.",
        ],
    },

    "crazy_eights_controls": {
        "title": "Crazy Eights: Controls",
        "lines": [
            "Playable cards in your hand receive a gold outline.",
            "",
            "Click a highlighted card to play it. Click Draw Card when you have no legal play.",
            "",
            "Playing an Eight opens the suit chooser. Select Clubs, Diamonds, Hearts, or Spades to continue.",
            "",
            "The active-player indicator shows whose turn it is while NPC opponents take their turns automatically.",
        ],
    },

    "bango_basics": {
        "title": "Bango: Basics",
        "lines": [
            "Bango is playing-card Bingo using two standard 52-card decks.",
            "",
            "Each player receives five cards face up from the first deck. The caller draws from a separate second deck and announces the exact card.",
            "",
            "If a called card appears in your five-card layout, that card is turned face down.",
            "",
            "The first player to turn all five cards face down wins and calls BANGO!",
        ],
    },

    "bango_controls": {
        "title": "Bango: Controls",
        "lines": [
            "Click Call Next Card to draw the next card from the caller deck.",
            "",
            "Matching cards are covered automatically for you and the NPC players. The newest called match receives a brief gold outline.",
            "",
            "The Covered counter shows each player's progress toward five marked cards.",
            "",
            "No strategy input is required once the cards are dealt; Bango is a race driven by the caller deck.",
        ],
    },

    "score_four_basics": {
        "title": "Score-Four: Basics",
        "lines": [
            "Use all four numbers to make 24.",
            "",
            "Combine numbers using addition, subtraction, multiplication, and division.",
        ],
    },

    "score_four_strategy": {
        "title": "Score-Four: Strategy",
        "lines": [
            "Look for useful intermediate values such as 6, 8, 12, and 24.",
            "",
            "Division can create fractions, and fractions may be necessary to solve some puzzles.",
        ],
    },

    "roulette_basics": {
        "title": "Roulette: Basics",
        "lines": [
            "Place one or more bets before spinning the wheel.",
            "",
            "The American roulette wheel contains 0, 00, and the numbers 1 through 36.",
            "",
            "You may place chips on individual numbers or use outside bets such as Red, Black, Odd, Even, 1-18, and 19-36.",
            "",
            "Dozen bets cover 1-12, 13-24, or 25-36. Column bets cover one of the three vertical number columns.",
            "",
            "Multiple bets may be active during the same spin. The Total Wager shows how much money is currently at risk.",
        ],
    },

    "roulette_controls": {
        "title": "Roulette: Controls",
        "lines": [
            "Choose a chip value before placing bets.",
            "",
            "Available chip values are $10, $50, $100, and $500.",
            "",
            "Left-click a betting space to place one chip of the selected value.",
            "",
            "Left-click the same space again to add another chip.",
            "",
            "Right-click a betting space to remove one chip of the selected value.",
            "",
            "Use Clear All Bets to remove every placed bet before spinning.",
            "",
            "Press Spin when you are satisfied with your bets. Bets cannot be changed while the wheel is spinning.",
            "",
            "Use Return to go back to Casino Night.",
        ],
    },

    "roulette_strategy": {
        "title": "Roulette: Strategy",
        "lines": [
            "Straight-up number bets offer the largest payout but win much less often than outside bets.",
            "",
            "Red, Black, Odd, Even, 1-18, and 19-36 cover large portions of the wheel but offer smaller payouts.",
            "",
            "Dozens and columns provide a middle ground between straight-up numbers and even-money bets.",
            "",
            "You can combine different bets on the same spin. For example, a number may also be covered by Red, Odd, and a dozen bet.",
            "",
            "Keep an eye on Total Wager. Several small chips can quickly add up to a large portion of your available cash.",
            "",
            "Using smaller chip values allows you to spread bets across more spaces while limiting the amount risked on each one.",
        ],
    },

    "roulette_payouts": {
        "title": "Roulette: Payouts",
        "lines": [
            "STRAIGHT-UP NUMBER",
            "A winning bet on a single number pays 35:1 profit. Your original wager is also returned.",
            "",
            "DOZENS AND COLUMNS",
            "Winning dozen and column bets pay 2:1 profit. Your original wager is also returned.",
            "",
            "EVEN-MONEY BETS",
            "Red, Black, Odd, Even, 1-18, and 19-36 pay 1:1 profit. Your original wager is also returned.",
            "",
            "0 AND 00",
            "The green 0 and 00 do not count as Red, Black, Odd, Even, Low, High, Dozen, or Column results.",
            "",
            "Each active bet is evaluated separately after the spin, so several bets may win or lose on the same result.",
        ],
    },

    "horse_races_basics": {
        "title": "Horse Races: Basics",
        "lines": [
            "Six horses compete in each race. Their listed odds are based on pre-race strength and form, but every race includes enough performance variance for genuine upsets.",
            "",
            "Choose a horse, choose Win, Place, or Show, select a chip value, and place one or more tickets before the race begins.",
            "",
            "The race is animated from start to finish. Front-runners, closers, steady runners, and streaky horses use different pacing curves, so the order can change throughout the race.",
            "",
            "After the finish, winning tickets are paid automatically. Choose Next Race to get a new six-horse field or Return to cash out the session.",
        ],
    },

    "horse_races_betting": {
        "title": "Horse Races: Betting",
        "lines": [
            "WIN pays only if your horse finishes first.",
            "",
            "PLACE pays if your horse finishes first or second. Its payout is lower than the same horse's Win price.",
            "",
            "SHOW pays if your horse finishes in the top three and has the lowest payout of the three bet types.",
            "",
            "You may place multiple tickets on the same race. Each ticket locks in the odds shown when it is placed.",
            "",
            "Use Clear Bets before the race starts to return every unstarted wager to your bankroll. Once the race begins, tickets are final.",
        ],
    },

    "faro_basics": {
        "title": "Faro: Basics",
        "lines": [
            "Faro is played against the bank using a single 52-card shoe and a layout of the thirteen card ranks.",
            "",
            "Place wagers on one or more ranks before dealing the next turn.",
            "",
            "Each turn reveals a Banker card first and a Player card second. The Banker-card rank loses; the Player-card rank wins even money.",
            "",
            "Bets on ranks that do not appear remain on the layout. If both cards have the same rank, the bank takes half of that rank's wager.",
            "",
            "The final unpaired card is revealed as the Case Card and ends the shoe.",
        ],
    },

    "faro_controls": {
        "title": "Faro: Controls",
        "lines": [
            "Choose a chip value, then left-click a rank to add that wager.",
            "",
            "Right-click a rank to remove one selected chip from that wager.",
            "",
            "Clear Bets returns all currently placed wagers to your cash before the next deal.",
            "",
            "Deal Next Turn reveals the Banker and Player cards. Remaining wagers stay on the table until they win, lose, are reduced by a doublet, or you remove them.",
            "",
            "Cash Out returns all surviving wagers and takes you back to Niche Game Night.",
        ],
    },

    "five_o_basics": {
        "title": "Five-O Poker: Basics",
        "lines": [
            "Five-O is heads-up poker played across five hands at the same time.",
            "",
            "Each player begins with five face-up cards in a row. On each turn, draw one card and place it on one of the five columns.",
            "",
            "Every column must receive one card in the current layer before any column can receive another. The fourth card in each five-card hand is hidden from the opponent; the fifth is face up.",
            "",
            "After both players have five complete poker hands, there is one betting round. Compare corresponding columns using normal poker hand rankings.",
            "",
            "Win at least three of the five columns to win the deal. Winning all five is a FIVE-O sweep.",
        ],
    },

    "five_o_controls": {
        "title": "Five-O Poker: Controls",
        "lines": [
            "During construction, your newly drawn card appears in the center. Click any highlighted column that has not yet received a card in the current layer.",
            "",
            "Your opponent places one card after each of your placements. Their fourth card in every column stays face down until showdown.",
            "",
            "The project version uses one compact fixed-wager betting round: CHECK or BET when action begins, then CALL or FOLD if your opponent bets.",
            "",
            "At showdown, WIN / LOSS / TIE labels show the result of each corresponding five-card poker hand.",
        ],
    },

    "bluff_basics": {
        "title": "Blind Man's Bluff: Basics",
        "lines": [
            "Each player receives one card that everyone else can see, but the owner cannot.",
            "",
            "You can see every opponent's forehead card. Your own card remains hidden from you until the hand ends.",
            "",
            "There is one betting round. Use the visible cards and the way opponents bet to judge whether your unseen card may be strongest.",
            "",
            "After betting, the highest card rank wins. Suits do not break ties, so equal high cards split the pot.",
        ],
    },

    "bluff_controls": {
        "title": "Blind Man's Bluff: Controls",
        "lines": [
            "Choose CHECK or BET when action begins. If an opponent bets after you check, choose CALL or FOLD.",
            "",
            "Opponent cards stay visible because that information is the entire game. Your own card back is deliberately never revealed early.",
            "",
            "The project version uses a fixed wager for the single betting round and does not include raises.",
            "",
            "After showdown, use Next Hand to continue the session or Cash Out to return to Niche Game Night or Free Play.",
        ],
    },

    "blackjack_basics": {
        "title": "Blackjack: Basics",
        "lines": [
            "Beat the dealer by finishing closer to 21 without going over.",
            "",
            "Number cards are worth their printed value. Face cards are worth 10. Aces count as 1 or 11, whichever helps the hand without busting.",
            "",
            "A two-card 21 is Blackjack. The dealer reveals the hole card before the result is settled.",
        ],
    },

    "blackjack_controls": {
        "title": "Blackjack: Controls",
        "lines": [
            "HIT takes another card. STAND ends your turn. DOUBLE doubles the wager, deals one final card, and then stands.",
            "",
            "The Next Hand Bet controls are always visible during a hand. Changing them affects the next deal rather than the current wager.",
            "",
            "Cash Out returns to Casino Night or Free Play after the current hand is complete.",
        ],
    },

    "career_basics": {
        "title": "Career: Basics",
        "lines": [
            "Build your career by completing activities on the Career calendar.",
        ],
    },

    "career_progression": {
        "title": "Career: Progression",
        "lines": [
            "Earn XP, increase your level, unlock games, and improve your Career rating.",
        ],
    },

    "career_money": {
        "title": "Career: Money",
        "lines": [
            "Earn cash through Career activities and use it throughout your career.",
        ],
    },

    "career_head_to_head": {
        "title": "Career: Head-to-Head",
        "lines": [
            "Head-to-Head pits you directly against a nearby Career rival in a timed Klondike race.",
            "",
            "Choose from four opponents near your Solitaire Rating. The matchup screen normally includes competitors just above and below you in the rankings.",
            "",
            "Both racers are trying to move all 52 cards to their foundations. Your opponent's progress appears in the race HUD while you play the real Solitaire board.",
            "",
            "Race deals are independently shuffled Draw-1 layouts with checked winning paths. Wins, losses and forfeits change Solitaire ratings. Normal Verified Solvable remains disabled.",
        ],
    },
}

# History pages live in help_history.py so their prose and image/caption data can
# be edited without touching this large orchestration file.
for _history_page_id, _history_page in HISTORY_HELP_PAGES.items():
    _history_category = _history_page.get("category")
    if _history_category in HELP_NAVIGATION:
        _pages = HELP_NAVIGATION[_history_category]["pages"]
        _entry = (_history_page_id, _history_page.get("button", "History"))
        _after_page = _history_page.get("after")
        _inserted = False
        if _after_page:
            for _page_index, (_existing_page_id, _existing_label) in enumerate(_pages):
                if _existing_page_id == _after_page:
                    _pages.insert(_page_index + 1, _entry)
                    _inserted = True
                    break
        if not _inserted:
            _pages.append(_entry)
    HELP_CONTENT[_history_page_id] = {
        "title": _history_page.get("title", "History"),
        "lines": list(_history_page.get("lines", [])),
        "image": _history_page.get("image"),
        "caption": _history_page.get("caption", ""),
        "history_page": True,
    }

STATE_CAREER_LEADERBOARD_BIO = (
    "career_leaderboard_bio"
)

CAREER_BROWSER_HEADER_HEIGHT = 64

CAREER_WEEKDAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
]


CAREER_MONTH_NAMES = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


CAREER_RESIDENCE_NAMES = {
    "dingy_apartment":
        "Dingy Apartment",

    "hippie_commune":
        "Hippie Commune",

    "towers":
        "Tableau Towers",

    "summit":
        "Sorcerer's Summit",

    "heliyacht":
        "Heliyacht",

    "card_castle":
        "Card Castle",
}

CAREER_RESIDENCES = {
    "dingy_apartment": {
        "name":
            "Dingy Apartment",

        "price":
            0,

        "image":
            "assets/career/residences/"
            "dingy_apartment.png",
    },

    "hippie_commune": {
        "name":
            "Hippie Commune",

        "price":
            500,

        "image":
            "assets/career/residences/"
            "hippie_commune.png",
    },

    "towers": {
        "name":
            "Tableau Towers",

        "price":
            1500,

        "image":
            "assets/career/residences/"
            "towers.png",
    },

    "summit": {
        "name":
            "Sorcerer's Summit",

        "price":
            4000,

        "image":
            "assets/career/residences/"
            "summit.png",
    },

    "heliyacht": {
        "name":
            "Heliyacht",

        "price":
            10000,

        "image":
            "assets/career/residences/"
            "heliyacht.png",
    },

    "card_castle": {
        "name":
            "Card Castle",

        "price":
            25000,

        "image":
            "assets/career/residences/"
            "card_castle.png",
    },
}



CAREER_JOB_NAMES = {
    "custodian":
        "Custodian",

    "satellite_repair":
        "Satellite Repair",

    "videographer":
        "Videographer",

    "airline_pilot":
        "Airline Pilot",

    "spiritual_guru":
        "Spiritual Guru",

    "solitaire_pensioner":
        "Solitaire Pensioner",
}

CAREER_JOBS = {
    "custodian": {
        "name": "Custodian",
        "required_rating": 0,
        "pay": 75,
        "image":
            "assets/career/jobs/"
            "custodian.png",
    },

    "satellite_repair": {
        "name": "Satellite Repair",
        "required_rating": 1200,
        "pay": 125,
        "image":
            "assets/career/jobs/"
            "satellite_repair.png",
    },

    "videographer": {
        "name": "Videographer",
        "required_rating": 1500,
        "pay": 200,
        "image":
            "assets/career/jobs/"
            "videographer.png",
    },

    "airline_pilot": {
        "name": "Airline Pilot",
        "required_rating": 1900,
        "pay": 300,
        "image":
            "assets/career/jobs/"
            "airline_pilot.png",
    },

    "spiritual_guru": {
        "name": "Spiritual Guru",
        "required_rating": 2000,
        "pay": 450,
        "image":
            "assets/career/jobs/"
            "spiritual_guru.png",
    },

    "solitaire_pensioner": {
        "name": "Solitaire Pensioner",
        "required_rating": 2500,
        "pay": 650,
        "image":
            "assets/career/jobs/"
            "solitaire_pensioner.png",
    },
}

TRAINING_RATING_REWARDS = {

    "card_bingo": {
        "loss": 20,
        "win": 35,
    },

    "trash": {
        "loss": 20,
        "win": 35,
    },

    "score_four": {
        "complete": 60,
    },

    "crazy_eights": {
        "loss": 45,
        "win": 60,
    },

    "cassino": {
        "loss": 60,
        "win": 80,
    },

    "piquet": {
        "loss": 90,
        "win": 100,
    },

    "blackjack": {
        0: 10,
        1: 25,
        2: 35,
        3: 45,
    },
    "faro": {
        "bad_session": 25,
        "break_even": 40,
        "profit": 55,
        "strong_profit": 70,
    },
    "five_o_poker": {
        "loss": 25,
        "break_even": 40,
        "profit": 70,
        "five_o": 95,
    },
    "blind_mans_bluff": {
        "loss": 20,
        "break_even": 35,
        "profit": 60,
    },
}


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

TRAINING_GAMES = {
    "card_bingo": {
        "name": "Card Bingo",
        "category": "Quick",
    },

    "trash": {
        "name": "Trash",
        "category": "Quick",
    },

    "score_four": {
        "name": "Score-Four",
        "category": "Quick",
    },
}

from npc_portrait_ui import (draw_portrait as draw_framed_npc_portrait,
                            get_npc_initials)

def _build_career_event_summary():

    global career_event_summary_title
    global career_event_summary_lines

    career_event_summary_title = (
        "EVENT COMPLETE"
    )

    career_event_summary_lines = []

    # ==================================================
    # No event data
    # ==================================================

    if career_event_entry is None:

        career_event_summary_lines = [
            "Event completed."
        ]

        return

    activity_type = (
        career_event_entry.get(
            "activity_type"
        )
    )

    event_name = (
        CAREER_EVENT_NAMES.get(
            activity_type,
            "Event"
        )
    )

    career_event_summary_title = (
        f"{event_name.upper()} COMPLETE"
    )

    if activity_type == CAREER_ACTIVITY_CASINO_NIGHT:
        blackjack_night_net = night_cash_total(globals(), "blackjack", blackjack_session_net)
        roulette_night_net = night_cash_total(globals(), "roulette", roulette_session_net)
        horse_races_night_net = night_cash_total(globals(), "horse_races", horse_races_session_net)

        career_event_summary_title = (
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

        career_event_summary_lines = [
            blackjack_text,
            roulette_text,
            horse_races_text,
            f"Total: ${blackjack_night_net + roulette_night_net + horse_races_night_net:+,}",
            f"Blackjack rating: {blackjack_session_rating_change:+d}",
            f"Current Cash: ${career_cash:,}",
            f"Current Fans: {career_fans:,}",
        ]
        return

    # ==================================================
    # Casual Cards
    # ==================================================

    if (
            activity_type
            == CAREER_ACTIVITY_CASUAL_CARDS
    ):

        career_event_summary_lines = [
            "Casual Cards completed.",
            f"Current Rating: {career_rating:,}",
            f"Current Fans: {career_fans:,}",
        ]

        return

    # ==================================================
    # Poker Night
    # ==================================================

    if (
            activity_type
            == CAREER_ACTIVITY_POKER_NIGHT
    ):

        career_event_summary_lines = [
            "Poker Night completed.",
            f"Current Cash: ${career_cash:,}",
            f"Current Rating: {career_rating:,}",
            f"Current Fans: {career_fans:,}",
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

        faro_text = _session_money_line("Faro", night_cash_total(globals(), "faro", night_game_net(career_event_result_log, "faro", faro_session_net)))
        five_o_text = _session_money_line("Five-O Poker", night_cash_total(globals(), "five_o_poker", night_game_net(career_event_result_log, "five_o_poker", five_o_poker_session_net)))
        bluff_text = _session_money_line("Blind Man's Bluff", night_cash_total(globals(), "blind_mans_bluff", night_game_net(career_event_result_log, "blind_mans_bluff", blind_mans_bluff_session_net)))
        career_event_summary_lines = [
            "Niche Game Night completed.",
            faro_text,
            five_o_text,
            bluff_text,
            f"Current Cash: ${career_cash:,}",
            f"Current Rating: {career_rating:,}",
            f"Current Fans: {career_fans:,}",
        ]

        return

    # ==================================================
    # Arcade Night
    # ==================================================

    if (
            activity_type
            == CAREER_ACTIVITY_ARCADE_NIGHT
    ):

        starting_tokens = int(globals().get("career_event_start_arcade_tokens", arcade_state.get("tokens", 0)))
        starting_tickets = int(globals().get("career_event_start_arcade_tickets", arcade_state.get("tickets", 0)))
        token_delta = int(arcade_state.get("tokens", 0)) - starting_tokens
        ticket_delta = int(arcade_state.get("tickets", 0)) - starting_tickets

        def _format_signed(value, prefix=""):
            sign = "+" if value >= 0 else "-"
            return f"{sign}{prefix}{abs(int(value)):,}"

        career_event_summary_lines = [
            "Arcade Night completed.",
            f"Tokens: {int(arcade_state.get('tokens', 0)):,} ({_format_signed(token_delta)})",
            f"Tickets: {int(arcade_state.get('tickets', 0)):,} ({_format_signed(ticket_delta)})",
            f"Tokens spent tonight: {int(globals().get('arcade_night_tokens_spent', 0)):,}",
            f"Tickets won tonight: +{int(globals().get('arcade_night_tickets_won', 0)):,}",
            f"Current Cash: ${career_cash:,}",
            f"Current Fans: {career_fans:,}",
        ]

        return

    # ==================================================
    # Generic fallback
    # ==================================================

    career_event_summary_lines = [
        f"{event_name} completed."
    ]

def build_career_event_summary():
    global career_event_summary_lines
    _build_career_event_summary()
    lines = [line for line in career_event_summary_lines if not line.startswith(("Current Rating:", "Current Fans:", "Blackjack rating:"))]
    delta = int(round(float(career_rating) - globals().get("career_event_start_global", float(career_rating))))
    lines.append(f"Global Rating: {round(career_rating):,} ({delta:+d})")
    changes = []
    for key in ("strategy", "poker", "casino"):
        diff = int(round(float(career_ratings[key]) - globals().get("career_event_start_"+key, float(career_ratings[key]))))
        if diff: changes.append(f"{key.title()} {diff:+d}")
    if changes: lines.append("  |  ".join(changes))
    fans = career_fans - globals().get("career_event_start_fans", career_fans)
    lines.append(f"Fans: {career_fans:,} ({fans:+d})")
    if globals().get("career_event_entry") and career_event_entry.get("activity_type") in (
            CAREER_ACTIVITY_CASUAL_CARDS, CAREER_ACTIVITY_POKER_NIGHT,
            CAREER_ACTIVITY_CASINO_NIGHT, CAREER_ACTIVITY_NICHE_NIGHT,
            globals().get("CAREER_ACTIVITY_ARCADE_NIGHT", "arcade_night")):
        cash_change = int(career_cash - globals().get("career_event_start_cash", career_cash))
        xp_change = max(0, int(player_xp - globals().get("career_event_start_xp", player_xp)))
        sign = "+" if cash_change >= 0 else "-"
        lines.append(f"Night cash: {sign}${abs(cash_change):,}  |  XP earned: +{xp_change:,}")
    career_event_summary_lines = lines


def get_poker_starting_stack():
    if career_cash <= 2000:
        return max(
            0,
            career_cash
        )

    return round(
        career_cash / 1000
    ) * 1000

def get_poker_ante(
        starting_stack,
        high_stakes=False
):
    if high_stakes:
        percentage = 0.05

    else:
        percentage = 0.01

    return max(
        1,
        round(
            starting_stack
            * percentage
        )
    )

def get_unlocked_games_for_event(
        activity_type
):
    game_ids = (
        CAREER_EVENT_GAMES.get(
            activity_type,
            []
        )
    )

    return [
        game_id
        for game_id in game_ids
        if is_game_unlocked(
            game_id
        )
    ]

def get_career_leaderboard_total_pages(
        entries_per_page=20,
        rating_key=None
):
    leaderboard = (
        get_career_leaderboard(
            rating_key=rating_key
        )
    )

    return max(
        1,
        (
            len(leaderboard)
            + entries_per_page
            - 1
        )
        // entries_per_page
    )

def refresh_future_work_tasks():

    for entry in career_current_schedule:

        # Ignore past days.
        if (
            entry.get(
                "day_number",
                0
            )
            < career_day_of_month
        ):
            continue

        # Only update work days.
        if (
            entry.get(
                "activity_type"
            )
            != CAREER_ACTIVITY_WORK
        ):
            continue

        # Reroll a task using the
        # player's NEW current job.
        entry[
            "title"
        ] = get_career_work_activity_name()

def get_career_month_name():
    if (
        1
        <= career_month
        <= 12
    ):
        return (
            CAREER_MONTH_NAMES[
                career_month
            ]
        )

    return "Unknown"

def load_career_leaderboard_players():
    # One in-place roster feeds rankings, normal game selectors and F10.
    return NPCS


def get_career_weekday_name():
    if (
        0
        <= career_weekday_index
        < len(
            CAREER_WEEKDAY_NAMES
        )
    ):
        return (
            CAREER_WEEKDAY_NAMES[
                career_weekday_index
            ]
        )

    return "Unknown"

def get_career_residence_name():
    return (
        CAREER_RESIDENCE_NAMES.get(
            career_residence,
            career_residence
        )
    )


def get_career_job_name():
    return (
        CAREER_JOB_NAMES.get(
            career_job,
            career_job
        )
    )


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

def get_career_news_preview(
        count=2
):

    ensure_career_news()

    return (
        career_news_items[
            :count
        ]
    )

def get_career_work_activity_name():

    activities = (
        CAREER_WORK_ACTIVITIES.get(
            career_job
        )
    )

    if not activities:
        return "Go to Work"

    return random.choice(
        activities
    )

def get_current_career_activity():

    for entry in career_current_schedule:

        if (
            entry.get(
                "day_number"
            )
            == career_day_of_month
        ):
            return entry

    return None

def get_current_career_activity_index():

    for index, entry in enumerate(
        career_current_schedule
    ):

        if (
            entry.get(
                "day_number"
            )
            == career_day_of_month
        ):
            return index

    return None

def auto_save_career():

    if guest_mode:
        return

    if current_profile_slot is None:
        return

    saved = save_profile(
        build_profile_save_data(),
        current_profile_slot
    )
    if saved is False:
        career_hub_controls.show_message(
            "Save file locked: progress kept in a recovery save. Close any other game instance.",
            pygame.time.get_ticks(), duration=8000
        )


def advance_career_day(
        completed=True,
        save_after=True
):
    global career_day
    global career_day_of_month
    global career_weekday_index
    global career_month
    global career_year
    global career_current_schedule
    global career_completed_days

    # ==================================================
    # Record current day
    # ==================================================

    current_index = (
        get_current_career_activity_index()
    )

    if current_index is not None:

        current_entry = (
            career_current_schedule[
                current_index
            ]
        )

        current_entry[
            "completed"
        ] = completed

        career_completed_days.append(
            {
                "year": career_year,
                "month": career_month,
                "day": career_day_of_month,
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

    career_day += 1

    career_day_of_month += 1

    career_weekday_index += 1

    if career_weekday_index >= 5:
        career_weekday_index = 0

    # ==================================================
    # End of current 15-day calendar block
    # ==================================================

    if (
            career_day_of_month
            > len(
        career_current_schedule
    )
    ):
        career_month += 1

        if career_month > 12:
            career_month = 1
            career_year += 1

        career_day_of_month = 1
        career_weekday_index = 0

        # Update the competitive world
        # once per new Career month.
        update_career_leaderboard_ratings()
        maybe_add_monthly_flavor_news()

        career_current_schedule = (
            build_default_career_schedule()
        )

    if save_after:
        auto_save_career()

def start_career_activity(work=False):
    global current_state
    entry = career_current_schedule[career_day_of_month - 1]
    alien = entry.get("event_id") == "alien_night"
    kind = "alien" if alien else "bigfoot"
    story = career_alien_story if alien else career_bigfoot_story
    if entry.get("career_activity", {}).get("kind") != kind or (entry["career_activity"].get("version") != 2 and not entry["career_activity"].get("claimed")):
        entry["career_activity"] = start_night(story, data=ALIEN_STORY if alien else None)
    current_state = STATE_CAREER_ACTIVITY
    auto_save_career()


def handle_career_activity(action):
    global current_state, career_cash
    state = career_current_schedule[career_day_of_month - 1]["career_activity"]
    if state["claimed"]:
        if action == "continue":
            advance_career_day(completed=True)
            current_state = STATE_CAREER_HUB
        return
    if isinstance(action, tuple) and action[0] == "choice":
        alien = state.get("kind") == "alien"
        story = career_alien_story if alien else career_bigfoot_story
        receipt = choose_option(story, state, action[1], career_cash, data=ALIEN_STORY if alien else None)
        if receipt is not None:
            career_cash += receipt["cash"]
            state["fan_change"] = award_career_fans(receipt["fans"], "Alien Night" if alien else "Bigfoot Night") if receipt["fans"] else 0
            reconcile_story_cosmetics(story, unlocked_menu_backgrounds, unlocked_felts, unlocked_titles, data=ALIEN_STORY if alien else None)
            refresh_adventure_schedule(career_current_schedule, career_bigfoot_story, career_alien_story, career_day_of_month)
            auto_save_career()


def complete_career_work_day():
    global career_cash

    job_data = CAREER_JOBS.get(
        career_job,
        CAREER_JOBS[
            "custodian"
        ]
    )

    pay = job_data.get(
        "pay",
        0
    )

    # A pre-removal shift may already have paid out on this calendar entry.
    legacy_shift = career_current_schedule[career_day_of_month - 1].get("career_activity", {})
    if legacy_shift.get("kind") == "work" and legacy_shift.get("claimed"):
        pay = 0

    career_cash += pay

    advance_career_day(
        completed=True
    )

    return pay

def skip_career_day():
    reset_career_hub_runtime()
    advance_career_day(completed=False)


def reset_career_hub_runtime():
    """Clear calendar/event selections before advancing or loading a profile."""
    global pending_career_activity_index, pending_career_activity_type
    global pending_career_challenge_id, career_event_entry
    global career_event_has_activity, career_event_summary_title
    global career_event_summary_lines, career_news_page, career_leaderboard_page
    pending_career_activity_index = None
    pending_career_activity_type = None
    pending_career_challenge_id = None
    career_event_entry = None
    career_event_has_activity = False
    career_event_summary_title = ""
    career_event_summary_lines = []
    career_news_page = 0
    career_leaderboard_page = 0
    career_hub_controls.reset()
    game.clear_challenge()


def skip_to_selected_career_day():
    ensure_career_schedule()
    skipped = career_hub_controls.days_to_skip(
        career_current_schedule, career_day_of_month
    )
    if not skipped:
        return
    reset_career_hub_runtime()
    # Use the existing calendar bookkeeping, with one save after the whole jump.
    # The selected day stays unplayed. Skipped activities grant no rewards.
    for _ in range(skipped):
        advance_career_day(completed=False, save_after=False)
    auto_save_career()
    career_hub_controls.show_message(
        f"Skipped {skipped} day{'s' if skipped != 1 else ''}. "
        f"Day {career_day_of_month} is ready to play.", pygame.time.get_ticks()
    )


def time_warp_career(months):
    ensure_career_schedule()
    reset_career_hub_runtime()
    skipped=advance_months(months,lambda:(career_year,career_month,career_day_of_month),advance_career_day)
    auto_save_career()
    career_hub_controls.show_message(f"Time Warp: skipped {months} month(s), {skipped} days.",pygame.time.get_ticks(),duration=4000)


def get_ordinal_day(number):
    try:
        number = int(number)
    except (TypeError, ValueError):
        return str(number)

    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def get_career_day_entry(day_number):
    for entry in career_current_schedule:
        if entry.get("day_number") == day_number:
            return entry
    return None


def start_career_cases():
    global current_state, current_game_mode
    current_game_mode = "career"
    award_earned_trophies(case_collection_state, achievement_state)
    case_screen.enter(case_collection_state, career_cash, buy_case_for_screen, career_residence)
    current_state = STATE_CASE_OPENING


def buy_case_for_screen(case_id):
    global career_cash, career_rating, career_fans
    if current_game_mode == "free":
        return purchase_loot_case(case_screen.state, case_id, case_screen.wallet)
    previous = (copy.deepcopy(case_collection_state), career_cash, copy.deepcopy(career_ratings), career_rating, career_fans, set(unlocked_felts))
    try:
        receipt, career_cash = purchase_loot_case(case_collection_state, case_id, career_cash)
        if receipt["kind"] == "rating":
            receipt["amount"] = apply_rating_change(career_ratings, receipt["game"], receipt["amount"])
            career_rating = career_ratings["overall"]
        elif receipt["kind"] == "fans":
            actual = clamp_fans(career_fans + receipt["amount"])
            receipt["amount"] = actual - career_fans
            career_fans = actual
        elif receipt["kind"] == "cosmetic":
            unlocked_felts.add("f_case_" + receipt["item_id"])
        auto_save_career()
        return receipt, career_cash
    except Exception:
        old_state, career_cash, old_ratings, career_rating, career_fans, old_felts = previous
        case_collection_state.clear(); case_collection_state.update(old_state)
        career_ratings.clear(); career_ratings.update(old_ratings)
        unlocked_felts.clear(); unlocked_felts.update(old_felts)
        raise


def start_career_cryptid():
    global current_state, current_game_mode
    current_game_mode='career'
    cryptid_screen.enter_career(NPCS,cryptid_collection_state,auto_save_career,settle_career_cryptid,
                                temporary=globals().get("guest_mode",False) or globals().get("current_profile_slot",1) is None)
    current_state=STATE_CRYPTID_CREATURES


def leave_career_cryptid():
    global current_state
    if not cryptid_screen.claim_result():return False
    try:auto_save_career()
    except OSError:
        cryptid_screen.notice='Could not save. Check the saves folder and retry Return.'
        cryptid_screen.collection_view.message=cryptid_screen.notice
        return False
    current_state=STATE_CAREER_HUB
    return True


def settle_career_cryptid(serial,winner):
    global player_xp,player_level,player_xp_to_next
    previous=copy.deepcopy(cryptid_collection_state)
    previous_progress=(player_xp,player_level,player_xp_to_next,list(level_up_queue))
    previous_cosmetics={name:set(globals()[name]) for name in ('unlocked_menu_backgrounds','unlocked_felts','unlocked_titles') if name in globals()}
    try:
        result=reward_battle(cryptid_collection_state,serial,winner)
        if result:
            progression=add_player_xp(result['xp'])
            level_up_queue.extend(progression['level_up_screens'])
            auto_save_career()
        return result
    except OSError:
        cryptid_collection_state.clear();cryptid_collection_state.update(previous)
        player_xp,player_level,player_xp_to_next,queued=previous_progress
        level_up_queue[:]=queued
        for name,values in previous_cosmetics.items():
            globals()[name].clear();globals()[name].update(values)
        raise


def save_career_from_hub():
    if guest_mode or current_profile_slot is None:
        career_hub_controls.show_message(
            "Guest progress is temporary. Choose a profile to save.",
            pygame.time.get_ticks()
        )
        return True
    try:
        auto_save_career()
    except OSError:
        career_hub_controls.show_message(
            "Could not save. Check the saves folder and try again.",
            pygame.time.get_ticks()
        )
        return False
    career_hub_controls.show_message(
        f"Profile saved to slot {current_profile_slot}.",
        pygame.time.get_ticks(),
        duration=1500,
        fade_ms=550
    )
    return True


def begin_career_profile_switch():
    global profile_switch_snapshot, profile_select_return_state
    global profile_name_active, profile_country_active, profile_age_active
    global profile_hometown_active, profile_bio_active
    global gender_dropdown_open, favorite_suit_dropdown_open, profile_message
    global pending_profile_slot, profile_creation_mode
    global confirm_delete_profile, profile_delete_slot, current_state
    if not save_career_from_hub():
        return
    # A snapshot lets Back restore even a guest or an abandoned empty slot.
    profile_switch_snapshot = (
        current_profile_slot, guest_mode, copy.deepcopy(build_profile_save_data())
    )
    profile_select_return_state = STATE_CAREER_HUB
    profile_name_active = False
    profile_country_active = False
    profile_age_active = False
    profile_hometown_active = False
    profile_bio_active = False
    gender_dropdown_open = False
    favorite_suit_dropdown_open = False
    profile_message = ""
    pending_profile_slot = None
    profile_creation_mode = False
    confirm_delete_profile = False
    profile_delete_slot = None
    current_state = STATE_PROFILE_SELECT


def finish_profile_selection():
    global current_state, current_game_mode, profile_select_return_state
    global profile_return_state, profile_switch_snapshot
    global profile_name_active, profile_country_active, profile_age_active
    global profile_hometown_active, profile_bio_active
    global gender_dropdown_open, favorite_suit_dropdown_open
    destination = profile_select_return_state
    profile_select_return_state = STATE_MENU
    profile_switch_snapshot = None
    profile_name_active = False
    profile_country_active = False
    profile_age_active = False
    profile_hometown_active = False
    profile_bio_active = False
    gender_dropdown_open = False
    favorite_suit_dropdown_open = False
    if destination == STATE_CAREER_HUB:
        reset_career_hub_runtime()
        current_game_mode = "career"
        ensure_career_schedule()
        ensure_career_leaderboard()
        ensure_career_news()
        auto_save_career()
    profile_return_state = destination
    current_state = destination


def cancel_career_profile_switch():
    global current_profile_slot, guest_mode, profile_creation_mode
    global pending_profile_slot, profile_message
    if profile_switch_snapshot is not None:
        slot, was_guest, data = profile_switch_snapshot
        current_profile_slot = slot
        guest_mode = was_guest
        apply_profile_save_data(copy.deepcopy(data))
        sync_unlocks_for_current_level()
    profile_creation_mode = False
    pending_profile_slot = None
    profile_message = ""
    finish_profile_selection()


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
        cycle = list(CAREER_CHALLENGES)
        random.shuffle(cycle)
        monthly_challenges.extend(cycle)
    monthly_challenges = monthly_challenges[:6]

    monthly_card_events = []
    for _half in range(2):
        # Each half-month now features one of every themed night: Casual
        # Cards, Poker Night, Casino Night, Niche Game Night, and Arcade Night.
        half_events = [
            CAREER_ACTIVITY_CASUAL_CARDS,
            CAREER_ACTIVITY_POKER_NIGHT,
            CAREER_ACTIVITY_CASINO_NIGHT,
            CAREER_ACTIVITY_NICHE_NIGHT,
            CAREER_ACTIVITY_ARCADE_NIGHT,
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
            CAREER_ACTIVITY_ROUND,
            "card",
            CAREER_ACTIVITY_WORK,
            "card",
            CAREER_ACTIVITY_CHALLENGE,
        ),
        (
            CAREER_ACTIVITY_EVENT,
            "card",
            CAREER_ACTIVITY_CHALLENGE,
            CAREER_ACTIVITY_WORK,
            CAREER_ACTIVITY_ROUND,
        ),
        (
            "card",
            CAREER_ACTIVITY_WORK,
            CAREER_ACTIVITY_CHALLENGE,
            "card",
            CAREER_ACTIVITY_EVENT,
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

            if activity_type == CAREER_ACTIVITY_ROUND:
                entry["title"] = "Play Solitaire"

            elif activity_type == CAREER_ACTIVITY_WORK:
                entry["title"] = get_career_work_activity_name()

            elif activity_type == CAREER_ACTIVITY_CHALLENGE:
                challenge = monthly_challenges[challenge_index]
                challenge_index += 1
                entry["title"] = "Challenge Round"
                entry["challenge_id"] = challenge["id"]
                entry["challenge_name"] = challenge["name"]

            elif activity_type == CAREER_ACTIVITY_EVENT:
                event_data = monthly_public_events[public_event_index]
                public_event_index += 1
                entry["title"] = event_data["title"]
                entry["event_id"] = event_data["event_id"]

            elif activity_type in (
                    CAREER_ACTIVITY_CASUAL_CARDS,
                    CAREER_ACTIVITY_POKER_NIGHT,
                    CAREER_ACTIVITY_CASINO_NIGHT,
                    CAREER_ACTIVITY_NICHE_NIGHT,
                    CAREER_ACTIVITY_ARCADE_NIGHT
            ):
                entry["title"] = CAREER_EVENT_NAMES[activity_type]
                entry["game_ids"] = CAREER_EVENT_GAMES[activity_type].copy()

                if activity_type == CAREER_ACTIVITY_POKER_NIGHT:
                    entry["high_stakes_game_id"] = random.choice(
                        entry["game_ids"]
                    ) if entry["game_ids"] else None

            schedule.append(entry)

    refresh_adventure_schedule(schedule, career_bigfoot_story, career_alien_story)
    return schedule

def ensure_career_schedule():
    global career_current_schedule

    if not career_current_schedule:
        career_current_schedule = build_default_career_schedule()
        return

    # Migrate existing 15-day saves in place. Keep the player's current first
    # half intact and append a freshly generated days 16-30 second half.
    if len(career_current_schedule) == 15:
        second_half = build_default_career_schedule()[15:30]
        career_current_schedule.extend(second_half)

def add_career_news(
        headline,
        body,
        category="general",
        *, year=None, month=None
):
    news_item = {
        "headline":
            headline,

        "body":
            body,

        "category":
            category,

        "month": career_month if month is None else month,

        "year": career_year if year is None else year,

        "career_day":
            career_day,
    }

    career_news_items.insert(
        0,
        news_item
    )

    # Don't let saves grow forever.
    career_news_items[:] = (
        career_news_items[:50]
    )

def get_career_news_date(
        item
):
    month_names = [
        "",
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    month = item.get(
        "month",
        1
    )

    year = item.get(
        "year",
        2026
    )

    if (
        month < 1
        or month > 12
    ):
        month = 1

    return (
        f"{month_names[month]} "
        f"{year}"
    )

def ensure_career_news():

    if career_news_items:
        return

    add_career_news(
        "NEW COMPETITOR JOINS SOLITAIRE CIRCUIT",
        (
            f"{player_name} has officially entered "
            f"the international competitive Solitaire scene. "
            f"Industry observers remain unsure what to expect."
        ),
        "career"
    )



def maybe_add_monthly_flavor_news():
    if random.random() > 0.72:
        return False

    npc_names = [
        npc.get("name", "")
        for npc in CAREER_LEADERBOARD_PLAYERS
        if isinstance(npc, dict)
    ]
    headline, body, category = build_monthly_flavor_story(npc_names)
    add_career_news(headline, body, category)
    return True


def reset_career_event_result_log():
    global career_event_result_log
    global career_event_news_posted
    career_event_result_log = []
    career_event_news_posted = False


def record_career_event_result(game_id, won=None, **details):
    fan_impact = details.pop("fan_impact", True)
    entry = {
        "game_id": game_id,
        "won": won,
    }
    entry.update(details)
    career_event_result_log.append(entry)

    # Career popularity can move in both directions now. Arcade machines use
    # their own ticket economy, so their results can explicitly opt out.
    if current_game_mode == "career" and won is False and fan_impact:
        net_value = details.get("net", 0)
        try:
            net_loss = max(0, -int(net_value))
        except (TypeError, ValueError):
            net_loss = 0
        lose_fans_for_bad_result(
            f"Poor {FREE_PLAY_GAME_NAMES.get(game_id, game_id.replace('_', ' ').title())} result",
            net_loss=net_loss,
            severity=1.0,
        )


def reset_career_event_session_totals(activity_type):
    global texas_holdem_session_net
    global five_card_draw_session_net
    global seven_card_stud_session_net
    global blackjack_session_net
    global blackjack_session_rating_change
    global roulette_session_net
    global horse_races_session_net
    global horse_races_last_rewarded_races
    global faro_session_net
    global five_o_poker_session_net
    global blind_mans_bluff_session_net
    global arcade_night_tokens_spent
    global arcade_night_tickets_won

    if activity_type == CAREER_ACTIVITY_POKER_NIGHT:
        texas_holdem_session_net = 0
        five_card_draw_session_net = 0
        seven_card_stud_session_net = 0

    elif activity_type == CAREER_ACTIVITY_CASINO_NIGHT:
        blackjack_session_net = 0
        blackjack_session_rating_change = 0
        roulette_session_net = 0
        horse_races_session_net = 0
        horse_races_last_rewarded_races = 0

    elif activity_type == CAREER_ACTIVITY_NICHE_NIGHT:
        faro_session_net = 0
        five_o_poker_session_net = 0
        blind_mans_bluff_session_net = 0

    elif activity_type == CAREER_ACTIVITY_ARCADE_NIGHT:
        arcade_night_tokens_spent = 0
        arcade_night_tickets_won = 0


def publish_career_event_news():
    global career_event_news_posted

    if career_event_news_posted:
        return False

    if not isinstance(career_event_entry, dict):
        return False

    activity_type = career_event_entry.get("activity_type")
    story = None

    if activity_type == CAREER_ACTIVITY_CASUAL_CARDS:
        story = build_casual_cards_story(
            player_name,
            career_event_result_log,
        )

    elif activity_type == CAREER_ACTIVITY_POKER_NIGHT:
        story = build_poker_story(
            player_name,
            {
                "texas_holdem": texas_holdem_session_net,
                "five_card_draw": five_card_draw_session_net,
                "seven_card_stud": seven_card_stud_session_net,
            },
        )

    elif activity_type == CAREER_ACTIVITY_CASINO_NIGHT:
        story = build_casino_story(
            player_name,
            blackjack_net=blackjack_session_net,
            roulette_net=roulette_session_net,
            horse_races_net=horse_races_session_net,
        )

    elif activity_type == CAREER_ACTIVITY_NICHE_NIGHT:
        story = build_niche_story(
            player_name,
            career_event_result_log,
        )

    elif activity_type == CAREER_ACTIVITY_ARCADE_NIGHT:
        story = build_arcade_story(
            player_name,
            career_event_result_log,
        )

    if story is None:
        return False

    headline, body, category = story
    add_career_news(headline, body, category)
    career_event_news_posted = True
    return True

def get_career_news_total_pages(
        items_per_page=6
):

    ensure_career_news()

    return max(
        1,
        (
            len(career_news_items)
            + items_per_page
            - 1
        )
        // items_per_page
    )

def update_career_leaderboard_ratings():
    global career_npc_world
    if current_game_mode == "free" or not career_leaderboard_state:
        return False
    previous_month = career_npc_world.get("last_simulated_month")
    before_rankings = get_npc_leaderboard_snapshot()
    career_npc_world, stories = advance_career_world(
        career_npc_world, career_leaderboard_state, BASE_NPCS, PROSPECT_POOL,
        career_year, career_month,
    )
    sync_career_npc_runtime_state()
    if career_npc_world["last_simulated_month"] == previous_month:
        return False
    for story in stories:
        add_career_news(story["headline"], story["body"], story["category"],
                        year=story["year"], month=story["month"])
    add_monthly_leaderboard_news(before_rankings, get_npc_leaderboard_snapshot())
    return True


CAREER_LEADERBOARD_PLAYERS = (
    load_career_leaderboard_players()
)

# ==================================================
# DISPLAY
# ==================================================

FPS = 60

# ==================================================
# MENU BACKGROUND DRIFT
# ==================================================

MENU_DRIFT_SCALE = 3
MENU_DRIFT_MARGIN = 35

MENU_DRIFT_X = 20
MENU_DRIFT_Y = 12

# Seconds for one full back-and-forth cycle.
MENU_DRIFT_PERIOD_X = 50.0
MENU_DRIFT_PERIOD_Y = 80.0

WINDOW_WIDTH, WINDOW_HEIGHT = DEFAULT_WINDOW_SIZE

# Remember the user's normal window size so fullscreen can
# return to it cleanly. Fullscreen uses the desktop size.
WINDOWED_WIDTH, WINDOWED_HEIGHT = DEFAULT_WINDOW_SIZE
fullscreen_enabled = False

# Reused destination surface for the final game -> window
# scale. Reusing it avoids allocating a new full-screen
# surface every frame.
scaled_surface_cache = None

screen = pygame.display.set_mode(
    (
        WINDOW_WIDTH,
        WINDOW_HEIGHT
    )
)

pygame.display.set_caption(
    "Solitaire"
)

# Everything in the game is designed at
# 1366 x 768 regardless of actual window size.
game_surface = pygame.Surface(
    (
        BASE_WIDTH,
        BASE_HEIGHT
    )
)

clock = pygame.time.Clock()

confirm_return_to_menu = False

game_pause_menu_open = False
options_return_state = STATE_MENU
customize_return_state = STATE_MENU
profile_return_state = STATE_MENU
profile_select_return_state = STATE_MENU
profile_switch_snapshot = None
career_hub_controls = CareerHubControls()

# ==================================================
# GAME
# ==================================================

game = Game(
    game_surface,
    audio
)

# ==================================================
# PROFILE SLOT STATE
# ==================================================

current_profile_slot = 1
guest_mode = False

profile_creation_mode = False
pending_profile_slot = None

profile_delete_slot = None
confirm_delete_profile = False

player_name = DEFAULT_PLAYER_NAME

player_level = DEFAULT_LEVEL
player_xp = DEFAULT_XP
player_xp_to_next = DEFAULT_XP_TO_NEXT

player_solitaire_points = 0

# ==================================================
# CAREER STATE / CAREER RUNTIME VARIABLES
# ==================================================

texas_holdem_hand_win_sound_at = 0

music_slider_dragging = False
sfx_slider_dragging = False

how_to_play_tab = "basics"

# MINIGAME RUNTIME OBJECTS
blackjack_game = BlackjackGame()
score_four_game = ScoreFourGame()
crazy_eights_game = CrazyEightsGame()
bango_game = BangoGame()
blackjack_dealer_npc = None

texas_holdem_game = TexasHoldemGame()

texas_holdem_starting_stack = 0
texas_holdem_session_net = 0
texas_holdem_buy_in_active = False

texas_holdem_next_npc_action_at = 0
texas_holdem_round_advance_at = 0

TEXAS_HOLDEM_NPC_DELAY = 1200
TEXAS_HOLDEM_STREET_DELAY = 1200

texas_holdem_next_hand_at = 0

TEXAS_HOLDEM_NEXT_HAND_DELAY = 15000

# ==================================================
# HOLDEM SHOWDOWN / SESSION END
# ==================================================

texas_holdem_last_processed_showdown_hand = 0

texas_holdem_session_end_at = 0

texas_holdem_table_sweep_rewarded = False


TEXAS_HOLDEM_SESSION_END_DELAY = 5000

TEXAS_HOLDEM_TABLE_SWEEP_RATING_BONUS = 100

# ==================================================
# FIVE-CARD DRAW RUNTIME
# ==================================================

five_card_draw_game = FiveCardDrawGame()

five_card_draw_starting_stack = 0
five_card_draw_session_net = 0
five_card_draw_buy_in_active = False

five_card_draw_next_npc_action_at = 0
five_card_draw_round_advance_at = 0
five_card_draw_next_hand_at = 0
five_card_draw_session_end_at = 0
five_card_draw_hand_win_sound_at = 0

five_card_draw_last_processed_showdown_hand = 0
five_card_draw_table_sweep_rewarded = False

FIVE_CARD_DRAW_SESSION_END_DELAY = 5000
FIVE_CARD_DRAW_TABLE_SWEEP_RATING_BONUS = 100

# ==================================================
# SEVEN-CARD STUD RUNTIME
# ==================================================

seven_card_stud_game = SevenCardStudGame()

seven_card_stud_starting_stack = 0
seven_card_stud_session_net = 0
seven_card_stud_buy_in_active = False

seven_card_stud_next_npc_action_at = 0
seven_card_stud_round_advance_at = 0
seven_card_stud_next_hand_at = 0
seven_card_stud_session_end_at = 0
seven_card_stud_hand_win_sound_at = 0

seven_card_stud_last_processed_showdown_hand = 0
seven_card_stud_table_sweep_rewarded = False

SEVEN_CARD_STUD_SESSION_END_DELAY = 5000
SEVEN_CARD_STUD_TABLE_SWEEP_RATING_BONUS = 100

roulette_game = RouletteGame()
horse_races_game = HorseRaceGame()
case_screen = CaseOpeningScreen()
case_collection_state = new_case_state()
cryptid_screen = CryptidScreen()
cryptid_collection_state = new_collection()
career_poker_learning = new_learning()
faro_game = FaroGame()
five_o_poker_game = FiveOPokerGame()
blind_mans_bluff_game = BlindMansBluffGame()
king_pong_game = KingPongGame()
battle_bosses_game = BattleBossesGame()
arcade_state = make_default_arcade_state()
arcade_night_tokens_spent = 0
arcade_night_tickets_won = 0
arcade_pending_launch_game_id = None
arcade_selected_prize_index = 0
king_pong_opponent_choices = []
king_pong_selected_opponent_index = None
battle_bosses_opponent_choices = []
battle_bosses_selected_choice_index = None
arcade_status_message = ""
arcade_status_message_expires = 0

roulette_session_net = 0
roulette_chip_value = 10
horse_races_session_net = 0
horse_races_last_rewarded_races = 0
faro_session_net = 0
faro_chip_value = 10
five_o_poker_starting_stack = 0
five_o_poker_session_net = 0
five_o_poker_buy_in_active = False
blind_mans_bluff_starting_stack = 0
blind_mans_bluff_session_net = 0
blind_mans_bluff_buy_in_active = False

blackjack_session_net = 0
blackjack_session_rating_change = 0

blackjack_selected_bet_percentage = None
blackjack_bet_dropdown_open = False

blackjack_dealer_npc = None

score_four_opponent_choices = []
score_four_opponent_npc = None

debug_previous_state = None
debug_poker_select_game_id = None
debug_poker_selected_ids = []


career_event_entry = None
career_event_has_activity = False

career_event_summary_title = ""
career_event_summary_lines = []
career_event_result_log = []
career_event_news_posted = False
career_event_start_arcade_tokens = 0
career_event_start_arcade_tickets = 0

career_news_page = 0

career_rating = 1000
career_ratings = make_player_rating_bundle(career_rating)
career_rating_results = {}
career_cash = 500
career_fans = 0
career_last_fan_change = 0
career_last_fan_reason = ""
career_fan_rewarded_jobs = set()
career_fan_news_milestones = set()

# ==================================================
# ACHIEVEMENTS
# ==================================================
achievement_state = make_default_achievement_state()
achievements_scroll_y = 0
achievement_popup_queue = []
achievement_popup_current = None
achievement_popup_started = 0
achievement_popup_fans = 0
achievement_popup_cosmetic = ""

blackjack_round_doubled = False
blackjack_round_all_in = False
blackjack_round_start_bet = 0
free_play_achievement_fans_earned = 0

# Press interview event runtime
career_interview_recent_ids = []
career_bigfoot_story = new_story()
career_alien_story = new_alien_story()
career_interview_questions = []
career_interview_index = 0
career_interview_media_heat = 0
career_interview_fan_change = 0
career_interview_feedback = ""

# Sign-autographs event runtime
career_autograph_event = AutographEvent()
career_autograph_fan_change = 0
career_autograph_last_change = 0

# Head-to-Head timed Klondike event runtime
head_to_head_race = HeadToHeadRace()
head_to_head_opponents = []
head_to_head_selected_index = None
head_to_head_previous_deal_mode = None
head_to_head_previous_difficulty = None
head_to_head_previous_stock_draw_count = None

career_year = 2026
career_month = 1
career_day_of_month = 1

career_weekday_index = 0
career_day = 1

career_residence_image_cache = {}

career_web_image_cache = {}

career_job_image_cache = {}




# ==================================================
# SCORE-FOUR RECTS
# ==================================================

score_four_number_rects = []

score_four_operator_rects = {}

score_four_undo_rect = pygame.Rect(
    460,
    700,
    140,
    46
)

score_four_exit_rect = pygame.Rect(
    766,
    700,
    140,
    46
)

score_four_complete_rect = pygame.Rect(
    BASE_WIDTH // 2 - 100,
    585,
    200,
    48
)

score_four_solo_rect = pygame.Rect(
    BASE_WIDTH // 2 - 260,
    330,
    220,
    70
)

score_four_competitive_rect = pygame.Rect(
    BASE_WIDTH // 2 + 40,
    330,
    220,
    70
)

score_four_mode_return_rect = pygame.Rect(
    BASE_WIDTH // 2 - 90,
    470,
    180,
    46
)

score_four_match_continue_rect = pygame.Rect(
    BASE_WIDTH // 2 - 100,
    585,
    200,
    48
)

score_four_hint_rect = pygame.Rect(
    BASE_WIDTH // 2 + 300,
    700,
    140,
    46
)



def draw_npc_portrait(npc, rect, style_id):
    draw_framed_npc_portrait(
        game_surface, npc, rect, style_id, NPC_PORTRAIT_STYLES,
        get_npc_portrait_surface, score_four_score_font
    )

def get_npc_portrait_surface(npc, size):
    portrait_path = npc.get("portrait")
    if portrait_path:
        cache_key = (portrait_path, size)
        if cache_key in npc_icon_cache:
            return npc_icon_cache[cache_key]
        try:
            image = pygame.image.load(portrait_path).convert_alpha()
            image = pygame.transform.smoothscale(image, (size, size))
            npc_icon_cache[cache_key] = image
            return image
        except (pygame.error, FileNotFoundError):
            pass
    return draw_layered_portrait(npc, size)













career_leaderboard_state = {}
career_npc_world = {}
career_leaderboard_star_id = None

career_residence = (
    "dingy_apartment"
)

career_owned_residences = [
    "dingy_apartment"
]

career_job = (
    "custodian"
)

selected_leaderboard_entry = None

career_rounds_won = 0
career_challenges_won = 0
career_total_moves = 0

career_leaderboard_page = 0
career_leaderboard_rating_key = "overall"

career_completed_days = []

career_current_schedule = []

career_news_items = []

npc_icon_cache = {}

# ----------------------------
# Current Career activity
# ----------------------------

pending_career_activity_index = None
pending_career_activity_type = None
pending_career_challenge_id = None

current_game_mode = None

unlocked_menu_backgrounds = set(
    DEFAULT_UNLOCKED_MENU_BACKGROUNDS
)

unlocked_felts = set(
    DEFAULT_UNLOCKED_FELTS
)

unlocked_titles = set(
    DEFAULT_UNLOCKED_TITLES
)

selected_menu_background = (
    DEFAULT_SELECTED_MENU_BACKGROUND
)

selected_felt = (
    DEFAULT_SELECTED_FELT
)

selected_title = (
    DEFAULT_SELECTED_TITLE
)

# Cursor cosmetics are unlocked by default. The actual
# available IDs are discovered from assets/ui/cursors.
selected_cursor = "cursor"


# ==================================================
# PROFILE STATE
# ==================================================

profile_name_text = player_name
profile_country_text = ""
profile_age_text = ""
profile_hometown_text = ""
profile_bio_text = ""

profile_gender = "non-binary"
profile_favorite_suit = ""

gender_options = [
    "male",
    "female",
    "non-binary",
]

favorite_suit_options = [
    "Clubs",
    "Diamonds",
    "Hearts",
    "Spades",
]

gender_dropdown_open = False
favorite_suit_dropdown_open = False

profile_name_active = False
profile_country_active = False
profile_age_active = False
profile_hometown_active = False
profile_bio_active = False

profile_message = ""

selected_avatar_base = "base_01"
selected_avatar_eyes = "eyes_01"
selected_avatar_hair = "hair_01"
selected_avatar_glasses = "glasses_01"
selected_avatar_top = "top_01"

# ==================================================
# LAYERED AVATAR ASSETS
# ==================================================

avatar_bases = load_avatar_bank("bases")
avatar_eyes = load_avatar_bank("eyes")
avatar_hair = load_avatar_bank("hair")
avatar_glasses = load_avatar_bank("glasses")
avatar_tops = load_avatar_bank("tops")

# ==================================================
# MINI MENU BUTTON ASSETS
# ==================================================

register_player_avatar_art(avatar_bases, avatar_eyes, avatar_hair, avatar_glasses, avatar_tops)

menu_button_icon = pygame.image.load(
    "assets/ui/gameplay/menu_button_icon.png"
).convert_alpha()

hint_button_icon = pygame.image.load(
    "assets/ui/gameplay/hint_button_icon.png"
).convert_alpha()

hint_lock_icon = pygame.image.load(
    "assets/ui/gameplay/hint_lock_icon.png"
).convert_alpha()

undo_button_icon = pygame.image.load(
    "assets/ui/gameplay/undo_button_icon.png"
).convert_alpha()

shuffle_button_icon = pygame.image.load(
    "assets/ui/gameplay/shuffle_button_icon.png"
).convert_alpha()

autosolve_button_icon = pygame.image.load(
    "assets/ui/gameplay/autosolve_button_icon.png"
).convert_alpha()

# ==================================================
# SPLASH ASSETS
# ==================================================

def _load_legacy_splash_asset(path, fallback_size=(BASE_WIDTH, BASE_HEIGHT)):
    try:
        return pygame.image.load(path).convert_alpha()
    except (pygame.error, FileNotFoundError):
        return pygame.Surface(fallback_size, pygame.SRCALPHA)


splash_background = _load_legacy_splash_asset(
    "assets/ui/splash/splash_background.png"
)

splash_spade = _load_legacy_splash_asset(
    "assets/ui/splash/splash_spade.png"
)

splash_diamond = _load_legacy_splash_asset(
    "assets/ui/splash/splash_diamond.png"
)

splash_club = _load_legacy_splash_asset(
    "assets/ui/splash/splash_club.png"
)

splash_heart = _load_legacy_splash_asset(
    "assets/ui/splash/splash_heart.png"
)

splash_prompt = _load_legacy_splash_asset(
    "assets/ui/splash/splash_prompt.png"
)

# Optional modern splash assets. Keep the original splash as a full fallback so
# the game remains launchable while the new artwork is still being created.
try:
    modern_splash_background = pygame.image.load(
        "assets/splash/background.png"
    ).convert_alpha()
    modern_splash_background = pygame.transform.smoothscale(
        modern_splash_background,
        (BASE_WIDTH, BASE_HEIGHT)
    )
except (pygame.error, FileNotFoundError):
    modern_splash_background = None

try:
    modern_splash_logo = pygame.image.load(
        "assets/splash/logo.png"
    ).convert_alpha()
except (pygame.error, FileNotFoundError):
    modern_splash_logo = None


splash_start_time = pygame.time.get_ticks()

audio.play_sound(
    "startup"
)


# ==================================================
# MENU / CUSTOMIZATION ASSETS
# ==================================================

button_normal = pygame.image.load(
    "assets/ui/menu_ui/button_normal.png"
).convert_alpha()

button_hover = pygame.image.load(
    "assets/ui/menu_ui/button_hover.png"
).convert_alpha()

button_selected = pygame.image.load(
    "assets/ui/menu_ui/button_selected.png"
).convert_alpha()

floating_logo = pygame.image.load(
    "assets/ui/menu_ui/floating_logo.png"
).convert_alpha()


background_catalog = CosmeticCatalog(MENU_BACKGROUNDS, "bg_default")
menu_background_surfaces = background_catalog.surfaces

avatar_base_options = avatar_options(avatar_bases, allow_none=False)

avatar_eye_options = avatar_options(avatar_eyes, allow_none=False)

avatar_hair_options = avatar_options(avatar_hair, allow_none=False)

avatar_glasses_options = avatar_options(avatar_glasses, allow_none=True)

avatar_top_options = avatar_options(avatar_tops, allow_none=False)

# ==================================================
# MORE UI ASSETS
# ==================================================

play_background_image = pygame.image.load(
    "assets/ui/menu_ui/play_background.png"
).convert_alpha()

play_background_image = pygame.transform.smoothscale(
    play_background_image,
    (
        BASE_WIDTH,
        BASE_HEIGHT
    )
)

# ----------------------------
# Supersampled copies used for
# slow menu background drifting
# ----------------------------
#
# The original drift rendered at 4x resolution. That looked
# smooth because the quarter-pixel movement survived the
# downsample, but it was expensive. The first performance
# pass dropped this to a direct 1x blit, which was fast but
# made very slow movement advance in obvious whole-pixel
# steps.
#
# A 3x drift buffer is the compromise: it restores subpixel-
# looking motion while processing substantially fewer pixels
# than the old 4x path.

menu_background_drift_cache = SingleDriftCache()

drift_width = (
    BASE_WIDTH
    + MENU_DRIFT_MARGIN * 2
)

drift_height = (
    BASE_HEIGHT
    + MENU_DRIFT_MARGIN * 2
)

menu_drift_render_surface = pygame.Surface(
    (
        BASE_WIDTH
        * MENU_DRIFT_SCALE,

        BASE_HEIGHT
        * MENU_DRIFT_SCALE
    )
).convert()

from case_opening import ITEMS as CASE_ITEMS
FELTS.update({
    "f_case_" + key: {"name": item["name"], "path": item["felt_path"]}
    for key, item in CASE_ITEMS.items() if item["kind"] == "cosmetic"
})
felt_catalog = CosmeticCatalog(FELTS, "f_default")
felt_surfaces = felt_catalog.surfaces


title_catalog = CosmeticCatalog(TITLES, "title_default")
title_surfaces = title_catalog.surfaces

# ==================================================
# CUSTOM CURSORS
# ==================================================

CURSOR_FOLDER = "assets/ui/cursors"
CURSOR_PREVIEW_FOLDER = os.path.join(
    CURSOR_FOLDER,
    "previews"
)
CURSOR_RUNTIME_SIZE = (34, 30)
CURSOR_PREVIEW_MAX_SIZE = (150, 115)

cursor_cosmetics = {}
cursor_surfaces = {}
cursor_preview_surfaces = {}
cursor_runtime_surfaces = {}

if os.path.isdir(CURSOR_FOLDER):
    cursor_files = [
        filename
        for filename in os.listdir(CURSOR_FOLDER)
        if filename.lower().endswith(".png")
    ]
else:
    cursor_files = []

# Keep the original cursor.png first, then sort additional
# customization assets alphabetically for stable ordering.
cursor_files.sort(
    key=lambda filename: (
        0 if filename.lower() == "cursor.png" else 1,
        filename.lower()
    )
)

for cursor_index, filename in enumerate(cursor_files):
    asset_id = os.path.splitext(filename)[0]
    path = os.path.join(CURSOR_FOLDER, filename)

    source = pygame.image.load(path).convert_alpha()

    cursor_surfaces[asset_id] = source
    cursor_runtime_surfaces[asset_id] = (
        pygame.transform.smoothscale(
            source,
            CURSOR_RUNTIME_SIZE
        )
    )

    # Prefer dedicated large preview artwork when present.
    # Otherwise build a crisp nearest-neighbor thumbnail once
    # at startup instead of smooth-scaling the tiny live cursor
    # every time the Customize screen is drawn.
    preview_path = os.path.join(
        CURSOR_PREVIEW_FOLDER,
        filename
    )

    if os.path.isfile(preview_path):
        preview_source = pygame.image.load(
            preview_path
        ).convert_alpha()
    else:
        preview_source = source

    preview_width = preview_source.get_width()
    preview_height = preview_source.get_height()

    if preview_width > 0 and preview_height > 0:
        preview_scale = min(
            CURSOR_PREVIEW_MAX_SIZE[0] / preview_width,
            CURSOR_PREVIEW_MAX_SIZE[1] / preview_height
        )

        # Never shrink dedicated preview art unnecessarily.
        # Tiny cursor sprites are enlarged with nearest-neighbor
        # scaling so pixel edges stay sharp.
        if preview_scale > 1.0:
            preview_size = (
                max(1, int(preview_width * preview_scale)),
                max(1, int(preview_height * preview_scale))
            )
            preview_surface = pygame.transform.scale(
                preview_source,
                preview_size
            )
        else:
            preview_surface = pygame.transform.smoothscale(
                preview_source,
                (
                    max(1, int(preview_width * preview_scale)),
                    max(1, int(preview_height * preview_scale))
                )
            )
    else:
        preview_surface = preview_source

    cursor_preview_surfaces[asset_id] = preview_surface

    if asset_id == "cursor":
        display_name = "Default"
    else:
        display_name = (
            asset_id
            .replace("cursor_", "")
            .replace("_", " ")
            .strip()
            .title()
        )

        if not display_name:
            display_name = asset_id

    cursor_cosmetics[asset_id] = {
        "name": display_name,
        "path": path,
        "order": (cursor_index + 1) * 10,
    }

unlocked_cursors = set(cursor_cosmetics.keys())

if selected_cursor not in cursor_runtime_surfaces:
    if "cursor" in cursor_runtime_surfaces:
        selected_cursor = "cursor"
    elif cursor_files:
        selected_cursor = os.path.splitext(cursor_files[0])[0]

cursor_image = cursor_runtime_surfaces.get(selected_cursor)

# Modern pygame/SDL can use an RGBA Surface as a true OS cursor. That keeps
# the default path snappy. However, some Windows systems use accessibility
# cursor sizes that are much larger than the standard arrow. In that case the
# tiny native replacement is hard to see, so we intentionally fall back to a
# software cursor that is scaled to the user's OS cursor metrics.
software_cursor_fallback = False
software_cursor_force_accessible = False
system_cursor_metrics = CURSOR_RUNTIME_SIZE
_cursor_scaled_cache = {}


def detect_accessible_cursor_mode():
    global software_cursor_force_accessible
    global system_cursor_metrics

    software_cursor_force_accessible = False
    system_cursor_metrics = CURSOR_RUNTIME_SIZE

    if not sys.platform.startswith("win"):
        return

    try:
        user32 = ctypes.windll.user32
        width = int(user32.GetSystemMetrics(13))
        height = int(user32.GetSystemMetrics(14))
    except Exception:
        return

    if width > 0 and height > 0:
        system_cursor_metrics = (width, height)
        software_cursor_force_accessible = (
            max(width, height) >= 48
            or width * height >= 2304
        )


def get_selected_cursor_surface(use_accessible_size=False):
    source = cursor_surfaces.get(selected_cursor)
    if source is None:
        return None

    if not use_accessible_size:
        return cursor_runtime_surfaces.get(selected_cursor)

    target_w, target_h = system_cursor_metrics
    target_w = max(target_w, CURSOR_RUNTIME_SIZE[0])
    target_h = max(target_h, CURSOR_RUNTIME_SIZE[1])
    cache_key = (selected_cursor, target_w, target_h)
    if cache_key in _cursor_scaled_cache:
        return _cursor_scaled_cache[cache_key]

    scale = min(target_w / max(1, source.get_width()), target_h / max(1, source.get_height()))
    scaled = pygame.transform.smoothscale(
        source,
        (
            max(1, int(round(source.get_width() * scale))),
            max(1, int(round(source.get_height() * scale))),
        )
    )
    _cursor_scaled_cache[cache_key] = scaled
    return scaled


def apply_selected_cursor():
    global cursor_image
    global software_cursor_fallback

    detect_accessible_cursor_mode()

    if software_cursor_force_accessible:
        cursor_image = get_selected_cursor_surface(use_accessible_size=True)
        pygame.mouse.set_visible(False)
        software_cursor_fallback = True
        return

    cursor_image = get_selected_cursor_surface(use_accessible_size=False)

    if cursor_image is None:
        pygame.mouse.set_visible(True)
        software_cursor_fallback = False
        return

    try:
        native_cursor = pygame.cursors.Cursor((0, 0), cursor_image)
        pygame.mouse.set_cursor(native_cursor)
        pygame.mouse.set_visible(True)
        software_cursor_fallback = False
    except (pygame.error, TypeError, ValueError):
        cursor_image = get_selected_cursor_surface(use_accessible_size=False)
        pygame.mouse.set_visible(False)
        software_cursor_fallback = True


apply_selected_cursor()

# ==================================================
# COSMETIC SYNC
# ==================================================

def sync_selected_cosmetics():
    game.set_felt_surface(
        felt_surfaces[selected_felt]
    )


sync_selected_cosmetics()

# ==================================================
# FONTS
# ==================================================

menu_title_font = pygame.font.SysFont(
    None,
    72
)

courrier_font_path = None

old_english_names = [
    "Old English Text MT",
    "OldEnglishTextMT",
    "Old English Text",
    "oldenglishtextmt",
]

for font_name in old_english_names:

    courrier_font_path = (
        pygame.font.match_font(
            font_name
        )
    )

    if courrier_font_path:
        break


if courrier_font_path:

    print(
        "Loaded Courrier font:",
        courrier_font_path
    )

    courrier_title_font = (
        pygame.font.Font(
            courrier_font_path,
            58
        )
    )

else:

    print(
        "Old English Text MT not found. "
        "Using fallback."
    )

    courrier_title_font = (
        menu_title_font
    )

menu_font = pygame.font.SysFont(
    None,
    42
)

options_title_font = pygame.font.SysFont(
    None,
    60
)

option_label_font = pygame.font.SysFont(
    None,
    34
)

option_value_font = pygame.font.SysFont(
    None,
    27
)

difficulty_detail_font = pygame.font.SysFont(
    None,
    24
)

tooltip_font = pygame.font.SysFont(
    None,
    22
)

# Blackjack deliberately uses its own typography rather than the default UI
# font so the table has a more distinct casino identity.
blackjack_title_font = pygame.font.SysFont(
    "georgia",
    46,
    bold=True
)
blackjack_heading_font = pygame.font.SysFont(
    "cambria",
    27,
    bold=True
)
blackjack_body_font = pygame.font.SysFont(
    "cambria",
    21
)
blackjack_small_font = pygame.font.SysFont(
    "cambria",
    17
)


ui_small_font = pygame.font.SysFont(
    None,
    24
)

leaderboard_tiny_font = pygame.font.SysFont(
    None,
    16
)

score_four_score_font = pygame.font.Font(
    None,
    36
)

score_four_round_font = pygame.font.Font(
    None,
    26
)

score_four_npc_font = pygame.font.Font(
    None,
    30
)


# ==================================================
# MAIN MENU UI
# ==================================================

new_game_rect = pygame.Rect(533, 214, 300, 54)
profile_rect = pygame.Rect(533, 278, 300, 54)
customize_rect = pygame.Rect(533, 342, 300, 54)
achievements_rect = pygame.Rect(533, 406, 300, 54)
how_to_play_rect = pygame.Rect(533, 470, 300, 54)
options_rect = pygame.Rect(533, 534, 300, 54)
quit_rect = pygame.Rect(533, 598, 300, 54)
multiplayer_rect = pygame.Rect(533, 662, 300, 54)

# ==================================================
# PROFILE UI
# ==================================================

profile_name_rect = pygame.Rect(
    410,
    180,
    340,
    46
)

profile_country_rect = pygame.Rect(
    775,
    180,
    145,
    46
)

profile_age_rect = pygame.Rect(
    945,
    180,
    145,
    46
)

profile_gender_rect = pygame.Rect(
    410,
    270,
    300,
    46
)

profile_favorite_suit_rect = pygame.Rect(
    735,
    270,
    355,
    46
)

profile_gender_option_rects = [
    pygame.Rect(
        410,
        316 + i * 42,
        300,
        42
    )
    for i in range(3)
]

profile_favorite_suit_option_rects = [
    pygame.Rect(
        735,
        316 + i * 42,
        355,
        42
    )
    for i in range(4)
]

profile_hometown_rect = pygame.Rect(
    410,
    360,
    680,
    46
)

profile_bio_rect = pygame.Rect(
    410,
    455,
    680,
    126
)

profile_save_rect = pygame.Rect(
    410,
    650,
    200,
    48
)

profile_switch_rect = pygame.Rect(
    630,
    650,
    240,
    48
)

profile_back_rect = pygame.Rect(
    890,
    650,
    200,
    48
)

# ==================================================
# CUSTOMIZATION UI
# ==================================================

customize_backgrounds_rect = pygame.Rect(
    250,
    120,
    200,
    50
)

customize_felts_rect = pygame.Rect(
    472,
    120,
    200,
    50
)

customize_titles_rect = pygame.Rect(
    694,
    120,
    200,
    50
)

customize_cursors_rect = pygame.Rect(
    916,
    120,
    200,
    50
)


customize_item_rects = [
    pygame.Rect(175, 215, 300, 190),
    pygame.Rect(533, 215, 300, 190),
    pygame.Rect(891, 215, 300, 190),

    pygame.Rect(175, 435, 300, 190),
    pygame.Rect(533, 435, 300, 190),
    pygame.Rect(891, 435, 300, 190),
]


customize_prev_rect = pygame.Rect(
    300,
    670,
    180,
    50
)

customize_back_rect = pygame.Rect(
    593,
    670,
    180,
    50
)

customize_next_rect = pygame.Rect(
    886,
    670,
    180,
    50
)

# ==================================================
# GAMEPLAY UI
# ==================================================

confirm_yes_rect = pygame.Rect(
    530,
    390,
    140,
    50
)

confirm_no_rect = pygame.Rect(
    695,
    390,
    140,
    50
)

confirm_delete_yes_rect = pygame.Rect(
    530,
    410,
    140,
    50
)

confirm_delete_no_rect = pygame.Rect(
    695,
    410,
    140,
    50
)


# ==================================================
# GAMEPLAY MINI BUTTONS
# ==================================================

mini_button_size = 56
mini_button_gap = 4

# MENU
game_menu_rect = pygame.Rect(
    10,
    0,
    mini_button_size,
    mini_button_size
)

# HINT
game_hint_rect = pygame.Rect(
    10,
    0,
    mini_button_size,
    mini_button_size
)

game_undo_rect = pygame.Rect(
    10,
    0,
    mini_button_size,
    mini_button_size
)

game_shuffle_rect = pygame.Rect(
    10,
    0,
    mini_button_size,
    mini_button_size
)

game_auto_solve_rect = pygame.Rect(
        10,
        0,
        mini_button_size,
        mini_button_size
    )

# ==================================================
# PROFILE SELECT UI
# ==================================================

profile_slot_rects = [
    pygame.Rect(
        333,
        180 + i * 120,
        700,
        90
    )
    for i in range(3)
]

guest_profile_rect = pygame.Rect(
    483,
    565,
    400,
    70
)

profile_delete_rects = [
    pygame.Rect(
        rect.right - 110,
        rect.y + 20,
        90,
        50
    )
    for rect in profile_slot_rects
]

# ==================================================
# PLAY MODE SELECT
# ==================================================

play_free_rect = pygame.Rect(
    0,
    0,
    BASE_WIDTH // 2,
    BASE_HEIGHT
)

play_career_rect = pygame.Rect(
    BASE_WIDTH // 2,
    0,
    BASE_WIDTH // 2,
    BASE_HEIGHT
)

play_return_rect = pygame.Rect(
    BASE_WIDTH // 2 - 90,
    BASE_HEIGHT - 70,
    180,
    46
)

# ==================================================
# FREE PLAY SELECT
# ==================================================

FREE_PLAY_GAME_IDS = (
    "case_opening",
    "cryptid_creatures",
    "solitaire",
    "score_four",
    "crazy_eights",
    "bango",
    "blackjack",
    "roulette",
    "horse_races",
    "texas_holdem",
    "five_card_draw",
    "seven_card_stud",
    "faro",
    "five_o_poker",
    "blind_mans_bluff",
)

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

free_play_game_rects = {}
for free_index, free_game_id in enumerate(FREE_PLAY_GAME_IDS):
    free_column = free_index % 3
    free_row = free_index // 3
    free_play_game_rects[free_game_id] = pygame.Rect(
        96 + free_column * 410,
        185 + free_row * 88,
        356,
        64
    )

free_play_back_rect = pygame.Rect(
    BASE_WIDTH // 2 - 150,
    675,
    300,
    50
)

free_play_snapshot = None
FREE_PLAY_STARTING_CASH = 5_000

# ==================================================
# DIFFICULTY SELECT -- AREA FOR UI RECTANGLE DEFINITIONS
# ==================================================

# ==================================================
# BLACKJACK UI // MINIGAME RECTS
# ==================================================

# During a hand these five buttons directly choose the NEXT hand's bet.
blackjack_bet_dropdown_rects = [
    pygame.Rect(1052, 365, 116, 44),
    pygame.Rect(1180, 365, 116, 44),
    pygame.Rect(1052, 419, 116, 44),
    pygame.Rect(1180, 419, 116, 44),
    pygame.Rect(1052, 473, 244, 44),
]

# Kept for compatibility with older state, but no longer drawn as a two-step
# Change Bet control.
blackjack_change_bet_rect = pygame.Rect(0, 0, 0, 0)

blackjack_hit_rect = pygame.Rect(430, 660, 150, 50)
blackjack_stand_rect = pygame.Rect(595, 660, 150, 50)
blackjack_double_rect = pygame.Rect(760, 660, 165, 50)
blackjack_split_rect = pygame.Rect(940, 660, 150, 50)
blackjack_return_rect = pygame.Rect(1105, 660, 185, 50)
blackjack_deal_again_rect = pygame.Rect(570, 660, 225, 50)

how_to_play_back_rect = pygame.Rect(
    533,
    690,
    300,
    50
)

score_four_opponent_rects = [
    pygame.Rect(
        240,
        180,
        390,
        180
    ),

    pygame.Rect(
        735,
        180,
        390,
        180
    ),

    pygame.Rect(
        240,
        405,
        390,
        180
    ),

    pygame.Rect(
        735,
        405,
        390,
        180
    ),
]

score_four_opponent_return_rect = pygame.Rect(
    BASE_WIDTH // 2 - 90,
    650,
    180,
    46
)

# ==================================================
# BLACKJACK BET SELECT
# ==================================================

blackjack_bet_1_rect = pygame.Rect(370, 390, 145, 58)
blackjack_bet_2_rect = pygame.Rect(525, 390, 145, 58)
blackjack_bet_5_rect = pygame.Rect(680, 390, 145, 58)
blackjack_bet_10_rect = pygame.Rect(835, 390, 145, 58)
blackjack_bet_all_rect = pygame.Rect(525, 475, 300, 58)
blackjack_bet_return_rect = pygame.Rect(BASE_WIDTH // 2 - 105, 640, 210, 48)

how_to_play_tab_rects = {
    "basics":
        pygame.Rect(
            120,
            105,
            170,
            50
        ),

    "rules":
        pygame.Rect(
            310,
            105,
            170,
            50
        ),

    "controls":
        pygame.Rect(
            500,
            105,
            170,
            50
        ),

    "strategy":
        pygame.Rect(
            690,
            105,
            170,
            50
        ),

    "variants":
        pygame.Rect(
            880,
            105,
            170,
            50
        ),

    "career":
        pygame.Rect(
            1070,
            105,
            170,
            50
        ),
}


free_play_rect = pygame.Rect(
    383,
    230,
    600,
    100
)


# ==================================================
# CAREER RECTANGLES // CAREER UI RECTS
# ==================================================

career_event_summary_continue_rect = pygame.Rect(
    BASE_WIDTH // 2 - 100,
    620,
    200,
    50
)

career_event_card_rects = []

career_event_return_rect = pygame.Rect(
    BASE_WIDTH // 2 - 245,
    646,
    220,
    59
)

career_event_end_rect = pygame.Rect(
    BASE_WIDTH // 2 + 25,
    646,
    220,
    59
)

arcade_machine_buy_tokens_rect = pygame.Rect(328, 535, 330, 92)
arcade_machine_prize_counter_rect = pygame.Rect(708, 535, 330, 92)

arcade_token_package_rects = {}
for package_index in range(len(ARCADE_TOKEN_PACKAGES)):
    row = package_index // 2
    column = package_index % 2
    arcade_token_package_rects[package_index] = pygame.Rect(
        248 + column * 475,
        270 + row * 172,
        395,
        132,
    )

arcade_token_exchange_back_rect = pygame.Rect(128, 658, 240, 54)
arcade_token_exchange_continue_rect = pygame.Rect(998, 658, 240, 54)

arcade_prize_card_rects = {}
for prize_index in range(len(ARCADE_PRIZE_CATALOG)):
    arcade_prize_card_rects[prize_index] = pygame.Rect(116 + prize_index * 388, 212, 350, 248)

arcade_prize_back_rect = pygame.Rect(106, 658, 220, 54)
arcade_prize_trophy_room_rect = pygame.Rect(573, 658, 220, 54)
arcade_prize_buy_rect = pygame.Rect(1040, 658, 220, 54)
arcade_trophy_room_back_rect = pygame.Rect(543, 658, 280, 54)

king_pong_return_rect = pygame.Rect(1132, 652, 198, 54)

king_pong_opponent_rects = [
    pygame.Rect(103 + index * 292, 205, 266, 340)
    for index in range(4)
]
king_pong_opponent_back_rect = pygame.Rect(103, 657, 220, 54)
king_pong_opponent_tokens_rect = pygame.Rect(573, 657, 220, 54)
king_pong_opponent_play_rect = pygame.Rect(1043, 657, 220, 54)

battle_bosses_choice_rects = [
    pygame.Rect(108 + (index % 2) * 590, 205 + (index // 2) * 210, 552, 185)
    for index in range(4)
]
battle_bosses_back_rect = pygame.Rect(108, 651, 240, 54)
battle_bosses_refresh_rect = pygame.Rect(563, 651, 240, 54)
battle_bosses_future_play_rect = pygame.Rect(1018, 651, 240, 54)
battle_bosses_quit_rect = pygame.Rect(1090, 675, 220, 50)

career_interview_answer_rects = [
    pygame.Rect(348, 410, 670, 54),
    pygame.Rect(348, 480, 670, 54),
    pygame.Rect(348, 550, 670, 54),
]

career_news_prev_rect = pygame.Rect(
    430,
    700,
    80,
    45
)

career_news_next_rect = pygame.Rect(
    855,
    700,
    80,
    45
)

career_mode_rect = pygame.Rect(
    383,
    430,
    600,
    100
)

mode_select_back_rect = pygame.Rect(
    533,
    650,
    300,
    55
)

career_play_rect = pygame.Rect(
    483,
    400,
    400,
    55
)

career_jobs_rect = pygame.Rect(
    333,
    485,
    300,
    55
)

career_real_estate_rect = pygame.Rect(
    733,
    485,
    300,
    55
)

career_leaderboards_rect = pygame.Rect(
    333,
    555,
    300,
    55
)

career_news_rect = pygame.Rect(
    733,
    555,
    300,
    55
)

career_back_rect = pygame.Rect(
    533,
    650,
    300,
    50
)

career_subpage_back_rect = pygame.Rect(
    533,
    715,
    300,
    45
)

career_leaderboard_prev_rect = pygame.Rect(
    430,
    700,
    80,
    45
)

career_leaderboard_next_rect = pygame.Rect(
    855,
    700,
    80,
    45
)

career_leaderboard_rating_prev_rect = pygame.Rect(
    510,
    164,
    42,
    30
)

career_leaderboard_rating_next_rect = pygame.Rect(
    814,
    164,
    42,
    30
)

career_leaderboard_bio_rects = []

career_job_option_rects = {
    "custodian":
        pygame.Rect(
            285,
            180,
            375,
            145
        ),

    "satellite_repair":
        pygame.Rect(
            705,
            180,
            375,
            145
        ),

    "videographer":
        pygame.Rect(
            285,
            345,
            375,
            145
        ),

    "airline_pilot":
        pygame.Rect(
            705,
            345,
            375,
            145
        ),

    "spiritual_guru":
        pygame.Rect(
            285,
            510,
            375,
            145
        ),

    "solitaire_pensioner":
        pygame.Rect(
            705,
            510,
            375,
            145
        ),
}

career_residence_option_rects = {
    "dingy_apartment": pygame.Rect(285,230,375,140),
    "hippie_commune": pygame.Rect(705,230,375,140),

    "towers": pygame.Rect(285,385,375,140),
    "summit": pygame.Rect(705,385,375,140),

    "heliyacht": pygame.Rect(285,540,375,140),
    "card_castle": pygame.Rect(705,540,375,140),
}

career_calendar_action_rect = pygame.Rect(
    0,
    0,
    0,
    0
)

career_calendar_skip_rect = pygame.Rect(
    0,
    0,
    0,
    0
)

career_fast_skip_yes_rect = pygame.Rect(
    505,
    438,
    160,
    48
)

career_fast_skip_no_rect = pygame.Rect(
    700,
    438,
    160,
    48
)

profile_switch_rect = pygame.Rect(
    630,
    650,
    240,
    48
)

pause_resume_rect = pygame.Rect(
    533,
    300,
    300,
    55
)

pause_options_rect = pygame.Rect(
    533,
    375,
    300,
    55
)

pause_menu_rect = pygame.Rect(
    533,
    450,
    300,
    55
)

difficulty_easy_rect = pygame.Rect(
    283,
    155,
    800,
    80
)

difficulty_normal_rect = pygame.Rect(
    283,
    250,
    800,
    80
)

difficulty_hard_rect = pygame.Rect(
    283,
    345,
    800,
    80
)

difficulty_very_hard_rect = pygame.Rect(
    283,
    440,
    800,
    80
)

difficulty_extreme_rect = pygame.Rect(
    283,
    535,
    800,
    80
)

difficulty_back_rect = pygame.Rect(
    533,
    665,
    300,
    50
)

avatar_selector_left_x = 1190
avatar_selector_right_x = 1275
avatar_selector_start_y = 195
avatar_selector_gap = 58

avatar_selector_left_rects = [
    pygame.Rect(
        avatar_selector_left_x,
        avatar_selector_start_y + i * avatar_selector_gap,
        45,
        40
    )
    for i in range(5)
]

avatar_selector_right_rects = [
    pygame.Rect(
        avatar_selector_right_x,
        avatar_selector_start_y + i * avatar_selector_gap,
        45,
        40
    )
    for i in range(5)
]

# ----------------------------
# Round recap buttons
# ----------------------------

recap_yes_rect = pygame.Rect(
    515,
    655,
    150,
    55
)

recap_no_rect = pygame.Rect(
    700,
    655,
    150,
    55
)

level_up_continue_rect = pygame.Rect(
    533,
    690,
    300,
    48
)

# ----------------------------
# Music mode
# ----------------------------

music_instrumental_rect = pygame.Rect(
    420,
    180,
    170,
    50
)

music_ambient_rect = pygame.Rect(
    600,
    180,
    170,
    50
)

music_off_rect = pygame.Rect(
    780,
    180,
    170,
    50
)


# ----------------------------
# Music volume
# ----------------------------

music_slider_rect = pygame.Rect(
    500,
    290,
    400,
    20
)


# ----------------------------
# SFX volume
# ----------------------------

sfx_slider_rect = pygame.Rect(
    500,
    390,
    400,
    20
)


# ----------------------------
# Double-click mode
# ----------------------------

double_foundation_rect = pygame.Rect(
    430,
    480,
    220,
    50
)

double_both_rect = pygame.Rect(
    670,
    480,
    260,
    50
)


# ----------------------------
# Solitaire deal mode
# ----------------------------

deal_random_rect = pygame.Rect(
    430,
    540,
    180,
    42
)

deal_verified_rect = pygame.Rect(
    630,
    540,
    300,
    42
)

# Temporarily keep the experimental verified-deal generator out of ordinary
# play while it is being rebuilt. Head-to-Head still uses its race-only
# constructive deal path.
VERIFIED_DEALS_ENABLED = False


# ----------------------------
# Resolution
# ----------------------------

resolution_rects = [
    pygame.Rect(
        440,
        598,
        125,
        38
    ),
    pygame.Rect(
        575,
        598,
        125,
        38
    ),
    pygame.Rect(
        710,
        598,
        125,
        38
    ),
    pygame.Rect(
        845,
        598,
        125,
        38
    ),
]


# ----------------------------
# Fullscreen
# ----------------------------

fullscreen_toggle_rect = pygame.Rect(
    760,
    646,
    210,
    38
)

# ----------------------------
# Back
# ----------------------------

options_back_rect = pygame.Rect(
    533,
    705,
    300,
    42
)

# ==================================================
# CUSTOMIZATION STATE
# ==================================================

CUSTOMIZE_BACKGROUNDS = "backgrounds"
CUSTOMIZE_FELTS = "felts"
CUSTOMIZE_TITLES = "titles"
CUSTOMIZE_CURSORS = "cursors"

customize_category = CUSTOMIZE_BACKGROUNDS
customize_page = 0

CUSTOMIZE_ITEMS_PER_PAGE = 6

# ==================================================
# STATE
# ==================================================

current_state = STATE_SPLASH

round_recap_data = None
last_progression_result = None

post_round_return_state = STATE_MENU

level_up_queue = []
current_level_up_data = None

def _render_blackjack_fit(text, max_width, size=21, bold=False, color=(255, 255, 255), minimum_size=13):
    current_size = int(size)
    while current_size >= minimum_size:
        font = pygame.font.SysFont("cambria", current_size, bold=bold)
        surface = font.render(str(text), True, color)
        if surface.get_width() <= max_width or current_size == minimum_size:
            return surface
        current_size -= 1
    return blackjack_small_font.render(str(text), True, color)


def _draw_blackjack_panel(rect, fill=(10, 28, 21, 205), border=(220, 190, 100), radius=12):
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, fill, panel.get_rect(), border_radius=radius)
    game_surface.blit(panel, rect.topleft)
    pygame.draw.rect(
        game_surface,
        border,
        rect,
        2,
        border_radius=radius
    )


def _draw_blackjack_dealer_identity(rect):
    _draw_blackjack_panel(
        rect,
        fill=(8, 24, 18, 218),
        border=(210, 220, 205),
        radius=12
    )

    heading = blackjack_small_font.render(
        "TONIGHT'S DEALER",
        True,
        (222, 190, 98)
    )
    game_surface.blit(
        heading,
        (rect.x + 14, rect.y + 12)
    )

    portrait_rect = pygame.Rect(
        rect.x + 14,
        rect.y + 44,
        88,
        88
    )

    if blackjack_dealer_npc is not None:
        draw_npc_portrait(
            blackjack_dealer_npc,
            portrait_rect,
            "blackjack"
        )
        dealer_name = blackjack_dealer_npc.get("name", "Dealer")
        hometown = blackjack_dealer_npc.get("hometown", "Unknown")
        favorite_suit = blackjack_dealer_npc.get("favorite_suit", "Unknown")
    else:
        pygame.draw.rect(game_surface, (42, 58, 49), portrait_rect)
        pygame.draw.rect(game_surface, (215, 215, 215), portrait_rect, 2)
        dealer_name = "Dealer"
        hometown = "Unknown"
        favorite_suit = "Unknown"

    portrait = game_surface.subsurface(portrait_rect).copy()
    mask = pygame.Surface(portrait_rect.size, pygame.SRCALPHA)
    pygame.draw.ellipse(mask, (255, 255, 255, 255), mask.get_rect())
    portrait = portrait.convert_alpha()
    portrait.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    pygame.draw.rect(game_surface, (13, 25, 32), portrait_rect)
    game_surface.blit(portrait, portrait_rect)
    pygame.draw.ellipse(game_surface, (207, 225, 233), portrait_rect, 2)

    name_surface = _render_blackjack_fit(
        dealer_name,
        rect.width - 126,
        size=27,
        bold=True,
        color=(255, 255, 255),
        minimum_size=17
    )
    game_surface.blit(
        name_surface,
        (rect.x + 116, rect.y + 48)
    )

    hometown_surface = _render_blackjack_fit(
        hometown,
        rect.width - 130,
        size=17,
        color=(205, 214, 208),
        minimum_size=12
    )
    game_surface.blit(
        hometown_surface,
        (rect.x + 116, rect.y + 84)
    )

    suit_surface = _render_blackjack_fit(
        f"Favorite suit: {favorite_suit}",
        rect.width - 130,
        size=17,
        color=(232, 210, 145),
        minimum_size=12
    )
    game_surface.blit(
        suit_surface,
        (rect.x + 116, rect.y + 112)
    )


def _draw_blackjack_background():
    from blackjack_presentation import draw_background
    draw_background(game_surface, menu_background_surfaces.get(selected_menu_background), felt_surfaces.get(selected_felt))


def _draw_blackjack_button(rect, label, mouse, font=None, selected=False):
    from blackjack_presentation import draw_button
    draw_button(game_surface, rect, label, mouse, font or blackjack_body_font, selected=selected)


def draw_blackjack_bet():
    _draw_blackjack_background()

    dealer_identity_rect = pygame.Rect(34, 122, 302, 164)
    _draw_blackjack_dealer_identity(dealer_identity_rect)

    bet_panel = pygame.Rect(360, 138, 650, 450)
    _draw_blackjack_panel(
        bet_panel,
        fill=(7, 31, 22, 210),
        border=(230, 205, 120),
        radius=14
    )

    cash_surface = blackjack_heading_font.render(
        f"Bankroll  ${career_cash:,}",
        True,
        (255, 228, 135)
    )
    game_surface.blit(
        cash_surface,
        cash_surface.get_rect(center=(bet_panel.centerx, 190))
    )

    prompt = blackjack_heading_font.render(
        "Choose your opening wager",
        True,
        (245, 245, 240)
    )
    game_surface.blit(
        prompt,
        prompt.get_rect(center=(bet_panel.centerx, 245))
    )

    detail = blackjack_body_font.render(
        "The percentage is calculated from your current bankroll.",
        True,
        (194, 207, 199)
    )
    game_surface.blit(
        detail,
        detail.get_rect(center=(bet_panel.centerx, 280))
    )

    if career_cash > 0:
        bet_options = [
            (blackjack_bet_1_rect, "1%", 0.01),
            (blackjack_bet_2_rect, "2%", 0.02),
            (blackjack_bet_5_rect, "5%", 0.05),
            (blackjack_bet_10_rect, "10%", 0.10),
            (blackjack_bet_all_rect, "ALL IN", 1.0),
        ]

        for rect, label_text, percentage in bet_options:
            amount = get_blackjack_bet(percentage)
            label = f"{label_text}   ${amount:,}"
            _draw_blackjack_button(
                rect,
                label,
                game_mouse_pos,
                selected=(blackjack_selected_bet_percentage == percentage),
                font=blackjack_small_font
            )
    else:
        broke_surface = blackjack_heading_font.render(
            "OUT OF CASH",
            True,
            (255, 220, 120)
        )
        game_surface.blit(
            broke_surface,
            broke_surface.get_rect(center=(bet_panel.centerx, 365))
        )

        broke_detail = blackjack_body_font.render(
            "Return to the previous screen to finish the session.",
            True,
            (210, 215, 210)
        )
        game_surface.blit(
            broke_detail,
            broke_detail.get_rect(center=(bet_panel.centerx, 410))
        )

    _draw_blackjack_button(
        blackjack_bet_return_rect,
        "Return",
        game_mouse_pos,
        font=blackjack_body_font
    )


def draw_blackjack():
    _draw_blackjack_background()

    dealer_identity_rect = pygame.Rect(28, 112, 305, 170)
    _draw_blackjack_dealer_identity(dealer_identity_rect)

    right_panel = pygame.Rect(1033, 106, 304, 530)
    _draw_blackjack_panel(
        right_panel,
        fill=(7, 26, 19, 220),
        border=(210, 220, 205),
        radius=12
    )

    # ==================================================
    # Table labels / cards
    # ==================================================

    dealer_heading = blackjack_heading_font.render(
        "DEALER",
        True,
        (245, 235, 205)
    )
    game_surface.blit(
        dealer_heading,
        dealer_heading.get_rect(center=(686, 116))
    )

    dealer_count = max(1, len(blackjack_game.dealer_hand))
    dealer_spacing = min(92, 430 // max(1, dealer_count - 1))
    dealer_total_width = 100 + max(0, dealer_count - 1) * dealer_spacing
    dealer_x = 686 - dealer_total_width // 2
    dealer_y = 145

    for index, card in enumerate(blackjack_game.dealer_hand):
        target_x = dealer_x + index * dealer_spacing
        position = get_blackjack_animated_position(
            "dealer",
            index,
            target_x,
            dealer_y
        )
        if position is None:
            continue

        x, y = position

        if index == 1:
            flip_progress = blackjack_game.get_dealer_flip_progress()

            if flip_progress is None or flip_progress <= 0.0:
                game_surface.blit(
                    game.get_card_back_surface(),
                    (x, y)
                )
                continue

            if flip_progress < 1.0:
                if flip_progress < 0.5:
                    image = game.get_card_back_surface()
                    scale_progress = 1.0 - flip_progress * 2.0
                else:
                    card_key = get_card_key(card)
                    image = game.card_fronts[card_key]
                    scale_progress = (flip_progress - 0.5) * 2.0

                original_width = image.get_width()
                original_height = image.get_height()
                scaled_width = max(1, int(original_width * scale_progress))
                scaled_image = pygame.transform.smoothscale(
                    image,
                    (scaled_width, original_height)
                )
                scaled_rect = scaled_image.get_rect(
                    center=(
                        x + original_width // 2,
                        y + original_height // 2
                    )
                )
                game_surface.blit(scaled_image, scaled_rect)
                continue

        card_key = get_card_key(card)
        game_surface.blit(
            game.card_fronts[card_key],
            (x, y)
        )

    dealer_value_text = (
        f"Dealer total: {blackjack_game.dealer_value()}"
        if blackjack_game.dealer_hole_is_revealed()
        else "Dealer total: ?"
    )
    dealer_value_surface = blackjack_body_font.render(
        dealer_value_text,
        True,
        (245, 245, 240)
    )
    dealer_value_rect = dealer_value_surface.get_rect(center=(686, 318))
    value_bg = dealer_value_rect.inflate(28, 14)
    _draw_blackjack_panel(
        value_bg,
        fill=(8, 24, 18, 205),
        border=(173, 190, 179),
        radius=8
    )
    game_surface.blit(dealer_value_surface, dealer_value_rect)

    if blackjack_game.is_split_round():
        player_heading = blackjack_heading_font.render(
            "YOUR SPLIT HANDS",
            True,
            (245, 235, 205)
        )
        game_surface.blit(
            player_heading,
            player_heading.get_rect(center=(686, 382))
        )

        split_centers = (535, 835)
        hands = blackjack_game.get_player_hands()

        for hand_index, hand in enumerate(hands):
            center_x = split_centers[hand_index]
            active = (
                not blackjack_game.round_complete
                and not blackjack_game.player_stood
                and blackjack_game.active_hand_index == hand_index
                and not blackjack_game.player_hand_done[hand_index]
            )

            hand_label = blackjack_small_font.render(
                f"HAND {hand_index + 1}",
                True,
                (255, 224, 120) if active else (215, 220, 216)
            )
            game_surface.blit(
                hand_label,
                hand_label.get_rect(center=(center_x, 408))
            )

            card_count = max(1, len(hand))
            card_spacing = min(70, 205 // max(1, card_count - 1))
            total_width = 100 + max(0, card_count - 1) * card_spacing
            start_x = center_x - total_width // 2
            card_y = 428

            for index, card in enumerate(hand):
                target_x = start_x + index * card_spacing
                position = get_blackjack_animated_position(
                    f"player_{hand_index}",
                    index,
                    target_x,
                    card_y
                )
                if position is None:
                    continue
                x, y = position
                card_key = get_card_key(card)
                game_surface.blit(game.card_fronts[card_key], (x, y))

            value = blackjack_game.get_hand_value_at(hand_index)
            wager = blackjack_game.player_hand_bets[hand_index]
            detail = blackjack_small_font.render(
                f"Total {value}   |   Bet ${wager:,}",
                True,
                (255, 232, 148) if active else (240, 240, 236)
            )
            detail_rect = detail.get_rect(center=(center_x, 594))
            detail_bg = detail_rect.inflate(20, 10)
            _draw_blackjack_panel(
                detail_bg,
                fill=(8, 24, 18, 205),
                border=(232, 198, 95) if active else (173, 190, 179),
                radius=8
            )
            game_surface.blit(detail, detail_rect)

            if blackjack_game.round_complete:
                hand_result = blackjack_game.get_hand_result(hand_index)
                result_names = {
                    "player": "WIN",
                    "push": "PUSH",
                    "dealer": "LOSS",
                }
                result_label = blackjack_small_font.render(
                    result_names.get(hand_result, ""),
                    True,
                    (255, 224, 120)
                )
                game_surface.blit(
                    result_label,
                    result_label.get_rect(center=(center_x, 625))
                )
    else:
        player_heading = blackjack_heading_font.render(
            "YOUR HAND",
            True,
            (245, 235, 205)
        )
        game_surface.blit(
            player_heading,
            player_heading.get_rect(center=(686, 390))
        )

        player_count = max(1, len(blackjack_game.player_hand))
        player_spacing = min(92, 430 // max(1, player_count - 1))
        player_total_width = 100 + max(0, player_count - 1) * player_spacing
        player_x = 686 - player_total_width // 2
        player_y = 420

        for index, card in enumerate(blackjack_game.player_hand):
            target_x = player_x + index * player_spacing
            position = get_blackjack_animated_position(
                "player",
                index,
                target_x,
                player_y
            )
            if position is None:
                continue

            x, y = position
            card_key = get_card_key(card)
            game_surface.blit(
                game.card_fronts[card_key],
                (x, y)
            )

        player_value_surface = blackjack_body_font.render(
            f"Hand total: {blackjack_game.player_value()}",
            True,
            (245, 245, 240)
        )
        player_value_rect = player_value_surface.get_rect(center=(686, 602))
        player_bg = player_value_rect.inflate(28, 14)
        _draw_blackjack_panel(
            player_bg,
            fill=(8, 24, 18, 205),
            border=(173, 190, 179),
            radius=8
        )
        game_surface.blit(player_value_surface, player_value_rect)

    # ==================================================
    # Bankroll / next wager panel
    # ==================================================

    panel_title = blackjack_heading_font.render(
        "TABLE BANK",
        True,
        (255, 225, 130)
    )
    game_surface.blit(
        panel_title,
        panel_title.get_rect(center=(right_panel.centerx, 138))
    )

    info_lines = [
        f"Current wager: ${blackjack_game.bet:,}",
        f"Cash: ${career_cash:,}",
    ]
    if blackjack_session_net > 0:
        session_text = f"Session: +${blackjack_session_net:,}"
    elif blackjack_session_net < 0:
        session_text = f"Session: -${abs(blackjack_session_net):,}"
    else:
        session_text = "Session: $0"
    info_lines.append(session_text)
    if current_game_mode == "career":
        info_lines.append(f"Casino: {career_ratings['casino']:,} ({blackjack_session_rating_change:+d})")

    for index, text in enumerate(info_lines):
        surface = blackjack_body_font.render(
            text,
            True,
            (235, 238, 235)
        )
        game_surface.blit(
            surface,
            (right_panel.x + 20, 182 + index * 34)
        )

    next_bet_heading = blackjack_heading_font.render(
        "NEXT HAND BET",
        True,
        (255, 225, 130)
    )
    game_surface.blit(
        next_bet_heading,
        next_bet_heading.get_rect(center=(right_panel.centerx, 326))
    )

    next_bet_note = blackjack_small_font.render(
        "Choose your next wager anytime.",
        True,
        (180, 196, 187)
    )
    game_surface.blit(
        next_bet_note,
        next_bet_note.get_rect(center=(right_panel.centerx, 350))
    )

    bet_choices = [
        ("1%", 0.01),
        ("2%", 0.02),
        ("5%", 0.05),
        ("10%", 0.10),
        ("ALL IN", 1.0),
    ]

    for index, (label_text, percentage) in enumerate(bet_choices):
        amount = get_blackjack_bet(percentage) if career_cash > 0 else 0
        if percentage >= 1.0:
            button_text = f"{label_text}  ${amount:,}"
        else:
            button_text = f"{label_text}  ${amount:,}"
        _draw_blackjack_button(
            blackjack_bet_dropdown_rects[index],
            button_text,
            game_mouse_pos,
            selected=(blackjack_selected_bet_percentage == percentage),
            font=blackjack_small_font
        )

    # ==================================================
    # Result / temporary dealer reveal status
    # ==================================================

    if blackjack_game.round_complete:
        net_result = blackjack_game.get_net_result()

        if blackjack_game.is_split_round():
            if net_result > 0:
                result_text = f"SPLIT HANDS  +${net_result:,}"
            elif net_result < 0:
                result_text = f"SPLIT HANDS  -${abs(net_result):,}"
            else:
                result_text = "SPLIT HANDS  EVEN"
        else:
            dealer_natural = (
                len(blackjack_game.dealer_hand) == 2
                and blackjack_game.dealer_value() == 21
            )
            player_natural = (
                len(blackjack_game.player_hand) == 2
                and blackjack_game.player_value() == 21
            )

            if blackjack_game.result == "blackjack":
                result_text = f"BLACKJACK!  +${net_result:,}"
            elif blackjack_game.result == "player":
                result_text = f"YOU WIN  +${net_result:,}"
            elif blackjack_game.result == "push" and dealer_natural and player_natural:
                result_text = "BOTH BLACKJACK - PUSH"
            elif blackjack_game.result == "push":
                result_text = "PUSH - BET RETURNED"
            elif dealer_natural:
                result_text = "DEALER BLACKJACK"
            else:
                result_text = f"DEALER WINS  ${blackjack_game.bet:,}"

        result_surface = blackjack_heading_font.render(
            result_text,
            True,
            (255, 226, 125)
        )
        result_rect = result_surface.get_rect(center=(686, 358))
        result_bg = result_rect.inflate(34, 18)
        _draw_blackjack_panel(
            result_bg,
            fill=(30, 24, 12, 225),
            border=(232, 198, 95),
            radius=9
        )
        game_surface.blit(result_surface, result_rect)

    elif blackjack_game.pending_natural_result is not None:
        reveal_surface = blackjack_body_font.render(
            "Dealer checks the hole card...",
            True,
            (244, 226, 165)
        )
        game_surface.blit(
            reveal_surface,
            reveal_surface.get_rect(center=(686, 358))
        )

    # ==================================================
    # Controls
    # ==================================================

    if (
            not blackjack_game.round_complete
            and not blackjack_game.player_stood
    ):
        _draw_blackjack_button(
            blackjack_hit_rect,
            "Hit",
            game_mouse_pos,
            font=blackjack_body_font
        )
        _draw_blackjack_button(
            blackjack_stand_rect,
            "Stand",
            game_mouse_pos,
            font=blackjack_body_font
        )
        if (
                blackjack_game.can_double_down()
                and career_cash >= blackjack_game.current_hand_bet()
        ):
            _draw_blackjack_button(
                blackjack_double_rect,
                "Double",
                game_mouse_pos,
                font=blackjack_body_font
            )

        if (
                blackjack_game.can_split()
                and career_cash >= blackjack_game.current_hand_bet()
        ):
            _draw_blackjack_button(
                blackjack_split_rect,
                "Split",
                game_mouse_pos,
                font=blackjack_body_font
            )

    elif blackjack_game.round_complete:
        if career_cash > 0:
            _draw_blackjack_button(
                blackjack_deal_again_rect,
                "Deal Next Hand",
                game_mouse_pos,
                font=blackjack_body_font
            )
        else:
            out_surface = blackjack_heading_font.render(
                "OUT OF CASH",
                True,
                (255, 220, 120)
            )
            game_surface.blit(
                out_surface,
                out_surface.get_rect(center=blackjack_deal_again_rect.center)
            )

    # Return is intentionally visible throughout the hand, but only clickable
    # after the result. The tooltip explains the disabled state.
    if blackjack_game.round_complete:
        _draw_blackjack_button(
            blackjack_return_rect,
            "Return",
            game_mouse_pos,
            font=blackjack_body_font
        )
    else:
        pygame.draw.rect(
            game_surface,
            (68, 76, 72),
            blackjack_return_rect,
            border_radius=7
        )
        pygame.draw.rect(
            game_surface,
            (145, 154, 149),
            blackjack_return_rect,
            2,
            border_radius=7
        )
        disabled = blackjack_body_font.render(
            "Return",
            True,
            (155, 160, 157)
        )
        game_surface.blit(
            disabled,
            disabled.get_rect(center=blackjack_return_rect.center)
        )

        if (
                game_mouse_pos is not None
                and blackjack_return_rect.collidepoint(game_mouse_pos)
        ):
            tooltip = blackjack_small_font.render(
                "Finish the current hand before leaving.",
                True,
                (255, 255, 255)
            )
            tooltip_rect = tooltip.get_rect(
                midbottom=(blackjack_return_rect.centerx, blackjack_return_rect.y - 8)
            )
            tooltip_bg = tooltip_rect.inflate(18, 10)
            pygame.draw.rect(
                game_surface,
                (18, 24, 21),
                tooltip_bg,
                border_radius=6
            )
            game_surface.blit(tooltip, tooltip_rect)


def grant_rating_cosmetics(force=False):
    if force or current_game_mode in ("career", "head_to_head"):
        unlock_ratings(career_ratings, (MENU_BACKGROUNDS, FELTS, TITLES),
                       (unlocked_menu_backgrounds, unlocked_felts, unlocked_titles))


def award_career_rating(rating_key, amount):
    """Apply a game reward and synchronize the derived Overall mirror."""
    global career_rating
    if current_game_mode not in ("career", "head_to_head") or rating_key not in GAME_RATING_KEYS:
        return 0
    actual = apply_rating_change(career_ratings, rating_key, amount)
    career_rating = career_ratings["overall"]
    grant_rating_cosmetics()
    return actual


def adjust_debug_ratings(amount):
    global career_rating
    for key in ("strategy", "poker", "casino"):
        apply_rating_change(career_ratings, key, amount, scale_rewards=False)
    career_rating = career_ratings["overall"]
    grant_rating_cosmetics()


def rate_competitive_game(game_key, opponent, won):
    global career_rating
    if current_game_mode not in ("career", "head_to_head"):
        return 0
    change = settle_competitive_result(
        career_ratings, career_rating_results, career_leaderboard_state,
        game_key, opponent, 1.0 if won else 0.0,
    )
    career_rating = career_ratings["overall"]
    grant_rating_cosmetics()
    sync_career_npc_runtime_state()
    return change


def preview_competitive_rating(game_key, opponent, won):
    if current_game_mode not in ("career", "head_to_head") or not isinstance(opponent, dict):
        return 0
    state = career_leaderboard_state.get(opponent.get("id"), {})
    bundle = state.get("ratings") or opponent.get("career_ratings") or opponent.get("ratings") or {}
    opponent_rating = bundle.get(game_key, opponent.get("race_rating", opponent.get("rating", 1000)))
    requested = elo_delta(career_ratings[game_key], opponent_rating, 1 if won else 0)
    if game_key == "score_four":
        requested = {"low":45, "mid":60, "strong":50, "elite":65}.get(opponent.get("skill_tier"),60) if won else -10
    from career_ratings import reward_scale
    if requested > 0: requested *= reward_scale(career_ratings[game_key])

    return int(round(max(100, career_ratings[game_key] + requested))) - int(round(career_ratings[game_key]))


def rate_house_game(game_key, net):
    global career_rating
    if current_game_mode != "career":
        return 0
    change = settle_house_result(career_ratings, career_rating_results, game_key, net)
    career_rating = career_ratings["overall"]
    grant_rating_cosmetics()
    return change


def rate_poker_cash_out(game_key, poker_game):
    global career_rating
    if current_game_mode != "career":
        return 0
    change = settle_poker_session(
        career_ratings, career_rating_results, career_leaderboard_state,
        game_key, poker_game,
    )
    career_rating = career_ratings["overall"]
    grant_rating_cosmetics()
    sync_career_npc_runtime_state()
    return change



def award_career_fans(amount, reason=""):
    global career_fans
    global career_last_fan_change
    global career_last_fan_reason
    global career_fan_news_milestones

    try:
        amount = int(round(amount))
    except (TypeError, ValueError):
        return 0

    before = int(career_fans)
    career_fans = clamp_fans(before + amount)
    actual = career_fans - before

    career_last_fan_change = actual
    career_last_fan_reason = str(reason or "")

    if actual > 0:
        milestone_labels = (
            (1_000, "1,000"),
            (10_000, "10,000"),
            (50_000, "50,000"),
            (100_000, "100,000"),
            (250_000, "250,000"),
            (500_000, "500,000"),
            (1_000_000, "1,000,000"),
        )
        for milestone, label in milestone_labels:
            if (
                    before < milestone <= career_fans
                    and milestone not in career_fan_news_milestones
            ):
                career_fan_news_milestones.add(milestone)
                add_career_news(
                    f"{player_name.upper()} SURPASSES {label} FANS",
                    (
                        f"{player_name} has crossed the {label}-fan mark. "
                        f"The latest surge followed {reason.lower() if reason else 'recent competition'}."
                    ),
                    "fans"
                )

    return actual


def award_fans_for_rating_win(rating_gain, reason="Game win"):
    gain = fan_gain_from_rating_win(
        rating_gain,
        current_rating=career_rating
    )
    return award_career_fans(gain, reason)


def award_fans_for_cash_win(net_win, reason="Casino win"):
    gain = fan_gain_from_cash_win(
        net_win,
        current_rating=career_rating
    )
    return award_career_fans(gain, reason)


def lose_fans_for_bad_result(reason="Poor performance", net_loss=0, severity=1.0):
    loss = fan_loss_from_bad_result(
        current_fans=career_fans,
        net_loss=net_loss,
        severity=severity,
    )
    if loss <= 0:
        return 0
    return award_career_fans(-loss, reason)


# XP values intentionally stay modest because many of these games can be
# played repeatedly inside one Career event.  Solitaire keeps its score-based
# XP system; everything else now contributes to profile progression too.
GAME_XP_VALUES = {
    "crazy_eights": (45, 90),
    "bango": (30, 65),
    "score_four_solo": (55, 85),
    "score_four_competitive": (55, 105),
    "blackjack": (18, 38),
    "roulette": (15, 32),
    "horse_races": (20, 42),
    "faro": (55, 95),
    "five_o_poker": (60, 110),
    "blind_mans_bluff": (60, 110),
    "texas_holdem": (70, 125),
    "five_card_draw": (65, 115),
    "seven_card_stud": (70, 125),
    "head_to_head": (65, 135),
}


def award_game_xp(game_id, won=False, bonus=0):
    values = GAME_XP_VALUES.get(game_id, (25, 50))
    amount = values[1] if won else values[0]
    amount = max(1, int(amount) + int(bonus or 0))
    result = add_player_xp(amount)
    if result.get("level_up_screens"):
        level_up_queue.extend(result["level_up_screens"])
    return amount


def award_achievement_fans(difficulty="normal", achievement_name="Achievement"):
    return award_career_fans(
        fan_bonus_for_achievement(difficulty),
        f"Achievement: {achievement_name}"
    )


def unlock_achievement_cosmetic(reward):
    reward_type = reward.get("type")
    asset_id = reward.get("id")
    if not asset_id:
        return ""

    if reward_type == "background":
        if asset_id in MENU_BACKGROUNDS:
            unlocked_menu_backgrounds.add(asset_id)
            return MENU_BACKGROUNDS[asset_id].get("name", asset_id)
        return ""

    if reward_type == "felt":
        if asset_id in FELTS:
            unlocked_felts.add(asset_id)
            return FELTS[asset_id].get("name", asset_id)
        return ""

    if reward_type == "title":
        if asset_id in TITLES:
            unlocked_titles.add(asset_id)
            return TITLES[asset_id].get("name", asset_id)
        return ""

    return ""


def sync_achievement_cosmetic_rewards():
    for achievement_id in achievement_state.get("unlocked", []):
        definition = get_achievement_definition(achievement_id)
        if not definition:
            continue
        for reward in iter_achievement_rewards(definition):
            unlock_achievement_cosmetic(reward)


def queue_achievement_popup(definition, fan_reward, cosmetic_label=""):
    achievement_popup_queue.append({
        "definition": definition,
        "fans": int(fan_reward or 0),
        "cosmetic": str(cosmetic_label or ""),
    })


def process_achievement_event(event_name, **data):
    global achievement_state
    global free_play_achievement_fans_earned

    achievement_state, newly_unlocked = record_achievement_event(
        achievement_state,
        event_name,
        **data
    )

    for definition in newly_unlocked:
        if current_game_mode == "free":
            fan_reward = fan_bonus_for_achievement(
                definition.get("difficulty", "normal")
            )
            free_play_achievement_fans_earned += fan_reward
        else:
            fan_reward = award_achievement_fans(
                definition.get("difficulty", "normal"),
                definition.get("title", "Achievement"),
            )

        cosmetic_labels = []
        for reward in iter_achievement_rewards(definition):
            label = unlock_achievement_cosmetic(reward)
            if label:
                cosmetic_labels.append(label)

        queue_achievement_popup(
            definition,
            fan_reward,
            ", ".join(cosmetic_labels),
        )

    if newly_unlocked and current_game_mode != "free":
        auto_save_career()

    return newly_unlocked


def debug_unlock_next_achievement():
    unlocked = set(achievement_state.get("unlocked", []))
    for definition in ACHIEVEMENT_DEFINITIONS:
        if definition["id"] in unlocked:
            continue

        achievement_state.setdefault("unlocked", []).append(definition["id"])
        fan_reward = award_achievement_fans(
            definition.get("difficulty", "normal"),
            definition.get("title", "Achievement"),
        )
        cosmetic_labels = []
        for reward in iter_achievement_rewards(definition):
            label = unlock_achievement_cosmetic(reward)
            if label:
                cosmetic_labels.append(label)
        queue_achievement_popup(
            definition,
            fan_reward,
            ", ".join(cosmetic_labels),
        )
        auto_save_career()
        return definition.get("title", "Achievement")

    return None


def update_achievement_popup():
    global achievement_popup_current
    global achievement_popup_started
    global achievement_popup_fans
    global achievement_popup_cosmetic

    now = pygame.time.get_ticks()

    if achievement_popup_current is not None:
        if now - achievement_popup_started >= 4400:
            achievement_popup_current = None

    if achievement_popup_current is None and achievement_popup_queue:
        item = achievement_popup_queue.pop(0)
        achievement_popup_current = item["definition"]
        achievement_popup_fans = item["fans"]
        achievement_popup_cosmetic = item["cosmetic"]
        achievement_popup_started = now


def get_holdem_player_winnings():
    total = 0
    for award in getattr(texas_holdem_game, "last_pot_awards", []):
        winners = list(award.get("winners", []))
        if 0 not in winners or not winners:
            continue
        ordered = sorted(winners)
        share = int(award.get("share", 0) or 0)
        remainder = int(award.get("remainder", 0) or 0)
        player_share = share
        if ordered.index(0) < remainder:
            player_share += 1
        total += player_share
    return total


def post_texas_holdem_chat(
        chat_entry
):

    if not chat_entry:
        return

    speaker, message = (
        chat_entry
    )

    add_holdem_chat_message(
        speaker,
        message
    )

def process_texas_holdem_showdown():

    global career_rating
    global career_event_has_activity

    global texas_holdem_hand_win_sound_at

    global texas_holdem_last_processed_showdown_hand

    global texas_holdem_next_hand_at
    global texas_holdem_session_end_at
    global texas_holdem_table_sweep_rewarded

    # ==================================================
    # Only process completed showdowns
    # ==================================================

    if not texas_holdem_game.hand_complete:
        return

    if (
            texas_holdem_game.current_stage
            != "showdown"
    ):
        return

    # ==================================================
    # Don't process the same showdown every frame
    # ==================================================

    if (
            texas_holdem_game.hand_number
            == texas_holdem_last_processed_showdown_hand
    ):
        return

    texas_holdem_last_processed_showdown_hand = (
        texas_holdem_game.hand_number
    )
    record_poker_showdown(texas_holdem_game)

    # ==================================================
    # SHOWDOWN AUDIO
    # ==================================================

    audio.play_sound(
        "card_flip"
    )

    # Player won at least one pot.
    if 0 in texas_holdem_game.winner_indexes:
        texas_holdem_hand_win_sound_at = (
                pygame.time.get_ticks()
                + 450
        )
        award_fans_for_cash_win(
            max(1, int(getattr(texas_holdem_game, "last_resolved_pot", 0))),
            "Hold'em hand win"
        )

        holdem_result = texas_holdem_game.get_showdown_result(0)
        holdem_score = holdem_result[0] if holdem_result else None
        process_achievement_event(
            "holdem_hand_win",
            winnings=get_holdem_player_winnings(),
            category=(holdem_score[0] if holdem_score else None),
            high=(holdem_score[1] if holdem_score and len(holdem_score) > 1 else None),
        )

    # ==================================================
    # NPC showdown / knockout chat
    # ==================================================

    showdown_messages = (
        generate_showdown_chat(
            texas_holdem_game
        )
    )

    for chat_entry in showdown_messages:

        post_texas_holdem_chat(
            chat_entry
        )

    # ==================================================
    # PLAYER BUSTED
    # ==================================================

    if texas_holdem_game.player_busted:

        texas_holdem_next_hand_at = 0

        texas_holdem_game.result_text += (
            " You are out of chips."
        )

        texas_holdem_session_end_at = (
            pygame.time.get_ticks()
            + TEXAS_HOLDEM_SESSION_END_DELAY
        )

        return

    # ==================================================
    # PLAYER CLEARED THE TABLE
    # ==================================================

    if texas_holdem_game.all_npcs_busted():

        texas_holdem_next_hand_at = 0

        fan_gain = 0

        if not texas_holdem_table_sweep_rewarded:
            process_achievement_event("poker_table_clear", game="texas_holdem")
            if current_game_mode == "career":
                fan_gain = award_fans_for_rating_win(
                    TEXAS_HOLDEM_TABLE_SWEEP_RATING_BONUS,
                    "Hold'em table clear"
                )
                career_event_has_activity = True
            texas_holdem_table_sweep_rewarded = True

        texas_holdem_game.result_text += " TABLE CLEARED!"
        if current_game_mode == "career":
            texas_holdem_game.result_text += (
                " Rating settles on cash-out. "
                f"+{fan_gain:,} Fans."
            )

        texas_holdem_session_end_at = (
            pygame.time.get_ticks()
            + TEXAS_HOLDEM_SESSION_END_DELAY
        )

# ==================================================
# TEXAS HOLD'EM AUDIO HELPERS
# ==================================================

def play_texas_holdem_npc_action_sound(
        npc_index
):

    if not (
            0
            <= npc_index
            < len(
                texas_holdem_game.npc_action_texts
            )
    ):
        return

    action_text = (
        texas_holdem_game
        .npc_action_texts[
            npc_index
        ]
        .strip()
        .lower()
    )

    # ------------------------------------------
    # Check
    # ------------------------------------------

    if action_text.startswith(
            "checked"
    ):

        audio.play_sound(
            "poker_check"
        )

        return

    # ------------------------------------------
    # Chips moving
    # ------------------------------------------

    if action_text.startswith(
            (
                "called",
                "bet",
                "raised",
            )
    ):

        play_texas_holdem_chip_sound()


def play_texas_holdem_new_hand_sound():

    audio.play_sound(
        "card_draw"
    )


def play_texas_holdem_street_sound():

    audio.play_sound(
        "card_draw"
    )

# ==================================================
# TEXAS HOLD'EM AUDIO HELPERS
# ==================================================

def play_texas_holdem_chip_sound():

    sound_name = random.choice(
        (
            "poker_chips_1",
            "poker_chips_2",
            "poker_chips_3",
        )
    )

    audio.play_sound(
        sound_name
    )


def play_texas_holdem_npc_action_sound(
        npc_index
):

    if not (
            0
            <= npc_index
            < len(
                texas_holdem_game.npc_action_texts
            )
    ):
        return

    action_text = (
        texas_holdem_game
        .npc_action_texts[
            npc_index
        ]
        .strip()
        .lower()
    )

    # Check
    if action_text.startswith(
            "checked"
    ):

        audio.play_sound(
            "poker_check"
        )

        return

    # Bet / Call / Raise
    if action_text.startswith(
            (
                "called",
                "bet",
                "raised",
            )
    ):

        play_texas_holdem_chip_sound()


def play_texas_holdem_new_hand_sound():

    audio.play_sound(
        "card_draw"
    )


def play_texas_holdem_street_sound():

    audio.play_sound(
        "card_draw"
    )


# ==================================================
# SCHEDULE NEXT NPC ACTION
# ==================================================

def debug_setup_holdem_heads_up():

    global texas_holdem_next_npc_action_at
    global texas_holdem_round_advance_at
    global texas_holdem_next_hand_at
    global texas_holdem_session_end_at

    if not texas_holdem_game.npcs:
        return

    # ==================================================
    # We add the ante here because start_hand() will
    # immediately deduct it.
    #
    # Result after ante:
    # Player = $10,000
    # NPC 0  = $3,000
    # ==================================================

    ante = max(
        0,
        texas_holdem_game.ante
    )

    texas_holdem_game.player_stack = (
        10000 + ante
    )

    texas_holdem_game.npc_stacks = [
        0
        for _ in texas_holdem_game.npcs
    ]

    texas_holdem_game.npc_stacks[0] = (
        3000 + ante
    )

    # ==================================================
    # Clear persistent state
    # ==================================================

    texas_holdem_game.player_busted = False

    texas_holdem_game.npc_busted = [
        False
        for _ in texas_holdem_game.npcs
    ]

    texas_holdem_game.player_all_in = False

    texas_holdem_game.npc_all_in = [
        False
        for _ in texas_holdem_game.npcs
    ]

    texas_holdem_game.player_folded = False

    texas_holdem_game.npc_folded = [
        False
        for _ in texas_holdem_game.npcs
    ]

    # Recalculate who is actually busted.
    texas_holdem_game.refresh_busted_state()

    # ==================================================
    # Cancel old scheduled actions
    # ==================================================

    texas_holdem_next_npc_action_at = 0
    texas_holdem_round_advance_at = 0
    texas_holdem_next_hand_at = 0
    texas_holdem_session_end_at = 0

    # ==================================================
    # Fresh hand
    # ==================================================

    texas_holdem_game.start_hand()

    play_texas_holdem_new_hand_sound()

    print(
        "HOLDEM DEBUG HEADS-UP:",
        "Player =",
        texas_holdem_game.player_stack,
        "|",
        texas_holdem_game.npcs[0]["name"],
        "=",
        texas_holdem_game.npc_stacks[0]
    )

def schedule_texas_holdem_npc_action():

    global texas_holdem_next_npc_action_at

    if (
            not texas_holdem_game.hand_complete
            and not texas_holdem_game.betting_round_complete
            and texas_holdem_game.current_actor != 0
    ):
        texas_holdem_next_npc_action_at = (
                pygame.time.get_ticks()
                + get_holdem_npc_delay()
        )

def get_texas_holdem_opponents():

    opponents = []
    used_ids = []

    while len(opponents) < 4:

        npc = get_random_npc(
            exclude_ids=used_ids
        )

        if npc is None:
            break

        opponents.append(
            npc
        )

        used_ids.append(
            npc["id"]
        )

    return opponents

def start_texas_holdem_session(
        starting_stack=None,
        opponents=None
):

    global career_cash

    global texas_holdem_starting_stack
    global texas_holdem_session_net
    global texas_holdem_buy_in_active

    global career_event_has_activity
    global current_state

    global texas_holdem_next_npc_action_at
    global texas_holdem_round_advance_at
    global texas_holdem_next_hand_at
    global texas_holdem_last_processed_showdown_hand

    # ==================================================
    # Determine / validate buy-in
    # ==================================================

    if starting_stack is None:

        # Debug/direct-entry fallback.
        starting_stack = (
            get_poker_starting_stack()
        )

    starting_stack = int(
        starting_stack
    )

    starting_stack = min(
        starting_stack,
        career_cash
    )

    if (
            starting_stack
            < TEXAS_HOLDEM_MIN_BUY_IN
    ):

        print(
            "Not enough cash to enter Poker Night."
        )

        return False

    # ==================================================
    # Ante scales from selected buy-in
    # ==================================================

    ante = (
        get_poker_ante(
            starting_stack,
            high_stakes=False
        )
    )

    # ==================================================
    # Choose opponents
    # ==================================================

    if opponents is None:
        opponents = get_texas_holdem_opponents()
    else:
        opponents = list(opponents)[:4]

    if len(opponents) < 4:

        print(
            "Could not find four Hold'em opponents."
        )

        return False

    # ==================================================
    # Career cash -> poker stack
    # ==================================================

    career_cash -= (
        starting_stack
    )

    texas_holdem_starting_stack = (
        starting_stack
    )

    texas_holdem_session_net = 0

    texas_holdem_buy_in_active = True
    texas_holdem_game.session_xp_rewarded = False
    texas_holdem_last_processed_showdown_hand = 0

    # ==================================================
    # Reset runtime timers
    # ==================================================

    texas_holdem_next_npc_action_at = 0
    texas_holdem_round_advance_at = 0
    texas_holdem_next_hand_at = 0

    # ==================================================
    # Start poker session
    # ==================================================

    texas_holdem_game.career_session_rated = current_game_mode == "career"
    texas_holdem_game.learning_store = globals().get("career_poker_learning") if current_game_mode == "career" else None
    texas_holdem_game.start_session(
        opponents,
        starting_stack,
        ante
    )

    if texas_holdem_game.start_hand():

        play_texas_holdem_new_hand_sound()

    career_event_has_activity = True

    current_state = (
        STATE_TEXAS_HOLDEM
    )

    return True

def finish_texas_holdem_session():

    global career_cash

    global texas_holdem_hand_win_sound_at

    global texas_holdem_session_net
    global texas_holdem_buy_in_active

    global career_event_has_activity
    global current_state

    if texas_holdem_buy_in_active:

        career_cash += (
            texas_holdem_game.player_stack
        )

        texas_holdem_session_net = (
            texas_holdem_game.player_stack
            - texas_holdem_starting_stack
        )

        texas_holdem_buy_in_active = False
        track_night_cash(globals(), "texas_holdem", texas_holdem_session_net)
        rate_poker_cash_out("texas_holdem", texas_holdem_game)

    if (
            texas_holdem_game.current_stage
            != "ready"
    ):

        career_event_has_activity = True

    texas_holdem_hand_win_sound_at = 0

    if (
            len(getattr(texas_holdem_game, "rating_seen_hands", ())) > 0
            and not getattr(texas_holdem_game, "session_xp_rewarded", False)
    ):
        won_session = texas_holdem_session_net > 0
        award_game_xp("texas_holdem", won=won_session)
        if current_game_mode == "career" and texas_holdem_session_net < 0:
            lose_fans_for_bad_result(
                "Rough Hold'em session",
                net_loss=abs(texas_holdem_session_net),
            )
        texas_holdem_game.session_xp_rewarded = True

    if current_game_mode == "free":
        finish_free_play_sandbox()
        current_state = STATE_FREE_PLAY_SELECT
    else:
        current_state = STATE_CAREER_EVENT_SELECT
        auto_save_career()

# ==================================================
# FIVE-CARD DRAW HELPERS
# ==================================================

def post_five_card_draw_chat(
        chat_entry
):

    if not chat_entry or not is_holdem_table_chat_enabled():
        return

    speaker, message = chat_entry

    add_five_card_draw_chat_message(
        speaker,
        message
    )


def get_five_card_draw_opponents():

    opponents = []
    used_ids = []

    while len(opponents) < 4:

        npc = get_random_npc(
            exclude_ids=used_ids
        )

        if npc is None:
            break

        opponents.append(npc)
        used_ids.append(
            npc["id"]
        )

    return opponents


def schedule_five_card_draw_npc_action():

    global five_card_draw_next_npc_action_at

    if (
            not five_card_draw_game.hand_complete
            and five_card_draw_game.current_stage
            in (
                "preflop",
                "post_draw",
            )
            and not five_card_draw_game.betting_round_complete
            and five_card_draw_game.current_actor
            not in (
                0,
                -1,
            )
    ):
        five_card_draw_next_npc_action_at = (
                pygame.time.get_ticks()
                + get_holdem_npc_delay()
        )


def start_five_card_draw_session(
        starting_stack=None,
        opponents=None
):

    global career_cash

    global five_card_draw_starting_stack
    global five_card_draw_session_net
    global five_card_draw_buy_in_active

    global five_card_draw_next_npc_action_at
    global five_card_draw_round_advance_at
    global five_card_draw_next_hand_at
    global five_card_draw_session_end_at
    global five_card_draw_last_processed_showdown_hand
    global five_card_draw_table_sweep_rewarded
    global five_card_draw_hand_win_sound_at

    global career_event_has_activity
    global current_state

    if starting_stack is None:
        starting_stack = (
            get_poker_starting_stack()
        )

    starting_stack = int(
        starting_stack
    )

    starting_stack = min(
        starting_stack,
        career_cash
    )

    if (
            starting_stack
            < FIVE_CARD_DRAW_MIN_BUY_IN
    ):
        print(
            "Not enough cash to enter Five-Card Draw."
        )
        return False

    blind_unit = get_poker_ante(
        starting_stack,
        high_stakes=False
    )

    if opponents is None:
        opponents = get_five_card_draw_opponents()
    else:
        opponents = list(opponents)[:4]

    if len(opponents) < 4:
        print(
            "Could not find four Five-Card Draw opponents."
        )
        return False

    career_cash -= (
        starting_stack
    )

    five_card_draw_starting_stack = (
        starting_stack
    )

    five_card_draw_session_net = 0
    five_card_draw_buy_in_active = True
    five_card_draw_game.session_xp_rewarded = False

    five_card_draw_next_npc_action_at = 0
    five_card_draw_round_advance_at = 0
    five_card_draw_next_hand_at = 0
    five_card_draw_session_end_at = 0
    five_card_draw_last_processed_showdown_hand = 0
    five_card_draw_table_sweep_rewarded = False
    five_card_draw_hand_win_sound_at = 0

    reset_five_card_draw_ui_session()

    five_card_draw_game.career_session_rated = current_game_mode == "career"
    five_card_draw_game.learning_store = globals().get("career_poker_learning") if current_game_mode == "career" else None
    five_card_draw_game.start_session(
        opponents,
        starting_stack,
        blind_unit
    )

    if five_card_draw_game.start_hand():
        audio.play_sound(
            "card_draw"
        )

    career_event_has_activity = True

    current_state = (
        STATE_FIVE_CARD_DRAW
    )

    return True


def finish_five_card_draw_session():

    global career_cash

    global five_card_draw_session_net
    global five_card_draw_buy_in_active
    global five_card_draw_hand_win_sound_at

    global five_card_draw_next_npc_action_at
    global five_card_draw_round_advance_at
    global five_card_draw_next_hand_at
    global five_card_draw_session_end_at

    global career_event_has_activity
    global current_state

    if five_card_draw_buy_in_active:

        career_cash += (
            five_card_draw_game.player_stack
        )

        five_card_draw_session_net = (
                five_card_draw_game.player_stack
                - five_card_draw_starting_stack
        )

        five_card_draw_buy_in_active = False
        track_night_cash(globals(), "five_card_draw", five_card_draw_session_net)
        rate_poker_cash_out("five_card_draw", five_card_draw_game)

    if (
            five_card_draw_game.current_stage
            != "ready"
    ):
        career_event_has_activity = True

    five_card_draw_hand_win_sound_at = 0

    five_card_draw_next_npc_action_at = 0
    five_card_draw_round_advance_at = 0
    five_card_draw_next_hand_at = 0
    five_card_draw_session_end_at = 0

    if (
            len(getattr(five_card_draw_game, "rating_seen_hands", ())) > 0
            and not getattr(five_card_draw_game, "session_xp_rewarded", False)
    ):
        won_session = five_card_draw_session_net > 0
        award_game_xp("five_card_draw", won=won_session)
        if current_game_mode == "career" and five_card_draw_session_net < 0:
            lose_fans_for_bad_result(
                "Rough Five-Card Draw session",
                net_loss=abs(five_card_draw_session_net),
            )
        five_card_draw_game.session_xp_rewarded = True

    if current_game_mode == "free":
        finish_free_play_sandbox()
        current_state = STATE_FREE_PLAY_SELECT
    else:
        current_state = STATE_CAREER_EVENT_SELECT
        auto_save_career()


def play_five_card_draw_npc_action_sound(
        npc_index
):

    if not (
            0 <= npc_index
            < len(
                five_card_draw_game.npc_action_texts
            )
    ):
        return

    action_text = (
        five_card_draw_game
        .npc_action_texts[npc_index]
        .strip()
        .lower()
    )

    if action_text.startswith(
            "checked"
    ):
        audio.play_sound(
            "poker_check"
        )
        return

    if action_text.startswith(
            (
                "called",
                "bet",
                "raised",
            )
    ):
        play_texas_holdem_chip_sound()


def process_five_card_draw_showdown():

    global career_rating
    global career_event_has_activity

    global five_card_draw_hand_win_sound_at
    global five_card_draw_last_processed_showdown_hand
    global five_card_draw_next_hand_at
    global five_card_draw_session_end_at
    global five_card_draw_table_sweep_rewarded

    if not five_card_draw_game.hand_complete:
        return

    if (
            five_card_draw_game.current_stage
            != "showdown"
    ):
        return

    if (
            five_card_draw_game.hand_number
            == five_card_draw_last_processed_showdown_hand
    ):
        return

    five_card_draw_last_processed_showdown_hand = (
        five_card_draw_game.hand_number
    )
    record_poker_showdown(five_card_draw_game)

    audio.play_sound(
        "card_flip"
    )

    if 0 in five_card_draw_game.winner_indexes:
        five_card_draw_hand_win_sound_at = (
                pygame.time.get_ticks()
                + 450
        )
        award_fans_for_cash_win(
            max(1, int(getattr(five_card_draw_game, "last_resolved_pot", 0))),
            "Five-Card Draw hand win"
        )

    showdown_messages = (
        generate_showdown_chat(
            five_card_draw_game
        )
    )

    for chat_entry in showdown_messages:
        post_five_card_draw_chat(
            chat_entry
        )

    if five_card_draw_game.player_busted:

        five_card_draw_next_hand_at = 0

        if (
                "out of chips"
                not in five_card_draw_game.result_text.lower()
        ):
            five_card_draw_game.result_text += (
                " You are out of chips."
            )

        five_card_draw_session_end_at = (
                pygame.time.get_ticks()
                + FIVE_CARD_DRAW_SESSION_END_DELAY
        )

        return

    if five_card_draw_game.all_npcs_busted():

        five_card_draw_next_hand_at = 0

        fan_gain = 0

        if not five_card_draw_table_sweep_rewarded:
            process_achievement_event("poker_table_clear", game="five_card_draw")
            if current_game_mode == "career":
                fan_gain = award_fans_for_rating_win(
                    FIVE_CARD_DRAW_TABLE_SWEEP_RATING_BONUS,
                    "Five-Card Draw table clear"
                )
                career_event_has_activity = True
            five_card_draw_table_sweep_rewarded = True

        five_card_draw_game.result_text += " TABLE CLEARED!"
        if current_game_mode == "career":
            five_card_draw_game.result_text += (
                " Rating settles on cash-out. "
                f"+{fan_gain:,} Fans."
            )

        five_card_draw_session_end_at = (
                pygame.time.get_ticks()
                + FIVE_CARD_DRAW_SESSION_END_DELAY
        )



# ==================================================
# SEVEN-CARD STUD HELPERS
# ==================================================

def post_seven_card_stud_chat(
        chat_entry
):
    if not chat_entry or not is_holdem_table_chat_enabled():
        return

    speaker, message = chat_entry

    add_seven_card_stud_chat_message(
        speaker,
        message
    )


def get_seven_card_stud_opponents():
    opponents = []
    used_ids = []

    while len(opponents) < 4:
        npc = get_random_npc(
            exclude_ids=used_ids
        )

        if npc is None:
            break

        opponents.append(
            npc
        )

        used_ids.append(
            npc["id"]
        )

    return opponents


def schedule_seven_card_stud_npc_action():
    global seven_card_stud_next_npc_action_at

    if (
            not seven_card_stud_game.hand_complete
            and seven_card_stud_game.current_stage
            in seven_card_stud_game.STUD_STAGES
            and not seven_card_stud_game.betting_round_complete
            and seven_card_stud_game.current_actor
            not in (
                0,
                -1,
            )
    ):
        seven_card_stud_next_npc_action_at = (
                pygame.time.get_ticks()
                + get_holdem_npc_delay()
        )


def start_seven_card_stud_session(
        starting_stack=None,
        opponents=None
):
    global career_cash

    global seven_card_stud_starting_stack
    global seven_card_stud_session_net
    global seven_card_stud_buy_in_active

    global seven_card_stud_next_npc_action_at
    global seven_card_stud_round_advance_at
    global seven_card_stud_next_hand_at
    global seven_card_stud_session_end_at
    global seven_card_stud_last_processed_showdown_hand
    global seven_card_stud_table_sweep_rewarded
    global seven_card_stud_hand_win_sound_at

    global career_event_has_activity
    global current_state

    if starting_stack is None:
        starting_stack = (
            get_poker_starting_stack()
        )

    starting_stack = int(
        starting_stack
    )

    starting_stack = min(
        starting_stack,
        career_cash
    )

    if (
            starting_stack
            < SEVEN_CARD_STUD_MIN_BUY_IN
    ):
        print(
            "Not enough cash to enter Seven-Card Stud."
        )
        return False

    base_unit = get_poker_ante(
        starting_stack,
        high_stakes=False
    )

    if opponents is None:
        opponents = get_seven_card_stud_opponents()
    else:
        opponents = list(opponents)[:4]

    if len(opponents) < 4:
        print(
            "Could not find four Seven-Card Stud opponents."
        )
        return False

    career_cash -= (
        starting_stack
    )

    seven_card_stud_starting_stack = (
        starting_stack
    )

    seven_card_stud_session_net = 0
    seven_card_stud_buy_in_active = True
    seven_card_stud_game.session_xp_rewarded = False

    seven_card_stud_next_npc_action_at = 0
    seven_card_stud_round_advance_at = 0
    seven_card_stud_next_hand_at = 0
    seven_card_stud_session_end_at = 0
    seven_card_stud_last_processed_showdown_hand = 0
    seven_card_stud_table_sweep_rewarded = False
    seven_card_stud_hand_win_sound_at = 0

    reset_seven_card_stud_ui_session()

    seven_card_stud_game.career_session_rated = current_game_mode == "career"
    seven_card_stud_game.learning_store = globals().get("career_poker_learning") if current_game_mode == "career" else None
    seven_card_stud_game.start_session(
        opponents,
        starting_stack,
        base_unit
    )

    if seven_card_stud_game.start_hand():
        audio.play_sound(
            "card_draw"
        )

    career_event_has_activity = True

    current_state = (
        STATE_SEVEN_CARD_STUD
    )

    return True


def finish_seven_card_stud_session():
    global career_cash

    global seven_card_stud_session_net
    global seven_card_stud_buy_in_active
    global seven_card_stud_hand_win_sound_at

    global seven_card_stud_next_npc_action_at
    global seven_card_stud_round_advance_at
    global seven_card_stud_next_hand_at
    global seven_card_stud_session_end_at

    global career_event_has_activity
    global current_state

    if seven_card_stud_buy_in_active:
        career_cash += (
            seven_card_stud_game.player_stack
        )

        seven_card_stud_session_net = (
                seven_card_stud_game.player_stack
                - seven_card_stud_starting_stack
        )

        seven_card_stud_buy_in_active = False
        track_night_cash(globals(), "seven_card_stud", seven_card_stud_session_net)
        rate_poker_cash_out("seven_card_stud", seven_card_stud_game)

    if (
            seven_card_stud_game.current_stage
            != "ready"
    ):
        career_event_has_activity = True

    seven_card_stud_hand_win_sound_at = 0

    seven_card_stud_next_npc_action_at = 0
    seven_card_stud_round_advance_at = 0
    seven_card_stud_next_hand_at = 0
    seven_card_stud_session_end_at = 0

    if (
            len(getattr(seven_card_stud_game, "rating_seen_hands", ())) > 0
            and not getattr(seven_card_stud_game, "session_xp_rewarded", False)
    ):
        won_session = seven_card_stud_session_net > 0
        award_game_xp("seven_card_stud", won=won_session)
        if current_game_mode == "career" and seven_card_stud_session_net < 0:
            lose_fans_for_bad_result(
                "Rough Seven-Card Stud session",
                net_loss=abs(seven_card_stud_session_net),
            )
        seven_card_stud_game.session_xp_rewarded = True

    if current_game_mode == "free":
        finish_free_play_sandbox()
        current_state = STATE_FREE_PLAY_SELECT
    else:
        current_state = STATE_CAREER_EVENT_SELECT
        auto_save_career()


def play_seven_card_stud_npc_action_sound(
        npc_index
):
    if not (
            0 <= npc_index
            < len(
                seven_card_stud_game.npc_action_texts
            )
    ):
        return

    action_text = (
        seven_card_stud_game
        .npc_action_texts[npc_index]
        .strip()
        .lower()
    )

    if action_text.startswith(
            "checked"
    ):
        audio.play_sound(
            "poker_check"
        )
        return

    if action_text.startswith(
            (
                "called",
                "bet",
                "raised",
                "bring-in",
            )
    ):
        play_texas_holdem_chip_sound()


def process_seven_card_stud_showdown():
    global career_rating
    global career_event_has_activity

    global seven_card_stud_hand_win_sound_at
    global seven_card_stud_last_processed_showdown_hand
    global seven_card_stud_next_hand_at
    global seven_card_stud_session_end_at
    global seven_card_stud_table_sweep_rewarded

    if not seven_card_stud_game.hand_complete:
        return

    if (
            seven_card_stud_game.current_stage
            != "showdown"
    ):
        return

    if (
            seven_card_stud_game.hand_number
            == seven_card_stud_last_processed_showdown_hand
    ):
        return

    seven_card_stud_last_processed_showdown_hand = (
        seven_card_stud_game.hand_number
    )
    record_poker_showdown(seven_card_stud_game)

    audio.play_sound(
        "card_flip"
    )

    if 0 in seven_card_stud_game.winner_indexes:
        seven_card_stud_hand_win_sound_at = (
                pygame.time.get_ticks()
                + 450
        )
        award_fans_for_cash_win(
            max(1, int(getattr(seven_card_stud_game, "last_resolved_pot", 0))),
            "Seven-Card Stud hand win"
        )

    showdown_messages = (
        generate_showdown_chat(
            seven_card_stud_game
        )
    )

    for chat_entry in showdown_messages:
        post_seven_card_stud_chat(
            chat_entry
        )

    if seven_card_stud_game.player_busted:
        seven_card_stud_next_hand_at = 0

        if (
                "out of chips"
                not in seven_card_stud_game.result_text.lower()
        ):
            seven_card_stud_game.result_text += (
                " You are out of chips."
            )

        seven_card_stud_session_end_at = (
                pygame.time.get_ticks()
                + SEVEN_CARD_STUD_SESSION_END_DELAY
        )

        return

    if seven_card_stud_game.all_npcs_busted():
        seven_card_stud_next_hand_at = 0

        fan_gain = 0

        if not seven_card_stud_table_sweep_rewarded:
            process_achievement_event("poker_table_clear", game="seven_card_stud")
            if current_game_mode == "career":
                fan_gain = award_fans_for_rating_win(
                    SEVEN_CARD_STUD_TABLE_SWEEP_RATING_BONUS,
                    "Seven-Card Stud table clear"
                )
                career_event_has_activity = True
            seven_card_stud_table_sweep_rewarded = True

        seven_card_stud_game.result_text += " TABLE CLEARED!"
        if current_game_mode == "career":
            seven_card_stud_game.result_text += (
                " Rating settles on cash-out. "
                f"+{fan_gain:,} Fans."
            )

        seven_card_stud_session_end_at = (
                pygame.time.get_ticks()
                + SEVEN_CARD_STUD_SESSION_END_DELAY
        )


def try_place_or_remove_roulette_bet(
        bet_type,
        bet_value,
        is_right_click
):

    wager = (
        roulette_chip_value
    )

    if is_right_click:

        if roulette_game.remove_bet(
                bet_type,
                bet_value,
                wager
        ):

            audio.play_sound(
                "button_click"
            )

        return

    if (
            wager > 0
            and (
                roulette_game.get_total_bet()
                + wager
            ) <= career_cash
    ):

        roulette_game.place_bet(
            bet_type,
            bet_value,
            wager
        )

        audio.play_sound(
            "button_click"
        )

print(
    "NPCs missing portraits:",
    len(
        get_npcs_missing_portraits()
    )
)

def get_npc_icon_surface(
        npc,
        size
):

    icon_path = npc.get(
        "icon"
    )

    if not icon_path:
        return None

    cache_key = (
        icon_path,
        size
    )

    if cache_key in npc_icon_cache:
        return npc_icon_cache[
            cache_key
        ]

    try:

        image = pygame.image.load(
            icon_path
        ).convert_alpha()

        image = (
            pygame.transform.smoothscale(
                image,
                (
                    size,
                    size
                )
            )
        )

        npc_icon_cache[
            cache_key
        ] = image

        return image

    except (
            pygame.error,
            FileNotFoundError
    ):

        return None



def get_score_four_npc_progress():

    if (
            score_four_game.mode
            != "competitive"
    ):
        return 0.0

    if score_four_game.round_complete:
        return 1.0

    elapsed = (
        time.monotonic()
        - score_four_game.round_start_time
    )

    if (
            score_four_game.npc_solve_time_seconds
            <= 0
    ):
        return 0.0

    return max(
        0.0,
        min(
            1.0,
            elapsed
            / score_four_game.npc_solve_time_seconds
        )
    )


def get_blackjack_bet(
        percentage
):

    if career_cash <= 0:
        return 0

    if percentage >= 1.0:
        return career_cash

    return max(
        1,
        round(
            career_cash
            * percentage
        )
    )

def settle_roulette_round():

    global career_cash
    global roulette_session_net

    if not roulette_game.round_complete:
        return

    if roulette_game.payout_claimed:
        return

    payout = (
        roulette_game.get_payout()
    )

    career_cash += (
        payout
    )

    net_result = (
        roulette_game.get_net_result()
    )

    roulette_session_net += (
        net_result
    )
    roulette_game.rating_change = (rate_house_game("roulette", net_result)
                                   if current_game_mode == "career" else None)

    if net_result > 0:
        award_fans_for_cash_win(
            net_result,
            "Roulette win"
        )
    elif current_game_mode == "career" and net_result <= -500:
        lose_fans_for_bad_result(
            "Rough Roulette spin",
            net_loss=abs(net_result),
            severity=0.65,
        )

    award_game_xp(
        "roulette",
        won=(net_result > 0),
        bonus=8 if net_result >= 1000 else 0,
    )

    process_achievement_event(
        "roulette_round",
        net=net_result,
        bets=[dict(bet) for bet in roulette_game.bets],
    )

    track_night_cash(globals(), "roulette", net_result)
    roulette_game.payout_claimed = True

def settle_blackjack_round():
    global career_cash
    global blackjack_session_net
    global blackjack_session_rating_change
    global blackjack_round_doubled
    global blackjack_round_all_in
    global blackjack_round_start_bet

    if not blackjack_game.round_complete:
        return

    if blackjack_game.payout_claimed:
        return

    payout = blackjack_game.get_payout()

    career_cash += payout

    net_result = (
        payout
        - blackjack_game.bet
    )

    blackjack_session_net += (
        net_result
    )
    if current_game_mode == "career":
        if blackjack_game.is_split_round():
            blackjack_game.rating_change = sum(rate_house_game("blackjack", 1 if result == "player" else -1 if result == "dealer" else 0)
                                               for result in blackjack_game.player_hand_results)
        else:
            blackjack_game.rating_change = rate_house_game("blackjack", net_result)
    else:
        blackjack_game.rating_change = None
    blackjack_session_rating_change = globals().get("blackjack_session_rating_change", 0) + int(blackjack_game.rating_change or 0)

    if net_result > 0:
        award_fans_for_cash_win(
            net_result,
            "Blackjack win"
        )
    elif current_game_mode == "career" and net_result <= -500:
        lose_fans_for_bad_result(
            "Rough Blackjack hand",
            net_loss=abs(net_result),
            severity=0.65,
        )

    award_game_xp(
        "blackjack",
        won=(net_result > 0),
        bonus=12 if blackjack_game.result == "blackjack" else 0,
    )

    blackjack_hand_values = [
        blackjack_game.get_hand_value(hand)
        for hand in blackjack_game.get_player_hands()
    ]

    process_achievement_event(
        "blackjack_round",
        result=blackjack_game.result,
        net=net_result,
        natural=(
            not blackjack_game.is_split_round()
            and len(blackjack_game.player_hand) == 2
            and blackjack_game.player_value() == 21
        ),
        doubled=blackjack_round_doubled,
        all_in=blackjack_round_all_in,
        stood=bool(getattr(blackjack_game, "player_stood", False)),
        player_total=max(blackjack_hand_values, default=0),
        hit_count=max(
            0,
            blackjack_game.get_total_player_cards()
            - (4 if blackjack_game.is_split_round() else 2)
        ),
        starting_bet=blackjack_round_start_bet,
    )

    track_night_cash(globals(), "blackjack", net_result)
    blackjack_game.payout_claimed = True

def settle_horse_race_result():
    global horse_races_session_net
    global horse_races_last_rewarded_races
    global career_event_has_activity

    if horse_races_game.races_completed <= horse_races_last_rewarded_races:
        horse_races_session_net = horse_races_game.get_session_net()
        return False

    horse_races_last_rewarded_races = horse_races_game.races_completed
    horse_races_session_net = horse_races_game.get_session_net()
    career_event_has_activity = True

    # Every completed race gets a quick winner celebration. This is separate
    # from whether the player personally held a winning ticket.
    audio.play_sound("celebration_3")

    if horse_races_game.race_net > 0:
        award_fans_for_cash_win(
            horse_races_game.race_net,
            "Horse race win"
        )

    award_game_xp(
        "horse_races",
        won=(horse_races_game.race_net > 0),
    )

    return True


def get_card_key(
        card
):
    rank, suit = card

    return f"{rank}{suit}"

def debug_open_casual_cards():

    global current_state
    global career_event_entry
    global career_event_has_activity

    career_event_entry = {
        "activity_type": (
            CAREER_ACTIVITY_CASUAL_CARDS
        ),
        "title": "Casual Cards",
        "game_ids": (
            CAREER_EVENT_GAMES[
                CAREER_ACTIVITY_CASUAL_CARDS
            ].copy()
        ),
    }

    career_event_has_activity = False
    reset_career_event_result_log()
    reset_career_event_session_totals(CAREER_ACTIVITY_CASUAL_CARDS)

    current_state = (
        STATE_CAREER_EVENT_SELECT
    )


def debug_open_casino_night():

    global current_state
    global career_event_entry
    global career_event_has_activity

    career_event_entry = {
        "activity_type": (
            CAREER_ACTIVITY_CASINO_NIGHT
        ),
        "title": "Casino Night",
        "game_ids": (
            CAREER_EVENT_GAMES[
                CAREER_ACTIVITY_CASINO_NIGHT
            ].copy()
        ),
    }

    career_event_has_activity = False
    reset_career_event_result_log()
    reset_career_event_session_totals(CAREER_ACTIVITY_CASINO_NIGHT)

    current_state = (
        STATE_CAREER_EVENT_SELECT
    )


def set_arcade_status_message(message, duration_ms=2600):
    global arcade_status_message
    global arcade_status_message_expires

    arcade_status_message = str(message or "")
    arcade_status_message_expires = pygame.time.get_ticks() + max(600, int(duration_ms or 0))


def open_arcade_token_exchange(pending_game_id=None):
    global current_state
    global arcade_pending_launch_game_id

    arcade_pending_launch_game_id = pending_game_id
    current_state = STATE_ARCADE_TOKEN_EXCHANGE


def build_king_pong_opponent_choices():
    """Pick one current Career NPC for each arcade difficulty tier."""
    choices = []
    used_ids = set()
    fallback_pool = [
        npc for npc in NPCS
        if isinstance(npc, dict) and npc.get("name")
    ]

    for difficulty_id, config in KING_PONG_DIFFICULTIES.items():
        tier = config.get("npc_tier", "mid")
        tier_pool = [
            npc for npc in fallback_pool
            if npc.get("skill_tier", "mid") == tier
            and npc.get("id") not in used_ids
        ]

        if not tier_pool:
            tier_pool = [
                npc for npc in fallback_pool
                if npc.get("id") not in used_ids
            ]

        if tier_pool:
            npc = random.choice(tier_pool)
            npc_id = npc.get("id")
            if npc_id is not None:
                used_ids.add(npc_id)
        else:
            npc = {
                "id": f"arcade_{difficulty_id}",
                "name": f"{config.get('label', difficulty_id.title())} Arcade Bot",
                "skill_tier": tier,
            }

        choices.append({
            "difficulty_id": difficulty_id,
            "npc": npc,
        })

    return choices


def open_king_pong_opponent_select(refresh=True):
    global current_state
    global king_pong_opponent_choices
    global king_pong_selected_opponent_index
    global arcade_pending_launch_game_id

    if refresh or len(king_pong_opponent_choices) != len(KING_PONG_DIFFICULTIES):
        king_pong_opponent_choices = build_king_pong_opponent_choices()
        king_pong_selected_opponent_index = None

    arcade_pending_launch_game_id = None
    current_state = STATE_KING_PONG_OPPONENT_SELECT


def build_battle_bosses_opponent_choices():
    return build_battle_bosses_choices(NPCS)


def open_battle_bosses_opponent_select(refresh=True):
    global current_state
    global battle_bosses_opponent_choices
    global battle_bosses_selected_choice_index

    if refresh or len(battle_bosses_opponent_choices) != len(BATTLE_BOSSES_DIFFICULTIES):
        battle_bosses_opponent_choices = build_battle_bosses_opponent_choices()
        battle_bosses_selected_choice_index = None

    current_state = STATE_BATTLE_BOSSES_OPPONENT_SELECT


def get_selected_battle_bosses_choice():
    if (
            battle_bosses_selected_choice_index is None
            or battle_bosses_selected_choice_index < 0
            or battle_bosses_selected_choice_index >= len(battle_bosses_opponent_choices)
    ):
        return None
    return battle_bosses_opponent_choices[battle_bosses_selected_choice_index]


def get_selected_king_pong_choice():
    if (
            king_pong_selected_opponent_index is None
            or king_pong_selected_opponent_index < 0
            or king_pong_selected_opponent_index >= len(king_pong_opponent_choices)
    ):
        return None
    return king_pong_opponent_choices[king_pong_selected_opponent_index]


def start_king_pong_session():
    global current_state
    global career_event_has_activity
    global arcade_state
    global arcade_night_tokens_spent
    global arcade_pending_launch_game_id

    selected = get_selected_king_pong_choice()
    if selected is None:
        open_king_pong_opponent_select(refresh=True)
        set_arcade_status_message("Choose a King Pong rival first.")
        return False

    token_cost = get_machine_cost("king_pong")
    success, updated_state = spend_tokens(arcade_state, token_cost)
    if not success:
        set_arcade_status_message("Not enough tokens. Buy more to play King Pong.")
        open_arcade_token_exchange("king_pong")
        return False

    arcade_state = updated_state
    arcade_night_tokens_spent += token_cost
    arcade_pending_launch_game_id = None
    career_event_has_activity = True

    difficulty_id = selected.get("difficulty_id", "medium")
    opponent = selected.get("npc") or {"name": "Arcade Rival", "skill_tier": "mid"}
    king_pong_game.start_match(
        opponent,
        difficulty_id=difficulty_id,
        target_score=5,
        player_name=player_name,
    )
    auto_save_career()
    current_state = STATE_KING_PONG
    return True


def claim_king_pong_result():
    global career_event_has_activity
    global arcade_state
    global arcade_night_tickets_won

    if king_pong_game.reward_claimed or not king_pong_game.finished:
        return False

    if king_pong_game.forfeited:
        base_tickets = 0
        tickets = 0
    else:
        base_tickets = award_king_pong_tickets(
            king_pong_game.player_score,
            king_pong_game.opponent_score,
        )
        tickets = max(
            0,
            int(round(base_tickets * king_pong_game.ticket_multiplier)),
        )

    arcade_state = register_king_pong_result(
        arcade_state,
        king_pong_game.player_won,
        tickets,
    )
    arcade_night_tickets_won += tickets
    career_event_has_activity = True

    record_career_event_result(
        "king_pong",
        won=king_pong_game.player_won,
        tickets=tickets,
        base_tickets=base_tickets,
        ticket_multiplier=king_pong_game.ticket_multiplier,
        difficulty=king_pong_game.difficulty_id,
        tokens_spent=get_machine_cost("king_pong"),
        player_score=king_pong_game.player_score,
        opponent_score=king_pong_game.opponent_score,
        opponent_name=king_pong_game.opponent_name,
        forfeited=bool(king_pong_game.forfeited),
        fan_impact=False,
    )

    king_pong_game.reward_claimed = True
    auto_save_career()
    return True


def finish_king_pong_session():
    global current_state

    claim_king_pong_result()
    current_state = STATE_CAREER_EVENT_SELECT


def start_battle_bosses_session():
    global current_state
    global career_event_has_activity
    global arcade_state
    global arcade_night_tokens_spent
    global arcade_pending_launch_game_id

    selected = get_selected_battle_bosses_choice()
    if selected is None:
        open_battle_bosses_opponent_select(refresh=True)
        set_arcade_status_message("Choose a Battle Bosses squad first.")
        return False

    token_cost = get_machine_cost("battle_bosses")
    success, updated_state = spend_tokens(arcade_state, token_cost)
    if not success:
        set_arcade_status_message("Not enough tokens. Buy more to enter Battle Bosses.")
        open_arcade_token_exchange("battle_bosses")
        return False

    arcade_state = updated_state
    arcade_night_tokens_spent += token_cost
    arcade_pending_launch_game_id = None
    career_event_has_activity = True

    difficulty_id = selected.get("difficulty_id", "standard")
    config = selected.get("config") or BATTLE_BOSSES_DIFFICULTIES.get(
        difficulty_id, BATTLE_BOSSES_DIFFICULTIES["standard"]
    )
    battle_bosses_game.start_match(
        selected.get("npcs") or [],
        difficulty_id=difficulty_id,
        difficulty_config=config,
        player_name=player_name,
    )
    auto_save_career()
    current_state = STATE_BATTLE_BOSSES
    return True


def claim_battle_bosses_result():
    global career_event_has_activity
    global arcade_state
    global arcade_night_tickets_won

    if battle_bosses_game.reward_claimed or not battle_bosses_game.finished:
        return False

    if battle_bosses_game.forfeited:
        base_tickets = 0
        tickets = 0
    else:
        base_tickets = award_battle_bosses_tickets(
            battle_bosses_game.rivals_eliminated,
            battle_bosses_game.player_won,
            battle_bosses_game.player_hp,
        )
        tickets = max(
            0,
            int(round(base_tickets * battle_bosses_game.ticket_multiplier)),
        )

    arcade_state = register_battle_bosses_result(
        arcade_state,
        battle_bosses_game.player_won,
        tickets,
        rivals_eliminated=battle_bosses_game.rivals_eliminated,
    )
    arcade_night_tickets_won += tickets
    career_event_has_activity = True

    record_career_event_result(
        "battle_bosses",
        won=battle_bosses_game.player_won,
        tickets=tickets,
        base_tickets=base_tickets,
        ticket_multiplier=battle_bosses_game.ticket_multiplier,
        difficulty=battle_bosses_game.difficulty_id,
        tokens_spent=get_machine_cost("battle_bosses"),
        rivals_eliminated=battle_bosses_game.rivals_eliminated,
        player_hp=battle_bosses_game.player_hp,
        forfeited=bool(battle_bosses_game.forfeited),
        fan_impact=False,
    )

    battle_bosses_game.reward_claimed = True
    auto_save_career()
    return True


def finish_battle_bosses_session():
    global current_state

    claim_battle_bosses_result()
    current_state = STATE_CAREER_EVENT_SELECT


def start_crazy_eights_session():

    global current_state

    opponents = get_random_npc_group(3)
    crazy_eights_game.start_game(opponents)

    current_state = STATE_CRAZY_EIGHTS



def claim_crazy_eights_result():

    global career_event_has_activity

    if crazy_eights_game.reward_claimed:
        return

    career_event_has_activity = True

    player_won = (crazy_eights_game.winner_index == 0)
    record_career_event_result(
        "crazy_eights",
        won=player_won,
    )

    if player_won:
        rating_gain = 60
        award_fans_for_rating_win(
            rating_gain,
            "Crazy Eights win"
        )

    award_game_xp("crazy_eights", won=player_won)
    crazy_eights_game.reward_claimed = True



def start_bango_session():

    global current_state

    opponents = get_random_npc_group(3)
    bango_game.start_game(
        opponents,
        hand_size=5
    )

    current_state = STATE_BANGO



def claim_bango_result():

    global career_event_has_activity

    if bango_game.reward_claimed:
        return

    career_event_has_activity = True

    player_won = (bango_game.winner_index == 0)
    record_career_event_result(
        "bango",
        won=player_won,
    )

    if player_won:
        rating_gain = 35
        award_fans_for_rating_win(
            rating_gain,
            "Bango win"
        )

    award_game_xp("bango", won=player_won)
    bango_game.reward_claimed = True



def debug_open_crazy_eights():

    global career_event_entry
    global career_event_has_activity

    career_event_entry = {
        "activity_type": CAREER_ACTIVITY_CASUAL_CARDS,
        "title": "Casual Cards",
        "game_ids": CAREER_EVENT_GAMES[
            CAREER_ACTIVITY_CASUAL_CARDS
        ].copy(),
    }

    career_event_has_activity = False
    start_crazy_eights_session()



def debug_open_bango():

    global career_event_entry
    global career_event_has_activity

    career_event_entry = {
        "activity_type": CAREER_ACTIVITY_CASUAL_CARDS,
        "title": "Casual Cards",
        "game_ids": CAREER_EVENT_GAMES[
            CAREER_ACTIVITY_CASUAL_CARDS
        ].copy(),
    }

    career_event_has_activity = False
    start_bango_session()



def debug_open_score_four_solo():

    global current_state
    global career_event_entry
    global career_event_has_activity

    career_event_entry = {
        "activity_type": (
            CAREER_ACTIVITY_CASUAL_CARDS
        ),
        "title": "Casual Cards",
        "game_ids": (
            CAREER_EVENT_GAMES[
                CAREER_ACTIVITY_CASUAL_CARDS
            ].copy()
        ),
    }

    career_event_has_activity = False

    score_four_game.start_solo_session()

    current_state = (
        STATE_SCORE_FOUR
    )


def debug_open_score_four_competitive():

    global current_state
    global career_event_entry
    global career_event_has_activity
    global score_four_opponent_choices
    global score_four_opponent_npc

    career_event_entry = {
        "activity_type": (
            CAREER_ACTIVITY_CASUAL_CARDS
        ),
        "title": "Casual Cards",
        "game_ids": (
            CAREER_EVENT_GAMES[
                CAREER_ACTIVITY_CASUAL_CARDS
            ].copy()
        ),
    }

    career_event_has_activity = False

    score_four_opponent_choices = (
        get_score_four_opponent_choices()
    )

    score_four_opponent_npc = None

    current_state = (
        STATE_SCORE_FOUR_OPPONENT_SELECT
    )


def debug_open_blackjack():

    global current_state
    global career_event_entry
    global career_event_has_activity
    global blackjack_dealer_npc
    global blackjack_selected_bet_percentage
    global blackjack_bet_dropdown_open
    global blackjack_session_net
    global blackjack_session_rating_change

    career_event_entry = {
        "activity_type": (
            CAREER_ACTIVITY_CASINO_NIGHT
        ),
        "title": "Casino Night",
        "game_ids": (
            CAREER_EVENT_GAMES[
                CAREER_ACTIVITY_CASINO_NIGHT
            ].copy()
        ),
    }

    career_event_has_activity = False

    blackjack_dealer_npc = (
        get_random_blackjack_dealer()
    )

    blackjack_selected_bet_percentage = None
    blackjack_bet_dropdown_open = False
    blackjack_session_net = 0
    blackjack_session_rating_change = 0

    current_state = (
        STATE_BLACKJACK_BET
    )

def get_blackjack_animated_position(
        hand_name,
        card_index,
        target_x,
        target_y
):

    progress = (
        blackjack_game.get_card_animation_progress(
            hand_name,
            card_index
        )
    )

    # Card's animation has not begun.
    if progress < 0:
        return None

    deck_x = 1120
    deck_y = 265

    # Smooth-out cubic ease.
    eased = (
        1
        - (1 - progress) ** 3
    )

    x = (
        deck_x
        + (
            target_x
            - deck_x
        )
        * eased
    )

    y = (
        deck_y
        + (
            target_y
            - deck_y
        )
        * eased
    )

    return (
        int(x),
        int(y)
    )

def debug_open_roulette():

    global current_state
    global career_event_entry
    global career_event_has_activity
    global roulette_session_net

    career_event_entry = {
        "activity_type": (
            CAREER_ACTIVITY_CASINO_NIGHT
        ),
        "title": "Casino Night",
        "game_ids": (
            CAREER_EVENT_GAMES[
                CAREER_ACTIVITY_CASINO_NIGHT
            ].copy()
        ),
    }

    career_event_has_activity = False

    roulette_session_net = 0

    roulette_game.reset_round()

    current_state = (
        STATE_ROULETTE
    )

def start_horse_race_music():
    global horse_race_music_channel
    global horse_race_previous_music_volume

    if horse_race_music_sound is None:
        return False

    if horse_race_music_channel is not None:
        try:
            if horse_race_music_channel.get_busy():
                return True
        except pygame.error:
            pass

    horse_race_previous_music_volume = float(audio.music_volume)
    audio.set_music_volume(horse_race_previous_music_volume * 0.22)

    try:
        horse_race_music_channel = pygame.mixer.find_channel(True)
        if horse_race_music_channel is None:
            audio.set_music_volume(horse_race_previous_music_volume)
            return False

        horse_race_music_channel.set_volume(
            max(0.0, min(1.0, horse_race_previous_music_volume * 0.70))
        )
        horse_race_music_channel.play(
            horse_race_music_sound,
            loops=-1,
            fade_ms=250,
        )
        return True
    except pygame.error:
        audio.set_music_volume(horse_race_previous_music_volume)
        horse_race_music_channel = None
        return False


def stop_horse_race_music(fade_ms=500):
    global horse_race_music_channel
    global horse_race_previous_music_volume

    if horse_race_music_channel is not None:
        try:
            horse_race_music_channel.fadeout(max(0, int(fade_ms)))
        except pygame.error:
            pass

    horse_race_music_channel = None

    if horse_race_previous_music_volume is not None:
        audio.set_music_volume(horse_race_previous_music_volume)

    horse_race_previous_music_volume = None


def start_horse_races_session():
    global current_state
    global horse_races_session_net
    global horse_races_last_rewarded_races

    horse_races_session_net = 0
    horse_races_last_rewarded_races = 0
    horse_races_game.start_session(career_cash)
    current_state = STATE_HORSE_RACES
    return True


def finish_horse_races_session():
    global career_cash
    global horse_races_session_net
    global career_event_has_activity
    global current_state

    career_cash = horse_races_game.cash_out()
    horse_races_session_net = horse_races_game.get_session_net()

    if horse_races_game.races_completed > 0:
        career_event_has_activity = True

    if (
            current_game_mode == "career"
            and horse_races_game.races_completed > 0
            and not horse_races_game.reward_claimed
    ):
        record_career_event_result(
            "horse_races",
            won=(horse_races_session_net > 0),
            net=horse_races_session_net,
            races=horse_races_game.races_completed,
            profitable_races=horse_races_game.races_with_profit,
        )
        track_night_cash(globals(), "horse_races", horse_races_session_net)
        horse_races_game.reward_claimed = True

    if current_game_mode == "free":
        finish_free_play_sandbox()
        current_state = STATE_FREE_PLAY_SELECT
    else:
        current_state = STATE_CAREER_EVENT_SELECT

    return horse_races_session_net


def debug_open_horse_races():
    global career_event_entry
    global career_event_has_activity
    global current_game_mode

    current_game_mode = "debug"
    career_event_entry = {
        "activity_type": CAREER_ACTIVITY_CASINO_NIGHT,
        "title": "Casino Night",
        "game_ids": CAREER_EVENT_GAMES[
            CAREER_ACTIVITY_CASINO_NIGHT
        ].copy(),
    }
    career_event_has_activity = False
    reset_career_event_result_log()
    reset_career_event_session_totals(CAREER_ACTIVITY_CASINO_NIGHT)
    return start_horse_races_session()


def start_faro_session():

    global current_state
    global faro_session_net

    faro_session_net = 0
    faro_game.start_session(career_cash)
    current_state = STATE_FARO
    return True


def claim_faro_session_result():

    global career_cash
    global career_event_has_activity
    global faro_session_net

    if faro_game.reward_claimed:
        career_cash = faro_game.cash_out()
        return faro_session_net

    career_cash = faro_game.cash_out()
    faro_session_net = faro_game.get_session_net()

    if faro_game.turns_dealt <= 0 or faro_game.wagered_total <= 0:
        faro_game.reward_claimed = True
        return faro_session_net

    career_event_has_activity = True

    strong_threshold = max(500, int(faro_game.starting_cash * 0.25))
    bad_threshold = max(100, int(faro_game.starting_cash * 0.10))

    if faro_session_net >= strong_threshold:
        reward_key = "strong_profit"
    elif faro_session_net > 0:
        reward_key = "profit"
    elif faro_session_net <= -bad_threshold:
        reward_key = "bad_session"
    else:
        reward_key = "break_even"

    rating_gain = TRAINING_RATING_REWARDS["faro"][reward_key]

    if faro_session_net > 0:
        award_fans_for_cash_win(
            faro_session_net,
            "Faro profit"
        )

    award_game_xp(
        "faro",
        won=(faro_session_net > 0),
    )

    record_career_event_result(
        "faro",
        won=(faro_session_net > 0),
        net=faro_session_net,
        turns=faro_game.turns_dealt,
    )

    track_night_cash(globals(), "faro", faro_session_net)
    faro_game.reward_claimed = True
    return faro_session_net


def debug_open_faro():

    global career_event_entry
    global career_event_has_activity

    career_event_entry = {
        "activity_type": CAREER_ACTIVITY_NICHE_NIGHT,
        "title": "Niche Game Night",
        "game_ids": CAREER_EVENT_GAMES[
            CAREER_ACTIVITY_NICHE_NIGHT
        ].copy(),
    }

    career_event_has_activity = False
    reset_career_event_result_log()
    reset_career_event_session_totals(CAREER_ACTIVITY_NICHE_NIGHT)
    start_faro_session()


# ==================================================
# FIVE-O POKER / BLIND MAN'S BLUFF HELPERS
# ==================================================

def get_niche_poker_starting_stack(minimum_buy_in=100):
    if career_cash < minimum_buy_in:
        return 0
    if career_cash <= 500:
        return career_cash
    return min(
        career_cash,
        2000,
        max(minimum_buy_in, int(round(career_cash * 0.25)))
    )

def start_five_o_poker_session(starting_stack=None):
    global career_cash
    global five_o_poker_starting_stack
    global five_o_poker_session_net
    global five_o_poker_buy_in_active
    global career_event_has_activity
    global current_state

    if starting_stack is None:
        starting_stack = get_niche_poker_starting_stack(
            FIVE_O_POKER_MIN_BUY_IN
        )

    starting_stack = min(max(0, int(starting_stack)), career_cash)
    if starting_stack < FIVE_O_POKER_MIN_BUY_IN:
        return False

    opponent = get_random_npc()
    if opponent is None:
        return False

    career_cash -= starting_stack
    five_o_poker_starting_stack = starting_stack
    five_o_poker_session_net = 0
    five_o_poker_buy_in_active = True
    five_o_poker_game.session_xp_rewarded = False

    if not five_o_poker_game.start_session(opponent, starting_stack):
        career_cash += starting_stack
        five_o_poker_buy_in_active = False
        return False

    career_event_has_activity = True
    current_state = STATE_FIVE_O_POKER
    audio.play_sound("card_shuffle")
    return True


def finish_five_o_poker_session():
    global career_cash
    global five_o_poker_session_net
    global five_o_poker_buy_in_active
    global career_event_has_activity
    global current_state

    if five_o_poker_buy_in_active:
        career_cash += five_o_poker_game.player_stack
        five_o_poker_session_net = (
            five_o_poker_game.player_stack - five_o_poker_starting_stack
        )
        five_o_poker_buy_in_active = False

    if five_o_poker_game.hands_played > 0:
        career_event_has_activity = True

    won_five_o_session = (
        five_o_poker_session_net > 0
        or five_o_poker_game.hands_won > five_o_poker_game.hands_lost
    )

    if (
            five_o_poker_game.hands_played > 0
            and not getattr(five_o_poker_game, "session_xp_rewarded", False)
    ):
        award_game_xp("five_o_poker", won=won_five_o_session)
        five_o_poker_game.session_xp_rewarded = True

    if (
            current_game_mode == "career"
            and five_o_poker_game.hands_played > 0
            and not five_o_poker_game.reward_claimed
    ):
        rating_gain = rate_poker_cash_out(
            "five_o_poker",
            five_o_poker_game,
        )

        won_session = won_five_o_session
        if won_session:
            award_fans_for_rating_win(
                rating_gain,
                "Five-O Poker session"
            )

        record_career_event_result(
            "five_o_poker",
            won=won_session,
            net=five_o_poker_session_net,
            hands=five_o_poker_game.hands_played,
            hands_won=five_o_poker_game.hands_won,
            five_o_wins=five_o_poker_game.five_o_wins,
            rating_reward=rating_gain,
        )
        track_night_cash(globals(), "five_o_poker", five_o_poker_session_net)
        five_o_poker_game.reward_claimed = True

    if current_game_mode == "free":
        finish_free_play_sandbox()
        current_state = STATE_FREE_PLAY_SELECT
    else:
        current_state = STATE_CAREER_EVENT_SELECT


def debug_open_five_o_poker():
    global career_event_entry
    global career_event_has_activity
    global current_game_mode

    current_game_mode = "debug"
    career_event_entry = {
        "activity_type": CAREER_ACTIVITY_NICHE_NIGHT,
        "title": "Niche Game Night",
        "game_ids": CAREER_EVENT_GAMES[CAREER_ACTIVITY_NICHE_NIGHT].copy(),
    }
    career_event_has_activity = False
    reset_career_event_result_log()
    reset_career_event_session_totals(CAREER_ACTIVITY_NICHE_NIGHT)
    return start_five_o_poker_session()


def start_blind_mans_bluff_session(starting_stack=None):
    global career_cash
    global blind_mans_bluff_starting_stack
    global blind_mans_bluff_session_net
    global blind_mans_bluff_buy_in_active
    global career_event_has_activity
    global current_state

    if starting_stack is None:
        starting_stack = get_niche_poker_starting_stack(
            BLIND_MANS_BLUFF_MIN_BUY_IN
        )

    starting_stack = min(max(0, int(starting_stack)), career_cash)
    if starting_stack < BLIND_MANS_BLUFF_MIN_BUY_IN:
        return False

    opponents = get_random_npc_group(3)
    if len(opponents) < 3:
        return False

    career_cash -= starting_stack
    blind_mans_bluff_starting_stack = starting_stack
    blind_mans_bluff_session_net = 0
    blind_mans_bluff_buy_in_active = True
    blind_mans_bluff_game.session_xp_rewarded = False

    if not blind_mans_bluff_game.start_session(opponents, starting_stack):
        career_cash += starting_stack
        blind_mans_bluff_buy_in_active = False
        return False

    career_event_has_activity = True
    current_state = STATE_BLIND_MANS_BLUFF
    audio.play_sound("card_shuffle")
    return True


def finish_blind_mans_bluff_session():
    global career_cash
    global blind_mans_bluff_session_net
    global blind_mans_bluff_buy_in_active
    global career_event_has_activity
    global current_state

    if blind_mans_bluff_buy_in_active:
        career_cash += blind_mans_bluff_game.player_stack
        blind_mans_bluff_session_net = (
            blind_mans_bluff_game.player_stack
            - blind_mans_bluff_starting_stack
        )
        blind_mans_bluff_buy_in_active = False

    if blind_mans_bluff_game.hands_played > 0:
        career_event_has_activity = True

    won_bluff_session = (
        blind_mans_bluff_session_net > 0
        or blind_mans_bluff_game.hands_won > blind_mans_bluff_game.hands_lost
    )

    if (
            blind_mans_bluff_game.hands_played > 0
            and not getattr(blind_mans_bluff_game, "session_xp_rewarded", False)
    ):
        award_game_xp("blind_mans_bluff", won=won_bluff_session)
        blind_mans_bluff_game.session_xp_rewarded = True

    if (
            current_game_mode == "career"
            and blind_mans_bluff_game.hands_played > 0
            and not blind_mans_bluff_game.reward_claimed
    ):
        if blind_mans_bluff_session_net > 0:
            reward_key = "profit"
        elif blind_mans_bluff_session_net == 0:
            reward_key = "break_even"
        else:
            reward_key = "loss"

        rating_gain = TRAINING_RATING_REWARDS["blind_mans_bluff"][reward_key]
    
        won_session = won_bluff_session
        if won_session:
            award_fans_for_rating_win(
                rating_gain,
                "Blind Man's Bluff session"
            )

        record_career_event_result(
            "blind_mans_bluff",
            won=won_session,
            net=blind_mans_bluff_session_net,
            hands=blind_mans_bluff_game.hands_played,
            hands_won=blind_mans_bluff_game.hands_won,
        )
        track_night_cash(globals(), "blind_mans_bluff", blind_mans_bluff_session_net)
        blind_mans_bluff_game.reward_claimed = True

    if current_game_mode == "free":
        finish_free_play_sandbox()
        current_state = STATE_FREE_PLAY_SELECT
    else:
        current_state = STATE_CAREER_EVENT_SELECT


def debug_open_blind_mans_bluff():
    global career_event_entry
    global career_event_has_activity
    global current_game_mode

    current_game_mode = "debug"
    career_event_entry = {
        "activity_type": CAREER_ACTIVITY_NICHE_NIGHT,
        "title": "Niche Game Night",
        "game_ids": CAREER_EVENT_GAMES[CAREER_ACTIVITY_NICHE_NIGHT].copy(),
    }
    career_event_has_activity = False
    reset_career_event_result_log()
    reset_career_event_session_totals(CAREER_ACTIVITY_NICHE_NIGHT)
    return start_blind_mans_bluff_session()


def debug_open_head_to_head():
    global career_event_entry
    global career_event_has_activity
    global current_state

    career_event_entry = {
        "activity_type": CAREER_ACTIVITY_EVENT,
        "title": "Head-to-Head",
        "event_id": "head_to_head_01",
        "debug": True,
    }
    career_event_has_activity = False
    start_head_to_head_event()
    current_state = STATE_CAREER_EVENT
    return True


def debug_prepare_poker_night():
    global career_event_entry
    global career_event_has_activity

    game_ids = (
        CAREER_EVENT_GAMES[
            CAREER_ACTIVITY_POKER_NIGHT
        ].copy()
    )

    career_event_entry = {
        "activity_type": CAREER_ACTIVITY_POKER_NIGHT,
        "title": "Poker Night",
        "game_ids": game_ids,
        "high_stakes_game_id": random.choice(
            game_ids
        ) if game_ids else None,
    }

    career_event_has_activity = False
    reset_career_event_result_log()
    reset_career_event_session_totals(CAREER_ACTIVITY_POKER_NIGHT)


def debug_open_poker_night():
    global current_state

    debug_prepare_poker_night()

    current_state = (
        STATE_CAREER_EVENT_SELECT
    )


def open_debug_poker_npc_select(game_id):
    global current_state
    global current_game_mode
    global debug_poker_select_game_id
    global debug_poker_selected_ids

    debug_prepare_poker_night()
    current_game_mode = "debug"
    debug_poker_select_game_id = str(game_id)
    debug_poker_selected_ids = make_debug_poker_default_selection(
        NPCS,
        count=4,
    )
    current_state = STATE_DEBUG_POKER_NPC_SELECT


def get_debug_poker_selected_npcs():
    selected = []
    selected_ids = set(debug_poker_selected_ids)
    for npc_id in debug_poker_selected_ids:
        for npc in NPCS:
            if npc.get("id") == npc_id:
                selected.append(npc)
                break
    return selected[:4]


def start_debug_selected_poker_table():
    global current_state

    opponents = get_debug_poker_selected_npcs()
    if len(opponents) < 4:
        return False

    if debug_poker_select_game_id == "texas_holdem":
        return start_texas_holdem_session(opponents=opponents)
    if debug_poker_select_game_id == "five_card_draw":
        return start_five_card_draw_session(opponents=opponents)
    if debug_poker_select_game_id == "seven_card_stud":
        return start_seven_card_stud_session(opponents=opponents)
    return False


def debug_open_solitaire_challenge(
        challenge_id
):
    global current_state
    global current_game_mode
    global pending_career_activity_index
    global pending_career_activity_type
    global pending_career_challenge_id

    pending_career_activity_index = None
    pending_career_activity_type = None
    pending_career_challenge_id = None

    current_game_mode = "debug"

    game.clear_challenge()
    game.set_difficulty(
        DEFAULT_DIFFICULTY
    )

    if not game.set_challenge(
            challenge_id
    ):
        return False

    game.new_game()

    current_state = (
        STATE_PLAYING
    )

    return True


def debug_set_player_level(
        target_level
):
    global player_level
    global player_xp
    global player_xp_to_next

    target_level = max(
        1,
        min(
            int(target_level),
            max(LEVEL_XP_THRESHOLDS)
        )
    )

    player_level = target_level
    player_xp = LEVEL_XP_THRESHOLDS.get(
        target_level,
        0
    )
    player_xp_to_next = get_next_level_xp(
        target_level
    )

    sync_unlocks_for_current_level()


def begin_free_play_sandbox(use_cash=False):
    """Protect Career state while a Free Play game is running."""
    global free_play_snapshot
    global career_cash
    global career_event_entry
    global career_event_has_activity
    global free_play_achievement_fans_earned

    if free_play_snapshot is None:
        free_play_snapshot = {
            "career_rating": career_rating,
            "career_ratings": copy.deepcopy(career_ratings),
            "career_cash": career_cash,
            "career_fans": career_fans,
            "career_fan_news_milestones": set(career_fan_news_milestones),
            "career_news_items": copy.deepcopy(career_news_items),
            "career_rounds_won": career_rounds_won,
            "career_challenges_won": career_challenges_won,
            "career_total_moves": career_total_moves,
            "career_event_result_log": copy.deepcopy(career_event_result_log),
            "career_event_has_activity": career_event_has_activity,
            "blackjack_session_rating_change": globals().get("blackjack_session_rating_change", 0),
        }

    career_event_entry = None
    career_event_has_activity = False
    free_play_achievement_fans_earned = 0

    if use_cash:
        career_cash = FREE_PLAY_STARTING_CASH


def finish_free_play_sandbox():
    global blackjack_session_rating_change
    global free_play_snapshot
    global career_rating
    global career_ratings
    global career_cash
    global career_fans
    global career_fan_news_milestones
    global career_news_items
    global career_rounds_won
    global career_challenges_won
    global career_total_moves
    global career_event_result_log
    global career_event_has_activity
    global career_event_entry
    global free_play_achievement_fans_earned

    if free_play_snapshot is not None:
        career_rating = free_play_snapshot["career_rating"]
        career_ratings = copy.deepcopy(free_play_snapshot["career_ratings"])
        career_cash = free_play_snapshot["career_cash"]
        career_fans = free_play_snapshot["career_fans"]
        career_fan_news_milestones = set(
            free_play_snapshot["career_fan_news_milestones"]
        )
        career_news_items = copy.deepcopy(
            free_play_snapshot["career_news_items"]
        )
        career_rounds_won = free_play_snapshot["career_rounds_won"]
        career_challenges_won = free_play_snapshot["career_challenges_won"]
        career_total_moves = free_play_snapshot["career_total_moves"]
        career_event_result_log = copy.deepcopy(
            free_play_snapshot["career_event_result_log"]
        )
        career_event_has_activity = free_play_snapshot[
            "career_event_has_activity"
        ]

    if free_play_snapshot is not None:
        blackjack_session_rating_change = free_play_snapshot.get("blackjack_session_rating_change", 0)

    career_event_entry = None
    free_play_snapshot = None

    if free_play_achievement_fans_earned > 0:
        award_career_fans(
            free_play_achievement_fans_earned,
            "Free Play achievement rewards"
        )
        free_play_achievement_fans_earned = 0
        auto_save_career()


def get_free_play_return_state():
    return STATE_FREE_PLAY_SELECT if current_game_mode == "free" else STATE_CAREER_EVENT_SELECT


def leave_free_play_game():
    global current_state
    if current_game_mode == "free":
        finish_free_play_sandbox()
        current_state = STATE_FREE_PLAY_SELECT
        return True
    return False


def start_free_play_game(game_id):
    global current_state
    global current_game_mode
    global blackjack_dealer_npc
    global blackjack_selected_bet_percentage
    global blackjack_bet_dropdown_open
    global blackjack_session_net
    global blackjack_session_rating_change
    global roulette_session_net
    global horse_races_session_net
    global horse_races_last_rewarded_races
    global faro_session_net
    global five_o_poker_session_net
    global blind_mans_bluff_session_net
    global score_four_opponent_npc

    current_game_mode = "free"

    cash_game = game_id in (
        "blackjack", "roulette", "horse_races", "texas_holdem",
        "five_card_draw", "seven_card_stud", "faro",
        "five_o_poker", "blind_mans_bluff"
    )
    begin_free_play_sandbox(use_cash=cash_game)

    if game_id == "solitaire":
        game.clear_challenge()
        current_state = STATE_DIFFICULTY
        return True

    if game_id == "case_opening":
        from case_opening import new_case_state
        case_screen.enter(new_case_state(), FREE_PLAY_STARTING_CASH, buy_case_for_screen, temporary=True)
        current_state = STATE_CASE_OPENING
        return True

    if game_id == "cryptid_creatures":
        cryptid_screen.enter(NPCS)
        current_state = STATE_CRYPTID_CREATURES
        return True

    if game_id == "score_four":
        score_four_opponent_npc = None
        current_state = STATE_SCORE_FOUR_MODE_SELECT
        return True

    if game_id == "crazy_eights":
        start_crazy_eights_session()
        return True

    if game_id == "bango":
        start_bango_session()
        return True

    if game_id == "blackjack":
        blackjack_dealer_npc = get_random_blackjack_dealer()
        blackjack_selected_bet_percentage = None
        blackjack_bet_dropdown_open = False
        blackjack_session_net = 0
        blackjack_session_rating_change = 0
        current_state = STATE_BLACKJACK_BET
        return True

    if game_id == "roulette":
        roulette_session_net = 0
        roulette_game.reset_round()
        current_state = STATE_ROULETTE
        return True

    if game_id == "horse_races":
        horse_races_session_net = 0
        horse_races_last_rewarded_races = 0
        start_horse_races_session()
        return True

    if game_id == "texas_holdem":
        current_state = STATE_TEXAS_HOLDEM_BUY_IN
        return True

    if game_id == "five_card_draw":
        current_state = STATE_FIVE_CARD_DRAW_BUY_IN
        return True

    if game_id == "seven_card_stud":
        current_state = STATE_SEVEN_CARD_STUD_BUY_IN
        return True

    if game_id == "faro":
        faro_session_net = 0
        start_faro_session()
        return True

    if game_id == "five_o_poker":
        five_o_poker_session_net = 0
        if start_five_o_poker_session():
            return True
        finish_free_play_sandbox()
        return False

    if game_id == "blind_mans_bluff":
        blind_mans_bluff_session_net = 0
        if start_blind_mans_bluff_session():
            return True
        finish_free_play_sandbox()
        return False

    finish_free_play_sandbox()
    return False


def debug_start_next_career_month(save=True):
    global current_game_mode
    global career_year
    global career_month
    global career_day
    global career_day_of_month
    global career_weekday_index
    global career_current_schedule

    if current_game_mode == "free":
        finish_free_play_sandbox()
    current_game_mode = "career"
    ensure_career_leaderboard()

    remaining_days = max(
        1,
        len(career_current_schedule)
        - career_day_of_month
        + 1
    )

    career_day += remaining_days
    career_month += 1

    if career_month > 12:
        career_month = 1
        career_year += 1

    career_day_of_month = 1
    career_weekday_index = 0

    update_career_leaderboard_ratings()
    maybe_add_monthly_flavor_news()

    career_current_schedule = (
        build_default_career_schedule()
    )

    if save:
        auto_save_career()

def debug_add_career_prospect(prodigy=False):
    global current_state, current_game_mode
    if current_game_mode == "free":
        finish_free_play_sandbox()
    current_game_mode = "career"
    ensure_career_leaderboard()
    story = add_prospect(career_npc_world, career_leaderboard_state, PROSPECT_POOL,
                         career_year, career_month, force_prodigy=prodigy)
    if story:
        sync_career_npc_runtime_state()
        add_career_news(story["headline"], story["body"], story["category"])
        auto_save_career()
        show_debug_message("Prodigy added to Career" if prodigy else "Prospect added to Career")
    else:
        show_debug_message("All 160 prospects have joined this Career")
    current_state = STATE_CAREER_HUB
    return bool(story)


def debug_advance_career_year():
    global current_state, current_game_mode
    if current_game_mode == "free":
        finish_free_play_sandbox()
    current_game_mode = "career"
    ensure_career_leaderboard()
    reset_career_hub_runtime()
    for _ in range(12):
        debug_start_next_career_month(save=False)
    auto_save_career()
    current_state = STATE_CAREER_HUB



def is_game_unlocked(
        game_id
):
    required_level = (
        GAME_UNLOCK_LEVELS.get(
            game_id,
            1
        )
    )

    return (
        player_level
        >= required_level
    )

def get_game_unlock_level(
        game_id
):
    return GAME_UNLOCK_LEVELS.get(
        game_id,
        1
    )

# ==================================================
# TIME HELPERS
# ==================================================

def format_round_time(
    seconds
):
    minutes = (
        seconds // 60
    )

    remaining_seconds = (
        seconds % 60
    )

    return (
        f"{minutes}:"
        f"{remaining_seconds:02d}"
    )

# ==================================================
# PROFILE HELPERS
# ==================================================

def get_profile_slot_display_data(
        slot
):
    loaded = load_profile(
        slot
    )

    if loaded is None:
        return {
            "exists": False,
            "name": "Empty Slot",
            "level": None,
        }

    identity = loaded.get(
        "identity",
        {}
    )

    progression = loaded.get(
        "progression",
        {}
    )

    return {
        "exists": True,

        "name": identity.get(
            "name",
            "Player"
        ),

        "level": progression.get(
            "level",
            1
        ),
    }

def cycle_option(
        current_value,
        options,
        direction
):
    current_index = options.index(
        current_value
    )

    new_index = (
        current_index + direction
    ) % len(options)

    return options[
        new_index
    ]

def apply_fresh_profile():
    global player_name
    global player_level
    global player_xp
    global player_xp_to_next

    global profile_name_text
    global profile_country_text
    global profile_age_text
    global profile_hometown_text
    global profile_bio_text
    global profile_gender
    global profile_favorite_suit

    global selected_menu_background
    global selected_felt
    global selected_title
    global selected_cursor

    global unlocked_menu_backgrounds
    global unlocked_felts
    global unlocked_titles

    default_data = (
        make_default_profile()
    )

    apply_profile_save_data(
        default_data
    )

    player_name = "Player"
    profile_name_text = "Player"

def get_profile_avatar():

    avatar_surface = pygame.Surface(
        (
            300,
            360
        ),
        pygame.SRCALPHA
    )

    avatar_surface.blit(
        avatar_bases[
            selected_avatar_base
        ],
        (0, 0)
    )

    avatar_surface.blit(
        avatar_eyes[
            selected_avatar_eyes
        ],
        (0, 0)
    )

    avatar_surface.blit(
        avatar_hair[
            selected_avatar_hair
        ],
        (0, 0)
    )

    if selected_avatar_glasses is not None:
        avatar_surface.blit(
            avatar_glasses[
                selected_avatar_glasses
            ],
            (0, 0)
        )

    avatar_surface.blit(
        avatar_tops[
            selected_avatar_top
        ],
        (0, 0)
    )

    return avatar_surface

def build_profile_save_data():
    from arcade_support import clone_arcade_state as clone_arcade_save_state
    store_event_progress(globals().get("career_event_entry"), globals())

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
    ] = player_name

    profile_data[
        "identity"
    ][
        "gender"
    ] = profile_gender

    identity_data = profile_data["identity"]
    identity_data["country"] = profile_country_text.strip().upper()[:3]
    age_text = profile_age_text.strip()
    identity_data["age"] = int(age_text) if age_text.isdigit() else ""
    identity_data["hometown"] = profile_hometown_text.strip()
    identity_data["favorite_suit"] = profile_favorite_suit
    identity_data["bio"] = profile_bio_text.strip()

    avatar_data = profile_data[
        "identity"
    ][
        "avatar"
    ]

    avatar_data[
        "base"
    ] = selected_avatar_base

    avatar_data[
        "eyes"
    ] = selected_avatar_eyes

    avatar_data[
        "hair"
    ] = selected_avatar_hair

    avatar_data[
        "glasses"
    ] = selected_avatar_glasses

    avatar_data[
        "top"
    ] = selected_avatar_top

    # ----------------------------
    # Progression
    # ----------------------------

    profile_data[
        "progression"
    ][
        "level"
    ] = player_level

    profile_data[
        "progression"
    ][
        "xp"
    ] = player_xp

    profile_data[
        "progression"
    ][
        "solitaire_points"
    ] = player_solitaire_points

    career_data = profile_data[
        "career"
    ]

    # ----------------------------
    # Core progression
    # ----------------------------

    career_data[
        "news_items"
    ] = list(
        career_news_items
    )

    career_data[
        "leaderboard_state"
    ] = copy.deepcopy(
        career_leaderboard_state
    )

    career_data[
        "leaderboard_star_id"
    ] = career_leaderboard_star_id

    career_data[
        "rating"
    ] = career_rating

    career_data[
        "ratings"
    ] = dict(
        career_ratings
    )
    career_data["rating_schema_version"] = 2
    career_data["rating_results"] = copy.deepcopy(career_rating_results)
    career_data["npc_world"] = copy.deepcopy(career_npc_world)

    career_data[
        "cash"
    ] = career_cash

    career_data[
        "fans"
    ] = career_fans

    career_data[
        "fan_rewarded_jobs"
    ] = sorted(career_fan_rewarded_jobs)

    career_data[
        "fan_news_milestones"
    ] = sorted(career_fan_news_milestones)

    # ----------------------------
    # Calendar
    # ----------------------------

    career_data[
        "year"
    ] = career_year

    career_data[
        "month"
    ] = career_month

    career_data[
        "day"
    ] = career_day_of_month

    career_data[
        "weekday_index"
    ] = career_weekday_index

    career_data[
        "career_day"
    ] = career_day

    # ----------------------------
    # Lifestyle
    # ----------------------------

    career_data[
        "residence"
    ] = career_residence

    career_data[
        "owned_residences"
    ] = list(
        career_owned_residences
    )

    career_data[
        "job"
    ] = career_job

    # ----------------------------
    # Statistics
    # ----------------------------

    career_data[
        "rounds_won"
    ] = career_rounds_won

    career_data[
        "challenges_won"
    ] = career_challenges_won

    career_data[
        "total_moves"
    ] = career_total_moves

    # ----------------------------
    # Calendar / event history
    # ----------------------------

    career_data["interview_recent_ids"] = list(career_interview_recent_ids)
    career_data["bigfoot_story"] = copy.deepcopy(career_bigfoot_story)
    career_data["alien_story"] = copy.deepcopy(career_alien_story)

    career_data[
        "completed_days"
    ] = list(
        career_completed_days
    )

    career_data[
        "current_schedule"
    ] = list(
        career_current_schedule
    )

    # ----------------------------
    # News
    # ----------------------------

    career_data[
        "news_items"
    ] = list(
        career_news_items
    )

    career_data[
        "arcade"
    ] = clone_arcade_save_state(
        arcade_state
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
    ] = (
        selected_menu_background
    )

    cosmetics[
        "selected_felt"
    ] = selected_felt

    cosmetics[
        "selected_title"
    ] = selected_title

    cosmetics[
        "selected_cursor"
    ] = selected_cursor

    cosmetics[
        "unlocked_menu_backgrounds"
    ] = list(
        unlocked_menu_backgrounds
    )

    cosmetics[
        "unlocked_felts"
    ] = list(
        unlocked_felts
    )

    cosmetics[
        "unlocked_titles"
    ] = list(
        unlocked_titles
    )

    # Card backs exist in the game
    # now, but are not part of the
    # customization system yet.

    profile_data["achievements"] = {
        "unlocked": list(achievement_state.get("unlocked", [])),
        "stats": dict(achievement_state.get("stats", {})),
    }

    # ----------------------------
    # Gameplay settings
    # ----------------------------

    profile_settings = profile_data.setdefault(
        "settings",
        {}
    )

    profile_settings["score_four_layout"] = getattr(score_four_game, "layout", "compact")

    profile_settings[
        "solitaire_deal_mode"
    ] = game.deal_mode

    profile_data["cryptid_creatures"] = copy.deepcopy(globals().get("cryptid_collection_state", profile_data["cryptid_creatures"]))
    from poker_learning import normalize_learning
    profile_data["poker_learning"] = normalize_learning(globals().get("career_poker_learning"))
    from case_opening import normalize_case_state
    profile_data["case_opening"] = normalize_case_state(globals().get("case_collection_state"))
    return profile_data

def apply_profile_save_data(
        data
):
    from arcade_support import normalize_arcade_state as normalize_arcade_save_state
    global career_bigfoot_story, career_alien_story
    from alien_night import STORY as ALIEN_STORY, refresh_adventure_schedule
    career_bigfoot_story = normalize_story(data.get("career", {}).get("bigfoot_story"))
    career_alien_story = normalize_story(data.get("career", {}).get("alien_story"), data=ALIEN_STORY)
    global career_poker_learning
    from poker_learning import normalize_learning
    career_poker_learning = normalize_learning(data.get("poker_learning"))
    global case_collection_state
    from case_opening import normalize_case_state
    case_collection_state = normalize_case_state(data.get("case_opening"))
    global cryptid_collection_state
    from cryptid_collection import normalize_collection
    cryptid_collection_state = normalize_collection(data.get('cryptid_creatures'),data.get('progression',{}).get('level',1))
    global profile_country_text
    global profile_age_text
    global profile_hometown_text
    global profile_bio_text
    global profile_favorite_suit
    global career_owned_residences
    global career_news_items
    global arcade_state

    global player_solitaire_points

    global career_leaderboard_state
    global career_npc_world
    global career_leaderboard_star_id
    global career_rating
    global career_ratings
    global career_rating_results
    global career_cash
    global career_fans
    global career_fan_rewarded_jobs
    global career_fan_news_milestones

    global career_year
    global career_month
    global career_day_of_month

    global career_weekday_index
    global career_day

    global career_residence
    global career_job

    global career_rounds_won
    global career_challenges_won
    global career_total_moves

    global career_completed_days
    global career_current_schedule

    global career_news_items

    global player_name
    global player_level
    global player_xp
    global player_xp_to_next

    global profile_name_text
    global profile_gender

    global selected_menu_background
    global selected_felt
    global selected_title
    global selected_cursor

    global unlocked_menu_backgrounds
    global unlocked_felts
    global unlocked_titles
    global achievement_state
    global achievements_scroll_y
    global achievement_popup_queue
    global achievement_popup_current

    global selected_avatar_base
    global selected_avatar_eyes
    global selected_avatar_hair
    global selected_avatar_glasses
    global selected_avatar_top

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

    selected_avatar_base = avatar_data.get(
        "base",
        "base_01"
    )

    if selected_avatar_base not in avatar_bases:
        selected_avatar_base = "base_01"

    selected_avatar_eyes = avatar_data.get(
        "eyes",
        "eyes_01"
    )

    if selected_avatar_eyes not in avatar_eyes:
        selected_avatar_eyes = "eyes_01"

    selected_avatar_hair = avatar_data.get(
        "hair",
        "hair_01"
    )

    if selected_avatar_hair not in avatar_hair:
        selected_avatar_hair = "hair_01"

    selected_avatar_glasses = avatar_data.get(
        "glasses",
        None
    )

    if (
            selected_avatar_glasses is not None
            and selected_avatar_glasses not in avatar_glasses
    ):
        selected_avatar_glasses = None

    selected_avatar_top = avatar_data.get(
        "top",
        "top_01"
    )

    if selected_avatar_top not in avatar_tops:
        selected_avatar_top = "top_01"

    player_name = identity.get(
        "name",
        "Player"
    )

    profile_name_text = (
        player_name
    )

    profile_gender = identity.get(
        "gender",
        "non-binary"
    )

    profile_country_text = str(identity.get("country", "") or "").upper()[:3]
    raw_age = identity.get("age", "")
    profile_age_text = str(raw_age) if raw_age not in (None, "") else ""
    profile_hometown_text = str(identity.get("hometown", "") or "")[:48]
    profile_bio_text = str(identity.get("bio", "") or "")[:180]
    profile_favorite_suit = str(identity.get("favorite_suit", "") or "")
    if profile_favorite_suit not in favorite_suit_options:
        profile_favorite_suit = ""

    # ----------------------------
    # Progression
    # ----------------------------

    progression = data.get(
        "progression",
        {}
    )

    player_level = progression.get(
        "level",
        1
    )

    player_xp = progression.get(
        "xp",
        0
    )

    player_solitaire_points = progression.get(
        "solitaire_points",
        0
    )

    player_xp_to_next = (
        get_next_level_xp(
            player_level
        )
    )


    # ----------------------------
    # Core progression
    # ----------------------------

    career_data = data.get(
        "career",
        {}
    )

    career_leaderboard_state = copy.deepcopy(
        career_data.get(
            "leaderboard_state",
            {}
        )
    )

    career_leaderboard_star_id = (
        career_data.get(
            "leaderboard_star_id"
        )
    )
    career_npc_world = copy.deepcopy(career_data.get("npc_world", {}))

    career_rating = career_data.get(
        "rating",
        1000
    )

    career_ratings = normalize_rating_bundle(
        career_data.get(
            "ratings"
        ),
        legacy_rating=career_rating
    )

    career_rating = career_ratings[
        "overall"
    ]
    career_rating_results = copy.deepcopy(career_data.get("rating_results", {}))

    career_cash = career_data.get(
        "cash",
        0
    )

    career_fans = clamp_fans(
        career_data.get(
            "fans",
            0
        )
    )

    career_fan_rewarded_jobs = set(
        career_data.get(
            "fan_rewarded_jobs",
            []
        )
    )

    career_fan_news_milestones = set(
        int(value)
        for value in career_data.get(
            "fan_news_milestones",
            []
        )
        if str(value).isdigit()
    )

    arcade_state = normalize_arcade_save_state(
        career_data.get(
            "arcade",
            {}
        )
    )

    # ----------------------------
    # Calendar
    # ----------------------------

    career_year = career_data.get(
        "year",
        2026
    )

    career_month = career_data.get(
        "month",
        1
    )

    career_day_of_month = career_data.get(
        "day",
        1
    )

    career_weekday_index = (
        career_data.get(
            "weekday_index",
            0
        )
    )

    career_day = career_data.get(
        "career_day",
        1
    )

    # ----------------------------
    # Lifestyle
    # ----------------------------

    career_residence = (
        career_data.get(
            "residence",
            "dingy_apartment"
        )
    )

    career_owned_residences = list(
        career_data.get(
            "owned_residences",
            [
                "dingy_apartment"
            ]
        )
    )

    if (
            "dingy_apartment"
            not in career_owned_residences
    ):
        career_owned_residences.append(
            "dingy_apartment"
        )

    career_job = career_data.get(
        "job",
        "custodian"
    )

    # ----------------------------
    # Statistics
    # ----------------------------

    career_rounds_won = (
        career_data.get(
            "rounds_won",
            0
        )
    )

    career_challenges_won = (
        career_data.get(
            "challenges_won",
            0
        )
    )

    career_total_moves = (
        career_data.get(
            "total_moves",
            0
        )
    )

    # ----------------------------
    # Calendar / events
    # ----------------------------

    career_completed_days = list(
        career_data.get(
            "completed_days",
            []
        )
    )

    career_current_schedule = list(
        career_data.get(
            "current_schedule",
            []
        )
    )

    # ----------------------------
    # News
    # ----------------------------

    career_news_items = list(
        career_data.get(
            "news_items",
            []
        )
    )

    # ----------------------------
    # Achievements
    # ----------------------------

    achievement_state = normalize_achievement_state(
        data.get("achievements", {})
    )
    achievements_scroll_y = 0
    achievement_popup_queue = []
    achievement_popup_current = None

    # ----------------------------
    # Cosmetics
    # ----------------------------

    cosmetics = data.get(
        "cosmetics",
        {}
    )

    selected_menu_background = (
        cosmetics.get(
            "selected_menu_background",
            "bg_default"
        )
    )

    selected_felt = cosmetics.get(
        "selected_felt",
        "f_default"
    )

    selected_title = cosmetics.get(
        "selected_title",
        "title_default"
    )

    selected_cursor = cosmetics.get(
        "selected_cursor",
        "cursor"
    )

    if selected_cursor not in cursor_runtime_surfaces:
        if "cursor" in cursor_runtime_surfaces:
            selected_cursor = "cursor"
        elif cursor_runtime_surfaces:
            selected_cursor = next(
                iter(cursor_runtime_surfaces)
            )

    unlocked_menu_backgrounds = set(
        cosmetics.get(
            "unlocked_menu_backgrounds",
            [
                "bg_default"
            ]
        )
    )

    unlocked_felts = set(
        cosmetics.get(
            "unlocked_felts",
            [
                "f_default"
            ]
        )
    )

    unlocked_titles = set(
        cosmetics.get(
            "unlocked_titles",
            [
                "title_default"
            ]
        )
    )

    gameplay_settings = data.get(
        "settings",
        {}
    )

    score_four_game.layout = "wide" if gameplay_settings.get("score_four_layout") == "wide" else "compact"

    requested_deal_mode = gameplay_settings.get(
        "solitaire_deal_mode",
        "random"
    )
    if not VERIFIED_DEALS_ENABLED and requested_deal_mode == "verified":
        requested_deal_mode = "random"
    game.set_deal_mode(requested_deal_mode)

    global career_interview_recent_ids
    for entry in career_current_schedule:
        if entry.get("event_id") == "career_encounter" and not entry.get("completed"):
            entry.update(title="Bigfoot Night", event_id="bigfoot_night")
    history = data.get("career", {}).get("interview_recent_ids", [])
    career_interview_recent_ids = [value for value in history if isinstance(value, str)][-12:] if isinstance(history, list) else []
    reconcile_story_cosmetics(career_bigfoot_story, unlocked_menu_backgrounds, unlocked_felts, unlocked_titles)
    reconcile_story_cosmetics(career_alien_story, unlocked_menu_backgrounds, unlocked_felts, unlocked_titles, data=ALIEN_STORY)
    refresh_adventure_schedule(career_current_schedule, career_bigfoot_story, career_alien_story, career_day_of_month)
    sync_achievement_cosmetic_rewards()
    grant_rating_cosmetics(force=True)
    sync_career_npc_runtime_state()
    sync_selected_cosmetics()
    apply_selected_cursor()

def draw_wrapped_text_limited(
        text,
        font,
        color,
        rect,
        max_lines,
        line_spacing=2
):

    words = text.split()

    lines = []
    current_line = ""

    for word in words:

        test_line = (
            current_line + " " + word
            if current_line
            else word
        )

        test_width = font.size(
            test_line
        )[0]

        if test_width <= rect.width:

            current_line = test_line

        else:

            if current_line:
                lines.append(
                    current_line
                )

            current_line = word

    if current_line:
        lines.append(
            current_line
        )

    # ----------------------------------------------
    # Limit visible lines
    # ----------------------------------------------

    lines = lines[
        :max_lines
    ]

    # Add ... if text was cut off
    if len(lines) == max_lines:

        displayed_text = " ".join(
            lines
        )

        if len(displayed_text) < len(
            text
        ):

            last_line = lines[
                -1
            ]

            while (
                font.size(
                    last_line + "..."
                )[0]
                > rect.width
                and last_line
            ):

                last_line = (
                    last_line[:-1]
                )

            lines[
                -1
            ] = (
                last_line.rstrip()
                + "..."
            )

    y = rect.y

    for line in lines:

        surface = font.render(
            line,
            True,
            color
        )

        game_surface.blit(
            surface,
            (
                rect.x,
                y
            )
        )

        y += (
            font.get_linesize()
            + line_spacing
        )

def draw_wrapped_text(
        text,
        font,
        color,
        rect,
        line_spacing=4
):
    words = text.split()

    lines = []

    current_line = ""

    for word in words:

        test_line = (
            word
            if not current_line
            else current_line
            + " "
            + word
        )

        test_surface = font.render(
            test_line,
            True,
            color
        )

        if (
            test_surface.get_width()
            <= rect.width
        ):
            current_line = (
                test_line
            )

        else:
            if current_line:
                lines.append(
                    current_line
                )

            current_line = (
                word
            )

    if current_line:
        lines.append(
            current_line
        )

    y = rect.y

    for line in lines:

        surface = font.render(
            line,
            True,
            color
        )

        game_surface.blit(
            surface,
            (
                rect.x,
                y
            )
        )

        y += (
            surface.get_height()
            + line_spacing
        )

def draw_score_four_opponent_select():
    from score_four_ui import background, logo, text
    background(game_surface)
    logo(game_surface)
    text(game_surface, 'Choose a rival', (683, 140), 32, center=True)
    text(game_surface, 'Win rewards include your Strategy rating adjustment', (683, 614), 24, center=True)

    for index, npc in enumerate(
            score_four_opponent_choices
    ):

        if index >= len(
                score_four_opponent_rects
        ):
            break

        rect = (
            score_four_opponent_rects[
                index
            ]
        )

        hovered = (
            game_mouse_pos is not None
            and rect.collidepoint(
                game_mouse_pos
            )
        )

        # ==========================================
        # Panel background
        # ==========================================

        panel = pygame.Surface(
            (
                rect.width,
                rect.height
            ),
            pygame.SRCALPHA
        )

        if hovered:

            panel.fill(
                (
                    255,
                    255,
                    255,
                    55
                )
            )

        else:

            panel.fill(
                (
                    0,
                    0,
                    0,
                    150
                )
            )

        game_surface.blit(
            panel,
            rect.topleft
        )

        pygame.draw.rect(
            game_surface,
            (
                210,
                210,
                210
            ),
            rect,
            2
        )

        # ==========================================
        # Portrait
        # ==========================================

        portrait_rect = pygame.Rect(
            rect.x + 18,
            rect.y + 22,
            105,
            105
        )

        draw_npc_portrait(
            npc,
            portrait_rect,
            "score_four"
        )

        # ==========================================
        # Name
        # ==========================================

        name_surface = (
            option_label_font.render(
                npc["name"],
                True,
                (
                    255,
                    255,
                    255
                )
            )
        )

        game_surface.blit(
            name_surface,
            (
                rect.x + 145,
                rect.y + 22
            )
        )

        # ==========================================
        # Tier
        # ==========================================

        tier_text = (
            SCORE_FOUR_TIER_DISPLAY_NAMES.get(
                npc["skill_tier"],
                npc["skill_tier"]
            ).upper()
        )

        tier_surface = (
            score_four_round_font.render(
                tier_text,
                True,
                (
                    255,
                    230,
                    0
                )
            )
        )

        game_surface.blit(
            tier_surface,
            (
                rect.x + 145,
                rect.y + 60
            )
        )

        # ==========================================
        # Location
        # ==========================================

        location_surface = (
            difficulty_detail_font.render(
                npc["hometown"],
                True,
                (
                    220,
                    220,
                    220
                )
            )
        )

        game_surface.blit(
            location_surface,
            (
                rect.x + 145,
                rect.y + 95
            )
        )

        if current_game_mode != "free":
            gain = preview_competitive_rating("score_four", npc, True)
            loss = preview_competitive_rating("score_four", npc, False)
            reward_text = f"Win {gain:+d} / Loss {loss:+d} Strategy"
        else:
            reward_text = "Practice • No rating changes"
        reward_label = pygame.font.Font(None, 24).render(reward_text, True, (225, 239, 244))
        game_surface.blit(reward_label, reward_label.get_rect(center=(rect.centerx, rect.bottom - 24)))

    draw_menu_button(
        score_four_opponent_return_rect,
        "Return",
        game_mouse_pos,
        font=difficulty_detail_font
    )

def draw_score_four_npc_panel():

    if (
            score_four_game.mode
            != "competitive"
            or score_four_opponent_npc is None
    ):
        return

    npc_panel = pygame.Rect(
        1040,
        180,
        285,
        235
    )

    pygame.draw.rect(
        game_surface,
        (
            25,
            45,
            30
        ),
        npc_panel
    )

    pygame.draw.rect(
        game_surface,
        (
            255,
            255,
            255
        ),
        npc_panel,
        2
    )

    avatar_rect = pygame.Rect(
        npc_panel.x + 15,
        npc_panel.y + 15,
        80,
        80
    )

    draw_npc_portrait(
        score_four_opponent_npc,
        avatar_rect,
        "score_four"
    )

    # ==================================================
    # NPC name
    # ==================================================

    npc_name_surface = (
        score_four_npc_font.render(
            score_four_opponent_npc[
                "name"
            ],
            True,
            (
                255,
                255,
                255
            )
        )
    )

    game_surface.blit(
        npc_name_surface,
        (
            npc_panel.x + 110,
            npc_panel.y + 20
        )
    )

    # ==================================================
    # Skill display
    # ==================================================

    tier_name = (
        SCORE_FOUR_TIER_DISPLAY_NAMES.get(
            score_four_opponent_npc[
                "skill_tier"
            ],
            score_four_opponent_npc[
                "skill_tier"
            ]
        )
    )

    tier_surface = (
        score_four_round_font.render(
            tier_name,
            True,
            (
                255,
                230,
                0
            )
        )
    )

    game_surface.blit(
        tier_surface,
        (
            npc_panel.x + 110,
            npc_panel.y + 60
        )
    )

    # ==================================================
    # Status
    # ==================================================

    if score_four_game.round_complete:

        thinking_text = "Finished"

    else:

        thinking_text = "Thinking..."

    thinking_surface = (
        score_four_round_font.render(
            thinking_text,
            True,
            (
                220,
                220,
                220
            )
        )
    )

    game_surface.blit(
        thinking_surface,
        (
            npc_panel.x + 15,
            npc_panel.y + 125
        )
    )

    # ==================================================
    # Progress bar
    # ==================================================

    progress = (
        get_score_four_npc_progress()
    )

    bar_rect = pygame.Rect(
        npc_panel.x + 15,
        npc_panel.y + 170,
        npc_panel.width - 30,
        24
    )

    pygame.draw.rect(
        game_surface,
        (
            80,
            80,
            80
        ),
        bar_rect
    )

    fill_rect = pygame.Rect(
        bar_rect.x,
        bar_rect.y,
        int(
            bar_rect.width
            * progress
        ),
        bar_rect.height
    )

    pygame.draw.rect(
        game_surface,
        (
            220,
            220,
            220
        ),
        fill_rect
    )

    pygame.draw.rect(
        game_surface,
        (
            255,
            255,
            255
        ),
        bar_rect,
        2
    )



def settle_score_four_session_result():
    """Bank the completed result once, before the player dismisses the screen."""
    global career_event_has_activity
    if score_four_game.reward_claimed:
        return
    if score_four_game.mode == "solo" and score_four_game.session_complete:
        rating_change = award_career_rating('score_four', {'easy': 30, 'standard': 50, 'difficult': 70, 'extreme': 90}[score_four_game.difficulty])
        if current_game_mode == 'career':
            record_result(career_rating_results, 'score_four', 1.0, rating_change)
        award_fans_for_rating_win(rating_change, 'Score-Four completion')
        process_achievement_event('score_four_win', mode='solo')
        award_game_xp('score_four_solo', won=True)
        record_career_event_result('score_four', won=True, mode='solo')
        score_four_game.reward_claimed = True
        career_event_has_activity = True
    elif score_four_game.mode == "competitive" and score_four_game.match_complete:
        player_won_match = score_four_game.match_winner == 'player'
        rating_change = rate_competitive_game('score_four', score_four_opponent_npc, player_won_match)
        if player_won_match:
            award_fans_for_rating_win(rating_change, 'Competitive Score-Four win')
            process_achievement_event('score_four_win', mode='competitive')
        award_game_xp('score_four_competitive', won=player_won_match)
        record_career_event_result('score_four', won=player_won_match, mode='competitive', opponent=score_four_opponent_npc.get('name') if isinstance(score_four_opponent_npc, dict) else 'NPC', opponent_tier=score_four_opponent_npc.get('skill_tier') if isinstance(score_four_opponent_npc, dict) else 'mid', rating_reward=rating_change)
        score_four_game.reward_claimed = True
        career_event_has_activity = True
    else:
        return
    score_four_game.last_rating_change = rating_change


def draw_score_four():
    from score_four_ui import draw_score_four_table
    settle_score_four_session_result()
    draw_score_four_table(game_surface, score_four_game, game_mouse_pos, globals())


def draw_solitaire_help_diagram(panel_rect):

    # ------------------------------------------
    # Diagram container
    # ------------------------------------------

    diagram_rect = pygame.Rect(
        panel_rect.x + panel_rect.width - 470,
        panel_rect.y + 60,
        440,
        280
    )

    pygame.draw.rect(
        game_surface,
        (245, 245, 240),
        diagram_rect
    )

    pygame.draw.rect(
        game_surface,
        (0, 0, 0),
        diagram_rect,
        2
    )

    # ------------------------------------------
    # Title
    # ------------------------------------------

    title_surface = option_label_font.render(
        "BOARD LAYOUT",
        True,
        (0, 0, 0)
    )

    game_surface.blit(
        title_surface,
        (
            diagram_rect.x + 15,
            diagram_rect.y + 4
        )
    )

    # ------------------------------------------
    # Mini card sizes
    # ------------------------------------------

    card_w = 42
    card_h = 58

    top_y = diagram_rect.y + 50
    left_x = diagram_rect.x + 20

    # ------------------------------------------
    # Stock
    # ------------------------------------------

    stock_rect = pygame.Rect(
        left_x,
        top_y,
        card_w,
        card_h
    )

    pygame.draw.rect(
        game_surface,
        (220, 220, 220),
        stock_rect
    )

    pygame.draw.rect(
        game_surface,
        (0, 0, 0),
        stock_rect,
        2
    )

    stock_label = difficulty_detail_font.render(
        "Stock",
        True,
        (0, 0, 0)
    )

    game_surface.blit(
        stock_label,
        (
            stock_rect.x - 2,
            stock_rect.y - 22
        )
    )

    # ------------------------------------------
    # Waste
    # ------------------------------------------

    waste_rect = pygame.Rect(
        left_x + 65,
        top_y,
        card_w,
        card_h
    )

    pygame.draw.rect(
        game_surface,
        (255, 255, 255),
        waste_rect
    )

    pygame.draw.rect(
        game_surface,
        (0, 0, 0),
        waste_rect,
        2
    )

    waste_label = difficulty_detail_font.render(
        "Waste",
        True,
        (0, 0, 0)
    )

    game_surface.blit(
        waste_label,
        (
            waste_rect.x - 3,
            waste_rect.y - 22
        )
    )

    # ------------------------------------------
    # Foundations
    # ------------------------------------------

    foundation_label = difficulty_detail_font.render(
        "Foundations",
        True,
        (0, 0, 0)
    )

    game_surface.blit(
        foundation_label,
        (
            diagram_rect.x + 245,
            top_y - 22
        )
    )

    foundation_start_x = diagram_rect.x + 230

    for i in range(4):
        foundation_rect = pygame.Rect(
            foundation_start_x + i * 48,
            top_y,
            card_w,
            card_h
        )

        pygame.draw.rect(
            game_surface,
            (255, 255, 255),
            foundation_rect
        )

        pygame.draw.rect(
            game_surface,
            (0, 0, 0),
            foundation_rect,
            2
        )

    # ------------------------------------------
    # Tableau
    # ------------------------------------------

    tableau_label = difficulty_detail_font.render(
        "Tableau",
        True,
        (0, 0, 0)
    )

    game_surface.blit(
        tableau_label,
        (
            diagram_rect.x + 15,
            top_y + 85
        )
    )

    tableau_y = top_y + 110

    for col in range(7):

        col_x = diagram_rect.x + 15 + col * 58

        # top card
        base_rect = pygame.Rect(
            col_x,
            tableau_y,
            card_w,
            card_h
        )

        pygame.draw.rect(
            game_surface,
            (255, 255, 255),
            base_rect
        )

        pygame.draw.rect(
            game_surface,
            (0, 0, 0),
            base_rect,
            2
        )

        # a couple stacked cards
        for offset in range(1, 3):
            stacked_rect = pygame.Rect(
                col_x,
                tableau_y + offset * 14,
                card_w,
                card_h
            )

            pygame.draw.rect(
                game_surface,
                (245, 245, 245),
                stacked_rect
            )

            pygame.draw.rect(
                game_surface,
                (0, 0, 0),
                stacked_rect,
                2
            )

def draw_score_four_mode_select():
    from score_four_ui import draw_difficulty_select, draw_mode_select
    if score_four_game.difficulty_menu:
        draw_difficulty_select(game_surface, game_mouse_pos, globals())
    else:
        draw_mode_select(game_surface, score_four_game, game_mouse_pos, globals())

# ==================================================
# WINDOW HELPERS
# ==================================================

def invalidate_scaled_surface_cache():
    global scaled_surface_cache
    scaled_surface_cache = None


def set_window_size(width, height):
    global screen
    global WINDOW_WIDTH
    global WINDOW_HEIGHT
    global WINDOWED_WIDTH
    global WINDOWED_HEIGHT
    global fullscreen_enabled

    WINDOWED_WIDTH = int(width)
    WINDOWED_HEIGHT = int(height)

    # Choosing a window size while fullscreen is active
    # returns the game to a normal window at that size.
    fullscreen_enabled = False

    WINDOW_WIDTH = WINDOWED_WIDTH
    WINDOW_HEIGHT = WINDOWED_HEIGHT

    screen = pygame.display.set_mode(
        (
            WINDOW_WIDTH,
            WINDOW_HEIGHT
        )
    )

    invalidate_scaled_surface_cache()
    apply_selected_cursor()


def set_fullscreen_enabled(enabled):
    global screen
    global WINDOW_WIDTH
    global WINDOW_HEIGHT
    global WINDOWED_WIDTH
    global WINDOWED_HEIGHT
    global fullscreen_enabled

    enabled = bool(enabled)

    if enabled == fullscreen_enabled:
        return

    if enabled:
        WINDOWED_WIDTH = WINDOW_WIDTH
        WINDOWED_HEIGHT = WINDOW_HEIGHT

        screen = pygame.display.set_mode(
            (0, 0),
            pygame.FULLSCREEN
        )

        WINDOW_WIDTH, WINDOW_HEIGHT = (
            screen.get_size()
        )

        fullscreen_enabled = True

    else:
        WINDOW_WIDTH = WINDOWED_WIDTH
        WINDOW_HEIGHT = WINDOWED_HEIGHT

        screen = pygame.display.set_mode(
            (
                WINDOW_WIDTH,
                WINDOW_HEIGHT
            )
        )

        fullscreen_enabled = False

    invalidate_scaled_surface_cache()
    apply_selected_cursor()


def window_to_game_coords(pos):
    x, y = pos

    game_x = int(
        x
        * BASE_WIDTH
        / WINDOW_WIDTH
    )

    game_y = int(
        y
        * BASE_HEIGHT
        / WINDOW_HEIGHT
    )

    return (
        game_x,
        game_y
    )

# ==================================================
# CUSTOMIZATION HELPERS
# ==================================================

def scale_surface_to_fit(
    surface,
    max_width,
    max_height
):
    width = surface.get_width()
    height = surface.get_height()

    if width == 0 or height == 0:
        return surface

    scale = min(
        max_width / width,
        max_height / height
    )

    new_width = max(
        1,
        int(width * scale)
    )

    new_height = max(
        1,
        int(height * scale)
    )

    return pygame.transform.smoothscale(
        surface,
        (
            new_width,
            new_height
        )
    )

debug_xp_rect = pygame.Rect(
    20,
    20,
    180,
    45
)

def refresh_cosmetic_assets():
    background_catalog.refresh()
    title_catalog.refresh()
    if felt_catalog.refresh():
        sync_selected_cosmetics()


def cosmetic_art_available(asset_id):
    catalog = {CUSTOMIZE_BACKGROUNDS: background_catalog,
               CUSTOMIZE_FELTS: felt_catalog, CUSTOMIZE_TITLES: title_catalog}.get(customize_category)
    return catalog.available(asset_id) if catalog is not None else True


def get_customize_data():
    refresh_cosmetic_assets()
    if current_game_mode in ("career", "head_to_head") or current_profile_slot is not None:
        unlock_ratings(career_ratings, (MENU_BACKGROUNDS, FELTS, TITLES),
                       (unlocked_menu_backgrounds, unlocked_felts, unlocked_titles))
    if customize_category == CUSTOMIZE_BACKGROUNDS:
        return (
            MENU_BACKGROUNDS,
            menu_background_surfaces,
            unlocked_menu_backgrounds,
            selected_menu_background
        )

    if customize_category == CUSTOMIZE_FELTS:
        return (
            FELTS,
            felt_surfaces,
            unlocked_felts,
            selected_felt
        )

    if customize_category == CUSTOMIZE_TITLES:
        return (
            TITLES,
            title_surfaces,
            unlocked_titles,
            selected_title
        )

    return (
        cursor_cosmetics,
        cursor_preview_surfaces,
        unlocked_cursors,
        selected_cursor
    )


def get_customize_asset_ids():
    asset_data, _, _, _ = (
        get_customize_data()
    )

    return sorted(
        asset_data.keys(),
        key=lambda asset_id: (
            asset_data[
                asset_id
            ].get(
                "order",
                9999
            )
        )
    )


def get_customize_page_count():
    asset_ids = (
        get_customize_asset_ids()
    )

    if not asset_ids:
        return 1

    return max(
        1,
        (
            len(asset_ids)
            + CUSTOMIZE_ITEMS_PER_PAGE
            - 1
        )
        // CUSTOMIZE_ITEMS_PER_PAGE
    )


def equip_customize_item(asset_id):
    global selected_menu_background
    global selected_felt
    global selected_title
    global selected_cursor

    refresh_cosmetic_assets()
    if not cosmetic_art_available(asset_id):
        return

    if customize_category == CUSTOMIZE_BACKGROUNDS:
        if asset_id not in unlocked_menu_backgrounds:
            return

        selected_menu_background = asset_id

    elif customize_category == CUSTOMIZE_FELTS:
        if asset_id not in unlocked_felts:
            return

        selected_felt = asset_id

        sync_selected_cosmetics()

    elif customize_category == CUSTOMIZE_TITLES:
        if asset_id not in unlocked_titles:
            return

        selected_title = asset_id

    elif customize_category == CUSTOMIZE_CURSORS:
        if asset_id not in unlocked_cursors:
            return

        selected_cursor = asset_id
        apply_selected_cursor()

def get_unlock_asset_data(
    unlock_type,
    asset_id
):
    if unlock_type == 'cryptid_pack':
        return ({'name':f'{asset_id} Creature Card Packs'},None,'Cryptid Creatures')
    if unlock_type == "background":
        return (
            MENU_BACKGROUNDS[asset_id],
            menu_background_surfaces[
                asset_id
            ],
            "Menu Background"
        )

    if unlock_type == "felt":
        return (
            FELTS[asset_id],
            felt_surfaces[
                asset_id
            ],
            "Felt Background"
        )

    if unlock_type == "title":
        return (
            TITLES[asset_id],
            title_surfaces[
                asset_id
            ],
            "Menu Title"
        )

    return (
        {
            "name": asset_id
        },
        None,
        "Unlock"
    )

def advance_level_up_screen():
    global current_state
    global current_level_up_data
    global level_up_queue
    global post_round_return_state

    if level_up_queue:
        current_level_up_data = (
            level_up_queue.pop(0)
        )

        current_state = (
            STATE_LEVEL_UP
        )


    else:

        current_level_up_data = None

        current_state = (

            post_round_return_state

        )

def get_npc_leaderboard_snapshot():

    rankings = []

    for npc in CAREER_LEADERBOARD_PLAYERS:

        npc_id = npc.get(
            "id"
        )

        if (
            npc_id is None
            or npc_id
            not in career_leaderboard_state
        ):
            continue

        rankings.append(
            {
                "id":
                    npc_id,

                "name":
                    npc.get(
                        "name",
                        "Unknown Player"
                    ),

                "rating":
                    career_leaderboard_state[
                        npc_id
                    ].get(
                        "rating",
                        1000
                    ),
            }
        )

    rankings.sort(
        key=lambda item:
            item[
                "rating"
            ],
        reverse=True
    )

    return rankings

def get_solitaire_rating_reward(current_rating):
    return 40

def add_monthly_leaderboard_news(
        before,
        after
):

    if not before or not after:
        return

    before_rank = {
        entry[
            "id"
        ]:
            index + 1

        for index, entry
        in enumerate(
            before
        )
    }

    after_rank = {
        entry[
            "id"
        ]:
            index + 1

        for index, entry
        in enumerate(
            after
        )
    }

    # ==================================================
    # World #1
    # ==================================================

    old_number_one = (
        before[
            0
        ]
    )

    new_number_one = (
        after[
            0
        ]
    )

    if (
        old_number_one[
            "id"
        ]
        !=
        new_number_one[
            "id"
        ]
    ):

        add_career_news(
            (
                f"{new_number_one['name'].upper()} "
                f"SEIZES WORLD #1"
            ),
            (
                f"{new_number_one['name']} has overtaken "
                f"{old_number_one['name']} for the top spot "
                f"in the international Global rankings."
            ),
            "leaderboard"
        )

    else:

        add_career_news(
            (
                f"{new_number_one['name'].upper()} "
                f"RETAINS WORLD #1"
            ),
            (
                f"{new_number_one['name']} remains atop "
                f"the international rankings with a rating "
                f"of {new_number_one['rating']:,}."
            ),
            "leaderboard"
        )

    # ==================================================
    # Biggest climber
    # ==================================================

    biggest_riser = None
    biggest_rise = 0

    for entry in after:

        npc_id = entry[
            "id"
        ]

        if (
            npc_id
            not in before_rank
        ):
            continue

        movement = (
            before_rank[
                npc_id
            ]
            - after_rank[
                npc_id
            ]
        )

        if movement > biggest_rise:

            biggest_rise = (
                movement
            )

            biggest_riser = (
                entry
            )

    if (
        biggest_riser is not None
        and biggest_rise >= 2
    ):

        add_career_news(
            (
                f"{biggest_riser['name'].upper()} "
                f"SURGES UP RANKINGS"
            ),
            (
                f"{biggest_riser['name']} climbed "
                f"{biggest_rise} places this month "
                f"and now sits at world "
                f"#{after_rank[biggest_riser['id']]}."
            ),
            "leaderboard"
        )

    # ==================================================
    # Biggest fall
    # ==================================================

    biggest_faller = None
    biggest_fall = 0

    for entry in after:

        npc_id = entry[
            "id"
        ]

        if (
            npc_id
            not in before_rank
        ):
            continue

        movement = (
            after_rank[
                npc_id
            ]
            - before_rank[
                npc_id
            ]
        )

        if movement > biggest_fall:

            biggest_fall = (
                movement
            )

            biggest_faller = (
                entry
            )

    if (
        biggest_faller is not None
        and biggest_fall >= 2
    ):

        add_career_news(
            (
                f"ROUGH MONTH FOR "
                f"{biggest_faller['name'].upper()}"
            ),
            (
                f"{biggest_faller['name']} fell "
                f"{biggest_fall} places in the international "
                f"rankings and now sits at world "
                f"#{after_rank[biggest_faller['id']]}."
            ),
            "leaderboard"
        )

# ==================================================
# LEVEL / XP HELPERS
# ==================================================

def get_level_from_xp(xp):
    level = 1

    for candidate_level in sorted(
        LEVEL_XP_THRESHOLDS.keys()
    ):
        required_xp = (
            LEVEL_XP_THRESHOLDS[
                candidate_level
            ]
        )

        if xp >= required_xp:
            level = candidate_level
        else:
            break

    return level


def get_next_level_xp(level):
    next_level = level + 1

    if next_level in LEVEL_XP_THRESHOLDS:
        return LEVEL_XP_THRESHOLDS[
            next_level
        ]

    return None

def sync_unlocks_for_current_level():
    for level in sorted(
            LEVEL_UNLOCKS.keys()
    ):
        if level > player_level:
            break

        rewards = LEVEL_UNLOCKS.get(
            level,
            {}
        )

        for asset_id in rewards.get(
                "backgrounds",
                []
        ):
            unlocked_menu_backgrounds.add(
                asset_id
            )

        for asset_id in rewards.get(
                "felts",
                []
        ):
            unlocked_felts.add(
                asset_id
            )

        for asset_id in rewards.get(
                "titles",
                []
        ):
            unlocked_titles.add(
                asset_id
            )

def unlock_rewards_for_level(level):
    rewards = LEVEL_UNLOCKS.get(
        level,
        {}
    )

    newly_unlocked = []

    # ----------------------------
    # Backgrounds
    # ----------------------------

    for asset_id in rewards.get(
        "backgrounds",
        []
    ):
        if (
            asset_id
            not in unlocked_menu_backgrounds
        ):
            unlocked_menu_backgrounds.add(
                asset_id
            )

            newly_unlocked.append(
                (
                    "background",
                    asset_id
                )
            )

    # ----------------------------
    # Felts
    # ----------------------------

    for asset_id in rewards.get(
        "felts",
        []
    ):
        if asset_id not in unlocked_felts:
            unlocked_felts.add(
                asset_id
            )

            newly_unlocked.append(
                (
                    "felt",
                    asset_id
                )
            )

    # ----------------------------
    # Titles
    # ----------------------------

    for asset_id in rewards.get(
        "titles",
        []
    ):
        if asset_id not in unlocked_titles:
            unlocked_titles.add(
                asset_id
            )

            newly_unlocked.append(
                (
                    "title",
                    asset_id
                )
            )

    # ----------------------------
    # Games
    # ----------------------------

    for game_id in rewards.get(
            "games",
            []
    ):
        newly_unlocked.append(
            (
                "game",
                game_id
            )
        )

    return newly_unlocked

def add_player_xp(amount):
    global player_xp
    global player_level
    global player_xp_to_next

    old_level = player_level

    player_xp += max(
        0,
        amount
    )

    new_level = get_level_from_xp(
        player_xp
    )

    level_ups = []
    unlocked_items = []

    level_up_screens = []

    if new_level > old_level:
        for level in range(
            old_level + 1,
            new_level + 1
        ):
            level_ups.append(
                level
            )

            level_unlocks = (
                unlock_rewards_for_level(
                    level
                )
            )

            if globals().get('cryptid_collection_state') is not None:
                from cryptid_collection import award_level_packs
                packs=award_level_packs(cryptid_collection_state,level)
                if packs:level_unlocks.append(('cryptid_pack',str(packs)))
            unlocked_items.extend(
                level_unlocks
            )

            level_up_screens.append(
                {
                    "level": level,
                    "unlocks": level_unlocks,
                }
            )

    player_level = new_level

    next_threshold = get_next_level_xp(
        player_level
    )

    if next_threshold is None:
        player_xp_to_next = None

    else:
        player_xp_to_next = (
            next_threshold
        )

    return {
        "old_level": old_level,
        "new_level": new_level,
        "level_ups": level_ups,
        "unlocked_items": unlocked_items,
        "level_up_screens": level_up_screens,
        "xp_added": amount,
        "total_xp": player_xp,
    }

def apply_round_rewards(
        round_data
):
    global player_solitaire_points

    global career_rating
    global career_cash


    # ==================================================
    # XP
    # ==================================================

    xp_earned = round_data.get(
        "xp_earned",
        0
    )

    progression_result = (
        add_player_xp(
            xp_earned
        )
    )

    print(
        "XP DEBUG:",
        "earned =",
        xp_earned,
        "| total XP =",
        progression_result[
            "total_xp"
        ],
        "| old level =",
        progression_result[
            "old_level"
        ],
        "| new level =",
        progression_result[
            "new_level"
        ],
        "| screens =",
        progression_result[
            "level_up_screens"
        ]
    )

    # ==================================================
    # Solitaire Points
    #
    # XP already includes the difficulty multiplier,
    # so SP inherits that benefit naturally.
    # ==================================================

    sp_earned = max(
        1,
        xp_earned // 2
    )

    player_solitaire_points += (
        sp_earned
    )

    round_data[
        "sp_earned"
    ] = sp_earned

    # Defaults for Free Play
    round_data[
        "cash_earned"
    ] = 0

    round_data[
        "rating_change"
    ] = 0

    # ==================================================
    # Career rewards
    # ==================================================

    if current_game_mode == "career":
        reward_multiplier = (
            round_data.get(
                "reward_multiplier",
                1.0
            )
        )

        base_cash = (
                100
                + round_data.get(
            "score",
            0
        ) // 100
        )

        cash_earned = max(
            1,
            int(
                round(
                    base_cash
                    * reward_multiplier
                )
            )
        )

        base_rating_change = (
            get_solitaire_rating_reward(
                career_ratings["solitaire"]
            )
        )

        rating_change = max(
            1,
            int(
                round(
                    base_rating_change
                    * reward_multiplier
                )
            )
        )

        career_cash += (
            cash_earned
        )

        rating_change = award_career_rating("solitaire", rating_change)
        record_result(career_rating_results, "solitaire", 1.0, rating_change)

        fans_earned = award_fans_for_rating_win(
            rating_change,
            "Solitaire win"
        )

        round_data[
            "cash_earned"
        ] = cash_earned

        round_data[
            "rating_change"
        ] = rating_change

        round_data[
            "fans_earned"
        ] = fans_earned

    return progression_result

def sync_career_npc_runtime_state():
    """Migrate at the current date and restore this profile's complete roster."""
    global career_npc_world
    if career_leaderboard_state:
        career_npc_world = ensure_career_world(
            career_npc_world, career_leaderboard_state, BASE_NPCS,
            career_year, career_month,
        )
    sync_npc_runtime_state(career_leaderboard_state, month=career_month)



def ensure_career_leaderboard():

    if not career_leaderboard_state:
        initialize_career_leaderboard()

        auto_save_career()
    else:
        sync_career_npc_runtime_state()

def initialize_career_leaderboard():
    global career_leaderboard_state
    global career_npc_world
    global career_leaderboard_star_id

    career_leaderboard_state = {}
    career_npc_world = {}
    sync_npc_runtime_state({})

    if not CAREER_LEADERBOARD_PLAYERS:
        return

    # ==================================================
    # Pick this career's superstar
    # ==================================================

    elite_candidates = [
        npc
        for npc in CAREER_LEADERBOARD_PLAYERS
        if npc.get(
            "skill_tier"
        ) == "elite"
    ]

    if elite_candidates:
        star = random.choice(
            elite_candidates
        )

    else:
        star = random.choice(
            CAREER_LEADERBOARD_PLAYERS
        )

    career_leaderboard_star_id = (
        star.get(
            "id"
        )
    )

    # ==================================================
    # Rating ranges
    # ==================================================

    rating_ranges = {
        "elite":
            (
                2150,
                2800
            ),

        "strong":
            (
                1650,
                2200
            ),

        "mid":
            (
                1150,
                1750
            ),

        "low":
            (
                750,
                1300
            ),
    }

    # ==================================================
    # Generate everybody
    # ==================================================

    for npc in CAREER_LEADERBOARD_PLAYERS:

        npc_id = npc.get(
            "id"
        )

        if npc_id is None:
            continue

        tier = npc.get(
            "skill_tier",
            "mid"
        )

        minimum, maximum = (
            rating_ranges.get(
                tier,
                rating_ranges[
                    "mid"
                ]
            )
        )

        rating = random.randint(
            minimum,
            maximum
        )

        npc_state = {
            "rating": rating,
            "last_change": 0,
            "ratings": make_npc_rating_bundle(
                rating,
                tier
            ),
        }

        career_leaderboard_state[
            npc_id
        ] = ensure_npc_career_state(
            npc_state,
            npc
        )

    # ==================================================
    # Give one player a Magnus-style lead
    # ==================================================

    if (
        career_leaderboard_star_id
        in career_leaderboard_state
    ):

        other_ratings = [
            data.get(
                "rating",
                1000
            )
            for npc_id, data
            in career_leaderboard_state.items()
            if npc_id
            != career_leaderboard_star_id
        ]

        if other_ratings:

            second_best = max(
                other_ratings
            )

            star_rating = (
                second_best
                + random.randint(
                    175,
                    325
                )
            )

            star_state = career_leaderboard_state[
                career_leaderboard_star_id
            ]

            boost_npc_overall(star_state, star_rating)

    sync_career_npc_runtime_state()

def get_career_leaderboard(
        rating_key="overall"
):

    ensure_career_leaderboard()

    if rating_key not in RATING_KEYS:
        rating_key = "overall"

    leaderboard = []

    for npc in CAREER_LEADERBOARD_PLAYERS:

        npc_id = npc.get(
            "id"
        )

        npc_state = (
            career_leaderboard_state.get(
                npc_id,
                {}
            )
        )

        npc_state = ensure_npc_career_state(
            npc_state,
            npc
        )

        career_leaderboard_state[
            npc_id
        ] = npc_state

        ratings = npc_state.get(
            "ratings",
            {}
        )

        selected_rating = ratings.get(
            rating_key,
            npc_state.get(
                "rating",
                1000
            )
        )

        monthly_change = npc_state.get("last_changes", {}).get(rating_key, 0)

        leaderboard.append(
            {
                "id": npc_id,
                "name": npc.get(
                    "name",
                    "Unknown Player"
                ),
                "rating": selected_rating,
                "rating_key": rating_key,
                "rating_label": RATING_DISPLAY_NAMES.get(
                    rating_key,
                    "Global"
                ),
                "ratings": dict(ratings),
                "last_change": monthly_change,
                "bio": npc.get(
                    "bio",
                    "Professional card player."
                ),
                "country": npc.get(
                    "country",
                    "Unknown"
                ),
                "age": npc_state.get(
                    "age",
                    npc.get(
                        "age",
                        "Unknown"
                    )
                ),
                "birthday_month": npc_state.get(
                    "birthday_month"
                ),
                "hometown": npc.get(
                    "hometown",
                    "Unknown"
                ),
                "favorite_suit": npc.get(
                    "favorite_suit",
                    "Unknown"
                ),
                "game_personality": npc.get(
                    "game_personality",
                    "balanced"
                ),
                "career_stage": development_stage(npc_state, career_month),
                "is_prospect": bool(npc_state.get("prospect_record")),
                "is_prodigy": bool(npc_state.get("development", {}).get("prodigy")),
                "joined_month": npc_state.get("joined_month"),
                "fans": npc_state.get("fans", 0),
                "public_appeal": npc_state.get("public_appeal", "steady"),
                "npc": npc,
                "is_star": (
                    rating_key == "overall"
                    and npc_id
                    == career_leaderboard_star_id
                ),
                "is_player": False,
            }
        )

    player_rating = career_ratings.get(
        rating_key,
        career_rating
    )

    leaderboard.append(
        {
            "id": "player",
            "name": player_name,
            "rating": player_rating,
            "rating_key": rating_key,
            "rating_label": RATING_DISPLAY_NAMES.get(
                rating_key,
                "Global"
            ),
            "ratings": dict(career_ratings),
            "last_change": 0,
            "bio": profile_bio_text.strip() or "Current Career Mode player.",
            "country": profile_country_text.strip().upper()[:3],
            "age": profile_age_text.strip() or "Unknown",
            "birthday_month": None,
            "hometown": profile_hometown_text.strip() or "Unknown",
            "favorite_suit": profile_favorite_suit or "Unknown",
            "game_personality": "player",
            "fans": career_fans,
            "public_appeal": "player",
            "npc": None,
            "is_star": False,
            "is_player": True,
        }
    )

    leaderboard.sort(
        key=lambda item: item[
            "rating"
        ],
        reverse=True
    )

    for index, entry in enumerate(leaderboard):
        entry["is_star"] = rating_key == "overall" and index == 0
    return leaderboard


def get_player_leaderboard_rank(
        rating_key="overall"
):

    leaderboard = (
        get_career_leaderboard(
            rating_key=rating_key
        )
    )

    for index, entry in enumerate(
        leaderboard
    ):

        if entry.get(
            "is_player"
        ):
            return index + 1

    return None

def get_career_job_image(
        job_id,
        size
):
    job_data = (
        CAREER_JOBS.get(
            job_id
        )
    )

    if job_data is None:
        return None

    image_path = (
        job_data.get(
            "image"
        )
    )

    if not image_path:
        return None

    cache_key = (
        job_id,
        size
    )

    if (
        cache_key
        in career_job_image_cache
    ):
        return (
            career_job_image_cache[
                cache_key
            ]
        )

    try:
        image = pygame.image.load(
            image_path
        ).convert_alpha()

        image = (
            pygame.transform.smoothscale(
                image,
                size
            )
        )

        career_job_image_cache[
            cache_key
        ] = image

        return image

    except (
        pygame.error,
        FileNotFoundError
    ):
        return None

def get_career_web_image(
        filename,
        size=None
):
    cache_key = (
        filename,
        size
    )

    if (
        cache_key
        in career_web_image_cache
    ):
        return (
            career_web_image_cache[
                cache_key
            ]
        )

    path = (
        "assets/career/web/"
        + filename
    )

    try:
        image = pygame.image.load(
            path
        ).convert_alpha()

        if size is not None:
            image = (
                pygame.transform.smoothscale(
                    image,
                    size
                )
            )

        career_web_image_cache[
            cache_key
        ] = image

        return image

    except (
        pygame.error,
        FileNotFoundError
    ):
        return None

def draw_career_event_summary():

    # ==================================================
    # Background
    # ==================================================

    draw_submenu_background(
        overlay_alpha=145
    )

    # ==================================================
    # Main panel
    # ==================================================

    panel_rect = pygame.Rect(
        BASE_WIDTH // 2 - 330,
        125,
        660,
        460
    )

    panel_surface = pygame.Surface(
        (
            panel_rect.width,
            panel_rect.height
        ),
        pygame.SRCALPHA
    )

    panel_surface.fill(
        (
            15,
            25,
            20,
            235
        )
    )

    game_surface.blit(
        panel_surface,
        panel_rect.topleft
    )

    pygame.draw.rect(
        game_surface,
        (
            225,
            225,
            225
        ),
        panel_rect,
        3
    )

    # ==================================================
    # Title
    # ==================================================

    title_surface = (
        options_title_font.render(
            career_event_summary_title,
            True,
            (
                255,
                255,
                255
            )
        )
    )

    title_rect = (
        title_surface.get_rect(
            center=(
                BASE_WIDTH // 2,
                185
            )
        )
    )

    game_surface.blit(
        title_surface,
        title_rect
    )

    # ==================================================
    # Divider
    # ==================================================

    pygame.draw.line(
        game_surface,
        (
            180,
            180,
            180
        ),
        (
            panel_rect.x + 45,
            235
        ),
        (
            panel_rect.right - 45,
            235
        ),
        2
    )

    # ==================================================
    # Summary lines
    # ==================================================

    start_y = 280
    line_count = max(1, len(career_event_summary_lines))
    line_spacing = min(50, 260 // max(1, line_count - 1))

    for index, line_text in enumerate(
            career_event_summary_lines
    ):

        line_surface = (
            (pygame.font.Font(None, 28) if line_count > 7 else option_label_font).render(
                line_text,
                True,
                (
                    240,
                    240,
                    240
                )
            )
        )

        line_rect = (
            line_surface.get_rect(
                center=(
                    BASE_WIDTH // 2,
                    start_y
                    + index
                    * line_spacing
                )
            )
        )

        game_surface.blit(
            line_surface,
            line_rect
        )

    # ==================================================
    # Continue button
    # ==================================================

    draw_menu_button(
        career_event_summary_continue_rect,
        "Continue",
        game_mouse_pos,
        font=difficulty_detail_font
    )

def draw_career_browser_header(
        url_text
):
    browser_header = (
        get_career_web_image(
            "browser_header.png",
            (
                BASE_WIDTH,
                CAREER_BROWSER_HEADER_HEIGHT
            )
        )
    )

    if browser_header is not None:
        game_surface.blit(
            browser_header,
            (
                0,
                0
            )
        )

    url_surface = (
        option_value_font.render(
            url_text,
            True,
            (
                0,
                0,
                0
            )
        )
    )

    # Center the URL inside the
    # white address field.
    url_rect = (
        url_surface.get_rect(
            midleft=(
                365,
                32
            )
        )
    )

    game_surface.blit(
        url_surface,
        url_rect
    )

def get_career_residence_image(
        residence_id,
        size
):
    residence_data = (
        CAREER_RESIDENCES.get(
            residence_id
        )
    )

    if residence_data is None:
        return None

    image_path = (
        residence_data.get(
            "image"
        )
    )

    if not image_path:
        return None

    cache_key = (
        residence_id,
        size
    )

    if (
        cache_key
        in career_residence_image_cache
    ):
        return (
            career_residence_image_cache[
                cache_key
            ]
        )



    try:
        image = pygame.image.load(
            image_path
        ).convert_alpha()

        image = (
            pygame.transform.smoothscale(
                image,
                size
            )
        )

        career_residence_image_cache[
            cache_key
        ] = image

        return image


    except (

            pygame.error,

            FileNotFoundError

    ) as error:

        print(

            "Residence image failed:",

            image_path,

            error

        )

        return None

# ==================================================
# GENERIC UI DRAWING
# ==================================================

def draw_button(
    rect,
    text,
    selected=False,
    font=None
):
    if font is None:
        font = option_value_font

    if selected:
        fill_color = (
            80,
            145,
            100
        )

    else:
        fill_color = (
            50,
            110,
            75
        )

    pygame.draw.rect(
        game_surface,
        fill_color,
        rect
    )

    pygame.draw.rect(
        game_surface,
        (
            255,
            255,
            255
        ),
        rect,
        2
    )

    label = font.render(
        text,
        True,
        (
            255,
            255,
            255
        )
    )

    label_rect = label.get_rect(
        center=rect.center
    )

    game_surface.blit(
        label,
        label_rect
    )

def draw_menu_button(
        rect,
        text,
        mouse_pos,
        selected=False,
        font=None
):
    if font is None:
        font = menu_font

    hovered = False

    if mouse_pos is not None:
        hovered = rect.collidepoint(
            mouse_pos
        )

    if selected:
        image = button_selected

    elif hovered:
        image = button_hover

    else:
        image = button_normal

    scaled_image = pygame.transform.smoothscale(
        image,
        (
            rect.width,
            rect.height
        )
    )

    game_surface.blit(
        scaled_image,
        rect.topleft
    )

    label = font.render(
        text,
        True,
        (
            255,
            255,
            255
        )
    )

    label_rect = label.get_rect(
        center=rect.center
    )

    game_surface.blit(
        label,
        label_rect
    )

def get_hint_tooltip_text():

    if not game.hints_enabled:
        return "Hint (H): disabled"

    if game.hints_remaining is None:
        return "Hint (H): unlimited"

    if game.hints_remaining == 1:
        return "Hint (H): 1 remaining"

    return f"Hint (H): {game.hints_remaining} remaining"


def get_undo_tooltip_text():

    if game.challenge_id == "no_undo":
        return "Undo disabled"

    if game.undo_history_limit is None:
        return "Unlimited undo"

    if game.undo_history_limit == 0:
        return "Undo disabled"

    return (
        f"Last {game.undo_history_limit} moves"
    )

profile_avatar_frame_rect = pygame.Rect(
    65,
    170,
    300,
    360
)

def render_text_fit(
        text,
        font,
        max_width,
        color=(0, 0, 0),
        minimum_size=14
):
    surface = font.render(
        text,
        True,
        color
    )

    if (
        surface.get_width()
        <= max_width
    ):
        return surface

    current_size = (
        font.get_height()
    )

    while current_size > minimum_size:

        current_size -= 1

        smaller_font = pygame.font.Font(
            None,
            current_size
        )

        surface = smaller_font.render(
            text,
            True,
            color
        )

        if (
            surface.get_width()
            <= max_width
        ):
            return surface

    return surface

def draw_free_play_select():
    game_surface.blit(play_background_image, (0, 0))

    overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
    overlay.fill((8, 14, 18, 155))
    game_surface.blit(overlay, (0, 0))

    title = options_title_font.render(
        "FREE PLAY", True, (255, 255, 255)
    )
    game_surface.blit(
        title, title.get_rect(center=(BASE_WIDTH // 2, 78))
    )

    subtitle = difficulty_detail_font.render(
        "Choose any unlocked game. Free Play does not change Career cash, ratings, or fans.",
        True, (220, 225, 230)
    )
    game_surface.blit(
        subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 122))
    )

    for game_id in FREE_PLAY_GAME_IDS:
        rect = free_play_game_rects[game_id]
        unlocked = (game_id == "solitaire" or is_game_unlocked(game_id))
        hovered = (
            unlocked
            and game_mouse_pos is not None
            and rect.collidepoint(game_mouse_pos)
        )

        fill = (42, 105, 72) if hovered else (30, 72, 55)
        if not unlocked:
            fill = (55, 55, 58)

        pygame.draw.rect(game_surface, fill, rect, border_radius=10)
        pygame.draw.rect(
            game_surface,
            (255, 220, 105) if hovered else (235, 235, 235),
            rect, 4 if hovered else 2, border_radius=10
        )

        label = FREE_PLAY_GAME_NAMES.get(game_id, game_id)
        label_surface = option_label_font.render(
            label, True, (255, 255, 255)
        )
        game_surface.blit(
            label_surface,
            label_surface.get_rect(midleft=(rect.x + 22, rect.centery))
        )

        if not unlocked:
            required = get_game_unlock_level(game_id)
            lock_surface = difficulty_detail_font.render(
                f"Level {required}", True, (210, 210, 210)
            )
            game_surface.blit(
                lock_surface,
                lock_surface.get_rect(midright=(rect.right - 18, rect.centery))
            )

    draw_button(
        free_play_back_rect,
        "Back",
        font=option_label_font
    )


def draw_mode_select():
    # ==================================================
    # Background
    # ==================================================

    game_surface.blit(
        play_background_image,
        (
            0,
            0
        )
    )

    mouse_pos = game_mouse_pos

    if mouse_pos is None:
        mouse_pos = pygame.mouse.get_pos()

    # ==================================================
    # Hover feedback
    # ==================================================

    hover_surface = pygame.Surface(
        (
            BASE_WIDTH // 2,
            BASE_HEIGHT
        ),
        pygame.SRCALPHA
    )

    hover_surface.fill(
        (
            255,
            255,
            255,
            25
        )
    )

    if play_free_rect.collidepoint(
            mouse_pos
    ):
        game_surface.blit(
            hover_surface,
            (
                0,
                0
            )
        )

    elif play_career_rect.collidepoint(
            mouse_pos
    ):
        game_surface.blit(
            hover_surface,
            (
                BASE_WIDTH // 2,
                0
            )
        )

    # ==================================================
    # Return
    # ==================================================

    draw_menu_button(
        play_return_rect,
        "Return to Menu",
        game_mouse_pos,
        font=difficulty_detail_font
    )

career_play_rect = pygame.Rect(
    500,
    175,
    300,
    55
)

career_jobs_rect = pygame.Rect(
    740,
    703,
    390,
    26
)

career_real_estate_rect = pygame.Rect(
    335,
    703,
    390,
    26
)

career_leaderboards_rect = pygame.Rect(
    1175,
    285,
    180,
    45
)

career_news_rect = pygame.Rect(
    1175,
    645,
    180,
    45
)

career_back_rect = pygame.Rect(
    1175,
    710,
    180,
    45
)

def draw_submenu_title(
        text,
        y=55,
        width=360,
        height=72
):
    rect = pygame.Rect(
        BASE_WIDTH // 2 - width // 2,
        y - height // 2,
        width,
        height
    )

    # Wood plaque
    plaque = pygame.transform.smoothscale(
        button_normal,
        (
            rect.width,
            rect.height
        )
    )

    game_surface.blit(
        plaque,
        rect.topleft
    )

    # Dark text shadow
    shadow = options_title_font.render(
        text,
        True,
        (
            35,
            20,
            10
        )
    )

    shadow_rect = shadow.get_rect(
        center=(
            rect.centerx + 3,
            rect.centery + 3
        )
    )

    game_surface.blit(
        shadow,
        shadow_rect
    )

    # Main title
    label = options_title_font.render(
        text,
        True,
        (
            255,
            255,
            255
        )
    )

    label_rect = label.get_rect(
        center=rect.center
    )

    game_surface.blit(
        label,
        label_rect
    )

def draw_submenu_background(
        overlay_alpha=120
):
    game_surface.blit(
        menu_background_surfaces[
            selected_menu_background
        ],
        (
            0,
            0
        )
    )

    overlay = pygame.Surface(
        (
            BASE_WIDTH,
            BASE_HEIGHT
        ),
        pygame.SRCALPHA
    )

    overlay.fill(
        (
            0,
            0,
            0,
            overlay_alpha
        )
    )

    game_surface.blit(
        overlay,
        (
            0,
            0
        )
    )

def draw_how_to_play():

    global help_nav_max_scroll
    global help_content_max_scroll
    global help_nav_scroll
    global help_content_scroll

    draw_submenu_background(
        overlay_alpha=135
    )

    help_category_rects.clear()
    help_page_rects.clear()

    draw_submenu_title(
        "HELP",
        y=60,
        width=300
    )

    nav_panel = HELP_NAV_PANEL_RECT
    content_rect = HELP_CONTENT_RECT

    nav_surface = pygame.Surface(
        (nav_panel.width, nav_panel.height),
        pygame.SRCALPHA
    )
    nav_surface.fill((15, 35, 25, 220))
    game_surface.blit(nav_surface, nav_panel.topleft)
    pygame.draw.rect(game_surface, (255, 255, 255), nav_panel, 2)

    content_surface = pygame.Surface(
        (content_rect.width, content_rect.height),
        pygame.SRCALPHA
    )
    content_surface.fill((245, 245, 238, 250))
    game_surface.blit(content_surface, content_rect.topleft)
    pygame.draw.rect(game_surface, (255, 255, 255), content_rect, 2)

    # ==================================================
    # Scrollable navigation index
    # ==================================================

    old_clip = game_surface.get_clip()
    game_surface.set_clip(nav_panel.inflate(-2, -2))

    current_y = nav_panel.y + 20 - help_nav_scroll
    unscrolled_y = nav_panel.y + 20

    for category_id, category_data in HELP_NAVIGATION.items():
        category_rect = pygame.Rect(
            nav_panel.x + 15,
            current_y,
            nav_panel.width - 30,
            46
        )

        if category_rect.bottom >= nav_panel.top and category_rect.top <= nav_panel.bottom:
            help_category_rects[category_id] = category_rect

            expanded = help_expanded_categories.get(category_id, False)
            arrow = "-" if expanded else "+"
            draw_menu_button(
                category_rect,
                f"{arrow}  {category_data['name']}",
                game_mouse_pos,
                font=difficulty_detail_font
            )

        expanded = help_expanded_categories.get(category_id, False)
        current_y += 52
        unscrolled_y += 52

        if expanded:
            for page_id, page_name in category_data["pages"]:
                page_rect = pygame.Rect(
                    nav_panel.x + 35,
                    current_y,
                    nav_panel.width - 55,
                    38
                )

                if page_rect.bottom >= nav_panel.top and page_rect.top <= nav_panel.bottom:
                    help_page_rects[page_id] = page_rect
                    draw_menu_button(
                        page_rect,
                        page_name,
                        game_mouse_pos,
                        selected=(help_current_page == page_id),
                        font=difficulty_detail_font
                    )

                current_y += 42
                unscrolled_y += 42

        current_y += 6
        unscrolled_y += 6

    game_surface.set_clip(old_clip)

    help_nav_max_scroll = max(
        0,
        unscrolled_y - (nav_panel.bottom - 12)
    )
    help_nav_scroll = max(0, min(help_nav_scroll, help_nav_max_scroll))

    if help_nav_max_scroll > 0:
        track = pygame.Rect(nav_panel.right - 9, nav_panel.y + 8, 4, nav_panel.height - 16)
        pygame.draw.rect(game_surface, (70, 92, 80), track, border_radius=2)
        ratio = nav_panel.height / max(nav_panel.height, nav_panel.height + help_nav_max_scroll)
        thumb_h = max(36, int(track.height * ratio))
        travel = max(1, track.height - thumb_h)
        position = 0 if help_nav_max_scroll <= 0 else int(
            travel * min(1.0, help_nav_scroll / help_nav_max_scroll)
        )
        thumb = pygame.Rect(track.x, track.y + position, track.width, thumb_h)
        pygame.draw.rect(game_surface, (220, 224, 218), thumb, border_radius=2)

    # ==================================================
    # Content page
    # ==================================================

    content = HELP_CONTENT.get(
        help_current_page,
        HELP_CONTENT["solitaire_basics"]
    )

    section_title = option_label_font.render(
        content["title"],
        True,
        (20, 20, 20)
    )
    game_surface.blit(
        section_title,
        (content_rect.x + 35, content_rect.y + 30)
    )

    history_image = None
    image_path = content.get("image")
    if image_path:
        if image_path not in help_history_image_cache:
            try:
                help_history_image_cache[image_path] = pygame.image.load(
                    image_path
                ).convert_alpha()
            except (pygame.error, FileNotFoundError):
                help_history_image_cache[image_path] = None
        history_image = help_history_image_cache.get(image_path)

    if help_current_page == "solitaire_basics":
        text_rect = pygame.Rect(
            content_rect.x + 35,
            content_rect.y + 90,
            455,
            content_rect.height - 125
        )
    elif history_image is not None:
        text_rect = pygame.Rect(
            content_rect.x + 35,
            content_rect.y + 90,
            505,
            content_rect.height - 125
        )
    else:
        text_rect = pygame.Rect(
            content_rect.x + 35,
            content_rect.y + 90,
            content_rect.width - 70,
            content_rect.height - 125
        )

    # Wrap first so we know the scrollable content height.
    wrapped_entries = []
    logical_height = 0

    for line in content.get("lines", []):
        if not line:
            wrapped_entries.append(("", True))
            logical_height += 14
            continue

        words = str(line).split()
        wrapped_lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            test_surface = difficulty_detail_font.render(
                test_line,
                True,
                (20, 20, 20)
            )
            if test_surface.get_width() <= text_rect.width:
                current_line = test_line
            else:
                if current_line:
                    wrapped_lines.append(current_line)
                current_line = word

        if current_line:
            wrapped_lines.append(current_line)

        for wrapped_line in wrapped_lines:
            wrapped_entries.append((wrapped_line, False))
            logical_height += 26
        logical_height += 10

    help_content_max_scroll = max(
        0,
        logical_height - text_rect.height
    )
    help_content_scroll = max(
        0,
        min(help_content_scroll, help_content_max_scroll)
    )

    text_clip = text_rect.copy()
    old_clip = game_surface.get_clip()
    game_surface.set_clip(text_clip)

    current_y = text_rect.y - help_content_scroll
    for line, blank in wrapped_entries:
        if blank:
            current_y += 14
            continue

        if current_y + 24 >= text_rect.top and current_y <= text_rect.bottom:
            line_surface = difficulty_detail_font.render(
                line,
                True,
                (20, 20, 20)
            )
            game_surface.blit(line_surface, (text_rect.x, current_y))
        current_y += 26

        # Paragraph spacing is represented by the 10 pixels added to the
        # logical height after the final wrapped line. Apply it whenever the
        # next entry is blank or this line closes a source paragraph.
        # A small uniform gap keeps histories readable without special markup.
        current_y += 2

    game_surface.set_clip(old_clip)

    if help_content_max_scroll > 0:
        track = pygame.Rect(text_rect.right - 5, text_rect.y, 3, text_rect.height)
        pygame.draw.rect(game_surface, (195, 198, 192), track)
        ratio = text_rect.height / max(text_rect.height, logical_height)
        thumb_h = max(30, int(track.height * ratio))
        travel = max(1, track.height - thumb_h)
        position = int(
            travel * min(1.0, help_content_scroll / help_content_max_scroll)
        )
        pygame.draw.rect(
            game_surface,
            (80, 88, 83),
            pygame.Rect(track.x, track.y + position, track.width, thumb_h)
        )

    if history_image is not None:
        image_panel = pygame.Rect(
            content_rect.right - 400,
            content_rect.y + 104,
            350,
            350
        )
        pygame.draw.rect(
            game_surface,
            (225, 225, 218),
            image_panel,
            border_radius=8
        )
        pygame.draw.rect(
            game_surface,
            (90, 90, 86),
            image_panel,
            2,
            border_radius=8
        )

        source_w, source_h = history_image.get_size()
        scale = min(
            (image_panel.width - 18) / max(1, source_w),
            (image_panel.height - 18) / max(1, source_h)
        )
        image_size = (
            max(1, int(source_w * scale)),
            max(1, int(source_h * scale))
        )
        scaled = pygame.transform.smoothscale(history_image, image_size)
        game_surface.blit(scaled, scaled.get_rect(center=image_panel.center))

        caption = str(content.get("caption", "") or "").strip()
        if caption:
            caption_rect = pygame.Rect(
                image_panel.x,
                image_panel.bottom + 12,
                image_panel.width,
                72
            )
            words = caption.split()
            line = ""
            lines = []
            for word in words:
                test = f"{line} {word}".strip()
                if difficulty_detail_font.size(test)[0] <= caption_rect.width:
                    line = test
                else:
                    if line:
                        lines.append(line)
                    line = word
            if line:
                lines.append(line)
            for index, caption_line in enumerate(lines[:3]):
                surf = difficulty_detail_font.render(
                    caption_line,
                    True,
                    (70, 70, 68)
                )
                game_surface.blit(
                    surf,
                    surf.get_rect(
                        center=(caption_rect.centerx, caption_rect.y + 12 + index * 20)
                    )
                )

    if help_current_page == "solitaire_basics":
        draw_solitaire_help_diagram(content_rect)

    draw_menu_button(
        how_to_play_back_rect,
        "Return",
        game_mouse_pos,
        font=difficulty_detail_font
    )


def draw_career_hub():

    # ==================================================
    # SHARED PAGE GEOMETRY
    # ==================================================

    center_x = 320
    center_width = 846

    calendar_rect = pygame.Rect(
        center_x,
        144,
        center_width,
        555
    )
    # ==================================================
    # PAGE BACKGROUND
    # ==================================================

    game_surface.fill(
        (
            245,
            245,
            245
        )
    )

    # ==================================================
    # Career Website Banner
    # ==================================================

    career_header = (
        get_career_hub_image(
            "career_header.png",
            (
                848,
                56
            )
        )
    )

    if career_header is not None:
        game_surface.blit(
            career_header,
            (
                320,
                0
            )
        )

    career_url_surface = (
        option_value_font.render(
            "https://www.mysolitairecareer.weebly.biz",
            True,
            (
                0,
                0,
                0
            )
        )
    )

    game_surface.blit(
        career_url_surface,
        (
            625,
            20
        )
    )


    # ==================================================
    # LEFT COLUMN
    # ==================================================

    left_column_rect = pygame.Rect(
        0,
        0,
        320,
        768
    )

    pygame.draw.rect(
        game_surface,
        (
            250,
            250,
            250
        ),
        left_column_rect
    )

    pygame.draw.rect(
        game_surface,
        (
            0,
            0,
            0
        ),
        left_column_rect,
        3
    )

    counter_image = get_career_hub_image(
        "visitor_counter.png",
        (
            140,
            32
        )
    )

    if counter_image is not None:
        game_surface.blit(
            counter_image,
            (
                18,
                742
            )
        )

    best_viewed_image = get_career_hub_image(
        "best_viewed_1080p.png",
        (
            120,
            31
        )
    )

    award_image = get_career_hub_image(
        "web_award.png",
        (
            88,
            31
        )
    )

    if best_viewed_image is not None:
        game_surface.blit(
            best_viewed_image,
            (
                center_x + 15,
                105
            )
        )

    if award_image is not None:
        game_surface.blit(
            award_image,
            (
                center_x + 145,
                105
            )
        )

    # Avatar panel

    avatar_panel_rect = pygame.Rect(
        18,
        18,
        285,
        235
    )

    pygame.draw.rect(
        game_surface,
        (
            210,
            210,
            210
        ),
        avatar_panel_rect
    )

    pygame.draw.rect(
        game_surface,
        (
            0,
            0,
            0
        ),
        avatar_panel_rect,
        2
    )

    avatar = get_profile_avatar()

    avatar_preview = pygame.transform.smoothscale(
        avatar,
        (
            190,
            228
        )
    )

    avatar_preview_rect = avatar_preview.get_rect(
        center=avatar_panel_rect.center
    )

    game_surface.blit(
        avatar_preview,
        avatar_preview_rect
    )

    # Name

    name_surface = option_label_font.render(
        player_name,
        True,
        (
            0,
            0,
            0
        )
    )

    name_rect = name_surface.get_rect(
        center=(
            160,
            272
        )
    )

    game_surface.blit(
        name_surface,
        name_rect
    )

    # Level / XP

    level_surface = option_value_font.render(
        f"Level: {player_level}",
        True,
        (
            0,
            0,
            0
        )
    )

    game_surface.blit(
        level_surface,
        (
            18,
            300
        )
    )

    if player_xp_to_next is not None:
        xp_text = (
            f"XP: {player_xp:,} / "
            f"{player_xp_to_next:,}"
        )
    else:
        xp_text = (
            f"XP: {player_xp:,} / MAX"
        )

    xp_surface = option_value_font.render(
        xp_text,
        True,
        (
            0,
            0,
            0
        )
    )

    game_surface.blit(
        xp_surface,
        (
            18,
            330
        )
    )

    # Career progress panel

    career_panel_rect = pygame.Rect(
        0,
        365,
        320,
        250
    )

    pygame.draw.rect(
        game_surface,
        (
            255,
            255,
            255
        ),
        career_panel_rect
    )

    pygame.draw.rect(
        game_surface,
        (
            220,
            0,
            0
        ),
        career_panel_rect,
        5
    )

    career_heading = option_label_font.render(
        "CAREER PROGRESS",
        True,
        (
            0,
            0,
            0
        )
    )

    career_heading_rect = career_heading.get_rect(
        center=(
            career_panel_rect.centerx,
            career_panel_rect.y + 28
        )
    )

    game_surface.blit(
        career_heading,
        career_heading_rect
    )

    career_lines = [
        f"Global Rating: {career_rating:,}",
        f"Global Rank: #{get_player_leaderboard_rank()}",
        f"Cash: ${career_cash:,}",
        f"Career Day: {career_day:,}",
        f"Residence: {get_career_residence_name()}",
        f"Fans: {career_fans:,}",
        f"Side Job: {get_career_job_name()}",
    ]

    career_stat_icons = {
        0: "icon_rating.png",
        1: "icon_leaderboard.png",
        2: "icon_cash.png",
        3: "icon_day.png",
        4: "icon_residence.png",
        5: "icon_fans.png",
        6: "icon_job.png",
    }

    for index, line_text in enumerate(
            career_lines
    ):

        line_y = (
                career_panel_rect.y
                + 58
                + index * 25
        )

        icon_filename = (
            career_stat_icons.get(
                index
            )
        )

        text_x = (
                career_panel_rect.x + 18
        )

        if icon_filename:

            icon = (
                get_career_hub_image(
                    icon_filename,
                    (
                        24,
                        24
                    )
                )
            )

            if icon is not None:
                game_surface.blit(
                    icon,
                    (
                        career_panel_rect.x + 10,
                        line_y - 2
                    )
                )

                text_x = (
                        career_panel_rect.x + 40
                )

        line_surface = (
            difficulty_detail_font.render(
                line_text,
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        game_surface.blit(
            line_surface,
            (
                text_x,
                line_y
            )
        )

    # Statistics panel

    stats_panel_rect = pygame.Rect(
        0,
        615,
        320,
        153
    )

    pygame.draw.rect(
        game_surface,
        (
            255,
            255,
            255
        ),
        stats_panel_rect
    )

    pygame.draw.rect(
        game_surface,
        (
            20,
            60,
            220
        ),
        stats_panel_rect,
        5
    )

    stats_heading = option_label_font.render(
        "STATISTICS",
        True,
        (
            0,
            0,
            0
        )
    )

    stats_heading_rect = stats_heading.get_rect(
        center=(
            stats_panel_rect.centerx,
            stats_panel_rect.y + 25
        )
    )

    game_surface.blit(
        stats_heading,
        stats_heading_rect
    )

    stats_lines = [
        f"Rounds Won: {career_rounds_won:,}",
        f"Challenges Won: {career_challenges_won:,}",
        f"Total Moves: {career_total_moves:,}",
    ]

    for index, text in enumerate(
        stats_lines
    ):
        line = option_value_font.render(
            text,
            True,
            (
                0,
                0,
                0
            )
        )

        game_surface.blit(
            line,
            (
                18,
                stats_panel_rect.y
                + 52
                + index * 26
            )
        )


    # ==================================================
    # CENTER CALENDAR AREA
    # ==================================================

    date_header_rect = pygame.Rect(
        center_x,
        64,
        center_width,
        80
    )

    pygame.draw.rect(
        game_surface,
        (
            250,
            250,
            250
        ),
        date_header_rect
    )

    date_title = pygame.font.SysFont(
        None,
        58
    ).render(
        f"{get_career_month_name()} {career_year}",
        True,
        (
            0,
            0,
            0
        )
    )

    date_title_rect = date_title.get_rect(
        center=(date_header_rect.centerx, 91)
    )

    game_surface.blit(
        date_title,
        date_title_rect
    )

    calendar_half_text = (
        "Days 1-15"
        if career_day_of_month <= 15
        else "Days 16-30"
    )
    calendar_status_surface = difficulty_detail_font.render(
        f"{calendar_half_text}   |   Last updated: Career Day {career_day}",
        True,
        (80, 80, 80)
    )
    game_surface.blit(
        calendar_status_surface,
        calendar_status_surface.get_rect(
            center=(date_header_rect.centerx, 129)
        )
    )


    pygame.draw.rect(
        game_surface,
        (
            252,
            252,
            252
        ),
        calendar_rect
    )

    pygame.draw.rect(
        game_surface,
        (
            0,
            0,
            0
        ),
        calendar_rect,
        2
    )

    badge_image = get_career_hub_image(
        "career_central_badge.png",
        (
            140,
            36
        )
    )

    if badge_image is not None:
        game_surface.blit(
            badge_image,
            (
                center_x + 8,
                101
            )
        )

    # ==================================================
    # CAREER CALENDAR GRID
    # ==================================================

    global career_calendar_action_rect
    global career_calendar_skip_rect

    ensure_career_schedule()
    ensure_career_leaderboard()
    ensure_career_news()

    columns = 5
    rows = 3

    cell_width = (
            calendar_rect.width
            // columns
    )

    cell_height = (
            calendar_rect.height
            // rows
    )

    calendar_page_start = 0 if career_day_of_month <= 15 else 15
    calendar_page_entries = career_current_schedule[
        calendar_page_start:calendar_page_start + 15
    ]

    career_hub_controls.begin_calendar(
        career_current_schedule,
        career_day_of_month
    )

    # Reset these every frame.
    career_calendar_action_rect = pygame.Rect(
        0,
        0,
        0,
        0
    )

    career_calendar_skip_rect = pygame.Rect(
        0,
        0,
        0,
        0
    )

    for schedule_index, entry in enumerate(
            calendar_page_entries
    ):

        row = (
                schedule_index
                // columns
        )

        column = (
                schedule_index
                % columns
        )

        cell_rect = pygame.Rect(
            calendar_rect.x
            + column * cell_width,

            calendar_rect.y
            + row * cell_height,

            cell_width,
            cell_height
        )

        # ==================================================
        # Determine state of day
        # ==================================================

        is_current_day = (
                entry[
                    "day_number"
                ]
                == career_day_of_month
        )

        is_past_day = (
                entry[
                    "day_number"
                ]
                < career_day_of_month
        )

        # ==================================================
        # Cell background
        # ==================================================

        if is_current_day:
            cell_fill = (
                255,
                248,
                220
            )

        elif is_past_day:
            cell_fill = (
                225,
                225,
                225
            )

        else:
            cell_fill = (
                250,
                250,
                250
            )

        pygame.draw.rect(
            game_surface,
            cell_fill,
            cell_rect
        )

        career_hub_controls.register_day(entry["day_number"], cell_rect)
        if career_hub_controls.selected_day == entry["day_number"]:
            cell_fill = (220, 238, 255)
            pygame.draw.rect(game_surface, cell_fill, cell_rect)

        # Current day gets a red outline like
        # your Photoshop mock-up.
        border_color = (
            (220, 0, 0)
            if is_current_day
            else (35, 110, 190)
            if career_hub_controls.selected_day == entry["day_number"]
            else (0, 0, 0)
        )

        border_width = (
            4
            if is_current_day
            else 2
        )

        pygame.draw.rect(
            game_surface,
            border_color,
            cell_rect,
            border_width
        )

        # ==================================================
        # Header
        # ==================================================

        weekday_name = (
            CAREER_WEEKDAY_NAMES[
                entry[
                    "weekday_index"
                ]
            ]
        )

        weekday_surface = (
            difficulty_detail_font.render(
                weekday_name,
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        game_surface.blit(
            weekday_surface,
            (
                cell_rect.x + 8,
                cell_rect.y + 6
            )
        )

        day_surface = (
            option_label_font.render(
                str(
                    entry[
                        "day_number"
                    ]
                ),
                True,
                (
                    220,
                    0,
                    40
                )
            )
        )

        day_rect = (
            day_surface.get_rect(
                top=cell_rect.y + 2,
                right=cell_rect.right - 8
            )
        )

        game_surface.blit(
            day_surface,
            day_rect
        )

        # Header divider
        pygame.draw.line(
            game_surface,
            (
                0,
                0,
                0
            ),
            (
                cell_rect.x,
                cell_rect.y + 34
            ),
            (
                cell_rect.right,
                cell_rect.y + 34
            ),
            2
        )

        # Future days get a one-click fast-forward shortcut. The whole square
        # still supports the existing select + toolbar flow.
        if not is_current_day and not is_past_day:
            fast_skip_rect = pygame.Rect(
                cell_rect.right - 34,
                cell_rect.bottom - 30,
                24,
                20
            )
            career_hub_controls.register_fast_skip(
                entry["day_number"],
                fast_skip_rect
            )

            hovered_fast = (
                game_mouse_pos is not None
                and fast_skip_rect.collidepoint(game_mouse_pos)
            )
            pygame.draw.rect(
                game_surface,
                (210, 228, 246) if hovered_fast else (232, 239, 246),
                fast_skip_rect,
                border_radius=4
            )
            pygame.draw.rect(
                game_surface,
                (35, 90, 150),
                fast_skip_rect,
                1,
                border_radius=4
            )

            triangle_y = fast_skip_rect.centery
            for triangle_x in (fast_skip_rect.x + 6, fast_skip_rect.x + 12):
                pygame.draw.polygon(
                    game_surface,
                    (35, 90, 150),
                    [
                        (triangle_x, triangle_y - 5),
                        (triangle_x, triangle_y + 5),
                        (triangle_x + 6, triangle_y),
                    ]
                )

        # ==================================================
        # Past days
        # ==================================================

        if is_past_day:

            history_entry = None

            for history_item in (
                    career_completed_days
            ):
                if (
                        history_item.get(
                            "year"
                        )
                        == career_year
                        and history_item.get(
                    "month"
                )
                        == career_month
                        and history_item.get(
                    "day"
                )
                        == entry[
                    "day_number"
                ]
                ):
                    history_entry = (
                        history_item
                    )

                    break

            if (
                    history_entry is not None
                    and not history_entry.get(
                "completed",
                True
            )
            ):
                status_text = "Skipped"

            else:
                status_text = "Completed"

            completed_surface = (
                difficulty_detail_font.render(
                    status_text,
                    True,
                    (
                        100,
                        100,
                        100
                    )
                )
            )

            completed_rect = (
                completed_surface.get_rect(
                    center=(
                        cell_rect.centerx,
                        cell_rect.centery
                    )
                )
            )

            game_surface.blit(
                completed_surface,
                completed_rect
            )

            continue

        # ==================================================
        # Activity title
        # ==================================================

        activity_type = entry[
            "activity_type"
        ]

        activity_title = entry.get(
            "title",
            ""
        )

        activity_icon_map = {
            CAREER_ACTIVITY_ROUND:
                "icon_round.png",

            CAREER_ACTIVITY_WORK:
                "icon_work.png",

            CAREER_ACTIVITY_CHALLENGE:
                "icon_challenge.png",

            CAREER_ACTIVITY_EVENT:
                "icon_event.png",

        }

        activity_icon_name = (
            activity_icon_map.get(
                activity_type
            )
        )

        if activity_icon_name:

            activity_icon = (
                get_career_hub_image(
                    activity_icon_name,
                    (
                        26,
                        26
                    )
                )
            )

            if activity_icon is not None:
                game_surface.blit(
                    activity_icon,
                    (
                        cell_rect.x + 10,
                        cell_rect.y + 38
                    )
                )


        # ----------------------------------------------
        # Challenge
        # ----------------------------------------------

        if (
                activity_type
                == CAREER_ACTIVITY_CHALLENGE
        ):
            line_1 = "Challenge Round:"

            line_2 = entry.get(
                "challenge_name",
                ""
            )

            title_surface = (
                difficulty_detail_font.render(
                    line_1,
                    True,
                    (
                        0,
                        0,
                        0
                    )
                )
            )

            title_rect = (
                title_surface.get_rect(
                    center=(
                        cell_rect.centerx,
                        cell_rect.y + 52
                    )
                )
            )

            game_surface.blit(
                title_surface,
                title_rect
            )

            challenge_surface = (
                option_label_font.render(
                    line_2,
                    True,
                    (
                        0,
                        0,
                        0
                    )
                )
            )

            challenge_rect = (
                challenge_surface.get_rect(
                    center=(
                        cell_rect.centerx,
                        cell_rect.y + 78
                    )
                )
            )

            game_surface.blit(
                challenge_surface,
                challenge_rect
            )

        # ----------------------------------------------
        # Everything else
        # ----------------------------------------------

        else:
            words = activity_title.split()
            if activity_title == "Head-to-Head":
                words = ["Head-to-", "Head"]
            title_lines = ["Head-to-", "Head"] if activity_title == "Head-to-Head" else [activity_title]

            if option_label_font.size(activity_title)[0] > cell_rect.width - 18 and len(words) > 1:
                best_split = 1
                best_width = 10 ** 9
                for split_index in range(1, len(words)):
                    line_a = " ".join(words[:split_index])
                    line_b = " ".join(words[split_index:])
                    candidate_width = max(
                        option_label_font.size(line_a)[0],
                        option_label_font.size(line_b)[0]
                    )
                    if candidate_width < best_width:
                        best_width = candidate_width
                        best_split = split_index
                title_lines = [
                    " ".join(words[:best_split]),
                    " ".join(words[best_split:]),
                ]

            base_y = cell_rect.y + (70 if len(title_lines) == 2 else 82)
            for line_index, title_line in enumerate(title_lines):
                activity_surface = render_text_fit(
                    title_line,
                    option_label_font,
                    cell_rect.width - 18,
                    (0, 0, 0),
                    minimum_size=18
                )
                activity_rect = activity_surface.get_rect(
                    center=(
                        cell_rect.centerx,
                        base_y + line_index * 24
                    )
                )
                game_surface.blit(activity_surface, activity_rect)

        # ==================================================
        # Only current day has buttons
        # ==================================================

        if is_current_day:

            career_calendar_action_rect = (
                pygame.Rect(
                    cell_rect.x + 12,
                    cell_rect.bottom - 78,
                    cell_rect.width - 24,
                    34
                )
            )

            career_calendar_skip_rect = (
                pygame.Rect(
                    cell_rect.x + 12,
                    cell_rect.bottom - 38,
                    cell_rect.width - 24,
                    28
                )
            )

            # ----------------------------------------------
            # Action button label
            # ----------------------------------------------

            if (
                    activity_type
                    == CAREER_ACTIVITY_ROUND
            ):
                action_text = "Play Solitaire"

            elif (
                    activity_type
                    == CAREER_ACTIVITY_WORK
            ):
                action_text = "Go to Work"

            elif (
                    activity_type
                    == CAREER_ACTIVITY_CHALLENGE
            ):
                action_text = "Play Challenge"


            elif (
                    activity_type
                    == CAREER_ACTIVITY_EVENT

            ):
                action_text = "View Event"


            elif activity_type in (

                    CAREER_ACTIVITY_CASUAL_CARDS,
                    CAREER_ACTIVITY_POKER_NIGHT,
                    CAREER_ACTIVITY_CASINO_NIGHT,
                    CAREER_ACTIVITY_NICHE_NIGHT,
                    CAREER_ACTIVITY_ARCADE_NIGHT

            ):

                action_text = "Play"


            else:
                action_text = "Continue"

            draw_button(
                career_calendar_action_rect,
                action_text,
                font=difficulty_detail_font
            )

            draw_button(
                career_calendar_skip_rect,
                "Skip Day",
                font=difficulty_detail_font
            )

    # ==================================================
    # RIGHT COLUMN
    # ==================================================

    right_x = 1166
    right_width = 200

    leaderboard_rect = pygame.Rect(
        right_x,
        0,
        right_width,
        410
    )

    pygame.draw.rect(
        game_surface,
        (
            250,
            250,
            250
        ),
        leaderboard_rect
    )

    pygame.draw.rect(
        game_surface,
        (
            0,
            0,
            0
        ),
        leaderboard_rect,
        3
    )

    top10_header = (
        get_career_hub_image(
            "top10_header.png",
            (
                180,
                38
            )
        )
    )

    if top10_header is not None:

        top10_header_rect = (
            top10_header.get_rect(
                center=(
                    leaderboard_rect.centerx,
                    leaderboard_rect.y + 24
                )
            )
        )

        game_surface.blit(
            top10_header,
            top10_header_rect
        )

    else:

        fallback_surface = (
            option_label_font.render(
                "TOP 10",
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        fallback_rect = (
            fallback_surface.get_rect(
                center=(
                    leaderboard_rect.centerx,
                    leaderboard_rect.y + 24
                )
            )
        )

        game_surface.blit(
            fallback_surface,
            fallback_rect
        )

    leaderboard_preview = (
        get_career_leaderboard()[
            :10
        ]
    )

    for index, entry in enumerate(
            leaderboard_preview
    ):
        text = (
            f"{index + 1}. "
            f"{entry['name']}"
        )

        line = (
            difficulty_detail_font.render(
                text,
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        game_surface.blit(
            line,
            (
                right_x + 10,
                52 + index * 23
            )
        )

    draw_button(
        career_leaderboards_rect,
        "View Leaderboards"
    )

    news_rect = pygame.Rect(
        right_x,
        350,
        right_width,
        350
    )

    pygame.draw.rect(
        game_surface,
        (
            245,
            241,
            222
        ),
        news_rect
    )

    pygame.draw.rect(
        game_surface,
        (
            0,
            0,
            0
        ),
        news_rect,
        3
    )

    courrier_preview = (
        get_career_hub_image(
            "courrier_preview.png",
            (
                185,
                40
            )
        )
    )

    if courrier_preview is not None:

        courrier_preview_rect = (
            courrier_preview.get_rect(
                center=(
                    news_rect.centerx,
                    news_rect.y + 28
                )
            )
        )

        game_surface.blit(
            courrier_preview,
            courrier_preview_rect
        )

    else:

        fallback_title = (
            option_label_font.render(
                "THE CARDED COURRIER",
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        fallback_rect = (
            fallback_title.get_rect(
                center=(
                    news_rect.centerx,
                    news_rect.y + 28
                )
            )
        )

        game_surface.blit(
            fallback_title,
            fallback_rect
        )

    pygame.draw.line(
        game_surface,
        (
            0,
            0,
            0
        ),
        (
            news_rect.x + 12,
            news_rect.y + 52
        ),
        (
            news_rect.right - 12,
            news_rect.y + 52
        ),
        2
    )

    # ==================================================
    # Newspaper Preview
    # ==================================================

    news_preview = (
        get_career_news_preview(
            1
        )
    )

    preview_y = (
            news_rect.y + 68
    )

    for item in news_preview:
        # ----------------------------------------------
        # Headline
        # ----------------------------------------------

        headline = (
            item.get(
                "headline",
                "UNTITLED STORY"
            )
        )

        headline_rect = pygame.Rect(
            news_rect.x + 12,
            preview_y,
            news_rect.width - 24,
            70
        )

        draw_wrapped_text(
            headline,
            difficulty_detail_font,
            (
                0,
                0,
                0
            ),
            headline_rect,
            line_spacing=3
        )

        preview_y += 72

        # ----------------------------------------------
        # Date
        # ----------------------------------------------

        date_surface = (
            difficulty_detail_font.render(
                get_career_news_date(
                    item
                ),
                True,
                (
                    100,
                    100,
                    100
                )
            )
        )

        game_surface.blit(
            date_surface,
            (
                news_rect.x + 12,
                preview_y
            )
        )

        preview_y += 34

        # ----------------------------------------------
        # Body preview
        # ----------------------------------------------

        body_preview = (
            item.get(
                "body",
                ""
            )
        )

        draw_wrapped_text_limited(
            body_preview,
            ui_small_font,
            (
                40,
                40,
                40
            ),
            pygame.Rect(
                news_rect.x + 12,
                preview_y,
                news_rect.width - 24,
                100
            ),
            max_lines=4,
            line_spacing=2
        )

    draw_button(
        career_news_rect,
        "View Newspaper"
    )

    draw_wrapped_text_limited(
        body_preview,
        ui_small_font,
        (
            40,
            40,
            40
        ),
        pygame.Rect(
            news_rect.x + 12,
            preview_y,
            news_rect.width - 24,
            100
        ),
        max_lines=4,
        line_spacing=2
    )

    # ==================================================
    # BOTTOM WEBSITE LINKS
    # ==================================================

    bottom_bar_rect = pygame.Rect(
        center_x,
        699,
        center_width,
        69
    )

    pygame.draw.rect(
        game_surface,
        (
            220,
            230,
            240
        ),
        bottom_bar_rect
    )

    pygame.draw.rect(
        game_surface,
        (
            0,
            0,
            0
        ),
        bottom_bar_rect,
        2
    )

    draw_button(
        career_real_estate_rect,
        "Visit RealEstate.apt",
        font=difficulty_detail_font
    )

    draw_button(
        career_jobs_rect,
        "Visit JimbosJobFinder.sk",
        font=difficulty_detail_font
    )

    career_hub_controls.draw_time_warp(game_surface,date_header_rect,draw_button,career_hub_controls.font)

    career_hub_controls.draw_toolbar(
        game_surface, draw_button, career_hub_controls.font, pygame.time.get_ticks()
    )

    draw_button(
        career_back_rect,
        "Exit Career"
    )

    # ==================================================
    # FAST-SKIP CONFIRMATION
    # ==================================================

    if career_hub_controls.confirm_skip_day is not None:
        confirm_day = career_hub_controls.confirm_skip_day
        confirm_entry = get_career_day_entry(confirm_day)
        if confirm_entry is not None:
            weekday = CAREER_WEEKDAY_NAMES[
                confirm_entry.get("weekday_index", 0)
            ]
            day_label = get_ordinal_day(confirm_day)
        else:
            weekday = "that day"
            day_label = str(confirm_day)

        overlay = pygame.Surface(
            (BASE_WIDTH, BASE_HEIGHT),
            pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 118))
        game_surface.blit(overlay, (0, 0))

        confirm_rect = pygame.Rect(390, 300, 586, 230)
        pygame.draw.rect(
            game_surface,
            (248, 248, 244),
            confirm_rect,
            border_radius=12
        )
        pygame.draw.rect(
            game_surface,
            (35, 90, 150),
            confirm_rect,
            3,
            border_radius=12
        )

        confirm_title = option_label_font.render(
            f"Skip ahead to {weekday} the {day_label}?",
            True,
            (20, 30, 38)
        )
        game_surface.blit(
            confirm_title,
            confirm_title.get_rect(center=(confirm_rect.centerx, 345))
        )

        confirm_detail = difficulty_detail_font.render(
            "All earlier days will be marked skipped and grant no rewards.",
            True,
            (70, 78, 84)
        )
        game_surface.blit(
            confirm_detail,
            confirm_detail.get_rect(center=(confirm_rect.centerx, 390))
        )

        draw_button(
            career_fast_skip_yes_rect,
            "Yes, Skip Ahead",
            font=difficulty_detail_font
        )
        draw_button(
            career_fast_skip_no_rect,
            "Cancel",
            font=difficulty_detail_font
        )

def draw_career_placeholder_page(
        title_text,
        subtitle_text
):
    game_surface.fill(
        (
            205,
            245,
            230
        )
    )

    title = options_title_font.render(
        title_text,
        True,
        (
            20,
            20,
            20
        )
    )

    title_rect = title.get_rect(
        center=(
            BASE_WIDTH // 2,
            120
        )
    )

    game_surface.blit(
        title,
        title_rect
    )

    subtitle = option_label_font.render(
        subtitle_text,
        True,
        (
            60,
            60,
            60
        )
    )

    subtitle_rect = subtitle.get_rect(
        center=(
            BASE_WIDTH // 2,
            230
        )
    )

    game_surface.blit(
        subtitle,
        subtitle_rect
    )

    draw_button(
        career_subpage_back_rect,
        "Return to Career"
    )

def draw_career_jobs():
    game_surface.fill(
        (
            235,
            235,
            225
        )
    )

    background_image = get_jobfinder_image(
        "jobfinder_background.png",
        (
            BASE_WIDTH,
            BASE_HEIGHT
        )
    )

    if background_image is not None:
        game_surface.blit(
            background_image,
            (
                0,
                0
            )
        )

    # ==================================================
    # Browser
    # ==================================================

    draw_career_browser_header(
        "https://www.jimbosjobfinder.sk"
    )

    # ==================================================
    # Page Title
    # ==================================================

    title = menu_title_font.render(
        "JIMBO'S JOB FINDER",
        True,
        (
            0,
            0,
            0
        )
    )

    title_rect = title.get_rect(
        center=(
            BASE_WIDTH // 2,
            105
        )
    )

    game_surface.blit(
        title,
        title_rect
    )

    rating_surface = (
        option_label_font.render(
            f"Your Rating: "
            f"{career_rating:,}",
            True,
            (
                0,
                0,
                0
            )
        )
    )

    rating_rect = (
        rating_surface.get_rect(
            center=(
                BASE_WIDTH // 2,
                145
            )
        )
    )

    game_surface.blit(
        rating_surface,
        rating_rect
    )

    ribbon_image = get_jobfinder_image(
        "ribbon_award.png",
        (
            150,
            210
        )
    )

    if ribbon_image is not None:
        game_surface.blit(
            ribbon_image,
            (
                30,
                135
            )
        )

    # ==================================================
    # Job Listings
    # ==================================================

    for job_id, rect in (
        career_job_option_rects.items()
    ):

        job_data = (
            CAREER_JOBS[
                job_id
            ]
        )

        required_rating = (
            job_data[
                "required_rating"
            ]
        )

        unlocked = (
            career_rating
            >= required_rating
        )

        current = (
            career_job
            == job_id
        )

        # ----------------------------------------------
        # Background
        # ----------------------------------------------

        if current:
            fill_color = (
                210,
                240,
                210
            )

        elif unlocked:
            fill_color = (
                210,
                230,
                255
            )

        else:
            fill_color = (
                245,
                205,
                205
            )

        pygame.draw.rect(
            game_surface,
            fill_color,
            rect
        )

        pygame.draw.rect(
            game_surface,
            (
                0,
                0,
                0
            ),
            rect,
            3
        )

        # ----------------------------------------------
        # Doodle
        # ----------------------------------------------

        image = (
            get_career_job_image(
                job_id,
                (
                    150,
                    112
                )
            )
        )

        text_x = (
            rect.x + 18
        )

        if image is not None:

            image_rect = (
                image.get_rect(
                    midleft=(
                        rect.x + 12,
                        rect.centery
                    )
                )
            )

            game_surface.blit(
                image,
                image_rect
            )

            text_x = (
                rect.x + 175
            )

        # ----------------------------------------------
        # Job Name
        # ----------------------------------------------

        name_surface = (
            render_text_fit(
                job_data[
                    "name"
                ],
                option_label_font,
                rect.right
                - text_x
                - 12,
                (
                    0,
                    0,
                    0
                ),
                minimum_size=18
            )
        )

        game_surface.blit(
            name_surface,
            (
                text_x,
                rect.y + 18
            )
        )

        # ----------------------------------------------
        # Requirement
        # ----------------------------------------------

        if required_rating <= 0:

            requirement_text = (
                "No Rating Required"
            )

        else:

            requirement_text = (
                f"{required_rating:,} Rating"
            )

        requirement_surface = (
            difficulty_detail_font.render(
                requirement_text,
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        game_surface.blit(
            requirement_surface,
            (
                text_x,
                rect.y + 53
            )
        )

        # ----------------------------------------------
        # Pay
        # ----------------------------------------------

        pay_surface = (
            difficulty_detail_font.render(
                f"${job_data['pay']:,} "
                f"per shift",
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        game_surface.blit(
            pay_surface,
            (
                text_x,
                rect.y + 78
            )
        )

        # ----------------------------------------------
        # Status
        # ----------------------------------------------

        if current:
            status_text = "HERE"

        elif unlocked:
            status_text = "APPLY"

        else:
            status_text = "LOCKED"

        status_surface = (
            difficulty_detail_font.render(
                status_text,
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        game_surface.blit(
            status_surface,
            (
                text_x,
                rect.y + 105
            )
        )

    advice_image = get_jobfinder_image(
        "helpful_advice.png",
        (
            190,
            165
        )
    )

    if advice_image is not None:
        game_surface.blit(
            advice_image,
            (
                1090,
                430
            )
        )

    # ==================================================
    # Return
    # ==================================================

    draw_button(
        career_subpage_back_rect,
        "Return to Career"
    )

def draw_career_real_estate():

    game_surface.fill(
        (
            238,
            235,
            220
        )
    )

    # ==================================================
    # Browser Header
    # ==================================================

    draw_career_browser_header(
        "https://www.realestate.apt"
    )

    realestate_header = get_realestate_image(
        "realestate_header.png",
        (
            BASE_WIDTH,
            58
        )
    )

    if realestate_header is not None:
        game_surface.blit(
            realestate_header,
            (
                0,
                64
            )
        )

    # ==================================================
    # Title
    # ==================================================

    title = menu_title_font.render(
        "REALEST.ESTATE.ONLINE.",
        True,
        (
            0,
            0,
            0
        )
    )

    title_rect = title.get_rect(
        center=(
            BASE_WIDTH // 2,
            150
        )
    )

    game_surface.blit(
        title,
        title_rect
    )

    cash_surface = (
        option_label_font.render(
            f"Available Cash: "
            f"${career_cash:,}",
            True,
            (
                0,
                0,
                0
            )
        )
    )

    cash_rect = (
        cash_surface.get_rect(
            center=(
                BASE_WIDTH // 2,
                185
            )
        )
    )

    game_surface.blit(
        cash_surface,
        cash_rect
    )



    # ==================================================
    # Listings
    # ==================================================

    for residence_id, rect in (
        career_residence_option_rects.items()
    ):

        residence_data = (
            CAREER_RESIDENCES[
                residence_id
            ]
        )

        price = (
            residence_data[
                "price"
            ]
        )

        owned = (
            residence_id
            in career_owned_residences
        )

        current = (
            career_residence
            == residence_id
        )

        affordable = (
            career_cash >= price
        )

        # ----------------------------------------------
        # Card background
        # ----------------------------------------------

        if current:
            fill_color = (
                210,
                240,
                210
            )

        elif owned:
            fill_color = (
                220,
                235,
                255
            )

        elif affordable:
            fill_color = (
                210,
                230,
                255
            )

        else:
            fill_color = (
                245,
                205,
                205
            )

        pygame.draw.rect(
            game_surface,
            fill_color,
            rect
        )

        pygame.draw.rect(
            game_surface,
            (
                0,
                0,
                0
            ),
            rect,
            3
        )

        # ----------------------------------------------
        # Doodle
        # ----------------------------------------------

        image = (
            get_career_residence_image(
                residence_id,
                (
                    150,
                    112
                )
            )
        )

        text_x = (
            rect.x + 175
        )

        if image is not None:

            image_rect = (
                image.get_rect(
                    midleft=(
                        rect.x + 12,
                        rect.centery
                    )
                )
            )

            game_surface.blit(
                image,
                image_rect
            )

            text_x = (
                rect.x + 175
            )

        # ----------------------------------------------
        # Residence Name Rendering Block
        # ----------------------------------------------

        # ----------------------------------------------
        # Residence Name
        # ----------------------------------------------

        if residence_id == "summit":
            residence_name_font = pygame.font.Font(
                None,
                25
            )

            name_surface = (
                residence_name_font.render(
                    residence_data[
                        "name"
                    ],
                    True,
                    (
                        0,
                        0,
                        0
                    )
                )
            )

        else:
            name_surface = (
                option_label_font.render(
                    residence_data[
                        "name"
                    ],
                    True,
                    (
                        0,
                        0,
                        0
                    )
                )
            )

        game_surface.blit(
            name_surface,
            (
                text_x,
                rect.y + 18
            )
        )

        # ----------------------------------------------
        # Price
        # ----------------------------------------------

        if price <= 0:
            price_text = (
                "Starter Residence"
            )

        elif owned:
            price_text = (
                "Owned"
            )

        else:
            price_text = (
                f"${price:,}"
            )

        price_surface = (
            difficulty_detail_font.render(
                price_text,
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        game_surface.blit(
            price_surface,
            (
                text_x,
                rect.y + 62
            )
        )

        # ----------------------------------------------
        # Status
        # ----------------------------------------------

        if current:
            status_text = "HERE"

        elif owned:
            status_text = "MOVE IN"

        elif affordable:
            status_text = "BUY"

        else:
            status_text = "TOO POOR"

        status_surface = (
            difficulty_detail_font.render(
                status_text,
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        game_surface.blit(
            status_surface,
            (
                text_x,
                rect.y + 95
            )
        )

        # ==================================================
        # Property badges / stamps
        # ==================================================

        badge_image = None
        badge_filename = None

        # Current residence
        if residence_id == career_residence:

            badge_filename = (
                "current_stamp.png"
            )

            badge_image = get_realestate_image(
                badge_filename,
                (
                    110,
                    38
                )
            )

        # Owned residence
        elif residence_id in career_owned_residences:

            badge_filename = (
                "owned_stamp.png"
            )

            badge_image = get_realestate_image(
                badge_filename,
                (
                    85,
                    36
                )
            )

        # Featured
        elif residence_id in (
                "towers",
                "card_castle"
        ):

            badge_filename = (
                "featured_badge.png"
            )

            badge_image = get_realestate_image(
                badge_filename,
                (
                    95,
                    40
                )
            )

        # Hot listing
        elif residence_id in (
                "summit",
                "heliyacht"
        ):

            badge_filename = (
                "hot_listing.png"
            )

            badge_image = get_realestate_image(
                badge_filename,
                (
                    80,
                    38
                )
            )

        if badge_filename is not None and badge_image is None:
            print(
                "Could not load RealEstate badge:",
                badge_filename,
                "for",
                residence_id
            )

        if badge_image is not None:

            if badge_filename in (
                    "featured_badge.png",
                    "hot_listing.png"
            ):

                badge_rect = badge_image.get_rect(
                    top=rect.y + 6,
                    left=rect.right - 35
                )


            else:

                badge_rect = badge_image.get_rect(
                    bottom=rect.bottom - 8,
                    right=rect.right - 8
                )

            game_surface.blit(
                badge_image,
                badge_rect
            )

    draw_button(
        career_subpage_back_rect,
        "Return to Career"
    )

def draw_career_leaderboard_bio():

    game_surface.fill((235, 235, 225))
    draw_career_browser_header("https://www.cardrankings.net/bios")

    if selected_leaderboard_entry is None:
        title = menu_title_font.render("PLAYER BIO", True, (0, 0, 0))
        game_surface.blit(
            title,
            title.get_rect(center=(BASE_WIDTH // 2, 130))
        )
        draw_button(career_subpage_back_rect, "Return to Rankings")
        return

    entry = selected_leaderboard_entry
    name = entry.get("name", "Unknown Player")
    rating = entry.get("rating", 1000)
    rating_label = entry.get("rating_label", "Global")
    personality = personality_summary(entry.get("npc") or entry)

    bio = entry.get("bio", "Professional card player.") or "Professional card player."
    country = entry.get("country", "Unknown") or "Unknown"
    age = entry.get("age", "Unknown") or "Unknown"
    hometown = entry.get("hometown", "Unknown") or "Unknown"
    favorite_suit = entry.get("favorite_suit", "Unknown") or "Unknown"
    fans = int(entry.get("fans", 0) or 0)
    appeal_key = entry.get("public_appeal", "steady")
    appeal = (
        "N/A"
        if entry.get("is_player")
        else get_public_appeal_display_name(appeal_key)
    )
    is_star = entry.get("is_star", False)
    is_player = entry.get("is_player", False)

    title = menu_title_font.render(name, True, (0, 0, 0))
    game_surface.blit(
        title,
        title.get_rect(center=(BASE_WIDTH // 2, 135))
    )

    rating_surface = option_label_font.render(
        f"{rating_label}: {rating:,}",
        True,
        (0, 0, 0)
    )
    game_surface.blit(
        rating_surface,
        rating_surface.get_rect(center=(BASE_WIDTH // 2, 190))
    )

    if entry.get("is_prospect"):
        joined_year, joined_zero_month = divmod(int(entry["joined_month"]), 12)
        label = "PRODIGY" if entry.get("is_prodigy") else "PROSPECT"
        joined = difficulty_detail_font.render(
            f"{label} · Joined {CAREER_MONTH_NAMES[joined_zero_month + 1]} {joined_year}"
            + (" · WORLD #1" if is_star else ""),
            True, (40, 95, 105),
        )
        game_surface.blit(joined, joined.get_rect(center=(BASE_WIDTH // 2, 220)))
    elif is_star:
        star_surface = option_label_font.render(
            "WORLD #1",
            True,
            (180, 120, 0)
        )
        game_surface.blit(
            star_surface,
            star_surface.get_rect(center=(BASE_WIDTH // 2, 220))
        )

    # The bio and portrait are treated as one centered composition.
    bio_panel_rect = pygame.Rect(218, 240, 665, 300)
    portrait_panel_rect = pygame.Rect(901, 240, 247, 300)

    for panel in (bio_panel_rect, portrait_panel_rect):
        pygame.draw.rect(game_surface, (250, 250, 250), panel)
        pygame.draw.rect(game_surface, (0, 0, 0), panel, 3)

    if is_player:
        personality = "Player"

    birthday_month = entry.get("birthday_month")
    birthday_text = (f"  |  Birthday: {CAREER_MONTH_NAMES[birthday_month][:3]}"
                     if isinstance(birthday_month, int) and 1 <= birthday_month <= 12 else "")
    details = [
        f"Country: {country}",
        f"Age: {age}" + birthday_text
        + (f"  |  {entry.get('career_stage', 'Established')}" if not is_player else ""),
        f"Personality: {personality}",
        f"Public Appeal: {appeal}",
        f"Fans: {fans:,}",
        f"Hometown: {hometown}",
        f"Favorite Suit: {favorite_suit}",
    ]

    for index, detail in enumerate(details):
        detail_surface = render_text_fit(
            detail,
            option_value_font,
            bio_panel_rect.width - 50,
            (0, 0, 0),
            minimum_size=20,
        )
        game_surface.blit(
            detail_surface,
            (bio_panel_rect.x + 25, bio_panel_rect.y + 20 + index * 24)
        )

    draw_wrapped_text_limited(
        bio,
        option_label_font,
        (0, 0, 0),
        pygame.Rect(
            bio_panel_rect.x + 25,
            bio_panel_rect.y + 190,
            bio_panel_rect.width - 50,
            bio_panel_rect.height - 202
        ),
        max_lines=3,
        line_spacing=4
    )

    npc = entry.get("npc")
    if is_player:
        portrait = get_profile_avatar()
    elif isinstance(npc, dict):
        portrait = get_npc_portrait_surface(npc, 260)
    else:
        portrait = None

    if portrait is not None:
        max_rect = portrait_panel_rect.inflate(-24, -24)
        src_w, src_h = portrait.get_size()
        scale = min(
            max_rect.width / max(1, src_w),
            max_rect.height / max(1, src_h)
        )
        draw_size = (
            max(1, int(src_w * scale)),
            max(1, int(src_h * scale))
        )
        portrait = pygame.transform.smoothscale(portrait, draw_size)
        game_surface.blit(
            portrait,
            portrait.get_rect(center=portrait_panel_rect.center)
        )
    else:
        placeholder = options_title_font.render(
            "PLAYER" if is_player else "NPC ICON",
            True,
            (20, 20, 20)
        )
        game_surface.blit(
            placeholder,
            placeholder.get_rect(center=portrait_panel_rect.center)
        )

    if not is_player:
        draw_npc_traits(game_surface, entry.get("npc") or entry,
                        pygame.Rect(218, 550, 930, 153), difficulty_detail_font)
    draw_button(career_subpage_back_rect, "Return to Rankings")

def draw_career_leaderboards():

    global career_leaderboard_bio_rects

    career_leaderboard_bio_rects = []

    game_surface.fill(
        (
            235,
            235,
            225
        )
    )

    # ==================================================
    # Browser
    # ==================================================

    draw_career_browser_header(
        "https://www.cardrankings.net"
    )

    # ==================================================
    # Title / selected rating
    # ==================================================

    title = menu_title_font.render(
        "INTERNATIONAL CARD RANKINGS",
        True,
        (
            0,
            0,
            0
        )
    )

    title_rect = title.get_rect(
        center=(
            BASE_WIDTH // 2,
            103
        )
    )

    game_surface.blit(
        title,
        title_rect
    )

    rating_label = RATING_DISPLAY_NAMES.get(
        career_leaderboard_rating_key,
        "Global"
    )

    player_rank = (
        get_player_leaderboard_rank(
            career_leaderboard_rating_key
        )
    )

    selected_player_rating = career_ratings.get(
        career_leaderboard_rating_key,
        career_rating
    )

    player_info = (
        f"Your Rank: #{player_rank}     "
        f"{rating_label}: "
        f"{selected_player_rating:,}"
    )

    player_surface = (
        option_label_font.render(
            player_info,
            True,
            (
                0,
                0,
                0
            )
        )
    )

    player_rect = (
        player_surface.get_rect(
            center=(
                BASE_WIDTH // 2,
                140
            )
        )
    )

    game_surface.blit(
        player_surface,
        player_rect
    )

    draw_button(
        career_leaderboard_rating_prev_rect,
        "<",
        font=difficulty_detail_font
    )

    draw_button(
        career_leaderboard_rating_next_rect,
        ">",
        font=difficulty_detail_font
    )

    filter_surface = (
        option_value_font.render(
            "Sort by: " + {"overall": "Global", "strategy": "Strategy", "poker": "Poker", "casino": "Casino"}.get(career_leaderboard_rating_key, "Global"),
            True,
            (
                20,
                20,
                20
            )
        )
    )

    filter_rect = filter_surface.get_rect(
        center=(
            BASE_WIDTH // 2,
            179
        )
    )

    game_surface.blit(
        filter_surface,
        filter_rect
    )

    # ==================================================
    # Table
    # ==================================================

    leaderboard = (
        get_career_leaderboard(
            career_leaderboard_rating_key
        )
    )

    entries_per_page = 20

    start_index = (
            career_leaderboard_page
            * entries_per_page
    )

    end_index = (
            start_index
            + entries_per_page
    )

    visible_entries = (
        leaderboard[
            start_index:end_index
        ]
    )

    left_x = 205
    right_x = 700
    first_y = 210
    row_height = 43

    # Two columns of 10.
    for index, entry in enumerate(
        visible_entries
    ):

        if index < 10:
            column_x = left_x
            row_index = index
        else:
            column_x = right_x
            row_index = index - 10

        row_rect = pygame.Rect(
            column_x,
            first_y
            + row_index
            * row_height,
            460,
            38
        )

        if entry.get(
            "is_player"
        ):
            fill_color = (
                255,
                245,
                190
            )
        else:
            fill_color = (
                250,
                250,
                250
            )

        pygame.draw.rect(
            game_surface,
            fill_color,
            row_rect
        )

        pygame.draw.rect(
            game_surface,
            (
                0,
                0,
                0
            ),
            row_rect,
            2
        )

        rank = (
                start_index
                + index
                + 1
        )

        rank_surface = (
            difficulty_detail_font.render(
                f"{rank}.",
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        game_surface.blit(
            rank_surface,
            (
                row_rect.x + 7,
                row_rect.y + 9
            )
        )

        # ----------------------------------------------
        # Country flag thumbnail
        # ----------------------------------------------

        flag_box = pygame.Rect(
            row_rect.x + 38,
            row_rect.y + 4,
            30,
            30
        )
        flag = get_country_flag_surface(
            entry.get("country", ""),
            (30, 20)
        )

        if flag is not None:
            flag_rect = flag.get_rect(center=flag_box.center)
            game_surface.blit(flag, flag_rect)
            pygame.draw.rect(
                game_surface,
                (85, 85, 85),
                flag_rect.inflate(2, 2),
                1
            )
        else:
            code_surface = leaderboard_tiny_font.render(
                str(entry.get("country", ""))[:3],
                True,
                (70, 70, 70)
            )
            game_surface.blit(
                code_surface,
                code_surface.get_rect(center=flag_box.center)
            )

        # ----------------------------------------------
        # Name + personality
        # ----------------------------------------------

        country = entry.get(
            "country",
            ""
        )

        display_name = entry.get(
            "name",
            "Unknown"
        )

        name_surface = render_text_fit(
            display_name,
            difficulty_detail_font,
            168,
            (
                0,
                0,
                0
            ),
            minimum_size=11
        )

        name_x = row_rect.x + 76

        game_surface.blit(
            name_surface,
            (
                name_x,
                row_rect.y + 3
            )
        )

        personality = personality_summary(entry.get("npc") or entry).split(" / ")[0]

        if entry.get(
            "is_player"
        ):
            personality = "You"

        personality_surface = (
            leaderboard_tiny_font.render(
                personality,
                True,
                (
                    95,
                    95,
                    95
                )
            )
        )

        game_surface.blit(
            personality_surface,
            (
                name_x,
                row_rect.y + 21
            )
        )

        # ----------------------------------------------
        # Rating
        # ----------------------------------------------

        rating_surface = (
            difficulty_detail_font.render(
                f"{round(entry['rating']):,}",
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        rating_rect = (
            rating_surface.get_rect(
                right=(
                        row_rect.x
                        + 355
                ),
                centery=(
                    row_rect.centery
                )
            )
        )

        game_surface.blit(
            rating_surface,
            rating_rect
        )

        # ----------------------------------------------
        # Last movement in the selected game category
        # ----------------------------------------------

        # Keep fractional progress in saves; leaderboard movements are whole points.
        rating_change = int(round(entry.get("last_change", 0)))

        if rating_change > 0:
            change_text = (
                f"+{rating_change}"
            )
            change_color = (
                25,
                140,
                45
            )

        elif rating_change < 0:
            change_text = str(
                rating_change
            )
            change_color = (
                190,
                35,
                35
            )

        else:
            change_text = ""

        if change_text:
            change_surface = (
                pygame.font.Font(None, 24).render(
                    change_text,
                    True,
                    change_color
                )
            )

            game_surface.blit(
                change_surface,
                (
                    rating_rect.right + 5,
                    row_rect.centery - change_surface.get_height() // 2
                )
            )

        # ----------------------------------------------
        # View Bio
        # ----------------------------------------------

        bio_surface = (
            difficulty_detail_font.render(
                "Bio",
                True,
                (
                    20,
                    70,
                    170
                )
            )
        )

        bio_rect = (
            bio_surface.get_rect(
                right=(
                        row_rect.right
                        - 9
                ),
                centery=(
                    row_rect.centery
                )
            )
        )

        game_surface.blit(
            bio_surface,
            bio_rect
        )

        career_leaderboard_bio_rects.append(
            (
                bio_rect.copy(),
                entry
            )
        )

    # ==================================================
    # Player outside visible page
    # ==================================================

    if (
        player_rank is not None
        and not (
            start_index
            < player_rank
            <= end_index
        )
    ):

        outside_text = (
            f"You are #{player_rank} in {rating_label} "
            f"with {selected_player_rating:,} Rating."
        )

        outside_surface = (
            option_label_font.render(
                outside_text,
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        outside_rect = (
            outside_surface.get_rect(
                center=(
                    BASE_WIDTH // 2,
                    655
                )
            )
        )

        game_surface.blit(
            outside_surface,
            outside_rect
        )

    # ==================================================
    # Leaderboard Pagination
    # ==================================================

    total_pages = max(
        1,
        (
                len(leaderboard)
                + entries_per_page
                - 1
        )
        // entries_per_page
    )

    if career_leaderboard_page > 0:
        draw_button(
            career_leaderboard_prev_rect,
            "<"
        )

    if (
            career_leaderboard_page
            < total_pages - 1
    ):
        draw_button(
            career_leaderboard_next_rect,
            ">"
        )

    page_text = (
        f"Page "
        f"{career_leaderboard_page + 1} "
        f"of {total_pages}"
    )

    page_surface = (
        difficulty_detail_font.render(
            page_text,
            True,
            (
                0,
                0,
                0
            )
        )
    )

    page_rect = (
        page_surface.get_rect(
            center=(
                BASE_WIDTH // 2,
                675
            )
        )
    )

    game_surface.blit(
        page_surface,
        page_rect
    )

    draw_button(
        career_subpage_back_rect,
        "Return to Career"
    )

def draw_career_news():

    game_surface.fill(
        (
            238,
            235,
            220
        )
    )

    # ==================================================
    # Browser
    # ==================================================

    draw_career_browser_header(
        "https://www.thecardedcourrier.news"
    )

    ensure_career_news()

    # ==================================================
    # Newspaper Masthead
    # ==================================================

    title = courrier_title_font.render(
        "THE CARDED COURRIER",
        True,
        (
            0,
            0,
            0
        )
    )

    title_rect = (
        title.get_rect(
            center=(
                BASE_WIDTH // 2,
                110
            )
        )
    )

    game_surface.blit(
        title,
        title_rect
    )

    subtitle = (
        difficulty_detail_font.render(
            "THE INTERNATIONAL VOICE "
            "OF COMPETITIVE SOLITAIRE",
            True,
            (
                0,
                0,
                0
            )
        )
    )

    subtitle_rect = (
        subtitle.get_rect(
            center=(
                BASE_WIDTH // 2,
                145
            )
        )
    )

    game_surface.blit(
        subtitle,
        subtitle_rect
    )

    pygame.draw.line(
        game_surface,
        (
            0,
            0,
            0
        ),
        (
            120,
            165
        ),
        (
            BASE_WIDTH - 120,
            165
        ),
        3
    )

    # ==================================================
    # Pagination
    # ==================================================

    items_per_page = 6

    start_index = (
        career_news_page
        * items_per_page
    )

    end_index = (
        start_index
        + items_per_page
    )

    visible_news = (
        career_news_items[
            start_index:end_index
        ]
    )

    # ==================================================
    # Story Grid
    # ==================================================

    story_rects = [
        pygame.Rect(
            150,
            190,
            500,
            135
        ),

        pygame.Rect(
            715,
            190,
            500,
            135
        ),

        pygame.Rect(
            150,
            345,
            500,
            135
        ),

        pygame.Rect(
            715,
            345,
            500,
            135
        ),

        pygame.Rect(
            150,
            500,
            500,
            135
        ),

        pygame.Rect(
            715,
            500,
            500,
            135
        ),
    ]

    for index, item in enumerate(
            visible_news
    ):

        if index >= len(
            story_rects
        ):
            break

        rect = story_rects[
            index
        ]

        pygame.draw.rect(
            game_surface,
            (
                250,
                248,
                235
            ),
            rect
        )

        pygame.draw.rect(
            game_surface,
            (
                0,
                0,
                0
            ),
            rect,
            2
        )

        # ----------------------------------------------
        # Date
        # ----------------------------------------------

        date_surface = (
            difficulty_detail_font.render(
                get_career_news_date(
                    item
                ),
                True,
                (
                    90,
                    90,
                    90
                )
            )
        )

        game_surface.blit(
            date_surface,
            (
                rect.x + 12,
                rect.y + 8
            )
        )

        # ----------------------------------------------
        # Headline
        # ----------------------------------------------

        headline_surface = (
            render_text_fit(
                item.get(
                    "headline",
                    "UNTITLED STORY"
                ),
                option_label_font,
                rect.width - 24,
                (
                    0,
                    0,
                    0
                ),
                minimum_size=16
            )
        )

        game_surface.blit(
            headline_surface,
            (
                rect.x + 12,
                rect.y + 34
            )
        )

        # ----------------------------------------------
        # Body preview
        # ----------------------------------------------

        body = item.get(
            "body",
            ""
        )

        draw_wrapped_text(
            body,
            difficulty_detail_font,
            (
                0,
                0,
                0
            ),
            pygame.Rect(
                rect.x + 12,
                rect.y + 67,
                rect.width - 24,
                58
            ),
            line_spacing=3
        )

    # ==================================================
    # Page Controls
    # ==================================================

    total_pages = (
        get_career_news_total_pages()
    )

    if career_news_page > 0:

        draw_button(
            career_news_prev_rect,
            "<"
        )

    if (
        career_news_page
        < total_pages - 1
    ):

        draw_button(
            career_news_next_rect,
            ">"
        )

    page_surface = (
        difficulty_detail_font.render(
            (
                f"Page "
                f"{career_news_page + 1} "
                f"of {total_pages}"
            ),
            True,
            (
                0,
                0,
                0
            )
        )
    )

    page_rect = (
        page_surface.get_rect(
            center=(
                BASE_WIDTH // 2,
                675
            )
        )
    )

    game_surface.blit(
        page_surface,
        page_rect
    )

    draw_button(
        career_subpage_back_rect,
        "Return to Career"
    )



def start_press_interview_event():
    global career_interview_questions
    global career_interview_index
    global career_interview_media_heat
    global career_interview_fan_change
    global career_interview_feedback

    global career_interview_recent_ids
    career_interview_questions = select_interview(career_interview_recent_ids)
    career_interview_recent_ids = (career_interview_recent_ids + [q['id'] for q in career_interview_questions])[-12:]
    career_interview_index = 0
    career_interview_media_heat = 0
    career_interview_fan_change = 0
    career_interview_feedback = "The cameras are rolling."


def get_press_interview_temperature_label():
    if career_interview_media_heat >= 55:
        return "HOT"
    if career_interview_media_heat >= 20:
        return "WARM"
    if career_interview_media_heat <= -55:
        return "ICY"
    if career_interview_media_heat <= -20:
        return "COLD"
    return "NEUTRAL"


def handle_press_interview_answer(answer_index):
    global career_interview_index
    global career_interview_media_heat
    global career_interview_fan_change
    global career_interview_feedback
    global career_event_has_activity
    global career_event_summary_title
    global career_event_summary_lines
    global current_state

    if not (0 <= career_interview_index < len(career_interview_questions)):
        return False

    answers = career_interview_questions[career_interview_index]["answers"]
    if not (0 <= answer_index < len(answers)):
        return False

    career_interview_media_heat, proposed_change = answer_outcome(
        career_interview_media_heat, answers[answer_index], career_rating, career_fans
    )
    actual_change = award_career_fans(
        proposed_change,
        "Press interview"
    )
    career_interview_fan_change += actual_change

    if actual_change > 0:
        career_interview_feedback = f"The room responds well. +{actual_change:,} fans."
    elif actual_change < 0:
        career_interview_feedback = f"That answer lands badly. {actual_change:,} fans."
    else:
        career_interview_feedback = "The answer barely moves the needle."

    career_interview_index += 1
    career_event_has_activity = True

    if career_interview_index >= len(career_interview_questions):
        temperature = get_press_interview_temperature_label()
        signed = (
            f"+{career_interview_fan_change:,}"
            if career_interview_fan_change >= 0
            else f"{career_interview_fan_change:,}"
        )
        career_event_summary_title = "PRESS INTERVIEW COMPLETE"
        career_event_summary_lines = [
            f"Media reception: {temperature}",
            f"Fan change: {signed}",
            f"Total Fans: {career_fans:,} / {MAX_FANS:,}",
        ]
        current_state = STATE_CAREER_EVENT_SUMMARY

    return True



def start_sign_autographs_event():
    global career_autograph_fan_change
    global career_autograph_last_change
    global career_event_has_activity

    career_autograph_event.start()
    career_autograph_fan_change = 0
    career_autograph_last_change = 0
    career_event_has_activity = False


def handle_sign_autograph_submit():
    global career_autograph_fan_change
    global career_autograph_last_change
    global career_event_has_activity
    global career_event_summary_title
    global career_event_summary_lines
    global current_state

    score = career_autograph_event.submit_current()
    if score is None:
        return False

    proposed_change = fan_change_from_autograph_accuracy(
        score,
        current_fans=career_fans,
        current_rating=career_rating,
    )
    actual_change = award_career_fans(
        proposed_change,
        "Autograph signing",
    )
    career_autograph_last_change = actual_change
    career_autograph_fan_change += actual_change

    if career_autograph_event.complete:
        career_event_has_activity = True
        average = career_autograph_event.average_accuracy()
        signed = (
            f"+{career_autograph_fan_change:,}"
            if career_autograph_fan_change >= 0
            else f"{career_autograph_fan_change:,}"
        )
        career_event_summary_title = "SIGNING COMPLETE"
        career_event_summary_lines = [
            f"Average tracing accuracy: {average:.0f}%",
            f"Fan change: {signed}",
            f"Total Fans: {career_fans:,} / {MAX_FANS:,}",
        ]
        current_state = STATE_CAREER_EVENT_SUMMARY

    return True




def start_head_to_head_event():
    global head_to_head_opponents
    global head_to_head_selected_index
    global career_event_has_activity

    leaderboard = get_career_leaderboard(
        rating_key="solitaire"
    )
    head_to_head_opponents = select_head_to_head_opponents(
        leaderboard,
        career_ratings["solitaire"],
        count=4,
    )
    random.shuffle(head_to_head_opponents)
    head_to_head_selected_index = None
    head_to_head_race.reset()
    career_event_has_activity = False


def restore_head_to_head_game_settings():
    global head_to_head_previous_deal_mode
    global head_to_head_previous_difficulty
    global head_to_head_previous_stock_draw_count

    if head_to_head_previous_deal_mode is not None:
        game.set_deal_mode(
            head_to_head_previous_deal_mode
        )

    if head_to_head_previous_difficulty is not None:
        game.set_difficulty(
            head_to_head_previous_difficulty
        )

    if head_to_head_previous_stock_draw_count is not None:
        game.stock_draw_count = head_to_head_previous_stock_draw_count

    game.clear_challenge()
    head_to_head_previous_deal_mode = None
    head_to_head_previous_difficulty = None
    head_to_head_previous_stock_draw_count = None


def begin_selected_head_to_head_race():
    global current_state
    global current_game_mode
    global head_to_head_previous_deal_mode
    global head_to_head_previous_difficulty
    global head_to_head_previous_stock_draw_count
    global career_event_has_activity

    if not (
            head_to_head_selected_index is not None
            and 0 <= head_to_head_selected_index < len(head_to_head_opponents)
    ):
        return False

    opponent = dict(
        head_to_head_opponents[
            head_to_head_selected_index
        ]
    )

    ratings = opponent.get("ratings") or {}
    opponent["race_rating"] = ratings.get(
        "solitaire",
        opponent.get("rating", 1000)
    )

    head_to_head_previous_deal_mode = game.deal_mode
    head_to_head_previous_difficulty = game.difficulty
    head_to_head_previous_stock_draw_count = game.stock_draw_count

    game.clear_challenge()
    game.set_difficulty(DEFAULT_DIFFICULTY)

    game.stock_draw_count = 1
    game.set_deal_mode("random")
    game.new_race_game()

    head_to_head_race.prepare(
        opponent,
        player_rating=career_ratings["solitaire"],
        now_ms=pygame.time.get_ticks(),
    )

    career_event_has_activity = True
    current_game_mode = "head_to_head"
    current_state = STATE_PLAYING
    return True


def finish_head_to_head_race(
        won,
        round_data=None,
        forfeited=False
):
    global career_event_has_activity
    global career_event_summary_title
    global career_event_summary_lines
    global current_state
    global current_game_mode

    if head_to_head_race.opponent is None or head_to_head_race.reward_claimed:
        return False
    head_to_head_race.reward_claimed = True

    now_ms = pygame.time.get_ticks()

    if won:
        head_to_head_race.mark_winner(
            "player",
            now_ms
        )
    elif head_to_head_race.winner is None:
        head_to_head_race.mark_winner(
            "npc",
            now_ms
        )

    opponent = head_to_head_race.opponent
    opponent_name = opponent.get(
        "name",
        "Opponent"
    )
    opponent_rating = int(
        opponent.get("race_rating", opponent.get("rating", 1000))
    )

    player_progress = (
        52
        if won
        else head_to_head_race.player_progress_from_foundations(
            game.foundations
        )
    )
    elapsed_text = head_to_head_race.format_elapsed(
        now_ms
    )

    rating_change = rate_competitive_game("solitaire", opponent, won and not forfeited)
    fans_earned = 0

    if not forfeited:

        if won:
            fans_earned = award_fans_for_rating_win(
                rating_change,
                "Head-to-Head win"
            )
        else:
            fans_earned = lose_fans_for_bad_result(
                "Head-to-Head loss",
                severity=1.05,
            )

        award_game_xp(
            "head_to_head",
            won=won,
        )

        headline, body, category = build_head_to_head_story(
            player_name,
            opponent_name,
            won,
            elapsed_text=elapsed_text,
        )
        add_career_news(
            headline,
            body,
            category
        )

    career_event_has_activity = True

    if forfeited:
        career_event_summary_title = "RACE FORFEITED"
        result_line = f"{opponent_name} wins by forfeit."
    elif won:
        career_event_summary_title = "HEAD-TO-HEAD WIN"
        result_line = f"You beat {opponent_name} to 52 foundation cards."
    else:
        career_event_summary_title = "HEAD-TO-HEAD LOSS"
        result_line = f"{opponent_name} reached 52 foundation cards first."

    career_event_summary_lines = [
        result_line,
        f"Race time: {elapsed_text}",
        f"Your progress: {player_progress}/52",
        f"Opponent rating: {opponent_rating:,}",
        f"Strategy rating change: {rating_change:+,}" if rating_change else "Strategy rating change: 0",
        (
            f"Fan change: {fans_earned:+,}"
            if fans_earned
            else "Fan change: 0"
        ),
        f"Current Fans: {career_fans:,}",
    ]

    restore_head_to_head_game_settings()
    current_game_mode = "career"
    current_state = STATE_CAREER_EVENT_SUMMARY
    return True


def draw_head_to_head_event():
    draw_head_to_head_selection(
        game_surface,
        game_mouse_pos,
        head_to_head_opponents,
        head_to_head_selected_index,
        player_name,
        career_ratings["solitaire"],
        get_npc_portrait_surface,
        options_title_font,
        option_label_font,
        difficulty_detail_font,
        ui_small_font,
        player_avatar=get_profile_avatar(),
    )


def draw_sign_autographs_event():
    draw_submenu_background(overlay_alpha=145)

    outer = pygame.Rect(238, 82, 890, 610)
    outer_surface = pygame.Surface(outer.size, pygame.SRCALPHA)
    outer_surface.fill((20, 24, 28, 242))
    game_surface.blit(outer_surface, outer.topleft)
    pygame.draw.rect(
        game_surface,
        (220, 220, 220),
        outer,
        3,
        border_radius=12,
    )

    title = options_title_font.render(
        "SIGN AUTOGRAPHS",
        True,
        (255, 255, 255),
    )
    game_surface.blit(
        title,
        title.get_rect(center=(BASE_WIDTH // 2, 118)),
    )

    template = career_autograph_event.current_template
    template_name = template.get("name", "Autograph") if template else "Autograph"
    progress = option_label_font.render(
        f"Trace: {template_name}",
        True,
        (245, 226, 160),
    )
    game_surface.blit(
        progress,
        progress.get_rect(center=(BASE_WIDTH // 2, 158)),
    )

    canvas = AUTOGRAPH_CANVAS_RECT
    pygame.draw.rect(
        game_surface,
        (244, 241, 230),
        canvas,
        border_radius=12,
    )
    pygame.draw.rect(
        game_surface,
        (65, 65, 68),
        canvas,
        3,
        border_radius=12,
    )

    instruction = difficulty_detail_font.render(
        "Hold the left mouse button and trace the guide.",
        True,
        (65, 65, 68),
    )
    game_surface.blit(
        instruction,
        instruction.get_rect(center=(canvas.centerx, canvas.y + 26)),
    )

    target_points = career_autograph_event.get_target_points()
    if len(target_points) >= 2:
        pygame.draw.lines(
            game_surface,
            (213, 186, 115),
            False,
            target_points,
            10,
        )
        pygame.draw.lines(
            game_surface,
            (252, 243, 205),
            False,
            target_points,
            4,
        )

    trace = career_autograph_event.trace_points
    if len(trace) >= 2:
        pygame.draw.lines(
            game_surface,
            (45, 100, 180),
            False,
            trace,
            5,
        )

    accuracy = career_autograph_event.current_accuracy()
    accuracy_surface = difficulty_detail_font.render(
        f"Current accuracy: {accuracy:.0f}%",
        True,
        (45, 70, 105),
    )
    game_surface.blit(
        accuracy_surface,
        accuracy_surface.get_rect(
            bottomright=(canvas.right - 18, canvas.bottom - 14)
        ),
    )

    draw_button(
        AUTOGRAPH_CLEAR_RECT,
        "Clear",
        font=option_label_font,
    )
    draw_button(
        AUTOGRAPH_SUBMIT_RECT,
        "Sign It!",
        font=option_label_font,
    )

    feedback = career_autograph_event.feedback
    if career_autograph_last_change:
        signed = (
            f"+{career_autograph_last_change:,}"
            if career_autograph_last_change > 0
            else f"{career_autograph_last_change:,}"
        )
        feedback = f"{feedback}   Fans: {signed}"

    feedback_surface = difficulty_detail_font.render(
        feedback,
        True,
        (215, 220, 224),
    )
    game_surface.blit(
        feedback_surface,
        feedback_surface.get_rect(center=(BASE_WIDTH // 2, 664)),
    )

def draw_career_event():
    event_id = (
        career_event_entry.get("event_id")
        if isinstance(career_event_entry, dict)
        else None
    )

    if event_id == "sign_autographs_01":
        draw_sign_autographs_event()
        return

    if event_id == "head_to_head_01":
        draw_head_to_head_event()
        return

    if event_id != "press_interview_01":
        draw_career_placeholder_page(
            "CAREER EVENT",
            "This career event is not implemented yet."
        )
        return

    draw_submenu_background(overlay_alpha=150)

    panel = pygame.Rect(235, 105, 896, 545)
    panel_surface = pygame.Surface(panel.size, pygame.SRCALPHA)
    panel_surface.fill((18, 23, 28, 242))
    game_surface.blit(panel_surface, panel.topleft)
    pygame.draw.rect(game_surface, (220, 220, 220), panel, 3, border_radius=12)

    title = options_title_font.render("PRESS INTERVIEW", True, (255, 255, 255))
    game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 150)))

    progress = difficulty_detail_font.render(
        f"Question {min(career_interview_index + 1, len(career_interview_questions))} of {len(career_interview_questions)}",
        True,
        (205, 210, 215)
    )
    game_surface.blit(progress, progress.get_rect(center=(BASE_WIDTH // 2, 192)))

    # Media hot/cold meter.
    meter = pygame.Rect(448, 224, 470, 28)
    pygame.draw.rect(game_surface, (70, 85, 115), meter, border_radius=9)
    midpoint = meter.centerx
    heat_width = int((abs(career_interview_media_heat) / 100.0) * (meter.width // 2 - 4))
    if career_interview_media_heat >= 0:
        heat_rect = pygame.Rect(midpoint, meter.y + 4, heat_width, meter.height - 8)
        heat_color = (220, 115, 55)
    else:
        heat_rect = pygame.Rect(midpoint - heat_width, meter.y + 4, heat_width, meter.height - 8)
        heat_color = (75, 155, 230)
    if heat_width > 0:
        pygame.draw.rect(game_surface, heat_color, heat_rect, border_radius=6)
    pygame.draw.line(game_surface, (245, 245, 245), (midpoint, meter.y), (midpoint, meter.bottom), 2)

    temperature = difficulty_detail_font.render(
        f"MEDIA: {get_press_interview_temperature_label()}",
        True,
        (255, 235, 165)
    )
    game_surface.blit(temperature, temperature.get_rect(center=(BASE_WIDTH // 2, 272)))

    if 0 <= career_interview_index < len(career_interview_questions):
        question = career_interview_questions[career_interview_index]
        draw_wrapped_text(
            question["question"],
            option_label_font,
            (255, 255, 255),
            pygame.Rect(335, 305, 696, 78),
            line_spacing=6
        )

        for index, (answer_text, _heat, _appeal) in enumerate(question["answers"]):
            rect = career_interview_answer_rects[index]
            draw_button(rect, answer_text, font=difficulty_detail_font)

    feedback = difficulty_detail_font.render(
        career_interview_feedback,
        True,
        (210, 215, 220)
    )
    game_surface.blit(feedback, feedback.get_rect(center=(BASE_WIDTH // 2, 620)))

    # The interview is a committed Career event once started. Complete all
    # three questions to return to the calendar.

POKER_NIGHT_SELECTION_IMAGE_SIZE = (
    288,
    162
)

POKER_NIGHT_SELECTION_IMAGE_PATHS = {
    "texas_holdem":
        "assets/poker/poker_night/texas_holdem.png",
    "seven_card_stud":
        "assets/poker/poker_night/seven_card_stud.png",
    "five_card_draw":
        "assets/poker/poker_night/five_card_draw.png",
}

_poker_night_selection_image_cache = {}


EVENT_SELECTION_IMAGE_SIZE = (288, 162)

EVENT_SELECTION_IMAGE_PATHS = {
    "score_four": "assets/events/casual_cards/score_four.png",
    "crazy_eights": "assets/events/casual_cards/crazy_eights.png",
    "bango": "assets/events/casual_cards/bango.png",
    "blackjack": "assets/events/casino_night/blackjack.png",
    "roulette": "assets/events/casino_night/roulette.png",
    "horse_races": "assets/events/casino_night/horse_races.png",
    "faro": "assets/events/niche_night/faro.png",
    "five_o_poker": "assets/events/niche_night/five_o_poker.png",
    "blind_mans_bluff": "assets/events/niche_night/blind_mans_bluff.png",
    "king_pong": "assets/arcade/king_pong/select.png",
    "battle_bosses": "assets/arcade/battle_bosses/select.png",
    "ace_invaders": "assets/arcade/ace_invaders/select.png",
    "suit_snake": "assets/arcade/suit_snake/select.png",
    "prize_counter": "assets/arcade/ui/prize_counter.png",
}

_event_selection_image_cache = {}

EVENT_TITLE_ASSET_PATHS = {
    CAREER_ACTIVITY_CASUAL_CARDS: "assets/events/casual_cards/title.png",
    CAREER_ACTIVITY_POKER_NIGHT: "assets/events/poker_night/title.png",
    CAREER_ACTIVITY_CASINO_NIGHT: "assets/events/casino_night/title.png",
    CAREER_ACTIVITY_NICHE_NIGHT: "assets/events/niche_night/title.png",
}

EVENT_BACKGROUND_ASSET_PATHS = {
    CAREER_ACTIVITY_CASUAL_CARDS: "assets/events/casual_cards/background.png",
    CAREER_ACTIVITY_POKER_NIGHT: "assets/events/poker_night/background.png",
    CAREER_ACTIVITY_CASINO_NIGHT: "assets/events/casino_night/background.png",
    CAREER_ACTIVITY_NICHE_NIGHT: "assets/events/niche_night/background.png",
    CAREER_ACTIVITY_ARCADE_NIGHT: "assets/arcade/bg.png",
}

EVENT_BUTTON_ASSET_PATHS = {
    CAREER_ACTIVITY_CASUAL_CARDS: {
        "return": "assets/events/casual_cards/return.png",
        "end": "assets/events/casual_cards/end_night.png",
    },
    CAREER_ACTIVITY_POKER_NIGHT: {
        "return": "assets/events/poker_night/return.png",
        "end": "assets/events/poker_night/end_night.png",
    },
    CAREER_ACTIVITY_CASINO_NIGHT: {
        "return": "assets/events/casino_night/return.png",
        "end": "assets/events/casino_night/end_night.png",
    },
    CAREER_ACTIVITY_NICHE_NIGHT: {
        "return": "assets/events/niche_night/return.png",
        "end": "assets/events/niche_night/end_night.png",
    },
}

_event_ui_asset_cache = {}


def get_event_ui_asset(path, size=None):
    if not path:
        return None
    cache_key = (path, tuple(size) if size else None)
    if cache_key in _event_ui_asset_cache:
        return _event_ui_asset_cache[cache_key]
    try:
        image = pygame.image.load(path).convert_alpha()
        if size is not None:
            image = pygame.transform.smoothscale(image, size)
    except (pygame.error, FileNotFoundError):
        image = None
    _event_ui_asset_cache[cache_key] = image
    return image


def draw_event_image_button(rect, activity_type, button_kind, fallback_text, enabled=True):
    path = EVENT_BUTTON_ASSET_PATHS.get(activity_type, {}).get(button_kind)
    image = get_event_ui_asset(path, rect.size)
    hovered = (
        enabled
        and game_mouse_pos is not None
        and rect.collidepoint(game_mouse_pos)
    )

    if image is None:
        draw_menu_button(
            rect,
            fallback_text,
            game_mouse_pos,
            font=difficulty_detail_font
        )
        if not enabled:
            overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 125))
            game_surface.blit(overlay, rect.topleft)
        return

    button = image.copy()
    if hovered:
        button.fill((22, 22, 22, 0), special_flags=pygame.BLEND_RGBA_ADD)
    if not enabled:
        button.fill((110, 110, 110, 255), special_flags=pygame.BLEND_RGBA_MULT)
        button.set_alpha(150)
    game_surface.blit(button, rect.topleft)


def get_event_selection_image(game_id, size=None):
    path = EVENT_SELECTION_IMAGE_PATHS.get(game_id)
    if not path:
        return None

    requested_size = tuple(size or EVENT_SELECTION_IMAGE_SIZE)
    cache_key = (game_id, requested_size)
    if cache_key in _event_selection_image_cache:
        return _event_selection_image_cache[cache_key]

    try:
        image = pygame.image.load(path).convert_alpha()
        image = pygame.transform.smoothscale(image, requested_size)
        _event_selection_image_cache[cache_key] = image
        return image
    except (pygame.error, FileNotFoundError):
        return None


def get_poker_night_selection_image(game_id, size=None):
    path = POKER_NIGHT_SELECTION_IMAGE_PATHS.get(game_id)

    if not path:
        return None

    requested_size = tuple(size or POKER_NIGHT_SELECTION_IMAGE_SIZE)
    cache_key = (game_id, requested_size)

    if cache_key in _poker_night_selection_image_cache:
        return _poker_night_selection_image_cache[cache_key]

    try:
        image = pygame.image.load(path).convert_alpha()
        image = pygame.transform.smoothscale(image, requested_size)
        _poker_night_selection_image_cache[cache_key] = image
        return image

    except (pygame.error, FileNotFoundError):
        return None


def get_career_event_card_layout(activity_type, game_count):
    if activity_type == CAREER_ACTIVITY_ARCADE_NIGHT or game_count >= 5:
        return 232, 312, 14, 184
    if game_count == 4:
        return 246, 320, 18, 180
    return 300, 330, 30, 178


def draw_poker_night_high_stakes_label(
        surface,
        center
):
    label = "HIGH STAKES"

    # Several soft offset passes make the gold lettering glow
    # without requiring a separate asset.
    for offset_x, offset_y, alpha in (
            (-3, 0, 60),
            (3, 0, 60),
            (0, -3, 60),
            (0, 3, 60),
            (-2, -2, 50),
            (2, -2, 50),
            (-2, 2, 50),
            (2, 2, 50),
    ):
        glow = difficulty_detail_font.render(
            label,
            True,
            (
                255,
                185,
                45
            )
        )
        glow.set_alpha(
            alpha
        )
        glow_rect = glow.get_rect(
            center=(
                center[0] + offset_x,
                center[1] + offset_y
            )
        )
        surface.blit(
            glow,
            glow_rect
        )

    text_surface = difficulty_detail_font.render(
        label,
        True,
        (
            255,
            230,
            95
        )
    )

    text_rect = text_surface.get_rect(
        center=center
    )

    surface.blit(
        text_surface,
        text_rect
    )


def draw_arcade_night_select():
    background = get_event_ui_asset("assets/arcade/bg.png", (BASE_WIDTH, BASE_HEIGHT))
    if background is not None:
        game_surface.blit(background, (0, 0))
    else:
        game_surface.fill((13, 18, 28))

    shade = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
    shade.fill((0, 0, 0, 42))
    game_surface.blit(shade, (0, 0))

    title = options_title_font.render("ARCADE NIGHT", True, (255, 255, 255))
    subtitle = difficulty_detail_font.render(
        "Choose a machine, buy tokens, and turn your wins into tickets.",
        True,
        (221, 226, 232),
    )
    game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 48)))
    game_surface.blit(subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 88)))

    counter_data = (
        ("CASH", f"${career_cash:,}"),
        ("TOKENS", f"{int(arcade_state.get('tokens', 0)):,}"),
        ("TICKETS", f"{int(arcade_state.get('tickets', 0)):,}"),
    )
    counter_width = 220
    counter_gap = 22
    total_counter_width = counter_width * 3 + counter_gap * 2
    counter_x = (BASE_WIDTH - total_counter_width) // 2
    for index, (label, value) in enumerate(counter_data):
        rect = pygame.Rect(counter_x + index * (counter_width + counter_gap), 112, counter_width, 54)
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((7, 14, 24, 222))
        game_surface.blit(panel, rect.topleft)
        pygame.draw.rect(game_surface, (92, 184, 218), rect, 2, border_radius=9)
        label_surface = difficulty_detail_font.render(label, True, (179, 191, 203))
        value_surface = option_label_font.render(value, True, (255, 237, 151))
        game_surface.blit(label_surface, label_surface.get_rect(midleft=(rect.x + 14, rect.centery)))
        game_surface.blit(value_surface, value_surface.get_rect(midright=(rect.right - 14, rect.centery)))

    machine_ids = [
        game_id
        for game_id in career_event_entry.get("game_ids", [])
        if game_id != "prize_counter"
    ]
    machine_names = {
        "king_pong": "King Pong",
        "battle_bosses": "Battle Bosses",
        "ace_invaders": "Ace Invaders",
        "suit_snake": "Suit Snake",
    }
    descriptions = {
        "king_pong": ("King vs. King paddle action.", "First to five wins."),
        "battle_bosses": ("Deflect the Joker projectile", "and break the rival strongholds."),
        "ace_invaders": ("Blast waves of incoming", "Aces before they reach you."),
        "suit_snake": ("Build a card-chain snake", "through the deck in sequence."),
    }

    card_width = 276
    card_height = 326
    card_gap = 18
    card_y = 188
    total_width = card_width * len(machine_ids) + card_gap * max(0, len(machine_ids) - 1)
    start_x = (BASE_WIDTH - total_width) // 2

    for index, game_id in enumerate(machine_ids):
        rect = pygame.Rect(start_x + index * (card_width + card_gap), card_y, card_width, card_height)
        unlocked = is_game_unlocked(game_id)
        coming_soon = game_id in ARCADE_COMING_SOON_GAME_IDS
        hovered = (
            unlocked
            and not coming_soon
            and game_mouse_pos is not None
            and rect.collidepoint(game_mouse_pos)
        )

        fill = (22, 31, 44, 238) if not hovered else (31, 57, 68, 242)
        card_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        card_surface.fill(fill)
        game_surface.blit(card_surface, rect.topleft)
        border = (247, 213, 115) if hovered else (198, 207, 219)
        pygame.draw.rect(game_surface, border, rect, 3 if hovered else 2, border_radius=12)

        image_rect = pygame.Rect(rect.x + 8, rect.y + 8, rect.width - 16, 146)
        image = get_event_selection_image(game_id, image_rect.size)
        if image is not None:
            game_surface.blit(image, image_rect)
        else:
            pygame.draw.rect(game_surface, (7, 10, 16), image_rect, border_radius=7)
            placeholder = difficulty_detail_font.render("SELECT ART", True, (114, 123, 136))
            game_surface.blit(placeholder, placeholder.get_rect(center=image_rect.center))

        if coming_soon or not unlocked:
            overlay = pygame.Surface(image_rect.size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 145))
            game_surface.blit(overlay, image_rect.topleft)
            if coming_soon:
                state_text = "COMING SOON"
            else:
                state_text = f"LOCKED — LEVEL {get_game_unlock_level(game_id)}"
            state_surface = option_label_font.render(state_text, True, (245, 245, 245))
            game_surface.blit(state_surface, state_surface.get_rect(center=image_rect.center))

        name = option_label_font.render(machine_names.get(game_id, game_id.replace("_", " ").title()), True, (248, 249, 250))
        game_surface.blit(name, name.get_rect(center=(rect.centerx, rect.y + 181)))

        for line_index, line in enumerate(descriptions.get(game_id, ("Arcade machine.", ""))):
            line_surface = difficulty_detail_font.render(line, True, (204, 212, 221))
            game_surface.blit(line_surface, line_surface.get_rect(center=(rect.centerx, rect.y + 220 + line_index * 25)))

        token_cost = get_machine_cost(game_id)
        cost_text = "COMING SOON" if coming_soon else f"{token_cost} TOKEN{'S' if token_cost != 1 else ''} PER PLAY"
        cost_color = (155, 163, 176) if coming_soon else (255, 235, 145)
        cost_surface = difficulty_detail_font.render(cost_text, True, cost_color)
        game_surface.blit(cost_surface, cost_surface.get_rect(center=(rect.centerx, rect.bottom - 28)))

        career_event_card_rects.append((rect, game_id))

    draw_menu_button(
        arcade_machine_buy_tokens_rect,
        "Buy Tokens",
        game_mouse_pos,
        font=option_label_font,
    )

    # Prize Counter uses its authored 640x360 select art rather than appearing
    # as another generic text button. Keep the art at 16:9 on the left and the
    # service label on the right so it remains readable at this compact size.
    prize_rect = arcade_machine_prize_counter_rect
    prize_hovered = game_mouse_pos is not None and prize_rect.collidepoint(game_mouse_pos)
    prize_panel = pygame.Surface(prize_rect.size, pygame.SRCALPHA)
    prize_panel.fill((28, 42, 55, 244) if prize_hovered else (18, 29, 42, 238))
    game_surface.blit(prize_panel, prize_rect.topleft)
    pygame.draw.rect(
        game_surface,
        (247, 213, 115) if prize_hovered else (178, 190, 204),
        prize_rect,
        3 if prize_hovered else 2,
        border_radius=10,
    )
    prize_art_rect = pygame.Rect(prize_rect.x + 4, prize_rect.y + 4, 149, 84)
    prize_art = get_event_selection_image("prize_counter", prize_art_rect.size)
    if prize_art is not None:
        game_surface.blit(prize_art, prize_art_rect)
    else:
        pygame.draw.rect(game_surface, (7, 12, 19), prize_art_rect, border_radius=6)
        missing = ui_small_font.render("PRIZE ART", True, (120, 132, 146))
        game_surface.blit(missing, missing.get_rect(center=prize_art_rect.center))
    prize_title = option_label_font.render("Prize Counter", True, (248, 249, 250))
    prize_note = ui_small_font.render("Tickets + Trophies", True, (255, 235, 145))
    label_center_x = prize_art_rect.right + (prize_rect.right - prize_art_rect.right) // 2
    game_surface.blit(prize_title, prize_title.get_rect(center=(label_center_x, prize_rect.y + 34)))
    game_surface.blit(prize_note, prize_note.get_rect(center=(label_center_x, prize_rect.y + 61)))

    career_event_card_rects.append((arcade_machine_buy_tokens_rect, "token_exchange"))
    career_event_card_rects.append((arcade_machine_prize_counter_rect, "prize_counter"))

    draw_event_image_button(
        career_event_return_rect,
        CAREER_ACTIVITY_ARCADE_NIGHT,
        "return",
        "Return",
        enabled=True,
    )
    draw_event_image_button(
        career_event_end_rect,
        CAREER_ACTIVITY_ARCADE_NIGHT,
        "end",
        "End Arcade Night",
        enabled=career_event_has_activity,
    )

    if not career_event_has_activity and game_mouse_pos is not None and career_event_end_rect.collidepoint(game_mouse_pos):
        tooltip_surface = difficulty_detail_font.render(
            "Play at least one arcade game before ending the night.",
            True,
            (245, 245, 245),
        )
        tooltip_rect = tooltip_surface.get_rect(
            midbottom=(career_event_end_rect.centerx, career_event_end_rect.y - 8)
        ).inflate(20, 12)
        panel = pygame.Surface(tooltip_rect.size, pygame.SRCALPHA)
        panel.fill((8, 14, 23, 235))
        game_surface.blit(panel, tooltip_rect.topleft)
        pygame.draw.rect(game_surface, (228, 198, 108), tooltip_rect, 2, border_radius=8)
        game_surface.blit(tooltip_surface, tooltip_surface.get_rect(center=tooltip_rect.center))

    if arcade_status_message and pygame.time.get_ticks() <= arcade_status_message_expires:
        message_surface = difficulty_detail_font.render(arcade_status_message, True, (251, 244, 217))
        backdrop = message_surface.get_rect(center=(BASE_WIDTH // 2, 540)).inflate(24, 12)
        pane = pygame.Surface(backdrop.size, pygame.SRCALPHA)
        pane.fill((8, 14, 24, 230))
        game_surface.blit(pane, backdrop.topleft)
        pygame.draw.rect(game_surface, (226, 194, 104), backdrop, 2, border_radius=8)
        game_surface.blit(message_surface, message_surface.get_rect(center=backdrop.center))


def _draw_career_event_select():
    game_surface.fill((20, 28, 35))
    career_event_card_rects.clear()

    if career_event_entry is None:
        return

    activity_type = career_event_entry.get("activity_type")
    if activity_type == CAREER_ACTIVITY_ARCADE_NIGHT:
        draw_arcade_night_select()
        return

    is_poker_night = activity_type == CAREER_ACTIVITY_POKER_NIGHT
    is_arcade_night = activity_type == CAREER_ACTIVITY_ARCADE_NIGHT
    event_title = CAREER_EVENT_NAMES.get(activity_type, "Card Event")

    background_path = EVENT_BACKGROUND_ASSET_PATHS.get(activity_type)
    background = get_event_ui_asset(background_path, (BASE_WIDTH, BASE_HEIGHT))
    if background is not None:
        game_surface.blit(background, (0, 0))
        shade = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 45))
        game_surface.blit(shade, (0, 0))

    title_asset = get_event_ui_asset(EVENT_TITLE_ASSET_PATHS.get(activity_type), (360, 96))
    if title_asset is not None:
        game_surface.blit(title_asset, title_asset.get_rect(center=(BASE_WIDTH // 2, 66)))
    else:
        title_surface = options_title_font.render(event_title, True, (255, 255, 255))
        game_surface.blit(title_surface, title_surface.get_rect(center=(BASE_WIDTH // 2, 78)))

    subtitle_text = "Choose your machine" if is_arcade_night else ("Choose your table" if is_poker_night else "Choose a game")
    subtitle_surface = difficulty_detail_font.render(subtitle_text, True, (230, 230, 230))
    subtitle_y = 126
    game_surface.blit(subtitle_surface, subtitle_surface.get_rect(center=(BASE_WIDTH // 2, subtitle_y)))

    if is_arcade_night:
        counters = (
            ("Cash", f"${career_cash:,}"),
            ("Tokens", f"{int(arcade_state.get('tokens', 0)):,}"),
            ("Tickets", f"{int(arcade_state.get('tickets', 0)):,}"),
        )
        for index, (label, value) in enumerate(counters):
            rect = pygame.Rect(392 + index * 198, 144, 182, 44)
            pygame.draw.rect(game_surface, (12, 20, 30), rect, border_radius=10)
            pygame.draw.rect(game_surface, (226, 195, 104), rect, 2, border_radius=10)
            label_surface = difficulty_detail_font.render(label, True, (212, 219, 225))
            value_surface = difficulty_detail_font.render(value, True, (255, 237, 156))
            game_surface.blit(label_surface, label_surface.get_rect(midleft=(rect.x + 14, rect.centery)))
            game_surface.blit(value_surface, value_surface.get_rect(midright=(rect.right - 14, rect.centery)))

    game_ids = career_event_entry.get("game_ids", [])
    uses_image_cards = activity_type in (
        CAREER_ACTIVITY_CASUAL_CARDS,
        CAREER_ACTIVITY_POKER_NIGHT,
        CAREER_ACTIVITY_CASINO_NIGHT,
        CAREER_ACTIVITY_NICHE_NIGHT,
        CAREER_ACTIVITY_ARCADE_NIGHT,
    )

    if uses_image_cards:
        card_width, card_height, card_gap, card_y = get_career_event_card_layout(activity_type, len(game_ids))
    else:
        card_width, card_height, card_gap, card_y = 270, 250, 35, 220

    total_width = card_width * len(game_ids) + card_gap * max(0, len(game_ids) - 1)
    start_x = BASE_WIDTH // 2 - total_width // 2

    game_names = {
        "score_four": "Score-Four",
        "bango": "Bango",
        "crazy_eights": "Crazy Eights",
        "texas_holdem": "Texas Hold'em",
        "seven_card_stud": "Seven-Card Stud",
        "five_card_draw": "Five-Card Draw",
        "blackjack": "Blackjack",
        "roulette": "Roulette",
        "horse_races": "Horse Races",
        "faro": "Faro",
        "five_o_poker": "Five-O Poker",
        "blind_mans_bluff": "Blind Man's Bluff",
        **ARCADE_MACHINE_NAMES,
    }

    poker_descriptions = {
        "texas_holdem": ("Community cards, blinds,", "and no-limit betting."),
        "seven_card_stud": ("Seven cards, exposed streets,", "and fixed-limit betting."),
        "five_card_draw": ("Classic draw poker with", "one discard-and-draw round."),
    }

    event_descriptions = {
        "score_four": ("Use all four numbers", "to make exactly 24."),
        "crazy_eights": ("Match suit or rank;", "eights are wild."),
        "bango": ("Cover all five cards", "before anyone else."),
        "blackjack": ("Beat the dealer", "without going over 21."),
        "roulette": ("Place your chips", "and spin the wheel."),
        "horse_races": ("Back a horse to Win,", "Place, or Show."),
        "faro": ("Back ranks against", "the banker deck."),
        "five_o_poker": ("Build five poker hands", "at the same time."),
        "blind_mans_bluff": ("See every card", "except your own."),
        "king_pong": ("Arcade paddle duel", "for tickets and bragging rights."),
        "battle_bosses": ("Card battlers and", "boss fights are on deck."),
        "ace_invaders": ("A retro shooter with", "card-flavored waves."),
        "suit_snake": ("Chase a longer chain", "of hearts, clubs, and spades."),
        "prize_counter": ("Redeem tickets and", "check your trophy shelf."),
    }

    for index, game_id in enumerate(game_ids):
        rect = pygame.Rect(start_x + index * (card_width + card_gap), card_y, card_width, card_height)
        unlocked = is_game_unlocked(game_id)
        coming_soon = is_arcade_night and game_id in ARCADE_COMING_SOON_GAME_IDS
        clickable = unlocked and not coming_soon
        hovered = clickable and game_mouse_pos is not None and rect.collidepoint(game_mouse_pos)

        if not unlocked:
            fill_color, border_color, border_width = (55, 55, 58), (125, 125, 130), 3
        elif coming_soon:
            fill_color, border_color, border_width = (48, 53, 70), (158, 166, 188), 3
        elif hovered:
            fill_color, border_color, border_width = (48, 112, 66), (255, 225, 120), 5
        else:
            fill_color, border_color, border_width = (38, 92, 53), (235, 235, 235), 3

        pygame.draw.rect(game_surface, fill_color, rect, border_radius=10)
        pygame.draw.rect(game_surface, border_color, rect, border_width, border_radius=10)

        game_name = game_names.get(game_id, game_id.replace("_", " ").title())
        is_high_stakes = is_poker_night and game_id == career_event_entry.get("high_stakes_game_id")

        image_width = max(120, card_width - 12)
        image_height = max(90, int(round(image_width * 9 / 16)))
        image_rect = pygame.Rect(rect.x + (card_width - image_width) // 2, rect.y + 17, image_width, image_height)
        image = get_poker_night_selection_image(game_id, image_rect.size) if is_poker_night else get_event_selection_image(game_id, image_rect.size)

        if image is not None:
            game_surface.blit(image, image_rect)
        else:
            pygame.draw.rect(game_surface, (24, 28, 31), image_rect, border_radius=6)
            pygame.draw.rect(game_surface, (115, 125, 130), image_rect, 2, border_radius=6)
            missing_name = option_label_font.render(game_name, True, (220, 222, 224))
            missing_note = difficulty_detail_font.render("EVENT ART", True, (150, 155, 160))
            game_surface.blit(missing_name, missing_name.get_rect(center=(image_rect.centerx, image_rect.centery - 12)))
            game_surface.blit(missing_note, missing_note.get_rect(center=(image_rect.centerx, image_rect.centery + 18)))

        if not unlocked or coming_soon:
            overlay = pygame.Surface(image_rect.size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 145 if not unlocked else 120))
            game_surface.blit(overlay, image_rect.topleft)
            if not unlocked:
                required_level = get_game_unlock_level(game_id)
                text_line = f"LOCKED - LEVEL {required_level}"
            else:
                text_line = "COMING SOON"
            lock_surface = difficulty_detail_font.render(text_line, True, (240, 240, 240))
            game_surface.blit(lock_surface, lock_surface.get_rect(center=image_rect.center))

        description_lines = poker_descriptions.get(game_id, ("Poker Night game.", "")) if is_poker_night else event_descriptions.get(game_id, ("Card game.", ""))
        description_y = image_rect.bottom + 18
        if is_high_stakes:
            draw_poker_night_high_stakes_label(game_surface, (rect.centerx, image_rect.bottom + 8))
            description_y += 18

        for line_index, line in enumerate(description_lines):
            if not line:
                continue
            line_surface = difficulty_detail_font.render(line, True, (220, 223, 225))
            game_surface.blit(line_surface, line_surface.get_rect(center=(rect.centerx, description_y + line_index * 25)))

        career_event_card_rects.append((rect, game_id))

    draw_event_image_button(career_event_return_rect, activity_type, "return", "Return", enabled=True)

    if career_event_entry is not None:
        event_name = CAREER_EVENT_NAMES.get(activity_type, "Event")
        draw_event_image_button(career_event_end_rect, activity_type, "end", f"End {event_name}", enabled=career_event_has_activity)

    if (not career_event_has_activity and game_mouse_pos is not None and career_event_end_rect.collidepoint(game_mouse_pos)):
        tooltip_text = "Play at least one game before ending the event."
        tooltip_surface = difficulty_detail_font.render(tooltip_text, True, (245, 245, 245))
        tooltip_rect = tooltip_surface.get_rect(midbottom=(career_event_end_rect.centerx, career_event_end_rect.y - 10)).inflate(22, 14)
        panel = pygame.Surface(tooltip_rect.size, pygame.SRCALPHA)
        panel.fill((12, 18, 16, 235))
        game_surface.blit(panel, tooltip_rect.topleft)
        pygame.draw.rect(game_surface, (228, 200, 115), tooltip_rect, 2, border_radius=7)
        game_surface.blit(tooltip_surface, tooltip_surface.get_rect(center=tooltip_rect.center))

    if is_arcade_night and arcade_status_message and pygame.time.get_ticks() <= arcade_status_message_expires:
        message_surface = difficulty_detail_font.render(arcade_status_message, True, (251, 244, 217))
        backdrop = message_surface.get_rect(center=(BASE_WIDTH // 2, 714)).inflate(28, 16)
        pane = pygame.Surface(backdrop.size, pygame.SRCALPHA)
        pane.fill((14, 19, 32, 228))
        game_surface.blit(pane, backdrop.topleft)
        pygame.draw.rect(game_surface, (226, 194, 104), backdrop, 2, border_radius=9)
        game_surface.blit(message_surface, message_surface.get_rect(center=backdrop.center))


def draw_career_event_select():
    _draw_career_event_select()
    if not career_event_entry:
        return
    if career_event_entry.get("activity_type") == CAREER_ACTIVITY_ARCADE_NIGHT:
        return
    from career_ratings import GAME_CATEGORIES
    games = career_event_entry.get("game_ids", [])
    count = len(games)
    if not count:
        return
    width, _height, gap, card_y = get_career_event_card_layout(career_event_entry.get("activity_type"), count)
    start = (BASE_WIDTH - (width * count + gap * (count - 1))) // 2
    label_y = max(150, card_y - 14)
    tag_font = pygame.font.Font(None, 24)
    for index, key in enumerate(games):
        category = GAME_CATEGORIES.get(key)
        if career_event_entry.get("activity_type") == CAREER_ACTIVITY_ARCADE_NIGHT and key == "prize_counter":
            label = "ARCADE SERVICE"
            color = (225, 225, 225)
        else:
            label = ("RATED • " + category.upper()) if category else "UNRATED"
            color = (255, 239, 165) if category else (225, 225, 225)
        text = tag_font.render(label, True, color)
        rect = text.get_rect(center=(start + index * (width + gap) + width // 2, label_y))
        pygame.draw.rect(game_surface, (10, 18, 25), rect.inflate(20, 6), border_radius=7)
        game_surface.blit(text, rect)


def draw_arcade_page_background(shade_alpha=72):
    background = get_event_ui_asset("assets/arcade/bg.png", (BASE_WIDTH, BASE_HEIGHT))
    if background is not None:
        game_surface.blit(background, (0, 0))
    else:
        game_surface.fill((12, 18, 28))
    shade = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
    shade.fill((0, 0, 0, max(0, min(255, int(shade_alpha)))))
    game_surface.blit(shade, (0, 0))


def draw_arcade_token_exchange():
    draw_arcade_page_background(62)

    panel = pygame.Rect(90, 58, 1186, 662)
    panel_surface = pygame.Surface(panel.size, pygame.SRCALPHA)
    panel_surface.fill((10, 17, 28, 235))
    game_surface.blit(panel_surface, panel.topleft)
    pygame.draw.rect(game_surface, (229, 197, 102), panel, 3, border_radius=16)

    title = options_title_font.render("ARCADE TOKEN EXCHANGE", True, (255, 255, 255))
    subtitle = difficulty_detail_font.render(
        "Trade Career cash for tokens. Tickets are earned by playing the machines.",
        True,
        (214, 220, 226),
    )
    game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 102)))
    game_surface.blit(subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 140)))

    status = (
        ("CASH", f"${career_cash:,}"),
        ("TOKENS", f"{int(arcade_state.get('tokens', 0)):,}"),
        ("TICKETS", f"{int(arcade_state.get('tickets', 0)):,}"),
    )
    for index, (label, value) in enumerate(status):
        rect = pygame.Rect(226 + index * 310, 166, 270, 58)
        pygame.draw.rect(game_surface, (7, 14, 24), rect, border_radius=10)
        pygame.draw.rect(game_surface, (95, 176, 205), rect, 2, border_radius=10)
        label_surface = difficulty_detail_font.render(label, True, (179, 191, 203))
        value_surface = option_label_font.render(value, True, (255, 237, 156))
        game_surface.blit(label_surface, label_surface.get_rect(midleft=(rect.x + 16, rect.centery)))
        game_surface.blit(value_surface, value_surface.get_rect(midright=(rect.right - 16, rect.centery)))

    for index, package in enumerate(ARCADE_TOKEN_PACKAGES):
        rect = arcade_token_package_rects[index]
        hovered = game_mouse_pos is not None and rect.collidepoint(game_mouse_pos)
        fill = (28, 38, 52) if not hovered else (37, 52, 68)
        pygame.draw.rect(game_surface, fill, rect, border_radius=14)
        pygame.draw.rect(
            game_surface,
            (230, 199, 108) if hovered else (119, 132, 148),
            rect,
            3 if hovered else 2,
            border_radius=14,
        )

        name = option_label_font.render(package["name"], True, (247, 248, 249))
        token_count = options_title_font.render(str(package["tokens"]), True, (255, 236, 142))
        token_label = difficulty_detail_font.render("TOKENS", True, (255, 240, 180))
        cash_label = difficulty_detail_font.render(
            f"${package['cash_cost']} CASH",
            True,
            (202, 210, 220),
        )

        game_surface.blit(name, name.get_rect(center=(rect.centerx, rect.y + 25)))
        game_surface.blit(token_count, token_count.get_rect(center=(rect.centerx, rect.y + 65)))
        game_surface.blit(token_label, token_label.get_rect(center=(rect.centerx, rect.y + 94)))
        game_surface.blit(cash_label, cash_label.get_rect(center=(rect.centerx, rect.bottom - 18)))

    if arcade_status_message and pygame.time.get_ticks() <= arcade_status_message_expires:
        info = difficulty_detail_font.render(arcade_status_message, True, (248, 242, 216))
        info_rect = info.get_rect(center=(BASE_WIDTH // 2, 619)).inflate(26, 12)
        info_panel = pygame.Surface(info_rect.size, pygame.SRCALPHA)
        info_panel.fill((5, 11, 20, 225))
        game_surface.blit(info_panel, info_rect.topleft)
        pygame.draw.rect(game_surface, (226, 194, 104), info_rect, 2, border_radius=8)
        game_surface.blit(info, info.get_rect(center=info_rect.center))

    draw_menu_button(arcade_token_exchange_back_rect, "Back", game_mouse_pos, font=option_label_font)
    if (
            arcade_pending_launch_game_id == "king_pong"
            and int(arcade_state.get("tokens", 0)) >= get_machine_cost("king_pong")
    ):
        continue_label = "Play King Pong"
    elif (
            arcade_pending_launch_game_id == "battle_bosses"
            and int(arcade_state.get("tokens", 0)) >= get_machine_cost("battle_bosses")
    ):
        continue_label = "Play Battle Bosses"
    else:
        continue_label = "Continue"
    draw_menu_button(
        arcade_token_exchange_continue_rect,
        continue_label,
        game_mouse_pos,
        font=option_label_font,
    )


def draw_arcade_prize_counter():
    draw_arcade_page_background(70)
    panel = pygame.Rect(70, 70, 1226, 620)
    pygame.draw.rect(game_surface, (16, 23, 34), panel, border_radius=18)
    pygame.draw.rect(game_surface, (226, 194, 104), panel, 3, border_radius=18)
    title = options_title_font.render("PRIZE COUNTER", True, (255, 255, 255))
    subtitle = difficulty_detail_font.render("Redeem tickets for arcade trophies. Cosmetic rewards can plug into this screen later.", True, (210, 217, 224))
    game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 118)))
    game_surface.blit(subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 152)))

    ticket_surface = option_label_font.render(f"Tickets: {int(arcade_state.get('tickets', 0)):,}", True, (255, 238, 154))
    game_surface.blit(ticket_surface, ticket_surface.get_rect(center=(BASE_WIDTH // 2, 182)))

    for index, prize in enumerate(ARCADE_PRIZE_CATALOG):
        rect = arcade_prize_card_rects[index]
        hovered = game_mouse_pos is not None and rect.collidepoint(game_mouse_pos)
        selected = index == arcade_selected_prize_index
        owned = prize['id'] in arcade_state.get('trophies', [])
        pygame.draw.rect(game_surface, (25, 34, 48) if not hovered and not selected else (34, 46, 64), rect, border_radius=14)
        pygame.draw.rect(game_surface, (220, 191, 103) if hovered or selected else (109, 121, 138), rect, 2, border_radius=14)
        name = option_label_font.render(prize['name'], True, (248, 249, 250))
        game_surface.blit(name, name.get_rect(center=(rect.centerx, rect.y + 30)))
        cost = options_title_font.render(f"{prize['cost']}", True, (255, 236, 142))
        game_surface.blit(cost, cost.get_rect(center=(rect.centerx, rect.y + 100)))
        tickets_word = difficulty_detail_font.render("TICKETS", True, (255, 240, 180))
        game_surface.blit(tickets_word, tickets_word.get_rect(center=(rect.centerx, rect.y + 134)))
        draw_wrapped_text_limited(prize['description'], difficulty_detail_font, (208, 216, 224), pygame.Rect(rect.x + 18, rect.y + 160, rect.width - 36, 60), 3, line_spacing=4)
        footer = "OWNED" if owned else "Click to select"
        footer_color = (135, 222, 173) if owned else (173, 182, 194)
        footer_surface = difficulty_detail_font.render(footer, True, footer_color)
        game_surface.blit(footer_surface, footer_surface.get_rect(center=(rect.centerx, rect.bottom - 24)))

    draw_menu_button(arcade_prize_back_rect, "Back", game_mouse_pos, font=option_label_font)
    draw_menu_button(arcade_prize_trophy_room_rect, "Trophy Room", game_mouse_pos, font=option_label_font)
    selected_prize = ARCADE_PRIZE_CATALOG[arcade_selected_prize_index]
    button_text = f"Redeem {selected_prize['cost']} Tickets"
    draw_menu_button(arcade_prize_buy_rect, button_text, game_mouse_pos, font=difficulty_detail_font)

    if arcade_status_message and pygame.time.get_ticks() <= arcade_status_message_expires:
        info = difficulty_detail_font.render(arcade_status_message, True, (246, 241, 217))
        bg = info.get_rect(center=(BASE_WIDTH // 2, 614)).inflate(28, 16)
        overlay = pygame.Surface(bg.size, pygame.SRCALPHA)
        overlay.fill((8, 14, 24, 225))
        game_surface.blit(overlay, bg.topleft)
        pygame.draw.rect(game_surface, (228, 197, 107), bg, 2, border_radius=9)
        game_surface.blit(info, info.get_rect(center=bg.center))


def draw_arcade_trophy_room():
    draw_arcade_page_background(66)
    panel = pygame.Rect(104, 92, 1158, 576)
    pygame.draw.rect(game_surface, (15, 21, 31), panel, border_radius=18)
    pygame.draw.rect(game_surface, (225, 193, 103), panel, 3, border_radius=18)
    title = options_title_font.render("ARCADE TROPHY ROOM", True, (255, 255, 255))
    subtitle = difficulty_detail_font.render("A running shelf of ticket prizes earned from Arcade Night.", True, (210, 217, 224))
    game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 132)))
    game_surface.blit(subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 166)))

    trophies = [prize for prize in ARCADE_PRIZE_CATALOG if prize['id'] in arcade_state.get('trophies', [])]
    if not trophies:
        empty = option_label_font.render("No trophies redeemed yet.", True, (232, 236, 240))
        hint = difficulty_detail_font.render("Visit the Prize Counter after stacking up some tickets.", True, (165, 175, 188))
        game_surface.blit(empty, empty.get_rect(center=(BASE_WIDTH // 2, 350)))
        game_surface.blit(hint, hint.get_rect(center=(BASE_WIDTH // 2, 388)))
    else:
        for index, prize in enumerate(trophies):
            rect = pygame.Rect(164 + (index % 3) * 330, 232 + (index // 3) * 180, 270, 132)
            pygame.draw.rect(game_surface, (29, 38, 52), rect, border_radius=14)
            pygame.draw.rect(game_surface, (222, 191, 102), rect, 2, border_radius=14)
            icon_rect = pygame.Rect(rect.x + 22, rect.y + 22, 58, 58)
            pygame.draw.ellipse(game_surface, (229, 192, 105), icon_rect)
            pygame.draw.ellipse(game_surface, (250, 243, 220), icon_rect.inflate(-18, -18))
            name = option_label_font.render(prize['name'], True, (248, 249, 250))
            cost = difficulty_detail_font.render(f"Redeemed for {prize['cost']} tickets", True, (189, 198, 208))
            game_surface.blit(name, name.get_rect(midleft=(rect.x + 96, rect.y + 42)))
            draw_wrapped_text_limited(prize['description'], difficulty_detail_font, (210, 217, 224), pygame.Rect(rect.x + 96, rect.y + 56, rect.width - 114, 46), 2, line_spacing=4)
            game_surface.blit(cost, cost.get_rect(midleft=(rect.x + 96, rect.bottom - 22)))

    draw_menu_button(arcade_trophy_room_back_rect, "Back to Prize Counter", game_mouse_pos, font=option_label_font)


def draw_king_pong_opponent_select():
    draw_arcade_page_background(62)

    panel = pygame.Rect(72, 44, 1222, 688)
    panel_surface = pygame.Surface(panel.size, pygame.SRCALPHA)
    panel_surface.fill((8, 15, 25, 238))
    game_surface.blit(panel_surface, panel.topleft)
    pygame.draw.rect(game_surface, (229, 197, 102), panel, 3, border_radius=16)

    logo = get_event_ui_asset(
        "assets/arcade/king_pong/logo.png",
        (330, 94),
    )
    if logo is not None:
        game_surface.blit(logo, logo.get_rect(center=(BASE_WIDTH // 2, 100)))
    else:
        title = options_title_font.render("KING PONG", True, (250, 249, 244))
        game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 92)))

    subtitle = difficulty_detail_font.render(
        "Choose a rival. Harder opponents move faster and pay more tickets.",
        True,
        (213, 220, 228),
    )
    game_surface.blit(subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 154)))

    wallet = difficulty_detail_font.render(
        f"TOKENS: {int(arcade_state.get('tokens', 0)):,}    |    "
        f"TICKETS: {int(arcade_state.get('tickets', 0)):,}",
        True,
        (255, 235, 145),
    )
    game_surface.blit(wallet, wallet.get_rect(center=(BASE_WIDTH // 2, 181)))

    difficulty_descriptions = {
        "low": "Slow reactions / wide tracking error",
        "medium": "Balanced arcade opponent",
        "high": "Fast reactions / accurate tracking",
        "expert": "Very fast / very small tracking error",
    }

    for index, choice in enumerate(king_pong_opponent_choices[:4]):
        rect = king_pong_opponent_rects[index]
        difficulty_id = choice.get("difficulty_id", "medium")
        config = KING_PONG_DIFFICULTIES.get(
            difficulty_id,
            KING_PONG_DIFFICULTIES["medium"],
        )
        npc = choice.get("npc") or {}
        selected = index == king_pong_selected_opponent_index
        hovered = game_mouse_pos is not None and rect.collidepoint(game_mouse_pos)

        fill = (34, 48, 64) if selected or hovered else (22, 31, 44)
        border = (255, 217, 108) if selected else ((102, 196, 225) if hovered else (111, 126, 145))
        pygame.draw.rect(game_surface, fill, rect, border_radius=14)
        pygame.draw.rect(game_surface, border, rect, 4 if selected else 2, border_radius=14)

        difficulty_surface = option_label_font.render(
            config.get("label", difficulty_id.upper()),
            True,
            (255, 234, 141),
        )
        game_surface.blit(
            difficulty_surface,
            difficulty_surface.get_rect(center=(rect.centerx, rect.y + 32)),
        )

        portrait_rect = pygame.Rect(rect.centerx - 55, rect.y + 62, 110, 110)
        pygame.draw.ellipse(game_surface, (14, 23, 34), portrait_rect)
        try:
            portrait = get_npc_portrait_surface(npc, 110)
        except Exception:
            portrait = None
        if portrait is not None:
            portrait = pygame.transform.smoothscale(portrait, portrait_rect.size)
            mask = pygame.Surface(portrait_rect.size, pygame.SRCALPHA)
            pygame.draw.ellipse(mask, (255, 255, 255, 255), mask.get_rect())
            clipped = portrait.copy()
            clipped.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            game_surface.blit(clipped, portrait_rect.topleft)
        pygame.draw.ellipse(game_surface, (229, 197, 102), portrait_rect, 3)

        npc_name = str(npc.get("name") or "Arcade Rival")
        name_surface = option_label_font.render(npc_name, True, (242, 245, 248))
        if name_surface.get_width() > rect.width - 24:
            name_surface = difficulty_detail_font.render(npc_name, True, (242, 245, 248))
        game_surface.blit(
            name_surface,
            name_surface.get_rect(center=(rect.centerx, rect.y + 198)),
        )

        multiplier = float(config.get("ticket_multiplier", 1.0))
        reward_surface = option_label_font.render(
            f"x{multiplier:.2f} TICKETS",
            True,
            (132, 222, 169) if multiplier >= 1.0 else (214, 201, 150),
        )
        game_surface.blit(
            reward_surface,
            reward_surface.get_rect(center=(rect.centerx, rect.y + 238)),
        )

        description = difficulty_detail_font.render(
            difficulty_descriptions.get(difficulty_id, "Arcade opponent"),
            True,
            (185, 195, 207),
        )
        game_surface.blit(
            description,
            description.get_rect(center=(rect.centerx, rect.y + 274)),
        )

        select_note = difficulty_detail_font.render(
            "SELECTED" if selected else "Click to select",
            True,
            (255, 231, 143) if selected else (148, 161, 176),
        )
        game_surface.blit(
            select_note,
            select_note.get_rect(center=(rect.centerx, rect.bottom - 30)),
        )

    draw_menu_button(
        king_pong_opponent_back_rect,
        "Back",
        game_mouse_pos,
        font=option_label_font,
    )
    draw_menu_button(
        king_pong_opponent_tokens_rect,
        "Buy Tokens",
        game_mouse_pos,
        font=option_label_font,
    )

    token_cost = get_machine_cost("king_pong")
    can_play = (
        get_selected_king_pong_choice() is not None
        and int(arcade_state.get("tokens", 0)) >= token_cost
    )
    draw_menu_button(
        king_pong_opponent_play_rect,
        f"Play - {token_cost} Tokens",
        game_mouse_pos if can_play else None,
        font=option_label_font,
    )
    if not can_play:
        overlay = pygame.Surface(king_pong_opponent_play_rect.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 125))
        game_surface.blit(overlay, king_pong_opponent_play_rect.topleft)

    if arcade_status_message and pygame.time.get_ticks() <= arcade_status_message_expires:
        info = difficulty_detail_font.render(
            arcade_status_message,
            True,
            (248, 242, 216),
        )
        game_surface.blit(info, info.get_rect(center=(BASE_WIDTH // 2, 620)))


def draw_battle_bosses_opponent_select():
    draw_arcade_page_background(62)

    panel = pygame.Rect(72, 42, 1222, 690)
    panel_surface = pygame.Surface(panel.size, pygame.SRCALPHA)
    panel_surface.fill((8, 15, 25, 238))
    game_surface.blit(panel_surface, panel.topleft)
    pygame.draw.rect(game_surface, (229, 197, 102), panel, 3, border_radius=16)

    logo = get_event_ui_asset(
        "assets/arcade/battle_bosses/logo.png",
        (390, 92),
    )
    if logo is not None:
        game_surface.blit(logo, logo.get_rect(center=(BASE_WIDTH // 2, 92)))
    else:
        title = options_title_font.render("BATTLE BOSSES", True, (250, 249, 244))
        game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 86)))

    subtitle = difficulty_detail_font.render(
        "Choose a three-rival squad. Harder squads move faster and pay more tickets.",
        True,
        (213, 220, 228),
    )
    game_surface.blit(subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 139)))

    wallet = difficulty_detail_font.render(
        f"TOKENS: {int(arcade_state.get('tokens', 0)):,}    |    "
        f"TICKETS: {int(arcade_state.get('tickets', 0)):,}    |    "
        f"ENTRY: {get_machine_cost('battle_bosses')} TOKENS",
        True,
        (255, 235, 145),
    )
    game_surface.blit(wallet, wallet.get_rect(center=(BASE_WIDTH // 2, 170)))

    battle_name_font = pygame.font.Font(None, 19)

    for index, choice in enumerate(battle_bosses_opponent_choices[:4]):
        rect = battle_bosses_choice_rects[index]
        difficulty_id = choice.get("difficulty_id", "standard")
        config = choice.get("config") or BATTLE_BOSSES_DIFFICULTIES.get(
            difficulty_id,
            BATTLE_BOSSES_DIFFICULTIES["standard"],
        )
        selected = index == battle_bosses_selected_choice_index
        hovered = game_mouse_pos is not None and rect.collidepoint(game_mouse_pos)

        fill = (34, 48, 64) if selected or hovered else (22, 31, 44)
        border = (255, 217, 108) if selected else ((102, 196, 225) if hovered else (111, 126, 145))
        pygame.draw.rect(game_surface, fill, rect, border_radius=14)
        pygame.draw.rect(game_surface, border, rect, 4 if selected else 2, border_radius=14)

        difficulty_surface = option_label_font.render(
            config.get("label", difficulty_id.upper()),
            True,
            (255, 234, 141),
        )
        game_surface.blit(
            difficulty_surface,
            difficulty_surface.get_rect(midleft=(rect.x + 18, rect.y + 27)),
        )

        multiplier = float(config.get("ticket_multiplier", 1.0))
        reward_surface = difficulty_detail_font.render(
            f"x{multiplier:.2f} tickets",
            True,
            (132, 222, 169) if multiplier >= 1.0 else (214, 201, 150),
        )
        game_surface.blit(
            reward_surface,
            reward_surface.get_rect(midright=(rect.right - 18, rect.y + 28)),
        )

        npcs = list(choice.get("npcs") or [])[:3]
        portrait_y = rect.y + 54
        portrait_size = 76
        portrait_gap = 28
        group_width = portrait_size * 3 + portrait_gap * 2
        group_x = rect.centerx - group_width // 2

        for npc_index, npc in enumerate(npcs):
            portrait_rect = pygame.Rect(
                group_x + npc_index * (portrait_size + portrait_gap),
                portrait_y,
                portrait_size,
                portrait_size,
            )
            pygame.draw.ellipse(game_surface, (14, 23, 34), portrait_rect)
            try:
                portrait = get_npc_portrait_surface(npc, portrait_size)
            except Exception:
                portrait = None
            if portrait is not None:
                portrait = pygame.transform.smoothscale(portrait, portrait_rect.size)
                mask = pygame.Surface(portrait_rect.size, pygame.SRCALPHA)
                pygame.draw.ellipse(mask, (255, 255, 255, 255), mask.get_rect())
                clipped = portrait.copy()
                clipped.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                game_surface.blit(clipped, portrait_rect.topleft)
            pygame.draw.ellipse(game_surface, (229, 197, 102), portrait_rect, 2)

            npc_name = str(npc.get("name") or f"Rival {npc_index + 1}")
            name_surface = battle_name_font.render(npc_name, True, (232, 236, 240))
            max_name_width = 92
            if name_surface.get_width() > max_name_width:
                scale = max_name_width / max(1, name_surface.get_width())
                name_surface = pygame.transform.smoothscale(
                    name_surface,
                    (max_name_width, max(1, int(name_surface.get_height() * scale))),
                )
            game_surface.blit(
                name_surface,
                name_surface.get_rect(center=(portrait_rect.centerx, portrait_rect.bottom + 15)),
            )

        description = difficulty_detail_font.render(
            config.get("description", "Three-rival arcade squad."),
            True,
            (185, 195, 207),
        )
        game_surface.blit(
            description,
            description.get_rect(center=(rect.centerx, rect.bottom - 20)),
        )

    draw_menu_button(
        battle_bosses_back_rect,
        "Back",
        game_mouse_pos,
        font=option_label_font,
    )
    draw_menu_button(
        battle_bosses_refresh_rect,
        "Reroll Rivals",
        game_mouse_pos,
        font=option_label_font,
    )
    battle_cost = get_machine_cost("battle_bosses")
    can_play = get_selected_battle_bosses_choice() is not None
    draw_menu_button(
        battle_bosses_future_play_rect,
        f"Play - {battle_cost} Tokens",
        game_mouse_pos if can_play else None,
        font=difficulty_detail_font,
    )
    if not can_play:
        disabled = pygame.Surface(battle_bosses_future_play_rect.size, pygame.SRCALPHA)
        disabled.fill((0, 0, 0, 125))
        game_surface.blit(disabled, battle_bosses_future_play_rect.topleft)

    if arcade_status_message and pygame.time.get_ticks() <= arcade_status_message_expires:
        info = difficulty_detail_font.render(arcade_status_message, True, (248, 242, 216))
        game_surface.blit(info, info.get_rect(center=(BASE_WIDTH // 2, 625)))


def draw_king_pong_screen():
    king_pong_game.draw(
        game_surface,
        {
            'title': options_title_font,
            'label': option_label_font,
            'detail': difficulty_detail_font,
            'small': ui_small_font,
        },
        portrait_loader=get_npc_portrait_surface,
    )
    draw_menu_button(
        king_pong_return_rect,
        "Quit",
        game_mouse_pos,
        font=option_label_font,
    )


def draw_battle_bosses_screen():
    try:
        player_portrait = get_profile_avatar()
    except Exception:
        player_portrait = None

    battle_bosses_game.draw(
        game_surface,
        {
            'title': options_title_font,
            'label': option_label_font,
            'detail': difficulty_detail_font,
            'small': ui_small_font,
        },
        portrait_loader=get_npc_portrait_surface,
        player_portrait=player_portrait,
    )
    draw_menu_button(
        battle_bosses_quit_rect,
        "Quit",
        game_mouse_pos,
        font=option_label_font,
    )


def draw_gameplay_ui():

    # ==================================================
    # MINI BUTTON LAYOUT
    # ==================================================

    show_shuffle = game.shuffle_enabled
    show_auto_solve = (
            game.can_auto_solve()
            and not game.auto_solving
    )

    mini_button_count = (
            3
            + int(show_shuffle)
            + int(show_auto_solve)
    )

    mini_button_stack_height = (
        mini_button_size
        * mini_button_count
        + mini_button_gap
        * (
            mini_button_count - 1
        )
    )

    mini_buttons_top = (
        BASE_HEIGHT
        - 10
        - mini_button_stack_height
    )

    game_menu_rect.topleft = (
        10,
        mini_buttons_top
    )

    game_hint_rect.topleft = (
        10,
        game_menu_rect.bottom
        + mini_button_gap
    )

    game_undo_rect.topleft = (
        10,
        game_hint_rect.bottom
        + mini_button_gap
    )

    game_shuffle_rect.topleft = (
        10,
        game_undo_rect.bottom
        + mini_button_gap
    )

    if show_shuffle:
        auto_solve_y = (
                game_shuffle_rect.bottom
                + mini_button_gap
        )
    else:
        auto_solve_y = (
                game_undo_rect.bottom
                + mini_button_gap
        )

    game_auto_solve_rect.topleft = (
        10,
        auto_solve_y
    )



    # --------------------------------------------------
    # Difficulty / stock status
    # --------------------------------------------------

    if game.challenge_id is not None:

        challenge_display_names = {
            "draw_3": "3 DRAW",
            "no_undo": "NO UNDO",
            "no_hints": "NO HINTS",
            "all_or_nothing": "ALL OR NOTHING",
        }

        difficulty_name = (
            challenge_display_names.get(
                game.challenge_id,
                "CHALLENGE"
            )
        )

    else:

        difficulty_display_names = {
            "easy": "EASY",
            "normal": "NORMAL",
            "hard": "HARD",
            "very_hard": "VERY HARD",
            "extreme": "IMPOSSIBLE",
        }

        difficulty_name = (
            difficulty_display_names.get(
                getattr(
                    game,
                    "difficulty",
                    "normal"
                ),
                "NORMAL"
            )
        )

    multiplier = (
        game.reward_multiplier
    )

    status_line_1 = (
        f"DIFFICULTY: {difficulty_name} (x{multiplier:.2f})"
    )

    if game.stock_pass_limit is None:
        status_line_2 = (
            "STOCK PASSES: UNLIMITED"
        )
    else:
        status_line_2 = (
            f"STOCK PASSES: {game.stock_passes_used}/{game.stock_pass_limit}"
        )

    difficulty_surface = ui_small_font.render(
        status_line_1,
        True,
        (255, 230, 0)
    )

    stock_surface = ui_small_font.render(
        status_line_2,
        True,
        (255, 230, 0)
    )

    if game.stock_pass_limit is None:
        stock_text = "STOCK: UNLIMITED"
    else:
        stock_text = (
            f"STOCK: "
            f"{game.stock_passes_used}/"
            f"{game.stock_pass_limit}"
        )

    status_text = (
        f"{difficulty_name}  "
        f"x{multiplier:.2f}     "
        f"{stock_text}"
        f"     DEAL: {game.get_deal_status_label()}"
    )



    if game.challenge_id is not None:
        challenge_display_names = {
            "draw_3":
                "3 DRAW",

            "no_undo":
                "NO UNDO",

            "no_hints":
                "NO HINTS",

            "all_or_nothing":
                "ALL OR NOTHING",
        }

        challenge_name = (
            challenge_display_names.get(
                game.challenge_id,
                game.challenge_id.upper()
            )
        )

        status_text += (
            f"     CHALLENGE: "
            f"{challenge_name}"
        )

    status_surface = ui_small_font.render(
        status_text,
        True,
        (255, 230, 0)
    )

    game_surface.blit(
        status_surface,
        (15, 12)
    )

    # --------------------------------------------------
    # Mini buttons
    # --------------------------------------------------

    mouse_pos = menu_mouse_pos

    current_hint_icon = (
        hint_button_icon
        if game.hints_enabled
        else hint_lock_icon
    )

    button_data = [
        (
            game_menu_rect,
            menu_button_icon,
            "Pause Menu",
            "View options or return to menu."
        ),
        (
            game_hint_rect,
            current_hint_icon,
            "Hint",
            get_hint_tooltip_text()
        ),
        (
            game_undo_rect,
            undo_button_icon,
            "Undo",
            get_undo_tooltip_text()
        ),
    ]

    if show_shuffle:
        button_data.append(
            (
                game_shuffle_rect,
                shuffle_button_icon,
                "Shuffle",
                "Shuffle the remaining stock and waste."
            )
        )

    if show_auto_solve:
        button_data.append(
            (
                game_auto_solve_rect,
                autosolve_button_icon,
                "Auto-Solve",
                "Automatically finish the remaining cards."
            )
        )

    hovered_rect = None
    hovered_title = ""
    hovered_subtext = ""

    for rect, icon_image, title, subtext in button_data:

        hovered = rect.collidepoint(
            mouse_pos
        )

        fill_color = (
            (70, 120, 85)
            if hovered
            else (50, 110, 75)
        )

        pygame.draw.rect(
            game_surface,
            fill_color,
            rect
        )

        pygame.draw.rect(
            game_surface,
            (255, 255, 255),
            rect,
            2
        )

        icon_rect = icon_image.get_rect(
            center=rect.center
        )

        game_surface.blit(
            icon_image,
            icon_rect
        )

        if hovered:
            hovered_rect = rect
            hovered_title = title
            hovered_subtext = subtext

    # --------------------------------------------------
    # Hover tooltip
    # --------------------------------------------------

    if hovered_rect is not None:
        tooltip_padding_x = 10
        tooltip_padding_y = 6

        title_surface = tooltip_font.render(
            hovered_title,
            True,
            (255, 255, 255)
        )

        sub_surface = tooltip_font.render(
            hovered_subtext,
            True,
            (220, 220, 220)
        )

        tooltip_width = max(
            title_surface.get_width(),
            sub_surface.get_width()
        ) + tooltip_padding_x * 2

        tooltip_height = (
            title_surface.get_height()
            + sub_surface.get_height()
            + tooltip_padding_y * 3
        )

        tooltip_rect = pygame.Rect(
            hovered_rect.right + 8,
            hovered_rect.y,
            tooltip_width,
            tooltip_height
        )

        pygame.draw.rect(
            game_surface,
            (15, 25, 15),
            tooltip_rect
        )

        pygame.draw.rect(
            game_surface,
            (255, 255, 255),
            tooltip_rect,
            2
        )

        game_surface.blit(
            title_surface,
            (
                tooltip_rect.x + tooltip_padding_x,
                tooltip_rect.y + tooltip_padding_y
            )
        )

        game_surface.blit(
            sub_surface,
            (
                tooltip_rect.x + tooltip_padding_x,
                tooltip_rect.y + tooltip_padding_y * 2 + title_surface.get_height()
            )
        )

# ==================================================
# PROFILE SELECT
# ==================================================

def draw_profile_select_screen():

    game_surface.fill(
        (
            20,
            70,
            45
        )
    )

    profile_select_title = get_event_ui_asset(
        "assets/ui/profile/select_profile_title.png",
        (360, 96)
    )
    if profile_select_title is not None:
        game_surface.blit(
            profile_select_title,
            profile_select_title.get_rect(center=(BASE_WIDTH // 2, 78))
        )
    else:
        title = options_title_font.render(
            "SELECT PROFILE",
            True,
            (255, 255, 255)
        )
        game_surface.blit(
            title,
            title.get_rect(center=(BASE_WIDTH // 2, 90))
        )



    # ----------------------------
    # Save slots
    # ----------------------------

    for index, rect in enumerate(
        profile_slot_rects
    ):
        slot = index + 1

        data = (
            get_profile_slot_display_data(
                slot
            )
        )

        hovered = rect.collidepoint(
            menu_mouse_pos
        )

        fill_color = (
            (80, 145, 100)
            if hovered
            else (50, 110, 75)
        )

        pygame.draw.rect(
            game_surface,
            fill_color,
            rect
        )

        pygame.draw.rect(
            game_surface,
            (
                255,
                255,
                255
            ),
            rect,
            2
        )

        # ------------------------
        # Slot label
        # ------------------------

        slot_surface = (
            option_value_font.render(
                f"PROFILE {slot}",
                True,
                (
                    210,
                    210,
                    210
                )
            )
        )

        game_surface.blit(
            slot_surface,
            (
                rect.x + 20,
                rect.y + 12
            )
        )

        # ------------------------
        # Name / Empty
        # ------------------------

        name_surface = (
            option_label_font.render(
                data["name"],
                True,
                (
                    255,
                    255,
                    255
                )
            )
        )

        game_surface.blit(
            name_surface,
            (
                rect.x + 20,
                rect.y + 42
            )
        )

        # ------------------------
        # Level
        # ------------------------

        if data["exists"]:
            level_surface = (
                option_value_font.render(
                    f"Level {data['level']}",
                    True,
                    (
                        255,
                        215,
                        0
                    )
                )
            )

            level_rect = (
                level_surface.get_rect(
                    right=rect.right - 20,
                    centery=rect.centery
                )
            )

            game_surface.blit(
                level_surface,
                level_rect
            )

            if data["exists"]:
                delete_rect = (
                    profile_delete_rects[
                        index
                    ]
                )

                pygame.draw.rect(
                    game_surface,
                    (
                        130,
                        45,
                        45
                    ),
                    delete_rect
                )

                pygame.draw.rect(
                    game_surface,
                    (
                        255,
                        255,
                        255
                    ),
                    delete_rect,
                    2
                )

                delete_surface = (
                    option_value_font.render(
                        "Delete",
                        True,
                        (
                            255,
                            255,
                            255
                        )
                    )
                )

                delete_surface_rect = (
                    delete_surface.get_rect(
                        center=delete_rect.center
                    )
                )

                game_surface.blit(
                    delete_surface,
                    delete_surface_rect
                )


    # ----------------------------
    # Guest
    # ----------------------------

    guest_hovered = (
        guest_profile_rect.collidepoint(
            menu_mouse_pos
        )
    )

    guest_color = (
        (80, 145, 100)
        if guest_hovered
        else (50, 110, 75)
    )

    pygame.draw.rect(
        game_surface,
        guest_color,
        guest_profile_rect
    )

    pygame.draw.rect(
        game_surface,
        (
            255,
            255,
            255
        ),
        guest_profile_rect,
        2
    )

    guest_surface = (
        option_label_font.render(
            "Guest",
            True,
            (
                255,
                255,
                255
            )
        )
    )

    guest_rect = (
        guest_surface.get_rect(
            center=guest_profile_rect.center
        )
    )

    game_surface.blit(
        guest_surface,
        guest_rect
    )

    if profile_select_return_state == STATE_CAREER_HUB:
        draw_button(career_hub_controls.profile_cancel_rect, "Back to Career",
                    font=option_value_font)

def draw_game_pause_menu():
    overlay = pygame.Surface(
        (
            BASE_WIDTH,
            BASE_HEIGHT
        ),
        pygame.SRCALPHA
    )

    overlay.fill(
        (
            0,
            0,
            0,
            150
        )
    )

    game_surface.blit(
        overlay,
        (0, 0)
    )

    panel_rect = pygame.Rect(
        443,
        210,
        480,
        405
    )

    pygame.draw.rect(
        game_surface,
        (
            35,
            85,
            60
        ),
        panel_rect
    )

    pygame.draw.rect(
        game_surface,
        (
            255,
            255,
            255
        ),
        panel_rect,
        3
    )

    title = options_title_font.render(
        "PAUSED",
        True,
        (
            255,
            255,
            255
        )
    )

    title_rect = title.get_rect(
        center=(
            panel_rect.centerx,
            260
        )
    )

    game_surface.blit(
        title,
        title_rect
    )

    draw_button(
        pause_resume_rect,
        "Resume"
    )

    draw_button(
        pause_options_rect,
        "Options"
    )

    return_label = (
        "Return to Career"
        if current_game_mode == "career"
        else "Return to Free Play"
        if current_game_mode == "free"
        else "Forfeit Race"
        if current_game_mode == "head_to_head"
        else "Return to Menu"
    )

    draw_button(
        pause_menu_rect,
        return_label
    )

    if solitaire_restart_prompt.allowed(game, current_game_mode):
        draw_button(solitaire_restart_prompt.button, "Restart Hand")

def draw_delete_profile_confirmation():
    overlay = pygame.Surface(
        (
            BASE_WIDTH,
            BASE_HEIGHT
        ),
        pygame.SRCALPHA
    )

    overlay.fill(
        (
            0,
            0,
            0,
            160
        )
    )

    game_surface.blit(
        overlay,
        (0, 0)
    )

    panel_rect = pygame.Rect(
        430,
        270,
        505,
        230
    )

    pygame.draw.rect(
        game_surface,
        (
            35,
            85,
            60
        ),
        panel_rect
    )

    pygame.draw.rect(
        game_surface,
        (
            255,
            255,
            255
        ),
        panel_rect,
        3
    )

    prompt = option_label_font.render(
        "Delete this profile?",
        True,
        (
            255,
            255,
            255
        )
    )

    prompt_rect = prompt.get_rect(
        center=(
            panel_rect.centerx,
            325
        )
    )

    game_surface.blit(
        prompt,
        prompt_rect
    )

    warning = option_value_font.render(
        "This cannot be undone.",
        True,
        (
            255,
            215,
            0
        )
    )

    warning_rect = warning.get_rect(
        center=(
            panel_rect.centerx,
            365
        )
    )

    game_surface.blit(
        warning,
        warning_rect
    )

    draw_button(
        confirm_delete_yes_rect,
        "Delete"
    )

    draw_button(
        confirm_delete_no_rect,
        "Cancel"
    )

def draw_return_confirmation():
    overlay = pygame.Surface(
        (
            BASE_WIDTH,
            BASE_HEIGHT
        ),
        pygame.SRCALPHA
    )

    overlay.fill(
        (
            0,
            0,
            0,
            150
        )
    )

    game_surface.blit(
        overlay,
        (0, 0)
    )

    panel_rect = pygame.Rect(
        430,
        270,
        505,
        220
    )

    pygame.draw.rect(
        game_surface,
        (
            35,
            85,
            60
        ),
        panel_rect
    )

    pygame.draw.rect(
        game_surface,
        (
            255,
            255,
            255
        ),
        panel_rect,
        3
    )

    return_target_name = (
        "Career Hub"
        if current_game_mode == "career"
        else "Free Play"
        if current_game_mode == "free"
        else "Career Hub"
        if current_game_mode == "head_to_head"
        else "main menu"
    )

    return_prompt = (
        "Forfeit this race and return to Career Hub?"
        if current_game_mode == "head_to_head"
        else f"Return to {return_target_name}?"
    )

    prompt = option_label_font.render(
        return_prompt,
        True,
        (
            255,
            255,
            255
        )
    )

    prompt_rect = prompt.get_rect(
        center=(
            panel_rect.centerx,
            325
        )
    )

    game_surface.blit(
        prompt,
        prompt_rect
    )

    draw_button(
        confirm_yes_rect,
        "Yes"
    )

    draw_button(
        confirm_no_rect,
        "No"
    )

# ==================================================
# DIFFICULTY SELECT
# ==================================================

def draw_difficulty_screen():

    game_surface.fill(
        (
            20,
            70,
            45
        )
    )

    title = options_title_font.render(
        "SELECT DIFFICULTY",
        True,
        (
            255,
            255,
            255
        )
    )

    title_rect = title.get_rect(
        center=(
            BASE_WIDTH // 2,
            90
        )
    )

    game_surface.blit(
        title,
        title_rect
    )

    difficulty_buttons = [
        (
            difficulty_easy_rect,
            "Easy",
            "0.70x rewards",
            "Unlimited stock  |  Unlimited hints  |  Unlimited undo  |  Shuffling"
        ),

        (
            difficulty_normal_rect,
            "Normal",
            "1.00x rewards",
            "Unlimited stock  |  Unlimited hints  |  Unlimited undo"
        ),

        (
            difficulty_hard_rect,
            "Hard",
            "1.25x rewards",
            "10 stock passes  |  15 hints  |  Unlimited undo"
        ),

        (
            difficulty_very_hard_rect,
            "Very Hard",
            "1.50x rewards",
            "8 stock passes  |  No hints  |  20-move undo history"
        ),

        (
            difficulty_extreme_rect,
            "Impossible",
            "1.85x rewards",
            "3 stock passes  |  No hints  |  5-move undo history"
        ),
    ]

    for (
            rect,
            name,
            reward_text,
            description
    ) in difficulty_buttons:
        hovered = rect.collidepoint(
            menu_mouse_pos
        )

        fill_color = (
            (80, 145, 100)
            if hovered
            else (50, 110, 75)
        )

        pygame.draw.rect(
            game_surface,
            fill_color,
            rect
        )

        pygame.draw.rect(
            game_surface,
            (
                255,
                255,
                255
            ),
            rect,
            2
        )

        # ------------------------
        # Difficulty name
        # ------------------------

        name_surface = option_label_font.render(
            name,
            True,
            (
                255,
                255,
                255
            )
        )

        game_surface.blit(
            name_surface,
            (
                rect.x + 20,
                rect.y + 10
            )
        )

        # ------------------------
        # Reward multiplier
        # ------------------------

        reward_surface = (
            option_value_font.render(
                reward_text,
                True,
                (
                    255,
                    215,
                    0
                )
            )
        )

        reward_rect = (
            reward_surface.get_rect(
                right=rect.right - 20,
                centery=rect.y + 25
            )
        )

        game_surface.blit(
            reward_surface,
            reward_rect
        )

        # ------------------------
        # Rules
        # ------------------------

        description_surface = (
            difficulty_detail_font.render(
                description,
                True,
                (
                    210,
                    210,
                    210
                )
            )
        )

        game_surface.blit(
            description_surface,
            (
                rect.x + 20,
                rect.y + 49
            )
        )

    draw_button(
        difficulty_back_rect,
        "Back"
    )


# ==================================================
# SPLASH SCREEN
# ==================================================

def draw_splash_screen():
    current_time = pygame.time.get_ticks()

    elapsed_ms = (
        current_time
        - splash_start_time
    )

    elapsed_seconds = (
        elapsed_ms / 1000.0
    )

    if modern_splash_background is not None:
        game_surface.blit(modern_splash_background, (0, 0))

        vignette = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        vignette.fill((0, 0, 0, 34))
        game_surface.blit(vignette, (0, 0))

        if modern_splash_logo is not None:
            source_w, source_h = modern_splash_logo.get_size()
            target_w = 690
            target_h = max(1, int(target_w * source_h / max(1, source_w)))
            logo = pygame.transform.smoothscale(
                modern_splash_logo,
                (target_w, target_h)
            )
            float_y = int(math.sin(elapsed_seconds * 0.8) * 3)
            logo_rect = logo.get_rect(
                center=(BASE_WIDTH // 2, 300 + float_y)
            )
            game_surface.blit(logo, logo_rect)
        else:
            logo_text = options_title_font.render(
                "SOLITAIRE+",
                True,
                (240, 238, 226)
            )
            game_surface.blit(
                logo_text,
                logo_text.get_rect(center=(BASE_WIDTH // 2, 305))
            )

        pulse = (math.sin(elapsed_seconds * 2.8) + 1.0) / 2.0
        prompt_alpha = int(115 + pulse * 120)
        prompt = option_label_font.render(
            "CLICK OR PRESS ANY KEY",
            True,
            (232, 226, 205)
        )
        prompt.set_alpha(prompt_alpha)
        game_surface.blit(
            prompt,
            prompt.get_rect(center=(BASE_WIDTH // 2, 610))
        )

        version = difficulty_detail_font.render(
            BUILD_VERSION,
            True,
            (145, 150, 146)
        )
        game_surface.blit(version, (24, BASE_HEIGHT - 34))
        return

    # Original splash fallback
    # Background
    game_surface.blit(
        splash_background,
        (0, 0)
    )

    # ----------------------------
    # Bobbing suits
    # ----------------------------

    bob_amount = 10
    bob_speed = 1.5

    spade_bob = int(
        math.sin(
            elapsed_seconds
            * bob_speed
        )
        * bob_amount
    )

    diamond_bob = int(
        math.sin(
            elapsed_seconds
            * bob_speed
            + 0.7
        )
        * bob_amount
    )

    club_bob = int(
        math.sin(
            elapsed_seconds
            * bob_speed
            + 1.4
        )
        * bob_amount
    )

    heart_bob = int(
        math.sin(
            elapsed_seconds
            * bob_speed
            + 2.1
        )
        * bob_amount
    )

    game_surface.blit(
        splash_spade,
        (0, spade_bob)
    )

    game_surface.blit(
        splash_diamond,
        (0, diamond_bob)
    )

    game_surface.blit(
        splash_club,
        (0, club_bob)
    )

    game_surface.blit(
        splash_heart,
        (0, heart_bob)
    )

    # ----------------------------
    # Pulsing prompt
    # ----------------------------

    flash_speed = 4.0

    pulse = (
        math.sin(
            elapsed_seconds
            * flash_speed
        )
        + 1
    ) / 2

    prompt_alpha = int(
        60
        + pulse * 195
    )

    prompt_surface = (
        splash_prompt.copy()
    )

    prompt_surface.set_alpha(
        prompt_alpha
    )

    game_surface.blit(
        prompt_surface,
        (0, 0)
    )

def draw_drifting_menu_background():

    background = menu_background_drift_cache.get(
        selected_menu_background, menu_background_surfaces[selected_menu_background],
        (drift_width * MENU_DRIFT_SCALE, drift_height * MENU_DRIFT_SCALE)
    )

    time_sec = (
        pygame.time.get_ticks()
        / 1000.0
    )

    # ----------------------------
    # Extremely slow drift
    # ----------------------------

    x_phase = (
        time_sec
        / MENU_DRIFT_PERIOD_X
        * math.tau
    )

    y_phase = (
        time_sec
        / MENU_DRIFT_PERIOD_Y
        * math.tau
    )

    drift_x = (
        math.sin(x_phase)
        * MENU_DRIFT_X
    )

    drift_y = (
        math.sin(
            y_phase + 1.3
        )
        * MENU_DRIFT_Y
    )

    # Convert movement into the supersampled drift space.
    # At 3x, one source-pixel step becomes one third of a
    # logical game pixel after the downsample.
    draw_x = round(
        (
            -MENU_DRIFT_MARGIN
            + drift_x
        )
        * MENU_DRIFT_SCALE
    )

    draw_y = round(
        (
            -MENU_DRIFT_MARGIN
            + drift_y
        )
        * MENU_DRIFT_SCALE
    )

    menu_drift_render_surface.blit(
        background,
        (
            draw_x,
            draw_y
        )
    )

    # Downsample only the drifting background. UI/text is
    # drawn afterward at the normal 1366x768 design size.
    pygame.transform.smoothscale(
        menu_drift_render_surface,
        (
            BASE_WIDTH,
            BASE_HEIGHT
        ),
        game_surface
    )

# ==================================================
# MAIN MENU
# ==================================================

def draw_main_menu():

    # ----------------------------
    # Drifting background
    # ----------------------------

    draw_drifting_menu_background()

    # ----------------------------
    # Floating logo
    # ----------------------------

    time_sec = pygame.time.get_ticks() / 1000.0

    bob_y = int(
        math.sin(time_sec * 1.7) * 10
    )

    game_surface.blit(
        floating_logo,
        (70, 690 + bob_y)
    )

    # ----------------------------
    # Title image
    # ----------------------------

    title_image = title_surfaces[
        selected_title
    ]

    game_surface.blit(
        title_image,
        (0, 0)
    )

    # ----------------------------
    # Buttons
    # ----------------------------

    draw_menu_button(
        new_game_rect,
        "Play",
        menu_mouse_pos
    )

    draw_menu_button(
        profile_rect,
        "Profile",
        menu_mouse_pos
    )

    draw_menu_button(
        customize_rect,
        "Customize",
        menu_mouse_pos
    )

    draw_menu_button(
        achievements_rect,
        "Achievements",
        menu_mouse_pos
    )

    draw_menu_button(
        how_to_play_rect,
        "Help",
        menu_mouse_pos
    )

    draw_menu_button(
        options_rect,
        "Options",
        menu_mouse_pos
    )

    draw_menu_button(
        quit_rect,
        "Quit",
        menu_mouse_pos
    )

    draw_menu_button(multiplayer_rect, "Launch Multiplayer", menu_mouse_pos)
    if multiplayer_launcher.error:
        message = ui_small_font.render(multiplayer_launcher.error, True, (255, 180, 140))
        game_surface.blit(message, message.get_rect(center=(BASE_WIDTH // 2, 735)))

    build_surface = ui_small_font.render(
        BUILD_VERSION,
        True,
        (
            120,
            120,
            120
        )
    )

    game_surface.blit(
        build_surface,
        (
            10,
            BASE_HEIGHT - 28
        )
    )


# ==================================================
# OPTIONS MENU
# ==================================================

def draw_options_menu():

    draw_submenu_background(
        overlay_alpha=135
    )

    draw_submenu_title(
        "OPTIONS",
        y=60,
        width=390
    )

    # ----------------------------
    # Music
    # ----------------------------

    label = option_label_font.render(
        "Music",
        True,
        (
            255,
            255,
            255
        )
    )

    game_surface.blit(
        label,
        (
            250,
            190
        )
    )

    draw_menu_button(
        music_instrumental_rect,
        "Instrumental",
        game_mouse_pos,
        selected=(
                audio.music_mode
                == "instrumental"
        ),
        font=option_value_font
    )

    draw_menu_button(
        music_ambient_rect,
        "Ambient",
        game_mouse_pos,
        selected=(
                audio.music_mode
                == "ambient"
        ),
        font=option_value_font
    )

    draw_menu_button(
        music_off_rect,
        "Off",
        game_mouse_pos,
        selected=(
                audio.music_mode
                == "off"
        ),
        font=option_value_font
    )

    # ----------------------------
    # Music volume
    # ----------------------------

    label = option_label_font.render(
        "Music Volume",
        True,
        (
            255,
            255,
            255
        )
    )

    game_surface.blit(
        label,
        (
            250,
            280
        )
    )

    pygame.draw.rect(
        game_surface,
        (
            100,
            100,
            100
        ),
        music_slider_rect
    )

    music_fill_width = int(
        music_slider_rect.width
        * audio.music_volume
    )

    pygame.draw.rect(
        game_surface,
        (
            255,
            255,
            255
        ),
        (
            music_slider_rect.x,
            music_slider_rect.y,
            music_fill_width,
            music_slider_rect.height
        )
    )

    music_knob_x = (
            music_slider_rect.x
            + music_fill_width
    )

    pygame.draw.circle(
        game_surface,
        (
            255,
            255,
            255
        ),
        (
            music_knob_x,
            music_slider_rect.centery
        ),
        12
    )

    pygame.draw.circle(
        game_surface,
        (
            40,
            40,
            40
        ),
        (
            music_knob_x,
            music_slider_rect.centery
        ),
        12,
        2
    )

    percent = option_value_font.render(
        f"{int(audio.music_volume * 100)}%",
        True,
        (
            255,
            255,
            255
        )
    )

    game_surface.blit(
        percent,
        (
            930,
            music_slider_rect.y - 5
        )
    )

    # ----------------------------
    # SFX volume
    # ----------------------------

    label = option_label_font.render(
        "Sound Effects",
        True,
        (
            255,
            255,
            255
        )
    )

    game_surface.blit(
        label,
        (
            250,
            380
        )
    )

    pygame.draw.rect(
        game_surface,
        (
            100,
            100,
            100
        ),
        sfx_slider_rect
    )

    sfx_fill_width = int(
        sfx_slider_rect.width
        * audio.sfx_volume
    )

    pygame.draw.rect(
        game_surface,
        (
            255,
            255,
            255
        ),
        (
            sfx_slider_rect.x,
            sfx_slider_rect.y,
            sfx_fill_width,
            sfx_slider_rect.height
        )
    )

    sfx_knob_x = (
            sfx_slider_rect.x
            + sfx_fill_width
    )

    pygame.draw.circle(
        game_surface,
        (
            255,
            255,
            255
        ),
        (
            sfx_knob_x,
            sfx_slider_rect.centery
        ),
        12
    )

    pygame.draw.circle(
        game_surface,
        (
            40,
            40,
            40
        ),
        (
            sfx_knob_x,
            sfx_slider_rect.centery
        ),
        12,
        2
    )

    percent = option_value_font.render(
        f"{int(audio.sfx_volume * 100)}%",
        True,
        (
            255,
            255,
            255
        )
    )

    game_surface.blit(
        percent,
        (
            930,
            sfx_slider_rect.y - 5
        )
    )

    # ----------------------------
    # Double-click mode
    # ----------------------------

    label = option_label_font.render(
        "Double Click",
        True,
        (
            255,
            255,
            255
        )
    )

    game_surface.blit(
        label,
        (
            250,
            490
        )
    )

    draw_menu_button(
        double_foundation_rect,
        "Foundation Only",
        game_mouse_pos,
        selected=(
                game.double_click_mode
                == "foundation"
        ),
        font=option_value_font
    )

    draw_menu_button(
        double_both_rect,
        "Foundation + Tableau",
        game_mouse_pos,
        selected=(
                game.double_click_mode
                == "foundation_and_tableau"
        ),
        font=option_value_font
    )

    # ----------------------------
    # Solitaire deal mode
    # ----------------------------

    label = option_label_font.render(
        "New Deals",
        True,
        (
            255,
            255,
            255
        )
    )

    game_surface.blit(
        label,
        (
            250,
            550
        )
    )

    draw_menu_button(
        deal_random_rect,
        "Random",
        game_mouse_pos,
        selected=(
                game.deal_mode
                == "random"
        ),
        font=option_value_font
    )

    if VERIFIED_DEALS_ENABLED:
        draw_menu_button(
            deal_verified_rect,
            "Verified Solvable",
            game_mouse_pos,
            selected=(game.deal_mode == "verified"),
            font=option_value_font
        )
    else:
        pygame.draw.rect(
            game_surface,
            (72, 76, 74),
            deal_verified_rect,
            border_radius=8,
        )
        pygame.draw.rect(
            game_surface,
            (115, 120, 118),
            deal_verified_rect,
            2,
            border_radius=8,
        )
        disabled_label = option_value_font.render(
            "Verified Solvable",
            True,
            (155, 158, 156),
        )
        game_surface.blit(
            disabled_label,
            disabled_label.get_rect(center=deal_verified_rect.center),
        )

        if (
                game_mouse_pos is not None
                and deal_verified_rect.collidepoint(game_mouse_pos)
        ):
            tooltip_rect = pygame.Rect(600, 492, 455, 38)
            pygame.draw.rect(
                game_surface,
                (22, 26, 24),
                tooltip_rect,
                border_radius=7,
            )
            pygame.draw.rect(
                game_surface,
                (205, 178, 90),
                tooltip_rect,
                2,
                border_radius=7,
            )
            tooltip = difficulty_detail_font.render(
                "Temporarily disabled while the deal generator is rebuilt.",
                True,
                (240, 235, 218),
            )
            game_surface.blit(
                tooltip,
                tooltip.get_rect(center=tooltip_rect.center),
            )

    # ----------------------------
    # Window size
    # ----------------------------

    label = option_label_font.render(
        "Window Size",
        True,
        (
            255,
            255,
            255
        )
    )

    game_surface.blit(
        label,
        (
            250,
            608
        )
    )

    for index, resolution in enumerate(
        RESOLUTION_OPTIONS
    ):
        width, height = resolution

        selected = (
            WINDOWED_WIDTH == width
            and WINDOWED_HEIGHT == height
        )

        text = (
            f"{width}x{height}"
        )

        draw_menu_button(
            resolution_rects[index],
            text,
            game_mouse_pos,
            selected=selected,
            font=option_value_font
        )

    # ----------------------------
    # Fullscreen
    # ----------------------------

    label = option_label_font.render(
        "Fullscreen",
        True,
        (
            255,
            255,
            255
        )
    )

    game_surface.blit(
        label,
        (
            250,
            654
        )
    )

    draw_menu_button(
        fullscreen_toggle_rect,
        "On" if fullscreen_enabled else "Off",
        game_mouse_pos,
        selected=fullscreen_enabled,
        font=option_value_font
    )

    # ----------------------------
    # Back
    # ----------------------------

    draw_menu_button(
        options_back_rect,
        "Return",
        game_mouse_pos,
        font=difficulty_detail_font
    )

menu_mouse_pos = (
    0,
    0
)

# ==================================================
# CUSTOMIZATION MENU
# ==================================================

def draw_customize_menu():
    draw_submenu_background(
        overlay_alpha=115
    )

    # ----------------------------
    # Title
    # ----------------------------

    title = options_title_font.render(
        "CUSTOMIZE",
        True,
        (
            255,
            255,
            255
        )
    )

    title_rect = title.get_rect(
        center=(
            BASE_WIDTH // 2,
            65
        )
    )

    game_surface.blit(
        title,
        title_rect
    )

    # ----------------------------
    # Category tabs
    # ----------------------------

    draw_menu_button(
        customize_backgrounds_rect,
        "Backgrounds",
        game_mouse_pos,
        selected=(
                customize_category
                == CUSTOMIZE_BACKGROUNDS
        ),
        font=difficulty_detail_font
    )

    draw_menu_button(
        customize_felts_rect,
        "Felts",
        game_mouse_pos,
        selected=(
                customize_category
                == CUSTOMIZE_FELTS
        ),
        font=difficulty_detail_font
    )

    draw_menu_button(
        customize_titles_rect,
        "Titles",
        game_mouse_pos,
        selected=(
                customize_category
                == CUSTOMIZE_TITLES
        ),
        font=difficulty_detail_font
    )

    draw_menu_button(
        customize_cursors_rect,
        "Cursors",
        game_mouse_pos,
        selected=(
                customize_category
                == CUSTOMIZE_CURSORS
        ),
        font=difficulty_detail_font
    )

    # ----------------------------
    # Player progression
    # ----------------------------

    level_text = option_value_font.render(
        f"Level {player_level}",
        True,
        (
            255,
            255,
            255
        )
    )

    game_surface.blit(
        level_text,
        (
            1050,
            40
        )
    )

    if player_xp_to_next is not None:
        xp_text_string = (
            f"XP {player_xp} / "
            f"{player_xp_to_next}"
        )
    else:
        xp_text_string = (
            f"XP {player_xp} / MAX"
        )

    xp_text = option_value_font.render(
        xp_text_string,
        True,
        (
            255,
            255,
            255
        )
    )

    game_surface.blit(
        xp_text,
        (
            1050,
            70
        )
    )

    # ----------------------------
    # Current category data
    # ----------------------------

    (
        asset_data,
        surface_data,
        unlocked_ids,
        selected_id
    ) = get_customize_data()

    asset_ids = get_customize_asset_ids()

    start_index = (
        customize_page
        * CUSTOMIZE_ITEMS_PER_PAGE
    )

    end_index = (
        start_index
        + CUSTOMIZE_ITEMS_PER_PAGE
    )

    visible_ids = asset_ids[
        start_index:end_index
    ]

    # ----------------------------
    # Item cards
    # ----------------------------

    for index, rect in enumerate(
        customize_item_rects
    ):
        pygame.draw.rect(
            game_surface,
            (
                35,
                85,
                60
            ),
            rect
        )

        pygame.draw.rect(
            game_surface,
            (
                180,
                180,
                180
            ),
            rect,
            2
        )

        if index >= len(
            visible_ids
        ):
            continue

        asset_id = visible_ids[index]

        data = asset_data[
            asset_id
        ]

        display_name = data[
            "name"
        ]

        unlocked = (
            asset_id
            in unlocked_ids
        )

        selected = (
            asset_id
            == selected_id
        )

        # ------------------------
        # Selected outline
        # ------------------------

        if selected:
            pygame.draw.rect(
                game_surface,
                (
                    255,
                    215,
                    0
                ),
                rect,
                5
            )

        # ------------------------
        # Unlocked preview
        # ------------------------

        if unlocked and cosmetic_art_available(asset_id):
            source_surface = (
                surface_data[
                    asset_id
                ]
            )

            if customize_category == CUSTOMIZE_CURSORS:
                preview = source_surface
            else:
                preview = (
                    scale_surface_to_fit(
                        source_surface,
                        rect.width - 30,
                        rect.height - 60
                    )
                )

            preview_rect = (
                preview.get_rect(
                    center=(
                        rect.centerx,
                        rect.centery - 12
                    )
                )
            )

            game_surface.blit(
                preview,
                preview_rect
            )

        # ------------------------
        # Locked placeholder
        # ------------------------

        else:
            lock_rect = pygame.Rect(
                rect.x + 20,
                rect.y + 20,
                rect.width - 40,
                rect.height - 70
            )

            pygame.draw.rect(
                game_surface,
                (
                    75,
                    75,
                    75
                ),
                lock_rect
            )

            locked_text = (
                option_value_font.render(
                    "ARTWORK UNAVAILABLE" if unlocked else "LOCKED",
                    True,
                    (
                        160,
                        160,
                        160
                    )
                )
            )

            locked_rect = (
                locked_text.get_rect(
                    center=lock_rect.center
                )
            )

            game_surface.blit(
                locked_text,
                locked_rect
            )
            kind = {CUSTOMIZE_BACKGROUNDS: "backgrounds", CUSTOMIZE_FELTS: "felts", CUSTOMIZE_TITLES: "titles"}.get(customize_category, "cursors")
            requirement = os.path.basename(data.get("path", "")) if unlocked else lock_reason(asset_id, data, kind, LEVEL_UNLOCKS, ACHIEVEMENT_DEFINITIONS)
            reason_font = pygame.font.Font(None, 23)
            words, rows = requirement.split(), [""]
            for word in words:
                trial = (rows[-1] + " " + word).strip()
                if reason_font.size(trial)[0] > lock_rect.width - 16:
                    rows.append(word)
                else:
                    rows[-1] = trial
            progress_text = "Add or re-save this PNG" if unlocked else rating_lock_progress(data, career_ratings)
            if progress_text:
                rows.append(progress_text)
            # Centre the full lock explanation inside its preview area.
            locked_rect.centery = lock_rect.centery - max(0, len(rows)-1)*11
            pygame.draw.rect(game_surface, (75, 75, 75), lock_rect)
            game_surface.blit(locked_text, locked_rect)
            for row_index, row in enumerate(rows):
                label = reason_font.render(row, True, (230, 230, 230))
                game_surface.blit(label, label.get_rect(midtop=(lock_rect.centerx, locked_rect.bottom + 8 + 22 * row_index)))


        # ------------------------
        # Name
        # ------------------------

        name_surface = (
            option_value_font.render(
                display_name,
                True,
                (
                    255,
                    255,
                    255
                )
                if unlocked
                else (
                    130,
                    130,
                    130
                )
            )
        )

        name_rect = (
            name_surface.get_rect(
                center=(
                    rect.centerx,
                    rect.bottom - 22
                )
            )
        )

        game_surface.blit(
            name_surface,
            name_rect
        )

    # ----------------------------
    # Page controls
    # ----------------------------

    page_count = (
        get_customize_page_count()
    )

    draw_menu_button(
        customize_prev_rect,
        "Previous",
        game_mouse_pos,
        font=difficulty_detail_font
    )

    draw_menu_button(
        customize_next_rect,
        "Next",
        game_mouse_pos,
        font=difficulty_detail_font
    )

    draw_menu_button(
        customize_back_rect,
        "Return",
        game_mouse_pos,
        font=difficulty_detail_font
    )

    page_text = (
        option_value_font.render(
            (
                f"Page "
                f"{customize_page + 1}"
                f" / {page_count}"
            ),
            True,
            (
                255,
                255,
                255
            )
        )
    )

    page_rect = (
        page_text.get_rect(
            center=(
                BASE_WIDTH // 2,
                645
            )
        )
    )

    game_surface.blit(
        page_text,
        page_rect
    )

    draw_button(
        debug_xp_rect,
        "DEBUG +100 XP"
    )

def draw_profile_screen():
    draw_submenu_background(
        overlay_alpha=125
    )

    profile_title_text = (
        "CREATE PROFILE"
        if profile_creation_mode
        else "PROFILE"
    )

    title = pygame.font.SysFont(
        "cambria",
        44,
        bold=True
    ).render(
        profile_title_text,
        True,
        (255, 255, 255)
    )
    game_surface.blit(
        title,
        title.get_rect(center=(BASE_WIDTH // 2, 58))
    )

    if guest_mode:
        slot_text = "Guest"
    elif current_profile_slot is not None:
        slot_text = f"Profile Slot {current_profile_slot}"
    else:
        slot_text = "New Profile"

    slot_surface = option_value_font.render(
        slot_text,
        True,
        (255, 220, 110)
    )
    game_surface.blit(
        slot_surface,
        slot_surface.get_rect(center=(BASE_WIDTH // 2, 105))
    )

    # ==================================================
    # Avatar preview
    # ==================================================

    pygame.draw.rect(
        game_surface,
        (24, 58, 43),
        profile_avatar_frame_rect,
        border_radius=12
    )
    pygame.draw.rect(
        game_surface,
        (230, 236, 232),
        profile_avatar_frame_rect,
        3,
        border_radius=12
    )

    avatar = get_profile_avatar()
    max_avatar_rect = profile_avatar_frame_rect.inflate(-18, -18)
    src_w, src_h = avatar.get_size()
    avatar_scale = min(
        max_avatar_rect.width / max(1, src_w),
        max_avatar_rect.height / max(1, src_h)
    )
    avatar_size = (
        max(1, int(src_w * avatar_scale)),
        max(1, int(src_h * avatar_scale))
    )
    avatar_preview = pygame.transform.smoothscale(
        avatar,
        avatar_size
    )
    game_surface.blit(
        avatar_preview,
        avatar_preview.get_rect(center=profile_avatar_frame_rect.center)
    )

    level_text = f"Level {player_level}"
    xp_text = f"XP {player_xp:,}"
    if player_xp_to_next is not None:
        xp_text += f" / {player_xp_to_next:,}"

    for index, text in enumerate((level_text, xp_text)):
        surface = option_value_font.render(
            text,
            True,
            (240, 240, 240)
        )
        game_surface.blit(
            surface,
            surface.get_rect(center=(profile_avatar_frame_rect.centerx, 555 + index * 31))
        )

    # ==================================================
    # Field helpers
    # ==================================================

    def draw_field(label, rect, value, active=False, placeholder=""):
        label_surface = difficulty_detail_font.render(
            label,
            True,
            (236, 236, 236)
        )
        game_surface.blit(
            label_surface,
            (rect.x, rect.y - 27)
        )

        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((18, 52, 38, 220))
        game_surface.blit(panel, rect.topleft)

        pygame.draw.rect(
            game_surface,
            (255, 215, 85) if active else (225, 232, 228),
            rect,
            3 if active else 2,
            border_radius=6
        )

        shown = value if value else placeholder
        color = (255, 255, 255) if value else (155, 172, 165)
        text_surface = render_text_fit(
            shown,
            option_value_font,
            rect.width - 26,
            color,
            minimum_size=15
        )
        game_surface.blit(
            text_surface,
            (rect.x + 13, rect.centery - text_surface.get_height() // 2)
        )

    def draw_dropdown_field(label, rect, value, open_state, placeholder):
        label_surface = difficulty_detail_font.render(
            label,
            True,
            (236, 236, 236)
        )
        game_surface.blit(label_surface, (rect.x, rect.y - 27))

        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((18, 52, 38, 220))
        game_surface.blit(panel, rect.topleft)
        pygame.draw.rect(
            game_surface,
            (255, 215, 85) if open_state else (225, 232, 228),
            rect,
            3 if open_state else 2,
            border_radius=6
        )

        shown = value if value else placeholder
        color = (255, 255, 255) if value else (155, 172, 165)
        text_surface = option_value_font.render(shown, True, color)
        game_surface.blit(
            text_surface,
            (rect.x + 13, rect.centery - text_surface.get_height() // 2)
        )
        arrow = difficulty_detail_font.render("v", True, (230, 230, 230))
        game_surface.blit(
            arrow,
            arrow.get_rect(center=(rect.right - 22, rect.centery))
        )

    draw_field(
        "Name",
        profile_name_rect,
        profile_name_text,
        profile_name_active,
        "Player name"
    )
    draw_field(
        "Country",
        profile_country_rect,
        profile_country_text,
        profile_country_active,
        "e.g. USA"
    )
    country_hint = leaderboard_tiny_font.render(
        "3-letter code",
        True,
        (185, 195, 190)
    )
    game_surface.blit(
        country_hint,
        (profile_country_rect.x, profile_country_rect.bottom + 3)
    )

    draw_field(
        "Age",
        profile_age_rect,
        profile_age_text,
        profile_age_active,
        "Age"
    )

    draw_dropdown_field(
        "Gender",
        profile_gender_rect,
        profile_gender.title(),
        gender_dropdown_open,
        "Choose"
    )
    draw_dropdown_field(
        "Favorite Suit",
        profile_favorite_suit_rect,
        profile_favorite_suit,
        favorite_suit_dropdown_open,
        "Choose a suit"
    )

    draw_field(
        "Hometown",
        profile_hometown_rect,
        profile_hometown_text,
        profile_hometown_active,
        "City, region / country"
    )

    bio_label = difficulty_detail_font.render(
        "Short Bio",
        True,
        (236, 236, 236)
    )
    game_surface.blit(
        bio_label,
        (profile_bio_rect.x, profile_bio_rect.y - 27)
    )
    bio_panel = pygame.Surface(profile_bio_rect.size, pygame.SRCALPHA)
    bio_panel.fill((18, 52, 38, 220))
    game_surface.blit(bio_panel, profile_bio_rect.topleft)
    pygame.draw.rect(
        game_surface,
        (255, 215, 85) if profile_bio_active else (225, 232, 228),
        profile_bio_rect,
        3 if profile_bio_active else 2,
        border_radius=6
    )

    bio_text = profile_bio_text if profile_bio_text else "A short leaderboard bio..."
    bio_color = (255, 255, 255) if profile_bio_text else (155, 172, 165)
    draw_wrapped_text_limited(
        bio_text,
        difficulty_detail_font,
        bio_color,
        profile_bio_rect.inflate(-22, -18),
        max_lines=4,
        line_spacing=3
    )
    counter_surface = leaderboard_tiny_font.render(
        f"{len(profile_bio_text)}/180",
        True,
        (170, 185, 178)
    )
    game_surface.blit(
        counter_surface,
        counter_surface.get_rect(bottomright=(profile_bio_rect.right - 8, profile_bio_rect.bottom - 5))
    )

    # ==================================================
    # Avatar customization panel
    # ==================================================

    avatar_panel = pygame.Rect(1110, 155, 220, 350)
    avatar_panel_surface = pygame.Surface(avatar_panel.size, pygame.SRCALPHA)
    avatar_panel_surface.fill((16, 40, 31, 200))
    game_surface.blit(avatar_panel_surface, avatar_panel.topleft)
    pygame.draw.rect(
        game_surface,
        (210, 220, 214),
        avatar_panel,
        2,
        border_radius=10
    )

    customize_title = difficulty_detail_font.render(
        "AVATAR",
        True,
        (255, 220, 110)
    )
    game_surface.blit(
        customize_title,
        customize_title.get_rect(center=(avatar_panel.centerx, 177))
    )

    avatar_selector_rows = [
        ("Base", selected_avatar_base, avatar_base_options),
        ("Eyes", selected_avatar_eyes, avatar_eye_options),
        ("Hair", selected_avatar_hair, avatar_hair_options),
        ("Glasses", selected_avatar_glasses, avatar_glasses_options),
        ("Top", selected_avatar_top, avatar_top_options),
    ]

    for index, (label_text, current_value, options) in enumerate(avatar_selector_rows):
        y = avatar_selector_start_y + index * avatar_selector_gap
        label_surface = difficulty_detail_font.render(
            label_text,
            True,
            (235, 235, 235)
        )
        game_surface.blit(
            label_surface,
            (1118, y + 8)
        )

        draw_button(avatar_selector_left_rects[index], "<")
        draw_button(avatar_selector_right_rects[index], ">")

        if current_value is None:
            display_text = "None"
        else:
            current_index = options.index(current_value)
            display_text = f"{current_index + 1}/{len(options)}"

        value_surface = difficulty_detail_font.render(
            display_text,
            True,
            (255, 220, 110)
        )
        game_surface.blit(
            value_surface,
            value_surface.get_rect(center=(1250, y + 20))
        )

    # ==================================================
    # Dropdown overlays
    # ==================================================

    if gender_dropdown_open:
        for index, gender in enumerate(gender_options):
            rect = profile_gender_option_rects[index]
            pygame.draw.rect(game_surface, (25, 72, 50), rect)
            pygame.draw.rect(game_surface, (235, 235, 235), rect, 1)
            label = option_value_font.render(
                gender.title(),
                True,
                (255, 255, 255)
            )
            game_surface.blit(
                label,
                (rect.x + 13, rect.centery - label.get_height() // 2)
            )

    if favorite_suit_dropdown_open:
        for index, suit in enumerate(favorite_suit_options):
            rect = profile_favorite_suit_option_rects[index]
            pygame.draw.rect(game_surface, (25, 72, 50), rect)
            pygame.draw.rect(game_surface, (235, 235, 235), rect, 1)
            label = option_value_font.render(
                suit,
                True,
                (255, 255, 255)
            )
            game_surface.blit(
                label,
                (rect.x + 13, rect.centery - label.get_height() // 2)
            )

    # ==================================================
    # Buttons / status
    # ==================================================

    save_button_text = "Create Profile" if profile_creation_mode else "Save"
    draw_menu_button(
        profile_save_rect,
        save_button_text,
        game_mouse_pos,
        font=difficulty_detail_font
    )

    if not profile_creation_mode:
        draw_menu_button(
            profile_switch_rect,
            "Switch Profile",
            game_mouse_pos,
            font=difficulty_detail_font
        )

    back_button_text = "Cancel" if profile_creation_mode else "Back"
    draw_menu_button(
        profile_back_rect,
        back_button_text,
        game_mouse_pos,
        font=difficulty_detail_font
    )

    if profile_message:
        message_surface = difficulty_detail_font.render(
            profile_message,
            True,
            (255, 235, 160)
        )
        game_surface.blit(
            message_surface,
            message_surface.get_rect(center=(BASE_WIDTH // 2, 724))
        )

# ==================================================
# ROUND RECAP
# ==================================================

def draw_round_recap():
    game_surface.fill(
        (
            20,
            70,
            45
        )
    )

    if round_recap_data is None:
        return

    # ----------------------------
    # Heading
    # ----------------------------

    if (
            round_recap_data.get(
                "challenge_id"
            )
            is not None
    ):
        recap_title_text = (
            "CHALLENGE COMPLETE"
        )

    else:
        recap_title_text = (
            "ROUND COMPLETE"
        )

    title = menu_title_font.render(
        recap_title_text,
        True,
        (
            255,
            255,
            255
        )
    )

    challenge_id = round_recap_data.get(
        "challenge_id"
    )

    if challenge_id is not None:
        challenge_names = {
            "draw_3": "3 Draw",
            "no_undo": "No Undo",
            "no_hints": "No Hints",
            "all_or_nothing": "All or Nothing",
        }

        challenge_surface = (
            option_label_font.render(
                challenge_names.get(
                    challenge_id,
                    challenge_id
                ),
                True,
                (
                    255,
                    215,
                    0
                )
            )
        )

        challenge_rect = (
            challenge_surface.get_rect(
                center=(
                    BASE_WIDTH // 2,
                    150
                )
            )
        )

        game_surface.blit(
            challenge_surface,
            challenge_rect
        )

    # ----------------------------
    # Stats
    # ----------------------------

    stats = [
        (
            "Time",
            format_round_time(
                round_recap_data[
                    "elapsed_seconds"
                ]
            )
        ),
        (
            "Moves",
            str(
                round_recap_data[
                    "moves"
                ]
            )
        ),
        (
            "Move Bonus",
            f"+{round_recap_data['move_bonus']:,}"
        ),
        (
            "Time Bonus",
            f"+{round_recap_data['time_bonus']:,}"
        ),
        (
            "Score",
            f"{round_recap_data['score']:,}"
        ),
        (
            "XP Earned",
            f"+{round_recap_data['xp_earned']:,}"
        ),
        (
            "SP Earned",
            f"+{round_recap_data.get('sp_earned', 0):,}"
        ),
    ]

    if current_game_mode == "career":
        stats.append(
            (
                "Cash Earned",
                f"+${round_recap_data.get('cash_earned', 0):,}"
            )
        )

        stats.append(
            (
                "Rating",
                f"+{round_recap_data.get('rating_change', 0):,}"
            )
        )

        stats.append(
            (
                "Fans",
                f"+{round_recap_data.get('fans_earned', 0):,}"
            )
        )

    start_y = 175

    for index, (
        label_text,
        value_text

    ) in enumerate(stats):
        y = (
                start_y
                + index * 45
        )

        label = option_label_font.render(
            label_text,
            True,
            (
                210,
                210,
                210
            )
        )

        value = option_label_font.render(
            value_text,
            True,
            (
                255,
                255,
                255
            )
        )

        game_surface.blit(
            label,
            (
                450,
                y
            )
        )

        value_rect = value.get_rect(
            right=900,
            y=y
        )

        game_surface.blit(
            value,
            value_rect
        )

    # ----------------------------
    # Remark
    # ----------------------------

    remark = option_label_font.render(
        round_recap_data[
            "remark"
        ],
        True,
        (
            255,
            255,
            255
        )
    )

    remark_rect = remark.get_rect(
        center=(
            BASE_WIDTH // 2,
            585
        )
    )

    game_surface.blit(
        remark,
        remark_rect
    )

    # ----------------------------
    # Return to menu prompt
    # ----------------------------

    prompt = option_label_font.render(
        "Leave Table?",
        True,
        (
            255,
            255,
            255
        )
    )

    prompt_rect = prompt.get_rect(
        center=(
            BASE_WIDTH // 2,
            620
        )
    )

    game_surface.blit(
        prompt,
        prompt_rect
    )

    draw_button(
        recap_yes_rect,
        "Yes"
    )

    draw_button(
        recap_no_rect,
        "No"
    )

# ==================================================
# LEVEL UP SCREEN
# ==================================================

def draw_level_up_screen():
    game_surface.fill((20, 190, 20))

    if current_level_up_data is None:
        return

    level = current_level_up_data["level"]
    unlocks = list(current_level_up_data.get("unlocks", []))

    heading = menu_title_font.render(
        f"You've reached level {level}!",
        True,
        (255, 255, 255),
    )
    game_surface.blit(
        heading,
        heading.get_rect(center=(BASE_WIDTH // 2, 58)),
    )

    subheading = options_title_font.render(
        "you've unlocked:",
        True,
        (255, 255, 255),
    )
    game_surface.blit(
        subheading,
        subheading.get_rect(center=(BASE_WIDTH // 2, 120)),
    )

    if unlocks:
        count = len(unlocks)
        if count <= 2:
            columns = count
            card_width, card_height = 360, 220
        elif count == 4:
            columns = 2
            card_width, card_height = 360, 190
        else:
            columns = min(3, count)
            card_width, card_height = 300, 190

        rows = (count + columns - 1) // columns
        gap_x = 28
        gap_y = 20
        card_height = min(card_height, (430 - max(0, rows - 1) * gap_y) // rows)
        total_height = rows * card_height + max(0, rows - 1) * gap_y
        start_y = 165 + max(0, (430 - total_height) // 2)

        for index, (unlock_type, asset_id) in enumerate(unlocks):
            row = index // columns
            column = index % columns

            items_this_row = min(columns, count - row * columns)
            row_width = (
                items_this_row * card_width
                + max(0, items_this_row - 1) * gap_x
            )
            row_start_x = (BASE_WIDTH - row_width) // 2
            card_x = row_start_x + column * (card_width + gap_x)
            card_y = start_y + row * (card_height + gap_y)

            card_rect = pygame.Rect(
                card_x,
                card_y,
                card_width,
                card_height,
            )

            pygame.draw.rect(
                game_surface,
                (245, 245, 245),
                card_rect,
                border_radius=10,
            )
            pygame.draw.rect(
                game_surface,
                (50, 50, 50),
                card_rect,
                2,
                border_radius=10,
            )

            asset_data, asset_surface, category_name = get_unlock_asset_data(
                unlock_type,
                asset_id,
            )

            preview_height = min(105 if card_height >= 210 else 82, max(30, card_height - 95))
            if asset_surface is not None:
                preview = scale_surface_to_fit(
                    asset_surface,
                    card_width - 34,
                    preview_height,
                )
                preview_rect = preview.get_rect(
                    center=(
                        card_rect.centerx,
                        card_rect.y + 18 + preview_height // 2,
                    )
                )
                game_surface.blit(preview, preview_rect)

            category_font = difficulty_detail_font
            category_surface = category_font.render(
                category_name,
                True,
                (65, 65, 65),
            )
            game_surface.blit(
                category_surface,
                category_surface.get_rect(
                    center=(card_rect.centerx, card_rect.bottom - 54)
                ),
            )

            name_text = str(asset_data.get("name", asset_id))
            name_font = option_value_font
            while name_font.size(name_text)[0] > card_width - 24 and len(name_text) > 4:
                name_text = name_text[:-4].rstrip() + "..."
            name_surface = name_font.render(
                name_text,
                True,
                (0, 0, 0),
            )
            game_surface.blit(
                name_surface,
                name_surface.get_rect(
                    center=(card_rect.centerx, card_rect.bottom - 25)
                ),
            )
    else:
        no_unlock_text = option_label_font.render(
            "No cosmetic unlocks this level.",
            True,
            (255, 255, 255),
        )
        game_surface.blit(
            no_unlock_text,
            no_unlock_text.get_rect(center=(BASE_WIDTH // 2, 375)),
        )

    if player_xp_to_next is not None:
        xp_string = f"{player_name}'s XP: {player_xp:,} / {player_xp_to_next:,}"
    else:
        xp_string = f"{player_name}'s XP: {player_xp:,} / MAX"

    xp_surface = option_label_font.render(
        xp_string,
        True,
        (0, 0, 0),
    )
    game_surface.blit(
        xp_surface,
        xp_surface.get_rect(center=(BASE_WIDTH // 2, 650)),
    )

    draw_button(
        level_up_continue_rect,
        "Continue",
        font=option_value_font,
    )

# ==================================================
# MAIN LOOP // EVENT STATE CHAIN
# ==================================================

running = True


while running:

    # ----------------------------------------------
    # Events
    # ----------------------------------------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        audio.handle_event(
            event
        )

        # ==================================================
        # GLOBAL FULLSCREEN HOTKEY
        # ==================================================

        if (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_F11
        ):
            set_fullscreen_enabled(
                not fullscreen_enabled
            )
            continue

        # ==================================================
        # GLOBAL DEBUG MENU HOTKEY
        # ==================================================

        if (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_F10
        ):

            print(
                "F10 DEBUG MENU"
            )

            if current_state == STATE_DEBUG_MENU:

                if debug_previous_state is not None:
                    current_state = (
                        debug_previous_state
                    )

            else:

                debug_previous_state = (
                    current_state
                )

                current_state = (
                    STATE_DEBUG_MENU
                )

            continue

        game_mouse_pos = None

        if hasattr(
            event,
            "pos"
        ):
            game_mouse_pos = (
                window_to_game_coords(
                    event.pos
                )
            )

        if game_mouse_pos is not None:
            menu_mouse_pos = game_mouse_pos

        # ==================================================
        # DEBUG POKER NPC SELECT INPUT
        # ==================================================

        if current_state == STATE_DEBUG_POKER_NPC_SELECT:
            if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):
                selector_action = get_debug_poker_select_action(
                    game_mouse_pos,
                    can_start=(career_cash >= 100),
                )

                if selector_action is not None:
                    action_name, action_value = selector_action

                    if action_name == DEBUG_POKER_ACTION_BACK:
                        audio.play_sound("button_click")
                        current_state = STATE_DEBUG_MENU

                    elif action_name == DEBUG_POKER_ACTION_RANDOMIZE:
                        audio.play_sound("button_click")
                        debug_poker_selected_ids = make_debug_poker_default_selection(
                            NPCS,
                            count=4,
                        )

                    elif action_name == DEBUG_POKER_ACTION_CYCLE:
                        audio.play_sound("button_click")
                        slot_index, direction = action_value
                        debug_poker_selected_ids = cycle_debug_poker_selection(
                            NPCS,
                            debug_poker_selected_ids,
                            slot_index,
                            direction,
                        )

                    elif action_name == DEBUG_POKER_ACTION_START:
                        audio.play_sound("button_click")
                        if not start_debug_selected_poker_table():
                            show_debug_message("Add cash to play")

            continue

        # ==================================================
        # DEBUG MENU INPUT
        # ==================================================

        if current_state == STATE_DEBUG_MENU:

            if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):

                debug_action = (
                    get_debug_action(
                        game_mouse_pos
                    )
                )

                # ==========================================
                # Career / event navigation
                # ==========================================

                if debug_action == ACTION_CAREER_HUB:
                    audio.play_sound("button_click")
                    current_state = STATE_CAREER_HUB

                elif debug_action == ACTION_CASUAL_CARDS:
                    audio.play_sound("button_click")
                    debug_open_casual_cards()

                elif debug_action == ACTION_POKER_NIGHT:
                    audio.play_sound("button_click")
                    debug_open_poker_night()

                elif debug_action == ACTION_CASINO_NIGHT:
                    audio.play_sound("button_click")
                    debug_open_casino_night()

                elif debug_action == ACTION_HEAD_TO_HEAD:
                    audio.play_sound("button_click")
                    debug_open_head_to_head()

                elif debug_action == ACTION_ADVANCE_CAREER_DAY:
                    audio.play_sound("button_click")
                    advance_career_day(
                        completed=False
                    )
                    current_state = STATE_CAREER_HUB

                elif debug_action == ACTION_NEW_CAREER_MONTH:
                    audio.play_sound("button_click")
                    debug_start_next_career_month()
                    current_state = STATE_CAREER_HUB

                elif debug_action in (ACTION_ADD_PROSPECT, ACTION_ADD_PRODIGY):
                    audio.play_sound("button_click")
                    debug_add_career_prospect(prodigy=debug_action == ACTION_ADD_PRODIGY)

                elif debug_action == ACTION_CAREER_YEAR:
                    audio.play_sound("button_click")
                    debug_advance_career_year()
                    current_state = STATE_CAREER_HUB

                # ==========================================
                # Solitaire challenges
                # ==========================================

                elif debug_action == ACTION_CHALLENGE_DRAW_3:
                    audio.play_sound("button_click")
                    debug_open_solitaire_challenge(
                        "draw_3"
                    )

                elif debug_action == ACTION_CHALLENGE_NO_UNDO:
                    audio.play_sound("button_click")
                    debug_open_solitaire_challenge(
                        "no_undo"
                    )

                elif debug_action == ACTION_CHALLENGE_NO_HINTS:
                    audio.play_sound("button_click")
                    debug_open_solitaire_challenge(
                        "no_hints"
                    )

                elif debug_action == ACTION_CHALLENGE_ALL_OR_NOTHING:
                    audio.play_sound("button_click")
                    debug_open_solitaire_challenge(
                        "all_or_nothing"
                    )

                # ==========================================
                # Minigames
                # ==========================================

                elif debug_action == ACTION_SCORE_FOUR_SOLO:
                    audio.play_sound("button_click")
                    debug_open_score_four_solo()

                elif debug_action == ACTION_SCORE_FOUR_COMPETITIVE:
                    audio.play_sound("button_click")
                    debug_open_score_four_competitive()

                elif debug_action == ACTION_CRAZY_EIGHTS:
                    audio.play_sound("button_click")
                    debug_open_crazy_eights()

                elif debug_action == ACTION_BANGO:
                    audio.play_sound("button_click")
                    debug_open_bango()

                elif debug_action == ACTION_FARO:
                    audio.play_sound("button_click")
                    if career_cash < 10:
                        show_debug_message("Add cash to play")
                    else:
                        debug_open_faro()

                elif debug_action == ACTION_FIVE_O_POKER:
                    audio.play_sound("button_click")
                    if not debug_open_five_o_poker():
                        show_debug_message("Add cash to play")

                elif debug_action == ACTION_BLIND_MANS_BLUFF:
                    audio.play_sound("button_click")
                    if not debug_open_blind_mans_bluff():
                        show_debug_message("Add cash to play")

                elif debug_action == ACTION_BLACKJACK:
                    audio.play_sound("button_click")
                    debug_open_blackjack()

                elif debug_action == ACTION_ROULETTE:
                    audio.play_sound("button_click")
                    debug_open_roulette()

                elif debug_action == ACTION_HORSE_RACES:
                    audio.play_sound("button_click")
                    if career_cash < 10:
                        show_debug_message("Add cash to play")
                    else:
                        debug_open_horse_races()

                elif debug_action == ACTION_TEXAS_HOLDEM:
                    audio.play_sound("button_click")
                    open_debug_poker_npc_select("texas_holdem")

                elif debug_action == ACTION_FIVE_CARD_DRAW:
                    audio.play_sound("button_click")
                    open_debug_poker_npc_select("five_card_draw")

                elif debug_action == ACTION_SEVEN_CARD_STUD:
                    audio.play_sound("button_click")
                    open_debug_poker_npc_select("seven_card_stud")

                # ==========================================
                # Progression controls
                # ==========================================

                elif debug_action == ACTION_ADD_CASH:
                    audio.play_sound("button_click")
                    career_cash += 5000
                    if debug_previous_state == STATE_FARO and not faro_game.cashed_out:
                        faro_game.cash += 5000
                        faro_game.starting_cash += 5000
                    elif debug_previous_state == STATE_HORSE_RACES:
                        horse_races_game.bankroll += 5000
                        horse_races_game.starting_cash += 5000
                    elif debug_previous_state == STATE_FIVE_O_POKER:
                        five_o_poker_game.player_stack += 5000
                        five_o_poker_game.starting_stack += 5000
                        five_o_poker_starting_stack += 5000
                    elif debug_previous_state == STATE_BLIND_MANS_BLUFF:
                        blind_mans_bluff_game.player_stack += 5000
                        blind_mans_bluff_game.starting_stack += 5000
                        blind_mans_bluff_starting_stack += 5000
                    print("Cash:", career_cash)

                elif debug_action == ACTION_ZERO_CASH:
                    audio.play_sound("button_click")
                    career_cash = 0
                    print("Cash:", career_cash)

                elif debug_action == ACTION_ADD_RATING:
                    audio.play_sound("button_click")
                    adjust_debug_ratings(100)
                    print("Rating:", career_rating)

                elif debug_action == ACTION_SUB_RATING:
                    audio.play_sound("button_click")
                    adjust_debug_ratings(-100)
                    print("Rating:", career_rating)

                elif debug_action == ACTION_ADD_XP:
                    audio.play_sound("button_click")
                    add_player_xp(1000)
                    print("XP:", player_xp, "Level:", player_level)

                elif debug_action == ACTION_LEVEL_3:
                    audio.play_sound("button_click")
                    debug_set_player_level(3)
                    print("Level:", player_level)

                elif debug_action == ACTION_LEVEL_6:
                    audio.play_sound("button_click")
                    debug_set_player_level(6)
                    print("Level:", player_level)

                elif debug_action == ACTION_LEVEL_10:
                    audio.play_sound("button_click")
                    debug_set_player_level(10)
                    print("Level:", player_level)

                elif debug_action == ACTION_LEVEL_MAX:
                    audio.play_sound("button_click")
                    debug_set_player_level(
                        max(LEVEL_XP_THRESHOLDS)
                    )
                    print("Level:", player_level)

                elif debug_action == ACTION_ACHIEVEMENT_TEST:
                    audio.play_sound("button_click")
                    unlocked_title = debug_unlock_next_achievement()
                    if unlocked_title:
                        show_debug_message(
                            f"Unlocked: {unlocked_title}",
                            duration=2200,
                        )
                    else:
                        show_debug_message("All achievements unlocked")

                # ==========================================
                # Close
                # ==========================================

                elif debug_action == ACTION_CLOSE:
                    audio.play_sound("button_click")

                    if debug_previous_state is not None:
                        current_state = debug_previous_state

            continue

        # ==========================================
        # SPLASH
        # ==========================================

        if current_state == STATE_SPLASH:

            if (
                event.type == pygame.KEYDOWN
                or event.type
                == pygame.MOUSEBUTTONDOWN
            ):
                audio.play_sound(
                    "button_click"
                )

                current_state = (
                    STATE_PROFILE_SELECT
                )

                audio.set_music_mode(
                    "ambient"
                )

        # ==========================================
        # PROFILE SELECT
        # ==========================================

        elif current_state == STATE_PROFILE_SELECT:

            if (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
            ):

                if confirm_delete_profile:

                    if confirm_delete_yes_rect.collidepoint(
                            game_mouse_pos
                    ):
                        audio.play_sound(
                            "button_click"
                        )

                        delete_profile(
                            profile_delete_slot
                        )

                        confirm_delete_profile = False
                        profile_delete_slot = None

                    elif confirm_delete_no_rect.collidepoint(
                            game_mouse_pos
                    ):
                        audio.play_sound(
                            "button_click"
                        )

                        confirm_delete_profile = False
                        profile_delete_slot = None

                    continue

                if (profile_select_return_state == STATE_CAREER_HUB
                        and career_hub_controls.profile_cancel_rect.collidepoint(game_mouse_pos)):
                    audio.play_sound("button_click")
                    cancel_career_profile_switch()
                    continue

                delete_clicked = False

                for index, delete_rect in enumerate(
                        profile_delete_rects
                ):
                    slot = index + 1

                    if (
                            profile_exists(slot)
                            and not (profile_switch_snapshot is not None
                                     and profile_switch_snapshot[0] == slot)
                            and delete_rect.collidepoint(
                        game_mouse_pos
                        )
                    ):
                        audio.play_sound(
                            "button_click"
                        )

                        profile_delete_slot = slot
                        confirm_delete_profile = True

                        delete_clicked = True

                        break

                if delete_clicked:
                    continue

                slot_selected = None

                for index, rect in enumerate(
                        profile_slot_rects
                ):
                    if rect.collidepoint(
                            game_mouse_pos
                    ):
                        slot_selected = (
                                index + 1
                        )

                        break

                # ----------------------------
                # Existing / new profile
                # ----------------------------

                if slot_selected is not None:
                    audio.play_sound(
                        "button_click"
                    )

                    loaded = load_profile(
                        slot_selected
                    )

                    # ----------------------------
                    # Empty slot -> create profile
                    # ----------------------------

                    if loaded is None:
                        pending_profile_slot = (
                            slot_selected
                        )

                        profile_creation_mode = True
                        guest_mode = False
                        current_profile_slot = None

                        apply_fresh_profile()

                        profile_name_text = ""
                        profile_gender = "non-binary"
                        profile_name_active = False
                        profile_country_active = False
                        profile_age_active = False
                        profile_hometown_active = False
                        profile_bio_active = False
                        gender_dropdown_open = False
                        favorite_suit_dropdown_open = False
                        profile_message = ""

                        current_state = (
                            STATE_PROFILE
                        )



                    # ----------------------------
                    # Existing slot -> load profile
                    # ----------------------------

                    else:
                        current_profile_slot = (
                            slot_selected
                        )

                        guest_mode = False
                        profile_creation_mode = False
                        pending_profile_slot = None

                        apply_profile_save_data(
                            loaded
                        )

                        sync_unlocks_for_current_level()

                        profile_message = ""

                        finish_profile_selection()

                # ----------------------------
                # Guest
                # ----------------------------

                elif guest_profile_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    guest_mode = True

                    current_profile_slot = None

                    apply_fresh_profile()

                    profile_message = ""

                    finish_profile_selection()

        # ==========================================
        # MAIN MENU
        # ==========================================

        elif current_state == STATE_MENU:

            if (
                event.type
                == pygame.MOUSEBUTTONDOWN
                and event.button == 1
            ):
                if new_game_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    current_state = (
                        STATE_MODE_SELECT
                    )

                elif multiplayer_rect.collidepoint(game_mouse_pos):
                    audio.play_sound("button_click")
                    multiplayer_launcher.launch()

                elif customize_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    customize_return_state = STATE_MENU
                    customize_category = (
                        CUSTOMIZE_BACKGROUNDS
                    )

                    customize_page = 0

                    current_state = (
                        STATE_CUSTOMIZE
                    )

                elif achievements_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound("button_click")
                    achievements_scroll_y = 0
                    current_state = STATE_ACHIEVEMENTS

                elif how_to_play_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    current_state = (
                        STATE_HOW_TO_PLAY
                    )

                elif options_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    options_return_state = (
                        STATE_MENU
                    )

                    current_state = (
                        STATE_OPTIONS
                    )

                elif profile_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    profile_return_state = STATE_MENU
                    profile_select_return_state = STATE_MENU
                    profile_name_text = player_name
                    profile_name_active = False
                    profile_country_active = False
                    profile_age_active = False
                    profile_hometown_active = False
                    profile_bio_active = False
                    gender_dropdown_open = False
                    favorite_suit_dropdown_open = False
                    profile_message = ""

                    current_state = STATE_PROFILE

                elif quit_rect.collidepoint(
                    game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    running = False

        # ==========================================
        # MODE SELECT
        # ==========================================

        elif current_state == STATE_MODE_SELECT:

            if (

                    event.type

                    == pygame.MOUSEBUTTONDOWN

                    and event.button == 1

            ):

                # ==========================================

                # Return

                # ==========================================

                if play_return_rect.collidepoint(

                        game_mouse_pos

                ):

                    audio.play_sound(

                        "button_click"

                    )

                    current_state = (

                        STATE_MENU

                    )


                # ==========================================

                # Free Play

                # ==========================================

                elif play_free_rect.collidepoint(
                        game_mouse_pos
                ):

                    audio.play_sound(
                        "button_click"
                    )

                    current_game_mode = "free"
                    current_state = STATE_FREE_PLAY_SELECT


                # ==========================================
                # Career
                # ==========================================

                elif play_career_rect.collidepoint(
                        game_mouse_pos
                ):

                    audio.play_sound(
                        "button_click"
                    )

                    current_game_mode = (
                        "career"
                    )

                    ensure_career_schedule()
                    ensure_career_leaderboard()
                    ensure_career_news()

                    current_state = (

                        STATE_CAREER_HUB

                    )

                elif mode_select_back_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    current_state = (
                        STATE_MENU
                    )

        # ==========================================
        # FREE PLAY SELECT
        # ==========================================

        elif current_state == STATE_CASE_OPENING:
            if case_screen.handle_event(event, game_mouse_pos) == "return":
                if current_game_mode == "free":
                    leave_free_play_game()
                else:
                    try:
                        auto_save_career()
                        current_state = STATE_CAREER_HUB
                    except OSError as error:
                        case_screen.notice = "Save failed. Check the saves folder and retry Return."

        elif current_state == STATE_CRYPTID_CREATURES:
            if cryptid_screen.handle_event(event, game_mouse_pos) == "return":
                if cryptid_screen.career_mode:
                    leave_career_cryptid()
                else:leave_free_play_game()

        elif current_state == STATE_FREE_PLAY_SELECT:
            if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):
                if free_play_back_rect.collidepoint(game_mouse_pos):
                    audio.play_sound("button_click")
                    finish_free_play_sandbox()
                    current_state = STATE_MODE_SELECT
                else:
                    for free_game_id, free_rect in free_play_game_rects.items():
                        if not free_rect.collidepoint(game_mouse_pos):
                            continue
                        if free_game_id != "solitaire" and not is_game_unlocked(free_game_id):
                            break
                        audio.play_sound("button_click")
                        start_free_play_game(free_game_id)
                        break

        # ==========================================
        # CAREER HUB
        # ==========================================

        elif current_state == STATE_CAREER_ACTIVITY:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                action = career_activity_screen.click(game_mouse_pos)
                if action is not None:
                    audio.play_sound("button_click")
                    handle_career_activity(action)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                auto_save_career()
                current_state = STATE_CAREER_HUB

        elif current_state == STATE_CAREER_HUB:

            if (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
            ):

                if career_hub_controls.confirm_skip_day is not None:
                    if career_fast_skip_yes_rect.collidepoint(game_mouse_pos):
                        audio.play_sound("button_click")
                        target_day = career_hub_controls.confirm_skip_day
                        career_hub_controls.selected_day = target_day
                        career_hub_controls.clear_skip_confirmation()
                        skip_to_selected_career_day()
                    elif career_fast_skip_no_rect.collidepoint(game_mouse_pos):
                        audio.play_sound("button_click")
                        career_hub_controls.clear_skip_confirmation()
                    continue

                fast_skip_day = (None if career_hub_controls.warp_open else career_hub_controls.request_fast_skip_at(
                    game_mouse_pos
                ))
                if fast_skip_day is not None:
                    audio.play_sound("button_click")
                    continue

                hub_action = career_hub_controls.get_action(game_mouse_pos)
                if hub_action is not None:
                    audio.play_sound("button_click")
                    if hub_action.startswith("warp:"):
                        time_warp_career(int(hub_action.split(":")[1]))
                    elif hub_action == "skip_to_day":
                        skip_to_selected_career_day()
                    elif hub_action == "save":
                        save_career_from_hub()
                    elif hub_action == "switch":
                        begin_career_profile_switch()
                    elif hub_action == "cases":
                        start_career_cases()
                    elif hub_action == "cryptid":
                        start_career_cryptid()
                    elif hub_action == "profile":
                        profile_return_state = STATE_CAREER_HUB
                        profile_name_text = player_name
                        profile_name_active = False
                        profile_country_active = False
                        profile_age_active = False
                        profile_hometown_active = False
                        profile_bio_active = False
                        gender_dropdown_open = False
                        favorite_suit_dropdown_open = False
                        profile_message = ""
                        current_state = STATE_PROFILE
                    elif hub_action == "options":
                        options_return_state = STATE_CAREER_HUB
                        current_state = STATE_OPTIONS
                    elif hub_action == "customize":
                        customize_return_state = STATE_CAREER_HUB
                        customize_category = CUSTOMIZE_BACKGROUNDS
                        customize_page = 0
                        current_state = STATE_CUSTOMIZE
                    continue
                if career_hub_controls.select_day_at(game_mouse_pos):
                    audio.play_sound("button_click")
                    continue

                if career_play_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    current_game_mode = (
                        "career"
                    )

                    current_state = (
                        STATE_DIFFICULTY
                    )

                if career_calendar_action_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    current_activity = (
                        get_current_career_activity()
                    )

                    if current_activity is not None:

                        activity_type = (
                            current_activity[
                                "activity_type"
                            ]
                        )

                        if (
                                activity_type
                                == CAREER_ACTIVITY_ROUND
                        ):
                            pending_career_activity_index = (
                                get_current_career_activity_index()
                            )

                            pending_career_activity_type = (
                                CAREER_ACTIVITY_ROUND
                            )

                            pending_career_challenge_id = None

                            current_game_mode = (
                                "career"
                            )

                            game.clear_challenge()

                            current_state = (
                                STATE_DIFFICULTY
                            )

                        # ----------------------------
                        # Challenge
                        # ----------------------------

                        elif (
                                activity_type
                                == CAREER_ACTIVITY_CHALLENGE
                        ):
                            pending_career_activity_index = (
                                get_current_career_activity_index()
                            )

                            pending_career_activity_type = (
                                CAREER_ACTIVITY_CHALLENGE
                            )

                            pending_career_challenge_id = (
                                current_activity.get(
                                    "challenge_id"
                                )
                            )

                            current_game_mode = (
                                "career"
                            )

                            game.set_challenge(
                                pending_career_challenge_id
                            )

                            game.new_game()

                            current_state = (
                                STATE_PLAYING
                            )

                        # ----------------------------
                        # Training
                        # ----------------------------

                        elif activity_type in (
                                CAREER_ACTIVITY_CASUAL_CARDS,
                                CAREER_ACTIVITY_POKER_NIGHT,
                                CAREER_ACTIVITY_CASINO_NIGHT,
                                CAREER_ACTIVITY_NICHE_NIGHT,
                                CAREER_ACTIVITY_ARCADE_NIGHT
                        ):

                            career_event_entry = career_current_schedule[
                                career_day_of_month - 1
                                ]

                            if not restore_event_progress(career_event_entry, globals()):
                                career_event_has_activity = False
                                reset_career_event_result_log()
                                reset_career_event_session_totals(activity_type)

                            current_state = (
                                STATE_CAREER_EVENT_SELECT
                            )

                        # ----------------------------
                        # Work
                        # ----------------------------

                        elif (
                                activity_type
                                == CAREER_ACTIVITY_WORK

                        ):

                            complete_career_work_day()

                        # ----------------------------
                        # Random event
                        # ----------------------------

                        elif (
                                activity_type
                                == CAREER_ACTIVITY_EVENT
                        ):
                            career_event_entry = career_current_schedule[
                                career_day_of_month - 1
                            ]
                            career_event_has_activity = False

                            event_id = career_event_entry.get("event_id")

                            if event_id == "press_interview_01":
                                start_press_interview_event()
                            elif event_id == "sign_autographs_01":
                                start_sign_autographs_event()
                            elif event_id == "head_to_head_01":
                                start_head_to_head_event()

                            if event_id in ("career_encounter", "bigfoot_night", "alien_night"):
                                start_career_activity(work=False)
                            else:
                                current_state = STATE_CAREER_EVENT

                elif career_jobs_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    current_state = (
                        STATE_CAREER_JOBS
                    )

                elif career_real_estate_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    current_state = (
                        STATE_CAREER_REAL_ESTATE
                    )

                elif career_leaderboards_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    current_state = (
                        STATE_CAREER_LEADERBOARDS
                    )

                elif career_news_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    current_state = (
                        STATE_CAREER_NEWS
                    )

                elif career_back_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    current_state = (
                        STATE_MODE_SELECT
                    )


                elif career_calendar_skip_rect.collidepoint(
                        game_mouse_pos
                ):

                    audio.play_sound(
                        "button_click"
                    )

                    skip_career_day()

        elif current_state == STATE_SCORE_FOUR_MODE_SELECT:

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and score_four_game.rating_info_open:
                score_four_game.rating_info_open = False
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and game_mouse_pos is not None:
                from score_four_ui import handle_rating_info_click
                if handle_rating_info_click(game_mouse_pos, score_four_game):
                    audio.play_sound("button_click")
                    continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and game_mouse_pos is not None:
                from score_four_ui import LAYOUT_RECT, toggle_layout, play_control_sound
                if not score_four_game.difficulty_menu and LAYOUT_RECT.collidepoint(game_mouse_pos):
                    toggle_layout(score_four_game)
                    play_control_sound(audio, "select")
                    continue

            if score_four_game.difficulty_menu and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and menu_mouse_pos is not None:
                from score_four_ui import difficulty_action
                choice = difficulty_action(menu_mouse_pos)
                if choice == "back":
                    score_four_game.difficulty_menu = False
                elif choice:
                    score_four_game.difficulty_menu = False
                    score_four_game.start_solo_session(choice)
                    current_state = STATE_SCORE_FOUR
                audio.play_sound("button_click")
                continue

            if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and menu_mouse_pos is not None
            ):

                # ------------------------------------------
                # Solo
                # ------------------------------------------

                if (
                        score_four_solo_rect.collidepoint(
                            menu_mouse_pos
                        )
                ):

                    audio.play_sound(
                        "button_click"
                    )

                    score_four_game.difficulty_menu = True

                # ------------------------------------------
                # Competitive
                # ------------------------------------------

                elif (
                        score_four_competitive_rect.collidepoint(
                            menu_mouse_pos
                        )
                ):

                    score_four_opponent_choices = (
                        get_score_four_opponent_choices()
                    )

                    if score_four_opponent_npc is not None:
                        opponent_name = (
                            score_four_opponent_npc["name"]
                        )
                    else:
                        opponent_name = "NPC"

                    audio.play_sound(
                        "button_click"
                    )

                    current_state = (
                        STATE_SCORE_FOUR_OPPONENT_SELECT
                    )

                # ------------------------------------------
                # Return
                # ------------------------------------------

                elif (
                        score_four_mode_return_rect.collidepoint(
                            menu_mouse_pos
                        )
                ):

                    audio.play_sound(
                        "button_click"
                    )

                    if current_game_mode == "free":
                        finish_free_play_sandbox()
                        current_state = STATE_FREE_PLAY_SELECT
                    else:
                        current_state = STATE_CAREER_EVENT_SELECT


        # ==================================================
        # SCORE-FOUR OPPONENT SELECT
        # ==================================================

        elif (
                current_state
                == STATE_SCORE_FOUR_OPPONENT_SELECT
        ):

            if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):

                opponent_clicked = False

                # ------------------------------------------
                # Opponent cards
                # ------------------------------------------

                for index, rect in enumerate(
                        score_four_opponent_rects
                ):

                    if (
                            index
                            < len(
                        score_four_opponent_choices
                    )
                            and rect.collidepoint(
                        game_mouse_pos
                    )
                    ):
                        score_four_opponent_npc = (
                            score_four_opponent_choices[
                                index
                            ]
                        )

                        audio.play_sound(
                            "button_click"
                        )

                        opponent_clicked = True

                        score_four_game.start_competitive_session(
                            skill_tier=(
                                score_four_opponent_npc[
                                    "skill_tier"
                                ]
                            ),
                            rating=score_four_opponent_npc.get("career_ratings", {}).get("score_four"),
                        )

                        current_state = (
                            STATE_SCORE_FOUR
                        )

                        break

                # ------------------------------------------
                # Return
                # ------------------------------------------

                if (
                        not opponent_clicked
                        and score_four_opponent_return_rect.collidepoint(
                    game_mouse_pos
                )
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    current_state = (
                        STATE_SCORE_FOUR_MODE_SELECT
                    )


        # ==================================================
        # SEVEN-CARD STUD BUY-IN
        # ==================================================

        elif (
                current_state
                == STATE_SEVEN_CARD_STUD_BUY_IN
        ):
            if (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):
                buy_in_action = (
                    get_seven_card_stud_buy_in_action(
                        game_mouse_pos,
                        career_cash,
                        SEVEN_CARD_STUD_MIN_BUY_IN
                    )
                )

                if buy_in_action is not None:
                    action_type, amount = (
                        buy_in_action
                    )

                    if action_type == "back":
                        audio.play_sound(
                            "button_click"
                        )

                        if current_game_mode == "free":
                            finish_free_play_sandbox()
                            current_state = STATE_FREE_PLAY_SELECT
                        else:
                            current_state = STATE_CAREER_EVENT_SELECT

                    elif action_type == "buy_in":
                        audio.play_sound(
                            "button_click"
                        )

                        start_seven_card_stud_session(
                            amount
                        )

        # ==================================================
        # SEVEN-CARD STUD
        # ==================================================

        elif current_state == STATE_SEVEN_CARD_STUD:

            if (
                    is_holdem_options_open()
                    and event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):
                option_changed = handle_holdem_options_click(
                    game_mouse_pos
                )
                if option_changed:
                    audio.play_sound("button_click")
                    if not is_holdem_auto_deal_enabled():
                        seven_card_stud_next_hand_at = 0
                continue

            if (
                    event.type == pygame.MOUSEWHEEL
                    and game_mouse_pos is not None
                    and STUD_LOG_RECT.collidepoint(
                        game_mouse_pos
                    )
            ):
                scroll_seven_card_stud_panel(
                    event.y,
                    seven_card_stud_game
                )

            elif (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):
                if handle_seven_card_stud_panel_click(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )
                    continue

                stud_action = (
                    get_seven_card_stud_action(
                        game_mouse_pos,
                        seven_card_stud_game
                    )
                )

                if (
                        stud_action
                        == STUD_ACTION_NEXT_HAND
                ):
                    if (
                            seven_card_stud_game.all_npcs_busted()
                            and not seven_card_stud_game.player_busted
                    ):
                        audio.play_sound(
                            "button_click"
                        )

                        process_seven_card_stud_showdown()
                        finish_seven_card_stud_session()

                    elif (
                            seven_card_stud_game.player_stack > 0
                            and not seven_card_stud_game.player_busted
                    ):
                        audio.play_sound(
                            "button_click"
                        )

                        seven_card_stud_next_hand_at = 0

                        if seven_card_stud_game.start_hand():
                            audio.play_sound(
                                "card_draw"
                            )

                elif (
                        stud_action
                        == STUD_ACTION_FOLD
                ):
                    if seven_card_stud_game.player_fold():
                        audio.play_sound(
                            "button_click"
                        )

                        seven_card_stud_session_net = (
                                seven_card_stud_game.player_stack
                                - seven_card_stud_starting_stack
                        )

                        career_event_has_activity = True

                elif (
                        stud_action
                        == STUD_ACTION_CHECK_CALL
                ):
                    amount_to_call = (
                        seven_card_stud_game
                        .get_player_amount_to_call()
                    )

                    if amount_to_call > 0:
                        success = (
                            seven_card_stud_game.player_call()
                        )
                        player_chat_action = "call"
                    else:
                        success = (
                            seven_card_stud_game.player_check()
                        )
                        player_chat_action = "check"

                    if success:
                        if amount_to_call > 0:
                            play_texas_holdem_chip_sound()
                        else:
                            audio.play_sound(
                                "poker_check"
                            )

                        post_seven_card_stud_chat(
                            generate_player_action_reaction(
                                seven_card_stud_game,
                                player_chat_action
                            )
                        )

                        schedule_seven_card_stud_npc_action()

                elif (
                        stud_action
                        == STUD_ACTION_BET_RAISE
                ):
                    wager_target = (
                        seven_card_stud_game
                        .get_player_fixed_bet_or_raise_to()
                    )

                    if seven_card_stud_game.current_bet == 0:
                        player_chat_action = "bet"
                        success = (
                            seven_card_stud_game.player_bet(
                                wager_target
                            )
                        )
                    else:
                        player_chat_action = "raise"
                        success = (
                            seven_card_stud_game.player_raise(
                                wager_target
                            )
                        )

                    if success:
                        play_texas_holdem_chip_sound()

                        post_seven_card_stud_chat(
                            generate_player_action_reaction(
                                seven_card_stud_game,
                                player_chat_action
                            )
                        )

                        schedule_seven_card_stud_npc_action()

                elif (
                        stud_action
                        == STUD_ACTION_OPTIONS
                ):
                    audio.play_sound("button_click")
                    toggle_holdem_options()

                elif (
                        stud_action
                        == STUD_ACTION_RETURN
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    finish_seven_card_stud_session()

        # ==================================================
        # FIVE-CARD DRAW BUY-IN
        # ==================================================

        elif (
                current_state
                == STATE_FIVE_CARD_DRAW_BUY_IN
        ):

            if (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):

                buy_in_action = (
                    get_five_card_draw_buy_in_action(
                        game_mouse_pos,
                        career_cash,
                        FIVE_CARD_DRAW_MIN_BUY_IN
                    )
                )

                if buy_in_action is not None:

                    action_type, amount = (
                        buy_in_action
                    )

                    if action_type == "back":
                        audio.play_sound(
                            "button_click"
                        )

                        if current_game_mode == "free":
                            finish_free_play_sandbox()
                            current_state = STATE_FREE_PLAY_SELECT
                        else:
                            current_state = STATE_CAREER_EVENT_SELECT

                    elif action_type == "buy_in":

                        audio.play_sound(
                            "button_click"
                        )

                        start_five_card_draw_session(
                            amount
                        )

        # ==================================================
        # FIVE-CARD DRAW
        # ==================================================

        elif current_state == STATE_FIVE_CARD_DRAW:

            if (
                    is_holdem_options_open()
                    and event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):
                option_changed = handle_holdem_options_click(
                    game_mouse_pos
                )
                if option_changed:
                    audio.play_sound("button_click")
                    if not is_holdem_auto_deal_enabled():
                        five_card_draw_next_hand_at = 0
                continue

            if event.type == pygame.KEYDOWN:
                if handle_five_card_draw_manual_bet_key(
                        event,
                        five_card_draw_game
                ):
                    continue

            if (
                    event.type == pygame.MOUSEMOTION
                    and game_mouse_pos is not None
            ):
                drag_five_card_draw_bet_slider(
                    game_mouse_pos
                )

            elif (
                    event.type == pygame.MOUSEBUTTONUP
                    and event.button == 1
            ):
                stop_five_card_draw_bet_slider()

            elif (
                    event.type == pygame.MOUSEWHEEL
                    and game_mouse_pos is not None
                    and DRAW_LOG_RECT.collidepoint(
                        game_mouse_pos
                    )
            ):

                scroll_five_card_draw_panel(
                    event.y,
                    five_card_draw_game
                )

            elif (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):

                if handle_five_card_draw_manual_bet_click(
                        game_mouse_pos,
                        five_card_draw_game
                ):
                    audio.play_sound("button_click")
                    continue

                if handle_five_card_draw_panel_click(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )
                    continue

                if handle_five_card_draw_card_click(
                        game_mouse_pos,
                        five_card_draw_game
                ):
                    audio.play_sound(
                        "button_click"
                    )
                    continue

                if update_five_card_draw_bet_slider(
                        game_mouse_pos,
                        five_card_draw_game
                ):
                    audio.play_sound("button_click")
                    continue

                if (
                        five_card_draw_game.current_stage
                        in (
                            "preflop",
                            "post_draw",
                        )
                        and handle_five_card_draw_bet_preset(
                            game_mouse_pos
                        )
                ):
                    audio.play_sound(
                        "button_click"
                    )
                    continue

                draw_action = (
                    get_five_card_draw_action(
                        game_mouse_pos,
                        five_card_draw_game
                    )
                )

                if (
                        draw_action
                        == DRAW_ACTION_NEXT_HAND
                ):

                    if (
                            five_card_draw_game.all_npcs_busted()
                            and not five_card_draw_game.player_busted
                    ):
                        audio.play_sound(
                            "button_click"
                        )

                        process_five_card_draw_showdown()
                        finish_five_card_draw_session()

                    elif (
                            five_card_draw_game.player_stack > 0
                            and not five_card_draw_game.player_busted
                    ):
                        audio.play_sound(
                            "button_click"
                        )

                        five_card_draw_next_hand_at = 0

                        if five_card_draw_game.start_hand():
                            audio.play_sound(
                                "card_draw"
                            )

                        clear_five_card_draw_selection()

                elif (
                        draw_action
                        == DRAW_ACTION_DRAW
                ):

                    discard_indexes = (
                        get_selected_draw_indexes()
                    )

                    if five_card_draw_game.player_draw(
                            discard_indexes
                    ):
                        audio.play_sound(
                            "card_draw"
                        )

                        clear_five_card_draw_selection()

                elif (
                        draw_action
                        == DRAW_ACTION_FOLD
                ):

                    if five_card_draw_game.player_fold():
                        audio.play_sound(
                            "button_click"
                        )

                        five_card_draw_session_net = (
                                five_card_draw_game.player_stack
                                - five_card_draw_starting_stack
                        )

                        career_event_has_activity = True

                elif (
                        draw_action
                        == DRAW_ACTION_CHECK_CALL
                ):

                    amount_to_call = (
                        five_card_draw_game
                        .get_player_amount_to_call()
                    )

                    if amount_to_call > 0:
                        success = (
                            five_card_draw_game.player_call()
                        )
                        player_chat_action = "call"

                    else:
                        success = (
                            five_card_draw_game.player_check()
                        )
                        player_chat_action = "check"

                    if success:

                        if amount_to_call > 0:
                            play_texas_holdem_chip_sound()

                        else:
                            audio.play_sound(
                                "poker_check"
                            )

                        post_five_card_draw_chat(
                            generate_player_action_reaction(
                                five_card_draw_game,
                                player_chat_action
                            )
                        )

                        schedule_five_card_draw_npc_action()

                elif (
                        draw_action
                        == DRAW_ACTION_BET_RAISE
                ):

                    bet_amount = (
                        get_five_card_draw_bet_amount(
                            five_card_draw_game
                        )
                    )

                    if five_card_draw_game.current_bet == 0:
                        player_chat_action = "bet"
                        success = five_card_draw_game.player_bet(
                            bet_amount
                        )

                    else:
                        player_chat_action = "raise"
                        success = five_card_draw_game.player_raise(
                            bet_amount
                        )

                    if success:
                        play_texas_holdem_chip_sound()
                        clear_five_card_draw_manual_bet()

                        post_five_card_draw_chat(
                            generate_player_action_reaction(
                                five_card_draw_game,
                                player_chat_action
                            )
                        )

                        schedule_five_card_draw_npc_action()

                elif (
                        draw_action
                        == DRAW_ACTION_OPTIONS
                ):
                    audio.play_sound("button_click")
                    toggle_holdem_options()

                elif (
                        draw_action
                        == DRAW_ACTION_RETURN
                ):

                    audio.play_sound(
                        "button_click"
                    )

                    finish_five_card_draw_session()

        # ==================================================
        # TEXAS HOLD'EM BUY-IN
        # ==================================================

        elif (
                current_state
                == STATE_TEXAS_HOLDEM_BUY_IN
        ):

            if (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):

                buy_in_action = (
                    get_texas_holdem_buy_in_action(
                        game_mouse_pos,
                        career_cash,
                        TEXAS_HOLDEM_MIN_BUY_IN
                    )
                )

                if buy_in_action is not None:

                    action_type, amount = (
                        buy_in_action
                    )

                    # ------------------------------------------
                    # Back
                    # ------------------------------------------

                    if action_type == "back":
                        audio.play_sound(
                            "button_click"
                        )

                        if current_game_mode == "free":
                            finish_free_play_sandbox()
                            current_state = STATE_FREE_PLAY_SELECT
                        else:
                            current_state = STATE_CAREER_EVENT_SELECT

                    # ------------------------------------------
                    # Buy in
                    # ------------------------------------------

                    elif (
                            action_type
                            == "buy_in"
                    ):

                        audio.play_sound(
                            "button_click"
                        )

                        start_texas_holdem_session(
                            amount
                        )

        # ==================================================
        # TEXAS HOLD'EM
        # ==================================================

        elif current_state == STATE_TEXAS_HOLDEM:

            if getattr(texas_holdem_game, "recap_open", False):
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    from poker_recap import get_recap_action
                    handle_recap_action(texas_holdem_game, get_recap_action(game_mouse_pos, texas_holdem_game))
                    if not texas_holdem_game.recap_open:
                        texas_holdem_next_hand_at = 0
                        if texas_holdem_game.player_busted or texas_holdem_game.all_npcs_busted():
                            texas_holdem_session_end_at = pygame.time.get_ticks() + TEXAS_HOLDEM_SESSION_END_DELAY
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    texas_holdem_game.recap_open = False
                    texas_holdem_next_hand_at = 0
                    if texas_holdem_game.player_busted or texas_holdem_game.all_npcs_busted():
                        texas_holdem_session_end_at = pygame.time.get_ticks() + TEXAS_HOLDEM_SESSION_END_DELAY
                continue

            # ==================================================
            # Temporary keyboard hand progression
            #
            # SPACE:
            # Ready/Showdown -> Deal
            # Preflop        -> Flop
            # Flop           -> Turn
            # Turn           -> River
            # River          -> Showdown
            # ==================================================

            if event.type == pygame.KEYDOWN:

                if handle_holdem_manual_bet_key(
                        event,
                        texas_holdem_game
                ):
                    continue

                if (
                        event.key == pygame.K_F7
                        and current_state
                        == STATE_TEXAS_HOLDEM
                ):
                    debug_setup_holdem_heads_up()

                    continue

                # ==================================================
                # SPACE = temporary hand progression
                # ==================================================

                if event.key == pygame.K_SPACE:

                    # ------------------------------------------
                    # Deal
                    # ------------------------------------------

                    if texas_holdem_game.current_stage in (
                            "idle",
                            "ready",
                            "showdown",
                    ):

                        if texas_holdem_game.start_hand():
                            play_texas_holdem_new_hand_sound()

                        career_event_has_activity = True

                        audio.play_sound(
                            "button_click"
                        )

                    # ------------------------------------------
                    # Flop
                    # ------------------------------------------

                    elif (
                            texas_holdem_game.current_stage
                            == "preflop"
                    ):

                        if texas_holdem_game.deal_flop():
                            audio.play_sound(
                                "button_click"
                            )

                    # ------------------------------------------
                    # Turn
                    # ------------------------------------------

                    elif (
                            texas_holdem_game.current_stage
                            == "flop"
                    ):

                        if texas_holdem_game.deal_turn():
                            audio.play_sound(
                                "button_click"
                            )

                    # ------------------------------------------
                    # River
                    # ------------------------------------------

                    elif (
                            texas_holdem_game.current_stage
                            == "turn"
                    ):

                        if texas_holdem_game.deal_river():
                            audio.play_sound(
                                "button_click"
                            )

                    # ------------------------------------------
                    # Showdown
                    # ------------------------------------------

                    elif (
                            texas_holdem_game.current_stage
                            == "river"
                    ):

                        if texas_holdem_game.showdown():
                            texas_holdem_session_net = (
                                    texas_holdem_game.player_stack
                                    - texas_holdem_starting_stack
                            )

                            career_event_has_activity = True

                            audio.play_sound(
                                "button_click"
                            )

                # ==================================================
                # B = temporary $50 bet test
                # ==================================================

                elif event.key == pygame.K_b:

                    result = (
                        texas_holdem_game.player_bet(
                            50
                        )
                    )

                    if result:
                        schedule_texas_holdem_npc_action()

                    print(
                        "BET RESULT:",
                        result
                    )

                    print(
                        "Player stack:",
                        texas_holdem_game.player_stack
                    )

                    print(
                        "NPC stacks:",
                        texas_holdem_game.npc_stacks
                    )

                    print(
                        "Pot:",
                        texas_holdem_game.pot
                    )

                    print(
                        "Current bet:",
                        texas_holdem_game.current_bet
                    )

                    print(
                        "Player round bet:",
                        texas_holdem_game.player_round_bet
                    )

                    print(
                        "NPC round bets:",
                        texas_holdem_game.npc_round_bets
                    )

                    print(
                        "Round complete:",
                        texas_holdem_game.is_betting_round_complete()
                    )

            # ==================================================
            # Game Log scrolling
            # ==================================================

            elif (
                    event.type == pygame.MOUSEWHEEL
                    and game_mouse_pos is not None
                    and HOLDEM_LOG_RECT.collidepoint(
                game_mouse_pos
            )
            ):

                scroll_holdem_log(
                    event.y,
                    len(holdem_log_history)
                )

            # ==================================================
            # Drag bet slider
            # ==================================================

            elif (
                    event.type == pygame.MOUSEMOTION
                    and game_mouse_pos is not None
            ):

                drag_holdem_bet_slider(
                    game_mouse_pos
                )


            # ==================================================
            # Release bet slider
            # ==================================================

            elif (
                    event.type == pygame.MOUSEBUTTONUP
                    and event.button == 1
            ):

                stop_holdem_bet_slider_drag()

            # ==================================================
            # Mouse controls
            # ==================================================

            elif (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):

                # ==================================================
                # Poker options overlay
                # ==================================================

                if is_holdem_options_open():

                    option_changed = (
                        handle_holdem_options_click(
                            game_mouse_pos
                        )
                    )

                    if option_changed:
                        audio.play_sound(
                            "button_click"
                        )

                    # Consume every click while overlay is open.
                    continue

                # ==================================================
                # Manual bet / raise-to entry
                # ==================================================

                if handle_holdem_manual_bet_click(
                        game_mouse_pos,
                        texas_holdem_game
                ):
                    audio.play_sound("button_click")
                    continue

                # ==================================================
                # Log / Chat tabs
                # ==================================================

                panel_handled = (
                    handle_holdem_panel_click(
                        game_mouse_pos
                    )
                )

                if panel_handled:

                    audio.play_sound(
                        "button_click"
                    )

                else:

                    # ==================================================
                    # Bet slider / shortcut buttons
                    # ==================================================

                    slider_handled = (
                        update_holdem_bet_slider(
                            game_mouse_pos,
                            texas_holdem_game
                        )
                    )

                    if slider_handled:

                        audio.play_sound(
                            "button_click"
                        )

                    else:

                        # ==================================================
                        # Main Hold'em controls
                        # ==================================================

                        holdem_action = (
                            get_texas_holdem_action(
                                game_mouse_pos,
                                texas_holdem_game
                            )
                        )

                        # ------------------------------------------
                        # Next Hand
                        # ------------------------------------------

                        if handle_recap_action(texas_holdem_game, holdem_action):
                            if holdem_action != "recap_block":
                                audio.play_sound("button_click")
                            texas_holdem_next_hand_at = 0
                            if not texas_holdem_game.recap_open and (texas_holdem_game.player_busted or texas_holdem_game.all_npcs_busted()):
                                texas_holdem_session_end_at = pygame.time.get_ticks() + TEXAS_HOLDEM_SESSION_END_DELAY
                        elif (
                                holdem_action
                                == HOLDEM_ACTION_NEXT_HAND
                        ):

                            if (
                                    texas_holdem_game.all_npcs_busted()
                                    and not texas_holdem_game.player_busted
                            ):
                                audio.play_sound(
                                    "button_click"
                                )

                                process_texas_holdem_showdown()

                                finish_texas_holdem_session()

                            elif (
                                    texas_holdem_game.player_stack > 0
                                    and not texas_holdem_game.player_busted
                            ):
                                audio.play_sound(
                                    "button_click"
                                )

                                texas_holdem_next_hand_at = 0

                                if texas_holdem_game.start_hand():
                                    play_texas_holdem_new_hand_sound()

                        elif (
                                holdem_action
                                == HOLDEM_ACTION_FOLD
                        ):

                            if texas_holdem_game.player_fold():
                                audio.play_sound(
                                    "button_click"
                                )

                                texas_holdem_session_net = (
                                        texas_holdem_game.player_stack
                                        - texas_holdem_starting_stack
                                )

                                career_event_has_activity = True

                        # ------------------------------------------
                        # Check / Call
                        # ------------------------------------------

                        elif (
                                holdem_action
                                == HOLDEM_ACTION_CHECK_CALL
                        ):

                            amount_to_call = (
                                texas_holdem_game
                                .get_player_amount_to_call()
                            )

                            if amount_to_call > 0:

                                success = (
                                    texas_holdem_game
                                    .player_call()
                                )

                            else:

                                success = (
                                    texas_holdem_game
                                    .player_check()
                                )

                            if success:

                                if amount_to_call > 0:

                                    play_texas_holdem_chip_sound()

                                    player_chat_action = (
                                        "call"
                                    )

                                else:

                                    audio.play_sound(
                                        "poker_check"
                                    )

                                    player_chat_action = (
                                        "check"
                                    )

                                post_texas_holdem_chat(
                                    generate_player_action_reaction(
                                        texas_holdem_game,
                                        player_chat_action
                                    )
                                )

                                schedule_texas_holdem_npc_action()

                        # ------------------------------------------
                        # Bet / Raise
                        # ------------------------------------------

                        elif (
                                holdem_action
                                == HOLDEM_ACTION_BET_RAISE
                        ):

                            bet_amount = (
                                get_holdem_bet_amount(
                                    texas_holdem_game
                                )
                            )

                            if (
                                    texas_holdem_game.current_bet
                                    == 0
                            ):

                                player_chat_action = (
                                    "bet"
                                )

                                success = (
                                    texas_holdem_game
                                    .player_bet(
                                        bet_amount
                                    )
                                )

                            else:

                                player_chat_action = (
                                    "raise"
                                )

                                success = (
                                    texas_holdem_game
                                    .player_raise(
                                        bet_amount
                                    )
                                )

                            if success:
                                play_texas_holdem_chip_sound()
                                clear_holdem_manual_bet()

                                post_texas_holdem_chat(
                                    generate_player_action_reaction(
                                        texas_holdem_game,
                                        player_chat_action
                                    )
                                )

                                schedule_texas_holdem_npc_action()

                        # ------------------------------------------
                        # Exit
                        # ------------------------------------------

                        elif (
                                holdem_action
                                == HOLDEM_ACTION_RETURN
                        ):

                            audio.play_sound(
                                "button_click"
                            )

                            finish_texas_holdem_session()

                        # ------------------------------------------
                        # Options
                        # ------------------------------------------

                        elif holdem_action == "options":

                            audio.play_sound(
                                "button_click"
                            )

                            toggle_holdem_options()



        elif current_state == STATE_BLACKJACK_BET:

            if (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):

                selected_bet = None

                # ==========================================
                # Bet selection
                # ==========================================

                if career_cash > 0:

                    if blackjack_bet_1_rect.collidepoint(
                            game_mouse_pos
                    ):

                        blackjack_selected_bet_percentage = (
                            0.01
                        )

                        selected_bet = (
                            get_blackjack_bet(
                                blackjack_selected_bet_percentage
                            )
                        )

                    elif blackjack_bet_2_rect.collidepoint(
                            game_mouse_pos
                    ):

                        blackjack_selected_bet_percentage = (
                            0.02
                        )

                        selected_bet = (
                            get_blackjack_bet(
                                blackjack_selected_bet_percentage
                            )
                        )

                    elif blackjack_bet_5_rect.collidepoint(
                            game_mouse_pos
                    ):

                        blackjack_selected_bet_percentage = (
                            0.05
                        )

                        selected_bet = (
                            get_blackjack_bet(
                                blackjack_selected_bet_percentage
                            )
                        )

                    elif blackjack_bet_10_rect.collidepoint(
                            game_mouse_pos
                    ):

                        blackjack_selected_bet_percentage = (
                            0.10
                        )

                        selected_bet = (
                            get_blackjack_bet(
                                blackjack_selected_bet_percentage
                            )
                        )

                    elif blackjack_bet_all_rect.collidepoint(
                            game_mouse_pos
                    ):

                        blackjack_selected_bet_percentage = (
                            1.0
                        )

                        selected_bet = (
                            get_blackjack_bet(
                                blackjack_selected_bet_percentage
                            )
                        )

                # ==========================================
                # Start hand
                # ==========================================

                if (
                        selected_bet is not None
                        and selected_bet > 0
                        and career_cash >= selected_bet
                ):

                    audio.play_sound(
                        "button_click"
                    )

                    blackjack_round_doubled = False
                    blackjack_round_all_in = (
                        selected_bet >= career_cash
                    )
                    blackjack_round_start_bet = selected_bet

                    career_cash -= (
                        selected_bet
                    )

                    blackjack_game.start_round(
                        selected_bet
                    )

                    career_event_has_activity = True

                    current_state = (
                        STATE_BLACKJACK
                    )

                # ==========================================
                # Return
                # ==========================================

                elif blackjack_bet_return_rect.collidepoint(
                        game_mouse_pos
                ):

                    audio.play_sound(
                        "button_click"
                    )

                    if current_game_mode == "free":
                        finish_free_play_sandbox()
                    current_state = (
                        STATE_FREE_PLAY_SELECT if current_game_mode == "free" else STATE_CAREER_EVENT_SELECT
                    )

        elif current_state == STATE_BLACKJACK:

            if (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):

                # ==========================================
                # Next-hand bet selection
                # ==========================================

                next_bet_choices = [
                    0.01,
                    0.02,
                    0.05,
                    0.10,
                    1.0,
                ]
                next_bet_clicked = False

                for index, rect in enumerate(blackjack_bet_dropdown_rects):
                    if rect.collidepoint(game_mouse_pos):
                        blackjack_selected_bet_percentage = next_bet_choices[index]
                        blackjack_bet_dropdown_open = False
                        audio.play_sound("button_click")
                        next_bet_clicked = True
                        break

                # ==========================================
                # Hit
                # ==========================================

                if next_bet_clicked:
                    continue

                # ==========================================

                elif (
                        not blackjack_game.round_complete
                        and blackjack_hit_rect.collidepoint(
                    game_mouse_pos
                )
                ):

                    audio.play_sound(
                        "card_draw"
                    )

                    blackjack_game.hit()

                # ==========================================
                # Stand
                # ==========================================

                elif (
                        not blackjack_game.round_complete
                        and blackjack_stand_rect.collidepoint(
                    game_mouse_pos
                )
                ):

                    audio.play_sound(
                        "button_click"
                    )

                    blackjack_game.stand()

                # ==========================================
                # Split
                # ==========================================

                elif (
                        blackjack_game.can_split()
                        and career_cash >= blackjack_game.current_hand_bet()
                        and blackjack_split_rect.collidepoint(
                    game_mouse_pos
                )
                ):
                    additional_bet = blackjack_game.current_hand_bet()

                    if career_cash >= additional_bet:
                        career_cash -= additional_bet
                        audio.play_sound("button_click")
                        audio.play_sound("card_draw")
                        blackjack_game.split_hand()

                # ==========================================
                # Double
                # ==========================================

                elif (
                        blackjack_game.can_double_down()
                        and career_cash >= blackjack_game.current_hand_bet()
                        and blackjack_double_rect.collidepoint(
                    game_mouse_pos
                )
                ):

                    additional_bet = blackjack_game.current_hand_bet()

                    if career_cash >= additional_bet:
                        career_cash -= (
                            additional_bet
                        )

                        audio.play_sound(
                            "button_click"
                        )

                        audio.play_sound(
                            "card_draw"
                        )

                        blackjack_round_doubled = True
                        blackjack_game.double_down()

                # ==========================================
                # Deal Again
                # ==========================================

                elif (
                        blackjack_game.round_complete
                        and career_cash > 0
                        and blackjack_deal_again_rect.collidepoint(
                    game_mouse_pos
                )
                ):

                    if (
                            blackjack_selected_bet_percentage
                            is not None
                    ):

                        next_bet = (
                            get_blackjack_bet(
                                blackjack_selected_bet_percentage
                            )
                        )

                        if (
                                next_bet > 0
                                and career_cash >= next_bet
                        ):
                            audio.play_sound(
                                "button_click"
                            )

                            blackjack_round_doubled = False
                            blackjack_round_all_in = (
                                next_bet >= career_cash
                            )
                            blackjack_round_start_bet = next_bet

                            career_cash -= (
                                next_bet
                            )

                            blackjack_game.start_round(
                                next_bet
                            )

                            blackjack_bet_dropdown_open = False

                # ==========================================
                # Return
                # ==========================================

                elif (
                        blackjack_game.round_complete
                        and blackjack_return_rect.collidepoint(
                    game_mouse_pos
                )
                ):

                    audio.play_sound(
                        "button_click"
                    )

                    blackjack_bet_dropdown_open = False

                    if current_game_mode == "free":
                        finish_free_play_sandbox()
                    current_state = (
                        STATE_FREE_PLAY_SELECT if current_game_mode == "free" else STATE_CAREER_EVENT_SELECT
                    )

        # ==================================================
        # ROULETTE
        # ==================================================

        elif current_state == STATE_ROULETTE:

            if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button in (
                    1,
                    3
            )
                    and game_mouse_pos is not None
            ):

                roulette_action = (
                    get_roulette_action(
                        game_mouse_pos
                    )
                )

                is_right_click = (
                        event.button == 3
                )

                # ==========================================
                # CHIP SELECTION
                # ==========================================

                if roulette_action == ACTION_CHIP_10:

                    roulette_chip_value = 10

                    audio.play_sound(
                        "button_click"
                    )

                elif roulette_action == ACTION_CHIP_50:

                    roulette_chip_value = 50

                    audio.play_sound(
                        "button_click"
                    )

                elif roulette_action == ACTION_CHIP_100:

                    roulette_chip_value = 100

                    audio.play_sound(
                        "button_click"
                    )

                elif roulette_action == ACTION_CHIP_500:

                    roulette_chip_value = 500

                    audio.play_sound(
                        "button_click"
                    )

                # ==========================================
                # CLEAR BETS
                # ==========================================

                elif (
                        roulette_action == ACTION_CLEAR_BETS
                        and not roulette_game.spinning
                ):

                    if roulette_game.clear_bets():
                        audio.play_sound(
                            "button_click"
                        )

                # ==========================================
                # NUMBER BET
                # ==========================================

                elif (
                        roulette_action is not None
                        and roulette_action.startswith(
                    ACTION_BET_NUMBER_PREFIX
                )
                        and not roulette_game.spinning
                ):

                    number = (
                        roulette_action[
                            len(
                                ACTION_BET_NUMBER_PREFIX
                            ):
                        ]
                    )

                    wager = (
                        roulette_chip_value
                    )

                    if is_right_click:

                        if roulette_game.remove_bet(
                                "number",
                                number,
                                wager
                        ):
                            audio.play_sound(
                                "button_click"
                            )

                    else:

                        if (
                                wager > 0
                                and (
                                roulette_game.get_total_bet()
                                + wager
                        ) <= career_cash
                        ):
                            roulette_game.place_bet(
                                "number",
                                number,
                                wager
                            )

                            audio.play_sound(
                                "button_click"
                            )

                # ==========================================
                # DOZENS
                # ==========================================

                elif roulette_action == ACTION_BET_DOZEN_1:

                    try_place_or_remove_roulette_bet(
                        "dozen",
                        1,
                        is_right_click
                    )

                elif roulette_action == ACTION_BET_DOZEN_2:

                    try_place_or_remove_roulette_bet(
                        "dozen",
                        2,
                        is_right_click
                    )

                elif roulette_action == ACTION_BET_DOZEN_3:

                    try_place_or_remove_roulette_bet(
                        "dozen",
                        3,
                        is_right_click
                    )

                # ==========================================
                # COLUMNS
                # ==========================================

                elif roulette_action == ACTION_BET_COLUMN_1:

                    try_place_or_remove_roulette_bet(
                        "column",
                        1,
                        is_right_click
                    )

                elif roulette_action == ACTION_BET_COLUMN_2:

                    try_place_or_remove_roulette_bet(
                        "column",
                        2,
                        is_right_click
                    )

                elif roulette_action == ACTION_BET_COLUMN_3:

                    try_place_or_remove_roulette_bet(
                        "column",
                        3,
                        is_right_click
                    )

                # ==========================================
                # RED
                # ==========================================

                elif (
                        roulette_action == ACTION_BET_RED
                        and not roulette_game.spinning
                ):

                    wager = (
                        roulette_chip_value
                    )

                    if is_right_click:

                        if roulette_game.remove_bet(
                                "color",
                                "red",
                                wager
                        ):
                            audio.play_sound(
                                "button_click"
                            )

                    else:

                        if (
                                wager > 0
                                and (
                                roulette_game.get_total_bet()
                                + wager
                        ) <= career_cash
                        ):
                            roulette_game.place_bet(
                                "color",
                                "red",
                                wager
                            )

                            audio.play_sound(
                                "button_click"
                            )

                # ==========================================
                # BLACK
                # ==========================================

                elif (
                        roulette_action == ACTION_BET_BLACK
                        and not roulette_game.spinning
                ):

                    wager = (
                        roulette_chip_value
                    )

                    if is_right_click:

                        if roulette_game.remove_bet(
                                "color",
                                "black",
                                wager
                        ):
                            audio.play_sound(
                                "button_click"
                            )

                    else:

                        if (
                                wager > 0
                                and (
                                roulette_game.get_total_bet()
                                + wager
                        ) <= career_cash
                        ):
                            roulette_game.place_bet(
                                "color",
                                "black",
                                wager
                            )

                            audio.play_sound(
                                "button_click"
                            )

                # ==========================================
                # ODD
                # ==========================================

                elif (
                        roulette_action == ACTION_BET_ODD
                        and not roulette_game.spinning
                ):

                    wager = (
                        roulette_chip_value
                    )

                    if is_right_click:

                        if roulette_game.remove_bet(
                                "parity",
                                "odd",
                                wager
                        ):
                            audio.play_sound(
                                "button_click"
                            )

                    else:

                        if (
                                wager > 0
                                and (
                                roulette_game.get_total_bet()
                                + wager
                        ) <= career_cash
                        ):
                            roulette_game.place_bet(
                                "parity",
                                "odd",
                                wager
                            )

                            audio.play_sound(
                                "button_click"
                            )

                # ==========================================
                # EVEN
                # ==========================================

                elif (
                        roulette_action == ACTION_BET_EVEN
                        and not roulette_game.spinning
                ):

                    wager = (
                        roulette_chip_value
                    )

                    if is_right_click:

                        if roulette_game.remove_bet(
                                "parity",
                                "even",
                                wager
                        ):
                            audio.play_sound(
                                "button_click"
                            )

                    else:

                        if (
                                wager > 0
                                and (
                                roulette_game.get_total_bet()
                                + wager
                        ) <= career_cash
                        ):
                            roulette_game.place_bet(
                                "parity",
                                "even",
                                wager
                            )

                            audio.play_sound(
                                "button_click"
                            )

                # ==========================================
                # LOW
                # ==========================================

                elif (
                        roulette_action == ACTION_BET_LOW
                        and not roulette_game.spinning
                ):

                    wager = (
                        roulette_chip_value
                    )

                    if is_right_click:

                        if roulette_game.remove_bet(
                                "range",
                                "low",
                                wager
                        ):
                            audio.play_sound(
                                "button_click"
                            )

                    else:

                        if (
                                wager > 0
                                and (
                                roulette_game.get_total_bet()
                                + wager
                        ) <= career_cash
                        ):
                            roulette_game.place_bet(
                                "range",
                                "low",
                                wager
                            )

                            audio.play_sound(
                                "button_click"
                            )

                # ==========================================
                # HIGH
                # ==========================================

                elif (
                        roulette_action == ACTION_BET_HIGH
                        and not roulette_game.spinning
                ):

                    wager = (
                        roulette_chip_value
                    )

                    if is_right_click:

                        if roulette_game.remove_bet(
                                "range",
                                "high",
                                wager
                        ):
                            audio.play_sound(
                                "button_click"
                            )

                    else:

                        if (
                                wager > 0
                                and (
                                roulette_game.get_total_bet()
                                + wager
                        ) <= career_cash
                        ):
                            roulette_game.place_bet(
                                "range",
                                "high",
                                wager
                            )

                            audio.play_sound(
                                "button_click"
                            )

                # ==========================================
                # SPIN
                # ==========================================

                elif (

                        roulette_action
                        == ROULETTE_ACTION_SPIN
                        and not roulette_game.spinning

                ):

                    total_bet = (
                        roulette_game.get_total_bet()
                    )

                    if (
                            total_bet > 0
                            and career_cash >= total_bet
                    ):

                        career_cash -= (
                            total_bet

                        )

                        if roulette_game.start_spin():
                            career_event_has_activity = True

                            audio.play_sound(

                                "button_click"

                            )

                # ==========================================
                # RETURN
                # ==========================================

                elif (
                        roulette_action
                        == ROULETTE_ACTION_RETURN
                        and not roulette_game.spinning
                ):

                    audio.play_sound(
                        "button_click"
                    )

                    if current_game_mode == "free":
                        finish_free_play_sandbox()
                        current_state = STATE_FREE_PLAY_SELECT
                    else:
                        current_state = STATE_CAREER_EVENT_SELECT

        elif current_state == STATE_HORSE_RACES:

            if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):
                horse_action = get_horse_races_action(game_mouse_pos)

                if (
                        horse_action is not None
                        and horse_action.startswith(HORSE_RACES_ACTION_HORSE_PREFIX)
                        and horse_races_game.stage == "betting"
                ):
                    try:
                        horse_index = int(
                            horse_action[len(HORSE_RACES_ACTION_HORSE_PREFIX):]
                        )
                    except ValueError:
                        horse_index = -1
                    if horse_races_game.set_selected_horse(horse_index):
                        audio.play_sound("button_click")

                elif horse_action == HORSE_RACES_ACTION_WIN:
                    if horse_races_game.set_bet_type("win"):
                        audio.play_sound("button_click")

                elif horse_action == HORSE_RACES_ACTION_PLACE:
                    if horse_races_game.set_bet_type("place"):
                        audio.play_sound("button_click")

                elif horse_action == HORSE_RACES_ACTION_SHOW:
                    if horse_races_game.set_bet_type("show"):
                        audio.play_sound("button_click")

                elif horse_action == HORSE_RACES_ACTION_CHIP_10:
                    if horse_races_game.set_chip_value(10):
                        audio.play_sound("button_click")

                elif horse_action == HORSE_RACES_ACTION_CHIP_50:
                    if horse_races_game.set_chip_value(50):
                        audio.play_sound("button_click")

                elif horse_action == HORSE_RACES_ACTION_CHIP_100:
                    if horse_races_game.set_chip_value(100):
                        audio.play_sound("button_click")

                elif horse_action == HORSE_RACES_ACTION_CHIP_500:
                    if horse_races_game.set_chip_value(500):
                        audio.play_sound("button_click")

                elif horse_action == HORSE_RACES_ACTION_PLACE_BET:
                    if horse_races_game.place_selected_bet():
                        audio.play_sound("poker_chips_1")

                elif horse_action == HORSE_RACES_ACTION_CLEAR_BETS:
                    if horse_races_game.clear_bets():
                        audio.play_sound("poker_chips_1")

                elif horse_action == HORSE_RACES_ACTION_START_RACE:
                    if horse_races_game.stage == "betting":
                        if horse_races_game.start_race(pygame.time.get_ticks()):
                            audio.play_sound("button_click")
                            start_horse_race_music()
                            career_event_has_activity = True
                    elif horse_races_game.stage == "results":
                        if horse_races_game.prepare_next_race():
                            audio.play_sound("button_click")

                elif (
                        horse_action == HORSE_RACES_ACTION_RETURN
                        and horse_races_game.stage != "racing"
                ):
                    audio.play_sound("button_click")
                    stop_horse_race_music(300)
                    finish_horse_races_session()

        elif current_state == STATE_FARO:

            if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button in (1, 3)
                    and game_mouse_pos is not None
            ):
                faro_action = get_faro_action(game_mouse_pos, event.button, faro_game)
                is_right_click = (event.button == 3)

                if faro_action == FARO_ACTION_CHIP_10:
                    faro_chip_value = 10
                    audio.play_sound("button_click")

                elif faro_action == FARO_ACTION_CHIP_50:
                    faro_chip_value = 50
                    audio.play_sound("button_click")

                elif faro_action == FARO_ACTION_CHIP_100:
                    faro_chip_value = 100
                    audio.play_sound("button_click")

                elif faro_action == FARO_ACTION_CHIP_500:
                    faro_chip_value = 500
                    audio.play_sound("button_click")

                elif faro_action == FARO_ACTION_CLEAR_BETS:
                    if faro_game.clear_bets():
                        audio.play_sound("poker_chips_1")

                elif (
                        faro_action is not None
                        and faro_action.startswith(FARO_ACTION_BET_RANK_PREFIX)
                ):
                    rank = faro_action[len(FARO_ACTION_BET_RANK_PREFIX):]
                    if is_right_click:
                        if faro_game.remove_bet(rank, faro_chip_value):
                            audio.play_sound("poker_chips_1")
                    else:
                        if faro_game.place_bet(rank, faro_chip_value):
                            audio.play_sound("poker_chips_1")

                elif (
                        faro_action == FARO_ACTION_DEAL
                        and event.button == 1
                        and not faro_game.session_complete
                ):
                    if faro_game.deal_turn():
                        net = faro_game.last_profit - faro_game.last_loss - faro_game.last_doublet_loss
                        if net: rate_house_game("faro", net)
                        audio.play_sound("card_draw")
                        if faro_game.turns_dealt > 0 and faro_game.wagered_total > 0:
                            career_event_has_activity = True

                elif (
                        faro_action == FARO_ACTION_RETURN
                        and event.button == 1
                ):
                    audio.play_sound("button_click")
                    claim_faro_session_result()
                    if current_game_mode == "free":
                        finish_free_play_sandbox()
                        current_state = STATE_FREE_PLAY_SELECT
                    else:
                        current_state = STATE_CAREER_EVENT_SELECT

        elif current_state == STATE_FIVE_O_POKER:

            if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):
                five_o_action = get_five_o_action(
                    game_mouse_pos,
                    five_o_poker_game
                )

                if five_o_action == "ui_click":
                    audio.play_sound("button_click")

                elif five_o_action == FIVE_O_ACTION_RETURN:
                    audio.play_sound("button_click")
                    finish_five_o_poker_session()

                elif five_o_action == FIVE_O_ACTION_NEXT_HAND:
                    if five_o_poker_game.start_hand():
                        audio.play_sound("card_shuffle")

                elif (
                        five_o_action is not None
                        and five_o_action.startswith(FIVE_O_ACTION_COLUMN_PREFIX)
                ):
                    try:
                        column_index = int(
                            five_o_action[len(FIVE_O_ACTION_COLUMN_PREFIX):]
                        )
                    except ValueError:
                        column_index = -1
                    if five_o_poker_game.place_player_card(column_index):
                        audio.play_sound("card_move")

                elif five_o_action == FIVE_O_ACTION_CHECK:
                    if five_o_poker_game.player_check():
                        audio.play_sound("poker_check")

                elif five_o_action == FIVE_O_ACTION_BET:
                    if five_o_poker_game.player_bet():
                        play_texas_holdem_chip_sound()

                elif five_o_action == FIVE_O_ACTION_CALL:
                    if five_o_poker_game.player_call():
                        play_texas_holdem_chip_sound()

                elif five_o_action == FIVE_O_ACTION_FOLD:
                    if five_o_poker_game.player_fold():
                        audio.play_sound("button_click")

        elif current_state == STATE_BLIND_MANS_BLUFF:

            if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):
                bluff_action = get_blind_mans_bluff_action(
                    game_mouse_pos,
                    blind_mans_bluff_game
                )

                if bluff_action == BLUFF_ACTION_RETURN:
                    audio.play_sound("button_click")
                    finish_blind_mans_bluff_session()

                elif bluff_action == BLUFF_ACTION_NEXT_HAND:
                    if blind_mans_bluff_game.start_hand():
                        audio.play_sound("card_shuffle")

                elif bluff_action == BLUFF_ACTION_CHECK:
                    if blind_mans_bluff_game.player_check():
                        audio.play_sound("poker_check")

                elif bluff_action == BLUFF_ACTION_BET:
                    bluff_bet_amount = get_blind_mans_bluff_bet_amount(
                        blind_mans_bluff_game
                    )
                    if blind_mans_bluff_game.player_bet(bluff_bet_amount):
                        play_texas_holdem_chip_sound()

                elif bluff_action == BLUFF_ACTION_RAISE:
                    amount = get_blind_mans_bluff_bet_amount(blind_mans_bluff_game)
                    if blind_mans_bluff_game.player_raise(amount):
                        play_texas_holdem_chip_sound()

                elif bluff_action == BLUFF_ACTION_CALL:
                    if blind_mans_bluff_game.player_call():
                        play_texas_holdem_chip_sound()

                elif bluff_action == BLUFF_ACTION_FOLD:
                    if blind_mans_bluff_game.player_fold():
                        audio.play_sound("button_click")

        elif current_state == STATE_CRAZY_EIGHTS:

            if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
            ):
                crazy_action = get_crazy_eights_action(
                    menu_mouse_pos,
                    crazy_eights_game
                )

                if crazy_action is not None:
                    action_name, action_value = crazy_action

                    if action_name == CRAZY_EIGHTS_ACTION_RETURN:
                        audio.play_sound("button_click")
                        if current_game_mode == "free":
                            finish_free_play_sandbox()
                            current_state = STATE_FREE_PLAY_SELECT
                        else:
                            current_state = STATE_CAREER_EVENT_SELECT

                    elif action_name == CRAZY_EIGHTS_ACTION_CONTINUE:
                        audio.play_sound("button_click")
                        claim_crazy_eights_result()
                        if current_game_mode == "free":
                            finish_free_play_sandbox()
                            current_state = STATE_FREE_PLAY_SELECT
                        else:
                            current_state = STATE_CAREER_EVENT_SELECT

                    elif action_name == CRAZY_EIGHTS_ACTION_DRAW:
                        if crazy_eights_game.draw_player_card():
                            audio.play_sound("card_draw")

                    elif action_name == CRAZY_EIGHTS_ACTION_CARD:
                        result = crazy_eights_game.play_player_card(
                            action_value
                        )
                        if result in ("played", "choose_suit"):
                            audio.play_sound("card_move")

                    elif action_name == CRAZY_EIGHTS_ACTION_SUIT:
                        if crazy_eights_game.choose_player_suit(
                                action_value
                        ):
                            audio.play_sound("card_move")

        elif current_state == STATE_BANGO:

            if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
            ):
                bango_action = get_bango_action(
                    menu_mouse_pos,
                    bango_game
                )

                if bango_action == BANGO_ACTION_RETURN:
                    audio.play_sound("button_click")
                    if current_game_mode == "free":
                        finish_free_play_sandbox()
                        current_state = STATE_FREE_PLAY_SELECT
                    else:
                        current_state = STATE_CAREER_EVENT_SELECT

                elif bango_action == BANGO_ACTION_CONTINUE:
                    audio.play_sound("button_click")
                    claim_bango_result()
                    if current_game_mode == "free":
                        finish_free_play_sandbox()
                        current_state = STATE_FREE_PLAY_SELECT
                    else:
                        current_state = STATE_CAREER_EVENT_SELECT

                elif bango_action == BANGO_ACTION_CALL:
                    if bango_game.call_next():
                        audio.play_sound("card_draw")

        elif current_state == STATE_SCORE_FOUR:

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and score_four_game.rating_info_open:
                score_four_game.rating_info_open = False
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and game_mouse_pos is not None:
                from score_four_ui import handle_rating_info_click
                if handle_rating_info_click(game_mouse_pos, score_four_game):
                    audio.play_sound("button_click")
                    continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and game_mouse_pos is not None:
                from score_four_ui import LAYOUT_RECT, toggle_layout, play_control_sound
                if not score_four_game.difficulty_menu and LAYOUT_RECT.collidepoint(game_mouse_pos):
                    toggle_layout(score_four_game)
                    play_control_sound(audio, "select")
                    continue

            # ----------------------------
            # TEMP DEBUG: complete training
            # ----------------------------

            if (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_F6
            ):
                score_four_game.puzzles_completed = 3
                score_four_game.round_complete = True
                score_four_game.session_complete = True

            if (

                    event.type

                    == pygame.MOUSEBUTTONDOWN

                    and event.button == 1

            ):

                # ==========================================

                # Training complete

                # ==========================================

                if (
                        score_four_game.mode == "solo"
                        and score_four_game.session_complete
                ):

                    if score_four_complete_rect.collidepoint(

                            menu_mouse_pos

                    ):

                        settle_score_four_session_result()

                        audio.play_sound(

                            "button_click"

                        )

                        if current_game_mode == "free":
                            finish_free_play_sandbox()
                            current_state = STATE_FREE_PLAY_SELECT
                        else:
                            current_state = STATE_CAREER_EVENT_SELECT

                    continue

                # ==========================================
                # Competitive match complete
                # ==========================================

                if (
                        score_four_game.mode == "competitive"
                        and score_four_game.match_complete
                ):

                    if (
                            score_four_match_continue_rect
                                    .collidepoint(
                                menu_mouse_pos
                            )
                    ):

                        settle_score_four_session_result()

                        audio.play_sound(
                            "button_click"
                        )

                        if current_game_mode == "free":
                            finish_free_play_sandbox()
                            current_state = STATE_FREE_PLAY_SELECT
                        else:
                            current_state = STATE_CAREER_EVENT_SELECT

                    continue

                # ==========================================
                # Competitive round result input lock
                # ==========================================

                if (
                        score_four_game.mode == "competitive"
                        and score_four_game.round_complete
                ):
                    from score_four_ui import ROUND_CONTINUE_RECT
                    if game_mouse_pos is not None and ROUND_CONTINUE_RECT.collidepoint(game_mouse_pos):
                        if score_four_game.continue_competitive_round():
                            audio.play_sound("button_click")
                    continue

                # ------------------------------------------
                # Number tiles
                # ------------------------------------------

                reset_rect = globals().get("score_four_reset_rect")
                if reset_rect is not None and menu_mouse_pos is not None and reset_rect.collidepoint(menu_mouse_pos):
                    if score_four_game.reset_current_puzzle(): play_control_sound(audio, "reset")
                    continue

                clicked_number = False

                for index, rect in enumerate(
                        score_four_number_rects
                ):

                    if rect.collidepoint(
                            menu_mouse_pos
                    ):
                        score_four_game.select_number(
                            index
                        )

                        if not score_four_game.round_complete:
                            play_control_sound(audio, "select")
                        clicked_number = True
                        break

                if clicked_number:
                    pass

                # ------------------------------------------
                # Operators
                # ------------------------------------------

                else:

                    clicked_operator = False

                    for (
                            operator_id,
                            rect
                    ) in score_four_operator_rects.items():

                        if rect.collidepoint(
                                menu_mouse_pos
                        ):
                            score_four_game.select_operator(
                                operator_id
                            )

                            play_control_sound(audio, "operator")
                            clicked_operator = True
                            break

                    if clicked_operator:
                        pass

                    elif (
                            score_four_game.solo_hint_available()
                            and score_four_hint_rect.collidepoint(
                        menu_mouse_pos
                    )
                    ):

                        if score_four_game.request_solo_hint():
                            play_control_sound(audio, "hint")

                    # --------------------------------------
                    # Undo
                    # --------------------------------------

                    elif score_four_undo_rect.collidepoint(
                            menu_mouse_pos
                    ):

                        score_four_game.undo()
                        play_control_sound(audio, "undo")

                    # --------------------------------------
                    # Exit
                    # --------------------------------------

                    elif score_four_exit_rect.collidepoint(
                            menu_mouse_pos
                    ):

                        if current_game_mode == "free":
                            finish_free_play_sandbox()
                            current_state = STATE_FREE_PLAY_SELECT
                        else:
                            current_state = STATE_CAREER_EVENT_SELECT

        elif current_state == STATE_ACHIEVEMENTS:

            if event.type == pygame.MOUSEWHEEL:
                achievements_scroll_y = clamp_achievements_scroll(
                    achievements_scroll_y - event.y * 78
                )

            elif (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
                    and ACHIEVEMENTS_BACK_RECT.collidepoint(game_mouse_pos)
            ):
                audio.play_sound("button_click")
                current_state = STATE_MENU

        elif current_state == STATE_HOW_TO_PLAY:

            if event.type == pygame.MOUSEWHEEL:
                if game_mouse_pos is not None and HELP_NAV_PANEL_RECT.collidepoint(game_mouse_pos):
                    help_nav_scroll = max(
                        0,
                        min(
                            help_nav_max_scroll,
                            help_nav_scroll - event.y * HELP_NAV_SCROLL_STEP
                        )
                    )
                elif game_mouse_pos is not None and HELP_CONTENT_RECT.collidepoint(game_mouse_pos):
                    help_content_scroll = max(
                        0,
                        min(
                            help_content_max_scroll,
                            help_content_scroll - event.y * HELP_CONTENT_SCROLL_STEP
                        )
                    )

            elif (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):

                click_handled = False

                for category_id, rect in help_category_rects.items():
                    if rect.collidepoint(game_mouse_pos):
                        audio.play_sound("button_click")

                        was_expanded = help_expanded_categories.get(
                            category_id,
                            False
                        )

                        for other_category_id in help_expanded_categories:
                            help_expanded_categories[other_category_id] = False

                        if not was_expanded:
                            help_expanded_categories[category_id] = True

                        click_handled = True
                        break

                if not click_handled:
                    for page_id, rect in help_page_rects.items():
                        if rect.collidepoint(game_mouse_pos):
                            audio.play_sound("button_click")
                            help_current_page = page_id
                            help_content_scroll = 0
                            click_handled = True
                            break

                if (
                        not click_handled
                        and how_to_play_back_rect.collidepoint(game_mouse_pos)
                ):
                    audio.play_sound("button_click")
                    current_state = STATE_MENU

        # ==========================================
        # CAREER SUB-PAGES
        # ==========================================

        elif current_state == STATE_CAREER_JOBS:

            if (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
            ):

                job_clicked = None

                for job_id, rect in (
                        career_job_option_rects.items()
                ):

                    if rect.collidepoint(
                            game_mouse_pos
                    ):
                        job_clicked = job_id
                        break

                if job_clicked is not None:

                    job_data = (
                        CAREER_JOBS[
                            job_clicked
                        ]
                    )

                    required_rating = (
                        job_data[
                            "required_rating"
                        ]
                    )

                    if (
                            career_rating
                            >= required_rating
                    ):
                        audio.play_sound(
                            "button_click"
                        )

                        old_job = (
                            career_job
                        )

                        career_job = (
                            job_clicked
                        )

                        refresh_future_work_tasks()

                        if old_job != career_job:
                            if career_job not in career_fan_rewarded_jobs:
                                award_career_fans(
                                    fan_bonus_for_job(
                                        job_data.get("required_rating", 0),
                                        job_data.get("pay", 0)
                                    ),
                                    f"New job: {job_data.get('name', career_job)}"
                                )
                                career_fan_rewarded_jobs.add(career_job)

                            add_career_news(
                                (
                                    f"{player_name.upper()} "
                                    f"TAKES NEW SIDE JOB"
                                ),
                                (
                                    f"{player_name} has accepted work as "
                                    f"{get_career_job_name()}. "
                                    f"Sources close to the situation say "
                                    f"the decision was largely financial."
                                ),
                                "job"
                            )

                        auto_save_career()

                elif career_subpage_back_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    current_state = (
                        STATE_CAREER_HUB
                    )

        elif (
                current_state
                == STATE_CAREER_LEADERBOARD_BIO
        ):

            if (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
            ):

                if career_subpage_back_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    current_state = (
                        STATE_CAREER_LEADERBOARDS
                    )

        elif current_state == STATE_CAREER_LEADERBOARDS:

            if (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
            ):

                total_pages = (
                    get_career_leaderboard_total_pages(
                        rating_key=career_leaderboard_rating_key
                    )
                )

                bio_clicked = False
                rating_filter_clicked = False

                # ==========================================
                # Rating category selector
                # ==========================================

                if career_leaderboard_rating_prev_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    current_index = RATING_KEYS.index(
                        career_leaderboard_rating_key
                    )

                    career_leaderboard_rating_key = RATING_KEYS[
                        (current_index - 1)
                        % len(RATING_KEYS)
                    ]

                    career_leaderboard_page = 0
                    rating_filter_clicked = True

                elif career_leaderboard_rating_next_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    current_index = RATING_KEYS.index(
                        career_leaderboard_rating_key
                    )

                    career_leaderboard_rating_key = RATING_KEYS[
                        (current_index + 1)
                        % len(RATING_KEYS)
                    ]

                    career_leaderboard_page = 0
                    rating_filter_clicked = True

                # ==========================================
                # Bio links
                # ==========================================

                if not rating_filter_clicked:
                    for bio_rect, entry in (
                            career_leaderboard_bio_rects
                    ):

                        if bio_rect.collidepoint(
                                game_mouse_pos
                        ):
                            audio.play_sound(
                                "button_click"
                            )

                            selected_leaderboard_entry = (
                                entry
                            )

                            current_state = (
                                STATE_CAREER_LEADERBOARD_BIO
                            )

                            bio_clicked = True

                            break

                # Previous pagination logic continues below.

                # ==========================================
                # Previous Page
                # ==========================================

                if (
                        not bio_clicked
                        and not rating_filter_clicked
                        and career_leaderboard_page > 0
                        and career_leaderboard_prev_rect.collidepoint(
                    game_mouse_pos
                )
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    career_leaderboard_page -= 1

                # ==========================================
                # Next Page
                # ==========================================

                elif (
                        not bio_clicked
                        and not rating_filter_clicked
                        and career_leaderboard_page
                        < total_pages - 1
                        and career_leaderboard_next_rect.collidepoint(
                    game_mouse_pos
                )
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    career_leaderboard_page += 1

                # ==========================================
                # Return to Career
                # ==========================================

                elif (
                        not bio_clicked
                        and not rating_filter_clicked
                        and career_subpage_back_rect.collidepoint(
                    game_mouse_pos
                )
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    current_state = (
                        STATE_CAREER_HUB
                    )


        elif current_state == STATE_CAREER_NEWS:

            if (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
            ):

                total_pages = (
                    get_career_news_total_pages()
                )

                # ==========================================
                # Previous
                # ==========================================

                if (
                        career_news_page > 0
                        and career_news_prev_rect.collidepoint(
                    game_mouse_pos
                )
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    career_news_page -= 1

                # ==========================================
                # Next
                # ==========================================

                elif (
                        career_news_page
                        < total_pages - 1
                        and career_news_next_rect.collidepoint(
                    game_mouse_pos
                )
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    career_news_page += 1

                # ==========================================
                # Return
                # ==========================================

                elif career_subpage_back_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    current_state = (
                        STATE_CAREER_HUB
                    )

        elif current_state == STATE_CAREER_EVENT:

            event_id = (
                career_event_entry.get("event_id")
                if isinstance(career_event_entry, dict)
                else None
            )

            if event_id == "press_interview_01":
                if (
                        event.type == pygame.MOUSEBUTTONDOWN
                        and event.button == 1
                        and game_mouse_pos is not None
                ):
                    for answer_index, answer_rect in enumerate(
                            career_interview_answer_rects
                    ):
                        if answer_rect.collidepoint(game_mouse_pos):
                            audio.play_sound("button_click")
                            handle_press_interview_answer(answer_index)
                            break

            elif event_id == "sign_autographs_01":
                if (
                        event.type == pygame.MOUSEBUTTONDOWN
                        and event.button == 1
                        and game_mouse_pos is not None
                ):
                    if AUTOGRAPH_CLEAR_RECT.collidepoint(game_mouse_pos):
                        audio.play_sound("button_click")
                        career_autograph_event.clear_trace()
                        career_autograph_last_change = 0

                    elif AUTOGRAPH_SUBMIT_RECT.collidepoint(game_mouse_pos):
                        audio.play_sound("button_click")
                        if len(career_autograph_event.trace_points) >= 2:
                            handle_sign_autograph_submit()
                        else:
                            career_autograph_event.feedback = (
                                "Trace the autograph before signing it."
                            )

                    else:
                        if career_autograph_event.begin_trace(game_mouse_pos):
                            career_autograph_last_change = 0

                elif (
                        event.type == pygame.MOUSEMOTION
                        and game_mouse_pos is not None
                        and career_autograph_event.drawing
                ):
                    career_autograph_event.add_trace_point(game_mouse_pos)

                elif (
                        event.type == pygame.MOUSEBUTTONUP
                        and event.button == 1
                ):
                    career_autograph_event.end_trace()

            elif event_id == "head_to_head_01":
                if (
                        event.type == pygame.MOUSEBUTTONDOWN
                        and event.button == 1
                        and game_mouse_pos is not None
                ):
                    head_to_head_action = get_head_to_head_selection_action(
                        game_mouse_pos,
                        len(head_to_head_opponents),
                    )

                    if head_to_head_action is not None:
                        action_name, action_value = head_to_head_action

                        if action_name == "opponent":
                            audio.play_sound("button_click")
                            head_to_head_selected_index = action_value

                        elif action_name == "start":
                            if head_to_head_selected_index is not None:
                                audio.play_sound("button_click")
                                begin_selected_head_to_head_race()

                        elif action_name == "return":
                            audio.play_sound("button_click")
                            current_state = STATE_CAREER_HUB

            elif (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
                    and career_subpage_back_rect.collidepoint(game_mouse_pos)
            ):
                audio.play_sound("button_click")
                current_state = STATE_CAREER_HUB

        # ==================================================
        # CAREER EVENT SUMMARY
        # ==================================================

        elif (
                current_state
                == STATE_CAREER_EVENT_SUMMARY
        ):

            if (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):

                if (
                        career_event_summary_continue_rect
                                .collidepoint(
                            game_mouse_pos
                        )
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    was_debug_event = (
                        isinstance(career_event_entry, dict)
                        and career_event_entry.get("debug", False)
                    )

                    if not was_debug_event:
                        advance_career_day(
                            completed=True
                        )

                    career_event_entry = None
                    career_event_has_activity = False

                    career_event_summary_title = ""
                    career_event_summary_lines = []

                    current_state = (
                        STATE_CAREER_HUB
                    )

        elif current_state == STATE_CAREER_EVENT_SELECT:

            if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and menu_mouse_pos is not None
            ):

                game_clicked = False

                for (rect, game_id) in career_event_card_rects:

                    if rect.collidepoint(menu_mouse_pos):
                        game_clicked = True

                        if not is_game_unlocked(game_id):
                            break

                        if (
                                career_event_entry is not None
                                and career_event_entry.get("activity_type") == CAREER_ACTIVITY_ARCADE_NIGHT
                                and game_id in ARCADE_COMING_SOON_GAME_IDS
                        ):
                            audio.play_sound("button_click")
                            set_arcade_status_message(f"{ARCADE_MACHINE_NAMES.get(game_id, game_id)} is coming soon.")
                            break

                        audio.play_sound("button_click")

                        if game_id == "score_four":
                            current_state = STATE_SCORE_FOUR_MODE_SELECT

                        elif game_id == "crazy_eights":
                            start_crazy_eights_session()

                        elif game_id == "bango":
                            start_bango_session()

                        elif game_id == "blackjack":
                            blackjack_selected_bet_percentage = None
                            blackjack_bet_dropdown_open = False
                            blackjack_session_net = 0
                            blackjack_session_rating_change = 0
                            blackjack_dealer_npc = get_random_blackjack_dealer()
                            current_state = STATE_BLACKJACK_BET

                        elif game_id == "roulette":
                            roulette_session_net = 0
                            roulette_game.reset_round()
                            current_state = STATE_ROULETTE

                        elif game_id == "horse_races":
                            start_horse_races_session()

                        elif game_id == "faro":
                            start_faro_session()

                        elif game_id == "five_o_poker":
                            if not start_five_o_poker_session():
                                print("Not enough cash to enter Five-O Poker.")

                        elif game_id == "blind_mans_bluff":
                            if not start_blind_mans_bluff_session():
                                print("Not enough cash to enter Blind Man's Bluff.")

                        elif game_id == "texas_holdem":
                            current_state = STATE_TEXAS_HOLDEM_BUY_IN

                        elif game_id == "seven_card_stud":
                            current_state = STATE_SEVEN_CARD_STUD_BUY_IN

                        elif game_id == "five_card_draw":
                            current_state = STATE_FIVE_CARD_DRAW_BUY_IN

                        elif game_id == "king_pong":
                            open_king_pong_opponent_select(refresh=True)

                        elif game_id == "battle_bosses":
                            open_battle_bosses_opponent_select(refresh=True)

                        elif game_id == "token_exchange":
                            open_arcade_token_exchange()

                        elif game_id == "prize_counter":
                            arcade_selected_prize_index = 0
                            current_state = STATE_ARCADE_PRIZE_COUNTER

                        else:
                            print("Career game not implemented yet:", game_id)

                        break

                if not game_clicked:

                    if career_event_return_rect.collidepoint(menu_mouse_pos):
                        audio.play_sound("button_click")
                        store_event_progress(career_event_entry, globals())
                        auto_save_career()
                        current_state = STATE_CAREER_HUB

                    elif (
                            career_event_end_rect.collidepoint(menu_mouse_pos)
                            and career_event_has_activity
                    ):
                        audio.play_sound("button_click")
                        publish_career_event_news()
                        build_career_event_summary()
                        current_state = STATE_CAREER_EVENT_SUMMARY

        elif current_state == STATE_KING_PONG_OPPONENT_SELECT:

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                audio.play_sound("button_click")
                current_state = STATE_CAREER_EVENT_SELECT

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and menu_mouse_pos is not None:
                opponent_clicked = False

                for opponent_index, rect in enumerate(king_pong_opponent_rects):
                    if (
                            opponent_index < len(king_pong_opponent_choices)
                            and rect.collidepoint(menu_mouse_pos)
                    ):
                        king_pong_selected_opponent_index = opponent_index
                        audio.play_sound("button_click")
                        opponent_clicked = True
                        break

                if not opponent_clicked:
                    if king_pong_opponent_back_rect.collidepoint(menu_mouse_pos):
                        audio.play_sound("button_click")
                        current_state = STATE_CAREER_EVENT_SELECT

                    elif king_pong_opponent_tokens_rect.collidepoint(menu_mouse_pos):
                        audio.play_sound("button_click")
                        open_arcade_token_exchange("king_pong")

                    elif king_pong_opponent_play_rect.collidepoint(menu_mouse_pos):
                        if get_selected_king_pong_choice() is None:
                            set_arcade_status_message("Choose a rival first.")
                        elif int(arcade_state.get("tokens", 0)) < get_machine_cost("king_pong"):
                            set_arcade_status_message("Not enough tokens. Buy more to play.")
                            open_arcade_token_exchange("king_pong")
                        else:
                            audio.play_sound("button_click")
                            start_king_pong_session()

        elif current_state == STATE_BATTLE_BOSSES_OPPONENT_SELECT:

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                audio.play_sound("button_click")
                current_state = STATE_CAREER_EVENT_SELECT

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and menu_mouse_pos is not None:
                choice_clicked = False
                for choice_index, rect in enumerate(battle_bosses_choice_rects):
                    if (
                            choice_index < len(battle_bosses_opponent_choices)
                            and rect.collidepoint(menu_mouse_pos)
                    ):
                        battle_bosses_selected_choice_index = choice_index
                        audio.play_sound("button_click")
                        choice_clicked = True
                        break

                if not choice_clicked:
                    if battle_bosses_back_rect.collidepoint(menu_mouse_pos):
                        audio.play_sound("button_click")
                        current_state = STATE_CAREER_EVENT_SELECT
                    elif battle_bosses_refresh_rect.collidepoint(menu_mouse_pos):
                        audio.play_sound("button_click")
                        open_battle_bosses_opponent_select(refresh=True)
                        set_arcade_status_message("Battle Bosses rival squads rerolled.")
                    elif battle_bosses_future_play_rect.collidepoint(menu_mouse_pos):
                        if get_selected_battle_bosses_choice() is None:
                            set_arcade_status_message("Choose a rival squad first.")
                        elif int(arcade_state.get("tokens", 0)) < get_machine_cost("battle_bosses"):
                            set_arcade_status_message("Not enough tokens. Buy more to enter the arena.")
                            open_arcade_token_exchange("battle_bosses")
                        else:
                            audio.play_sound("button_click")
                            start_battle_bosses_session()

        elif current_state == STATE_ARCADE_TOKEN_EXCHANGE:

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and menu_mouse_pos is not None:
                if arcade_token_exchange_back_rect.collidepoint(menu_mouse_pos):
                    audio.play_sound("button_click")
                    if arcade_pending_launch_game_id == "king_pong":
                        arcade_pending_launch_game_id = None
                        current_state = STATE_KING_PONG_OPPONENT_SELECT
                    elif arcade_pending_launch_game_id == "battle_bosses":
                        arcade_pending_launch_game_id = None
                        current_state = STATE_BATTLE_BOSSES_OPPONENT_SELECT
                    else:
                        current_state = STATE_CAREER_EVENT_SELECT
                elif arcade_token_exchange_continue_rect.collidepoint(menu_mouse_pos):
                    audio.play_sound("button_click")
                    if arcade_pending_launch_game_id == "king_pong":
                        if int(arcade_state.get("tokens", 0)) >= get_machine_cost("king_pong"):
                            start_king_pong_session()
                        else:
                            set_arcade_status_message("Buy enough tokens to play King Pong.")
                    elif arcade_pending_launch_game_id == "battle_bosses":
                        if int(arcade_state.get("tokens", 0)) >= get_machine_cost("battle_bosses"):
                            start_battle_bosses_session()
                        else:
                            set_arcade_status_message("Buy enough tokens to play Battle Bosses.")
                    else:
                        current_state = STATE_CAREER_EVENT_SELECT
                else:
                    for package_index, rect in arcade_token_package_rects.items():
                        if rect.collidepoint(menu_mouse_pos):
                            package = ARCADE_TOKEN_PACKAGES[package_index]
                            success, new_state, new_cash, message = buy_token_package(arcade_state, career_cash, package['id'])
                            arcade_state = new_state
                            if success:
                                career_cash = new_cash
                                auto_save_career()
                            set_arcade_status_message(message)
                            audio.play_sound("button_click")
                            break

        elif current_state == STATE_ARCADE_PRIZE_COUNTER:

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and menu_mouse_pos is not None:
                if arcade_prize_back_rect.collidepoint(menu_mouse_pos):
                    audio.play_sound("button_click")
                    current_state = STATE_CAREER_EVENT_SELECT
                elif arcade_prize_trophy_room_rect.collidepoint(menu_mouse_pos):
                    audio.play_sound("button_click")
                    current_state = STATE_ARCADE_TROPHY_ROOM
                elif arcade_prize_buy_rect.collidepoint(menu_mouse_pos):
                    prize = ARCADE_PRIZE_CATALOG[arcade_selected_prize_index]
                    success, new_state, message, _prize = redeem_prize(arcade_state, prize['id'])
                    arcade_state = new_state
                    if success:
                        auto_save_career()
                    set_arcade_status_message(message)
                    audio.play_sound("button_click")
                else:
                    for prize_index, rect in arcade_prize_card_rects.items():
                        if rect.collidepoint(menu_mouse_pos):
                            arcade_selected_prize_index = prize_index
                            audio.play_sound("button_click")
                            break

        elif current_state == STATE_ARCADE_TROPHY_ROOM:

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and menu_mouse_pos is not None:
                if arcade_trophy_room_back_rect.collidepoint(menu_mouse_pos):
                    audio.play_sound("button_click")
                    current_state = STATE_ARCADE_PRIZE_COUNTER

        elif current_state == STATE_KING_PONG:

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if not king_pong_game.finished:
                        king_pong_game.forfeit()
                    finish_king_pong_session()
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if not king_pong_game.finished:
                        king_pong_game.forfeit()
                    finish_king_pong_session()
                elif event.key == pygame.K_SPACE and king_pong_game.finished:
                    start_king_pong_session()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and menu_mouse_pos is not None:
                if king_pong_return_rect.collidepoint(menu_mouse_pos):
                    audio.play_sound("button_click")
                    if not king_pong_game.finished:
                        king_pong_game.forfeit()
                    finish_king_pong_session()

        elif current_state == STATE_BATTLE_BOSSES:

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if not battle_bosses_game.finished:
                        battle_bosses_game.forfeit()
                    finish_battle_bosses_session()
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if battle_bosses_game.finished:
                        finish_battle_bosses_session()
                elif event.key == pygame.K_SPACE and battle_bosses_game.finished:
                    start_battle_bosses_session()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and menu_mouse_pos is not None:
                if battle_bosses_quit_rect.collidepoint(menu_mouse_pos):
                    audio.play_sound("button_click")
                    if not battle_bosses_game.finished:
                        battle_bosses_game.forfeit()
                    finish_battle_bosses_session()

        elif current_state == STATE_CAREER_REAL_ESTATE:

            if (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
            ):

                residence_clicked = None

                for residence_id, rect in (
                        career_residence_option_rects.items()
                ):

                    if rect.collidepoint(
                            game_mouse_pos
                    ):
                        residence_clicked = (
                            residence_id
                        )

                        break

                if residence_clicked is not None:

                    residence_data = (
                        CAREER_RESIDENCES[
                            residence_clicked
                        ]
                    )

                    price = (
                        residence_data[
                            "price"
                        ]
                    )

                    # ==========================================
                    # Already owned
                    # ==========================================

                    if (
                            residence_clicked
                            in career_owned_residences
                    ):
                        audio.play_sound(
                            "button_click"
                        )

                        career_residence = (
                            residence_clicked
                        )

                        auto_save_career()

                    # ==========================================
                    # Purchase
                    # ==========================================

                    elif (
                            career_cash
                            >= price
                    ):
                        audio.play_sound(
                            "button_click"
                        )

                        career_cash -= price

                        career_owned_residences.append(
                            residence_clicked
                        )

                        career_residence = (
                            residence_clicked
                        )

                        fan_bonus = award_career_fans(
                            fan_bonus_for_residence(price),
                            f"New residence: {get_career_residence_name()}"
                        )

                        add_career_news(
                            (
                                f"{player_name.upper()} "
                                f"PURCHASES "
                                f"{get_career_residence_name().upper()}"
                            ),
                            (
                                f"The competitive Solitaire player "
                                f"has reportedly moved into "
                                f"{get_career_residence_name()} "
                                f"after completing the purchase."
                            ),
                            "residence"
                        )

                        auto_save_career()

                elif career_subpage_back_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    current_state = (
                        STATE_CAREER_HUB
                    )

        # ==========================================
        # DIFFICULTY
        # ==========================================

        elif current_state == STATE_DIFFICULTY:

            if (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
            ):

                selected_difficulty = None

                if difficulty_easy_rect.collidepoint(
                        game_mouse_pos
                ):
                    selected_difficulty = "easy"

                elif difficulty_normal_rect.collidepoint(
                        game_mouse_pos
                ):
                    selected_difficulty = "normal"

                elif difficulty_hard_rect.collidepoint(
                        game_mouse_pos
                ):
                    selected_difficulty = "hard"

                elif difficulty_very_hard_rect.collidepoint(
                        game_mouse_pos
                ):
                    selected_difficulty = (
                        "very_hard"
                    )

                elif difficulty_extreme_rect.collidepoint(
                        game_mouse_pos
                ):
                    selected_difficulty = (
                        "extreme"
                    )


                elif difficulty_back_rect.collidepoint(

                        game_mouse_pos

                ):

                    audio.play_sound(

                        "button_click"

                    )

                    if current_game_mode == "career":

                        current_state = (

                            STATE_CAREER_HUB

                        )


                    else:

                        if current_game_mode == "free":
                            finish_free_play_sandbox()
                            current_state = STATE_FREE_PLAY_SELECT
                        else:
                            current_state = STATE_MODE_SELECT

                if selected_difficulty is not None:
                    audio.play_sound(
                        "button_click"
                    )

                    game.set_difficulty(
                        selected_difficulty
                    )


                    game.new_game()

                    current_state = (
                        STATE_PLAYING
                    )

        elif current_state == STATE_OPTIONS:

            # ==================================================
            # Mouse down
            # ==================================================

            if (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):

                # ----------------------------
                # Music mode
                # ----------------------------

                if music_instrumental_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    audio.set_music_mode(
                        "instrumental"
                    )

                elif music_ambient_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    audio.set_music_mode(
                        "ambient"
                    )

                elif music_off_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    audio.set_music_mode(
                        "off"
                    )

                # ----------------------------
                # Music volume
                # ----------------------------

                elif music_slider_rect.collidepoint(
                        game_mouse_pos
                ):
                    music_slider_dragging = True

                    relative_x = (
                            game_mouse_pos[0]
                            - music_slider_rect.x
                    )

                    volume = (
                            relative_x
                            / music_slider_rect.width
                    )

                    volume = max(
                        0.0,
                        min(
                            1.0,
                            volume
                        )
                    )

                    audio.set_music_volume(
                        volume
                    )

                # ----------------------------
                # SFX volume
                # ----------------------------

                elif sfx_slider_rect.collidepoint(
                        game_mouse_pos
                ):
                    sfx_slider_dragging = True

                    relative_x = (
                            game_mouse_pos[0]
                            - sfx_slider_rect.x
                    )

                    volume = (
                            relative_x
                            / sfx_slider_rect.width
                    )

                    volume = max(
                        0.0,
                        min(
                            1.0,
                            volume
                        )
                    )

                    audio.set_sfx_volume(
                        volume
                    )

                    audio.play_sound(
                        "button_click"
                    )

                # ----------------------------
                # Double click
                # ----------------------------

                elif double_foundation_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    game.double_click_mode = (
                        "foundation"
                    )

                elif double_both_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    game.double_click_mode = (
                        "foundation_and_tableau"
                    )

                # ----------------------------
                # Solitaire deal mode
                # ----------------------------

                elif deal_random_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )
                    game.set_deal_mode(
                        "random"
                    )

                elif deal_verified_rect.collidepoint(
                        game_mouse_pos
                ):
                    if VERIFIED_DEALS_ENABLED:
                        audio.play_sound("button_click")
                        game.set_deal_mode("verified")

                # ----------------------------
                # Fullscreen
                # ----------------------------

                elif fullscreen_toggle_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    set_fullscreen_enabled(
                        not fullscreen_enabled
                    )

                # ----------------------------
                # Resolution
                # ----------------------------

                else:
                    resolution_clicked = False

                    for index, rect in enumerate(
                            resolution_rects
                    ):
                        if rect.collidepoint(
                                game_mouse_pos
                        ):
                            width, height = (
                                RESOLUTION_OPTIONS[
                                    index
                                ]
                            )

                            audio.play_sound(
                                "button_click"
                            )

                            set_window_size(
                                width,
                                height
                            )

                            resolution_clicked = True

                            break

                    # ----------------------------
                    # Back
                    # ----------------------------

                    if (
                            not resolution_clicked
                            and options_back_rect
                            .collidepoint(
                        game_mouse_pos
                    )
                    ):
                        audio.play_sound(
                            "button_click"
                        )

                        music_slider_dragging = False
                        sfx_slider_dragging = False

                        if options_return_state == STATE_CAREER_HUB:
                            save_career_from_hub()
                        current_state = options_return_state

            # ==================================================
            # Slider dragging
            # ==================================================

            elif (
                    event.type == pygame.MOUSEMOTION
                    and game_mouse_pos is not None
            ):

                # ----------------------------
                # Music volume
                # ----------------------------

                if music_slider_dragging:

                    relative_x = (
                            game_mouse_pos[0]
                            - music_slider_rect.x
                    )

                    volume = (
                            relative_x
                            / music_slider_rect.width
                    )

                    volume = max(
                        0.0,
                        min(
                            1.0,
                            volume
                        )
                    )

                    audio.set_music_volume(
                        volume
                    )

                # ----------------------------
                # SFX volume
                # ----------------------------

                elif sfx_slider_dragging:

                    relative_x = (
                            game_mouse_pos[0]
                            - sfx_slider_rect.x
                    )

                    volume = (
                            relative_x
                            / sfx_slider_rect.width
                    )

                    volume = max(
                        0.0,
                        min(
                            1.0,
                            volume
                        )
                    )

                    audio.set_sfx_volume(
                        volume
                    )

            # ==================================================
            # End slider dragging
            # ==================================================

            elif (
                    event.type
                    == pygame.MOUSEBUTTONUP
                    and event.button == 1
            ):

                music_slider_dragging = False
                sfx_slider_dragging = False

        # ==========================================
        # CUSTOMIZE
        # ==========================================

        elif current_state == STATE_CUSTOMIZE:

            if (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
            ):

                if debug_xp_rect.collidepoint(
                        game_mouse_pos
                ):
                    result = add_player_xp(
                        100
                    )

                    print(
                        "XP:",
                        result
                    )

                    audio.play_sound(
                        "button_click"
                    )

                # ----------------------------
                # Category tabs
                # ----------------------------

                elif customize_backgrounds_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    customize_category = (
                        CUSTOMIZE_BACKGROUNDS
                    )

                    customize_page = 0

                elif customize_felts_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    customize_category = (
                        CUSTOMIZE_FELTS
                    )

                    customize_page = 0

                elif customize_titles_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    customize_category = (
                        CUSTOMIZE_TITLES
                    )

                    customize_page = 0

                elif customize_cursors_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    customize_category = (
                        CUSTOMIZE_CURSORS
                    )

                    customize_page = 0

                # ----------------------------
                # Previous page
                # ----------------------------

                elif customize_prev_rect.collidepoint(
                        game_mouse_pos
                ):
                    if customize_page > 0:
                        audio.play_sound(
                            "button_click"
                        )

                        customize_page -= 1

                # ----------------------------
                # Next page
                # ----------------------------

                elif customize_next_rect.collidepoint(
                        game_mouse_pos
                ):
                    page_count = (
                        get_customize_page_count()
                    )

                    if (
                            customize_page
                            < page_count - 1
                    ):
                        audio.play_sound(
                            "button_click"
                        )

                        customize_page += 1

                # ----------------------------
                # Back
                # ----------------------------

                elif customize_back_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    if customize_return_state == STATE_CAREER_HUB:
                        save_career_from_hub()
                    current_state = customize_return_state

                # ----------------------------
                # Cosmetic items
                # ----------------------------

                else:
                    asset_ids = (
                        get_customize_asset_ids()
                    )

                    start_index = (
                            customize_page
                            * CUSTOMIZE_ITEMS_PER_PAGE
                    )

                    visible_ids = asset_ids[
                        start_index:
                        start_index
                        + CUSTOMIZE_ITEMS_PER_PAGE
                    ]

                    for index, rect in enumerate(
                            customize_item_rects
                    ):
                        if index >= len(
                                visible_ids
                        ):
                            break

                        if rect.collidepoint(
                                game_mouse_pos
                        ):
                            asset_id = (
                                visible_ids[index]
                            )

                            (
                                _,
                                _,
                                unlocked_ids,
                                _
                            ) = get_customize_data()

                            if asset_id in unlocked_ids:
                                audio.play_sound(
                                    "button_click"
                                )

                                equip_customize_item(
                                    asset_id
                                )

                            break

        # ==========================================
        # ROUND RECAP
        # ==========================================

        elif current_state == STATE_RECAP:

            if (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
            ):
                if recap_yes_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    # If this win earned levels,
                    # show them before returning
                    # to the main menu.
                    if (
                            last_progression_result
                            and last_progression_result[
                        "level_up_screens"
                    ]
                    ):
                        level_up_queue = list(
                            last_progression_result[
                                "level_up_screens"
                            ]
                        )

                        advance_level_up_screen()


                    else:

                        current_state = (

                            post_round_return_state

                        )

                elif recap_no_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    # Stay at the table and deal another hand. If the completed
                    # round earned one or more levels, show those screens first
                    # and then return directly to the fresh deal.
                    game.new_game()
                    post_round_return_state = STATE_PLAYING

                    if (
                            last_progression_result
                            and last_progression_result.get("level_up_screens")
                    ):
                        level_up_queue = list(
                            last_progression_result["level_up_screens"]
                        )
                        advance_level_up_screen()
                    else:
                        current_state = STATE_PLAYING


        # ==========================================
        # LEVEL UP
        # ==========================================

        elif current_state == STATE_LEVEL_UP:

            continue_level_up = (
                event.type == pygame.KEYDOWN
                and event.key in (
                    pygame.K_RETURN,
                    pygame.K_KP_ENTER,
                    pygame.K_SPACE,
                    pygame.K_ESCAPE,
                )
            )

            if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
                    and level_up_continue_rect.collidepoint(game_mouse_pos)
            ):
                continue_level_up = True

            if continue_level_up:
                audio.play_sound("button_click")
                advance_level_up_screen()


        # ==========================================
        # PROFILE
        # ==========================================

        elif current_state == STATE_PROFILE:

            # ==========================================
            # KEYBOARD INPUT
            # ==========================================

            if event.type == pygame.KEYDOWN:
                active_field = None
                if profile_name_active:
                    active_field = "name"
                elif profile_country_active:
                    active_field = "country"
                elif profile_age_active:
                    active_field = "age"
                elif profile_hometown_active:
                    active_field = "hometown"
                elif profile_bio_active:
                    active_field = "bio"

                if active_field is not None:
                    if event.key == pygame.K_BACKSPACE:
                        if active_field == "name":
                            profile_name_text = profile_name_text[:-1]
                        elif active_field == "country":
                            profile_country_text = profile_country_text[:-1]
                        elif active_field == "age":
                            profile_age_text = profile_age_text[:-1]
                        elif active_field == "hometown":
                            profile_hometown_text = profile_hometown_text[:-1]
                        elif active_field == "bio":
                            profile_bio_text = profile_bio_text[:-1]

                    elif event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                        profile_name_active = False
                        profile_country_active = False
                        profile_age_active = False
                        profile_hometown_active = False
                        profile_bio_active = False

                    elif event.unicode and event.unicode.isprintable():
                        char = event.unicode

                        if active_field == "name":
                            if len(profile_name_text) < 20:
                                profile_name_text += char

                        elif active_field == "country":
                            if char.isalpha() and len(profile_country_text) < 3:
                                profile_country_text += char.upper()

                        elif active_field == "age":
                            if char.isdigit() and len(profile_age_text) < 3:
                                profile_age_text += char

                        elif active_field == "hometown":
                            if len(profile_hometown_text) < 48:
                                profile_hometown_text += char

                        elif active_field == "bio":
                            if len(profile_bio_text) < 180:
                                profile_bio_text += char

            # ==========================================
            # MOUSE INPUT
            # ==========================================

            elif (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):
                click_consumed = False

                # --------------------------------------
                # Open dropdown choices get first chance
                # --------------------------------------

                if gender_dropdown_open:
                    for index, rect in enumerate(profile_gender_option_rects):
                        if rect.collidepoint(game_mouse_pos):
                            profile_gender = gender_options[index]
                            gender_dropdown_open = False
                            favorite_suit_dropdown_open = False
                            audio.play_sound("button_click")
                            click_consumed = True
                            break
                    if not click_consumed and not profile_gender_rect.collidepoint(game_mouse_pos):
                        gender_dropdown_open = False

                if not click_consumed and favorite_suit_dropdown_open:
                    for index, rect in enumerate(profile_favorite_suit_option_rects):
                        if rect.collidepoint(game_mouse_pos):
                            profile_favorite_suit = favorite_suit_options[index]
                            favorite_suit_dropdown_open = False
                            gender_dropdown_open = False
                            audio.play_sound("button_click")
                            click_consumed = True
                            break
                    if not click_consumed and not profile_favorite_suit_rect.collidepoint(game_mouse_pos):
                        favorite_suit_dropdown_open = False

                if click_consumed:
                    continue

                # --------------------------------------
                # Text focus
                # --------------------------------------

                profile_name_active = profile_name_rect.collidepoint(game_mouse_pos)
                profile_country_active = profile_country_rect.collidepoint(game_mouse_pos)
                profile_age_active = profile_age_rect.collidepoint(game_mouse_pos)
                profile_hometown_active = profile_hometown_rect.collidepoint(game_mouse_pos)
                profile_bio_active = profile_bio_rect.collidepoint(game_mouse_pos)

                if profile_name_active and profile_name_text == "Player":
                    profile_name_text = ""

                # --------------------------------------
                # Dropdown toggles
                # --------------------------------------

                if profile_gender_rect.collidepoint(game_mouse_pos):
                    gender_dropdown_open = not gender_dropdown_open
                    favorite_suit_dropdown_open = False
                    profile_name_active = False
                    profile_country_active = False
                    profile_age_active = False
                    profile_hometown_active = False
                    profile_bio_active = False
                    audio.play_sound("button_click")
                    continue

                if profile_favorite_suit_rect.collidepoint(game_mouse_pos):
                    favorite_suit_dropdown_open = not favorite_suit_dropdown_open
                    gender_dropdown_open = False
                    profile_name_active = False
                    profile_country_active = False
                    profile_age_active = False
                    profile_hometown_active = False
                    profile_bio_active = False
                    audio.play_sound("button_click")
                    continue

                # --------------------------------------
                # Avatar selectors
                # --------------------------------------

                avatar_selector_clicked = False

                for index in range(5):
                    if avatar_selector_left_rects[index].collidepoint(game_mouse_pos):
                        direction = -1
                        avatar_selector_clicked = True
                    elif avatar_selector_right_rects[index].collidepoint(game_mouse_pos):
                        direction = 1
                        avatar_selector_clicked = True
                    else:
                        continue

                    if index == 0:
                        selected_avatar_base = cycle_option(
                            selected_avatar_base,
                            avatar_base_options,
                            direction
                        )
                    elif index == 1:
                        selected_avatar_eyes = cycle_option(
                            selected_avatar_eyes,
                            avatar_eye_options,
                            direction
                        )
                    elif index == 2:
                        selected_avatar_hair = cycle_option(
                            selected_avatar_hair,
                            avatar_hair_options,
                            direction
                        )
                    elif index == 3:
                        selected_avatar_glasses = cycle_option(
                            selected_avatar_glasses,
                            avatar_glasses_options,
                            direction
                        )
                    elif index == 4:
                        selected_avatar_top = cycle_option(
                            selected_avatar_top,
                            avatar_top_options,
                            direction
                        )

                    audio.play_sound("button_click")
                    break

                if avatar_selector_clicked:
                    continue

                # --------------------------------------
                # Save / Create
                # --------------------------------------

                if profile_save_rect.collidepoint(game_mouse_pos):
                    country_code = profile_country_text.strip().upper()
                    if country_code and len(country_code) != 3:
                        profile_message = "Country must use a 3-letter abbreviation."
                        continue

                    if profile_age_text.strip():
                        try:
                            age_value = int(profile_age_text)
                        except ValueError:
                            age_value = 0
                        if not 1 <= age_value <= 999:
                            profile_message = "Age must be a number from 1 to 999."
                            continue
                        profile_age_text = str(age_value)

                    profile_country_text = country_code
                    player_name = profile_name_text.strip() or "Player"
                    profile_name_text = player_name

                    if profile_creation_mode:
                        current_profile_slot = pending_profile_slot
                        guest_mode = False

                        save_profile(
                            build_profile_save_data(),
                            current_profile_slot
                        )

                        profile_creation_mode = False
                        pending_profile_slot = None
                        profile_message = ""
                        audio.play_sound("button_click")
                        finish_profile_selection()

                    else:
                        if not guest_mode:
                            save_profile(
                                build_profile_save_data(),
                                current_profile_slot
                            )
                            profile_message = f"Profile saved to slot {current_profile_slot}."
                        else:
                            profile_message = "Guest mode does not save progress."

                        profile_name_active = False
                        profile_country_active = False
                        profile_age_active = False
                        profile_hometown_active = False
                        profile_bio_active = False
                        audio.play_sound("button_click")

                # --------------------------------------
                # Switch Profile
                # --------------------------------------

                elif (
                        not profile_creation_mode
                        and profile_switch_rect.collidepoint(game_mouse_pos)
                ):
                    audio.play_sound("button_click")

                    if profile_return_state == STATE_CAREER_HUB:
                        begin_career_profile_switch()
                        continue

                    profile_select_return_state = STATE_MENU
                    profile_name_active = False
                    profile_country_active = False
                    profile_age_active = False
                    profile_hometown_active = False
                    profile_bio_active = False
                    gender_dropdown_open = False
                    favorite_suit_dropdown_open = False
                    profile_message = ""
                    pending_profile_slot = None
                    profile_creation_mode = False
                    confirm_delete_profile = False
                    profile_delete_slot = None
                    current_state = STATE_PROFILE_SELECT

                # --------------------------------------
                # Back / Cancel
                # --------------------------------------

                elif profile_back_rect.collidepoint(game_mouse_pos):
                    audio.play_sound("button_click")

                    profile_name_active = False
                    profile_country_active = False
                    profile_age_active = False
                    profile_hometown_active = False
                    profile_bio_active = False
                    gender_dropdown_open = False
                    favorite_suit_dropdown_open = False

                    if profile_creation_mode:
                        profile_creation_mode = False
                        pending_profile_slot = None
                        current_state = STATE_PROFILE_SELECT
                    else:
                        if profile_return_state == STATE_CAREER_HUB:
                            save_career_from_hub()
                        current_state = profile_return_state

        # ==========================================
        # PLAYING
        # ==========================================

        elif current_state == STATE_PLAYING:

            if solitaire_restart_prompt.open:
                solitaire_restart_prompt.event(event, game_mouse_pos, game, audio)
                continue
            if (game_pause_menu_open and event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1 and game_mouse_pos is not None
                    and solitaire_restart_prompt.button.collidepoint(game_mouse_pos)
                    and solitaire_restart_prompt.allowed(game, current_game_mode)):
                solitaire_restart_prompt.open = True
                game_pause_menu_open = False
                audio.play_sound("button_click")
                continue

            # H = Hint. This mirrors the on-screen Hint button and respects
            # difficulty/challenge hint limits.
            if (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_h
                    and not game_pause_menu_open
                    and not confirm_return_to_menu
                    and not game.auto_solving
            ):
                if game.request_hint():
                    audio.play_sound("button_click")

            # ----------------------------
            # TEMP DEBUG: fake completed round
            # ----------------------------

            if (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_F8
            ):
                game.round_won = True

                game.round_summary = {
                    "moves": 112,
                    "elapsed_seconds": 387,
                    "base_score": 5000,
                    "move_bonus": 1700,
                    "time_bonus": 952,
                    "score": 7652,
                    "xp_earned": 150,
                    "remark": "Efficient work.",
                }

                game.audio.play_sound(
                    "celebration_1"
                )

                game.start_debug_victory_animation()

            if (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_F7
                    and current_state == STATE_PLAYING
            ):
                game.debug_auto_solve_state()


            # ==================================================
            # MOUSE DOWN // MOUSEBUTTONDOWN sorta
            # ==================================================

            elif (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
            ):

                # ----------------------------
                # Pause menu
                # ----------------------------

                if game_pause_menu_open:

                    if pause_resume_rect.collidepoint(
                            game_mouse_pos
                    ):
                        audio.play_sound(
                            "button_click"
                        )

                        game_pause_menu_open = False

                    elif pause_options_rect.collidepoint(
                            game_mouse_pos
                    ):
                        audio.play_sound(
                            "button_click"
                        )

                        game_pause_menu_open = False

                        options_return_state = (
                            STATE_PLAYING
                        )

                        current_state = (
                            STATE_OPTIONS
                        )

                    elif pause_menu_rect.collidepoint(
                            game_mouse_pos
                    ):
                        audio.play_sound(
                            "button_click"
                        )

                        game_pause_menu_open = False

                        confirm_return_to_menu = True

                # ----------------------------
                # Return confirmation
                # ----------------------------

                elif confirm_return_to_menu:

                    if confirm_yes_rect.collidepoint(
                            game_mouse_pos
                    ):
                        audio.play_sound(
                            "button_click"
                        )

                        confirm_return_to_menu = False

                        if current_game_mode == "career":
                            current_state = STATE_CAREER_HUB
                        elif current_game_mode == "free":
                            finish_free_play_sandbox()
                            current_state = STATE_FREE_PLAY_SELECT
                        elif current_game_mode == "head_to_head":
                            finish_head_to_head_race(
                                False,
                                forfeited=True
                            )
                        else:
                            current_state = STATE_MENU

                    elif confirm_no_rect.collidepoint(
                            game_mouse_pos
                    ):
                        audio.play_sound(
                            "button_click"
                        )

                        confirm_return_to_menu = False
                        game_pause_menu_open = True

                # ----------------------------
                # Gameplay menu
                # ----------------------------

                elif game_menu_rect.collidepoint(
                        game_mouse_pos
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    game_pause_menu_open = True

                # ----------------------------
                # Head-to-Head countdown lock
                # ----------------------------

                elif (
                        current_game_mode == "head_to_head"
                        and head_to_head_race.is_countdown_active(
                            pygame.time.get_ticks()
                        )
                ):
                    pass

                # ----------------------------
                # Auto-solve input lock
                # ----------------------------

                elif game.auto_solving:
                    pass


                # ----------------------------
                # SHUFFLE
                # ----------------------------

                elif (
                        game.shuffle_enabled
                        and game_shuffle_rect.collidepoint(
                    game_mouse_pos
                )
                ):
                    game.shuffle_stock()

                # ----------------------------
                # AUTO SOLVE
                # ----------------------------

                elif (
                        game.can_auto_solve()
                        and game_auto_solve_rect.collidepoint(
                    game_mouse_pos
                )
                ):
                    game.auto_solve()



                # ----------------------------
                # Hint
                # ----------------------------

                elif game_hint_rect.collidepoint(
                        game_mouse_pos
                ):
                    if game.request_hint():
                        audio.play_sound(
                            "button_click"
                        )

                # ----------------------------
                # Undo
                # ----------------------------

                elif game_undo_rect.collidepoint(
                        game_mouse_pos
                ):
                    if game.undo():
                        audio.play_sound(
                            "button_click"
                        )

                # ----------------------------
                # Cards
                # ----------------------------

                else:
                    game.handle_mouse_down(
                        game_mouse_pos,
                        event.clicks
                    )

            # ==================================================
            # MOUSE MOTION
            # ==================================================

            elif event.type == pygame.MOUSEMOTION:

                game.handle_mouse_motion(
                    game_mouse_pos
                )

            # ==================================================
            # MOUSE UP
            # ==================================================

            elif (
                    event.type
                    == pygame.MOUSEBUTTONUP
                    and event.button == 1
            ):

                game.handle_mouse_up(
                    game_mouse_pos
                )


    # ----------------------------------------------
    # Head-to-Head opponent race update
    # ----------------------------------------------

    if (
            current_state == STATE_PLAYING
            and current_game_mode == "head_to_head"
            and game.round_summary is None
    ):
        head_to_head_race.update(
            pygame.time.get_ticks()
        )

        if head_to_head_race.winner == "npc":
            finish_head_to_head_race(
                False
            )

    # Player finished the real Klondike board before the NPC. Consume the
    # normal Solitaire summary here so Career does not also award the regular
    # round rewards on top of the Head-to-Head result.
    if (
            current_state == STATE_PLAYING
            and current_game_mode == "head_to_head"
            and game.round_summary is not None
    ):
        head_to_head_round = game.consume_round_summary()
        finish_head_to_head_race(
            True,
            round_data=head_to_head_round
        )

    # ----------------------------------------------
    # Completed round check
    # ----------------------------------------------

    if current_state == STATE_PLAYING:
        completed_round = (
            game.consume_round_summary()
        )

        if completed_round is not None:
            round_recap_data = (
                completed_round
            )

            process_achievement_event(
                "solitaire_win",
                moves=round_recap_data.get("moves", 0),
                elapsed_seconds=round_recap_data.get("elapsed_seconds", 0),
                challenge_id=(
                    pending_career_challenge_id
                    if current_game_mode == "career"
                    else game.challenge_id
                ),
            )

            # ----------------------------
            # Decide where this game
            # should return afterward.
            # ----------------------------

            if current_game_mode == "career":
                post_round_return_state = STATE_CAREER_HUB
            elif current_game_mode == "free":
                post_round_return_state = STATE_FREE_PLAY_SELECT
            else:
                post_round_return_state = STATE_MENU

            # ----------------------------
            # Apply all rewards
            # ----------------------------

            last_progression_result = (
                apply_round_rewards(
                    round_recap_data
                )
            )

            if current_game_mode == "free":
                finish_free_play_sandbox()

            # ==========================================
            # CAREER ACTIVITY COMPLETION
            # ==========================================

            if (
                    current_game_mode == "career"
                    and pending_career_activity_type
                    is not None
            ):

                # ----------------------------
                # Career statistics
                # ----------------------------

                career_total_moves += (
                    round_recap_data.get(
                        "moves",
                        0
                    )
                )

                if (
                        pending_career_activity_type
                        == CAREER_ACTIVITY_ROUND
                ):
                    career_rounds_won += 1

                elif (
                        pending_career_activity_type
                        == CAREER_ACTIVITY_CHALLENGE
                ):
                    career_challenges_won += 1

                    challenge_names = {
                        "draw_3":
                            "3 Draw",

                        "no_undo":
                            "No Undo",

                        "no_hints":
                            "No Hints",

                        "all_or_nothing":
                            "All or Nothing",
                    }

                    challenge_name = (
                        challenge_names.get(
                            pending_career_challenge_id,
                            "Career Challenge"
                        )
                    )

                    add_career_news(
                        (
                            f"{player_name.upper()} "
                            f"CONQUERS {challenge_name.upper()}"
                        ),
                        (
                            f"{player_name} successfully completed "
                            f"the {challenge_name} challenge and "
                            f"continued climbing the competitive "
                            f"Solitaire circuit."
                        ),
                        "competition"
                    )

                # ----------------------------
                # Advance Career calendar
                # ----------------------------

                advance_career_day(
                    completed=True
                )

                # ----------------------------
                # Clear pending activity
                # ----------------------------

                pending_career_activity_index = None
                pending_career_activity_type = None
                pending_career_challenge_id = None

            current_state = (
                STATE_RECAP
            )

    if (
            current_state != STATE_HORSE_RACES
            and horse_race_music_channel is not None
    ):
        stop_horse_race_music(300)

    # Non-Solitaire games award XP too. If that XP crossed a level threshold,
    # wait until the player has safely returned to a hub/selection screen before
    # presenting the queued level-up cards.
    if (
            level_up_queue
            and current_level_up_data is None
            and current_state in (
                STATE_MENU,
                STATE_CAREER_HUB,
                STATE_CAREER_EVENT_SELECT,
                STATE_FREE_PLAY_SELECT,
            )
    ):
        post_round_return_state = current_state
        advance_level_up_screen()

    # ----------------------------------------------
    # Drawing State Chain // Drawing Chain
    # ----------------------------------------------

    if current_state == STATE_SPLASH:
        draw_splash_screen()


    elif current_state == STATE_PROFILE_SELECT:

        draw_profile_select_screen()

        if confirm_delete_profile:
            draw_delete_profile_confirmation()



    elif current_state == STATE_MENU:

        draw_main_menu()

    elif current_state == STATE_ACHIEVEMENTS:

        draw_achievements_screen(
            game_surface,
            game_mouse_pos,
            achievement_state,
            achievements_scroll_y,
            draw_submenu_background,
            draw_submenu_title,
            draw_menu_button,
            options_title_font,
            option_label_font,
            difficulty_detail_font,
        )

    elif current_state == STATE_HOW_TO_PLAY:

        draw_how_to_play()

    elif current_state == STATE_MODE_SELECT:

        draw_mode_select()




    elif current_state == STATE_CASE_OPENING:
        case_screen.update(pygame.time.get_ticks(), audio.play_sound)
        case_screen.draw(game_surface, game_mouse_pos)

    elif current_state == STATE_CRYPTID_CREATURES:
        cryptid_screen.sfx_volume = audio.sfx_volume
        cryptid_screen.update(pygame.time.get_ticks())
        cryptid_screen.draw(game_surface, menu_mouse_pos)

    elif current_state == STATE_FREE_PLAY_SELECT:

        draw_free_play_select()


    elif current_state == STATE_CAREER_ACTIVITY:
        draw_submenu_background(overlay_alpha=100)
        career_activity_screen.draw(game_surface,
            career_current_schedule[career_day_of_month - 1]["career_activity"],
            game_mouse_pos, career_cash, career_alien_story if career_current_schedule[career_day_of_month - 1]["career_activity"].get("kind") == "alien" else career_bigfoot_story)

    elif current_state == STATE_CAREER_HUB:

        draw_career_hub()



    elif current_state == STATE_CAREER_JOBS:

        draw_career_jobs()



    elif current_state == STATE_CAREER_REAL_ESTATE:

        draw_career_real_estate()



    elif current_state == STATE_CAREER_LEADERBOARDS:

        draw_career_leaderboards()

    elif (
            current_state
            == STATE_CAREER_LEADERBOARD_BIO
    ):
        draw_career_leaderboard_bio()



    elif current_state == STATE_CAREER_NEWS:

        draw_career_news()



    elif current_state == STATE_CAREER_EVENT_SELECT:

        draw_career_event_select()

    elif current_state == STATE_KING_PONG_OPPONENT_SELECT:

        draw_king_pong_opponent_select()

    elif current_state == STATE_BATTLE_BOSSES_OPPONENT_SELECT:

        draw_battle_bosses_opponent_select()

    elif current_state == STATE_ARCADE_TOKEN_EXCHANGE:

        draw_arcade_token_exchange()

    elif current_state == STATE_ARCADE_PRIZE_COUNTER:

        draw_arcade_prize_counter()

    elif current_state == STATE_ARCADE_TROPHY_ROOM:

        draw_arcade_trophy_room()

    elif current_state == STATE_CAREER_EVENT:

        draw_career_event()

    elif current_state == STATE_CAREER_EVENT_SUMMARY:

        draw_career_event_summary()


    elif current_state == STATE_DIFFICULTY:

        draw_difficulty_screen()


    elif current_state == STATE_OPTIONS:

        draw_options_menu()


    elif current_state == STATE_CUSTOMIZE:

        draw_customize_menu()

    elif current_state == STATE_PROFILE:

        draw_profile_screen()

    elif current_state == STATE_RECAP:

        draw_round_recap()

    elif current_state == STATE_CRAZY_EIGHTS:

        crazy_eights_game.update()

        draw_crazy_eights(
            game_surface,
            game_mouse_pos,
            crazy_eights_game,
            game.card_fronts,
            game.get_card_back_surface(),
            portrait_loader=get_npc_portrait_surface,
        )

    elif current_state == STATE_BANGO:

        draw_bango(
            game_surface,
            game_mouse_pos,
            bango_game,
            game.card_fronts,
            game.get_card_back_surface(),
            portrait_loader=get_npc_portrait_surface,
        )

    elif current_state == STATE_SCORE_FOUR_MODE_SELECT:

        draw_score_four_mode_select()

    elif current_state == STATE_SCORE_FOUR:

        score_four_game.update()

        draw_score_four()

    elif current_state == STATE_SCORE_FOUR_OPPONENT_SELECT:

        draw_score_four_opponent_select()


    elif current_state == STATE_BLACKJACK:

        blackjack_game.update()

        settle_blackjack_round()

        draw_blackjack()

    elif current_state == STATE_ROULETTE:

        roulette_game.update()

        settle_roulette_round()

        draw_roulette(
            game_surface,
            game_mouse_pos,
            roulette_game,
            RED_NUMBERS,
            draw_submenu_background,
            draw_submenu_title,
            draw_menu_button,
            options_title_font,
            option_label_font,
            difficulty_detail_font,
            career_cash,
            roulette_session_net,
            roulette_chip_value
        )

    elif current_state == STATE_HORSE_RACES:

        horse_previous_stage = horse_races_game.stage
        horse_races_game.update(pygame.time.get_ticks())
        if (
                horse_previous_stage == "racing"
                and horse_races_game.stage == "results"
        ):
            stop_horse_race_music(600)
        settle_horse_race_result()

        draw_horse_races(
            game_surface,
            game_mouse_pos,
            horse_races_game,
        )

    elif current_state == STATE_KING_PONG:

        king_pong_game.update(1.0 / 60.0, pygame.key.get_pressed())
        while True:
            point_event = king_pong_game.pop_point_event()
            if point_event is None:
                break
            audio.play_sound(
                "five_o_column_win"
                if point_event.get("player_scored")
                else "five_o_column_loss"
            )
        if king_pong_game.finished:
            claim_king_pong_result()
        draw_king_pong_screen()

    elif current_state == STATE_BATTLE_BOSSES:

        battle_bosses_game.update(1.0 / 60.0, pygame.key.get_pressed())
        for battle_sound_event in battle_bosses_game.pop_sound_events():
            audio.play_sound(battle_sound_event)
        if battle_bosses_game.finished:
            claim_battle_bosses_result()
        draw_battle_bosses_screen()

    elif current_state == STATE_FARO:

        draw_faro(
            game_surface,
            game_mouse_pos,
            faro_game,
            faro_chip_value,
            draw_submenu_background,
            draw_submenu_title,
            draw_menu_button,
            options_title_font,
            option_label_font,
            difficulty_detail_font,
            card_fronts=game.card_fronts,
            card_back_surface=game.get_card_back_surface(),
        )

    elif current_state == STATE_FIVE_O_POKER:

        five_o_poker_game.update()

        draw_five_o_poker(
            game_surface,
            game_mouse_pos,
            five_o_poker_game,
            player_name,
            draw_submenu_background,
            options_title_font,
            option_label_font,
            difficulty_detail_font,
            card_fronts=game.card_fronts,
            card_back_surface=game.get_card_back_surface(),
        )

    elif current_state == STATE_BLIND_MANS_BLUFF:

        update_bluff_presentation(blind_mans_bluff_game, audio.play_sound)
        draw_blind_mans_bluff(
            game_surface,
            game_mouse_pos,
            blind_mans_bluff_game,
            player_name,
            draw_submenu_background,
            options_title_font,
            option_label_font,
            difficulty_detail_font,
            card_fronts=game.card_fronts,
            card_back_surface=game.get_card_back_surface(),
        )

    elif current_state == STATE_BLACKJACK_BET:

        draw_blackjack_bet()


    elif (
            current_state
            == STATE_SEVEN_CARD_STUD_BUY_IN
    ):
        draw_seven_card_stud_buy_in(
            game_surface,
            game_mouse_pos,
            career_cash,
            draw_submenu_background,
            minimum_buy_in=(
                SEVEN_CARD_STUD_MIN_BUY_IN
            )
        )

    elif current_state == STATE_SEVEN_CARD_STUD:
        seven_card_stud_next_hand_seconds = None

        if (
                seven_card_stud_game.hand_complete
                and seven_card_stud_next_hand_at > 0
        ):
            remaining_ms = max(
                0,
                seven_card_stud_next_hand_at
                - pygame.time.get_ticks()
            )

            seven_card_stud_next_hand_seconds = (
                remaining_ms + 999
            ) // 1000

        draw_seven_card_stud(
            game_surface,
            game_mouse_pos,
            seven_card_stud_game,
            game.card_fronts,
            game.get_card_back_surface(),
            draw_submenu_background,
            draw_npc_portrait,
            player_name,
            game.felt_surface,
            next_hand_seconds=(
                seven_card_stud_next_hand_seconds
            )
        )

        draw_holdem_options_overlay(
            game_surface,
            game_mouse_pos
        )

    elif (
            current_state
            == STATE_FIVE_CARD_DRAW_BUY_IN
    ):

        draw_five_card_draw_buy_in(
            game_surface,
            game_mouse_pos,
            career_cash,
            draw_submenu_background,
            minimum_buy_in=(
                FIVE_CARD_DRAW_MIN_BUY_IN
            )
        )

    elif current_state == STATE_FIVE_CARD_DRAW:

        five_card_draw_next_hand_seconds = None

        if (
                five_card_draw_game.hand_complete
                and five_card_draw_next_hand_at > 0
        ):
            remaining_ms = max(
                0,
                five_card_draw_next_hand_at
                - pygame.time.get_ticks()
            )

            five_card_draw_next_hand_seconds = (
                remaining_ms + 999
            ) // 1000

        draw_five_card_draw(
            game_surface,
            game_mouse_pos,
            five_card_draw_game,
            game.card_fronts,
            game.get_card_back_surface(),
            draw_submenu_background,
            draw_npc_portrait,
            player_name,
            game.felt_surface,
            next_hand_seconds=(
                five_card_draw_next_hand_seconds
            )
        )

        draw_holdem_options_overlay(
            game_surface,
            game_mouse_pos
        )

    elif (
            current_state
            == STATE_TEXAS_HOLDEM_BUY_IN
    ):

        draw_texas_holdem_buy_in(
            game_surface,
            game_mouse_pos,
            career_cash,
            draw_submenu_background,
            minimum_buy_in=(
                TEXAS_HOLDEM_MIN_BUY_IN
            )
        )

    elif current_state == STATE_TEXAS_HOLDEM:

        texas_holdem_next_hand_seconds = None

        if (
                texas_holdem_game.hand_complete
                and texas_holdem_next_hand_at > 0
        ):
            remaining_ms = max(
                0,
                texas_holdem_next_hand_at
                - pygame.time.get_ticks()
            )

            texas_holdem_next_hand_seconds = (
                remaining_ms + 999
            ) // 1000

        draw_texas_holdem(
            game_surface,
            game_mouse_pos,
            texas_holdem_game,
            game.card_fronts,
            game.get_card_back_surface(),
            draw_submenu_background,
            draw_submenu_title,
            draw_menu_button,
            draw_npc_portrait,
            options_title_font,
            option_label_font,
            difficulty_detail_font,
            player_name,
            game.felt_surface,
            next_hand_seconds=(
                texas_holdem_next_hand_seconds
            )
        )

    # ==================================================
    # TEXAS HOLD'EM TIMED NPC ACTIONS
    # ==================================================

    if current_state == STATE_TEXAS_HOLDEM:

        now = pygame.time.get_ticks()
        from holdem_turn_flow import repair_betting_turn
        repair_betting_turn(texas_holdem_game)

        # ==================================================
        # Make sure an NPC turn is always scheduled
        #
        # With rotating blinds, a new hand or street can
        # begin directly on an NPC rather than the player.
        # ==================================================

        if (
                not texas_holdem_game.hand_complete
                and texas_holdem_game.current_actor not in (
                0,
                -1
        )
                and texas_holdem_next_npc_action_at == 0
                and not texas_holdem_game.is_betting_round_complete()
        ):
            texas_holdem_next_npc_action_at = (
                    now
                    + get_holdem_npc_delay()
            )

        # ==================================================
        # Cancel pending auto-deal if user turns it off
        # ==================================================

        if not is_holdem_auto_deal_enabled():
            texas_holdem_next_hand_at = 0

        # ==================================================
        # Delayed winning-hand sound
        # ==================================================

        if (
                texas_holdem_hand_win_sound_at > 0
                and now
                >= texas_holdem_hand_win_sound_at
        ):
            audio.play_sound(
                "poker_hand_win"
            )

            texas_holdem_hand_win_sound_at = 0

        process_texas_holdem_showdown()
        if getattr(texas_holdem_game, "recap_open", False):
            texas_holdem_next_hand_at = 0
            texas_holdem_session_end_at = 0

        # ==================================================
        # Start next-hand countdown after showdown
        # ==================================================

        if (
                texas_holdem_game.hand_complete
                and texas_holdem_game.current_stage == "showdown"
                and texas_holdem_next_hand_at == 0
                and texas_holdem_session_end_at == 0
                and texas_holdem_game.player_stack > 0
                and not texas_holdem_game.player_busted
                and not texas_holdem_game.all_npcs_busted()
                and is_holdem_auto_deal_enabled()
                and not getattr(texas_holdem_game, "recap_open", False)
        ):
            texas_holdem_next_hand_at = (
                    now
                    + get_holdem_next_hand_delay()
            )

        # ==================================================
        # Run one scheduled NPC action
        # ==================================================

        if (
                texas_holdem_next_npc_action_at > 0
                and now >= texas_holdem_next_npc_action_at
                and not texas_holdem_game.hand_complete
        ):

            texas_holdem_next_npc_action_at = 0

            # Remember who is acting because
            # run_next_npc_action() advances current_actor.
            acting_actor = (
                texas_holdem_game.current_actor
            )

            action_success = (
                texas_holdem_game
                .run_next_npc_action()
            )

            if (
                    action_success
                    and acting_actor > 0
            ):
                acting_npc_index = (
                        acting_actor - 1
                )

                # ------------------------------------------
                # Action sound
                # ------------------------------------------

                play_texas_holdem_npc_action_sound(
                    acting_npc_index
                )

                # ------------------------------------------
                # Personality chat
                # ------------------------------------------

                post_texas_holdem_chat(
                    generate_npc_action_chat(
                        texas_holdem_game,
                        acting_npc_index
                    )
                )

            # ------------------------------------------
            # Another NPC still needs to act
            # ------------------------------------------

            if (
                    not texas_holdem_game
                            .is_betting_round_complete()
                    and texas_holdem_game.current_actor != 0
            ):
                texas_holdem_next_npc_action_at = (
                        now
                        + get_holdem_npc_delay()
                )

        # ==================================================
        # Betting round has finished
        #
        # Schedule street advance ONCE.
        # This check happens every frame, so we cannot
        # get stuck after the final NPC acts.
        # ==================================================

        if (
                not texas_holdem_game.hand_complete
                and texas_holdem_game
                .is_betting_round_complete()
                and texas_holdem_round_advance_at == 0
        ):
            texas_holdem_round_advance_at = (
                    now
                    + get_holdem_street_delay()
            )

            # Nobody is actively taking a turn now.
            texas_holdem_game.current_actor = -1

        # ==================================================
        # Advance to flop / turn / river / showdown
        # ==================================================

        if (
                texas_holdem_round_advance_at > 0
                and now >= texas_holdem_round_advance_at
        ):

            texas_holdem_round_advance_at = 0

            previous_stage = (
                texas_holdem_game.current_stage
            )

            advanced = (
                texas_holdem_game
                .advance_after_betting_round()
            )

            new_stage = (
                texas_holdem_game.current_stage
            )

            # ==================================================
            # Flop / Turn / River card sound
            # ==================================================

            if (
                    advanced
                    and new_stage
                    in (
                    "flop",
                    "turn",
                    "river",
            )
                    and new_stage
                    != previous_stage
            ):
                play_texas_holdem_street_sound()

            # ==================================================
            # If the player is all-in, the new street may
            # begin directly with an NPC.
            # ==================================================

            if (
                    advanced
                    and not texas_holdem_game.hand_complete
                    and texas_holdem_game.current_actor != 0
            ):
                schedule_texas_holdem_npc_action()

        # ==================================================
        # Automatically start next hand
        # ==================================================

        if (
                texas_holdem_next_hand_at > 0
                and now >= texas_holdem_next_hand_at
        ):
            texas_holdem_next_hand_at = 0

            texas_holdem_game.start_hand()

        # ==================================================
        # Poker session finished
        # ==================================================

        if (
                texas_holdem_session_end_at > 0
                and now >= texas_holdem_session_end_at
        ):
            texas_holdem_session_end_at = 0

            texas_holdem_next_hand_at = 0
            texas_holdem_next_npc_action_at = 0
            texas_holdem_round_advance_at = 0

            finish_texas_holdem_session()



    elif current_state == STATE_SEVEN_CARD_STUD:

        now = pygame.time.get_ticks()

        # ==================================================
        # Make sure NPC-first Stud streets are scheduled
        # ==================================================

        if (
                not seven_card_stud_game.hand_complete
                and seven_card_stud_game.current_stage
                in seven_card_stud_game.STUD_STAGES
                and seven_card_stud_game.current_actor
                not in (
                    0,
                    -1,
                )
                and seven_card_stud_next_npc_action_at == 0
                and not seven_card_stud_game.is_betting_round_complete()
        ):
            seven_card_stud_next_npc_action_at = (
                    now
                    + get_holdem_npc_delay()
            )

        # ==================================================
        # Delayed player win sound
        # ==================================================

        if (
                seven_card_stud_hand_win_sound_at > 0
                and now >= seven_card_stud_hand_win_sound_at
        ):
            audio.play_sound(
                "poker_hand_win"
            )

            seven_card_stud_hand_win_sound_at = 0

        process_seven_card_stud_showdown()

        # ==================================================
        # Start next-hand countdown
        # ==================================================

        if (
                seven_card_stud_game.hand_complete
                and seven_card_stud_game.current_stage == "showdown"
                and seven_card_stud_next_hand_at == 0
                and seven_card_stud_session_end_at == 0
                and is_holdem_auto_deal_enabled()
                and seven_card_stud_game.player_stack > 0
                and not seven_card_stud_game.player_busted
                and not seven_card_stud_game.all_npcs_busted()
        ):
            seven_card_stud_next_hand_at = (
                    now
                    + get_holdem_next_hand_delay()
            )

        # ==================================================
        # Run one NPC betting action
        # ==================================================

        if (
                seven_card_stud_next_npc_action_at > 0
                and now >= seven_card_stud_next_npc_action_at
                and not seven_card_stud_game.hand_complete
        ):
            seven_card_stud_next_npc_action_at = 0

            acting_actor = (
                seven_card_stud_game.current_actor
            )

            action_success = (
                seven_card_stud_game.run_next_npc_action()
            )

            if (
                    action_success
                    and acting_actor > 0
            ):
                acting_npc_index = (
                        acting_actor - 1
                )

                play_seven_card_stud_npc_action_sound(
                    acting_npc_index
                )

                post_seven_card_stud_chat(
                    generate_npc_action_chat(
                        seven_card_stud_game,
                        acting_npc_index
                    )
                )

            if (
                    not seven_card_stud_game.is_betting_round_complete()
                    and seven_card_stud_game.current_actor
                    not in (
                        0,
                        -1,
                    )
            ):
                seven_card_stud_next_npc_action_at = (
                        now
                        + get_holdem_npc_delay()
                )

        # ==================================================
        # Finished betting round -> schedule next street
        # ==================================================

        if (
                not seven_card_stud_game.hand_complete
                and seven_card_stud_game.current_stage
                in seven_card_stud_game.STUD_STAGES
                and seven_card_stud_game.is_betting_round_complete()
                and seven_card_stud_round_advance_at == 0
        ):
            seven_card_stud_round_advance_at = (
                    now
                    + get_holdem_street_delay()
            )

            seven_card_stud_game.current_actor = -1

        # ==================================================
        # Advance Third -> Fourth -> ... -> Showdown
        # ==================================================

        if (
                seven_card_stud_round_advance_at > 0
                and now >= seven_card_stud_round_advance_at
        ):
            seven_card_stud_round_advance_at = 0

            previous_stage = (
                seven_card_stud_game.current_stage
            )

            advanced = (
                seven_card_stud_game.advance_after_betting_round()
            )

            new_stage = (
                seven_card_stud_game.current_stage
            )

            if (
                    advanced
                    and previous_stage != new_stage
                    and new_stage
                    in seven_card_stud_game.STUD_STAGES
            ):
                audio.play_sound(
                    "card_draw"
                )

            if (
                    advanced
                    and not seven_card_stud_game.hand_complete
                    and new_stage
                    in seven_card_stud_game.STUD_STAGES
                    and seven_card_stud_game.current_actor
                    not in (
                        0,
                        -1,
                    )
            ):
                schedule_seven_card_stud_npc_action()

        # ==================================================
        # Automatically start next hand
        # ==================================================

        if (
                seven_card_stud_next_hand_at > 0
                and now >= seven_card_stud_next_hand_at
        ):
            seven_card_stud_next_hand_at = 0

            if seven_card_stud_game.start_hand():
                audio.play_sound(
                    "card_draw"
                )

        # ==================================================
        # Session finished
        # ==================================================

        if (
                seven_card_stud_session_end_at > 0
                and now >= seven_card_stud_session_end_at
        ):
            seven_card_stud_session_end_at = 0

            finish_seven_card_stud_session()


    elif current_state == STATE_FIVE_CARD_DRAW:

        now = pygame.time.get_ticks()

        # ==================================================
        # Make sure an NPC-first betting turn is scheduled
        # ==================================================

        if (
                not five_card_draw_game.hand_complete
                and five_card_draw_game.current_stage
                in (
                    "preflop",
                    "post_draw",
                )
                and five_card_draw_game.current_actor
                not in (
                    0,
                    -1,
                )
                and five_card_draw_next_npc_action_at == 0
                and not five_card_draw_game.is_betting_round_complete()
        ):
            five_card_draw_next_npc_action_at = (
                    now
                    + get_holdem_npc_delay()
            )

        # ==================================================
        # Delayed hand-win sound
        # ==================================================

        if (
                five_card_draw_hand_win_sound_at > 0
                and now >= five_card_draw_hand_win_sound_at
        ):
            audio.play_sound(
                "poker_hand_win"
            )

            five_card_draw_hand_win_sound_at = 0

        process_five_card_draw_showdown()

        # ==================================================
        # Start next-hand countdown
        # ==================================================

        if (
                five_card_draw_game.hand_complete
                and five_card_draw_game.current_stage == "showdown"
                and five_card_draw_next_hand_at == 0
                and five_card_draw_session_end_at == 0
                and is_holdem_auto_deal_enabled()
                and five_card_draw_game.player_stack > 0
                and not five_card_draw_game.player_busted
                and not five_card_draw_game.all_npcs_busted()
        ):
            five_card_draw_next_hand_at = (
                    now
                    + get_holdem_next_hand_delay()
            )

        # ==================================================
        # Run one NPC betting action
        # ==================================================

        if (
                five_card_draw_next_npc_action_at > 0
                and now >= five_card_draw_next_npc_action_at
                and not five_card_draw_game.hand_complete
        ):
            five_card_draw_next_npc_action_at = 0

            acting_actor = (
                five_card_draw_game.current_actor
            )

            action_success = (
                five_card_draw_game.run_next_npc_action()
            )

            if (
                    action_success
                    and acting_actor > 0
            ):
                acting_npc_index = (
                        acting_actor - 1
                )

                play_five_card_draw_npc_action_sound(
                    acting_npc_index
                )

                post_five_card_draw_chat(
                    generate_npc_action_chat(
                        five_card_draw_game,
                        acting_npc_index
                    )
                )

            if (
                    not five_card_draw_game.is_betting_round_complete()
                    and five_card_draw_game.current_actor
                    not in (
                        0,
                        -1,
                    )
            ):
                five_card_draw_next_npc_action_at = (
                        now
                        + get_holdem_npc_delay()
                )

        # ==================================================
        # Finished betting round -> schedule transition
        # ==================================================

        if (
                not five_card_draw_game.hand_complete
                and five_card_draw_game.current_stage
                in (
                    "preflop",
                    "post_draw",
                )
                and five_card_draw_game.is_betting_round_complete()
                and five_card_draw_round_advance_at == 0
        ):
            five_card_draw_round_advance_at = (
                    now
                    + get_holdem_street_delay()
            )

            five_card_draw_game.current_actor = -1

        # ==================================================
        # First betting -> draw / final betting -> showdown
        # ==================================================

        if (
                five_card_draw_round_advance_at > 0
                and now >= five_card_draw_round_advance_at
        ):
            five_card_draw_round_advance_at = 0

            previous_stage = (
                five_card_draw_game.current_stage
            )

            advanced = (
                five_card_draw_game.advance_after_betting_round()
            )

            new_stage = (
                five_card_draw_game.current_stage
            )

            if (
                    advanced
                    and previous_stage == "preflop"
                    and new_stage in (
                        "draw",
                        "post_draw",
                    )
            ):
                audio.play_sound(
                    "card_draw"
                )

            if (
                    advanced
                    and not five_card_draw_game.hand_complete
                    and new_stage
                    in (
                        "preflop",
                        "post_draw",
                    )
                    and five_card_draw_game.current_actor
                    not in (
                        0,
                        -1,
                    )
            ):
                schedule_five_card_draw_npc_action()

        # ==================================================
        # Automatically start next hand
        # ==================================================

        if (
                five_card_draw_next_hand_at > 0
                and now >= five_card_draw_next_hand_at
        ):
            five_card_draw_next_hand_at = 0

            if five_card_draw_game.start_hand():
                audio.play_sound(
                    "card_draw"
                )

            clear_five_card_draw_selection()

        # ==================================================
        # Session finished
        # ==================================================

        if (
                five_card_draw_session_end_at > 0
                and now >= five_card_draw_session_end_at
        ):
            five_card_draw_session_end_at = 0

            finish_five_card_draw_session()


    elif current_state == STATE_DEBUG_POKER_NPC_SELECT:

        debug_game_labels = {
            "texas_holdem": "Texas Hold'em",
            "five_card_draw": "Five-Card Draw",
            "seven_card_stud": "Seven-Card Stud",
        }
        draw_debug_poker_npc_select(
            game_surface,
            game_mouse_pos,
            debug_game_labels.get(debug_poker_select_game_id, "Poker"),
            NPCS,
            debug_poker_selected_ids,
            portrait_loader=get_npc_portrait_surface,
            can_start=(career_cash >= 100),
            cash=career_cash,
        )

    elif current_state == STATE_DEBUG_MENU:

        draw_debug_menu(

            game_surface,

            game_mouse_pos,

            draw_submenu_background,

            draw_submenu_title,

            draw_menu_button,

            option_label_font,

            difficulty_detail_font

        )

    elif current_state == STATE_LEVEL_UP:

        draw_level_up_screen()


    elif current_state == STATE_PLAYING:

        game.update_auto_solve()

        game.draw()

        draw_gameplay_ui()

        if current_game_mode == "head_to_head":
            head_to_head_race.update(
                pygame.time.get_ticks()
            )
            draw_head_to_head_hud(
                game_surface,
                head_to_head_race,
                head_to_head_race.player_progress_from_foundations(
                    game.foundations
                ),
                pygame.time.get_ticks(),
                get_npc_portrait_surface,
                option_label_font,
                difficulty_detail_font,
                ui_small_font,
            )

        if game_pause_menu_open:
            draw_game_pause_menu()

        elif confirm_return_to_menu:
            draw_return_confirmation()
        if solitaire_restart_prompt.open:
            solitaire_restart_prompt.draw(game_surface, game_mouse_pos)

    update_achievement_popup()
    if achievement_popup_current is not None:
        draw_achievement_popup(
            game_surface,
            achievement_popup_current,
            pygame.time.get_ticks() - achievement_popup_started,
            achievement_popup_fans,
            achievement_popup_cosmetic,
            option_label_font,
            difficulty_detail_font,
        )

    # ----------------------------------------------
    # Scale internal 1366x768 image
    # to the selected actual window size.
    # ----------------------------------------------

    if (
            WINDOW_WIDTH == BASE_WIDTH
            and WINDOW_HEIGHT == BASE_HEIGHT
    ):
        screen.blit(
            game_surface,
            (0, 0)
        )

    else:
        if (
                scaled_surface_cache is None
                or scaled_surface_cache.get_size()
                != (WINDOW_WIDTH, WINDOW_HEIGHT)
        ):
            scaled_surface_cache = pygame.Surface(
                (
                    WINDOW_WIDTH,
                    WINDOW_HEIGHT
                )
            ).convert()

        # Keep the cached destination surface from the
        # performance pass, but use filtered scaling again.
        # Plain transform.scale() made the entire 1366x768
        # frame, especially text, visibly blurry/blocky when
        # enlarged to 1920x1080 or 2560x1440.
        pygame.transform.smoothscale(
            game_surface,
            (
                WINDOW_WIDTH,
                WINDOW_HEIGHT
            ),
            scaled_surface_cache
        )

        screen.blit(
            scaled_surface_cache,
            (0, 0)
        )

    # ----------------------------
    # Software cursor fallback
    # ----------------------------

    if (
            software_cursor_fallback
            and cursor_image is not None
    ):
        mouse_x, mouse_y = (
            pygame.mouse.get_pos()
        )

        screen.blit(
            cursor_image,
            (
                mouse_x,
                mouse_y
            )
        )

    pygame.display.flip()


    clock.tick(
        FPS
    )


pygame.quit()


