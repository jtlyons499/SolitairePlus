import unittest
import pygame
from cosmetic_assets import normalize_cosmetic

class CosmeticAlignment(unittest.TestCase):
    def test_background_uses_logical_canvas(self):
        image = pygame.Surface((1920, 1080), pygame.SRCALPHA)
        self.assertEqual(normalize_cosmetic(image, 'backgrounds').get_size(), (1366, 768))

    def test_compact_title_centers_visible_art(self):
        image = pygame.Surface((900, 240), pygame.SRCALPHA)
        image.fill((0, 0, 0, 0))
        pygame.draw.rect(image, (255, 255, 255, 255), (10, 20, 800, 180))
        result = normalize_cosmetic(image, 'titles')
        bounds = result.get_bounding_rect()
        self.assertEqual(result.get_size(), (1366, 768))
        self.assertLessEqual(bounds.height, 140)
        self.assertLessEqual(bounds.width, 893)
        self.assertLessEqual(abs(bounds.centerx - pygame.Rect(252, 28, 893, 140).centerx), 1)
        self.assertLessEqual(abs(bounds.centery - 98), 1)

    def test_legacy_title_and_felt_preserved(self):
        image = pygame.Surface((1366, 768), pygame.SRCALPHA)
        self.assertIs(normalize_cosmetic(image, 'titles'), image)
        self.assertIs(normalize_cosmetic(image, 'felts'), image)
