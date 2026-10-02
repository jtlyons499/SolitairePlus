import os
import sys
import time
import copy

from career_hub_controls import CareerHubControls

import random

import math
import pygame
import json


from audio import AudioManager
from game import Game, BASE_WIDTH, BASE_HEIGHT

from score_four import ScoreFourGame
from blackjack import BlackjackGame

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
    get_random_npc,
    get_random_blackjack_dealer,
    get_score_four_opponent_choices,
    get_npcs_missing_portraits,
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

from debug_menu import (
    draw_debug_menu,
    get_debug_action,
    ACTION_CAREER_HUB,
    ACTION_CASUAL_CARDS,
    ACTION_POKER_NIGHT,
    ACTION_CASINO_NIGHT,
    ACTION_ADVANCE_CAREER_DAY,
    ACTION_NEW_CAREER_MONTH,
    ACTION_CHALLENGE_DRAW_3,
    ACTION_CHALLENGE_NO_UNDO,
    ACTION_CHALLENGE_NO_HINTS,
    ACTION_CHALLENGE_ALL_OR_NOTHING,
    ACTION_SCORE_FOUR_SOLO,
    ACTION_SCORE_FOUR_COMPETITIVE,
    ACTION_BLACKJACK,
    ACTION_ROULETTE,
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

if getattr(sys, "frozen", False):
    # Running as packaged EXE
    os.chdir(
        os.path.dirname(
            sys.executable
        )
    )
else:
    # Running from Python / PyCharm
    os.chdir(
        os.path.dirname(
            os.path.abspath(__file__)
        )
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


# ========================================================================================
# GAME STATES // CONSTANTS // CAREER CONSTANTS // CAREER STATES // BUILD VERSION
# ========================================================================================

BUILD_VERSION = "0.0.2-dantest"

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
STATE_HOW_TO_PLAY = "how_to_play"

# MINIGAME STATE VARIABLE
STATE_SCORE_FOUR = "score_four"
STATE_SCORE_FOUR_MODE_SELECT = "score_four_mode_select"

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

STATE_ROULETTE = "roulette"

STATE_CAREER_EVENT_SUMMARY = (
    "career_event_summary"
)

STATE_CAREER_HUB = "career_hub"
STATE_CAREER_JOBS = "career_jobs"
STATE_CAREER_REAL_ESTATE = "career_real_estate"
STATE_CAREER_LEADERBOARDS = "career_leaderboards"
STATE_CAREER_NEWS = "career_news"
STATE_CAREER_NEWS = "career_news"
STATE_CAREER_EVENT = "career_event"
STATE_CAREER_EVENT_SELECT = "career_event_select"

STATE_DEBUG_MENU = "debug_menu"

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
            "Options can use random deals or Verified Solvable deals with a known winning line.",
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
            "Your rating increases logarithmically, gains slow down as rating rises. Rating also determines your position on the international leaderboard.",
            "",
            "Random events, news stories, and changing rival ratings make each career save different. Reach #1 to conquer the Solitaire world.",
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
    "score_four": False,
    "roulette": False,
    "career": False,
}

help_category_rects = {}
help_page_rects = {}

help_current_page = (
    "solitaire_basics"
)

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

    "score_four": {
        "name": "Score-Four",
        "pages": [
            ("score_four_basics", "Basics"),
            ("score_four_strategy", "Strategy"),
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

    "career": {
        "name": "Career",
        "pages": [
            ("career_basics", "Basics"),
            ("career_progression", "Progression"),
            ("career_money", "Money"),
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

def build_career_event_summary():

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

        career_event_summary_title = (
            "CASINO NIGHT COMPLETE"
        )

        # ==========================================
        # Blackjack
        # ==========================================

        if blackjack_session_net > 0:

            blackjack_text = (
                f"Blackjack: +${blackjack_session_net:,}"
            )

        elif blackjack_session_net < 0:

            blackjack_text = (
                f"Blackjack: -${abs(blackjack_session_net):,}"
            )

        else:

            blackjack_text = (
                "Blackjack: $0"
            )

        # ==========================================
        # Roulette
        # ==========================================

        if roulette_session_net > 0:

            roulette_text = (
                f"Roulette: +${roulette_session_net:,}"
            )

        elif roulette_session_net < 0:

            roulette_text = (
                f"Roulette: -${abs(roulette_session_net):,}"
            )

        else:

            roulette_text = (
                "Roulette: $0"
            )

        # ==========================================
        # Summary
        # ==========================================

        career_event_summary_lines = [
            blackjack_text,
            roulette_text,
            f"Current Cash: ${career_cash:,}",
        ]

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
        ]

        return

    # ==================================================
    # Niche Game Night
    # ==================================================

    if (
            activity_type
            == CAREER_ACTIVITY_NICHE_NIGHT
    ):

        career_event_summary_lines = [
            "Niche Game Night completed.",
            f"Current Rating: {career_rating:,}",
        ]

        return

    # ==================================================
    # Generic fallback
    # ==================================================

    career_event_summary_lines = [
        f"{event_name} completed."
    ]

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
        entries_per_page=20
):
    leaderboard = (
        get_career_leaderboard()
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

    path = (
        "data/"
        "npcs.json"
    )

    try:
        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )

        return data

    except (
        FileNotFoundError,
        json.JSONDecodeError
    ) as error:

        print(
            "Could not load leaderboard:",
            error
        )

        return []

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

    save_profile(
        build_profile_save_data(),
        current_profile_slot
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

        career_current_schedule = (
            build_default_career_schedule()
        )

    if save_after:
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
        f"Profile saved to slot {current_profile_slot}.", pygame.time.get_ticks()
    )
    return True


def begin_career_profile_switch():
    global profile_switch_snapshot, profile_select_return_state
    global profile_name_active, gender_dropdown_open, profile_message
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
    gender_dropdown_open = False
    profile_message = ""
    pending_profile_slot = None
    profile_creation_mode = False
    confirm_delete_profile = False
    profile_delete_slot = None
    current_state = STATE_PROFILE_SELECT


def finish_profile_selection():
    global current_state, current_game_mode, profile_select_return_state
    global profile_return_state, profile_switch_snapshot
    global profile_name_active, gender_dropdown_open
    destination = profile_select_return_state
    profile_select_return_state = STATE_MENU
    profile_switch_snapshot = None
    profile_name_active = False
    gender_dropdown_open = False
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

    # There are three challenge days per Career month. Pick three
    # different challenge types so newer rules, including All or Nothing,
    # actually rotate into the calendar instead of being stranded at the
    # end of a fixed list.
    monthly_challenges = random.sample(
        CAREER_CHALLENGES,
        min(3, len(CAREER_CHALLENGES))
    )

    # ==================================================
    # Choose 3 different card-event types
    # for this Career month.
    # ==================================================

    available_card_events = [
        CAREER_ACTIVITY_CASUAL_CARDS,
        CAREER_ACTIVITY_POKER_NIGHT,
        CAREER_ACTIVITY_CASINO_NIGHT,
        CAREER_ACTIVITY_NICHE_NIGHT,
    ]

    monthly_card_events = random.sample(
        available_card_events,
        3
    )

    # ==================================================
    # Build 3 visible Career weeks
    # ==================================================

    for week_index in range(3):

        # ----------------------------------------------
        # One themed card event per week
        # ----------------------------------------------

        card_event_type = (
            monthly_card_events[
                week_index
            ]
        )

        if week_index == 0:
            week_types = [
                CAREER_ACTIVITY_ROUND,
                card_event_type,
                CAREER_ACTIVITY_WORK,
                CAREER_ACTIVITY_ROUND,
                CAREER_ACTIVITY_CHALLENGE,
            ]

        elif week_index == 1:
            week_types = [
                CAREER_ACTIVITY_WORK,
                CAREER_ACTIVITY_ROUND,
                CAREER_ACTIVITY_CHALLENGE,
                card_event_type,
                CAREER_ACTIVITY_ROUND,
            ]

        else:
            week_types = [
                CAREER_ACTIVITY_EVENT,
                card_event_type,
                CAREER_ACTIVITY_WORK,
                CAREER_ACTIVITY_ROUND,
                CAREER_ACTIVITY_CHALLENGE,
            ]

        # ----------------------------------------------
        # Create 5 weekdays
        # ----------------------------------------------

        for weekday_index, activity_type in enumerate(
                week_types
        ):
            day_number = (
                week_index * 5
                + weekday_index
                + 1
            )

            entry = {
                "day_number": day_number,
                "weekday_index": weekday_index,
                "activity_type": activity_type,
                "completed": False,
            }

            # ==========================================
            # Play Round
            # ==========================================

            if activity_type == CAREER_ACTIVITY_ROUND:

                entry[
                    "title"
                ] = "Play Solitaire"

            # ==========================================
            # Work
            # ==========================================

            elif activity_type == CAREER_ACTIVITY_WORK:

                entry[
                    "title"
                ] = get_career_work_activity_name()

            # ==========================================
            # Challenge
            # ==========================================

            elif activity_type == CAREER_ACTIVITY_CHALLENGE:

                challenge = (
                    monthly_challenges[
                        challenge_index
                        % len(
                            monthly_challenges
                        )
                    ]
                )

                challenge_index += 1

                entry[
                    "title"
                ] = (
                    "Challenge Round"
                )

                entry[
                    "challenge_id"
                ] = challenge[
                    "id"
                ]

                entry[
                    "challenge_name"
                ] = challenge[
                    "name"
                ]

            # ==========================================
            # Event
            # ==========================================

            elif activity_type == CAREER_ACTIVITY_EVENT:

                entry[
                    "title"
                ] = "Press Interview"

                entry[
                    "event_id"
                ] = "press_interview_01"

            # ==========================================
            # Card Events
            # ==========================================

            elif activity_type in (
                    CAREER_ACTIVITY_CASUAL_CARDS,
                    CAREER_ACTIVITY_POKER_NIGHT,
                    CAREER_ACTIVITY_CASINO_NIGHT,
                    CAREER_ACTIVITY_NICHE_NIGHT
            ):

                entry[
                    "title"
                ] = (
                    CAREER_EVENT_NAMES[
                        activity_type
                    ]
                )

                entry[
                    "game_ids"
                ] = (
                    CAREER_EVENT_GAMES[
                        activity_type
                    ].copy()
                )

                entry[
                    "game_ids"
                ] = (
                    CAREER_EVENT_GAMES[
                        activity_type
                    ].copy()
                )

                if (
                        activity_type
                        == CAREER_ACTIVITY_POKER_NIGHT
                ):
                    entry[
                        "high_stakes_game_id"
                    ] = random.choice(
                        entry[
                            "game_ids"
                        ]
                    )

            # ==========================================
            # Add completed entry
            # ==========================================

            schedule.append(
                entry
            )

    return schedule

def ensure_career_schedule():
    global career_current_schedule

    if not career_current_schedule:
        career_current_schedule = (
            build_default_career_schedule()
        )

def add_career_news(
        headline,
        body,
        category="general"
):
    news_item = {
        "headline":
            headline,

        "body":
            body,

        "category":
            category,

        "month":
            career_month,

        "year":
            career_year,

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

    if not career_leaderboard_state:
        return

    before_rankings = (
        get_npc_leaderboard_snapshot()
    )

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

        skill_tier = npc.get(
            "skill_tier",
            "mid"
        )

        # ==========================================
        # Monthly movement ranges
        # ==========================================

        if (
            npc_id
            == career_leaderboard_star_id
        ):
            # The dominant player tends to remain
            # strong, but can still have a bad month.
            change = random.randint(
                -25,
                55
            )

        elif skill_tier == "elite":
            change = random.randint(
                -45,
                50
            )

        elif skill_tier == "strong":
            change = random.randint(
                -50,
                45
            )

        elif skill_tier == "mid":
            change = random.randint(
                -55,
                55
            )

        else:
            change = random.randint(
                -60,
                60
            )

        current_rating = (
            career_leaderboard_state[
                npc_id
            ].get(
                "rating",
                1000
            )
        )

        new_rating = max(
            100,
            current_rating + change
        )

        career_leaderboard_state[
            npc_id
        ][
            "rating"
        ] = new_rating

        career_leaderboard_state[
            npc_id
        ][
            "last_change"
        ] = change

    after_rankings = (
        get_npc_leaderboard_snapshot()
    )

    add_monthly_leaderboard_news(
        before_rankings,
        after_rankings
    )

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

roulette_session_net = 0
roulette_chip_value = 10

blackjack_session_net = 0

blackjack_selected_bet_percentage = None
blackjack_bet_dropdown_open = False

blackjack_dealer_npc = None

score_four_opponent_choices = []
score_four_opponent_npc = None

debug_previous_state = None


career_event_entry = None
career_event_has_activity = False

career_event_summary_title = ""
career_event_summary_lines = []

career_news_page = 0

career_rating = 1000
career_cash = 500
career_fans = 1000

career_year = 2026
career_month = 1
career_day_of_month = 1

career_weekday_index = 0
career_day = 1

career_residence_image_cache = {}

career_web_image_cache = {}

career_job_image_cache = {}

career_hub_image_cache = {}

realestate_image_cache = {}

jobfinder_image_cache = {}

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

def get_npc_initials(
        npc
):

    name_parts = (
        npc.get(
            "name",
            "NPC"
        ).split()
    )

    initials = "".join(
        part[0]
        for part in name_parts[:2]
        if part
    )

    return initials.upper()


def draw_npc_portrait(
        npc,
        rect,
        style_id
):

    style = (
        NPC_PORTRAIT_STYLES.get(
            style_id,
            NPC_PORTRAIT_STYLES[
                "score_four"
            ]
        )
    )

    shape = style.get(
        "shape",
        "rect"
    )

    border_width = style.get(
        "border_width",
        2
    )

    padding = style.get(
        "padding",
        5
    )

    inner_rect = rect.inflate(
        -padding * 2,
        -padding * 2
    )

    portrait_size = max(
        inner_rect.width,
        inner_rect.height
    )

    portrait = (
        get_npc_portrait_surface(
            npc,
            portrait_size
        )
    )

    # ==================================================
    # Rectangular portrait
    # ==================================================

    if shape == "rect":

        pygame.draw.rect(
            game_surface,
            (
                55,
                70,
                60
            ),
            rect
        )

        if portrait is not None:

            scaled_portrait = (
                pygame.transform.smoothscale(
                    portrait,
                    (
                        inner_rect.width,
                        inner_rect.height
                    )
                )
            )

            game_surface.blit(
                scaled_portrait,
                inner_rect.topleft
            )

        else:

            initials = (
                get_npc_initials(
                    npc
                )
            )

            initials_surface = (
                score_four_score_font.render(
                    initials,
                    True,
                    (
                        255,
                        255,
                        255
                    )
                )
            )

            initials_rect = (
                initials_surface.get_rect(
                    center=rect.center
                )
            )

            game_surface.blit(
                initials_surface,
                initials_rect
            )

        pygame.draw.rect(
            game_surface,
            (
                255,
                255,
                255
            ),
            rect,
            border_width
        )

        return

    # ==================================================
    # Oval portrait
    # ==================================================

    if shape == "oval":

        oval_surface = pygame.Surface(
            (
                rect.width,
                rect.height
            ),
            pygame.SRCALPHA
        )

        # ------------------------------------------
        # Background
        # ------------------------------------------

        pygame.draw.ellipse(
            oval_surface,
            (
                55,
                70,
                60,
                255
            ),
            oval_surface.get_rect()
        )

        # ------------------------------------------
        # Portrait image
        # ------------------------------------------

        if portrait is not None:

            scaled_portrait = (
                pygame.transform.smoothscale(
                    portrait,
                    (
                        inner_rect.width,
                        inner_rect.height
                    )
                )
            )

            portrait_surface = (
                pygame.Surface(
                    (
                        rect.width,
                        rect.height
                    ),
                    pygame.SRCALPHA
                )
            )

            portrait_surface.blit(
                scaled_portrait,
                (
                    padding,
                    padding
                )
            )

            mask_surface = (
                pygame.Surface(
                    (
                        rect.width,
                        rect.height
                    ),
                    pygame.SRCALPHA
                )
            )

            pygame.draw.ellipse(
                mask_surface,
                (
                    255,
                    255,
                    255,
                    255
                ),
                mask_surface.get_rect()
            )

            portrait_surface.blit(
                mask_surface,
                (
                    0,
                    0
                ),
                special_flags=pygame.BLEND_RGBA_MULT
            )

            oval_surface.blit(
                portrait_surface,
                (
                    0,
                    0
                )
            )

        else:

            initials = (
                get_npc_initials(
                    npc
                )
            )

            initials_surface = (
                score_four_score_font.render(
                    initials,
                    True,
                    (
                        255,
                        255,
                        255
                    )
                )
            )

            initials_rect = (
                initials_surface.get_rect(
                    center=(
                        rect.width // 2,
                        rect.height // 2
                    )
                )
            )

            oval_surface.blit(
                initials_surface,
                initials_rect
            )

        # ------------------------------------------
        # Border
        # ------------------------------------------

        pygame.draw.ellipse(
            oval_surface,
            (
                255,
                255,
                255
            ),
            oval_surface.get_rect(),
            border_width
        )

        game_surface.blit(
            oval_surface,
            rect.topleft
        )

def get_npc_portrait_surface(
        npc,
        size
):

    portrait_path = npc.get(
        "portrait"
    )

    if not portrait_path:
        return None

    cache_key = (
        portrait_path,
        size
    )

    if cache_key in npc_icon_cache:
        return npc_icon_cache[
            cache_key
        ]

    try:

        image = pygame.image.load(
            portrait_path
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

def get_jobfinder_image(
        filename,
        size=None
):
    cache_key = (
        filename,
        size
    )

    if cache_key in jobfinder_image_cache:
        return jobfinder_image_cache[cache_key]

    path = (
        "assets/career/jobfinder/"
        + filename
    )

    try:
        image = pygame.image.load(
            path
        ).convert_alpha()

        if size is not None:
            image = pygame.transform.smoothscale(
                image,
                size
            )

        jobfinder_image_cache[
            cache_key
        ] = image

        return image

    except (
        pygame.error,
        FileNotFoundError
    ):
        return None



def get_realestate_image(
        filename,
        size=None
):

    cache_key = (
        filename,
        size
    )

    if cache_key in realestate_image_cache:
        return realestate_image_cache[
            cache_key
        ]

    path = (
        "assets/career/realestate/"
        + filename
    )

    try:

        image = pygame.image.load(
            path
        ).convert_alpha()

        if size is not None:

            image = pygame.transform.smoothscale(
                image,
                size
            )

        realestate_image_cache[
            cache_key
        ] = image

        return image

    except (
        pygame.error,
        FileNotFoundError
    ):

        return None


def get_career_hub_image(
        filename,
        size=None
):

    cache_key = (
        filename,
        size
    )

    if (
        cache_key
        in career_hub_image_cache
    ):
        return (
            career_hub_image_cache[
                cache_key
            ]
        )

    path = (
        "assets/career/hub/"
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

        career_hub_image_cache[
            cache_key
        ] = image

        return image

    except (
        pygame.error,
        FileNotFoundError
    ):

        return None

career_leaderboard_state = {}
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

profile_gender = "non-binary"

gender_options = [
    "male",
    "female",
    "non-binary",
]

gender_dropdown_open = False

profile_name_active = False

profile_message = ""

selected_avatar_base = "base_01"
selected_avatar_eyes = "eyes_01"
selected_avatar_hair = "hair_01"
selected_avatar_glasses = "glasses_01"
selected_avatar_top = "top_01"

# ==================================================
# LAYERED AVATAR ASSETS
# ==================================================

avatar_bases = {}
avatar_eyes = {}
avatar_hair = {}
avatar_glasses = {}
avatar_tops = {}

for i in range(1, 8):

    asset_id = f"base_{i:02d}"

    avatar_bases[asset_id] = pygame.image.load(
        f"assets/ui/profile/avatar/bases/{asset_id}.png"
    ).convert_alpha()


for i in range(1, 10):

    asset_id = f"eyes_{i:02d}"

    avatar_eyes[asset_id] = pygame.image.load(
        f"assets/ui/profile/avatar/eyes/{asset_id}.png"
    ).convert_alpha()


for i in range(1, 13):

    asset_id = f"hair_{i:02d}"

    avatar_hair[asset_id] = pygame.image.load(
        f"assets/ui/profile/avatar/hair/{asset_id}.png"
    ).convert_alpha()


for i in range(1, 7):

    asset_id = f"glasses_{i:02d}"

    avatar_glasses[asset_id] = pygame.image.load(
        f"assets/ui/profile/avatar/glasses/{asset_id}.png"
    ).convert_alpha()


for i in range(1, 7):

    asset_id = f"top_{i:02d}"

    avatar_tops[asset_id] = pygame.image.load(
        f"assets/ui/profile/avatar/tops/{asset_id}.png"
    ).convert_alpha()

# ==================================================
# MINI MENU BUTTON ASSETS
# ==================================================

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

splash_background = pygame.image.load(
    "assets/ui/splash/splash_background.png"
).convert_alpha()

splash_spade = pygame.image.load(
    "assets/ui/splash/splash_spade.png"
).convert_alpha()

splash_diamond = pygame.image.load(
    "assets/ui/splash/splash_diamond.png"
).convert_alpha()

splash_club = pygame.image.load(
    "assets/ui/splash/splash_club.png"
).convert_alpha()

splash_heart = pygame.image.load(
    "assets/ui/splash/splash_heart.png"
).convert_alpha()

splash_prompt = pygame.image.load(
    "assets/ui/splash/splash_prompt.png"
).convert_alpha()


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


menu_background_surfaces = {}
for asset_id, asset_data in MENU_BACKGROUNDS.items():
    menu_background_surfaces[asset_id] = pygame.image.load(
        asset_data["path"]
    ).convert_alpha()

avatar_base_options = [
    "base_01",
    "base_02",
    "base_03",
    "base_04",
    "base_05",
    "base_06",
    "base_07"
]

avatar_eye_options = [
    "eyes_01",
    "eyes_02",
    "eyes_03",
    "eyes_04",
    "eyes_05",
    "eyes_06",
    "eyes_07",
    "eyes_08",
    "eyes_09"
]

avatar_hair_options = [
    "hair_01",
    "hair_02",
    "hair_03",
    "hair_04",
    "hair_05",
    "hair_06",
    "hair_07",
    "hair_08",
    "hair_09",
    "hair_10",
    "hair_11",
    "hair_12"
]

avatar_glasses_options = [
    None,
    "glasses_01",
    "glasses_02",
    "glasses_03",
    "glasses_04",
    "glasses_05",
    "glasses_06"
]

avatar_top_options = [
    "top_01",
    "top_02",
    "top_03",
    "top_04",
    "top_05",
    "top_06"
]

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

menu_background_drift_surfaces = {}

drift_width = (
    BASE_WIDTH
    + MENU_DRIFT_MARGIN * 2
)

drift_height = (
    BASE_HEIGHT
    + MENU_DRIFT_MARGIN * 2
)

for asset_id, surface in (
    menu_background_surfaces.items()
):

    menu_background_drift_surfaces[
        asset_id
    ] = pygame.transform.smoothscale(
        surface,
        (
            drift_width
            * MENU_DRIFT_SCALE,

            drift_height
            * MENU_DRIFT_SCALE
        )
    )

menu_drift_render_surface = pygame.Surface(
    (
        BASE_WIDTH
        * MENU_DRIFT_SCALE,

        BASE_HEIGHT
        * MENU_DRIFT_SCALE
    )
).convert()

felt_surfaces = {}
for asset_id, asset_data in FELTS.items():
    felt_surfaces[asset_id] = pygame.image.load(
        asset_data["path"]
    ).convert_alpha()


title_surfaces = {}
for asset_id, asset_data in TITLES.items():
    title_surfaces[asset_id] = pygame.image.load(
        asset_data["path"]
    ).convert_alpha()

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

cursor_image = (
    cursor_runtime_surfaces.get(selected_cursor)
)

# Modern pygame/SDL can use an RGBA Surface as a true OS
# cursor. That cursor is updated independently from the
# game's 60 FPS loop, which removes the sluggish feel the
# old software-drawn cursor could have. A software fallback
# remains for platforms that reject color cursors.
software_cursor_fallback = False

def apply_selected_cursor():
    global cursor_image
    global software_cursor_fallback

    cursor_image = cursor_runtime_surfaces.get(
        selected_cursor
    )

    if cursor_image is None:
        pygame.mouse.set_visible(True)
        software_cursor_fallback = False
        return

    try:
        native_cursor = pygame.cursors.Cursor(
            (0, 0),
            cursor_image
        )

        pygame.mouse.set_cursor(native_cursor)
        pygame.mouse.set_visible(True)
        software_cursor_fallback = False

    except (pygame.error, TypeError, ValueError):
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


ui_small_font = pygame.font.SysFont(
    None,
    24
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

new_game_rect = pygame.Rect(
    533,
    240,
    300,
    60
)

profile_rect = pygame.Rect(
    533,
    320,
    300,
    60
)

customize_rect = pygame.Rect(
    533,
    400,
    300,
    60
)

how_to_play_rect = pygame.Rect(
    533,
    480,
    300,
    60
)

options_rect = pygame.Rect(
    533,
    560,
    300,
    60
)

quit_rect = pygame.Rect(
    533,
    640,
    300,
    60
)

# ==================================================
# PROFILE UI
# ==================================================

profile_name_rect = pygame.Rect(
    590,
    220,
    380,
    55
)

profile_gender_rect = pygame.Rect(
    590,
    330,
    380,
    55
)

profile_gender_option_rects = [
    pygame.Rect(
        590,
        385 + i * 50,
        380,
        50
    )
    for i in range(3)
]

profile_save_rect = pygame.Rect(
    590,
    530,
    380,
    55
)

profile_switch_rect = pygame.Rect(
    590,
    600,
    380,
    50
)

profile_back_rect = pygame.Rect(
    690,
    670,
    180,
    50
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
# DIFFICULTY SELECT -- AREA FOR UI RECTANGLE DEFINITIONS
# ==================================================

# ==================================================
# BLACKJACK UI // MINIGAME RECTS
# ==================================================

blackjack_change_bet_rect = pygame.Rect(
    970,
    230,
    220,
    50
)

blackjack_bet_dropdown_rects = [
    pygame.Rect(
        970,
        285 + index * 46,
        220,
        42
    )
    for index in range(5)
]

blackjack_hit_rect = pygame.Rect(
    420,
    650,
    140,
    50
)

blackjack_stand_rect = pygame.Rect(
    580,
    650,
    140,
    50
)

blackjack_double_rect = pygame.Rect(
    740,
    650,
    160,
    50
)

blackjack_return_rect = pygame.Rect(
    920,
    650,
    160,
    50
)

blackjack_deal_again_rect = pygame.Rect(
    500,
    650,
    180,
    50
)

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

blackjack_bet_1_rect = pygame.Rect(
    300,
    375,
    140,
    60
)

blackjack_bet_2_rect = pygame.Rect(
    460,
    375,
    140,
    60
)

blackjack_bet_5_rect = pygame.Rect(
    620,
    375,
    140,
    60
)

blackjack_bet_10_rect = pygame.Rect(
    780,
    375,
    140,
    60
)

blackjack_bet_all_rect = pygame.Rect(
    940,
    375,
    140,
    60
)

blackjack_bet_return_rect = pygame.Rect(
    BASE_WIDTH // 2 - 90,
    560,
    180,
    46
)

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
    BASE_WIDTH // 2 - 200,
    650,
    180,
    46
)

career_event_end_rect = pygame.Rect(
    BASE_WIDTH // 2 + 20,
    650,
    180,
    46
)

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

profile_switch_rect = pygame.Rect(
    590,
    605,
    380,
    50
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

avatar_selector_left_x = 1030
avatar_selector_right_x = 1150
avatar_selector_start_y = 185
avatar_selector_gap = 52

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

def draw_blackjack_bet():

    game_surface.fill(
        (
            20,
            105,
            40
        )
    )

    # ==================================================
    # Title
    # ==================================================

    title = options_title_font.render(
        "BLACKJACK",
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
            100
        )
    )

    game_surface.blit(
        title,
        title_rect
    )

    # ==================================================
    # Cash
    # ==================================================

    cash_surface = option_label_font.render(
        f"Cash: ${career_cash:,}",
        True,
        (
            255,
            230,
            0
        )
    )

    cash_rect = cash_surface.get_rect(
        center=(
            BASE_WIDTH // 2,
            185
        )
    )

    game_surface.blit(
        cash_surface,
        cash_rect
    )

    prompt = option_label_font.render(
        "Choose Your Starting Bet Amount (% of your cash)",
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
            250
        )
    )

    game_surface.blit(
        prompt,
        prompt_rect
    )

    # ==================================================
    # Dealer identity
    # ==================================================

    if blackjack_dealer_npc is not None:
        dealer_identity_rect = pygame.Rect(
            130,
            95,
            430,
            90
        )

        pygame.draw.rect(
            game_surface,
            (
                25,
                65,
                35
            ),
            dealer_identity_rect
        )

        pygame.draw.rect(
            game_surface,
            (
                255,
                255,
                255
            ),
            dealer_identity_rect,
            2
        )

        dealer_portrait_rect = pygame.Rect(
            dealer_identity_rect.x + 10,
            dealer_identity_rect.y + 10,
            70,
            70
        )

        draw_npc_portrait(
            blackjack_dealer_npc,
            dealer_portrait_rect,
            "blackjack"
        )

        dealer_name_surface = (
            option_label_font.render(
                blackjack_dealer_npc["name"],
                True,
                (
                    255,
                    255,
                    255
                )
            )
        )

        game_surface.blit(
            dealer_name_surface,
            (
                dealer_identity_rect.x + 95,
                dealer_identity_rect.y + 15
            )
        )

        dealer_info_surface = (
            difficulty_detail_font.render(
                (
                    f"{blackjack_dealer_npc['hometown']}  |  "
                    f"Favorite suit: "
                    f"{blackjack_dealer_npc['favorite_suit']}"
                ),
                True,
                (
                    215,
                    215,
                    215
                )
            )
        )

        game_surface.blit(
            dealer_info_surface,
            (
                dealer_identity_rect.x + 95,
                dealer_identity_rect.y + 52
            )
        )

    # ==================================================
    # Bet buttons / broke state
    # ==================================================

    if career_cash > 0:

        bet_options = [
            (
                blackjack_bet_1_rect,
                "1%",
                get_blackjack_bet(
                    0.01
                )
            ),
            (
                blackjack_bet_2_rect,
                "2%",
                get_blackjack_bet(
                    0.02
                )
            ),
            (
                blackjack_bet_5_rect,
                "5%",
                get_blackjack_bet(
                    0.05
                )
            ),
            (
                blackjack_bet_10_rect,
                "10%",
                get_blackjack_bet(
                    0.10
                )
            ),
            (
                blackjack_bet_all_rect,
                "ALL IN",
                get_blackjack_bet(
                    1.0
                )
            ),
        ]

        for (
                rect,
                label_text,
                amount
        ) in bet_options:
            draw_menu_button(
                rect,
                label_text,
                game_mouse_pos,
                font=difficulty_detail_font
            )

            amount_surface = (
                difficulty_detail_font.render(
                    f"${amount:,}",
                    True,
                    (
                        255,
                        255,
                        255
                    )
                )
            )

            amount_rect = (
                amount_surface.get_rect(
                    center=(
                        rect.centerx,
                        rect.bottom + 25
                    )
                )
            )

            game_surface.blit(
                amount_surface,
                amount_rect
            )

    else:

        broke_surface = (
            option_label_font.render(
                "You're out of cash.",
                True,
                (
                    255,
                    230,
                    0
                )
            )
        )

        broke_rect = (
            broke_surface.get_rect(
                center=(
                    BASE_WIDTH // 2,
                    415
                )
            )
        )

        game_surface.blit(
            broke_surface,
            broke_rect
        )

        broke_detail_surface = (
            difficulty_detail_font.render(
                "Return to Casino Night to finish the event.",
                True,
                (
                    225,
                    225,
                    225
                )
            )
        )

        broke_detail_rect = (
            broke_detail_surface.get_rect(
                center=(
                    BASE_WIDTH // 2,
                    455
                )
            )
        )

        game_surface.blit(
            broke_detail_surface,
            broke_detail_rect
        )

    # ==================================================
    # Return
    # ==================================================

    draw_menu_button(
        blackjack_bet_return_rect,
        "Return",
        game_mouse_pos,
        font=difficulty_detail_font
    )

def draw_blackjack():

    game_surface.fill(
        (
            20,
            105,
            40
        )
    )

    # ==================================================
    # Title
    # ==================================================

    title = options_title_font.render(
        "BLACKJACK",
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
            55
        )
    )

    game_surface.blit(
        title,
        title_rect
    )

    dealer_portrait_rect = pygame.Rect(
        150,
        105,
        72,
        72
    )

    if blackjack_dealer_npc is not None:
        draw_npc_portrait(
            blackjack_dealer_npc,
            dealer_portrait_rect,
            "blackjack"
        )

    # ==================================================
    # Dealer
    # ==================================================

    if blackjack_dealer_npc is not None:

        dealer_name = (
            blackjack_dealer_npc[
                "name"
            ]
        )

    else:

        dealer_name = (
            "Dealer"
        )

    dealer_label = option_label_font.render(
        dealer_name,
        True,
        (
            255,
            255,
            255
        )
    )

    if blackjack_dealer_npc is not None:
        dealer_info_text = (
            f"{blackjack_dealer_npc['hometown']}  |  "
            f"Favorite suit: "
            f"{blackjack_dealer_npc['favorite_suit']}"
        )

        dealer_info_surface = (
            difficulty_detail_font.render(
                dealer_info_text,
                True,
                (
                    220,
                    220,
                    220
                )
            )
        )

        game_surface.blit(
            dealer_info_surface,
            (
                240,
                150
            )
        )

    game_surface.blit(
        dealer_label,
        (
            240,
            115
        )
    )

    dealer_x = 150
    dealer_y = 205

    for index, card in enumerate(
            blackjack_game.dealer_hand
    ):

        target_x = (
                dealer_x
                + index * 95
        )

        position = (
            get_blackjack_animated_position(
                "dealer",
                index,
                target_x,
                dealer_y
            )
        )

        # Card has not started its
        # deal animation yet.
        if position is None:
            continue

        x, y = position

        # ==================================================
        # Dealer hole card
        # ==================================================

        if index == 1:

            flip_progress = (
                blackjack_game.get_dealer_flip_progress()
            )

            # ------------------------------------------
            # Hole card is still face-down
            # ------------------------------------------

            if (
                    flip_progress is None
                    or flip_progress <= 0.0
            ):
                game_surface.blit(
                    game.get_card_back_surface(),
                    (
                        x,
                        y
                    )
                )

                continue

            # ------------------------------------------
            # Hole card is flipping
            # ------------------------------------------

            if flip_progress < 1.0:

                if flip_progress < 0.5:

                    image = (
                        game.get_card_back_surface()
                    )

                    scale_progress = (
                            1.0
                            - flip_progress * 2.0
                    )

                else:

                    card_key = (
                        get_card_key(
                            card
                        )
                    )

                    image = (
                        game.card_fronts[
                            card_key
                        ]
                    )

                    scale_progress = (
                            (flip_progress - 0.5)
                            * 2.0
                    )

                original_width = (
                    image.get_width()
                )

                original_height = (
                    image.get_height()
                )

                scaled_width = max(
                    1,
                    int(
                        original_width
                        * scale_progress
                    )
                )

                scaled_image = (
                    pygame.transform.smoothscale(
                        image,
                        (
                            scaled_width,
                            original_height
                        )
                    )
                )

                scaled_rect = (
                    scaled_image.get_rect(
                        center=(
                            x
                            + original_width // 2,
                            y
                            + original_height // 2
                        )
                    )
                )

                game_surface.blit(
                    scaled_image,
                    scaled_rect
                )

                continue

            # ------------------------------------------
            # Hole card flip finished
            # ------------------------------------------

            card_key = (
                get_card_key(
                    card
                )
            )

            game_surface.blit(
                game.card_fronts[
                    card_key
                ],
                (
                    x,
                    y
                )
            )

            continue

        # ==================================================
        # All other dealer cards
        # ==================================================

        card_key = (
            get_card_key(
                card
            )
        )

        game_surface.blit(
            game.card_fronts[
                card_key
            ],
            (
                x,
                y
            )
        )

    # ==================================================
    # Dealer value
    # ==================================================

    if blackjack_game.dealer_hole_is_revealed():

        dealer_value_text = (
            f"Dealer: "
            f"{blackjack_game.dealer_value()}"
        )

    else:

        dealer_value_text = (
            "Dealer: ?"
        )

    dealer_value_surface = (
        difficulty_detail_font.render(
            dealer_value_text,
            True,
            (
                255,
                255,
                255
            )
        )
    )

    game_surface.blit(
        dealer_value_surface,
        (
            150,
            365
        )
    )

    # ==================================================
    # Player
    # ==================================================

    player_label = option_label_font.render(
        "You",
        True,
        (
            255,
            255,
            255
        )
    )

    game_surface.blit(
        player_label,
        (
            150,
            405
        )
    )

    player_x = 150
    player_y = 430

    for index, card in enumerate(
            blackjack_game.player_hand
    ):

        target_x = (
                player_x
                + index * 95
        )

        position = (
            get_blackjack_animated_position(
                "player",
                index,
                target_x,
                player_y
            )
        )

        if position is None:
            continue

        x, y = position

        card_key = (
            get_card_key(
                card
            )
        )

        game_surface.blit(
            game.card_fronts[
                card_key
            ],
            (
                x,
                y
            )
        )

    player_value_surface = (
        difficulty_detail_font.render(
            (
                f"Hand: "
                f"{blackjack_game.player_value()}"
            ),
            True,
            (
                255,
                255,
                255
            )
        )
    )

    game_surface.blit(
        player_value_surface,
        (
            150,
            630
        )
    )

    # ==================================================
    # Bet
    # ==================================================

    bet_surface = (
        option_label_font.render(
            f"Bet: ${blackjack_game.bet:,}",
            True,
            (
                255,
                230,
                0
            )
        )
    )

    game_surface.blit(
        bet_surface,
        (
            1000,
            95
        )
    )

    cash_surface = (
        option_label_font.render(
            f"Cash: ${career_cash:,}",
            True,
            (
                255,
                255,
                255
            )
        )
    )

    game_surface.blit(
        cash_surface,
        (
            1000,
            135
        )
    )

    if blackjack_session_net > 0:

        session_text = (
            f"Session: +${blackjack_session_net:,}"
        )

    elif blackjack_session_net < 0:

        session_text = (
            f"Session: -${abs(blackjack_session_net):,}"
        )

    else:

        session_text = (
            "Session: $0"
        )

    session_surface = (
        option_label_font.render(
            session_text,
            True,
            (
                255,
                255,
                255
            )
        )
    )

    game_surface.blit(
        session_surface,
        (
            1000,
            175
        )
    )

    if (
            blackjack_selected_bet_percentage
            is not None
            and career_cash > 0
    ):

        if (
                blackjack_selected_bet_percentage
                >= 1.0
        ):
            bet_label = "ALL IN"

        else:
            bet_label = (
                f"{int(
                    blackjack_selected_bet_percentage
                    * 100
                )}%"
            )

        draw_menu_button(
            blackjack_change_bet_rect,
            f"Change Bet: {bet_label}",
            game_mouse_pos,
            selected=blackjack_bet_dropdown_open,
            font=difficulty_detail_font
        )

    if (
            blackjack_selected_bet_percentage
            is not None
            and career_cash > 0
    ):

        bet_choices = [
            ("1%", 0.01),
            ("2%", 0.02),
            ("5%", 0.05),
            ("10%", 0.10),
            ("ALL IN", 1.0),
        ]

        for (
                index,
                (
                        label_text,
                        percentage
                )
        ) in enumerate(
            bet_choices
        ):
            draw_menu_button(
                blackjack_bet_dropdown_rects[
                    index
                ],
                label_text,
                game_mouse_pos,
                selected=(
                        blackjack_selected_bet_percentage
                        == percentage
                ),
                font=difficulty_detail_font
            )

    # ==================================================
    # Result
    # ==================================================

    if blackjack_game.round_complete:

        net_result = (
            blackjack_game.get_net_result()
        )

        if blackjack_game.result == "blackjack":

            result_text = (
                f"BLACKJACK!  +${net_result:,}"
            )

        elif blackjack_game.result == "player":

            result_text = (
                f"YOU WIN  +${net_result:,}"
            )

        elif blackjack_game.result == "push":

            result_text = (
                "PUSH - BET RETURNED"
            )


        else:

            result_text = (
                f"YOU LOSE  ${blackjack_game.bet:,}"

            )

        result_surface = (
            option_label_font.render(
                result_text,
                True,
                (
                    255,
                    230,
                    0
                )
            )
        )

        result_rect = (
            result_surface.get_rect(
                center=(
                    BASE_WIDTH // 2,
                    560
                )
            )
        )

        game_surface.blit(
            result_surface,
            result_rect
        )

    # ==================================================
    # Controls
    # ==================================================

    if (
            not blackjack_game.round_complete
            and not blackjack_game.player_stood
    ):

        draw_menu_button(
            blackjack_hit_rect,
            "Hit",
            game_mouse_pos,
            font=difficulty_detail_font
        )

        draw_menu_button(
            blackjack_stand_rect,
            "Stand",
            game_mouse_pos,
            font=difficulty_detail_font
        )

        if (
                blackjack_game.can_double_down()
                and career_cash >= blackjack_game.bet
        ):
            draw_menu_button(
                blackjack_double_rect,
                "Double",
                game_mouse_pos,
                font=difficulty_detail_font
            )

    elif blackjack_game.round_complete:

        if career_cash > 0:

            draw_menu_button(
                blackjack_deal_again_rect,
                "Deal Again",
                game_mouse_pos,
                font=difficulty_detail_font
            )

        else:

            out_of_cash_surface = (
                option_label_font.render(
                    "OUT OF CASH",
                    True,
                    (
                        255,
                        230,
                        0
                    )
                )
            )

            out_of_cash_rect = (
                out_of_cash_surface.get_rect(
                    center=(
                        blackjack_deal_again_rect.centerx,
                        blackjack_deal_again_rect.centery
                    )
                )
            )

            game_surface.blit(
                out_of_cash_surface,
                out_of_cash_rect
            )

    draw_menu_button(
        blackjack_return_rect,
        "Return",
        game_mouse_pos,
        font=difficulty_detail_font
    )

    if (
            not blackjack_game.round_complete
            and game_mouse_pos is not None
            and blackjack_return_rect.collidepoint(
        game_mouse_pos
    )
    ):
        tooltip_text = (
            "Finish the current hand before leaving."
        )

        tooltip_surface = (
            difficulty_detail_font.render(
                tooltip_text,
                True,
                (
                    255,
                    255,
                    255
                )
            )
        )

        tooltip_bg = pygame.Rect(
            blackjack_return_rect.x - 45,
            blackjack_return_rect.y - 48,
            tooltip_surface.get_width() + 24,
            34
        )

        pygame.draw.rect(
            game_surface,
            (
                25,
                25,
                25
            ),
            tooltip_bg
        )

        pygame.draw.rect(
            game_surface,
            (
                255,
                255,
                255
            ),
            tooltip_bg,
            2
        )

        game_surface.blit(
            tooltip_surface,
            (
                tooltip_bg.x + 12,
                tooltip_bg.y + 7
            )
        )

# ==================================================
# MISC HELPERS (Game Unlocks, etc.)
# ==================================================

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

        if (
                not texas_holdem_table_sweep_rewarded
        ):

            career_rating += (
                TEXAS_HOLDEM_TABLE_SWEEP_RATING_BONUS
            )

            texas_holdem_table_sweep_rewarded = True

            career_event_has_activity = True

        texas_holdem_game.result_text += (
            " TABLE CLEARED! "
            f"+{TEXAS_HOLDEM_TABLE_SWEEP_RATING_BONUS} "
            "Rating."
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
        starting_stack=None
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

    opponents = (
        get_texas_holdem_opponents()
    )

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

    # ==================================================
    # Reset runtime timers
    # ==================================================

    texas_holdem_next_npc_action_at = 0
    texas_holdem_round_advance_at = 0
    texas_holdem_next_hand_at = 0

    # ==================================================
    # Start poker session
    # ==================================================

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

    if (
            texas_holdem_game.current_stage
            != "ready"
    ):

        career_event_has_activity = True

    texas_holdem_hand_win_sound_at = 0

    current_state = (
        STATE_CAREER_EVENT_SELECT
    )

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
        starting_stack=None
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

    opponents = (
        get_five_card_draw_opponents()
    )

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

    five_card_draw_next_npc_action_at = 0
    five_card_draw_round_advance_at = 0
    five_card_draw_next_hand_at = 0
    five_card_draw_session_end_at = 0
    five_card_draw_last_processed_showdown_hand = 0
    five_card_draw_table_sweep_rewarded = False
    five_card_draw_hand_win_sound_at = 0

    reset_five_card_draw_ui_session()

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

    current_state = (
        STATE_CAREER_EVENT_SELECT
    )


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

    audio.play_sound(
        "card_flip"
    )

    if 0 in five_card_draw_game.winner_indexes:
        five_card_draw_hand_win_sound_at = (
                pygame.time.get_ticks()
                + 450
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

        if not five_card_draw_table_sweep_rewarded:

            career_rating += (
                FIVE_CARD_DRAW_TABLE_SWEEP_RATING_BONUS
            )

            five_card_draw_table_sweep_rewarded = True
            career_event_has_activity = True

        five_card_draw_game.result_text += (
            " TABLE CLEARED! "
            f"+{FIVE_CARD_DRAW_TABLE_SWEEP_RATING_BONUS} "
            "Rating."
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
        starting_stack=None
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

    opponents = (
        get_seven_card_stud_opponents()
    )

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

    seven_card_stud_next_npc_action_at = 0
    seven_card_stud_round_advance_at = 0
    seven_card_stud_next_hand_at = 0
    seven_card_stud_session_end_at = 0
    seven_card_stud_last_processed_showdown_hand = 0
    seven_card_stud_table_sweep_rewarded = False
    seven_card_stud_hand_win_sound_at = 0

    reset_seven_card_stud_ui_session()

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

    current_state = (
        STATE_CAREER_EVENT_SELECT
    )


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

    audio.play_sound(
        "card_flip"
    )

    if 0 in seven_card_stud_game.winner_indexes:
        seven_card_stud_hand_win_sound_at = (
                pygame.time.get_ticks()
                + 450
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

        if not seven_card_stud_table_sweep_rewarded:
            career_rating += (
                SEVEN_CARD_STUD_TABLE_SWEEP_RATING_BONUS
            )

            seven_card_stud_table_sweep_rewarded = True
            career_event_has_activity = True

        seven_card_stud_game.result_text += (
            " TABLE CLEARED! "
            f"+{SEVEN_CARD_STUD_TABLE_SWEEP_RATING_BONUS} "
            "Rating."
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

    roulette_game.payout_claimed = True

def settle_blackjack_round():
    global career_cash
    global blackjack_session_net

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

    blackjack_game.payout_claimed = True

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

    current_state = (
        STATE_CAREER_EVENT_SELECT
    )


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


def debug_open_poker_night():
    global current_state

    debug_prepare_poker_night()

    current_state = (
        STATE_CAREER_EVENT_SELECT
    )


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


def debug_start_next_career_month():
    global career_year
    global career_month
    global career_day
    global career_day_of_month
    global career_weekday_index
    global career_current_schedule

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

    career_current_schedule = (
        build_default_career_schedule()
    )

    auto_save_career()


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
    global profile_gender

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
    ] = dict(
        career_leaderboard_state
    )

    career_data[
        "leaderboard_star_id"
    ] = career_leaderboard_star_id

    career_data[
        "rating"
    ] = career_rating

    career_data[
        "cash"
    ] = career_cash

    career_data[
        "fans"
    ] = career_fans

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

    # ----------------------------
    # Gameplay settings
    # ----------------------------

    profile_settings = profile_data.setdefault(
        "settings",
        {}
    )

    profile_settings[
        "solitaire_deal_mode"
    ] = game.deal_mode

    return profile_data

def apply_profile_save_data(
        data
):
    global career_owned_residences
    global career_news_items

    global player_solitaire_points

    global career_leaderboard_state
    global career_leaderboard_star_id
    global career_rating
    global career_cash
    global career_fans

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

    career_leaderboard_state = dict(
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

    career_rating = career_data.get(
        "rating",
        1000
    )

    career_cash = career_data.get(
        "cash",
        0
    )

    career_fans = career_data.get(
        "fans",
        0
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

    game.set_deal_mode(
        gameplay_settings.get(
            "solitaire_deal_mode",
            "random"
        )
    )

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

    draw_submenu_background(
        overlay_alpha=135
    )

    draw_submenu_title(
        "CHOOSE OPPONENT",
        y=60,
        width=500
    )

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

        # ==========================================
        # Favorite suit
        # ==========================================

        suit_surface = (
            difficulty_detail_font.render(
                (
                    "Favorite suit: "
                    f"{npc['favorite_suit']}"
                ),
                True,
                (
                    220,
                    220,
                    220
                )
            )
        )

        game_surface.blit(
            suit_surface,
            (
                rect.x + 145,
                rect.y + 127
            )
        )

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



def draw_score_four():

    game_surface.fill(
        (
            20,
            120,
            35
        )
    )

    # ==================================================
    # Mode status
    # ==================================================

    if score_four_game.mode == "competitive":

        if score_four_opponent_npc is not None:
            opponent_name = (
                score_four_opponent_npc["name"]
            )
        else:
            opponent_name = "NPC"

        status_text = (
            f"YOU  {score_four_game.player_score}"
            f"     -     "
            f"{score_four_game.npc_score}  "
            f"{opponent_name}"
        )

        status_surface = (
            score_four_score_font.render(
                status_text,
                True,
                (
                    255,
                    255,
                    255
                )
            )
        )

        status_rect = (
            status_surface.get_rect(
                center=(
                    BASE_WIDTH // 2,
                    70
                )
            )
        )

        game_surface.blit(
            status_surface,
            status_rect
        )

        round_surface = (
            score_four_round_font.render(
                (
                    f"ROUND "
                    f"{score_four_game.round_number}"
                    f"     BEST OF 5"
                ),
                True,
                (
                    255,
                    230,
                    0
                )
            )
        )

        round_rect = (
            round_surface.get_rect(
                center=(
                    BASE_WIDTH // 2,
                    105
                )
            )
        )

        game_surface.blit(
            round_surface,
            round_rect
        )

    else:

        progress_text = (
            f"Solved: "
            f"{score_four_game.puzzles_completed}"
            f"/"
            f"{score_four_game.puzzles_required}"
        )

        progress_surface = (
            difficulty_detail_font.render(
                progress_text,
                True,
                (
                    255,
                    255,
                    255
                )
            )
        )

        progress_rect = (
            progress_surface.get_rect(
                center=(
                    BASE_WIDTH // 2,
                    100
                )
            )
        )

        game_surface.blit(
            progress_surface,
            progress_rect
        )

    # ==================================================
    # Original cards
    # ==================================================

    card_y = 155

    card_width = 120
    card_height = 168

    card_gap = 24

    total_card_width = (
        card_width * 4
        + card_gap * 3
    )

    card_start_x = (
        BASE_WIDTH
        - total_card_width
    ) // 2

    for index, number in enumerate(
            score_four_game.original_numbers
    ):

        suit = (
            score_four_game.card_suits[
                index
            ]
        )

        rank = (
            "A"
            if number == 1
            else str(number)
        )

        suit_letter_map = {
            "Clubs": "C",
            "Diamonds": "D",
            "Hearts": "H",
            "Spades": "S",
        }

        card_key = (
            f"{rank}"
            f"{suit_letter_map[suit]}"
        )

        card_image = game.card_fronts[
            card_key
        ]

        x = (
            card_start_x
            + index
            * (
                card_width
                + card_gap
            )
        )

        game_surface.blit(
            card_image,
            (
                x,
                card_y
            )
        )

    # ==================================================
    # Number tiles
    # ==================================================

    tile_size = 130
    tile_gap = 8

    tile_start_x = (
        BASE_WIDTH // 2
        - tile_size
        - tile_gap // 2
    )

    tile_start_y = 335

    score_four_number_rects.clear()

    tile_positions = [
        (
            tile_start_x,
            tile_start_y
        ),
        (
            tile_start_x
            + tile_size
            + tile_gap,
            tile_start_y
        ),
        (
            tile_start_x,
            tile_start_y
            + tile_size
            + tile_gap
        ),
        (
            tile_start_x
            + tile_size
            + tile_gap,
            tile_start_y
            + tile_size
            + tile_gap
        ),
    ]

    for index, position in enumerate(
            tile_positions
    ):

        rect = pygame.Rect(
            position[0],
            position[1],
            tile_size,
            tile_size
        )

        score_four_number_rects.append(
            rect
        )

        value = (
            score_four_game.values[
                index
            ]
        )

        selected = (
            score_four_game.selected_index
            == index
        )

        fill_color = (
            (
                255,
                220,
                120
            )
            if selected
            else (
                225,
                225,
                225
            )
        )

        pygame.draw.rect(
            game_surface,
            fill_color,
            rect
        )

        pygame.draw.rect(
            game_surface,
            (
                20,
                20,
                20
            ),
            rect,
            3
        )

        if value is not None:

            if value.denominator == 1:
                display_text = str(
                    value.numerator
                )

            else:
                display_text = (
                    f"{value.numerator}/"
                    f"{value.denominator}"
                )

            value_surface = (
                options_title_font.render(
                    display_text,
                    True,
                    (
                        0,
                        0,
                        0
                    )
                )
            )

            value_rect = (
                value_surface.get_rect(
                    center=rect.center
                )
            )

            game_surface.blit(
                value_surface,
                value_rect
            )

    # ==================================================
    # Operators
    # ==================================================

    operator_y = (
        tile_start_y
        + tile_size * 2
        + tile_gap
        + 10
    )

    operator_width = 65
    operator_height = 46

    operator_symbols = [
        (
            "+",
            "+"
        ),
        (
            "-",
            "−"
        ),
        (
            "*",
            "×"
        ),
        (
            "/",
            "÷"
        ),
    ]

    total_operator_width = (
        operator_width * 4
    )

    operator_start_x = (
        BASE_WIDTH
        - total_operator_width
    ) // 2

    score_four_operator_rects.clear()

    for index, (
        operator_id,
        symbol
    ) in enumerate(
        operator_symbols
    ):

        rect = pygame.Rect(
            operator_start_x
            + index
            * operator_width,
            operator_y,
            operator_width,
            operator_height
        )

        score_four_operator_rects[
            operator_id
        ] = rect

        selected = (
            score_four_game.selected_operator
            == operator_id
        )

        fill_color = (
            (
                255,
                220,
                120
            )
            if selected
            else (
                210,
                210,
                210
            )
        )

        pygame.draw.rect(
            game_surface,
            fill_color,
            rect
        )

        pygame.draw.rect(
            game_surface,
            (
                20,
                20,
                20
            ),
            rect,
            3
        )

        symbol_surface = (
            option_label_font.render(
                symbol,
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        symbol_rect = (
            symbol_surface.get_rect(
                center=rect.center
            )
        )

        game_surface.blit(
            symbol_surface,
            symbol_rect
        )

    if score_four_game.solo_hint_available():
        draw_button(
            score_four_hint_rect,
            "Hint",
            font=difficulty_detail_font
        )

    # ==================================================
    # Hint text
    # ==================================================

    if (
            score_four_game.hint_text is not None
            and not score_four_game.session_complete
    ):
        hint_surface = (
            difficulty_detail_font.render(
                score_four_game.hint_text,
                True,
                (
                    255,
                    230,
                    0
                )
            )
        )

        hint_rect = (
            hint_surface.get_rect(
                center=(
                    BASE_WIDTH // 2,
                    675
                )
            )
        )

        game_surface.blit(
            hint_surface,
            hint_rect
        )

    # ==================================================
    # Undo / Exit
    # ==================================================

    draw_button(
        score_four_undo_rect,
        "Undo",
        font=difficulty_detail_font
    )

    draw_button(
        score_four_exit_rect,
        "Exit",
        font=difficulty_detail_font
    )

    score_four_complete_rect = pygame.Rect(
        BASE_WIDTH // 2 - 100,
        585,
        200,
        48
    )

    draw_score_four_npc_panel()

    # ==================================================
    # Solved text
    # ==================================================

    if (
            score_four_game.is_solved()
            and not score_four_game.session_complete
    ):

        solved_surface = (
            option_label_font.render(
                "Solved!",
                True,
                (
                    255,
                    230,
                    0
                )
            )
        )

        solved_rect = (
            solved_surface.get_rect(
                center=(
                    BASE_WIDTH // 2,
                    680
                )
            )
        )

        game_surface.blit(
            solved_surface,
            solved_rect
        )

    # ==================================================
    # Competitive round result
    # ==================================================

    if (
            score_four_game.mode
            == "competitive"
            and score_four_game.round_complete
    ):

        result_rect = pygame.Rect(
            BASE_WIDTH // 2 - 325,
            285,
            650,
            190
        )

        pygame.draw.rect(
            game_surface,
            (
                25,
                45,
                30
            ),
            result_rect
        )

        pygame.draw.rect(
            game_surface,
            (
                255,
                255,
                255
            ),
            result_rect,
            3
        )

        # ==================================================
        # Opponent portrait
        # ==================================================

        if score_four_opponent_npc is not None:
            result_portrait_rect = pygame.Rect(
                result_rect.x + 25,
                result_rect.y + 35,
                90,
                90
            )

            draw_npc_portrait(
                score_four_opponent_npc,
                result_portrait_rect,
                "score_four"
            )

        # ==================================================
        # Result text
        # ==================================================

        if (
                score_four_game.round_result
                == "player"
        ):

            result_text = (
                "YOU WIN THE ROUND!"
            )

        else:

            if score_four_opponent_npc is not None:

                result_text = (
                    f"{score_four_opponent_npc['name']} "
                    f"WINS THE ROUND!"
                )

            else:

                result_text = (
                    "NPC WINS THE ROUND!"
                )

        result_surface = (
            option_label_font.render(
                result_text,
                True,
                (
                    255,
                    230,
                    0
                )
            )
        )

        result_text_rect = (
            result_surface.get_rect(
                center=(
                    result_rect.centerx + 55,
                    result_rect.y + 55
                )
            )
        )

        game_surface.blit(
            result_surface,
            result_text_rect
        )

        # ==================================================
        # NPC solution
        # ==================================================

        if (
                score_four_game.round_result
                == "npc"
        ):
            solution_surface = (
                difficulty_detail_font.render(
                    (
                            "Solution: "
                            + score_four_game.solution
                    ),
                    True,
                    (
                        230,
                        230,
                        230
                    )
                )
            )

            solution_rect = (
                solution_surface.get_rect(
                    center=(
                        result_rect.centerx + 55,
                        result_rect.y + 120
                    )
                )
            )

            game_surface.blit(
                solution_surface,
                solution_rect
            )

    # ==================================================
    # Solo session complete / result
    # ==================================================

    if score_four_game.session_complete:
        overlay_rect = pygame.Rect(
            BASE_WIDTH // 2 - 230,
            250,
            460,
            400
        )

        pygame.draw.rect(
            game_surface,
            (
                25,
                45,
                30
            ),
            overlay_rect
        )

        pygame.draw.rect(
            game_surface,
            (
                255,
                255,
                255
            ),
            overlay_rect,
            3
        )

        complete_surface = (
            options_title_font.render(
                "SOLO COMPLETE",
                True,
                (
                    255,
                    255,
                    255
                )
            )
        )

        complete_rect = (
            complete_surface.get_rect(
                center=(
                    overlay_rect.centerx,
                    overlay_rect.y + 75
                )
            )
        )

        game_surface.blit(
            complete_surface,
            complete_rect
        )

        reward_surface = (
            option_label_font.render(
                "+60 Rating",
                True,
                (
                    255,
                    230,
                    0
                )
            )
        )

        reward_rect = (
            reward_surface.get_rect(
                center=(
                    overlay_rect.centerx,
                    overlay_rect.y + 155
                )
            )
        )

        game_surface.blit(
            reward_surface,
            reward_rect
        )

        summary_surface = (
            difficulty_detail_font.render(
                "3 Score-Four puzzles solved",
                True,
                (
                    220,
                    220,
                    220
                )
            )
        )

        summary_rect = (
            summary_surface.get_rect(
                center=(
                    overlay_rect.centerx,
                    overlay_rect.y + 205
                )
            )
        )

        game_surface.blit(
            summary_surface,
            summary_rect
        )

        draw_button(
            score_four_complete_rect,
            "Continue",
            font=difficulty_detail_font
        )

    # ==================================================
    # Competitive match complete
    # ==================================================

    if (
            score_four_game.mode
            == "competitive"
            and score_four_game.match_complete
    ):

        overlay_rect = pygame.Rect(
            BASE_WIDTH // 2 - 260,
            235,
            520,
            410
        )

        pygame.draw.rect(
            game_surface,
            (
                25,
                45,
                30
            ),
            overlay_rect
        )

        pygame.draw.rect(
            game_surface,
            (
                255,
                255,
                255
            ),
            overlay_rect,
            3
        )

        title_surface = (
            options_title_font.render(
                "MATCH COMPLETE",
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
                    overlay_rect.centerx,
                    overlay_rect.y + 65
                )
            )
        )

        game_surface.blit(
            title_surface,
            title_rect
        )

        # ----------------------------------------------
        # Winner
        # ----------------------------------------------

        if (
                score_four_game.match_winner
                == "player"
        ):
            winner_text = "YOU WIN!"

        else:
            winner_text = "NPC WINS"

        winner_surface = (
            option_label_font.render(
                winner_text,
                True,
                (
                    255,
                    230,
                    0
                )
            )
        )

        winner_rect = (
            winner_surface.get_rect(
                center=(
                    overlay_rect.centerx,
                    overlay_rect.y + 135
                )
            )
        )

        game_surface.blit(
            winner_surface,
            winner_rect
        )

        # ----------------------------------------------
        # Final score
        # ----------------------------------------------

        score_text = (
            f"YOU  {score_four_game.player_score}"
            f"     -     "
            f"{score_four_game.npc_score}  NPC"
        )

        score_surface = (
            option_label_font.render(
                score_text,
                True,
                (
                    255,
                    255,
                    255
                )
            )
        )

        score_rect = (
            score_surface.get_rect(
                center=(
                    overlay_rect.centerx,
                    overlay_rect.y + 200
                )
            )
        )

        game_surface.blit(
            score_surface,
            score_rect
        )

        reward_surface = (
            option_label_font.render(
                (
                    f"+"
                    f"{score_four_game.competitive_reward}"
                    f" Rating"
                ),
                True,
                (
                    255,
                    230,
                    0
                )
            )
        )

        reward_rect = (
            reward_surface.get_rect(
                center=(
                    overlay_rect.centerx,
                    overlay_rect.y + 250
                )
            )
        )

        game_surface.blit(
            reward_surface,
            reward_rect
        )

        # ----------------------------------------------
        # NPC's final solution
        # ----------------------------------------------

        if (
                score_four_game.round_result
                == "npc"
        ):
            solution_surface = (
                difficulty_detail_font.render(
                    (
                            "Solution: "
                            + score_four_game.solution
                    ),
                    True,
                    (
                        220,
                        220,
                        220
                    )
                )
            )

            solution_rect = (
                solution_surface.get_rect(
                    center=(
                        overlay_rect.centerx,
                        overlay_rect.y + 295
                    )
                )
            )

            game_surface.blit(
                solution_surface,
                solution_rect
            )

        draw_button(
            score_four_match_continue_rect,
            "Continue",
            font=difficulty_detail_font
        )

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

    game_surface.fill(
        (
            20,
            120,
            35
        )
    )

    # ==================================================
    # Title
    # ==================================================

    title_surface = (
        options_title_font.render(
            "SCORE-FOUR",
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
                150
            )
        )
    )

    game_surface.blit(
        title_surface,
        title_rect
    )

    subtitle_surface = (
        option_label_font.render(
            "Choose a Mode",
            True,
            (
                230,
                230,
                230
            )
        )
    )

    subtitle_rect = (
        subtitle_surface.get_rect(
            center=(
                BASE_WIDTH // 2,
                215
            )
        )
    )

    game_surface.blit(
        subtitle_surface,
        subtitle_rect
    )

    # ==================================================
    # Mode buttons
    # ==================================================

    draw_button(
        score_four_solo_rect,
        "Solo",
        font=option_label_font
    )

    draw_button(
        score_four_competitive_rect,
        "Competitive",
        font=option_label_font
    )

    # --------------------------------------------------
    # Descriptions
    # --------------------------------------------------

    solo_surface = (
        difficulty_detail_font.render(
            "Solve 3 puzzles",
            True,
            (
                230,
                230,
                230
            )
        )
    )

    solo_rect = (
        solo_surface.get_rect(
            center=(
                score_four_solo_rect.centerx,
                score_four_solo_rect.bottom
                + 30
            )
        )
    )

    game_surface.blit(
        solo_surface,
        solo_rect
    )

    competitive_surface = (
        difficulty_detail_font.render(
            "First to 3 wins",
            True,
            (
                230,
                230,
                230
            )
        )
    )

    competitive_rect = (
        competitive_surface.get_rect(
            center=(
                score_four_competitive_rect.centerx,
                score_four_competitive_rect.bottom
                + 30
            )
        )
    )

    game_surface.blit(
        competitive_surface,
        competitive_rect
    )

    draw_button(
        score_four_mode_return_rect,
        "Return",
        font=difficulty_detail_font
    )

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

def get_customize_data():
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

def get_solitaire_rating_reward(
        current_rating
):

    if current_rating <= 999:
        return 85

    elif current_rating <= 1299:
        return 75

    elif current_rating <= 1599:
        return 72

    elif current_rating <= 1899:
        return 67

    elif current_rating <= 2099:
        return 60

    elif current_rating <= 2399:
        return 50

    elif current_rating <= 2799:
        return 40

    else:
        return 25

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
                f"in the international Solitaire rankings."
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
                career_rating
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

        career_rating += (
            rating_change
        )

        round_data[
            "cash_earned"
        ] = cash_earned

        round_data[
            "rating_change"
        ] = rating_change

    return progression_result

def ensure_career_leaderboard():

    if not career_leaderboard_state:
        initialize_career_leaderboard()

        auto_save_career()

def initialize_career_leaderboard():
    global career_leaderboard_state
    global career_leaderboard_star_id

    career_leaderboard_state = {}

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

        career_leaderboard_state[
            npc_id
        ] = {
            "rating":
                rating,

            "last_change":
                0,
        }

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

            career_leaderboard_state[
                career_leaderboard_star_id
            ][
                "rating"
            ] = (
                second_best
                + random.randint(
                    175,
                    325
                )
            )

def get_career_leaderboard():

    ensure_career_leaderboard()

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

        leaderboard.append(
            {
                "id":
                    npc_id,

                "name":
                    npc.get(
                        "name",
                        "Unknown Player"
                    ),

                "last_change":
                    0,

                "rating":
                    npc_state.get(
                        "rating",
                        1000
                    ),

                "last_change":
                    npc_state.get(
                        "last_change",
                        0
                    ),

                "bio":
                    npc.get(
                        "bio",
                        "Professional Solitaire player."
                    ),

                "country":
                    npc.get(
                        "country",
                        "Unknown"
                    ),

                "age":
                    npc.get(
                        "age",
                        "Unknown"
                    ),

                "hometown":
                    npc.get(
                        "hometown",
                        "Unknown"
                    ),

                "favorite_suit":
                    npc.get(
                        "favorite_suit",
                        "Unknown"
                    ),

                "is_star":
                    (
                        npc_id
                        == career_leaderboard_star_id
                    ),

                "is_player":
                    False,
            }
        )

    leaderboard.append(
        {
            "id":
                "player",

            "name":
                player_name,

            "rating":
                career_rating,

            "bio":
                "Current Career Mode player.",

            "country":
                "",

            "age":
                "",

            "hometown":
                "",

            "favorite_suit":
                "",

            "is_star":
                False,

            "is_player":
                True,
        }
    )

    leaderboard.sort(
        key=lambda item:
            item[
                "rating"
            ],
        reverse=True
    )

    return leaderboard

def get_player_leaderboard_rank():

    leaderboard = (
        get_career_leaderboard()
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

    start_y = 285
    line_spacing = 58

    for index, line_text in enumerate(
            career_event_summary_lines
    ):

        line_surface = (
            option_label_font.render(
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
        return "Hints disabled"

    if game.hints_remaining is None:
        return "Unlimited hints"

    if game.hints_remaining == 1:
        return "1 hint remaining"

    return f"{game.hints_remaining} hints remaining"


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
    235,
    180,
    330,
    410
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

    # ==================================================
    # Background
    # ==================================================

    draw_submenu_background(
        overlay_alpha=135
    )

    help_category_rects.clear()
    help_page_rects.clear()

    # ==================================================
    # Title
    # ==================================================

    draw_submenu_title(
        "HELP",
        y=60,
        width=300
    )

    # ==================================================
    # Main panels
    # ==================================================

    nav_panel = pygame.Rect(
        40,
        110,
        280,
        570
    )

    content_rect = pygame.Rect(
        345,
        110,
        980,
        570
    )

    # Left panel
    nav_surface = pygame.Surface(
        (
            nav_panel.width,
            nav_panel.height
        ),
        pygame.SRCALPHA
    )

    nav_surface.fill(
        (
            15,
            35,
            25,
            210
        )
    )

    game_surface.blit(
        nav_surface,
        nav_panel.topleft
    )

    pygame.draw.rect(
        game_surface,
        (
            255,
            255,
            255
        ),
        nav_panel,
        2
    )

    # Right panel
    content_surface = pygame.Surface(
        (
            content_rect.width,
            content_rect.height
        ),
        pygame.SRCALPHA
    )

    content_surface.fill(
        (
            245,
            245,
            238,
            250
        )
    )

    game_surface.blit(
        content_surface,
        content_rect.topleft
    )

    pygame.draw.rect(
        game_surface,
        (
            255,
            255,
            255
        ),
        content_rect,
        2
    )

    # ==================================================
    # Left navigation
    # ==================================================

    current_y = (
        nav_panel.y + 20
    )

    for (
            category_id,
            category_data
    ) in HELP_NAVIGATION.items():

        category_rect = pygame.Rect(
            nav_panel.x + 15,
            current_y,
            nav_panel.width - 30,
            46
        )

        help_category_rects[
            category_id
        ] = category_rect

        expanded = (
            help_expanded_categories.get(
                category_id,
                False
            )
        )

        arrow = (
            "-"
            if expanded
            else "+"
        )

        draw_menu_button(
            category_rect,
            (
                f"{arrow}  "
                f"{category_data['name']}"
            ),
            game_mouse_pos,
            font=difficulty_detail_font
        )

        current_y += 52

        # ----------------------------------------------
        # Child pages
        # ----------------------------------------------

        if expanded:

            for (
                    page_id,
                    page_name
            ) in category_data[
                "pages"
            ]:

                page_rect = pygame.Rect(
                    nav_panel.x + 35,
                    current_y,
                    nav_panel.width - 55,
                    38
                )

                help_page_rects[
                    page_id
                ] = page_rect

                selected = (
                    help_current_page
                    == page_id
                )

                draw_menu_button(
                    page_rect,
                    page_name,
                    game_mouse_pos,
                    selected=selected,
                    font=difficulty_detail_font
                )

                current_y += 42

        current_y += 6

    # ==================================================
    # Content
    # ==================================================

    content = HELP_CONTENT.get(
        help_current_page,
        HELP_CONTENT[
            "solitaire_basics"
        ]
    )

    section_title = (
        option_label_font.render(
            content[
                "title"
            ],
            True,
            (
                20,
                20,
                20
            )
        )
    )

    game_surface.blit(
        section_title,
        (
            content_rect.x + 35,
            content_rect.y + 30
        )
    )

    if (
            help_current_page
            == "solitaire_basics"
    ):
        text_rect = pygame.Rect(
            content_rect.x + 35,
            content_rect.y + 90,
            455,
            content_rect.height - 125
        )

    else:
        text_rect = pygame.Rect(
            content_rect.x + 35,
            content_rect.y + 90,
            content_rect.width - 70,
            content_rect.height - 125
        )

    current_y = (
        text_rect.y
    )

    for line in content[
        "lines"
    ]:

        if not line:
            current_y += 14
            continue

        words = line.split()

        wrapped_lines = []
        current_line = ""

        for word in words:

            if current_line:
                test_line = (
                    current_line
                    + " "
                    + word
                )

            else:
                test_line = word

            test_surface = (
                difficulty_detail_font.render(
                    test_line,
                    True,
                    (
                        20,
                        20,
                        20
                    )
                )
            )

            if (
                    test_surface.get_width()
                    <= text_rect.width
            ):
                current_line = (
                    test_line
                )

            else:

                if current_line:
                    wrapped_lines.append(
                        current_line
                    )

                current_line = word

        if current_line:
            wrapped_lines.append(
                current_line
            )

        for wrapped_line in wrapped_lines:

            line_surface = (
                difficulty_detail_font.render(
                    wrapped_line,
                    True,
                    (
                        20,
                        20,
                        20
                    )
                )
            )

            game_surface.blit(
                line_surface,
                (
                    text_rect.x,
                    current_y
                )
            )

            current_y += 26

        current_y += 10

    # ==================================================
    # Solitaire diagram
    # ==================================================

    if (
            help_current_page
            == "solitaire_basics"
    ):
        draw_solitaire_help_diagram(
            content_rect
        )

    # ==================================================
    # Return
    # ==================================================

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
        f"Rating: {career_rating:,}",
        f"Leaderboard: #{get_player_leaderboard_rank()}",
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

    date_title = menu_title_font.render(
        f"{get_career_month_name()} {career_year}",
        True,
        (
            0,
            0,
            0
        )
    )

    date_title_rect = date_title.get_rect(
        center=date_header_rect.center
    )

    game_surface.blit(
        date_title,
        date_title_rect
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

    updated_surface = ui_small_font.render(
        f"Last updated: Day {career_day}",
        True,
        (
            90,
            90,
            90
        )
    )

    updated_rect = updated_surface.get_rect(
        midtop=(
            date_header_rect.centerx,
            date_title_rect.bottom - 4
        )
    )

    game_surface.blit(
        updated_surface,
        updated_rect
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

    career_hub_controls.begin_calendar(career_current_schedule, career_day_of_month)

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
            career_current_schedule[:15]
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
                        cell_rect.y + 70
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
                        cell_rect.y + 105
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

            activity_surface = (
                render_text_fit(
                    activity_title,
                    option_label_font,
                    cell_rect.width - 20,
                    (
                        0,
                        0,
                        0
                    )
                )
            )

            activity_rect = (
                activity_surface.get_rect(
                    center=(
                        cell_rect.centerx,
                        cell_rect.y + 82
                    )
                )
            )

            game_surface.blit(
                activity_surface,
                activity_rect
            )

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
                    CAREER_ACTIVITY_NICHE_NIGHT

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

    career_hub_controls.draw_toolbar(
        game_surface, draw_button, career_hub_controls.font, pygame.time.get_ticks()
    )

    draw_button(
        career_back_rect,
        "Exit Career"
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

    game_surface.fill(
        (
            235,
            235,
            225
        )
    )

    draw_career_browser_header(
        "https://www.solitaireleaderboards.net/bios"
    )

    if selected_leaderboard_entry is None:

        title = menu_title_font.render(
            "PLAYER BIO",
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
                130
            )
        )

        game_surface.blit(
            title,
            title_rect
        )

        draw_button(
            career_subpage_back_rect,
            "Return to Rankings"
        )

        return

    name = (
        selected_leaderboard_entry.get(
            "name",
            "Unknown Player"
        )
    )

    rating = (
        selected_leaderboard_entry.get(
            "rating",
            1000
        )
    )

    bio = (
        selected_leaderboard_entry.get(
            "bio",
            "Professional Solitaire player."
        )
    )

    country = (
        selected_leaderboard_entry.get(
            "country",
            "Unknown"
        )
    )

    age = (
        selected_leaderboard_entry.get(
            "age",
            "Unknown"
        )
    )

    hometown = (
        selected_leaderboard_entry.get(
            "hometown",
            "Unknown"
        )
    )

    favorite_suit = (
        selected_leaderboard_entry.get(
            "favorite_suit",
            "Unknown"
        )
    )

    is_star = (
        selected_leaderboard_entry.get(
            "is_star",
            False
        )
    )


    is_player = (
        selected_leaderboard_entry.get(
            "is_player",
            False
        )
    )

    title = menu_title_font.render(
        name,
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
            135
        )
    )

    game_surface.blit(
        title,
        title_rect
    )

    rating_surface = (
        option_label_font.render(
            f"Rating: {rating:,}",
            True,
            (
                0,
                0,
                0
            )
        )
    )

    # ==================================================
    # World #1 Marker
    # ==================================================

    if is_star:
        star_surface = (
            option_label_font.render(
                "WORLD #1",
                True,
                (
                    180,
                    120,
                    0
                )
            )
        )

        star_rect = (
            star_surface.get_rect(
                center=(
                    BASE_WIDTH // 2,
                    220
                )
            )
        )

        game_surface.blit(
            star_surface,
            star_rect
        )

    rating_rect = (
        rating_surface.get_rect(
            center=(
                BASE_WIDTH // 2,
                190
            )
        )
    )

    game_surface.blit(
        rating_surface,
        rating_rect
    )

    bio_panel_rect = pygame.Rect(
        330,
        240,
        705,
        280
    )

    pygame.draw.rect(
        game_surface,
        (
            250,
            250,
            250
        ),
        bio_panel_rect
    )

    pygame.draw.rect(
        game_surface,
        (
            0,
            0,
            0
        ),
        bio_panel_rect,
        3
    )

    if is_player:
        bio = (
            "This is you!"
        )



    details = [
        f"Country: {country}",
        f"Age: {age}",
        f"Hometown: {hometown}",
        f"Favorite Suit: {favorite_suit}",
    ]

    for index, detail in enumerate(
            details
    ):
        detail_surface = (
            option_value_font.render(
                detail,
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        game_surface.blit(
            detail_surface,
            (
                bio_panel_rect.x + 25,
                bio_panel_rect.y
                + 25
                + index * 30
            )
        )

    draw_wrapped_text(
        bio,
        option_label_font,
        (
            0,
            0,
            0
        ),
        pygame.Rect(
            bio_panel_rect.x + 25,
            bio_panel_rect.y + 160,
            bio_panel_rect.width - 50,
            bio_panel_rect.height - 185
        ),
        line_spacing=8
    )


    draw_button(
        career_subpage_back_rect,
        "Return to Rankings"
    )

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
        "https://www.solitaireleaderboards.net"
    )

    # ==================================================
    # Title
    # ==================================================

    title = menu_title_font.render(
        "INTERNATIONAL SOLITAIRE RANKINGS",
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

    player_rank = (
        get_player_leaderboard_rank()
    )

    player_info = (
        f"Your Rank: "
        f"#{player_rank}     "
        f"Rating: "
        f"{career_rating:,}"
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
                145
            )
        )
    )

    game_surface.blit(
        player_surface,
        player_rect
    )

    # ==================================================
    # Table
    # ==================================================

    leaderboard = (
        get_career_leaderboard()
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

    left_x = 215
    right_x = 700

    first_y = 190

    row_height = 45

    # Two columns of 10.
    for index, entry in enumerate(
        visible_entries
    ):

        if index < 10:

            column_x = (
                left_x
            )

            row_index = (
                index
            )

        else:

            column_x = (
                right_x
            )

            row_index = (
                index - 10
            )

        row_rect = pygame.Rect(
            column_x,
            first_y
            + row_index
            * row_height,
            450,
            38
        )

        # ----------------------------------------------
        # Highlight player
        # ----------------------------------------------

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
                row_rect.x + 8,
                row_rect.y + 8
            )
        )

        country = entry.get(
            "country",
            ""
        )

        if country:
            display_name = (
                f"{entry['name']} [{country}]"
            )

        else:
            display_name = (
                entry[
                    "name"
                ]
            )

        name_surface = (
            difficulty_detail_font.render(
                display_name,
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
                row_rect.x + 45,
                row_rect.y + 8
            )
        )

        # ----------------------------------------------
        # Rating
        # ----------------------------------------------

        rating_surface = (
            difficulty_detail_font.render(
                f"{entry['rating']:,}",
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
                        + 320
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
        # Monthly Rating Change
        # ----------------------------------------------

        rating_change = entry.get(
            "last_change",
            0
        )

        if rating_change > 0:

            change_text = (
                f"(+{rating_change})"
            )

            change_color = (
                25,
                140,
                45
            )

        elif rating_change < 0:

            change_text = (
                f"({rating_change})"
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
                difficulty_detail_font.render(
                    change_text,
                    True,
                    change_color
                )
            )

            game_surface.blit(
                change_surface,
                (
                    rating_rect.right + 8,
                    row_rect.y + 8
                )
            )

        # ----------------------------------------------
        # View Bio
        # ----------------------------------------------

        bio_surface = (
            difficulty_detail_font.render(
                "View Bio",
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
                        - 10
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
    # Player outside Top 20
    # ==================================================

    if (
        player_rank is not None
        and player_rank > 20
    ):

        outside_text = (
            f"You are currently "
            f"#{player_rank} with "
            f"{career_rating:,} Rating."
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

def draw_career_event():
    draw_career_placeholder_page(
        "CAREER EVENT",
        "Random career events will appear here."
    )

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


def get_poker_night_selection_image(
        game_id
):
    path = POKER_NIGHT_SELECTION_IMAGE_PATHS.get(
        game_id
    )

    if not path:
        return None

    cache_key = (
        game_id,
        POKER_NIGHT_SELECTION_IMAGE_SIZE
    )

    if cache_key in _poker_night_selection_image_cache:
        return _poker_night_selection_image_cache[
            cache_key
        ]

    try:
        image = pygame.image.load(
            path
        ).convert_alpha()

        image = pygame.transform.smoothscale(
            image,
            POKER_NIGHT_SELECTION_IMAGE_SIZE
        )

        _poker_night_selection_image_cache[
            cache_key
        ] = image

        return image

    except (
            pygame.error,
            FileNotFoundError
    ):
        return None


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


def draw_career_event_select():
    game_surface.fill(
        (
            20,
            120,
            35
        )
    )

    career_event_card_rects.clear()

    if career_event_entry is None:
        return

    activity_type = (
        career_event_entry.get(
            "activity_type"
        )
    )

    is_poker_night = (
        activity_type
        == CAREER_ACTIVITY_POKER_NIGHT
    )

    event_title = (
        CAREER_EVENT_NAMES.get(
            activity_type,
            "Card Event"
        )
    )

    title_surface = (
        options_title_font.render(
            event_title,
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
                78
            )
        )
    )

    game_surface.blit(
        title_surface,
        title_rect
    )

    subtitle_surface = (
        difficulty_detail_font.render(
            (
                "Choose your table"
                if is_poker_night
                else "Choose a game"
            ),
            True,
            (
                230,
                230,
                230
            )
        )
    )

    subtitle_rect = (
        subtitle_surface.get_rect(
            center=(
                BASE_WIDTH // 2,
                128
            )
        )
    )

    game_surface.blit(
        subtitle_surface,
        subtitle_rect
    )

    game_ids = (
        career_event_entry.get(
            "game_ids",
            []
        )
    )

    if is_poker_night:
        card_width = 300
        card_height = 330
        card_gap = 30
        card_y = 170
    else:
        card_width = 270
        card_height = 250
        card_gap = 35
        card_y = 220

    total_width = (
        card_width * len(game_ids)
        + card_gap
        * max(
            0,
            len(game_ids) - 1
        )
    )

    start_x = (
        BASE_WIDTH // 2
        - total_width // 2
    )

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
        "blind_mans_bluff": (
            "Blind Man's Bluff"
        ),
    }

    poker_descriptions = {
        "texas_holdem": (
            "Community cards, blinds,",
            "and no-limit betting."
        ),
        "seven_card_stud": (
            "Seven cards, exposed streets,",
            "and fixed-limit betting."
        ),
        "five_card_draw": (
            "Classic draw poker with",
            "one discard-and-draw round."
        ),
    }

    for index, game_id in enumerate(
            game_ids
    ):
        x = (
            start_x
            + index
            * (
                card_width
                + card_gap
            )
        )

        rect = pygame.Rect(
            x,
            card_y,
            card_width,
            card_height
        )

        unlocked = (
            is_game_unlocked(
                game_id
            )
        )

        hovered = (
            unlocked
            and game_mouse_pos is not None
            and rect.collidepoint(
                game_mouse_pos
            )
        )

        if not unlocked:
            fill_color = (
                55,
                55,
                58
            )

            border_color = (
                125,
                125,
                130
            )

            border_width = 3

        elif hovered:
            fill_color = (
                48,
                112,
                66
            )

            border_color = (
                255,
                225,
                120
            )

            border_width = 5

        else:
            fill_color = (
                38,
                92,
                53
            )

            border_color = (
                235,
                235,
                235
            )

            border_width = 3

        pygame.draw.rect(
            game_surface,
            fill_color,
            rect,
            border_radius=10
        )

        pygame.draw.rect(
            game_surface,
            border_color,
            rect,
            border_width,
            border_radius=10
        )

        game_name = (
            game_names.get(
                game_id,
                game_id
            )
        )

        is_high_stakes = (
                is_poker_night
                and game_id
                == career_event_entry.get(
                    "high_stakes_game_id"
                )
        )

        if is_poker_night:
            image_rect = pygame.Rect(
                rect.x + 6,
                rect.y + 17,
                *POKER_NIGHT_SELECTION_IMAGE_SIZE
            )

            image = (
                get_poker_night_selection_image(
                    game_id
                )
            )

            if image is not None:
                game_surface.blit(
                    image,
                    image_rect
                )

            else:
                pygame.draw.rect(
                    game_surface,
                    (
                        24,
                        28,
                        31
                    ),
                    image_rect,
                    border_radius=6
                )

                pygame.draw.rect(
                    game_surface,
                    (
                        115,
                        125,
                        130
                    ),
                    image_rect,
                    2,
                    border_radius=6
                )

                missing_surface = (
                    difficulty_detail_font.render(
                        "POKER NIGHT ART",
                        True,
                        (
                            185,
                            190,
                            195
                        )
                    )
                )

                game_surface.blit(
                    missing_surface,
                    missing_surface.get_rect(
                        center=image_rect.center
                    )
                )

            if not unlocked:
                lock_overlay = pygame.Surface(
                    image_rect.size,
                    pygame.SRCALPHA
                )
                lock_overlay.fill(
                    (
                        0,
                        0,
                        0,
                        145
                    )
                )
                game_surface.blit(
                    lock_overlay,
                    image_rect.topleft
                )

                required_level = (
                    get_game_unlock_level(
                        game_id
                    )
                )

                lock_surface = (
                    difficulty_detail_font.render(
                        f"LOCKED - LEVEL {required_level}",
                        True,
                        (
                            240,
                            240,
                            240
                        )
                    )
                )

                game_surface.blit(
                    lock_surface,
                    lock_surface.get_rect(
                        center=image_rect.center
                    )
                )

            if is_high_stakes:
                draw_poker_night_high_stakes_label(
                    game_surface,
                    (
                        rect.centerx,
                        rect.y + 230
                    )
                )

            description_lines = (
                poker_descriptions.get(
                    game_id,
                    (
                        "Poker Night game.",
                        ""
                    )
                )
            )

            description_y = (
                rect.y + 264
                if is_high_stakes
                else rect.y + 245
            )

            for line_index, line in enumerate(
                    description_lines
            ):
                if not line:
                    continue

                line_surface = (
                    difficulty_detail_font.render(
                        line,
                        True,
                        (
                            220,
                            223,
                            225
                        )
                    )
                )

                game_surface.blit(
                    line_surface,
                    line_surface.get_rect(
                        center=(
                            rect.centerx,
                            description_y
                            + line_index * 25
                        )
                    )
                )

        else:
            name_surface = (
                option_label_font.render(
                    game_name,
                    True,
                    (
                        255,
                        255,
                        255
                    )
                )
            )

            name_rect = (
                name_surface.get_rect(
                    center=(
                        rect.centerx,
                        rect.y + 60
                    )
                )
            )

            game_surface.blit(
                name_surface,
                name_rect
            )

            if unlocked:
                detail_text_by_game = {
                    "score_four":
                        "Make 24 using all four cards.",
                }

                detail_text = (
                    detail_text_by_game.get(
                        game_id,
                        "Coming soon"
                    )
                )

                detail_surface = (
                    difficulty_detail_font.render(
                        detail_text,
                        True,
                        (
                            210,
                            210,
                            210
                        )
                    )
                )

                detail_rect = (
                    detail_surface.get_rect(
                        center=(
                            rect.centerx,
                            rect.y + 185
                        )
                    )
                )

                game_surface.blit(
                    detail_surface,
                    detail_rect
                )

            else:
                required_level = (
                    get_game_unlock_level(
                        game_id
                    )
                )

                status_surface = (
                    difficulty_detail_font.render(
                        (
                            f"LOCKED - Level "
                            f"{required_level}"
                        ),
                        True,
                        (
                            230,
                            230,
                            230
                        )
                    )
                )

                status_rect = (
                    status_surface.get_rect(
                        center=(
                            rect.centerx,
                            rect.y + 125
                        )
                    )
                )

                game_surface.blit(
                    status_surface,
                    status_rect
                )

        career_event_card_rects.append(
            (
                rect,
                game_id
            )
        )

    draw_button(
        career_event_return_rect,
        "Return",
        font=difficulty_detail_font
    )

    if career_event_entry is not None:
        event_name = (
            CAREER_EVENT_NAMES.get(
                activity_type,
                "Event"
            )
        )

        draw_menu_button(
            career_event_end_rect,
            f"End {event_name}",
            game_mouse_pos,
            font=difficulty_detail_font
        )

    if not career_event_has_activity:
        message_surface = (
            difficulty_detail_font.render(
                "Play at least one game before ending the event.",
                True,
                (
                    220,
                    220,
                    220
                )
            )
        )

        message_rect = (
            message_surface.get_rect(
                center=(
                    career_event_end_rect.centerx,
                    career_event_end_rect.y - 25
                )
            )
        )

        game_surface.blit(
            message_surface,
            message_rect
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

    title = options_title_font.render(
        "SELECT PROFILE",
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
        330
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

    draw_button(
        pause_menu_rect,
        "Return to Menu"
    )

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

    prompt = option_label_font.render(
        "Return to the main menu?",
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

    background = (
        menu_background_drift_surfaces[
            selected_menu_background
        ]
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

    draw_menu_button(
        deal_verified_rect,
        "Verified Solvable",
        game_mouse_pos,
        selected=(
                game.deal_mode
                == "verified"
        ),
        font=option_value_font
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

    asset_ids = list(
        asset_data.keys()
    )

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

        if unlocked:
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
                    "LOCKED",
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
        overlay_alpha=115
    )

    # ----------------------------
    # Heading
    # ----------------------------

    profile_title_text = (
        "CREATE PROFILE"
        if profile_creation_mode
        else "PROFILE"
    )

    title = options_title_font.render(
        profile_title_text,
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
            85
        )
    )

    game_surface.blit(
        title,
        title_rect
    )

    if guest_mode:
        slot_text = "Guest"
    elif current_profile_slot is not None:
        slot_text = (
            f"Profile Slot {current_profile_slot}"
        )
    else:
        slot_text = "No Profile"

    slot_surface = option_value_font.render(
        slot_text,
        True,
        (
            255,
            215,
            0
        )
    )

    slot_rect = slot_surface.get_rect(
        center=(
            BASE_WIDTH // 2,
            130
        )
    )

    game_surface.blit(
        slot_surface,
        slot_rect
    )

    if not profile_creation_mode:
        draw_menu_button(
            profile_switch_rect,
            "Switch Profile",
            game_mouse_pos,
            font=option_value_font
        )

    # ----------------------------
    # Avatar frame
    # ----------------------------

    pygame.draw.rect(
        game_surface,
        (
            30,
            80,
            55
        ),
        profile_avatar_frame_rect
    )

    pygame.draw.rect(
        game_surface,
        (
            255,
            255,
            255
        ),
        profile_avatar_frame_rect,
        3
    )

    # ----------------------------
    # Avatar
    # ----------------------------

    avatar = get_profile_avatar()

    avatar_rect = avatar.get_rect(
        center=profile_avatar_frame_rect.center
    )

    game_surface.blit(
        avatar,
        avatar_rect
    )

    # ----------------------------
    # Name label
    # ----------------------------

    name_label = option_label_font.render(
        "Name",
        True,
        (
            255,
            255,
            255
        )
    )

    game_surface.blit(
        name_label,
        (
            590,
            185
        )
    )

    if profile_name_active:
        name_border_color = (
            255,
            215,
            0
        )
    else:
        name_border_color = (
            255,
            255,
            255
        )

    pygame.draw.rect(
        game_surface,
        name_border_color,
        profile_name_rect,
        3 if profile_name_active else 2
    )

    name_surface = (
        option_value_font.render(
            profile_name_text,
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
            profile_name_rect.x + 15,
            profile_name_rect.y + 15
        )
    )

    # ----------------------------
    # Gender
    # ----------------------------

    gender_label = (
        option_label_font.render(
            "Gender",
            True,
            (
                255,
                255,
                255
            )
        )
    )

    game_surface.blit(
        gender_label,
        (
            590,
            295
        )
    )

    pygame.draw.rect(
        game_surface,
        (
            50,
            110,
            75
        ),
        profile_gender_rect
    )

    pygame.draw.rect(
        game_surface,
        (
            255,
            255,
            255
        ),
        profile_gender_rect,
        2
    )

    gender_surface = (
        option_value_font.render(
            profile_gender.title(),
            True,
            (
                255,
                255,
                255
            )
        )
    )

    game_surface.blit(
        gender_surface,
        (
            profile_gender_rect.x + 15,
            profile_gender_rect.y + 15
        )
    )

    arrow = option_value_font.render(
        "V",
        True,
        (
            255,
            255,
            255
        )
    )

    game_surface.blit(
        arrow,
        (
            profile_gender_rect.right - 35,
            profile_gender_rect.y + 14
        )
    )

    # ----------------------------
    # Dropdown
    # ----------------------------

    if gender_dropdown_open:
        for index, gender in enumerate(
            gender_options
        ):
            rect = (
                profile_gender_option_rects[
                    index
                ]
            )

            pygame.draw.rect(
                game_surface,
                (
                    40,
                    90,
                    65
                ),
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
                1
            )

            label = (
                option_value_font.render(
                    gender.title(),
                    True,
                    (
                        255,
                        255,
                        255
                    )
                )
            )

            game_surface.blit(
                label,
                (
                    rect.x + 15,
                    rect.y + 13
                )
            )

    # ----------------------------
    # User details
    # ----------------------------

    unlocked_avatar_bases = {
        "base_01",
        "base_02",
        "base_03",
        "base_04",
        "base_05",
        "base_06",
        "base_07"
    }

    unlocked_avatar_eyes = {
        "eyes_01",
        "eyes_02",
        "eyes_03",
        "eyes_04",
        "eyes_05",
        "eyes_06",
        "eyes_07",
        "eyes_08",
        "eyes_09"
    }

    unlocked_avatar_hair = {
        "hair_01",
        "hair_02",
        "hair_03",
        "hair_04",
        "hair_05",
        "hair_06",
        "hair_07",
        "hair_08",
        "hair_09",
        "hair_10",
        "hair_11",
        "hair_12"
    }

    unlocked_avatar_glasses = {
        "glasses_01",
        "glasses_02",
        "glasses_03",
        "glasses_04",
        "glasses_05",
        "glasses_06"
    }

    unlocked_avatar_tops = {
        "top_01",
        "top_02",
        "top_03",
        "top_04",
        "top_05",
        "top_06"
    }

    details = [
        f"Level: {player_level}",
        f"XP: {player_xp:,}"
    ]

    if player_xp_to_next is not None:
        details[1] += (
            f" / "
            f"{player_xp_to_next:,}"
        )

    for index, text in enumerate(
        details
    ):
        surface = (
            option_label_font.render(
                text,
                True,
                (
                    255,
                    255,
                    255
                )
            )
        )

        game_surface.blit(
            surface,
            (
                285,
                605 + index * 35
            )
        )

    avatar_selector_rows = [
        (
            "Base",
            selected_avatar_base,
            avatar_base_options
        ),
        (
            "Eyes",
            selected_avatar_eyes,
            avatar_eye_options
        ),
        (
            "Hair",
            selected_avatar_hair,
            avatar_hair_options
        ),
        (
            "Glasses",
            selected_avatar_glasses,
            avatar_glasses_options
        ),
        (
            "Top",
            selected_avatar_top,
            avatar_top_options
        ),
    ]

    for index, (
            label_text,
            current_value,
            options
    ) in enumerate(
        avatar_selector_rows
    ):
        y = (
                avatar_selector_start_y
                + index * avatar_selector_gap
        )

        label_surface = option_value_font.render(
            label_text,
            True,
            (255, 255, 255)
        )

        game_surface.blit(
            label_surface,
            (
                985,
                y + 8
            )
        )

        draw_button(
            avatar_selector_left_rects[
                index
            ],
            "<"
        )

        draw_button(
            avatar_selector_right_rects[
                index
            ],
            ">"
        )

        if current_value is None:
            display_text = "None"
        else:
            current_index = (
                options.index(
                    current_value
                )
            )

            display_text = (
                f"{current_index + 1}"
                f"/{len(options)}"
            )

        value_surface = option_value_font.render(
            display_text,
            True,
            (255, 215, 0)
        )

        value_rect = value_surface.get_rect(
            center=(
                1122,
                y + 20
            )
        )

        game_surface.blit(
            value_surface,
            value_rect
        )

    # ----------------------------
    # Buttons
    # ----------------------------

    save_button_text = (
        "Create Profile"
        if profile_creation_mode
        else "Save"
    )

    draw_menu_button(
        profile_save_rect,
        save_button_text,
        game_mouse_pos,
        font=option_value_font
    )

    back_button_text = (
        "Cancel"
        if profile_creation_mode
        else "Back"
    )

    draw_menu_button(
        profile_back_rect,
        back_button_text,
        game_mouse_pos,
        font=difficulty_detail_font
    )

    # ----------------------------
    # Status message
    # ----------------------------

    if profile_message:
        message_surface = (
            option_value_font.render(
                profile_message,
                True,
                (
                    255,
                    255,
                    255
                )
            )
        )

        message_rect = (
            message_surface.get_rect(
                center=(
                    BASE_WIDTH // 2,
                    740
                )
            )
        )

        game_surface.blit(
            message_surface,
            message_rect
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
    game_surface.fill(
        (
            20,
            190,
            20
        )
    )

    if current_level_up_data is None:
        return

    level = current_level_up_data[
        "level"
    ]

    unlocks = current_level_up_data[
        "unlocks"
    ]

    # ----------------------------
    # Main heading
    # ----------------------------

    heading = menu_title_font.render(
        f"You've reached level {level}!",
        True,
        (
            255,
            255,
            255
        )
    )

    heading_rect = heading.get_rect(
        center=(
            BASE_WIDTH // 2,
            70
        )
    )

    game_surface.blit(
        heading,
        heading_rect
    )

    # ----------------------------
    # Unlock heading
    # ----------------------------

    subheading = options_title_font.render(
        "you've unlocked:",
        True,
        (
            255,
            255,
            255
        )
    )

    subheading_rect = (
        subheading.get_rect(
            center=(
                BASE_WIDTH // 2,
                170
            )
        )
    )

    game_surface.blit(
        subheading,
        subheading_rect
    )

    # ----------------------------
    # Unlock cards
    # ----------------------------

    if unlocks:
        card_width = 330
        card_height = 270
        gap = 105

        total_width = (
            len(unlocks)
            * card_width
            + (
                len(unlocks) - 1
            ) * gap
        )

        start_x = (
            BASE_WIDTH
            - total_width
        ) // 2

        for index, (
            unlock_type,
            asset_id
        ) in enumerate(unlocks):

            card_x = (
                start_x
                + index
                * (
                    card_width
                    + gap
                )
            )

            card_rect = pygame.Rect(
                card_x,
                275,
                card_width,
                card_height
            )

            # White card background
            pygame.draw.rect(
                game_surface,
                (
                    245,
                    245,
                    245
                ),
                card_rect
            )

            pygame.draw.rect(
                game_surface,
                (
                    50,
                    50,
                    50
                ),
                card_rect,
                2
            )

            (
                asset_data,
                asset_surface,
                category_name
            ) = get_unlock_asset_data(
                unlock_type,
                asset_id
            )

            # ------------------------
            # Preview
            # ------------------------

            if asset_surface is not None:
                preview = (
                    scale_surface_to_fit(
                        asset_surface,
                        card_width - 40,
                        160
                    )
                )

                preview_rect = (
                    preview.get_rect(
                        center=(
                            card_rect.centerx,
                            card_rect.y + 100
                        )
                    )
                )

                game_surface.blit(
                    preview,
                    preview_rect
                )

            # ------------------------
            # Category label
            # ------------------------

            category_surface = (
                option_value_font.render(
                    category_name,
                    True,
                    (
                        50,
                        50,
                        50
                    )
                )
            )

            category_rect = (
                category_surface.get_rect(
                    center=(
                        card_rect.centerx,
                        card_rect.y + 195
                    )
                )
            )

            game_surface.blit(
                category_surface,
                category_rect
            )

            # ------------------------
            # Asset name
            # ------------------------

            name_surface = (
                option_label_font.render(
                    asset_data["name"],
                    True,
                    (
                        0,
                        0,
                        0
                    )
                )
            )

            name_rect = (
                name_surface.get_rect(
                    center=(
                        card_rect.centerx,
                        card_rect.y + 230
                    )
                )
            )

            game_surface.blit(
                name_surface,
                name_rect
            )

    else:
        no_unlock_text = (
            option_label_font.render(
                "No cosmetic unlocks this level.",
                True,
                (
                    255,
                    255,
                    255
                )
            )
        )

        no_unlock_rect = (
            no_unlock_text.get_rect(
                center=(
                    BASE_WIDTH // 2,
                    400
                )
            )
        )

        game_surface.blit(
            no_unlock_text,
            no_unlock_rect
        )

    # ----------------------------
    # Current XP
    # ----------------------------

    if player_xp_to_next is not None:
        xp_string = (
            f"{player_name}'s XP: "
            f"{player_xp:,} / "
            f"{player_xp_to_next:,}"
        )

    else:
        xp_string = (
            f"{player_name}'s XP: "
            f"{player_xp:,} / MAX"
        )

    xp_surface = option_label_font.render(
        xp_string,
        True,
        (
            0,
            0,
            0
        )
    )

    xp_rect = xp_surface.get_rect(
        center=(
            BASE_WIDTH // 2,
            650
        )
    )

    game_surface.blit(
        xp_surface,
        xp_rect
    )

    # ----------------------------
    # Continue prompt
    # ----------------------------

    continue_surface = (
        option_value_font.render(
            "Press any key to continue",
            True,
            (
                255,
                255,
                255
            )
        )
    )

    continue_rect = (
        continue_surface.get_rect(
            center=(
                BASE_WIDTH // 2,
                720
            )
        )
    )

    game_surface.blit(
        continue_surface,
        continue_rect
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

                elif debug_action == ACTION_BLACKJACK:
                    audio.play_sound("button_click")
                    debug_open_blackjack()

                elif debug_action == ACTION_ROULETTE:
                    audio.play_sound("button_click")
                    debug_open_roulette()

                elif debug_action == ACTION_TEXAS_HOLDEM:
                    audio.play_sound("button_click")
                    debug_prepare_poker_night()
                    start_texas_holdem_session()

                elif debug_action == ACTION_FIVE_CARD_DRAW:
                    audio.play_sound("button_click")
                    debug_prepare_poker_night()
                    start_five_card_draw_session()

                elif debug_action == ACTION_SEVEN_CARD_STUD:
                    audio.play_sound("button_click")
                    debug_prepare_poker_night()
                    start_seven_card_stud_session()

                # ==========================================
                # Progression controls
                # ==========================================

                elif debug_action == ACTION_ADD_CASH:
                    audio.play_sound("button_click")
                    career_cash += 5000
                    print("Cash:", career_cash)

                elif debug_action == ACTION_ZERO_CASH:
                    audio.play_sound("button_click")
                    career_cash = 0
                    print("Cash:", career_cash)

                elif debug_action == ACTION_ADD_RATING:
                    audio.play_sound("button_click")
                    career_rating += 100
                    print("Rating:", career_rating)

                elif debug_action == ACTION_SUB_RATING:
                    audio.play_sound("button_click")
                    career_rating = max(100, career_rating - 100)
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

                    current_game_mode = (
                        "free"
                    )

                    # KEEP YOUR EXISTING FREE PLAY
                    # DESTINATION/ACTION HERE


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
        # CAREER HUB
        # ==========================================

        elif current_state == STATE_CAREER_HUB:

            if (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
            ):

                hub_action = career_hub_controls.get_action(game_mouse_pos)
                if hub_action is not None:
                    audio.play_sound("button_click")
                    if hub_action == "skip_to_day":
                        skip_to_selected_career_day()
                    elif hub_action == "save":
                        save_career_from_hub()
                    elif hub_action == "switch":
                        begin_career_profile_switch()
                    elif hub_action == "profile":
                        profile_return_state = STATE_CAREER_HUB
                        profile_name_text = player_name
                        profile_name_active = False
                        gender_dropdown_open = False
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
                                CAREER_ACTIVITY_NICHE_NIGHT
                        ):

                            career_event_entry = career_current_schedule[
                                career_day_of_month - 1
                                ]

                            career_event_has_activity = False

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

                            pay = (
                                complete_career_work_day()
                            )

                            print(
                                "Career work complete:",
                                get_career_job_name(),
                                f"+${pay}"
                            )

                        # ----------------------------
                        # Random event
                        # ----------------------------

                        elif (
                                activity_type
                                == CAREER_ACTIVITY_EVENT
                        ):
                            current_state = (
                                STATE_CAREER_EVENT
                            )

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

                    score_four_game.start_solo_session()

                    current_state = (
                        STATE_SCORE_FOUR
                    )

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

                    current_state = (
                        STATE_CAREER_EVENT_SELECT
                    )


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
                            )
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

                        current_state = (
                            STATE_CAREER_EVENT_SELECT
                        )

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

                        current_state = (
                            STATE_CAREER_EVENT_SELECT
                        )

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

                        current_state = (
                            STATE_CAREER_EVENT_SELECT
                        )

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

                        if (
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

                    current_state = (
                        STATE_CAREER_EVENT_SELECT
                    )

        elif current_state == STATE_BLACKJACK:

            if (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):

                # ==========================================
                # Change Bet button
                # ==========================================

                if blackjack_change_bet_rect.collidepoint(
                        game_mouse_pos
                ):

                    audio.play_sound(
                        "button_click"
                    )

                    blackjack_bet_dropdown_open = not (
                        blackjack_bet_dropdown_open
                    )

                # ==========================================
                # Dropdown choices
                # ==========================================

                elif blackjack_bet_dropdown_open:

                    bet_choices = [
                        0.01,
                        0.02,
                        0.05,
                        0.10,
                        1.0,
                    ]

                    bet_option_clicked = False

                    for index, rect in enumerate(
                            blackjack_bet_dropdown_rects
                    ):

                        if rect.collidepoint(
                                game_mouse_pos
                        ):
                            blackjack_selected_bet_percentage = (
                                bet_choices[
                                    index
                                ]
                            )

                            blackjack_bet_dropdown_open = False

                            audio.play_sound(
                                "button_click"
                            )

                            bet_option_clicked = True

                            break

                    # Clicking anywhere outside the
                    # dropdown simply closes it.
                    if not bet_option_clicked:
                        blackjack_bet_dropdown_open = False

                # ==========================================
                # Hit
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
                # Double
                # ==========================================

                elif (
                        blackjack_game.can_double_down()
                        and career_cash >= blackjack_game.bet
                        and blackjack_double_rect.collidepoint(
                    game_mouse_pos
                )
                ):

                    additional_bet = (
                        blackjack_game.bet
                    )

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

                    current_state = (
                        STATE_CAREER_EVENT_SELECT
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

                    current_state = (
                        STATE_CAREER_EVENT_SELECT
                    )

        elif current_state == STATE_SCORE_FOUR:

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

                if score_four_game.session_complete:

                    if score_four_complete_rect.collidepoint(

                            menu_mouse_pos

                    ):

                        if not score_four_game.reward_claimed:
                            career_rating += 60

                            score_four_game.reward_claimed = True

                            career_event_has_activity = True

                        audio.play_sound(

                            "button_click"

                        )

                        current_state = (
                            STATE_CAREER_EVENT_SELECT
                        )

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

                        if not score_four_game.reward_claimed:
                            career_rating += (
                                score_four_game.competitive_reward
                            )

                            score_four_game.reward_claimed = True

                            career_event_has_activity = True

                        audio.play_sound(
                            "button_click"
                        )

                        current_state = (
                            STATE_CAREER_EVENT_SELECT
                        )

                    continue

                # ==========================================
                # Competitive round result input lock
                # ==========================================

                if (
                        score_four_game.mode == "competitive"
                        and score_four_game.round_complete
                ):
                    continue

                # ------------------------------------------
                # Number tiles
                # ------------------------------------------

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
                            audio.play_sound(
                                "button_click"
                            )

                    # --------------------------------------
                    # Undo
                    # --------------------------------------

                    elif score_four_undo_rect.collidepoint(
                            menu_mouse_pos
                    ):

                        score_four_game.undo()

                    # --------------------------------------
                    # Exit
                    # --------------------------------------

                    elif score_four_exit_rect.collidepoint(
                            menu_mouse_pos
                    ):

                        current_state = (
                            STATE_CAREER_EVENT_SELECT
                        )

        elif current_state == STATE_HOW_TO_PLAY:

            if (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):

                click_handled = False

                # ==================================================
                # Category expand / collapse
                # ==================================================

                for (
                        category_id,
                        rect
                ) in help_category_rects.items():

                    if rect.collidepoint(
                            game_mouse_pos
                    ):
                        audio.play_sound(
                            "button_click"
                        )

                        was_expanded = (
                            help_expanded_categories.get(
                                category_id,
                                False
                            )
                        )

                        # Close every category first
                        for other_category_id in (
                                help_expanded_categories
                        ):
                            help_expanded_categories[
                                other_category_id
                            ] = False

                        # If this category was closed,
                        # open it now.
                        if not was_expanded:
                            help_expanded_categories[
                                category_id
                            ] = True

                        click_handled = True

                        break

                # ==================================================
                # Page selection
                # ==================================================

                if not click_handled:

                    for (
                            page_id,
                            rect
                    ) in help_page_rects.items():

                        if rect.collidepoint(
                                game_mouse_pos
                        ):
                            audio.play_sound(
                                "button_click"
                            )

                            help_current_page = (
                                page_id
                            )

                            click_handled = True

                            break

                # ==================================================
                # Return
                # ==================================================

                if (
                        not click_handled
                        and how_to_play_back_rect
                        .collidepoint(
                    game_mouse_pos
                )
                ):
                    audio.play_sound(
                        "button_click"
                    )

                    current_state = (
                        STATE_MENU
                    )

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
                    get_career_leaderboard_total_pages()
                )

                bio_clicked = False

                # ==========================================
                # Bio links
                # ==========================================

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

                # ==========================================
                # Previous Page
                # ==========================================

                if (
                        not bio_clicked
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
                        STATE_CAREER_HUB
                    )

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

                for (
                        rect,
                        game_id
                ) in career_event_card_rects:

                    if rect.collidepoint(
                            menu_mouse_pos
                    ):

                        game_clicked = True

                        # ======================================
                        # Locked game
                        # ======================================

                        if not is_game_unlocked(
                                game_id
                        ):
                            break

                        audio.play_sound(
                            "button_click"
                        )

                        # ======================================
                        # SCORE-FOUR
                        # ======================================

                        if game_id == "score_four":

                            current_state = (
                                STATE_SCORE_FOUR_MODE_SELECT
                            )

                        # ======================================
                        # BLACKJACK
                        # ======================================

                        elif game_id == "blackjack":

                            blackjack_selected_bet_percentage = (
                                None
                            )

                            blackjack_bet_dropdown_open = False

                            blackjack_session_net = 0

                            blackjack_dealer_npc = (
                                get_random_blackjack_dealer()
                            )

                            current_state = (
                                STATE_BLACKJACK_BET
                            )

                        # ======================================
                        # ROULETTE
                        # ======================================

                        elif game_id == "roulette":

                            roulette_session_net = 0

                            roulette_game.reset_round()

                            current_state = (
                                STATE_ROULETTE
                            )

                        # ======================================
                        # TEXAS HOLD'EM
                        # ======================================

                        elif game_id == "texas_holdem":

                            current_state = (

                                STATE_TEXAS_HOLDEM_BUY_IN

                            )

                        # ======================================
                        # SEVEN-CARD STUD
                        # ======================================

                        elif game_id == "seven_card_stud":

                            current_state = (

                                STATE_SEVEN_CARD_STUD_BUY_IN

                            )

                        # ======================================
                        # FIVE-CARD DRAW
                        # ======================================

                        elif game_id == "five_card_draw":

                            current_state = (

                                STATE_FIVE_CARD_DRAW_BUY_IN

                            )

                        # ======================================
                        # NOT IMPLEMENTED
                        # ======================================

                        else:

                            print(
                                "Career game not implemented yet:",
                                game_id
                            )

                        break

                # ==============================================
                # EVENT MENU BUTTONS
                # ==============================================

                if not game_clicked:

                    # ==========================================
                    # Return
                    # ==========================================

                    if career_event_return_rect.collidepoint(
                            menu_mouse_pos
                    ):

                        audio.play_sound(
                            "button_click"
                        )

                        current_state = (
                            STATE_CAREER_HUB
                        )

                    # ==========================================
                    # End event
                    # ==========================================

                    elif (
                            career_event_end_rect.collidepoint(
                                menu_mouse_pos
                            )
                            and career_event_has_activity
                    ):

                        audio.play_sound(
                            "button_click"
                        )

                        build_career_event_summary()

                        current_state = (
                            STATE_CAREER_EVENT_SUMMARY
                        )


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

                        current_state = (

                            STATE_MODE_SELECT

                        )

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
                    audio.play_sound(
                        "button_click"
                    )
                    game.set_deal_mode(
                        "verified"
                    )

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


        # ==========================================
        # LEVEL UP
        # ==========================================

        elif current_state == STATE_LEVEL_UP:

            if (
                    event.type == pygame.KEYDOWN
                    or event.type == pygame.MOUSEBUTTONDOWN
            ):
                audio.play_sound(
                    "button_click"
                )

                advance_level_up_screen()


        # ==========================================
        # PROFILE
        # ==========================================

        elif current_state == STATE_PROFILE:

            # ==========================================
            # KEYBOARD INPUT
            # ==========================================

            if event.type == pygame.KEYDOWN:

                if profile_name_active:

                    if event.key == pygame.K_BACKSPACE:

                        profile_name_text = (
                            profile_name_text[:-1]
                        )

                    elif event.key == pygame.K_RETURN:

                        profile_name_active = False

                    elif event.key == pygame.K_ESCAPE:

                        profile_name_active = False

                    else:

                        if (
                                event.unicode
                                and event.unicode.isprintable()
                                and len(profile_name_text) < 20
                        ):
                            profile_name_text += (
                                event.unicode
                            )

            # ==========================================
            # MOUSE INPUT
            # ==========================================

            elif (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_mouse_pos is not None
            ):

                # ----------------------------
                # Name box
                # ----------------------------

                if profile_name_rect.collidepoint(
                        game_mouse_pos
                ):

                    profile_name_active = True

                    if profile_name_text == "Player":
                        profile_name_text = ""

                else:

                    profile_name_active = False

                # ----------------------------
                # Gender dropdown
                # ----------------------------

                if profile_gender_rect.collidepoint(
                        game_mouse_pos
                ):

                    gender_dropdown_open = (
                        not gender_dropdown_open
                    )

                elif gender_dropdown_open:

                    gender_selected = False

                    for index, rect in enumerate(
                            profile_gender_option_rects
                    ):

                        if rect.collidepoint(
                                game_mouse_pos
                        ):
                            profile_gender = (
                                gender_options[index]
                            )

                            gender_dropdown_open = False
                            gender_selected = True

                            audio.play_sound(
                                "button_click"
                            )

                            break

                    if not gender_selected:
                        gender_dropdown_open = False

                # ----------------------------
                # Avatar selectors
                # ----------------------------

                avatar_selector_clicked = False

                for index in range(5):

                    if avatar_selector_left_rects[
                        index
                    ].collidepoint(
                        game_mouse_pos
                    ):

                        direction = -1
                        avatar_selector_clicked = True

                    elif avatar_selector_right_rects[
                        index
                    ].collidepoint(
                        game_mouse_pos
                    ):

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

                    audio.play_sound(
                        "button_click"
                    )

                    break

                # ----------------------------
                # Save / Create
                # ----------------------------

                if (
                        not avatar_selector_clicked
                        and profile_save_rect.collidepoint(
                    game_mouse_pos
                )
                ):

                    player_name = (
                        profile_name_text.strip()
                    )

                    if not player_name:
                        player_name = "Player"

                    profile_name_text = (
                        player_name
                    )

                    if profile_creation_mode:

                        current_profile_slot = (
                            pending_profile_slot
                        )

                        guest_mode = False

                        save_profile(
                            build_profile_save_data(),
                            current_profile_slot
                        )

                        profile_creation_mode = False
                        pending_profile_slot = None
                        profile_message = ""

                        audio.play_sound(
                            "button_click"
                        )

                        finish_profile_selection()

                    else:

                        if not guest_mode:

                            save_profile(
                                build_profile_save_data(),
                                current_profile_slot
                            )

                            profile_message = (
                                f"Profile saved to slot "
                                f"{current_profile_slot}."
                            )

                        else:

                            profile_message = (
                                "Guest mode does not save progress."
                            )

                        profile_name_active = False

                        audio.play_sound(
                            "button_click"
                        )

                # ----------------------------
                # Switch Profile
                # ----------------------------

                elif (
                        not profile_creation_mode
                        and profile_switch_rect.collidepoint(
                    game_mouse_pos
                )
                ):

                    audio.play_sound(
                        "button_click"
                    )

                    if profile_return_state == STATE_CAREER_HUB:
                        begin_career_profile_switch()
                        continue
                    profile_select_return_state = STATE_MENU
                    profile_name_active = False
                    gender_dropdown_open = False
                    profile_message = ""

                    pending_profile_slot = None
                    profile_creation_mode = False

                    confirm_delete_profile = False
                    profile_delete_slot = None

                    current_state = (
                        STATE_PROFILE_SELECT
                    )

                # ----------------------------
                # Back / Cancel
                # ----------------------------

                elif profile_back_rect.collidepoint(
                        game_mouse_pos
                ):

                    audio.play_sound(
                        "button_click"
                    )

                    profile_name_active = False

                    if profile_creation_mode:

                        profile_creation_mode = False
                        pending_profile_slot = None

                        current_state = (
                            STATE_PROFILE_SELECT
                        )

                    else:

                        if profile_return_state == STATE_CAREER_HUB:
                            save_career_from_hub()
                        current_state = profile_return_state


        # ==========================================
        # PLAYING
        # ==========================================

        elif current_state == STATE_PLAYING:

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

                        current_state = (
                            STATE_MENU
                        )

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

            # ----------------------------
            # Decide where this game
            # should return afterward.
            # ----------------------------

            if current_game_mode == "career":
                post_round_return_state = (
                    STATE_CAREER_HUB
                )

            else:
                post_round_return_state = (
                    STATE_MENU
                )

            # ----------------------------
            # Apply all rewards
            # ----------------------------

            last_progression_result = (
                apply_round_rewards(
                    round_recap_data
                )
            )

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

    elif current_state == STATE_HOW_TO_PLAY:

        draw_how_to_play()

    elif current_state == STATE_MODE_SELECT:

        draw_mode_select()




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

        if game_pause_menu_open:
            draw_game_pause_menu()

        elif confirm_return_to_menu:
            draw_return_confirmation()

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