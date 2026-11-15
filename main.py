from solitaireplus.app.runtime_support import bootstrap
bootstrap()

# Dispatch before importing single-player modules or initializing its window.
import sys as _launch_sys
if "--multiplayer" in _launch_sys.argv:
    from solitaireplus.app.multiplayer_launcher import run_multiplayer
    run_multiplayer()
    raise SystemExit(0)

# If an update was interrupted (e.g. power cut), let the updater undo it first.
# It restarts the game afterwards. See update_check.py.
from solitaireplus.app import update_check
if update_check.recover_if_needed():
    raise SystemExit(0)
update_check.cleanup_leftovers()

# Real screen pixels, not Windows' stretched "logical" ones (must happen before pygame opens
# the display). Multiplayer gets the same treatment in its own window code.
from solitaireplus.app import window
window.enable_dpi_awareness()

# Everything else lives in the solitaireplus package; loop.run() is the old main loop.
from solitaireplus.app import loop

loop.run()
