"""Proof that the boost is actually wired up, not merely written to a file.

A config block means the app did its job; it does not mean Windows is running the
APO. Equalizer APO is only active on devices where its COM classes are listed in
the endpoint's FX property store, so that is what we inspect.

Windows-only; every function fails closed (returns "unknown") elsewhere.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Mapping

PRE_MIX = "{eacd2258-fcac-4ff4-b36d-419e924a6d79}"
POST_MIX = "{ec1cc9ce-faed-4822-828a-82a81a6f018f}"
APO_CLASSES = frozenset({PRE_MIX, POST_MIX})

_RENDER_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render"
_FX_PROPERTY = "{d04e05a6-594b-4fb6-a80d-01af5eed7d1d}"
_FRIENDLY_NAME = "{a45c254e-df1c-4efd-8020-67d146a850e0},2"
_INSTALL_KEY = r"SOFTWARE\EqualizerAPO"
_SYSFX_PROPERTY = "{1da5d803-d492-4edd-8c23-e0c0ffee7f0e},5"

_PREAMP = re.compile(r"^Preamp:\s*(-?\d+(?:\.\d+)?)\s*dB", re.IGNORECASE | re.MULTILINE)
_TOLERANCE_DB = 0.05


def endpoint_has_apo(properties: Mapping[str, str]) -> bool:
    """True when any FX slot of the endpoint points at an Equalizer APO class."""
    for name, value in properties.items():
        if not str(name).lower().startswith(_FX_PROPERTY):
            continue
        if str(value).strip().lower() in APO_CLASSES:
            return True
    return False


def preamp_db(text: str) -> float | None:
    match = _PREAMP.search(text or "")
    return float(match.group(1)) if match else None


def matches_expected(text: str, expected_db: float) -> bool:
    value = preamp_db(text)
    if value is None:
        return False
    return abs(value - expected_db) <= _TOLERANCE_DB


def installed() -> bool:
    """Equalizer APO registers itself here; the config file is checked separately."""
    if not sys.platform.startswith("win"):
        return False
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _INSTALL_KEY) as key:
            winreg.QueryValueEx(key, "InstallPath")
        return True
    except OSError:
        return False


def _read_properties(winreg, guid: str) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, rf"{_RENDER_KEY}\{guid}\FxProperties") as key:
            index = 0
            while True:
                try:
                    name, value, _kind = winreg.EnumValue(key, index)
                except OSError:
                    break
                values[name] = str(value)
                index += 1
    except OSError:
        return {}
    return values


def _friendly_name(winreg, guid: str) -> str:
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, rf"{_RENDER_KEY}\{guid}\Properties"
        ) as key:
            value, _kind = winreg.QueryValueEx(key, _FRIENDLY_NAME)
            return str(value)
    except OSError:
        return guid


def _enhancements_disabled(winreg, guid: str) -> bool:
    """PKEY_AudioEndpoint_Disable_SysFx: the "Disable all enhancements" checkbox.

    It lives in the endpoint's Properties key, not in FxProperties, and it is
    absent when the box is unticked, which is the healthy default.
    """
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, rf"{_RENDER_KEY}\{guid}\Properties"
        ) as key:
            value, _kind = winreg.QueryValueEx(key, _SYSFX_PROPERTY)
    except OSError:
        return False
    try:
        return int(value) != 0
    except (TypeError, ValueError):
        return False


def render_endpoints() -> list[dict]:
    """Every render endpoint present on the machine, with its attachment state."""
    if not sys.platform.startswith("win"):
        return []
    try:
        import winreg
    except ImportError:
        return []

    endpoints: list[dict] = []
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _RENDER_KEY) as root:
            index = 0
            while True:
                try:
                    guid = winreg.EnumKey(root, index)
                except OSError:
                    break
                index += 1
                properties = _read_properties(winreg, guid)
                if not properties:
                    continue
                endpoints.append(
                    {
                        "id": guid,
                        "name": _friendly_name(winreg, guid),
                        "attached": endpoint_has_apo(properties),
                        "enhancements_disabled": _enhancements_disabled(winreg, guid),
                    }
                )
    except OSError:
        return []
    return endpoints


def health(
    config_text: str | None,
    expected_db: float,
    *,
    is_installed=None,
    list_endpoints=None,
) -> dict:
    """One of: unsupported | missing | detached | drift | ok.

    ``is_installed`` and ``list_endpoints`` exist so the state machine can be
    tested without a real audio stack.
    """
    real_call = is_installed is None and list_endpoints is None
    if real_call and not sys.platform.startswith("win"):
        return {"level": "unsupported"}

    check = is_installed or installed
    if not check():
        return {"level": "missing"}

    endpoints = (list_endpoints or render_endpoints)()
    attached = [item for item in endpoints if item["attached"]]
    if not attached:
        return {"level": "detached", "endpoints": len(endpoints)}

    names = [item["name"] for item in attached]
    blocked = [
        item["name"] for item in attached if item.get("enhancements_disabled")
    ]
    if config_text is None or not matches_expected(config_text, expected_db):
        return {
            "level": "drift",
            "devices": names,
            "endpoints": len(endpoints),
            "blocked": blocked,
        }
    return {
        "level": "ok",
        "devices": names,
        "endpoints": len(endpoints),
        "blocked": blocked,
    }
