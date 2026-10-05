"""Career collection, three owned-card deck slots and saved pack reveals."""
from collections import Counter
import math
import pygame
from cryptid_collection import deck_errors, open_pack, save_deck, transaction

GOLD=(241,196,101)
TEXT=(242,237,218)
MUTED=(179,198,194)
PANEL=(27,46,49)


class CryptidCollectionView:
    def __init__(self,screen,state,persist):
        self.screen,self.state,self.persist=screen,state,persist
        self.page_index=0
        self.filter='all'
        self.search=''
        self.slot=state['active_deck']
        self.draft=list(state['decks'][self.slot]['cards'])
        self.deck_scroll=0
        self.clock=0
        self.last_update=None
        self.opening_started=0
        self.revealed=0
        self.message=''

    def update(self,now,paused=False):
        delta=0 if self.last_update is None else max(0,now-self.last_update)
        self.last_update=now
        if paused:return
        self.clock+=delta
        if self.screen.page=='pack_open':
            elapsed=self.clock-self.opening_started
            count=min(5,max(0,int((elapsed-650)/330)+1)) if elapsed>=650 else 0
            if count>self.revealed:
                self.screen.sounds.volume=self.screen.sfx_volume
                self.screen.sounds.play('heal' if count==5 else 'switch')
            self.revealed=count

    def _commit(self,operation):
        try:
            result=transaction(self.state,operation,self.persist)
            self.message=''
            return True,result
        except (OSError,ValueError) as error:
            self.message='Could not save: '+str(error) if isinstance(error,OSError) else str(error)
            return False,None

    def navigate(self,page):
        self.screen.page=page
        self.page_index=0
        self.message=''
        if page=='builder':
            self.slot=self.state['active_deck']
            self.draft=list(self.state['decks'][self.slot]['cards'])
            self.deck_scroll=0
        if page=='pack_open':
            self.opening_started=self.clock
            self.revealed=0

    def ids(self):
        cards=self.screen.catalog.cards
        return [cid for cid,c in cards.items() if self.search.lower() in c['name'].lower()
                and (self.filter=='all' or self.filter=='owned' and self.state['owned'].get(cid,0)>0
                     or self.filter=='creature' and c['kind']=='creature'
                     or self.filter=='support' and c['kind']!='creature')]

    def draw(self,surface,mouse):
        s=self.screen
        if s.page=='career_home':self._home(surface,mouse)
        elif s.page=='packs':self._packs(surface,mouse)
        elif s.page=='pack_open':self._opening(surface,mouse)
        else:self._cards(surface,mouse,s.page=='builder')
        if self.message:
            pygame.draw.rect(surface,(17,30,33),(28,730,1308,36))
            message=self.message
            font=s.renderer.font(24)
            if font.size(message)[0]>1280:
                while message and font.size(message+'...')[0]>1280:message=message[:-1]
                message+='...'
            s._text(surface,message,35,738,24,GOLD)

    def _home(self,surface,mouse):
        s=self.screen;active=self.state['decks'][self.state['active_deck']]
        s._text(surface,'YOUR CRYPTID COLLECTION',40,88,37,GOLD,True)
        owned=sum(n>0 for n in self.state['owned'].values())
        s._text(surface,f"{owned}/60 cards discovered | {sum(self.state['owned'].values())} copies | {self.state['packs']['creature']} packs waiting",40,136,28,TEXT)
        pygame.draw.rect(surface,PANEL,(40,188,728,402),border_radius=14)
        s._text(surface,'EQUIPPED DECK: '+active['name'],60,208,32,GOLD,True)
        creatures=list(dict.fromkeys(cid for cid in active['cards'] if s.catalog.cards[cid]['kind']=='creature'))
        for i,cid in enumerate(creatures[:4]):s._card(surface,cid,(62+i*174,264,154,216),tag='library')
        s._text(surface,'30 cards | 8 creatures | Maximum 2 of each card',60,509,27,TEXT)
        s._text(surface,f"Career battles {self.state['matches']} | Wins {self.state['wins']} | Draws {self.state['draws']}",60,550,27,MUTED)
        for y,label,command in ((198,'Collection / card library','collection'),(276,'Build / equip deck','builder'),(354,'Open creature packs','packs')):
            s._button(surface,(802,y,520,60),label,('cc_nav',command),mouse,size=31)
        s._button(surface,(802,434,520,54),'Opponent: '+s.npc.get('name','Keeper')+' — Next',('opponent',),mouse,size=27)
        s._button(surface,(802,508,520,60),'Start Career Battle',('start',),mouse,size=32)
        s._button(surface,(40,627,320,52),'Battle Rules',('rules',),mouse,size=28)
        s._wrap(surface,'A win awards one creature pack and 120 XP. A draw awards 70 XP; a loss awards 55 XP. Each level-up adds two creature packs.',390,623,924,27,MUTED)
        footer=('Guest collection is temporary and resets when you change profiles.' if s.temporary_collection else
                'Starter cards are yours. Packs expand your options; deck slots share the same collection.')
        s._text(surface,footer,40,737,25,MUTED)

    def _cards(self,surface,mouse,builder):
        s=self.screen
        s._button(surface,(1080,77,258,42),'Back to Cryptid Hub',('cc_nav','career_home'),mouse,size=25)
        for i,(key,label) in enumerate((('all','All cards'),('owned','Owned'),('creature','Creatures'),('support','Support / Arena'))):
            s._button(surface,(32+i*196,78,184,40),label,('cc_filter',key),mouse,selected=self.filter==key,size=24)
        s._text(surface,'Search (type): '+(self.search or 'all names')+'  | Backspace clears',34,131,25,MUTED)
        ids=self.ids();per_page=8 if builder else 10;columns=4 if builder else 5
        pages=max(1,(len(ids)+per_page-1)//per_page)
        self.page_index=max(0,min(self.page_index,pages-1))
        counts=Counter(self.draft)
        for i,cid in enumerate(ids[self.page_index*per_page:self.page_index*per_page+per_page]):
            x=34+(i%columns)*(214 if builder else 260);y=174+(i//columns)*240
            s._card(surface,cid,(x,y,142,199),tag='library')
            owned=self.state['owned'].get(cid,0)
            s._text(surface,f'Owned {owned}',x,y+201,24,GOLD if owned else MUTED,True)
            if builder:
                n=counts[cid];card=s.catalog.cards[cid]
                creatures=sum(s.catalog.cards[c]['kind']=='creature' for c in self.draft)
                allowed=owned>n and n<2 and len(self.draft)<30 and (card['kind']!='creature' or creatures<8)
                s._button(surface,(x+148,y+14,48,44),'+',('cc_add',cid),mouse,enabled=allowed,size=31)
                s._button(surface,(x+148,y+69,48,44),'-',('cc_remove',cid),mouse,enabled=n>0,size=31)
                s._text(surface,f'{n}/2',x+152,y+126,23,TEXT)
            elif not owned:
                shade=pygame.Surface((142,199),pygame.SRCALPHA);shade.fill((12,20,25,140));surface.blit(shade,(x,y))
        s._button(surface,(34,668,170,42),'Previous',('cc_page',-1),mouse,enabled=self.page_index>0)
        s._text(surface,f'Page {self.page_index+1}/{pages} | Click any card to inspect',226,679,25,MUTED)
        s._button(surface,(690 if builder else 1138,668,170,42),'Next',('cc_page',1),mouse,enabled=self.page_index+1<pages)
        if not ids:s._text(surface,'No cards match this search.',40,280,30,MUTED)
        if builder:self._deck(surface,mouse)

    def _deck(self,surface,mouse):
        s=self.screen
        pygame.draw.rect(surface,PANEL,(904,160,434,548),border_radius=12)
        for i in range(3):s._button(surface,(918+i*138,173,128,38),f'Deck {i+1}',('cc_slot',i),mouse,selected=i==self.slot,size=24)
        creatures=sum(s.catalog.cards[c]['kind']=='creature' for c in self.draft)
        s._text(surface,f'{len(self.draft)}/30 cards | {creatures}/8 creatures',920,227,28,GOLD,True)
        s._text(surface,'Click a row to remove one copy',920,262,23,MUTED)
        counts=Counter(self.draft);rows=list(counts)
        self.deck_scroll=max(0,min(self.deck_scroll,max(0,len(rows)-8)))
        for i,cid in enumerate(rows[self.deck_scroll:self.deck_scroll+8]):
            label=f"{counts[cid]} × {s.catalog.cards[cid]['name']}"
            s._button(surface,(918,298+i*34,404,30),label,('cc_remove',cid),mouse,size=23)
        s._button(surface,(918,577,128,32),'Up',('cc_scroll',-1),mouse,enabled=self.deck_scroll>0,size=22)
        s._button(surface,(1056,577,128,32),'Down',('cc_scroll',1),mouse,enabled=self.deck_scroll+8<len(rows),size=22)
        s._button(surface,(1194,577,128,32),'Clear',('cc_clear',),mouse,size=22)
        errors=deck_errors(self.draft,self.state['owned'],s.catalog)
        s._button(surface,(918,625,404,48),'Save & Equip Deck',('cc_save',),mouse,enabled=not errors,size=29)
        if errors:s._wrap(surface,errors[0],922,676,402,22,MUTED)

    def _pack_shape(self,surface,rect,angle=0):
        rect=pygame.Rect(rect);s=self.screen
        art=s.renderer._image('creature_pack.png')
        if art:
            surface.blit(pygame.transform.smoothscale(art,rect.size),rect)
            return
        pygame.draw.rect(surface,(29,87,93),rect,border_radius=16)
        pygame.draw.rect(surface,GOLD,rect,4,border_radius=16)
        for y in range(rect.y+12,rect.bottom-12,18):
            pygame.draw.line(surface,(48,109,112),(rect.x+8,y),(rect.right-8,y),1)
        pygame.draw.circle(surface,(16,46,53),rect.center,min(rect.w//3,90))
        stamp=s.renderer.font(min(80,rect.w//3),True).render('CC',True,GOLD)
        surface.blit(stamp,stamp.get_rect(center=rect.center))
        label=s.renderer.font(27,True).render('CREATURE PACK',True,TEXT)
        surface.blit(label,label.get_rect(center=(rect.centerx,rect.bottom-50)))

    def _packs(self,surface,mouse):
        s=self.screen
        s._text(surface,'CREATURE PACKS',50,95,40,GOLD,True)
        self._pack_shape(surface,(120,185,300,418))
        s._text(surface,f"Packs available: {self.state['packs']['creature']}",508,185,37,GOLD,True)
        s._wrap(surface,'Five cards per pack: at least three creatures, one support/arena card, and one guaranteed Uncommon. Extra copies stay in your collection; decks allow up to two copies of each card.',508,251,784,30,TEXT)
        s._wrap(surface,'Earn one pack by winning a Career Cryptid battle, and two packs at every new player level. Your two welcome packs are already included.',508,389,784,29,MUTED)
        pending=bool(self.state['pending_reveal'])
        s._button(surface,(508,539,784,64),'Resume saved pack reveal' if pending else 'Open One Pack',('cc_open',),mouse,enabled=pending or self.state['packs']['creature']>0,size=33)
        s._button(surface,(508,634,784,48),'Back to Cryptid Hub',('cc_nav','career_home'),mouse,size=27)

    def _opening(self,surface,mouse):
        s=self.screen;receipt=self.state['pending_reveal']
        if not receipt:self.navigate('packs');return
        elapsed=self.clock-self.opening_started
        s._text(surface,f"CREATURE PACK #{receipt['number']}",45,91,39,GOLD,True)
        label=('Cards awarded to your collection. Guest progress is temporary.' if s.temporary_collection else
               'Cards are already awarded and saved. Reveal them at your own pace.')
        s._text(surface,label,45,142,27,MUTED)
        if elapsed<650:
            self._pack_shape(surface,(513,205,340,416))
            if elapsed>180:
                tear=round(min(1,(elapsed-180)/350)*340)
                pygame.draw.line(surface,(255,237,177),(513,258),(513+tear,258),7)
                for i in range(12):
                    phase=elapsed*.006+i
                    pygame.draw.circle(surface,GOLD,(round(683+math.cos(phase)*(90+i*7)),round(355+math.sin(phase)*(70+i*5))),3)
        else:
            for i,entry in enumerate(receipt['cards']):
                rect=pygame.Rect(68+i*249,228,226,316)
                if i>=self.revealed:
                    self._pack_shape(surface,rect)
                else:
                    age=elapsed-650-i*330
                    width=max(4,round(rect.w*min(1,max(0,age/180))))
                    face=s.renderer.render(entry['id'],rect.size)
                    if width<rect.w:surface.blit(pygame.transform.smoothscale(face,(width,rect.h)),(rect.centerx-width//2,rect.y))
                    else:s._card(surface,entry['id'],rect,tag='library')
                    rarity=s.catalog.cards[entry['id']]['rarity']
                    if rarity=='Uncommon':pygame.draw.rect(surface,GOLD,rect.inflate(6,6),3,border_radius=12)
                    s._text(surface,rarity,rect.x,565,28,GOLD if rarity=='Uncommon' else TEXT,True)
                    s._text(surface,'NEW!' if entry['new'] else f"Copy {entry['copies_after']}",rect.x,605,29,GOLD if entry['new'] else MUTED,True)
        s._button(surface,(398,670,274,54),'Reveal all',('cc_reveal_all',),mouse,enabled=self.revealed<5,size=29)
        s._button(surface,(692,670,274,54),'Done',('cc_done',),mouse,enabled=self.revealed==5,size=29)

    def command(self,command):
        name=command[0]
        if name=='cc_nav':self.navigate(command[1])
        elif name=='cc_filter':self.filter=command[1];self.page_index=0
        elif name=='cc_page':self.page_index+=command[1]
        elif name=='cc_slot':
            self.slot=command[1];self.draft=list(self.state['decks'][self.slot]['cards']);self.deck_scroll=0;self.message=''
        elif name=='cc_add':
            cid=command[1];count=self.draft.count(cid)
            creatures=sum(self.screen.catalog.cards[c]['kind']=='creature' for c in self.draft)
            if len(self.draft)<30 and count<min(2,self.state['owned'].get(cid,0)) and (self.screen.catalog.cards[cid]['kind']!='creature' or creatures<8):self.draft.append(cid)
        elif name=='cc_remove':
            if command[1] in self.draft:self.draft.remove(command[1])
        elif name=='cc_scroll':self.deck_scroll+=command[1]
        elif name=='cc_clear':self.draft=[]
        elif name=='cc_save':
            ok,_=self._commit(lambda:save_deck(self.state,self.slot,self.draft,f'Custom Deck {self.slot+1}',self.screen.catalog))
            if ok:self.message='Deck saved and equipped.'
        elif name=='cc_open':
            ok,_=self._commit(lambda:open_pack(self.state,self.screen.catalog))
            if ok:self.navigate('pack_open')
        elif name=='cc_reveal_all':self.opening_started=self.clock-2600;self.revealed=5
        elif name=='cc_done':
            ok,_=self._commit(lambda:self.state.update(pending_reveal=None))
            if ok:self.navigate('packs')

    def handle_key(self,event):
        if event.type!=pygame.KEYDOWN:return False
        page=self.screen.page
        if page not in ('career_home','collection','builder','packs','pack_open'):return False
        if event.key==pygame.K_ESCAPE:
            if page=='career_home':return 'return'
            if page=='pack_open':
                if self.revealed<5:self.command(('cc_reveal_all',))
                else:self.command(('cc_done',))
            else:self.navigate('career_home')
        elif page in ('collection','builder'):
            if event.key==pygame.K_BACKSPACE:self.search=self.search[:-1];self.page_index=0
            elif event.key==pygame.K_DELETE:self.search='';self.page_index=0
            elif getattr(event,'unicode','') and event.unicode.isprintable() and len(self.search)<32:
                self.search+=event.unicode;self.page_index=0
        elif page=='pack_open' and event.key in (pygame.K_SPACE,pygame.K_RETURN):
            self.command(('cc_reveal_all',) if self.revealed<5 else ('cc_done',))
        elif page=='career_home' and event.key==pygame.K_RETURN:self.screen.start_battle()
        return True
