import random
from npc_personality import get_npc_traits, trait_units
from collections import Counter
from itertools import combinations

from poker_core import describe_poker_score, format_poker_cards
from poker_ai import (
    get_poker_personality,
    get_poker_skill_factor,
)
from texas_holdem import (
    HAND_NAMES,
    RANK_VALUES,
    TexasHoldemGame,
)


class FiveCardDrawGame(TexasHoldemGame):
    """Five-Card Draw built on the proven shared betting/table machinery.

    The Hold'em class currently owns the mature seat, blind, betting, all-in,
    side-pot, hand-history and shared-AI plumbing. This subclass replaces only
    the game-specific deal/draw/street/showdown behavior.
    """

    rating_game_key = "five_card_draw"

    def __init__(self):
        super().__init__()

        self.player_draw_complete = False
        self.player_last_draw_count = 0
        self.player_last_draw_indexes = []
        self.npc_draw_counts = []
        self.npc_stood_pat = []

    # ==================================================
    # SESSION
    # ==================================================

    def start_session(self, npcs, starting_stack, ante):
        result = super().start_session(
            npcs,
            starting_stack,
            ante,
        )

        self.player_draw_complete = False
        self.player_last_draw_count = 0
        self.player_last_draw_indexes = []
        self.npc_draw_counts = [
            0 for _ in self.npcs
        ]
        self.npc_stood_pat = [
            False for _ in self.npcs
        ]

        return result

    # ==================================================
    # DEAL / NEW HAND
    # ==================================================

    def get_hand_deal_order(self):
        # A blind may consume the final chip. That seat still owns this hand.
        live = set(self.hand_seat_indexes)
        if not live:
            return []

        actor_count = len(self.npcs) + 1
        if self.dealer_index is None:
            start = 0
        else:
            start = (self.dealer_index + 1) % actor_count

        order = []
        for offset in range(actor_count):
            seat = (start + offset) % actor_count
            if seat in live:
                order.append(seat)

        return order

    def _give_card_to_seat(self, player_index, card):
        if card is None:
            return

        if player_index == 0:
            self.player_hand.append(card)
            return

        npc_index = player_index - 1
        if 0 <= npc_index < len(self.npc_hands):
            self.npc_hands[npc_index].append(card)

    def start_hand(self):
        self.refresh_busted_state()

        if self.player_busted:
            self.hand_complete = True
            self.current_actor = -1
            self.current_stage = "busted"
            self.result_text = "You are out of chips."
            return False

        live_indexes = self.get_live_player_indexes()

        if len(live_indexes) < 2:
            self.hand_complete = True
            self.current_actor = -1
            self.current_stage = "showdown"
            self.result_text = "The table has been cleared."
            return False

        self.hand_seat_indexes = list(live_indexes)
        self.player_model.start_hand()

        self.hand_number += 1
        self.last_hand_busted_indexes = []

        self.hand_history.start_hand(
            self.hand_number,
            "Five-Card Draw",
            stage="preflop",
        )

        self.build_deck()

        self.player_hand = []
        self.npc_hands = [
            [] for _ in self.npcs
        ]
        self.community_cards = []

        self.pot = 0
        self.hand_complete = False
        self.winner_indexes = []
        self.result_text = ""
        self.last_pot_awards = []
        self.last_resolved_pot = 0

        self.player_hand_contribution = 0
        self.npc_hand_contributions = [
            0 for _ in self.npcs
        ]

        self.player_folded = False
        self.npc_folded = [
            busted for busted in self.npc_busted
        ]

        self.player_all_in = False
        self.npc_all_in = [
            False for _ in self.npcs
        ]

        self.player_draw_complete = False
        self.player_last_draw_count = 0
        self.player_last_draw_indexes = []
        self.npc_draw_counts = [
            0 for _ in self.npcs
        ]
        self.npc_stood_pat = [
            False for _ in self.npcs
        ]

        self.rotate_dealer()
        self.assign_blind_positions()

        self.current_stage = "preflop"

        dealer_name = self.get_table_player_name(
            self.dealer_index
        )
        self.log_hand_event(
            "dealer",
            f"Dealer: {dealer_name}.",
            actor_index=self.dealer_index,
        )

        self.reset_betting_round(
            assign_actor=False
        )

        self.post_blind(
            self.small_blind_index,
            self.small_blind,
            "SB",
        )
        self.post_blind(
            self.big_blind_index,
            self.big_blind,
            "BB",
        )

        self.current_bet = self.big_blind
        self.last_raise_size = self.big_blind
        self.last_raiser = None

        for npc_index in range(len(self.npcs)):
            if self.npc_busted[npc_index]:
                self.npc_action_texts[npc_index] = "Busted"

        deal_order = self.get_hand_deal_order()

        for _ in range(5):
            for player_index in deal_order:
                self._give_card_to_seat(
                    player_index,
                    self.draw_card(),
                )

        self.log_hand_event(
            "hole_cards",
            f"You are dealt {format_poker_cards(self.player_hand)}.",
            actor_index=0,
            cards=[
                dict(card)
                for card in self.player_hand
                if card
            ],
        )

        self.set_first_actor_from(
            self.get_preflop_first_actor_index()
        )

        return True

    # ==================================================
    # FIVE-CARD DRAW HAND / DRAW HELPERS
    # ==================================================

    @staticmethod
    def _rank_groups(hand):
        groups = {}
        for index, card in enumerate(hand):
            groups.setdefault(
                RANK_VALUES[card["rank"]],
                [],
            ).append(index)
        return groups

    @staticmethod
    def _four_flush_keep_indexes(hand):
        suit_groups = {}
        for index, card in enumerate(hand):
            suit_groups.setdefault(
                card["suit"],
                [],
            ).append(index)

        candidates = [
            indexes
            for indexes in suit_groups.values()
            if len(indexes) == 4
        ]

        if not candidates:
            return None

        return set(candidates[0])

    @staticmethod
    def _four_straight_keep_indexes(hand):
        best = None
        best_score = None

        for indexes in combinations(range(5), 4):
            values = sorted({
                RANK_VALUES[hand[index]["rank"]]
                for index in indexes
            })

            if len(values) != 4:
                continue

            ace_low_values = sorted(
                1 if value == 14 else value
                for value in values
            )

            value_sets = [values, ace_low_values]

            for candidate_values in value_sets:
                low = min(candidate_values)
                high = max(candidate_values)

                if high - low > 4:
                    continue

                missing = 5 - len(candidate_values)
                if missing != 1:
                    continue

                score = (
                    max(candidate_values),
                    -sum(
                        1
                        for left, right
                        in zip(
                            candidate_values,
                            candidate_values[1:],
                        )
                        if right - left > 1
                    ),
                )

                if best_score is None or score > best_score:
                    best_score = score
                    best = set(indexes)

        return best

    def choose_npc_discard_indexes(self, npc_index):
        if not (
            0 <= npc_index < len(self.npc_hands)
        ):
            return []

        hand = self.npc_hands[npc_index]
        if len(hand) != 5:
            return []

        result = self.evaluate_five_cards(hand)
        if result is None:
            return []

        category = result[0]
        personality = get_poker_personality(
            self.npcs[npc_index]
        )
        skill_factor = get_poker_skill_factor(
            self.npcs[npc_index]
        )

        # Occasional stand-pat bluff with a weak hand.
        t = trait_units(get_npc_traits(self.npcs[npc_index]))
        stand_pat_bluff_chance = max(0.002, 0.005 + 0.04*t["aggressiveness"]
                                    + 0.04*t["unpredictability"] - 0.035*t["selectivity"])


        stand_pat_bluff_chance *= (
            0.55 + 0.65 * skill_factor
        )

        if (
            category <= 1
            and random.random() < stand_pat_bluff_chance
        ):
            self.npc_stood_pat[npc_index] = True
            return []

        # Straight or better: keep everything.
        if category >= 4:
            self.npc_stood_pat[npc_index] = True
            return []

        groups = self._rank_groups(hand)
        group_sizes = sorted(
            (
                (len(indexes), rank, indexes)
                for rank, indexes in groups.items()
            ),
            reverse=True,
        )

        # Trips: keep the three matching cards.
        if category == 3:
            keep = set(group_sizes[0][2])
            return [
                index for index in range(5)
                if index not in keep
            ]

        # Two pair: throw only the kicker.
        if category == 2:
            keep = set()
            for size, _rank, indexes in group_sizes:
                if size == 2:
                    keep.update(indexes)
            return [
                index for index in range(5)
                if index not in keep
            ]

        # One pair: keep the pair and draw three.
        if category == 1:
            pair_indexes = next(
                indexes
                for size, _rank, indexes in group_sizes
                if size == 2
            )
            keep = set(pair_indexes)
            return [
                index for index in range(5)
                if index not in keep
            ]

        # High-card draw: prioritize a four-flush.
        flush_keep = self._four_flush_keep_indexes(hand)
        if flush_keep is not None:
            return [
                index for index in range(5)
                if index not in flush_keep
            ]

        # Then prioritize a four-card straight draw.
        straight_keep = self._four_straight_keep_indexes(hand)
        if straight_keep is not None:
            return [
                index for index in range(5)
                if index not in straight_keep
            ]

        # Otherwise retain useful high cards. Stronger NPCs are
        # slightly more selective about what counts as worth keeping.
        high_cutoff = 12 if skill_factor >= 0.75 else 11
        high_indexes = [
            index
            for index, card in enumerate(hand)
            if RANK_VALUES[card["rank"]] >= high_cutoff
        ]

        # Preserve at most two high cards so the draw still has teeth.
        high_indexes.sort(
            key=lambda index: RANK_VALUES[hand[index]["rank"]],
            reverse=True,
        )
        keep = set(high_indexes[:2])

        if not keep:
            highest_index = max(
                range(5),
                key=lambda index: RANK_VALUES[hand[index]["rank"]],
            )
            keep.add(highest_index)

        return [
            index for index in range(5)
            if index not in keep
        ]

    def _replace_cards(self, hand, discard_indexes):
        discard_indexes = sorted({
            int(index)
            for index in discard_indexes
            if 0 <= int(index) < len(hand)
        })

        for index in discard_indexes:
            replacement = self.draw_card()
            if replacement is not None:
                hand[index] = replacement

        return len(discard_indexes)

    def perform_npc_draw(self, npc_index):
        if not (
            0 <= npc_index < len(self.npcs)
        ):
            return False

        if (
            self.npc_busted[npc_index]
            or self.npc_folded[npc_index]
        ):
            return False

        discard_indexes = self.choose_npc_discard_indexes(
            npc_index
        )

        count = self._replace_cards(
            self.npc_hands[npc_index],
            discard_indexes,
        )

        self.npc_draw_counts[npc_index] = count
        self.npc_stood_pat[npc_index] = count == 0

        name = self.get_table_player_name(
            npc_index + 1
        )

        if count == 0:
            text = f"{name} stands pat."
        elif count == 1:
            text = f"{name} draws 1 card."
        else:
            text = f"{name} draws {count} cards."

        self.log_hand_event(
            "draw",
            text,
            actor_index=npc_index + 1,
            draw_count=count,
        )

        return True

    def begin_draw_phase(self):
        if self.hand_complete:
            return False

        self.current_stage = "draw"
        self.current_actor = -1
        self.betting_round_complete = False

        self.player_draw_complete = (
            self.player_folded
            or self.player_busted
        )
        self.player_last_draw_count = 0
        self.player_last_draw_indexes = []

        self.npc_draw_counts = [
            0 for _ in self.npcs
        ]
        self.npc_stood_pat = [
            False for _ in self.npcs
        ]

        self.log_hand_event(
            "draw_phase",
            "Draw.",
        )

        # NPC draw decisions are immediate. The human gets an
        # interactive selection step before the second betting round.
        for npc_index in range(len(self.npcs)):
            if (
                self.npc_busted[npc_index]
                or self.npc_folded[npc_index]
            ):
                continue

            self.perform_npc_draw(npc_index)

        if self.player_draw_complete:
            return self.start_second_betting_round()

        return True

    def player_draw(self, discard_indexes):
        if (
            self.current_stage != "draw"
            or self.hand_complete
            or self.player_folded
            or self.player_busted
            or self.player_draw_complete
        ):
            return False

        discard_indexes = sorted({
            int(index)
            for index in discard_indexes
            if 0 <= int(index) < len(self.player_hand)
        })

        count = self._replace_cards(
            self.player_hand,
            discard_indexes,
        )

        self.player_draw_complete = True
        self.player_last_draw_count = count
        self.player_last_draw_indexes = list(discard_indexes)

        if count == 0:
            text = "You stand pat."
        elif count == 1:
            text = "You draw 1 card."
        else:
            text = f"You draw {count} cards."

        self.log_hand_event(
            "draw",
            text,
            actor_index=0,
            draw_count=count,
        )

        self.log_hand_event(
            "player_hand",
            f"Your hand: {format_poker_cards(self.player_hand)}.",
            actor_index=0,
            cards=[
                dict(card)
                for card in self.player_hand
                if card
            ],
        )

        return self.start_second_betting_round()

    def start_second_betting_round(self):
        if self.hand_complete:
            return False

        self.current_stage = "post_draw"

        first_actor = self.get_postflop_first_actor_index()

        self.reset_betting_round(
            first_actor=first_actor,
            assign_actor=True,
        )

        return True

    # ==================================================
    # BETTING / AI OVERRIDES
    # ==================================================

    def advance_after_betting_round(self):
        if not self.is_betting_round_complete():
            return False

        if self.current_stage == "preflop":
            return self.begin_draw_phase()

        if self.current_stage == "post_draw":
            return self.showdown()

        return False

    def resolve_after_fold(self):
        if self.hand_complete:
            return False

        active_indexes = self.get_active_player_indexes()

        if not active_indexes:
            return False

        if len(active_indexes) == 1:
            return self.award_pot_to_single_player(
                active_indexes[0]
            )

        # Unlike Hold'em, there is no hidden board to run out. If the
        # human folds, simply allow the remaining NPC action to continue.
        if self.player_folded and self.current_actor == 0:
            self.advance_to_next_actor()

        return True

    def get_npc_stage_bet_cap(self, npc_index):
        stack = self.npc_stacks[npc_index]

        if stack <= 0:
            return self.npc_round_bets[npc_index]

        stage_fractions = {
            "preflop": 0.15,
            "post_draw": 1.00,
        }

        fraction = stage_fractions.get(
            self.current_stage,
            0.35,
        )

        # A deep-stack Draw player should be able to press a chip advantage,
        # especially after the draw, without turning every rich NPC into a
        # maniac. Personality/hand strength still decide whether this extra
        # room is actually used.
        wealth_pressure = self.get_npc_wealth_pressure(npc_index)
        stage_wealth_boost = {
            "preflop": 0.60,
            "post_draw": 0.35,
        }.get(self.current_stage, 0.30)
        fraction *= 1.0 + wealth_pressure * stage_wealth_boost

        base_stack = max(1, self.starting_stack)
        target_cap = max(
            self.get_minimum_open_bet(),
            int(base_stack * fraction),
        )

        maximum_total = (
            self.npc_round_bets[npc_index]
            + stack
        )

        return min(target_cap, maximum_total)

    def build_npc_ai_context(self, npc_index, strength=None):
        context = super().build_npc_ai_context(
            npc_index,
            strength=strength,
        )

        context["game"] = "five_card_draw"
        context["draw_count"] = (
            self.npc_draw_counts[npc_index]
            if 0 <= npc_index < len(self.npc_draw_counts)
            else 0
        )
        context["stood_pat"] = (
            self.npc_stood_pat[npc_index]
            if 0 <= npc_index < len(self.npc_stood_pat)
            else False
        )

        # Hold'em supplies the shared stack-wealth signal. Draw keeps most of
        # it, but tones it down before cards are exchanged because the first
        # betting round contains substantially less information.
        wealth_scale = (
            0.80
            if self.current_stage == "preflop"
            else 1.00
        )
        context["wealth_pressure"] = min(
            1.0,
            max(0.0, float(context.get("wealth_pressure", 0.0)))
            * wealth_scale,
        )
        context["wealth_variant_scale"] = wealth_scale

        return context

    def get_npc_hand_strength(self, npc_index):
        if not (
            0 <= npc_index < len(self.npc_hands)
        ):
            return 0.0

        hand = self.npc_hands[npc_index]
        if len(hand) != 5:
            return 0.0

        result = self.evaluate_five_cards(hand)
        if result is None:
            return 0.0

        score = result
        category = score[0]

        category_strengths = {
            0: 0.17,
            1: 0.43,
            2: 0.63,
            3: 0.74,
            4: 0.84,
            5: 0.88,
            6: 0.94,
            7: 0.985,
            8: 1.00,
        }

        strength = category_strengths.get(
            category,
            0.17,
        )

        # Kicker/detail information nudges hands inside a category.
        detail_values = [
            value
            for value in score[1:]
            if isinstance(value, int)
        ]

        if detail_values:
            strength += (
                min(14, max(detail_values))
                / 14.0
                * 0.045
            )

        # Before the draw, account for strong drawing structures.
        if self.current_stage == "preflop" and category == 0:
            if self._four_flush_keep_indexes(hand) is not None:
                strength = max(strength, 0.37)

            if self._four_straight_keep_indexes(hand) is not None:
                strength = max(strength, 0.34)

        return max(
            0.0,
            min(strength, 1.0),
        )

    # ==================================================
    # SHOWDOWN
    # ==================================================

    def showdown(self):
        active_indexes = self.get_active_player_indexes()

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
                results[player_index] = result

        if not results:
            return False

        self.last_resolved_pot = max(
            0,
            int(self.pot)
        )

        self.log_hand_event(
            "showdown",
            "Showdown.",
        )

        for player_index, result in results.items():
            if player_index == 0:
                cards = self.player_hand
                prefix = "You show"
            else:
                npc_index = player_index - 1
                cards = self.npc_hands[npc_index]
                prefix = (
                    f"{self.get_table_player_name(player_index)} "
                    f"shows"
                )

            category = HAND_NAMES[result[0][0]]
            hand_detail = describe_poker_score(
                result[0],
                compact=True,
            )

            self.log_hand_event(
                "showdown_hand",
                (
                    f"{prefix} {format_poker_cards(cards)} "
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

        side_pots = self.build_side_pots()

        payout_totals = {
            player_index: 0
            for player_index in results
        }

        self.last_pot_awards = []

        for pot_data in side_pots:
            pot_amount = pot_data["amount"]
            eligible = [
                player_index
                for player_index in pot_data["eligible"]
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
                if results[player_index][0] == best_score
            ]

            if not winners:
                continue

            # Odd-chip priority begins left of the dealer.
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

            share = pot_amount // len(winners)
            remainder = pot_amount % len(winners)

            for winner_order, winner_index in enumerate(winners):
                winnings = share
                if winner_order < remainder:
                    winnings += 1

                self.award_chips_to_player(
                    winner_index,
                    winnings,
                )
                payout_totals[winner_index] += winnings

            self.last_pot_awards.append({
                "amount": pot_amount,
                "eligible": eligible.copy(),
                "winners": winners.copy(),
                "share": share,
                "remainder": remainder,
            })

        self.winner_indexes = sorted([
            player_index
            for player_index, winnings in payout_totals.items()
            if winnings > 0
        ])

        payout_winners = [
            player_index
            for player_index in self.winner_indexes
            if payout_totals.get(player_index, 0) > 0
        ]

        if len(payout_winners) == 1:
            winner_index = payout_winners[0]
            winnings = payout_totals[winner_index]
            category = HAND_NAMES[
                results[winner_index][0][0]
            ]
            hand_detail = describe_poker_score(
                results[winner_index][0],
                compact=True,
            )

            if winner_index == 0:
                self.result_text = (
                    f"You win ${winnings:,} with {hand_detail}!"
                )
            else:
                winner_name = self.get_table_player_name(
                    winner_index
                )
                self.result_text = (
                    f"{winner_name} wins ${winnings:,} "
                    f"with {hand_detail}."
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
                + "; ".join(payout_parts)
                + "."
            )

        self.log_detailed_pot_awards(
            results.keys()
        )

        self.log_hand_event(
            "result",
            self.result_text,
            winners=self.winner_indexes.copy(),
            payouts={
                player_index: amount
                for player_index, amount in payout_totals.items()
                if amount > 0
            },
        )

        self.record_personality_showdown(results)

        self.pot = 0
        self.hand_complete = True
        self.current_actor = -1
        self.current_stage = "showdown"

        newly_busted = self.refresh_busted_state()
        self.log_newly_busted_players(
            newly_busted
        )

        self.finalize_showdown_display_state()

        return True

    def get_player_hand_name(self):
        if len(self.player_hand) != 5:
            return ""

        result = self.evaluate_five_cards(
            self.player_hand
        )
        if result is None:
            return ""

        return HAND_NAMES[result[0]]

    def get_npc_hand_name(self, npc_index):
        if not (
            0 <= npc_index < len(self.npc_hands)
        ):
            return ""

        hand = self.npc_hands[npc_index]
        if len(hand) != 5:
            return ""

        result = self.evaluate_five_cards(hand)
        if result is None:
            return ""

        return HAND_NAMES[result[0]]
