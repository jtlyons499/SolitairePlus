import random
from collections import Counter

from poker_core import describe_poker_score, format_poker_card, format_poker_cards
from poker_ai import (
    get_poker_personality_profile,
)
from texas_holdem import (
    HAND_NAMES,
    RANK_VALUES,
    TexasHoldemGame,
)


SUIT_BRING_IN_ORDER = {
    "Clubs": 0,
    "Diamonds": 1,
    "Hearts": 2,
    "Spades": 3,
}


class SevenCardStudGame(TexasHoldemGame):
    """Seven-Card Stud using the shared poker betting, pot, history, and AI systems.

    Table indexes remain consistent with the other poker games:
    0 = human player, 1+ = NPCs.

    This implementation uses traditional fixed-limit Stud structure:
    - every live player antes
    - two down cards + one up card on Third Street
    - lowest exposed card posts the bring-in
    - Fourth/Fifth/Sixth Streets are dealt face-up
    - Seventh Street is dealt face-down
    - small bet on Third/Fourth, big bet on Fifth/Sixth/Seventh
    """

    STUD_STAGES = (
        "third",
        "fourth",
        "fifth",
        "sixth",
        "seventh",
    )

    def __init__(self):
        super().__init__()

        self.ante_amount = 1
        self.bring_in_amount = 1
        self.small_bet = 2
        self.big_bet = 4

        self.bring_in_index = None
        self.third_street_completed = False

        # Standard fixed-limit structure: after a full opening wager,
        # allow up to three additional full raises in one betting round.
        self.raises_this_round = 0
        self.max_raises_per_round = 3

    # ==================================================
    # SESSION
    # ==================================================

    def start_session(self, npcs, starting_stack, ante):
        result = super().start_session(
            npcs,
            starting_stack,
            ante,
        )

        # main.py passes the same scalable poker base unit used by
        # the other variants. In Stud it becomes the small-bet unit.
        self.small_bet = max(
            2,
            int(ante),
        )

        self.big_bet = max(
            self.small_bet * 2,
            self.small_bet + 1,
        )

        self.ante_amount = max(
            1,
            int(round(self.small_bet * 0.20)),
        )

        self.bring_in_amount = max(
            1,
            int(round(self.small_bet * 0.50)),
        )

        self.bring_in_amount = min(
            self.small_bet,
            self.bring_in_amount,
        )

        # Keep these inherited denominations meaningful for generic
        # chip helpers and AI context.
        self.small_blind = self.small_bet
        self.big_blind = self.big_bet

        self.bring_in_index = None
        self.third_street_completed = False
        self.raises_this_round = 0

        return result

    # ==================================================
    # CARD / SEAT HELPERS
    # ==================================================

    def get_hand_deal_order(self):
        live = set(self.get_live_player_indexes())

        if not live:
            return []

        actor_count = len(self.npcs) + 1

        if self.dealer_index is None:
            start = 0
        else:
            start = (
                self.dealer_index + 1
            ) % actor_count

        order = []

        for offset in range(actor_count):
            seat = (
                start + offset
            ) % actor_count

            if seat in live:
                order.append(seat)

        return order

    def get_seat_hand(self, player_index):
        if player_index == 0:
            return self.player_hand

        npc_index = player_index - 1

        if not (
                0 <= npc_index < len(self.npc_hands)
        ):
            return []

        return self.npc_hands[npc_index]

    def _give_card_to_seat(self, player_index, card):
        if card is None:
            return

        if player_index == 0:
            self.player_hand.append(card)
            return

        npc_index = player_index - 1

        if 0 <= npc_index < len(self.npc_hands):
            self.npc_hands[npc_index].append(card)

    @staticmethod
    def is_stud_card_exposed(card_index):
        # Card order:
        # 0 down, 1 down, 2 up, 3 up, 4 up, 5 up, 6 down.
        return 2 <= int(card_index) <= 5

    def get_exposed_cards(self, player_index):
        hand = self.get_seat_hand(
            player_index
        )

        return [
            card
            for card_index, card
            in enumerate(hand)
            if (
                card is not None
                and self.is_stud_card_exposed(
                    card_index
                )
            )
        ]

    def get_all_visible_cards(
            self,
            exclude_player_index=None
    ):
        visible = []

        for player_index in range(
                len(self.npcs) + 1
        ):
            if (
                    exclude_player_index is not None
                    and player_index == exclude_player_index
            ):
                continue

            if player_index == 0:
                if self.player_folded:
                    continue
            else:
                npc_index = player_index - 1

                if (
                        npc_index < 0
                        or npc_index >= len(self.npc_folded)
                        or self.npc_folded[npc_index]
                ):
                    continue

            visible.extend(
                self.get_exposed_cards(
                    player_index
                )
            )

        return visible

    # ==================================================
    # FORCED WAGERS
    # ==================================================

    def post_ante(self, player_index):
        amount = max(
            0,
            int(self.ante_amount),
        )

        if amount <= 0:
            return 0

        if player_index == 0:
            paid = self.commit_player_chips(
                amount,
                count_round_bet=False,
                show_chunk=True,
            )

            if paid > 0:
                suffix = (
                    " and are all-in."
                    if self.player_all_in
                    else "."
                )

                self.log_hand_event(
                    "ante",
                    f"You ante ${paid:,}{suffix}",
                    actor_index=0,
                    amount=paid,
                    all_in=self.player_all_in,
                )

            return paid

        npc_index = player_index - 1

        if not (
                0 <= npc_index < len(self.npcs)
        ):
            return 0

        paid = self.commit_npc_chips(
            npc_index,
            amount,
            count_round_bet=False,
            show_chunk=True,
        )

        if paid > 0:
            name = self.get_table_player_name(
                player_index
            )

            suffix = (
                " and is all-in."
                if self.npc_all_in[npc_index]
                else "."
            )

            self.log_hand_event(
                "ante",
                f"{name} antes ${paid:,}{suffix}",
                actor_index=player_index,
                amount=paid,
                all_in=self.npc_all_in[npc_index],
            )

        return paid

    def get_bring_in_index(self):
        candidates = []

        for player_index in (
                self.get_active_player_indexes()
        ):
            hand = self.get_seat_hand(
                player_index
            )

            if len(hand) < 3:
                continue

            door_card = hand[2]

            candidates.append(
                (
                    RANK_VALUES[
                        door_card["rank"]
                    ],
                    SUIT_BRING_IN_ORDER.get(
                        door_card["suit"],
                        0,
                    ),
                    player_index,
                )
            )

        if not candidates:
            return None

        candidates.sort()

        return candidates[0][2]

    def post_bring_in(self, player_index):
        if player_index is None:
            return 0

        amount = max(
            1,
            int(self.bring_in_amount),
        )

        if player_index == 0:
            paid = self.commit_player_chips(
                amount,
                count_round_bet=True,
                show_chunk=True,
            )

            if paid <= 0:
                return 0

            self.player_has_acted = True
            self.player_action_text = (
                f"Bring-in ${paid:,}"
            )

            suffix = (
                " and are all-in."
                if self.player_all_in
                else "."
            )

            self.log_hand_event(
                "bring_in",
                f"You post the bring-in ${paid:,}{suffix}",
                actor_index=0,
                amount=paid,
                all_in=self.player_all_in,
            )

            return paid

        npc_index = player_index - 1

        if not (
                0 <= npc_index < len(self.npcs)
        ):
            return 0

        paid = self.commit_npc_chips(
            npc_index,
            amount,
            count_round_bet=True,
            show_chunk=True,
        )

        if paid <= 0:
            return 0

        self.npc_has_acted[
            npc_index
        ] = True

        self.npc_action_texts[
            npc_index
        ] = (
            f"Bring-in ${paid:,}"
        )

        name = self.get_table_player_name(
            player_index
        )

        suffix = (
            " and is all-in."
            if self.npc_all_in[npc_index]
            else "."
        )

        self.log_hand_event(
            "bring_in",
            f"{name} posts the bring-in ${paid:,}{suffix}",
            actor_index=player_index,
            amount=paid,
            all_in=self.npc_all_in[npc_index],
        )

        return paid

    # ==================================================
    # NEW HAND / THIRD STREET
    # ==================================================

    def start_hand(self):
        self.refresh_busted_state()

        if self.player_busted:
            self.hand_complete = True
            self.current_actor = -1
            self.current_stage = "busted"
            self.result_text = (
                "You are out of chips."
            )
            return False

        live_indexes = (
            self.get_live_player_indexes()
        )

        if len(live_indexes) < 2:
            self.hand_complete = True
            self.current_actor = -1
            self.current_stage = "showdown"
            self.result_text = (
                "The table has been cleared."
            )
            return False

        self.hand_seat_indexes = list(
            live_indexes
        )

        self.player_model.start_hand()

        self.hand_number += 1
        self.last_hand_busted_indexes = []

        self.hand_history.start_hand(
            self.hand_number,
            "Seven-Card Stud",
            stage="third",
        )

        self.build_deck()

        self.player_hand = []

        self.npc_hands = [
            []
            for _ in self.npcs
        ]

        self.community_cards = []

        self.pot = 0
        self.hand_complete = False
        self.winner_indexes = []
        self.result_text = ""
        self.last_pot_awards = []

        self.player_hand_contribution = 0

        self.npc_hand_contributions = [
            0
            for _ in self.npcs
        ]

        self.player_folded = False

        self.npc_folded = [
            busted
            for busted in self.npc_busted
        ]

        self.player_all_in = False

        self.npc_all_in = [
            False
            for _ in self.npcs
        ]

        # We retain a rotating dealing reference even though Stud
        # does not use a Hold'em-style dealer button for action.
        self.rotate_dealer()

        self.small_blind_index = None
        self.big_blind_index = None
        self.bring_in_index = None
        self.third_street_completed = False

        self.current_stage = "third"

        self.reset_betting_round(
            assign_actor=False
        )

        # Everyone at the table antes.
        for player_index in live_indexes:
            self.post_ante(
                player_index
            )

        # Deal one card at a time, beginning left of the rotating
        # dealing reference. First two are down; third is the door card.
        deal_order = (
            self.get_hand_deal_order()
        )

        for _ in range(3):
            for player_index in deal_order:
                self._give_card_to_seat(
                    player_index,
                    self.draw_card(),
                )

        if len(self.player_hand) >= 3:
            self.log_hand_event(
                "third_street",
                (
                    "Third Street: you receive "
                    f"{format_poker_cards(self.player_hand[:2])} "
                    f"down / {format_poker_card(self.player_hand[2])} up."
                ),
                actor_index=0,
                cards=[
                    dict(card)
                    for card in self.player_hand
                    if card
                ],
            )

        # Lowest door card is forced to post the bring-in.
        self.bring_in_index = (
            self.get_bring_in_index()
        )

        if self.bring_in_index is None:
            return False

        bring_in_paid = self.post_bring_in(
            self.bring_in_index
        )

        # Preserve the nominal bring-in even if that seat could only
        # post a short all-in amount.
        self.current_bet = max(
            1,
            self.bring_in_amount,
        )

        self.third_street_completed = (
            self.current_bet
            >= self.small_bet
        )

        self.last_raise_size = max(
            1,
            self.small_bet
            - self.bring_in_amount,
        )

        self.last_raiser = None

        actor_count = len(self.npcs) + 1

        first_after_bring_in = (
            self.bring_in_index + 1
        ) % actor_count

        self.set_first_actor_from(
            first_after_bring_in
        )

        # If everyone except one player is already all-in from antes,
        # the scheduler can immediately run out the remaining streets.
        if self.is_betting_round_complete():
            self.current_actor = -1

        return bring_in_paid >= 0

    # ==================================================
    # STUD STREET / ACTION ORDER
    # ==================================================

    def get_street_bet_size(self):
        if self.current_stage in (
                "third",
                "fourth",
        ):
            return max(
                1,
                self.small_bet,
            )

        return max(
            1,
            self.big_bet,
        )

    def _exposed_hand_score(self, player_index):
        cards = self.get_exposed_cards(
            player_index
        )

        if not cards:
            return (
                0,
                0,
            )

        values = sorted(
            (
                RANK_VALUES[
                    card["rank"]
                ]
                for card in cards
            ),
            reverse=True,
        )

        counts = Counter(values)

        groups = sorted(
            (
                (count, rank)
                for rank, count
                in counts.items()
            ),
            reverse=True,
        )

        # With at most four exposed cards, rank-group structure is
        # what determines the visible poker hand.
        if groups[0][0] == 4:
            return (
                5,
                groups[0][1],
            )

        if groups[0][0] == 3:
            kickers = sorted(
                (
                    rank
                    for rank in values
                    if rank != groups[0][1]
                ),
                reverse=True,
            )

            return (
                4,
                groups[0][1],
                *kickers,
            )

        pairs = sorted(
            (
                rank
                for rank, count
                in counts.items()
                if count == 2
            ),
            reverse=True,
        )

        if len(pairs) >= 2:
            kickers = sorted(
                (
                    rank
                    for rank in values
                    if rank not in pairs[:2]
                ),
                reverse=True,
            )

            return (
                3,
                pairs[0],
                pairs[1],
                *kickers,
            )

        if pairs:
            kickers = sorted(
                (
                    rank
                    for rank in values
                    if rank != pairs[0]
                ),
                reverse=True,
            )

            return (
                2,
                pairs[0],
                *kickers,
            )

        return (
            1,
            *values,
        )

    def get_street_first_actor_index(self):
        candidates = []

        for player_index in (
                self.get_active_player_indexes()
        ):
            if player_index == 0:
                stack = self.player_stack
            else:
                stack = self.npc_stacks[
                    player_index - 1
                ]

            if stack <= 0:
                continue

            candidates.append(
                player_index
            )

        if not candidates:
            return None

        actor_count = len(self.npcs) + 1

        # Tied visible hands are resolved by clockwise position from
        # the rotating dealing reference.
        dealer = (
            self.dealer_index
            if self.dealer_index is not None
            else -1
        )

        return max(
            candidates,
            key=lambda player_index: (
                self._exposed_hand_score(
                    player_index
                ),
                -(
                    (
                        player_index
                        - dealer
                    )
                    % actor_count
                ),
            ),
        )

    def deal_next_street(self):
        next_stage_by_stage = {
            "third": "fourth",
            "fourth": "fifth",
            "fifth": "sixth",
            "sixth": "seventh",
        }

        next_stage = next_stage_by_stage.get(
            self.current_stage
        )

        if next_stage is None:
            return False

        active_indexes = (
            self.get_active_player_indexes()
        )

        if len(active_indexes) <= 1:
            if active_indexes:
                return self.award_pot_to_single_player(
                    active_indexes[0]
                )

            return False

        # Deal to every player still entitled to showdown cards,
        # including all-in players.
        actor_count = len(self.npcs) + 1

        if self.dealer_index is None:
            deal_start = 0
        else:
            deal_start = (
                self.dealer_index + 1
            ) % actor_count

        active_set = set(
            active_indexes
        )

        deal_order = []

        for offset in range(actor_count):
            player_index = (
                deal_start + offset
            ) % actor_count

            if player_index in active_set:
                deal_order.append(
                    player_index
                )

        newly_dealt = {}

        for player_index in deal_order:
            card = self.draw_card()

            self._give_card_to_seat(
                player_index,
                card,
            )

            newly_dealt[
                player_index
            ] = card

        self.current_stage = next_stage

        street_names = {
            "fourth": "Fourth Street",
            "fifth": "Fifth Street",
            "sixth": "Sixth Street",
            "seventh": "Seventh Street",
        }

        street_name = street_names[
            next_stage
        ]

        self.log_hand_event(
            "street",
            f"{street_name}.",
            street=next_stage,
        )

        # Fourth through Sixth are public. Seventh is down.
        if next_stage != "seventh":
            for player_index in deal_order:
                card = newly_dealt.get(
                    player_index
                )

                if card is None:
                    continue

                name = self.get_table_player_name(
                    player_index
                )

                if player_index == 0:
                    text = (
                        f"You receive "
                        f"{format_poker_card(card)} face-up."
                    )
                else:
                    text = (
                        f"{name} receives "
                        f"{format_poker_card(card)} face-up."
                    )

                self.log_hand_event(
                    "upcard",
                    text,
                    actor_index=player_index,
                    cards=[dict(card)],
                    street=next_stage,
                )

        else:
            player_card = newly_dealt.get(
                0
            )

            if player_card is not None:
                self.log_hand_event(
                    "downcard",
                    (
                        "You receive "
                        f"{format_poker_card(player_card)} face-down."
                    ),
                    actor_index=0,
                    cards=[dict(player_card)],
                    street=next_stage,
                )

            self.log_hand_event(
                "downcards",
                "Remaining players receive their final card face-down.",
                street=next_stage,
            )

        first_actor = (
            self.get_street_first_actor_index()
        )

        self.reset_betting_round(
            first_actor=first_actor,
            assign_actor=True,
        )

        return True

    def advance_after_betting_round(self):
        if not self.is_betting_round_complete():
            return False

        if self.current_stage in (
                "third",
                "fourth",
                "fifth",
                "sixth",
        ):
            return self.deal_next_street()

        if self.current_stage == "seventh":
            return self.showdown()

        return False

    def resolve_after_fold(self):
        if self.hand_complete:
            return False

        active_indexes = (
            self.get_active_player_indexes()
        )

        if not active_indexes:
            return False

        if len(active_indexes) == 1:
            return self.award_pot_to_single_player(
                active_indexes[0]
            )

        if (
                self.player_folded
                and self.current_actor == 0
        ):
            self.advance_to_next_actor()

        return True

    # ==================================================
    # FIXED-LIMIT BETTING
    # ==================================================

    def reset_betting_round(
            self,
            first_actor=None,
            assign_actor=True
    ):
        super().reset_betting_round(
            first_actor=first_actor,
            assign_actor=assign_actor,
        )

        self.raises_this_round = 0

    def get_minimum_open_bet(self):
        return self.get_street_bet_size()

    def get_minimum_raise_size(self):
        street_bet = (
            self.get_street_bet_size()
        )

        # Third Street begins with a partial bring-in. Completing it
        # to the small bet is the first full wager.
        if (
                self.current_stage == "third"
                and not self.third_street_completed
        ):
            return max(
                1,
                self.small_bet
                - self.bring_in_amount,
            )

        return street_bet

    def get_minimum_raise_to(self):
        if self.current_bet <= 0:
            return self.get_minimum_open_bet()

        street_bet = (
            self.get_street_bet_size()
        )

        if (
                self.current_stage == "third"
                and self.current_bet < street_bet
        ):
            return street_bet

        return (
            self.current_bet
            + street_bet
        )

    def get_player_fixed_bet_or_raise_to(self):
        if self.current_bet <= 0:
            return min(
                self.player_stack,
                self.get_minimum_open_bet(),
            )

        target = self.get_minimum_raise_to()

        return min(
            self.get_player_maximum_raise_to(),
            target,
        )

    def can_player_raise(self):
        if (
                self.raises_this_round
                >= self.max_raises_per_round
        ):
            return False

        return super().can_player_raise()

    def can_npc_raise(self, npc_index):
        if (
                self.raises_this_round
                >= self.max_raises_per_round
        ):
            return False

        return super().can_npc_raise(
            npc_index
        )

    def player_raise(self, raise_to):
        old_current_bet = self.current_bet
        old_street_bet = (
            self.get_street_bet_size()
        )

        success = super().player_raise(
            raise_to
        )

        completed_bring_in = (
            success
            and self.current_stage == "third"
            and old_current_bet < old_street_bet
            and self.current_bet >= old_street_bet
        )

        if completed_bring_in:
            self.third_street_completed = True

        if (
                success
                and self.current_bet
                > old_current_bet
                and not completed_bring_in
        ):
            self.raises_this_round += 1

        return success

    def npc_raise(self, npc_index, raise_to):
        old_current_bet = self.current_bet
        old_street_bet = (
            self.get_street_bet_size()
        )

        success = super().npc_raise(
            npc_index,
            raise_to,
        )

        completed_bring_in = (
            success
            and self.current_stage == "third"
            and old_current_bet < old_street_bet
            and self.current_bet >= old_street_bet
        )

        if completed_bring_in:
            self.third_street_completed = True

        if (
                success
                and self.current_bet
                > old_current_bet
                and not completed_bring_in
        ):
            self.raises_this_round += 1

        return success

    def get_npc_stage_bet_cap(self, npc_index):
        if not (
                0 <= npc_index < len(self.npc_stacks)
        ):
            return 0

        maximum_total = (
            self.npc_round_bets[npc_index]
            + self.npc_stacks[npc_index]
        )

        if self.current_bet <= 0:
            target = (
                self.npc_round_bets[npc_index]
                + self.get_minimum_open_bet()
            )
        else:
            target = self.get_minimum_raise_to()

        return min(
            maximum_total,
            target,
        )

    def get_npc_open_bet_amount(
            self,
            npc_index,
            strength,
            profile,
            bluff=False
    ):
        del strength, profile, bluff

        if not (
                0 <= npc_index < len(self.npc_stacks)
        ):
            return None

        return min(
            self.npc_stacks[npc_index],
            self.get_minimum_open_bet(),
        )

    def get_npc_raise_to_amount(
            self,
            npc_index,
            strength,
            profile,
            bluff=False
    ):
        del strength, profile, bluff

        if not self.can_npc_raise(
                npc_index
        ):
            return None

        maximum_raise_to = (
            self.npc_round_bets[npc_index]
            + self.npc_stacks[npc_index]
        )

        target = self.get_minimum_raise_to()

        if maximum_raise_to <= self.current_bet:
            return None

        return min(
            target,
            maximum_raise_to,
        )

    # ==================================================
    # STUD-AWARE AI
    # ==================================================

    def build_npc_ai_context(
            self,
            npc_index,
            strength=None
    ):
        context = super().build_npc_ai_context(
            npc_index,
            strength=strength,
        )

        context["game"] = "seven_card_stud"
        context["stage"] = self.current_stage
        context["position"] = "unknown"
        context["fixed_limit"] = True
        context["street_bet"] = (
            self.get_street_bet_size()
        )
        context["raises_remaining"] = max(
            0,
            self.max_raises_per_round
            - self.raises_this_round,
        )

        player_index = npc_index + 1

        context["exposed_cards"] = [
            dict(card)
            for card in self.get_exposed_cards(
                player_index
            )
        ]

        context["visible_cards"] = [
            dict(card)
            for card in self.get_all_visible_cards(
                exclude_player_index=player_index
            )
        ]

        return context

    def _visible_threat_penalty(self, npc_index):
        player_index = npc_index + 1
        penalty = 0.0

        for opponent_index in (
                self.get_active_player_indexes()
        ):
            if opponent_index == player_index:
                continue

            exposed = self.get_exposed_cards(
                opponent_index
            )

            if not exposed:
                continue

            counts = Counter(
                RANK_VALUES[card["rank"]]
                for card in exposed
            )

            max_count = max(
                counts.values(),
                default=1,
            )

            if max_count >= 3:
                penalty = max(
                    penalty,
                    0.10,
                )

            elif max_count == 2:
                penalty = max(
                    penalty,
                    0.055,
                )

        return penalty

    def _dead_card_adjustment(
            self,
            npc_index,
            hand
    ):
        if not hand:
            return 0.0

        player_index = npc_index + 1

        visible_elsewhere = (
            self.get_all_visible_cards(
                exclude_player_index=player_index
            )
        )

        adjustment = 0.0

        own_rank_counts = Counter(
            card["rank"]
            for card in hand
        )

        # If an NPC owns a pair/trips but matching ranks are visibly
        # dead around the table, reduce the value of improving that hand.
        for rank, count in own_rank_counts.items():
            if count < 2:
                continue

            dead_same_rank = sum(
                1
                for card in visible_elsewhere
                if card["rank"] == rank
            )

            adjustment -= (
                0.022
                * dead_same_rank
            )

        own_suit_counts = Counter(
            card["suit"]
            for card in hand
        )

        best_suit, best_suit_count = max(
            own_suit_counts.items(),
            key=lambda item: item[1],
        )

        if best_suit_count >= 3:
            dead_same_suit = sum(
                1
                for card in visible_elsewhere
                if card["suit"] == best_suit
            )

            # Seeing many cards of the suit we still need makes a
            # developing flush meaningfully less attractive.
            adjustment -= min(
                0.075,
                0.010 * dead_same_suit,
            )

        return adjustment

    def get_npc_hand_strength(self, npc_index):
        if not (
                0 <= npc_index < len(self.npc_hands)
        ):
            return 0.0

        hand = self.npc_hands[
            npc_index
        ]

        if len(hand) < 3:
            return 0.0

        values = [
            RANK_VALUES[
                card["rank"]
            ]
            for card in hand
        ]

        counts = Counter(values)

        pair_ranks = sorted(
            (
                rank
                for rank, count
                in counts.items()
                if count == 2
            ),
            reverse=True,
        )

        trips = sorted(
            (
                rank
                for rank, count
                in counts.items()
                if count == 3
            ),
            reverse=True,
        )

        quads = sorted(
            (
                rank
                for rank, count
                in counts.items()
                if count == 4
            ),
            reverse=True,
        )

        if len(hand) >= 5:
            result = self.evaluate_best_hand(
                hand
            )

            if result is None:
                strength = 0.20
            else:
                score = result[0]
                category = score[0]

                category_strengths = {
                    0: 0.18,
                    1: 0.42,
                    2: 0.61,
                    3: 0.72,
                    4: 0.81,
                    5: 0.86,
                    6: 0.93,
                    7: 0.985,
                    8: 1.00,
                }

                strength = (
                    category_strengths.get(
                        category,
                        0.20,
                    )
                )

                if (
                        len(score) >= 2
                        and isinstance(
                            score[1],
                            int,
                        )
                ):
                    strength += (
                        score[1]
                        / 14.0
                        * 0.045
                    )

        else:
            high_rank = max(
                values
            )

            if quads:
                strength = 0.98

            elif trips:
                strength = (
                    0.69
                    + trips[0]
                    / 14.0
                    * 0.055
                )

            elif len(pair_ranks) >= 2:
                strength = (
                    0.60
                    + pair_ranks[0]
                    / 14.0
                    * 0.045
                )

            elif pair_ranks:
                strength = (
                    0.42
                    + pair_ranks[0]
                    / 14.0
                    * 0.065
                )

            else:
                strength = (
                    0.15
                    + high_rank
                    / 14.0
                    * 0.16
                )

            suit_counts = Counter(
                card["suit"]
                for card in hand
            )

            best_suit_count = max(
                suit_counts.values(),
                default=1,
            )

            if best_suit_count >= 3:
                strength += 0.035

            unique_values = sorted(
                set(values)
            )

            # A compact straight-potential bump.
            if len(unique_values) >= 3:
                span = (
                    max(unique_values)
                    - min(unique_values)
                )

                if span <= 4:
                    strength += 0.035

        strength += self._dead_card_adjustment(
            npc_index,
            hand,
        )

        strength -= self._visible_threat_penalty(
            npc_index
        )

        return max(
            0.0,
            min(
                strength,
                1.0,
            ),
        )

    # ==================================================
    # SHOWDOWN
    # ==================================================

    def showdown(self):
        active_indexes = (
            self.get_active_player_indexes()
        )

        if not active_indexes:
            return False

        if len(active_indexes) == 1:
            return self.award_pot_to_single_player(
                active_indexes[0]
            )

        results = {}

        for player_index in active_indexes:
            result = self.get_showdown_result(
                player_index
            )

            if result is not None:
                results[
                    player_index
                ] = result

        if not results:
            return False

        self.log_hand_event(
            "showdown",
            "Showdown.",
        )

        for player_index, result in results.items():
            cards = self.get_seat_hand(
                player_index
            )

            if player_index == 0:
                prefix = "You show"
            else:
                prefix = (
                    f"{self.get_table_player_name(player_index)} "
                    f"shows"
                )

            category = HAND_NAMES[
                result[0][0]
            ]

            hand_detail = describe_poker_score(
                result[0],
                compact=True,
            )

            self.log_hand_event(
                "showdown_hand",
                (
                    f"{prefix} "
                    f"{format_poker_cards(cards)} "
                    f"({hand_detail})."
                ),
                actor_index=player_index,
                cards=[
                    dict(card)
                    for card in cards
                    if card
                ],
                hand_name=category,
                hand_detail=hand_detail,
            )

        side_pots = (
            self.build_side_pots()
        )

        payout_totals = {
            player_index: 0
            for player_index
            in results
        }

        self.last_pot_awards = []

        for pot_data in side_pots:
            pot_amount = (
                pot_data["amount"]
            )

            eligible = [
                player_index
                for player_index
                in pot_data["eligible"]
                if player_index in results
            ]

            if not eligible:
                continue

            best_score = max(
                results[player_index][0]
                for player_index in eligible
            )

            winners = [
                player_index
                for player_index in eligible
                if (
                    results[player_index][0]
                    == best_score
                )
            ]

            if not winners:
                continue

            actor_count = len(self.npcs) + 1

            dealer = (
                self.dealer_index
                if self.dealer_index is not None
                else -1
            )

            winners.sort(
                key=lambda index: (
                    index - dealer
                ) % actor_count
            )

            share = (
                pot_amount
                // len(winners)
            )

            remainder = (
                pot_amount
                % len(winners)
            )

            for winner_order, winner_index in enumerate(
                    winners
            ):
                winnings = share

                if winner_order < remainder:
                    winnings += 1

                self.award_chips_to_player(
                    winner_index,
                    winnings,
                )

                payout_totals[
                    winner_index
                ] += winnings

            self.last_pot_awards.append(
                {
                    "amount": pot_amount,
                    "winners": winners.copy(),
                    "share": share,
                    "remainder": remainder,
                }
            )

        self.winner_indexes = sorted(
            [
                player_index
                for player_index, winnings
                in payout_totals.items()
                if winnings > 0
            ]
        )

        payout_winners = [
            player_index
            for player_index
            in self.winner_indexes
            if payout_totals.get(
                player_index,
                0,
            ) > 0
        ]

        if len(payout_winners) == 1:
            winner_index = (
                payout_winners[0]
            )

            winnings = (
                payout_totals[
                    winner_index
                ]
            )

            category = HAND_NAMES[
                results[
                    winner_index
                ][0][0]
            ]

            hand_detail = describe_poker_score(
                results[winner_index][0],
                compact=True,
            )

            if winner_index == 0:
                self.result_text = (
                    f"You win ${winnings:,} "
                    f"with {hand_detail}!"
                )
            else:
                winner_name = (
                    self.get_table_player_name(
                        winner_index
                    )
                )

                self.result_text = (
                    f"{winner_name} wins "
                    f"${winnings:,} with "
                    f"{hand_detail}."
                )

        else:
            payout_parts = []

            for player_index in payout_winners:
                payout_parts.append(
                    f"{self.get_table_player_name(player_index)} "
                    f"${payout_totals[player_index]:,}"
                )

            self.result_text = (
                "Payouts: "
                + "; ".join(
                    payout_parts
                )
                + "."
            )

        if len(self.last_pot_awards) > 1:
            for pot_index, pot_award in enumerate(
                    self.last_pot_awards
            ):
                pot_label = (
                    "Main pot"
                    if pot_index == 0
                    else f"Side pot {pot_index}"
                )

                pot_amount = int(
                    pot_award.get(
                        "amount",
                        0,
                    )
                )

                winners = list(
                    pot_award.get(
                        "winners",
                        [],
                    )
                )

                winner_names = [
                    self.get_table_player_name(
                        index
                    )
                    for index in winners
                ]

                if len(winner_names) == 1:
                    award_text = (
                        f"{pot_label} ${pot_amount:,}: "
                        f"{winner_names[0]} wins."
                    )
                else:
                    award_text = (
                        f"{pot_label} ${pot_amount:,}: "
                        f"split between "
                        f"{', '.join(winner_names)}."
                    )

                self.log_hand_event(
                    "pot_award",
                    award_text,
                    amount=pot_amount,
                    winners=winners,
                    pot_index=pot_index,
                )

        self.log_hand_event(
            "result",
            self.result_text,
            winners=self.winner_indexes.copy(),
            payouts={
                player_index: amount
                for player_index, amount
                in payout_totals.items()
                if amount > 0
            },
        )

        self.pot = 0
        self.hand_complete = True
        self.current_actor = -1
        self.current_stage = "showdown"

        newly_busted = (
            self.refresh_busted_state()
        )

        self.log_newly_busted_players(
            newly_busted
        )

        return True

    def get_player_hand_name(self):
        if len(self.player_hand) < 5:
            return ""

        result = self.evaluate_best_hand(
            self.player_hand
        )

        if result is None:
            return ""

        return HAND_NAMES[
            result[0][0]
        ]

    def get_npc_hand_name(self, npc_index):
        if not (
                0 <= npc_index < len(self.npc_hands)
        ):
            return ""

        hand = self.npc_hands[
            npc_index
        ]

        if len(hand) < 5:
            return ""

        result = self.evaluate_best_hand(
            hand
        )

        if result is None:
            return ""

        return HAND_NAMES[
            result[0][0]
        ]
