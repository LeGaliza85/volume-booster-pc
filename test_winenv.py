"""Tests for the Windows requirement rows (no Windows calls involved)."""

from __future__ import annotations

import unittest

import winenv


def states(rows: list[dict]) -> dict[str, str]:
    return {row["key"]: row["state"] for row in rows}


def actions(rows: list[dict]) -> dict[str, str]:
    return {row["key"]: row["action"] for row in rows}


class InspectTests(unittest.TestCase):
    def test_everything_fine(self):
        rows = winenv.inspect(installed=True, level="ok")
        self.assertEqual(states(rows)["req_engine"], winenv.OK)
        self.assertEqual(states(rows)["req_attached"], winenv.OK)
        self.assertEqual(actions(rows)["req_engine"], winenv.NONE)
        self.assertEqual(actions(rows)["req_attached"], winenv.NONE)

    def test_missing_engine_offers_the_download(self):
        rows = winenv.inspect(installed=False, level="missing")
        self.assertEqual(states(rows)["req_engine"], winenv.FAIL)
        self.assertEqual(actions(rows)["req_engine"], winenv.OPEN_DOWNLOAD)

    def test_detached_offers_the_configurator(self):
        rows = winenv.inspect(installed=True, level="detached")
        self.assertEqual(states(rows)["req_engine"], winenv.OK)
        self.assertEqual(states(rows)["req_attached"], winenv.FAIL)
        self.assertEqual(actions(rows)["req_attached"], winenv.OPEN_CONFIGURATOR)

    def test_drift_still_counts_as_attached(self):
        rows = winenv.inspect(installed=True, level="drift")
        self.assertEqual(states(rows)["req_attached"], winenv.OK)

    def test_advice_rows_are_informational(self):
        rows = winenv.inspect(installed=True, level="ok")
        self.assertEqual(states(rows)["req_enhancements"], winenv.INFO)
        self.assertEqual(states(rows)["req_reboot"], winenv.INFO)
        self.assertEqual(actions(rows)["req_enhancements"], winenv.OPEN_SOUND)
        self.assertEqual(actions(rows)["req_reboot"], winenv.NONE)

    def test_every_row_has_a_key_and_an_action(self):
        for row in winenv.inspect(installed=False, level="missing"):
            self.assertTrue(row["key"])
            allowed = {winenv.NONE, winenv.OPEN_DOWNLOAD, winenv.OPEN_CONFIGURATOR, winenv.OPEN_SOUND}
            self.assertIn(row["action"], allowed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
