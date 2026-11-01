# Contributing

Thanks for taking the time to help.

## Setup

```
python -m pip install ruff mypy pyinstaller
```

Python 3.11 or newer. There are no runtime dependencies.

## Before opening a pull request

```
ruff check .
mypy
python -m unittest test_configfile test_apo test_i18n test_platform test_settings test_diagnostics test_verify test_report test_hotkey test_winenv test_preview test_update
python app.py --smoke
python app.py --smoke-ui
```

All five must pass. `test_apo` and the smoke tests only run on Windows (they
exercise Equalizer APO) and skip elsewhere.

## Ground rules

- **No runtime dependencies.** The app must keep working with the standard
  library only; every dependency is a future broken install.
- **Never stack gain.** A `Preamp` filter adds to any other one in the same
  audio chain. The app owns exactly one gain source
  (`volume-booster.txt`) and removes any legacy block.
- **Fail closed.** A config with unbalanced markers must be refused, never
  guessed at. A broken settings file must fall back to defaults.
- **No hidden writes.** Anything that touches the user's audio configuration
  gets a backup and an atomic write.
- **No network.** No telemetry, analytics or auto-updater.

## Translations

Each language lives in `i18n.py`. Add the key to every table; the test suite
fails if a language is missing one, or if placeholders (`{gain}`, `{engine}`,
`{error}`, `{location}`) differ from English.

## Style

Line length 120, `ruff` rules as configured in `pyproject.toml`, type hints on
every public function. Commit messages follow Conventional Commits
(`feat:`, `fix:`, `docs:`, `test:`, `refactor:`).
