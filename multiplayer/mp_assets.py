"""Shared multiplayer table assets: card faces, card back, font and NPC portraits."""
from collections import OrderedDict
import pygame
from solitaireplus.app import paths
from solitaireplus.npc.portraits import draw_layered_portrait

CACHE_LIMIT=96

def remember(cache,key,value,maximum=CACHE_LIMIT):
    """Store value as the newest entry of an OrderedDict and drop the oldest past maximum."""
    cache[key]=value;cache.move_to_end(key)
    while len(cache)>maximum:cache.popitem(last=False)
    return value

class TableView:
    def __init__(self,surface):
        # portraits: finished (masked, scaled) portrait surfaces, newest last.
        self.surface=surface;self.portraits=OrderedDict();self.font=pygame.font.Font(None,28);self.cards={}
        for suit,letter in [('Clubs','C'),('Diamonds','D'),('Hearts','H'),('Spades','S')]:
            for rank in ['A','2','3','4','5','6','7','8','9','10','J','Q','K']:
                key=rank+letter;path=paths.asset('cards','fronts',f'{key}.png')
                if path.exists():self.cards[key]=pygame.image.load(path).convert_alpha()
                else:
                    # Fully functional native card faces when running without optional artwork.
                    card=pygame.Surface((150,210));card.fill((248,245,231));pygame.draw.rect(card,(40,40,40),card.get_rect(),3)
                    color=(188,37,38) if letter in 'DH' else (25,30,30)
                    card.blit(self.font.render(rank+' '+letter,True,color),(12,12));self.cards[key]=card
        path=paths.asset('cards','backs','back_default.png')
        self.back=pygame.image.load(path).convert_alpha() if path.exists() else pygame.Surface((150,210))
        if not path.exists():self.back.fill((38,73,125));pygame.draw.rect(self.back,(236,221,167),self.back.get_rect().inflate(-16,-16),3)
    def portrait(self,npc,rect,game=None):
        # Keyed by the NPC's look as well as its id, so a new look is never drawn from a stale entry.
        look=repr((npc.get('avatar'),npc.get('portrait_style'),npc.get('age')))
        key=(npc.get('id'),str(npc.get('portrait','')),look,rect.w,rect.h)
        if key in self.portraits:
            self.portraits.move_to_end(key);finished=self.portraits[key]
        else:finished=remember(self.portraits,key,self.finished_portrait(npc,rect.size))
        if finished is not None:self.surface.blit(finished,rect)
        else:
            pygame.draw.ellipse(self.surface,(43,74,68),rect)
            initial=self.font.render(npc.get('name','?')[0],True,(242,229,192));self.surface.blit(initial,initial.get_rect(center=rect.center))
        pygame.draw.ellipse(self.surface,(226,235,220),rect,2)
    def finished_portrait(self,npc,size):
        """The portrait art scaled into an oval on a dark disc, or None when there is no art."""
        path=paths.resolve(str(npc.get('portrait','')))
        image=pygame.image.load(path).convert_alpha() if path.is_file() else draw_layered_portrait(npc,size[0])
        if image is None:return None
        layer=pygame.Surface(size,pygame.SRCALPHA)
        pygame.draw.ellipse(layer,(36,65,58),layer.get_rect())
        layer.blit(pygame.transform.smoothscale(image,size),(0,0))
        mask=pygame.Surface(size,pygame.SRCALPHA);pygame.draw.ellipse(mask,(255,255,255,255),mask.get_rect())
        layer.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
        return layer
