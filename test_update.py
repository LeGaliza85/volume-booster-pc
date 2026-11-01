"""Tests for the update check: version maths and the network edge cases."""

from __future__ import annotations

import unittest
from unittest import mock

import update
import version

RELEASE_JSON = (
    b'{"tag_name": "v9.9.9", "assets": ['
    b'{"name": "VolumeBoosterSetup.exe", "browser_download_url": "https://x/setup"},'
    b'{"name": "SHA256SUMS-windows.txt", "browser_download_url": "https://x/sums"}]}'
)


class ParseTests(unittest.TestCase):
    def test_plain_and_prefixed(self):
        self.assertEqual(update.parse_version("1.3.1"), (1, 3, 1))
        self.assertEqual(update.parse_version("v1.4.0"), (1, 4, 0))
        self.assertEqual(update.parse_version("V2.0"), (2, 0))

    def test_trailing_noise_is_ignored(self):
        self.assertEqual(update.parse_version("1.3.1-beta"), (1, 3, 1))

    def test_unparsable_is_empty(self):
        for value in (None, "", "nonsense", "v."):
            self.assertEqual(update.parse_version(value), (), value)


class CompareTests(unittest.TestCase):
    def test_newer_and_older(self):
        self.assertTrue(update.is_newer("1.3.1", "1.4.0"))
        self.assertTrue(update.is_newer("1.3.1", "2.0"))
        self.assertFalse(update.is_newer("1.4.0", "1.3.9"))
        self.assertFalse(update.is_newer("1.3.1", "1.3.1"))

    def test_unknown_remote_is_never_newer(self):
        self.assertFalse(update.is_newer("1.3.1", None))
        self.assertFalse(update.is_newer("1.3.1", "garbage"))


class LatestReleaseTests(unittest.TestCase):
    def test_reads_the_tag_and_the_installer_urls(self):
        with mock.patch.object(update, "_get", return_value=RELEASE_JSON):
            release = update.latest_release()
        self.assertEqual(release["tag"], "v9.9.9")
        self.assertEqual(release["version"], "9.9.9")
        self.assertEqual(release["setup"], "https://x/setup")
        self.assertEqual(release["sums"], "https://x/sums")

    def test_network_error_is_none(self):
        with mock.patch.object(update, "_get", side_effect=OSError("offline")):
            self.assertIsNone(update.latest_release())

    def test_broken_json_is_none(self):
        with mock.patch.object(update, "_get", return_value=b"not json"):
            self.assertIsNone(update.latest_release())

    def test_missing_tag_is_none(self):
        with mock.patch.object(update, "_get", return_value=b'{"name": "no tag"}'):
            self.assertIsNone(update.latest_release())


class CheckTests(unittest.TestCase):
    def test_reports_a_newer_release(self):
        with mock.patch.object(update, "_get", return_value=RELEASE_JSON):
            result = update.check()
        self.assertEqual(result["status"], update.STATUS_NEWER)
        self.assertEqual(result["latest"], "9.9.9")
        self.assertTrue(result["url"].endswith("/releases/latest"))
        self.assertEqual(result["setup"], "https://x/setup")

    def test_reports_the_current_version(self):
        payload = f'{{"tag_name": "v{version.VERSION}"}}'.encode()
        with mock.patch.object(update, "_get", return_value=payload):
            result = update.check()
        self.assertEqual(result["status"], update.STATUS_CURRENT)

    def test_offline_is_unknown_not_a_crash(self):
        with mock.patch.object(update, "_get", side_effect=OSError("offline")):
            result = update.check()
        self.assertEqual(result["status"], update.STATUS_UNKNOWN)
        self.assertEqual(result["latest"], "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
