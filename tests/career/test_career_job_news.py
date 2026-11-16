"""B19: choosing a job on the Jobs screen spammed the news feed.

Every switch to another job added a "TAKES NEW SIDE JOB" story, so clicking back and forth between
jobs filled the 50-item news feed with copies. These tests click the real Jobs screen handler
(``career/jobs_screen.py`` ``handle_event``) and check that:
* clicking the job the player already has adds no news,
* switching jobs twice on one career day leaves one job story (naming the job the player ended on),
* a switch on a later career day gets its own story.
"""
import os
import types
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from solitaireplus.app import state
from solitaireplus.career import career_names
from solitaireplus.career import jobs_screen


class CareerJobNewsTests(unittest.TestCase):
    def setUp(self):
        self.saves = []
        self.fans = []
        self.sounds = []
        patches = [
            mock.patch.object(state, "game_mouse_pos", (0, 0), create=True),
            mock.patch.object(state, "player_name", "Tester", create=True),
            mock.patch.object(state, "current_state", None, create=True),
            mock.patch.object(state, "career_rating", 10 ** 9),
            mock.patch.object(state, "career_job", "custodian"),
            mock.patch.object(state, "career_fan_rewarded_jobs", {"custodian"}),
            mock.patch.object(state, "career_current_schedule", []),
            mock.patch.object(state, "career_news_items", []),
            mock.patch.object(state, "career_day", 5),
            mock.patch.object(state, "career_month", 3),
            mock.patch.object(state, "career_year", 2026),
            mock.patch.object(jobs_screen, "sounds",
                              types.SimpleNamespace(audio=types.SimpleNamespace(play_sound=self.sounds.append))),
            mock.patch.object(jobs_screen, "career_saving",
                              types.SimpleNamespace(auto_save_career=lambda: self.saves.append(True))),
            mock.patch.object(jobs_screen, "career_rewards",
                              types.SimpleNamespace(award_career_fans=lambda *args: self.fans.append(args))),
        ]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def click_job(self, job_id):
        pos = jobs_screen.career_job_option_rects[job_id].center
        state.game_mouse_pos = pos
        jobs_screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))

    def job_news(self):
        return [item for item in state.career_news_items if item.get("category") == "job"]

    def test_clicking_current_job_adds_no_news(self):
        self.click_job("custodian")
        self.click_job("custodian")
        self.assertEqual(state.career_job, "custodian")
        self.assertEqual(state.career_news_items, [])

    def test_switching_twice_in_one_day_adds_one_news_item(self):
        self.click_job("satellite_repair")
        self.click_job("videographer")
        self.assertEqual(state.career_job, "videographer")
        news = self.job_news()
        self.assertEqual(len(news), 1)
        self.assertEqual(len(state.career_news_items), 1)
        # The one story names the job the player ended the day with.
        self.assertIn(career_names.CAREER_JOB_NAMES["videographer"], news[0]["body"])
        self.assertEqual(news[0]["career_day"], 5)

    def test_switching_back_and_forth_in_one_day_adds_one_news_item(self):
        for job_id in ("satellite_repair", "custodian", "satellite_repair", "custodian", "videographer"):
            self.click_job(job_id)
        self.assertEqual(len(self.job_news()), 1)

    def test_switch_on_a_later_day_adds_another_news_item(self):
        self.click_job("satellite_repair")
        state.career_day += 1
        self.click_job("videographer")
        news = self.job_news()
        self.assertEqual(len(news), 2)
        self.assertEqual([item["career_day"] for item in news], [6, 5])

    def test_job_story_from_an_earlier_day_is_left_alone(self):
        self.click_job("satellite_repair")
        earlier = dict(self.job_news()[0])
        state.career_day += 1
        self.click_job("videographer")
        self.assertEqual(self.job_news()[1], earlier)

    def test_switching_still_saves_and_rewards_new_jobs(self):
        self.click_job("satellite_repair")
        self.click_job("videographer")
        self.assertEqual(len(self.fans), 2)
        self.assertEqual(state.career_fan_rewarded_jobs, {"custodian", "satellite_repair", "videographer"})
        self.assertEqual(len(self.saves), 2)


if __name__ == "__main__":
    unittest.main()
