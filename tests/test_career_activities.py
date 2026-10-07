import ast
import copy
import json
import unittest
from pathlib import Path
import pygame
from career_activities import (STORY,new_story,normalize_story,start_night,choose_option,
 requirement_reason,validate_story,add_story_catalogs,reconcile_story_cosmetics)
from career_activities_ui import CareerActivityScreen

class BigfootTests(unittest.TestCase):
    def test_all_playable_paths_finish_and_unlock_all_endings(self):
        endings=set();cosmetics=set();paths=[]
        def walk(story,cash,depth):
            self.assertLess(depth,10)
            if story['finished']:
                endings.add(story['flags']['ending']);cosmetics.update(story['cosmetics']);paths.append(story)
                self.assertEqual(start_night(story)['stage'],'complete')
                self.assertIsNone(choose_option(story,start_night(story),0,cash))
                return
            night=start_night(story);available=0
            for i,option in enumerate(night['options']):
                if requirement_reason(story,option,cash):continue
                available+=1;branch=copy.deepcopy(story);outing=copy.deepcopy(night)
                receipt=choose_option(branch,outing,i,cash)
                self.assertIsNotNone(receipt)
                self.assertIsNone(choose_option(branch,outing,i,cash))
                restored=normalize_story(json.loads(json.dumps(branch)))
                self.assertEqual(restored,branch)
                walk(restored,cash+receipt['cash'],depth+1)
            self.assertGreater(available,0)
        walk(new_story(),100,0)
        self.assertEqual(endings,{'reverent','inner_circle','cast_out'})
        self.assertEqual(cosmetics,set(STORY['cosmetics']))
        self.assertGreater(len(paths),20)

    def test_cash_and_item_gates(self):
        story=new_story();night=start_night(story)
        self.assertIsNone(choose_option(story,night,1,49))
        self.assertEqual(story['visits'],0)
        choose_option(story,night,0,0)
        self.assertIn('lucky_dart',story['items'])
        self.assertEqual(story['scene'],'hq_social')
        choose_option(story,start_night(story),0,50)
        self.assertEqual(story['scene'],'camp_arrival')
        self.assertEqual(story['visits'],2)
        self.assertTrue(requirement_reason(story,STORY['scenes']['mountain_campsite']['options'][1],100))

    def test_confirmed_rewards_and_connections(self):
        dart=STORY['scenes']['mountain_campsite']['options'][2]
        self.assertEqual(dart['next'],'ladder');self.assertEqual(dart['requires']['items'],['lucky_dart'])
        inner=STORY['scenes']['ladder']['options'][1]
        self.assertEqual(inner['effects']['cash'],20000)
        self.assertIn('$20,000',inner['result'])

    def test_validation_catches_broken_links(self):
        data=copy.deepcopy(STORY);data['scenes']['hq_start']['options'][0]['next']='missing'
        with self.assertRaises(ValueError):validate_story(data)

    def test_legacy_progress_migrates_without_resetting_day_count(self):
        state=normalize_story({'visits':4,'shoes':True,'location':'Forest'})
        self.assertEqual(state['visits'],4);self.assertEqual(state['scene'],'hq_start')
        self.assertEqual(state['items'],['sasquatch_sandals'])

    def test_rewards_reconcile_to_catalogs(self):
        catalogs=[{}, {}, {}];add_story_catalogs(*catalogs)
        story=new_story();story['cosmetics']=list(STORY['cosmetics'])
        unlocked=[set(),set(),set()];reconcile_story_cosmetics(story,*unlocked)
        for catalog,values in zip(catalogs,unlocked):self.assertEqual(set(catalog),values)

    def test_every_scene_and_result_renders_with_none_mouse(self):
        pygame.init();pygame.display.set_mode((1,1));surface=pygame.Surface((1366,768));screen=CareerActivityScreen()
        for scene_id,scene in STORY['scenes'].items():
            story=new_story();story.update(scene=scene_id,location=scene['location'])
            night=start_night(story);screen.draw(surface,night,None,100,story)
            screen.view='choices';screen.draw(surface,night,None,100,story)
            for rect,action,enabled in screen.buttons:self.assertLessEqual(rect.bottom,740)
            self.assertIsNone(screen.click(None))
            for choice in scene['options']:
                night.update(claimed=True,result_text=choice['result'],cash_change=choice['effects']['cash'],fan_change=choice['effects']['fans'],earned_cosmetics=choice['effects']['cosmetics'])
                screen.draw(surface,night,None,100,story)
        pygame.quit()

    def test_main_claims_once_and_reopens_current_result(self):
        tree=ast.parse(Path('main.py').read_text());names={'start_career_activity','handle_career_activity'}
        code=compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'main.py','exec')
        scope=dict(start_night=start_night,choose_option=choose_option,reconcile_story_cosmetics=reconcile_story_cosmetics,
          career_current_schedule=[{}],career_day_of_month=1,career_bigfoot_story=new_story(),career_cash=100,
          unlocked_menu_backgrounds=set(),unlocked_felts=set(),unlocked_titles=set(),
          STATE_CAREER_ACTIVITY='story',STATE_CAREER_HUB='hub',auto_save_career=lambda:None,
          award_career_fans=lambda n,r:n,advance_career_day=lambda **kw:None)
        exec(code,scope);scope['start_career_activity']();scope['handle_career_activity'](('choice',0))
        scope['handle_career_activity'](('choice',0));scope['start_career_activity']()
        self.assertEqual(scope['career_cash'],150)
        self.assertEqual(scope['career_bigfoot_story']['visits'],1)
        self.assertTrue(scope['career_current_schedule'][0]['career_activity']['claimed'])
