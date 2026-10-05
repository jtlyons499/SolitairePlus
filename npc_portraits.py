"""Built-in illustrated prospect portraits, with optional PNG art overrides."""
import random
import pygame

from career_npc_development import stable_seed

SKINS = ((246, 215, 181), (232, 188, 145), (207, 153, 107), (177, 119, 78),
         (143, 88, 58), (110, 66, 45), (86, 52, 38))
HAIR = ((38, 30, 27), (83, 50, 30), (143, 83, 39), (198, 149, 72), (191, 64, 33), (57, 49, 62))
SHIRTS = ((48, 101, 141), (135, 66, 83), (48, 118, 96), (125, 94, 149),
          (178, 115, 53), (66, 76, 117), (115, 137, 55), (164, 85, 64))
_cache = {}


def draw_builtin_portrait(npc, size):
    """Return a finished character portrait; no assets or font are required."""
    style = npc.get("portrait_style") or {}
    seed = int(style.get("seed", stable_seed(npc.get("id"), "portrait")))
    age = int(npc.get("age", 10))
    age_band = "child" if age < 13 else "teen" if age < 20 else "adult" if age < 50 else "veteran"
    key = (seed, age_band, int(size))
    if key in _cache:
        return _cache[key]
    rng = random.Random(seed)
    skin = SKINS[int(style.get("skin", rng.randrange(len(SKINS)))) % len(SKINS)]
    hair = HAIR[int(style.get("hair", rng.randrange(len(HAIR)))) % len(HAIR)]
    shirt = SHIRTS[int(style.get("shirt", rng.randrange(len(SHIRTS)))) % len(SHIRTS)]
    cut = int(style.get("cut", rng.randrange(5))) % 5
    glasses = bool(style.get("glasses", rng.random() < 0.2))
    # Render large and downsample for clean curves at table/icon sizes.
    surface = pygame.Surface((400, 400), pygame.SRCALPHA)
    surface.fill((20, 42, 48))
    glow = pygame.Surface((400, 400), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*shirt, 75), (200, 155), 160)
    surface.blit(glow, (0, 0))
    pygame.draw.circle(surface, (219, 205, 155, 50), (345, 66), 36)
    pygame.draw.circle(surface, (219, 205, 155, 30), (55, 310), 48)
    pygame.draw.ellipse(surface, (11, 24, 29), (35, 293, 330, 140))
    pygame.draw.ellipse(surface, shirt, (45, 282, 310, 186))
    pygame.draw.polygon(surface, (229, 226, 205), [(150, 281), (200, 327), (250, 281), (239, 275), (161, 275)])
    pygame.draw.rect(surface, skin, (170, 235, 60, 68), border_radius=18)
    shade = tuple(max(0, channel - 20) for channel in skin)
    pygame.draw.ellipse(surface, shade, (170, 235, 60, 30))
    if cut in (1, 4):
        pygame.draw.ellipse(surface, hair, (88, 58, 226, 254))
    if cut == 4:
        pygame.draw.ellipse(surface, hair, (68, 150, 52, 150))
        pygame.draw.ellipse(surface, hair, (278, 150, 52, 150))
    pygame.draw.ellipse(surface, skin, (94, 153, 40, 60))
    pygame.draw.ellipse(surface, skin, (266, 153, 40, 60))
    pygame.draw.ellipse(surface, skin, (108, 76, 184, 204))
    pygame.draw.arc(surface, shade, (122, 93, 157, 174), 3.25, 6.15, 3)
    if age_band == "veteran":
        hair = tuple(min(220, int(value * 0.45 + 120)) for value in hair)
    if cut == 0:
        pygame.draw.ellipse(surface, hair, (105, 58, 190, 88))
        pygame.draw.polygon(surface, skin, [(132, 122), (221, 94), (277, 134), (277, 169), (129, 167)])
    elif cut == 1:
        pygame.draw.ellipse(surface, hair, (108, 60, 186, 94))
        pygame.draw.polygon(surface, skin, [(135, 135), (220, 87), (275, 137), (265, 168), (139, 168)])
    elif cut == 2:
        for x, y, radius in ((133, 89, 35), (174, 76, 38), (220, 76, 37), (263, 96, 35), (108, 121, 22), (289, 125, 20)):
            pygame.draw.circle(surface, hair, (x, y), radius)
    elif cut == 3:
        pygame.draw.polygon(surface, hair, [(110, 140), (108, 89), (145, 98), (157, 51),
                                           (185, 84), (218, 45), (233, 87), (272, 72), (290, 146), (252, 108), (149, 112)])
    else:
        pygame.draw.ellipse(surface, hair, (105, 61, 190, 96))
        pygame.draw.polygon(surface, skin, [(134, 125), (200, 97), (264, 128), (275, 174), (125, 174)])
    eye_y = 177 if age_band == "child" else 171
    pygame.draw.line(surface, hair, (139, eye_y - 22), (168, eye_y - 26), 5)
    pygame.draw.line(surface, hair, (232, eye_y - 26), (261, eye_y - 22), 5)
    for x in (154, 246):
        pygame.draw.ellipse(surface, (249, 247, 234), (x - 18, eye_y - 10, 36, 22))
        pygame.draw.circle(surface, (66, 69, 53), (x, eye_y + 1), 10)
        pygame.draw.circle(surface, (26, 27, 26), (x, eye_y + 1), 6)
        pygame.draw.circle(surface, (255, 255, 246), (x + 3, eye_y - 3), 3)
    pygame.draw.lines(surface, shade, False, [(201, 184), (194, 211), (208, 213)], 4)
    pygame.draw.arc(surface, (117, 65, 53), (166, 209, 68, 39), 3.3, 6.05, 4)
    if glasses:
        for x in (126, 218):
            pygame.draw.rect(surface, (33, 40, 51), (x, eye_y - 17, 56, 37), 5, border_radius=12)
        pygame.draw.line(surface, (33, 40, 51), (182, eye_y), (218, eye_y), 4)
        pygame.draw.line(surface, (33, 40, 51), (108, eye_y), (126, eye_y), 4)
        pygame.draw.line(surface, (33, 40, 51), (274, eye_y), (292, eye_y), 4)
    pygame.draw.circle(surface, (228, 206, 145), (298, 348), 14)
    pygame.draw.polygon(surface, (29, 52, 65), [(298, 336), (309, 348), (298, 360), (287, 348)])
    image = pygame.transform.smoothscale(surface, (int(size), int(size)))
    _cache[key] = image
    return image
