"""Player-local table textures and decoded public avatars."""
import base64
import io
import pygame
from multiplayer_paths import ROOT


class Appearance:
    def __init__(self, profile):
        self.profile=profile;self.cache={};self.avatars={}

    def image(self, path, size):
        key=(path, size)
        if key not in self.cache:
            try:self.cache[key]=pygame.transform.smoothscale(pygame.image.load(str(ROOT/path)).convert_alpha(),size)
            except (pygame.error,OSError):self.cache[key]=None
        return self.cache[key]

    def selected(self, category, size):
        key=self.profile.data['selected'][category]
        return self.image(self.profile.catalog[category][key]['path'],size)

    def background(self,surface):
        image=self.selected('background',surface.get_size())
        if image:surface.blit(image,(0,0))
        else:surface.fill((30,56,47))
        shade=pygame.Surface(surface.get_size(),pygame.SRCALPHA);shade.fill((0,0,0,35));surface.blit(shade,(0,0))

    def felt(self,surface,rect):
        pygame.draw.ellipse(surface,(109,77,45),rect.inflate(24,24))
        pygame.draw.ellipse(surface,(143,204,180),rect)
        image=self.selected('felt',rect.size)
        if image:
            layer=image.copy();mask=pygame.Surface(rect.size,pygame.SRCALPHA)
            pygame.draw.ellipse(mask,(255,255,255,255),mask.get_rect())
            layer.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT);surface.blit(layer,rect)
        pygame.draw.ellipse(surface,(224,239,220),rect,2)

    def avatar(self,surface,value,rect,name='Player'):
        encoded=value.get('avatar','') if value else ''
        if encoded and encoded not in self.avatars:
            try:self.avatars[encoded]=pygame.image.load(io.BytesIO(base64.b64decode(encoded))).convert_alpha()
            except (ValueError,pygame.error):self.avatars[encoded]=None
            if len(self.avatars)>32:self.avatars.pop(next(iter(self.avatars)))
        image=self.avatars.get(encoded)
        pygame.draw.ellipse(surface,(36,65,58),rect)
        if image:
            layer=pygame.transform.smoothscale(image,rect.size);mask=pygame.Surface(rect.size,pygame.SRCALPHA)
            pygame.draw.ellipse(mask,(255,255,255,255),mask.get_rect());layer.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT);surface.blit(layer,rect)
        else:
            text=pygame.font.Font(None,36).render((name or '?')[0].upper(),True,(249,235,199));surface.blit(text,text.get_rect(center=rect.center))
        pygame.draw.ellipse(surface,(226,235,220),rect,2)
