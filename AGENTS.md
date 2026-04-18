# AGENTS.md

## Purpose

This file is for coding agents and automation touching this repository.

## Mandatory Checks Before Declaring Success

1. Run:
   ```bash
   python3 -m unittest discover -s tests -v
   ```
2. If build-related files changed, verify:
   ```bash
   flet build macos --yes
   ```
3. When changing packaging or CI behavior, inspect:
   - `build/flutter/app/app.zip`
   - `build/flutter/pubspec.yaml`

## Packaging Constraints

- Keep `main.py` at repo root as the Flet entry point.
- App package excludes are intentional and should remain unless replaced with an
  equally strict alternative.
- The generated Flutter shell consumes overrides from:
  `tool.flet.flutter.pubspec` in `pyproject.toml`.

## CI Constraints

- CI intentionally uses `uvx --from "flet-cli==0.83.1"` for Flet builds.
- CI intentionally uses `macos-15` for macOS builds.
- If macOS CI fails in native compilation, check plugin versions before
  changing Python code.
- `build-desktop.yml` artifacts are not release artifacts.
- Public macOS downloads must come from `release-desktop.yml` only.

## Dependency Overrides That Must Stay Explained

These currently exist for CI stability:

```toml
[tool.flet.flutter.pubspec.dependency_overrides]
connectivity_plus = "7.0.0"
device_info_plus = "12.3.0"
```

Reason:

- unpinned Flutter plugin resolution produced `connectivity_plus 7.1.1`
- that version failed on CI with:
  `NWPath has no member 'isUltraConstrained'`

## Functional Invariants

- Normalization must not silently overwrite an existing different file.
- Failed rename sequences must roll back.
- Bulk fix must process children before parents.
- Realtime monitoring and bulk fix should share the same core rename logic.
- Final macOS release validation must happen on the packaged zip after
  extraction, not only on the staging `.app`.
