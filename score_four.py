import random
import time

from fractions import Fraction


class ScoreFourGame:

    def __init__(self):

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

        self.new_puzzle()

        self.card_suits = []

        self.reward_claimed = False

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
        self.round_result_delay = 3.5

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
                self.round_number += 1

                self.new_puzzle()

                self.start_npc_timer()

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

    def get_hint_step(self):

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

        return "Try undoing a move and taking another approach."

    def solo_hint_available(self):

        if self.mode != "solo":
            return False

        if self.session_complete:
            return False

        if self.round_complete:
            return False

        if self.hint_used:
            return False

        elapsed = (
                time.monotonic()
                - self.puzzle_start_time
        )

        return elapsed >= 30.0

    def request_solo_hint(self):

        if not self.solo_hint_available():
            return False

        self.hint_text = (
            self.get_hint_step()
        )

        self.hint_used = True

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

    def start_solo_session(self):

        self.mode = "solo"

        self.puzzles_completed = 0

        self.session_complete = False
        self.reward_claimed = False

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
            "low": {"win": 45, "loss": 10},
            "mid": {"win": 60, "loss": 15},
            "strong": {"win": 80, "loss": 20},
            "elite": {"win": 100, "loss": 25},
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

        while True:

            numbers = [
                random.randint(
                    1,
                    10
                )
                for _ in range(4)
            ]

            values = [
                Fraction(number)
                for number in numbers
            ]

            solution = (
                self.solve_numbers(
                    values
                )
            )

            if solution is not None:
                break

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

        if not self.undo_stack:
            return False

        (
            self.values,
            self.selected_index,
            self.selected_operator
        ) = self.undo_stack.pop()

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
