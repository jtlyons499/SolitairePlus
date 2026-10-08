"""Readable story pages, choices and map for Bigfoot Night."""
from pathlib import Path
import pygame
from career_activities import STORY, requirement_reason
from alien_night import STORY as ALIEN_STORY

MAP_PATH = 'assets/events/bigfoot_night/map.png'

class CareerActivityScreen:
    def __init__(self):
        self.story_data = STORY
        self.map_path = MAP_PATH
        self.buttons = []
        self.map_image = None
        self.map_signature = None
        self.view = 'intro'
        self.page = 0
        self.identity = None

    def lines(self, text, width, size):
        font = pygame.font.Font(None, size)
        lines = []
        for paragraph in text.split('\n'):
            line = ''
            for word in paragraph.split():
                trial = (line+' '+word).strip()
                if line and font.size(trial)[0] > width:
                    lines.append(line);line=word
                else:line=trial
            lines.append(line)
        return lines

    def text(self, surface, text, x, y, width, size=28, colour=(242,244,232)):
        font=pygame.font.Font(None,size)
        for line in self.lines(text,width,size):
            surface.blit(font.render(line,True,colour),(x,y))
            y+=font.get_linesize()+4
        return y

    def button(self, surface, rect, label, action, mouse, enabled=True, detail=''):
        rect=pygame.Rect(rect);hover=mouse is not None and rect.collidepoint(mouse)
        pygame.draw.rect(surface,(50,85,68) if enabled else (40,47,43),rect,border_radius=12)
        pygame.draw.rect(surface,(218,202,129) if hover and enabled else (103,135,112),rect,2,border_radius=12)
        self.text(surface,label,rect.x+14,rect.y+12,rect.width-28,26,(245,244,224) if enabled else (155,165,155))
        if detail:
            self.text(surface,detail,rect.x+14,rect.bottom-29,rect.width-28,21,(222,205,140) if enabled else (165,165,155))
        self.buttons.append((rect,action,enabled))

    def load_map(self):
        path=Path(self.map_path)
        try:
            stat=path.stat();signature=(str(path),stat.st_mtime_ns,stat.st_size)
        except OSError:signature=None
        if signature!=self.map_signature:
            self.map_signature=signature;self.map_image=None
            if signature:
                try:
                    image=pygame.image.load(str(path))
                    # Fit artwork without distorting its original proportions.
                    ratio=min(530/image.get_width(),440/image.get_height())
                    self.map_image=pygame.transform.smoothscale(image,(round(image.get_width()*ratio),round(image.get_height()*ratio)))
                except (OSError,pygame.error):pass

    def draw_map(self,surface,story):
        rect=pygame.Rect(85,160,530,440)
        pygame.draw.rect(surface,(29,54,38),rect,border_radius=16)
        self.load_map()
        if self.map_image:surface.blit(self.map_image,self.map_image.get_rect(center=rect.center))
        points={name:(round(rect.x+xy[0]*rect.width),round(rect.y+xy[1]*rect.height)) for name,xy in self.story_data['locations'].items()}
        pygame.draw.lines(surface,(135,131,95),False,list(points.values()),4)
        for name,point in points.items():
            current=story['location']==name;visited=name in story['visited_locations']
            pygame.draw.circle(surface,(255,216,95) if current else (145,181,132) if visited else (68,94,72),point,14 if current else 9)
            label=pygame.font.Font(None,23).render(name,True,(255,239,180) if current else (209,221,202))
            caption=label.get_rect(midtop=(point[0],point[1]+16));caption.clamp_ip(rect)
            surface.blit(label,caption)
        self.text(surface,'Items',90,618,520,26,(222,205,140))
        inventory=', '.join(self.story_data['items'][key] for key in story['items']) or 'None yet'
        self.text(surface,inventory,90,649,520,25)
        attitude={'trusted':'Trusted','distrustful':'Distrusted','clout_chaser':'Clout chaser'}.get(story['flags'].get('attitude'),'Unknown')
        if self.story_data.get('kind') == 'alien':
            attitude={'trusted':'Trusted','untrusted':'Untrusted','sympathetic':'Sympathetic'}.get(story['flags'].get('agents'),'Unknown')
            self.text(surface,'Agents’ impression: '+attitude,90,705,520,24)
        else:
            self.text(surface,'Bigfoot’s impression: '+attitude,90,705,520,24)

    def draw(self,surface,state,mouse,cash,story):
        self.story_data = ALIEN_STORY if state.get('kind') == 'alien' else STORY
        self.map_path = 'assets/events/alien_night/map.png' if state.get('kind') == 'alien' else MAP_PATH
        identity=(id(state),state.get('scene'),state['night'],state['claimed'])
        if identity!=self.identity:
            self.identity=identity;self.view='result' if state['claimed'] else 'intro';self.page=0
        self.buttons=[]
        pygame.draw.rect(surface,(15,29,24),(60,35,1246,705),border_radius=20)
        pygame.draw.rect(surface,(108,140,110),(60,35,1246,705),2,border_radius=20)
        self.text(surface,f"{self.story_data.get('name', 'Bigfoot Night').upper()}  •  INVESTIGATION DAY {state['night']}",90,60,1150,40)
        title=self.story_data['scenes'].get(state.get('scene'),{}).get('title','INVESTIGATION COMPLETE')
        self.text(surface,title,655,115,605,29,(222,205,140))
        self.draw_map(surface,story)
        if self.view in ('intro','result'):
            body=state.get('result_text','') if state['claimed'] else state['intro']
            lines=self.lines(body,605,30);per_page=13;count=max(1,(len(lines)+per_page-1)//per_page)
            self.page=min(self.page,count-1)
            font=pygame.font.Font(None,30)
            for i,line in enumerate(lines[self.page*per_page:(self.page+1)*per_page]):
                surface.blit(font.render(line,True,(242,244,232)),(655,165+i*(font.get_linesize()+4)))
            if count>1:
                self.button(surface,(655,564,180,45),'Previous',('page',-1),mouse,self.page>0)
                self.text(surface,f'{self.page+1}/{count}',935,575,100,25)
                self.button(surface,(1080,564,180,45),'Next page',('page',1),mouse,self.page<count-1)
            if state['claimed'] and state.get('stage')!='complete':
                labels=[f"Cash: ${state['cash_change']:+,}",f"Fans: {state['fan_change']:+,}"]
                cosmetics=[self.story_data['cosmetics'][key]['name']+' '+self.story_data['cosmetics'][key]['kind'].rstrip('s') for key in state.get('earned_cosmetics',[])]
                if cosmetics:labels.append('Unlocked: '+', '.join(cosmetics))
                self.text(surface,'  |  '.join(labels),655,615,605,25,(248,223,129))
            label='Continue to calendar' if state['claimed'] else 'Choose your action'
            self.button(surface,(655,674,605,48),label,'continue' if state['claimed'] else 'choices',mouse)
        else:
            for i,choice in enumerate(state['options']):
                reason=requirement_reason(story,choice,cash,data=self.story_data)
                effects=choice['effects'];details=[]
                if effects['cash']:details.append(f"${effects['cash']:+,}")
                if effects['fans']:details.append(f"{effects['fans']:+,} fans")
                details += [self.story_data['items'][key] for key in effects['items']]
                details += ['Unlock: '+self.story_data['cosmetics'][key]['name'] for key in effects['cosmetics']]
                self.button(surface,(655,163+i*123,605,113),choice['text'],('choice',i),mouse,not reason,reason or ' • '.join(details))
            self.button(surface,(655,674,605,48),'Read scene again','intro',mouse)

    def click(self,pos):
        if pos is None:return None
        action=next((action for rect,action,enabled in self.buttons if enabled and rect.collidepoint(pos)),None)
        if action in ('choices','intro'):
            self.view=action;self.page=0;return action
        if isinstance(action,tuple) and action[0]=='page':
            self.page=max(0,self.page+action[1]);return action
        return action
