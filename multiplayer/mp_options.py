"""Persistent local display/audio options with host-only table pacing.

The window itself is solitaireplus/app/window.py, shared with single-player (W1): DPI-aware,
sizes that fit the screen, centred, letterboxed desktop fullscreen. The game always draws on
window.game_surface (1366x768) and SDL scales it into the window.
"""
import json
import os
from pathlib import Path
import pygame
from mp_widgets import wooden_button
from solitaireplus.app import state, window
from solitaireplus.app.settings import RESOLUTION_OPTIONS

SIZES=tuple(RESOLUTION_OPTIONS)
CAPTION='Solitaire+ Multiplayer'


def inherited_window(environ=None):
    """(size or None, fullscreen or None) handed over by the single-player game.

    multiplayer_launcher.py passes the player's window size as SOLITAIRE_MP_WINDOW='WxH' (any
    positive size: the default size is usually not one of the Options sizes) and the fullscreen
    choice as SOLITAIRE_MP_FULLSCREEN='0'/'1'. Each is read on its own; anything else is None."""
    environ=os.environ if environ is None else environ
    size=None
    parts=str(environ.get('SOLITAIRE_MP_WINDOW','')).strip().lower().split('x')
    if len(parts)==2:
        try:
            width,height=int(parts[0]),int(parts[1])
            if width>0 and height>0:size=(width,height)
        except ValueError:pass
    fullscreen={'0':False,'1':True}.get(str(environ.get('SOLITAIRE_MP_FULLSCREEN','')).strip())
    return size,fullscreen


class Options:
    def __init__(self):
        self.path=Path(os.environ.get('LOCALAPPDATA',Path.home()/'.config'))/'SolitaireMultiplayer'/'options.json'
        # size None = the default window size for this screen (window.default_window_size).
        self.values={'size':None,'fullscreen':False,'sound':True,'volume':75,'animations':True,'speed':'normal','motion':'normal'}
        try:
            raw=json.loads(self.path.read_text(encoding='utf-8'))
            if isinstance(raw,dict):
                size=raw.get('size')
                if isinstance(size,list) and tuple(size) in SIZES:self.values['size']=list(size)
                for key in ('fullscreen','sound','animations'):
                    if isinstance(raw.get(key),bool):self.values[key]=raw[key]
                if raw.get('speed') in ('slow','normal','fast'):self.values['speed']=raw['speed']
                if raw.get('motion') in ('slow','normal','fast'):self.values['motion']=raw['motion']
                if isinstance(raw.get('volume'),int):self.values['volume']=max(0,min(100,raw['volume']))
        except (OSError,ValueError,TypeError):pass
        # What the single-player game handed over wins for this start, but is never saved.
        size,fullscreen=inherited_window()
        self.start_size=size or self.values['size']
        self.start_fullscreen=fullscreen if fullscreen is not None else self.values['fullscreen']
        state.holdem_table_speed=self.values['speed'];self.open=False;self.buttons=[]
        self.font=pygame.font.Font(None,30);self.small=pygame.font.Font(None,25)

    def open_window(self):
        """Create the window (once, at start-up): the start size if it fits, else the default."""
        state.window_custom_cursor=False   # multiplayer has no single-player cursor choices
        window.open_window(CAPTION,self.start_size)
        if self.start_fullscreen:window.set_fullscreen_enabled(True)

    def set_fullscreen(self,on):
        window.set_fullscreen_enabled(on)
        self.values['fullscreen']=state.fullscreen_enabled;self.save()

    def set_size(self,size):
        """Windowed mode at an Options size; sizes too large for this screen do nothing."""
        size=tuple(size)
        if not window.fits(size,window.usable_area()):return False
        window.set_window_size(*size)
        self.values['size']=list(size);self.values['fullscreen']=False;self.save()
        return True

    def save(self):
        # No 'size' key for the default size: older versions read a null size as a broken file.
        values={key:value for key,value in self.values.items() if not (key=='size' and value is None)}
        try:self.path.parent.mkdir(parents=True,exist_ok=True);self.path.write_text(json.dumps(values),encoding='utf-8')
        except OSError:pass

    def draw(self,surface,table):
        shade=pygame.Surface(surface.get_size(),pygame.SRCALPHA);shade.fill((0,0,0,190));surface.blit(shade,(0,0))
        pygame.draw.rect(surface,(20,46,37),(325,135,716,500),border_radius=16);self.buttons=[]
        def text(value,x,y,font=None,color=(245,236,211)):surface.blit((font or self.font).render(value,True,color),(x,y))
        def button(value,rect,action,enabled=True):
            rect=pygame.Rect(rect);wooden_button(surface,None,rect,value,self.small,enabled)
            if enabled:self.buttons.append((rect,action))
        text('OPTIONS',365,163);button('Done',(875,155,120,40),'close')
        current=(getattr(state,'WINDOWED_WIDTH',None),getattr(state,'WINDOWED_HEIGHT',None))
        text('Window size'+(f' (now {current[0]}×{current[1]})' if None not in current else ''),365,223)
        choices=window.window_size_choices(window.usable_area(),SIZES)
        if not all(fits for _,fits in choices):text('Greyed out: too large for this screen',700,226,self.small,(205,196,170))
        for i,(size,fits) in enumerate(choices):
            # Greyed-out sizes are not clickable (they are not added to self.buttons).
            button(f'{size[0]}×{size[1]}'+(' *' if size==current else ''),(365+i*160,265,150,40),('size',size),fits)
        button('Fullscreen: '+('On' if state.fullscreen_enabled else 'Off'),(365,325,300,42),('toggle','fullscreen'))
        button('SFX: '+('On' if self.values['sound'] else 'Off'),(685,325,300,42),('toggle','sound'))
        text(f'SFX volume: {self.values["volume"]}%',365,390)
        button('−',(700,383,100,40),('volume',-25));button('+',(815,383,100,40),('volume',25))
        button('Animation '+('On' if self.values['animations'] else 'Off'),(365,448,180,40),('toggle','animations'))
        for i,speed in enumerate(('slow','normal','fast')):button(speed.title()+(' *' if self.values['motion']==speed else ''),(560+i*145,448,135,40),('motion',speed))
        holdem_context=table is None or getattr(table,'mode','holdem') in (None,'holdem')
        host=holdem_context and (table is None or not hasattr(table,'hosting') or table.hosting)
        text("Hold'em table pace (host controls the room)",365,510)
        current=getattr(table,'message',{}).get('table_speed',self.values['speed'])
        for i,speed in enumerate(('slow','normal','fast')):button(speed.title()+(' [On]' if current==speed else ''),(365+i*210,553,195,40),('speed',speed),host)

    def event(self,event,mouse,table):
        if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:self.open=False
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            for rect,action in self.buttons:
                if not rect.collidepoint(mouse):continue
                if action=='close':self.open=False
                elif action[0]=='size':self.set_size(action[1]);break        # set_size saves
                elif action==('toggle','fullscreen'):self.set_fullscreen(not state.fullscreen_enabled);break
                elif action[0]=='toggle':self.values[action[1]]=not self.values[action[1]]
                elif action[0]=='volume':self.values['volume']=max(0,min(100,self.values['volume']+action[1]))
                elif action[0]=='speed':
                    self.values['speed']=action[1];state.holdem_table_speed=action[1]
                    authority=getattr(table,'authority',None)
                    if getattr(table,'hosting',False) and authority is not None and hasattr(authority,'set_speed'):authority.set_speed(action[1])
                elif action[0]=='motion':self.values['motion']=action[1]
                self.save();break
