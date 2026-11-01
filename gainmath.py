"""Platform-neutral gain math shared by every backend."""

from __future__ import annotations

import math

MIN_PERCENT = 0
MAX_PERCENT = 500
DEFAULT_PERCENT = 100
SILENT_DB = -100.0


def clamp_percent(value: object) -> int:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return DEFAULT_PERCENT
    if math.isnan(number) or math.isinf(number):
        return DEFAULT_PERCENT
    return int(max(MIN_PERCENT, min(MAX_PERCENT, round(number))))


def percent_to_db(percent: float) -> float:
    """Linear gain as dB. 100 % -> 0 dB, 500 % -> +13.98 dB, 0 % -> silence."""
    value = float(percent)
    if value <= 0:
        return SILENT_DB
    return round(20.0 * math.log10(value / 100.0), 2)


def format_db(db: float) -> str:
    if db > 0:
        return f"+{db:.2f} dB"
    return f"{db:.2f} dB"
