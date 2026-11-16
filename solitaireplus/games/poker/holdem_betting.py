"""Hold'em betting: recording a wager, the betting rules (minimum bet and raise, what the
player may do) and the player's actions (a mixin of holdem.TexasHoldemGame; Draw and Stud
inherit it).
"""
from solitaireplus.games.poker.core import (
    bet_to_match,
    can_raise,
    classify_wager,
    minimum_raise_to,
    opening_current_bet,
)


class BettingMixin:
    def apply_wager(
            self,
            seat,
            old_current_bet,
            new_total,
            minimum_size
    ):
        """Record a bet or raise that took seat's round bet to new_total.

        The bet to call rises to new_total if it is higher. Only a full
        wager (at least minimum_size more, core.classify_wager) sets the
        next minimum raise, becomes the last raise and reopens betting
        for the seats that already acted. Returns whether it was full.
        """
        increase, full = classify_wager(
            old_current_bet,
            new_total,
            minimum_size
        )

        if increase > 0:
            self.current_bet = new_total

        if full:
            self.last_raise_size = increase
            self.last_raiser = seat
            self.reset_actions_after_aggression(
                seat
            )

        self.last_wager_full = full

        return full

    # ==================================================
    # BETTING RULE HELPERS
    # ==================================================

    def get_minimum_open_bet(self):

        # A legal opening bet is one big blind.
        return max(
            1,
            self.big_blind
        )

    def get_minimum_raise_size(self):

        if self.last_raise_size > 0:
            return self.last_raise_size

        return max(
            1,
            self.big_blind
        )

    def get_minimum_raise_to(self):

        return minimum_raise_to(
            self.current_bet,
            self.last_raise_size,
            self.get_minimum_open_bet()
        )

    def set_opening_wager(
            self,
            nominal_bet,
            minimum_raise
    ):
        """Set the bet to call once a hand's forced bets are posted.

        nominal_bet is the forced wager (big blind or bring-in);
        minimum_raise is the first full raise. With at most one seat able
        to act, only what was really posted can be called
        (core.opening_current_bet).
        """
        self.current_bet = opening_current_bet(
            nominal_bet,
            self.seat_round_bets(),
            self.seat_can_act()
        )
        self.settle_bet_to_match()

        self.last_raise_size = minimum_raise
        self.last_raiser = None

    def settle_bet_to_match(self):
        """Lower the bet to call when nobody can contest it (core.bet_to_match).

        With at most one seat in the hand holding chips, that seat only has
        to match the largest round bet of the other seats in the hand. Run
        at the deal, after every fold and before every turn, so a fold that
        leaves the human alone against all-in seats never asks it for a call
        that would only be returned.
        """
        self.current_bet = bet_to_match(
            self.seat_in_hand(),
            self.seat_stacks(),
            self.seat_round_bets(),
            self.current_bet
        )

    def get_player_maximum_raise_to(self):

        return (
                self.player_round_bet
                + self.player_stack
        )

    def get_player_amount_to_call(self):

        return max(
            0,
            self.current_bet
            - self.player_round_bet
        )

    def can_player_act_now(self):

        if (
                self.current_actor != 0
                or self.player_stack <= 0
                or self.player_busted
                or self.player_folded
                or self.player_all_in
                or self.hand_complete
        ):
            return False

        # The player may already have acted earlier
        # in the betting round but still owe money
        # because of a later raise.
        return (
                not self.player_has_acted
                or self.player_round_bet
                < self.current_bet
        )

    def can_player_check(self):

        return (
                self.can_player_act_now()
                and self.get_player_amount_to_call() == 0
        )

    def can_player_call(self):

        return (
                self.can_player_act_now()
                and self.get_player_amount_to_call() > 0
        )

    def can_player_raise(self):

        # The shared rule (core.can_raise): chips beyond the call,
        # somebody left to respond, and betting reopened
        # (seat_betting_reopened). If the player already acted and has
        # only been brought back by a short all-in raise, Call/Fold are
        # allowed, but raising is not reopened.
        return (
                self.can_player_act_now()
                and can_raise(
                    0,
                    self.seat_in_hand(),
                    self.seat_stacks(),
                    self.seat_round_bets(),
                    self.current_bet,
                    reopened=self.seat_betting_reopened(0)
                )
        )

    def player_fold(self):

        if (
                self.player_stack <= 0
                or self.player_folded
                or self.player_all_in
                or self.hand_complete
        ):
            return False

        self.record_player_tendency_action(
            "fold"
        )

        self.player_folded = True
        self.player_has_acted = True

        self.player_action_text = (
            "Folded"
        )

        self.log_hand_event(
            "fold",
            "You fold.",
            actor_index=0
        )

        self.resolve_after_fold()

        return True

    def player_check(self):

        if not self.can_player_check():
            return False

        self.record_player_tendency_action(
            "check"
        )

        self.player_has_acted = True
        self.player_action_text = "Checked"

        self.log_hand_event(
            "check",
            "You check.",
            actor_index=0
        )

        self.advance_to_next_actor()

        return True

    def player_call(self):

        if not self.can_player_call():
            return False

        amount_to_call = (
            self.get_player_amount_to_call()
        )

        pot_before = self.pot

        amount_paid = (
            self.commit_player_chips(
                amount_to_call
            )
        )

        if amount_paid <= 0:
            return False

        self.record_player_tendency_action(
            "call",
            amount=amount_paid,
            amount_to_call=amount_to_call,
            pot_before=pot_before
        )

        self.player_has_acted = True

        self.player_action_text = (
            f"Called ${amount_paid:,}"
        )

        suffix = (
            " and are all-in."
            if self.player_all_in
            else "."
        )

        self.log_hand_event(
            "call",
            f"You call ${amount_paid:,}{suffix}",
            actor_index=0,
            amount=amount_paid,
            all_in=self.player_all_in
        )

        self.advance_to_next_actor()

        return True

    def player_bet(
            self,
            amount
    ):

        self.last_wager_full = False

        if not self.can_player_act_now():
            return False

        if self.current_bet > 0:
            return False

        if self.player_stack <= 0:
            return False

        # B36: a bet needs somebody left to respond.
        if not self.can_player_raise():
            return False

        amount = int(
            amount
        )

        if amount <= 0:
            return False

        minimum_bet = (
            self.get_minimum_open_bet()
        )

        maximum_bet = (
            self.player_stack
        )

        if (
                amount < minimum_bet
                and amount < maximum_bet
        ):
            return False

        old_current_bet = self.current_bet
        pot_before = self.pot

        amount_paid = (
            self.commit_player_chips(
                min(
                    amount,
                    maximum_bet
                )
            )
        )

        if amount_paid <= 0:
            return False

        self.record_player_tendency_action(
            "bet",
            amount=amount_paid,
            amount_to_call=0,
            pot_before=pot_before
        )

        self.apply_wager(
            0,
            old_current_bet,
            self.player_round_bet,
            minimum_bet
        )

        self.player_has_acted = True

        self.player_action_text = (
            f"Bet ${amount_paid:,}"
        )

        suffix = (
            " and are all-in."
            if self.player_all_in
            else "."
        )

        self.log_hand_event(
            "bet",
            f"You bet ${amount_paid:,}{suffix}",
            actor_index=0,
            amount=amount_paid,
            all_in=self.player_all_in
        )

        self.advance_to_next_actor()

        return True

    def player_raise(
            self,
            raise_to
    ):

        self.last_wager_full = False

        # An all-in call uses the same chips as Call; it must remain available
        # even when the stack cannot reach the opponent's bet.
        if self.can_player_call() and self.get_player_amount_to_call() >= self.player_stack:
            return self.player_call()
        # B36: anything else lifts the bet to call, so it needs a legal raise
        # (somebody left to respond, betting still open to the player).
        if not self.can_player_raise():
            return False

        if self.current_bet <= 0:
            return False

        raise_to = int(
            raise_to
        )

        maximum_raise_to = (
            self.get_player_maximum_raise_to()
        )

        minimum_raise_to = (
            self.get_minimum_raise_to()
        )

        if raise_to <= self.current_bet:
            return False

        if (
                raise_to < minimum_raise_to
                and raise_to < maximum_raise_to
        ):
            return False

        target = min(
            raise_to,
            maximum_raise_to
        )

        old_current_bet = self.current_bet
        amount_to_call = self.get_player_amount_to_call()
        pot_before = self.pot

        amount_needed = (
            target
            - self.player_round_bet
        )

        if amount_needed <= 0:
            return False

        amount_paid = (
            self.commit_player_chips(
                amount_needed
            )
        )

        if amount_paid <= 0:
            return False

        self.record_player_tendency_action(
            "raise",
            amount=amount_paid,
            amount_to_call=amount_to_call,
            pot_before=pot_before
        )

        self.apply_wager(
            0,
            old_current_bet,
            self.player_round_bet,
            self.get_minimum_raise_size()
        )

        self.player_has_acted = True

        self.player_action_text = (
            f"Raised to "
            f"${self.player_round_bet:,}"
        )

        suffix = (
            " and are all-in."
            if self.player_all_in
            else "."
        )

        self.log_hand_event(
            "raise",
            (
                f"You raise to "
                f"${self.player_round_bet:,}"
                f"{suffix}"
            ),
            actor_index=0,
            amount=amount_paid,
            raise_to=self.player_round_bet,
            all_in=self.player_all_in
        )

        self.advance_to_next_actor()

        return True
