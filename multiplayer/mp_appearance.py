"""Player-local table textures and decoded public avatars."""
import base64
import io
from collections import OrderedDict
import pygame
from solitaireplus.app import paths
from mp_assets import remember


class Appearance:
    def __init__(self, profile):
        self.profile=profile;self.cache={};self.avatars={}
        # Surfaces reused across frames instead of rebuilt on every draw (B84): the background
        # shade per surface size, the oval felt and avatar layers per image and size (newest
        # last, bounded), and the font of an avatar's initial.
        self._shades={};self._ovals=OrderedDict();self._initial_font=None

    def image(self, path, size):
        key=(path, size)
        if key not in self.cache:
            try:self.cache[key]=pygame.transform.smoothscale(pygame.image.load(str(paths.resolve(path))).convert_alpha(),size)
            except (pygame.error,OSError):self.cache[key]=None
        return self.cache[key]

    def selected(self, category, size):
        key=self.profile.data['selected'][category]
        return self.image(self.profile.catalog[category][key]['path'],size)

    def background(self,surface):
        image=self.selected('background',surface.get_size())
        if image:surface.blit(image,(0,0))
        else:surface.fill((30,56,47))
        size=surface.get_size();shade=self._shades.get(size)
        if shade is None:
            shade=self._shades[size]=pygame.Surface(size,pygame.SRCALPHA);shade.fill((0,0,0,35))
        surface.blit(shade,(0,0))

    def oval(self,kind,image,size):
        """image cut to an oval of size (scaled to it first for an avatar), built once.

        The entry keeps the image alive, so its id cannot be reused by another surface."""
        size=tuple(size);key=(kind,id(image),size);entry=self._ovals.get(key)
        if entry is not None and entry[0] is image:
            self._ovals.move_to_end(key);return entry[1]
        layer=image.copy() if kind=='felt' else pygame.transform.smoothscale(image,size)
        mask=pygame.Surface(size,pygame.SRCALPHA)
        pygame.draw.ellipse(mask,(255,255,255,255),mask.get_rect());layer.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
        return remember(self._ovals,key,(image,layer))[1]

    def felt(self,surface,rect):
        pygame.draw.ellipse(surface,(109,77,45),rect.inflate(24,24))
        pygame.draw.ellipse(surface,(143,204,180),rect)
        image=self.selected('felt',rect.size)
        if image:surface.blit(self.oval('felt',image,rect.size),rect)
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
            surface.blit(self.oval('avatar',image,rect.size),rect)
        else:
            if self._initial_font is None:self._initial_font=pygame.font.Font(None,36)
            text=self._initial_font.render((name or '?')[0].upper(),True,(249,235,199));surface.blit(text,text.get_rect(center=rect.center))
        pygame.draw.ellipse(surface,(226,235,220),rect,2)
