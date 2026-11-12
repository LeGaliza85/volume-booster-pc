"""Tests for the percentage/dB maths."""

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
