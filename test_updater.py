"""Tests for the detached installer hand-over."""

from __future__ import annotations

import unittest
from pathlib import Path

import updater


class ScriptTests(unittest.TestCase):
    def test_it_waits_installs_silently_and_relaunches(self):
        text = updater.script(
            Path(r"C:\Temp\VolumeBoosterSetup.exe"),
            Path(r"C:\Apps\Volume Booster\VolumeBooster.exe"),
        )
        self.assertIn('start "" /wait "C:\\Temp\\VolumeBoosterSetup.exe"', text)
        self.assertIn("/VERYSILENT", text)
        self.assertIn("/SUPPRESSMSGBOXES", text)
        self.assertIn("/NORESTART", text)
        self.assertIn('start "" "C:\\Apps\\Volume Booster\\VolumeBooster.exe"', text)
        self.assertIn('del /q "%~f0"', text)
        self.assertIn(':waitforinstaller', text)
        self.assertIn('goto waitforinstaller', text)
        self.assertIn('del /q "C:\\Temp\\VolumeBoosterSetup.exe"', text)

    def test_it_waits_before_installing(self):
        self.assertIn("ping -n 4", updater.script(Path("a"), Path("b"), wait=3))

    def test_it_is_plain_ascii(self):
        text = updater.script(Path(r"C:\Temp\a.exe"), Path(r"C:\b.exe"))
        text.encode("ascii")


class BuildTests(unittest.TestCase):
    def test_running_from_source_is_not_an_installed_build(self):
        # The portable/source build must never replace itself with an install.
        self.assertFalse(updater.installed_build())


if __name__ == "__main__":
    unittest.main(verbosity=2)
