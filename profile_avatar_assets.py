"""Discover numbered player-avatar PNGs without fixed variant counts."""
from pathlib import Path
import re
import pygame

AVATAR_ROOT = Path(__file__).resolve().parent / 'assets' / 'ui' / 'profile' / 'avatar'
PARTS = {'bases':'base', 'eyes':'eyes', 'hair':'hair', 'glasses':'glasses', 'tops':'top'}

def load_avatar_bank(folder, root=AVATAR_ROOT):
    prefix = PARTS[folder]
    pattern = re.compile(rf'{prefix}_(\d{{2,}})\.png', re.IGNORECASE)
    paths = []
    for path in (Path(root)/folder).glob('*.png'):
        match = pattern.fullmatch(path.name)
        if match and int(match.group(1)) > 0:
            paths.append((int(match.group(1)), path.name, path))
    bank = {}
    for number, name, path in sorted(paths):
        try:
            image = pygame.image.load(str(path))
            if pygame.display.get_surface() is not None:
                image = image.convert_alpha()
            bank[path.stem.lower()] = image
        except (OSError, pygame.error) as error:
            print(f'Avatar artwork skipped: {path}: {error}')
    return bank

def avatar_options(bank, allow_none=False):
    identities = sorted(bank, key=lambda identity: (int(identity.rsplit('_',1)[1]), identity))
    return ([None] if allow_none else []) + identities
