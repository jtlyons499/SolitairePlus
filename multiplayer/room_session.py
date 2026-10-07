"""Main-thread room coordinator; relay routes only explicitly targeted views."""
import queue
import uuid
from mp_profile import clean_public, winning_xp
from lan_protocol import ClientGame
from lan_session import clean_name
from relay_transport import RelayPeer
from room_table import RoomAuthority

class RoomTable:
    def __init__(self,name,hosting,address,code='',profile=None):
        if profile:profile.data['name']=clean_name(name)
        self.profile=profile;self.public_profiles={};self.session_id=str(uuid.uuid4());self.reward_hand=0;self.participants={};self.awards={};self.profile_sent=False;self.public_log=[];self.log_hand=0;self.log_actions=[];self.log_stage=None;self.notices_seen=0;self.last_payout=None
        if profile:self.public_profiles[0]=profile.public() if hosting else {}
        self.name=clean_name(name);self.hosting=hosting;self.identity=0 if hosting else None
        self.peer=RelayPeer(hosting,address,self.name,code,version=2)
        self.authority=RoomAuthority(self.name) if hosting else None
        self.game=ClientGame();self.message={'type':'connecting'};self.status='Connecting to relay…';self.failed=False;self.last_sent=-1;self.pending=False
    @property
    def code(self):return self.peer.code
    def close(self):self.peer.close()
    def update(self,now):
        while True:
            try:m=self.peer.inbox.get_nowait()
            except queue.Empty:break
            kind=m.get('type')
            if kind=='disconnected':self.failed=True;self.status=m.get('text','Disconnected')
            elif kind=='status':self.status=m.get('text','Connecting')
            elif kind in ('room','joined'):
                self.identity=m['identity'];self.peer.code=m['code'];self.last_sent=-1
                if self.profile and not self.hosting:self.peer.send({'type':'action','action':'profile','profile':self.profile.public()})
            elif kind=='peer_joined' and self.hosting:
                self.authority.join(m['identity'],clean_name(m['name']));self.last_sent=-1
                for owner,value in self.public_profiles.items():self.send_profile(owner,value,[m['identity']])
            elif kind=='peer_left' and self.hosting:self.authority.leave(m['identity']);self.last_sent=-1
            elif kind in ('lobby','state','waiting') and not self.hosting:self.apply(m)
            elif kind=='action' and self.hosting:
                who=m.get('sender')
                if m.get('action')=='profile':
                    value=clean_public(m.get('profile'))
                    if value and who in self.authority.connections:
                        self.public_profiles[who]=value;self.send_profile(who,value)
                    continue
                self.collect_awards()
                ok=self.authority.act(who,m.get('action'),m.get('amount',0),m.get('revision'))
                self.collect_awards()
                self.peer.send({'type':'ack','target':who,'ok':ok});self.last_sent=-1
            elif kind=='ack' and 'public_profile' in m:
                value=clean_public(m['public_profile'])
                if value:self.public_profiles[m['owner']]=value
            elif kind=='ack':
                self.pending=False
                if not m.get('ok'):self.status='Table changed; try again after the next update'
        if self.hosting and not self.failed and self.code:
            self.collect_awards();self.authority.update(now);self.collect_awards();self.apply(self.view(0))
            if self.code and self.last_sent!=self.authority.revision:
                sent=True
                for identity in self.authority.connections:
                    if identity:
                        m=self.view(identity);m['target']=identity
                        sent=self.peer.send(m) and sent
                if sent:self.last_sent=self.authority.revision
    def apply(self,m):
        self.message=m;self.pending=False
        if self.profile:
            previous=self.profile.data['xp']
            for award in m.get('xp_awards',[]):self.profile.award(award)
            if previous!=self.profile.data['xp']:self.refresh_profile()
        if m['type']=='state':
            self.game.apply(m)
            if self.game.hand_complete:
                import copy
                from types import SimpleNamespace
                self.last_payout=SimpleNamespace(**copy.deepcopy(dict(names=self.game.names,last_pot_awards=self.game.last_pot_awards,result_text=self.game.result_text,showdown_hands=self.game.showdown_hands,hand_number=self.game.hand_number)))
            self.status='Your turn' if self.game.current_actor==0 else 'Waiting for other seats'
        elif m['type']=='lobby':self.status='Host selects NPCs and starts the table'
        else:self.status=m.get('text','Waiting for next hand')
    def act(self,action,amount=0):
        if self.failed or self.pending:return False
        revision=self.message.get('revision',0)
        if self.hosting:
            self.collect_awards()
            ok=self.authority.act(0,action,amount,revision)
            self.collect_awards()
            if ok:self.last_sent=-1
        else:
            ok=self.peer.send({'type':'action','action':action,'amount':amount,'revision':revision});self.pending=ok
        return ok

    def send_profile(self, owner, value, recipients=None):
        recipients=self.authority.connections if recipients is None else recipients
        for target in recipients:
            if target:self.peer.send({'type':'ack','target':target,'owner':owner,'public_profile':value})

    def refresh_profile(self):
        if not self.profile:return
        if self.hosting:
            self.public_profiles[0]=self.profile.public();self.send_profile(0,self.profile.public())
        elif self.identity is not None:
            self.peer.send({'type':'action','action':'profile','profile':self.profile.public()})

    def collect_awards(self):
        g=self.authority.game
        if not g:return
        if getattr(self,'tracked_hand',None)!=g.hand_number:
            self.tracked_hand=g.hand_number;self.participants=dict(self.authority.humans)
        if not g.hand_complete or self.reward_hand==g.hand_number:return
        self.reward_hand=g.hand_number
        for identity,xp in winning_xp(g,self.participants,self.participants).items():
            self.awards.setdefault(identity,[]).append({'id':f'{self.session_id}:{g.hand_number}','xp':xp})
            self.awards[identity]=self.awards[identity][-200:]
        self.last_sent=-1

    def view(self,identity):
        for notice in self.authority.table_notices[self.notices_seen:]:self.public_log.append(notice)
        self.notices_seen=len(self.authority.table_notices)
        self.collect_log()
        message=self.authority.view(identity)
        message['public_log']=self.public_log[-100:]
        message['chips_added']=self.authority.chips_added
        message['xp_awards']=self.awards.get(identity,[])
        for owner,seat in self.authority.humans.items():message['seats'][seat]['identity']=owner
        return message

    def collect_log(self):
        g=self.authority.game
        if not g:return
        if self.log_hand!=g.hand_number:
            self.log_hand=g.hand_number;self.log_actions=['']*6;self.log_stage=None
            self.public_log.append(f'Hand {g.hand_number} • Blinds ${g.small_blind}/${g.big_blind}')
        if self.log_stage!=g.current_stage:
            self.log_stage=g.current_stage
            if g.community_cards:
                from texas_holdem_ui import get_card_key
                self.public_log.append(g.current_stage.title()+': '+' '.join(get_card_key(c) for c in g.community_cards))
        actions=[g.player_action_text,*g.npc_action_texts]
        for i,action in enumerate(actions):
            if action and action!=self.log_actions[i]:self.public_log.append(f'{self.authority.names[i]}: {action}')
        self.log_actions=list(actions);self.public_log=self.public_log[-100:]
