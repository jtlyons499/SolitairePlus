"""Six-seat authority with humans taking over only between hands."""
import copy
import math
import random
from solitaireplus.app import state
from solitaireplus.games.poker import holdem_ui as ui
from room_game import RoomGame, load_roster
from room_protocol import snapshot

# B67: a timer due this much later than the clock was armed on another clock: re-arm it.
CLOCK_JUMP_MS=60000
# The pause between a finished hand and the next deal.
NEXT_HAND_MS=6000

class RoomAuthority:
    def __init__(self, host_name, roster=None):
        self.roster=copy.deepcopy(load_roster() if roster is None else roster)
        self.npcs=random.sample(self.roster,5)
        self.names=[host_name]+[n['name'] for n in self.npcs]
        self.humans={0:0};self.connections={0:host_name};self.waiting=[];self.departed=set()
        self.game=None;self.revision=0;self.ready=set();self.due=0;self.starting_stack=5000;self.new_seats=set()
        self.chips_added=0;self.table_notices=[];self.sit_out=set();self.pending_buybacks=set();self.resume_at=None;self.completed_hand=0;self.now=0;self.table_speed=state.holdem_table_speed
    def join(self, identity, name):
        if identity in self.connections:return
        self.connections[identity]=name
        if self.game is None:self.assign(identity,name)
        else:self.waiting.append((identity,name))
        self.revision+=1
    def assign(self, identity, name):
        occupied=set(self.humans.values())
        candidates=[i for i in range(1,6) if i not in occupied]
        if self.game:
            # B68: a knocked-out NPC's seat first (with the buy-in), else a funded NPC seat and its stack.
            candidates.sort(key=lambda i:self.game.npc_stacks[i-1]>0)
        if not candidates:return False
        seat=candidates[0];old=self.names[seat];self.humans[identity]=seat;self.names[seat]=name
        if self.game:
            if self.game.npc_stacks[seat-1]<=0:
                self.game.npc_stacks[seat-1]=self.starting_stack;self.game.npc_busted[seat-1]=False
                self.chips_added+=self.starting_stack
                self.table_notices.append(f"{name} buys in for ${self.starting_stack:,} in {old}'s seat.")
            self._install_seat(seat)
            self.new_seats.add(seat)
        return True
    def _install_seat(self, seat):
        """Put the seat's current occupant into the game, built from the room's state now, and
        forget what the table learned about the previous one (B81)."""
        owner=next((identity for identity,s in self.humans.items() if s==seat),None)
        if owner is None:record=copy.deepcopy(self.npcs[seat-1])
        else:record={'id':f'human_{owner}','name':self.names[seat],'skill_tier':'mid'}
        self.game.npcs[seat-1]=record
        self.game.reset_seat_ai_state(seat)
    def leave(self, identity):
        self.connections.pop(identity,None);self.sit_out.discard(identity);self.pending_buybacks.discard(identity)
        self.waiting=[pair for pair in self.waiting if pair[0]!=identity]
        if identity in self.humans:self.departed.add(identity)
        self.ready.discard(identity);self.revision+=1
        if self.game is None or self.game.hand_complete:self.boundary()
    def boundary(self):
        """Seat changes between hands. Returns True only if someone left a seat or was seated (B69)."""
        changed=bool(self.departed)
        for identity in list(self.departed):
            seat=self.humans.pop(identity,None)
            if seat:
                self.names[seat]=self.npcs[seat-1]['name']
                if self.game:self._install_seat(seat)
        self.departed.clear()
        remaining=[]
        for identity,name in self.waiting:
            if self.assign(identity,name):changed=True
            else:remaining.append((identity,name))
        self.waiting=remaining
        return changed
    def configure(self, seat=None, delta=0, stack=None):
        if self.game:return False
        if stack in (1000,5000,10000,25000):self.starting_stack=stack
        if isinstance(seat,int) and 1<=seat<=5 and seat not in self.humans.values():
            old=self.npcs[seat-1]
            index=next((i for i,n in enumerate(self.roster) if n['id']==old['id']),0)
            step=1 if delta>=0 else -1
            occupied={n['id'] for j,n in enumerate(self.npcs) if j!=seat-1}
            for _ in self.roster:
                index=(index+step)%len(self.roster)
                if self.roster[index]['id'] not in occupied:break
            self.npcs[seat-1]=self.roster[index]
            self.names[seat]=self.npcs[seat-1]['name']
        self.revision+=1;return True
    def start(self):
        if self.game:return False
        self.game=RoomGame()
        # B79: showdown pots name their contributors, so a pot of only the winners' own chips gives no XP.
        self.game.record_pot_contributors=True
        participants=copy.deepcopy(self.npcs)
        for identity,seat in self.humans.items():
            if seat:participants[seat-1]={'id':f'human_{identity}','name':self.names[seat],'skill_tier':'mid'}
        self.game.start_session(participants,self.starting_stack,25);self.game.start_hand()
        self.revision+=1;return True
    def required(self):return set(self.humans)&set(self.connections)
    def seats(self):
        by_seat={seat:identity for identity,seat in self.humans.items()}
        return [{'name':n,'kind':'Human' if i in by_seat else 'NPC','connected':by_seat.get(i) in self.connections if i in by_seat else True} for i,n in enumerate(self.names)]
    def view(self, identity):
        base={'revision':self.revision,'seats':self.seats(),'waiting_names':[n for _,n in self.waiting],'starting_stack':self.starting_stack}
        if self.game is None:return {'type':'lobby',**base}
        if identity not in self.humans:return {'type':'waiting',**base,'text':'Waiting for a seat at the next hand'}
        message=snapshot(self.game,self.humans[identity],self.revision,self.names)
        if self.humans[identity] in self.new_seats:message['data']['player_hand']=[]
        for j,seat in enumerate([i for i in range(6) if i!=self.humans[identity]]):
            if seat in self.new_seats:message['data']['npc_hands'][j]=[]
        message.update(base);message['ready_count']=len(self.ready&self.required());message['ready_total']=len(self.required());message['you_ready']=identity in self.ready
        message['physical_seat']=self.humans[identity]
        message['sit_out']=identity in self.sit_out
        message['buyback_pending']=identity in self.pending_buybacks
        message['resting_seats']=sorted(self.game.sitting_out)
        message['table_speed']=self.table_speed
        message['next_hand_seconds']=self.countdown_seconds()
        # B70: the next hand starts at countdown_at on the host clock; host_now is when this view
        # was built, so a guest can count down on its own clock with no revision bump per second.
        message['countdown_at']=self.resume_at
        message['host_now']=self.now
        return message
    def countdown_seconds(self):
        if self.resume_at is None:return NEXT_HAND_MS//1000
        return max(0,math.ceil((self.resume_at-self.now)/1000))
    def act(self, identity, action, amount=0, revision=None):
        if identity not in self.connections or revision!=self.revision:return False
        if action=='start':return identity==0 and self.start()
        if action=='sit_out':
            if identity not in self.humans:return False
            if identity in self.sit_out:self.sit_out.remove(identity);text='will rejoin next hand'
            else:self.sit_out.add(identity);text='will sit out next hand'
            self.table_notices.append(f'{self.names[self.humans[identity]]} {text}.');self.revision+=1
            return True
        if action=='buyback':
            if not self.game or identity not in self.humans or identity in self.pending_buybacks:return False
            seat=self.humans[identity]
            stack=self.game.player_stack if seat==0 else self.game.npc_stacks[seat-1]
            if stack>0:return False
            self.ready.discard(identity)
            if not self.game.hand_complete:
                # A rebuy during an active hand is only a reservation. Restoring
                # chips now can make a busted seat visible to live-seat logic and
                # accidentally drop it into the current hand.
                self.pending_buybacks.add(identity);self.revision+=1
                self.table_notices.append(f'{self.names[seat]} bought back for ${self.starting_stack:,} and will rejoin next hand.')
                return True
            self._apply_buyback(identity)
            self.revision+=1
            return True
        if action=='next_hand':
            if not self.game or not self.game.hand_complete:return False
            self.boundary()
            if identity not in self.humans:return False
            self.ready.add(identity);self.revision+=1
            self.next_if_ready();return True
        if not self.game or identity not in self.humans:return False
        g=self.game;seat=self.humans[identity]
        if g.hand_complete or g.current_actor!=seat or not g.actor_needs_action(seat):return False
        if not isinstance(amount,int) or isinstance(amount,bool) or not 0<=amount<=1000000:return False
        if seat==0:
            if action=='fold':ok=g.player_fold()
            elif action=='check_call':ok=g.player_call() if g.get_player_amount_to_call() else g.player_check()
            elif action=='bet_raise':ok=g.player_bet(amount) if g.current_bet==0 else g.player_raise(amount)
            else:return False
        else:
            i=seat-1
            if action=='fold':ok=g.npc_fold(i)
            elif action=='check_call':ok=g.npc_call(i) if g.get_npc_amount_to_call(i) else g.npc_check(i)
            elif action=='bet_raise':
                # B80: the host's rule (can_player_raise) for guests too: no bet or raise that no
                # seat left in the hand can answer. Refused before the engine changes anything.
                if not g.can_npc_raise(i):return False
                ok=g.npc_raise(i,amount) if g.current_bet else g.npc_bet(i,amount)
            else:return False
        if ok:
            if not g.hand_complete and (seat or action=='fold'):g.advance_to_next_actor()
            self.revision+=1;self.due=0
        return ok
    def _apply_buyback(self,identity):
        if not self.game or identity not in self.humans:return False
        seat=self.humans[identity]
        stack=self.game.player_stack if seat==0 else self.game.npc_stacks[seat-1]
        if stack>0:
            self.pending_buybacks.discard(identity);return False
        if seat==0:self.game.player_stack=self.starting_stack;self.game.player_busted=False
        else:self.game.npc_stacks[seat-1]=self.starting_stack;self.game.npc_busted[seat-1]=False
        self.pending_buybacks.discard(identity);self.chips_added+=self.starting_stack
        self.table_notices.append(f'{self.names[seat]} returns with ${self.starting_stack:,}.')
        return True
    def apply_pending_buybacks(self):
        changed=False
        for identity in list(self.pending_buybacks):
            if identity in self.connections:changed=self._apply_buyback(identity) or changed
            else:self.pending_buybacks.discard(identity)
        return changed
    def next_if_ready(self):
        if self.game and self.game.hand_complete and self.required()<=self.ready:
            # B68: waiting humans are seated (in busted NPC seats first) before replacement NPCs.
            changed=self.boundary()
            changed=self.replace_busted_npcs() or changed
            changed=self.apply_pending_buybacks() or changed
            if sum(s>0 for s in [self.game.player_stack,*self.game.npc_stacks])>1:
                self.game.sitting_out={self.humans[i] for i in self.sit_out if i in self.humans}
                if len(self.game.get_live_player_indexes())>=2:
                    self.ready.clear();self.new_seats.clear();self.game.start_hand();self.revision+=1;self.due=0;self.resume_at=None
                    return
            if changed:self.revision+=1
    def replace_busted_npcs(self):
        changed=False
        occupied=set(self.humans.values())
        for seat in range(1,6):
            if seat in occupied or self.game.npc_stacks[seat-1]>0:continue
            used={n['id'] for n in self.npcs}
            choices=[n for n in self.roster if n['id'] not in used]
            if not choices:choices=[n for n in self.roster if n['id']!=self.npcs[seat-1]['id']]
            replacement=copy.deepcopy(random.choice(choices))
            old=self.names[seat];self.npcs[seat-1]=replacement;self.names[seat]=replacement['name']
            self._install_seat(seat)
            self.game.npc_stacks[seat-1]=self.starting_stack;self.game.npc_busted[seat-1]=False
            self.chips_added+=self.starting_stack
            self.table_notices.append(f'{replacement["name"]} replaces {old} with ${self.starting_stack:,}.')
            changed=True
        return changed
    def set_speed(self,speed):
        if speed not in ('slow','normal','fast') or speed==self.table_speed:return
        old=self.table_speed;self.table_speed=speed;state.holdem_table_speed=speed
        self.table_notices.append(f'Host has set table speed from {old.title()} to {speed.title()}.');self.revision+=1
    def update(self, now):
        self.now=now
        g=self.game
        if not g:return
        # B67: a timer armed on another, much later clock re-arms instead of never coming due.
        if self.due and now<self.due-CLOCK_JUMP_MS:self.due=0
        if self.resume_at is not None and now<self.resume_at-NEXT_HAND_MS-CLOCK_JUMP_MS:self.resume_at=now+NEXT_HAND_MS
        if g.hand_complete:
            # B69: only a real seat change bumps the revision (a bump makes guests' actions stale).
            if (self.waiting or self.departed) and self.boundary():self.revision+=1
            if self.completed_hand!=g.hand_number:
                # B70: one bump sends the 'starts at' time (countdown_at), not one bump a second.
                self.completed_hand=g.hand_number
                self.resume_at=now+NEXT_HAND_MS;self.revision+=1
            if self.resume_at is not None and now>=self.resume_at:self.ready.update(self.required())
            self.next_if_ready();return
        complete=g.is_betting_round_complete()
        seat=g.current_actor
        controlling=next((identity for identity,s in self.humans.items() if s==seat),None)
        if not complete and controlling in self.connections:self.due=0;return
        if not self.due:self.due=now+(ui.get_holdem_street_delay(speed=self.table_speed) if complete else ui.get_holdem_npc_delay(speed=self.table_speed));return
        if now<self.due:return
        self.due=0
        if complete:g.advance_after_betting_round()
        elif controlling is not None:
            if seat==0:g.player_fold()
            else:g.npc_fold(seat-1)
            if not g.hand_complete:g.advance_to_next_actor()
        elif seat>0:g.run_next_npc_action()
        else:g.advance_to_next_actor()
        self.revision+=1
