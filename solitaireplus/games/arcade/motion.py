"""Sub-pixel movement for the arcade machines' pygame Rects."""
from __future__ import annotations

import math

import pygame


def _whole(value):
    """Round half up, so objects moving in step stay in step."""
    return int(math.floor(value + 0.5))


def move_rect(rect, position, dx, dy):
    """Move rect by (dx, dy) pixels, keeping the exact float top-left in position.

    A Rect only holds whole pixels, so adding a rounded step every frame loses
    (or gains) the fraction each frame. position is a pygame.Vector2 (or None
    the first time) holding the float top-left; the Rect gets the rounded copy
    for drawing and collisions. If code placed the Rect directly since the last
    move (a reset, a clamp to a wall, a bounce), that axis restarts from the
    Rect. Returns the position to keep for the next move.
    """
    if position is None:
        position = pygame.Vector2(rect.topleft)
    else:
        if _whole(position.x) != rect.x:
            position.x = rect.x
        if _whole(position.y) != rect.y:
            position.y = rect.y
    position.x += dx
    position.y += dy
    rect.topleft = (_whole(position.x), _whole(position.y))
    return position
