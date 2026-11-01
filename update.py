"""Check GitHub for a newer release.

This is the only network call the application ever makes, and it only happens
when the user asks for it or explicitly turns automatic checks on. Nothing is sent
except the request itself: no identifiers, no counters, no usage data.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

import version

API_URL = "https://api.github.com/repos/LeGaliza85/volume-booster-pc/releases/latest"
RELEASES_URL = f"{version.REPOSITORY}/releases/latest"
TIMEOUT = 6.0
USER_AGENT = f"{version.APP_ID}/{version.VERSION}"

STATUS_CURRENT = "current"
STATUS_NEWER = "newer"
STATUS_UNKNOWN = "unknown"


def parse_version(text: str | None) -> tuple[int, ...]:
    """``v1.3.1`` -> ``(1, 3, 1)``. Anything unparsable becomes an empty tuple."""
    cleaned = (text or "").strip().lstrip("vV")
    parts: list[int] = []
    for chunk in cleaned.split("."):
        digits = "".join(character for character in chunk if character.isdigit())
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts)


def is_newer(local: str | None, remote: str | None) -> bool:
    local_version = parse_version(local)
    remote_version = parse_version(remote)
    if not remote_version:
        return False
    return remote_version > local_version


def latest_tag(timeout: float = TIMEOUT) -> str | None:
    """The latest release tag, or None when the check cannot be completed."""
    request = urllib.request.Request(
        API_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError, urllib.error.URLError):
        return None
    tag = payload.get("tag_name") if isinstance(payload, dict) else None
    return tag if isinstance(tag, str) and tag else None


def check(timeout: float = TIMEOUT) -> dict:
    """``{"status": current|newer|unknown, "latest": "1.4.0", "url": ...}``"""
    tag = latest_tag(timeout)
    if not tag:
        return {"status": STATUS_UNKNOWN, "latest": "", "url": RELEASES_URL}
    latest = tag.lstrip("vV")
    status = STATUS_NEWER if is_newer(version.VERSION, tag) else STATUS_CURRENT
    return {"status": status, "latest": latest, "url": RELEASES_URL}
