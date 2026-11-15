"""Bounded PNG/image cache with safe reload when artists replace files."""
from collections import OrderedDict
from pathlib import Path
import time
import pygame

class ImageCache:
    def __init__(self, root, maximum=128, refresh_interval=1.0):
        self.root = Path(root)
        self.maximum = max(1, int(maximum))
        self.refresh_interval = max(0.0, float(refresh_interval))
        self._entries = OrderedDict()

    def load(self, relative_path, size=None, fit=False):
        dimensions = tuple(int(value) for value in size) if size is not None else None
        if dimensions is not None and (len(dimensions) != 2 or min(dimensions) <= 0):
            raise ValueError('Image dimensions must be two positive numbers')
        path = self.root / relative_path
        key = (str(path), dimensions, bool(fit))
        now = time.monotonic()
        old = self._entries.get(key)
        if old is not None and now < old[2]:
            self._entries.move_to_end(key)
            return old[1]
        try:
            stat = path.stat()
            signature = (stat.st_size, stat.st_mtime_ns)
        except OSError:
            signature = None
        if old is not None and old[0] == signature:
            image = old[1]
        else:
            image = None
            if signature is not None:
                try:
                    image = pygame.image.load(str(path))
                    if pygame.display.get_surface() is not None:
                        image = image.convert_alpha()
                    if dimensions is not None:
                        target = dimensions
                        if fit:
                            width, height = image.get_size()
                            scale = min(dimensions[0] / width, dimensions[1] / height)
                            target = (max(1, round(width * scale)), max(1, round(height * scale)))
                        image = pygame.transform.smoothscale(image, target)
                except (pygame.error, OSError):
                    image = None
        self._entries[key] = (signature, image, now + self.refresh_interval)
        self._entries.move_to_end(key)
        while len(self._entries) > self.maximum:
            self._entries.popitem(last=False)
        return image

    def clear(self):
        self._entries.clear()
