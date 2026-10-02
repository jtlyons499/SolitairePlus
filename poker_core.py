# ==================================================
# SHARED POKER CORE HELPERS
#
# This module is intentionally game-agnostic so
# Texas Hold'em, Five-Card Draw, and Seven-Card Stud
# can share the same hand-history/event infrastructure.
# ==================================================

SUIT_SYMBOLS = {
    "Clubs": "C",
    "Diamonds": "D",
    "Hearts": "H",
    "Spades": "S",
}


def format_poker_card(card):

    if not card:
        return "?"

    rank = str(
        card.get(
            "rank",
            "?"
        )
    )

    suit = SUIT_SYMBOLS.get(
        card.get("suit"),
        "?"
    )

    return f"{rank}{suit}"


def format_poker_cards(cards):

    return " ".join(
        format_poker_card(card)
        for card in cards
        if card
    )


class PokerHandHistory:

    def __init__(
            self,
            max_lines=500,
            max_events=1000
    ):

        self.max_lines = max(
            50,
            int(max_lines)
        )

        self.max_events = max(
            100,
            int(max_events)
        )

        self.lines = []
        self.events = []

    def clear(self):

        self.lines.clear()
        self.events.clear()

    def start_hand(
            self,
            hand_number,
            game_name="Poker",
            stage="start"
    ):

        if self.lines:
            self.lines.append("")

        self.add(
            "hand_start",
            f"--- {game_name} Hand {hand_number} ---",
            hand_number=hand_number,
            stage=stage
        )

    def add(
            self,
            event_type,
            text,
            hand_number=None,
            stage=None,
            actor_index=None,
            amount=None,
            **data
    ):

        if not text:
            return

        text = str(text)

        event = {
            "type": str(event_type),
            "text": text,
            "hand_number": hand_number,
            "stage": stage,
            "actor_index": actor_index,
            "amount": amount,
        }

        if data:
            event.update(data)

        self.events.append(event)
        self.lines.append(text)

        if len(self.events) > self.max_events:
            del self.events[
                :-self.max_events
            ]

        if len(self.lines) > self.max_lines:
            del self.lines[
                :-self.max_lines
            ]

    def get_lines(self):

        return list(self.lines)

    def get_events(self):

        return [
            dict(event)
            for event in self.events
        ]

    def get_current_hand_events(
            self,
            hand_number
    ):

        return [
            dict(event)
            for event in self.events
            if event.get("hand_number")
            == hand_number
        ]
