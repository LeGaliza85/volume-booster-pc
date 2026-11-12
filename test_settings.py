"""Tests for the user settings: defaults, sanitising, confirmation, round trip."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import settings


class SanitizeTests(unittest.TestCase):
    def test_defaults_for_broken_input(self):
        for broken in (None, [], "text", 42):
            self.assertEqual(settings.sanitize(broken), settings.DEFAULTS)

    def test_clamps_max_percent(self):
        self.assertEqual(settings.sanitize({"max_percent": 50})["max_percent"], 100)
        self.assertEqual(settings.sanitize({"max_percent": 5000})["max_percent"], 1000)
        self.assertEqual(settings.sanitize({"max_percent": "600"})["max_percent"], 600)

    def test_clamps_confirm_above(self):
        self.assertEqual(settings.sanitize({"confirm_above": -10})["confirm_above"], 0)
        data = settings.sanitize({"max_percent": 800, "confirm_above": 9999})
        self.assertEqual(data["confirm_above"], 800)

    def test_confirm_above_never_exceeds_max(self):
        data = settings.sanitize({"max_percent": 200, "confirm_above": 800})
        self.assertEqual(data["confirm_above"], 200)

    def test_restore_on_exit_only_accepts_bools(self):
        self.assertTrue(settings.sanitize({"restore_on_exit": "yes"})["restore_on_exit"])
        self.assertTrue(settings.sanitize({"restore_on_exit": True})["restore_on_exit"])
        self.assertFalse(settings.sanitize({"restore_on_exit": False})["restore_on_exit"])

    def test_unknown_keys_are_dropped(self):
        data = settings.sanitize({"dangerous": 1})
        self.assertNotIn("dangerous", data)


class ConfirmTests(unittest.TestCase):
    def test_confirms_above_the_threshold(self):
        data = {"confirm_above": 300}
        self.assertTrue(settings.should_confirm(301, data))
        self.assertFalse(settings.should_confirm(300, data))
        self.assertFalse(settings.should_confirm(100, data))

    def test_zero_disables_confirmation(self):
        self.assertFalse(settings.should_confirm(1000, {"confirm_above": 0}))


class FileTests(unittest.TestCase):
    def test_missing_file_uses_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(settings.load(Path(tmp) / "settings.json"), settings.DEFAULTS)

    def test_corrupt_json_uses_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            path.write_text("{not json", encoding="utf-8")
            self.assertEqual(settings.load(path), settings.DEFAULTS)

    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            stored = {"max_percent": 800, "confirm_above": 400, "restore_on_exit": True}
            settings.save(path, stored)
            loaded = settings.load(path)
            self.assertEqual(loaded["max_percent"], 800)
            self.assertEqual(loaded["confirm_above"], 400)
            self.assertTrue(loaded["restore_on_exit"])
            self.assertEqual(set(loaded), set(settings.DEFAULTS))
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["max_percent"], 800)

    def test_hotkeys_are_normalised(self):
        data = settings.sanitize({"hotkey_up": "alt+ctrl+up", "hotkey_down": "Shift+F5"})
        self.assertEqual(data["hotkey_up"], "Ctrl+Alt+Up")
        self.assertEqual(data["hotkey_down"], "Shift+F5")

    def test_invalid_hotkey_falls_back_to_the_default(self):
        data = settings.sanitize({"hotkey_up": "nonsense"})
        self.assertEqual(data["hotkey_up"], settings.DEFAULTS["hotkey_up"])

    def test_empty_hotkey_is_a_deliberate_no_hotkey(self):
        data = settings.sanitize({"hotkey_down": ""})
        self.assertEqual(data["hotkey_down"], "")

    def test_hotkey_that_is_not_a_string_is_ignored(self):
        data = settings.sanitize({"hotkey_up": 42})
        self.assertEqual(data["hotkey_up"], settings.DEFAULTS["hotkey_up"])

    def test_bom_is_tolerated(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            path.write_bytes(b"\xef\xbb\xbf" + b'{"max_percent": 700}')
            self.assertEqual(settings.load(path)["max_percent"], 700)


if __name__ == "__main__":
    unittest.main(verbosity=2)
