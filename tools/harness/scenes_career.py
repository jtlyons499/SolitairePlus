"""Scenes: career, arcade, cryptid, Dead Man's Hand. See scripts.py for the script API.

The fixture profile starts on career day 1 of January 2026. Its calendar has Sign
Autographs on day 6 and the Press Interview on day 15; those events are opened the way
the hub's calendar button opens them (same functions, same order).
"""
import pygame

from harness.scripts import scene, to_main_menu, enter_career_hub, goto  # noqa: F401

AUTOGRAPHS_DAY = 6
PRESS_INTERVIEW_DAY = 15
CRYPTID_START_BATTLE = (1062, 537)     # "Start Career Battle" on the collection screen


def to_career_hub(h):
    yield from to_main_menu(h)
    yield from enter_career_hub(h)


def click_hub_toolbar(h, action):
    h.click(tuple(h.get("career_hub_controls").toolbar_rects[action].center))


def open_calendar_event(h, day):
    """What the hub's calendar button does for a Random Event day (without skipping days)."""
    entry = h.get("career_current_schedule")[day - 1]
    h.set("career_event_entry", entry)
    h.set("career_event_has_activity", False)
    event_id = entry.get("event_id")
    if event_id == "press_interview_01":
        h.call("start_press_interview_event")
    elif event_id == "sign_autographs_01":
        h.call("start_sign_autographs_event")
    else:
        raise AssertionError(f"day {day} is not the expected event: {entry!r}")
    h.set("current_state", h.const("CAREER_EVENT"))


def click_event_card(h, game_id):
    """Click a game card on the event-select screen (rects are rebuilt every frame by the draw code)."""
    for rect, card_id in h.get("career_event_card_rects"):
        if card_id == game_id:
            h.click(tuple(rect.center))
            return
    raise AssertionError(f"no {game_id!r} card on the event-select screen")


# ------------------------------------------------------------------ career hub and pages

@scene("career_hub")
def career_hub(h):
    yield from to_career_hub(h)
    yield 20
    h.shot()
    # The hub's only hover effect: the fast-skip button on a future calendar day.
    h.move(tuple(h.get("career_hub_controls").fast_skip_rects[2].center))
    yield 5
    h.shot("hover_fast_skip")


@scene("career_jobs")
def career_jobs(h):
    yield from to_career_hub(h)
    h.click("career_jobs_rect")
    yield from h.until_state("CAREER_JOBS", 20)
    yield 10
    h.shot()


@scene("career_real_estate")
def career_real_estate(h):
    yield from to_career_hub(h)
    h.click("career_real_estate_rect")
    yield from h.until_state("CAREER_REAL_ESTATE", 20)
    yield 10
    h.shot()


@scene("career_leaderboards")
def career_leaderboards(h):
    yield from to_career_hub(h)
    h.click("career_leaderboards_rect")
    yield from h.until_state("CAREER_LEADERBOARDS", 20)
    yield 10
    h.shot()


@scene("career_leaderboard_bio")
def career_leaderboard_bio(h):
    yield from to_career_hub(h)
    h.click("career_leaderboards_rect")
    yield from h.until_state("CAREER_LEADERBOARDS", 20)
    yield 5
    bio_rect, _entry = h.get("career_leaderboard_bio_rects")[0]
    h.click(tuple(bio_rect.center))
    yield from h.until_state("CAREER_LEADERBOARD_BIO", 20)
    yield 10
    h.shot()


@scene("career_news")
def career_news(h):
    yield from to_career_hub(h)
    h.click("career_news_rect")
    yield from h.until_state("CAREER_NEWS", 20)
    yield 10
    h.shot()


@scene("career_activity")
def career_activity(h):
    """A Bigfoot story night (the hub opens it with start_career_activity for encounter days)."""
    yield from to_career_hub(h)
    h.call("start_career_activity", work=False)
    yield from h.until_state("CAREER_ACTIVITY", 20)
    yield 15
    h.shot()


@scene("career_event_press_interview")
def career_event_press_interview(h):
    yield from to_career_hub(h)
    open_calendar_event(h, PRESS_INTERVIEW_DAY)
    yield 15
    h.shot()


@scene("career_event_autographs")
def career_event_autographs(h):
    yield from to_career_hub(h)
    open_calendar_event(h, AUTOGRAPHS_DAY)
    yield 15
    h.shot()
    # Trace part of the guide: hold the button and drag along the left edge of the diamond.
    h.mouse_down((684, 246))
    yield 2
    for step in range(1, 11):
        h.move((684 - 23 * step, 246 + 7.6 * step))
        yield 2
    h.mouse_up()
    yield 10
    h.shot("traced")


@scene("career_event_select")
def career_event_select(h):
    yield from to_career_hub(h)
    h.call("debug_open_casino_night")
    yield from h.until_state("CAREER_EVENT_SELECT", 20)
    yield 10
    h.shot()                                 # Casino Night
    h.call("debug_open_casual_cards")
    yield 10
    h.shot("casual_cards")
    h.call("debug_open_arcade_night")
    yield 10
    h.shot("arcade_night")


@scene("career_event_summary")
def career_event_summary(h):
    yield from to_career_hub(h)
    h.call("debug_open_casino_night")
    yield from h.until_state("CAREER_EVENT_SELECT", 20)
    yield 5
    h.set("career_event_has_activity", True)  # as if a game had been played tonight
    yield 2
    h.click("career_event_end_rect")
    yield from h.until_state("CAREER_EVENT_SUMMARY", 20)
    yield 10
    h.shot()


@scene("career_case_opening")
def career_case_opening(h):
    yield from to_career_hub(h)
    click_hub_toolbar(h, "cases")
    yield from h.until_state("CASE_OPENING", 20)
    yield 15
    h.shot()


# ------------------------------------------------------------------ arcade

def to_arcade_night(h):
    yield from to_career_hub(h)
    h.call("debug_open_arcade_night")
    yield from h.until_state("CAREER_EVENT_SELECT", 20)
    yield 5


@scene("arcade_token_exchange")
def arcade_token_exchange(h):
    yield from to_arcade_night(h)
    click_event_card(h, "token_exchange")
    yield from h.until_state("ARCADE_TOKEN_EXCHANGE", 20)
    yield 10
    h.shot()


@scene("arcade_prize_counter")
def arcade_prize_counter(h):
    yield from to_arcade_night(h)
    click_event_card(h, "prize_counter")
    yield from h.until_state("ARCADE_PRIZE_COUNTER", 20)
    yield 10
    h.shot()


@scene("arcade_trophy_room")
def arcade_trophy_room(h):
    yield from to_arcade_night(h)
    click_event_card(h, "prize_counter")
    yield from h.until_state("ARCADE_PRIZE_COUNTER", 20)
    yield 5
    h.click("arcade_prize_trophy_room_rect")
    yield from h.until_state("ARCADE_TROPHY_ROOM", 20)
    yield 10
    h.shot()


def buy_tokens_and_play(h, play_rect_name, machine_state):
    """Press Play with no tokens: the game opens the exchange; buy a package, then Continue."""
    h.click(play_rect_name)
    yield from h.until_state("ARCADE_TOKEN_EXCHANGE", 20)
    yield 5
    packages = h.get("arcade_token_package_rects")
    h.click(tuple(packages[max(packages)].center))   # the largest package covers every machine
    yield 5
    h.click("arcade_token_exchange_continue_rect")
    yield from h.until_state(machine_state, 20)


@scene("arcade_king_pong")
def arcade_king_pong(h):
    yield from to_arcade_night(h)
    click_event_card(h, "king_pong")
    yield from h.until_state("KING_PONG_OPPONENT_SELECT", 20)
    yield 10
    h.shot("select")
    h.click(tuple(h.get("king_pong_opponent_rects")[0].center))
    yield 5
    h.shot("select_chosen")
    yield from buy_tokens_and_play(h, "king_pong_opponent_play_rect", "KING_PONG")
    h.hold(pygame.K_UP)
    yield 40
    h.release(pygame.K_UP)
    h.hold(pygame.K_DOWN)
    yield 50
    h.release(pygame.K_DOWN)
    yield 30
    h.shot()


@scene("arcade_battle_bosses")
def arcade_battle_bosses(h):
    yield from to_arcade_night(h)
    click_event_card(h, "battle_bosses")
    yield from h.until_state("BATTLE_BOSSES_OPPONENT_SELECT", 20)
    yield 10
    h.shot("select")
    h.click(tuple(h.get("battle_bosses_choice_rects")[0].center))
    yield 5
    yield from buy_tokens_and_play(h, "battle_bosses_future_play_rect", "BATTLE_BOSSES")
    h.hold(pygame.K_LEFT)
    yield 40
    h.release(pygame.K_LEFT)
    h.hold(pygame.K_RIGHT)
    yield 50
    h.release(pygame.K_RIGHT)
    yield 30
    h.shot()


@scene("arcade_ace_invaders")
def arcade_ace_invaders(h):
    yield from to_arcade_night(h)
    click_event_card(h, "ace_invaders")
    yield from h.until_state("ACE_INVADERS_DIFFICULTY_SELECT", 20)
    yield 10
    h.shot("select")
    h.click(tuple(h.get("ace_invaders_difficulty_rects")[0].center))
    yield 5
    yield from buy_tokens_and_play(h, "ace_invaders_play_rect", "ACE_INVADERS")
    h.hold(pygame.K_LEFT)
    h.hold(pygame.K_SPACE)
    yield 40
    h.release(pygame.K_LEFT)
    h.hold(pygame.K_RIGHT)
    yield 50
    h.release(pygame.K_RIGHT)
    h.release(pygame.K_SPACE)
    yield 30
    h.shot()


@scene("arcade_suit_snake")
def arcade_suit_snake(h):
    yield from to_arcade_night(h)
    click_event_card(h, "suit_snake")
    yield from h.until_state("SUIT_SNAKE_DIFFICULTY_SELECT", 20)
    yield 10
    h.shot("select")
    h.click(tuple(h.get("suit_snake_mode_rects")[0].center))
    yield 5
    yield from buy_tokens_and_play(h, "suit_snake_play_rect", "SUIT_SNAKE")
    yield 40
    h.key(pygame.K_UP)
    yield 40
    h.key(pygame.K_LEFT)
    yield 40
    h.shot()


# ------------------------------------------------------------------ cryptid and Dead Man's Hand

@scene("cryptid_creatures")
def cryptid_creatures(h):
    yield from to_career_hub(h)
    click_hub_toolbar(h, "cryptid")
    yield from h.until_state("CRYPTID_CREATURES", 20)
    yield 15
    h.shot()
    h.click(CRYPTID_START_BATTLE)
    yield 30
    h.shot("battle")


@scene("dmh_dead_mans_hand")
def dmh_dead_mans_hand(h):
    yield from to_main_menu(h)
    h.call("start_dead_mans_hand")
    yield from h.until_state("DEAD_MANS_HAND", 20)
    yield 30
    h.shot("start")
    h.hold(pygame.K_w)
    yield 45
    h.release(pygame.K_w)
    h.move((683, 384))
    yield 2
    for step in range(10):                   # turn right with the mouse
        h.move((683 + 15 * (step + 1), 384))
        yield 2
    h.hold(pygame.K_d)
    yield 30
    h.release(pygame.K_d)
    yield 10
    h.shot()
