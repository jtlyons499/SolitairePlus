"""Solitaire Multiplayer foundation: standalone local Hold'em, LAN and room-code relay."""
import os
from pathlib import Path
from multiplayer_paths import ROOT
from runtime_support import bootstrap
bootstrap()
import pygame
from mp_widgets import wooden_button,TextInput
from texas_holdem_ui import draw_holdem_glossy_button
from standalone_table import StandaloneTable
from lan_session import OnlineTable
from room_session import RoomTable
from room_view import RoomView
import connection_settings
from mp_profile import MultiplayerProfile
from mp_appearance import Appearance
from mp_profile_ui import ProfileScreen
from mp_options import Options
from standalone_view import TableView
import texas_holdem_ui as ui
from poker_recap import handle_recap_action
from dead_mans_hand_pvp import DeadMansHandPvPMode

from multiplayer_paths import ROOT

def main():
    os.chdir(ROOT)
    pygame.init();options=Options();screen=options.display()
    pygame.display.set_caption('Solitaire+ Poker Table — Multiplayer')
    canvas=pygame.Surface((1366,768));clock=pygame.time.Clock();font=pygame.font.Font(None,36)
    profile=MultiplayerProfile();appearance=Appearance(profile);profile_screen=ProfileScreen(profile,appearance)
    view=TableView(canvas);room_view=RoomView(canvas,view,appearance,options);saved=connection_settings.load();name=profile.data['name'] if profile.path.exists() else saved.get('name','');address='127.0.0.1';room_code='';relay_address=saved.get('relay_address') or 'tcp://yamanote.proxy.rlwy.net:40274';focus='name';text_input=TextInput();table=None;running=True;pygame.key.start_text_input()
    sounds={}
    if pygame.mixer.get_init():
        for folder in ('assets/sounds','assets/sfx'):
            for path in (ROOT/folder).rglob('*'):
                if path.suffix.lower() not in ('.wav','.ogg','.mp3'):continue
                try:sounds[path.stem]=pygame.mixer.Sound(path)
                except pygame.error:continue
    def sound(key):
        aliases={'chip_move':'chips_1','win':'hand_win'}
        key=key if key in sounds else aliases.get(key,key)
        if key in sounds and options.values['sound']:
            sounds[key].set_volume(options.values['volume']/100);sounds[key].play()
    room_view.presentation.sound=sound
    name_rect=pygame.Rect(423,290,520,52);start_rect=pygame.Rect(183,460,300,60)
    host_rect=pygame.Rect(533,460,300,60);join_rect=pygame.Rect(883,460,300,60)
    address_rect=pygame.Rect(423,380,520,52);leave_rect=pygame.Rect(1130,15,210,40);ready_rect=pygame.Rect(800,20,280,40)
    relay_rect=pygame.Rect(183,590,520,48);code_rect=pygame.Rect(723,590,460,48)
    quit_rect=pygame.Rect(740,15,160,40)
    options_rect=pygame.Rect(915,15,150,40)
    profile_rect=pygame.Rect(1110,15,230,40)
    create_rect=pygame.Rect(363,660,300,55);room_join_rect=pygame.Rect(703,660,300,55)
    dmh_pvp_rect=pygame.Rect(18,15,210,40);pvp_mode=None
    while running:
        sx,sy=screen.get_size();scale=min(sx/1366,sy/768);offset=((sx-1366*scale)/2,(sy-768*scale)/2)
        raw=pygame.mouse.get_pos();mouse=((raw[0]-offset[0])/scale,(raw[1]-offset[1])/scale)
        profile_rect.y=65 if table is not None else 15
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                if pvp_mode is not None:pvp_mode.close()
                running=False;continue
            if pvp_mode is not None and event.type==pygame.KEYDOWN and event.key==pygame.K_F11:
                options.values['fullscreen']=not options.values['fullscreen'];options.save();screen=options.display();continue
            if pvp_mode is not None:
                pvp_mode.handle_event(event,mouse)
                if pvp_mode.closed:
                    pvp_mode=None;pygame.key.start_text_input()
                continue
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11:
                options.values['fullscreen']=not options.values['fullscreen'];options.save();screen=options.display();continue
            if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                if options.open:clickable=[rect for rect,action in options.buttons]
                elif profile_screen.open:clickable=[rect for rect,action in profile_screen.buttons]
                else:
                    clickable=[options_rect,profile_rect]
                    if table is None:clickable += [quit_rect,start_rect,host_rect,join_rect,create_rect,room_join_rect,dmh_pvp_rect]
                    else:
                        clickable.append(leave_rect)
                        if isinstance(table,RoomTable):clickable += [rect for rect,action in room_view.buttons]
                if any(rect.collidepoint(mouse) for rect in clickable):sound('button_click')
            if table is None and not options.open and not profile_screen.open and event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and quit_rect.collidepoint(mouse):
                running=False
                continue
            if options.open:
                if options.event(event,mouse,table):screen=options.display()
                if not options.open and table is None:pygame.key.start_text_input()
                continue
            if (event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and options_rect.collidepoint(mouse)) or (event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE and not profile_screen.open and not room_view.editing and not room_view.details):
                options.open=True;pygame.key.stop_text_input();continue
            if profile_screen.open:
                profile_screen.event(event,mouse,table if isinstance(table,RoomTable) else None)
                name=profile.data['name']
                if not profile_screen.open and table is None:pygame.key.start_text_input()
                continue
            if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and profile_rect.collidepoint(mouse):
                if table is None and name.strip():profile.data['name']=name.strip();profile.save()
                profile_screen.open=True;continue
            if table is None:
                if event.type in (pygame.TEXTINPUT,pygame.KEYDOWN):
                    values={'name':name,'address':address,'relay':relay_address,'code':room_code}
                    value=text_input.event(event,values[focus],32 if focus=='name' else 5 if focus=='code' else 128,uppercase=focus=='code')
                    if focus=='name':name=value
                    elif focus=='address':address=value
                    elif focus=='relay':relay_address=value
                    else:room_code=value
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                    text_input.selected=False
                    if name_rect.collidepoint(mouse):focus='name'
                    elif address_rect.collidepoint(mouse):focus='address'
                    elif relay_rect.collidepoint(mouse):focus='relay'
                    elif code_rect.collidepoint(mouse):focus='code'
                    elif create_rect.collidepoint(mouse):table=RoomTable(name,True,relay_address,profile=profile)
                    elif room_join_rect.collidepoint(mouse):table=RoomTable(name,False,relay_address,code=room_code,profile=profile)
                    elif host_rect.collidepoint(mouse):table=OnlineTable(name,True)
                    elif join_rect.collidepoint(mouse):table=OnlineTable(name,False,address.strip() or '127.0.0.1')
                    elif start_rect.collidepoint(mouse):table=StandaloneTable(name)
                    elif dmh_pvp_rect.collidepoint(mouse):
                        profile.data['name']=name.strip() or 'Player';profile.save();connection_settings.save(name,relay_address)
                        pvp_mode=DeadMansHandPvPMode(profile.data['name'],relay_address,sound=sound);pygame.key.stop_text_input()
                if event.type==pygame.KEYDOWN and event.key==pygame.K_RETURN:
                    if focus=='code' and room_code:table=RoomTable(name,False,relay_address,code=room_code,profile=profile)
                    elif focus=='relay':table=RoomTable(name,True,relay_address,profile=profile)
                    else:focus='relay'
                if table is not None:
                    profile.data['name']=name.strip() or 'Player';profile.save();connection_settings.save(name,relay_address);pygame.key.stop_text_input()
                continue
            online=isinstance(table,(OnlineTable,RoomTable))
            if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and leave_rect.collidepoint(mouse):
                if online:table.close()
                table=None;pygame.key.start_text_input();continue
            if isinstance(table,RoomTable):
                room_view.event(event,mouse,table);continue
            if online and not table.playable:
                if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
                    table.close();table=None;pygame.key.start_text_input()
                continue
            g=table.game
            if online and g.hand_complete and event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and ready_rect.collidepoint(mouse):
                if not g.you_ready:table.act('next_hand')
                continue
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:ui.holdem_options_open=not ui.holdem_options_open
                else:ui.handle_holdem_manual_bet_key(event,g)
            if event.type==pygame.MOUSEMOTION:ui.drag_holdem_bet_slider(mouse)
            if event.type==pygame.MOUSEBUTTONUP:ui.stop_holdem_bet_slider_drag()
            if event.type==pygame.MOUSEWHEEL:
                ui.holdem_log_scroll=max(0,ui.holdem_log_scroll-event.y)
            if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                if ui.handle_holdem_options_click(mouse) or ui.handle_holdem_panel_click(mouse):continue
                if ui.handle_holdem_manual_bet_click(mouse,g):continue
                if ui.update_holdem_bet_slider(mouse,g):continue
                action=ui.get_texas_holdem_action(mouse,g)
                if not action:continue
                if action in ('options','return'):continue  # Outer Options/Leave Table own these controls.
                elif action=='next_hand' and table.finished:
                    
                    if isinstance(table,(OnlineTable,RoomTable)):table.close()
                    table=None;pygame.key.start_text_input()
                elif action.startswith('recap_'):handle_recap_action(g,action)
                elif table.act(action):sound('card_move')
        if pvp_mode is not None:
            pvp_mode.update(min(0.05,max(0.0,clock.get_time()/1000.0)))
            pvp_mode.draw(canvas,mouse)
            screen.fill((0,0,0));screen.blit(pygame.transform.smoothscale(canvas,(round(1366*scale),round(768*scale))),offset);pygame.display.flip();clock.tick(60)
            continue
        if table is None:
            appearance.background(canvas)
            logo=appearance.image('assets/multiplayer/logo.png',(900,198)) or appearance.image('assets/ui/menu_ui/floating_logo.png',(620,175))
            if logo:canvas.blit(logo,logo.get_rect(center=(683,163)))
            for text,y in [('Your name',265),('Join address: localhost or the host’s LAN IP',355),('Relay address',560)]:
                label=font.render(text,True,(245,233,201));canvas.blit(label,label.get_rect(center=(443 if y==560 else 683,y)))
            label=font.render('Room code (joining only)',True,(245,233,201));canvas.blit(label,label.get_rect(center=(953,560)))
            for rect,value,field in ((name_rect,name,'name'),(address_rect,address,'address'),(relay_rect,relay_address,'relay'),(code_rect,room_code,'code')):
                pygame.draw.rect(canvas,(73,98,113) if focus==field and text_input.selected else (32,76,57),rect);pygame.draw.rect(canvas,(229,194,110) if focus==field else (130,166,145),rect,2)
                clip=canvas.get_clip();canvas.set_clip(rect.inflate(-12,-6))
                canvas.blit(font.render(value+('|' if focus==field else ''),True,(250,243,216)),(rect.x+15,rect.y+15));canvas.set_clip(clip)
            for rect,label in ((start_rect,'Local Practice'),(host_rect,'Host Table'),(join_rect,'Join LAN'),(create_rect,'Create Room'),(room_join_rect,'Join Room')):
                wooden_button(canvas,appearance,rect,label,font,hover=rect.collidepoint(mouse))
        else:
            online=isinstance(table,(OnlineTable,RoomTable))
            if online or not ui.holdem_options_open:
                key=table.update(pygame.time.get_ticks())
                if key:sound(key)
            if isinstance(table,RoomTable):room_view.draw(table,mouse)
            elif not online or table.playable:
                ui.draw_texas_holdem(canvas,mouse,table.game,view.cards,view.back,view.background,view.title,view.button,view.portrait,font,font,font,table.name,view.felt,show_utility_buttons=False)
            else:
                appearance.background(canvas);label=font.render(table.status,True,(245,233,201));canvas.blit(label,label.get_rect(center=(683,320)))
                label=font.render('Share the room code and relay address with your friend.',True,(245,233,201));canvas.blit(label,label.get_rect(center=(683,385)))
            draw_holdem_glossy_button(canvas,leave_rect,'Leave table',mouse,pygame.font.Font(None,26))
            if isinstance(table,OnlineTable) and table.playable and table.game.hand_complete:
                alive=sum(stack>0 for stack in [table.game.player_stack,*table.game.npc_stacks])
                text='Table finished' if alive<2 else f'Ready ({table.game.ready_count}/2)' if table.game.you_ready else 'Ready for next hand'
                pygame.draw.rect(canvas,(65,96,77),ready_rect,border_radius=8);image=pygame.font.Font(None,26).render(text,True,(245,233,201));canvas.blit(image,image.get_rect(center=ready_rect.center))
            if isinstance(table,OnlineTable):
                label=pygame.font.Font(None,22).render(table.status,True,(245,233,201));canvas.blit(label,(450,72))
        if table is None:
            wooden_button(canvas,appearance,dmh_pvp_rect,"DMH PvP",pygame.font.Font(None,24),hover=dmh_pvp_rect.collidepoint(mouse))
            wooden_button(canvas,appearance,profile_rect,f'Edit Profile • Lv {profile.level}',pygame.font.Font(None,24),hover=profile_rect.collidepoint(mouse))
            wooden_button(canvas,appearance,options_rect,'Options',pygame.font.Font(None,26),hover=options_rect.collidepoint(mouse))
            wooden_button(canvas,appearance,quit_rect,'Quit Game',pygame.font.Font(None,26),hover=quit_rect.collidepoint(mouse))
        else:
            draw_holdem_glossy_button(canvas,profile_rect,f'Edit Profile • Lv {profile.level}',mouse,pygame.font.Font(None,24))
            draw_holdem_glossy_button(canvas,options_rect,'Options',mouse,pygame.font.Font(None,26))
        if profile_screen.open:profile_screen.draw(canvas,table)
        if options.open:options.draw(canvas,table)
        screen.fill((0,0,0));screen.blit(pygame.transform.smoothscale(canvas,(round(1366*scale),round(768*scale))),offset);pygame.display.flip();clock.tick(60)
    if isinstance(table,(OnlineTable,RoomTable)):table.close()
    pygame.key.stop_text_input();pygame.quit()

if __name__=='__main__':main()
