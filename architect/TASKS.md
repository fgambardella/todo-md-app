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
- Settings use fully visible, centered Save/Cancel actions, validate and save the full payload, apply theme and completed-item filtering live, and discard unsaved controls on window Cancel. Filtering never changes stored content.
- Directory changes apply live with optional list movement and an explicit confirmation question; popup Cancel retains the directory while saving other settings. Populated destinations are accepted, transfers reject filename collisions without overwriting, equivalent paths are harmless, and configuration stays fixed.
- Relocation failures preserve recoverable files and refresh the active view. Failed settings persistence keeps the destination usable and supports retry without repeating completed moves; pending theme/filter edits remain unapplied.
- Automated GUI tests intercept unexpected dialogs and verify cleanup after failures without human interaction.
- Build and release scripts produce a launch-tested Apple Silicon app bundle and versioned distributable ZIP.

## Active Task

### 40: Settings Theme section appearance (S)

- Branch: `implementer/task-40-settings-theme-style`; base/integration: `main`.
- Scope: one focused Theme-section styling correction, including its surrounding horizontal margin.
- Acceptance: section body, title and radio labels use the existing light/dark palette with readable text, including active/selected radio states. Both outer horizontal margins are nonzero and symmetric. Dialog margin background matches the surrounding palette. Existing/open/reopened dialogs follow live theme changes; native theme behavior and settings semantics remain intact.
- Required tests: both palette values, relevant ttk state lookups, measured outer margins, open-dialog light/dark switching and reopening, plus existing geometry/behavior regressions.
- Commands from `implementer/`: `(cd src && .venv/bin/python -m pytest tests/test_gui_settings.py tests/test_gui_theme.py tests/test_gui_theme_switch.py -q)`; `(cd src && .venv/bin/python -m pytest tests -q)`.
- Complete Implementer prompt: Fix task 40 in `src/todo_md/app.py` and `src/tests/test_gui_settings.py` only (normal hook VERSION change allowed). Use existing theme colors for the Settings Theme LabelFrame/title/radiobutton backgrounds and foregrounds, prevent default bright/tanned active fills, and add left/right outer margins consistent with adjacent content. Ensure the Toplevel background behind margins uses the same palette on opening and live theme changes. Preserve native theme fallback policy, radio selection, Save/Cancel semantics, content-aware geometry and centered actions. Add regression tests with existing isolated fixtures for startup and live/reopened theme transitions, active/selected styles, and real symmetric margins. Follow DESIGN Presentation/Tk constraints and run both exact commands. Do not change completion ordering or entry cursors yet.

## Queue

- 41: Completed items must appear above incomplete items in completion order (oldest first); completing another item should evict only the oldest visible completed item when the configured limit is exceeded.
- 42: Input-field insertion cursors must remain visible in light mode.

## Active Blockers

None.

## Recently Completed

- 39: Visible centered Settings actions; independently verified and approved; `7c69eb2413098f97ffa91d5e2507578c07aac669`.
- 38: Main-window sidebar visibility; independently verified and approved; `ba7e7bbe4fc309c02ed23c099403c292e81256af`.
- 37: Populated lists destinations and confirmation question; independently verified and approved; `b20176d08c7450398a1767e82b5bf5669fc6c62e`.
- 36b2: GUI relocation and unattended test harness; independently verified and approved; `a0fc76918d5424334a1116176838013115eaed84`.
- 36b1: Headless controller directory switching; verified and merged; `9612b3b`.
