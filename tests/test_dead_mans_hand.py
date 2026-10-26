from dead_mans_hand import LEVELS, LEVEL_VALIDATION_ERRORS, normalize_angle, wall_at


def test_dead_mans_hand_levels_validate():
    assert LEVEL_VALIDATION_ERRORS == []
    assert len(LEVELS) >= 3


def test_dead_mans_hand_maps_are_enclosed_and_spawns_are_open():
    for level in LEVELS:
        px, py, _angle = level["player"]
        assert wall_at(level, px, py) is None
        for _card, x, y in level["enemies"]:
            assert wall_at(level, x, y) is None


def test_angle_normalization():
    assert -3.14160 < normalize_angle(0.0) < 3.14160
    assert -3.14160 < normalize_angle(100.0) < 3.14160
    assert -3.14160 < normalize_angle(-100.0) < 3.14160


def test_dead_mans_hand_has_card_enemy_progression():
    cards = [card for level in LEVELS for card, _x, _y in level["enemies"]]
    assert any(card.startswith("J") for card in cards)
    assert any(card.startswith("Q") for card in cards)
    assert any(card.startswith("K") for card in cards)
