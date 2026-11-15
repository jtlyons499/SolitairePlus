"""Splash screen (moved out of legacy.py)."""
from solitaireplus.games.solitaire.rules import BASE_HEIGHT
from solitaireplus.games.solitaire.rules import BASE_WIDTH
from version import __version__ as BUILD_VERSION
import math
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
fonts = lazy("solitaireplus.app.fonts")
assets = lazy("solitaireplus.app.assets")
options_screen = lazy("solitaireplus.menus.options_screen")


# ==================================================
# SPLASH SCREEN
# ==================================================

def draw_splash_screen():
    current_time = pygame.time.get_ticks()

    elapsed_ms = (
        current_time
        - assets.splash_start_time
    )

    elapsed_seconds = (
        elapsed_ms / 1000.0
    )

    if state.modern_splash_background is not None:
        window.game_surface.blit(state.modern_splash_background, (0, 0))

        vignette = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        vignette.fill((0, 0, 0, 34))
        window.game_surface.blit(vignette, (0, 0))

        if state.modern_splash_logo is not None:
            source_w, source_h = state.modern_splash_logo.get_size()
            target_w = 690
            target_h = max(1, int(target_w * source_h / max(1, source_w)))
            logo = pygame.transform.smoothscale(
                state.modern_splash_logo,
                (target_w, target_h)
            )
            float_y = int(math.sin(elapsed_seconds * 0.8) * 3)
            logo_rect = logo.get_rect(
                center=(BASE_WIDTH // 2, 300 + float_y)
            )
            window.game_surface.blit(logo, logo_rect)
        else:
            logo_text = fonts.options_title_font.render(
                "SOLITAIRE+",
                True,
                (240, 238, 226)
            )
            window.game_surface.blit(
                logo_text,
                logo_text.get_rect(center=(BASE_WIDTH // 2, 305))
            )

        pulse = (math.sin(elapsed_seconds * 2.8) + 1.0) / 2.0
        prompt_alpha = int(115 + pulse * 120)
        prompt = fonts.option_label_font.render(
            "CLICK OR PRESS ANY KEY",
            True,
            (232, 226, 205)
        )
        prompt.set_alpha(prompt_alpha)
        window.game_surface.blit(
            prompt,
            prompt.get_rect(center=(BASE_WIDTH // 2, 610))
        )

        version = fonts.difficulty_detail_font.render(
            BUILD_VERSION,
            True,
            (145, 150, 146)
        )
        window.game_surface.blit(version, (24, BASE_HEIGHT - 34))
        return

    # Original splash fallback
    # Background
    window.game_surface.blit(
        assets.splash_background,
        (0, 0)
    )

    # ----------------------------
    # Bobbing suits
    # ----------------------------

    bob_amount = 10
    bob_speed = 1.5

    spade_bob = int(
        math.sin(
            elapsed_seconds
            * bob_speed
        )
        * bob_amount
    )

    diamond_bob = int(
        math.sin(
            elapsed_seconds
            * bob_speed
            + 0.7
        )
        * bob_amount
    )

    club_bob = int(
        math.sin(
            elapsed_seconds
            * bob_speed
            + 1.4
        )
        * bob_amount
    )

    heart_bob = int(
        math.sin(
            elapsed_seconds
            * bob_speed
            + 2.1
        )
        * bob_amount
    )

    window.game_surface.blit(
        assets.splash_spade,
        (0, spade_bob)
    )

    window.game_surface.blit(
        assets.splash_diamond,
        (0, diamond_bob)
    )

    window.game_surface.blit(
        assets.splash_club,
        (0, club_bob)
    )

    window.game_surface.blit(
        assets.splash_heart,
        (0, heart_bob)
    )

    # ----------------------------
    # Pulsing prompt
    # ----------------------------

    flash_speed = 4.0

    pulse = (
        math.sin(
            elapsed_seconds
            * flash_speed
        )
        + 1
    ) / 2

    prompt_alpha = int(
        60
        + pulse * 195
    )

    prompt_surface = (
        assets.splash_prompt.copy()
    )

    prompt_surface.set_alpha(
        prompt_alpha
    )

    window.game_surface.blit(
        prompt_surface,
        (0, 0)
    )


def handle_event(event):
    """Old main-loop event branch for STATE_SPLASH."""

    if (
        event.type == pygame.KEYDOWN
        or event.type
        == pygame.MOUSEBUTTONDOWN
    ):
        sounds.audio.play_sound(
            "button_click"
        )

        state.current_state = state_names.STATE_PROFILE_SELECT

        # Keep the music mode the player saved in Options (B14); with nothing saved (first
        # launch) start Ambient as before. set_music_mode does not restart music that is
        # already playing in that mode.
        sounds.audio.set_music_mode(
            options_screen.app_settings.get("music_mode")
            or "ambient"
        )


def draw():
    """Old draw-chain branch for STATE_SPLASH."""
    draw_splash_screen()
