"""Windows-side requirements: what to check, and where to send the user to fix it.

Only what actually needs attention is returned. A row that is fine and has
nothing to do would just be noise, and the settings window is a list of things to
fix, not a status screen.

"Disable all enhancements" *is* detectable: Windows stores it per endpoint as
PKEY_AudioEndpoint_Disable_SysFx (verify.py reads it). Windows still offers no way
to open one device's properties page directly, so the row explains the clicks and
the button opens the Sound panel — but the row appears and disappears on its own,
without the user having to mark anything as done.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

APO_DOWNLOAD = "https://sourceforge.net/projects/equalizerapo/"
OK = "ok"
FAIL = "fail"
INFO = "info"

# action ids understood by settingswindow.py
OPEN_DOWNLOAD = "download"
OPEN_CONFIGURATOR = "configurator"
OPEN_SOUND = "sound"
NONE = "none"

# Equalizer APO 1.4 ships the device picker as DeviceSelector.exe; older builds
# called it Configurator.exe. Missing either one used to fall back to the download
# page, which is nonsense when the app is already installed.
_CONFIGURATOR_NAMES = ("DeviceSelector.exe", "Configurator.exe", "EqualizerAPO.exe")


def _startfile(target: str) -> bool:
    try:
        os.startfile(target)
        return True
    except (AttributeError, OSError):
        return False


def _launch(path: Path) -> bool:
    """Start an elevated Qt tool with its own folder as the working directory.

    The Equalizer APO device picker requests administrator rights in its
    manifest, so ``subprocess.Popen`` is refused with WinError 740. The
    ``runas`` verb shows the UAC prompt and then starts it. The working
    directory matters too: the Qt tools ship plugins in ``qt/platforms`` and
    have no ``qt.conf``, so they only find them when the process starts inside
    their folder.
    """
    try:
        import ctypes
        from ctypes import wintypes

        shell32 = ctypes.WinDLL("shell32", use_last_error=True)
        shell32.ShellExecuteW.argtypes = (
            wintypes.HWND,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            ctypes.c_int,
        )
        shell32.ShellExecuteW.restype = ctypes.c_void_p
        result = shell32.ShellExecuteW(None, "runas", str(path), None, str(path.parent), 1)
    except (AttributeError, OSError):
        return False
    return int(result or 0) > 32


def configurator() -> Path | None:
    """The executable where devices get ticked."""
    if not sys.platform.startswith("win"):
        return None
    for variable in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)"):
        root = os.environ.get(variable)
        if not root:
            continue
        folder = Path(root) / "EqualizerAPO"
        for name in _CONFIGURATOR_NAMES:
            candidate = folder / name
            if candidate.exists():
                return candidate
    return None


def apo_installed() -> bool:
    """True when Equalizer APO's config file can be found the same way the engine does."""
    if not sys.platform.startswith("win"):
        return False
    import apo

    return apo.find_config_path() is not None


def open_download() -> bool:
    if not sys.platform.startswith("win"):
        return False
    return _startfile(APO_DOWNLOAD)


def open_configurator() -> bool:
    target = configurator()
    if target is None:
        return False
    return _launch(target)


def open_sound() -> bool:
    """The Sound control panel, where a device's Enhancements tab lives.

    Windows has no documented way to open one device's properties page directly,
    so this lands on the Playback tab and the row text says what to click next.
    """
    if not sys.platform.startswith("win"):
        return False
    for target in ("mmsys.cpl", "ms-settings:sound"):
        if _startfile(target):
            return True
    try:
        subprocess.Popen(["control", "mmsys.cpl"])
        return True
    except OSError:
        return False


def open_action(action: str) -> bool:
    if action == OPEN_DOWNLOAD:
        return open_download()
    if action == OPEN_CONFIGURATOR:
        return open_configurator()
    if action == OPEN_SOUND:
        return open_sound()
    return False


def inspect(*, installed: bool, level: str, blocked: list[str] | None = None) -> list[dict]:
    """Rows that need the user's attention, in the order they should be fixed."""
    attached = level in ("ok", "drift")
    if not installed:
        return [
            {"key": "req_engine", "state": FAIL, "action": OPEN_DOWNLOAD, "label": "download"}
        ]

    if not attached:
        return [
            {
                "key": "req_attached",
                "state": FAIL,
                "action": OPEN_CONFIGURATOR,
                "label": "open",
            },
            # Attached means the APO is already running, so there is nothing to
            # reboot for. Not attached right after an install usually is.
            {"key": "req_reboot", "state": INFO, "action": NONE, "label": NONE},
        ]

    rows: list[dict] = [
        {
            "key": "req_attached",
            "state": OK,
            "action": OPEN_CONFIGURATOR,
            "label": "change",
        }
    ]
    device = (blocked or [""])[0]
    if device:
        rows.append(
            {
                "key": "req_enhancements",
                "state": FAIL,
                "action": OPEN_SOUND,
                "label": "open_sound",
                "device": device,
            }
        )
    return rows
