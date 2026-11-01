"""Windows-side requirements: what to check, and where to send the user to fix it.

Only what actually needs attention is returned. A row that is fine and has
nothing to do would just be noise, and the settings window is a list of things to
fix, not a status screen.

The two things the app cannot detect are shown as instructions, never as a fake
verdict: whether "Disable all enhancements" is ticked, and whether Windows still
wants a reboot. The second one is inferred from the APO not being attached yet,
which is the only reboot signal that belongs to this app's domain.
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
    """The Sound control panel, where a device's Enhancements tab lives.

    Windows has no documented way to open one device's properties page directly,
    so this lands on the Playback tab and the instructions say what to click next.
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


def inspect(*, installed: bool, level: str) -> list[dict]:
    """Rows that need the user's attention, in the order they should be fixed."""
    attached = level in ("ok", "drift")
    if not installed:
        return [
            {
                "key": "req_engine",
                "state": FAIL,
                "action": OPEN_DOWNLOAD,
                "label": "download",
            }
        ]

    rows: list[dict] = [
        {
            "key": "req_attached",
            "state": OK if attached else FAIL,
            "action": OPEN_CONFIGURATOR,
            "label": "change" if attached else "open",
        },
        {
            "key": "req_enhancements",
            "state": INFO,
            "action": OPEN_SOUND,
            "label": "open_sound",
        },
    ]
    if not attached:
        # Attached means the APO is already running, so there is nothing to reboot
        # for. Not attached right after an install usually is a pending restart.
        rows.append({"key": "req_reboot", "state": INFO, "action": NONE, "label": NONE})
    return rows
