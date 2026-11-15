"""Career jobs screen (moved out of legacy.py)."""
from solitaireplus.games.solitaire.rules import BASE_HEIGHT
from solitaireplus.games.solitaire.rules import BASE_WIDTH
from solitaireplus.career.fans import fan_bonus_for_job
from solitaireplus.career.asset_images import get_jobfinder_image
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
web_pages = lazy("solitaireplus.career.web_pages")
news_screen = lazy("solitaireplus.career.news_screen")
night = lazy("solitaireplus.career.events.night")
career_saving = lazy("solitaireplus.career.career_saving")
career_rewards = lazy("solitaireplus.career.career_rewards")
career_names = lazy("solitaireplus.career.career_names")
calendar = lazy("solitaireplus.career.calendar")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
ui_text = lazy("solitaireplus.ui.text")
sounds = lazy("solitaireplus.app.sounds")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")


def refresh_future_work_tasks():

    for entry in state.career_current_schedule:

        # Ignore past days.
        if (
            entry.get(
                "day_number",
                0
            )
            < state.career_day_of_month
        ):
            continue

        # Only update work days.
        if (
            entry.get(
                "activity_type"
            )
            != night.CAREER_ACTIVITY_WORK
        ):
            continue

        # Reroll a task using the
        # player's NEW current job.
        entry[
            "title"
        ] = calendar.get_career_work_activity_name()

career_job_image_cache = {}

career_job_option_rects = {
    "custodian":
        pygame.Rect(
            285,
            180,
            375,
            145
        ),

    "satellite_repair":
        pygame.Rect(
            705,
            180,
            375,
            145
        ),

    "videographer":
        pygame.Rect(
            285,
            345,
            375,
            145
        ),

    "airline_pilot":
        pygame.Rect(
            705,
            345,
            375,
            145
        ),

    "spiritual_guru":
        pygame.Rect(
            285,
            510,
            375,
            145
        ),

    "solitaire_pensioner":
        pygame.Rect(
            705,
            510,
            375,
            145
        ),
}

def get_career_job_image(
        job_id,
        size
):
    job_data = (
        career_names.CAREER_JOBS.get(
            job_id
        )
    )

    if job_data is None:
        return None

    image_path = (
        job_data.get(
            "image"
        )
    )

    if not image_path:
        return None

    cache_key = (
        job_id,
        size
    )

    if (
        cache_key
        in career_job_image_cache
    ):
        return (
            career_job_image_cache[
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

        career_job_image_cache[
            cache_key
        ] = image

        return image

    except (
        pygame.error,
        FileNotFoundError
    ):
        return None

def draw_career_jobs():
    window.game_surface.fill(
        (
            235,
            235,
            225
        )
    )

    background_image = get_jobfinder_image(
        "jobfinder_background.png",
        (
            BASE_WIDTH,
            BASE_HEIGHT
        )
    )

    if background_image is not None:
        window.game_surface.blit(
            background_image,
            (
                0,
                0
            )
        )

    # ==================================================
    # Browser
    # ==================================================

    web_pages.draw_career_browser_header(
        "https://www.jimbosjobfinder.sk"
    )

    # ==================================================
    # Page Title
    # ==================================================

    title = fonts.menu_title_font.render(
        "JIMBO'S JOB FINDER",
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
            105
        )
    )

    window.game_surface.blit(
        title,
        title_rect
    )

    rating_surface = (
        fonts.option_label_font.render(
            f"Your Rating: "
            f"{state.career_rating:,}",
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
            center=(
                BASE_WIDTH // 2,
                145
            )
        )
    )

    window.game_surface.blit(
        rating_surface,
        rating_rect
    )

    ribbon_image = get_jobfinder_image(
        "ribbon_award.png",
        (
            150,
            210
        )
    )

    if ribbon_image is not None:
        window.game_surface.blit(
            ribbon_image,
            (
                30,
                135
            )
        )

    # ==================================================
    # Job Listings
    # ==================================================

    for job_id, rect in (
        career_job_option_rects.items()
    ):

        job_data = (
            career_names.CAREER_JOBS[
                job_id
            ]
        )

        required_rating = (
            job_data[
                "required_rating"
            ]
        )

        unlocked = (
            state.career_rating
            >= required_rating
        )

        current = (
            state.career_job
            == job_id
        )

        # ----------------------------------------------
        # Background
        # ----------------------------------------------

        if current:
            fill_color = (
                210,
                240,
                210
            )

        elif unlocked:
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
            get_career_job_image(
                job_id,
                (
                    150,
                    112
                )
            )
        )

        text_x = (
            rect.x + 18
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
        # Job Name
        # ----------------------------------------------

        name_surface = (
            ui_text.render_text_fit(
                job_data[
                    "name"
                ],
                fonts.option_label_font,
                rect.right
                - text_x
                - 12,
                (
                    0,
                    0,
                    0
                ),
                minimum_size=18
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
        # Requirement
        # ----------------------------------------------

        if required_rating <= 0:

            requirement_text = (
                "No Rating Required"
            )

        else:

            requirement_text = (
                f"{required_rating:,} Rating"
            )

        requirement_surface = (
            fonts.difficulty_detail_font.render(
                requirement_text,
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        window.game_surface.blit(
            requirement_surface,
            (
                text_x,
                rect.y + 53
            )
        )

        # ----------------------------------------------
        # Pay
        # ----------------------------------------------

        pay_surface = (
            fonts.difficulty_detail_font.render(
                f"${job_data['pay']:,} "
                f"per shift",
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        window.game_surface.blit(
            pay_surface,
            (
                text_x,
                rect.y + 78
            )
        )

        # ----------------------------------------------
        # Status
        # ----------------------------------------------

        if current:
            status_text = "HERE"

        elif unlocked:
            status_text = "APPLY"

        else:
            status_text = "LOCKED"

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
                rect.y + 105
            )
        )

    advice_image = get_jobfinder_image(
        "helpful_advice.png",
        (
            190,
            165
        )
    )

    if advice_image is not None:
        window.game_surface.blit(
            advice_image,
            (
                1090,
                430
            )
        )

    # ==================================================
    # Return
    # ==================================================

    buttons.draw_button(
        web_pages.career_subpage_back_rect,
        "Return to Career"
    )


def add_job_change_news():
    """Report the player's new job in the news, at most once per career day.

    A later switch on the same career day rewrites that day's job story (so it names
    the job the player now has) instead of adding another one."""

    headline = (
        f"{state.player_name.upper()} "
        f"TAKES NEW SIDE JOB"
    )

    body = (
        f"{state.player_name} has accepted work as "
        f"{career_names.get_career_job_name()}. "
        f"Sources close to the situation say "
        f"the decision was largely financial."
    )

    for item in state.career_news_items:
        if (
                item.get("category") == "job"
                and item.get("career_day") == state.career_day
        ):
            item["headline"] = headline
            item["body"] = body
            return

    news_screen.add_career_news(
        headline,
        body,
        "job"
    )


def handle_event(event):
    """Old main-loop event branch for STATE_CAREER_JOBS."""

    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
    ):

        job_clicked = None

        for job_id, state.rect in (
                career_job_option_rects.items()
        ):

            if state.rect.collidepoint(
                    state.game_mouse_pos
            ):
                job_clicked = job_id
                break

        if job_clicked is not None:

            job_data = (
                career_names.CAREER_JOBS[
                    job_clicked
                ]
            )

            required_rating = (
                job_data[
                    "required_rating"
                ]
            )

            if (
                    state.career_rating
                    >= required_rating
            ):
                sounds.audio.play_sound(
                    "button_click"
                )

                old_job = state.career_job

                state.career_job = (
                    job_clicked
                )

                refresh_future_work_tasks()

                if old_job != state.career_job:
                    if state.career_job not in state.career_fan_rewarded_jobs:
                        career_rewards.award_career_fans(
                            fan_bonus_for_job(
                                job_data.get("required_rating", 0),
                                job_data.get("pay", 0)
                            ),
                            f"New job: {job_data.get('name', state.career_job)}"
                        )
                        state.career_fan_rewarded_jobs.add(state.career_job)

                    add_job_change_news()

                career_saving.auto_save_career()

        elif web_pages.career_subpage_back_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.current_state = state_names.STATE_CAREER_HUB


def draw():
    """Old draw-chain branch for STATE_CAREER_JOBS."""

    draw_career_jobs()
