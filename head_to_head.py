import bisect
import math
import random


HEAD_TO_HEAD_TARGET_CARDS = 52
HEAD_TO_HEAD_COUNTDOWN_MS = 3000


def _clamp(value, low, high):
    return max(low, min(high, value))


def select_head_to_head_opponents(leaderboard, player_rating, count=4):
    """Return nearby NPC rivals, favoring two just above and two just below.

    ``leaderboard`` is the same entry structure used by the Career leaderboard.
    The function stays UI/game agnostic so it is easy to test independently.
    """
    try:
        player_rating = int(player_rating)
    except (TypeError, ValueError):
        player_rating = 1000

    candidates = [
        entry
        for entry in list(leaderboard or [])
        if isinstance(entry, dict)
        and not entry.get("is_player")
        and entry.get("id") not in (None, "player")
    ]

    if not candidates:
        return []

    def rating_of(entry):
        try:
            return int(entry.get("rating", 1000))
        except (TypeError, ValueError):
            return 1000

    above = sorted(
        [entry for entry in candidates if rating_of(entry) >= player_rating],
        key=lambda entry: (rating_of(entry) - player_rating, entry.get("name", "")),
    )
    below = sorted(
        [entry for entry in candidates if rating_of(entry) < player_rating],
        key=lambda entry: (player_rating - rating_of(entry), entry.get("name", "")),
    )

    selected = []
    selected_ids = set()

    # Interleave nearby stronger/weaker opponents when possible. Two of each is
    # the normal four-card matchup screen, but the fallback also works near the
    # very top/bottom of the ranking list.
    preferred = []
    for index in range(max(2, count)):
        if index < 2 and index < len(above):
            preferred.append(above[index])
        if index < 2 and index < len(below):
            preferred.append(below[index])

    for entry in preferred:
        entry_id = entry.get("id")
        if entry_id in selected_ids:
            continue
        selected.append(entry)
        selected_ids.add(entry_id)
        if len(selected) >= count:
            return selected[:count]

    remaining = sorted(
        [entry for entry in candidates if entry.get("id") not in selected_ids],
        key=lambda entry: (abs(rating_of(entry) - player_rating), entry.get("name", "")),
    )

    for entry in remaining:
        selected.append(entry)
        if len(selected) >= count:
            break

    return selected[:count]


def calculate_head_to_head_rating_reward(player_rating, opponent_rating, won):
    from career_ratings import elo_delta
    return elo_delta(player_rating, opponent_rating, 1 if won else 0)


class HeadToHeadRace:
    """Simulate an NPC Klondike solve while the human plays the real board."""

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.reset()

    def reset(self):
        self.opponent = None
        self.player_rating = 1000
        self.opponent_rating = 1000
        self.countdown_started_ms = None
        self.race_started_ms = None
        self.target_duration_ms = 300_000
        self.card_completion_ms = []
        self.npc_progress_cards = 0
        self.winner = None
        self.reward_claimed = False
        self.finished_ms = None

    def prepare(self, opponent, player_rating=1000, now_ms=0):
        self.reset()
        self.opponent = dict(opponent or {})

        try:
            self.player_rating = int(player_rating)
        except (TypeError, ValueError):
            self.player_rating = 1000

        try:
            self.opponent_rating = int(self.opponent.get("race_rating", self.opponent.get("rating", 1000)))
        except (TypeError, ValueError):
            self.opponent_rating = 1000

        # Around 6.5 minutes for a 1000-rated player, descending toward roughly
        # 2 minutes for the elite end. The random spread makes repeat matchups
        # feel like actual runs rather than metronomes.
        seconds = 420.0 - (self.opponent_rating - 800) * 0.11
        seconds = _clamp(seconds, 125.0, 445.0)
        seconds *= self.rng.uniform(0.88, 1.13)
        self.target_duration_ms = max(90_000, int(seconds * 1000))

        # Build 52 irregular completion checkpoints. Occasional heavier weights
        # model a stalled tableau/stock cycle, while later cards get modestly
        # quicker as a real Klondike board opens up.
        weights = []
        for card_index in range(HEAD_TO_HEAD_TARGET_CARDS):
            progress = card_index / max(1, HEAD_TO_HEAD_TARGET_CARDS - 1)
            weight = self.rng.uniform(0.72, 1.32)
            weight *= 1.12 - progress * 0.22
            if self.rng.random() < 0.095:
                weight *= self.rng.uniform(1.5, 2.5)
            weights.append(weight)

        total = max(0.001, sum(weights))
        cumulative = 0.0
        self.card_completion_ms = []
        for weight in weights:
            cumulative += weight
            self.card_completion_ms.append(
                int(self.target_duration_ms * (cumulative / total))
            )

        self.countdown_started_ms = int(now_ms)
        self.race_started_ms = self.countdown_started_ms + HEAD_TO_HEAD_COUNTDOWN_MS
        return self

    def countdown_remaining(self, now_ms):
        if self.race_started_ms is None:
            return 0
        return max(0, self.race_started_ms - int(now_ms))

    def is_countdown_active(self, now_ms):
        return self.winner is None and self.countdown_remaining(now_ms) > 0

    def elapsed_ms(self, now_ms):
        if self.race_started_ms is None:
            return 0
        return max(0, int(now_ms) - self.race_started_ms)

    def update(self, now_ms):
        if self.opponent is None or self.winner is not None:
            return self.npc_progress_cards

        if self.is_countdown_active(now_ms):
            self.npc_progress_cards = 0
            return 0

        elapsed = self.elapsed_ms(now_ms)
        self.npc_progress_cards = bisect.bisect_right(
            self.card_completion_ms,
            elapsed,
        )
        self.npc_progress_cards = min(
            HEAD_TO_HEAD_TARGET_CARDS,
            self.npc_progress_cards,
        )

        if self.npc_progress_cards >= HEAD_TO_HEAD_TARGET_CARDS:
            self.mark_winner("npc", now_ms)

        return self.npc_progress_cards

    def mark_winner(self, winner, now_ms):
        if self.winner is not None:
            return False
        if winner not in ("player", "npc"):
            return False
        self.winner = winner
        self.finished_ms = int(now_ms)
        return True

    def player_progress_from_foundations(self, foundations):
        return min(
            HEAD_TO_HEAD_TARGET_CARDS,
            sum(len(pile or []) for pile in list(foundations or [])),
        )

    def progress_fraction(self):
        return self.npc_progress_cards / float(HEAD_TO_HEAD_TARGET_CARDS)

    def format_elapsed(self, now_ms):
        elapsed_seconds = self.elapsed_ms(now_ms) // 1000
        minutes, seconds = divmod(elapsed_seconds, 60)
        return f"{minutes}:{seconds:02d}"

    def countdown_label(self, now_ms):
        remaining = self.countdown_remaining(now_ms)
        if remaining <= 0:
            return "GO!"
        return str(max(1, int(math.ceil(remaining / 1000.0))))

