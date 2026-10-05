"""Timed encounter feedback. Rules stay in CryptidBattle; snapshots stay visual."""
from array import array
import copy
import math
from pathlib import Path
import random
import pygame

from cryptid_creatures import ROOT


def snapshot(battle):
    return copy.deepcopy(battle.sides)


class BattleFeedback:
    def __init__(self):
        self.before = self.after = None
        self.started = 0
        self.duration = 0
        self.kind = ""
        self.style = "Slam"
        self.seat = 0
        self.message = "Choose your move."
        self.changes = []
        self.knockouts = []
        self.sound_played = False
        self.active = False
        self.healing = False
        self.shielding = False

    def start(self, before, battle, action, seat, now):
        self.before, self.after = before, snapshot(battle)
        self.started, self.seat = now, seat
        self.kind = action.kind
        self.style = "Slam"
        self.changes, self.knockouts = [], []
        previous={c.uid:c for side in before for c in side.creatures()}
        self.healing=any(c.uid in previous and (c.hp>previous[c.uid].hp or c.ap>previous[c.uid].ap)
                         for side in self.after for c in side.creatures())
        self.shielding=any(c.guard and c.uid in previous and c.guard!=previous[c.uid].guard
                           for side in self.after for c in side.creatures())
        for index in (0,1):
            old, new = before[index].active, self.after[index].active
            if old and (new is None or old.uid == new.uid):
                hp, ap = (new.hp,new.ap) if new else (0, max(0,old.ap))
                if new is None:
                    self.knockouts.append(index)
                    # The last hit gives the actual armor left on a knocked-out card.
                    hit=battle.last_hit
                    if action.kind in ('move','struggle') and hit and hit.get('seat')==1-index:
                        ap=max(0,old.ap-hit['ap_loss'])
                if hp!=old.hp or ap!=old.ap:
                    self.changes.append((index,hp-old.hp,ap-old.ap))
        actor=before[seat].active
        if action.kind in ('move','struggle') and actor:
            move=(battle.catalog.moves['struggle'] if action.kind=='struggle' else
                  battle.catalog.moves[battle.card(actor.card_id)['moves'][action.index]])
            self.kind=move['kind']
            self.style=move.get('style','Ethereal')
            name=battle.card(actor.card_id)['name']
            self.message=f"{name} used {move['name']}!"
            if self.kind=='attack' and battle.last_hit:
                hit=battle.last_hit
                self.message+=f" {hit['ap_loss']} armor / {hit['hp_loss']} HP."
                reason=hit['steps'][1]
                if 'x0.5' in reason:self.message+=' Resisted!'
                elif 'x2' in reason:self.message+=' Super effective!'
        elif action.kind=='play':
            card=battle.card(before[seat].hand[action.index])
            self.kind='deploy' if card['kind']=='creature' else 'arena' if card['kind']=='arena' else 'support'
            self.message=('You played ' if seat==0 else 'Opponent played ')+card['name']+'.'
            for creature in self.after[seat].creatures():
                old=previous.get(creature.uid)
                if old and (creature.hp>old.hp or creature.ap>old.ap):
                    self.message+=f" {battle.card(creature.card_id)['name']} +{max(0,creature.hp-old.hp)} HP / +{max(0,creature.ap-old.ap)} armor."
        elif action.kind in ('switch','promote'):
            new=self.after[seat].active
            self.kind='switch'
            self.message=('You sent out ' if seat==0 else 'Opponent sent out ')+battle.card(new.card_id)['name']+'!'
        elif action.kind=='end':
            self.kind='status' if self.changes else 'turn'
            self.message=('Your turn.' if battle.turn==0 else 'Opponent’s turn.')
            if self.changes:self.message+=' '+battle.log[-1]
        elif action.kind=='discard':
            self.message='Card discarded.'
        self.duration=(850 if self.kind=='attack' else 580 if self.kind in ('switch','arena','guard','repair','support','deploy','status') else 160)
        if self.knockouts:self.duration+=320
        self.sound_played=False
        self.active=True

    def elapsed(self, now):
        return max(0,now-self.started)

    def advance(self, now, sound):
        if not self.active:return
        if not self.sound_played and self.elapsed(now)>=180 and self.kind not in ('turn','discard'):
            sound.play('attack_'+self.style.lower() if self.kind=='attack' else
                       'heal' if self.healing else
                       'shield' if self.shielding or self.kind=='guard' else self.kind)
            self.sound_played=True
        if self.elapsed(now)>=self.duration:
            if self.knockouts:sound.play('knockout')
            self.active=False

    def visual_sides(self, battle, now):
        if not self.active:return battle.sides
        sides=copy.deepcopy(self.after)
        progress=min(1,max(0,(self.elapsed(now)-240)/400))
        for seat in (0,1):
            old,new=self.before[seat].active,self.after[seat].active
            if self.kind=='switch' and seat==self.seat and self.elapsed(now)<230:
                sides[seat]=copy.deepcopy(self.before[seat])
                continue
            if old and (new is None or old.uid==new.uid):
                shown=copy.deepcopy(new or old)
                change=next(((h,a) for s,h,a in self.changes if s==seat),(0,0))
                shown.hp=round(old.hp+change[0]*progress)
                shown.ap=round(old.ap+change[1]*progress)
                sides[seat].active=shown
            elif old and self.kind=='switch' and self.elapsed(now)<230:
                sides[seat].active=copy.deepcopy(old)
            previous={c.uid:c for c in self.before[seat].creatures()}
            for creature in sides[seat].docket:
                old_creature=previous.get(creature.uid)
                if old_creature:
                    creature.hp=round(old_creature.hp+(creature.hp-old_creature.hp)*progress)
                    creature.ap=round(old_creature.ap+(creature.ap-old_creature.ap)*progress)
            if seat in self.knockouts and self.elapsed(now)<680:
                sides[1-seat].knockouts=self.before[1-seat].knockouts
        return sides

    def offset(self,seat,now):
        if not self.active:return (0,0)
        t=self.elapsed(now)
        if self.kind=='attack':
            if seat==self.seat and t<240:
                return (round((1 if seat==1 else -1)*16*math.sin(t/240*math.pi)),0)
            if seat!=self.seat and 220<t<430:
                return (round(6*math.sin(t*.12)),round(3*math.cos(t*.15)))
        return (0,0)

    def draw(self,surface,rects,now,font,colors):
        if not self.active:return
        t=self.elapsed(now)
        target=rects[1-self.seat]
        color=colors.get(self.style,(236,184,79))
        layer=pygame.Surface(surface.get_size(),pygame.SRCALPHA)
        if self.kind=='attack' and 80<t<420:
            start,end=rects[self.seat].center,target.center
            p=min(1,max(0,(t-80)/170))
            center=(round(start[0]+(end[0]-start[0])*p),round(start[1]+(end[1]-start[1])*p))
            if self.style=='Slash':
                for shift in (-16,0,16):pygame.draw.line(layer,(*color,220),(center[0]-30+shift,center[1]+40),(center[0]+30+shift,center[1]-40),5)
            elif self.style=='Air':
                for size in (20,36,52):pygame.draw.circle(layer,(*color,180),center,size,3)
            else:
                pygame.draw.circle(layer,(*color,75),center,34)
                pygame.draw.circle(layer,(*color,245),center,16 if self.style=='Munition' else 24)
                pygame.draw.circle(layer,(255,245,210,240),center,8)
            if t>220:
                fade=max(0,1-(t-220)/220)
                pygame.draw.rect(layer,(255,235,184,round(110*fade)),target,border_radius=16)
                for i in range(10):
                    angle=i*math.tau/10
                    radius=18+(t-220)*.25
                    point=(round(target.centerx+math.cos(angle)*radius),round(target.centery+math.sin(angle)*radius))
                    pygame.draw.circle(layer,(*color,round(230*fade)),point,5)
        if self.kind in ('guard','support','repair','status') and 160<t<560:
            for seat,hp,ap in self.changes or [(self.seat,0,0)]:
                rect=rects[seat];positive=hp>0 or ap>0
                tint=(88,232,145) if positive else (102,173,251) if self.kind=='guard' else (193,136,239)
                pygame.draw.rect(layer,(*tint,130),rect.inflate(8,8),4,border_radius=16)
                for i in range(7):
                    y=rect.bottom-round((t-160)*.5+i*29)%rect.h
                    x=rect.x+20+(i*37)%(rect.w-40)
                    pygame.draw.line(layer,(*tint,200),(x-5,y),(x+5,y),3)
                    pygame.draw.line(layer,(*tint,200),(x,y-5),(x,y+5),3)
        if self.kind=='arena' and 120<t<500:
            pygame.draw.rect(layer,(153,122,224,90),surface.get_rect(),12)
        if self.kind in ('switch','deploy') and t<530:
            rect=rects[self.seat]
            fade=max(0,1-t/530)
            for radius in (round(20+t*.2),round(30+t*.28)):
                pygame.draw.circle(layer,(117,223,234,round(200*fade)),rect.center,radius,5)
            if 150<t<270:
                pygame.draw.rect(layer,(151,241,255,round(160*math.sin((t-150)/120*math.pi))),rect,border_radius=12)
        for seat,hp,ap in self.changes:
            if t<240:continue
            rect=rects[seat]
            pieces=[]
            if ap:pieces.append(f"{'+' if ap>0 else ''}{ap} ARMOR")
            if hp:pieces.append(f"{'+' if hp>0 else ''}{hp} HP")
            text=font(35,True).render(' / '.join(pieces),True,(104,252,164) if hp>0 or ap>0 else (255,219,151))
            pos=text.get_rect(center=(rect.centerx,rect.centery-round(min(t-240,450)*.07)))
            pygame.draw.rect(layer,(16,25,34,235),pos.inflate(18,12),border_radius=8)
            layer.blit(text,pos)
        for seat in self.knockouts:
            if t<680:continue
            rect=rects[seat]
            pygame.draw.rect(layer,(13,20,29,min(200,round((t-680)*.6))),rect,border_radius=12)
            text=font(40,True).render('KNOCKOUT',True,(255,185,103))
            layer.blit(text,text.get_rect(center=rect.center))
        surface.blit(layer,(0,0))


class BattleSounds:
    """Artist supplied WAV overrides; otherwise short purpose-built synth cues."""
    def __init__(self):
        self.volume=.6
        self.cache={}
        self.channel=None

    def play(self,key):
        if self.volume<=0 or not pygame.mixer.get_init():return
        try:
            if key not in self.cache:
                path=ROOT/'assets'/'cryptid_creatures'/'sfx'/(key+'.wav')
                if path.is_file():sound=pygame.mixer.Sound(str(path))
                else:
                    rate,fmt,channels=pygame.mixer.get_init()
                    if fmt!=-16:return
                    duration=.24 if key.startswith('attack') else .42 if key=='knockout' else .2
                    samples=array('h');rng=random.Random(key)
                    for i in range(round(rate*duration)):
                        t=i/rate;p=t/duration
                        if key.startswith('attack'):
                            f=440 if key.endswith('air') else 780 if key.endswith('munition') else 210
                            wave=.55*math.sin(math.tau*(f*t-170*t*t))+.45*rng.uniform(-1,1)
                        elif key=='heal':wave=math.sin(math.tau*(480*t+650*t*t))*.65
                        elif key=='knockout':wave=math.sin(math.tau*(240*t-180*t*t))*.7
                        elif key=='shield':wave=(math.sin(math.tau*620*t)+math.sin(math.tau*930*t))*.35
                        else:wave=math.sin(math.tau*(350*t+200*t*t))*.5
                        value=round(8500*wave*(1-p)**2*min(1,t/.008))
                        for _ in range(channels):samples.append(value)
                    sound=pygame.mixer.Sound(buffer=samples.tobytes())
                self.cache[key]=sound
            if self.channel is None or self.channel.get_busy():
                self.channel=pygame.mixer.find_channel()
            if self.channel:
                self.channel.set_volume(max(0,min(1,self.volume)))
                self.channel.play(self.cache[key])
        except (pygame.error,OSError,ValueError):
            pass
