"""Saving career progress (moved out of legacy.py)."""
import pygame
from solitaireplus.profile import save_data
from solitaireplus.profile.saves import save_profile
from solitaireplus.app import state
from solitaireplus.app.lazy import lazy
legacy = lazy("solitaireplus.legacy")


def auto_save_career():

    if state.guest_mode:
        return

    if state.current_profile_slot is None:
        return

    saved = save_profile(
        save_data.build_profile_save_data(),
        state.current_profile_slot
    )
    if saved is False:
        legacy.career_hub_controls.show_message(
            "Save file locked: progress kept in a recovery save. Close any other game instance.",
            pygame.time.get_ticks(), duration=8000
        )


def save_career_from_hub():
    if state.guest_mode or state.current_profile_slot is None:
        legacy.career_hub_controls.show_message(
            "Guest progress is temporary. Choose a profile to save.",
            pygame.time.get_ticks()
        )
        return True
    try:
        auto_save_career()
    except OSError:
        legacy.career_hub_controls.show_message(
            "Could not save. Check the saves folder and try again.",
            pygame.time.get_ticks()
        )
        return False
    legacy.career_hub_controls.show_message(
        f"Profile saved to slot {state.current_profile_slot}.",
        pygame.time.get_ticks(),
        duration=1500,
        fade_ms=550
    )
    return True
