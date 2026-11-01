# BoostAudio

A focused, dark-themed volume control that pushes your system audio from **0 % to 500 %**
(up to 1000 % if you allow it), with a real verification that Windows is applying it.

- **Windows 10/11** — single portable `.exe`, no Python, no installer required.
- **Linux** — native, no extra component.
- **macOS** — not supported (needs a virtual audio device, which adds latency).

> BoostAudio raises the **whole output endpoint**, not just headphones: the gain sits
> before any `Device:` block. It keeps it in its own file (`boostaudio.txt`) so it can
> never stack with another app's block: two `Preamp` filters in the same chain would
> **add up**.

![BoostAudio](assets/screenshot.png)

## Why Windows warns you

The executable is **not code-signed**: a signing certificate costs ~200 €/year and
this project is free. Windows SmartScreen shows *"Windows protected your PC"* for
any new, unsigned binary — it is a reputation warning, not a virus detection.

To continue: **More info → Run anyway**.

If you prefer not to trust a binary, verify it or build it yourself:

```powershell
# 1. Compare the hash with SHA256SUMS.txt from the same release
Get-FileHash .\BoostAudio.exe -Algorithm SHA256

# 2. Or build from source (Python 3.11+)
powershell -ExecutionPolicy Bypass -File build.ps1
```

## Install (Windows)

1. Download `BoostAudio.exe` (or `BoostAudio-portable.zip`) from Releases.
2. Run it. The status bar tells you what is happening.
3. Equalizer APO is required for the boost above 100 %:

   1. Install [Equalizer APO](https://sourceforge.net/projects/equalizerapo/) and tick **only the device you want to boost**.
   2. Reboot.
   3. Sound settings → your device → **Enhancements**: leave *Disable all enhancements* **unticked**.
   4. Run the app again.

## Status states

| State | Meaning | What to do |
|---|---|---|
| `Applied: … · Equalizer APO` | Gain written and the APO is attached to at least one device | Nothing |
| `Equalizer APO is not attached to any device` | Installed, but no endpoint uses it | Re-run the installer and tick the device you want to boost |
| `The config was changed outside the app` | Someone else edited the gain file | Press Apply |
| `Boost engine not found` | Equalizer APO missing | Press Setup |

The check reads the COM classes Windows registers for each audio endpoint. It is
read-only, has no cost, and never plays audio.

## Settings

`%APPDATA%\BoostAudio\settings.json` is created on first run and can be
edited by hand:

| Key | Default | Range | Meaning |
|---|---|---|---|
| `max_percent` | `500` | 100–1000 | Slider ceiling |
| `confirm_above` | `300` | 0–1000 | Ask before jumping above this level; `0` disables the question |
| `restore_on_exit` | `false` | bool | Set the gain back to 100 % when the app closes |

Invalid values are ignored and clamped; a broken file never crashes the app.

## Languages

English, Español, Français, Deutsch, Italiano, Português (BR), Русский,
简体中文, 日本語. The app starts in your system language.

## Privacy

- No telemetry, no analytics, no network calls.
- Audio never leaves the machine: the app only writes one line to a text file.
- `--diagnostics` writes a support bundle to `%LOCALAPPDATA%\BoostAudio`.
  It contains version, OS, engine state and the recent log, with your user name
  and home path replaced by `<user>` / `<home>`.

## Command line

```
BoostAudio.exe            # the UI
BoostAudio.exe --version
BoostAudio.exe --health   # verification state as JSON
BoostAudio.exe --settings # effective settings and their path
BoostAudio.exe --diagnostics
```

## Build from source

```powershell
python -m pip install pyinstaller
powershell -ExecutionPolicy Bypass -File build.ps1
```

`build.ps1` regenerates the icon, builds the executable, creates the portable zip
and writes `dist\SHA256SUMS.txt`.

On Linux: `./build.sh`.

## Tests

```
python -m unittest test_configfile test_apo test_i18n test_platform test_settings test_diagnostics test_verify
python app.py --smoke
python app.py --smoke-ui
```

`test_apo` and the smoke tests are Windows-only and skip elsewhere.

## Platform support

| OS | Status | Engine |
| --- | --- | --- |
| Windows 10/11 | Full | Equalizer APO |
| Linux (PipeWire/PulseAudio) | Full | `pactl set-sink-volume` |
| macOS | Not supported | Would need a virtual audio device (adds latency) |

## Credits

Made by **LeGaliza85** — https://github.com/LeGaliza85

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 LeGaliza85.
