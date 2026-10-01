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
- The GUI supports list creation, item toggles, per-item deletion, placeholder hints, and confirmation of destructive actions. Main-window sizing keeps sidebar controls fully accessible. Completed items retain completion order above unfinished items, showing only the newest configured count without deleting hidden items.
- Light/dark themes include readable controls, a theme-aware version badge, and custom dock/Finder icons. Settings theme controls have consistent palette colors and symmetric margins, including during live theme changes.
- Settings use fully visible, centered Save/Cancel actions, validate and save the full payload, apply theme and completed-item filtering live, and discard unsaved controls on window Cancel. Filtering never changes stored content.
- Directory changes apply live with optional list movement and an explicit confirmation question; popup Cancel retains the directory while saving other settings. Populated destinations are accepted, transfers reject filename collisions without overwriting, equivalent paths are harmless, and configuration stays fixed.
- Relocation failures preserve recoverable files and refresh the active view. Failed settings persistence keeps the destination usable and supports retry without repeating completed moves; pending theme/filter edits remain unapplied.
- Automated GUI tests intercept unexpected dialogs and verify cleanup after failures without human interaction.
- Build and release scripts produce a launch-tested Apple Silicon app bundle and versioned distributable ZIP.

## Active Task

### 42: Visible input insertion cursors (S)

- Branch: `implementer/task-42-input-caret-contrast`; base/integration: `main`.
- Scope: focused theme-style correction for all editable input carets.
- Acceptance: list-name, new-item, Settings folder and completed-count spinbox carets contrast with their effective field backgrounds in light and dark modes, both startup and live switches. Fields keep their text, focus/editing and placeholder behavior; open/reopened Settings controls receive current styles. Preserve native appearance/fallback policy.
- Required tests: actual widgets and effective ttk insertion-color/field-background options, light/dark contrast, focused editing, live transitions and settings reopen; existing placeholder/theme/settings regressions.
- Commands from `implementer/`: `(cd src && .venv/bin/python -m pytest tests/test_gui_theme.py tests/test_gui_settings.py tests/test_gui_placeholders.py -q)`; `(cd src && .venv/bin/python -m pytest tests -q)`.
- Complete Implementer prompt: Fix task 42 in `src/todo_md/app.py`, `src/tests/test_gui_theme.py`, and `src/tests/test_gui_settings.py` only (normal hook VERSION change allowed). Inspect the actual ttk Entry/Spinbox insertion-color option rather than assuming plain tk insertbackground applies. Explicitly theme carets and any necessary field colors using the existing palette for all four input kinds. Preserve native appearance handling, existing state/placeholder behavior and every earlier layout/order fix. Add isolated real-widget tests proving contrasting insertion colors at startup and after light/dark transitions, including Settings open/reopen and focused editing. Use existing managed-root fixtures where available and fail-fast dialogs. Follow DESIGN Presentation/Tk constraints and run both commands. No unrelated refactoring.

## Queue

None.

## Active Blockers

None.

## Recently Completed

- 41: Persisted completion order and safe filtered GUI callbacks; independently verified and approved; `5b9c4457bf25fc6b682ffd1e14e243577789e81c`.
- 40: Settings Theme palette and margins; independently verified and approved; `9d785ef23b8b9778645936b5e7f42113a8ae9434`.
- 39: Visible centered Settings actions; independently verified and approved; `7c69eb2413098f97ffa91d5e2507578c07aac669`.
- 38: Main-window sidebar visibility; independently verified and approved; `ba7e7bbe4fc309c02ed23c099403c292e81256af`.
- 37: Populated lists destinations and confirmation question; independently verified and approved; `b20176d08c7450398a1767e82b5bf5669fc6c62e`.
