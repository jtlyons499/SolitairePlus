"""Scenes: poker, casino and casual card tables. See scripts.py for the script API.

Most tables are opened the way Free Play does it (``start_free_play_game(game_id)``,
which is what clicking a game tile on the Free Play screen calls), so they run with
the Free Play sandbox cash. Button positions are fixed layout coordinates (they live in
the *_ui modules, not in main.py, so they are not looked up by name).
"""
from harness.scripts import scene, to_main_menu, enter_career_hub, goto  # noqa: F401

# Buy-in screens (Hold'em, Draw and Stud share the layout): the 25% and 50% buttons.
BUY_IN_25 = (400, 380)
BUY_IN_50 = (588, 380)

# Poker action buttons ("Check/Call").
HOLDEM_CALL = (1130, 642)
DRAW_CALL = (1130, 642)
DRAW_CONFIRM = (1116, 692)       # "Draw" during the draw round (no cards selected = stand pat)
STUD_CALL = (1130, 656)
BLUFF_CHECK_CALL = (1020, 712)   # blind_mans_bluff_ui.py: Check / Call share one button

# Roulette (roulette_ui.py)
ROULETTE_CHIP_100 = (670, 668)
ROULETTE_RED = (257, 578)
ROULETTE_NUMBER_17 = (575, 322)
ROULETTE_DOZEN_1 = (380, 494)
ROULETTE_SPIN = (1090, 605)

# Horse races (horse_races_ui.py)
HORSE_ROW_1 = (1165, 189)
HORSE_CHIP_100 = (667, 588)
HORSE_PLACE_BET = (1000, 599)
HORSE_RACE_ACTION = (1184, 679)

# Faro (faro_ui.py)
FARO_CHIP_100 = (379, 718)
FARO_RANK_7 = (971, 222)
FARO_RANK_K = (915, 324)
FARO_DEAL = (1000, 718)


def open_free_play(h, game_id, frames=20):
    """What clicking a game tile on the Free Play screen does."""
    h.set("current_game_mode", "free")
    h.set("current_state", h.const("FREE_PLAY_SELECT"))
    yield 5
    assert h.call("start_free_play_game", game_id), f"start_free_play_game({game_id!r}) refused"
    yield frames


def poker_can_act(game):
    return game.current_actor == 0 and game.can_player_act_now()


def play_poker_until(h, game_name, call_pos, done, limit=2400, draw_confirm=None, what="poker condition"):
    """Check/call whenever it is the player's turn (and stand pat in Draw) until done(game)."""
    for _ in range(limit):
        game = h.get(game_name)
        if done(game):
            return
        if (draw_confirm is not None and game.current_stage == "draw"
                and not game.player_draw_complete and not game.player_folded):
            h.click(draw_confirm)
            yield 20
            continue
        if poker_can_act(game):
            h.click(call_pos)
            yield 20
            continue
        yield 1
    raise AssertionError(f"timed out waiting for {what} (stage {h.get(game_name).current_stage!r})")


# ------------------------------------------------------------------ poker

@scene("poker_holdem_buy_in")
def holdem_buy_in(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "texas_holdem")
    h.move((588, 380))                      # hover the 50% button
    yield 5
    h.shot()


@scene("poker_holdem")
def holdem(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "texas_holdem")
    h.click(BUY_IN_25)
    yield from h.until_state("TEXAS_HOLDEM", 30)
    yield 45
    h.shot("hand_start")
    yield from play_poker_until(h, "texas_holdem_game", HOLDEM_CALL,
                                lambda g: g.hand_complete or g.current_stage in ("flop", "turn", "river"),
                                what="the flop")
    yield 90
    h.shot("mid_hand")
    yield from play_poker_until(h, "texas_holdem_game", HOLDEM_CALL, lambda g: g.hand_complete,
                                what="the end of the hand")
    yield 30
    h.shot("hand_result")


@scene("poker_debug_npc_select")
def debug_poker_npc_select(h):
    yield from to_main_menu(h)
    h.call("open_debug_poker_npc_select", "texas_holdem")
    yield 15
    h.shot()


@scene("poker_draw_buy_in")
def draw_buy_in(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "five_card_draw")
    h.shot()


@scene("poker_draw")
def draw(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "five_card_draw")
    h.click(BUY_IN_25)
    yield from h.until_state("FIVE_CARD_DRAW", 30)
    yield 45
    h.shot("hand_start")
    yield from play_poker_until(h, "five_card_draw_game", DRAW_CALL,
                                lambda g: g.hand_complete or g.current_stage == "draw", what="the draw round")
    yield 30
    h.shot("draw_round")
    yield from play_poker_until(h, "five_card_draw_game", DRAW_CALL, lambda g: g.hand_complete,
                                draw_confirm=DRAW_CONFIRM, what="the end of the hand")
    yield 30
    h.shot("hand_result")


@scene("poker_stud_buy_in")
def stud_buy_in(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "seven_card_stud")
    h.shot()


@scene("poker_stud")
def stud(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "seven_card_stud")
    h.click(BUY_IN_25)
    yield from h.until_state("SEVEN_CARD_STUD", 30)
    yield 45
    h.shot("hand_start")
    start_stage = h.get("seven_card_stud_game").current_stage
    yield from play_poker_until(h, "seven_card_stud_game", STUD_CALL,
                                lambda g: g.hand_complete or g.current_stage != start_stage,
                                what="the next street")
    yield 90
    h.shot("mid_hand")


@scene("poker_five_o")
def five_o(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "five_o_poker", frames=60)
    h.shot()


@scene("poker_blind_mans_bluff")
def blind_mans_bluff(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "blind_mans_bluff", frames=60)
    h.shot("start")
    h.click(BLUFF_CHECK_CALL)                     # check; the NPCs check too, so the hand reaches its showdown
    yield 240
    h.shot("showdown")


# ------------------------------------------------------------------ casino

@scene("casino_blackjack_bet")
def blackjack_bet(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "blackjack")
    h.shot()
    h.move(h.center("blackjack_bet_5_rect"))     # hover a bet button
    yield 5
    h.shot("hover")


@scene("casino_blackjack")
def blackjack(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "blackjack")
    h.click("blackjack_bet_5_rect")
    yield from h.until_state("BLACKJACK", 30)
    yield 90
    h.shot("dealt")
    h.click(h.get("blackjack_bet_dropdown_rects")[2].center)   # choose the next hand's bet (5%)
    yield 10
    h.shot("next_bet_chosen")
    game = h.get("blackjack_game")
    if not game.round_complete:
        h.click("blackjack_stand_rect")
    yield from h.until(lambda: h.get("blackjack_game").round_complete, 900, "the round to finish")
    yield 120
    h.shot("result")


@scene("casino_roulette")
def roulette(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "roulette")
    h.shot("empty")
    h.click(ROULETTE_CHIP_100)
    yield 3
    for spot in (ROULETTE_RED, ROULETTE_NUMBER_17, ROULETTE_DOZEN_1):
        h.click(spot)
        yield 3
    yield 10
    h.shot("bets_placed")
    h.click(ROULETTE_SPIN)
    yield 60
    h.shot("spinning")
    yield from h.until(lambda: not h.get("roulette_game").spinning, 1800, "the wheel to stop")
    yield 60
    h.shot("result")


@scene("casino_horse_races")
def horse_races(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "horse_races")
    h.click(HORSE_ROW_1)
    yield 3
    h.click(HORSE_CHIP_100)
    yield 3
    h.click(HORSE_PLACE_BET)
    yield 10
    h.shot("betting")
    h.click(HORSE_RACE_ACTION)
    yield from h.until(lambda: h.get("horse_races_game").stage == "racing", 60, "the race to start")
    yield 180
    h.shot("racing")
    yield from h.until(lambda: h.get("horse_races_game").stage == "results", 3600, "the race results")
    yield 30
    h.shot("results")


@scene("casino_faro")
def faro(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "faro")
    h.shot("start")
    h.click(FARO_CHIP_100)
    yield 3
    h.click(FARO_RANK_7)
    yield 3
    h.click(FARO_RANK_K)
    yield 10
    h.shot("bets_placed")
    h.click(FARO_DEAL)
    yield 60
    h.shot("after_deal")


# ------------------------------------------------------------------ casual cards

@scene("cards_crazy_eights")
def crazy_eights(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "crazy_eights", frames=60)
    h.shot()


@scene("cards_bango")
def bango(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "bango", frames=60)
    h.shot()


@scene("cards_score_four_mode_select")
def score_four_mode_select(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "score_four")
    h.shot()
    h.click("score_four_solo_rect")               # opens the solo difficulty menu
    yield 10
    h.shot("difficulty_menu")


@scene("cards_score_four_opponent_select")
def score_four_opponent_select(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "score_four")
    h.click("score_four_competitive_rect")
    yield from h.until_state("SCORE_FOUR_OPPONENT_SELECT", 30)
    yield 10
    h.shot()


@scene("cards_score_four")
def score_four(h):
    yield from to_main_menu(h)
    yield from open_free_play(h, "score_four")
    h.click("score_four_solo_rect")
    yield 10
    h.click((683, 354))                            # "standard" difficulty
    yield from h.until_state("SCORE_FOUR", 30)
    yield 30
    h.shot("solo")
    h.set("current_state", h.const("SCORE_FOUR_MODE_SELECT"))
    yield 5
    h.click("score_four_competitive_rect")
    yield from h.until_state("SCORE_FOUR_OPPONENT_SELECT", 30)
    yield 5
    h.click(h.get("score_four_opponent_rects")[0].center)
    yield from h.until_state("SCORE_FOUR", 30)
    yield 60
    h.shot("competitive")
