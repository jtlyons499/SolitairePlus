"""Start-up: what the old main.py did before its main loop, in the same order.

app/loop.py imports this module near its top, where the old main.py's start-up code ran (only the
shared state and the achievement popup's drawing are imported before it); importing it runs the
start-up sequence. Many modules run start-up code when they are first imported (they load images and
fonts, build tables and engines, draw seeded random numbers), so this module imports them in the
order in which the old main.py first imported them, and sets the shared state defaults (app/state.py)
at the same points as before. Moving a line up or down can change the game: for example, the
Solitaire engine (games/solitaire/table.py) deals a first hand when it is built, and the screenshot
harness compares those seeded draws.

The names live in their own modules; this module only runs the sequence and defines nothing that
other modules use.
"""
import pygame

from solitaireplus.app import state, state_names

# ==================================================
# Modules, in the order the old main.py imported them
# ==================================================

import solitaireplus.app.paths
import solitaireplus.app.update_check
from solitaireplus.career.alien_night import new_alien_story
import solitaireplus.games.solitaire.restart
import solitaireplus.profile.save_data
import solitaireplus.games.solitaire.screen  # start-up code of this module runs here, as before
import solitaireplus.profile.avatar
import solitaireplus.career.asset_images
from solitaireplus.career.activities import new_story
import solitaireplus.career.activities_ui
import solitaireplus.app.cosmetic_assets
import solitaireplus.career.events.press_interview
import solitaireplus.career.session_summary
import solitaireplus.profile.unlocks
import solitaireplus.app.multiplayer_launcher
import solitaireplus.menus.main_menu  # start-up code of this module runs here, as before
import solitaireplus.career.event_progress
import solitaireplus.career.time_warp
from solitaireplus.career.case_opening import new_case_state
import solitaireplus.career.case_opening_ui
from solitaireplus.games.arcade.support import make_default_arcade_state
import solitaireplus.games.poker.bluff_presentation
import solitaireplus.games.poker.recap
from solitaireplus.games.poker.learning import new_learning
import solitaireplus.career.hub_controls
import solitaireplus.npc.personality
import solitaireplus.npc.personality_ui
import solitaireplus.app.audio
import solitaireplus.games.solitaire.rules
import solitaireplus.games.cards.score_four
import solitaireplus.games.cards.crazy_eights
import solitaireplus.games.cards.crazy_eights_ui
import solitaireplus.games.cards.bango
import solitaireplus.games.cryptid.ui
from solitaireplus.games.cryptid.collection import new_collection
import solitaireplus.games.cards.bango_ui
import solitaireplus.games.casino.blackjack
import solitaireplus.games.arcade.king_pong
import solitaireplus.games.arcade.battle_bosses
import solitaireplus.games.arcade.battle_bosses_game
import solitaireplus.games.arcade.ace_invaders
import solitaireplus.games.arcade.ace_invaders_game
import solitaireplus.games.arcade.suit_snake
import solitaireplus.games.arcade.suit_snake_game
import solitaireplus.games.dead_mans_hand.game
import solitaireplus.games.poker.holdem
import solitaireplus.games.poker.holdem_ui
import solitaireplus.games.poker.holdem_chat
import solitaireplus.games.poker.five_card_draw
import solitaireplus.games.poker.five_card_draw_ui
import solitaireplus.games.poker.seven_card_stud
import solitaireplus.games.poker.seven_card_stud_ui
from solitaireplus.npc.manager import get_npcs_missing_portraits
import solitaireplus.games.casino.roulette
import solitaireplus.games.casino.roulette_ui
import solitaireplus.games.casino.horse_races
import solitaireplus.games.casino.horse_races_ui
import solitaireplus.games.casino.faro
import solitaireplus.games.casino.faro_ui
import solitaireplus.games.poker.five_o
import solitaireplus.games.poker.five_o_ui
import solitaireplus.games.poker.blind_mans_bluff
import solitaireplus.games.poker.blind_mans_bluff_ui
import solitaireplus.debug.game_mode
import solitaireplus.debug.poker_select
import solitaireplus.games.solitaire.head_to_head
import solitaireplus.games.solitaire.head_to_head_ui
import solitaireplus.debug.menu
import solitaireplus.profile.saves
from solitaireplus.career.ratings import make_player_rating_bundle
import solitaireplus.career.rating_events
import solitaireplus.career.npc_world
import solitaireplus.career.npc_development
import solitaireplus.npc.portraits
import solitaireplus.career.fans
import solitaireplus.career.world_flavor
from solitaireplus.profile.achievements import make_default_achievement_state, register_optional_cosmetics
import solitaireplus.menus.achievements_screen
import solitaireplus.career.events.autographs
import solitaireplus.career.news
import solitaireplus.app.help_history
from solitaireplus.app.settings import (
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
)
import solitaireplus.games.solitaire.head_to_head_screen
import solitaireplus.career.career_rewards
import solitaireplus.career.career_saving
from solitaireplus.profile import cosmetics

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
# Register their metadata before the image catalogs are built.
cosmetics.register_reward_cosmetics()

# ==================================================
# PYGAME INITIALIZATION
# ==================================================

pygame.display.init()
pygame.font.init()
from solitaireplus.app import sounds  # start-up code of this module runs here, as it did in main.py
from solitaireplus.games.cards import score_four_tiers  # start-up code of this module runs here, as before
from solitaireplus.games.poker import table_stakes  # start-up code of this module runs here, as before
from solitaireplus.games.arcade import machine_music  # start-up code of this module runs here, as before
from solitaireplus.career import activity_screen  # start-up code of this module runs here, as before
from solitaireplus.menus import help_screen  # start-up code of this module (and of menus/help_content.py) runs here
from solitaireplus.career import web_pages  # start-up code of this module runs here, as before
from solitaireplus.career import calendar  # start-up code of this module runs here, as before
from solitaireplus.career import career_names  # start-up code of this module runs here, as before
from solitaireplus.career import real_estate_screen  # start-up code of this module runs here, as before
from solitaireplus.career import training  # start-up code of this module runs here, as before
from solitaireplus.career.events import night  # start-up code of this module runs here, as before
import solitaireplus.npc.portrait_ui
from solitaireplus.career import leaderboard_engine  # start-up code of this module runs here, as before
from solitaireplus.app import window  # start-up code of this module runs here, as it did in main.py
window.open_window()
from solitaireplus.ui import backgrounds  # start-up code of this module runs here, as it did in main.py
state.options_return_state = state_names.STATE_MENU
state.customize_return_state = state_names.STATE_MENU
state.profile_return_state = state_names.STATE_MENU
state.profile_select_return_state = state_names.STATE_MENU

# ==================================================
# GAME
# ==================================================

from solitaireplus.games.solitaire import table  # builds the Solitaire engine (table.game) here, as before

state.player_name = DEFAULT_PLAYER_NAME

state.player_level = DEFAULT_LEVEL
state.player_xp = DEFAULT_XP
state.player_xp_to_next = DEFAULT_XP_TO_NEXT

from solitaireplus.games.casino import blackjack_screen  # start-up code of this module runs here, as before
from solitaireplus.games.cards import score_four_screen  # start-up code of this module runs here, as before
from solitaireplus.games.cards import crazy_eights_screen  # start-up code of this module runs here, as before
from solitaireplus.games.cards import bango_screen  # start-up code of this module runs here, as before
from solitaireplus.games.poker import holdem_screen  # start-up code of this module runs here, as before
from solitaireplus.games.poker import five_card_draw_screen  # start-up code of this module runs here, as before
from solitaireplus.games.poker import seven_card_stud_screen  # start-up code of this module runs here, as before
from solitaireplus.games.casino import roulette_screen  # start-up code of this module runs here, as before
from solitaireplus.games.casino import horse_races_screen  # start-up code of this module runs here, as before
from solitaireplus.career import case_opening_screen  # start-up code of this module runs here, as before
state.case_collection_state = new_case_state()
from solitaireplus.games.cryptid import collection_screen  # start-up code of this module runs here, as before
state.cryptid_collection_state = new_collection()
state.career_poker_learning = new_learning()
from solitaireplus.games.casino import faro_screen  # start-up code of this module runs here, as before
from solitaireplus.games.poker import five_o_screen  # start-up code of this module runs here, as before
from solitaireplus.games.poker import blind_mans_bluff_screen  # start-up code of this module runs here, as before
from solitaireplus.games.arcade import machine_screens  # start-up code of this module runs here, as before
from solitaireplus.games.dead_mans_hand import game_screen  # start-up code of this module runs here, as before
state.dead_mans_hand_return_state = state_names.STATE_DEBUG_MENU
state.arcade_state = make_default_arcade_state()

state.career_ratings = make_player_rating_bundle(state.career_rating)

# ==================================================
# ACHIEVEMENTS
# ==================================================
state.achievement_state = make_default_achievement_state()
state.career_bigfoot_story = new_story()
state.career_alien_story = new_alien_story()
from solitaireplus.career.events import event_screen  # start-up code of this module runs here, as before
from solitaireplus.career import jobs_screen  # start-up code of this module runs here, as before
from solitaireplus.npc import game_portraits  # NPC portraits (defined here in the old main.py)

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

table.sync_selected_cosmetics()
from solitaireplus.app import fonts  # start-up code of this module runs here, as it did in main.py
from solitaireplus.menus import customize  # start-up code of this module runs here, as before
from solitaireplus.menus import mode_select  # start-up code of this module runs here, as before
from solitaireplus.menus import free_play_select  # start-up code of this module (the Free Play grid) runs here
from solitaireplus.career.events import summary_screen  # start-up code of this module runs here, as before
from solitaireplus.career.events import event_select_screen  # start-up code of this module runs here, as before
from solitaireplus.games.arcade import hub_screens  # start-up code of this module runs here, as before
from solitaireplus.games.arcade import machine_select  # start-up code of this module runs here, as before
from solitaireplus.career import news_screen  # start-up code of this module runs here, as before
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
from solitaireplus.career import hub_screen  # start-up code of this module (and the hub controls) runs here

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

# ==================================================
# CUSTOMIZATION STATE
# ==================================================

state.customize_category = customize.CUSTOMIZE_BACKGROUNDS

# ==================================================
# STATE
# ==================================================

state.current_state = state_names.STATE_SPLASH

state.post_round_return_state = state_names.STATE_MENU
from solitaireplus.profile import leveling  # start-up code of this module runs here, as before

print(
    "NPCs missing portraits:",
    len(
        get_npcs_missing_portraits()
    )
)
from solitaireplus.ui import text as ui_text  # start-up code of this module runs here, as it did in main.py
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
from solitaireplus.ui import images  # UI pictures (defined here in the old main.py)
from solitaireplus.app import game_globals  # game_namespace() (defined here in the old main.py)
