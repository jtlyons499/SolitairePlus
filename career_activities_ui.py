"""Bigfoot Night: persistent route map, recap and manually authored choices."""
from pathlib import Path
import pygame

MAP_PATH = 'assets/events/bigfoot_night/map.png'
POINTS = {'Camp': (280, 520), 'Forest': (465, 345), 'Clearing': (270, 205)}

class CareerActivityScreen:
    def __init__(self):
        self.buttons = []
        self.map_image = None
        self.map_signature = None

    def text(self, surface, text, x, y, width, size=28, colour=(242, 244, 232)):
        font = pygame.font.Font(None, size)
        lines, line = [], ''
        for word in text.split():
            trial = (line+' '+word).strip()
            if line and font.size(trial)[0] > width:
                lines.append(line); line=word
            else: line=trial
        lines.append(line)
        for line in lines:
            surface.blit(font.render(line, True, colour), (x,y))
            y += font.get_linesize()+4
        return y

    def button(self, surface, rect, label, action, mouse, enabled=True):
        rect=pygame.Rect(rect)
        hover=mouse is not None and rect.collidepoint(mouse)
        pygame.draw.rect(surface, (50,85,68) if enabled else (45,49,46),rect,border_radius=12)
        pygame.draw.rect(surface,(218,202,129) if hover and enabled else (103,135,112),rect,2,border_radius=12)
        self.text(surface,label,rect.x+14,rect.y+12,rect.width-28,26,(245,244,224) if enabled else (155,155,150))
        self.buttons.append((rect,action,enabled))

    def load_map(self):
        path=Path(MAP_PATH)
        try:
            stat=path.stat();signature=(stat.st_mtime_ns,stat.st_size)
        except OSError: signature=None
        if signature!=self.map_signature:
            self.map_signature=signature;self.map_image=None
            if signature:
                try:self.map_image=pygame.transform.smoothscale(pygame.image.load(str(path)),(530,470))
                except (OSError,pygame.error):pass

    def draw(self, surface, state, mouse, cash, story=None):
        self.buttons=[];story=story or {'location':'Camp','shoes':False,'clues':0,'last_result':''}
        panel=pygame.Rect(60,35,1246,690)
        pygame.draw.rect(surface,(15,29,24),panel,border_radius=20)
        pygame.draw.rect(surface,(108,140,110),panel,2,border_radius=20)
        self.text(surface,f"BIGFOOT NIGHT — NIGHT {state['night']}",90,60,1100,44)
        self.load_map()
        map_rect=pygame.Rect(85,155,530,470)
        if self.map_image:surface.blit(self.map_image,map_rect)
        else:
            pygame.draw.rect(surface,(29,54,38),map_rect,border_radius=16)
            pygame.draw.lines(surface,(135,131,95),False,[POINTS[x] for x in ('Camp','Forest','Clearing')],5)
        for location,point in POINTS.items():
            current=story['location']==location
            pygame.draw.circle(surface,(255,216,95) if current else (130,162,118),point,15 if current else 10)
            self.text(surface,location,point[0]+22,point[1]-12,140,28)
        self.text(surface,f"Location: {story['location']}  |  Clues: {story['clues']}",90,643,520,27)
        self.text(surface,'Gear: Sasquatch Shoes' if story['shoes'] else 'Gear: Everyday shoes',90,680,520,26)
        x,y,width=655,140,605
        if state['claimed']:
            y=self.text(surface,state['result_text'],x,y,width,31)
            self.text(surface,f"Fans: {state['fan_change']:+d}   |   Cash: ${state['cash_change']:+d}",x,max(y+25,360),width,32,(248,223,129))
            self.button(surface,(655,595,605,65),'Continue to calendar','continue',mouse)
        else:
            y=self.text(surface,state['intro'],x,y,width,28)
            # Keep every authored choice visible; use compact four-choice layout.
            count=len(state['options']);top=max(325,min(y+20,365 if count==4 else 390))
            height=67 if count==4 else 88;gap=9
            for i,choice in enumerate(state['options']):
                extra=' • Unlocks Sasquatch Shoes' if choice['changes'].get('shoes') else ''
                label=f"{choice['name']}\n".replace('\n',' ') + f"({choice['fans']:+d} fans, ${choice['cash']:+d})"+extra
                self.button(surface,(655,top+i*(height+gap),605,height),label,('choice',i),mouse,cash+choice['cash']>=0)

    def click(self,pos):
        if pos is None:return None
        return next((action for rect,action,enabled in self.buttons if enabled and rect.collidepoint(pos)),None)
