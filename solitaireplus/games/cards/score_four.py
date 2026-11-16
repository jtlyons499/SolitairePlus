import random
import time

from fractions import Fraction
from solitaireplus.games.cards.score_four_difficulty import puzzle_pool

# Hint text when even the original four cards cannot make 24.
NO_HINT = "No hint: these cards can't make 24."


class ScoreFourGame:

    def __init__(self):

        self.layout = "compact"
        self.difficulty = "standard"
        self.difficulty_menu = False
        self.rating_info_open = False
        self.last_hint_at = 0.0
        self.competitive_reward = 0

        self.puzzle_start_time = 0.0

        self.hint_text = None
        self.hint_used = False

        self.original_numbers = []
        self.values = []

        self.selected_index = None
        self.selected_operator = None

        self.undo_stack = []

        self.solution = None

        self.puzzles_completed = 0

        self.puzzles_required = 3

        self.round_complete = False
        self.round_complete_time = 0.0

        self.session_complete = False
        self.npc_skill_tier = "mid"

        self.mode = "solo"
        self.new_puzzle()

        self.reward_claimed = False
        self.last_rating_change = None

        # ==================================================
        # Mode / competitive state
        # ==================================================

        self.mode = "solo"

        self.player_score = 0
        self.npc_score = 0

        self.round_number = 1

        self.match_complete = False
        self.match_winner = None

        self.round_result = None
        self.round_result_time = 0.0
        self.round_result_delay = 8.0

        self.npc_solve_time_seconds = 0.0
        self.round_start_time = 0.0

    def update(self):

        # ==================================================
        # COMPETITIVE MODE
        # ==================================================

        if self.mode == "competitive":

            # ----------------------------------------------
            # Match already finished
            # ----------------------------------------------

            if self.match_complete:
                return

            # ----------------------------------------------
            # Round still active:
            # check whether NPC has solved it
            # ----------------------------------------------

            if not self.round_complete:

                elapsed = (
                        time.monotonic()
                        - self.round_start_time
                )

                if (
                        elapsed
                        >= self.npc_solve_time_seconds
                ):
                    self.finish_competitive_round(
                        "npc"
                    )

                return

            # ----------------------------------------------
            # Round finished:
            # briefly show result
            # ----------------------------------------------

            elapsed_result = (
                    time.monotonic()
                    - self.round_result_time
            )

            if (
                    elapsed_result
                    >= self.round_result_delay
            ):
                self.continue_competitive_round()

            return

        # ==================================================
        # SOLO MODE
        # ==================================================

        if not self.round_complete:
            return

        if self.session_complete:
            return

        elapsed = (
                time.monotonic()
                - self.round_complete_time
        )

        if elapsed >= 0.8:
            self.new_puzzle()

    def round_countdown_remaining(self):
        if self.mode != "competitive" or not self.round_complete or self.match_complete:
            return 0.0
        return max(0.0, self.round_result_delay - (time.monotonic() - self.round_result_time))

    def continue_competitive_round(self):
        if self.mode != "competitive" or not self.round_complete or self.match_complete:
            return False
        self.round_number += 1
        self.new_puzzle()
        self.start_npc_timer()
        return True

    def get_hint_step(self, _reset_depth=0):

        active_indices = [
            index
            for index, value in enumerate(
                self.values
            )
            if value is not None
        ]

        for first_index in active_indices:

            for second_index in active_indices:

                if first_index == second_index:
                    continue

                first_value = self.values[
                    first_index
                ]

                second_value = self.values[
                    second_index
                ]

                possibilities = [
                    (
                        "+",
                        first_value + second_value,
                        "adding"
                    ),
                    (
                        "-",
                        first_value - second_value,
                        "subtracting"
                    ),
                    (
                        "*",
                        first_value * second_value,
                        "multiplying"
                    ),
                ]

                if second_value != 0:
                    possibilities.append(
                        (
                            "/",
                            first_value / second_value,
                            "dividing"
                        )
                    )

                for (
                        operator,
                        result,
                        verb
                ) in possibilities:

                    remaining = []

                    for index, value in enumerate(
                            self.values
                    ):

                        if value is None:
                            continue

                        if index in (
                                first_index,
                                second_index
                        ):
                            continue

                        remaining.append(
                            value
                        )

                    remaining.append(
                        result
                    )

                    solution = self.solve_numbers(
                        remaining
                    )

                    if solution is None:
                        continue

                    first_text = (
                        str(first_value.numerator)
                        if first_value.denominator == 1
                        else (
                            f"{first_value.numerator}/"
                            f"{first_value.denominator}"
                        )
                    )

                    second_text = (
                        str(second_value.numerator)
                        if second_value.denominator == 1
                        else (
                            f"{second_value.numerator}/"
                            f"{second_value.denominator}"
                        )
                    )

                    if operator == "+":
                        return (
                            f"Try adding "
                            f"{first_text} and "
                            f"{second_text}."
                        )

                    if operator == "-":
                        return (
                            f"Try subtracting "
                            f"{second_text} from "
                            f"{first_text}."
                        )

                    if operator == "*":
                        return (
                            f"Try multiplying "
                            f"{first_text} by "
                            f"{second_text}."
                        )

                    if operator == "/":
                        return (
                            f"Try dividing "
                            f"{first_text} by "
                            f"{second_text}."
                        )

        active = [value for value in self.values if value is not None]
        if len(active) == 1 and active[0] == 24:
            return "Solved: 24!"
        # A dead end gets a concrete first step from the original puzzle.
        # The reset is tried once: an unsolvable original has no hint.
        if _reset_depth:
            return NO_HINT
        saved_values = self.values
        self.values = [Fraction(number) for number in self.original_numbers]
        try:
            first_step = self.get_hint_step(_reset_depth=_reset_depth + 1)
        finally:
            self.values = saved_values
        if first_step == NO_HINT:
            return NO_HINT
        return "Reset to the original four cards. " + first_step

    def solo_hint_progress(self, now=None):
        """Thirty seconds to the first hint and between subsequent hints."""
        if self.mode != "solo" or self.session_complete or self.round_complete:
            return 0.0
        now = time.monotonic() if now is None else now
        origin = max(self.puzzle_start_time, self.last_hint_at)
        return max(0.0, min(1.0, (now - origin) / 30.0))

    def solo_hint_available(self):
        return self.solo_hint_progress() >= 1.0

    def request_solo_hint(self):

        if not self.solo_hint_available():
            return False

        self.hint_text = (
            self.get_hint_step()
        )

        self.hint_used = True
        self.last_hint_at = time.monotonic()

        return True

    # ==================================================
    # Solver
    # ==================================================

    def solve_numbers(
            self,
            values,
            expressions=None
    ):

        if expressions is None:
            expressions = [
                str(value)
                for value in values
            ]

        if len(values) == 1:

            if values[0] == 24:
                return expressions[0]

            return None

        for first_index in range(
                len(values)
        ):

            for second_index in range(
                    len(values)
            ):

                if first_index == second_index:
                    continue

                first_value = values[
                    first_index
                ]

                second_value = values[
                    second_index
                ]

                first_expression = expressions[
                    first_index
                ]

                second_expression = expressions[
                    second_index
                ]

                remaining_values = []
                remaining_expressions = []

                for index in range(
                        len(values)
                ):

                    if index in (
                            first_index,
                            second_index
                    ):
                        continue

                    remaining_values.append(
                        values[index]
                    )

                    remaining_expressions.append(
                        expressions[index]
                    )

                operations = [
                    (
                        first_value
                        + second_value,

                        f"({first_expression} + "
                        f"{second_expression})"
                    ),

                    (
                        first_value
                        - second_value,

                        f"({first_expression} - "
                        f"{second_expression})"
                    ),

                    (
                        first_value
                        * second_value,

                        f"({first_expression} × "
                        f"{second_expression})"
                    ),
                ]

                if second_value != 0:

                    operations.append(
                        (
                            first_value
                            / second_value,

                            f"({first_expression} ÷ "
                            f"{second_expression})"
                        )
                    )

                for (
                    result,
                    expression
                ) in operations:

                    solution = (
                        self.solve_numbers(
                            remaining_values
                            + [
                                result
                            ],
                            remaining_expressions
                            + [
                                expression
                            ]
                        )
                    )

                    if solution is not None:
                        return solution

        return None

    def reset_current_puzzle(self):
        if self.round_complete or self.session_complete or self.match_complete:
            return False
        self.values = [Fraction(number) for number in self.original_numbers]
        self.selected_index = self.selected_operator = None
        self.undo_stack.clear()
        return True

    def start_solo_session(self, difficulty=None):
        if difficulty is not None:
            puzzle_pool(difficulty)
            self.difficulty = difficulty

        self.mode = "solo"

        self.puzzles_completed = 0

        self.session_complete = False
        self.reward_claimed = False
        self.last_rating_change = None

        self.match_complete = False
        self.match_winner = None

        self.new_puzzle()


    def start_competitive_session(
            self,
            skill_tier="mid",
            rating=None
    ):

        self.mode = "competitive"

        self.competitive_reward = 0

        self.player_score = 0
        self.npc_score = 0

        self.round_number = 1

        self.match_complete = False
        self.match_winner = None
        self.session_complete = False

        self.round_complete = False
        self.round_result = None

        self.reward_claimed = False
        self.last_rating_change = None

        self.npc_skill_tier = (
            skill_tier
        )
        self.npc_rating = rating

        self.new_puzzle()

        self.start_npc_timer()

    def start_npc_timer(self):

        tier_ranges = {
            "low": (
                55.0,
                75.0
            ),
            "mid": (
                40.0,
                65.0
            ),
            "strong": (
                23.0,
                36.0
            ),
            "elite": (
                15.0,
                26.0
            ),
        }

        minimum_time, maximum_time = (
            tier_ranges.get(
                getattr(
                    self,
                    "npc_skill_tier",
                    "mid"
                ),
                (
                    25.0,
                    40.0
                )
            )
        )

        if getattr(self, "npc_rating", None) is not None:
            try:
                mean_time = max(12.0, min(65.0, 52.0 - (int(self.npc_rating) - 800) * 0.017))
                minimum_time, maximum_time = mean_time * 0.82, mean_time * 1.18
            except (TypeError, ValueError, OverflowError):
                pass

        self.npc_solve_time_seconds = (
            random.uniform(
                minimum_time,
                maximum_time
            )
        )

        self.round_start_time = (
            time.monotonic()
        )

    def finish_competitive_round(
            self,
            winner
    ):

        if self.round_complete:
            return

        if self.match_complete:
            return

        self.round_complete = True
        self.round_result = winner

        self.round_result_time = (
            time.monotonic()
        )

        if winner == "player":
            self.player_score += 1

        elif winner == "npc":
            self.npc_score += 1

        # ----------------------------------------------
        # First to 3 wins the match
        # ----------------------------------------------

        reward_table = {
            "low": {"win": 45, "loss": -10},
            "mid": {"win": 60, "loss": -10},
            "strong": {"win": 50, "loss": -10},
            "elite": {"win": 65, "loss": -10},
        }
        rewards = reward_table.get(
            getattr(self, "npc_skill_tier", "mid"),
            reward_table["mid"],
        )

        if self.player_score >= 3:

            self.match_complete = True
            self.match_winner = "player"

            self.competitive_reward = rewards["win"]

        elif self.npc_score >= 3:

            self.match_complete = True
            self.match_winner = "npc"

            self.competitive_reward = rewards["loss"]


    # ==================================================
    # Deal solvable puzzle
    # ==================================================

    def new_puzzle(self):

        numbers = list(random.choice(puzzle_pool(self.difficulty if self.mode == "solo" else "standard")))
        random.shuffle(numbers)
        solution = self.solve_numbers([Fraction(number) for number in numbers])
        if solution is None:
            raise ValueError(f"Unsolvable ranked Score-Four puzzle: {numbers}")

        self.original_numbers = numbers

        self.card_suits = [
            random.choice(
                [
                    "Hearts",
                    "Diamonds",
                    "Clubs",
                    "Spades",
                ]
            )
            for _ in range(4)
        ]

        self.values = [
            Fraction(number)
            for number in numbers
        ]

        self.solution = solution

        self.selected_index = None
        self.selected_operator = None

        self.undo_stack = []

        self.round_complete = False
        self.round_complete_time = 0.0

        self.puzzle_start_time = (
            time.monotonic()
        )

        self.hint_text = None
        self.hint_used = False
        self.last_hint_at = 0.0

    # ==================================================
    # Selection
    # ==================================================

    def select_number(
            self,
            index
    ):

        if self.round_complete:
            return False

        if index < 0:
            return False

        if index >= len(
                self.values
        ):
            return False

        if self.values[index] is None:
            return False

        # First number
        if self.selected_index is None:

            self.selected_index = index

            return True

        # Click the selected number again to cancel
        # the entire pending operation.
        if self.selected_index == index:
            self.selected_index = None
            self.selected_operator = None

            return True

        # Waiting for operator
        if self.selected_operator is None:

            self.selected_index = index

            return True

        # Second number chosen:
        # perform calculation
        self.combine_with(
            index
        )

        return True

    def select_operator(
            self,
            operator
    ):

        if self.selected_index is None:
            return False

        if operator not in (
                "+",
                "-",
                "*",
                "/"
        ):
            return False

        # Click selected operator again
        # to deselect it.
        if self.selected_operator == operator:
            self.selected_operator = None
            return True

        self.selected_operator = operator

        return True

    # ==================================================
    # Combine tiles
    # ==================================================

    def combine_with(
            self,
            second_index
    ):

        first_index = (
            self.selected_index
        )

        if (
                first_index is None
                or first_index
                == second_index
        ):
            return False

        first_value = self.values[
            first_index
        ]

        second_value = self.values[
            second_index
        ]

        if (
                first_value is None
                or second_value is None
        ):
            return False

        operator = (
            self.selected_operator
        )

        if (
                operator == "/"
                and second_value == 0
        ):
            return False

        # Save complete state for Undo
        self.undo_stack.append(
            (
                self.values.copy(),
                self.selected_index,
                self.selected_operator
            )
        )

        if operator == "+":
            result = (
                first_value
                + second_value
            )

        elif operator == "-":
            result = (
                first_value
                - second_value
            )

        elif operator == "*":
            result = (
                first_value
                * second_value
            )

        elif operator == "/":
            result = (
                first_value
                / second_value
            )

        else:
            return False

        # First tile disappears.
        self.values[
            first_index
        ] = None

        # Result lands in second tile.
        self.values[
            second_index
        ] = result

        self.selected_index = None
        self.selected_operator = None

        if self.is_solved():

            # ==============================================
            # Competitive
            # ==============================================

            if self.mode == "competitive":

                self.finish_competitive_round(
                    "player"
                )

            # ==============================================
            # Solo
            # ==============================================

            else:

                self.puzzles_completed += 1

                self.round_complete = True

                self.round_complete_time = (
                    time.monotonic()
                )

                if (
                        self.puzzles_completed
                        >= self.puzzles_required
                ):
                    self.session_complete = True

        return True

    # ==================================================
    # Undo
    # ==================================================

    def undo(self):
        if self.round_complete:
            return False
        had_selection = self.selected_index is not None or self.selected_operator is not None
        self.selected_index = self.selected_operator = None
        if not self.undo_stack:
            return had_selection
        self.values, _selected_index, _selected_operator = self.undo_stack.pop()
        self.hint_text = None
        return True

    # ==================================================
    # Win check
    # ==================================================

    def is_solved(self):

        remaining_values = [
            value
            for value in self.values
            if value is not None
        ]

        return (
            len(remaining_values) == 1
            and remaining_values[0] == 24
        )


# ==================================================
# Solve check (multiplayer)
# ==================================================

SOLUTION_OPERATORS = ("+", "-", "*", "/")


def _live_tile(values, index):
    return (
        isinstance(index, int)
        and not isinstance(index, bool)
        and 0 <= index < len(values)
        and values[index] is not None
    )


def check_solution(numbers, steps):
    """Return True if ``steps`` turn the four ``numbers`` into 24 by the game's rules.

    The multiplayer Score-Four host checks a guest's "solved" claim with it.
    ``steps`` must be exactly three ``[first_index, operator, second_index]``
    steps (lists or tuples), the moves select_number and select_operator make:
    both indexes are ints 0-3 (not bools), different, and still on the table;
    the operator is one of + - * /, and dividing by zero is refused. As in
    combine_with, the first tile is removed and the result goes into the
    second. Fraction arithmetic; the one value left must equal 24. Anything
    else, malformed input included, gives False. The inputs are not changed.
    """
    try:
        values = [Fraction(number) for number in numbers]
    except (TypeError, ValueError, ZeroDivisionError):
        return False

    if (
            len(values) != 4
            or not isinstance(steps, (list, tuple))
            or len(steps) != 3
    ):
        return False

    for step in steps:
        if not isinstance(step, (list, tuple)) or len(step) != 3:
            return False

        first_index, operator, second_index = step

        if (
                not _live_tile(values, first_index)
                or not _live_tile(values, second_index)
                or first_index == second_index
                or not isinstance(operator, str)
                or operator not in SOLUTION_OPERATORS
        ):
            return False

        first_value = values[first_index]
        second_value = values[second_index]

        if operator == "+":
            result = first_value + second_value
        elif operator == "-":
            result = first_value - second_value
        elif operator == "*":
            result = first_value * second_value
        elif second_value == 0:
            return False
        else:
            result = first_value / second_value

        values[first_index] = None
        values[second_index] = result

    remaining_values = [value for value in values if value is not None]

    return len(remaining_values) == 1 and remaining_values[0] == 24

