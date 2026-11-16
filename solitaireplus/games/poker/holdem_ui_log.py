"""Texas Hold'em table UI: the GAME LOG / TABLE CHAT panel and Quick Chat.

One part of the Hold'em table UI (see holdem_ui.py, which re-exports every name here).
The log and chat histories and the Quick Chat queue are the lists in holdem_ui_state.py.
"""
from solitaireplus.app import state

import pygame

from solitaireplus.games.poker.speech import is_poker_chat_popups_enabled
from solitaireplus.games.poker.log_rows import log_rows, visible_log_rows
from solitaireplus.games.poker.quick_chat import (
    quick_chat_options_for_game,
    quick_chat_target_options,
    quick_chat_availability,
    submit_holdem_quick_chat,
)
from solitaireplus.games.poker.holdem_ui_state import (
    HOLDEM_LOG_LINE_STEP,
    HOLDEM_LOG_MIN_SQUASH,
    HOLDEM_LOG_RECT,
    HOLDEM_LOG_TEXT_HEIGHT,
    HOLDEM_LOG_TEXT_WIDTH,
    WHITE,
    _holdem_speech_overlay,
    _ui,
    get_holdem_fonts,
    holdem_chat_history,
    holdem_log_history,
    holdem_quick_chat_pending,
)
from solitaireplus.games.poker.holdem_ui_widgets import draw_holdem_glossy_button, draw_translucent_panel


# ==================================================
# QUICK CHAT AND LOG / CHAT PANEL CLICKS
# ==================================================

def _get_holdem_quick_chat_rects(game=None, target_mode=None):
    outer_rect = HOLDEM_LOG_RECT
    toggle_rect = pygame.Rect(
        outer_rect.x + 202,
        outer_rect.y + 10,
        110,
        28
    )
    if target_mode:
        rows = [("__back__", "‹ Back")] + list(quick_chat_target_options(game, target_mode))
    else:
        rows = list(quick_chat_options_for_game(game))

    row_height = 27
    row_gap = 4
    popup_height = 42 + len(rows) * (row_height + row_gap)
    popup_height = max(74, min(322, popup_height))
    popup_rect = pygame.Rect(
        outer_rect.x,
        outer_rect.y - popup_height - 12,
        320,
        popup_height
    )
    option_rects = []
    option_y = popup_rect.y + 34
    for item in rows:
        if target_mode and item[0] != "__back__":
            npc_index, label = item
            key = ("__target__", int(npc_index))
        else:
            key, label = item
        option_rects.append((
            key,
            label,
            pygame.Rect(
                popup_rect.x + 12,
                option_y,
                popup_rect.width - 24,
                row_height
            )
        ))
        option_y += row_height + row_gap
    return toggle_rect, popup_rect, option_rects


def _queue_holdem_quick_chat_responses(responses):
    now = pygame.time.get_ticks()
    for response in responses or ():
        if isinstance(response, dict):
            speaker = response.get("speaker", "")
            message = response.get("message", "")
            delay = max(0, int(response.get("delay_ms", 0) or 0))
        else:
            try:
                speaker, message = response[:2]
                delay = int(response[2]) if len(response) > 2 else 0
            except (TypeError, ValueError):
                continue
        if not message:
            continue
        if delay <= 0:
            add_holdem_chat_message(speaker, message)
        else:
            holdem_quick_chat_pending.append((now + delay, speaker, message))
    holdem_quick_chat_pending.sort(key=lambda item: item[0])


def _pump_holdem_quick_chat_responses():
    if not holdem_quick_chat_pending:
        return
    now = pygame.time.get_ticks()
    due = []
    while holdem_quick_chat_pending and holdem_quick_chat_pending[0][0] <= now:
        due.append(holdem_quick_chat_pending.pop(0))
    for _when, speaker, message in due:
        add_holdem_chat_message(speaker, message)


def handle_holdem_panel_click(
        mouse_pos
):

    if mouse_pos is None:
        return False

    outer_rect = HOLDEM_LOG_RECT

    log_tab_rect = pygame.Rect(
        outer_rect.x + 12,
        outer_rect.y + 10,
        100,
        28
    )

    chat_tab_rect = pygame.Rect(
        outer_rect.x + 118,
        outer_rect.y + 10,
        76,
        28
    )

    game = _ui.holdem_active_game
    quick_toggle_rect, quick_popup_rect, quick_option_rects = (
        _get_holdem_quick_chat_rects(game, state.holdem_quick_chat_target_mode)
    )

    if log_tab_rect.collidepoint(mouse_pos):
        state.holdem_active_tab = "log"
        state.holdem_quick_chat_open = False
        state.holdem_quick_chat_target_mode = None
        return True

    if chat_tab_rect.collidepoint(mouse_pos):
        state.holdem_active_tab = "chat"
        state.holdem_chat_unread = False
        state.holdem_quick_chat_open = False
        state.holdem_quick_chat_target_mode = None
        return True

    if quick_toggle_rect.collidepoint(mouse_pos):
        if (
            state.holdem_table_chat_enabled
            and game is not None
            and quick_chat_options_for_game(game)
        ):
            state.holdem_quick_chat_open = not state.holdem_quick_chat_open
            if not state.holdem_quick_chat_open:
                state.holdem_quick_chat_target_mode = None
        return True

    if state.holdem_quick_chat_open:
        for key, label, rect in quick_option_rects:
            if not rect.collidepoint(mouse_pos):
                continue
            if game is None:
                return True

            if key == "__back__":
                state.holdem_quick_chat_target_mode = None
                return True

            if isinstance(key, tuple) and key and key[0] == "__target__":
                target_index = int(key[1])
                chat_key = state.holdem_quick_chat_target_mode
                if not chat_key:
                    return True
                enabled, _reason = quick_chat_availability(game, chat_key, target_index)
                if not enabled:
                    return True
                result = submit_holdem_quick_chat(game, chat_key, target_index=target_index)
            else:
                enabled, _reason = quick_chat_availability(game, key)
                if not enabled:
                    return True
                if quick_chat_target_options(game, key):
                    state.holdem_quick_chat_target_mode = key
                    return True
                result = submit_holdem_quick_chat(game, key)

            if result.get("accepted"):
                add_holdem_chat_message("You", result.get("label", label))
                _queue_holdem_quick_chat_responses(result.get("responses", []))
                state.holdem_active_tab = "chat"
                state.holdem_chat_unread = False
                state.holdem_quick_chat_open = False
                state.holdem_quick_chat_target_mode = None
            return True

        if quick_popup_rect.collidepoint(mouse_pos):
            return True

        state.holdem_quick_chat_open = False
        state.holdem_quick_chat_target_mode = None

    return False


def get_holdem_log_rows(log_lines):
    """The GAME LOG's rows: a log line too wide that squashes to 65 % or more is one
    row, squashed to fit (_holdem_log_line_squashes_legibly); a longer one
    word-wraps to the panel (log_rows).

    The log scrolls by these rows, so the screen passes their count to
    scroll_holdem_log.
    """
    return log_rows(
        get_holdem_fonts()["small"],
        log_lines,
        HOLDEM_LOG_TEXT_WIDTH,
        _holdem_log_line_squashes_legibly
    )


def _holdem_log_line_squashes_legibly(font, text, width):
    """Whether squash_holdem_log_text keeps this log line, too wide for ``width``,
    at HOLDEM_LOG_MIN_SQUASH of its size or more (the same factor it squashes by).

    log_rows asks once per line and remembers the answer.
    """
    return width / font.size(text)[0] >= HOLDEM_LOG_MIN_SQUASH


def squash_holdem_log_text(text_surface, max_width):
    """A rendered log or chat line squashed to ``max_width``, keeping its proportions,
    if it is wider (as the panel always drew a long line); else the same surface."""
    if text_surface.get_width() > max_width:
        scale = max_width / text_surface.get_width()
        new_width = max(1, int(text_surface.get_width() * scale))
        new_height = max(1, int(text_surface.get_height() * scale))
        text_surface = pygame.transform.smoothscale(text_surface, (new_width, new_height))

    return text_surface


def get_holdem_log_layout():
    """The GAME LOG's height, line step, wrapped-row step and row height
    (log_rows.visible_log_rows).

    A row at offset y is centred HOLDEM_LOG_LINE_STEP // 2 below it (as every line
    was), so its bottom is that plus the lower half of a rendered row. Three rows
    always fit and four never do, so scroll_holdem_log stops three rows from the
    oldest (log_rows.max_log_scroll).
    """
    rendered_height = get_holdem_fonts()["small"].size("Ag")[1]

    return (
        HOLDEM_LOG_TEXT_HEIGHT,
        HOLDEM_LOG_LINE_STEP,
        rendered_height,
        HOLDEM_LOG_LINE_STEP // 2 + rendered_height - rendered_height // 2
    )


def scroll_holdem_log(
        wheel_y,
        total_lines
):

    visible_line_count = 3

    # ==================================================
    # CHAT
    # ==================================================

    if state.holdem_active_tab == "chat":

        total_chat_lines = (
            len(
                holdem_chat_history
            )
        )

        max_scroll = max(
            0,
            total_chat_lines
            - visible_line_count
        )

        state.holdem_chat_scroll += (
            wheel_y
        )

        state.holdem_chat_scroll = max(
            0,
            min(
                state.holdem_chat_scroll,
                max_scroll
            )
        )

        return

    # ==================================================
    # GAME LOG
    # ==================================================

    max_scroll = max(
        0,
        total_lines
        - visible_line_count
    )

    state.holdem_log_scroll += (
        wheel_y
    )

    state.holdem_log_scroll = max(
        0,
        min(
            state.holdem_log_scroll,
            max_scroll
        )
    )


def add_holdem_chat_message(
        speaker,
        message
):

    if not message:
        return

    if not state.holdem_table_chat_enabled:
        return

    if speaker and is_poker_chat_popups_enabled():
        _holdem_speech_overlay.post(
            speaker,
            message
        )

    if speaker:

        text = (
            f"{speaker}: {message}"
        )

    else:

        text = message

    holdem_chat_history.append(
        text
    )

    # Keep history from growing forever
    if len(
            holdem_chat_history
    ) > 100:

        del holdem_chat_history[
            :-100
        ]

    # New messages return view to newest
    state.holdem_chat_scroll = 0

    # If player is not currently looking at chat,
    # light up the Chat tab.
    if state.holdem_active_tab != "chat":

        state.holdem_chat_unread = True

def update_holdem_log(
        holdem_game
):

    # ==================================================
    # Engine-owned hand history
    #
    # TexasHoldemGame now records the actual sequence of
    # blinds, actions, streets, showdown hands, side pots,
    # payouts, and eliminations. The UI simply mirrors it.
    # ==================================================

    get_history = getattr(
        holdem_game,
        "get_hand_history_lines",
        None
    )

    if callable(get_history):

        engine_lines = get_history()

        if engine_lines != holdem_log_history:

            holdem_log_history[:] = (
                engine_lines
            )

            # New information always returns the log view
            # to the most recent action.
            state.holdem_log_scroll = 0

        return

    # ==================================================
    # Compatibility fallback
    #
    # This remains only so an older poker engine can still
    # be displayed without crashing.
    # ==================================================

    stage = holdem_game.current_stage

    if stage != _ui.holdem_last_stage:

        stage_messages = {
            "ready":
                "Waiting for next hand.",

            "preflop":
                "Hole cards dealt.",

            "showdown":
                "Showdown.",
        }

        message = stage_messages.get(
            stage
        )

        if message:
            holdem_log_history.append(
                message
            )

        _ui.holdem_last_stage = stage
        state.holdem_log_scroll = 0

    result_text = getattr(
        holdem_game,
        "result_text",
        ""
    )

    if (
            result_text
            and result_text
            != _ui.holdem_last_result
    ):

        holdem_log_history.append(
            result_text
        )

        _ui.holdem_last_result = (
            result_text
        )

        state.holdem_log_scroll = 0


def draw_holdem_log_panel(
        game_surface,
        detail_font,
        mouse_pos,
        active_tab="log",
        log_lines=None
):

    holdem_fonts = get_holdem_fonts()

    holdem_small_font = (
        holdem_fonts["small"]
    )

    if log_lines is None:
        log_lines = []

    outer_rect = HOLDEM_LOG_RECT

    draw_translucent_panel(
        game_surface,
        outer_rect,
        (
            8,
            16,
            18,
            205
        ),
        border_color=(
            185,
            185,
            190
        ),
        border_width=2,
        radius=12
    )

    # ==================================================
    # Tabs
    # ==================================================

    log_tab_rect = pygame.Rect(
        outer_rect.x + 12,
        outer_rect.y + 10,
        100,
        28
    )

    chat_tab_rect = pygame.Rect(
        outer_rect.x + 118,
        outer_rect.y + 10,
        76,
        28
    )

    draw_holdem_glossy_button(
        game_surface,
        log_tab_rect,
        "Game Log",
        mouse_pos,
        holdem_small_font,
        enabled=True,
        selected=(
            active_tab == "log"
        )
    )

    draw_holdem_glossy_button(
        game_surface,
        chat_tab_rect,
        "Chat",
        mouse_pos,
        holdem_small_font,
        enabled=True,
        selected=(
                active_tab == "chat"
        ),
        attention=(
                state.holdem_chat_unread
                and active_tab != "chat"
        )
    )

    quick_options = quick_chat_options_for_game(_ui.holdem_active_game)
    quick_toggle_rect, quick_popup_rect, quick_option_rects = (
        _get_holdem_quick_chat_rects(
            _ui.holdem_active_game,
            state.holdem_quick_chat_target_mode
        )
    )
    quick_enabled = (
        state.holdem_table_chat_enabled
        and _ui.holdem_active_game is not None
        and bool(quick_options)
    )

    draw_holdem_glossy_button(
        game_surface,
        quick_toggle_rect,
        "Quick Chat",
        mouse_pos,
        holdem_small_font,
        enabled=quick_enabled,
        selected=state.holdem_quick_chat_open
    )

    if state.holdem_quick_chat_open and quick_enabled:
        draw_translucent_panel(
            game_surface,
            quick_popup_rect,
            (8, 16, 18, 238),
            border_color=(210, 178, 90),
            border_width=2,
            radius=12
        )

        title_text = "CHOOSE PLAYER" if state.holdem_quick_chat_target_mode else "QUICK CHAT"
        popup_title = holdem_small_font.render(
            title_text,
            True,
            (242, 224, 172)
        )
        game_surface.blit(
            popup_title,
            popup_title.get_rect(
                center=(quick_popup_rect.centerx, quick_popup_rect.y + 18)
            )
        )

        tiny_font = get_holdem_fonts()["tiny"]
        for key, label, rect in quick_option_rects:
            if key == "__back__" or (isinstance(key, tuple) and key and key[0] == "__target__"):
                enabled = True
                button_text = label
            else:
                enabled, _reason = quick_chat_availability(_ui.holdem_active_game, key)
                button_text = label
            draw_holdem_glossy_button(
                game_surface,
                rect,
                button_text,
                mouse_pos,
                tiny_font,
                enabled=enabled
            )

    # ==================================================
    # Inner text area
    # ==================================================

    inner_rect = pygame.Rect(
        outer_rect.x + 12,
        outer_rect.y + 48,
        outer_rect.width - 24,
        outer_rect.height - 58
    )

    draw_translucent_panel(
        game_surface,
        inner_rect,
        (
            0,
            0,
            0,
            150
        ),
        border_color=(
            90,
            95,
            100
        ),
        border_width=1,
        radius=8
    )

    # ==================================================
    # Visible log lines
    # ==================================================

    if active_tab == "log":

        line_spacing = HOLDEM_LOG_LINE_STEP

        # A long line wraps onto several rows at the log font size, and the log
        # scrolls by rows; the newest rows stay at the bottom.
        log_rows_all = get_holdem_log_rows(log_lines)
        visible_rows = visible_log_rows(
            log_rows_all,
            state.holdem_log_scroll,
            *get_holdem_log_layout()
        )

    else:

        visible_line_count = 4
        line_spacing = 18

        end_index = (

                len(holdem_chat_history)

                - state.holdem_chat_scroll

        )

        end_index = max(

            0,

            min(

                end_index,

                len(holdem_chat_history)

            )

        )

        start_index = max(

            0,

            end_index

            - visible_line_count

        )

        visible_lines = (

            holdem_chat_history[

                start_index:end_index

            ]

        )

        if not visible_lines:
            visible_lines = [

                "No table chat yet."

            ]

    # ==================================================
    # Draw lines
    # ==================================================

    text_y = (
        inner_rect.y + 9
    )

    # Nothing is drawn outside the panel. Log rows stay inside the inner box (they
    # end 2 px above its bottom); chat rows, shrunk to the box's width, keep their
    # old place, where the fourth row's descenders reach the box's bottom edge.
    panel_clip = game_surface.get_clip()
    game_surface.set_clip(panel_clip.clip(
        inner_rect if active_tab == "log" else outer_rect.inflate(-4, -4)
    ))

    if active_tab == "log":

        for row_text, row_offset in visible_rows:

            # A wrapped row fits; a line too wide but legible squashed is one row,
            # squashed to fit as it always was (get_holdem_log_rows).
            row_surface = squash_holdem_log_text(
                holdem_small_font.render(
                    row_text,
                    True,
                    WHITE
                ),
                HOLDEM_LOG_TEXT_WIDTH
            )

            game_surface.blit(
                row_surface,
                row_surface.get_rect(
                    midleft=(
                        inner_rect.x + 10,
                        text_y
                        + row_offset
                        + line_spacing // 2
                    )
                )
            )

        visible_lines = []

    for line in visible_lines:

        line_surface = (
            holdem_small_font.render(
                line,
                True,
                WHITE
            )
        )

        max_text_width = (
                inner_rect.width - 24
        )

        line_surface = squash_holdem_log_text(
            line_surface,
            max_text_width
        )

        line_rect = (
            line_surface.get_rect(
                midleft=(
                    inner_rect.x + 10,
                    text_y
                    + line_spacing // 2
                )
            )
        )

        game_surface.blit(
            line_surface,
            line_rect
        )

        text_y += line_spacing

    game_surface.set_clip(panel_clip)

    # ==================================================
    # Scroll indicator (log rows, newest at the bottom)
    # ==================================================

    if (
            active_tab == "log"
            and len(log_rows_all) > 3
    ):

        track_rect = pygame.Rect(
            inner_rect.right - 7,
            inner_rect.y + 6,
            3,
            inner_rect.height - 12
        )

        pygame.draw.rect(
            game_surface,
            (
                70,
                75,
                80
            ),
            track_rect,
            border_radius=2
        )

        max_scroll = max(
            1,
            len(log_rows_all) - 3
        )

        thumb_height = max(
            12,
            int(
                track_rect.height
                * (
                    3
                    / len(log_rows_all)
                )
            )
        )

        available_travel = (
            track_rect.height
            - thumb_height
        )

        scroll_fraction = (
            state.holdem_log_scroll
            / max_scroll
        )

        # scroll=0 means newest, so thumb sits at bottom
        thumb_y = (
            track_rect.bottom
            - thumb_height
            - int(
                available_travel
                * scroll_fraction
            )
        )

        thumb_rect = pygame.Rect(
            track_rect.x,
            thumb_y,
            track_rect.width,
            thumb_height
        )

        pygame.draw.rect(
            game_surface,
            (
                190,
                195,
                200
            ),
            thumb_rect,
            border_radius=2
        )

    return {
        "log_tab": log_tab_rect,
        "chat_tab": chat_tab_rect,
    }
