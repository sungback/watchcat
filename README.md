# watchcat

watchcat is a Flet desktop app that fixes Korean filename normalization issues,
primarily converting decomposed NFD names into NFC names on macOS-originated
files.

## Structure

- `main.py`: Thin Flet entry point kept at repo root for `flet build`
- `watchcat_app/ui.py`: Flet UI and monitor/bulk-fix wiring
- `watchcat_app/path_fixer.py`: Filename normalization and bulk traversal logic
- `watchcat_app/monitor.py`: `watchdog` event handler
- `watchcat_app/unicode_utils.py`: Jamo visualization helpers for log output
- `tests/test_main.py`: Regression tests for pure normalization behavior

## Local Development

Install dependencies with `uv` and run tests:

```bash
uv sync
python3 -m unittest discover -s tests -v
```

Build locally:

```bash
flet build macos --yes
```

## Important Build Notes

- Keep `main.py` as the root entry point unless `tool.flet.app.module` is
  changed as well.
- App packaging excludes `tests`, `.venv`, `.claude`, `.git`, and common cache
  directories via `pyproject.toml`.
- Flutter dependency drift caused CI-only macOS failures. The repo currently
  pins these overrides in `pyproject.toml` under
  `tool.flet.flutter.pubspec.dependency_overrides`:
  - `connectivity_plus = "7.0.0"`
  - `device_info_plus = "12.3.0"`
- CI also pins `flet-cli==0.83.1`. Do not casually upgrade it without rerunning
  the macOS packaging workflow.

## CI and Release Rules

- Desktop CI uses `uvx --from "flet-cli==${FLET_CLI_VERSION}" flet build ...`
  instead of `uv run flet build ...`.
- macOS CI currently targets `macos-15` because newer Flutter/plugin
  combinations required Xcode 16.x during this debugging cycle.
- `build-desktop.yml` artifacts are CI verification outputs only. They are not
  official end-user downloads and must be treated as unsigned/unsafe for public
  distribution.
- Official macOS distribution must come from the GitHub Release asset produced
  by `release-desktop.yml` after signing, notarization, stapling, and zip
  re-verification.
- Failure diagnostics intentionally dump:
  - `build/`
  - `build/flutter/build/`
  - `build/flutter/app/`

## Behavior Guarantees Covered by Tests

- Missing or already-normalized paths are skipped
- NFD names are renamed and logged correctly
- Existing normalized targets are not silently overwritten
- Failed second-stage rename attempts roll back to the original path
- Bulk fix counts scanned and fixed entries correctly

## Known Recent Fixes

- Refactored the app into `watchcat_app/` while keeping Flet packaging working
- Prevented overwrite-on-normalize collisions
- Added rollback after failed rename sequences
- Removed the observer start/join race in monitor mode
- Stabilized GitHub Actions macOS builds by pinning Flet CLI and Flutter plugin
  overrides
