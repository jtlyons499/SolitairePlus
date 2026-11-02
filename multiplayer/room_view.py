"""Readable six-seat table and host lobby; uses existing card/portrait art."""
import pygame
from mp_widgets import wooden_button,hand_type,TextInput
from mp_appearance import Appearance
from mp_profile import MultiplayerProfile
from mp_presentation import Presentation
from mp_showdown import payout_lines,compact_result
from texas_holdem_ui import get_card_key as card_key,draw_holdem_glossy_button,get_holdem_fonts

class RoomView:
    def __init__(self,surface,assets,appearance=None,options=None,sound=None):
        self.appearance=appearance or Appearance(MultiplayerProfile());self.presentation=Presentation(self.appearance,options,sound);self.details=False;self.details_scroll=0;self.history_index=-1;self.mouse=(-1,-1);self.badge_rects=[];self.dragging=False;self.slider=None;self.minimum=0;self.maximum=0;self.log_scroll=0
        self.surface=surface;self.assets=assets;self.buttons=[];self.raise_amount=100;self.hand=-1;self.editing=False;self.amount_text='';self.bet_input=TextInput()
        try:
            fonts=get_holdem_fonts();self.font=fonts['small'];self.small=fonts['tiny'];self.large=fonts['title']
        except Exception:
            self.font=pygame.font.SysFont("georgia",23);self.small=pygame.font.SysFont("georgia",18);self.large=pygame.font.SysFont("georgia",29)
    def text(self,text,x,y,font=None,color=(246,237,207)):
        self.surface.blit((font or self.font).render(str(text),True,color),(x,y))
    def button(self,label,rect,action,enabled=True):
        rect=pygame.Rect(rect)
        font=self.small if self.small.size(label)[0]<=rect.w-14 else pygame.font.SysFont('georgia',max(12,int(18*(rect.w-14)/self.small.size(label)[0])))
        draw_holdem_glossy_button(self.surface,rect,label,self.mouse,font,enabled,attention=enabled and action=='check_call')
        if enabled:self.buttons.append((rect,action))
    def event(self,event,mouse,table):
        if self.details:
            if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:self.details=False
            elif event.type==pygame.MOUSEWHEEL:self.details_scroll=max(0,self.details_scroll-event.y)
            elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                for rect,action in self.buttons:
                    if not rect.collidepoint(mouse):continue
                    if action=='close_details':self.details=False
                    elif action=='history_prev':self.history_index=max(0,self.history_index-1);self.details_scroll=0
                    elif action=='history_next':self.history_index+=1;self.details_scroll=0
                    break
            return True
        if event.type==pygame.MOUSEWHEEL:self.log_scroll=max(0,self.log_scroll-event.y);return True
        if event.type==pygame.MOUSEBUTTONUP:self.dragging=False
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and self.slider and self.slider.collidepoint(mouse):self.dragging=True
        if self.dragging and event.type in (pygame.MOUSEMOTION,pygame.MOUSEBUTTONDOWN):
            fraction=max(0,min(1,(mouse[0]-self.slider.x)/self.slider.w))
            self.raise_amount=round(self.minimum+fraction*(self.maximum-self.minimum));return True
        if self.editing and event.type==pygame.KEYDOWN and getattr(event,'mod',0) & pygame.KMOD_CTRL:
            self.amount_text=self.bet_input.event(event,self.amount_text,7,digits=True);self.raise_amount=int(self.amount_text or 0);return True
        if event.type==pygame.TEXTINPUT and self.editing:
            self.amount_text=self.bet_input.event(event,self.amount_text,7,digits=True)
            self.raise_amount=int(self.amount_text or 0);return True
        if event.type==pygame.KEYDOWN and self.editing:
            if event.key==pygame.K_BACKSPACE:self.amount_text=self.amount_text[:-1];self.raise_amount=int(self.amount_text or 0)
            elif event.key in (pygame.K_RETURN,pygame.K_KP_ENTER):table.act('bet_raise',self.raise_amount);self.editing=False;pygame.key.stop_text_input()
            elif event.key==pygame.K_ESCAPE:self.editing=False;pygame.key.stop_text_input()
            return True
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            for rect,action in self.buttons:
                if rect.collidepoint(mouse):
                    if action=='copy':
                        try:pygame.scrap.put_text(table.code)
                        except pygame.error:table.status='Room code: '+table.code
                    elif isinstance(action,tuple):
                        if action[0]=='npc':table.authority.configure(seat=action[1],delta=action[2])
                        elif action[0]=='stack':table.authority.configure(stack=action[1])
                        elif action[0]=='amount':self.raise_amount=action[1]
                        elif action[0]=='allin':
                            if action[1]<=table.game.current_bet:table.act('check_call')
                            else:table.act('bet_raise',action[1])
                    elif action=='edit':self.editing=True;self.amount_text='';self.bet_input=TextInput();pygame.key.start_text_input()
                    elif action=='details':self.details=True;self.details_scroll=0;self.history_index=len(getattr(table,'payout_history',[]))-1
                    elif action=='raise':table.act('bet_raise',self.raise_amount)
                    else:table.act(action)
                    return True
        return False
    def card(self,card,x,y,w=66,h=92,key=None):
        image=self.assets.cards.get(card_key(card),self.assets.back) if card else self.assets.back
        x,y,w,h,hidden=self.presentation.card_position(key,x,y,w,h,pygame.time.get_ticks())
        if hidden:image=self.assets.back
        # Single-player-style depth: a small shadow keeps cards readable over
        # custom felts and makes deal animations feel less flat.
        shadow=pygame.Surface((max(1,w),max(1,h)),pygame.SRCALPHA)
        pygame.draw.rect(shadow,(0,0,0,80),shadow.get_rect(),border_radius=max(3,w//12))
        self.surface.blit(shadow,(x+4,y+5))
        self.surface.blit(pygame.transform.smoothscale(image,(w,h)),(x,y))
    def draw(self,table,mouse=None):
        if mouse is not None:self.mouse=mouse
        s=self.surface;self.appearance.background(s);self.buttons=[];self.slider=None
        back=self.appearance.selected('back',self.assets.back.get_size())
        if back:self.assets.back=back
        logo=self.appearance.image('assets/poker/logos/texas_holdem.png',(225,76))
        if logo:s.blit(logo,(20,92))
        else:self.text('HOLD’EM',24,105,self.large)
        code_rect=pygame.Rect(20,15,310,40)
        self.text('Room Code: '+(table.code or '…'),24,23)
        if table.code:self.buttons.append((code_rect,'copy'))
        if code_rect.collidepoint(self.mouse) and table.code and not self.details:
            self.panel((350,20,120,30));self.text('copy code',361,23,self.small)
        self.text(table.status[:95],430,66,self.small)
        if table.failed:
            self.text('Connection ended. Leave and create/join a new room.',230,325,self.large);return
        m=table.message
        if m['type']=='connecting':self.text('Connecting to relay…',440,325,self.large);return
        if m['type'] in ('lobby','waiting'):
            self.text('Room lobby' if m['type']=='lobby' else 'Joining between hands',430,125,self.large)
            for i,seat in enumerate(m['seats']):
                y=190+i*62
                self.text(f"Seat {i+1}  •  {seat['kind']}  •  {seat['name']}",250,y)
                self.text(('Connected' if seat['connected'] else 'Disconnected') if seat['kind']=='Human' else 'Computer player',835,y,self.small)
                if table.hosting and m['type']=='lobby' and seat['kind']=='NPC':
                    self.button('Previous',(1050,y-5,90,36),('npc',i,-1));self.button('Next',(1150,y-5,70,36),('npc',i,1))
            self.text('Starting chips per seat: $'+str(m['starting_stack']),250,585)
            if table.hosting and m['type']=='lobby':
                for j,value in enumerate((1000,5000,10000,25000)):self.button('$'+str(value),(250+j*125,625,112,40),('stack',value))
                self.button('Start table',(860,625,260,50),'start',bool(table.code))
            if m.get('waiting_names'):self.text('Waiting: '+', '.join(m['waiting_names']),250,710,self.small)
            return
        g=table.game;now=pygame.time.get_ticks()
        if self.presentation.hand!=g.hand_number:self.log_scroll=0
        self.presentation.update(g,now);self.badge_rects=[]
        self.appearance.felt(s,pygame.Rect(174,176,1030,405))
        self.panel((548,275,330,82))
        self.text(f'Blinds  ${g.small_blind} / ${g.big_blind}',565,282,self.small)
        pot_label=('Last pot' if g.hand_complete else 'Pot')+f': ${g.pot if not g.hand_complete else g.last_resolved_pot:,}'
        image=self.font.render(pot_label,True,(246,237,207))
        if image.get_width()>205:image=pygame.transform.smoothscale(image,(205,image.get_height()))
        s.blit(image,(565,309))
        stage=(g.current_stage or 'preflop').replace('_',' ').title()
        self.text(f'Hand {g.hand_number}  •  {stage}',580,337,self.small,(218,225,216))
        for i,card in enumerate(g.community_cards):self.card(card,431+i*103,374,96,134,key=('board',i))
        # Cards, avatar and compact name/stack badges echo the single-player table.
        positions=[(525,668),(85,400),(335,200),(658,140),(992,200),(1055,425)]
        stacks=[g.player_stack,*g.npc_stacks];hands=[g.player_hand,*g.npc_hands]
        folded=[g.player_folded,*g.npc_folded];actions=[g.player_action_text,*g.npc_action_texts]
        physical=[m['physical_seat']]+[i for i in range(6) if i!=m['physical_seat']]
        for i,(x,y) in enumerate(positions):
            active=g.current_actor==i and not g.hand_complete
            seat=m['seats'][physical[i]];name=g.names[i]
            display_name=('van Dijk' if 'van Dijk' in name else name.split()[0]) if seat['kind']=='NPC' else name
            if not folded[i] and (hands[i] or i in g.hand_seat_indexes):
                for j in range(2):self.card(hands[i][j] if len(hands[i])>j else None,x+32+j*(98 if i==0 else 53),y-(142 if i==0 else 85),96 if i==0 else 60,134 if i==0 else 84,key=('seat',i,j))
            avatar=pygame.Rect(x-40,y-3,64,64)
            if active:
                pygame.draw.ellipse(s,(239,196,77),avatar.inflate(10,10),4)
            if seat['kind']=='Human':
                public=table.public_profiles.get(seat.get('identity'),{})
                self.appearance.avatar(s,public,avatar,name)
                dot=(105,220,125) if seat.get('connected') else (205,83,76)
                pygame.draw.circle(s,dot,(avatar.right-3,avatar.bottom-3),7)
                pygame.draw.circle(s,(20,22,22),(avatar.right-3,avatar.bottom-3),7,2)
            elif i>0:self.assets.portrait(g.npcs[i-1],avatar)
            label=self.font.render(display_name,True,(246,237,207))
            maximum=260 if i==0 else 210
            if label.get_width()>maximum-20:label=pygame.transform.smoothscale(label,(maximum-20,label.get_height()))
            money=self.small.render(f'${stacks[i]:,}',True,(246,237,207))
            width=min(maximum,max(78,label.get_width()+20,money.get_width()+20))
            badge=pygame.Rect(x+25,y,width,38);self.badge_rects.append(badge)
            winner=g.hand_complete and i in g.winner_indexes
            self.panel(badge,active);s.blit(label,(x+35,y+5))
            money_rect=pygame.Rect(x+25,y+40,width,29);self.panel(money_rect);s.blit(money,money.get_rect(center=money_rect.center))
            if winner:
                pygame.draw.rect(s,(138,228,128),badge.inflate(4,4),4,border_radius=12)
                crown=self.small.render('WINNER',True,(157,239,155));s.blit(crown,(badge.right+7,badge.y+7))
            action=('Disconnected' if not seat['connected'] else 'Busted' if stacks[i]==0 and g.hand_complete else 'All in' if stacks[i]==0 and i in g.hand_seat_indexes else 'Sitting out' if physical[i] in m.get('resting_seats',[]) and i not in g.hand_seat_indexes else 'Folded' if folded[i] else actions[i])
            if action:
                action=action[:26];action_width=min(210,max(78,self.small.size(action)[0]+18))
                self.panel((x+25,y+72,action_width,27));self.text(action,x+34,y+75,self.small)
            roles=[]
            if g.dealer_index==i:roles.append('D')
            if g.small_blind_index==i:roles.append('SB')
            if g.big_blind_index==i:roles.append('BB')
            if roles:
                rx=x-40
                for role in roles:
                    colors={'D':((118,88,22),(245,205,90)),'SB':((48,68,88),(155,190,220)),'BB':((88,44,44),(220,145,145))}
                    fill,border=colors.get(role,((35,50,48),(180,190,185)))
                    rw=30 if role=='D' else 38;rr=pygame.Rect(rx,y-32,rw,24)
                    pygame.draw.rect(s,fill,rr,border_radius=8);pygame.draw.rect(s,border,rr,2,border_radius=8)
                    txt=self.small.render(role,True,(255,255,255));s.blit(txt,txt.get_rect(center=rr.center));rx+=rw+5
        self.panel((20,610,365,140));self.text('Game Log',35,620)
        self.button('Payout History',(195,618,175,30),'details',bool(getattr(table,'last_payout',None)) or g.hand_complete)
        self.button('Rejoin next hand' if m.get('sit_out') else 'Sit out next hand',(20,566,205,32),'sit_out',not table.pending)
        self.panel((920,566,420,38))
        description=hand_type(g)
        if description.endswith('-high'):description='High card: '+description[:-5]
        hand_label=self.font.render(description,True,(246,237,207))
        if hand_label.get_width()>390:hand_label=pygame.transform.smoothscale(hand_label,(390,hand_label.get_height()))
        s.blit(hand_label,hand_label.get_rect(midleft=(935,585)))
        if g.player_stack<=0 and (g.hand_complete or 0 not in g.hand_seat_indexes):
            self.button('Buy back $'+str(m.get('starting_stack',g.starting_stack)),(235,566,200,32),'buyback',not table.pending)
        lines=m.get('public_log',g.get_hand_history_lines())
        end=max(0,len(lines)-self.log_scroll);shown=lines[max(0,end-4):end]
        clip=s.get_clip();s.set_clip(pygame.Rect(32,655,340,87))
        for j,line in enumerate(shown):self.text(line,35,655+j*21,self.small)
        s.set_clip(clip)
        self.panel((920,610,420,140))
        if g.hand_complete:
            ready=m.get('ready_count',0);total=m.get('ready_total',1)
            summary=compact_result(g)
            for j,line in enumerate(summary):
                label=self.small.render(line,True,(246,237,207))
                if label.get_width()>385:label=pygame.transform.smoothscale(label,(385,label.get_height()))
                s.blit(label,(937,619+j*23))
            self.text('Next hand in '+str(m.get('next_hand_seconds',6))+' seconds' if m.get('next_hand_seconds',6)>0 else 'Waiting for players to rejoin',937,678,self.small)
        else:
            active=g.current_actor==0 and g.actor_needs_action(0) and not table.pending
            if active:
                turn_rect=pygame.Rect(920,575,420,30)
                layer=pygame.Surface(turn_rect.size,pygame.SRCALPHA);layer.fill((125,91,18,225));s.blit(layer,turn_rect)
                pygame.draw.rect(s,(242,202,79),turn_rect,2,border_radius=8)
                turn=self.small.render('YOUR TURN',True,(255,248,218));s.blit(turn,turn.get_rect(center=turn_rect.center))
            call=g.get_player_amount_to_call();minimum=g.get_minimum_raise_to() if g.current_bet else g.big_blind
            maximum=g.player_stack+g.player_round_bet
            if self.hand!=g.hand_number:self.hand=g.hand_number;self.raise_amount=minimum;self.editing=False;self.log_scroll=0
            self.raise_amount=min(maximum,max(minimum,self.raise_amount))
            canraise=active and (not g.current_bet or g.can_player_raise()) and maximum>g.current_bet
            self.button('FOLD',(935,621,90,40),'fold',active)
            self.button('Call $'+str(min(call,g.player_stack)) if call else 'CHECK',(1035,621,135,40),'check_call',active)
            self.button(('Raise $' if g.current_bet else 'Bet $')+str(self.raise_amount),(1180,621,145,40),'raise',canraise)
            self.minimum=min(minimum,maximum);self.maximum=maximum
            rail=pygame.Rect(935,677,242,10);pygame.draw.rect(s,(90,104,106),rail,border_radius=5)
            fraction=(self.raise_amount-self.minimum)/max(1,maximum-self.minimum)
            pygame.draw.circle(s,(141,185,221),(round(rail.x+rail.w*fraction),rail.centery),9)
            if canraise:self.slider=rail.inflate(0,18)
            self.button(self.amount_text+'|' if self.editing else 'BET $',(1190,671,135,29),'edit',canraise)
            for j,(label,value) in enumerate((('MIN',minimum),('½',max(minimum,g.current_bet+g.pot//2)),('POT',max(minimum,g.current_bet+g.pot)),('ALL IN',maximum))):
                action=('allin',maximum) if label=='ALL IN' else ('amount',value)
                self.button(label,(935+j*99,710,92,29),action,active if label=='ALL IN' else canraise)
        self.presentation.draw(s,g,now,self.small)
        if g.hand_complete:
            result=(getattr(g,'result_text','') or '').strip()
            if result:
                banner=pygame.Rect(365,514,635,46);layer=pygame.Surface(banner.size,pygame.SRCALPHA);layer.fill((12,18,18,220));s.blit(layer,banner)
                pygame.draw.rect(s,(235,190,70),banner,2,border_radius=12)
                text=self.small.render(result,True,(255,245,214))
                if text.get_width()>banner.w-30:text=pygame.transform.smoothscale(text,(banner.w-30,text.get_height()))
                s.blit(text,text.get_rect(center=banner.center))
        if self.details:
            history=getattr(table,'payout_history',[])
            if history:
                self.history_index=max(0,min(self.history_index,len(history)-1))
                self.draw_details(history[self.history_index])
                self.button('Previous',(745,165,115,38),'history_prev',self.history_index>0)
                self.button('Next',(875,165,115,38),'history_next',self.history_index<len(history)-1)
            else:self.draw_details(getattr(table,'last_payout',None) or g)

        if m.get('waiting_names'):self.text('Joining next hand: '+', '.join(m['waiting_names']),390,748,self.small)

    def panel(self,rect,active=False):
        rect=pygame.Rect(rect);layer=pygame.Surface(rect.size,pygame.SRCALPHA)
        pygame.draw.rect(layer,(12,23,25,220),layer.get_rect(),border_radius=10);self.surface.blit(layer,rect)
        pygame.draw.rect(self.surface,(230,190,72) if active else (144,165,159),rect,3 if active else 1,border_radius=10)

    def draw_details(self,g):
        s=self.surface;shade=pygame.Surface(s.get_size(),pygame.SRCALPHA);shade.fill((0,0,0,185));s.blit(shade,(0,0))
        self.panel((215,145,930,475));self.text('Payout History • Hand '+str(g.hand_number),240,163,self.large)
        self.button('Close',(1020,165,105,38),'close_details')
        lines=payout_lines(g)
        lines+=['Revealed hands:']+[g.names[int(i)]+': '+hand for i,hand in getattr(g,'showdown_hands',{}).items()]
        lines.append('Amounts above are gross payouts; your own wagers were already deducted.')
        # Wrap whole explanations rather than cutting names or hand kickers off.
        wrapped=[]
        for line in lines:
            words=line.split();current=''
            for word in words:
                candidate=(current+' '+word).strip()
                if self.small.size(candidate)[0]>850 and current:wrapped.append(current);current=word
                else:current=candidate
            wrapped.append(current)
        self.details_scroll=min(self.details_scroll,max(0,len(wrapped)-14))
        for j,line in enumerate(wrapped[self.details_scroll:self.details_scroll+14]):self.text(line,240,220+j*25,self.small)
        self.text('Scroll for more • Esc closes',240,588,self.small)
