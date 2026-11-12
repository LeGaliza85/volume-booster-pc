"""Proof that the boost is actually wired up, not merely written to a file.

A config block means the app did its job; it does not mean Windows is running the
APO. Equalizer APO is only active on devices where its COM classes are listed in
the endpoint's FX property store, so that is what we inspect. The device that is
actually playing matters too: an APO attached to the TV is irrelevant while the
default output is a pair of USB speakers, so the default endpoint is checked
explicitly.

Windows-only; every function fails closed (returns "unknown") elsewhere.
"""

from __future__ import annotations

import ctypes
import re
import sys
import uuid
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
_ENDPOINT_GUID = re.compile(
    r"\{[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\}\s*$"
)
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


def endpoint_guid(device_id: object) -> str:
    """The endpoint GUID inside an MMDevice ID, lowercased, or "".

    MMDevice IDs look like ``{0.0.0.00000000}.{guid}``, while the registry keys
    under ``MMDevices\\Audio\\Render`` are the bare ``{guid}``, so both spellings
    must compare equal.
    """
    match = _ENDPOINT_GUID.search(str(device_id or ""))
    return match.group(0).strip().lower() if match else ""


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


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_uint32),
        ("Data2", ctypes.c_uint16),
        ("Data3", ctypes.c_uint16),
        ("Data4", ctypes.c_ubyte * 8),
    ]


def _guid(value: str) -> _GUID:
    return _GUID.from_buffer_copy(uuid.UUID(value).bytes_le)


_CLSID_MMDEVICE_ENUMERATOR = _guid("BCDE0395-E52F-467C-8E3D-C4579291692E")
_IID_IMMDEVICE_ENUMERATOR = _guid("A95664D2-9614-4F35-A746-DE8DB63617E6")
_CLSCTX_ALL = 0x17
_COINIT_APARTMENTTHREADED = 0x2
_RENDER = 0
_MULTIMEDIA = 1


def _com_call(pointer, index: int, *argument_types):
    table = ctypes.cast(pointer, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))[0]
    prototype = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, *argument_types)
    return prototype(table[index])


def _default_endpoint_id() -> str | None:
    """COM walk: MMDeviceEnumerator -> default playback device -> its ID."""
    ole32 = ctypes.WinDLL("ole32")
    ole32.CoInitializeEx.argtypes = (ctypes.c_void_p, ctypes.c_uint32)
    ole32.CoInitializeEx.restype = ctypes.c_long
    ole32.CoCreateInstance.argtypes = (
        ctypes.POINTER(_GUID),
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.POINTER(_GUID),
        ctypes.POINTER(ctypes.c_void_p),
    )
    ole32.CoCreateInstance.restype = ctypes.c_long
    ole32.CoTaskMemFree.argtypes = (ctypes.c_void_p,)

    initialised = ole32.CoInitializeEx(None, _COINIT_APARTMENTTHREADED) >= 0
    enumerator = ctypes.c_void_p()
    try:
        result = ole32.CoCreateInstance(
            ctypes.byref(_CLSID_MMDEVICE_ENUMERATOR),
            None,
            _CLSCTX_ALL,
            ctypes.byref(_IID_IMMDEVICE_ENUMERATOR),
            ctypes.byref(enumerator),
        )
        if result != 0 or not enumerator:
            return None
        try:
            get_default = _com_call(
                enumerator, 4, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)
            )
            device = ctypes.c_void_p()
            result = get_default(enumerator, _RENDER, _MULTIMEDIA, ctypes.byref(device))
            if result != 0 or not device:
                return None
            try:
                get_id = _com_call(device, 5, ctypes.POINTER(ctypes.c_wchar_p))
                raw = ctypes.c_wchar_p()
                result = get_id(device, ctypes.byref(raw))
                if result != 0 or not raw.value:
                    return None
                try:
                    return raw.value
                finally:
                    ole32.CoTaskMemFree(ctypes.cast(raw, ctypes.c_void_p))
            finally:
                _com_call(device, 2)(device)
        finally:
            _com_call(enumerator, 2)(enumerator)
    finally:
        if initialised:
            ole32.CoUninitialize()


def default_render_endpoint_id() -> str | None:
    """ID of the system's default playback device, or None when unknown."""
    if not sys.platform.startswith("win"):
        return None
    try:
        return _default_endpoint_id()
    except (OSError, AttributeError, ValueError, ctypes.ArgumentError):
        return None


def _default_mismatch(endpoints: list[dict], default_id: str | None) -> str | None:
    """Name of the default endpoint when it lacks the APO, else None.

    An unknown default (no COM, or an endpoint the registry does not list) never
    invents a failure.
    """
    key = endpoint_guid(default_id)
    if not key:
        return None
    for item in endpoints:
        if endpoint_guid(item.get("id")) != key:
            continue
        return None if item["attached"] else item["name"]
    return None


def health(
    config_text: str | None,
    expected_db: float,
    *,
    is_installed=None,
    list_endpoints=None,
    default_id: str | None = None,
) -> dict:
    """One of: unsupported | missing | detached | drift | ok.

    ``is_installed``, ``list_endpoints`` and ``default_id`` exist so the state
    machine can be tested without a real audio stack.
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
    blocked = [item["name"] for item in attached if item.get("enhancements_disabled")]
    if real_call and default_id is None:
        default_id = default_render_endpoint_id()
    missing_on_default = _default_mismatch(endpoints, default_id)
    if missing_on_default:
        return {
            "level": "detached",
            "devices": names,
            "default": missing_on_default,
            "endpoints": len(endpoints),
            "blocked": blocked,
        }
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
