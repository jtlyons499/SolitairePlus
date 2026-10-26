from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_debug_menu_exposes_dead_mans_hand_as_standalone_prototype():
    source = (ROOT / "debug_menu.py").read_text(encoding="utf-8")
    assert 'ACTION_DEAD_MANS_HAND = "dead_mans_hand"' in source
    assert '"Standalone / Prototype"' in source
    assert '(ACTION_DEAD_MANS_HAND, "Dead Man\'s Hand")' in source


def test_main_has_isolated_dead_mans_hand_state_and_launcher():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert 'STATE_DEAD_MANS_HAND = "dead_mans_hand"' in source
    assert 'def start_dead_mans_hand(return_state=None):' in source
    assert 'start_dead_mans_hand(return_state=STATE_DEBUG_MENU)' in source
    assert 'dead_mans_hand_game.draw(game_surface)' in source


def test_dead_mans_hand_not_attached_to_existing_night_framework():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    # The prototype must remain standalone until its own Career calendar-day
    # integration is intentionally added in a later batch.
    assert 'CAREER_EVENT_GAMES[CAREER_ACTIVITY_DEAD_MANS_HAND]' not in source
    assert 'debug_prepare_arcade_night()\n    start_dead_mans_hand' not in source
