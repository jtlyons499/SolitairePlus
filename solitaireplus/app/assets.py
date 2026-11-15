"""Images loaded at start-up: avatar art, menu backgrounds, felts, card backs, titles, splash art,
the drifting menu background constants and the cosmetic catalogs (moved out of main.py)."""
from solitaireplus.app import paths
from solitaireplus.profile.avatar import load_avatar_bank, avatar_options
from solitaireplus.app.cosmetic_assets import CosmeticCatalog, SingleDriftCache
import pygame
from solitaireplus.games.solitaire.rules import BASE_WIDTH, BASE_HEIGHT
from solitaireplus.npc.portraits import register_player_avatar_art
from solitaireplus.app.settings import MENU_BACKGROUNDS, FELTS, TITLES
from solitaireplus.app import state
from solitaireplus.app.lazy import lazy
backgrounds = lazy("solitaireplus.ui.backgrounds")
sounds = lazy("solitaireplus.app.sounds")

# ==================================================
# LAYERED AVATAR ASSETS
# ==================================================

avatar_bases = load_avatar_bank("bases")
avatar_eyes = load_avatar_bank("eyes")
avatar_hair = load_avatar_bank("hair")
avatar_glasses = load_avatar_bank("glasses")
avatar_tops = load_avatar_bank("tops")

# ==================================================
# MINI MENU BUTTON ASSETS
# ==================================================

register_player_avatar_art(avatar_bases, avatar_eyes, avatar_hair, avatar_glasses, avatar_tops)

menu_button_icon = pygame.image.load(
    str(paths.asset("ui/gameplay/menu_button_icon.png"))
).convert_alpha()

hint_button_icon = pygame.image.load(
    str(paths.asset("ui/gameplay/hint_button_icon.png"))
).convert_alpha()

hint_lock_icon = pygame.image.load(
    str(paths.asset("ui/gameplay/hint_lock_icon.png"))
).convert_alpha()

undo_button_icon = pygame.image.load(
    str(paths.asset("ui/gameplay/undo_button_icon.png"))
).convert_alpha()

shuffle_button_icon = pygame.image.load(
    str(paths.asset("ui/gameplay/shuffle_button_icon.png"))
).convert_alpha()

autosolve_button_icon = pygame.image.load(
    str(paths.asset("ui/gameplay/autosolve_button_icon.png"))
).convert_alpha()

# ==================================================
# SPLASH ASSETS
# ==================================================

def _load_legacy_splash_asset(path, fallback_size=(BASE_WIDTH, BASE_HEIGHT)):
    try:
        return pygame.image.load(path).convert_alpha()
    except (pygame.error, FileNotFoundError):
        return pygame.Surface(fallback_size, pygame.SRCALPHA)


splash_background = _load_legacy_splash_asset(
    str(paths.asset("ui/splash/splash_background.png"))
)

splash_spade = _load_legacy_splash_asset(
    str(paths.asset("ui/splash/splash_spade.png"))
)

splash_diamond = _load_legacy_splash_asset(
    str(paths.asset("ui/splash/splash_diamond.png"))
)

splash_club = _load_legacy_splash_asset(
    str(paths.asset("ui/splash/splash_club.png"))
)

splash_heart = _load_legacy_splash_asset(
    str(paths.asset("ui/splash/splash_heart.png"))
)

splash_prompt = _load_legacy_splash_asset(
    str(paths.asset("ui/splash/splash_prompt.png"))
)

# Optional modern splash assets. Keep the original splash as a full fallback so
# the game remains launchable while the new artwork is still being created.
try:
    state.modern_splash_background = pygame.image.load(
        str(paths.asset("splash/background.png"))
    ).convert_alpha()
    state.modern_splash_background = pygame.transform.smoothscale(
        state.modern_splash_background,
        (BASE_WIDTH, BASE_HEIGHT)
    )
except (pygame.error, FileNotFoundError):
    state.modern_splash_background = None

try:
    state.modern_splash_logo = pygame.image.load(
        str(paths.asset("splash/logo.png"))
    ).convert_alpha()
except (pygame.error, FileNotFoundError):
    state.modern_splash_logo = None


splash_start_time = pygame.time.get_ticks()

sounds.audio.play_sound(
    "startup"
)


# ==================================================
# MENU / CUSTOMIZATION ASSETS
# ==================================================

button_normal = pygame.image.load(
    str(paths.asset("ui/menu_ui/button_normal.png"))
).convert_alpha()

button_hover = pygame.image.load(
    str(paths.asset("ui/menu_ui/button_hover.png"))
).convert_alpha()

button_selected = pygame.image.load(
    str(paths.asset("ui/menu_ui/button_selected.png"))
).convert_alpha()

floating_logo = pygame.image.load(
    str(paths.asset("ui/menu_ui/floating_logo.png"))
).convert_alpha()


background_catalog = CosmeticCatalog(MENU_BACKGROUNDS, "bg_default")
menu_background_surfaces = background_catalog.surfaces

avatar_base_options = avatar_options(avatar_bases, allow_none=False)

avatar_eye_options = avatar_options(avatar_eyes, allow_none=False)

avatar_hair_options = avatar_options(avatar_hair, allow_none=False)

avatar_glasses_options = avatar_options(avatar_glasses, allow_none=True)

avatar_top_options = avatar_options(avatar_tops, allow_none=False)

# ==================================================
# MORE UI ASSETS
# ==================================================

state.play_background_image = pygame.image.load(
    str(paths.asset("ui/menu_ui/play_background.png"))
).convert_alpha()

state.play_background_image = pygame.transform.smoothscale(
    state.play_background_image,
    (
        BASE_WIDTH,
        BASE_HEIGHT
    )
)

# ----------------------------
# Supersampled copies used for
# slow menu background drifting
# ----------------------------
#
# The original drift rendered at 4x resolution. That looked
# smooth because the quarter-pixel movement survived the
# downsample, but it was expensive. The first performance
# pass dropped this to a direct 1x blit, which was fast but
# made very slow movement advance in obvious whole-pixel
# steps.
#
# A 3x drift buffer is the compromise: it restores subpixel-
# looking motion while processing substantially fewer pixels
# than the old 4x path.

menu_background_drift_cache = SingleDriftCache()

drift_width = (
    BASE_WIDTH
    + backgrounds.MENU_DRIFT_MARGIN * 2
)

drift_height = (
    BASE_HEIGHT
    + backgrounds.MENU_DRIFT_MARGIN * 2
)

menu_drift_render_surface = pygame.Surface(
    (
        BASE_WIDTH
        * backgrounds.MENU_DRIFT_SCALE,

        BASE_HEIGHT
        * backgrounds.MENU_DRIFT_SCALE
    )
).convert()

felt_catalog = CosmeticCatalog(FELTS, "f_default")
felt_surfaces = felt_catalog.surfaces


title_catalog = CosmeticCatalog(TITLES, "title_default")
title_surfaces = title_catalog.surfaces
