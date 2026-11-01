# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.1] - 2026-11-01

### Added

- Windows installer (`VolumeBoosterSetup.exe`, Inno Setup). It is per-user, so it
  never asks for administrator rights, and it ships a Start-menu entry and a
  clean uninstaller. The portable executable is still available and unchanged.
- `build-installer.ps1` for building the installer locally.

### Changed

- The app is now called **Volume Booster** and the repository is
  `volume-booster-pc`, so it reads as a volume booster for PC in search.
- Rounded controls are anti-aliased: pills, the toggle and the slider thumb are
  rendered from a 4x4 supersample grid instead of Tk's aliased primitives.
- Fonts use whole-pixel sizes, so glyphs sit on the pixel grid.

## [1.0.0] - 2026-10-31

### Added

- Continuous 0–500 % volume selector (up to 1000 % through settings), with exact
  numeric entry.
- Real engine verification: reads the Equalizer APO COM classes each audio
  endpoint uses, so "applied" is never confused with "installed".
- Isolated gain file (`volume-booster.txt`) referenced from Equalizer APO
  through a single `Include:` line. The previous app's block is removed, so two
  gains can never stack.
- Support bundle (`--diagnostics`): scrubbed report, engine state, recent log.
  No telemetry, no network.
- Nine languages with system-language detection: English, Español, Français,
  Deutsch, Italiano, Português (BR), Русский, 简体中文, 日本語.
- Opt-in start at login (per-user, no administrator needed) with confirmation.
- Settings file with `max_percent`, `confirm_above` and `restore_on_exit`.
- Single instance: launching again focuses the open window.
- Linux backend using `pactl` (PipeWire and PulseAudio).
- Portable Windows build with `SHA256SUMS.txt`, plus a CI matrix for lint,
  types and tests.

### Notes

- Windows needs Equalizer APO once (administrator + reboot). The application
  bundles no driver and never captures audio, so it adds no latency.
- The gain applies to the whole output endpoint, so speakers and headphones go
  through the same chain.
- macOS is not supported: it would need a virtual audio device, which adds
  latency.

[1.0.0]: https://github.com/LeGaliza85/volume-booster-pc/releases/tag/v1.0.0
