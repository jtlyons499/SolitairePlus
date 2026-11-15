"""Career real-estate screen (moved out of legacy.py)."""
from solitaireplus.games.solitaire.rules import BASE_WIDTH
from solitaireplus.career.fans import fan_bonus_for_residence
from solitaireplus.career.asset_images import get_realestate_image
from solitaireplus.app import paths
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
web_pages = lazy("solitaireplus.career.web_pages")
news_screen = lazy("solitaireplus.career.news_screen")
career_saving = lazy("solitaireplus.career.career_saving")
career_rewards = lazy("solitaireplus.career.career_rewards")
career_names = lazy("solitaireplus.career.career_names")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
ui_text = lazy("solitaireplus.ui.text")
sounds = lazy("solitaireplus.app.sounds")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")


CAREER_RESIDENCES = {
    "dingy_apartment": {
        "name":
            "Dingy Apartment",

        "price":
            0,

        "image":
            str(paths.asset("career/residences/dingy_apartment.png")),
    },

    "hippie_commune": {
        "name":
            "Hippie Commune",

        "price":
            500,

        "image":
            str(paths.asset("career/residences/hippie_commune.png")),
    },

    "towers": {
        "name":
            "Tableau Towers",

        "price":
            1500,

        "image":
            str(paths.asset("career/residences/towers.png")),
    },

    "summit": {
        "name":
            "Sorcerer's Summit",

        "price":
            4000,

        "image":
            str(paths.asset("career/residences/summit.png")),
    },

    "heliyacht": {
        "name":
            "Heliyacht",

        "price":
            10000,

        "image":
            str(paths.asset("career/residences/heliyacht.png")),
    },

    "card_castle": {
        "name":
            "Card Castle",

        "price":
            25000,

        "image":
            str(paths.asset("career/residences/card_castle.png")),
    },
}

career_residence_image_cache = {}

career_residence_option_rects = {
    "dingy_apartment": pygame.Rect(285,230,375,140),
    "hippie_commune": pygame.Rect(705,230,375,140),

    "towers": pygame.Rect(285,385,375,140),
    "summit": pygame.Rect(705,385,375,140),

    "heliyacht": pygame.Rect(285,540,375,140),
    "card_castle": pygame.Rect(705,540,375,140),
}

def get_career_residence_image(
        residence_id,
        size
):
    residence_data = (
        CAREER_RESIDENCES.get(
            residence_id
        )
    )

    if residence_data is None:
        return None

    image_path = (
        residence_data.get(
            "image"
        )
    )

    if not image_path:
        return None

    cache_key = (
        residence_id,
        size
    )

    if (
        cache_key
        in career_residence_image_cache
    ):
        return (
            career_residence_image_cache[
                cache_key
            ]
        )



    try:
        image = pygame.image.load(
            image_path
        ).convert_alpha()

        image = (
            pygame.transform.smoothscale(
                image,
                size
            )
        )

        career_residence_image_cache[
            cache_key
        ] = image

        return image


    except (

            pygame.error,

            FileNotFoundError

    ) as error:

        print(

            "Residence image failed:",

            image_path,

            error

        )

        return None

def draw_career_real_estate():

    window.game_surface.fill(
        (
            238,
            235,
            220
        )
    )

    # ==================================================
    # Browser Header
    # ==================================================

    web_pages.draw_career_browser_header(
        "https://www.realestate.apt"
    )

    realestate_header = get_realestate_image(
        "realestate_header.png",
        (
            BASE_WIDTH,
            58
        )
    )

    if realestate_header is not None:
        window.game_surface.blit(
            realestate_header,
            (
                0,
                64
            )
        )

    # ==================================================
    # Title
    # ==================================================

    title = fonts.menu_title_font.render(
        "REALEST.ESTATE.ONLINE.",
        True,
        (
            0,
            0,
            0
        )
    )

    title_rect = title.get_rect(
        center=(
            BASE_WIDTH // 2,
            150
        )
    )

    window.game_surface.blit(
        title,
        title_rect
    )

    cash_surface = (
        fonts.option_label_font.render(
            f"Available Cash: "
            f"${state.career_cash:,}",
            True,
            (
                0,
                0,
                0
            )
        )
    )

    cash_rect = (
        cash_surface.get_rect(
            center=(
                BASE_WIDTH // 2,
                185
            )
        )
    )

    window.game_surface.blit(
        cash_surface,
        cash_rect
    )



    # ==================================================
    # Listings
    # ==================================================

    for residence_id, rect in (
        career_residence_option_rects.items()
    ):

        residence_data = (
            CAREER_RESIDENCES[
                residence_id
            ]
        )

        price = (
            residence_data[
                "price"
            ]
        )

        owned = (
            residence_id
            in state.career_owned_residences
        )

        current = (
            state.career_residence
            == residence_id
        )

        affordable = (
            state.career_cash >= price
        )

        # ----------------------------------------------
        # Card background
        # ----------------------------------------------

        if current:
            fill_color = (
                210,
                240,
                210
            )

        elif owned:
            fill_color = (
                220,
                235,
                255
            )

        elif affordable:
            fill_color = (
                210,
                230,
                255
            )

        else:
            fill_color = (
                245,
                205,
                205
            )

        pygame.draw.rect(
            window.game_surface,
            fill_color,
            rect
        )

        pygame.draw.rect(
            window.game_surface,
            (
                0,
                0,
                0
            ),
            rect,
            3
        )

        # ----------------------------------------------
        # Doodle
        # ----------------------------------------------

        image = (
            get_career_residence_image(
                residence_id,
                (
                    150,
                    112
                )
            )
        )

        text_x = (
            rect.x + 175
        )

        if image is not None:

            image_rect = (
                image.get_rect(
                    midleft=(
                        rect.x + 12,
                        rect.centery
                    )
                )
            )

            window.game_surface.blit(
                image,
                image_rect
            )

            text_x = (
                rect.x + 175
            )

        # ----------------------------------------------
        # Residence Name Rendering Block
        # ----------------------------------------------

        # ----------------------------------------------
        # Residence Name
        # ----------------------------------------------

        if residence_id == "summit":
            residence_name_font = ui_text.get_font(
                None,
                25
            )

            name_surface = (
                residence_name_font.render(
                    residence_data[
                        "name"
                    ],
                    True,
                    (
                        0,
                        0,
                        0
                    )
                )
            )

        else:
            name_surface = (
                fonts.option_label_font.render(
                    residence_data[
                        "name"
                    ],
                    True,
                    (
                        0,
                        0,
                        0
                    )
                )
            )

        window.game_surface.blit(
            name_surface,
            (
                text_x,
                rect.y + 18
            )
        )

        # ----------------------------------------------
        # Price
        # ----------------------------------------------

        if price <= 0:
            price_text = (
                "Starter Residence"
            )

        elif owned:
            price_text = (
                "Owned"
            )

        else:
            price_text = (
                f"${price:,}"
            )

        price_surface = (
            fonts.difficulty_detail_font.render(
                price_text,
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        window.game_surface.blit(
            price_surface,
            (
                text_x,
                rect.y + 62
            )
        )

        # ----------------------------------------------
        # Status
        # ----------------------------------------------

        if current:
            status_text = "HERE"

        elif owned:
            status_text = "MOVE IN"

        elif affordable:
            status_text = "BUY"

        else:
            status_text = "TOO POOR"

        status_surface = (
            fonts.difficulty_detail_font.render(
                status_text,
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        window.game_surface.blit(
            status_surface,
            (
                text_x,
                rect.y + 95
            )
        )

        # ==================================================
        # Property badges / stamps
        # ==================================================

        badge_image = None
        badge_filename = None

        # Current residence
        if residence_id == state.career_residence:

            badge_filename = (
                "current_stamp.png"
            )

            badge_image = get_realestate_image(
                badge_filename,
                (
                    110,
                    38
                )
            )

        # Owned residence
        elif residence_id in state.career_owned_residences:

            badge_filename = (
                "owned_stamp.png"
            )

            badge_image = get_realestate_image(
                badge_filename,
                (
                    85,
                    36
                )
            )

        # Featured
        elif residence_id in (
                "towers",
                "card_castle"
        ):

            badge_filename = (
                "featured_badge.png"
            )

            badge_image = get_realestate_image(
                badge_filename,
                (
                    95,
                    40
                )
            )

        # Hot listing
        elif residence_id in (
                "summit",
                "heliyacht"
        ):

            badge_filename = (
                "hot_listing.png"
            )

            badge_image = get_realestate_image(
                badge_filename,
                (
                    80,
                    38
                )
            )

        if badge_filename is not None and badge_image is None:
            print(
                "Could not load RealEstate badge:",
                badge_filename,
                "for",
                residence_id
            )

        if badge_image is not None:

            if badge_filename in (
                    "featured_badge.png",
                    "hot_listing.png"
            ):

                badge_rect = badge_image.get_rect(
                    top=rect.y + 6,
                    left=rect.right - 35
                )


            else:

                badge_rect = badge_image.get_rect(
                    bottom=rect.bottom - 8,
                    right=rect.right - 8
                )

            window.game_surface.blit(
                badge_image,
                badge_rect
            )

    buttons.draw_button(
        web_pages.career_subpage_back_rect,
        "Return to Career"
    )


def handle_event(event):
    """Old main-loop event branch for STATE_CAREER_REAL_ESTATE."""

    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
    ):

        residence_clicked = None

        for residence_id, state.rect in (
                career_residence_option_rects.items()
        ):

            if state.rect.collidepoint(
                    state.game_mouse_pos
            ):
                residence_clicked = (
                    residence_id
                )

                break

        if residence_clicked is not None:

            residence_data = (
                CAREER_RESIDENCES[
                    residence_clicked
                ]
            )

            price = (
                residence_data[
                    "price"
                ]
            )

            # ==========================================
            # Already owned
            # ==========================================

            if (
                    residence_clicked
                    in state.career_owned_residences
            ):
                sounds.audio.play_sound(
                    "button_click"
                )

                state.career_residence = (
                    residence_clicked
                )

                career_saving.auto_save_career()

            # ==========================================
            # Purchase
            # ==========================================

            elif (
                    state.career_cash
                    >= price
            ):
                sounds.audio.play_sound(
                    "button_click"
                )

                state.career_cash -= price

                state.career_owned_residences.append(
                    residence_clicked
                )

                state.career_residence = (
                    residence_clicked
                )

                fan_bonus = career_rewards.award_career_fans(
                    fan_bonus_for_residence(price),
                    f"New residence: {career_names.get_career_residence_name()}"
                )

                news_screen.add_career_news(
                    (
                        f"{state.player_name.upper()} "
                        f"PURCHASES "
                        f"{career_names.get_career_residence_name().upper()}"
                    ),
                    (
                        f"The competitive Solitaire player "
                        f"has reportedly moved into "
                        f"{career_names.get_career_residence_name()} "
                        f"after completing the purchase."
                    ),
                    "residence"
                )

                career_saving.auto_save_career()

        elif web_pages.career_subpage_back_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.current_state = state_names.STATE_CAREER_HUB


def draw():
    """Old draw-chain branch for STATE_CAREER_REAL_ESTATE."""

    draw_career_real_estate()
