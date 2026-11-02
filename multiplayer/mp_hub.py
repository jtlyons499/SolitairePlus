"""Base-game-styled multiplayer front page."""
import pygame
from mp_widgets import wooden_button

MODES = (
    ("holdem", "Texas Hold'em", "Up to six seats • room-code poker"),
    ("score_four", "Score-Four (24)", "Up to four players • first to three"),
    ("blind_mans_bluff", "Blind Man's Bluff", "Up to four players • forehead poker"),
    ("roulette", "Roulette", "Up to four players • shared timed wheel"),
    ("dmh", "Dead Man's Hand PvP", "1v1 western duel • first to five"),
)


class MultiplayerHub:
    def __init__(self, appearance, profile):
        self.appearance=appearance;self.profile=profile;self.buttons=[]
        self.selected_mode='holdem';self.font=pygame.font.Font(None,30);self.small=pygame.font.Font(None,22);self.large=pygame.font.Font(None,40)
        self.code_rect=pygame.Rect(1028,338,250,50)

    def panel(self,surface,rect,fill=(12,34,27,228),border=(156,174,165),width=1,radius=14):
        rect=pygame.Rect(rect);layer=pygame.Surface(rect.size,pygame.SRCALPHA);pygame.draw.rect(layer,fill,layer.get_rect(),border_radius=radius);surface.blit(layer,rect);pygame.draw.rect(surface,border,rect,width,border_radius=radius);return rect

    def text(self,surface,text,pos,font=None,color=(244,236,211),center=False):
        image=(font or self.font).render(str(text),True,color);surface.blit(image,image.get_rect(center=pos) if center else pos);return image

    def button(self,surface,label,rect,action,mouse,enabled=True):
        rect=pygame.Rect(rect);wooden_button(surface,self.appearance,rect,label,self.small,enabled,hover=enabled and rect.collidepoint(mouse));
        if enabled:self.buttons.append((rect,action))

    def draw(self,surface,mouse,room_code='',code_active=False):
        self.buttons=[];self.appearance.background(surface)
        shade=pygame.Surface(surface.get_size(),pygame.SRCALPHA);shade.fill((0,0,0,38));surface.blit(shade,(0,0))
        logo=self.appearance.image('assets/ui/menu_ui/floating_logo.png',(560,158))
        if logo:surface.blit(logo,logo.get_rect(center=(683,92)))
        else:self.text(surface,'SOLITAIRE+',(683,76),pygame.font.Font(None,64),(255,220,110),True)
        self.text(surface,'MULTIPLAYER',(683,152),self.large,(255,220,110),True)

        # Player card.
        self.panel(surface,(64,195,290,485),(10,31,25,235),(218,226,220),2)
        self.text(surface,'YOUR PROFILE',(209,222),self.font,(255,220,110),True)
        self.appearance.avatar(surface,self.profile.public(),pygame.Rect(151,255,116,116),self.profile.data['name'])
        self.text(surface,self.profile.data['name'] or 'Player',(209,395),self.font,(244,236,211),True)
        self.text(surface,f'Multiplayer Level {self.profile.level}',(209,427),self.small,(196,209,201),True)
        self.text(surface,f"{self.profile.data['xp']} XP  •  {self.profile.data['wins']} winning hands",(209,455),self.small,(196,209,201),True)
        self.button(surface,'EDIT PROFILE / AVATAR',(94,500,230,48),'profile',mouse)
        self.text(surface,'Avatar editing follows the same', (209,575),self.small,(196,209,201),True)
        self.text(surface,'builder as single-player profiles.', (209,600),self.small,(196,209,201),True)

        # Game selector.
        self.panel(surface,(385,195,575,485),(10,31,25,235),(218,226,220),2)
        self.text(surface,'CHOOSE A GAME',(415,218),self.font,(255,220,110))
        for i,(key,title,description) in enumerate(MODES):
            y=260+i*78;rect=pygame.Rect(415,y,515,64);selected=key==self.selected_mode
            self.panel(surface,rect,(30,70,53,242) if selected else (17,47,37,225),(255,215,85) if selected else (119,146,133),3 if selected else 1,10)
            self.text(surface,title,(435,y+10),self.font,(255,232,145) if selected else (244,236,211))
            self.text(surface,description,(435,y+38),self.small,(196,209,201))
            self.buttons.append((rect,('mode',key)))

        # Connection panel. Relay URL is deliberately hidden from normal users.
        self.panel(surface,(990,195,312,485),(10,31,25,235),(218,226,220),2)
        self.text(surface,'ONLINE ROOM',(1146,222),self.font,(255,220,110),True)
        selected=dict((k,(t,d)) for k,t,d in MODES)[self.selected_mode][0]
        self.text(surface,selected,(1146,267),self.font,(244,236,211),True)
        if self.selected_mode=='dmh':
            self.text(surface,'Dead Man’s Hand uses its own', (1146,326),self.small,(196,209,201),True)
            self.text(surface,'host / join duel lobby.', (1146,351),self.small,(196,209,201),True)
            self.button(surface,'OPEN DUEL LOBBY',(1028,410,238,54),'dmh',mouse)
        else:
            self.text(surface,'JOIN WITH CODE',(1146,309),self.small,(196,209,201),True)
            pygame.draw.rect(surface,(18,52,38),self.code_rect,border_radius=8);pygame.draw.rect(surface,(255,215,85) if code_active else (215,226,219),self.code_rect,3 if code_active else 2,border_radius=8)
            display=(room_code or '5-digit code')+('|' if code_active else '')
            color=(250,243,216) if room_code else (139,160,150)
            label=self.font.render(display,True,color);surface.blit(label,label.get_rect(center=self.code_rect.center))
            self.buttons.append((self.code_rect,'code'))
            self.button(surface,'CREATE ROOM',(1028,415,238,52),'create',mouse)
            self.button(surface,'JOIN ROOM',(1028,481,238,52),'join',mouse,enabled=len(room_code)==5)
            self.text(surface,'The host chooses game settings and', (1146,568),self.small,(196,209,201),True)
            self.text(surface,'optional NPC seats inside the room.', (1146,593),self.small,(196,209,201),True)
        self.text(surface,'Uses the saved online relay automatically.',(1146,637),self.small,(173,193,183),True)
        return self.buttons
