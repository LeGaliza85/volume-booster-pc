# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.5.8] - 2026-11-01

### Fixed

- **The maximum boost could not be saved.** The Limits field only committed on
  Enter or FocusOut, and FocusOut does not fire when the settings window is
  destroyed, so typing 1000 and closing lost the value. It now has an **Apply**
  button next to the field, and closing the window commits whatever is in it.

## [1.5.7] - 2026-11-01

### Fixed

- **The app came back as `Failed to load Python DLL` after an automatic update.**
  The installed copy was a one-file build, so every start unpacked itself into
  `%TEMP%\`; doing that while an update replaced files is what broke it.
  The installer now ships a **folder build** (`dist\VolumeBooster\`), which
  starts without unpacking anything. The portable download is still a single
  `.exe`.
- Killing the app left its whole unpack folder behind: I found 193 MB of them. The
  folder build makes that impossible.

## [1.5.6] - 2026-11-01

### Fixed

- **The 1000 % range did not exist.** `gainmath.MAX_PERCENT` capped every value
  at 500, so neither the slider nor `settings.json` could go past it, while the
  README and the settings table both promised 1000 %. The limit now allows 1000 %.
- The invalid-value message hardcoded 500; it now uses the configured ceiling.

### Added

- **Settings -> Limits**: the slider ceiling is editable (100-1000 %) without
  touching JSON, and the slider updates in place when it changes.

## [1.5.5] - 2026-11-01

### Fixed

- **The app still did not come back after an automatic update.** The installer was
  started with `DETACHED_PROCESS`; with that flag Inno finishes the install but
  never runs its `[Run]` entry, so the relaunch silently never happened. A plain
  child process is enough, and Windows keeps it alive after the app exits.

## [1.5.4] - 2026-11-01

### Added

- The settings window now shows the running version under its title, which is the
  only way to tell which build an automatic update actually landed on.

### Fixed

- The downloaded installer was left in %TEMP% after every update (14 MB). The next
  start removes it.

## [1.5.3] - 2026-11-01

### Fixed

- **The app did not come back after an automatic update.** The detached batch that
  waited for the installer raced with Inno re-executing itself: sometimes it
  relaunched too early (`Failed to load Python DLL`), sometimes it never relaunched
  at all and left the batch and the 14 MB installer behind.
- The batch is gone. The installer now runs the app from its own `[Run]` entry, so
  the restart happens exactly when Inno knows the files are written. `updater.py`
  shrank to "is this an installed build" plus "start the installer silently".

## [1.5.2] - 2026-11-01

### Fixed

- **The app failed to restart right after an automatic update**, showing
  `Failed to load Python DLL`. `start /wait` returns as soon as the setup parent
  exits, and Inno Setup can re-exec itself, so the app was launched while files
  were still being written. The updater now waits for the setup process to
  disappear before starting the app again.

## [1.5.1] - 2026-11-01

### Fixed

- `SECURITY.md` claimed "there is no telemetry, no updater and no analytics" after
  1.5.0 added one. It now documents the two network switches, what the request
  carries, and the honest threat model: the checksum protects against a corrupted
  download, not against a compromised release, and a silently installed file has no
  Mark-of-the-Web for SmartScreen to judge.
- `CONTRIBUTING.md` said "no network, no auto-updater"; the rule is now "no
  telemetry, and network access only where it is declared" — `update.py` and
  nowhere else.
- The detached updater deletes the downloaded installer as well as itself, so a
  successful update leaves no 14 MB file in `%TEMP%`.

## [1.5.0] - 2026-11-01

### Added

- **Automatic updates**, opt-in. With *Download and install updates automatically*
  on, the app checks at startup, downloads `VolumeBoosterSetup.exe` and its
  `SHA256SUMS-windows.txt` from the same release, verifies the hash, hands the
  installer to Windows, waits while it installs silently and starts again.
- Three rails: it only self-installs from an **installed** copy (the portable
  `.exe` is never replaced behind your back), a version that failed once is not
  retried in a loop, and nothing is executed when the hash does not match.

### Changed

- `check_updates` now only decides whether to look; the new `auto_update` decides
  whether to install. Both are off by default.

## [1.4.2] - 2026-11-01

### Fixed

- **The Device Selector no longer fails with "no Qt platform plugin could be
  initialized".** Equalizer APO's Qt tools keep their plugins in `qt/platforms`
  and ship no `qt.conf`, so they only find them when the process starts inside
  their own folder. `os.startfile` inherited our working directory. The
  Configurator is now started with its folder as the working directory, the same
  way the Start-menu shortcut does it, and a test pins that argument.

## [1.4.1] - 2026-11-01

### Fixed

- **Change device sent you to the download page.** Equalizer APO 1.4 ships the
  device picker as `DeviceSelector.exe`; the app only looked for `Configurator.exe`,
  did not find it, and fell back to opening the download page for a program that was
  already installed. It now looks for DeviceSelector first, and when none is found
  it says so instead of pretending.
- **"Disable all enhancements" is no longer guesswork.** Windows stores it per
  endpoint as `PKEY_AudioEndpoint_Disable_SysFx`, so the app can tell when a device
  is blocked. The row appears only while it is actually disabled, names the device,
  and disappears on its own once the box is unticked — nothing to mark as done.

## [1.4.0] - 2026-11-01

### Changed

- The settings window only lists what needs attention. A missing Equalizer APO is
  one red row with a **Download** button; once installed, the row disappears. The
  attached-device row offers **Change** when everything is fine, and the reboot
  hint only appears while the APO is not attached yet.
- The Enhancements row now says exactly what the button does and which clicks
  follow, since Windows cannot open a single device's properties page directly.
- Hotkey capture grabs the keyboard while it waits, so the combination always
  lands on the field, and the hint explains how to edit them.

### Added

- **Check for updates** link in the window and an **Updates** section in settings.
  The automatic check is off by default; the manual one is the only network call
  the app makes, and it sends nothing about the user.

## [1.3.1] - 2026-11-01

### Fixed

- The preview tone produced no sound at all: winsound refuses `SND_MEMORY` together
  with `SND_ASYNC` (it raises `Cannot play asynchronously from memory`) and the
  error was swallowed. The tone now goes through a small file played
  asynchronously, alternating two names so the write never touches the file being
  played.
- Every toggle in Settings did nothing: `ToggleSwitch` reported the new value but
  never updated its own, so it looked frozen and repeated clicks sent the same
  state. The widget now flips itself before calling back, and callers that refuse
  a change still call `set_state` to put it back. This also fixes the checkbox in
  the loud-level warning.

## [1.3.0] - 2026-11-01

### Added

- **Preview tone**: a short Test button next to Apply plays a tone through the
  current chain, and moving the slider plays one at the level you are pointing to.
  The tone is generated in memory with fades at both ends and its amplitude is
  clamped, so it can never clip. preview_sound turns it off.
- **Don't ask again** in the loud-level warning, which is now a small themed window
  instead of a message box. It sets confirm_above to 0; Settings -> Sound can
  turn the warning back on.

### Changed

- The loud-level warning no longer uses a native message box, so it can carry the
  checkbox and match the app's theme.

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
