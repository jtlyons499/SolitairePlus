from pathlib import Path


def test_debug_menu_uses_expandable_minigame_categories():
    source = Path("debug_menu.py").read_text(encoding="utf-8")
    assert "MINIGAME_CATEGORIES = (" in source
    assert '"Arcade Games"' in source
    assert '"Casual / Puzzle"' in source
    assert '"Casino"' in source
    assert '"Poker"' in source
    assert "def toggle_minigame_category(action):" in source
    assert 'marker = "-" if expanded else "+"' in source
    assert '_expanded_minigame_category = None' in source


def test_arcade_debug_entries_are_available_from_minigame_accordion():
    debug_source = Path("debug_menu.py").read_text(encoding="utf-8")
    main_source = Path("main.py").read_text(encoding="utf-8")

    assert 'ACTION_ARCADE_NIGHT = "arcade_night"' in debug_source
    assert 'ACTION_KING_PONG = "king_pong"' in debug_source
    assert 'ACTION_BATTLE_BOSSES = "battle_bosses"' in debug_source
    assert 'ACTION_ACE_INVADERS = "ace_invaders"' in debug_source
    assert 'ACTION_SUIT_SNAKE = "suit_snake"' in debug_source
    assert '(ACTION_ARCADE_NIGHT, "Arcade Night")' in debug_source
    assert '(ACTION_KING_PONG, "King Pong")' in debug_source
    assert '(ACTION_BATTLE_BOSSES, "Battle Bosses")' in debug_source
    assert '(ACTION_ACE_INVADERS, "Ace Invaders")' in debug_source
    assert '(ACTION_SUIT_SNAKE, "Suit Snake")' in debug_source

    assert "def debug_prepare_arcade_night():" in main_source
    assert "def debug_open_arcade_night():" in main_source
    assert "def debug_open_king_pong():" in main_source
    assert "def debug_open_battle_bosses():" in main_source
    assert "def debug_open_ace_invaders():" in main_source
    assert "def debug_open_suit_snake():" in main_source
    assert "is_minigame_category_action(debug_action)" in main_source
    assert "toggle_minigame_category(debug_action)" in main_source


def test_niche_games_moved_into_relevant_minigame_categories():
    source = Path("debug_menu.py").read_text(encoding="utf-8")
    challenge_block = source.split("CHALLENGE_ENTRIES = (", 1)[1].split(")\n\nPROGRESSION_ENTRIES", 1)[0]
    assert "ACTION_FARO" not in challenge_block
    assert "ACTION_FIVE_O_POKER" not in challenge_block
    assert "ACTION_BLIND_MANS_BLUFF" not in challenge_block

    assert '(ACTION_FARO, "Faro")' in source
    assert '(ACTION_FIVE_O_POKER, "Five-O Poker")' in source
    assert '(ACTION_BLIND_MANS_BLUFF, "Blind Man\'s Bluff")' in source
