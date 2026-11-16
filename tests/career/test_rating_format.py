"""B65: RatingPoints keeps fractional precision but always formats as whole points."""
import unittest

from solitaireplus.career.ratings import RatingPoints, make_player_rating_bundle


class RatingPointsFormatTests(unittest.TestCase):
    def setUp(self):
        self.rating = RatingPoints(1234.6)

    def test_value_keeps_fractional_precision(self):
        self.assertEqual(float(self.rating), 1234.6)
        self.assertEqual(str(self.rating), "1235")

    def test_default_and_grouping_specs_show_whole_points(self):
        self.assertEqual(format(self.rating, ""), "1235")
        self.assertEqual(format(self.rating, ","), "1,235")
        self.assertEqual(f"{self.rating:,}", "1,235")
        self.assertEqual(f"{self.rating:+,}", "+1,235")

    def test_d_specs_keep_working(self):
        self.assertEqual(format(self.rating, "d"), "1235")
        self.assertEqual(format(self.rating, ",d"), "1,235")
        self.assertEqual(format(self.rating, "+d"), "+1235")
        self.assertEqual(format(self.rating, ">8d"), "    1235")
        self.assertEqual(format(self.rating, "08,d"), "0,001,235")

    def test_f_specs_show_rounded_whole_number(self):
        self.assertEqual(format(self.rating, "f"), "1235")
        self.assertEqual(format(self.rating, "F"), "1235")
        self.assertEqual(format(self.rating, ".0f"), "1235")
        self.assertEqual(format(self.rating, ",.1f"), "1,235")
        self.assertEqual(format(self.rating, ">8.2f"), "    1235")
        self.assertEqual(format(self.rating, "+,.3f"), "+1,235")
        self.assertEqual(format(self.rating, "z,.1f"), "1,235")
        self.assertEqual(f"{self.rating:,.0f}", "1,235")

    def test_precision_without_type_shows_whole_number(self):
        self.assertEqual(format(self.rating, ".2"), "1235")
        self.assertEqual(format(self.rating, ",.1"), "1,235")

    def test_f_as_fill_character_is_not_a_type(self):
        self.assertEqual(format(self.rating, "f>6"), "ff1235")
        self.assertEqual(format(self.rating, "f>6d"), "ff1235")
        self.assertEqual(format(self.rating, "f>6.1f"), "ff1235")

    def test_other_presentation_types_unchanged(self):
        self.assertEqual(format(self.rating, ".1e"), format(1235, ".1e"))
        self.assertEqual(format(self.rating, "x"), format(1235, "x"))
        with self.assertRaises(ValueError):
            format(self.rating, "q")

    def test_bundle_ratings_format_like_game_labels(self):
        bundle = make_player_rating_bundle(1500.4)
        self.assertEqual(f"Current Rating: {bundle['strategy']:,}", "Current Rating: 1,500")
        self.assertEqual(f"{bundle['strategy']:,.0f}", "1,500")
        self.assertEqual(f"{bundle['strategy']:,.1f}", "1,500")


if __name__ == "__main__":
    unittest.main()
