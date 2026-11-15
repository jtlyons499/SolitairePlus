"""Replay journeys: scripted playthroughs with value checkpoints. See scripts.py for the API.

Each journey records h.checkpoint(label) at its key moments; tools/replay.py compares the
recorded values (state, cash, XP, level, rating, career day, fans) and screenshots.
"""
import pygame

from harness.scripts import (PROFILE_SLOT_1, enter_career_hub, journey, leave_splash,  # noqa: F401
                             load_fixture_profile, to_main_menu)
from harness.scenes_menus import card_click, instant_solitaire_win, to_free_play_solitaire

PROFILE_SLOT_2 = (450, 345)


def window_pos(h, pos):
    """Game coordinates -> window coordinates while the game believes its window is another size.

    The harness window is always 1366x768. Before W1 the game scaled mouse positions by
    WINDOW_WIDTH/HEIGHT after picking another window size; since W1 SDL does the scaling and the
    game's mapping is the identity. Ask the game which one it does, so this works on both.
    """
    if tuple(h.call("window_to_game_coords", (1000, 500))) == (1000, 500):
        return pos
    width = h.get("WINDOW_WIDTH", 1366)
    height = h.get("WINDOW_HEIGHT", 768)
    return (round(pos[0] * width / 1366), round(pos[1] * height / 768))


@journey("01_create_profile")
def create_profile(h):
    yield from leave_splash(h)
    h.checkpoint("profile_select")
    h.click(PROFILE_SLOT_2)                      # empty slot -> profile creation
    yield from h.until_state("PROFILE", 30)
    yield 5
    h.click("profile_name_rect")
    yield 3
    h.type_text("Replay Tester")
    yield 3
    h.key(pygame.K_RETURN)
    yield 3
    h.click("profile_age_rect")
    yield 3
    h.type_text("41")
    yield 3
    h.checkpoint("profile_filled")
    h.click("profile_save_rect")
    yield from h.until_state("MENU", 30)
    yield 10
    h.checkpoint("menu_after_create", "player_name", "current_profile_slot")


@journey("02_options")
def options(h):
    yield from to_main_menu(h)
    h.click("options_rect")
    yield from h.until_state("OPTIONS", 30)
    yield 5
    h.checkpoint("options_open")
    h.click("music_off_rect")
    yield 5
    h.click("music_ambient_rect")
    yield 5
    slider = h.rect("music_slider_rect")
    h.mouse_down((slider.x + slider.width // 4, slider.centery))
    yield 3
    h.move((slider.x + slider.width // 3, slider.centery))
    yield 3
    h.mouse_up()
    yield 3
    sfx = h.rect("sfx_slider_rect")
    h.click((sfx.x + sfx.width * 3 // 4, sfx.centery))
    yield 5
    h.checkpoint("options_audio_changed")
    h.click(h.get("resolution_rects")[1].center)  # 1600x900
    yield 10
    h.checkpoint("options_window_1600", "WINDOW_WIDTH", "WINDOW_HEIGHT")
    h.click(window_pos(h, h.get("resolution_rects")[0].center))  # back to 1366x768
    yield 10
    h.checkpoint("options_window_1366", "WINDOW_WIDTH", "WINDOW_HEIGHT")
    h.click("options_back_rect")
    yield from h.until_state("MENU", 30)
    yield 5
    h.checkpoint("menu_after_options")


@journey("03_solitaire")
def solitaire(h):
    yield from to_free_play_solitaire(h)
    h.checkpoint("dealt")
    game = h.get("game")
    for _ in range(3):
        yield from card_click(h, game.stock_rect.center)
        yield 20
    h.checkpoint("after_stock_moves")
    instant_solitaire_win(h)          # the designer's instant win (F8 today, the F10 menu after D1)
    yield from h.until_state("RECAP", 1800)
    yield 10
    h.checkpoint("recap_reward", "level_up_queue")
    h.click("recap_yes_rect")
    yield 30
    h.checkpoint("after_recap", "level_up_queue")


@journey("04_career_day")
def career_day(h):
    yield from to_main_menu(h)
    h.click("new_game_rect")
    yield from h.until_state("MODE_SELECT", 30)
    yield 5
    h.click("play_career_rect")
    yield from h.until_state("CAREER_HUB", 30)
    yield 20
    h.checkpoint("hub")
    for button, state in (("career_jobs_rect", "CAREER_JOBS"), ("career_real_estate_rect", "CAREER_REAL_ESTATE"),
                          ("career_news_rect", "CAREER_NEWS"), ("career_leaderboards_rect", "CAREER_LEADERBOARDS")):
        h.click(button)
        yield from h.until_state(state, 30)
        yield 15
        h.checkpoint(state.lower())
        h.click("career_subpage_back_rect")
        yield from h.until_state("CAREER_HUB", 30)
        yield 10
    h.click("career_calendar_skip_rect")
    yield 20
    h.checkpoint("after_skip_day")


@journey("15_debug_menu_quit")
def debug_menu_then_quit(h):
    yield from to_main_menu(h)
    h.key(pygame.K_F10)
    yield from h.until_state("DEBUG_MENU", 30)
    yield 10
    h.checkpoint("debug_menu")
    h.key(pygame.K_F10)
    yield from h.until_state("MENU", 30)
    yield 5
    h.checkpoint("back_to_menu")
    h.expect_quit()
    h.click("quit_rect")
    yield 30


# ------------------------------------------------------------------ arcade, Cryptid, Dead Man's Hand

from harness.scenes_career import (CRYPTID_START_BATTLE, buy_tokens_and_play, click_event_card,  # noqa: E402
                                   click_hub_toolbar, to_arcade_night, to_career_hub)

ARCADE_MACHINES = {
    # journey suffix: (event card, select state, choice rects variable, play rect, machine state, keys to hold)
    "king_pong": ("king_pong", "KING_PONG_OPPONENT_SELECT", "king_pong_opponent_rects",
                  "king_pong_opponent_play_rect", "KING_PONG", (pygame.K_UP, pygame.K_DOWN)),
    "battle_bosses": ("battle_bosses", "BATTLE_BOSSES_OPPONENT_SELECT", "battle_bosses_choice_rects",
                      "battle_bosses_future_play_rect", "BATTLE_BOSSES", (pygame.K_LEFT, pygame.K_RIGHT)),
    "ace_invaders": ("ace_invaders", "ACE_INVADERS_DIFFICULTY_SELECT", "ace_invaders_difficulty_rects",
                     "ace_invaders_play_rect", "ACE_INVADERS", (pygame.K_LEFT, pygame.K_RIGHT)),
    "suit_snake": ("suit_snake", "SUIT_SNAKE_DIFFICULTY_SELECT", "suit_snake_mode_rects",
                   "suit_snake_play_rect", "SUIT_SNAKE", (pygame.K_UP, pygame.K_LEFT)),
}


def play_machine_for_five_seconds(machine):
    card, select_state, choices, play_rect, machine_state, keys = ARCADE_MACHINES[machine]

    def run(h):
        yield from to_arcade_night(h)
        click_event_card(h, card)
        yield from h.until_state(select_state, 20)
        yield 5
        choice_rects = h.get(choices)
        first = choice_rects[0] if isinstance(choice_rects, (list, tuple)) else next(iter(choice_rects.values()))
        h.click(tuple(first.center))
        yield 5
        yield from buy_tokens_and_play(h, play_rect, machine_state)
        h.checkpoint("machine_started", "arcade_state")
        for second in range(5):              # five seconds of play, alternating two keys
            key = keys[second % 2]
            h.hold(key)
            yield 30
            if machine == "ace_invaders":
                h.key(pygame.K_SPACE)
            yield 30
            h.release(key)
        h.checkpoint("after_five_seconds", "arcade_state")

    return run


for _machine in ARCADE_MACHINES:
    journey(f"13_arcade_{_machine}")(play_machine_for_five_seconds(_machine))


@journey("14_cryptid_and_dead_mans_hand")
def cryptid_and_dead_mans_hand(h):
    yield from to_career_hub(h)
    click_hub_toolbar(h, "cryptid")
    yield from h.until_state("CRYPTID_CREATURES", 20)
    yield 15
    h.checkpoint("cryptid_collection")
    h.click(CRYPTID_START_BATTLE)
    yield 120
    h.checkpoint("cryptid_battle")
    h.key(pygame.K_F10)                      # leave through the debug menu, like a tester would
    yield from h.until_state("DEBUG_MENU", 20)
    yield 5
    h.call("start_dead_mans_hand")
    yield from h.until_state("DEAD_MANS_HAND", 20)
    yield 20
    h.checkpoint("dmh_started")
    h.hold(pygame.K_w)
    yield 60
    h.release(pygame.K_w)
    for step in range(10):
        h.move((683 + 12 * (step + 1), 384))
        yield 3
    h.hold(pygame.K_a)
    yield 60
    h.release(pygame.K_a)
    yield 30
    h.checkpoint("dmh_moved")


# ------------------------------------------------------------------ tables (Free Play sandbox cash)

from harness.scenes_tables import (BUY_IN_25, DRAW_CALL, DRAW_CONFIRM, FARO_CHIP_100, FARO_DEAL,  # noqa: E402
                                   FARO_RANK_7, FARO_RANK_K, HOLDEM_CALL, HORSE_CHIP_100, HORSE_PLACE_BET,
                                   HORSE_RACE_ACTION, HORSE_ROW_1, ROULETTE_CHIP_100, ROULETTE_DOZEN_1,
                                   ROULETTE_NUMBER_17, ROULETTE_RED, ROULETTE_SPIN, STUD_CALL, open_free_play,
                                   play_poker_until)


@journey("05_blackjack")
def blackjack(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "blackjack")
    h.checkpoint("bet_screen", "blackjack_session_net")
    h.click("blackjack_bet_5_rect")
    yield from h.until_state("BLACKJACK", 30)
    yield 90
    h.checkpoint("dealt", "blackjack_session_net")
    if not h.get("blackjack_game").round_complete:
        h.click("blackjack_hit_rect")
        yield 60
        h.checkpoint("after_hit", "blackjack_session_net")
    if not h.get("blackjack_game").round_complete:
        h.click("blackjack_stand_rect")
    yield from h.until(lambda: h.get("blackjack_game").round_complete, 900, "the round to finish")
    yield 120
    h.checkpoint("round_settled", "blackjack_session_net")


@journey("06_roulette")
def roulette(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "roulette")
    h.click(ROULETTE_CHIP_100)
    yield 3
    for spot in (ROULETTE_RED, ROULETTE_NUMBER_17, ROULETTE_DOZEN_1):
        h.click(spot)
        yield 3
    yield 10
    h.checkpoint("bets_placed", "roulette_session_net")
    h.click(ROULETTE_SPIN)
    yield 30
    h.checkpoint("spinning", "roulette_session_net")
    yield from h.until(lambda: not h.get("roulette_game").spinning, 1800, "the wheel to stop")
    yield 60
    h.checkpoint("result", "roulette_session_net")


@journey("07_horse_race")
def horse_race(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "horse_races")
    h.click(HORSE_ROW_1)
    yield 3
    h.click(HORSE_CHIP_100)
    yield 3
    h.click(HORSE_PLACE_BET)
    yield 10
    h.checkpoint("ticket_placed", "horse_races_session_net")
    h.click(HORSE_RACE_ACTION)
    yield from h.until(lambda: h.get("horse_races_game").stage == "racing", 60, "the race to start")
    yield 120
    h.checkpoint("racing", "horse_races_session_net")
    yield from h.until(lambda: h.get("horse_races_game").stage == "results", 3600, "the race results")
    yield 30
    h.checkpoint("results", "horse_races_session_net")


@journey("08_faro")
def faro(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "faro")
    h.click(FARO_CHIP_100)
    yield 3
    h.click(FARO_RANK_7)
    yield 3
    h.click(FARO_RANK_K)
    yield 10
    h.checkpoint("bets_placed", "faro_session_net")
    for turn in range(3):
        h.click(FARO_DEAL)
        yield 60
        h.checkpoint(f"turn_{turn + 1}", "faro_session_net")


def poker_hand(game_id, state_name, game_name, call_pos, net_name, draw_confirm=None):
    def run(h):
        yield from to_main_menu(h)
        yield from open_free_play(h, game_id)
        h.click(BUY_IN_25)
        yield from h.until_state(state_name, 30)
        yield 45
        h.checkpoint("hand_start", net_name)
        yield from play_poker_until(h, game_name, call_pos, lambda g: g.hand_complete,
                                    draw_confirm=draw_confirm, what="the end of the hand")
        yield 60
        h.checkpoint("hand_complete", net_name)
    return run


journey("09_holdem")(poker_hand("texas_holdem", "TEXAS_HOLDEM", "texas_holdem_game", HOLDEM_CALL,
                                "texas_holdem_session_net"))
journey("10_five_card_draw")(poker_hand("five_card_draw", "FIVE_CARD_DRAW", "five_card_draw_game", DRAW_CALL,
                                        "five_card_draw_session_net", draw_confirm=DRAW_CONFIRM))
journey("11_seven_card_stud")(poker_hand("seven_card_stud", "SEVEN_CARD_STUD", "seven_card_stud_game", STUD_CALL,
                                         "seven_card_stud_session_net"))


@journey("12_crazy_eights_and_score_four")
def crazy_eights_and_score_four(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "crazy_eights", frames=60)
    h.checkpoint("crazy_eights_dealt")
    yield 240                                # NPC turns play out
    h.checkpoint("crazy_eights_later")
    h.set("current_state", h.const("FREE_PLAY_SELECT"))
    yield 5
    yield from open_free_play(h, "score_four")
    h.click("score_four_solo_rect")
    yield 10
    h.click((683, 354))                      # "standard" difficulty
    yield from h.until_state("SCORE_FOUR", 30)
    yield 30
    h.checkpoint("score_four_solo")
