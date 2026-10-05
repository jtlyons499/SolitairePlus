"""Lightweight chip movement driven by committed wagers and actual payouts."""
from weakref import WeakKeyDictionary
import pygame

_EFFECTS = WeakKeyDictionary()
POT = (683, 326)
SEATS = ((800, 560), (430, 320), (803, 290), (1176, 320))


def chip(surface, center, color=(220,181,77), radius=10):
    x,y=map(round,center)
    pygame.draw.circle(surface,(14,20,20),(x+2,y+3),radius)
    pygame.draw.circle(surface,color,(x,y),radius)
    pygame.draw.circle(surface,(247,236,197),(x,y),radius,2)
    for dx,dy in ((0,-radius),(radius,0),(0,radius),(-radius,0)):
        pygame.draw.line(surface,(245,236,213),(x+dx*.6,y+dy*.6),(x+dx*.9,y+dy*.9),2)


class BluffEffects:
    def __init__(self):
        self.hand = None
        self.motions = []
        self.sounds = []

    def update(self,game,now):
        if self.hand != game.hand_number:
            self.hand=game.hand_number;self.motions.clear();self.sounds.clear()
        events=getattr(game,'presentation_events',None)
        while events:
            event=events.popleft()
            if event['kind'] in ('wager','payout') and event['amount']>0:
                scheduled = now
                if event['kind'] == 'payout':
                    scheduled = max(now, max((start + 550 for start, prior in self.motions if prior['kind'] == 'wager'), default=now))
                self.motions.append((scheduled,event))
                # Player input already has its own SFX; add feedback for NPC
                # decisions and for the actual payout, without duplicate sounds.
                if event['kind']=='payout':self.sounds.append('poker_hand_win' if event['seat']==0 else 'poker_chips_1')
                elif event['seat']>0:self.sounds.append('poker_chips_1')
            elif event['kind'] in ('check','fold') and event['seat']>0:
                self.sounds.append('poker_check' if event['kind']=='check' else 'card_move')
        self.motions=[m for m in self.motions if now-m[0]<1000]


def effects_for(game):
    if game not in _EFFECTS:_EFFECTS[game]=BluffEffects()
    return _EFFECTS[game]


def update_bluff_presentation(game,play_sound,now=None):
    fx=effects_for(game);fx.update(game,pygame.time.get_ticks() if now is None else now)
    for sound in dict.fromkeys(fx.sounds):play_sound(sound)
    fx.sounds.clear()


def draw_bluff_effects(surface,game,now=None):
    now=pygame.time.get_ticks() if now is None else now
    fx=effects_for(game);fx.update(game,now)
    if game.pot:
        for i in range(min(7,max(1,len(str(game.pot))))):chip(surface,(POT[0]+(i%3-1)*23,POT[1]-(i//3)*7))
    font=pygame.font.Font(None,27)
    for start,event in fx.motions:
        age=now-start
        if age < 0:
            continue
        seat=SEATS[min(event['seat'],len(SEATS)-1)]
        source,target=(seat,POT) if event['kind']=='wager' else (POT,seat)
        t=min(1,age/520);t=1-(1-t)**3
        if age<600:
            for i in range(3):
                x=source[0]+(target[0]-source[0])*t+i*8
                y=source[1]+(target[1]-source[1])*t-i*6
                chip(surface,(x,y),(91,180,119) if event['kind']=='payout' else (220,181,77))
        sign='+' if event['kind']=='payout' else '−'
        text=font.render(f"{sign}${event['amount']:,}",True,(239,220,149))
        text.set_alpha(max(0,min(255,round((1000-age)*255/500))))
        surface.blit(text,text.get_rect(center=(seat[0],seat[1]-30-age*.025)))
