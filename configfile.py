"""The Pro project's own gain file, independent from any other app's block.

Equalizer APO only has one audio chain per device, so two `Preamp` blocks would
add up instead of replacing each other. To stay safe:

  * the gain lives in ``volume-booster.txt``, a file this app owns;
  * ``config.txt`` only carries a single ``Include:`` line pointing at it;
  * the legacy block written by the previous app is removed, so exactly one gain
    source exists.

All functions here are pure: they take and return text.
"""

from __future__ import annotations

import os
from pathlib import Path

INCLUDE_NAME = "volume-booster.txt"
INCLUDE_LINE = f"Include: {INCLUDE_NAME}"

PRO_BEGIN = "# >>> Volume Booster >>>"
PRO_END = "# <<< Volume Booster <<<"
LEGACY_BEGIN = "# >>> Amplificador Voz >>>"
LEGACY_END = "# <<< Amplificador Voz <<<"

_BLOCKS = ((PRO_BEGIN, PRO_END), (LEGACY_BEGIN, LEGACY_END))


class ConfigError(Exception):
    """The config could not be prepared without guessing."""


def _newline(text: str) -> str:
    if not text:
        return "\r\n" if os.name == "nt" else "\n"
    crlf = text.count("\r\n")
    return "\r\n" if crlf > (text.count("\n") - crlf) else "\n"


def strip_blocks(text: str) -> str:
    """Remove every block this app or its predecessor wrote."""
    for begin, end in _BLOCKS:
        lines = text.splitlines(keepends=True)
        if sum(1 for line in lines if line.strip() == begin) != sum(
            1 for line in lines if line.strip() == end
        ):
            raise ConfigError(f"Unbalanced markers: {begin}")
        kept: list[str] = []
        inside = False
        for line in lines:
            token = line.strip()
            if token == begin:
                inside = True
                continue
            if token == end:
                inside = False
                continue
            if not inside:
                kept.append(line)
        text = "".join(kept)
    return text


def include_present(text: str) -> bool:
    return any(line.strip().lower() == INCLUDE_LINE.lower() for line in text.splitlines())


def ensure_include(text: str) -> str:
    """Exactly one include line, at the top, so it applies to every device block."""
    newline = _newline(text)
    without = "".join(
        line
        for line in text.splitlines(keepends=True)
        if line.strip().lower() != INCLUDE_LINE.lower()
    )
    return INCLUDE_LINE + newline + without


def prepare_config(text: str) -> str:
    return ensure_include(strip_blocks(text))


def render_gain(percent_db: float) -> str:
    return f"Preamp: {percent_db:.2f} dB\n"


def include_path(config_path: Path) -> Path:
    return config_path.parent / INCLUDE_NAME


def has_gain(text: str) -> bool:
    return "preamp:" in (text or "").lower()
