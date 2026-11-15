"""Child-side simulation: deterministic patches, the state probe and the script driver.

Only imported inside a harness child process (tools/harness/child.py). Installing the
patches changes ``time``, ``random``, ``secrets`` and several ``pygame`` functions for
the whole process, which is exactly what a throwaway child process wants.
"""
from __future__ import annotations

import itertools
import json
import os
import random
import secrets
import sys
import time
import traceback
import types
from pathlib import Path

import pygame

FPS = 60
BASE_SIZE = (1366, 768)
EPOCH = 1_800_000_000.0        # fixed "wall clock" at frame 0 (January 2027)
MONOTONIC_START = 1000.0
MAX_FRAMES = FPS * 180         # a script that runs longer than 3 game-minutes is stuck
RANDOM_SEED = 1234


class ScriptDone(BaseException):
    """Raised from the flip hook when the script has finished (stops the game loop)."""


class ScriptFailed(BaseException):
    """Raised from the flip hook when the script itself failed or ran too long."""


# ------------------------------------------------------------------ virtual clock

class VirtualClock:
    def __init__(self):
        self.frame = 0

    @property
    def seconds(self) -> float:
        return self.frame / FPS

    def ticks(self) -> int:
        return (self.frame * 1000) // FPS


CLOCK = VirtualClock()


class FakeClock:
    """Stands in for pygame.time.Clock: never sleeps, reports exactly the virtual frame time."""

    def __init__(self):
        self._last = CLOCK.ticks()
        self._time = 0

    def tick(self, framerate=0):
        now = CLOCK.ticks()
        self._time, self._last = now - self._last, now
        return self._time

    tick_busy_loop = tick

    def get_time(self):
        return self._time

    def get_rawtime(self):
        return self._time

    def get_fps(self):
        return float(FPS)


# ------------------------------------------------------------------ scripted input

class KeyState:
    """What pygame.key.get_pressed() returns: indexable by any key constant."""

    def __init__(self, held):
        self._held = frozenset(held)

    def __getitem__(self, key):
        return key in self._held

    def __len__(self):
        return 512

    def __iter__(self):
        return (index in self._held for index in range(512))


class Input:
    def __init__(self):
        self.mouse_pos = (BASE_SIZE[0] // 2, BASE_SIZE[1] // 2)
        self.buttons = [False, False, False, False, False]
        self.held_keys: set[int] = set()
        self.mods = 0
        self.rel = [0, 0]
        self.pending: list[tuple[int, pygame.event.Event]] = []   # (deliver at frame, event)

    def queue(self, event, delay=0):
        self.pending.append((CLOCK.frame + 1 + delay, event))

    def take(self, wanted=None):
        ready, keep = [], []
        for due, event in self.pending:
            if due <= CLOCK.frame and (wanted is None or event.type in wanted):
                ready.append(event)
            else:
                keep.append((due, event))
        self.pending = keep
        return ready


INPUT = Input()


def _wanted_types(eventtype, exclude):
    if eventtype is None and exclude is None:
        return None
    every = set(range(0, 0x10000))
    wanted = every
    if eventtype is not None:
        wanted = set(eventtype) if isinstance(eventtype, (list, tuple, set)) else {eventtype}
    if exclude is not None:
        wanted -= set(exclude) if isinstance(exclude, (list, tuple, set)) else {exclude}
    return wanted


# ------------------------------------------------------------------ fake music

class FakeMusic:
    """pygame.mixer.music driven by the virtual clock. Tracks never end on their own."""

    def __init__(self):
        self.path = None
        self.playing = False
        self.paused = False
        self.volume = 1.0
        self.endevent = pygame.NOEVENT
        self.started_frame = 0
        self.fade_end_frame = None

    def _busy(self):
        if self.fade_end_frame is not None and CLOCK.frame >= self.fade_end_frame:
            self.playing = False
            self.fade_end_frame = None
        return self.playing and not self.paused

    def install(self, music):
        def load(filename, namehint=""):
            if isinstance(filename, (str, os.PathLike)) and not os.path.isfile(filename):
                raise pygame.error(f"No file '{filename}' found")
            self.path = filename
            self.playing = False

        def play(loops=0, start=0.0, fade_ms=0):
            if self.path is None:
                raise pygame.error("music not loaded")
            self.playing, self.paused = True, False
            self.started_frame = CLOCK.frame
            self.fade_end_frame = None

        def stop():
            self.playing = False
            self.fade_end_frame = None

        def fadeout(time_ms):
            if self.playing:
                self.fade_end_frame = CLOCK.frame + max(1, (int(time_ms) * FPS + 999) // 1000)

        def pause():
            self.paused = True

        def unpause():
            self.paused = False

        def set_volume(value):
            self.volume = max(0.0, min(1.0, float(value)))

        def get_pos():
            return -1 if not self.playing else (CLOCK.frame - self.started_frame) * 1000 // FPS

        def set_endevent(event_type=pygame.NOEVENT):
            self.endevent = event_type

        def unload():
            self.path = None
            self.playing = False

        def queue(filename, namehint="", loops=0):
            if isinstance(filename, (str, os.PathLike)) and not os.path.isfile(filename):
                raise pygame.error(f"No file '{filename}' found")

        replacements = dict(
            load=load, play=play, stop=stop, fadeout=fadeout, pause=pause, unpause=unpause,
            rewind=lambda: None, set_volume=set_volume, get_volume=lambda: self.volume,
            get_busy=self._busy, get_pos=get_pos, set_pos=lambda pos: None,
            set_endevent=set_endevent, get_endevent=lambda: self.endevent,
            unload=unload, queue=queue,
        )
        for name, function in replacements.items():
            setattr(music, name, function)


# ------------------------------------------------------------------ state probe

class Probe:
    """Reads and writes game state wherever it lives.

    Before the restructure everything is in main.py's namespace (``__main__`` while
    runpy runs it). Afterwards shared state is in ``solitaireplus.app.state`` and
    functions and screen variables are in other ``solitaireplus`` modules. Lookups go:
    state module, then ``__main__``, then every other loaded ``solitaireplus`` module.
    """

    STATE_MODULE = "solitaireplus.app.state"

    def spaces(self):
        found = []
        state = sys.modules.get(self.STATE_MODULE)
        if state is not None:
            found.append(vars(state))
        main = sys.modules.get("__main__")
        if main is not None:
            found.append(vars(main))
        # Names of the old main.py first (legacy, then app modules), then everything else: a moved
        # name never loses to an unrelated same-named object in some other package module.
        def priority(name):
            if name == "solitaireplus.legacy":
                return (0, name)
            if name.startswith("solitaireplus.app."):
                return (1, name)
            return (2, name)
        for name in sorted((n for n in sys.modules if n.startswith("solitaireplus.")), key=priority):
            module = sys.modules[name]
            if module is not state and module is not None:
                found.append(vars(module))
        return found

    def has(self, name):
        return any(name in space for space in self.spaces())

    def get(self, name, *default):
        for space in self.spaces():
            # skip sub-modules and module aliases (e.g. the package attribute
            # solitaireplus.games.dead_mans_hand.game when a script asks for the `game` object)
            if name in space and not isinstance(space[name], types.ModuleType) \
                    and type(space[name]).__name__ != "LazyModule":
                return space[name]
        if default:
            return default[0]
        raise KeyError(f"game has no variable or function named {name!r}")

    def set(self, name, value):
        for space in self.spaces():
            if name in space and not isinstance(space[name], types.ModuleType):
                space[name] = value
                return
        raise KeyError(f"cannot set {name!r}: the game has no variable with that name")

    def call(self, name, *args, **kwargs):
        function = self.get(name)
        if not callable(function):
            raise TypeError(f"{name!r} is not callable")
        return function(*args, **kwargs)


PROBE = Probe()


# ------------------------------------------------------------------ script helper API

class Script:
    """The object a script generator receives. ``yield n`` lets n frames render."""

    def __init__(self, driver):
        self._driver = driver
        self.probe = PROBE

    # state
    def get(self, name, *default):
        return PROBE.get(name, *default)

    def set(self, name=None, value=None, **values):
        if name is not None:
            PROBE.set(name, value)
        for key, item in values.items():
            PROBE.set(key, item)

    def call(self, name, *args, **kwargs):
        return PROBE.call(name, *args, **kwargs)

    def has(self, name):
        return PROBE.has(name)

    @property
    def state(self):
        return PROBE.get("current_state")

    @property
    def frame(self):
        return CLOCK.frame

    def const(self, state_name):
        """Value of a STATE_* constant, e.g. const('MENU')."""
        return PROBE.get("STATE_" + state_name)

    def rect(self, name):
        return PROBE.get(name)

    def center(self, name):
        return tuple(PROBE.get(name).center)

    # input (delivered on the next frame)
    def move(self, pos):
        pos = (int(pos[0]), int(pos[1]))
        old = INPUT.mouse_pos
        INPUT.rel[0] += pos[0] - old[0]
        INPUT.rel[1] += pos[1] - old[1]
        INPUT.mouse_pos = pos
        INPUT.queue(pygame.event.Event(pygame.MOUSEMOTION, pos=pos, rel=(pos[0] - old[0], pos[1] - old[1]),
                                       buttons=tuple(INPUT.buttons[:3]), touch=False, window=None))

    def click(self, pos, button=1, clicks=1):
        if isinstance(pos, str):
            pos = self.center(pos)
        self.move(pos)
        pos = INPUT.mouse_pos
        INPUT.queue(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=button, clicks=clicks, touch=False,
                                       window=None))
        INPUT.queue(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=pos, button=button, touch=False, window=None),
                    delay=1)

    def mouse_down(self, pos, button=1):
        self.move(pos)
        INPUT.buttons[button - 1] = True
        INPUT.queue(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=INPUT.mouse_pos, button=button, clicks=1,
                                       touch=False, window=None))

    def mouse_up(self, pos=None, button=1):
        if pos is not None:
            self.move(pos)
        INPUT.buttons[button - 1] = False
        INPUT.queue(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=INPUT.mouse_pos, button=button,
                                       touch=False, window=None))

    def wheel(self, y):
        INPUT.queue(pygame.event.Event(pygame.MOUSEWHEEL, x=0, y=int(y), flipped=False, precise_x=0.0,
                                       precise_y=float(y), touch=False, window=None))

    def key(self, key, unicode="", mod=0):
        INPUT.queue(pygame.event.Event(pygame.KEYDOWN, key=key, mod=mod, unicode=unicode, scancode=0, window=None))
        INPUT.queue(pygame.event.Event(pygame.KEYUP, key=key, mod=mod, unicode=unicode, scancode=0, window=None),
                    delay=1)

    def hold(self, key):
        INPUT.held_keys.add(key)
        INPUT.queue(pygame.event.Event(pygame.KEYDOWN, key=key, mod=INPUT.mods, unicode="", scancode=0, window=None))

    def release(self, key):
        INPUT.held_keys.discard(key)
        INPUT.queue(pygame.event.Event(pygame.KEYUP, key=key, mod=INPUT.mods, unicode="", scancode=0, window=None))

    def type_text(self, text):
        for character in text:
            INPUT.queue(pygame.event.Event(pygame.KEYDOWN, key=ord(character.lower()), mod=0,
                                           unicode=character, scancode=0, window=None))
            INPUT.queue(pygame.event.Event(pygame.TEXTINPUT, text=character, window=None))

    def post(self, event_type, **attributes):
        INPUT.queue(pygame.event.Event(event_type, **attributes))

    # output
    def shot(self, sub=None):
        return self._driver.shot(sub)

    def checkpoint(self, label, *extra_names, screenshot=True):
        return self._driver.checkpoint(label, extra_names, screenshot)

    def expect_quit(self):
        """The script ends by quitting the game; a normal exit of the main loop is then a success."""
        self._driver.expect_quit = True

    def note(self, text):
        self._driver.result["notes"].append(f"frame {CLOCK.frame}: {text}")

    # waiting
    def until(self, condition, limit=600, what="condition"):
        """yield from h.until(lambda: ..., limit): wait up to `limit` frames for it to be true."""
        for _ in range(limit):
            if condition():
                return
            yield 1
        raise AssertionError(f"timed out after {limit} frames waiting for {what} (state {self.state!r})")

    def until_state(self, state_name, limit=600):
        target = self.const(state_name)
        yield from self.until(lambda: self.state == target, limit, f"state {target!r}")


DEFAULT_CHECKPOINT_VALUES = (
    "current_state", "career_cash", "player_xp", "player_level", "career_rating",
    "career_day", "career_day_of_month", "career_month", "career_year", "career_fans",
)


class Driver:
    """Runs one script generator, one step per frame, from inside pygame.display.flip()."""

    def __init__(self, name, script_function, out_dir: Path):
        self.name = name
        self.out_dir = out_dir
        self.script_function = script_function
        self.generator = None
        self.wait = 0
        self.done = False
        self.expect_quit = False
        self.real_flip = None
        self.result = {"name": name, "ok": False, "error": None, "frames": 0,
                       "shots": [], "checkpoints": [], "notes": []}

    def shot(self, sub=None):
        filename = self.name if not sub else f"{self.name}__{sub}"
        path = self.out_dir / f"{filename}.png"
        pygame.image.save(pygame.display.get_surface(), str(path))
        self.result["shots"].append(path.name)
        return path.name

    def checkpoint(self, label, extra_names=(), screenshot=True):
        values = {}
        for name in (*DEFAULT_CHECKPOINT_VALUES, *extra_names):
            value = PROBE.get(name, "<missing>")
            values[name] = _plain(value)
        entry = {"label": label, "frame": CLOCK.frame, "values": values}
        if screenshot:
            entry["shot"] = self.shot(f"cp_{len(self.result['checkpoints']):02d}_{label}")
        self.result["checkpoints"].append(entry)
        return entry

    def on_flip(self, *args):
        try:
            if self.generator is None:
                self.generator = self.script_function(Script(self))
            if not self.done:
                if self.wait > 0:
                    self.wait -= 1
                else:
                    try:
                        frames = next(self.generator)
                        self.wait = max(0, int(frames if frames is not None else 1) - 1)
                    except StopIteration:
                        self.done = True
        except (ScriptDone, ScriptFailed):
            raise
        except BaseException:
            self.result["error"] = "script error:\n" + traceback.format_exc()
            raise ScriptFailed()
        self.real_flip()
        CLOCK.frame += 1
        self.result["frames"] = CLOCK.frame
        if self.done:
            raise ScriptDone()
        if CLOCK.frame > MAX_FRAMES:
            self.result["error"] = f"script still running after {MAX_FRAMES} frames"
            raise ScriptFailed()


def _plain(value):
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        if isinstance(value, (set, frozenset)):
            return sorted(map(str, value))
        return repr(value)


# ------------------------------------------------------------------ installing the patches

def install(driver: Driver) -> None:
    # Randomness: everything starts from fixed seeds.
    seeds = itertools.count(1)
    original_seed = random.Random.seed

    def seed(self, a=None, version=2):
        if a is None:
            a = 0x5EED0000 + next(seeds)
        return original_seed(self, a, version)

    random.Random.seed = seed
    random.seed(RANDOM_SEED)
    random.SystemRandom = lambda *args, **kwargs: random.Random(0x5157E000 + next(seeds))
    secret_rng = random.Random(0x5EC2E7)
    secrets.randbits = secret_rng.getrandbits
    secrets.randbelow = lambda n: secret_rng.randrange(n)
    secrets.choice = secret_rng.choice
    secrets.token_bytes = lambda n=32: bytes(secret_rng.getrandbits(8) for _ in range(n or 32))
    secrets.token_hex = lambda n=32: secrets.token_bytes(n).hex()

    # Time: one frame = exactly 1/60 s, whatever the machine does.
    time.time = lambda: EPOCH + CLOCK.seconds
    time.time_ns = lambda: int((EPOCH + CLOCK.seconds) * 1e9)
    time.monotonic = lambda: MONOTONIC_START + CLOCK.seconds
    time.monotonic_ns = lambda: int((MONOTONIC_START + CLOCK.seconds) * 1e9)
    time.perf_counter = time.monotonic
    time.perf_counter_ns = time.monotonic_ns
    time.sleep = lambda seconds: None
    pygame.time.get_ticks = CLOCK.ticks
    pygame.time.Clock = FakeClock
    pygame.time.wait = lambda milliseconds: 0
    pygame.time.delay = lambda milliseconds: 0
    pygame.time.set_timer = lambda *args, **kwargs: None

    # Input: scripted events, virtual mouse and keyboard.
    real_get = pygame.event.get

    def drain_real():
        try:
            real_get()
        except pygame.error:
            pass

    def event_get(eventtype=None, pump=True, exclude=None):
        drain_real()
        return INPUT.take(_wanted_types(eventtype, exclude))

    def event_poll():
        drain_real()
        ready = INPUT.take()
        if not ready:
            return pygame.event.Event(pygame.NOEVENT)
        first, rest = ready[0], ready[1:]
        INPUT.pending[0:0] = [(CLOCK.frame, event) for event in rest]
        return first

    def event_peek(eventtype=None, pump=True):
        wanted = _wanted_types(eventtype, None)
        return any(due <= CLOCK.frame and (wanted is None or event.type in wanted)
                   for due, event in INPUT.pending)

    def event_post(event):
        INPUT.pending.append((CLOCK.frame, event))
        return True

    def event_clear(eventtype=None, pump=True):
        drain_real()
        INPUT.take(_wanted_types(eventtype, None))

    pygame.event.get = event_get
    pygame.event.poll = event_poll
    pygame.event.wait = lambda timeout=0: event_poll()
    pygame.event.peek = event_peek
    pygame.event.post = event_post
    pygame.event.clear = event_clear
    pygame.event.pump = drain_real

    def get_rel():
        rel = tuple(INPUT.rel)
        INPUT.rel[:] = [0, 0]
        return rel

    def set_pos(*pos):
        pos = pos[0] if len(pos) == 1 else pos
        INPUT.mouse_pos = (int(pos[0]), int(pos[1]))

    pygame.mouse.get_pos = lambda: INPUT.mouse_pos
    pygame.mouse.get_pressed = lambda num_buttons=3: tuple(INPUT.buttons[:num_buttons])
    pygame.mouse.get_rel = get_rel
    pygame.mouse.set_pos = set_pos
    pygame.mouse.get_focused = lambda: True
    pygame.key.get_pressed = lambda: KeyState(INPUT.held_keys)
    pygame.key.get_mods = lambda: INPUT.mods
    pygame.key.get_focused = lambda: True

    # Display: always a plain 1366x768 window; flip runs the script.
    real_set_mode = pygame.display.set_mode

    def set_mode(size=(0, 0), flags=0, depth=0, display=0, vsync=0):
        return real_set_mode(BASE_SIZE, 0)

    pygame.display.set_mode = set_mode
    pygame.display.toggle_fullscreen = lambda: 1

    class NoWindowObject:
        """The game may resize/centre its window through pygame.Window (W1); the harness window
        must stay a plain 1366x768 surface, so the window object is unavailable here."""

        @staticmethod
        def from_display_module(*args, **kwargs):
            raise pygame.error("pygame.Window is disabled in the screen harness")

    pygame.Window = NoWindowObject
    driver.real_flip = pygame.display.flip
    pygame.display.flip = driver.on_flip
    pygame.display.update = driver.on_flip

    # Music follows the virtual clock (the dummy audio device plays in real time).
    FakeMusic().install(pygame.mixer.music)
