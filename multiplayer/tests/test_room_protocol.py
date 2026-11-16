"""Room protocol coverage: RoomAuthority + snapshot() + ClientGame.

Ported from the deleted LAN tests (test_lan.py) so the parts the room code
still uses (room_protocol.py, room_game.py) keep their coverage after the LAN
and Practice tables were removed.
Every test seeds `random` and drives the host with one fake millisecond clock.
"""
import copy
import json
import random
import unittest

from room_table import RoomAuthority
from room_protocol import ClientGame, snapshot
from mp_widgets import hand_type

TOTAL_CHIPS = 6 * 5000


def make_room(seed=42):
    """Host (identity 0, seat 0) and one guest (identity 1, seat 1) plus four NPCs."""
    random.seed(seed)
    room = RoomAuthority('Host')
    room.join(1, 'Guest')
    room.start()
    return room


def human_on_turn(room):
    """The connected identity whose seat must act now, or None."""
    game = room.game
    seat = game.current_actor
    identity = next((i for i, s in room.humans.items() if s == seat), None)
    if identity in room.connections and not game.hand_complete and game.actor_needs_action(seat):
        return identity
    return None


def client_view(room, identity):
    client = ClientGame()
    client.apply(room.view(identity))
    return client


class RoomProtocolTests(unittest.TestCase):
    def drive(self, room, now=0, choose=None, check=None, steps=2000):
        """Run the host clock until the hand ends; humans act through `choose`."""
        game = room.game
        for _ in range(steps):
            if check:
                check(room)
            if game.hand_complete:
                return now
            identity = human_on_turn(room)
            if identity is not None:
                action, amount = choose(room, identity) if choose else ('check_call', 0)
                self.assertTrue(room.act(identity, action, amount, room.revision),
                                f'{action} rejected for identity {identity}')
            now += 10000
            room.update(now)
        self.fail(f'Hand stalled at actor {game.current_actor}, stage {game.current_stage}')

    def test_host_fold_keeps_guest_round_alive(self):
        room = make_room(7)
        game = room.game
        game.current_actor = 0
        self.assertTrue(game.actor_needs_action(0))
        self.assertTrue(room.act(0, 'fold', 0, room.revision))
        self.assertTrue(game.player_folded)
        self.assertFalse(game.hand_complete)
        self.assertEqual(game.current_stage, 'preflop')
        self.assertEqual(game.community_cards, [])
        self.assertFalse(game.npc_folded[0])
        # The host clock keeps the hand going and the guest still gets a turn.
        now = 0
        for _ in range(200):
            if human_on_turn(room) == 1:
                break
            self.assertFalse(game.hand_complete, 'hand ended before the guest could act')
            now += 10000
            room.update(now)
        self.assertEqual(human_on_turn(room), 1)
        self.assertTrue(room.act(1, 'check_call', 0, room.revision))
        self.assertTrue(game.player_folded)

    def test_busted_host_spectates_with_no_hole_cards(self):
        room = make_room(11)
        game = room.game
        game.player_stack = 0
        game.npc_stacks = [10000, 5000, 5000, 5000, 5000]
        game.refresh_busted_state()
        game.hand_complete = True
        self.assertTrue(room.act(0, 'next_hand', 0, room.revision))
        self.assertTrue(room.act(1, 'next_hand', 0, room.revision))
        self.assertEqual(game.hand_number, 2)
        self.assertFalse(game.hand_complete)
        self.assertTrue(game.player_busted)
        self.assertEqual(game.player_hand, [])
        self.assertEqual(len(game.npc_hands[0]), 2)
        self.assertNotIn(0, game.hand_seat_indexes)
        message = room.view(0)
        self.assertEqual(message['data']['player_hand'], [])
        host = ClientGame()
        host.apply(message)
        self.assertEqual(hand_type(host), 'Out of chips')
        # The guest still plays the hand with real cards.
        guest = client_view(room, 1)
        self.assertEqual(guest.player_hand, game.npc_hands[0])

    def test_runout_reveal_privacy(self):
        hands_seen = []

        def check(room):
            game = room.game
            seats = [game.player_hand, *game.npc_hands]
            folded = [game.player_folded, *game.npc_folded]
            reveal = game.current_stage == 'showdown' or game.should_reveal_runout_hands()
            for identity, seat in room.humans.items():
                data = room.view(identity)['data']
                self.assertEqual(data['player_hand'], seats[seat])
                self.assertNotIn('deck', data)
                others = [i for i in range(6) if i != seat]
                for position, other in enumerate(others):
                    cards = data['npc_hands'][position]
                    if cards:
                        self.assertTrue(reveal, f'seat {other} shown to seat {seat} at {game.current_stage}')
                        self.assertFalse(folded[other])
                        self.assertEqual(cards, seats[other])
                        hands_seen.append(other)

        for seed in range(12):
            room = make_room(seed)

            def all_in_sometimes(room, identity, seed=seed):
                game = room.game
                seat = room.humans[identity]
                if seed % 2 and seat == 0 and game.can_player_raise():
                    return 'bet_raise', game.player_stack + game.player_round_bet
                return 'check_call', 0

            self.drive(room, choose=all_in_sometimes, check=check)
        self.assertTrue(hands_seen, 'no showdown or run-out was exercised')

        # A built run-out: host and guest all in on the flop, everyone else folded.
        room = make_room(3)
        game = room.game
        game.current_actor = 1
        game.current_bet = 0
        game.player_round_bet = 0
        game.npc_round_bets = [0] * 5
        self.assertTrue(room.act(1, 'bet_raise', 200, room.revision))
        self.assertEqual(game.current_bet, 200)
        self.assertFalse(game.should_reveal_runout_hands())
        self.assertEqual(room.view(0)['data']['npc_hands'], [[]] * 5)
        game.player_stack = 0
        game.player_all_in = True
        game.npc_stacks = [0, 5000, 5000, 5000, 5000]
        game.npc_all_in = [True, False, False, False, False]
        game.npc_folded = [False, True, True, True, True]
        game.current_stage = 'flop'
        self.assertTrue(game.should_reveal_runout_hands())
        self.assertEqual(room.view(0)['data']['npc_hands'], [game.npc_hands[0], [], [], [], []])
        self.assertEqual(room.view(1)['data']['npc_hands'], [game.player_hand, [], [], [], []])

    def test_guest_side_pot_eligible_reindexed_and_new_hand_recap_reset(self):
        room = make_room(5)
        game = room.game
        game.last_pot_awards = [
            {'amount': 300, 'eligible': [0, 1, 2], 'winners': [1], 'share': 300, 'remainder': 0, 'hand': 'Pair'},
            {'amount': 120, 'eligible': [1, 3], 'winners': [1, 3], 'share': 60, 'remainder': 0, 'hand': 'Flush'},
        ]
        guest_pots = room.view(1)['data']['last_pot_awards']
        self.assertEqual(guest_pots[0]['winners'], [0])
        self.assertEqual(guest_pots[0]['eligible'], [1, 0, 2])
        self.assertEqual(guest_pots[1]['winners'], [0, 3])
        self.assertEqual(guest_pots[1]['eligible'], [0, 3])
        host_pots = room.view(0)['data']['last_pot_awards']
        self.assertEqual(host_pots, game.last_pot_awards)
        # Seat-relative copies never change the authority's own pot list.
        self.assertEqual(game.last_pot_awards[0]['winners'], [1])

        message = room.view(1)
        client = ClientGame()
        client.apply(message)
        client.recap_open = True
        client.recap_page = 2
        client.apply(message)
        self.assertTrue(client.recap_open, 'same hand must keep the recap open')
        self.assertEqual(client.recap_page, 2)
        message['data']['hand_number'] += 1
        client.apply(message)
        self.assertFalse(client.recap_open)
        self.assertEqual(client.recap_page, 0)

    def test_rejected_action_does_not_mutate_view(self):
        room = make_room(9)
        now = 0
        for _ in range(200):
            if human_on_turn(room) is not None:
                break
            now += 10000
            room.update(now)
        actor = human_on_turn(room)
        self.assertIsNotNone(actor)
        other = 1 - actor
        before = {identity: copy.deepcopy(room.view(identity)) for identity in (0, 1)}
        revision = room.revision
        self.assertFalse(room.act(actor, 'check_call', 0, revision - 1))
        self.assertFalse(room.act(actor, 'check_call', 0, None))
        self.assertFalse(room.act(actor, 'cheat', 0, revision))
        self.assertFalse(room.act(actor, 'bet_raise', -100, revision))
        self.assertFalse(room.act(actor, 'bet_raise', True, revision))
        self.assertFalse(room.act(actor, 'bet_raise', 1000001, revision))
        self.assertFalse(room.act(actor, 'bet_raise', '200', revision))
        self.assertFalse(room.act(other, 'check_call', 0, revision))
        self.assertFalse(room.act(other, 'next_hand', 0, revision))
        self.assertFalse(room.act(99, 'fold', 0, revision))
        self.assertFalse(room.act(1, 'start', 0, revision))
        self.assertEqual(room.revision, revision)
        for identity in (0, 1):
            self.assertEqual(room.view(identity), before[identity])

    def test_snapshot_json_round_trip(self):
        checked = set()

        def check(room):
            game = room.game
            for viewer in (0, 1):
                message = snapshot(game, viewer, room.revision, room.names)
                wire = json.loads(json.dumps(message))
                self.assertEqual(wire, message)
                full = room.view(viewer)
                self.assertEqual(json.loads(json.dumps(full)), full)
                direct, decoded = ClientGame(), ClientGame()
                direct.apply(full)
                decoded.apply(json.loads(json.dumps(full)))
                for key in full['data']:
                    self.assertEqual(getattr(decoded, key), getattr(direct, key), key)
                self.assertEqual(decoded.names, full['names'])
                self.assertEqual(decoded.revision, room.revision)
                self.assertEqual(decoded.get_hand_history_lines(), direct.get_hand_history_lines())
                checked.add(game.current_stage)

        for seed in (1, 2):
            room = make_room(seed)
            self.drive(room, check=check)
            check(room)
        self.assertIn('preflop', checked)
        self.assertTrue(checked & {'showdown', 'flop', 'turn', 'river'})

    def test_malformed_refunds_and_payouts_are_dropped_not_raised(self):
        """The seat-keyed fields the shared engine added (last_refunds, a pot's payouts) are
        parsed by ClientGame.apply; bad host data must not crash the guest's frame loop."""
        room = make_room(4)
        for refunds, expected in (('x', {}), (['1'], {}), (None, {}),
                                  ({'a': 5, '2': 'b', '3': 5, '4': True, '1': 7}, {3: 5, 1: 7})):
            with self.subTest(refunds=refunds):
                message = copy.deepcopy(room.view(1))
                message['data']['last_refunds'] = refunds
                message['data']['last_pot_awards'] = [
                    {'amount': 10, 'winners': [0], 'payouts': refunds}, 'not a pot', {'amount': 5}]
                client = ClientGame()
                client.apply(message)
                self.assertEqual(client.last_refunds, expected)
                self.assertEqual(client.last_pot_awards[0]['payouts'], expected)
                self.assertEqual(client.last_pot_awards[1:], ['not a pot', {'amount': 5}])
        message = copy.deepcopy(room.view(1))
        message['data']['last_pot_awards'] = None
        client = ClientGame()
        client.apply(message)
        self.assertIsNone(client.last_pot_awards)

    def test_two_humans_complete_and_conserve_chips(self):
        for seed in range(30):
            room = make_room(seed)
            game = room.game

            def choose(room, identity, seed=seed):
                return ('fold', 0) if seed % 5 == 0 and room.humans[identity] == 0 else ('check_call', 0)

            self.drive(room, choose=choose)
            self.assertTrue(game.hand_complete, f'seed {seed}')
            self.assertEqual(game.player_stack + sum(game.npc_stacks), TOTAL_CHIPS, f'seed {seed}')
            revision = room.revision
            self.assertTrue(room.act(0, 'next_hand', 0, revision))
            self.assertEqual(game.hand_number, 1, 'one ready human must not start the next hand')
            self.assertTrue(room.act(1, 'next_hand', 0, room.revision))
            if sum(stack > 0 for stack in [game.player_stack, *game.npc_stacks]) > 1:
                self.assertEqual(game.hand_number, 2, f'seed {seed}')
                self.assertEqual(game.player_stack + sum(game.npc_stacks) + game.pot,
                                 TOTAL_CHIPS + room.chips_added, f'seed {seed}')


if __name__ == '__main__':
    unittest.main()
