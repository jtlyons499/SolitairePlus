"""Hold'em NPCs: NPC bets, raises, checks, folds and calls, personality, hand strength and
bet sizing (a mixin of holdem.TexasHoldemGame; Draw and Stud inherit it).

run_next_npc_action, which asks ai.decide_poker_action for the NPC's choice, stays in
holdem.py (tests patch holdem.decide_poker_action).
"""
from solitaireplus.games.poker.quick_chat import get_npc_quick_chat_context
from solitaireplus.games.poker.npc_inputs import (
    grudge_seats,
    npc_decision_inputs,
    opponent_rows,
    soft_bet_cap,
    table_identities,
    wealth_pressure,
)
from solitaireplus.games.poker.core import (
    RANK_VALUES,
    betting_reopened,
    can_raise,
)
from solitaireplus.games.poker.ai import (
    choose_poker_open_bet_amount,
    choose_poker_raise_to_amount,
    get_effective_poker_personality,
    get_poker_personality,
    get_poker_personality_profile,
    get_poker_skill_factor,
)


class NpcMixin:
    # ==================================================
    # BETTING HELPERS
    # ==================================================
    def npc_raise(
            self,
            npc_index,
            raise_to
    ):

        self.ensure_npc_bet_chunk_state()
        self.ensure_npc_action_state()
        self.last_wager_full = False

        if not (
                0
                <= npc_index
                < len(self.npcs)
        ):
            return False

        if (
                self.npc_busted[npc_index]
                or self.npc_folded[npc_index]
                or self.npc_all_in[npc_index]
        ):
            return False

        if self.current_bet <= 0:
            return False

        stack = (
            self.npc_stacks[
                npc_index
            ]
        )

        if stack <= 0:
            return False

        maximum_raise_to = (
                self.npc_round_bets[
                    npc_index
                ]
                + stack
        )

        minimum_raise_to = (
            self.get_minimum_raise_to()
        )

        raise_to = int(
            raise_to
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

        # B36: a raise needs somebody left to respond (and an open
        # betting round). A short stack's all-in call is still allowed.
        if (
                target > self.current_bet
                and not self.can_npc_raise(npc_index)
        ):
            return False

        old_current_bet = (
            self.current_bet
        )

        amount_needed = (
                target
                - self.npc_round_bets[
                    npc_index
                ]
        )

        if amount_needed <= 0:
            return False

        amount_paid = (
            self.commit_npc_chips(
                npc_index,
                amount_needed
            )
        )

        if amount_paid <= 0:
            return False

        self.apply_wager(
            npc_index + 1,
            old_current_bet,
            self.npc_round_bets[npc_index],
            self.get_minimum_raise_size()
        )

        self.npc_has_acted[
            npc_index
        ] = True

        self.npc_action_texts[
            npc_index
        ] = (
            f"Raised to "
            f"${self.npc_round_bets[npc_index]:,}"
        )

        name = self.get_table_player_name(
            npc_index + 1
        )

        suffix = (
            " and is all-in."
            if self.npc_all_in[npc_index]
            else "."
        )

        self.log_hand_event(
            "raise",
            (
                f"{name} raises to "
                f"${self.npc_round_bets[npc_index]:,}"
                f"{suffix}"
            ),
            actor_index=npc_index + 1,
            amount=amount_paid,
            raise_to=self.npc_round_bets[npc_index],
            all_in=self.npc_all_in[npc_index]
        )

        return True

    def npc_bet(
            self,
            npc_index,
            amount
    ):

        self.ensure_npc_bet_chunk_state()
        self.ensure_npc_action_state()
        self.last_wager_full = False

        if not (
                0
                <= npc_index
                < len(self.npcs)
        ):
            return False

        if self.current_bet > 0:
            return False

        if (
                self.npc_busted[npc_index]
                or self.npc_folded[npc_index]
                or self.npc_all_in[npc_index]
        ):
            return False

        stack = (
            self.npc_stacks[
                npc_index
            ]
        )

        if stack <= 0:
            return False

        # B36: a bet needs somebody left to respond.
        if not self.can_npc_raise(npc_index):
            return False

        amount = int(
            amount
        )

        minimum_bet = (
            self.get_minimum_open_bet()
        )

        if (
                amount < minimum_bet
                and amount < stack
        ):
            return False

        target_amount = min(
            max(
                1,
                amount
            ),
            stack
        )

        old_current_bet = (
            self.current_bet
        )

        amount_paid = (
            self.commit_npc_chips(
                npc_index,
                target_amount
            )
        )

        if amount_paid <= 0:
            return False

        self.apply_wager(
            npc_index + 1,
            old_current_bet,
            self.npc_round_bets[npc_index],
            minimum_bet
        )

        self.npc_has_acted[
            npc_index
        ] = True

        self.npc_action_texts[
            npc_index
        ] = (
            f"Bet ${amount_paid:,}"
        )

        name = self.get_table_player_name(
            npc_index + 1
        )

        suffix = (
            " and is all-in."
            if self.npc_all_in[npc_index]
            else "."
        )

        self.log_hand_event(
            "bet",
            f"{name} bets ${amount_paid:,}{suffix}",
            actor_index=npc_index + 1,
            amount=amount_paid,
            all_in=self.npc_all_in[npc_index]
        )

        return True

    def get_npc_amount_to_call(
            self,
            npc_index
    ):

        if not (
                0
                <= npc_index
                < len(self.npc_stacks)
        ):
            return 0

        return max(
            0,
            self.current_bet
            - self.npc_round_bets[
                npc_index
            ]
        )

    def npc_check(
            self,
            npc_index
    ):

        if self.npc_folded[npc_index]:
            return False

        if (
                self.npc_all_in[npc_index]
                and self.npc_stacks[npc_index] <= 0
        ):
            return False

        if (
                self.get_npc_amount_to_call(
                    npc_index
                )
                != 0
        ):
            return False

        self.npc_has_acted[
            npc_index
        ] = True

        self.npc_action_texts[
            npc_index
        ] = "Checked"

        name = self.get_table_player_name(
            npc_index + 1
        )

        self.log_hand_event(
            "check",
            f"{name} checks.",
            actor_index=npc_index + 1
        )

        return True

    def npc_fold(
            self,
            npc_index
    ):

        self.ensure_npc_action_state()

        if self.npc_folded[npc_index]:
            return False

        if (
                self.npc_all_in[npc_index]
                and self.npc_stacks[npc_index] <= 0
        ):
            return False

        self.npc_folded[
            npc_index
        ] = True

        self.npc_has_acted[
            npc_index
        ] = True

        self.npc_action_texts[
            npc_index
        ] = "Folded"

        name = self.get_table_player_name(
            npc_index + 1
        )

        self.log_hand_event(
            "fold",
            f"{name} folds.",
            actor_index=npc_index + 1
        )

        # ==================================================
        # If this fold leaves only one player,
        # award the pot immediately.
        # ==================================================

        active_indexes = (
            self.get_active_player_indexes()
        )

        if len(active_indexes) == 1:
            self.award_pot_to_single_player(
                active_indexes[0]
            )
        else:
            self.settle_bet_to_match()

        return True

    def npc_call(
            self,
            npc_index
    ):

        self.ensure_npc_action_state()
        self.ensure_npc_bet_chunk_state()

        if not (
                0
                <= npc_index
                < len(self.npcs)
        ):
            return False

        if (
                self.npc_busted[npc_index]
                or self.npc_folded[npc_index]
                or self.npc_all_in[npc_index]
        ):
            return False

        amount_to_call = (
            self.get_npc_amount_to_call(
                npc_index
            )
        )

        if amount_to_call <= 0:
            return False

        amount_paid = (
            self.commit_npc_chips(
                npc_index,
                amount_to_call
            )
        )

        if amount_paid <= 0:
            return False

        self.npc_has_acted[
            npc_index
        ] = True

        self.npc_action_texts[
            npc_index
        ] = (
            f"Called ${amount_paid:,}"
        )

        name = self.get_table_player_name(
            npc_index + 1
        )

        suffix = (
            " and is all-in."
            if self.npc_all_in[npc_index]
            else "."
        )

        self.log_hand_event(
            "call",
            f"{name} calls ${amount_paid:,}{suffix}",
            actor_index=npc_index + 1,
            amount=amount_paid,
            all_in=self.npc_all_in[npc_index]
        )

        return True

    # ==================================================
    # NPC BETTING LOOP
    # ==================================================

    # ==================================================
    # NPC PERSONALITY HELPERS
    # ==================================================

    def get_npc_personality(
            self,
            npc_index
    ):

        if not (
                0
                <= npc_index
                < len(self.npcs)
        ):
            return "balanced"

        return get_poker_personality(
            self.npcs[npc_index]
        )

    def get_npc_effective_personality(
            self,
            npc_index
    ):

        return get_effective_poker_personality(
            self.get_npc_personality(
                npc_index
            )
        )

    def get_npc_personality_profile(
            self,
            npc_index
    ):

        if not 0 <= npc_index < len(self.npcs):
            return "balanced", get_poker_personality_profile("balanced")

        effective_personality = (
            self.get_npc_effective_personality(
                npc_index
            )
        )

        return (
            effective_personality,
            get_poker_personality_profile(self.npcs[npc_index])
        )

    def get_npc_skill_factor(
            self,
            npc_index
    ):

        if not (
                0
                <= npc_index
                < len(self.npcs)
        ):
            return 0.55

        return get_poker_skill_factor(
            self.npcs[npc_index], self.rating_game_key
        )

    def get_poker_position_label(
            self,
            player_index
    ):

        if player_index == self.dealer_index:
            return "button"

        if player_index == self.small_blind_index:
            return "small_blind"

        if player_index == self.big_blind_index:
            return "big_blind"

        hand_indexes = list(
            self.hand_seat_indexes
        )

        if not hand_indexes:
            hand_indexes = (
                self.get_live_player_indexes()
            )

        if player_index not in hand_indexes:
            return "unknown"

        if self.big_blind_index is None:
            return "unknown"

        actor_count = len(self.npcs) + 1

        non_blind_indexes = [
            index
            for index in hand_indexes
            if index not in (
                self.dealer_index,
                self.small_blind_index,
                self.big_blind_index,
            )
        ]

        non_blind_indexes.sort(
            key=lambda index: (
                index
                - self.big_blind_index
            ) % actor_count
        )

        if player_index not in non_blind_indexes:
            return "unknown"

        if len(non_blind_indexes) == 1:
            return "early"

        if player_index == non_blind_indexes[-1]:
            return "cutoff"

        if player_index == non_blind_indexes[0]:
            return "early"

        return "middle"

    def build_npc_ai_context(
            self,
            npc_index,
            strength=None
    ):

        if strength is None:
            strength = (
                self.get_npc_hand_strength(
                    npc_index
                )
            )

        stack = self.npc_stacks[npc_index]
        current_round_bet = (
            self.npc_round_bets[npc_index]
        )

        maximum_raise_to = (
            current_round_bet
            + stack
        )

        minimum_raise_to = (
            self.get_minimum_raise_to()
        )

        stage_cap = (
            self.get_npc_stage_bet_cap(
                npc_index
            )
        )

        soft_maximum_raise_to = min(
            maximum_raise_to,
            stage_cap
        )

        active_indexes = (
            self.get_active_player_indexes()
        )

        context = {
            "game": "texas_holdem",
            "stage": self.current_stage,
            "position": self.get_poker_position_label(
                npc_index + 1
            ),
            "hand_strength": strength,
            "pot": self.pot,
            "amount_to_call": self.get_npc_amount_to_call(
                npc_index
            ),
            "stack": stack,
            "current_bet": self.current_bet,
            "current_round_bet": current_round_bet,
            "minimum_open_bet": self.get_minimum_open_bet(),
            "maximum_open_bet": min(
                stack,
                stage_cap
            ),
            "minimum_raise_size": self.get_minimum_raise_size(),
            "minimum_raise_to": minimum_raise_to,
            "maximum_raise_to": maximum_raise_to,
            "soft_maximum_raise_to": soft_maximum_raise_to,
            "can_raise": self.can_npc_raise(
                npc_index
            ),
            "players_remaining": len(
                active_indexes
            ),
            "opponents_remaining": max(
                0,
                len(active_indexes) - 1
            ),
            "last_raiser": self.last_raiser,
            "last_raiser_is_player": (
                self.last_raiser == 0
            ),
        }

        # The inputs every poker variant shares: traits, skill, cash on
        # hand, table reads, player tendencies and grudges.
        context.update(npc_decision_inputs(
            npc=self.npcs[npc_index],
            seat=npc_index + 1,
            rating_game_key=self.rating_game_key,
            stack=stack,
            starting_stack=self.starting_stack,
            hand_number=self.hand_number,
            opponents=self.get_npc_opponent_rows(npc_index),
            last_raiser=self.last_raiser,
            grudge_memory=self.personality_memory,
            table_reads=self.table_reads,
            player_model=self.player_model,
            player_active=(
                not self.player_busted
                and not self.player_folded
            ),
            wealth_scale=self.get_npc_wealth_scale(),
        ))
        context["skill_factor"] = self.get_npc_skill_factor(
            npc_index
        )

        if self.quick_chat_enabled:
            context.update(get_npc_quick_chat_context(self, npc_index))

        return context

    def get_npc_wealth_scale(self):
        """How much of the shared wealth pressure this variant uses (1.0 in Hold'em)."""

        return 1.0

    # ==================================================
    # NPC HAND STRENGTH
    #
    # Returns roughly:
    #
    # 0.00 = garbage
    # 0.25 = weak
    # 0.50 = decent
    # 0.75 = strong
    # 1.00 = monster
    # ==================================================

    def get_npc_opponent_rows(self, npc_index):
        """Public rows (npc_inputs.opponent_rows) for every other seat in the hand."""
        seat = npc_index + 1
        active = self.get_active_player_indexes()
        names = {
            other: self.get_table_player_name(other)
            for other in active if other != seat
        }
        return opponent_rows(seat, active, names, table_identities(self.npcs),
                             self.seat_stacks(), self.seat_round_bets())

    def get_npc_grudge_context(self, npc_index):
        return self.personality_memory.context(self.npcs[npc_index], npc_index + 1,
                                              self.get_npc_opponent_rows(npc_index),
                                              self.last_raiser, self.hand_number)

    def record_personality_showdown(self, results):
        """Only resent an opponent who actually beat this NPC in a contested pot.

        A side-pot winner may still lose another pot, and folded players do not
        get invented showdown grudges. The memory deduplicates repeated hooks.
        """
        awards = [
            {"eligible": sorted(set(pot.get("eligible", results)) & set(results)),
             "winners": list(pot.get("winners", []))}
            for pot in self.last_pot_awards
        ]
        self.personality_memory.record_showdown(
            awards, grudge_seats(self.npcs, self.get_hand_contributions()),
            self.hand_number, self.starting_stack)

    def get_npc_hand_strength(
            self,
            npc_index
    ):

        if not (
                0
                <= npc_index
                < len(self.npc_hands)
        ):
            return 0.0

        hand = (
            self.npc_hands[
                npc_index
            ]
        )

        if len(hand) < 2:
            return 0.0

        # ==================================================
        # PREFLOP
        # ==================================================

        if len(
                self.community_cards
        ) < 3:

            rank_1 = (
                RANK_VALUES[
                    hand[0]["rank"]
                ]
            )

            rank_2 = (
                RANK_VALUES[
                    hand[1]["rank"]
                ]
            )

            high_rank = max(
                rank_1,
                rank_2
            )

            low_rank = min(
                rank_1,
                rank_2
            )

            suited = (
                    hand[0]["suit"]
                    == hand[1]["suit"]
            )

            gap = abs(
                rank_1 - rank_2
            )

            # ------------------------------------------
            # Pocket pair
            # ------------------------------------------

            if rank_1 == rank_2:
                strength = (
                        0.43
                        + (
                                high_rank - 2
                        )
                        / 12.0
                        * 0.52
                )

                return max(
                    0.0,
                    min(
                        strength,
                        1.0
                    )
                )

            # ------------------------------------------
            # Non-pair
            # ------------------------------------------

            strength = (
                    0.08
                    + (
                            high_rank - 2
                    )
                    / 12.0
                    * 0.42
                    + (
                            low_rank - 2
                    )
                    / 12.0
                    * 0.12
            )

            # Suited cards
            if suited:
                strength += 0.07

            # Connected / nearly connected
            if gap == 1:
                strength += 0.07

            elif gap == 2:
                strength += 0.035

            # Two broadway cards
            if (
                    high_rank >= 10
                    and low_rank >= 10
            ):
                strength += 0.08

            # Ace bonus
            if high_rank == 14:
                strength += 0.035

            return max(
                0.0,
                min(
                    strength,
                    0.92
                )
            )

        # ==================================================
        # FLOP / TURN / RIVER
        # ==================================================

        cards = (
                hand
                + self.community_cards
        )

        result = (
            self.evaluate_best_hand(
                cards
            )
        )

        if result is None:
            return 0.0

        score = (
            result[0]
        )

        category = (
            score[0]
        )

        category_strengths = {
            0: 0.18,  # High card
            1: 0.40,  # Pair
            2: 0.58,  # Two pair
            3: 0.69,  # Trips
            4: 0.78,  # Straight
            5: 0.83,  # Flush
            6: 0.91,  # Full house
            7: 0.97,  # Quads
            8: 1.00,  # Straight flush
        }

        strength = (
            category_strengths.get(
                category,
                0.20
            )
        )

        # Give a small boost based on the most
        # important rank in the evaluated hand.
        if (
                len(score) >= 2
                and isinstance(
            score[1],
            int
        )
        ):
            strength += (
                    score[1]
                    / 14.0
                    * 0.06
            )

        return max(
            0.0,
            min(
                strength,
                1.0
            )
        )

    def can_npc_raise(
            self,
            npc_index
    ):

        if not (
                0
                <= npc_index
                < len(self.npcs)
        ):
            return False

        if (
                self.npc_busted[npc_index]
                or self.npc_folded[npc_index]
                or self.npc_all_in[npc_index]
        ):
            return False

        # The shared rule (core.can_raise): chips beyond the call,
        # somebody left to respond (B36), and betting reopened
        # (seat_betting_reopened). An NPC that already acted and only
        # returned because of a short all-in raise may call or fold, but
        # not raise.
        return can_raise(
            npc_index + 1,
            self.seat_in_hand(),
            self.seat_stacks(),
            self.seat_round_bets(),
            self.current_bet,
            reopened=self.seat_betting_reopened(npc_index + 1)
        )

    def seat_betting_reopened(self, seat):
        """May seat bet or raise again this round (core.betting_reopened)?

        No-limit (Hold'em, Draw): a seat that already acted may raise
        again once the short all-ins it faces add up to a full raise
        (TDA Rule 47). Seven-Card Stud overrides this with its
        fixed-limit rule.
        """
        return betting_reopened(
            self.seat_has_acted()[seat],
            self.seat_round_bets()[seat],
            self.current_bet,
            self.get_minimum_raise_size()
        )

    # ==================================================
    # NPC BET SIZING
    # ==================================================

    # ==================================================
    # NPC STREET BETTING CAP
    #
    # This is a SOFT AI cap, not a poker-rule cap.
    # It keeps NPCs from voluntarily detonating their
    # entire stack too early in the hand.
    # ==================================================

    def get_npc_wealth_pressure(
            self,
            npc_index
    ):
        """Return 0..1 pressure from a stack that has grown beyond the buy-in.

        A small run-good bump should not rewrite a personality, so the effect
        begins only after the NPC is at least 15% above the starting stack and
        reaches full strength around 2.5x the original buy-in.
        """
        if not (0 <= npc_index < len(self.npc_stacks)):
            return 0.0

        return wealth_pressure(
            self.npc_stacks[npc_index],
            self.starting_stack
        )

    def get_npc_stage_bet_cap(
            self,
            npc_index
    ):

        stack = self.npc_stacks[npc_index]

        if stack <= 0:
            return self.npc_round_bets[npc_index]

        stage_fractions = {
            "preflop": 0.12,
            "flop": 0.22,
            "turn": 0.40,
            "river": 1.00,
        }

        # Wealthy stacks are allowed to exert more pressure on early/middle
        # streets. The personality AI still decides whether to use this extra
        # room; this merely prevents the old fixed buy-in cap from making a
        # huge chip leader bet exactly like a fresh stack.
        stage_wealth_boost = {
            "preflop": 0.70,
            "flop": 0.85,
            "turn": 0.65,
            "river": 0.50,
        }

        return soft_bet_cap(
            self.starting_stack,
            stage_fractions.get(self.current_stage, 0.25),
            self.get_npc_wealth_pressure(npc_index),
            stage_wealth_boost.get(self.current_stage, 0.45),
            self.get_minimum_open_bet(),
            self.npc_round_bets[npc_index] + stack,
        )

    def get_npc_open_bet_amount(
            self,
            npc_index,
            strength,
            profile,
            bluff=False
    ):

        context = self.build_npc_ai_context(
            npc_index,
            strength=strength
        )

        return choose_poker_open_bet_amount(
            context,
            profile,
            strength,
            bluff=bluff
        )

    def get_npc_raise_to_amount(
            self,
            npc_index,
            strength,
            profile,
            bluff=False
    ):

        context = self.build_npc_ai_context(
            npc_index,
            strength=strength
        )

        return choose_poker_raise_to_amount(
            context,
            profile,
            strength,
            bluff=bluff
        )
