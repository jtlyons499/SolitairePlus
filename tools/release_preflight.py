"""Validate release resources; report optional cosmetics without blocking a build."""
from pathlib import Path
import json
import os
import sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
os.chdir(ROOT)
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
pygame.init()
pygame.display.set_mode((1,1))
errors=[]
checked=0
for path in (ROOT/'assets').rglob('*'):
    if path.suffix.lower() in {'.png','.jpg','.jpeg','.bmp','.webp'}:
        checked+=1
        try: pygame.image.load(str(path))
        except Exception as exc: errors.append(str(path.relative_to(ROOT))+': '+str(exc))
for path in (ROOT/'data').rglob('*.json'):
    try: json.loads(path.read_text(encoding='utf-8-sig'))
    except Exception as exc: errors.append(str(path.relative_to(ROOT))+': '+str(exc))
required=['data/npcs.json','assets/cards/backs/back_default.png']
for name in required:
    if not (ROOT/name).is_file(): errors.append('Missing required: '+name)
from settings import MENU_BACKGROUNDS,FELTS,TITLES
missing=[]
for catalog in (MENU_BACKGROUNDS,FELTS,TITLES):
    for key,item in catalog.items():
        name=item.get('path')
        if name and not (ROOT/name).is_file(): missing.append(name)
report={'images_checked':checked,'errors':errors,'optional_cosmetics_missing':sorted(set(missing))}
(ROOT/'release_preflight.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(f"Images checked: {checked}; errors: {len(errors)}; optional cosmetics missing: {len(set(missing))}")
for error in errors: print(error)
pygame.quit()
raise SystemExit(bool(errors))
