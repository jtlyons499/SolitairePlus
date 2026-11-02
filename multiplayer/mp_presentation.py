"""Client-local Hold'em presentation.

The room authority owns every poker value.  This module is deliberately limited
 to animation, sound edges, and cosmetic chip/card movement so multiplayer can
feel like the single-player table without delaying or mutating network state.
"""
import math
import random
import pygame

POSITIONS=[(525,668),(85,400),(335,200),(658,140),(992,200),(1055,425)]
BET_POINTS=[(790,557),(325,437),(481,318),(605,235),(955,325),(1010,507)]
CHIP_ASSETS=(
    'assets/poker/chip_blue.png',
    'assets/poker/chip_green.png',
    'assets/poker/chip_red.png',
    'assets/poker/chip_yellow.png',
    'assets/poker/chip_black.png',
)


class Presentation:
    def __init__(self,appearance,options=None,sound=None):
        self.appearance=appearance;self.options=options;self.sound=sound or (lambda key:None)
        self.hand=None;self.previous_bets=[0]*6;self.previous_actions=['']*6
        self.previous_folded=[False]*6;self.community=0;self.stage=None;self.complete=False
        self.starts={};self.flights=[];self.win_sound_at=0;self.win_sound_hand=None

    @property
    def enabled(self):return self.options is None or self.options.values['animations']

    @property
    def scale(self):
        return {'slow':1.6,'normal':1,'fast':.55}.get(self.options.values['motion'],1) if self.options else 1

    def _chip_sound(self):
        self.sound(random.choice(('chips_1','chips_2','chips_3')))

    @staticmethod
    def _action_sound_kind(text):
        text=(text or '').strip().lower()
        if text.startswith('checked'):return 'check'
        if text.startswith(('called','bet','raised','all in')):return 'chips'
        if text.startswith('folded'):return 'fold'
        return None

    def update(self,game,now):
        bets=[game.player_round_bet,*game.npc_round_bets]
        actions=[game.player_action_text,*game.npc_action_texts]
        folded=[game.player_folded,*game.npc_folded]

        if self.hand!=game.hand_number:
            self.hand=game.hand_number
            self.starts={('seat',i,j):now+i*65+j*90 for i in range(6) for j in range(2)}
            self.previous_bets=[0]*6;self.previous_actions=['']*6;self.previous_folded=[False]*6
            self.community=0;self.stage=game.current_stage;self.complete=False;self.flights=[]
            self.win_sound_at=0;self.win_sound_hand=None
            # Match single-player: one clear card sound at the beginning of a hand.
            self.sound('card_draw')

        if self.stage is not None and game.current_stage!=self.stage:
            # A repeated action word (for example Checked on two streets) is a
            # new event after the betting round changes.
            self.previous_actions=['']*6

        action_chip_seats=set();chip_sound_played=False
        for i,(old,new) in enumerate(zip(self.previous_actions,actions)):
            if not new or new==old:continue
            kind=self._action_sound_kind(new)
            if kind=='check':self.sound('check')
            elif kind=='chips':
                if not chip_sound_played:self._chip_sound();chip_sound_played=True
                action_chip_seats.add(i)
            elif kind=='fold':self.sound('card_move')

        # Animate money moving to the betting points.  Blinds/antes still make
        # a chip sound even though they do not produce an action-text edge.
        for i,(old,new) in enumerate(zip(self.previous_bets,bets)):
            if new>old:
                self.flights.append((now,POSITIONS[i],BET_POINTS[i],max(1,new-old)))
                if i not in action_chip_seats and not chip_sound_played:self._chip_sound();chip_sound_played=True
            elif old and new<old:
                self.flights.append((now,BET_POINTS[i],(805,310),max(1,old)))

        # Every newly revealed street uses the same card-draw cue as the
        # single-player Hold'em table.  Showdown adds the face-up flip cue.
        new_cards=len(game.community_cards)-self.community
        if new_cards>0:
            for i in range(self.community,len(game.community_cards)):
                self.starts[('board',i)]=now+(i-self.community)*120
            self.sound('card_draw')

        if game.hand_complete and not self.complete:
            for i,amount in enumerate(bets):
                if amount:self.flights.append((now,BET_POINTS[i],(805,310),max(1,amount)))
            for i in game.winner_indexes:self.flights.append((now+350,(805,310),POSITIONS[i],max(1,getattr(game,'last_resolved_pot',1))))
            self.sound('card_flip')
            if 0 in game.winner_indexes:
                self.win_sound_at=now+450;self.win_sound_hand=game.hand_number
            else:
                if not chip_sound_played:self._chip_sound();chip_sound_played=True

        if self.win_sound_at and now>=self.win_sound_at and self.win_sound_hand==game.hand_number:
            self.sound('hand_win');self.win_sound_at=0

        self.previous_bets=list(bets);self.previous_actions=list(actions);self.previous_folded=list(folded)
        self.community=len(game.community_cards);self.stage=game.current_stage;self.complete=game.hand_complete
        self.flights=[f for f in self.flights if now-f[0]<650*self.scale]

    def card_position(self,key,x,y,w,h,now):
        if not self.enabled or key not in self.starts:return x,y,w,h,False
        progress=max(0,min(1,(now-self.starts[key])/(430*self.scale)))
        if progress>=1:return x,y,w,h,False
        ease=1-(1-progress)**3
        return round(685+(x-685)*ease),round(327+(y-327)*ease),max(2,round(w*abs(1-2*progress))),h,progress<.5

    def chip(self,surface,point,count=1,amount=0):
        # Give large wagers a visibly richer stack instead of five identical
        # green chips.  This is cosmetic only; authoritative amounts are text.
        level=min(len(CHIP_ASSETS)-1,max(0,int(math.log10(max(1,amount))) if amount else count-1))
        for j in range(min(6,max(1,count))):
            asset=CHIP_ASSETS[max(0,level-j//2)]
            image=self.appearance.image(asset,(25,25)) if self.appearance else None
            x,y=point[0]+j*9,point[1]-j*4
            if image:surface.blit(image,(x,y))
            else:
                pygame.draw.circle(surface,(75,151,86),(round(x+12),round(y+12)),12)
                pygame.draw.circle(surface,(243,232,201),(round(x+12),round(y+12)),10,2)

    def draw(self,surface,game,now,font):
        for i,amount in enumerate([game.player_round_bet,*game.npc_round_bets]):
            if amount and not game.hand_complete:
                self.chip(surface,BET_POINTS[i],1+int(math.log10(max(1,amount))),amount)
                label=font.render(f'${amount:,}',True,(251,241,206))
                shadow=font.render(f'${amount:,}',True,(0,0,0))
                surface.blit(shadow,(BET_POINTS[i][0]+1,BET_POINTS[i][1]+28))
                surface.blit(label,(BET_POINTS[i][0],BET_POINTS[i][1]+27))
        pot_amount=game.pot if not game.hand_complete else game.last_resolved_pot
        if pot_amount:
            self.chip(surface,(805,306),3+min(3,int(math.log10(max(1,pot_amount)))),pot_amount)
        if self.enabled:
            for start,origin,target,amount in self.flights:
                t=max(0,min(1,(now-start)/(650*self.scale)));t=t*t*(3-2*t)
                self.chip(surface,(origin[0]+(target[0]-origin[0])*t,origin[1]+(target[1]-origin[1])*t),2,amount)
