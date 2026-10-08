"""Artwork reload, safe failures, sizing and Career asset routing."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame
from shared.image_cache import ImageCache
import career_asset_images as career

class ImageCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init();pygame.display.set_mode((1,1))
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cache = ImageCache(self.root, refresh_interval=0)
    def save(self, name, color, size=(80,40)):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True)
        image=pygame.Surface(size,pygame.SRCALPHA);image.fill(color)
        pygame.image.save(image,str(p));return p
    def test_missing_added_changed_corrupt_and_removed_art(self):
        self.assertIsNone(self.cache.load('art.png'))
        p=self.save('art.png',(255,0,0,255))
        self.assertEqual(self.cache.load('art.png').get_at((0,0)).r,255)
        self.save('art.png',(0,0,255,255),(81,41))
        self.assertEqual(self.cache.load('art.png').get_at((0,0)).b,255)
        p.write_bytes(b'invalid PNG')
        self.assertIsNone(self.cache.load('art.png'))
        self.save('art.png',(0,255,0,255))
        self.assertEqual(self.cache.load('art.png').get_at((0,0)).g,255)
        p.unlink();self.assertIsNone(self.cache.load('art.png'))
    def test_fit_stretch_and_cache_reuse(self):
        self.save('flag.png',(1,2,3,255))
        fit=self.cache.load('flag.png',(30,20),fit=True)
        self.assertEqual(fit.get_size(),(30,15))
        self.assertIs(fit,self.cache.load('flag.png',(30,20),fit=True))
        self.assertEqual(self.cache.load('flag.png',(30,20)).get_size(),(30,20))
        with self.assertRaises(ValueError):self.cache.load('flag.png',(0,20))
    def test_cache_is_bounded(self):
        cache=ImageCache(self.root,maximum=2)
        for name in ('one.png','two.png','three.png'):cache.load(name)
        self.assertEqual(len(cache._entries),2)
        cache.clear();self.assertEqual(len(cache._entries),0)
    def test_career_routes_and_flag_aliases(self):
        self.save('assets/ui/flags/USA.png',(50,60,70,255))
        self.save('assets/career/hub/test.png',(70,80,90,255))
        self.save('assets/career/jobfinder/test.png',(90,80,70,255))
        self.save('assets/career/realestate/test.png',(10,20,30,255))
        with patch.object(career,'_cache',self.cache):
            self.assertEqual(career.get_country_flag_surface(' us ').get_size(),(30,15))
            self.assertIsNone(career.get_country_flag_surface(''))
            self.assertEqual(career.get_career_hub_image('test.png').get_at((0,0)).r,70)
            self.assertEqual(career.get_jobfinder_image('test.png',(10,10)).get_size(),(10,10))
            self.assertEqual(career.get_realestate_image('test.png').get_at((0,0)).r,10)
