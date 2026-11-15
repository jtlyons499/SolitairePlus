"""Screen scenes (one or more screenshots per screen). See scripts.py for the script API.

Scenes are split by area into scenes_*.py; each registers itself with @scene. Scene
names are "<area>_<screen>"; extra screenshots of the same scene get a suffix through
h.shot("suffix").
"""
from harness.scripts import scene, to_main_menu  # noqa: F401


@scene("menu_splash")
def splash(h):
    yield 45
    h.shot()


@scene("menu_main")
def main_menu(h):
    yield from to_main_menu(h)
    yield 30
    h.shot()


from harness import scenes_menus, scenes_career, scenes_tables  # noqa: E402,F401
