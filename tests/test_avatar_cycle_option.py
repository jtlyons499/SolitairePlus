"""B11: the profile editor's avatar arrows must not crash on a value missing from the bank.

Fallbacks such as "base_01" are used when a save names an unknown part, but
"base_01" itself may not be in the avatar bank. cycle_option used
options.index(current), which raised ValueError on the first arrow press.
"""
import types
import unittest

import pygame

from tests.support import locate


def load_cycle_option():
    env = locate.exec_functions(["cycle_option"], {})
    return env["cycle_option"]


class CycleOptionTests(unittest.TestCase):
    def setUp(self):
        self.cycle_option = load_cycle_option()

    def test_missing_value_does_not_raise(self):
        result = self.cycle_option("missing", ["a", "b"], 1)
        self.assertIn(result, ["a", "b"])

    def test_missing_value_counts_as_first_option(self):
        # A value not in the list is treated as sitting at index 0, then stepped.
        options = ["a", "b", "c"]
        self.assertEqual(self.cycle_option("missing", options, 1), "b")
        self.assertEqual(self.cycle_option("missing", options, -1), "c")

    def test_missing_none_does_not_raise(self):
        self.assertIn(self.cycle_option(None, ["a", "b"], -1), ["a", "b"])

    def test_empty_options_returns_current(self):
        self.assertEqual(self.cycle_option("base_01", [], 1), "base_01")
        self.assertIsNone(self.cycle_option(None, [], -1))

    def test_known_values_still_cycle_and_wrap(self):
        options = [None, "glasses_01", "glasses_02"]
        self.assertEqual(self.cycle_option(None, options, 1), "glasses_01")
        self.assertEqual(self.cycle_option("glasses_02", options, 1), None)
        self.assertEqual(self.cycle_option(None, options, -1), "glasses_02")
        self.assertEqual(self.cycle_option("glasses_01", options, -1), None)


class AvatarSelectorLabelTests(unittest.TestCase):
    """The label beside the arrows used options.index too (draw_profile_screen)."""

    def setUp(self):
        self.label = locate.exec_functions(["avatar_selector_label"], {})["avatar_selector_label"]

    def test_missing_value_shows_unknown(self):
        self.assertEqual(self.label("base_01", ["base_02", "base_03"]), "-/2")

    def test_known_value_and_none(self):
        self.assertEqual(self.label("base_03", ["base_02", "base_03"]), "2/2")
        self.assertEqual(self.label(None, [None, "glasses_01"]), "None")


class ProfileAvatarMissingPartTests(unittest.TestCase):
    """get_profile_avatar indexed each bank directly and raised KeyError."""

    def build(self, selected):
        red = pygame.Surface((300, 360), pygame.SRCALPHA)
        red.fill((255, 0, 0, 255))
        assets = types.SimpleNamespace(
            avatar_bases={"base_02": red},
            avatar_eyes={}, avatar_hair={}, avatar_glasses={}, avatar_tops={},
        )
        state = types.SimpleNamespace(**selected)
        env = locate.exec_functions(["get_profile_avatar"], {"pygame": pygame, "assets": assets, "state": state})
        return env["get_profile_avatar"]()

    def test_missing_parts_are_skipped(self):
        surface = self.build(dict(
            selected_avatar_base="base_01", selected_avatar_eyes="eyes_01",
            selected_avatar_hair="hair_01", selected_avatar_glasses="glasses_09",
            selected_avatar_top="top_01",
        ))
        self.assertEqual(surface.get_size(), (300, 360))
        self.assertEqual(surface.get_at((10, 10)).a, 0)

    def test_present_parts_still_draw(self):
        surface = self.build(dict(
            selected_avatar_base="base_02", selected_avatar_eyes="eyes_01",
            selected_avatar_hair="hair_01", selected_avatar_glasses=None,
            selected_avatar_top="top_01",
        ))
        self.assertEqual(tuple(surface.get_at((10, 10))), (255, 0, 0, 255))


if __name__ == "__main__":
    unittest.main()
