"""Compact eight-trait panel for the Career ranking bio screen."""
import pygame
from npc_personality import get_npc_traits, TRAIT_NAMES, TRAIT_LABELS


def draw_npc_traits(surface, npc, rect, font):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, (250, 250, 250), rect)
    pygame.draw.rect(surface, (40, 40, 40), rect, 2)
    title = font.render("PERSONALITY TRAITS", True, (25, 25, 25))
    surface.blit(title, (rect.x + 18, rect.y + 10))
    traits = get_npc_traits(npc)
    col_width = (rect.width - 36)//2
    for index, key in enumerate(TRAIT_NAMES):
        column, row = divmod(index, 4)
        x = rect.x + 18 + column*col_width
        y = rect.y + 37 + row*27
        label = font.render(f"{TRAIT_LABELS[key]}: {traits[key]}/10", True, (35, 35, 35))
        surface.blit(label, (x, y))
        bar = pygame.Rect(x + col_width - 142, y + 4, 118, 12)
        pygame.draw.rect(surface, (220, 225, 220), bar, border_radius=4)
        fill = bar.copy()
        fill.width = max(1, round(bar.width*traits[key]/10))
        pygame.draw.rect(surface, (38, 114, 76), fill, border_radius=4)
