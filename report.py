"""Build a pre-filled GitHub issue URL, so a bug report arrives with the basics.

The repository uses an issue form (``.github/ISSUE_TEMPLATE/bug_report.yml``).
GitHub pre-fills form fields from the query string using each field's ``id``, so
the app can hand over the version and the operating system without the reporter
typing them — the two things people most often get wrong or leave out.
"""

from __future__ import annotations

import sys
from urllib.parse import urlencode

import version

TEMPLATE = "bug_report.yml"
WINDOWS_11_BUILD = 22000

_OPTIONS = {
    "win": ("Windows 10", "Windows 11"),
    "linux": ("Linux (PipeWire)", "Linux (PulseAudio)"),
}


def os_option(*, platform: str | None = None, build: int | None = None) -> str:
    """The dropdown option for this machine, or an empty string when unknown.

    Returns an empty string rather than guessing: a value that does not match an
    option exactly is silently dropped by GitHub, which is worse than no value
    because the field then looks answered when it is not.
    """
    name = sys.platform if platform is None else platform
    if name.startswith("win"):
        if build is None:
            try:
                build = sys.getwindowsversion().build
            except AttributeError:
                return ""
        return _OPTIONS["win"][1 if build >= WINDOWS_11_BUILD else 0]
    if name.startswith("linux"):
        return _OPTIONS["linux"][0]
    return ""


def build_issue_url(*, app_version: str, os_name: str = "") -> str:
    """URL that opens the bug-report form with the known fields already filled."""
    title = f"[bug] {version.APP_NAME} {app_version}: "
    params: dict[str, str] = {
        "template": TEMPLATE,
        "title": title,
        "version": f"{version.APP_NAME} {app_version}",
    }
    if os_name:
        params["os"] = os_name
    return f"{version.REPOSITORY}/issues/new?{urlencode(params)}"
