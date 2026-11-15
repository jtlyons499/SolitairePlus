"""Head-to-Head races: starting, finishing and restoring the player's Solitaire settings (moved out of legacy.py)."""
from solitaireplus.career.news import build_head_to_head_story
import pygame
import random
from solitaireplus.games.solitaire.head_to_head import select_head_to_head_opponents
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
legacy = lazy("solitaireplus.legacy")
leveling = lazy("solitaireplus.profile.leveling")


def start_head_to_head_event():

    leaderboard = legacy.get_career_leaderboard(
        rating_key="solitaire"
    )
    state.head_to_head_opponents = select_head_to_head_opponents(
        leaderboard,
        state.career_ratings["solitaire"],
        count=4,
    )
    random.shuffle(state.head_to_head_opponents)
    state.head_to_head_selected_index = None
    legacy.head_to_head_race.reset()
    state.career_event_has_activity = False


def restore_head_to_head_game_settings():

    if state.head_to_head_previous_deal_mode is not None:
        legacy.game.set_deal_mode(
            state.head_to_head_previous_deal_mode
        )

    if state.head_to_head_previous_difficulty is not None:
        legacy.game.set_difficulty(
            state.head_to_head_previous_difficulty
        )

    if state.head_to_head_previous_stock_draw_count is not None:
        legacy.game.stock_draw_count = state.head_to_head_previous_stock_draw_count

    legacy.game.clear_challenge()
    state.head_to_head_previous_deal_mode = None
    state.head_to_head_previous_difficulty = None
    state.head_to_head_previous_stock_draw_count = None


def finish_head_to_head_race(
        won,
        round_data=None,
        forfeited=False
):

    if legacy.head_to_head_race.opponent is None or legacy.head_to_head_race.reward_claimed:
        return False
    legacy.head_to_head_race.reward_claimed = True

    now_ms = pygame.time.get_ticks()

    if won:
        legacy.head_to_head_race.mark_winner(
            "player",
            now_ms
        )
    elif legacy.head_to_head_race.winner is None:
        legacy.head_to_head_race.mark_winner(
            "npc",
            now_ms
        )

    opponent = legacy.head_to_head_race.opponent
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
        else legacy.head_to_head_race.player_progress_from_foundations(
            legacy.game.foundations
        )
    )
    elapsed_text = legacy.head_to_head_race.format_elapsed(
        now_ms
    )

    rating_change = legacy.rate_competitive_game("solitaire", opponent, won and not forfeited)
    fans_earned = 0

    if not forfeited:

        if won:
            fans_earned = legacy.award_fans_for_rating_win(
                rating_change,
                "Head-to-Head win"
            )
        else:
            fans_earned = legacy.lose_fans_for_bad_result(
                "Head-to-Head loss",
                severity=1.05,
            )

        leveling.award_game_xp(
            "head_to_head",
            won=won,
        )

        headline, body, category = build_head_to_head_story(
            state.player_name,
            opponent_name,
            won,
            elapsed_text=elapsed_text,
        )
        legacy.add_career_news(
            headline,
            body,
            category
        )

    state.career_event_has_activity = True

    if forfeited:
        state.career_event_summary_title = "RACE FORFEITED"
        result_line = f"{opponent_name} wins by forfeit."
    elif won:
        state.career_event_summary_title = "HEAD-TO-HEAD WIN"
        result_line = f"You beat {opponent_name} to 52 foundation cards."
    else:
        state.career_event_summary_title = "HEAD-TO-HEAD LOSS"
        result_line = f"{opponent_name} reached 52 foundation cards first."

    state.career_event_summary_lines = [
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
        f"Current Fans: {state.career_fans:,}",
    ]

    restore_head_to_head_game_settings()
    state.current_game_mode = "career"
    state.current_state = state_names.STATE_CAREER_EVENT_SUMMARY
    return True
