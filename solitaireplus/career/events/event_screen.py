"""Career event screen: press interviews and autographs (moved out of legacy.py)."""
from solitaireplus.career.events.autographs import AUTOGRAPH_CANVAS_RECT
from solitaireplus.career.events.autographs import AUTOGRAPH_CLEAR_RECT
from solitaireplus.career.events.autographs import AUTOGRAPH_SUBMIT_RECT
from solitaireplus.career.events.autographs import AutographEvent
from solitaireplus.games.solitaire.rules import BASE_WIDTH
from solitaireplus.app.settings import DEFAULT_DIFFICULTY
from solitaireplus.games.solitaire.head_to_head import HeadToHeadRace
from solitaireplus.career.fans import MAX_FANS
from solitaireplus.career.events.press_interview import answer_outcome
from solitaireplus.games.solitaire.head_to_head_ui import draw_head_to_head_selection
from solitaireplus.career.fans import fan_change_from_autograph_accuracy
from solitaireplus.games.solitaire.head_to_head_ui import get_selection_action as get_head_to_head_selection_action
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
web_pages = lazy("solitaireplus.career.web_pages")
career_rewards = lazy("solitaireplus.career.career_rewards")
game_portraits = lazy("solitaireplus.npc.game_portraits")
profile_editor = lazy("solitaireplus.profile.profile_editor")
table = lazy("solitaireplus.games.solitaire.table")
window = lazy("solitaireplus.app.window")
ui_text = lazy("solitaireplus.ui.text")
sounds = lazy("solitaireplus.app.sounds")
panels = lazy("solitaireplus.ui.panels")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")


# Sign-autographs event runtime
career_autograph_event = AutographEvent()

# Head-to-Head timed Klondike event runtime
head_to_head_race = HeadToHeadRace()

career_interview_answer_rects = [
    pygame.Rect(348, 410, 670, 54),
    pygame.Rect(348, 480, 670, 54),
    pygame.Rect(348, 550, 670, 54),
]

def draw_career_placeholder_page(
        title_text,
        subtitle_text
):
    window.game_surface.fill(
        (
            205,
            245,
            230
        )
    )

    title = fonts.options_title_font.render(
        title_text,
        True,
        (
            20,
            20,
            20
        )
    )

    title_rect = title.get_rect(
        center=(
            BASE_WIDTH // 2,
            120
        )
    )

    window.game_surface.blit(
        title,
        title_rect
    )

    subtitle = fonts.option_label_font.render(
        subtitle_text,
        True,
        (
            60,
            60,
            60
        )
    )

    subtitle_rect = subtitle.get_rect(
        center=(
            BASE_WIDTH // 2,
            230
        )
    )

    window.game_surface.blit(
        subtitle,
        subtitle_rect
    )

    buttons.draw_button(
        web_pages.career_subpage_back_rect,
        "Return to Career"
    )


def get_press_interview_temperature_label():
    if state.career_interview_media_heat >= 55:
        return "HOT"
    if state.career_interview_media_heat >= 20:
        return "WARM"
    if state.career_interview_media_heat <= -55:
        return "ICY"
    if state.career_interview_media_heat <= -20:
        return "COLD"
    return "NEUTRAL"


def handle_press_interview_answer(answer_index):

    if not (0 <= state.career_interview_index < len(state.career_interview_questions)):
        return False

    answers = state.career_interview_questions[state.career_interview_index]["answers"]
    if not (0 <= answer_index < len(answers)):
        return False

    state.career_interview_media_heat, proposed_change = answer_outcome(
        state.career_interview_media_heat, answers[answer_index], state.career_rating, state.career_fans
    )
    actual_change = career_rewards.award_career_fans(
        proposed_change,
        "Press interview"
    )
    state.career_interview_fan_change += actual_change

    if actual_change > 0:
        state.career_interview_feedback = f"The room responds well. +{actual_change:,} fans."
    elif actual_change < 0:
        state.career_interview_feedback = f"That answer lands badly. {actual_change:,} fans."
    else:
        state.career_interview_feedback = "The answer barely moves the needle."

    state.career_interview_index += 1
    state.career_event_has_activity = True

    if state.career_interview_index >= len(state.career_interview_questions):
        temperature = get_press_interview_temperature_label()
        signed = (
            f"+{state.career_interview_fan_change:,}"
            if state.career_interview_fan_change >= 0
            else f"{state.career_interview_fan_change:,}"
        )
        state.career_event_summary_title = "PRESS INTERVIEW COMPLETE"
        state.career_event_summary_lines = [
            f"Media reception: {temperature}",
            f"Fan change: {signed}",
            f"Total Fans: {state.career_fans:,} / {MAX_FANS:,}",
        ]
        state.current_state = state_names.STATE_CAREER_EVENT_SUMMARY

    return True


def handle_sign_autograph_submit():

    score = career_autograph_event.submit_current()
    if score is None:
        return False

    proposed_change = fan_change_from_autograph_accuracy(
        score,
        current_fans=state.career_fans,
        current_rating=state.career_rating,
    )
    actual_change = career_rewards.award_career_fans(
        proposed_change,
        "Autograph signing",
    )
    state.career_autograph_last_change = actual_change
    state.career_autograph_fan_change += actual_change

    if career_autograph_event.complete:
        state.career_event_has_activity = True
        average = career_autograph_event.average_accuracy()
        signed = (
            f"+{state.career_autograph_fan_change:,}"
            if state.career_autograph_fan_change >= 0
            else f"{state.career_autograph_fan_change:,}"
        )
        state.career_event_summary_title = "SIGNING COMPLETE"
        state.career_event_summary_lines = [
            f"Average tracing accuracy: {average:.0f}%",
            f"Fan change: {signed}",
            f"Total Fans: {state.career_fans:,} / {MAX_FANS:,}",
        ]
        state.current_state = state_names.STATE_CAREER_EVENT_SUMMARY

    return True


def begin_selected_head_to_head_race():

    if not (
            state.head_to_head_selected_index is not None
            and 0 <= state.head_to_head_selected_index < len(state.head_to_head_opponents)
    ):
        return False

    opponent = dict(
        state.head_to_head_opponents[
            state.head_to_head_selected_index
        ]
    )

    ratings = opponent.get("ratings") or {}
    opponent["race_rating"] = ratings.get(
        "solitaire",
        opponent.get("rating", 1000)
    )

    state.head_to_head_previous_deal_mode = table.game.deal_mode
    state.head_to_head_previous_difficulty = table.game.difficulty
    state.head_to_head_previous_stock_draw_count = table.game.stock_draw_count

    table.game.clear_challenge()
    table.game.set_difficulty(DEFAULT_DIFFICULTY)

    table.game.stock_draw_count = 1
    table.game.set_deal_mode("random")
    table.game.new_race_game()

    head_to_head_race.prepare(
        opponent,
        player_rating=state.career_ratings["solitaire"],
        now_ms=pygame.time.get_ticks(),
    )
    # The player's clock starts at GO, like the opponent's: the 3-2-1 countdown is not race time.
    table.game.round_start_ticks = head_to_head_race.race_started_ms

    state.career_event_has_activity = True
    state.current_game_mode = "head_to_head"
    state.current_state = state_names.STATE_PLAYING
    return True


def draw_head_to_head_event():
    draw_head_to_head_selection(
        window.game_surface,
        state.game_mouse_pos,
        state.head_to_head_opponents,
        state.head_to_head_selected_index,
        state.player_name,
        state.career_ratings["solitaire"],
        game_portraits.get_npc_portrait_surface,
        fonts.options_title_font,
        fonts.option_label_font,
        fonts.difficulty_detail_font,
        fonts.ui_small_font,
        player_avatar=profile_editor.get_profile_avatar(),
    )


def draw_sign_autographs_event():
    panels.draw_submenu_background(overlay_alpha=145)

    outer = pygame.Rect(238, 82, 890, 610)
    outer_surface = pygame.Surface(outer.size, pygame.SRCALPHA)
    outer_surface.fill((20, 24, 28, 242))
    window.game_surface.blit(outer_surface, outer.topleft)
    pygame.draw.rect(
        window.game_surface,
        (220, 220, 220),
        outer,
        3,
        border_radius=12,
    )

    title = fonts.options_title_font.render(
        "SIGN AUTOGRAPHS",
        True,
        (255, 255, 255),
    )
    window.game_surface.blit(
        title,
        title.get_rect(center=(BASE_WIDTH // 2, 118)),
    )

    template = career_autograph_event.current_template
    template_name = template.get("name", "Autograph") if template else "Autograph"
    progress = fonts.option_label_font.render(
        f"Trace: {template_name}",
        True,
        (245, 226, 160),
    )
    window.game_surface.blit(
        progress,
        progress.get_rect(center=(BASE_WIDTH // 2, 158)),
    )

    canvas = AUTOGRAPH_CANVAS_RECT
    pygame.draw.rect(
        window.game_surface,
        (244, 241, 230),
        canvas,
        border_radius=12,
    )
    pygame.draw.rect(
        window.game_surface,
        (65, 65, 68),
        canvas,
        3,
        border_radius=12,
    )

    instruction = fonts.difficulty_detail_font.render(
        "Hold the left mouse button and trace the guide.",
        True,
        (65, 65, 68),
    )
    window.game_surface.blit(
        instruction,
        instruction.get_rect(center=(canvas.centerx, canvas.y + 26)),
    )

    target_points = career_autograph_event.get_target_points()
    if len(target_points) >= 2:
        pygame.draw.lines(
            window.game_surface,
            (213, 186, 115),
            False,
            target_points,
            10,
        )
        pygame.draw.lines(
            window.game_surface,
            (252, 243, 205),
            False,
            target_points,
            4,
        )

    trace = career_autograph_event.trace_points
    if len(trace) >= 2:
        pygame.draw.lines(
            window.game_surface,
            (45, 100, 180),
            False,
            trace,
            5,
        )

    accuracy = career_autograph_event.current_accuracy()
    accuracy_surface = fonts.difficulty_detail_font.render(
        f"Current accuracy: {accuracy:.0f}%",
        True,
        (45, 70, 105),
    )
    window.game_surface.blit(
        accuracy_surface,
        accuracy_surface.get_rect(
            bottomright=(canvas.right - 18, canvas.bottom - 14)
        ),
    )

    buttons.draw_button(
        AUTOGRAPH_CLEAR_RECT,
        "Clear",
        font=fonts.option_label_font,
    )
    buttons.draw_button(
        AUTOGRAPH_SUBMIT_RECT,
        "Sign It!",
        font=fonts.option_label_font,
    )

    feedback = career_autograph_event.feedback
    if state.career_autograph_last_change:
        signed = (
            f"+{state.career_autograph_last_change:,}"
            if state.career_autograph_last_change > 0
            else f"{state.career_autograph_last_change:,}"
        )
        feedback = f"{feedback}   Fans: {signed}"

    feedback_surface = fonts.difficulty_detail_font.render(
        feedback,
        True,
        (215, 220, 224),
    )
    window.game_surface.blit(
        feedback_surface,
        feedback_surface.get_rect(center=(BASE_WIDTH // 2, 664)),
    )

def draw_career_event():
    event_id = (
        state.career_event_entry.get("event_id")
        if isinstance(state.career_event_entry, dict)
        else None
    )

    if event_id == "sign_autographs_01":
        draw_sign_autographs_event()
        return

    if event_id == "head_to_head_01":
        draw_head_to_head_event()
        return

    if event_id != "press_interview_01":
        draw_career_placeholder_page(
            "CAREER EVENT",
            "This career event is not implemented yet."
        )
        return

    panels.draw_submenu_background(overlay_alpha=150)

    panel = pygame.Rect(235, 105, 896, 545)
    panel_surface = pygame.Surface(panel.size, pygame.SRCALPHA)
    panel_surface.fill((18, 23, 28, 242))
    window.game_surface.blit(panel_surface, panel.topleft)
    pygame.draw.rect(window.game_surface, (220, 220, 220), panel, 3, border_radius=12)

    title = fonts.options_title_font.render("PRESS INTERVIEW", True, (255, 255, 255))
    window.game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 150)))

    progress = fonts.difficulty_detail_font.render(
        f"Question {min(state.career_interview_index + 1, len(state.career_interview_questions))} of {len(state.career_interview_questions)}",
        True,
        (205, 210, 215)
    )
    window.game_surface.blit(progress, progress.get_rect(center=(BASE_WIDTH // 2, 192)))

    # Media hot/cold meter.
    meter = pygame.Rect(448, 224, 470, 28)
    pygame.draw.rect(window.game_surface, (70, 85, 115), meter, border_radius=9)
    midpoint = meter.centerx
    heat_width = int((abs(state.career_interview_media_heat) / 100.0) * (meter.width // 2 - 4))
    if state.career_interview_media_heat >= 0:
        heat_rect = pygame.Rect(midpoint, meter.y + 4, heat_width, meter.height - 8)
        heat_color = (220, 115, 55)
    else:
        heat_rect = pygame.Rect(midpoint - heat_width, meter.y + 4, heat_width, meter.height - 8)
        heat_color = (75, 155, 230)
    if heat_width > 0:
        pygame.draw.rect(window.game_surface, heat_color, heat_rect, border_radius=6)
    pygame.draw.line(window.game_surface, (245, 245, 245), (midpoint, meter.y), (midpoint, meter.bottom), 2)

    temperature = fonts.difficulty_detail_font.render(
        f"MEDIA: {get_press_interview_temperature_label()}",
        True,
        (255, 235, 165)
    )
    window.game_surface.blit(temperature, temperature.get_rect(center=(BASE_WIDTH // 2, 272)))

    if 0 <= state.career_interview_index < len(state.career_interview_questions):
        question = state.career_interview_questions[state.career_interview_index]
        ui_text.draw_wrapped_text(
            question["question"],
            fonts.option_label_font,
            (255, 255, 255),
            pygame.Rect(335, 305, 696, 78),
            line_spacing=6
        )

        for index, (answer_text, _heat, _appeal) in enumerate(question["answers"]):
            rect = career_interview_answer_rects[index]
            buttons.draw_button(rect, answer_text, font=fonts.difficulty_detail_font)

    feedback = fonts.difficulty_detail_font.render(
        state.career_interview_feedback,
        True,
        (210, 215, 220)
    )
    window.game_surface.blit(feedback, feedback.get_rect(center=(BASE_WIDTH // 2, 620)))

    # The interview is a committed Career event once started. Complete all
    # three questions to return to the calendar.


def handle_event(event):
    """Old main-loop event branch for STATE_CAREER_EVENT."""

    event_id = (
        state.career_event_entry.get("event_id")
        if isinstance(state.career_event_entry, dict)
        else None
    )

    if event_id == "press_interview_01":
        if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and state.game_mouse_pos is not None
        ):
            for answer_index, answer_rect in enumerate(
                    career_interview_answer_rects
            ):
                if answer_rect.collidepoint(state.game_mouse_pos):
                    sounds.audio.play_sound("button_click")
                    handle_press_interview_answer(answer_index)
                    break

    elif event_id == "sign_autographs_01":
        if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and state.game_mouse_pos is not None
        ):
            if AUTOGRAPH_CLEAR_RECT.collidepoint(state.game_mouse_pos):
                sounds.audio.play_sound("button_click")
                career_autograph_event.clear_trace()
                state.career_autograph_last_change = 0

            elif AUTOGRAPH_SUBMIT_RECT.collidepoint(state.game_mouse_pos):
                sounds.audio.play_sound("button_click")
                if len(career_autograph_event.trace_points) >= 2:
                    handle_sign_autograph_submit()
                else:
                    career_autograph_event.feedback = (
                        "Trace the autograph before signing it."
                    )

            else:
                if career_autograph_event.begin_trace(state.game_mouse_pos):
                    state.career_autograph_last_change = 0

        elif (
                event.type == pygame.MOUSEMOTION
                and state.game_mouse_pos is not None
                and career_autograph_event.drawing
        ):
            career_autograph_event.add_trace_point(state.game_mouse_pos)

        elif (
                event.type == pygame.MOUSEBUTTONUP
                and event.button == 1
        ):
            career_autograph_event.end_trace()

    elif event_id == "head_to_head_01":
        if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and state.game_mouse_pos is not None
        ):
            head_to_head_action = get_head_to_head_selection_action(
                state.game_mouse_pos,
                len(state.head_to_head_opponents),
            )

            if head_to_head_action is not None:
                action_name, action_value = head_to_head_action

                if action_name == "opponent":
                    sounds.audio.play_sound("button_click")
                    state.head_to_head_selected_index = action_value

                elif action_name == "start":
                    if state.head_to_head_selected_index is not None:
                        sounds.audio.play_sound("button_click")
                        begin_selected_head_to_head_race()

                elif action_name == "return":
                    sounds.audio.play_sound("button_click")
                    state.current_state = state_names.STATE_CAREER_HUB

    elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
            and web_pages.career_subpage_back_rect.collidepoint(state.game_mouse_pos)
    ):
        sounds.audio.play_sound("button_click")
        state.current_state = state_names.STATE_CAREER_HUB


def draw():
    """Old draw-chain branch for STATE_CAREER_EVENT."""

    draw_career_event()
