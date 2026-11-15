"""Framing, portrait fallback and main-loop delegation."""
from tests.support import locate
import ast
import os
from pathlib import Path
import unittest
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame
from solitaireplus.npc.portrait_ui import draw_portrait, get_npc_initials

class PortraitUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
    def test_framing_and_oval_clipping(self):
        styles = {'score_four': {'shape': 'rect'}, 'holdem': {'shape': 'oval'}}
        for style in ('score_four', 'holdem', 'unknown'):
            with self.subTest(style=style):
                target = pygame.Surface((160, 160), pygame.SRCALPHA)
                portrait = pygame.Surface((80, 80), pygame.SRCALPHA)
                portrait.fill((250, 20, 10, 255))
                draw_portrait(target, {'name': 'Bob'}, pygame.Rect(20, 20, 100, 100),
                              style, styles, lambda npc, size: portrait,
                              pygame.font.Font(None, 24))
                self.assertEqual(tuple(target.get_at((70, 70)))[:3], (250, 20, 10))
                if style == 'holdem': self.assertEqual(target.get_at((20, 20)).a, 0)
                else: self.assertEqual(tuple(target.get_at((20, 20)))[:3], (255, 255, 255))
    def test_missing_portrait_draws_initials(self):
        target = pygame.Surface((100, 100), pygame.SRCALPHA)
        draw_portrait(target, {'name': 'Bert Footer'}, pygame.Rect(5, 5, 90, 90),
                      'score_four', {'score_four': {}}, lambda npc, size: None,
                      pygame.font.Font(None, 24))
        self.assertEqual(get_npc_initials({'name': 'Bert Footer'}), 'BF')
        self.assertTrue(any(target.get_at((x,y))[:3] == (255,255,255)
                            for x in range(25,75) for y in range(25,75)))
    def test_main_delegates_with_current_surface_and_loader(self):
        node = locate.function_node('draw_npc_portrait')
        seen = []
        values = [object() for _ in range(4)]
        env = dict(game_surface=values[0], NPC_PORTRAIT_STYLES=values[1],
                   get_npc_portrait_surface=values[2], score_four_score_font=values[3],
                   draw_framed_npc_portrait=lambda *args: seen.append(args))
        locate.namespace(env, [node])
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'integration', 'exec'), env)
        npc = {'name': 'Bert'};rect = pygame.Rect(0, 0, 50, 50)
        env['draw_npc_portrait'](npc, rect, 'holdem')
        self.assertEqual(seen, [(values[0],npc,rect,'holdem',values[1],values[2],values[3])])
