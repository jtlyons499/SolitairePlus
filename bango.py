import random


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


class BangoGame:
    """Playing-card Bingo/Bango using two independent standard decks.

    One deck supplies five face-up cards to each player. The second deck is the
    caller deck. When a matching card is called, that dealt card is turned face
    down. The first player whose five cards are all face down wins.
    """

    def __init__(self):
        self.npcs = []
        self.hands = []
        self.caller_deck = []
        self.called_cards = []

        self.last_called_card = None
        self.last_match_indexes = []
        self.call_count = 0

        self.game_over = False
        self.winner_index = None
        self.result_text = ""
        self.reward_claimed = False

        self.action_log = []
        self.last_action_text = ""

    @staticmethod
    def build_deck():
        return [
            {"rank": rank, "suit": suit}
            for suit in SUITS
            for rank in RANKS
        ]

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

    def start_game(self, npcs, hand_size=5):
        self.npcs = list(npcs or [])
        player_count = len(self.npcs) + 1

        player_deck = self.build_deck()
        random.shuffle(player_deck)

        self.hands = [
            []
            for _ in range(player_count)
        ]

        for _ in range(max(1, int(hand_size))):
            for player_index in range(player_count):
                card = player_deck.pop()
                self.hands[player_index].append(
                    {
                        "card": card,
                        "marked": False,
                    }
                )

        self.caller_deck = self.build_deck()
        random.shuffle(self.caller_deck)

        self.called_cards = []
        self.last_called_card = None
        self.last_match_indexes = []
        self.call_count = 0

        self.game_over = False
        self.winner_index = None
        self.result_text = ""
        self.reward_claimed = False

        self.action_log = []
        self.last_action_text = ""
        self._log("Bango begins. Call cards until somebody covers all five.")
        return True

    def call_next(self):
        if self.game_over:
            return False

        if not self.caller_deck:
            return False

        card = self.caller_deck.pop()
        self.last_called_card = card
        self.called_cards.append(card)
        self.call_count += 1
        self.last_match_indexes = []

        card_key = self.card_key(card)
        matched_names = []

        for player_index, hand in enumerate(self.hands):
            for item in hand:
                if item["marked"]:
                    continue

                if self.card_key(item["card"]) == card_key:
                    item["marked"] = True
                    self.last_match_indexes.append(player_index)
                    matched_names.append(self.get_player_name(player_index))

        call_text = f"Caller: {self.card_label(card)}."
        if matched_names:
            if matched_names == ["You"]:
                call_text += " You turn it face down."
            else:
                call_text += " " + ", ".join(matched_names) + " marks it."

        self._log(call_text)

        for player_index, hand in enumerate(self.hands):
            if hand and all(item["marked"] for item in hand):
                self._finish_game(player_index)
                break

        return True

    def get_marked_count(self, player_index):
        if not (0 <= player_index < len(self.hands)):
            return 0
        return sum(1 for item in self.hands[player_index] if item["marked"])

    def _finish_game(self, winner_index):
        self.game_over = True
        self.winner_index = winner_index

        if winner_index == 0:
            self.result_text = "BANGO! You covered all five cards first!"
        else:
            name = self.get_player_name(winner_index)
            self.result_text = f"BANGO! {name} covered all five cards first."

        self._log(self.result_text)

    def _log(self, text):
        self.last_action_text = str(text)
        self.action_log.append(self.last_action_text)
        self.action_log = self.action_log[-8:]
