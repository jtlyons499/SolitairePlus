"""Career menu images and leaderboard flags. Paths are relative to the game root (paths.root()), where the cache is rooted."""
from solitaireplus.app import paths
from pathlib import Path
from solitaireplus.ui.image_cache import ImageCache

ROOT = paths.root()
_cache = ImageCache(ROOT)
COUNTRY_FLAG_ALIASES = {'US': 'USA', 'UK': 'GBR', 'DEU': 'GER', 'NLD': 'NED'}

def get_jobfinder_image(filename, size=None):
    return _cache.load(Path('assets/career/jobfinder') / filename, size)

def get_realestate_image(filename, size=None):
    return _cache.load(Path('assets/career/realestate') / filename, size)

def get_career_hub_image(filename, size=None):
    return _cache.load(Path('assets/career/hub') / filename, size)

def get_country_flag_surface(country_code, box_size=(30, 20)):
    code = str(country_code or '').strip().upper()
    if not code:
        return None
    code = COUNTRY_FLAG_ALIASES.get(code, code)
    return _cache.load(Path('assets/ui/flags') / (code + '.png'), box_size, fit=True)
