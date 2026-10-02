import random
import time


# ==================================================
# ROULETTE CONSTANTS
# ==================================================

ROULETTE_NUMBERS = [
    "0",
    "00",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "11",
    "12",
    "13",
    "14",
    "15",
    "16",
    "17",
    "18",
    "19",
    "20",
    "21",
    "22",
    "23",
    "24",
    "25",
    "26",
    "27",
    "28",
    "29",
    "30",
    "31",
    "32",
    "33",
    "34",
    "35",
    "36",
]

AMERICAN_WHEEL_ORDER = [
    "0",
    "28",
    "9",
    "26",
    "30",
    "11",
    "7",
    "20",
    "32",
    "17",
    "5",
    "22",
    "34",
    "15",
    "3",
    "24",
    "36",
    "13",
    "1",
    "00",
    "27",
    "10",
    "25",
    "29",
    "12",
    "8",
    "19",
    "31",
    "18",
    "6",
    "21",
    "33",
    "16",
    "4",
    "23",
    "35",
    "14",
    "2",
]


RED_NUMBERS = {
    1, 3, 5, 7, 9,
    12, 14, 16, 18,
    19, 21, 23, 25, 27,
    30, 32, 34, 36,
}


BLACK_NUMBERS = {
    2, 4, 6, 8, 10,
    11, 13, 15, 17,
    20, 22, 24, 26, 28,
    29, 31, 33, 35,
}


# ==================================================
# ROULETTE GAME
# ==================================================

class RouletteGame:

    def __init__(self):

        self.bets = []

        self.result = None

        self.round_complete = False
        self.payout_claimed = False

        self.spinning = False
        self.spin_start_time = 0.0
        self.spin_duration = 4.5

        self.display_result = None

    # ==================================================
    # ROUND RESET
    # ==================================================

    def reset_round(self):

        self.bets = []

        self.result = None

        self.round_complete = False
        self.payout_claimed = False

        self.spinning = False
        self.spin_start_time = 0.0

        self.display_result = None

    def remove_bet(
            self,
            bet_type,
            bet_value,
            bet_amount
    ):

        if self.spinning:
            return False

        if bet_amount <= 0:
            return False

        for bet in self.bets:

            if (
                    bet["type"] == bet_type
                    and bet["value"] == bet_value
            ):

                bet["amount"] -= (
                    bet_amount
                )

                if bet["amount"] <= 0:
                    self.bets.remove(
                        bet
                    )

                return True

        return False

    # ==================================================
    # BET
    # ==================================================

    def place_bet(
            self,
            bet_type,
            bet_value,
            bet_amount
    ):

        if self.spinning:
            return False

        if bet_amount <= 0:
            return False

        # ==========================================
        # Stack onto an existing identical bet
        # ==========================================

        for bet in self.bets:

            if (
                    bet["type"] == bet_type
                    and bet["value"] == bet_value
            ):
                bet["amount"] += (
                    bet_amount
                )

                return True

        # ==========================================
        # New bet
        # ==========================================

        self.bets.append(
            {
                "type": bet_type,
                "value": bet_value,
                "amount": bet_amount,
            }
        )

        self.result = None
        self.round_complete = False
        self.payout_claimed = False
        self.display_result = None

        return True
    # ==================================================
    # SPIN
    # ==================================================

    def start_spin(self):

        if not self.bets:
            return False

        if self.get_total_bet() <= 0:
            return False

        if self.spinning:
            return False

        self.spinning = True
        self.round_complete = False

        self.spin_start_time = (
            time.monotonic()
        )

        self.result = random.choice(
            ROULETTE_NUMBERS
        )

        self.display_result = None

        return True

    # ==================================================
    # UPDATE
    # ==================================================

    def update(self):

        if not self.spinning:
            return

        elapsed = (
            time.monotonic()
            - self.spin_start_time
        )

        if elapsed >= self.spin_duration:

            self.spinning = False

            self.display_result = (
                self.result
            )

            self.round_complete = True

    # ==================================================
    # SPIN PROGRESS
    # ==================================================

    def get_spin_progress(self):

        if not self.spinning:
            return 1.0

        elapsed = (
            time.monotonic()
            - self.spin_start_time
        )

        progress = (
            elapsed
            / self.spin_duration
        )

        return max(
            0.0,
            min(
                1.0,
                progress
            )
        )

    # ==================================================
    # RESULT COLOR
    # ==================================================

    def get_result_color(self):

        if self.result is None:
            return None

        if self.result in (
                "0",
                "00"
        ):
            return "green"

        number = int(
            self.result
        )

        if number in RED_NUMBERS:
            return "red"

        return "black"

    # ==================================================
    # WIN CHECK
    # ==================================================

    def is_bet_winner(
            self,
            bet
    ):

        if self.result is None:
            return False

        bet_type = bet["type"]
        bet_value = bet["value"]

        if bet_type == "number":
            return (
                    self.result
                    == str(
                bet_value
            )
            )

        if self.result in (
                "0",
                "00"
        ):
            return False

        number = int(
            self.result
        )

        if bet_type == "color":
            return (
                    self.get_result_color()
                    == bet_value
            )

        if bet_type == "parity":

            if bet_value == "odd":
                return (
                        number % 2 == 1
                )

            if bet_value == "even":
                return (
                        number % 2 == 0
                )

        if bet_type == "range":

            if bet_value == "low":
                return (
                        1 <= number <= 18
                )

            if bet_value == "high":
                return (
                        19 <= number <= 36
                )
        # ------------------------------------------
        # Dozens
        # ------------------------------------------

        if bet_type == "dozen":

            if bet_value == 1:
                return 1 <= number <= 12

            if bet_value == 2:
                return 13 <= number <= 24

            if bet_value == 3:
                return 25 <= number <= 36

        # ------------------------------------------
        # Columns
        # ------------------------------------------

        if bet_type == "column":

            if bet_value == 1:
                return number % 3 == 1

            if bet_value == 2:
                return number % 3 == 2

            if bet_value == 3:
                return number % 3 == 0

        return False

    def get_payout(self):

        if not self.round_complete:
            return 0

        total_payout = 0

        for bet in self.bets:

            if not self.is_bet_winner(
                    bet
            ):
                continue

            if bet["type"] == "number":

                # 35:1 profit + wager
                total_payout += (
                        bet["amount"]
                        * 36
                )

            elif bet["type"] in (
                    "dozen",
                    "column",
            ):

                # 2:1 profit + wager
                total_payout += (
                        bet["amount"]
                        * 3
                )

            else:

                # 1:1 profit + wager
                total_payout += (
                        bet["amount"]
                        * 2
                )

        return total_payout

    # ==================================================
    # NET RESULT
    # ==================================================

    def get_net_result(self):

        if not self.round_complete:
            return 0

        return (
                self.get_payout()
                - self.get_total_bet()
        )


    # ==================================================
    # HUMAN-READABLE BET NAME
    # ==================================================

    def get_bet_label(self):

        if not self.bets:
            return "No Bets"

        if len(self.bets) == 1:

            bet = self.bets[0]

            if bet["type"] == "number":
                return (
                    f"Number "
                    f"{bet['value']}"
                )

            if bet["type"] == "color":
                return str(
                    bet["value"]
                ).title()

            if bet["type"] == "parity":
                return str(
                    bet["value"]
                ).title()

            if bet["type"] == "range":

                if bet["value"] == "low":
                    return "1-18"

                if bet["value"] == "high":
                    return "19-36"

        return (
            f"{len(self.bets)} active bets"
        )

    def get_total_bet(self):

        return sum(
            bet["amount"]
            for bet in self.bets
        )

    def clear_bets(self):

        if self.spinning:
            return False

        self.bets = []

        return True

    def get_bet_amount(
            self,
            bet_type,
            bet_value
    ):

        for bet in self.bets:

            if (
                    bet["type"] == bet_type
                    and bet["value"] == bet_value
            ):
                return bet["amount"]

        return 0