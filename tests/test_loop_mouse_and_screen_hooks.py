"""The main loop's mouse position for drawing (B15) and its screen enter/leave hooks (B16).

The real loop (solitaireplus/app/loop.py) and the real Options event code
(solitaireplus/menus/options_screen.py) run here in a fake namespace (tests/support/locate.py), so the game is never started. A fake pygame
plays a scripted list of frames; each frame is where the mouse is plus the events of that frame.
"""
import ast
import contextlib
import io
import os
import types
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from solitaireplus.app import state_names
from tests.support import locate

LOOP_FILE = locate.ROOT / "solitaireplus" / "app" / "loop.py"
OPTIONS_FILE = "solitaireplus/menus/options_screen.py"
OPTIONS_MODULE = "solitaireplus.menus.options_screen"


# ------------------------------------------------------------------ fakes

class FakePygame:
    """pygame as the loop sees it: scripted events and mouse positions, the rest is real pygame."""

    def __init__(self, frames):
        self.frames = list(frames)      # [(mouse position in the window, [events]), ...]
        self.frame = 0
        self.mouse = types.SimpleNamespace(get_pos=lambda: self.frames[self.frame][0])
        self.event = types.SimpleNamespace(get=lambda: list(self.frames[self.frame][1]))
        self.time = types.SimpleNamespace(get_ticks=lambda: 1000 + self.frame * 16)

    def __getattr__(self, name):
        return getattr(pygame, name)

    def quit(self):
        pass


class Anything:
    """Accepts every method call (settings, update checker, audio ...) and returns None."""

    def __getattr__(self, name):
        return lambda *args, **kwargs: None


class FakeAudio(Anything):
    def __init__(self):
        self.music_volumes = []
        self.sfx_volumes = []

    def set_music_volume(self, value):
        self.music_volumes.append(value)

    def set_sfx_volume(self, value):
        self.sfx_volumes.append(value)


def loop_env(frames, screens_module, screens, current_state, to_game=lambda pos: tuple(pos)):
    """A namespace that runs loop.run() for the given frames, then stops.

    screens maps a screen name to its slug (a screen still in legacy: screens_module holds its
    loop_<kind>_<slug> functions) or to a dotted module name (a screen module, like the real
    SCREENS entries without ":": screens_module holds its handle_event/draw/enter/leave).
    screens_module None: the namespace itself, like solitaireplus.legacy for the real legacy screens."""
    fake = FakePygame(frames)
    env = {}
    if screens_module is None:
        screens_module = locate.EnvModule(env)

    def tick(fps):
        fake.frame += 1
        if fake.frame >= len(fake.frames):
            env["running"] = False
        return 16                         # milliseconds, like pygame.time.Clock.tick

    nodes = [node for node in ast.parse(LOOP_FILE.read_text(encoding="utf-8")).body
             if isinstance(node, (ast.FunctionDef, ast.ClassDef))]
    env.update({name: getattr(state_names, name) for name in dir(state_names) if name.startswith("STATE_")})
    env.update(
        pygame=fake,
        importlib=types.SimpleNamespace(import_module=lambda name: screens_module),
        SCREENS={name: slug if "." in slug else f"screens:{slug}" for name, slug in screens.items()},
        DRAWN_LATE=set(),
        _loaded={},
        draw_achievement_popup=lambda *args: None,
        # state
        current_state=current_state,
        game_mouse_pos=None,
        menu_mouse_pos=(0, 0),
        debug_previous_state=None,
        fullscreen_enabled=False,
        arcade_placeholder_music_enabled=False,
        achievement_popup_current=None,
        # legacy
        apply_saved_app_settings=lambda: None,
        app_settings=Anything(),
        update_checker=Anything(),
        current_app_settings_values=lambda: {},
        ARCADE_MACHINE_MUSIC_BY_STATE={},
        dead_mans_hand_game=Anything(),
        loop_post_event_updates=lambda: None,
        update_achievement_popup=lambda: None,
        # sounds / window
        audio=FakeAudio(),
        window_to_game_coords=to_game,
        set_fullscreen_enabled=lambda enabled: None,
        present=lambda: None,
        clock=types.SimpleNamespace(tick=tick),
        FPS=60,
        game_surface=pygame.Surface((1366, 768)),
    )
    locate.exec_nodes(nodes, env, filename=str(LOOP_FILE))
    # F10 on the debug menu goes back through the real close_debug_menu (B59).
    locate.exec_functions(["close_debug_menu"], env, path="solitaireplus/debug/actions.py")
    return env


def run_loop(env):
    with contextlib.redirect_stdout(io.StringIO()):   # the F10 hotkey prints a line
        env["run"]()


def mouse_motion(pos):
    return pygame.event.Event(pygame.MOUSEMOTION, pos=pos, rel=(0, 0), buttons=(0, 0, 0))


def mouse_button(kind, pos):
    return pygame.event.Event(kind, pos=pos, button=1)


def key(kind, key_code):
    return pygame.event.Event(kind, key=key_code, mod=0, unicode="")


def defined(*names, path=OPTIONS_FILE):
    """The names that the screen's file defines (a screen without a hook simply has none)."""
    found = []
    for name in names:
        try:
            locate.function_node(name, path=path)
        except LookupError:
            continue
        found.append(name)
    return found


# ------------------------------------------------------------------ B15

class DrawingUsesTheFramesMousePosition(unittest.TestCase):
    """B15: a key press used to clear game_mouse_pos, so nothing was hovered until the mouse moved."""

    def recording_screen(self, log):
        def handle_event(event):
            log.append(("event", event.type, env_ref["env"]["game_mouse_pos"]))

        def draw():
            env = env_ref["env"]
            log.append(("draw", env["game_mouse_pos"], env["menu_mouse_pos"]))

        def late_update():
            log.append(("late", env_ref["env"]["game_mouse_pos"]))

        env_ref = {}
        module = types.SimpleNamespace(loop_event_menu=handle_event, loop_draw_menu=draw, loop_late_menu=late_update)
        return module, env_ref

    def test_a_key_press_keeps_the_hover_position_for_drawing(self):
        log = []
        module, env_ref = self.recording_screen(log)
        at = (800, 600)                      # window position; the fake mapping halves it
        frames = [
            (at, [mouse_motion(at)]),
            (at, [key(pygame.KEYDOWN, pygame.K_LSHIFT)]),
            (at, [key(pygame.KEYUP, pygame.K_LSHIFT)]),
            (at, []),
        ]
        env = env_ref["env"] = loop_env(frames, module, {"menu": "menu"}, "menu",
                                        to_game=lambda pos: (pos[0] // 2, pos[1] // 2))
        run_loop(env)

        game_pos = (400, 300)
        # Event handlers still get the event's own position (None for a key) ...
        self.assertEqual([entry for entry in log if entry[0] == "event"], [
            ("event", pygame.MOUSEMOTION, game_pos),
            ("event", pygame.KEYDOWN, None),
            ("event", pygame.KEYUP, None),
        ])
        # ... but both draw chains see where the mouse is, every frame.
        self.assertEqual([entry for entry in log if entry[0] != "event"],
                         [("draw", game_pos, game_pos), ("late", game_pos)] * 4)
        self.assertEqual(env["mouse_pos"], game_pos)

    def test_pointer_in_a_letterbox_bar_hovers_nothing(self):
        # In SCALED mode SDL clamps mouse.get_pos() to the picture's edge when the pointer is in a
        # black bar, while events report the real (outside) position; drawing must use the latter.
        log = []
        module, env_ref = self.recording_screen(log)
        frames = [
            ((0, 100), [mouse_motion((-25, 100))]),
            ((0, 100), [key(pygame.KEYDOWN, pygame.K_LSHIFT)]),
            ((10, 100), [mouse_motion((10, 100))]),
        ]
        env = env_ref["env"] = loop_env(frames, module, {"menu": "menu"}, "menu")
        run_loop(env)
        draws = [entry[1] for entry in log if entry[0] == "draw"]
        self.assertEqual(draws, [(-25, 100), (-25, 100), (10, 100)])

    def test_leaving_the_window_clears_the_hover(self):
        log = []
        module, env_ref = self.recording_screen(log)
        frames = [
            ((300, 200), [mouse_motion((300, 200))]),
            ((300, 200), [pygame.event.Event(pygame.WINDOWLEAVE)]),
            ((300, 200), []),
            ((310, 200), [pygame.event.Event(pygame.WINDOWENTER), mouse_motion((310, 200))]),
        ]
        env = env_ref["env"] = loop_env(frames, module, {"menu": "menu"}, "menu")
        run_loop(env)
        draws = [entry[1] for entry in log if entry[0] == "draw"]
        self.assertEqual(draws, [(300, 200), None, None, (310, 200)])

    def test_events_use_their_own_position_and_drawing_the_mouse_position(self):
        log = []
        module, env_ref = self.recording_screen(log)
        frames = [((1000, 700), [mouse_button(pygame.MOUSEBUTTONDOWN, (200, 100))])]
        env = env_ref["env"] = loop_env(frames, module, {"menu": "menu"}, "menu",
                                        to_game=lambda pos: (pos[0] // 2, pos[1] // 2))
        run_loop(env)

        self.assertEqual(log, [
            ("event", pygame.MOUSEBUTTONDOWN, (100, 50)),
            ("draw", (500, 350), (500, 350)),
            ("late", (500, 350)),
        ])
        self.assertEqual(env["mouse_pos"], (500, 350))

    def test_state_declares_the_per_frame_mouse_position(self):
        tree = ast.parse((locate.ROOT / "solitaireplus" / "app" / "state.py").read_text(encoding="utf-8"))
        declared = {target.id for node in tree.body if isinstance(node, ast.Assign)
                    for target in node.targets if isinstance(target, ast.Name)}
        self.assertTrue("mouse_pos" in declared, "solitaireplus/app/state.py does not declare mouse_pos")


# ------------------------------------------------------------------ B16

class ScreenEnterAndLeaveHooks(unittest.TestCase):

    def test_hooks_run_when_the_screen_changes(self):
        log = []

        def switch_on_return(event):
            log.append(("event a", event.key))
            if event.key == pygame.K_RETURN:
                env["current_state"] = "b"

        def post_event_updates():
            if env["pygame"].frame == 4:      # a change outside the event loop (e.g. a finished round)
                env["current_state"] = "a"

        module = types.SimpleNamespace(
            loop_event_a=switch_on_return,
            loop_event_b=lambda event: log.append(("event b", event.key)),
            loop_enter_a=lambda: log.append("enter a"),
            loop_leave_a=lambda: log.append("leave a"),
            loop_enter_b=lambda: log.append("enter b"),
            loop_leave_b=lambda: log.append("leave b"),
            loop_enter_debug_menu=lambda: log.append("enter debug"),
            loop_leave_debug_menu=lambda: log.append("leave debug"),
        )
        frames = [
            ((0, 0), []),
            ((0, 0), [key(pygame.KEYDOWN, pygame.K_RETURN), key(pygame.KEYDOWN, pygame.K_SPACE)]),
            ((0, 0), [key(pygame.KEYDOWN, pygame.K_F10)]),
            ((0, 0), [key(pygame.KEYDOWN, pygame.K_F10)]),
            ((0, 0), []),
            ((0, 0), []),
        ]
        env = loop_env(frames, module,
                       {"a": "a", "b": "b", state_names.STATE_DEBUG_MENU: "debug_menu"}, "a")
        env["loop_post_event_updates"] = post_event_updates
        run_loop(env)

        self.assertEqual(log, [
            "enter a",                                       # frame 1: the first screen
            ("event a", pygame.K_RETURN), "leave a", "enter b", ("event b", pygame.K_SPACE),
            "leave b", "enter debug",                        # F10 opens the debug menu
            "leave debug", "enter b",                        # F10 goes back
            "leave b", "enter a",                            # next frame, after the post-event change
        ])

    def test_options_enter_and_leave_reset_the_slider_drags(self):
        env = {"music_slider_dragging": True, "sfx_slider_dragging": True}
        locate.exec_functions(["enter", "leave"], env, path=OPTIONS_FILE)
        env["enter"]()
        self.assertEqual((env["music_slider_dragging"], env["sfx_slider_dragging"]), (False, False))
        env.update(music_slider_dragging=True, sfx_slider_dragging=True)
        env["leave"]()
        self.assertEqual((env["music_slider_dragging"], env["sfx_slider_dragging"]), (False, False))

    def test_volume_unchanged_after_leaving_options_mid_drag(self):
        """B16: drag the music slider, F10 away, release, F10 back, move: the volume must not follow."""
        slider = pygame.Rect(500, 300, 400, 20)
        frames = [
            ((600, 310), [mouse_button(pygame.MOUSEBUTTONDOWN, (600, 310))]),   # grab the slider at 25 %
            ((600, 310), [key(pygame.KEYDOWN, pygame.K_F10)]),                  # debug menu mid-drag
            ((700, 500), [mouse_button(pygame.MOUSEBUTTONUP, (700, 500))]),     # released there
            ((700, 500), [key(pygame.KEYDOWN, pygame.K_F10)]),                  # back to Options
            ((860, 310), [mouse_motion((860, 310))]),                           # move over the slider
        ]
        # Options is a screen module (its functions are defined in the namespace below); the
        # debug menu is still a legacy screen.
        env = loop_env(frames, None, {state_names.STATE_OPTIONS: OPTIONS_MODULE,
                                      state_names.STATE_DEBUG_MENU: "debug_menu"},
                       state_names.STATE_OPTIONS)
        env.update(
            music_slider_dragging=False,
            sfx_slider_dragging=False,
            music_instrumental_rect=pygame.Rect(0, 0, 10, 10),
            music_ambient_rect=pygame.Rect(20, 0, 10, 10),
            music_off_rect=pygame.Rect(40, 0, 10, 10),
            music_slider_rect=slider,
            sfx_slider_rect=pygame.Rect(500, 400, 400, 20),
        )
        locate.exec_functions(["handle_event", *defined("enter", "leave")], env, path=OPTIONS_FILE)
        run_loop(env)

        self.assertEqual(env["audio"].music_volumes, [0.25])
        self.assertFalse(env["music_slider_dragging"])
        self.assertFalse(env["sfx_slider_dragging"])
        self.assertEqual(env["current_state"], state_names.STATE_OPTIONS)


if __name__ == "__main__":
    unittest.main()
