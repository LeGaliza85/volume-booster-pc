"""Tests for handing the installer over.

The installer is a Windows thing, and so is the updater: on other platforms
``launch`` declines before it ever starts a process, which is the behaviour these
tests are not about.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

import updater

WINDOWS = sys.platform.startswith("win")


@unittest.skipUnless(WINDOWS, "the installer only exists on Windows")
class LaunchTests(unittest.TestCase):
    def test_it_runs_the_installer_silently_and_detached(self):
        setup = Path(r"C:\Temp\VolumeBoosterSetup.exe")
        with mock.patch.object(updater.subprocess, "Popen") as popen:
            self.assertTrue(updater.launch(setup))
        popen.assert_called_once()
        args, kwargs = popen.call_args
        self.assertEqual(args[0][0], str(setup))
        for flag in ("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"):
            self.assertIn(flag, args[0])
        self.assertIn("creationflags", kwargs)

    def test_a_failure_to_start_is_reported(self):
        with mock.patch.object(updater.subprocess, "Popen", side_effect=OSError("nope")):
            self.assertFalse(updater.launch(Path(r"C:\Temp\a.exe")))


class PlatformTests(unittest.TestCase):
    def test_other_platforms_decline(self):
        if WINDOWS:
            self.skipTest("this asserts the non-Windows branch")
        self.assertFalse(updater.launch(Path("/tmp/setup.exe")))


class BuildTests(unittest.TestCase):
    def test_running_from_source_is_not_an_installed_build(self):
        # The portable/source build must never replace itself with an install.
        self.assertFalse(updater.installed_build())


if __name__ == "__main__":
    unittest.main(verbosity=2)
