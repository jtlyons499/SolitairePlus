"""Game round tracking and scoring: move count, elapsed time, round score, XP and remark,
the round summary, and win detection (a mixin of rules.Game).
"""
import pygame

from solitaireplus.app.settings import (
    ROUND_BASE_SCORE,
    ROUND_MOVE_BONUS_MAX,
    ROUND_MOVE_PAR,
    ROUND_MOVE_PENALTY,
    ROUND_TIME_BONUS_MAX,
    ROUND_TIME_PENALTY_PER_SECOND,
    ROUND_MIN_XP,
    ROUND_SCORE_PER_XP,
)


class ScoringMixin:
    # --------------------------------------------------
    # Round tracking / scoring
    # --------------------------------------------------

    def record_move(self):
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
