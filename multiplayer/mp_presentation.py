"""Local card/chip motion; authoritative game values are never delayed or edited."""
import math
import pygame

POSITIONS=[(525,668),(85,400),(335,200),(658,140),(992,200),(1055,425)]
BET_POINTS=[(790,557),(325,437),(481,318),(605,235),(955,325),(1010,507)]


class Presentation:
    def __init__(self,appearance,options=None,sound=None):
        self.appearance=appearance;self.options=options;self.sound=sound or (lambda key:None)
        self.hand=None;self.previous_bets=[0]*6;self.community=0;self.complete=False;self.starts={};self.flights=[]

    @property
    def enabled(self):return self.options is None or self.options.values['animations']

    @property
    def scale(self):
        return {'slow':1.6,'normal':1,'fast':.55}.get(self.options.values['motion'],1) if self.options else 1

    def update(self,game,now):
        bets=[game.player_round_bet,*game.npc_round_bets]
        if self.hand!=game.hand_number:
            self.hand=game.hand_number;self.starts={('seat',i,j):now+i*65+j*90 for i in range(6) for j in range(2)}
            self.previous_bets=[0]*6;self.community=0;self.complete=False;self.flights=[]
            self.sound('card_move')
        for i,(old,new) in enumerate(zip(self.previous_bets,bets)):
            if new>old:self.flights.append((now,POSITIONS[i],BET_POINTS[i]));self.sound('chip_move')
            elif old and new<old:self.flights.append((now,BET_POINTS[i],(805,310)))
        for i in range(self.community,len(game.community_cards)):
            self.starts[('board',i)]=now+(i-self.community)*120
        if len(game.community_cards)>self.community:self.sound('card_move')
        if game.hand_complete and not self.complete:
            for i,amount in enumerate(bets):
                if amount:self.flights.append((now,BET_POINTS[i],(805,310)))
            for i in game.winner_indexes:self.flights.append((now+350,(805,310),POSITIONS[i]))
            self.sound('win')
        self.previous_bets=list(bets);self.community=len(game.community_cards);self.complete=game.hand_complete
        self.flights=[f for f in self.flights if now-f[0]<650*self.scale]

    def card_position(self,key,x,y,w,h,now):
        if not self.enabled or key not in self.starts:return x,y,w,h,False
        progress=max(0,min(1,(now-self.starts[key])/(430*self.scale)))
        if progress>=1:return x,y,w,h,False
        ease=1-(1-progress)**3
        return round(685+(x-685)*ease),round(327+(y-327)*ease),max(2,round(w*abs(1-2*progress))),h,progress<.5

    def chip(self,surface,point,count=1):
        image=self.appearance.image('assets/poker/chip_green.png',(25,25))
        for j in range(min(5,count)):
            x,y=point[0]+j*10,point[1]-j*3
            if image:surface.blit(image,(x,y))
            else:
                pygame.draw.circle(surface,(75,151,86),(round(x+12),round(y+12)),12)
                pygame.draw.circle(surface,(243,232,201),(round(x+12),round(y+12)),10,2)

    def draw(self,surface,game,now,font):
        for i,amount in enumerate([game.player_round_bet,*game.npc_round_bets]):
            if amount and not game.hand_complete:
                self.chip(surface,BET_POINTS[i],1+int(math.log10(max(1,amount))))
                label=font.render(f'${amount:,}',True,(251,241,206));surface.blit(label,(BET_POINTS[i][0],BET_POINTS[i][1]+27))
        self.chip(surface,(805,306),3 if game.pot or game.last_resolved_pot else 1)
        if self.enabled:
            for start,origin,target in self.flights:
                t=max(0,min(1,(now-start)/(650*self.scale)));t=t*t*(3-2*t)
                self.chip(surface,(origin[0]+(target[0]-origin[0])*t,origin[1]+(target[1]-origin[1])*t),2)
