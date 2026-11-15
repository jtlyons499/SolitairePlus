"""Everything from the old main.py that has not moved to its own module yet.

Temporary: the restructure (docs/dev/RESTRUCTURE_BRIEF.md, Phases 3-10) empties this module
area by area and then deletes it. Each old main-loop branch is a function here
(loop_event_<screen>, loop_draw_<screen>, loop_late_<screen>), called through the screen
registry in solitaireplus/app/loop.py.
"""
from solitaireplus.app import paths
import collections as _collections
from solitaireplus.app import update_check
from solitaireplus.app import state, state_names


from solitaireplus.career.alien_night import STORY as ALIEN_STORY, new_alien_story, refresh_adventure_schedule
from solitaireplus.games.solitaire.restart import RestartPrompt
from solitaireplus.profile import save_data
from solitaireplus.games.solitaire import screen  # start-up code of this module runs here, as before
from solitaireplus.profile.avatar import load_avatar_bank, avatar_options
from solitaireplus.career.asset_images import (get_jobfinder_image, get_realestate_image,
                                 get_career_hub_image, get_country_flag_surface)
from solitaireplus.career.activities import new_story, normalize_story, start_night, choose_option, reconcile_story_cosmetics
from solitaireplus.career.activities_ui import CareerActivityScreen
from solitaireplus.app.cosmetic_assets import CosmeticCatalog, SingleDriftCache
from solitaireplus.career.events.press_interview import PRESS_INTERVIEW_QUESTION_POOL, select_interview, answer_outcome
from solitaireplus.career.session_summary import poker_session_status, night_game_net, track_night_cash, night_cash_total
from solitaireplus.profile.unlocks import unlock_ratings, lock_reason, rating_lock_progress
from solitaireplus.app.multiplayer_launcher import MultiplayerLauncher
from solitaireplus.menus import main_menu  # start-up code of this module runs here, as before

from solitaireplus.career.event_progress import store_event_progress, restore_event_progress
from solitaireplus.career.time_warp import advance_months
from solitaireplus.career.case_opening import (
    ITEMS as CASE_ITEMS,
    new_case_state,
    normalize_case_state,
    purchase as purchase_loot_case,
    award_earned_trophies,
)
from solitaireplus.career.case_opening_ui import CaseOpeningScreen
from solitaireplus.games.arcade.support import (
    ARCADE_COMING_SOON_GAME_IDS,
    ARCADE_MACHINE_NAMES,
    ARCADE_PRIZE_CATALOG,
    ARCADE_TOKEN_PACKAGES,
    award_ace_invaders_tickets,
    award_battle_bosses_tickets,
    award_king_pong_tickets,
    award_suit_snake_tickets,
    buy_token_package,
    clone_arcade_state,
    get_machine_cost,
    make_default_arcade_state,
    normalize_arcade_state,
    redeem_prize,
    register_ace_invaders_result,
    register_battle_bosses_result,
    register_king_pong_result,
    register_suit_snake_result,
    spend_tokens,
)
from solitaireplus.games.poker.bluff_presentation import update_bluff_presentation
from solitaireplus.games.poker.recap import handle_recap_action
from solitaireplus.games.poker.learning import new_learning, normalize_learning
import os
import sys
import time
import copy
import ctypes

from solitaireplus.career.hub_controls import CareerHubControls
from solitaireplus.npc.personality import personality_summary
from solitaireplus.npc.personality_ui import draw_npc_traits

import random

import math
import pygame
import json


from solitaireplus.app.audio import AudioManager
from solitaireplus.games.solitaire.rules import Game, BASE_WIDTH, BASE_HEIGHT

from solitaireplus.games.cards.score_four import ScoreFourGame
from solitaireplus.games.cards.crazy_eights import CrazyEightsGame
from solitaireplus.games.cards.crazy_eights_ui import (
    draw_crazy_eights,
    get_crazy_eights_action,
    ACTION_RETURN as CRAZY_EIGHTS_ACTION_RETURN,
    ACTION_DRAW as CRAZY_EIGHTS_ACTION_DRAW,
    ACTION_CONTINUE as CRAZY_EIGHTS_ACTION_CONTINUE,
    ACTION_CARD as CRAZY_EIGHTS_ACTION_CARD,
    ACTION_SUIT as CRAZY_EIGHTS_ACTION_SUIT,
)
from solitaireplus.games.cards.bango import BangoGame
from solitaireplus.games.cryptid.ui import CryptidScreen
from solitaireplus.games.cryptid.collection import new_collection, normalize_collection, award_level_packs, reward_battle
from solitaireplus.games.cards.bango_ui import (
    draw_bango,
    get_bango_action,
    ACTION_RETURN as BANGO_ACTION_RETURN,
    ACTION_CALL as BANGO_ACTION_CALL,
    ACTION_CONTINUE as BANGO_ACTION_CONTINUE,
)
from solitaireplus.games.casino.blackjack import BlackjackGame
from solitaireplus.games.arcade.king_pong import KingPongGame, KING_PONG_DIFFICULTIES
from solitaireplus.games.arcade.battle_bosses import (
    BATTLE_BOSSES_DIFFICULTIES,
    build_battle_bosses_choices,
)
from solitaireplus.games.arcade.battle_bosses_game import BattleBossesGame
from solitaireplus.games.arcade.ace_invaders import ACE_INVADERS_DIFFICULTIES
from solitaireplus.games.arcade.ace_invaders_game import AceInvadersGame
from solitaireplus.games.arcade.suit_snake import SUIT_SNAKE_MODES, SUIT_SNAKE_MOVEMENT_STYLES
from solitaireplus.games.arcade.suit_snake_game import SuitSnakeGame
from solitaireplus.games.dead_mans_hand.game import DeadMansHandGame

from solitaireplus.games.poker.holdem import (
    TexasHoldemGame,
)

from solitaireplus.games.poker.holdem_ui import (
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

from solitaireplus.games.poker.holdem_chat import (
    generate_npc_action_chat,
    generate_player_action_reaction,
    generate_showdown_chat,
)

from solitaireplus.games.poker.five_card_draw import (
    FiveCardDrawGame,
)

from solitaireplus.games.poker.five_card_draw_ui import (
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

from solitaireplus.games.poker.seven_card_stud import (
    SevenCardStudGame,
)

from solitaireplus.games.poker.seven_card_stud_ui import (
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

from solitaireplus.npc.manager import (
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

from solitaireplus.games.casino.roulette import (
    RouletteGame,
    RED_NUMBERS,
)

from solitaireplus.games.casino.roulette_ui import (
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

from solitaireplus.games.casino.horse_races import HorseRaceGame
from solitaireplus.games.casino.horse_races_ui import (
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

from solitaireplus.games.casino.faro import FaroGame
from solitaireplus.games.casino.faro_ui import (
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

from solitaireplus.games.poker.five_o import FiveOPokerGame
from solitaireplus.games.poker.five_o_ui import (
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

from solitaireplus.games.poker.blind_mans_bluff import BlindMansBluffGame
from solitaireplus.games.poker.blind_mans_bluff_ui import (
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

from solitaireplus.debug.game_mode import enter_debug_game_mode, end_debug_game_mode, keep_night_context, restore_night_context

from solitaireplus.debug.poker_select import (
    draw_debug_poker_npc_select,
    get_debug_poker_select_action,
    make_default_selection as make_debug_poker_default_selection,
    cycle_selection as cycle_debug_poker_selection,
    ACTION_BACK as DEBUG_POKER_ACTION_BACK,
    ACTION_START as DEBUG_POKER_ACTION_START,
    ACTION_RANDOMIZE as DEBUG_POKER_ACTION_RANDOMIZE,
    ACTION_CYCLE as DEBUG_POKER_ACTION_CYCLE,
)

from solitaireplus.games.solitaire.head_to_head import (
    HeadToHeadRace,
    select_head_to_head_opponents,
)
from solitaireplus.games.solitaire.head_to_head_ui import (
    draw_head_to_head_selection,
    draw_head_to_head_hud,
    get_selection_action as get_head_to_head_selection_action,
)

from solitaireplus.debug.menu import (
    draw_debug_menu,
    get_debug_action,
    show_debug_message,
    is_minigame_category_action,
    toggle_minigame_category,
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
    ACTION_ARCADE_NIGHT,
    ACTION_KING_PONG,
    ACTION_BATTLE_BOSSES,
    ACTION_ACE_INVADERS,
    ACTION_SUIT_SNAKE,
    ACTION_DEAD_MANS_HAND,
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
    LAUNCH_ACTIONS as DEBUG_LAUNCH_ACTIONS,
    CAREER_HUB_JUMP_ACTIONS as DEBUG_CAREER_HUB_JUMP_ACTIONS,
)

from solitaireplus.profile.saves import (
    make_default_profile,
    save_profile,
    load_profile,
    profile_exists,
    delete_profile,
    PROFILE_SLOT_COUNT,
    ProfileUnavailable,
)

from solitaireplus.career.ratings import (
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

from solitaireplus.career.rating_events import (
    record_result,
    record_poker_showdown,
    settle_competitive_result,
    settle_house_result,
    settle_poker_session,
)

from solitaireplus.career.npc_world import ensure_career_world, advance_career_world, add_prospect
from solitaireplus.career.npc_development import development_stage
from solitaireplus.npc.portraits import draw_layered_portrait, register_player_avatar_art

from solitaireplus.career.fans import (
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
    get_player_public_appeal_display_name,
    normalize_fan_trend,
    record_fan_trend,
)
from solitaireplus.career.world_flavor import rating_milestone_stories, strongest_rating_status

from solitaireplus.profile.achievements import (
    ACHIEVEMENT_DEFINITIONS,
    make_default_achievement_state,
    normalize_achievement_state,
    record_event as record_achievement_event,
    iter_rewards as iter_achievement_rewards,
    get_definition as get_achievement_definition,
    register_optional_cosmetics,
)

from solitaireplus.menus.achievements_screen import (
    BACK_RECT as ACHIEVEMENTS_BACK_RECT,
    clamp_scroll as clamp_achievements_scroll,
    draw_achievements_screen,
    draw_achievement_popup,
)

from solitaireplus.career.events.autographs import (
    AutographEvent,
    AUTOGRAPH_CANVAS_RECT,
    AUTOGRAPH_CLEAR_RECT,
    AUTOGRAPH_SUBMIT_RECT,
)

from solitaireplus.career.news import (
    build_casual_cards_story,
    build_poker_story,
    build_casino_story,
    build_niche_story,
    build_arcade_story,
    build_monthly_flavor_story,
    build_head_to_head_story,
)

from solitaireplus.app.help_history import HISTORY_HELP_PAGES

from solitaireplus.app.settings import (
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
from solitaireplus.games.solitaire import head_to_head_screen
from solitaireplus.career import career_rewards
from solitaireplus.career import career_saving

# ==================================================
# Working directory
# ==================================================

# Resource paths were set before imports by runtime_support.bootstrap().

register_optional_cosmetics(
    MENU_BACKGROUNDS,
    FELTS,
    TITLES,
)

# Case-opening and Arcade Prize Counter cosmetics are real Customize rewards.
# Register their metadata before the image catalogs are built. Missing PNGs are
# intentionally allowed: ownership can be earned now and the art can be dropped
# in later without changing code or losing the unlock.
REWARD_CURSOR_IDS = set()
for _reward in [*CASE_ITEMS.values(), *ARCADE_PRIZE_CATALOG]:
    if _reward.get("kind") != "cosmetic":
        continue
    _ctype = str(_reward.get("cosmetic_type", "")).lower()
    _asset_id = str(_reward.get("asset_id", "")).strip()
    _asset_path = str(_reward.get("asset_path", "")).strip()
    if not _asset_id or not _asset_path:
        continue
    state._entry = {
        "name": _reward.get("name", _asset_id),
        "path": _asset_path,
        "order": state._reward_cosmetic_order,
    }
    state._reward_cosmetic_order += 10
    if _ctype == "background":
        MENU_BACKGROUNDS.setdefault(_asset_id, state._entry)
    elif _ctype == "felt":
        FELTS.setdefault(_asset_id, state._entry)
    elif _ctype == "title":
        TITLES.setdefault(_asset_id, state._entry)
    elif _ctype == "cursor":
        REWARD_CURSOR_IDS.add(_asset_id)

# ==================================================
# PYGAME INITIALIZATION
# ==================================================

pygame.display.init()
pygame.font.init()
from solitaireplus.app import sounds  # start-up code of this module runs here, as it did in main.py


# ========================================================================================
# GAME STATES // CONSTANTS // CAREER CONSTANTS // CAREER STATES // BUILD VERSION
# ========================================================================================

# The version lives in version.py (single source of truth). Do not edit here.
from version import __version__ as BUILD_VERSION
from solitaireplus.app import state_names  # start-up code of this module runs here, as it did in main.py
SCORE_FOUR_TIER_DISPLAY_NAMES = {
    "low": "Casual",
    "mid": "Skilled",
    "strong": "Expert",
    "elite": "Master",
}

TEXAS_HOLDEM_MIN_BUY_IN = 100
FIVE_CARD_DRAW_MIN_BUY_IN = 100
SEVEN_CARD_STUD_MIN_BUY_IN = 100
FIVE_O_POKER_MIN_BUY_IN = 100
BLIND_MANS_BLUFF_MIN_BUY_IN = 100

ARCADE_MACHINE_MUSIC_BY_STATE = {
    state_names.STATE_KING_PONG: sounds.ARCADE_MACHINE_MUSIC_TRACKS.get("king_pong"),
    state_names.STATE_BATTLE_BOSSES: sounds.ARCADE_MACHINE_MUSIC_TRACKS.get("battle_bosses"),
    state_names.STATE_ACE_INVADERS: sounds.ARCADE_MACHINE_MUSIC_TRACKS.get("ace_invaders"),
    state_names.STATE_SUIT_SNAKE: sounds.ARCADE_MACHINE_MUSIC_TRACKS.get("suit_snake"),
}
from solitaireplus.career import activity_screen  # start-up code of this module runs here, as before

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
from solitaireplus.menus import help_screen  # start-up code of this module runs here, as before

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
        state._entry = (_history_page_id, _history_page.get("button", "History"))
        _after_page = _history_page.get("after")
        state._inserted = False
        if _after_page:
            for _page_index, (_existing_page_id, _existing_label) in enumerate(_pages):
                if _existing_page_id == _after_page:
                    _pages.insert(_page_index + 1, state._entry)
                    state._inserted = True
                    break
        if not state._inserted:
            _pages.append(state._entry)
    HELP_CONTENT[_history_page_id] = {
        "title": _history_page.get("title", "History"),
        "lines": list(_history_page.get("lines", [])),
        "image": _history_page.get("image"),
        "caption": _history_page.get("caption", ""),
        "history_page": True,
    }
from solitaireplus.career import web_pages  # start-up code of this module runs here, as before
from solitaireplus.career import calendar  # start-up code of this module runs here, as before
from solitaireplus.career import career_names  # start-up code of this module runs here, as before
from solitaireplus.career import real_estate_screen  # start-up code of this module runs here, as before

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
from solitaireplus.career.events import night  # start-up code of this module runs here, as before

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

from solitaireplus.npc.portrait_ui import (draw_portrait as draw_framed_npc_portrait,
                            get_npc_initials)


def get_poker_starting_stack():
    if state.career_cash <= 2000:
        return max(
            0,
            state.career_cash
        )

    return round(
        state.career_cash / 1000
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
        night.CAREER_EVENT_GAMES.get(
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

def get_current_career_activity_index():

    for index, entry in enumerate(
        state.career_current_schedule
    ):

        if (
            entry.get(
                "day_number"
            )
            == state.career_day_of_month
        ):
            return index

    return None


def leave_career_cryptid():
    if not cryptid_screen.claim_result():return False
    try:career_saving.auto_save_career()
    except OSError:
        cryptid_screen.notice='Could not save. Check the saves folder and retry Return.'
        cryptid_screen.collection_view.message=cryptid_screen.notice
        return False
    state.current_state=state_names.STATE_CAREER_HUB
    return True



def maybe_add_monthly_flavor_news():
    if random.random() > 0.72:
        return False

    npc_names = [
        npc.get("name", "")
        for npc in leaderboard_engine.CAREER_LEADERBOARD_PLAYERS
        if isinstance(npc, dict)
    ]
    headline, body, category = build_monthly_flavor_story(npc_names)
    news_screen.add_career_news(headline, body, category)
    return True
from solitaireplus.career import leaderboard_engine  # start-up code of this module runs here, as before
from solitaireplus.app import window  # start-up code of this module runs here, as it did in main.py
window.open_window()
from solitaireplus.ui import backgrounds  # start-up code of this module runs here, as it did in main.py
state.options_return_state = state_names.STATE_MENU
state.customize_return_state = state_names.STATE_MENU
state.profile_return_state = state_names.STATE_MENU
state.profile_select_return_state = state_names.STATE_MENU
career_hub_controls = CareerHubControls()

# ==================================================
# GAME
# ==================================================

game = Game(
    window.game_surface,
    sounds.audio
)

state.player_name = DEFAULT_PLAYER_NAME

state.player_level = DEFAULT_LEVEL
state.player_xp = DEFAULT_XP
state.player_xp_to_next = DEFAULT_XP_TO_NEXT

how_to_play_tab = "basics"

# MINIGAME RUNTIME OBJECTS
blackjack_game = BlackjackGame()
score_four_game = ScoreFourGame()
crazy_eights_game = CrazyEightsGame()
bango_game = BangoGame()

texas_holdem_game = TexasHoldemGame()

TEXAS_HOLDEM_NPC_DELAY = 1200
TEXAS_HOLDEM_STREET_DELAY = 1200

TEXAS_HOLDEM_NEXT_HAND_DELAY = 15000


TEXAS_HOLDEM_SESSION_END_DELAY = 5000

TEXAS_HOLDEM_TABLE_SWEEP_RATING_BONUS = 100

# ==================================================
# FIVE-CARD DRAW RUNTIME
# ==================================================

five_card_draw_game = FiveCardDrawGame()

FIVE_CARD_DRAW_SESSION_END_DELAY = 5000
FIVE_CARD_DRAW_TABLE_SWEEP_RATING_BONUS = 100

# ==================================================
# SEVEN-CARD STUD RUNTIME
# ==================================================

seven_card_stud_game = SevenCardStudGame()

SEVEN_CARD_STUD_SESSION_END_DELAY = 5000
SEVEN_CARD_STUD_TABLE_SWEEP_RATING_BONUS = 100

roulette_game = RouletteGame()
horse_races_game = HorseRaceGame()
from solitaireplus.career import case_opening_screen  # start-up code of this module runs here, as before
state.case_collection_state = new_case_state()
cryptid_screen = CryptidScreen()
state.cryptid_collection_state = new_collection()
state.career_poker_learning = new_learning()
faro_game = FaroGame()
five_o_poker_game = FiveOPokerGame()
blind_mans_bluff_game = BlindMansBluffGame()
king_pong_game = KingPongGame()
battle_bosses_game = BattleBossesGame()
ace_invaders_game = AceInvadersGame()
suit_snake_game = SuitSnakeGame()
dead_mans_hand_game = DeadMansHandGame()
state.dead_mans_hand_return_state = state_names.STATE_DEBUG_MENU
state.arcade_state = make_default_arcade_state()

state.blackjack_dealer_npc = None
career_event_start_arcade_tokens = 0
career_event_start_arcade_tickets = 0
state.career_ratings = make_player_rating_bundle(state.career_rating)

# ==================================================
# ACHIEVEMENTS
# ==================================================
state.achievement_state = make_default_achievement_state()
state.career_bigfoot_story = new_story()
state.career_alien_story = new_alien_story()
from solitaireplus.career.events import event_screen  # start-up code of this module runs here, as before
from solitaireplus.career import jobs_screen  # start-up code of this module runs here, as before




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
        window.game_surface, npc, rect, style_id, NPC_PORTRAIT_STYLES,
        get_npc_portrait_surface, fonts.score_four_score_font
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

npc_icon_cache = {}

state.unlocked_menu_backgrounds = set(
    DEFAULT_UNLOCKED_MENU_BACKGROUNDS
)

state.unlocked_felts = set(
    DEFAULT_UNLOCKED_FELTS
)

state.unlocked_titles = set(
    DEFAULT_UNLOCKED_TITLES
)

state.selected_menu_background = (
    DEFAULT_SELECTED_MENU_BACKGROUND
)

state.selected_felt = (
    DEFAULT_SELECTED_FELT
)

state.selected_title = (
    DEFAULT_SELECTED_TITLE
)


# ==================================================
# PROFILE STATE
# ==================================================

state.profile_name_text = state.player_name
from solitaireplus.profile import profile_editor  # start-up code of this module runs here, as before
from solitaireplus.profile import profile_select  # start-up code of this module runs here, as before
from solitaireplus.app import assets  # start-up code of this module runs here, as it did in main.py
from solitaireplus.ui import cursors  # start-up code of this module runs here, as it did in main.py

# ==================================================
# COSMETIC SYNC
# ==================================================

def sync_selected_cosmetics():
    game.set_felt_surface(
        assets.felt_surfaces[state.selected_felt]
    )


sync_selected_cosmetics()
from solitaireplus.app import fonts  # start-up code of this module runs here, as it did in main.py

state.profile_switch_rect = pygame.Rect(
    630,
    650,
    240,
    48
)
from solitaireplus.menus import customize  # start-up code of this module runs here, as before
from solitaireplus.menus import mode_select  # start-up code of this module runs here, as before

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

free_play_game_rects = {}
for free_index, state.free_game_id in enumerate(FREE_PLAY_GAME_IDS):
    free_column = free_index % 3
    free_row = free_index // 3
    free_play_game_rects[state.free_game_id] = pygame.Rect(
        96 + free_column * 410,
        185 + free_row * 88,
        356,
        64
    )
from solitaireplus.menus import free_play_select  # start-up code of this module runs here, as before

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
from solitaireplus.career.events import summary_screen  # start-up code of this module runs here, as before
from solitaireplus.career.events import event_select_screen  # start-up code of this module runs here, as before

arcade_token_package_rects = {}
for state.package_index in range(len(ARCADE_TOKEN_PACKAGES)):
    row = state.package_index // 2
    column = state.package_index % 2
    arcade_token_package_rects[state.package_index] = pygame.Rect(
        248 + column * 475,
        270 + row * 172,
        395,
        132,
    )

arcade_token_exchange_back_rect = pygame.Rect(128, 658, 240, 54)
arcade_token_exchange_continue_rect = pygame.Rect(998, 658, 240, 54)

ARCADE_PRIZES_PER_PAGE = 4
arcade_prize_card_rects = {
    slot: pygame.Rect(102 + slot * 292, 207, 270, 300)
    for slot in range(ARCADE_PRIZES_PER_PAGE)
}
arcade_prize_prev_rect = pygame.Rect(474, 525, 118, 38)
arcade_prize_next_rect = pygame.Rect(774, 525, 118, 38)
arcade_prize_back_rect = pygame.Rect(106, 658, 220, 54)
arcade_prize_trophy_room_rect = pygame.Rect(573, 658, 220, 54)
arcade_prize_buy_rect = pygame.Rect(1040, 658, 220, 54)
arcade_trophy_room_back_rect = pygame.Rect(503, 658, 360, 54)

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

ace_invaders_difficulty_rects = [
    pygame.Rect(103 + index * 292, 220, 266, 320)
    for index in range(4)
]
ace_invaders_back_rect = pygame.Rect(103, 657, 220, 54)
ace_invaders_tokens_rect = pygame.Rect(573, 657, 220, 54)
ace_invaders_play_rect = pygame.Rect(1043, 657, 220, 54)
ace_invaders_quit_rect = pygame.Rect(1120, 676, 190, 50)

suit_snake_mode_rects = [
    pygame.Rect(103 + index * 292, 212, 266, 300)
    for index in range(4)
]
suit_snake_step_movement_rect = pygame.Rect(438, 548, 230, 52)
suit_snake_smooth_movement_rect = pygame.Rect(698, 548, 230, 52)
suit_snake_back_rect = pygame.Rect(103, 657, 220, 54)
suit_snake_tokens_rect = pygame.Rect(573, 657, 220, 54)
suit_snake_play_rect = pygame.Rect(1043, 657, 220, 54)
# Keep the gameplay Quit control completely outside Suit Snake's playfield
# and footer, including the larger 30x16 board.
suit_snake_quit_rect = pygame.Rect(1155, 660, 190, 50)
from solitaireplus.career import news_screen  # start-up code of this module runs here, as before

career_mode_rect = pygame.Rect(
    383,
    430,
    600,
    100
)

state.career_jobs_rect = pygame.Rect(
    333,
    485,
    300,
    55
)

state.career_real_estate_rect = pygame.Rect(
    733,
    485,
    300,
    55
)

state.career_leaderboards_rect = pygame.Rect(
    333,
    555,
    300,
    55
)

state.career_news_rect = pygame.Rect(
    733,
    555,
    300,
    55
)

state.career_back_rect = pygame.Rect(
    533,
    650,
    300,
    50
)
from solitaireplus.career import leaderboards_screen  # start-up code of this module runs here, as before

state.career_calendar_action_rect = pygame.Rect(
    0,
    0,
    0,
    0
)

state.career_calendar_skip_rect = pygame.Rect(
    0,
    0,
    0,
    0
)
from solitaireplus.career import hub_screen  # start-up code of this module runs here, as before

state.profile_switch_rect = pygame.Rect(
    630,
    650,
    240,
    48
)
from solitaireplus.menus import difficulty_screen  # start-up code of this module runs here, as before
from solitaireplus.profile import recap  # start-up code of this module runs here, as before
from solitaireplus.profile import level_up  # start-up code of this module runs here, as before
from solitaireplus.menus import options_screen  # start-up code of this module runs here, as before

# Temporarily keep the experimental verified-deal generator out of ordinary
# play while it is being rebuilt. Head-to-Head still uses its race-only
# constructive deal path.
VERIFIED_DEALS_ENABLED = False

# ==================================================
# UPDATES AND SAVED OPTIONS
# (update_check.py talks to SolitaireUpdater.exe; app_settings.py stores
#  Options choices in %LOCALAPPDATA%\SimpleSolitaire\app_settings.json)
# ==================================================

from solitaireplus.app import app_settings as app_settings_module

# ==================================================
# CUSTOMIZATION STATE
# ==================================================

CUSTOMIZE_BACKGROUNDS = "backgrounds"

state.customize_category = CUSTOMIZE_BACKGROUNDS

# ==================================================
# STATE
# ==================================================

state.current_state = state_names.STATE_SPLASH

state.post_round_return_state = state_names.STATE_MENU

def _render_blackjack_fit(text, max_width, size=21, bold=False, color=(255, 255, 255), minimum_size=13):
    current_size = int(size)
    while current_size >= minimum_size:
        font = pygame.font.SysFont("cambria", current_size, bold=bold)
        surface = font.render(str(text), True, color)
        if surface.get_width() <= max_width or current_size == minimum_size:
            return surface
        current_size -= 1
    return fonts.blackjack_small_font.render(str(text), True, color)


def _draw_blackjack_panel(rect, fill=(10, 28, 21, 205), border=(220, 190, 100), radius=12):
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, fill, panel.get_rect(), border_radius=radius)
    window.game_surface.blit(panel, rect.topleft)
    pygame.draw.rect(
        window.game_surface,
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

    heading = fonts.blackjack_small_font.render(
        "TONIGHT'S DEALER",
        True,
        (222, 190, 98)
    )
    window.game_surface.blit(
        heading,
        (rect.x + 14, rect.y + 12)
    )

    portrait_rect = pygame.Rect(
        rect.x + 14,
        rect.y + 44,
        88,
        88
    )

    if state.blackjack_dealer_npc is not None:
        draw_npc_portrait(
            state.blackjack_dealer_npc,
            portrait_rect,
            "blackjack"
        )
        dealer_name = state.blackjack_dealer_npc.get("name", "Dealer")
        hometown = state.blackjack_dealer_npc.get("hometown", "Unknown")
        favorite_suit = state.blackjack_dealer_npc.get("favorite_suit", "Unknown")
    else:
        pygame.draw.rect(window.game_surface, (42, 58, 49), portrait_rect)
        pygame.draw.rect(window.game_surface, (215, 215, 215), portrait_rect, 2)
        dealer_name = "Dealer"
        hometown = "Unknown"
        favorite_suit = "Unknown"

    portrait = window.game_surface.subsurface(portrait_rect).copy()
    mask = pygame.Surface(portrait_rect.size, pygame.SRCALPHA)
    pygame.draw.ellipse(mask, (255, 255, 255, 255), mask.get_rect())
    portrait = portrait.convert_alpha()
    portrait.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    pygame.draw.rect(window.game_surface, (13, 25, 32), portrait_rect)
    window.game_surface.blit(portrait, portrait_rect)
    pygame.draw.ellipse(window.game_surface, (207, 225, 233), portrait_rect, 2)

    name_surface = _render_blackjack_fit(
        dealer_name,
        rect.width - 126,
        size=27,
        bold=True,
        color=(255, 255, 255),
        minimum_size=17
    )
    window.game_surface.blit(
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
    window.game_surface.blit(
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
    window.game_surface.blit(
        suit_surface,
        (rect.x + 116, rect.y + 112)
    )


def _draw_blackjack_background():
    from solitaireplus.games.casino.blackjack_presentation import draw_background
    draw_background(window.game_surface, assets.menu_background_surfaces.get(state.selected_menu_background), assets.felt_surfaces.get(state.selected_felt))


def _draw_blackjack_button(rect, label, mouse, font=None, selected=False):
    from solitaireplus.games.casino.blackjack_presentation import draw_button
    draw_button(window.game_surface, rect, label, mouse, font or fonts.blackjack_body_font, selected=selected)


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

    cash_surface = fonts.blackjack_heading_font.render(
        f"Bankroll  ${state.career_cash:,}",
        True,
        (255, 228, 135)
    )
    window.game_surface.blit(
        cash_surface,
        cash_surface.get_rect(center=(bet_panel.centerx, 190))
    )

    prompt = fonts.blackjack_heading_font.render(
        "Choose your opening wager",
        True,
        (245, 245, 240)
    )
    window.game_surface.blit(
        prompt,
        prompt.get_rect(center=(bet_panel.centerx, 245))
    )

    detail = fonts.blackjack_body_font.render(
        "The percentage is calculated from your current bankroll.",
        True,
        (194, 207, 199)
    )
    window.game_surface.blit(
        detail,
        detail.get_rect(center=(bet_panel.centerx, 280))
    )

    if state.career_cash > 0:
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
                state.game_mouse_pos,
                selected=(state.blackjack_selected_bet_percentage == percentage),
                font=fonts.blackjack_small_font
            )
    else:
        broke_surface = fonts.blackjack_heading_font.render(
            "OUT OF CASH",
            True,
            (255, 220, 120)
        )
        window.game_surface.blit(
            broke_surface,
            broke_surface.get_rect(center=(bet_panel.centerx, 365))
        )

        broke_detail = fonts.blackjack_body_font.render(
            "Return to the previous screen to finish the session.",
            True,
            (210, 215, 210)
        )
        window.game_surface.blit(
            broke_detail,
            broke_detail.get_rect(center=(bet_panel.centerx, 410))
        )

    _draw_blackjack_button(
        blackjack_bet_return_rect,
        "Return",
        state.game_mouse_pos,
        font=fonts.blackjack_body_font
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

    dealer_heading = fonts.blackjack_heading_font.render(
        "DEALER",
        True,
        (245, 235, 205)
    )
    window.game_surface.blit(
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
                window.game_surface.blit(
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
                window.game_surface.blit(scaled_image, scaled_rect)
                continue

        card_key = get_card_key(card)
        window.game_surface.blit(
            game.card_fronts[card_key],
            (x, y)
        )

    dealer_value_text = (
        f"Dealer total: {blackjack_game.dealer_value()}"
        if blackjack_game.dealer_hole_is_revealed()
        else "Dealer total: ?"
    )
    dealer_value_surface = fonts.blackjack_body_font.render(
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
    window.game_surface.blit(dealer_value_surface, dealer_value_rect)

    if blackjack_game.is_split_round():
        player_heading = fonts.blackjack_heading_font.render(
            "YOUR SPLIT HANDS",
            True,
            (245, 235, 205)
        )
        window.game_surface.blit(
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

            hand_label = fonts.blackjack_small_font.render(
                f"HAND {hand_index + 1}",
                True,
                (255, 224, 120) if active else (215, 220, 216)
            )
            window.game_surface.blit(
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
                window.game_surface.blit(game.card_fronts[card_key], (x, y))

            value = blackjack_game.get_hand_value_at(hand_index)
            wager = blackjack_game.player_hand_bets[hand_index]
            detail = fonts.blackjack_small_font.render(
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
            window.game_surface.blit(detail, detail_rect)

            if blackjack_game.round_complete:
                hand_result = blackjack_game.get_hand_result(hand_index)
                result_names = {
                    "player": "WIN",
                    "push": "PUSH",
                    "dealer": "LOSS",
                }
                result_label = fonts.blackjack_small_font.render(
                    result_names.get(hand_result, ""),
                    True,
                    (255, 224, 120)
                )
                window.game_surface.blit(
                    result_label,
                    result_label.get_rect(center=(center_x, 625))
                )
    else:
        player_heading = fonts.blackjack_heading_font.render(
            "YOUR HAND",
            True,
            (245, 235, 205)
        )
        window.game_surface.blit(
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
            window.game_surface.blit(
                game.card_fronts[card_key],
                (x, y)
            )

        player_value_surface = fonts.blackjack_body_font.render(
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
        window.game_surface.blit(player_value_surface, player_value_rect)

    # ==================================================
    # Bankroll / next wager panel
    # ==================================================

    panel_title = fonts.blackjack_heading_font.render(
        "TABLE BANK",
        True,
        (255, 225, 130)
    )
    window.game_surface.blit(
        panel_title,
        panel_title.get_rect(center=(right_panel.centerx, 138))
    )

    info_lines = [
        f"Current wager: ${blackjack_game.bet:,}",
        f"Cash: ${state.career_cash:,}",
    ]
    if state.blackjack_session_net > 0:
        session_text = f"Session: +${state.blackjack_session_net:,}"
    elif state.blackjack_session_net < 0:
        session_text = f"Session: -${abs(state.blackjack_session_net):,}"
    else:
        session_text = "Session: $0"
    info_lines.append(session_text)
    if state.current_game_mode == "career":
        info_lines.append(f"Casino: {state.career_ratings['casino']:,} ({state.blackjack_session_rating_change:+d})")

    for index, text in enumerate(info_lines):
        surface = fonts.blackjack_body_font.render(
            text,
            True,
            (235, 238, 235)
        )
        window.game_surface.blit(
            surface,
            (right_panel.x + 20, 182 + index * 34)
        )

    next_bet_heading = fonts.blackjack_heading_font.render(
        "NEXT HAND BET",
        True,
        (255, 225, 130)
    )
    window.game_surface.blit(
        next_bet_heading,
        next_bet_heading.get_rect(center=(right_panel.centerx, 326))
    )

    next_bet_note = fonts.blackjack_small_font.render(
        "Choose your next wager anytime.",
        True,
        (180, 196, 187)
    )
    window.game_surface.blit(
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
        amount = get_blackjack_bet(percentage) if state.career_cash > 0 else 0
        if percentage >= 1.0:
            button_text = f"{label_text}  ${amount:,}"
        else:
            button_text = f"{label_text}  ${amount:,}"
        _draw_blackjack_button(
            blackjack_bet_dropdown_rects[index],
            button_text,
            state.game_mouse_pos,
            selected=(state.blackjack_selected_bet_percentage == percentage),
            font=fonts.blackjack_small_font
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

        result_surface = fonts.blackjack_heading_font.render(
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
        window.game_surface.blit(result_surface, result_rect)

    elif blackjack_game.pending_natural_result is not None:
        reveal_surface = fonts.blackjack_body_font.render(
            "Dealer checks the hole card...",
            True,
            (244, 226, 165)
        )
        window.game_surface.blit(
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
            state.game_mouse_pos,
            font=fonts.blackjack_body_font
        )
        _draw_blackjack_button(
            blackjack_stand_rect,
            "Stand",
            state.game_mouse_pos,
            font=fonts.blackjack_body_font
        )
        if (
                blackjack_game.can_double_down()
                and state.career_cash >= blackjack_game.current_hand_bet()
        ):
            _draw_blackjack_button(
                blackjack_double_rect,
                "Double",
                state.game_mouse_pos,
                font=fonts.blackjack_body_font
            )

        if (
                blackjack_game.can_split()
                and state.career_cash >= blackjack_game.current_hand_bet()
        ):
            _draw_blackjack_button(
                blackjack_split_rect,
                "Split",
                state.game_mouse_pos,
                font=fonts.blackjack_body_font
            )

    elif blackjack_game.round_complete:
        if state.career_cash > 0:
            _draw_blackjack_button(
                blackjack_deal_again_rect,
                "Deal Next Hand",
                state.game_mouse_pos,
                font=fonts.blackjack_body_font
            )
        else:
            out_surface = fonts.blackjack_heading_font.render(
                "OUT OF CASH",
                True,
                (255, 220, 120)
            )
            window.game_surface.blit(
                out_surface,
                out_surface.get_rect(center=blackjack_deal_again_rect.center)
            )

    # Return is intentionally visible throughout the hand, but only clickable
    # after the result. The tooltip explains the disabled state.
    if blackjack_game.round_complete:
        _draw_blackjack_button(
            blackjack_return_rect,
            "Return",
            state.game_mouse_pos,
            font=fonts.blackjack_body_font
        )
    else:
        pygame.draw.rect(
            window.game_surface,
            (68, 76, 72),
            blackjack_return_rect,
            border_radius=7
        )
        pygame.draw.rect(
            window.game_surface,
            (145, 154, 149),
            blackjack_return_rect,
            2,
            border_radius=7
        )
        disabled = fonts.blackjack_body_font.render(
            "Return",
            True,
            (155, 160, 157)
        )
        window.game_surface.blit(
            disabled,
            disabled.get_rect(center=blackjack_return_rect.center)
        )

        if (
                state.game_mouse_pos is not None
                and blackjack_return_rect.collidepoint(state.game_mouse_pos)
        ):
            tooltip = fonts.blackjack_small_font.render(
                "Finish the current hand before leaving.",
                True,
                (255, 255, 255)
            )
            tooltip_rect = tooltip.get_rect(
                midbottom=(blackjack_return_rect.centerx, blackjack_return_rect.y - 8)
            )
            tooltip_bg = tooltip_rect.inflate(18, 10)
            pygame.draw.rect(
                window.game_surface,
                (18, 24, 21),
                tooltip_bg,
                border_radius=6
            )
            window.game_surface.blit(tooltip, tooltip_rect)


def adjust_debug_ratings(amount):
    for key in ("strategy", "poker", "casino"):
        apply_rating_change(state.career_ratings, key, amount, scale_rewards=False)
    state.career_rating = state.career_ratings["overall"]
    career_rewards.grant_rating_cosmetics()


def lose_fans_for_bad_result(reason="Poor performance", net_loss=0, severity=1.0):
    loss = fan_loss_from_bad_result(
        current_fans=state.career_fans,
        net_loss=net_loss,
        severity=severity,
    )
    if loss <= 0:
        return 0
    return career_rewards.award_career_fans(-loss, reason)
from solitaireplus.profile import leveling  # start-up code of this module runs here, as before


def unlock_achievement_cosmetic(reward):
    reward_type = reward.get("type")
    asset_id = reward.get("id")
    if not asset_id:
        return ""

    if reward_type == "background":
        if asset_id in MENU_BACKGROUNDS:
            state.unlocked_menu_backgrounds.add(asset_id)
            return MENU_BACKGROUNDS[asset_id].get("name", asset_id)
        return ""

    if reward_type == "felt":
        if asset_id in FELTS:
            state.unlocked_felts.add(asset_id)
            return FELTS[asset_id].get("name", asset_id)
        return ""

    if reward_type == "title":
        if asset_id in TITLES:
            state.unlocked_titles.add(asset_id)
            return TITLES[asset_id].get("name", asset_id)
        return ""

    return ""


def queue_achievement_popup(definition, fan_reward, cosmetic_label=""):
    state.achievement_popup_queue.append({
        "definition": definition,
        "fans": int(fan_reward or 0),
        "cosmetic": str(cosmetic_label or ""),
    })


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
            label = unlock_achievement_cosmetic(reward)
            if label:
                cosmetic_labels.append(label)
        queue_achievement_popup(
            definition,
            fan_reward,
            ", ".join(cosmetic_labels),
        )
        career_saving.auto_save_career()
        return definition.get("title", "Achievement")

    return None


def update_achievement_popup():

    now = pygame.time.get_ticks()

    if state.achievement_popup_current is not None:
        if now - state.achievement_popup_started >= 4400:
            state.achievement_popup_current = None

    if state.achievement_popup_current is None and state.achievement_popup_queue:
        item = state.achievement_popup_queue.pop(0)
        state.achievement_popup_current = item["definition"]
        state.achievement_popup_fans = item["fans"]
        state.achievement_popup_cosmetic = item["cosmetic"]
        state.achievement_popup_started = now


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
            == state.texas_holdem_last_processed_showdown_hand
    ):
        return

    state.texas_holdem_last_processed_showdown_hand = (
        texas_holdem_game.hand_number
    )
    record_poker_showdown(texas_holdem_game)

    # ==================================================
    # SHOWDOWN AUDIO
    # ==================================================

    sounds.audio.play_sound(
        "card_flip"
    )

    # Player won at least one pot.
    if 0 in texas_holdem_game.winner_indexes:
        state.texas_holdem_hand_win_sound_at = (
                pygame.time.get_ticks()
                + 450
        )
        career_rewards.award_fans_for_cash_win(
            max(1, int(getattr(texas_holdem_game, "last_resolved_pot", 0))),
            "Hold'em hand win"
        )

        holdem_result = texas_holdem_game.get_showdown_result(0)
        holdem_score = holdem_result[0] if holdem_result else None
        leveling.process_achievement_event(
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

        state.texas_holdem_next_hand_at = 0

        texas_holdem_game.result_text += (
            " You are out of chips."
        )

        state.texas_holdem_session_end_at = (
            pygame.time.get_ticks()
            + TEXAS_HOLDEM_SESSION_END_DELAY
        )

        return

    # ==================================================
    # PLAYER CLEARED THE TABLE
    # ==================================================

    if texas_holdem_game.all_npcs_busted():

        state.texas_holdem_next_hand_at = 0

        fan_gain = 0

        if not state.texas_holdem_table_sweep_rewarded:
            leveling.process_achievement_event("poker_table_clear", game="texas_holdem")
            if state.current_game_mode == "career":
                fan_gain = career_rewards.award_fans_for_rating_win(
                    TEXAS_HOLDEM_TABLE_SWEEP_RATING_BONUS,
                    "Hold'em table clear"
                )
                state.career_event_has_activity = True
            state.texas_holdem_table_sweep_rewarded = True

        texas_holdem_game.result_text += " TABLE CLEARED!"
        if state.current_game_mode == "career":
            texas_holdem_game.result_text += (
                " Rating settles on cash-out. "
                f"+{fan_gain:,} Fans."
            )

        state.texas_holdem_session_end_at = (
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

        sounds.audio.play_sound(
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

    sounds.audio.play_sound(
        "card_draw"
    )


def play_texas_holdem_street_sound():

    sounds.audio.play_sound(
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

    sounds.audio.play_sound(
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

        sounds.audio.play_sound(
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

    sounds.audio.play_sound(
        "card_draw"
    )


def play_texas_holdem_street_sound():

    sounds.audio.play_sound(
        "card_draw"
    )


# ==================================================
# SCHEDULE NEXT NPC ACTION
# ==================================================

def debug_setup_holdem_heads_up():

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

    state.texas_holdem_next_npc_action_at = 0
    state.texas_holdem_round_advance_at = 0
    state.texas_holdem_next_hand_at = 0
    state.texas_holdem_session_end_at = 0

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

    if (
            not texas_holdem_game.hand_complete
            and not texas_holdem_game.betting_round_complete
            and texas_holdem_game.current_actor != 0
    ):
        state.texas_holdem_next_npc_action_at = (
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
        state.career_cash
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

    state.career_cash -= (
        starting_stack
    )

    state.texas_holdem_starting_stack = (
        starting_stack
    )

    state.texas_holdem_session_net = 0

    state.texas_holdem_buy_in_active = True
    texas_holdem_game.session_xp_rewarded = False
    state.texas_holdem_last_processed_showdown_hand = 0

    # ==================================================
    # Reset runtime timers
    # ==================================================

    state.texas_holdem_next_npc_action_at = 0
    state.texas_holdem_round_advance_at = 0
    state.texas_holdem_next_hand_at = 0

    # ==================================================
    # Start poker session
    # ==================================================

    texas_holdem_game.career_session_rated = state.current_game_mode == "career"
    texas_holdem_game.learning_store = game_namespace().get("career_poker_learning") if state.current_game_mode == "career" else None
    texas_holdem_game.start_session(
        opponents,
        starting_stack,
        ante
    )

    if texas_holdem_game.start_hand():

        play_texas_holdem_new_hand_sound()

    state.career_event_has_activity = True

    state.current_state = state_names.STATE_TEXAS_HOLDEM

    return True

def finish_texas_holdem_session():

    if state.texas_holdem_buy_in_active:

        state.career_cash += (
            texas_holdem_game.player_stack
        )

        state.texas_holdem_session_net = (
            texas_holdem_game.player_stack
            - state.texas_holdem_starting_stack
        )

        state.texas_holdem_buy_in_active = False
        track_night_cash(game_namespace(), "texas_holdem", state.texas_holdem_session_net)
        career_rewards.rate_poker_cash_out("texas_holdem", texas_holdem_game)

    if (
            texas_holdem_game.current_stage
            != "ready"
    ):

        state.career_event_has_activity = True

    state.texas_holdem_hand_win_sound_at = 0

    if (
            len(getattr(texas_holdem_game, "rating_seen_hands", ())) > 0
            and not getattr(texas_holdem_game, "session_xp_rewarded", False)
    ):
        won_session = state.texas_holdem_session_net > 0
        leveling.award_game_xp("texas_holdem", won=won_session)
        if state.current_game_mode == "career" and state.texas_holdem_session_net < 0:
            lose_fans_for_bad_result(
                "Rough Hold'em session",
                net_loss=abs(state.texas_holdem_session_net),
            )
        texas_holdem_game.session_xp_rewarded = True

    if state.current_game_mode == "free":
        finish_free_play_sandbox()
        state.current_state = state_names.STATE_FREE_PLAY_SELECT
    else:
        state.current_state = state_names.STATE_CAREER_EVENT_SELECT
        career_saving.auto_save_career()

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
        state.five_card_draw_next_npc_action_at = (
                pygame.time.get_ticks()
                + get_holdem_npc_delay()
        )


def start_five_card_draw_session(
        starting_stack=None,
        opponents=None
):

    if starting_stack is None:
        starting_stack = (
            get_poker_starting_stack()
        )

    starting_stack = int(
        starting_stack
    )

    starting_stack = min(
        starting_stack,
        state.career_cash
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

    state.career_cash -= (
        starting_stack
    )

    state.five_card_draw_starting_stack = (
        starting_stack
    )

    state.five_card_draw_session_net = 0
    state.five_card_draw_buy_in_active = True
    five_card_draw_game.session_xp_rewarded = False

    state.five_card_draw_next_npc_action_at = 0
    state.five_card_draw_round_advance_at = 0
    state.five_card_draw_next_hand_at = 0
    state.five_card_draw_session_end_at = 0
    state.five_card_draw_last_processed_showdown_hand = 0
    state.five_card_draw_table_sweep_rewarded = False
    state.five_card_draw_hand_win_sound_at = 0

    reset_five_card_draw_ui_session()

    five_card_draw_game.career_session_rated = state.current_game_mode == "career"
    five_card_draw_game.learning_store = game_namespace().get("career_poker_learning") if state.current_game_mode == "career" else None
    five_card_draw_game.start_session(
        opponents,
        starting_stack,
        blind_unit
    )

    if five_card_draw_game.start_hand():
        sounds.audio.play_sound(
            "card_draw"
        )

    state.career_event_has_activity = True

    state.current_state = state_names.STATE_FIVE_CARD_DRAW

    return True


def finish_five_card_draw_session():

    if state.five_card_draw_buy_in_active:

        state.career_cash += (
            five_card_draw_game.player_stack
        )

        state.five_card_draw_session_net = (
                five_card_draw_game.player_stack
                - state.five_card_draw_starting_stack
        )

        state.five_card_draw_buy_in_active = False
        track_night_cash(game_namespace(), "five_card_draw", state.five_card_draw_session_net)
        career_rewards.rate_poker_cash_out("five_card_draw", five_card_draw_game)

    if (
            five_card_draw_game.current_stage
            != "ready"
    ):
        state.career_event_has_activity = True

    state.five_card_draw_hand_win_sound_at = 0

    state.five_card_draw_next_npc_action_at = 0
    state.five_card_draw_round_advance_at = 0
    state.five_card_draw_next_hand_at = 0
    state.five_card_draw_session_end_at = 0

    if (
            len(getattr(five_card_draw_game, "rating_seen_hands", ())) > 0
            and not getattr(five_card_draw_game, "session_xp_rewarded", False)
    ):
        won_session = state.five_card_draw_session_net > 0
        leveling.award_game_xp("five_card_draw", won=won_session)
        if state.current_game_mode == "career" and state.five_card_draw_session_net < 0:
            lose_fans_for_bad_result(
                "Rough Five-Card Draw session",
                net_loss=abs(state.five_card_draw_session_net),
            )
        five_card_draw_game.session_xp_rewarded = True

    if state.current_game_mode == "free":
        finish_free_play_sandbox()
        state.current_state = state_names.STATE_FREE_PLAY_SELECT
    else:
        state.current_state = state_names.STATE_CAREER_EVENT_SELECT
        career_saving.auto_save_career()


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
        sounds.audio.play_sound(
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

    if not five_card_draw_game.hand_complete:
        return

    if (
            five_card_draw_game.current_stage
            != "showdown"
    ):
        return

    if (
            five_card_draw_game.hand_number
            == state.five_card_draw_last_processed_showdown_hand
    ):
        return

    state.five_card_draw_last_processed_showdown_hand = (
        five_card_draw_game.hand_number
    )
    record_poker_showdown(five_card_draw_game)

    sounds.audio.play_sound(
        "card_flip"
    )

    if 0 in five_card_draw_game.winner_indexes:
        state.five_card_draw_hand_win_sound_at = (
                pygame.time.get_ticks()
                + 450
        )
        career_rewards.award_fans_for_cash_win(
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

        state.five_card_draw_next_hand_at = 0

        if (
                "out of chips"
                not in five_card_draw_game.result_text.lower()
        ):
            five_card_draw_game.result_text += (
                " You are out of chips."
            )

        state.five_card_draw_session_end_at = (
                pygame.time.get_ticks()
                + FIVE_CARD_DRAW_SESSION_END_DELAY
        )

        return

    if five_card_draw_game.all_npcs_busted():

        state.five_card_draw_next_hand_at = 0

        fan_gain = 0

        if not state.five_card_draw_table_sweep_rewarded:
            leveling.process_achievement_event("poker_table_clear", game="five_card_draw")
            if state.current_game_mode == "career":
                fan_gain = career_rewards.award_fans_for_rating_win(
                    FIVE_CARD_DRAW_TABLE_SWEEP_RATING_BONUS,
                    "Five-Card Draw table clear"
                )
                state.career_event_has_activity = True
            state.five_card_draw_table_sweep_rewarded = True

        five_card_draw_game.result_text += " TABLE CLEARED!"
        if state.current_game_mode == "career":
            five_card_draw_game.result_text += (
                " Rating settles on cash-out. "
                f"+{fan_gain:,} Fans."
            )

        state.five_card_draw_session_end_at = (
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
        state.seven_card_stud_next_npc_action_at = (
                pygame.time.get_ticks()
                + get_holdem_npc_delay()
        )


def start_seven_card_stud_session(
        starting_stack=None,
        opponents=None
):

    if starting_stack is None:
        starting_stack = (
            get_poker_starting_stack()
        )

    starting_stack = int(
        starting_stack
    )

    starting_stack = min(
        starting_stack,
        state.career_cash
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

    state.career_cash -= (
        starting_stack
    )

    state.seven_card_stud_starting_stack = (
        starting_stack
    )

    state.seven_card_stud_session_net = 0
    state.seven_card_stud_buy_in_active = True
    seven_card_stud_game.session_xp_rewarded = False

    state.seven_card_stud_next_npc_action_at = 0
    state.seven_card_stud_round_advance_at = 0
    state.seven_card_stud_next_hand_at = 0
    state.seven_card_stud_session_end_at = 0
    state.seven_card_stud_last_processed_showdown_hand = 0
    state.seven_card_stud_table_sweep_rewarded = False
    state.seven_card_stud_hand_win_sound_at = 0

    reset_seven_card_stud_ui_session()

    seven_card_stud_game.career_session_rated = state.current_game_mode == "career"
    seven_card_stud_game.learning_store = game_namespace().get("career_poker_learning") if state.current_game_mode == "career" else None
    seven_card_stud_game.start_session(
        opponents,
        starting_stack,
        base_unit
    )

    if seven_card_stud_game.start_hand():
        sounds.audio.play_sound(
            "card_draw"
        )

    state.career_event_has_activity = True

    state.current_state = state_names.STATE_SEVEN_CARD_STUD

    return True


def finish_seven_card_stud_session():

    if state.seven_card_stud_buy_in_active:
        state.career_cash += (
            seven_card_stud_game.player_stack
        )

        state.seven_card_stud_session_net = (
                seven_card_stud_game.player_stack
                - state.seven_card_stud_starting_stack
        )

        state.seven_card_stud_buy_in_active = False
        track_night_cash(game_namespace(), "seven_card_stud", state.seven_card_stud_session_net)
        career_rewards.rate_poker_cash_out("seven_card_stud", seven_card_stud_game)

    if (
            seven_card_stud_game.current_stage
            != "ready"
    ):
        state.career_event_has_activity = True

    state.seven_card_stud_hand_win_sound_at = 0

    state.seven_card_stud_next_npc_action_at = 0
    state.seven_card_stud_round_advance_at = 0
    state.seven_card_stud_next_hand_at = 0
    state.seven_card_stud_session_end_at = 0

    if (
            len(getattr(seven_card_stud_game, "rating_seen_hands", ())) > 0
            and not getattr(seven_card_stud_game, "session_xp_rewarded", False)
    ):
        won_session = state.seven_card_stud_session_net > 0
        leveling.award_game_xp("seven_card_stud", won=won_session)
        if state.current_game_mode == "career" and state.seven_card_stud_session_net < 0:
            lose_fans_for_bad_result(
                "Rough Seven-Card Stud session",
                net_loss=abs(state.seven_card_stud_session_net),
            )
        seven_card_stud_game.session_xp_rewarded = True

    if state.current_game_mode == "free":
        finish_free_play_sandbox()
        state.current_state = state_names.STATE_FREE_PLAY_SELECT
    else:
        state.current_state = state_names.STATE_CAREER_EVENT_SELECT
        career_saving.auto_save_career()


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
        sounds.audio.play_sound(
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

    if not seven_card_stud_game.hand_complete:
        return

    if (
            seven_card_stud_game.current_stage
            != "showdown"
    ):
        return

    if (
            seven_card_stud_game.hand_number
            == state.seven_card_stud_last_processed_showdown_hand
    ):
        return

    state.seven_card_stud_last_processed_showdown_hand = (
        seven_card_stud_game.hand_number
    )
    record_poker_showdown(seven_card_stud_game)

    sounds.audio.play_sound(
        "card_flip"
    )

    if 0 in seven_card_stud_game.winner_indexes:
        state.seven_card_stud_hand_win_sound_at = (
                pygame.time.get_ticks()
                + 450
        )
        career_rewards.award_fans_for_cash_win(
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
        state.seven_card_stud_next_hand_at = 0

        if (
                "out of chips"
                not in seven_card_stud_game.result_text.lower()
        ):
            seven_card_stud_game.result_text += (
                " You are out of chips."
            )

        state.seven_card_stud_session_end_at = (
                pygame.time.get_ticks()
                + SEVEN_CARD_STUD_SESSION_END_DELAY
        )

        return

    if seven_card_stud_game.all_npcs_busted():
        state.seven_card_stud_next_hand_at = 0

        fan_gain = 0

        if not state.seven_card_stud_table_sweep_rewarded:
            leveling.process_achievement_event("poker_table_clear", game="seven_card_stud")
            if state.current_game_mode == "career":
                fan_gain = career_rewards.award_fans_for_rating_win(
                    SEVEN_CARD_STUD_TABLE_SWEEP_RATING_BONUS,
                    "Seven-Card Stud table clear"
                )
                state.career_event_has_activity = True
            state.seven_card_stud_table_sweep_rewarded = True

        seven_card_stud_game.result_text += " TABLE CLEARED!"
        if state.current_game_mode == "career":
            seven_card_stud_game.result_text += (
                " Rating settles on cash-out. "
                f"+{fan_gain:,} Fans."
            )

        state.seven_card_stud_session_end_at = (
                pygame.time.get_ticks()
                + SEVEN_CARD_STUD_SESSION_END_DELAY
        )


def try_place_or_remove_roulette_bet(
        bet_type,
        bet_value,
        is_right_click
):

    wager = state.roulette_chip_value

    if is_right_click:

        if roulette_game.remove_bet(
                bet_type,
                bet_value,
                wager
        ):

            sounds.audio.play_sound(
                "button_click"
            )

        return

    if (
            wager > 0
            and (
                roulette_game.get_total_bet()
                + wager
            ) <= state.career_cash
    ):

        roulette_game.place_bet(
            bet_type,
            bet_value,
            wager
        )

        sounds.audio.play_sound(
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

    if state.career_cash <= 0:
        return 0

    if percentage >= 1.0:
        return state.career_cash

    return max(
        1,
        round(
            state.career_cash
            * percentage
        )
    )

def settle_roulette_round():

    if not roulette_game.round_complete:
        return

    if roulette_game.payout_claimed:
        return

    payout = (
        roulette_game.get_payout()
    )

    state.career_cash += (
        payout
    )

    net_result = (
        roulette_game.get_net_result()
    )

    state.roulette_session_net += (
        net_result
    )
    roulette_game.rating_change = (career_rewards.rate_house_game("roulette", net_result)
                                   if state.current_game_mode == "career" else None)

    if net_result > 0:
        career_rewards.award_fans_for_cash_win(
            net_result,
            "Roulette win"
        )
    elif state.current_game_mode == "career" and net_result <= -500:
        lose_fans_for_bad_result(
            "Rough Roulette spin",
            net_loss=abs(net_result),
            severity=0.65,
        )

    leveling.award_game_xp(
        "roulette",
        won=(net_result > 0),
        bonus=8 if net_result >= 1000 else 0,
    )

    leveling.process_achievement_event(
        "roulette_round",
        net=net_result,
        bets=[dict(bet) for bet in roulette_game.bets],
    )

    track_night_cash(game_namespace(), "roulette", net_result)
    roulette_game.payout_claimed = True

def settle_blackjack_round():

    if not blackjack_game.round_complete:
        return

    if blackjack_game.payout_claimed:
        return

    payout = blackjack_game.get_payout()

    state.career_cash += payout

    net_result = (
        payout
        - blackjack_game.bet
    )

    state.blackjack_session_net += (
        net_result
    )
    if state.current_game_mode == "career":
        if blackjack_game.is_split_round():
            blackjack_game.rating_change = sum(career_rewards.rate_house_game("blackjack", 1 if result == "player" else -1 if result == "dealer" else 0)
                                               for result in blackjack_game.player_hand_results)
        else:
            blackjack_game.rating_change = career_rewards.rate_house_game("blackjack", net_result)
    else:
        blackjack_game.rating_change = None
    state.blackjack_session_rating_change = game_namespace().get("blackjack_session_rating_change", 0) + int(blackjack_game.rating_change or 0)

    if net_result > 0:
        career_rewards.award_fans_for_cash_win(
            net_result,
            "Blackjack win"
        )
    elif state.current_game_mode == "career" and net_result <= -500:
        lose_fans_for_bad_result(
            "Rough Blackjack hand",
            net_loss=abs(net_result),
            severity=0.65,
        )

    leveling.award_game_xp(
        "blackjack",
        won=(net_result > 0),
        bonus=12 if blackjack_game.result == "blackjack" else 0,
    )

    blackjack_hand_values = [
        blackjack_game.get_hand_value(hand)
        for hand in blackjack_game.get_player_hands()
    ]

    leveling.process_achievement_event(
        "blackjack_round",
        result=blackjack_game.result,
        net=net_result,
        natural=(
            not blackjack_game.is_split_round()
            and len(blackjack_game.player_hand) == 2
            and blackjack_game.player_value() == 21
        ),
        doubled=state.blackjack_round_doubled,
        all_in=state.blackjack_round_all_in,
        stood=bool(getattr(blackjack_game, "player_stood", False)),
        player_total=max(blackjack_hand_values, default=0),
        hit_count=max(
            0,
            blackjack_game.get_total_player_cards()
            - (4 if blackjack_game.is_split_round() else 2)
        ),
        starting_bet=state.blackjack_round_start_bet,
    )

    track_night_cash(game_namespace(), "blackjack", net_result)
    blackjack_game.payout_claimed = True

def settle_horse_race_result():

    if horse_races_game.races_completed <= state.horse_races_last_rewarded_races:
        state.horse_races_session_net = horse_races_game.get_session_net()
        return False

    state.horse_races_last_rewarded_races = horse_races_game.races_completed
    state.horse_races_session_net = horse_races_game.get_session_net()
    state.career_event_has_activity = True

    # Every completed race gets a quick winner celebration. This is separate
    # from whether the player personally held a winning ticket.
    sounds.audio.play_sound("celebration_3")

    if horse_races_game.race_net > 0:
        career_rewards.award_fans_for_cash_win(
            horse_races_game.race_net,
            "Horse race win"
        )

    leveling.award_game_xp(
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
    open_king_pong_opponent_select(refresh=True)


def debug_open_battle_bosses():
    debug_prepare_arcade_night()
    open_battle_bosses_opponent_select(refresh=True)


def debug_open_ace_invaders():
    debug_prepare_arcade_night()
    open_ace_invaders_difficulty_select(reset_selection=True)


def debug_open_suit_snake():
    debug_prepare_arcade_night()
    open_suit_snake_difficulty_select(reset_selection=True)


def start_dead_mans_hand(return_state=None):
    """Launch the isolated raycaster prototype without attaching it to a Night."""

    state.dead_mans_hand_return_state = return_state or state_names.STATE_DEBUG_MENU
    dead_mans_hand_game.start_run()
    dead_mans_hand_game.capture_mouse()
    state.current_state = state_names.STATE_DEAD_MANS_HAND


def exit_dead_mans_hand():
    dead_mans_hand_game.release_mouse()
    state.current_state = state.dead_mans_hand_return_state or state_names.STATE_DEBUG_MENU


def set_arcade_status_message(message, duration_ms=2600):

    state.arcade_status_message = str(message or "")
    state.arcade_status_message_expires = pygame.time.get_ticks() + max(600, int(duration_ms or 0))


def open_arcade_token_exchange(pending_game_id=None):

    state.arcade_pending_launch_game_id = pending_game_id
    state.current_state = state_names.STATE_ARCADE_TOKEN_EXCHANGE


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

    if refresh or len(state.king_pong_opponent_choices) != len(KING_PONG_DIFFICULTIES):
        state.king_pong_opponent_choices = build_king_pong_opponent_choices()
        state.king_pong_selected_opponent_index = None

    state.arcade_pending_launch_game_id = None
    state.current_state = state_names.STATE_KING_PONG_OPPONENT_SELECT


def build_battle_bosses_opponent_choices():
    return build_battle_bosses_choices(NPCS)


def open_battle_bosses_opponent_select(refresh=True):

    if refresh or len(state.battle_bosses_opponent_choices) != len(BATTLE_BOSSES_DIFFICULTIES):
        state.battle_bosses_opponent_choices = build_battle_bosses_opponent_choices()
        state.battle_bosses_selected_choice_index = None

    state.current_state = state_names.STATE_BATTLE_BOSSES_OPPONENT_SELECT


def open_ace_invaders_difficulty_select(reset_selection=False):

    if reset_selection:
        state.ace_invaders_selected_difficulty_index = None

    state.arcade_pending_launch_game_id = None
    state.current_state = state_names.STATE_ACE_INVADERS_DIFFICULTY_SELECT


def get_selected_ace_invaders_difficulty():
    difficulty_ids = list(ACE_INVADERS_DIFFICULTIES)
    if (
            state.ace_invaders_selected_difficulty_index is None
            or state.ace_invaders_selected_difficulty_index < 0
            or state.ace_invaders_selected_difficulty_index >= len(difficulty_ids)
    ):
        return None
    return difficulty_ids[state.ace_invaders_selected_difficulty_index]


def open_suit_snake_difficulty_select(reset_selection=False):
    """Open Suit Snake's mode/movement setup screen.

    The state name is retained for debug/navigation compatibility even though
    Suit Snake now selects cabinet modes instead of speed difficulties.
    """

    if reset_selection:
        state.suit_snake_selected_mode_index = None
        state.suit_snake_selected_movement_style = "step"

    state.arcade_pending_launch_game_id = None
    state.current_state = state_names.STATE_SUIT_SNAKE_DIFFICULTY_SELECT


def get_selected_suit_snake_mode():
    mode_ids = list(SUIT_SNAKE_MODES)
    if (
            state.suit_snake_selected_mode_index is None
            or state.suit_snake_selected_mode_index < 0
            or state.suit_snake_selected_mode_index >= len(mode_ids)
    ):
        return None
    return mode_ids[state.suit_snake_selected_mode_index]


def get_selected_suit_snake_difficulty():
    """Backward-compatible alias for older integration paths/tests."""
    return get_selected_suit_snake_mode()

def get_selected_battle_bosses_choice():
    if (
            state.battle_bosses_selected_choice_index is None
            or state.battle_bosses_selected_choice_index < 0
            or state.battle_bosses_selected_choice_index >= len(state.battle_bosses_opponent_choices)
    ):
        return None
    return state.battle_bosses_opponent_choices[state.battle_bosses_selected_choice_index]


def get_selected_king_pong_choice():
    if (
            state.king_pong_selected_opponent_index is None
            or state.king_pong_selected_opponent_index < 0
            or state.king_pong_selected_opponent_index >= len(state.king_pong_opponent_choices)
    ):
        return None
    return state.king_pong_opponent_choices[state.king_pong_selected_opponent_index]


def start_king_pong_session():

    selected = get_selected_king_pong_choice()
    if selected is None:
        open_king_pong_opponent_select(refresh=True)
        set_arcade_status_message("Choose a King Pong rival first.")
        return False

    token_cost = get_machine_cost("king_pong")
    success, updated_state = spend_tokens(state.arcade_state, token_cost)
    if not success:
        set_arcade_status_message("Not enough tokens. Buy more to play King Pong.")
        open_arcade_token_exchange("king_pong")
        return False

    state.arcade_state = updated_state
    state.arcade_night_tokens_spent += token_cost
    state.arcade_pending_launch_game_id = None
    state.career_event_has_activity = True

    difficulty_id = selected.get("difficulty_id", "medium")
    opponent = selected.get("npc") or {"name": "Arcade Rival", "skill_tier": "mid"}
    king_pong_game.start_match(
        opponent,
        difficulty_id=difficulty_id,
        target_score=5,
        player_name=state.player_name,
    )
    career_saving.auto_save_career()
    state.current_state = state_names.STATE_KING_PONG
    return True


def claim_king_pong_result():

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

    state.arcade_state = register_king_pong_result(
        state.arcade_state,
        king_pong_game.player_won,
        tickets,
    )
    state.arcade_night_tickets_won += tickets
    state.career_event_has_activity = True

    night.record_career_event_result(
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
    career_saving.auto_save_career()
    return True


def finish_king_pong_session():

    claim_king_pong_result()
    state.current_state = state_names.STATE_CAREER_EVENT_SELECT


def start_battle_bosses_session():

    selected = get_selected_battle_bosses_choice()
    if selected is None:
        open_battle_bosses_opponent_select(refresh=True)
        set_arcade_status_message("Choose a Battle Bosses squad first.")
        return False

    token_cost = get_machine_cost("battle_bosses")
    success, updated_state = spend_tokens(state.arcade_state, token_cost)
    if not success:
        set_arcade_status_message("Not enough tokens. Buy more to enter Battle Bosses.")
        open_arcade_token_exchange("battle_bosses")
        return False

    state.arcade_state = updated_state
    state.arcade_night_tokens_spent += token_cost
    state.arcade_pending_launch_game_id = None
    state.career_event_has_activity = True

    difficulty_id = selected.get("difficulty_id", "standard")
    config = selected.get("config") or BATTLE_BOSSES_DIFFICULTIES.get(
        difficulty_id, BATTLE_BOSSES_DIFFICULTIES["standard"]
    )
    battle_bosses_game.start_match(
        selected.get("npcs") or [],
        difficulty_id=difficulty_id,
        difficulty_config=config,
        player_name=state.player_name,
    )
    career_saving.auto_save_career()
    state.current_state = state_names.STATE_BATTLE_BOSSES
    return True


def claim_battle_bosses_result():

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

    state.arcade_state = register_battle_bosses_result(
        state.arcade_state,
        battle_bosses_game.player_won,
        tickets,
        rivals_eliminated=battle_bosses_game.rivals_eliminated,
    )
    state.arcade_night_tickets_won += tickets
    state.career_event_has_activity = True

    night.record_career_event_result(
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
    career_saving.auto_save_career()
    return True


def finish_battle_bosses_session():

    claim_battle_bosses_result()
    state.current_state = state_names.STATE_CAREER_EVENT_SELECT


def start_ace_invaders_session():

    difficulty_id = get_selected_ace_invaders_difficulty()
    if difficulty_id is None:
        open_ace_invaders_difficulty_select(reset_selection=False)
        set_arcade_status_message("Choose an Ace Invaders difficulty first.")
        return False

    token_cost = get_machine_cost("ace_invaders")
    success, updated_state = spend_tokens(state.arcade_state, token_cost)
    if not success:
        set_arcade_status_message("Not enough tokens. Buy more to play Ace Invaders.")
        open_arcade_token_exchange("ace_invaders")
        return False

    state.arcade_state = updated_state
    state.arcade_night_tokens_spent += token_cost
    state.arcade_pending_launch_game_id = None
    state.career_event_has_activity = True

    saved_high_score = int(
        state.arcade_state.get("stats", {}).get("ace_invaders_high_score", 0) or 0
    )
    ace_invaders_game.start_session(
        difficulty_id,
        high_score=saved_high_score,
    )
    career_saving.auto_save_career()
    state.current_state = state_names.STATE_ACE_INVADERS
    return True


def claim_ace_invaders_result():

    if ace_invaders_game.reward_claimed or not ace_invaders_game.finished:
        return False

    if ace_invaders_game.forfeited:
        base_tickets = 0
        tickets = 0
    else:
        base_tickets = award_ace_invaders_tickets(
            ace_invaders_game.score,
            ace_invaders_game.waves_cleared,
        )
        tickets = max(
            0,
            int(round(base_tickets * ace_invaders_game.ticket_multiplier)),
        )

    state.arcade_state = register_ace_invaders_result(
        state.arcade_state,
        None,
        tickets,
        score=ace_invaders_game.score,
        enemies_destroyed=ace_invaders_game.enemies_destroyed,
        waves_cleared=ace_invaders_game.waves_cleared,
    )
    state.arcade_night_tickets_won += tickets
    state.career_event_has_activity = True

    night.record_career_event_result(
        "ace_invaders",
        won=None,
        tickets=tickets,
        base_tickets=base_tickets,
        ticket_multiplier=ace_invaders_game.ticket_multiplier,
        difficulty=ace_invaders_game.difficulty_id,
        tokens_spent=get_machine_cost("ace_invaders"),
        score=ace_invaders_game.score,
        high_score=ace_invaders_game.high_score,
        waves_cleared=ace_invaders_game.waves_cleared,
        enemies_destroyed=ace_invaders_game.enemies_destroyed,
        lives=ace_invaders_game.lives,
        accuracy=ace_invaders_game.accuracy_percent,
        forfeited=bool(ace_invaders_game.forfeited),
        fan_impact=False,
    )

    ace_invaders_game.reward_claimed = True
    career_saving.auto_save_career()
    return True


def finish_ace_invaders_session():

    claim_ace_invaders_result()
    state.current_state = state_names.STATE_CAREER_EVENT_SELECT


def start_suit_snake_session():

    mode_id = get_selected_suit_snake_mode()
    if mode_id is None:
        open_suit_snake_difficulty_select(reset_selection=False)
        set_arcade_status_message("Choose a Suit Snake mode first.")
        return False

    movement_style = (
        state.suit_snake_selected_movement_style
        if state.suit_snake_selected_movement_style in SUIT_SNAKE_MOVEMENT_STYLES
        else "step"
    )

    token_cost = get_machine_cost("suit_snake")
    success, updated_state = spend_tokens(state.arcade_state, token_cost)
    if not success:
        set_arcade_status_message("Not enough tokens. Buy more to play Suit Snake.")
        open_arcade_token_exchange("suit_snake")
        return False

    state.arcade_state = updated_state
    state.arcade_night_tokens_spent += token_cost
    state.arcade_pending_launch_game_id = None
    state.career_event_has_activity = True

    saved_high_score = int(
        state.arcade_state.get("stats", {}).get("suit_snake_high_score", 0) or 0
    )
    suit_snake_game.start_session(
        mode_id,
        movement_style=movement_style,
        high_score=saved_high_score,
    )
    career_saving.auto_save_career()
    state.current_state = state_names.STATE_SUIT_SNAKE
    return True

def claim_suit_snake_result():

    if suit_snake_game.reward_claimed or not suit_snake_game.finished:
        return False

    if suit_snake_game.forfeited:
        base_tickets = 0
        tickets = 0
    else:
        base_tickets = award_suit_snake_tickets(
            suit_snake_game.score,
            suit_snake_game.cards_collected,
            suit_snake_game.decks_completed,
        )
        tickets = max(
            0,
            int(round(base_tickets * suit_snake_game.ticket_multiplier)),
        )

    state.arcade_state = register_suit_snake_result(
        state.arcade_state,
        tickets,
        score=suit_snake_game.score,
        cards_collected=suit_snake_game.cards_collected,
        decks_completed=suit_snake_game.decks_completed,
        chain_length=suit_snake_game.chain_length,
    )
    state.arcade_night_tickets_won += tickets
    state.career_event_has_activity = True

    night.record_career_event_result(
        "suit_snake",
        won=None,
        tickets=tickets,
        base_tickets=base_tickets,
        ticket_multiplier=suit_snake_game.ticket_multiplier,
        difficulty=suit_snake_game.mode_id,
        mode=suit_snake_game.mode_id,
        movement=suit_snake_game.movement_style,
        tokens_spent=get_machine_cost("suit_snake"),
        score=suit_snake_game.score,
        high_score=suit_snake_game.high_score,
        cards_collected=suit_snake_game.cards_collected,
        decks_completed=suit_snake_game.decks_completed,
        chain_length=suit_snake_game.chain_length,
        forfeited=bool(suit_snake_game.forfeited),
        fan_impact=False,
    )

    suit_snake_game.reward_claimed = True
    career_saving.auto_save_career()
    return True


def finish_suit_snake_session():

    claim_suit_snake_result()
    state.current_state = state_names.STATE_CAREER_EVENT_SELECT


def start_crazy_eights_session():

    opponents = get_random_npc_group(3)
    crazy_eights_game.start_game(opponents)

    state.current_state = state_names.STATE_CRAZY_EIGHTS



def claim_crazy_eights_result():

    if crazy_eights_game.reward_claimed:
        return

    state.career_event_has_activity = True

    player_won = (crazy_eights_game.winner_index == 0)
    night.record_career_event_result(
        "crazy_eights",
        won=player_won,
    )

    if player_won:
        rating_gain = 60
        career_rewards.award_fans_for_rating_win(
            rating_gain,
            "Crazy Eights win"
        )

    leveling.award_game_xp("crazy_eights", won=player_won)
    crazy_eights_game.reward_claimed = True



def start_bango_session():

    opponents = get_random_npc_group(3)
    bango_game.start_game(
        opponents,
        hand_size=5
    )

    state.current_state = state_names.STATE_BANGO



def claim_bango_result():

    if bango_game.reward_claimed:
        return

    state.career_event_has_activity = True

    player_won = (bango_game.winner_index == 0)
    night.record_career_event_result(
        "bango",
        won=player_won,
    )

    if player_won:
        rating_gain = 35
        career_rewards.award_fans_for_rating_win(
            rating_gain,
            "Bango win"
        )

    leveling.award_game_xp("bango", won=player_won)
    bango_game.reward_claimed = True



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
    start_crazy_eights_session()



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
    start_bango_session()



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

    score_four_game.start_solo_session()

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

    roulette_game.reset_round()

    state.current_state = state_names.STATE_ROULETTE

def start_horse_race_music():

    if state.horse_race_music_sound is None:
        return False

    if state.horse_race_music_channel is not None:
        try:
            if state.horse_race_music_channel.get_busy():
                return True
        except pygame.error:
            pass

    state.horse_race_previous_music_volume = float(sounds.audio.music_volume)
    sounds.audio.set_music_volume(state.horse_race_previous_music_volume * 0.22)

    try:
        state.horse_race_music_channel = pygame.mixer.find_channel(True)
        if state.horse_race_music_channel is None:
            sounds.audio.set_music_volume(state.horse_race_previous_music_volume)
            return False

        state.horse_race_music_channel.set_volume(
            max(0.0, min(1.0, state.horse_race_previous_music_volume * 0.70))
        )
        state.horse_race_music_channel.play(
            state.horse_race_music_sound,
            loops=-1,
            fade_ms=250,
        )
        return True
    except pygame.error:
        sounds.audio.set_music_volume(state.horse_race_previous_music_volume)
        state.horse_race_music_channel = None
        return False


def stop_horse_race_music(fade_ms=500):

    if state.horse_race_music_channel is not None:
        try:
            state.horse_race_music_channel.fadeout(max(0, int(fade_ms)))
        except pygame.error:
            pass

    state.horse_race_music_channel = None

    if state.horse_race_previous_music_volume is not None:
        sounds.audio.set_music_volume(state.horse_race_previous_music_volume)

    state.horse_race_previous_music_volume = None


def start_horse_races_session():

    state.horse_races_session_net = 0
    state.horse_races_last_rewarded_races = 0
    horse_races_game.start_session(state.career_cash)
    state.current_state = state_names.STATE_HORSE_RACES
    return True


def finish_horse_races_session():

    state.career_cash = horse_races_game.cash_out()
    state.horse_races_session_net = horse_races_game.get_session_net()

    if horse_races_game.races_completed > 0:
        state.career_event_has_activity = True

    if (
            state.current_game_mode == "career"
            and horse_races_game.races_completed > 0
            and not horse_races_game.reward_claimed
    ):
        night.record_career_event_result(
            "horse_races",
            won=(state.horse_races_session_net > 0),
            net=state.horse_races_session_net,
            races=horse_races_game.races_completed,
            profitable_races=horse_races_game.races_with_profit,
        )
        track_night_cash(game_namespace(), "horse_races", state.horse_races_session_net)
        horse_races_game.reward_claimed = True

    if state.current_game_mode == "free":
        finish_free_play_sandbox()
        state.current_state = state_names.STATE_FREE_PLAY_SELECT
    else:
        state.current_state = state_names.STATE_CAREER_EVENT_SELECT

    return state.horse_races_session_net


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
    return start_horse_races_session()


def start_faro_session():

    state.faro_session_net = 0
    faro_game.start_session(state.career_cash)
    state.current_state = state_names.STATE_FARO
    return True


def claim_faro_session_result():

    if faro_game.reward_claimed:
        state.career_cash = faro_game.cash_out()
        return state.faro_session_net

    state.career_cash = faro_game.cash_out()
    state.faro_session_net = faro_game.get_session_net()

    if faro_game.turns_dealt <= 0 or faro_game.wagered_total <= 0:
        faro_game.reward_claimed = True
        return state.faro_session_net

    state.career_event_has_activity = True

    strong_threshold = max(500, int(faro_game.starting_cash * 0.25))
    bad_threshold = max(100, int(faro_game.starting_cash * 0.10))

    if state.faro_session_net >= strong_threshold:
        reward_key = "strong_profit"
    elif state.faro_session_net > 0:
        reward_key = "profit"
    elif state.faro_session_net <= -bad_threshold:
        reward_key = "bad_session"
    else:
        reward_key = "break_even"

    rating_gain = TRAINING_RATING_REWARDS["faro"][reward_key]

    if state.faro_session_net > 0:
        career_rewards.award_fans_for_cash_win(
            state.faro_session_net,
            "Faro profit"
        )

    leveling.award_game_xp(
        "faro",
        won=(state.faro_session_net > 0),
    )

    night.record_career_event_result(
        "faro",
        won=(state.faro_session_net > 0),
        net=state.faro_session_net,
        turns=faro_game.turns_dealt,
    )

    track_night_cash(game_namespace(), "faro", state.faro_session_net)
    faro_game.reward_claimed = True
    return state.faro_session_net


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
    start_faro_session()


# ==================================================
# FIVE-O POKER / BLIND MAN'S BLUFF HELPERS
# ==================================================

def get_niche_poker_starting_stack(minimum_buy_in=100):
    if state.career_cash < minimum_buy_in:
        return 0
    if state.career_cash <= 500:
        return state.career_cash
    return min(
        state.career_cash,
        2000,
        max(minimum_buy_in, int(round(state.career_cash * 0.25)))
    )

def start_five_o_poker_session(starting_stack=None):

    if starting_stack is None:
        starting_stack = get_niche_poker_starting_stack(
            FIVE_O_POKER_MIN_BUY_IN
        )

    starting_stack = min(max(0, int(starting_stack)), state.career_cash)
    if starting_stack < FIVE_O_POKER_MIN_BUY_IN:
        return False

    opponent = get_random_npc()
    if opponent is None:
        return False

    state.career_cash -= starting_stack
    state.five_o_poker_starting_stack = starting_stack
    state.five_o_poker_session_net = 0
    state.five_o_poker_buy_in_active = True
    five_o_poker_game.session_xp_rewarded = False

    if not five_o_poker_game.start_session(opponent, starting_stack):
        state.career_cash += starting_stack
        state.five_o_poker_buy_in_active = False
        return False

    state.career_event_has_activity = True
    state.current_state = state_names.STATE_FIVE_O_POKER
    sounds.audio.play_sound("card_shuffle")
    return True


def finish_five_o_poker_session():

    if state.five_o_poker_buy_in_active:
        state.career_cash += five_o_poker_game.player_stack
        state.five_o_poker_session_net = (
            five_o_poker_game.player_stack - state.five_o_poker_starting_stack
        )
        state.five_o_poker_buy_in_active = False

    if five_o_poker_game.hands_played > 0:
        state.career_event_has_activity = True

    won_five_o_session = (
        state.five_o_poker_session_net > 0
        or five_o_poker_game.hands_won > five_o_poker_game.hands_lost
    )

    if (
            five_o_poker_game.hands_played > 0
            and not getattr(five_o_poker_game, "session_xp_rewarded", False)
    ):
        leveling.award_game_xp("five_o_poker", won=won_five_o_session)
        five_o_poker_game.session_xp_rewarded = True

    if (
            state.current_game_mode == "career"
            and five_o_poker_game.hands_played > 0
            and not five_o_poker_game.reward_claimed
    ):
        rating_gain = career_rewards.rate_poker_cash_out(
            "five_o_poker",
            five_o_poker_game,
        )

        won_session = won_five_o_session
        if won_session:
            career_rewards.award_fans_for_rating_win(
                rating_gain,
                "Five-O Poker session"
            )

        night.record_career_event_result(
            "five_o_poker",
            won=won_session,
            net=state.five_o_poker_session_net,
            hands=five_o_poker_game.hands_played,
            hands_won=five_o_poker_game.hands_won,
            five_o_wins=five_o_poker_game.five_o_wins,
            rating_reward=rating_gain,
        )
        track_night_cash(game_namespace(), "five_o_poker", state.five_o_poker_session_net)
        five_o_poker_game.reward_claimed = True

    if state.current_game_mode == "free":
        finish_free_play_sandbox()
        state.current_state = state_names.STATE_FREE_PLAY_SELECT
    else:
        state.current_state = state_names.STATE_CAREER_EVENT_SELECT


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
    if start_five_o_poker_session():
        return True
    # Nothing started (not enough cash). Leave "debug" only if this launcher switched it on:
    # an earlier debug session the player goes back to must stay in "debug" mode.
    if entered_debug_mode:
        end_debug_game_mode()
    restore_night_context(saved_night)   # the night in progress, untouched
    return False


def start_blind_mans_bluff_session(starting_stack=None):

    if starting_stack is None:
        starting_stack = get_niche_poker_starting_stack(
            BLIND_MANS_BLUFF_MIN_BUY_IN
        )

    starting_stack = min(max(0, int(starting_stack)), state.career_cash)
    if starting_stack < BLIND_MANS_BLUFF_MIN_BUY_IN:
        return False

    opponents = get_random_npc_group(3)
    if len(opponents) < 3:
        return False

    state.career_cash -= starting_stack
    state.blind_mans_bluff_starting_stack = starting_stack
    state.blind_mans_bluff_session_net = 0
    state.blind_mans_bluff_buy_in_active = True
    blind_mans_bluff_game.session_xp_rewarded = False

    if not blind_mans_bluff_game.start_session(opponents, starting_stack):
        state.career_cash += starting_stack
        state.blind_mans_bluff_buy_in_active = False
        return False

    state.career_event_has_activity = True
    state.current_state = state_names.STATE_BLIND_MANS_BLUFF
    sounds.audio.play_sound("card_shuffle")
    return True


def finish_blind_mans_bluff_session():

    if state.blind_mans_bluff_buy_in_active:
        state.career_cash += blind_mans_bluff_game.player_stack
        state.blind_mans_bluff_session_net = (
            blind_mans_bluff_game.player_stack
            - state.blind_mans_bluff_starting_stack
        )
        state.blind_mans_bluff_buy_in_active = False

    if blind_mans_bluff_game.hands_played > 0:
        state.career_event_has_activity = True

    won_bluff_session = (
        state.blind_mans_bluff_session_net > 0
        or blind_mans_bluff_game.hands_won > blind_mans_bluff_game.hands_lost
    )

    if (
            blind_mans_bluff_game.hands_played > 0
            and not getattr(blind_mans_bluff_game, "session_xp_rewarded", False)
    ):
        leveling.award_game_xp("blind_mans_bluff", won=won_bluff_session)
        blind_mans_bluff_game.session_xp_rewarded = True

    if (
            state.current_game_mode == "career"
            and blind_mans_bluff_game.hands_played > 0
            and not blind_mans_bluff_game.reward_claimed
    ):
        if state.blind_mans_bluff_session_net > 0:
            reward_key = "profit"
        elif state.blind_mans_bluff_session_net == 0:
            reward_key = "break_even"
        else:
            reward_key = "loss"

        rating_gain = TRAINING_RATING_REWARDS["blind_mans_bluff"][reward_key]
    
        won_session = won_bluff_session
        if won_session:
            career_rewards.award_fans_for_rating_win(
                rating_gain,
                "Blind Man's Bluff session"
            )

        night.record_career_event_result(
            "blind_mans_bluff",
            won=won_session,
            net=state.blind_mans_bluff_session_net,
            hands=blind_mans_bluff_game.hands_played,
            hands_won=blind_mans_bluff_game.hands_won,
        )
        track_night_cash(game_namespace(), "blind_mans_bluff", state.blind_mans_bluff_session_net)
        blind_mans_bluff_game.reward_claimed = True

    if state.current_game_mode == "free":
        finish_free_play_sandbox()
        state.current_state = state_names.STATE_FREE_PLAY_SELECT
    else:
        state.current_state = state_names.STATE_CAREER_EVENT_SELECT


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
    if start_blind_mans_bluff_session():
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


def get_debug_poker_selected_npcs():
    selected = []
    selected_ids = set(state.debug_poker_selected_ids)
    for npc_id in state.debug_poker_selected_ids:
        for npc in NPCS:
            if npc.get("id") == npc_id:
                selected.append(npc)
                break
    return selected[:4]


def start_debug_selected_poker_table():

    opponents = get_debug_poker_selected_npcs()
    if len(opponents) < 4:
        return False

    if state.debug_poker_select_game_id == "texas_holdem":
        return start_texas_holdem_session(opponents=opponents)
    if state.debug_poker_select_game_id == "five_card_draw":
        return start_five_card_draw_session(opponents=opponents)
    if state.debug_poker_select_game_id == "seven_card_stud":
        return start_seven_card_stud_session(opponents=opponents)
    return False


def debug_open_solitaire_challenge(
        challenge_id
):

    state.pending_career_activity_index = None
    state.pending_career_activity_type = None
    state.pending_career_challenge_id = None

    entered_debug_mode = enter_debug_game_mode()

    game.clear_challenge()
    game.set_difficulty(
        DEFAULT_DIFFICULTY
    )

    if not game.set_challenge(
            challenge_id
    ):
        if entered_debug_mode:
            end_debug_game_mode()   # nothing started: leave only the "debug" mode this switched on
        return False

    game.new_game()

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


def finish_free_play_sandbox():

    if state.free_play_snapshot is not None:
        state.career_rating = state.free_play_snapshot["career_rating"]
        state.career_ratings = copy.deepcopy(state.free_play_snapshot["career_ratings"])
        state.career_cash = state.free_play_snapshot["career_cash"]
        state.career_fans = state.free_play_snapshot["career_fans"]
        state.career_fan_news_milestones = set(
            state.free_play_snapshot["career_fan_news_milestones"]
        )
        state.career_fan_trend[:] = list(
            state.free_play_snapshot.get("career_fan_trend", state.career_fan_trend)
        )
        state.career_news_items = copy.deepcopy(
            state.free_play_snapshot["career_news_items"]
        )
        state.career_rounds_won = state.free_play_snapshot["career_rounds_won"]
        state.career_challenges_won = state.free_play_snapshot["career_challenges_won"]
        state.career_total_moves = state.free_play_snapshot["career_total_moves"]
        state.career_event_result_log = copy.deepcopy(
            state.free_play_snapshot["career_event_result_log"]
        )
        state.career_event_has_activity = state.free_play_snapshot[
            "career_event_has_activity"
        ]

    if state.free_play_snapshot is not None:
        state.blackjack_session_rating_change = state.free_play_snapshot.get("blackjack_session_rating_change", 0)

    state.career_event_entry = None
    state.free_play_snapshot = None

    if state.free_play_achievement_fans_earned > 0:
        career_rewards.award_career_fans(
            state.free_play_achievement_fans_earned,
            "Free Play achievement rewards"
        )
        state.free_play_achievement_fans_earned = 0
        career_saving.auto_save_career()


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
        finish_free_play_sandbox()

    if free_mode:
        state.current_game_mode = "career"
    if saved_free_mode:
        state.debug_saved_game_mode = "career"

    if sandbox_running:
        state.debug_previous_state = state_names.STATE_FREE_PLAY_SELECT

    return True


def get_free_play_return_state():
    return state_names.STATE_FREE_PLAY_SELECT if state.current_game_mode == "free" else state_names.STATE_CAREER_EVENT_SELECT


def leave_free_play_game():
    if state.current_game_mode == "free":
        finish_free_play_sandbox()
        state.current_state = state_names.STATE_FREE_PLAY_SELECT
        return True
    return False


def debug_start_next_career_month(save=True):

    if state.current_game_mode == "free":
        finish_free_play_sandbox()
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
    maybe_add_monthly_flavor_news()

    state.career_current_schedule = (
        calendar.build_default_career_schedule()
    )

    if save:
        career_saving.auto_save_career()

def debug_add_career_prospect(prodigy=False):
    if state.current_game_mode == "free":
        finish_free_play_sandbox()
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
        finish_free_play_sandbox()
    state.current_game_mode = "career"
    leaderboard_engine.ensure_career_leaderboard()
    calendar.reset_career_hub_runtime()
    for _ in range(12):
        debug_start_next_career_month(save=False)
    career_saving.auto_save_career()
    state.current_state = state_names.STATE_CAREER_HUB



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
        state.player_level
        >= required_level
    )

def get_profile_avatar():

    avatar_surface = pygame.Surface(
        (
            300,
            360
        ),
        pygame.SRCALPHA
    )

    # B11: a part that is missing from its bank (for example the "base_01"
    # fallback when that file is absent) is skipped instead of raising
    # KeyError; the other layers still draw.
    layers = (
        (assets.avatar_bases, state.selected_avatar_base),
        (assets.avatar_eyes, state.selected_avatar_eyes),
        (assets.avatar_hair, state.selected_avatar_hair),
        (assets.avatar_glasses, state.selected_avatar_glasses),
        (assets.avatar_tops, state.selected_avatar_top),
    )

    for bank, key in layers:
        if key is None:
            continue
        layer = bank.get(key)
        if layer is not None:
            avatar_surface.blit(layer, (0, 0))

    return avatar_surface
from solitaireplus.ui import text as ui_text  # start-up code of this module runs here, as it did in main.py

def draw_score_four_opponent_select():
    from solitaireplus.games.cards.score_four_ui import background, logo, text
    background(window.game_surface)
    logo(window.game_surface)
    text(window.game_surface, 'Choose a rival', (683, 140), 32, center=True)
    text(window.game_surface, 'Win rewards include your Strategy rating adjustment', (683, 614), 24, center=True)

    for index, npc in enumerate(
            state.score_four_opponent_choices
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
            state.game_mouse_pos is not None
            and rect.collidepoint(
                state.game_mouse_pos
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

        window.game_surface.blit(
            panel,
            rect.topleft
        )

        pygame.draw.rect(
            window.game_surface,
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
            fonts.option_label_font.render(
                npc["name"],
                True,
                (
                    255,
                    255,
                    255
                )
            )
        )

        window.game_surface.blit(
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
            fonts.score_four_round_font.render(
                tier_text,
                True,
                (
                    255,
                    230,
                    0
                )
            )
        )

        window.game_surface.blit(
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
            fonts.difficulty_detail_font.render(
                npc["hometown"],
                True,
                (
                    220,
                    220,
                    220
                )
            )
        )

        window.game_surface.blit(
            location_surface,
            (
                rect.x + 145,
                rect.y + 95
            )
        )

        if state.current_game_mode != "free":
            gain = career_rewards.preview_competitive_rating("score_four", npc, True)
            loss = career_rewards.preview_competitive_rating("score_four", npc, False)
            reward_text = f"Win {gain:+d} / Loss {loss:+d} Strategy"
        else:
            reward_text = "Practice • No rating changes"
        reward_label = ui_text.get_font(None, 24).render(reward_text, True, (225, 239, 244))
        window.game_surface.blit(reward_label, reward_label.get_rect(center=(rect.centerx, rect.bottom - 24)))

    buttons.draw_menu_button(
        score_four_opponent_return_rect,
        "Return",
        state.game_mouse_pos,
        font=fonts.difficulty_detail_font
    )

def draw_score_four_npc_panel():

    if (
            score_four_game.mode
            != "competitive"
            or state.score_four_opponent_npc is None
    ):
        return

    npc_panel = pygame.Rect(
        1040,
        180,
        285,
        235
    )

    pygame.draw.rect(
        window.game_surface,
        (
            25,
            45,
            30
        ),
        npc_panel
    )

    pygame.draw.rect(
        window.game_surface,
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
        state.score_four_opponent_npc,
        avatar_rect,
        "score_four"
    )

    # ==================================================
    # NPC name
    # ==================================================

    npc_name_surface = (
        fonts.score_four_npc_font.render(
            state.score_four_opponent_npc[
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

    window.game_surface.blit(
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
            state.score_four_opponent_npc[
                "skill_tier"
            ],
            state.score_four_opponent_npc[
                "skill_tier"
            ]
        )
    )

    tier_surface = (
        fonts.score_four_round_font.render(
            tier_name,
            True,
            (
                255,
                230,
                0
            )
        )
    )

    window.game_surface.blit(
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
        fonts.score_four_round_font.render(
            thinking_text,
            True,
            (
                220,
                220,
                220
            )
        )
    )

    window.game_surface.blit(
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
        window.game_surface,
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
        window.game_surface,
        (
            220,
            220,
            220
        ),
        fill_rect
    )

    pygame.draw.rect(
        window.game_surface,
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
    if score_four_game.reward_claimed:
        return
    if score_four_game.mode == "solo" and score_four_game.session_complete:
        rating_change = career_rewards.award_career_rating('score_four', {'easy': 30, 'standard': 50, 'difficult': 70, 'extreme': 90}[score_four_game.difficulty])
        if state.current_game_mode == 'career':
            record_result(state.career_rating_results, 'score_four', 1.0, rating_change)
        career_rewards.award_fans_for_rating_win(rating_change, 'Score-Four completion')
        leveling.process_achievement_event('score_four_win', mode='solo')
        leveling.award_game_xp('score_four_solo', won=True)
        night.record_career_event_result('score_four', won=True, mode='solo')
        score_four_game.reward_claimed = True
        state.career_event_has_activity = True
    elif score_four_game.mode == "competitive" and score_four_game.match_complete:
        player_won_match = score_four_game.match_winner == 'player'
        rating_change = career_rewards.rate_competitive_game('score_four', state.score_four_opponent_npc, player_won_match)
        if player_won_match:
            career_rewards.award_fans_for_rating_win(rating_change, 'Competitive Score-Four win')
            leveling.process_achievement_event('score_four_win', mode='competitive')
        leveling.award_game_xp('score_four_competitive', won=player_won_match)
        night.record_career_event_result('score_four', won=player_won_match, mode='competitive', opponent=state.score_four_opponent_npc.get('name') if isinstance(state.score_four_opponent_npc, dict) else 'NPC', opponent_tier=state.score_four_opponent_npc.get('skill_tier') if isinstance(state.score_four_opponent_npc, dict) else 'mid', rating_reward=rating_change)
        score_four_game.reward_claimed = True
        state.career_event_has_activity = True
    else:
        return
    score_four_game.last_rating_change = rating_change


def draw_score_four():
    from solitaireplus.games.cards.score_four_ui import draw_score_four_table
    settle_score_four_session_result()
    draw_score_four_table(window.game_surface, score_four_game, state.game_mouse_pos, game_namespace())

def draw_score_four_mode_select():
    from solitaireplus.games.cards.score_four_ui import draw_difficulty_select, draw_mode_select
    if score_four_game.difficulty_menu:
        draw_difficulty_select(window.game_surface, state.game_mouse_pos, game_namespace())
    else:
        draw_mode_select(window.game_surface, score_four_game, state.game_mouse_pos, game_namespace())

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
from solitaireplus.ui import buttons  # start-up code of this module runs here, as it did in main.py

state.career_jobs_rect = pygame.Rect(
    740,
    703,
    390,
    26
)

state.career_real_estate_rect = pygame.Rect(
    335,
    703,
    390,
    26
)

state.career_leaderboards_rect = pygame.Rect(
    1175,
    285,
    180,
    45
)

state.career_news_rect = pygame.Rect(
    1175,
    645,
    180,
    45
)

state.career_back_rect = pygame.Rect(
    1175,
    710,
    180,
    45
)
from solitaireplus.ui import panels  # start-up code of this module runs here, as it did in main.py


# Arcade Night uses authored image buttons instead of the generic wood/menu
# controls. Missing art falls back to the normal button renderer so a code
# update never makes the event unusable while artwork is being prepared.
ARCADE_ACTION_BUTTON_ASSET_PATHS = {
    "buy_tokens": str(paths.asset("arcade/ui/buy_tokens.png")),
    "prize_counter": str(paths.asset("arcade/ui/prize_counter.png")),
    "return": str(paths.asset("arcade/ui/return.png")),
    "end": str(paths.asset("arcade/ui/end_night.png")),
    # Shared small controls used by the individual Arcade game setup screens.
    # play_tokens.png should include the PLAY artwork/label; the changing token
    # price is drawn by code just above the button so one asset works for every game.
    "back": str(paths.asset("arcade/ui/back.png")),
    "play_tokens": str(paths.asset("arcade/ui/play_tokens.png")),
    "reroll_rivals": str(paths.asset("arcade/ui/reroll_rivals.png")),
    "quit": str(paths.asset("arcade/ui/quit.png")),
    "continue": str(paths.asset("arcade/ui/continue.png")),
    "redeem_tickets": str(paths.asset("arcade/ui/redeem_tickets.png")),
    "trophy_room": str(paths.asset("arcade/ui/trophy_room.png")),
    "back_to_prize_counter": str(paths.asset("arcade/ui/back_to_prize_counter.png")),
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


def get_cover_scaled_ui_asset(path, size):
    """Scale an authored image to fill a button without distorting its aspect ratio."""
    if not path or not size:
        return None

    target_w, target_h = int(size[0]), int(size[1])
    if target_w <= 0 or target_h <= 0:
        return None

    cache_key = ("cover", path, target_w, target_h)
    if cache_key in _event_ui_asset_cache:
        return _event_ui_asset_cache[cache_key]

    source = get_event_ui_asset(path)
    if source is None:
        _event_ui_asset_cache[cache_key] = None
        return None

    source_w, source_h = source.get_size()
    target_ratio = target_w / target_h
    source_ratio = source_w / max(1, source_h)

    if source_ratio > target_ratio:
        crop_w = max(1, int(round(source_h * target_ratio)))
        crop_x = max(0, (source_w - crop_w) // 2)
        crop_rect = pygame.Rect(crop_x, 0, crop_w, source_h)
    else:
        crop_h = max(1, int(round(source_w / target_ratio)))
        crop_y = max(0, (source_h - crop_h) // 2)
        crop_rect = pygame.Rect(0, crop_y, source_w, crop_h)

    cropped = source.subsurface(crop_rect).copy()
    image = pygame.transform.smoothscale(cropped, (target_w, target_h))
    _event_ui_asset_cache[cache_key] = image
    return image


def draw_arcade_action_image_button(
        rect,
        button_kind,
        fallback_text,
        enabled=True,
        badge_text=None,
):
    """Draw an Arcade control with authored PNG art and a safe generic fallback.

    ``badge_text`` is intended for values that change in code (currently the
    machine entry price). The authored play_tokens.png can therefore say PLAY
    while the live ``2 TOKENS`` / ``3 TOKENS`` value remains accurate without
    covering any part of the button artwork.
    """
    path = ARCADE_ACTION_BUTTON_ASSET_PATHS.get(button_kind)
    image = get_cover_scaled_ui_asset(path, rect.size)
    hovered = (
        enabled
        and state.game_mouse_pos is not None
        and rect.collidepoint(state.game_mouse_pos)
    )

    if image is None:
        buttons.draw_menu_button(
            rect,
            fallback_text,
            state.game_mouse_pos if enabled else None,
            font=fonts.difficulty_detail_font,
        )
        if not enabled:
            overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 125))
            window.game_surface.blit(overlay, rect.topleft)
        return

    button = image.copy()
    if hovered:
        button.fill((24, 24, 24, 0), special_flags=pygame.BLEND_RGBA_ADD)
    if not enabled:
        button.fill((105, 105, 105, 255), special_flags=pygame.BLEND_RGBA_MULT)
        button.set_alpha(145)

    window.game_surface.blit(button, rect.topleft)

    border_color = (247, 213, 115) if hovered else (177, 190, 205)
    pygame.draw.rect(
        window.game_surface,
        border_color,
        rect,
        3 if hovered else 2,
        border_radius=9,
    )

    if badge_text:
        # Keep the changing entry price completely outside the authored PLAY
        # art. This preserves custom transparent button designs instead of
        # covering the right side with a live-value badge.
        badge = fonts.arcade_button_badge_font.render(
            badge_text,
            True,
            (246, 239, 214),
        )
        shadow = fonts.arcade_button_badge_font.render(
            badge_text,
            True,
            (6, 9, 13),
        )
        badge_center = (rect.centerx, rect.top - 11)
        window.game_surface.blit(
            shadow,
            shadow.get_rect(center=(badge_center[0] + 1, badge_center[1] + 1)),
        )
        window.game_surface.blit(
            badge,
            badge.get_rect(center=badge_center),
        )


def draw_arcade_page_background(shade_alpha=72):
    background = get_event_ui_asset(str(paths.asset("arcade/bg.png")), (BASE_WIDTH, BASE_HEIGHT))
    if background is not None:
        window.game_surface.blit(background, (0, 0))
    else:
        window.game_surface.fill((12, 18, 28))
    shade = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
    shade.fill((0, 0, 0, max(0, min(255, int(shade_alpha)))))
    window.game_surface.blit(shade, (0, 0))


def draw_arcade_token_exchange():
    draw_arcade_page_background(62)

    panel = pygame.Rect(90, 58, 1186, 662)
    panel_surface = pygame.Surface(panel.size, pygame.SRCALPHA)
    panel_surface.fill((10, 17, 28, 235))
    window.game_surface.blit(panel_surface, panel.topleft)
    pygame.draw.rect(window.game_surface, (229, 197, 102), panel, 3, border_radius=16)

    title = fonts.options_title_font.render("ARCADE TOKEN EXCHANGE", True, (255, 255, 255))
    subtitle = fonts.difficulty_detail_font.render(
        "Trade Career cash for tokens. Tickets are earned by playing the machines.",
        True,
        (214, 220, 226),
    )
    window.game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 102)))
    window.game_surface.blit(subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 140)))

    status = (
        ("CASH", f"${state.career_cash:,}"),
        ("TOKENS", f"{int(state.arcade_state.get('tokens', 0)):,}"),
        ("TICKETS", f"{int(state.arcade_state.get('tickets', 0)):,}"),
    )
    for index, (label, value) in enumerate(status):
        rect = pygame.Rect(226 + index * 310, 166, 270, 58)
        pygame.draw.rect(window.game_surface, (7, 14, 24), rect, border_radius=10)
        pygame.draw.rect(window.game_surface, (95, 176, 205), rect, 2, border_radius=10)
        label_surface = fonts.difficulty_detail_font.render(label, True, (179, 191, 203))
        value_surface = fonts.option_label_font.render(value, True, (255, 237, 156))
        window.game_surface.blit(label_surface, label_surface.get_rect(midleft=(rect.x + 16, rect.centery)))
        window.game_surface.blit(value_surface, value_surface.get_rect(midright=(rect.right - 16, rect.centery)))

    for index, package in enumerate(ARCADE_TOKEN_PACKAGES):
        rect = arcade_token_package_rects[index]
        hovered = state.game_mouse_pos is not None and rect.collidepoint(state.game_mouse_pos)
        fill = (28, 38, 52) if not hovered else (37, 52, 68)
        pygame.draw.rect(window.game_surface, fill, rect, border_radius=14)
        pygame.draw.rect(
            window.game_surface,
            (230, 199, 108) if hovered else (119, 132, 148),
            rect,
            3 if hovered else 2,
            border_radius=14,
        )

        name = fonts.option_label_font.render(package["name"], True, (247, 248, 249))
        token_count = fonts.options_title_font.render(str(package["tokens"]), True, (255, 236, 142))
        token_label = fonts.difficulty_detail_font.render("TOKENS", True, (255, 240, 180))
        cash_label = fonts.difficulty_detail_font.render(
            f"${package['cash_cost']} CASH",
            True,
            (202, 210, 220),
        )

        window.game_surface.blit(name, name.get_rect(center=(rect.centerx, rect.y + 25)))
        window.game_surface.blit(token_count, token_count.get_rect(center=(rect.centerx, rect.y + 65)))
        window.game_surface.blit(token_label, token_label.get_rect(center=(rect.centerx, rect.y + 94)))
        window.game_surface.blit(cash_label, cash_label.get_rect(center=(rect.centerx, rect.bottom - 18)))

    if state.arcade_status_message and pygame.time.get_ticks() <= state.arcade_status_message_expires:
        info = fonts.difficulty_detail_font.render(state.arcade_status_message, True, (248, 242, 216))
        info_rect = info.get_rect(center=(BASE_WIDTH // 2, 619)).inflate(26, 12)
        info_panel = pygame.Surface(info_rect.size, pygame.SRCALPHA)
        info_panel.fill((5, 11, 20, 225))
        window.game_surface.blit(info_panel, info_rect.topleft)
        pygame.draw.rect(window.game_surface, (226, 194, 104), info_rect, 2, border_radius=8)
        window.game_surface.blit(info, info.get_rect(center=info_rect.center))

    draw_arcade_action_image_button(
        arcade_token_exchange_back_rect,
        "back",
        "Back",
    )
    if (
            state.arcade_pending_launch_game_id == "king_pong"
            and int(state.arcade_state.get("tokens", 0)) >= get_machine_cost("king_pong")
    ):
        continue_label = "Play King Pong"
    elif (
            state.arcade_pending_launch_game_id == "battle_bosses"
            and int(state.arcade_state.get("tokens", 0)) >= get_machine_cost("battle_bosses")
    ):
        continue_label = "Play Battle Bosses"
    else:
        continue_label = "Continue"
    draw_arcade_action_image_button(
        arcade_token_exchange_continue_rect,
        "continue",
        continue_label,
        enabled=True,
    )


def redeem_arcade_prize_for_career(prize_id):
    """Redeem one ticket prize and atomically unlock any attached cosmetic."""
    previous_state = clone_arcade_state(state.arcade_state)
    previous_backgrounds = set(state.unlocked_menu_backgrounds)
    previous_felts = set(state.unlocked_felts)
    previous_titles = set(state.unlocked_titles)
    previous_cursors = set(cursors.unlocked_cursors)

    success, new_state, message, prize = redeem_prize(state.arcade_state, prize_id)
    if not success:
        return False, message, prize

    state.arcade_state = new_state
    if prize and prize.get("kind") == "cosmetic":
        from solitaireplus.profile.cosmetics import unlock_reward
        unlock_reward(
            prize.get("cosmetic_type"),
            prize.get("asset_id"),
            state.unlocked_menu_backgrounds,
            state.unlocked_felts,
            state.unlocked_titles,
            cursors.unlocked_cursors,
        )

    try:
        career_saving.auto_save_career()
    except Exception:
        state.arcade_state = previous_state
        state.unlocked_menu_backgrounds.clear(); state.unlocked_menu_backgrounds.update(previous_backgrounds)
        state.unlocked_felts.clear(); state.unlocked_felts.update(previous_felts)
        state.unlocked_titles.clear(); state.unlocked_titles.update(previous_titles)
        cursors.unlocked_cursors.clear(); cursors.unlocked_cursors.update(previous_cursors)
        raise
    return True, message, prize


def _draw_arcade_prize_page_button(rect, label, enabled):
    hovered = enabled and state.game_mouse_pos is not None and rect.collidepoint(state.game_mouse_pos)
    fill = (34, 48, 65) if hovered else (20, 29, 41)
    border = (247, 213, 115) if hovered else (126, 141, 158)
    pygame.draw.rect(window.game_surface, fill, rect, border_radius=8)
    pygame.draw.rect(window.game_surface, border, rect, 2, border_radius=8)
    color = (247, 241, 217) if enabled else (100, 111, 124)
    text = fonts.difficulty_detail_font.render(label, True, color)
    window.game_surface.blit(text, text.get_rect(center=rect.center))


def _draw_arcade_prize_art(prize, art_rect):
    art = get_event_ui_asset(prize.get("image"))
    if art is not None:
        scale = min(art_rect.width / art.get_width(), art_rect.height / art.get_height())
        size = (
            max(1, int(round(art.get_width() * scale))),
            max(1, int(round(art.get_height() * scale))),
        )
        art = pygame.transform.smoothscale(art, size)
        window.game_surface.blit(art, art.get_rect(center=art_rect.center))
        return

    # Safe placeholder while the authored prize PNG is being created.
    kind = prize.get("cosmetic_type") or prize.get("kind", "prize")
    pygame.draw.rect(window.game_surface, (12, 18, 27), art_rect, border_radius=10)
    pygame.draw.rect(window.game_surface, (91, 109, 132), art_rect, 2, border_radius=10)
    label = fonts.difficulty_detail_font.render(str(kind).replace("_", " ").upper(), True, (184, 196, 210))
    window.game_surface.blit(label, label.get_rect(center=art_rect.center))


def draw_arcade_prize_counter():
    draw_arcade_page_background(70)
    panel = pygame.Rect(70, 70, 1226, 620)
    pygame.draw.rect(window.game_surface, (16, 23, 34), panel, border_radius=18)
    pygame.draw.rect(window.game_surface, (226, 194, 104), panel, 3, border_radius=18)
    title = fonts.options_title_font.render("PRIZE COUNTER", True, (255, 255, 255))
    subtitle = fonts.difficulty_detail_font.render(
        "Redeem tickets for trophies and exclusive arcade cosmetics.",
        True,
        (210, 217, 224),
    )
    window.game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 112)))
    window.game_surface.blit(subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 145)))

    ticket_surface = fonts.option_label_font.render(
        f"Tickets: {int(state.arcade_state.get('tickets', 0)):,}",
        True,
        (255, 238, 154),
    )
    window.game_surface.blit(ticket_surface, ticket_surface.get_rect(center=(BASE_WIDTH // 2, 176)))

    page_count = max(1, math.ceil(len(ARCADE_PRIZE_CATALOG) / ARCADE_PRIZES_PER_PAGE))
    page = max(0, min(page_count - 1, int(state.arcade_prize_page)))
    page_start = page * ARCADE_PRIZES_PER_PAGE

    for slot, rect in arcade_prize_card_rects.items():
        index = page_start + slot
        if index >= len(ARCADE_PRIZE_CATALOG):
            continue
        prize = ARCADE_PRIZE_CATALOG[index]
        hovered = state.game_mouse_pos is not None and rect.collidepoint(state.game_mouse_pos)
        selected = index == state.arcade_selected_prize_index
        owned = prize['id'] in state.arcade_state.get('trophies', [])
        pygame.draw.rect(
            window.game_surface,
            (25, 34, 48) if not hovered and not selected else (34, 46, 64),
            rect,
            border_radius=14,
        )
        pygame.draw.rect(
            window.game_surface,
            (220, 191, 103) if hovered or selected else (109, 121, 138),
            rect,
            2,
            border_radius=14,
        )

        name_rect = pygame.Rect(rect.x + 12, rect.y + 12, rect.width - 24, 50)
        ui_text.draw_wrapped_text_limited(
            prize['name'], fonts.option_label_font, (248, 249, 250), name_rect, 2, line_spacing=2
        )
        _draw_arcade_prize_art(prize, pygame.Rect(rect.x + 72, rect.y + 66, 126, 86))

        cost = fonts.options_title_font.render(f"{prize['cost']}", True, (255, 236, 142))
        window.game_surface.blit(cost, cost.get_rect(center=(rect.centerx, rect.y + 178)))
        tickets_word = fonts.difficulty_detail_font.render("TICKETS", True, (255, 240, 180))
        window.game_surface.blit(tickets_word, tickets_word.get_rect(center=(rect.centerx, rect.y + 207)))
        ui_text.draw_wrapped_text_limited(
            prize['description'],
            fonts.difficulty_detail_font,
            (208, 216, 224),
            pygame.Rect(rect.x + 14, rect.y + 226, rect.width - 28, 46),
            2,
            line_spacing=3,
        )
        footer = "OWNED" if owned else prize.get("cosmetic_type", "Select").replace("_", " ").upper()
        footer_color = (135, 222, 173) if owned else (173, 182, 194)
        footer_surface = fonts.difficulty_detail_font.render(footer, True, footer_color)
        window.game_surface.blit(footer_surface, footer_surface.get_rect(center=(rect.centerx, rect.bottom - 16)))

    _draw_arcade_prize_page_button(arcade_prize_prev_rect, "PREV", page > 0)
    _draw_arcade_prize_page_button(arcade_prize_next_rect, "NEXT", page + 1 < page_count)
    page_text = fonts.difficulty_detail_font.render(f"PAGE {page + 1} / {page_count}", True, (178, 190, 204))
    window.game_surface.blit(page_text, page_text.get_rect(center=(BASE_WIDTH // 2, 544)))

    draw_arcade_action_image_button(arcade_prize_back_rect, "back", "Back")
    draw_arcade_action_image_button(arcade_prize_trophy_room_rect, "trophy_room", "Trophy Room")

    selected_index = max(0, min(len(ARCADE_PRIZE_CATALOG) - 1, state.arcade_selected_prize_index))
    selected_prize = ARCADE_PRIZE_CATALOG[selected_index]
    owned = selected_prize['id'] in state.arcade_state.get('trophies', [])
    draw_arcade_action_image_button(
        arcade_prize_buy_rect,
        "redeem_tickets",
        "Redeem Tickets",
        enabled=not owned,
        badge_text=f"{selected_prize['cost']} TICKETS" if not owned else "OWNED",
    )

    if state.arcade_status_message and pygame.time.get_ticks() <= state.arcade_status_message_expires:
        info = fonts.difficulty_detail_font.render(state.arcade_status_message, True, (246, 241, 217))
        bg = info.get_rect(center=(BASE_WIDTH // 2, 610)).inflate(28, 16)
        overlay = pygame.Surface(bg.size, pygame.SRCALPHA)
        overlay.fill((8, 14, 24, 225))
        window.game_surface.blit(overlay, bg.topleft)
        pygame.draw.rect(window.game_surface, (228, 197, 107), bg, 2, border_radius=9)
        window.game_surface.blit(info, info.get_rect(center=bg.center))

def draw_arcade_trophy_room():
    draw_arcade_page_background(66)
    panel = pygame.Rect(104, 92, 1158, 576)
    pygame.draw.rect(window.game_surface, (15, 21, 31), panel, border_radius=18)
    pygame.draw.rect(window.game_surface, (225, 193, 103), panel, 3, border_radius=18)
    title = fonts.options_title_font.render("ARCADE TROPHY ROOM", True, (255, 255, 255))
    subtitle = fonts.difficulty_detail_font.render(
        "Ticket trophies live here. Redeemed cosmetics are available under Customize.",
        True,
        (210, 217, 224),
    )
    window.game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 132)))
    window.game_surface.blit(subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 166)))

    trophies = [
        prize for prize in ARCADE_PRIZE_CATALOG
        if prize.get('kind') == 'trophy' and prize['id'] in state.arcade_state.get('trophies', [])
    ]
    if not trophies:
        empty = fonts.option_label_font.render("No trophies redeemed yet.", True, (232, 236, 240))
        hint = fonts.difficulty_detail_font.render("Visit the Prize Counter after stacking up some tickets.", True, (165, 175, 188))
        window.game_surface.blit(empty, empty.get_rect(center=(BASE_WIDTH // 2, 350)))
        window.game_surface.blit(hint, hint.get_rect(center=(BASE_WIDTH // 2, 388)))
    else:
        for index, prize in enumerate(trophies):
            rect = pygame.Rect(164 + (index % 3) * 330, 232 + (index // 3) * 180, 270, 132)
            pygame.draw.rect(window.game_surface, (29, 38, 52), rect, border_radius=14)
            pygame.draw.rect(window.game_surface, (222, 191, 102), rect, 2, border_radius=14)
            _draw_arcade_prize_art(prize, pygame.Rect(rect.x + 18, rect.y + 20, 66, 66))
            name = fonts.option_label_font.render(prize['name'], True, (248, 249, 250))
            cost = fonts.difficulty_detail_font.render(f"Redeemed for {prize['cost']} tickets", True, (189, 198, 208))
            window.game_surface.blit(name, name.get_rect(midleft=(rect.x + 96, rect.y + 42)))
            ui_text.draw_wrapped_text_limited(
                prize['description'], fonts.difficulty_detail_font, (210, 217, 224),
                pygame.Rect(rect.x + 96, rect.y + 56, rect.width - 114, 46), 2, line_spacing=4
            )
            window.game_surface.blit(cost, cost.get_rect(midleft=(rect.x + 96, rect.bottom - 22)))

    draw_arcade_action_image_button(
        arcade_trophy_room_back_rect,
        "back_to_prize_counter",
        "Back to Prize Counter",
    )

def draw_king_pong_opponent_select():
    draw_arcade_page_background(62)

    panel = pygame.Rect(72, 44, 1222, 688)
    panel_surface = pygame.Surface(panel.size, pygame.SRCALPHA)
    panel_surface.fill((8, 15, 25, 238))
    window.game_surface.blit(panel_surface, panel.topleft)
    pygame.draw.rect(window.game_surface, (229, 197, 102), panel, 3, border_radius=16)

    logo = get_event_ui_asset(
        str(paths.asset("arcade/king_pong/logo.png")),
        (330, 94),
    )
    if logo is not None:
        window.game_surface.blit(logo, logo.get_rect(center=(BASE_WIDTH // 2, 100)))
    else:
        title = fonts.options_title_font.render("KING PONG", True, (250, 249, 244))
        window.game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 92)))

    subtitle = fonts.difficulty_detail_font.render(
        "Choose a rival. Harder opponents move faster and pay more tickets.",
        True,
        (213, 220, 228),
    )
    window.game_surface.blit(subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 154)))

    wallet = fonts.difficulty_detail_font.render(
        f"TOKENS: {int(state.arcade_state.get('tokens', 0)):,}    |    "
        f"TICKETS: {int(state.arcade_state.get('tickets', 0)):,}",
        True,
        (255, 235, 145),
    )
    window.game_surface.blit(wallet, wallet.get_rect(center=(BASE_WIDTH // 2, 181)))

    difficulty_descriptions = {
        "low": "Slow reactions / wide tracking error",
        "medium": "Balanced arcade opponent",
        "high": "Fast reactions / accurate tracking",
        "expert": "Very fast / very small tracking error",
    }

    for index, choice in enumerate(state.king_pong_opponent_choices[:4]):
        rect = king_pong_opponent_rects[index]
        difficulty_id = choice.get("difficulty_id", "medium")
        config = KING_PONG_DIFFICULTIES.get(
            difficulty_id,
            KING_PONG_DIFFICULTIES["medium"],
        )
        npc = choice.get("npc") or {}
        selected = index == state.king_pong_selected_opponent_index
        hovered = state.game_mouse_pos is not None and rect.collidepoint(state.game_mouse_pos)

        fill = (34, 48, 64) if selected or hovered else (22, 31, 44)
        border = (255, 217, 108) if selected else ((102, 196, 225) if hovered else (111, 126, 145))
        pygame.draw.rect(window.game_surface, fill, rect, border_radius=14)
        pygame.draw.rect(window.game_surface, border, rect, 4 if selected else 2, border_radius=14)

        difficulty_surface = fonts.option_label_font.render(
            config.get("label", difficulty_id.upper()),
            True,
            (255, 234, 141),
        )
        window.game_surface.blit(
            difficulty_surface,
            difficulty_surface.get_rect(center=(rect.centerx, rect.y + 32)),
        )

        portrait_rect = pygame.Rect(rect.centerx - 55, rect.y + 62, 110, 110)
        pygame.draw.ellipse(window.game_surface, (14, 23, 34), portrait_rect)
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
            window.game_surface.blit(clipped, portrait_rect.topleft)
        pygame.draw.ellipse(window.game_surface, (229, 197, 102), portrait_rect, 3)

        npc_name = str(npc.get("name") or "Arcade Rival")
        name_surface = fonts.option_label_font.render(npc_name, True, (242, 245, 248))
        if name_surface.get_width() > rect.width - 24:
            name_surface = fonts.difficulty_detail_font.render(npc_name, True, (242, 245, 248))
        window.game_surface.blit(
            name_surface,
            name_surface.get_rect(center=(rect.centerx, rect.y + 198)),
        )

        multiplier = float(config.get("ticket_multiplier", 1.0))
        reward_surface = fonts.option_label_font.render(
            f"x{multiplier:.2f} TICKETS",
            True,
            (132, 222, 169) if multiplier >= 1.0 else (214, 201, 150),
        )
        window.game_surface.blit(
            reward_surface,
            reward_surface.get_rect(center=(rect.centerx, rect.y + 238)),
        )

        description_rect = pygame.Rect(
            rect.x + 16,
            rect.y + 258,
            rect.width - 32,
            50,
        )
        ui_text.draw_wrapped_text_limited(
            difficulty_descriptions.get(difficulty_id, "Arcade opponent"),
            fonts.difficulty_detail_font,
            (185, 195, 207),
            description_rect,
            2,
            line_spacing=1,
        )

        select_note = fonts.difficulty_detail_font.render(
            "SELECTED" if selected else "Click to select",
            True,
            (255, 231, 143) if selected else (148, 161, 176),
        )
        window.game_surface.blit(
            select_note,
            select_note.get_rect(center=(rect.centerx, rect.bottom - 30)),
        )

    draw_arcade_action_image_button(
        king_pong_opponent_back_rect,
        "back",
        "Back",
    )
    draw_arcade_action_image_button(
        king_pong_opponent_tokens_rect,
        "buy_tokens",
        "Buy Tokens",
    )

    token_cost = get_machine_cost("king_pong")
    can_play = (
        get_selected_king_pong_choice() is not None
        and int(state.arcade_state.get("tokens", 0)) >= token_cost
    )
    draw_arcade_action_image_button(
        king_pong_opponent_play_rect,
        "play_tokens",
        f"Play - {token_cost} Tokens",
        enabled=can_play,
        badge_text=f"{token_cost} TOKENS",
    )

    if state.arcade_status_message and pygame.time.get_ticks() <= state.arcade_status_message_expires:
        info = fonts.difficulty_detail_font.render(
            state.arcade_status_message,
            True,
            (248, 242, 216),
        )
        window.game_surface.blit(info, info.get_rect(center=(BASE_WIDTH // 2, 620)))


def draw_battle_bosses_opponent_select():
    draw_arcade_page_background(62)

    panel = pygame.Rect(72, 42, 1222, 690)
    panel_surface = pygame.Surface(panel.size, pygame.SRCALPHA)
    panel_surface.fill((8, 15, 25, 238))
    window.game_surface.blit(panel_surface, panel.topleft)
    pygame.draw.rect(window.game_surface, (229, 197, 102), panel, 3, border_radius=16)

    logo = get_event_ui_asset(
        str(paths.asset("arcade/battle_bosses/logo.png")),
        (390, 92),
    )
    if logo is not None:
        window.game_surface.blit(logo, logo.get_rect(center=(BASE_WIDTH // 2, 92)))
    else:
        title = fonts.options_title_font.render("BATTLE BOSSES", True, (250, 249, 244))
        window.game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 86)))

    subtitle = fonts.difficulty_detail_font.render(
        "Choose a three-rival squad. Harder squads move faster and pay more tickets.",
        True,
        (213, 220, 228),
    )
    window.game_surface.blit(subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 139)))

    wallet = fonts.difficulty_detail_font.render(
        f"TOKENS: {int(state.arcade_state.get('tokens', 0)):,}    |    "
        f"TICKETS: {int(state.arcade_state.get('tickets', 0)):,}    |    "
        f"ENTRY: {get_machine_cost('battle_bosses')} TOKENS",
        True,
        (255, 235, 145),
    )
    window.game_surface.blit(wallet, wallet.get_rect(center=(BASE_WIDTH // 2, 170)))

    battle_name_font = ui_text.get_font(None, 19)

    for index, choice in enumerate(state.battle_bosses_opponent_choices[:4]):
        rect = battle_bosses_choice_rects[index]
        difficulty_id = choice.get("difficulty_id", "standard")
        config = choice.get("config") or BATTLE_BOSSES_DIFFICULTIES.get(
            difficulty_id,
            BATTLE_BOSSES_DIFFICULTIES["standard"],
        )
        selected = index == state.battle_bosses_selected_choice_index
        hovered = state.game_mouse_pos is not None and rect.collidepoint(state.game_mouse_pos)

        fill = (34, 48, 64) if selected or hovered else (22, 31, 44)
        border = (255, 217, 108) if selected else ((102, 196, 225) if hovered else (111, 126, 145))
        pygame.draw.rect(window.game_surface, fill, rect, border_radius=14)
        pygame.draw.rect(window.game_surface, border, rect, 4 if selected else 2, border_radius=14)

        difficulty_surface = fonts.option_label_font.render(
            config.get("label", difficulty_id.upper()),
            True,
            (255, 234, 141),
        )
        window.game_surface.blit(
            difficulty_surface,
            difficulty_surface.get_rect(midleft=(rect.x + 18, rect.y + 27)),
        )

        multiplier = float(config.get("ticket_multiplier", 1.0))
        reward_surface = fonts.difficulty_detail_font.render(
            f"x{multiplier:.2f} tickets",
            True,
            (132, 222, 169) if multiplier >= 1.0 else (214, 201, 150),
        )
        window.game_surface.blit(
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
            pygame.draw.ellipse(window.game_surface, (14, 23, 34), portrait_rect)
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
                window.game_surface.blit(clipped, portrait_rect.topleft)
            pygame.draw.ellipse(window.game_surface, (229, 197, 102), portrait_rect, 2)

            npc_name = str(npc.get("name") or f"Rival {npc_index + 1}")
            name_surface = battle_name_font.render(npc_name, True, (232, 236, 240))
            max_name_width = 92
            if name_surface.get_width() > max_name_width:
                scale = max_name_width / max(1, name_surface.get_width())
                name_surface = pygame.transform.smoothscale(
                    name_surface,
                    (max_name_width, max(1, int(name_surface.get_height() * scale))),
                )
            window.game_surface.blit(
                name_surface,
                name_surface.get_rect(center=(portrait_rect.centerx, portrait_rect.bottom + 15)),
            )

        description = fonts.difficulty_detail_font.render(
            config.get("description", "Three-rival arcade squad."),
            True,
            (185, 195, 207),
        )
        window.game_surface.blit(
            description,
            description.get_rect(center=(rect.centerx, rect.bottom - 20)),
        )

    draw_arcade_action_image_button(
        battle_bosses_back_rect,
        "back",
        "Back",
    )
    draw_arcade_action_image_button(
        battle_bosses_refresh_rect,
        "reroll_rivals",
        "Reroll Rivals",
    )
    battle_cost = get_machine_cost("battle_bosses")
    can_play = get_selected_battle_bosses_choice() is not None
    draw_arcade_action_image_button(
        battle_bosses_future_play_rect,
        "play_tokens",
        f"Play - {battle_cost} Tokens",
        enabled=can_play,
        badge_text=f"{battle_cost} TOKENS",
    )

    if state.arcade_status_message and pygame.time.get_ticks() <= state.arcade_status_message_expires:
        info = fonts.difficulty_detail_font.render(state.arcade_status_message, True, (248, 242, 216))
        window.game_surface.blit(info, info.get_rect(center=(BASE_WIDTH // 2, 625)))


def draw_ace_invaders_difficulty_select():
    draw_arcade_page_background(62)

    panel = pygame.Rect(72, 44, 1222, 688)
    panel_surface = pygame.Surface(panel.size, pygame.SRCALPHA)
    panel_surface.fill((8, 15, 25, 238))
    window.game_surface.blit(panel_surface, panel.topleft)
    pygame.draw.rect(window.game_surface, (229, 197, 102), panel, 3, border_radius=16)

    logo = get_event_ui_asset(
        str(paths.asset("arcade/ace_invaders/logo.png")),
        (360, 96),
    )
    if logo is not None:
        window.game_surface.blit(logo, logo.get_rect(center=(BASE_WIDTH // 2, 96)))
    else:
        title = fonts.options_title_font.render("ACE INVADERS", True, (250, 249, 244))
        window.game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 90)))

    subtitle = fonts.difficulty_detail_font.render(
        "Choose a difficulty. Survive consecutive waves to earn tickets.",
        True,
        (213, 220, 228),
    )
    window.game_surface.blit(subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 157)))

    wallet = fonts.difficulty_detail_font.render(
        f"TOKENS {int(state.arcade_state.get('tokens', 0)):,}    |    "
        f"TICKETS {int(state.arcade_state.get('tickets', 0)):,}    |    "
        f"ENTRY {get_machine_cost('ace_invaders')}    |    "
        f"HIGH {int(state.arcade_state.get('stats', {}).get('ace_invaders_high_score', 0) or 0):,}",
        True,
        (255, 235, 145),
    )
    window.game_surface.blit(wallet, wallet.get_rect(center=(BASE_WIDTH // 2, 185)))

    difficulty_ids = list(ACE_INVADERS_DIFFICULTIES)
    for index, difficulty_id in enumerate(difficulty_ids[:4]):
        rect = ace_invaders_difficulty_rects[index]
        config = ACE_INVADERS_DIFFICULTIES[difficulty_id]
        selected = index == state.ace_invaders_selected_difficulty_index
        hovered = state.game_mouse_pos is not None and rect.collidepoint(state.game_mouse_pos)

        fill = (34, 48, 64) if selected or hovered else (22, 31, 44)
        border = (
            (255, 217, 108)
            if selected
            else ((102, 196, 225) if hovered else (111, 126, 145))
        )
        pygame.draw.rect(window.game_surface, fill, rect, border_radius=14)
        pygame.draw.rect(
            window.game_surface,
            border,
            rect,
            4 if selected else 2,
            border_radius=14,
        )

        label = fonts.option_label_font.render(
            config.get("label", difficulty_id.upper()),
            True,
            (255, 234, 141),
        )
        window.game_surface.blit(label, label.get_rect(center=(rect.centerx, rect.y + 35)))

        multiplier = float(config.get("ticket_multiplier", 1.0))
        reward = fonts.option_label_font.render(
            f"x{multiplier:.2f} TICKETS",
            True,
            (132, 222, 169) if multiplier >= 1.0 else (214, 201, 150),
        )
        window.game_surface.blit(reward, reward.get_rect(center=(rect.centerx, rect.y + 78)))

        rows = int(config.get("rows", 3))
        columns = int(config.get("columns", 8))
        enemy_count = rows * columns
        stat_lines = (
            f"Starts at {enemy_count} Aces",
            f"Formation speed: {int(config.get('formation_speed', 68))}",
            f"Enemy fire: {int(config.get('enemy_fire_ms', 1125))} ms",
            f"Shot speed: {int(config.get('enemy_bullet_speed', 220))}",
        )
        for line_index, line in enumerate(stat_lines):
            rendered = fonts.difficulty_detail_font.render(
                line,
                True,
                (219, 224, 230),
            )
            window.game_surface.blit(
                rendered,
                rendered.get_rect(center=(rect.centerx, rect.y + 126 + line_index * 30)),
            )

        description_rect = pygame.Rect(
            rect.x + 18,
            rect.y + 235,
            rect.width - 36,
            48,
        )
        ui_text.draw_wrapped_text_limited(
            config.get("description", "Arcade shooter difficulty."),
            fonts.difficulty_detail_font,
            (178, 190, 204),
            description_rect,
            2,
            line_spacing=3,
        )

        select_note = fonts.difficulty_detail_font.render(
            "SELECTED" if selected else "Click to select",
            True,
            (255, 231, 143) if selected else (148, 161, 176),
        )
        window.game_surface.blit(
            select_note,
            select_note.get_rect(center=(rect.centerx, rect.bottom - 24)),
        )

    draw_arcade_action_image_button(
        ace_invaders_back_rect,
        "back",
        "Back",
    )
    draw_arcade_action_image_button(
        ace_invaders_tokens_rect,
        "buy_tokens",
        "Buy Tokens",
    )

    token_cost = get_machine_cost("ace_invaders")
    can_play = (
        get_selected_ace_invaders_difficulty() is not None
        and int(state.arcade_state.get("tokens", 0)) >= token_cost
    )
    draw_arcade_action_image_button(
        ace_invaders_play_rect,
        "play_tokens",
        f"Play - {token_cost} Tokens",
        enabled=can_play,
        badge_text=f"{token_cost} TOKENS",
    )

    if state.arcade_status_message and pygame.time.get_ticks() <= state.arcade_status_message_expires:
        info = fonts.difficulty_detail_font.render(
            state.arcade_status_message,
            True,
            (248, 242, 216),
        )
        window.game_surface.blit(info, info.get_rect(center=(BASE_WIDTH // 2, 620)))


def draw_ace_invaders_screen():
    ace_invaders_game.draw(
        window.game_surface,
        {
            "title": fonts.options_title_font,
            "label": fonts.option_label_font,
            "detail": fonts.difficulty_detail_font,
            "small": fonts.ui_small_font,
        },
    )
    draw_arcade_action_image_button(
        ace_invaders_quit_rect,
        "quit",
        "Quit",
    )


def draw_king_pong_screen():
    king_pong_game.draw(
        window.game_surface,
        {
            'title': fonts.options_title_font,
            'label': fonts.option_label_font,
            'detail': fonts.difficulty_detail_font,
            'small': fonts.ui_small_font,
        },
        portrait_loader=get_npc_portrait_surface,
    )
    draw_arcade_action_image_button(
        king_pong_return_rect,
        "quit",
        "Quit",
    )


def draw_battle_bosses_screen():
    try:
        player_portrait = get_profile_avatar()
    except Exception:
        player_portrait = None

    battle_bosses_game.draw(
        window.game_surface,
        {
            'title': fonts.options_title_font,
            'label': fonts.option_label_font,
            'detail': fonts.difficulty_detail_font,
            'small': fonts.ui_small_font,
        },
        portrait_loader=get_npc_portrait_surface,
        player_portrait=player_portrait,
    )
    draw_arcade_action_image_button(
        battle_bosses_quit_rect,
        "quit",
        "Quit",
    )



def draw_suit_snake_difficulty_select():
    draw_arcade_page_background(62)

    panel = pygame.Rect(72, 44, 1222, 688)
    panel_surface = pygame.Surface(panel.size, pygame.SRCALPHA)
    panel_surface.fill((8, 15, 25, 238))
    window.game_surface.blit(panel_surface, panel.topleft)
    pygame.draw.rect(window.game_surface, (229, 197, 102), panel, 3, border_radius=16)

    logo = get_event_ui_asset(
        str(paths.asset("arcade/suit_snake/logo.png")),
        (360, 96),
    )
    if logo is not None:
        window.game_surface.blit(logo, logo.get_rect(center=(BASE_WIDTH // 2, 96)))
    else:
        title = fonts.options_title_font.render("SUIT SNAKE", True, (250, 249, 244))
        window.game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 90)))

    subtitle = fonts.difficulty_detail_font.render(
        "Choose a mode, then choose Step or Smooth Movement.",
        True,
        (213, 220, 228),
    )
    window.game_surface.blit(subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 157)))

    wallet = fonts.difficulty_detail_font.render(
        f"TOKENS {int(state.arcade_state.get('tokens', 0)):,}    |    "
        f"TICKETS {int(state.arcade_state.get('tickets', 0)):,}    |    "
        f"ENTRY {get_machine_cost('suit_snake')}    |    "
        f"HIGH {int(state.arcade_state.get('stats', {}).get('suit_snake_high_score', 0) or 0):,}",
        True,
        (255, 235, 145),
    )
    window.game_surface.blit(wallet, wallet.get_rect(center=(BASE_WIDTH // 2, 184)))

    mode_ids = list(SUIT_SNAKE_MODES)
    for index, mode_id in enumerate(mode_ids[:4]):
        rect = suit_snake_mode_rects[index]
        config = SUIT_SNAKE_MODES[mode_id]
        selected = index == state.suit_snake_selected_mode_index
        hovered = state.game_mouse_pos is not None and rect.collidepoint(state.game_mouse_pos)

        fill = (34, 48, 64) if selected or hovered else (22, 31, 44)
        border = (
            (255, 217, 108)
            if selected
            else ((102, 196, 225) if hovered else (111, 126, 145))
        )
        pygame.draw.rect(window.game_surface, fill, rect, border_radius=14)
        pygame.draw.rect(
            window.game_surface,
            border,
            rect,
            4 if selected else 2,
            border_radius=14,
        )

        label_lines = config.get("label_lines", (config.get("label", mode_id.upper()),))
        label_start_y = rect.y + 30
        for line_index, label_text in enumerate(label_lines[:2]):
            label = ui_text.render_text_fit(
                str(label_text),
                fonts.option_label_font,
                rect.width - 28,
                color=(255, 234, 141),
                minimum_size=16,
            )
            window.game_surface.blit(
                label,
                label.get_rect(center=(rect.centerx, label_start_y + line_index * 27)),
            )

        columns = int(config.get("grid_columns", 24))
        rows = int(config.get("grid_rows", 13))
        wraparound = bool(config.get("wraparound", False))
        stat_lines = (
            f"Grid: {columns} x {rows}",
            "Borders: WRAPAROUND" if wraparound else "Borders: DEADLY",
            "Self collision: Game Over",
        )
        for line_index, line in enumerate(stat_lines):
            rendered = fonts.difficulty_detail_font.render(
                line,
                True,
                (132, 222, 169) if wraparound and line_index == 1 else (219, 224, 230),
            )
            window.game_surface.blit(
                rendered,
                rendered.get_rect(center=(rect.centerx, rect.y + 105 + line_index * 30)),
            )

        description_rect = pygame.Rect(
            rect.x + 18,
            rect.y + 198,
            rect.width - 36,
            54,
        )
        ui_text.draw_wrapped_text_limited(
            config.get("description", "Suit Snake cabinet mode."),
            fonts.difficulty_detail_font,
            (178, 190, 204),
            description_rect,
            2,
            line_spacing=3,
        )

        select_note = fonts.difficulty_detail_font.render(
            "SELECTED" if selected else "Click to select",
            True,
            (255, 231, 143) if selected else (148, 161, 176),
        )
        window.game_surface.blit(
            select_note,
            select_note.get_rect(center=(rect.centerx, rect.bottom - 22)),
        )

    movement_label = fonts.difficulty_detail_font.render(
        "MOVEMENT STYLE",
        True,
        (213, 220, 228),
    )
    window.game_surface.blit(
        movement_label,
        movement_label.get_rect(center=(BASE_WIDTH // 2, 530)),
    )

    movement_options = (
        ("step", suit_snake_step_movement_rect),
        ("smooth", suit_snake_smooth_movement_rect),
    )
    for movement_id, rect in movement_options:
        selected = state.suit_snake_selected_movement_style == movement_id
        hovered = state.game_mouse_pos is not None and rect.collidepoint(state.game_mouse_pos)
        fill = (34, 48, 64) if selected or hovered else (20, 29, 41)
        border = (
            (255, 217, 108)
            if selected
            else ((102, 196, 225) if hovered else (111, 126, 145))
        )
        pygame.draw.rect(window.game_surface, fill, rect, border_radius=10)
        pygame.draw.rect(
            window.game_surface,
            border,
            rect,
            3 if selected else 2,
            border_radius=10,
        )
        movement_text = SUIT_SNAKE_MOVEMENT_STYLES[movement_id]["label"]
        rendered = ui_text.render_text_fit(
            movement_text,
            fonts.difficulty_detail_font,
            rect.width - 24,
            color=(255, 234, 141) if selected else (218, 225, 232),
            minimum_size=14,
        )
        window.game_surface.blit(rendered, rendered.get_rect(center=rect.center))

    movement_description = SUIT_SNAKE_MOVEMENT_STYLES[
        state.suit_snake_selected_movement_style
    ]["description"]
    description = fonts.ui_small_font.render(
        movement_description,
        True,
        (168, 181, 194),
    )
    window.game_surface.blit(
        description,
        description.get_rect(center=(BASE_WIDTH // 2, 614)),
    )

    draw_arcade_action_image_button(
        suit_snake_back_rect,
        "back",
        "Back",
    )
    draw_arcade_action_image_button(
        suit_snake_tokens_rect,
        "buy_tokens",
        "Buy Tokens",
    )

    token_cost = get_machine_cost("suit_snake")
    can_play = (
        get_selected_suit_snake_mode() is not None
        and int(state.arcade_state.get("tokens", 0)) >= token_cost
    )
    draw_arcade_action_image_button(
        suit_snake_play_rect,
        "play_tokens",
        f"Play - {token_cost} Token",
        enabled=can_play,
        badge_text=f"{token_cost} TOKEN" if token_cost == 1 else f"{token_cost} TOKENS",
    )

    if state.arcade_status_message and pygame.time.get_ticks() <= state.arcade_status_message_expires:
        info = fonts.ui_small_font.render(
            state.arcade_status_message,
            True,
            (248, 242, 216),
        )
        window.game_surface.blit(info, info.get_rect(center=(BASE_WIDTH // 2, 638)))

def draw_suit_snake_screen():
    suit_snake_game.draw(
        window.game_surface,
        {
            "title": fonts.options_title_font,
            "label": fonts.option_label_font,
            "detail": fonts.difficulty_detail_font,
            "small": fonts.ui_small_font,
        },
    )
    draw_arcade_action_image_button(
        suit_snake_quit_rect,
        "quit",
        "Quit",
    )


def game_namespace():
    """What globals() used to be in main.py: shared state first, then everything else.

    Writes go to solitaireplus.app.state. Temporary, like this module.
    """
    import sys
    from solitaireplus.app import sounds
    from solitaireplus.app import window
    from solitaireplus.app import assets
    from solitaireplus.app import fonts
    from solitaireplus.ui import cursors
    from solitaireplus.ui import buttons
    from solitaireplus.ui import text as ui_text
    from solitaireplus.ui import panels
    from solitaireplus.ui import backgrounds
    modules = [state, state_names, sounds, window, assets, fonts, cursors, buttons, ui_text, panels, backgrounds, sys.modules[__name__]]
    return _collections.ChainMap(*(vars(module) for module in modules))


def loop_event_debug_poker_npc_select(event):
    """Old main-loop event branch for STATE_DEBUG_POKER_NPC_SELECT."""
    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):
        selector_action = get_debug_poker_select_action(
            state.game_mouse_pos,
            can_start=(state.career_cash >= 100),
        )

        if selector_action is not None:
            action_name, action_value = selector_action

            if action_name == DEBUG_POKER_ACTION_BACK:
                sounds.audio.play_sound("button_click")
                # No table was played: leave the "debug" mode open_debug_poker_npc_select
                # switched on, so Close does not take it onto a real screen (B22). An earlier
                # debug session's mode stays.
                if state.debug_poker_select_entered_debug_mode:
                    end_debug_game_mode()
                state.debug_poker_select_entered_debug_mode = False
                restore_night_context(state.debug_poker_select_saved_night)
                state.debug_poker_select_saved_night = None
                state.current_state = state_names.STATE_DEBUG_MENU

            elif action_name == DEBUG_POKER_ACTION_RANDOMIZE:
                sounds.audio.play_sound("button_click")
                state.debug_poker_selected_ids = make_debug_poker_default_selection(
                    NPCS,
                    count=4,
                )

            elif action_name == DEBUG_POKER_ACTION_CYCLE:
                sounds.audio.play_sound("button_click")
                slot_index, state.direction = action_value
                state.debug_poker_selected_ids = cycle_debug_poker_selection(
                    NPCS,
                    state.debug_poker_selected_ids,
                    slot_index,
                    state.direction,
                )

            elif action_name == DEBUG_POKER_ACTION_START:
                sounds.audio.play_sound("button_click")
                if not start_debug_selected_poker_table():
                    show_debug_message("Add cash to play")

    return


def loop_event_debug_menu(event):
    """Old main-loop event branch for STATE_DEBUG_MENU."""

    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):

        debug_action = (
            get_debug_action(
                state.game_mouse_pos
            )
        )

        # Every button that launches a game, night or career screen ends a running Free Play
        # sandbox first, so no later Career save (hub actions, the event select's Return...)
        # writes the sandbox cash (B21). The menu's own controls and Close keep the sandbox.
        if debug_action in DEBUG_LAUNCH_ACTIONS:
            debug_end_free_play_sandbox()

        # A jump to the Career Hub also leaves the "debug" mode of a debug night the player
        # did not end, so the real hub never runs in "debug" mode (B22).
        if debug_action in DEBUG_CAREER_HUB_JUMP_ACTIONS:
            end_debug_game_mode()
            # The hub only runs Career nights: a mode left over from the main menu (None) would
            # record no results, like "debug".
            if state.current_game_mode != "career":
                state.current_game_mode = "career"

        # ==========================================
        # Expandable Minigames navigation
        # ==========================================

        if is_minigame_category_action(debug_action):
            sounds.audio.play_sound("button_click")
            toggle_minigame_category(debug_action)

        # ==========================================
        # Career / event navigation
        # ==========================================

        elif debug_action == ACTION_CAREER_HUB:
            sounds.audio.play_sound("button_click")
            state.current_state = state_names.STATE_CAREER_HUB

        elif debug_action == ACTION_CASUAL_CARDS:
            sounds.audio.play_sound("button_click")
            debug_open_casual_cards()

        elif debug_action == ACTION_POKER_NIGHT:
            sounds.audio.play_sound("button_click")
            debug_open_poker_night()

        elif debug_action == ACTION_CASINO_NIGHT:
            sounds.audio.play_sound("button_click")
            debug_open_casino_night()

        elif debug_action == ACTION_HEAD_TO_HEAD:
            sounds.audio.play_sound("button_click")
            debug_open_head_to_head()

        elif debug_action == ACTION_ADVANCE_CAREER_DAY:
            sounds.audio.play_sound("button_click")
            calendar.advance_career_day(
                completed=False
            )
            state.current_state = state_names.STATE_CAREER_HUB

        elif debug_action == ACTION_NEW_CAREER_MONTH:
            sounds.audio.play_sound("button_click")
            debug_start_next_career_month()
            state.current_state = state_names.STATE_CAREER_HUB

        elif debug_action in (ACTION_ADD_PROSPECT, ACTION_ADD_PRODIGY):
            sounds.audio.play_sound("button_click")
            debug_add_career_prospect(prodigy=debug_action == ACTION_ADD_PRODIGY)

        elif debug_action == ACTION_CAREER_YEAR:
            sounds.audio.play_sound("button_click")
            debug_advance_career_year()
            state.current_state = state_names.STATE_CAREER_HUB

        # ==========================================
        # Solitaire challenges
        # ==========================================

        elif debug_action == ACTION_CHALLENGE_DRAW_3:
            sounds.audio.play_sound("button_click")
            debug_open_solitaire_challenge(
                "draw_3"
            )

        elif debug_action == ACTION_CHALLENGE_NO_UNDO:
            sounds.audio.play_sound("button_click")
            debug_open_solitaire_challenge(
                "no_undo"
            )

        elif debug_action == ACTION_CHALLENGE_NO_HINTS:
            sounds.audio.play_sound("button_click")
            debug_open_solitaire_challenge(
                "no_hints"
            )

        elif debug_action == ACTION_CHALLENGE_ALL_OR_NOTHING:
            sounds.audio.play_sound("button_click")
            debug_open_solitaire_challenge(
                "all_or_nothing"
            )

        # ==========================================
        # Minigames
        # ==========================================

        elif debug_action == ACTION_ARCADE_NIGHT:
            sounds.audio.play_sound("button_click")
            debug_open_arcade_night()

        elif debug_action == ACTION_KING_PONG:
            sounds.audio.play_sound("button_click")
            debug_open_king_pong()

        elif debug_action == ACTION_BATTLE_BOSSES:
            sounds.audio.play_sound("button_click")
            debug_open_battle_bosses()

        elif debug_action == ACTION_ACE_INVADERS:
            sounds.audio.play_sound("button_click")
            debug_open_ace_invaders()

        elif debug_action == ACTION_SUIT_SNAKE:
            sounds.audio.play_sound("button_click")
            debug_open_suit_snake()

        elif debug_action == ACTION_DEAD_MANS_HAND:
            sounds.audio.play_sound("button_click")
            start_dead_mans_hand(return_state=state_names.STATE_DEBUG_MENU)

        elif debug_action == ACTION_SCORE_FOUR_SOLO:
            sounds.audio.play_sound("button_click")
            debug_open_score_four_solo()

        elif debug_action == ACTION_SCORE_FOUR_COMPETITIVE:
            sounds.audio.play_sound("button_click")
            debug_open_score_four_competitive()

        elif debug_action == ACTION_CRAZY_EIGHTS:
            sounds.audio.play_sound("button_click")
            debug_open_crazy_eights()

        elif debug_action == ACTION_BANGO:
            sounds.audio.play_sound("button_click")
            debug_open_bango()

        elif debug_action == ACTION_FARO:
            sounds.audio.play_sound("button_click")
            if state.career_cash < 10:
                show_debug_message("Add cash to play")
            else:
                debug_open_faro()

        elif debug_action == ACTION_FIVE_O_POKER:
            sounds.audio.play_sound("button_click")
            if not debug_open_five_o_poker():
                show_debug_message("Add cash to play")

        elif debug_action == ACTION_BLIND_MANS_BLUFF:
            sounds.audio.play_sound("button_click")
            if not debug_open_blind_mans_bluff():
                show_debug_message("Add cash to play")

        elif debug_action == ACTION_BLACKJACK:
            sounds.audio.play_sound("button_click")
            debug_open_blackjack()

        elif debug_action == ACTION_ROULETTE:
            sounds.audio.play_sound("button_click")
            debug_open_roulette()

        elif debug_action == ACTION_HORSE_RACES:
            sounds.audio.play_sound("button_click")
            if state.career_cash < 10:
                show_debug_message("Add cash to play")
            else:
                debug_open_horse_races()

        elif debug_action == ACTION_TEXAS_HOLDEM:
            sounds.audio.play_sound("button_click")
            open_debug_poker_npc_select("texas_holdem")

        elif debug_action == ACTION_FIVE_CARD_DRAW:
            sounds.audio.play_sound("button_click")
            open_debug_poker_npc_select("five_card_draw")

        elif debug_action == ACTION_SEVEN_CARD_STUD:
            sounds.audio.play_sound("button_click")
            open_debug_poker_npc_select("seven_card_stud")

        # ==========================================
        # Progression controls
        # ==========================================

        elif debug_action == ACTION_ADD_CASH:
            sounds.audio.play_sound("button_click")
            state.career_cash += 5000
            if state.debug_previous_state == state_names.STATE_FARO and not faro_game.cashed_out:
                faro_game.cash += 5000
                faro_game.starting_cash += 5000
            elif state.debug_previous_state == state_names.STATE_HORSE_RACES:
                horse_races_game.bankroll += 5000
                horse_races_game.starting_cash += 5000
            elif state.debug_previous_state == state_names.STATE_FIVE_O_POKER:
                five_o_poker_game.player_stack += 5000
                five_o_poker_game.starting_stack += 5000
                state.five_o_poker_starting_stack += 5000
            elif state.debug_previous_state == state_names.STATE_BLIND_MANS_BLUFF:
                blind_mans_bluff_game.player_stack += 5000
                blind_mans_bluff_game.starting_stack += 5000
                state.blind_mans_bluff_starting_stack += 5000
            print("Cash:", state.career_cash)

        elif debug_action == ACTION_ZERO_CASH:
            sounds.audio.play_sound("button_click")
            state.career_cash = 0
            print("Cash:", state.career_cash)

        elif debug_action == ACTION_ADD_RATING:
            sounds.audio.play_sound("button_click")
            adjust_debug_ratings(100)
            print("Rating:", state.career_rating)

        elif debug_action == ACTION_SUB_RATING:
            sounds.audio.play_sound("button_click")
            adjust_debug_ratings(-100)
            print("Rating:", state.career_rating)

        elif debug_action == ACTION_ADD_XP:
            sounds.audio.play_sound("button_click")
            leveling.add_player_xp(1000)
            print("XP:", state.player_xp, "Level:", state.player_level)

        elif debug_action == ACTION_LEVEL_3:
            sounds.audio.play_sound("button_click")
            debug_set_player_level(3)
            print("Level:", state.player_level)

        elif debug_action == ACTION_LEVEL_6:
            sounds.audio.play_sound("button_click")
            debug_set_player_level(6)
            print("Level:", state.player_level)

        elif debug_action == ACTION_LEVEL_10:
            sounds.audio.play_sound("button_click")
            debug_set_player_level(10)
            print("Level:", state.player_level)

        elif debug_action == ACTION_LEVEL_MAX:
            sounds.audio.play_sound("button_click")
            debug_set_player_level(
                max(LEVEL_XP_THRESHOLDS)
            )
            from solitaireplus.debug.unlocks import debug_unlock_everything
            unlock_summary = debug_unlock_everything(game_namespace())
            show_debug_message(
                "Max level + all current unlocks enabled"
            )
            print("Level:", state.player_level, "Unlocks:", unlock_summary)

        elif debug_action == ACTION_ACHIEVEMENT_TEST:
            sounds.audio.play_sound("button_click")
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
            sounds.audio.play_sound("button_click")

            if state.debug_previous_state is not None:
                state.current_state = state.debug_previous_state

    return


def loop_event_cryptid_creatures(event):
    """Old main-loop event branch for STATE_CRYPTID_CREATURES."""
    if cryptid_screen.handle_event(event, state.game_mouse_pos) == "return":
        if cryptid_screen.career_mode:
            leave_career_cryptid()
        else:leave_free_play_game()


def loop_event_score_four_mode_select(event):
    """Old main-loop event branch for STATE_SCORE_FOUR_MODE_SELECT."""

    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and score_four_game.rating_info_open:
        score_four_game.rating_info_open = False
        return
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.game_mouse_pos is not None:
        from solitaireplus.games.cards.score_four_ui import handle_rating_info_click
        if handle_rating_info_click(state.game_mouse_pos, score_four_game):
            sounds.audio.play_sound("button_click")
            return

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.game_mouse_pos is not None:
        from solitaireplus.games.cards.score_four_ui import LAYOUT_RECT, toggle_layout, play_control_sound
        if not score_four_game.difficulty_menu and LAYOUT_RECT.collidepoint(state.game_mouse_pos):
            toggle_layout(score_four_game)
            play_control_sound(sounds.audio, "select")
            return

    if score_four_game.difficulty_menu and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        from solitaireplus.games.cards.score_four_ui import difficulty_action
        choice = difficulty_action(state.menu_mouse_pos)
        if choice == "back":
            score_four_game.difficulty_menu = False
        elif choice:
            score_four_game.difficulty_menu = False
            score_four_game.start_solo_session(choice)
            state.current_state = state_names.STATE_SCORE_FOUR
        sounds.audio.play_sound("button_click")
        return

    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.menu_mouse_pos is not None
    ):

        # ------------------------------------------
        # Solo
        # ------------------------------------------

        if (
                score_four_solo_rect.collidepoint(
                    state.menu_mouse_pos
                )
        ):

            sounds.audio.play_sound(
                "button_click"
            )

            score_four_game.difficulty_menu = True

        # ------------------------------------------
        # Competitive
        # ------------------------------------------

        elif (
                score_four_competitive_rect.collidepoint(
                    state.menu_mouse_pos
                )
        ):

            state.score_four_opponent_choices = (
                get_score_four_opponent_choices()
            )

            if state.score_four_opponent_npc is not None:
                opponent_name = (
                    state.score_four_opponent_npc["name"]
                )
            else:
                opponent_name = "NPC"

            sounds.audio.play_sound(
                "button_click"
            )

            state.current_state = state_names.STATE_SCORE_FOUR_OPPONENT_SELECT

        # ------------------------------------------
        # Return
        # ------------------------------------------

        elif (
                score_four_mode_return_rect.collidepoint(
                    state.menu_mouse_pos
                )
        ):

            sounds.audio.play_sound(
                "button_click"
            )

            if state.current_game_mode == "free":
                finish_free_play_sandbox()
                state.current_state = state_names.STATE_FREE_PLAY_SELECT
            else:
                state.current_state = state_names.STATE_CAREER_EVENT_SELECT


def loop_event_score_four_opponent_select(event):
    """Old main-loop event branch for STATE_SCORE_FOUR_OPPONENT_SELECT."""

    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):

        opponent_clicked = False

        # ------------------------------------------
        # Opponent cards
        # ------------------------------------------

        for state.index, state.rect in enumerate(
                score_four_opponent_rects
        ):

            if (
                    state.index
                    < len(
                state.score_four_opponent_choices
            )
                    and state.rect.collidepoint(
                state.game_mouse_pos
            )
            ):
                state.score_four_opponent_npc = (
                    state.score_four_opponent_choices[
                        state.index
                    ]
                )

                sounds.audio.play_sound(
                    "button_click"
                )

                opponent_clicked = True

                score_four_game.start_competitive_session(
                    skill_tier=(
                        state.score_four_opponent_npc[
                            "skill_tier"
                        ]
                    ),
                    rating=state.score_four_opponent_npc.get("career_ratings", {}).get("score_four"),
                )

                state.current_state = state_names.STATE_SCORE_FOUR

                break

        # ------------------------------------------
        # Return
        # ------------------------------------------

        if (
                not opponent_clicked
                and score_four_opponent_return_rect.collidepoint(
            state.game_mouse_pos
        )
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.current_state = state_names.STATE_SCORE_FOUR_MODE_SELECT


def loop_event_seven_card_stud_buy_in(event):
    """Old main-loop event branch for STATE_SEVEN_CARD_STUD_BUY_IN."""
    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):
        buy_in_action = (
            get_seven_card_stud_buy_in_action(
                state.game_mouse_pos,
                state.career_cash,
                SEVEN_CARD_STUD_MIN_BUY_IN
            )
        )

        if buy_in_action is not None:
            action_type, amount = (
                buy_in_action
            )

            if action_type == "back":
                sounds.audio.play_sound(
                    "button_click"
                )

                if state.current_game_mode == "free":
                    finish_free_play_sandbox()
                    state.current_state = state_names.STATE_FREE_PLAY_SELECT
                else:
                    state.current_state = state_names.STATE_CAREER_EVENT_SELECT

            elif action_type == "buy_in":
                sounds.audio.play_sound(
                    "button_click"
                )

                start_seven_card_stud_session(
                    amount
                )


def loop_event_seven_card_stud(event):
    """Old main-loop event branch for STATE_SEVEN_CARD_STUD."""

    if (
            is_holdem_options_open()
            and event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):
        option_changed = handle_holdem_options_click(
            state.game_mouse_pos
        )
        if option_changed:
            sounds.audio.play_sound("button_click")
            if not is_holdem_auto_deal_enabled():
                state.seven_card_stud_next_hand_at = 0
        return

    if (
            event.type == pygame.MOUSEWHEEL
            and state.game_mouse_pos is not None
            and STUD_LOG_RECT.collidepoint(
                state.game_mouse_pos
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
            and state.game_mouse_pos is not None
    ):
        if handle_seven_card_stud_panel_click(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )
            return

        stud_action = (
            get_seven_card_stud_action(
                state.game_mouse_pos,
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
                sounds.audio.play_sound(
                    "button_click"
                )

                process_seven_card_stud_showdown()
                finish_seven_card_stud_session()

            elif (
                    seven_card_stud_game.player_stack > 0
                    and not seven_card_stud_game.player_busted
            ):
                sounds.audio.play_sound(
                    "button_click"
                )

                state.seven_card_stud_next_hand_at = 0

                if seven_card_stud_game.start_hand():
                    sounds.audio.play_sound(
                        "card_draw"
                    )

        elif (
                stud_action
                == STUD_ACTION_FOLD
        ):
            if seven_card_stud_game.player_fold():
                sounds.audio.play_sound(
                    "button_click"
                )

                state.seven_card_stud_session_net = (
                        seven_card_stud_game.player_stack
                        - state.seven_card_stud_starting_stack
                )

                state.career_event_has_activity = True

        elif (
                stud_action
                == STUD_ACTION_CHECK_CALL
        ):
            amount_to_call = (
                seven_card_stud_game
                .get_player_amount_to_call()
            )

            if amount_to_call > 0:
                state.success = (
                    seven_card_stud_game.player_call()
                )
                state.player_chat_action = "call"
            else:
                state.success = (
                    seven_card_stud_game.player_check()
                )
                state.player_chat_action = "check"

            if state.success:
                if amount_to_call > 0:
                    play_texas_holdem_chip_sound()
                else:
                    sounds.audio.play_sound(
                        "poker_check"
                    )

                post_seven_card_stud_chat(
                    generate_player_action_reaction(
                        seven_card_stud_game,
                        state.player_chat_action
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
                state.player_chat_action = "bet"
                state.success = (
                    seven_card_stud_game.player_bet(
                        wager_target
                    )
                )
            else:
                state.player_chat_action = "raise"
                state.success = (
                    seven_card_stud_game.player_raise(
                        wager_target
                    )
                )

            if state.success:
                play_texas_holdem_chip_sound()

                post_seven_card_stud_chat(
                    generate_player_action_reaction(
                        seven_card_stud_game,
                        state.player_chat_action
                    )
                )

                schedule_seven_card_stud_npc_action()

        elif (
                stud_action
                == STUD_ACTION_OPTIONS
        ):
            sounds.audio.play_sound("button_click")
            toggle_holdem_options()

        elif (
                stud_action
                == STUD_ACTION_RETURN
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            finish_seven_card_stud_session()


def loop_event_five_card_draw_buy_in(event):
    """Old main-loop event branch for STATE_FIVE_CARD_DRAW_BUY_IN."""

    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):

        buy_in_action = (
            get_five_card_draw_buy_in_action(
                state.game_mouse_pos,
                state.career_cash,
                FIVE_CARD_DRAW_MIN_BUY_IN
            )
        )

        if buy_in_action is not None:

            action_type, amount = (
                buy_in_action
            )

            if action_type == "back":
                sounds.audio.play_sound(
                    "button_click"
                )

                if state.current_game_mode == "free":
                    finish_free_play_sandbox()
                    state.current_state = state_names.STATE_FREE_PLAY_SELECT
                else:
                    state.current_state = state_names.STATE_CAREER_EVENT_SELECT

            elif action_type == "buy_in":

                sounds.audio.play_sound(
                    "button_click"
                )

                start_five_card_draw_session(
                    amount
                )


def loop_event_five_card_draw(event):
    """Old main-loop event branch for STATE_FIVE_CARD_DRAW."""

    if (
            is_holdem_options_open()
            and event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):
        option_changed = handle_holdem_options_click(
            state.game_mouse_pos
        )
        if option_changed:
            sounds.audio.play_sound("button_click")
            if not is_holdem_auto_deal_enabled():
                state.five_card_draw_next_hand_at = 0
        return

    if event.type == pygame.KEYDOWN:
        if handle_five_card_draw_manual_bet_key(
                event,
                five_card_draw_game
        ):
            return

    if (
            event.type == pygame.MOUSEMOTION
            and state.game_mouse_pos is not None
    ):
        drag_five_card_draw_bet_slider(
            state.game_mouse_pos
        )

    elif (
            event.type == pygame.MOUSEBUTTONUP
            and event.button == 1
    ):
        stop_five_card_draw_bet_slider()

    elif (
            event.type == pygame.MOUSEWHEEL
            and state.game_mouse_pos is not None
            and DRAW_LOG_RECT.collidepoint(
                state.game_mouse_pos
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
            and state.game_mouse_pos is not None
    ):

        if handle_five_card_draw_manual_bet_click(
                state.game_mouse_pos,
                five_card_draw_game
        ):
            sounds.audio.play_sound("button_click")
            return

        if handle_five_card_draw_panel_click(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )
            return

        if handle_five_card_draw_card_click(
                state.game_mouse_pos,
                five_card_draw_game
        ):
            sounds.audio.play_sound(
                "button_click"
            )
            return

        if update_five_card_draw_bet_slider(
                state.game_mouse_pos,
                five_card_draw_game
        ):
            sounds.audio.play_sound("button_click")
            return

        if (
                five_card_draw_game.current_stage
                in (
                    "preflop",
                    "post_draw",
                )
                and handle_five_card_draw_bet_preset(
                    state.game_mouse_pos
                )
        ):
            sounds.audio.play_sound(
                "button_click"
            )
            return

        draw_action = (
            get_five_card_draw_action(
                state.game_mouse_pos,
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
                sounds.audio.play_sound(
                    "button_click"
                )

                process_five_card_draw_showdown()
                finish_five_card_draw_session()

            elif (
                    five_card_draw_game.player_stack > 0
                    and not five_card_draw_game.player_busted
            ):
                sounds.audio.play_sound(
                    "button_click"
                )

                state.five_card_draw_next_hand_at = 0

                if five_card_draw_game.start_hand():
                    sounds.audio.play_sound(
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
                sounds.audio.play_sound(
                    "card_draw"
                )

                clear_five_card_draw_selection()

        elif (
                draw_action
                == DRAW_ACTION_FOLD
        ):

            if five_card_draw_game.player_fold():
                sounds.audio.play_sound(
                    "button_click"
                )

                state.five_card_draw_session_net = (
                        five_card_draw_game.player_stack
                        - state.five_card_draw_starting_stack
                )

                state.career_event_has_activity = True

        elif (
                draw_action
                == DRAW_ACTION_CHECK_CALL
        ):

            amount_to_call = (
                five_card_draw_game
                .get_player_amount_to_call()
            )

            if amount_to_call > 0:
                state.success = (
                    five_card_draw_game.player_call()
                )
                state.player_chat_action = "call"

            else:
                state.success = (
                    five_card_draw_game.player_check()
                )
                state.player_chat_action = "check"

            if state.success:

                if amount_to_call > 0:
                    play_texas_holdem_chip_sound()

                else:
                    sounds.audio.play_sound(
                        "poker_check"
                    )

                post_five_card_draw_chat(
                    generate_player_action_reaction(
                        five_card_draw_game,
                        state.player_chat_action
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
                state.player_chat_action = "bet"
                state.success = five_card_draw_game.player_bet(
                    bet_amount
                )

            else:
                state.player_chat_action = "raise"
                state.success = five_card_draw_game.player_raise(
                    bet_amount
                )

            if state.success:
                play_texas_holdem_chip_sound()
                clear_five_card_draw_manual_bet()

                post_five_card_draw_chat(
                    generate_player_action_reaction(
                        five_card_draw_game,
                        state.player_chat_action
                    )
                )

                schedule_five_card_draw_npc_action()

        elif (
                draw_action
                == DRAW_ACTION_OPTIONS
        ):
            sounds.audio.play_sound("button_click")
            toggle_holdem_options()

        elif (
                draw_action
                == DRAW_ACTION_RETURN
        ):

            sounds.audio.play_sound(
                "button_click"
            )

            finish_five_card_draw_session()


def loop_event_texas_holdem_buy_in(event):
    """Old main-loop event branch for STATE_TEXAS_HOLDEM_BUY_IN."""

    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):

        buy_in_action = (
            get_texas_holdem_buy_in_action(
                state.game_mouse_pos,
                state.career_cash,
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
                sounds.audio.play_sound(
                    "button_click"
                )

                if state.current_game_mode == "free":
                    finish_free_play_sandbox()
                    state.current_state = state_names.STATE_FREE_PLAY_SELECT
                else:
                    state.current_state = state_names.STATE_CAREER_EVENT_SELECT

            # ------------------------------------------
            # Buy in
            # ------------------------------------------

            elif (
                    action_type
                    == "buy_in"
            ):

                sounds.audio.play_sound(
                    "button_click"
                )

                start_texas_holdem_session(
                    amount
                )


def loop_event_texas_holdem(event):
    """Old main-loop event branch for STATE_TEXAS_HOLDEM."""

    if getattr(texas_holdem_game, "recap_open", False):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            from solitaireplus.games.poker.recap import get_recap_action
            handle_recap_action(texas_holdem_game, get_recap_action(state.game_mouse_pos, texas_holdem_game))
            if not texas_holdem_game.recap_open:
                state.texas_holdem_next_hand_at = 0
                if texas_holdem_game.player_busted or texas_holdem_game.all_npcs_busted():
                    state.texas_holdem_session_end_at = pygame.time.get_ticks() + TEXAS_HOLDEM_SESSION_END_DELAY
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            texas_holdem_game.recap_open = False
            state.texas_holdem_next_hand_at = 0
            if texas_holdem_game.player_busted or texas_holdem_game.all_npcs_busted():
                state.texas_holdem_session_end_at = pygame.time.get_ticks() + TEXAS_HOLDEM_SESSION_END_DELAY
        return

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
            return

        if (
                event.key == pygame.K_F7
                and state.current_state
                == state_names.STATE_TEXAS_HOLDEM
        ):
            debug_setup_holdem_heads_up()

            return

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

                state.career_event_has_activity = True

                sounds.audio.play_sound(
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
                    sounds.audio.play_sound(
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
                    sounds.audio.play_sound(
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
                    sounds.audio.play_sound(
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
                    state.texas_holdem_session_net = (
                            texas_holdem_game.player_stack
                            - state.texas_holdem_starting_stack
                    )

                    state.career_event_has_activity = True

                    sounds.audio.play_sound(
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
            and state.game_mouse_pos is not None
            and HOLDEM_LOG_RECT.collidepoint(
        state.game_mouse_pos
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
            and state.game_mouse_pos is not None
    ):

        drag_holdem_bet_slider(
            state.game_mouse_pos
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
            and state.game_mouse_pos is not None
    ):

        # ==================================================
        # Poker options overlay
        # ==================================================

        if is_holdem_options_open():

            option_changed = (
                handle_holdem_options_click(
                    state.game_mouse_pos
                )
            )

            if option_changed:
                sounds.audio.play_sound(
                    "button_click"
                )

            # Consume every click while overlay is open.
            return

        # ==================================================
        # Manual bet / raise-to entry
        # ==================================================

        if handle_holdem_manual_bet_click(
                state.game_mouse_pos,
                texas_holdem_game
        ):
            sounds.audio.play_sound("button_click")
            return

        # ==================================================
        # Log / Chat tabs
        # ==================================================

        panel_handled = (
            handle_holdem_panel_click(
                state.game_mouse_pos
            )
        )

        if panel_handled:

            sounds.audio.play_sound(
                "button_click"
            )

        else:

            # ==================================================
            # Bet slider / shortcut buttons
            # ==================================================

            slider_handled = (
                update_holdem_bet_slider(
                    state.game_mouse_pos,
                    texas_holdem_game
                )
            )

            if slider_handled:

                sounds.audio.play_sound(
                    "button_click"
                )

            else:

                # ==================================================
                # Main Hold'em controls
                # ==================================================

                holdem_action = (
                    get_texas_holdem_action(
                        state.game_mouse_pos,
                        texas_holdem_game
                    )
                )

                # ------------------------------------------
                # Next Hand
                # ------------------------------------------

                if handle_recap_action(texas_holdem_game, holdem_action):
                    if holdem_action != "recap_block":
                        sounds.audio.play_sound("button_click")
                    state.texas_holdem_next_hand_at = 0
                    if not texas_holdem_game.recap_open and (texas_holdem_game.player_busted or texas_holdem_game.all_npcs_busted()):
                        state.texas_holdem_session_end_at = pygame.time.get_ticks() + TEXAS_HOLDEM_SESSION_END_DELAY
                elif (
                        holdem_action
                        == HOLDEM_ACTION_NEXT_HAND
                ):

                    if (
                            texas_holdem_game.all_npcs_busted()
                            and not texas_holdem_game.player_busted
                    ):
                        sounds.audio.play_sound(
                            "button_click"
                        )

                        process_texas_holdem_showdown()

                        finish_texas_holdem_session()

                    elif (
                            texas_holdem_game.player_stack > 0
                            and not texas_holdem_game.player_busted
                    ):
                        sounds.audio.play_sound(
                            "button_click"
                        )

                        state.texas_holdem_next_hand_at = 0

                        if texas_holdem_game.start_hand():
                            play_texas_holdem_new_hand_sound()

                elif (
                        holdem_action
                        == HOLDEM_ACTION_FOLD
                ):

                    if texas_holdem_game.player_fold():
                        sounds.audio.play_sound(
                            "button_click"
                        )

                        state.texas_holdem_session_net = (
                                texas_holdem_game.player_stack
                                - state.texas_holdem_starting_stack
                        )

                        state.career_event_has_activity = True

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

                        state.success = (
                            texas_holdem_game
                            .player_call()
                        )

                    else:

                        state.success = (
                            texas_holdem_game
                            .player_check()
                        )

                    if state.success:

                        if amount_to_call > 0:

                            play_texas_holdem_chip_sound()

                            state.player_chat_action = (
                                "call"
                            )

                        else:

                            sounds.audio.play_sound(
                                "poker_check"
                            )

                            state.player_chat_action = (
                                "check"
                            )

                        post_texas_holdem_chat(
                            generate_player_action_reaction(
                                texas_holdem_game,
                                state.player_chat_action
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

                        state.player_chat_action = (
                            "bet"
                        )

                        state.success = (
                            texas_holdem_game
                            .player_bet(
                                bet_amount
                            )
                        )

                    else:

                        state.player_chat_action = (
                            "raise"
                        )

                        state.success = (
                            texas_holdem_game
                            .player_raise(
                                bet_amount
                            )
                        )

                    if state.success:
                        play_texas_holdem_chip_sound()
                        clear_holdem_manual_bet()

                        post_texas_holdem_chat(
                            generate_player_action_reaction(
                                texas_holdem_game,
                                state.player_chat_action
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

                    sounds.audio.play_sound(
                        "button_click"
                    )

                    finish_texas_holdem_session()

                # ------------------------------------------
                # Options
                # ------------------------------------------

                elif holdem_action == "options":

                    sounds.audio.play_sound(
                        "button_click"
                    )

                    toggle_holdem_options()


def loop_event_blackjack_bet(event):
    """Old main-loop event branch for STATE_BLACKJACK_BET."""

    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):

        selected_bet = None

        # ==========================================
        # Bet selection
        # ==========================================

        if state.career_cash > 0:

            if blackjack_bet_1_rect.collidepoint(
                    state.game_mouse_pos
            ):

                state.blackjack_selected_bet_percentage = (
                    0.01
                )

                selected_bet = (
                    get_blackjack_bet(
                        state.blackjack_selected_bet_percentage
                    )
                )

            elif blackjack_bet_2_rect.collidepoint(
                    state.game_mouse_pos
            ):

                state.blackjack_selected_bet_percentage = (
                    0.02
                )

                selected_bet = (
                    get_blackjack_bet(
                        state.blackjack_selected_bet_percentage
                    )
                )

            elif blackjack_bet_5_rect.collidepoint(
                    state.game_mouse_pos
            ):

                state.blackjack_selected_bet_percentage = (
                    0.05
                )

                selected_bet = (
                    get_blackjack_bet(
                        state.blackjack_selected_bet_percentage
                    )
                )

            elif blackjack_bet_10_rect.collidepoint(
                    state.game_mouse_pos
            ):

                state.blackjack_selected_bet_percentage = (
                    0.10
                )

                selected_bet = (
                    get_blackjack_bet(
                        state.blackjack_selected_bet_percentage
                    )
                )

            elif blackjack_bet_all_rect.collidepoint(
                    state.game_mouse_pos
            ):

                state.blackjack_selected_bet_percentage = (
                    1.0
                )

                selected_bet = (
                    get_blackjack_bet(
                        state.blackjack_selected_bet_percentage
                    )
                )

        # ==========================================
        # Start hand
        # ==========================================

        if (
                selected_bet is not None
                and selected_bet > 0
                and state.career_cash >= selected_bet
        ):

            sounds.audio.play_sound(
                "button_click"
            )

            state.blackjack_round_doubled = False
            state.blackjack_round_all_in = (
                selected_bet >= state.career_cash
            )
            state.blackjack_round_start_bet = selected_bet

            state.career_cash -= (
                selected_bet
            )

            blackjack_game.start_round(
                selected_bet
            )

            state.career_event_has_activity = True

            state.current_state = state_names.STATE_BLACKJACK

        # ==========================================
        # Return
        # ==========================================

        elif blackjack_bet_return_rect.collidepoint(
                state.game_mouse_pos
        ):

            sounds.audio.play_sound(
                "button_click"
            )

            if state.current_game_mode == "free":
                finish_free_play_sandbox()
            state.current_state = (
                state_names.STATE_FREE_PLAY_SELECT if state.current_game_mode == "free" else state_names.STATE_CAREER_EVENT_SELECT
            )


def loop_event_blackjack(event):
    """Old main-loop event branch for STATE_BLACKJACK."""

    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
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

        for state.index, state.rect in enumerate(blackjack_bet_dropdown_rects):
            if state.rect.collidepoint(state.game_mouse_pos):
                state.blackjack_selected_bet_percentage = next_bet_choices[state.index]
                state.blackjack_bet_dropdown_open = False
                sounds.audio.play_sound("button_click")
                next_bet_clicked = True
                break

        # ==========================================
        # Hit
        # ==========================================

        if next_bet_clicked:
            return

        # ==========================================

        elif (
                not blackjack_game.round_complete
                and blackjack_hit_rect.collidepoint(
            state.game_mouse_pos
        )
        ):

            sounds.audio.play_sound(
                "card_draw"
            )

            blackjack_game.hit()

        # ==========================================
        # Stand
        # ==========================================

        elif (
                not blackjack_game.round_complete
                and blackjack_stand_rect.collidepoint(
            state.game_mouse_pos
        )
        ):

            sounds.audio.play_sound(
                "button_click"
            )

            blackjack_game.stand()

        # ==========================================
        # Split
        # ==========================================

        elif (
                blackjack_game.can_split()
                and state.career_cash >= blackjack_game.current_hand_bet()
                and blackjack_split_rect.collidepoint(
            state.game_mouse_pos
        )
        ):
            state.additional_bet = blackjack_game.current_hand_bet()

            if state.career_cash >= state.additional_bet:
                state.career_cash -= state.additional_bet
                sounds.audio.play_sound("button_click")
                sounds.audio.play_sound("card_draw")
                blackjack_game.split_hand()

        # ==========================================
        # Double
        # ==========================================

        elif (
                blackjack_game.can_double_down()
                and state.career_cash >= blackjack_game.current_hand_bet()
                and blackjack_double_rect.collidepoint(
            state.game_mouse_pos
        )
        ):

            state.additional_bet = blackjack_game.current_hand_bet()

            if state.career_cash >= state.additional_bet:
                state.career_cash -= state.additional_bet

                sounds.audio.play_sound(
                    "button_click"
                )

                sounds.audio.play_sound(
                    "card_draw"
                )

                state.blackjack_round_doubled = True
                blackjack_game.double_down()

        # ==========================================
        # Deal Again
        # ==========================================

        elif (
                blackjack_game.round_complete
                and state.career_cash > 0
                and blackjack_deal_again_rect.collidepoint(
            state.game_mouse_pos
        )
        ):

            if (
                    state.blackjack_selected_bet_percentage
                    is not None
            ):

                next_bet = (
                    get_blackjack_bet(
                        state.blackjack_selected_bet_percentage
                    )
                )

                if (
                        next_bet > 0
                        and state.career_cash >= next_bet
                ):
                    sounds.audio.play_sound(
                        "button_click"
                    )

                    state.blackjack_round_doubled = False
                    state.blackjack_round_all_in = (
                        next_bet >= state.career_cash
                    )
                    state.blackjack_round_start_bet = next_bet

                    state.career_cash -= (
                        next_bet
                    )

                    blackjack_game.start_round(
                        next_bet
                    )

                    state.blackjack_bet_dropdown_open = False

        # ==========================================
        # Return
        # ==========================================

        elif (
                blackjack_game.round_complete
                and blackjack_return_rect.collidepoint(
            state.game_mouse_pos
        )
        ):

            sounds.audio.play_sound(
                "button_click"
            )

            state.blackjack_bet_dropdown_open = False

            if state.current_game_mode == "free":
                finish_free_play_sandbox()
            state.current_state = (
                state_names.STATE_FREE_PLAY_SELECT if state.current_game_mode == "free" else state_names.STATE_CAREER_EVENT_SELECT
            )


def loop_event_roulette(event):
    """Old main-loop event branch for STATE_ROULETTE."""

    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button in (
            1,
            3
    )
            and state.game_mouse_pos is not None
    ):

        roulette_action = (
            get_roulette_action(
                state.game_mouse_pos
            )
        )

        is_right_click = (
                event.button == 3
        )

        # ==========================================
        # CHIP SELECTION
        # ==========================================

        if roulette_action == ACTION_CHIP_10:

            state.roulette_chip_value = 10

            sounds.audio.play_sound(
                "button_click"
            )

        elif roulette_action == ACTION_CHIP_50:

            state.roulette_chip_value = 50

            sounds.audio.play_sound(
                "button_click"
            )

        elif roulette_action == ACTION_CHIP_100:

            state.roulette_chip_value = 100

            sounds.audio.play_sound(
                "button_click"
            )

        elif roulette_action == ACTION_CHIP_500:

            state.roulette_chip_value = 500

            sounds.audio.play_sound(
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
                sounds.audio.play_sound(
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

            state.wager = state.roulette_chip_value

            if is_right_click:

                if roulette_game.remove_bet(
                        "number",
                        number,
                        state.wager
                ):
                    sounds.audio.play_sound(
                        "button_click"
                    )

            else:

                if (
                        state.wager > 0
                        and (
                        roulette_game.get_total_bet()
                        + state.wager
                ) <= state.career_cash
                ):
                    roulette_game.place_bet(
                        "number",
                        number,
                        state.wager
                    )

                    sounds.audio.play_sound(
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

            state.wager = state.roulette_chip_value

            if is_right_click:

                if roulette_game.remove_bet(
                        "color",
                        "red",
                        state.wager
                ):
                    sounds.audio.play_sound(
                        "button_click"
                    )

            else:

                if (
                        state.wager > 0
                        and (
                        roulette_game.get_total_bet()
                        + state.wager
                ) <= state.career_cash
                ):
                    roulette_game.place_bet(
                        "color",
                        "red",
                        state.wager
                    )

                    sounds.audio.play_sound(
                        "button_click"
                    )

        # ==========================================
        # BLACK
        # ==========================================

        elif (
                roulette_action == ACTION_BET_BLACK
                and not roulette_game.spinning
        ):

            state.wager = state.roulette_chip_value

            if is_right_click:

                if roulette_game.remove_bet(
                        "color",
                        "black",
                        state.wager
                ):
                    sounds.audio.play_sound(
                        "button_click"
                    )

            else:

                if (
                        state.wager > 0
                        and (
                        roulette_game.get_total_bet()
                        + state.wager
                ) <= state.career_cash
                ):
                    roulette_game.place_bet(
                        "color",
                        "black",
                        state.wager
                    )

                    sounds.audio.play_sound(
                        "button_click"
                    )

        # ==========================================
        # ODD
        # ==========================================

        elif (
                roulette_action == ACTION_BET_ODD
                and not roulette_game.spinning
        ):

            state.wager = state.roulette_chip_value

            if is_right_click:

                if roulette_game.remove_bet(
                        "parity",
                        "odd",
                        state.wager
                ):
                    sounds.audio.play_sound(
                        "button_click"
                    )

            else:

                if (
                        state.wager > 0
                        and (
                        roulette_game.get_total_bet()
                        + state.wager
                ) <= state.career_cash
                ):
                    roulette_game.place_bet(
                        "parity",
                        "odd",
                        state.wager
                    )

                    sounds.audio.play_sound(
                        "button_click"
                    )

        # ==========================================
        # EVEN
        # ==========================================

        elif (
                roulette_action == ACTION_BET_EVEN
                and not roulette_game.spinning
        ):

            state.wager = state.roulette_chip_value

            if is_right_click:

                if roulette_game.remove_bet(
                        "parity",
                        "even",
                        state.wager
                ):
                    sounds.audio.play_sound(
                        "button_click"
                    )

            else:

                if (
                        state.wager > 0
                        and (
                        roulette_game.get_total_bet()
                        + state.wager
                ) <= state.career_cash
                ):
                    roulette_game.place_bet(
                        "parity",
                        "even",
                        state.wager
                    )

                    sounds.audio.play_sound(
                        "button_click"
                    )

        # ==========================================
        # LOW
        # ==========================================

        elif (
                roulette_action == ACTION_BET_LOW
                and not roulette_game.spinning
        ):

            state.wager = state.roulette_chip_value

            if is_right_click:

                if roulette_game.remove_bet(
                        "range",
                        "low",
                        state.wager
                ):
                    sounds.audio.play_sound(
                        "button_click"
                    )

            else:

                if (
                        state.wager > 0
                        and (
                        roulette_game.get_total_bet()
                        + state.wager
                ) <= state.career_cash
                ):
                    roulette_game.place_bet(
                        "range",
                        "low",
                        state.wager
                    )

                    sounds.audio.play_sound(
                        "button_click"
                    )

        # ==========================================
        # HIGH
        # ==========================================

        elif (
                roulette_action == ACTION_BET_HIGH
                and not roulette_game.spinning
        ):

            state.wager = state.roulette_chip_value

            if is_right_click:

                if roulette_game.remove_bet(
                        "range",
                        "high",
                        state.wager
                ):
                    sounds.audio.play_sound(
                        "button_click"
                    )

            else:

                if (
                        state.wager > 0
                        and (
                        roulette_game.get_total_bet()
                        + state.wager
                ) <= state.career_cash
                ):
                    roulette_game.place_bet(
                        "range",
                        "high",
                        state.wager
                    )

                    sounds.audio.play_sound(
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
                    and state.career_cash >= total_bet
            ):

                state.career_cash -= (
                    total_bet

                )

                if roulette_game.start_spin():
                    state.career_event_has_activity = True

                    sounds.audio.play_sound(

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

            sounds.audio.play_sound(
                "button_click"
            )

            if state.current_game_mode == "free":
                finish_free_play_sandbox()
                state.current_state = state_names.STATE_FREE_PLAY_SELECT
            else:
                state.current_state = state_names.STATE_CAREER_EVENT_SELECT


def loop_event_horse_races(event):
    """Old main-loop event branch for STATE_HORSE_RACES."""

    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):
        horse_action = get_horse_races_action(state.game_mouse_pos)

        if (
                horse_action is not None
                and horse_action.startswith(HORSE_RACES_ACTION_HORSE_PREFIX)
                and horse_races_game.stage == "betting"
        ):
            try:
                state.horse_index = int(
                    horse_action[len(HORSE_RACES_ACTION_HORSE_PREFIX):]
                )
            except ValueError:
                state.horse_index = -1
            if horse_races_game.set_selected_horse(state.horse_index):
                sounds.audio.play_sound("button_click")

        elif horse_action == HORSE_RACES_ACTION_WIN:
            if horse_races_game.set_bet_type("win"):
                sounds.audio.play_sound("button_click")

        elif horse_action == HORSE_RACES_ACTION_PLACE:
            if horse_races_game.set_bet_type("place"):
                sounds.audio.play_sound("button_click")

        elif horse_action == HORSE_RACES_ACTION_SHOW:
            if horse_races_game.set_bet_type("show"):
                sounds.audio.play_sound("button_click")

        elif horse_action == HORSE_RACES_ACTION_CHIP_10:
            if horse_races_game.set_chip_value(10):
                sounds.audio.play_sound("button_click")

        elif horse_action == HORSE_RACES_ACTION_CHIP_50:
            if horse_races_game.set_chip_value(50):
                sounds.audio.play_sound("button_click")

        elif horse_action == HORSE_RACES_ACTION_CHIP_100:
            if horse_races_game.set_chip_value(100):
                sounds.audio.play_sound("button_click")

        elif horse_action == HORSE_RACES_ACTION_CHIP_500:
            if horse_races_game.set_chip_value(500):
                sounds.audio.play_sound("button_click")

        elif horse_action == HORSE_RACES_ACTION_PLACE_BET:
            if horse_races_game.place_selected_bet():
                sounds.audio.play_sound("poker_chips_1")

        elif horse_action == HORSE_RACES_ACTION_CLEAR_BETS:
            if horse_races_game.clear_bets():
                sounds.audio.play_sound("poker_chips_1")

        elif horse_action == HORSE_RACES_ACTION_START_RACE:
            if horse_races_game.stage == "betting":
                if horse_races_game.start_race(pygame.time.get_ticks()):
                    sounds.audio.play_sound("button_click")
                    start_horse_race_music()
                    state.career_event_has_activity = True
            elif horse_races_game.stage == "results":
                if horse_races_game.prepare_next_race():
                    sounds.audio.play_sound("button_click")

        elif (
                horse_action == HORSE_RACES_ACTION_RETURN
                and horse_races_game.stage != "racing"
        ):
            sounds.audio.play_sound("button_click")
            stop_horse_race_music(300)
            finish_horse_races_session()


def loop_event_faro(event):
    """Old main-loop event branch for STATE_FARO."""

    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button in (1, 3)
            and state.game_mouse_pos is not None
    ):
        faro_action = get_faro_action(state.game_mouse_pos, event.button, faro_game)
        is_right_click = (event.button == 3)

        if faro_action == FARO_ACTION_CHIP_10:
            state.faro_chip_value = 10
            sounds.audio.play_sound("button_click")

        elif faro_action == FARO_ACTION_CHIP_50:
            state.faro_chip_value = 50
            sounds.audio.play_sound("button_click")

        elif faro_action == FARO_ACTION_CHIP_100:
            state.faro_chip_value = 100
            sounds.audio.play_sound("button_click")

        elif faro_action == FARO_ACTION_CHIP_500:
            state.faro_chip_value = 500
            sounds.audio.play_sound("button_click")

        elif faro_action == FARO_ACTION_CLEAR_BETS:
            if faro_game.clear_bets():
                sounds.audio.play_sound("poker_chips_1")

        elif (
                faro_action is not None
                and faro_action.startswith(FARO_ACTION_BET_RANK_PREFIX)
        ):
            rank = faro_action[len(FARO_ACTION_BET_RANK_PREFIX):]
            if is_right_click:
                if faro_game.remove_bet(rank, state.faro_chip_value):
                    sounds.audio.play_sound("poker_chips_1")
            else:
                if faro_game.place_bet(rank, state.faro_chip_value):
                    sounds.audio.play_sound("poker_chips_1")

        elif (
                faro_action == FARO_ACTION_DEAL
                and event.button == 1
                and not faro_game.session_complete
        ):
            if faro_game.deal_turn():
                net = faro_game.last_profit - faro_game.last_loss - faro_game.last_doublet_loss
                if net: career_rewards.rate_house_game("faro", net)
                sounds.audio.play_sound("card_draw")
                if faro_game.turns_dealt > 0 and faro_game.wagered_total > 0:
                    state.career_event_has_activity = True

        elif (
                faro_action == FARO_ACTION_RETURN
                and event.button == 1
        ):
            sounds.audio.play_sound("button_click")
            claim_faro_session_result()
            if state.current_game_mode == "free":
                finish_free_play_sandbox()
                state.current_state = state_names.STATE_FREE_PLAY_SELECT
            else:
                state.current_state = state_names.STATE_CAREER_EVENT_SELECT


def loop_event_five_o_poker(event):
    """Old main-loop event branch for STATE_FIVE_O_POKER."""

    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):
        five_o_action = get_five_o_action(
            state.game_mouse_pos,
            five_o_poker_game
        )

        if five_o_action == "ui_click":
            sounds.audio.play_sound("button_click")

        elif five_o_action == FIVE_O_ACTION_RETURN:
            sounds.audio.play_sound("button_click")
            finish_five_o_poker_session()

        elif five_o_action == FIVE_O_ACTION_NEXT_HAND:
            if five_o_poker_game.start_hand():
                sounds.audio.play_sound("card_shuffle")

        elif (
                five_o_action is not None
                and five_o_action.startswith(FIVE_O_ACTION_COLUMN_PREFIX)
        ):
            try:
                state.column_index = int(
                    five_o_action[len(FIVE_O_ACTION_COLUMN_PREFIX):]
                )
            except ValueError:
                state.column_index = -1
            if five_o_poker_game.place_player_card(state.column_index):
                sounds.audio.play_sound("card_move")

        elif five_o_action == FIVE_O_ACTION_CHECK:
            if five_o_poker_game.player_check():
                sounds.audio.play_sound("poker_check")

        elif five_o_action == FIVE_O_ACTION_BET:
            if five_o_poker_game.player_bet():
                play_texas_holdem_chip_sound()

        elif five_o_action == FIVE_O_ACTION_CALL:
            if five_o_poker_game.player_call():
                play_texas_holdem_chip_sound()

        elif five_o_action == FIVE_O_ACTION_FOLD:
            if five_o_poker_game.player_fold():
                sounds.audio.play_sound("button_click")


def loop_event_blind_mans_bluff(event):
    """Old main-loop event branch for STATE_BLIND_MANS_BLUFF."""

    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):
        bluff_action = get_blind_mans_bluff_action(
            state.game_mouse_pos,
            blind_mans_bluff_game
        )

        if bluff_action == BLUFF_ACTION_RETURN:
            sounds.audio.play_sound("button_click")
            finish_blind_mans_bluff_session()

        elif bluff_action == BLUFF_ACTION_NEXT_HAND:
            if blind_mans_bluff_game.start_hand():
                sounds.audio.play_sound("card_shuffle")

        elif bluff_action == BLUFF_ACTION_CHECK:
            if blind_mans_bluff_game.player_check():
                sounds.audio.play_sound("poker_check")

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
                sounds.audio.play_sound("button_click")


def loop_event_crazy_eights(event):
    """Old main-loop event branch for STATE_CRAZY_EIGHTS."""

    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
    ):
        crazy_action = get_crazy_eights_action(
            state.menu_mouse_pos,
            crazy_eights_game
        )

        if crazy_action is not None:
            action_name, action_value = crazy_action

            if action_name == CRAZY_EIGHTS_ACTION_RETURN:
                sounds.audio.play_sound("button_click")
                if state.current_game_mode == "free":
                    finish_free_play_sandbox()
                    state.current_state = state_names.STATE_FREE_PLAY_SELECT
                else:
                    state.current_state = state_names.STATE_CAREER_EVENT_SELECT

            elif action_name == CRAZY_EIGHTS_ACTION_CONTINUE:
                sounds.audio.play_sound("button_click")
                claim_crazy_eights_result()
                if state.current_game_mode == "free":
                    finish_free_play_sandbox()
                    state.current_state = state_names.STATE_FREE_PLAY_SELECT
                else:
                    state.current_state = state_names.STATE_CAREER_EVENT_SELECT

            elif action_name == CRAZY_EIGHTS_ACTION_DRAW:
                if crazy_eights_game.draw_player_card():
                    sounds.audio.play_sound("card_draw")

            elif action_name == CRAZY_EIGHTS_ACTION_CARD:
                result = crazy_eights_game.play_player_card(
                    action_value
                )
                if result in ("played", "choose_suit"):
                    sounds.audio.play_sound("card_move")

            elif action_name == CRAZY_EIGHTS_ACTION_SUIT:
                if crazy_eights_game.choose_player_suit(
                        action_value
                ):
                    sounds.audio.play_sound("card_move")


def loop_event_bango(event):
    """Old main-loop event branch for STATE_BANGO."""

    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
    ):
        bango_action = get_bango_action(
            state.menu_mouse_pos,
            bango_game
        )

        if bango_action == BANGO_ACTION_RETURN:
            sounds.audio.play_sound("button_click")
            if state.current_game_mode == "free":
                finish_free_play_sandbox()
                state.current_state = state_names.STATE_FREE_PLAY_SELECT
            else:
                state.current_state = state_names.STATE_CAREER_EVENT_SELECT

        elif bango_action == BANGO_ACTION_CONTINUE:
            sounds.audio.play_sound("button_click")
            claim_bango_result()
            if state.current_game_mode == "free":
                finish_free_play_sandbox()
                state.current_state = state_names.STATE_FREE_PLAY_SELECT
            else:
                state.current_state = state_names.STATE_CAREER_EVENT_SELECT

        elif bango_action == BANGO_ACTION_CALL:
            if bango_game.call_next():
                sounds.audio.play_sound("card_draw")


def loop_event_score_four(event):
    """Old main-loop event branch for STATE_SCORE_FOUR."""

    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and score_four_game.rating_info_open:
        score_four_game.rating_info_open = False
        return
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.game_mouse_pos is not None:
        from solitaireplus.games.cards.score_four_ui import handle_rating_info_click
        if handle_rating_info_click(state.game_mouse_pos, score_four_game):
            sounds.audio.play_sound("button_click")
            return

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.game_mouse_pos is not None:
        from solitaireplus.games.cards.score_four_ui import LAYOUT_RECT, toggle_layout, play_control_sound
        if not score_four_game.difficulty_menu and LAYOUT_RECT.collidepoint(state.game_mouse_pos):
            toggle_layout(score_four_game)
            play_control_sound(sounds.audio, "select")
            return

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

                    state.menu_mouse_pos

            ):

                settle_score_four_session_result()

                sounds.audio.play_sound(

                    "button_click"

                )

                if state.current_game_mode == "free":
                    finish_free_play_sandbox()
                    state.current_state = state_names.STATE_FREE_PLAY_SELECT
                else:
                    state.current_state = state_names.STATE_CAREER_EVENT_SELECT

            return

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
                        state.menu_mouse_pos
                    )
            ):

                settle_score_four_session_result()

                sounds.audio.play_sound(
                    "button_click"
                )

                if state.current_game_mode == "free":
                    finish_free_play_sandbox()
                    state.current_state = state_names.STATE_FREE_PLAY_SELECT
                else:
                    state.current_state = state_names.STATE_CAREER_EVENT_SELECT

            return

        # ==========================================
        # Competitive round result input lock
        # ==========================================

        if (
                score_four_game.mode == "competitive"
                and score_four_game.round_complete
        ):
            from solitaireplus.games.cards.score_four_ui import ROUND_CONTINUE_RECT
            if state.game_mouse_pos is not None and ROUND_CONTINUE_RECT.collidepoint(state.game_mouse_pos):
                if score_four_game.continue_competitive_round():
                    sounds.audio.play_sound("button_click")
            return

        # ------------------------------------------
        # Number tiles
        # ------------------------------------------

        reset_rect = game_namespace().get("score_four_reset_rect")
        if reset_rect is not None and state.menu_mouse_pos is not None and reset_rect.collidepoint(state.menu_mouse_pos):
            if score_four_game.reset_current_puzzle(): play_control_sound(sounds.audio, "reset")
            return

        clicked_number = False

        for state.index, state.rect in enumerate(
                score_four_number_rects
        ):

            if state.rect.collidepoint(
                    state.menu_mouse_pos
            ):
                score_four_game.select_number(
                    state.index
                )

                if not score_four_game.round_complete:
                    play_control_sound(sounds.audio, "select")
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
                    state.rect
            ) in score_four_operator_rects.items():

                if state.rect.collidepoint(
                        state.menu_mouse_pos
                ):
                    score_four_game.select_operator(
                        operator_id
                    )

                    play_control_sound(sounds.audio, "operator")
                    clicked_operator = True
                    break

            if clicked_operator:
                pass

            elif (
                    score_four_game.solo_hint_available()
                    and score_four_hint_rect.collidepoint(
                state.menu_mouse_pos
            )
            ):

                if score_four_game.request_solo_hint():
                    play_control_sound(sounds.audio, "hint")

            # --------------------------------------
            # Undo
            # --------------------------------------

            elif score_four_undo_rect.collidepoint(
                    state.menu_mouse_pos
            ):

                score_four_game.undo()
                play_control_sound(sounds.audio, "undo")

            # --------------------------------------
            # Exit
            # --------------------------------------

            elif score_four_exit_rect.collidepoint(
                    state.menu_mouse_pos
            ):

                if state.current_game_mode == "free":
                    finish_free_play_sandbox()
                    state.current_state = state_names.STATE_FREE_PLAY_SELECT
                else:
                    state.current_state = state_names.STATE_CAREER_EVENT_SELECT


def loop_event_king_pong_opponent_select(event):
    """Old main-loop event branch for STATE_KING_PONG_OPPONENT_SELECT."""

    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        sounds.audio.play_sound("button_click")
        state.current_state = state_names.STATE_CAREER_EVENT_SELECT

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        opponent_clicked = False

        for opponent_index, state.rect in enumerate(king_pong_opponent_rects):
            if (
                    opponent_index < len(state.king_pong_opponent_choices)
                    and state.rect.collidepoint(state.menu_mouse_pos)
            ):
                state.king_pong_selected_opponent_index = opponent_index
                sounds.audio.play_sound("button_click")
                opponent_clicked = True
                break

        if not opponent_clicked:
            if king_pong_opponent_back_rect.collidepoint(state.menu_mouse_pos):
                sounds.audio.play_sound("button_click")
                state.current_state = state_names.STATE_CAREER_EVENT_SELECT

            elif king_pong_opponent_tokens_rect.collidepoint(state.menu_mouse_pos):
                sounds.audio.play_sound("button_click")
                open_arcade_token_exchange("king_pong")

            elif king_pong_opponent_play_rect.collidepoint(state.menu_mouse_pos):
                if get_selected_king_pong_choice() is None:
                    set_arcade_status_message("Choose a rival first.")
                elif int(state.arcade_state.get("tokens", 0)) < get_machine_cost("king_pong"):
                    set_arcade_status_message("Not enough tokens. Buy more to play.")
                    open_arcade_token_exchange("king_pong")
                else:
                    sounds.audio.play_sound("button_click")
                    start_king_pong_session()


def loop_event_battle_bosses_opponent_select(event):
    """Old main-loop event branch for STATE_BATTLE_BOSSES_OPPONENT_SELECT."""

    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        sounds.audio.play_sound("button_click")
        state.current_state = state_names.STATE_CAREER_EVENT_SELECT

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        choice_clicked = False
        for choice_index, state.rect in enumerate(battle_bosses_choice_rects):
            if (
                    choice_index < len(state.battle_bosses_opponent_choices)
                    and state.rect.collidepoint(state.menu_mouse_pos)
            ):
                state.battle_bosses_selected_choice_index = choice_index
                sounds.audio.play_sound("button_click")
                choice_clicked = True
                break

        if not choice_clicked:
            if battle_bosses_back_rect.collidepoint(state.menu_mouse_pos):
                sounds.audio.play_sound("button_click")
                state.current_state = state_names.STATE_CAREER_EVENT_SELECT
            elif battle_bosses_refresh_rect.collidepoint(state.menu_mouse_pos):
                sounds.audio.play_sound("button_click")
                open_battle_bosses_opponent_select(refresh=True)
                set_arcade_status_message("Battle Bosses rival squads rerolled.")
            elif battle_bosses_future_play_rect.collidepoint(state.menu_mouse_pos):
                if get_selected_battle_bosses_choice() is None:
                    set_arcade_status_message("Choose a rival squad first.")
                elif int(state.arcade_state.get("tokens", 0)) < get_machine_cost("battle_bosses"):
                    set_arcade_status_message("Not enough tokens. Buy more to enter the arena.")
                    open_arcade_token_exchange("battle_bosses")
                else:
                    sounds.audio.play_sound("button_click")
                    start_battle_bosses_session()


def loop_event_ace_invaders_difficulty_select(event):
    """Old main-loop event branch for STATE_ACE_INVADERS_DIFFICULTY_SELECT."""

    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        sounds.audio.play_sound("button_click")
        state.current_state = state_names.STATE_CAREER_EVENT_SELECT

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        difficulty_clicked = False
        difficulty_ids = list(ACE_INVADERS_DIFFICULTIES)

        for difficulty_index, state.rect in enumerate(ace_invaders_difficulty_rects):
            if (
                    difficulty_index < len(difficulty_ids)
                    and state.rect.collidepoint(state.menu_mouse_pos)
            ):
                state.ace_invaders_selected_difficulty_index = difficulty_index
                sounds.audio.play_sound("button_click")
                difficulty_clicked = True
                break

        if not difficulty_clicked:
            if ace_invaders_back_rect.collidepoint(state.menu_mouse_pos):
                sounds.audio.play_sound("button_click")
                state.current_state = state_names.STATE_CAREER_EVENT_SELECT

            elif ace_invaders_tokens_rect.collidepoint(state.menu_mouse_pos):
                sounds.audio.play_sound("button_click")
                open_arcade_token_exchange("ace_invaders")

            elif ace_invaders_play_rect.collidepoint(state.menu_mouse_pos):
                if get_selected_ace_invaders_difficulty() is None:
                    set_arcade_status_message("Choose an Ace Invaders difficulty first.")
                elif int(state.arcade_state.get("tokens", 0)) < get_machine_cost("ace_invaders"):
                    set_arcade_status_message("Not enough tokens. Buy more to play.")
                    open_arcade_token_exchange("ace_invaders")
                else:
                    sounds.audio.play_sound("button_click")
                    start_ace_invaders_session()


def loop_event_suit_snake_difficulty_select(event):
    """Old main-loop event branch for STATE_SUIT_SNAKE_DIFFICULTY_SELECT."""

    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        sounds.audio.play_sound("button_click")
        state.current_state = state_names.STATE_CAREER_EVENT_SELECT

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        setup_clicked = False
        mode_ids = list(SUIT_SNAKE_MODES)

        for mode_index, state.rect in enumerate(suit_snake_mode_rects):
            if (
                    mode_index < len(mode_ids)
                    and state.rect.collidepoint(state.menu_mouse_pos)
            ):
                state.suit_snake_selected_mode_index = mode_index
                sounds.audio.play_sound("button_click")
                setup_clicked = True
                break

        if not setup_clicked and suit_snake_step_movement_rect.collidepoint(state.menu_mouse_pos):
            state.suit_snake_selected_movement_style = "step"
            sounds.audio.play_sound("button_click")
            setup_clicked = True

        if not setup_clicked and suit_snake_smooth_movement_rect.collidepoint(state.menu_mouse_pos):
            state.suit_snake_selected_movement_style = "smooth"
            sounds.audio.play_sound("button_click")
            setup_clicked = True

        if not setup_clicked:
            if suit_snake_back_rect.collidepoint(state.menu_mouse_pos):
                sounds.audio.play_sound("button_click")
                state.current_state = state_names.STATE_CAREER_EVENT_SELECT

            elif suit_snake_tokens_rect.collidepoint(state.menu_mouse_pos):
                sounds.audio.play_sound("button_click")
                open_arcade_token_exchange("suit_snake")

            elif suit_snake_play_rect.collidepoint(state.menu_mouse_pos):
                if get_selected_suit_snake_mode() is None:
                    set_arcade_status_message("Choose a Suit Snake mode first.")
                elif int(state.arcade_state.get("tokens", 0)) < get_machine_cost("suit_snake"):
                    set_arcade_status_message("Not enough tokens. Buy more to play.")
                    open_arcade_token_exchange("suit_snake")
                else:
                    sounds.audio.play_sound("button_click")
                    start_suit_snake_session()


def loop_event_arcade_token_exchange(event):
    """Old main-loop event branch for STATE_ARCADE_TOKEN_EXCHANGE."""

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        if arcade_token_exchange_back_rect.collidepoint(state.menu_mouse_pos):
            sounds.audio.play_sound("button_click")
            if state.arcade_pending_launch_game_id == "king_pong":
                state.arcade_pending_launch_game_id = None
                state.current_state = state_names.STATE_KING_PONG_OPPONENT_SELECT
            elif state.arcade_pending_launch_game_id == "battle_bosses":
                state.arcade_pending_launch_game_id = None
                state.current_state = state_names.STATE_BATTLE_BOSSES_OPPONENT_SELECT
            elif state.arcade_pending_launch_game_id == "ace_invaders":
                state.arcade_pending_launch_game_id = None
                state.current_state = state_names.STATE_ACE_INVADERS_DIFFICULTY_SELECT
            elif state.arcade_pending_launch_game_id == "suit_snake":
                state.arcade_pending_launch_game_id = None
                state.current_state = state_names.STATE_SUIT_SNAKE_DIFFICULTY_SELECT
            else:
                state.current_state = state_names.STATE_CAREER_EVENT_SELECT
        elif arcade_token_exchange_continue_rect.collidepoint(state.menu_mouse_pos):
            sounds.audio.play_sound("button_click")
            if state.arcade_pending_launch_game_id == "king_pong":
                if int(state.arcade_state.get("tokens", 0)) >= get_machine_cost("king_pong"):
                    start_king_pong_session()
                else:
                    set_arcade_status_message("Buy enough tokens to play King Pong.")
            elif state.arcade_pending_launch_game_id == "battle_bosses":
                if int(state.arcade_state.get("tokens", 0)) >= get_machine_cost("battle_bosses"):
                    start_battle_bosses_session()
                else:
                    set_arcade_status_message("Buy enough tokens to play Battle Bosses.")
            elif state.arcade_pending_launch_game_id == "ace_invaders":
                if int(state.arcade_state.get("tokens", 0)) >= get_machine_cost("ace_invaders"):
                    start_ace_invaders_session()
                else:
                    set_arcade_status_message("Buy enough tokens to play Ace Invaders.")
            elif state.arcade_pending_launch_game_id == "suit_snake":
                if int(state.arcade_state.get("tokens", 0)) >= get_machine_cost("suit_snake"):
                    start_suit_snake_session()
                else:
                    set_arcade_status_message("Buy enough tokens to play Suit Snake.")
            else:
                state.current_state = state_names.STATE_CAREER_EVENT_SELECT
        else:
            for state.package_index, state.rect in arcade_token_package_rects.items():
                if state.rect.collidepoint(state.menu_mouse_pos):
                    package = ARCADE_TOKEN_PACKAGES[state.package_index]
                    state.success, new_state, new_cash, message = buy_token_package(state.arcade_state, state.career_cash, package['id'])
                    state.arcade_state = new_state
                    if state.success:
                        state.career_cash = new_cash
                        career_saving.auto_save_career()
                    set_arcade_status_message(message)
                    sounds.audio.play_sound("button_click")
                    break


def loop_event_arcade_prize_counter(event):
    """Old main-loop event branch for STATE_ARCADE_PRIZE_COUNTER."""

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        page_count = max(1, math.ceil(len(ARCADE_PRIZE_CATALOG) / ARCADE_PRIZES_PER_PAGE))
        if arcade_prize_back_rect.collidepoint(state.menu_mouse_pos):
            sounds.audio.play_sound("button_click")
            state.current_state = state_names.STATE_CAREER_EVENT_SELECT
        elif arcade_prize_trophy_room_rect.collidepoint(state.menu_mouse_pos):
            sounds.audio.play_sound("button_click")
            state.current_state = state_names.STATE_ARCADE_TROPHY_ROOM
        elif arcade_prize_buy_rect.collidepoint(state.menu_mouse_pos):
            prize = ARCADE_PRIZE_CATALOG[state.arcade_selected_prize_index]
            _success, message, _prize = redeem_arcade_prize_for_career(prize['id'])
            set_arcade_status_message(message)
            sounds.audio.play_sound("button_click")
        elif arcade_prize_prev_rect.collidepoint(state.menu_mouse_pos) and state.arcade_prize_page > 0:
            state.arcade_prize_page -= 1
            state.arcade_selected_prize_index = state.arcade_prize_page * ARCADE_PRIZES_PER_PAGE
            sounds.audio.play_sound("button_click")
        elif arcade_prize_next_rect.collidepoint(state.menu_mouse_pos) and state.arcade_prize_page + 1 < page_count:
            state.arcade_prize_page += 1
            state.arcade_selected_prize_index = state.arcade_prize_page * ARCADE_PRIZES_PER_PAGE
            sounds.audio.play_sound("button_click")
        else:
            page_start = state.arcade_prize_page * ARCADE_PRIZES_PER_PAGE
            for prize_slot, state.rect in arcade_prize_card_rects.items():
                prize_index = page_start + prize_slot
                if prize_index < len(ARCADE_PRIZE_CATALOG) and state.rect.collidepoint(state.menu_mouse_pos):
                    state.arcade_selected_prize_index = prize_index
                    sounds.audio.play_sound("button_click")
                    break


def loop_event_arcade_trophy_room(event):
    """Old main-loop event branch for STATE_ARCADE_TROPHY_ROOM."""

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        if arcade_trophy_room_back_rect.collidepoint(state.menu_mouse_pos):
            sounds.audio.play_sound("button_click")
            state.current_state = state_names.STATE_ARCADE_PRIZE_COUNTER


def loop_event_king_pong(event):
    """Old main-loop event branch for STATE_KING_PONG."""

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

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        if king_pong_return_rect.collidepoint(state.menu_mouse_pos):
            sounds.audio.play_sound("button_click")
            if not king_pong_game.finished:
                king_pong_game.forfeit()
            finish_king_pong_session()


def loop_event_battle_bosses(event):
    """Old main-loop event branch for STATE_BATTLE_BOSSES."""

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

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        if battle_bosses_quit_rect.collidepoint(state.menu_mouse_pos):
            sounds.audio.play_sound("button_click")
            if not battle_bosses_game.finished:
                battle_bosses_game.forfeit()
            finish_battle_bosses_session()


def loop_event_ace_invaders(event):
    """Old main-loop event branch for STATE_ACE_INVADERS."""

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            if not ace_invaders_game.finished:
                ace_invaders_game.forfeit()
            finish_ace_invaders_session()
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if ace_invaders_game.finished:
                finish_ace_invaders_session()
        elif event.key == pygame.K_r and ace_invaders_game.finished:
            start_ace_invaders_session()

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        if ace_invaders_quit_rect.collidepoint(state.menu_mouse_pos):
            sounds.audio.play_sound("button_click")
            if not ace_invaders_game.finished:
                ace_invaders_game.forfeit()
            finish_ace_invaders_session()


def loop_event_suit_snake(event):
    """Old main-loop event branch for STATE_SUIT_SNAKE."""

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            if not suit_snake_game.finished:
                suit_snake_game.forfeit()
            finish_suit_snake_session()
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if suit_snake_game.finished:
                finish_suit_snake_session()
        elif event.key == pygame.K_r and suit_snake_game.finished:
            start_suit_snake_session()
        elif event.key in (pygame.K_w, pygame.K_UP):
            suit_snake_game.queue_direction("up")
        elif event.key in (pygame.K_s, pygame.K_DOWN):
            suit_snake_game.queue_direction("down")
        elif event.key in (pygame.K_a, pygame.K_LEFT):
            suit_snake_game.queue_direction("left")
        elif event.key in (pygame.K_d, pygame.K_RIGHT):
            suit_snake_game.queue_direction("right")

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        if suit_snake_quit_rect.collidepoint(state.menu_mouse_pos):
            sounds.audio.play_sound("button_click")
            if not suit_snake_game.finished:
                suit_snake_game.forfeit()
            finish_suit_snake_session()


def loop_event_dead_mans_hand(event):
    """Old main-loop event branch for STATE_DEAD_MANS_HAND."""

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            exit_dead_mans_hand()
        elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
            dead_mans_hand_game.switch_weapon_by_slot(event.key - pygame.K_0)
        elif event.key == pygame.K_r:
            if dead_mans_hand_game.game_over or dead_mans_hand_game.prototype_complete:
                dead_mans_hand_game.start_run()
                dead_mans_hand_game.capture_mouse()
            else:
                dead_mans_hand_game.start_reload()
    elif event.type == pygame.MOUSEMOTION:
        dead_mans_hand_game.handle_mouse_motion(event.rel[0])
    elif event.type == pygame.MOUSEWHEEL:
        dead_mans_hand_game.cycle_weapon(1 if event.y < 0 else -1)
    elif event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1:
            dead_mans_hand_game.set_trigger_held(True)
            dead_mans_hand_game.fire()
        elif event.button == 3:
            dead_mans_hand_game.set_aiming(True)
        elif event.button == 4:
            dead_mans_hand_game.cycle_weapon(-1)
        elif event.button == 5:
            dead_mans_hand_game.cycle_weapon(1)
    elif event.type == pygame.MOUSEBUTTONUP:
        if event.button == 1:
            dead_mans_hand_game.set_trigger_held(False)
        elif event.button == 3:
            dead_mans_hand_game.set_aiming(False)


def loop_draw_cryptid_creatures():
    """Old draw-chain branch for STATE_CRYPTID_CREATURES."""
    cryptid_screen.sfx_volume = sounds.audio.sfx_volume
    cryptid_screen.update(pygame.time.get_ticks())
    cryptid_screen.draw(window.game_surface, state.menu_mouse_pos)


def loop_draw_king_pong_opponent_select():
    """Old draw-chain branch for STATE_KING_PONG_OPPONENT_SELECT."""

    draw_king_pong_opponent_select()


def loop_draw_battle_bosses_opponent_select():
    """Old draw-chain branch for STATE_BATTLE_BOSSES_OPPONENT_SELECT."""

    draw_battle_bosses_opponent_select()


def loop_draw_ace_invaders_difficulty_select():
    """Old draw-chain branch for STATE_ACE_INVADERS_DIFFICULTY_SELECT."""

    draw_ace_invaders_difficulty_select()


def loop_draw_suit_snake_difficulty_select():
    """Old draw-chain branch for STATE_SUIT_SNAKE_DIFFICULTY_SELECT."""

    draw_suit_snake_difficulty_select()


def loop_draw_arcade_token_exchange():
    """Old draw-chain branch for STATE_ARCADE_TOKEN_EXCHANGE."""

    draw_arcade_token_exchange()


def loop_draw_arcade_prize_counter():
    """Old draw-chain branch for STATE_ARCADE_PRIZE_COUNTER."""

    draw_arcade_prize_counter()


def loop_draw_arcade_trophy_room():
    """Old draw-chain branch for STATE_ARCADE_TROPHY_ROOM."""

    draw_arcade_trophy_room()


def loop_draw_crazy_eights():
    """Old draw-chain branch for STATE_CRAZY_EIGHTS."""

    crazy_eights_game.update()

    draw_crazy_eights(
        window.game_surface,
        state.game_mouse_pos,
        crazy_eights_game,
        game.card_fronts,
        game.get_card_back_surface(),
        portrait_loader=get_npc_portrait_surface,
    )


def loop_draw_bango():
    """Old draw-chain branch for STATE_BANGO."""

    draw_bango(
        window.game_surface,
        state.game_mouse_pos,
        bango_game,
        game.card_fronts,
        game.get_card_back_surface(),
        portrait_loader=get_npc_portrait_surface,
    )


def loop_draw_score_four_mode_select():
    """Old draw-chain branch for STATE_SCORE_FOUR_MODE_SELECT."""

    draw_score_four_mode_select()


def loop_draw_score_four():
    """Old draw-chain branch for STATE_SCORE_FOUR."""

    score_four_game.update()

    draw_score_four()


def loop_draw_score_four_opponent_select():
    """Old draw-chain branch for STATE_SCORE_FOUR_OPPONENT_SELECT."""

    draw_score_four_opponent_select()


def loop_draw_blackjack():
    """Old draw-chain branch for STATE_BLACKJACK."""

    blackjack_game.update()

    settle_blackjack_round()

    draw_blackjack()


def loop_draw_roulette():
    """Old draw-chain branch for STATE_ROULETTE."""

    roulette_game.update()

    settle_roulette_round()

    draw_roulette(
        window.game_surface,
        state.game_mouse_pos,
        roulette_game,
        RED_NUMBERS,
        panels.draw_submenu_background,
        panels.draw_submenu_title,
        buttons.draw_menu_button,
        fonts.options_title_font,
        fonts.option_label_font,
        fonts.difficulty_detail_font,
        state.career_cash,
        state.roulette_session_net,
        state.roulette_chip_value
    )


def loop_draw_horse_races():
    """Old draw-chain branch for STATE_HORSE_RACES."""

    horse_previous_stage = horse_races_game.stage
    horse_races_game.update(pygame.time.get_ticks())
    if (
            horse_previous_stage == "racing"
            and horse_races_game.stage == "results"
    ):
        stop_horse_race_music(600)
    settle_horse_race_result()

    draw_horse_races(
        window.game_surface,
        state.game_mouse_pos,
        horse_races_game,
    )


def loop_draw_king_pong():
    """Old draw-chain branch for STATE_KING_PONG."""

    king_pong_game.update(1.0 / 60.0, pygame.key.get_pressed())
    while True:
        point_event = king_pong_game.pop_point_event()
        if point_event is None:
            break
        sounds.audio.play_sound(
            "five_o_column_win"
            if point_event.get("player_scored")
            else "five_o_column_loss"
        )
    if king_pong_game.finished:
        claim_king_pong_result()
    draw_king_pong_screen()


def loop_draw_battle_bosses():
    """Old draw-chain branch for STATE_BATTLE_BOSSES."""

    battle_bosses_game.update(1.0 / 60.0, pygame.key.get_pressed())
    for battle_sound_event in battle_bosses_game.pop_sound_events():
        sounds.audio.play_sound(battle_sound_event)
    if battle_bosses_game.finished:
        claim_battle_bosses_result()
    draw_battle_bosses_screen()


def loop_draw_ace_invaders():
    """Old draw-chain branch for STATE_ACE_INVADERS."""

    ace_invaders_game.update(1.0 / 60.0, pygame.key.get_pressed())
    for ace_sound_event in ace_invaders_game.pop_sound_events():
        sounds.audio.play_sound(ace_sound_event)
    if ace_invaders_game.finished:
        claim_ace_invaders_result()
    draw_ace_invaders_screen()


def loop_draw_suit_snake():
    """Old draw-chain branch for STATE_SUIT_SNAKE."""

    suit_snake_game.update(1.0 / 60.0, pygame.key.get_pressed())
    for suit_snake_sound_event in suit_snake_game.pop_sound_events():
        sounds.audio.play_sound(suit_snake_sound_event)
    if suit_snake_game.finished:
        claim_suit_snake_result()
    draw_suit_snake_screen()


def loop_draw_dead_mans_hand():
    """Old draw-chain branch for STATE_DEAD_MANS_HAND."""

    dead_mans_hand_dt = min(0.05, max(0.0, window.clock.get_time() / 1000.0))
    dead_mans_hand_game.update(dead_mans_hand_dt, pygame.key.get_pressed())
    for dmh_sound_event in dead_mans_hand_game.pop_sound_events():
        sound_name = {
            "pistol_shot": "dead_mans_hand_pistol_shot",
            "pistol_reload": "dead_mans_hand_pistol_reload",
            "kar98k_shot": "dead_mans_hand_kar98k_shot",
            "kar98k_bolt": "dead_mans_hand_kar98k_bolt",
            "kar98k_reload": "dead_mans_hand_kar98k_reload",
            "thompson_shot": "dead_mans_hand_thompson_shot",
            "thompson_reload": "dead_mans_hand_thompson_reload",
            "scar20_shot": "dead_mans_hand_scar20_shot",
            "scar20_reload": "dead_mans_hand_scar20_reload",
            "weapon_pickup": "dead_mans_hand_weapon_pickup",
            "enemy_hit": "dead_mans_hand_enemy_hit",
            "enemy_down": "dead_mans_hand_enemy_down",
            "player_hit": "dead_mans_hand_player_hit",
            "player_down": "dead_mans_hand_player_down",
        }.get(dmh_sound_event)
        if sound_name:
            sounds.audio.play_sound(sound_name)
    dead_mans_hand_game.draw(window.game_surface)


def loop_draw_faro():
    """Old draw-chain branch for STATE_FARO."""

    draw_faro(
        window.game_surface,
        state.game_mouse_pos,
        faro_game,
        state.faro_chip_value,
        panels.draw_submenu_background,
        panels.draw_submenu_title,
        buttons.draw_menu_button,
        fonts.options_title_font,
        fonts.option_label_font,
        fonts.difficulty_detail_font,
        card_fronts=game.card_fronts,
        card_back_surface=game.get_card_back_surface(),
    )


def loop_draw_five_o_poker():
    """Old draw-chain branch for STATE_FIVE_O_POKER."""

    five_o_poker_game.update()

    draw_five_o_poker(
        window.game_surface,
        state.game_mouse_pos,
        five_o_poker_game,
        state.player_name,
        panels.draw_submenu_background,
        fonts.options_title_font,
        fonts.option_label_font,
        fonts.difficulty_detail_font,
        card_fronts=game.card_fronts,
        card_back_surface=game.get_card_back_surface(),
    )


def loop_draw_blind_mans_bluff():
    """Old draw-chain branch for STATE_BLIND_MANS_BLUFF."""

    update_bluff_presentation(blind_mans_bluff_game, sounds.audio.play_sound)
    draw_blind_mans_bluff(
        window.game_surface,
        state.game_mouse_pos,
        blind_mans_bluff_game,
        state.player_name,
        panels.draw_submenu_background,
        fonts.options_title_font,
        fonts.option_label_font,
        fonts.difficulty_detail_font,
        card_fronts=game.card_fronts,
        card_back_surface=game.get_card_back_surface(),
    )


def loop_draw_blackjack_bet():
    """Old draw-chain branch for STATE_BLACKJACK_BET."""

    draw_blackjack_bet()


def loop_draw_seven_card_stud_buy_in():
    """Old draw-chain branch for STATE_SEVEN_CARD_STUD_BUY_IN."""
    draw_seven_card_stud_buy_in(
        window.game_surface,
        state.game_mouse_pos,
        state.career_cash,
        panels.draw_submenu_background,
        minimum_buy_in=(
            SEVEN_CARD_STUD_MIN_BUY_IN
        )
    )


def loop_draw_seven_card_stud():
    """Old draw-chain branch for STATE_SEVEN_CARD_STUD."""
    seven_card_stud_next_hand_seconds = None

    if (
            seven_card_stud_game.hand_complete
            and state.seven_card_stud_next_hand_at > 0
    ):
        remaining_ms = max(
            0,
            state.seven_card_stud_next_hand_at
            - pygame.time.get_ticks()
        )

        seven_card_stud_next_hand_seconds = (
            remaining_ms + 999
        ) // 1000

    draw_seven_card_stud(
        window.game_surface,
        state.game_mouse_pos,
        seven_card_stud_game,
        game.card_fronts,
        game.get_card_back_surface(),
        panels.draw_submenu_background,
        draw_npc_portrait,
        state.player_name,
        game.felt_surface,
        next_hand_seconds=(
            seven_card_stud_next_hand_seconds
        )
    )

    draw_holdem_options_overlay(
        window.game_surface,
        state.game_mouse_pos
    )


def loop_draw_five_card_draw_buy_in():
    """Old draw-chain branch for STATE_FIVE_CARD_DRAW_BUY_IN."""

    draw_five_card_draw_buy_in(
        window.game_surface,
        state.game_mouse_pos,
        state.career_cash,
        panels.draw_submenu_background,
        minimum_buy_in=(
            FIVE_CARD_DRAW_MIN_BUY_IN
        )
    )


def loop_draw_five_card_draw():
    """Old draw-chain branch for STATE_FIVE_CARD_DRAW."""

    five_card_draw_next_hand_seconds = None

    if (
            five_card_draw_game.hand_complete
            and state.five_card_draw_next_hand_at > 0
    ):
        remaining_ms = max(
            0,
            state.five_card_draw_next_hand_at
            - pygame.time.get_ticks()
        )

        five_card_draw_next_hand_seconds = (
            remaining_ms + 999
        ) // 1000

    draw_five_card_draw(
        window.game_surface,
        state.game_mouse_pos,
        five_card_draw_game,
        game.card_fronts,
        game.get_card_back_surface(),
        panels.draw_submenu_background,
        draw_npc_portrait,
        state.player_name,
        game.felt_surface,
        next_hand_seconds=(
            five_card_draw_next_hand_seconds
        )
    )

    draw_holdem_options_overlay(
        window.game_surface,
        state.game_mouse_pos
    )


def loop_draw_texas_holdem_buy_in():
    """Old draw-chain branch for STATE_TEXAS_HOLDEM_BUY_IN."""

    draw_texas_holdem_buy_in(
        window.game_surface,
        state.game_mouse_pos,
        state.career_cash,
        panels.draw_submenu_background,
        minimum_buy_in=(
            TEXAS_HOLDEM_MIN_BUY_IN
        )
    )


def loop_draw_texas_holdem():
    """Old draw-chain branch for STATE_TEXAS_HOLDEM."""

    texas_holdem_next_hand_seconds = None

    if (
            texas_holdem_game.hand_complete
            and state.texas_holdem_next_hand_at > 0
    ):
        remaining_ms = max(
            0,
            state.texas_holdem_next_hand_at
            - pygame.time.get_ticks()
        )

        texas_holdem_next_hand_seconds = (
            remaining_ms + 999
        ) // 1000

    draw_texas_holdem(
        window.game_surface,
        state.game_mouse_pos,
        texas_holdem_game,
        game.card_fronts,
        game.get_card_back_surface(),
        panels.draw_submenu_background,
        panels.draw_submenu_title,
        buttons.draw_menu_button,
        draw_npc_portrait,
        fonts.options_title_font,
        fonts.option_label_font,
        fonts.difficulty_detail_font,
        state.player_name,
        game.felt_surface,
        next_hand_seconds=(
            texas_holdem_next_hand_seconds
        )
    )


def loop_late_texas_holdem():
    """Old timed-NPC branch for STATE_TEXAS_HOLDEM (runs after drawing, as before)."""

    now = pygame.time.get_ticks()
    from solitaireplus.games.poker.turn_flow import repair_betting_turn
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
            and state.texas_holdem_next_npc_action_at == 0
            and not texas_holdem_game.is_betting_round_complete()
    ):
        state.texas_holdem_next_npc_action_at = (
                now
                + get_holdem_npc_delay()
        )

    # ==================================================
    # Cancel pending auto-deal if user turns it off
    # ==================================================

    if not is_holdem_auto_deal_enabled():
        state.texas_holdem_next_hand_at = 0

    # ==================================================
    # Delayed winning-hand sound
    # ==================================================

    if (
            state.texas_holdem_hand_win_sound_at > 0
            and now
            >= state.texas_holdem_hand_win_sound_at
    ):
        sounds.audio.play_sound(
            "poker_hand_win"
        )

        state.texas_holdem_hand_win_sound_at = 0

    process_texas_holdem_showdown()
    if getattr(texas_holdem_game, "recap_open", False):
        state.texas_holdem_next_hand_at = 0
        state.texas_holdem_session_end_at = 0

    # ==================================================
    # Start next-hand countdown after showdown
    # ==================================================

    if (
            texas_holdem_game.hand_complete
            and texas_holdem_game.current_stage == "showdown"
            and state.texas_holdem_next_hand_at == 0
            and state.texas_holdem_session_end_at == 0
            and texas_holdem_game.player_stack > 0
            and not texas_holdem_game.player_busted
            and not texas_holdem_game.all_npcs_busted()
            and is_holdem_auto_deal_enabled()
            and not getattr(texas_holdem_game, "recap_open", False)
    ):
        state.texas_holdem_next_hand_at = (
                now
                + get_holdem_next_hand_delay()
        )

    # ==================================================
    # Run one scheduled NPC action
    # ==================================================

    if (
            state.texas_holdem_next_npc_action_at > 0
            and now >= state.texas_holdem_next_npc_action_at
            and not texas_holdem_game.hand_complete
    ):

        state.texas_holdem_next_npc_action_at = 0

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
            state.texas_holdem_next_npc_action_at = (
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
            and state.texas_holdem_round_advance_at == 0
    ):
        state.texas_holdem_round_advance_at = (
                now
                + get_holdem_street_delay()
        )

        # Nobody is actively taking a turn now.
        texas_holdem_game.current_actor = -1

    # ==================================================
    # Advance to flop / turn / river / showdown
    # ==================================================

    if (
            state.texas_holdem_round_advance_at > 0
            and now >= state.texas_holdem_round_advance_at
    ):

        state.texas_holdem_round_advance_at = 0

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
            state.texas_holdem_next_hand_at > 0
            and now >= state.texas_holdem_next_hand_at
    ):
        state.texas_holdem_next_hand_at = 0

        texas_holdem_game.start_hand()

    # ==================================================
    # Poker session finished
    # ==================================================

    if (
            state.texas_holdem_session_end_at > 0
            and now >= state.texas_holdem_session_end_at
    ):
        state.texas_holdem_session_end_at = 0

        state.texas_holdem_next_hand_at = 0
        state.texas_holdem_next_npc_action_at = 0
        state.texas_holdem_round_advance_at = 0

        finish_texas_holdem_session()


def loop_late_seven_card_stud():
    """Old timed-NPC branch for STATE_SEVEN_CARD_STUD (runs after drawing, as before)."""

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
            and state.seven_card_stud_next_npc_action_at == 0
            and not seven_card_stud_game.is_betting_round_complete()
    ):
        state.seven_card_stud_next_npc_action_at = (
                now
                + get_holdem_npc_delay()
        )

    # ==================================================
    # Delayed player win sound
    # ==================================================

    if (
            state.seven_card_stud_hand_win_sound_at > 0
            and now >= state.seven_card_stud_hand_win_sound_at
    ):
        sounds.audio.play_sound(
            "poker_hand_win"
        )

        state.seven_card_stud_hand_win_sound_at = 0

    process_seven_card_stud_showdown()

    # ==================================================
    # Start next-hand countdown
    # ==================================================

    if (
            seven_card_stud_game.hand_complete
            and seven_card_stud_game.current_stage == "showdown"
            and state.seven_card_stud_next_hand_at == 0
            and state.seven_card_stud_session_end_at == 0
            and is_holdem_auto_deal_enabled()
            and seven_card_stud_game.player_stack > 0
            and not seven_card_stud_game.player_busted
            and not seven_card_stud_game.all_npcs_busted()
    ):
        state.seven_card_stud_next_hand_at = (
                now
                + get_holdem_next_hand_delay()
        )

    # ==================================================
    # Run one NPC betting action
    # ==================================================

    if (
            state.seven_card_stud_next_npc_action_at > 0
            and now >= state.seven_card_stud_next_npc_action_at
            and not seven_card_stud_game.hand_complete
    ):
        state.seven_card_stud_next_npc_action_at = 0

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
            state.seven_card_stud_next_npc_action_at = (
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
            and state.seven_card_stud_round_advance_at == 0
    ):
        state.seven_card_stud_round_advance_at = (
                now
                + get_holdem_street_delay()
        )

        seven_card_stud_game.current_actor = -1

    # ==================================================
    # Advance Third -> Fourth -> ... -> Showdown
    # ==================================================

    if (
            state.seven_card_stud_round_advance_at > 0
            and now >= state.seven_card_stud_round_advance_at
    ):
        state.seven_card_stud_round_advance_at = 0

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
            sounds.audio.play_sound(
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
            state.seven_card_stud_next_hand_at > 0
            and now >= state.seven_card_stud_next_hand_at
    ):
        state.seven_card_stud_next_hand_at = 0

        if seven_card_stud_game.start_hand():
            sounds.audio.play_sound(
                "card_draw"
            )

    # ==================================================
    # Session finished
    # ==================================================

    if (
            state.seven_card_stud_session_end_at > 0
            and now >= state.seven_card_stud_session_end_at
    ):
        state.seven_card_stud_session_end_at = 0

        finish_seven_card_stud_session()


def loop_late_five_card_draw():
    """Old timed-NPC branch for STATE_FIVE_CARD_DRAW (runs after drawing, as before)."""

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
            and state.five_card_draw_next_npc_action_at == 0
            and not five_card_draw_game.is_betting_round_complete()
    ):
        state.five_card_draw_next_npc_action_at = (
                now
                + get_holdem_npc_delay()
        )

    # ==================================================
    # Delayed hand-win sound
    # ==================================================

    if (
            state.five_card_draw_hand_win_sound_at > 0
            and now >= state.five_card_draw_hand_win_sound_at
    ):
        sounds.audio.play_sound(
            "poker_hand_win"
        )

        state.five_card_draw_hand_win_sound_at = 0

    process_five_card_draw_showdown()

    # ==================================================
    # Start next-hand countdown
    # ==================================================

    if (
            five_card_draw_game.hand_complete
            and five_card_draw_game.current_stage == "showdown"
            and state.five_card_draw_next_hand_at == 0
            and state.five_card_draw_session_end_at == 0
            and is_holdem_auto_deal_enabled()
            and five_card_draw_game.player_stack > 0
            and not five_card_draw_game.player_busted
            and not five_card_draw_game.all_npcs_busted()
    ):
        state.five_card_draw_next_hand_at = (
                now
                + get_holdem_next_hand_delay()
        )

    # ==================================================
    # Run one NPC betting action
    # ==================================================

    if (
            state.five_card_draw_next_npc_action_at > 0
            and now >= state.five_card_draw_next_npc_action_at
            and not five_card_draw_game.hand_complete
    ):
        state.five_card_draw_next_npc_action_at = 0

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
            state.five_card_draw_next_npc_action_at = (
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
            and state.five_card_draw_round_advance_at == 0
    ):
        state.five_card_draw_round_advance_at = (
                now
                + get_holdem_street_delay()
        )

        five_card_draw_game.current_actor = -1

    # ==================================================
    # First betting -> draw / final betting -> showdown
    # ==================================================

    if (
            state.five_card_draw_round_advance_at > 0
            and now >= state.five_card_draw_round_advance_at
    ):
        state.five_card_draw_round_advance_at = 0

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
            sounds.audio.play_sound(
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
            state.five_card_draw_next_hand_at > 0
            and now >= state.five_card_draw_next_hand_at
    ):
        state.five_card_draw_next_hand_at = 0

        if five_card_draw_game.start_hand():
            sounds.audio.play_sound(
                "card_draw"
            )

        clear_five_card_draw_selection()

    # ==================================================
    # Session finished
    # ==================================================

    if (
            state.five_card_draw_session_end_at > 0
            and now >= state.five_card_draw_session_end_at
    ):
        state.five_card_draw_session_end_at = 0

        finish_five_card_draw_session()


def loop_draw_debug_poker_npc_select():
    """Old draw-chain branch for STATE_DEBUG_POKER_NPC_SELECT."""

    debug_game_labels = {
        "texas_holdem": "Texas Hold'em",
        "five_card_draw": "Five-Card Draw",
        "seven_card_stud": "Seven-Card Stud",
    }
    draw_debug_poker_npc_select(
        window.game_surface,
        state.game_mouse_pos,
        debug_game_labels.get(state.debug_poker_select_game_id, "Poker"),
        NPCS,
        state.debug_poker_selected_ids,
        portrait_loader=get_npc_portrait_surface,
        can_start=(state.career_cash >= 100),
        cash=state.career_cash,
    )


def loop_draw_debug_menu():
    """Old draw-chain branch for STATE_DEBUG_MENU."""

    draw_debug_menu(

        window.game_surface,

        state.game_mouse_pos,

        panels.draw_submenu_background,

        panels.draw_submenu_title,

        buttons.draw_menu_button,

        fonts.option_label_font,

        fonts.difficulty_detail_font

    )


def loop_post_event_updates():
    """Old per-frame updates between the event loop and drawing."""
    screen.update_solitaire_round()

    if (
            state.current_state != state_names.STATE_HORSE_RACES
            and state.horse_race_music_channel is not None
    ):
        stop_horse_race_music(300)

    # Non-Solitaire games award XP too. If that XP crossed a level threshold,
    # wait until the player has safely returned to a hub/selection screen before
    # presenting the queued level-up cards.
    if (
            state.level_up_queue
            and state.current_level_up_data is None
            and state.current_state in (
                state_names.STATE_MENU,
                state_names.STATE_CAREER_HUB,
                state_names.STATE_CAREER_EVENT_SELECT,
                state_names.STATE_FREE_PLAY_SELECT,
            )
    ):
        state.post_round_return_state = state.current_state
        level_up.advance_level_up_screen()
