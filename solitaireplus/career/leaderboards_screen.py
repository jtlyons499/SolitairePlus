"""Career leaderboards screen (moved out of legacy.py)."""
from solitaireplus.games.solitaire.rules import BASE_WIDTH
from solitaireplus.career.ratings import RATING_DISPLAY_NAMES
from solitaireplus.career.ratings import RATING_KEYS
from solitaireplus.career.asset_images import get_country_flag_surface
from solitaireplus.npc.personality import personality_summary
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
web_pages = lazy("solitaireplus.career.web_pages")
leaderboard_engine = lazy("solitaireplus.career.leaderboard_engine")
window = lazy("solitaireplus.app.window")
ui_text = lazy("solitaireplus.ui.text")
sounds = lazy("solitaireplus.app.sounds")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")


def get_career_leaderboard_total_pages(
        entries_per_page=20,
        rating_key=None
):
    leaderboard = (
        leaderboard_engine.get_career_leaderboard(
            rating_key=rating_key
        )
    )

    return max(
        1,
        (
            len(leaderboard)
            + entries_per_page
            - 1
        )
        // entries_per_page
    )

career_leaderboard_prev_rect = pygame.Rect(
    430,
    700,
    80,
    45
)

career_leaderboard_next_rect = pygame.Rect(
    855,
    700,
    80,
    45
)

career_leaderboard_rating_prev_rect = pygame.Rect(
    510,
    164,
    42,
    30
)

career_leaderboard_rating_next_rect = pygame.Rect(
    814,
    164,
    42,
    30
)

def draw_career_leaderboards():

    state.career_leaderboard_bio_rects = []

    window.game_surface.fill(
        (
            235,
            235,
            225
        )
    )

    # ==================================================
    # Browser
    # ==================================================

    web_pages.draw_career_browser_header(
        "https://www.cardrankings.net"
    )

    # ==================================================
    # Title / selected rating
    # ==================================================

    title = fonts.menu_title_font.render(
        "INTERNATIONAL CARD RANKINGS",
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
            103
        )
    )

    window.game_surface.blit(
        title,
        title_rect
    )

    rating_label = RATING_DISPLAY_NAMES.get(
        state.career_leaderboard_rating_key,
        "Global"
    )

    player_rank = (
        leaderboard_engine.get_player_leaderboard_rank(
            state.career_leaderboard_rating_key
        )
    )

    selected_player_rating = state.career_ratings.get(
        state.career_leaderboard_rating_key,
        state.career_rating
    )

    player_info = (
        f"Your Rank: #{player_rank}     "
        f"{rating_label}: "
        f"{selected_player_rating:,}"
    )

    player_surface = (
        fonts.option_label_font.render(
            player_info,
            True,
            (
                0,
                0,
                0
            )
        )
    )

    player_rect = (
        player_surface.get_rect(
            center=(
                BASE_WIDTH // 2,
                140
            )
        )
    )

    window.game_surface.blit(
        player_surface,
        player_rect
    )

    buttons.draw_button(
        career_leaderboard_rating_prev_rect,
        "<",
        font=fonts.difficulty_detail_font
    )

    buttons.draw_button(
        career_leaderboard_rating_next_rect,
        ">",
        font=fonts.difficulty_detail_font
    )

    filter_surface = (
        fonts.option_value_font.render(
            "Sort by: " + {"overall": "Global", "strategy": "Strategy", "poker": "Poker", "casino": "Casino"}.get(state.career_leaderboard_rating_key, "Global"),
            True,
            (
                20,
                20,
                20
            )
        )
    )

    filter_rect = filter_surface.get_rect(
        center=(
            BASE_WIDTH // 2,
            179
        )
    )

    window.game_surface.blit(
        filter_surface,
        filter_rect
    )

    # ==================================================
    # Table
    # ==================================================

    leaderboard = (
        leaderboard_engine.get_career_leaderboard(
            state.career_leaderboard_rating_key
        )
    )

    entries_per_page = 20

    start_index = (
            state.career_leaderboard_page
            * entries_per_page
    )

    end_index = (
            start_index
            + entries_per_page
    )

    visible_entries = (
        leaderboard[
            start_index:end_index
        ]
    )

    left_x = 205
    right_x = 700
    first_y = 210
    row_height = 43

    # Two columns of 10.
    for index, entry in enumerate(
        visible_entries
    ):

        if index < 10:
            column_x = left_x
            row_index = index
        else:
            column_x = right_x
            row_index = index - 10

        row_rect = pygame.Rect(
            column_x,
            first_y
            + row_index
            * row_height,
            460,
            38
        )

        if entry.get(
            "is_player"
        ):
            fill_color = (
                255,
                245,
                190
            )
        else:
            fill_color = (
                250,
                250,
                250
            )

        pygame.draw.rect(
            window.game_surface,
            fill_color,
            row_rect
        )

        pygame.draw.rect(
            window.game_surface,
            (
                0,
                0,
                0
            ),
            row_rect,
            2
        )

        rank = (
                start_index
                + index
                + 1
        )

        rank_surface = (
            fonts.difficulty_detail_font.render(
                f"{rank}.",
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        window.game_surface.blit(
            rank_surface,
            (
                row_rect.x + 7,
                row_rect.y + 9
            )
        )

        # ----------------------------------------------
        # Country flag thumbnail
        # ----------------------------------------------

        flag_box = pygame.Rect(
            row_rect.x + 38,
            row_rect.y + 4,
            30,
            30
        )
        flag = get_country_flag_surface(
            entry.get("country", ""),
            (30, 20)
        )

        if flag is not None:
            flag_rect = flag.get_rect(center=flag_box.center)
            window.game_surface.blit(flag, flag_rect)
            pygame.draw.rect(
                window.game_surface,
                (85, 85, 85),
                flag_rect.inflate(2, 2),
                1
            )
        else:
            code_surface = fonts.leaderboard_tiny_font.render(
                str(entry.get("country", ""))[:3],
                True,
                (70, 70, 70)
            )
            window.game_surface.blit(
                code_surface,
                code_surface.get_rect(center=flag_box.center)
            )

        # ----------------------------------------------
        # Name + personality
        # ----------------------------------------------

        country = entry.get(
            "country",
            ""
        )

        display_name = entry.get(
            "name",
            "Unknown"
        )

        name_surface = ui_text.render_text_fit(
            display_name,
            fonts.difficulty_detail_font,
            168,
            (
                0,
                0,
                0
            ),
            minimum_size=11
        )

        name_x = row_rect.x + 76

        window.game_surface.blit(
            name_surface,
            (
                name_x,
                row_rect.y + 3
            )
        )

        personality = personality_summary(entry.get("npc") or entry).split(" / ")[0]

        if entry.get(
            "is_player"
        ):
            personality = "You"

        personality_surface = (
            fonts.leaderboard_tiny_font.render(
                personality,
                True,
                (
                    95,
                    95,
                    95
                )
            )
        )

        window.game_surface.blit(
            personality_surface,
            (
                name_x,
                row_rect.y + 21
            )
        )

        # ----------------------------------------------
        # Rating
        # ----------------------------------------------

        rating_surface = (
            fonts.difficulty_detail_font.render(
                f"{round(entry['rating']):,}",
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        rating_rect = (
            rating_surface.get_rect(
                right=(
                        row_rect.x
                        + 355
                ),
                centery=(
                    row_rect.centery
                )
            )
        )

        window.game_surface.blit(
            rating_surface,
            rating_rect
        )

        # ----------------------------------------------
        # Last movement in the selected game category
        # ----------------------------------------------

        # Keep fractional progress in saves; leaderboard movements are whole points.
        rating_change = int(round(entry.get("last_change", 0)))

        if rating_change > 0:
            change_text = (
                f"+{rating_change}"
            )
            change_color = (
                25,
                140,
                45
            )

        elif rating_change < 0:
            change_text = str(
                rating_change
            )
            change_color = (
                190,
                35,
                35
            )

        else:
            change_text = ""

        if change_text:
            change_surface = (
                ui_text.get_font(None, 24).render(
                    change_text,
                    True,
                    change_color
                )
            )

            window.game_surface.blit(
                change_surface,
                (
                    rating_rect.right + 5,
                    row_rect.centery - change_surface.get_height() // 2
                )
            )

        # ----------------------------------------------
        # View Bio
        # ----------------------------------------------

        bio_surface = (
            fonts.difficulty_detail_font.render(
                "Bio",
                True,
                (
                    20,
                    70,
                    170
                )
            )
        )

        bio_rect = (
            bio_surface.get_rect(
                right=(
                        row_rect.right
                        - 9
                ),
                centery=(
                    row_rect.centery
                )
            )
        )

        window.game_surface.blit(
            bio_surface,
            bio_rect
        )

        state.career_leaderboard_bio_rects.append(
            (
                bio_rect.copy(),
                entry
            )
        )

    # ==================================================
    # Player outside visible page
    # ==================================================

    if (
        player_rank is not None
        and not (
            start_index
            < player_rank
            <= end_index
        )
    ):

        outside_text = (
            f"You are #{player_rank} in {rating_label} "
            f"with {selected_player_rating:,} Rating."
        )

        outside_surface = (
            fonts.option_label_font.render(
                outside_text,
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        outside_rect = (
            outside_surface.get_rect(
                center=(
                    BASE_WIDTH // 2,
                    655
                )
            )
        )

        window.game_surface.blit(
            outside_surface,
            outside_rect
        )

    # ==================================================
    # Leaderboard Pagination
    # ==================================================

    total_pages = max(
        1,
        (
                len(leaderboard)
                + entries_per_page
                - 1
        )
        // entries_per_page
    )

    if state.career_leaderboard_page > 0:
        buttons.draw_button(
            career_leaderboard_prev_rect,
            "<"
        )

    if (
            state.career_leaderboard_page
            < total_pages - 1
    ):
        buttons.draw_button(
            career_leaderboard_next_rect,
            ">"
        )

    page_text = (
        f"Page "
        f"{state.career_leaderboard_page + 1} "
        f"of {total_pages}"
    )

    page_surface = (
        fonts.difficulty_detail_font.render(
            page_text,
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
    """Old main-loop event branch for STATE_CAREER_LEADERBOARDS."""

    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
    ):

        total_pages = (
            get_career_leaderboard_total_pages(
                rating_key=state.career_leaderboard_rating_key
            )
        )

        bio_clicked = False
        rating_filter_clicked = False

        # ==========================================
        # Rating category selector
        # ==========================================

        if career_leaderboard_rating_prev_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.current_index = RATING_KEYS.index(
                state.career_leaderboard_rating_key
            )

            state.career_leaderboard_rating_key = RATING_KEYS[
                (state.current_index - 1)
                % len(RATING_KEYS)
            ]

            state.career_leaderboard_page = 0
            rating_filter_clicked = True

        elif career_leaderboard_rating_next_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.current_index = RATING_KEYS.index(
                state.career_leaderboard_rating_key
            )

            state.career_leaderboard_rating_key = RATING_KEYS[
                (state.current_index + 1)
                % len(RATING_KEYS)
            ]

            state.career_leaderboard_page = 0
            rating_filter_clicked = True

        # ==========================================
        # Bio links
        # ==========================================

        if not rating_filter_clicked:
            for bio_rect, entry in state.career_leaderboard_bio_rects:

                if bio_rect.collidepoint(
                        state.game_mouse_pos
                ):
                    sounds.audio.play_sound(
                        "button_click"
                    )

                    state.selected_leaderboard_entry = (
                        entry
                    )

                    state.current_state = state_names.STATE_CAREER_LEADERBOARD_BIO

                    bio_clicked = True

                    break

        # Previous pagination logic continues below.

        # ==========================================
        # Previous Page
        # ==========================================

        if (
                not bio_clicked
                and not rating_filter_clicked
                and state.career_leaderboard_page > 0
                and career_leaderboard_prev_rect.collidepoint(
            state.game_mouse_pos
        )
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.career_leaderboard_page -= 1

        # ==========================================
        # Next Page
        # ==========================================

        elif (
                not bio_clicked
                and not rating_filter_clicked
                and state.career_leaderboard_page
                < total_pages - 1
                and career_leaderboard_next_rect.collidepoint(
            state.game_mouse_pos
        )
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.career_leaderboard_page += 1

        # ==========================================
        # Return to Career
        # ==========================================

        elif (
                not bio_clicked
                and not rating_filter_clicked
                and web_pages.career_subpage_back_rect.collidepoint(
            state.game_mouse_pos
        )
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.current_state = state_names.STATE_CAREER_HUB


def draw():
    """Old draw-chain branch for STATE_CAREER_LEADERBOARDS."""

    draw_career_leaderboards()
