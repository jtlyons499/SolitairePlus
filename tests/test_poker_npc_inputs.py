"""The same NPC decision inputs in every poker variant (B86 group 5).

The maintainer asked that "NPC behavior should be consistent between all variants, including
holding grudges and behaving differently based on the amount of cash on hand". Every engine now
builds its NPC decision context through games/poker/npc_inputs.py:

* cash on hand: wealth_ratio, wealth_pressure (0 up to 1.15x the buy-in, full at 2.5x) times a
  per-variant scale, and minimum_open_bet for the short-stack tenacity rule;
* personality traits and the rating-based skill factor (Blind Man's Bluff has no rating, so it
  keeps the skill tier);
* grudges: recorded at a contested showdown with severity = the loser's contribution / buy-in
  (never on fold wins or splits); grudge_pressure only against the last full bettor/raiser;
* public table reads (opponent_reads, public_opponents), the player-tendency model and
  profile-owned rival learning in career;
* one session reset of all that memory.

Hold'em, Draw and Stud must not change at all: HoldemFamilySameInputsTests compares every
decision context of seeded hands with the formulas the inline code used. Five-O and Blind Man's
Bluff gain the inputs they lacked.

The contexts are captured where each engine hands them to decide_poker_action.

B86 review: F14 (every variant's NPC table talk goes through personality_chat.game_trait_chat,
so the decision's tactic line comes before the trait mix everywhere) and F15 (a human who is not
in the hand only gets the quick-chat lines that do not change NPC decisions).
"""
import contextlib
import copy
import json
import random
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

from solitaireplus.games.poker import ai as ai_module
from solitaireplus.games.poker.ai import (
    POKER_SKILL_FACTORS,
    PokerOpponentModel,
    get_poker_personality_profile,
    get_poker_skill_factor,
)
from solitaireplus.games.poker.learning import new_learning, normalize_learning
from solitaireplus.games.poker.strategy import PokerTableReads
from solitaireplus.npc.personality import PokerGrudgeMemory, get_npc_traits, npc_identity
from tests.support.poker_variants import ADAPTERS, ADAPTERS_BY_KEY, FORCED_STACK

HOLDEM_FAMILY = ("texas_holdem", "five_card_draw", "seven_card_stud")
BMB = ADAPTERS_BY_KEY["blind_mans_bluff"]
FIVE_O = ADAPTERS_BY_KEY["five_o_poker"]

# Where each engine looks up its NPC decision (the Hold'em family shares run_next_npc_action).
DECISION_FUNCTION = {
    "texas_holdem": "solitaireplus.games.poker.holdem.decide_poker_action",
    "five_card_draw": "solitaireplus.games.poker.holdem.decide_poker_action",
    "seven_card_stud": "solitaireplus.games.poker.holdem.decide_poker_action",
    "blind_mans_bluff": "solitaireplus.games.poker.blind_mans_bluff.decide_poker_action",
    "five_o_poker": "solitaireplus.games.poker.five_o.decide_poker_action",
}

SHARED_KEYS = (
    "personality_traits", "skill_factor", "npc_identity", "hand_number", "starting_stack",
    "wealth_ratio", "wealth_pressure", "wealth_variant_scale", "opponent_reads",
    "public_opponents", "player_tendencies", "player_active", "grudge_pressure", "grudge_target",
    "grudge_intensity", "grudge_target_round_total", "minimum_open_bet",
)
QUICK_CHAT_KEYS = (
    "quick_chat_aggression", "quick_chat_call_requirement_delta", "quick_chat_bluff_delta",
)

DRAW_WEALTH_SCALE = {"preflop": 0.80}
STUD_WEALTH_SCALE = {"third": 0.45, "fourth": 0.55, "fifth": 0.65, "sixth": 0.75, "seventh": 0.85}


def npc_inputs():
    """The shared module (imported late, so the per-variant tests still run without it)."""
    from solitaireplus.games.poker import npc_inputs as module
    return module


def expected_wealth_scale(adapter, game):
    stage = getattr(game, "current_stage", "")
    if adapter.key == "five_card_draw":
        return DRAW_WEALTH_SCALE.get(stage, 1.00)
    if adapter.key == "seven_card_stud":
        return STUD_WEALTH_SCALE.get(stage, 0.55)
    return 1.0


def rng_for(adapter, name):
    return random.Random(f"npc-inputs-{name}-{adapter.key}")


class Decisions:
    """Patch an engine's decide_poker_action: record every context, answer with `action`."""

    def __init__(self, adapter, action="check"):
        self.contexts = []
        self.action = action
        self._patch = mock.patch(DECISION_FUNCTION[adapter.key], self.decide)

    def decide(self, personality, context, rng=None):
        self.contexts.append(dict(context))
        return {"action": self.action, "profile": get_poker_personality_profile("balanced"),
                "bluff": False}

    def __enter__(self):
        self._patch.start()
        return self

    def __exit__(self, *exc):
        self._patch.stop()
        return False


def npc_of(adapter, game, seat):
    return game.npc if adapter.key == "five_o_poker" else game.npcs[seat - 1]


def name_of(adapter, game, seat):
    if adapter.key == "blind_mans_bluff":
        return game.get_name(seat)
    if adapter.key == "five_o_poker":
        return "You" if seat == 0 else game.get_npc_name()
    return game.get_table_player_name(seat)


def stacks_with(adapter, seat, stack):
    stacks = [FORCED_STACK] * adapter.seat_count
    stacks[seat] = stack
    return stacks


def open_round(adapter, game, stacks=None):
    """A betting round with nothing bet yet: the human may open, NPC seat 1 acts next.

    Five-O: the human opens odd-numbered hands, so the hand number is moved on when needed;
    the stacks are set once every card is placed (placement does not bet)."""
    if adapter.key == "five_o_poker":
        if game.hand_number % 2:
            game.hand_number += 1
        adapter.start_hand(game)
        adapter.place_all_cards(game)
        if stacks is not None:
            adapter.set_stacks(game, stacks)
        assert game.bet_state == "player_open", game.bet_state
        return game
    adapter.force_open_round(game, stacks or [FORCED_STACK] * adapter.seat_count)
    return game


def human_bets(adapter, game, reply="call"):
    """The human opens the betting; returns the context of NPC seat 1's answer."""
    with Decisions(adapter, reply) as decisions:
        if adapter.key == "five_o_poker":
            assert game.player_bet()
            game.pending_npc_at -= 1000.0   # the NPC's thinking pause is over
            game.update()
        elif adapter.key == "blind_mans_bluff":
            adapter.give_turn(game, 0)
            assert game.player_bet(game._base_minimum())
        else:
            adapter.give_turn(game, 0)
            assert adapter.try_wager(game, 0, game.get_minimum_open_bet())
            adapter.give_turn(game, 1)
            game.run_next_npc_action()
    return decisions.contexts[0]


def npc_decides_unbet(adapter, game, reply="check"):
    """NPC seat 1 acts with nothing bet this round; returns its context."""
    with Decisions(adapter, reply) as decisions:
        if adapter.key == "five_o_poker":
            assert game.player_check()
            game.pending_npc_at -= 1000.0
            game.update()
        elif adapter.key == "blind_mans_bluff":
            game._npc_take_turn(1)
        else:
            adapter.give_turn(game, 1)
            game.run_next_npc_action()
    return decisions.contexts[0]


def human_checks(adapter, game):
    """The human checks with nothing bet; returns the context of NPC seat 1's turn after it."""
    if adapter.key == "five_o_poker":
        return npc_decides_unbet(adapter, game)
    adapter.give_turn(game, 0)
    with Decisions(adapter, "check") as decisions:
        assert game.player_check()
        if adapter.key != "blind_mans_bluff":   # BMB runs the NPC turns itself
            adapter.give_turn(game, 1)
            game.run_next_npc_action()
    return decisions.contexts[0]


def npc_decides_after_npc_bet(adapter, game, bettor=2):
    """NPC `bettor` opens the betting, then NPC seat 1 acts; returns seat 1's context."""
    if adapter.key == "blind_mans_bluff":
        assert game._act(bettor, "bet", game._base_minimum())
        with Decisions(adapter, "call") as decisions:
            game._npc_take_turn(1)
        return decisions.contexts[0]
    adapter.give_turn(game, bettor)
    assert adapter.try_wager(game, bettor, game.get_minimum_open_bet())
    adapter.give_turn(game, 1)
    with Decisions(adapter, "call") as decisions:
        game.run_next_npc_action()
    return decisions.contexts[0]


def game_with_store(adapter, rng, store):
    """A started session whose engine has a rival-learning store bound before start_session."""
    random.seed(rng.getrandbits(64))
    game = adapter._create(rng)
    game.learning_store = store
    adapter._start_session(game, adapter.seat_count)
    return game


def read_of(context, seat):
    return next(read for read in context["opponent_reads"] if read["seat"] == seat)


def two_seat_contributions(adapter, amount):
    contributions = [0] * adapter.seat_count
    contributions[0] = contributions[1] = amount
    live = [seat < 2 for seat in range(adapter.seat_count)]
    return contributions, live


# ==================================================
# THE SHARED MODULE
# ==================================================

class WealthTests(unittest.TestCase):
    def test_wealth_pressure_starts_above_115_percent_and_is_full_at_25x(self):
        wealth_pressure = npc_inputs().wealth_pressure
        self.assertEqual(wealth_pressure(1000, 1000), 0.0)
        self.assertEqual(wealth_pressure(1150, 1000), 0.0)
        self.assertEqual(wealth_pressure(0, 1000), 0.0)
        self.assertEqual(wealth_pressure(-50, 1000), 0.0)
        self.assertAlmostEqual(wealth_pressure(1151, 1000), (1.151 - 1.15) / 1.35)
        self.assertAlmostEqual(wealth_pressure(1825, 1000), 0.5)
        self.assertAlmostEqual(wealth_pressure(2500, 1000), 1.0)
        self.assertEqual(wealth_pressure(9000, 1000), 1.0)
        # A buy-in of 0 counts as 1, as in the engines.
        self.assertEqual(wealth_pressure(5, 0), 1.0)
        self.assertEqual(wealth_pressure(1, 0), 0.0)

    def test_soft_bet_cap(self):
        soft_bet_cap = npc_inputs().soft_bet_cap
        self.assertEqual(soft_bet_cap(1000, 0.12, 0.0, 0.70, 20, 5000), 120)
        self.assertEqual(soft_bet_cap(1000, 0.12, 1.0, 0.70, 20, 5000), int(1000 * (0.12 * 1.70)))
        self.assertEqual(soft_bet_cap(1000, 0.40, 0.5, 0.65, 20, 5000), int(1000 * (0.40 * (1 + 0.5 * 0.65))))
        self.assertEqual(soft_bet_cap(1000, 0.01, 0.0, 0.70, 50, 5000), 50)     # at least the minimum bet
        self.assertEqual(soft_bet_cap(1000, 1.00, 1.0, 0.50, 20, 900), 900)     # never past the stack
        self.assertEqual(soft_bet_cap(0, 1.00, 0.0, 0.50, 0, 10), 1)            # a buy-in of 0 counts as 1

    def test_final_round_cap_is_holdems_river_entry(self):
        module = npc_inputs()
        self.assertEqual(module.FINAL_ROUND_CAP, (1.00, 0.50))
        adapter = ADAPTERS_BY_KEY["texas_holdem"]
        for stack in (300, 1000, 1600, 2500, 6000):
            game = adapter.force_open_round(adapter.new_game(random.Random(stack)),
                                            stacks_with(adapter, 1, stack))
            game.current_stage = "river"
            fraction, boost = module.FINAL_ROUND_CAP
            expected = module.soft_bet_cap(game.starting_stack, fraction, game.get_npc_wealth_pressure(0),
                                           boost, game.get_minimum_open_bet(), stack)
            self.assertEqual(game.get_npc_stage_bet_cap(0), expected)


class TableRowTests(unittest.TestCase):
    def test_table_identities(self):
        identities = npc_inputs().table_identities([{"id": "ada", "name": "Ada"}, {"name": "Bo"}, {}])
        self.assertEqual(identities, {0: "player", 1: "ada", 2: "Bo", 3: "seat_3"})
        self.assertEqual(npc_inputs().table_identities([]), {0: "player"})

    def test_opponent_rows_are_the_other_seats_in_the_hand(self):
        rows = npc_inputs().opponent_rows(
            2, [0, 2, 3], ["You", "Ada", "Bo", "Cy"], {0: "player", 1: "ada", 2: "bo", 3: "cy"},
            [100, 200, 300, 400], [5, 0, 10, 20])
        self.assertEqual(rows, [
            {"seat": 0, "id": "player", "name": "You", "stack": 100, "round_bet": 5},
            {"seat": 3, "id": "cy", "name": "Cy", "stack": 400, "round_bet": 20},
        ])
        self.assertEqual(npc_inputs().opponent_rows(1, [1], ["You", "Ada"], {0: "player", 1: "ada"},
                                                    [1, 2], [0, 0]), [])


class DecisionInputsTests(unittest.TestCase):
    NPC = {"id": "ada", "name": "Ada", "skill_tier": "strong", "career_ratings": {"five_o_poker": 1500},
           "personality_traits": {"bitterness": 10}}

    def inputs(self, **changes):
        reads = PokerTableReads()
        reads.observe("bet", 0, hand_number=4, stage="river", amount=50, pot=150)
        memory = PokerGrudgeMemory()
        memory.record_loss("ada", "player", 4, 10, 1.0)
        model = PokerOpponentModel()
        model.record_action("bet", stage="river", amount_to_call=0, pot_before=100, amount=50)
        opponents = [{"seat": 0, "id": "player", "name": "You", "stack": 700, "round_bet": 50}]
        arguments = dict(npc=self.NPC, seat=1, rating_game_key="five_o_poker", stack=2500,
                         starting_stack=1000, hand_number=4, opponents=opponents, last_raiser=0,
                         grudge_memory=memory, table_reads=reads, player_model=model)
        arguments.update(changes)
        return npc_inputs().npc_decision_inputs(**arguments), reads, memory, model, opponents

    def test_every_input(self):
        inputs, reads, memory, model, opponents = self.inputs()
        self.assertEqual(inputs["personality_traits"], get_npc_traits(self.NPC))
        self.assertAlmostEqual(inputs["skill_factor"], 0.35 + 700 * 0.0003)
        self.assertEqual(inputs["npc_identity"], "ada")
        self.assertEqual(inputs["hand_number"], 4)
        self.assertEqual(inputs["starting_stack"], 1000)
        self.assertEqual(inputs["wealth_ratio"], 2.5)
        self.assertAlmostEqual(inputs["wealth_pressure"], 1.0)
        self.assertEqual(inputs["wealth_variant_scale"], 1.0)
        self.assertEqual(inputs["opponent_reads"], [reads.snapshot(0, observer="ada")])
        self.assertEqual(inputs["opponent_reads"][0]["decisions"], 1)
        self.assertEqual(inputs["public_opponents"], [{"seat": 0, "stack": 700, "round_bet": 50}])
        self.assertEqual(inputs["player_tendencies"], model.snapshot())
        self.assertIs(inputs["player_active"], True)
        context = memory.context(self.NPC, 1, opponents, 0, 4)
        self.assertGreater(context["grudge_pressure"], 0)
        for key, value in context.items():
            self.assertEqual(inputs[key], value, key)
        self.assertEqual(set(inputs), set(SHARED_KEYS) - {"minimum_open_bet"})

    def test_scale_clamp_and_defaults(self):
        inputs = self.inputs(wealth_scale=0.5, stack=1825)[0]
        self.assertAlmostEqual(inputs["wealth_pressure"], 0.25)
        self.assertEqual(inputs["wealth_variant_scale"], 0.5)
        self.assertEqual(self.inputs(wealth_scale=3.0)[0]["wealth_pressure"], 1.0)
        inputs = self.inputs(player_model=None, player_active=False, last_raiser=None)[0]
        self.assertEqual(inputs["player_tendencies"], {})
        self.assertIs(inputs["player_active"], False)
        self.assertEqual(inputs["grudge_pressure"], 0.0)
        self.assertEqual(inputs["grudge_target"], "You")
        # Skill falls back to the tier when the NPC has no rating for this game.
        self.assertEqual(self.inputs(rating_game_key="blind_mans_bluff")[0]["skill_factor"],
                         POKER_SKILL_FACTORS["strong"])


class SessionMemoryTests(unittest.TestCase):
    def stub(self, store=None):
        game = SimpleNamespace(
            npcs=[{"id": "ada"}, {"id": "bo"}], learning_store=store, hand_number=3, pot=90,
            personality_memory=PokerGrudgeMemory(), player_model=PokerOpponentModel(),
            table_reads=PokerTableReads(), quick_chat_state={"effects": [{"hand": 3}]},
            _quick_chat_event_counter=9, _quick_chat_event_signature=("old",),
            seat_stacks=lambda: [100, 100, 100], seat_at_table=lambda: [True, True, True])
        game.personality_memory.record_loss("ada", "player", 3, 10, 1.0)
        game.player_model.record_action("bet", stage="flop", amount=10)
        game.table_reads.observe("bet", 0, hand_number=3, stage="flop", amount=10, pot=30)
        return game

    def test_reset_session_memory(self):
        store = new_learning()
        game = self.stub(store)
        npc_inputs().reset_session_memory(game, "five_o_poker")
        self.assertEqual(game.personality_memory.entries, {})
        self.assertEqual(game.personality_memory.recorded, set())
        self.assertEqual(game.quick_chat_state, {"last_event": -999, "last_manipulative_event": -999,
                                                 "uses_by_hand": {}, "effects": []})
        self.assertEqual(game._quick_chat_event_counter, 0)
        self.assertIsNone(game._quick_chat_event_signature)
        self.assertEqual(game.player_model.snapshot(), PokerOpponentModel().snapshot())
        self.assertEqual(game.table_reads.histories, {})
        self.assertEqual(game.table_reads.learning.identities, {0: "player", 1: "ada", 2: "bo"})
        self.assertEqual(set(store["games"]["five_o_poker"]), {"ada", "bo"})

    def test_observe_public_action_uses_the_table_and_live_observers(self):
        store = new_learning()
        game = self.stub(store)
        npc_inputs().reset_session_memory(game, "blind_mans_bluff")
        game.seat_at_table = lambda: [True, False, True]   # Ada was knocked out: she stops observing
        npc_inputs().observe_public_action(game, "bet", 0, stage="forehead_bet", amount=30,
                                           round_total=30, facing_amount=0)
        self.assertEqual(game.table_reads.histories[0][-1], ("bet", "forehead_bet", False, 30 / 60))
        self.assertEqual(game.table_reads.hand_number, 3)
        self.assertEqual(game.table_reads.learning.active_observers, {"bo"})
        bank = store["games"]["blind_mans_bluff"]
        self.assertEqual(bank["ada"], {})
        self.assertEqual(len(bank["bo"]["player"]["history"]), 1)
        # Chips do not decide it: an NPC all-in with 0 chips is still at the table.
        game.seat_stacks = lambda: [100, 0, 50]
        game.seat_at_table = lambda: [True, True, False]
        npc_inputs().observe_public_action(game, "check", 0, stage="forehead_bet")
        self.assertEqual(game.table_reads.learning.active_observers, {"ada"})

    def test_weak_reveal_is_passed_on(self):
        game = self.stub()
        npc_inputs().reset_session_memory(game, "five_o_poker")
        npc_inputs().observe_public_action(game, "bet", 0, stage="showdown_bet", amount=10)
        npc_inputs().observe_public_action(game, "showdown_hand", 0, stage="showdown_bet", weak=True)
        self.assertEqual(list(game.table_reads.reveals[0]), [True])


class SharedModuleAdditionTests(unittest.TestCase):
    """Names added to the modules multiplayer re-exports; nothing existing changed."""

    def test_record_showdown(self):
        seats = {0: {"id": "player", "bitterness": None, "contribution": 400},
                 1: {"id": "ada", "bitterness": 10, "contribution": 300},
                 2: {"id": "bo", "bitterness": 4, "contribution": 3000},
                 3: {"id": "cy", "bitterness": 8, "contribution": 50}}
        awards = [{"eligible": [0, 1, 2], "winners": [0]},
                  {"eligible": [1, 2], "winners": [1]},
                  {"eligible": [3], "winners": [3]}]          # a fold win: nothing contested
        memory = PokerGrudgeMemory()
        memory.record_showdown(awards, seats, 7, 1000)
        expected = PokerGrudgeMemory()
        expected.record_loss("ada", "player", 7, 10, 0.3)
        expected.record_loss("bo", "player", 7, 4, 1.0)       # severity is capped at 1
        expected.record_loss("bo", "ada", 7, 4, 1.0)
        self.assertEqual(memory.entries, expected.entries)
        self.assertNotIn(("player", "ada"), memory.entries)    # the human never resents
        self.assertNotIn(("cy", "player"), memory.entries)

    def test_record_showdown_split_and_empty(self):
        seats = {0: {"id": "player", "bitterness": None, "contribution": 100},
                 1: {"id": "ada", "bitterness": 10, "contribution": 100}}
        memory = PokerGrudgeMemory()
        memory.record_showdown([{"eligible": [0, 1], "winners": [0, 1]}], seats, 1, 1000)
        memory.record_showdown([], seats, 2, 1000)
        self.assertEqual(memory.entries, {})
        # Two winners: the loser resents both.
        seats[2] = {"id": "bo", "bitterness": 10, "contribution": 500}
        memory.record_showdown([{"eligible": [0, 1, 2], "winners": [0, 1]}], seats, 3, 1000)
        self.assertEqual(set(memory.entries), {("bo", "player"), ("bo", "ada")})

    def test_late_streets_include_the_single_rounds(self):
        from solitaireplus.games.poker.strategy import LATE_STREETS
        self.assertLessEqual({"turn", "river", "post_draw", "fifth", "sixth", "seventh"}, LATE_STREETS)
        self.assertLessEqual({"showdown_bet", "forehead_bet"}, LATE_STREETS)

    def test_observe_weak_overrides_the_hand_name(self):
        for weak, hand_name, expected in ((True, "Flush", True), (False, "High Card", False),
                                          (None, "High Card", True), (None, "Flush", False),
                                          (1, None, True), (0, None, False)):
            reads = PokerTableReads()
            reads.observe("bet", 0, hand_number=1, stage="river", amount=10, pot=30)
            reads.observe("showdown_hand", 0, hand_number=1, stage="river", hand_name=hand_name, weak=weak)
            self.assertEqual(list(reads.reveals[0]), [expected], (weak, hand_name))
        # No late aggression, no reveal sample.
        reads = PokerTableReads()
        reads.observe("call", 0, hand_number=1, stage="river", amount=10, pot=30)
        reads.observe("showdown_hand", 0, hand_number=1, stage="river", weak=True)
        self.assertEqual(reads.reveals, {})

    def test_learning_games(self):
        from solitaireplus.games.poker.learning import GAMES
        self.assertEqual(GAMES, ("texas_holdem", "five_card_draw", "seven_card_stud",
                                 "five_o_poker", "blind_mans_bluff"))


# ==================================================
# EVERY VARIANT
# ==================================================

class ContextKeyTests(unittest.TestCase):
    def test_every_variant_context_has_the_shared_and_quick_chat_inputs(self):
        for adapter in ADAPTERS:
            with self.subTest(adapter.key):
                game = open_round(adapter, adapter.new_game(rng_for(adapter, "keys")))
                facing = human_bets(adapter, game, reply="fold")
                facing_hand = game.hand_number
                open_round(adapter, game)
                unbet = npc_decides_unbet(adapter, game)
                for context, hand in ((facing, facing_hand), (unbet, game.hand_number)):
                    missing = [key for key in SHARED_KEYS + QUICK_CHAT_KEYS if key not in context]
                    self.assertEqual(missing, [])
                    self.assertEqual(context["npc_identity"], npc_identity(npc_of(adapter, game, 1), 1))
                    self.assertEqual(context["hand_number"], hand)
                    self.assertEqual(context["starting_stack"], game.starting_stack)
                    self.assertEqual(context["personality_traits"], get_npc_traits(npc_of(adapter, game, 1)))
                    self.assertIs(context["player_active"], True)
                    self.assertEqual([read["seat"] for read in context["opponent_reads"]],
                                     [row["seat"] for row in context["public_opponents"]])
                    self.assertIn(0, [row["seat"] for row in context["public_opponents"]])


class CashOnHandTests(unittest.TestCase):
    def context_for_stack(self, adapter, multiple, stage=None):
        game = adapter.new_game(rng_for(adapter, f"cash-{multiple}-{stage}"))
        stack = int(game.starting_stack * multiple)
        open_round(adapter, game, stacks_with(adapter, 1, stack))
        if stage is not None:
            game.current_stage = stage
        return game, stack, npc_decides_unbet(adapter, game)

    def test_wealth_pressure_ratio_and_short_stack_input(self):
        for adapter in ADAPTERS:
            stages = {"five_card_draw": (None, "post_draw"),
                      "seven_card_stud": (None, "third", "seventh")}.get(adapter.key, (None,))
            for stage in stages:
                with self.subTest(adapter.key, stage=stage):
                    game, stack, rich = self.context_for_stack(adapter, 2.5, stage)
                    scale = expected_wealth_scale(adapter, game)
                    self.assertEqual(rich["wealth_ratio"], stack / game.starting_stack)
                    self.assertEqual(rich["wealth_ratio"], 2.5)
                    self.assertAlmostEqual(rich["wealth_pressure"], 1.0 * scale)
                    self.assertEqual(rich["wealth_variant_scale"], scale)
                    game, fresh_stack, fresh = self.context_for_stack(adapter, 1.0, stage)
                    self.assertEqual(fresh["wealth_ratio"], 1.0)
                    self.assertEqual(fresh["wealth_pressure"], 0.0)
                    # The short-stack tenacity rule compares the stack with 6x this.
                    self.assertGreater(fresh["minimum_open_bet"], 0)
                    self.assertEqual(fresh["stack"], fresh_stack)
                    game, stack, middle = self.context_for_stack(adapter, 1.6, stage)
                    self.assertEqual(middle["wealth_ratio"], stack / game.starting_stack)
                    self.assertAlmostEqual(middle["wealth_pressure"],
                                           min(1.0, (stack / game.starting_stack - 1.15) / 1.35) * scale)

    def test_bmb_soft_cap_for_rich_npcs(self):
        module = npc_inputs()
        for multiple in (2.5, 5.0, 1.3):
            with self.subTest(multiple=multiple):
                game = BMB.new_game(rng_for(BMB, f"cap-{multiple}"))
                stack = int(game.starting_stack * multiple)
                BMB.force_open_round(game, stacks_with(BMB, 1, stack))
                context = npc_decides_unbet(BMB, game)
                round_bet = game.round_bets[1]
                fraction, boost = module.FINAL_ROUND_CAP
                cap = module.soft_bet_cap(game.starting_stack, fraction, context["wealth_pressure"], boost,
                                          game._base_minimum(), stack + round_bet)
                self.assertLess(cap, stack)
                self.assertEqual(context["maximum_open_bet"], min(stack, cap))
                self.assertLessEqual(context["maximum_open_bet"], cap)
                self.assertEqual(context["soft_maximum_raise_to"], min(stack + round_bet, cap))
                self.assertEqual(context["maximum_raise_to"], stack + round_bet)
                # The NPC's real opening bet stays within the cap.
                BMB.force_open_round(game, stacks_with(BMB, 1, stack))
                with Decisions(BMB, "bet"):
                    game._npc_take_turn(1)
                self.assertGreater(game.round_bets[1], 0)
                self.assertLessEqual(game.round_bets[1], cap)

    def test_bmb_npc_at_its_buy_in_may_still_bet_its_stack(self):
        game = BMB.new_game(rng_for(BMB, "cap-fresh"))
        for stack in (game.starting_stack, 400, 30):
            BMB.force_open_round(game, stacks_with(BMB, 1, stack))
            context = npc_decides_unbet(BMB, game)
            self.assertEqual(context["maximum_open_bet"], stack)
            self.assertEqual(context["soft_maximum_raise_to"], stack)


class SkillTests(unittest.TestCase):
    def test_rating_for_this_game_sets_the_skill(self):
        for adapter in ADAPTERS:
            with self.subTest(adapter.key):
                game = adapter.new_game(rng_for(adapter, "skill"))
                ratings = {key: 900 for key in ADAPTERS_BY_KEY if key != "blind_mans_bluff"}
                if adapter.key != "blind_mans_bluff":
                    ratings[adapter.key] = 1500
                for seat in range(1, adapter.seat_count):
                    npc_of(adapter, game, seat)["career_ratings"] = dict(ratings)
                open_round(adapter, game)
                context = npc_decides_unbet(adapter, game)
                if adapter.key == "blind_mans_bluff":
                    # No Blind Man's Bluff rating exists: the skill tier decides.
                    self.assertEqual(context["skill_factor"], POKER_SKILL_FACTORS["mid"])
                else:
                    self.assertAlmostEqual(context["skill_factor"], 0.35 + 700 * 0.0003)
                    self.assertAlmostEqual(context["skill_factor"], 0.56)

    @staticmethod
    def skill_sites():
        """Every poker module that imported get_poker_skill_factor (each call site's own name)."""
        return sorted(name for name, module in list(sys.modules.items())
                      if name.startswith("solitaireplus.games.poker.") and name != ai_module.__name__
                      and getattr(module, "get_poker_skill_factor", None) is ai_module.get_poker_skill_factor)

    def spy_on_skill(self, patches, spy):
        sites = self.skill_sites()
        self.assertIn("solitaireplus.games.poker.holdem", sites)
        for site in sites:
            patches.enter_context(mock.patch(f"{site}.get_poker_skill_factor", spy))

    def test_every_skill_lookup_in_a_hand_uses_the_variants_rating(self):
        """Betting and non-betting choices (Draw's discards, Five-O's columns) share one skill."""
        for adapter in ADAPTERS:
            with self.subTest(adapter.key):
                keys = []

                def spy(npc, game_key=None):
                    keys.append(game_key)
                    return get_poker_skill_factor(npc, game_key)

                with contextlib.ExitStack() as patches:
                    self.spy_on_skill(patches, spy)
                    rng = rng_for(adapter, "skill-keys")
                    game = adapter.new_game(rng)
                    for _ in range(4):
                        if adapter.session_over(game) or not adapter.start_hand(game):
                            break
                        adapter.play_hand(game, rng)
                self.assertTrue(keys)
                self.assertEqual(set(keys), {adapter.key})

    def test_draw_discards_use_the_draw_rating(self):
        """Review finding: Draw's discard choice used the skill tier while its betting used the
        five_card_draw rating, so one NPC played at two skill levels."""
        adapter = ADAPTERS_BY_KEY["five_card_draw"]
        game = adapter.new_game(rng_for(adapter, "discards"))
        for npc in game.npcs:
            npc["skill_tier"] = "mid"
            npc["career_ratings"] = {"five_card_draw": 1900}
        adapter.start_hand(game)
        used = []

        def spy(npc, game_key=None):
            used.append(get_poker_skill_factor(npc, game_key))
            return used[-1]

        with contextlib.ExitStack() as patches:
            self.spy_on_skill(patches, spy)
            game.choose_npc_discard_indexes(0)
            betting = game.build_npc_ai_context(0)["skill_factor"]
        self.assertAlmostEqual(betting, 0.35 + 1100 * 0.0003)
        self.assertTrue(used)
        self.assertTrue(all(abs(skill - betting) < 1e-9 for skill in used), used)

    def test_five_o_column_choice_uses_the_five_o_rating(self):
        game = FIVE_O.new_game(rng_for(FIVE_O, "columns"))
        keys = []

        def spy(npc, game_key=None):
            keys.append(game_key)
            return get_poker_skill_factor(npc, game_key)

        with mock.patch("solitaireplus.games.poker.five_o.get_poker_skill_factor", spy):
            FIVE_O.start_hand(game)
            FIVE_O.place_all_cards(game)
        self.assertTrue(keys)
        self.assertEqual(set(keys), {"five_o_poker"})


class GrudgeTests(unittest.TestCase):
    def test_showdown_loss_grudge_severity_is_contribution_over_buy_in(self):
        for adapter in ADAPTERS:
            with self.subTest(adapter.key):
                game = adapter.new_game(rng_for(adapter, "grudge"))
                contributions, live = two_seat_contributions(adapter, 60)
                ranks = [14, 5] + [2] * (adapter.seat_count - 2)
                adapter.force_showdown(game, contributions, live, ranks, dealer_seat=0)
                npc = npc_of(adapter, game, 1)
                observer, bitterness = npc_identity(npc, 1), get_npc_traits(npc)["bitterness"]
                expected = PokerGrudgeMemory()
                expected.record_loss(observer, "player", game.hand_number, bitterness,
                                     60 / game.starting_stack)
                actual = game.personality_memory.intensity(observer, "player", game.hand_number, bitterness)
                self.assertGreater(actual, 0)
                self.assertEqual(actual, expected.intensity(observer, "player", game.hand_number, bitterness))
                self.assertEqual(set(game.personality_memory.entries), {(observer, "player")})

    def test_npc_beaten_by_npc_resents_that_npc(self):
        for adapter in ADAPTERS:
            if adapter.seat_count < 3:
                continue
            with self.subTest(adapter.key):
                game = adapter.new_game(rng_for(adapter, "npc-grudge"))
                contributions = [0, 80, 80] + [0] * (adapter.seat_count - 3)
                live = [False, True, True] + [False] * (adapter.seat_count - 3)
                ranks = [2, 4, 13] + [2] * (adapter.seat_count - 3)
                adapter.force_showdown(game, contributions, live, ranks, dealer_seat=0)
                loser, winner = npc_of(adapter, game, 1), npc_of(adapter, game, 2)
                bitterness = get_npc_traits(loser)["bitterness"]
                expected = PokerGrudgeMemory()
                expected.record_loss(npc_identity(loser, 1), npc_identity(winner, 2), game.hand_number,
                                     bitterness, 80 / game.starting_stack)
                self.assertEqual(game.personality_memory.entries, expected.entries)

    def test_fold_wins_and_splits_record_nothing(self):
        for adapter in ADAPTERS:
            with self.subTest(adapter.key):
                game = adapter.new_game(rng_for(adapter, "no-grudge"))
                contributions, live = two_seat_contributions(adapter, 60)
                for winner in (0, 1):
                    adapter.force_fold_win(game, contributions, winner)
                    self.assertEqual(game.personality_memory.entries, {})
                ranks = [9] * adapter.seat_count
                adapter.force_showdown(game, contributions, live, ranks, dealer_seat=0)
                self.assertEqual(len(adapter.awards(game)[0]["winners"]), 2)
                self.assertEqual(game.personality_memory.entries, {})

    def resent_player(self, adapter, game, seat=1, target=0):
        npc = npc_of(adapter, game, seat)
        target_id = "player" if target == 0 else npc_identity(npc_of(adapter, game, target), target)
        game.personality_memory.record_loss(npc_identity(npc, seat), target_id, game.hand_number, 10, 1.0)
        return game.personality_memory.intensity(npc_identity(npc, seat), target_id, game.hand_number,
                                                 get_npc_traits(npc)["bitterness"])

    def test_grudge_pressure_only_against_the_last_raiser(self):
        for adapter in ADAPTERS:
            with self.subTest(adapter.key, raiser="human"):
                game = open_round(adapter, adapter.new_game(rng_for(adapter, "pressure")))
                intensity = self.resent_player(adapter, game)
                self.assertGreater(intensity, 0)
                context = human_bets(adapter, game, reply="fold")
                self.assertEqual(context["last_raiser"], 0)
                self.assertEqual(context["grudge_pressure"], intensity)
                self.assertEqual(context["grudge_target"], "You")
                self.assertEqual(context["grudge_intensity"], intensity)
                human = next(row for row in context["public_opponents"] if row["seat"] == 0)
                self.assertGreater(human["round_bet"], 0)
                self.assertEqual(context["grudge_target_round_total"], human["stack"] + human["round_bet"])
            with self.subTest(adapter.key, raiser=None):
                game = open_round(adapter, game)
                intensity = self.resent_player(adapter, game)
                context = npc_decides_unbet(adapter, game)
                self.assertIsNone(context["last_raiser"])
                self.assertEqual(context["grudge_pressure"], 0.0)
                self.assertEqual(context["grudge_target"], "You")
                self.assertEqual(context["grudge_intensity"], intensity)
            if adapter.seat_count < 3:
                continue
            with self.subTest(adapter.key, raiser="another NPC"):
                game = open_round(adapter, game)
                self.resent_player(adapter, game)
                context = npc_decides_after_npc_bet(adapter, game, bettor=2)
                self.assertEqual(context["last_raiser"], 2)
                self.assertEqual(context["grudge_pressure"], 0.0)
                self.assertEqual(context["grudge_target"], "You")
            with self.subTest(adapter.key, raiser="the resented NPC"):
                game = open_round(adapter, game)
                intensity = self.resent_player(adapter, game, target=2)
                context = npc_decides_after_npc_bet(adapter, game, bettor=2)
                self.assertEqual(context["grudge_pressure"], intensity)
                self.assertEqual(context["grudge_target"], name_of(adapter, game, 2))

    def test_start_session_forgets_grudges(self):
        for adapter in ADAPTERS:
            with self.subTest(adapter.key):
                game = open_round(adapter, adapter.new_game(rng_for(adapter, "forget")))
                self.assertGreater(self.resent_player(adapter, game), 0)
                adapter._start_session(game, adapter.seat_count)
                self.assertEqual(game.personality_memory.entries, {})


class ReadsAndTendencyTests(unittest.TestCase):
    BETS = 3

    def test_npc_reads_every_human_bet(self):
        for adapter in ADAPTERS:
            with self.subTest(adapter.key):
                game = adapter.new_game(rng_for(adapter, "reads"))
                for count in range(1, self.BETS + 1):
                    open_round(adapter, game)
                    context = human_bets(adapter, game, reply="fold")
                    read = read_of(context, 0)
                    self.assertEqual(read["decisions"], count)
                    self.assertEqual(read["hand_actions"][-1][0], "bet")
                    self.assertEqual(context["player_tendencies"]["total_decisions"], count)
                    self.assertEqual(context["player_tendencies"], game.player_model.snapshot())

    def test_human_checks_are_read_too(self):
        for adapter in ADAPTERS:
            with self.subTest(adapter.key):
                game = open_round(adapter, adapter.new_game(rng_for(adapter, "check")))
                stage = {"five_o_poker": "showdown_bet", "blind_mans_bluff": "forehead_bet"}.get(
                    adapter.key, getattr(game, "current_stage", None))
                context = human_checks(adapter, game)
                read = read_of(context, 0)
                self.assertEqual(read["decisions"], 1)
                self.assertEqual(read["hand_actions"], [("check", stage, False, 0.0)])
                self.assertEqual(game.player_model.total_decisions, 1)
                self.assertEqual(game.player_model.passive_actions, 1)

    def test_start_hand_counts_a_hand_seen(self):
        for adapter in ADAPTERS:
            with self.subTest(adapter.key):
                game = adapter.new_game(rng_for(adapter, "hands-seen"))
                before = game.player_model.hands_seen
                with Decisions(adapter, "check"):
                    self.assertTrue(adapter.start_hand(game))
                self.assertEqual(game.player_model.hands_seen, before + 1)

    def test_late_aggression_reveals_feed_the_reads(self):
        """Five-O and BMB: a seat that bet and is shown down records whether it held a winner."""
        for adapter in (FIVE_O, BMB):
            with self.subTest(adapter.key):
                game = open_round(adapter, adapter.new_game(rng_for(adapter, "reveal")))
                human_bets(adapter, game, reply="call")
                awards = adapter.awards(game)
                won = any(award["payouts"].get(0, 0) > 0 for award in awards)
                self.assertEqual(list(game.table_reads.reveals[0]), [not won])
                # NPCs that only called have no late aggression to explain.
                self.assertNotIn(1, game.table_reads.reveals)


class LearningTests(unittest.TestCase):
    BETS = 3

    def play_bets(self, adapter, game):
        for _ in range(self.BETS):
            open_round(adapter, game)
            human_bets(adapter, game, reply="fold")

    def test_observations_land_under_the_variants_rating_game(self):
        for adapter in ADAPTERS:
            with self.subTest(adapter.key):
                store = new_learning()
                game = game_with_store(adapter, rng_for(adapter, "store"), store)
                self.assertEqual(game.rating_game_key, adapter.key)
                self.play_bets(adapter, game)
                self.assertEqual(set(store["games"]), {adapter.key})
                identities = [npc_identity(npc_of(adapter, game, seat), seat)
                              for seat in range(1, adapter.seat_count)]
                self.assertEqual(set(store["games"][adapter.key]), set(identities))
                history = store["games"][adapter.key][identities[0]]["player"]["history"]
                self.assertEqual([item[0] for item in history], ["bet"] * self.BETS)

                # A saved profile restores the reads in a later session.
                restored = normalize_learning(json.loads(json.dumps(store)))
                self.assertEqual(restored["games"][adapter.key],
                                 json.loads(json.dumps(store))["games"][adapter.key])
                later = game_with_store(adapter, rng_for(adapter, "store-later"), restored)
                context = npc_decides_unbet(adapter, open_round(adapter, later))
                # Five-O: the human checked first in this session, which is read as well.
                checked = adapter.key == "five_o_poker"
                self.assertEqual(read_of(context, 0)["decisions"], self.BETS + checked)
                self.assertEqual(read_of(context, 0)["hand_actions"],
                                 [("check", "showdown_bet", False, 0.0)] if checked else [])

                # Free play (no store) leaves the career store alone.
                before = copy.deepcopy(store)
                game.learning_store = None
                adapter._start_session(game, adapter.seat_count)
                self.play_bets(adapter, game)
                self.assertEqual(store, before)

    def knock_out_or_all_in(self, adapter, game, seat, knocked_out):
        """Seat `seat` (an NPC) is all-in with 0 chips in this hand, or was knocked out before it."""
        if adapter.key in HOLDEM_FAMILY:
            # Not set_stacks: it would mark the seat busted, which happens only between hands.
            game.npc_stacks[seat - 1] = 0
            game.npc_all_in[seat - 1] = True
            if knocked_out:
                game.npc_busted[seat - 1] = True
        elif adapter.key == "blind_mans_bluff":
            game.npc_stacks[seat - 1] = 0
            game.pending.discard(seat)
            game.raise_rights.discard(seat)
            if knocked_out:
                game.live_at_start.remove(seat)
                game.folded[seat] = True
        else:
            game.npc_stack = 0

    def human_checks_once(self, adapter, game):
        with Decisions(adapter, "check"):
            if adapter.key != "five_o_poker":
                adapter.give_turn(game, 0)
            self.assertTrue(game.player_check())

    def test_an_all_in_npc_keeps_learning_and_a_knocked_out_npc_does_not(self):
        """Review finding: Five-O and BMB used chips > 0, so an all-in NPC stopped learning there
        but not in the Hold'em family. One rule now: every NPC still at the table reads."""
        for adapter in ADAPTERS:
            cases = (False, True) if adapter.key != "five_o_poker" else (False,)
            for knocked_out in cases:
                with self.subTest(adapter.key, knocked_out=knocked_out):
                    store = new_learning()
                    game = game_with_store(adapter, rng_for(adapter, "all-in-learning"), store)
                    open_round(adapter, game)
                    self.knock_out_or_all_in(adapter, game, 1, knocked_out)
                    self.human_checks_once(adapter, game)
                    bank = store["games"][adapter.key]
                    seen = bank[npc_identity(npc_of(adapter, game, 1), 1)].get("player", {}).get("history", [])
                    self.assertEqual([item[0] for item in seen], [] if knocked_out else ["check"])
                    if adapter.seat_count > 2:
                        other = bank[npc_identity(npc_of(adapter, game, 2), 2)]["player"]["history"]
                        self.assertEqual([item[0] for item in other], ["check"])
        # Five-O is heads-up: an NPC that cannot ante ends the session, so it is never knocked
        # out while hands go on.
        game = FIVE_O.new_game(rng_for(FIVE_O, "knocked-out"))
        game.npc_stack = game.ante - 1
        self.assertFalse(FIVE_O.start_hand(game))
        self.assertTrue(game.session_complete)

    def test_normalize_keeps_the_new_games(self):
        record = {"rival": {"player": {"history": [["bet", "showdown_bet", False, 0.5]], "reveals": [True]}}}
        source = {"games": {key: copy.deepcopy(record)
                            for key in ("five_o_poker", "blind_mans_bluff", "not_a_game")}}
        cleaned = normalize_learning(source)
        self.assertEqual(set(cleaned["games"]), {"five_o_poker", "blind_mans_bluff"})
        for key in ("five_o_poker", "blind_mans_bluff"):
            self.assertEqual(cleaned["games"][key], source["games"][key])


class BettingRoundClassTests(unittest.TestCase):
    """Review finding: the AI counted Blind Man's Bluff's single round as an early street (so the
    pessimism trait applied) and Five-O's as neither, while the table reads count both as late.
    One classification now: strategy.EARLY_STREETS / LATE_STREETS, the single rounds late."""

    # Per variant: (early betting rounds, late betting rounds).
    ROUNDS = {
        "texas_holdem": (("preflop", "flop"), ("turn", "river")),
        "five_card_draw": (("preflop",), ("post_draw",)),
        "seven_card_stud": (("third", "fourth"), ("fifth", "sixth", "seventh")),
        "five_o_poker": ((), ("showdown_bet",)),
        "blind_mans_bluff": ((), ("forehead_bet",)),
    }
    GLOOMY = {"id": "gloomy", "name": "Gloomy", "personality_traits": {
        "caution": 5, "aggressiveness": 5, "unpredictability": 3, "escalation": 5,
        "selectivity": 5, "tenacity": 5, "pessimism": 10, "bitterness": 3}}

    def test_every_betting_round_is_early_or_late(self):
        from solitaireplus.games.poker.blind_mans_bluff import BlindMansBluffGame
        from solitaireplus.games.poker.five_o import FiveOPokerGame
        from solitaireplus.games.poker.strategy import EARLY_STREETS, LATE_STREETS
        self.assertEqual(set(self.ROUNDS), set(ADAPTERS_BY_KEY))
        self.assertEqual(EARLY_STREETS & LATE_STREETS, frozenset())
        self.assertEqual((FiveOPokerGame.BETTING_STAGE, BlindMansBluffGame.BETTING_STAGE),
                         ("showdown_bet", "forehead_bet"))
        for key, (early, late) in self.ROUNDS.items():
            with self.subTest(key):
                self.assertLessEqual(set(early), EARLY_STREETS)
                self.assertLessEqual(set(late), LATE_STREETS)

    def decisions(self, stage, facing, trials=400):
        from solitaireplus.games.poker.ai import decide_poker_action, get_poker_personality
        rng = random.Random("same-decisions")
        context = {
            "game": "blind_mans_bluff", "stage": stage, "position": "unknown", "hand_strength": 0.30,
            "amount_to_call": facing, "stack": 1000, "pot": 100, "current_bet": facing, "can_raise": True,
            "opponents_remaining": 1, "minimum_open_bet": 20, "maximum_open_bet": 1000,
            "minimum_raise_to": 80, "maximum_raise_to": 1000, "starting_stack": 1000,
            "personality_traits": get_npc_traits(self.GLOOMY), "skill_factor": 0.55,
        }
        personality = get_poker_personality(self.GLOOMY)
        return [decide_poker_action(personality, dict(context), rng)["action"] for _ in range(trials)]

    def test_single_round_npcs_decide_alike(self):
        # The same weak, pessimistic NPC in the same spot: only the stage name differs.
        for facing in (0, 40):
            with self.subTest(facing=facing):
                bluff = self.decisions("forehead_bet", facing)
                self.assertEqual(bluff, self.decisions("showdown_bet", facing))
                self.assertEqual(bluff, self.decisions("river", facing))
        # Pessimism still works on an early street: facing a bet it folds more there.
        self.assertGreater(self.decisions("flop", 40).count("fold"),
                           self.decisions("forehead_bet", 40).count("fold"))


class SessionResetTests(unittest.TestCase):
    def test_start_session_clears_reads_model_quick_chat_and_grudges(self):
        for adapter in ADAPTERS:
            with self.subTest(adapter.key):
                store = new_learning()
                game = game_with_store(adapter, rng_for(adapter, "reset"), store)
                open_round(adapter, game)
                human_bets(adapter, game, reply="fold")
                npc = npc_of(adapter, game, 1)
                game.personality_memory.record_loss(npc_identity(npc, 1), "player", game.hand_number, 10, 1)
                game.quick_chat_state = {"last_event": 4, "last_manipulative_event": 4,
                                         "uses_by_hand": {1: {"bored": 1}}, "effects": [{"hand": 1}]}
                game._quick_chat_event_counter = 7
                game._quick_chat_event_signature = ("stale",)
                self.assertTrue(game.table_reads.histories)
                self.assertGreater(game.player_model.total_decisions, 0)

                adapter._start_session(game, adapter.seat_count)
                self.assertEqual(game.table_reads.histories, {})
                self.assertEqual(game.table_reads.reveals, {})
                self.assertEqual(game.table_reads.hand_actions, {})
                self.assertEqual(game.player_model.snapshot(), PokerOpponentModel().snapshot())
                self.assertEqual(game.quick_chat_state, {"last_event": -999, "last_manipulative_event": -999,
                                                         "uses_by_hand": {}, "effects": []})
                self.assertEqual(game._quick_chat_event_counter, 0)
                self.assertIsNone(game._quick_chat_event_signature)
                self.assertEqual(game.personality_memory.entries, {})
                # Learning is bound again, for this session's seats.
                self.assertEqual(game.table_reads.learning.identities,
                                 npc_inputs().table_identities(game.npcs))
                self.assertIn(npc_identity(npc, 1), store["games"][adapter.key])


# ==================================================
# HOLD'EM, DRAW AND STUD: NO CHANGE
# ==================================================

def old_stage_cap(key, game, npc_index):
    """The pre-group-5 get_npc_stage_bet_cap of Hold'em and Draw, verbatim."""
    stack = game.npc_stacks[npc_index]
    if stack <= 0:
        return game.npc_round_bets[npc_index]
    if key == "texas_holdem":
        fraction = {"preflop": 0.12, "flop": 0.22, "turn": 0.40, "river": 1.00}.get(game.current_stage, 0.25)
        boost = {"preflop": 0.70, "flop": 0.85, "turn": 0.65, "river": 0.50}.get(game.current_stage, 0.45)
    else:
        fraction = {"preflop": 0.15, "post_draw": 1.00}.get(game.current_stage, 0.35)
        boost = {"preflop": 0.60, "post_draw": 0.35}.get(game.current_stage, 0.30)
    fraction *= 1.0 + old_wealth_pressure(game, npc_index) * boost
    target = max(int(max(1, game.starting_stack) * fraction), game.get_minimum_open_bet())
    return min(target, game.npc_round_bets[npc_index] + stack)


def old_wealth_pressure(game, npc_index):
    starting_stack = max(1, int(game.starting_stack or 0))
    ratio = max(0, int(game.npc_stacks[npc_index])) / starting_stack
    if ratio <= 1.15:
        return 0.0
    return max(0.0, min(1.0, (ratio - 1.15) / 1.35))


def old_inputs(key, game, npc_index):
    """The values the inline build_npc_ai_context code gave before group 5."""
    seat = npc_index + 1
    npc = game.npcs[npc_index]
    stack = game.npc_stacks[npc_index]
    pressure = old_wealth_pressure(game, npc_index)
    expected = {}
    if key == "five_card_draw":
        scale = 0.80 if game.current_stage == "preflop" else 1.00
    elif key == "seven_card_stud":
        scale = STUD_WEALTH_SCALE.get(game.current_stage, 0.55)
    else:
        scale = None
    if scale is not None:
        pressure = min(1.0, max(0.0, float(pressure)) * scale)
        expected["wealth_variant_scale"] = scale
    others = [other for other in game.get_active_player_indexes() if other != seat]
    identity = npc_identity(npc, seat)

    def stack_of(other):
        return game.player_stack if other == 0 else game.npc_stacks[other - 1]

    def round_bet_of(other):
        return game.player_round_bet if other == 0 else game.npc_round_bets[other - 1]

    opponents = [{"seat": other, "id": npc_identity(game.npcs[other - 1] if other else {}, other),
                  "name": game.get_table_player_name(other), "stack": stack_of(other),
                  "round_bet": round_bet_of(other)} for other in others]
    reads = [game.table_reads.snapshot(other, observer=identity) for other in others]
    if key == "seven_card_stud":
        for read in reads:
            read["exposed_cards"] = [dict(card) for card in game.get_exposed_cards(read["seat"])]
    expected.update({
        "personality_traits": get_npc_traits(npc),
        "skill_factor": get_poker_skill_factor(npc, game.rating_game_key),
        "starting_stack": game.starting_stack,
        "wealth_ratio": stack / max(1, game.starting_stack),
        "wealth_pressure": pressure,
        "hand_number": game.hand_number,
        "npc_identity": identity,
        "opponent_reads": reads,
        "public_opponents": [{"seat": row["seat"], "stack": row["stack"], "round_bet": row["round_bet"]}
                             for row in opponents],
        "player_tendencies": game.player_model.snapshot(),
        "player_active": not game.player_busted and not game.player_folded,
        "last_raiser": game.last_raiser,
    })
    expected.update(game.personality_memory.context(npc, seat, opponents, game.last_raiser, game.hand_number))
    if key != "seven_card_stud":
        cap = old_stage_cap(key, game, npc_index)
        expected["maximum_open_bet"] = min(stack, cap)
        expected["soft_maximum_raise_to"] = min(game.npc_round_bets[npc_index] + stack, cap)
    return expected


class HoldemFamilySameInputsTests(unittest.TestCase):
    """Every decision context of seeded hands equals the pre-group-5 inline formulas."""

    HANDS = 60
    STACKS = (700, 2600, 1700, 400, 1000)   # some NPCs start rich, one short

    def test_contexts_match_the_old_formulas(self):
        real_decide = ai_module.decide_poker_action
        for key in HOLDEM_FAMILY:
            adapter = ADAPTERS_BY_KEY[key]
            with self.subTest(key):
                rng = random.Random("same-inputs-" + key)
                box = {"game": None, "decisions": 0, "rich": 0, "grudges": 0, "pressure": 0}

                def decide(personality, context, rng=None):
                    game = box["game"]
                    expected = old_inputs(key, game, game.current_actor - 1)
                    for name, value in expected.items():
                        self.assertEqual(context[name], value, f"{key} hand {game.hand_number}: {name}")
                    box["decisions"] += 1
                    box["rich"] += context["wealth_pressure"] > 0
                    box["grudges"] += context["grudge_intensity"] > 0
                    box["pressure"] += context["grudge_pressure"] > 0
                    return real_decide(personality, context)

                with mock.patch(DECISION_FUNCTION[key], decide):
                    hands = 0
                    while hands < self.HANDS:
                        game = box["game"]
                        if game is None or adapter.session_over(game):
                            game = box["game"] = adapter.new_game(rng, stacks=list(self.STACKS))
                            for npc in game.npcs:
                                npc["personality_traits"] = dict(npc["personality_traits"], bitterness=10)
                        if not adapter.start_hand(game):
                            box["game"] = None
                            continue
                        adapter.play_hand(game, rng)
                        hands += 1
                self.assertGreater(box["decisions"], 100)
                self.assertGreater(box["rich"], 0)
                self.assertGreater(box["grudges"], 0)
                self.assertGreater(box["pressure"], 0)



# ==================================================
# F14: THE SAME NPC TALKS THE SAME WAY EVERYWHERE
# ==================================================

class ZeroRandom(random.Random):
    """random() is always 0.0: every chat chance fires and the first weighted pool is chosen."""

    def random(self):
        return 0.0


def tactic_decision(personality, context, rng=None):
    # A fixed decision whose strategy is the trapper tactic (its check line: "No hurry.").
    return {"action": "check", "profile": get_poker_personality_profile("balanced"), "bluff": False,
            "strategy": {"enabled": True, "tactic": "trapper", "weight": 1.0}}


class TableTalkTests(unittest.TestCase):
    TACTIC_LINE = "No hurry."

    def npc_line(self, adapter):
        game = adapter.new_game(random.Random(f"talk-{adapter.key}"))
        with mock.patch(DECISION_FUNCTION[adapter.key], tactic_decision):
            if adapter.key == "five_o_poker":
                game.hand_number = 1        # hand 2: the NPC opens the betting, at once
                game.npc_delay_seconds = 0
                adapter.start_hand(game)
                game.rng = ZeroRandom(3)
                adapter.place_all_cards(game)
                self.assertEqual(game.last_npc_action, f"{game.get_npc_name()} checks.")
                return game.last_npc_chat
            adapter.force_open_round(game, [FORCED_STACK] * adapter.seat_count)
            if adapter.key == "blind_mans_bluff":
                game.rng = ZeroRandom(3)
                game._npc_take_turn(1)
                self.assertEqual(game.last_actions[1], "Checked")
                return game.last_chat[1]
            from solitaireplus.games.poker.holdem_chat import generate_npc_action_chat
            adapter.give_turn(game, 1)
            self.assertTrue(game.run_next_npc_action())
            with mock.patch("random.random", return_value=0.0):
                speaker, line = generate_npc_action_chat(game, 0)
            return line

    def test_a_decision_tactic_line_comes_first_in_every_variant(self):
        for adapter in ADAPTERS:
            with self.subTest(adapter.key):
                self.assertEqual(self.npc_line(adapter), self.TACTIC_LINE)

    def test_niche_tables_have_the_grudge_context_the_talk_reads(self):
        for adapter in (BMB, FIVE_O):
            with self.subTest(adapter.key):
                game = adapter.new_game(random.Random(f"talk-context-{adapter.key}"))
                adapter.start_hand(game)
                context = game.get_npc_grudge_context(0)
                self.assertEqual(set(context), {"grudge_pressure", "grudge_target", "grudge_intensity",
                                                "grudge_target_round_total"})


# ==================================================
# F15: NO DECISION-CHANGING QUICK CHAT WHILE OUT OF THE HAND
# ==================================================

class QuickChatOutOfHandTests(unittest.TestCase):
    def chat_game(self, adapter, folded):
        """A hand in progress, the human folded or not; the object the table's quick chat reads."""
        from solitaireplus.games.poker.quick_chat_adapter import adapt_quick_chat_game
        game = adapter.new_game(random.Random(f"chat-{adapter.key}"))
        adapter.force_open_round(game, [FORCED_STACK] * adapter.seat_count)
        if adapter.key == "blind_mans_bluff":
            game.folded[0] = folded
            return adapt_quick_chat_game(game, adapter.key)
        game.player_folded = folded
        # Hold'em's table reads the engine itself; Draw and Stud go through the adapter.
        return game if adapter.key == "texas_holdem" else adapt_quick_chat_game(game, adapter.key)

    def test_a_folded_human_keeps_the_social_lines_only(self):
        from solitaireplus.games.poker.quick_chat import (
            IN_HAND_OPTIONS, MANIPULATIVE_QUICK_CHAT, quick_chat_availability, quick_chat_options_for_game,
            submit_holdem_quick_chat)
        social = tuple(option for option in IN_HAND_OPTIONS if option[0] not in MANIPULATIVE_QUICK_CHAT)
        self.assertEqual({key for key, _label in IN_HAND_OPTIONS} - {key for key, _label in social},
                         {"bored", "great_hand"})
        for adapter in ADAPTERS:
            if adapter.key == "five_o_poker":
                continue   # heads-up: the human's fold ends the hand (between-hand lines then)
            with self.subTest(adapter.key):
                in_hand = self.chat_game(adapter, folded=False)
                self.assertEqual(tuple(quick_chat_options_for_game(in_hand)), IN_HAND_OPTIONS)
                folded = self.chat_game(adapter, folded=True)
                self.assertEqual(tuple(quick_chat_options_for_game(folded)), social)
                for key in ("bored", "great_hand"):
                    self.assertEqual(quick_chat_availability(folded, key), (False, "Not available right now"))
                    result = submit_holdem_quick_chat(folded, key, rng=random.Random(1))
                    self.assertFalse(result["accepted"])
                self.assertEqual(folded.quick_chat_state.get("effects", []), [])

    def test_five_o_fold_ends_the_hand(self):
        from solitaireplus.games.poker.quick_chat import BETWEEN_HAND_OPTIONS, quick_chat_options_for_game
        from solitaireplus.games.poker.quick_chat_adapter import adapt_quick_chat_game
        game = FIVE_O.new_game(random.Random("chat-five-o"))
        open_round(FIVE_O, game)
        self.assertTrue(game.player_check())
        game.pending_npc_at -= 1000.0
        with Decisions(FIVE_O, "bet"):
            game.update()
        self.assertTrue(game.player_fold())
        self.assertEqual(tuple(quick_chat_options_for_game(adapt_quick_chat_game(game, "five_o_poker"))),
                         BETWEEN_HAND_OPTIONS)


if __name__ == "__main__":
    unittest.main()
