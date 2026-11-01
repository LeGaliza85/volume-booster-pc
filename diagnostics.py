"""Crash-safe logging and the support bundle.

Everything stays on the machine: no telemetry, no network. The bundle is a zip the
user can attach to an issue, containing a scrubbed report and the recent log.
"""

from __future__ import annotations

import contextlib
import faulthandler
import json
import logging
import os
import platform
import re
import sys
import zipfile
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

import version

LOG_NAME = "app.log"
_MAX_BYTES = 512_000
_BACKUPS = 3
_LOG_TAIL_LINES = 400
_PREAMP = re.compile(r"^Preamp:\s*(-?\d+(?:\.\d+)?)\s*dB", re.IGNORECASE | re.MULTILINE)


def app_data_dir() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / version.APP_ID
    return Path.home() / ".local" / "share" / version.APP_ID


def log_dir() -> Path:
    return app_data_dir() / "logs"


def log_path() -> Path:
    return log_dir() / LOG_NAME


def crash_log_path() -> Path:
    return log_dir() / "crash.log"


_CRASH_HANDLES: list = []


def enable_crash_log() -> Path | None:
    """Record a native crash (an access violation in ctypes) with its Python stack.

    A failed Win32 call can kill the process without raising anything Python can
    catch, which leaves no evidence at all. faulthandler writes the stack at the
    moment of the fault.
    """
    target = crash_log_path()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        handle = open(target, "w", encoding="utf-8")  # noqa: SIM115 - faulthandler owns it
    except OSError:
        return None
    _CRASH_HANDLES.append(handle)
    faulthandler.enable(file=handle, all_threads=True)
    return target


def configure(root=None) -> Path:
    """Rotating file log plus hooks for unhandled and Tk-callback exceptions."""
    target = log_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    handlers: list[logging.Handler] = [
        RotatingFileHandler(target, maxBytes=_MAX_BYTES, backupCount=_BACKUPS, encoding="utf-8")
    ]
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=handlers,
        force=True,
    )

    def _hook(exc_type, exc_value, exc_tb):
        logging.getLogger("crash").exception("unhandled", exc_info=(exc_type, exc_value, exc_tb))

    sys.excepthook = _hook
    enable_crash_log()
    if root is not None:
        def _tk_hook(exc_type, exc_value, exc_tb):
            logging.getLogger("tk").exception(
                "callback failed", exc_info=(exc_type, exc_value, exc_tb)
            )

        root.report_callback_exception = _tk_hook
    return target


def text_block(text: str) -> str:
    """The gain line this app owns, if present."""
    match = _PREAMP.search(text or "")
    return f"{match.group(1)} dB" if match else ""


def scrub(value: object) -> str:
    """Remove user-identifying path fragments from anything we report."""
    text = str(value)
    home = str(Path.home())
    if home:
        text = text.replace(home, "<home>")
    user = os.environ.get("USERNAME") or os.environ.get("USER")
    if user and len(user) > 2:
        text = text.replace(user, "<user>")
    text = re.sub(r"([A-Za-z]:\\Users\\)[^\\]+", r"\1<user>", text)
    return text


def _scrub_tree(value):
    if isinstance(value, dict):
        return {key: _scrub_tree(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_scrub_tree(item) for item in value]
    if isinstance(value, str):
        return scrub(value)
    return value


def environment() -> dict:
    return {
        "app": version.APP_NAME,
        "version": version.VERSION,
        "frozen": bool(getattr(sys, "frozen", False)),
        "executable": sys.executable,
        "python": platform.python_version(),
        "os": platform.platform(),
        "arch": platform.machine(),
        "locale": os.environ.get("LANG") or os.environ.get("LC_ALL") or "",
    }


def log_tail(lines: int = _LOG_TAIL_LINES) -> str:
    try:
        with log_path().open("r", encoding="utf-8", errors="replace") as handle:
            content = handle.readlines()
    except OSError:
        return ""
    return "".join(content[-lines:])


def build_report(extra: dict | None = None) -> dict:
    report = environment()
    report.update(
        {
            "generated": datetime.now().isoformat(timespec="seconds"),
            "log_path": str(log_path()),
        }
    )
    if extra:
        report.update(extra)
    return _scrub_tree(report)


def export(extra: dict | None = None, destination: Path | None = None) -> Path:
    """Write a zip support bundle and return its path."""
    app_data_dir().mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = destination or (app_data_dir() / f"diagnostics-{stamp}.zip")
    report = build_report(extra)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("report.json", json.dumps(report, indent=2, ensure_ascii=False))
        tail = log_tail()
        if tail:
            bundle.writestr("app.log", tail)
        crash = crash_log_path()
        if crash.exists():
            with contextlib.suppress(OSError):
                bundle.writestr("crash.log", crash.read_text(encoding="utf-8", errors="replace"))
    return target
