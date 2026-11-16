"""Klondike Solitaire rules engine: the Game class (one table: tableau, stock, waste, foundations).

Game is assembled from topic mixins in this package (one class split across modules; every
method keeps its name and works on the same Game instance):
    constants.py   base window size, colours, tableau layout, animation timings
    layout.py      LayoutMixin: tableau spacing, card rects, what is under the mouse
    moves.py       MovesMixin: move rules, stock, tableau / waste / foundation moves, auto-moves, undo
    scoring.py     ScoringMixin: round tracking, score, XP, round summary, win detection
    hints.py       HintMixin: the hint system
    auto_solve.py  AutoSolveMixin: auto-solve
    animation.py   AnimationMixin: card flip and victory animations
    drawing.py     DrawingMixin: card art and drawing the table
    controls.py    ControlsMixin: mouse input and events
This module keeps the constructor, deal mode, new games, difficulty and Career challenge rules.

Every module-level name rules.py had is still importable from here (BASE_WIDTH and BASE_HEIGHT
are imported from here by most screens). The imports below stay in their original order: this
module is imported early in start-up (app/window.py), so it loads the same modules in the same order.
"""
from solitaireplus.app import paths
import pygame
import copy
import random
import math

from solitaireplus.games.solitaire.card import CARD_WIDTH, CARD_HEIGHT
from solitaireplus.games.solitaire.deck import create_deck, deal_tableau
from solitaireplus.app.settings import (
    ROUND_BASE_SCORE,
    ROUND_MOVE_BONUS_MAX,
    ROUND_MOVE_PAR,
    ROUND_MOVE_PENALTY,
    ROUND_TIME_BONUS_MAX,
    ROUND_TIME_PENALTY_PER_SECOND,
    ROUND_MIN_XP,
    ROUND_SCORE_PER_XP,
    DIFFICULTY_RULES,
    DEFAULT_DIFFICULTY,
    CAREER_CHALLENGE_RULES,
)
from solitaireplus.games.solitaire.assist import (
    DEAL_MODE_RANDOM,
    DEAL_MODE_VERIFIED,
    build_verified_deal,
    get_complete_suit_run,
    is_same_suit_descending_step,
    normalize_deal_mode,
)

from solitaireplus.games.solitaire.constants import (
    BASE_WIDTH,
    BASE_HEIGHT,
    TABLE_GREEN,
    PLACEHOLDER,
    OUTLINE,
    CARD_BACK,
    START_X,
    START_Y,
    SPACING_X,
    FACE_DOWN_SPACING,
    FACE_UP_SPACING,
    FLIP_DURATION_MS,
    HINT_DURATION_MS,
    VICTORY_DURATION_MS,
    VICTORY_CARD_DELAY_MS,
    VICTORY_GRAVITY,
    VICTORY_BOUNCE,
)
from solitaireplus.games.solitaire.layout import LayoutMixin
from solitaireplus.games.solitaire.moves import MovesMixin
from solitaireplus.games.solitaire.scoring import ScoringMixin
from solitaireplus.games.solitaire.hints import HintMixin
from solitaireplus.games.solitaire.auto_solve import AutoSolveMixin
from solitaireplus.games.solitaire.animation import AnimationMixin
from solitaireplus.games.solitaire.drawing import DrawingMixin
from solitaireplus.games.solitaire.controls import ControlsMixin


class Game(
    LayoutMixin,
    MovesMixin,
    ScoringMixin,
    HintMixin,
    AutoSolveMixin,
    AnimationMixin,
    DrawingMixin,
    ControlsMixin,
):
    def __init__(
        self,
        screen,
        audio
    ):
        self.screen = screen
        self.audio = audio
        self.felt_surface = None

        self.card_fronts = {}

        self.card_backs = {}
        self.selected_card_back = "back_default"

        self.load_card_images()



        # ----------------------------
        # Dragging
        # ----------------------------

        self.dragging = False

        self.drag_cards = []
        self.drag_source = None
        self.drag_source_index = None

        self.drag_mouse_x = 0
        self.drag_mouse_y = 0

        self.drag_offset_x = 0
        self.drag_offset_y = 0

        self.drag_spacing = FACE_UP_SPACING

        # A mouse-down begins as a possible click.
        # It only becomes a drag after the mouse
        # moves a few pixels.
        self.drag_candidate = False
        self.drag_start_pos = None
        self.drag_start_rect = None

        self.pending_clicks = 1

        self.drag_threshold = 6

        # ----------------------------
        # Game data
        # ----------------------------

        self.tableau = []
        self.stock = []
        self.waste = []

        self.foundations = [
            [],
            [],
            [],
            []
        ]

        # ----------------------------
        # Selection
        # ----------------------------

        self.selected_card = None
        self.selected_source = None

        # ----------------------------
        # Round state
        # ----------------------------

        self.round_won = False

        self.move_count = 0
        self.round_start_ticks = pygame.time.get_ticks()

        self.round_summary = None

        self.undo_stack = []

        self.flip_animation = None
        self.victory_animation = None

        self.hints_enabled = True
        self.hint_data = None
        self.hint_start_ticks = 0

        self.auto_solving = False
        self.auto_solve_last_ticks = 0
        self.auto_solve_delay_ms = 140
        self.auto_solve_steps = 0
        self.auto_solve_max_steps = 500
        # (cards left in stock + waste, cards on foundations) at the last recycle
        self.auto_solve_recycle_signature = None

        # ----------------------------
        # Difficulty
        # ----------------------------

        self.shuffle_enabled = False

        self.difficulty = DEFAULT_DIFFICULTY

        self.stock_pass_limit = None
        self.stock_passes_used = 1

        self.hint_limit = None
        self.hints_remaining = None

        self.undo_history_limit = None

        self.reward_multiplier = 1.0

        self.clean_stock_bonus = 1.0

        # ----------------------------
        # Career challenge
        # ----------------------------

        self.challenge_id = None
        self.challenge_notice_start_ticks = 0

        # Number of cards drawn from stock
        # with one stock click.
        self.stock_draw_count = 1

        # New-deal behavior. Random deals are never labeled solvable.
        # Verified deals use a constructive arrangement with a known win path.
        self.deal_mode = DEAL_MODE_RANDOM
        self.deal_status = "random"

        self.apply_difficulty_rules()

        # ----------------------------
        # Options
        # ----------------------------

        # "foundation"
        # "foundation_and_tableau"
        self.double_click_mode = "foundation_and_tableau"

        self.challenge_title_font = pygame.font.SysFont(
            "cambria",
            21,
            bold=True
        )
        self.challenge_body_font = pygame.font.SysFont(
            "cambria",
            14,
            bold=True
        )

        # ----------------------------
        # Stock and waste locations
        # ----------------------------

        self.stock_rect = pygame.Rect(
            55,
            45,
            CARD_WIDTH,
            CARD_HEIGHT
        )

        self.waste_rect = pygame.Rect(
            230,
            45,
            CARD_WIDTH,
            CARD_HEIGHT
        )

        # ----------------------------
        # Foundation locations
        # ----------------------------

        self.foundation_rects = [
            pygame.Rect(
                760,
                45,
                CARD_WIDTH,
                CARD_HEIGHT
            ),
            pygame.Rect(
                900,
                45,
                CARD_WIDTH,
                CARD_HEIGHT
            ),
            pygame.Rect(
                1040,
                45,
                CARD_WIDTH,
                CARD_HEIGHT
            ),
            pygame.Rect(
                1180,
                45,
                CARD_WIDTH,
                CARD_HEIGHT
            )
        ]

        # Initial deal, without shuffle SFX
        self.new_game(
            play_shuffle=False
        )

    # --------------------------------------------------
    # Deal mode / status
    # --------------------------------------------------

    def set_deal_mode(self, mode):
        normalized = normalize_deal_mode(mode)
        if normalized == self.deal_mode:
            return False

        self.deal_mode = normalized
        return True

    def get_deal_status_label(self):
        labels = {
            "verified": "VERIFIED SOLVABLE",
            "race_verified": "RACE / PROVEN DRAW-1",
            "random": "RANDOM / UNVERIFIED",
            "modified": "SHUFFLED / UNVERIFIED",
            "challenge_unverified": "CHALLENGE / UNVERIFIED",
        }
        return labels.get(
            self.deal_status,
            "UNVERIFIED"
        )

    # --------------------------------------------------
    # New game
    # --------------------------------------------------

    def new_race_game(self):
        from solitaireplus.games.solitaire.race_deals import build_race_deal
        tableau, stock, metadata = build_race_deal()
        self.new_game()
        self.tableau = tableau
        self.stock = stock
        self.race_deal_metadata = metadata
        self.deal_status = "race_verified"
        # new_game() snapshotted the random deal it built; Restart must reproduce the race deal.
        from solitaireplus.games.solitaire.restart import capture_deal
        capture_deal(self)

    def new_game(self, play_shuffle=True):
        deck = create_deck()

        if self.deal_mode == DEAL_MODE_VERIFIED:
            self.tableau, self.stock = build_verified_deal(
                deck,
                draw_count=self.stock_draw_count
            )

            if self.challenge_id == "all_or_nothing":
                self.deal_status = "challenge_unverified"
            else:
                self.deal_status = "verified"

        else:
            self.tableau = deal_tableau(
                deck
            )

            self.stock = deck
            self.deal_status = "random"

        self.waste = []

        self.foundations = [
            [],
            [],
            [],
            []
        ]

        self.auto_solving = False
        self.auto_solve_last_ticks = 0
        self.auto_solve_steps = 0

        self.recent_hint_moves = []
        self.max_recent_hint_moves = 8

        self.selected_card = None
        self.selected_source = None

        self.clear_drag()

        self.undo_stack = []

        self.flip_animation = None
        self.victory_animation = None

        self.hint_data = None
        self.hint_start_ticks = 0

        if self.challenge_id == "all_or_nothing":
            self.challenge_notice_start_ticks = pygame.time.get_ticks()
        else:
            self.challenge_notice_start_ticks = 0

        self.round_won = False

        self.move_count = 0

        self.round_start_ticks = (
            pygame.time.get_ticks()
        )

        self.round_summary = None

        self.stock_passes_used = 1

        if self.hint_limit is None:
            self.hints_remaining = None
        else:
            self.hints_remaining = (
                self.hint_limit
            )

        from solitaireplus.games.solitaire.restart import capture_deal
        capture_deal(self)

        if play_shuffle:
            self.audio.play_sound(
                "card_shuffle"
            )

    # --------------------------------------------------
    # Difficulty
    # --------------------------------------------------

    def set_difficulty(
            self,
            difficulty_id
    ):
        if difficulty_id not in DIFFICULTY_RULES:
            return False

        self.difficulty = difficulty_id

        self.apply_difficulty_rules()


        return True

    def apply_difficulty_rules(self):
        rules = DIFFICULTY_RULES[
            self.difficulty
        ]

        self.shuffle_enabled = rules.get(
            "shuffle_enabled",
            False
        )

        self.stock_pass_limit = (
            rules[
                "stock_pass_limit"
            ]
        )

        self.hint_limit = (
            rules[
                "hint_limit"
            ]
        )

        self.undo_history_limit = (
            rules[
                "undo_history_limit"
            ]
        )

        self.reward_multiplier = (
            rules[
                "reward_multiplier"
            ]
        )

        self.clean_stock_bonus = (
            rules.get(
                "clean_stock_bonus",
                1.0
            )
        )

        self.hints_enabled = (
                self.hint_limit != 0
        )

    # --------------------------------------------------
    # Career challenge rules
    # --------------------------------------------------

    def set_challenge(
            self,
            challenge_id
    ):
        if (
                challenge_id
                not in CAREER_CHALLENGE_RULES
        ):
            return False

        rules = CAREER_CHALLENGE_RULES[
            challenge_id
        ]

        self.set_difficulty("normal")
        self.challenge_id = (
            challenge_id
        )

        self.stock_draw_count = (
            rules.get(
                "stock_draw_count",
                1
            )
        )

        self.stock_pass_limit = (
            rules.get(
                "stock_pass_limit"
            )
        )

        self.hint_limit = (
            rules.get(
                "hint_limit"
            )
        )

        self.undo_history_limit = (
            rules.get(
                "undo_history_limit"
            )
        )

        self.reward_multiplier = (
            rules.get(
                "reward_multiplier",
                1.0
            )
        )

        self.clean_stock_bonus = (
            rules.get(
                "clean_stock_bonus",
                1.0
            )
        )

        self.hints_enabled = (
                self.hint_limit != 0
        )

        if self.hint_limit is None:
            self.hints_remaining = None
        else:
            self.hints_remaining = (
                self.hint_limit
            )

        self.undo_stack = []
        self.challenge_notice_start_ticks = 0

        return True

    def clear_challenge(self):

        self.challenge_id = None
        self.challenge_notice_start_ticks = 0

        self.stock_draw_count = 1

        # Restore whatever the current
        # difficulty normally allows.
        self.apply_difficulty_rules()
