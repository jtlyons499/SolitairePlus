"""One small adapter per poker variant, so a table rule can be tested against all of them.

    from tests.support.poker_variants import ADAPTERS

    for adapter in ADAPTERS:
        with self.subTest(adapter.key):
            game = adapter.new_game(random.Random(1), stacks=[20] * adapter.seat_count)
            adapter.start_hand(game)
            adapter.play_hand(game, rng)

The engines store table state differently (Hold'em, Draw and Stud: player_* scalars
plus npc_* lists; Blind Man's Bluff: per-seat lists; Five-O: two scalars). An adapter
hides that. Everywhere: seat 0 is the human, seat i is npcs[i-1], and clockwise means
increasing seat index.

Interface of every adapter:
    key, seat_count, has_side_pots
    new_game(rng, stacks=None, seats=None)
                                 a started session, no hand dealt yet; seats: a smaller table
                                 (Hold'em family and BMB; the forced-state helpers below
                                 assume the default seat_count)
    start_hand(game) -> bool
    stacks(game), set_stacks(game, stacks), pot(game), total_chips(game)
    hand_complete(game), session_over(game)
    step(game, rng)              exactly one unit of progress; returns a short label
    play_hand(game, rng, max_steps=3000)
    can_raise(game, seat)        the engine's own answer
    dealer_seat(game), awards(game), refunds(game), winners(game)
    contributions(game)          per seat, the chips put in this hand (antes included)
    minimum_stack()              smallest stack that can start a hand (Five-O needs its ante)

Forced end states (B86 group 2), for testing how a hand is settled:
    force_showdown(game, contributions, live, ranks, dealer_seat, pot=None)
        Builds a resolvable end state and settles it with the engine's own showdown code.
        contributions: per seat, chips put in this hand; live: per seat, still in the hand;
        ranks: per seat, a card rank 2..14 (only live seats matter; higher wins, equal ties);
        dealer_seat: the seat odd chips start after. Every stack is set to FORCED_STACK first,
        so a seat's gain is stacks(game)[seat] - FORCED_STACK. pot overrides the pot (Five-O's
        theoretical odd chip only). Returns the game.
    force_fold_win(game, contributions, winner)
        Everyone but winner has folded; the engine pays the pot to winner.

Betting (B86 group 3):
    forced_bets                  "blinds" (Hold'em, Draw), "bring_in" (Stud) or "antes" (Five-O, BMB)
    in_hand(game)                per seat: still in this hand (dealt in, not folded)
    others_can_respond(game, seat)   another seat in the hand still has chips
    deal_forced_bets(game, stacks, dealer_seat=0, bring_in_seat=None)
        Deal a hand from these stacks and stop once the forced bets are in, before anyone acts.
    force_all_in_opponents(game, actor, bet)
        actor (with FORCED_STACK chips, half of `bet` in this round) faces a bet of `bet`
        (0: nothing bet yet) and every other seat in the hand is all-in. It is actor's turn.
    try_wager(game, seat, total) The engine's bet/raise entry point for seat (to `total` chips
                                 this round; Five-O's fixed size ignores it). Returns its result.
    npc_context(game, seat)      the NPC's AI decision context
    npc_turn(game, seat, action) run the NPC's turn with its AI decision forced to `action`
    record_wagers(game, log)     wrap the bet/raise entry points: every bet or raise that lifts
                                 the current bet appends (seat, others_can_respond beforehand)
  Hold'em family and Blind Man's Bluff only (Five-O's single round has a fixed bet size):
    force_open_round(game, stacks)   a betting round with nothing bet and every seat to act
                                     (Stud: fifth street, where the street bet is the big bet)
    call(game, seat), give_turn(game, seat)
"""
import random
from unittest import mock

from solitaireplus.games.poker.ai import get_poker_personality_profile
from solitaireplus.games.poker.blind_mans_bluff import BlindMansBluffGame
from solitaireplus.games.poker.five_card_draw import FiveCardDrawGame
from solitaireplus.games.poker.five_o import FiveOPokerGame
from solitaireplus.games.poker.holdem import TexasHoldemGame
from solitaireplus.games.poker.seven_card_stud import SevenCardStudGame


def _traits(caution, aggressiveness, unpredictability, escalation,
            selectivity, tenacity, pessimism, bitterness):
    return {
        "caution": caution, "aggressiveness": aggressiveness,
        "unpredictability": unpredictability, "escalation": escalation,
        "selectivity": selectivity, "tenacity": tenacity,
        "pessimism": pessimism, "bitterness": bitterness,
    }


# Fixed opponents with clearly different personalities, so the AI takes every kind of action.
TEST_NPCS = (
    {"id": "variant_test_ada", "name": "Ada Test", "personality_traits": _traits(2, 9, 4, 7, 3, 4, 2, 6)},
    {"id": "variant_test_bo", "name": "Bo Test", "personality_traits": _traits(9, 2, 2, 2, 7, 8, 7, 3)},
    {"id": "variant_test_cy", "name": "Cy Test", "personality_traits": _traits(5, 6, 10, 6, 4, 5, 4, 8)},
    {"id": "variant_test_di", "name": "Di Test", "personality_traits": _traits(5, 5, 3, 4, 5, 5, 4, 3)},
)


FORCED_STACK = 500

# Card rank names by value, for engines that score real cards (Blind Man's Bluff, Five-O).
RANK_NAMES = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9", 10: "10",
              11: "J", 12: "Q", 13: "K", 14: "A"}


def _forced_decision(action):
    """A stand-in for decide_poker_action that always returns `action`."""
    def decide(personality, context, rng=None):
        return {"action": action, "profile": get_poker_personality_profile("balanced"), "bluff": False}

    return decide


def _start_session_without_dealing(game, start):
    """Run start_session for an engine that deals hand 1 inside it (Five-O, Blind Man's Bluff).

    start_hand is shadowed on the instance for the duration of the call, so the session is set
    up exactly as usual but no chips move and no cards are dealt until the adapter's start_hand.
    """
    game.start_hand = lambda: True
    try:
        start()
    finally:
        del game.start_hand


class PokerVariantAdapter:
    key = ""
    seat_count = 0
    has_side_pots = True
    starting_stack = 1000

    def npcs(self, seats=None):
        return [dict(npc) for npc in TEST_NPCS[:(seats or self.seat_count) - 1]]

    def new_game(self, rng, stacks=None, seats=None):
        """seats: table size (default seat_count); the forced-state helpers assume the default."""
        # Hold'em-family decks and the shared AI use the module-level random.
        random.seed(rng.getrandbits(64))
        game = self._create(rng)
        self._start_session(game, seats or self.seat_count)
        if stacks is not None:
            self.set_stacks(game, stacks)
        return game

    def start_hand(self, game):
        return bool(game.start_hand())

    def pot(self, game):
        return game.pot

    def total_chips(self, game):
        return sum(self.stacks(game)) + self.pot(game)

    def hand_complete(self, game):
        return bool(game.hand_complete)

    def minimum_stack(self):
        return 1

    def play_hand(self, game, rng, max_steps=3000):
        labels = []
        for _ in range(max_steps):
            if self.hand_complete(game):
                return labels
            labels.append(self.step(game, rng))
        raise AssertionError(
            f"{self.key}: hand {game.hand_number} stalled after {max_steps} steps; "
            f"last steps {labels[-6:]}, stacks {self.stacks(game)}, pot {self.pot(game)}"
        )

    def awards(self, game):
        return getattr(game, "last_pot_awards", [])

    def refunds(self, game):
        return getattr(game, "last_refunds", {})

    def _stall(self, game, why):
        raise AssertionError(f"{self.key}: hand {game.hand_number} cannot progress: {why}")

    def others_can_respond(self, game, seat):
        in_hand, stacks = self.in_hand(game), self.stacks(game)
        return any(other != seat and in_hand[other] and stacks[other] > 0 for other in range(len(stacks)))

    def _record(self, game, log, name, seat_of):
        """Wrap game.<name>; a call that lifts current_bet logs (seat, others_can_respond before)."""
        method = getattr(game, name)

        def wrapper(*args, **kwargs):
            seat = seat_of(args, kwargs)
            respond = self.others_can_respond(game, seat)
            before = game.current_bet
            result = method(*args, **kwargs)
            if result and game.current_bet > before:
                log.append((seat, respond))
            return result

        setattr(game, name, wrapper)


class HoldemFamilyAdapter(PokerVariantAdapter):
    """Texas Hold'em, Five-Card Draw and Seven-Card Stud share TexasHoldemGame's table."""

    seat_count = 5
    blind_unit = 10   # table_stakes.get_poker_ante(1000): Hold'em 10/20 blinds, Stud 10/20 limits

    def __init__(self, key, game_class, fixed_limit=False):
        self.key = key
        self.game_class = game_class
        self.fixed_limit = fixed_limit
        self.forced_bets = "bring_in" if fixed_limit else "blinds"

    def _create(self, rng):
        return self.game_class()

    def _start_session(self, game, seats):
        game.start_session(self.npcs(seats), self.starting_stack, self.blind_unit)

    def stacks(self, game):
        return game.seat_stacks()

    def set_stacks(self, game, stacks):
        game.player_stack = int(stacks[0])
        game.npc_stacks = [int(stack) for stack in stacks[1:]]
        game.player_busted = game.player_stack <= 0
        game.npc_busted = [stack <= 0 for stack in game.npc_stacks]

    def session_over(self, game):
        return game.table_is_over()

    def step(self, game, rng):
        if game.current_stage == "draw":
            discards = [index for index in range(len(game.player_hand)) if rng.random() < 0.4]
            if not game.player_draw(discards):
                self._stall(game, "player_draw refused")
            return "draw"
        if game.is_betting_round_complete():
            stage = game.current_stage
            if not game.advance_after_betting_round():
                self._stall(game, f"advance_after_betting_round refused at {stage}")
            return "advance"
        if game.current_actor == 0:
            return self._human_action(game, rng)
        game.run_next_npc_action()
        return "npc"

    def _human_action(self, game, rng):
        choices = []
        if game.can_player_check():
            choices += ["check"] * 4
        if game.can_player_call():
            choices += ["call"] * 4 + ["fold"]
        if game.can_player_raise():
            choices += ["raise"] * 2
        if not choices:
            self._stall(game, "the human is the current actor but has no legal action")
        action = rng.choice(choices)
        if action == "raise":
            action = "bet" if game.current_bet <= 0 else "raise"
            done = self._human_wager(game, rng)
        else:
            done = getattr(game, "player_" + action)()
        if not done:
            self._stall(game, f"player_{action} refused")
        return "human:" + action

    def _human_wager(self, game, rng):
        if self.fixed_limit:
            total = game.get_player_fixed_bet_or_raise_to()
        else:
            highest = game.get_player_maximum_raise_to()
            total = rng.randint(min(game.get_minimum_raise_to(), highest), highest)
        if game.current_bet <= 0:
            # Nothing is bet this round, so the round bet is 0 and the total is the bet.
            return game.player_bet(total)
        return game.player_raise(total)

    def can_raise(self, game, seat):
        if seat == 0:
            return game.can_player_raise()
        return game.can_npc_raise(seat - 1)

    def dealer_seat(self, game):
        return game.dealer_index

    def winners(self, game):
        return list(game.winner_indexes)

    def contributions(self, game):
        return list(game.get_hand_contributions())

    def _force_end_state(self, game, contributions, live, dealer_seat):
        self.start_hand(game)
        while len(game.community_cards) < 5 and self.key == "texas_holdem":
            game.community_cards.append(game.draw_card())
        game.player_hand_contribution = int(contributions[0])
        game.npc_hand_contributions = [int(amount) for amount in contributions[1:]]
        self.set_stacks(game, [FORCED_STACK] * self.seat_count)
        game.pot = sum(contributions)
        game.player_folded = not live[0]
        game.npc_folded = [not flag for flag in live[1:]]
        game.dealer_index = dealer_seat

    def force_showdown(self, game, contributions, live, ranks, dealer_seat, pot=None):
        self._force_end_state(game, contributions, live, dealer_seat)
        if pot is not None:
            game.pot = pot
        # A high-card score whose only kicker is the rank: higher rank wins, equal ranks tie.
        results = {seat: ((0, int(ranks[seat])), []) for seat in range(self.seat_count) if live[seat]}
        with mock.patch.object(game, "get_showdown_result", side_effect=results.get):
            game.showdown()
        return game

    def force_fold_win(self, game, contributions, winner):
        live = [seat == winner for seat in range(self.seat_count)]
        self._force_end_state(game, contributions, live, game.dealer_index)
        game.award_pot_to_single_player(winner)
        return game

    # ----- betting (group 3) -----

    def in_hand(self, game):
        return game.seat_in_hand()

    def deal_forced_bets(self, game, stacks, dealer_seat=0, bring_in_seat=None):
        self.set_stacks(game, stacks)
        game.dealer_index = dealer_seat - 1   # rotate_dealer moves the button on to dealer_seat
        if bring_in_seat is None:
            return self.start_hand(game)
        with mock.patch.object(game, "get_bring_in_index", return_value=bring_in_seat):
            return self.start_hand(game)

    def _fresh_round(self, game):
        self.start_hand(game)
        if self.fixed_limit:
            game.current_stage = "fifth"
            game.third_street_completed = True
        game.reset_betting_round(assign_actor=False)

    def _set_betting_state(self, game, stacks, round_bets, has_acted, current_bet, actor):
        """Every seat in the hand; round bets are the whole hand's contributions and the pot."""
        npc_count = self.seat_count - 1
        game.player_stack, game.npc_stacks = int(stacks[0]), [int(stack) for stack in stacks[1:]]
        game.player_busted, game.npc_busted = False, [False] * npc_count
        game.player_folded, game.npc_folded = False, [False] * npc_count
        game.player_all_in, game.npc_all_in = stacks[0] == 0, [stack == 0 for stack in stacks[1:]]
        game.player_round_bet, game.npc_round_bets = round_bets[0], list(round_bets[1:])
        game.player_hand_contribution, game.npc_hand_contributions = round_bets[0], list(round_bets[1:])
        game.pot = sum(round_bets)
        game.player_has_acted, game.npc_has_acted = has_acted[0], list(has_acted[1:])
        game.current_bet = current_bet
        game.current_actor = actor
        game.betting_round_complete = False

    def force_all_in_opponents(self, game, actor, bet):
        self._fresh_round(game)
        stacks = [0] * self.seat_count
        stacks[actor] = FORCED_STACK
        round_bets = [bet] * self.seat_count
        round_bets[actor] = bet // 2
        has_acted = [True] * self.seat_count
        has_acted[actor] = False
        self._set_betting_state(game, stacks, round_bets, has_acted, bet, actor)
        game.last_raise_size = bet // 2
        game.last_raiser = (actor + 1) % self.seat_count if bet else None
        return game

    def force_open_round(self, game, stacks):
        self._fresh_round(game)
        self._set_betting_state(game, stacks, [0] * self.seat_count, [False] * self.seat_count, 0, 1)
        game.last_raise_size, game.last_raiser = 0, None
        return game

    def give_turn(self, game, seat):
        game.current_actor = seat

    def try_wager(self, game, seat, total):
        if seat == 0:
            game.current_actor = 0
            return game.player_bet(total) if game.current_bet <= 0 else game.player_raise(total)
        if game.current_bet <= 0:
            return game.npc_bet(seat - 1, total)
        return game.npc_raise(seat - 1, total)

    def call(self, game, seat):
        if seat == 0:
            game.current_actor = 0
            return game.player_call()
        return game.npc_call(seat - 1)

    def npc_context(self, game, seat):
        return game.build_npc_ai_context(seat - 1)

    def npc_turn(self, game, seat, action):
        game.current_actor = seat
        with mock.patch("solitaireplus.games.poker.holdem.decide_poker_action", _forced_decision(action)):
            return game.run_next_npc_action()

    def record_wagers(self, game, log):
        def npc_seat(args, kwargs):
            return (args[0] if args else kwargs["npc_index"]) + 1

        for name in ("player_bet", "player_raise"):
            self._record(game, log, name, lambda args, kwargs: 0)
        for name in ("npc_bet", "npc_raise"):
            self._record(game, log, name, npc_seat)


class BlindMansBluffAdapter(PokerVariantAdapter):
    key = "blind_mans_bluff"
    seat_count = 4
    forced_bets = "antes"

    def _create(self, rng):
        game = BlindMansBluffGame(random.Random(rng.getrandbits(64)))
        game.npc_delay_seconds = 0   # NPC turns run inside the engine, without the table-speed pause
        return game

    def _start_session(self, game, seats):
        _start_session_without_dealing(
            game, lambda: game.start_session(self.npcs(seats), self.starting_stack))

    def stacks(self, game):
        return game.seat_stacks()

    def set_stacks(self, game, stacks):
        game.player_stack = int(stacks[0])
        game.npc_stacks = [int(stack) for stack in stacks[1:]]

    def session_over(self, game):
        return bool(game.session_complete)

    def step(self, game, rng):
        # NPC turns run inside the engine until the human must act or the hand ends.
        actions = game.get_player_actions()
        if not actions:
            self._stall(game, "the hand is live but the human has no action")
        weights = {"check": 4, "call": 4, "fold": 1, "bet": 2, "raise": 2}
        action = rng.choice([name for name in actions for _ in range(weights.get(name, 1))])
        if action in ("bet", "raise"):
            amount = rng.choice(game.get_player_bet_presets())[1]
            done = getattr(game, "player_" + action)(amount)
        else:
            done = getattr(game, "player_" + action)()
        if not done:
            self._stall(game, f"player_{action} refused")
        return "human:" + action

    def can_raise(self, game, seat):
        if seat == 0:
            actions = game.get_player_actions()
            return "bet" in actions or "raise" in actions
        return game._can_raise(seat)

    def dealer_seat(self, game):
        # The seat before the opener, so the opener is first to the dealer's left.
        return (game.opening_index - 1) % self.seat_count

    def winners(self, game):
        return list(game.last_winner_indexes)

    def contributions(self, game):
        return list(game.hand_contributions)

    def _force_end_state(self, game, contributions, live, ranks, opening_index):
        # Built directly rather than through start_hand, which could already run NPC turns.
        count = self.seat_count
        game.hand_number += 1
        game.presentation_events.clear()
        game.cards = [{"rank": RANK_NAMES[int(ranks[seat])], "suit": "Clubs Diamonds Hearts Spades".split()[seat % 4]}
                      for seat in range(count)]
        game.folded = [not flag for flag in live]
        game.live_at_start = list(range(count))
        game.hand_contributions = [int(amount) for amount in contributions]
        game.round_bets = list(game.hand_contributions)
        game.last_actions, game.last_chat = [""] * count, [""] * count
        game.npc_ai_last_decisions = [None] * (count - 1)
        self.set_stacks(game, [FORCED_STACK] * count)
        game.pot = sum(game.hand_contributions)
        game.current_bet = max(game.hand_contributions)
        game.opening_index = opening_index
        game.pending, game.raise_rights = set(), set()
        game.phase, game.bet_state = "betting", ""
        game.hand_complete = False

    def force_showdown(self, game, contributions, live, ranks, dealer_seat, pot=None):
        self._force_end_state(game, contributions, live, ranks, (dealer_seat + 1) % self.seat_count)
        if pot is not None:
            game.pot = pot
        game._showdown()
        return game

    def force_fold_win(self, game, contributions, winner):
        live = [seat == winner for seat in range(self.seat_count)]
        self._force_end_state(game, contributions, live, [2] * self.seat_count, game.opening_index)
        game._advance(winner)   # one seat left: the engine pays it the pot
        return game

    # ----- betting (group 3) -----

    def in_hand(self, game):
        return game.seat_in_hand()

    def deal_forced_bets(self, game, stacks, dealer_seat=0, bring_in_seat=None):
        # start_hand posts the antes and then runs turns until the human must act; stop before
        # the first turn. dealer_seat is not used: the opener rotates with the hand number.
        self.set_stacks(game, stacks)
        with mock.patch.object(game, "_advance"):
            return self.start_hand(game)

    def _set_betting_state(self, game, stacks, round_bets, pending, current_bet, actor):
        count = self.seat_count
        game.hand_number += 1
        game.presentation_events.clear()
        game.cards = [{"rank": RANK_NAMES[10 + seat], "suit": "Clubs"} for seat in range(count)]
        game.folded = [False] * count
        game.live_at_start = list(range(count))
        game.round_bets = list(round_bets)
        game.hand_contributions = list(round_bets)
        game.last_actions, game.last_chat = [""] * count, [""] * count
        game.npc_ai_last_decisions = [None] * (count - 1)
        self.set_stacks(game, stacks)
        game.pot = sum(round_bets)
        game.current_bet = current_bet
        game.pending, game.raise_rights = set(pending), set(pending)
        game.current_actor = actor
        game.phase, game.bet_state = "betting", ""
        game.hand_complete = False

    def force_all_in_opponents(self, game, actor, bet):
        stacks = [0] * self.seat_count
        stacks[actor] = FORCED_STACK
        round_bets = [bet] * self.seat_count
        round_bets[actor] = bet // 2
        self._set_betting_state(game, stacks, round_bets, {actor}, bet, actor)
        game.last_raise_size = bet // 2 if bet else game._base_minimum()
        game.bettor_index = game.last_raiser = (actor + 1) % self.seat_count if bet else None
        return game

    def force_open_round(self, game, stacks):
        pending = {seat for seat in range(self.seat_count) if stacks[seat] > 0}
        self._set_betting_state(game, stacks, [0] * self.seat_count, pending, 0, 1)
        game.last_raise_size = game._base_minimum()
        game.bettor_index = game.last_raiser = None
        return game

    def give_turn(self, game, seat):
        game.current_actor = seat

    def try_wager(self, game, seat, total):
        return game._act(seat, "raise" if game.current_bet else "bet", total)

    def call(self, game, seat):
        return game._act(seat, "call")

    def npc_context(self, game, seat):
        return game._npc_context(seat)

    def npc_turn(self, game, seat, action):
        with mock.patch("solitaireplus.games.poker.blind_mans_bluff.decide_poker_action",
                        _forced_decision(action)):
            game._npc_take_turn(seat)

    def record_wagers(self, game, log):
        self._record(game, log, "_act", lambda args, kwargs: args[0])


class FiveOAdapter(PokerVariantAdapter):
    key = "five_o_poker"
    seat_count = 2
    has_side_pots = False
    forced_bets = "antes"
    starting_stack = 500   # ante 5, the smallest Five-O ante

    def _create(self, rng):
        return FiveOPokerGame(random.Random(rng.getrandbits(64)))

    def _start_session(self, game, seats):
        if seats != 2:
            raise ValueError("Five-O is always heads-up")
        _start_session_without_dealing(
            game, lambda: game.start_session(self.npcs()[0], self.starting_stack))

    def minimum_stack(self):
        game = FiveOPokerGame(random.Random(0))
        self._start_session(game, 2)
        return game.ante

    def stacks(self, game):
        return game.seat_stacks()

    def set_stacks(self, game, stacks):
        game.player_stack, game.npc_stack = (int(stack) for stack in stacks)

    def session_over(self, game):
        return bool(game.session_complete)

    def step(self, game, rng):
        if game.phase == "placement":
            columns = game.get_available_player_columns()
            if not columns:
                self._stall(game, "placement phase without an open column")
            game.place_player_card(rng.choice(columns))
            return "place"
        if game.pending_npc_at:
            game.pending_npc_at -= 1000.0   # the NPC's thinking pause is over
            game.update()
            return "npc"
        if game.showdown_pending_finish:
            game.showdown_reveal_started_at -= 1000.0   # every column has been revealed
            game.update()
            return "reveal"
        actions = game.get_player_actions()
        if not actions:
            self._stall(game, f"no human action in phase {game.phase!r} / {game.bet_state!r}")
        weights = {"check": 4, "call": 4, "fold": 1, "bet": 2}
        action = rng.choice([name for name in actions for _ in range(weights.get(name, 1))])
        if not getattr(game, "player_" + action)():
            self._stall(game, f"player_{action} refused")
        return "human:" + action

    def can_raise(self, game, seat):
        if seat == 0:
            return "bet" in game.get_player_actions()
        # The NPC opens and raises through _npc_bet/_npc_raise, which both ask _seat_can_raise.
        return game.phase == "betting" and game._seat_can_raise(seat)

    def dealer_seat(self, game):
        # The non-opener, so the opener is first to the dealer's left.
        return 1 - game.opening_index

    def winners(self, game):
        return {"player": [0], "npc": [1], "tie": [0, 1]}.get(game.last_winner, [])

    def contributions(self, game):
        return list(game.hand_contributions)

    # Column hands for forced showdowns: a pair of aces beats seven-high; two seven-highs tie.
    STRONG_COLUMN = (("A", "Clubs"), ("A", "Diamonds"), ("K", "Hearts"), ("Q", "Spades"), ("J", "Clubs"))
    WEAK_COLUMN = (("2", "Clubs"), ("3", "Diamonds"), ("4", "Hearts"), ("5", "Spades"), ("7", "Clubs"))

    def _column(self, cards):
        return [{"rank": rank, "suit": suit} for rank, suit in cards]

    def _force_end_state(self, game, contributions, opening_index):
        self.start_hand(game)
        self.set_stacks(game, [FORCED_STACK] * 2)
        game.hand_contributions = [int(amount) for amount in contributions]
        game.pot = sum(game.hand_contributions)
        game.opening_index = opening_index
        game.phase, game.bet_state = "betting", ""
        game.pending_npc_at = 0.0
        game.player_drawn_card = None

    def force_showdown(self, game, contributions, live, ranks, dealer_seat, pot=None):
        if not (live[0] and live[1]):
            raise ValueError("a Five-O showdown needs both seats; use force_fold_win")
        if contributions[0] != contributions[1]:
            raise ValueError("Five-O has one pot: a showdown always has equal contributions")
        self._force_end_state(game, contributions, 1 - dealer_seat)
        if pot is not None:
            game.pot = pot
        # The better rank wins the first three columns (a 3-0 win); the rest tie.
        winner = None if ranks[0] == ranks[1] else (0 if ranks[0] > ranks[1] else 1)
        player, npc = [], []
        for column in range(5):
            mine = self.STRONG_COLUMN if winner == 0 and column < 3 else self.WEAK_COLUMN
            theirs = self.STRONG_COLUMN if winner == 1 and column < 3 else self.WEAK_COLUMN
            player.append(self._column(mine))
            npc.append(self._column(theirs))
        game.player_columns, game.npc_columns = player, npc
        game._showdown()
        game.showdown_reveal_started_at -= 1000.0   # every column has been revealed
        game.update()
        return game

    def force_fold_win(self, game, contributions, winner):
        self._force_end_state(game, contributions, game.opening_index)
        game.player_folded, game.npc_folded = winner != 0, winner != 1
        game._award_fold_win(player_won=winner == 0)
        return game

    # ----- betting (group 3) -----

    def in_hand(self, game):
        return game.seat_in_hand()

    def deal_forced_bets(self, game, stacks, dealer_seat=0, bring_in_seat=None):
        # Only antes: the hand starts with the placement phase, where nobody bets.
        self.set_stacks(game, stacks)
        return self.start_hand(game)

    def place_all_cards(self, game, rng=None):
        """Finish the placement phase (the human takes the first open column).

        When the NPC opens the betting, its queued opening (bet_state "npc_open") is resolved
        too, by moving its thinking pause into the past, so the round is ready for the human."""
        while game.phase == "placement":
            game.place_player_card(game.get_available_player_columns()[0])
        if game.bet_state == "npc_open" and game.pending_npc_at:
            game.pending_npc_at -= 1000.0
            game.update()

    def force_all_in_opponents(self, game, actor, bet):
        self.start_hand(game)
        self.place_all_cards(game)   # hand 1: the human opens, so no NPC decision runs yet
        stacks = [0, 0]
        stacks[actor] = FORCED_STACK
        paid = [bet, bet]
        paid[actor] = bet // 2
        self.set_stacks(game, stacks)
        game.player_betting_paid, game.npc_betting_paid = paid
        game.hand_contributions = [game.ante + paid[0], game.ante + paid[1]]
        game.pot = sum(game.hand_contributions)
        game.current_bet = bet
        game.raise_count = 0
        game.pending_npc_at = 0.0
        game.bet_state = ("player_response" if bet else "player_open") if actor == 0 else "player_open"
        return game

    def try_wager(self, game, seat, total):
        if seat == 0:
            return game.player_bet()
        return game._npc_raise() if game.current_bet else game._npc_bet()

    def npc_context(self, game, seat):
        captured = {}

        def decide(personality, context, rng=None):
            captured.update(context)
            return {"action": "check", "profile": get_poker_personality_profile("balanced"), "bluff": False}

        with mock.patch("solitaireplus.games.poker.five_o.decide_poker_action", decide):
            game._npc_decision(facing_bet=game.current_bet > game.npc_betting_paid)
        return captured

    def npc_turn(self, game, seat, action):
        with mock.patch("solitaireplus.games.poker.five_o.decide_poker_action", _forced_decision(action)):
            game._finish_opponent_response()

    def record_wagers(self, game, log):
        self._record(game, log, "player_bet", lambda args, kwargs: 0)
        for name in ("_npc_bet", "_npc_raise"):
            self._record(game, log, name, lambda args, kwargs: 1)


ADAPTERS = (
    HoldemFamilyAdapter("texas_holdem", TexasHoldemGame),
    HoldemFamilyAdapter("five_card_draw", FiveCardDrawGame),
    HoldemFamilyAdapter("seven_card_stud", SevenCardStudGame, fixed_limit=True),
    FiveOAdapter(),
    BlindMansBluffAdapter(),
)

ADAPTERS_BY_KEY = {adapter.key: adapter for adapter in ADAPTERS}
