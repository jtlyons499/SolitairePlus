import os
from pathlib import Path
import tempfile
import unittest
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
from profile_avatar_assets import load_avatar_bank, avatar_options

class AvatarAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init();pygame.display.set_mode((1,1))
    def test_all_new_counts_and_next_number_are_discovered(self):
        with tempfile.TemporaryDirectory() as root:
            for folder,prefix,count in [('eyes','eyes',17),('tops','top',14),('hair','hair',17),('glasses','glasses',10)]:
                path=Path(root)/folder;path.mkdir()
                image=pygame.Surface((4,4),pygame.SRCALPHA)
                for i in range(1,count+2):pygame.image.save(image,str(path/f'{prefix}_{i:02d}.png'))
                bank=load_avatar_bank(folder,root)
                self.assertEqual(len(bank),count+1)
                self.assertEqual(avatar_options(bank)[-1],f'{prefix}_{count+1:02d}')
                if folder=='glasses':self.assertIsNone(avatar_options(bank,True)[0])
    def test_unrelated_and_invalid_files_are_not_choices(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'eyes';path.mkdir()
            image=pygame.Surface((4,4),pygame.SRCALPHA)
            for name in ['eyes_01.png','eyes_02.png','preview.png','eyes_00.png']:
                pygame.image.save(image,str(path/name))
            (path/'eyes_03.png').write_bytes(b'broken PNG')
            self.assertEqual(avatar_options(load_avatar_bank('eyes',root)),['eyes_01','eyes_02'])
