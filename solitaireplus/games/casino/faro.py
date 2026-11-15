import random


FARO_RANKS = (
    "A", "2", "3", "4", "5", "6", "7",
    "8", "9", "10", "J", "Q", "K",
)

FARO_SUITS = ("C", "D", "H", "S")


class FaroGame:
    """Compact Faro session model.

    The player places wagers on ranks. Each turn reveals a banker card first
    (that rank loses) and a player card second (that rank wins even money).
    Bets on ranks that do not appear stay on the layout for future turns.
    A doublet takes half the wager on that rank. The final unpaired card is
    revealed as the case card and ends the shoe.
    """

    def __init__(self):
        self.deck = []
        self.soda_card = None
        self.banker_card = None
        self.player_card = None
        self.case_card = None
        self.bets = {rank: 0 for rank in FARO_RANKS}
        self.starting_cash = 0
        self.cash = 0
        self.turn_number = 0
        self.turns_dealt = 0
        self.wagered_total = 0
        self.session_complete = False
        self.reward_claimed = False
        self.cashed_out = False
        self.last_result_text = "Place a wager on one or more ranks."
        self.last_profit = 0
        self.last_loss = 0
        self.last_doublet_loss = 0

    @staticmethod
    def _build_deck():
        return [
            {"rank": rank, "suit": suit}
            for suit in FARO_SUITS
            for rank in FARO_RANKS
        ]

    def start_session(self, starting_cash):
        try:
            starting_cash = max(0, int(starting_cash))
        except (TypeError, ValueError):
            starting_cash = 0

        self.deck = self._build_deck()
        random.shuffle(self.deck)

        # Traditional Faro begins with a burned "soda" card. With 51 cards
        # left, the shoe resolves into 25 two-card turns plus one case card.
        self.soda_card = self.deck.pop() if self.deck else None
        self.banker_card = None
        self.player_card = None
        self.case_card = None
        self.bets = {rank: 0 for rank in FARO_RANKS}
        self.starting_cash = starting_cash
        self.cash = starting_cash
        self.turn_number = 0
        self.turns_dealt = 0
        self.wagered_total = 0
        self.session_complete = False
        self.reward_claimed = False
        self.cashed_out = False
        self.last_result_text = "Place a wager on one or more ranks."
        self.last_profit = 0
        self.last_loss = 0
        self.last_doublet_loss = 0

    def get_total_bet(self):
        return sum(max(0, int(value)) for value in self.bets.values())

    def get_total_wealth(self):
        return self.cash + self.get_total_bet()

    def get_session_net(self):
        return self.get_total_wealth() - self.starting_cash

    def get_bet_amount(self, rank):
        return max(0, int(self.bets.get(rank, 0)))

    def place_bet(self, rank, amount):
        if self.session_complete or self.cashed_out:
            return False
        if rank not in self.bets:
            return False
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            return False
        if amount <= 0 or amount > self.cash:
            return False

        self.cash -= amount
        self.bets[rank] += amount
        self.wagered_total += amount
        return True

    def remove_bet(self, rank, amount):
        if self.session_complete or self.cashed_out:
            return False
        if rank not in self.bets:
            return False
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            return False
        if amount <= 0:
            return False

        removed = min(amount, self.bets[rank])
        if removed <= 0:
            return False

        self.bets[rank] -= removed
        self.cash += removed
        return True

    def clear_bets(self):
        if self.session_complete or self.cashed_out:
            return False

        total = self.get_total_bet()
        if total <= 0:
            return False

        self.cash += total
        for rank in self.bets:
            self.bets[rank] = 0
        return True

    def _resolve_pair(self, banker_card, player_card):
        banker_rank = banker_card["rank"]
        player_rank = player_card["rank"]

        self.last_profit = 0
        self.last_loss = 0
        self.last_doublet_loss = 0

        if banker_rank == player_rank:
            wager = self.bets.get(banker_rank, 0)
            if wager > 0:
                # On a doublet the house takes half of the wager. Round the
                # odd chip in the house's favor, matching traditional practice.
                house_take = (wager + 1) // 2
                self.bets[banker_rank] -= house_take
                self.last_doublet_loss = house_take
                self.last_result_text = (
                    f"Doublet: {banker_rank}. House takes ${house_take:,}."
                )
            else:
                self.last_result_text = f"Doublet: both cards are {banker_rank}."
            return

        losing_wager = self.bets.get(banker_rank, 0)
        if losing_wager > 0:
            self.bets[banker_rank] = 0
            self.last_loss = losing_wager

        winning_wager = self.bets.get(player_rank, 0)
        if winning_wager > 0:
            # The original wager remains on the layout. Even-money profit is
            # paid directly to cash.
            self.cash += winning_wager
            self.last_profit = winning_wager

        parts = [
            f"Banker: {banker_rank} loses.",
            f"Player: {player_rank} wins.",
        ]
        if self.last_profit:
            parts.append(f"+${self.last_profit:,}")
        if self.last_loss:
            parts.append(f"-${self.last_loss:,}")
        self.last_result_text = "  ".join(parts)

    def deal_turn(self):
        if self.session_complete or self.cashed_out:
            return False

        # The single card left after the 25 pairs is the case card. It does not
        # resolve a normal wager; revealing it closes the shoe.
        if len(self.deck) == 1:
            self.case_card = self.deck.pop()
            self.banker_card = None
            self.player_card = None
            self.session_complete = True
            self.last_profit = 0
            self.last_loss = 0
            self.last_doublet_loss = 0
            self.last_result_text = (
                f"Case card: {self.case_card['rank']} of "
                f"{self._suit_name(self.case_card['suit'])}. Shoe complete."
            )
            return True

        if len(self.deck) < 2:
            self.session_complete = True
            self.last_result_text = "Shoe complete."
            return False

        self.banker_card = self.deck.pop()
        self.player_card = self.deck.pop()
        self.turn_number += 1
        self.turns_dealt += 1
        self._resolve_pair(self.banker_card, self.player_card)
        return True

    def cash_out(self):
        if self.cashed_out:
            return self.cash

        self.cash += self.get_total_bet()
        for rank in self.bets:
            self.bets[rank] = 0
        self.cashed_out = True
        return self.cash

    def get_deal_button_label(self):
        if self.session_complete:
            return "SHOE COMPLETE"
        if len(self.deck) == 1:
            return "REVEAL CASE CARD"
        return "DEAL NEXT TURN"

    @staticmethod
    def _suit_name(suit):
        return {
            "C": "Clubs",
            "D": "Diamonds",
            "H": "Hearts",
            "S": "Spades",
        }.get(suit, suit)
