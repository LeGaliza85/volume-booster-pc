"""Tests for the percentage/dB maths and the perceptual slider mapping."""

from __future__ import annotations

import unittest

import gainmath


class PercentDbTests(unittest.TestCase):
    def test_reference_points(self):
        self.assertEqual(gainmath.percent_to_db(100), 0.0)
        self.assertEqual(gainmath.percent_to_db(200), 6.02)
        self.assertEqual(gainmath.percent_to_db(500), 13.98)
        self.assertEqual(gainmath.percent_to_db(1000), 20.0)

    def test_zero_is_silence(self):
        self.assertEqual(gainmath.percent_to_db(0), gainmath.SILENT_DB)


class SliderPositionTests(unittest.TestCase):
    def test_extremes(self):
        self.assertAlmostEqual(gainmath.percent_to_position(0, 1000), 0.0)
        self.assertAlmostEqual(gainmath.percent_to_position(1000, 1000), 1.0)
        self.assertEqual(gainmath.position_to_percent(0.0, 1000), 0)
        self.assertEqual(gainmath.position_to_percent(1.0, 1000), 1000)

    def test_zero_db_is_two_thirds_of_the_travel(self):
        self.assertAlmostEqual(gainmath.percent_to_position(100, 1000), 2 / 3, places=3)

    def test_equal_db_steps_take_equal_travel(self):
        # 100->200 and 200->400 are both +6.02 dB, so they must move the same.
        first = gainmath.percent_to_position(200, 1000) - gainmath.percent_to_position(100, 1000)
        second = gainmath.percent_to_position(400, 1000) - gainmath.percent_to_position(200, 1000)
        self.assertAlmostEqual(first, second, places=3)

    def test_the_top_of_the_slider_is_not_dead(self):
        # The old linear scale spent 80 % of the travel on the last 14 dB. The
        # new one is uniform in dB, so 200->1000 must cover 14/60 of the track.
        span = gainmath.percent_to_position(1000, 1000) - gainmath.percent_to_position(200, 1000)
        self.assertAlmostEqual(span, 14 / 60, places=2)

    def test_round_trip(self):
        for maximum in (100, 500, 1000):
            for percent in (0, 1, 10, 32, 100, 200, 500, maximum):
                if percent > maximum:
                    continue
                position = gainmath.percent_to_position(percent, maximum)
                recovered = gainmath.position_to_percent(position, maximum)
                self.assertLessEqual(abs(recovered - percent), 1, (maximum, percent, recovered))

    def test_ceiling_changes_the_scale(self):
        self.assertAlmostEqual(gainmath.percent_to_position(100, 500), 40 / 53.98, places=3)
        self.assertAlmostEqual(gainmath.percent_to_position(100, 1000), 2 / 3, places=3)

    def test_clamps(self):
        self.assertEqual(gainmath.position_to_percent(-1, 1000), 0)
        self.assertEqual(gainmath.position_to_percent(2, 1000), 1000)
        self.assertEqual(gainmath.percent_to_position(-5, 1000), 0.0)
        self.assertLessEqual(gainmath.percent_to_position(9999, 1000), 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
