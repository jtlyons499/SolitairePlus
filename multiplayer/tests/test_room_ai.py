"""Room NPCs and recaps use the shared single-player AI and recap (Phase 11 ai-recap).

The multiplayer copies multiplayer/poker_ai.py and multiplayer/poker_recap.py are gone.
These tests pin that room NPCs decide through solitaireplus.games.poker.ai with no
quick-chat inputs, that the shared recap names the eligible player of a fold win seen
through a guest's or the host's ClientGame, and that the multiplayer Payout History
(mp_showdown) pays out exactly the chips the engine moved in a split side pot with an
odd chip and in a three-way split main pot.

Hands that need set cards seat six humans (no NPC decisions), set the hole cards and the
deck after the deal, and drive every action through RoomAuthority.act; the host clock is
a fake millisecond counter. Every test seeds `random`.
"""
import importlib.util
import json
import random
import re
import unittest
from types import SimpleNamespace
from unittest import mock

import pygame

from mp_showdown import compact_result, payout_lines
from multiplayer_paths import ROOT
from room_game import RoomGame
from room_protocol import ClientGame, snapshot
from room_session import RoomTable
from room_table import RoomAuthority
from solitaireplus.games.poker import ai, holdem, recap

QUICK_CHAT_KEYS = {'quick_chat_aggression', 'quick_chat_call_requirement_delta', 'quick_chat_bluff_delta'}
SUITS = {'c': 'Clubs', 'd': 'Diamonds', 'h': 'Hearts', 's': 'Spades'}
BOARD = ['2c', '7d', '9h', 'Js', 'Kc']
RECEIVES = re.compile(r'^(?P<name>.+) receives \$(?P<amount>[\d,]+)$')


def card(text):
    return {'rank': text[:-1], 'suit': SUITS[text[-1]]}


def six_human_room(seed, stacks):
    """Host plus guests 1-5 (identity == seat). Hand 2 starts with these stacks, dealer seat 0.

    Hand 1 is closed by hand (its cards are random); every human then asks for the next
    hand, so the dealer moves from seat 5 to seat 0: small blind seat 1, big blind seat 2,
    and seat 3 acts first preflop.
    """
    random.seed(seed)
    room = RoomAuthority('Host')
    for identity in range(1, 6):
        room.join(identity, f'Guest {identity}')
    room.start()
    game = room.game
    game.player_stack = stacks[0]
    game.npc_stacks = list(stacks[1:])
    game.refresh_busted_state()
    game.hand_complete = True
    game.dealer_index = 5
    for identity in sorted(room.humans):
        room.act(identity, 'next_hand', 0, room.revision)
    return room


def set_cards(game, hands, board=BOARD):
    """Give every seat its hole cards and stack the deck so the board comes out as `board`."""
    game.player_hand = [card(text) for text in hands[0]]
    game.npc_hands = [[card(text) for text in hands[seat]] for seat in range(1, 6)]
    burns = ['8c', '8d', '8h']   # each street burns one card first; the deck pops from its end
    game.deck = [card(text) for text in (board[4], burns[0], board[3], burns[1],
                                         board[2], board[1], board[0], burns[2])]


def play_script(test, room, script, steps=500):
    """Play one hand to the end: each human acts from script[(stage, seat)] in order; the
    host clock deals the streets and settles the hand."""
    game = room.game
    now = 0
    for _ in range(steps):
        if game.hand_complete:
            test.assertFalse(any(script.values()), f'unused actions: {script}')
            return
        seat = game.current_actor
        if not game.is_betting_round_complete() and game.actor_needs_action(seat):
            action, amount = script[(game.current_stage, seat)].pop(0)
            test.assertTrue(room.act(seat, action, amount, room.revision),
                            f'{game.current_stage}: seat {seat} {action} {amount} rejected')
        else:
            now += 10000
            room.update(now)
    test.fail(f'hand stalled at actor {game.current_actor}, stage {game.current_stage}')


def stacks_before_hand(game):
    return [game.player_stack + game.player_hand_contribution,
            *(stack + paid for stack, paid in zip(game.npc_stacks, game.npc_hand_contributions))]


def chips_back(game, before):
    """What each physical seat got back when the hand settled (pot payouts plus refunds)."""
    after = [game.player_stack, *game.npc_stacks]
    return [end - (start - paid) for end, start, paid in zip(after, before, game.get_hand_contributions())]


def printed_payouts(lines):
    totals = {}
    for line in lines:
        match = RECEIVES.match(line)
        if match:
            name = match['name']
            totals[name] = totals.get(name, 0) + int(match['amount'].replace(',', ''))
    return totals


def client_views(room, seats=range(6)):
    """Each seat's ClientGame, built from its room view after a JSON round trip (the wire)."""
    views = {}
    for seat in seats:
        client = ClientGame()
        client.apply(json.loads(json.dumps(room.view(seat))))
        views[seat] = client
    return views


class RoomAiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def test_copies_are_gone(self):
        for stem in ('poker_ai', 'poker_recap'):
            self.assertFalse((ROOT / 'multiplayer' / f'{stem}.py').exists(), stem)
            self.assertIsNone(importlib.util.find_spec(stem), stem)
        self.assertIs(holdem.decide_poker_action, ai.decide_poker_action)

    def test_room_npc_context_has_no_quick_chat_keys(self):
        random.seed(21)
        room = RoomAuthority('Host')
        room.start()
        game = room.game
        self.assertIsInstance(game, RoomGame)
        plain = holdem.TexasHoldemGame()
        plain.start_session([dict(npc) for npc in game.npcs], 5000, 25)
        plain.start_hand()
        for npc_index in range(5):
            context = game.build_npc_ai_context(npc_index)
            self.assertFalse([key for key in context if 'quick_chat' in key], context)
            # The single-player table does add them, so this check can fail.
            single_player = plain.build_npc_ai_context(npc_index)
            self.assertEqual(QUICK_CHAT_KEYS & set(single_player), QUICK_CHAT_KEYS)
            # Otherwise the room builds the same single-player context.
            self.assertEqual(set(context), set(single_player) - QUICK_CHAT_KEYS)

        # Every room NPC decision goes through the shared AI with that context.
        contexts = []

        def recorded(personality, context, rng=None):
            contexts.append(dict(context))
            return ai.decide_poker_action(personality, context, rng)

        with mock.patch.object(holdem, 'decide_poker_action', side_effect=recorded):
            now = 0
            for _ in range(3000):
                if game.hand_complete:
                    break
                if game.current_actor == 0 and game.actor_needs_action(0) and not game.is_betting_round_complete():
                    room.act(0, 'check_call', 0, room.revision)
                else:
                    now += 10000
                    room.update(now)
        self.assertTrue(game.hand_complete)
        self.assertTrue(contexts, 'no NPC decided')
        for context in contexts:
            self.assertFalse(QUICK_CHAT_KEYS & set(context), context)
            self.assertIn('personality_traits', context)

    def test_fold_win_recap_names_eligible_player(self):
        room = six_human_room(5, [5000] * 6)
        game = room.game
        self.assertEqual((game.small_blind, game.big_blind), (25, 50))
        before = stacks_before_hand(game)
        # Seat 3 raises to 150 and everyone folds: it wins the 125 it matched (both blinds
        # and its first 50) and gets its uncalled 100 back.
        script = {('preflop', 3): [('bet_raise', 150)],
                  **{('preflop', seat): [('fold', 0)] for seat in (4, 5, 0, 1, 2)}}
        play_script(self, room, script)
        self.assertEqual(game.winner_indexes, [3])
        self.assertEqual(game.last_pot_awards[0]['eligible'], [3])
        self.assertEqual(game.last_refunds, {3: 100})
        back = chips_back(game, before)
        self.assertEqual(back, [0, 0, 0, 225, 0, 0])

        views = client_views(room)
        for seat, client in views.items():
            lines = recap.recap_lines(client)
            where = f'seat {seat}: {lines}'
            you = seat == 3
            self.assertEqual(lines[0], 'Main pot: $125 — Everyone else folded', where)
            self.assertTrue(lines[1].startswith('    Guest 3 receive') and lines[1].endswith(' $125'), where)
            self.assertEqual(lines[2], '    Eligible: Guest 3', where)
            # B86 F7: refunds have their own heading.
            self.assertEqual(lines[3:5], ['Returned (uncalled):',
                                          '    Uncalled $100 returned to ' + ('you' if you else 'Guest 3')], where)
            net = back[seat] - game.get_hand_contributions()[seat]
            sign = '+' if net >= 0 else '−'
            self.assertEqual(lines[5:], [f'You received: ${back[seat]:,}',
                                         f'Your hand contribution: ${game.get_hand_contributions()[seat]:,}',
                                         f'Your net for this hand: {sign}${abs(net):,}'], where)
            self.assertEqual(recap.player_hand_net(client), [game.player_stack, *game.npc_stacks][seat] - before[seat])
            # B86 F7 follow-up 2: the display rows keep each line's indent.
            rows = recap.recap_display_lines(client)
            self.assertIn('    Eligible: Guest 3', rows, where)
            self.assertIn('Returned (uncalled):', rows, where)

        # The guest's own seat is seat 0 in its view; the host sees the winner at seat 3.
        self.assertEqual(views[3].last_pot_awards[0]['eligible'], [0])
        self.assertEqual(views[0].last_pot_awards[0]['eligible'], [3])
        # Payout History names the winner of the fold win too.
        self.assertEqual(payout_lines(views[0])[:3],
                         ['Main pot: $125', 'Won uncontested: everyone else folded.', 'Guest 3 receives $125'])
        self.assertEqual(compact_result(views[0]), ['Guest 3 wins', 'Uncontested'])

    def test_fold_win_payout_history_lists_returned_chips(self):
        """B86 settles a fold win like a one-seat showdown: the pot is the matched 125 and the
        uncalled 100 is a refund. The Payout History must still account for all 225 chips the
        table showed in the pot, for the host and for a guest, through RoomTable.apply."""
        room = six_human_room(5, [5000] * 6)
        game = room.game
        before = stacks_before_hand(game)
        script = {('preflop', 3): [('bet_raise', 150)],
                  **{('preflop', seat): [('fold', 0)] for seat in (4, 5, 0, 1, 2)}}
        play_script(self, room, script)
        self.assertEqual(game.last_refunds, {3: 100})
        self.assertEqual(chips_back(game, before)[3], 225)
        for seat in (0, 3):
            with self.subTest(viewer=seat):
                table = RoomTable.__new__(RoomTable)
                table.game = ClientGame()
                table.profile = None
                table.last_payout = None
                table.mode = None
                table.apply(json.loads(json.dumps(room.view(seat))))
                self.assertEqual(table.last_payout.last_refunds, {room.view(seat)['names'].index('Guest 3'): 100})
                for shown in (table.game, table.last_payout, table.payout_history[-1]):
                    lines = payout_lines(shown)
                    self.assertEqual(lines[:3], ['Main pot: $125', 'Won uncontested: everyone else folded.',
                                                 'Guest 3 receives $125'], lines)
                    self.assertEqual(lines[4:6], ['Returned (uncalled):', 'Uncalled $100 returned to Guest 3'], lines)
                    paid = sum(printed_payouts(lines).values())
                    returned = sum(int(line.split('$')[1].split()[0].replace(',', ''))
                                   for line in lines if line.startswith('Uncalled $'))
                    self.assertEqual(paid + returned, 225, lines)
        # A Payout History entry kept from before this change (no last_refunds) still renders.
        old = SimpleNamespace(names=table.game.names, last_pot_awards=table.game.last_pot_awards,
                              result_text='', hand_number=game.hand_number, showdown_hands={})
        self.assertNotIn('Returned (uncalled):', payout_lines(old))

    def test_showdown_payout_lines_match_chip_changes(self):
        cases = (
            # Seat 3 (short, all in for 117) wins the main pot with aces. Seats 0 and 1 tie with
            # kings for the side pot, which holds seat 2's folded 333: 1,199 split 600/599, the
            # odd chip to seat 1, first left of the dealer (seat 0).
            ('split side pot with an odd chip', 'As Ad',
             {('preflop', 3): [('bet_raise', 117)], ('preflop', 4): [('fold', 0)], ('preflop', 5): [('fold', 0)],
              ('preflop', 0): [('check_call', 0)], ('preflop', 1): [('check_call', 0)],
              ('preflop', 2): [('check_call', 0)],
              ('flop', 1): [('bet_raise', 333)], ('flop', 2): [('check_call', 0)], ('flop', 0): [('check_call', 0)],
              ('turn', 1): [('bet_raise', 100)], ('turn', 2): [('fold', 0)], ('turn', 0): [('check_call', 0)],
              ('river', 1): [('check_call', 0)], ('river', 0): [('check_call', 0)]},
             [{'amount': 468, 'eligible': [0, 1, 3], 'payouts': {3: 468}},
              {'amount': 1199, 'eligible': [0, 1], 'payouts': {1: 600, 0: 599}}],
             ['Guest 3 wins', 'Pair of Aces • 1 side pot(s)']),
            # Seat 3 ties the kings: the 401 main pot (the big blind folded its 50) splits three
            # ways, 134/134/133 with the odd chips to seats 1 and 3; the 666 side pot splits evenly.
            ('three-way split main pot', 'Ks 3h',
             {('preflop', 3): [('bet_raise', 117)], ('preflop', 4): [('fold', 0)], ('preflop', 5): [('fold', 0)],
              ('preflop', 0): [('check_call', 0)], ('preflop', 1): [('check_call', 0)],
              ('preflop', 2): [('fold', 0)],
              ('flop', 1): [('bet_raise', 333)], ('flop', 0): [('check_call', 0)],
              ('turn', 1): [('check_call', 0)], ('turn', 0): [('check_call', 0)],
              ('river', 1): [('check_call', 0)], ('river', 0): [('check_call', 0)]},
             [{'amount': 401, 'eligible': [0, 1, 3], 'payouts': {1: 134, 3: 134, 0: 133}},
              {'amount': 666, 'eligible': [0, 1], 'payouts': {1: 333, 0: 333}}],
             ['Main pot split 3 ways', 'Pair of Kings • 1 side pot(s)']),
        )
        for name, short_hand, script, pots, summary in cases:
            with self.subTest(name):
                room = six_human_room(7, [5000, 5000, 5000, 117, 5000, 5000])
                game = room.game
                set_cards(game, {0: ['Kd', '4c'], 1: ['Kh', '4d'], 2: ['Qc', 'Qd'],
                                 3: short_hand.split(), 4: ['3c', '3d'], 5: ['5h', '6h']})
                before = stacks_before_hand(game)
                play_script(self, room, script)
                self.assertEqual(game.current_stage, 'showdown')
                self.assertEqual([{key: pot[key] for key in ('amount', 'eligible', 'payouts')}
                                  for pot in game.last_pot_awards], pots)
                self.assertEqual(game.last_refunds, {})
                back = chips_back(game, before)
                self.assertEqual(sum(back), sum(game.get_hand_contributions()))
                real = {room.names[seat]: amount for seat, amount in enumerate(back) if amount}

                for seat, client in client_views(room).items():
                    lines = payout_lines(client)
                    self.assertEqual(printed_payouts(lines), real, f'seat {seat}: {lines}')
                    self.assertEqual(compact_result(client), summary)
                    # The Payout History keeps a copy of these fields (room_session.last_payout).
                    history = SimpleNamespace(names=client.names, last_pot_awards=client.last_pot_awards,
                                              result_text=client.result_text, hand_number=client.hand_number,
                                              showdown_hands=client.showdown_hands)
                    self.assertEqual(payout_lines(history), lines)
                    # The shared recap agrees for the viewer's own seat.
                    self.assertEqual(recap.received_total(client, 0), back[seat])
                    self.assertEqual(recap.player_hand_net(client),
                                     [game.player_stack, *game.npc_stacks][seat] - before[seat])
                # The odd chip line follows the engine's winner order, not seat order.
                host_lines = payout_lines(client_views(room, [0])[0])
                first_split = next(pot for pot in game.last_pot_awards if len(pot['winners']) > 1)
                odd_seat = first_split['winners'][0]
                self.assertIn(f"{room.names[odd_seat]} receives ${first_split['payouts'][odd_seat]:,}", host_lines)
                self.assertGreater(first_split['payouts'][odd_seat], first_split['share'])

    def test_snapshot_of_settled_hand_is_unchanged_by_recaps(self):
        room = six_human_room(9, [5000, 5000, 5000, 117, 5000, 5000])
        game = room.game
        set_cards(game, {0: ['Kd', '4c'], 1: ['Kh', '4d'], 2: ['Qc', 'Qd'],
                         3: ['As', 'Ad'], 4: ['3c', '3d'], 5: ['5h', '6h']})
        script = {('preflop', 3): [('bet_raise', 117)],
                  **{('preflop', seat): [('fold', 0)] for seat in (4, 5, 2)},
                  ('preflop', 0): [('check_call', 0)], ('preflop', 1): [('check_call', 0)],
                  **{(stage, seat): [('check_call', 0)] for stage in ('flop', 'turn', 'river') for seat in (0, 1)}}
        play_script(self, room, script)
        message = snapshot(game, 1, room.revision, room.names)
        wire = json.dumps(message, sort_keys=True)
        client = ClientGame()
        client.apply(message)
        recap.recap_lines(client)
        recap.recap_display_lines(client)
        payout_lines(client)
        compact_result(client)
        self.assertEqual(json.dumps(message, sort_keys=True), wire)


if __name__ == '__main__':
    unittest.main()
