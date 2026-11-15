"""B61: Dead Man's Hand enemies must only spawn where the player can reach them.

The spawn picker used to consider every open floor cell, so a room sealed off
by walls (unreachable from the player start) could receive card enemies that
the player can never get to, leaving the level unwinnable.
"""

import unittest

from solitaireplus.games.dead_mans_hand.levels import LEVELS, _build_map, _enemy_spawns

# 16x12 map with a 4x4 room in the top-right corner (x 11-14, y 1-4) walled off
# by a vertical wall at x=10 and a horizontal wall at y=5.  The room is the part
# of the map farthest from the player, so a picker that ignores reachability
# puts enemies there.
SEALED_BLOCKS = (("1", 10, 1, 1, 5), ("1", 11, 5, 4, 1))
PLAYER = (2.5, 9.5, 0.0)
CARDS = ("9H", "9S", "JS", "9D", "KH", "QH")


def _in_sealed_room(x, y):
    return 11 <= x < 15 and 1 <= y < 5


def _reachable_cells(rows, player):
    start = (int(player[0]), int(player[1]))
    seen = {start}
    stack = [start]
    while stack:
        x, y = stack.pop()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= ny < len(rows) and 0 <= nx < len(rows[ny]) and rows[ny][nx] == "." and (nx, ny) not in seen:
                seen.add((nx, ny))
                stack.append((nx, ny))
    return seen


class DeadMansHandSpawnReachabilityTest(unittest.TestCase):
    def setUp(self):
        self.rows = _build_map(16, 12, SEALED_BLOCKS)

    def test_sealed_room_is_really_sealed(self):
        reachable = _reachable_cells(self.rows, PLAYER)
        sealed = [(x, y) for y in range(1, 5) for x in range(11, 15)]
        self.assertTrue(all(self.rows[y][x] == "." for x, y in sealed))
        self.assertFalse(any(cell in reachable for cell in sealed))

    def test_no_enemy_spawns_inside_a_sealed_room(self):
        for salt in range(12):
            spawns = _enemy_spawns(self.rows, PLAYER, CARDS, salt=salt)
            self.assertEqual(len(spawns), len(CARDS), f"salt {salt}")
            for card, x, y in spawns:
                self.assertFalse(_in_sealed_room(x, y), f"salt {salt}: {card} spawned in the sealed room at {(x, y)}")

    def test_every_spawn_is_reachable_from_the_player_start(self):
        reachable = _reachable_cells(self.rows, PLAYER)
        for salt in range(12):
            for card, x, y in _enemy_spawns(self.rows, PLAYER, CARDS, salt=salt):
                self.assertTrue((int(x), int(y)) in reachable, f"salt {salt}: {card} at {(x, y)} is unreachable")

    def test_spawns_that_were_already_reachable_keep_their_cells(self):
        # With salt 0 the old picker put 9H and 9D in the sealed room; the other
        # four were reachable and must not move.
        spawns = {card: (x, y) for card, x, y in _enemy_spawns(self.rows, PLAYER, CARDS, salt=0)}
        self.assertEqual(spawns["9S"], (14.5, 7.5))
        self.assertEqual(spawns["JS"], (13.5, 6.5))
        self.assertEqual(spawns["KH"], (12.5, 8.5))
        self.assertEqual(spawns["QH"], (11.5, 9.5))

    def test_spawns_stay_spaced_apart(self):
        for salt in range(12):
            spawns = _enemy_spawns(self.rows, PLAYER, CARDS, salt=salt)
            cells = {(x, y) for _card, x, y in spawns}
            self.assertEqual(len(cells), len(spawns), f"salt {salt}: two enemies share a cell")

    def test_authored_levels_are_fully_reachable_and_unchanged(self):
        # Every authored level is one connected area, so the fix must not move
        # any authored spawn (the first level's roster is pinned here).
        for level in LEVELS:
            reachable = _reachable_cells(level["map"], level["player"])
            for card, x, y in level["enemies"]:
                self.assertTrue((int(x), int(y)) in reachable, f"{level['name']}: {card} at {(x, y)} is unreachable")
        self.assertEqual(
            LEVELS[0]["enemies"],
            (("9H", 12.5, 1.5), ("9S", 14.5, 9.5), ("JS", 13.5, 10.5), ("9D", 9.5, 1.5), ("KH", 11.5, 5.5)),
        )

    def test_no_reachable_floor_means_no_spawns(self):
        # The player is boxed into a single cell: nothing else is reachable.
        rows = _build_map(10, 10, (("1", 1, 1, 3, 1), ("1", 1, 3, 3, 1), ("1", 1, 2, 1, 1), ("1", 3, 2, 1, 1)))
        self.assertEqual(rows[2][2], ".")
        self.assertEqual(_enemy_spawns(rows, (2.5, 2.5, 0.0), CARDS, salt=0), ())


if __name__ == "__main__":
    unittest.main()
