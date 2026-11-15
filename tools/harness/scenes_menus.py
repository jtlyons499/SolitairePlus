"""Scenes: menus, profile, Solitaire and the debug screens. See scripts.py for the script API."""
import os
from pathlib import Path

import pygame

from harness.scripts import (scene, to_main_menu, leave_splash, load_fixture_profile,  # noqa: F401
                             enter_career_hub, goto, PROFILE_SLOT_1)

PROFILE_SLOT_2 = (PROFILE_SLOT_1[0], PROFILE_SLOT_1[1] + 120)
PROFILE_SLOT_3 = (PROFILE_SLOT_1[0], PROFILE_SLOT_1[1] + 240)
MODE_SELECT_FREE_PLAY = (300, 384)     # left half of the mode-select screen


# ------------------------------------------------------------------ helpers

def saves_folder():
    return Path(os.environ["LOCALAPPDATA"]) / "SimpleSolitaire" / "saves"


def card_click(h, pos, clicks=1):
    """A click on the Solitaire table. Card clicks read event.clicks, which h.click does not set."""
    pos = (int(pos[0]), int(pos[1]))
    h.move(pos)
    h.post(pygame.MOUSEBUTTONDOWN, pos=pos, button=1, clicks=clicks, touch=False, window=None)
    yield 1
    h.post(pygame.MOUSEBUTTONUP, pos=pos, button=1, clicks=clicks, touch=False, window=None)
    yield 1


def to_mode_select(h):
    yield from to_main_menu(h)
    h.click("new_game_rect")
    yield from h.until_state("MODE_SELECT", 30)
    yield 5


def to_free_play_select(h):
    yield from to_mode_select(h)
    h.click(MODE_SELECT_FREE_PLAY)
    yield from h.until_state("FREE_PLAY_SELECT", 30)
    yield 5


def to_difficulty(h):
    yield from to_free_play_select(h)
    h.click(tuple(h.get("free_play_game_rects")["solitaire"].center))
    yield from h.until_state("DIFFICULTY", 30)
    yield 5


def to_free_play_solitaire(h):
    """Free Play -> Solitaire -> Easy: a fresh (seeded) deal."""
    yield from to_difficulty(h)
    h.click("difficulty_easy_rect")
    yield from h.until_state("PLAYING", 30)
    yield 90   # let the deal settle


def instant_solitaire_win(h):
    """What the old F8 debug key does: mark the round won with a fixed summary and start the win animation."""
    game = h.get("game")
    game.round_won = True
    game.round_summary = {
        "moves": 112,
        "elapsed_seconds": 387,
        "base_score": 5000,
        "move_bonus": 1700,
        "time_bonus": 952,
        "score": 7652,
        "xp_earned": 150,
        "remark": "Efficient work.",
    }
    game.audio.play_sound("celebration_1")
    game.start_debug_victory_animation()


# ------------------------------------------------------------------ menus

@scene("menu_main_hover")
def main_menu_hover(h):
    yield from to_main_menu(h)
    h.move(h.center("options_rect"))
    yield 10
    h.shot()


@scene("menu_hover_after_key")
def hover_after_key(h):
    """B15: a key press must not drop the hover (drawing uses the mouse position of the frame)."""
    yield from to_main_menu(h)
    h.move(h.center("options_rect"))
    yield 10
    h.key(pygame.K_LSHIFT)
    yield 10
    h.shot()
    # The main menu hovers with menu_mouse_pos; Options (like most screens) with game_mouse_pos.
    h.click("options_rect")
    yield from h.until_state("OPTIONS", 30)
    h.move(h.center("options_back_rect"))
    yield 10
    h.key(pygame.K_LSHIFT)
    yield 10
    h.shot("options")


@scene("menu_mode_select")
def mode_select(h):
    yield from to_mode_select(h)
    h.move(MODE_SELECT_FREE_PLAY)
    yield 10
    h.shot()


@scene("menu_free_play_select")
def free_play_select(h):
    yield from to_free_play_select(h)
    yield 10
    h.shot()


@scene("menu_difficulty")
def difficulty(h):
    yield from to_difficulty(h)
    yield 10
    h.shot()


@scene("menu_how_to_play")
def how_to_play(h):
    yield from to_main_menu(h)
    h.click("how_to_play_rect")
    yield from h.until_state("HOW_TO_PLAY", 30)
    yield 10
    h.shot()
    categories = list(h.get("help_category_rects").items())
    h.click(tuple(categories[1][1].center))          # expand the second category
    yield 10
    h.shot("category")
    pages = list(h.get("help_page_rects").items())
    h.click(tuple(pages[-1][1].center))               # open its last page
    yield 10
    h.shot("page")


@scene("menu_achievements")
def achievements(h):
    yield from to_main_menu(h)
    h.click("achievements_rect")
    yield from h.until_state("ACHIEVEMENTS", 30)
    yield 10
    h.shot()
    h.move((683, 400))
    h.wheel(-3)
    yield 10
    h.shot("scrolled")


@scene("menu_options")
def options(h):
    yield from to_main_menu(h)
    h.click("options_rect")
    yield from h.until_state("OPTIONS", 30)
    yield 10
    h.shot()


@scene("menu_options_update_available")
def options_update_available(h):
    """The Options update panel and the main-menu banner when an update has been found."""
    yield from to_main_menu(h)
    h.get("update_checker").result = {"status": "update_available", "latest": "9.9.9"}
    yield 10
    h.shot("menu_banner")
    h.click("options_rect")
    yield from h.until_state("OPTIONS", 30)
    yield 10
    h.shot()


@scene("menu_customize")
def customize(h):
    yield from to_main_menu(h)
    h.click("customize_rect")
    yield from h.until_state("CUSTOMIZE", 30)
    yield 10
    h.shot()
    h.click("customize_felts_rect")
    yield 10
    h.shot("felts")
    h.click("customize_cursors_rect")
    yield 10
    h.shot("cursors")


# ------------------------------------------------------------------ profile

@scene("profile_select")
def profile_select(h):
    yield from leave_splash(h)
    h.move((683, 700))
    yield 10
    h.shot()


@scene("profile_select_delete_confirm")
def profile_select_delete_confirm(h):
    yield from leave_splash(h)
    h.click(tuple(h.get("profile_delete_rects")[0].center))
    yield 10
    if not h.get("confirm_delete_profile"):
        raise AssertionError("the delete confirmation did not open")
    h.shot()


@scene("profile_select_damaged")
def profile_select_damaged(h):
    """A damaged save in slot 2 shows as unavailable; clicking it explains why."""
    (saves_folder() / "profile_2.json").write_text("{this is not a valid save", encoding="utf-8")
    yield from leave_splash(h)
    yield 10
    h.shot()
    h.click(PROFILE_SLOT_2)
    yield 10
    if h.state != h.const("PROFILE_SELECT"):
        raise AssertionError("clicking a damaged save left the profile-select screen")
    h.shot("notice")


@scene("profile_edit")
def profile_edit(h):
    yield from to_main_menu(h)
    h.click("profile_rect")
    yield from h.until_state("PROFILE", 30)
    yield 10
    h.shot()
    h.click("profile_name_rect")
    yield 10
    h.shot("name_field_active")


@scene("profile_create")
def profile_create(h):
    yield from leave_splash(h)
    h.click(PROFILE_SLOT_3)              # empty slot -> new profile
    yield from h.until_state("PROFILE", 30)
    yield 10
    if not h.get("profile_creation_mode"):
        raise AssertionError("slot 3 did not open profile creation")
    h.shot()


# ------------------------------------------------------------------ Solitaire

@scene("solitaire_playing")
def solitaire_playing(h):
    yield from to_free_play_solitaire(h)
    h.shot()
    game = h.get("game")
    for _ in range(3):                    # deal from the stock three times
        yield from card_click(h, game.stock_rect.center)
        yield 20
    h.click("game_hint_rect")
    yield 10
    h.shot("after_moves")


@scene("solitaire_pause_menu")
def solitaire_pause_menu(h):
    yield from to_free_play_solitaire(h)
    h.click("game_menu_rect")
    yield 10
    if not h.get("game_pause_menu_open"):
        raise AssertionError("the pause menu did not open")
    h.shot()
    h.click("pause_menu_rect")
    yield 10
    if not h.get("confirm_return_to_menu"):
        raise AssertionError("the return-to-menu confirmation did not open")
    h.shot("return_confirm")


@scene("solitaire_recap")
def solitaire_recap(h):
    yield from to_free_play_solitaire(h)
    instant_solitaire_win(h)
    yield 30
    h.shot("victory_animation")
    yield from h.until_state("RECAP", 1800)
    yield 10
    h.shot()


@scene("solitaire_level_up")
def solitaire_level_up(h):
    yield from to_main_menu(h)
    level = h.get("player_level")
    needed = h.call("get_next_level_xp", level) - h.get("player_xp") + 1
    result = h.call("add_player_xp", needed)
    if not result.get("level_up_screens"):
        raise AssertionError(f"adding {needed} XP at level {level} gave no level-up screen")
    h.get("level_up_queue").extend(result["level_up_screens"])
    h.set("post_round_return_state", h.const("MENU"))
    h.call("advance_level_up_screen")
    yield from h.until_state("LEVEL_UP", 10)
    yield 30
    h.shot()


@scene("solitaire_head_to_head")
def solitaire_head_to_head(h):
    yield from to_main_menu(h)
    h.call("debug_open_head_to_head")
    yield from h.until_state("CAREER_EVENT", 10)
    yield 10
    h.shot("opponent_select")
    h.set("head_to_head_selected_index", 0)
    if not h.call("begin_selected_head_to_head_race"):
        raise AssertionError("the Head-to-Head race did not start")
    yield from h.until_state("PLAYING", 10)
    yield 30
    h.shot("countdown")
    race = h.get("head_to_head_race")
    yield from h.until(lambda: not race.is_countdown_active(pygame.time.get_ticks()), 900, "countdown end")
    yield 120
    h.shot()


# ------------------------------------------------------------------ debug

@scene("debug_menu")
def debug_menu(h):
    yield from to_main_menu(h)
    h.key(pygame.K_F10)
    yield from h.until_state("DEBUG_MENU", 10)
    yield 10
    h.shot()


@scene("debug_poker_npc_select")
def debug_poker_npc_select(h):
    yield from to_main_menu(h)
    h.call("open_debug_poker_npc_select", "texas_holdem")
    yield from h.until_state("DEBUG_POKER_NPC_SELECT", 10)
    yield 10
    h.shot()
