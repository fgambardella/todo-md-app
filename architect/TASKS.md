# TASKS.md

## Project Goal

Build a macOS desktop TODO app in Python with a stdlib-only runtime. Persist each list as a portable Markdown file with GFM checkboxes. Keep domain, persistence, and controller logic headlessly testable beneath the Tkinter GUI, with persistent settings and light/dark themes.

## Test Policy

- Framework: pytest, already used throughout `implementer/src/tests/`.
- Full suite from `implementer/`: `(cd src && .venv/bin/python -m pytest tests -v)`.
- Targeted convention from `implementer/`: `(cd src && .venv/bin/python -m pytest tests/<file>.py -v)`.
- Tests require `implementer/src/` as working directory for existing relative asset paths; tools may set that workdir directly and run the inner command.
- Build/release changes also require the corresponding gated tests from `implementer/src/`: `RUN_BUILD_TESTS=1 .venv/bin/python -m pytest tests/test_build_script.py -v`; `RUN_RELEASE_TESTS=1 .venv/bin/python -m pytest tests/test_release_package.py -v`.
- GUI tests run on the local display with isolated data/config directories. Owned roots are updated and unconditionally destroyed, including failure paths; headless tests never launch the GUI.
- Automated tests must never require human input. Mock expected dialog choices explicitly; unexpected dialogs must fail immediately or at teardown when swallowed by Tk. Shared facilities: `implementer/src/tests/conftest.py`. Negative subprocess tests assert expected inner failures while the outer suite remains green. Never blanket-answer Yes, suppress failures, or add skips/xfails to hide regressions.

## Current Implementation Summary

- Lists persist as separate Markdown files with atomic writes and filesystem-safe names; validated item operations are persisted immediately.
- The GUI supports list creation, item toggles, per-item deletion, placeholder hints, and confirmation of destructive actions. Main-window sizing keeps sidebar controls fully accessible.
- Light/dark themes include readable controls, a theme-aware version badge, and custom dock/Finder icons.
- Settings validate and save the full payload, apply theme and completed-item filtering live, and discard unsaved controls on window Cancel. Filtering never changes stored content.
- Directory changes apply live with optional list movement and an explicit confirmation question; popup Cancel retains the directory while saving other settings. Populated destinations are accepted, transfers reject filename collisions without overwriting, equivalent paths are harmless, and configuration stays fixed.
- Relocation failures preserve recoverable files and refresh the active view. Failed settings persistence keeps the destination usable and supports retry without repeating completed moves; pending theme/filter edits remain unapplied.
- Automated GUI tests intercept unexpected dialogs and verify cleanup after failures without human interaction.
- Build and release scripts produce a launch-tested Apple Silicon app bundle and versioned distributable ZIP.

## Active Task

### 39: Visible centered Settings actions (S)

- Branch: `implementer/task-39-settings-actions`; base/integration: `main`.
- Scope: one focused Settings-dialog layout correction for clipped and right-aligned Save/Cancel buttons.
- Acceptance: both actions and all settings fields fit when opened in light/dark modes; the combined Cancel/Save group is horizontally centered and stays centered after widening. Minimum resizing cannot clip controls. Existing Save/Cancel behavior and single-dialog lifecycle remain unchanged.
- Required tests: actual mapped dimensions/ancestor bounds, centered group midpoint within a small pixel tolerance, initial/enlarged/minimum geometry in both themes, existing behavior regressions.
- Commands from `implementer/`: `(cd src && .venv/bin/python -m pytest tests/test_gui_settings.py tests/test_gui_layout.py -q)`; `(cd src && .venv/bin/python -m pytest tests -q)`.
- Complete Implementer prompt: Implement task 39 only in `src/todo_md/app.py` and `src/tests/test_gui_settings.py` (normal hook VERSION change allowed). Replace undersized fixed Settings geometry with content-aware initial/minimum sizing and center the Cancel/Save group as a unit. Preserve the relative button order and all callbacks/behavior. Reuse existing test fixtures and ensure geometry tests prove full visibility, non-overlap and centering on startup and resizing in both palettes. Follow DESIGN Presentation/Tk constraints. Run both exact commands. Do not address Theme section styling/margins, completion ordering, or cursor colors yet.

## Queue

- 40: Settings Theme section needs palette-matched light/dark backgrounds and left/right margins.
- 41: Completed items must appear above incomplete items in completion order (oldest first); completing another item should evict only the oldest visible completed item when the configured limit is exceeded.
- 42: Input-field insertion cursors must remain visible in light mode.

## Active Blockers

None.

## Recently Completed

- 38: Main-window sidebar visibility; independently verified and approved; `ba7e7bbe4fc309c02ed23c099403c292e81256af`.
- 37: Populated lists destinations and confirmation question; independently verified and approved; `b20176d08c7450398a1767e82b5bf5669fc6c62e`.
- 36b2: GUI relocation and unattended test harness; independently verified and approved; `a0fc76918d5424334a1116176838013115eaed84`.
- 36b1: Headless controller directory switching; verified and merged; `9612b3b`.
- 36a: Headless lists-directory relocation; verified and merged; `f543275`.
