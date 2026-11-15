"""Career news screen (moved out of legacy.py)."""
from solitaireplus.games.solitaire.rules import BASE_WIDTH
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
web_pages = lazy("solitaireplus.career.web_pages")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
ui_text = lazy("solitaireplus.ui.text")
sounds = lazy("solitaireplus.app.sounds")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")


def add_career_news(
        headline,
        body,
        category="general",
        *, year=None, month=None
):
    news_item = {
        "headline":
            headline,

        "body":
            body,

        "category":
            category,

        "month": state.career_month if month is None else month,

        "year": state.career_year if year is None else year,

        "career_day":
            state.career_day,
    }

    state.career_news_items.insert(
        0,
        news_item
    )

    # Don't let saves grow forever.
    state.career_news_items[:] = (
        state.career_news_items[:50]
    )

def get_career_news_date(
        item
):
    month_names = [
        "",
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    month = item.get(
        "month",
        1
    )

    year = item.get(
        "year",
        2026
    )

    if (
        month < 1
        or month > 12
    ):
        month = 1

    return (
        f"{month_names[month]} "
        f"{year}"
    )

def ensure_career_news():

    if state.career_news_items:
        return

    add_career_news(
        "NEW COMPETITOR JOINS SOLITAIRE CIRCUIT",
        (
            f"{state.player_name} has officially entered "
            f"the international competitive Solitaire scene. "
            f"Industry observers remain unsure what to expect."
        ),
        "career"
    )

def get_career_news_total_pages(
        items_per_page=6
):

    ensure_career_news()

    return max(
        1,
        (
            len(state.career_news_items)
            + items_per_page
            - 1
        )
        // items_per_page
    )

career_news_prev_rect = pygame.Rect(
    430,
    700,
    80,
    45
)

career_news_next_rect = pygame.Rect(
    855,
    700,
    80,
    45
)

def draw_career_news():

    window.game_surface.fill(
        (
            238,
            235,
            220
        )
    )

    # ==================================================
    # Browser
    # ==================================================

    web_pages.draw_career_browser_header(
        "https://www.thecardedcourrier.news"
    )

    ensure_career_news()

    # ==================================================
    # Newspaper Masthead
    # ==================================================

    title = state.courrier_title_font.render(
        "THE CARDED COURRIER",
        True,
        (
            0,
            0,
            0
        )
    )

    title_rect = (
        title.get_rect(
            center=(
                BASE_WIDTH // 2,
                110
            )
        )
    )

    window.game_surface.blit(
        title,
        title_rect
    )

    subtitle = (
        fonts.difficulty_detail_font.render(
            "THE INTERNATIONAL VOICE "
            "OF COMPETITIVE SOLITAIRE",
            True,
            (
                0,
                0,
                0
            )
        )
    )

    subtitle_rect = (
        subtitle.get_rect(
            center=(
                BASE_WIDTH // 2,
                145
            )
        )
    )

    window.game_surface.blit(
        subtitle,
        subtitle_rect
    )

    pygame.draw.line(
        window.game_surface,
        (
            0,
            0,
            0
        ),
        (
            120,
            165
        ),
        (
            BASE_WIDTH - 120,
            165
        ),
        3
    )

    # ==================================================
    # Pagination
    # ==================================================

    items_per_page = 6

    start_index = (
        state.career_news_page
        * items_per_page
    )

    end_index = (
        start_index
        + items_per_page
    )

    visible_news = (
        state.career_news_items[
            start_index:end_index
        ]
    )

    # ==================================================
    # Story Grid
    # ==================================================

    story_rects = [
        pygame.Rect(
            150,
            190,
            500,
            135
        ),

        pygame.Rect(
            715,
            190,
            500,
            135
        ),

        pygame.Rect(
            150,
            345,
            500,
            135
        ),

        pygame.Rect(
            715,
            345,
            500,
            135
        ),

        pygame.Rect(
            150,
            500,
            500,
            135
        ),

        pygame.Rect(
            715,
            500,
            500,
            135
        ),
    ]

    for index, item in enumerate(
            visible_news
    ):

        if index >= len(
            story_rects
        ):
            break

        rect = story_rects[
            index
        ]

        pygame.draw.rect(
            window.game_surface,
            (
                250,
                248,
                235
            ),
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
            2
        )

        # ----------------------------------------------
        # Date
        # ----------------------------------------------

        date_surface = (
            fonts.difficulty_detail_font.render(
                get_career_news_date(
                    item
                ),
                True,
                (
                    90,
                    90,
                    90
                )
            )
        )

        window.game_surface.blit(
            date_surface,
            (
                rect.x + 12,
                rect.y + 8
            )
        )

        # ----------------------------------------------
        # Headline
        # ----------------------------------------------

        headline_surface = (
            ui_text.render_text_fit(
                item.get(
                    "headline",
                    "UNTITLED STORY"
                ),
                fonts.option_label_font,
                rect.width - 24,
                (
                    0,
                    0,
                    0
                ),
                minimum_size=16
            )
        )

        window.game_surface.blit(
            headline_surface,
            (
                rect.x + 12,
                rect.y + 34
            )
        )

        # ----------------------------------------------
        # Body preview
        # ----------------------------------------------

        body = item.get(
            "body",
            ""
        )

        ui_text.draw_wrapped_text(
            body,
            fonts.difficulty_detail_font,
            (
                0,
                0,
                0
            ),
            pygame.Rect(
                rect.x + 12,
                rect.y + 67,
                rect.width - 24,
                58
            ),
            line_spacing=3
        )

    # ==================================================
    # Page Controls
    # ==================================================

    total_pages = (
        get_career_news_total_pages()
    )

    if state.career_news_page > 0:

        buttons.draw_button(
            career_news_prev_rect,
            "<"
        )

    if (
        state.career_news_page
        < total_pages - 1
    ):

        buttons.draw_button(
            career_news_next_rect,
            ">"
        )

    page_surface = (
        fonts.difficulty_detail_font.render(
            (
                f"Page "
                f"{state.career_news_page + 1} "
                f"of {total_pages}"
            ),
            True,
            (
                0,
                0,
                0
            )
        )
    )

    page_rect = (
        page_surface.get_rect(
            center=(
                BASE_WIDTH // 2,
                675
            )
        )
    )

    window.game_surface.blit(
        page_surface,
        page_rect
    )

    buttons.draw_button(
        web_pages.career_subpage_back_rect,
        "Return to Career"
    )


def handle_event(event):
    """Old main-loop event branch for STATE_CAREER_NEWS."""

    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
    ):

        total_pages = (
            get_career_news_total_pages()
        )

        # ==========================================
        # Previous
        # ==========================================

        if (
                state.career_news_page > 0
                and career_news_prev_rect.collidepoint(
            state.game_mouse_pos
        )
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.career_news_page -= 1

        # ==========================================
        # Next
        # ==========================================

        elif (
                state.career_news_page
                < total_pages - 1
                and career_news_next_rect.collidepoint(
            state.game_mouse_pos
        )
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.career_news_page += 1

        # ==========================================
        # Return
        # ==========================================

        elif web_pages.career_subpage_back_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.current_state = state_names.STATE_CAREER_HUB


def draw():
    """Old draw-chain branch for STATE_CAREER_NEWS."""

    draw_career_news()
