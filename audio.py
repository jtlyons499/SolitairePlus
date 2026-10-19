import random
import pygame


class AudioManager:
    def __init__(self):
        pygame.mixer.init()

        # ----------------------------
        # Volume
        # ----------------------------

        self.instrumental_gain = 0.10
        self.ambient_gain = 0.4
        self.arcade_gain = 0.4

        self.music_volume = 0.5
        self.sfx_volume = 1

        # ----------------------------
        # Sound effects
        # ----------------------------

        self.sounds = {}

        # ----------------------------
        # Music playlists
        # ----------------------------

        self.playlists = {}

        self.music_mode = "instrumental"

        self.current_track = None
        self.current_playlist = []

        # Used so every song plays before
        # reshuffling the playlist
        self.music_queue = []

        # Tracks that SDL_mixer could not decode/load this session.  A bad
        # optional music file must never crash the game or repeatedly poison
        # the playlist each time the end event fires.
        self._failed_music_tracks = set()

        # ----------------------------
        # Temporary arcade-machine music
        # ----------------------------

        self.machine_music_active = False
        self.machine_music_id = None
        self.machine_music_track = None
        self.machine_music_resume_mode = None

        # Non-blocking fade transition. This keeps the game responsive while
        # moving between the normal soundtrack and an individual cabinet loop.
        self._music_transition = None
        self._music_transition_due = 0
        self._music_transition_ms = 220

        # Custom pygame event fired
        # when a song finishes
        self.MUSIC_END_EVENT = pygame.USEREVENT + 1

        pygame.mixer.music.set_endevent(
            self.MUSIC_END_EVENT
        )

    # ==================================================
    # SOUND EFFECTS
    # ==================================================

    def load_sound(self, name, path):
        sound = pygame.mixer.Sound(path)

        sound.set_volume(
            self.sfx_volume
        )

        self.sounds[name] = sound

    def play_sound(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    # ==================================================
    # MUSIC PLAYLISTS
    # ==================================================

    def add_playlist(
        self,
        name,
        tracks,
        startup_track=None
    ):
        self.playlists[name] = {
            "tracks": list(tracks),
            "startup_track": startup_track
        }

    def set_music_mode(self, mode, force=False):
        # If the user explicitly changes the global music setting while a
        # cabinet track is active, leave cabinet mode and honor the new choice.
        if self.machine_music_active or self._transition_targets_machine():
            self.machine_music_active = False
            self.machine_music_id = None
            self.machine_music_track = None
            self.machine_music_resume_mode = None
            self._music_transition = None

        if (
                not force
                and mode == self.music_mode
                and pygame.mixer.music.get_busy()
        ):
            return

        pygame.mixer.music.stop()

        self.music_mode = mode
        self.current_track = None
        self.current_playlist = []
        self.music_queue = []

        # No music
        if mode == "off":
            return

        if mode not in self.playlists:
            return

        playlist_data = self.playlists[mode]

        self.current_playlist = list(
            playlist_data["tracks"]
        )

        startup_track = (
            playlist_data["startup_track"]
        )

        # Play designated starting song
        if startup_track and self.play_music_track(startup_track):
            self.build_music_queue(
                exclude=startup_track
            )

        # Otherwise start with the first valid shuffled track.  This also
        # covers a designated startup file that exists but SDL cannot decode.
        else:
            self.build_music_queue()
            self.play_next_track()

    def build_music_queue(
        self,
        exclude=None
    ):
        self.music_queue = [
            track
            for track in self.current_playlist
            if track != exclude
            and track not in self._failed_music_tracks
        ]

        random.shuffle(
            self.music_queue
        )

    def _effective_music_volume(self):
        volume = self.music_volume

        if self.machine_music_active:
            volume *= self.arcade_gain
        elif self.music_mode == "instrumental":
            volume *= self.instrumental_gain
        elif self.music_mode == "ambient":
            volume *= self.ambient_gain

        return volume

    def play_music_track(self, path, loops=0, fade_ms=0):
        if not path or path in self._failed_music_tracks:
            return False

        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(
                self._effective_music_volume()
            )
            pygame.mixer.music.play(
                loops=loops,
                fade_ms=max(0, int(fade_ms)),
            )
        except (pygame.error, OSError) as exc:
            self._failed_music_tracks.add(path)
            if self.current_track == path:
                self.current_track = None
            print(
                f"Skipping unsupported/unreadable music track: {path} "
                f"({exc})"
            )
            return False

        self.current_track = path
        return True

    def play_next_track(self):
        if self.music_mode == "off":
            return False

        if self.machine_music_active:
            return False

        if not self.current_playlist:
            return False

        # Once every valid track has played, create another shuffled rotation.
        # Failed files are filtered out so a malformed WAV/MP3/OGG cannot
        # crash (or repeatedly stall) the playlist on every music-end event.
        if not self.music_queue:
            self.build_music_queue(
                exclude=self.current_track
            )

        while self.music_queue:
            next_track = self.music_queue.pop(0)
            if self.play_music_track(next_track):
                return True

        return False

    # ==================================================
    # ARCADE MACHINE MUSIC
    # ==================================================

    def _transition_targets_machine(self):
        return (
            isinstance(self._music_transition, tuple)
            and self._music_transition
            and self._music_transition[0] == "machine"
        )

    def _begin_music_transition(self, transition):
        self._music_transition = transition
        self._music_transition_due = (
            pygame.time.get_ticks() + self._music_transition_ms
        )

        if pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(
                self._music_transition_ms
            )

    def sync_machine_music(self, machine_id=None, path=None):
        """Keep cabinet music aligned with the currently active game state.

        Passing a machine id + path requests that cabinet's looping track.
        Passing no machine requests a return to the user's normal music mode.
        Missing files should be filtered by the caller; a falsey path simply
        leaves the normal soundtrack alone.
        """
        wants_machine = bool(machine_id and path)

        if wants_machine and self.music_mode == "off":
            wants_machine = False

        if wants_machine:
            if (
                    self.machine_music_active
                    and self.machine_music_id == machine_id
                    and self.machine_music_track == path
            ):
                return

            if (
                    self._transition_targets_machine()
                    and self._music_transition[1] == machine_id
                    and self._music_transition[2] == path
            ):
                return

            if self.machine_music_resume_mode is None:
                self.machine_music_resume_mode = self.music_mode

            self._begin_music_transition(
                ("machine", machine_id, path)
            )
            return

        # If no cabinet track is requested, only transition back when an
        # override is actually active/pending. Missing optional cabinet files
        # therefore leave the normal soundtrack completely untouched.
        if (
                isinstance(self._music_transition, tuple)
                and self._music_transition
                and self._music_transition[0] == "playlist"
        ):
            return

        if not self.machine_music_active and not self._transition_targets_machine():
            return

        resume_mode = (
            self.machine_music_resume_mode
            if self.machine_music_resume_mode is not None
            else self.music_mode
        )

        self._begin_music_transition(
            ("playlist", resume_mode)
        )

    def _finish_music_transition(self):
        transition = self._music_transition
        self._music_transition = None

        if not transition:
            return

        kind = transition[0]

        if kind == "machine":
            _, machine_id, path = transition

            self.machine_music_active = True
            self.machine_music_id = machine_id
            self.machine_music_track = path
            self.current_track = path

            started = self.play_music_track(
                path,
                loops=-1,
                fade_ms=self._music_transition_ms,
            )
            if not started:
                # Optional machine music must never make a cabinet unusable.
                self.machine_music_active = False
                self.machine_music_id = None
                self.machine_music_track = None

                resume_mode = (
                    self.machine_music_resume_mode
                    if self.machine_music_resume_mode is not None
                    else self.music_mode
                )
                self.machine_music_resume_mode = None
                self.set_music_mode(
                    resume_mode,
                    force=True,
                )

        elif kind == "playlist":
            _, resume_mode = transition

            self.machine_music_active = False
            self.machine_music_id = None
            self.machine_music_track = None
            self.machine_music_resume_mode = None

            self.set_music_mode(
                resume_mode,
                force=True,
            )

    # ==================================================
    # EVENTS
    # ==================================================

    def handle_event(self, event):
        if event.type == self.MUSIC_END_EVENT:
            if self._music_transition is not None:
                return

            if self.machine_music_active:
                return

            self.play_next_track()

    def update(self):
        if (
                self._music_transition is not None
                and pygame.time.get_ticks() >= self._music_transition_due
        ):
            self._finish_music_transition()

        if self._music_transition is not None:
            return

        if self.machine_music_active:
            # Machine tracks loop indefinitely, but recover cleanly if SDL
            # unexpectedly stops the channel.
            if (
                    self.machine_music_track
                    and not pygame.mixer.music.get_busy()
            ):
                if not self.play_music_track(
                        self.machine_music_track,
                        loops=-1,
                ):
                    self.sync_machine_music(None, None)
            return

        if self.music_mode == "off":
            return

        if not self.current_playlist:
            return

        if not pygame.mixer.music.get_busy():
            self.play_next_track()

    # ==================================================
    # VOLUME
    # ==================================================

    def set_music_volume(self, volume):
        self.music_volume = max(
            0.0,
            min(volume, 1.0)
        )

        pygame.mixer.music.set_volume(
            self._effective_music_volume()
        )

    def set_sfx_volume(self, volume):
        self.sfx_volume = max(
            0.0,
            min(volume, 1.0)
        )

        for sound in self.sounds.values():
            sound.set_volume(
                self.sfx_volume
            )
