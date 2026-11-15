"""Mouse cursors: cosmetic cursor images, the accessible-size check and the software cursor
fallback (moved out of main.py)."""
from solitaireplus.app import paths
import os
import sys
import ctypes
import pygame
from solitaireplus.app import state
from solitaireplus.app.lazy import lazy
legacy = lazy("solitaireplus.legacy")

# ==================================================
# CUSTOM CURSORS
# ==================================================

CURSOR_FOLDER = str(paths.asset("ui/cursors"))
CURSOR_PREVIEW_FOLDER = os.path.join(
    CURSOR_FOLDER,
    "previews"
)
CURSOR_RUNTIME_SIZE = (34, 30)
CURSOR_PREVIEW_MAX_SIZE = (150, 115)

cursor_cosmetics = {}
cursor_surfaces = {}
cursor_preview_surfaces = {}
cursor_runtime_surfaces = {}

if os.path.isdir(CURSOR_FOLDER):
    state.cursor_files = [
        filename
        for filename in os.listdir(CURSOR_FOLDER)
        if filename.lower().endswith(".png")
    ]
else:
    state.cursor_files = []

# Keep the original cursor.png first, then sort additional
# customization assets alphabetically for stable ordering.
state.cursor_files.sort(
    key=lambda filename: (
        0 if filename.lower() == "cursor.png" else 1,
        filename.lower()
    )
)

for cursor_index, filename in enumerate(state.cursor_files):
    state.asset_id = os.path.splitext(filename)[0]
    path = os.path.join(CURSOR_FOLDER, filename)

    source = pygame.image.load(path).convert_alpha()

    cursor_surfaces[state.asset_id] = source
    cursor_runtime_surfaces[state.asset_id] = (
        pygame.transform.smoothscale(
            source,
            CURSOR_RUNTIME_SIZE
        )
    )

    # Prefer dedicated large preview artwork when present.
    # Otherwise build a crisp nearest-neighbor thumbnail once
    # at startup instead of smooth-scaling the tiny live cursor
    # every time the Customize screen is drawn.
    preview_path = os.path.join(
        CURSOR_PREVIEW_FOLDER,
        filename
    )

    if os.path.isfile(preview_path):
        state.preview_source = pygame.image.load(
            preview_path
        ).convert_alpha()
    else:
        state.preview_source = source

    preview_width = state.preview_source.get_width()
    preview_height = state.preview_source.get_height()

    if preview_width > 0 and preview_height > 0:
        preview_scale = min(
            CURSOR_PREVIEW_MAX_SIZE[0] / preview_width,
            CURSOR_PREVIEW_MAX_SIZE[1] / preview_height
        )

        # Never shrink dedicated preview art unnecessarily.
        # Tiny cursor sprites are enlarged with nearest-neighbor
        # scaling so pixel edges stay sharp.
        if preview_scale > 1.0:
            preview_size = (
                max(1, int(preview_width * preview_scale)),
                max(1, int(preview_height * preview_scale))
            )
            state.preview_surface = pygame.transform.scale(
                state.preview_source,
                preview_size
            )
        else:
            state.preview_surface = pygame.transform.smoothscale(
                state.preview_source,
                (
                    max(1, int(preview_width * preview_scale)),
                    max(1, int(preview_height * preview_scale))
                )
            )
    else:
        state.preview_surface = state.preview_source

    cursor_preview_surfaces[state.asset_id] = state.preview_surface

    if state.asset_id == "cursor":
        state.display_name = "Default"
    else:
        state.display_name = (
            state.asset_id
            .replace("cursor_", "")
            .replace("_", " ")
            .strip()
            .title()
        )

        if not state.display_name:
            state.display_name = state.asset_id

    cursor_cosmetics[state.asset_id] = {
        "name": state.display_name,
        "path": path,
        "order": (cursor_index + 1) * 10,
    }

unlocked_cursors = set(cursor_cosmetics.keys()) - legacy.REWARD_CURSOR_IDS

if state.selected_cursor not in cursor_runtime_surfaces:
    if "cursor" in cursor_runtime_surfaces:
        state.selected_cursor = "cursor"
    elif state.cursor_files:
        state.selected_cursor = os.path.splitext(state.cursor_files[0])[0]

state.cursor_image = cursor_runtime_surfaces.get(state.selected_cursor)
state.system_cursor_metrics = CURSOR_RUNTIME_SIZE
_cursor_scaled_cache = {}


def detect_accessible_cursor_mode():

    state.software_cursor_force_accessible = False
    state.system_cursor_metrics = CURSOR_RUNTIME_SIZE

    if not sys.platform.startswith("win"):
        return

    try:
        user32 = ctypes.windll.user32
        width = int(user32.GetSystemMetrics(13))
        height = int(user32.GetSystemMetrics(14))
        # The game is DPI-aware (W1), so Windows reports cursor sizes in real pixels at the
        # system scaling (40 px at 125%, 64 px at 200%). Compare them at 100% scaling, as before.
        dpi = int(user32.GetDpiForSystem()) if hasattr(user32, "GetDpiForSystem") else 96
        if dpi > 96:
            width = round(width * 96 / dpi)
            height = round(height * 96 / dpi)
    except Exception:
        return

    if width > 0 and height > 0:
        state.system_cursor_metrics = (width, height)
        state.software_cursor_force_accessible = (
            max(width, height) >= 48
            or width * height >= 2304
        )


def get_selected_cursor_surface(use_accessible_size=False):
    source = cursor_surfaces.get(state.selected_cursor)
    if source is None:
        return None

    if not use_accessible_size:
        return cursor_runtime_surfaces.get(state.selected_cursor)

    target_w, target_h = state.system_cursor_metrics
    target_w = max(target_w, CURSOR_RUNTIME_SIZE[0])
    target_h = max(target_h, CURSOR_RUNTIME_SIZE[1])
    cache_key = (state.selected_cursor, target_w, target_h)
    if cache_key in _cursor_scaled_cache:
        return _cursor_scaled_cache[cache_key]

    scale = min(target_w / max(1, source.get_width()), target_h / max(1, source.get_height()))
    scaled = pygame.transform.smoothscale(
        source,
        (
            max(1, int(round(source.get_width() * scale))),
            max(1, int(round(source.get_height() * scale))),
        )
    )
    _cursor_scaled_cache[cache_key] = scaled
    return scaled


def apply_selected_cursor():

    detect_accessible_cursor_mode()

    if state.software_cursor_force_accessible:
        state.cursor_image = get_selected_cursor_surface(use_accessible_size=True)
        pygame.mouse.set_visible(False)
        state.software_cursor_fallback = True
        return

    state.cursor_image = get_selected_cursor_surface(use_accessible_size=False)

    if state.cursor_image is None:
        pygame.mouse.set_visible(True)
        state.software_cursor_fallback = False
        return

    try:
        native_cursor = pygame.cursors.Cursor((0, 0), state.cursor_image)
        pygame.mouse.set_cursor(native_cursor)
        pygame.mouse.set_visible(True)
        state.software_cursor_fallback = False
    except (pygame.error, TypeError, ValueError):
        state.cursor_image = get_selected_cursor_surface(use_accessible_size=False)
        pygame.mouse.set_visible(False)
        state.software_cursor_fallback = True


apply_selected_cursor()
