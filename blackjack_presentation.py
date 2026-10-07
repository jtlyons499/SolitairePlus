"""Blackjack presentation using the player's existing background and felt artwork."""
import pygame

_logo = None
_logo_loaded = False
_felt_cache = {}

def draw_background(surface, background, felt):
    global _logo, _logo_loaded
    if background is not None:
        surface.blit(pygame.transform.smoothscale(background, surface.get_size()), (0, 0))
    else:
        surface.fill((18, 29, 37))
    shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    shade.fill((6, 12, 19, 145))
    surface.blit(shade, (0, 0))
    rail = pygame.Rect(345, 92, 680, 551)
    pygame.draw.rect(surface, (9, 15, 22), rail.move(0, 7), border_radius=54)
    pygame.draw.rect(surface, (61, 47, 36), rail, border_radius=54)
    inner = rail.inflate(-20, -20)
    key = id(felt), inner.size
    if key not in _felt_cache:
        layer = pygame.Surface(inner.size, pygame.SRCALPHA)
        if felt is not None:
            layer.blit(pygame.transform.smoothscale(felt, inner.size), (0, 0))
        else:
            layer.fill((32, 82, 71))
        mask = pygame.Surface(inner.size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=44)
        layer.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        _felt_cache.clear()
        _felt_cache[key] = layer
    surface.blit(_felt_cache[key], inner)
    pygame.draw.rect(surface, (200, 184, 131), inner, 2, border_radius=44)
    if not _logo_loaded:
        try: _logo = pygame.image.load('assets/blackjack/logo.png').convert_alpha()
        except (OSError, pygame.error): _logo = None
        _logo_loaded = True
    if _logo is not None:
        ratio = min(380/_logo.get_width(), 88/_logo.get_height())
        image = pygame.transform.smoothscale(_logo, (int(_logo.get_width()*ratio), int(_logo.get_height()*ratio)))
        surface.blit(image, image.get_rect(center=(683, 46)))
    else:
        label = pygame.font.Font(None, 46).render('BLACKJACK', True, (244, 235, 209))
        surface.blit(label, label.get_rect(center=(683, 46)))

def draw_button(surface, rect, label, mouse, font, selected=False):
    hover = selected or (mouse is not None and rect.collidepoint(mouse))
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(layer, (54, 89, 106, 225) if hover else (12, 28, 40, 215), layer.get_rect(), border_radius=12)
    pygame.draw.rect(layer, (148, 224, 244, 245) if hover else (140, 171, 184, 220), layer.get_rect(), 2, border_radius=12)
    surface.blit(layer, rect)
    text = font.render(label, True, (243, 246, 246))
    surface.blit(text, text.get_rect(center=rect.center))
