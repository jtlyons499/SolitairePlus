import random
import time


class BlackjackGame:

    def __init__(self):
        self.deck = []

        # ``player_hand`` is kept as a compatibility alias for the currently
        # active hand. Split rounds use ``player_hands`` internally.
        self.player_hand = []
        self.player_hands = []
        self.player_hand_bets = []
        self.player_hand_done = []
        self.player_hand_results = []
        self.active_hand_index = 0
        self.was_split = False
        self.split_aces = False

        self.dealer_hand = []

        # Total money committed to the round across all hands. This preserves
        # the old public ``bet`` API while making split/double settlement sane.
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

        # Natural-blackjack results wait until the hole card visibly flips.
        self.pending_natural_result = None
        self.pending_natural_finish_time = None

        # If every split hand busts, still reveal the hole card briefly before
        # announcing the result rather than ending on a hidden dealer card.
        self.pending_split_finish_time = None

    # ==================================================
    # Deck
    # ==================================================

    def reset_deck(self):
        suits = ["C", "D", "H", "S"]
        ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        self.deck = [(rank, suit) for suit in suits for rank in ranks]
        random.shuffle(self.deck)

    def draw_card(self):
        if not self.deck:
            self.reset_deck()
        return self.deck.pop()

    # ==================================================
    # Animation helpers
    # ==================================================

    def queue_card_animation(self, hand_name, card_index, delay=0.0, duration=None):
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
                "start_time": time.monotonic() + delay,
                "duration": duration,
            }
        )

    def get_card_animation_progress(self, hand_name, card_index):
        for animation in reversed(self.card_animations):
            if animation["hand"] == hand_name and animation["index"] == card_index:
                elapsed = time.monotonic() - animation["start_time"]
                if elapsed < 0:
                    return -1.0
                duration = animation.get("duration", self.animation_duration)
                return min(1.0, elapsed / duration)
        return 1.0

    def dealer_hole_is_revealed(self):
        if self.dealer_reveal_time is None:
            return self.round_complete
        return time.monotonic() >= self.dealer_reveal_time

    def start_dealer_reveal(self, delay=0.20):
        now = time.monotonic()
        self.dealer_flip_start_time = now + max(0.0, float(delay))
        self.dealer_reveal_time = self.dealer_flip_start_time + self.dealer_flip_duration
        return self.dealer_reveal_time

    def get_dealer_flip_progress(self):
        if self.dealer_flip_start_time is None:
            return None
        elapsed = time.monotonic() - self.dealer_flip_start_time
        if elapsed < 0:
            return 0.0
        return min(1.0, elapsed / self.dealer_flip_duration)

    # ==================================================
    # Hand helpers
    # ==================================================

    def get_hand_value(self, hand):
        total = 0
        aces = 0
        for rank, _suit in hand:
            if rank == "A":
                total += 11
                aces += 1
            elif rank in ("J", "Q", "K"):
                total += 10
            else:
                total += int(rank)

        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    def _sync_player_hand_alias(self):
        if self.player_hands:
            index = max(0, min(self.active_hand_index, len(self.player_hands) - 1))
            self.player_hand = self.player_hands[index]
        else:
            self.player_hand = []

    def get_player_hands(self):
        return self.player_hands if self.player_hands else [self.player_hand]

    def is_split_round(self):
        return self.was_split and len(self.player_hands) > 1

    def current_hand(self):
        self._sync_player_hand_alias()
        return self.player_hand

    def current_hand_bet(self):
        if not self.player_hand_bets:
            return self.bet
        index = max(0, min(self.active_hand_index, len(self.player_hand_bets) - 1))
        return self.player_hand_bets[index]

    def get_total_wager(self):
        return self.bet

    def get_total_player_cards(self):
        return sum(len(hand) for hand in self.get_player_hands())

    def get_hand_value_at(self, index):
        if not (0 <= index < len(self.player_hands)):
            return 0
        return self.get_hand_value(self.player_hands[index])

    def get_hand_result(self, index):
        if not (0 <= index < len(self.player_hand_results)):
            return None
        return self.player_hand_results[index]

    def player_value(self):
        return self.get_hand_value(self.current_hand())

    def dealer_value(self):
        return self.get_hand_value(self.dealer_hand)

    # ==================================================
    # Round
    # ==================================================

    def start_round(self, bet):
        self.payout_claimed = False
        opening_bet = max(1, int(bet))
        self.bet = opening_bet

        first_hand = [self.draw_card(), self.draw_card()]
        self.player_hands = [first_hand]
        self.player_hand_bets = [opening_bet]
        self.player_hand_done = [False]
        self.player_hand_results = [None]
        self.active_hand_index = 0
        self.was_split = False
        self.split_aces = False
        self._sync_player_hand_alias()

        self.dealer_hand = [self.draw_card(), self.draw_card()]

        self.card_animations = []
        self.dealer_reveal_time = None
        self.dealer_flip_start_time = None
        self.dealer_playing = False
        self.dealer_next_action_time = None
        self.pending_natural_result = None
        self.pending_natural_finish_time = None
        self.pending_split_finish_time = None

        # Proper deal order: player, dealer, player, dealer.
        self.queue_card_animation("player", 0, 0.00)
        self.queue_card_animation("dealer", 0, self.animation_stagger)
        self.queue_card_animation("player", 1, self.animation_stagger * 2)
        self.queue_card_animation("dealer", 1, self.animation_stagger * 3)

        self.round_complete = False
        self.result = None
        self.player_stood = False

        player_blackjack = self.player_value() == 21
        dealer_blackjack = self.dealer_value() == 21

        if player_blackjack or dealer_blackjack:
            if player_blackjack and dealer_blackjack:
                natural_result = "push"
            elif player_blackjack:
                natural_result = "blackjack"
            else:
                natural_result = "dealer"

            self.player_stood = True
            self.player_hand_done[0] = True
            initial_deal_remaining = (
                self.animation_stagger * 3
                + self.animation_duration
                + 0.16
            )
            reveal_finish = self.start_dealer_reveal(initial_deal_remaining)
            self.pending_natural_result = natural_result
            self.pending_natural_finish_time = reveal_finish + 0.34

    # ==================================================
    # Splitting
    # ==================================================

    def can_split(self):
        if self.round_complete or self.player_stood or self.was_split:
            return False
        if len(self.player_hands) != 1 or len(self.player_hands[0]) != 2:
            return False
        first_rank = self.player_hands[0][0][0]
        second_rank = self.player_hands[0][1][0]
        return first_rank == second_rank

    def split_hand(self):
        if not self.can_split():
            return False

        original = list(self.player_hands[0])
        original_bet = self.player_hand_bets[0]
        self.was_split = True
        self.split_aces = original[0][0] == "A"

        self.player_hands = [
            [original[0], self.draw_card()],
            [original[1], self.draw_card()],
        ]
        self.player_hand_bets = [original_bet, original_bet]
        self.player_hand_done = [False, False]
        self.player_hand_results = [None, None]
        self.active_hand_index = 0
        self.bet += original_bet
        self.player_stood = False

        # Existing split cards are already on the table; animate only the new
        # cards being dealt to each new hand.
        self.queue_card_animation("player_0", 1, 0.00, duration=0.30)
        self.queue_card_animation("player_1", 1, self.animation_stagger, duration=0.30)
        self._sync_player_hand_alias()

        # Common casino rule: split aces receive one card each and then stand.
        if self.split_aces:
            self.player_hand_done = [True, True]
            self.player_stood = True
            self._begin_dealer_play(delay=self.animation_stagger + 0.30)

        return True

    # ==================================================
    # Player actions
    # ==================================================

    def _complete_active_hand(self):
        if not self.player_hands:
            return
        self.player_hand_done[self.active_hand_index] = True

        for index in range(self.active_hand_index + 1, len(self.player_hands)):
            if not self.player_hand_done[index]:
                self.active_hand_index = index
                self._sync_player_hand_alias()
                return

        self.player_stood = True

        if all(self.get_hand_value(hand) > 21 for hand in self.player_hands):
            reveal_finish = self.start_dealer_reveal(0.18)
            self.pending_split_finish_time = reveal_finish + 0.20
        else:
            self._begin_dealer_play()

    def hit(self):
        if self.round_complete or self.player_stood:
            return False

        hand = self.current_hand()
        hand.append(self.draw_card())
        new_card_index = len(hand) - 1
        animation_name = f"player_{self.active_hand_index}" if self.is_split_round() else "player"
        self.queue_card_animation(animation_name, new_card_index)

        value = self.get_hand_value(hand)
        if value >= 21:
            self._complete_active_hand()
        return True

    def stand(self):
        if self.round_complete or self.player_stood:
            return False
        self._complete_active_hand()
        return True

    def can_double_down(self):
        if self.round_complete or self.player_stood:
            return False
        hand = self.current_hand()
        return len(hand) == 2 and not self.player_hand_done[self.active_hand_index]

    def double_down(self):
        if not self.can_double_down():
            return False

        hand_index = self.active_hand_index
        additional_bet = self.player_hand_bets[hand_index]
        self.player_hand_bets[hand_index] *= 2
        self.bet += additional_bet

        hand = self.current_hand()
        hand.append(self.draw_card())
        new_card_index = len(hand) - 1
        animation_name = f"player_{hand_index}" if self.is_split_round() else "player"
        self.queue_card_animation(animation_name, new_card_index, duration=0.32)
        self._complete_active_hand()
        return True

    # ==================================================
    # Dealer / resolution
    # ==================================================

    def _begin_dealer_play(self, delay=0.20):
        self.player_stood = True
        self.dealer_playing = True
        reveal_finish = self.start_dealer_reveal(delay)
        self.dealer_next_action_time = reveal_finish + 0.35

    def _resolve_split_round(self):
        dealer_value = self.dealer_value()
        results = []

        for hand in self.player_hands:
            value = self.get_hand_value(hand)
            if value > 21:
                results.append("dealer")
            elif dealer_value > 21:
                results.append("player")
            elif value > dealer_value:
                results.append("player")
            elif value < dealer_value:
                results.append("dealer")
            else:
                results.append("push")

        self.player_hand_results = results
        self.round_complete = True
        self.result = "split"
        self.dealer_playing = False
        self.dealer_next_action_time = None
        self.pending_split_finish_time = None

    def _resolve_unsplit_round(self):
        player_value = self.player_value()
        dealer_value = self.dealer_value()

        if dealer_value > 21:
            self.finish_round("player")
        elif dealer_value > player_value:
            self.finish_round("dealer")
        elif dealer_value < player_value:
            self.finish_round("player")
        else:
            self.finish_round("push")

    def finish_round(self, result):
        self.round_complete = True
        self.result = result
        self.pending_natural_result = None
        self.pending_natural_finish_time = None
        self.pending_split_finish_time = None

        if self.player_hand_results:
            self.player_hand_results[0] = result

    # ==================================================
    # Payout
    # ==================================================

    def get_payout(self):
        if not self.round_complete:
            return 0

        if self.is_split_round():
            payout = 0
            for index, result in enumerate(self.player_hand_results):
                wager = self.player_hand_bets[index]
                if result == "player":
                    payout += wager * 2
                elif result == "push":
                    payout += wager
            return payout

        if self.result == "blackjack":
            return int(round(self.bet * 2.5))
        if self.result == "player":
            return self.bet * 2
        if self.result == "push":
            return self.bet
        return 0

    def get_net_result(self):
        if not self.round_complete:
            return 0
        return self.get_payout() - self.bet

    # ==================================================
    # Update
    # ==================================================

    def update(self):
        now = time.monotonic()

        if self.pending_natural_result is not None:
            if (
                self.pending_natural_finish_time is not None
                and now >= self.pending_natural_finish_time
            ):
                result = self.pending_natural_result
                self.finish_round(result)
            return

        if self.pending_split_finish_time is not None:
            if now >= self.pending_split_finish_time:
                self._resolve_split_round()
            return

        if not self.dealer_playing:
            return

        if self.round_complete:
            self.dealer_playing = False
            return

        if self.dealer_next_action_time is None or now < self.dealer_next_action_time:
            return

        if self.dealer_value() < 17:
            self.dealer_hand.append(self.draw_card())
            new_card_index = len(self.dealer_hand) - 1
            final_dealer_card = self.dealer_value() >= 17
            if final_dealer_card:
                card_duration = 0.60
                action_pause = 0.30
            else:
                card_duration = 0.32
                action_pause = 0.18

            self.queue_card_animation("dealer", new_card_index, duration=card_duration)
            self.dealer_next_action_time = now + card_duration + action_pause
            return

        self.dealer_playing = False
        self.dealer_next_action_time = None

        if self.is_split_round():
            self._resolve_split_round()
        else:
            self._resolve_unsplit_round()
