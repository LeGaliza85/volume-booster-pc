"""Start-at-login registration.

Windows uses the per-user Run key (no administrator needed), Linux uses an XDG
autostart entry. macOS is not supported by this app, so registration is refused.
"""

from __future__ import annotations

import sys
from pathlib import Path

from version import APP_ID, APP_NAME

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_DESKTOP_NAME = f"{APP_ID.lower()}.desktop"


def launch_command() -> str:
    """The exact command Windows/Linux should run at login."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --minimized'

    script = Path(__file__).resolve().parent / "app.py"
    executable = Path(sys.executable)
    if sys.platform.startswith("win"):
        windowless = executable.with_name("pythonw.exe")
        if windowless.exists():
            executable = windowless
    return f'"{executable}" "{script}" --minimized'


def desktop_entry(command: str) -> str:
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={APP_NAME}\n"
        f"Exec={command}\n"
        "Terminal=false\n"
        "X-GNOME-Autostart-enabled=true\n"
    )


def _desktop_path() -> Path:
    base = Path.home() / ".config" / "autostart"
    return base / _DESKTOP_NAME


def is_enabled() -> bool:
    if sys.platform.startswith("win"):
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_READ) as key:
                winreg.QueryValueEx(key, APP_ID)
            return True
        except OSError:
            return False
    if sys.platform.startswith("linux"):
        return _desktop_path().exists()
    return False


def enable() -> None:
    if sys.platform.startswith("win"):
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, APP_ID, 0, winreg.REG_SZ, launch_command())
        return
    if sys.platform.startswith("linux"):
        path = _desktop_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(desktop_entry(launch_command()), encoding="utf-8")
        return
    raise OSError("Start at login is not supported on this system.")


def disable() -> None:
    if sys.platform.startswith("win"):
        import winreg

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, APP_ID)
        except FileNotFoundError:
            pass
        return
    if sys.platform.startswith("linux"):
        _desktop_path().unlink(missing_ok=True)
        return
    raise OSError("Start at login is not supported on this system.")
