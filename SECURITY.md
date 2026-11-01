# Security policy

## Supported versions

| Version | Supported |
| --- | --- |
| 1.x | Yes |

## What this app does on your machine

- Writes one line to Equalizer APO's config directory (a file it names
  `boostaudio.txt`) and adds a single `Include:` line to `config.txt`.
- Optionally registers a per-user start-at-login entry
  (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run` or an XDG `.desktop`
  file). No administrator rights, no services, no drivers.
- Stores the last value and the settings under `%APPDATA%\BoostAudio`
  (`~/.config/boostaudio` on Linux).
- Sends nothing over the network. There is no telemetry, no updater and no
  analytics.

## Reporting a vulnerability

Open a private security advisory on GitHub (Security → Advisories) or email the
maintainer listed in the repository profile. Please do not open a public issue
for a vulnerability.

Include the version reported by `--version`, your OS, and the steps to
reproduce. **Do not attach** the support bundle if you suspect it contains
anything sensitive; the bundle is scrubbed of user names and home paths, but you
can inspect the zip yourself before sending it.

## Downloads

Releases are unsigned. Verify the file against `SHA256SUMS*.txt` published next
to it, or build from source with `build.ps1` / `build.sh`.
