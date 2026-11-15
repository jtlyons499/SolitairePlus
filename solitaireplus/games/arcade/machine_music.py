"""Which music track each arcade machine plays (read by the main loop; moved out of legacy.py)."""
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
sounds = lazy("solitaireplus.app.sounds")


ARCADE_MACHINE_MUSIC_BY_STATE = {
    state_names.STATE_KING_PONG: sounds.ARCADE_MACHINE_MUSIC_TRACKS.get("king_pong"),
    state_names.STATE_BATTLE_BOSSES: sounds.ARCADE_MACHINE_MUSIC_TRACKS.get("battle_bosses"),
    state_names.STATE_ACE_INVADERS: sounds.ARCADE_MACHINE_MUSIC_TRACKS.get("ace_invaders"),
    state_names.STATE_SUIT_SNAKE: sounds.ARCADE_MACHINE_MUSIC_TRACKS.get("suit_snake"),
}
