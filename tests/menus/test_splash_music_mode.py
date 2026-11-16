"""Leaving the splash screen keeps the music mode saved in Options (B14).

The real splash event code (solitaireplus/menus/splash.py handle_event) runs in a fake namespace
(tests/support/locate.py) with the real AppSettings reading a temporary settings file, so the game
is never started.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from solitaireplus.app import app_settings as app_settings_module
from solitaireplus.app import state_names
from tests.support import locate

SPLASH_FILE = "solitaireplus/menus/splash.py"


class FakeAudio:
    """Records music mode changes like AudioManager.set_music_mode would make them."""

    def __init__(self, music_mode):
        self.music_mode = music_mode
        self.mode_calls = []
        self.sounds_played = []

    def set_music_mode(self, mode, force=False):
        self.mode_calls.append(mode)
        self.music_mode = mode

    def play_sound(self, name):
        self.sounds_played.append(name)


class SplashMusicModeTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "app_settings.json"

    def leave_splash(self, saved, music_mode_after_restore, event_type=pygame.KEYDOWN):
        """Write the saved settings (None: first launch, no file), then press a key on the splash."""
        if saved is not None:
            self.path.write_text(json.dumps(saved), encoding="utf-8")
        audio = FakeAudio(music_mode_after_restore)
        env = {
            "pygame": pygame,
            "audio": audio,
            "app_settings": app_settings_module.AppSettings(self.path),
            "STATE_SPLASH": state_names.STATE_SPLASH,
            "STATE_PROFILE_SELECT": state_names.STATE_PROFILE_SELECT,
            "current_state": state_names.STATE_SPLASH,
        }
        locate.exec_functions(["handle_event"], env, path=SPLASH_FILE)
        env["handle_event"](pygame.event.Event(event_type, {}))
        return env, audio

    def test_saved_off_stays_off(self):
        # apply_saved_app_settings() already switched the music off before the splash.
        env, audio = self.leave_splash({"music_mode": "off"}, "off")
        self.assertEqual(audio.music_mode, "off")
        self.assertNotIn("ambient", audio.mode_calls)
        self.assertEqual(env["current_state"], state_names.STATE_PROFILE_SELECT)

    def test_saved_off_stays_off_on_click(self):
        env, audio = self.leave_splash({"music_mode": "off"}, "off", pygame.MOUSEBUTTONDOWN)
        self.assertEqual(audio.music_mode, "off")
        self.assertEqual(env["current_state"], state_names.STATE_PROFILE_SELECT)

    def test_saved_instrumental_starts_instrumental(self):
        # "instrumental" is the AudioManager's built-in mode, so the restore did not start it;
        # leaving the splash starts it (like the first launch starts Ambient there).
        env, audio = self.leave_splash({"music_mode": "instrumental"}, "instrumental")
        self.assertEqual(audio.music_mode, "instrumental")
        self.assertEqual(audio.mode_calls, ["instrumental"])

    def test_saved_ambient_stays_ambient(self):
        env, audio = self.leave_splash({"music_mode": "ambient"}, "ambient")
        self.assertEqual(audio.music_mode, "ambient")

    def test_first_launch_still_starts_ambient(self):
        # No settings file: the old behaviour (Ambient after the splash) is kept.
        env, audio = self.leave_splash(None, "instrumental")
        self.assertEqual(audio.mode_calls, ["ambient"])
        self.assertEqual(audio.music_mode, "ambient")
        self.assertEqual(audio.sounds_played, ["button_click"])
        self.assertEqual(env["current_state"], state_names.STATE_PROFILE_SELECT)

    def test_settings_without_music_mode_start_ambient(self):
        # A settings file saved before music mode was stored (or with a bad value) has no mode.
        env, audio = self.leave_splash({"music_volume": 0.5, "music_mode": "polka"}, "instrumental")
        self.assertEqual(audio.mode_calls, ["ambient"])

    def test_other_events_do_nothing(self):
        env, audio = self.leave_splash({"music_mode": "off"}, "off", pygame.MOUSEMOTION)
        self.assertEqual(audio.mode_calls, [])
        self.assertEqual(audio.sounds_played, [])
        self.assertEqual(env["current_state"], state_names.STATE_SPLASH)


if __name__ == "__main__":
    unittest.main()
