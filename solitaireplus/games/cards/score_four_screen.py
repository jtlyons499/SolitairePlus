"""Score Four screens: mode select, opponent select and the table (moved out of legacy.py)."""
from solitaireplus.games.solitaire.rules import BASE_WIDTH
from solitaireplus.games.cards.score_four import ScoreFourGame
from solitaireplus.career import career_rewards
from solitaireplus.npc.manager import get_score_four_opponent_choices
import pygame
from solitaireplus.career.rating_events import record_result
from solitaireplus.app import state
from solitaireplus.app import state_names
import sys
import time
from solitaireplus.app.lazy import lazy
score_four_tiers = lazy("solitaireplus.games.cards.score_four_tiers")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
ui_text = lazy("solitaireplus.ui.text")
sounds = lazy("solitaireplus.app.sounds")
night = lazy("solitaireplus.career.events.night")
leveling = lazy("solitaireplus.profile.leveling")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")


score_four_game = ScoreFourGame()




# ==================================================
# SCORE-FOUR RECTS
# ==================================================

score_four_number_rects = []

score_four_operator_rects = {}

score_four_undo_rect = pygame.Rect(
    460,
    700,
    140,
    46
)

score_four_exit_rect = pygame.Rect(
    766,
    700,
    140,
    46
)

score_four_complete_rect = pygame.Rect(
    BASE_WIDTH // 2 - 100,
    585,
    200,
    48
)

score_four_solo_rect = pygame.Rect(
    BASE_WIDTH // 2 - 260,
    330,
    220,
    70
)

score_four_competitive_rect = pygame.Rect(
    BASE_WIDTH // 2 + 40,
    330,
    220,
    70
)

score_four_mode_return_rect = pygame.Rect(
    BASE_WIDTH // 2 - 90,
    470,
    180,
    46
)

score_four_match_continue_rect = pygame.Rect(
    BASE_WIDTH // 2 - 100,
    585,
    200,
    48
)

score_four_hint_rect = pygame.Rect(
    BASE_WIDTH // 2 + 300,
    700,
    140,
    46
)

score_four_opponent_rects = [
    pygame.Rect(
        240,
        180,
        390,
        180
    ),

    pygame.Rect(
        735,
        180,
        390,
        180
    ),

    pygame.Rect(
        240,
        405,
        390,
        180
    ),

    pygame.Rect(
        735,
        405,
        390,
        180
    ),
]

score_four_opponent_return_rect = pygame.Rect(
    BASE_WIDTH // 2 - 90,
    650,
    180,
    46
)



def get_score_four_npc_progress():

    if (
            score_four_game.mode
            != "competitive"
    ):
        return 0.0

    if score_four_game.round_complete:
        return 1.0

    elapsed = (
        time.monotonic()
        - score_four_game.round_start_time
    )

    if (
            score_four_game.npc_solve_time_seconds
            <= 0
    ):
        return 0.0

    return max(
        0.0,
        min(
            1.0,
            elapsed
            / score_four_game.npc_solve_time_seconds
        )
    )

def draw_score_four_opponent_select():
    from solitaireplus.games.cards.score_four_ui import background, logo, text
    background(window.game_surface)
    logo(window.game_surface)
    text(window.game_surface, 'Choose a rival', (683, 140), 32, center=True)
    text(window.game_surface, 'Win rewards include your Strategy rating adjustment', (683, 614), 24, center=True)

    for index, npc in enumerate(
            state.score_four_opponent_choices
    ):

        if index >= len(
                score_four_opponent_rects
        ):
            break

        rect = (
            score_four_opponent_rects[
                index
            ]
        )

        hovered = (
            state.game_mouse_pos is not None
            and rect.collidepoint(
                state.game_mouse_pos
            )
        )

        # ==========================================
        # Panel background
        # ==========================================

        panel = pygame.Surface(
            (
                rect.width,
                rect.height
            ),
            pygame.SRCALPHA
        )

        if hovered:

            panel.fill(
                (
                    255,
                    255,
                    255,
                    55
                )
            )

        else:

            panel.fill(
                (
                    0,
                    0,
                    0,
                    150
                )
            )

        window.game_surface.blit(
            panel,
            rect.topleft
        )

        pygame.draw.rect(
            window.game_surface,
            (
                210,
                210,
                210
            ),
            rect,
            2
        )

        # ==========================================
        # Portrait
        # ==========================================

        portrait_rect = pygame.Rect(
            rect.x + 18,
            rect.y + 22,
            105,
            105
        )

        legacy.draw_npc_portrait(
            npc,
            portrait_rect,
            "score_four"
        )

        # ==========================================
        # Name
        # ==========================================

        name_surface = (
            fonts.option_label_font.render(
                npc["name"],
                True,
                (
                    255,
                    255,
                    255
                )
            )
        )

        window.game_surface.blit(
            name_surface,
            (
                rect.x + 145,
                rect.y + 22
            )
        )

        # ==========================================
        # Tier
        # ==========================================

        tier_text = (
            score_four_tiers.SCORE_FOUR_TIER_DISPLAY_NAMES.get(
                npc["skill_tier"],
                npc["skill_tier"]
            ).upper()
        )

        tier_surface = (
            fonts.score_four_round_font.render(
                tier_text,
                True,
                (
                    255,
                    230,
                    0
                )
            )
        )

        window.game_surface.blit(
            tier_surface,
            (
                rect.x + 145,
                rect.y + 60
            )
        )

        # ==========================================
        # Location
        # ==========================================

        location_surface = (
            fonts.difficulty_detail_font.render(
                npc["hometown"],
                True,
                (
                    220,
                    220,
                    220
                )
            )
        )

        window.game_surface.blit(
            location_surface,
            (
                rect.x + 145,
                rect.y + 95
            )
        )

        if state.current_game_mode != "free":
            gain = career_rewards.preview_competitive_rating("score_four", npc, True)
            loss = career_rewards.preview_competitive_rating("score_four", npc, False)
            reward_text = f"Win {gain:+d} / Loss {loss:+d} Strategy"
        else:
            reward_text = "Practice • No rating changes"
        reward_label = ui_text.get_font(None, 24).render(reward_text, True, (225, 239, 244))
        window.game_surface.blit(reward_label, reward_label.get_rect(center=(rect.centerx, rect.bottom - 24)))

    buttons.draw_menu_button(
        score_four_opponent_return_rect,
        "Return",
        state.game_mouse_pos,
        font=fonts.difficulty_detail_font
    )

def draw_score_four_npc_panel():

    if (
            score_four_game.mode
            != "competitive"
            or state.score_four_opponent_npc is None
    ):
        return

    npc_panel = pygame.Rect(
        1040,
        180,
        285,
        235
    )

    pygame.draw.rect(
        window.game_surface,
        (
            25,
            45,
            30
        ),
        npc_panel
    )

    pygame.draw.rect(
        window.game_surface,
        (
            255,
            255,
            255
        ),
        npc_panel,
        2
    )

    avatar_rect = pygame.Rect(
        npc_panel.x + 15,
        npc_panel.y + 15,
        80,
        80
    )

    legacy.draw_npc_portrait(
        state.score_four_opponent_npc,
        avatar_rect,
        "score_four"
    )

    # ==================================================
    # NPC name
    # ==================================================

    npc_name_surface = (
        fonts.score_four_npc_font.render(
            state.score_four_opponent_npc[
                "name"
            ],
            True,
            (
                255,
                255,
                255
            )
        )
    )

    window.game_surface.blit(
        npc_name_surface,
        (
            npc_panel.x + 110,
            npc_panel.y + 20
        )
    )

    # ==================================================
    # Skill display
    # ==================================================

    tier_name = (
        score_four_tiers.SCORE_FOUR_TIER_DISPLAY_NAMES.get(
            state.score_four_opponent_npc[
                "skill_tier"
            ],
            state.score_four_opponent_npc[
                "skill_tier"
            ]
        )
    )

    tier_surface = (
        fonts.score_four_round_font.render(
            tier_name,
            True,
            (
                255,
                230,
                0
            )
        )
    )

    window.game_surface.blit(
        tier_surface,
        (
            npc_panel.x + 110,
            npc_panel.y + 60
        )
    )

    # ==================================================
    # Status
    # ==================================================

    if score_four_game.round_complete:

        thinking_text = "Finished"

    else:

        thinking_text = "Thinking..."

    thinking_surface = (
        fonts.score_four_round_font.render(
            thinking_text,
            True,
            (
                220,
                220,
                220
            )
        )
    )

    window.game_surface.blit(
        thinking_surface,
        (
            npc_panel.x + 15,
            npc_panel.y + 125
        )
    )

    # ==================================================
    # Progress bar
    # ==================================================

    progress = (
        get_score_four_npc_progress()
    )

    bar_rect = pygame.Rect(
        npc_panel.x + 15,
        npc_panel.y + 170,
        npc_panel.width - 30,
        24
    )

    pygame.draw.rect(
        window.game_surface,
        (
            80,
            80,
            80
        ),
        bar_rect
    )

    fill_rect = pygame.Rect(
        bar_rect.x,
        bar_rect.y,
        int(
            bar_rect.width
            * progress
        ),
        bar_rect.height
    )

    pygame.draw.rect(
        window.game_surface,
        (
            220,
            220,
            220
        ),
        fill_rect
    )

    pygame.draw.rect(
        window.game_surface,
        (
            255,
            255,
            255
        ),
        bar_rect,
        2
    )



def settle_score_four_session_result():
    """Bank the completed result once, before the player dismisses the screen."""
    if score_four_game.reward_claimed:
        return
    if score_four_game.mode == "solo" and score_four_game.session_complete:
        rating_change = career_rewards.award_career_rating('score_four', {'easy': 30, 'standard': 50, 'difficult': 70, 'extreme': 90}[score_four_game.difficulty])
        if state.current_game_mode == 'career':
            record_result(state.career_rating_results, 'score_four', 1.0, rating_change)
        career_rewards.award_fans_for_rating_win(rating_change, 'Score-Four completion')
        leveling.process_achievement_event('score_four_win', mode='solo')
        leveling.award_game_xp('score_four_solo', won=True)
        night.record_career_event_result('score_four', won=True, mode='solo')
        score_four_game.reward_claimed = True
        state.career_event_has_activity = True
    elif score_four_game.mode == "competitive" and score_four_game.match_complete:
        player_won_match = score_four_game.match_winner == 'player'
        rating_change = career_rewards.rate_competitive_game('score_four', state.score_four_opponent_npc, player_won_match)
        if player_won_match:
            career_rewards.award_fans_for_rating_win(rating_change, 'Competitive Score-Four win')
            leveling.process_achievement_event('score_four_win', mode='competitive')
        leveling.award_game_xp('score_four_competitive', won=player_won_match)
        night.record_career_event_result('score_four', won=player_won_match, mode='competitive', opponent=state.score_four_opponent_npc.get('name') if isinstance(state.score_four_opponent_npc, dict) else 'NPC', opponent_tier=state.score_four_opponent_npc.get('skill_tier') if isinstance(state.score_four_opponent_npc, dict) else 'mid', rating_reward=rating_change)
        score_four_game.reward_claimed = True
        state.career_event_has_activity = True
    else:
        return
    score_four_game.last_rating_change = rating_change


def score_four_namespace():
    """legacy.game_namespace() (the old globals()) with this module added last: score_four_ui looks
    up the Score Four engine, rects and helpers by name, and they live here now. Writes still go to
    state, and every name the old namespace had is still found first."""
    namespace = legacy.game_namespace()
    namespace.maps.append(vars(sys.modules[__name__]))
    return namespace


def draw_score_four():
    from solitaireplus.games.cards.score_four_ui import draw_score_four_table
    settle_score_four_session_result()
    draw_score_four_table(window.game_surface, score_four_game, state.game_mouse_pos, score_four_namespace())

def draw_score_four_mode_select():
    from solitaireplus.games.cards.score_four_ui import draw_difficulty_select, draw_mode_select
    if score_four_game.difficulty_menu:
        draw_difficulty_select(window.game_surface, state.game_mouse_pos, score_four_namespace())
    else:
        draw_mode_select(window.game_surface, score_four_game, state.game_mouse_pos, score_four_namespace())


def loop_event_score_four_mode_select(event):
    """Old main-loop event branch for STATE_SCORE_FOUR_MODE_SELECT."""

    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and score_four_game.rating_info_open:
        score_four_game.rating_info_open = False
        return
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.game_mouse_pos is not None:
        from solitaireplus.games.cards.score_four_ui import handle_rating_info_click
        if handle_rating_info_click(state.game_mouse_pos, score_four_game):
            sounds.audio.play_sound("button_click")
            return

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.game_mouse_pos is not None:
        from solitaireplus.games.cards.score_four_ui import LAYOUT_RECT, toggle_layout, play_control_sound
        if not score_four_game.difficulty_menu and LAYOUT_RECT.collidepoint(state.game_mouse_pos):
            toggle_layout(score_four_game)
            play_control_sound(sounds.audio, "select")
            return

    if score_four_game.difficulty_menu and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        from solitaireplus.games.cards.score_four_ui import difficulty_action
        choice = difficulty_action(state.menu_mouse_pos)
        if choice == "back":
            score_four_game.difficulty_menu = False
        elif choice:
            score_four_game.difficulty_menu = False
            score_four_game.start_solo_session(choice)
            state.current_state = state_names.STATE_SCORE_FOUR
        sounds.audio.play_sound("button_click")
        return

    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.menu_mouse_pos is not None
    ):

        # ------------------------------------------
        # Solo
        # ------------------------------------------

        if (
                score_four_solo_rect.collidepoint(
                    state.menu_mouse_pos
                )
        ):

            sounds.audio.play_sound(
                "button_click"
            )

            score_four_game.difficulty_menu = True

        # ------------------------------------------
        # Competitive
        # ------------------------------------------

        elif (
                score_four_competitive_rect.collidepoint(
                    state.menu_mouse_pos
                )
        ):

            state.score_four_opponent_choices = (
                get_score_four_opponent_choices()
            )

            if state.score_four_opponent_npc is not None:
                opponent_name = (
                    state.score_four_opponent_npc["name"]
                )
            else:
                opponent_name = "NPC"

            sounds.audio.play_sound(
                "button_click"
            )

            state.current_state = state_names.STATE_SCORE_FOUR_OPPONENT_SELECT

        # ------------------------------------------
        # Return
        # ------------------------------------------

        elif (
                score_four_mode_return_rect.collidepoint(
                    state.menu_mouse_pos
                )
        ):

            sounds.audio.play_sound(
                "button_click"
            )

            if state.current_game_mode == "free":
                legacy.finish_free_play_sandbox()
                state.current_state = state_names.STATE_FREE_PLAY_SELECT
            else:
                state.current_state = state_names.STATE_CAREER_EVENT_SELECT


def loop_event_score_four_opponent_select(event):
    """Old main-loop event branch for STATE_SCORE_FOUR_OPPONENT_SELECT."""

    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):

        opponent_clicked = False

        # ------------------------------------------
        # Opponent cards
        # ------------------------------------------

        for state.index, state.rect in enumerate(
                score_four_opponent_rects
        ):

            if (
                    state.index
                    < len(
                state.score_four_opponent_choices
            )
                    and state.rect.collidepoint(
                state.game_mouse_pos
            )
            ):
                state.score_four_opponent_npc = (
                    state.score_four_opponent_choices[
                        state.index
                    ]
                )

                sounds.audio.play_sound(
                    "button_click"
                )

                opponent_clicked = True

                score_four_game.start_competitive_session(
                    skill_tier=(
                        state.score_four_opponent_npc[
                            "skill_tier"
                        ]
                    ),
                    rating=state.score_four_opponent_npc.get("career_ratings", {}).get("score_four"),
                )

                state.current_state = state_names.STATE_SCORE_FOUR

                break

        # ------------------------------------------
        # Return
        # ------------------------------------------

        if (
                not opponent_clicked
                and score_four_opponent_return_rect.collidepoint(
            state.game_mouse_pos
        )
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.current_state = state_names.STATE_SCORE_FOUR_MODE_SELECT


def loop_event_score_four(event):
    """Old main-loop event branch for STATE_SCORE_FOUR."""

    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and score_four_game.rating_info_open:
        score_four_game.rating_info_open = False
        return
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.game_mouse_pos is not None:
        from solitaireplus.games.cards.score_four_ui import handle_rating_info_click
        if handle_rating_info_click(state.game_mouse_pos, score_four_game):
            sounds.audio.play_sound("button_click")
            return

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.game_mouse_pos is not None:
        from solitaireplus.games.cards.score_four_ui import LAYOUT_RECT, toggle_layout, play_control_sound
        if not score_four_game.difficulty_menu and LAYOUT_RECT.collidepoint(state.game_mouse_pos):
            toggle_layout(score_four_game)
            play_control_sound(sounds.audio, "select")
            return

    if (

            event.type

            == pygame.MOUSEBUTTONDOWN

            and event.button == 1

    ):

        # ==========================================

        # Training complete

        # ==========================================

        if (
                score_four_game.mode == "solo"
                and score_four_game.session_complete
        ):

            if score_four_complete_rect.collidepoint(

                    state.menu_mouse_pos

            ):

                settle_score_four_session_result()

                sounds.audio.play_sound(

                    "button_click"

                )

                if state.current_game_mode == "free":
                    legacy.finish_free_play_sandbox()
                    state.current_state = state_names.STATE_FREE_PLAY_SELECT
                else:
                    state.current_state = state_names.STATE_CAREER_EVENT_SELECT

            return

        # ==========================================
        # Competitive match complete
        # ==========================================

        if (
                score_four_game.mode == "competitive"
                and score_four_game.match_complete
        ):

            if (
                    score_four_match_continue_rect
                            .collidepoint(
                        state.menu_mouse_pos
                    )
            ):

                settle_score_four_session_result()

                sounds.audio.play_sound(
                    "button_click"
                )

                if state.current_game_mode == "free":
                    legacy.finish_free_play_sandbox()
                    state.current_state = state_names.STATE_FREE_PLAY_SELECT
                else:
                    state.current_state = state_names.STATE_CAREER_EVENT_SELECT

            return

        # ==========================================
        # Competitive round result input lock
        # ==========================================

        if (
                score_four_game.mode == "competitive"
                and score_four_game.round_complete
        ):
            from solitaireplus.games.cards.score_four_ui import ROUND_CONTINUE_RECT
            if state.game_mouse_pos is not None and ROUND_CONTINUE_RECT.collidepoint(state.game_mouse_pos):
                if score_four_game.continue_competitive_round():
                    sounds.audio.play_sound("button_click")
            return

        # ------------------------------------------
        # Number tiles
        # ------------------------------------------

        reset_rect = legacy.game_namespace().get("score_four_reset_rect")
        if reset_rect is not None and state.menu_mouse_pos is not None and reset_rect.collidepoint(state.menu_mouse_pos):
            if score_four_game.reset_current_puzzle(): play_control_sound(sounds.audio, "reset")
            return

        clicked_number = False

        for state.index, state.rect in enumerate(
                score_four_number_rects
        ):

            if state.rect.collidepoint(
                    state.menu_mouse_pos
            ):
                score_four_game.select_number(
                    state.index
                )

                if not score_four_game.round_complete:
                    play_control_sound(sounds.audio, "select")
                clicked_number = True
                break

        if clicked_number:
            pass

        # ------------------------------------------
        # Operators
        # ------------------------------------------

        else:

            clicked_operator = False

            for (
                    operator_id,
                    state.rect
            ) in score_four_operator_rects.items():

                if state.rect.collidepoint(
                        state.menu_mouse_pos
                ):
                    score_four_game.select_operator(
                        operator_id
                    )

                    play_control_sound(sounds.audio, "operator")
                    clicked_operator = True
                    break

            if clicked_operator:
                pass

            elif (
                    score_four_game.solo_hint_available()
                    and score_four_hint_rect.collidepoint(
                state.menu_mouse_pos
            )
            ):

                if score_four_game.request_solo_hint():
                    play_control_sound(sounds.audio, "hint")

            # --------------------------------------
            # Undo
            # --------------------------------------

            elif score_four_undo_rect.collidepoint(
                    state.menu_mouse_pos
            ):

                score_four_game.undo()
                play_control_sound(sounds.audio, "undo")

            # --------------------------------------
            # Exit
            # --------------------------------------

            elif score_four_exit_rect.collidepoint(
                    state.menu_mouse_pos
            ):

                if state.current_game_mode == "free":
                    legacy.finish_free_play_sandbox()
                    state.current_state = state_names.STATE_FREE_PLAY_SELECT
                else:
                    state.current_state = state_names.STATE_CAREER_EVENT_SELECT


def loop_draw_score_four_mode_select():
    """Old draw-chain branch for STATE_SCORE_FOUR_MODE_SELECT."""

    draw_score_four_mode_select()


def loop_draw_score_four():
    """Old draw-chain branch for STATE_SCORE_FOUR."""

    score_four_game.update()

    draw_score_four()


def loop_draw_score_four_opponent_select():
    """Old draw-chain branch for STATE_SCORE_FOUR_OPPONENT_SELECT."""

    draw_score_four_opponent_select()
