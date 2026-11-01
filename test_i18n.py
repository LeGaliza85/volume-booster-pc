"""Tests for the translation tables."""

from __future__ import annotations

import re
import unittest

import i18n

_PLACEHOLDER = re.compile(r"\{(\w+)\}")


class TranslationTests(unittest.TestCase):
    def test_every_language_has_a_name(self):
        self.assertEqual(set(i18n.LANGUAGES), set(i18n.TRANSLATIONS))

    def test_every_language_has_the_same_keys(self):
        reference = set(i18n.TRANSLATIONS[i18n.FALLBACK])
        for code, table in i18n.TRANSLATIONS.items():
            self.assertEqual(set(table), reference, f"{code} key mismatch")

    def test_no_empty_translation(self):
        for code, table in i18n.TRANSLATIONS.items():
            for key, text in table.items():
                self.assertTrue(text.strip(), f"{code}:{key} is empty")

    def test_placeholders_match_english(self):
        reference = i18n.TRANSLATIONS[i18n.FALLBACK]
        for code, table in i18n.TRANSLATIONS.items():
            for key, text in table.items():
                self.assertEqual(
                    set(_PLACEHOLDER.findall(text)),
                    set(_PLACEHOLDER.findall(reference[key])),
                    f"{code}:{key} placeholder mismatch",
                )

    def test_required_keys_exist(self):
        for key in (
            "subtitle",
            "exact",
            "apply",
            "setup",
            "muted",
            "applied",
            "not_available",
            "bad_number",
            "write_failed",
            "warning",
            "autostart",
            "autostart_question",
            "autostart_failed",
            "help_windows",
            "help_linux",
            "help_macos",
        ):
            self.assertIn(key, i18n.TRANSLATIONS[i18n.FALLBACK])


class TranslateTests(unittest.TestCase):
    def test_formats_placeholders(self):
        for code in i18n.LANGUAGES:
            text = i18n.translate(code, "applied", gain="+13.98 dB", engine="Equalizer APO")
            self.assertIn("+13.98 dB", text, code)
            self.assertIn("Equalizer APO", text, code)

    def test_unknown_language_falls_back_to_english(self):
        self.assertEqual(i18n.translate("xx", "apply"), "Apply")

    def test_unknown_key_returns_the_key(self):
        self.assertEqual(i18n.translate("en", "missing.key"), "missing.key")

    def test_missing_placeholder_does_not_raise(self):
        self.assertIn("{gain}", i18n.translate("en", "applied"))


class LanguageIdTests(unittest.TestCase):
    def test_primary_language_ids(self):
        self.assertEqual(i18n.language_from_langid(0x0409), "en")
        self.assertEqual(i18n.language_from_langid(0x0C0A), "es")
        self.assertEqual(i18n.language_from_langid(0x040C), "fr")
        self.assertEqual(i18n.language_from_langid(0x0407), "de")
        self.assertEqual(i18n.language_from_langid(0x0410), "it")
        self.assertEqual(i18n.language_from_langid(0x0416), "pt")
        self.assertEqual(i18n.language_from_langid(0x0419), "ru")
        self.assertEqual(i18n.language_from_langid(0x0804), "zh")
        self.assertEqual(i18n.language_from_langid(0x0411), "ja")

    def test_unknown_language_id_is_english(self):
        self.assertEqual(i18n.language_from_langid(0x7FFF), "en")

    def test_system_language_is_supported(self):
        self.assertIn(i18n.system_language(), i18n.LANGUAGES)


if __name__ == "__main__":
    unittest.main(verbosity=2)
