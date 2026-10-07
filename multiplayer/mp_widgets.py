"""Shared artwork buttons, clipboard text entry and private hand descriptions."""
import pygame
from poker_core import describe_poker_score
from multiplayer_paths import ROOT

BUTTON_ART={}


def wooden_button(surface,appearance,rect,label,font,enabled=True,hover=False):
    rect=pygame.Rect(rect)
    path='assets/ui/menu_ui/button_'+('hover' if hover and enabled else 'normal')+'.png'
    if appearance:image=appearance.image(path,rect.size)
    else:
        key=(path,rect.size)
        if key not in BUTTON_ART:
            try:BUTTON_ART[key]=pygame.transform.smoothscale(pygame.image.load(str(ROOT/path)).convert_alpha(),rect.size)
            except (OSError,pygame.error):BUTTON_ART[key]=None
        image=BUTTON_ART[key]
    if image:
        if not enabled:image=image.copy();image.set_alpha(100)
        surface.blit(image,rect)
    else:pygame.draw.rect(surface,(111,72,42) if enabled else (62,55,48),rect,border_radius=7)
    text=font.render(label,True,(255,242,208) if enabled else (167,155,135))
    if text.get_width()>rect.w-14:text=pygame.transform.smoothscale(text,(rect.w-14,text.get_height()))
    surface.blit(text,text.get_rect(center=rect.center))


class TextInput:
    def __init__(self):self.selected=False
    def event(self,event,value,limit,uppercase=False,digits=False):
        def clean(text):
            text=''.join(c for c in text if c.isprintable())
            if uppercase:text=text.upper()
            if digits:text=''.join(c for c in text if c in '0123456789')
            return text
        if event.type==pygame.TEXTINPUT:
            value=('' if self.selected else value)+clean(event.text);self.selected=False
        elif event.type==pygame.KEYDOWN:
            if getattr(event,'mod',0) & pygame.KMOD_CTRL:
                if event.key==pygame.K_a:self.selected=True
                elif event.key in (pygame.K_c,pygame.K_x):
                    try:pygame.scrap.put_text(value)
                    except pygame.error:pass
                    if event.key==pygame.K_x:value='';self.selected=False
                elif event.key==pygame.K_v:
                    try:text=pygame.scrap.get_text() or ''
                    except pygame.error:text=''
                    value=('' if self.selected else value)+clean(text);self.selected=False
            elif event.key==pygame.K_BACKSPACE:value='' if self.selected else value[:-1];self.selected=False
        return clean(value)[:limit]


def hand_type(game):
    cards=game.player_hand+game.community_cards
    if not game.player_hand:return 'Sitting out' if game.player_stack>0 else 'Out of chips'
    evaluated=game.evaluate_best_hand(cards)
    if evaluated:return describe_poker_score(evaluated[0],compact=True).split(',')[0]
    return 'One pair' if len(cards)==2 and cards[0]['rank']==cards[1]['rank'] else 'High card'
