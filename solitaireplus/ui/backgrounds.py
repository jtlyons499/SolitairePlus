"""The slowly drifting main-menu background (moved out of main.py)."""
import math
import pygame
from solitaireplus.games.solitaire.rules import BASE_WIDTH, BASE_HEIGHT
from solitaireplus.app import state
from solitaireplus.app.lazy import lazy
assets = lazy("solitaireplus.app.assets")
window = lazy("solitaireplus.app.window")

# ==================================================
# MENU BACKGROUND DRIFT
# ==================================================

MENU_DRIFT_SCALE = 3
MENU_DRIFT_MARGIN = 35

MENU_DRIFT_X = 20
MENU_DRIFT_Y = 12

# Seconds for one full back-and-forth cycle.
MENU_DRIFT_PERIOD_X = 50.0
MENU_DRIFT_PERIOD_Y = 80.0

# Pre-scaled drift frames (B17). The old code blitted the 3x background into the 3x buffer and
# smoothscaled the whole buffer down to the game surface every frame. Shrinking by exactly 3
# averages each 3x3 block on its own, so a frame only depends on the drift offset modulo 3 (the
# sub-pixel phase); the rest of the offset just picks which window of the result is shown. Each
# phase is downsampled once (at most 9 images per background) and a frame is a plain copy of the
# right window: the same pixels. A background with see-through pixels keeps the old path, because
# there every frame blends over what the 3x buffer still holds from earlier frames.
_prescaled_drift = {
    "background": None,   # the 3x background the frames below were made from
    "opaque": False,
    "frames": {},         # (phase_x, phase_y) -> that phase downsampled to 1x
    "buffer_owed": None,  # (background, draw_x, draw_y) last drawn without the 3x buffer
}


# Scaling opaque art to 3x leaves a few alpha values of 251-254 (rounding in smoothscale), which
# made the old code blend 1-2% of the previous frame into each new one. Such "nearly opaque"
# backgrounds are flattened once and then use the pre-scaled frames too: the picture differs from
# the old one by at most a few colour levels, without the faint ghosting. Backgrounds with real
# transparency (any alpha below this) keep the old, frame-by-frame path.
NEARLY_OPAQUE_ALPHA = 251


def _is_opaque(surface):
    """True when blitting the surface replaces every pixel under it (no blending)."""
    if surface.get_colorkey() is not None or surface.get_alpha() not in (None, 255):
        return False
    if not surface.get_flags() & pygame.SRCALPHA:
        return True
    fully_opaque = pygame.mask.from_surface(surface, 254)   # set where alpha == 255
    return fully_opaque.count() == surface.get_width() * surface.get_height()


def _is_nearly_opaque(surface):
    if surface.get_colorkey() is not None or surface.get_alpha() not in (None, 255):
        return False
    if not surface.get_flags() & pygame.SRCALPHA:
        return True
    solid = pygame.mask.from_surface(surface, NEARLY_OPAQUE_ALPHA - 1)   # set where alpha >= 251
    return solid.count() == surface.get_width() * surface.get_height()


def _flattened(surface):
    """An opaque copy (alpha dropped) with the same colours."""
    flat = pygame.Surface(surface.get_size(), 0, 32)
    flat.blit(surface, (0, 0), special_flags=pygame.BLEND_RGBA_MAX)   # copy RGB, ignore alpha
    return flat


def _prescaled_drift_frame(background, draw_x, draw_y):
    """(frame, area) to copy onto the game surface for this drift offset, or None to draw it the
    old way (a background that isn't opaque, or one that doesn't cover the 3x buffer)."""
    buffer = assets.menu_drift_render_surface
    target = window.game_surface
    if (buffer.get_size() != (BASE_WIDTH * MENU_DRIFT_SCALE, BASE_HEIGHT * MENU_DRIFT_SCALE)
            or target.get_size() != (BASE_WIDTH, BASE_HEIGHT)
            or target.get_flags() & pygame.SRCALPHA):   # the copy below must not blend
        return None

    cache = _prescaled_drift
    if cache["background"] is not background:
        cache["background"] = background
        cache["frames"] = {}
        if _is_opaque(background):
            cache["opaque"], cache["source"] = True, background
        elif _is_nearly_opaque(background):
            cache["opaque"], cache["source"] = True, _flattened(background)
        else:
            cache["opaque"], cache["source"] = False, None
    if not cache["opaque"]:
        return None
    source = cache["source"]

    phase_x, start_x = (-draw_x) % MENU_DRIFT_SCALE, (-draw_x) // MENU_DRIFT_SCALE
    phase_y, start_y = (-draw_y) % MENU_DRIFT_SCALE, (-draw_y) // MENU_DRIFT_SCALE
    width = (background.get_width() - phase_x) // MENU_DRIFT_SCALE
    height = (background.get_height() - phase_y) // MENU_DRIFT_SCALE
    area = pygame.Rect(start_x, start_y, BASE_WIDTH, BASE_HEIGHT)
    if not pygame.Rect(0, 0, width, height).contains(area):
        return None

    frame = cache["frames"].get((phase_x, phase_y))
    if frame is None:
        # Exactly what the old code did, once: blit into a buffer like the 3x one, then shrink.
        supersampled = pygame.Surface((width * MENU_DRIFT_SCALE, height * MENU_DRIFT_SCALE), 0, buffer)
        supersampled.blit(source, (-phase_x, -phase_y))
        frame = pygame.Surface((width, height), 0, target)
        pygame.transform.smoothscale(supersampled, (width, height), frame)
        cache["frames"][(phase_x, phase_y)] = frame
    return frame, area

def draw_drifting_menu_background():

    background = assets.menu_background_drift_cache.get(
        state.selected_menu_background, assets.menu_background_surfaces[state.selected_menu_background],
        (assets.drift_width * MENU_DRIFT_SCALE, assets.drift_height * MENU_DRIFT_SCALE)
    )

    time_sec = (
        pygame.time.get_ticks()
        / 1000.0
    )

    # ----------------------------
    # Extremely slow drift
    # ----------------------------

    x_phase = (
        time_sec
        / MENU_DRIFT_PERIOD_X
        * math.tau
    )

    y_phase = (
        time_sec
        / MENU_DRIFT_PERIOD_Y
        * math.tau
    )

    drift_x = (
        math.sin(x_phase)
        * MENU_DRIFT_X
    )

    drift_y = (
        math.sin(
            y_phase + 1.3
        )
        * MENU_DRIFT_Y
    )

    # Convert movement into the supersampled drift space.
    # At 3x, one source-pixel step becomes one third of a
    # logical game pixel after the downsample.
    draw_x = round(
        (
            -MENU_DRIFT_MARGIN
            + drift_x
        )
        * MENU_DRIFT_SCALE
    )

    draw_y = round(
        (
            -MENU_DRIFT_MARGIN
            + drift_y
        )
        * MENU_DRIFT_SCALE
    )

    prescaled = _prescaled_drift_frame(background, draw_x, draw_y)

    if prescaled is not None:
        frame, area = prescaled
        window.game_surface.blit(frame, (0, 0), area)
        _prescaled_drift["buffer_owed"] = (background, draw_x, draw_y)
        return

    owed = _prescaled_drift["buffer_owed"]

    if owed is not None:
        # The old code always left the last frame in the 3x buffer, and a see-through
        # background blends over it: put that frame back first.
        _prescaled_drift["buffer_owed"] = None
        assets.menu_drift_render_surface.blit(owed[0], (owed[1], owed[2]))

    assets.menu_drift_render_surface.blit(
        background,
        (
            draw_x,
            draw_y
        )
    )

    # Downsample only the drifting background. UI/text is
    # drawn afterward at the normal 1366x768 design size.
    pygame.transform.smoothscale(
        assets.menu_drift_render_surface,
        (
            BASE_WIDTH,
            BASE_HEIGHT
        ),
        window.game_surface
    )
