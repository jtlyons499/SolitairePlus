"""All authored paths, saved progress, one-time rewards and calendar handoff."""
import copy
import json
import unittest
from alien_night import STORY, new_alien_story, refresh_adventure_schedule
from career_activities import new_story, normalize_story, start_night, choose_option, requirement_reason

class AlienNightTests(unittest.TestCase):
    def test_every_choice_is_reachable_and_all_endings_and_rewards_work(self):
        seen=set();endings=set();cosmetics=set()
        def visit(story,cash):
            if story['finished']:
                endings.add(story['flags']['ending']);cosmetics.update(story['cosmetics'])
                self.assertEqual(normalize_story(json.loads(json.dumps(story)),data=STORY),story)
                return
            night=start_night(story,data=STORY)
            choices=STORY['scenes'][story['scene']]['options'];available=0
            for index,choice in enumerate(choices):
                if requirement_reason(story,choice,cash,data=STORY):continue
                available+=1;seen.add(choice['id'])
                branch=copy.deepcopy(story);snapshot=copy.deepcopy(night)
                receipt=choose_option(branch,snapshot,index,cash,data=STORY)
                self.assertIsNotNone(receipt)
                self.assertIsNone(choose_option(branch,snapshot,index,cash,data=STORY))
                restored=normalize_story(json.loads(json.dumps(branch)),data=STORY)
                self.assertEqual(restored,branch)
                visit(restored,cash+receipt['cash'])
            self.assertGreater(available,0)
        visit(new_alien_story(),0)
        self.assertEqual(seen,{c['id'] for scene in STORY['scenes'].values() for c in scene['options']})
        self.assertEqual(endings,{'pure_evil','too_late','little_green_men'})
        self.assertEqual(cosmetics,set(STORY['cosmetics']))
    def test_tidy_branch_routes_and_rewards(self):
        self.assertEqual(STORY['scenes']['decision_chip']['options'][0]['next'],'flight_good')
        self.assertEqual(STORY['scenes']['goobles_good']['options'][0]['text'],'Free Mr. Goobles')
        for scene,index,expected in [('decision_other',1,20000),('flight_evil',1,20000),('goobles_evil',1,5000),('goobles_good',0,20000)]:
            self.assertEqual(STORY['scenes'][scene]['options'][index]['effects']['cash'],expected)
    def test_calendar_switch_preserves_completed_history_and_current_receipt(self):
        bigfoot=new_story();alien=new_alien_story()
        schedule=[{'event_id':'bigfoot_night','completed':True},
                  {'event_id':'bigfoot_night','career_activity':{'claimed':True}},
                  {'event_id':'bigfoot_night'}]
        bigfoot['finished']=True
        refresh_adventure_schedule(schedule,bigfoot,alien,current_day=2)
        self.assertEqual(schedule[0]['event_id'],'bigfoot_night')
        self.assertEqual(schedule[1]['event_id'],'bigfoot_night')
        self.assertEqual(schedule[2]['event_id'],'alien_night')
        alien['finished']=True
        refresh_adventure_schedule(schedule,bigfoot,alien,current_day=2)
        self.assertEqual(schedule[2]['event_id'],'press_interview_01')
    def test_old_profiles_start_alien_without_resetting_bigfoot(self):
        bigfoot={'schema':2,'scene':'finished','visits':8,'items':['lucky_dart'],'flags':{'ending':'inner_circle'}}
        bigfoot=normalize_story(bigfoot)
        alien=normalize_story(None,data=STORY)
        self.assertTrue(bigfoot['finished']);self.assertEqual(alien['visits'],0)
        self.assertEqual(start_night(alien,data=STORY)['kind'],'alien')
