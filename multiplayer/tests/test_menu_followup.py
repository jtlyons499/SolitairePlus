"""Exercise the lobby Quit button and practice utility ownership."""
import os
import tempfile
import unittest
from unittest.mock import patch
import pygame
import main
import texas_holdem_ui as ui
from standalone_table import StandaloneTable
from standalone_view import TableView

class MenuFollowupTests(unittest.TestCase):
    def setUp(self):
        self.original_cwd=os.getcwd()
        os.chdir(main.ROOT)
        pygame.init();pygame.display.set_mode((1366,768))
    def tearDown(self):
        os.chdir(self.original_cwd)
        pygame.quit()
    def test_lobby_quit_button_ends_the_loop(self):
        event=pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(820,35))
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ,LOCALAPPDATA=folder), \
             patch('pygame.mouse.get_pos',return_value=(820,35)), \
             patch('pygame.event.get',side_effect=[[event]]) as events, \
             patch.object(main.Options,'display',side_effect=lambda:pygame.display.set_mode((1366,768))):
            main.main()
            self.assertEqual(events.call_count,1)
    def test_practice_does_not_draw_its_own_options_exit_buttons(self):
        surface=pygame.Surface((1366,768));table=StandaloneTable('Tester')
        with patch.object(ui,'draw_modern_button',wraps=ui.draw_modern_button) as button:
            TableView(surface).draw(table)
            rects=[call.args[1] for call in button.call_args_list]
        self.assertNotIn(ui.holdem_options_rect,rects)
        self.assertNotIn(ui.holdem_exit_rect,rects)
