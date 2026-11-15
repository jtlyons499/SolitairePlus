"""Horse races screen and its music cue (moved out of legacy.py)."""
from solitaireplus.games.casino.horse_races_ui import ACTION_CHIP_10 as HORSE_RACES_ACTION_CHIP_10
from solitaireplus.games.casino.horse_races_ui import ACTION_CHIP_100 as HORSE_RACES_ACTION_CHIP_100
from solitaireplus.games.casino.horse_races_ui import ACTION_CHIP_50 as HORSE_RACES_ACTION_CHIP_50
from solitaireplus.games.casino.horse_races_ui import ACTION_CHIP_500 as HORSE_RACES_ACTION_CHIP_500
from solitaireplus.games.casino.horse_races_ui import ACTION_CLEAR_BETS as HORSE_RACES_ACTION_CLEAR_BETS
from solitaireplus.games.casino.horse_races_ui import ACTION_HORSE_PREFIX as HORSE_RACES_ACTION_HORSE_PREFIX
from solitaireplus.games.casino.horse_races_ui import ACTION_PLACE as HORSE_RACES_ACTION_PLACE
from solitaireplus.games.casino.horse_races_ui import ACTION_PLACE_BET as HORSE_RACES_ACTION_PLACE_BET
from solitaireplus.games.casino.horse_races_ui import ACTION_RETURN as HORSE_RACES_ACTION_RETURN
from solitaireplus.games.casino.horse_races_ui import ACTION_SHOW as HORSE_RACES_ACTION_SHOW
from solitaireplus.games.casino.horse_races_ui import ACTION_START_RACE as HORSE_RACES_ACTION_START_RACE
from solitaireplus.games.casino.horse_races_ui import ACTION_WIN as HORSE_RACES_ACTION_WIN
from solitaireplus.games.casino.horse_races import HorseRaceGame
from solitaireplus.career import career_rewards
from solitaireplus.games.casino.horse_races_ui import draw_horse_races
from solitaireplus.games.casino.horse_races_ui import get_horse_races_action
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.career.session_summary import track_night_cash
from solitaireplus.app.lazy import lazy
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
night = lazy("solitaireplus.career.events.night")
leveling = lazy("solitaireplus.profile.leveling")


horse_races_game = HorseRaceGame()

def settle_horse_race_result():

    if horse_races_game.races_completed <= state.horse_races_last_rewarded_races:
        state.horse_races_session_net = horse_races_game.get_session_net()
        return False

    state.horse_races_last_rewarded_races = horse_races_game.races_completed
    state.horse_races_session_net = horse_races_game.get_session_net()
    state.career_event_has_activity = True

    # Every completed race gets a quick winner celebration. This is separate
    # from whether the player personally held a winning ticket.
    sounds.audio.play_sound("celebration_3")

    if horse_races_game.race_net > 0:
        career_rewards.award_fans_for_cash_win(
            horse_races_game.race_net,
            "Horse race win"
        )

    leveling.award_game_xp(
        "horse_races",
        won=(horse_races_game.race_net > 0),
    )

    return True

def start_horse_race_music():

    if state.horse_race_music_sound is None:
        return False

    if state.horse_race_music_channel is not None:
        try:
            if state.horse_race_music_channel.get_busy():
                return True
        except pygame.error:
            pass

    # Take the base volume only while the music is not ducked yet: a second start (after the cue
    # was cut off) must not take the ducked volume as the one to restore later (B31).
    if state.horse_race_previous_music_volume is None:
        state.horse_race_previous_music_volume = float(sounds.audio.music_volume)
    sounds.audio.set_music_volume(state.horse_race_previous_music_volume * 0.22)

    try:
        state.horse_race_music_channel = pygame.mixer.find_channel(True)
        if state.horse_race_music_channel is None:
            sounds.audio.set_music_volume(state.horse_race_previous_music_volume)
            state.horse_race_previous_music_volume = None
            return False

        state.horse_race_music_channel.set_volume(
            max(0.0, min(1.0, state.horse_race_previous_music_volume * 0.70))
        )
        state.horse_race_music_channel.play(
            state.horse_race_music_sound,
            loops=-1,
            fade_ms=250,
        )
        return True
    except pygame.error:
        sounds.audio.set_music_volume(state.horse_race_previous_music_volume)
        state.horse_race_previous_music_volume = None
        state.horse_race_music_channel = None
        return False


def stop_horse_race_music(fade_ms=500):

    if state.horse_race_music_channel is not None:
        try:
            state.horse_race_music_channel.fadeout(max(0, int(fade_ms)))
        except pygame.error:
            pass

    state.horse_race_music_channel = None

    if state.horse_race_previous_music_volume is not None:
        sounds.audio.set_music_volume(state.horse_race_previous_music_volume)

    state.horse_race_previous_music_volume = None


def start_horse_races_session():

    state.horse_races_session_net = 0
    state.horse_races_last_rewarded_races = 0
    horse_races_game.start_session(state.career_cash)
    state.current_state = state_names.STATE_HORSE_RACES
    return True


def finish_horse_races_session():

    state.career_cash = horse_races_game.cash_out()
    state.horse_races_session_net = horse_races_game.get_session_net()

    if horse_races_game.races_completed > 0:
        state.career_event_has_activity = True

    if (
            state.current_game_mode == "career"
            and horse_races_game.races_completed > 0
            and not horse_races_game.reward_claimed
    ):
        night.record_career_event_result(
            "horse_races",
            won=(state.horse_races_session_net > 0),
            net=state.horse_races_session_net,
            races=horse_races_game.races_completed,
            profitable_races=horse_races_game.races_with_profit,
        )
        track_night_cash(legacy.game_namespace(), "horse_races", state.horse_races_session_net)
        horse_races_game.reward_claimed = True

    if state.current_game_mode == "free":
        legacy.finish_free_play_sandbox()
        state.current_state = state_names.STATE_FREE_PLAY_SELECT
    else:
        state.current_state = state_names.STATE_CAREER_EVENT_SELECT

    return state.horse_races_session_net


def leave():
    """Leaving the horse races by any route (Return, the F10 debug menu, a debug launch, the end
    of the night...) ends the race cue and puts the music back to its volume from before (B31)."""
    stop_horse_race_music(300)


def handle_event(event):
    """Old main-loop event branch for STATE_HORSE_RACES."""

    if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):
        horse_action = get_horse_races_action(state.game_mouse_pos)

        if (
                horse_action is not None
                and horse_action.startswith(HORSE_RACES_ACTION_HORSE_PREFIX)
                and horse_races_game.stage == "betting"
        ):
            try:
                state.horse_index = int(
                    horse_action[len(HORSE_RACES_ACTION_HORSE_PREFIX):]
                )
            except ValueError:
                state.horse_index = -1
            if horse_races_game.set_selected_horse(state.horse_index):
                sounds.audio.play_sound("button_click")

        elif horse_action == HORSE_RACES_ACTION_WIN:
            if horse_races_game.set_bet_type("win"):
                sounds.audio.play_sound("button_click")

        elif horse_action == HORSE_RACES_ACTION_PLACE:
            if horse_races_game.set_bet_type("place"):
                sounds.audio.play_sound("button_click")

        elif horse_action == HORSE_RACES_ACTION_SHOW:
            if horse_races_game.set_bet_type("show"):
                sounds.audio.play_sound("button_click")

        elif horse_action == HORSE_RACES_ACTION_CHIP_10:
            if horse_races_game.set_chip_value(10):
                sounds.audio.play_sound("button_click")

        elif horse_action == HORSE_RACES_ACTION_CHIP_50:
            if horse_races_game.set_chip_value(50):
                sounds.audio.play_sound("button_click")

        elif horse_action == HORSE_RACES_ACTION_CHIP_100:
            if horse_races_game.set_chip_value(100):
                sounds.audio.play_sound("button_click")

        elif horse_action == HORSE_RACES_ACTION_CHIP_500:
            if horse_races_game.set_chip_value(500):
                sounds.audio.play_sound("button_click")

        elif horse_action == HORSE_RACES_ACTION_PLACE_BET:
            if horse_races_game.place_selected_bet():
                sounds.audio.play_sound("poker_chips_1")

        elif horse_action == HORSE_RACES_ACTION_CLEAR_BETS:
            if horse_races_game.clear_bets():
                sounds.audio.play_sound("poker_chips_1")

        elif horse_action == HORSE_RACES_ACTION_START_RACE:
            if horse_races_game.stage == "betting":
                if horse_races_game.start_race(pygame.time.get_ticks()):
                    sounds.audio.play_sound("button_click")
                    start_horse_race_music()
                    state.career_event_has_activity = True
            elif horse_races_game.stage == "results":
                if horse_races_game.prepare_next_race():
                    sounds.audio.play_sound("button_click")

        elif (
                horse_action == HORSE_RACES_ACTION_RETURN
                and horse_races_game.stage != "racing"
        ):
            sounds.audio.play_sound("button_click")
            stop_horse_race_music(300)
            finish_horse_races_session()


def draw():
    """Old draw-chain branch for STATE_HORSE_RACES."""

    horse_previous_stage = horse_races_game.stage
    horse_races_game.update(pygame.time.get_ticks())
    if (
            horse_previous_stage == "racing"
            and horse_races_game.stage == "results"
    ):
        stop_horse_race_music(600)
    settle_horse_race_result()

    draw_horse_races(
        window.game_surface,
        state.game_mouse_pos,
        horse_races_game,
    )
