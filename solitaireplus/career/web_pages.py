"""The career 'web browser' look shared by the jobs, real-estate and news pages (moved out of legacy.py)."""
from solitaireplus.games.solitaire.rules import BASE_WIDTH
from solitaireplus.app import paths
import pygame
from solitaireplus.app.lazy import lazy
window = lazy("solitaireplus.app.window")
fonts = lazy("solitaireplus.app.fonts")


CAREER_BROWSER_HEADER_HEIGHT = 64

career_web_image_cache = {}

career_subpage_back_rect = pygame.Rect(
    533,
    715,
    300,
    45
)

def get_career_web_image(
        filename,
        size=None
):
    cache_key = (
        filename,
        size
    )

    if (
        cache_key
        in career_web_image_cache
    ):
        return (
            career_web_image_cache[
                cache_key
            ]
        )

    path = str(paths.asset((
        "career/web/"
        + filename
    )))

    try:
        image = pygame.image.load(
            path
        ).convert_alpha()

        if size is not None:
            image = (
                pygame.transform.smoothscale(
                    image,
                    size
                )
            )

        career_web_image_cache[
            cache_key
        ] = image

        return image

    except (
        pygame.error,
        FileNotFoundError
    ):
        return None

def draw_career_browser_header(
        url_text
):
    browser_header = (
        get_career_web_image(
            "browser_header.png",
            (
                BASE_WIDTH,
                CAREER_BROWSER_HEADER_HEIGHT
            )
        )
    )

    if browser_header is not None:
        window.game_surface.blit(
            browser_header,
            (
                0,
                0
            )
        )

    url_surface = (
        fonts.option_value_font.render(
            url_text,
            True,
            (
                0,
                0,
                0
            )
        )
    )

    # Center the URL inside the
    # white address field.
    url_rect = (
        url_surface.get_rect(
            midleft=(
                365,
                32
            )
        )
    )

    window.game_surface.blit(
        url_surface,
        url_rect
    )
