"""The Solitaire table: the one rules.Game engine that every Solitaire round is played on (moved
out of legacy.py). Other screens borrow its card art (game.card_fronts, game.get_card_back_surface()).

The engine is built when this module is first imported. Start-up (app/startup.py) imports it once the
window is open, at the point where the old main.py built it: building it deals a first hand, which
draws seeded random numbers, so it must stay at that point in the start-up order.
"""
from solitaireplus.app import sounds
from solitaireplus.app import state
from solitaireplus.app import window
from solitaireplus.app.lazy import lazy
from solitaireplus.games.solitaire.rules import Game
assets = lazy("solitaireplus.app.assets")

# ==================================================
# GAME
# ==================================================

game = Game(
    window.game_surface,
    sounds.audio
)

# Temporarily keep the experimental verified-deal generator out of ordinary
# play while it is being rebuilt. Head-to-Head still uses its race-only
# constructive deal path.
VERIFIED_DEALS_ENABLED = False

# ==================================================
# COSMETIC SYNC
# ==================================================

def sync_selected_cosmetics():
    game.set_felt_surface(
        assets.felt_surfaces[state.selected_felt]
    )
