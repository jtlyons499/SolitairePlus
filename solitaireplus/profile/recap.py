"""Solitaire round recap screen (moved out of legacy.py)."""
from solitaireplus.games.solitaire.rules import BASE_WIDTH
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
level_up = lazy("solitaireplus.profile.level_up")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")


# ----------------------------
# Round recap buttons
# ----------------------------

recap_yes_rect = pygame.Rect(
    515,
    655,
    150,
    55
)

recap_no_rect = pygame.Rect(
    700,
    655,
    150,
    55
)

# ==================================================
# TIME HELPERS
# ==================================================

def format_round_time(
    seconds
):
    minutes = (
        seconds // 60
    )

    remaining_seconds = (
        seconds % 60
    )

    return (
        f"{minutes}:"
        f"{remaining_seconds:02d}"
    )

# ==================================================
# ROUND RECAP
# ==================================================

def draw_round_recap():
    window.game_surface.fill(
        (
            20,
            70,
            45
        )
    )

    if state.round_recap_data is None:
        return

    # ----------------------------
    # Heading
    # ----------------------------

    if (
            state.round_recap_data.get(
                "challenge_id"
            )
            is not None
    ):
        recap_title_text = (
            "CHALLENGE COMPLETE"
        )

    else:
        recap_title_text = (
            "ROUND COMPLETE"
        )

    title = fonts.menu_title_font.render(
        recap_title_text,
        True,
        (
            255,
            255,
            255
        )
    )

    challenge_id = state.round_recap_data.get(
        "challenge_id"
    )

    if challenge_id is not None:
        challenge_names = {
            "draw_3": "3 Draw",
            "no_undo": "No Undo",
            "no_hints": "No Hints",
            "all_or_nothing": "All or Nothing",
        }

        challenge_surface = (
            fonts.option_label_font.render(
                challenge_names.get(
                    challenge_id,
                    challenge_id
                ),
                True,
                (
                    255,
                    215,
                    0
                )
            )
        )

        challenge_rect = (
            challenge_surface.get_rect(
                center=(
                    BASE_WIDTH // 2,
                    150
                )
            )
        )

        window.game_surface.blit(
            challenge_surface,
            challenge_rect
        )

    # ----------------------------
    # Stats
    # ----------------------------

    stats = [
        (
            "Time",
            format_round_time(
                state.round_recap_data[
                    "elapsed_seconds"
                ]
            )
        ),
        (
            "Moves",
            str(
                state.round_recap_data[
                    "moves"
                ]
            )
        ),
        (
            "Move Bonus",
            f"+{state.round_recap_data['move_bonus']:,}"
        ),
        (
            "Time Bonus",
            f"+{state.round_recap_data['time_bonus']:,}"
        ),
        (
            "Score",
            f"{state.round_recap_data['score']:,}"
        ),
        (
            "XP Earned",
            f"+{state.round_recap_data['xp_earned']:,}"
        ),
        (
            "SP Earned",
            f"+{state.round_recap_data.get('sp_earned', 0):,}"
        ),
    ]

    if state.current_game_mode == "career":
        stats.append(
            (
                "Cash Earned",
                f"+${state.round_recap_data.get('cash_earned', 0):,}"
            )
        )

        stats.append(
            (
                "Rating",
                f"+{state.round_recap_data.get('rating_change', 0):,}"
            )
        )

        stats.append(
            (
                "Fans",
                f"+{state.round_recap_data.get('fans_earned', 0):,}"
            )
        )

    start_y = 175

    for index, (
        label_text,
        value_text

    ) in enumerate(stats):
        y = (
                start_y
                + index * 45
        )

        label = fonts.option_label_font.render(
            label_text,
            True,
            (
                210,
                210,
                210
            )
        )

        value = fonts.option_label_font.render(
            value_text,
            True,
            (
                255,
                255,
                255
            )
        )

        window.game_surface.blit(
            label,
            (
                450,
                y
            )
        )

        value_rect = value.get_rect(
            right=900,
            y=y
        )

        window.game_surface.blit(
            value,
            value_rect
        )

    # ----------------------------
    # Remark
    # ----------------------------

    remark = fonts.option_label_font.render(
        state.round_recap_data[
            "remark"
        ],
        True,
        (
            255,
            255,
            255
        )
    )

    remark_rect = remark.get_rect(
        center=(
            BASE_WIDTH // 2,
            585
        )
    )

    window.game_surface.blit(
        remark,
        remark_rect
    )

    # ----------------------------
    # Return to menu prompt
    # ----------------------------

    prompt = fonts.option_label_font.render(
        "Leave Table?",
        True,
        (
            255,
            255,
            255
        )
    )

    prompt_rect = prompt.get_rect(
        center=(
            BASE_WIDTH // 2,
            620
        )
    )

    window.game_surface.blit(
        prompt,
        prompt_rect
    )

    buttons.draw_button(
        recap_yes_rect,
        "Yes"
    )

    buttons.draw_button(
        recap_no_rect,
        "No"
    )


def handle_event(event):
    """Old main-loop event branch for STATE_RECAP."""

    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
    ):
        if recap_yes_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            # If this win earned levels,
            # show them before returning
            # to the main menu.
            if (
                    state.last_progression_result
                    and state.last_progression_result[
                "level_up_screens"
            ]
            ):
                # Extend, not replace: level-ups queued before this
                # recap (other games, battles) must still show (B7).
                state.level_up_queue.extend(
                    state.last_progression_result[
                        "level_up_screens"
                    ]
                )

                level_up.advance_level_up_screen()


            else:

                state.current_state = state.post_round_return_state

        elif recap_no_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            if state.current_game_mode == "career":
                # B5: the career round already used its calendar day and
                # cleared the pending activity, so a new deal here would pay
                # full career rewards for free. Return to the Career hub
                # instead, without dealing (designer decision 2026-11-15).
                state.post_round_return_state = state_names.STATE_CAREER_HUB
            else:
                # Stay at the table and deal another hand. If the completed
                # round earned one or more levels, show those screens first
                # and then return directly to the fresh deal.
                legacy.game.new_game()
                state.post_round_return_state = state_names.STATE_PLAYING

            if (
                    state.last_progression_result
                    and state.last_progression_result.get("level_up_screens")
            ):
                # Extend, not replace (B7): keep level-ups queued earlier.
                state.level_up_queue.extend(
                    state.last_progression_result["level_up_screens"]
                )
                level_up.advance_level_up_screen()
            else:
                state.current_state = state.post_round_return_state


def draw():
    """Old draw-chain branch for STATE_RECAP."""

    draw_round_recap()
