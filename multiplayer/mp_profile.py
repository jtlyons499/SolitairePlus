"""Independent local multiplayer progression, cosmetic catalog and PNG avatars."""
import base64
import copy
import io
import json
import os
from pathlib import Path
import uuid
import tempfile

from multiplayer_paths import ROOT


def catalogs():
    from settings import MENU_BACKGROUNDS, FELTS, CARD_BACKS, TITLES
    from achievements import register_optional_cosmetics
    result = {'background': copy.deepcopy(MENU_BACKGROUNDS), 'felt': copy.deepcopy(FELTS),
              'back': copy.deepcopy(CARD_BACKS)}
    register_optional_cosmetics(result['background'], result['felt'], copy.deepcopy(TITLES))
    return result


DEFAULTS = {'background': 'bg_default', 'felt': 'f_default', 'back': 'back_default'}

AVATAR_DEFAULTS = {'base':'base_01','eyes':'eyes_01','hair':'hair_01','glasses':None,'top':'top_01'}
AVATAR_FOLDERS = {'base':'bases','eyes':'eyes','hair':'hair','glasses':'glasses','top':'tops'}


class MultiplayerProfile:
    def __init__(self, slot=1, directory=None):
        self.directory = Path(directory) if directory else Path(os.environ.get('LOCALAPPDATA', Path.home()/'.config')) / 'SolitaireMultiplayer' / 'profiles'
        self.catalog = catalogs()
        self._avatar_catalog_cache = None
        self.notice = ''
        self.load(slot)

    @property
    def path(self):
        return self.directory / f'profile_{self.slot}.json'

    def load(self, slot):
        self.slot = max(1, min(3, int(slot)))
        try:
            raw = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(raw, dict):raw = {}
        except (OSError, ValueError):raw = {}
        def integer(key):
            try:return max(0,int(raw.get(key,0)))
            except (ValueError,TypeError):return 0
        awards=raw.get('awards',[])
        self.data = {'version': 1, 'id': str(raw.get('id') or uuid.uuid4()),
                     'name': str(raw.get('name', 'Player'))[:32], 'xp': integer('xp'),
                     'wins': integer('wins'), 'avatar': str(raw.get('avatar', ''))[:24000],
                     'avatar_parts': dict(AVATAR_DEFAULTS),
                     'selected': dict(DEFAULTS), 'awards': awards[-2000:] if isinstance(awards,list) else []}
        avatar_parts=raw.get('avatar_parts',{})
        if not isinstance(avatar_parts,dict):avatar_parts={}
        for key,default in AVATAR_DEFAULTS.items():
            value=avatar_parts.get(key,default)
            if value is None and key=='glasses':self.data['avatar_parts'][key]=None
            elif isinstance(value,str) and len(value)<=40:self.data['avatar_parts'][key]=value
        selected=raw.get('selected',{})
        if not isinstance(selected,dict):selected={}
        for category, default in DEFAULTS.items():
            value = selected.get(category, default)
            if value in self.unlocked(category):self.data['selected'][category] = value

    @property
    def level(self):return 1 + self.data['xp'] // 100

    def unlock_level(self, category, key):
        ordered = list(self.catalog[category])
        if key == DEFAULTS[category]:return 1
        return 2 + [k for k in ordered if k != DEFAULTS[category]].index(key)

    def unlocked(self, category):
        return [key for key in self.catalog[category] if self.unlock_level(category, key) <= self.level]

    def select(self, category, key):
        if key not in self.unlocked(category):return False
        self.data['selected'][category] = key
        return self.save()

    def save(self):
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            temp = None
            try:
                with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.directory,
                                                 suffix='.tmp', delete=False) as stream:
                    temp=Path(stream.name)
                    json.dump(self.data,stream,ensure_ascii=False,indent=2)
                    stream.flush()
                    os.fsync(stream.fileno())
                temp.replace(self.path)
                temp=None
            finally:
                if temp is not None:
                    temp.unlink(missing_ok=True)
            return True
        except OSError:
            self.notice = 'Could not save profile. Check the profile folder permissions.'
            return False

    def award(self, event):
        if not isinstance(event, dict):return False
        token = str(event.get('id', ''))
        xp = event.get('xp')
        if not token or len(token)>100 or not isinstance(xp,int) or isinstance(xp,bool) or not 1<=xp<=20:return False
        if token in self.data['awards']:return False
        self.data['awards'].append(token)
        self.data['awards'] = self.data['awards'][-2000:]
        self.data['xp'] += xp;self.data['wins'] += 1
        self.notice = f'+{xp} XP • Multiplayer level {self.level}'
        self.save();return True

    def avatar_choices(self):
        # Avatar artwork is static for a running build. Cache the loaded layers
        # so the profile preview does not hit disk and decode PNGs every frame.
        if self._avatar_catalog_cache is not None:
            return self._avatar_catalog_cache
        from profile_avatar_assets import load_avatar_bank, avatar_options
        banks={}
        choices={}
        for key,folder in AVATAR_FOLDERS.items():
            bank=load_avatar_bank(folder)
            banks[key]=bank
            choices[key]=avatar_options(bank,allow_none=(key=='glasses'))
        self._avatar_catalog_cache=(banks,choices)
        return self._avatar_catalog_cache

    def render_avatar_surface(self):
        import pygame
        banks,choices=self.avatar_choices()
        canvas=pygame.Surface((300,360),pygame.SRCALPHA)
        parts=self.data.setdefault('avatar_parts',dict(AVATAR_DEFAULTS))
        for key in ('base','eyes','hair','glasses','top'):
            value=parts.get(key,AVATAR_DEFAULTS[key])
            if value is None and key=='glasses':continue
            if value not in banks[key]:
                value=next((item for item in choices[key] if item is not None),None)
                parts[key]=value
            image=banks[key].get(value) if value is not None else None
            if image is not None:canvas.blit(image,(0,0))
        return canvas

    def rebuild_avatar(self):
        import pygame
        canvas=self.render_avatar_surface()
        # Preserve the single-player avatar proportions, then crop a centered
        # square portrait for circular multiplayer badges.
        encoded=''
        for width,height,crop_y in ((80,96,-8),(64,77,-6),(48,58,-5)):
            scaled=pygame.transform.smoothscale(canvas,(width,height))
            portrait=pygame.Surface((width,width),pygame.SRCALPHA)
            portrait.blit(scaled,(0,crop_y))
            buffer=io.BytesIO();pygame.image.save(portrait,buffer,'avatar.png')
            candidate=base64.b64encode(buffer.getvalue()).decode('ascii')
            if len(candidate)<=24000:
                encoded=candidate;break
        if not encoded:
            raise ValueError('Avatar portrait could not be compressed for multiplayer.')
        self.data['avatar']=encoded
        self.notice='Avatar updated.'
        return self.save()

    def cycle_avatar_part(self,key,delta):
        if key not in AVATAR_FOLDERS:return False
        _banks,choices=self.avatar_choices()
        options=choices[key]
        if not options:return False
        current=self.data.setdefault('avatar_parts',dict(AVATAR_DEFAULTS)).get(key)
        try:index=options.index(current)
        except ValueError:index=0
        self.data['avatar_parts'][key]=options[(index+(1 if delta>=0 else -1))%len(options)]
        return self.rebuild_avatar()

    def import_avatar(self, path):
        import pygame
        path = Path(str(path).strip().strip('"'))
        if path.suffix.lower() != '.png':raise ValueError('Choose a PNG image.')
        if path.stat().st_size > 8*1024*1024:raise ValueError('Use a PNG smaller than 8 MB.')
        image = pygame.image.load(str(path))
        if max(image.get_size())>4096:raise ValueError('Use an image no larger than 4096 pixels.')
        # Normalize avatar pixels before transmission; never send the user's local path.
        canvas = pygame.Surface((96,96), pygame.SRCALPHA)
        image = pygame.transform.smoothscale(image, (96,96))
        canvas.blit(image,(0,0));buffer=io.BytesIO();pygame.image.save(canvas,buffer,'avatar.png')
        encoded=base64.b64encode(buffer.getvalue()).decode('ascii')
        if len(encoded)>24000:raise ValueError('Avatar has too much image detail. Try a simpler PNG.')
        self.data['avatar']=encoded;self.notice='Avatar saved and shared with the table.';self.save()

    def public(self):
        return {'name':self.data['name'], 'level':self.level, 'avatar':self.data['avatar']}


def clean_public(value):
    """Limit one avatar packet so six seats never exceed relay frame limits."""
    if not isinstance(value,dict):return None
    avatar=value.get('avatar','')
    if not isinstance(avatar,str) or len(avatar)>24000:return None
    if avatar:
        try:
            pixels=base64.b64decode(avatar,validate=True)
            # PNG signature, IHDR and bounded dimensions, before UI decoding.
            if pixels[:8]!=b'\x89PNG\r\n\x1a\n' or pixels[12:16]!=b'IHDR':return None
            if not 1<=int.from_bytes(pixels[16:20],'big')<=96 or not 1<=int.from_bytes(pixels[20:24],'big')<=96:return None
        except (ValueError,TypeError):return None
    level=value.get('level',1)
    if not isinstance(level,int) or isinstance(level,bool):return None
    return {'name':str(value.get('name','Player'))[:32], 'level':max(1,min(9999,level)), 'avatar':avatar}


def winning_xp(game, humans, participants):
    """20 XP for an outright pot win; 10 for split-only wins, once per hand."""
    result={}
    for identity,seat in humans.items():
        if identity not in participants:continue
        pots=[p for p in game.last_pot_awards if seat in p.get('winners',[]) and p.get('amount',0)>0]
        if pots:result[identity]=20 if any(len(p['winners'])==1 for p in pots) else 10
    return result
