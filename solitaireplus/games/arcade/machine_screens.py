"""The four arcade machines in play: King Pong, Battle Bosses, Ace Invaders, Suit Snake (moved out of legacy.py)."""
from solitaireplus.games.arcade.ace_invaders_game import AceInvadersGame
from solitaireplus.games.arcade.battle_bosses import BATTLE_BOSSES_DIFFICULTIES
from solitaireplus.games.arcade.battle_bosses_game import BattleBossesGame
from solitaireplus.games.arcade.king_pong import KingPongGame
from solitaireplus.games.arcade.suit_snake import SUIT_SNAKE_MOVEMENT_STYLES
from solitaireplus.games.arcade.suit_snake_game import SuitSnakeGame
from solitaireplus.games.arcade.support import award_ace_invaders_tickets
from solitaireplus.games.arcade.support import award_battle_bosses_tickets
from solitaireplus.games.arcade.support import award_king_pong_tickets
from solitaireplus.games.arcade.support import award_suit_snake_tickets
from solitaireplus.career import career_saving
from solitaireplus.games.arcade.support import get_machine_cost
import pygame
from solitaireplus.games.arcade.support import register_ace_invaders_result
from solitaireplus.games.arcade.support import register_battle_bosses_result
from solitaireplus.games.arcade.support import register_king_pong_result
from solitaireplus.games.arcade.support import register_suit_snake_result
from solitaireplus.games.arcade.support import spend_tokens
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
machine_select = lazy("solitaireplus.games.arcade.machine_select")
hub_screens = lazy("solitaireplus.games.arcade.hub_screens")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
night = lazy("solitaireplus.career.events.night")
fonts = lazy("solitaireplus.app.fonts")


king_pong_game = KingPongGame()
battle_bosses_game = BattleBossesGame()
ace_invaders_game = AceInvadersGame()
suit_snake_game = SuitSnakeGame()

king_pong_return_rect = pygame.Rect(1132, 652, 198, 54)
battle_bosses_quit_rect = pygame.Rect(1090, 675, 220, 50)
ace_invaders_quit_rect = pygame.Rect(1120, 676, 190, 50)
# Keep the gameplay Quit control completely outside Suit Snake's playfield
# and footer, including the larger 30x16 board.
suit_snake_quit_rect = pygame.Rect(1155, 660, 190, 50)


def start_king_pong_session():

    selected = machine_select.get_selected_king_pong_choice()
    if selected is None:
        machine_select.open_king_pong_opponent_select(refresh=True)
        hub_screens.set_arcade_status_message("Choose a King Pong rival first.")
        return False

    token_cost = get_machine_cost("king_pong")
    success, updated_state = spend_tokens(state.arcade_state, token_cost)
    if not success:
        hub_screens.set_arcade_status_message("Not enough tokens. Buy more to play King Pong.")
        hub_screens.open_arcade_token_exchange("king_pong")
        return False

    state.arcade_state = updated_state
    state.arcade_night_tokens_spent += token_cost
    state.arcade_pending_launch_game_id = None
    state.career_event_has_activity = True

    difficulty_id = selected.get("difficulty_id", "medium")
    opponent = selected.get("npc") or {"name": "Arcade Rival", "skill_tier": "mid"}
    king_pong_game.start_match(
        opponent,
        difficulty_id=difficulty_id,
        target_score=5,
        player_name=state.player_name,
    )
    career_saving.auto_save_career()
    state.current_state = state_names.STATE_KING_PONG
    return True


def claim_king_pong_result():

    if king_pong_game.reward_claimed or not king_pong_game.finished:
        return False

    if king_pong_game.forfeited:
        base_tickets = 0
        tickets = 0
    else:
        base_tickets = award_king_pong_tickets(
            king_pong_game.player_score,
            king_pong_game.opponent_score,
        )
        tickets = max(
            0,
            int(round(base_tickets * king_pong_game.ticket_multiplier)),
        )

    state.arcade_state = register_king_pong_result(
        state.arcade_state,
        king_pong_game.player_won,
        tickets,
    )
    state.arcade_night_tickets_won += tickets
    state.career_event_has_activity = True

    night.record_career_event_result(
        "king_pong",
        won=king_pong_game.player_won,
        tickets=tickets,
        base_tickets=base_tickets,
        ticket_multiplier=king_pong_game.ticket_multiplier,
        difficulty=king_pong_game.difficulty_id,
        tokens_spent=get_machine_cost("king_pong"),
        player_score=king_pong_game.player_score,
        opponent_score=king_pong_game.opponent_score,
        opponent_name=king_pong_game.opponent_name,
        forfeited=bool(king_pong_game.forfeited),
        fan_impact=False,
    )

    king_pong_game.reward_claimed = True
    career_saving.auto_save_career()
    return True


def finish_king_pong_session():

    claim_king_pong_result()
    state.current_state = state_names.STATE_CAREER_EVENT_SELECT


def start_battle_bosses_session():

    selected = machine_select.get_selected_battle_bosses_choice()
    if selected is None:
        machine_select.open_battle_bosses_opponent_select(refresh=True)
        hub_screens.set_arcade_status_message("Choose a Battle Bosses squad first.")
        return False

    token_cost = get_machine_cost("battle_bosses")
    success, updated_state = spend_tokens(state.arcade_state, token_cost)
    if not success:
        hub_screens.set_arcade_status_message("Not enough tokens. Buy more to enter Battle Bosses.")
        hub_screens.open_arcade_token_exchange("battle_bosses")
        return False

    state.arcade_state = updated_state
    state.arcade_night_tokens_spent += token_cost
    state.arcade_pending_launch_game_id = None
    state.career_event_has_activity = True

    difficulty_id = selected.get("difficulty_id", "standard")
    config = selected.get("config") or BATTLE_BOSSES_DIFFICULTIES.get(
        difficulty_id, BATTLE_BOSSES_DIFFICULTIES["standard"]
    )
    battle_bosses_game.start_match(
        selected.get("npcs") or [],
        difficulty_id=difficulty_id,
        difficulty_config=config,
        player_name=state.player_name,
    )
    career_saving.auto_save_career()
    state.current_state = state_names.STATE_BATTLE_BOSSES
    return True


def claim_battle_bosses_result():

    if battle_bosses_game.reward_claimed or not battle_bosses_game.finished:
        return False

    if battle_bosses_game.forfeited:
        base_tickets = 0
        tickets = 0
    else:
        base_tickets = award_battle_bosses_tickets(
            battle_bosses_game.rivals_eliminated,
            battle_bosses_game.player_won,
            battle_bosses_game.player_hp,
        )
        tickets = max(
            0,
            int(round(base_tickets * battle_bosses_game.ticket_multiplier)),
        )

    state.arcade_state = register_battle_bosses_result(
        state.arcade_state,
        battle_bosses_game.player_won,
        tickets,
        rivals_eliminated=battle_bosses_game.rivals_eliminated,
    )
    state.arcade_night_tickets_won += tickets
    state.career_event_has_activity = True

    night.record_career_event_result(
        "battle_bosses",
        won=battle_bosses_game.player_won,
        tickets=tickets,
        base_tickets=base_tickets,
        ticket_multiplier=battle_bosses_game.ticket_multiplier,
        difficulty=battle_bosses_game.difficulty_id,
        tokens_spent=get_machine_cost("battle_bosses"),
        rivals_eliminated=battle_bosses_game.rivals_eliminated,
        player_hp=battle_bosses_game.player_hp,
        forfeited=bool(battle_bosses_game.forfeited),
        fan_impact=False,
    )

    battle_bosses_game.reward_claimed = True
    career_saving.auto_save_career()
    return True


def finish_battle_bosses_session():

    claim_battle_bosses_result()
    state.current_state = state_names.STATE_CAREER_EVENT_SELECT


def start_ace_invaders_session():

    difficulty_id = machine_select.get_selected_ace_invaders_difficulty()
    if difficulty_id is None:
        machine_select.open_ace_invaders_difficulty_select(reset_selection=False)
        hub_screens.set_arcade_status_message("Choose an Ace Invaders difficulty first.")
        return False

    token_cost = get_machine_cost("ace_invaders")
    success, updated_state = spend_tokens(state.arcade_state, token_cost)
    if not success:
        hub_screens.set_arcade_status_message("Not enough tokens. Buy more to play Ace Invaders.")
        hub_screens.open_arcade_token_exchange("ace_invaders")
        return False

    state.arcade_state = updated_state
    state.arcade_night_tokens_spent += token_cost
    state.arcade_pending_launch_game_id = None
    state.career_event_has_activity = True

    saved_high_score = int(
        state.arcade_state.get("stats", {}).get("ace_invaders_high_score", 0) or 0
    )
    ace_invaders_game.start_session(
        difficulty_id,
        high_score=saved_high_score,
    )
    career_saving.auto_save_career()
    state.current_state = state_names.STATE_ACE_INVADERS
    return True


def claim_ace_invaders_result():

    if ace_invaders_game.reward_claimed or not ace_invaders_game.finished:
        return False

    if ace_invaders_game.forfeited:
        base_tickets = 0
        tickets = 0
    else:
        base_tickets = award_ace_invaders_tickets(
            ace_invaders_game.score,
            ace_invaders_game.waves_cleared,
        )
        tickets = max(
            0,
            int(round(base_tickets * ace_invaders_game.ticket_multiplier)),
        )

    state.arcade_state = register_ace_invaders_result(
        state.arcade_state,
        None,
        tickets,
        score=ace_invaders_game.score,
        enemies_destroyed=ace_invaders_game.enemies_destroyed,
        waves_cleared=ace_invaders_game.waves_cleared,
    )
    state.arcade_night_tickets_won += tickets
    state.career_event_has_activity = True

    night.record_career_event_result(
        "ace_invaders",
        won=None,
        tickets=tickets,
        base_tickets=base_tickets,
        ticket_multiplier=ace_invaders_game.ticket_multiplier,
        difficulty=ace_invaders_game.difficulty_id,
        tokens_spent=get_machine_cost("ace_invaders"),
        score=ace_invaders_game.score,
        high_score=ace_invaders_game.high_score,
        waves_cleared=ace_invaders_game.waves_cleared,
        enemies_destroyed=ace_invaders_game.enemies_destroyed,
        lives=ace_invaders_game.lives,
        accuracy=ace_invaders_game.accuracy_percent,
        forfeited=bool(ace_invaders_game.forfeited),
        fan_impact=False,
    )

    ace_invaders_game.reward_claimed = True
    career_saving.auto_save_career()
    return True


def finish_ace_invaders_session():

    claim_ace_invaders_result()
    state.current_state = state_names.STATE_CAREER_EVENT_SELECT


def start_suit_snake_session():

    mode_id = machine_select.get_selected_suit_snake_mode()
    if mode_id is None:
        machine_select.open_suit_snake_difficulty_select(reset_selection=False)
        hub_screens.set_arcade_status_message("Choose a Suit Snake mode first.")
        return False

    movement_style = (
        state.suit_snake_selected_movement_style
        if state.suit_snake_selected_movement_style in SUIT_SNAKE_MOVEMENT_STYLES
        else "step"
    )

    token_cost = get_machine_cost("suit_snake")
    success, updated_state = spend_tokens(state.arcade_state, token_cost)
    if not success:
        hub_screens.set_arcade_status_message("Not enough tokens. Buy more to play Suit Snake.")
        hub_screens.open_arcade_token_exchange("suit_snake")
        return False

    state.arcade_state = updated_state
    state.arcade_night_tokens_spent += token_cost
    state.arcade_pending_launch_game_id = None
    state.career_event_has_activity = True

    saved_high_score = int(
        state.arcade_state.get("stats", {}).get("suit_snake_high_score", 0) or 0
    )
    suit_snake_game.start_session(
        mode_id,
        movement_style=movement_style,
        high_score=saved_high_score,
    )
    career_saving.auto_save_career()
    state.current_state = state_names.STATE_SUIT_SNAKE
    return True

def claim_suit_snake_result():

    if suit_snake_game.reward_claimed or not suit_snake_game.finished:
        return False

    if suit_snake_game.forfeited:
        base_tickets = 0
        tickets = 0
    else:
        base_tickets = award_suit_snake_tickets(
            suit_snake_game.score,
            suit_snake_game.cards_collected,
            suit_snake_game.decks_completed,
        )
        tickets = max(
            0,
            int(round(base_tickets * suit_snake_game.ticket_multiplier)),
        )

    state.arcade_state = register_suit_snake_result(
        state.arcade_state,
        tickets,
        score=suit_snake_game.score,
        cards_collected=suit_snake_game.cards_collected,
        decks_completed=suit_snake_game.decks_completed,
        chain_length=suit_snake_game.chain_length,
    )
    state.arcade_night_tickets_won += tickets
    state.career_event_has_activity = True

    night.record_career_event_result(
        "suit_snake",
        won=None,
        tickets=tickets,
        base_tickets=base_tickets,
        ticket_multiplier=suit_snake_game.ticket_multiplier,
        difficulty=suit_snake_game.mode_id,
        mode=suit_snake_game.mode_id,
        movement=suit_snake_game.movement_style,
        tokens_spent=get_machine_cost("suit_snake"),
        score=suit_snake_game.score,
        high_score=suit_snake_game.high_score,
        cards_collected=suit_snake_game.cards_collected,
        decks_completed=suit_snake_game.decks_completed,
        chain_length=suit_snake_game.chain_length,
        forfeited=bool(suit_snake_game.forfeited),
        fan_impact=False,
    )

    suit_snake_game.reward_claimed = True
    career_saving.auto_save_career()
    return True


def finish_suit_snake_session():

    claim_suit_snake_result()
    state.current_state = state_names.STATE_CAREER_EVENT_SELECT


def draw_ace_invaders_screen():
    ace_invaders_game.draw(
        window.game_surface,
        {
            "title": fonts.options_title_font,
            "label": fonts.option_label_font,
            "detail": fonts.difficulty_detail_font,
            "small": fonts.ui_small_font,
        },
    )
    hub_screens.draw_arcade_action_image_button(
        ace_invaders_quit_rect,
        "quit",
        "Quit",
    )


def draw_king_pong_screen():
    king_pong_game.draw(
        window.game_surface,
        {
            'title': fonts.options_title_font,
            'label': fonts.option_label_font,
            'detail': fonts.difficulty_detail_font,
            'small': fonts.ui_small_font,
        },
        portrait_loader=legacy.get_npc_portrait_surface,
    )
    hub_screens.draw_arcade_action_image_button(
        king_pong_return_rect,
        "quit",
        "Quit",
    )


def draw_battle_bosses_screen():
    try:
        player_portrait = legacy.get_profile_avatar()
    except Exception:
        player_portrait = None

    battle_bosses_game.draw(
        window.game_surface,
        {
            'title': fonts.options_title_font,
            'label': fonts.option_label_font,
            'detail': fonts.difficulty_detail_font,
            'small': fonts.ui_small_font,
        },
        portrait_loader=legacy.get_npc_portrait_surface,
        player_portrait=player_portrait,
    )
    hub_screens.draw_arcade_action_image_button(
        battle_bosses_quit_rect,
        "quit",
        "Quit",
    )

def draw_suit_snake_screen():
    suit_snake_game.draw(
        window.game_surface,
        {
            "title": fonts.options_title_font,
            "label": fonts.option_label_font,
            "detail": fonts.difficulty_detail_font,
            "small": fonts.ui_small_font,
        },
    )
    hub_screens.draw_arcade_action_image_button(
        suit_snake_quit_rect,
        "quit",
        "Quit",
    )


def loop_event_king_pong(event):
    """Old main-loop event branch for STATE_KING_PONG."""

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            if not king_pong_game.finished:
                king_pong_game.forfeit()
            finish_king_pong_session()
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if not king_pong_game.finished:
                king_pong_game.forfeit()
            finish_king_pong_session()
        elif event.key == pygame.K_SPACE and king_pong_game.finished:
            start_king_pong_session()

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        if king_pong_return_rect.collidepoint(state.menu_mouse_pos):
            sounds.audio.play_sound("button_click")
            if not king_pong_game.finished:
                king_pong_game.forfeit()
            finish_king_pong_session()


def loop_event_battle_bosses(event):
    """Old main-loop event branch for STATE_BATTLE_BOSSES."""

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            if not battle_bosses_game.finished:
                battle_bosses_game.forfeit()
            finish_battle_bosses_session()
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if battle_bosses_game.finished:
                finish_battle_bosses_session()
        elif event.key == pygame.K_SPACE and battle_bosses_game.finished:
            start_battle_bosses_session()

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        if battle_bosses_quit_rect.collidepoint(state.menu_mouse_pos):
            sounds.audio.play_sound("button_click")
            if not battle_bosses_game.finished:
                battle_bosses_game.forfeit()
            finish_battle_bosses_session()


def loop_event_ace_invaders(event):
    """Old main-loop event branch for STATE_ACE_INVADERS."""

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            if not ace_invaders_game.finished:
                ace_invaders_game.forfeit()
            finish_ace_invaders_session()
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if ace_invaders_game.finished:
                finish_ace_invaders_session()
        elif event.key == pygame.K_r and ace_invaders_game.finished:
            start_ace_invaders_session()

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        if ace_invaders_quit_rect.collidepoint(state.menu_mouse_pos):
            sounds.audio.play_sound("button_click")
            if not ace_invaders_game.finished:
                ace_invaders_game.forfeit()
            finish_ace_invaders_session()


def loop_event_suit_snake(event):
    """Old main-loop event branch for STATE_SUIT_SNAKE."""

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            if not suit_snake_game.finished:
                suit_snake_game.forfeit()
            finish_suit_snake_session()
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if suit_snake_game.finished:
                finish_suit_snake_session()
        elif event.key == pygame.K_r and suit_snake_game.finished:
            start_suit_snake_session()
        elif event.key in (pygame.K_w, pygame.K_UP):
            suit_snake_game.queue_direction("up")
        elif event.key in (pygame.K_s, pygame.K_DOWN):
            suit_snake_game.queue_direction("down")
        elif event.key in (pygame.K_a, pygame.K_LEFT):
            suit_snake_game.queue_direction("left")
        elif event.key in (pygame.K_d, pygame.K_RIGHT):
            suit_snake_game.queue_direction("right")

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        if suit_snake_quit_rect.collidepoint(state.menu_mouse_pos):
            sounds.audio.play_sound("button_click")
            if not suit_snake_game.finished:
                suit_snake_game.forfeit()
            finish_suit_snake_session()


def loop_draw_king_pong():
    """Old draw-chain branch for STATE_KING_PONG."""

    king_pong_game.update(1.0 / 60.0, pygame.key.get_pressed())
    while True:
        point_event = king_pong_game.pop_point_event()
        if point_event is None:
            break
        sounds.audio.play_sound(
            "five_o_column_win"
            if point_event.get("player_scored")
            else "five_o_column_loss"
        )
    if king_pong_game.finished:
        claim_king_pong_result()
    draw_king_pong_screen()


def loop_draw_battle_bosses():
    """Old draw-chain branch for STATE_BATTLE_BOSSES."""

    battle_bosses_game.update(1.0 / 60.0, pygame.key.get_pressed())
    for battle_sound_event in battle_bosses_game.pop_sound_events():
        sounds.audio.play_sound(battle_sound_event)
    if battle_bosses_game.finished:
        claim_battle_bosses_result()
    draw_battle_bosses_screen()


def loop_draw_ace_invaders():
    """Old draw-chain branch for STATE_ACE_INVADERS."""

    ace_invaders_game.update(1.0 / 60.0, pygame.key.get_pressed())
    for ace_sound_event in ace_invaders_game.pop_sound_events():
        sounds.audio.play_sound(ace_sound_event)
    if ace_invaders_game.finished:
        claim_ace_invaders_result()
    draw_ace_invaders_screen()


def loop_draw_suit_snake():
    """Old draw-chain branch for STATE_SUIT_SNAKE."""

    suit_snake_game.update(1.0 / 60.0, pygame.key.get_pressed())
    for suit_snake_sound_event in suit_snake_game.pop_sound_events():
        sounds.audio.play_sound(suit_snake_sound_event)
    if suit_snake_game.finished:
        claim_suit_snake_result()
    draw_suit_snake_screen()
