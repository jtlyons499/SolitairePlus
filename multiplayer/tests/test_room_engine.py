"""Room Hold'em plays on the shared single-player engine (Phase 11 engine merge, B80).

The multiplayer copy of the engine (multiplayer/texas_holdem.py) is gone. These
tests pin the three network-table options, start-of-hand parity with a plain
solitaireplus TexasHoldemGame (all-in blinds, short heads-up big blind), the
seat-relative fold-win pot record, quick chat staying off at room tables, and
that a guest's ClientGame works out the same call and raise amounts as the host.
Every test seeds `random`; the host clock is a fake millisecond counter.
"""
import copy
import importlib.util
import json
import random
import unittest

import room_game
import room_protocol
from room_game import RoomGame, TwoHumanGame
from room_protocol import ClientGame, snapshot
from room_table import RoomAuthority
from multiplayer_paths import ROOT
from solitaireplus.games.poker import holdem

QUICK_CHAT_ATTRIBUTES = ('quick_chat_state', '_quick_chat_event_counter', '_quick_chat_event_signature')


def room_with_humans(seed, guests):
    """Host (identity 0, seat 0) plus guests 1..guests in seats 1..guests; NPCs fill the rest."""
    random.seed(seed)
    room = RoomAuthority('Host')
    for identity in range(1, guests + 1):
        room.join(identity, f'Guest {identity}')
    room.start()
    return room


def next_room_hand(room, stacks, previous_dealer):
    """Finish hand 1 by hand, set the stacks and dealer, and let every human start the next hand.

    Busted seats are human seats, so replace_busted_npcs() leaves them empty.
    """
    game = room.game
    game.player_stack = stacks[0]
    game.npc_stacks = list(stacks[1:])
    game.refresh_busted_state()
    game.hand_complete = True
    game.dealer_index = previous_dealer
    for identity in sorted(room.humans):
        room.act(identity, 'next_hand', 0, room.revision)
    return game


def plain_hand(npcs, stacks, previous_dealer):
    """The same table on a plain single-player TexasHoldemGame."""
    game = holdem.TexasHoldemGame()
    game.start_session(copy.deepcopy(npcs), 5000, 25)
    game.player_stack = stacks[0]
    game.npc_stacks = list(stacks[1:])
    game.refresh_busted_state()
    game.dealer_index = previous_dealer
    game.start_hand()
    return game


def opening_state(game):
    return {
        'dealer': game.dealer_index,
        'small_blind': game.small_blind_index,
        'big_blind': game.big_blind_index,
        'first_actor': game.current_actor,
        'current_bet': game.current_bet,
        'last_raise_size': game.last_raise_size,
        'round_bets': [game.player_round_bet, *game.npc_round_bets],
        'stacks': [game.player_stack, *game.npc_stacks],
        'all_in': [game.player_all_in, *game.npc_all_in],
        'busted': [game.player_busted, *game.npc_busted],
        'in_hand': game.get_active_player_indexes(),
        'minimum_raise_to': game.get_minimum_raise_to(),
        'hand_complete': game.hand_complete,
    }


def human_on_turn(room):
    game = room.game
    seat = game.current_actor
    identity = next((i for i, s in room.humans.items() if s == seat), None)
    if identity in room.connections and not game.hand_complete and game.actor_needs_action(seat):
        return identity
    return None


def drive(test, room, choose, after=None, steps=3000):
    """Run one hand to the end on the host clock; connected humans act through `choose`."""
    now = 0
    for _ in range(steps):
        if room.game.hand_complete:
            return
        identity = human_on_turn(room)
        if identity is not None:
            action, amount = choose(room, identity)
            if not room.act(identity, action, amount, room.revision):
                test.assertTrue(room.act(identity, 'check_call', 0, room.revision),
                                f'check/call rejected for identity {identity}')
        else:
            now += 10000
            room.update(now)
        if after:
            after(room)
    test.fail(f'hand stalled at actor {room.game.current_actor}, stage {room.game.current_stage}')


def check_call(room, identity):
    return 'check_call', 0


class RoomEngineTests(unittest.TestCase):
    def test_room_game_flags(self):
        self.assertIs(room_game.TexasHoldemGame, holdem.TexasHoldemGame)
        self.assertIs(room_protocol.TexasHoldemGame, holdem.TexasHoldemGame)
        self.assertEqual(room_game.TexasHoldemGame.__module__, 'solitaireplus.games.poker.holdem')
        self.assertFalse((ROOT / 'multiplayer' / 'texas_holdem.py').exists())
        self.assertIsNone(importlib.util.find_spec('texas_holdem'))
        # Single-player defaults are untouched.
        base = holdem.TexasHoldemGame
        self.assertEqual((base.allow_network_spectator, base.finish_hand_after_player_fold, base.quick_chat_enabled),
                         (False, True, True))
        for cls in (TwoHumanGame, RoomGame):
            self.assertTrue(cls.allow_network_spectator, cls.__name__)
            self.assertFalse(cls.finish_hand_after_player_fold, cls.__name__)
            self.assertFalse(cls.quick_chat_enabled, cls.__name__)
        # TwoHumanGame is only the three settings now: no overrides of its own.
        self.assertFalse({'__init__', 'resolve_after_fold'} & set(vars(TwoHumanGame)))
        self.assertFalse(ClientGame.quick_chat_enabled)
        game = RoomGame()
        self.assertTrue(game.allow_network_spectator)
        self.assertEqual(game.sitting_out, set())

    def test_preflop_first_actor_with_all_in_blinds_matches_shared_engine(self):
        cases = (
            # 3-handed: host deals, both blinds are short NPCs; busted guests in seats 1-3.
            ('3-handed', 3, [5000, 0, 0, 0, 10, 30], 5, [4, 5]),
            # 4-handed: host deals, short blinds in seats 3 and 4, a funded NPC is first to act.
            ('4-handed', 2, [5000, 0, 0, 10, 30, 5000], 5, [3, 4]),
        )
        for name, guests, stacks, previous_dealer, blinds in cases:
            with self.subTest(name):
                room = room_with_humans(1, guests)
                game = next_room_hand(room, stacks, previous_dealer)
                self.assertEqual(game.hand_number, 2)
                plain = plain_hand(game.npcs, stacks, previous_dealer)
                room_state, plain_state = opening_state(game), opening_state(plain)
                self.assertEqual(room_state, plain_state)
                self.assertEqual([game.small_blind_index, game.big_blind_index], blinds)
                self.assertTrue(all(room_state['all_in'][seat] for seat in blinds), room_state)
                # The all-in blinds are still in the hand (not flagged busted).
                for seat in blinds:
                    self.assertIn(seat, room_state['in_hand'])
                    self.assertFalse(game.npc_busted[seat - 1])
                total = game.player_stack + sum(game.npc_stacks) + game.pot
                drive(self, room, check_call)
                self.assertEqual(game.player_stack + sum(game.npc_stacks), total)
                main_pot = game.last_pot_awards[0]
                for seat in blinds:
                    self.assertIn(seat, main_pot['eligible'], game.last_pot_awards)

    def test_heads_up_short_big_blind_matches_shared_engine(self):
        cases = (
            # The host deals and posts the small blind; the NPC big blind is short.
            ('NPC short big blind', [5000, 0, 0, 0, 0, 30], 5, 0, 5),
            # The NPC deals; the host is the short big blind.
            ('host short big blind', [30, 0, 0, 0, 0, 5000], 0, 5, 0),
        )
        for name, stacks, previous_dealer, dealer, big_blind in cases:
            with self.subTest(name):
                room = room_with_humans(2, 4)
                game = next_room_hand(room, stacks, previous_dealer)
                plain = plain_hand(game.npcs, stacks, previous_dealer)
                self.assertEqual(opening_state(game), opening_state(plain))
                self.assertEqual((game.dealer_index, game.small_blind_index, game.big_blind_index),
                                 (dealer, dealer, big_blind))
                self.assertEqual(game.current_actor, dealer, 'heads-up: the dealer acts first preflop')
                self.assertEqual(sorted(game.get_active_player_indexes()), sorted((0, 5)))
                host = ClientGame()
                host.apply(room.view(0))
                self.assertEqual(host.get_player_amount_to_call(), plain.get_player_amount_to_call())
                self.assertEqual(host.get_minimum_raise_to(), plain.get_minimum_raise_to())
                total = game.player_stack + sum(game.npc_stacks) + game.pot
                drive(self, room, check_call)
                self.assertEqual(game.player_stack + sum(game.npc_stacks), total)
                self.assertIn(big_blind, game.last_pot_awards[0]['eligible'], game.last_pot_awards)

    def test_fold_win_pot_has_eligible_and_guest_view_remaps_it(self):
        # Guests 2-5 leave mid-hand: the host clock folds their seats in turn. The host folds
        # too, so guest 1 (seat 1) wins the pot uncontested; its raise nobody called comes back
        # as a refund (the shared engine settles a fold win like a one-seat showdown).
        room = room_with_humans(4, 5)
        game = room.game
        for identity in range(2, 6):
            room.leave(identity)
        start_stacks = [game.player_stack + game.player_hand_contribution,
                        *(s + c for s, c in zip(game.npc_stacks, game.npc_hand_contributions))]

        def host_folds_guest_raises(room, identity):
            if identity == 0:
                return 'fold', 0
            return 'bet_raise', game.get_minimum_raise_to() if game.current_bet else game.get_minimum_open_bet()

        drive(self, room, host_folds_guest_raises)
        self.assertEqual(game.winner_indexes, [1])
        self.assertEqual(len(game.last_pot_awards), 1)
        pot = game.last_pot_awards[0]
        self.assertEqual((pot['eligible'], pot['winners'], pot['hand']), ([1], [1], ''))
        self.assertGreater(game.last_refunds.get(1, 0), 0, game.last_refunds)
        won = pot['payouts'][1] + game.last_refunds.get(1, 0)
        self.assertEqual(game.npc_stacks[0], start_stacks[1] - game.npc_hand_contributions[0] + won)

        guest_message = room.view(1)
        guest_pot = guest_message['data']['last_pot_awards'][0]
        self.assertEqual((guest_pot['eligible'], guest_pot['winners']), ([0], [0]))
        self.assertEqual(guest_pot['payouts'], {'0': pot['payouts'][1]})
        # Seen from seat 1, seats 0 and 1 swap places; the others keep their numbers.
        guest_seat = {1: 0, 0: 1, 2: 2, 3: 3, 4: 4, 5: 5}
        self.assertEqual(guest_message['data']['last_refunds'],
                         {str(guest_seat[seat]): amount for seat, amount in game.last_refunds.items()})
        host_pot = room.view(0)['data']['last_pot_awards'][0]
        self.assertEqual((host_pot['eligible'], host_pot['winners'], host_pot['payouts']),
                         ([1], [1], {'1': pot['payouts'][1]}))
        # The authority's own record is not changed by the seat-relative copies.
        self.assertEqual(game.last_pot_awards[0]['eligible'], [1])
        self.assertEqual(game.last_pot_awards[0]['payouts'], {1: pot['payouts'][1]})

        # Over the wire (JSON) and back, the guest's ClientGame has numeric seat keys again.
        for message in (guest_message, json.loads(json.dumps(guest_message))):
            guest = ClientGame()
            guest.apply(message)
            client_pot = guest.last_pot_awards[0]
            self.assertEqual((client_pot['eligible'], client_pot['winners']), ([0], [0]))
            self.assertEqual(client_pot['payouts'], {0: pot['payouts'][1]})
            self.assertEqual(guest.last_refunds, {guest_seat[seat]: amount for seat, amount in game.last_refunds.items()})
            self.assertEqual(guest.player_stack, game.npc_stacks[0])
            self.assertEqual(guest.get_table_player_name(0), 'Guest 1')
        self.assertEqual(guest_message['data']['last_pot_awards'][0]['payouts'], {'0': pot['payouts'][1]},
                         'applying a view must not change the message')

    def test_room_npcs_create_no_quick_chat_state(self):
        room = room_with_humans(6, 1)
        game = room.game
        decisions = []
        run_next_npc_action = game.run_next_npc_action

        def counted():
            decisions.append(game.current_actor)
            return run_next_npc_action()

        game.run_next_npc_action = counted
        drive(self, room, check_call)
        self.assertTrue(game.hand_complete)
        self.assertTrue(decisions, 'no NPC acted')
        for name in QUICK_CHAT_ATTRIBUTES:
            self.assertNotIn(name, vars(game))
        context = game.build_npc_ai_context(1)
        self.assertFalse([key for key in context if 'quick_chat' in key], context)
        guest = ClientGame()
        guest.apply(room.view(1))
        for name in QUICK_CHAT_ATTRIBUTES:
            self.assertNotIn(name, vars(guest))

    def test_client_matches_authority_amounts(self):
        checks = []

        def compare(room):
            game = room.game
            if checks and checks[-1] == (id(room), room.revision):
                return
            checks.append((id(room), room.revision))
            for identity, seat in room.humans.items():
                client = ClientGame()
                client.apply(snapshot(game, seat, room.revision, room.names))
                if seat == 0:
                    to_call = game.get_player_amount_to_call()
                else:
                    to_call = game.get_npc_amount_to_call(seat - 1)
                where = f'seat {seat}, hand {game.hand_number}, {game.current_stage}, revision {room.revision}'
                self.assertEqual(client.get_player_amount_to_call(), to_call, where)
                self.assertEqual(client.get_minimum_raise_to(), game.get_minimum_raise_to(), where)
                self.assertEqual(client.current_bet, game.current_bet, where)

        for seed in range(10):
            room = room_with_humans(100 + seed, 2)

            def choose(room, identity, seed=seed):
                game = room.game
                seat = room.humans[identity]
                if (seed + game.hand_number + len(game.community_cards)) % 3 == 0:
                    if game.current_bet == 0:
                        return 'bet_raise', game.get_minimum_open_bet()
                    return 'bet_raise', game.get_minimum_raise_to()
                if seed % 4 == 3 and seat == 2:
                    return 'fold', 0
                return 'check_call', 0

            compare(room)
            drive(self, room, choose, after=compare)
            compare(room)
        self.assertGreater(len(checks), 100)


if __name__ == '__main__':
    unittest.main()
