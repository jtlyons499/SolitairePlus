import pygame
import copy
import random
import math

from card import CARD_WIDTH, CARD_HEIGHT
from deck import create_deck, deal_tableau
from settings import (
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
from solitaire_assist import (
    DEAL_MODE_RANDOM,
    DEAL_MODE_VERIFIED,
    build_verified_deal,
    get_complete_suit_run,
    is_same_suit_descending_step,
    normalize_deal_mode,
)

# ----------------------------
# Window settings
# ----------------------------

BASE_WIDTH = 1366
BASE_HEIGHT = 768


# ----------------------------
# Colors
# ----------------------------

TABLE_GREEN = (30, 110, 60)
PLACEHOLDER = (255, 255, 255)
OUTLINE = (200, 200, 200)

CARD_BACK = (40, 60, 150)


# ----------------------------
# Tableau layout
# ----------------------------

START_X = 65
START_Y = 235

SPACING_X = 185

FACE_DOWN_SPACING = 30
FACE_UP_SPACING = 48

FLIP_DURATION_MS = 220
HINT_DURATION_MS = 2200

VICTORY_DURATION_MS = 6500
VICTORY_CARD_DELAY_MS = 85

VICTORY_GRAVITY = 0.32
VICTORY_BOUNCE = -0.72

class Game:
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

    def handle_mouse_click(
            self,
            mouse_pos,
            clicks=1
    ):
        if self.victory_animation is not None:
            return


        if clicks >= 2:
            self.handle_double_click(
                mouse_pos
            )

        else:
            self.handle_click(
                mouse_pos
            )

    def debug_auto_solve_state(self):

        deck = create_deck()

        rank_order = {
            "A": 1,
            "2": 2,
            "3": 3,
            "4": 4,
            "5": 5,
            "6": 6,
            "7": 7,
            "8": 8,
            "9": 9,
            "10": 10,
            "J": 11,
            "Q": 12,
            "K": 13,
        }

        # --------------------------------------------------
        # Group cards by suit
        # --------------------------------------------------

        suits = {}

        for card in deck:
            suits.setdefault(
                card.suit,
                []
            ).append(card)

        for suit_cards in suits.values():
            suit_cards.sort(
                key=lambda card:
                rank_order[card.rank]
            )

        # --------------------------------------------------
        # Foundations contain A through Q
        # --------------------------------------------------

        self.foundations = []

        kings = []

        for suit_cards in suits.values():

            foundation_cards = []

            for card in suit_cards:

                card.face_up = True

                if card.rank == "K":
                    kings.append(card)

                else:
                    foundation_cards.append(
                        card
                    )

            self.foundations.append(
                foundation_cards
            )

        # --------------------------------------------------
        # Four exposed Kings in tableau
        # --------------------------------------------------

        self.tableau = [
            [],
            [],
            [],
            [],
            [],
            [],
            []
        ]

        for index, king in enumerate(kings):
            self.tableau[index].append(
                king
            )

        # --------------------------------------------------
        # Nothing left in stock or waste
        # --------------------------------------------------

        self.stock = []
        self.waste = []

        # --------------------------------------------------
        # Reset temporary state
        # --------------------------------------------------

        self.clear_selection()
        self.clear_drag()

        self.undo_stack = []

        self.flip_animation = None
        self.victory_animation = None

        self.hint_data = None

        self.round_won = False

        self.move_count = 0

        self.round_start_ticks = (
            pygame.time.get_ticks()
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

        if self.challenge_id is not None:
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

        if play_shuffle:
            self.audio.play_sound(
                "card_shuffle"
            )

    # --------------------------------------------------
    # Round tracking / scoring
    # --------------------------------------------------

    def record_move(self):
        # Any successful move invalidates the visual hint. Leaving the old
        # source rectangle on screen after the card has moved is confusing.
        self.hint_data = None
        self.hint_start_ticks = 0

        if not self.round_won:
            self.move_count += 1

    def get_elapsed_seconds(self):
        elapsed_ms = (
                pygame.time.get_ticks()
                - self.round_start_ticks
        )

        return max(
            0,
            elapsed_ms // 1000
        )

    def calculate_round_score(
            self,
            elapsed_seconds
    ):
        moves_over_par = max(
            0,
            self.move_count
            - ROUND_MOVE_PAR
        )

        move_bonus = max(
            0,
            ROUND_MOVE_BONUS_MAX
            - (
                    moves_over_par
                    * ROUND_MOVE_PENALTY
            )
        )

        time_bonus = max(
            0,
            ROUND_TIME_BONUS_MAX
            - (
                    elapsed_seconds
                    * ROUND_TIME_PENALTY_PER_SECOND
            )
        )

        total_score = (
                ROUND_BASE_SCORE
                + move_bonus
                + time_bonus
        )

        return {
            "base_score": ROUND_BASE_SCORE,
            "move_bonus": move_bonus,
            "time_bonus": time_bonus,
            "total_score": total_score,
        }

    def calculate_round_xp(
            self,
            score
    ):
        base_xp = max(
            ROUND_MIN_XP,
            score
            // ROUND_SCORE_PER_XP
        )

        multiplier = (
            self.reward_multiplier
        )

        # Extreme bonus:
        # finish after recycling the stock
        # no more than once.
        #
        # stock_passes_used:
        # 1 = never recycled
        # 2 = recycled once
        if (
                self.difficulty == "extreme"
                and self.stock_passes_used <= 2
        ):
            multiplier *= (
                self.clean_stock_bonus
            )

        return max(
            1,
            int(
                round(
                    base_xp
                    * multiplier
                )
            )
        )

    def get_round_remark(
            self,
            elapsed_seconds
    ):
        if (
                self.move_count <= 100
                and elapsed_seconds <= 560
        ):
            return "Genius!"

        if self.move_count <= 110:
            return "Great time!"

        if elapsed_seconds <= 420:
            return "Quick win!"

        if self.move_count >= 180:
            return "Lawn chair pace."

        return "."

    def consume_round_summary(self):
        # Wait until the victory animation
        # has completely finished.
        if self.victory_animation is not None:
            return None

        summary = self.round_summary

        self.round_summary = None

        return summary

    # --------------------------------------------------
    # Card flip animation
    # --------------------------------------------------

    def start_flip_animation(
            self,
            card
    ):
        card.face_up = True

        self.flip_animation = {
            "card": card,
            "start_ticks": pygame.time.get_ticks(),
        }

    def draw_card_sprite(
            self,
            card,
            x,
            y,
            selected=False
    ):
        rect = pygame.Rect(
            x,
            y,
            CARD_WIDTH,
            CARD_HEIGHT
        )

        # --------------------------------------------------
        # Flip animation
        # --------------------------------------------------

        if (
                self.flip_animation is not None
                and self.flip_animation["card"] is card
        ):
            elapsed = (
                    pygame.time.get_ticks()
                    - self.flip_animation[
                        "start_ticks"
                    ]
            )

            if elapsed >= FLIP_DURATION_MS:
                self.flip_animation = None

            else:
                progress = (
                        elapsed
                        / FLIP_DURATION_MS
                )

                # First half shows the back shrinking.
                if progress < 0.5:
                    image = (
                        self.get_card_back_surface()
                    )

                    width_percent = (
                            1.0
                            - progress * 2
                    )

                # Second half shows the front expanding.
                else:
                    key = (
                        self.get_card_image_key(
                            card
                        )
                    )

                    image = self.card_fronts[key]

                    width_percent = (
                            (progress - 0.5)
                            * 2
                    )

                animated_width = max(
                    1,
                    int(
                        CARD_WIDTH
                        * width_percent
                    )
                )

                animated_image = (
                    pygame.transform.scale(
                        image,
                        (
                            animated_width,
                            CARD_HEIGHT
                        )
                    )
                )

                animated_x = (
                        x
                        + (
                                CARD_WIDTH
                                - animated_width
                        ) // 2
                )

                self.screen.blit(
                    animated_image,
                    (
                        animated_x,
                        y
                    )
                )

                return

        # --------------------------------------------------
        # Normal card drawing
        # --------------------------------------------------

        if card.face_up:
            key = self.get_card_image_key(
                card
            )

            image = self.card_fronts[key]

        else:
            image = (
                self.get_card_back_surface()
            )

        self.screen.blit(
            image,
            (
                x,
                y
            )
        )

        if selected:
            pygame.draw.rect(
                self.screen,
                (
                    255,
                    215,
                    0
                ),
                rect,
                3
            )

        rect = pygame.Rect(
            x,
            y,
            CARD_WIDTH,
            CARD_HEIGHT
        )

        if card.face_up:
            key = self.get_card_image_key(
                card
            )

            image = self.card_fronts[
                key
            ]

        else:
            image = (
                self.get_card_back_surface()
            )

        self.screen.blit(
            image,
            (x, y)
        )

        # Optional outline if selected
        if selected:
            pygame.draw.rect(
                self.screen,
                (255, 215, 0),
                rect,
                3
            )

    # --------------------------------------------------
    # Victory animation
    # --------------------------------------------------

    def start_victory_animation(self):
        animated_cards = []

        # Work from the four completed foundations.
        for foundation_index, foundation in enumerate(
                self.foundations
        ):
            foundation_rect = self.foundation_rects[
                foundation_index
            ]

            for card_index, card in enumerate(
                    reversed(foundation)
            ):
                # Alternate horizontal directions and
                # vary the strength slightly by foundation.
                direction = (
                    -1
                    if foundation_index % 2 == 0
                    else 1
                )

                speed_x = (
                        direction
                        * (
                                3.2
                                + foundation_index * 0.55
                                + card_index * 0.025
                        )
                )

                speed_y = (
                        -5.5
                        - (card_index % 5) * 0.45
                )

                animated_cards.append(
                    {
                        "card": card,
                        "x": float(
                            foundation_rect.x
                        ),
                        "y": float(
                            foundation_rect.y
                        ),
                        "vx": speed_x,
                        "vy": speed_y,
                        "delay": (
                                len(animated_cards)
                                * VICTORY_CARD_DELAY_MS
                        ),
                        "active": False,
                    }
                )

        self.victory_animation = {
            "start_ticks": pygame.time.get_ticks(),
            "last_ticks": pygame.time.get_ticks(),
            "cards": animated_cards,
        }

    def start_debug_victory_animation(self):
        all_cards = []

        # Tableau cards
        for column in self.tableau:
            all_cards.extend(
                column
            )

        # Stock cards
        all_cards.extend(
            self.stock
        )

        # Waste cards
        all_cards.extend(
            self.waste
        )

        # Foundation cards
        for foundation in self.foundations:
            all_cards.extend(
                foundation
            )

        animated_cards = []

        for index, card in enumerate(
                all_cards
        ):
            foundation_index = (
                    index % 4
            )

            foundation_rect = (
                self.foundation_rects[
                    foundation_index
                ]
            )

            direction = (
                -1
                if foundation_index % 2 == 0
                else 1
            )

            speed_x = (
                    direction
                    * (
                            3.2
                            + foundation_index * 0.55
                            + index * 0.025
                    )
            )

            speed_y = (
                    -5.5
                    - (index % 5) * 0.45
            )

            animated_cards.append(
                {
                    "card": card,

                    "x": float(
                        foundation_rect.x
                    ),

                    "y": float(
                        foundation_rect.y
                    ),

                    "vx": speed_x,
                    "vy": speed_y,

                    "delay": (
                            index
                            * VICTORY_CARD_DELAY_MS
                    ),

                    "active": False,
                }
            )

        now = pygame.time.get_ticks()

        self.victory_animation = {
            "start_ticks": now,
            "last_ticks": now,
            "cards": animated_cards,
        }

    def update_victory_animation(self):
        if self.victory_animation is None:
            return

        now = pygame.time.get_ticks()

        elapsed = (
                now
                - self.victory_animation[
                    "start_ticks"
                ]
        )

        delta_ms = (
                now
                - self.victory_animation[
                    "last_ticks"
                ]
        )

        self.victory_animation[
            "last_ticks"
        ] = now

        # Normalize around 60 FPS.
        delta = min(
            2.0,
            delta_ms / 16.67
        )

        for data in self.victory_animation[
            "cards"
        ]:
            if elapsed < data["delay"]:
                continue

            data["active"] = True

            data["x"] += (
                    data["vx"] * delta
            )

            data["y"] += (
                    data["vy"] * delta
            )

            data["vy"] += (
                    VICTORY_GRAVITY * delta
            )

            # Bounce off bottom edge.
            if (
                    data["y"] + CARD_HEIGHT
                    >= BASE_HEIGHT
            ):
                data["y"] = (
                        BASE_HEIGHT
                        - CARD_HEIGHT
                )

                data["vy"] *= (
                    VICTORY_BOUNCE
                )

                # Lose a little horizontal energy.
                data["vx"] *= 0.98

            # Wrap horizontally.
            if (
                    data["x"]
                    > BASE_WIDTH
            ):
                data["x"] = (
                    -CARD_WIDTH
                )

            elif (
                    data["x"] + CARD_WIDTH
                    < 0
            ):
                data["x"] = (
                    BASE_WIDTH
                )

        if elapsed >= VICTORY_DURATION_MS:
            self.victory_animation = None

    def draw_victory_animation(self):
        if self.victory_animation is None:
            return

        for data in self.victory_animation[
            "cards"
        ]:
            if not data["active"]:
                continue

            card = data["card"]

            key = self.get_card_image_key(
                card
            )

            image = self.card_fronts[
                key
            ]

            self.screen.blit(
                image,
                (
                    int(data["x"]),
                    int(data["y"])
                )
            )

    def get_card_image_key(self, card):
        suit_map = {
            "Clubs": "C",
            "Diamonds": "D",
            "Hearts": "H",
            "Spades": "S",
            "C": "C",
            "D": "D",
            "H": "H",
            "S": "S",
        }

        suit_letter = suit_map[
            card.suit
        ]

        return f"{card.rank}{suit_letter}"

    def set_felt_surface(self, felt_surface):
        self.felt_surface = felt_surface

    def load_card_images(self):
        ranks = [
            "A", "2", "3", "4", "5", "6", "7",
            "8", "9", "10", "J", "Q", "K"
        ]

        suits = ["C", "D", "H", "S"]

        for rank in ranks:
            for suit in suits:
                key = f"{rank}{suit}"
                path = (
                    f"assets/cards/fronts/{key}.png"
                )

                image = pygame.image.load(
                    path
                ).convert_alpha()

                # Optional safety resize in case
                # your files are not exactly 100x140
                image = pygame.transform.scale(
                    image,
                    (
                        CARD_WIDTH,
                        CARD_HEIGHT
                    )
                )

                self.card_fronts[key] = image



        # ----------------------------
        # Card backs
        # ----------------------------

        card_back_paths = {
            "back_default":
                "assets/cards/backs/back_default.png",

            "back_red":
                "assets/cards/backs/back_red.png",

            "back_cyan":
                "assets/cards/backs/back_cyan.png",

            "back_july_four":
                "assets/cards/backs/back_july_four.png",
        }

        for back_id, path in card_back_paths.items():
            image = pygame.image.load(
                path
            ).convert_alpha()

            image = pygame.transform.scale(
                image,
                (
                    CARD_WIDTH,
                    CARD_HEIGHT
                )
            )

            self.card_backs[
                back_id
            ] = image

    def set_card_back(
            self,
            card_back_id
    ):
        if card_back_id in self.card_backs:
            self.selected_card_back = (
                card_back_id
            )

    def get_card_back_surface(self):
        return self.card_backs[
            self.selected_card_back
        ]

    # --------------------------------------------------
    # Win detection
    # --------------------------------------------------

    def is_game_won(self):
        return all(
            len(foundation) == 13
            for foundation in self.foundations
        )

    def check_for_win(self):
        if self.round_won:
            return

        if self.is_game_won():
            self.round_won = True

            elapsed_seconds = (
                self.get_elapsed_seconds()
            )

            score_data = (
                self.calculate_round_score(
                    elapsed_seconds
                )
            )

            xp_earned = (
                self.calculate_round_xp(
                    score_data[
                        "total_score"
                    ]
                )
            )

            self.round_summary = {
                "moves": self.move_count,
                "elapsed_seconds": elapsed_seconds,
                "base_score": score_data[
                    "base_score"
                ],
                "move_bonus": score_data[
                    "move_bonus"
                ],
                "time_bonus": score_data[
                    "time_bonus"
                ],
                "score": score_data[
                    "total_score"
                ],
                "xp_earned": xp_earned,
                "remark": self.get_round_remark(
                    elapsed_seconds
                ),
                "difficulty":
                    self.difficulty,

                "challenge_id":
                    self.challenge_id,

                "reward_multiplier":
                    self.reward_multiplier,

                "stock_passes":
                    self.stock_passes_used,
            }

            self.audio.play_sound(
                "celebration_1"
            )

            self.start_victory_animation()

            print(
                "Round complete:",
                self.round_summary
            )

    # --------------------------------------------------
    # Solitaire rules
    # --------------------------------------------------

    def can_place_on_tableau(self, moving_card, target_card):
        different_color = (
            moving_card.is_red
            != target_card.is_red
        )

        correct_rank = (
            moving_card.value
            == target_card.value - 1
        )

        standard_move = different_color and correct_rank

        if self.challenge_id == "all_or_nothing":
            return (
                standard_move
                or is_same_suit_descending_step(
                    moving_card,
                    target_card
                )
            )

        return standard_move

    def can_place_on_foundation(self, moving_card, foundation):
        if self.challenge_id == "all_or_nothing":
            return False

        if not foundation:
            return moving_card.rank == "A"

        top_card = foundation[-1]

        same_suit = (
            moving_card.suit
            == top_card.suit
        )

        next_rank = (
            moving_card.value
            == top_card.value + 1
        )

        return same_suit and next_rank

    def get_all_or_nothing_stack(
            self,
            source_column_index,
            selected_card=None
    ):
        if self.challenge_id != "all_or_nothing":
            return None

        if not (
                0 <= source_column_index < len(self.tableau)
        ):
            return None

        return get_complete_suit_run(
            self.tableau[source_column_index],
            selected_card=selected_card
        )

    def move_all_or_nothing_stack_to_foundation(
            self,
            source_column_index,
            selected_card,
            foundation_index
    ):
        if self.challenge_id != "all_or_nothing":
            return False

        if not (0 <= foundation_index < len(self.foundations)):
            return False

        foundation = self.foundations[foundation_index]
        if foundation:
            return False

        run = self.get_all_or_nothing_stack(
            source_column_index,
            selected_card=selected_card
        )

        if run is None:
            return False

        source_column = self.tableau[source_column_index]

        self.save_undo_state()

        del source_column[-13:]

        # Tableau run is K..A from top to playable end. Foundations store
        # A..K so the completed suit behaves like a normal finished pile.
        foundation.extend(reversed(run))

        self.record_move()
        self.audio.play_sound("card_move")

        if (
                source_column
                and not source_column[-1].face_up
        ):
            self.start_flip_animation(
                source_column[-1]
            )
            self.audio.play_sound("card_flip")

        self.clear_selection()
        self.check_for_win()
        return True

    # --------------------------------------------------
    # Utility / Check Methods
    # --------------------------------------------------

    def can_auto_solve(self):

        if self.challenge_id == "all_or_nothing":
            return False

        if self.victory_animation is not None:
            return False

        if self.round_won:
            return False

        # Every tableau card must be face-up.
        for column in self.tableau:
            for card in column:
                if not card.face_up:
                    return False

        return True

    def auto_solve(self):

        if not self.can_auto_solve():
            return False

        self.clear_selection()
        self.clear_drag()

        self.auto_solving = True

        self.auto_solve_last_ticks = (
            pygame.time.get_ticks()
        )

        self.auto_solve_steps = 0

        return True

    def update_auto_solve(self):

        if not self.auto_solving:
            return

        if self.round_won:
            self.auto_solving = False
            return

        current_ticks = (
            pygame.time.get_ticks()
        )

        if (
                current_ticks
                - self.auto_solve_last_ticks
                < self.auto_solve_delay_ms
        ):
            return

        self.auto_solve_last_ticks = (
            current_ticks
        )

        self.auto_solve_steps += 1

        if (
                self.auto_solve_steps
                >= self.auto_solve_max_steps
        ):
            self.auto_solving = False
            return

        # ==================================================
        # TABLEAU -> FOUNDATION
        # ==================================================

        for source_index, column in enumerate(
                self.tableau
        ):

            if not column:
                continue

            card = column[-1]

            for foundation_index in range(4):

                if self.move_tableau_to_foundation(
                        source_index,
                        card,
                        foundation_index
                ):
                    return

        # ==================================================
        # WASTE -> FOUNDATION
        # ==================================================

        if self.waste:

            for foundation_index in range(4):

                if self.move_waste_to_foundation(
                        foundation_index
                ):
                    return

        # ==================================================
        # STOCK
        # ==================================================

        if self.stock:
            self.click_stock()
            return

        # ==================================================
        # RECYCLE WASTE -> STOCK
        # ==================================================

        if self.waste:

            old_stock_count = len(
                self.stock
            )

            self.click_stock()

            if len(self.stock) > old_stock_count:
                return

        # ==================================================
        # NOTHING ELSE TO DO
        # ==================================================

        self.auto_solving = False

    # --------------------------------------------------
    # Hint system
    # --------------------------------------------------

    def is_recent_tableau_hint(
            self,
            source_index,
            target_index,
            card
    ):

        for recent_move in self.recent_hint_moves:

            (
                recent_source,
                recent_target,
                recent_rank,
                recent_suit
            ) = recent_move

            same_stack = (
                    recent_rank == card.rank
                    and recent_suit == card.suit
            )

            if not same_stack:
                continue

            # Exact same hint again.
            if (
                    recent_source == source_index
                    and recent_target == target_index
            ):
                return True

            # Reverse of a recent hint.
            if (
                    recent_source == target_index
                    and recent_target == source_index
            ):
                return True

        return False

    def find_hint(self):

        # ==================================================
        # ALL OR NOTHING: completed suit -> foundation
        # ==================================================

        if self.challenge_id == "all_or_nothing":
            empty_foundation_index = next(
                (
                    index
                    for index, foundation in enumerate(self.foundations)
                    if not foundation
                ),
                None
            )

            if empty_foundation_index is not None:
                for column_index, column in enumerate(self.tableau):
                    run = get_complete_suit_run(column)
                    if run is None:
                        continue

                    return {
                        "source_rect": self.get_tableau_card_rect(
                            column_index,
                            run[0]
                        ),
                        "target_rect": self.foundation_rects[
                            empty_foundation_index
                        ],
                        "text": "Move complete suit to foundation",
                    }

        # ==================================================
        # 1. Tableau -> foundation
        # ==================================================

        for column_index, column in enumerate(
                self.tableau
        ):
            if not column:
                continue

            card = column[-1]

            if not card.face_up:
                continue

            for foundation_index, foundation in enumerate(
                    self.foundations
            ):
                if self.can_place_on_foundation(
                        card,
                        foundation
                ):
                    return {
                        "source_rect":
                            self.get_tableau_card_rect(
                                column_index,
                                card
                            ),

                        "target_rect":
                            self.foundation_rects[
                                foundation_index
                            ],

                        "text":
                            "Move card to foundation",
                    }

        # ==================================================
        # 2. Waste -> foundation
        # ==================================================

        if self.waste:
            card = self.waste[-1]

            for foundation_index, foundation in enumerate(
                    self.foundations
            ):
                if self.can_place_on_foundation(
                        card,
                        foundation
                ):
                    return {
                        "source_rect":
                            self.waste_rect.copy(),

                        "target_rect":
                            self.foundation_rects[
                                foundation_index
                            ],

                        "text":
                            "Move waste card to foundation",
                    }

        # ==================================================
        # 3. Tableau -> tableau
        #
        # First prefer moves that reveal a face-down card.
        # ==================================================

        for source_index, source_column in enumerate(
                self.tableau
        ):
            if not source_column:
                continue

            for card_index, card in enumerate(
                    source_column
            ):
                if not card.face_up:
                    continue

                # Prefer a move that exposes a hidden card.
                reveals_hidden = (
                        card_index > 0
                        and not source_column[
                    card_index - 1
                    ].face_up
                )

                if not reveals_hidden:
                    continue

                for target_index, target_column in enumerate(
                        self.tableau
                ):
                    if target_index == source_index:
                        continue

                    if not target_column:
                        legal = (
                                card.rank == "K"
                        )

                    else:
                        legal = (
                            self.can_place_on_tableau(
                                card,
                                target_column[-1]
                            )
                        )

                    if legal:
                        return {
                            "source_rect":
                                self.get_tableau_card_rect(
                                    source_index,
                                    card
                                ),

                            "target_rect":
                                self.get_tableau_target_rect(
                                    target_index
                                ),

                            "text":
                                "Move stack to reveal a card",

                            "move_type":
                                "tableau_to_tableau",

                            "source_index":
                                source_index,

                            "target_index":
                                target_index,

                            "card_rank":
                                card.rank,

                            "card_suit":
                                card.suit,
                        }

        # ==================================================
        # 4. Waste -> tableau
        # ==================================================

        if self.waste:
            card = self.waste[-1]

            for target_index, target_column in enumerate(
                    self.tableau
            ):
                if not target_column:
                    legal = (
                            card.rank == "K"
                    )

                else:
                    legal = (
                        self.can_place_on_tableau(
                            card,
                            target_column[-1]
                        )
                    )

                if legal:
                    return {
                        "source_rect":
                            self.waste_rect.copy(),

                        "target_rect":
                            self.get_tableau_target_rect(
                                target_index
                            ),

                        "text":
                            "Move waste card to tableau",
                    }

        # ==================================================
        # 5. Useful tableau -> tableau move
        #
        # Avoid moves that simply shift an entire
        # face-up pile into an empty column.
        # ==================================================

        for source_index, source_column in enumerate(
                self.tableau
        ):
            if not source_column:
                continue

            for card_index, card in enumerate(
                    source_column
            ):

                if not card.face_up:
                    continue

                for target_index, target_column in enumerate(
                        self.tableau
                ):
                    if target_index == source_index:
                        continue

                    # ----------------------------
                    # Empty tableau
                    # ----------------------------

                    if not target_column:

                        if card.rank != "K":
                            continue

                        # If this King is the first card
                        # in the source column, moving it
                        # just transfers the entire pile
                        # from one empty slot to another.
                        if card_index == 0:
                            continue

                        legal = True

                    # ----------------------------
                    # Occupied tableau
                    # ----------------------------

                    else:
                        legal = (
                            self.can_place_on_tableau(
                                card,
                                target_column[-1]
                            )
                        )

                    if not legal:
                        continue

                    # ==================================================
                    # Avoid meaningless equivalent-parent moves
                    #
                    # Example:
                    #
                    # J - 10 - 9 - 8 - 7
                    #
                    # moving the 9-8-7 onto another 10 without
                    # revealing anything underneath.
                    # ==================================================

                    if (
                            target_column
                            and card_index > 0
                    ):

                        source_parent = (
                            source_column[
                                card_index - 1
                                ]
                        )

                        target_parent = (
                            target_column[-1]
                        )

                        if (
                                source_parent.face_up
                                and source_parent.rank
                                == target_parent.rank
                        ):
                            continue

                    # ==================================================
                    # Avoid recently suggested loops / reversals
                    # ==================================================

                    if self.is_recent_tableau_hint(
                            source_index,
                            target_index,
                            card
                    ):
                        continue

                    return {
                        "source_rect":
                            self.get_tableau_card_rect(
                                source_index,
                                card
                            ),

                        "target_rect":
                            self.get_tableau_target_rect(
                                target_index
                            ),

                        "text":
                            "Move card or stack",

                        "move_type":
                            "tableau_to_tableau",

                        "source_index":
                            source_index,

                        "target_index":
                            target_index,

                        "card_rank":
                            card.rank,

                        "card_suit":
                            card.suit,
                    }

        # ==================================================
        # 6. Nothing obvious -> draw from stock
        # ==================================================

        if self.stock or self.waste:
            return {
                "source_rect":
                    self.stock_rect.copy(),

                "target_rect":
                    None,

                "text":
                    "Draw from stock",
            }

        return None

    def request_hint(self):

        if not self.hints_enabled:
            return False

        if (
                self.hints_remaining
                is not None
                and self.hints_remaining <= 0
        ):
            return False

        if self.victory_animation is not None:
            return False

        self.clear_selection()

        hint = self.find_hint()

        if hint is None:
            return False

        self.hint_data = hint

        if (
                hint.get(
                    "move_type"
                )
                == "tableau_to_tableau"
        ):

            recent_move = (
                hint["source_index"],
                hint["target_index"],
                hint["card_rank"],
                hint["card_suit"],
            )

            self.recent_hint_moves.append(
                recent_move
            )

            if (
                    len(
                        self.recent_hint_moves
                    )
                    > self.max_recent_hint_moves
            ):
                self.recent_hint_moves.pop(0)

        self.hint_start_ticks = (
            pygame.time.get_ticks()
        )

        if self.hints_remaining is not None:
            self.hints_remaining -= 1

        return True

    def draw_hint(self):

        if self.hint_data is None:
            return

        elapsed = (
                pygame.time.get_ticks()
                - self.hint_start_ticks
        )

        if elapsed >= HINT_DURATION_MS:
            self.hint_data = None
            return

        source_rect = self.hint_data[
            "source_rect"
        ]

        target_rect = self.hint_data[
            "target_rect"
        ]

        # A bright pulse is much easier to follow than the old static
        # outline, especially when source and destination are far apart.
        phase = (elapsed % 520) / 520.0
        pulse = (
            math.sin(phase * math.tau)
            + 1.0
        ) / 2.0

        border_width = 3 + int(round(pulse * 4))
        highlight_color = (
            255,
            int(185 + 70 * pulse),
            int(25 + 120 * pulse)
        )

        def draw_pulsing_outline(rect):
            if rect is None:
                return

            outer = rect.inflate(
                int(4 + pulse * 6),
                int(4 + pulse * 6)
            )

            pygame.draw.rect(
                self.screen,
                highlight_color,
                outer,
                border_width,
                border_radius=5
            )

            if pulse >= 0.55:
                pygame.draw.rect(
                    self.screen,
                    (255, 255, 255),
                    rect.inflate(2, 2),
                    2,
                    border_radius=4
                )

        draw_pulsing_outline(source_rect)
        draw_pulsing_outline(target_rect)

    # --------------------------------------------------
    # Stock
    # --------------------------------------------------

    def click_stock(self):

        if self.flip_animation is not None:
            return

        self.clear_selection()

        if self.stock:
            self.save_undo_state()

            cards_to_draw = min(
                self.stock_draw_count,
                len(self.stock)
            )

            last_card = None

            for _ in range(
                    cards_to_draw
            ):
                card = self.stock.pop()

                card.face_up = True

                self.waste.append(
                    card
                )

                last_card = card

            # Animate only the final/top card.
            if last_card is not None:
                self.start_flip_animation(
                    last_card
                )

            self.record_move()

            self.audio.play_sound(
                "card_draw"
            )

        elif self.waste:

            # ----------------------------
            # Check stock-pass limit
            # ----------------------------

            if (
                    self.stock_pass_limit
                    is not None
                    and self.stock_passes_used
                    >= self.stock_pass_limit
            ):
                return

            self.save_undo_state()

            while self.waste:
                card = self.waste.pop()

                card.face_up = False

                self.stock.append(
                    card
                )

            self.stock_passes_used += 1

            self.record_move()

    def shuffle_stock(self):

        if not self.shuffle_enabled:
            return False

        cards = (
                self.stock[:]
                + self.waste[:]
        )

        if not cards:
            return False

        self.save_undo_state()

        for card in cards:
            card.face_up = False

        random.shuffle(cards)

        self.stock = cards
        self.waste = []
        self.deal_status = "modified"

        self.clear_selection()
        self.flip_animation = None

        self.record_move()

        self.audio.play_sound(
            "card_shuffle"
        )

        return True

    # --------------------------------------------------
    # Tableau movement
    # --------------------------------------------------

    def move_tableau_stack(
        self,
        source_column_index,
        selected_card,
        target_column_index
    ):
        source_column = self.tableau[
            source_column_index
        ]

        target_column = self.tableau[
            target_column_index
        ]

        if selected_card not in source_column:
            self.clear_selection()
            return False

        selected_index = source_column.index(
            selected_card
        )

        moving_stack = source_column[
            selected_index:
        ]

        if not target_column:
            if selected_card.rank != "K":
                return False

        else:
            target_card = target_column[-1]

            if not self.can_place_on_tableau(
                selected_card,
                target_card
            ):
                return False

        self.save_undo_state()

        del source_column[selected_index:]

        target_column.extend(moving_stack)

        self.record_move()

        self.audio.play_sound(
            "card_move"
        )

        if (
                source_column
                and not source_column[-1].face_up
        ):
            self.start_flip_animation(
                source_column[-1]
            )

            self.audio.play_sound(
                "card_flip"
            )

        return True

    # --------------------------------------------------
    # Waste -> tableau
    # --------------------------------------------------

    def move_waste_to_tableau(
        self,
        target_column_index
    ):
        if not self.waste:
            return False

        moving_card = self.waste[-1]

        target_column = self.tableau[
            target_column_index
        ]

        if not target_column:
            if moving_card.rank != "K":
                return False

        else:
            target_card = target_column[-1]

            if not self.can_place_on_tableau(
                moving_card,
                target_card
            ):
                return False

        self.save_undo_state()

        self.waste.pop()

        target_column.append(
            moving_card
        )

        self.record_move()

        self.audio.play_sound(
            "card_move"
        )

        return True

    # --------------------------------------------------
    # Waste -> foundation
    # --------------------------------------------------

    def move_waste_to_foundation(
        self,
        foundation_index
    ):
        if not self.waste:
            return False

        moving_card = self.waste[-1]

        foundation = self.foundations[
            foundation_index
        ]

        if not self.can_place_on_foundation(
            moving_card,
            foundation
        ):
            return False

        self.save_undo_state()

        self.waste.pop()
        foundation.append(moving_card)
        self.record_move()

        self.audio.play_sound("card_move")

        self.check_for_win()

        return True

    # --------------------------------------------------
    # Tableau -> foundation
    # --------------------------------------------------

    def move_tableau_to_foundation(
        self,
        source_column_index,
        selected_card,
        foundation_index
    ):
        if self.challenge_id == "all_or_nothing":
            return self.move_all_or_nothing_stack_to_foundation(
                source_column_index,
                selected_card,
                foundation_index
            )

        source_column = self.tableau[
            source_column_index
        ]

        if not source_column:
            return False

        if source_column[-1] is not selected_card:
            return False

        foundation = self.foundations[
            foundation_index
        ]

        if not self.can_place_on_foundation(
            selected_card,
            foundation
        ):
            return False

        self.save_undo_state()

        source_column.pop()
        foundation.append(selected_card)
        self.record_move()

        self.audio.play_sound(
            "card_move"
        )

        if (
                source_column
                and not source_column[-1].face_up
        ):
            self.start_flip_animation(
                source_column[-1]
            )

            self.audio.play_sound(
                "card_flip"
            )

        self.check_for_win()

        return True

    # --------------------------------------------------
    # Foundation -> tableau
    # --------------------------------------------------

    def move_foundation_to_tableau(
        self,
        foundation_index,
        target_column_index
    ):
        if self.challenge_id == "all_or_nothing":
            return False

        foundation = self.foundations[
            foundation_index
        ]

        if not foundation:
            return False

        moving_card = foundation[-1]

        target_column = self.tableau[
            target_column_index
        ]

        if not target_column:
            if moving_card.rank != "K":
                return False

        else:
            target_card = target_column[-1]

            if not self.can_place_on_tableau(
                moving_card,
                target_card
            ):
                return False

        self.save_undo_state()

        foundation.pop()
        target_column.append(moving_card)

        self.record_move()

        self.audio.play_sound(
            "card_move"
        )

        return True

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

    # --------------------------------------------------
    # Auto-move helpers
    # --------------------------------------------------

    def try_auto_move_to_foundation(
            self,
            card,
            source
    ):
        if self.challenge_id == "all_or_nothing":
            if (
                    source is None
                    or source[0] != "tableau"
            ):
                return False

            for foundation_index, foundation in enumerate(
                    self.foundations
            ):
                if foundation:
                    continue

                if self.move_all_or_nothing_stack_to_foundation(
                        source[1],
                        card,
                        foundation_index
                ):
                    return True

            return False

        for foundation_index, foundation in enumerate(
                self.foundations
        ):
            if not self.can_place_on_foundation(
                    card,
                    foundation
            ):
                continue

            # Waste -> foundation
            if source == ("waste", None):
                if not self.waste:
                    return False

                if self.waste[-1] is not card:
                    return False

                self.save_undo_state()

                self.waste.pop()

                foundation.append(
                    card
                )

                self.record_move()

                self.audio.play_sound(
                    "card_move"
                )

                self.check_for_win()

                self.clear_selection()

                return True

            # Tableau -> foundation
            if (
                    source is not None
                    and source[0] == "tableau"
            ):
                source_column = self.tableau[
                    source[1]
                ]

                if not source_column:
                    return False

                if source_column[-1] is not card:
                    return False

                self.save_undo_state()

                source_column.pop()

                foundation.append(
                    card
                )

                self.record_move()

                self.audio.play_sound(
                    "card_move"
                )

                self.check_for_win()

                # Flip newly exposed card
                if (
                        source_column
                        and not source_column[-1].face_up
                ):
                    self.start_flip_animation(
                        source_column[-1]
                    )

                    self.audio.play_sound(
                        "card_flip"
                    )

                self.clear_selection()

                return True

        return False

    # --------------------------------------------------
    # Undo
    # --------------------------------------------------

    def save_undo_state(self):
        state = {
            "tableau": self.tableau,
            "stock": self.stock,
            "waste": self.waste,
            "foundations": self.foundations,
            "move_count": self.move_count,
            "stock_passes_used":
                self.stock_passes_used,
            "hints_remaining":
                self.hints_remaining,
            "deal_status":
                self.deal_status,
        }

        self.undo_stack.append(
            copy.deepcopy(state)
        )

        if (
                self.undo_history_limit
                is not None
        ):
            while (
                    len(self.undo_stack)
                    > self.undo_history_limit
            ):
                self.undo_stack.pop(0)

    def undo(self):

        if self.challenge_id == "no_undo":
            return False

        if not self.undo_stack:
            return False

        state = self.undo_stack.pop()

        self.tableau = state["tableau"]
        self.stock = state["stock"]
        self.waste = state["waste"]
        self.foundations = state["foundations"]
        self.move_count = state["move_count"]

        self.stock_passes_used = (
            state[
                "stock_passes_used"
            ]
        )

        self.hints_remaining = (
            state[
                "hints_remaining"
            ]
        )

        self.deal_status = state.get(
            "deal_status",
            self.deal_status
        )

        self.selected_card = None
        self.selected_source = None

        self.flip_animation = None

        return True

    def try_auto_move_to_tableau(
            self,
            card,
            source
    ):
        for target_column_index, target_column in enumerate(
                self.tableau
        ):
            # Avoid moving a tableau card
            # onto its own column
            if (
                    source is not None
                    and source[0] == "tableau"
                    and source[1] == target_column_index
            ):
                continue

            # Check target validity
            if not target_column:
                if card.rank != "K":
                    continue

            else:
                target_card = target_column[-1]

                if not self.can_place_on_tableau(
                        card,
                        target_card
                ):
                    continue

            # ----------------------------
            # Waste -> tableau
            # ----------------------------

            if source == ("waste", None):
                if not self.waste:
                    return False

                if self.waste[-1] is not card:
                    return False

                self.save_undo_state()

                self.waste.pop()
                target_column.append(card)

                self.record_move()

                self.audio.play_sound("card_move")

                self.clear_selection()

                return True

            # ----------------------------
            # Foundation -> tableau
            # ----------------------------

            if (
                    source is not None
                    and source[0] == "foundation"
            ):
                foundation = self.foundations[
                    source[1]
                ]

                if not foundation:
                    return False

                if foundation[-1] is not card:
                    return False

                self.save_undo_state()

                foundation.pop()
                target_column.append(card)

                self.record_move()

                self.audio.play_sound("card_move")

                self.clear_selection()

                return True

            # ----------------------------
            # Tableau -> tableau
            # ----------------------------

            if (
                    source is not None
                    and source[0] == "tableau"
            ):
                source_column = self.tableau[
                    source[1]
                ]

                if card not in source_column:
                    return False

                card_index = source_column.index(card)

                moving_stack = source_column[
                    card_index:
                ]

                self.save_undo_state()

                del source_column[
                    card_index:
                ]

                target_column.extend(
                    moving_stack
                )

                self.record_move()

                self.audio.play_sound("card_move")

                # Flip newly exposed card
                if (
                        source_column
                        and not source_column[-1].face_up
                ):
                    self.start_flip_animation(
                        source_column[-1]
                    )

                    self.audio.play_sound(
                        "card_flip"
                    )

                return True

        return False

    # --------------------------------------------------
    # Dynamic tableau spacing
    # --------------------------------------------------

    def get_tableau_spacings(self, column):
        bottom_margin = 20

        available_height = (
            BASE_HEIGHT
            - START_Y
            - bottom_margin
        )

        normal_stack_height = CARD_HEIGHT

        for card in column[:-1]:
            if card.face_up:
                normal_stack_height += (
                    FACE_UP_SPACING
                )

            else:
                normal_stack_height += (
                    FACE_DOWN_SPACING
                )

        face_down_spacing = FACE_DOWN_SPACING
        face_up_spacing = FACE_UP_SPACING

        if normal_stack_height > available_height:
            extra_cards = len(column) - 1

            if extra_cards > 0:
                compressed_spacing = (
                    available_height
                    - CARD_HEIGHT
                ) / extra_cards

                face_down_spacing = min(
                    FACE_DOWN_SPACING,
                    compressed_spacing
                )

                face_up_spacing = min(
                    FACE_UP_SPACING,
                    compressed_spacing
                )

        return (
            face_down_spacing,
            face_up_spacing
        )

    def get_tableau_card_rect(
            self,
            column_index,
            target_card
    ):
        column = self.tableau[
            column_index
        ]

        x = (
                START_X
                + column_index * SPACING_X
        )

        y = START_Y

        face_down_spacing, face_up_spacing = (
            self.get_tableau_spacings(
                column
            )
        )

        for card in column:
            rect = pygame.Rect(
                x,
                y,
                CARD_WIDTH,
                CARD_HEIGHT
            )

            if card is target_card:
                return rect

            if card.face_up:
                y += face_up_spacing
            else:
                y += face_down_spacing

        return None

    def get_tableau_target_rect(
            self,
            column_index
    ):
        column = self.tableau[
            column_index
        ]

        x = (
                START_X
                + column_index * SPACING_X
        )

        if not column:
            return pygame.Rect(
                x,
                START_Y,
                CARD_WIDTH,
                CARD_HEIGHT
            )

        return self.get_tableau_card_rect(
            column_index,
            column[-1]
        )

    # --------------------------------------------------
    # Finding clicked cards
    # --------------------------------------------------

    def get_tableau_card_at_position(
        self,
        mouse_pos
    ):
        for column_index, column in enumerate(
            self.tableau
        ):
            x = (
                START_X
                + column_index * SPACING_X
            )

            y = START_Y

            face_down_spacing, face_up_spacing = (
                self.get_tableau_spacings(
                    column
                )
            )

            card_positions = []

            for card in column:
                rect = pygame.Rect(
                    x,
                    y,
                    CARD_WIDTH,
                    CARD_HEIGHT
                )

                card_positions.append(
                    (card, rect)
                )

                if card.face_up:
                    y += face_up_spacing

                else:
                    y += face_down_spacing

            for card, rect in reversed(
                card_positions
            ):
                if (
                    rect.collidepoint(mouse_pos)
                    and card.face_up
                ):
                    return card, column_index

        return None, None

    def get_tableau_column_at_position(
        self,
        mouse_pos
    ):
        for column_index in range(7):
            x = (
                START_X
                + column_index * SPACING_X
            )

            column_rect = pygame.Rect(
                x,
                START_Y,
                CARD_WIDTH,
                BASE_HEIGHT - START_Y
            )

            if column_rect.collidepoint(
                mouse_pos
            ):
                return column_index

        return None

    def get_foundation_at_position(
        self,
        mouse_pos
    ):
        for index, rect in enumerate(
            self.foundation_rects
        ):
            if rect.collidepoint(mouse_pos):
                return index

        return None

    # --------------------------------------------------
    # Selection
    # --------------------------------------------------

    def clear_selection(self):
        self.selected_card = None
        self.selected_source = None

    # --------------------------------------------------
    # Drag helpers
    # --------------------------------------------------

    def clear_drag(self):
        self.dragging = False

        self.drag_cards = []
        self.drag_source = None
        self.drag_source_index = None

        self.drag_candidate = False
        self.drag_start_pos = None
        self.drag_start_rect = None

        self.drag_spacing = FACE_UP_SPACING

    def handle_mouse_down(
            self,
            mouse_pos,
            clicks=1
    ):
        if self.victory_animation is not None:
            return

        self.pending_clicks = clicks

        # ----------------------------
        # Double click
        # ----------------------------

        if clicks >= 2:
            self.clear_drag()

            self.handle_double_click(
                mouse_pos
            )

            return

        self.clear_drag()

        self.drag_start_pos = mouse_pos

        # ==================================================
        # Waste
        # ==================================================

        if (
                self.waste
                and self.waste_rect.collidepoint(
            mouse_pos
        )
        ):
            card = self.waste[-1]

            self.drag_candidate = True

            self.drag_cards = [
                card
            ]

            self.drag_source = (
                "waste",
                None
            )

            self.drag_start_rect = (
                self.waste_rect.copy()
            )

            self.drag_offset_x = (
                    mouse_pos[0]
                    - self.drag_start_rect.x
            )

            self.drag_offset_y = (
                    mouse_pos[1]
                    - self.drag_start_rect.y
            )

            return

        # ==================================================
        # Foundation
        # ==================================================

        foundation_index = (
            self.get_foundation_at_position(
                mouse_pos
            )
        )

        if (
                foundation_index is not None
                and self.foundations[
            foundation_index
        ]
        ):
            card = self.foundations[
                foundation_index
            ][-1]

            self.drag_candidate = True

            self.drag_cards = [
                card
            ]

            self.drag_source = (
                "foundation",
                foundation_index
            )

            self.drag_start_rect = (
                self.foundation_rects[
                    foundation_index
                ].copy()
            )

            self.drag_offset_x = (
                    mouse_pos[0]
                    - self.drag_start_rect.x
            )

            self.drag_offset_y = (
                    mouse_pos[1]
                    - self.drag_start_rect.y
            )

            return

        # ==================================================
        # Tableau
        # ==================================================

        card, column_index = (
            self.get_tableau_card_at_position(
                mouse_pos
            )
        )

        if card is None:
            return

        source_column = self.tableau[
            column_index
        ]

        card_index = source_column.index(
            card
        )

        # Everything from the selected card downward
        # travels together.
        self.drag_cards = source_column[
            card_index:
        ]

        self.drag_candidate = True

        self.drag_source = (
            "tableau",
            column_index
        )

        self.drag_source_index = (
            card_index
        )

        self.drag_start_rect = (
            self.get_tableau_card_rect(
                column_index,
                card
            )
        )

        (
            _,
            face_up_spacing
        ) = self.get_tableau_spacings(
            source_column
        )

        self.drag_spacing = (
            face_up_spacing
        )

        self.drag_offset_x = (
                mouse_pos[0]
                - self.drag_start_rect.x
        )

        self.drag_offset_y = (
                mouse_pos[1]
                - self.drag_start_rect.y
        )

    def handle_mouse_motion(
            self,
            mouse_pos
    ):
        if not self.drag_candidate:
            return

        if self.drag_start_pos is None:
            return

        delta_x = (
                mouse_pos[0]
                - self.drag_start_pos[0]
        )

        delta_y = (
                mouse_pos[1]
                - self.drag_start_pos[1]
        )

        distance_squared = (
                delta_x * delta_x
                + delta_y * delta_y
        )

        # Don't turn tiny mouse movements
        # into accidental drags.
        if (
                not self.dragging
                and distance_squared
                >= self.drag_threshold ** 2
        ):
            self.dragging = True

            self.clear_selection()

        if self.dragging:
            self.drag_mouse_x = (
                mouse_pos[0]
            )

            self.drag_mouse_y = (
                mouse_pos[1]
            )

    def handle_mouse_up(
            self,
            mouse_pos
    ):
        # ==================================================
        # Normal click
        # ==================================================

        if not self.dragging:

            clicks = self.pending_clicks

            self.clear_drag()

            # Double clicks were already handled
            # during mouse-down.
            if clicks < 2:
                self.handle_mouse_click(
                    mouse_pos,
                    clicks
                )

            return

        # ==================================================
        # Drag drop
        # ==================================================

        source = self.drag_source

        if (
                source is None
                or not self.drag_cards
        ):
            self.clear_drag()
            return

        moving_card = self.drag_cards[0]

        moved = False

        # ----------------------------
        # Find destination
        # ----------------------------

        foundation_index = (
            self.get_foundation_at_position(
                mouse_pos
            )
        )

        target_column = (
            self.get_tableau_column_at_position(
                mouse_pos
            )
        )

        # ==================================================
        # Waste source
        # ==================================================

        if source[0] == "waste":

            if foundation_index is not None:
                moved = (
                    self.move_waste_to_foundation(
                        foundation_index
                    )
                )

            elif target_column is not None:
                moved = (
                    self.move_waste_to_tableau(
                        target_column
                    )
                )

        # ==================================================
        # Foundation source
        # ==================================================

        elif source[0] == "foundation":

            source_foundation = (
                source[1]
            )

            if target_column is not None:
                moved = (
                    self.move_foundation_to_tableau(
                        source_foundation,
                        target_column
                    )
                )

        # ==================================================
        # Tableau source
        # ==================================================

        elif source[0] == "tableau":

            source_column = (
                source[1]
            )

            # ----------------------------
            # Tableau -> foundation
            # ----------------------------

            if foundation_index is not None:

                # Existing method only succeeds if
                # this is the bottom/top playable card.
                moved = (
                    self.move_tableau_to_foundation(
                        source_column,
                        moving_card,
                        foundation_index
                    )
                )

            # ----------------------------
            # Tableau -> tableau
            # ----------------------------

            elif (
                    target_column is not None
                    and target_column
                    != source_column
            ):
                moved = (
                    self.move_tableau_stack(
                        source_column,
                        moving_card,
                        target_column
                    )
                )

        # Whether valid or invalid, stop dragging.
        # An invalid drop simply causes the original
        # cards to appear back in their source pile.
        self.clear_drag()

        self.clear_selection()

    # --------------------------------------------------
    # Mouse input
    # --------------------------------------------------

    def handle_click(self, mouse_pos):

        # Stock
        if self.stock_rect.collidepoint(
            mouse_pos
        ):
            self.click_stock()
            return

        # Waste
        if (
            self.waste_rect.collidepoint(
                mouse_pos
            )
            and self.waste
        ):
            self.selected_card = self.waste[-1]

            self.selected_source = (
                "waste",
                None
            )

            return

        # Foundation
        foundation_index = (
            self.get_foundation_at_position(
                mouse_pos
            )
        )

        # Waste -> foundation
        if (
            self.selected_card is not None
            and self.selected_source
            == ("waste", None)
            and foundation_index is not None
        ):
            moved = (
                self.move_waste_to_foundation(
                    foundation_index
                )
            )

            if moved:
                self.clear_selection()

            return

        # Tableau -> foundation
        if (
            self.selected_card is not None
            and self.selected_source is not None
            and self.selected_source[0]
            == "tableau"
            and foundation_index is not None
        ):
            moved = (
                self.move_tableau_to_foundation(
                    self.selected_source[1],
                    self.selected_card,
                    foundation_index
                )
            )

            if moved:
                self.clear_selection()

            return

        # Select foundation card
        if (
            foundation_index is not None
            and self.foundations[
                foundation_index
            ]
            and self.selected_card is None
        ):
            self.selected_card = (
                self.foundations[
                    foundation_index
                ][-1]
            )

            self.selected_source = (
                "foundation",
                foundation_index
            )

            return

        # Tableau click detection
        card, clicked_column = (
            self.get_tableau_card_at_position(
                mouse_pos
            )
        )

        target_column = (
            self.get_tableau_column_at_position(
                mouse_pos
            )
        )

        # Waste -> tableau
        if (
            self.selected_card is not None
            and self.selected_source
            == ("waste", None)
            and target_column is not None
        ):
            moved = (
                self.move_waste_to_tableau(
                    target_column
                )
            )

            if moved:
                self.clear_selection()

            return

        # Foundation -> tableau
        if (
            self.selected_card is not None
            and self.selected_source is not None
            and self.selected_source[0]
            == "foundation"
            and target_column is not None
        ):
            moved = (
                self.move_foundation_to_tableau(
                    self.selected_source[1],
                    target_column
                )
            )

            if moved:
                self.clear_selection()

            return

        # Tableau -> tableau
        if (
            self.selected_card is not None
            and self.selected_source is not None
            and self.selected_source[0]
            == "tableau"
            and target_column is not None
        ):
            source_column = (
                self.selected_source[1]
            )

            if target_column != source_column:
                moved = (
                    self.move_tableau_stack(
                        source_column,
                        self.selected_card,
                        target_column
                    )
                )

                if moved:
                    self.clear_selection()

                return

        # Select tableau card
        if card is not None:
            self.selected_card = card

            self.selected_source = (
                "tableau",
                clicked_column
            )

        else:
            self.clear_selection()

    # --------------------------------------------------
    # Double-click
    # --------------------------------------------------

    def handle_double_click(
            self,
            mouse_pos
    ):
        self.clear_selection()

        # ----------------------------
        # Stock
        # ----------------------------

        if self.stock_rect.collidepoint(
                mouse_pos
        ):
            self.click_stock()
            return

        # ----------------------------
        # Waste
        # -----------------------------------------------------

        if (
            self.waste_rect.collidepoint(
                mouse_pos
            )
            and self.waste
        ):
            card = self.waste[-1]

            source = (
                "waste",
                None
            )

            moved = (
                self.try_auto_move_to_foundation(
                    card,
                    source
                )
            )

            if (
                not moved
                and self.double_click_mode
                == "foundation_and_tableau"
            ):
                self.try_auto_move_to_tableau(
                    card,
                    source
                )

            return

        # ----------------------------
        # Foundation
        # ----------------------------

        foundation_index = (
            self.get_foundation_at_position(
                mouse_pos
            )
        )

        if (
            foundation_index is not None
            and self.foundations[
                foundation_index
            ]
        ):
            card = self.foundations[
                foundation_index
            ][-1]

            source = (
                "foundation",
                foundation_index
            )

            if (
                self.double_click_mode
                == "foundation_and_tableau"
            ):
                self.try_auto_move_to_tableau(
                    card,
                    source
                )

            return

        # ----------------------------
        # Tableau
        # ----------------------------

        card, column_index = (
            self.get_tableau_card_at_position(
                mouse_pos
            )
        )

        if card is None:
            return

        source = (
            "tableau",
            column_index
        )

        moved = (
            self.try_auto_move_to_foundation(
                card,
                source
            )
        )

        if (
            not moved
            and self.double_click_mode
            == "foundation_and_tableau"
        ):
            self.try_auto_move_to_tableau(
                card,
                source
            )

    # --------------------------------------------------
    # Events
    # --------------------------------------------------

    def handle_event(self, event):
        if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            if event.clicks >= 2:
                self.handle_double_click(
                    event.pos
                )

            else:
                self.handle_click(
                    event.pos
                )

    # --------------------------------------------------
    # Drawing
    # --------------------------------------------------

    def draw(self):
        if self.felt_surface is not None:
            self.screen.blit(
                self.felt_surface,
                (0, 0)
            )
        else:
            self.screen.fill(
                TABLE_GREEN
            )

        self.draw_stock()
        self.draw_waste()
        self.draw_foundations()
        self.draw_tableau()

        self.draw_challenge_notice()
        self.draw_hint()

        # Draw moving cards above all normal piles.
        self.draw_dragged_cards()

        self.update_victory_animation()
        self.draw_victory_animation()

    def draw_challenge_notice(self):
        if self.challenge_id is None:
            return

        if self.challenge_notice_start_ticks <= 0:
            return

        rules = CAREER_CHALLENGE_RULES.get(
            self.challenge_id,
            {}
        )

        notice_title = rules.get(
            "notice_title",
            rules.get(
                "name",
                "CHALLENGE"
            ).upper()
        )

        notice_lines = list(
            rules.get(
                "notice_lines",
                []
            )
        )

        if not notice_lines:
            return

        elapsed = (
            pygame.time.get_ticks()
            - self.challenge_notice_start_ticks
        )

        if elapsed >= 7500:
            return

        panel_rect = pygame.Rect(375, 58, 350, 112)
        panel = pygame.Surface(
            panel_rect.size,
            pygame.SRCALPHA
        )

        alpha = 225
        if elapsed >= 6200:
            alpha = max(0, int(225 * (7500 - elapsed) / 1300))

        pygame.draw.rect(
            panel,
            (15, 24, 18, alpha),
            panel.get_rect(),
            border_radius=12
        )
        pygame.draw.rect(
            panel,
            (255, 220, 90, alpha),
            panel.get_rect(),
            2,
            border_radius=12
        )

        title = self.challenge_title_font.render(
            notice_title,
            True,
            (255, 225, 105)
        )
        title.set_alpha(alpha)

        panel.blit(
            title,
            title.get_rect(center=(panel_rect.width // 2, 27))
        )

        line_y_positions = (64, 87)

        for line_index, line_text in enumerate(
                notice_lines[:2]
        ):
            line_surface = self.challenge_body_font.render(
                line_text,
                True,
                (245, 245, 245)
            )
            line_surface.set_alpha(alpha)
            panel.blit(
                line_surface,
                line_surface.get_rect(
                    center=(
                        panel_rect.width // 2,
                        line_y_positions[line_index]
                    )
                )
            )

        self.screen.blit(
            panel,
            panel_rect.topleft
        )

    def draw_stock(self):
        if self.stock:
            self.screen.blit(
                self.get_card_back_surface(),
                (
                    self.stock_rect.x,
                    self.stock_rect.y
                )
            )

        else:
            pygame.draw.rect(
                self.screen,
                PLACEHOLDER,
                self.stock_rect,
                2
            )

    def draw_waste(self):
        if not self.waste:
            pygame.draw.rect(
                self.screen,
                PLACEHOLDER,
                self.waste_rect,
                2
            )
            return

        # Show up to the last 3 waste cards.
        # Only the newest/top card is actually playable.
        visible_cards = self.waste[-3:]

        history_offset = 22

        start_x = (
                self.waste_rect.x
                - history_offset
                * (len(visible_cards) - 1)
        )

        for index, card in enumerate(
                visible_cards
        ):

            if (
                    self.dragging
                    and self.drag_source
                    == ("waste", None)
                    and card is self.waste[-1]
            ):
                continue

            x = (
                    start_x
                    + index * history_offset
            )

            is_top_card = (
                    card is self.waste[-1]
            )

            self.draw_card_sprite(
                card,
                x,
                self.waste_rect.y,
                selected=(
                        is_top_card
                        and self.selected_card
                        is card
                )
            )

    def draw_foundations(self):
        for index, rect in enumerate(
                self.foundation_rects
        ):
            foundation = self.foundations[
                index
            ]

            dragging_this_card = (
                    self.dragging
                    and self.drag_source
                    == (
                        "foundation",
                        index
                    )
            )

            # While the top foundation card is being dragged,
            # keep the source pile visible underneath it.
            #
            # If another card remains in the pile, show that
            # newly exposed card. If the dragged card was the
            # only card, show the normal empty foundation slot.
            if dragging_this_card:

                if len(foundation) >= 2:
                    exposed_card = foundation[-2]

                    self.draw_card_sprite(
                        exposed_card,
                        rect.x,
                        rect.y,
                        selected=False
                    )

                else:
                    pygame.draw.rect(
                        self.screen,
                        PLACEHOLDER,
                        rect,
                        2
                    )

                continue

            if foundation:
                card = foundation[-1]

                self.draw_card_sprite(
                    card,
                    rect.x,
                    rect.y,
                    selected=(
                            self.selected_card
                            is card
                    )
                )

            else:
                pygame.draw.rect(
                    self.screen,
                    PLACEHOLDER,
                    rect,
                    2
                )

    def draw_tableau(self):
        for column_index, column in enumerate(
                self.tableau
        ):
            x = (
                    START_X
                    + column_index * SPACING_X
            )

            y = START_Y

            # ----------------------------
            # Empty column
            # ----------------------------

            if not column:
                pygame.draw.rect(
                    self.screen,
                    OUTLINE,
                    pygame.Rect(
                        x,
                        START_Y,
                        CARD_WIDTH,
                        CARD_HEIGHT
                    ),
                    2
                )

                continue

            # ----------------------------
            # Dynamic spacing
            # ----------------------------

            face_down_spacing, face_up_spacing = (
                self.get_tableau_spacings(
                    column
                )
            )

            # ----------------------------
            # Cards
            # ----------------------------

            for card_index, card in enumerate(
                    column
            ):

                dragging_this_card = (
                        self.dragging
                        and self.drag_source
                        == (
                            "tableau",
                            column_index
                        )
                        and self.drag_source_index
                        is not None
                        and card_index
                        >= self.drag_source_index
                )

                if not dragging_this_card:
                    self.draw_card_sprite(
                        card,
                        x,
                        y,
                        selected=(
                                self.selected_card
                                is card
                        )
                    )

                if card.face_up:
                    y += face_up_spacing

                else:
                    y += face_down_spacing



    def draw_dragged_cards(self):
        if not self.dragging:
            return

        if not self.drag_cards:
            return

        x = (
                self.drag_mouse_x
                - self.drag_offset_x
        )

        y = (
                self.drag_mouse_y
                - self.drag_offset_y
        )

        for index, card in enumerate(
                self.drag_cards
        ):
            self.draw_card_sprite(
                card,
                x,
                y + index * self.drag_spacing
            )