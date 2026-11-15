"""Sound effects, music playlists and the horse-race music cue (moved out of main.py)."""
from solitaireplus.app import paths
import os
import pygame
from solitaireplus.app.audio import AudioManager
from solitaireplus.app import state

# ==================================================
# AUDIO
# ==================================================

audio = AudioManager()


SUPPORTED_MUSIC_EXTENSIONS = (".ogg", ".mp3", ".wav")


def discover_music_files(directory, prefix):
    """Return sorted drop-in music files whose names start with prefix."""
    if not os.path.isdir(directory):
        return []

    tracks = []
    for filename in os.listdir(directory):
        lower_name = filename.lower()
        if not lower_name.startswith(prefix.lower()):
            continue
        if not lower_name.endswith(SUPPORTED_MUSIC_EXTENSIONS):
            continue

        full_path = os.path.join(directory, filename)
        if os.path.isfile(full_path):
            tracks.append(full_path.replace("\\", "/"))

    return sorted(tracks, key=lambda path: os.path.basename(path).lower())


def discover_named_music_track(directory, stem):
    """Find one optional cabinet track, preferring OGG, then MP3, then WAV."""
    if not os.path.isdir(directory):
        return None

    files_by_lower_name = {
        filename.lower(): filename
        for filename in os.listdir(directory)
    }

    for extension in SUPPORTED_MUSIC_EXTENSIONS:
        lookup_name = f"{stem}{extension}".lower()
        actual_name = files_by_lower_name.get(lookup_name)
        if actual_name:
            full_path = os.path.join(directory, actual_name)
            if os.path.isfile(full_path):
                return full_path.replace("\\", "/")

    return None


ARCADE_MACHINE_MUSIC_TRACKS = {
    game_id: discover_named_music_track(str(paths.asset("music/arcade")), game_id)
    for game_id in (
        "king_pong",
        "battle_bosses",
        "ace_invaders",
        "suit_snake",
    )
}


# ----------------------------
# Instrumental soundtrack
# ----------------------------

instrumental_tracks = [
    str(paths.asset("music/hello.mp3")),
    str(paths.asset("music/block.mp3")),
    str(paths.asset("music/rock.mp3")),
    str(paths.asset("music/rail_trail.mp3")),
    str(paths.asset("music/rail_trail_pt2.mp3")),
    str(paths.asset("music/electric.mp3")),
    #"assets/music/on_death_and_dying.mp3",
    str(paths.asset("music/jay.mp3")),
    str(paths.asset("music/high_note.mp3")),
]

audio.add_playlist(
    "instrumental",
    instrumental_tracks
)


# ----------------------------
# Ambient soundtrack
# ----------------------------

# Any supported file named ambient_* inside assets/music joins the rotation
# automatically. Adding ambient_05, ambient_06, etc. no longer requires code.
ambient_tracks = discover_music_files(
    str(paths.asset("music")),
    "ambient_",
)

ambient_startup_track = next(
    (
        track
        for track in ambient_tracks
        if os.path.splitext(os.path.basename(track))[0].lower() == "ambient_01"
    ),
    ambient_tracks[0] if ambient_tracks else None,
)

audio.add_playlist(
    "ambient",
    ambient_tracks,
    startup_track=ambient_startup_track,
)


# ----------------------------
# Sound effects
# ----------------------------

audio.load_sound(
    "button_click",
    str(paths.asset("sounds/button_click.wav"))
)

audio.load_sound(
    "card_draw",
    str(paths.asset("sounds/card_draw.wav"))
)

audio.load_sound(
    "card_flip",
    str(paths.asset("sounds/card_flip.wav"))
)

audio.load_sound(
    "poker_check",
    str(paths.asset("sounds/check.wav"))
)

audio.load_sound(
    "poker_chips_1",
    str(paths.asset("sounds/chips_1.wav"))
)

audio.load_sound(
    "poker_chips_2",
    str(paths.asset("sounds/chips_2.wav"))
)

audio.load_sound(
    "poker_chips_3",
    str(paths.asset("sounds/chips_3.wav"))
)

audio.load_sound(
    "poker_hand_win",
    str(paths.asset("sounds/hand_win.wav"))
)

# Reused by both Five-O presentation and King Pong point scoring.
audio.load_sound(
    "five_o_column_win",
    str(paths.asset("sounds/five_o_column_win.wav"))
)

audio.load_sound(
    "five_o_column_loss",
    str(paths.asset("sounds/five_o_column_loss.wav"))
)

# Battle Bosses SFX are optional while the custom audio is being created.
# Dropping any of these WAVs into assets/sounds automatically activates the
# corresponding gameplay event without making missing work-in-progress audio
# a startup error.
for battle_sound_name, battle_sound_path in (
        ("battle_bosses_ricochet", str(paths.asset("sounds/battle_bosses_ricochet.wav"))),
        ("battle_bosses_fort_hit", str(paths.asset("sounds/battle_bosses_fort_hit.wav"))),
        ("battle_bosses_eliminate", str(paths.asset("sounds/battle_bosses_eliminate.wav"))),
        ("battle_bosses_win", str(paths.asset("sounds/battle_bosses_win.wav"))),
        ("battle_bosses_loss", str(paths.asset("sounds/battle_bosses_loss.wav"))),
):
    if os.path.isfile(battle_sound_path):
        try:
            audio.load_sound(battle_sound_name, battle_sound_path)
        except pygame.error:
            pass

# Ace Invaders uses the same drop-in audio contract. The cabinet remains fully
# playable while these work-in-progress sounds are absent.
for ace_sound_name, ace_sound_path in (
        ("ace_invaders_shoot", str(paths.asset("sounds/ace_invaders_shoot.wav"))),
        ("ace_invaders_enemy_shoot", str(paths.asset("sounds/ace_invaders_enemy_shoot.wav"))),
        ("ace_invaders_enemy_hit", str(paths.asset("sounds/ace_invaders_enemy_hit.wav"))),
        ("ace_invaders_player_hit", str(paths.asset("sounds/ace_invaders_player_hit.wav"))),
        ("ace_invaders_shield_hit", str(paths.asset("sounds/ace_invaders_shield_hit.wav"))),
        ("ace_invaders_wave_clear", str(paths.asset("sounds/ace_invaders_wave_clear.wav"))),
        ("ace_invaders_loss", str(paths.asset("sounds/ace_invaders_loss.wav"))),
):
    if os.path.isfile(ace_sound_path):
        try:
            audio.load_sound(ace_sound_name, ace_sound_path)
        except pygame.error:
            pass

# Suit Snake audio follows the same optional drop-in pattern.
for suit_snake_sound_name, suit_snake_sound_path in (
        ("suit_snake_collect", str(paths.asset("sounds/suit_snake_collect.wav"))),
        ("suit_snake_deck", str(paths.asset("sounds/suit_snake_deck.wav"))),
        ("suit_snake_loss", str(paths.asset("sounds/suit_snake_loss.wav"))),
):
    if os.path.isfile(suit_snake_sound_path):
        try:
            audio.load_sound(suit_snake_sound_name, suit_snake_sound_path)
        except pygame.error:
            pass

# Dead Man's Hand keeps its SFX in a dedicated folder so adding weapons/enemies
# does not clutter assets/sounds. New names are preferred; Prototype 1's flat
# filenames remain optional fallbacks so existing local builds do not go silent.
for dmh_sound_name, dmh_sound_candidates in (
        ("dead_mans_hand_pistol_shot", (
            str(paths.asset("sounds/dead_mans_hand/pistol_shot.wav")),
            str(paths.asset("sounds/dead_mans_hand_gunshot.wav")),
        )),
        ("dead_mans_hand_pistol_reload", (
            str(paths.asset("sounds/dead_mans_hand/pistol_reload.wav")),
            str(paths.asset("sounds/dead_mans_hand_pistol_reload.wav")),
        )),
        ("dead_mans_hand_kar98k_shot", (str(paths.asset("sounds/dead_mans_hand/kar98k_shot.wav")),)),
        ("dead_mans_hand_kar98k_bolt", (str(paths.asset("sounds/dead_mans_hand/kar98k_bolt.wav")),)),
        ("dead_mans_hand_kar98k_reload", (str(paths.asset("sounds/dead_mans_hand/kar98k_reload.wav")),)),
        ("dead_mans_hand_thompson_shot", (str(paths.asset("sounds/dead_mans_hand/thompson_shot.wav")),)),
        ("dead_mans_hand_thompson_reload", (str(paths.asset("sounds/dead_mans_hand/thompson_reload.wav")),)),
        ("dead_mans_hand_scar20_shot", (str(paths.asset("sounds/dead_mans_hand/scar20_shot.wav")),)),
        ("dead_mans_hand_scar20_reload", (str(paths.asset("sounds/dead_mans_hand/scar20_reload.wav")),)),
        ("dead_mans_hand_weapon_pickup", (str(paths.asset("sounds/dead_mans_hand/weapon_pickup.wav")),)),
        ("dead_mans_hand_enemy_hit", (
            str(paths.asset("sounds/dead_mans_hand/enemy_hit.wav")),
            str(paths.asset("sounds/dead_mans_hand_enemy_hit.wav")),
        )),
        ("dead_mans_hand_enemy_down", (
            str(paths.asset("sounds/dead_mans_hand/enemy_down.wav")),
            str(paths.asset("sounds/dead_mans_hand_enemy_down.wav")),
        )),
        ("dead_mans_hand_player_hit", (
            str(paths.asset("sounds/dead_mans_hand/player_hit.wav")),
            str(paths.asset("sounds/dead_mans_hand_player_hit.wav")),
        )),
        ("dead_mans_hand_player_down", (
            str(paths.asset("sounds/dead_mans_hand/player_down.wav")),
            str(paths.asset("sounds/dead_mans_hand_player_down.wav")),
        )),
):
    for dmh_sound_path in dmh_sound_candidates:
        if not os.path.isfile(dmh_sound_path):
            continue
        try:
            audio.load_sound(dmh_sound_name, dmh_sound_path)
            break
        except pygame.error:
            continue

audio.load_sound(
    "card_move",
    str(paths.asset("sounds/card_move.wav"))
)

audio.load_sound(
    "card_shuffle",
    str(paths.asset("sounds/card_shuffle.wav"))
)

audio.load_sound(
    "startup",
    str(paths.asset("sounds/startup.wav"))
)

audio.load_sound(
    "celebration_1",
    str(paths.asset("sounds/celebration_1.wav"))
)

audio.load_sound(
    "celebration_2",
    str(paths.asset("sounds/celebration_2.wav"))
)

audio.load_sound(
    "celebration_3",
    str(paths.asset("sounds/celebration_3.wav"))
)

audio.load_sound(
    "celebration_4",
    str(paths.asset("sounds/celebration_4.wav"))
)

audio.load_sound(
    "celebration_5",
    str(paths.asset("sounds/celebration_5.wav"))
)

try:
    if os.path.exists(str(paths.asset("music/horse_race.mp3"))):
        state.horse_race_music_sound = pygame.mixer.Sound(
            str(paths.asset("music/horse_race.mp3"))
        )
except (pygame.error, OSError):
    state.horse_race_music_sound = None
