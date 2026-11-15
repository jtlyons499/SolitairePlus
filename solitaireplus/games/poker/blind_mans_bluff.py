import random
import time
from collections import deque
from solitaireplus.games.poker.niche_common import RANK_VALUES, build_standard_deck, card_key, round_chip_amount
from solitaireplus.games.poker.ai import (PokerOpponentModel, decide_poker_action, get_poker_personality,
                      choose_poker_open_bet_amount, choose_poker_raise_to_amount)
from solitaireplus.games.poker.core import (award_pots, betting_closed, betting_reopened, build_pots, can_raise,
                                            classify_wager, format_poker_display_name, hand_nets,
                                            hand_outcome, hand_winners, minimum_raise_to, session_over,
                                            settle_fold_win)
from solitaireplus.games.poker.npc_inputs import (FINAL_ROUND_CAP, grudge_seats, npc_decision_inputs,
                                                  observe_public_action, opponent_rows, reset_session_memory,
                                                  soft_bet_cap, table_identities)
from solitaireplus.games.poker.strategy import PokerTableReads
from solitaireplus.npc.personality import PokerGrudgeMemory
from solitaireplus.npc.personality_chat import game_trait_chat
from solitaireplus.games.poker.holdem_chat import npc_action_chat_chance, npc_action_chat_event


class BlindMansBluffGame:
    """Forehead poker: one full betting round; only opponents' cards are visible.

    Check, bet, call, raise and fold use real round contributions. All-ins create
    side pots and short all-in raises do not reopen an already-acted player's
    raise rights. Highest rank wins each eligible pot; equal ranks split it,
    with odd chips from the opener round the table (core.split_pot).
    A seat short of the ante antes all it has and plays the hand all-in;
    the session ends when the human, or every opponent, has 0 chips.
    With npc_delay_seconds > 0 each NPC turn waits for that thinking pause
    (pending_npc_at) and update() runs it; with 0 NPC turns run at once.
    """
    # There is no Blind Man's Bluff career rating, so NPC skill keeps the skill
    # tier; the key also names this game's rival-learning memories.
    rating_game_key = "blind_mans_bluff"

    # The stage name of the single betting round in NPC contexts and table reads.
    BETTING_STAGE = "forehead_bet"

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.npcs = []
        self.starting_stack = self.player_stack = self.ante = self.bet_unit = 0
        self.npc_stacks = []
        self.pot = self.hand_number = self.current_bet = self.pot_awarded = 0
        self.deck, self.cards, self.folded, self.live_at_start = [], [], [], []
        self.phase, self.bet_state, self.result_text = "idle", "", ""
        self.bettor_index = None
        self.hand_complete = self.session_complete = False
        self.last_winner_indexes, self.last_actions, self.last_chat = [], [], []
        self.hands_played = self.hands_won = self.hands_lost = self.hands_tied = 0
        self.reward_claimed = False
        self.opening_index = self.current_actor = 0
        self.round_bets, self.hand_contributions = [], []
        self.pending, self.raise_rights = set(), set()
        self.last_raise_size = 1
        # The seat of the last full bet or raise (bettor_index is the last wager of any size).
        self.last_raiser = None
        # How the last hand was settled, in the shared record shape (core.award_pots).
        self.last_pot_awards, self.last_refunds, self.last_resolved_pot = [], {}, 0
        self.personality_memory = PokerGrudgeMemory()
        # Public reads of every seat, the human's tendencies and (career only)
        # the profile's rival-learning store, as at the other poker tables.
        self.table_reads = PokerTableReads()
        self.player_model = PokerOpponentModel()
        self.learning_store = None
        self.npc_ai_last_decisions = []
        self.presentation_events = deque(maxlen=128)
        # The NPC's thinking pause before each turn, in seconds. The screen sets
        # it from the table speed; the default 0 keeps the engine synchronous
        # (tests and simulations). pending_npc_at: when the queued NPC turn of
        # current_actor is due (time.monotonic()), 0 when none is queued.
        self.npc_delay_seconds = 0.0
        self.pending_npc_at = 0.0

    def start_session(self, npcs, starting_stack):
        self.npcs = list(npcs or [])[:3]
        # Grudges, quick chat, player tendencies and table reads start fresh;
        # the reads bind to the career rival-learning store.
        reset_session_memory(self, self.rating_game_key)
        self.starting_stack = max(0, int(starting_stack))
        self.player_stack = self.starting_stack
        self.npc_stacks = [self.starting_stack for _ in self.npcs]
        self.ante = round_chip_amount(self.starting_stack * 0.008, minimum=5)
        self.bet_unit = round_chip_amount(self.starting_stack * 0.02, minimum=10)
        self.hand_number = self.hands_played = self.hands_won = self.hands_lost = self.hands_tied = 0
        self.reward_claimed = self.session_complete = False
        return self.start_hand()

    def _stack_for(self, seat):
        return self.player_stack if seat == 0 else self.npc_stacks[seat - 1]

    def _commit(self, seat, amount, round_bet=True):
        paid = min(max(0, int(amount)), self._stack_for(seat))
        if seat == 0:
            self.player_stack -= paid
        else:
            self.npc_stacks[seat - 1] -= paid
        self.pot += paid
        if paid:
            self.presentation_events.append({"kind": "wager", "seat": seat, "amount": paid})
        self.hand_contributions[seat] += paid
        if round_bet:
            self.round_bets[seat] += paid
        return paid

    def get_npc(self, seat):
        return self.npcs[seat - 1] if 1 <= seat <= len(self.npcs) else {}

    def get_name(self, seat):
        return "You" if seat == 0 else format_poker_display_name(self.get_npc(seat).get("name", "Opponent"))

    def get_active_indexes(self, include_folded=False):
        return [seat for seat in self.live_at_start if include_folded or not self.folded[seat]]

    # Seat views: read-only per-seat lists for the shared table rules in core.py.
    # Seat 0 is the human, seat i is npcs[i-1]. round_bets and
    # hand_contributions are already per-seat lists.
    def seat_stacks(self):
        return [self.player_stack, *self.npc_stacks]

    def seat_in_hand(self):
        """Per seat: dealt into this hand and not folded."""
        live = set(self.live_at_start)
        return [seat in live and not self.folded[seat] for seat in range(len(self.cards))]

    def seat_at_table(self):
        """Per seat: not knocked out of the session, i.e. dealt into this hand (every seat
        with chips is). A seat all-in with 0 chips is still at the table until the hand ends."""
        live = set(self.live_at_start)
        return [seat in live for seat in range(len(self.npcs) + 1)]

    def start_hand(self):
        # Every seat with chips is dealt in. A seat short of the ante posts all
        # it has (_commit) and plays the hand all-in; with 0 chips left it is
        # never pending. The session ends only at 0 chips (core.session_over).
        eligible = [seat for seat in range(len(self.npcs) + 1) if self._stack_for(seat) > 0]
        if session_over(self.seat_stacks()) or len(eligible) < 2:
            self.session_complete = self.hand_complete = True
            self.phase = "session_over"
            self.result_text = "Not enough chips or opponents for another hand."
            return False
        self.presentation_events.clear()
        self.pending_npc_at = 0.0
        self.player_model.start_hand()
        self.hand_number += 1
        self.deck = build_standard_deck(self.rng)
        count = len(self.npcs) + 1
        self.cards, self.folded = [None]*count, [True]*count
        self.last_actions, self.last_chat = [""]*count, [""]*count
        self.round_bets, self.hand_contributions = [0]*count, [0]*count
        self.npc_ai_last_decisions = [None]*len(self.npcs)
        self.live_at_start = eligible
        self.pot = self.current_bet = self.pot_awarded = 0
        self.bettor_index = self.last_raiser = None
        self.phase = "betting"
        self.hand_complete = False
        self.result_text = "You can see everyone else's card, but not your own."
        self.last_winner_indexes = []
        self.last_pot_awards, self.last_refunds, self.last_resolved_pot = [], {}, 0
        for seat in eligible:
            self.folded[seat] = False
            self._commit(seat, self.ante, round_bet=False)
            self.cards[seat] = self.deck.pop()
        self.last_raise_size = self._base_minimum()
        self.opening_index = eligible[(self.hand_number - 1) % len(eligible)]
        self.current_actor = self.opening_index
        self.pending = {seat for seat in eligible if self._stack_for(seat) > 0}
        self.raise_rights = set(self.pending)
        self._advance(self.current_actor, inclusive=True)
        return True

    def get_visible_cards_for(self, viewer_index):
        return [
            self.cards[index]
            for index in self.get_active_indexes()
            if index != viewer_index and self.cards[index] is not None
        ]

    def _npc_hidden_card_strength(self, table_index):
        """Exact expected showdown share from the NPC's legal information.

        The NPC knows all active opponent cards and treats its own forehead card
        as any card remaining in the deck. Suits do not break Blind Man's Bluff
        ties, matching the supplied highest-card rule.
        """
        visible_active = self.get_visible_cards_for(table_index)
        if not visible_active:
            return 0.5

        # Folded forehead cards are still visible and therefore known to be
        # unavailable as the NPC's own card, even though they no longer matter
        # when deciding which live rank must be beaten.
        known_other_cards = [
            self.cards[index]
            for index in self.live_at_start
            if index != table_index and self.cards[index] is not None
        ]
        visible_keys = {card_key(card) for card in known_other_cards}
        unseen = [
            card for card in build_standard_deck(random.Random(0))
            if card_key(card) not in visible_keys
        ]
        if not unseen:
            return 0.5

        max_visible = max(RANK_VALUES[card["rank"]] for card in visible_active)
        visible_max_count = sum(
            1 for card in visible_active
            if RANK_VALUES[card["rank"]] == max_visible
        )

        total_value = 0.0
        for candidate in unseen:
            value = RANK_VALUES[candidate["rank"]]
            if value > max_visible:
                total_value += 1.0
            elif value == max_visible:
                total_value += 1.0 / (visible_max_count + 1.0)
        return total_value / len(unseen)

    def _base_minimum(self):
        return max(self.ante, round_chip_amount(self.starting_stack * 0.01, minimum=5))

    def get_player_amount_to_call(self):
        return min(self.player_stack, max(0, self.current_bet - self.round_bets[0])) if self.round_bets else 0

    def _can_raise(self, seat):
        # The shared rule (core.can_raise); raise_rights holds the seats that have not
        # acted since the last full bet or raise. A seat that has acted may raise again
        # once the short all-ins it faces add up to a full raise (core.betting_reopened).
        if not 0 <= seat < len(self.round_bets):
            return False
        reopened = betting_reopened(seat not in self.raise_rights, self.round_bets[seat],
                                    self.current_bet, self.last_raise_size)
        return can_raise(seat, self.seat_in_hand(), self.seat_stacks(), self.round_bets,
                         self.current_bet, reopened=reopened)

    def can_player_raise(self):
        """May the human bet or raise now? The prompts name raising only then."""
        return self._can_raise(0)

    def get_player_response_prompt(self):
        """The engine's prompt for the human's turn: it names raising only when the
        raise button is offered (get_player_actions), as at the Five-O table."""
        due = self.get_player_amount_to_call()
        if due:
            return f"Call ${due:,}, raise, or fold." if self.can_player_raise() else f"Call ${due:,} or fold."
        return "Check or choose a wager." if self.can_player_raise() else "Check."

    def get_max_open_bet(self):
        return self.player_stack if self._can_raise(0) else 0

    def get_min_open_bet(self):
        return min(self.get_max_open_bet(), self._base_minimum())

    def get_minimum_raise_to(self):
        return minimum_raise_to(self.current_bet, self.last_raise_size, self._base_minimum())

    def get_player_bet_presets(self):
        raising = self.current_bet > 0
        maximum = self.player_stack + (self.round_bets[0] if raising else 0)
        if not self._can_raise(0):
            return []
        minimum = min(maximum, self.get_minimum_raise_to() if raising else self._base_minimum())
        raw = [("MIN", minimum),
               ("1/2 POT", max(minimum, self.current_bet + int(self.pot*0.5))),
               ("POT", max(minimum, self.current_bet + self.pot)), ("MAX", maximum)]
        seen, presets = set(), []
        for label, amount in raw:
            amount = max(minimum, min(maximum, int(amount)))
            if amount not in seen:
                presets.append((label, amount))
                seen.add(amount)
        return presets

    def get_effective_bet_unit(self):
        return self.get_min_open_bet()

    def get_player_actions(self):
        if self.hand_complete or self.phase != "betting" or self.current_actor != 0 or 0 not in self.pending:
            return []
        due = max(0, self.current_bet - self.round_bets[0])
        actions = ["fold", "call"] if due else ["check"]
        if self._can_raise(0):
            actions.append("raise" if self.current_bet else "bet")
        return actions

    def _opponent_rows(self, seat):
        """Public rows (npc_inputs.opponent_rows) for every other seat in the hand."""
        names = [self.get_name(other) for other in range(len(self.npcs) + 1)]
        return opponent_rows(seat, self.get_active_indexes(), names, table_identities(self.npcs),
                             self.seat_stacks(), self.round_bets)

    def get_npc_grudge_context(self, npc_index):
        """The NPC's grudge context now (PokerGrudgeMemory.context), as at every table."""
        seat = npc_index + 1
        return self.personality_memory.context(self.get_npc(seat), seat, self._opponent_rows(seat),
                                               self.last_raiser, self.hand_number)

    def _npc_context(self, seat):
        stack = self._stack_for(seat)
        round_bet = self.round_bets[seat]
        context = {
            "game": "blind_mans_bluff", "stage": self.BETTING_STAGE, "position": "unknown",
            "hand_strength": self._npc_hidden_card_strength(seat),
            "amount_to_call": max(0, self.current_bet - round_bet),
            "stack": stack, "pot": self.pot, "current_bet": self.current_bet,
            "current_round_bet": round_bet,
            # last_raiser: the last full bet or raise (bettor_index is any wager, for the UI).
            "can_raise": self._can_raise(seat), "last_raiser": self.last_raiser,
            "opponents_remaining": len(self.get_active_indexes()) - 1,
            "minimum_open_bet": self._base_minimum(),
            "minimum_raise_to": self.get_minimum_raise_to(),
            "minimum_raise_size": self.last_raise_size,
            "maximum_raise_to": stack + round_bet,
        }
        # The inputs every poker variant shares: traits, skill, cash on hand,
        # table reads, player tendencies and the grudge against the last raiser.
        context.update(npc_decision_inputs(
            npc=self.get_npc(seat), seat=seat, rating_game_key=self.rating_game_key,
            stack=stack, starting_stack=self.starting_stack, hand_number=self.hand_number,
            opponents=self._opponent_rows(seat), last_raiser=self.last_raiser,
            grudge_memory=self.personality_memory, table_reads=self.table_reads,
            player_model=self.player_model, player_active=0 in self.get_active_indexes(),
        ))
        # The single round is the final one: a rich NPC's soft cap is Hold'em's river cap.
        fraction, wealth_boost = FINAL_ROUND_CAP
        cap = soft_bet_cap(self.starting_stack, fraction, context["wealth_pressure"], wealth_boost,
                           self._base_minimum(), stack + round_bet)
        context["maximum_open_bet"] = min(stack, cap)
        context["soft_maximum_raise_to"] = min(stack + round_bet, cap)
        from solitaireplus.games.poker.quick_chat import get_npc_quick_chat_context
        from solitaireplus.games.poker.quick_chat_adapter import adapt_quick_chat_game
        context.update(get_npc_quick_chat_context(
            adapt_quick_chat_game(self, "blind_mans_bluff"),
            seat - 1,
        ))
        return context

    def _npc_take_turn(self, seat):
        context = self._npc_context(seat)
        decision = decide_poker_action(get_poker_personality(self.get_npc(seat)), context, self.rng)
        self.npc_ai_last_decisions[seat - 1] = decision
        action = decision["action"]
        amount = None
        if action == "bet":
            amount = choose_poker_open_bet_amount(context, decision["profile"], context["hand_strength"], decision["bluff"])
        elif action == "raise":
            amount = choose_poker_raise_to_amount(context, decision["profile"], context["hand_strength"], decision["bluff"])
        if amount is None and action in ("bet", "raise"):
            action = "call" if context["amount_to_call"] else "check"
        if not self._act(seat, action, amount):
            action = "call" if context["amount_to_call"] else "check"
            self._act(seat, action)
        # The shared table talk, as at every poker table: how often an NPC talks after
        # its action (npc_action_chat_chance), then what it says (game_trait_chat: a
        # strong grudge first, then the decision's tactic line, then the trait mix).
        event = npc_action_chat_event(action, self._stack_for(seat))
        if self.rng.random() < npc_action_chat_chance(self.get_npc(seat), event):
            self.last_chat[seat] = game_trait_chat(self, seat - 1, event, self.rng)

    def _act(self, seat, action, amount=None):
        if seat not in self.pending or self.hand_complete:
            return False
        due = max(0, self.current_bet - self.round_bets[seat])
        pot_before, paid = self.pot, 0
        if action == "fold":
            self.folded[seat] = True
            self.last_actions[seat] = "Folded"
        elif action == "check":
            if due:
                return False
            self.last_actions[seat] = "Checked"
        elif action == "call":
            if not due:
                return False
            paid = self._commit(seat, due)
            self.last_actions[seat] = f"Called ${paid:,}"
        elif action in ("bet", "raise"):
            if not self._can_raise(seat) or (action == "bet") != (self.current_bet == 0):
                return False
            maximum = self.round_bets[seat] + self._stack_for(seat)
            minimum = self.get_minimum_raise_to() if self.current_bet else self._base_minimum()
            try:
                target = int(amount if amount is not None else max(minimum, self.current_bet + self.pot))
            except (TypeError, ValueError):
                return False
            target = min(maximum, max(minimum, target))
            if target <= self.current_bet:
                return False
            increase, full_raise = classify_wager(self.current_bet, target, self.last_raise_size)
            paid = self._commit(seat, target - self.round_bets[seat])
            self.current_bet, self.bettor_index = target, seat
            if full_raise:
                self.last_raise_size, self.last_raiser = increase, seat
                self.raise_rights = {other for other in self.get_active_indexes() if self._stack_for(other) > 0}
                self.pending = set(self.raise_rights)
            else:
                self.pending.update(other for other in self.get_active_indexes()
                                    if self._stack_for(other) > 0 and self.round_bets[other] < target)
            self.last_actions[seat] = f"{'Bet' if action == 'bet' else 'Raised to'} ${target:,}"
        else:
            return False
        if action in ("check", "fold"):
            self.presentation_events.append({"kind": action, "seat": seat, "amount": 0})
        # Every seat still at the table reads the action; the human's also
        # feeds the player-tendency model.
        if seat == 0:
            self.player_model.record_action(action, stage=self.BETTING_STAGE, amount_to_call=due,
                                            pot_before=pot_before, amount=paid)
        observe_public_action(self, action, seat, stage=self.BETTING_STAGE, amount=paid,
                              round_total=self.round_bets[seat], facing_amount=due)
        self.pending.discard(seat)
        self.raise_rights.discard(seat)
        return True

    def _advance(self, after, inclusive=False):
        count = len(self.npcs) + 1
        search_from = after if inclusive else (after + 1) % count
        while not self.hand_complete:
            active = self.get_active_indexes()
            if len(active) == 1:
                self._award_single_survivor(active[0])
                return
            self.pending.intersection_update(seat for seat in active if self._stack_for(seat) > 0)
            # With every call settled and nobody left to respond, a free option
            # cannot create a pot: straight to the showdown (core.betting_closed).
            if betting_closed(self.seat_in_hand(), self.seat_stacks(), self.round_bets, self.current_bet):
                self.pending.clear()
            if not self.pending:
                self._showdown()
                return
            seat = next((search_from + offset) % count for offset in range(count)
                        if (search_from + offset) % count in self.pending)
            self.current_actor = seat
            if seat == 0:
                self.bet_state = "player_response" if self.current_bet > self.round_bets[0] else "player_open"
                self.result_text = self.get_player_response_prompt()
                return
            if self.npc_delay_seconds > 0:
                # The NPC thinks first; update() takes its turn once it is due.
                # bet_state is cleared so the human's last prompt is not shown meanwhile.
                self.pending_npc_at = time.monotonic() + self.npc_delay_seconds
                self.bet_state = ""
                self.result_text = f"{self.get_name(seat)} is thinking…"
                return
            self._npc_take_turn(seat)
            search_from = (seat + 1) % count

    def update(self, now=None):
        """Take the queued NPC turn once its thinking pause is over.

        now: the time.monotonic() value to test against (default: the clock).
        Returns True if an NPC acted. The hand then moves on as usual: to the
        human, to the next NPC's pause, or to the showdown.
        """
        if not self.pending_npc_at or self.hand_complete:
            return False
        if (time.monotonic() if now is None else now) < self.pending_npc_at:
            return False
        seat = self.current_actor
        self.pending_npc_at = 0.0
        self._npc_take_turn(seat)
        self._advance(seat)
        return True

    def _player_action(self, action, amount=None):
        if action not in self.get_player_actions() or not self._act(0, action, amount):
            return False
        self._advance(0)
        return True

    def player_check(self):
        return self._player_action("check")

    def player_bet(self, amount=None):
        return self._player_action("bet", amount)

    def player_raise(self, amount=None):
        return self._player_action("raise", amount)

    def player_call(self):
        return self._player_action("call")

    def player_fold(self):
        return self._player_action("fold")

    def _credit(self, seat, amount, won=False):
        # won: the seat won or tied the hand (core.hand_outcome). A payout that is only
        # its own chips back, or a pot it collected uncontested without making money on
        # the hand, is not a win: the table plays the win sound only for a won payout, as
        # at the Hold'em tables.
        if amount:
            self.presentation_events.append({"kind": "payout", "seat": seat, "amount": amount,
                                             "won": bool(won)})
        if seat == 0:
            self.player_stack += amount
        else:
            self.npc_stacks[seat - 1] += amount

    def _award_single_survivor(self, seat):
        # core.settle_fold_win: settled like a showdown with one live seat. The
        # survivor wins the pot of matched chips; uncalled chips go back to whoever
        # put them in, the survivor's own included (paid with its win, as a
        # showdown pays a seat its pots and refunds together).
        winnings, refunds = settle_fold_win(self.hand_contributions, seat)
        self.pot_awarded = winnings
        self._credit(seat, winnings + refunds.get(seat, 0), won=True)
        for other, amount in sorted(refunds.items()):
            if other != seat:
                self._credit(other, amount)
        self.pot = 0
        self.last_winner_indexes = [seat]
        # The same record shape as a showdown pot.
        self.last_pot_awards = [{"amount": winnings, "eligible": [seat], "winners": [seat],
                                 "payouts": {seat: winnings}, "share": winnings,
                                 "remainder": 0, "hand": ""}]
        self.last_refunds = dict(refunds)
        self.last_resolved_pot = winnings
        if seat == 0:
            self.hands_won += 1
        else:
            self.hands_lost += 1
        winner = "You win" if seat == 0 else f"{self.get_name(seat)} wins"
        self.result_text = f"{winner} ${winnings:,} after the folds."
        for other, amount in sorted(refunds.items()):
            owner = "you" if other == 0 else self.get_name(other)
            self.result_text += f" Uncalled ${amount:,} returned to {owner}."
        self._finish_hand()

    def _showdown(self):
        """Settle the hand with the shared pot rules in core.py.

        Uncalled chips (and any layer no live seat paid into) go back to their
        owners; each pot goes to the highest live card, ties split with odd chips
        from the opener round the table. The opener counts as the first seat
        left of the dealer.
        """
        active = self.get_active_indexes()
        count = len(self.cards)
        pots, refunds = build_pots(self.hand_contributions, [seat in active for seat in range(count)])
        scores = {seat: RANK_VALUES[self.cards[seat]["rank"]] for seat in active}
        awards, totals = award_pots(pots, scores, (self.opening_index - 1) % count, count)
        nets = hand_nets(self.hand_contributions, awards, refunds)
        for seat in range(count):
            self._credit(seat, totals.get(seat, 0) + refunds.get(seat, 0),
                         won=hand_outcome(awards, seat, nets) != "lost")
        self.pot = 0
        self.last_pot_awards, self.last_refunds = awards, dict(refunds)
        self.last_resolved_pot = sum(award["amount"] for award in awards)
        self.pot_awarded = self.last_resolved_pot
        # core.hand_winners: a contested pot (two or more eligible seats) is won; a pot a
        # seat collected uncontested is won only when the seat made money on the hand
        # (otherwise it still pays the seat, but is not a win).
        self.last_winner_indexes = hand_winners(awards, nets)
        collectors = sorted(seat for seat, amount in totals.items() if amount > 0)
        outcome = hand_outcome(awards, 0, nets)
        if outcome == "won":
            self.hands_won += 1
        elif outcome == "tied":
            self.hands_tied += 1
        else:
            self.hands_lost += 1
        # Every live card is shown: a seat that bet or raised and won no pot
        # (core.hand_winners) showed a weak holding. Only a seat that lost a
        # contested pot resents its winners, by how much it put in.
        for seat in active:
            observe_public_action(self, "showdown_hand", seat, stage=self.BETTING_STAGE,
                                  weak=seat not in self.last_winner_indexes)
        self.personality_memory.record_showdown(
            awards, grudge_seats(self.npcs, self.hand_contributions),
            self.hand_number, self.starting_stack)
        parts = [f"{self.get_name(seat)} ${totals[seat]:,}" for seat in collectors]
        self.result_text = "Payouts: " + "; ".join(parts) + "."
        for seat, amount in sorted(refunds.items()):
            owner = "you" if seat == 0 else self.get_name(seat)
            self.result_text += f" Uncalled ${amount:,} returned to {owner}."
        self._finish_hand()

    def _finish_hand(self):
        self.hand_complete = True
        self.phase, self.bet_state = "showdown", ""
        self.current_actor = -1
        self.pending_npc_at = 0.0
        self.hands_played += 1
        self.session_complete = session_over(self.seat_stacks())

    def can_start_next_hand(self):
        return self.hand_complete and not self.session_complete

    def get_session_net(self):
        return self.player_stack - self.starting_stack
