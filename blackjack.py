import random
import time


class BlackjackGame:

    def __init__(self):

        self.deck = []

        self.player_hand = []
        self.dealer_hand = []

        self.bet = 0

        self.round_complete = False
        self.result = None

        self.player_stood = False

        self.reset_deck()

        self.payout_claimed = False

        # ==================================================
        # Card animation
        # ==================================================

        self.card_animations = []

        self.animation_duration = 0.22
        self.animation_stagger = 0.13

        self.dealer_reveal_time = None

        self.dealer_playing = False
        self.dealer_next_action_time = None
        self.dealer_action_delay = 0.55

        self.dealer_flip_start_time = None
        self.dealer_flip_duration = 0.32

    # ==================================================
    # Deck
    # ==================================================

    def reset_deck(self):

        suits = [
            "C",
            "D",
            "H",
            "S",
        ]

        ranks = [
            "A",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10",
            "J",
            "Q",
            "K",
        ]

        self.deck = []

        for suit in suits:

            for rank in ranks:

                self.deck.append(
                    (
                        rank,
                        suit
                    )
                )

        random.shuffle(
            self.deck
        )

    def draw_card(self):

        if not self.deck:
            self.reset_deck()

        return self.deck.pop()

    def queue_card_animation(
            self,
            hand_name,
            card_index,
            delay=0.0,
            duration=None
    ):

        if duration is None:
            duration = self.animation_duration

        self.card_animations = [
            animation
            for animation in self.card_animations
            if not (
                    animation["hand"] == hand_name
                    and animation["index"] == card_index
            )
        ]

        self.card_animations.append(
            {
                "hand": hand_name,
                "index": card_index,
                "start_time": (
                        time.monotonic()
                        + delay
                ),
                "duration": duration,
            }
        )

    def get_card_animation_progress(
            self,
            hand_name,
            card_index
    ):

        for animation in reversed(
                self.card_animations
        ):

            if (
                    animation["hand"] == hand_name
                    and animation["index"] == card_index
            ):

                elapsed = (
                        time.monotonic()
                        - animation["start_time"]
                )

                if elapsed < 0:
                    return -1.0

                duration = animation.get(
                    "duration",
                    self.animation_duration
                )

                progress = (
                        elapsed
                        / duration
                )

                return min(
                    1.0,
                    progress
                )

        return 1.0

    def dealer_hole_is_revealed(self):

        if not self.round_complete:
            return False

        if self.dealer_reveal_time is None:
            return True

        return (
                time.monotonic()
                >= self.dealer_reveal_time
        )

    def get_net_result(self):

        if not self.round_complete:
            return 0

        payout = self.get_payout()

        return payout - self.bet

    # ==================================================
    # Hand values
    # ==================================================

    def get_hand_value(
            self,
            hand
    ):

        total = 0
        aces = 0

        for rank, suit in hand:

            if rank == "A":

                total += 11
                aces += 1

            elif rank in (
                    "J",
                    "Q",
                    "K"
            ):

                total += 10

            else:

                total += int(
                    rank
                )

        while (
                total > 21
                and aces > 0
        ):

            total -= 10
            aces -= 1

        return total

    def player_value(self):

        return self.get_hand_value(
            self.player_hand
        )

    def dealer_value(self):

        return self.get_hand_value(
            self.dealer_hand
        )

    # ==================================================
    # Round
    # ==================================================

    def start_round(
            self,
            bet
    ):
        self.payout_claimed = False

        self.bet = max(
            1,
            int(
                bet
            )
        )

        self.player_hand = [
            self.draw_card(),
            self.draw_card(),
        ]

        self.dealer_hand = [
            self.draw_card(),
            self.draw_card(),
        ]

        self.card_animations = []
        self.dealer_reveal_time = None
        self.dealer_flip_start_time = None

        # Proper deal order:
        # Player
        # Dealer
        # Player
        # Dealer

        self.queue_card_animation(
            "player",
            0,
            0.00
        )

        self.queue_card_animation(
            "dealer",
            0,
            self.animation_stagger
        )

        self.queue_card_animation(
            "player",
            1,
            self.animation_stagger * 2
        )

        self.queue_card_animation(
            "dealer",
            1,
            self.animation_stagger * 3
        )

        self.round_complete = False
        self.result = None

        self.player_stood = False

        # Natural blackjack checks

        player_blackjack = (
            self.player_value()
            == 21
        )

        dealer_blackjack = (
            self.dealer_value()
            == 21
        )

        if (
                player_blackjack
                or dealer_blackjack
        ):

            if (
                    player_blackjack
                    and dealer_blackjack
            ):

                self.finish_round(
                    "push"
                )

            elif player_blackjack:

                self.finish_round(
                    "blackjack"
                )

            else:

                self.finish_round(
                    "dealer"
                )

    # ==================================================
    # Player actions
    # ==================================================

    def hit(self):

        if self.round_complete:
            return False

        if self.player_stood:
            return False

        self.player_hand.append(
            self.draw_card()
        )

        new_card_index = (
                len(self.player_hand) - 1
        )

        self.queue_card_animation(
            "player",
            new_card_index
        )

        value = (
            self.player_value()
        )

        if value > 21:

            self.dealer_reveal_time = (
                    time.monotonic()
                    + 0.20
            )

            self.finish_round(
                "dealer"
            )

        elif value == 21:

            self.stand()

        return True

    def stand(self):

        if self.round_complete:
            return False

        if self.player_stood:
            return False

        self.player_stood = True
        self.dealer_playing = True

        now = time.monotonic()

        self.dealer_flip_start_time = (
                now + 0.20
        )

        self.dealer_reveal_time = (
                now
                + 0.20
                + self.dealer_flip_duration
        )

        self.dealer_next_action_time = (
                now
                + 0.20
                + self.dealer_flip_duration
                + 0.35
        )

        return True

    def get_dealer_flip_progress(self):

        if self.dealer_flip_start_time is None:
            return None

        elapsed = (
                time.monotonic()
                - self.dealer_flip_start_time
        )

        if elapsed < 0:
            return 0.0

        progress = (
                elapsed
                / self.dealer_flip_duration
        )

        return min(
            1.0,
            progress
        )

    def can_double_down(self):

        return (
                not self.round_complete
                and not self.player_stood
                and len(self.player_hand) == 2
        )

    def double_down(self):

        if not self.can_double_down():
            return False

        self.bet *= 2

        self.player_hand.append(
            self.draw_card()
        )

        new_card_index = (
                len(self.player_hand) - 1
        )

        self.queue_card_animation(
            "player",
            new_card_index,
            duration=0.32
        )

        if self.player_value() > 21:

            self.dealer_reveal_time = (
                    time.monotonic()
                    + 0.35
            )

            self.finish_round(
                "dealer"
            )

        else:

            self.stand()

        return True

    # ==================================================
    # Dealer
    # ==================================================

    def play_dealer(self):

        draw_delay = 0.38

        while self.dealer_value() < 17:
            self.dealer_hand.append(
                self.draw_card()
            )

            new_card_index = (
                    len(self.dealer_hand) - 1
            )

            self.queue_card_animation(
                "dealer",
                new_card_index,
                draw_delay
            )

            draw_delay += (
                self.animation_stagger
            )

        player_value = (
            self.player_value()
        )

        dealer_value = (
            self.dealer_value()
        )

        if dealer_value > 21:

            self.finish_round(
                "player"
            )

        elif dealer_value > player_value:

            self.finish_round(
                "dealer"
            )

        elif dealer_value < player_value:

            self.finish_round(
                "player"
            )

        else:

            self.finish_round(
                "push"
            )

    # ==================================================
    # Result
    # ==================================================

    def finish_round(
            self,
            result
    ):

        self.round_complete = True
        self.result = result

    def get_payout(self):

        if not self.round_complete:
            return 0

        if self.result == "blackjack":

            # Original bet returned
            # plus 3:2 winnings.
            return int(
                round(
                    self.bet * 2.5
                )
            )

        if self.result == "player":

            # Original bet + equal winnings.
            return (
                self.bet * 2
            )

        if self.result == "push":

            # Original bet returned.
            return self.bet

        # Dealer win.
        return 0

    def update(self):

        if not self.dealer_playing:
            return

        if self.round_complete:
            self.dealer_playing = False
            return

        now = time.monotonic()

        if self.dealer_next_action_time is None:
            return

        if now < self.dealer_next_action_time:
            return

        # ==================================================
        # Dealer draws
        # ==================================================

        if self.dealer_value() < 17:

            self.dealer_hand.append(
                self.draw_card()
            )

            new_card_index = (
                    len(self.dealer_hand) - 1
            )

            # We can tell after drawing whether
            # this will be the dealer's final card.
            final_dealer_card = (
                    self.dealer_value() >= 17
            )

            if final_dealer_card:

                card_duration = 0.60
                action_pause = 0.30

            else:

                card_duration = 0.32
                action_pause = 0.18

            self.queue_card_animation(
                "dealer",
                new_card_index,
                duration=card_duration
            )

            # Do not evaluate the dealer again
            # until the card has visibly arrived.
            self.dealer_next_action_time = (
                    now
                    + card_duration
                    + action_pause
            )

            return

        # ==================================================
        # Dealer is finished drawing
        # ==================================================

        player_value = (
            self.player_value()
        )

        dealer_value = (
            self.dealer_value()
        )

        self.dealer_playing = False
        self.dealer_next_action_time = None

        if dealer_value > 21:

            self.finish_round(
                "player"
            )

        elif dealer_value > player_value:

            self.finish_round(
                "dealer"
            )

        elif dealer_value < player_value:

            self.finish_round(
                "player"
            )

        else:

            self.finish_round(
                "push"
            )