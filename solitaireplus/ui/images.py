"""Pictures for the UI: authored images loaded once per size, cover-scaled button art, and
scale-to-fit previews (moved out of legacy.py).

A missing or unreadable file gives None (get_event_ui_asset, get_cover_scaled_ui_asset), so a
screen can fall back to drawing without the art.
"""
import pygame


def scale_surface_to_fit(
    surface,
    max_width,
    max_height
):
    width = surface.get_width()
    height = surface.get_height()

    if width == 0 or height == 0:
        return surface

    scale = min(
        max_width / width,
        max_height / height
    )

    new_width = max(
        1,
        int(width * scale)
    )

    new_height = max(
        1,
        int(height * scale)
    )

    return pygame.transform.smoothscale(
        surface,
        (
            new_width,
            new_height
        )
    )


_event_ui_asset_cache = {}


def get_event_ui_asset(path, size=None):
    if not path:
        return None
    cache_key = (path, tuple(size) if size else None)
    if cache_key in _event_ui_asset_cache:
        return _event_ui_asset_cache[cache_key]
    try:
        image = pygame.image.load(path).convert_alpha()
        if size is not None:
            image = pygame.transform.smoothscale(image, size)
    except (pygame.error, FileNotFoundError):
        image = None
    _event_ui_asset_cache[cache_key] = image
    return image


def get_cover_scaled_ui_asset(path, size):
    """Scale an authored image to fill a button without distorting its aspect ratio."""
    if not path or not size:
        return None

    target_w, target_h = int(size[0]), int(size[1])
    if target_w <= 0 or target_h <= 0:
        return None

    cache_key = ("cover", path, target_w, target_h)
    if cache_key in _event_ui_asset_cache:
        return _event_ui_asset_cache[cache_key]

    source = get_event_ui_asset(path)
    if source is None:
        _event_ui_asset_cache[cache_key] = None
        return None

    source_w, source_h = source.get_size()
    target_ratio = target_w / target_h
    source_ratio = source_w / max(1, source_h)

    if source_ratio > target_ratio:
        crop_w = max(1, int(round(source_h * target_ratio)))
        crop_x = max(0, (source_w - crop_w) // 2)
        crop_rect = pygame.Rect(crop_x, 0, crop_w, source_h)
    else:
        crop_h = max(1, int(round(source_w / target_ratio)))
        crop_y = max(0, (source_h - crop_h) // 2)
        crop_rect = pygame.Rect(0, crop_y, source_w, crop_h)

    cropped = source.subsurface(crop_rect).copy()
    image = pygame.transform.smoothscale(cropped, (target_w, target_h))
    _event_ui_asset_cache[cache_key] = image
    return image
