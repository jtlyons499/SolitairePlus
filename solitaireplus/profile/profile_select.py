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
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
news_screen = lazy("solitaireplus.career.news_screen")
leaderboard_engine = lazy("solitaireplus.career.leaderboard_engine")
career_saving = lazy("solitaireplus.career.career_saving")
calendar = lazy("solitaireplus.career.calendar")
save_data = lazy("solitaireplus.profile.save_data")
leveling = lazy("solitaireplus.profile.leveling")
hub_screen = lazy("solitaireplus.career.hub_screen")
images = lazy("solitaireplus.ui.images")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")


def finish_profile_selection():
    destination = state.profile_select_return_state
    state.profile_select_return_state = state_names.STATE_MENU
    state.profile_switch_snapshot = None
    state.profile_chosen = True
    state.profile_name_active = False
    state.profile_country_active = False
    state.profile_age_active = False
    state.profile_hometown_active = False
    state.profile_bio_active = False
    state.gender_dropdown_open = False
    state.favorite_suit_dropdown_open = False
    if destination == state_names.STATE_CAREER_HUB:
        calendar.reset_career_hub_runtime()
        state.current_game_mode = "career"
        calendar.ensure_career_schedule()
        leaderboard_engine.ensure_career_leaderboard()
        news_screen.ensure_career_news()
        career_saving.auto_save_career()
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


PROFILE_IN_USE_NOTICE = "This profile is in use. Load another profile first to delete it."


def profile_in_use(slot):
    """True if slot holds the loaded profile (or the one Back to Career restores)."""
    if state.profile_switch_snapshot is not None and state.profile_switch_snapshot[0] == slot:
        return True
    # Before the first pick current_profile_slot is only its start-up default; a guest has no slot.
    return state.profile_chosen and not state.guest_mode and state.current_profile_slot == slot

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
            leveling.unlock_achievement_cosmetic(reward)

# ==================================================
# PROFILE HELPERS
# ==================================================

# B10: what each slot shows (name, level), read from its save once and kept, because reading,
# parsing and migrating three saves every frame (and hashing a damaged one) is slow.
# Read again when the screen is entered and after a profile is saved, created or deleted.
_slot_display_cache = {}   # slot -> display data


def forget_slot_display_data():
    """Read the save slots again the next time the profile-select screen is drawn."""
    _slot_display_cache.clear()


def enter():
    """The loop calls this when the profile-select screen opens: show the saves as they are now."""
    forget_slot_display_data()
    # Notices explain the last click on this screen; a new visit starts clean.
    state.profile_select_notice = ""


def get_profile_slot_display_data(
        slot
):
    """What a save slot shows on this screen (kept until forget_slot_display_data())."""
    if slot not in _slot_display_cache:
        _slot_display_cache[slot] = read_profile_slot_display_data(slot)
    return _slot_display_cache[slot]


def read_profile_slot_display_data(
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

    profile_select_title = images.get_event_ui_asset(
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

            # Every existing slot gets a Delete button (drawn below), so keep the
            # level / "Can't open" text to its left instead of underneath it.
            level_rect = (
                level_surface.get_rect(
                    right=profile_delete_rects[index].left - 16,
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
        buttons.draw_button(hub_screen.career_hub_controls.profile_cancel_rect, "Back to Career",
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
                forget_slot_display_data()

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
                and hub_screen.career_hub_controls.profile_cancel_rect.collidepoint(state.game_mouse_pos)):
            sounds.audio.play_sound("button_click")
            cancel_career_profile_switch()
            return

        delete_clicked = False

        for delete_index, delete_rect in enumerate(
                profile_delete_rects
        ):
            slot = delete_index + 1

            # The Delete buttons drawn are the cached slot data's (B10), so the
            # click checks the same data instead of the disk.
            if (
                    get_profile_slot_display_data(slot)["exists"]
                    and delete_rect.collidepoint(
                state.game_mouse_pos
                )
            ):
                sounds.audio.play_sound(
                    "button_click"
                )

                if profile_in_use(slot):
                    # Deleting the loaded save would lose it (or let the next save recreate it).
                    state.profile_select_notice = PROFILE_IN_USE_NOTICE
                else:
                    state.profile_select_notice = ""
                    state.profile_delete_slot = slot
                    state.confirm_delete_profile = True

                delete_clicked = True

                break

        if delete_clicked:
            return

        slot_selected = None

        for slot_index, slot_rect in enumerate(
                profile_slot_rects
        ):
            if slot_rect.collidepoint(
                    state.game_mouse_pos
            ):
                slot_selected = (
                        slot_index + 1
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
