"""Cryptid Creatures: data-driven cards and a UI-independent practice battle.

One active creature, three Docket slots, regenerating Focus, one creature move
per turn, and three knockouts to win. Hidden hands never feed opponent AI.
"""
from collections import Counter, deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
import json
import random


ROOT = Path(__file__).resolve().parent
STYLES = ("Slam", "Slash", "Air", "Ethereal", "Elemental", "Corruption", "Munition")
ARMORS = ("Scales", "Leather", "Steel", "Fur", "Bare", "Bone")
ERAS = ("Grene", "Thede", "Polis")
DEFENSES = {
    "Brute": ({"Slam", "Slash", "Munition", "Elemental"}, {"Ethereal", "Corruption"}),
    "Evasion": ({"Slam", "Air", "Munition"}, {"Slash", "Elemental"}),
    "Shield": ({"Slam", "Slash", "Elemental"}, {"Air", "Ethereal", "Corruption"}),
    "Mystic": ({"Ethereal", "Elemental", "Corruption"}, {"Munition", "Slam", "Slash"}),
}
NEGATIVE_CONDITIONS = frozenset(("sick", "spent", "stunned"))
CONDITIONS = NEGATIVE_CONDITIONS | {"steeled", "sharpened"}
EFFECTS = {"heal_hp", "heal_ap", "barrier_ap", "rearm", "cleanse", "condition",
           "duration", "guard", "guard_ap", "guard_hp", "reflect", "arena"}
HAND_LIMIT = 10
MAX_FOCUS = 6


class CryptidCatalog:
    def __init__(self, path=None):
        path = Path(path) if path else ROOT / "data" / "cryptid_creatures.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.cards, self.moves, self.decks = data["cards"], data["moves"], data["decks"]
        self.validate()

    def validate(self):
        for key, move in self.moves.items():
            if key != move["id"] or move["kind"] not in ("attack", "guard", "repair", "arena"):
                raise ValueError(f"Invalid move: {key}")
            if not 0 <= move["focus"] <= MAX_FOCUS or (move["uses"] is not None and move["uses"] < 1):
                raise ValueError(f"Invalid costs/uses: {key}")
            if move["kind"] == "attack":
                if move["style"] not in STYLES or min(move["ap_damage"], move["hp_damage"]) < 0:
                    raise ValueError(f"Invalid attack: {key}")
                if move.get("condition") and move["condition"] not in CONDITIONS:
                    raise ValueError(f"Invalid condition: {key}")
                if not 0 <= move.get("condition_chance", 0) <= 1:
                    raise ValueError(f"Invalid condition chance: {key}")
            self._validate_effects(move.get("effects", {}), key)
        for key, card in self.cards.items():
            if key != card["id"] or Path(card["art"]).name != card["art"]:
                raise ValueError(f"Invalid card identity/art path: {key}")
            if card["kind"] == "creature":
                if (not 1 <= card["hp"] <= 100 or not 0 <= card["ap"] <= 150
                        or card["era"] not in ERAS or card["armor"] not in ARMORS
                        or card["attack_style"] not in STYLES or card["defense_style"] not in DEFENSES
                        or not 1 <= len(card["moves"]) <= 4
                        or any(m not in self.moves for m in card["moves"])):
                    raise ValueError(f"Invalid creature: {key}")
            elif card["kind"] in ("support", "arena"):
                if not 0 <= card["focus"] <= MAX_FOCUS or card["target"] not in ("friendly", "bench", "arena"):
                    raise ValueError(f"Invalid support: {key}")
                self._validate_effects(card["effects"], key)
            else:
                raise ValueError(f"Unknown card kind: {key}")
        for key, deck in self.decks.items():
            counts = Counter(deck["cards"])
            if (len(deck["cards"]) != 30 or max(counts.values()) > 2
                    or any(c not in self.cards for c in counts)
                    or sum(self.cards[c]["kind"] == "creature" for c in deck["cards"]) != 8):
                raise ValueError(f"Invalid starter deck: {key}")

    @staticmethod
    def _validate_effects(effects, key):
        if set(effects) - EFFECTS:
            raise ValueError(f"Unknown effect in {key}")
        if effects.get("condition") and effects["condition"] not in CONDITIONS:
            raise ValueError(f"Unknown condition in {key}")
        arena = effects.get("arena")
        if arena and (arena["scope"] not in ("all", "self", "enemy", "self_ap")
                      or arena["duration"] < 1
                      or any(s not in (*STYLES, "*") for s in arena["styles"])):
            raise ValueError(f"Invalid arena in {key}")


@dataclass
class Creature:
    card_id: str
    uid: int
    hp: int
    ap: int
    uses: dict
    conditions: dict = field(default_factory=dict)
    guard: dict = field(default_factory=dict)


@dataclass
class Side:
    deck: list
    hand: list = field(default_factory=list)
    discard: list = field(default_factory=list)
    active: Creature | None = None
    docket: list = field(default_factory=list)
    focus: int = 0
    knockouts: int = 0
    move_used: bool = False
    switched: bool = False
    fatigue: int = 0

    def creatures(self):
        return ([self.active] if self.active else []) + self.docket


@dataclass(frozen=True)
class Action:
    kind: str
    index: int = -1
    target: int = 0


def matchup(style, defense):
    resistant, weak = DEFENSES[defense]
    return .5 if style in resistant else 2.0 if style in weak else 1.0


def damage_breakdown(move, attacker, defender, attacker_card, defender_card, arena=None, owner=0):
    """Pure prediction using only the two public creatures and current arena."""
    sharp = "sharpened" in attacker.conditions
    weak = "spent" in defender.conditions or sharp
    strong = "steeled" in defender.conditions
    factor = (1 if weak and strong else 2 if weak else .5 if strong
              else matchup(move["style"], defender_card["defense_style"]))
    reason = ("Opposing conditions cancel" if weak and strong else
              "Spent / Sharpened weakness" if weak else "Steeled resistance" if strong else
              f"{move['style']} vs {defender_card['defense_style']}")
    steps = [f"{reason}: x{factor:g}"]
    if move["style"] == attacker_card["attack_style"] and move["id"] != "struggle":
        factor *= 1.1
        steps.append("Native attack style: x1.1")
    if arena:
        style_matches = "*" in arena["styles"] or move["style"] in arena["styles"]
        applies = (arena["scope"] == "all"
                   or arena["scope"] in ("self", "self_ap") and arena["owner"] == owner
                   or arena["scope"] == "enemy" and arena["owner"] != owner)
        if style_matches and applies and (arena["scope"] != "self_ap" or defender.ap > 0):
            factor *= arena["factor"]
            steps.append(f"Arena: x{arena['factor']:g}")
    # Whole damage multiplier is capped; guards are applied separately below.
    capped = max(.25, min(2.0, factor))
    if capped != factor:
        steps.append(f"Combined multiplier capped: x{capped:g}")
    factor = capped
    armored = defender.ap > 0
    base = move["ap_damage"] if armored else move["hp_damage"]
    damage = max(0, int(base*factor + .5))
    steps.insert(0,f"{'Armor present: use AP' if armored else 'No armor: use HP'} {base}")
    steps.append(f"After multipliers: {base} x {factor:g} = {damage} (rounded)")
    if defender.guard:
        steps.append(f"Guard: x{defender.guard.get('guard',1):g}, subtract {defender.guard.get('guard_ap' if armored else 'guard_hp',0)}")
    damage = max(0, int(damage*defender.guard.get("guard", 1) + .5)
                 - defender.guard.get("guard_ap" if armored else "guard_hp", 0))
    ap_loss = min(defender.ap, damage) if armored else 0
    hp_loss = min(defender.hp, damage-ap_loss)
    steps.append(f"Actual loss: {ap_loss} AP + {hp_loss} HP (capped by remaining stats)")
    if defender.guard.get("reflect"):
        steps.append(f"Reflection: {ap_loss+hp_loss} direct HP back to attacker")
    return {"ap_loss":ap_loss,"hp_loss":hp_loss,"steps":steps,"name":move.get("name",move["id"])}


def damage_values(move, attacker, defender, attacker_card, defender_card, arena=None, owner=0):
    result = damage_breakdown(move,attacker,defender,attacker_card,defender_card,arena,owner)
    return result["ap_loss"],result["hp_loss"]


class CryptidBattle:
    def __init__(self, catalog=None, player_deck="frontier", npc_deck="mystic_garden", seed=None, player_cards=None):
        self.catalog = catalog or CryptidCatalog()
        self.rng = random.Random(seed)
        self.sides = [Side(list(self.catalog.decks[key]["cards"])) for key in (player_deck, npc_deck)]
        if player_cards is not None:
            from cryptid_collection import deck_errors
            errors=deck_errors(player_cards,cards=self.catalog)
            if errors:raise ValueError(' '.join(errors))
            self.sides[0].deck=list(player_cards)
        self.turn = 0
        self.turn_number = 0
        self.winner = None  # 0 human, 1 NPC, 2 simultaneous draw.
        self.arena = None
        self.last_hit = None
        self.log = deque(maxlen=200)
        self._next_uid = 1
        for side in self.sides:
            self.rng.shuffle(side.deck)
            # Choose two random creatures from the shuffled deck for a reliable
            # opener. This is a setup rule for both seats, never an AI read.
            for _ in range(2):
                index = next(i for i, cid in enumerate(side.deck) if self.card(cid)["kind"] == "creature")
                side.hand.append(side.deck.pop(index))
            for _ in range(5):
                self._draw(side)
            cid = side.hand.pop(0)
            side.active = self.make_creature(cid)
            side.docket.append(self.make_creature(side.hand.pop(0)))
        self.log.append("First to three knockouts wins. Focus regenerates by two each turn.")
        self._begin_turn()

    def card(self, card_id):
        return self.catalog.cards[card_id]

    def make_creature(self, card_id):
        card = self.card(card_id)
        result = Creature(card_id, self._next_uid, card["hp"], card["ap"],
                          {mid: self.catalog.moves[mid]["uses"] for mid in card["moves"]})
        self._next_uid += 1
        return result

    def _draw(self, side):
        if side.deck:
            side.hand.append(side.deck.pop())
            return True
        return False

    def _name(self, seat):
        return "You" if seat == 0 else "Opponent"

    def _begin_turn(self):
        self.turn_number += 1
        side = self.sides[self.turn]
        side.focus = min(MAX_FOCUS, side.focus + 2)
        side.move_used = side.switched = False
        if self.turn_number > 1 and not self._draw(side):
            side.fatigue += 1
            if side.active:
                damage = 3*side.fatigue
                side.active.hp = max(0, side.active.hp-damage)
                self.log.append(f"{self._name(self.turn)} take {damage} fatigue HP damage.")
        if side.active:
            if "sick" in side.active.conditions:
                damage = 6+self.rng.randint(1, 6)
                side.active.hp = max(0, side.active.hp-damage)
                self.log.append(f"{self.card(side.active.card_id)['name']} loses {damage} HP to sickness.")
            if "stunned" in side.active.conditions:
                roll = self.rng.randint(1, 6)
                side.move_used = roll % 2 == 1
                side.active.conditions.pop("stunned")
                self.log.append(f"Stun recovery: rolled {roll}. " + ("Move skipped." if side.move_used else "Recovered."))
        self._resolve_knockouts()

    def _can_field(self, side):
        return bool(side.active or side.docket
                    or any(self.card(cid)["kind"] == "creature" for cid in side.hand))

    def _resolve_knockouts(self):
        # Resolve simultaneous effects together; neither seat wins by loop order.
        for seat, side in enumerate(self.sides):
            if side.active and side.active.hp <= 0:
                dead = side.active
                side.discard.append(dead.card_id)
                side.active = None
                self.sides[1-seat].knockouts += 1
                self.log.append(f"{self.card(dead.card_id)['name']} is knocked out.")
        wins = [self.sides[s].knockouts >= 3 or not self._can_field(self.sides[1-s]) for s in (0, 1)]
        if any(wins):
            self.winner = 2 if all(wins) else (0 if wins[0] else 1)
            self.log.append("Draw." if self.winner == 2 else f"{self._name(self.winner)} win the battle.")

    @staticmethod
    def _target(side, index):
        return side.active if index == 0 else side.docket[index-1]

    def legal_actions(self, seat=None):
        seat = self.turn if seat is None else seat
        if self.winner is not None or seat != self.turn:
            return []
        side = self.sides[seat]
        if not side.active:
            return ([Action("promote", i, 1) for i in range(len(side.docket))]
                    + [Action("promote", i, 0) for i, cid in enumerate(side.hand) if self.card(cid)["kind"] == "creature"])
        if len(side.hand) > HAND_LIMIT:
            return [Action("discard", i) for i in range(len(side.hand))]
        actions = [Action("end")]
        if not side.switched and side.focus >= 1:
            actions.extend(Action("switch", i) for i in range(len(side.docket)))
        for i, cid in enumerate(side.hand):
            card = self.card(cid)
            if card["kind"] == "creature":
                if len(side.docket) < 3 and side.focus >= 1:
                    actions.append(Action("play", i))
            elif side.focus >= card["focus"]:
                targets = (range(1, len(side.docket)+1) if card["target"] == "bench"
                           else range(len(side.docket)+1) if card["target"] == "friendly" else (0,))
                actions.extend(Action("play", i, target) for target in targets)
        if not side.move_used:
            ids = self.card(side.active.card_id)["moves"]
            for i, mid in enumerate(ids):
                move = self.catalog.moves[mid]
                uses = side.active.uses[mid]
                if (uses is None or uses > 0) and side.focus >= move["focus"]:
                    targets = range(1, len(side.docket)+1) if move.get("target") == "bench" else (0,)
                    actions.extend(Action("move", i, target) for target in targets)
            attacks = [mid for mid in ids if self.catalog.moves[mid]["kind"] == "attack"]
            if not any(side.active.uses[mid] is None or side.active.uses[mid] > 0 for mid in attacks):
                actions.append(Action("struggle"))
        return actions

    def _effects(self, seat, effects, target=0):
        side = self.sides[seat]
        if "arena" in effects:
            self.arena = dict(effects["arena"], owner=seat)
            return
        creature = self._target(side, target)
        card = self.card(creature.card_id)
        # A repair never reduces temporary armor that is already above maximum.
        creature.hp += min(effects.get("heal_hp", 0), max(0, card["hp"]-creature.hp))
        creature.ap += min(effects.get("heal_ap", 0), max(0, card["ap"]-creature.ap))
        if effects.get("barrier_ap"):
            creature.ap = min(card["ap"]+30, creature.ap+effects["barrier_ap"])
        if effects.get("rearm"):
            for mid, count in creature.uses.items():
                if count is not None:
                    creature.uses[mid] = min(self.catalog.moves[mid]["uses"], count+effects["rearm"])
        if effects.get("cleanse"):
            for condition in NEGATIVE_CONDITIONS:
                creature.conditions.pop(condition, None)
        if effects.get("condition"):
            condition = effects["condition"]
            creature.conditions[condition] = max(creature.conditions.get(condition, 0), effects.get("duration", 2))
        if any(key in effects for key in ("guard", "guard_ap", "guard_hp", "reflect")):
            creature.guard = {key: effects[key] for key in ("guard", "guard_ap", "guard_hp", "reflect") if key in effects}

    def _attack(self, seat, move):
        attacker, defender = self.sides[seat].active, self.sides[1-seat].active
        if defender is None:
            return
        self.last_hit = damage_breakdown(move, attacker, defender, self.card(attacker.card_id),
                                         self.card(defender.card_id), self.arena, seat)
        self.last_hit['seat'] = seat
        ap_loss, hp_loss = self.last_hit['ap_loss'], self.last_hit['hp_loss']
        reflect = defender.guard.get("reflect", False)
        defender.ap -= ap_loss
        defender.hp -= hp_loss
        defender.guard.clear()
        self.log.append(f"{move['name']}: {ap_loss} AP / {hp_loss} HP damage.")
        if reflect:
            # Reflect directly once: no type modifiers, armor rerouting or recursion.
            attacker.hp = max(0, attacker.hp-ap_loss-hp_loss)
            self.log.append(f"Redirect reflects {ap_loss+hp_loss} HP damage.")
        if move.get("condition") and defender.hp > 0 and self.rng.random() < move["condition_chance"]:
            condition = move["condition"]
            defender.conditions[condition] = max(defender.conditions.get(condition, 0), move.get("condition_duration", 2))
            self.log.append(f"{self.card(defender.card_id)['name']} becomes {condition.title()}.")
        recoil = move.get("self_damage")
        if recoil:
            armored = attacker.ap > 0
            amount = recoil["ap"] if armored else recoil["hp"]
            # Struggle recoil explicitly bypasses armor.
            if move["id"] == "struggle":
                armored, amount = False, 3
            lost_ap = min(attacker.ap, amount) if armored else 0
            attacker.ap -= lost_ap
            attacker.hp = max(0, attacker.hp-amount+lost_ap)
            self.log.append(f"Recoil: {lost_ap} AP / {amount-lost_ap} HP.")

    def act(self, action):
        if action not in self.legal_actions():
            return False
        seat, side = self.turn, self.sides[self.turn]
        if action.kind == "end":
            for creature in side.creatures():
                creature.conditions = {key: value-1 for key, value in creature.conditions.items() if value > 1}
            if self.arena:
                self.arena["duration"] -= 1
                if self.arena["duration"] <= 0:
                    self.arena = None
                    self.log.append("The arena effect expires.")
            self.turn = 1-seat
            self._begin_turn()
            return True
        if action.kind == "promote":
            side.active = (side.docket.pop(action.index) if action.target == 1
                           else self.make_creature(side.hand.pop(action.index)))
            self.log.append(f"{self._name(seat)} promote {self.card(side.active.card_id)['name']}.")
        elif action.kind == "discard":
            cid = side.hand.pop(action.index)
            side.discard.append(cid)
            self.log.append(f"{self._name(seat)} discard {self.card(cid)['name']} from a full hand.")
        elif action.kind == "switch":
            previous = side.active
            side.active = side.docket[action.index]
            side.docket[action.index] = previous
            side.focus -= 1
            side.switched = True
            self.log.append(f"{self._name(seat)} switch to {self.card(side.active.card_id)['name']}.")
        elif action.kind == "play":
            cid = side.hand.pop(action.index)
            card = self.card(cid)
            side.focus -= 1 if card["kind"] == "creature" else card["focus"]
            if card["kind"] == "creature":
                side.docket.append(self.make_creature(cid))
            else:
                side.discard.append(cid)
                self._effects(seat, card["effects"], action.target)
            self.log.append(f"{self._name(seat)} play {card['name']}.")
        else:
            move = (self.catalog.moves["struggle"] if action.kind == "struggle"
                    else self.catalog.moves[self.card(side.active.card_id)["moves"][action.index]])
            side.focus -= move["focus"]
            side.move_used = True
            if action.kind != "struggle" and side.active.uses[move["id"]] is not None:
                side.active.uses[move["id"]] -= 1
            if move["kind"] == "attack":
                self._attack(seat, move)
            else:
                self._effects(seat, move["effects"], action.target)
                self.log.append(f"{self._name(seat)} use {move['name']}.")
        self._resolve_knockouts()
        return True

    def public_snapshot(self):
        """A useful boundary for diagnostics and later stronger opponent models."""
        return {"turn": self.turn, "turn_number": self.turn_number, "winner": self.winner,
                "arena": dict(self.arena) if self.arena else None,
                "sides": [{"focus": s.focus, "knockouts": s.knockouts, "hand_count": len(s.hand),
                           "deck_count": len(s.deck), "active": asdict(s.active) if s.active else None,
                           "docket": [asdict(c) for c in s.docket]} for s in self.sides]}
