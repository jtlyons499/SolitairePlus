"""B20: bad story-activity data on the calendar must not crash the Career activity screen.

The activity screen read state.career_current_schedule[day - 1]["career_activity"] and then
activity["claimed"] in its draw and click handler. A calendar day without that key, or with a
value that is not a dict, raised every frame. A malformed activity is now skipped: nothing is
drawn or paid, the day is not used, and the draw sends the player back to the calendar.

Second pass: the real screen (CareerActivityScreen.draw) also indexes keys inside the activity:
"night", "claimed", "intro", "options", "cash_change", "fan_change", and the choice effects and
earned cosmetics, which it looks up in the story catalogs. start_career_activity kept a dict such
as {"kind": "bigfoot", "version": 2} or {"kind": "bigfoot", "claimed": True}, and then the draw raised
KeyError every frame. activities.night_is_valid() now says whether the screen can show a night. The
screen and the click handler treat a night that fails it like a missing one (no crash, no reward).
start_career_activity replaces a malformed night with a fresh one only when it is not claimed. A
claimed one is kept as it is and the hub stays open, so a claimed calendar day can't pay again.
The calendar lookups (start_career_activity, the hub's calendar button and
complete_career_work_day) also stop safely at an empty or short schedule, a day of 0 or less
(which used to wrap round to the last day) and a day entry that is not a dict.
"""
import copy
import os
import types
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from tests.support import locate
from solitaireplus.career.activities import (STORY, choose_option, new_story, night_is_valid,
                                             reconcile_story_cosmetics, start_night)
from solitaireplus.career.activities_ui import CareerActivityScreen
from solitaireplus.career.alien_night import STORY as ALIEN_STORY, new_alien_story, refresh_adventure_schedule
from solitaireplus.career.hub_controls import CareerHubControls

SCREEN_FILE = "solitaireplus/career/activity_screen.py"
HUB_FILE = "solitaireplus/career/hub_screen.py"
BAD_ACTIVITIES = (None, "broken", 7, ["claimed"])
JOB_PAY = 40


def setUpModule():
    pygame.init()


class FakeActivityScreen:
    def __init__(self):
        self.buttons = ["stale button"]
        self.drawn = []

    def draw(self, surface, activity, mouse, cash, story):
        self.drawn.append(activity)


def make_env(schedule, day=1, real_screen=False):
    env = dict(
        career_current_schedule=schedule, career_day_of_month=day, career_cash=100,
        career_bigfoot_story=new_story(), career_alien_story=new_alien_story(),
        game_mouse_pos=None, current_state="activity",
        STATE_CAREER_ACTIVITY="activity", STATE_CAREER_HUB="hub",
        STATE_CAREER_EVENT="event", STATE_CAREER_EVENT_SELECT="event_select",
        career_activity_screen=CareerActivityScreen() if real_screen else FakeActivityScreen(),
        game_surface=pygame.Surface((1366, 768)) if real_screen else object(),
        draw_submenu_background=lambda **kw: None,
        choose_option=choose_option, reconcile_story_cosmetics=reconcile_story_cosmetics,
        refresh_adventure_schedule=refresh_adventure_schedule, start_night=start_night,
        night_is_valid=night_is_valid, ALIEN_STORY=ALIEN_STORY,
        unlocked_menu_backgrounds=set(), unlocked_felts=set(), unlocked_titles=set(),
        career_job="custodian", CAREER_JOBS={"custodian": {"pay": JOB_PAY}},
        saves=[], days_advanced=[], fans_awarded=[],
    )
    env["auto_save_career"] = lambda: env["saves"].append(1)
    env["advance_career_day"] = lambda **kw: env["days_advanced"].append(kw)
    env["award_career_fans"] = lambda n, reason: env["fans_awarded"].append(n) or n
    locate.exec_functions(["draw", "handle_career_activity", "current_career_activity"], env, path=SCREEN_FILE)
    locate.exec_functions(["start_career_activity", "current_career_schedule_entry", "complete_career_work_day",
                           "get_current_career_activity"], env, path=HUB_FILE)
    return env


def bad_schedules():
    yield "day without career_activity", [{"event_id": "bigfoot_night"}]
    for value in BAD_ACTIVITIES:
        yield f"career_activity={value!r}", [{"event_id": "bigfoot_night", "career_activity": value}]
    yield "day that is not a dict", [None]
    yield "no calendar day at all", []


def bigfoot_night():
    return start_night(new_story())


def claimed_bigfoot_night():
    story = new_story()
    night = start_night(story)
    choose_option(story, night, 0, 100)
    return night


def with_bad_choice(night, **changes):
    night = copy.deepcopy(night)
    night["options"][0].update(changes)
    return night


def with_unknown_item(night):
    night = copy.deepcopy(night)
    night["options"][0]["effects"]["items"] = ["no_such_item"]
    return night


def without(night, key):
    night = copy.deepcopy(night)
    night.pop(key)
    return night


def without_choice_key(night, key):
    night = copy.deepcopy(night)
    night["options"][0].pop(key)
    return night


def malformed_nights():
    """(label, night) pairs the activity screen can't show. Built fresh for every use."""
    night, claimed = bigfoot_night(), claimed_bigfoot_night()
    return [
        ("version 2 and nothing else", {"kind": "bigfoot", "version": 2}),
        ("claimed and nothing else", {"kind": "bigfoot", "claimed": True}),
        ("no intro or options", {"kind": "bigfoot", "version": 2, "night": 1, "scene": "hq_start", "claimed": False}),
        ("claimed without cash or fan change", without(without(claimed, "cash_change"), "fan_change")),
        ("no claimed flag", without(night, "claimed")),
        ("no night number", without(night, "night")),
        ("options not a list", dict(night, options="broken")),
        ("no options", dict(night, options=[])),
        ("choice that is not a dict", dict(night, options=[None])),
        ("choice without effects", with_bad_choice(night, effects=None)),
        ("choice without text", without_choice_key(night, "text")),
        ("choice without id", without_choice_key(night, "id")),
        ("choice with an unknown item", with_unknown_item(night)),
        ("choice with bad requirements", with_bad_choice(night, requires={"attitude": 5})),
        ("intro not text", dict(night, intro=None)),
        ("scene not a name", dict(night, scene=["hq_start"])),
        ("night number not a number", dict(night, night="one")),
        ("claimed flag not true or false", dict(claimed, claimed="yes")),
        ("claimed with an unknown cosmetic", dict(claimed, earned_cosmetics=["no_such_cosmetic"])),
        ("result text not text", dict(claimed, result_text=5)),
        ("claimed without kind", without(claimed, "kind")),
        ("Bigfoot choices marked alien", dict(night, kind="alien")),
    ]


class DrawSkipsBadActivity(unittest.TestCase):
    def test_bad_activity_does_not_crash_draw(self):
        for label, schedule in bad_schedules():
            with self.subTest(label):
                env = make_env(schedule)
                env["draw"]()
                env["draw"]()  # every frame, not just the first
                self.assertEqual(env["career_activity_screen"].drawn, [])
                self.assertEqual(env["career_activity_screen"].buttons, [],
                                 "old buttons must not stay clickable")
                self.assertEqual(env["current_state"], "hub")
                self.assertEqual(env["career_cash"], 100)
                self.assertEqual(env["days_advanced"], [])

    def test_good_activity_is_still_drawn(self):
        night = start_night(new_story())
        env = make_env([{"event_id": "bigfoot_night", "career_activity": night}])
        env["draw"]()
        self.assertEqual(env["career_activity_screen"].drawn, [night])
        self.assertEqual(env["current_state"], "activity")


class RealScreenSkipsMalformedNight(unittest.TestCase):
    """The real CareerActivityScreen, which indexes the keys inside the night."""

    def draw_both_views(self, env):
        env["draw"]()
        env["career_activity_screen"].view = "choices"  # as if "Choose your action" was clicked
        env["draw"]()

    def test_malformed_night_does_not_crash_the_real_screen(self):
        for label, night in malformed_nights():
            with self.subTest(label):
                env = make_env([{"event_id": "bigfoot_night", "career_activity": night}], real_screen=True)
                env["career_activity_screen"].buttons = [(pygame.Rect(0, 0, 9999, 9999), "continue", True)]
                self.draw_both_views(env)
                self.assertEqual(env["current_state"], "hub")
                self.assertEqual(env["career_activity_screen"].buttons, [], "old buttons must not stay clickable")
                self.assertEqual(env["career_cash"], 100)
                self.assertEqual(env["days_advanced"], [])

    def test_valid_nights_still_draw_on_the_real_screen(self):
        finished = new_story()
        finished.update(finished=True, scene="finished", last_result="The end.")
        legacy_claimed = {"kind": "bigfoot", "night": 3, "intro": "Old intro", "options": [{"name": "old"}],
                          "stage": "result", "claimed": True, "result_text": "Old result.",
                          "cash_change": 25, "fan_change": 4}  # a claimed night saved before version 2
        alien = start_night(new_alien_story(), data=ALIEN_STORY)
        cases = [("unclaimed Bigfoot night", bigfoot_night(), "bigfoot_night"),
                 ("claimed Bigfoot night", claimed_bigfoot_night(), "bigfoot_night"),
                 ("finished story", start_night(finished), "bigfoot_night"),
                 ("claimed night from before version 2", legacy_claimed, "bigfoot_night"),
                 ("unclaimed Alien night", alien, "alien_night")]
        for label, night, event_id in cases:
            with self.subTest(label):
                self.assertTrue(night_is_valid(night, data=ALIEN_STORY if night["kind"] == "alien" else None))
                env = make_env([{"event_id": event_id, "career_activity": night}], real_screen=True)
                screen = env["career_activity_screen"]
                env["draw"]()
                self.assertEqual(env["current_state"], "activity")
                self.assertEqual(screen.view, "result" if night["claimed"] else "intro")
                actions = [action for _, action, _ in screen.buttons]
                self.assertIn("continue" if night["claimed"] else "choices", actions)
                if not night["claimed"]:
                    screen.view = "choices"
                    env["draw"]()
                    actions = [action for _, action, _ in screen.buttons]
                    self.assertEqual(actions, [("choice", i) for i in range(len(night["options"]))] + ["intro"])


class HandlerSkipsBadActivity(unittest.TestCase):
    def assert_no_reward(self, env, story_before):
        self.assertEqual(env["career_cash"], 100)
        self.assertEqual(env["fans_awarded"], [])
        self.assertEqual(env["days_advanced"], [])
        self.assertEqual(env["career_bigfoot_story"], story_before)

    def test_bad_activity_does_not_crash_handler(self):
        for label, schedule in bad_schedules():
            for action in (("choice", 0), "continue", "choices"):
                with self.subTest(label, action=action):
                    env = make_env(schedule)
                    story_before = new_story()
                    env["handle_career_activity"](action)
                    self.assert_no_reward(env, story_before)

    def test_activity_without_claimed_key_does_not_crash_handler(self):
        env = make_env([{"event_id": "bigfoot_night", "career_activity": {"kind": "bigfoot"}}])
        story_before = new_story()
        env["handle_career_activity"](("choice", 0))
        env["handle_career_activity"]("continue")
        self.assert_no_reward(env, story_before)

    def test_malformed_night_pays_nothing_and_uses_no_day(self):
        for label, night in malformed_nights():
            for action in (("choice", 0), ("choice", 1), "continue"):
                with self.subTest(label, action=action):
                    env = make_env([{"event_id": "bigfoot_night", "career_activity": night}])
                    story_before = new_story()
                    env["handle_career_activity"](action)
                    self.assert_no_reward(env, story_before)
                    self.assertEqual(env["saves"], [])

    def test_valid_night_still_pays_once(self):
        env = make_env([{"event_id": "bigfoot_night", "career_activity": bigfoot_night()}])
        env["handle_career_activity"](("choice", 0))
        env["handle_career_activity"](("choice", 0))
        self.assertEqual(env["career_bigfoot_story"]["visits"], 1)
        self.assertTrue(env["career_current_schedule"][0]["career_activity"]["claimed"])
        env["handle_career_activity"]("continue")
        self.assertEqual(env["days_advanced"], [{"completed": True}])
        self.assertEqual(env["current_state"], "hub")


class StartReplacesBadActivity(unittest.TestCase):
    def test_non_dict_activity_starts_a_fresh_night(self):
        for value in BAD_ACTIVITIES:
            with self.subTest(career_activity=value):
                env = make_env([{"event_id": "bigfoot_night", "career_activity": value}])
                env["start_career_activity"]()
                activity = env["career_current_schedule"][0]["career_activity"]
                self.assertIsInstance(activity, dict)
                self.assertFalse(activity["claimed"])
                self.assertEqual(activity["kind"], "bigfoot")
                self.assertEqual(env["current_state"], "activity")
                self.assertEqual(env["career_cash"], 100)

    def test_unclaimed_malformed_night_starts_a_fresh_night(self):
        for label, night in malformed_nights():
            if night.get("claimed"):
                continue
            with self.subTest(label):
                env = make_env([{"event_id": "bigfoot_night", "career_activity": night}], real_screen=True)
                env["current_state"] = "hub"
                env["start_career_activity"]()
                activity = env["career_current_schedule"][0]["career_activity"]
                self.assertEqual(activity, start_night(env["career_bigfoot_story"]))
                self.assertEqual(env["current_state"], "activity")
                env["draw"]()  # the real screen shows the fresh night
                self.assertEqual(env["current_state"], "activity")
                self.assertIn("choices", [action for _, action, _ in env["career_activity_screen"].buttons])
                self.assertEqual(env["career_cash"], 100)

    def test_claimed_malformed_night_is_kept_and_never_replayed(self):
        for label, night in malformed_nights():
            if not night.get("claimed"):
                continue
            with self.subTest(label):
                env = make_env([{"event_id": "bigfoot_night", "career_activity": night}], real_screen=True)
                env["current_state"] = "hub"
                before = copy.deepcopy(night)
                story_before = copy.deepcopy(env["career_bigfoot_story"])
                env["start_career_activity"]()
                self.assertIs(env["career_current_schedule"][0]["career_activity"], night, "not replaced")
                self.assertEqual(night, before)
                self.assertEqual(env["current_state"], "hub")
                self.assertEqual(env["saves"], [])
                for action in (("choice", 0), "continue"):
                    env["handle_career_activity"](action)
                env["draw"]()
                self.assertEqual(env["current_state"], "hub")
                self.assertEqual(env["career_cash"], 100)
                self.assertEqual(env["fans_awarded"], [])
                self.assertEqual(env["days_advanced"], [])
                self.assertEqual(env["career_bigfoot_story"], story_before)

    def test_alien_day_replaces_an_unclaimed_malformed_night_and_keeps_a_claimed_one(self):
        env = make_env([{"event_id": "alien_night", "career_activity": {"kind": "alien", "version": 2}}])
        env["start_career_activity"]()
        self.assertEqual(env["career_current_schedule"][0]["career_activity"],
                         start_night(env["career_alien_story"], data=ALIEN_STORY))
        claimed = {"kind": "alien", "version": 2, "claimed": True}
        env = make_env([{"event_id": "alien_night", "career_activity": claimed}])
        env["current_state"] = "hub"
        env["start_career_activity"]()
        self.assertIs(env["career_current_schedule"][0]["career_activity"], claimed)
        self.assertEqual(env["current_state"], "hub")

    def test_valid_nights_are_kept_as_before(self):
        for night in (bigfoot_night(), claimed_bigfoot_night()):
            env = make_env([{"event_id": "bigfoot_night", "career_activity": night}])
            env["start_career_activity"]()
            self.assertIs(env["career_current_schedule"][0]["career_activity"], night)
            self.assertEqual(env["current_state"], "activity")
            self.assertEqual(env["saves"], [1])


def bad_calendar_days():
    """(label, schedule, day) where the calendar has no usable entry for career_day_of_month."""
    night_day = {"event_id": "bigfoot_night"}
    yield "empty schedule", [], 1
    yield "day entry None", [None], 1
    yield "day entry not a dict", ["bigfoot_night"], 1
    yield "day 0", [dict(night_day), dict(night_day)], 0
    yield "day -1", [dict(night_day), dict(night_day)], -1
    yield "day past the end", [dict(night_day)], 2


class CalendarLookupIsGuarded(unittest.TestCase):
    def test_start_career_activity_without_a_calendar_entry_stays_on_the_hub(self):
        for label, schedule, day in bad_calendar_days():
            with self.subTest(label):
                env = make_env(schedule, day)
                env["current_state"] = "hub"
                before = copy.deepcopy(schedule)
                env["start_career_activity"]()
                self.assertEqual(env["current_state"], "hub")
                self.assertEqual(env["career_current_schedule"], before, "no other day gets a night")
                self.assertEqual(env["saves"], [])

    def test_work_day_with_bad_calendar_data_pays_once(self):
        cases = [(label, schedule, day) for label, schedule, day in bad_calendar_days()]
        cases += [(f"career_activity={value!r}", [{"activity_type": "work", "career_activity": value}], 1)
                  for value in BAD_ACTIVITIES]
        for label, schedule, day in cases:
            with self.subTest(label):
                env = make_env(schedule, day)
                self.assertEqual(env["complete_career_work_day"](), JOB_PAY)
                self.assertEqual(env["career_cash"], 100 + JOB_PAY)
                self.assertEqual(env["days_advanced"], [{"completed": True}])

    def test_work_day_with_a_paid_legacy_shift_still_pays_nothing(self):
        env = make_env([{"activity_type": "work", "career_activity": {"kind": "work", "claimed": True}}])
        self.assertEqual(env["complete_career_work_day"](), 0)
        self.assertEqual(env["career_cash"], 100)
        self.assertEqual(env["days_advanced"], [{"completed": True}])

    def test_day_0_does_not_read_the_last_days_legacy_shift(self):
        schedule = [{"activity_type": "work"}, {"activity_type": "work", "career_activity": {"kind": "work", "claimed": True}}]
        env = make_env(schedule, day=0)
        self.assertEqual(env["complete_career_work_day"](), JOB_PAY)


class HubCalendarButtonIsGuarded(unittest.TestCase):
    """The hub's calendar action button (hub_screen.handle_event) with bad calendar data."""

    ACTION_RECT = pygame.Rect(501, 251, 145, 34)

    def click(self, schedule, day):
        env = make_env(schedule, day)
        env.update(
            current_state="hub", pygame=pygame, career_event_entry=None, career_event_has_activity=None,
            career_hub_controls=CareerHubControls(), career_calendar_action_rect=self.ACTION_RECT,
            sounds=types.SimpleNamespace(audio=types.SimpleNamespace(play_sound=lambda name: None)),
            CAREER_ACTIVITY_ROUND="round", CAREER_ACTIVITY_CHALLENGE="challenge",
            CAREER_ACTIVITY_CASUAL_CARDS="casual_cards", CAREER_ACTIVITY_POKER_NIGHT="poker_night",
            CAREER_ACTIVITY_CASINO_NIGHT="casino_night", CAREER_ACTIVITY_NICHE_NIGHT="niche_night",
            CAREER_ACTIVITY_ARCADE_NIGHT="arcade_night", CAREER_ACTIVITY_WORK="work", CAREER_ACTIVITY_EVENT="event",
            restored=[],
        )
        env["restore_event_progress"] = lambda entry, namespace: env["restored"].append(entry) or True
        locate.exec_functions(["handle_event"], env, path=HUB_FILE)
        env["game_mouse_pos"] = self.ACTION_RECT.center
        env["handle_event"](pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=self.ACTION_RECT.center))
        return env

    def assert_stayed_on_hub(self, env):
        self.assertEqual(env["current_state"], "hub")
        self.assertIsNone(env["career_event_entry"])
        self.assertEqual(env["restored"], [])
        self.assertEqual(env["saves"], [])
        self.assertEqual(env["career_cash"], 100)

    def test_event_day_missing_from_the_schedule_list_stays_on_the_hub(self):
        # get_current_career_activity finds day 2 by its day_number, but the list has no index 1.
        env = self.click([{"day_number": 2, "activity_type": "event", "event_id": "bigfoot_night"}], day=2)
        self.assert_stayed_on_hub(env)

    def test_training_day_missing_from_the_schedule_list_stays_on_the_hub(self):
        env = self.click([{"day_number": 2, "activity_type": "casual_cards"}], day=2)
        self.assert_stayed_on_hub(env)

    def test_day_without_an_activity_type_does_nothing(self):
        env = self.click([{"day_number": 1}], day=1)
        self.assert_stayed_on_hub(env)

    def test_non_dict_day_entries_are_skipped(self):
        schedule = [None, {"day_number": 2, "activity_type": "event", "event_id": "bigfoot_night"}]
        env = self.click(schedule, day=2)
        self.assertEqual(env["current_state"], "activity")
        self.assertEqual(schedule[1]["career_activity"], start_night(new_story()))

    def test_valid_event_day_still_opens_the_story_night(self):
        schedule = [{"day_number": 1, "activity_type": "event", "event_id": "bigfoot_night"}]
        env = self.click(schedule, day=1)
        self.assertEqual(env["current_state"], "activity")
        self.assertIs(env["career_event_entry"], schedule[0])
        self.assertEqual(schedule[0]["career_activity"], start_night(new_story()))
        self.assertEqual(env["saves"], [1])

    def test_valid_training_day_still_opens_event_select(self):
        schedule = [{"day_number": 1, "activity_type": "casual_cards"}]
        env = self.click(schedule, day=1)
        self.assertEqual(env["current_state"], "event_select")
        self.assertEqual(env["restored"], [schedule[0]])


class PlayedNightsAreNeverReplayed(unittest.TestCase):
    """Review of the B20 repair: a night that was played keeps its calendar day, even when its
    claimed flag is damaged or it belongs to the other story."""

    def test_played_night_with_a_damaged_claimed_flag_is_not_replayed(self):
        for label, damage in (("claimed None", {"claimed": None}), ("claimed 0", {"claimed": 0}),
                              ("no claimed flag", None)):
            with self.subTest(label):
                story = new_story()
                night = start_night(story)
                self.assertIsNotNone(choose_option(story, night, 0, 100))   # played and paid
                if damage is None:
                    del night["claimed"]
                else:
                    night.update(damage)
                env = make_env([{"event_id": "bigfoot_night", "career_activity": night}], real_screen=True)
                env["career_bigfoot_story"] = story
                env["current_state"] = "hub"
                visits = story["visits"]
                env["start_career_activity"]()
                self.assertIs(env["career_current_schedule"][0]["career_activity"], night, "not replaced")
                self.assertEqual(env["current_state"], "hub")
                env["handle_career_activity"](("choice", 0))
                self.assertEqual(story["visits"], visits)
                self.assertEqual(env["career_cash"], 100)
                self.assertEqual(env["fans_awarded"], [])

    def test_played_night_of_the_other_story_is_kept(self):
        played = claimed_bigfoot_night()
        env = make_env([{"event_id": "alien_night", "career_activity": played}], real_screen=True)
        env["current_state"] = "hub"
        alien_before = copy.deepcopy(env["career_alien_story"])
        env["start_career_activity"]()
        self.assertIs(env["career_current_schedule"][0]["career_activity"], played)
        env["handle_career_activity"](("choice", 0))
        self.assertEqual(env["career_alien_story"], alien_before)
        self.assertEqual(env["career_cash"], 100)

    def test_text_pygame_cannot_render_is_malformed(self):
        night, claimed = bigfoot_night(), claimed_bigfoot_night()
        for label, bad in (("NUL in the intro", dict(night, intro="Bigfoot" + chr(0))),
                           ("lone surrogate in the intro", dict(night, intro="Bigfoot" + chr(0xD800))),
                           ("NUL in a choice", with_bad_choice(night, text="Go" + chr(0))),
                           ("NUL in the result", dict(claimed, result_text="Done" + chr(0)))):
            with self.subTest(label):
                self.assertFalse(night_is_valid(bad))
                env = make_env([{"event_id": "bigfoot_night", "career_activity": bad}], real_screen=True)
                env["draw"]()   # the real screen: no ValueError / UnicodeEncodeError every frame
                self.assertEqual(env["current_state"], "hub")


class NightValidation(unittest.TestCase):
    def test_every_night_the_story_engine_makes_is_valid(self):
        for data in (STORY, ALIEN_STORY):
            for scene_id, scene in data["scenes"].items():
                with self.subTest(story=data.get("kind", "bigfoot"), scene=scene_id):
                    story = new_story(data=data)
                    story.update(scene=scene_id, location=scene["location"])
                    night = start_night(story, data=data)
                    self.assertTrue(night_is_valid(night, data=data))
                    for index in range(len(scene["options"])):
                        played, outing = copy.deepcopy(story), copy.deepcopy(night)
                        if choose_option(played, outing, index, 10 ** 6, data=data) is not None:
                            self.assertTrue(night_is_valid(outing, data=data))
                            self.assertTrue(night_is_valid(start_night(played, data=data), data=data))

    def test_malformed_nights_are_rejected(self):
        for label, night in malformed_nights():
            with self.subTest(label):
                self.assertFalse(night_is_valid(night, data=ALIEN_STORY if night.get("kind") == "alien" else None))
        for value in BAD_ACTIVITIES:
            self.assertFalse(night_is_valid(value))


class RefreshScheduleSkipsBadActivity(unittest.TestCase):
    """refresh_adventure_schedule runs on load with the current day: a non-dict activity there raised."""

    def test_non_dict_current_day_activity_does_not_crash(self):
        finished = new_story()
        finished["finished"] = True
        for value in BAD_ACTIVITIES:
            with self.subTest(career_activity=value):
                schedule = [{"event_id": "bigfoot_night", "career_activity": value}]
                refresh_adventure_schedule(schedule, finished, new_alien_story(), 1)
                self.assertEqual(schedule[0]["event_id"], "alien_night")
                self.assertNotIn("career_activity", schedule[0])

    def test_claimed_current_day_outcome_is_still_kept(self):
        finished = new_story()
        finished["finished"] = True
        night = claimed_bigfoot_night()
        schedule = [{"event_id": "bigfoot_night", "career_activity": night}]
        refresh_adventure_schedule(schedule, finished, new_alien_story(), 1)
        self.assertEqual(schedule[0]["event_id"], "bigfoot_night")
        self.assertIs(schedule[0]["career_activity"], night)


if __name__ == "__main__":
    unittest.main()
