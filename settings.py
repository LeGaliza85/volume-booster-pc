"""User settings that personalise the app without touching the audio engine.

Stored as JSON next to the state file so it can be edited by hand and inspected
by support. Every value is sanitised on load: a broken file can never crash the
app or silently allow a dangerous level.
"""

from __future__ import annotations

import json
from pathlib import Path

import hotkey

DEFAULTS: dict = {
    "max_percent": 500,
    "confirm_above": 300,
    "restore_on_exit": False,
    "start_hidden": True,
    "close_to_tray": True,
    "hotkey_up": "Ctrl+Alt+Up",
    "hotkey_down": "Ctrl+Alt+Down",
}

LIMITS: dict[str, tuple[int, int]] = {
    "max_percent": (100, 1000),
    "confirm_above": (0, 1000),
}

BOOLEANS = ("restore_on_exit", "start_hidden", "close_to_tray")
HOTKEYS = ("hotkey_up", "hotkey_down")


def sanitize(raw: object) -> dict:
    data = dict(DEFAULTS)
    if not isinstance(raw, dict):
        return data

    for key, (low, high) in LIMITS.items():
        if key not in raw:
            continue
        try:
            value = int(raw[key])
        except (TypeError, ValueError):
            continue
        data[key] = max(low, min(high, value))

    for key in BOOLEANS:
        if isinstance(raw.get(key), bool):
            data[key] = raw[key]

    # An empty string is a deliberate "no hotkey"; anything else must parse, or
    # it falls back to the default instead of silently doing nothing.
    for key in HOTKEYS:
        if key not in raw:
            continue
        value = raw[key]
        if value == "":
            data[key] = ""
        elif isinstance(value, str) and hotkey.is_valid(value):
            data[key] = hotkey.normalise(value)

    data["confirm_above"] = min(data["confirm_above"], data["max_percent"])
    return data


def load(path: Path) -> dict:
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, AttributeError):
        return dict(DEFAULTS)
    return sanitize(raw)


def save(path: Path, data: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(sanitize(data), indent=2), encoding="utf-8")
    except OSError:
        pass


def should_confirm(percent: int, data: dict) -> bool:
    """Ask before a jump above the user's own comfort threshold."""
    limit = int(data.get("confirm_above", 0) or 0)
    return limit > 0 and percent > limit
