"""Tests for the installer download: the hash check is the safety rail."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import update

PAYLOAD = b"pretend this is an installer"
PAYLOAD_HASH = hashlib.sha256(PAYLOAD).hexdigest().upper()
RELEASE = {
    "tag": "v9.9.9",
    "version": "9.9.9",
    "setup": "https://example.invalid/VolumeBoosterSetup.exe",
    "sums": "https://example.invalid/SHA256SUMS-windows.txt",
}


class HashParsingTests(unittest.TestCase):
    def test_plain_line(self):
        text = f"{PAYLOAD_HASH}  VolumeBoosterSetup.exe\n"
        self.assertEqual(update.expected_hash(text, "VolumeBoosterSetup.exe"), PAYLOAD_HASH)

    def test_binary_marker(self):
        text = f"{PAYLOAD_HASH} *VolumeBoosterSetup.exe\n"
        self.assertEqual(update.expected_hash(text, "VolumeBoosterSetup.exe"), PAYLOAD_HASH)

    def test_lowercase_is_accepted(self):
        text = f"{PAYLOAD_HASH.lower()}  VolumeBoosterSetup.exe\n"
        self.assertEqual(update.expected_hash(text, "VolumeBoosterSetup.exe"), PAYLOAD_HASH)

    def test_other_files_are_ignored(self):
        text = f"{'0' * 64}  other.exe\n{PAYLOAD_HASH}  VolumeBoosterSetup.exe\n"
        self.assertEqual(update.expected_hash(text, "VolumeBoosterSetup.exe"), PAYLOAD_HASH)

    def test_missing_or_broken_is_empty(self):
        for text in ("", "garbage", f"{'0' * 64}  nothing.exe", "abc  VolumeBoosterSetup.exe"):
            self.assertEqual(update.expected_hash(text, "VolumeBoosterSetup.exe"), "")


class DownloadTests(unittest.TestCase):
    def _run(self, payload: bytes, sums: bytes):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "setup.exe"
            with mock.patch.object(update, "latest_release", return_value=RELEASE), mock.patch.object(
                update, "_get", side_effect=[payload, sums]
            ):
                result = update.download_installer(target)
            return result, target.exists()

    def test_a_matching_hash_saves_the_file(self):
        result, exists = self._run(PAYLOAD, f"{PAYLOAD_HASH}  VolumeBoosterSetup.exe\n".encode())
        self.assertIsNotNone(result)
        self.assertTrue(exists)

    def test_a_wrong_hash_deletes_the_file(self):
        result, exists = self._run(PAYLOAD, f"{'0' * 64}  VolumeBoosterSetup.exe\n".encode())
        self.assertIsNone(result)
        self.assertFalse(exists)

    def test_a_missing_checksum_is_refused(self):
        result, exists = self._run(PAYLOAD, b"nothing useful here\n")
        self.assertIsNone(result)
        self.assertFalse(exists)

    def test_no_urls_means_no_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(
                update, "latest_release", return_value={"tag": "v9", "version": "9", "setup": "", "sums": ""}
            ):
                self.assertIsNone(update.download_installer(Path(tmp) / "setup.exe"))

    def test_a_network_error_is_none(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            update, "latest_release", return_value=RELEASE
        ), mock.patch.object(update, "_get", side_effect=OSError("offline")):
            self.assertIsNone(update.download_installer(Path(tmp) / "setup.exe"))

    def test_sha256_matches_hashlib(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.bin"
            path.write_bytes(PAYLOAD)
            self.assertEqual(update.sha256_of(path), PAYLOAD_HASH)


if __name__ == "__main__":
    unittest.main(verbosity=2)
