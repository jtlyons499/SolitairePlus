"""Career ratings and fans earned from games (moved out of legacy.py)."""
from solitaireplus.app.settings import FELTS
from solitaireplus.career.ratings import GAME_RATING_KEYS
from solitaireplus.app.settings import MENU_BACKGROUNDS
from solitaireplus.app.settings import TITLES
from solitaireplus.career.ratings import apply_rating_change
from solitaireplus.career.fans import clamp_fans
from solitaireplus.career.ratings import elo_delta
from solitaireplus.career.fans import fan_gain_from_cash_win
from solitaireplus.career.fans import fan_gain_from_rating_win
from solitaireplus.career.fans import fan_loss_from_bad_result
from solitaireplus.career.world_flavor import rating_milestone_stories
from solitaireplus.career.fans import record_fan_trend
from solitaireplus.career.rating_events import settle_competitive_result
from solitaireplus.career.rating_events import settle_house_result
from solitaireplus.career.rating_events import settle_poker_session
from solitaireplus.app import state
from solitaireplus.profile.unlocks import unlock_ratings
from solitaireplus.app.lazy import lazy
news_screen = lazy("solitaireplus.career.news_screen")
leaderboard_engine = lazy("solitaireplus.career.leaderboard_engine")
game_globals = lazy("solitaireplus.app.game_globals")


def check_player_rating_world_reactions():
    stories, updated_flags = rating_milestone_stories(
        state.player_name,
        state.career_ratings,
        state.career_rating_news_flags,
    )
    state.career_rating_news_flags = updated_flags
    for headline, body, category in stories:
        news_screen.add_career_news(headline, body, category)


def grant_rating_cosmetics(force=False):
    if force or state.current_game_mode in ("career", "head_to_head"):
        unlock_ratings(state.career_ratings, (MENU_BACKGROUNDS, FELTS, TITLES),
                       (state.unlocked_menu_backgrounds, state.unlocked_felts, state.unlocked_titles))
        check_player_rating_world_reactions()


def award_career_rating(rating_key, amount):
    """Apply a game reward and synchronize the derived Overall mirror."""
    if state.current_game_mode not in ("career", "head_to_head") or rating_key not in GAME_RATING_KEYS:
        return 0
    actual = apply_rating_change(state.career_ratings, rating_key, amount)
    state.career_rating = state.career_ratings["overall"]
    grant_rating_cosmetics()
    return actual


def rate_competitive_game(game_key, opponent, won):
    if state.current_game_mode not in ("career", "head_to_head"):
        return 0
    change = settle_competitive_result(
        state.career_ratings, state.career_rating_results, state.career_leaderboard_state,
        game_key, opponent, 1.0 if won else 0.0,
    )
    state.career_rating = state.career_ratings["overall"]
    grant_rating_cosmetics()
    leaderboard_engine.sync_career_npc_runtime_state()
    return change


def preview_competitive_rating(game_key, opponent, won):
    if state.current_game_mode not in ("career", "head_to_head") or not isinstance(opponent, dict):
        return 0
    opponent_state = state.career_leaderboard_state.get(opponent.get("id"), {})
    bundle = opponent_state.get("ratings") or opponent.get("career_ratings") or opponent.get("ratings") or {}
    opponent_rating = bundle.get(game_key, opponent.get("race_rating", opponent.get("rating", 1000)))
    requested = elo_delta(state.career_ratings[game_key], opponent_rating, 1 if won else 0)
    if game_key == "score_four":
        requested = {"low":45, "mid":60, "strong":50, "elite":65}.get(opponent.get("skill_tier"),60) if won else -10
    from solitaireplus.career.ratings import reward_scale
    if requested > 0: requested *= reward_scale(state.career_ratings[game_key])

    return int(round(max(100, state.career_ratings[game_key] + requested))) - int(round(state.career_ratings[game_key]))


def rate_house_game(game_key, net):
    if state.current_game_mode != "career":
        return 0
    change = settle_house_result(state.career_ratings, state.career_rating_results, game_key, net)
    state.career_rating = state.career_ratings["overall"]
    grant_rating_cosmetics()
    return change


def rate_poker_cash_out(game_key, poker_game):
    if state.current_game_mode != "career":
        return 0
    change = settle_poker_session(
        state.career_ratings, state.career_rating_results, state.career_leaderboard_state,
        game_key, poker_game,
    )
    state.career_rating = state.career_ratings["overall"]
    grant_rating_cosmetics()
    leaderboard_engine.sync_career_npc_runtime_state()
    return change



def award_career_fans(amount, reason=""):

    try:
        amount = int(round(amount))
    except (TypeError, ValueError):
        return 0

    before = int(state.career_fans)
    state.career_fans = clamp_fans(before + amount)
    actual = state.career_fans - before

    state.career_last_fan_change = actual
    state.career_last_fan_reason = str(reason or "")
    state.career_fan_trend = record_fan_trend(
        state.career_fan_trend,
        actual,
        reason=state.career_last_fan_reason,
        day=game_globals.game_namespace().get("career_day"),
    )

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
                    before < milestone <= state.career_fans
                    and milestone not in state.career_fan_news_milestones
            ):
                state.career_fan_news_milestones.add(milestone)
                news_screen.add_career_news(
                    f"{state.player_name.upper()} SURPASSES {label} FANS",
                    (
                        f"{state.player_name} has crossed the {label}-fan mark. "
                        f"The latest surge followed {reason.lower() if reason else 'recent competition'}."
                    ),
                    "fans"
                )

    return actual


def award_fans_for_rating_win(rating_gain, reason="Game win"):
    gain = fan_gain_from_rating_win(
        rating_gain,
        current_rating=state.career_rating
    )
    return award_career_fans(gain, reason)


def award_fans_for_cash_win(net_win, reason="Casino win"):
    gain = fan_gain_from_cash_win(
        net_win,
        current_rating=state.career_rating
    )
    return award_career_fans(gain, reason)


def lose_fans_for_bad_result(reason="Poor performance", net_loss=0, severity=1.0):
    loss = fan_loss_from_bad_result(
        current_fans=state.career_fans,
        net_loss=net_loss,
        severity=severity,
    )
    if loss <= 0:
        return 0
    return award_career_fans(-loss, reason)
