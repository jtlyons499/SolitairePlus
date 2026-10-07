import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
import pygame
from score_four_ui import hint_meter_surface
from poker_recap import recap_lines, recap_display_lines, draw_recap
from career_event_progress import restore_event_progress, store_event_progress

class ReadabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
    @classmethod
    def tearDownClass(cls):
        pygame.quit()
    def test_meter_never_paints_outside_inset_even_at_tiny_progress(self):
        for progress in (0, .001, .01, .05, .5, 1, -1, 2):
            image = hint_meter_surface((116, 46), progress)
            bounds = image.get_bounding_rect()
            if bounds.width:
                self.assertTrue(pygame.Rect(3, 3, 110, 40).contains(bounds), (progress,bounds))
            if progress <= 0:
                self.assertEqual(bounds.width, 0)
    def test_long_payouts_wrap_without_losing_words_or_shrinking_font(self):
        game = SimpleNamespace(last_pot_awards=[{'amount':300, 'hand':'Pair of Kings with Ace Queen Jack kickers '*5, 'winners':[0,1], 'share':150, 'eligible':[0,1]}], get_table_player_name=lambda seat: 'You' if seat==0 else 'A very long opponent name', player_hand_contribution=100, hand_complete=True, recap_open=True, recap_page=0)
        rows = recap_display_lines(game)
        self.assertEqual(' '.join(' '.join(rows).split()), ' '.join(' '.join(recap_lines(game)).split()))
        font=pygame.font.Font(None,32)
        self.assertTrue(all(font.size(row)[0] <=800 for row in rows))
        draw_recap(pygame.Surface((1366,768)), None, game)
    def test_night_recap_keeps_starting_snapshot_after_reentry(self):
        namespace={'current_game_mode':'career', 'career_rating':1000, 'career_ratings':dict(strategy=1000,poker=1000,casino=1000), 'career_fans':10}
        entry={}
        restore_event_progress(entry,namespace)
        namespace.update(career_rating=1040.4,career_ratings=dict(strategy=1060.5,poker=1020.2,casino=1000),career_fans=17)
        store_event_progress(entry,namespace)
        restore_event_progress(entry,namespace)
        tree=ast.parse(Path('main.py').read_text())
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='build_career_event_summary')
        namespace['_build_career_event_summary']=lambda:namespace.update(career_event_summary_lines=['Night completed.','Current Rating: 1040.4','Current Fans: 17'])
        exec(compile(ast.Module(body=[function],type_ignores=[]),'night summary','exec'),namespace)
        namespace['build_career_event_summary']()
        self.assertIn('Global Rating: 1,040 (+40)',namespace['career_event_summary_lines'])
        self.assertIn('Strategy +60  |  Poker +20',namespace['career_event_summary_lines'])
        self.assertIn('Fans: 17 (+7)',namespace['career_event_summary_lines'])
