"""Career event-night summary screen (moved out of legacy.py)."""
from solitaireplus.games.solitaire.rules import BASE_WIDTH
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
calendar = lazy("solitaireplus.career.calendar")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
ui_text = lazy("solitaireplus.ui.text")
sounds = lazy("solitaireplus.app.sounds")
panels = lazy("solitaireplus.ui.panels")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")


# ==================================================
# CAREER RECTANGLES // CAREER UI RECTS
# ==================================================

career_event_summary_continue_rect = pygame.Rect(
    BASE_WIDTH // 2 - 100,
    620,
    200,
    50
)

def draw_career_event_summary():

    # ==================================================
    # Background
    # ==================================================

    panels.draw_submenu_background(
        overlay_alpha=145
    )

    # ==================================================
    # Main panel
    # ==================================================

    panel_rect = pygame.Rect(
        BASE_WIDTH // 2 - 330,
        125,
        660,
        460
    )

    panel_surface = pygame.Surface(
        (
            panel_rect.width,
            panel_rect.height
        ),
        pygame.SRCALPHA
    )

    panel_surface.fill(
        (
            15,
            25,
            20,
            235
        )
    )

    window.game_surface.blit(
        panel_surface,
        panel_rect.topleft
    )

    pygame.draw.rect(
        window.game_surface,
        (
            225,
            225,
            225
        ),
        panel_rect,
        3
    )

    # ==================================================
    # Title
    # ==================================================

    title_surface = (
        fonts.options_title_font.render(
            state.career_event_summary_title,
            True,
            (
                255,
                255,
                255
            )
        )
    )

    title_rect = (
        title_surface.get_rect(
            center=(
                BASE_WIDTH // 2,
                185
            )
        )
    )

    window.game_surface.blit(
        title_surface,
        title_rect
    )

    # ==================================================
    # Divider
    # ==================================================

    pygame.draw.line(
        window.game_surface,
        (
            180,
            180,
            180
        ),
        (
            panel_rect.x + 45,
            235
        ),
        (
            panel_rect.right - 45,
            235
        ),
        2
    )

    # ==================================================
    # Summary lines
    # ==================================================

    start_y = 280
    line_count = max(1, len(state.career_event_summary_lines))
    line_spacing = min(50, 260 // max(1, line_count - 1))

    for index, line_text in enumerate(
            state.career_event_summary_lines
    ):

        line_surface = (
            (ui_text.get_font(None, 28) if line_count > 7 else fonts.option_label_font).render(
                line_text,
                True,
                (
                    240,
                    240,
                    240
                )
            )
        )

        line_rect = (
            line_surface.get_rect(
                center=(
                    BASE_WIDTH // 2,
                    start_y
                    + index
                    * line_spacing
                )
            )
        )

        window.game_surface.blit(
            line_surface,
            line_rect
        )

    # ==================================================
    # Continue button
    # ==================================================

    buttons.draw_menu_button(
        career_event_summary_continue_rect,
        "Continue",
        state.game_mouse_pos,
        font=fonts.difficulty_detail_font
    )


def handle_event(event):
    """Old main-loop event branch for STATE_CAREER_EVENT_SUMMARY."""

    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):

        if (
                career_event_summary_continue_rect
                        .collidepoint(
                    state.game_mouse_pos
                )
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            was_debug_event = (
                isinstance(state.career_event_entry, dict)
                and state.career_event_entry.get("debug", False)
            )

            if not was_debug_event:
                calendar.advance_career_day(
                    completed=True
                )

            state.career_event_entry = None
            state.career_event_has_activity = False

            state.career_event_summary_title = ""
            state.career_event_summary_lines = []

            state.current_state = state_names.STATE_CAREER_HUB


def draw():
    """Old draw-chain branch for STATE_CAREER_EVENT_SUMMARY."""

    draw_career_event_summary()
