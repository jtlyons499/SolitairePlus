"""B31: the horse-race music cue never leaves the soundtrack ducked.

Starting a race plays the race cue and ducks the normal music to 22%; ending the cue puts the
music back to the volume it had before. start_horse_race_music() used to take that "before"
volume every time it ran, even when the music was already ducked (a second start while the cue
had been cut off took the ducked volume as the base), so stop_horse_race_music() restored the
ducked value and Options later saved it. The base volume is now taken only when the music is not
ducked, and the horse races screen puts the music back whenever it is left (its leave() hook), so
no exit route (F10 debug menu, a debug launch, the end of the night...) can keep it ducked.

The real screen code and the real loop screen hooks run here with a fake mixer channel and a fake
audio manager; nothing is played.
"""
import importlib
import unittest
from unittest.mock import patch

import pygame

from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.games.casino import horse_races_screen
from solitaireplus.games.casino.horse_races import HorseRaceGame
from solitaireplus.games.casino.horse_races_ui import ACTION_PLACE_BET
from solitaireplus.games.casino.horse_races_ui import ACTION_RETURN
from solitaireplus.games.casino.horse_races_ui import ACTION_START_RACE
from tests.support import locate

ORIGINAL_VOLUME = 0.5
HORSE_RACES_MODULE = "solitaireplus.games.casino.horse_races_screen"


class FakeAudio:
    def __init__(self, music_volume):
        self.music_volume = music_volume

    def set_music_volume(self, volume):
        self.music_volume = max(0.0, min(volume, 1.0))

    def play_sound(self, *args, **kwargs):
        pass


class FakeSounds:
    def __init__(self, audio):
        self.audio = audio


class FakeChannel:
    def __init__(self):
        self.busy = False

    def get_busy(self):
        return self.busy

    def set_volume(self, volume):
        pass

    def play(self, sound, loops=0, fade_ms=0):
        self.busy = True

    def fadeout(self, ms):
        self.busy = False


class Quiet:
    """Accepts every call (XP, fans, night results ...) and returns None."""

    def __getattr__(self, name):
        return lambda *args, **kwargs: None


class HorseRaceMusicDuckingTests(unittest.TestCase):
    def setUp(self):
        self.audio = FakeAudio(ORIGINAL_VOLUME)
        self.channels = []
        self.channel_available = True
        self.action = None
        self.now = 10_000

        def find_channel(force=False):
            if not self.channel_available:
                return None
            channel = FakeChannel()
            self.channels.append(channel)
            return channel

        for target, name, value in (
                (horse_races_screen, "horse_races_game", HorseRaceGame()),
                (horse_races_screen, "get_horse_races_action", lambda pos: self.action),
                (horse_races_screen, "draw_horse_races", lambda *args, **kwargs: None),
                (horse_races_screen, "sounds", FakeSounds(self.audio)),
                (horse_races_screen, "window", Quiet()),
                (horse_races_screen, "game_globals", Quiet()),
                (horse_races_screen, "free_play_select", Quiet()),
                (horse_races_screen, "night", Quiet()),
                (horse_races_screen, "leveling", Quiet()),
                (horse_races_screen, "career_rewards", Quiet()),
                (horse_races_screen, "track_night_cash", lambda *args, **kwargs: None),
                (pygame.mixer, "find_channel", find_channel),
                (pygame.time, "get_ticks", lambda: self.now),
                (state, "horse_race_music_sound", object()),
                (state, "horse_race_music_channel", None),
                (state, "horse_race_previous_music_volume", None),
                (state, "game_mouse_pos", (10, 10)),
                (state, "career_cash", 1000),
                (state, "career_event_has_activity", False),
                (state, "current_game_mode", "career"),
                (state, "current_state", state_names.STATE_CAREER_EVENT_SELECT),
                (state, "horse_races_session_net", 0),
                (state, "horse_races_last_rewarded_races", 0),
                (state, "horse_index", -1),
                (state, "free_play_snapshot", None),
        ):
            # create=True: some state values (game_mouse_pos...) only exist once the loop ran.
            patcher = patch.object(target, name, value, create=True)
            patcher.start()
            self.addCleanup(patcher.stop)

        # The real screen enter/leave hooks of the main loop (solitaireplus/app/loop.py), with
        # only the horse races screen registered.
        self.loop = locate.exec_functions(["run_screen_hooks", "screen_for"], {
            "state": state,
            "importlib": importlib,
            "SCREENS": {state_names.STATE_HORSE_RACES: HORSE_RACES_MODULE},
            "DRAWN_LATE": set(),
            "_LegacyScreen": None,
            "_loaded": {},
        }, path="solitaireplus/app/loop.py")
        self.entered = state.current_state

    # ------------------------------------------------------------------ helpers

    def run_hooks(self):
        self.entered = self.loop["run_screen_hooks"](self.entered)

    def click(self, action):
        self.action = action
        horse_races_screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(10, 10)))
        self.run_hooks()

    def enter_races(self):
        horse_races_screen.start_horse_races_session()
        self.run_hooks()
        self.assertEqual(self.entered, state_names.STATE_HORSE_RACES)

    def start_race(self):
        self.click(ACTION_PLACE_BET)
        self.click(ACTION_START_RACE)
        self.assertEqual(horse_races_screen.horse_races_game.stage, "racing")
        self.assertLess(self.audio.music_volume, ORIGINAL_VOLUME, "the race cue ducks the music")

    def finish_race(self):
        self.now += 60_000          # every horse has crossed the line
        horse_races_screen.draw()
        self.assertEqual(horse_races_screen.horse_races_game.stage, "results")

    def press_f10(self):
        """The loop's F10 debug-menu hotkey, mid-race."""
        state.debug_previous_state = state.current_state
        state.current_state = state_names.STATE_DEBUG_MENU
        self.run_hooks()

    # ------------------------------------------------------------------ tests

    def test_second_start_while_ducked_restores_the_original_volume(self):
        self.assertTrue(horse_races_screen.start_horse_race_music())
        self.channels[-1].busy = False       # the cue was cut off; the music is still ducked
        self.assertTrue(horse_races_screen.start_horse_race_music())
        horse_races_screen.stop_horse_race_music(0)
        self.assertAlmostEqual(self.audio.music_volume, ORIGINAL_VOLUME)

    def test_enter_and_leave_the_races_twice_mid_race(self):
        with patch.object(state, "debug_previous_state", None, create=True):
            for visit in range(2):
                with self.subTest(visit=visit):
                    self.enter_races()
                    self.start_race()
                    self.press_f10()          # leave the screen while the race still runs
                    self.assertAlmostEqual(self.audio.music_volume, ORIGINAL_VOLUME)
                    self.assertIsNone(state.horse_race_music_channel)
        self.assertAlmostEqual(self.audio.music_volume, ORIGINAL_VOLUME)

    def test_enter_and_leave_the_races_twice_after_full_races(self):
        for visit in range(2):
            with self.subTest(visit=visit):
                self.enter_races()
                for race in range(2):
                    if race:
                        self.click(ACTION_START_RACE)        # Next Race (results -> betting)
                    self.start_race()
                    self.finish_race()
                    self.assertAlmostEqual(self.audio.music_volume, ORIGINAL_VOLUME)
                self.click(ACTION_RETURN)
                self.assertEqual(state.current_state, state_names.STATE_CAREER_EVENT_SELECT)
                self.assertAlmostEqual(self.audio.music_volume, ORIGINAL_VOLUME)

    def test_cue_without_a_free_channel_keeps_no_stale_base_volume(self):
        self.channel_available = False
        self.assertFalse(horse_races_screen.start_horse_race_music())
        self.assertAlmostEqual(self.audio.music_volume, ORIGINAL_VOLUME)
        self.assertIsNone(state.horse_race_previous_music_volume)

        self.audio.set_music_volume(0.8)     # the player changes the volume in Options
        self.channel_available = True
        self.assertTrue(horse_races_screen.start_horse_race_music())
        horse_races_screen.stop_horse_race_music(0)
        self.assertAlmostEqual(self.audio.music_volume, 0.8)


if __name__ == "__main__":
    unittest.main()
