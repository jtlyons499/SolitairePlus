"""NPC portraits as the game's screens draw them (moved out of legacy.py).

get_npc_portrait_surface(npc, size): the NPC's portrait image at that size (its own portrait file,
loaded once per size, else composed from the artist's layers). draw_npc_portrait(npc, rect,
style_id): a framed portrait on the game surface, in a table's style (NPC_PORTRAIT_STYLES).
"""
import pygame

from solitaireplus.app import window
from solitaireplus.app.lazy import lazy
from solitaireplus.npc.portrait_ui import draw_portrait as draw_framed_npc_portrait
from solitaireplus.npc.portraits import draw_layered_portrait
fonts = lazy("solitaireplus.app.fonts")

NPC_PORTRAIT_STYLES = {
    "score_four": {
        "shape": "rect",
        "border_width": 2,
        "padding": 5,
    },

    "blackjack": {
        "shape": "rect",
        "border_width": 2,
        "padding": 5,
    },

    "holdem": {
        "shape": "oval",
        "border_width": 3,
        "padding": 6,
    },
}


def draw_npc_portrait(npc, rect, style_id):
    draw_framed_npc_portrait(
        window.game_surface, npc, rect, style_id, NPC_PORTRAIT_STYLES,
        get_npc_portrait_surface, fonts.score_four_score_font
    )

def get_npc_portrait_surface(npc, size):
    portrait_path = npc.get("portrait")
    if portrait_path:
        cache_key = (portrait_path, size)
        if cache_key in npc_icon_cache:
            return npc_icon_cache[cache_key]
        try:
            image = pygame.image.load(portrait_path).convert_alpha()
            image = pygame.transform.smoothscale(image, (size, size))
            npc_icon_cache[cache_key] = image
            return image
        except (pygame.error, FileNotFoundError):
            pass
    return draw_layered_portrait(npc, size)

npc_icon_cache = {}
