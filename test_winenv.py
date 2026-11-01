"""Tests for the Windows requirement rows (no Windows calls involved).

The contract is "only what needs attention": a missing APO hides everything else,
and the reboot advice only appears while the APO is not attached yet.
"""

from __future__ import annotations

import unittest

import winenv


def by_key(rows: list[dict]) -> dict[str, dict]:
    return {row["key"]: row for row in rows}


class MissingApoTests(unittest.TestCase):
    def test_only_the_download_row_is_returned(self):
        rows = winenv.inspect(installed=False, level="missing")
        self.assertEqual([row["key"] for row in rows], ["req_engine"])
        self.assertEqual(rows[0]["state"], winenv.FAIL)
        self.assertEqual(rows[0]["action"], winenv.OPEN_DOWNLOAD)
        self.assertEqual(rows[0]["label"], "download")


class AttachedTests(unittest.TestCase):
    def test_nothing_red_and_no_reboot_advice(self):
        rows = by_key(winenv.inspect(installed=True, level="ok"))
        self.assertEqual(rows["req_attached"]["state"], winenv.OK)
        self.assertEqual(rows["req_attached"]["action"], winenv.OPEN_CONFIGURATOR)
        self.assertEqual(rows["req_attached"]["label"], "change")
        self.assertNotIn("req_reboot", rows)
        self.assertNotIn("req_engine", rows)

    def test_drift_still_counts_as_attached(self):
        rows = by_key(winenv.inspect(installed=True, level="drift"))
        self.assertEqual(rows["req_attached"]["state"], winenv.OK)
        self.assertNotIn("req_reboot", rows)

    def test_enhancements_hidden_when_the_apo_is_working(self):
        rows = by_key(winenv.inspect(installed=True, level="ok"))
        self.assertNotIn("req_enhancements", rows)

    def test_enhancements_red_when_windows_blocks_the_device(self):
        rows = by_key(winenv.inspect(installed=True, level="ok", blocked=["Altavoces"]))
        self.assertEqual(rows["req_enhancements"]["state"], winenv.FAIL)
        self.assertEqual(rows["req_enhancements"]["action"], winenv.OPEN_SOUND)
        self.assertEqual(rows["req_enhancements"]["label"], "open_sound")
        self.assertEqual(rows["req_enhancements"]["device"], "Altavoces")


class DetachedTests(unittest.TestCase):
    def test_red_row_with_the_configurator_and_a_reboot_hint(self):
        rows = by_key(winenv.inspect(installed=True, level="detached"))
        self.assertEqual(rows["req_attached"]["state"], winenv.FAIL)
        self.assertEqual(rows["req_attached"]["action"], winenv.OPEN_CONFIGURATOR)
        self.assertEqual(rows["req_attached"]["label"], "open")
        self.assertEqual(rows["req_reboot"]["state"], winenv.INFO)
        self.assertEqual(rows["req_reboot"]["action"], winenv.NONE)


class ShapeTests(unittest.TestCase):
    def test_every_row_is_renderable(self):
        allowed = {winenv.NONE, winenv.OPEN_DOWNLOAD, winenv.OPEN_CONFIGURATOR, winenv.OPEN_SOUND}
        for installed, level in ((False, "missing"), (True, "ok"), (True, "detached")):
            for row in winenv.inspect(installed=installed, level=level):
                self.assertTrue(row["key"])
                self.assertIn(row["state"], {winenv.OK, winenv.FAIL, winenv.INFO})
                self.assertIn(row["action"], allowed)
                self.assertTrue(row["label"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
