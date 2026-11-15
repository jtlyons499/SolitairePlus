"""B4: the Career hub had an invisible "Career Solitaire" hotspot.

``career_play_rect`` was checked by the hub's click handler but never drawn. It sat over the top
calendar row, and a click there opened Career Solitaire with no pending calendar activity (so a win
paid out without using a day). It was a plain ``if``, so the rest of the hub's button checks also ran
on the same click. These tests run the hub's real click handler (``career/hub_screen.py``
``handle_event``, the old ``loop_event_career_hub``) with the hub's real start-up
button rects and check that the area does nothing now, and that every other hub button still works.
"""
import ast
import os
import types
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from solitaireplus.app import state_names
from solitaireplus.career.hub_controls import CareerHubControls
from tests.support import locate

# Where the hotspot was (the value start-up left in state.career_play_rect): the top calendar row.
OLD_HOTSPOT = pygame.Rect(500, 175, 300, 55)

HUB_RECT_NAMES = (
    "career_jobs_rect", "career_real_estate_rect", "career_leaderboards_rect", "career_news_rect",
    "career_back_rect", "career_fast_skip_yes_rect", "career_fast_skip_no_rect",
)


HUB_SCREEN = "solitaireplus/career/hub_screen.py"


def startup_rects():
    """The hub's fixed button rects as start-up code leaves them (the last module-level assignment wins).

    They are set by start-up code in solitaireplus/legacy.py and the hub screen module."""
    rects = {}
    nodes = []
    for relative in ("solitaireplus/legacy.py", HUB_SCREEN):
        nodes += ast.parse((locate.ROOT / relative).read_text(encoding="utf-8")).body
    for node in nodes:
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1):
            continue
        target = node.targets[0]
        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "state":
            name = target.attr
        elif isinstance(target, ast.Name):
            name = target.id
        else:
            continue
        value = node.value
        # career_play_rect too, while it exists, so the handler sees the hotspot exactly as the game did.
        if (name in HUB_RECT_NAMES + ("career_play_rect",) and isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)
                and value.func.attr == "Rect" and len(value.args) == 4
                and all(isinstance(arg, ast.Constant) for arg in value.args)):
            rects[name] = pygame.Rect(*(arg.value for arg in value.args))
    return rects


class CareerHubHotspotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()
        cls.rects = startup_rects()
        missing = set(HUB_RECT_NAMES) - set(cls.rects)
        if missing:
            raise AssertionError(f"hub rects not found at start-up: {sorted(missing)}")

    def setUp(self):
        self.calls = []
        self.sounds = []
        self.activity = None
        calls = self.calls

        def record(name):
            return lambda *args, **kwargs: calls.append((name, args))

        self.controls = CareerHubControls()
        env = {
            "pygame": pygame,
            "state_names": state_names,
            "sounds": types.SimpleNamespace(audio=types.SimpleNamespace(play_sound=self.sounds.append)),
            "career_hub_controls": self.controls,
            "current_state": state_names.STATE_CAREER_HUB,
            "current_game_mode": "menu",
            "game_mouse_pos": None,
            "pending_career_activity_index": None,
            "pending_career_activity_type": None,
            "pending_career_challenge_id": None,
            "player_name": "Tester",
            # Reset every frame by draw_career_hub; only the current day's cell has these buttons.
            "career_calendar_action_rect": pygame.Rect(0, 0, 0, 0),
            "career_calendar_skip_rect": pygame.Rect(0, 0, 0, 0),
            "CUSTOMIZE_BACKGROUNDS": "backgrounds",
            "CAREER_ACTIVITY_ROUND": "round",
            "CAREER_ACTIVITY_CHALLENGE": "challenge",
            "CAREER_ACTIVITY_CASUAL_CARDS": "casual_cards",
            "CAREER_ACTIVITY_POKER_NIGHT": "poker_night",
            "CAREER_ACTIVITY_CASINO_NIGHT": "casino_night",
            "CAREER_ACTIVITY_NICHE_NIGHT": "niche_night",
            "CAREER_ACTIVITY_ARCADE_NIGHT": "arcade_night",
            "CAREER_ACTIVITY_WORK": "work",
            "CAREER_ACTIVITY_EVENT": "event",
            "get_current_career_activity": lambda: self.activity,
            "get_current_career_activity_index": lambda: 4,
            "game": types.SimpleNamespace(clear_challenge=record("game.clear_challenge"),
                                          set_challenge=record("game.set_challenge"),
                                          new_game=record("game.new_game")),
        }
        for name in ("skip_to_selected_career_day", "time_warp_career", "save_career_from_hub",
                     "begin_career_profile_switch", "start_career_cases", "start_career_cryptid",
                     "restore_event_progress", "reset_career_event_result_log",
                     "reset_career_event_session_totals", "complete_career_work_day",
                     "start_press_interview_event", "start_sign_autographs_event",
                     "start_career_activity", "skip_career_day"):
            env[name] = record(name)
        env.update(self.rects)
        self.env = locate.exec_functions(["handle_event"], env, path=HUB_SCREEN)

    def click(self, pos):
        self.env["game_mouse_pos"] = pos
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)
        self.env["handle_event"](event)

    def assert_nothing_happened(self):
        self.assertEqual(self.env["current_state"], state_names.STATE_CAREER_HUB)
        self.assertEqual(self.env["current_game_mode"], "menu")
        self.assertIsNone(self.env["pending_career_activity_type"])
        self.assertEqual(self.calls, [])
        self.assertEqual(self.sounds, [])

    # -- the hotspot is gone ------------------------------------------------------------------------

    def test_click_on_old_hotspot_does_not_start_career_solitaire(self):
        for pos in (OLD_HOTSPOT.center, OLD_HOTSPOT.topleft,
                    (OLD_HOTSPOT.right - 1, OLD_HOTSPOT.bottom - 1)):
            with self.subTest(pos=pos):
                self.click(pos)
                self.assertNotEqual(self.env["current_state"], state_names.STATE_DIFFICULTY)
                self.assertNotEqual(self.env["current_state"], state_names.STATE_PLAYING)
                self.assert_nothing_happened()

    def test_no_code_defines_or_reads_career_play_rect(self):
        uses = [f"{path.name}:{node.lineno}" for path, tree in locate.trees() for node in ast.walk(tree)
                if (isinstance(node, ast.Attribute) and node.attr == "career_play_rect")
                or (isinstance(node, ast.Name) and node.id == "career_play_rect")]
        self.assertEqual(uses, [])

    def test_one_click_does_only_one_thing(self):
        # Even when another hub button lies over that area, the click only does that button's job.
        self.env["career_calendar_skip_rect"] = OLD_HOTSPOT.copy()
        self.click(OLD_HOTSPOT.center)
        self.assertEqual(self.env["current_state"], state_names.STATE_CAREER_HUB)
        self.assertEqual(self.env["current_game_mode"], "menu")
        self.assertEqual(self.calls, [("skip_career_day", ())])
        self.assertEqual(self.sounds, ["button_click"])

    # -- the other hub buttons still work -----------------------------------------------------------

    def test_fixed_hub_buttons_still_open_their_screens(self):
        expected = {
            "career_jobs_rect": state_names.STATE_CAREER_JOBS,
            "career_real_estate_rect": state_names.STATE_CAREER_REAL_ESTATE,
            "career_leaderboards_rect": state_names.STATE_CAREER_LEADERBOARDS,
            "career_news_rect": state_names.STATE_CAREER_NEWS,
            "career_back_rect": state_names.STATE_MODE_SELECT,
        }
        for rect_name, target in expected.items():
            with self.subTest(button=rect_name):
                self.env["current_state"] = state_names.STATE_CAREER_HUB
                del self.sounds[:]
                self.click(self.rects[rect_name].center)
                self.assertEqual(self.env["current_state"], target)
                self.assertEqual(self.sounds, ["button_click"])
                self.assertEqual(self.env["current_game_mode"], "menu")

    def test_calendar_play_button_still_starts_the_pending_round(self):
        # The current day's "Play" button in the top row (column 1, as draw_career_hub lays it out).
        self.env["career_calendar_action_rect"] = pygame.Rect(501, 251, 145, 34)
        self.activity = {"activity_type": "round"}
        self.click((560, 265))
        self.assertEqual(self.env["current_state"], state_names.STATE_DIFFICULTY)
        self.assertEqual(self.env["current_game_mode"], "career")
        self.assertEqual(self.env["pending_career_activity_type"], "round")
        self.assertEqual(self.env["pending_career_activity_index"], 4)
        self.assertEqual(self.calls, [("game.clear_challenge", ())])
        self.assertEqual(self.sounds, ["button_click"])

    def test_calendar_skip_button_still_skips_the_day(self):
        self.env["career_calendar_skip_rect"] = pygame.Rect(501, 291, 145, 28)
        self.click((560, 300))
        self.assertEqual(self.calls, [("skip_career_day", ())])
        self.assertEqual(self.env["current_state"], state_names.STATE_CAREER_HUB)
        self.assertEqual(self.sounds, ["button_click"])

    def test_toolbar_and_skip_confirmation_still_work(self):
        self.click(self.controls.toolbar_rects["options"].center)
        self.assertEqual(self.env["current_state"], state_names.STATE_OPTIONS)
        self.assertEqual(self.env["options_return_state"], state_names.STATE_CAREER_HUB)

        self.env["current_state"] = state_names.STATE_CAREER_HUB
        self.controls.future_days = {9}
        self.controls.confirm_skip_day = 9
        self.click(self.rects["career_fast_skip_yes_rect"].center)
        self.assertIn(("skip_to_selected_career_day", ()), self.calls)
        self.assertEqual(self.controls.selected_day, 9)
        self.assertIsNone(self.controls.confirm_skip_day)


if __name__ == "__main__":
    unittest.main()
