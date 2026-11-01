# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.2.2] - 2026-11-01

### Fixed

- The notification-area icon is put back when Explorer restarts. Windows drops
  every icon in that case, and a hidden app with no icon has no way back.
- The tray message pump can no longer stop itself: a failure is logged and the
  loop keeps running, instead of the icon going deaf for the rest of the session.

### Added

- `crash.log` records a native crash with its Python stack (faulthandler), and
  `--diagnostics` includes it. A failed Win32 call can kill the process without
  raising anything Python can catch, which used to leave no evidence at all.

## [1.2.1] - 2026-11-01

### Added

- Feedback when a hotkey changes the level while the window is hidden: the tray
  tooltip always shows the current percentage, and one notification reports the
  final value after a burst of presses (debounced, so ten presses are one toast).
- README: the "Which devices get boosted?" section, explaining that device
  selection belongs to Equalizer APO's Configurator — and why per-device gain
  profiles are intentionally not implemented.

### Note

Per-device gain profiles were considered and rejected: a `Device:` rule that does
not match is applied silently, so the feature could claim success while doing
nothing on that device.

## [1.2.0] - 2026-11-01

### Added

- **Notification-area icon**: the app no longer takes a taskbar slot. Left-click
  opens the window, right-click offers Open, Settings, Report a bug and Quit.
  Closing the window hides it instead of quitting, and the first run still shows
  the window once so the icon is not a mystery.
- **Global hotkeys**: `Ctrl+Alt+Up` and `Ctrl+Alt+Down` raise and lower the boost
  by ten percent, and they work while the window is hidden.
- **A real Settings window**: the four Windows requirements with their state and a
  button that opens the exact place to fix them (APO download, Configurator, sound
  settings), plus hotkey capture and startup options.
- `start_hidden`, `close_to_tray`, `hotkey_up` and `hotkey_down` settings; hotkeys
  are validated on load and an invalid one falls back to the default.

### Fixed

- The tray is optional: if Windows refuses the icon, the window is shown instead of
  leaving the app invisible.

## [1.1.0] - 2026-11-01

### Added

- **Report a bug** link in the window, and a `--report` flag that prints the same
  URL. It opens the GitHub issue form with the app version and the operating
  system already filled in, so the report arrives complete instead of asking the
  reporter to look things up.
- A troubleshooting section in the README explaining what makes a report useful
  (`--diagnostics`, the status bar text, the Equalizer APO state).

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
