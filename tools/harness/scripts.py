"""Script registry and the shared steps every script uses.

A script is a generator function taking ``h`` (a ``sim.Script``). ``yield n`` lets n
frames render; ``h.shot()``/``h.checkpoint()`` record output. Scripts must only use
function and variable names that exist both before and after the restructure
(names stay stable, brief section 4.3), so the same script works on both sides of
a comparison.
"""
from __future__ import annotations

SCENES: dict = {}
JOURNEYS: dict = {}
FIXTURES: dict = {}
KINDS = {"scene": SCENES, "journey": JOURNEYS, "fixture": FIXTURES}

SPLASH_CLICK = (683, 700)          # anywhere: any click leaves the splash screen
PROFILE_SLOT_1 = (450, 225)        # slot 1, left of its Delete button
FIXTURE_NAME = "Harness"


def scene(name):
    def register(function):
        if name in SCENES:
            raise ValueError(f"duplicate scene {name!r}")
        SCENES[name] = function
        return function
    return register


def journey(name):
    def register(function):
        if name in JOURNEYS:
            raise ValueError(f"duplicate journey {name!r}")
        JOURNEYS[name] = function
        return function
    return register


def fixture(name):
    def register(function):
        FIXTURES[name] = function
        return function
    return register


# ------------------------------------------------------------------ shared steps

def leave_splash(h, frames_on_splash=20):
    yield frames_on_splash
    h.click(SPLASH_CLICK)
    yield from h.until_state("PROFILE_SELECT", 30)
    yield 5


def load_fixture_profile(h):
    """From the profile-select screen, open the fixture profile in slot 1 (lands on the main menu)."""
    h.click(PROFILE_SLOT_1)
    yield from h.until_state("MENU", 30)
    yield 5


def to_main_menu(h):
    yield from leave_splash(h)
    yield from load_fixture_profile(h)


def enter_career_hub(h):
    """What clicking Career on the mode-select screen does."""
    h.set("current_game_mode", "career")
    h.call("ensure_career_schedule")
    h.call("ensure_career_leaderboard")
    h.call("ensure_career_news")
    h.set("current_state", h.const("CAREER_HUB"))
    yield 10


def goto(h, state_name, frames=10):
    """Jump straight to a screen by setting current_state (for screens with no setup)."""
    h.set("current_state", h.const(state_name))
    yield frames


# ------------------------------------------------------------------ fixture maker

@fixture("profile_1")
def make_fixture_profile(h):
    """Create the slot-1 test profile the way a player would, then give it career progress."""
    yield from leave_splash(h)
    h.click(PROFILE_SLOT_1)                 # empty slot -> profile creation screen
    yield from h.until_state("PROFILE", 30)
    yield 5
    h.set(profile_name_text=FIXTURE_NAME, profile_country_text="USA", profile_age_text="30",
          profile_hometown_text="Testville", profile_bio_text="Fixture profile for the screen harness.")
    yield 2
    h.click("profile_save_rect")
    yield from h.until_state("MENU", 30)
    yield 5
    h.call("debug_set_player_level", 12)    # every game unlocked (highest unlock level is 10)
    h.set("career_cash", 25000)
    yield from enter_career_hub(h)
    h.call("auto_save_career")
    yield 2


from harness import scenes, journeys  # noqa: E402,F401  (registers the scripts)
