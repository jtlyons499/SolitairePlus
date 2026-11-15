"""Career hub screen: calendar, toolbar, day actions (moved out of legacy.py)."""
from solitaireplus.career.alien_night import STORY as ALIEN_STORY
from solitaireplus.games.solitaire.rules import BASE_HEIGHT
from solitaireplus.games.solitaire.rules import BASE_WIDTH
from solitaireplus.career.case_opening import ITEMS as CASE_ITEMS
from solitaireplus.npc.manager import NPCS
from solitaireplus.career.time_warp import advance_months
from solitaireplus.career.ratings import apply_rating_change
from solitaireplus.career.case_opening import award_earned_trophies
from solitaireplus.career.fans import clamp_fans
import copy
from solitaireplus.career.asset_images import get_career_hub_image
from solitaireplus.games.solitaire import head_to_head_screen
from solitaireplus.career.case_opening import purchase as purchase_loot_case
import pygame
from solitaireplus.career.event_progress import restore_event_progress
from solitaireplus.games.cryptid.collection import reward_battle
from solitaireplus.profile import save_data
from solitaireplus.career.events.press_interview import select_interview
from solitaireplus.career.activities import night_is_valid, start_night
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
news_screen = lazy("solitaireplus.career.news_screen")
leaderboard_engine = lazy("solitaireplus.career.leaderboard_engine")
night = lazy("solitaireplus.career.events.night")
event_screen = lazy("solitaireplus.career.events.event_screen")
case_opening_screen = lazy("solitaireplus.career.case_opening_screen")
career_saving = lazy("solitaireplus.career.career_saving")
career_names = lazy("solitaireplus.career.career_names")
calendar = lazy("solitaireplus.career.calendar")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
ui_text = lazy("solitaireplus.ui.text")
sounds = lazy("solitaireplus.app.sounds")
leveling = lazy("solitaireplus.profile.leveling")
fonts = lazy("solitaireplus.app.fonts")
cursors = lazy("solitaireplus.ui.cursors")
buttons = lazy("solitaireplus.ui.buttons")


def get_career_month_name():
    if (
        1
        <= state.career_month
        <= 12
    ):
        return (
            career_names.CAREER_MONTH_NAMES[
                state.career_month
            ]
        )

    return "Unknown"

def get_career_news_preview(
        count=2
):

    news_screen.ensure_career_news()

    return (
        state.career_news_items[
            :count
        ]
    )

def get_current_career_activity():

    for entry in state.career_current_schedule:

        if (
            isinstance(entry, dict)  # skip a bad (non-dict) day from save data
            and entry.get(
                "day_number"
            )
            == state.career_day_of_month
        ):
            return entry

    return None

def current_career_schedule_entry():
    """Today's calendar entry, career_current_schedule[career_day_of_month - 1].

    None when bad save data leaves no such entry (B20): an empty or short schedule, a day of 0 or
    less (which must not wrap round to the end of the list), or an entry that is not a dict.
    """
    days = state.career_current_schedule
    day = state.career_day_of_month
    if not isinstance(days, list) or not isinstance(day, int) or not 1 <= day <= len(days):
        return None
    entry = days[day - 1]
    return entry if isinstance(entry, dict) else None

def start_career_activity(work=False):
    entry = current_career_schedule_entry()
    if entry is None:
        return  # no calendar entry for today (bad save data): stay on the hub, nothing to start
    alien = entry.get("event_id") == "alien_night"
    kind = "alien" if alien else "bigfoot"
    story = state.career_alien_story if alien else state.career_bigfoot_story
    activity = entry.get("career_activity")
    played = False
    if isinstance(activity, dict):
        # A night already played paid its reward: it is never replaced by a fresh night, so this
        # calendar day can't pay twice. "Played" also counts a result left by choose_option()
        # when the claimed flag itself is damaged, and a played night of the other story.
        played = (bool(activity.get("claimed")) or activity.get("stage") in ("result", "complete")
                  or "result_text" in activity or "cash_change" in activity)
        if not night_is_valid(activity, data=ALIEN_STORY if activity.get("kind") == "alien" else None):
            # A malformed night (B20) the activity screen can't show: a played one stays (and
            # the player stays on the hub); an unplayed one holds nothing, so a fresh night
            # replaces it.
            if played:
                return
            activity = None
    # A missing, malformed or out-of-date unplayed activity is replaced by a fresh night.
    if not isinstance(activity, dict) or (not played and (activity.get("kind") != kind or activity.get("version") != 2)):
        entry["career_activity"] = start_night(story, data=ALIEN_STORY if alien else None)
    state.current_state = state_names.STATE_CAREER_ACTIVITY
    career_saving.auto_save_career()


def complete_career_work_day():

    job_data = career_names.CAREER_JOBS.get(
        state.career_job,
        career_names.CAREER_JOBS[
            "custodian"
        ]
    )

    pay = job_data.get(
        "pay",
        0
    )

    # A pre-removal shift may already have paid out on this calendar entry. A missing day entry or
    # a non-dict activity (bad save data) holds no paid shift, so the work day pays normally.
    entry = current_career_schedule_entry()
    legacy_shift = entry.get("career_activity") if entry is not None else None
    if isinstance(legacy_shift, dict) and legacy_shift.get("kind") == "work" and legacy_shift.get("claimed"):
        pay = 0

    state.career_cash += pay

    calendar.advance_career_day(
        completed=True
    )

    return pay

def skip_career_day():
    calendar.reset_career_hub_runtime()
    calendar.advance_career_day(completed=False)


def skip_to_selected_career_day():
    calendar.ensure_career_schedule()
    skipped = legacy.career_hub_controls.days_to_skip(
        state.career_current_schedule, state.career_day_of_month
    )
    if not skipped:
        return
    calendar.reset_career_hub_runtime()
    # Use the existing calendar bookkeeping, with one save after the whole jump.
    # The selected day stays unplayed. Skipped activities grant no rewards.
    for _ in range(skipped):
        calendar.advance_career_day(completed=False, save_after=False)
    career_saving.auto_save_career()
    legacy.career_hub_controls.show_message(
        f"Skipped {skipped} day{'s' if skipped != 1 else ''}. "
        f"Day {state.career_day_of_month} is ready to play.", pygame.time.get_ticks()
    )


def time_warp_career(months):
    calendar.ensure_career_schedule()
    calendar.reset_career_hub_runtime()
    skipped=advance_months(months,lambda:(state.career_year,state.career_month,state.career_day_of_month),calendar.advance_career_day)
    career_saving.auto_save_career()
    legacy.career_hub_controls.show_message(f"Time Warp: skipped {months} month(s), {skipped} days.",pygame.time.get_ticks(),duration=4000)


def get_ordinal_day(number):
    try:
        number = int(number)
    except (TypeError, ValueError):
        return str(number)

    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def get_career_day_entry(day_number):
    for entry in state.career_current_schedule:
        if entry.get("day_number") == day_number:
            return entry
    return None


def start_career_cases():
    state.current_game_mode = "career"
    award_earned_trophies(state.case_collection_state, state.achievement_state)
    case_opening_screen.case_screen.enter(state.case_collection_state, state.career_cash, buy_case_for_screen, state.career_residence)
    state.current_state = state_names.STATE_CASE_OPENING


def buy_case_for_screen(case_id):
    if state.current_game_mode == "free":
        return purchase_loot_case(case_opening_screen.case_screen.state, case_id, case_opening_screen.case_screen.wallet)
    previous = (
        copy.deepcopy(state.case_collection_state),
        state.career_cash,
        copy.deepcopy(state.career_ratings),
        state.career_rating,
        state.career_fans,
        set(state.unlocked_menu_backgrounds),
        set(state.unlocked_felts),
        set(state.unlocked_titles),
        set(cursors.unlocked_cursors),
    )
    try:
        receipt, state.career_cash = purchase_loot_case(
            state.case_collection_state,
            case_id,
            state.career_cash,
            fans=state.career_fans,
        )
        if receipt["kind"] == "rating":
            receipt["amount"] = apply_rating_change(state.career_ratings, receipt["game"], receipt["amount"])
            state.career_rating = state.career_ratings["overall"]
        elif receipt["kind"] == "fans":
            actual = clamp_fans(state.career_fans + receipt["amount"])
            receipt["amount"] = actual - state.career_fans
            state.career_fans = actual
        elif receipt["kind"] == "cosmetic":
            from solitaireplus.profile.cosmetics import unlock_reward
            item = CASE_ITEMS[receipt["item_id"]]
            unlock_reward(
                item.get("cosmetic_type"),
                item.get("asset_id"),
                state.unlocked_menu_backgrounds,
                state.unlocked_felts,
                state.unlocked_titles,
                cursors.unlocked_cursors,
            )
        career_saving.auto_save_career()
        return receipt, state.career_cash
    except Exception:
        (
            old_state,
            state.career_cash,
            old_ratings,
            state.career_rating,
            state.career_fans,
            old_backgrounds,
            old_felts,
            old_titles,
            old_cursors,
        ) = previous
        state.case_collection_state.clear(); state.case_collection_state.update(old_state)
        state.career_ratings.clear(); state.career_ratings.update(old_ratings)
        state.unlocked_menu_backgrounds.clear(); state.unlocked_menu_backgrounds.update(old_backgrounds)
        state.unlocked_felts.clear(); state.unlocked_felts.update(old_felts)
        state.unlocked_titles.clear(); state.unlocked_titles.update(old_titles)
        cursors.unlocked_cursors.clear(); cursors.unlocked_cursors.update(old_cursors)
        raise


def start_career_cryptid():
    state.current_game_mode='career'
    legacy.cryptid_screen.enter_career(NPCS,state.cryptid_collection_state,career_saving.auto_save_career,settle_career_cryptid,
                                temporary=legacy.game_namespace().get("guest_mode",False) or legacy.game_namespace().get("current_profile_slot",1) is None)
    state.current_state=state_names.STATE_CRYPTID_CREATURES


def settle_career_cryptid(serial,winner):
    previous=copy.deepcopy(state.cryptid_collection_state)
    previous_progress=(state.player_xp,state.player_level,state.player_xp_to_next,list(state.level_up_queue))
    previous_cosmetics={name:set(legacy.game_namespace()[name]) for name in ('unlocked_menu_backgrounds','unlocked_felts','unlocked_titles') if name in legacy.game_namespace()}
    try:
        result=reward_battle(state.cryptid_collection_state,serial,winner)
        if result:
            progression=leveling.add_player_xp(result['xp'])
            state.level_up_queue.extend(progression['level_up_screens'])
            career_saving.auto_save_career()
        return result
    except OSError:
        state.cryptid_collection_state.clear();state.cryptid_collection_state.update(previous)
        state.player_xp,state.player_level,state.player_xp_to_next,queued=previous_progress
        state.level_up_queue[:]=queued
        for name,values in previous_cosmetics.items():
            legacy.game_namespace()[name].clear();legacy.game_namespace()[name].update(values)
        raise


def begin_career_profile_switch():
    if not career_saving.save_career_from_hub():
        return
    # A snapshot lets Back restore even a guest or an abandoned empty slot.
    state.profile_switch_snapshot = (
        state.current_profile_slot, state.guest_mode, copy.deepcopy(save_data.build_profile_save_data())
    )
    state.profile_select_return_state = state_names.STATE_CAREER_HUB
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

career_fast_skip_yes_rect = pygame.Rect(
    505,
    438,
    160,
    48
)

career_fast_skip_no_rect = pygame.Rect(
    700,
    438,
    160,
    48
)


def draw_career_hub():

    # ==================================================
    # SHARED PAGE GEOMETRY
    # ==================================================

    center_x = 320
    center_width = 846

    calendar_rect = pygame.Rect(
        center_x,
        144,
        center_width,
        555
    )
    # ==================================================
    # PAGE BACKGROUND
    # ==================================================

    window.game_surface.fill(
        (
            245,
            245,
            245
        )
    )

    # ==================================================
    # Career Website Banner
    # ==================================================

    career_header = (
        get_career_hub_image(
            "career_header.png",
            (
                848,
                56
            )
        )
    )

    if career_header is not None:
        window.game_surface.blit(
            career_header,
            (
                320,
                0
            )
        )

    career_url_surface = (
        fonts.option_value_font.render(
            "https://www.mysolitairecareer.weebly.biz",
            True,
            (
                0,
                0,
                0
            )
        )
    )

    window.game_surface.blit(
        career_url_surface,
        (
            625,
            20
        )
    )


    # ==================================================
    # LEFT COLUMN
    # ==================================================

    left_column_rect = pygame.Rect(
        0,
        0,
        320,
        768
    )

    pygame.draw.rect(
        window.game_surface,
        (
            250,
            250,
            250
        ),
        left_column_rect
    )

    pygame.draw.rect(
        window.game_surface,
        (
            0,
            0,
            0
        ),
        left_column_rect,
        3
    )

    counter_image = get_career_hub_image(
        "visitor_counter.png",
        (
            140,
            32
        )
    )

    if counter_image is not None:
        window.game_surface.blit(
            counter_image,
            (
                18,
                742
            )
        )

    best_viewed_image = get_career_hub_image(
        "best_viewed_1080p.png",
        (
            120,
            31
        )
    )

    award_image = get_career_hub_image(
        "web_award.png",
        (
            88,
            31
        )
    )

    if best_viewed_image is not None:
        window.game_surface.blit(
            best_viewed_image,
            (
                center_x + 15,
                105
            )
        )

    if award_image is not None:
        window.game_surface.blit(
            award_image,
            (
                center_x + 145,
                105
            )
        )

    # Avatar panel

    avatar_panel_rect = pygame.Rect(
        18,
        18,
        285,
        235
    )

    pygame.draw.rect(
        window.game_surface,
        (
            210,
            210,
            210
        ),
        avatar_panel_rect
    )

    pygame.draw.rect(
        window.game_surface,
        (
            0,
            0,
            0
        ),
        avatar_panel_rect,
        2
    )

    avatar = legacy.get_profile_avatar()

    avatar_preview = pygame.transform.smoothscale(
        avatar,
        (
            190,
            228
        )
    )

    avatar_preview_rect = avatar_preview.get_rect(
        center=avatar_panel_rect.center
    )

    window.game_surface.blit(
        avatar_preview,
        avatar_preview_rect
    )

    # Name

    name_surface = fonts.option_label_font.render(
        state.player_name,
        True,
        (
            0,
            0,
            0
        )
    )

    name_rect = name_surface.get_rect(
        center=(
            160,
            272
        )
    )

    window.game_surface.blit(
        name_surface,
        name_rect
    )

    # Level / XP

    level_surface = fonts.option_value_font.render(
        f"Level: {state.player_level}",
        True,
        (
            0,
            0,
            0
        )
    )

    window.game_surface.blit(
        level_surface,
        (
            18,
            300
        )
    )

    if state.player_xp_to_next is not None:
        xp_text = (
            f"XP: {state.player_xp:,} / "
            f"{state.player_xp_to_next:,}"
        )
    else:
        xp_text = (
            f"XP: {state.player_xp:,} / MAX"
        )

    xp_surface = fonts.option_value_font.render(
        xp_text,
        True,
        (
            0,
            0,
            0
        )
    )

    window.game_surface.blit(
        xp_surface,
        (
            18,
            330
        )
    )

    # Career progress panel

    career_panel_rect = pygame.Rect(
        0,
        365,
        320,
        250
    )

    pygame.draw.rect(
        window.game_surface,
        (
            255,
            255,
            255
        ),
        career_panel_rect
    )

    pygame.draw.rect(
        window.game_surface,
        (
            220,
            0,
            0
        ),
        career_panel_rect,
        5
    )

    career_heading = fonts.option_label_font.render(
        "CAREER PROGRESS",
        True,
        (
            0,
            0,
            0
        )
    )

    career_heading_rect = career_heading.get_rect(
        center=(
            career_panel_rect.centerx,
            career_panel_rect.y + 28
        )
    )

    window.game_surface.blit(
        career_heading,
        career_heading_rect
    )

    career_lines = [
        f"Global Rating: {state.career_rating:,}",
        f"Global Rank: #{leaderboard_engine.get_player_leaderboard_rank()}",
        f"Cash: ${state.career_cash:,}",
        f"Career Day: {state.career_day:,}",
        f"Residence: {career_names.get_career_residence_name()}",
        f"Fans: {state.career_fans:,}",
        f"Side Job: {career_names.get_career_job_name()}",
    ]

    career_stat_icons = {
        0: "icon_rating.png",
        1: "icon_leaderboard.png",
        2: "icon_cash.png",
        3: "icon_day.png",
        4: "icon_residence.png",
        5: "icon_fans.png",
        6: "icon_job.png",
    }

    for index, line_text in enumerate(
            career_lines
    ):

        line_y = (
                career_panel_rect.y
                + 58
                + index * 25
        )

        icon_filename = (
            career_stat_icons.get(
                index
            )
        )

        text_x = (
                career_panel_rect.x + 18
        )

        if icon_filename:

            icon = (
                get_career_hub_image(
                    icon_filename,
                    (
                        24,
                        24
                    )
                )
            )

            if icon is not None:
                window.game_surface.blit(
                    icon,
                    (
                        career_panel_rect.x + 10,
                        line_y - 2
                    )
                )

                text_x = (
                        career_panel_rect.x + 40
                )

        line_surface = (
            fonts.difficulty_detail_font.render(
                line_text,
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        window.game_surface.blit(
            line_surface,
            (
                text_x,
                line_y
            )
        )

    # Statistics panel

    stats_panel_rect = pygame.Rect(
        0,
        615,
        320,
        153
    )

    pygame.draw.rect(
        window.game_surface,
        (
            255,
            255,
            255
        ),
        stats_panel_rect
    )

    pygame.draw.rect(
        window.game_surface,
        (
            20,
            60,
            220
        ),
        stats_panel_rect,
        5
    )

    stats_heading = fonts.option_label_font.render(
        "STATISTICS",
        True,
        (
            0,
            0,
            0
        )
    )

    stats_heading_rect = stats_heading.get_rect(
        center=(
            stats_panel_rect.centerx,
            stats_panel_rect.y + 25
        )
    )

    window.game_surface.blit(
        stats_heading,
        stats_heading_rect
    )

    stats_lines = [
        f"Rounds Won: {state.career_rounds_won:,}",
        f"Challenges Won: {state.career_challenges_won:,}",
        f"Total Moves: {state.career_total_moves:,}",
    ]

    for index, text in enumerate(
        stats_lines
    ):
        line = fonts.option_value_font.render(
            text,
            True,
            (
                0,
                0,
                0
            )
        )

        window.game_surface.blit(
            line,
            (
                18,
                stats_panel_rect.y
                + 52
                + index * 26
            )
        )


    # ==================================================
    # CENTER CALENDAR AREA
    # ==================================================

    date_header_rect = pygame.Rect(
        center_x,
        64,
        center_width,
        80
    )

    pygame.draw.rect(
        window.game_surface,
        (
            250,
            250,
            250
        ),
        date_header_rect
    )

    date_title = ui_text.get_font(
        None,
        58,
        sysfont=True
    ).render(
        f"{get_career_month_name()} {state.career_year}",
        True,
        (
            0,
            0,
            0
        )
    )

    date_title_rect = date_title.get_rect(
        center=(date_header_rect.centerx, 91)
    )

    window.game_surface.blit(
        date_title,
        date_title_rect
    )

    calendar_half_text = (
        "Days 1-15"
        if state.career_day_of_month <= 15
        else "Days 16-30"
    )
    calendar_status_surface = fonts.difficulty_detail_font.render(
        f"{calendar_half_text}   |   Last updated: Career Day {state.career_day}",
        True,
        (80, 80, 80)
    )
    window.game_surface.blit(
        calendar_status_surface,
        calendar_status_surface.get_rect(
            center=(date_header_rect.centerx, 129)
        )
    )


    pygame.draw.rect(
        window.game_surface,
        (
            252,
            252,
            252
        ),
        calendar_rect
    )

    pygame.draw.rect(
        window.game_surface,
        (
            0,
            0,
            0
        ),
        calendar_rect,
        2
    )

    badge_image = get_career_hub_image(
        "career_central_badge.png",
        (
            140,
            36
        )
    )

    if badge_image is not None:
        window.game_surface.blit(
            badge_image,
            (
                center_x + 8,
                101
            )
        )

    calendar.ensure_career_schedule()
    leaderboard_engine.ensure_career_leaderboard()
    news_screen.ensure_career_news()

    columns = 5
    rows = 3

    cell_width = (
            calendar_rect.width
            // columns
    )

    cell_height = (
            calendar_rect.height
            // rows
    )

    calendar_page_start = 0 if state.career_day_of_month <= 15 else 15
    calendar_page_entries = state.career_current_schedule[
        calendar_page_start:calendar_page_start + 15
    ]

    legacy.career_hub_controls.begin_calendar(
        state.career_current_schedule,
        state.career_day_of_month
    )

    # Reset these every frame.
    state.career_calendar_action_rect = pygame.Rect(
        0,
        0,
        0,
        0
    )

    state.career_calendar_skip_rect = pygame.Rect(
        0,
        0,
        0,
        0
    )

    for schedule_index, entry in enumerate(
            calendar_page_entries
    ):

        row = (
                schedule_index
                // columns
        )

        column = (
                schedule_index
                % columns
        )

        cell_rect = pygame.Rect(
            calendar_rect.x
            + column * cell_width,

            calendar_rect.y
            + row * cell_height,

            cell_width,
            cell_height
        )

        # ==================================================
        # Determine state of day
        # ==================================================

        is_current_day = (
                entry[
                    "day_number"
                ]
                == state.career_day_of_month
        )

        is_past_day = (
                entry[
                    "day_number"
                ]
                < state.career_day_of_month
        )

        # ==================================================
        # Cell background
        # ==================================================

        if is_current_day:
            cell_fill = (
                255,
                248,
                220
            )

        elif is_past_day:
            cell_fill = (
                225,
                225,
                225
            )

        else:
            cell_fill = (
                250,
                250,
                250
            )

        pygame.draw.rect(
            window.game_surface,
            cell_fill,
            cell_rect
        )

        legacy.career_hub_controls.register_day(entry["day_number"], cell_rect)
        if legacy.career_hub_controls.selected_day == entry["day_number"]:
            cell_fill = (220, 238, 255)
            pygame.draw.rect(window.game_surface, cell_fill, cell_rect)

        # Current day gets a red outline like
        # your Photoshop mock-up.
        border_color = (
            (220, 0, 0)
            if is_current_day
            else (35, 110, 190)
            if legacy.career_hub_controls.selected_day == entry["day_number"]
            else (0, 0, 0)
        )

        border_width = (
            4
            if is_current_day
            else 2
        )

        pygame.draw.rect(
            window.game_surface,
            border_color,
            cell_rect,
            border_width
        )

        # ==================================================
        # Header
        # ==================================================

        weekday_name = (
            calendar.CAREER_WEEKDAY_NAMES[
                entry[
                    "weekday_index"
                ]
            ]
        )

        weekday_surface = (
            fonts.difficulty_detail_font.render(
                weekday_name,
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        window.game_surface.blit(
            weekday_surface,
            (
                cell_rect.x + 8,
                cell_rect.y + 6
            )
        )

        day_surface = (
            fonts.option_label_font.render(
                str(
                    entry[
                        "day_number"
                    ]
                ),
                True,
                (
                    220,
                    0,
                    40
                )
            )
        )

        day_rect = (
            day_surface.get_rect(
                top=cell_rect.y + 2,
                right=cell_rect.right - 8
            )
        )

        window.game_surface.blit(
            day_surface,
            day_rect
        )

        # Header divider
        pygame.draw.line(
            window.game_surface,
            (
                0,
                0,
                0
            ),
            (
                cell_rect.x,
                cell_rect.y + 34
            ),
            (
                cell_rect.right,
                cell_rect.y + 34
            ),
            2
        )

        # Future days get a one-click fast-forward shortcut. The whole square
        # still supports the existing select + toolbar flow.
        if not is_current_day and not is_past_day:
            fast_skip_rect = pygame.Rect(
                cell_rect.right - 34,
                cell_rect.bottom - 30,
                24,
                20
            )
            legacy.career_hub_controls.register_fast_skip(
                entry["day_number"],
                fast_skip_rect
            )

            hovered_fast = (
                state.game_mouse_pos is not None
                and fast_skip_rect.collidepoint(state.game_mouse_pos)
            )
            pygame.draw.rect(
                window.game_surface,
                (210, 228, 246) if hovered_fast else (232, 239, 246),
                fast_skip_rect,
                border_radius=4
            )
            pygame.draw.rect(
                window.game_surface,
                (35, 90, 150),
                fast_skip_rect,
                1,
                border_radius=4
            )

            triangle_y = fast_skip_rect.centery
            for triangle_x in (fast_skip_rect.x + 6, fast_skip_rect.x + 12):
                pygame.draw.polygon(
                    window.game_surface,
                    (35, 90, 150),
                    [
                        (triangle_x, triangle_y - 5),
                        (triangle_x, triangle_y + 5),
                        (triangle_x + 6, triangle_y),
                    ]
                )

        # ==================================================
        # Past days
        # ==================================================

        if is_past_day:

            history_entry = None

            for history_item in state.career_completed_days:
                if (
                        history_item.get(
                            "year"
                        )
                        == state.career_year
                        and history_item.get(
                    "month"
                )
                        == state.career_month
                        and history_item.get(
                    "day"
                )
                        == entry[
                    "day_number"
                ]
                ):
                    history_entry = (
                        history_item
                    )

                    break

            if (
                    history_entry is not None
                    and not history_entry.get(
                "completed",
                True
            )
            ):
                status_text = "Skipped"

            else:
                status_text = "Completed"

            completed_surface = (
                fonts.difficulty_detail_font.render(
                    status_text,
                    True,
                    (
                        100,
                        100,
                        100
                    )
                )
            )

            completed_rect = (
                completed_surface.get_rect(
                    center=(
                        cell_rect.centerx,
                        cell_rect.centery
                    )
                )
            )

            window.game_surface.blit(
                completed_surface,
                completed_rect
            )

            continue

        # ==================================================
        # Activity title
        # ==================================================

        activity_type = entry[
            "activity_type"
        ]

        activity_title = entry.get(
            "title",
            ""
        )

        activity_icon_map = {
            night.CAREER_ACTIVITY_ROUND:
                "icon_round.png",

            night.CAREER_ACTIVITY_WORK:
                "icon_work.png",

            night.CAREER_ACTIVITY_CHALLENGE:
                "icon_challenge.png",

            night.CAREER_ACTIVITY_EVENT:
                "icon_event.png",

        }

        activity_icon_name = (
            activity_icon_map.get(
                activity_type
            )
        )

        if activity_icon_name:

            activity_icon = (
                get_career_hub_image(
                    activity_icon_name,
                    (
                        26,
                        26
                    )
                )
            )

            if activity_icon is not None:
                window.game_surface.blit(
                    activity_icon,
                    (
                        cell_rect.x + 10,
                        cell_rect.y + 38
                    )
                )


        # ----------------------------------------------
        # Challenge
        # ----------------------------------------------

        if (
                activity_type
                == night.CAREER_ACTIVITY_CHALLENGE
        ):
            line_1 = "Challenge Round:"

            line_2 = entry.get(
                "challenge_name",
                ""
            )

            title_surface = (
                fonts.difficulty_detail_font.render(
                    line_1,
                    True,
                    (
                        0,
                        0,
                        0
                    )
                )
            )

            title_rect = (
                title_surface.get_rect(
                    center=(
                        cell_rect.centerx,
                        cell_rect.y + 52
                    )
                )
            )

            window.game_surface.blit(
                title_surface,
                title_rect
            )

            challenge_surface = (
                fonts.option_label_font.render(
                    line_2,
                    True,
                    (
                        0,
                        0,
                        0
                    )
                )
            )

            challenge_rect = (
                challenge_surface.get_rect(
                    center=(
                        cell_rect.centerx,
                        cell_rect.y + 78
                    )
                )
            )

            window.game_surface.blit(
                challenge_surface,
                challenge_rect
            )

        # ----------------------------------------------
        # Everything else
        # ----------------------------------------------

        else:
            words = activity_title.split()
            if activity_title == "Head-to-Head":
                words = ["Head-to-", "Head"]
            title_lines = ["Head-to-", "Head"] if activity_title == "Head-to-Head" else [activity_title]

            if fonts.option_label_font.size(activity_title)[0] > cell_rect.width - 18 and len(words) > 1:
                best_split = 1
                best_width = 10 ** 9
                for split_index in range(1, len(words)):
                    line_a = " ".join(words[:split_index])
                    line_b = " ".join(words[split_index:])
                    candidate_width = max(
                        fonts.option_label_font.size(line_a)[0],
                        fonts.option_label_font.size(line_b)[0]
                    )
                    if candidate_width < best_width:
                        best_width = candidate_width
                        best_split = split_index
                title_lines = [
                    " ".join(words[:best_split]),
                    " ".join(words[best_split:]),
                ]

            base_y = cell_rect.y + (70 if len(title_lines) == 2 else 82)
            for line_index, title_line in enumerate(title_lines):
                activity_surface = ui_text.render_text_fit(
                    title_line,
                    fonts.option_label_font,
                    cell_rect.width - 18,
                    (0, 0, 0),
                    minimum_size=18
                )
                activity_rect = activity_surface.get_rect(
                    center=(
                        cell_rect.centerx,
                        base_y + line_index * 24
                    )
                )
                window.game_surface.blit(activity_surface, activity_rect)

        # ==================================================
        # Only current day has buttons
        # ==================================================

        if is_current_day:

            state.career_calendar_action_rect = (
                pygame.Rect(
                    cell_rect.x + 12,
                    cell_rect.bottom - 78,
                    cell_rect.width - 24,
                    34
                )
            )

            state.career_calendar_skip_rect = (
                pygame.Rect(
                    cell_rect.x + 12,
                    cell_rect.bottom - 38,
                    cell_rect.width - 24,
                    28
                )
            )

            # ----------------------------------------------
            # Action button label
            # ----------------------------------------------

            if (
                    activity_type
                    == night.CAREER_ACTIVITY_ROUND
            ):
                action_text = "Play Solitaire"

            elif (
                    activity_type
                    == night.CAREER_ACTIVITY_WORK
            ):
                action_text = "Go to Work"

            elif (
                    activity_type
                    == night.CAREER_ACTIVITY_CHALLENGE
            ):
                action_text = "Play Challenge"


            elif (
                    activity_type
                    == night.CAREER_ACTIVITY_EVENT

            ):
                action_text = "View Event"


            elif activity_type in (

                    night.CAREER_ACTIVITY_CASUAL_CARDS,
                    night.CAREER_ACTIVITY_POKER_NIGHT,
                    night.CAREER_ACTIVITY_CASINO_NIGHT,
                    night.CAREER_ACTIVITY_NICHE_NIGHT,
                    night.CAREER_ACTIVITY_ARCADE_NIGHT

            ):

                action_text = "Play"


            else:
                action_text = "Continue"

            buttons.draw_button(
                state.career_calendar_action_rect,
                action_text,
                font=fonts.difficulty_detail_font
            )

            buttons.draw_button(
                state.career_calendar_skip_rect,
                "Skip Day",
                font=fonts.difficulty_detail_font
            )

    # ==================================================
    # RIGHT COLUMN
    # ==================================================

    right_x = 1166
    right_width = 200

    leaderboard_rect = pygame.Rect(
        right_x,
        0,
        right_width,
        410
    )

    pygame.draw.rect(
        window.game_surface,
        (
            250,
            250,
            250
        ),
        leaderboard_rect
    )

    pygame.draw.rect(
        window.game_surface,
        (
            0,
            0,
            0
        ),
        leaderboard_rect,
        3
    )

    top10_header = (
        get_career_hub_image(
            "top10_header.png",
            (
                180,
                38
            )
        )
    )

    if top10_header is not None:

        top10_header_rect = (
            top10_header.get_rect(
                center=(
                    leaderboard_rect.centerx,
                    leaderboard_rect.y + 24
                )
            )
        )

        window.game_surface.blit(
            top10_header,
            top10_header_rect
        )

    else:

        fallback_surface = (
            fonts.option_label_font.render(
                "TOP 10",
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        fallback_rect = (
            fallback_surface.get_rect(
                center=(
                    leaderboard_rect.centerx,
                    leaderboard_rect.y + 24
                )
            )
        )

        window.game_surface.blit(
            fallback_surface,
            fallback_rect
        )

    leaderboard_preview = (
        leaderboard_engine.get_career_leaderboard()[
            :10
        ]
    )

    for index, entry in enumerate(
            leaderboard_preview
    ):
        text = (
            f"{index + 1}. "
            f"{entry['name']}"
        )

        line = (
            fonts.difficulty_detail_font.render(
                text,
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        window.game_surface.blit(
            line,
            (
                right_x + 10,
                52 + index * 23
            )
        )

    buttons.draw_button(
        state.career_leaderboards_rect,
        "View Leaderboards"
    )

    news_rect = pygame.Rect(
        right_x,
        350,
        right_width,
        350
    )

    pygame.draw.rect(
        window.game_surface,
        (
            245,
            241,
            222
        ),
        news_rect
    )

    pygame.draw.rect(
        window.game_surface,
        (
            0,
            0,
            0
        ),
        news_rect,
        3
    )

    courrier_preview = (
        get_career_hub_image(
            "courrier_preview.png",
            (
                185,
                40
            )
        )
    )

    if courrier_preview is not None:

        courrier_preview_rect = (
            courrier_preview.get_rect(
                center=(
                    news_rect.centerx,
                    news_rect.y + 28
                )
            )
        )

        window.game_surface.blit(
            courrier_preview,
            courrier_preview_rect
        )

    else:

        fallback_title = (
            fonts.option_label_font.render(
                "THE CARDED COURRIER",
                True,
                (
                    0,
                    0,
                    0
                )
            )
        )

        fallback_rect = (
            fallback_title.get_rect(
                center=(
                    news_rect.centerx,
                    news_rect.y + 28
                )
            )
        )

        window.game_surface.blit(
            fallback_title,
            fallback_rect
        )

    pygame.draw.line(
        window.game_surface,
        (
            0,
            0,
            0
        ),
        (
            news_rect.x + 12,
            news_rect.y + 52
        ),
        (
            news_rect.right - 12,
            news_rect.y + 52
        ),
        2
    )

    # ==================================================
    # Newspaper Preview
    # ==================================================

    news_preview = (
        get_career_news_preview(
            1
        )
    )

    preview_y = (
            news_rect.y + 68
    )

    for item in news_preview:
        # ----------------------------------------------
        # Headline
        # ----------------------------------------------

        headline = (
            item.get(
                "headline",
                "UNTITLED STORY"
            )
        )

        headline_rect = pygame.Rect(
            news_rect.x + 12,
            preview_y,
            news_rect.width - 24,
            70
        )

        ui_text.draw_wrapped_text(
            headline,
            fonts.difficulty_detail_font,
            (
                0,
                0,
                0
            ),
            headline_rect,
            line_spacing=3
        )

        preview_y += 72

        # ----------------------------------------------
        # Date
        # ----------------------------------------------

        date_surface = (
            fonts.difficulty_detail_font.render(
                news_screen.get_career_news_date(
                    item
                ),
                True,
                (
                    100,
                    100,
                    100
                )
            )
        )

        window.game_surface.blit(
            date_surface,
            (
                news_rect.x + 12,
                preview_y
            )
        )

        preview_y += 34

        # ----------------------------------------------
        # Body preview
        # ----------------------------------------------

        body_preview = (
            item.get(
                "body",
                ""
            )
        )

        ui_text.draw_wrapped_text_limited(
            body_preview,
            fonts.ui_small_font,
            (
                40,
                40,
                40
            ),
            pygame.Rect(
                news_rect.x + 12,
                preview_y,
                news_rect.width - 24,
                100
            ),
            max_lines=4,
            line_spacing=2
        )

    buttons.draw_button(
        state.career_news_rect,
        "View Newspaper"
    )

    ui_text.draw_wrapped_text_limited(
        body_preview,
        fonts.ui_small_font,
        (
            40,
            40,
            40
        ),
        pygame.Rect(
            news_rect.x + 12,
            preview_y,
            news_rect.width - 24,
            100
        ),
        max_lines=4,
        line_spacing=2
    )

    # ==================================================
    # BOTTOM WEBSITE LINKS
    # ==================================================

    bottom_bar_rect = pygame.Rect(
        center_x,
        699,
        center_width,
        69
    )

    pygame.draw.rect(
        window.game_surface,
        (
            220,
            230,
            240
        ),
        bottom_bar_rect
    )

    pygame.draw.rect(
        window.game_surface,
        (
            0,
            0,
            0
        ),
        bottom_bar_rect,
        2
    )

    buttons.draw_button(
        state.career_real_estate_rect,
        "Visit RealEstate.apt",
        font=fonts.difficulty_detail_font
    )

    buttons.draw_button(
        state.career_jobs_rect,
        "Visit JimbosJobFinder.sk",
        font=fonts.difficulty_detail_font
    )

    legacy.career_hub_controls.draw_time_warp(window.game_surface,date_header_rect,buttons.draw_button,legacy.career_hub_controls.font)

    legacy.career_hub_controls.draw_toolbar(
        window.game_surface, buttons.draw_button, legacy.career_hub_controls.font, pygame.time.get_ticks()
    )

    buttons.draw_button(
        state.career_back_rect,
        "Exit Career"
    )

    # ==================================================
    # FAST-SKIP CONFIRMATION
    # ==================================================

    if legacy.career_hub_controls.confirm_skip_day is not None:
        confirm_day = legacy.career_hub_controls.confirm_skip_day
        confirm_entry = get_career_day_entry(confirm_day)
        if confirm_entry is not None:
            weekday = calendar.CAREER_WEEKDAY_NAMES[
                confirm_entry.get("weekday_index", 0)
            ]
            day_label = get_ordinal_day(confirm_day)
        else:
            weekday = "that day"
            day_label = str(confirm_day)

        overlay = pygame.Surface(
            (BASE_WIDTH, BASE_HEIGHT),
            pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 118))
        window.game_surface.blit(overlay, (0, 0))

        confirm_rect = pygame.Rect(390, 300, 586, 230)
        pygame.draw.rect(
            window.game_surface,
            (248, 248, 244),
            confirm_rect,
            border_radius=12
        )
        pygame.draw.rect(
            window.game_surface,
            (35, 90, 150),
            confirm_rect,
            3,
            border_radius=12
        )

        confirm_title = fonts.option_label_font.render(
            f"Skip ahead to {weekday} the {day_label}?",
            True,
            (20, 30, 38)
        )
        window.game_surface.blit(
            confirm_title,
            confirm_title.get_rect(center=(confirm_rect.centerx, 345))
        )

        confirm_detail = fonts.difficulty_detail_font.render(
            "All earlier days will be marked skipped and grant no rewards.",
            True,
            (70, 78, 84)
        )
        window.game_surface.blit(
            confirm_detail,
            confirm_detail.get_rect(center=(confirm_rect.centerx, 390))
        )

        buttons.draw_button(
            career_fast_skip_yes_rect,
            "Yes, Skip Ahead",
            font=fonts.difficulty_detail_font
        )
        buttons.draw_button(
            career_fast_skip_no_rect,
            "Cancel",
            font=fonts.difficulty_detail_font
        )



def start_press_interview_event():
    state.career_interview_questions = select_interview(state.career_interview_recent_ids)
    state.career_interview_recent_ids = (state.career_interview_recent_ids + [q['id'] for q in state.career_interview_questions])[-12:]
    state.career_interview_index = 0
    state.career_interview_media_heat = 0
    state.career_interview_fan_change = 0
    state.career_interview_feedback = "The cameras are rolling."



def start_sign_autographs_event():

    event_screen.career_autograph_event.start()
    state.career_autograph_fan_change = 0
    state.career_autograph_last_change = 0
    state.career_event_has_activity = False


def handle_event(event):
    """Old main-loop event branch for STATE_CAREER_HUB."""

    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
    ):

        if legacy.career_hub_controls.confirm_skip_day is not None:
            if career_fast_skip_yes_rect.collidepoint(state.game_mouse_pos):
                sounds.audio.play_sound("button_click")
                target_day = legacy.career_hub_controls.confirm_skip_day
                legacy.career_hub_controls.selected_day = target_day
                legacy.career_hub_controls.clear_skip_confirmation()
                skip_to_selected_career_day()
            elif career_fast_skip_no_rect.collidepoint(state.game_mouse_pos):
                sounds.audio.play_sound("button_click")
                legacy.career_hub_controls.clear_skip_confirmation()
            return

        fast_skip_day = (None if legacy.career_hub_controls.warp_open else legacy.career_hub_controls.request_fast_skip_at(
            state.game_mouse_pos
        ))
        if fast_skip_day is not None:
            sounds.audio.play_sound("button_click")
            return

        hub_action = legacy.career_hub_controls.get_action(state.game_mouse_pos)
        if hub_action is not None:
            sounds.audio.play_sound("button_click")
            if hub_action.startswith("warp:"):
                time_warp_career(int(hub_action.split(":")[1]))
            elif hub_action == "skip_to_day":
                skip_to_selected_career_day()
            elif hub_action == "save":
                career_saving.save_career_from_hub()
            elif hub_action == "switch":
                begin_career_profile_switch()
            elif hub_action == "cases":
                start_career_cases()
            elif hub_action == "cryptid":
                start_career_cryptid()
            elif hub_action == "profile":
                state.profile_return_state = state_names.STATE_CAREER_HUB
                state.profile_name_text = state.player_name
                state.profile_name_active = False
                state.profile_country_active = False
                state.profile_age_active = False
                state.profile_hometown_active = False
                state.profile_bio_active = False
                state.gender_dropdown_open = False
                state.favorite_suit_dropdown_open = False
                state.profile_message = ""
                state.current_state = state_names.STATE_PROFILE
            elif hub_action == "options":
                state.options_return_state = state_names.STATE_CAREER_HUB
                state.current_state = state_names.STATE_OPTIONS
            elif hub_action == "customize":
                state.customize_return_state = state_names.STATE_CAREER_HUB
                state.customize_category = legacy.CUSTOMIZE_BACKGROUNDS
                state.customize_page = 0
                state.current_state = state_names.STATE_CUSTOMIZE
            return
        if legacy.career_hub_controls.select_day_at(state.game_mouse_pos):
            sounds.audio.play_sound("button_click")
            return

        if state.career_calendar_action_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            current_activity = (
                get_current_career_activity()
            )

            if current_activity is not None:

                activity_type = (
                    current_activity.get(  # a day without one (bad save data) matches no branch
                        "activity_type"
                    )
                )

                if (
                        activity_type
                        == night.CAREER_ACTIVITY_ROUND
                ):
                    state.pending_career_activity_index = (
                        legacy.get_current_career_activity_index()
                    )

                    state.pending_career_activity_type = night.CAREER_ACTIVITY_ROUND

                    state.pending_career_challenge_id = None

                    state.current_game_mode = (
                        "career"
                    )

                    legacy.game.clear_challenge()

                    state.current_state = state_names.STATE_DIFFICULTY

                # ----------------------------
                # Challenge
                # ----------------------------

                elif (
                        activity_type
                        == night.CAREER_ACTIVITY_CHALLENGE
                ):
                    state.pending_career_activity_index = (
                        legacy.get_current_career_activity_index()
                    )

                    state.pending_career_activity_type = night.CAREER_ACTIVITY_CHALLENGE

                    state.pending_career_challenge_id = (
                        current_activity.get(
                            "challenge_id"
                        )
                    )

                    state.current_game_mode = (
                        "career"
                    )

                    legacy.game.set_challenge(
                        state.pending_career_challenge_id
                    )

                    legacy.game.new_game()

                    state.current_state = state_names.STATE_PLAYING

                # ----------------------------
                # Training
                # ----------------------------

                elif activity_type in (
                        night.CAREER_ACTIVITY_CASUAL_CARDS,
                        night.CAREER_ACTIVITY_POKER_NIGHT,
                        night.CAREER_ACTIVITY_CASINO_NIGHT,
                        night.CAREER_ACTIVITY_NICHE_NIGHT,
                        night.CAREER_ACTIVITY_ARCADE_NIGHT
                ):

                    entry = current_career_schedule_entry()

                    # No calendar entry for today (bad save data): stay on the hub.
                    if entry is not None:
                        state.career_event_entry = entry

                        if not restore_event_progress(state.career_event_entry, legacy.game_namespace()):
                            state.career_event_has_activity = False
                            night.reset_career_event_result_log()
                            night.reset_career_event_session_totals(activity_type)

                        state.current_state = state_names.STATE_CAREER_EVENT_SELECT

                # ----------------------------
                # Work
                # ----------------------------

                elif (
                        activity_type
                        == night.CAREER_ACTIVITY_WORK

                ):

                    complete_career_work_day()

                # ----------------------------
                # Random event
                # ----------------------------

                elif (
                        activity_type
                        == night.CAREER_ACTIVITY_EVENT
                ):
                    entry = current_career_schedule_entry()

                    # No calendar entry for today (bad save data): stay on the hub.
                    if entry is not None:
                        state.career_event_entry = entry
                        state.career_event_has_activity = False

                        event_id = state.career_event_entry.get("event_id")

                        if event_id == "press_interview_01":
                            start_press_interview_event()
                        elif event_id == "sign_autographs_01":
                            start_sign_autographs_event()
                        elif event_id == "head_to_head_01":
                            head_to_head_screen.start_head_to_head_event()

                        if event_id in ("career_encounter", "bigfoot_night", "alien_night"):
                            start_career_activity(work=False)
                        else:
                            state.current_state = state_names.STATE_CAREER_EVENT

        elif state.career_jobs_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.current_state = state_names.STATE_CAREER_JOBS

        elif state.career_real_estate_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.current_state = state_names.STATE_CAREER_REAL_ESTATE

        elif state.career_leaderboards_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.current_state = state_names.STATE_CAREER_LEADERBOARDS

        elif state.career_news_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.current_state = state_names.STATE_CAREER_NEWS

        elif state.career_back_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.current_state = state_names.STATE_MODE_SELECT


        elif state.career_calendar_skip_rect.collidepoint(
                state.game_mouse_pos
        ):

            sounds.audio.play_sound(
                "button_click"
            )

            skip_career_day()


def draw():
    """Old draw-chain branch for STATE_CAREER_HUB."""

    draw_career_hub()
