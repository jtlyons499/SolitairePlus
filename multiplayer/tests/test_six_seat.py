import unittest
import json
import random
from room_table import RoomAuthority
from room_protocol import ClientGame, snapshot


def stacks(t):
    return [t.game.player_stack,*t.game.npc_stacks]


def seat_can_raise(g,seat):
    """The host's raise rule for one seat (B86 core.can_raise through the engine)."""
    return g.can_player_raise() if seat==0 else g.can_npc_raise(seat-1)

class SixSeatTests(unittest.TestCase):
    def make(self, count=6):
        t=RoomAuthority('Host')
        for i in range(1,count):t.join(i,'Human '+str(i))
        t.start();return t
    def finish(self,t,now=0):
        for _ in range(2000):
            if t.game.hand_complete:return now
            actor=t.game.current_actor
            human=next((i for i,s in t.humans.items() if s==actor),None)
            if human in t.connections:t.act(human,'check_call',0,t.revision)
            now+=10000;t.update(now)
        self.fail('Hand never completed')
    def test_six_humans_many_hands(self):
        t=self.make();now=0
        for _ in range(30):
            now=self.finish(t,now)
            self.assertEqual(sum([t.game.player_stack,*t.game.npc_stacks]),30000)
            if sum(s>0 for s in [t.game.player_stack,*t.game.npc_stacks])<2:break
            for identity in list(t.connections):self.assertTrue(t.act(identity,'next_hand',0,t.revision))
        self.assertEqual(len(t.game.npcs),5)
    def test_private_views_all_seats(self):
        t=self.make()
        all_hands=[t.game.player_hand,*t.game.npc_hands]
        for identity,seat in t.humans.items():
            m=t.view(identity)
            self.assertEqual(m['data']['player_hand'],all_hands[seat])
            self.assertTrue(all(not cards for cards in m['data']['npc_hands']))
            self.assertNotIn('deck',json.dumps(m))
            self.assertEqual(len(m['names']),6)
    def test_late_join_no_mid_hand_takeover(self):
        t=self.make(2);before=t.names[:];t.join(9,'Late')
        self.assertNotIn(9,t.humans);self.assertEqual(t.view(9)['type'],'waiting')
        self.assertEqual(t.names,before)
        self.finish(t);before_stacks=stacks(t);busted=[seat for seat in range(2,6) if before_stacks[seat]<=0]
        t.update(999999)
        self.assertIn(9,t.humans)
        # B68: a busted NPC seat (if the hand left one) is taken first, with the normal buy-in.
        expected=list(before_stacks)
        if busted:
            self.assertEqual(t.humans[9],busted[0]);expected[busted[0]]=t.starting_stack
        self.assertEqual(expected,stacks(t))
        self.assertEqual(t.chips_added,t.starting_stack if busted else 0)
        self.assertEqual(t.names[t.humans[9]],'Late')
        self.assertEqual(t.view(9)['data']['player_hand'],[]) # no inherited private cards until new deal
    def test_disconnect_folds_then_npc(self):
        t=self.make(3);seat=t.humans[2];t.leave(2)
        self.finish(t);t.update(999999)
        self.assertNotIn(2,t.humans);self.assertEqual(t.names[seat],t.npcs[seat-1]['name'])
        self.assertEqual(sum([t.game.player_stack,*t.game.npc_stacks]),30000)
    def test_lobby_config_and_invalid_actions(self):
        t=RoomAuthority('Host');t.configure(stack=10000);t.configure(seat=3,delta=1);t.join(1,'Guest')
        self.assertFalse(t.act(1,'start',0,t.revision));self.assertTrue(t.act(0,'start',0,t.revision))
        self.assertEqual(sum([t.game.player_stack,*t.game.npc_stacks])+t.game.pot,60000)
        self.assertFalse(t.act(99,'fold',0,t.revision));self.assertFalse(t.act(0,'fold',0,-1))
        self.assertFalse(t.configure(stack=1000))
        lobby=RoomAuthority('Host');lobby.join(1,'Guest');lobby.leave(1)
        self.assertNotIn(1,lobby.humans)
        self.assertEqual(lobby.names[1],lobby.npcs[0]['name'])
    def test_sidepots_allin(self):
        t=self.make();g=t.game
        # Restart a hand with uneven existing bankrolls, preserving total money.
        self.finish(t)
        g.player_stack=500;g.npc_stacks=[1000,2000,3000,8000,15500]
        for identity in list(t.connections):t.act(identity,'next_hand',0,t.revision)
        now=0
        for _ in range(500):
            if g.hand_complete:break
            actor=g.current_actor
            human=next((i for i,s in t.humans.items() if s==actor),None)
            if human is not None:
                stack=[g.player_stack,*g.npc_stacks][actor];bet=[g.player_round_bet,*g.npc_round_bets][actor]
                if not t.act(human,'bet_raise',stack+bet,t.revision):t.act(human,'check_call',0,t.revision)
            now+=10000;t.update(now)
        self.assertTrue(g.hand_complete)
        self.assertEqual(sum([g.player_stack,*g.npc_stacks]),30000)
        self.assertGreater(len(g.last_pot_awards),1)
        # B79: every showdown pot names the seats that paid into it, seat-relative in each view.
        contributions=[g.player_hand_contribution,*g.npc_hand_contributions]
        for pot in g.last_pot_awards:
            self.assertGreaterEqual(len(pot['contributors']),2,pot)
            self.assertLessEqual(set(pot['eligible']),set(pot['contributors']),pot)
            self.assertTrue(all(contributions[seat]>0 for seat in pot['contributors']),pot)
        for i,seat in t.humans.items():
            order=[seat]+[s for s in range(6) if s!=seat]
            for pot,host_pot in zip(t.view(i)['data']['last_pot_awards'],g.last_pot_awards):
                self.assertTrue(all(0<=s<6 for s in pot['winners']))
                self.assertEqual(sorted(order[s] for s in pot['contributors']),sorted(host_pot['contributors']))

    def npc_must_act(self,t):
        """Host checks/calls until an NPC seat is on the turn (seeded)."""
        for _ in range(20):
            g=t.game
            if g.current_actor!=0 and not g.is_betting_round_complete():return
            self.assertTrue(t.act(0,'check_call',0,t.revision))
        self.fail('No NPC turn came up')

    def test_clock_going_backwards_rearms_timer(self):
        # B67: a timer armed on a much later clock (another clock source) re-arms instead of stalling.
        random.seed(5)
        t=RoomAuthority('Host');t.table_speed='normal';t.start();self.npc_must_act(t)
        actor,revision=t.game.current_actor,t.revision
        t.update(10**9);self.assertEqual((t.game.current_actor,t.revision),(actor,revision))
        t.update(10000);t.update(12000)
        self.assertNotEqual((t.game.current_actor,t.revision),(actor,revision))
        # The next-hand countdown re-arms the same way.
        now=self.finish(t,10**9);t.update(now+1);hand=t.game.hand_number
        self.assertEqual(t.resume_at,now+6001)
        t.update(20000);self.assertEqual(t.game.hand_number,hand)
        t.update(26001);self.assertEqual(t.game.hand_number,hand+1)

    def test_unseatable_waiter_does_not_bump_revision(self):
        # B69: six humans, a seventh waits; nothing changes, so the revision stays and guests can act.
        random.seed(8)
        t=self.make(6);now=self.finish(t);t.update(now+1)
        t.join(9,'Late');revision=t.revision
        for _ in range(3):t.update(now+2)
        self.assertEqual(t.revision,revision)
        self.assertEqual([name for _,name in t.waiting],['Late'])
        self.assertTrue(t.act(1,'sit_out',0,revision))

    def test_late_join_takes_busted_npc_seat_with_buy_in(self):
        # B68: a waiting human takes a busted NPC seat with the buy-in, before a replacement NPC is made.
        random.seed(11)
        t=self.make(2);now=self.finish(t);g=t.game
        # Host, guest (seat 1) and NPC seats 2-5. Seat 2 has chips; seat 3 is knocked out (same total).
        self.assertEqual(sum(stacks(t)),30000)
        g.player_stack=5000;g.npc_stacks=[5000,5000,0,10000,5000];g.refresh_busted_state()
        self.assertTrue(g.npc_busted[2]);self.assertFalse(g.npc_busted[1])
        old=t.names[3]
        t.join(9,'Late');self.assertEqual(t.view(9)['type'],'waiting')
        self.assertEqual(t.view(9)['text'],'Waiting for a seat at the next hand')
        t.update(now+1)
        self.assertEqual(t.humans[9],3)
        self.assertEqual(stacks(t),[5000,5000,5000,t.starting_stack,10000,5000]);self.assertFalse(g.npc_busted[2])
        self.assertEqual(t.chips_added,t.starting_stack)
        self.assertEqual(t.names[3],'Late');self.assertEqual(g.npcs[2]['id'],'human_9')
        self.assertIn(f"Late buys in for ${t.starting_stack:,} in {old}'s seat.",t.table_notices)
        for identity in list(t.connections):t.act(identity,'next_hand',0,t.revision)
        self.assertFalse(g.hand_complete);self.assertIn(3,g.hand_seat_indexes)
        self.assertEqual(sum(stacks(t))+g.pot,30000+t.starting_stack)
        self.assertFalse(any('replaces' in notice for notice in t.table_notices))
        self.assertEqual(t.view(9)['physical_seat'],3)
        # With no busted NPC seat, a joiner still takes over a funded NPC seat and its stack.
        now=self.finish(t,now);t.update(now+1)
        g.player_stack=5000;g.npc_stacks=[5000,5000,5000,15000,5000];g.refresh_busted_state()
        before=stacks(t);added=t.chips_added
        t.join(10,'Later');t.update(now+2)
        self.assertEqual(t.humans[10],2);self.assertEqual(stacks(t),before);self.assertEqual(t.chips_added,added)

    def test_takeover_resets_seat_ai_state(self):
        # B81: a new occupant does not inherit what the table learned about the old one.
        random.seed(4)
        t=self.make(1);now=self.finish(t);g=t.game
        reads=g.table_reads
        self.assertTrue(reads.histories.get(1),'precondition: the seat-1 NPC acted this hand')
        g.npc_ai_last_decisions[0]={'action':'call'};reads.reveals[1]=[True]
        self.assertEqual(reads.learning.identities[1],t.npcs[0]['id'])
        t.join(9,'Late');t.update(now+1)
        self.assertEqual(t.humans[9],1)
        self.assertEqual(g.npcs[0],{'id':'human_9','name':'Late','skill_tier':'mid'})
        self.assertNotIn(1,reads.histories);self.assertNotIn(1,reads.reveals)
        self.assertIsNone(g.npc_ai_last_decisions[0])
        self.assertEqual(reads.learning.identities[1],'human_9')
        self.assertTrue(any(reads.histories.get(seat) for seat in range(2,6)),'other seats keep their reads')
        # The human leaves: the seat's NPC comes back fresh, from the room's current NPC list.
        reads.histories[1]=[('call','preflop',False,0.0)]
        t.leave(9)
        self.assertNotIn(9,t.humans);self.assertEqual(g.npcs[0],t.npcs[0]);self.assertIsNot(g.npcs[0],t.npcs[0])
        self.assertNotIn(1,reads.histories);self.assertEqual(reads.learning.identities[1],t.npcs[0]['id'])
        # A busted NPC replaced by a new one: fresh state too.
        g.npc_stacks[1]+=g.npc_stacks[0];g.npc_stacks[0]=0;g.refresh_busted_state()
        reads.histories[1]=[('raise','flop',True,1.0)];g.npc_ai_last_decisions[0]={'action':'raise'}
        t.replace_busted_npcs()
        self.assertEqual(g.npcs[0],t.npcs[0]);self.assertNotIn(1,reads.histories)
        self.assertIsNone(g.npc_ai_last_decisions[0]);self.assertEqual(reads.learning.identities[1],t.npcs[0]['id'])

    def test_guest_cannot_raise_when_no_one_can_respond(self):
        # B80: like the host (can_player_raise), a guest may not bet or raise when every other
        # seat still in the hand is all in; the refusal changes nothing.
        random.seed(2)
        t=self.make(6);g=t.game
        guest=g.big_blind_index;self.assertNotEqual(guest,0)
        shover=g.current_actor;self.assertNotIn(shover,(0,guest))
        g.npc_stacks[shover-1]//=4  # the short stack that shoves; everyone else folds to the guest
        for _ in range(40):
            seat=g.current_actor
            if seat==guest:break
            identity=next(i for i,s in t.humans.items() if s==seat)
            if seat==shover:
                self.assertTrue(t.act(identity,'bet_raise',g.npc_stacks[seat-1]+g.npc_round_bets[seat-1],t.revision))
            else:self.assertTrue(t.act(identity,'fold',0,t.revision))
        i=guest-1;identity=next(k for k,s in t.humans.items() if s==guest)
        self.assertEqual(g.current_actor,guest)
        self.assertTrue(g.npc_all_in[shover-1]);self.assertGreater(g.get_npc_amount_to_call(i),0)
        self.assertGreater(g.npc_stacks[i],g.get_npc_amount_to_call(i))  # the guest could cover a raise
        names=list(t.names);before=json.dumps(snapshot(g,guest,t.revision,names),sort_keys=True)
        revision=t.revision;wager_flag=getattr(g,'last_wager_full',None)
        self.assertFalse(t.act(identity,'bet_raise',g.npc_stacks[i]+g.npc_round_bets[i],t.revision))
        self.assertFalse(t.act(identity,'bet_raise',g.get_minimum_raise_to(),t.revision))
        self.assertEqual(t.revision,revision);self.assertEqual(getattr(g,'last_wager_full',None),wager_flag)
        self.assertEqual(json.dumps(snapshot(g,guest,t.revision,names),sort_keys=True),before)
        client=ClientGame();client.apply(t.view(identity))
        self.assertTrue(client.can_player_call());self.assertFalse(client.can_player_raise())
        self.assertTrue(t.act(identity,'check_call',0,t.revision))
        self.assertTrue(g.npc_round_bets[i]==g.current_bet or g.hand_complete or g.is_betting_round_complete())

    def test_can_raise_agrees_for_every_human_seat(self):
        # B80 parity: each human's ClientGame offers a raise exactly when the host would accept one.
        checked=0;refused=0
        for seed in range(20):
            random.seed(300+seed);t=self.make(6);g=t.game;rng=random.Random(seed);now=0
            if seed%2:g.player_stack//=5;g.npc_stacks[2]//=3  # uneven stacks: short all-ins
            for _ in range(600):
                if g.hand_complete:break
                seat=g.current_actor;identity=next((i for i,s in t.humans.items() if s==seat),None)
                if identity is None or not g.actor_needs_action(seat):
                    now+=10000;t.update(now);continue
                client=ClientGame();client.apply(t.view(identity))
                where=f'seed {seed}, seat {seat}, {g.current_stage}'
                can=seat_can_raise(g,seat)
                self.assertEqual(client.can_player_raise(),can,where)
                self.assertEqual(client.get_minimum_raise_to(),g.get_minimum_raise_to(),where)
                checked+=1;refused+=not can
                stack=stacks(t)[seat];bet=[g.player_round_bet,*g.npc_round_bets][seat]
                roll=rng.random()
                if roll<.25:action,amount='bet_raise',stack+bet
                elif roll<.45:action,amount='bet_raise',g.get_minimum_raise_to() if g.current_bet else g.get_minimum_open_bet()
                elif roll<.55:action,amount='fold',0
                else:action,amount='check_call',0
                current=g.current_bet;accepted=t.act(identity,action,amount,t.revision)
                # A refused raise changes nothing; a short stack's all-in 'raise' is a call (accepted).
                if action=='bet_raise' and not can and stack+bet>current:self.assertFalse(accepted,where)
                if not accepted:self.assertTrue(t.act(identity,'check_call',0,t.revision),where)
            self.assertTrue(g.hand_complete)
        self.assertGreater(checked,150);self.assertGreater(refused,0)

import test_relay
from room_session import RoomTable
import time

class SixRelayTests(unittest.TestCase):
    setUp=test_relay.RelayTests.setUp
    tearDown=test_relay.RelayTests.tearDown
    def test_six_clients_and_late_join(self):
        # B67: every room gets the same fake millisecond clock (the old test mixed
        # time.monotonic() with a counter restarting at 0, so the host's timers never fired).
        clock=[0]
        host=RoomTable('Host',True,self.address);self.peers.append(host)
        deadline=time.monotonic()+8
        while not host.code and time.monotonic()<deadline:host.update(clock[0]);time.sleep(.01)
        self.assertTrue(host.code)
        from relay_server import CODE_ALPHABET
        self.assertEqual(len(host.code),6);self.assertTrue(set(host.code)<=set(CODE_ALPHABET))  # 6-character codes since 0.0.7
        clients=[host]
        for i in range(1,3):
            client=RoomTable('Guest '+str(i),False,self.address,host.code);self.peers.append(client);clients.append(client)
        def pump(seconds=1,until=None):
            """Update every room on the shared clock (+16 ms a frame) until `until()` or the time is up."""
            deadline=time.monotonic()+seconds
            while time.monotonic()<deadline:
                clock[0]+=16
                for c in clients:c.update(clock[0])
                if until and until():return
                time.sleep(.005)
        pump(8,lambda:len(host.authority.humans)==3)
        self.assertEqual(len(host.authority.humans),3)
        self.assertTrue(host.act('start'));pump(4,lambda:all(c.message['type']=='state' for c in clients))
        for i in range(3,6):
            c=RoomTable('Late '+str(i),False,self.address,host.code);self.peers.append(c);clients.append(c)
        pump(8,lambda:len(host.authority.waiting)==3 and all(c.message['type']=='waiting' for c in clients[3:]))
        self.assertEqual(len(host.authority.waiting),3)
        self.assertTrue(all(c.message['type']=='waiting' for c in clients[3:]))
        deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            clock[0]+=10000
            for c in clients:c.update(clock[0])
            for c in clients:
                if c.message['type']=='state' and not c.game.hand_complete and c.game.current_actor==0:c.act('check_call')
            if (host.game.hand_complete or host.game.hand_number>1) and len(host.authority.humans)==6 and all(c.message['type']=='state' for c in clients):break
            time.sleep(.004)
        self.assertEqual(len(host.authority.humans),6)
        self.assertTrue(host.game.hand_complete or host.game.hand_number>1)
        extra=RoomTable('Seventh',False,self.address,host.code);self.peers.append(extra)
        deadline=time.monotonic()+8
        while not extra.failed and time.monotonic()<deadline:clock[0]+=16;extra.update(clock[0]);time.sleep(.01)
        self.assertTrue(extra.failed);self.assertIn('six',extra.status)
        clients[2].close();clients.remove(clients[2]);pump(5,lambda:len(host.authority.connections)==5)
        self.assertEqual(len(host.authority.connections),5)
        self.assertFalse(host.failed)
        host.close();pump(5,lambda:all(c.failed for c in clients[1:]))
        self.assertTrue(all(c.failed for c in clients[1:]))
