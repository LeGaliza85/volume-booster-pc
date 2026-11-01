"""Platform backend selection.

Each platform owns a different engine because Windows has no user-mode gain above
100 %, while Linux does:

  * Windows -> Equalizer APO config block (see apo.py / backend_windows.py)
  * Linux   -> PulseAudio / PipeWire sink volume (native, no extra component)
  * macOS   -> no system-wide gain without a virtual audio device, so unsupported

Only the platform backend is imported, which keeps ``winreg`` off Linux.
"""

from __future__ import annotations

import sys


class BackendError(Exception):
    """The platform engine could not apply the requested gain."""


class UnsupportedBackend:
    key = "unsupported"
    engine = "-"

    def available(self) -> bool:
        return False

    def apply(self, percent: int) -> None:
        raise BackendError("This operating system is not supported yet.")

    def location(self) -> str:
        return ""


def detect() -> object:
    """Return the backend for the current platform."""
    if sys.platform.startswith("win"):
        from backend_windows import WindowsBackend

        return WindowsBackend()
    if sys.platform.startswith("linux"):
        from backend_linux import LinuxBackend

        return LinuxBackend()
    return UnsupportedBackend()
