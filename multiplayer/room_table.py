"""Six-seat authority with humans taking over only between hands."""
import copy
import random
import texas_holdem_ui as ui
from lan_table import TwoHumanGame
from lan_protocol import snapshot
from standalone_table import load_roster

class RoomGame(TwoHumanGame):
    """Exclude resting seats without moving, spending or removing their chips."""
    def __init__(self):
        super().__init__();self.sitting_out=set();self.starting_network_hand=False
    def get_live_player_indexes(self):
        return [seat for seat in super().get_live_player_indexes() if seat not in self.sitting_out]
    def refresh_busted_state(self):
        newly_busted=super().refresh_busted_state()
        if self.starting_network_hand:
            if 0 in self.sitting_out:self.player_busted=True
            for seat in self.sitting_out:
                if seat:self.npc_busted[seat-1]=True
        return newly_busted
    def start_hand(self):
        self.starting_network_hand=True
        try:result=super().start_hand()
        finally:self.starting_network_hand=False
        self.player_busted=self.player_stack<=0
        self.npc_busted=[stack<=0 for stack in self.npc_stacks]
        if result:
            if 0 in self.sitting_out:self.player_folded=True;self.player_action_text='Sitting out'
            for seat in self.sitting_out:
                if seat:self.npc_folded[seat-1]=True;self.npc_action_texts[seat-1]='Sitting out'
        return result

class RoomAuthority:
    def __init__(self, host_name, roster=None):
        self.roster=copy.deepcopy(load_roster() if roster is None else roster)
        self.npcs=random.sample(self.roster,5)
        self.names=[host_name]+[n['name'] for n in self.npcs]
        self.humans={0:0};self.connections={0:host_name};self.waiting=[];self.departed=set()
        self.game=None;self.revision=0;self.ready=set();self.due=0;self.starting_stack=5000;self.new_seats=set()
        self.chips_added=0;self.table_notices=[];self.sit_out=set();self.resume_at=None;self.completed_hand=0;self.table_speed=ui.holdem_table_speed
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
            candidates=[i for i in candidates if self.game.npc_stacks[i-1]>0]
        if not candidates:return False
        seat=candidates[0];self.humans[identity]=seat;self.names[seat]=name
        if self.game:
            self.game.npcs[seat-1]={'id':f'human_{identity}','name':name,'skill_tier':'mid'}
            self.new_seats.add(seat)
        return True
    def leave(self, identity):
        self.connections.pop(identity,None);self.sit_out.discard(identity)
        self.waiting=[pair for pair in self.waiting if pair[0]!=identity]
        if identity in self.humans:self.departed.add(identity)
        self.ready.discard(identity);self.revision+=1
        if self.game is None or self.game.hand_complete:self.boundary()
    def boundary(self):
        for identity in list(self.departed):
            seat=self.humans.pop(identity,None)
            if seat:
                npc=copy.deepcopy(self.npcs[seat-1]);self.names[seat]=npc['name']
                if self.game:self.game.npcs[seat-1]=npc
        self.departed.clear()
        remaining=[]
        for identity,name in self.waiting:
            if not self.assign(identity,name):remaining.append((identity,name))
        self.waiting=remaining
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
        if identity not in self.humans:return {'type':'waiting',**base,'text':'Waiting for a surviving NPC seat at the next hand'}
        message=snapshot(self.game,self.humans[identity],self.revision,self.names)
        if self.humans[identity] in self.new_seats:message['data']['player_hand']=[]
        for j,seat in enumerate([i for i in range(6) if i!=self.humans[identity]]):
            if seat in self.new_seats:message['data']['npc_hands'][j]=[]
        message.update(base);message['ready_count']=len(self.ready&self.required());message['ready_total']=len(self.required());message['you_ready']=identity in self.ready
        message['physical_seat']=self.humans[identity]
        message['sit_out']=identity in self.sit_out
        message['resting_seats']=sorted(self.game.sitting_out)
        message['table_speed']=self.table_speed
        return message
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
            if not self.game or identity not in self.humans:return False
            seat=self.humans[identity]
            if not self.game.hand_complete and seat in self.game.hand_seat_indexes:return False
            stack=self.game.player_stack if seat==0 else self.game.npc_stacks[seat-1]
            if stack>0:return False
            if seat==0:self.game.player_stack=self.starting_stack;self.game.player_busted=False
            else:self.game.npc_stacks[seat-1]=self.starting_stack;self.game.npc_busted[seat-1]=False
            self.chips_added+=self.starting_stack;self.ready.discard(identity);self.revision+=1
            self.table_notices.append(f'{self.names[seat]} bought back in for ${self.starting_stack:,}.')
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
                if g.current_bet and not g.can_npc_raise(i):return False
                ok=g.npc_raise(i,amount) if g.current_bet else g.npc_bet(i,amount)
            else:return False
        if ok:
            if not g.hand_complete and (seat or action=='fold'):g.advance_to_next_actor()
            self.revision+=1;self.due=0
        return ok
    def next_if_ready(self):
        if self.game and self.game.hand_complete and self.required()<=self.ready:
            self.replace_busted_npcs()
            self.boundary()
            if sum(s>0 for s in [self.game.player_stack,*self.game.npc_stacks])>1:
                self.game.sitting_out={self.humans[i] for i in self.sit_out if i in self.humans}
                if len(self.game.get_live_player_indexes())<2:return
                self.ready.clear();self.new_seats.clear();self.game.start_hand();self.revision+=1;self.due=0;self.resume_at=None
    def replace_busted_npcs(self):
        occupied=set(self.humans.values())
        for seat in range(1,6):
            if seat in occupied or self.game.npc_stacks[seat-1]>0:continue
            used={n['id'] for n in self.npcs}
            choices=[n for n in self.roster if n['id'] not in used]
            if not choices:choices=[n for n in self.roster if n['id']!=self.npcs[seat-1]['id']]
            replacement=copy.deepcopy(random.choice(choices))
            old=self.names[seat];self.npcs[seat-1]=replacement;self.names[seat]=replacement['name']
            self.game.npcs[seat-1]=copy.deepcopy(replacement)
            self.game.npc_stacks[seat-1]=self.starting_stack;self.game.npc_busted[seat-1]=False
            self.chips_added+=self.starting_stack
            self.table_notices.append(f'{replacement["name"]} replaces {old} with ${self.starting_stack:,}.')
    def set_speed(self,speed):
        if speed not in ('slow','normal','fast') or speed==self.table_speed:return
        old=self.table_speed;self.table_speed=speed;ui.holdem_table_speed=speed
        self.table_notices.append(f'Host has set table speed from {old.title()} to {speed.title()}.');self.revision+=1
    def update(self, now):
        g=self.game
        if not g:return
        if g.hand_complete:
            if self.waiting or self.departed:self.boundary();self.revision+=1
            if self.completed_hand!=g.hand_number:
                self.completed_hand=g.hand_number
                self.resume_at=now+{'slow':10000,'normal':7000,'fast':4500}.get(self.table_speed,7000)
            if self.resume_at is not None and now>=self.resume_at:self.ready.update(self.required())
            self.next_if_ready();return
        complete=g.is_betting_round_complete()
        seat=g.current_actor
        controlling=next((identity for identity,s in self.humans.items() if s==seat),None)
        if not complete and controlling in self.connections:self.due=0;return
        if not self.due:self.due=now+(ui.get_holdem_street_delay() if complete else ui.get_holdem_npc_delay());return
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
