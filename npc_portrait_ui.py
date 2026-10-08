"""Draw framed NPC portraits without depending on the main game loop."""
import pygame

def get_npc_initials(npc):
    name_parts = npc.get('name', 'NPC').split()
    initials = ''.join((part[0] for part in name_parts[:2] if part))
    return initials.upper()

def draw_portrait(surface, npc, rect, style_id, styles, portrait_loader, initials_font):
    style = styles.get(style_id, styles['score_four'])
    shape = style.get('shape', 'rect')
    border_width = style.get('border_width', 2)
    padding = style.get('padding', 5)
    inner_rect = rect.inflate(-padding * 2, -padding * 2)
    portrait_size = max(inner_rect.width, inner_rect.height)
    portrait = portrait_loader(npc, portrait_size)
    if shape == 'rect':
        pygame.draw.rect(surface, (55, 70, 60), rect)
        if portrait is not None:
            scaled_portrait = pygame.transform.smoothscale(portrait, (inner_rect.width, inner_rect.height))
            surface.blit(scaled_portrait, inner_rect.topleft)
        else:
            initials = get_npc_initials(npc)
            initials_surface = initials_font.render(initials, True, (255, 255, 255))
            initials_rect = initials_surface.get_rect(center=rect.center)
            surface.blit(initials_surface, initials_rect)
        pygame.draw.rect(surface, (255, 255, 255), rect, border_width)
        return
    if shape == 'oval':
        oval_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.ellipse(oval_surface, (55, 70, 60, 255), oval_surface.get_rect())
        if portrait is not None:
            scaled_portrait = pygame.transform.smoothscale(portrait, (inner_rect.width, inner_rect.height))
            portrait_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            portrait_surface.blit(scaled_portrait, (padding, padding))
            mask_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.ellipse(mask_surface, (255, 255, 255, 255), mask_surface.get_rect())
            portrait_surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            oval_surface.blit(portrait_surface, (0, 0))
        else:
            initials = get_npc_initials(npc)
            initials_surface = initials_font.render(initials, True, (255, 255, 255))
            initials_rect = initials_surface.get_rect(center=(rect.width // 2, rect.height // 2))
            oval_surface.blit(initials_surface, initials_rect)
        pygame.draw.ellipse(oval_surface, (255, 255, 255), oval_surface.get_rect(), border_width)
        surface.blit(oval_surface, rect.topleft)
