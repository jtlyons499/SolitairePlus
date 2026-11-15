import random
from solitaireplus.npc.personality import get_npc_traits, trait_units
from collections import Counter
from itertools import combinations

from solitaireplus.games.poker.core import format_poker_cards
from solitaireplus.games.poker.npc_inputs import soft_bet_cap
from solitaireplus.games.poker.ai import (
    get_poker_personality,
)
from solitaireplus.games.poker.holdem import (
    HAND_NAMES,
    RANK_VALUES,
    TexasHoldemGame,
)


class FiveCardDrawGame(TexasHoldemGame):
    """Five-Card Draw built on the proven shared betting/table machinery.

    The Hold'em class currently owns the mature seat, blind, betting, all-in,
    side-pot, showdown, hand-history and shared-AI plumbing. This subclass
    replaces only the game-specific deal/draw/street behavior.
    """

    rating_game_key = "five_card_draw"

    # The showdown banner is one fixed-width line (see TexasHoldemGame).
    payout_text_names_hands = False

    def __init__(self):
        super().__init__()

        self.player_draw_complete = False
        self.player_last_draw_count = 0
        self.player_last_draw_indexes = []
        self.npc_draw_counts = []
        self.npc_stood_pat = []
        # Cards thrown away during this hand's draw (never in a live hand).
        self.draw_muck = []

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
        self.draw_muck = []

        self.player_hand = []
        self.npc_hands = [
            [] for _ in self.npcs
        ]
        self.community_cards = []

        self.pot = 0
        self.hand_complete = False
        self.result_text = ""
        self.begin_hand_records()

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

        # B39: the same rule as Hold'em. A short all-in big blind keeps the
        # nominal wager only while two or more seats can still act.
        self.set_opening_wager(
            self.big_blind,
            self.big_blind,
        )

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
        # The same skill as this NPC's betting: its Five-Card Draw rating, or
        # its skill tier without one (get_npc_skill_factor).
        skill_factor = self.get_npc_skill_factor(
            npc_index
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

    def _reshuffle_muck_into_deck(self):
        if self.deck or not self.draw_muck:
            return False

        self.deck = list(self.draw_muck)
        self.draw_muck = []
        random.shuffle(self.deck)

        self.log_hand_event(
            "reshuffle",
            "The deck is empty; the discards are shuffled in.",
        )
        return True

    def _replace_cards(self, hand, discard_indexes):
        """Swap discards for new cards; return (replaced, kept) indexes."""
        discard_indexes = sorted({
            int(index)
            for index in discard_indexes
            if 0 <= int(index) < len(hand)
        })

        replaced = []
        kept = []
        thrown = []

        for index in discard_indexes:
            replacement = self.draw_card()
            if replacement is None and self._reshuffle_muck_into_deck():
                replacement = self.draw_card()

            if replacement is None:
                # Deck and muck are both exhausted: the old card stays.
                kept.append(index)
                continue

            thrown.append(hand[index])
            hand[index] = replacement
            replaced.append(index)

        # Join the muck only after this hand has drawn, so nobody is dealt
        # their own discards straight back.
        self.draw_muck.extend(thrown)

        return replaced, kept

    def _deck_ran_out_text(self, actor_index, kept_count):
        cards = "card" if kept_count == 1 else "cards"
        if actor_index == 0:
            who = f"you keep {kept_count} {cards}"
        else:
            who = (
                f"{self.get_table_player_name(actor_index)} "
                f"keeps {kept_count} {cards}"
            )

        return f"The deck ran out: {who}."

    def _log_draw(self, actor_index, received_count, kept_count):
        """Log one seat's draw.

        draw_count is how many cards the seat asked for (what the table saw
        it throw), which is what table reads learn from. The text and
        received_count say how many cards it actually got.
        """
        asked_count = received_count + kept_count

        if actor_index == 0:
            subject, verb, pat = "You", "draw", "stand pat"
        else:
            subject = self.get_table_player_name(actor_index)
            verb, pat = "draws", "stands pat"

        if asked_count == 0:
            text = f"{subject} {pat}."
        elif received_count == 0:
            # Nothing was left to draw: one line says so.
            text = self._deck_ran_out_text(actor_index, kept_count)
        elif received_count == 1:
            text = f"{subject} {verb} 1 card."
        else:
            text = f"{subject} {verb} {received_count} cards."

        self.log_hand_event(
            "draw",
            text,
            actor_index=actor_index,
            draw_count=asked_count,
            received_count=received_count,
            kept_count=kept_count,
        )

        if received_count > 0 and kept_count > 0:
            self.log_hand_event(
                "draw_short",
                self._deck_ran_out_text(actor_index, kept_count),
                actor_index=actor_index,
                kept_count=kept_count,
            )

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

        replaced, kept = self._replace_cards(
            self.npc_hands[npc_index],
            discard_indexes,
        )
        count = len(replaced)

        self.npc_draw_counts[npc_index] = count
        self.npc_stood_pat[npc_index] = count == 0 and not kept

        self._log_draw(npc_index + 1, count, len(kept))

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

        replaced, kept = self._replace_cards(
            self.player_hand,
            discard_indexes,
        )
        count = len(replaced)

        self.player_draw_complete = True
        self.player_last_draw_count = count
        self.player_last_draw_indexes = list(replaced)

        self._log_draw(0, count, len(kept))

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

    def get_npc_stage_bet_cap(self, npc_index):
        stack = self.npc_stacks[npc_index]

        if stack <= 0:
            return self.npc_round_bets[npc_index]

        stage_fractions = {
            "preflop": 0.15,
            "post_draw": 1.00,
        }

        # A deep-stack Draw player should be able to press a chip advantage,
        # especially after the draw, without turning every rich NPC into a
        # maniac. Personality/hand strength still decide whether this extra
        # room is actually used.
        stage_wealth_boost = {
            "preflop": 0.60,
            "post_draw": 0.35,
        }

        return soft_bet_cap(
            self.starting_stack,
            stage_fractions.get(self.current_stage, 0.35),
            self.get_npc_wealth_pressure(npc_index),
            stage_wealth_boost.get(self.current_stage, 0.30),
            self.get_minimum_open_bet(),
            self.npc_round_bets[npc_index] + stack,
        )

    def get_npc_wealth_scale(self):
        # Draw keeps most of the shared stack-wealth signal, but tones it down
        # before cards are exchanged because the first betting round contains
        # substantially less information.
        return 0.80 if self.current_stage == "preflop" else 1.00

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
    #
    # TexasHoldemGame.resolve_showdown settles the hand
    # with the shared pot rules; the cards shown are the
    # five-card hands in player_hand / npc_hands.
    # ==================================================

    def showdown_ready(self):
        # No board: the showdown follows the last betting round.
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
