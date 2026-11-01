"""Linux backend: PulseAudio and PipeWire accept sink volume above 100 %."""

from __future__ import annotations

import re
import shutil
import subprocess

from backend import BackendError

DEFAULT_SINK = "@DEFAULT_SINK@"
_PERCENT = re.compile(r"(\d+)%")


class LinuxBackend:
    key = "linux"
    engine = "PipeWire / PulseAudio"
    help_key = "help_linux"

    def __init__(self) -> None:
        self.pactl = shutil.which("pactl")

    def available(self) -> bool:
        return self.pactl is not None

    def apply(self, percent: int) -> None:
        if not self.pactl:
            raise BackendError("pactl not found.")
        if percent <= 0:
            self._run("set-sink-mute", DEFAULT_SINK, "1")
            self._run("set-sink-volume", DEFAULT_SINK, "0%")
            return
        self._run("set-sink-mute", DEFAULT_SINK, "0")
        self._run("set-sink-volume", DEFAULT_SINK, f"{percent}%")

    def current_percent(self) -> int | None:
        """Read the sink volume back, so the UI can follow the system keys."""
        if not self.pactl:
            return None
        try:
            output = self._run("get-sink-volume", DEFAULT_SINK)
        except BackendError:
            return None
        return parse_volume(output)

    def location(self) -> str:
        return self.pactl or "pactl"

    def _run(self, *arguments: str) -> str:
        pactl = self.pactl
        if not pactl:
            raise BackendError("pactl not found.")
        try:
            done = subprocess.run(
                [pactl, *arguments],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise BackendError(str(exc)) from exc
        if done.returncode != 0:
            message = (done.stderr or done.stdout).strip() or f"pactl exit {done.returncode}"
            raise BackendError(message)
        return done.stdout


def parse_volume(output: str) -> int | None:
    """First percentage in ``pactl get-sink-volume`` output, e.g. 65536 / 250%."""
    match = _PERCENT.search(output or "")
    return int(match.group(1)) if match else None
