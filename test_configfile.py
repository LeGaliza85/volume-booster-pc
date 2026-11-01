"""Tests for the isolated gain file: block stripping, include handling, rendering."""

from __future__ import annotations

import unittest

import configfile

LEGACY = (
    "# >>> Amplificador Voz >>>\r\n"
    "Preamp: 13.98 dB\r\n"
    "# <<< Amplificador Voz <<<\r\n"
)
PRO = (
    "# >>> Volume Booster >>>\r\n"
    "Preamp: 3.52 dB\r\n"
    "# <<< Volume Booster <<<\r\n"
)
USER = "Device: Headphones\r\nFilter: ON PK Fc 80 Hz Gain 3 dB Q 1.0\r\n"


class StripTests(unittest.TestCase):
    def test_removes_the_legacy_block(self):
        cleaned = configfile.strip_blocks(LEGACY + USER)
        self.assertNotIn(configfile.LEGACY_BEGIN, cleaned)
        self.assertNotIn("Preamp:", cleaned)
        self.assertIn("Device: Headphones", cleaned)

    def test_removes_the_pro_block(self):
        cleaned = configfile.strip_blocks(PRO + USER)
        self.assertNotIn(configfile.PRO_BEGIN, cleaned)
        self.assertNotIn("3.52 dB", cleaned)

    def test_removes_several_blocks(self):
        cleaned = configfile.strip_blocks(PRO + LEGACY + PRO + USER)
        self.assertNotIn("Preamp:", cleaned)
        self.assertIn("Device: Headphones", cleaned)

    def test_user_content_is_untouched(self):
        self.assertEqual(configfile.strip_blocks(USER), USER)

    def test_unbalanced_markers_are_refused(self):
        with self.assertRaises(configfile.ConfigError):
            configfile.strip_blocks(configfile.LEGACY_BEGIN + "\n" + USER)


class IncludeTests(unittest.TestCase):
    def test_adds_the_line_once(self):
        text = configfile.ensure_include(USER)
        self.assertTrue(text.startswith(configfile.INCLUDE_LINE))
        self.assertEqual(text.count(configfile.INCLUDE_LINE), 1)

    def test_is_idempotent(self):
        once = configfile.ensure_include(USER)
        self.assertEqual(configfile.ensure_include(once), once)

    def test_collapses_duplicates(self):
        doubled = configfile.INCLUDE_LINE + "\n" + configfile.INCLUDE_LINE + "\n" + USER
        self.assertEqual(configfile.ensure_include(doubled).count(configfile.INCLUDE_LINE), 1)

    def test_detection_is_case_insensitive(self):
        self.assertTrue(
            configfile.include_present(f"include: {configfile.INCLUDE_NAME.upper()}\n")
        )

    def test_missing_line(self):
        self.assertFalse(configfile.include_present(USER))


class PrepareTests(unittest.TestCase):
    def test_full_prepare(self):
        prepared = configfile.prepare_config(PRO + LEGACY + USER)
        self.assertTrue(prepared.startswith(configfile.INCLUDE_LINE))
        self.assertNotIn("Preamp:", prepared)
        self.assertIn("Device: Headphones", prepared)

    def test_render_gain(self):
        self.assertEqual(configfile.render_gain(13.98), "Preamp: 13.98 dB\n")
        self.assertIn("-6.02", configfile.render_gain(-6.02))

    def test_has_gain(self):
        self.assertTrue(configfile.has_gain("Preamp: 0.00 dB"))
        self.assertFalse(configfile.has_gain("Device: A"))

    def test_include_path_is_next_to_config(self):
        from pathlib import Path

        self.assertEqual(
            configfile.include_path(Path("C:/ap/config.txt")).name, configfile.INCLUDE_NAME
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
