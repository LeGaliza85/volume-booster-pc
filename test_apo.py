"""Tests for the Equalizer APO integration: include file, legacy cleanup, IO safety."""

from __future__ import annotations

import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

import configfile
import gainmath

WINDOWS = sys.platform.startswith("win")

if WINDOWS:
    import apo

USER_BLOCK = (
    "Device: Headphones\r\n"
    "Filter: ON PK Fc 80 Hz Gain 3 dB Q 1.0\r\n"
    "Filter: ON HPQ Fc 25 Hz Q 0.707\r\n"
)
LEGACY = (
    "# >>> Amplificador Voz >>>\r\n"
    "Preamp: 13.98 dB\r\n"
    "# <<< Amplificador Voz <<<\r\n"
)


class PercentMathTests(unittest.TestCase):
    def test_reference_points(self):
        self.assertEqual(gainmath.percent_to_db(100), 0.0)
        self.assertEqual(gainmath.percent_to_db(500), 13.98)
        self.assertEqual(gainmath.percent_to_db(250), 7.96)
        self.assertEqual(gainmath.percent_to_db(200), 6.02)
        self.assertEqual(gainmath.percent_to_db(50), -6.02)

    def test_zero_is_silence_not_negative_infinity(self):
        self.assertEqual(gainmath.percent_to_db(0), gainmath.SILENT_DB)

    def test_clamp(self):
        self.assertEqual(gainmath.clamp_percent(-20), 0)
        self.assertEqual(gainmath.clamp_percent(900), 500)
        self.assertEqual(gainmath.clamp_percent("250"), 250)
        self.assertEqual(gainmath.clamp_percent("nonsense"), gainmath.DEFAULT_PERCENT)


@unittest.skipUnless(WINDOWS, "Equalizer APO engine is Windows-only")
class IncludeFileTests(unittest.TestCase):
    def test_apply_adds_one_include_and_writes_the_gain(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.txt"
            path.write_bytes(b"\xef\xbb\xbf" + USER_BLOCK.encode("utf-8"))

            apo.apply_percent(path, 500)

            text, encoding, has_bom = apo.read_config(path)
            self.assertTrue(has_bom)
            self.assertEqual(encoding, "utf-8")
            self.assertTrue(configfile.include_present(text))
            self.assertEqual(text.count(configfile.INCLUDE_LINE), 1)
            self.assertTrue(text.endswith(USER_BLOCK))
            self.assertNotIn("Preamp:", text)

            gain = apo.gain_text(path)
            self.assertIn("Preamp: 13.98 dB", gain)
            self.assertTrue(apo.include_path(path).exists())

    def test_legacy_block_is_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.txt"
            path.write_text(LEGACY + USER_BLOCK, encoding="utf-8", newline="")

            apo.apply_percent(path, 250)

            text, _encoding, _bom = apo.read_config(path)
            self.assertNotIn(configfile.LEGACY_BEGIN, text)
            self.assertNotIn("Preamp: 13.98 dB", text)
            self.assertIn("Filter: ON PK Fc 80 Hz Gain 3 dB Q 1.0", text)
            self.assertIn("Preamp: 7.96 dB", apo.gain_text(path))

    def test_reapply_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.txt"
            path.write_text(USER_BLOCK, encoding="utf-8", newline="")
            apo.apply_percent(path, 300)
            first = path.read_bytes()
            apo.apply_percent(path, 300)
            self.assertEqual(first, path.read_bytes())
            self.assertEqual(path.read_bytes().count(configfile.INCLUDE_LINE.encode()), 1)

    def test_backup_is_the_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.txt"
            path.write_text(USER_BLOCK, encoding="utf-8", newline="")
            apo.apply_percent(path, 200)
            backup = path.with_name(path.name + apo._BACKUP_SUFFIX)
            self.assertTrue(backup.exists())
            self.assertEqual(backup.read_bytes(), USER_BLOCK.encode("utf-8"))

    def test_missing_file_raises_instead_of_creating_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(apo.ConfigNotFoundError):
                apo.apply_percent(Path(tmp) / "config.txt", 200)
            self.assertFalse((Path(tmp) / "config.txt").exists())

    def test_failed_write_keeps_file_and_leaves_no_temp(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.txt"
            path.write_bytes(b"Device: A\r\n")
            os.chmod(path, stat.S_IREAD)
            try:
                with self.assertRaises(apo.ConfigError):
                    apo.apply_percent(path, 200)
                self.assertEqual(path.read_bytes(), b"Device: A\r\n")
                self.assertEqual(list(Path(tmp).glob(".amplificador-voz-*")), [])
            finally:
                os.chmod(path, stat.S_IWRITE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
