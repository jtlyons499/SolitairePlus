"""Free Play game grid (moved out of legacy.py)."""
from solitaireplus.games.solitaire.rules import BASE_HEIGHT
from solitaireplus.games.solitaire.rules import BASE_WIDTH
from solitaireplus.npc.manager import NPCS
import copy
from solitaireplus.npc.manager import get_random_blackjack_dealer
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
hub_screen = lazy("solitaireplus.career.hub_screen")
night = lazy("solitaireplus.career.events.night")
event_select_screen = lazy("solitaireplus.career.events.event_select_screen")
case_opening_screen = lazy("solitaireplus.career.case_opening_screen")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")


free_play_back_rect = pygame.Rect(
    BASE_WIDTH // 2 - 150,
    675,
    300,
    50
)
FREE_PLAY_STARTING_CASH = 5_000


def begin_free_play_sandbox(use_cash=False):
    """Protect Career state while a Free Play game is running."""

    if state.free_play_snapshot is None:
        state.free_play_snapshot = {
            "career_rating": state.career_rating,
            "career_ratings": copy.deepcopy(state.career_ratings),
            "career_cash": state.career_cash,
            "career_fans": state.career_fans,
            "career_fan_news_milestones": set(state.career_fan_news_milestones),
            "career_fan_trend": list(state.career_fan_trend),
            "career_news_items": copy.deepcopy(state.career_news_items),
            "career_rounds_won": state.career_rounds_won,
            "career_challenges_won": state.career_challenges_won,
            "career_total_moves": state.career_total_moves,
            "career_event_result_log": copy.deepcopy(state.career_event_result_log),
            "career_event_has_activity": state.career_event_has_activity,
            "blackjack_session_rating_change": legacy.game_namespace().get("blackjack_session_rating_change", 0),
        }

    state.career_event_entry = None
    state.career_event_has_activity = False
    state.free_play_achievement_fans_earned = 0

    if use_cash:
        state.career_cash = FREE_PLAY_STARTING_CASH


def start_free_play_game(game_id):

    state.current_game_mode = "free"

    cash_game = game_id in (
        "blackjack", "roulette", "horse_races", "texas_holdem",
        "five_card_draw", "seven_card_stud", "faro",
        "five_o_poker", "blind_mans_bluff"
    )
    begin_free_play_sandbox(use_cash=cash_game)

    if game_id == "solitaire":
        legacy.game.clear_challenge()
        state.current_state = state_names.STATE_DIFFICULTY
        return True

    if game_id == "case_opening":
        from solitaireplus.career.case_opening import new_case_state
        case_opening_screen.case_screen.enter(new_case_state(), FREE_PLAY_STARTING_CASH, hub_screen.buy_case_for_screen, temporary=True)
        state.current_state = state_names.STATE_CASE_OPENING
        return True

    if game_id == "cryptid_creatures":
        legacy.cryptid_screen.enter(NPCS)
        state.current_state = state_names.STATE_CRYPTID_CREATURES
        return True

    if game_id == "score_four":
        state.score_four_opponent_npc = None
        state.current_state = state_names.STATE_SCORE_FOUR_MODE_SELECT
        return True

    if game_id == "crazy_eights":
        legacy.start_crazy_eights_session()
        return True

    if game_id == "bango":
        legacy.start_bango_session()
        return True

    if game_id == "blackjack":
        state.blackjack_dealer_npc = get_random_blackjack_dealer()
        state.blackjack_selected_bet_percentage = None
        state.blackjack_bet_dropdown_open = False
        state.blackjack_session_net = 0
        state.blackjack_session_rating_change = 0
        state.current_state = state_names.STATE_BLACKJACK_BET
        return True

    if game_id == "roulette":
        state.roulette_session_net = 0
        legacy.roulette_game.reset_round()
        state.current_state = state_names.STATE_ROULETTE
        return True

    if game_id == "horse_races":
        state.horse_races_session_net = 0
        state.horse_races_last_rewarded_races = 0
        legacy.start_horse_races_session()
        return True

    if game_id == "texas_holdem":
        state.current_state = state_names.STATE_TEXAS_HOLDEM_BUY_IN
        return True

    if game_id == "five_card_draw":
        state.current_state = state_names.STATE_FIVE_CARD_DRAW_BUY_IN
        return True

    if game_id == "seven_card_stud":
        state.current_state = state_names.STATE_SEVEN_CARD_STUD_BUY_IN
        return True

    if game_id == "faro":
        state.faro_session_net = 0
        legacy.start_faro_session()
        return True

    if game_id == "five_o_poker":
        state.five_o_poker_session_net = 0
        if legacy.start_five_o_poker_session():
            return True
        legacy.finish_free_play_sandbox()
        return False

    if game_id == "blind_mans_bluff":
        state.blind_mans_bluff_session_net = 0
        if legacy.start_blind_mans_bluff_session():
            return True
        legacy.finish_free_play_sandbox()
        return False

    legacy.finish_free_play_sandbox()
    return False

def draw_free_play_select():
    window.game_surface.blit(state.play_background_image, (0, 0))

    overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
    overlay.fill((8, 14, 18, 155))
    window.game_surface.blit(overlay, (0, 0))

    title = fonts.options_title_font.render(
        "FREE PLAY", True, (255, 255, 255)
    )
    window.game_surface.blit(
        title, title.get_rect(center=(BASE_WIDTH // 2, 78))
    )

    subtitle = fonts.difficulty_detail_font.render(
        "Choose any unlocked game. Free Play does not change Career cash, ratings, or fans.",
        True, (220, 225, 230)
    )
    window.game_surface.blit(
        subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 122))
    )

    for game_id in legacy.FREE_PLAY_GAME_IDS:
        rect = legacy.free_play_game_rects[game_id]
        unlocked = (game_id == "solitaire" or legacy.is_game_unlocked(game_id))
        hovered = (
            unlocked
            and state.game_mouse_pos is not None
            and rect.collidepoint(state.game_mouse_pos)
        )

        fill = (42, 105, 72) if hovered else (30, 72, 55)
        if not unlocked:
            fill = (55, 55, 58)

        pygame.draw.rect(window.game_surface, fill, rect, border_radius=10)
        pygame.draw.rect(
            window.game_surface,
            (255, 220, 105) if hovered else (235, 235, 235),
            rect, 4 if hovered else 2, border_radius=10
        )

        label = night.FREE_PLAY_GAME_NAMES.get(game_id, game_id)
        label_surface = fonts.option_label_font.render(
            label, True, (255, 255, 255)
        )
        window.game_surface.blit(
            label_surface,
            label_surface.get_rect(midleft=(rect.x + 22, rect.centery))
        )

        if not unlocked:
            required = event_select_screen.get_game_unlock_level(game_id)
            lock_surface = fonts.difficulty_detail_font.render(
                f"Level {required}", True, (210, 210, 210)
            )
            window.game_surface.blit(
                lock_surface,
                lock_surface.get_rect(midright=(rect.right - 18, rect.centery))
            )

    buttons.draw_button(
        free_play_back_rect,
        "Back",
        font=fonts.option_label_font
    )


def handle_event(event):
    """Old main-loop event branch for STATE_FREE_PLAY_SELECT."""
    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):
        if free_play_back_rect.collidepoint(state.game_mouse_pos):
            sounds.audio.play_sound("button_click")
            legacy.finish_free_play_sandbox()
            state.current_state = state_names.STATE_MODE_SELECT
        else:
            for state.free_game_id, free_rect in legacy.free_play_game_rects.items():
                if not free_rect.collidepoint(state.game_mouse_pos):
                    continue
                if state.free_game_id != "solitaire" and not legacy.is_game_unlocked(state.free_game_id):
                    break
                sounds.audio.play_sound("button_click")
                start_free_play_game(state.free_game_id)
                break


def draw():
    """Old draw-chain branch for STATE_FREE_PLAY_SELECT."""

    draw_free_play_select()
