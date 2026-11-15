"""B66: roulette chip labels must not truncate $1,500 to '1k'.

draw_bet_chip() abbreviates stakes of $1,000 and up. It used to do
amount // 1000, so a $1,500 stake showed as '1k'. The label now keeps one
decimal where needed ('1.5k') and stays '1k', '2k' ... for whole thousands.
"""
import unittest

from solitaireplus.games.casino import roulette_ui


class RouletteChipLabelTests(unittest.TestCase):

    def test_half_thousands_keep_one_decimal(self):
        self.assertEqual(roulette_ui.format_chip_amount(1500), "1.5k")
        self.assertEqual(roulette_ui.format_chip_amount(2500), "2.5k")
        # From $10k up the decimal is dropped so the label fits on the 26 px chip.
        self.assertEqual(roulette_ui.format_chip_amount(12500), "12k")
        self.assertEqual(roulette_ui.format_chip_amount(99900), "99k")

    def test_whole_thousands_have_no_decimal(self):
        self.assertEqual(roulette_ui.format_chip_amount(1000), "1k")
        self.assertEqual(roulette_ui.format_chip_amount(2000), "2k")
        self.assertEqual(roulette_ui.format_chip_amount(10000), "10k")

    def test_never_overstates_the_stake(self):
        # Stakes are multiples of $10; extra digits past one decimal are dropped,
        # never rounded up (1,990 must not read as 2k).
        self.assertEqual(roulette_ui.format_chip_amount(1990), "1.9k")
        self.assertEqual(roulette_ui.format_chip_amount(1050), "1k")
        self.assertEqual(roulette_ui.format_chip_amount(1150), "1.1k")

    def test_amounts_below_1000_are_unchanged(self):
        for amount in (10, 50, 100, 500, 990):
            self.assertEqual(roulette_ui.format_chip_amount(amount), str(amount))

    def test_draw_bet_chip_tells_1500_apart_from_1000(self):
        import pygame

        pygame.font.init()

        def chip_pixels(amount):
            surface = pygame.Surface((100, 100))
            roulette_ui.draw_bet_chip(surface, pygame.Rect(0, 0, 100, 100), amount, None)
            return pygame.image.tobytes(surface, "RGB")

        self.assertTrue(
            chip_pixels(1500) != chip_pixels(1000),
            "a $1,500 chip is drawn exactly like a $1,000 chip",
        )


if __name__ == "__main__":
    unittest.main()
