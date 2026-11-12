# Equalizer plan — Volume Booster PC

Status: proposal. This document changes no production code.
Date: 2026-11-12
Product: Volume Booster PC (`volume-booster-pc`), MIT, Windows 10/11 + Linux.
Team: orchestrator (lead), DSP/audio engineer, Windows integration engineer,
product/UX + QA/legal.
Inputs: repository exploration with `path:line` evidence; Equalizer APO 1.4.2
configuration reference; Peace; EasyEffects; AutoEq; FxSound; Boom 3D;
CamillaDSP; the user's product decisions (linear percentage slider, verified
boost, no telemetry, English artifacts except the Spanish landing page).

---

## 1. Executive summary

Build a **Windows-first equalizer on top of Equalizer APO**, rendered into a
second app-owned include file, as a companion to the existing verified volume
boost. Do not build a DSP engine, a driver, or a virtual audio device.

Recommended first release (P0):

- A 10-band graphic equalizer (ISO centres, independent peaking filters).
- Automatic headroom so positive EQ cannot clip on its own.
- One active preset, four built-ins, save/rename/delete, native JSON.
- Import of AutoEQ `ParametricEQ.txt` with attribution.
- A/B bypass that never touches the volume boost.
- Windows only; Linux keeps the boost and shows "EQ not available".

Later releases add a full parametric editor, per-device profiles keyed by exact
endpoint GUID, an online AutoEQ catalog, REW import, and a guided measurement
wizard. True compression, limiting, dynamic EQ, per-app EQ, 3D processing and a
custom driver are explicitly out of scope: stock Equalizer APO cannot do them,
and faking them would break the product's "verified" promise.

Effort for one maintainer: roughly 9-12 weeks across four phases; P0 alone is a
4-6 week slice including translation and release hardening.

Why this shape:

- Equalizer APO is already installed, verified per endpoint and used by the
  boost. It is the only option that needs no new runtime dependency.
- The proven market model is a GUI/config layer over EQ APO (Peace). The gap is
  a simpler, safer, Spanish-first booster that also shapes tone.
- AutoEQ is the automation users expect; importing its text output is legal,
  offline and deterministic, while bundling its measurement database is not.
- The app already resolves the default endpoint and checks APO attachment
  (`verify.py`), so "the curve applies to the device that is playing" can be a
  real promise instead of a guess.

---

## 2. Non-goals (P0)

- Linux equalization. `backend_linux.py` only calls `pactl`; a real Linux EQ
  needs PipeWire filter-chain/EasyEffects integration, which is a separate
  engine.
- Per-app EQ. Windows APOs process endpoints, not applications.
- Compression, limiting, dynamic EQ, loudness linked to system volume, 3D
  surround, virtual devices, convolution/IR, per-channel EQ, 31 bands.
- Bundling Equalizer APO binaries, AutoEQ measurements, or third-party presets
  without a licence review.
- Changing the volume-boost slider scale: it stays linear in percentage
  (0 % left, 50 % = 500 %, ceiling right), as decided.

---

## 3. Competitive analysis

| Product | Licence / price | Engine / platform | Strengths | Weaknesses | What to borrow / avoid |
|---|---|---|---|---|---|
| Equalizer APO | GPL, free | Windows system APO | De-facto Windows engine; Preamp, PK/PEQ, shelves, HP/LP/BP/notch/AP, GraphicEQ, convolution, delay, channel routing, Device blocks, expressions | No GUI; config syntax is power-user only | Use as the only DSP engine; write its config; never bundle it |
| Peace | GPLv2, free | AutoIt GUI over EQ APO | Up to 31 bands/channel, per-slider Fc/Gain/Q, graph, AutoEQ interface, presets, per-device profiles, tray/hotkeys/MIDI, 15 languages, themes; 4.9/5 and ~46k downloads/week | Complex for a casual user; Windows only; AutoIt | Borrow the feature set and the AutoEQ idea; do not clone the breadth in P0 |
| EasyEffects | GPLv3, free | Linux PipeWire | Reorderable effect chain, EQ, convolver, limiter, compressor, autogain, loudness, community presets | Linux only; not portable to Windows | Borrow the chain/preset vocabulary; use as the Linux reference |
| AutoEq | MIT (code) | Python + web | Headphone measurements, target curves, parametric optimizer with shelves, CSV/txt results, web app | Does not apply EQ; measurement sources have their own terms | Import its text output; do not bundle measurements without review |
| FxSound | Free, open source since 2023 | Windows | EQ, effects, presets, volume/bass boost, voice clarity; consumer-simple | Effect-stack approach, not a precise EQ | Borrow the one-click preset UX; avoid the effects pile |
| Boom 3D | Paid | Windows/macOS | 3D surround + EQ, consumer polish | Paid; 3D/effects focus | Reference for consumer presentation only; do not compete on 3D |
| CamillaDSP | GPLv3 / MPL2 | Rust, cross-platform, YAML + websocket | IIR/FIR, limiter, loudness, compressor, REW import, high-end routing | Needs a virtual loopback on Windows; separate process; CLI/YAML | Reference for future DSP features; not the P0 engine |

Lessons:

1. The market has split into simple consumer enhancers (FxSound), professional
   APO front-ends (Peace), and full DSP engines (CamillaDSP/EasyEffects).
2. The open gap is a **boost-first, verified, safe equalizer**: the volume boost
   stays the primary job; the EQ is subordinate and cannot silently break it.
3. AutoEQ import is the highest-value automatic feature and the cheapest to
   ship correctly.
4. Real room correction needs a calibrated measurement chain. An uncalibrated
   phone or laptop mic can support a guided 20-300 Hz correction at most.
5. Per-device profiles are expected by power users but are dangerous when
   matched by name; the only acceptable key is the endpoint GUID, verified.

---

## 4. Architecture

### 4.1 Layers

```
Equalizer APO (only DSP engine)
        ^
        | config files (data, not code)
        |
configfile.py / apo.py  <- equalizer.py (model -> APO lines)
        ^
        | presets.json / equalizer.json
        |
presets.py  <- eqwindow.py (Toplevel) + eqwidgets.py (graph, vertical sliders)
        ^
        |
app.py (main window strip: EQ on/off, preset name, Edit)
        |
verify.py (endpoint attachment + health)
```

### 4.2 Files the app owns

- `config.txt`: exactly two lines owned by the app:
  `Include: volume-booster.txt` and `Include: volume-booster-eq.txt`. The rest
  of the user's config is untouched.
- `volume-booster.txt`: the volume boost, one `Preamp` line. Its first line
  remains the boost contract used by `verify.preamp_db()` and
  `diagnostics.text_block()`.
- `volume-booster-eq.txt`: the EQ chain: an optional headroom `Preamp`, an
  optional `Device:` block, the filter lines, then `Device: all` and
  `Channel: all`.
- `presets.json`: user and built-in presets.
- `equalizer.json`: active preset id, enabled/bypass, device profile selection.

Two includes instead of one are deliberate:

- The first-Preamp invariant survives: `verify.py` and `diagnostics.py` keep
  reading the boost from `volume-booster.txt`.
- An older build (or a user with the previous version) rewrites only its own
  include and never deletes the EQ.
- The Equalizer APO Editor owns `config.txt`; our filters live in a file it does
  not edit, so a save from the Editor cannot erase the curve.

### 4.3 Generated chain (example)

```
# volume-booster.txt
Preamp: 13.98 dB

# volume-booster-eq.txt
Preamp: -4.50 dB
Device: {2b2e13fa-4964-4d96-a6c6-359b022b53c5}
Filter 1: ON PK Fc 31.5 Hz Gain 3.0 dB Q 1.41
Filter 2: ON PK Fc 63 Hz Gain 1.5 dB Q 1.41
Filter 3: ON PK Fc 125 Hz Gain 0.0 dB Q 1.41
...
Filter 10: ON PK Fc 16000 Hz Gain -2.0 dB Q 1.41
Device: all
Channel: all
```

`Preamp` lines are additive per channel. The boost Preamp and the EQ headroom
sum; the app must show the total (boost dB + headroom dB) in the UI.

### 4.4 Renderer rules

- One pure function: model -> text. No partial patching, no line merging.
- Whitelist of commands and filter types; unknown types are rejected before
  writing because Equalizer APO silently ignores unknown lines.
- Stable formatting and ordering; byte-identical output for the same model.
- Atomic write (temp + `os.replace`, reuse `apo.write_config`); preserve BOM and
  encoding of `config.txt`; the include is UTF-8 without BOM.
- Debounce edits 150-300 ms so APO reloads do not stutter.
- Bypass means "EQ bypass": omit filters and headroom, keep the boost; A/B is
  level-matched or true-bypass, labelled as such.
- If the model is invalid, refuse to write and keep the previous file; show the
  error. Never leave a half-written chain.

### 4.5 Device scoping

- `Device:` is stateful. A non-matching pattern makes the following commands be
  ignored, so every generated file ends with `Device: all` and `Channel: all`.
- Per-device profiles use the exact endpoint GUID (lowercase), never a friendly
  name. Name is display-only.
- If the selected GUID is not present, do not write a Device block: apply
  globally and warn. A profile is never applied by name in silence.
- P0 is global EQ for all devices; profiles are P1.

### 4.6 Automatic headroom

The EQ is static IIR; it has no limiter. To avoid EQ-induced clipping:

- Evaluate the cascade magnitude `20*log10|H(f)|` on ~2048 log-spaced points
  from 20 Hz to `0.45 * sample_rate`, across 44.1/48/96/192 kHz worst case.
- Take the maximum; add 0.1 dB margin; write a negative `Preamp` (clamp
  -40..0 dB).
- Use the composite response, not the sum of band gains: overlapping bands can
  exceed any individual gain.
- Cuts only produce 0 dB headroom.
- Show "EQ headroom -X dB · Boost +Y dB · Total +Z dB"; warn above +6 dB total
  and reuse the existing loud confirmation.

This prevents EQ-induced clipping. It cannot prevent clipping from the volume
boost itself or from a source already at full scale; the app must say so.

---

## 5. Feature catalogue

### P0 — first shippable equalizer

| Feature | Acceptance |
|---|---|
| 10-band graphic EQ, ISO centres (31.5, 63, 125, 250, 500, 1k, 2k, 4k, 8k, 16k Hz) | Independent `PK` filters (Q 1.41) so moving one band does not reshape its neighbours; 1 dB steps, +/-12 dB |
| Draggable graph + vertical sliders | Both edit the same model; double-click resets a band; keyboard arrows adjust 1 dB |
| Automatic headroom | Composite response; visible headroom and total gain; no positive EQ without visible headroom |
| A/B bypass | EQ only; boost unaffected; toggling twice restores the exact previous bytes |
| Presets | Flat, Speech clarity, Bass, Warm; save/save as/rename/delete; unique case-insensitive names; built-ins read-only |
| Native JSON round-trip | Export -> import equals the original; schema version enforced |
| AutoEQ import | Parse `ParametricEQ.txt` (Preamp + PK/LSC/HSC); approximate to the 10-band editor; show "approximated from N filters"; keep source/licence metadata |
| Platform state | Windows: full; Linux: "EQ not available", boost unchanged |
| Health/status | EQ applied / bypassed / unavailable / APO detached / drift; no silent success |
| Tests | Golden strings, headroom, round-trip, idempotency, failure injection, i18n parity |

### P1 — professional controls

- Full parametric editor: PK, LSC/HSC, HP/LP, notch; Fc/Gain/Q; up to 20 bands.
- Per-device profiles by exact GUID, opt-in, verified; fallback to global.
- Online AutoEQ catalog with per-source attribution and licence metadata (opt-in
  network call; the app's no-telemetry rule still holds).
- Import REW filter text and APO config subsets; export an APO-compatible
  snippet.
- Undo/redo; preset duplication; Settings section for EQ defaults.
- Level-matched A/B and a "show total gain" graph overlay.

### P2 — advanced

- Guided measurement: import a measurement or use an uncalibrated mic for a
  20-300 Hz correction, with a clear "not a calibrated SPL measurement" label.
- Per-channel EQ (L/R), 31-band mode, convolution/IR with sample-rate matching.
- Static loudness presets (not dynamic; EQ APO cannot see system volume).
- Peace preset import (clean-room, only if the format is documented).
- Linux: PipeWire filter-chain or EasyEffects integration research.

### Explicitly not

Compressor, limiter, dynamic EQ, per-app EQ, 3D/surround, virtual audio device,
custom APO/driver, cloud presets, marketplace, telemetry.

---

## 6. UX

### 6.1 Entry point

The main window stays a volume booster. Add one compact strip above the footer:
`EQ: Flat  [Edit]` with an on/off switch. The boost slider, Apply and Test stay
one click away. Do not put the EQ inside the existing Settings Toplevel: it is
fixed, non-scrollable, and a graph does not fit (`settingswindow.py:28-41`,
`54-103`).

### 6.2 Equalizer window

A separate Toplevel, fixed layout:

1. Header: preset selector, A/B, Save.
2. Scope banner: "Applying to: <device> · Equalizer APO verified" or a warning
   if detached/unknown.
3. Graph: log frequency 20 Hz-20 kHz, +/-12 dB (P0), draggable nodes.
4. Ten vertical sliders under the graph, with numeric readout.
5. Footer: headroom, boost, total gain, Reset, Close.

First open shows one small sheet: "Boost changes level; EQ changes tone;
headroom protects against clipping", with Start flat / Load preset / Import.
Never block the boost.

### 6.3 Manual flow

Open EQ -> choose Flat -> drag a band or type a gain -> headroom updates -> A/B
-> Save or Close. Applying on release is fine; no per-pixel writes. Every
control is reachable without dragging (tab order, arrows, numeric entry).
Tk's screen-reader support is limited; document it rather than promise it.

### 6.4 Automatic flow

Import AutoEQ txt -> preview graph -> apply approximated 10-band preset -> show
source and licence. No network in P0. Four built-ins are original presets, not
measurements.

### 6.5 Presets and profiles

One active preset, dirty marker, Save/Save as, duplicate/rename/delete, unique
case-insensitive names, built-ins read-only. Export native JSON for fidelity and
an APO `.txt` snippet for sharing. Reject imports containing `Device:`,
`Include:` or `Convolution:` with a reason. Device association is P1 and
verified by GUID.

### 6.6 Errors and i18n

Reuse the existing status dot vocabulary. EQ-specific messages: engine missing,
detached, enhancements off, import parse error with line number, unsupported
schema, "EQ not available on Linux". Every new key goes into all nine locale
tables; `test_i18n.py` enforces parity (`i18n.py:28-641`). Batch strings and
freeze them per phase.

---

## 7. Data model

### 7.1 Active state (`equalizer.json`)

```json
{
  "schema_version": 1,
  "enabled": true,
  "bypass": false,
  "preset_id": "flat",
  "bands": [
    {"id": "b1", "type": "PK", "fc_hz": 31.5, "gain_db": 0.0, "q": 1.41, "enabled": true}
  ],
  "preamp": {"mode": "auto", "manual_db": 0.0},
  "device": {"kind": "all", "guid": ""},
  "source": {"kind": "manual", "model": "", "target": "", "license": ""}
}
```

### 7.2 Preset store (`presets.json`)

```json
{
  "schema_version": 1,
  "presets": [
    {"id": "flat", "name": "Flat", "kind": "builtin", "bands": [], "preamp": {"mode": "auto"}}
  ]
}
```

### 7.3 Profiles (P1)

```json
{
  "schema_version": 1,
  "profiles": [
    {"device_guid": "{2b2e13fa-4964-4d96-a6c6-359b022b53c5}", "device_name": "Altavoces", "preset_id": "flat"}
  ]
}
```

### 7.4 Validation

- `fc_hz` 10-24000 (UI 20-20000, below Nyquist check at render); `gain_db`
  +/-24; `q` 0.1-20 for PK, 0.1-4 for shelves, 0.1-2 for HP/LP; 1-30 for notch.
- 10 bands in P0, hard cap 20. Graphic points 1-64, strictly increasing.
- `manual_db` -40..0. Preset payload max 64 KB.
- Reject NaN/Inf, bool-as-int, duplicate ids, unknown types/keys, schema newer
  than the app. Fail closed: keep the previous preset; only safety fields clamp.
- UTF-8 without BOM, 2-space JSON, atomic replace, stable ordering.
- Device profiles store the exact lowercase GUID; names are display-only.

Storage lives next to `settings.json` under `%LOCALAPPDATA%\VolumeBooster`
(`diagnostics.app_data_dir()`), not in `state.json` (only percent+language,
`app.py:78-97`) and not in `settings.json` (flat whitelist that drops unknown
keys, `settings.py:38-74`).

---

## 8. Integration with the current codebase

| File | Change |
|---|---|
| `equalizer.py` (new) | Model, validation, biquad math, composite response, headroom, renderer |
| `presets.py` (new) | Store, load/save, migration, import/export |
| `eqwindow.py` (new) | Equalizer Toplevel |
| `eqwidgets.py` (new) | Graph canvas, vertical band slider, preset list |
| `configfile.py` | `render_chain()`; EQ include name/line; keep `render_gain()` as a special case |
| `apo.py` | `apply_eq()` / single chain writer; preserve `apply_percent` for the boost; reuse atomic write and backups |
| `backend_windows.py` | Expose EQ apply; keep `apply_percent` for the slider |
| `backend_linux.py` | EQ unavailable; boost unchanged |
| `app.py` | EQ strip; pass EQ state to the engine; main status; open EQ window; `_rebuild` recreates the Toplevel |
| `verify.py` | EQ health: rendered filter count/headroom; device scope; first-Preamp invariant |
| `diagnostics.py` | Keep parsing the boost from `volume-booster.txt`; add EQ file facts to the report |
| `settingswindow.py` | EQ defaults section (P1); no graph |
| `i18n.py` | ~40-60 keys x 9 locales; parity test |
| Tests | `test_equalizer.py`, `test_presets.py`, `test_apo.py`/`test_configfile.py` extensions, `--smoke-ui` |
| CI / docs | Add test modules to `ci.yml:33-37`, `CONTRIBUTING.md:18`, `README.md:343`; README feature/settings sections; CHANGELOG |
| Packaging | New modules are collected automatically by `VolumeBooster.spec`; no new data assets in P0 |
| `pyproject.toml` | Add new modules to the mypy `files` list |

Migration:

- Phase 0 freezes the current format and adds the EQ include line idempotently.
- A one-time migration writes `volume-booster-eq.txt` empty and adds the second
  `Include:`; backup before touching `config.txt`.
- Rollback: remove the EQ include line and restore the backup; the boost include
  is untouched.
- The old build never deletes the EQ include because it only rewrites its own
  include and manages its own `Include:` line.
- If the Equalizer APO Editor is running, do not rewrite `config.txt`
  automatically; warn and retry after it closes.

---

## 9. Verification and acceptance

Automated:

- Golden config strings: boost-only output stays byte-identical to today; 1 PK,
  10 bands, shelf, notch, bypass, device block.
- First-Preamp invariant: `verify.preamp_db()` and
  `diagnostics.text_block()` still return the boost; health ok/drift unchanged.
- Headroom: +6 dB PK -> about -6.0 dB; two overlapping +6 dB bands -> about
  -12 dB; cuts only -> 0; composite maximum <= 0.1 dB across 44.1/48/96 kHz.
- Round-trip: model -> render -> constrained parser -> model within 0.01 dB /
  0.1 Hz.
- Idempotency: render twice byte-identical; apply twice byte-identical; exactly
  one EQ include; user filters untouched.
- Failure injection: read-only files/dirs, missing APO, unbalanced markers,
  unknown GUID, unsupported type, oversized preset: no partial writes, previous
  config preserved.
- Performance: 20-band render under 10 ms; debounce 150-300 ms.
- i18n: all keys present and placeholders identical in nine locales.
- Smoke: `--smoke` and `--smoke-ui` extended to apply an EQ preset, toggle
  bypass, change max and verify the chain.

Manual QA matrix:

- Windows 10 21H2/22H2 and Windows 11 22H2/23H2/24H2.
- Outputs: onboard analog, USB DAC, HDMI/DisplayPort, Bluetooth A2DP/LE,
  USB-C dock; virtual devices reported as unknown, not as failure.
- Formats: 44.1/48/96/192 kHz, 16/24-bit, mono/stereo/5.1/7.1, exclusive mode,
  spatial audio.
- Coexistence: Realtek/Dolby/Nahimic/SteelSeries APOs; enhancements on/off;
  Equalizer APO Editor open; AV/PyInstaller; UAC for the device selector.
- Recovery: APO detached after a driver/Windows update; new endpoint without
  APO; corrupt preset; read-only config.

---

## 10. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Clipping or hearing/equipment damage from boost + positive EQ | High | Composite auto headroom, visible total gain, warning above +6 dB, reuse loud confirmation, never claim a limiter |
| `Device:`/`Channel:` state leaks into the user's config | High | Exact GUID, `Device: all` and `Channel: all` terminators, tests with user content after the includes |
| Health/verification regression | Medium | Two includes, first-Preamp invariant, golden tests, smoke |
| Equalizer APO silently ignores unknown lines | Medium | Whitelist, read-back, health check for rendered filter count, fail closed |
| AutoEQ measurement licensing | Medium | Import-first, store source/licence metadata, no bundle without review |
| Program Files ACL / UAC | Medium | Installer ACL, atomic writes, backups, one-shot elevation for the device selector |
| Editor or other APO tools overwrite config | Medium | Own include files, two Include lines, detect Editor and warn |
| Linux users expect EQ | Medium | Label Windows-only in P0, keep boost, document the PipeWire path |
| Scope creep into a Peace clone | High | Fixed P0 non-goals, 10 bands, phase gates |

---

## 11. Legal and licensing

- **Equalizer APO**: GPL. The app writes its configuration file; it does not
  link or redistribute the APO. Do not bundle APO binaries without full GPL
  compliance. Keep the user-installed link and a third-party notice.
- **AutoEQ**: code MIT, but measurements come from oratory1990, crinacle,
  Rtings, Innerfidelity and others with their own terms. P0 imports user files
  or links out; do not bundle measurements. If a curated catalog is added, show
  source, licence and attribution, and have the data reviewed.
- **Peace**: GPLv2. Clean-room format compatibility only in P2; no code copying;
  do not use the name in the product name.
- **Reverse engineering**: documented config formats, AutoEQ txt/CSV and
  observable behaviour are in scope. Proprietary binary decompilation and DRM
  bypass are out.
- **Naming**: keep "Volume Booster PC"; say "works with Equalizer APO"; credit
  AutoEq and the measurement source. Do not imply endorsement.
- **Safety**: keep the hearing/equipment warnings; add a first-run EQ warning
  and state that EQ can raise levels and clip. Add `THIRD_PARTY_NOTICES`.

---

## 12. Roadmap

### Phase 0 — specification and spikes (1-2 weeks)

- Approve this plan and freeze the P0 scope.
- Write JSON schemas and validation rules.
- Implement the AutoEQ/APO text parser and golden fixtures.
- Spike the graph canvas and biquad magnitude math in pure Python.
- List the i18n keys; freeze the P0 strings.
- Decide the open questions below.

Exit: schemas, parser fixtures, graph spike and a signed-off P0 list.

### Phase 1 — P0 engine and editor (3-4 weeks)

- `equalizer.py`, `presets.py`, `eqwindow.py`, `eqwidgets.py`.
- 10-band editor, auto headroom, bypass, four built-ins, AutoEQ import.
- Windows-only state, health, i18n, tests, README/CHANGELOG.
- Release 1.6.0 (or the next agreed version).

Exit: P0 acceptance matrix green on Windows 10/11; Linux boost unchanged.

### Phase 2 — professional controls (3-4 weeks)

- Parametric editor, per-device profiles by GUID, online AutoEQ catalog, REW
  import, undo, Settings section.

Exit: profile switching verified against real endpoints; no name-only writes.

### Phase 3 — advanced and platform (2 weeks)

- Measurement wizard (if approved), per-channel EQ, 31-band, convolution
  research, Linux PipeWire/EasyEffects research, release hardening.

Exit: documented decision on each advanced item; no unfinished UI shipped.

---

## 13. Open decisions

1. P0 scope: 10-band graphic only (recommended) or parametric from day one?
2. AutoEQ: import-only (recommended until a licence review) or curated bundle?
3. Per-device profiles: P1 with exact GUID (recommended) or keep global?
4. Measurement wizard: keep the zero-capture promise (recommended) or allow an
   opt-in uncalibrated 20-300 Hz guide in P2?
5. Separate EQUALIZER window (recommended) or embed a graph in Settings?
6. Built-in presets: Flat, Speech clarity, Bass, Warm (recommended); any other?
7. Release cadence: ship P0 as its own release or wait for P1?

---

## Appendix — sources

- Equalizer APO configuration reference:
  https://sourceforge.net/p/equalizerapo/wiki/Configuration%20reference/
- Peace: https://sourceforge.net/projects/peace-equalizer-apo-extension/
- EasyEffects: https://github.com/wwmm/easyeffects
- AutoEq: https://github.com/jaakkopasanen/AutoEq
- FxSound: https://www.fxsound.com/
- Boom 3D: https://www.globaldelight.com/boom3d
- CamillaDSP: https://github.com/HEnquist/camilladsp
- Repo evidence: `settings.py:15-35`, `settings.py:38-74`, `settingswindow.py:28-41`,
  `settingswindow.py:54-103`, `app.py:78-97`, `app.py:262-270`,
  `app.py:771-825`, `apo.py:99-127`, `configfile.py:19-27`,
  `configfile.py:84-90`, `verify.py:38-57`, `verify.py:113-164`,
  `diagnostics.py:28`, `diagnostics.py:100`, `widgets.py:252-367`,
  `i18n.py:28-641`, `.github/workflows/ci.yml:33-37`, `README.md:258-272`,
  `README.md:343`.

No proprietary binary was reverse engineered for this plan. Formats and
observable behaviour were analysed; the only binary inspection was the embedded
manifest of the already-installed Equalizer APO tools, used to explain the UAC
requirement.
