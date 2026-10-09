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


class MultiplayerProfile:
    def __init__(self, slot=1, directory=None):
        self.directory = Path(directory) if directory else Path(os.environ.get('LOCALAPPDATA', Path.home()/'.config')) / 'SolitaireMultiplayer' / 'profiles'
        self.catalog = catalogs()
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
                     'selected': dict(DEFAULTS), 'awards': awards[-2000:] if isinstance(awards,list) else []}
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
