"""Tests for the Linux sink-volume backend and the login registration helpers."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

import autostart
from backend import BackendError
from backend_linux import LinuxBackend, parse_volume

SHIM = '''\
import pathlib, sys
here = pathlib.Path(__file__).resolve().parent
with open(here / "calls.txt", "a", encoding="utf-8") as log:
    log.write(" ".join(sys.argv[1:]) + "\\n")
args = sys.argv[1:]
if args[:1] == ["get-sink-volume"]:
    print("Volume: front-left: 163840 /  250% / 7.96 dB,   "
          "front-right: 163840 /  250% / 7.96 dB")
elif args[:1] in (["set-sink-volume"], ["set-sink-mute"]):
    if "fail-me" in args:
        print("Connection failure", file=sys.stderr)
        sys.exit(1)
else:
    sys.exit(1)
'''


def _fake_pactl(directory: Path) -> str:
    """Create an executable pactl shim that logs its arguments."""
    (directory / "shim.py").write_text(SHIM, encoding="utf-8")
    if os.name == "nt":
        script = directory / "pactl.cmd"
        script.write_text(
            f'@echo off\r\n"{sys.executable}" "{directory / "shim.py"}" %*\r\n',
            encoding="utf-8",
        )
    else:
        script = directory / "pactl"
        script.write_text(
            f'#!/bin/sh\nexec "{sys.executable}" "{directory / "shim.py"}" "$@"\n',
            encoding="utf-8",
        )
        script.chmod(0o755)
    return str(script)


class LinuxBackendCommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.backend = LinuxBackend()
        self.backend.pactl = _fake_pactl(self.directory)

    def calls(self) -> list[str]:
        return (self.directory / "calls.txt").read_text(encoding="utf-8").splitlines()

    def test_unmutes_then_sets_the_percentage(self):
        self.backend.apply(250)
        self.assertEqual(
            self.calls(),
            ["set-sink-mute @DEFAULT_SINK@ 0", "set-sink-volume @DEFAULT_SINK@ 250%"],
        )

    def test_zero_mutes_and_zeroes_the_sink(self):
        self.backend.apply(0)
        self.assertEqual(
            self.calls(),
            ["set-sink-mute @DEFAULT_SINK@ 1", "set-sink-volume @DEFAULT_SINK@ 0%"],
        )

    def test_reads_the_current_percentage_back(self):
        self.assertEqual(self.backend.current_percent(), 250)

    def test_failure_becomes_backend_error(self):
        with self.assertRaises(BackendError):
            self.backend._run("set-sink-volume", "@DEFAULT_SINK@", "fail-me")

    def test_missing_pactl_is_reported(self):
        missing = LinuxBackend()
        missing.pactl = None
        self.assertFalse(missing.available())
        with self.assertRaises(BackendError):
            missing.apply(100)

    def test_unavailable_current_percentage_returns_none(self):
        broken = LinuxBackend()
        broken.pactl = None
        self.assertIsNone(broken.current_percent())


class ParseVolumeTests(unittest.TestCase):
    def test_typical_pactl_output(self):
        output = (
            "Volume: front-left: 65536 / 100% / 0.00 dB,   "
            "front-right: 65536 / 100% / 0.00 dB\n"
            "        balance 0.00\n"
            "        base volume: 65536 / 100% / 0.00 dB\n"
        )
        self.assertEqual(parse_volume(output), 100)

    def test_above_full_scale(self):
        self.assertEqual(parse_volume("Volume: front-left: 327680 / 500% / 13.98 dB"), 500)

    def test_muted_sink_still_reports_volume(self):
        self.assertEqual(parse_volume("Volume: mono: 0 /   0% / -inf dB"), 0)

    def test_garbage_returns_none(self):
        self.assertIsNone(parse_volume(""))
        self.assertIsNone(parse_volume("no volume here"))


class DesktopEntryTests(unittest.TestCase):
    def test_entry_is_valid(self):
        entry = autostart.desktop_entry('"/usr/bin/volume-amplifier" --minimized')
        self.assertTrue(entry.startswith("[Desktop Entry]"))
        self.assertIn("Type=Application", entry)
        self.assertIn('Exec="/usr/bin/volume-amplifier" --minimized', entry)
        self.assertIn("Terminal=false", entry)

    def test_launch_command_requests_minimized(self):
        command = autostart.launch_command()
        self.assertTrue(command.endswith("--minimized"), command)
        self.assertIn("app.py", command)


if __name__ == "__main__":
    unittest.main(verbosity=2)
