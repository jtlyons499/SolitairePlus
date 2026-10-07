"""Reloadable cosmetic PNG catalogs and a bounded animation texture cache."""
from pathlib import Path
import time
import pygame


def normalize_cosmetic(surface, kind):
    """Accept both legacy full-canvas PNGs and compact title artwork."""
    canvas_size = (1366, 768)
    if kind == 'backgrounds':
        return pygame.transform.smoothscale(surface, canvas_size) if surface.get_size() != canvas_size else surface
    if kind == 'titles' and surface.get_size() != canvas_size:
        bounds = surface.get_bounding_rect()
        canvas = pygame.Surface(canvas_size, pygame.SRCALPHA)
        if bounds.width and bounds.height:
            artwork = surface.subsurface(bounds)
            slot = pygame.Rect(252, 28, 893, 140)
            scale = min(slot.width / bounds.width, slot.height / bounds.height)
            size = (max(1, round(bounds.width * scale)), max(1, round(bounds.height * scale)))
            artwork = pygame.transform.smoothscale(artwork, size)
            canvas.blit(artwork, artwork.get_rect(center=slot.center))
        return canvas
    return surface


class CosmeticCatalog:
    def __init__(self, catalog, default_id):
        self.catalog, self.default_id = catalog, default_id
        self.surfaces, self.errors = {}, {}
        self._signatures, self._images = {}, {}
        self._checked_at = -float('inf')
        self.refresh(force=True)

    def refresh(self, force=False):
        now = time.monotonic()
        if not force and now-self._checked_at < 1:
            return False
        self._checked_at = now
        changed = False
        for key, data in self.catalog.items():
            path = Path(data['path'])
            try:
                stat = path.stat()
                signature = (str(path), stat.st_mtime_ns, stat.st_size)
            except OSError:
                signature = (str(path), None, None)
            if key in self._signatures and self._signatures[key] == signature:
                continue
            changed = True
            self._signatures[key] = signature
            try:
                self._images[key] = normalize_cosmetic(
                    pygame.image.load(str(path)).convert_alpha(), path.parent.name
                )
                self.errors.pop(key, None)
            except (OSError, pygame.error) as exc:
                self._images.pop(key, None)
                self.errors[key] = str(exc)
        fallback = self._images.get(self.default_id)
        if fallback is None:
            fallback = next(iter(self._images.values()), None)
        if fallback is None:
            raise pygame.error(f'No readable artwork in cosmetic catalog; check {self.catalog[self.default_id]["path"]}')
        # Runtime renderers may still reference saved, temporarily missing IDs.
        # They use existing default art; unavailable items cannot be newly equipped.
        for key in self.catalog:
            self.surfaces[key] = self._images.get(key, fallback)
        return changed

    def available(self, key):
        return key in self._images


class SingleDriftCache:
    """Keep only the current background's large supersampled texture."""
    def __init__(self):
        self._key = None
        self.surface = None

    def get(self, key, source, size):
        signature = (key, id(source), tuple(size))
        if signature != self._key:
            self.surface = pygame.transform.smoothscale(source, size)
            self._key = signature
        return self.surface
