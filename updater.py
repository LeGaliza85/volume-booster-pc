"""Hand the downloaded installer to the installer itself.

The installer replaces the running executable, so the app cannot stay alive while
it works — and it must not guess when the installer has finished. Inno Setup runs
the app again through its `[Run]` entry, which happens after the files are written.

An earlier version used a detached batch that waited and relaunched; that raced
with Inno re-executing itself, and the new process failed to load its bundled
Python DLL.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

INSTALL_FLAGS = ("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART")


def installed_build() -> bool:
    """True when this executable came from the installer.

    The portable build is a single loose file, so it must never install another
    copy of itself behind the user's back; it only gets told about the update.
    """
    if not getattr(sys, "frozen", False):
        return False
    return (Path(sys.executable).parent / "unins000.exe").exists()


def launch(setup: Path) -> bool:
    """Start the silent installer and let it outlive us.

    No ``DETACHED_PROCESS``: with that flag Inno Setup finishes the install but
    never runs its ``[Run]`` entry, so the app never comes back. A plain child is
    enough — Windows does not kill it when this process exits, which is what the
    app does right after this call.
    """
    if not sys.platform.startswith("win"):
        return False
    try:
        subprocess.Popen([str(setup), *INSTALL_FLAGS], close_fds=True)
    except OSError:
        return False
    return True
