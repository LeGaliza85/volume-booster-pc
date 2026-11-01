"""Tests for the hotkey model: parsing, normalising, formatting and capture."""

from __future__ import annotations

import unittest

import hotkey


class ParseTests(unittest.TestCase):
    def test_control_alt_up(self):
        self.assertEqual(hotkey.parse("Ctrl+Alt+Up"), (hotkey.MOD_CONTROL | hotkey.MOD_ALT, 0x26))

    def test_case_and_spacing_do_not_matter(self):
        self.assertEqual(hotkey.parse("ctrl + alt + up"), hotkey.parse("CTRL+ALT+UP"))

    def test_letters_digits_and_function_keys(self):
        self.assertEqual(hotkey.parse("Ctrl+k"), (hotkey.MOD_CONTROL, ord("K")))
        self.assertEqual(hotkey.parse("Alt+5"), (hotkey.MOD_ALT, ord("5")))
        self.assertEqual(hotkey.parse("Shift+F5"), (hotkey.MOD_SHIFT, 0x6F + 5))

    def test_rejects_a_hotkey_without_modifier(self):
        self.assertIsNone(hotkey.parse("Up"))
        self.assertIsNone(hotkey.parse("F5"))

    def test_rejects_nonsense(self):
        for text in ("", None, "Ctrl+", "+Up", "Ctrl+Alt", "Ctrl+Alt+Nope", "Ctrl+Up+Down"):
            self.assertIsNone(hotkey.parse(text), text)

    def test_rejects_two_keys(self):
        self.assertIsNone(hotkey.parse("Ctrl+A+B"))


class FormatTests(unittest.TestCase):
    def test_canonical_order(self):
        modifiers = hotkey.MOD_WIN | hotkey.MOD_ALT | hotkey.MOD_CONTROL
        self.assertEqual(hotkey.format_hotkey(modifiers, 0x26), "Ctrl+Alt+Win+Up")

    def test_round_trip(self):
        for text in ("Ctrl+Alt+Up", "Shift+F5", "Ctrl+Alt+Shift+K", "Alt+Space"):
            self.assertEqual(hotkey.normalise(text), text)

    def test_normalise_lowercase(self):
        self.assertEqual(hotkey.normalise("alt+ctrl+down"), "Ctrl+Alt+Down")

    def test_invalid_normalises_to_empty(self):
        self.assertEqual(hotkey.normalise("nonsense"), "")


class CaptureTests(unittest.TestCase):
    def test_keysym_mapping(self):
        self.assertEqual(hotkey.from_event("Up", hotkey.MOD_CONTROL), "Ctrl+Up")
        self.assertEqual(hotkey.from_event("Prior", hotkey.MOD_ALT), "Alt+PageUp")
        self.assertEqual(hotkey.from_event("Next", hotkey.MOD_ALT), "Alt+PageDown")
        self.assertEqual(hotkey.from_event("Return", hotkey.MOD_CONTROL), "Ctrl+Enter")
        self.assertEqual(hotkey.from_event("space", hotkey.MOD_SHIFT), "Shift+Space")

    def test_letters_and_function_keys(self):
        self.assertEqual(hotkey.from_event("f5", hotkey.MOD_SHIFT), "Shift+F5")
        self.assertEqual(hotkey.from_event("k", hotkey.MOD_CONTROL), "Ctrl+K")

    def test_without_modifier_there_is_no_hotkey(self):
        self.assertEqual(hotkey.from_event("Up", 0), "")

    def test_modifier_keysyms_are_recognised(self):
        self.assertTrue(hotkey.is_modifier_keysym("Control_L"))
        self.assertTrue(hotkey.is_modifier_keysym("Alt_R"))
        self.assertFalse(hotkey.is_modifier_keysym("Up"))

    def test_unknown_keysym_is_ignored(self):
        self.assertEqual(hotkey.from_event("XF86AudioMute", hotkey.MOD_CONTROL), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
