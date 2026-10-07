"""Profile slots, PNG import and multiplayer-only cosmetic selection."""
import pygame
from mp_widgets import TextInput,wooden_button


class ProfileScreen:
    def __init__(self,profile,appearance):
        self.profile=profile;self.appearance=appearance;self.open=False;self.buttons=[];self.field=None;self.text_input=TextInput();self.avatar_path='';self.message='';self.page={'background':0,'felt':0,'back':0}
        self.font=pygame.font.Font(None,30);self.small=pygame.font.Font(None,24);self.large=pygame.font.Font(None,44)

    def text(self,s,text,pos,font=None):s.blit((font or self.font).render(str(text),True,(244,236,211)),pos)

    def button(self,s,label,rect,action,enabled=True):
        rect=pygame.Rect(rect);wooden_button(s,self.appearance,rect,label,self.small,enabled)
        if enabled:self.buttons.append((rect,action))

    def draw(self,s,table=None):
        self.appearance.background(s);self.buttons=[]
        panel=pygame.Surface((1226,678),pygame.SRCALPHA);panel.fill((13,30,25,235));s.blit(panel,(70,45))
        self.text(s,'MULTIPLAYER PROFILE',(105,70),self.large)
        self.button(s,'Done',(1155,65,105,42),'close')
        for i in range(1,4):self.button(s,f'Profile {i}'+(' • Active' if i==self.profile.slot else ''),(105+(i-1)*185,130,170,40),('slot',i),table is None)
        self.text(s,f'Level {self.profile.level} • {self.profile.data["xp"]} XP • {self.profile.data["wins"]} winning hands',(105,193))
        self.text(s,'100 XP per level. Outright win: 20 XP. Split-only win: 10 XP.',(105,232),self.small)
        self.button(s,'Name: '+self.profile.data['name']+('|' if self.field=='name' else ''),(105,275,430,44),'name',table is None)
        self.appearance.avatar(s,self.profile.public(),pygame.Rect(1120,155,110,110),self.profile.data['name'])
        self.text(s,'Avatar PNG — paste its full path; recommended source: 256×256',(105,337),self.small)
        rect=pygame.Rect(105,374,640,44);pygame.draw.rect(s,(35,59,49),rect,border_radius=7)
        clip=s.get_clip();s.set_clip(rect.inflate(-12,-4));self.text(s,self.avatar_path+('|' if self.field=='avatar' else ''),(115,384),self.small);s.set_clip(clip)
        self.buttons.append((rect,'avatar'))
        self.button(s,'Load PNG',(760,374,145,44),'import');self.button(s,'Use initials',(920,374,145,44),'clear')
        for row,category in enumerate(('background','felt','back')):
            y=456+row*66;keys=list(self.profile.catalog[category]);self.page[category]%=len(keys)
            key=keys[self.page[category]];item=self.profile.catalog[category][key];required=self.profile.unlock_level(category,key)
            self.text(s,category.title(),(105,y+8))
            self.button(s,'‹',(275,y,45,42),('cycle',category,-1))
            self.text(s,item['name'],(335,y+8))
            self.button(s,'›',(650,y,45,42),('cycle',category,1))
            label='Selected' if self.profile.data['selected'][category]==key else 'Select' if required<=self.profile.level else f'Unlocks at level {required}'
            self.button(s,label,(720,y,240,42),('select',category,key),required<=self.profile.level)
            preview=self.appearance.image(item['path'],(160,46) if category!='back' else (33,46))
            if preview:s.blit(preview,(995,y))
        self.text(s,(self.message or self.profile.notice or 'These choices and unlocks belong only to Multiplayer.')[:110],(105,674),self.small)

    def event(self,event,mouse,table=None):
        changed=False
        if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:self.open=False;self.field=None;self.text_input=TextInput();pygame.key.stop_text_input();return True
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            for rect,action in self.buttons:
                if not rect.collidepoint(mouse):continue
                self.message=''
                if action=='close':self.open=False;self.field=None;self.text_input=TextInput();self.profile.save();pygame.key.stop_text_input()
                elif action in ('name','avatar'):
                    self.field=action;self.text_input.selected=False;pygame.key.start_text_input()
                elif action=='import':
                    try:self.profile.import_avatar(self.avatar_path);changed=True
                    except (OSError,ValueError,pygame.error) as error:self.message=str(error)[:110]
                elif action=='clear':self.profile.data['avatar']='';self.profile.save();changed=True
                elif isinstance(action,tuple):
                    if action[0]=='slot':self.profile.save();self.profile.load(action[1]);changed=True
                    elif action[0]=='cycle':self.page[action[1]]+=action[2]
                    elif action[0]=='select':self.profile.select(action[1],action[2]);changed=True
                break
        if self.field and event.type in (pygame.TEXTINPUT,pygame.KEYDOWN):
            value=self.profile.data['name'] if self.field=='name' else self.avatar_path
            value=self.text_input.event(event,value,32 if self.field=='name' else 500)
            if event.type==pygame.KEYDOWN and event.key in (pygame.K_RETURN,pygame.K_KP_ENTER):self.profile.save();pygame.key.stop_text_input()
            if self.field=='name':self.profile.data['name']=''.join(c for c in value if c.isprintable())[:32]
            elif self.field=='avatar':self.avatar_path=value[:500]
        if changed and table:table.refresh_profile()
        return True
