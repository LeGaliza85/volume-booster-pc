"""Tests for the update check: version maths and the network edge cases."""

from __future__ import annotations

import unittest
from unittest import mock

import update
import version


class FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


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


class LatestTagTests(unittest.TestCase):
    def test_reads_the_tag(self):
        response = FakeResponse(b'{"tag_name": "v9.9.9"}')
        with mock.patch("update.urllib.request.urlopen", return_value=response):
            self.assertEqual(update.latest_tag(), "v9.9.9")

    def test_network_error_is_none(self):
        with mock.patch("update.urllib.request.urlopen", side_effect=OSError("offline")):
            self.assertIsNone(update.latest_tag())

    def test_broken_json_is_none(self):
        response = FakeResponse(b"not json")
        with mock.patch("update.urllib.request.urlopen", return_value=response):
            self.assertIsNone(update.latest_tag())

    def test_missing_tag_is_none(self):
        response = FakeResponse(b'{"name": "no tag"}')
        with mock.patch("update.urllib.request.urlopen", return_value=response):
            self.assertIsNone(update.latest_tag())


class CheckTests(unittest.TestCase):
    def test_reports_a_newer_release(self):
        response = FakeResponse(b'{"tag_name": "v99.0.0"}')
        with mock.patch("update.urllib.request.urlopen", return_value=response):
            result = update.check()
        self.assertEqual(result["status"], update.STATUS_NEWER)
        self.assertEqual(result["latest"], "99.0.0")
        self.assertTrue(result["url"].endswith("/releases/latest"))

    def test_reports_the_current_version(self):
        response = FakeResponse(f'{{"tag_name": "v{version.VERSION}"}}'.encode())
        with mock.patch("update.urllib.request.urlopen", return_value=response):
            result = update.check()
        self.assertEqual(result["status"], update.STATUS_CURRENT)

    def test_offline_is_unknown_not_a_crash(self):
        with mock.patch("update.urllib.request.urlopen", side_effect=OSError("offline")):
            result = update.check()
        self.assertEqual(result["status"], update.STATUS_UNKNOWN)
        self.assertEqual(result["latest"], "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
