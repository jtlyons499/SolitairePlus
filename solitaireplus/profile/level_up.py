"""Level-up screen (moved out of legacy.py)."""
from solitaireplus.games.solitaire.rules import BASE_WIDTH
from solitaireplus.app.settings import FELTS
from solitaireplus.app.settings import MENU_BACKGROUNDS
from solitaireplus.app.settings import TITLES
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
images = lazy("solitaireplus.ui.images")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")
assets = lazy("solitaireplus.app.assets")


level_up_continue_rect = pygame.Rect(
    533,
    690,
    300,
    48
)

def get_unlock_asset_data(
    unlock_type,
    asset_id
):
    if unlock_type == 'cryptid_pack':
        return ({'name':f'{asset_id} Creature Card Packs'},None,'Cryptid Creatures')
    if unlock_type == "background":
        return (
            MENU_BACKGROUNDS[asset_id],
            assets.menu_background_surfaces[
                asset_id
            ],
            "Menu Background"
        )

    if unlock_type == "felt":
        return (
            FELTS[asset_id],
            assets.felt_surfaces[
                asset_id
            ],
            "Felt Background"
        )

    if unlock_type == "title":
        return (
            TITLES[asset_id],
            assets.title_surfaces[
                asset_id
            ],
            "Menu Title"
        )

    return (
        {
            "name": asset_id
        },
        None,
        "Unlock"
    )

def advance_level_up_screen():

    if state.level_up_queue:
        state.current_level_up_data = (
            state.level_up_queue.pop(0)
        )

        state.current_state = state_names.STATE_LEVEL_UP


    else:

        state.current_level_up_data = None

        state.current_state = state.post_round_return_state

# ==================================================
# LEVEL UP SCREEN
# ==================================================

def draw_level_up_screen():
    window.game_surface.fill((20, 190, 20))

    if state.current_level_up_data is None:
        return

    level = state.current_level_up_data["level"]
    unlocks = list(state.current_level_up_data.get("unlocks", []))

    heading = fonts.menu_title_font.render(
        f"You've reached level {level}!",
        True,
        (255, 255, 255),
    )
    window.game_surface.blit(
        heading,
        heading.get_rect(center=(BASE_WIDTH // 2, 58)),
    )

    subheading = fonts.options_title_font.render(
        "you've unlocked:",
        True,
        (255, 255, 255),
    )
    window.game_surface.blit(
        subheading,
        subheading.get_rect(center=(BASE_WIDTH // 2, 120)),
    )

    if unlocks:
        count = len(unlocks)
        if count <= 2:
            columns = count
            card_width, card_height = 360, 220
        elif count == 4:
            columns = 2
            card_width, card_height = 360, 190
        else:
            columns = min(3, count)
            card_width, card_height = 300, 190

        rows = (count + columns - 1) // columns
        gap_x = 28
        gap_y = 20
        card_height = min(card_height, (430 - max(0, rows - 1) * gap_y) // rows)
        total_height = rows * card_height + max(0, rows - 1) * gap_y
        start_y = 165 + max(0, (430 - total_height) // 2)

        for index, (unlock_type, asset_id) in enumerate(unlocks):
            row = index // columns
            column = index % columns

            items_this_row = min(columns, count - row * columns)
            row_width = (
                items_this_row * card_width
                + max(0, items_this_row - 1) * gap_x
            )
            row_start_x = (BASE_WIDTH - row_width) // 2
            card_x = row_start_x + column * (card_width + gap_x)
            card_y = start_y + row * (card_height + gap_y)

            card_rect = pygame.Rect(
                card_x,
                card_y,
                card_width,
                card_height,
            )

            pygame.draw.rect(
                window.game_surface,
                (245, 245, 245),
                card_rect,
                border_radius=10,
            )
            pygame.draw.rect(
                window.game_surface,
                (50, 50, 50),
                card_rect,
                2,
                border_radius=10,
            )

            asset_data, asset_surface, category_name = get_unlock_asset_data(
                unlock_type,
                asset_id,
            )

            preview_height = min(105 if card_height >= 210 else 82, max(30, card_height - 95))
            if asset_surface is not None:
                preview = images.scale_surface_to_fit(
                    asset_surface,
                    card_width - 34,
                    preview_height,
                )
                preview_rect = preview.get_rect(
                    center=(
                        card_rect.centerx,
                        card_rect.y + 18 + preview_height // 2,
                    )
                )
                window.game_surface.blit(preview, preview_rect)

            category_font = fonts.difficulty_detail_font
            category_surface = category_font.render(
                category_name,
                True,
                (65, 65, 65),
            )
            window.game_surface.blit(
                category_surface,
                category_surface.get_rect(
                    center=(card_rect.centerx, card_rect.bottom - 54)
                ),
            )

            name_text = str(asset_data.get("name", asset_id))
            name_font = fonts.option_value_font
            while name_font.size(name_text)[0] > card_width - 24 and len(name_text) > 4:
                name_text = name_text[:-4].rstrip() + "..."
            name_surface = name_font.render(
                name_text,
                True,
                (0, 0, 0),
            )
            window.game_surface.blit(
                name_surface,
                name_surface.get_rect(
                    center=(card_rect.centerx, card_rect.bottom - 25)
                ),
            )
    else:
        no_unlock_text = fonts.option_label_font.render(
            "No cosmetic unlocks this level.",
            True,
            (255, 255, 255),
        )
        window.game_surface.blit(
            no_unlock_text,
            no_unlock_text.get_rect(center=(BASE_WIDTH // 2, 375)),
        )

    if state.player_xp_to_next is not None:
        xp_string = f"{state.player_name}'s XP: {state.player_xp:,} / {state.player_xp_to_next:,}"
    else:
        xp_string = f"{state.player_name}'s XP: {state.player_xp:,} / MAX"

    xp_surface = fonts.option_label_font.render(
        xp_string,
        True,
        (0, 0, 0),
    )
    window.game_surface.blit(
        xp_surface,
        xp_surface.get_rect(center=(BASE_WIDTH // 2, 650)),
    )

    buttons.draw_button(
        level_up_continue_rect,
        "Continue",
        font=fonts.option_value_font,
    )


def handle_event(event):
    """Old main-loop event branch for STATE_LEVEL_UP."""

    continue_level_up = (
        event.type == pygame.KEYDOWN
        and event.key in (
            pygame.K_RETURN,
            pygame.K_KP_ENTER,
            pygame.K_SPACE,
            pygame.K_ESCAPE,
        )
    )

    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
            and level_up_continue_rect.collidepoint(state.game_mouse_pos)
    ):
        continue_level_up = True

    if continue_level_up:
        sounds.audio.play_sound("button_click")
        advance_level_up_screen()


def draw():
    """Old draw-chain branch for STATE_LEVEL_UP."""

    draw_level_up_screen()


# The old loop drew this screen in its second draw chain (see app/loop.py).
DRAWS_LATE = True
