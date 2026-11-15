"""Profile editing / creation screen (moved out of legacy.py)."""
from solitaireplus.games.solitaire.rules import BASE_WIDTH
import pygame
from solitaireplus.profile.saves import save_profile
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
save_data = lazy("solitaireplus.profile.save_data")
profile_select = lazy("solitaireplus.profile.profile_select")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
ui_text = lazy("solitaireplus.ui.text")
sounds = lazy("solitaireplus.app.sounds")
panels = lazy("solitaireplus.ui.panels")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")
assets = lazy("solitaireplus.app.assets")


gender_options = [
    "male",
    "female",
    "non-binary",
]

# ==================================================
# PROFILE UI
# ==================================================

profile_name_rect = pygame.Rect(
    410,
    180,
    340,
    46
)

profile_country_rect = pygame.Rect(
    775,
    180,
    145,
    46
)

profile_age_rect = pygame.Rect(
    945,
    180,
    145,
    46
)

profile_gender_rect = pygame.Rect(
    410,
    270,
    300,
    46
)

profile_favorite_suit_rect = pygame.Rect(
    735,
    270,
    355,
    46
)

profile_gender_option_rects = [
    pygame.Rect(
        410,
        316 + i * 42,
        300,
        42
    )
    for i in range(3)
]

profile_favorite_suit_option_rects = [
    pygame.Rect(
        735,
        316 + i * 42,
        355,
        42
    )
    for i in range(4)
]

profile_hometown_rect = pygame.Rect(
    410,
    360,
    680,
    46
)

profile_bio_rect = pygame.Rect(
    410,
    455,
    680,
    126
)

profile_save_rect = pygame.Rect(
    410,
    650,
    200,
    48
)

profile_back_rect = pygame.Rect(
    890,
    650,
    200,
    48
)

avatar_selector_left_x = 1190
avatar_selector_right_x = 1275
avatar_selector_start_y = 195
avatar_selector_gap = 58

avatar_selector_left_rects = [
    pygame.Rect(
        avatar_selector_left_x,
        avatar_selector_start_y + i * avatar_selector_gap,
        45,
        40
    )
    for i in range(5)
]

avatar_selector_right_rects = [
    pygame.Rect(
        avatar_selector_right_x,
        avatar_selector_start_y + i * avatar_selector_gap,
        45,
        40
    )
    for i in range(5)
]

def cycle_option(
        current_value,
        options,
        direction
):
    current_index = options.index(
        current_value
    )

    new_index = (
        current_index + direction
    ) % len(options)

    return options[
        new_index
    ]

profile_avatar_frame_rect = pygame.Rect(
    65,
    170,
    300,
    360
)

def draw_profile_screen():
    panels.draw_submenu_background(
        overlay_alpha=125
    )

    profile_title_text = (
        "CREATE PROFILE"
        if state.profile_creation_mode
        else "PROFILE"
    )

    title = ui_text.get_font(
        "cambria",
        44,
        bold=True,
        sysfont=True
    ).render(
        profile_title_text,
        True,
        (255, 255, 255)
    )
    window.game_surface.blit(
        title,
        title.get_rect(center=(BASE_WIDTH // 2, 58))
    )

    if state.guest_mode:
        slot_text = "Guest"
    elif state.current_profile_slot is not None:
        slot_text = f"Profile Slot {state.current_profile_slot}"
    else:
        slot_text = "New Profile"

    slot_surface = fonts.option_value_font.render(
        slot_text,
        True,
        (255, 220, 110)
    )
    window.game_surface.blit(
        slot_surface,
        slot_surface.get_rect(center=(BASE_WIDTH // 2, 105))
    )

    # ==================================================
    # Avatar preview
    # ==================================================

    pygame.draw.rect(
        window.game_surface,
        (24, 58, 43),
        profile_avatar_frame_rect,
        border_radius=12
    )
    pygame.draw.rect(
        window.game_surface,
        (230, 236, 232),
        profile_avatar_frame_rect,
        3,
        border_radius=12
    )

    avatar = legacy.get_profile_avatar()
    max_avatar_rect = profile_avatar_frame_rect.inflate(-18, -18)
    src_w, src_h = avatar.get_size()
    avatar_scale = min(
        max_avatar_rect.width / max(1, src_w),
        max_avatar_rect.height / max(1, src_h)
    )
    avatar_size = (
        max(1, int(src_w * avatar_scale)),
        max(1, int(src_h * avatar_scale))
    )
    avatar_preview = pygame.transform.smoothscale(
        avatar,
        avatar_size
    )
    window.game_surface.blit(
        avatar_preview,
        avatar_preview.get_rect(center=profile_avatar_frame_rect.center)
    )

    level_text = f"Level {state.player_level}"
    xp_text = f"XP {state.player_xp:,}"
    if state.player_xp_to_next is not None:
        xp_text += f" / {state.player_xp_to_next:,}"

    for index, text in enumerate((level_text, xp_text)):
        surface = fonts.option_value_font.render(
            text,
            True,
            (240, 240, 240)
        )
        window.game_surface.blit(
            surface,
            surface.get_rect(center=(profile_avatar_frame_rect.centerx, 555 + index * 31))
        )

    # ==================================================
    # Field helpers
    # ==================================================

    def draw_field(label, rect, value, active=False, placeholder=""):
        label_surface = fonts.difficulty_detail_font.render(
            label,
            True,
            (236, 236, 236)
        )
        window.game_surface.blit(
            label_surface,
            (rect.x, rect.y - 27)
        )

        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((18, 52, 38, 220))
        window.game_surface.blit(panel, rect.topleft)

        pygame.draw.rect(
            window.game_surface,
            (255, 215, 85) if active else (225, 232, 228),
            rect,
            3 if active else 2,
            border_radius=6
        )

        shown = value if value else placeholder
        color = (255, 255, 255) if value else (155, 172, 165)
        text_surface = ui_text.render_text_fit(
            shown,
            fonts.option_value_font,
            rect.width - 26,
            color,
            minimum_size=15
        )
        window.game_surface.blit(
            text_surface,
            (rect.x + 13, rect.centery - text_surface.get_height() // 2)
        )

    def draw_dropdown_field(label, rect, value, open_state, placeholder):
        label_surface = fonts.difficulty_detail_font.render(
            label,
            True,
            (236, 236, 236)
        )
        window.game_surface.blit(label_surface, (rect.x, rect.y - 27))

        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((18, 52, 38, 220))
        window.game_surface.blit(panel, rect.topleft)
        pygame.draw.rect(
            window.game_surface,
            (255, 215, 85) if open_state else (225, 232, 228),
            rect,
            3 if open_state else 2,
            border_radius=6
        )

        shown = value if value else placeholder
        color = (255, 255, 255) if value else (155, 172, 165)
        text_surface = fonts.option_value_font.render(shown, True, color)
        window.game_surface.blit(
            text_surface,
            (rect.x + 13, rect.centery - text_surface.get_height() // 2)
        )
        arrow = fonts.difficulty_detail_font.render("v", True, (230, 230, 230))
        window.game_surface.blit(
            arrow,
            arrow.get_rect(center=(rect.right - 22, rect.centery))
        )

    draw_field(
        "Name",
        profile_name_rect,
        state.profile_name_text,
        state.profile_name_active,
        "Player name"
    )
    draw_field(
        "Country",
        profile_country_rect,
        state.profile_country_text,
        state.profile_country_active,
        "e.g. USA"
    )
    country_hint = fonts.leaderboard_tiny_font.render(
        "3-letter code",
        True,
        (185, 195, 190)
    )
    window.game_surface.blit(
        country_hint,
        (profile_country_rect.x, profile_country_rect.bottom + 3)
    )

    draw_field(
        "Age",
        profile_age_rect,
        state.profile_age_text,
        state.profile_age_active,
        "Age"
    )

    draw_dropdown_field(
        "Gender",
        profile_gender_rect,
        state.profile_gender.title(),
        state.gender_dropdown_open,
        "Choose"
    )
    draw_dropdown_field(
        "Favorite Suit",
        profile_favorite_suit_rect,
        state.profile_favorite_suit,
        state.favorite_suit_dropdown_open,
        "Choose a suit"
    )

    draw_field(
        "Hometown",
        profile_hometown_rect,
        state.profile_hometown_text,
        state.profile_hometown_active,
        "City, region / country"
    )

    bio_label = fonts.difficulty_detail_font.render(
        "Short Bio",
        True,
        (236, 236, 236)
    )
    window.game_surface.blit(
        bio_label,
        (profile_bio_rect.x, profile_bio_rect.y - 27)
    )
    bio_panel = pygame.Surface(profile_bio_rect.size, pygame.SRCALPHA)
    bio_panel.fill((18, 52, 38, 220))
    window.game_surface.blit(bio_panel, profile_bio_rect.topleft)
    pygame.draw.rect(
        window.game_surface,
        (255, 215, 85) if state.profile_bio_active else (225, 232, 228),
        profile_bio_rect,
        3 if state.profile_bio_active else 2,
        border_radius=6
    )

    bio_text = state.profile_bio_text if state.profile_bio_text else "A short leaderboard bio..."
    bio_color = (255, 255, 255) if state.profile_bio_text else (155, 172, 165)
    ui_text.draw_wrapped_text_limited(
        bio_text,
        fonts.difficulty_detail_font,
        bio_color,
        profile_bio_rect.inflate(-22, -18),
        max_lines=4,
        line_spacing=3
    )
    counter_surface = fonts.leaderboard_tiny_font.render(
        f"{len(state.profile_bio_text)}/180",
        True,
        (170, 185, 178)
    )
    window.game_surface.blit(
        counter_surface,
        counter_surface.get_rect(bottomright=(profile_bio_rect.right - 8, profile_bio_rect.bottom - 5))
    )

    # ==================================================
    # Avatar customization panel
    # ==================================================

    avatar_panel = pygame.Rect(1110, 155, 220, 350)
    avatar_panel_surface = pygame.Surface(avatar_panel.size, pygame.SRCALPHA)
    avatar_panel_surface.fill((16, 40, 31, 200))
    window.game_surface.blit(avatar_panel_surface, avatar_panel.topleft)
    pygame.draw.rect(
        window.game_surface,
        (210, 220, 214),
        avatar_panel,
        2,
        border_radius=10
    )

    customize_title = fonts.difficulty_detail_font.render(
        "AVATAR",
        True,
        (255, 220, 110)
    )
    window.game_surface.blit(
        customize_title,
        customize_title.get_rect(center=(avatar_panel.centerx, 177))
    )

    avatar_selector_rows = [
        ("Base", state.selected_avatar_base, assets.avatar_base_options),
        ("Eyes", state.selected_avatar_eyes, assets.avatar_eye_options),
        ("Hair", state.selected_avatar_hair, assets.avatar_hair_options),
        ("Glasses", state.selected_avatar_glasses, assets.avatar_glasses_options),
        ("Top", state.selected_avatar_top, assets.avatar_top_options),
    ]

    for index, (label_text, current_value, options) in enumerate(avatar_selector_rows):
        y = avatar_selector_start_y + index * avatar_selector_gap
        label_surface = fonts.difficulty_detail_font.render(
            label_text,
            True,
            (235, 235, 235)
        )
        window.game_surface.blit(
            label_surface,
            (1118, y + 8)
        )

        buttons.draw_button(avatar_selector_left_rects[index], "<")
        buttons.draw_button(avatar_selector_right_rects[index], ">")

        if current_value is None:
            display_text = "None"
        else:
            current_index = options.index(current_value)
            display_text = f"{current_index + 1}/{len(options)}"

        value_surface = fonts.difficulty_detail_font.render(
            display_text,
            True,
            (255, 220, 110)
        )
        window.game_surface.blit(
            value_surface,
            value_surface.get_rect(center=(1250, y + 20))
        )

    # ==================================================
    # Dropdown overlays
    # ==================================================

    if state.gender_dropdown_open:
        for index, gender in enumerate(gender_options):
            rect = profile_gender_option_rects[index]
            pygame.draw.rect(window.game_surface, (25, 72, 50), rect)
            pygame.draw.rect(window.game_surface, (235, 235, 235), rect, 1)
            label = fonts.option_value_font.render(
                gender.title(),
                True,
                (255, 255, 255)
            )
            window.game_surface.blit(
                label,
                (rect.x + 13, rect.centery - label.get_height() // 2)
            )

    if state.favorite_suit_dropdown_open:
        for index, suit in enumerate(profile_select.favorite_suit_options):
            rect = profile_favorite_suit_option_rects[index]
            pygame.draw.rect(window.game_surface, (25, 72, 50), rect)
            pygame.draw.rect(window.game_surface, (235, 235, 235), rect, 1)
            label = fonts.option_value_font.render(
                suit,
                True,
                (255, 255, 255)
            )
            window.game_surface.blit(
                label,
                (rect.x + 13, rect.centery - label.get_height() // 2)
            )

    # ==================================================
    # Buttons / status
    # ==================================================

    save_button_text = "Create Profile" if state.profile_creation_mode else "Save"
    buttons.draw_menu_button(
        profile_save_rect,
        save_button_text,
        state.game_mouse_pos,
        font=fonts.difficulty_detail_font
    )

    if not state.profile_creation_mode:
        buttons.draw_menu_button(
            state.profile_switch_rect,
            "Switch Profile",
            state.game_mouse_pos,
            font=fonts.difficulty_detail_font
        )

    back_button_text = "Cancel" if state.profile_creation_mode else "Back"
    buttons.draw_menu_button(
        profile_back_rect,
        back_button_text,
        state.game_mouse_pos,
        font=fonts.difficulty_detail_font
    )

    if state.profile_message:
        message_surface = fonts.difficulty_detail_font.render(
            state.profile_message,
            True,
            (255, 235, 160)
        )
        window.game_surface.blit(
            message_surface,
            message_surface.get_rect(center=(BASE_WIDTH // 2, 724))
        )


def handle_event(event):
    """Old main-loop event branch for STATE_PROFILE."""

    # ==========================================
    # KEYBOARD INPUT
    # ==========================================

    if event.type == pygame.KEYDOWN:
        active_field = None
        if state.profile_name_active:
            active_field = "name"
        elif state.profile_country_active:
            active_field = "country"
        elif state.profile_age_active:
            active_field = "age"
        elif state.profile_hometown_active:
            active_field = "hometown"
        elif state.profile_bio_active:
            active_field = "bio"

        if active_field is not None:
            if event.key == pygame.K_BACKSPACE:
                if active_field == "name":
                    state.profile_name_text = state.profile_name_text[:-1]
                elif active_field == "country":
                    state.profile_country_text = state.profile_country_text[:-1]
                elif active_field == "age":
                    state.profile_age_text = state.profile_age_text[:-1]
                elif active_field == "hometown":
                    state.profile_hometown_text = state.profile_hometown_text[:-1]
                elif active_field == "bio":
                    state.profile_bio_text = state.profile_bio_text[:-1]

            elif event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                state.profile_name_active = False
                state.profile_country_active = False
                state.profile_age_active = False
                state.profile_hometown_active = False
                state.profile_bio_active = False

            elif event.unicode and event.unicode.isprintable():
                char = event.unicode

                if active_field == "name":
                    if len(state.profile_name_text) < 20:
                        state.profile_name_text += char

                elif active_field == "country":
                    if char.isalpha() and len(state.profile_country_text) < 3:
                        state.profile_country_text += char.upper()

                elif active_field == "age":
                    if char.isdigit() and len(state.profile_age_text) < 3:
                        state.profile_age_text += char

                elif active_field == "hometown":
                    if len(state.profile_hometown_text) < 48:
                        state.profile_hometown_text += char

                elif active_field == "bio":
                    if len(state.profile_bio_text) < 180:
                        state.profile_bio_text += char

    # ==========================================
    # MOUSE INPUT
    # ==========================================

    elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):
        click_consumed = False

        # --------------------------------------
        # Open dropdown choices get first chance
        # --------------------------------------

        if state.gender_dropdown_open:
            for state.index, state.rect in enumerate(profile_gender_option_rects):
                if state.rect.collidepoint(state.game_mouse_pos):
                    state.profile_gender = gender_options[state.index]
                    state.gender_dropdown_open = False
                    state.favorite_suit_dropdown_open = False
                    sounds.audio.play_sound("button_click")
                    click_consumed = True
                    break
            if not click_consumed and not profile_gender_rect.collidepoint(state.game_mouse_pos):
                state.gender_dropdown_open = False

        if not click_consumed and state.favorite_suit_dropdown_open:
            for state.index, state.rect in enumerate(profile_favorite_suit_option_rects):
                if state.rect.collidepoint(state.game_mouse_pos):
                    state.profile_favorite_suit = profile_select.favorite_suit_options[state.index]
                    state.favorite_suit_dropdown_open = False
                    state.gender_dropdown_open = False
                    sounds.audio.play_sound("button_click")
                    click_consumed = True
                    break
            if not click_consumed and not profile_favorite_suit_rect.collidepoint(state.game_mouse_pos):
                state.favorite_suit_dropdown_open = False

        if click_consumed:
            return

        # --------------------------------------
        # Text focus
        # --------------------------------------

        state.profile_name_active = profile_name_rect.collidepoint(state.game_mouse_pos)
        state.profile_country_active = profile_country_rect.collidepoint(state.game_mouse_pos)
        state.profile_age_active = profile_age_rect.collidepoint(state.game_mouse_pos)
        state.profile_hometown_active = profile_hometown_rect.collidepoint(state.game_mouse_pos)
        state.profile_bio_active = profile_bio_rect.collidepoint(state.game_mouse_pos)

        if state.profile_name_active and state.profile_name_text == "Player":
            state.profile_name_text = ""

        # --------------------------------------
        # Dropdown toggles
        # --------------------------------------

        if profile_gender_rect.collidepoint(state.game_mouse_pos):
            state.gender_dropdown_open = not state.gender_dropdown_open
            state.favorite_suit_dropdown_open = False
            state.profile_name_active = False
            state.profile_country_active = False
            state.profile_age_active = False
            state.profile_hometown_active = False
            state.profile_bio_active = False
            sounds.audio.play_sound("button_click")
            return

        if profile_favorite_suit_rect.collidepoint(state.game_mouse_pos):
            state.favorite_suit_dropdown_open = not state.favorite_suit_dropdown_open
            state.gender_dropdown_open = False
            state.profile_name_active = False
            state.profile_country_active = False
            state.profile_age_active = False
            state.profile_hometown_active = False
            state.profile_bio_active = False
            sounds.audio.play_sound("button_click")
            return

        # --------------------------------------
        # Avatar selectors
        # --------------------------------------

        avatar_selector_clicked = False

        for state.index in range(5):
            if avatar_selector_left_rects[state.index].collidepoint(state.game_mouse_pos):
                state.direction = -1
                avatar_selector_clicked = True
            elif avatar_selector_right_rects[state.index].collidepoint(state.game_mouse_pos):
                state.direction = 1
                avatar_selector_clicked = True
            else:
                continue

            if state.index == 0:
                state.selected_avatar_base = cycle_option(
                    state.selected_avatar_base,
                    assets.avatar_base_options,
                    state.direction
                )
            elif state.index == 1:
                state.selected_avatar_eyes = cycle_option(
                    state.selected_avatar_eyes,
                    assets.avatar_eye_options,
                    state.direction
                )
            elif state.index == 2:
                state.selected_avatar_hair = cycle_option(
                    state.selected_avatar_hair,
                    assets.avatar_hair_options,
                    state.direction
                )
            elif state.index == 3:
                state.selected_avatar_glasses = cycle_option(
                    state.selected_avatar_glasses,
                    assets.avatar_glasses_options,
                    state.direction
                )
            elif state.index == 4:
                state.selected_avatar_top = cycle_option(
                    state.selected_avatar_top,
                    assets.avatar_top_options,
                    state.direction
                )

            sounds.audio.play_sound("button_click")
            break

        if avatar_selector_clicked:
            return

        # --------------------------------------
        # Save / Create
        # --------------------------------------

        if profile_save_rect.collidepoint(state.game_mouse_pos):
            country_code = state.profile_country_text.strip().upper()
            if country_code and len(country_code) != 3:
                state.profile_message = "Country must use a 3-letter abbreviation."
                return

            if state.profile_age_text.strip():
                try:
                    state.age_value = int(state.profile_age_text)
                except ValueError:
                    state.age_value = 0
                if not 1 <= state.age_value <= 999:
                    state.profile_message = "Age must be a number from 1 to 999."
                    return
                state.profile_age_text = str(state.age_value)

            state.profile_country_text = country_code
            state.player_name = state.profile_name_text.strip() or "Player"
            state.profile_name_text = state.player_name

            if state.profile_creation_mode:
                state.current_profile_slot = state.pending_profile_slot
                state.guest_mode = False

                save_profile(
                    save_data.build_profile_save_data(),
                    state.current_profile_slot
                )

                state.profile_creation_mode = False
                state.pending_profile_slot = None
                state.profile_message = ""
                sounds.audio.play_sound("button_click")
                profile_select.finish_profile_selection()

            else:
                if not state.guest_mode:
                    save_profile(
                        save_data.build_profile_save_data(),
                        state.current_profile_slot
                    )
                    state.profile_message = f"Profile saved to slot {state.current_profile_slot}."
                else:
                    state.profile_message = "Guest mode does not save progress."

                state.profile_name_active = False
                state.profile_country_active = False
                state.profile_age_active = False
                state.profile_hometown_active = False
                state.profile_bio_active = False
                sounds.audio.play_sound("button_click")

        # --------------------------------------
        # Switch Profile
        # --------------------------------------

        elif (
                not state.profile_creation_mode
                and state.profile_switch_rect.collidepoint(state.game_mouse_pos)
        ):
            sounds.audio.play_sound("button_click")

            if state.profile_return_state == state_names.STATE_CAREER_HUB:
                legacy.begin_career_profile_switch()
                return

            state.profile_select_return_state = state_names.STATE_MENU
            state.profile_name_active = False
            state.profile_country_active = False
            state.profile_age_active = False
            state.profile_hometown_active = False
            state.profile_bio_active = False
            state.gender_dropdown_open = False
            state.favorite_suit_dropdown_open = False
            state.profile_message = ""
            state.pending_profile_slot = None
            state.profile_creation_mode = False
            state.confirm_delete_profile = False
            state.profile_delete_slot = None
            state.current_state = state_names.STATE_PROFILE_SELECT

        # --------------------------------------
        # Back / Cancel
        # --------------------------------------

        elif profile_back_rect.collidepoint(state.game_mouse_pos):
            sounds.audio.play_sound("button_click")

            state.profile_name_active = False
            state.profile_country_active = False
            state.profile_age_active = False
            state.profile_hometown_active = False
            state.profile_bio_active = False
            state.gender_dropdown_open = False
            state.favorite_suit_dropdown_open = False

            if state.profile_creation_mode:
                state.profile_creation_mode = False
                state.pending_profile_slot = None
                state.current_state = state_names.STATE_PROFILE_SELECT
            else:
                if state.profile_return_state == state_names.STATE_CAREER_HUB:
                    legacy.save_career_from_hub()
                state.current_state = state.profile_return_state


def draw():
    """Old draw-chain branch for STATE_PROFILE."""

    draw_profile_screen()
