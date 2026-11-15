"""The Solitaire table screen: the game, its buttons, pause menu, return confirmation and the per-frame round and Head-to-Head updates (moved out of legacy.py)."""
from solitaireplus.games.solitaire.rules import BASE_HEIGHT
from solitaireplus.games.solitaire.rules import BASE_WIDTH
from solitaireplus.games.solitaire.restart import RestartPrompt
from solitaireplus.games.solitaire.head_to_head_ui import draw_head_to_head_hud
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
news_screen = lazy("solitaireplus.career.news_screen")
night = lazy("solitaireplus.career.events.night")
event_screen = lazy("solitaireplus.career.events.event_screen")
calendar = lazy("solitaireplus.career.calendar")
head_to_head_screen = lazy("solitaireplus.games.solitaire.head_to_head_screen")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
leveling = lazy("solitaireplus.profile.leveling")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")
assets = lazy("solitaireplus.app.assets")


solitaire_restart_prompt = RestartPrompt()

# ==================================================
# GAMEPLAY UI
# ==================================================

confirm_yes_rect = pygame.Rect(
    530,
    390,
    140,
    50
)

confirm_no_rect = pygame.Rect(
    695,
    390,
    140,
    50
)


# ==================================================
# GAMEPLAY MINI BUTTONS
# ==================================================

mini_button_size = 56
mini_button_gap = 4

# MENU
game_menu_rect = pygame.Rect(
    10,
    0,
    mini_button_size,
    mini_button_size
)

# HINT
game_hint_rect = pygame.Rect(
    10,
    0,
    mini_button_size,
    mini_button_size
)

game_undo_rect = pygame.Rect(
    10,
    0,
    mini_button_size,
    mini_button_size
)

game_shuffle_rect = pygame.Rect(
    10,
    0,
    mini_button_size,
    mini_button_size
)

game_auto_solve_rect = pygame.Rect(
        10,
        0,
        mini_button_size,
        mini_button_size
    )

pause_resume_rect = pygame.Rect(
    533,
    300,
    300,
    55
)

pause_options_rect = pygame.Rect(
    533,
    375,
    300,
    55
)

pause_menu_rect = pygame.Rect(
    533,
    450,
    300,
    55
)

def get_hint_tooltip_text():

    if not legacy.game.hints_enabled:
        return "Hint (H): disabled"

    if legacy.game.hints_remaining is None:
        return "Hint (H): unlimited"

    if legacy.game.hints_remaining == 1:
        return "Hint (H): 1 remaining"

    return f"Hint (H): {legacy.game.hints_remaining} remaining"


def get_undo_tooltip_text():

    if legacy.game.challenge_id == "no_undo":
        return "Undo disabled"

    if legacy.game.undo_history_limit is None:
        return "Unlimited undo"

    if legacy.game.undo_history_limit == 0:
        return "Undo disabled"

    return (
        f"Last {legacy.game.undo_history_limit} moves"
    )


def draw_gameplay_ui():

    # ==================================================
    # MINI BUTTON LAYOUT
    # ==================================================

    show_shuffle = legacy.game.shuffle_enabled
    show_auto_solve = (
            legacy.game.can_auto_solve()
            and not legacy.game.auto_solving
    )

    mini_button_count = (
            3
            + int(show_shuffle)
            + int(show_auto_solve)
    )

    mini_button_stack_height = (
        mini_button_size
        * mini_button_count
        + mini_button_gap
        * (
            mini_button_count - 1
        )
    )

    mini_buttons_top = (
        BASE_HEIGHT
        - 10
        - mini_button_stack_height
    )

    game_menu_rect.topleft = (
        10,
        mini_buttons_top
    )

    game_hint_rect.topleft = (
        10,
        game_menu_rect.bottom
        + mini_button_gap
    )

    game_undo_rect.topleft = (
        10,
        game_hint_rect.bottom
        + mini_button_gap
    )

    game_shuffle_rect.topleft = (
        10,
        game_undo_rect.bottom
        + mini_button_gap
    )

    if show_shuffle:
        auto_solve_y = (
                game_shuffle_rect.bottom
                + mini_button_gap
        )
    else:
        auto_solve_y = (
                game_undo_rect.bottom
                + mini_button_gap
        )

    game_auto_solve_rect.topleft = (
        10,
        auto_solve_y
    )



    # --------------------------------------------------
    # Difficulty / stock status
    # --------------------------------------------------

    if legacy.game.challenge_id is not None:

        challenge_display_names = {
            "draw_3": "3 DRAW",
            "no_undo": "NO UNDO",
            "no_hints": "NO HINTS",
            "all_or_nothing": "ALL OR NOTHING",
        }

        difficulty_name = (
            challenge_display_names.get(
                legacy.game.challenge_id,
                "CHALLENGE"
            )
        )

    else:

        difficulty_display_names = {
            "easy": "EASY",
            "normal": "NORMAL",
            "hard": "HARD",
            "very_hard": "VERY HARD",
            "extreme": "IMPOSSIBLE",
        }

        difficulty_name = (
            difficulty_display_names.get(
                getattr(
                    legacy.game,
                    "difficulty",
                    "normal"
                ),
                "NORMAL"
            )
        )

    multiplier = (
        legacy.game.reward_multiplier
    )

    status_line_1 = (
        f"DIFFICULTY: {difficulty_name} (x{multiplier:.2f})"
    )

    if legacy.game.stock_pass_limit is None:
        status_line_2 = (
            "STOCK PASSES: UNLIMITED"
        )
    else:
        status_line_2 = (
            f"STOCK PASSES: {legacy.game.stock_passes_used}/{legacy.game.stock_pass_limit}"
        )

    difficulty_surface = fonts.ui_small_font.render(
        status_line_1,
        True,
        (255, 230, 0)
    )

    stock_surface = fonts.ui_small_font.render(
        status_line_2,
        True,
        (255, 230, 0)
    )

    if legacy.game.stock_pass_limit is None:
        stock_text = "STOCK: UNLIMITED"
    else:
        stock_text = (
            f"STOCK: "
            f"{legacy.game.stock_passes_used}/"
            f"{legacy.game.stock_pass_limit}"
        )

    status_text = (
        f"{difficulty_name}  "
        f"x{multiplier:.2f}     "
        f"{stock_text}"
        f"     DEAL: {legacy.game.get_deal_status_label()}"
    )



    if legacy.game.challenge_id is not None:
        challenge_display_names = {
            "draw_3":
                "3 DRAW",

            "no_undo":
                "NO UNDO",

            "no_hints":
                "NO HINTS",

            "all_or_nothing":
                "ALL OR NOTHING",
        }

        challenge_name = (
            challenge_display_names.get(
                legacy.game.challenge_id,
                legacy.game.challenge_id.upper()
            )
        )

        status_text += (
            f"     CHALLENGE: "
            f"{challenge_name}"
        )

    status_surface = fonts.ui_small_font.render(
        status_text,
        True,
        (255, 230, 0)
    )

    window.game_surface.blit(
        status_surface,
        (15, 12)
    )

    # --------------------------------------------------
    # Mini buttons
    # --------------------------------------------------

    mouse_pos = state.menu_mouse_pos

    current_hint_icon = (
        assets.hint_button_icon
        if legacy.game.hints_enabled
        else assets.hint_lock_icon
    )

    button_data = [
        (
            game_menu_rect,
            assets.menu_button_icon,
            "Pause Menu",
            "View options or return to menu."
        ),
        (
            game_hint_rect,
            current_hint_icon,
            "Hint",
            get_hint_tooltip_text()
        ),
        (
            game_undo_rect,
            assets.undo_button_icon,
            "Undo",
            get_undo_tooltip_text()
        ),
    ]

    if show_shuffle:
        button_data.append(
            (
                game_shuffle_rect,
                assets.shuffle_button_icon,
                "Shuffle",
                "Shuffle the remaining stock and waste."
            )
        )

    if show_auto_solve:
        button_data.append(
            (
                game_auto_solve_rect,
                assets.autosolve_button_icon,
                "Auto-Solve",
                "Automatically finish the remaining cards."
            )
        )

    hovered_rect = None
    hovered_title = ""
    hovered_subtext = ""

    for rect, icon_image, title, subtext in button_data:

        hovered = rect.collidepoint(
            mouse_pos
        )

        fill_color = (
            (70, 120, 85)
            if hovered
            else (50, 110, 75)
        )

        pygame.draw.rect(
            window.game_surface,
            fill_color,
            rect
        )

        pygame.draw.rect(
            window.game_surface,
            (255, 255, 255),
            rect,
            2
        )

        icon_rect = icon_image.get_rect(
            center=rect.center
        )

        window.game_surface.blit(
            icon_image,
            icon_rect
        )

        if hovered:
            hovered_rect = rect
            hovered_title = title
            hovered_subtext = subtext

    # --------------------------------------------------
    # Hover tooltip
    # --------------------------------------------------

    if hovered_rect is not None:
        tooltip_padding_x = 10
        tooltip_padding_y = 6

        title_surface = fonts.tooltip_font.render(
            hovered_title,
            True,
            (255, 255, 255)
        )

        sub_surface = fonts.tooltip_font.render(
            hovered_subtext,
            True,
            (220, 220, 220)
        )

        tooltip_width = max(
            title_surface.get_width(),
            sub_surface.get_width()
        ) + tooltip_padding_x * 2

        tooltip_height = (
            title_surface.get_height()
            + sub_surface.get_height()
            + tooltip_padding_y * 3
        )

        tooltip_rect = pygame.Rect(
            hovered_rect.right + 8,
            hovered_rect.y,
            tooltip_width,
            tooltip_height
        )

        pygame.draw.rect(
            window.game_surface,
            (15, 25, 15),
            tooltip_rect
        )

        pygame.draw.rect(
            window.game_surface,
            (255, 255, 255),
            tooltip_rect,
            2
        )

        window.game_surface.blit(
            title_surface,
            (
                tooltip_rect.x + tooltip_padding_x,
                tooltip_rect.y + tooltip_padding_y
            )
        )

        window.game_surface.blit(
            sub_surface,
            (
                tooltip_rect.x + tooltip_padding_x,
                tooltip_rect.y + tooltip_padding_y * 2 + title_surface.get_height()
            )
        )

def draw_game_pause_menu():
    overlay = pygame.Surface(
        (
            BASE_WIDTH,
            BASE_HEIGHT
        ),
        pygame.SRCALPHA
    )

    overlay.fill(
        (
            0,
            0,
            0,
            150
        )
    )

    window.game_surface.blit(
        overlay,
        (0, 0)
    )

    panel_rect = pygame.Rect(
        443,
        210,
        480,
        405
    )

    pygame.draw.rect(
        window.game_surface,
        (
            35,
            85,
            60
        ),
        panel_rect
    )

    pygame.draw.rect(
        window.game_surface,
        (
            255,
            255,
            255
        ),
        panel_rect,
        3
    )

    title = fonts.options_title_font.render(
        "PAUSED",
        True,
        (
            255,
            255,
            255
        )
    )

    title_rect = title.get_rect(
        center=(
            panel_rect.centerx,
            260
        )
    )

    window.game_surface.blit(
        title,
        title_rect
    )

    buttons.draw_button(
        pause_resume_rect,
        "Resume"
    )

    buttons.draw_button(
        pause_options_rect,
        "Options"
    )

    return_label = (
        "Return to Career"
        if state.current_game_mode == "career"
        else "Return to Free Play"
        if state.current_game_mode == "free"
        else "Forfeit Race"
        if state.current_game_mode == "head_to_head"
        else "Return to Menu"
    )

    buttons.draw_button(
        pause_menu_rect,
        return_label
    )

    if solitaire_restart_prompt.allowed(legacy.game, state.current_game_mode):
        buttons.draw_button(solitaire_restart_prompt.button, "Restart Hand")

def draw_return_confirmation():
    overlay = pygame.Surface(
        (
            BASE_WIDTH,
            BASE_HEIGHT
        ),
        pygame.SRCALPHA
    )

    overlay.fill(
        (
            0,
            0,
            0,
            150
        )
    )

    window.game_surface.blit(
        overlay,
        (0, 0)
    )

    panel_rect = pygame.Rect(
        430,
        270,
        505,
        220
    )

    pygame.draw.rect(
        window.game_surface,
        (
            35,
            85,
            60
        ),
        panel_rect
    )

    pygame.draw.rect(
        window.game_surface,
        (
            255,
            255,
            255
        ),
        panel_rect,
        3
    )

    return_target_name = (
        "Career Hub"
        if state.current_game_mode == "career"
        else "Free Play"
        if state.current_game_mode == "free"
        else "Career Hub"
        if state.current_game_mode == "head_to_head"
        else "main menu"
    )

    return_prompt = (
        "Forfeit this race and return to Career Hub?"
        if state.current_game_mode == "head_to_head"
        else f"Return to {return_target_name}?"
    )

    prompt = fonts.option_label_font.render(
        return_prompt,
        True,
        (
            255,
            255,
            255
        )
    )

    prompt_rect = prompt.get_rect(
        center=(
            panel_rect.centerx,
            325
        )
    )

    window.game_surface.blit(
        prompt,
        prompt_rect
    )

    buttons.draw_button(
        confirm_yes_rect,
        "Yes"
    )

    buttons.draw_button(
        confirm_no_rect,
        "No"
    )


def instant_win_round():
    """Designer's instant win (was the F8 debug hotkey): fake a completed round.

    Not bound to any key; the F10 debug menu's 'Win this Solitaire round' button
    (Phase 10) calls this.
    """

    legacy.game.round_won = True

    legacy.game.round_summary = {
        "moves": 112,
        "elapsed_seconds": 387,
        "base_score": 5000,
        "move_bonus": 1700,
        "time_bonus": 952,
        "score": 7652,
        "xp_earned": 150,
        "remark": "Efficient work.",
    }

    legacy.game.audio.play_sound(
        "celebration_1"
    )

    legacy.game.start_debug_victory_animation()


def handle_event(event):
    """Old main-loop event branch for STATE_PLAYING."""

    if solitaire_restart_prompt.open:
        solitaire_restart_prompt.event(event, state.game_mouse_pos, legacy.game, sounds.audio)
        return
    if (state.game_pause_menu_open and event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1 and state.game_mouse_pos is not None
            and solitaire_restart_prompt.button.collidepoint(state.game_mouse_pos)
            and solitaire_restart_prompt.allowed(legacy.game, state.current_game_mode)):
        solitaire_restart_prompt.open = True
        state.game_pause_menu_open = False
        sounds.audio.play_sound("button_click")
        return

    # H = Hint. This mirrors the on-screen Hint button and respects
    # difficulty/challenge hint limits.
    if (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_h
            and not state.game_pause_menu_open
            and not state.confirm_return_to_menu
            and not legacy.game.auto_solving
    ):
        if legacy.game.request_hint():
            sounds.audio.play_sound("button_click")

    # ==================================================
    # MOUSE DOWN // MOUSEBUTTONDOWN sorta
    # ==================================================

    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
    ):

        # ----------------------------
        # Pause menu
        # ----------------------------

        if state.game_pause_menu_open:

            if pause_resume_rect.collidepoint(
                    state.game_mouse_pos
            ):
                sounds.audio.play_sound(
                    "button_click"
                )

                state.game_pause_menu_open = False

            elif pause_options_rect.collidepoint(
                    state.game_mouse_pos
            ):
                sounds.audio.play_sound(
                    "button_click"
                )

                state.game_pause_menu_open = False

                state.options_return_state = state_names.STATE_PLAYING

                state.current_state = state_names.STATE_OPTIONS

            elif pause_menu_rect.collidepoint(
                    state.game_mouse_pos
            ):
                sounds.audio.play_sound(
                    "button_click"
                )

                state.game_pause_menu_open = False

                state.confirm_return_to_menu = True

        # ----------------------------
        # Return confirmation
        # ----------------------------

        elif state.confirm_return_to_menu:

            if confirm_yes_rect.collidepoint(
                    state.game_mouse_pos
            ):
                sounds.audio.play_sound(
                    "button_click"
                )

                state.confirm_return_to_menu = False

                if state.current_game_mode == "career":
                    # Abandoned: no activity is pending and the challenge rules end (B6).
                    state.pending_career_activity_index = None
                    state.pending_career_activity_type = None
                    state.pending_career_challenge_id = None
                    legacy.game.clear_challenge()
                    state.current_state = state_names.STATE_CAREER_HUB
                elif state.current_game_mode == "free":
                    legacy.finish_free_play_sandbox()
                    state.current_state = state_names.STATE_FREE_PLAY_SELECT
                elif state.current_game_mode == "head_to_head":
                    head_to_head_screen.finish_head_to_head_race(
                        False,
                        forfeited=True
                    )
                else:
                    state.current_state = state_names.STATE_MENU

            elif confirm_no_rect.collidepoint(
                    state.game_mouse_pos
            ):
                sounds.audio.play_sound(
                    "button_click"
                )

                state.confirm_return_to_menu = False
                state.game_pause_menu_open = True

        # ----------------------------
        # Gameplay menu
        # ----------------------------

        elif game_menu_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.game_pause_menu_open = True

        # ----------------------------
        # Head-to-Head countdown lock
        # ----------------------------

        elif (
                state.current_game_mode == "head_to_head"
                and event_screen.head_to_head_race.is_countdown_active(
                    pygame.time.get_ticks()
                )
        ):
            pass

        # ----------------------------
        # Auto-solve input lock
        # ----------------------------

        elif legacy.game.auto_solving:
            pass


        # ----------------------------
        # SHUFFLE
        # ----------------------------

        elif (
                legacy.game.shuffle_enabled
                and game_shuffle_rect.collidepoint(
            state.game_mouse_pos
        )
        ):
            legacy.game.shuffle_stock()

        # ----------------------------
        # AUTO SOLVE
        # ----------------------------

        elif (
                legacy.game.can_auto_solve()
                and game_auto_solve_rect.collidepoint(
            state.game_mouse_pos
        )
        ):
            legacy.game.auto_solve()



        # ----------------------------
        # Hint
        # ----------------------------

        elif game_hint_rect.collidepoint(
                state.game_mouse_pos
        ):
            if legacy.game.request_hint():
                sounds.audio.play_sound(
                    "button_click"
                )

        # ----------------------------
        # Undo
        # ----------------------------

        elif game_undo_rect.collidepoint(
                state.game_mouse_pos
        ):
            if legacy.game.undo():
                sounds.audio.play_sound(
                    "button_click"
                )

        # ----------------------------
        # Cards
        # ----------------------------

        else:
            legacy.game.handle_mouse_down(
                state.game_mouse_pos,
                event.clicks
            )

    # ==================================================
    # MOUSE MOTION
    # ==================================================

    elif event.type == pygame.MOUSEMOTION:

        legacy.game.handle_mouse_motion(
            state.game_mouse_pos
        )

    # ==================================================
    # MOUSE UP
    # ==================================================

    elif (
            event.type
            == pygame.MOUSEBUTTONUP
            and event.button == 1
    ):

        legacy.game.handle_mouse_up(
            state.game_mouse_pos
        )


def draw():
    """Old draw-chain branch for STATE_PLAYING."""

    legacy.game.update_auto_solve()

    legacy.game.draw()

    draw_gameplay_ui()

    if state.current_game_mode == "head_to_head":
        event_screen.head_to_head_race.update(
            pygame.time.get_ticks()
        )
        draw_head_to_head_hud(
            window.game_surface,
            event_screen.head_to_head_race,
            event_screen.head_to_head_race.player_progress_from_foundations(
                legacy.game.foundations
            ),
            pygame.time.get_ticks(),
            legacy.get_npc_portrait_surface,
            fonts.option_label_font,
            fonts.difficulty_detail_font,
            fonts.ui_small_font,
        )

    if state.game_pause_menu_open:
        draw_game_pause_menu()

    elif state.confirm_return_to_menu:
        draw_return_confirmation()
    if solitaire_restart_prompt.open:
        solitaire_restart_prompt.draw(window.game_surface, state.game_mouse_pos)


def update_solitaire_round():
    """Head-to-Head opponent progress and Solitaire round completion (every frame while playing)."""


    # ----------------------------------------------
    # Head-to-Head opponent race update
    # ----------------------------------------------

    # The opponent races only while the player is at the table: on any other
    # screen (pause -> Options, the F10 menu) the race clock stands still, and
    # the time away does not count when the player comes back.
    if state.current_game_mode == "head_to_head":
        if state.current_state == state_names.STATE_PLAYING:
            now = pygame.time.get_ticks()
            paused_at = event_screen.head_to_head_race.paused_at_ms
            if event_screen.head_to_head_race.resume(now) and paused_at is not None:
                # The player's own round clock started with the race clock (B3):
                # skip the same time away so both keep showing the same race time.
                legacy.game.round_start_ticks += max(0, now - paused_at)
        else:
            event_screen.head_to_head_race.pause(pygame.time.get_ticks())

    if (
            state.current_state == state_names.STATE_PLAYING
            and state.current_game_mode == "head_to_head"
            and legacy.game.round_summary is None
    ):
        event_screen.head_to_head_race.update(
            pygame.time.get_ticks()
        )

        if event_screen.head_to_head_race.winner == "npc":
            head_to_head_screen.finish_head_to_head_race(
                False
            )

    # Player finished the real Klondike board before the NPC. Consume the
    # normal Solitaire summary here so Career does not also award the regular
    # round rewards on top of the Head-to-Head result.
    if (
            state.current_state == state_names.STATE_PLAYING
            and state.current_game_mode == "head_to_head"
            and legacy.game.round_summary is not None
    ):
        head_to_head_round = legacy.game.consume_round_summary()
        head_to_head_screen.finish_head_to_head_race(
            True,
            round_data=head_to_head_round
        )

    # ----------------------------------------------
    # Completed round check
    # ----------------------------------------------

    if state.current_state == state_names.STATE_PLAYING:
        completed_round = (
            legacy.game.consume_round_summary()
        )

        if completed_round is not None:
            state.round_recap_data = (
                completed_round
            )

            leveling.process_achievement_event(
                "solitaire_win",
                moves=state.round_recap_data.get("moves", 0),
                elapsed_seconds=state.round_recap_data.get("elapsed_seconds", 0),
                challenge_id=(
                    state.pending_career_challenge_id
                    if state.current_game_mode == "career"
                    else legacy.game.challenge_id
                ),
            )

            # ----------------------------
            # Decide where this game
            # should return afterward.
            # ----------------------------

            if state.current_game_mode == "career":
                state.post_round_return_state = state_names.STATE_CAREER_HUB
            elif state.current_game_mode == "free":
                state.post_round_return_state = state_names.STATE_FREE_PLAY_SELECT
            else:
                state.post_round_return_state = state_names.STATE_MENU

            # ----------------------------
            # Apply all rewards
            # ----------------------------

            state.last_progression_result = (
                leveling.apply_round_rewards(
                    state.round_recap_data
                )
            )

            if state.current_game_mode == "free":
                legacy.finish_free_play_sandbox()

            # ==========================================
            # CAREER ACTIVITY COMPLETION
            # ==========================================

            if (
                    state.current_game_mode == "career"
                    and state.pending_career_activity_type
                    is not None
            ):

                # ----------------------------
                # Career statistics
                # ----------------------------

                state.career_total_moves += (
                    state.round_recap_data.get(
                        "moves",
                        0
                    )
                )

                if (
                        state.pending_career_activity_type
                        == night.CAREER_ACTIVITY_ROUND
                ):
                    state.career_rounds_won += 1

                elif (
                        state.pending_career_activity_type
                        == night.CAREER_ACTIVITY_CHALLENGE
                ):
                    state.career_challenges_won += 1

                    challenge_names = {
                        "draw_3":
                            "3 Draw",

                        "no_undo":
                            "No Undo",

                        "no_hints":
                            "No Hints",

                        "all_or_nothing":
                            "All or Nothing",
                    }

                    challenge_name = (
                        challenge_names.get(
                            state.pending_career_challenge_id,
                            "Career Challenge"
                        )
                    )

                    news_screen.add_career_news(
                        (
                            f"{state.player_name.upper()} "
                            f"CONQUERS {challenge_name.upper()}"
                        ),
                        (
                            f"{state.player_name} successfully completed "
                            f"the {challenge_name} challenge and "
                            f"continued climbing the competitive "
                            f"Solitaire circuit."
                        ),
                        "competition"
                    )

                # ----------------------------
                # Advance Career calendar
                # ----------------------------

                calendar.advance_career_day(
                    completed=True
                )

                # ----------------------------
                # Clear pending activity
                # ----------------------------

                state.pending_career_activity_index = None
                state.pending_career_activity_type = None
                state.pending_career_challenge_id = None

            state.current_state = state_names.STATE_RECAP


# The old loop drew this screen in its second draw chain (see app/loop.py).
DRAWS_LATE = True
