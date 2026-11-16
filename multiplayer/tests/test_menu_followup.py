"""Exercise the real launcher loop and the lobby Quit button."""
import os
import tempfile
import unittest
from unittest.mock import patch
import pygame
import main

class MenuFollowupTests(unittest.TestCase):
    def setUp(self):
        self.original_cwd=os.getcwd()
        os.chdir(main.ROOT)
        pygame.init();pygame.display.set_mode((1366,768))
    def tearDown(self):
        os.chdir(self.original_cwd)
        pygame.quit()
    def test_launcher_starts_and_quits(self):
        # Moved from the deleted test_standalone.py; same event batches. A temporary
        # LOCALAPPDATA keeps the real multiplayer profile and options untouched.
        batches=[[],[pygame.event.Event(pygame.TEXTINPUT,text='John'),pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN)],[],[pygame.event.Event(pygame.KEYDOWN,key=pygame.K_1,unicode='1')],[],[pygame.event.Event(pygame.QUIT)]]
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ,{'LOCALAPPDATA':folder}), \
             patch('pygame.event.get',side_effect=batches) as events:
            main.main()
        self.assertEqual(events.call_count,len(batches))
    def test_lobby_quit_button_ends_the_loop(self):
        event=pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(820,35))
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ,LOCALAPPDATA=folder), \
             patch('pygame.mouse.get_pos',return_value=(820,35)), \
             patch('pygame.event.get',side_effect=[[event]]) as events, \
             patch.object(main.Options,'display',side_effect=lambda:pygame.display.set_mode((1366,768))):
            main.main()
            self.assertEqual(events.call_count,1)
