"""Equalizer APO config management for the Volume Amplifier app.

Windows clamps endpoint volume at 100 %. A signed APO (Equalizer APO) is what
actually applies digital gain above that ceiling. This module does not reimplement
any DSP: it owns exactly one marked block of Equalizer APO's config file.

Safety rules:
  * The rest of the user's config is never touched. The block is inserted at the
    top (so it applies to every APO-enabled device) and replaced in place later.
  * The original file is copied once to ``<config>.amplificador-voz.bak`` before
    the first modification.
  * Writes are atomic (temp file + os.replace) and preserve BOM and encoding.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import tempfile
import winreg
from pathlib import Path

import configfile
from gainmath import (
    clamp_percent,
    percent_to_db,
)

ENV_OVERRIDE = "AMPLIFICADOR_VOZ_APO_CONFIG"
_BACKUP_SUFFIX = ".amplificador-voz.bak"
_BOM = b"\xef\xbb\xbf"


class ConfigError(Exception):
    """The config file could not be read or written safely."""


class ConfigNotFoundError(ConfigError):
    """Equalizer APO's config file was not found."""


def read_config(path: Path) -> tuple[str, str, bool]:
    """Return (text, encoding, has_bom) without guessing away information."""
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ConfigError(f"Cannot read {path}: {exc}") from exc

    has_bom = raw.startswith(_BOM)
    if has_bom:
        raw = raw[len(_BOM) :]

    try:
        return raw.decode("utf-8"), "utf-8", has_bom
    except UnicodeDecodeError:
        pass
    try:
        return raw.decode("cp1252"), "cp1252", has_bom
    except UnicodeDecodeError as exc:
        raise ConfigError(f"{path} is not valid UTF-8 or CP1252 text.") from exc


def write_config(path: Path, text: str, encoding: str, has_bom: bool) -> None:
    data = (_BOM if has_bom else b"") + text.encode(encoding)
    tmp_name = ""
    handle = None
    try:
        fd, tmp_name = tempfile.mkstemp(
            dir=str(path.parent), prefix=".amplificador-voz-", suffix=".tmp"
        )
        handle = os.fdopen(fd, "wb")
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
        handle.close()
        handle = None
        os.replace(tmp_name, path)
    except OSError as exc:
        raise ConfigError(f"Cannot write {path}: {exc}") from exc
    finally:
        if handle is not None:
            handle.close()
        if tmp_name and os.path.exists(tmp_name):
            with contextlib.suppress(OSError):
                os.remove(tmp_name)


def backup_once(path: Path) -> Path:
    backup = path.with_name(path.name + _BACKUP_SUFFIX)
    if path.exists() and not backup.exists():
        try:
            shutil.copy2(path, backup)
        except OSError as exc:
            raise ConfigError(f"Cannot back up {path}: {exc}") from exc
    return backup


def apply_percent(path: Path, percent: object) -> int:
    """Write the gain into this app's own include file.

    ``config.txt`` only gains a single ``Include:`` line, and the block written by
    the previous app is removed, so exactly one gain source exists per device.
    """
    if not path.exists():
        raise ConfigNotFoundError(f"{path} does not exist. Is Equalizer APO installed?")
    if not path.parent.is_dir():
        raise ConfigNotFoundError(f"{path.parent} is not a directory.")

    value = clamp_percent(percent)
    text, encoding, has_bom = read_config(path)
    try:
        updated = configfile.prepare_config(text)
    except configfile.ConfigError as exc:
        raise ConfigError(str(exc)) from exc

    if updated != text:
        backup_once(path)
        write_config(path, updated, encoding, has_bom)

    write_config(
        configfile.include_path(path),
        configfile.render_gain(percent_to_db(value)),
        "utf-8",
        False,
    )
    return value


def include_path(path: Path) -> Path:
    return configfile.include_path(path)


def gain_text(path: Path) -> str:
    """Contents of this app's gain file, or an empty string when absent."""
    include = configfile.include_path(path)
    if not include.exists():
        return ""
    text, _encoding, _bom = read_config(include)
    return text


def find_config_path() -> Path | None:
    """Best-effort discovery of Equalizer APO's config.txt."""
    override = os.environ.get(ENV_OVERRIDE)
    if override:
        return Path(override)

    for variable in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)"):
        root = os.environ.get(variable)
        if not root:
            continue
        candidate = Path(root) / "EqualizerAPO" / "config" / "config.txt"
        if candidate.exists():
            return candidate

    return _registry_config_path()


def _registry_config_path() -> Path | None:
    flags = (winreg.KEY_READ | winreg.KEY_WOW64_64KEY, winreg.KEY_READ | winreg.KEY_WOW64_32KEY)
    for flag in flags:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\EqualizerAPO", 0, flag) as key:
                for name in ("ConfigPath", "InstallPath", "Install_Dir", "InstallPath64"):
                    try:
                        raw, _ = winreg.QueryValueEx(key, name)
                    except OSError:
                        continue
                    candidate = Path(str(raw))
                    if candidate.name.lower() == "config.txt" and candidate.exists():
                        return candidate
                    nested = candidate / "config" / "config.txt"
                    if nested.exists():
                        return nested
        except OSError:
            continue
    return None


def expected_config_path() -> Path:
    root = os.environ.get("ProgramFiles", r"C:\Program Files")
    return Path(root) / "EqualizerAPO" / "config" / "config.txt"
