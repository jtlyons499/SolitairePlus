"""Case shop, deterministic decelerating reel, loot collection and trophy shelves."""
import math
import random
from pathlib import Path
import pygame
from case_opening import CASES, ITEMS, COLORS, case_price, choose_item

ROOT=Path(__file__).resolve().parent/'assets'/'case_opening'


class CaseOpeningScreen:
 def __init__(self):
  self.buttons=[];self.images={};self.fonts={};self.phase='shop';self.notice='';self.state=None
 def enter(self,state,wallet,purchase_callback,residence='dingy_apartment',temporary=False):
  self.state=state;self.wallet=wallet;self.purchase_callback=purchase_callback;self.residence=residence
  self.temporary=temporary;self.phase='shop';self.notice='';self.page=0;self.receipt=None;self.buttons=[];self.images.clear()
 def font(self,size):
  if size not in self.fonts:self.fonts[size]=pygame.font.Font(None,size)
  return self.fonts[size]
 def image(self,path):
  if path not in self.images:
   try:self.images[path]=pygame.image.load(ROOT/path).convert_alpha()
   except (FileNotFoundError,pygame.error):self.images[path]=None
  return self.images[path]
 def text(self,out,value,x,y,size=28,color=(240,239,221),width=None):
  font=self.font(size)
  if width:
   while font.size(value)[0]>width and size>20:size-=1;font=self.font(size)
  out.blit(font.render(value,True,color),(x,y))
 def button(self,out,rect,label,action,mouse,enabled=True):
  rect=pygame.Rect(rect);hover=enabled and mouse and rect.collidepoint(mouse)
  pygame.draw.rect(out,(65,104,111) if hover else (28,54,61),rect,border_radius=9)
  pygame.draw.rect(out,(234,189,93) if enabled else (86,106,110),rect,2,border_radius=9)
  size=28
  while self.font(size).size(label)[0]>rect.w-16 and size>18:size-=1
  image=self.font(size).render(label,True,(247,232,197) if enabled else (113,133,136))
  out.blit(image,image.get_rect(center=rect.center))
  if enabled:self.buttons.append((rect,action))
 def item(self,out,identity,rect):
  item=ITEMS[identity];rect=pygame.Rect(rect);color=COLORS[item['kind']]
  pygame.draw.rect(out,(24,37,46),rect,border_radius=12);pygame.draw.rect(out,color,rect,3,border_radius=12)
  art=self.image(item.get('image','items/'+identity+'.png'))
  artrect=pygame.Rect(rect.x+12,rect.y+14,rect.w-24,rect.h-68)
  if art:
   ratio=min(artrect.w/art.get_width(),artrect.h/art.get_height());scaled=pygame.transform.smoothscale(art,(round(art.get_width()*ratio),round(art.get_height()*ratio)))
   out.blit(scaled,scaled.get_rect(center=artrect.center))
  else:
   cx,cy=artrect.center;r=min(artrect.w,artrect.h)//3
   if item['kind']=='trophy':
    pygame.draw.polygon(out,color,[(cx-r,cy-r),(cx+r,cy-r),(cx+r//2,cy+r//3),(cx-r//2,cy+r//3)])
    pygame.draw.rect(out,color,(cx-5,cy,10,r));pygame.draw.rect(out,color,(cx-r//2,cy+r,r,8))
   elif item['kind']=='cash':
    pygame.draw.rect(out,color,artrect.inflate(-20,-20),border_radius=12)
    glyph=self.font(56).render('$',True,(18,39,33));out.blit(glyph,glyph.get_rect(center=artrect.center))
   elif item['kind']=='fans':
    for dx in (-r//2,r//2):pygame.draw.circle(out,color,(cx+dx,cy-r//3),r//3);pygame.draw.rect(out,color,(cx+dx-r//3,cy,r*2//3,r),border_radius=10)
   elif item['kind']=='rating':
    pygame.draw.polygon(out,color,[(cx-r,cy+r),(cx-r,cy),(cx,cy),(cx,cy-r),(cx+r,cy-r),(cx+r,cy+r)])
   elif item['kind']=='cosmetic':
    for i in range(4):pygame.draw.circle(out,color,(cx,cy),r-i*6,2)
   else:
    pygame.draw.lines(out,color,False,[(cx-r,cy-r//2),(cx+r,cy),(cx-r//2,cy+r),(cx+r//2,cy-r)],5)
  pygame.draw.rect(out,color,(rect.x+2,rect.bottom-49,rect.w-4,47),border_radius=7)
  size=25
  while self.font(size).size(item['name'])[0]>rect.w-16 and size>19:size-=1
  label=self.font(size).render(item['name'],True,(12,23,32));out.blit(label,label.get_rect(center=(rect.centerx,rect.bottom-25)))
 def begin(self,case_id):
  try:receipt,wallet=self.purchase_callback(case_id)
  except (OSError,ValueError) as error:self.notice=str(error);return
  self.receipt=receipt;self.wallet=wallet;self.started=pygame.time.get_ticks();self.phase='opening'
  rng=random.Random(receipt['number']*7019+self.started);self.reel=[choose_item(case_id,rng)['id'] for _ in range(45)]
  self.reel[36]=receipt['item_id'];self.target=36*184+86-603+rng.uniform(-55,55)
  self.last_tick=-1;self.last_sound=0
 def update(self,now,play_sound=None):
  if self.phase!='opening':return
  t=max(0,min(1,(now-self.started)/3800));self.distance=self.target*(1-(1-t)**4)
  tick=int((self.distance+603)/184)
  if tick!=self.last_tick and now-self.last_sound>45:
   if play_sound:play_sound('card_move')
   self.last_tick=tick;self.last_sound=now
  if t>=1:
   self.phase='result'
   if play_sound:play_sound('poker_hand_win' if self.receipt['kind'] in ('trophy','cosmetic') else 'card_flip')
 def handle_event(self,event,mouse=None):
  if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
   if self.phase in ('shop','collection','trophies'):return 'return'
   self.phase='shop';return
  if event.type!=pygame.MOUSEBUTTONDOWN or event.button!=1:return
  for rect,action in self.buttons:
   if not mouse or not rect.collidepoint(mouse):continue
   if action=='return':return 'return'
   if action in ('shop','collection','trophies'):self.phase=action;self.page=0;self.notice=''
   elif action.startswith('open:'):self.begin(action[5:])
   elif action=='skip':self.phase='result'
   elif action=='prev':self.page=max(0,self.page-1)
   elif action=='next':self.page+=1
   return
 def draw(self,out,mouse=None):
  self.buttons=[];out.fill((13,25,34));background=self.image('background.png')
  if self.phase=='trophies':
   background=self.image('trophy_room/walls/'+self.residence+'.png')
   if background is None:
    palette=((39,43,49),(52,43,38),(43,50,48),(51,43,60),(60,51,37),(39,51,62))
    color=palette[sum(ord(c) for c in self.residence)%len(palette)];out.fill(color)
    for x in range(0,1366,82):pygame.draw.line(out,tuple(c+9 for c in color),(x,130),(x,670),2)
  if background:out.blit(pygame.transform.smoothscale(background,out.get_size()),(0,0))
  self.text(out,'CASE ROOM',32,24,44,(247,198,94));self.text(out,f'Cash ${self.wallet:,}',32,72,30)
  self.text(out,'PRACTICE — collection and rewards are temporary' if self.temporary else 'Career collection — rewards save before the reel spins',340,34,26)
  self.button(out,(1158,24,176,48),'Return','return',mouse)
  if self.phase in ('shop','collection','trophies'):
   for i,(name,label) in enumerate((('shop','Cases'),('collection','All loot'),('trophies','Trophy room'))):self.button(out,(340+i*205,78,190,42),label,name,mouse)
  if self.phase=='shop':
   pages=max(1,(len(CASES)+2)//3);self.page=min(self.page,pages-1)
   for index,(key,case) in enumerate(list(CASES.items())[self.page*3:(self.page+1)*3]):
    x=44+index*440;rect=pygame.Rect(x,152,398,476)
    pygame.draw.rect(out,(23,42,52),rect,border_radius=16);pygame.draw.rect(out,(115,143,155),rect,2,border_radius=16)
    self.text(out,case['name'],x+22,170,36,width=354)
    art=self.image(case.get('image','cases/'+key+'.png'))
    if art:out.blit(pygame.transform.smoothscale(art,(290,172)),(x+54,216))
    else:
     pygame.draw.rect(out,(53,76,94),(x+65,239,268,125),border_radius=15)
     pygame.draw.line(out,(213,171,85),(x+65,275),(x+333,275),5);pygame.draw.rect(out,(239,191,91),(x+185,264,27,43),border_radius=4)
    price=case_price(key,self.wallet);self.text(out,f'${price:,} to open',x+22,393,32,(248,201,117))
    for i,(kind,chance) in enumerate(case['weights'].items()):self.text(out,f'{kind.title()}: {chance}%',x+22+(i%2)*182,440+(i//2)*29,25,COLORS[kind])
    self.button(out,(x+22,554,354,52),'Open '+case['name'],'open:'+key,mouse,self.wallet>=price)
   self.text(out,'Prices scale with your cash. Each case contains one item. Odds are shown above.',44,654,28)
   self.text(out,f"Opened {self.state['opened']:,} / Spent ${self.state['spent']:,}",44,701,27)
   self.button(out,(690,686,180,48),'Previous','prev',mouse,self.page>0)
   self.text(out,f'{self.page+1} / {pages}',890,699,27)
   self.button(out,(982,686,180,48),'Next','next',mouse,self.page+1<pages)
  elif self.phase=='opening':
   self.text(out,CASES[self.receipt['case']]['name'],44,172,38)
   self.text(out,'Your reward is already committed. The reel never rerolls it.',44,224,29)
   clip=out.get_clip();out.set_clip((80,300,1206,260))
   for i,identity in enumerate(self.reel):
    x=80+i*184-getattr(self,'distance',0)
    if x>-100 and x<1286:self.item(out,identity,(round(x),314,172,220))
   out.set_clip(clip);pygame.draw.line(out,(248,221,122),(683,291),(683,561),5)
   pygame.draw.polygon(out,(248,221,122),[(668,282),(698,282),(683,304)])
   self.button(out,(542,654,282,54),'Skip animation','skip',mouse)
  elif self.phase=='result':
   receipt=self.receipt;self.item(out,receipt['item_id'],(503,159,360,360))
   item=ITEMS[receipt['item_id']];kind=receipt['kind'];amount=receipt['amount']
   cosmetic_label = item.get('cosmetic_type', 'cosmetic').replace('_', ' ').title()
   detail={'cash':f'+${amount:,} cash','fans':f'+{amount:,} fans','rating':f'+{amount} {item.get("game","").replace("_"," ")} rating',
           'cosmetic':f'{cosmetic_label} unlocked in Customize','trophy':'Added to your trophy room','junk':'Added to your loot collection'}[kind]
   if self.temporary and kind in ('rating','fans','cosmetic'):detail += ' (practice loot only)'
   self.text(out,detail,290,558,35,COLORS[kind],width=800)
   self.text(out,f"Case cost ${receipt['cost']:,}  /  Cash now ${self.wallet:,}",360,604,29)
   self.button(out,(360,672,270,54),'More cases','shop',mouse);self.button(out,(654,672,350,54),'View collection','collection',mouse)
  else:
   trophies=self.phase=='trophies';keys=[k for k in self.state['inventory'] if not trophies or ITEMS[k]['kind']=='trophy']
   keys.sort(key=lambda k:(ITEMS[k]['kind'],ITEMS[k]['name']));pages=max(1,(len(keys)+7)//8);self.page=min(self.page,pages-1)
   if trophies:
    cabinet=self.image('trophy_room/cabinet.png')
    if cabinet:out.blit(pygame.transform.smoothscale(cabinet,(1250,500)),(58,145))
    else:
     for y in (388,635):pygame.draw.rect(out,(103,67,42),(50,y,1266,17));pygame.draw.rect(out,(157,115,66),(50,y,1266,5))
    self.text(out,self.residence.replace('_',' ').title()+' trophy wall',48,132,26)
   for i,key in enumerate(keys[self.page*8:(self.page+1)*8]):
    x=78+(i%4)*317;y=176+(i//4)*246;self.item(out,key,(x,y,260,207));self.text(out,f"Owned: {self.state['inventory'][key]}",x,y+212,25)
   if not keys:self.text(out,'Your first trophy is waiting in a case.',340,344,38)
   self.button(out,(370,686,200,48),'Previous','prev',mouse,self.page>0);self.button(out,(794,686,200,48),'Next','next',mouse,self.page+1<pages)
   self.text(out,f'Page {self.page+1} / {pages}',622,698,28)
  if self.notice:
   pygame.draw.rect(out,(66,32,38),(20,735,1326,30));self.text(out,self.notice,32,740,24,(255,207,177),width=1300)
