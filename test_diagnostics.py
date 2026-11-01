"""Tests for the support bundle: scrubbing, report contents and the zip."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import diagnostics
import version


class ScrubTests(unittest.TestCase):
    def test_home_is_replaced(self):
        home = str(Path.home())
        self.assertNotIn(home, diagnostics.scrub(home + r"\AppData"))
        self.assertIn("<home>", diagnostics.scrub(home + r"\AppData"))

    def test_username_is_replaced(self):
        user = os.environ.get("USERNAME") or os.environ.get("USER")
        if not user or len(user) <= 2:
            self.skipTest("no user name in this environment")
        self.assertNotIn(user, diagnostics.scrub(f"C:/stuff/{user}/x"))

    def test_windows_profile_path_is_generic(self):
        cleaned = diagnostics.scrub(r"C:\Users\someone\AppData\Roaming")
        self.assertIn("<user>", cleaned)

    def test_plain_text_survives(self):
        self.assertEqual(diagnostics.scrub("no paths here"), "no paths here")


class BlockTests(unittest.TestCase):
    def test_reads_the_preamp(self):
        text = "# >>> Amplificador Voz >>>\nPreamp: 13.98 dB\n# <<< Amplificador Voz <<<\n"
        self.assertEqual(diagnostics.text_block(text), "13.98 dB")

    def test_negative_preamp(self):
        self.assertEqual(diagnostics.text_block("Preamp: -6.02 dB"), "-6.02 dB")

    def test_missing_block(self):
        self.assertEqual(diagnostics.text_block("Filter: ON PK Fc 80 Hz"), "")


class CrashLogTests(unittest.TestCase):
    def test_crash_log_sits_next_to_the_app_log(self):
        self.assertEqual(diagnostics.crash_log_path().name, "crash.log")
        self.assertEqual(diagnostics.crash_log_path().parent, diagnostics.log_path().parent)


class ReportTests(unittest.TestCase):
    def test_report_identity_and_scrubbing(self):
        report = diagnostics.build_report({"state": {"percent": 320, "language": "es"}})
        self.assertEqual(report["app"], version.APP_NAME)
        self.assertEqual(report["version"], version.VERSION)
        self.assertEqual(report["state"]["percent"], 320)
        self.assertNotIn(str(Path.home()), json.dumps(report))

    def test_export_writes_a_valid_bundle(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            diagnostics, "app_data_dir", return_value=Path(tmp)
        ), mock.patch.object(diagnostics, "log_path", return_value=Path(tmp) / "app.log"):
            target = diagnostics.export({"state": {"percent": 100}})
            self.assertTrue(target.exists())
            with zipfile.ZipFile(target) as bundle:
                self.assertIn("report.json", bundle.namelist())
                report = json.loads(bundle.read("report.json"))
        self.assertEqual(report["state"]["percent"], 100)
        self.assertIn("generated", report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
