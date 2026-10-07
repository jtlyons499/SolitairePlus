import ast
import copy
import json
import unittest
from pathlib import Path
import pygame
from career_activities import new_story, normalize_story, start_night, choose_option, chapter
from career_activities_ui import CareerActivityScreen

class BigfootTests(unittest.TestCase):
    def test_exact_first_night_rewards_and_branch(self):
        for index, cash, fans, location in ((0,50,50,'Camp'),(1,-50,0,'Camp'),(2,0,100,'Forest')):
            story=new_story();night=start_night(story)
            receipt=choose_option(story,night,index,100)
            self.assertEqual((receipt['cash'],receipt['fans'],story['location']),(cash,fans,location))
            self.assertIsNone(choose_option(story,night,index,100))
            self.assertEqual(story['visits'],1)

    def test_shoes_unlock_next_visit_choice(self):
        story=new_story();night=start_night(story)
        self.assertIsNone(choose_option(story,night,1,20))
        choose_option(story,night,1,50)
        restored=normalize_story(json.loads(json.dumps(story)))
        next_night=start_night(restored)
        self.assertEqual(next_night['night'],2)
        self.assertIn('Sasquatch Shoes',next_night['options'][1]['name'])
        self.assertEqual(next_night['options'][1]['fans'],150)
        choose_option(restored,next_night,1,0)
        self.assertEqual(restored['location'],'Forest')
        self.assertEqual(len(chapter(restored)['options']),4)

    def test_full_route_and_return(self):
        story=new_story()
        for index in (2,0,0):
            choose_option(story,start_night(story),index,100)
        self.assertEqual(story['location'],'Camp')
        self.assertEqual(story['visits'],3)
        self.assertEqual(story['clues'],3)

    def test_none_mouse_and_all_screens(self):
        pygame.init();pygame.display.set_mode((1,1))
        screen=CareerActivityScreen();surface=pygame.Surface((1366,768))
        for location in ('Camp','Forest','Clearing'):
            story=new_story();story.update(location=location,shoes=True,visits=3)
            night=start_night(story)
            screen.draw(surface,night,None,100,story)
            self.assertIsNone(screen.click(None))
            for rect,action,enabled in screen.buttons:
                self.assertLessEqual(rect.bottom,725)
            choose_option(story,night,0,100)
            screen.draw(surface,night,None,100,story)
        pygame.quit()

    def test_main_integration_claims_once_and_resumes(self):
        tree=ast.parse(Path('main.py').read_text())
        names={'start_career_activity','handle_career_activity'}
        code=compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'main.py','exec')
        scope=dict(new_story=new_story,start_night=start_night,choose_option=choose_option,
          career_current_schedule=[{}],career_day_of_month=1,career_bigfoot_story=new_story(),
          career_cash=100,STATE_CAREER_ACTIVITY='story',STATE_CAREER_HUB='hub',
          auto_save_career=lambda:None,award_career_fans=lambda n,r:n,advance_career_day=lambda **kw:None)
        exec(code,scope)
        scope['start_career_activity']()
        scope['handle_career_activity'](('choice',0))
        scope['handle_career_activity'](('choice',0))
        self.assertEqual(scope['career_cash'],150)
        scope['start_career_activity']()
        self.assertTrue(scope['career_current_schedule'][0]['career_activity']['claimed'])
        self.assertEqual(scope['career_bigfoot_story']['visits'],1)
