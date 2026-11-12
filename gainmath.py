"""Platform-neutral gain math shared by every backend."""

from __future__ import annotations

import math

MIN_PERCENT = 0
MAX_PERCENT = 1000
DEFAULT_PERCENT = 100
SILENT_DB = -100.0
# The slider travel is linear in decibels, not in percentage: 0 % sits at the
# left end, 100 % (0 dB) two thirds along, and the ceiling at the right end.
# A linear percentage scale compresses the last 14 dB of a 1000 % range into a
# few pixels, which is what made the top of the slider feel dead.
MIN_POSITION_DB = -40.0


def clamp_percent(value: object) -> int:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return DEFAULT_PERCENT
    if math.isnan(number) or math.isinf(number):
        return DEFAULT_PERCENT
    return int(max(MIN_PERCENT, min(MAX_PERCENT, round(number))))


def percent_to_db(percent: float) -> float:
    """Linear gain as dB. 100 % -> 0 dB, 500 % -> +13.98 dB, 1000 % -> +20 dB."""
    value = float(percent)
    if value <= 0:
        return SILENT_DB
    return round(20.0 * math.log10(value / 100.0), 2)


def percent_to_position(percent: float, maximum: int) -> float:
    """Slider travel (0..1) for a percentage, linear in dB.

    0 % is the left end; the ceiling is the right end; 100 % lands where 0 dB
    falls, which is 2/3 of the travel for the default 1000 % ceiling.
    """
    ceiling = percent_to_db(maximum)
    span = ceiling - MIN_POSITION_DB
    if span <= 0:
        return 0.0
    value = percent_to_db(max(MIN_PERCENT, min(float(maximum), float(percent))))
    return max(0.0, min(1.0, (value - MIN_POSITION_DB) / span))


def position_to_percent(position: float, maximum: int) -> int:
    """Percentage for a slider position (0..1), linear in dB.

    The left end is 0 % (mute). Moving right from it starts at 1 % (-40 dB).
    """
    ratio = max(0.0, min(1.0, float(position)))
    if ratio <= 0.0:
        return MIN_PERCENT
    ceiling = percent_to_db(maximum)
    span = ceiling - MIN_POSITION_DB
    if span <= 0:
        return int(maximum)
    db = MIN_POSITION_DB + ratio * span
    percent = round(100.0 * 10 ** (db / 20.0))
    return int(max(1, min(int(maximum), percent)))


def format_db(db: float) -> str:
    if db > 0:
        return f"+{db:.2f} dB"
    return f"{db:.2f} dB"
