"""Texas Hold'em table UI: the main table drawing, the session reset and the click routing.

The table UI is split into topic modules in this package (one module's functions split
across modules; every function moved verbatim and keeps its name):
    holdem_ui_state.py     shared state (_ui), action names, log sizes, colours, HUD rects,
                           the log and chat histories, fonts and chip images
    holdem_ui_widgets.py   translucent panels, buttons and fitted text
    holdem_ui_options.py   the buy-in screen, the Options overlay, table settings and delays
    holdem_ui_pot.py       the pot stack, chip and payout animations, the showdown banner
    holdem_ui_cards.py     card faces and backs, card deal and flip animations
    holdem_ui_log.py       the GAME LOG / TABLE CHAT panel and Quick Chat
    holdem_ui_controls.py  the bet slider, the manual bet entry and the action panel
    holdem_ui_hud.py       the player's hand text, dealer / blind badges and the player HUD
This module keeps reset_texas_holdem_ui_session, draw_texas_holdem and get_texas_holdem_action.

Every module-level name holdem_ui.py had is still importable from here: holdem_screen.py, the
variant screens and multiplayer/ import them from this module. Each piece of module state
(_ui, the histories, the rects) is made once, in the module that owns it; this module and the
others import the same object. The first import block below is the original one, in its
original order (this module is imported in start-up, app/startup.py).
"""
from solitaireplus.app import paths
from solitaireplus.app import state
from solitaireplus.career.session_summary import poker_session_status
from solitaireplus.games.poker.core import collected_uncontested
from solitaireplus.games.poker.recap import draw_recap, get_recap_action, pot_explanation, received_total
import math
from types import SimpleNamespace

import pygame

from solitaireplus.games.poker.speech import (
    PokerSpeechOverlay,
    is_poker_chat_popups_enabled,
    set_poker_chat_popups_enabled,
)
from solitaireplus.games.poker.log_rows import log_rows, visible_log_rows
from solitaireplus.games.poker.ui_assets import draw_poker_logo
from solitaireplus.games.poker.quick_chat import (
    quick_chat_options_for_game,
    quick_chat_target_options,
    quick_chat_availability,
    submit_holdem_quick_chat,
)
from solitaireplus.ui import text as ui_text

# The names from the topic modules (see the docstring), imported here so that
# holdem_ui.<name> still works for every one of them.
from solitaireplus.games.poker.holdem_ui_state import (
    _ui,
    ACTION_DEAL,
    ACTION_FLOP,
    ACTION_TURN,
    ACTION_RIVER,
    ACTION_SHOWDOWN,
    ACTION_RETURN,
    ACTION_FOLD,
    ACTION_CHECK_CALL,
    ACTION_BET_RAISE,
    ACTION_NEXT_HAND,
    HOLDEM_LOG_RECT,
    HOLDEM_LOG_TEXT_WIDTH,
    HOLDEM_LOG_TEXT_HEIGHT,
    HOLDEM_LOG_LINE_STEP,
    HOLDEM_LOG_MIN_SQUASH,
    get_poker_chip_images,
    clear_holdem_fonts,
    _holdem_fonts_quit_hook,
    get_holdem_fonts,
    WHITE,
    BLACK,
    TABLE_GREEN,
    TABLE_EDGE,
    PANEL_DARK,
    holdem_next_hand_rect,
    holdem_action_panel_rect,
    holdem_fold_rect,
    holdem_call_rect,
    holdem_raise_rect,
    holdem_slider_rect,
    holdem_manual_bet_rect,
    holdem_min_rect,
    holdem_half_rect,
    holdem_pot_rect,
    holdem_max_rect,
    holdem_options_rect,
    holdem_exit_rect,
    holdem_log_history,
    holdem_chat_history,
    _holdem_speech_overlay,
    holdem_quick_chat_pending,
)
from solitaireplus.games.poker.holdem_ui_widgets import (
    draw_translucent_panel,
    draw_modern_button,
    blit_text_fit,
    draw_holdem_glossy_button,
)
from solitaireplus.games.poker.holdem_ui_options import (
    holdem_options_panel_rect,
    holdem_options_close_rect,
    holdem_speed_slow_rect,
    holdem_speed_normal_rect,
    holdem_speed_fast_rect,
    holdem_auto_deal_toggle_rect,
    holdem_chat_toggle_rect,
    holdem_chat_popups_toggle_rect,
    holdem_buy_in_panel_rect,
    holdem_buy_in_25_rect,
    holdem_buy_in_50_rect,
    holdem_buy_in_75_rect,
    holdem_buy_in_max_rect,
    holdem_buy_in_back_rect,
    get_holdem_buy_in_amounts,
    get_texas_holdem_buy_in_action,
    is_holdem_options_open,
    toggle_holdem_options,
    close_holdem_options,
    is_holdem_auto_deal_enabled,
    is_holdem_table_chat_enabled,
    is_holdem_table_chat_popups_enabled,
    get_holdem_npc_delay,
    get_holdem_street_delay,
    get_holdem_next_hand_delay,
    handle_holdem_options_click,
    draw_texas_holdem_buy_in,
    draw_holdem_options_overlay,
)
from solitaireplus.games.poker.holdem_ui_pot import (
    HOLDEM_CHIP_FX_DURATION,
    HOLDEM_WAGER_SWEEP_DELAY,
    HOLDEM_WAGER_SWEEP_DURATION,
    HOLDEM_PAYOUT_FX_DURATION,
    _holdem_chip_key_for_amount,
    _holdem_pot_chip_count,
    draw_holdem_pot_stack,
    get_holdem_payout_fx_progress,
    draw_holdem_payout_animation,
    draw_holdem_showdown_banner,
    sync_holdem_chip_fx_context,
    get_holdem_chip_fx,
    get_holdem_chip_ease,
    get_holdem_wager_sweep_progress,
    draw_holdem_chip_chunks,
)
from solitaireplus.games.poker.holdem_ui_cards import (
    get_card_key,
    draw_card_face,
    draw_card_back,
    sync_holdem_card_fx,
    get_holdem_card_fx_progress,
    get_holdem_eased_progress,
    draw_holdem_popping_card_face,
    draw_holdem_popping_card_back,
    draw_holdem_flipping_card,
)
from solitaireplus.games.poker.holdem_ui_log import (
    _get_holdem_quick_chat_rects,
    _queue_holdem_quick_chat_responses,
    _pump_holdem_quick_chat_responses,
    handle_holdem_panel_click,
    get_holdem_log_rows,
    _holdem_log_line_squashes_legibly,
    squash_holdem_log_text,
    get_holdem_log_layout,
    scroll_holdem_log,
    add_holdem_chat_message,
    update_holdem_log,
    draw_holdem_log_panel,
)
from solitaireplus.games.poker.holdem_ui_controls import (
    set_holdem_bet_slider_from_mouse,
    drag_holdem_bet_slider,
    stop_holdem_bet_slider_drag,
    update_holdem_bet_slider,
    clear_holdem_manual_bet,
    handle_holdem_manual_bet_click,
    handle_holdem_manual_bet_key,
    get_holdem_manual_bet_amount,
    get_holdem_bet_amount,
    draw_holdem_side_panel,
)
from solitaireplus.games.poker.holdem_ui_hud import (
    get_holdem_player_hand_text,
    get_holdem_position_labels,
    draw_holdem_position_badges,
    draw_holdem_player_hud,
)


def reset_texas_holdem_ui_session():
    """Forget the last session's table UI (like reset_five_card_draw_ui_session).

    Clears the chat history in place (the module list is never rebound),
    queued quick-chat replies and speech bubbles, and resets the chat
    scroll and unread marker. A half-typed manual bet, a bet-slider drag
    and an open quick-chat menu do not carry over into the new session.
    """

    holdem_chat_history.clear()
    holdem_quick_chat_pending.clear()
    _holdem_speech_overlay.clear()
    state.holdem_chat_scroll = 0
    state.holdem_chat_unread = False
    clear_holdem_manual_bet()
    stop_holdem_bet_slider_drag()
    state.holdem_quick_chat_open = False
    state.holdem_quick_chat_target_mode = None


# ==================================================
# MAIN DRAW
# ==================================================

def draw_texas_holdem(
        game_surface,
        mouse_pos,
        holdem_game,
        card_fronts,
        card_back,
        draw_submenu_background,
        draw_submenu_title,
        draw_menu_button,
        draw_npc_portrait,
        title_font,
        label_font,
        detail_font,
        player_name,
        felt_surface,
        next_hand_seconds=None
):
    if _ui.holdem_active_game is not holdem_game:
        state.holdem_quick_chat_open = False
        state.holdem_quick_chat_target_mode = None
        holdem_quick_chat_pending.clear()
        _ui.holdem_active_game = holdem_game

    _pump_holdem_quick_chat_responses()

    # If the hand changes context while the menu is open, immediately leave a
    # target submenu that no longer belongs to the current situation.
    if state.holdem_quick_chat_target_mode and not quick_chat_target_options(holdem_game, state.holdem_quick_chat_target_mode):
        state.holdem_quick_chat_target_mode = None

    poker_chip_images = (
        get_poker_chip_images()
    )

    card_fx_kind, card_fx_elapsed = (
        sync_holdem_card_fx(
            holdem_game
        )
    )

    sync_holdem_chip_fx_context(
        holdem_game
    )

    wager_sweep_progress = (
        get_holdem_wager_sweep_progress(
            holdem_game
        )
    )

    # ==================================================
    # Background
    # ==================================================

    draw_submenu_background(
        overlay_alpha=110
    )

    holdem_fonts = get_holdem_fonts()

    holdem_title_font = holdem_fonts["title"]
    holdem_name_font = holdem_fonts["name"]
    holdem_small_font = holdem_fonts["small"]
    holdem_tiny_font = holdem_fonts["tiny"]



    # ==================================================
    # Table
    # ==================================================

    table_rect = pygame.Rect(
        233,
        105,
        900,
        460
    )

    wager_sweep_target = (
        table_rect.centerx,
        235
    )

    pygame.draw.ellipse(
        game_surface,
        TABLE_EDGE,
        table_rect
    )

    inner_table_rect = (
        table_rect.inflate(
            -30,
            -30
        )
    )

    if felt_surface is not None:

        scaled_felt = pygame.transform.smoothscale(
            felt_surface,
            inner_table_rect.size
        )

        felt_layer = pygame.Surface(
            inner_table_rect.size,
            pygame.SRCALPHA
        )

        felt_layer.blit(
            scaled_felt,
            (0, 0)
        )

        felt_mask = pygame.Surface(
            inner_table_rect.size,
            pygame.SRCALPHA
        )

        pygame.draw.ellipse(
            felt_mask,
            (
                255,
                255,
                255,
                255
            ),
            felt_mask.get_rect()
        )

        felt_layer.blit(
            felt_mask,
            (0, 0),
            special_flags=pygame.BLEND_RGBA_MULT
        )

        game_surface.blit(
            felt_layer,
            inner_table_rect.topleft
        )

    else:

        pygame.draw.ellipse(
            game_surface,
            TABLE_GREEN,
            inner_table_rect
        )

    pygame.draw.ellipse(
        game_surface,
        WHITE,
        inner_table_rect,
        2
    )

    # ==================================================
    # Center table information backdrop
    #
    # Draw this before the seats so upper NPC HUDs/cards
    # always sit on top of it, matching Draw and Stud.
    # ==================================================

    info_panel_rect = pygame.Rect(
        table_rect.centerx - 142,
        184,
        284,
        88
    )

    draw_translucent_panel(
        game_surface,
        info_panel_rect,
        (0, 0, 0, 82),
        border_color=(110, 120, 115),
        border_width=1,
        radius=10
    )

    # ==================================================
    # NPC SEAT ANCHORS
    # ==================================================

    npc_anchors = [
        (180, 325),  # left
        (450, 120),  # upper-left: higher + farther left
        (900, 120),  # upper-right: higher + farther right
        (1090, 325),  # right
    ]

    # ==================================================
    # NPC DRAWING
    # ==================================================

    for index, npc in enumerate(
            holdem_game.npcs
    ):

        if index >= len(
                npc_anchors
        ):
            break

        anchor_x, anchor_y = (
            npc_anchors[index]
        )

        npc_is_busted = (
                index < len(
            holdem_game.npc_busted
        )
                and holdem_game.npc_busted[
                    index
                ]
        )

        npc_is_current_actor = (
                not holdem_game.hand_complete
                and not npc_is_busted
                and holdem_game.current_actor
                == index + 1
        )

        npc_is_folded = (
                index < len(
            holdem_game.npc_folded
        )
                and holdem_game.npc_folded[
                    index
                ]
        )

        npc_is_winner = (
                holdem_game.current_stage == "showdown"
                and index + 1 in holdem_game.winner_indexes
        )


        npc_is_all_in = (
                index < len(
            holdem_game.npc_all_in
        )
                and holdem_game.npc_all_in[
                    index
                ]
                and not npc_is_busted
                and not npc_is_folded
        )

        portrait_size = 72

        card_width = 64
        card_height = 88
        card_overlap = 20

        name_width = 165
        name_height = 40

        money_width = 118
        money_height = 28

        # ------------------------------------------
        # Portrait
        # ------------------------------------------

        portrait_rect = pygame.Rect(
            anchor_x - 52,
            anchor_y,
            portrait_size,
            portrait_size
        )

        draw_npc_portrait(
            npc,
            portrait_rect,
            "holdem"
        )

        # ==================================================
        # Portrait state overlay
        # ==================================================

        if npc_is_busted:

            busted_overlay = pygame.Surface(
                (
                    portrait_rect.width,
                    portrait_rect.height
                ),
                pygame.SRCALPHA
            )

            pygame.draw.circle(
                busted_overlay,
                (
                    5,
                    5,
                    5,
                    205
                ),
                (
                    portrait_rect.width // 2,
                    portrait_rect.height // 2
                ),
                min(
                    portrait_rect.width,
                    portrait_rect.height
                ) // 2
            )

            game_surface.blit(
                busted_overlay,
                portrait_rect.topleft
            )

            # Small X over eliminated portrait.
            pygame.draw.line(
                game_surface,
                (
                    150,
                    150,
                    150
                ),
                (
                    portrait_rect.left + 18,
                    portrait_rect.top + 18
                ),
                (
                    portrait_rect.right - 18,
                    portrait_rect.bottom - 18
                ),
                3
            )

            pygame.draw.line(
                game_surface,
                (
                    150,
                    150,
                    150
                ),
                (
                    portrait_rect.right - 18,
                    portrait_rect.top + 18
                ),
                (
                    portrait_rect.left + 18,
                    portrait_rect.bottom - 18
                ),
                3
            )

        elif npc_is_folded:

            fold_overlay = pygame.Surface(
                (
                    portrait_rect.width,
                    portrait_rect.height
                ),
                pygame.SRCALPHA
            )

            pygame.draw.circle(
                fold_overlay,
                (
                    0,
                    0,
                    0,
                    165
                ),
                (
                    portrait_rect.width // 2,
                    portrait_rect.height // 2
                ),
                min(
                    portrait_rect.width,
                    portrait_rect.height
                ) // 2
            )

            game_surface.blit(
                fold_overlay,
                portrait_rect.topleft
            )

        # ------------------------------------------
        # Current-turn gold border
        # ------------------------------------------

        if npc_is_current_actor or npc_is_winner:
            pygame.draw.rect(
                game_surface,
                (
                    235,
                    190,
                    70
                ),
                portrait_rect.inflate(
                    6,
                    6
                ),
                4 if npc_is_winner else 3,
                border_radius=9
            )

        # ------------------------------------------
        # Dealer / blind position badges
        # ------------------------------------------

        draw_holdem_position_badges(
            game_surface,
            holdem_game,
            index + 1,
            portrait_rect.x - 45,
            portrait_rect.bottom + 4
        )

        # ------------------------------------------
        # Cards above portrait/name
        # ------------------------------------------

        cards_y = (
                anchor_y - 56
        )

        first_card_x = (
                anchor_x + 8
        )

        second_card_x = (
                first_card_x
                + card_width
                - card_overlap
        )

        # ------------------------------------------
        # Show cards at showdown if NPC did not fold
        # ------------------------------------------

        npc_is_busted = (
                index
                < len(
            holdem_game.npc_busted
        )
                and holdem_game.npc_busted[
                    index
                ]
        )

        show_npc_cards = (
                (holdem_game.current_stage == "showdown"
                 or holdem_game.should_reveal_runout_hands())
                and not npc_is_folded
                and not npc_is_busted
                and index
                < len(
            holdem_game.npc_hands
        )
                and len(
            holdem_game.npc_hands[
                index
            ]
        ) >= 2
        )

        # ==================================================
        # Busted NPCs receive no cards
        # ==================================================

        if not npc_is_busted:

            for card_number in range(2):

                card_x = (
                    first_card_x
                    if card_number == 0
                    else second_card_x
                )

                # ==========================================
                # SHOWDOWN FLIP
                # ==========================================

                if show_npc_cards:

                    if (
                            card_fx_kind
                            == "showdown"
                    ):

                        flip_order = (
                                index * 2
                                + card_number
                        )

                        progress = (
                            get_holdem_card_fx_progress(
                                card_fx_elapsed,
                                delay=(
                                        flip_order
                                        * 90
                                ),
                                duration=240
                            )
                        )

                        draw_holdem_flipping_card(
                            game_surface,
                            holdem_game.npc_hands[
                                index
                            ][
                                card_number
                            ],
                            card_back,
                            card_x,
                            cards_y,
                            card_fronts,
                            card_width,
                            card_height,
                            progress
                        )

                    else:

                        draw_card_face(
                            game_surface,
                            holdem_game.npc_hands[
                                index
                            ][
                                card_number
                            ],
                            card_x,
                            cards_y,
                            card_fronts,
                            width=card_width,
                            height=card_height
                        )

                # ==========================================
                # HIDDEN HOLE CARD
                # ==========================================

                else:

                    if card_fx_kind == "deal":

                        # Deal:
                        # NPC 0,1,2,3 → player
                        # then repeat for second card.
                        deal_order = (
                                card_number * 5
                                + index
                        )

                        progress = (
                            get_holdem_card_fx_progress(
                                card_fx_elapsed,
                                delay=(
                                        deal_order
                                        * 70
                                ),
                                duration=180
                            )
                        )

                        draw_holdem_popping_card_back(
                            game_surface,
                            card_back,
                            card_x,
                            cards_y,
                            card_width,
                            card_height,
                            progress
                        )

                    else:

                        draw_card_back(
                            game_surface,
                            card_back,
                            card_x,
                            cards_y,
                            width=card_width,
                            height=card_height
                        )

            # Once a player folds, keep their hidden cards visibly inactive
            # for the rest of the hand even after the transient FOLDED action
            # label is cleared on a later street.
            if npc_is_folded:

                folded_card_overlay = pygame.Surface(
                    (
                        card_width,
                        card_height
                    ),
                    pygame.SRCALPHA
                )

                folded_card_overlay.fill(
                    (
                        105,
                        105,
                        105,
                        185
                    )
                )

                for folded_card_x in (
                        first_card_x,
                        second_card_x
                ):

                    game_surface.blit(
                        folded_card_overlay,
                        (
                            folded_card_x,
                            cards_y
                        )
                    )

        # ------------------------------------------
        # Name box
        # ------------------------------------------

        name_rect = pygame.Rect(
            anchor_x,
            anchor_y + 6,
            name_width,
            name_height
        )

        if npc_is_busted:

            name_fill = (
                24,
                24,
                26,
                225
            )

            name_border = (
                75,
                75,
                80
            )

            name_text_color = (
                145,
                145,
                150
            )

        elif npc_is_folded:

            name_fill = (
                10,
                10,
                10,
                210
            )

            name_border = (
                85,
                85,
                90
            )

            name_text_color = (
                185,
                185,
                190
            )

        else:

            name_fill = (
                18,
                20,
                24,
                235
            )

            name_border = (
                (
                    235,
                    190,
                    70
                )
                if (npc_is_current_actor or npc_is_winner)
                else (
                    120,
                    125,
                    130
                )
            )

            name_text_color = WHITE

        draw_translucent_panel(
            game_surface,
            name_rect,
            name_fill,
            border_color=name_border,
            border_width=(
                4
                if npc_is_winner
                else (
                    3
                    if npc_is_current_actor
                    else 2
                )
            ),
            radius=10
        )

        npc_display_name = (
            holdem_game.get_table_player_name(
                index + 1
            )
        )

        blit_text_fit(
            game_surface,
            npc_display_name,
            holdem_name_font,
            name_text_color,
            name_rect,
            padding=10
        )

        # ==================================================
        # Money / status box
        # ==================================================

        money_rect = pygame.Rect(
            name_rect.centerx
            - money_width // 2,
            name_rect.bottom - 2,
            money_width,
            money_height
        )

        npc_stack = 0

        if index < len(
                holdem_game.npc_stacks
        ):
            npc_stack = (
                holdem_game.npc_stacks[
                    index
                ]
            )

        if npc_is_busted:

            money_fill = (
                28,
                28,
                30,
                240
            )

            money_border = (
                85,
                85,
                90
            )

            money_text = "OUT"

            money_text_color = (
                165,
                165,
                170
            )

        else:

            money_fill = (
                12,
                14,
                16,
                240
            )

            money_border = (
                90,
                95,
                100
            )

            money_text = (
                f"${npc_stack:,}"
            )

            money_text_color = (
                240,
                255,
                235
            )

        draw_translucent_panel(
            game_surface,
            money_rect,
            money_fill,
            border_color=money_border,
            border_width=1,
            radius=8
        )

        money_text_surface = (
            holdem_small_font.render(
                money_text,
                True,
                money_text_color
            )
        )

        money_text_rect = (
            money_text_surface.get_rect(
                center=money_rect.center
            )
        )

        game_surface.blit(
            money_text_surface,
            money_text_rect
        )


        # ------------------------------------------
        # Action box
        # ------------------------------------------

        action_rect = pygame.Rect(
            money_rect.x,
            money_rect.bottom + 4,
            money_rect.width,
            money_rect.height
        )

        action_text = ""

        if index < len(
                holdem_game.npc_action_texts
        ):
            action_text = (
                holdem_game.npc_action_texts[
                    index
                ]
            )

        # ==================================================
        # Persistent status takes priority over last action
        # ==================================================

        if npc_is_busted:

            action_text = (
                "ELIMINATED"
            )

        elif npc_is_all_in:

            action_text = (
                "ALL IN"
            )

        if action_text:

            # ==================================================
            # Eliminated
            # ==================================================

            if action_text == "ELIMINATED":

                action_fill = (
                    30,
                    30,
                    32,
                    240
                )

                action_border = (
                    85,
                    85,
                    90
                )

                action_text_color = (
                    150,
                    150,
                    155
                )

            # ==================================================
            # Folded
            # ==================================================

            elif action_text == "Folded":

                action_fill = (
                    70,
                    25,
                    25,
                    235
                )

                action_border = (
                    145,
                    75,
                    75
                )

                action_text_color = (
                    225,
                    205,
                    205
                )

            # ==================================================
            # All in
            # ==================================================

            elif action_text == "ALL IN":

                action_fill = (
                    105,
                    72,
                    18,
                    240
                )

                action_border = (
                    240,
                    190,
                    70
                )

                action_text_color = WHITE

            # ==================================================
            # Normal action
            # ==================================================

            else:

                action_fill = (
                    10,
                    12,
                    14,
                    235
                )

                action_border = (
                    110,
                    115,
                    120
                )

                action_text_color = WHITE

            draw_translucent_panel(
                game_surface,
                action_rect,
                action_fill,
                border_color=action_border,
                border_width=1,
                radius=8
            )

            blit_text_fit(
                game_surface,
                action_text,
                holdem_small_font,
                action_text_color,
                action_rect,
                padding=6
            )

        # ------------------------------------------
        # Chips committed this betting round
        # ------------------------------------------

        npc_chunks = []

        if index < len(
                holdem_game.npc_bet_chunks
        ):

            npc_chunks = (
                holdem_game.npc_bet_chunks[
                    index
                ]
            )

        if (
                npc_chunks
                and not npc_is_busted
        ):

            # ======================================
            # Position chips toward center of table
            # ======================================

            npc_chip_positions = [
                # Left seat
                (
                    anchor_x + 190,
                    anchor_y + 55
                ),

                # Upper-left seat
                (
                    anchor_x + 95,
                    anchor_y + 125
                ),

                # Upper-right seat
                (
                    anchor_x - 5,
                    anchor_y + 125
                ),

                # Right seat
                (
                    anchor_x - 105,
                    anchor_y + 55
                ),
            ]

            chip_center_x, chip_y = (
                npc_chip_positions[
                    index
                ]
            )

            draw_holdem_chip_chunks(
                game_surface,
                npc_chunks,
                chip_center_x,
                chip_y,
                poker_chip_images,
                base_unit=max(
                    1,
                    holdem_game.ante
                ),
                origin=(
                    money_rect.centerx,
                    money_rect.centery
                ),
                animation_key=(
                    f"npc_{index}"
                ),
                sweep_target=(
                    wager_sweep_target
                ),
                sweep_progress=(
                    wager_sweep_progress
                )
            )


    # ==================================================
    # Community cards
    # ==================================================

    community_card_width = 100
    community_card_height = 138
    community_card_gap = 12

    community_y = 282

    total_community_width = (
            community_card_width * 5
            + community_card_gap * 4
    )

    community_start_x = (
            table_rect.centerx
            - total_community_width // 2
    )

    # ==================================================
    # Pot
    # ==================================================

    display_pot = (
        holdem_game.get_display_pot_amount()
        if hasattr(holdem_game, "get_display_pot_amount")
        else holdem_game.pot
    )

    pot_base_unit = max(
        1,
        int(
            getattr(
                holdem_game,
                "ante",
                1
            )
        )
    )

    draw_holdem_pot_stack(
        game_surface,
        display_pot,
        (
            table_rect.centerx,
            community_y - 48
        ),
        pot_base_unit
    )

    pot_surface = holdem_small_font.render(
        f"Pot: ${display_pot:,}",
        True,
        WHITE
    )

    pot_rect = (
        pot_surface.get_rect(
            center=(
                table_rect.centerx,
                community_y - 18
            )
        )
    )

    game_surface.blit(
        pot_surface,
        pot_rect
    )

    # ==================================================
    # Blind level
    # ==================================================

    small_blind = getattr(
        holdem_game,
        "small_blind",
        max(
            1,
            getattr(
                holdem_game,
                "ante",
                1
            )
        )
    )

    big_blind = getattr(
        holdem_game,
        "big_blind",
        max(
            2,
            small_blind * 2
        )
    )

    blinds_surface = (
        holdem_tiny_font.render(
            (
                f"Blinds: "
                f"${small_blind:,} / "
                f"${big_blind:,}"
            ),
            True,
            (
                225,
                225,
                230
            )
        )
    )

    blinds_rect = (
        blinds_surface.get_rect(
            center=(
                table_rect.centerx,
                205
            )
        )
    )

    game_surface.blit(
        blinds_surface,
        blinds_rect
    )


    for index in range(5):

        card_x = (
                community_start_x
                + index
                * (
                        community_card_width
                        + community_card_gap
                )
        )

        if index < len(
                holdem_game.community_cards
        ):

            animate_card = False
            animation_delay = 0

            # ==========================================
            # FLOP
            # ==========================================

            if (
                    card_fx_kind == "flop"
                    and index <= 2
            ):

                animate_card = True

                animation_delay = (
                        index * 110
                )

            # ==========================================
            # TURN
            # ==========================================

            elif (
                    card_fx_kind == "turn"
                    and index == 3
            ):

                animate_card = True

            # ==========================================
            # RIVER
            # ==========================================

            elif (
                    card_fx_kind == "river"
                    and index == 4
            ):

                animate_card = True

            # ==========================================
            # Animated reveal
            # ==========================================

            if animate_card:

                progress = (
                    get_holdem_card_fx_progress(
                        card_fx_elapsed,
                        delay=animation_delay,
                        duration=220
                    )
                )

                draw_holdem_popping_card_face(
                    game_surface,
                    holdem_game.community_cards[
                        index
                    ],
                    card_x,
                    community_y,
                    card_fronts,
                    community_card_width,
                    community_card_height,
                    progress
                )

            # ==========================================
            # Already-established card
            # ==========================================

            else:

                draw_card_face(
                    game_surface,
                    holdem_game.community_cards[
                        index
                    ],
                    card_x,
                    community_y,
                    card_fronts,
                    width=community_card_width,
                    height=community_card_height
                )


    # ==================================================
    # Player area
    # ==================================================

    player_center_x = 683

    player_card_width = 126
    player_card_height = 174
    player_card_overlap = 34

    player_cards_total_width = (
            player_card_width * 2
            - player_card_overlap
    )

    player_start_x = (
            player_center_x
            - player_cards_total_width // 2
    )

    player_cards_y = 563

    # ==================================================
    # Player hole cards
    # ==================================================

    for card_number in range(
            min(
                2,
                len(
                    holdem_game.player_hand
                )
            )
    ):

        card_x = (
                player_start_x
                + card_number
                * (
                        player_card_width
                        - player_card_overlap
                )
        )

        if card_fx_kind == "deal":

            # Player is fifth in each deal cycle:
            #
            # NPC0 NPC1 NPC2 NPC3 PLAYER
            deal_order = (
                    card_number * 5
                    + 4
            )

            progress = (
                get_holdem_card_fx_progress(
                    card_fx_elapsed,
                    delay=(
                            deal_order
                            * 70
                    ),
                    duration=180
                )
            )

            draw_holdem_popping_card_face(
                game_surface,
                holdem_game.player_hand[
                    card_number
                ],
                card_x,
                player_cards_y,
                card_fronts,
                player_card_width,
                player_card_height,
                progress
            )

        else:

            draw_card_face(
                game_surface,
                holdem_game.player_hand[
                    card_number
                ],
                card_x,
                player_cards_y,
                card_fronts,
                width=player_card_width,
                height=player_card_height
            )

    # ==================================================
    # Player chips
    # ==================================================

    if holdem_game.player_bet_chunks:
        draw_holdem_chip_chunks(
            game_surface,
            holdem_game.player_bet_chunks,
            player_center_x + 130,
            535,
            poker_chip_images,
            base_unit=max(
                1,
                holdem_game.ante
            ),
            origin=(
                player_center_x,
                700
            ),
            animation_key="player",
            sweep_target=(
                wager_sweep_target
            ),
            sweep_progress=(
                wager_sweep_progress
            )
        )

    draw_holdem_position_badges(
        game_surface,
        holdem_game,
        0,
        player_center_x + 144,
        686
    )

    draw_holdem_player_hud(
        game_surface=game_surface,
        player_name=player_name,
        player_stack=holdem_game.player_stack,
        panel_center_x=player_center_x,
        panel_y=680,
        label_font=label_font,
        detail_font=detail_font,
        is_current_actor=(
                not holdem_game.hand_complete
                and holdem_game.current_actor == 0
                and not holdem_game.player_has_acted
        ),
        is_winner=(
                holdem_game.current_stage == "showdown"
                and 0 in holdem_game.winner_indexes
        )
    )

    draw_holdem_payout_animation(
        game_surface,
        holdem_game,
        npc_anchors,
        max(
            1,
            getattr(
                holdem_game,
                "ante",
                1
            )
        )
    )

    draw_holdem_showdown_banner(
        game_surface,
        holdem_game
    )

    # ==================================================
    # Game log content
    # ==================================================

    update_holdem_log(
        holdem_game
    )

    # ==================================================
    # Game logo
    # ==================================================

    draw_poker_logo(
        game_surface,
        "texas_holdem",
        pygame.Rect(32, 66, 280, 75)
    )

    # ==================================================
    # Game log / Chat panel
    # ==================================================

    completed = len(getattr(holdem_game, 'rating_seen_hands', ()))
    rating_status = poker_session_status(holdem_game, getattr(holdem_game, 'career_session_rated', True))
    rating_label = ui_text.get_font(None, 24).render(rating_status, True, (231, 239, 234))
    game_surface.blit(rating_label, (22, 553))

    draw_holdem_log_panel(
        game_surface=game_surface,
        detail_font=detail_font,
        mouse_pos=mouse_pos,
        active_tab=state.holdem_active_tab,
        log_lines=holdem_log_history
    )

    # ==================================================
    # Current hand above controls
    # ==================================================

    hand_text = (
        get_holdem_player_hand_text(
            holdem_game
        )
    )

    if hand_text:
        hand_surface = holdem_small_font.render(
            hand_text,
            True,
            WHITE
        )

        hand_rect = (
            hand_surface.get_rect(
                bottomright=(
                    holdem_action_panel_rect.right - 6,
                    holdem_action_panel_rect.y - 8
                )
            )
        )

        game_surface.blit(
            hand_surface,
            hand_rect
        )

    # ==================================================
    # Poker controls
    # ==================================================

    draw_holdem_side_panel(
        surface=game_surface,
        holdem_game=holdem_game,
        title_font=label_font,
        detail_font=detail_font,
        mouse_pos=mouse_pos,
        next_hand_seconds=next_hand_seconds
    )

    # ==================================================
    # Top-right utility buttons
    # ==================================================

    draw_modern_button(
        game_surface,
        holdem_options_rect,
        "OPTIONS",
        mouse_pos,
        holdem_small_font,
        enabled=True
    )

    draw_modern_button(
        game_surface,
        holdem_exit_rect,
        "EXIT",
        mouse_pos,
        holdem_small_font,
        enabled=bool(holdem_game.hand_complete)
    )

    # ==================================================
    # Final speech-bubble overlay pass
    # ==================================================

    if is_poker_chat_popups_enabled():
        for index, _npc in enumerate(holdem_game.npcs[:4]):
            anchor_x, anchor_y = npc_anchors[index]
            name_rect = pygame.Rect(anchor_x, anchor_y + 6, 165, 40)
            _holdem_speech_overlay.draw(
                game_surface,
                holdem_game.get_table_player_name(index + 1),
                name_rect,
                holdem_small_font
            )

    # ==================================================
    # Options overlay
    # ==================================================

    draw_holdem_options_overlay(
        game_surface,
        mouse_pos
    )
    draw_recap(game_surface, mouse_pos, holdem_game)


def get_texas_holdem_action(
        mouse_pos,
        holdem_game
):

    if mouse_pos is None:
        return None

    recap_action = get_recap_action(mouse_pos, holdem_game)
    if recap_action:
        return recap_action

    if state.holdem_options_open:
        return None

    # ==================================================
    # Next hand
    # ==================================================

    if (
            holdem_game.hand_complete
            and holdem_next_hand_rect.collidepoint(
        mouse_pos
    )
    ):
        return ACTION_NEXT_HAND

    # ==================================================
    # Main poker actions
    # ==================================================

    if holdem_game.can_player_act_now():

        if holdem_fold_rect.collidepoint(
                mouse_pos
        ):
            return ACTION_FOLD

        if holdem_call_rect.collidepoint(
                mouse_pos
        ):
            return ACTION_CHECK_CALL

        if holdem_raise_rect.collidepoint(
                mouse_pos
        ):
            return ACTION_BET_RAISE

    # ==================================================
    # Exit
    # ==================================================

    if (
            holdem_game.hand_complete
            and holdem_exit_rect.collidepoint(mouse_pos)
    ):
        return ACTION_RETURN

    # ==================================================
    # Options
    # ==================================================

    if holdem_options_rect.collidepoint(
            mouse_pos
    ):
        return "options"

    return None
