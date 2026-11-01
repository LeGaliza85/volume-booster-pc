"""Check GitHub for a newer release, and fetch its installer when asked to.

This is the only network activity in the application. It happens when the user
presses the check button, or at startup if they turned that on, and the download
only happens when they also turned on automatic installation. Nothing is sent
except the request itself: no identifiers, no counters, no usage data.

An installer is a program, so it is never executed on trust: the SHA-256 from the
release's own ``SHA256SUMS-windows.txt`` is checked first.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path

import version

API_URL = "https://api.github.com/repos/LeGaliza85/volume-booster-pc/releases/latest"
RELEASES_URL = f"{version.REPOSITORY}/releases/latest"
TIMEOUT = 6.0
DOWNLOAD_TIMEOUT = 60.0
USER_AGENT = f"{version.APP_ID}/{version.VERSION}"

STATUS_CURRENT = "current"
STATUS_NEWER = "newer"
STATUS_UNKNOWN = "unknown"

SETUP_NAME = "VolumeBoosterSetup.exe"
SUMS_NAME = "SHA256SUMS-windows.txt"


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


def _get(url: str, timeout: float) -> bytes:
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _asset_urls(payload: dict) -> dict[str, str]:
    urls: dict[str, str] = {}
    for asset in payload.get("assets") or []:
        name = asset.get("name")
        url = asset.get("browser_download_url")
        if isinstance(name, str) and isinstance(url, str):
            urls[name] = url
    return urls


def latest_release(timeout: float = TIMEOUT) -> dict | None:
    """Tag, version and installer URLs, or None when the check cannot complete."""
    try:
        payload = json.loads(_get(API_URL, timeout).decode("utf-8"))
    except (OSError, ValueError, urllib.error.URLError):
        return None
    if not isinstance(payload, dict):
        return None
    tag = payload.get("tag_name")
    if not isinstance(tag, str) or not tag:
        return None
    assets = _asset_urls(payload)
    return {
        "tag": tag,
        "version": tag.lstrip("vV"),
        "setup": assets.get(SETUP_NAME, ""),
        "sums": assets.get(SUMS_NAME, ""),
    }


def check(timeout: float = TIMEOUT) -> dict:
    """``{"status": current|newer|unknown, "latest": "1.4.0", "url": ..., ...}``"""
    release = latest_release(timeout)
    if release is None:
        return {"status": STATUS_UNKNOWN, "latest": "", "url": RELEASES_URL}
    status = STATUS_NEWER if is_newer(version.VERSION, release["tag"]) else STATUS_CURRENT
    return {
        "status": status,
        "latest": release["version"],
        "url": RELEASES_URL,
        "setup": release["setup"],
        "sums": release["sums"],
    }


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def expected_hash(sums_text: str, filename: str) -> str:
    """The hash for ``filename`` in a ``<hash>  <name>`` file, or an empty string."""
    for line in (sums_text or "").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[-1].lstrip("*") == filename:
            candidate = parts[0].strip().upper()
            if len(candidate) == 64 and all(c in "0123456789ABCDEF" for c in candidate):
                return candidate
    return ""


def download_installer(destination: Path, *, timeout: float = DOWNLOAD_TIMEOUT) -> Path | None:
    """Fetch the installer and its checksum, verify it, and return the path.

    Returns None on any doubt: no URLs, a failed download, a missing checksum, or
    a hash that does not match. Nothing is executed here.
    """
    release = latest_release()
    if release is None:
        return None
    setup_url = release.get("setup") or ""
    sums_url = release.get("sums") or ""
    if not setup_url or not sums_url:
        return None
    try:
        setup_bytes = _get(setup_url, timeout)
        sums_text = _get(sums_url, timeout).decode("utf-8", "replace")
    except (OSError, ValueError, urllib.error.URLError):
        return None

    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        destination.write_bytes(setup_bytes)
    except OSError:
        return None

    expected = expected_hash(sums_text, SETUP_NAME)
    if not expected or sha256_of(destination) != expected:
        with contextlib.suppress(OSError):
            destination.unlink()
        return None
    return destination
