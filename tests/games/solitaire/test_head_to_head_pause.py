"""B8: the Head-to-Head opponent must not keep racing while the player is away from the table
(pause -> Options, the F10 menu). The time away does not count: the opponent resumes where it
was. A race the player never leaves is unchanged (same progress, same finish time)."""
import bisect
import random
import unittest
from types import SimpleNamespace

from tests.support import locate
from solitaireplus.games.solitaire.head_to_head import (HEAD_TO_HEAD_COUNTDOWN_MS, HEAD_TO_HEAD_TARGET_CARDS,
                                                        HeadToHeadRace)

PLAYING = "playing"
OPTIONS = "options"
DEBUG_MENU = "debug_menu"
OPPONENT = {"id": "rival", "name": "Rival", "rating": 1000, "race_rating": 1000}
FRAME_MS = 1000
AWAY_MS = 600_000   # ten minutes: longer than any opponent needs for the whole race


class Clock:
    """A controlled pygame.time."""

    def __init__(self):
        self.now = 0

    def get_ticks(self):
        return self.now


def make_race(seed=7):
    race = HeadToHeadRace(random.Random(seed))
    race.prepare(OPPONENT, 1000, now_ms=0)
    return race


class Table:
    """The real update_solitaire_round, run once per frame with a controlled clock."""

    def __init__(self, race):
        self.race = race
        self.clock = Clock()
        self.finished = []
        self.env = {
            "head_to_head_race": race,
            "pygame": SimpleNamespace(time=self.clock),
            "current_state": PLAYING,
            "current_game_mode": "head_to_head",
            "STATE_PLAYING": PLAYING,
            "STATE_OPTIONS": OPTIONS,
            # the player's round clock starts with the race clock (B3)
            "game": SimpleNamespace(round_summary=None, consume_round_summary=lambda: None,
                                    round_start_ticks=race.race_started_ms),
            "finish_head_to_head_race": self.finish,
        }
        locate.exec_functions(["update_solitaire_round"], self.env)

    def finish(self, won, round_data=None, forfeited=False):
        self.finished.append((won, self.clock.now))
        return True

    def frame(self, now, screen=PLAYING):
        self.clock.now = now
        self.env["current_state"] = screen
        self.env["update_solitaire_round"]()

    def run(self, start, end, screen=PLAYING):
        """One frame every FRAME_MS from start to end (both included)."""
        for now in range(start, end + 1, FRAME_MS):
            self.frame(now, screen)

    def first_finish(self):
        return self.finished[0] if self.finished else None


def expected_progress(race, now):
    """The opponent's cards at wall time `now` of a race started at 0 that nobody paused."""
    elapsed = max(0, now - HEAD_TO_HEAD_COUNTDOWN_MS)
    return min(HEAD_TO_HEAD_TARGET_CARDS, bisect.bisect_right(race.card_completion_ms, elapsed))


def reference_finish_time(seed=7):
    """When the opponent of a race nobody leaves finishes, frame by frame."""
    table = Table(make_race(seed))
    table.run(0, 900_000)
    return table.first_finish()


class OptionsPausesTheOpponentTests(unittest.TestCase):
    def test_time_in_options_does_not_advance_the_opponent(self):
        table = Table(make_race())
        table.run(0, 60_000)
        cards_before = table.race.npc_progress_cards
        elapsed_before = table.race.elapsed_ms(60_000)
        self.assertGreater(cards_before, 0)
        self.assertLess(cards_before, HEAD_TO_HEAD_TARGET_CARDS)

        table.run(60_000 + FRAME_MS, 60_000 + AWAY_MS, OPTIONS)
        self.assertEqual(table.race.npc_progress_cards, cards_before)
        self.assertIsNone(table.race.winner)

        back = 60_000 + AWAY_MS + FRAME_MS
        table.frame(back)
        self.assertEqual(table.finished, [])
        self.assertIsNone(table.race.winner)
        self.assertEqual(table.race.npc_progress_cards, cards_before)
        self.assertEqual(table.race.elapsed_ms(back), elapsed_before + FRAME_MS)

    def test_opponent_resumes_where_it_was(self):
        won, finished_at = reference_finish_time()
        self.assertFalse(won)
        away_start = 60_000
        table = Table(make_race())
        table.run(0, away_start)
        table.run(away_start + FRAME_MS, away_start + AWAY_MS, OPTIONS)
        table.run(away_start + AWAY_MS + FRAME_MS, 2_000_000)
        self.assertEqual(table.first_finish(), (False, finished_at + AWAY_MS))

    def test_options_during_the_countdown_keeps_the_countdown(self):
        table = Table(make_race())
        table.run(0, 1000)
        self.assertEqual(table.race.countdown_remaining(1000), HEAD_TO_HEAD_COUNTDOWN_MS - 1000)
        table.run(2000, 50_000, OPTIONS)
        table.frame(51_000)
        self.assertTrue(table.race.is_countdown_active(51_000))
        self.assertEqual(table.race.countdown_remaining(51_000), HEAD_TO_HEAD_COUNTDOWN_MS - 2000)
        self.assertEqual(table.race.npc_progress_cards, 0)

    def test_any_screen_other_than_the_table_pauses(self):
        table = Table(make_race())
        table.run(0, 30_000)
        elapsed_before = table.race.elapsed_ms(30_000)
        table.run(31_000, 31_000 + AWAY_MS, DEBUG_MENU)
        table.frame(32_000 + AWAY_MS)
        self.assertEqual(table.race.elapsed_ms(32_000 + AWAY_MS), elapsed_before + FRAME_MS)
        self.assertEqual(table.finished, [])

    def test_player_clock_skips_the_time_away_too(self):
        # Review of B3 + B8: the player's own round clock (Game.round_start_ticks, which B3
        # starts at GO) must skip the time away like the race clock, during the countdown
        # and after GO.
        for away_start in (500, 30_000):
            table = Table(make_race())
            game = table.env["game"]
            table.run(0, away_start)
            table.run(away_start + FRAME_MS, away_start + AWAY_MS, OPTIONS)
            back = away_start + AWAY_MS + 5 * FRAME_MS
            table.frame(back)
            self.assertEqual(max(0, back - game.round_start_ticks), table.race.elapsed_ms(back), away_start)

    def test_player_who_never_leaves_sees_the_same_race(self):
        race = make_race()
        table = Table(race)
        for now in range(0, 900_000, 16):
            table.frame(now)
            if table.finished:
                break
            self.assertEqual(race.npc_progress_cards, expected_progress(race, now), now)
        finish_wall_time = HEAD_TO_HEAD_COUNTDOWN_MS + race.card_completion_ms[-1]
        first_frame_at_or_after = -(-finish_wall_time // 16) * 16
        self.assertEqual(table.first_finish(), (False, first_frame_at_or_after))
        self.assertEqual(race.finished_ms, first_frame_at_or_after)
        self.assertEqual(race.winner, "npc")


class RacePauseTests(unittest.TestCase):
    def test_clock_stands_still_while_paused(self):
        race = make_race()
        race.update(40_000)
        race.pause(40_000)
        self.assertEqual(race.elapsed_ms(400_000), 37_000)
        self.assertEqual(race.format_elapsed(400_000), "0:37")
        self.assertEqual(race.update(400_000), expected_progress(race, 40_000))
        self.assertIsNone(race.winner)
        race.resume(400_000)
        self.assertEqual(race.elapsed_ms(401_000), 38_000)

    def test_second_pause_keeps_the_first_pause_time(self):
        race = make_race()
        race.pause(10_000)
        race.pause(20_000)
        race.resume(30_000)
        self.assertEqual(race.elapsed_ms(30_000), 7_000)

    def test_resume_without_pause_changes_nothing(self):
        race = make_race()
        race.resume(50_000)
        self.assertEqual(race.elapsed_ms(50_000), 47_000)

    def test_no_pause_before_a_race_or_after_it_ends(self):
        race = HeadToHeadRace(random.Random(1))
        race.pause(1000)
        self.assertEqual(race.elapsed_ms(5000), 0)
        race = make_race()
        race.mark_winner("player", 20_000)
        race.pause(20_000)
        self.assertEqual(race.elapsed_ms(30_000), 27_000)

    def test_prepare_clears_a_pause(self):
        race = make_race()
        race.pause(10_000)
        race.prepare(OPPONENT, 1000, now_ms=100_000)
        self.assertEqual(race.elapsed_ms(110_000), 7_000)


if __name__ == "__main__":
    unittest.main()
