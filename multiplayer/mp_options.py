"""Persistent local display/audio options with host-only table pacing."""
import json
import os
from pathlib import Path
import pygame
from mp_widgets import wooden_button
import texas_holdem_ui as ui

SIZES=((1366,768),(1600,900),(1920,1080),(2560,1440))


class Options:
    def __init__(self):
        self.path=Path(os.environ.get('LOCALAPPDATA',Path.home()/'.config'))/'SolitaireMultiplayer'/'options.json'
        self.values={'size':[1366,768],'fullscreen':False,'sound':True,'volume':75,'animations':True,'speed':'normal','motion':'normal'}
        try:
            raw=json.loads(self.path.read_text(encoding='utf-8'))
            if isinstance(raw,dict):
                if tuple(raw.get('size',())) in SIZES:self.values['size']=raw['size']
                for key in ('fullscreen','sound','animations'):
                    if isinstance(raw.get(key),bool):self.values[key]=raw[key]
                if raw.get('speed') in ('slow','normal','fast'):self.values['speed']=raw['speed']
                if raw.get('motion') in ('slow','normal','fast'):self.values['motion']=raw['motion']
                if isinstance(raw.get('volume'),int):self.values['volume']=max(0,min(100,raw['volume']))
        except (OSError,ValueError,TypeError):pass
        inherited=os.environ.get('SOLITAIRE_MP_WINDOW','').split('x')
        try:
            size=tuple(map(int,inherited))
            if size in SIZES:self.values['size']=list(size);self.values['fullscreen']=os.environ.get('SOLITAIRE_MP_FULLSCREEN')=='1'
        except ValueError:pass
        ui.holdem_table_speed=self.values['speed'];self.open=False;self.buttons=[]
        self.font=pygame.font.Font(None,30);self.small=pygame.font.Font(None,25)

    def display(self):
        return pygame.display.set_mode((0,0) if self.values['fullscreen'] else self.values['size'],pygame.FULLSCREEN if self.values['fullscreen'] else pygame.RESIZABLE)

    def save(self):
        try:self.path.parent.mkdir(parents=True,exist_ok=True);self.path.write_text(json.dumps(self.values),encoding='utf-8')
        except OSError:pass

    def draw(self,surface,table):
        shade=pygame.Surface(surface.get_size(),pygame.SRCALPHA);shade.fill((0,0,0,190));surface.blit(shade,(0,0))
        pygame.draw.rect(surface,(20,46,37),(325,135,716,500),border_radius=16);self.buttons=[]
        def text(value,x,y):surface.blit(self.font.render(value,True,(245,236,211)),(x,y))
        def button(value,rect,action,enabled=True):
            rect=pygame.Rect(rect);wooden_button(surface,None,rect,value,self.small,enabled)
            if enabled:self.buttons.append((rect,action))
        text('OPTIONS',365,163);button('Done',(875,155,120,40),'close')
        text('Window size',365,223)
        for i,size in enumerate(SIZES):button(f'{size[0]}×{size[1]}',(365+i*160,265,150,40),('size',size))
        button('Fullscreen: '+('On' if self.values['fullscreen'] else 'Off'),(365,325,300,42),('toggle','fullscreen'))
        button('SFX: '+('On' if self.values['sound'] else 'Off'),(685,325,300,42),('toggle','sound'))
        text(f'SFX volume: {self.values["volume"]}%',365,390)
        button('−',(700,383,100,40),('volume',-25));button('+',(815,383,100,40),('volume',25))
        button('Animation '+('On' if self.values['animations'] else 'Off'),(365,448,180,40),('toggle','animations'))
        for i,speed in enumerate(('slow','normal','fast')):button(speed.title()+(' *' if self.values['motion']==speed else ''),(560+i*145,448,135,40),('motion',speed))
        host=table is None or not hasattr(table,'hosting') or table.hosting
        text('Table pace (host controls the room)',365,510)
        current=getattr(table,'message',{}).get('table_speed',self.values['speed'])
        for i,speed in enumerate(('slow','normal','fast')):button(speed.title()+(' [On]' if current==speed else ''),(365+i*210,553,195,40),('speed',speed),host)

    def event(self,event,mouse,table):
        resize=False
        if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:self.open=False
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            for rect,action in self.buttons:
                if not rect.collidepoint(mouse):continue
                if action=='close':self.open=False
                elif action[0]=='size':self.values['size']=list(action[1]);self.values['fullscreen']=False;resize=True
                elif action[0]=='toggle':self.values[action[1]]=not self.values[action[1]];resize=action[1]=='fullscreen'
                elif action[0]=='volume':self.values['volume']=max(0,min(100,self.values['volume']+action[1]))
                elif action[0]=='speed':
                    self.values['speed']=action[1];ui.holdem_table_speed=action[1]
                    if getattr(table,'hosting',False) and getattr(table,'authority',None):table.authority.set_speed(action[1])
                elif action[0]=='motion':self.values['motion']=action[1]
                self.save();break
        return resize
