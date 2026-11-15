"""Career story activities screen (Bigfoot / Alien nights) (moved out of legacy.py)."""
from solitaireplus.career.alien_night import STORY as ALIEN_STORY
from solitaireplus.career.activities_ui import CareerActivityScreen
from solitaireplus.career.activities import choose_option, night_is_valid
import pygame
from solitaireplus.career.activities import reconcile_story_cosmetics
from solitaireplus.career.alien_night import refresh_adventure_schedule
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
career_saving = lazy("solitaireplus.career.career_saving")
career_rewards = lazy("solitaireplus.career.career_rewards")
calendar = lazy("solitaireplus.career.calendar")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
panels = lazy("solitaireplus.ui.panels")
hub_screen = lazy("solitaireplus.career.hub_screen")


career_activity_screen = CareerActivityScreen()


def current_career_activity():
    """Today's story night from the calendar, or None when it is missing or malformed (B20).

    Bad save data must not crash the screen or pay a reward. A missing calendar day, a day entry or
    activity that is not a dict, and a night that fails night_is_valid() (such as
    {"kind": "bigfoot", "version": 2}, which has no "night", "claimed", "intro" or "options") all
    count as no activity.
    """
    entry = hub_screen.current_career_schedule_entry()
    activity = entry.get("career_activity") if entry is not None else None
    if not isinstance(activity, dict):
        return None
    alien = activity.get("kind") == "alien"
    return activity if night_is_valid(activity, data=ALIEN_STORY if alien else None) else None


def handle_career_activity(action):
    activity = current_career_activity()
    if activity is None:
        return  # missing or malformed activity: nothing to claim, no reward, the day is not used
    if activity.get("claimed"):
        if action == "continue":
            calendar.advance_career_day(completed=True)
            state.current_state = state_names.STATE_CAREER_HUB
        return
    if isinstance(action, tuple) and action[0] == "choice":
        alien = activity.get("kind") == "alien"
        story = state.career_alien_story if alien else state.career_bigfoot_story
        receipt = choose_option(story, activity, action[1], state.career_cash, data=ALIEN_STORY if alien else None)
        if receipt is not None:
            state.career_cash += receipt["cash"]
            activity["fan_change"] = career_rewards.award_career_fans(receipt["fans"], "Alien Night" if alien else "Bigfoot Night") if receipt["fans"] else 0
            reconcile_story_cosmetics(story, state.unlocked_menu_backgrounds, state.unlocked_felts, state.unlocked_titles, data=ALIEN_STORY if alien else None)
            refresh_adventure_schedule(state.career_current_schedule, state.career_bigfoot_story, state.career_alien_story, state.career_day_of_month)
            career_saving.auto_save_career()


def handle_event(event):
    """Old main-loop event branch for STATE_CAREER_ACTIVITY."""
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        action = career_activity_screen.click(state.game_mouse_pos)
        if action is not None:
            sounds.audio.play_sound("button_click")
            handle_career_activity(action)
    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        career_saving.auto_save_career()
        state.current_state = state_names.STATE_CAREER_HUB


def draw():
    """Old draw-chain branch for STATE_CAREER_ACTIVITY."""
    panels.draw_submenu_background(overlay_alpha=100)
    activity = current_career_activity()
    if activity is None:
        # Missing or malformed activity: skip it. Drop the last frame's buttons so they can't be
        # clicked, and go back to the calendar (the day is not used and nothing is paid).
        career_activity_screen.buttons = []
        state.current_state = state_names.STATE_CAREER_HUB
        return
    career_activity_screen.draw(window.game_surface, activity,
        state.game_mouse_pos, state.career_cash, state.career_alien_story if activity.get("kind") == "alien" else state.career_bigfoot_story)
