"""B62: the music playlist must advance exactly once per finished track.

AudioManager used to start the next track in two places: update() (when the
mixer went idle) and handle_event() (on the end-of-music event), so every other
track was skipped. These tests drive a real AudioManager with a fake
pygame.mixer.music that behaves like pygame-ce 2.5 / SDL_mixer: a track that
finishes, a stop() of playing music and a completed fade-out each post one
end-of-music event. Frames run in the same order as solitaireplus/app/loop.py:
sync_machine_music(), update(), then that frame's events.
"""
import random
import unittest
from unittest import mock

import pygame

from solitaireplus.app.audio import AudioManager


AMBIENT = [f"music/ambient_{n:02d}.mp3" for n in range(1, 6)]
INSTRUMENTAL = [f"music/instrumental_{n:02d}.mp3" for n in range(1, 4)]
CABINET = "music/arcade/king_pong.ogg"


class FakeMusic:
    """pygame.mixer.music stand-in; end events wait in `posted` until a frame takes them."""

    def __init__(self, bad=()):
        self.bad = set(bad)
        self.loaded = None
        self.playing = None
        self.fading = False
        self.endevent = pygame.NOEVENT
        self.posted = []
        self.started = []

    # --- the pygame.mixer.music API used by AudioManager
    def load(self, path, namehint=""):
        if path in self.bad:
            raise pygame.error(f"Unrecognized audio format: {path}")
        self.loaded = path

    def play(self, loops=0, start=0.0, fade_ms=0):
        # Replacing playing music with load()+play() posts no end event.
        self.playing = self.loaded
        self.fading = False
        self.started.append(self.loaded)

    def stop(self):
        if self.playing is not None:
            self._end()

    def fadeout(self, time_ms):
        if self.playing is not None:
            self.fading = True

    def get_busy(self):
        return self.playing is not None

    def set_volume(self, value):
        pass

    def set_endevent(self, event_type=pygame.NOEVENT):
        self.endevent = event_type

    # --- test controls
    def _end(self):
        self.playing = None
        self.fading = False
        self.posted.append(pygame.event.Event(self.endevent))

    def finish_track(self):
        """The playing track reaches its end (SDL posts the end event)."""
        self._end()

    def complete_fade(self):
        if self.fading:
            self._end()

    def take_events(self):
        events, self.posted = self.posted, []
        return events


class MusicPlaylistTests(unittest.TestCase):

    def make_audio(self, bad=()):
        self.music = FakeMusic(bad=bad)
        self.now = 0
        patches = [
            mock.patch.object(pygame.mixer, "init", lambda *args, **kwargs: None),
            mock.patch.multiple(
                pygame.mixer.music,
                load=self.music.load,
                play=self.music.play,
                stop=self.music.stop,
                fadeout=self.music.fadeout,
                get_busy=self.music.get_busy,
                set_volume=self.music.set_volume,
                set_endevent=self.music.set_endevent,
            ),
            mock.patch.object(pygame.time, "get_ticks", lambda: self.now),
            # Keep the playlist order predictable.
            mock.patch.object(random, "shuffle", lambda seq: None),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

        self.audio = AudioManager()
        self.audio.add_playlist("ambient", AMBIENT)
        self.audio.add_playlist(
            "instrumental", INSTRUMENTAL, startup_track=INSTRUMENTAL[0]
        )
        return self.audio

    def run_frame(self, machine_id=None, machine_track=None, ms=16):
        self.now += ms
        self.audio.sync_machine_music(machine_id, machine_track)
        self.audio.update()
        for event in self.music.take_events():
            self.audio.handle_event(event)

    def started_since(self, count):
        return self.music.started[count:]

    # ------------------------------------------------------------------

    def test_one_end_event_then_update_advances_playlist_by_exactly_one(self):
        audio = self.make_audio()
        audio.set_music_mode("ambient")
        self.run_frame()
        self.assertEqual(self.music.playing, AMBIENT[0])

        started = len(self.music.started)
        queue_before = list(audio.music_queue)

        self.music.finish_track()
        for _ in range(3):
            self.run_frame()

        self.assertEqual(self.started_since(started), [queue_before[0]])
        self.assertEqual(audio.music_queue, queue_before[1:])
        self.assertEqual(self.music.playing, queue_before[0])

    def test_every_track_plays_in_order_across_several_track_ends(self):
        audio = self.make_audio()
        audio.set_music_mode("ambient")
        self.run_frame()

        for _ in range(len(AMBIENT) - 1):
            self.music.finish_track()
            self.run_frame()
            self.run_frame()

        self.assertEqual(self.music.started, AMBIENT)

    def test_mode_change_end_event_does_not_skip_startup_track(self):
        audio = self.make_audio()
        audio.set_music_mode("ambient")
        self.run_frame()

        started = len(self.music.started)
        # stop() of the playing ambient track posts an end event.
        audio.set_music_mode("instrumental")
        for _ in range(3):
            self.run_frame()

        self.assertEqual(self.started_since(started), [INSTRUMENTAL[0]])
        self.assertEqual(self.music.playing, INSTRUMENTAL[0])

    def test_cabinet_fade_out_and_back_starts_playlist_once(self):
        audio = self.make_audio()
        audio.set_music_mode("ambient")
        self.run_frame()

        # Into the cabinet: the fade-out finishes and posts an end event.
        self.run_frame("king_pong", CABINET)
        self.now += 300
        self.music.complete_fade()
        self.run_frame("king_pong", CABINET)
        self.run_frame("king_pong", CABINET)
        self.assertTrue(audio.machine_music_active)
        self.assertEqual(self.music.playing, CABINET)

        # Back to the playlist: the cabinet fade-out also posts an end event.
        started = len(self.music.started)
        self.run_frame()
        self.now += 300
        self.music.complete_fade()
        for _ in range(3):
            self.run_frame()

        self.assertFalse(audio.machine_music_active)
        self.assertEqual(len(self.started_since(started)), 1)
        self.assertIn(self.music.playing, AMBIENT)

    def test_return_from_cabinet_starts_playlist_without_an_end_event(self):
        audio = self.make_audio()
        audio.set_music_mode("ambient")
        self.run_frame()

        self.run_frame("king_pong", CABINET)
        self.now += 300
        self.run_frame("king_pong", CABINET)
        self.assertEqual(self.music.playing, CABINET)

        self.run_frame()
        self.now += 300
        self.music.complete_fade()
        self.music.posted.clear()  # no end event ever arrives
        for _ in range(3):
            self.run_frame()

        self.assertIn(self.music.playing, AMBIENT)

    def test_cabinet_track_restarts_if_the_mixer_stops_it(self):
        audio = self.make_audio()
        audio.set_music_mode("ambient")
        self.run_frame()
        self.run_frame("king_pong", CABINET)
        self.now += 300
        self.run_frame("king_pong", CABINET)
        self.assertEqual(self.music.playing, CABINET)

        self.music.finish_track()
        self.run_frame("king_pong", CABINET)
        self.run_frame("king_pong", CABINET)

        self.assertTrue(audio.machine_music_active)
        self.assertEqual(self.music.playing, CABINET)

    def test_unreadable_tracks_at_end_of_rotation_do_not_silence_music(self):
        # The last two tracks of the rotation cannot be decoded. The next valid
        # track from a fresh rotation must start instead of silence.
        audio = self.make_audio(bad={AMBIENT[3], AMBIENT[4]})
        audio.set_music_mode("ambient")
        self.run_frame()

        for _ in range(3):
            self.music.finish_track()
            self.run_frame()
            self.run_frame()

        self.assertEqual(self.music.started, [AMBIENT[0], AMBIENT[1], AMBIENT[2], AMBIENT[0]])
        self.assertEqual(self.music.playing, AMBIENT[0])

    def test_off_mode_stays_silent(self):
        audio = self.make_audio()
        audio.set_music_mode("ambient")
        self.run_frame()

        audio.set_music_mode("off")
        for _ in range(3):
            self.run_frame()

        self.assertIsNone(self.music.playing)


if __name__ == "__main__":
    unittest.main()
