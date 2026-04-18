# CLAUDE.md

## Project Summary

watchcat is a Flet desktop application for fixing Korean filename normalization
issues. The repo was recently split into a package-based layout while keeping a
root `main.py` entry point because Flet packaging depends on it.

## Code Layout

- `main.py`: import-only entry point for Flet
- `watchcat_app/ui.py`: UI composition and monitor lifecycle
- `watchcat_app/path_fixer.py`: normalization, collision checks, rollback logic
- `watchcat_app/monitor.py`: `watchdog` integration
- `watchcat_app/picker.py`: macOS native folder picker
- `watchcat_app/unicode_utils.py`: visible Jamo rendering for logs

## Rules That Matter

1. Do not move app startup out of root `main.py` unless you also update
   `tool.flet.app.module` or `tool.flet.app.path`.
2. Do not remove the app/package excludes in `pyproject.toml` unless you verify
   `build/flutter/app/app.zip` no longer captures repo-local junk such as
   `.venv`, `.claude`, or tests.
3. Do not remove Flutter dependency overrides casually:
   - `connectivity_plus = "7.0.0"`
   - `device_info_plus = "12.3.0"`
   These were added to stop CI-only macOS native compile failures caused by
   upstream plugin drift.
4. Do not upgrade `flet-cli` in CI casually. The workflows intentionally pin
   `0.83.1` because `0.84.0` hit a `serious_python` macOS packaging regression.
5. If macOS CI breaks again, inspect generated `build/flutter/pubspec.yaml`
   before changing app code. The root cause may be Flutter-side dependency
   resolution, not Python code.
6. Do not hand out artifacts from `build-desktop.yml` as releases. Only the
   release workflow output is expected to be signed, notarized, stapled, and
   safe for Gatekeeper.

## Testing Expectations

Run:

```bash
python3 -m unittest discover -s tests -v
```

Current regression tests cover:

- successful NFD to NFC rename
- no-op cases
- collision skip behavior
- rollback after failed second rename
- bulk-fix scanned/fixed counts

## Build Expectations

Local build command:

```bash
flet build macos --yes
```

CI build command:

```bash
uvx --from "flet-cli==${FLET_CLI_VERSION}" flet build <target> --yes --verbose --clear-cache
```

## Recent Root Causes and Fixes

- `fix_path()` used to overwrite existing normalized files on Unix-like systems.
  It now detects collisions and skips them.
- `fix_path()` used to leave temp artifacts if the second rename failed. It now
  rolls back.
- Monitor mode used to wrap `Observer.start()` in another thread, creating a
  `join before start` race. That wrapper was removed.
- CI once failed in `serious_python` packaging and then in Flutter plugin
  compilation. The durable fix was a combination of:
  - pinning `flet-cli` in workflows
  - keeping macOS CI on `macos-15`
  - pinning Flutter plugin overrides in `pyproject.toml`
- Gatekeeper-facing distribution must be validated from the final packaged zip,
  not just the in-place `.app`, because users open the released archive.
