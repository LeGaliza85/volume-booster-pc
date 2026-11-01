"""Tests for the pre-filled bug-report URL."""

from __future__ import annotations

import unittest
from urllib.parse import parse_qs, urlsplit

import report
import version


class OsOptionTests(unittest.TestCase):
    def test_windows_11(self):
        self.assertEqual(report.os_option(platform="win32", build=22631), "Windows 11")

    def test_windows_10(self):
        self.assertEqual(report.os_option(platform="win32", build=19045), "Windows 10")

    def test_linux(self):
        self.assertEqual(report.os_option(platform="linux"), "Linux (PipeWire)")

    def test_unknown_platform_is_empty(self):
        self.assertEqual(report.os_option(platform="darwin"), "")

    def test_windows_without_a_build_number_is_not_guessed(self):
        self.assertEqual(report.os_option(platform="win32", build=-1), "Windows 10")


class IssueUrlTests(unittest.TestCase):
    def test_targets_the_bug_report_form(self):
        url = report.build_issue_url(app_version="1.0.1")
        parts = urlsplit(url)
        self.assertEqual(parts.path, "/LeGaliza85/volume-booster-pc/issues/new")
        self.assertEqual(parse_qs(parts.query)["template"], ["bug_report.yml"])

    def test_prefills_the_version(self):
        query = parse_qs(urlsplit(report.build_issue_url(app_version="1.0.1")).query)
        self.assertEqual(query["version"], [f"{version.APP_NAME} 1.0.1"])

    def test_prefills_the_title_with_the_version(self):
        query = parse_qs(urlsplit(report.build_issue_url(app_version="1.0.1")).query)
        self.assertIn("1.0.1", query["title"][0])
        self.assertTrue(query["title"][0].startswith("[bug] "))

    def test_prefills_the_os_only_when_known(self):
        with_os = parse_qs(
            urlsplit(report.build_issue_url(app_version="1.0.1", os_name="Windows 11")).query
        )
        self.assertEqual(with_os["os"], ["Windows 11"])
        without = parse_qs(urlsplit(report.build_issue_url(app_version="1.0.1")).query)
        self.assertNotIn("os", without)

    def test_never_contains_a_space(self):
        url = report.build_issue_url(app_version="1.0.1", os_name="Windows 11")
        self.assertNotIn(" ", url)


if __name__ == "__main__":
    unittest.main(verbosity=2)
