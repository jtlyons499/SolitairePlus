import random
import time
from collections import Counter


RANKS = [
    "A", "2", "3", "4", "5", "6", "7",
    "8", "9", "10", "J", "Q", "K",
]

SUITS = ["C", "D", "H", "S"]

SUIT_NAMES = {
    "C": "Clubs",
    "D": "Diamonds",
    "H": "Hearts",
    "S": "Spades",
}


class CrazyEightsGame:
    """Four-seat Crazy Eights game used by Casual Cards.

    Seat 0 is always the human player. Seats 1+ are NPCs. The implementation
    uses a simple draw-one rule: if a player has no legal play they draw one
    card. A playable drawn card may be played immediately; otherwise the turn
    passes. Eights are wild and choose the active suit.
    """

    def __init__(self):
        self.npcs = []
        self.hands = []
        self.stock = []
        self.discard_pile = []

        self.current_player = 0
        self.current_suit = None
        self.player_has_drawn = False

        self.pending_eight_index = None
        self.waiting_for_suit_choice = False

        self.game_over = False
        self.winner_index = None
        self.result_text = ""
        self.reward_claimed = False

        self.action_log = []
        self.last_action_text = ""

        self.npc_action_delay = 0.75
        self.npc_action_due = 0.0

    # ==================================================
    # Deck / setup
    # ==================================================

    @staticmethod
    def build_deck():
        return [
            {"rank": rank, "suit": suit}
            for suit in SUITS
            for rank in RANKS
        ]

    def start_game(self, npcs, hand_size=5):
        self.npcs = list(npcs or [])

        player_count = len(self.npcs) + 1
        self.hands = [
            []
            for _ in range(player_count)
        ]

        deck = self.build_deck()
        random.shuffle(deck)

        for _ in range(max(1, int(hand_size))):
            for player_index in range(player_count):
                if deck:
                    self.hands[player_index].append(deck.pop())

        # Start on a non-eight so the opening suit is unambiguous.
        skipped_eights = []
        first_discard = None

        while deck:
            candidate = deck.pop()
            if candidate["rank"] == "8":
                skipped_eights.append(candidate)
                continue

            first_discard = candidate
            break

        if first_discard is None:
            # Effectively impossible with a normal deck, but keep the state safe.
            first_discard = skipped_eights.pop() if skipped_eights else {
                "rank": "A",
                "suit": "S",
            }

        deck.extend(skipped_eights)
        random.shuffle(deck)

        self.stock = deck
        self.discard_pile = [first_discard]

        self.current_player = 0
        self.current_suit = first_discard["suit"]
        self.player_has_drawn = False

        self.pending_eight_index = None
        self.waiting_for_suit_choice = False

        self.game_over = False
        self.winner_index = None
        self.result_text = ""
        self.reward_claimed = False

        self.action_log = []
        self.last_action_text = ""

        self._log(
            f"Crazy Eights begins. {self.card_label(first_discard)} is up."
        )

        self._schedule_npc_action()
        return True

    # ==================================================
    # Display helpers
    # ==================================================

    @staticmethod
    def card_key(card):
        if not card:
            return None
        return f"{card['rank']}{card['suit']}"

    @staticmethod
    def card_label(card):
        if not card:
            return "card"
        return f"{card['rank']} of {SUIT_NAMES.get(card['suit'], card['suit'])}"

    def get_player_name(self, player_index):
        if player_index == 0:
            return "You"

        npc_index = player_index - 1
        if 0 <= npc_index < len(self.npcs):
            return str(self.npcs[npc_index].get("name", "NPC"))

        return "NPC"

    def get_top_discard(self):
        if not self.discard_pile:
            return None
        return self.discard_pile[-1]

    def get_active_suit_name(self):
        return SUIT_NAMES.get(self.current_suit, str(self.current_suit or ""))

    # ==================================================
    # Rules
    # ==================================================

    def is_card_playable(self, card):
        if not card or self.game_over:
            return False

        top = self.get_top_discard()
        if top is None:
            return True

        return (
            card["rank"] == "8"
            or card["suit"] == self.current_suit
            or card["rank"] == top["rank"]
        )

    def get_playable_indexes(self, player_index):
        if not (0 <= player_index < len(self.hands)):
            return []

        return [
            index
            for index, card in enumerate(self.hands[player_index])
            if self.is_card_playable(card)
        ]

    def has_playable_card(self, player_index):
        return bool(self.get_playable_indexes(player_index))

    def can_player_draw(self):
        return (
            not self.game_over
            and self.current_player == 0
            and not self.waiting_for_suit_choice
            and not self.player_has_drawn
            and not self.has_playable_card(0)
        )

    # ==================================================
    # Human actions
    # ==================================================

    def play_player_card(self, card_index):
        if self.game_over or self.current_player != 0:
            return "invalid"

        if self.waiting_for_suit_choice:
            return "choose_suit"

        if not (0 <= card_index < len(self.hands[0])):
            return "invalid"

        card = self.hands[0][card_index]
        if not self.is_card_playable(card):
            return "invalid"

        if card["rank"] == "8":
            self.pending_eight_index = card_index
            self.waiting_for_suit_choice = True
            return "choose_suit"

        self._commit_play(0, card_index, chosen_suit=None)
        return "played"

    def choose_player_suit(self, suit):
        if (
            self.game_over
            or self.current_player != 0
            or not self.waiting_for_suit_choice
            or self.pending_eight_index is None
            or suit not in SUITS
        ):
            return False

        card_index = self.pending_eight_index
        self.pending_eight_index = None
        self.waiting_for_suit_choice = False

        if not (0 <= card_index < len(self.hands[0])):
            return False

        card = self.hands[0][card_index]
        if card["rank"] != "8":
            return False

        self._commit_play(0, card_index, chosen_suit=suit)
        return True

    def draw_player_card(self):
        if not self.can_player_draw():
            return False

        card = self._draw_one()
        self.player_has_drawn = True

        if card is None:
            self._log("No cards remain to draw.")
            self._advance_turn()
            return False

        self.hands[0].append(card)
        self._log(f"You draw {self.card_label(card)}.")

        # A playable drawn card may be played immediately. Otherwise turn passes.
        if not self.is_card_playable(card):
            self._advance_turn()

        return True

    # ==================================================
    # NPC turns
    # ==================================================

    def update(self):
        if self.game_over or self.waiting_for_suit_choice:
            return False

        if self.current_player == 0:
            return False

        if time.monotonic() < self.npc_action_due:
            return False

        return self._take_npc_turn(self.current_player)

    def _take_npc_turn(self, player_index):
        playable = self.get_playable_indexes(player_index)

        if playable:
            card_index = self._choose_npc_card(player_index, playable)
            card = self.hands[player_index][card_index]
            chosen_suit = None

            if card["rank"] == "8":
                chosen_suit = self._choose_npc_suit(player_index, card_index)

            self._commit_play(
                player_index,
                card_index,
                chosen_suit=chosen_suit,
            )
            return True

        card = self._draw_one()
        name = self.get_player_name(player_index)

        if card is None:
            self._log(f"{name} cannot draw.")
            self._advance_turn()
            return True

        self.hands[player_index].append(card)
        self._log(f"{name} draws a card.")

        if self.is_card_playable(card):
            card_index = len(self.hands[player_index]) - 1
            chosen_suit = None

            if card["rank"] == "8":
                chosen_suit = self._choose_npc_suit(player_index, card_index)

            self._commit_play(
                player_index,
                card_index,
                chosen_suit=chosen_suit,
            )
        else:
            self._advance_turn()

        return True

    def _choose_npc_card(self, player_index, playable_indexes):
        npc_index = player_index - 1
        npc = self.npcs[npc_index] if 0 <= npc_index < len(self.npcs) else {}
        tier = str(npc.get("skill_tier", "mid")).lower()
        personality = str(npc.get("game_personality", "balanced")).lower()

        if tier == "low" or personality == "unpredictable":
            return random.choice(playable_indexes)

        hand = self.hands[player_index]
        non_eights = [
            index
            for index in playable_indexes
            if hand[index]["rank"] != "8"
        ]

        # Stronger NPCs generally preserve wild cards for later.
        candidates = non_eights or list(playable_indexes)

        suit_counts = Counter(
            card["suit"]
            for card in hand
            if card["rank"] != "8"
        )

        def score(index):
            card = hand[index]
            value = suit_counts.get(card["suit"], 0) * 5

            if card["rank"] == "8":
                value -= 7

            if card["rank"] in ("K", "Q", "J", "10"):
                value += 2

            if personality in ("aggressive", "escalator"):
                value += random.uniform(0.0, 3.0)
            else:
                value += random.uniform(0.0, 1.5)

            return value

        return max(candidates, key=score)

    def _choose_npc_suit(self, player_index, eight_index):
        remaining = [
            card
            for index, card in enumerate(self.hands[player_index])
            if index != eight_index
        ]

        counts = Counter(
            card["suit"]
            for card in remaining
            if card["rank"] != "8"
        )

        if not counts:
            return random.choice(SUITS)

        best_count = max(counts.values())
        best_suits = [
            suit
            for suit, count in counts.items()
            if count == best_count
        ]
        return random.choice(best_suits)

    # ==================================================
    # Internal flow
    # ==================================================

    def _commit_play(self, player_index, card_index, chosen_suit=None):
        hand = self.hands[player_index]
        card = hand.pop(card_index)
        self.discard_pile.append(card)

        if card["rank"] == "8":
            self.current_suit = chosen_suit or card["suit"]
        else:
            self.current_suit = card["suit"]

        name = self.get_player_name(player_index)
        if player_index == 0:
            prefix = "You play"
        else:
            prefix = f"{name} plays"

        text = f"{prefix} {self.card_label(card)}"
        if card["rank"] == "8":
            text += f" and calls {self.get_active_suit_name()}"
        text += "."
        self._log(text)

        if not hand:
            self._finish_game(player_index)
            return

        self._advance_turn()

    def _advance_turn(self):
        if self.game_over or not self.hands:
            return

        self.current_player = (
            self.current_player + 1
        ) % len(self.hands)

        self.player_has_drawn = False
        self.pending_eight_index = None
        self.waiting_for_suit_choice = False

        self._schedule_npc_action()

    def _schedule_npc_action(self):
        if self.current_player == 0:
            self.npc_action_due = 0.0
        else:
            self.npc_action_due = time.monotonic() + self.npc_action_delay

    def _draw_one(self):
        if not self.stock:
            self._recycle_stock()

        if not self.stock:
            self._resolve_blocked_game()
            return None

        return self.stock.pop()

    def _recycle_stock(self):
        if len(self.discard_pile) <= 1:
            return False

        top = self.discard_pile[-1]
        recycled = self.discard_pile[:-1]
        random.shuffle(recycled)

        self.stock = recycled
        self.discard_pile = [top]
        self._log("The discard pile is reshuffled into the draw pile.")
        return True

    def _resolve_blocked_game(self):
        if self.game_over or not self.hands:
            return

        smallest = min(len(hand) for hand in self.hands)
        winners = [
            index
            for index, hand in enumerate(self.hands)
            if len(hand) == smallest
        ]

        if len(winners) == 1:
            self._finish_game(winners[0], blocked=True)
            return

        self.game_over = True
        self.winner_index = None
        names = ", ".join(self.get_player_name(index) for index in winners)
        self.result_text = f"Blocked game. Lowest-card tie: {names}."
        self._log(self.result_text)

    def _finish_game(self, winner_index, blocked=False):
        self.game_over = True
        self.winner_index = winner_index
        winner_name = self.get_player_name(winner_index)

        if winner_index == 0:
            self.result_text = "You win Crazy Eights!"
        else:
            self.result_text = f"{winner_name} wins Crazy Eights."

        if blocked:
            self.result_text = self.result_text.replace(
                "Crazy Eights", "the blocked game"
            )

        self._log(self.result_text)

    def _log(self, text):
        self.last_action_text = str(text)
        self.action_log.append(self.last_action_text)
        self.action_log = self.action_log[-8:]
