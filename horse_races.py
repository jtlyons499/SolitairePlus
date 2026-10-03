import json
import math
import random
from pathlib import Path


HORSE_FILE = Path(__file__).parent / "data" / "horses.json"
BET_TYPES = ("win", "place", "show")
CHIP_VALUES = (10, 50, 100, 500)
FIELD_SIZE = 6
PHOTO_FINISH_SECONDS = 0.12


def _clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def load_horse_roster():
    try:
        with HORSE_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        data = []

    roster = []
    for index, horse in enumerate(data):
        if not isinstance(horse, dict):
            continue
        horse_id = str(horse.get("id") or f"horse_{index + 1}")
        name = str(horse.get("name") or horse_id.replace("_", " ").title())
        try:
            quality = float(horse.get("quality", 0.65))
        except (TypeError, ValueError):
            quality = 0.65
        style = str(horse.get("style", "steady")).strip().lower()
        if style not in {"steady", "front_runner", "closer", "streaky"}:
            style = "steady"
        roster.append({
            "id": horse_id,
            "name": name,
            "quality": _clamp(quality, 0.35, 0.98),
            "style": style,
        })

    if len(roster) < FIELD_SIZE:
        raise ValueError("Horse Races requires at least six horses in data/horses.json.")
    return roster


class HorseRaceGame:
    """Casino-night horse racing with deterministic frame-independent animation.

    Odds are derived from each horse's public pre-race strength. The actual race
    adds hidden performance variance, so favorites deserve their prices without
    becoming guaranteed winners.
    """

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.roster = load_horse_roster()
        self.reset_session()

    def reset_session(self):
        self.starting_cash = 0
        self.bankroll = 0
        self.session_wagered = 0
        self.session_payout = 0
        self.races_completed = 0
        self.races_with_profit = 0
        self.reward_claimed = False
        self.current_field = []
        self.tickets = []
        self.stage = "idle"
        self.positions = [0.0] * FIELD_SIZE
        self.finish_times = [None] * FIELD_SIZE
        self.result_order = []
        self.race_started_ms = 0
        self.last_update_ms = 0
        self.race_payout = 0
        self.race_wagered = 0
        self.race_net = 0
        self.race_message = ""
        self.photo_finish = False
        self.selected_horse_index = 0
        self.selected_bet_type = "win"
        self.selected_chip_value = 10

    def start_session(self, starting_cash):
        self.reset_session()
        self.starting_cash = max(0, int(starting_cash or 0))
        self.bankroll = self.starting_cash
        self.stage = "betting"
        self.prepare_next_race()
        return True

    def _build_field_strengths(self, selected):
        raw_scores = []
        prepared = []
        for lane, source in enumerate(selected):
            horse = dict(source)
            form = self.rng.uniform(-0.08, 0.08)
            public_strength = _clamp(horse["quality"] + form, 0.28, 1.02)
            horse["lane"] = lane + 1
            horse["form"] = form
            horse["public_strength"] = public_strength
            raw = math.exp(public_strength * 3.2)
            raw_scores.append(raw)
            prepared.append(horse)

        total = max(1e-9, sum(raw_scores))
        probabilities = [value / total for value in raw_scores]

        for horse, probability in zip(prepared, probabilities):
            # 10% house margin. Odds are profit odds: 3.0 means win $3 profit
            # for every $1 wagered, plus the original stake back.
            win_odds = max(0.55, (0.90 / max(0.02, probability)) - 1.0)
            win_odds = round(min(12.0, win_odds), 2)
            horse["win_probability"] = probability
            horse["win_odds"] = win_odds
            horse["place_odds"] = round(max(0.25, win_odds * 0.46), 2)
            horse["show_odds"] = round(max(0.15, win_odds * 0.28), 2)

            # Hidden race-day variance determines the actual running time.
            performance = _clamp(
                horse["public_strength"] + self.rng.gauss(0.0, 0.105),
                0.18,
                1.12,
            )
            base_duration = 14.3 - performance * 4.75
            horse["finish_duration"] = max(
                7.4,
                base_duration + self.rng.uniform(-0.60, 0.60),
            )
            horse["phase"] = self.rng.uniform(0.0, math.tau)

        return prepared

    def prepare_next_race(self):
        if self.stage == "racing":
            return False
        selected = self.rng.sample(self.roster, FIELD_SIZE)
        self.current_field = self._build_field_strengths(selected)
        self.tickets = []
        self.positions = [0.0] * FIELD_SIZE
        self.finish_times = [None] * FIELD_SIZE
        self.result_order = []
        self.race_started_ms = 0
        self.last_update_ms = 0
        self.race_payout = 0
        self.race_wagered = 0
        self.race_net = 0
        self.race_message = "Choose a horse, bet type, and chip value."
        self.photo_finish = False
        self.selected_horse_index = 0
        self.selected_bet_type = "win"
        if self.selected_chip_value not in CHIP_VALUES:
            self.selected_chip_value = 10
        self.stage = "betting"
        return True

    def get_selected_horse(self):
        if 0 <= self.selected_horse_index < len(self.current_field):
            return self.current_field[self.selected_horse_index]
        return None

    def set_selected_horse(self, horse_index):
        if self.stage != "betting":
            return False
        try:
            horse_index = int(horse_index)
        except (TypeError, ValueError):
            return False
        if not 0 <= horse_index < len(self.current_field):
            return False
        self.selected_horse_index = horse_index
        return True

    def set_bet_type(self, bet_type):
        bet_type = str(bet_type or "").strip().lower()
        if self.stage != "betting" or bet_type not in BET_TYPES:
            return False
        self.selected_bet_type = bet_type
        return True

    def set_chip_value(self, amount):
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            return False
        if amount not in CHIP_VALUES:
            return False
        self.selected_chip_value = amount
        return True

    def _get_odds_for(self, horse, bet_type):
        return float(horse.get(f"{bet_type}_odds", 0.0) or 0.0)

    def place_selected_bet(self):
        if self.stage != "betting":
            return False
        horse = self.get_selected_horse()
        if horse is None:
            return False
        amount = int(self.selected_chip_value)
        if amount <= 0 or self.bankroll < amount:
            self.race_message = "Not enough bankroll for that chip."
            return False

        odds = self._get_odds_for(horse, self.selected_bet_type)
        self.bankroll -= amount
        self.race_wagered += amount
        self.session_wagered += amount

        # Merge identical tickets so the ticket panel stays readable.
        for ticket in self.tickets:
            if (
                ticket["horse_id"] == horse["id"]
                and ticket["bet_type"] == self.selected_bet_type
                and abs(ticket["odds"] - odds) < 1e-9
            ):
                ticket["stake"] += amount
                self.race_message = (
                    f"Added ${amount:,} to {horse['name']} "
                    f"{self.selected_bet_type.upper()}."
                )
                return True

        self.tickets.append({
            "horse_id": horse["id"],
            "horse_name": horse["name"],
            "lane": horse["lane"],
            "bet_type": self.selected_bet_type,
            "stake": amount,
            "odds": odds,
        })
        self.race_message = (
            f"Bet ${amount:,} on {horse['name']} "
            f"to {self.selected_bet_type.upper()}."
        )
        return True

    def clear_bets(self):
        if self.stage != "betting" or not self.tickets:
            return False
        refund = sum(ticket["stake"] for ticket in self.tickets)
        self.bankroll += refund
        self.race_wagered = 0
        self.session_wagered = max(0, self.session_wagered - refund)
        self.tickets = []
        self.race_message = f"Returned ${refund:,} in unstarted wagers."
        return True

    def start_race(self, now_ms):
        if self.stage != "betting" or not self.tickets:
            if self.stage == "betting":
                self.race_message = "Place at least one bet before starting the race."
            return False
        self.stage = "racing"
        self.race_started_ms = int(now_ms)
        self.last_update_ms = int(now_ms)
        self.positions = [0.0] * FIELD_SIZE
        self.finish_times = [None] * FIELD_SIZE
        self.result_order = []
        self.race_message = "And they're off!"
        return True

    @staticmethod
    def _style_progress(style, u, phase=0.0):
        u = _clamp(u)
        if style == "front_runner":
            value = u ** 0.84
        elif style == "closer":
            value = u ** 1.17
        elif style == "streaky":
            wobble = math.sin(u * math.tau * 2.2 + phase) * 0.020 * (1.0 - u)
            value = u + wobble
        else:
            value = u
        return _clamp(value)

    def update(self, now_ms):
        if self.stage != "racing":
            return False

        elapsed = max(0.0, (int(now_ms) - self.race_started_ms) / 1000.0)
        changed = False

        for index, horse in enumerate(self.current_field):
            duration = max(0.1, float(horse["finish_duration"]))
            raw_u = elapsed / duration
            position = self._style_progress(
                horse.get("style", "steady"),
                raw_u,
                float(horse.get("phase", 0.0)),
            )
            position = max(self.positions[index], position)
            if position != self.positions[index]:
                self.positions[index] = position
                changed = True

            if raw_u >= 1.0 and self.finish_times[index] is None:
                self.positions[index] = 1.0
                self.finish_times[index] = duration
                changed = True

        if all(value is not None for value in self.finish_times):
            self._finish_race()
            changed = True

        self.last_update_ms = int(now_ms)
        return changed

    def _finish_race(self):
        self.result_order = sorted(
            range(len(self.current_field)),
            key=lambda index: self.finish_times[index],
        )
        winner_index = self.result_order[0]
        winner = self.current_field[winner_index]
        self.photo_finish = (
            len(self.result_order) >= 2
            and abs(
                self.finish_times[self.result_order[0]]
                - self.finish_times[self.result_order[1]]
            ) <= PHOTO_FINISH_SECONDS
        )

        finish_rank = {
            horse_index: place + 1
            for place, horse_index in enumerate(self.result_order)
        }
        payout = 0
        winning_tickets = 0

        for ticket in self.tickets:
            horse_index = next(
                (
                    index for index, horse in enumerate(self.current_field)
                    if horse["id"] == ticket["horse_id"]
                ),
                None,
            )
            if horse_index is None:
                continue
            place = finish_rank[horse_index]
            bet_type = ticket["bet_type"]
            qualifies = (
                (bet_type == "win" and place == 1)
                or (bet_type == "place" and place <= 2)
                or (bet_type == "show" and place <= 3)
            )
            if not qualifies:
                continue
            stake = int(ticket["stake"])
            profit = int(round(stake * float(ticket["odds"])))
            ticket_return = stake + profit
            payout += ticket_return
            winning_tickets += 1
            ticket["won"] = True
            ticket["return"] = ticket_return
        for ticket in self.tickets:
            ticket.setdefault("won", False)
            ticket.setdefault("return", 0)

        self.bankroll += payout
        self.race_payout = payout
        self.session_payout += payout
        self.race_net = payout - self.race_wagered
        self.races_completed += 1
        if self.race_net > 0:
            self.races_with_profit += 1
        self.stage = "results"

        if self.photo_finish:
            runner_up = self.current_field[self.result_order[1]]
            self.race_message = (
                f"PHOTO FINISH! {winner['name']} edges {runner_up['name']}."
            )
        else:
            self.race_message = f"{winner['name']} wins the race."
        if winning_tickets:
            self.race_message += f" Payout: ${payout:,}."
        else:
            self.race_message += " No winning tickets."

    def get_session_net(self):
        return int(self.bankroll - self.starting_cash)

    def get_result_rows(self):
        rows = []
        for place, horse_index in enumerate(self.result_order, start=1):
            horse = self.current_field[horse_index]
            rows.append({
                "place": place,
                "lane": horse["lane"],
                "name": horse["name"],
                "time": self.finish_times[horse_index],
            })
        return rows

    def can_start_race(self):
        return self.stage == "betting" and bool(self.tickets)

    def can_next_race(self):
        return self.stage == "results"

    def cash_out(self):
        if self.stage == "betting" and self.tickets:
            self.clear_bets()
        return int(self.bankroll)
