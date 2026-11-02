"""Host-authoritative multiplayer modes that share the room-code relay.

The relay only routes JSON.  All game rules live here on the host so every
client sees one authoritative result.  These modes intentionally use four
seats even though the Hold'em relay can route six clients.
"""
from __future__ import annotations

import copy
import json
import math
import random
from fractions import Fraction

from niche_poker_common import RANK_VALUES, build_standard_deck, round_chip_amount
from score_four_difficulty import puzzle_pool
from roulette import ROULETTE_NUMBERS, RED_NUMBERS
from multiplayer_paths import ROOT

SKILL_KEYS = ("low", "mid", "strong", "elite")
SKILL_LABELS = {
    "low": "Casual",
    "mid": "Skilled",
    "strong": "Expert",
    "elite": "Master",
}
STACK_OPTIONS = (1000, 5000, 10000, 25000)
ROULETTE_TIMERS = (15, 25, 40, 60)
SCORE_FOUR_DIFFICULTIES = ("easy", "standard", "difficult", "extreme")


def _load_npc_roster():
    roster = json.loads((ROOT / "data" / "npcs.json").read_text(encoding="utf-8"))
    if not isinstance(roster, list) or not roster:
        raise ValueError("data/npcs.json must contain NPC records")
    return roster


def _clean_name(value):
    return "".join(c for c in str(value or "Player") if c.isprintable())[:32].strip() or "Player"


def _clamp_int(value, low, high, default=None):
    try:
        return max(low, min(high, int(value)))
    except (TypeError, ValueError, OverflowError):
        return low if default is None else default


def _seat_record(kind="Empty", name="Open seat", skill="mid", identity=None, npc=None):
    return {
        "kind": kind,
        "name": _clean_name(name),
        "skill": skill if skill in SKILL_KEYS else "mid",
        "identity": identity,
        "npc": copy.deepcopy(npc) if isinstance(npc, dict) else None,
        "connected": kind != "Human" or identity is not None,
        "spectator": False,
        "stack": 0,
        "score": 0,
        "action": "",
    }


class FourSeatAuthority:
    mode = "party"
    title = "Multiplayer"

    def __init__(self, host_name, rng=None):
        self.rng = rng or random.Random()
        self.roster = copy.deepcopy(_load_npc_roster())
        self.connections = {0: _clean_name(host_name)}
        self.humans = {0: 0}
        self.seat_data = [_seat_record() for _ in range(4)]
        self.seat_data[0] = _seat_record("Human", host_name, identity=0)
        self.revision = 0
        self.started = False
        self.waiting = []
        self.notice = ""
        self.now = 0

    def _touch(self, notice=None):
        if notice:
            self.notice = str(notice)[:120]
        self.revision += 1

    def join(self, identity, name):
        if identity in self.connections:
            return
        name = _clean_name(name)
        self.connections[identity] = name
        if self.started:
            self.waiting.append((identity, name))
            self._touch(f"{name} will join when the table returns to the lobby.")
            return
        self._assign_joiner(identity, name)
        self._touch(f"{name} joined the room.")

    def _assign_joiner(self, identity, name):
        # Humans replace an optional NPC before being refused a seat.
        seat = next((i for i in range(1, 4) if self.seat_data[i]["kind"] == "Empty"), None)
        if seat is None:
            seat = next((i for i in range(1, 4) if self.seat_data[i]["kind"] == "NPC"), None)
        if seat is None:
            self.waiting.append((identity, name))
            return False
        self.humans[identity] = seat
        self.seat_data[seat] = _seat_record("Human", name, identity=identity)
        return True

    def leave(self, identity):
        self.connections.pop(identity, None)
        self.waiting = [pair for pair in self.waiting if pair[0] != identity]
        seat = self.humans.pop(identity, None)
        if seat is None:
            return
        if self.started:
            self.seat_data[seat]["connected"] = False
            self.seat_data[seat]["spectator"] = True
            self.seat_data[seat]["action"] = "Disconnected"
        else:
            self.seat_data[seat] = _seat_record()
        self._touch()

    def _active_lobby_count(self):
        return sum(1 for seat in self.seat_data if seat["kind"] in ("Human", "NPC"))

    def _random_npc_record(self, seat=None):
        used = {
            row.get("npc", {}).get("id")
            for index, row in enumerate(self.seat_data)
            if index != seat and row.get("kind") == "NPC" and isinstance(row.get("npc"), dict)
        }
        choices = [npc for npc in self.roster if npc.get("id") not in used] or list(self.roster)
        npc = copy.deepcopy(self.rng.choice(choices))
        # Party-mode skill is intentionally independent from the NPC's
        # single-player tier. It is rerolled for each lobby selection.
        skill = self.rng.choice(SKILL_KEYS)
        return _seat_record("NPC", npc.get("name", "Computer"), skill=skill, npc=npc)

    def _cycle_npc(self, seat, delta=1):
        # Older clients used this action to cycle skill. Keep accepting it,
        # but reroll the actual single-player NPC + party-game skill together.
        if not 1 <= seat <= 3 or seat in self.humans.values() or self.started:
            return False
        self.seat_data[seat] = self._random_npc_record(seat)
        self._touch()
        return True

    def _toggle_npc(self, seat):
        if not 1 <= seat <= 3 or seat in self.humans.values() or self.started:
            return False
        if self.seat_data[seat]["kind"] == "NPC":
            self.seat_data[seat] = _seat_record()
        else:
            self.seat_data[seat] = self._random_npc_record(seat)
        self._touch()
        return True

    def _base_view(self, identity):
        seats = copy.deepcopy(self.seat_data)
        for index, seat in enumerate(seats):
            if seat["kind"] == "Human":
                owner = seat.get("identity")
                seat["connected"] = owner in self.connections
        return {
            "mode": self.mode,
            "title": self.title,
            "revision": self.revision,
            "seats": seats,
            "your_seat": self.humans.get(identity),
            "hosting": identity == 0,
            "waiting_names": [name for _, name in self.waiting],
            "notice": self.notice,
        }

    def lobby_view(self, identity):
        data = self._base_view(identity)
        data.update({"type": "lobby", "can_start": self._active_lobby_count() >= 2})
        return data

    def act_lobby(self, identity, action, amount):
        if identity != 0 or self.started:
            return False
        if action == "npc_toggle":
            try:
                seat = int((amount or {}).get("seat"))
            except (TypeError, ValueError, AttributeError):
                return False
            return self._toggle_npc(seat)
        if action in ("npc_skill", "npc_reroll"):
            try:
                seat = int((amount or {}).get("seat"))
                delta = int((amount or {}).get("delta", 1))
            except (TypeError, ValueError, AttributeError):
                return False
            return self._cycle_npc(seat, delta)
        return False

    def view(self, identity):
        return self.lobby_view(identity)

    def act(self, identity, action, amount=0, revision=None):
        if identity not in self.connections or revision != self.revision:
            return False
        return self.act_lobby(identity, action, amount)

    def update(self, now):
        self.now = int(now)
        return None


class ScoreFourAuthority(FourSeatAuthority):
    mode = "score_four"
    title = "Score-Four (24)"

    NPC_RANGES = {
        "low": (55.0, 75.0),
        "mid": (40.0, 65.0),
        "strong": (23.0, 36.0),
        "elite": (15.0, 26.0),
    }

    def __init__(self, host_name, rng=None):
        super().__init__(host_name, rng)
        self.difficulty = "standard"
        self.scores = [0, 0, 0, 0]
        self.round_number = 0
        self.numbers = []
        self.suits = []
        self.round_started_at = 0
        self.round_winner = None
        self.match_winner = None
        self.ready = set()
        self.npc_deadlines = {}

    def lobby_view(self, identity):
        data = super().lobby_view(identity)
        data.update({"difficulty": self.difficulty})
        return data

    def _start_round(self, now):
        numbers = list(self.rng.choice(puzzle_pool(self.difficulty)))
        self.rng.shuffle(numbers)
        self.numbers = numbers
        self.suits = [self.rng.choice(("Hearts", "Diamonds", "Clubs", "Spades")) for _ in range(4)]
        self.round_number += 1
        self.round_started_at = int(now)
        self.round_winner = None
        self.ready.clear()
        self.npc_deadlines = {}
        for seat, record in enumerate(self.seat_data):
            if record["kind"] != "NPC":
                continue
            low, high = self.NPC_RANGES.get(record.get("skill", "mid"), self.NPC_RANGES["mid"])
            self.npc_deadlines[seat] = self.round_started_at + int(self.rng.uniform(low, high) * 1000)
        self._touch()

    def start(self, now=0):
        if self.started or self._active_lobby_count() < 2:
            return False
        self.started = True
        self.scores = [0, 0, 0, 0]
        self.round_number = 0
        self.match_winner = None
        self._start_round(now)
        return True

    def _win_round(self, seat):
        if self.round_winner is not None or self.match_winner is not None:
            return False
        if not 0 <= seat < 4 or self.seat_data[seat]["kind"] not in ("Human", "NPC"):
            return False
        self.round_winner = seat
        self.scores[seat] += 1
        self.seat_data[seat]["score"] = self.scores[seat]
        if self.scores[seat] >= 3:
            self.match_winner = seat
        self.ready = {i for i, row in enumerate(self.seat_data) if row["kind"] == "NPC"}
        self._touch(f"{self.seat_data[seat]['name']} solved the round first.")
        return True

    def act(self, identity, action, amount=0, revision=None):
        if identity not in self.connections or revision != self.revision:
            return False
        if not self.started:
            if action == "difficulty" and identity == 0 and str(amount) in SCORE_FOUR_DIFFICULTIES:
                self.difficulty = str(amount); self._touch(); return True
            if action == "start" and identity == 0:
                return self.start(self.now)
            return self.act_lobby(identity, action, amount)
        seat = self.humans.get(identity)
        if seat is None:
            return False
        if action == "solved" and self.round_winner is None and self.match_winner is None:
            return self._win_round(seat)
        if action == "ready" and self.round_winner is not None and self.match_winner is None:
            self.ready.add(seat); self._touch(); return True
        if action == "rematch" and identity == 0 and self.match_winner is not None:
            self.scores = [0, 0, 0, 0]
            for row in self.seat_data: row["score"] = 0
            self.match_winner = None; self.round_number = 0
            self._start_round(self.now); return True
        if action == "return_lobby" and identity == 0 and self.match_winner is not None:
            self.started = False; self.round_winner = None; self.match_winner = None; self.ready.clear(); self._touch(); return True
        return False

    def update(self, now):
        self.now = int(now)
        if not self.started:
            return
        if self.match_winner is not None:
            return
        if self.round_winner is None:
            due = [(deadline, seat) for seat, deadline in self.npc_deadlines.items()]
            if due:
                deadline, seat = min(due)
                if now >= deadline:
                    self._win_round(seat)
            return
        human_seats = {seat for identity, seat in self.humans.items() if identity in self.connections}
        needed = human_seats | {i for i, row in enumerate(self.seat_data) if row["kind"] == "NPC"}
        if needed <= self.ready:
            self._start_round(now)

    def view(self, identity):
        if not self.started:
            return self.lobby_view(identity)
        data = self._base_view(identity)
        data.update({
            "type": "party_state",
            "phase": "match_result" if self.match_winner is not None else "round_result" if self.round_winner is not None else "round",
            "difficulty": self.difficulty,
            "numbers": list(self.numbers),
            "suits": list(self.suits),
            "scores": list(self.scores),
            "round_number": self.round_number,
            "round_winner": self.round_winner,
            "match_winner": self.match_winner,
            "ready_seats": sorted(self.ready),
            "target_score": 3,
        })
        return data


class BlindBluffAuthority(FourSeatAuthority):
    mode = "blind_mans_bluff"
    title = "Blind Man's Bluff"

    def __init__(self, host_name, rng=None):
        super().__init__(host_name, rng)
        self.starting_stack = 5000
        self.ante = 40
        self.bet_unit = 100
        self.hand_number = 0
        self.cards = [None] * 4
        self.folded = [True] * 4
        self.stacks = [0] * 4
        self.round_bets = [0] * 4
        self.contributions = [0] * 4
        self.actions = [""] * 4
        self.current_bet = 0
        self.last_raise = 1
        self.current_actor = None
        self.pending = set()
        self.raise_rights = set()
        self.hand_complete = False
        self.winners = []
        self.result_text = ""
        self.result_until = 0
        self.npc_due = 0
        self.opening_cursor = -1

    def lobby_view(self, identity):
        data = super().lobby_view(identity)
        data.update({"starting_stack": self.starting_stack})
        return data

    def _participants(self):
        return [i for i, row in enumerate(self.seat_data) if row["kind"] in ("Human", "NPC")]

    def start(self, now=0):
        if self.started or self._active_lobby_count() < 2:
            return False
        self.started = True
        self.stacks = [self.starting_stack if row["kind"] in ("Human", "NPC") else 0 for row in self.seat_data]
        for i, row in enumerate(self.seat_data):
            row["stack"] = self.stacks[i]
            row["spectator"] = False
        self.ante = round_chip_amount(self.starting_stack * 0.008, minimum=5)
        self.bet_unit = round_chip_amount(self.starting_stack * 0.02, minimum=10)
        self.opening_cursor = -1
        self._start_hand(now)
        return True

    def _commit(self, seat, amount):
        paid = min(max(0, int(amount)), self.stacks[seat])
        self.stacks[seat] -= paid
        self.round_bets[seat] += paid
        self.contributions[seat] += paid
        self.seat_data[seat]["stack"] = self.stacks[seat]
        return paid

    def _start_hand(self, now):
        eligible = [seat for seat in self._participants() if self.stacks[seat] >= self.ante]
        for seat in self._participants():
            self.seat_data[seat]["spectator"] = seat not in eligible
        if len(eligible) < 2:
            self.hand_complete = True
            self.current_actor = None
            self.result_text = "Not enough funded seats remain. Broke players are spectating."
            self._touch(self.result_text)
            return False
        self.hand_number += 1
        deck = build_standard_deck(self.rng)
        self.cards = [None] * 4
        self.folded = [True] * 4
        self.round_bets = [0] * 4
        self.contributions = [0] * 4
        self.actions = [""] * 4
        self.current_bet = 0
        self.last_raise = max(self.ante, round_chip_amount(self.starting_stack * .01, minimum=5))
        self.pending = set()
        self.raise_rights = set()
        self.hand_complete = False
        self.winners = []
        self.result_text = "See every forehead card except your own."
        for seat in eligible:
            self.folded[seat] = False
            paid = min(self.ante, self.stacks[seat])
            self.stacks[seat] -= paid
            self.contributions[seat] += paid
            self.seat_data[seat]["stack"] = self.stacks[seat]
            self.cards[seat] = deck.pop()
            if self.stacks[seat] > 0:
                self.pending.add(seat); self.raise_rights.add(seat)
        live_order = eligible
        self.opening_cursor = (self.opening_cursor + 1) % len(live_order)
        self.current_actor = live_order[self.opening_cursor]
        self.npc_due = 0
        self._advance(now, inclusive=True)
        self._touch()
        return True

    def _active(self):
        return [i for i in self._participants() if not self.folded[i] and self.cards[i] is not None]

    def _can_raise(self, seat):
        return seat in self.raise_rights and self.stacks[seat] + self.round_bets[seat] > self.current_bet

    def _min_raise_to(self):
        return self.current_bet + self.last_raise if self.current_bet else self.bet_unit

    def _award_single(self, seat, now):
        total = sum(self.contributions)
        self.stacks[seat] += total
        self.seat_data[seat]["stack"] = self.stacks[seat]
        self.winners = [seat]
        self.result_text = f"{self.seat_data[seat]['name']} wins ${total:,}; everyone else folded."
        self.hand_complete = True; self.current_actor = None; self.result_until = now + 5500
        self._touch(self.result_text)

    def _showdown(self, now):
        levels = sorted({amount for amount in self.contributions if amount > 0})
        previous = 0
        winners_any = set()
        for level in levels:
            contributors = [i for i, amount in enumerate(self.contributions) if amount >= level]
            eligible = [i for i in contributors if not self.folded[i] and self.cards[i] is not None]
            amount = (level - previous) * len(contributors)
            previous = level
            if not eligible or amount <= 0:
                continue
            best = max(RANK_VALUES[self.cards[i]["rank"]] for i in eligible)
            winners = [i for i in eligible if RANK_VALUES[self.cards[i]["rank"]] == best]
            share, remainder = divmod(amount, len(winners))
            for j, seat in enumerate(winners):
                self.stacks[seat] += share + (1 if j < remainder else 0)
                self.seat_data[seat]["stack"] = self.stacks[seat]
                winners_any.add(seat)
        self.winners = sorted(winners_any)
        names = ", ".join(self.seat_data[i]["name"] for i in self.winners) or "Nobody"
        self.result_text = f"{names} {'split the pot' if len(self.winners)>1 else 'wins the pot'}."
        self.hand_complete = True; self.current_actor = None; self.result_until = now + 5500
        self._touch(self.result_text)

    def _hidden_strength(self, seat):
        visible = [self.cards[i] for i in self._active() if i != seat and self.cards[i] is not None]
        if not visible:
            return .5
        maximum = max(RANK_VALUES[c["rank"]] for c in visible)
        # Approximate the chance the hidden rank is competitive. Skill controls
        # how closely the NPC trusts this estimate rather than changing cards.
        beat = sum(1 for rank in RANK_VALUES.values() if rank > maximum)
        tie = 1 if maximum in RANK_VALUES.values() else 0
        return max(.02, min(.98, (beat + .5 * tie) / 13.0))

    def _npc_action(self, seat, now):
        skill = self.seat_data[seat].get("skill", "mid")
        accuracy = {"low": .45, "mid": .62, "strong": .78, "elite": .92}.get(skill, .62)
        rational = self._hidden_strength(seat)
        strength = rational * accuracy + self.rng.random() * (1.0 - accuracy)
        due = max(0, self.current_bet - self.round_bets[seat])
        pot = max(1, sum(self.contributions))
        pressure = due / max(1, pot + due)
        if due:
            if strength + .08 < pressure and self.rng.random() < .82:
                return self._act_seat(seat, "fold", 0, now)
            if strength > .72 and self._can_raise(seat) and self.rng.random() < .42:
                target = min(self.round_bets[seat] + self.stacks[seat], max(self._min_raise_to(), self.current_bet + self.bet_unit * 2))
                return self._act_seat(seat, "bet_raise", target, now)
            return self._act_seat(seat, "check_call", 0, now)
        if strength > .58 and self._can_raise(seat) and self.rng.random() < (.30 + .35 * strength):
            target = min(self.stacks[seat], self.bet_unit * (2 if strength > .78 else 1))
            return self._act_seat(seat, "bet_raise", max(self.bet_unit, target), now)
        return self._act_seat(seat, "check_call", 0, now)

    def _act_seat(self, seat, action, amount, now):
        if self.hand_complete or seat not in self.pending or seat != self.current_actor:
            return False
        due = max(0, self.current_bet - self.round_bets[seat])
        if action == "fold":
            self.folded[seat] = True; self.actions[seat] = "Folded"
        elif action == "check_call":
            if due:
                paid = self._commit(seat, due); self.actions[seat] = f"Called ${paid:,}"
            else:
                self.actions[seat] = "Checked"
        elif action == "bet_raise":
            if not self._can_raise(seat):
                return False
            maximum = self.round_bets[seat] + self.stacks[seat]
            minimum = self._min_raise_to()
            target = _clamp_int(amount, minimum, maximum, minimum)
            if target <= self.current_bet:
                return False
            increase = target - self.current_bet
            self._commit(seat, target - self.round_bets[seat])
            self.actions[seat] = f"{'Bet' if self.current_bet == 0 else 'Raised to'} ${target:,}"
            full = increase >= self.last_raise
            self.current_bet = target
            if full:
                self.last_raise = increase
                self.raise_rights = {i for i in self._active() if self.stacks[i] > 0}
                self.pending = set(self.raise_rights)
            else:
                self.pending.update(i for i in self._active() if self.stacks[i] > 0 and self.round_bets[i] < target)
        else:
            return False
        self.pending.discard(seat); self.raise_rights.discard(seat)
        self._touch()
        self._advance(now, inclusive=False)
        return True

    def _advance(self, now, inclusive=False):
        active = self._active()
        if len(active) == 1:
            self._award_single(active[0], now); return
        self.pending.intersection_update(i for i in active if self.stacks[i] > 0)
        if not self.pending:
            self._showdown(now); return
        start = self.current_actor if inclusive and self.current_actor is not None else ((self.current_actor or 0) + 1) % 4
        for offset in range(4):
            seat = (start + offset) % 4
            if seat in self.pending:
                self.current_actor = seat
                self.npc_due = now + self.rng.randint(550, 1150) if self.seat_data[seat]["kind"] == "NPC" else 0
                return

    def act(self, identity, action, amount=0, revision=None):
        if identity not in self.connections or revision != self.revision:
            return False
        if not self.started:
            if action == "stack" and identity == 0 and amount in STACK_OPTIONS:
                self.starting_stack = int(amount); self._touch(); return True
            if action == "start" and identity == 0:
                return self.start(self.now)
            return self.act_lobby(identity, action, amount)
        seat = self.humans.get(identity)
        if seat is None or self.seat_data[seat].get("spectator"):
            return False
        return self._act_seat(seat, action, amount, self.now)

    def update(self, now):
        self.now = int(now)
        if not self.started:
            return
        if self.hand_complete:
            if self.result_until and now >= self.result_until:
                self._start_hand(now)
            return
        if self.current_actor is not None and self.seat_data[self.current_actor]["kind"] == "NPC" and now >= self.npc_due:
            self._npc_action(self.current_actor, now)

    def view(self, identity):
        if not self.started:
            return self.lobby_view(identity)
        data = self._base_view(identity)
        viewer = self.humans.get(identity)
        spectator = viewer is None or self.seat_data[viewer].get("spectator", False)
        cards = []
        for seat, card in enumerate(self.cards):
            cards.append(copy.deepcopy(card) if spectator or seat != viewer else None)
        data.update({
            "type": "party_state", "phase": "result" if self.hand_complete else "betting",
            "starting_stack": self.starting_stack, "ante": self.ante, "bet_unit": self.bet_unit,
            "hand_number": self.hand_number, "cards": cards, "folded": list(self.folded),
            "stacks": list(self.stacks), "round_bets": list(self.round_bets), "actions": list(self.actions),
            "pot": sum(self.contributions), "current_bet": self.current_bet,
            "current_actor": self.current_actor, "winners": list(self.winners), "result_text": self.result_text,
            "spectating": spectator, "minimum_raise_to": self._min_raise_to(),
        })
        return data


class RouletteAuthority(FourSeatAuthority):
    mode = "roulette"
    title = "Roulette"

    def __init__(self, host_name, rng=None):
        super().__init__(host_name, rng)
        self.starting_stack = 5000
        self.bet_seconds = 25
        self.stacks = [0] * 4
        self.bets = [[] for _ in range(4)]
        self.phase = "lobby"
        self.deadline = 0
        self.result = None
        self.round_number = 0
        self.last_net = [0] * 4
        self.last_countdown = None

    def lobby_view(self, identity):
        data = super().lobby_view(identity)
        data.update({"starting_stack": self.starting_stack, "bet_seconds": self.bet_seconds})
        return data

    def _participants(self):
        return [i for i, row in enumerate(self.seat_data) if row["kind"] in ("Human", "NPC")]

    def start(self, now=0):
        if self.started or self._active_lobby_count() < 2:
            return False
        self.started = True
        self.stacks = [self.starting_stack if row["kind"] in ("Human", "NPC") else 0 for row in self.seat_data]
        for i, row in enumerate(self.seat_data): row["stack"] = self.stacks[i]; row["spectator"] = False
        self.round_number = 0
        self._new_betting(now)
        return True

    def _new_betting(self, now):
        self.round_number += 1
        self.phase = "betting"; self.deadline = now + self.bet_seconds * 1000
        self.result = None; self.bets = [[] for _ in range(4)]; self.last_net = [0] * 4
        self.last_countdown = self.bet_seconds
        for seat in self._participants():
            broke = self.stacks[seat] <= 0
            self.seat_data[seat]["spectator"] = broke
            self.seat_data[seat]["action"] = "Spectating" if broke else "Betting"
            self.seat_data[seat]["stack"] = self.stacks[seat]
        self._npc_bets()
        self._touch()

    def _npc_bets(self):
        choices = [
            ("color", "red"), ("color", "black"), ("parity", "odd"), ("parity", "even"),
            ("range", "low"), ("range", "high"), ("dozen", 1), ("dozen", 2), ("dozen", 3),
        ]
        for seat in self._participants():
            if self.seat_data[seat]["kind"] != "NPC" or self.stacks[seat] <= 0:
                continue
            count = self.rng.randint(1, 3)
            for _ in range(count):
                bet_type, value = self.rng.choice(choices)
                if self.rng.random() < .20:
                    bet_type, value = "number", self.rng.choice(ROULETTE_NUMBERS)
                amount = min(self.stacks[seat], max(10, round_chip_amount(self.starting_stack * self.rng.uniform(.01, .04), minimum=10)))
                self._place_bet(seat, bet_type, value, amount)

    def _place_bet(self, seat, bet_type, value, amount):
        if self.phase != "betting" or self.stacks[seat] <= 0:
            return False
        amount = _clamp_int(amount, 1, self.stacks[seat], 0)
        if amount <= 0:
            return False
        valid = False
        if bet_type == "number": valid = str(value) in ROULETTE_NUMBERS; value = str(value)
        elif bet_type == "color": valid = value in ("red", "black")
        elif bet_type == "parity": valid = value in ("odd", "even")
        elif bet_type == "range": valid = value in ("low", "high")
        elif bet_type in ("dozen", "column"): valid = value in (1, 2, 3)
        if not valid:
            return False
        self.stacks[seat] -= amount
        self.seat_data[seat]["stack"] = self.stacks[seat]
        for bet in self.bets[seat]:
            if bet["type"] == bet_type and bet["value"] == value:
                bet["amount"] += amount; return True
        self.bets[seat].append({"type": bet_type, "value": value, "amount": amount})
        return True

    def _is_winner(self, bet):
        if self.result is None:
            return False
        t, value = bet["type"], bet["value"]
        if t == "number": return self.result == str(value)
        if self.result in ("0", "00"): return False
        number = int(self.result)
        color = "red" if number in RED_NUMBERS else "black"
        if t == "color": return color == value
        if t == "parity": return (number % 2 == 1) == (value == "odd")
        if t == "range": return (1 <= number <= 18) if value == "low" else (19 <= number <= 36)
        if t == "dozen": return (value - 1) * 12 + 1 <= number <= value * 12
        if t == "column": return number % 3 == value % 3
        return False

    def _settle(self):
        for seat in self._participants():
            wager = sum(b["amount"] for b in self.bets[seat])
            payout = 0
            for bet in self.bets[seat]:
                if not self._is_winner(bet): continue
                multiplier = 36 if bet["type"] == "number" else 3 if bet["type"] in ("dozen", "column") else 2
                payout += bet["amount"] * multiplier
            self.stacks[seat] += payout
            self.last_net[seat] = payout - wager
            self.seat_data[seat]["stack"] = self.stacks[seat]
            if self.stacks[seat] <= 0:
                self.seat_data[seat]["spectator"] = True; self.seat_data[seat]["action"] = "Broke • Spectating"
            else:
                self.seat_data[seat]["action"] = f"{self.last_net[seat]:+d}"

    def act(self, identity, action, amount=0, revision=None):
        if identity not in self.connections or revision != self.revision:
            return False
        if not self.started:
            if action == "stack" and identity == 0 and amount in STACK_OPTIONS:
                self.starting_stack = int(amount); self._touch(); return True
            if action == "timer" and identity == 0 and amount in ROULETTE_TIMERS:
                self.bet_seconds = int(amount); self._touch(); return True
            if action == "start" and identity == 0:
                return self.start(self.now)
            return self.act_lobby(identity, action, amount)
        seat = self.humans.get(identity)
        if seat is None or self.seat_data[seat].get("spectator"):
            return False
        if action == "bet" and isinstance(amount, dict):
            ok = self._place_bet(seat, amount.get("type"), amount.get("value"), amount.get("amount", 0))
            if ok: self._touch()
            return ok
        if action == "clear_bets" and self.phase == "betting":
            refund = sum(b["amount"] for b in self.bets[seat])
            if refund <= 0: return False
            self.stacks[seat] += refund; self.bets[seat] = []; self.seat_data[seat]["stack"] = self.stacks[seat]; self._touch(); return True
        return False

    def update(self, now):
        self.now = int(now)
        if not self.started:
            return
        if self.phase == "betting":
            seconds = max(0, math.ceil((self.deadline - now) / 1000))
            if seconds != self.last_countdown:
                self.last_countdown = seconds; self.revision += 1
            if now >= self.deadline:
                self.phase = "spinning"; self.result = self.rng.choice(ROULETTE_NUMBERS); self.deadline = now + 4500; self._touch()
        elif self.phase == "spinning" and now >= self.deadline:
            self._settle(); self.phase = "result"; self.deadline = now + 5500; self._touch()
        elif self.phase == "result" and now >= self.deadline:
            if any(self.stacks[seat] > 0 for seat in self._participants()): self._new_betting(now)
            else:
                self.phase = "finished"; self._touch("Everyone is broke. The table is finished.")

    def view(self, identity):
        if not self.started:
            return self.lobby_view(identity)
        data = self._base_view(identity)
        viewer = self.humans.get(identity)
        data.update({
            "type": "party_state", "phase": self.phase, "starting_stack": self.starting_stack,
            "bet_seconds": self.bet_seconds, "seconds_left": max(0, math.ceil((self.deadline) / 1000)) if False else self.last_countdown,
            "round_number": self.round_number, "stacks": list(self.stacks), "result": self.result,
            "last_net": list(self.last_net), "bets": copy.deepcopy(self.bets[viewer]) if viewer is not None else [],
            "all_bets": copy.deepcopy(self.bets),
            "spectating": viewer is None or self.seat_data[viewer].get("spectator", False),
        })
        return data


def make_party_authority(mode, host_name):
    if mode == "score_four": return ScoreFourAuthority(host_name)
    if mode == "blind_mans_bluff": return BlindBluffAuthority(host_name)
    if mode == "roulette": return RouletteAuthority(host_name)
    raise ValueError("Unsupported multiplayer mode: " + str(mode))
