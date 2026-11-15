"""Headless, deterministic game runner shared by tools/screen_harness.py and tools/replay.py.

The game is run from a checkout's ``main.py`` in a child process with:

* the dummy SDL video/audio drivers and a 1366x768 window (no scaling);
* a virtual clock that advances exactly 1/60 s per frame;
* fixed random seeds (``random``, unseeded ``random.Random()``, ``SystemRandom``,
  ``secrets``) and ``PYTHONHASHSEED=0``;
* scripted input (events, mouse position, held keys) instead of the real devices;
* a fake ``pygame.mixer.music`` that follows the virtual clock;
* a temporary ``LOCALAPPDATA`` holding the fixture save and app settings.

A script is a generator that runs inside ``pygame.display.flip()`` once per frame,
so it can read and change game state between frames (see ``sim.Driver``).
Nothing here is shipped with the game.
"""
import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
