"""Profile slot screen (moved out of legacy.py)."""
from solitaireplus.games.solitaire.rules import BASE_HEIGHT
from solitaireplus.games.solitaire.rules import BASE_WIDTH
from solitaireplus.profile.saves import ProfileUnavailable
import copy
from solitaireplus.profile.saves import delete_profile
from solitaireplus.profile.achievements import get_definition as get_achievement_definition
from solitaireplus.profile.achievements import iter_rewards as iter_achievement_rewards
from solitaireplus.profile.saves import load_profile
from solitaireplus.app import paths
from solitaireplus.profile.saves import profile_exists
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
save_data = lazy("solitaireplus.profile.save_data")
leveling = lazy("solitaireplus.profile.leveling")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")


def finish_profile_selection():
    destination = state.profile_select_return_state
    state.profile_select_return_state = state_names.STATE_MENU
    state.profile_switch_snapshot = None
    state.profile_name_active = False
    state.profile_country_active = False
    state.profile_age_active = False
    state.profile_hometown_active = False
    state.profile_bio_active = False
    state.gender_dropdown_open = False
    state.favorite_suit_dropdown_open = False
    if destination == state_names.STATE_CAREER_HUB:
        legacy.reset_career_hub_runtime()
        state.current_game_mode = "career"
        legacy.ensure_career_schedule()
        legacy.ensure_career_leaderboard()
        legacy.ensure_career_news()
        legacy.auto_save_career()
    state.profile_return_state = destination
    state.current_state = destination


def cancel_career_profile_switch():
    if state.profile_switch_snapshot is not None:
        slot, was_guest, data = state.profile_switch_snapshot
        state.current_profile_slot = slot
        state.guest_mode = was_guest
        save_data.apply_profile_save_data(copy.deepcopy(data))
        leveling.sync_unlocks_for_current_level()
    state.profile_creation_mode = False
    state.pending_profile_slot = None
    state.profile_message = ""
    finish_profile_selection()

favorite_suit_options = [
    "Clubs",
    "Diamonds",
    "Hearts",
    "Spades",
]

confirm_delete_yes_rect = pygame.Rect(
    530,
    410,
    140,
    50
)

confirm_delete_no_rect = pygame.Rect(
    695,
    410,
    140,
    50
)

# ==================================================
# PROFILE SELECT UI
# ==================================================

profile_slot_rects = [
    pygame.Rect(
        333,
        180 + i * 120,
        700,
        90
    )
    for i in range(3)
]

guest_profile_rect = pygame.Rect(
    483,
    565,
    400,
    70
)

profile_delete_rects = [
    pygame.Rect(
        rect.right - 110,
        rect.y + 20,
        90,
        50
    )
    for rect in profile_slot_rects
]


def sync_achievement_cosmetic_rewards():
    for achievement_id in state.achievement_state.get("unlocked", []):
        definition = get_achievement_definition(achievement_id)
        if not definition:
            continue
        for reward in iter_achievement_rewards(definition):
            legacy.unlock_achievement_cosmetic(reward)

# ==================================================
# PROFILE HELPERS
# ==================================================

def get_profile_slot_display_data(
        slot
):
    try:
        loaded = load_profile(
            slot
        )
    except ProfileUnavailable as problem:
        # Show the slot as unavailable instead of crashing the profile screen.
        return {
            "exists": True,
            "name": problem.short_label,
            "level": None,
        }

    if loaded is None:
        return {
            "exists": False,
            "name": "Empty Slot",
            "level": None,
        }

    identity = loaded.get(
        "identity",
        {}
    )

    progression = loaded.get(
        "progression",
        {}
    )

    return {
        "exists": True,

        "name": identity.get(
            "name",
            "Player"
        ),

        "level": progression.get(
            "level",
            1
        ),
    }

# ==================================================
# PROFILE SELECT
# ==================================================

def draw_profile_select_screen():

    window.game_surface.fill(
        (
            20,
            70,
            45
        )
    )

    profile_select_title = legacy.get_event_ui_asset(
        str(paths.asset("ui/profile/select_profile_title.png")),
        (360, 96)
    )
    if profile_select_title is not None:
        window.game_surface.blit(
            profile_select_title,
            profile_select_title.get_rect(center=(BASE_WIDTH // 2, 78))
        )
    else:
        title = fonts.options_title_font.render(
            "SELECT PROFILE",
            True,
            (255, 255, 255)
        )
        window.game_surface.blit(
            title,
            title.get_rect(center=(BASE_WIDTH // 2, 90))
        )



    if state.profile_select_notice:
        notice = fonts.ui_small_font.render(state.profile_select_notice, True, (255, 210, 160))
        window.game_surface.blit(notice, notice.get_rect(center=(BASE_WIDTH // 2, 150)))

    # ----------------------------
    # Save slots
    # ----------------------------

    for index, rect in enumerate(
        profile_slot_rects
    ):
        slot = index + 1

        data = (
            get_profile_slot_display_data(
                slot
            )
        )

        hovered = rect.collidepoint(
            state.menu_mouse_pos
        )

        fill_color = (
            (80, 145, 100)
            if hovered
            else (50, 110, 75)
        )

        pygame.draw.rect(
            window.game_surface,
            fill_color,
            rect
        )

        pygame.draw.rect(
            window.game_surface,
            (
                255,
                255,
                255
            ),
            rect,
            2
        )

        # ------------------------
        # Slot label
        # ------------------------

        slot_surface = (
            fonts.option_value_font.render(
                f"PROFILE {slot}",
                True,
                (
                    210,
                    210,
                    210
                )
            )
        )

        window.game_surface.blit(
            slot_surface,
            (
                rect.x + 20,
                rect.y + 12
            )
        )

        # ------------------------
        # Name / Empty
        # ------------------------

        name_surface = (
            fonts.option_label_font.render(
                data["name"],
                True,
                (
                    255,
                    255,
                    255
                )
            )
        )

        window.game_surface.blit(
            name_surface,
            (
                rect.x + 20,
                rect.y + 42
            )
        )

        # ------------------------
        # Level
        # ------------------------

        if data["exists"]:
            level_surface = (
                fonts.option_value_font.render(
                    f"Level {data['level']}" if data["level"] is not None else "Can't open",
                    True,
                    (
                        255,
                        215,
                        0
                    )
                )
            )

            level_rect = (
                level_surface.get_rect(
                    right=rect.right - 20,
                    centery=rect.centery
                )
            )

            window.game_surface.blit(
                level_surface,
                level_rect
            )

            if data["exists"]:
                delete_rect = (
                    profile_delete_rects[
                        index
                    ]
                )

                pygame.draw.rect(
                    window.game_surface,
                    (
                        130,
                        45,
                        45
                    ),
                    delete_rect
                )

                pygame.draw.rect(
                    window.game_surface,
                    (
                        255,
                        255,
                        255
                    ),
                    delete_rect,
                    2
                )

                delete_surface = (
                    fonts.option_value_font.render(
                        "Delete",
                        True,
                        (
                            255,
                            255,
                            255
                        )
                    )
                )

                delete_surface_rect = (
                    delete_surface.get_rect(
                        center=delete_rect.center
                    )
                )

                window.game_surface.blit(
                    delete_surface,
                    delete_surface_rect
                )


    # ----------------------------
    # Guest
    # ----------------------------

    guest_hovered = (
        guest_profile_rect.collidepoint(
            state.menu_mouse_pos
        )
    )

    guest_color = (
        (80, 145, 100)
        if guest_hovered
        else (50, 110, 75)
    )

    pygame.draw.rect(
        window.game_surface,
        guest_color,
        guest_profile_rect
    )

    pygame.draw.rect(
        window.game_surface,
        (
            255,
            255,
            255
        ),
        guest_profile_rect,
        2
    )

    guest_surface = (
        fonts.option_label_font.render(
            "Guest",
            True,
            (
                255,
                255,
                255
            )
        )
    )

    guest_rect = (
        guest_surface.get_rect(
            center=guest_profile_rect.center
        )
    )

    window.game_surface.blit(
        guest_surface,
        guest_rect
    )

    if state.profile_select_return_state == state_names.STATE_CAREER_HUB:
        buttons.draw_button(legacy.career_hub_controls.profile_cancel_rect, "Back to Career",
                    font=fonts.option_value_font)

def draw_delete_profile_confirmation():
    overlay = pygame.Surface(
        (
            BASE_WIDTH,
            BASE_HEIGHT
        ),
        pygame.SRCALPHA
    )

    overlay.fill(
        (
            0,
            0,
            0,
            160
        )
    )

    window.game_surface.blit(
        overlay,
        (0, 0)
    )

    panel_rect = pygame.Rect(
        430,
        270,
        505,
        230
    )

    pygame.draw.rect(
        window.game_surface,
        (
            35,
            85,
            60
        ),
        panel_rect
    )

    pygame.draw.rect(
        window.game_surface,
        (
            255,
            255,
            255
        ),
        panel_rect,
        3
    )

    prompt = fonts.option_label_font.render(
        "Delete this profile?",
        True,
        (
            255,
            255,
            255
        )
    )

    prompt_rect = prompt.get_rect(
        center=(
            panel_rect.centerx,
            325
        )
    )

    window.game_surface.blit(
        prompt,
        prompt_rect
    )

    warning = fonts.option_value_font.render(
        "This cannot be undone.",
        True,
        (
            255,
            215,
            0
        )
    )

    warning_rect = warning.get_rect(
        center=(
            panel_rect.centerx,
            365
        )
    )

    window.game_surface.blit(
        warning,
        warning_rect
    )

    buttons.draw_button(
        confirm_delete_yes_rect,
        "Delete"
    )

    buttons.draw_button(
        confirm_delete_no_rect,
        "Cancel"
    )


def handle_event(event):
    """Old main-loop event branch for STATE_PROFILE_SELECT."""

    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
    ):

        if state.confirm_delete_profile:

            if confirm_delete_yes_rect.collidepoint(
                    state.game_mouse_pos
            ):
                sounds.audio.play_sound(
                    "button_click"
                )

                delete_profile(
                    state.profile_delete_slot
                )

                state.confirm_delete_profile = False
                state.profile_delete_slot = None

            elif confirm_delete_no_rect.collidepoint(
                    state.game_mouse_pos
            ):
                sounds.audio.play_sound(
                    "button_click"
                )

                state.confirm_delete_profile = False
                state.profile_delete_slot = None

            return

        if (state.profile_select_return_state == state_names.STATE_CAREER_HUB
                and legacy.career_hub_controls.profile_cancel_rect.collidepoint(state.game_mouse_pos)):
            sounds.audio.play_sound("button_click")
            cancel_career_profile_switch()
            return

        delete_clicked = False

        for state.index, delete_rect in enumerate(
                profile_delete_rects
        ):
            slot = state.index + 1

            if (
                    profile_exists(slot)
                    and not (state.profile_switch_snapshot is not None
                             and state.profile_switch_snapshot[0] == slot)
                    and delete_rect.collidepoint(
                state.game_mouse_pos
                )
            ):
                sounds.audio.play_sound(
                    "button_click"
                )

                state.profile_delete_slot = slot
                state.confirm_delete_profile = True

                delete_clicked = True

                break

        if delete_clicked:
            return

        slot_selected = None

        for state.index, state.rect in enumerate(
                profile_slot_rects
        ):
            if state.rect.collidepoint(
                    state.game_mouse_pos
            ):
                slot_selected = (
                        state.index + 1
                )

                break

        # ----------------------------
        # Existing / new profile
        # ----------------------------

        if slot_selected is not None:
            sounds.audio.play_sound(
                "button_click"
            )

            try:
                state.loaded = load_profile(
                    slot_selected
                )
                state.profile_select_notice = ""
            except ProfileUnavailable as problem:
                # Damaged, or made by a newer version: explain, and never treat it
                # as an empty slot (creating a profile there would overwrite it).
                state.loaded = False
                state.profile_select_notice = str(problem)

            if state.loaded is False:
                pass

            # ----------------------------
            # Empty slot -> create profile
            # ----------------------------

            elif state.loaded is None:
                state.pending_profile_slot = (
                    slot_selected
                )

                state.profile_creation_mode = True
                state.guest_mode = False
                state.current_profile_slot = None

                save_data.apply_fresh_profile()

                state.profile_name_text = ""
                state.profile_gender = "non-binary"
                state.profile_name_active = False
                state.profile_country_active = False
                state.profile_age_active = False
                state.profile_hometown_active = False
                state.profile_bio_active = False
                state.gender_dropdown_open = False
                state.favorite_suit_dropdown_open = False
                state.profile_message = ""

                state.current_state = state_names.STATE_PROFILE



            # ----------------------------
            # Existing slot -> load profile
            # ----------------------------

            else:
                state.current_profile_slot = (
                    slot_selected
                )

                state.guest_mode = False
                state.profile_creation_mode = False
                state.pending_profile_slot = None

                save_data.apply_profile_save_data(
                    state.loaded
                )

                leveling.sync_unlocks_for_current_level()

                state.profile_message = ""

                finish_profile_selection()

        # ----------------------------
        # Guest
        # ----------------------------

        elif guest_profile_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.guest_mode = True

            state.current_profile_slot = None

            save_data.apply_fresh_profile()

            state.profile_message = ""

            finish_profile_selection()


def draw():
    """Old draw-chain branch for STATE_PROFILE_SELECT."""

    draw_profile_select_screen()

    if state.confirm_delete_profile:
        draw_delete_profile_confirmation()
