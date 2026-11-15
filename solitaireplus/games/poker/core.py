# ==================================================
# SHARED POKER CORE HELPERS
#
# This module is intentionally game-agnostic so
# Texas Hold'em, Five-Card Draw, and Seven-Card Stud
# can share the same hand-history/event infrastructure.
#
# It also holds the one hand evaluator every poker
# variant uses (see HAND EVALUATION) and the shared
# pot and betting rules (see ODD CHIPS, POTS and
# BETTING at the end).
# Multiplayer re-exports this module, so it must not
# import any other project module.
# ==================================================

from collections import Counter
from itertools import combinations

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


# ==================================================
# POKER DISPLAY HELPERS
# ==================================================

POKER_RANK_NAMES = {
    14: "Ace",
    13: "King",
    12: "Queen",
    11: "Jack",
    10: "Ten",
    9: "Nine",
    8: "Eight",
    7: "Seven",
    6: "Six",
    5: "Five",
    4: "Four",
    3: "Three",
    2: "Two",
    1: "Ace",
}

POKER_RANK_PLURALS = {
    14: "Aces",
    13: "Kings",
    12: "Queens",
    11: "Jacks",
    10: "Tens",
    9: "Nines",
    8: "Eights",
    7: "Sevens",
    6: "Sixes",
    5: "Fives",
    4: "Fours",
    3: "Threes",
    2: "Twos",
    1: "Aces",
}

POKER_RANK_SHORT = {
    14: "A",
    13: "K",
    12: "Q",
    11: "J",
    10: "10",
    9: "9",
    8: "8",
    7: "7",
    6: "6",
    5: "5",
    4: "4",
    3: "3",
    2: "2",
    1: "A",
}


def format_poker_display_name(name):
    """Return the compact table name used by every poker variant.

    Most NPCs use only their first name to keep HUDs, chat, and history tidy.
    Memphis van Dijk intentionally keeps the distinctive ``van Dijk`` label.
    """
    raw = str(name or "Opponent").strip()

    if not raw:
        return "Opponent"

    lowered = raw.casefold()

    if "van dijk" in lowered:
        return "van Dijk"

    return raw.split()[0]


def join_poker_names(names):
    """Join table names for a sentence: 'Ada', 'Ada and you', 'Ada, Bo and you'."""
    names = [str(name) for name in names]

    if len(names) <= 1:
        return "".join(names)

    return f"{', '.join(names[:-1])} and {names[-1]}"


def _poker_rank_name(value, plural=False, compact=False):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return str(value)

    if compact:
        return POKER_RANK_SHORT.get(value, str(value))

    mapping = (
        POKER_RANK_PLURALS
        if plural
        else POKER_RANK_NAMES
    )

    return mapping.get(value, str(value))


def describe_poker_score(score, compact=True):
    """Explain a five-card comparison tuple, including kicker information."""
    if not score:
        return "Unknown hand"

    score = tuple(score)
    category = score[0]
    values = list(score[1:])

    if category == 8:
        high = values[0] if values else 0

        if high == 14:
            return "Royal Flush"

        return (
            f"{_poker_rank_name(high, compact=compact)}-high "
            f"Straight Flush"
        )

    if category == 7:
        quad = values[0] if values else 0
        kicker = values[1] if len(values) > 1 else None

        text = (
            f"Four of a Kind, "
            f"{_poker_rank_name(quad, plural=True, compact=False)}"
        )

        if kicker is not None:
            text += (
                f", {_poker_rank_name(kicker, compact=compact)} kicker"
            )

        return text

    if category == 6:
        trips = values[0] if values else 0
        pair = values[1] if len(values) > 1 else 0

        return (
            f"Full House, "
            f"{_poker_rank_name(trips, plural=True, compact=False)} over "
            f"{_poker_rank_name(pair, plural=True, compact=False)}"
        )

    if category == 5:
        if not values:
            return "Flush"

        if compact:
            ranks = "-".join(
                _poker_rank_name(value, compact=True)
                for value in values
            )
            return f"Flush, {ranks}"

        return (
            f"Flush, "
            f"{_poker_rank_name(values[0], compact=False)}-high"
        )

    if category == 4:
        high = values[0] if values else 0
        return (
            f"{_poker_rank_name(high, compact=compact)}-high Straight"
        )

    if category == 3:
        trips = values[0] if values else 0
        kickers = values[1:]

        text = (
            f"Three of a Kind, "
            f"{_poker_rank_name(trips, plural=True, compact=False)}"
        )

        if kickers:
            kicker_text = "-".join(
                _poker_rank_name(value, compact=True)
                for value in kickers
            )
            text += (
                f", {kicker_text} "
                f"{'kicker' if len(kickers) == 1 else 'kickers'}"
            )

        return text

    if category == 2:
        high_pair = values[0] if values else 0
        low_pair = values[1] if len(values) > 1 else 0
        kicker = values[2] if len(values) > 2 else None

        text = (
            f"Two Pair, "
            f"{_poker_rank_name(high_pair, plural=True, compact=False)} "
            f"and {_poker_rank_name(low_pair, plural=True, compact=False)}"
        )

        if kicker is not None:
            text += (
                f", {_poker_rank_name(kicker, compact=compact)} kicker"
            )

        return text

    if category == 1:
        pair = values[0] if values else 0
        kickers = values[1:]

        text = (
            f"Pair of "
            f"{_poker_rank_name(pair, plural=True, compact=False)}"
        )

        if kickers:
            kicker_text = "-".join(
                _poker_rank_name(value, compact=True)
                for value in kickers
            )
            text += (
                f", {kicker_text} "
                f"{'kicker' if len(kickers) == 1 else 'kickers'}"
            )

        return text

    if category == 0:
        if not values:
            return "High Card"

        high = values[0]
        kickers = values[1:]

        text = (
            f"{_poker_rank_name(high, compact=compact)}-high"
        )

        if kickers:
            kicker_text = "-".join(
                _poker_rank_name(value, compact=True)
                for value in kickers
            )
            text += (
                f", {kicker_text} "
                f"{'kicker' if len(kickers) == 1 else 'kickers'}"
            )

        return text

    return "Poker hand"


# ==================================================
# HAND EVALUATION
#
# The one five-card scorer shared by every poker variant.
# A score is a tuple compared with the ordinary tuple
# operators: the category first (see HAND_NAMES), then the
# ranks that break ties inside that category. The ace plays
# low only in the five-high straight (the "wheel"), which
# therefore ranks below a six-high straight.
# ==================================================

RANK_VALUES = {
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 11,
    "Q": 12,
    "K": 13,
    "A": 14,
}

HAND_NAMES = {
    8: "Straight Flush",
    7: "Four of a Kind",
    6: "Full House",
    5: "Flush",
    4: "Straight",
    3: "Three of a Kind",
    2: "Two Pair",
    1: "Pair",
    0: "High Card",
}


def evaluate_five_cards(cards):
    """Return the sortable score tuple of exactly five cards.

    Returns None unless ``cards`` holds exactly five real cards.
    Cards are dicts with "rank" (a RANK_VALUES key) and "suit".
    """
    if cards is None or len(cards) != 5 or any(card is None for card in cards):
        return None

    values = sorted(
        [RANK_VALUES[card["rank"]] for card in cards],
        reverse=True,
    )
    suits = [card["suit"] for card in cards]
    counts = Counter(values)

    is_flush = len(set(suits)) == 1
    unique_values = sorted(set(values), reverse=True)
    # The ace also plays low, in the five-high straight only.
    if 14 in unique_values:
        unique_values.append(1)

    straight_high = None
    for index in range(len(unique_values) - 4):
        window = unique_values[index:index + 5]
        if window[0] - window[4] == 4:
            straight_high = window[0]
            break

    if is_flush and straight_high is not None:
        return 8, straight_high

    quads = sorted(
        (value for value, count in counts.items() if count == 4),
        reverse=True,
    )
    if quads:
        quad = quads[0]
        kicker = max(value for value in values if value != quad)
        return 7, quad, kicker

    triples = sorted(
        (value for value, count in counts.items() if count == 3),
        reverse=True,
    )
    pairs_or_better = sorted(
        (value for value, count in counts.items() if count >= 2),
        reverse=True,
    )
    if triples:
        trip = triples[0]
        pair_candidates = [value for value in pairs_or_better if value != trip]
        if len(triples) >= 2:
            pair_candidates.append(triples[1])
        if pair_candidates:
            return 6, trip, max(pair_candidates)

    if is_flush:
        return 5, *values

    if straight_high is not None:
        return 4, straight_high

    if triples:
        trip = triples[0]
        kickers = sorted(
            (value for value in values if value != trip),
            reverse=True,
        )[:2]
        return 3, trip, *kickers

    exact_pairs = sorted(
        (value for value, count in counts.items() if count == 2),
        reverse=True,
    )
    if len(exact_pairs) >= 2:
        high_pair, low_pair = exact_pairs[:2]
        kicker = max(
            value for value in values
            if value not in (high_pair, low_pair)
        )
        return 2, high_pair, low_pair, kicker

    if len(exact_pairs) == 1:
        pair = exact_pairs[0]
        kickers = sorted(
            (value for value in values if value != pair),
            reverse=True,
        )[:3]
        return 1, pair, *kickers

    return 0, *values


def evaluate_best_hand(cards):
    """Return ``(score, five_cards)`` for the best five of ``cards``.

    Returns None for fewer than five cards. When several five-card
    combinations score the same, the first one in
    itertools.combinations order is kept. Combinations that are not
    five real cards are skipped; None is returned if none are left.
    """
    if len(cards) < 5:
        return None

    best_score = None
    best_cards = None

    for combo in combinations(cards, 5):
        score = evaluate_five_cards(combo)

        if score is None:
            continue

        if best_score is None or score > best_score:
            best_score = score
            best_cards = list(combo)

    if best_score is None:
        return None

    return best_score, best_cards


def compare_scores(left, right):
    """Return 1 if ``left`` wins, -1 if ``right`` wins and 0 for a tie.

    A missing score (None) loses to any real score.
    """
    if left is None and right is None:
        return 0
    if left is None:
        return -1
    if right is None:
        return 1
    if left > right:
        return 1
    if left < right:
        return -1
    return 0


# ==================================================
# ODD CHIPS
#
# When a pot does not divide evenly between tied winners,
# the leftover ("odd") chips go one at a time to the tied
# winners in clockwise order, starting with the first seat
# to the dealer's left. The dealer, if tied, comes last.
# Clockwise means increasing seat index, wrapping round.
# ==================================================

def odd_chip_order(seats, dealer_seat, seat_count):
    """Return the distinct ``seats`` in the order they take odd chips.

    The first seat left of ``dealer_seat`` comes first and the dealer
    comes last. ``dealer_seat`` None counts as -1, so seat 0 is first.
    """
    dealer = -1 if dealer_seat is None else int(dealer_seat)

    return sorted(
        dict.fromkeys(seats),
        key=lambda seat: (seat - dealer - 1) % seat_count,
    )


def split_pot(amount, winners, dealer_seat, seat_count):
    """Divide ``amount`` chips between tied ``winners``.

    Every winner gets ``amount // len(winners)``; the remaining odd chips
    go one each to the first winners in odd_chip_order. Returns
    ``{seat: chips}`` in that order; the values always sum to ``amount``.
    Raises ValueError when there is no winner.
    """
    order = odd_chip_order(winners, dealer_seat, seat_count)

    if not order:
        raise ValueError("split_pot needs at least one winner")

    share = amount // len(order)
    remainder = amount % len(order)

    return {
        seat: share + (1 if position < remainder else 0)
        for position, seat in enumerate(order)
    }


# ==================================================
# POTS
#
# Every variant settles a hand the same way: build the main
# pot and side pots from what each seat put in this hand,
# return chips nobody else matched, then award each pot to
# the best eligible hand (ties split, see ODD CHIPS).
# ==================================================

def build_pots(contributions, live):
    """Build the main pot and side pots of one hand.

    contributions: per seat, every chip it put in this hand (antes,
    blinds, bring-in and all betting rounds).
    live: per seat, True if the seat can still win (not folded, holds a
    scored hand). A seat past the end of ``live`` is not live.

    Returns ``(pots, refunds)``. ``pots`` is a list of
    ``{"amount", "contributors", "eligible"}`` from the main pot upward;
    ``refunds`` is ``{seat: chips}`` returned without a contest.

    For each distinct positive contribution level L (ascending), the
    layer size d is L minus the previous level; its contributors are the
    seats that put in at least L and its eligible seats are the live
    contributors:

    * exactly one contributor: d is refunded to it (uncalled chips);
    * no eligible contributor: d is refunded to every contributor;
    * the same eligible seats as the last pot: the layer joins that pot
      (folded seats' dead money does not make a new side pot);
    * otherwise the layer is a new pot.

    Always: sum of pot amounts + sum of refunds == sum(contributions).
    """
    contributions = [int(amount) for amount in contributions]

    pots = []
    refunds = {}
    previous_level = 0

    for level in sorted({amount for amount in contributions if amount > 0}):
        layer = level - previous_level
        previous_level = level

        contributors = [
            seat
            for seat, amount in enumerate(contributions)
            if amount >= level
        ]
        eligible = [
            seat
            for seat in contributors
            if seat < len(live) and live[seat]
        ]

        if len(contributors) == 1:
            seat = contributors[0]
            refunds[seat] = refunds.get(seat, 0) + layer
        elif not eligible:
            for seat in contributors:
                refunds[seat] = refunds.get(seat, 0) + layer
        elif pots and pots[-1]["eligible"] == eligible:
            pots[-1]["amount"] += layer * len(contributors)
        else:
            pots.append({
                "amount": layer * len(contributors),
                "contributors": contributors,
                "eligible": eligible,
            })

    return pots, refunds


def award_pots(pots, scores, dealer_seat, seat_count, describe=None):
    """Award every pot from build_pots to its best eligible hand.

    scores: ``{seat: score}``; a higher score wins and equal scores tie.
    Only seats in ``scores`` can win, so callers build ``live`` from it.
    describe: optional function turning the winning score into text.

    Returns ``(awards, totals)``. ``awards`` holds one record per pot:
    ``{"amount", "eligible", "winners" (odd-chip order), "payouts"
    {seat: chips}, "share", "remainder", "hand"}``. ``totals`` is
    ``{seat: chips won over all pots}``. Raises ValueError for a pot
    with no eligible seat in ``scores``.
    """
    awards = []
    totals = {}

    for pot in pots:
        amount = int(pot["amount"])
        candidates = [
            seat
            for seat in pot["eligible"]
            if seat in scores
        ]

        if not candidates:
            raise ValueError("a pot has no eligible seat with a score")

        best = max(scores[seat] for seat in candidates)
        payouts = split_pot(
            amount,
            [seat for seat in candidates if scores[seat] == best],
            dealer_seat,
            seat_count,
        )
        winners = list(payouts)

        for seat, chips in payouts.items():
            totals[seat] = totals.get(seat, 0) + chips

        awards.append({
            "amount": amount,
            "eligible": list(candidates),
            "winners": winners,
            "payouts": payouts,
            "share": amount // len(winners),
            "remainder": amount % len(winners),
            "hand": describe(best) if describe else "",
        })

    return awards, totals


def settle_fold_win(contributions, winner):
    """Settle a hand that ended because every seat but ``winner`` folded.

    It is settled exactly like a showdown with ``winner`` as the only live
    seat (build_pots): the winner wins the pot of matched chips, from each
    other seat at most what it matched itself. Uncalled chips go back to
    whoever put them in, the winner's own included: a 1,000 shove that
    blinds of 10 and 20 fold to wins the 50 pot (the blinds plus the
    first 20 of the shove, which the big blind's 20 matches) and the other
    980 goes back to the shover, as it would at a showdown. A short all-in survivor never
    wins chips it did not match either.

    Returns ``(winnings, refunds)``: the chips the winner wins (the pot)
    and ``{seat: chips}`` returned uncalled, the winner's own chips
    included. Always: winnings + sum of refunds == sum(contributions).
    """
    pots, refunds = build_pots(
        contributions,
        [seat == winner for seat in range(len(contributions))],
    )

    return sum(pot["amount"] for pot in pots), refunds


def hand_nets(contributions, awards, refunds):
    """Return every seat's net for one hand: ``{seat: chips}``.

    A seat's net is what it got back (its pot payouts from ``awards``
    plus its ``refunds``) minus what it put in (``contributions``, per
    seat). The nets of all seats always sum to 0.
    """
    nets = {
        seat: -int(amount)
        for seat, amount in enumerate(contributions)
    }

    for award in awards:
        for seat, chips in award.get("payouts", {}).items():
            nets[seat] = nets.get(seat, 0) + int(chips)

    for seat, chips in refunds.items():
        nets[seat] = nets.get(seat, 0) + int(chips)

    return nets


def _contested(award):
    # A record without an "eligible" list counts as contested.
    return "eligible" not in award or len(award["eligible"]) >= 2


def collected_uncontested(award, awards):
    """Return True when ``award`` is a pot nobody else could win, at a showdown.

    Only one seat was eligible for it while the hand still had a contested
    pot (``awards`` is the hand's whole list), so it beat nobody: it holds
    that seat's own excess and folded seats' dead money. The hand history,
    recap and result banner name no winning hand for it; the seat collects
    it. A fold win's only pot is not one (everyone else folded).
    """
    return not _contested(award) and any(_contested(other) for other in awards)


def counted_awards(awards, nets=None):
    """Return the pot awards that count as winning or losing a hand.

    A pot with two or more eligible seats was contested and counts. A
    pot whose only eligible seat takes it always holds folded seats'
    dead money (build_pots refunds a layer with one contributor) besides
    that seat's own excess. It counts as won when the seat made money on
    the hand (``nets[seat] > 0``): it bet those seats out of the pot, as
    a fold win does. When the seat got back no more than it put in, the
    chips still go to it, but it did not win them.

    nets: ``{seat: net}`` for the hand (hand_nets); without it no such
    pot counts. A hand that ended because everyone else folded has only
    such a pot, and that pot is the win, so it always counts.
    """
    awards = list(awards)

    if not any(_contested(award) for award in awards):
        return awards

    nets = nets or {}

    return [
        award
        for award in awards
        if _contested(award)
        or any(
            nets.get(seat, 0) > 0
            for seat in award.get("winners", [])
        )
    ]


def hand_winners(awards, nets=None):
    """Return the seats that won or tied a hand (hand_outcome), sorted.

    nets: ``{seat: net}`` for the hand (hand_nets, see counted_awards).
    """
    return sorted({
        seat
        for award in counted_awards(awards, nets)
        for seat in award.get("winners", [])
    })


def hand_outcome(awards, seat, nets=None):
    """Return how ``seat`` did over a hand's pot awards.

    'won': it was the only winner of at least one pot that counts.
    'tied': it won no such pot alone but shared at least one.
    'lost': it won nothing. Refunds are not pots, and a pot it only
    collected uncontested counts only when it made money on the hand
    (counted_awards; nets is ``{seat: net}`` from hand_nets).
    """
    shared = False

    for award in counted_awards(awards, nets):
        winners = list(award.get("winners", []))

        if seat not in winners:
            continue

        if len(winners) == 1:
            return "won"

        shared = True

    return "tied" if shared else "lost"


# ==================================================
# BETTING
#
# The betting rules every variant shares. Each function
# takes plain per-seat lists (seat 0 is the human) and
# never touches an engine. Variant limits (Stud's raise
# cap, Five-O's fixed bet size) are checked by the caller
# on top of these.
# ==================================================

def opening_current_bet(nominal_bet, round_bets, can_act):
    """Return the bet to call once a hand's forced bets are posted.

    nominal_bet: the wager the forced bet stands for (the big blind, the
    bring-in; 0 when there are only antes).
    round_bets: per seat, the chips posted this round. Dead antes are not
    round bets.
    can_act: per seat, True if the seat is in the hand with chips left
    after posting.

    With at most one seat able to act, nobody can contest more than was
    really posted, so the bet is the largest amount posted. Otherwise a
    short all-in forced bet keeps the nominal wager. Engines then apply
    bet_to_match, which also covers the folds and all-ins that later
    leave a single seat with chips.
    """
    posted = max(round_bets, default=0)

    if sum(bool(flag) for flag in can_act) <= 1:
        return posted

    return max(nominal_bet, posted)


def bet_to_match(in_hand, stacks, round_bets, current_bet):
    """Return the bet the seats that can still act must match this round.

    Normally ``current_bet``. Whenever at most one seat in the hand has
    chips, nobody can contest more than the other seats in the hand
    really put in this round, so that seat only has to match the largest
    round bet among them, never more than ``current_bet``. If it already
    has, betting is over (betting_closed); if not, it may call up to that
    amount or fold, and it cannot raise (can_raise: nobody could answer).

    Example: the human posted a small blind of 10, the big blind is
    all-in for 5 and the dealer folds: the bet to match is 5, which the
    human has covered, so the hand runs out without asking for a call.
    Engines lower their current bet to this value after every action.

    in_hand, stacks and round_bets are per-seat lists.
    """
    seats = range(min(len(in_hand), len(stacks), len(round_bets)))
    actors = [
        seat
        for seat in seats
        if in_hand[seat] and stacks[seat] > 0
    ]

    if len(actors) > 1:
        return current_bet

    others = [
        round_bets[seat]
        for seat in seats
        if in_hand[seat] and seat not in actors
    ]

    if not others:
        return current_bet

    return min(current_bet, max(others))


def can_raise(seat, in_hand, stacks, round_bets, current_bet, reopened=True):
    """Return True if ``seat`` may bet (nothing bet yet) or raise now.

    All of these must hold:

    * the seat is in the hand and has chips;
    * ``reopened``: betting is open to it (False when the seat already
      acted and has since faced only short all-in raises);
    * it can put in more than ``current_bet`` this round;
    * another seat in the hand has chips, so somebody can respond.

    in_hand, stacks and round_bets are per-seat lists.
    """
    if not (0 <= seat < min(len(in_hand), len(stacks), len(round_bets))):
        return False

    if not in_hand[seat] or stacks[seat] <= 0:
        return False

    if not reopened:
        return False

    if round_bets[seat] + stacks[seat] <= current_bet:
        return False

    return any(
        other != seat and in_hand[other] and stacks[other] > 0
        for other in range(min(len(in_hand), len(stacks)))
    )


def minimum_raise_to(current_bet, last_full_raise, minimum_bet):
    """Return the smallest legal total for a bet or a full raise.

    Nothing bet yet: ``minimum_bet``. Otherwise the current bet plus the
    last full bet or raise this round (``minimum_bet`` before there was one).
    """
    if current_bet <= 0:
        return minimum_bet

    return current_bet + (last_full_raise if last_full_raise > 0 else minimum_bet)


def classify_wager(current_bet, new_total, minimum_raise_size):
    """Classify a bet or raise to ``new_total`` against ``current_bet``.

    Returns ``(increase, full)``. ``increase`` is how far the bet to call
    rises (0 or less: it does not rise, so the wager is only a call).
    ``full`` is True when the increase is at least ``minimum_raise_size``.
    Only a full wager sets the next minimum raise, becomes the last raise
    and reopens betting; a short all-in only lifts the bet to call.
    """
    increase = new_total - current_bet

    return increase, increase > 0 and increase >= minimum_raise_size


def betting_reopened(has_acted, round_bet, current_bet, full_raise_size):
    """Return True if a seat may bet or raise again (TDA Rule 47, no-limit).

    has_acted: the seat has acted since the last full bet or raise.
    round_bet: its chips in this round. A seat with chips that has acted
    matched the bet to call (or set it) when it did, so this is the bet
    level it last acted at.
    full_raise_size: the size a full raise needs now (the last full bet
    or raise this round, or the minimum bet before there was one).

    A seat that has not acted since the last full wager may raise. A seat
    that already acted may raise again only when it now faces at least a
    full raise in total: short all-ins that together add up to a full
    raise reopen betting for it, one short all-in below a full raise does
    not. Fixed-limit Stud keeps its own rule (short all-ins never reopen).
    """
    if not has_acted:
        return True

    return current_bet - round_bet >= max(1, full_raise_size)


# ==================================================
# HAND AND SESSION FLOW
#
# When betting is over for the hand and when the
# session is over. Plain per-seat lists again.
# ==================================================

def betting_closed(in_hand, stacks, round_bets, current_bet):
    """Return True when nobody can bet any more this hand.

    At most one seat still in the hand has chips (the rest are all-in),
    so nobody could answer a bet, and that seat has matched the bet it
    must match (bet_to_match: never more than the other seats in the
    hand put in this round). The engine then deals the remaining streets
    or draws without betting (an all-in run-out).

    in_hand, stacks and round_bets are per-seat lists.
    """
    actors = [
        seat
        for seat in range(min(len(in_hand), len(stacks)))
        if in_hand[seat] and stacks[seat] > 0
    ]

    if len(actors) > 1:
        return False

    target = bet_to_match(in_hand, stacks, round_bets, current_bet)

    return all(round_bets[seat] >= target for seat in actors)


def session_over(stacks, human_seat=0):
    """Return True when the session cannot go on.

    That is when the human has no chips left, or no other seat has
    chips. A seat is busted at 0 chips; any stack above 0 can still play
    a hand (all-in on its forced bet if it is short). Check it between
    hands: during a hand an all-in seat has 0 chips but is still playing.
    """
    return (
        stacks[human_seat] <= 0
        or not any(
            stack > 0
            for seat, stack in enumerate(stacks)
            if seat != human_seat
        )
    )
