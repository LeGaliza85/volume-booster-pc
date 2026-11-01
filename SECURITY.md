# Security policy

## Supported versions

| Version | Supported |
| --- | --- |
| 1.x | Yes |

## What this app does on your machine

- Writes one line to Equalizer APO's config directory (a file it names
  `volume-booster.txt`) and adds a single `Include:` line to `config.txt`.
- Optionally registers a per-user start-at-login entry
  (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run` or an XDG `.desktop`
  file). No administrator rights, no services, no drivers.
- Stores the last value and the settings under `%APPDATA%\VolumeBooster`
  (`~/.config/volume-booster-pc` on Linux).
- Sends nothing over the network by default. There is no telemetry and no
  analytics.

## Network access and the updater

Two opt-in switches control the only network activity in the app:

- `check_updates` asks `api.github.com` for the latest release tag of this
  repository. The request carries a user agent with the app name and version and
  nothing else — no identifiers, no counters, no usage data.
- `auto_update` additionally downloads `VolumeBoosterSetup.exe` and
  `SHA256SUMS-windows.txt` **from that same release**, and refuses to run the
  installer unless its SHA-256 matches the published checksum. A mismatch deletes
  the file and stops.

Both are off by default. What this means as a threat model, honestly:

- The checksum comes from the same origin as the installer, so it protects against
  a corrupted or truncated download, **not** against a compromised GitHub release.
  That is the same trust model as any unsigned updater.
- The installer runs silently, which means SmartScreen does not get a say: a file
  written by the app carries no Mark-of-the-Web. Treat a compromise of the release
  channel as equivalent to running arbitrary code.
- Automatic installation only happens for an installed build (the one with
  `unins000.exe` next to it). The portable `.exe` is never replaced.
- A version that failed to install once is recorded and not retried in a loop.

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
