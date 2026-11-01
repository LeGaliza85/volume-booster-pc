"""Hand the downloaded installer to Windows after this process exits.

The installer has to replace the running executable, so the app cannot stay alive
while it works. A detached batch waits a couple of seconds, runs the installer
silently, starts the app again and deletes itself.

Nothing here decides *whether* to update: that is the caller's business, after the
hash has been checked.
"""

from __future__ import annotations

import contextlib
import subprocess
import sys
import tempfile
from pathlib import Path

DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
WAIT_SECONDS = 3


def installed_build() -> bool:
    """True when this executable came from the installer.

    The portable build is a single loose file, so it must never install another
    copy of itself behind the user's back; it only gets told about the update.
    """
    if not getattr(sys, "frozen", False):
        return False
    return (Path(sys.executable).parent / "unins000.exe").exists()


def script(setup: Path, app: Path, wait: int = WAIT_SECONDS) -> str:
    """The batch text: wait, install silently, wait it out, relaunch, clean up.

    ``start /wait`` is not enough on its own: Inno Setup can re-exec itself, so the
    parent returns while the real install is still writing files. Relaunching at
    that moment gives "Failed to load Python DLL", because the app extracts itself
    from an executable that is being replaced. The loop waits for the setup process
    to disappear before starting the app again.
    """
    setup_name = setup.name
    return "\r\n".join(
        [
            "@echo off",
            f"ping -n {wait + 1} 127.0.0.1 >nul",
            f'start "" /wait "{setup}" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART',
            ":waitforinstaller",
            f'tasklist /fi "imagename eq {setup_name}" 2>nul | find /i "{setup_name}" >nul',
            "if not errorlevel 1 (",
            "    ping -n 2 127.0.0.1 >nul",
            "    goto waitforinstaller",
            ")",
            "ping -n 3 127.0.0.1 >nul",
            f'start "" "{app}"',
            f'del /q "{setup}"',
            'del /q "%~f0"',
            "",
        ]
    )


def launch(setup: Path, app: Path) -> bool:
    """Start the detached updater. The caller is expected to quit right after."""
    if not sys.platform.startswith("win"):
        return False
    target = Path(tempfile.gettempdir()) / "volume-booster-update.cmd"
    try:
        target.write_text(script(setup, app), encoding="ascii")
    except OSError:
        return False
    try:
        subprocess.Popen(
            ["cmd", "/c", str(target)],
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
            close_fds=True,
        )
    except OSError:
        return False
    return True


def cleanup() -> None:
    """Remove the batch and the installer left behind by a failed attempt."""
    for name in ("volume-booster-update.cmd", "VolumeBoosterSetup.exe"):
        with contextlib.suppress(OSError):
            (Path(tempfile.gettempdir()) / name).unlink()
