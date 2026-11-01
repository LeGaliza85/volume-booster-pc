"""Windows-side requirements: what to check, and where to send the user to fix it.

The app can only *detect* part of this. Equalizer APO installed and attached are
readable from the registry; "Disable all enhancements" and "you have not
rebooted" are not, so those are shown as advice rather than as a pass/fail the
code would be inventing.
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


def _startfile(target: str) -> bool:
    try:
        os.startfile(target)
        return True
    except (AttributeError, OSError):
        return False


def configurator() -> Path | None:
    """Equalizer APO's Configurator, where devices get ticked."""
    if not sys.platform.startswith("win"):
        return None
    for variable in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)"):
        root = os.environ.get(variable)
        if not root:
            continue
        for name in ("Configurator.exe", "EqualizerAPO.exe"):
            candidate = Path(root) / "EqualizerAPO" / name
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
        return open_download()
    return _startfile(str(target))


def open_sound() -> bool:
    """Sound settings, where enhancements live for each playback device."""
    if not sys.platform.startswith("win"):
        return False
    for target in ("ms-settings:sound", "mmsys.cpl"):
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


def inspect(*, installed: bool, level: str) -> list[dict]:
    """Rows for the settings window. ``level`` is the engine health level."""
    attached = level in ("ok", "drift")
    return [
        {
            "key": "req_engine",
            "state": OK if installed else FAIL,
            "action": NONE if installed else OPEN_DOWNLOAD,
        },
        {
            "key": "req_attached",
            "state": OK if attached else FAIL,
            "action": NONE if attached else OPEN_CONFIGURATOR,
        },
        {
            "key": "req_enhancements",
            "state": INFO,
            "action": OPEN_SOUND,
        },
        {
            "key": "req_reboot",
            "state": INFO,
            "action": NONE,
        },
    ]
