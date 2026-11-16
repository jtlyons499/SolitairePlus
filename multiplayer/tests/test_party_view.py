"""Party room client view: the Score-Four solve (B75, B76), the Roulette countdown (B70)
and the Blind Man's Bluff raise button.

The view is driven the way multiplayer/main.py drives it: draw a frame, then hand it
mouse clicks through PartyView.event. The table is a stand-in for room_session.RoomTable
with a recording act().
"""
import random
import unittest
from types import SimpleNamespace
from unittest import mock

import pygame

from party_authority import ScoreFourAuthority
from party_view import PartyView

SOLVE = [[0, '*', 1], [1, '*', 2], [2, '*', 3]]


def setUpModule():
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1366, 768))


class Appearance:
    def background(self, surface):
        surface.fill((10, 30, 25))

    def felt(self, surface, rect):
        pygame.draw.rect(surface, (20, 90, 50), rect)

    def avatar(self, surface, public, rect, name='Player'):
        pygame.draw.ellipse(surface, (90, 90, 90), rect)


def make_view():
    assets = SimpleNamespace(cards={}, back=pygame.Surface((150, 210)), portrait=lambda npc, rect: None)
    return PartyView(pygame.Surface((1366, 768)), assets, Appearance())


def seats():
    return [{'kind': 'Human', 'name': f'Player {i}', 'identity': i, 'skill': 'mid'} for i in range(4)]


def score_message(revision=5, round_number=1, numbers=(8, 3, 1, 1), phase='round'):
    return {'type': 'party_state', 'mode': 'score_four', 'phase': phase, 'revision': revision,
            'round_number': round_number, 'numbers': list(numbers), 'suits': ['Spades'] * 4,
            'scores': [0, 0, 0, 0], 'seats': seats(), 'your_seat': 1, 'ready_seats': []}


class Table(SimpleNamespace):
    def __init__(self, message, mode, results=()):
        super().__init__(message=message, mode=mode, pending=False, failed=False, hosting=False,
                         code='12345', public_profiles={}, leave_notice='', leave_notice_seq=0)
        self.calls = []
        self.results = list(results)

    def act(self, action, amount=0):
        self.calls.append((action, amount))
        return self.results.pop(0) if self.results else True


def click(view, table, pos):
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)
    return view.event(event, pos, table)


def number(view, table, index):
    assert click(view, table, view.score_number_rects[index].center)


def operator(view, table, symbol):
    assert click(view, table, view.score_operator_rects[symbol].center)


def button(view, action):
    return next(rect.center for rect, name in view.buttons if name == action)


def combine(view, table, first, symbol, second):
    number(view, table, first)
    operator(view, table, symbol)
    number(view, table, second)


class ScoreFourSolveTests(unittest.TestCase):
    def test_solve_is_retried_until_the_room_takes_it(self):
        view = make_view()
        table = Table(score_message(), 'score_four', results=[False, True])
        view.draw_score_four(table)
        combine(view, table, 0, '*', 1)
        combine(view, table, 1, '*', 2)
        self.assertEqual(table.calls, [])
        combine(view, table, 2, '*', 3)
        self.assertTrue(view.score_game.is_solved())
        # The click sent the solve and it failed; the next frame sends it again.
        self.assertEqual(table.calls, [('solved', {'steps': SOLVE})])
        view.draw_score_four(table)
        self.assertEqual(table.calls, [('solved', {'steps': SOLVE})] * 2)
        for _ in range(5):
            view.draw_score_four(table)
        self.assertEqual(len(table.calls), 2)
        # Nothing is sent while an action is waiting for its answer, and a new table
        # revision (the room changed under the solve) sends it once more.
        table.message = score_message(revision=6)
        table.pending = True
        view.draw_score_four(table)
        self.assertEqual(len(table.calls), 2)
        table.pending = False
        view.draw_score_four(table)
        view.draw_score_four(table)
        self.assertEqual(table.calls, [('solved', {'steps': SOLVE})] * 3)
        # Once the round is over nothing more is sent.
        table.message = score_message(revision=7, phase='round_result')
        view.draw_score_four(table)
        self.assertEqual(len(table.calls), 3)

    def test_steps_follow_undo_reset_and_a_new_round(self):
        view = make_view()
        table = Table(score_message(numbers=(6, 8, 3, 4)), 'score_four')
        view.draw_score_four(table)
        combine(view, table, 0, '+', 1)                    # 6 + 8 into tile 1
        self.assertEqual(view.score_steps, [[0, '+', 1]])
        number(view, table, 2)
        number(view, table, 2)                             # select and cancel: no step
        number(view, table, 3)
        number(view, table, 2)                             # reselect without an operator
        self.assertEqual(view.score_steps, [[0, '+', 1]])
        operator(view, table, '-')
        number(view, table, 1)                             # 3 - 14 into tile 1
        self.assertEqual(view.score_steps, [[0, '+', 1], [2, '-', 1]])
        click(view, table, button(view, 'score_undo'))
        self.assertEqual(view.score_steps, [[0, '+', 1]])
        self.assertEqual(view.score_game.values[1], 14)
        click(view, table, button(view, 'score_undo'))
        click(view, table, button(view, 'score_undo'))     # nothing left to undo
        self.assertEqual(view.score_steps, [])
        combine(view, table, 3, '*', 2)                    # 4 * 3 = 12 into tile 2
        combine(view, table, 0, '+', 1)
        self.assertEqual(len(view.score_steps), 2)
        click(view, table, button(view, 'score_reset'))
        self.assertEqual(view.score_steps, [])
        # Solve it: (8 - 6) * (3 * 4) = 24, sent with exactly these steps.
        combine(view, table, 0, '-', 1)                    # 6 - 8 = -2 into tile 1
        combine(view, table, 2, '*', 3)                    # 3 * 4 = 12 into tile 3
        combine(view, table, 3, '*', 1)                    # 12 * -2 = -24: not solved
        self.assertFalse(view.score_game.is_solved())
        self.assertEqual(table.calls, [])
        click(view, table, button(view, 'score_undo'))
        click(view, table, button(view, 'score_undo'))
        click(view, table, button(view, 'score_undo'))
        combine(view, table, 1, '-', 0)                    # 8 - 6 = 2 into tile 0
        combine(view, table, 2, '*', 3)
        combine(view, table, 3, '*', 0)
        self.assertTrue(view.score_game.is_solved())
        self.assertEqual(table.calls, [('solved', {'steps': [[1, '-', 0], [2, '*', 3], [3, '*', 0]]})])
        # The next round starts with no steps.
        table.message = score_message(revision=9, round_number=2, numbers=(1, 2, 3, 4))
        view.draw_score_four(table)
        self.assertEqual(view.score_steps, [])
        self.assertFalse(view.score_game.is_solved())

    def test_sent_steps_pass_the_host_check(self):
        host = ScoreFourAuthority('Host', rng=random.Random(4))
        host.join(1, 'Guest')
        host.update(1000)
        self.assertTrue(host.act(0, 'start', 0, host.revision))
        host.numbers = [6, 8, 3, 4]
        view = make_view()
        message = host.view(1)
        table = Table(message, 'score_four')
        table.act = lambda action, amount=0: host.act(1, action, amount, message['revision'])
        view.draw_score_four(table)
        combine(view, table, 1, '-', 0)
        combine(view, table, 2, '*', 3)
        combine(view, table, 3, '*', 0)
        self.assertEqual(host.round_winner, 1)

    def test_a_new_room_on_the_same_round_gets_its_own_cards(self):
        # One PartyView lasts the whole session (multiplayer/main.py). A player leaves room A
        # during round 1 and joins room B, which is also on round 1, with other cards.
        view = make_view()
        room_a = Table(score_message(revision=3, numbers=(1, 2, 3, 4)), 'score_four')
        view.draw_score_four(room_a)
        combine(view, room_a, 0, '+', 1)
        host = ScoreFourAuthority('Host', rng=random.Random(4))
        host.join(1, 'Guest')
        host.update(1000)
        self.assertTrue(host.act(0, 'start', 0, host.revision))
        host.numbers = [8, 3, 1, 1]
        message = host.view(1)
        self.assertEqual(message['round_number'], 1)
        room_b = Table(message, 'score_four')
        room_b.act = lambda action, amount=0: host.act(1, action, amount, message['revision'])
        view.draw_score_four(room_b)
        self.assertEqual(view.score_game.original_numbers, [8, 3, 1, 1])
        self.assertEqual(view.score_steps, [])
        self.assertFalse(view.score_game.is_solved())
        for step in SOLVE:
            combine(view, room_b, *step)
        self.assertEqual(host.round_winner, 1)
        # The same room on the same round keeps the board as it is.
        view.draw_score_four(room_b)
        self.assertTrue(view.score_game.is_solved())


class RouletteCountdownTests(unittest.TestCase):
    def message(self, **extra):
        message = {'type': 'party_state', 'mode': 'roulette', 'phase': 'betting', 'seconds_left': 25,
                   'revision': 3}
        message.update(extra)
        return message

    def test_countdown_runs_on_the_local_clock(self):
        view = make_view()
        table = Table(self.message(), 'roulette')
        self.assertEqual(view.roulette_seconds_left(table, now=1000), 25)   # an older host
        table.countdown_until = 50_000                     # set by room_session
        self.assertEqual(view.roulette_seconds_left(table, now=30_001), 20)
        self.assertEqual(view.roulette_seconds_left(table, now=49_999), 1)
        self.assertEqual(view.roulette_seconds_left(table, now=60_000), 0)
        with mock.patch('pygame.time.get_ticks', return_value=41_500):
            self.assertEqual(view.roulette_seconds_left(table), 9)

    def test_countdown_from_the_message_without_countdown_until(self):
        # The host's clock is far from ours: only countdown_at - host_now counts.
        view = make_view()
        table = Table(self.message(countdown_at=926_000, host_now=901_000, seconds_left=25), 'roulette')
        self.assertEqual(view.roulette_seconds_left(table, now=2000), 25)
        self.assertEqual(view.roulette_seconds_left(table, now=12_500), 15)   # no new message
        self.assertEqual(view.roulette_seconds_left(table, now=40_000), 0)
        # A new message (someone bet) restarts the count from its own times.
        table.message = self.message(revision=4, countdown_at=926_000, host_now=916_000, seconds_left=10)
        self.assertEqual(view.roulette_seconds_left(table, now=50_000), 10)
        self.assertEqual(view.roulette_seconds_left(table, now=55_000), 5)
        # Outside betting the host sends no countdown time.
        table.message = self.message(revision=5, phase='spinning', countdown_at=None, host_now=926_000,
                                     seconds_left=0)
        self.assertEqual(view.roulette_seconds_left(table, now=56_000), 0)
        view.draw_roulette(table)

    def shown(self, view, table, now):
        """The texts draw_roulette draws at get_ticks() == now."""
        with mock.patch('pygame.time.get_ticks', return_value=now), \
                mock.patch.object(view, 'text', wraps=view.text) as text:
            view.draw_roulette(table)
        return [call.args[0] for call in text.call_args_list]

    def test_draw_shows_the_local_countdown(self):
        # The host's seconds_left (25) is frozen between messages; the screen counts down.
        view = make_view()
        table = Table(self.message(seconds_left=25), 'roulette')
        table.countdown_until = 50_000
        self.assertIn('BETTING • 9s', self.shown(view, table, 41_500))
        self.assertIn('BETTING • 1s', self.shown(view, table, 49_999))
        self.assertIn('BETTING • 0s', self.shown(view, table, 50_000))
        table.countdown_until = None                       # an older host: its seconds_left
        self.assertIn('BETTING • 25s', self.shown(view, table, 41_500))

    def test_malformed_countdown_falls_back_to_seconds_left(self):
        # room_session sets countdown_until to None for a malformed countdown; the view
        # must then show seconds_left, not do the arithmetic itself.
        huge = 10 ** 400
        for bad in ('abc', float('nan'), float('inf'), [1], huge):
            with self.subTest(countdown_at=str(bad)[:12]):
                view = make_view()
                table = Table(self.message(countdown_at=bad, host_now=5, seconds_left=12), 'roulette')
                table.countdown_until = None
                self.assertEqual(view.roulette_seconds_left(table, now=1000), 12)
                self.assertIn('BETTING • 12s', self.shown(view, table, 1000))
                # A stand-in table without countdown_until checks the values the same way.
                del table.countdown_until
                self.assertEqual(view.roulette_seconds_left(table, now=1000), 12)
                view.draw_roulette(table)


class BluffRaiseButtonTests(unittest.TestCase):
    def bluff_message(self, **extra):
        message = {'type': 'party_state', 'mode': 'blind_mans_bluff', 'phase': 'betting', 'revision': 4,
                   'seats': seats(), 'your_seat': 0, 'current_actor': 0, 'spectating': False,
                   'cards': [None, None, None, None], 'stacks': [4860, 0, 4960, 4960],
                   'folded': [False, False, False, False], 'round_bets': [100, 150, 0, 0],
                   'actions': ['', '', '', ''], 'current_bet': 150, 'bet_unit': 100,
                   'minimum_raise_to': 250, 'hand_number': 1, 'ante': 40, 'pot': 410}
        message.update(extra)
        return message

    def test_raise_button_follows_the_host_rule(self):
        view = make_view()
        table = Table(self.bluff_message(can_raise=False), 'blind_mans_bluff')
        view.draw_bluff(table)
        actions = [name for _, name in view.buttons]
        self.assertIn('check_call', actions)
        self.assertNotIn('bet_raise', actions)
        table.message = self.bluff_message(can_raise=True)
        view.draw_bluff(table)
        self.assertIn('bet_raise', [name for _, name in view.buttons])
        # An older host sends no can_raise: the button follows the stack, as before.
        table.message = self.bluff_message()
        view.draw_bluff(table)
        self.assertIn('bet_raise', [name for _, name in view.buttons])


if __name__ == '__main__':
    unittest.main()
