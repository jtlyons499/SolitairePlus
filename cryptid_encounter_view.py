"""Encounter composition: live cards, command panel, Docket and real hand cards."""
import pygame
from cryptid_cards import STYLE_COLORS
from cryptid_creatures import Action, HAND_LIMIT

ACTIVE_RECTS={1:pygame.Rect(154,109,300,420),0:pygame.Rect(502,109,300,420)}


def _fit(screen,surface,value,rect,size=28,color=None,bold=False):
    rect=pygame.Rect(rect);font=screen.renderer.font(size,bold)
    while font.size(value)[0]>rect.w and size>20:
        size-=1;font=screen.renderer.font(size,bold)
    old=surface.get_clip();surface.set_clip(rect)
    text=font.render(value,True,color or (241,237,220))
    surface.blit(text,text.get_rect(midleft=rect.midleft));surface.set_clip(old)


def _bar(screen,surface,rect,value,maximum,color,label):
    rect=pygame.Rect(rect)
    pygame.draw.rect(surface,(29,40,49),rect,border_radius=6)
    amount=max(0,min(1,value/max(1,maximum)))
    if amount:pygame.draw.rect(surface,color,(rect.x,rect.y,max(1,round(rect.w*amount)),rect.h),border_radius=6)
    pygame.draw.rect(surface,(159,179,177),rect,1,border_radius=6)
    font=screen.renderer.font(23,True)
    text=font.render(f'{label} {value}/{maximum}',True,(255,255,243))
    shadow=font.render(f'{label} {value}/{maximum}',True,(12,19,23))
    pos=text.get_rect(center=rect.center)
    surface.blit(shadow,pos.move(1,1));surface.blit(text,pos)


def draw_encounter(screen,surface,mouse):
    b=screen.battle
    if not b:return
    now=screen.feedback_now
    feedback=screen.feedback
    shown=feedback.visual_sides(b,now)
    busy=feedback.active
    legal=[] if busy else b.legal_actions(0)
    gold=(244,199,108);muted=(174,193,190);text=(240,235,220)
    # A restrained table with clear regions leaves the cards as the main artwork.
    if screen.renderer._image("background.png") is not None:
        tint = pygame.Surface((1366, 534), pygame.SRCALPHA)
        tint.fill((23, 41, 44, 135))
        surface.blit(tint, (0, 64))
    else:
        pygame.draw.rect(surface,(23,41,44),(0,64,1366,534))
    pygame.draw.rect(surface,(32,61,62),(0,598,1366,34))
    screen._text(surface,'RESERVES',16,76,22,muted,True)
    for seat in (1,0):
        side=shown[seat];rect=ACTIVE_RECTS[seat]
        label='OPPONENT' if seat else 'YOUR ACTIVE CARD'
        _fit(screen,surface,label, (rect.x,70,300,31),29,gold,True)
        if side.active:
            c=side.active;printed=b.card(c.card_id)
            dx,dy=feedback.offset(seat,now)
            screen._card(surface,c.card_id,rect.move(dx,dy),c,tag=('active',seat))
            _bar(screen,surface,(rect.x,535,300,23),c.hp,printed['hp'],(61,155,105),'HP')
            _bar(screen,surface,(rect.x,563,300,23),c.ap,printed['ap'],(60,120,188),'ARMOR')
            statuses=list(c.conditions)
            if c.guard:statuses.append('Guarded')
            if statuses:
                status_rect=pygame.Rect(rect.x+8,rect.y+8,284,30)
                pygame.draw.rect(surface,(20,35,40),status_rect,border_radius=5)
                _fit(screen,surface,' / '.join(s.title() for s in statuses),status_rect.inflate(-10,0),23,gold,True)
        else:
            pygame.draw.rect(surface,(30,53,55),rect,border_radius=12)
            screen._wrap(surface,'Choose a creature to send out.' if seat==0 else 'Awaiting opponent creature.',rect.x+25,rect.centery-25,250,30,text)
    pygame.draw.circle(surface,(22,67,75),(478,317),32)
    _fit(screen,surface,'VS',(458,297,48,42),34,gold,True)
    for i,c in enumerate(shown[1].docket):
        rect=pygame.Rect(28,110+i*145,82,115)
        screen._card(surface,c.card_id,rect,c,tag=('docket',1,i))
        screen._text(surface,f'{c.hp}H / {c.ap}A',24,rect.bottom+4,21,text,True)
    enemy=shown[1]
    screen._text(surface,f"KOs {enemy.knockouts}/3",18,538,22,muted)
    screen._text(surface,f"Hand {len(enemy.hand)}",18,558,22,muted)
    screen._text(surface,f"Deck {len(enemy.deck)}",18,578,22,muted)
    side=b.sides[0]
    screen._button(surface,(834,74,246,38),'Auto-end: '+('ON' if screen.auto_end else 'OFF'),('auto_end',),mouse,size=25,enabled=not busy)
    screen._button(surface,(1090,74,258,38),'Details / log',('damage',),mouse,size=25)
    screen._text(surface,f"FOCUS {shown[0].focus}/6  |  YOUR KOs {shown[0].knockouts}/3",836,120,29,gold,True)
    preview=None;hover_move=None
    if side.active:
        for i,mid in enumerate(b.card(side.active.card_id)['moves']):
            move=b.catalog.moves[mid];uses=side.active.uses[mid]
            choices=[a for a in legal if a.kind=='move' and a.index==i]
            rect=pygame.Rect(834+(i%2)*262,161+(i//2)*84,252,74)
            screen._button(surface,rect,'',('actions',choices),mouse,enabled=bool(choices))
            _fit(screen,surface,move['name'],(rect.x+12,rect.y+5,228,32),29,gold if choices else muted,True)
            detail=f"Focus {move['focus']} | "+('Unlimited' if uses is None else f'{uses} uses')
            _fit(screen,surface,detail,(rect.x+12,rect.y+40,228,27),23,text if choices else muted)
            if mouse and rect.collidepoint(mouse) and not busy:
                hover_move=move;preview=screen._preview(move)
        if Action('struggle') in legal:
            screen._button(surface,(834,329,252,38),'Struggle — free attack',('act',Action('struggle')),mouse,size=24)
    panel=pygame.Rect(834,376,514,210)
    pygame.draw.rect(surface,(19,33,38),panel,border_radius=12)
    old=surface.get_clip();surface.set_clip(panel.inflate(-20,-16))
    y=389
    if busy:
        y=screen._wrap(surface,feedback.message,850,y,480,29,text)+12
        if feedback.knockouts and feedback.elapsed(now)>680:
            screen._text(surface,'Creature knocked out!',850,y,30,gold,True)
    elif hover_move:
        y=screen._wrap(surface,hover_move['name'],850,y,480,30,gold)+8
        if preview:
            y=screen._wrap(surface,f"Will deal {preview['ap_loss']} armor + {preview['hp_loss']} HP.",850,y,480,29,text)+8
            y=screen._wrap(surface,preview['steps'][1]+'. '+('Native style bonus applies.' if any('Native' in x for x in preview['steps']) else ''),850,y,480,25,muted)+8
            if preview['ap_loss']+preview['hp_loss']>=b.sides[1].active.hp+b.sides[1].active.ap:
                screen._text(surface,'Predicted knockout!',850,y,27,gold,True)
        else:y=screen._wrap(surface,hover_move['description'],850,y,480,27,text)+8
        reason=('Move already used this turn.' if side.move_used else 'Not enough Focus.' if side.focus<hover_move['focus'] else 'No uses remaining.' if side.active.uses[hover_move['id']]==0 else '')
        if reason:screen._wrap(surface,reason,850,y,480,25,muted)
    elif screen.selected_hand is not None and 0<=screen.selected_hand<len(side.hand):
        card=b.card(side.hand[screen.selected_hand])
        y=screen._wrap(surface,card['name'],850,y,480,30,gold)+8
        value=card['description'] if card['kind']!='creature' else 'Deploy to your Docket, then switch it into battle. '+card['description']
        screen._wrap(surface,value,850,y,480,26,text)
    else:
        y=screen._wrap(surface,screen.notice or screen._battle_status(),850,y,480,29,gold)+12
        y=screen._wrap(surface,feedback.message,850,y,480,27,text)+12
        if b.arena:
            screen._wrap(surface,f"Arena: x{b.arena['factor']:g} ({', '.join(b.arena['styles'])}), {b.arena['duration']} turns left.",850,y,480,24,muted)
        elif screen.auto_end:
            screen._wrap(surface,'Play support before your move. Auto-end OFF lets you continue afterward.',850,y,480,24,muted)
    surface.set_clip(old)
    feedback.draw(surface,ACTIVE_RECTS,now,screen.renderer.font,STYLE_COLORS)
    # Two explicitly separate areas: deployed creatures and cards still in hand.
    screen._text(surface,'YOUR DOCKET',16,604,24,gold,True)
    screen._text(surface,f'YOUR HAND ({len(side.hand)})',322,604,24,gold,True)
    for i,c in enumerate(shown[0].docket):
        rect=pygame.Rect(16+i*98,638,80,112)
        screen._card(surface,c.card_id,rect,c,tag=('docket',0,i))
        _fit(screen,surface,f'{c.hp}H {c.ap}A',(rect.x,751,80,17),20,text)
    screen.hand_page=max(0,min(screen.hand_page,max(0,(len(side.hand)-1)//8)))
    start=screen.hand_page*8
    for j,cid in enumerate(side.hand[start:start+8]):
        index=start+j;rect=pygame.Rect(322+j*104,635,92,129)
        screen._card(surface,cid,rect,tag=('hand',index),selected=index==screen.selected_hand)
        # Label on the lower part of the actual card, not a replacement text tile.
        label=pygame.Rect(rect.x+2,rect.bottom-43,rect.w-4,41)
        pygame.draw.rect(surface,(24,44,47),label,border_radius=5)
        _fit(screen,surface,b.card(cid)['name'],(label.x+3,label.y+2,label.w-6,20),23,gold,True)
        card=b.card(cid)
        _fit(screen,surface,'F '+str(1 if card['kind']=='creature' else card['focus']),(label.x+3,label.y+21,label.w-6,18),21,text)
    if len(side.hand)>8:
        screen._button(surface,(878,599,116,30),'Previous',('hand_page',-1),mouse,enabled=screen.hand_page>0,size=21)
        screen._button(surface,(1004,599,116,30),'Next',('hand_page',1),mouse,enabled=start+8<len(side.hand),size=21)
    selected=[a for a in legal if a.kind=='play' and a.index==screen.selected_hand]
    screen._button(surface,(1170,635,178,37),'Play selected',('actions',selected),mouse,enabled=bool(selected),size=24)
    screen._button(surface,(1170,678,178,37),'Inspect card',('inspect_selected',),mouse,enabled=screen.selected_hand is not None,size=24)
    screen._button(surface,(1170,721,178,37),'End turn',('act',Action('end')),mouse,enabled=Action('end') in legal,size=25)
    if b.winner is not None and not busy:
        screen._button(surface,(834,329,514,38),'Battle finished — Rematch / Decks',('menu',),mouse,size=26)
