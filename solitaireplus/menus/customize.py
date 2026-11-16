"""Customize screen: backgrounds, felts, card backs, titles, cursors (moved out of legacy.py)."""
from solitaireplus.profile.achievements import ACHIEVEMENT_DEFINITIONS
from solitaireplus.games.solitaire.rules import BASE_WIDTH
from solitaireplus.app.settings import FELTS
from solitaireplus.app.settings import LEVEL_UNLOCKS
from solitaireplus.app.settings import MENU_BACKGROUNDS
from solitaireplus.app.settings import TITLES
from solitaireplus.profile.unlocks import lock_reason
import os
import pygame
from solitaireplus.profile.unlocks import rating_lock_progress
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.profile.unlocks import unlock_ratings
from solitaireplus.app.lazy import lazy
career_saving = lazy("solitaireplus.career.career_saving")
images = lazy("solitaireplus.ui.images")
table = lazy("solitaireplus.games.solitaire.table")
window = lazy("solitaireplus.app.window")
ui_text = lazy("solitaireplus.ui.text")
sounds = lazy("solitaireplus.app.sounds")
panels = lazy("solitaireplus.ui.panels")
fonts = lazy("solitaireplus.app.fonts")
cursors = lazy("solitaireplus.ui.cursors")
buttons = lazy("solitaireplus.ui.buttons")
assets = lazy("solitaireplus.app.assets")


# ==================================================
# CUSTOMIZATION UI
# ==================================================

customize_backgrounds_rect = pygame.Rect(
    250,
    120,
    200,
    50
)

customize_felts_rect = pygame.Rect(
    472,
    120,
    200,
    50
)

customize_titles_rect = pygame.Rect(
    694,
    120,
    200,
    50
)

customize_cursors_rect = pygame.Rect(
    916,
    120,
    200,
    50
)


customize_item_rects = [
    pygame.Rect(175, 215, 300, 190),
    pygame.Rect(533, 215, 300, 190),
    pygame.Rect(891, 215, 300, 190),

    pygame.Rect(175, 435, 300, 190),
    pygame.Rect(533, 435, 300, 190),
    pygame.Rect(891, 435, 300, 190),
]


customize_prev_rect = pygame.Rect(
    300,
    670,
    180,
    50
)

customize_back_rect = pygame.Rect(
    593,
    670,
    180,
    50
)

customize_next_rect = pygame.Rect(
    886,
    670,
    180,
    50
)
CUSTOMIZE_BACKGROUNDS = "backgrounds"
CUSTOMIZE_FELTS = "felts"
CUSTOMIZE_TITLES = "titles"
CUSTOMIZE_CURSORS = "cursors"

CUSTOMIZE_ITEMS_PER_PAGE = 6

def refresh_cosmetic_assets():
    assets.background_catalog.refresh()
    assets.title_catalog.refresh()
    if assets.felt_catalog.refresh():
        table.sync_selected_cosmetics()


def cosmetic_art_available(asset_id):
    catalog = {CUSTOMIZE_BACKGROUNDS: assets.background_catalog,
               CUSTOMIZE_FELTS: assets.felt_catalog, CUSTOMIZE_TITLES: assets.title_catalog}.get(state.customize_category)
    return catalog.available(asset_id) if catalog is not None else True


def get_customize_data():
    refresh_cosmetic_assets()
    if state.current_game_mode in ("career", "head_to_head") or state.current_profile_slot is not None:
        unlock_ratings(state.career_ratings, (MENU_BACKGROUNDS, FELTS, TITLES),
                       (state.unlocked_menu_backgrounds, state.unlocked_felts, state.unlocked_titles))
    if state.customize_category == CUSTOMIZE_BACKGROUNDS:
        return (
            MENU_BACKGROUNDS,
            assets.menu_background_surfaces,
            state.unlocked_menu_backgrounds,
            state.selected_menu_background
        )

    if state.customize_category == CUSTOMIZE_FELTS:
        return (
            FELTS,
            assets.felt_surfaces,
            state.unlocked_felts,
            state.selected_felt
        )

    if state.customize_category == CUSTOMIZE_TITLES:
        return (
            TITLES,
            assets.title_surfaces,
            state.unlocked_titles,
            state.selected_title
        )

    return (
        cursors.cursor_cosmetics,
        cursors.cursor_preview_surfaces,
        cursors.unlocked_cursors,
        state.selected_cursor
    )


def get_customize_asset_ids():
    asset_data, _, _, _ = (
        get_customize_data()
    )

    return sorted(
        asset_data.keys(),
        key=lambda asset_id: (
            asset_data[
                asset_id
            ].get(
                "order",
                9999
            )
        )
    )


def get_customize_page_count():
    asset_ids = (
        get_customize_asset_ids()
    )

    if not asset_ids:
        return 1

    return max(
        1,
        (
            len(asset_ids)
            + CUSTOMIZE_ITEMS_PER_PAGE
            - 1
        )
        // CUSTOMIZE_ITEMS_PER_PAGE
    )


def equip_customize_item(asset_id):

    refresh_cosmetic_assets()
    if not cosmetic_art_available(asset_id):
        return

    if state.customize_category == CUSTOMIZE_BACKGROUNDS:
        if asset_id not in state.unlocked_menu_backgrounds:
            return

        state.selected_menu_background = asset_id

    elif state.customize_category == CUSTOMIZE_FELTS:
        if asset_id not in state.unlocked_felts:
            return

        state.selected_felt = asset_id

        table.sync_selected_cosmetics()

    elif state.customize_category == CUSTOMIZE_TITLES:
        if asset_id not in state.unlocked_titles:
            return

        state.selected_title = asset_id

    elif state.customize_category == CUSTOMIZE_CURSORS:
        if asset_id not in cursors.unlocked_cursors:
            return

        state.selected_cursor = asset_id
        cursors.apply_selected_cursor()

# ==================================================
# CUSTOMIZATION MENU
# ==================================================

def draw_customize_menu():
    panels.draw_submenu_background(
        overlay_alpha=115
    )

    # ----------------------------
    # Title
    # ----------------------------

    title = fonts.options_title_font.render(
        "CUSTOMIZE",
        True,
        (
            255,
            255,
            255
        )
    )

    title_rect = title.get_rect(
        center=(
            BASE_WIDTH // 2,
            65
        )
    )

    window.game_surface.blit(
        title,
        title_rect
    )

    # ----------------------------
    # Category tabs
    # ----------------------------

    buttons.draw_menu_button(
        customize_backgrounds_rect,
        "Backgrounds",
        state.game_mouse_pos,
        selected=(
                state.customize_category
                == CUSTOMIZE_BACKGROUNDS
        ),
        font=fonts.difficulty_detail_font
    )

    buttons.draw_menu_button(
        customize_felts_rect,
        "Felts",
        state.game_mouse_pos,
        selected=(
                state.customize_category
                == CUSTOMIZE_FELTS
        ),
        font=fonts.difficulty_detail_font
    )

    buttons.draw_menu_button(
        customize_titles_rect,
        "Titles",
        state.game_mouse_pos,
        selected=(
                state.customize_category
                == CUSTOMIZE_TITLES
        ),
        font=fonts.difficulty_detail_font
    )

    buttons.draw_menu_button(
        customize_cursors_rect,
        "Cursors",
        state.game_mouse_pos,
        selected=(
                state.customize_category
                == CUSTOMIZE_CURSORS
        ),
        font=fonts.difficulty_detail_font
    )

    # ----------------------------
    # Player progression
    # ----------------------------

    level_text = fonts.option_value_font.render(
        f"Level {state.player_level}",
        True,
        (
            255,
            255,
            255
        )
    )

    window.game_surface.blit(
        level_text,
        (
            1050,
            40
        )
    )

    if state.player_xp_to_next is not None:
        xp_text_string = (
            f"XP {state.player_xp} / "
            f"{state.player_xp_to_next}"
        )
    else:
        xp_text_string = (
            f"XP {state.player_xp} / MAX"
        )

    xp_text = fonts.option_value_font.render(
        xp_text_string,
        True,
        (
            255,
            255,
            255
        )
    )

    window.game_surface.blit(
        xp_text,
        (
            1050,
            70
        )
    )

    # ----------------------------
    # Current category data
    # ----------------------------

    (
        asset_data,
        surface_data,
        unlocked_ids,
        selected_id
    ) = get_customize_data()

    asset_ids = get_customize_asset_ids()

    start_index = (
        state.customize_page
        * CUSTOMIZE_ITEMS_PER_PAGE
    )

    end_index = (
        start_index
        + CUSTOMIZE_ITEMS_PER_PAGE
    )

    visible_ids = asset_ids[
        start_index:end_index
    ]

    # ----------------------------
    # Item cards
    # ----------------------------

    for index, rect in enumerate(
        customize_item_rects
    ):
        pygame.draw.rect(
            window.game_surface,
            (
                35,
                85,
                60
            ),
            rect
        )

        pygame.draw.rect(
            window.game_surface,
            (
                180,
                180,
                180
            ),
            rect,
            2
        )

        if index >= len(
            visible_ids
        ):
            continue

        asset_id = visible_ids[index]

        data = asset_data[
            asset_id
        ]

        display_name = data[
            "name"
        ]

        unlocked = (
            asset_id
            in unlocked_ids
        )

        selected = (
            asset_id
            == selected_id
        )

        # ------------------------
        # Selected outline
        # ------------------------

        if selected:
            pygame.draw.rect(
                window.game_surface,
                (
                    255,
                    215,
                    0
                ),
                rect,
                5
            )

        # ------------------------
        # Unlocked preview
        # ------------------------

        if unlocked and cosmetic_art_available(asset_id):
            source_surface = (
                surface_data[
                    asset_id
                ]
            )

            if state.customize_category == CUSTOMIZE_CURSORS:
                preview = source_surface
            else:
                preview = (
                    images.scale_surface_to_fit(
                        source_surface,
                        rect.width - 30,
                        rect.height - 60
                    )
                )

            preview_rect = (
                preview.get_rect(
                    center=(
                        rect.centerx,
                        rect.centery - 12
                    )
                )
            )

            window.game_surface.blit(
                preview,
                preview_rect
            )

        # ------------------------
        # Locked placeholder
        # ------------------------

        else:
            lock_rect = pygame.Rect(
                rect.x + 20,
                rect.y + 20,
                rect.width - 40,
                rect.height - 70
            )

            pygame.draw.rect(
                window.game_surface,
                (
                    75,
                    75,
                    75
                ),
                lock_rect
            )

            locked_text = (
                fonts.option_value_font.render(
                    "ARTWORK UNAVAILABLE" if unlocked else "LOCKED",
                    True,
                    (
                        160,
                        160,
                        160
                    )
                )
            )

            locked_rect = (
                locked_text.get_rect(
                    center=lock_rect.center
                )
            )

            window.game_surface.blit(
                locked_text,
                locked_rect
            )
            kind = {CUSTOMIZE_BACKGROUNDS: "backgrounds", CUSTOMIZE_FELTS: "felts", CUSTOMIZE_TITLES: "titles"}.get(state.customize_category, "cursors")
            requirement = os.path.basename(data.get("path", "")) if unlocked else lock_reason(asset_id, data, kind, LEVEL_UNLOCKS, ACHIEVEMENT_DEFINITIONS)
            reason_font = ui_text.get_font(None, 23)
            words, rows = requirement.split(), [""]
            for word in words:
                trial = (rows[-1] + " " + word).strip()
                if reason_font.size(trial)[0] > lock_rect.width - 16:
                    rows.append(word)
                else:
                    rows[-1] = trial
            progress_text = "Add or re-save this PNG" if unlocked else rating_lock_progress(data, state.career_ratings)
            if progress_text:
                rows.append(progress_text)
            # Centre the full lock explanation inside its preview area.
            locked_rect.centery = lock_rect.centery - max(0, len(rows)-1)*11
            pygame.draw.rect(window.game_surface, (75, 75, 75), lock_rect)
            window.game_surface.blit(locked_text, locked_rect)
            for row_index, row in enumerate(rows):
                label = reason_font.render(row, True, (230, 230, 230))
                window.game_surface.blit(label, label.get_rect(midtop=(lock_rect.centerx, locked_rect.bottom + 8 + 22 * row_index)))


        # ------------------------
        # Name
        # ------------------------

        name_surface = (
            fonts.option_value_font.render(
                display_name,
                True,
                (
                    255,
                    255,
                    255
                )
                if unlocked
                else (
                    130,
                    130,
                    130
                )
            )
        )

        name_rect = (
            name_surface.get_rect(
                center=(
                    rect.centerx,
                    rect.bottom - 22
                )
            )
        )

        window.game_surface.blit(
            name_surface,
            name_rect
        )

    # ----------------------------
    # Page controls
    # ----------------------------

    page_count = (
        get_customize_page_count()
    )

    buttons.draw_menu_button(
        customize_prev_rect,
        "Previous",
        state.game_mouse_pos,
        font=fonts.difficulty_detail_font
    )

    buttons.draw_menu_button(
        customize_next_rect,
        "Next",
        state.game_mouse_pos,
        font=fonts.difficulty_detail_font
    )

    buttons.draw_menu_button(
        customize_back_rect,
        "Return",
        state.game_mouse_pos,
        font=fonts.difficulty_detail_font
    )

    page_text = (
        fonts.option_value_font.render(
            (
                f"Page "
                f"{state.customize_page + 1}"
                f" / {page_count}"
            ),
            True,
            (
                255,
                255,
                255
            )
        )
    )

    page_rect = (
        page_text.get_rect(
            center=(
                BASE_WIDTH // 2,
                645
            )
        )
    )

    window.game_surface.blit(
        page_text,
        page_rect
    )


def handle_event(event):
    """Old main-loop event branch for STATE_CUSTOMIZE."""

    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
    ):

        # ----------------------------
        # Category tabs
        # ----------------------------

        if customize_backgrounds_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.customize_category = CUSTOMIZE_BACKGROUNDS

            state.customize_page = 0

        elif customize_felts_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.customize_category = (
                CUSTOMIZE_FELTS
            )

            state.customize_page = 0

        elif customize_titles_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.customize_category = (
                CUSTOMIZE_TITLES
            )

            state.customize_page = 0

        elif customize_cursors_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.customize_category = (
                CUSTOMIZE_CURSORS
            )

            state.customize_page = 0

        # ----------------------------
        # Previous page
        # ----------------------------

        elif customize_prev_rect.collidepoint(
                state.game_mouse_pos
        ):
            if state.customize_page > 0:
                sounds.audio.play_sound(
                    "button_click"
                )

                state.customize_page -= 1

        # ----------------------------
        # Next page
        # ----------------------------

        elif customize_next_rect.collidepoint(
                state.game_mouse_pos
        ):
            page_count = (
                get_customize_page_count()
            )

            if (
                    state.customize_page
                    < page_count - 1
            ):
                sounds.audio.play_sound(
                    "button_click"
                )

                state.customize_page += 1

        # ----------------------------
        # Back
        # ----------------------------

        elif customize_back_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            if state.customize_return_state == state_names.STATE_CAREER_HUB:
                career_saving.save_career_from_hub()
            state.current_state = state.customize_return_state

        # ----------------------------
        # Cosmetic items
        # ----------------------------

        else:
            asset_ids = (
                get_customize_asset_ids()
            )

            start_index = (
                    state.customize_page
                    * CUSTOMIZE_ITEMS_PER_PAGE
            )

            visible_ids = asset_ids[
                start_index:
                start_index
                + CUSTOMIZE_ITEMS_PER_PAGE
            ]

            for item_index, item_rect in enumerate(
                    customize_item_rects
            ):
                if item_index >= len(
                        visible_ids
                ):
                    break

                if item_rect.collidepoint(
                        state.game_mouse_pos
                ):
                    state.asset_id = (
                        visible_ids[item_index]
                    )

                    (
                        _,
                        _,
                        unlocked_ids,
                        _
                    ) = get_customize_data()

                    if state.asset_id in unlocked_ids:
                        sounds.audio.play_sound(
                            "button_click"
                        )

                        equip_customize_item(
                            state.asset_id
                        )

                    break


def draw():
    """Old draw-chain branch for STATE_CUSTOMIZE."""

    draw_customize_menu()
