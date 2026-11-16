"""Party-room rules on the host (B70 Roulette, B71-B74, B76-B78 and the BMB pots).

Every test builds the authority with a seeded ``random.Random`` and drives it with one
fake millisecond clock (``now``), the way room_session.RoomTable does on the host.
Guests are identities 1-4; seats are 0-3 with the host in seat 0.
"""
import json
import random
import unittest

from party_authority import BlindBluffAuthority, RouletteAuthority, ScoreFourAuthority
from solitaireplus.games.cards.score_four import check_solution


def card(rank, suit='Spades'):
    return {'rank': rank, 'suit': suit}


def make(cls, guests=(1,), seed=7, npc_seats=()):
    authority = cls('Host', rng=random.Random(seed))
    for identity in guests:
        authority.join(identity, f'Guest {identity}')
    for seat in npc_seats:
        assert authority.act(0, 'npc_toggle', {'seat': seat}, authority.revision)
    return authority


def start(authority, now=1000):
    authority.update(now)
    assert authority.act(0, 'start', 0, authority.revision), 'start refused'
    return authority


def identity_of(authority, seat):
    return next(identity for identity, owned in authority.humans.items() if owned == seat)


def bluff_act(authority, seat, action, amount=0):
    """Act for the human in ``seat`` through the public act() path."""
    return authority.act(identity_of(authority, seat), action, amount, authority.revision)


def ghost(authority, seat):
    row = authority.seat_data[seat]
    return row['kind'] == 'Human' and row['identity'] not in authority.connections


def finish_bluff_hand(authority, action='fold', limit=40):
    """Play the hand out: connected humans take ``action``; NPC and disconnected seats
    act on the host clock once their pause is over."""
    for _ in range(limit):
        if authority.hand_complete:
            return
        seat = authority.current_actor
        if authority.seat_data[seat]['kind'] == 'NPC' or ghost(authority, seat):
            authority.update(max(authority.now, authority.npc_due))
        else:
            assert bluff_act(authority, seat, action), (seat, action)
    raise AssertionError('the hand did not finish')


def finish_bluff_hand_by_folds(authority):
    """Fold every human whose turn it is until one seat is left."""
    for _ in range(8):
        if authority.hand_complete:
            return
        seat = authority.current_actor
        assert authority.seat_data[seat]['kind'] == 'Human'
        assert bluff_act(authority, seat, 'fold')
    raise AssertionError('the hand did not finish')


def next_bluff_hand(authority):
    authority.update(authority.result_until)
    assert not authority.hand_complete


class RouletteCountdownTests(unittest.TestCase):
    def test_roulette_countdown_keeps_revision(self):
        table = start(make(RouletteAuthority))
        revision = table.revision
        self.assertEqual(table.deadline, 1000 + table.bet_seconds * 1000)
        for now in (1500, 2001, 3001, 9999):
            table.update(now)
            self.assertEqual(table.revision, revision, f'revision moved at {now}')
        view = table.view(1)
        self.assertEqual(view['seconds_left'], 17)  # ceil((26000 - 9999) / 1000)
        self.assertEqual(view['countdown_at'], table.deadline)
        self.assertEqual(view['host_now'], 9999)
        json.dumps(view)
        # A guest action sent with the revision it saw before the countdown ticked is legal.
        self.assertTrue(table.act(1, 'bet', {'type': 'color', 'value': 'red', 'amount': 50}, revision))
        # Outside betting there is no countdown to show.
        table.update(table.deadline)
        self.assertEqual(table.phase, 'spinning')
        view = table.view(1)
        self.assertIsNone(view['countdown_at'])
        self.assertEqual(view['seconds_left'], 0)
        self.assertEqual(view['host_now'], table.deadline - 4500)


class LateJoinTests(unittest.TestCase):
    def test_bluff_late_joiner_seated_at_next_hand(self):
        table = start(make(BlindBluffAuthority, guests=(1,)))
        table.join(2, 'Late Lou')
        self.assertEqual(table.waiting, [(2, 'Late Lou')])
        self.assertIn('Late Lou will join at the next hand', table.notice)
        self.assertNotIn(2, table.humans)
        finish_bluff_hand_by_folds(table)
        next_bluff_hand(table)
        seat = table.humans[2]
        self.assertEqual(seat, 2)
        self.assertEqual(table.waiting, [])
        row = table.seat_data[seat]
        self.assertEqual((row['kind'], row['identity'], row['name']), ('Human', 2, 'Late Lou'))
        # An empty seat buys in for the starting stack and is dealt into the hand.
        self.assertEqual(table.stacks[seat], table.starting_stack - table.ante)
        self.assertIsNotNone(table.cards[seat])
        self.assertFalse(table.folded[seat])
        self.assertFalse(table.view(2)['spectating'])
        self.assertEqual(table.view(2)['your_seat'], seat)

    def test_roulette_late_joiner_seated_at_next_spin(self):
        table = start(make(RouletteAuthority, guests=(1,)))
        table.join(2, 'Late Lou')
        self.assertIn('Late Lou will join at the next spin', table.notice)
        self.assertNotIn(2, table.humans)
        self.assertFalse(table.act(2, 'bet', {'type': 'color', 'value': 'red', 'amount': 10}, table.revision))
        table.update(table.deadline)            # spinning
        table.update(table.deadline)            # result
        self.assertEqual(table.phase, 'result')
        self.assertNotIn(2, table.humans)
        table.update(table.deadline)            # next betting round
        self.assertEqual(table.phase, 'betting')
        seat = table.humans[2]
        self.assertEqual(seat, 2)
        self.assertEqual(table.stacks[seat], table.starting_stack)
        self.assertEqual(table.seat_data[seat]['stack'], table.starting_stack)
        self.assertFalse(table.view(2)['spectating'])
        self.assertTrue(table.act(2, 'bet', {'type': 'color', 'value': 'red', 'amount': 10}, table.revision))
        self.assertEqual(table.stacks[seat], table.starting_stack - 10)

    def test_score_four_late_joiner_seated_on_return_to_lobby(self):
        table = start(make(ScoreFourAuthority, guests=(1,)))
        table.join(2, 'Late Lou')
        self.assertIn('Late Lou will join when the table returns to the lobby', table.notice)
        for _ in range(3):
            table._win_round(0)
            if table.match_winner is None:
                table._start_round(table.now)
        self.assertEqual(table.match_winner, 0)
        self.assertNotIn(2, table.humans)
        self.assertTrue(table.act(0, 'return_lobby', 0, table.revision))
        self.assertFalse(table.started)
        self.assertEqual(table.humans[2], 2)
        self.assertEqual(table.waiting, [])
        lobby = table.view(2)
        self.assertEqual(lobby['type'], 'lobby')
        self.assertEqual(lobby['your_seat'], 2)
        self.assertEqual(lobby['seats'][2]['kind'], 'Human')
        self.assertEqual(lobby['waiting_names'], [])

    def test_waiter_takes_ghost_then_npc_seat_and_is_queued_once(self):
        # Seats: host, guest 1, guest 2, NPC in seat 3 (the NPC seat is filled by the
        # lobby toggle). Two joiners wait; at the next hand the first takes the
        # disconnected guest's seat with its stack and the second the NPC's seat.
        table = make(BlindBluffAuthority, guests=(1, 2), npc_seats=(3,))
        start(table)
        table.join(5, 'Five')
        table.join(6, 'Six')
        table.join(5, 'Five again')          # a duplicate join is ignored
        self.assertEqual([identity for identity, _ in table.waiting], [5, 6])
        table.leave(2)                       # guest 2's seat becomes a ghost seat
        finish_bluff_hand(table)
        ghost_stack = table.stacks[2]
        npc_stack = table.stacks[3]
        self.assertGreater(npc_stack, 0)
        next_bluff_hand(table)
        self.assertEqual(table.humans[5], 2)
        self.assertEqual(table.humans[6], 3)
        self.assertEqual(table.waiting, [])
        # Both inherit the seat's chips (minus this hand's ante).
        self.assertEqual(table.stacks[2], ghost_stack - table.ante)
        self.assertEqual(table.stacks[3], npc_stack - table.ante)
        self.assertEqual(table.seat_data[3]['kind'], 'Human')
        self.assertIsNone(table.seat_data[3]['npc'])
        # Every seat is now a connected human, so a new joiner waits, once, hand after hand.
        table.join(7, 'Seven')
        for _ in range(3):
            finish_bluff_hand_by_folds(table)
            next_bluff_hand(table)
            self.assertEqual(table.waiting, [(7, 'Seven')])

    def test_lobby_waiter_takes_a_seat_freed_in_the_lobby(self):
        table = make(ScoreFourAuthority, guests=(1, 2, 3))
        table.join(4, 'Four')
        self.assertEqual(table.waiting, [(4, 'Four')])
        self.assertEqual(table.lobby_view(4)['waiting_names'], ['Four'])
        table.leave(2)
        self.assertEqual(table.humans[4], 2)
        self.assertEqual(table.waiting, [])
        self.assertEqual(table.lobby_view(4)['your_seat'], 2)
        # A waiter who leaves is dropped from the list, and the room hears of it.
        table.join(5, 'Five')
        revision = table.revision
        table.leave(5)
        self.assertEqual(table.waiting, [])
        self.assertGreater(table.revision, revision)

    def test_broke_seat_buys_in_for_the_joiner(self):
        # Seat 3 holds an NPC, so there is no empty seat: the joiner takes the
        # disconnected guest's seat, and a broke seat buys in for the starting stack.
        table = start(make(BlindBluffAuthority, guests=(1, 2), npc_seats=(3,)))
        table.join(5, 'Five')
        table.leave(2)
        finish_bluff_hand(table)
        moved = table.stacks[2]
        table.stacks[2] = 0
        table.seat_data[2]['stack'] = 0
        table.stacks[0] += moved
        table.seat_data[0]['stack'] = table.stacks[0]
        next_bluff_hand(table)
        self.assertEqual(table.humans[5], 2)
        self.assertEqual(table.seat_data[3]['kind'], 'NPC')
        self.assertEqual(table.stacks[2], table.starting_stack - table.ante)
        self.assertFalse(table.seat_data[2]['spectator'])
        self.assertFalse(table.folded[2])


class DisconnectTests(unittest.TestCase):
    def three_handed(self):
        table = start(make(BlindBluffAuthority, guests=(1, 2)))
        self.assertEqual(table.current_actor, 0)
        return table

    def test_disconnected_actor_checks_after_a_pause(self):
        table = self.three_handed()
        self.assertTrue(bluff_act(table, 0, 'check_call'))
        self.assertEqual(table.current_actor, 1)
        table.update(5000)
        table.leave(1)
        self.assertEqual(table.npc_due, 5600)
        table.update(5599)
        self.assertEqual(table.current_actor, 1)
        table.update(5600)
        self.assertEqual(table.actions[1], 'Checked')
        self.assertFalse(table.folded[1])
        self.assertEqual(table.current_actor, 2)

    def test_disconnected_actor_folds_to_a_bet(self):
        table = self.three_handed()
        self.assertTrue(bluff_act(table, 0, 'bet_raise', table.bet_unit))
        self.assertEqual(table.current_actor, 1)
        table.leave(1)
        table.update(table.npc_due)
        self.assertTrue(table.folded[1])
        self.assertEqual(table.actions[1], 'Folded')
        self.assertEqual(table.current_actor, 2)

    def test_disconnected_seat_acts_when_its_turn_comes(self):
        table = self.three_handed()
        table.update(2000)
        table.leave(2)                       # not the actor: no pause yet
        self.assertTrue(bluff_act(table, 0, 'bet_raise', table.bet_unit))
        self.assertTrue(bluff_act(table, 1, 'check_call'))
        self.assertEqual(table.current_actor, 2)
        self.assertEqual(table.npc_due, 2600)
        revision = table.revision
        table.update(2599)
        self.assertEqual(table.revision, revision)
        table.update(2600)
        self.assertTrue(table.folded[2])
        self.assertTrue(table.hand_complete)
        # The ghost seat keeps being dealt in and checks when nothing is owed.
        next_bluff_hand(table)
        self.assertFalse(table.folded[2])
        finish_bluff_hand(table, 'check_call')
        self.assertEqual(table.actions[2], 'Checked')


class FinishedTableTests(unittest.TestCase):
    def test_bluff_finishes_when_fewer_than_two_can_ante(self):
        table = start(make(BlindBluffAuthority, guests=(1,)))
        finish_bluff_hand_by_folds(table)
        loser = 1 if table.winners == [0] else 0
        table.stacks[loser] = table.ante - 1
        table.seat_data[loser]['stack'] = table.ante - 1
        table.update(table.result_until)
        self.assertTrue(table.finished)
        revision = table.revision
        for step in range(1, 6):
            table.update(table.result_until + step * 1000)
        self.assertEqual(table.revision, revision)
        view = table.view(1)
        self.assertEqual(view['phase'], 'finished')
        self.assertIsNone(view['current_actor'])
        self.assertFalse(table.act(0, 'check_call', 0, table.revision))

    def test_late_joiner_deals_a_finished_bluff_table_back_in(self):
        # The joiner's buy-in gives two seats that can ante, so the notice comes true.
        table = start(make(BlindBluffAuthority, guests=(1,)))
        finish_bluff_hand_by_folds(table)
        loser = 1 if table.winners == [0] else 0
        table.stacks[loser] = 0
        table.seat_data[loser]['stack'] = 0
        table.update(table.result_until)
        self.assertTrue(table.finished)
        hand = table.hand_number
        table.join(5, 'Late')
        self.assertIn('Late will join at the next hand', table.notice)
        table.update(table.now + 16)
        self.assertFalse(table.finished)
        self.assertEqual(table.waiting, [])
        seat = table.humans[5]
        self.assertEqual(table.hand_number, hand + 1)
        self.assertFalse(table.hand_complete)
        self.assertIsNotNone(table.cards[seat])
        self.assertEqual(table.stacks[seat], table.starting_stack - table.ante)
        self.assertEqual(table.view(5)['phase'], 'betting')
        self.assertTrue(table.seat_data[loser]['spectator'])   # the broke seat still watches

    def test_full_finished_bluff_table_keeps_its_revision(self):
        # Nobody can be seated (every seat is a connected human): no retry, no revision spam.
        table = start(make(BlindBluffAuthority, guests=(1, 2, 3)))
        for seat in range(1, 4):
            table.stacks[seat] = 0
            table.seat_data[seat]['stack'] = 0
        table.current_actor = None
        table.hand_complete = True
        table.result_until = table.now + 10
        table.update(table.result_until)
        self.assertTrue(table.finished)
        table.join(9, 'Late')
        revision = table.revision
        for step in range(1, 6):
            table.update(table.now + step * 16)
        self.assertTrue(table.finished)
        self.assertEqual(table.waiting, [(9, 'Late')])
        self.assertEqual(table.revision, revision)

    def test_late_joiner_restarts_a_finished_roulette_table(self):
        table = start(make(RouletteAuthority, guests=(1,)))
        for seat in table._participants():
            table.stacks[seat] = 0
        table.update(table.deadline)            # spinning
        table.update(table.deadline)            # result
        table.update(table.deadline)            # everyone is broke
        self.assertEqual(table.phase, 'finished')
        rounds = table.round_number
        table.join(7, 'Late')
        self.assertIn('Late will join at the next spin', table.notice)
        table.update(table.now + 16)
        self.assertEqual(table.phase, 'betting')
        self.assertEqual(table.round_number, rounds + 1)
        seat = table.humans[7]
        self.assertEqual(table.stacks[seat], table.starting_stack)
        self.assertFalse(table.view(7)['spectating'])
        self.assertTrue(table.act(7, 'bet', {'type': 'color', 'value': 'red', 'amount': 10}, table.revision))


class GhostSeatTests(unittest.TestCase):
    def test_score_four_return_lobby_frees_ghost_seats(self):
        table = start(make(ScoreFourAuthority, guests=(1, 2)))
        table.leave(2)
        self.assertEqual(table.seat_data[2]['kind'], 'Human')     # kept during the match
        for _ in range(3):
            table._win_round(0)
            if table.match_winner is None:
                table._start_round(table.now)
        self.assertTrue(table.act(0, 'return_lobby', 0, table.revision))
        lobby = table.view(0)
        self.assertEqual(lobby['type'], 'lobby')
        self.assertEqual(lobby['seats'][2]['kind'], 'Empty')
        self.assertEqual(lobby['seats'][1]['kind'], 'Human')
        self.assertEqual(table._active_lobby_count(), 2)
        # The host can put an NPC in the freed seat again.
        self.assertTrue(table.act(0, 'npc_toggle', {'seat': 2}, table.revision))
        self.assertEqual(table.seat_data[2]['kind'], 'NPC')


class ScoreFourSolveTests(unittest.TestCase):
    def test_score_four_host_checks_the_guest_solve(self):
        table = start(make(ScoreFourAuthority, guests=(1,)))
        table.numbers = [8, 3, 1, 1]
        revision = table.revision
        good = [[0, '*', 1], [1, '*', 2], [2, '*', 3]]
        for claim in (0, None, 'solved', {}, {'steps': None}, {'steps': good[:2]},
                      {'steps': [[0, '+', 1], [1, '+', 2], [2, '+', 3]]}):
            with self.subTest(claim=claim):
                self.assertFalse(table.act(1, 'solved', claim, revision))
        self.assertEqual(table.revision, revision)
        self.assertIsNone(table.round_winner)
        self.assertTrue(check_solution(table.numbers, good))
        self.assertTrue(table.act(1, 'solved', {'steps': good}, revision))
        self.assertEqual(table.round_winner, 1)
        self.assertEqual(table.scores[1], 1)


class ShortAllInRaiseTests(unittest.TestCase):
    def test_short_all_in_raise_is_recorded_as_the_real_amount(self):
        table = start(make(BlindBluffAuthority, guests=(1,)))
        total = sum(table.stacks) + sum(table.contributions)
        self.assertTrue(bluff_act(table, 0, 'bet_raise', table.bet_unit))
        self.assertEqual(table.current_bet, 100)
        self.assertEqual(table._min_raise_to(), 200)
        # Seat 1 has 150 left: below the minimum raise, above the bet.
        moved = table.stacks[1] - 150
        table.stacks[1] = 150
        table.seat_data[1]['stack'] = 150
        total -= moved
        for amount in ('abc', None, True, 175.0, [200], {'to': 200}):
            with self.subTest(amount=amount):
                self.assertFalse(bluff_act(table, 1, 'bet_raise', amount))
        self.assertTrue(bluff_act(table, 1, 'bet_raise', 200))
        self.assertEqual(table.round_bets[1], 150)
        self.assertEqual(table.stacks[1], 0)
        self.assertEqual(table.current_bet, 150)
        self.assertEqual(table.actions[1], 'Raised to $150')
        self.assertEqual(table.last_raise, 100)         # a short raise is not a full raise
        self.assertEqual(table.current_actor, 0)
        view = table.view(0)
        self.assertEqual(view['current_bet'] - view['round_bets'][0], 50)
        self.assertFalse(view['can_raise'])             # nobody left to answer a raise
        self.assertFalse(bluff_act(table, 0, 'bet_raise', 1000))
        self.assertTrue(bluff_act(table, 0, 'check_call'))
        self.assertTrue(table.hand_complete)
        self.assertEqual(sum(table.stacks), total)

    def test_npc_short_stack_bet_is_its_stack(self):
        # An NPC with less than one bet unit left bets what it has.
        table = make(BlindBluffAuthority, guests=(), npc_seats=(1,))
        start(table)
        table.seat_data[1]['skill'] = 'elite'
        table.stacks[1] = 30
        table.seat_data[1]['stack'] = 30
        table.current_actor = 1
        table.pending = {1}
        table.raise_rights = {0, 1}
        table.rng = type('Rng', (), {'random': lambda self: 0.0, 'randint': lambda self, a, b: a,
                                     'uniform': lambda self, a, b: a, 'choice': lambda self, s: s[0]})()
        table._hidden_strength = lambda seat: 1.0
        table._npc_action(1, table.now)
        self.assertEqual(table.round_bets[1], 30)
        self.assertEqual(table.current_bet, 30)
        self.assertEqual(table.actions[1], 'Bet $30')


class RouletteBetTests(unittest.TestCase):
    def test_roulette_rejects_bets_below_the_minimum(self):
        table = start(make(RouletteAuthority, guests=(1,)))
        stack = table.stacks[1]
        for amount in (0, -5, True, False, '10', 10.0, None, [10]):
            with self.subTest(amount=amount):
                self.assertFalse(table.act(1, 'bet', {'type': 'color', 'value': 'red', 'amount': amount},
                                           table.revision))
        self.assertEqual(table.stacks[1], stack)
        self.assertEqual(table.bets[1], [])
        self.assertTrue(table.act(1, 'bet', {'type': 'color', 'value': 'red', 'amount': 1}, table.revision))
        self.assertEqual(table.bets[1], [{'type': 'color', 'value': 'red', 'amount': 1}])
        # A bet above the stack is limited to the stack.
        self.assertTrue(table.act(1, 'bet', {'type': 'number', 'value': '7', 'amount': 10 ** 9},
                                  table.revision))
        self.assertEqual(table.stacks[1], 0)
        self.assertEqual(table.bets[1][-1], {'type': 'number', 'value': '7', 'amount': stack - 1})


class BluffPotTests(unittest.TestCase):
    def four_humans(self):
        return start(make(BlindBluffAuthority, guests=(1, 2, 3)))

    def test_bmb_pots_use_the_shared_rules(self):
        # (1) Uncalled chips come back as a refund and are not won.
        table = self.four_humans()
        total = sum(table.stacks) + sum(table.contributions)
        table.cards = [card('9'), card('A'), card('5'), card('2')]
        table.stacks[1] = 60
        table.seat_data[1]['stack'] = 60
        total -= 4960 - 60
        self.assertTrue(bluff_act(table, 0, 'bet_raise', 100))
        self.assertTrue(bluff_act(table, 1, 'check_call'))       # all in for 60 more
        self.assertTrue(bluff_act(table, 2, 'fold'))
        self.assertTrue(bluff_act(table, 3, 'bet_raise', 600))
        self.assertTrue(bluff_act(table, 0, 'fold'))
        self.assertTrue(table.hand_complete)
        self.assertEqual(table.contributions, [140, 100, 40, 640])
        # Main pot 340 (seats 1 and 3 eligible) to seat 1's ace; seat 3 collects the
        # 80 nobody else could win and gets its uncalled 500 back.
        self.assertEqual(table.stacks[1], 340)
        self.assertEqual(table.last_refunds, {3: 500})
        self.assertEqual(table.winners, [1])
        self.assertEqual(table.view(3)['winners'], [1])
        self.assertEqual(sum(table.stacks), total)
        self.assertIn('Uncalled $500 returned to Guest 3', table.result_text)

        # (2) Odd chips go first to the seat left of the dealer (the seat before the opener).
        table = self.four_humans()
        finish_bluff_hand_by_folds(table)
        next_bluff_hand(table)
        self.assertEqual(table.current_actor, 1)                  # hand 2 opens at seat 1
        total = sum(table.stacks) + sum(table.contributions)
        table.cards = [card('K', 'Hearts'), card('4'), card('K', 'Clubs'), card('7')]
        self.assertTrue(bluff_act(table, 1, 'bet_raise', 101))
        self.assertTrue(bluff_act(table, 2, 'check_call'))
        self.assertTrue(bluff_act(table, 3, 'fold'))
        self.assertTrue(bluff_act(table, 0, 'check_call'))
        self.assertTrue(table.hand_complete)
        self.assertEqual(sum(table.contributions), 463)
        self.assertEqual(table.winners, [0, 2])
        award = table.last_pot_awards[0]
        self.assertEqual(award['payouts'], {2: 232, 0: 231})
        self.assertEqual(list(award['payouts']), [2, 0])
        self.assertEqual(sum(table.stacks), total)

        # (3) A layer only folded seats paid into goes back to them.
        table = self.four_humans()
        total = sum(table.stacks) + sum(table.contributions)
        table.cards = [card('Q'), card('3'), card('J'), card('8')]
        table.contributions = [100, 100, 300, 300]
        table.stacks = [table.stacks[0] - 60, table.stacks[1] - 60, table.stacks[2] - 260, table.stacks[3] - 260]
        table.folded = [False, False, True, True]
        table._showdown(table.now)
        self.assertEqual(table.last_refunds, {2: 200, 3: 200})
        self.assertEqual(table.last_pot_awards[0]['amount'], 400)
        self.assertEqual(sum(table.stacks), total)
        self.assertEqual(table.winners, [0])

        # (4) A short survivor of the folds wins only what it matched.
        table = self.four_humans()
        total = sum(table.stacks) + sum(table.contributions)
        table.contributions = [100, 400, 40, 40]
        table.stacks = [table.stacks[0] - 60, table.stacks[1] - 360, table.stacks[2], table.stacks[3]]
        table.folded = [False, True, True, True]
        before = table.stacks[0]
        table._award_single(0, table.now)
        self.assertEqual(table.stacks[0] - before, 280)            # 4 x 40 + 2 x 60
        self.assertEqual(table.last_refunds, {1: 300})
        self.assertEqual(table.winners, [0])
        self.assertEqual(sum(table.stacks), total)
        self.assertIn('wins $280', table.result_text)
        self.assertIn('Uncalled $300 returned to Guest 1', table.result_text)

    def test_folded_to_bettor_gets_uncalled_bet_back(self):
        table = self.four_humans()
        total = sum(table.stacks) + sum(table.contributions)
        self.assertTrue(bluff_act(table, 0, 'bet_raise', 300))
        for seat in (1, 2, 3):
            self.assertTrue(bluff_act(table, seat, 'fold'))
        self.assertTrue(table.hand_complete)
        self.assertEqual(table.winners, [0])
        self.assertEqual(table.last_refunds, {0: 300})
        self.assertEqual(table.last_pot_awards[0]['amount'], 160)
        self.assertEqual(sum(table.stacks), total)
        self.assertEqual(table.stacks[0], 5000 + 120)          # the other three antes

    def test_reraise_rights_follow_the_shared_rule(self):
        # Seat 0 bets 100 and seat 1 calls. Seat 2 goes all in short to 150: one short
        # raise does not reopen betting for seats that acted. Seat 3 goes all in short
        # to 210: together the short raises add 110, a full raise, so it reopens.
        table = self.four_humans()
        self.assertTrue(bluff_act(table, 0, 'bet_raise', 100))
        self.assertTrue(bluff_act(table, 1, 'check_call'))
        for seat, stack in ((2, 150), (3, 210)):
            table.stacks[seat] = stack
            table.seat_data[seat]['stack'] = stack
        self.assertTrue(bluff_act(table, 2, 'bet_raise', 150))
        self.assertEqual(table.current_bet, 150)
        self.assertFalse(table._can_raise(0))
        self.assertFalse(table._can_raise(1))
        self.assertTrue(bluff_act(table, 3, 'bet_raise', 210))
        self.assertEqual(table.current_bet, 210)
        self.assertEqual(table.current_actor, 0)
        self.assertTrue(table._can_raise(0))
        self.assertTrue(table.view(0)['can_raise'])
        self.assertTrue(bluff_act(table, 0, 'bet_raise', 400))
        self.assertEqual(table.current_actor, 1)
        self.assertTrue(table._can_raise(1))
        self.assertTrue(bluff_act(table, 1, 'check_call'))
        self.assertTrue(table.hand_complete)
        self.assertEqual(table.contributions, [440, 440, 190, 250])


if __name__ == '__main__':
    unittest.main()
