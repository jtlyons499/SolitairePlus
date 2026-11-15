"""NPC action timing follows the table speed in Five-O and Blind Man's Bluff (B86 group 6).

Hold'em, Draw and Stud already pace every NPC decision with holdem_ui.get_holdem_npc_delay()
(1800 / 1200 / 600 ms for slow / normal / fast). The two niche tables now do too:

* Five-O: the engine's npc_delay_seconds (default 0.65 s, the old fixed pause) times the NPC's
  answer to the human, and, when the NPC opens the betting, its opening action (bet_state
  "npc_open"). With a delay of 0 the opening is immediate, as before.
* Blind Man's Bluff: with npc_delay_seconds > 0, _advance stops before an NPC turn
  (pending_npc_at) and update() runs exactly one queued NPC turn once it is due. The default
  of 0 keeps the engine synchronous for tests and simulations.
* The screens set npc_delay_seconds from the table speed every frame (sync_npc_delay), before
  the engine's update().

Kept as they are: Five-O's instant card placements, its column-reveal interval and the manual
Next Hand of both tables.

B86 review: F8 (Five-O's prompt names raising only when the human may raise) and F11 (a queued
Five-O NPC turn never runs once the hand has settled).
"""
import random
import unittest
from types import SimpleNamespace
from unittest import mock

from solitaireplus.app import state
from solitaireplus.games.poker import blind_mans_bluff_screen, five_o_screen
from solitaireplus.games.poker.ai import get_poker_personality_profile
from solitaireplus.games.poker.blind_mans_bluff import BlindMansBluffGame
from solitaireplus.games.poker.five_o import FiveOPokerGame
from tests.support.poker_variants import ADAPTERS_BY_KEY

FIVE_O = ADAPTERS_BY_KEY["five_o_poker"]
BMB = ADAPTERS_BY_KEY["blind_mans_bluff"]

FIVE_O_DECISION = "solitaireplus.games.poker.five_o.decide_poker_action"
BMB_DECISION = "solitaireplus.games.poker.blind_mans_bluff.decide_poker_action"

TABLE_SPEEDS = (("slow", 1.8), ("normal", 1.2), ("fast", 0.6))


class FakeClock:
    """Stands in for the time module an engine reads time.monotonic() from."""

    def __init__(self, now=1000.0):
        self.now = now

    def monotonic(self):
        return self.now


def patch_clock(testcase, engine_module, now=1000.0):
    clock = FakeClock(now)
    patcher = mock.patch(f"solitaireplus.games.poker.{engine_module}.time", clock)
    patcher.start()
    testcase.addCleanup(patcher.stop)
    return clock


def forced(target, action, calls=None):
    """Patch an engine's decide_poker_action to always answer `action`; calls counts decisions."""
    def decide(personality, context, rng=None):
        if calls is not None:
            calls.append(dict(context))
        return {"action": action, "profile": get_poker_personality_profile("balanced"), "bluff": False}

    return mock.patch(target, decide)


# ==================================================
# FIVE-O
# ==================================================

class FiveOTimingTests(unittest.TestCase):
    def setUp(self):
        self.clock = patch_clock(self, "five_o")

    def new_hand(self, npc_opens=False, delay=0.3):
        game = FIVE_O.new_game(random.Random("timing-five-o"))
        game.npc_delay_seconds = delay
        if npc_opens:
            game.hand_number = 1   # start_hand deals hand 2: the NPC opens even-numbered hands
        self.assertTrue(FIVE_O.start_hand(game))
        self.assertEqual(game.opening_index, 1 if npc_opens else 0)
        return game

    @staticmethod
    def place_cards(game):
        # Placements stay instant; the last one starts the betting round.
        while game.phase == "placement":
            game.place_player_card(game.get_available_player_columns()[0])

    def test_engine_default_keeps_the_old_pause(self):
        self.assertEqual(FiveOPokerGame().npc_delay_seconds, 0.65)

    def test_response_waits_for_the_delay(self):
        game = self.new_hand(delay=0.3)
        total = FIVE_O.total_chips(game)
        calls = []
        with forced(FIVE_O_DECISION, "call", calls):
            self.place_cards(game)
            self.assertEqual(game.bet_state, "player_open")
            self.clock.now = 1000.0
            self.assertTrue(game.player_bet())
            bet = game.current_bet
            self.assertAlmostEqual(game.pending_npc_at, 1000.3)
            self.assertEqual(game.result_text, f"{game.get_npc_name()} is considering the action…")
            self.assertEqual(game.get_player_actions(), [])

            self.clock.now = 1000.29
            game.update()
            self.assertEqual(calls, [])
            self.assertAlmostEqual(game.pending_npc_at, 1000.3)
            self.assertEqual(game.npc_betting_paid, 0)
            self.assertEqual(game.phase, "betting")

            self.clock.now = 1000.31
            game.update()
        self.assertEqual(len(calls), 1)
        self.assertEqual(game.pending_npc_at, 0.0)
        self.assertEqual(game.npc_betting_paid, bet)
        self.assertEqual(game.last_npc_action, f"{game.get_npc_name()} calls ${bet:,}.")
        self.assertTrue(game.showdown_pending_finish)
        self.assertEqual(FIVE_O.total_chips(game), total)

    def test_opening_bet_is_queued_and_resolved_the_same_way(self):
        game = self.new_hand(npc_opens=True, delay=0.3)
        total = FIVE_O.total_chips(game)
        calls = []
        with forced(FIVE_O_DECISION, "bet", calls):
            self.clock.now = 2000.0
            self.place_cards(game)
            self.assertEqual(game.phase, "betting")
            self.assertEqual(game.bet_state, "npc_open")
            self.assertAlmostEqual(game.pending_npc_at, 2000.3)
            self.assertEqual(game.result_text, f"{game.get_npc_name()} is considering the action…")
            self.assertEqual(game.current_bet, 0)
            self.assertEqual(game.get_player_actions(), [])
            self.assertEqual(calls, [])

            self.clock.now = 2000.29
            game.update()
            self.assertEqual(calls, [])
            self.assertEqual(game.bet_state, "npc_open")
            self.assertEqual(game.current_bet, 0)

            self.clock.now = 2000.31
            game.update()
        self.assertEqual(len(calls), 1)
        self.assertFalse(calls[0]["can_raise"])   # nothing bet yet: the NPC opens
        self.assertEqual(game.pending_npc_at, 0.0)
        self.assertEqual(game.bet_state, "player_response")
        self.assertGreater(game.current_bet, 0)
        self.assertEqual(game.npc_betting_paid, game.current_bet)
        name = game.get_npc_name()
        self.assertEqual(game.last_npc_action, f"{name} bets ${game.current_bet:,}.")
        # The human may raise (the "bet" action), so the prompt names raising (F8).
        self.assertEqual(game.result_text, f"{name} opens for ${game.current_bet:,}. Call, raise or fold.")
        self.assertEqual(game.get_player_actions(), ["fold", "call", "bet"])
        self.assertEqual(FIVE_O.total_chips(game), total)
        FIVE_O.play_hand(game, random.Random(1))
        self.assertEqual(FIVE_O.total_chips(game), total)

    def test_queued_opening_check_hands_the_last_action_to_the_human(self):
        game = self.new_hand(npc_opens=True, delay=0.3)
        with forced(FIVE_O_DECISION, "check"):
            self.clock.now = 3000.0
            self.place_cards(game)
            self.assertEqual(game.bet_state, "npc_open")
            self.clock.now = 3000.31
            game.update()
        name = game.get_npc_name()
        self.assertEqual(game.bet_state, "player_last_open")
        self.assertEqual(game.last_npc_action, f"{name} checks.")
        self.assertEqual(game.result_text, f"{name} checks. Action is on you.")
        self.assertEqual(game.current_bet, 0)
        self.assertEqual(game.get_player_actions(), ["check", "bet"])

    def test_zero_delay_opens_at_once(self):
        game = self.new_hand(npc_opens=True, delay=0)
        calls = []
        with forced(FIVE_O_DECISION, "bet", calls):
            self.place_cards(game)
            self.assertEqual(len(calls), 1)
            self.assertEqual(game.pending_npc_at, 0.0)
            self.assertEqual(game.bet_state, "player_response")
            self.assertGreater(game.current_bet, 0)
            self.assertEqual(game.result_text,
                             f"{game.get_npc_name()} opens for ${game.current_bet:,}. Call, raise or fold.")
            # The answer to the human's raise is still queued, and due at once.
            self.clock.now = 4000.0
            self.assertTrue(game.player_bet())
            self.assertEqual(game.pending_npc_at, 4000.0)
            game.update()
        self.assertEqual(len(calls), 2)
        self.assertEqual(game.pending_npc_at, 0.0)

    def test_prompt_names_raising_only_when_the_human_can_raise(self):
        # F8: the raise cap. Bet, NPC raise, raise, NPC raise: three raises after the bet.
        game = self.new_hand(delay=0.3)
        name = game.get_npc_name()
        with forced(FIVE_O_DECISION, "raise"):
            self.place_cards(game)
            self.assertTrue(game.player_bet())
            self.clock.now += 1.0
            game.update()
            self.assertEqual(game.raise_count, 1)
            self.assertIn("bet", game.get_player_actions())
            self.assertEqual(game.result_text, f"{name} raises to ${game.current_bet:,}. Call, raise or fold.")
            self.assertTrue(game.player_bet())
            self.clock.now += 1.0
            game.update()
        self.assertEqual(game.raise_count, 3)
        self.assertEqual(game.get_player_actions(), ["fold", "call"])
        self.assertEqual(game.result_text, f"{name} raises to ${game.current_bet:,}. Call or fold.")

    def test_an_all_in_opening_bet_cannot_be_raised(self):
        # F8: the NPC opens with all it has left, so nobody could answer a raise.
        game = self.new_hand(npc_opens=True, delay=0)
        game.npc_stack = 7
        with forced(FIVE_O_DECISION, "bet"):
            self.place_cards(game)
        self.assertEqual(game.npc_stack, 0)
        self.assertEqual(game.get_player_actions(), ["fold", "call"])
        self.assertEqual(game.result_text, f"{game.get_npc_name()} opens for $7. Call or fold.")

    def test_an_npc_bet_after_the_human_checks_names_raising_when_offered(self):
        # A guard for the wording kept from before F8 (the case F8 changed is the next test).
        game = self.new_hand(delay=0.3)
        with forced(FIVE_O_DECISION, "bet"):
            self.place_cards(game)
            self.assertTrue(game.player_check())
            self.clock.now += 1.0
            game.update()
        self.assertEqual(game.get_player_actions(), ["fold", "call", "bet"])
        self.assertEqual(game.result_text,
                         f"{game.get_npc_name()} bets ${game.current_bet:,}. Call, raise or fold.")

    def test_an_all_in_npc_bet_after_the_human_checks_cannot_be_raised(self):
        # F8: the NPC bets all it has left after the human checks, so nobody could answer a
        # raise; the prompt said "Call, raise or fold." on this path before.
        game = self.new_hand(delay=0.3)
        game.npc_stack = 7
        with forced(FIVE_O_DECISION, "bet"):
            self.place_cards(game)
            self.assertTrue(game.player_check())
            self.clock.now += 1.0
            game.update()
        self.assertEqual(game.npc_stack, 0)
        self.assertEqual(game.get_player_actions(), ["fold", "call"])
        self.assertEqual(game.result_text, f"{game.get_npc_name()} bets $7. Call or fold.")

    def test_a_queued_opening_never_runs_on_a_settled_hand(self):
        # F11: the hand reaches its showdown while the NPC's opening is still queued.
        game = self.new_hand(npc_opens=True, delay=0.3)
        calls = []
        with forced(FIVE_O_DECISION, "bet", calls):
            self.clock.now = 5000.0
            self.place_cards(game)
            self.assertEqual(game.bet_state, "npc_open")
            game._showdown()
            self.assertEqual(game.pending_npc_at, 0.0)
            total, stacks = FIVE_O.total_chips(game), FIVE_O.stacks(game)
            self.clock.now = 5001.0
            game.update()
            # Even with a turn left queued on a completed hand, update() drops it.
            game.showdown_reveal_started_at -= 1000.0
            game.update()
            self.assertTrue(game.hand_complete)
            game.pending_npc_at = 5000.5
            game.update()
        self.assertEqual(calls, [])
        self.assertEqual(game.pending_npc_at, 0.0)
        self.assertEqual(game.current_bet, 0)
        self.assertEqual(FIVE_O.stacks(game), stacks)
        self.assertEqual(FIVE_O.total_chips(game), total)

    def test_reveal_interval_and_placements_are_unchanged(self):
        game = self.new_hand(npc_opens=True, delay=1.8)
        self.assertEqual(game.showdown_reveal_interval, 1.1)
        placed = 0
        while game.phase == "placement":
            self.assertEqual(game.pending_npc_at, 0.0)   # NPC placements never wait
            game.place_player_card(game.get_available_player_columns()[0])
            placed += 1
        self.assertEqual(placed, 20)   # four layers of five columns
        self.assertTrue(all(len(column) == 5 for column in game.npc_columns))


# ==================================================
# BLIND MAN'S BLUFF
# ==================================================

class BlindMansBluffTimingTests(unittest.TestCase):
    def setUp(self):
        self.clock = patch_clock(self, "blind_mans_bluff")

    def new_game(self, delay, name="timing-bmb"):
        game = BMB.new_game(random.Random(name))
        game.npc_delay_seconds = delay
        return game

    def npc_opens(self, game):
        game.hand_number = 1   # hand 2: seat 1 opens
        self.assertTrue(BMB.start_hand(game))
        self.assertEqual(game.opening_index, 1)

    def test_engine_default_is_synchronous(self):
        game = BlindMansBluffGame()
        self.assertEqual(game.npc_delay_seconds, 0.0)
        self.assertEqual(game.pending_npc_at, 0.0)

    def test_start_hand_stops_at_the_first_npc_seat(self):
        game = self.new_game(0.5)
        calls = []
        self.clock.now = 50.0
        with forced(BMB_DECISION, "check", calls):
            self.npc_opens(game)
        self.assertEqual(calls, [])
        self.assertEqual(game.current_actor, 1)
        self.assertAlmostEqual(game.pending_npc_at, 50.5)
        self.assertEqual(game.result_text, f"{game.get_name(1)} is thinking…")
        self.assertEqual(game.last_actions, [""] * 4)
        self.assertEqual(game.round_bets, [0] * 4)
        self.assertEqual(game.pot, 4 * game.ante)
        self.assertEqual(game.get_player_actions(), [])
        self.assertFalse(game.player_check())

    def test_update_runs_exactly_one_npc_turn_when_due(self):
        game = self.new_game(0.5)
        total = BMB.total_chips(game)
        calls = []
        self.clock.now = 50.0
        with forced(BMB_DECISION, "check", calls):
            self.npc_opens(game)
            self.clock.now = 50.49
            self.assertFalse(game.update())
            self.assertEqual(calls, [])
            self.assertEqual((game.current_actor, game.last_actions[1]), (1, ""))
            self.assertFalse(game.update(now=50.49))

            for seat, due in ((1, 50.5), (2, 51.0), (3, 51.5)):
                self.clock.now = due
                self.assertTrue(game.update())
                self.assertEqual(len(calls), seat)
                self.assertEqual(game.last_actions[seat], "Checked")
                if seat < 3:
                    self.assertEqual(game.current_actor, seat + 1)
                    self.assertAlmostEqual(game.pending_npc_at, due + 0.5)
                    self.assertEqual(game.result_text, f"{game.get_name(seat + 1)} is thinking…")
                    self.assertEqual(game.last_actions[seat + 1], "")
                    self.assertEqual(game.get_player_actions(), [])
            # The human is last to act: no NPC is queued and the human has the action.
            self.assertEqual(game.current_actor, 0)
            self.assertEqual(game.pending_npc_at, 0.0)
            self.assertIn("check", game.get_player_actions())

            # The human bets: the NPCs answer one at a time again.
            self.clock.now = 60.0
            self.assertTrue(game.player_bet(game._base_minimum()))
            self.assertEqual(game.current_actor, 1)
            self.assertAlmostEqual(game.pending_npc_at, 60.5)
            self.assertEqual(len(calls), 3)
        with forced(BMB_DECISION, "call", calls):
            for seat, due in ((1, 60.5), (2, 61.0), (3, 61.5)):
                self.clock.now = due
                self.assertTrue(game.update(now=due))
                self.assertEqual(len(calls), 3 + seat)
                self.assertTrue(game.last_actions[seat].startswith("Called"))
        self.assertTrue(game.hand_complete)
        self.assertEqual(game.pending_npc_at, 0.0)
        self.assertFalse(game.update())
        self.assertEqual(BMB.total_chips(game), total)

    def test_zero_delay_is_synchronous_as_before(self):
        game = self.new_game(0)
        calls = []
        with forced(BMB_DECISION, "check", calls):
            self.npc_opens(game)
        self.assertEqual(len(calls), 3)
        self.assertEqual(game.current_actor, 0)
        self.assertEqual(game.pending_npc_at, 0.0)
        self.assertEqual(game.last_actions[1:], ["Checked"] * 3)
        self.assertFalse(game.update())
        self.assertIn("check", game.get_player_actions())

    def test_start_hand_clears_a_stale_pending_turn(self):
        game = self.new_game(0.5)
        self.clock.now = 70.0
        with forced(BMB_DECISION, "check"):
            self.npc_opens(game)
            self.assertTrue(game.pending_npc_at)
            game.hand_number = 2   # hand 3: seat 2 opens
            game.npc_delay_seconds = 0
            self.assertTrue(game.start_hand())
        self.assertEqual(game.pending_npc_at, 0.0)
        self.assertEqual(game.current_actor, 0)

    def test_chips_are_conserved_over_50_hands_driven_by_update(self):
        rng = random.Random("timing-bmb-conservation")
        stack_choices = [1, 8, 20, 60, 150, 400, 1000, 2500]
        hands = npc_turns = 0
        game = None
        while hands < 50:
            if game is None or game.session_complete:
                game = BMB.new_game(random.Random(rng.getrandbits(64)),
                                    stacks=[rng.choice(stack_choices) for _ in range(BMB.seat_count)])
                game.npc_delay_seconds = rng.choice([1.8, 1.2, 0.6])
                in_update, turns = self.instrument(game)
            total = BMB.total_chips(game)
            self.clock.now += 5.0
            if not BMB.start_hand(game):
                continue
            hands += 1
            for _ in range(200):
                self.assertEqual(BMB.total_chips(game), total)
                if game.hand_complete:
                    break
                if game.pending_npc_at:
                    actor, due = game.current_actor, game.pending_npc_at
                    self.assertNotEqual(actor, 0)
                    self.assertEqual(game.get_player_actions(), [])
                    self.clock.now = due - 0.01
                    self.assertFalse(game.update())
                    self.assertEqual((game.current_actor, game.pending_npc_at), (actor, due))
                    before = len(turns)
                    self.clock.now = due
                    self.assertTrue(game.update())
                    self.assertEqual(turns[before:], [actor])   # exactly one NPC acted
                    npc_turns += 1
                    # Then: the hand is over, the human has the action, or the next NPC is queued.
                    if not game.hand_complete:
                        if game.pending_npc_at:
                            self.assertAlmostEqual(game.pending_npc_at, due + game.npc_delay_seconds)
                        else:
                            self.assertEqual(game.current_actor, 0)
                            self.assertTrue(game.get_player_actions())
                    continue
                BMB.step(game, rng)
            else:
                self.fail(f"hand {game.hand_number} stalled")
            self.assertEqual(game.pot, 0)
            self.assertEqual(game.pending_npc_at, 0.0)
            self.assertEqual(BMB.total_chips(game), total)
            self.assertTrue(all(in_update))   # every NPC turn ran from update()
        self.assertGreater(npc_turns, 50)

    @staticmethod
    def instrument(game):
        """Record each NPC turn's seat, and whether it ran inside update()."""
        in_update, turns, inside = [], [], [False]
        take_turn, update = game._npc_take_turn, game.update

        def recording_take_turn(seat):
            in_update.append(inside[0])
            turns.append(seat)
            return take_turn(seat)

        def recording_update(now=None):
            inside[0] = True
            try:
                return update(now)
            finally:
                inside[0] = False

        game._npc_take_turn, game.update = recording_take_turn, recording_update
        return in_update, turns


# ==================================================
# SCREENS
# ==================================================

class ScreenDelayTests(unittest.TestCase):
    def setUp(self):
        speed = state.holdem_table_speed
        self.addCleanup(setattr, state, "holdem_table_speed", speed)
        # Set by the main loop at run time, read by draw().
        for name in ("game_mouse_pos", "player_name"):
            patcher = mock.patch.object(state, name, None, create=True)
            patcher.start()
            self.addCleanup(patcher.stop)

    def patch(self, module, **names):
        for name, value in names.items():
            patcher = mock.patch.object(module, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def drawing_stubs(self):
        return {
            "window": SimpleNamespace(game_surface=None),
            "legacy": SimpleNamespace(game=SimpleNamespace(card_fronts=None, get_card_back_surface=lambda: None)),
            "panels": SimpleNamespace(draw_submenu_background=None),
            "fonts": SimpleNamespace(options_title_font=None, option_label_font=None, difficulty_detail_font=None),
        }

    def test_sync_npc_delay_follows_the_table_speed(self):
        for module, game_class in ((five_o_screen, FiveOPokerGame), (blind_mans_bluff_screen, BlindMansBluffGame)):
            for speed, seconds in TABLE_SPEEDS:
                with self.subTest(module.__name__, speed=speed):
                    state.holdem_table_speed = speed
                    game = game_class()
                    module.sync_npc_delay(game)
                    self.assertAlmostEqual(game.npc_delay_seconds, seconds)

    def test_five_o_draw_sets_the_delay_before_update(self):
        log = []
        game = SimpleNamespace(npc_delay_seconds=0.65)
        game.update = lambda: log.append(("update", game.npc_delay_seconds))
        self.patch(five_o_screen, five_o_poker_game=game,
                   draw_five_o_poker=lambda *args, **kwargs: log.append("draw"), **self.drawing_stubs())
        for speed, seconds in TABLE_SPEEDS:
            with self.subTest(speed=speed):
                state.holdem_table_speed = speed
                log.clear()
                five_o_screen.draw()
                self.assertEqual(log, [("update", seconds), "draw"])

    def test_bluff_draw_runs_the_due_npc_turn_before_the_presentation(self):
        log = []
        game = SimpleNamespace(npc_delay_seconds=0.0)
        game.update = lambda: log.append(("update", game.npc_delay_seconds))
        self.patch(blind_mans_bluff_screen, blind_mans_bluff_game=game,
                   update_bluff_presentation=lambda g, play: log.append("presentation"),
                   draw_blind_mans_bluff=lambda *args, **kwargs: log.append("draw"),
                   sounds=SimpleNamespace(audio=SimpleNamespace(play_sound=lambda *a: None)),
                   **self.drawing_stubs())
        for speed, seconds in TABLE_SPEEDS:
            with self.subTest(speed=speed):
                state.holdem_table_speed = speed
                log.clear()
                blind_mans_bluff_screen.draw()
                self.assertEqual(log, [("update", seconds), "presentation", "draw"])

    def test_bluff_screen_frames_pace_a_real_hand(self):
        clock = patch_clock(self, "blind_mans_bluff", now=10.0)
        game = BMB.new_game(random.Random("timing-bmb-screen"))
        self.patch(blind_mans_bluff_screen, blind_mans_bluff_game=game,
                   update_bluff_presentation=lambda g, play: None,
                   draw_blind_mans_bluff=lambda *args, **kwargs: None,
                   sounds=SimpleNamespace(audio=SimpleNamespace(play_sound=lambda *a: None)),
                   **self.drawing_stubs())
        state.holdem_table_speed = "fast"
        blind_mans_bluff_screen.draw()             # a frame before Next Hand syncs the delay
        self.assertAlmostEqual(game.npc_delay_seconds, 0.6)
        with forced(BMB_DECISION, "check"):
            game.hand_number = 1                   # Next Hand deals hand 2: seat 1 opens
            self.assertTrue(game.start_hand())
            self.assertAlmostEqual(game.pending_npc_at, 10.6)
            clock.now = 10.59
            blind_mans_bluff_screen.draw()
            self.assertEqual(game.current_actor, 1)
            self.assertEqual(game.last_actions[1], "")
            clock.now = game.pending_npc_at
            blind_mans_bluff_screen.draw()
            self.assertEqual(game.last_actions[1], "Checked")
            self.assertEqual(game.current_actor, 2)
            self.assertAlmostEqual(game.pending_npc_at, 11.2)


if __name__ == "__main__":
    unittest.main()
