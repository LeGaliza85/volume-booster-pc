"""Windows backend: the gain lives in Equalizer APO's config file."""

from __future__ import annotations

import apo
from backend import BackendError


class WindowsBackend:
    key = "windows"
    engine = "Equalizer APO"
    help_key = "help_windows"

    def __init__(self) -> None:
        self.path = apo.find_config_path()

    def available(self) -> bool:
        return self.path is not None

    def apply(self, percent: int) -> None:
        if self.path is None:
            raise BackendError("Equalizer APO config not found.")
        try:
            apo.apply_percent(self.path, percent)
        except apo.ConfigError as exc:
            raise BackendError(str(exc)) from exc

    def location(self) -> str:
        return str(self.path) if self.path else str(apo.expected_config_path())
